"""
Configuración centralizada del sistema
"""

# Excel
EXCEL_PATH = "matriz_riesgos_v2.xlsx"

# Ollama
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_DEFAULT_MODEL = "llama3"
OLLAMA_TIMEOUT = 90

# Cuestionarios
N_PREGUNTAS_BASE = 5
N_PREGUNTAS_IA = 15

# Headers Excel
CUESTIONARIOS_HEADERS = [
    "ID_Evaluacion",
    "ID_Activo",
    "Fecha_Version",
    "ID_Pregunta",
    "Bloque",
    "Pregunta",
    "Opcion_1",
    "Opcion_2",
    "Opcion_3",
    "Opcion_4",
    "Peso",
    "Dimension",
    "Fuente"
]

RESPUESTAS_HEADERS = [
    "ID_Evaluacion",
    "ID_Activo",
    "Fecha_Cuestionario",
    "ID_Pregunta",
    "Bloque",
    "Pregunta",
    "Respuesta",
    "Valor_Numerico",
    "Peso",
    "Dimension",
    "Fecha"
]

IMPACTO_HEADERS = [
    "ID_Evaluacion",
    "ID_Activo",
    "Fecha_Cuestionario",
    "Impacto_D",
    "Impacto_I",
    "Impacto_C",
    "Impacto_Global",
    "Fecha_Calculo"
]

ANALISIS_RIESGO_HEADERS = [
    "ID_Evaluacion",
    "ID_Activo",
    "Fecha_Analisis",
    "Probabilidad",
    "Impacto",
    "Riesgo_Inherente",
    "Amenazas_JSON",
    "Vulnerabilidades_JSON",
    "Salvaguardas_JSON",
    "Justificacion",
    "Modelo_IA"
]

# Colores para niveles de riesgo
RISK_COLORS = {
    "Muy Bajo": "#28a745",
    "Bajo": "#90ee90",
    "Medio": "#ffc107",
    "Alto": "#fd7e14",
    "Crítico": "#dc3545"
}

def get_risk_level(riesgo: int) -> str:
    """Determina nivel de riesgo según valor 1-25"""
    if riesgo <= 4:
        return "Muy Bajo"
    elif riesgo <= 8:
        return "Bajo"
    elif riesgo <= 15:
        return "Medio"
    elif riesgo <= 20:
        return "Alto"
    else:
        return "Crítico"
