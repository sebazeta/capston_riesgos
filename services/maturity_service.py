"""
SERVICIO DE CÁLCULO DE NIVEL DE MADUREZ DE CIBERSEGURIDAD
==========================================================
Calcula:
- Nivel de madurez por evaluación (1-5)
- Puntuación numérica (0-100)
- Desglose por dominios ISO 27002
- Comparativa entre evaluaciones
- Relación con reducción de riesgos

Niveles de Madurez (basado en CMMI/ISO):
1 - Inicial: Procesos ad-hoc, sin controles formales
2 - Básico: Controles básicos implementados, documentación mínima
3 - Definido: Procesos documentados, controles estandarizados
4 - Gestionado: Controles medidos y monitoreados
5 - Optimizado: Mejora continua, controles automatizados
"""
import json
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from services.database_service import read_table, get_connection


# ==================== MODELOS DE DATOS ====================

@dataclass
class ResultadoMadurez:
    """Resultado del cálculo de madurez para una evaluación"""
    id_evaluacion: str
    puntuacion_total: float  # 0-100
    nivel_madurez: int  # 1-5
    nombre_nivel: str  # Inicial, Básico, Definido, Gestionado, Optimizado
    
    # Desglose por dominios ISO 27002:2022
    dominio_organizacional: float  # % controles 5.x
    dominio_personas: float  # % controles 6.x  
    dominio_fisico: float  # % controles 7.x
    dominio_tecnologico: float  # % controles 8.x
    
    # Métricas de riesgo
    pct_controles_implementados: float
    pct_controles_medidos: float
    pct_riesgos_criticos_mitigados: float
    pct_activos_evaluados: float
    
    # Resumen de controles
    total_controles_posibles: int
    controles_implementados: int
    controles_parciales: int
    controles_no_implementados: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ComparativaMadurez:
    """Comparativa de madurez entre dos evaluaciones"""
    eval_1: str
    eval_2: str
    madurez_1: ResultadoMadurez
    madurez_2: ResultadoMadurez
    
    delta_puntuacion: float
    delta_nivel: int
    delta_riesgo_residual: float
    
    mejoras: List[str]  # Áreas que mejoraron
    retrocesos: List[str]  # Áreas que empeoraron
    recomendaciones: List[str]


# ==================== MAPEO DE CONTROLES A DOMINIOS ====================

def get_dominio_control(codigo: str) -> str:
    """Determina el dominio de un control ISO 27002 por su código"""
    if codigo.startswith("5."):
        return "organizacional"
    elif codigo.startswith("6."):
        return "personas"
    elif codigo.startswith("7."):
        return "fisico"
    elif codigo.startswith("8."):
        return "tecnologico"
    return "otro"


# ==================== MAPEO AMPLIADO PREGUNTAS -> CONTROLES ====================

# Mapeo detallado de preguntas del cuestionario a controles ISO 27002
# Incluye nivel de implementación implícito basado en respuesta

