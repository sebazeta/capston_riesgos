"""
SERVICIO DE RIESGO POR CONCENTRACIÓN - PROYECTO TITA
=====================================================
Implementa el modelo híbrido de riesgo por dependencia:
- Fase 1: Blast Radius (VM → Host) - El host hereda impacto de sus VMs
- Fase 2: Herencia (Host → VM) - Las VMs heredan riesgo del host
- Fase 3: Ajuste de Riesgo Residual por concentración

Basado en MAGERIT v3, Libro II, Capítulo 4 (Propagación de impacto)
"""
import json
import datetime as dt
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict, field
from services.database_service import (
    read_table, insert_rows, update_row, delete_row,
    get_connection
)


# ==================== CONSTANTES ====================

# Factor de herencia: cuánto del riesgo del host se transfiere a la VM
FACTOR_HERENCIA = 0.7

# Umbral para calcular factor de concentración
UMBRAL_BLAST_RADIUS = 5

# Máximo factor de concentración (limita el ajuste)
MAX_FACTOR_CONCENTRACION = 4

# Penalización a efectividad de controles por concentración
PENALIZACION_CONCENTRACION = 0.1


# ==================== MODELOS DE DATOS ====================

@dataclass
class DependenciaVM:
    """Representa la dependencia de una VM con su host"""
    id_activo: str
    nombre_activo: str
    id_host: str
    nombre_host: str
    tipo_dependencia: str  # 'total', 'parcial', 'ninguna'
    criticidad_vm: int  # max(D, I, C) de la VM
    peso_dependencia: float  # 1.0, 0.5, 0.0 según tipo
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ResultadoConcentracion:
    """Resultado del cálculo de concentración para un host"""
    id_evaluacion: str
    id_host: str
    nombre_host: str
    num_vms_dependientes: int
    blast_radius: float
    factor_concentracion: int
    impacto_d_original: int
    impacto_d_ajustado: int
    riesgo_original: float
    riesgo_ajustado: float
    vms_criticas: List[Dict]  # Lista de VMs con criticidad >= 4
    es_spof: bool  # Single Point of Failure
    fecha_calculo: str
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['vms_criticas'] = json.dumps(self.vms_criticas, ensure_ascii=False)
        return result


@dataclass
class RiesgoHeredado:
    """Riesgo heredado por una VM desde su host"""
    id_activo: str
    nombre_activo: str
    id_host: str
    nombre_host: str
    riesgo_vm_propio: float
    riesgo_host: float
    riesgo_heredado: float
    riesgo_final: float
    nivel_riesgo_final: str
    ajuste_aplicado: bool
    justificacion: str


# ==================== FUNCIONES DE BASE DE DATOS ====================

