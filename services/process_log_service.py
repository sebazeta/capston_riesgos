"""
SERVICIO DE LOG DE PROCESOS
============================
Registra fechas de inicio y fin de cada proceso del sistema:
evaluaciones, carga de inventario, análisis IA, cuestionarios, etc.
"""
import json
import datetime as dt
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from services.database_service import get_connection


# ==================== CONTEXT MANAGER PARA LOG ====================

@contextmanager
def log_proceso(eval_id: str, proceso: str, tipo: str, descripcion: str = "",
                usuario: str = "sistema", detalles: Dict = None):
    """
    Context manager que registra automáticamente inicio, fin y duración.
    
    Uso:
        with log_proceso("EVA-001", "analisis_ia", "IA", "Análisis de activo X"):
            # ... código del proceso ...
    """
    inicio = dt.datetime.now()
    resultado = {"estado": "completado", "error": None}
    try:
        yield resultado
    except Exception as e:
        resultado["estado"] = "error"
        resultado["error"] = str(e)
        raise
    finally:
        fin = dt.datetime.now()
        duracion = (fin - inicio).total_seconds()
        
        detalles_final = detalles or {}
        if resultado["error"]:
            detalles_final["error"] = resultado["error"]
        
        registrar_proceso(
            eval_id=eval_id,
            proceso=proceso,
            tipo=tipo,
            descripcion=descripcion,
            estado=resultado["estado"],
            detalles=detalles_final,
            usuario=usuario,
            fecha_inicio=inicio.strftime("%Y-%m-%d %H:%M:%S"),
            fecha_fin=fin.strftime("%Y-%m-%d %H:%M:%S"),
            duracion=duracion
        )


# ==================== FUNCIONES DE REGISTRO ====================

def registrar_proceso(
    eval_id: str,
    proceso: str,
    tipo: str,
    descripcion: str = "",
    estado: str = "completado",
    detalles: Dict = None,
    usuario: str = "sistema",
    fecha_inicio: str = None,
    fecha_fin: str = None,
    duracion: float = 0
) -> bool:
    """Registra un proceso en el log"""
    try:
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_connection() as conn:
            conn.execute('''
                INSERT INTO LOG_PROCESOS (
                    ID_Evaluacion, Proceso, Tipo, Descripcion, Estado,
                    Detalles_JSON, Usuario, Fecha_Inicio, Fecha_Fin, Duracion_Seg
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                eval_id,
                proceso,
                tipo,
                descripcion,
                estado,
                json.dumps(detalles or {}, ensure_ascii=False, default=str),
                usuario,
                fecha_inicio or now,
                fecha_fin or now,
                duracion
            ])
        return True
    except Exception as e:
        print(f"Error registrando proceso: {e}")
        return False


def registrar_proceso_rapido(eval_id: str, proceso: str, tipo: str,
                              descripcion: str = "", usuario: str = "sistema",
                              detalles: Dict = None) -> bool:
    """Registro rápido sin medición de tiempo (para eventos instantáneos)"""
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return registrar_proceso(
        eval_id=eval_id, proceso=proceso, tipo=tipo,
        descripcion=descripcion, estado="completado",
        detalles=detalles, usuario=usuario,
        fecha_inicio=now, fecha_fin=now, duracion=0
    )


# ==================== CONSULTAS ====================

def obtener_log_procesos(
    eval_id: str = None,
    tipo: str = None,
    limite: int = 200
) -> List[Dict]:
    """Obtiene el log de procesos con filtros opcionales"""
    try:
        with get_connection() as conn:
            query = "SELECT * FROM LOG_PROCESOS WHERE 1=1"
            params = []
            
            if eval_id:
                query += " AND ID_Evaluacion = ?"
                params.append(eval_id)
            if tipo:
                query += " AND Tipo = ?"
                params.append(tipo)
            
            query += " ORDER BY Fecha_Inicio DESC LIMIT ?"
            params.append(limite)
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        print(f"Error obteniendo log: {e}")
        return []


def obtener_resumen_procesos(eval_id: str) -> Dict:
    """Resumen de procesos por tipo para una evaluación"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT Tipo, COUNT(*) as total,
                       MIN(Fecha_Inicio) as primera,
                       MAX(Fecha_Fin) as ultima,
                       SUM(Duracion_Seg) as duracion_total,
                       SUM(CASE WHEN Estado = 'error' THEN 1 ELSE 0 END) as errores
                FROM LOG_PROCESOS
                WHERE ID_Evaluacion = ?
                GROUP BY Tipo
                ORDER BY ultima DESC
            ''', [eval_id])
            
            resumen = {}
            for row in cursor.fetchall():
                r = dict(row)
                resumen[r["Tipo"]] = r
            return resumen
    except Exception as e:
        print(f"Error obteniendo resumen: {e}")
        return {}


def obtener_timeline_evaluacion(eval_id: str) -> List[Dict]:
    """Timeline cronológico de todos los eventos de una evaluación"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT Proceso, Tipo, Descripcion, Estado,
                       Fecha_Inicio, Fecha_Fin, Duracion_Seg, Usuario
                FROM LOG_PROCESOS
                WHERE ID_Evaluacion = ?
                ORDER BY Fecha_Inicio ASC
            ''', [eval_id])
            return [dict(r) for r in cursor.fetchall()]
    except:
        return []
