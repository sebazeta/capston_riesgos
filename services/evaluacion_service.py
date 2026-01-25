"""
Servicio de gestión de evaluaciones - Versión SQLite
"""
import datetime as dt
import pandas as pd
from services.database_service import read_table, insert_rows, update_row


def crear_evaluacion(nombre: str, descripcion: str, responsable: str, 
                     origen_id: str = None) -> str:
    """
    Crea una nueva evaluación
    
    Args:
        nombre: Nombre de la evaluación
        descripcion: Descripción
        responsable: Persona responsable
        origen_id: ID de evaluación origen si es re-evaluación
    
    Returns:
        ID de la nueva evaluación
    """
    evals = read_table("EVALUACIONES")
    
    # Generar ID único
    if evals.empty:
        nuevo_id = "EVA-001"
    else:
        max_num = 0
        for eval_id in evals["ID_Evaluacion"].dropna():
            try:
                num = int(str(eval_id).split("-")[1])
                max_num = max(max_num, num)
            except:
                pass
        nuevo_id = f"EVA-{str(max_num + 1).zfill(3)}"
    
    # Crear registro
    nueva_eval = {
        "ID_Evaluacion": nuevo_id,
        "Nombre": nombre,
        "Descripcion": descripcion,
        "Fecha_Creacion": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Responsable": responsable,
        "Estado": "En Progreso",
        "Origen_Re_Evaluacion": origen_id if origen_id else ""
    }
    
    insert_rows("EVALUACIONES", [nueva_eval])
    
    # Si es re-evaluación, copiar activos
    if origen_id:
        copiar_activos_evaluacion(origen_id, nuevo_id)
    
    return nuevo_id


def copiar_activos_evaluacion(origen_id: str, destino_id: str):
    """
    Copia los activos de una evaluación a otra (solo metadatos, sin respuestas)
    Genera nuevos IDs únicos para evitar conflictos de UNIQUE constraint
    """
    activos = read_table("INVENTARIO_ACTIVOS")
    if activos.empty:
        return
    
    # Filtrar activos de la evaluación origen
    activos_origen = activos[activos["ID_Evaluacion"].astype(str) == str(origen_id)]
    
    if activos_origen.empty:
        return
    
    # Obtener el máximo número de activo existente para generar nuevos IDs
    max_num = 0
    for activo_id in activos["ID_Activo"].dropna():
        try:
            # Formato: ACT-EVA-XXX-YYY
            partes = str(activo_id).split("-")
            if len(partes) >= 4:
                num = int(partes[3])
                max_num = max(max_num, num)
        except:
            pass
    
    # Copiar con nuevo ID de evaluación y nuevos IDs de activo
    nuevos_activos = []
    contador = max_num + 1
    for _, activo in activos_origen.iterrows():
        nuevo_activo = activo.to_dict()
        # Generar nuevo ID único para el activo
        nuevo_activo["ID_Activo"] = f"ACT-{destino_id}-{str(contador).zfill(3)}"
        nuevo_activo["ID_Evaluacion"] = destino_id
        nuevo_activo["Estado"] = "Pendiente"
        contador += 1
        nuevos_activos.append(nuevo_activo)
    
    if nuevos_activos:
        insert_rows("INVENTARIO_ACTIVOS", nuevos_activos)


def get_evaluaciones() -> pd.DataFrame:
    """Obtiene todas las evaluaciones"""
    return read_table("EVALUACIONES")


def actualizar_estado_evaluacion(eval_id: str, nuevo_estado: str):
    """Actualiza el estado de una evaluación"""
    try:
        update_row(
            "EVALUACIONES",
            {"Estado": nuevo_estado},
            {"ID_Evaluacion": eval_id}
        )
        return True
    except Exception:
        return False


def get_activos_por_evaluacion(eval_id: str) -> pd.DataFrame:
    """Obtiene todos los activos de una evaluación"""
    activos = read_table("INVENTARIO_ACTIVOS")
    if activos.empty:
        return pd.DataFrame()
    
    return activos[activos["ID_Evaluacion"].astype(str) == str(eval_id)]


def get_estadisticas_evaluacion(eval_id: str) -> dict:
    """Obtiene estadísticas de una evaluación"""
    activos = get_activos_por_evaluacion(eval_id)
    
    if activos.empty:
        return {
            "total_activos": 0,
            "pendientes": 0,
            "incompletos": 0,
            "completos": 0,
            "evaluados": 0,
            "progreso": 0
        }
    
    estados = activos["Estado"].value_counts().to_dict() if "Estado" in activos.columns else {}
    
    total = len(activos)
    evaluados = estados.get("Evaluado", 0)
    progreso = round((evaluados / total * 100), 2) if total > 0 else 0
    
    return {
        "total_activos": total,
        "pendientes": estados.get("Pendiente", 0),
        "incompletos": estados.get("Incompleto", 0),
        "completos": estados.get("Completo", 0),
        "evaluados": evaluados,
        "progreso": progreso
    }
