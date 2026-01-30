"""
MÓDULO DE DEGRADACIÓN MAGERIT
==============================
Implementa el concepto de DEGRADACIÓN según Marco Teórico MAGERIT:
- Degradación por dimensión (D, I, C) con valores [0.0 - 1.0]
- MOTOR DE CÁLCULO: Valores basados en catálogo MAGERIT v3 (ya no depende de IA)
- Cálculo correcto: IMPACTO = CRITICIDAD × MAX(Deg_D, Deg_I, Deg_C)
"""
import json
import datetime as dt
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from services.database_service import get_connection


# =============================================================================
# MAPEO DE DEGRADACIÓN POR AMENAZA MAGERIT v3
# =============================================================================
# Valores de degradación D/I/C según el tipo de amenaza y su naturaleza
# Fuente: MAGERIT v3 - Libro II: Catálogo de Elementos
# Valores en escala 0.0 - 1.0

DEGRADACION_MAGERIT = {
    # ========== [N] DESASTRES NATURALES ==========
    # Afectan principalmente Disponibilidad, poco I/C
    "N.1":  {"d": 1.00, "i": 0.10, "c": 0.05, "desc": "Fuego"},
    "N.2":  {"d": 1.00, "i": 0.10, "c": 0.05, "desc": "Daños por agua"},
    "N.*":  {"d": 0.90, "i": 0.10, "c": 0.05, "desc": "Desastres naturales (genérico)"},
    
    # ========== [I] DE ORIGEN INDUSTRIAL ==========
    # Afectan principalmente Disponibilidad
    "I.1":  {"d": 0.90, "i": 0.15, "c": 0.05, "desc": "Fuego (industrial)"},
    "I.2":  {"d": 0.85, "i": 0.10, "c": 0.05, "desc": "Daños por agua (industrial)"},
    "I.3":  {"d": 0.80, "i": 0.10, "c": 0.05, "desc": "Contaminación mecánica"},
    "I.4":  {"d": 0.80, "i": 0.10, "c": 0.05, "desc": "Contaminación electromagnética"},
    "I.5":  {"d": 0.95, "i": 0.05, "c": 0.05, "desc": "Avería de origen físico o lógico"},
    "I.6":  {"d": 0.85, "i": 0.05, "c": 0.05, "desc": "Corte del suministro eléctrico"},
    "I.7":  {"d": 0.80, "i": 0.05, "c": 0.05, "desc": "Condiciones inadecuadas de temperatura/humedad"},
    "I.8":  {"d": 0.90, "i": 0.20, "c": 0.10, "desc": "Fallo de servicios de comunicaciones"},
    "I.9":  {"d": 0.85, "i": 0.15, "c": 0.10, "desc": "Interrupción de otros servicios"},
    "I.10": {"d": 0.70, "i": 0.15, "c": 0.10, "desc": "Degradación de los soportes de almacenamiento"},
    "I.11": {"d": 0.75, "i": 0.10, "c": 0.05, "desc": "Emanaciones electromagnéticas"},
    "I.*":  {"d": 0.80, "i": 0.10, "c": 0.05, "desc": "Origen industrial (genérico)"},
    
    # ========== [E] ERRORES Y FALLOS NO INTENCIONADOS ==========
    # Balance entre D/I, bajo C
    "E.1":  {"d": 0.60, "i": 0.70, "c": 0.40, "desc": "Errores de los usuarios"},
    "E.2":  {"d": 0.70, "i": 0.75, "c": 0.30, "desc": "Errores del administrador"},
    "E.3":  {"d": 0.50, "i": 0.40, "c": 0.20, "desc": "Errores de monitorización (log)"},
    "E.4":  {"d": 0.55, "i": 0.60, "c": 0.25, "desc": "Errores de configuración"},
    "E.7":  {"d": 0.30, "i": 0.50, "c": 0.40, "desc": "Deficiencias en la organización"},
    "E.8":  {"d": 0.65, "i": 0.75, "c": 0.35, "desc": "Difusión de software dañino"},
    "E.9":  {"d": 0.70, "i": 0.60, "c": 0.30, "desc": "Errores de [re-]encaminamiento"},
    "E.10": {"d": 0.55, "i": 0.50, "c": 0.40, "desc": "Errores de secuencia"},
    "E.14": {"d": 0.20, "i": 0.30, "c": 0.80, "desc": "Escapes de información"},
    "E.15": {"d": 0.75, "i": 0.60, "c": 0.30, "desc": "Alteración accidental de la información"},
    "E.18": {"d": 0.90, "i": 0.20, "c": 0.15, "desc": "Destrucción de información"},
    "E.19": {"d": 0.25, "i": 0.35, "c": 0.85, "desc": "Fugas de información"},
    "E.20": {"d": 0.70, "i": 0.65, "c": 0.45, "desc": "Vulnerabilidades de los programas (software)"},
    "E.21": {"d": 0.80, "i": 0.50, "c": 0.30, "desc": "Errores de mantenimiento/actualización (software)"},
    "E.23": {"d": 0.85, "i": 0.40, "c": 0.20, "desc": "Errores de mantenimiento/actualización (hardware)"},
    "E.24": {"d": 0.90, "i": 0.30, "c": 0.70, "desc": "Caída del sistema por agotamiento de recursos"},
    "E.25": {"d": 0.95, "i": 0.20, "c": 0.60, "desc": "Pérdida de equipos"},
    "E.28": {"d": 0.40, "i": 0.75, "c": 0.50, "desc": "Indisponibilidad del personal"},
    "E.*":  {"d": 0.60, "i": 0.55, "c": 0.35, "desc": "Errores no intencionados (genérico)"},
    
    # ========== [A] ATAQUES INTENCIONADOS ==========
    # Mayor impacto en I/C, variable en D
    "A.3":  {"d": 0.20, "i": 0.80, "c": 0.95, "desc": "Manipulación de los registros de actividad (log)"},
    "A.4":  {"d": 0.30, "i": 0.90, "c": 0.70, "desc": "Manipulación de la configuración"},
    "A.5":  {"d": 0.40, "i": 0.85, "c": 0.90, "desc": "Suplantación de identidad del usuario"},
    "A.6":  {"d": 0.50, "i": 0.80, "c": 0.85, "desc": "Abuso de privilegios de acceso"},
    "A.7":  {"d": 0.60, "i": 0.75, "c": 0.80, "desc": "Uso no previsto"},
    "A.8":  {"d": 0.65, "i": 0.70, "c": 0.40, "desc": "Difusión de software dañino"},
    "A.9":  {"d": 0.50, "i": 0.65, "c": 0.50, "desc": "[Re-]encaminamiento de mensajes"},
    "A.10": {"d": 0.30, "i": 0.55, "c": 0.45, "desc": "Alteración de secuencia"},
    "A.11": {"d": 0.60, "i": 0.85, "c": 0.90, "desc": "Acceso no autorizado"},
    "A.12": {"d": 0.20, "i": 0.30, "c": 0.90, "desc": "Análisis de tráfico"},
    "A.13": {"d": 0.35, "i": 0.70, "c": 0.60, "desc": "Repudio"},
    "A.14": {"d": 0.25, "i": 0.85, "c": 0.95, "desc": "Interceptación de información (escucha)"},
    "A.15": {"d": 0.40, "i": 0.90, "c": 0.70, "desc": "Modificación deliberada de información"},
    "A.18": {"d": 0.95, "i": 0.60, "c": 0.50, "desc": "Destrucción de información"},
    "A.19": {"d": 0.30, "i": 0.45, "c": 0.95, "desc": "Divulgación de información"},
    "A.22": {"d": 0.75, "i": 0.85, "c": 0.80, "desc": "Manipulación de programas"},
    "A.23": {"d": 0.80, "i": 0.50, "c": 0.35, "desc": "Manipulación de los equipos"},
    "A.24": {"d": 0.95, "i": 0.15, "c": 0.10, "desc": "Denegación de servicio (DoS/DDoS)"},
    "A.25": {"d": 0.90, "i": 0.40, "c": 0.85, "desc": "Robo"},
    "A.26": {"d": 0.70, "i": 0.80, "c": 0.90, "desc": "Ataque destructivo"},
    "A.27": {"d": 0.50, "i": 0.45, "c": 0.40, "desc": "Ocupación enemiga"},
    "A.28": {"d": 0.40, "i": 0.75, "c": 0.65, "desc": "Indisponibilidad del personal"},
    "A.29": {"d": 0.55, "i": 0.70, "c": 0.85, "desc": "Extorsión"},
    "A.30": {"d": 0.65, "i": 0.80, "c": 0.90, "desc": "Ingeniería social"},
    "A.*":  {"d": 0.55, "i": 0.75, "c": 0.75, "desc": "Ataques intencionados (genérico)"},
}

