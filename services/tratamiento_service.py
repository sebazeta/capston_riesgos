"""
SERVICIO DE TRATAMIENTO DE RIESGOS
===================================
Gestión de decisiones de tratamiento por activo.
Tipos: Mitigar, Aceptar, Transferir, Evitar
"""
import json
import datetime as dt
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from services.database_service import get_connection


# Tipos de tratamiento válidos
TIPOS_TRATAMIENTO = {
    "Mitigar": "Implementar controles para reducir el riesgo a un nivel aceptable",
    "Aceptar": "Asumir el riesgo conscientemente sin acción adicional",
    "Transferir": "Trasladar el riesgo a un tercero (seguros, outsourcing)",
    "Evitar": "Eliminar la actividad o activo que genera el riesgo"
}


@dataclass
class TratamientoRiesgo:
    """Decisión de tratamiento para un riesgo"""
    id: int = None
    id_evaluacion: str = ""
    id_activo: str = ""
    tipo_tratamiento: str = "Mitigar"
    justificacion: str = ""
    riesgo_actual: float = 0.0
    riesgo_objetivo: float = 0.0
    controles_propuestos: str = ""
    responsable: str = ""
    fecha_objetivo: str = ""
    fecha_decision: str = ""
    estado: str = "Propuesto"
    
    def __post_init__(self):
        if not self.fecha_decision:
            self.fecha_decision = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =============================================================================
# CRUD TRATAMIENTO
# =============================================================================

def crear_tratamiento(trat: TratamientoRiesgo) -> Optional[int]:
    """Crea un tratamiento de riesgo. Retorna el ID o None si falla."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO TRATAMIENTO_RIESGOS (
                    ID_Evaluacion, ID_Activo, Codigo_Amenaza, Tipo_Tratamiento,
                    Justificacion, Riesgo_Actual, Riesgo_Objetivo, Estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                trat.id_evaluacion,
                trat.id_activo,
                "",  # Codigo_Amenaza vacío por ahora
                trat.tipo_tratamiento,
                trat.justificacion,
                trat.riesgo_actual,
                trat.riesgo_objetivo,
                trat.estado
            ])
            return cursor.lastrowid
    except Exception as e:
        print(f"Error creando tratamiento: {e}")
        return None


def obtener_tratamiento(trat_id: int) -> Optional[TratamientoRiesgo]:
    """Obtiene un tratamiento por ID"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, ID_Evaluacion, ID_Activo, Tipo_Tratamiento,
                       Justificacion, Riesgo_Actual, Riesgo_Objetivo, Estado
                FROM TRATAMIENTO_RIESGOS
                WHERE id = ?
            ''', [trat_id])
            
            row = cursor.fetchone()
            if row:
                return TratamientoRiesgo(
                    id=row[0],
                    id_evaluacion=row[1],
                    id_activo=row[2],
                    tipo_tratamiento=row[3],
                    justificacion=row[4] or "",
                    riesgo_actual=row[5] or 0.0,
                    riesgo_objetivo=row[6] or 0.0,
                    estado=row[7] or "Propuesto"
                )
            return None
    except Exception as e:
        print(f"Error obteniendo tratamiento: {e}")
        return None


def actualizar_tratamiento(trat: TratamientoRiesgo) -> bool:
    """Actualiza un tratamiento existente"""
    if not trat.id:
        return False
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE TRATAMIENTO_RIESGOS SET
                    Tipo_Tratamiento = ?,
                    Justificacion = ?,
                    Riesgo_Actual = ?,
                    Riesgo_Objetivo = ?,
                    Estado = ?
                WHERE id = ?
            ''', [
                trat.tipo_tratamiento,
                trat.justificacion,
                trat.riesgo_actual,
                trat.riesgo_objetivo,
                trat.estado,
                trat.id
            ])
        return True
    except Exception as e:
        print(f"Error actualizando tratamiento: {e}")
        return False