MAPEO_PREGUNTAS_CONTROLES_DETALLADO = {
    # Bloque A - Impacto Operativo / BIA
    "A01": {
        "controles": ["5.29", "5.30"],
        "descripcion": "RTO/RPO -> Continuidad de negocio"
    },
    "A02": {
        "controles": ["5.9", "5.10"],
        "descripcion": "Dependencias -> Inventario de activos"
    },
    "A03": {
        "controles": ["8.13"],
        "descripcion": "Tolerancia pérdida datos -> Respaldos"
    },
    "A04": {
        "controles": ["5.12", "5.13"],
        "descripcion": "Clasificación información"
    },
    "A05": {
        "controles": ["5.29", "5.24"],
        "descripcion": "Impacto financiero -> Continuidad, Gestión incidentes"
    },
    
    # Bloque B - Continuidad y Recuperación
    "B01": {
        "controles": ["8.14", "5.30"],
        "descripcion": "Failover/Redundancia -> Alta disponibilidad"
    },
    "B02": {
        "controles": ["8.13"],
        "descripcion": "Backups implementados"
    },
    "B03": {
        "controles": ["8.13", "5.30"],
        "descripcion": "Restauración probada"
    },
    "B04": {
        "controles": ["7.11", "7.12"],
        "descripcion": "UPS/Energía -> Servicios de apoyo"
    },
    "B05": {
        "controles": ["5.30", "5.29"],
        "descripcion": "Plan DRP documentado"
    },
    
    # Bloque C - Controles de Acceso y Autenticación
    "C01": {
        "controles": ["5.15", "5.16", "5.17", "8.5"],
        "descripcion": "Control de acceso, Gestión identidades, MFA"
    },
    "C02": {
        "controles": ["8.8", "8.19"],
        "descripcion": "Parches -> Gestión vulnerabilidades"
    },
    "C03": {
        "controles": ["8.16"],
        "descripcion": "Monitoreo de actividad"
    },
    "C04": {
        "controles": ["8.15"],
        "descripcion": "Logging/Registros de auditoría"
    },
    "C05": {
        "controles": ["8.22"],
        "descripcion": "Segmentación de red"
    },
    "C06": {
        "controles": ["5.18", "8.2"],
        "descripcion": "Privilegios mínimos"
    },
    "C07": {
        "controles": ["5.17"],
        "descripcion": "Gestión de contraseñas"
    },
    
    # Bloque D - Ciberseguridad y Protección
    "D01": {
        "controles": ["8.7"],
        "descripcion": "Antimalware"
    },
    "D02": {
        "controles": ["8.24"],
        "descripcion": "Cifrado"
    },
    "D03": {
        "controles": ["8.8", "8.34"],
        "descripcion": "Análisis vulnerabilidades, Pentesting"
    },
    "D04": {
        "controles": ["8.13", "8.7", "5.24"],
        "descripcion": "Protección ransomware"
    },
    "D05": {
        "controles": ["8.23"],
        "descripcion": "Filtrado web"
    },
    "D06": {
        "controles": ["5.24", "5.26"],
        "descripcion": "Respuesta a incidentes"
    },
    
    # Bloque E - Exposición y Dependencias Externas
    "E01": {
        "controles": ["8.20", "8.21"],
        "descripcion": "Exposición Internet -> Seguridad de red"
    },
    "E02": {
        "controles": ["7.1", "7.2", "7.3"],
        "descripcion": "Seguridad física"
    },
    "E03": {
        "controles": ["5.19", "5.21", "5.22"],
        "descripcion": "Proveedores y terceros"
    },
    "E04": {
        "controles": ["8.20"],
        "descripcion": "Seguridad de acceso remoto"
    },
    
    # Bloque F - Gobierno y Gestión (si existe)
    "F01": {
        "controles": ["5.1", "5.2"],
        "descripcion": "Políticas de seguridad"
    },
    "F02": {
        "controles": ["5.3", "5.4"],
        "descripcion": "Roles y responsabilidades"
    },
    "F03": {
        "controles": ["5.31", "5.36"],
        "descripcion": "Cumplimiento legal"
    },
}


# ==================== NIVELES DE IMPLEMENTACIÓN ====================

def determinar_nivel_implementacion(valor_respuesta: int) -> Tuple[str, float]:
    """
    Determina el nivel de implementación de un control basado en respuesta.
    
    IMPORTANTE: Solo respuestas >= 3 indican implementación real.
    Las respuestas del cuestionario típicamente significan:
    1 = No implementado / No existe / No aplica
    2 = Parcial / Ad-hoc / En proceso
    3 = Implementado / Documentado
    4 = Implementado y medido / Optimizado
    
    CORRECCIÓN: No contar como "implementado" las respuestas básicas (1-2)
    
    Returns:
        (nivel_texto, efectividad 0-1)
    """
    if valor_respuesta <= 1:
        return "No implementado", 0.0
    elif valor_respuesta == 2:
        return "Parcial", 0.25  # Reducido de 0.33 a 0.25
    elif valor_respuesta == 3:
        return "Implementado", 0.75  # Ajustado de 0.66 a 0.75
    else:  # valor >= 4
        return "Implementado y medido", 1.0


# ==================== CÁLCULO DE CONTROLES EXISTENTES ====================

