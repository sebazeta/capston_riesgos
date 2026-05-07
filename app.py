"""
PROYECTO TITA - Sistema de Evaluación de Riesgos MAGERIT/ISO 27002
Versión: FINAL (Flujo Correcto con Evaluación como Capa 1 Obligatoria)

REGLAS FUNDAMENTALES:
1. Evaluación es contenedor obligatorio (Capa 1)
2. Activos NO pueden existir sin evaluación
3. Estados son automáticos (calculados, no seteados manualmente)
4. Dashboards reactivos (siempre leen desde Excel)
"""
import json
import datetime as dt
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from streamlit_option_menu import option_menu

# Plotly dark template que combina con el tema TITA
_TITA_PLOTLY = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(10,22,40,0.4)",
        font=dict(color="#c0ccd8", family="Segoe UI, sans-serif"),
        title=dict(font=dict(color="#e0eff8", size=16)),
        colorway=["#2ec4b6", "#42a5f5", "#ffb74d", "#ef5350", "#ab47bc",
                   "#66bb6a", "#26c6da", "#ffa726", "#7e57c2", "#ec407a"],
        xaxis=dict(gridcolor="rgba(46,196,182,0.08)", zerolinecolor="rgba(46,196,182,0.12)"),
        yaxis=dict(gridcolor="rgba(46,196,182,0.08)", zerolinecolor="rgba(46,196,182,0.12)"),
    )
)
pio.templates["tita_dark"] = _TITA_PLOTLY
pio.templates.default = "plotly_dark+tita_dark"

# Importar servicios
from services import (
    # Database SQLite
    ensure_sheet_exists, read_sheet, append_rows, read_table,
    set_eval_active, update_cuestionarios_version,
    # Ollama
    ollama_generate, ollama_analyze_risk,
    extract_json_array, validate_ia_questions,
    # Evaluaciones
    crear_evaluacion, get_evaluaciones,
    actualizar_estado_evaluacion, get_activos_por_evaluacion,
    get_estadisticas_evaluacion,
    # Activos
    crear_activo, editar_activo, eliminar_activo,
    get_activo, actualizar_estado_activo, validar_duplicado,
    # Cuestionarios
    generar_cuestionario, get_cuestionario,
    guardar_respuestas, verificar_cuestionario_completo, invalidar_analisis_ia,
    verificar_respuestas_existentes,
    # Motor MAGERIT v3
    get_nivel_riesgo, get_color_riesgo,
    evaluar_activo_magerit, guardar_resultado_magerit,
    get_resultado_magerit, get_resumen_evaluacion, get_amenazas_activo,
    # IA MAGERIT
    analizar_activo_con_ia, verificar_ollama_disponible,
    crear_evaluacion_manual, get_catalogo_amenazas, get_catalogo_controles,
    # Madurez de Ciberseguridad
    calcular_madurez_evaluacion, guardar_madurez, get_madurez_evaluacion,
    comparar_madurez, get_controles_existentes_detallados
)
# Componentes Dashboard
try:
    from components import (
        render_mapa_calor_riesgos, render_ranking_activos,
        render_comparativo_riesgos, render_distribucion_amenazas,
        render_cobertura_controles, render_resumen_ejecutivo,
        render_detalle_activo, render_gauge_riesgo, COLORES_RIESGO,
        render_madurez_completo, render_comparativa_madurez,
        render_controles_existentes,
        render_ranking_activos_criticos,
        render_activos_urgente_tratamiento,
        render_dashboard_amenazas,
        render_dashboard_amenazas_mejorado,
        render_dashboard_controles_salvaguardas,
        render_dashboard_evaluacion_completo,
        render_matriz_5x5_activos
    )
    DASHBOARD_DISPONIBLE = True
except ImportError as e:
    DASHBOARD_DISPONIBLE = False
    print(f"Warning: Dashboard not available: {e}")

# Componentes de Validación IA
try:
    from components.ia_validation_ui import (
        render_tab_validacion_ia, render_estado_ia_badge,
        render_boton_evaluar_bloqueado, verificar_ia_lista_para_evaluar,
        render_indicador_ia_en_header
    )
    from services.ia_validation_service import obtener_estado_ia
    VALIDACION_IA_DISPONIBLE = True
except ImportError as e:
    VALIDACION_IA_DISPONIBLE = False
    print(f"Warning: IA Validation not available: {e}")

# Componentes de Carga Masiva
try:
    from components.carga_masiva_ui import render_carga_masiva
    CARGA_MASIVA_DISPONIBLE = True
except ImportError as e:
    CARGA_MASIVA_DISPONIBLE = False
    print(f"Warning: Carga Masiva not available: {e}")

# Componentes de Riesgo por Concentración
try:
    from components.concentration_risk_ui import render_concentracion_tab
    from services.concentration_risk_service import init_concentration_tables, get_resumen_concentracion
    CONCENTRACION_DISPONIBLE = True
except ImportError as e:
    CONCENTRACION_DISPONIBLE = False
    print(f"Warning: Concentration Risk not available: {e}")

# Componentes de Degradación MAGERIT
try:
    from components.degradacion_ui import render_degradacion_tab, render_resumen_degradacion_evaluacion
    DEGRADACION_DISPONIBLE = True
except ImportError as e:
    DEGRADACION_DISPONIBLE = False
    print(f"Warning: Degradación UI not available: {e}")

from config.settings import (
    CUESTIONARIOS_HEADERS, RESPUESTAS_HEADERS, IMPACTO_HEADERS,
    ANALISIS_RIESGO_HEADERS, RISK_COLORS, get_risk_level,
    N_PREGUNTAS_BASE, N_PREGUNTAS_IA, OLLAMA_DEFAULT_MODEL
)

# Autenticación
from components.login_ui import (
    init_auth, is_authenticated, render_login_page,
    render_sidebar_user, render_mi_perfil, render_gestion_usuarios,
    render_auth_logs, get_current_user as get_auth_user, logout
)
from config.auth_config import has_permission, get_role_info
from services.process_log_service import log_proceso, registrar_proceso_rapido, obtener_log_procesos, obtener_resumen_procesos, obtener_timeline_evaluacion

# ==================== FUNCIONES AUXILIARES ====================

