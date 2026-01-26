"""
SERVICIO DE IA AVANZADA PARA TITA
==================================
Funcionalidades adicionales de IA usando Ollama LOCAL:
1. Generador de Planes de Tratamiento
2. Chatbot Consultor MAGERIT
3. Resumen Ejecutivo Automático
4. Predicción de Riesgo Futuro
5. Priorización Inteligente de Controles

IMPORTANTE: Todo funciona 100% offline con Ollama local.
"""
import json
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import pandas as pd
from services.database_service import read_table, insert_rows, query_rows, delete_rows


# ==================== CONFIGURACIÓN ====================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO_DEFAULT = "llama3.2:1b"
TIMEOUT = 60  # Más tiempo para respuestas largas


# ==================== PERSISTENCIA DE RESULTADOS IA ====================

def _init_tabla_resultados_ia():
    """Inicializa la tabla para guardar resultados de IA Avanzada."""
    import sqlite3
    from services.database_service import DB_PATH
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS IA_RESULTADOS_AVANZADOS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_evaluacion TEXT NOT NULL,
            tipo_resultado TEXT NOT NULL,
            datos_json TEXT NOT NULL,
            fecha_generacion TEXT NOT NULL,
            modelo_ia TEXT,
            UNIQUE(id_evaluacion, tipo_resultado)
        )
    """)
    
    conn.commit()
    conn.close()


def guardar_resultado_ia(eval_id: str, tipo: str, datos: dict, modelo: str = None):
    """
    Guarda un resultado de IA en la base de datos.
    
    Args:
        eval_id: ID de la evaluación
        tipo: Tipo de resultado (resumen, prediccion, priorizacion, planes)
        datos: Diccionario con los datos a guardar
        modelo: Modelo de IA usado
    """
    _init_tabla_resultados_ia()
    
    import sqlite3
    from services.database_service import DB_PATH
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Usar REPLACE para actualizar si ya existe
    cursor.execute("""
        INSERT OR REPLACE INTO IA_RESULTADOS_AVANZADOS 
        (id_evaluacion, tipo_resultado, datos_json, fecha_generacion, modelo_ia)
        VALUES (?, ?, ?, ?, ?)
    """, (
        eval_id,
        tipo,
        json.dumps(datos, ensure_ascii=False),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        modelo or MODELO_DEFAULT
    ))
    
    conn.commit()
    conn.close()


def cargar_resultado_ia(eval_id: str, tipo: str) -> Optional[dict]:
    """
    Carga un resultado de IA guardado previamente.
    
    Returns:
        Diccionario con los datos o None si no existe
    """
    _init_tabla_resultados_ia()
    
    import sqlite3
    from services.database_service import DB_PATH
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT datos_json, fecha_generacion, modelo_ia 
        FROM IA_RESULTADOS_AVANZADOS 
        WHERE id_evaluacion = ? AND tipo_resultado = ?
    """, (eval_id, tipo))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "datos": json.loads(row[0]),
            "fecha": row[1],
            "modelo": row[2]
        }
    return None


