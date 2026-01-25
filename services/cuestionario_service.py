"""
Servicio de cuestionarios estáticos según tipo de activo - Versión SQLite
"""
import datetime as dt
import pandas as pd
from typing import List, Dict
from services.database_service import read_table, insert_rows, delete_row


# Configuración - Máximo 21 preguntas por cuestionario (nuevo formato oficial)
MAX_PREGUNTAS = 21


def get_banco_preguntas(tipo_activo: str) -> pd.DataFrame:
    """
    Obtiene el banco de preguntas según tipo de activo
    
    Args:
        tipo_activo: "Servidor Físico" o "Servidor Virtual"
    
    Returns:
        DataFrame con preguntas del banco correspondiente
    """
    if "Físico" in tipo_activo or "físico" in tipo_activo.lower():
        banco = read_table("BANCO_PREGUNTAS_FISICAS")
    elif "Virtual" in tipo_activo or "virtual" in tipo_activo.lower():
        banco = read_table("BANCO_PREGUNTAS_VIRTUALES")
    else:
        # Fallback al banco de físicos por defecto
        banco = read_table("BANCO_PREGUNTAS_FISICAS")
    
    return banco


def generar_cuestionario(eval_id: str, activo: Dict, model: str = "llama3") -> tuple:
    """
    Genera un cuestionario para un activo usando SOLO el banco de preguntas correspondiente.
    NO usa IA - simplemente asigna las preguntas del banco según el tipo de activo.
    
    Args:
        eval_id: ID de evaluación
        activo: Diccionario con datos del activo
        model: Ignorado (mantenido por compatibilidad)
    
    Returns:
        (exito: bool, mensaje: str, num_preguntas: int)
    """
    activo_id = activo.get("ID_Activo")
    tipo_activo = activo.get("Tipo_Activo", "Servidor Físico")
    
    # Verificar si ya existe cuestionario
    cuestionarios_existentes = read_table("CUESTIONARIOS")
    if not cuestionarios_existentes.empty:
        ya_existe = not cuestionarios_existentes[
            (cuestionarios_existentes["ID_Evaluacion"].astype(str) == str(eval_id)) &
            (cuestionarios_existentes["ID_Activo"].astype(str) == str(activo_id))
        ].empty
        
        if ya_existe:
            return False, "⚠️ Este activo ya tiene un cuestionario generado", 0
    
    # Generar timestamp de versión
    fecha_version = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Obtener banco de preguntas según tipo de activo
    banco = get_banco_preguntas(tipo_activo)
    
    if banco.empty:
        return False, f"❌ No existe banco de preguntas para {tipo_activo}", 0
    
    # Tomar TODAS las preguntas del banco (máximo 21 - formato oficial)
    num_preguntas = min(21, len(banco))
    preguntas_seleccionadas = banco.head(num_preguntas)
    
    # Preparar filas para guardar
    rows = []
    for idx, pregunta in preguntas_seleccionadas.iterrows():
        rows.append({
            "ID_Evaluacion": eval_id,
            "ID_Activo": activo_id,
            "Fecha_Version": fecha_version,
            "ID_Pregunta": str(pregunta.get("ID_Pregunta", f"P-{idx+1}")),
            "Bloque": str(pregunta.get("Bloque", "")),
            "Pregunta": str(pregunta.get("Pregunta", "")),
            "Opcion_1": str(pregunta.get("Opcion_1", "")),
            "Opcion_2": str(pregunta.get("Opcion_2", "")),
            "Opcion_3": str(pregunta.get("Opcion_3", "")),
            "Opcion_4": str(pregunta.get("Opcion_4", "")),
            "Peso": int(pregunta.get("Peso", 3)),
            "Dimension": str(pregunta.get("Dimension", "I")),
            "Fuente": "Banco"
        })
    
    # Guardar cuestionario
    if rows:
        insert_rows("CUESTIONARIOS", rows)
        return True, f"✅ Cuestionario generado con {len(rows)} preguntas del banco {tipo_activo}", len(rows)
    else:
        return False, "❌ No se pudieron cargar preguntas del banco", 0


def get_cuestionario(eval_id: str, activo_id: str, fecha_version: str = None) -> pd.DataFrame:
    """
    Obtiene el cuestionario de un activo
    Si no se especifica versión, devuelve la más reciente
    """
    cuestionarios = read_table("CUESTIONARIOS")
    
    if cuestionarios.empty:
        return pd.DataFrame()
    
    # Verificar que existan las columnas necesarias
    if "ID_Evaluacion" not in cuestionarios.columns or "ID_Activo" not in cuestionarios.columns:
        return pd.DataFrame()
    
    # Filtrar por evaluación y activo
    filtrado = cuestionarios[
        (cuestionarios["ID_Evaluacion"].astype(str) == str(eval_id)) &
        (cuestionarios["ID_Activo"].astype(str) == str(activo_id))
    ]
    
    if filtrado.empty:
        return pd.DataFrame()
    
    # Si se especifica versión y existe la columna, usarla
    if fecha_version and "Fecha_Version" in filtrado.columns:
        filtrado = filtrado[filtrado["Fecha_Version"].astype(str) == str(fecha_version)]
    elif "Fecha_Version" in filtrado.columns:
        # Última versión
        ultima_fecha = filtrado["Fecha_Version"].max()
        filtrado = filtrado[filtrado["Fecha_Version"] == ultima_fecha]
    
    return filtrado