def init_concentration_tables():
    """Inicializa las tablas necesarias para riesgo por concentración"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Agregar columnas a INVENTARIO_ACTIVOS si no existen
        try:
            cursor.execute("ALTER TABLE INVENTARIO_ACTIVOS ADD COLUMN ID_Host TEXT")
        except:
            pass  # Ya existe
        
        try:
            cursor.execute("ALTER TABLE INVENTARIO_ACTIVOS ADD COLUMN Tipo_Dependencia TEXT DEFAULT 'total'")
        except:
            pass  # Ya existe
        
        # Tabla de resultados de concentración
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS RESULTADOS_CONCENTRACION (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_Evaluacion TEXT,
                ID_Host TEXT,
                Nombre_Host TEXT,
                Num_VMs_Dependientes INTEGER,
                Blast_Radius REAL,
                Factor_Concentracion INTEGER,
                Impacto_D_Original INTEGER,
                Impacto_D_Ajustado INTEGER,
                Riesgo_Original REAL,
                Riesgo_Ajustado REAL,
                VMs_Criticas TEXT,
                Es_SPOF INTEGER DEFAULT 0,
                Fecha_Calculo TEXT,
                UNIQUE(ID_Evaluacion, ID_Host)
            )
        ''')
        
        # Tabla de herencia de riesgo
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS RIESGO_HEREDADO (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_Evaluacion TEXT,
                ID_Activo TEXT,
                ID_Host TEXT,
                Riesgo_VM_Propio REAL,
                Riesgo_Host REAL,
                Riesgo_Heredado REAL,
                Riesgo_Final REAL,
                Nivel_Riesgo_Final TEXT,
                Ajuste_Aplicado INTEGER DEFAULT 0,
                Justificacion TEXT,
                Fecha_Calculo TEXT,
                UNIQUE(ID_Evaluacion, ID_Activo)
            )
        ''')
        
        conn.commit()


def asignar_host_a_vm(eval_id: str, id_vm: str, id_host: str, 
                      tipo_dependencia: str = "total") -> Tuple[bool, str]:
    """
    Asigna un host físico a una VM
    
    Args:
        eval_id: ID de la evaluación
        id_vm: ID del activo virtual
        id_host: ID del host físico
        tipo_dependencia: 'total', 'parcial', 'ninguna'
    
    Returns:
        (éxito, mensaje)
    """
    try:
        # Validar que el host existe y es físico
        activos = read_table("INVENTARIO_ACTIVOS")
        
        host = activos[
            (activos["ID_Evaluacion"] == eval_id) &
            (activos["ID_Activo"] == id_host)
        ]
        
        if host.empty:
            return False, f"Host {id_host} no encontrado"
        
        if host.iloc[0].get("Tipo_Activo") != "Servidor Físico":
            return False, f"El activo {id_host} no es un Servidor Físico"
        
        # Validar que la VM existe y es virtual
        vm = activos[
            (activos["ID_Evaluacion"] == eval_id) &
            (activos["ID_Activo"] == id_vm)
        ]
        
        if vm.empty:
            return False, f"VM {id_vm} no encontrada"
        
        if vm.iloc[0].get("Tipo_Activo") != "Servidor Virtual":
            return False, f"El activo {id_vm} no es un Servidor Virtual"
        
        # Asignar
        update_row(
            "INVENTARIO_ACTIVOS",
            {"ID_Host": id_host, "Tipo_Dependencia": tipo_dependencia},
            {"ID_Evaluacion": eval_id, "ID_Activo": id_vm}
        )
        
        return True, f"✅ VM {id_vm} asignada al host {id_host} ({tipo_dependencia})"
    
    except Exception as e:
        return False, f"❌ Error: {str(e)}"


def get_vms_de_host(eval_id: str, id_host: str) -> pd.DataFrame:
    """Obtiene todas las VMs que dependen de un host"""
    activos = read_table("INVENTARIO_ACTIVOS")
    
    if activos.empty or "ID_Host" not in activos.columns:
        return pd.DataFrame()
    
    return activos[
        (activos["ID_Evaluacion"] == eval_id) &
        (activos["ID_Host"] == id_host) &
        (activos["Tipo_Activo"] == "Servidor Virtual")
    ]


def get_hosts_evaluacion(eval_id: str) -> pd.DataFrame:
    """Obtiene todos los hosts físicos de una evaluación"""
    activos = read_table("INVENTARIO_ACTIVOS")
    
    if activos.empty:
        return pd.DataFrame()
    
    return activos[
        (activos["ID_Evaluacion"] == eval_id) &
        (activos["Tipo_Activo"] == "Servidor Físico")
    ]


# ==================== CÁLCULO DE BLAST RADIUS ====================

def obtener_criticidad_vm(eval_id: str, id_activo: str) -> int:
    """
    Obtiene la criticidad de una VM (max de D, I, C)
    Busca primero en RESULTADOS_MAGERIT, luego en IMPACTO_ACTIVOS
    """
    # Intentar desde RESULTADOS_MAGERIT
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT Impacto_D, Impacto_I, Impacto_C 
                FROM RESULTADOS_MAGERIT 
                WHERE ID_Evaluacion = ? AND ID_Activo = ?
                ORDER BY Fecha_Evaluacion DESC LIMIT 1
            ''', [eval_id, id_activo])
            
            row = cursor.fetchone()
            if row:
                d = row[0] or 3
                i = row[1] or 3
                c = row[2] or 3
                return max(d, i, c)
    except:
        pass
    
    # Fallback: valor por defecto
    return 3


def calcular_blast_radius(eval_id: str, id_host: str) -> ResultadoConcentracion:
    """
    Calcula el blast radius de un host físico
    
    Blast Radius = Σ(Criticidad_VM × Peso_Dependencia)
    
    Donde:
    - Criticidad = max(D, I, C) de cada VM
    - Peso = 1.0 (total), 0.5 (parcial), 0.0 (ninguna)
    """
    # Obtener datos del host
    activos = read_table("INVENTARIO_ACTIVOS")
    host_data = activos[
        (activos["ID_Evaluacion"] == eval_id) &
        (activos["ID_Activo"] == id_host)
    ]
    
    if host_data.empty:
        raise ValueError(f"Host {id_host} no encontrado")
    
    host = host_data.iloc[0]
    nombre_host = host.get("Nombre_Activo", id_host)
    
    # Obtener VMs dependientes
    vms = get_vms_de_host(eval_id, id_host)
    
    if vms.empty:
        # Sin VMs, sin concentración
        return ResultadoConcentracion(
            id_evaluacion=eval_id,
            id_host=id_host,
            nombre_host=nombre_host,
            num_vms_dependientes=0,
            blast_radius=0.0,
            factor_concentracion=0,
            impacto_d_original=3,
            impacto_d_ajustado=3,
            riesgo_original=0.0,
            riesgo_ajustado=0.0,
            vms_criticas=[],
            es_spof=False,
            fecha_calculo=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    # Calcular blast radius
    blast_radius = 0.0
    vms_criticas = []
    
    peso_map = {"total": 1.0, "parcial": 0.5, "ninguna": 0.0}
    
    for _, vm in vms.iterrows():
        id_vm = vm["ID_Activo"]
        nombre_vm = vm.get("Nombre_Activo", id_vm)
        tipo_dep = vm.get("Tipo_Dependencia", "total")
        peso = peso_map.get(tipo_dep, 1.0)
        
        criticidad = obtener_criticidad_vm(eval_id, id_vm)
        
        aporte = criticidad * peso
        blast_radius += aporte
        
        if criticidad >= 4:
            vms_criticas.append({
                "id": id_vm,
                "nombre": nombre_vm,
                "criticidad": criticidad,
                "dependencia": tipo_dep
            })
    
    # Calcular factor de concentración
    factor_concentracion = min(
        MAX_FACTOR_CONCENTRACION,
        int(blast_radius / UMBRAL_BLAST_RADIUS)
    )
    
    # Obtener impacto original del host
    impacto_d_original = obtener_criticidad_vm(eval_id, id_host)
    
    # Calcular impacto ajustado
    impacto_d_ajustado = min(5, impacto_d_original + factor_concentracion)
    
    # Determinar si es SPOF
    es_spof = len(vms_criticas) >= 2 or (len(vms) >= 3 and factor_concentracion >= 2)
    
    # Obtener riesgo original del host
    riesgo_original = _obtener_riesgo_activo(eval_id, id_host)
    
    # Calcular riesgo ajustado (recalcular con nuevo impacto)
    # Riesgo = Probabilidad × Impacto
    probabilidad_host = _obtener_probabilidad_activo(eval_id, id_host)
    riesgo_ajustado = probabilidad_host * impacto_d_ajustado
    
    return ResultadoConcentracion(
        id_evaluacion=eval_id,
        id_host=id_host,
        nombre_host=nombre_host,
        num_vms_dependientes=len(vms),
        blast_radius=blast_radius,
        factor_concentracion=factor_concentracion,
        impacto_d_original=impacto_d_original,
        impacto_d_ajustado=impacto_d_ajustado,
        riesgo_original=riesgo_original,
        riesgo_ajustado=riesgo_ajustado,
        vms_criticas=vms_criticas,
        es_spof=es_spof,
        fecha_calculo=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


def _obtener_riesgo_activo(eval_id: str, id_activo: str) -> float:
    """Obtiene el riesgo inherente de un activo desde RESULTADOS_MAGERIT"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT Riesgo_Inherente 
                FROM RESULTADOS_MAGERIT 
                WHERE ID_Evaluacion = ? AND ID_Activo = ?
                ORDER BY Fecha_Evaluacion DESC LIMIT 1
            ''', [eval_id, id_activo])
            
            row = cursor.fetchone()
            if row:
                return float(row[0] or 0)
    except:
        pass
    return 0.0


def _obtener_probabilidad_activo(eval_id: str, id_activo: str) -> float:
    """Obtiene la probabilidad de un activo"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT Probabilidad 
                FROM RESULTADOS_MAGERIT 
                WHERE ID_Evaluacion = ? AND ID_Activo = ?
                ORDER BY Fecha_Evaluacion DESC LIMIT 1
            ''', [eval_id, id_activo])
            
            row = cursor.fetchone()
            if row:
                return float(row[0] or 3)
    except:
        pass
    return 3.0