def eliminar_resultado_ia(eval_id: str, tipo: str):
    """Elimina un resultado guardado."""
    _init_tabla_resultados_ia()
    
    import sqlite3
    from services.database_service import DB_PATH
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM IA_RESULTADOS_AVANZADOS 
        WHERE id_evaluacion = ? AND tipo_resultado = ?
    """, (eval_id, tipo))
    conn.commit()
    conn.close()


# ==================== FUNCIONES AUXILIARES ====================

def obtener_amenazas_evaluacion(eval_id: str) -> pd.DataFrame:
    """
    Extrae las amenazas de una evaluación desde RESULTADOS_MAGERIT.Amenazas_JSON.
    Retorna un DataFrame con las amenazas desagregadas.
    """
    resultados = read_table("RESULTADOS_MAGERIT")
    if resultados.empty:
        return pd.DataFrame()
    
    # Normalizar nombre de columna (puede ser ID_Evaluacion o id_evaluacion)
    col_eval = None
    for c in ["ID_Evaluacion", "id_evaluacion"]:
        if c in resultados.columns:
            col_eval = c
            break
    
    if not col_eval:
        return pd.DataFrame()
    
    # Filtrar por evaluación
    resultados_eval = resultados[resultados[col_eval] == eval_id]
    if resultados_eval.empty:
        return pd.DataFrame()
    
    # Extraer amenazas del JSON
    amenazas_list = []
    for _, row in resultados_eval.iterrows():
        json_str = row.get("Amenazas_JSON", "[]")
        try:
            amenazas = json.loads(json_str) if isinstance(json_str, str) else json_str
            if not isinstance(amenazas, list):
                amenazas = []
        except:
            amenazas = []
        
        id_activo = row.get("ID_Activo", row.get("id_activo", ""))
        nombre_activo = row.get("Nombre_Activo", row.get("nombre_activo", ""))
        
        for am in amenazas:
            amenazas_list.append({
                "id_evaluacion": eval_id,
                "id_activo": id_activo,
                "nombre_activo": nombre_activo,
                "codigo": am.get("codigo", ""),
                "amenaza": am.get("amenaza", ""),
                "tipo_amenaza": am.get("tipo_amenaza", ""),
                "dimension": am.get("dimension", "D"),
                "probabilidad": am.get("probabilidad", 3),
                "impacto": am.get("impacto", 3),
                "riesgo_inherente": am.get("riesgo_inherente", 9),
                "nivel_riesgo": am.get("nivel_riesgo", "MEDIO"),
                "riesgo_residual": am.get("riesgo_residual", 9),
                "tratamiento": am.get("tratamiento", "mitigar"),
                "controles_recomendados": am.get("controles_recomendados", [])
            })
    
    return pd.DataFrame(amenazas_list)


# ==================== MODELOS DE DATOS ====================

@dataclass
class PlanTratamiento:
    """Plan de tratamiento para un riesgo"""
    id_evaluacion: str
    id_activo: str
    codigo_amenaza: str
    nombre_amenaza: str
    nivel_riesgo: str
    acciones_corto_plazo: List[Dict]  # [{accion, responsable, plazo, costo}]
    acciones_mediano_plazo: List[Dict]
    acciones_largo_plazo: List[Dict]
    kpis_seguimiento: List[str]
    inversion_estimada: str
    reduccion_riesgo_esperada: str
    fecha_generacion: str
    modelo_ia: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ResumenEjecutivo:
    """Resumen ejecutivo de una evaluación"""
    id_evaluacion: str
    fecha_generacion: str
    total_activos: int
    total_amenazas: int
    distribucion_riesgo: Dict[str, int]  # {CRITICO: 2, ALTO: 5, ...}
    hallazgos_principales: List[str]
    activos_criticos: List[Dict]
    recomendaciones_prioritarias: List[str]
    inversion_estimada: str
    reduccion_riesgo_esperada: str
    conclusion: str
    modelo_ia: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PrediccionRiesgo:
    """Predicción de evolución del riesgo"""
    id_evaluacion: str
    fecha_generacion: str
    riesgo_actual: float
    proyeccion_sin_controles: List[Dict]  # [{mes: 1, riesgo: 15, nivel: "ALTO"}]
    proyeccion_con_controles: List[Dict]
    factores_incremento: List[str]
    factores_mitigacion: List[str]
    recomendacion: str
    modelo_ia: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ControlPriorizado:
    """Control con priorización inteligente"""
    codigo: str
    nombre: str
    categoria: str
    riesgos_que_mitiga: int
    activos_afectados: List[str]
    costo_estimado: str  # BAJO, MEDIO, ALTO
    tiempo_implementacion: str
    roi_seguridad: int  # 1-5 estrellas
    justificacion: str
    orden_prioridad: int


# ==================== FUNCIÓN BASE DE LLAMADA A OLLAMA ====================

def llamar_ollama_avanzado(
    prompt: str,
    modelo: str = None,
    max_tokens: int = 3000,
    temperature: float = 0.4
) -> Tuple[bool, str]:
    """
    Llama a Ollama con configuración para respuestas largas.
    
    Returns:
        (éxito: bool, respuesta: str)
    """
    modelo_usar = modelo or MODELO_DEFAULT
    
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": modelo_usar,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, data.get("response", "")
        else:
            return False, f"Error HTTP {response.status_code}"
    
    except requests.exceptions.Timeout:
        return False, "Timeout: La IA tardó demasiado en responder"
    except requests.exceptions.ConnectionError:
        return False, "Error: Ollama no está disponible en localhost:11434"
    except Exception as e:
        return False, f"Error: {str(e)}"


def extraer_json_seguro(texto: str) -> Optional[Dict]:
    """Extrae JSON de una respuesta de texto, manejando errores."""
    import re
    
    # Buscar bloque JSON
    patterns = [
        r'```json\s*([\s\S]*?)\s*```',
        r'```\s*([\s\S]*?)\s*```',
        r'\{[\s\S]*\}'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, texto)
        if match:
            json_str = match.group(1) if '```' in pattern else match.group(0)
            try:
                return json.loads(json_str.strip())
            except:
                continue
    
    return None


# ==================== 1. GENERADOR DE PLANES DE TRATAMIENTO ====================

def generar_plan_tratamiento(
    eval_id: str,
    activo_id: str,
    codigo_amenaza: str,
    modelo: str = None
) -> Tuple[bool, Optional[PlanTratamiento], str]:
    """
    Genera un plan de tratamiento detallado para una amenaza específica.
    
    Args:
        eval_id: ID de la evaluación
        activo_id: ID del activo
        codigo_amenaza: Código de la amenaza MAGERIT
        modelo: Modelo de Ollama (opcional)
    
    Returns:
        (éxito, plan, mensaje)
    """
    # Obtener datos del activo
    activos = read_table("INVENTARIO_ACTIVOS")
    activo = activos[activos["ID_Activo"] == activo_id]
    if activo.empty:
        return False, None, f"Activo {activo_id} no encontrado"
    activo = activo.iloc[0]
    
    # Obtener datos de la amenaza
    amenazas = read_table("CATALOGO_AMENAZAS_MAGERIT")
    amenaza = amenazas[amenazas["codigo"] == codigo_amenaza]
    if amenaza.empty:
        return False, None, f"Amenaza {codigo_amenaza} no encontrada"
    amenaza = amenaza.iloc[0]
    
    # Obtener resultado de evaluación si existe
    resultados = read_table("RESULTADOS_MAGERIT")
    resultado = pd.DataFrame()
    if not resultados.empty:
        # Normalizar nombres de columnas (pueden ser ID_Evaluacion o id_evaluacion)
        col_eval = "ID_Evaluacion" if "ID_Evaluacion" in resultados.columns else "id_evaluacion"
        col_activo = "ID_Activo" if "ID_Activo" in resultados.columns else "id_activo"
        if col_eval in resultados.columns and col_activo in resultados.columns:
            resultado = resultados[
                (resultados[col_eval] == eval_id) &
                (resultados[col_activo] == activo_id)
            ]
    nivel_riesgo = "ALTO"
    if not resultado.empty:
        nivel_riesgo = resultado.iloc[0].get("Nivel_Riesgo", resultado.iloc[0].get("nivel_riesgo_inherente", "ALTO"))
    
    # Obtener controles recomendados
    controles = read_table("CATALOGO_CONTROLES_ISO27002")
    
    prompt = f"""Eres un consultor experto en seguridad de la información y gestión de riesgos MAGERIT.

CONTEXTO:
- Activo: {activo.get("Nombre_Activo", "")} ({activo.get("Tipo_Activo", "")})
- Amenaza: [{codigo_amenaza}] {amenaza.get("amenaza", "")}
- Tipo de amenaza: {amenaza.get("tipo_amenaza", "")}
- Nivel de riesgo actual: {nivel_riesgo}
- Dimensión afectada: {amenaza.get("dimension_afectada", "D")}

TAREA:
Genera un plan de tratamiento detallado y práctico para mitigar esta amenaza.

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{{
  "acciones_corto_plazo": [
    {{"accion": "descripción de la acción", "responsable": "rol responsable", "plazo": "1-2 semanas", "costo": "BAJO"}}
  ],
  "acciones_mediano_plazo": [
    {{"accion": "descripción", "responsable": "rol", "plazo": "1-2 meses", "costo": "MEDIO"}}
  ],
  "acciones_largo_plazo": [
    {{"accion": "descripción", "responsable": "rol", "plazo": "3-6 meses", "costo": "ALTO"}}
  ],
  "kpis_seguimiento": [
    "KPI 1 medible",
    "KPI 2 medible"
  ],
  "inversion_estimada": "rango en USD o descripción",
  "reduccion_riesgo_esperada": "porcentaje estimado"
}}