def calcular_estado_activo(eval_id: str, activo_id: str) -> str:
    """
    Calcula el estado automático del activo basado en datos reales.
    NO se debe setear manualmente, siempre se calcula.
    
    Lógica:
    - Pendiente: Activo creado, sin cuestionario
    - Incompleto: Cuestionario iniciado pero no completo
    - Completo: Cuestionario completo, sin evaluación IA
    - Evaluado: Tiene resultados de IA
    """
    try:
        # 1. Verificar si existe cuestionario
        cuestionarios = read_sheet("CUESTIONARIOS")
        if cuestionarios.empty or "ID_Evaluacion" not in cuestionarios.columns:
            return "Pendiente"
        
        tiene_cuestionario = not cuestionarios[
            (cuestionarios["ID_Evaluacion"].astype(str) == str(eval_id)) &
            (cuestionarios["ID_Activo"].astype(str) == str(activo_id))
        ].empty
        
        if not tiene_cuestionario:
            return "Pendiente"
        
        # 2. Verificar respuestas
        respuestas = read_sheet("RESPUESTAS")
        if respuestas.empty or "ID_Evaluacion" not in respuestas.columns:
            return "Pendiente"
        
        respuestas_activo = respuestas[
            (respuestas["ID_Evaluacion"].astype(str) == str(eval_id)) &
            (respuestas["ID_Activo"].astype(str) == str(activo_id))
        ]
        
        if respuestas_activo.empty:
            return "Pendiente"
        
        # 3. Verificar si cuestionario está completo
        try:
            cuestionario_completo = verificar_cuestionario_completo(eval_id, activo_id)
            if not cuestionario_completo:
                return "Incompleto"
        except:
            return "Incompleto"
        
        # 4. Verificar si tiene evaluación IA
        analisis = read_sheet("ANALISIS_RIESGO")
        if not analisis.empty and "ID_Evaluacion" in analisis.columns:
            tiene_analisis = not analisis[
                (analisis["ID_Evaluacion"].astype(str) == str(eval_id)) &
                (analisis["ID_Activo"].astype(str) == str(activo_id))
            ].empty
            
            if tiene_analisis:
                return "Evaluado"
        
        return "Completo"
    
    except Exception as e:
        # En caso de error, retornar Pendiente por seguridad
        print(f"Error calculando estado: {str(e)}")
        return "Pendiente"


def actualizar_estados_automaticos(eval_id: str):
    """
    Recalcula estados de todos los activos de una evaluación.
    Se debe llamar después de cada operación crítica:
    - Crear/editar/eliminar respuestas
    - Ejecutar IA
    - Modificar cuestionario
    """
    try:
        activos = get_activos_por_evaluacion(eval_id)
        if activos.empty:
            return
        
        for _, activo in activos.iterrows():
            try:
                estado_nuevo = calcular_estado_activo(eval_id, activo["ID_Activo"])
                actualizar_estado_activo(eval_id, activo["ID_Activo"], estado_nuevo)
            except Exception as e:
                print(f"Error actualizando estado de {activo['ID_Activo']}: {str(e)}")
                continue
    except Exception as e:
        print(f"Error en actualizar_estados_automaticos: {str(e)}")


def validar_contexto_evaluacion() -> bool:
    """
    Valida que hay una evaluación seleccionada.
    Retorna True si hay evaluación, False si no.
    NO usa st.stop() para no afectar otros tabs.
    """
    if not st.session_state.get("eval_actual"):
        st.error("**EVALUACIÓN REQUERIDA**")
        st.warning(
            "No puedes gestionar activos, cuestionarios o evaluaciones sin "
            "seleccionar primero una **Evaluación**.\n\n"
            "Ve a la pestaña **Evaluaciones** y selecciona o crea una evaluación."
        )
        return False
    return True


# ==================== CONFIGURACIÓN INICIAL ====================