def get_versiones_cuestionario(eval_id: str, activo_id: str) -> List[str]:
    """Obtiene todas las versiones de cuestionario de un activo"""
    cuestionarios = read_table("CUESTIONARIOS")
    
    if cuestionarios.empty:
        return []
    
    filtrado = cuestionarios[
        (cuestionarios["ID_Evaluacion"].astype(str) == str(eval_id)) &
        (cuestionarios["ID_Activo"].astype(str) == str(activo_id))
    ]
    
    if filtrado.empty:
        return []
    
    return sorted(filtrado["Fecha_Version"].dropna().astype(str).unique().tolist())


def verificar_respuestas_existentes(eval_id: str, activo_id: str) -> bool:
    """
    Verifica si ya existen respuestas guardadas para un activo en una evaluación
    
    Returns:
        bool: True si ya existen respuestas, False si no
    """
    respuestas = read_table("RESPUESTAS")
    
    if respuestas.empty:
        return False
    
    existentes = respuestas[
        (respuestas["ID_Evaluacion"].astype(str) == str(eval_id)) &
        (respuestas["ID_Activo"].astype(str) == str(activo_id))
    ]
    
    return not existentes.empty


def guardar_respuestas(eval_id: str, activo_id: str, fecha_cuestionario: str, respuestas: List[Dict]) -> bool:
    """
    Guarda las respuestas de un cuestionario
    
    Args:
        respuestas: Lista de diccionarios con respuestas
    
    Returns:
        bool: éxito de la operación
    """
    if not respuestas:
        return False
    
    # Verificar si ya existen respuestas para este activo
    if verificar_respuestas_existentes(eval_id, activo_id):
        return False  # Ya existen respuestas, no permitir duplicados
    
    # Formatear respuestas
    rows = []
    for resp in respuestas:
        rows.append({
            "ID_Evaluacion": eval_id,
            "ID_Activo": activo_id,
            "Fecha_Cuestionario": fecha_cuestionario,
            "ID_Pregunta": resp["ID_Pregunta"],
            "Bloque": resp.get("Bloque", ""),
            "Pregunta": resp["Pregunta"],
            "Respuesta": resp["Respuesta"],
            "Valor_Numerico": resp.get("Valor_Numerico", 1),
            "Peso": resp["Peso"],
            "Dimension": resp["Dimension"],
            "Fecha": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    insert_rows("RESPUESTAS", rows)
    return True


def get_respuestas(eval_id: str, activo_id: str, fecha_cuestionario: str = None) -> pd.DataFrame:
    """Obtiene las respuestas guardadas de un cuestionario"""
    respuestas = read_table("RESPUESTAS")
    
    if respuestas.empty:
        return pd.DataFrame()
    
    filtrado = respuestas[
        (respuestas["ID_Evaluacion"].astype(str) == str(eval_id)) &
        (respuestas["ID_Activo"].astype(str) == str(activo_id))
    ]
    
    if fecha_cuestionario:
        filtrado = filtrado[filtrado["Fecha_Cuestionario"].astype(str) == str(fecha_cuestionario)]
    
    return filtrado


def verificar_cuestionario_completo(eval_id: str, activo_id: str, fecha_cuestionario: str = None) -> bool:
    """
    Verifica si un cuestionario está completo
    
    Returns:
        bool: True si está completo, False si no
    """
    cuestionario = get_cuestionario(eval_id, activo_id, fecha_cuestionario)
    respuestas = get_respuestas(eval_id, activo_id, fecha_cuestionario)
    
    if cuestionario.empty:
        return False
    
    total = len(cuestionario)
    respondidas = len(respuestas)
    
    return respondidas >= total


def invalidar_analisis_ia(eval_id: str, activo_id: str) -> bool:
    """
    REGLA CRÍTICA: Si se modifican respuestas después de evaluar con IA,
    el análisis IA queda obsoleto y debe marcarse como tal.
    
    Esta función elimina el análisis IA del activo para forzar re-evaluación.
    El estado del activo volverá automáticamente a "Completo".
    
    Args:
        eval_id: ID de evaluación
        activo_id: ID de activo
    
    Returns:
        bool: True si se invalidó análisis, False si no había análisis
    """
    try:
        # Verificar si existe análisis
        analisis = read_table("ANALISIS_RIESGO")
        if analisis.empty:
            return False
        
        existe = not analisis[
            (analisis["ID_Evaluacion"].astype(str) == str(eval_id)) &
            (analisis["ID_Activo"].astype(str) == str(activo_id))
        ].empty
        
        if existe:
            delete_row("ANALISIS_RIESGO", {
                "ID_Evaluacion": eval_id,
                "ID_Activo": activo_id
            })
            return True
        return False
    except Exception as e:
        print(f"Error invalidando análisis: {str(e)}")
        return False