Las acciones deben ser específicas, prácticas y alineadas con ISO 27002.
Incluye al menos 2 acciones por plazo."""

    exito, respuesta = llamar_ollama_avanzado(prompt, modelo, max_tokens=2000)
    
    if not exito:
        # Generar plan heurístico si IA falla
        plan = _generar_plan_heuristico(activo, amenaza, nivel_riesgo, codigo_amenaza, eval_id, activo_id)
        return True, plan, "Plan generado con método heurístico (IA no disponible)"
    
    # Parsear respuesta
    datos = extraer_json_seguro(respuesta)
    if not datos:
        plan = _generar_plan_heuristico(activo, amenaza, nivel_riesgo, codigo_amenaza, eval_id, activo_id)
        return True, plan, "Plan generado con método heurístico (respuesta IA inválida)"
    
    # Construir objeto PlanTratamiento
    plan = PlanTratamiento(
        id_evaluacion=eval_id,
        id_activo=activo_id,
        codigo_amenaza=codigo_amenaza,
        nombre_amenaza=amenaza.get("amenaza", ""),
        nivel_riesgo=nivel_riesgo,
        acciones_corto_plazo=datos.get("acciones_corto_plazo", []),
        acciones_mediano_plazo=datos.get("acciones_mediano_plazo", []),
        acciones_largo_plazo=datos.get("acciones_largo_plazo", []),
        kpis_seguimiento=datos.get("kpis_seguimiento", []),
        inversion_estimada=datos.get("inversion_estimada", "A determinar"),
        reduccion_riesgo_esperada=datos.get("reduccion_riesgo_esperada", "30-50%"),
        fecha_generacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        modelo_ia=modelo or MODELO_DEFAULT
    )
    
    return True, plan, f"Plan de tratamiento generado exitosamente"


def _generar_plan_heuristico(activo, amenaza, nivel_riesgo, codigo_amenaza, eval_id, activo_id) -> PlanTratamiento:
    """Genera un plan de tratamiento usando reglas heurísticas cuando IA falla."""
    
    # Mapeo de acciones por tipo de amenaza
    acciones_por_tipo = {
        "Desastres naturales": {
            "corto": [{"accion": "Revisar y actualizar plan de contingencia", "responsable": "Jefe de TI", "plazo": "2 semanas", "costo": "BAJO"}],
            "mediano": [{"accion": "Implementar respaldos off-site", "responsable": "Administrador de Sistemas", "plazo": "1 mes", "costo": "MEDIO"}],
            "largo": [{"accion": "Evaluar sitio alterno de recuperación", "responsable": "Gerente de TI", "plazo": "6 meses", "costo": "ALTO"}]
        },
        "De origen industrial": {
            "corto": [{"accion": "Verificar UPS y sistemas de energía", "responsable": "Soporte Técnico", "plazo": "1 semana", "costo": "BAJO"}],
            "mediano": [{"accion": "Implementar redundancia eléctrica", "responsable": "Infraestructura", "plazo": "2 meses", "costo": "MEDIO"}],
            "largo": [{"accion": "Migrar a datacenter con certificación Tier III", "responsable": "Dirección TI", "plazo": "6 meses", "costo": "ALTO"}]
        },
        "Errores y fallos no intencionados": {
            "corto": [{"accion": "Capacitar al personal en procedimientos", "responsable": "RRHH/TI", "plazo": "2 semanas", "costo": "BAJO"}],
            "mediano": [{"accion": "Implementar validaciones automáticas", "responsable": "Desarrollo", "plazo": "1 mes", "costo": "MEDIO"}],
            "largo": [{"accion": "Automatizar procesos críticos", "responsable": "Arquitectura TI", "plazo": "3 meses", "costo": "ALTO"}]
        },
        "Ataques intencionados": {
            "corto": [{"accion": "Actualizar firmas de antivirus y firewall", "responsable": "Seguridad TI", "plazo": "1 semana", "costo": "BAJO"}],
            "mediano": [{"accion": "Implementar SIEM/monitoreo de seguridad", "responsable": "Seguridad TI", "plazo": "2 meses", "costo": "MEDIO"}],
            "largo": [{"accion": "Contratar servicio de SOC externo", "responsable": "Dirección TI", "plazo": "6 meses", "costo": "ALTO"}]
        }
    }
    
    tipo = amenaza.get("tipo_amenaza", "Ataques intencionados")
    acciones = acciones_por_tipo.get(tipo, acciones_por_tipo["Ataques intencionados"])
    
    return PlanTratamiento(
        id_evaluacion=eval_id,
        id_activo=activo_id,
        codigo_amenaza=codigo_amenaza,
        nombre_amenaza=amenaza.get("amenaza", ""),
        nivel_riesgo=nivel_riesgo,
        acciones_corto_plazo=acciones["corto"],
        acciones_mediano_plazo=acciones["mediano"],
        acciones_largo_plazo=acciones["largo"],
        kpis_seguimiento=[
            "Tiempo de detección de incidentes",
            "Tiempo de recuperación (RTO)",
            "Número de incidentes por mes"
        ],
        inversion_estimada="$5,000 - $15,000 USD",
        reduccion_riesgo_esperada="40-60%",
        fecha_generacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        modelo_ia="heurístico (fallback)"
    )


def generar_planes_evaluacion(eval_id: str, modelo: str = None) -> List[PlanTratamiento]:
    """Genera planes de tratamiento para todos los riesgos ALTO y CRÍTICO de una evaluación."""
    planes = []
    
    # Obtener amenazas desde RESULTADOS_MAGERIT.Amenazas_JSON
    amenazas_eval = obtener_amenazas_evaluacion(eval_id)
    
    # Validar que hay datos
    if amenazas_eval.empty:
        return planes
    
    if "nivel_riesgo" not in amenazas_eval.columns:
        return planes
    
    # Filtrar solo ALTO y CRÍTICO
    amenazas_criticas = amenazas_eval[
        amenazas_eval["nivel_riesgo"].isin(["ALTO", "CRÍTICO", "CRITICO"])
    ]
    
    for _, row in amenazas_criticas.iterrows():
        exito, plan, _ = generar_plan_tratamiento(
            eval_id,
            row["id_activo"],
            row["codigo"],
            modelo
        )
        if exito and plan:
            planes.append(plan)
    
    return planes


# ==================== 2. CHATBOT CONSULTOR MAGERIT ====================

def consultar_chatbot_magerit(
    eval_id: str,
    pregunta: str,
    historial: List[Dict] = None,
    modelo: str = None
) -> Tuple[bool, str, List[Dict]]:
    """
    Chatbot que responde preguntas sobre la evaluación MAGERIT.
    
    Args:
        eval_id: ID de la evaluación
        pregunta: Pregunta del usuario
        historial: Lista de mensajes previos [{rol: "user"/"assistant", contenido: "..."}]
        modelo: Modelo de Ollama
    
    Returns:
        (éxito, respuesta, historial_actualizado)
    """
    historial = historial or []
    
    # Cargar contexto de la evaluación
    contexto = _construir_contexto_evaluacion(eval_id)
    
    # Construir historial de conversación
    historial_texto = ""
    for msg in historial[-6:]:  # Últimos 6 mensajes para no exceder contexto
        rol = "Usuario" if msg.get("rol") == "user" else "Asistente"
        historial_texto += f"{rol}: {msg.get('contenido', '')}\n"
    
    prompt = f"""Eres TITA-Advisor, un asistente experto en seguridad de la información, metodología MAGERIT v3 e ISO 27002.