# ==================== HERENCIA DE RIESGO ====================

def calcular_riesgo_heredado(eval_id: str, id_vm: str) -> Optional[RiesgoHeredado]:
    """
    Calcula el riesgo heredado de una VM desde su host
    
    Riesgo_Final = max(Riesgo_VM_Propio, Riesgo_Host × FACTOR_HERENCIA)
    """
    # Obtener datos de la VM
    activos = read_table("INVENTARIO_ACTIVOS")
    
    vm_data = activos[
        (activos["ID_Evaluacion"] == eval_id) &
        (activos["ID_Activo"] == id_vm)
    ]
    
    if vm_data.empty:
        return None
    
    vm = vm_data.iloc[0]
    
    if vm.get("Tipo_Activo") != "Servidor Virtual":
        return None
    
    id_host = vm.get("ID_Host")
    
    if not id_host or pd.isna(id_host):
        # VM sin host asignado
        riesgo_propio = _obtener_riesgo_activo(eval_id, id_vm)
        return RiesgoHeredado(
            id_activo=id_vm,
            nombre_activo=vm.get("Nombre_Activo", id_vm),
            id_host="",
            nombre_host="(Sin host asignado)",
            riesgo_vm_propio=riesgo_propio,
            riesgo_host=0.0,
            riesgo_heredado=0.0,
            riesgo_final=riesgo_propio,
            nivel_riesgo_final=_get_nivel_riesgo(riesgo_propio),
            ajuste_aplicado=False,
            justificacion="VM sin host asignado, usando riesgo propio"
        )
    
    # Obtener datos del host
    host_data = activos[
        (activos["ID_Evaluacion"] == eval_id) &
        (activos["ID_Activo"] == id_host)
    ]
    
    if host_data.empty:
        riesgo_propio = _obtener_riesgo_activo(eval_id, id_vm)
        return RiesgoHeredado(
            id_activo=id_vm,
            nombre_activo=vm.get("Nombre_Activo", id_vm),
            id_host=id_host,
            nombre_host="(Host no encontrado)",
            riesgo_vm_propio=riesgo_propio,
            riesgo_host=0.0,
            riesgo_heredado=0.0,
            riesgo_final=riesgo_propio,
            nivel_riesgo_final=_get_nivel_riesgo(riesgo_propio),
            ajuste_aplicado=False,
            justificacion="Host no encontrado, usando riesgo propio"
        )
    
    host = host_data.iloc[0]
    nombre_host = host.get("Nombre_Activo", id_host)
    
    # Obtener riesgos
    riesgo_vm_propio = _obtener_riesgo_activo(eval_id, id_vm)
    
    # Para el host, usar el riesgo ajustado si existe
    riesgo_host = _obtener_riesgo_ajustado_host(eval_id, id_host)
    if riesgo_host == 0:
        riesgo_host = _obtener_riesgo_activo(eval_id, id_host)
    
    # Calcular herencia
    riesgo_heredado = riesgo_host * FACTOR_HERENCIA
    
    # El riesgo final es el máximo
    if riesgo_heredado > riesgo_vm_propio:
        riesgo_final = riesgo_heredado
        ajuste_aplicado = True
        justificacion = f"Riesgo heredado del host ({riesgo_heredado:.1f}) supera riesgo propio ({riesgo_vm_propio:.1f})"
    else:
        riesgo_final = riesgo_vm_propio
        ajuste_aplicado = False
        justificacion = f"Riesgo propio ({riesgo_vm_propio:.1f}) es mayor que heredado ({riesgo_heredado:.1f})"
    
    return RiesgoHeredado(
        id_activo=id_vm,
        nombre_activo=vm.get("Nombre_Activo", id_vm),
        id_host=id_host,
        nombre_host=nombre_host,
        riesgo_vm_propio=riesgo_vm_propio,
        riesgo_host=riesgo_host,
        riesgo_heredado=riesgo_heredado,
        riesgo_final=riesgo_final,
        nivel_riesgo_final=_get_nivel_riesgo(riesgo_final),
        ajuste_aplicado=ajuste_aplicado,
        justificacion=justificacion
    )