def eliminar_tratamiento(trat_id: int) -> bool:
    """Elimina un tratamiento por ID"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM TRATAMIENTO_RIESGOS WHERE id = ?
            ''', [trat_id])
        return True
    except Exception as e:
        print(f"Error eliminando tratamiento: {e}")
        return False


def listar_tratamientos_activo(id_activo: str) -> List[TratamientoRiesgo]:
    """Lista todos los tratamientos de un activo"""
    tratamientos = []
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, ID_Evaluacion, ID_Activo, Tipo_Tratamiento,
                       Justificacion, Riesgo_Actual, Riesgo_Objetivo, Estado
                FROM TRATAMIENTO_RIESGOS
                WHERE ID_Activo = ?
                ORDER BY Riesgo_Actual DESC
            ''', [id_activo])
            
            for row in cursor.fetchall():
                tratamientos.append(TratamientoRiesgo(
                    id=row[0],
                    id_evaluacion=row[1],
                    id_activo=row[2],
                    tipo_tratamiento=row[3],
                    justificacion=row[4] or "",
                    riesgo_actual=row[5] or 0.0,
                    riesgo_objetivo=row[6] or 0.0,
                    estado=row[7] or "Propuesto"
                ))
    except Exception as e:
        print(f"Error listando tratamientos: {e}")
    return tratamientos


def listar_tratamientos_evaluacion(id_evaluacion: str) -> List[TratamientoRiesgo]:
    """Lista todos los tratamientos de una evaluación"""
    tratamientos = []
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, ID_Evaluacion, ID_Activo, Tipo_Tratamiento,
                       Justificacion, Riesgo_Actual, Riesgo_Objetivo, Estado
                FROM TRATAMIENTO_RIESGOS
                WHERE ID_Evaluacion = ?
                ORDER BY Riesgo_Actual DESC
            ''', [id_evaluacion])
            
            for row in cursor.fetchall():
                tratamientos.append(TratamientoRiesgo(
                    id=row[0],
                    id_evaluacion=row[1],
                    id_activo=row[2],
                    tipo_tratamiento=row[3],
                    justificacion=row[4] or "",
                    riesgo_actual=row[5] or 0.0,
                    riesgo_objetivo=row[6] or 0.0,
                    estado=row[7] or "Propuesto"
                ))
    except Exception as e:
        print(f"Error listando tratamientos: {e}")
    return tratamientos


# =============================================================================
# SUGERENCIAS DE TRATAMIENTO
# =============================================================================

def sugerir_tratamiento(riesgo: float) -> Dict:
    """Sugiere tipo de tratamiento basado en nivel de riesgo"""
    if riesgo >= 8:  # Crítico
        return {
            "tipo": "Mitigar",
            "descripcion": TIPOS_TRATAMIENTO["Mitigar"],
            "justificacion": f"Riesgo {riesgo:.1f} supera nivel crítico (>=8). Acción obligatoria para reducir el riesgo.",
            "prioridad": "URGENTE"
        }
    elif riesgo >= 6:  # Alto
        return {
            "tipo": "Mitigar",
            "descripcion": TIPOS_TRATAMIENTO["Mitigar"],
            "justificacion": f"Riesgo {riesgo:.1f} es alto (>=6). Se recomienda implementar controles adicionales.",
            "prioridad": "ALTA"
        }
    elif riesgo >= 4:  # Medio
        return {
            "tipo": "Mitigar",
            "descripcion": TIPOS_TRATAMIENTO["Mitigar"],
            "justificacion": f"Riesgo {riesgo:.1f} es moderado. Evaluar costo-beneficio de controles adicionales.",
            "prioridad": "MEDIA"
        }
    elif riesgo >= 2:  # Bajo
        return {
            "tipo": "Aceptar",
            "descripcion": TIPOS_TRATAMIENTO["Aceptar"],
            "justificacion": f"Riesgo {riesgo:.1f} está en nivel bajo. Puede aceptarse con monitoreo.",
            "prioridad": "BAJA"
        }
    else:  # Muy bajo
        return {
            "tipo": "Aceptar",
            "descripcion": TIPOS_TRATAMIENTO["Aceptar"],
            "justificacion": f"Riesgo {riesgo:.1f} es mínimo. Aceptar y mantener controles existentes.",
            "prioridad": "MUY BAJA"
        }


# =============================================================================
# ESTADÍSTICAS
# =============================================================================

def get_estadisticas_tratamiento(id_evaluacion: str) -> Dict[str, Any]:
    """Obtiene estadísticas de tratamiento para una evaluación"""
    stats = {
        "total": 0,
        "por_tipo": {},
        "por_estado": {},
        "activos_con_tratamiento": 0,
        "riesgo_promedio_actual": 0.0,
        "riesgo_promedio_objetivo": 0.0
    }
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Total
            cursor.execute('''
                SELECT COUNT(*) FROM TRATAMIENTO_RIESGOS
                WHERE ID_Evaluacion = ?
            ''', [id_evaluacion])
            stats["total"] = cursor.fetchone()[0]
            
            # Por tipo
            cursor.execute('''
                SELECT Tipo_Tratamiento, COUNT(*) FROM TRATAMIENTO_RIESGOS
                WHERE ID_Evaluacion = ?
                GROUP BY Tipo_Tratamiento
            ''', [id_evaluacion])
            for row in cursor.fetchall():
                stats["por_tipo"][row[0] or "Sin tipo"] = row[1]
            
            # Por estado
            cursor.execute('''
                SELECT Estado, COUNT(*) FROM TRATAMIENTO_RIESGOS
                WHERE ID_Evaluacion = ?
                GROUP BY Estado
            ''', [id_evaluacion])
            for row in cursor.fetchall():
                stats["por_estado"][row[0] or "Sin estado"] = row[1]
            
            # Activos únicos con tratamiento
            cursor.execute('''
                SELECT COUNT(DISTINCT ID_Activo) FROM TRATAMIENTO_RIESGOS
                WHERE ID_Evaluacion = ?
            ''', [id_evaluacion])
            stats["activos_con_tratamiento"] = cursor.fetchone()[0]
            
            # Promedios
            cursor.execute('''
                SELECT AVG(Riesgo_Actual), AVG(Riesgo_Objetivo)
                FROM TRATAMIENTO_RIESGOS
                WHERE ID_Evaluacion = ?
            ''', [id_evaluacion])
            row = cursor.fetchone()
            if row:
                stats["riesgo_promedio_actual"] = round(row[0] or 0, 2)
                stats["riesgo_promedio_objetivo"] = round(row[1] or 0, 2)
                    
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
    
    return stats