Tu rol es ayudar al usuario a entender los resultados de su evaluación de riesgos y dar recomendaciones prácticas.

=== DATOS REALES DE LA EVALUACIÓN ===
{contexto}

=== HISTORIAL DE CONVERSACIÓN ===
{historial_texto}

=== PREGUNTA DEL USUARIO ===
{pregunta}

=== INSTRUCCIONES PARA RESPONDER ===
1. SIEMPRE usa los datos reales de la evaluación mostrados arriba para responder
2. Si preguntan por activos críticos, usa la lista de "ACTIVOS MÁS CRÍTICOS"
3. Si preguntan por amenazas, usa "AMENAZAS MÁS FRECUENTES"
4. Si preguntan por distribución de riesgos, usa "DISTRIBUCIÓN DE RIESGOS"
5. Responde en español de forma clara y profesional
6. Usa viñetas (•) para listas
7. Da recomendaciones específicas basadas en los datos
8. Si no tienes información suficiente, indícalo claramente

RESPUESTA (usa los datos de arriba):"""

    exito, respuesta = llamar_ollama_avanzado(prompt, modelo, max_tokens=1500, temperature=0.3)
    
    if not exito:
        respuesta = _respuesta_chatbot_fallback(pregunta, eval_id)
    
    # Actualizar historial
    historial.append({"rol": "user", "contenido": pregunta})
    historial.append({"rol": "assistant", "contenido": respuesta})
    
    return True, respuesta, historial


def _construir_contexto_evaluacion(eval_id: str) -> str:
    """Construye el contexto de la evaluación para el chatbot."""
    
    # Obtener evaluación
    evaluaciones = read_table("EVALUACIONES")
    
    # Obtener activos
    activos = read_table("INVENTARIO_ACTIVOS")
    activos_eval = pd.DataFrame()
    if not activos.empty and "ID_Evaluacion" in activos.columns:
        activos_eval = activos[activos["ID_Evaluacion"] == eval_id]
    
    # Obtener resultados MAGERIT
    resultados = read_table("RESULTADOS_MAGERIT")
    resultados_eval = pd.DataFrame()
    if not resultados.empty and "id_evaluacion" in resultados.columns:
        resultados_eval = resultados[resultados["id_evaluacion"] == eval_id]
    
    # Obtener amenazas desde JSON de RESULTADOS_MAGERIT
    amenazas_eval = obtener_amenazas_evaluacion(eval_id)
    
    # Construir resumen
    contexto = f"""
EVALUACIÓN: {eval_id}
- Total de activos registrados: {len(activos_eval)}
- Activos evaluados con MAGERIT: {len(resultados_eval)}
- Total amenazas identificadas: {len(amenazas_eval)}

