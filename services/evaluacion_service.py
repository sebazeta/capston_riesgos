"""
Servicio de gestión de evaluaciones - Versión SQLite
"""
import datetime as dt
import pandas as pd
from services.database_service import read_table, insert_rows, update_row, get_connection


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


def actualizar_evaluacion(eval_id: str, nombre: str = None, descripcion: str = None, 
                         responsable: str = None, estado: str = None) -> bool:
    """
    Actualiza los datos de una evaluación existente
    
    Args:
        eval_id: ID de la evaluación a actualizar
        nombre: Nuevo nombre (opcional)
        descripcion: Nueva descripción (opcional)
        responsable: Nuevo responsable (opcional)
        estado: Nuevo estado (opcional)
    
    Returns:
        True si se actualizó correctamente, False en caso contrario
    """
    try:
        cambios = {}
        if nombre is not None:
            cambios["Nombre"] = nombre
        if descripcion is not None:
            cambios["Descripcion"] = descripcion
        if responsable is not None:
            cambios["Responsable"] = responsable
        if estado is not None:
            cambios["Estado"] = estado
        
        if cambios:
            update_row("EVALUACIONES", cambios, {"ID_Evaluacion": eval_id})
            return True
        return False
    except Exception as e:
        print(f"Error al actualizar evaluación: {e}")
        return False


def eliminar_evaluacion(eval_id: str) -> bool:
    """
    Elimina una evaluación y todos sus datos relacionados
    
    Args:
        eval_id: ID de la evaluación a eliminar
    
    Returns:
        True si se eliminó correctamente, False en caso contrario
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener lista de tablas existentes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tablas_existentes = [row[0] for row in cursor.fetchall()]
            
            # Función auxiliar para eliminar de una tabla si existe
            def eliminar_de_tabla(tabla: str, condicion: str, params: list):
                if tabla in tablas_existentes:
                    try:
                        cursor.execute(f"DELETE FROM {tabla} WHERE {condicion}", params)
                    except Exception as e:
                        print(f"Advertencia al eliminar de {tabla}: {e}")
            
            # ===== LISTA COMPLETA DE TABLAS A LIMPIAR =====
            # Tablas con ID_Evaluacion directo
            tablas_con_evaluacion = [
                "RESULTADOS_MAGERIT",
                "RESULTADOS_MADUREZ",
                "RESULTADOS_CONCENTRACION",
                "RESPUESTAS",
                "SALVAGUARDAS",
                "IDENTIFICACION_VALORACION",
                "CUESTIONARIOS",
                "IMPACTO_ACTIVOS",
                "ANALISIS_RIESGO",
                "MAPA_RIESGOS",
                "RIESGO_ACTIVOS",
                "RIESGO_AMENAZA",
                "VULNERABILIDADES_AMENAZAS",
                "DEGRADACION_AMENAZAS",
                "DEGRADACION",
                "MADUREZ",
                "RIESGO_HEREDADO",
                "IA_RESULTADOS_AVANZADOS",
                "IA_STATUS",
                "IA_EXECUTION_EVIDENCE",
                "IA_VALIDATION_LOG",
                "VULNERABILIDADES",
                "VULNERABILIDADES_ACTIVO",
                "HISTORIAL_EVALUACIONES",
                "TRATAMIENTO_RIESGOS",
                "AUDITORIA_CAMBIOS",
                "CONFIGURACION_EVALUACION"
            ]
            
            # Eliminar de todas las tablas con ID_Evaluacion
            for tabla in tablas_con_evaluacion:
                eliminar_de_tabla(tabla, "ID_Evaluacion = ?", [eval_id])
            
            # Eliminar activos
            eliminar_de_tabla("INVENTARIO_ACTIVOS", "ID_Evaluacion = ?", [eval_id])
            
            # Eliminar evaluación (al final)
            eliminar_de_tabla("EVALUACIONES", "ID_Evaluacion = ?", [eval_id])
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Error al eliminar evaluación: {e}")
        import traceback
        traceback.print_exc()
        return False


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
    
    total = len(activos)
    
    # Contar activos que tienen resultado MAGERIT (realmente evaluados)
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(DISTINCT ID_Activo) FROM RESULTADOS_MAGERIT WHERE ID_Evaluacion = ?",
                [eval_id]
            )
            evaluados = cursor.fetchone()[0] or 0
    except:
        evaluados = 0
    
    # Contar por estado de cuestionario
    estados = activos["Estado"].value_counts().to_dict() if "Estado" in activos.columns else {}
    
    # Pendientes = sin cuestionario completo
    pendientes = estados.get("Pendiente", 0) + estados.get("Incompleto", 0)
    
    # Progreso basado en activos evaluados (con resultado MAGERIT)
    progreso = round((evaluados / total * 100), 1) if total > 0 else 0
    
    return {
        "total_activos": total,
        "pendientes": pendientes,
        "incompletos": estados.get("Incompleto", 0),
        "completos": estados.get("Completo", 0),
        "evaluados": evaluados,
        "progreso": progreso
    }