def _obtener_riesgo_ajustado_host(eval_id: str, id_host: str) -> float:
    """Obtiene el riesgo ajustado de un host desde RESULTADOS_CONCENTRACION"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT Riesgo_Ajustado 
                FROM RESULTADOS_CONCENTRACION 
                WHERE ID_Evaluacion = ? AND ID_Host = ?
            ''', [eval_id, id_host])
            
            row = cursor.fetchone()
            if row:
                return float(row[0] or 0)
    except:
        pass
    return 0.0


def _get_nivel_riesgo(valor: float) -> str:
    """Determina el nivel de riesgo"""
    if valor >= 20:
        return "CRÍTICO"
    elif valor >= 12:
        return "ALTO"
    elif valor >= 6:
        return "MEDIO"
    elif valor >= 3:
        return "BAJO"
    else:
        return "MUY BAJO"


# ==================== FUNCIONES PRINCIPALES ====================

def calcular_concentracion_evaluacion(eval_id: str) -> List[ResultadoConcentracion]:
    """
    Calcula el riesgo por concentración para todos los hosts de una evaluación
    
    Proceso:
    1. Obtener todos los hosts físicos
    2. Para cada host, calcular blast radius
    3. Guardar resultados
    """
    # Inicializar tablas si no existen
    init_concentration_tables()
    
    resultados = []
    hosts = get_hosts_evaluacion(eval_id)
    
    if hosts.empty:
        return resultados
    
    for _, host in hosts.iterrows():
        id_host = host["ID_Activo"]
        
        try:
            resultado = calcular_blast_radius(eval_id, id_host)
            resultados.append(resultado)
            
            # Guardar en BD
            _guardar_resultado_concentracion(resultado)
        
        except Exception as e:
            print(f"Error calculando concentración para {id_host}: {e}")
    
    return resultados


def calcular_herencia_evaluacion(eval_id: str) -> List[RiesgoHeredado]:
    """
    Calcula el riesgo heredado para todas las VMs de una evaluación
    
    Debe ejecutarse DESPUÉS de calcular_concentracion_evaluacion
    """
    resultados = []
    activos = read_table("INVENTARIO_ACTIVOS")
    
    if activos.empty:
        return resultados
    
    vms = activos[
        (activos["ID_Evaluacion"] == eval_id) &
        (activos["Tipo_Activo"] == "Servidor Virtual")
    ]
    
    for _, vm in vms.iterrows():
        id_vm = vm["ID_Activo"]
        
        try:
            resultado = calcular_riesgo_heredado(eval_id, id_vm)
            if resultado:
                resultados.append(resultado)
                _guardar_riesgo_heredado(eval_id, resultado)
        
        except Exception as e:
            print(f"Error calculando herencia para {id_vm}: {e}")
    
    return resultados


def _guardar_resultado_concentracion(resultado: ResultadoConcentracion):
    """Guarda o actualiza el resultado de concentración"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar si existe
        cursor.execute('''
            SELECT id FROM RESULTADOS_CONCENTRACION 
            WHERE ID_Evaluacion = ? AND ID_Host = ?
        ''', [resultado.id_evaluacion, resultado.id_host])
        
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute('''
                UPDATE RESULTADOS_CONCENTRACION SET
                    Nombre_Host = ?,
                    Num_VMs_Dependientes = ?,
                    Blast_Radius = ?,
                    Factor_Concentracion = ?,
                    Impacto_D_Original = ?,
                    Impacto_D_Ajustado = ?,
                    Riesgo_Original = ?,
                    Riesgo_Ajustado = ?,
                    VMs_Criticas = ?,
                    Es_SPOF = ?,
                    Fecha_Calculo = ?
                WHERE ID_Evaluacion = ? AND ID_Host = ?
            ''', [
                resultado.nombre_host,
                resultado.num_vms_dependientes,
                resultado.blast_radius,
                resultado.factor_concentracion,
                resultado.impacto_d_original,
                resultado.impacto_d_ajustado,
                resultado.riesgo_original,
                resultado.riesgo_ajustado,
                json.dumps(resultado.vms_criticas, ensure_ascii=False),
                1 if resultado.es_spof else 0,
                resultado.fecha_calculo,
                resultado.id_evaluacion,
                resultado.id_host
            ])
        else:
            cursor.execute('''
                INSERT INTO RESULTADOS_CONCENTRACION 
                (ID_Evaluacion, ID_Host, Nombre_Host, Num_VMs_Dependientes,
                 Blast_Radius, Factor_Concentracion, Impacto_D_Original,
                 Impacto_D_Ajustado, Riesgo_Original, Riesgo_Ajustado,
                 VMs_Criticas, Es_SPOF, Fecha_Calculo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                resultado.id_evaluacion,
                resultado.id_host,
                resultado.nombre_host,
                resultado.num_vms_dependientes,
                resultado.blast_radius,
                resultado.factor_concentracion,
                resultado.impacto_d_original,
                resultado.impacto_d_ajustado,
                resultado.riesgo_original,
                resultado.riesgo_ajustado,
                json.dumps(resultado.vms_criticas, ensure_ascii=False),
                1 if resultado.es_spof else 0,
                resultado.fecha_calculo
            ])
        
        conn.commit()


def _guardar_riesgo_heredado(eval_id: str, resultado: RiesgoHeredado):
    """Guarda o actualiza el riesgo heredado de una VM"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM RIESGO_HEREDADO 
            WHERE ID_Evaluacion = ? AND ID_Activo = ?
        ''', [eval_id, resultado.id_activo])
        
        exists = cursor.fetchone()
        fecha = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if exists:
            cursor.execute('''
                UPDATE RIESGO_HEREDADO SET
                    ID_Host = ?,
                    Riesgo_VM_Propio = ?,
                    Riesgo_Host = ?,
                    Riesgo_Heredado = ?,
                    Riesgo_Final = ?,
                    Nivel_Riesgo_Final = ?,
                    Ajuste_Aplicado = ?,
                    Justificacion = ?,
                    Fecha_Calculo = ?
                WHERE ID_Evaluacion = ? AND ID_Activo = ?
            ''', [
                resultado.id_host,
                resultado.riesgo_vm_propio,
                resultado.riesgo_host,
                resultado.riesgo_heredado,
                resultado.riesgo_final,
                resultado.nivel_riesgo_final,
                1 if resultado.ajuste_aplicado else 0,
                resultado.justificacion,
                fecha,
                eval_id,
                resultado.id_activo
            ])
        else:
            cursor.execute('''
                INSERT INTO RIESGO_HEREDADO 
                (ID_Evaluacion, ID_Activo, ID_Host, Riesgo_VM_Propio,
                 Riesgo_Host, Riesgo_Heredado, Riesgo_Final,
                 Nivel_Riesgo_Final, Ajuste_Aplicado, Justificacion, Fecha_Calculo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                eval_id,
                resultado.id_activo,
                resultado.id_host,
                resultado.riesgo_vm_propio,
                resultado.riesgo_host,
                resultado.riesgo_heredado,
                resultado.riesgo_final,
                resultado.nivel_riesgo_final,
                1 if resultado.ajuste_aplicado else 0,
                resultado.justificacion,
                fecha
            ])
        
        conn.commit()


# ==================== CONSULTAS ====================

def get_hosts_spof(eval_id: str) -> pd.DataFrame:
    """Obtiene los hosts identificados como SPOF"""
    try:
        with get_connection() as conn:
            return pd.read_sql_query('''
                SELECT * FROM RESULTADOS_CONCENTRACION
                WHERE ID_Evaluacion = ? AND Es_SPOF = 1
                ORDER BY Blast_Radius DESC
            ''', conn, params=[eval_id])
    except:
        return pd.DataFrame()


def get_ranking_hosts_blast_radius(eval_id: str) -> pd.DataFrame:
    """Obtiene ranking de hosts por blast radius"""
    try:
        with get_connection() as conn:
            return pd.read_sql_query('''
                SELECT 
                    ID_Host,
                    Nombre_Host,
                    Num_VMs_Dependientes,
                    Blast_Radius,
                    Factor_Concentracion,
                    Impacto_D_Original,
                    Impacto_D_Ajustado,
                    Riesgo_Ajustado,
                    Es_SPOF
                FROM RESULTADOS_CONCENTRACION
                WHERE ID_Evaluacion = ?
                ORDER BY Blast_Radius DESC
            ''', conn, params=[eval_id])
    except:
        return pd.DataFrame()


def get_vms_con_riesgo_heredado(eval_id: str) -> pd.DataFrame:
    """Obtiene VMs cuyo riesgo fue ajustado por herencia"""
    try:
        with get_connection() as conn:
            return pd.read_sql_query('''
                SELECT * FROM RIESGO_HEREDADO
                WHERE ID_Evaluacion = ? AND Ajuste_Aplicado = 1
                ORDER BY Riesgo_Final DESC
            ''', conn, params=[eval_id])
    except:
        return pd.DataFrame()


def get_resumen_concentracion(eval_id: str) -> Dict:
    """Obtiene resumen de concentración para dashboard"""
    hosts_df = get_ranking_hosts_blast_radius(eval_id)
    vms_heredadas = get_vms_con_riesgo_heredado(eval_id)
    
    if hosts_df.empty:
        return {
            "total_hosts": 0,
            "hosts_spof": 0,
            "max_blast_radius": 0,
            "vms_afectadas": 0,
            "riesgo_promedio_ajustado": 0
        }
    
    return {
        "total_hosts": len(hosts_df),
        "hosts_spof": int(hosts_df["Es_SPOF"].sum()) if "Es_SPOF" in hosts_df.columns else 0,
        "max_blast_radius": float(hosts_df["Blast_Radius"].max()) if not hosts_df.empty else 0,
        "vms_afectadas": len(vms_heredadas),
        "riesgo_promedio_ajustado": float(hosts_df["Riesgo_Ajustado"].mean()) if not hosts_df.empty else 0
    }