DISTRIBUCIÓN DE RIESGOS (por nivel):
"""
    
    if not amenazas_eval.empty and "nivel_riesgo" in amenazas_eval.columns:
        distribucion = amenazas_eval["nivel_riesgo"].value_counts().to_dict()
        for nivel in ["CRÍTICO", "CRITICO", "ALTO", "MEDIO", "BAJO"]:
            if nivel in distribucion:
                contexto += f"• {nivel}: {distribucion[nivel]} amenazas\n"
    else:
        contexto += "• Sin datos de distribución disponibles\n"
    
    # Activos más críticos con más detalle
    if not resultados_eval.empty:
        contexto += "\nACTIVOS MÁS CRÍTICOS (ordenados por riesgo):\n"
        col_riesgo = "Riesgo_Inherente" if "Riesgo_Inherente" in resultados_eval.columns else "riesgo_inherente_global"
        col_nivel = "Nivel_Riesgo" if "Nivel_Riesgo" in resultados_eval.columns else "nivel_riesgo_inherente"
        col_nombre = "Nombre_Activo" if "Nombre_Activo" in resultados_eval.columns else "nombre_activo"
        
        if col_riesgo in resultados_eval.columns:
            resultados_ordenados = resultados_eval.sort_values(by=col_riesgo, ascending=False).head(5)
        else:
            resultados_ordenados = resultados_eval.head(5)
        
        for i, (_, r) in enumerate(resultados_ordenados.iterrows(), 1):
            nombre = r.get(col_nombre, 'N/A')
            nivel = r.get(col_nivel, 'N/A')
            riesgo = r.get(col_riesgo, 0)
            contexto += f"• {i}. {nombre} - Nivel: {nivel} (Valor: {riesgo})\n"
    else:
        contexto += "\nACTIVOS MÁS CRÍTICOS: Sin datos disponibles\n"
    
    # Amenazas más frecuentes
    if not amenazas_eval.empty and "codigo" in amenazas_eval.columns:
        contexto += "\nAMENAZAS MÁS FRECUENTES:\n"
        frecuentes = amenazas_eval["codigo"].value_counts().head(5)
        catalogo = read_table("CATALOGO_AMENAZAS_MAGERIT")
        for codigo, count in frecuentes.items():
            nombre = catalogo[catalogo["codigo"] == codigo]["amenaza"].values
            nombre = nombre[0] if len(nombre) > 0 else codigo
            contexto += f"- [{codigo}] {nombre}: {count} activos afectados\n"
    
    return contexto


def _respuesta_chatbot_fallback(pregunta: str, eval_id: str) -> str:
    """Genera respuesta de fallback cuando la IA no está disponible."""
    pregunta_lower = pregunta.lower()
    
    # Obtener datos básicos
    resultados = read_table("RESULTADOS_MAGERIT")
    resultados_eval = pd.DataFrame()
    if not resultados.empty:
        col_eval = "ID_Evaluacion" if "ID_Evaluacion" in resultados.columns else "id_evaluacion"
        if col_eval in resultados.columns:
            resultados_eval = resultados[resultados[col_eval] == eval_id]
    
    if "crítico" in pregunta_lower or "critico" in pregunta_lower or "más riesgo" in pregunta_lower:
        col_riesgo = "Riesgo_Inherente" if "Riesgo_Inherente" in resultados_eval.columns else "riesgo_inherente_global"
        col_nivel = "Nivel_Riesgo" if "Nivel_Riesgo" in resultados_eval.columns else "nivel_riesgo_inherente"
        col_nombre = "Nombre_Activo" if "Nombre_Activo" in resultados_eval.columns else "nombre_activo"
        
        if not resultados_eval.empty and col_riesgo in resultados_eval.columns:
            critico = resultados_eval.sort_values(col_riesgo, ascending=False).iloc[0]
            return f"El activo más crítico es **{critico.get(col_nombre, 'N/A')}** con un nivel de riesgo {critico.get(col_nivel, 'ALTO')}."
    
    if "control" in pregunta_lower or "implementar" in pregunta_lower:
        return "Para ver los controles recomendados, consulta la pestaña 'Resultados MAGERIT'. Los controles están priorizados según el impacto en la reducción de riesgos."
    
    if "resumen" in pregunta_lower or "general" in pregunta_lower:
        total = len(resultados_eval)
        return f"La evaluación incluye {total} activos evaluados. Para un resumen completo, utiliza la función 'Resumen Ejecutivo' en la pestaña de IA Avanzada."
    
    return "Aún no hay suficientes datos para responder. Primero ejecuta la evaluación MAGERIT en la pestaña correspondiente."


# ==================== 3. RESUMEN EJECUTIVO AUTOMÁTICO ====================

def generar_resumen_ejecutivo(
    eval_id: str,
    modelo: str = None
) -> Tuple[bool, Optional[ResumenEjecutivo], str]:
    """
    Genera un resumen ejecutivo completo de la evaluación.
    
    Returns:
        (éxito, resumen, mensaje)
    """
    # Recopilar datos de la evaluación
    activos = read_table("INVENTARIO_ACTIVOS")
    activos_eval = pd.DataFrame()
    if not activos.empty and "ID_Evaluacion" in activos.columns:
        activos_eval = activos[activos["ID_Evaluacion"] == eval_id]
    
    resultados = read_table("RESULTADOS_MAGERIT")
    resultados_eval = pd.DataFrame()
    if not resultados.empty:
        col_eval = "ID_Evaluacion" if "ID_Evaluacion" in resultados.columns else "id_evaluacion"
        if col_eval in resultados.columns:
            resultados_eval = resultados[resultados[col_eval] == eval_id]
    
    # Obtener amenazas desde JSON de RESULTADOS_MAGERIT
    amenazas_eval = obtener_amenazas_evaluacion(eval_id)
    
    if resultados_eval.empty:
        return False, None, "No hay resultados de evaluación. Primero ejecuta la evaluación MAGERIT."
    
    # Calcular estadísticas
    total_activos = len(activos_eval)
    total_amenazas = len(amenazas_eval)
    
    distribucion = {}
    if not amenazas_eval.empty and "nivel_riesgo" in amenazas_eval.columns:
        distribucion = amenazas_eval["nivel_riesgo"].value_counts().to_dict()
    
    # Activos críticos
    activos_criticos = []
    if not resultados_eval.empty:
        # Determinar columna de riesgo (puede variar entre mayúsculas/minúsculas)
        col_riesgo = "Riesgo_Inherente" if "Riesgo_Inherente" in resultados_eval.columns else "riesgo_inherente_global"
        col_nivel = "Nivel_Riesgo" if "Nivel_Riesgo" in resultados_eval.columns else "nivel_riesgo_inherente"
        col_nombre = "Nombre_Activo" if "Nombre_Activo" in resultados_eval.columns else "nombre_activo"
        
        if col_riesgo in resultados_eval.columns:
            top_criticos = resultados_eval.sort_values(col_riesgo, ascending=False).head(5)
        else:
            top_criticos = resultados_eval.head(5)
        
        for _, r in top_criticos.iterrows():
            activos_criticos.append({
                "nombre": r.get(col_nombre, r.get("Nombre_Activo", "")),
                "tipo": r.get("Tipo_Activo", r.get("tipo_activo", "")),
                "riesgo": r.get(col_riesgo, 0),
                "nivel": r.get(col_nivel, "")
            })
    
    # Construir prompt para IA
    datos_evaluacion = f"""
DATOS DE LA EVALUACIÓN {eval_id}:
- Total de activos evaluados: {total_activos}
- Total de amenazas identificadas: {total_amenazas}
- Distribución de riesgos: {json.dumps(distribucion)}

ACTIVOS MÁS CRÍTICOS:
"""
    for a in activos_criticos:
        datos_evaluacion += f"- {a['nombre']} ({a['tipo']}): Riesgo {a['nivel']}\n"
    
    prompt = f"""Eres un consultor senior de seguridad de la información.
Genera un resumen ejecutivo profesional para presentar a la alta gerencia.

{datos_evaluacion}

Responde ÚNICAMENTE con un JSON válido con esta estructura:
{{
  "hallazgos_principales": [
    "Hallazgo 1 importante",
    "Hallazgo 2 importante",
    "Hallazgo 3 importante"
  ],
  "recomendaciones_prioritarias": [
    "Recomendación 1 con acción concreta",
    "Recomendación 2 con acción concreta",
    "Recomendación 3 con acción concreta"
  ],
  "inversion_estimada": "$15,000 - $45,000 USD",
  "reduccion_riesgo_esperada": "40-60%",
  "conclusion": "Párrafo de conclusión ejecutiva de 2-3 oraciones"
}}