def analizar_controles_desde_respuestas(respuestas: pd.DataFrame) -> Dict:
    """
    Analiza las respuestas del cuestionario para identificar controles existentes
    con su nivel de implementación.
    
    Returns:
        {
            "controles": {codigo: {nivel, efectividad, pregunta}},
            "por_dominio": {dominio: [controles]},
            "metricas": {total, implementados, parciales, no_implementados}
        }
    """
    if respuestas.empty:
        return {
            "controles": {},
            "por_dominio": {"organizacional": [], "personas": [], "fisico": [], "tecnologico": []},
            "metricas": {"total": 0, "implementados": 0, "parciales": 0, "no_implementados": 0}
        }
    
    controles_encontrados = {}
    controles_por_dominio = {
        "organizacional": [],
        "personas": [],
        "fisico": [],
        "tecnologico": []
    }
    
    for _, resp in respuestas.iterrows():
        id_pregunta = str(resp.get("ID_Pregunta", ""))
        valor = int(resp.get("Valor_Numerico", 1))
        pregunta_texto = str(resp.get("Pregunta", ""))
        
        # Extraer código de pregunta (ej: PF-A01 -> A01, PV-B02 -> B02)
        partes = id_pregunta.split("-")
        if len(partes) >= 2:
            codigo_pregunta = partes[-1]  # A01, B02, etc.
        else:
            codigo_pregunta = id_pregunta
        
        # Buscar controles asociados
        if codigo_pregunta in MAPEO_PREGUNTAS_CONTROLES_DETALLADO:
            info_mapeo = MAPEO_PREGUNTAS_CONTROLES_DETALLADO[codigo_pregunta]
            controles = info_mapeo["controles"]
            descripcion = info_mapeo["descripcion"]
            
            nivel_texto, efectividad = determinar_nivel_implementacion(valor)
            
            for ctrl in controles:
                dominio = get_dominio_control(ctrl)
                
                # Guardar el mejor nivel encontrado para cada control
                if ctrl not in controles_encontrados:
                    controles_encontrados[ctrl] = {
                        "nivel": nivel_texto,
                        "efectividad": efectividad,
                        "pregunta": pregunta_texto,
                        "codigo_pregunta": codigo_pregunta,
                        "descripcion": descripcion,
                        "dominio": dominio
                    }
                else:
                    # Si ya existe, quedarnos con la mejor efectividad
                    if efectividad > controles_encontrados[ctrl]["efectividad"]:
                        controles_encontrados[ctrl]["efectividad"] = efectividad
                        controles_encontrados[ctrl]["nivel"] = nivel_texto
                
                # Agregar al dominio correspondiente
                if ctrl not in controles_por_dominio.get(dominio, []):
                    controles_por_dominio.setdefault(dominio, []).append(ctrl)
    
    # Calcular métricas
    total = len(controles_encontrados)
    implementados = sum(1 for c in controles_encontrados.values() if c["efectividad"] >= 0.75)
    parciales = sum(1 for c in controles_encontrados.values() if 0 < c["efectividad"] < 0.75)
    no_implementados = sum(1 for c in controles_encontrados.values() if c["efectividad"] == 0)
    
    return {
        "controles": controles_encontrados,
        "por_dominio": controles_por_dominio,
        "metricas": {
            "total": total,
            "implementados": implementados,
            "parciales": parciales,
            "no_implementados": no_implementados
        }
    }


# ==================== CÁLCULO DE MADUREZ ====================