# Ajustes por tipo de activo (multiplicadores)
AJUSTE_TIPO_ACTIVO = {
    # Activos físicos: mayor impacto en Disponibilidad
    "hardware": {"d": 1.15, "i": 0.90, "c": 0.85},
    "físico": {"d": 1.15, "i": 0.90, "c": 0.85},
    "fisico": {"d": 1.15, "i": 0.90, "c": 0.85},
    "infraestructura": {"d": 1.10, "i": 0.95, "c": 0.90},
    "equipamiento": {"d": 1.10, "i": 0.95, "c": 0.90},
    
    # Activos de datos: mayor impacto en Confidencialidad e Integridad
    "datos": {"d": 0.85, "i": 1.15, "c": 1.20},
    "información": {"d": 0.85, "i": 1.15, "c": 1.20},
    "informacion": {"d": 0.85, "i": 1.15, "c": 1.20},
    "base de datos": {"d": 0.90, "i": 1.20, "c": 1.15},
    "documento": {"d": 0.80, "i": 1.10, "c": 1.25},
    
    # Software: balance con énfasis en I
    "software": {"d": 1.00, "i": 1.10, "c": 1.00},
    "aplicación": {"d": 1.00, "i": 1.10, "c": 1.05},
    "aplicacion": {"d": 1.00, "i": 1.10, "c": 1.05},
    "sistema": {"d": 1.05, "i": 1.05, "c": 1.00},
    
    # Servicios: énfasis en Disponibilidad
    "servicio": {"d": 1.15, "i": 1.00, "c": 0.95},
    "red": {"d": 1.10, "i": 1.00, "c": 1.00},
    "comunicaciones": {"d": 1.15, "i": 0.95, "c": 0.95},
    
    # Personal: balance general
    "personal": {"d": 0.95, "i": 1.00, "c": 1.10},
    "rrhh": {"d": 0.95, "i": 1.00, "c": 1.15},
}