IMPORTANTE:
- Para inversion_estimada: proporciona un rango en USD basado en los {total_amenazas} riesgos identificados (ej: "$10,000 - $30,000 USD")
- Para reduccion_riesgo_esperada: proporciona un porcentaje realista (ej: "35-50%")
- Sé específico con números concretos, NO uses texto genérico

Sé específico, profesional y orientado a la acción."""

    exito, respuesta = llamar_ollama_avanzado(prompt, modelo, max_tokens=1500)
    
    if exito:
        datos = extraer_json_seguro(respuesta)
        if datos:
            resumen = ResumenEjecutivo(
                id_evaluacion=eval_id,
                fecha_generacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                total_activos=total_activos,
                total_amenazas=total_amenazas,
                distribucion_riesgo=distribucion,
                hallazgos_principales=datos.get("hallazgos_principales", []),
                activos_criticos=activos_criticos,
                recomendaciones_prioritarias=datos.get("recomendaciones_prioritarias", []),
                inversion_estimada=datos.get("inversion_estimada", "A determinar"),
                reduccion_riesgo_esperada=datos.get("reduccion_riesgo_esperada", "30-50%"),
                conclusion=datos.get("conclusion", ""),
                modelo_ia=modelo or MODELO_DEFAULT
            )
            return True, resumen, "Resumen ejecutivo generado exitosamente"
    
    # Fallback heurístico
    resumen = _generar_resumen_heuristico(eval_id, total_activos, total_amenazas, distribucion, activos_criticos)
    return True, resumen, "Resumen generado con método heurístico"


def _generar_resumen_heuristico(eval_id, total_activos, total_amenazas, distribucion, activos_criticos) -> ResumenEjecutivo:
    """Genera resumen ejecutivo usando reglas heurísticas."""
    
    # Calcular hallazgos basados en datos
    hallazgos = []
    criticos = distribucion.get("CRÍTICO", 0) + distribucion.get("CRITICO", 0)
    altos = distribucion.get("ALTO", 0)
    
    if criticos > 0:
        hallazgos.append(f"Se identificaron {criticos} riesgos de nivel CRÍTICO que requieren atención inmediata")
    if altos > 0:
        hallazgos.append(f"Existen {altos} riesgos de nivel ALTO que deben abordarse en el corto plazo")
    
    pct_critico = (criticos + altos) / max(total_amenazas, 1) * 100
    hallazgos.append(f"El {pct_critico:.0f}% de las amenazas identificadas son de nivel ALTO o CRÍTICO")
    
    # Recomendaciones genéricas pero útiles
    recomendaciones = [
        "Implementar controles de respaldo y recuperación (ISO 27002: 8.13) para activos críticos",
        "Establecer monitoreo continuo de seguridad (ISO 27002: 8.16) para detección temprana",
        "Desarrollar plan de respuesta a incidentes (ISO 27002: 5.24) con roles definidos",
        "Realizar capacitación de concientización (ISO 27002: 6.3) al personal"
    ]
    
    return ResumenEjecutivo(
        id_evaluacion=eval_id,
        fecha_generacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_activos=total_activos,
        total_amenazas=total_amenazas,
        distribucion_riesgo=distribucion,
        hallazgos_principales=hallazgos,
        activos_criticos=activos_criticos,
        recomendaciones_prioritarias=recomendaciones,
        inversion_estimada="$10,000 - $30,000 USD (estimación inicial)",
        reduccion_riesgo_esperada="40-60% con implementación completa",
        conclusion=f"La evaluación de {total_activos} activos reveló {total_amenazas} amenazas potenciales. Se recomienda priorizar la mitigación de los {criticos + altos} riesgos de nivel ALTO y CRÍTICO mediante la implementación de los controles ISO 27002 recomendados.",
        modelo_ia="heurístico (fallback)"
    )


# ==================== 4. PREDICCIÓN DE RIESGO FUTURO ====================

def generar_prediccion_riesgo(
    eval_id: str,
    meses_proyeccion: int = 6,
    modelo: str = None
) -> Tuple[bool, Optional[PrediccionRiesgo], str]:
    """
    Genera una predicción de cómo evolucionará el riesgo.
    
    Returns:
        (éxito, predicción, mensaje)
    """
    # Obtener datos actuales
    resultados = read_table("RESULTADOS_MAGERIT")
    resultados_eval = pd.DataFrame()
    if not resultados.empty:
        col_eval = "ID_Evaluacion" if "ID_Evaluacion" in resultados.columns else "id_evaluacion"
        if col_eval in resultados.columns:
            resultados_eval = resultados[resultados[col_eval] == eval_id]
    
    if resultados_eval.empty:
        return False, None, "No hay resultados para generar predicción. Ejecuta primero la evaluación MAGERIT."
    
    # Calcular riesgo promedio actual
    riesgo_actual = 10.0  # Valor por defecto
    riesgo_residual = 5.0
    if "Riesgo_Inherente" in resultados_eval.columns:
        riesgo_actual = resultados_eval["Riesgo_Inherente"].mean()
    elif "riesgo_inherente_global" in resultados_eval.columns:
        riesgo_actual = resultados_eval["riesgo_inherente_global"].mean()
    if "Riesgo_Residual" in resultados_eval.columns:
        riesgo_residual = resultados_eval["Riesgo_Residual"].mean()
    elif "riesgo_residual_global" in resultados_eval.columns:
        riesgo_residual = resultados_eval["riesgo_residual_global"].mean()
    
    # Obtener amenazas desde JSON de RESULTADOS_MAGERIT
    amenazas_eval = obtener_amenazas_evaluacion(eval_id)
    
    prompt = f"""Eres un analista de riesgos de seguridad de la información.
Analiza la siguiente situación y genera una predicción de evolución del riesgo.

SITUACIÓN ACTUAL:
- Riesgo inherente promedio: {riesgo_actual:.1f} (escala 1-25)
- Riesgo residual promedio: {riesgo_residual:.1f}
- Total de amenazas identificadas: {len(amenazas_eval)}
- Período de proyección: {meses_proyeccion} meses

