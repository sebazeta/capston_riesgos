"""
MÓDULO DE DEGRADACIÓN MAGERIT
==============================
Implementa el concepto de DEGRADACIÓN según Marco Teórico MAGERIT:
- Degradación por dimensión (D, I, C) con valores [0.0 - 1.0]
- Captura manual y/o sugerencia IA
- Cálculo correcto: IMPACTO = CRITICIDAD × MAX(Deg_D, Deg_I, Deg_C)
"""
import json
import datetime as dt
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from services.database_service import get_connection


@dataclass
class DegradacionAmenaza:
    """Degradación causada por una amenaza sobre un activo"""
    id_evaluacion: str
    id_activo: str
    codigo_amenaza: str
    degradacion_d: float  # 0.0 - 1.0
    degradacion_i: float  # 0.0 - 1.0  
    degradacion_c: float  # 0.0 - 1.0
    justificacion: str = ""
    fuente: str = "manual"  # "manual" o "IA"
    
    @property
    def degradacion_maxima(self) -> float:
        """MAX(Deg_D, Deg_I, Deg_C) - usado para cálculo de impacto"""
        return max(self.degradacion_d, self.degradacion_i, self.degradacion_c)
    
    def to_dict(self) -> Dict:
        return asdict(self)


# =============================================================================
# FUNCIONES CRUD PARA DEGRADACIÓN
# =============================================================================

def obtener_degradacion(eval_id: str, activo_id: str, codigo_amenaza: str) -> Optional[DegradacionAmenaza]:
    """Obtiene la degradación registrada para una amenaza sobre un activo"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT Degradacion_D, Degradacion_I, Degradacion_C, 
                       Justificacion, Fuente
                FROM DEGRADACION_AMENAZAS
                WHERE ID_Evaluacion = ? AND ID_Activo = ? AND Codigo_Amenaza = ?
            ''', [eval_id, activo_id, codigo_amenaza])
            row = cursor.fetchone()
            
            if row:
                return DegradacionAmenaza(
                    id_evaluacion=eval_id,
                    id_activo=activo_id,
                    codigo_amenaza=codigo_amenaza,
                    degradacion_d=row[0],
                    degradacion_i=row[1],
                    degradacion_c=row[2],
                    justificacion=row[3] or "",
                    fuente=row[4] or "manual"
                )
            return None
    except Exception as e:
        print(f"Error obteniendo degradación: {e}")
        return None


def guardar_degradacion(deg: DegradacionAmenaza) -> bool:
    """Guarda o actualiza la degradación de una amenaza"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO DEGRADACION_AMENAZAS 
                (ID_Evaluacion, ID_Activo, Codigo_Amenaza, 
                 Degradacion_D, Degradacion_I, Degradacion_C,
                 Justificacion, Fuente, Fecha_Registro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                deg.id_evaluacion,
                deg.id_activo,
                deg.codigo_amenaza,
                deg.degradacion_d,
                deg.degradacion_i,
                deg.degradacion_c,
                deg.justificacion,
                deg.fuente,
                dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])
        return True
    except Exception as e:
        print(f"Error guardando degradación: {e}")
        return False


def obtener_degradaciones_activo(eval_id: str, activo_id: str) -> List[DegradacionAmenaza]:
    """Obtiene todas las degradaciones para un activo en una evaluación"""
    degradaciones = []
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT Codigo_Amenaza, Degradacion_D, Degradacion_I, Degradacion_C,
                       Justificacion, Fuente
                FROM DEGRADACION_AMENAZAS
                WHERE ID_Evaluacion = ? AND ID_Activo = ?
            ''', [eval_id, activo_id])
            
            for row in cursor.fetchall():
                degradaciones.append(DegradacionAmenaza(
                    id_evaluacion=eval_id,
                    id_activo=activo_id,
                    codigo_amenaza=row[0],
                    degradacion_d=row[1],
                    degradacion_i=row[2],
                    degradacion_c=row[3],
                    justificacion=row[4] or "",
                    fuente=row[5] or "manual"
                ))
    except Exception as e:
        print(f"Error obteniendo degradaciones: {e}")
    return degradaciones


def eliminar_degradacion(eval_id: str, activo_id: str, codigo_amenaza: str) -> bool:
    """Elimina una degradación específica"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM DEGRADACION_AMENAZAS
                WHERE ID_Evaluacion = ? AND ID_Activo = ? AND Codigo_Amenaza = ?
            ''', [eval_id, activo_id, codigo_amenaza])
        return True
    except Exception as e:
        print(f"Error eliminando degradación: {e}")
        return False


