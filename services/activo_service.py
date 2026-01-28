"""
Servicio de gestión de activos con validación de duplicados - Versión SQLite
"""
import pandas as pd
from typing import Optional, Dict, List
from services.database_service import read_table, insert_rows, update_row, delete_row, query_rows
import datetime as dt


def normalizar_nombre(nombre: str) -> str:
    """Normaliza un nombre para comparación"""
    return str(nombre).strip().lower().replace(" ", "_")


def generar_clave_activo(eval_id: str, nombre: str, ubicacion: str, tipo_servicio: str) -> str:
    """Genera clave lógica única para validación de duplicados"""
    return f"{eval_id}_{normalizar_nombre(nombre)}_{normalizar_nombre(ubicacion)}_{normalizar_nombre(tipo_servicio)}"


def validar_duplicado(eval_id: str, nombre: str, ubicacion: str, 
                     tipo_servicio: str, id_activo_excluir: str = None) -> tuple:
    """
    Valida si existe un activo duplicado en la evaluación
    
    Returns:
        (es_duplicado: bool, mensaje: str)
    """
    activos = read_table("INVENTARIO_ACTIVOS")
    if activos.empty:
        return False, ""
    
    # Filtrar por evaluación
    activos_eval = activos[activos["ID_Evaluacion"].astype(str) == str(eval_id)]
    
    if activos_eval.empty:
        return False, ""
    
    # Generar clave del nuevo activo
    nueva_clave = generar_clave_activo(eval_id, nombre, ubicacion, tipo_servicio)
    
    # Verificar duplicados
    for _, activo in activos_eval.iterrows():
        # Excluir el activo actual si estamos editando
        if id_activo_excluir and str(activo.get("ID_Activo", "")) == str(id_activo_excluir):
            continue
        
        clave_existente = generar_clave_activo(
            eval_id,
            activo.get("Nombre_Activo", ""),
            activo.get("Ubicacion", ""),
            activo.get("Tipo_Servicio", "")
        )
        
        if nueva_clave == clave_existente:
            return True, f"⚠️ Ya existe un activo con el mismo nombre '{nombre}' en {ubicacion} como {tipo_servicio}"
    
    return False, ""