Responde ÚNICAMENTE con un JSON válido:
{{
  "proyeccion_sin_controles": [
    {{"mes": 1, "riesgo": 12, "nivel": "ALTO"}},
    {{"mes": 3, "riesgo": 15, "nivel": "ALTO"}},
    {{"mes": 6, "riesgo": 18, "nivel": "CRÍTICO"}}
  ],
  "proyeccion_con_controles": [
    {{"mes": 1, "riesgo": 10, "nivel": "MEDIO"}},
    {{"mes": 3, "riesgo": 7, "nivel": "MEDIO"}},
    {{"mes": 6, "riesgo": 5, "nivel": "BAJO"}}
  ],
  "factores_incremento": [
    "Factor 1 que incrementa el riesgo",
    "Factor 2"
  ],
  "factores_mitigacion": [
    "Factor 1 que reduce el riesgo",
    "Factor 2"
  ],
  "recomendacion": "Recomendación principal basada en el análisis"
}}

Basa la proyección en tendencias realistas de ciberseguridad."""

    exito, respuesta = llamar_ollama_avanzado(prompt, modelo, max_tokens=1500)
    
    if exito:
        datos = extraer_json_seguro(respuesta)
        if datos:
            prediccion = PrediccionRiesgo(
                id_evaluacion=eval_id,
                fecha_generacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                riesgo_actual=riesgo_actual,
                proyeccion_sin_controles=datos.get("proyeccion_sin_controles", []),
                proyeccion_con_controles=datos.get("proyeccion_con_controles", []),
                factores_incremento=datos.get("factores_incremento", []),
                factores_mitigacion=datos.get("factores_mitigacion", []),
                recomendacion=datos.get("recomendacion", ""),
                modelo_ia=modelo or MODELO_DEFAULT
            )
            return True, prediccion, "Predicción generada exitosamente"
    
    # Fallback heurístico
    prediccion = _generar_prediccion_heuristica(eval_id, riesgo_actual, riesgo_residual, meses_proyeccion)
    return True, prediccion, "Predicción generada con método heurístico"


def _generar_prediccion_heuristica(eval_id, riesgo_actual, riesgo_residual, meses) -> PrediccionRiesgo:
    """Genera predicción usando modelo heurístico simple."""
    
    # Modelo simple: sin controles el riesgo crece 10% mensual
    # Con controles se reduce hacia el residual
    
    proy_sin = []
    proy_con = []
    
    for m in [1, 3, 6]:
        if m <= meses:
            # Sin controles: incremento gradual
            r_sin = min(25, riesgo_actual * (1 + 0.08 * m))
            proy_sin.append({
                "mes": m,
                "riesgo": round(r_sin, 1),
                "nivel": _get_nivel(r_sin)
            })
            
            # Con controles: reducción hacia residual
            factor = 1 - (0.15 * m)
            r_con = max(riesgo_residual, riesgo_actual * factor)
            proy_con.append({
                "mes": m,
                "riesgo": round(r_con, 1),
                "nivel": _get_nivel(r_con)
            })
    
    return PrediccionRiesgo(
        id_evaluacion=eval_id,
        fecha_generacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        riesgo_actual=riesgo_actual,
        proyeccion_sin_controles=proy_sin,
        proyeccion_con_controles=proy_con,
        factores_incremento=[
            "Evolución de amenazas de ransomware y malware",
            "Obsolescencia de sistemas sin parches de seguridad",
            "Aumento de ataques dirigidos a la industria"
        ],
        factores_mitigacion=[
            "Implementación de controles ISO 27002 recomendados",
            "Capacitación continua del personal",
            "Monitoreo y respuesta a incidentes activo"
        ],
        recomendacion="Se recomienda implementar los controles prioritarios en los próximos 30 días para evitar el incremento proyectado del riesgo.",
        modelo_ia="heurístico (fallback)"
    )


def _get_nivel(valor: float) -> str:
    """Determina el nivel de riesgo."""
    if valor >= 20:
        return "CRÍTICO"
    elif valor >= 12:
        return "ALTO"
    elif valor >= 6:
        return "MEDIO"
    elif valor >= 3:
        return "BAJO"
    return "MUY BAJO"


# ==================== 5. PRIORIZACIÓN INTELIGENTE DE CONTROLES ====================

def obtener_controles_evaluacion(eval_id: str) -> pd.DataFrame:
    """
    Extrae los controles recomendados de una evaluación desde RESULTADOS_MAGERIT.
    Los controles están dentro de cada amenaza en el campo Amenazas_JSON.
    """
    resultados = read_table("RESULTADOS_MAGERIT")
    if resultados.empty:
        return pd.DataFrame()
    
    # Normalizar nombre de columna
    col_eval = "ID_Evaluacion" if "ID_Evaluacion" in resultados.columns else "id_evaluacion"
    if col_eval not in resultados.columns:
        return pd.DataFrame()
    
    # Filtrar por evaluación
    resultados_eval = resultados[resultados[col_eval] == eval_id]
    if resultados_eval.empty:
        return pd.DataFrame()
    
    # Extraer controles del JSON de amenazas
    controles_list = []
    for _, row in resultados_eval.iterrows():
        json_str = row.get("Amenazas_JSON", "[]")
        try:
            amenazas = json.loads(json_str) if isinstance(json_str, str) else json_str
            if not isinstance(amenazas, list):
                amenazas = []
        except:
            amenazas = []
        
        id_activo = row.get("ID_Activo", row.get("id_activo", ""))
        
        for am in amenazas:
            codigo_amenaza = am.get("codigo", "")
            controles_rec = am.get("controles_recomendados", [])
            for ctrl in controles_rec:
                controles_list.append({
                    "id_evaluacion": eval_id,
                    "id_activo": id_activo,
                    "codigo": ctrl.get("codigo", ""),
                    "nombre": ctrl.get("nombre", ""),
                    "categoria": ctrl.get("categoria", ""),
                    "prioridad": ctrl.get("prioridad", "Media"),
                    "amenaza_origen": codigo_amenaza,
                    "motivo": ctrl.get("motivo", "")
                })
    
    return pd.DataFrame(controles_list)


def generar_priorizacion_controles(
    eval_id: str,
    modelo: str = None
) -> Tuple[bool, List[ControlPriorizado], str]:
    """
    Genera una lista priorizada de controles por ROI de seguridad.
    
    Returns:
        (éxito, lista_controles, mensaje)
    """
    # Obtener controles desde JSON de RESULTADOS_MAGERIT
    controles_eval = obtener_controles_evaluacion(eval_id)
    
    # Validar datos
    if controles_eval.empty:
        return False, [], "No hay controles recomendados. Ejecuta primero la evaluación MAGERIT."
    
    # Obtener catálogo de controles
    catalogo = read_table("CATALOGO_CONTROLES_ISO27002")
    
    # Agrupar por código de control
    controles_agrupados = {}
    for _, ctrl in controles_eval.iterrows():
        codigo = ctrl.get("codigo", "")
        if not codigo:
            continue
        if codigo not in controles_agrupados:
            controles_agrupados[codigo] = {
                "activos": [],
                "prioridades": [],
                "amenazas": []
            }
        controles_agrupados[codigo]["activos"].append(ctrl.get("id_activo", ""))
        controles_agrupados[codigo]["prioridades"].append(ctrl.get("prioridad", "Media"))
        controles_agrupados[codigo]["amenazas"].append(ctrl.get("amenaza_origen", ""))
    
    if not controles_agrupados:
        return False, [], "No se encontraron controles válidos"
    
    # Construir lista para prompt
    controles_texto = ""
    for codigo, datos in controles_agrupados.items():
        if not catalogo.empty and "codigo" in catalogo.columns:
            info = catalogo[catalogo["codigo"] == codigo]
            nombre = info["nombre"].values[0] if not info.empty else codigo
        else:
            nombre = codigo
        controles_texto += f"- [{codigo}] {nombre}: Mitiga {len(set(datos['amenazas']))} amenazas en {len(set(datos['activos']))} activos\n"
    
    prompt = f"""Eres un consultor de seguridad que debe priorizar controles por costo-beneficio.