def obtener_degradacion_motor(
    codigo_amenaza: str,
    tipo_activo: str = "",
    criticidad: int = 3
) -> Tuple[float, float, float, str]:
    """
    MOTOR DE CÁLCULO DE DEGRADACIÓN MAGERIT
    ========================================
    Calcula degradación D/I/C basándose en:
    1. Catálogo MAGERIT v3 (valores base por código de amenaza)
    2. Tipo de activo (ajuste multiplicador)
    3. Criticidad del activo (factor de escala)
    
    Args:
        codigo_amenaza: Código MAGERIT (ej: "A.24", "E.1", "N.1")
        tipo_activo: Tipo del activo para ajustes
        criticidad: Valor de criticidad 1-5 (para ajuste de severidad)
    
    Returns:
        Tuple (deg_d, deg_i, deg_c, justificacion)
        Valores normalizados entre 0.0 y 1.0
    """
    # 1. Obtener valores base del catálogo MAGERIT
    if codigo_amenaza in DEGRADACION_MAGERIT:
        base = DEGRADACION_MAGERIT[codigo_amenaza]
    else:
        # Buscar categoría genérica (N.*, I.*, E.*, A.*)
        categoria = codigo_amenaza[0] + ".*" if codigo_amenaza else "E.*"
        base = DEGRADACION_MAGERIT.get(categoria, {"d": 0.5, "i": 0.5, "c": 0.5, "desc": "Genérico"})
    
    deg_d = base["d"]
    deg_i = base["i"]
    deg_c = base["c"]
    desc_amenaza = base["desc"]
    
    # 2. Aplicar ajuste por tipo de activo
    tipo_lower = tipo_activo.lower() if tipo_activo else ""
    ajuste = {"d": 1.0, "i": 1.0, "c": 1.0}
    
    for tipo_key, multiplicadores in AJUSTE_TIPO_ACTIVO.items():
        if tipo_key in tipo_lower:
            ajuste = multiplicadores
            break
    
    deg_d = deg_d * ajuste["d"]
    deg_i = deg_i * ajuste["i"]
    deg_c = deg_c * ajuste["c"]
    
    # 3. Ajuste por criticidad (activos más críticos = degradación más severa)
    factor_criticidad = 0.7 + (criticidad / 5) * 0.4  # Rango: 0.7 - 1.1
    deg_d = deg_d * factor_criticidad
    deg_i = deg_i * factor_criticidad
    deg_c = deg_c * factor_criticidad
    
    # 4. Normalizar a rango [0.0, 1.0]
    deg_d = min(1.0, max(0.0, round(deg_d, 2)))
    deg_i = min(1.0, max(0.0, round(deg_i, 2)))
    deg_c = min(1.0, max(0.0, round(deg_c, 2)))
    
    # 5. Construir justificación
    justificacion = (
        f"Motor MAGERIT v3: {desc_amenaza}. "
        f"Base: D={base['d']:.0%}, I={base['i']:.0%}, C={base['c']:.0%}. "
        f"Ajuste tipo activo '{tipo_activo}' y criticidad {criticidad}."
    )
    
    return deg_d, deg_i, deg_c, justificacion