def calcular_madurez_evaluacion(eval_id: str) -> Optional[ResultadoMadurez]:
    """
    Calcula el nivel de madurez de ciberseguridad basado en DATOS REALES de la evaluación.
    
    NUEVA FÓRMULA SIMPLIFICADA (0-100):
    - 40% -> Salvaguardas identificadas y recomendadas
    - 30% -> Riesgos identificados y analizados
    - 30% -> Activos evaluados completamente (con valoración DIC)
    
    Returns:
        ResultadoMadurez o None si no hay datos suficientes
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Total de activos en la evaluación
            cursor.execute(
                "SELECT COUNT(*) FROM INVENTARIO_ACTIVOS WHERE ID_Evaluacion = ?",
                [eval_id]
            )
            total_activos = cursor.fetchone()[0]
            
            if total_activos == 0:
                return None
            
            # 2. Activos con valoración DIC completa
            cursor.execute(
                "SELECT COUNT(*) FROM IDENTIFICACION_VALORACION WHERE ID_Evaluacion = ?",
                [eval_id]
            )
            activos_valorados = cursor.fetchone()[0]
            
            # 3. Activos con riesgos identificados (vulnerabilidades + amenazas)
            cursor.execute(
                "SELECT COUNT(DISTINCT ID_Activo) FROM RIESGO_AMENAZA WHERE ID_Evaluacion = ?",
                [eval_id]
            )
            activos_con_riesgos = cursor.fetchone()[0]
            
            # 4. Total de riesgos identificados
            cursor.execute(
                "SELECT COUNT(*) FROM RIESGO_AMENAZA WHERE ID_Evaluacion = ?",
                [eval_id]
            )
            total_riesgos = cursor.fetchone()[0]
            
            # 5. Total de salvaguardas recomendadas
            cursor.execute(
                "SELECT COUNT(*) FROM SALVAGUARDAS WHERE ID_Evaluacion = ?",
                [eval_id]
            )
            total_salvaguardas = cursor.fetchone()[0]
            
            # 6. Promedio de criticidad de activos (0-10)
            cursor.execute(
                """SELECT AVG(Criticidad) 
                   FROM IDENTIFICACION_VALORACION 
                   WHERE ID_Evaluacion = ?""",
                [eval_id]
            )
            criticidad_promedio = cursor.fetchone()[0] or 0
            
            # 7. Promedio de riesgo actual
            cursor.execute(
                """SELECT AVG(Riesgo_Actual) 
                   FROM RIESGO_ACTIVOS 
                   WHERE ID_Evaluacion = ?""",
                [eval_id]
            )
            riesgo_promedio = cursor.fetchone()[0] or 0
            
            # ===== CÁLCULO DE PUNTUACIONES =====
            
            # Componente 1: Salvaguardas (40%)
            # Lógica: Por cada activo debería haber al menos 3-5 salvaguardas
            # Si tengo salvaguardas >= activos * 3 = 100%
            salvaguardas_esperadas = total_activos * 3
            pct_salvaguardas = min(100, (total_salvaguardas / salvaguardas_esperadas * 100)) if salvaguardas_esperadas > 0 else 0
            
            # Componente 2: Riesgos identificados (30%)
            # Lógica: Por cada activo debería haber al menos 5 riesgos identificados
            # Si tengo riesgos >= activos * 5 = 100%
            riesgos_esperados = total_activos * 5
            pct_riesgos = min(100, (total_riesgos / riesgos_esperados * 100)) if riesgos_esperados > 0 else 0
            
            # Componente 3: Activos evaluados (30%)
            # Lógica: % de activos con valoración DIC completa
            pct_activos_evaluados = (activos_valorados / total_activos * 100) if total_activos > 0 else 0
            
            # ===== PUNTUACIÓN TOTAL =====
            puntuacion = (
                pct_salvaguardas * 0.40 +
                pct_riesgos * 0.30 +
                pct_activos_evaluados * 0.30
            )
            
            # ===== DETERMINAR NIVEL DE MADUREZ =====
            # Umbrales ajustados basados en completitud de la evaluación
            if puntuacion >= 80:
                nivel = 5
                nombre_nivel = "Optimizado"
            elif puntuacion >= 60:
                nivel = 4
                nombre_nivel = "Gestionado"
            elif puntuacion >= 40:
                nivel = 3
                nombre_nivel = "Definido"
            elif puntuacion >= 20:
                nivel = 2
                nombre_nivel = "Básico"
            else:
                nivel = 1
                nombre_nivel = "Inicial"
            
            # ===== CREAR RESULTADO =====
            return ResultadoMadurez(
                id_evaluacion=eval_id,
                puntuacion_total=round(puntuacion, 1),
                nivel_madurez=nivel,
                nombre_nivel=nombre_nivel,
                dominio_organizacional=0,  # No usado
                dominio_personas=0,  # No usado
                dominio_fisico=0,  # No usado
                dominio_tecnologico=0,  # No usado
                pct_controles_implementados=round(pct_salvaguardas, 1),
                pct_controles_medidos=round(pct_riesgos, 1),
                pct_riesgos_criticos_mitigados=round(pct_activos_evaluados, 1),
                pct_activos_evaluados=round(pct_activos_evaluados, 1),
                total_controles_posibles=total_activos,
                controles_implementados=total_salvaguardas,
                controles_parciales=total_riesgos,
                controles_no_implementados=total_activos - activos_valorados
            )
    
    except Exception as e:
        print(f"Error calculando madurez: {e}")
        import traceback
        traceback.print_exc()
        return None


def guardar_madurez(resultado) -> bool:
    """Guarda el resultado de madurez en la base de datos.
    Acepta tanto ResultadoMadurez como dict.
    """
    try:
        # Convertir diccionario a valores accesibles
        if isinstance(resultado, dict):
            r = resultado
            get_val = lambda key, default=0: r.get(key, default)
            id_evaluacion = get_val("ID_Evaluacion", get_val("id_evaluacion", ""))
            puntuacion_total = get_val("Puntuacion_Total", get_val("puntuacion_total", 0))
            nivel_madurez = get_val("Nivel_Madurez", get_val("nivel_madurez", 1))
            nombre_nivel = get_val("Nombre_Nivel", get_val("nombre_nivel", "Inicial"))
            dominio_organizacional = get_val("Dominio_Organizacional", get_val("dominio_organizacional", 0))
            dominio_personas = get_val("Dominio_Personas", get_val("dominio_personas", 0))
            dominio_fisico = get_val("Dominio_Fisico", get_val("dominio_fisico", 0))
            dominio_tecnologico = get_val("Dominio_Tecnologico", get_val("dominio_tecnologico", 0))
            pct_controles_impl = get_val("Pct_Controles_Implementados", get_val("pct_controles_implementados", 0))
            pct_controles_med = get_val("Pct_Controles_Medidos", get_val("pct_controles_medidos", 0))
            pct_riesgos_mit = get_val("Pct_Riesgos_Criticos_Mitigados", get_val("pct_riesgos_criticos_mitigados", 0))
            pct_activos_eval = get_val("Pct_Activos_Evaluados", get_val("pct_activos_evaluados", 0))
            controles_impl = get_val("Controles_Implementados", get_val("controles_implementados", 0))
            controles_parc = get_val("Controles_Parciales", get_val("controles_parciales", 0))
            controles_no_impl = get_val("Controles_No_Implementados", get_val("controles_no_implementados", 0))
        else:
            # Es un ResultadoMadurez
            id_evaluacion = resultado.id_evaluacion
            puntuacion_total = resultado.puntuacion_total
            nivel_madurez = resultado.nivel_madurez
            nombre_nivel = resultado.nombre_nivel
            dominio_organizacional = resultado.dominio_organizacional
            dominio_personas = resultado.dominio_personas
            dominio_fisico = resultado.dominio_fisico
            dominio_tecnologico = resultado.dominio_tecnologico
            pct_controles_impl = resultado.pct_controles_implementados
            pct_controles_med = resultado.pct_controles_medidos
            pct_riesgos_mit = resultado.pct_riesgos_criticos_mitigados
            pct_activos_eval = resultado.pct_activos_evaluados
            controles_impl = resultado.controles_implementados
            controles_parc = resultado.controles_parciales
            controles_no_impl = resultado.controles_no_implementados
        
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Crear tabla si no existe
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS RESULTADOS_MADUREZ (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ID_Evaluacion TEXT UNIQUE,
                    Puntuacion_Total REAL,
                    Nivel_Madurez INTEGER,
                    Nombre_Nivel TEXT,
                    Dominio_Organizacional REAL,
                    Dominio_Personas REAL,
                    Dominio_Fisico REAL,
                    Dominio_Tecnologico REAL,
                    Pct_Controles_Implementados REAL,
                    Pct_Controles_Medidos REAL,
                    Pct_Riesgos_Mitigados REAL,
                    Pct_Activos_Evaluados REAL,
                    Controles_Implementados INTEGER,
                    Controles_Parciales INTEGER,
                    Controles_No_Implementados INTEGER,
                    Fecha_Calculo TEXT
                )
            ''')
            
            # Insertar o reemplazar
            cursor.execute('''
                INSERT OR REPLACE INTO RESULTADOS_MADUREZ (
                    ID_Evaluacion, Puntuacion_Total, Nivel_Madurez, Nombre_Nivel,
                    Dominio_Organizacional, Dominio_Personas, Dominio_Fisico, Dominio_Tecnologico,
                    Pct_Controles_Implementados, Pct_Controles_Medidos, Pct_Riesgos_Mitigados,
                    Pct_Activos_Evaluados, Controles_Implementados, Controles_Parciales,
                    Controles_No_Implementados, Fecha_Calculo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ''', [
                id_evaluacion,
                puntuacion_total,
                nivel_madurez,
                nombre_nivel,
                dominio_organizacional,
                dominio_personas,
                dominio_fisico,
                dominio_tecnologico,
                pct_controles_impl,
                pct_controles_med,
                pct_riesgos_mit,
                pct_activos_eval,
                controles_impl,
                controles_parc,
                controles_no_impl
            ])
        
        return True
    except Exception as e:
        print(f"Error guardando madurez: {e}")
        return False


def get_madurez_evaluacion(eval_id: str) -> Optional[Dict]:
    """Obtiene el resultado de madurez guardado"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM RESULTADOS_MADUREZ WHERE ID_Evaluacion = ?",
                [eval_id]
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
    except:
        pass
    return None


