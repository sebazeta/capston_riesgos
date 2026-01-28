"""
SERVICIO DE COMPARATIVA/REEVALUACIÓN
=====================================
Compara evaluaciones y detecta mejoras/deterioros.
"""
import json
import datetime as dt
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from services.database_service import get_connection


@dataclass 
class ComparativaEvaluacion:
    """Resultado de comparar dos evaluaciones"""
    eval_origen: str
    eval_destino: str
    fecha_comparacion: str
    total_activos_origen: int
    total_activos_destino: int
    riesgo_promedio_origen: float
    riesgo_promedio_destino: float
    delta_riesgo_promedio: float
    riesgo_maximo_origen: float
    riesgo_maximo_destino: float
    delta_riesgo_maximo: float
    activos_mejorados: int
    activos_deteriorados: int
    activos_sin_cambio: int
    detalle_mejoras: List[Dict]
    detalle_deterioros: List[Dict]


def comparar_evaluaciones(eval_origen_id: str, eval_destino_id: str) -> Optional[ComparativaEvaluacion]:
    """
    Compara dos evaluaciones y calcula deltas.
    eval_origen: Evaluación anterior (baseline)
    eval_destino: Evaluación actual (para comparar)
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener resultados de evaluación origen
            cursor.execute('''
                SELECT ID_Activo, Nombre_Activo, Riesgo_Promedio, Riesgo_Maximo,
                       Riesgo_Inherente, Riesgo_Residual
                FROM RESULTADOS_MAGERIT
                WHERE ID_Evaluacion = ?
            ''', [eval_origen_id])
            
            resultados_origen = {}
            riesgos_origen = []
            for row in cursor.fetchall():
                resultados_origen[row[0]] = {
                    "nombre": row[1],
                    "riesgo_promedio": row[2] or row[4] or 0,
                    "riesgo_maximo": row[3] or row[4] or 0,
                    "riesgo_residual": row[5] or 0
                }
                riesgos_origen.append(row[2] or row[4] or 0)
            
            # Obtener resultados de evaluación destino
            cursor.execute('''
                SELECT ID_Activo, Nombre_Activo, Riesgo_Promedio, Riesgo_Maximo,
                       Riesgo_Inherente, Riesgo_Residual
                FROM RESULTADOS_MAGERIT
                WHERE ID_Evaluacion = ?
            ''', [eval_destino_id])
            
            resultados_destino = {}
            riesgos_destino = []
            for row in cursor.fetchall():
                resultados_destino[row[0]] = {
                    "nombre": row[1],
                    "riesgo_promedio": row[2] or row[4] or 0,
                    "riesgo_maximo": row[3] or row[4] or 0,
                    "riesgo_residual": row[5] or 0
                }
                riesgos_destino.append(row[2] or row[4] or 0)
            
            # Calcular promedios y máximos
            prom_origen = sum(riesgos_origen) / len(riesgos_origen) if riesgos_origen else 0
            prom_destino = sum(riesgos_destino) / len(riesgos_destino) if riesgos_destino else 0
            max_origen = max(riesgos_origen) if riesgos_origen else 0
            max_destino = max(riesgos_destino) if riesgos_destino else 0
            
            # Comparar activos comunes
            activos_comunes = set(resultados_origen.keys()) & set(resultados_destino.keys())
            
            mejoras = []
            deterioros = []
            sin_cambio = 0
            
            for activo_id in activos_comunes:
                origen = resultados_origen[activo_id]
                destino = resultados_destino[activo_id]
                
                delta = destino["riesgo_promedio"] - origen["riesgo_promedio"]
                
                if delta < -0.5:  # Mejora significativa
                    mejoras.append({
                        "id_activo": activo_id,
                        "nombre": origen["nombre"],
                        "riesgo_anterior": round(origen["riesgo_promedio"], 2),
                        "riesgo_actual": round(destino["riesgo_promedio"], 2),
                        "delta": round(delta, 2),
                        "porcentaje": round((delta / origen["riesgo_promedio"]) * 100, 1) if origen["riesgo_promedio"] > 0 else 0
                    })
                elif delta > 0.5:  # Deterioro
                    deterioros.append({
                        "id_activo": activo_id,
                        "nombre": origen["nombre"],
                        "riesgo_anterior": round(origen["riesgo_promedio"], 2),
                        "riesgo_actual": round(destino["riesgo_promedio"], 2),
                        "delta": round(delta, 2),
                        "porcentaje": round((delta / origen["riesgo_promedio"]) * 100, 1) if origen["riesgo_promedio"] > 0 else 0
                    })
                else:
                    sin_cambio += 1
            
            # Crear objeto comparativa
            comparativa = ComparativaEvaluacion(
                eval_origen=eval_origen_id,
                eval_destino=eval_destino_id,
                fecha_comparacion=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                total_activos_origen=len(resultados_origen),
                total_activos_destino=len(resultados_destino),
                riesgo_promedio_origen=round(prom_origen, 2),
                riesgo_promedio_destino=round(prom_destino, 2),
                delta_riesgo_promedio=round(prom_destino - prom_origen, 2),
                riesgo_maximo_origen=round(max_origen, 2),
                riesgo_maximo_destino=round(max_destino, 2),
                delta_riesgo_maximo=round(max_destino - max_origen, 2),
                activos_mejorados=len(mejoras),
                activos_deteriorados=len(deterioros),
                activos_sin_cambio=sin_cambio,
                detalle_mejoras=mejoras,
                detalle_deterioros=deterioros
            )
            
            # Guardar en historial
            guardar_comparativa(comparativa)
            
            return comparativa
            
    except Exception as e:
        print(f"Error comparando evaluaciones: {e}")
        return None


def guardar_comparativa(comp: ComparativaEvaluacion) -> bool:
    """Guarda la comparativa en el historial"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO HISTORIAL_EVALUACIONES (
                    ID_Evaluacion_Origen, ID_Evaluacion_Destino, Fecha_Comparacion,
                    Delta_Riesgo_Promedio, Delta_Riesgo_Maximo,
                    Activos_Mejorados, Activos_Deteriorados, Detalle_JSON
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                comp.eval_origen,
                comp.eval_destino,
                comp.fecha_comparacion,
                comp.delta_riesgo_promedio,
                comp.delta_riesgo_maximo,
                comp.activos_mejorados,
                comp.activos_deteriorados,
                json.dumps({
                    "mejoras": comp.detalle_mejoras,
                    "deterioros": comp.detalle_deterioros
                }, ensure_ascii=False)
            ])
        return True
    except Exception as e:
        print(f"Error guardando comparativa: {e}")
        return False