st.set_page_config(
    page_title="TITA - Evaluación de Riesgos MAGERIT",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ocultar navegación automática de Streamlit (pages/)
st.markdown("""
<style>
/* Ocultar navegación automática de páginas de Streamlit */
[data-testid="stSidebarNav"],
section[data-testid="stSidebar"] > div > div > div > div > ul,
[data-testid="stSidebarNavItems"],
nav[data-testid="stSidebarNav"] {
    display: none !important;
    height: 0 !important;
    overflow: hidden !important;
}
/* Ocultar header nativo de Streamlit */
[data-testid="stApp"] > header[data-testid="stHeader"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# CSS personalizado — Tema corporativo oscuro TITA
st.markdown("""
<style>
/* ═══════════════════════════════════════════════════════════════
   PROYECTO TITA — TEMA CORPORATIVO OSCURO (Teal + Dark Blue)
   Paleta: #0a1628 (fondo) · #0f2027 · #1a3a4a · #2ec4b6 (acento)
   ═══════════════════════════════════════════════════════════════ */

/* ────── FONDO PRINCIPAL ────── */
[data-testid="stApp"],
[data-testid="stApp"] > div {
    background: linear-gradient(160deg, #0a1628 0%, #0e1b30 40%, #0f2027 100%) !important;
    color: #d0d8e0 !important;
}

/* ────── SIDEBAR ────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #081222 0%, #0c1a2e 50%, #0a1628 100%) !important;
    border-right: 1px solid rgba(46, 196, 182, 0.15) !important;
}
[data-testid="stSidebar"] * {
    color: #c0ccd8 !important;
}
[data-testid="stSidebar"] .stMetric label {
    color: #7eb8c9 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
[data-testid="stSidebar"] [data-testid="stMetricValue"] {
    color: #2ec4b6 !important;
    font-weight: 700 !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(46, 196, 182, 0.15) !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: rgba(46, 196, 182, 0.12) !important;
    color: #2ec4b6 !important;
    border: 1px solid rgba(46, 196, 182, 0.3) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.25s ease !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(46, 196, 182, 0.25) !important;
    border-color: #2ec4b6 !important;
}

/* ────── TÍTULOS Y TEXTO ────── */
h1 {
    color: #e8eff8 !important;
    font-weight: 800 !important;
    letter-spacing: 0.5px !important;
}
h2, .stHeader h2, [data-testid="stHeader"] h2 {
    color: #c8dbe8 !important;
    font-weight: 700 !important;
    border-bottom: 2px solid rgba(46, 196, 182, 0.25);
    padding-bottom: 0.4rem;
}
h3 {
    color: #b0c8d8 !important;
    font-weight: 600 !important;
}
p, li, span, div {
    color: #c0ccd8;
}
a {
    color: #2ec4b6 !important;
}

/* ────── TABS ────── */
[data-testid="stTabs"] {
    background: transparent !important;
}
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: rgba(10, 22, 40, 0.7) !important;
    border-radius: 12px 12px 0 0 !important;
    padding: 0.3rem 0.5rem 0 0.5rem !important;
    gap: 3px !important;
    border-bottom: 2px solid rgba(46, 196, 182, 0.12) !important;
    overflow-x: auto !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: rgba(15, 32, 39, 0.5) !important;
    color: #7ea8b8 !important;
    border: 1px solid rgba(46, 196, 182, 0.08) !important;
    border-bottom: none !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 0.5rem 1rem !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    transition: all 0.25s ease !important;
    white-space: nowrap !important;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    background: rgba(46, 196, 182, 0.1) !important;
    color: #a0d8d0 !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: rgba(46, 196, 182, 0.15) !important;
    color: #2ec4b6 !important;
    border-color: rgba(46, 196, 182, 0.3) !important;
    font-weight: 700 !important;
    box-shadow: inset 0 -2px 0 #2ec4b6;
}

/* ────── BOTONES ────── */
.stButton > button[kind="primary"],
.stButton > button[data-testid="stFormSubmitButton"] {
    background: linear-gradient(135deg, #2ec4b6 0%, #1a9e94 100%) !important;
    color: #0a1628 !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 8px rgba(46, 196, 182, 0.2) !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #26a69a 0%, #158a80 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(46, 196, 182, 0.35) !important;
}
.stButton > button[kind="secondary"],
.stButton > button:not([kind="primary"]) {
    background: rgba(15, 32, 39, 0.6) !important;
    color: #b0cad8 !important;
    border: 1px solid rgba(46, 196, 182, 0.2) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.25s ease !important;
}
.stButton > button[kind="secondary"]:hover,
.stButton > button:not([kind="primary"]):hover {
    background: rgba(46, 196, 182, 0.12) !important;
    border-color: rgba(46, 196, 182, 0.4) !important;
    color: #2ec4b6 !important;
}

/* ────── FORMULARIOS ────── */
[data-testid="stForm"] {
    background: rgba(12, 26, 46, 0.5) !important;
    border: 1px solid rgba(46, 196, 182, 0.12) !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    backdrop-filter: blur(8px);
}

/* ────── INPUTS (Text, Select, TextArea) ────── */
.stTextInput input,
.stNumberInput input,
.stTextArea textarea {
    background: rgba(15, 25, 45, 0.8) !important;
    color: #d8e2ec !important;
    border: 1px solid rgba(46, 196, 182, 0.2) !important;
    border-radius: 8px !important;
    transition: border-color 0.25s ease !important;
}
.stTextInput input:focus,
.stNumberInput input:focus,
.stTextArea textarea:focus {
    border-color: #2ec4b6 !important;
    box-shadow: 0 0 0 2px rgba(46, 196, 182, 0.15) !important;
}
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #5a7080 !important;
}
.stTextInput label,
.stNumberInput label,
.stTextArea label,
.stSelectbox label,
.stRadio label,
.stSlider label,
.stMultiSelect label,
.stCheckbox label {
    color: #90b0c0 !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
}

/* Select boxes */
.stSelectbox [data-baseweb="select"] > div {
    background: rgba(15, 25, 45, 0.8) !important;
    border: 1px solid rgba(46, 196, 182, 0.2) !important;
    border-radius: 8px !important;
    color: #d8e2ec !important;
}
.stSelectbox [data-baseweb="select"] > div:hover {
    border-color: rgba(46, 196, 182, 0.4) !important;
}
/* Dropdown menu */
[data-baseweb="popover"] {
    background: #0f1d30 !important;
    border: 1px solid rgba(46, 196, 182, 0.2) !important;
    border-radius: 8px !important;
}
[data-baseweb="menu"] {
    background: #0f1d30 !important;
}
[data-baseweb="menu"] li {
    color: #c0ccd8 !important;
    background: transparent !important;
}
[data-baseweb="menu"] li:hover {
    background: rgba(46, 196, 182, 0.12) !important;
    color: #2ec4b6 !important;
}

/* ────── METRICS ────── */
[data-testid="stMetric"] {
    background: rgba(12, 26, 46, 0.55) !important;
    border: 1px solid rgba(46, 196, 182, 0.12) !important;
    border-radius: 10px !important;
    padding: 0.9rem 1rem !important;
    transition: border-color 0.3s ease, transform 0.2s ease !important;
}
[data-testid="stMetric"]:hover {
    border-color: rgba(46, 196, 182, 0.3) !important;
    transform: translateY(-1px) !important;
}
[data-testid="stMetric"] label {
    color: #7ea8b8 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.6px !important;
    font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
    color: #e0eff8 !important;
    font-weight: 800 !important;
    font-size: 1.6rem !important;
}
[data-testid="stMetricDelta"] svg {
    display: inline !important;
}

/* ────── DATAFRAMES / TABLAS ────── */
[data-testid="stDataFrame"],
.stDataFrame {
    border-radius: 10px !important;
    overflow: hidden !important;
    border: 1px solid rgba(46, 196, 182, 0.1) !important;
}
[data-testid="stDataFrame"] [data-testid="glideDataEditor"] {
    border-radius: 10px !important;
}

/* ────── EXPANDERS ────── */
[data-testid="stExpander"] {
    background: rgba(12, 26, 46, 0.4) !important;
    border: 1px solid rgba(46, 196, 182, 0.1) !important;
    border-radius: 10px !important;
    margin-bottom: 0.5rem !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    color: #b0cad8 !important;
    font-weight: 600 !important;
    padding: 0.7rem 1rem !important;
}
[data-testid="stExpander"] summary:hover {
    color: #2ec4b6 !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    border-top: 1px solid rgba(46, 196, 182, 0.08) !important;
    padding: 1rem !important;
}

/* ────── ALERTAS (Success, Warning, Error, Info) ────── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border-left-width: 4px !important;
    backdrop-filter: blur(4px) !important;
}
.stSuccess, div[data-testid="stAlert"][data-baseweb*="positive"],
div[role="alert"]:has(> div > svg[data-testid="stAlertSuccessIcon"]) {
    background: rgba(46, 196, 182, 0.08) !important;
    border-left-color: #2ec4b6 !important;
}
.stWarning, div[data-testid="stAlert"][data-baseweb*="warning"],
div[role="alert"]:has(> div > svg[data-testid="stAlertWarningIcon"]) {
    background: rgba(255, 183, 77, 0.08) !important;
    border-left-color: #ffb74d !important;
}
.stError, div[data-testid="stAlert"][data-baseweb*="negative"],
div[role="alert"]:has(> div > svg[data-testid="stAlertErrorIcon"]) {
    background: rgba(255, 82, 82, 0.08) !important;
    border-left-color: #ff5252 !important;
}
.stInfo, div[data-testid="stAlert"][data-baseweb*="informational"],
div[role="alert"]:has(> div > svg[data-testid="stAlertInfoIcon"]) {
    background: rgba(66, 165, 245, 0.1) !important;
    border-left-color: #42a5f5 !important;
}

/* ────── PROGRESS BAR ────── */
[data-testid="stProgress"] > div > div {
    background: rgba(46, 196, 182, 0.12) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}
[data-testid="stProgress"] > div > div > div {
    background: linear-gradient(90deg, #1a9e94, #2ec4b6, #40d8c8) !important;
    border-radius: 8px !important;
}
[data-testid="stProgress"] p {
    color: #90b0c0 !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
}

/* ────── DIVIDERS ────── */
hr {
    border-color: rgba(46, 196, 182, 0.1) !important;
    margin: 1rem 0 !important;
}

/* ────── CAPTION / SMALL TEXT ────── */
.stCaption, [data-testid="stCaptionContainer"] {
    color: #5a7888 !important;
    font-size: 0.8rem !important;
}

/* ────── RADIO / CHECKBOX ────── */
.stRadio > div {
    gap: 0.6rem !important;
}
.stRadio [data-testid="stMarkdownContainer"] p,
.stCheckbox [data-testid="stMarkdownContainer"] p {
    color: #b0c8d8 !important;
}

/* ────── SLIDER ────── */
.stSlider [data-baseweb="slider"] [role="slider"] {
    background: #2ec4b6 !important;
}
.stSlider [data-baseweb="slider"] > div > div {
    background: rgba(46, 196, 182, 0.25) !important;
}

/* ────── SPINNER (ocultar Lottie, usar CSS puro) ────── */
[data-testid="stStatusWidget"] svg,
[data-testid="stStatusWidget"] img,
[data-testid="stStatusWidget"] canvas,
[data-testid="stStatusWidget"] lottie-player,
[data-testid="stStatusWidget"] > div > div,
div[data-testid="stSpinner"] > div > div > svg,
div.stSpinner svg,
.element-container svg[class*="running"],
div[class*="StatusWidget"] svg {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    width: 0 !important;
    height: 0 !important;
}
div[data-testid="stSpinner"] > div {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}
div[data-testid="stSpinner"] > div::before {
    content: "" !important;
    display: block !important;
    width: 22px !important;
    height: 22px !important;
    border: 3px solid rgba(46, 196, 182, 0.2) !important;
    border-top-color: #2ec4b6 !important;
    border-radius: 50% !important;
    animation: tita-spin 0.7s linear infinite !important;
}
@keyframes tita-spin {
    to { transform: rotate(360deg); }
}
[data-testid="stStatusWidget"] {
    display: none !important;
}

/* ────── MARKDOWN TABLES ────── */
table {
    border-collapse: separate !important;
    border-spacing: 0 !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    border: 1px solid rgba(46, 196, 182, 0.12) !important;
    width: 100% !important;
}
th {
    background: rgba(46, 196, 182, 0.12) !important;
    color: #a0d0c8 !important;
    font-weight: 700 !important;
    padding: 0.6rem 1rem !important;
    border-bottom: 1px solid rgba(46, 196, 182, 0.15) !important;
    font-size: 0.85rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.4px !important;
}
td {
    padding: 0.55rem 1rem !important;
    border-bottom: 1px solid rgba(46, 196, 182, 0.06) !important;
    color: #c0ccd8 !important;
    font-size: 0.88rem !important;
}
tr:hover td {
    background: rgba(46, 196, 182, 0.04) !important;
}

/* ────── CODE BLOCKS ────── */
code {
    background: rgba(46, 196, 182, 0.1) !important;
    color: #2ec4b6 !important;
    padding: 0.15rem 0.45rem !important;
    border-radius: 5px !important;
    font-size: 0.85rem !important;
}

/* ────── FILE UPLOADER ────── */
[data-testid="stFileUploader"] {
    border: 2px dashed rgba(46, 196, 182, 0.2) !important;
    border-radius: 12px !important;
    background: rgba(12, 26, 46, 0.3) !important;
    transition: border-color 0.3s ease !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(46, 196, 182, 0.4) !important;
}
[data-testid="stFileUploader"] section {
    color: #90b0c0 !important;
}

/* ────── MULTISELECT / CHIPS ────── */
.stMultiSelect [data-baseweb="tag"] {
    background: rgba(46, 196, 182, 0.15) !important;
    color: #2ec4b6 !important;
    border-radius: 6px !important;
}

/* ────── PLOTLY / CHARTS ────── */
.js-plotly-plot .plotly .main-svg {
    background: transparent !important;
}

/* ────── SCROLLBAR ────── */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: rgba(10, 22, 40, 0.4);
}
::-webkit-scrollbar-thumb {
    background: rgba(46, 196, 182, 0.25);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(46, 196, 182, 0.4);
}

/* ────── TOAST / NOTIFICATIONS ────── */
[data-testid="stToast"] {
    background: #0f1d30 !important;
    border: 1px solid rgba(46, 196, 182, 0.2) !important;
    border-radius: 10px !important;
    color: #c0ccd8 !important;
}
/* ────── REUBICACIÓN DEL SIDEBAR A LA DERECHA ────── */
@media (min-width: 769px) {
    [data-testid="stAppViewContainer"] {
        flex-direction: row !important;
    }
    [data-testid="stSidebar"] {
        border-right: none !important;
        border-left: 1px solid rgba(46, 196, 182, 0.15) !important;
    }
}

/* ────── ACCESIBILIDAD Y FOCOS (a11y) ────── */
a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible, [tabindex="0"]:focus-visible {
    outline: 2px solid #2ec4b6 !important;
    outline-offset: 2px !important;
}

/* ────── DISEÑO RESPONSIVO (MEDIA QUERIES) ────── */
@media (max-width: 768px) {
    h1 {
        font-size: 1.8rem !important;
        letter-spacing: 1px !important;
    }
    h2, .stHeader h2, [data-testid="stHeader"] h2 {
        font-size: 1.3rem !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
    }
    [data-testid="stForm"] {
        padding: 1rem !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        padding: 0.5rem 0.6rem !important;
        font-size: 0.75rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# Desactivar autocomplete del navegador en todos los inputs
st.markdown("""
<script>
const _disableAC = () => {
    document.querySelectorAll('input, textarea').forEach(el => {
        el.setAttribute('autocomplete', 'off');
        el.setAttribute('autocorrect', 'off');
        el.setAttribute('autocapitalize', 'off');
        el.setAttribute('spellcheck', 'false');
    });
};
_disableAC();
const _obs = new MutationObserver(_disableAC);
_obs.observe(document.body, {childList: true, subtree: true});
</script>
""", unsafe_allow_html=True)

# Inicializar session_state
if "eval_actual" not in st.session_state:
    st.session_state["eval_actual"] = None
if "eval_nombre" not in st.session_state:
    st.session_state["eval_nombre"] = None

# ==================== AUTENTICACIÓN ====================
init_auth()

if not is_authenticated():
    render_login_page()
    st.stop()

# Usuario autenticado — obtener datos
_current_user = get_auth_user()
_user_role = _current_user["role"] if _current_user else "viewer"

# Asegurar hojas necesarias
ensure_sheet_exists("CUESTIONARIOS", CUESTIONARIOS_HEADERS)
ensure_sheet_exists("RESPUESTAS", RESPUESTAS_HEADERS)
ensure_sheet_exists("IMPACTO_ACTIVOS", IMPACTO_HEADERS)
ensure_sheet_exists("ANALISIS_RIESGO", ANALISIS_RIESGO_HEADERS)

# ==================== TÍTULO Y SIDEBAR ====================

st.markdown("""
<div style="text-align:center; padding: 1rem 0 0.5rem 0;">
    <h1 style="font-size:2.2rem; letter-spacing:3px; color:#e0eff8; margin-bottom:0.2rem;">
        PROYECTO TITA
    </h1>
    <p style="color:#7eb8c9; font-size:0.92rem; letter-spacing:1px; margin:0;">
        Metodología MAGERIT v3 · ISO/IEC 27002:2022 · IA con Ollama
    </p>
</div>
""", unsafe_allow_html=True)

# ==================== NAVEGACIÓN POR SIDEBAR ====================

# Opciones de menú base
_menu_options = [
    "Nueva Evaluación",
    "Evaluaciones",
    "Activos",
    "Cuestionarios",
    "IA Evaluación",
    "Degradación",
    "Vulnerabilidades",
    "Tratamiento",
    "Dashboard",
    "Madurez",
    "Matriz MAGERIT",
    "Comparativas",
    "Auditoría",
    "Validación IA",
]

# Opciones admin
if _user_role == "admin":
    _menu_options.append("Editor Cuestionarios")
    _menu_options.append("Usuarios")
    _menu_options.append("Logs Auth")

# ==================== SIDEBAR CON OPTION MENU ====================
_user_initial = _current_user['full_name'][0].upper() if _current_user and _current_user.get('full_name') else '?'
_user_display = _current_user['full_name'] if _current_user else 'Usuario'
_role_info_topbar = get_role_info(_user_role) if _current_user else {'label': '', 'icon': ''}

# Íconos para cada opción del menú (bootstrap-icons)
_menu_icons = [
    "plus-circle",        # Nueva Evaluación
    "folder2-open",       # Evaluaciones
    "hdd-stack",          # Activos
    "clipboard-check",    # Cuestionarios
    "robot",              # IA Evaluación
    "graph-down-arrow",   # Degradación
    "shield-exclamation", # Vulnerabilidades
    "bandaid",            # Tratamiento
    "speedometer2",       # Dashboard
    "award",              # Madurez
    "grid-3x3",           # Matriz MAGERIT
    "arrows-angle-contract",  # Comparativas
    "journal-check",      # Auditoría
    "check2-circle",      # Validación IA
]

# Opciones admin con íconos
if _user_role == "admin":
    _menu_icons.extend(["pencil-square", "people", "file-earmark-text"])

# Agregar separador y opciones de usuario al final
_menu_options.append("Mi Perfil")
_menu_options.append("Cerrar Sesión")
_menu_icons.extend(["person-circle", "box-arrow-right"])

with st.sidebar:
    # Badge de usuario
    st.markdown(f"""
    <div style="
        padding: 12px 16px;
        background: linear-gradient(135deg, #1a3a4a 0%, #0f2027 100%);
        border: 1px solid rgba(46, 196, 182, 0.3);
        border-radius: 10px;
        margin-bottom: 12px;
    ">
        <p style="margin: 0; font-size: 15px; color: #e0e8f0; font-weight: 600;">
            {_role_info_topbar['icon']} {_user_display}
        </p>
        <p style="margin: 2px 0 0 0; font-size: 12px; color: #2ec4b6;">
            {_role_info_topbar['label']} &middot; @{_current_user['username'] if _current_user else ''}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Selector de Evaluacion (siempre visible en sidebar) ──
    _sidebar_evals = get_evaluaciones()

    if not _sidebar_evals.empty:
        _eval_ids = _sidebar_evals["ID_Evaluacion"].tolist()
        _eval_actual = st.session_state.get("eval_actual")

        # Determinar indice actual en la lista
        _default_idx = 0
        if _eval_actual and _eval_actual in _eval_ids:
            _default_idx = _eval_ids.index(_eval_actual)

        _sidebar_eval_selec = st.selectbox(
            "Evaluacion activa",
            _eval_ids,
            index=_default_idx,
            key="sidebar_eval_selector",
            format_func=lambda x: f"{x} - {_sidebar_evals[_sidebar_evals['ID_Evaluacion']==x].iloc[0]['Nombre']}"
        )

        _sidebar_eval_data = _sidebar_evals[_sidebar_evals["ID_Evaluacion"] == _sidebar_eval_selec].iloc[0]
        _sidebar_eval_name = _sidebar_eval_data["Nombre"]

        # Boton activar (solo si es diferente a la actual)
        if _sidebar_eval_selec != _eval_actual:
            if st.button("Activar evaluacion", key="sidebar_btn_activar", type="primary", use_container_width=True):
                st.session_state["eval_actual"] = _sidebar_eval_selec
                st.session_state["eval_nombre"] = _sidebar_eval_name
                st.rerun()
        else:
            st.markdown(f"""
            <div style="
                background: rgba(46,196,182,0.08);
                border: 1px solid rgba(46,196,182,0.2);
                border-radius: 8px;
                padding: 6px 12px;
                margin-bottom: 4px;
                text-align: center;
            ">
                <span style="color:#2ec4b6; font-size:0.75rem; font-weight:600;">Evaluacion activa</span>
            </div>
            """, unsafe_allow_html=True)

        # Widget de estadisticas de la evaluacion activa
        if st.session_state.get("eval_actual"):
            _sidebar_stats = get_estadisticas_evaluacion(st.session_state["eval_actual"])
            st.markdown(f"""
            <div style="
                background: rgba(46,196,182,0.06);
                border: 1px solid rgba(46,196,182,0.15);
                border-radius: 10px;
                padding: 10px 14px;
                margin-bottom: 12px;
            ">
                <div style="color:#7eb8c9; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.8px; margin-bottom:6px;">
                    ESTADISTICAS
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px;">
                    <div style="background:rgba(10,22,40,0.5); border-radius:8px; padding:6px 10px; text-align:center;">
                        <div style="color:#7eb8c9; font-size:0.62rem; text-transform:uppercase; letter-spacing:0.5px;">Activos</div>
                        <div style="color:#e0eff8; font-weight:800; font-size:1.1rem;">{_sidebar_stats['total_activos']}</div>
                    </div>
                    <div style="background:rgba(10,22,40,0.5); border-radius:8px; padding:6px 10px; text-align:center;">
                        <div style="color:#7eb8c9; font-size:0.62rem; text-transform:uppercase; letter-spacing:0.5px;">Progreso</div>
                        <div style="color:#2ec4b6; font-weight:800; font-size:1.1rem;">{_sidebar_stats['progreso']}%</div>
                    </div>
                    <div style="background:rgba(10,22,40,0.5); border-radius:8px; padding:6px 10px; text-align:center;">
                        <div style="color:#7eb8c9; font-size:0.62rem; text-transform:uppercase; letter-spacing:0.5px;">Evaluados</div>
                        <div style="color:#66bb6a; font-weight:800; font-size:1.1rem;">{_sidebar_stats['evaluados']}</div>
                    </div>
                    <div style="background:rgba(10,22,40,0.5); border-radius:8px; padding:6px 10px; text-align:center;">
                        <div style="color:#7eb8c9; font-size:0.62rem; text-transform:uppercase; letter-spacing:0.5px;">Pendientes</div>
                        <div style="color:#ffb74d; font-weight:800; font-size:1.1rem;">{_sidebar_stats['pendientes']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="
            background: rgba(255,183,77,0.06);
            border: 1px solid rgba(255,183,77,0.15);
            border-radius: 10px;
            padding: 10px 14px;
            margin-bottom: 12px;
            text-align: center;
        ">
            <div style="color:#ffb74d; font-size:0.75rem; font-weight:600;">Sin evaluaciones</div>
            <div style="color:#5a8898; font-size:0.68rem; margin-top:2px;">Crea una en Nueva Evaluacion</div>
        </div>
        """, unsafe_allow_html=True)

    pagina = option_menu(
        menu_title=None,
        options=_menu_options,
        icons=_menu_icons,
        default_index=0,
        key="nav_pagina",
        styles={
            "container": {
                "padding": "0 !important",
                "background-color": "transparent",
            },
            "icon": {
                "color": "#2ec4b6",
                "font-size": "16px",
            },
            "nav-link": {
                "font-size": "14px",
                "text-align": "left",
                "margin": "2px 0",
                "padding": "8px 12px",
                "color": "#c0ccd8",
                "border-radius": "8px",
                "--hover-color": "rgba(46, 196, 182, 0.1)",
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, rgba(46,196,182,0.15) 0%, rgba(46,196,182,0.08) 100%)",
                "color": "#2ec4b6",
                "font-weight": "700",
                "border-left": "3px solid #2ec4b6",
            },
            "separator": {
                "border-color": "rgba(46, 196, 182, 0.15)",
                "margin": "8px 0",
            },
        },
    )

    st.divider()
    st.markdown("""
    <div style="color:#4a6878; font-size:0.72rem; text-align:center; padding:0.3rem 0;">
        SQLite: tita_database.db · Estados automáticos
    </div>
    """, unsafe_allow_html=True)

# Manejar Cerrar Sesión
if pagina == "Cerrar Sesión":
    logout()
    st.rerun()


def _styled_header(icon: str, title: str, subtitle: str = ""):
    """Genera un header estilizado para cada sección/tab."""
    sub_html = f'<p style="color:#5a8898; font-size:0.82rem; margin:0;">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(46,196,182,0.08) 0%, rgba(12,26,46,0.4) 100%);
                border: 1px solid rgba(46,196,182,0.12); border-radius:12px;
                padding:1.2rem 1.5rem; margin-bottom:1rem;">
        <h2 style="color:#e0eff8; font-weight:700; margin:0 0 0.2rem 0; font-size:1.4rem; border:none; padding:0;">
            {icon} {title}
        </h2>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def _eval_badge():
    """Muestra badge estilizado de la evaluación activa."""
    if st.session_state.get("eval_actual"):
        st.markdown(f"""
        <div style="background:rgba(46,196,182,0.06); border-left:3px solid #2ec4b6;
                    border-radius:0 8px 8px 0; padding:0.6rem 1rem; margin-bottom:1rem;
                    display:flex; align-items:center; gap:0.8rem;">
            <span style="font-size:1.3rem;"></span>
            <div>
                <span style="color:#7eb8c9; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.8px;">Evaluación activa</span><br>
                <span style="color:#e0eff8; font-weight:700; font-size:0.95rem;">{st.session_state['eval_nombre']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==================== PÁGINA: NUEVA EVALUACIÓN (WIZARD) ====================
if pagina == "Nueva Evaluación":
    from pages.wizard_evaluacion import render_wizard
    render_wizard(_styled_header)


# ==================== PÁGINA: EVALUACIONES ====================
if pagina == "Evaluaciones":
    from pages.evaluaciones import render_evaluaciones
    render_evaluaciones(_styled_header)


# ==================== PÁGINA: ACTIVOS ====================
if pagina == "Activos":
    from pages.activos import render_activos
    render_activos(_styled_header, calcular_estado_activo, actualizar_estados_automaticos)


# ==================== PÁGINA: CUESTIONARIOS ====================
if pagina == "Cuestionarios":
    from pages.cuestionarios import render_cuestionarios
    render_cuestionarios(_styled_header, actualizar_estados_automaticos)


# ==================== PÁGINA: IA EVALUACIÓN ====================
if pagina == "IA Evaluación":
    from pages.ia_evaluacion import render_ia_evaluacion
    render_ia_evaluacion(_styled_header)

# ==================== TAB DEGRADACIÓN: GESTIÓN DE DEGRADACIÓN MAGERIT ====================
if pagina == "Degradación":
    if not st.session_state.get("eval_actual"):
        st.error("⚠️ EVALUACIÓN REQUERIDA")
        st.warning("Ve a la pestaña **Evaluaciones** y selecciona una evaluación primero.")
    else:
        if DEGRADACION_DISPONIBLE:
            render_degradacion_tab(st.session_state["eval_actual"])
        else:
            st.error("❌ Componente de Degradación no disponible")
            st.info("Verifica que el archivo `components/degradacion_ui.py` existe y no tiene errores de sintaxis.")


# ==================== TAB VULNERABILIDADES: GESTIÓN DE VULNERABILIDADES ====================
if pagina == "Vulnerabilidades":
    if not st.session_state.get("eval_actual"):
        st.error("⚠️ EVALUACIÓN REQUERIDA")
        st.warning("Ve a la pestaña **Evaluaciones** y selecciona una evaluación primero.")
    else:
        try:
            from components.vulnerabilidades_ui import render_vulnerabilidades_tab
            render_vulnerabilidades_tab(st.session_state["eval_actual"])
        except Exception as e:
            st.error(f"❌ Error cargando módulo de vulnerabilidades: {e}")


# ==================== TAB TRATAMIENTO: TRATAMIENTO DE RIESGOS ====================
if pagina == "Tratamiento":
    if not st.session_state.get("eval_actual"):
        st.error("⚠️ EVALUACIÓN REQUERIDA")
        st.warning("Ve a la pestaña **Evaluaciones** y selecciona una evaluación primero.")
    else:
        try:
            from components.tratamiento_ui import render_tratamiento_tab
            render_tratamiento_tab(st.session_state["eval_actual"])
        except Exception as e:
            st.error(f"❌ Error cargando módulo de tratamiento: {e}")


# ==================== PÁGINA: DASHBOARD ====================
if pagina == "Dashboard":
    from pages.dashboard import render_dashboard
    render_dashboard(_styled_header)


# ==================== PÁGINA: MADUREZ ====================
if pagina == "Madurez":
    from pages.madurez import render_madurez
    render_madurez(_styled_header)


# ==================== TAB MATRIZ MAGERIT: VISTA CONSOLIDADA ====================
if pagina == "Matriz MAGERIT":
    _styled_header("", "Matriz MAGERIT - Vista Técnica", "Vista técnica consolidada de la evaluación de riesgos")

    if not st.session_state.get("eval_actual"):
        st.error("**EVALUACIÓN REQUERIDA**")
        st.warning("Ve a la sección **Evaluaciones** y selecciona una evaluación primero.")
    else:
        st.success(f"Evaluación: **{st.session_state['eval_nombre']}**")

        # Obtener todos los resultados MAGERIT
        resumen_magerit = get_resumen_evaluacion(st.session_state["eval_actual"])

        if resumen_magerit.empty:
            st.info("No hay evaluaciones completadas. Ve a IA Evaluación para evaluar activos.")
        else:
            # ========== MATRIZ 5x5 VISUAL ==========
            if DASHBOARD_DISPONIBLE:
                st.markdown("### Matriz 5x5 - Probabilidad x Impacto")
                st.markdown("""
                Esta matriz visual muestra la posicion de cada activo segun su nivel de riesgo.
                Los colores siguen la escala oficial MAGERIT v3.
                """)
                render_matriz_5x5_activos(resumen_magerit, key_suffix="tab_matriz")
                st.divider()

            st.markdown("""
            **Matriz MAGERIT v3** - Cada fila representa una relacion **ACTIVO - AMENAZA** con todos los
            valores calculados por el sistema. Esta matriz sirve como evidencia tecnica y respaldo metodologico.
            """)

            # ========== FUNCIÓN AUXILIAR PARA EXTRAER CONTROLES ==========
            def extraer_controles_str(controles_list):
                """Extrae códigos de controles de lista de dicts o strings"""
                if not controles_list:
                    return ""
                resultado = []
                for ctrl in controles_list[:3]:
                    if isinstance(ctrl, dict):
                        codigo = ctrl.get("codigo", ctrl.get("control", ctrl.get("nombre", "")))
                        if codigo:
                            resultado.append(str(codigo))
                    elif isinstance(ctrl, str):
                        resultado.append(ctrl)
                return ", ".join(resultado)

            # ========== CONSTRUIR MATRIZ MAGERIT COMPLETA ==========
            matriz_rows = []
            for _, row in resumen_magerit.iterrows():
                resultado = get_resultado_magerit(st.session_state["eval_actual"], row["id_activo"])
                if resultado and resultado.get("amenazas"):
                    for amenaza in resultado["amenazas"]:
                        ctrl_existentes = amenaza.get("controles_existentes", [])
                        ctrl_recomendados = amenaza.get("controles_recomendados", [])

                        matriz_row = {
                            "Evaluación": st.session_state['eval_nombre'],
                            "ID Activo": row["id_activo"],
                            "Activo": row.get("nombre_activo", resultado.get("nombre_activo", "")),
                            "Tipo Activo": row.get("tipo_activo", "N/A"),
                            "Código Amenaza": amenaza.get("codigo", ""),
                            "Amenaza": amenaza.get("amenaza", ""),
                            "Tipo Amenaza": amenaza.get("tipo_amenaza", ""),
                            "Dimensión": amenaza.get("dimension", ""),
                            "D": resultado.get("impacto_d", row.get("impacto_d", 0)),
                            "I": resultado.get("impacto_i", row.get("impacto_i", 0)),
                            "C": resultado.get("impacto_c", row.get("impacto_c", 0)),
                            "Impacto": amenaza.get("impacto", 0),
                            "Probabilidad": amenaza.get("probabilidad", 0),
                            "Riesgo Inherente": amenaza.get("riesgo_inherente", 0),
                            "Riesgo Residual": amenaza.get("riesgo_residual", 0),
                            "Nivel Riesgo": amenaza.get("nivel_riesgo", ""),
                            "Tratamiento": amenaza.get("tratamiento", ""),
                            "Controles Existentes": extraer_controles_str(ctrl_existentes) if isinstance(ctrl_existentes, list) else str(ctrl_existentes),
                            "Salvaguardas (Recomendadas)": extraer_controles_str(ctrl_recomendados),
                            "Efectividad Controles": f"{amenaza.get('efectividad_controles', 0) * 100:.0f}%" if amenaza.get('efectividad_controles') else "0%",
                            "Justificación": amenaza.get("justificacion", "")[:100] if amenaza.get("justificacion") else ""
                        }
                        matriz_rows.append(matriz_row)
                elif resultado:
                    matriz_row = {
                        "Evaluación": st.session_state['eval_nombre'],
                        "ID Activo": row["id_activo"],
                        "Activo": row.get("nombre_activo", resultado.get("nombre_activo", "")),
                        "Tipo Activo": row.get("tipo_activo", "N/A"),
                        "Código Amenaza": "-",
                        "Amenaza": "Sin amenazas identificadas",
                        "Tipo Amenaza": "-",
                        "Dimensión": "-",
                        "D": resultado.get("impacto_d", 0),
                        "I": resultado.get("impacto_i", 0),
                        "C": resultado.get("impacto_c", 0),
                        "Impacto": round((resultado.get("impacto_d", 0) + resultado.get("impacto_i", 0) + resultado.get("impacto_c", 0)) / 3, 1),
                        "Probabilidad": 0,
                        "Riesgo Inherente": resultado.get("riesgo_inherente", 0),
                        "Riesgo Residual": resultado.get("riesgo_residual", 0),
                        "Nivel Riesgo": resultado.get("nivel_riesgo", "N/A"),
                        "Tratamiento": "-",
                        "Controles Existentes": "",
                        "Salvaguardas (Recomendadas)": "",
                        "Efectividad Controles": "0%",
                        "Justificación": ""
                    }
                    matriz_rows.append(matriz_row)

            if matriz_rows:
                matriz_df = pd.DataFrame(matriz_rows)

                # ========== FILTROS ==========
                st.markdown("### Filtros")
                col1, col2, col3 = st.columns(3)

                with col1:
                    activos_unicos = ["Todos"] + matriz_df["Activo"].unique().tolist()
                    filtro_activo = st.selectbox("Filtrar por Activo:", activos_unicos, key="magerit_filtro_activo")

                with col2:
                    niveles_riesgo = ["Todos", "CRÍTICO", "ALTO", "MEDIO", "BAJO", "MUY BAJO"]
                    filtro_nivel = st.selectbox("Filtrar por Nivel de Riesgo:", niveles_riesgo, key="magerit_filtro_nivel")

                with col3:
                    ordenar_por = st.selectbox(
                        "Ordenar por:",
                        ["Riesgo Inherente (Mayor)", "Riesgo Inherente (Menor)", "Riesgo Residual (Mayor)", "Riesgo Residual (Menor)", "Activo"],
                        key="magerit_ordenar"
                    )

                # Aplicar filtros
                df_filtrado = matriz_df.copy()

                if filtro_activo != "Todos":
                    df_filtrado = df_filtrado[df_filtrado["Activo"] == filtro_activo]

                if filtro_nivel != "Todos":
                    df_filtrado = df_filtrado[df_filtrado["Nivel Riesgo"].str.upper() == filtro_nivel]

                # Ordenar
                if ordenar_por == "Riesgo Inherente (Mayor)":
                    df_filtrado = df_filtrado.sort_values("Riesgo Inherente", ascending=False)
                elif ordenar_por == "Riesgo Inherente (Menor)":
                    df_filtrado = df_filtrado.sort_values("Riesgo Inherente", ascending=True)
                elif ordenar_por == "Riesgo Residual (Mayor)":
                    df_filtrado = df_filtrado.sort_values("Riesgo Residual", ascending=False)
                elif ordenar_por == "Riesgo Residual (Menor)":
                    df_filtrado = df_filtrado.sort_values("Riesgo Residual", ascending=True)
                elif ordenar_por == "Activo":
                    df_filtrado = df_filtrado.sort_values("Activo")

                # ========== MÉTRICAS RESUMEN ==========
                st.markdown("### Resumen de la Matriz")
                col1, col2, col3, col4, col5 = st.columns(5)

                col1.metric("Total Registros", len(df_filtrado))
                col2.metric("Activos Únicos", df_filtrado["ID Activo"].nunique())
                col3.metric("Amenazas Únicas", len(df_filtrado[df_filtrado["Código Amenaza"] != "-"]))

                criticos = (df_filtrado["Nivel Riesgo"].str.upper().isin(["CRÍTICO", "CRITICO"])).sum()
                altos = (df_filtrado["Nivel Riesgo"].str.upper() == "ALTO").sum()
                col4.metric("Críticos", criticos)
                col5.metric("Altos", altos)

                st.divider()

                # ========== MATRIZ MAGERIT PRINCIPAL ==========
                st.markdown("### Matriz MAGERIT v3 - Relación Activo-Amenaza")

                st.dataframe(
                    df_filtrado,
                    use_container_width=True,
                    hide_index=True,
                    height=500
                )

                st.divider()

                # ========== EXPORTAR ==========
                st.markdown("### Exportar Matriz")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("Generar Excel Completo", key="magerit_exportar_excel"):
                        import io

                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df_filtrado.to_excel(writer, sheet_name='Matriz_MAGERIT', index=False)

                            resumen_activos = df_filtrado.groupby(["ID Activo", "Activo"]).agg({
                                "Riesgo Inherente": "max",
                                "Riesgo Residual": "max",
                                "D": "first",
                                "I": "first",
                                "C": "first"
                            }).reset_index()
                            resumen_activos.to_excel(writer, sheet_name='Resumen_Activos', index=False)

                            if len(df_filtrado[df_filtrado["Código Amenaza"] != "-"]) > 0:
                                amenazas_group = df_filtrado[df_filtrado["Código Amenaza"] != "-"].groupby(
                                    ["Código Amenaza", "Amenaza", "Tipo Amenaza"]
                                ).size().reset_index(name="Frecuencia")
                                amenazas_group = amenazas_group.sort_values("Frecuencia", ascending=False)
                                amenazas_group.to_excel(writer, sheet_name='Amenazas_Frecuencia', index=False)

                        st.download_button(
                            "Descargar Matriz MAGERIT (.xlsx)",
                            data=buffer.getvalue(),
                            file_name=f"Matriz_MAGERIT_{st.session_state['eval_actual']}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_magerit_excel"
                        )

                with col2:
                    csv_data = df_filtrado.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Descargar CSV",
                        data=csv_data,
                        file_name=f"Matriz_MAGERIT_{st.session_state['eval_actual']}.csv",
                        mime="text/csv",
                        key="download_magerit_csv"
                    )

                with st.expander("Información Metodológica MAGERIT v3"):
                    st.markdown("""
                    **Esta matriz sigue la metodología MAGERIT v3 del CCN-CERT (Ministerio de Hacienda, España)**

                    ### Columnas de la Matriz

                    | Columna | Descripción |
                    |---------|-------------|
                    | **D, I, C** | Impacto en Disponibilidad, Integridad y Confidencialidad (escala 1-5) |
                    | **Impacto** | Valor de impacto de la amenaza sobre el activo |
                    | **Probabilidad** | Frecuencia estimada de materialización (1-5) |
                    | **Riesgo Inherente** | Probabilidad x Impacto (sin considerar controles) |
                    | **Riesgo Residual** | Riesgo después de aplicar salvaguardas existentes |
                    | **Nivel Riesgo** | Clasificación: CRÍTICO, ALTO, MEDIO, BAJO, MUY BAJO |
                    | **Controles Existentes** | Salvaguardas ISO 27002 ya implementadas |
                    | **Salvaguardas** | Controles recomendados para mitigar el riesgo |
                    | **Efectividad** | Porcentaje de efectividad de controles actuales |

                    ### Niveles de Riesgo y Tratamiento

                    | Nivel | Rango | Tratamiento Sugerido |
                    |-------|-------|---------------------|
                    | **CRÍTICO** | >=20 | Acción inmediata, escalamiento a dirección |
                    | **ALTO** | 15-19 | Plan de tratamiento prioritario (<30 días) |
                    | **MEDIO** | 10-14 | Seguimiento y controles adicionales |
                    | **BAJO** | 5-9 | Aceptable con controles básicos |
                    | **MUY BAJO** | <5 | Riesgo aceptable, monitoreo rutinario |
                    """)
            else:
                st.warning("No se pudieron generar datos para la matriz. Verifique que los activos tengan evaluación MAGERIT completada.")

# ==================== PÁGINA: COMPARATIVAS ====================
if pagina == "Comparativas":
    from components.comparativa_ui import render_comparativa_tab
    _styled_header("", "Comparativas", "Compara evaluaciones para detectar cambios y tendencias")
    render_comparativa_tab()


# ==================== PÁGINA: AUDITORÍA ====================
if pagina == "Auditoría":
    try:
        from components.auditoria_ui import render_auditoria_tab
        render_auditoria_tab()
    except Exception as e:
        st.error(f"Error cargando módulo de auditoría: {e}")


# ==================== PÁGINA: VALIDACIÓN IA ====================
if pagina == "Validación IA":
    from pages.validacion_ia import render_validacion_ia
    render_validacion_ia(_styled_header)

# ==================== PÁGINA: MI PERFIL ====================
if pagina == "Mi Perfil":
    render_mi_perfil()


# ==================== PÁGINA: EDITOR CUESTIONARIOS (Admin) ====================
if pagina == "Editor Cuestionarios":
    from components.cuestionario_editor_ui import render_editor_cuestionarios
    render_editor_cuestionarios()


# ==================== PÁGINA: GESTIÓN USUARIOS (Admin) ====================
if pagina == "Usuarios":
    render_gestion_usuarios()


# ==================== PÁGINA: LOGS AUTH (Admin) ====================
if pagina == "Logs Auth":
    render_auth_logs()


# Footer
st.divider()
st.caption("🛡️ RiskMaster AI v3.0 - Motor MAGERIT v3 + ISO 27002:2022 | 52 Amenazas | 93 Controles | Madurez CMMI")