# ==================== COMPARATIVA DE MADUREZ ====================

def comparar_madurez(eval_id_1: str, eval_id_2: str) -> Optional[Dict]:
    """
    Compara la madurez entre dos evaluaciones.
    
    Returns:
        Diccionario con comparativa o None si faltan datos
    """
    madurez_1 = calcular_madurez_evaluacion(eval_id_1)
    madurez_2 = calcular_madurez_evaluacion(eval_id_2)
    
    if not madurez_1 or not madurez_2:
        return None
    
    # Calcular deltas
    delta_puntuacion = madurez_2.puntuacion_total - madurez_1.puntuacion_total
    delta_nivel = madurez_2.nivel_madurez - madurez_1.nivel_madurez
    
    # Calcular delta de riesgo residual promedio
    with get_connection() as conn:
        res_1 = pd.read_sql_query(
            "SELECT AVG(Riesgo_Residual) as prom FROM RESULTADOS_MAGERIT WHERE ID_Evaluacion = ?",
            conn, params=[eval_id_1]
        )
        res_2 = pd.read_sql_query(
            "SELECT AVG(Riesgo_Residual) as prom FROM RESULTADOS_MAGERIT WHERE ID_Evaluacion = ?",
            conn, params=[eval_id_2]
        )
    
    riesgo_res_1 = res_1["prom"].values[0] if not res_1.empty and res_1["prom"].values[0] else 0
    riesgo_res_2 = res_2["prom"].values[0] if not res_2.empty and res_2["prom"].values[0] else 0
    delta_riesgo = riesgo_res_2 - riesgo_res_1
    
    # Identificar mejoras y retrocesos por dominio
    mejoras = []
    retrocesos = []
    
    dominios = [
        ("Organizacional", madurez_1.dominio_organizacional, madurez_2.dominio_organizacional),
        ("Personas", madurez_1.dominio_personas, madurez_2.dominio_personas),
        ("Físico", madurez_1.dominio_fisico, madurez_2.dominio_fisico),
        ("Tecnológico", madurez_1.dominio_tecnologico, madurez_2.dominio_tecnologico),
    ]
    
    for nombre, val_1, val_2 in dominios:
        diff = val_2 - val_1
        if diff > 5:
            mejoras.append(f"{nombre}: +{diff:.0f}%")
        elif diff < -5:
            retrocesos.append(f"{nombre}: {diff:.0f}%")
    
    # Generar recomendaciones
    recomendaciones = []
    
    if madurez_2.dominio_tecnologico < 50:
        recomendaciones.append("Priorizar controles tecnológicos (8.x): monitoreo, cifrado, gestión de vulnerabilidades")
    if madurez_2.dominio_organizacional < 50:
        recomendaciones.append("Desarrollar políticas de seguridad y procedimientos documentados (5.x)")
    if madurez_2.pct_controles_medidos < 30:
        recomendaciones.append("Implementar métricas y KPIs para los controles existentes")
    if madurez_2.pct_riesgos_criticos_mitigados < 80:
        recomendaciones.append("Enfocar esfuerzos en mitigar riesgos críticos y altos restantes")
    
    # Generar mensaje resumen
    if delta_nivel > 0:
        mensaje = f"La madurez pasó de Nivel {madurez_1.nivel_madurez} ({madurez_1.nombre_nivel}) a Nivel {madurez_2.nivel_madurez} ({madurez_2.nombre_nivel})"
    elif delta_nivel < 0:
        mensaje = f"La madurez retrocedió de Nivel {madurez_1.nivel_madurez} ({madurez_1.nombre_nivel}) a Nivel {madurez_2.nivel_madurez} ({madurez_2.nombre_nivel})"
    else:
        mensaje = f"La madurez se mantiene en Nivel {madurez_2.nivel_madurez} ({madurez_2.nombre_nivel})"
    
    if delta_riesgo < 0:
        mensaje += f", con una reducción del {abs(delta_riesgo/riesgo_res_1*100):.0f}% del riesgo residual." if riesgo_res_1 > 0 else "."
    elif delta_riesgo > 0:
        mensaje += f", pero con un incremento del {abs(delta_riesgo/riesgo_res_1*100):.0f}% del riesgo residual." if riesgo_res_1 > 0 else "."
    
    return {
        "eval_1": eval_id_1,
        "eval_2": eval_id_2,
        "madurez_1": madurez_1.to_dict(),
        "madurez_2": madurez_2.to_dict(),
        "delta_puntuacion": round(delta_puntuacion, 1),
        "delta_nivel": delta_nivel,
        "delta_riesgo_residual": round(delta_riesgo, 2),
        "mejoras": mejoras,
        "retrocesos": retrocesos,
        "recomendaciones": recomendaciones,
        "mensaje_resumen": mensaje
    }