def calcular_degradacion_amenazas(
    amenazas: List[Dict],
    tipo_activo: str,
    criticidad: int
) -> List[Dict]:
    """
    Calcula la degradación para una lista de amenazas usando el motor.
    
    Args:
        amenazas: Lista de diccionarios con al menos 'codigo_amenaza'
        tipo_activo: Tipo del activo
        criticidad: Criticidad del activo (1-5)
    
    Returns:
        Lista de amenazas con degradaciones actualizadas por el motor
    """
    for amenaza in amenazas:
        codigo = amenaza.get("codigo_amenaza", "")
        deg_d, deg_i, deg_c, justificacion = obtener_degradacion_motor(
            codigo, tipo_activo, criticidad
        )
        
        # Actualizar valores (en escala 0-100 para compatibilidad)
        amenaza["degradacion_d"] = int(deg_d * 100)
        amenaza["degradacion_i"] = int(deg_i * 100)
        amenaza["degradacion_c"] = int(deg_c * 100)
        amenaza["justificacion_motor"] = justificacion
        amenaza["fuente_degradacion"] = "MOTOR_MAGERIT"
    
    return amenazas


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
    
    IMPORTANTE: Valores en escala 0.0-1.0 (porcentaje de degradación según MAGERIT).
    Ajustados para generar variedad de riesgos (bajos, medios, altos).
    """
    # Valores base REDUCIDOS para generar más variedad de riesgos
    deg_d = 0.3  # 30% base
    deg_i = 0.3  # 30% base
    deg_c = 0.3  # 30% base
    
    # Ajuste por tipo de amenaza
    tipo_amenaza_upper = tipo_amenaza.upper() if tipo_amenaza else ""
    
    if "DESASTRE" in tipo_amenaza_upper or "NATURAL" in tipo_amenaza_upper:
        deg_d = 0.8  # Alta
        deg_i = 0.3  # Media-baja
        deg_c = 0.15 # Baja
    elif "ERROR" in tipo_amenaza_upper or "FALLO" in tipo_amenaza_upper:
        deg_d = 0.5  # Media
        deg_i = 0.4  # Media
        deg_c = 0.2  # Baja
    elif "ATAQUE" in tipo_amenaza_upper or "INTENCION" in tipo_amenaza_upper:
        deg_d = 0.4  # Media
        deg_i = 0.7  # Alta
        deg_c = 0.8  # Alta
    elif "FUGA" in tipo_amenaza_upper or "ACCESO" in tipo_amenaza_upper:
        deg_d = 0.1  # Muy Baja
        deg_i = 0.2  # Baja
        deg_c = 0.85 # Muy Alta
    elif "MANIPULACION" in tipo_amenaza_upper or "SABOTAJE" in tipo_amenaza_upper:
        deg_d = 0.6  # Media-Alta
        deg_i = 0.9  # Muy Alta
        deg_c = 0.3  # Media-baja
    else:
        # Valores por defecto más moderados
        deg_d = 0.4
        deg_i = 0.35
        deg_c = 0.3
        
    # Ajuste por tipo de activo (moderado)
    tipo_activo_upper = tipo_activo.upper() if tipo_activo else ""
    
    if "FISICO" in tipo_activo_upper or "FÍSICO" in tipo_activo_upper:
        deg_d = min(1.0, deg_d * 1.15)  # Ligero aumento en disponibilidad
    elif "VIRTUAL" in tipo_activo_upper or "DATO" in tipo_activo_upper:
        deg_c = min(1.0, deg_c * 1.2)   # Mayor impacto en confidencialidad
        deg_i = min(1.0, deg_i * 1.15)  # Mayor impacto en integridad
    elif "SERVICIO" in tipo_activo_upper:
        deg_d = min(1.0, deg_d * 1.3)   # Servicios dependen de disponibilidad
        deg_i = min(1.0, deg_i * 1.1)
    
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