# =============================================================================
# CÁLCULOS CON DEGRADACIÓN (FÓRMULAS CORRECTAS MAGERIT)
# =============================================================================

def calcular_impacto_con_degradacion(criticidad: int, degradacion: DegradacionAmenaza) -> float:
    """
    FÓRMULA CORRECTA MAGERIT:
    IMPACTO = CRITICIDAD × MAX(Deg_D, Deg_I, Deg_C)
    
    Args:
        criticidad: Valor de criticidad del activo (1-5), donde CRITICIDAD = MAX(D, I, C)
        degradacion: Objeto DegradacionAmenaza con los valores de degradación
        
    Returns:
        float: Valor de impacto (0.0 - 5.0)
    """
    return criticidad * degradacion.degradacion_maxima


def calcular_riesgo_con_degradacion(
    frecuencia: int,
    criticidad: int,
    degradacion: DegradacionAmenaza
) -> float:
    """
    FÓRMULA CORRECTA MAGERIT:
    RIESGO = FRECUENCIA × IMPACTO
    IMPACTO = CRITICIDAD × MAX(Deg_D, Deg_I, Deg_C)
    
    Args:
        frecuencia: Frecuencia de la amenaza (1-5)
        criticidad: MAX(D, I, C) del activo (1-5)
        degradacion: Degradación de la amenaza
        
    Returns:
        float: Valor de riesgo (0.0 - 25.0)
    """
    impacto = calcular_impacto_con_degradacion(criticidad, degradacion)
    return frecuencia * impacto


def calcular_riesgo_activo_dual(riesgos: List[float]) -> Dict[str, float]:
    """
    Calcula ambas agregaciones de riesgo por activo:
    - PROMEDIO: Para visión general balanceada
    - MÁXIMO: Para caso pesimista (riesgo más alto)
    
    Args:
        riesgos: Lista de valores de riesgo para cada amenaza del activo
        
    Returns:
        Dict con 'promedio' y 'maximo'
    """
    if not riesgos:
        return {"promedio": 0.0, "maximo": 0.0}
    
    return {
        "promedio": round(sum(riesgos) / len(riesgos), 2),
        "maximo": round(max(riesgos), 2)
    }


def calcular_riesgo_objetivo(riesgo_actual: float, factor: float = 0.5) -> float:
    """
    Calcula el riesgo objetivo según la política de tratamiento.
    
    FÓRMULA: Riesgo_Objetivo = Riesgo_Actual × Factor
    
    Args:
        riesgo_actual: Valor de riesgo residual actual
        factor: Factor de reducción objetivo (default 0.5 = reducir 50%)
        
    Returns:
        float: Valor de riesgo objetivo
    """
    return round(riesgo_actual * factor, 2)


def supera_limite(riesgo: float, limite: float = 7.0) -> bool:
    """
    Verifica si un riesgo supera el límite aceptable.
    
    Args:
        riesgo: Valor de riesgo a evaluar
        limite: Límite de riesgo aceptable (default 7.0 = medio)
        
    Returns:
        bool: True si supera el límite
    """
    return riesgo > limite


# =============================================================================
# SUGERENCIA IA DE DEGRADACIÓN
# =============================================================================