CONTROLES RECOMENDADOS EN LA EVALUACIÓN:
{controles_texto}

Para cada control, asigna:
- costo_estimado: BAJO, MEDIO o ALTO
- tiempo_implementacion: "1-2 semanas", "1 mes", "2-3 meses", etc.
- roi_seguridad: 1 a 5 (5 = máximo retorno)
- justificacion: por qué esta prioridad

Responde ÚNICAMENTE con un JSON:
{{
  "controles_priorizados": [
    {{
      "codigo": "8.13",
      "costo_estimado": "BAJO",
      "tiempo_implementacion": "2 semanas",
      "roi_seguridad": 5,
      "justificacion": "Alto impacto con baja inversión"
    }}
  ]
}}

Ordena de mayor a menor ROI."""

    exito, respuesta = llamar_ollama_avanzado(prompt, modelo, max_tokens=2000)
    
    controles_priorizados = []
    datos_ia = {}
    
    if exito:
        datos = extraer_json_seguro(respuesta)
        if datos and "controles_priorizados" in datos:
            for cp in datos["controles_priorizados"]:
                datos_ia[cp.get("codigo", "")] = cp
    
    # Construir lista final
    orden = 1
    for codigo, datos_ctrl in sorted(
        controles_agrupados.items(),
        key=lambda x: len(set(x[1]["amenazas"])),
        reverse=True
    ):
        info = catalogo[catalogo["codigo"] == codigo]
        nombre = info["nombre"].values[0] if not info.empty else codigo
        categoria = info["categoria"].values[0] if not info.empty else ""
        
        # Usar datos de IA si están disponibles
        ia_data = datos_ia.get(codigo, {})
        
        ctrl_priorizado = ControlPriorizado(
            codigo=codigo,
            nombre=nombre,
            categoria=categoria,
            riesgos_que_mitiga=len(set(datos_ctrl["amenazas"])),
            activos_afectados=list(set(datos_ctrl["activos"])),
            costo_estimado=ia_data.get("costo_estimado", _estimar_costo(codigo)),
            tiempo_implementacion=ia_data.get("tiempo_implementacion", _estimar_tiempo(codigo)),
            roi_seguridad=ia_data.get("roi_seguridad", _calcular_roi_heuristico(len(set(datos_ctrl["amenazas"])))),
            justificacion=ia_data.get("justificacion", f"Mitiga {len(set(datos_ctrl['amenazas']))} amenazas"),
            orden_prioridad=orden
        )
        controles_priorizados.append(ctrl_priorizado)
        orden += 1
    
    # Ordenar por ROI
    controles_priorizados.sort(key=lambda x: x.roi_seguridad, reverse=True)
    for i, ctrl in enumerate(controles_priorizados):
        ctrl.orden_prioridad = i + 1
    
    return True, controles_priorizados, f"{len(controles_priorizados)} controles priorizados"


def _estimar_costo(codigo: str) -> str:
    """Estima costo basado en categoría del control."""
    # Controles organizacionales (5.x, 6.x) suelen ser de bajo costo
    if codigo.startswith("5.") or codigo.startswith("6."):
        return "BAJO"
    # Controles físicos (7.x) suelen ser de costo medio-alto
    elif codigo.startswith("7."):
        return "MEDIO"
    # Controles tecnológicos (8.x) varían
    else:
        return "MEDIO"


def _estimar_tiempo(codigo: str) -> str:
    """Estima tiempo de implementación."""
    if codigo.startswith("5."):
        return "2-4 semanas"
    elif codigo.startswith("6."):
        return "1-2 semanas"
    elif codigo.startswith("7."):
        return "1-3 meses"
    else:
        return "2-6 semanas"


def _calcular_roi_heuristico(num_amenazas: int) -> int:
    """Calcula ROI basado en número de amenazas mitigadas."""
    if num_amenazas >= 5:
        return 5
    elif num_amenazas >= 3:
        return 4
    elif num_amenazas >= 2:
        return 3
    else:
        return 2


# ==================== VERIFICACIÓN DE DISPONIBILIDAD ====================

def verificar_ia_disponible() -> Tuple[bool, str]:
    """Verifica si Ollama está disponible."""
    try:
        response = requests.get(
            "http://localhost:11434/api/tags",
            timeout=5
        )
        if response.status_code == 200:
            modelos = response.json().get("models", [])
            return True, f"Ollama disponible con {len(modelos)} modelos"
        return False, "Ollama no responde correctamente"
    except:
        return False, "Ollama no está disponible en localhost:11434"