def crear_activo(eval_id: str, datos: Dict) -> tuple:
    """
    Crea un nuevo activo con validación de duplicados
    
    Returns:
        (exito: bool, mensaje: str, id_activo: str)
    """
    # Validar campos obligatorios
    campos_requeridos = ["Nombre_Activo", "Tipo_Activo", "Ubicacion", "Propietario", "Tipo_Servicio"]
    for campo in campos_requeridos:
        if not datos.get(campo):
            return False, f"❌ El campo {campo} es obligatorio", ""
    
    # Validar duplicados
    es_duplicado, msg_dup = validar_duplicado(
        eval_id,
        datos["Nombre_Activo"],
        datos["Ubicacion"],
        datos["Tipo_Servicio"]
    )
    
    if es_duplicado:
        return False, msg_dup, ""
    
    # Generar ID único
    activos = read_table("INVENTARIO_ACTIVOS")
    if activos.empty:
        nuevo_id = f"ACT-{eval_id}-001"
    else:
        # Filtrar activos de esta evaluación
        activos_eval = activos[activos["ID_Evaluacion"].astype(str) == str(eval_id)]
        max_num = len(activos_eval)
        nuevo_id = f"ACT-{eval_id}-{str(max_num + 1).zfill(3)}"
    
    # Crear registro
    nuevo_activo = {
        "ID_Evaluacion": eval_id,
        "ID_Activo": nuevo_id,
        "Nombre_Activo": datos["Nombre_Activo"],
        "Tipo_Activo": datos["Tipo_Activo"],
        "Ubicacion": datos["Ubicacion"],
        "Propietario": datos["Propietario"],
        "Tipo_Servicio": datos["Tipo_Servicio"],
        "App_Critica": datos.get("App_Critica", "No"),
        "Descripcion": datos.get("Descripcion", ""),
        "RTO": datos.get("RTO", ""),
        "RPO": datos.get("RPO", ""),
        "BIA": datos.get("BIA", ""),
        # Nuevos campos técnicos
        "Modelo": datos.get("Modelo", ""),
        "Serial": datos.get("Serial", ""),
        "Fabricante": datos.get("Fabricante", ""),
        "Sistema_Operativo": datos.get("Sistema_Operativo", ""),
        "Virtualizacion": datos.get("Virtualizacion", "N/A"),
        "Desc_Hardware": datos.get("Desc_Hardware", ""),
        "Dependencias": datos.get("Dependencias", ""),
        "Rack": datos.get("Rack", ""),
        "Num_Administradores": datos.get("Num_Administradores", 1),
        # Campos de mantenimiento
        "Fecha_Instalacion": datos.get("Fecha_Instalacion", ""),
        "Vigencia_Tecnologica": datos.get("Vigencia_Tecnologica", "Vigente"),
        "Fecha_Garantia": datos.get("Fecha_Garantia", ""),
        "Proveedor_Mantenimiento": datos.get("Proveedor_Mantenimiento", ""),
        "Contrato_Mantenimiento": datos.get("Contrato_Mantenimiento", "No"),
        # Estado
        "Estado": "Pendiente",
        "Fecha_Creacion": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    insert_rows("INVENTARIO_ACTIVOS", [nuevo_activo])
    
    return True, f"✅ Activo {nuevo_id} creado correctamente", nuevo_id


def actualizar_estado_activo(eval_id: str, id_activo: str, nuevo_estado: str) -> bool:
    """Actualiza el estado de un activo"""
    try:
        update_row(
            "INVENTARIO_ACTIVOS",
            {"Estado": nuevo_estado},
            {"ID_Evaluacion": eval_id, "ID_Activo": id_activo}
        )
        return True
    except Exception:
        return False


def eliminar_activo(eval_id: str, id_activo: str) -> tuple:
    """
    Elimina un activo de la base de datos
    
    Returns:
        (exito: bool, mensaje: str)
    """
    try:
        delete_row(
            "INVENTARIO_ACTIVOS",
            {"ID_Evaluacion": eval_id, "ID_Activo": id_activo}
        )
        return True, f"✅ Activo {id_activo} eliminado correctamente"
    except Exception as e:
        return False, f"❌ Error al eliminar activo: {str(e)}"


def get_activo(eval_id: str, id_activo: str) -> Optional[Dict]:
    """Obtiene los datos de un activo específico"""
    activos = read_table("INVENTARIO_ACTIVOS")
    if activos.empty:
        return None
    
    activo_filtrado = activos[
        (activos["ID_Evaluacion"].astype(str) == str(eval_id)) &
        (activos["ID_Activo"].astype(str) == str(id_activo))
    ]
    
    if activo_filtrado.empty:
        return None
    
    return activo_filtrado.iloc[0].to_dict()


def editar_activo(eval_id: str, id_activo: str, datos: Dict) -> tuple:
    """
    Edita un activo existente con validación de duplicados
    
    Returns:
        (exito: bool, mensaje: str)
    """
    # Validar duplicados (excluyendo el activo actual)
    es_duplicado, msg_dup = validar_duplicado(
        eval_id,
        datos.get("Nombre_Activo", ""),
        datos.get("Ubicacion", ""),
        datos.get("Tipo_Servicio", ""),
        id_activo_excluir=id_activo
    )
    
    if es_duplicado:
        return False, msg_dup
    
    try:
        update_row(
            "INVENTARIO_ACTIVOS",
            datos,
            {"ID_Evaluacion": eval_id, "ID_Activo": id_activo}
        )
        return True, f"✅ Activo {id_activo} actualizado correctamente"
    except Exception as e:
        return False, f"❌ Error al actualizar: {str(e)}"