def sugerir_degradacion_ia(
    tipo_activo: str,
    codigo_amenaza: str,
    tipo_amenaza: str,
    contexto_respuestas: Dict = None
) -> DegradacionAmenaza:
    """
    Sugiere valores de degradación basados en heurísticas.
    Esta función puede ser mejorada con IA real en el futuro.
    
    Reglas heurísticas actuales:
    - Amenazas de tipo "Desastres naturales" → Alta degradación D, media I, baja C
    - Amenazas de tipo "Errores y fallos" → Media degradación en todas
    - Amenazas de tipo "Ataques intencionados" → Alta degradación C, alta I
    - Activos físicos → Mayor impacto en D
    - Activos virtuales → Mayor impacto en C e I
    """
    # Valores base
    deg_d = 0.5
    deg_i = 0.5
    deg_c = 0.5
    
    # Ajuste por tipo de amenaza
    tipo_amenaza_upper = tipo_amenaza.upper() if tipo_amenaza else ""
    
    if "DESASTRE" in tipo_amenaza_upper or "NATURAL" in tipo_amenaza_upper:
        deg_d = 0.9
        deg_i = 0.4
        deg_c = 0.2
    elif "ERROR" in tipo_amenaza_upper or "FALLO" in tipo_amenaza_upper:
        deg_d = 0.6
        deg_i = 0.5
        deg_c = 0.3
    elif "ATAQUE" in tipo_amenaza_upper or "INTENCION" in tipo_amenaza_upper:
        deg_d = 0.5
        deg_i = 0.8
        deg_c = 0.9
    elif "FUGA" in tipo_amenaza_upper or "ACCESO" in tipo_amenaza_upper:
        deg_d = 0.2
        deg_i = 0.3
        deg_c = 0.9
        
    # Ajuste por tipo de activo
    tipo_activo_upper = tipo_activo.upper() if tipo_activo else ""
    
    if "FISICO" in tipo_activo_upper or "FÍSICO" in tipo_activo_upper:
        deg_d = min(1.0, deg_d * 1.2)  # Mayor impacto en disponibilidad
    elif "VIRTUAL" in tipo_activo_upper or "DATO" in tipo_activo_upper:
        deg_c = min(1.0, deg_c * 1.2)  # Mayor impacto en confidencialidad
        deg_i = min(1.0, deg_i * 1.1)  # Mayor impacto en integridad
    
    justificacion = f"Sugerencia automática basada en tipo de amenaza '{tipo_amenaza}' y tipo de activo '{tipo_activo}'"
    
    return DegradacionAmenaza(
        id_evaluacion="",
        id_activo="",
        codigo_amenaza=codigo_amenaza,
        degradacion_d=round(deg_d, 2),
        degradacion_i=round(deg_i, 2),
        degradacion_c=round(deg_c, 2),
        justificacion=justificacion,
        fuente="IA"
    )


# =============================================================================
# CONFIGURACIÓN DE EVALUACIÓN
# =============================================================================

def obtener_limite_evaluacion(eval_id: str) -> float:
    """Obtiene el límite de riesgo configurado para una evaluación"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT Limite_Riesgo FROM EVALUACIONES WHERE ID_Evaluacion = ?',
                [eval_id]
            )
            row = cursor.fetchone()
            return row[0] if row and row[0] else 7.0
    except Exception as e:
        print(f"Error obteniendo límite: {e}")
        return 7.0


def actualizar_limite_evaluacion(eval_id: str, limite: float) -> bool:
    """Actualiza el límite de riesgo para una evaluación"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE EVALUACIONES SET Limite_Riesgo = ? WHERE ID_Evaluacion = ?',
                [limite, eval_id]
            )
        return True
    except Exception as e:
        print(f"Error actualizando límite: {e}")
        return False