# ==================== OBTENER CONTROLES EXISTENTES DETALLADOS ====================

def get_controles_existentes_detallados(eval_id: str, activo_id: str = None) -> Dict:
    """
    Obtiene los controles existentes con detalle para mostrar en UI.
    Nunca retorna vacío si hay respuestas - siempre muestra el análisis.
    
    Returns:
        {
            "controles": [{codigo, nombre, nivel, efectividad, pregunta, dominio}],
            "resumen": {implementados, parciales, no_implementados},
            "por_dominio": {dominio: [{controles}]}
        }
    """
    respuestas = read_table("RESPUESTAS")
    
    if respuestas.empty:
        return {
            "controles": [],
            "resumen": {"implementados": 0, "parciales": 0, "no_implementados": 0},
            "por_dominio": {}
        }
    
    # Filtrar respuestas
    filtro = respuestas["ID_Evaluacion"].astype(str) == str(eval_id)
    if activo_id:
        filtro = filtro & (respuestas["ID_Activo"].astype(str) == str(activo_id))
    
    respuestas_filtradas = respuestas[filtro]
    
    if respuestas_filtradas.empty:
        return {
            "controles": [],
            "resumen": {"implementados": 0, "parciales": 0, "no_implementados": 0},
            "por_dominio": {}
        }
    
    # Analizar controles
    analisis = analizar_controles_desde_respuestas(respuestas_filtradas)
    
    # Obtener catálogo de controles para nombres
    catalogo = read_table("CATALOGO_CONTROLES_ISO27002")
    nombres_controles = {}
    for _, ctrl in catalogo.iterrows():
        nombres_controles[str(ctrl.get("codigo", ""))] = str(ctrl.get("nombre", ""))
    
    # Formatear controles para UI
    controles_lista = []
    por_dominio = {}
    
    for codigo, info in analisis["controles"].items():
        control_data = {
            "codigo": codigo,
            "nombre": nombres_controles.get(codigo, ""),
            "nivel": info["nivel"],
            "efectividad": info["efectividad"],
            "pregunta": info["pregunta"],
            "descripcion": info["descripcion"],
            "dominio": info["dominio"]
        }
        controles_lista.append(control_data)
        
        # Agrupar por dominio
        dominio = info["dominio"]
        if dominio not in por_dominio:
            por_dominio[dominio] = []
        por_dominio[dominio].append(control_data)
    
    # Ordenar por efectividad descendente
    controles_lista.sort(key=lambda x: x["efectividad"], reverse=True)
    
    return {
        "controles": controles_lista,
        "resumen": analisis["metricas"],
        "por_dominio": por_dominio
    }