def listar_historial_comparativas(eval_id: str = None) -> List[Dict]:
    """Lista el historial de comparativas"""
    historial = []
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            if eval_id:
                cursor.execute('''
                    SELECT ID_Evaluacion_Origen, ID_Evaluacion_Destino, Fecha_Comparacion,
                           Delta_Riesgo_Promedio, Activos_Mejorados, Activos_Deteriorados
                    FROM HISTORIAL_EVALUACIONES
                    WHERE ID_Evaluacion_Origen = ? OR ID_Evaluacion_Destino = ?
                    ORDER BY Fecha_Comparacion DESC
                ''', [eval_id, eval_id])
            else:
                cursor.execute('''
                    SELECT ID_Evaluacion_Origen, ID_Evaluacion_Destino, Fecha_Comparacion,
                           Delta_Riesgo_Promedio, Activos_Mejorados, Activos_Deteriorados
                    FROM HISTORIAL_EVALUACIONES
                    ORDER BY Fecha_Comparacion DESC
                ''')
            
            for row in cursor.fetchall():
                historial.append({
                    "eval_origen": row[0],
                    "eval_destino": row[1],
                    "fecha": row[2],
                    "delta_promedio": row[3],
                    "mejorados": row[4],
                    "deteriorados": row[5]
                })
    except Exception as e:
        print(f"Error listando historial: {e}")
    
    return historial


def get_tendencia_riesgo(eval_ids: List[str]) -> List[Dict]:
    """Obtiene la tendencia de riesgo a lo largo de varias evaluaciones"""
    tendencia = []
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            for eval_id in eval_ids:
                cursor.execute('''
                    SELECT e.Nombre, e.Fecha,
                           AVG(r.Riesgo_Promedio), MAX(r.Riesgo_Maximo)
                    FROM EVALUACIONES e
                    LEFT JOIN RESULTADOS_MAGERIT r ON e.ID_Evaluacion = r.ID_Evaluacion
                    WHERE e.ID_Evaluacion = ?
                    GROUP BY e.ID_Evaluacion
                ''', [eval_id])
                
                row = cursor.fetchone()
                if row:
                    tendencia.append({
                        "evaluacion": row[0],
                        "fecha": row[1],
                        "riesgo_promedio": round(row[2] or 0, 2),
                        "riesgo_maximo": round(row[3] or 0, 2)
                    })
    except Exception as e:
        print(f"Error obteniendo tendencia: {e}")
    
    return tendencia