def obtener_factor_objetivo(eval_id: str) -> float:
    """Obtiene el factor de riesgo objetivo para una evaluación"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT Factor_Objetivo FROM EVALUACIONES WHERE ID_Evaluacion = ?',
                [eval_id]
            )
            row = cursor.fetchone()
            return row[0] if row and row[0] else 0.5
    except Exception as e:
        print(f"Error obteniendo factor: {e}")
        return 0.5


# =============================================================================
# VALIDACIONES DE TRAZABILIDAD
# =============================================================================

def validar_trazabilidad_completa(eval_id: str, activo_id: str) -> Dict[str, Any]:
    """
    Valida que exista trazabilidad completa:
    Activo → Riesgo → Amenaza → Vulnerabilidad → Salvaguarda
    
    Returns:
        Dict con resultados de validación
    """
    resultado = {
        "valido": True,
        "errores": [],
        "advertencias": []
    }
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Verificar que el activo existe
            cursor.execute(
                'SELECT COUNT(*) FROM INVENTARIO_ACTIVOS WHERE ID_Activo = ?',
                [activo_id]
            )
            if cursor.fetchone()[0] == 0:
                resultado["valido"] = False
                resultado["errores"].append(f"Activo {activo_id} no existe en inventario")
                return resultado
            
            # 2. Verificar que hay degradaciones registradas para las amenazas
            cursor.execute('''
                SELECT COUNT(*) FROM DEGRADACION_AMENAZAS
                WHERE ID_Evaluacion = ? AND ID_Activo = ?
            ''', [eval_id, activo_id])
            num_degradaciones = cursor.fetchone()[0]
            
            # 3. Verificar resultados MAGERIT
            cursor.execute('''
                SELECT Amenazas_JSON, Controles_JSON FROM RESULTADOS_MAGERIT
                WHERE ID_Evaluacion = ? AND ID_Activo = ?
            ''', [eval_id, activo_id])
            row = cursor.fetchone()
            
            if row:
                amenazas_json = row[0]
                if amenazas_json:
                    amenazas = json.loads(amenazas_json)
                    num_amenazas = len(amenazas)
                    
                    # Advertencia si hay amenazas sin degradación registrada
                    if num_degradaciones < num_amenazas:
                        resultado["advertencias"].append(
                            f"Hay {num_amenazas} amenazas pero solo {num_degradaciones} degradaciones registradas"
                        )
                    
                    # Verificar que cada amenaza tiene controles
                    amenazas_sin_controles = []
                    for a in amenazas:
                        if not a.get("controles_recomendados"):
                            amenazas_sin_controles.append(a.get("codigo", "?"))
                    
                    if amenazas_sin_controles:
                        resultado["advertencias"].append(
                            f"Amenazas sin controles recomendados: {', '.join(amenazas_sin_controles)}"
                        )
            else:
                resultado["advertencias"].append("No hay resultados MAGERIT para este activo")
                
    except Exception as e:
        resultado["valido"] = False
        resultado["errores"].append(f"Error en validación: {str(e)}")
    
    return resultado


# =============================================================================
# FUNCIONES DE REPORTE
# =============================================================================

def obtener_resumen_riesgos_evaluacion(eval_id: str) -> Dict[str, Any]:
    """
    Obtiene un resumen de riesgos para toda la evaluación.
    Incluye ambas métricas: promedio y máximo.
    """
    resumen = {
        "total_activos": 0,
        "activos_evaluados": 0,
        "activos_sobre_limite": 0,
        "riesgo_promedio_global": 0.0,
        "riesgo_maximo_global": 0.0,
        "distribucion_niveles": {
            "CRITICO": 0,
            "ALTO": 0,
            "MEDIO": 0,
            "BAJO": 0,
            "MUY BAJO": 0
        },
        "limite_configurado": obtener_limite_evaluacion(eval_id)
    }
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Total activos en evaluación
            cursor.execute('''
                SELECT COUNT(*) FROM INVENTARIO_ACTIVOS
                WHERE ID_Evaluacion = ?
            ''', [eval_id])
            resumen["total_activos"] = cursor.fetchone()[0]
            
            # Obtener resultados
            cursor.execute('''
                SELECT Riesgo_Inherente, Riesgo_Residual, Nivel_Riesgo,
                       Riesgo_Promedio, Riesgo_Maximo, Supera_Limite
                FROM RESULTADOS_MAGERIT
                WHERE ID_Evaluacion = ?
            ''', [eval_id])
            
            riesgos = []
            for row in cursor.fetchall():
                resumen["activos_evaluados"] += 1
                
                riesgo_residual = row[1] or 0
                nivel = row[2] or "MEDIO"
                supera = row[5] or 0
                
                riesgos.append(riesgo_residual)
                resumen["activos_sobre_limite"] += supera
                
                if nivel in resumen["distribucion_niveles"]:
                    resumen["distribucion_niveles"][nivel] += 1
            
            if riesgos:
                resumen["riesgo_promedio_global"] = round(sum(riesgos) / len(riesgos), 2)
                resumen["riesgo_maximo_global"] = round(max(riesgos), 2)
                
    except Exception as e:
        print(f"Error obteniendo resumen: {e}")
    
    return resumen
