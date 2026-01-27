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

# Componentes de IA Avanzada
try:
    from components.ia_advanced_ui import render_ia_avanzada_ui
    from services.ia_advanced_service import obtener_amenazas_evaluacion
    IA_AVANZADA_DISPONIBLE = True
except ImportError as e:
    IA_AVANZADA_DISPONIBLE = False
    print(f"Warning: IA Avanzada not available: {e}")

from config.settings import (
    CUESTIONARIOS_HEADERS, RESPUESTAS_HEADERS, IMPACTO_HEADERS,
    ANALISIS_RIESGO_HEADERS, RISK_COLORS, get_risk_level,
    N_PREGUNTAS_BASE, N_PREGUNTAS_IA, OLLAMA_DEFAULT_MODEL
)

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
        st.error("🚫 **EVALUACIÓN REQUERIDA**")
        st.warning(
            "No puedes gestionar activos, cuestionarios o evaluaciones sin "
            "seleccionar primero una **Evaluación**.\n\n"
            "👉 Ve a la pestaña **🏠 Evaluaciones** y selecciona o crea una evaluación."
        )
        return False
    return True


# ==================== CONFIGURACIÓN INICIAL ====================

st.set_page_config(
    page_title="TITA - Evaluación de Riesgos MAGERIT",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para ocultar spinner de personas
st.markdown("""
<style>
/* OCULTAR COMPLETAMENTE la animacion de personas Lottie */
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

/* Spinner simple centrado */
div[data-testid="stSpinner"] > div {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}

div[data-testid="stSpinner"] > div::before {
    content: "" !important;
    display: block !important;
    width: 24px !important;
    height: 24px !important;
    border: 3px solid #e0e0e0 !important;
    border-top-color: #ff4b4b !important;
    border-radius: 50% !important;
    animation: spinner-rotate 0.8s linear infinite !important;
}

@keyframes spinner-rotate {
    to { transform: rotate(360deg); }
}

/* Ocultar el status widget de la esquina superior derecha */
[data-testid="stStatusWidget"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# Inicializar session_state
if "eval_actual" not in st.session_state:
    st.session_state["eval_actual"] = None
if "eval_nombre" not in st.session_state:
    st.session_state["eval_nombre"] = None

# Asegurar hojas necesarias
ensure_sheet_exists("CUESTIONARIOS", CUESTIONARIOS_HEADERS)
ensure_sheet_exists("RESPUESTAS", RESPUESTAS_HEADERS)
ensure_sheet_exists("IMPACTO_ACTIVOS", IMPACTO_HEADERS)
ensure_sheet_exists("ANALISIS_RIESGO", ANALISIS_RIESGO_HEADERS)

# ==================== TÍTULO Y SIDEBAR ====================

st.title("🛡️ Proyecto TITA - Evaluación de Riesgos")
st.caption("Metodología MAGERIT + ISO/IEC 27002:2022 | IA con Ollama")

# Sidebar
with st.sidebar:
    st.header("📊 Panel de Control")
    
    # Estado de evaluación actual
    if st.session_state["eval_actual"]:
        st.success(f"✅ **Evaluación Activa**")
        st.info(f"📋 {st.session_state['eval_nombre']}\n\n🆔 `{st.session_state['eval_actual']}`")
        
        # Estadísticas
        stats = get_estadisticas_evaluacion(st.session_state["eval_actual"])
        col1, col2 = st.columns(2)
        col1.metric("Activos", stats["total_activos"])
        col2.metric("Progreso", f"{stats['progreso']}%")
        
        col3, col4 = st.columns(2)
        col3.metric("✅ Evaluados", stats["evaluados"])
        col4.metric("⏳ Pendientes", stats["pendientes"])
        
        if st.button("🔄 Cambiar Evaluación", use_container_width=True):
            st.session_state["eval_actual"] = None
            st.session_state["eval_nombre"] = None
            st.rerun()
    else:
        st.warning("⚠️ **Sin Evaluación Seleccionada**")
        st.info("👉 Ve a la pestaña **🏠 Evaluaciones** para seleccionar o crear una.")
    
    st.divider()
    st.caption("💾 SQLite: tita_database.db")
    st.caption("🔄 Estados automáticos activados")

# ==================== TABS ====================

tab0, tab1, tab2, tab3, tab4, tab5, tab_matriz, tab_ia_adv, tab6, tab_ia = st.tabs([
    "Evaluaciones",
    "Activos",
    "Cuestionarios",
    "Evaluacion con IA",
    "Dashboard",
    "Madurez",
    "Matriz MAGERIT",
    "IA Avanzada",
    "Comparativas",
    "Validacion IA"
])

# ==================== TAB 0: EVALUACIONES (CAPA 1 - OBLIGATORIA) ====================
with tab0:
    st.header("🏠 Gestión de Evaluaciones")
    st.markdown("""
    Las **Evaluaciones** son el contenedor principal del sistema. Todo activo, cuestionario 
    y análisis debe pertenecer a una evaluación.
    
    📌 **Flujo correcto:**
    1. Crea o selecciona una evaluación
    2. Gestiona activos dentro de esa evaluación
    3. Responde cuestionarios y ejecuta análisis IA
    """)
    
    col1, col2 = st.columns([2, 1])
    
    # COLUMNA 1: Listado de evaluaciones
    with col1:
        st.subheader("📋 Evaluaciones Existentes")
        
        evals = get_evaluaciones()
        
        if evals.empty:
            st.info("ℹ️ No hay evaluaciones creadas. **Crea la primera evaluación** →")
        else:
            # Filtros
            fcol1, fcol2 = st.columns(2)
            with fcol1:
                filtro_estado = st.selectbox(
                    "Filtrar por estado",
                    ["Todos", "En Progreso", "Completada", "Archivada"],
                    key="t0_filtro_estado"
                )
            with fcol2:
                buscar = st.text_input("🔍 Buscar", placeholder="Nombre o ID...", key="t0_buscar")
            
            # Aplicar filtros
            evals_filtradas = evals.copy()
            if filtro_estado != "Todos":
                evals_filtradas = evals_filtradas[evals_filtradas["Estado"] == filtro_estado]
            if buscar:
                evals_filtradas = evals_filtradas[
                    evals_filtradas["ID_Evaluacion"].str.contains(buscar, case=False, na=False) |
                    evals_filtradas["Nombre"].str.contains(buscar, case=False, na=False)
                ]
            
            # Tabla (usar solo columnas existentes)
            columnas_mostrar = ["ID_Evaluacion", "Nombre", "Estado"]
            if "Fecha_Creacion" in evals_filtradas.columns:
                columnas_mostrar.insert(2, "Fecha_Creacion")
            if "Responsable" in evals_filtradas.columns:
                columnas_mostrar.insert(3, "Responsable")
            
            st.dataframe(
                evals_filtradas[columnas_mostrar],
                use_container_width=True,
                height=300
            )
            
            # Seleccionar y trabajar
            if not evals_filtradas.empty:
                st.markdown("---")
                
                scol1, scol2 = st.columns([3, 1])
                with scol1:
                    eval_selec = st.selectbox(
                        "🎯 Seleccionar evaluación para gestionar",
                        evals_filtradas["ID_Evaluacion"].tolist(),
                        key="t0_eval_accion",
                        format_func=lambda x: f"{x} - {evals[evals['ID_Evaluacion']==x].iloc[0]['Nombre']}"
                    )
                
                with scol2:
                    st.write("")  # Espaciador
                    st.write("")
                    bcol1, bcol2 = st.columns(2)
                    with bcol1:
                        if st.button("🚀 **Gestionar**", key="t0_trabajar", type="primary", use_container_width=True):
                            st.session_state["eval_actual"] = eval_selec
                            eval_data = evals[evals["ID_Evaluacion"] == eval_selec].iloc[0]
                            st.session_state["eval_nombre"] = eval_data["Nombre"]
                            st.success(f"✅ Evaluación **{eval_selec}** activada")
                            st.balloons()
                            st.rerun()
                    with bcol2:
                        if st.button("🗑️ Eliminar", key="t0_eliminar", type="secondary", use_container_width=True):
                            st.session_state["eval_a_eliminar"] = eval_selec
                
                # Diálogo de confirmación para eliminar
                if st.session_state.get("eval_a_eliminar") == eval_selec:
                    st.warning(f"⚠️ ¿Seguro que deseas eliminar la evaluación **{eval_selec}**? Esta acción eliminará todos sus activos, cuestionarios y resultados.")
                    dcol1, dcol2 = st.columns(2)
                    with dcol1:
                        if st.button("✅ Sí, eliminar", key="t0_confirmar_elim", type="primary"):
                            from services.database_service import delete_rows
                            # Eliminar datos relacionados
                            delete_rows("RESPUESTAS", {"ID_Evaluacion": eval_selec})
                            delete_rows("CUESTIONARIOS", {"ID_Evaluacion": eval_selec})
                            delete_rows("IMPACTO_ACTIVOS", {"ID_Evaluacion": eval_selec})
                            delete_rows("INVENTARIO_ACTIVOS", {"ID_Evaluacion": eval_selec})
                            delete_rows("RESULTADOS_MAGERIT", {"ID_Evaluacion": eval_selec})
                            delete_rows("EVALUACIONES", {"ID_Evaluacion": eval_selec})
                            # Limpiar estado
                            if st.session_state.get("eval_actual") == eval_selec:
                                st.session_state["eval_actual"] = None
                                st.session_state["eval_nombre"] = None
                            st.session_state["eval_a_eliminar"] = None
                            st.success(f"🗑️ Evaluación **{eval_selec}** eliminada correctamente")
                            st.rerun()
                    with dcol2:
                        if st.button("❌ Cancelar", key="t0_cancelar_elim"):
                            st.session_state["eval_a_eliminar"] = None
                            st.rerun()
    
    # COLUMNA 2: Crear nueva evaluación
    with col2:
        st.subheader("➕ Nueva Evaluación")
        
        modo = st.radio(
            "Tipo",
            ["Desde cero", "Re-evaluación"],
            key="t0_modo",
            help="Re-evaluación copia activos sin respuestas"
        )
        
        with st.form("form_nueva_eval"):
            nombre = st.text_input("Nombre *", placeholder="Ej: Evaluación Q1 2026")
            responsable = st.text_input("Responsable *", placeholder="Ej: Juan Pérez")
            descripcion = st.text_area("Descripción", placeholder="Contexto...")
            
            origen_eval = None
            if modo == "Re-evaluación":
                st.info("ℹ️ Se copiarán activos (sin respuestas)")
                if not evals.empty:
                    origen_eval = st.selectbox(
                        "Evaluación origen",
                        evals["ID_Evaluacion"].tolist(),
                        key="t0_origen"
                    )
                else:
                    st.warning("No hay evaluaciones para re-evaluar")
            
            submitted = st.form_submit_button("✅ Crear Evaluación", type="primary")
        
        if submitted:
            if not nombre or not responsable:
                st.error("❌ Nombre y responsable obligatorios")
            else:
                nuevo_id = crear_evaluacion(
                    nombre=nombre,
                    descripcion=descripcion,
                    responsable=responsable,
                    origen_id=origen_eval if modo == "Re-evaluación" else None
                )
                st.success(f"🎉 Evaluación **{nuevo_id}** creada")
                st.session_state["eval_actual"] = nuevo_id
                st.session_state["eval_nombre"] = nombre
                st.balloons()
                st.rerun()


# ==================== TAB 1: ACTIVOS (REQUIERE EVALUACIÓN) ====================
with tab1:
    st.header("📦 Gestión de Activos")
    
    # VALIDACIÓN OBLIGATORIA
    if st.session_state.get("eval_actual"):
        st.success(f"📋 Evaluación: **{st.session_state['eval_nombre']}** (`{st.session_state['eval_actual']}`)")
        
        # Actualizar estados automáticos al entrar
        actualizar_estados_automaticos(st.session_state["eval_actual"])
    
    actcol1, actcol2 = st.columns([2, 1])
    
    # COLUMNA 1: Listado de activos
    with actcol1:
        st.subheader("📊 Inventario de Activos")
        
        activos = get_activos_por_evaluacion(st.session_state["eval_actual"])
        
        if activos.empty:
            st.info("ℹ️ No hay activos. **Crea el primero** →")
        else:
            # Filtros
            fcol1, fcol2, fcol3 = st.columns(3)
            with fcol1:
                tipos = ["Todos"] + activos["Tipo_Activo"].dropna().unique().tolist()
                tipo_filter = st.selectbox("Tipo", tipos, key="t1_tipo")
            with fcol2:
                ubicaciones = ["Todas"] + activos["Ubicacion"].dropna().unique().tolist()
                ubic_filter = st.selectbox("Ubicación", ubicaciones, key="t1_ubic")
            with fcol3:
                estados = ["Todos"] + activos["Estado"].dropna().unique().tolist()
                estado_filter = st.selectbox("Estado", estados, key="t1_estado")
            
            # Aplicar filtros
            activos_filtrados = activos.copy()
            if tipo_filter != "Todos":
                activos_filtrados = activos_filtrados[activos_filtrados["Tipo_Activo"] == tipo_filter]
            if ubic_filter != "Todas":
                activos_filtrados = activos_filtrados[activos_filtrados["Ubicacion"] == ubic_filter]
            if estado_filter != "Todos":
                activos_filtrados = activos_filtrados[activos_filtrados["Estado"] == estado_filter]
            
            # Tabla con estados coloreados
            st.dataframe(
                activos_filtrados[["ID_Activo", "Nombre_Activo", "Tipo_Activo", "Ubicacion", "Estado", "Tipo_Servicio"]],
                use_container_width=True,
                height=350
            )
            st.caption(f"📊 Mostrando {len(activos_filtrados)} de {len(activos)} activos")
            
            # Acciones
            if not activos_filtrados.empty:
                st.markdown("### ⚙️ Acciones")
                activo_selec = st.selectbox(
                    "Seleccionar activo",
                    activos_filtrados["ID_Activo"].tolist(),
                    key="t1_activo_selec"
                )
                
                acol1, acol2 = st.columns(2)
                
                with acol1:
                    if st.button("✏️ Editar", key="t1_editar"):
                        st.session_state["editar_activo"] = activo_selec
                        st.rerun()
                
                with acol2:
                    if st.button("🗑️ Eliminar", key="t1_eliminar"):
                        st.session_state["confirmar_eliminar"] = activo_selec
                        st.rerun()
                
                # Confirmación de eliminación
                if st.session_state.get("confirmar_eliminar"):
                    st.warning(f"⚠️ ¿Eliminar **{st.session_state['confirmar_eliminar']}**?")
                    ccol1, ccol2 = st.columns(2)
                    with ccol1:
                        if st.button("✅ Sí, eliminar", key="t1_confirmar_si"):
                            exito, msg = eliminar_activo(
                                st.session_state["eval_actual"],
                                st.session_state["confirmar_eliminar"]
                            )
                            if exito:
                                st.success(msg)
                                st.session_state["confirmar_eliminar"] = None
                                actualizar_estados_automaticos(st.session_state["eval_actual"])
                                st.rerun()
                            else:
                                st.error(msg)
                    with ccol2:
                        if st.button("❌ Cancelar", key="t1_confirmar_no"):
                            st.session_state["confirmar_eliminar"] = None
                            st.rerun()
                
                # Mostrar estado automático
                activo_data = get_activo(st.session_state["eval_actual"], activo_selec)
                estado_actual = calcular_estado_activo(st.session_state["eval_actual"], activo_selec)
                
                st.info(f"🔄 **Estado automático:** `{estado_actual}`")
                
                # Explicación del estado
                if estado_actual == "Pendiente":
                    st.caption("📌 Sin cuestionario generado")
                elif estado_actual == "Incompleto":
                    st.caption("⏳ Cuestionario iniciado pero no completo")
                elif estado_actual == "Completo":
                    st.caption("✅ Cuestionario completo, listo para evaluar con IA")
                elif estado_actual == "Evaluado":
                    st.caption("🎯 Evaluado con IA")
    
    # COLUMNA 2: Crear/Editar activo
    with actcol2:
        if st.session_state.get("editar_activo"):
            st.subheader("✏️ Editar Activo")
            activo_data = get_activo(st.session_state["eval_actual"], st.session_state["editar_activo"])
            
            with st.form("form_editar_activo"):
                nombre_act = st.text_input("Nombre *", value=activo_data.get("Nombre_Activo", ""))
                tipo_act = st.selectbox(
                    "Tipo *",
                    ["Servidor Físico", "Servidor Virtual"],
                    index=0 if activo_data.get("Tipo_Activo") == "Servidor Físico" else 1
                )
                ubicacion = st.selectbox(
                    "Ubicación *",
                    ["UdlaPark", "Granados"],
                    index=0 if activo_data.get("Ubicacion") == "UdlaPark" else 1
                )
                propietario = st.selectbox(
                    "Propietario *",
                    ["Infraestructura", "Seguridad de la Información", "Soporte"],
                    index=["Infraestructura", "Seguridad de la Información", "Soporte"].index(
                        activo_data.get("Propietario", "Infraestructura")
                    )
                )
                tipo_servicio = st.selectbox(
                    "Tipo Servicio *",
                    ["Base de datos", "Servidor web", "Servidor aplicaciones", 
                     "Firewall", "Switch", "Router", "Storage", "Backup", "Otro"]
                )
                app_critica = st.radio(
                    "Aplicación Crítica",
                    ["Sí", "No"],
                    index=0 if activo_data.get("App_Critica") == "Sí" else 1,
                    horizontal=True
                )
                
                submitted_edit = st.form_submit_button("💾 Guardar", type="primary")
            
            if submitted_edit:
                datos = {
                    "Nombre_Activo": nombre_act,
                    "Tipo_Activo": tipo_act,
                    "Ubicacion": ubicacion,
                    "Propietario": propietario,
                    "Tipo_Servicio": tipo_servicio,
                    "App_Critica": app_critica
                }
                exito, msg = editar_activo(
                    st.session_state["eval_actual"],
                    st.session_state["editar_activo"],
                    datos
                )
                if exito:
                    st.success(msg)
                    st.session_state["editar_activo"] = None
                    actualizar_estados_automaticos(st.session_state["eval_actual"])
                    st.rerun()
                else:
                    st.error(msg)
            
            if st.button("❌ Cancelar", key="t1_cancelar_edit"):
                st.session_state["editar_activo"] = None
                st.rerun()
        
        else:
            st.subheader("➕ Crear Activo")
            
            # Botón para carga masiva
            if CARGA_MASIVA_DISPONIBLE:
                if st.button("📤 Carga Masiva (JSON/Excel)", key="t1_btn_carga_masiva", type="secondary"):
                    st.session_state["mostrar_carga_masiva"] = True
                    st.rerun()
            
            with st.form("form_crear_activo"):
                nombre_act = st.text_input("Nombre *", placeholder="Ej: Servidor DB Principal")
                tipo_act = st.selectbox("Tipo *", ["Servidor Físico", "Servidor Virtual"])
                ubicacion = st.selectbox("Ubicación *", ["UdlaPark", "Granados"])
                propietario = st.selectbox(
                    "Propietario *",
                    ["Infraestructura", "Seguridad de la Información", "Soporte"]
                )
                tipo_servicio = st.selectbox(
                    "Tipo Servicio *",
                    ["Base de datos", "Servidor web", "Servidor aplicaciones", 
                     "Firewall", "Switch", "Router", "Storage", "Backup", "Otro"]
                )
                app_critica = st.radio("Aplicación Crítica", ["Sí", "No"], horizontal=True)
                
                submitted_create = st.form_submit_button("✅ Crear", type="primary")
            
            if submitted_create:
                if not nombre_act:
                    st.error("❌ Nombre obligatorio")
                else:
                    # Validar duplicados
                    es_duplicado, msg_dup = validar_duplicado(
                        st.session_state["eval_actual"],
                        nombre_act,
                        ubicacion,
                        tipo_servicio
                    )
                    
                    if es_duplicado:
                        st.error(f"❌ {msg_dup}")
                    else:
                        datos = {
                            "Nombre_Activo": nombre_act,
                            "Tipo_Activo": tipo_act,
                            "Ubicacion": ubicacion,
                            "Propietario": propietario,
                            "Tipo_Servicio": tipo_servicio,
                            "App_Critica": app_critica
                        }
                        
                        exito, msg, nuevo_id = crear_activo(st.session_state["eval_actual"], datos)
                        if exito:
                            st.success(msg)
                            actualizar_estados_automaticos(st.session_state["eval_actual"])
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(msg)
    
    # ===== SECCIÓN DE CARGA MASIVA (Modal-like) =====
    if st.session_state.get("mostrar_carga_masiva") and CARGA_MASIVA_DISPONIBLE:
        st.divider()
        
        col_header1, col_header2 = st.columns([6, 1])
        with col_header1:
            st.markdown("## 📤 Carga Masiva de Activos")
        with col_header2:
            if st.button("❌ Cerrar", key="t1_cerrar_carga_masiva"):
                st.session_state["mostrar_carga_masiva"] = False
                st.rerun()
        
        render_carga_masiva(
            st.session_state["eval_actual"],
            st.session_state["eval_nombre"]
        )


# ==================== TAB 2: CUESTIONARIO (REQUIERE EVALUACIÓN) ====================
with tab2:
    st.header("📝 Cuestionarios")
    
    if not st.session_state.get("eval_actual"):
        st.error("🚫 **EVALUACIÓN REQUERIDA**")
        st.warning("👉 Ve a la pestaña **🏠 Evaluaciones** y selecciona una evaluación primero.")
    else:
        st.success(f"📋 Evaluación: **{st.session_state['eval_nombre']}**")
        
        activos = get_activos_por_evaluacion(st.session_state["eval_actual"])
        
        if activos.empty:
            st.warning("⚠️ No hay activos registrados. Ve a **📦 Activos** para crear uno.")
        else:
            # ===== Selector de activo con estado =====
            st.markdown("### 🎯 Seleccionar Activo")
            
            # Crear diccionario para format_func y calcular estados
            activos_dict = dict(zip(activos["ID_Activo"], activos["Nombre_Activo"]))
            
            # Mostrar tabla de activos con estado
            datos_activos = []
            for _, activo in activos.iterrows():
                activo_id_temp = activo["ID_Activo"]
                cuest_temp = get_cuestionario(st.session_state["eval_actual"], activo_id_temp)
                resp_temp = read_sheet("RESPUESTAS")
                resp_activo = resp_temp[
                    (resp_temp["ID_Evaluacion"] == st.session_state["eval_actual"]) &
                    (resp_temp["ID_Activo"] == activo_id_temp)
                ] if not resp_temp.empty else pd.DataFrame()
                
                total_preg = len(cuest_temp)
                respondidas = len(resp_activo)
                
                if total_preg == 0:
                    estado = "🔴 Sin cuestionario"
                elif respondidas == 0:
                    estado = "🟡 Pendiente"
                elif respondidas < total_preg:
                    estado = f"🟠 En proceso ({respondidas}/{total_preg})"
                else:
                    estado = "🟢 Completado"
                
                datos_activos.append({
                    "ID": activo_id_temp,
                    "Nombre": activo["Nombre_Activo"],
                    "Tipo": activo.get("Tipo_Activo", "N/A"),
                    "Estado": estado
                })
            
            df_estados = pd.DataFrame(datos_activos)
            st.dataframe(df_estados, use_container_width=True, hide_index=True)
            
            # Selector
            activo_id = st.selectbox(
                "Seleccionar activo para responder cuestionario:",
                activos["ID_Activo"].tolist(),
                key="t2_activo",
                format_func=lambda x: f"{x} - {activos_dict.get(x, 'N/A')}"
            )
            
            activo_data = get_activo(st.session_state["eval_actual"], activo_id)
            
            st.divider()
            
            # ===== Verificar/Generar cuestionario automáticamente =====
            cuestionario_df = get_cuestionario(st.session_state["eval_actual"], activo_id)
            cuestionario_error = False
            
            if cuestionario_df.empty:
                with st.spinner(f"🔄 Cargando cuestionario del banco {activo_data.get('Tipo_Activo', 'N/A')}..."):
                    try:
                        exito, mensaje, num_preguntas = generar_cuestionario(
                            eval_id=st.session_state["eval_actual"],
                            activo=activo_data,
                            model=""
                        )
                        if exito:
                            actualizar_estados_automaticos(st.session_state["eval_actual"])
                            st.rerun()
                        else:
                            st.error(f"❌ {mensaje}")
                            cuestionario_error = True
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        cuestionario_error = True
            
            if not cuestionario_error and not cuestionario_df.empty:
                # ===== Cargar respuestas existentes =====
                respuestas_df = read_sheet("RESPUESTAS")
                respuestas_existentes = respuestas_df[
                    (respuestas_df["ID_Evaluacion"] == st.session_state["eval_actual"]) &
                    (respuestas_df["ID_Activo"] == activo_id)
                ] if not respuestas_df.empty else pd.DataFrame()
                
                total_preguntas = len(cuestionario_df)
                respondidas = len(respuestas_existentes)
                progreso = int((respondidas / total_preguntas) * 100) if total_preguntas > 0 else 0
                
                # ===== Estado y progreso =====
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📋 Total Preguntas", total_preguntas)
                with col2:
                    st.metric("✅ Respondidas", respondidas)
                with col3:
                    if respondidas == 0:
                        st.warning("🟡 Pendiente")
                    elif respondidas < total_preguntas:
                        st.info(f"🟠 En proceso")
                    else:
                        st.success("🟢 Completado")
                
                st.progress(min(progreso / 100, 1.0))
                
                st.divider()
                
                # ===== Verificar si ya existen respuestas completas (cuestionario ya guardado) =====
                cuestionario_ya_guardado = verificar_respuestas_existentes(st.session_state["eval_actual"], activo_id)
                
                if cuestionario_ya_guardado:
                    st.success("✅ **Cuestionario completado y guardado**")
                    st.info("ℹ️ Las respuestas ya fueron registradas para este activo. Puedes ir a **📊 Valoración DIC** o **🤖 Análisis IA**.")
                    
                    # Mostrar respuestas en modo lectura
                    st.markdown(f"### 📋 Respuestas Guardadas - {activo_data.get('Tipo_Activo', 'Activo')}")
                    
                    for idx, row in respuestas_existentes.iterrows():
                        with st.expander(f"**{row.get('ID_Pregunta', 'N/A')}** - {row.get('Bloque', '')}", expanded=False):
                            st.write(f"**Pregunta:** {row.get('Pregunta', 'N/A')}")
                            st.write(f"**Respuesta:** {row.get('Respuesta', 'N/A')}")
                            st.caption(f"Valor: {row.get('Valor_Numerico', 'N/A')} | Peso: {row.get('Peso', 'N/A')} | Dimensión: {row.get('Dimension', 'N/A')}")
                
                else:
                    # ===== Formulario de respuestas (solo si no hay respuestas guardadas) =====
                    st.markdown(f"### ✍️ Responder Cuestionario - {activo_data.get('Tipo_Activo', 'Activo')}")
                    
                    with st.form("form_cuestionario"):
                        respuestas = {}
                        
                        # Agrupar por dimensión
                        dimensiones = {"D": "🛡️ Disponibilidad", "I": "✅ Integridad", "C": "🔒 Confidencialidad"}
                        
                        for dim_code, dim_name in dimensiones.items():
                            preguntas_dim = cuestionario_df[cuestionario_df["Dimension"] == dim_code]
                            if not preguntas_dim.empty:
                                st.markdown(f"#### {dim_name}")
                                
                                for idx, row in preguntas_dim.iterrows():
                                    id_pregunta = row.get('ID_Pregunta', f'P{idx}')
                                    pregunta_texto = row.get('Pregunta', 'N/A')
                                    bloque = row.get('Bloque', '')
                                    
                                    # Obtener las 4 opciones
                                    opciones = [
                                        str(row.get('Opcion_1', '')),
                                        str(row.get('Opcion_2', '')),
                                        str(row.get('Opcion_3', '')),
                                        str(row.get('Opcion_4', ''))
                                    ]
                                    opciones = [o for o in opciones if o and o != 'nan']
                                    
                                    st.markdown(f"**{id_pregunta}.** {pregunta_texto}")
                                    if bloque:
                                        st.caption(f"📂 {bloque}")
                                    
                                    # Buscar respuesta existente
                                    resp_existente = respuestas_existentes[
                                        respuestas_existentes["ID_Pregunta"].astype(str) == str(id_pregunta)
                                    ] if not respuestas_existentes.empty else pd.DataFrame()
                                    
                                    valor_inicial = ""
                                    if not resp_existente.empty:
                                        valor_inicial = str(resp_existente.iloc[0]["Respuesta"])
                                    
                                    # Mostrar radio buttons con las 4 opciones
                                    if len(opciones) >= 4:
                                        # Determinar índice inicial - POR DEFECTO: ACTIVO CRÍTICO
                                        idx_inicial = 3  # Por defecto opción 4 (más crítico para impacto)
                                        if valor_inicial:
                                            try:
                                                idx_inicial = opciones.index(valor_inicial)
                                            except ValueError:
                                                idx_inicial = 3
                                        else:
                                            # Sin respuesta previa: seleccionar valores de ACTIVO CRÍTICO
                                            # Lógica basada en el bloque de la pregunta:
                                            bloque_upper = str(bloque).upper()
                                            
                                            if "IMPACTO" in bloque_upper or bloque_upper.startswith("A"):
                                                # Bloque A-Impacto: Opción 4 = mayor criticidad
                                                # (RTO menor, más usuarios, más dependencia, etc.)
                                                idx_inicial = 3
                                            elif "CONTINUIDAD" in bloque_upper or bloque_upper.startswith("B"):
                                                # Bloque B-Continuidad: Opción 1 = SIN controles = más crítico
                                                # (sin respaldo, sin failover, sin redundancia)
                                                idx_inicial = 0
                                            elif "CONTROL" in bloque_upper or bloque_upper.startswith("C"):
                                                # Bloque C-Controles: Opción 1 = SIN control = más crítico
                                                # (sin MFA, sin parches, sin monitoreo)
                                                idx_inicial = 0
                                            elif "EXPOSICION" in bloque_upper or "AMENAZA" in bloque_upper or bloque_upper.startswith("D"):
                                                # Bloque D-Exposición: Opción 4 = mayor exposición = más crítico
                                                idx_inicial = 3
                                            elif "CAPACIDAD" in bloque_upper or bloque_upper.startswith("E"):
                                                # Bloque E-Capacidad/Respuesta: Opción 1 = sin capacidad = más crítico
                                                idx_inicial = 0
                                            else:
                                                # Por defecto: Opción 4 para asumir mayor impacto
                                                idx_inicial = 3
                                        
                                        # Radio buttons con formato visual (1-4 = niveles de madurez)
                                        opciones_formateadas = [f"{i+1}. {op}" for i, op in enumerate(opciones)]
                                        
                                        resp = st.radio(
                                            f"Respuesta {id_pregunta}",
                                            options=opciones_formateadas,
                                            index=idx_inicial,
                                            key=f"t2_resp_{id_pregunta}",
                                            horizontal=False,
                                            label_visibility="collapsed"
                                        )
                                        # Extraer la opción sin el número
                                        respuestas[id_pregunta] = resp.split(". ", 1)[1] if ". " in resp else resp
                                    else:
                                        # Fallback a texto si no hay 4 opciones
                                        respuestas[id_pregunta] = st.text_area(
                                            f"Respuesta {id_pregunta}",
                                            value=valor_inicial,
                                            key=f"t2_resp_{id_pregunta}",
                                            label_visibility="collapsed",
                                            height=80
                                        )
                                    
                                    st.caption(f"Peso: {row.get('Peso', 'N/A')} | Dimensión: {dim_code}")
                                    st.divider()
                        
                        submitted = st.form_submit_button("💾 Guardar Respuestas", type="primary", use_container_width=True)
                    
                    if submitted:
                        # Validar respuestas no vacías
                        respuestas_validas = {k: v for k, v in respuestas.items() if v and str(v).strip()}
                        
                        if not respuestas_validas:
                            st.error("❌ Debes responder al menos una pregunta")
                        else:
                            fecha_cuestionario = cuestionario_df.iloc[0].get("Fecha_Version", dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            
                            respuestas_lista = []
                            for id_preg, respuesta_texto in respuestas_validas.items():
                                fila_preg = cuestionario_df[cuestionario_df["ID_Pregunta"] == id_preg]
                                if not fila_preg.empty:
                                    row = fila_preg.iloc[0]
                                    # Calcular valor numérico (1-4) basado en la opción seleccionada
                                    valor_numerico = 1
                                    for i, opt in enumerate(['Opcion_1', 'Opcion_2', 'Opcion_3', 'Opcion_4']):
                                        if str(row.get(opt, '')) == respuesta_texto:
                                            valor_numerico = i + 1
                                            break
                                    
                                    respuestas_lista.append({
                                        "ID_Pregunta": id_preg,
                                        "Pregunta": row.get("Pregunta", ""),
                                        "Respuesta": respuesta_texto,
                                        "Valor_Numerico": valor_numerico,
                                        "Peso": row.get("Peso", 3),
                                        "Dimension": row.get("Dimension", "I"),
                                        "Bloque": row.get("Bloque", "")
                                    })
                            
                            # Verificar análisis previo
                            analisis_previo = read_sheet("ANALISIS_RIESGO")
                            tenia_analisis = not analisis_previo[
                                (analisis_previo["ID_Evaluacion"] == st.session_state["eval_actual"]) &
                                (analisis_previo["ID_Activo"] == activo_id)
                            ].empty if not analisis_previo.empty else False
                            
                            exito = guardar_respuestas(
                                st.session_state["eval_actual"],
                                activo_id,
                                fecha_cuestionario,
                                respuestas_lista
                            )
                            
                            if exito:
                                st.success(f"✅ {len(respuestas_validas)} respuestas guardadas")
                                
                                if tenia_analisis:
                                    invalidar_analisis_ia(st.session_state["eval_actual"], activo_id)
                                    st.warning("⚠️ Respuestas modificadas invalidan el análisis IA anterior.")
                                
                                actualizar_estados_automaticos(st.session_state["eval_actual"])
                                
                                if verificar_cuestionario_completo(st.session_state["eval_actual"], activo_id):
                                    st.balloons()
                                    st.success("🎉 ¡Cuestionario completo! Puedes ir a **🤖 Análisis IA**")
                                
                                st.rerun()
                            else:
                                st.warning("⚠️ Ya existen respuestas guardadas para este activo. No se permiten duplicados.")


# ==================== TAB 3: EVALUACIÓN CON IA ====================
with tab3:
    st.header("🤖 Evaluación con IA")
    
    if not st.session_state.get("eval_actual"):
        st.error("🚫 **EVALUACIÓN REQUERIDA**")
        st.warning("👉 Ve a la pestaña **🏠 Evaluaciones** y selecciona una evaluación primero.")
    else:
        st.success(f"📋 Evaluación: **{st.session_state['eval_nombre']}**")
        
        st.markdown("""
        **Este módulo ejecutará una Evaluación de Riesgos usando IA:**
        - 🔄 Impacto DIC será calculado desde las respuestas del cuestionario
        - 🔄 La IA identificará amenazas del catálogo oficial (52 amenazas)
        - 🔄 Se recomendarán controles ISO 27002:2022 (93 controles oficiales)
        - 🔄 Se sugerirán salvaguardas para reducir el riesgo
        - 🔄 Se calcularán Riesgo Inherente y Residual
        
        ⚠️ **Antes de evaluar:** Asegúrate de haber completado el cuestionario de cada activo.
        """)
        
        # Verificar Ollama
        ollama_ok, modelos_disponibles = verificar_ollama_disponible()
        
        if ollama_ok:
            st.success(f"🟢 Ollama conectado. Modelos: {', '.join(modelos_disponibles[:5])}")
            modelo_ia = st.selectbox("Modelo IA", modelos_disponibles, index=0, key="t3_modelo")
        else:
            st.warning("⚠️ Ollama no disponible. Se usará modo manual.")
            modelo_ia = None
        
        # Verificar catálogos
        catalogo_amenazas = get_catalogo_amenazas()
        catalogo_controles = get_catalogo_controles()
        
        if not catalogo_amenazas or not catalogo_controles:
            st.error("❌ Catálogos no cargados. Ejecuta: `python seed_catalogos_magerit.py`")
        else:
            st.caption(f"📚 Catálogos: {len(catalogo_amenazas)} amenazas MAGERIT | {len(catalogo_controles)} controles ISO 27002")
            
            st.divider()
            
            # Obtener activos y sus estados
            activos = get_activos_por_evaluacion(st.session_state["eval_actual"])
            
            if activos.empty:
                st.warning("⚠️ No hay activos. Crea uno en el tab 📦 Activos.")
            else:
                respuestas_df = read_table("RESPUESTAS")
                
                # Calcular estados
                datos_activos = []
                activos_listos = []
                activos_evaluados = []
                
                for _, activo in activos.iterrows():
                    activo_id = activo["ID_Activo"]
                    
                    # Verificar cuestionario
                    cuest = get_cuestionario(st.session_state["eval_actual"], activo_id)
                    resp_activo = respuestas_df[
                        (respuestas_df["ID_Evaluacion"] == st.session_state["eval_actual"]) &
                        (respuestas_df["ID_Activo"] == activo_id)
                    ] if not respuestas_df.empty else pd.DataFrame()
                    
                    # Verificar resultado MAGERIT existente
                    resultado_existente = get_resultado_magerit(st.session_state["eval_actual"], activo_id)
                    
                    total_preg = len(cuest)
                    respondidas = len(resp_activo)
                    
                    if resultado_existente:
                        estado = "✅ Evaluado"
                        activos_evaluados.append(activo_id)
                        listo = False
                    elif total_preg == 0:
                        estado = "⚪ Sin cuestionario"
                        listo = False
                    elif respondidas < total_preg:
                        estado = f"🟡 Incompleto ({respondidas}/{total_preg})"
                        listo = False
                    else:
                        estado = "🟢 Listo para evaluar"
                        listo = True
                        activos_listos.append(activo_id)
                    
                    datos_activos.append({
                        "ID": activo_id,
                        "Nombre": activo["Nombre_Activo"],
                        "Tipo": activo.get("Tipo_Activo", "N/A"),
                        "Estado": estado
                    })
                
                df_estados = pd.DataFrame(datos_activos)
                st.dataframe(df_estados, use_container_width=True, hide_index=True)
                
                st.divider()
                
                # Verificar si IA está validada (bloqueo de seguridad)
                ia_validada_para_evaluar = True
                mensaje_bloqueo = ""
                
                if VALIDACION_IA_DISPONIBLE:
                    ia_validada_para_evaluar, mensaje_bloqueo = verificar_ia_lista_para_evaluar()
                    if not ia_validada_para_evaluar:
                        st.warning(f"⚠️ **Evaluación bloqueada:** {mensaje_bloqueo}")
                        st.info("👉 Vaya a la pestaña **🛡️ Validación IA** para validar la IA primero.")
                        render_boton_evaluar_bloqueado()
                
                # Sección de evaluación con IA
                if activos_listos and ollama_ok and ia_validada_para_evaluar:
                    st.markdown(f"### 🚀 Evaluar con IA ({len(activos_listos)} activos listos)")
                    
                    if st.button("🤖 Evaluar Todos con IA", type="primary", use_container_width=True):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        resultados_log = []
                        
                        for i, activo_id in enumerate(activos_listos):
                            status_text.text(f"Analizando {activo_id}... ({i+1}/{len(activos_listos)})")
                            progress_bar.progress(i / len(activos_listos))
                            
                            try:
                                # 1. Llamar IA con validación
                                exito_ia, resultado_ia, mensaje_ia = analizar_activo_con_ia(
                                    st.session_state["eval_actual"],
                                    activo_id,
                                    modelo_ia
                                )
                                
                                if exito_ia:
                                    # 2. Ejecutar motor MAGERIT
                                    resultado_magerit = evaluar_activo_magerit(
                                        st.session_state["eval_actual"],
                                        activo_id,
                                        resultado_ia.get("amenazas", []),
                                        resultado_ia.get("probabilidad", 3),
                                        resultado_ia.get("observaciones", ""),
                                        modelo_ia
                                    )
                                    
                                    # 3. Guardar resultado
                                    guardar_resultado_magerit(resultado_magerit)
                                    resultados_log.append(f"✅ {activo_id}: {len(resultado_magerit.amenazas)} amenazas identificadas")
                                else:
                                    resultados_log.append(f"⚠️ {activo_id}: {mensaje_ia[:200]}")
                            
                            except Exception as e:
                                resultados_log.append(f"❌ {activo_id}: {str(e)[:200]}")
                            
                            progress_bar.progress((i + 1) / len(activos_listos))
                        
                        status_text.text("✅ Evaluación MAGERIT completada")
                        
                        # Contar resultados
                        exitos = sum(1 for log in resultados_log if log.startswith("✅"))
                        advertencias = sum(1 for log in resultados_log if log.startswith("⚠️"))
                        errores_count = sum(1 for log in resultados_log if log.startswith("❌"))
                        
                        # Mostrar resumen
                        st.markdown("### 📊 Resumen de Evaluación")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("✅ Exitosos", exitos)
                        col2.metric("⚠️ Advertencias", advertencias)
                        col3.metric("❌ Errores", errores_count)
                        
                        # Mostrar logs detallados
                        with st.expander("📋 Ver detalles de cada activo", expanded=True):
                            for log in resultados_log:
                                if log.startswith("✅"):
                                    st.success(log)
                                elif log.startswith("⚠️"):
                                    st.warning(log)
                                else:
                                    st.error(log)
                        
                        if exitos > 0:
                            st.balloons()
                            st.success(f"🎉 {exitos} activo(s) evaluados correctamente. Ve al **📈 Dashboard** para ver los resultados.")
                        else:
                            st.error("❌ No se pudo evaluar ningún activo. Revisa los errores arriba.")
                        
                        # Botón para recargar en lugar de rerun automático
                        if st.button("🔄 Actualizar Vista", key="t3_refresh_after_eval"):
                            st.rerun()
                
                elif activos_listos and not ollama_ok:
                    st.markdown("### 📝 Evaluación Manual (Ollama no disponible)")
                    
                    activo_manual = st.selectbox(
                        "Seleccionar activo",
                        activos_listos,
                        format_func=lambda x: f"{x} - {df_estados[df_estados['ID']==x]['Nombre'].values[0]}"
                    )
                    
                    # Selector de amenazas manual
                    st.write("**Seleccionar amenazas aplicables:**")
                    amenazas_por_tipo = {}
                    for codigo, info in catalogo_amenazas.items():
                        tipo = info["tipo_amenaza"]
                        if tipo not in amenazas_por_tipo:
                            amenazas_por_tipo[tipo] = []
                        amenazas_por_tipo[tipo].append((codigo, info["amenaza"]))
                    
                    amenazas_seleccionadas = []
                    for tipo, lista in amenazas_por_tipo.items():
                        with st.expander(f"📁 {tipo}"):
                            for codigo, nombre in lista:
                                if st.checkbox(f"{codigo}: {nombre}", key=f"am_{codigo}"):
                                    amenazas_seleccionadas.append(codigo)
                    
                    prob_manual = st.slider("Probabilidad general (1-5)", 1, 5, 3)
                    obs_manual = st.text_area("Observaciones")
                    
                    if st.button("💾 Guardar Evaluación Manual", type="primary") and amenazas_seleccionadas:
                        activo_data = get_activo(st.session_state["eval_actual"], activo_manual)
                        eval_manual = crear_evaluacion_manual(
                            activo_data, amenazas_seleccionadas, prob_manual, obs_manual
                        )
                        
                        resultado = evaluar_activo_magerit(
                            st.session_state["eval_actual"],
                            activo_manual,
                            eval_manual["amenazas"],
                            eval_manual["probabilidad"],
                            eval_manual["observaciones"],
                            "manual"
                        )
                        guardar_resultado_magerit(resultado)
                        st.success(f"✅ Evaluación guardada: {len(resultado.amenazas)} amenazas")
                        st.rerun()
                
                else:
                    st.info("ℹ️ No hay activos listos para evaluar. Completa los cuestionarios primero.")
                
                st.divider()
                
                # Mostrar resultados existentes
                if activos_evaluados:
                    st.markdown("### 📊 Resultados de Evaluación MAGERIT")
                    
                    for activo_id in activos_evaluados:
                        resultado = get_resultado_magerit(st.session_state["eval_actual"], activo_id)
                        if resultado:
                            nombre = resultado.get("nombre_activo", activo_id)
                            nivel_inh = resultado.get("nivel_riesgo_inherente_global", "N/A")
                            nivel_res = resultado.get("nivel_riesgo_residual_global", "N/A")
                            
                            with st.expander(f"🔍 {activo_id} - {nombre} | Inherente: {nivel_inh} | Residual: {nivel_res}"):
                                # Impacto DIC
                                impacto = resultado.get("impacto", {})
                                col1, col2, col3, col4 = st.columns(4)
                                col1.metric("Disponibilidad", impacto.get("disponibilidad", "-"))
                                col2.metric("Integridad", impacto.get("integridad", "-"))
                                col3.metric("Confidencialidad", impacto.get("confidencialidad", "-"))
                                col4.metric("Impacto Global", max(
                                    impacto.get("disponibilidad", 0),
                                    impacto.get("integridad", 0),
                                    impacto.get("confidencialidad", 0)
                                ))
                                
                                st.caption(f"D: {impacto.get('justificacion_d', '')} | I: {impacto.get('justificacion_i', '')} | C: {impacto.get('justificacion_c', '')}")
                                
                                # Riesgos
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric(
                                        "Riesgo Inherente",
                                        f"{resultado.get('riesgo_inherente_global', 0)} ({nivel_inh})"
                                    )
                                with col2:
                                    st.metric(
                                        "Riesgo Residual",
                                        f"{resultado.get('riesgo_residual_global', 0)} ({nivel_res})"
                                    )
                                
                                # Controles existentes identificados
                                controles_exist = resultado.get("controles", [])
                                if controles_exist:
                                    st.markdown("**✅ Controles existentes identificados:**")
                                    for ctrl_code in controles_exist[:8]:
                                        st.markdown(f"- `{ctrl_code}`")
                                    if len(controles_exist) > 8:
                                        st.caption(f"... y {len(controles_exist) - 8} más")
                                else:
                                    # Obtener controles desde respuestas
                                    ctrl_detalle = get_controles_existentes_detallados(
                                        st.session_state["eval_actual"], activo_id
                                    )
                                    if ctrl_detalle.get("controles"):
                                        st.markdown("**✅ Controles existentes identificados:**")
                                        resumen = ctrl_detalle.get("resumen", {})
                                        st.caption(f"Implementados: {resumen.get('implementados', 0)} | Parciales: {resumen.get('parciales', 0)}")
                                        for ctrl in ctrl_detalle["controles"][:5]:
                                            icono = "✅" if ctrl["efectividad"] >= 0.66 else "⚠️"
                                            st.markdown(f"- {icono} `{ctrl['codigo']}`: {ctrl['nombre'][:40]}...")
                                    else:
                                        st.caption("ℹ️ Complete el cuestionario para identificar controles")
                                
                                # Amenazas
                                amenazas = resultado.get("amenazas", [])
                                if amenazas:
                                    st.markdown("**⚠️ Amenazas identificadas:**")
                                    for am in amenazas:
                                        nivel = am.get("nivel_riesgo", "")
                                        icono = "🔴" if nivel == "CRÍTICO" else "🟠" if nivel == "ALTO" else "🟡" if nivel == "MEDIO" else "🟢"
                                        st.markdown(f"- {icono} **{am.get('codigo', '')}**: {am.get('amenaza', '')} (R={am.get('riesgo_inherente', 0)} → R.Res={am.get('riesgo_residual', 0)}) - {am.get('tratamiento', '')}")
                                
                                # Controles recomendados
                                controles_rec = resultado.get("controles_recomendados_global", [])
                                if controles_rec:
                                    st.markdown("**🛡️ Controles recomendados:**")
                                    for ctrl in controles_rec[:10]:
                                        st.markdown(f"- **{ctrl.get('codigo', '')}**: {ctrl.get('nombre', '')} ({ctrl.get('prioridad', '')})")
                                
                                # Observaciones
                                if resultado.get("observaciones"):
                                    st.info(f"📝 {resultado.get('observaciones')}")


# ==================== TAB 4: DASHBOARD RIESGOS MAGERIT ====================
with tab4:
    st.header("Dashboard de Evaluacion")
    
    if not st.session_state.get("eval_actual"):
        st.error("EVALUACION REQUERIDA")
        st.warning("Ve a la pestana Evaluaciones y selecciona una evaluacion primero.")
    else:
        st.success(f"Evaluacion: **{st.session_state['eval_nombre']}**")
        
        # Obtener resumen de evaluación MAGERIT
        resumen_magerit = get_resumen_evaluacion(st.session_state["eval_actual"])
        activos = get_activos_por_evaluacion(st.session_state["eval_actual"])
        
        # Obtener datos de madurez
        madurez_data = get_madurez_evaluacion(st.session_state["eval_actual"])
        
        if resumen_magerit.empty:
            st.info("No hay evaluaciones completadas. Ve al tab Evaluacion con IA para evaluar activos.")
            
            # Mostrar estadísticas básicas de activos
            if not activos.empty:
                st.markdown("### Estado de Activos")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Activos", len(activos))
                col2.metric("Pendientes", len(activos[activos["Estado"] == "Pendiente"]))
                col3.metric("Completos", len(activos[activos["Estado"] == "Completo"]))
        else:
            # Usar componentes de dashboard si están disponibles
            if DASHBOARD_DISPONIBLE:
                # Crear tabs internos para organizar dashboards (sin Vista Clasica)
                dash_tab1, dash_tab2, dash_tab3, dash_tab4 = st.tabs([
                    "🎯 Activos Criticos",
                    "⚠️ Tratamiento Urgente", 
                    "🔥 Amenazas MAGERIT",
                    "🛡️ Controles y Salvaguardas"
                ])
                
                with dash_tab1:
                    render_ranking_activos_criticos(resumen_magerit)
                    st.divider()
                    render_resumen_ejecutivo(resumen_magerit)
                    st.divider()
                    # Matriz 5x5 MAGERIT
                    render_matriz_5x5_activos(resumen_magerit, key_suffix="activos_criticos")
                
                with dash_tab2:
                    render_activos_urgente_tratamiento(resumen_magerit)
                
                with dash_tab3:
                    # Dashboard de amenazas MAGERIT con catalogo y matriz 5x5
                    render_dashboard_amenazas_mejorado(resumen_magerit, st.session_state["eval_actual"])
                
                with dash_tab4:
                    render_dashboard_controles_salvaguardas(resumen_magerit, madurez_data)
            
            else:
                # Dashboard básico sin componentes
                st.markdown("### Resumen de Evaluacion")
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Activos Evaluados", len(resumen_magerit))
                
                if not resumen_magerit.empty:
                    col2.metric("Riesgo Maximo", f"{resumen_magerit['riesgo_inherente_global'].max():.1f}")
                    criticos = (resumen_magerit["nivel_riesgo_inherente"] == "CRITICO").sum()
                    altos = (resumen_magerit["nivel_riesgo_inherente"] == "ALTO").sum()
                    col3.metric("Criticos + Altos", criticos + altos)
                    col4.metric("Riesgo Residual Prom.", f"{resumen_magerit['riesgo_residual_global'].mean():.1f}")
                
                # Tabla de resultados
                st.markdown("### Tabla de Riesgos por Activo")
                st.dataframe(resumen_magerit[[
                    "nombre_activo", "tipo_activo", "impacto_global",
                    "riesgo_inherente_global", "nivel_riesgo_inherente",
                    "riesgo_residual_global", "nivel_riesgo_residual"
                ]], use_container_width=True, hide_index=True)
                
                # Gráfico de barras comparativo
                if len(resumen_magerit) > 0:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        name="Riesgo Inherente",
                        x=resumen_magerit["nombre_activo"],
                        y=resumen_magerit["riesgo_inherente_global"],
                        marker_color="#FF6347"
                    ))
                    fig.add_trace(go.Bar(
                        name="Riesgo Residual",
                        x=resumen_magerit["nombre_activo"],
                        y=resumen_magerit["riesgo_residual_global"],
                        marker_color="#32CD32"
                    ))
                    fig.update_layout(barmode='group', title="Riesgo Inherente vs Residual por Activo")
                    st.plotly_chart(fig, use_container_width=True, key="t4_riesgo_inh_res")
            
            # Selector de detalle de activo
            st.divider()
            st.markdown("### Ver Detalle de Activo")
            
            activo_detalle = st.selectbox(
                "Seleccionar activo",
                resumen_magerit["id_activo"].tolist(),
                format_func=lambda x: f"{x} - {resumen_magerit[resumen_magerit['id_activo']==x]['nombre_activo'].values[0]}",
                key=f"t4_detalle_activo_{st.session_state['eval_actual']}"
            )
            
            if activo_detalle:
                resultado = get_resultado_magerit(st.session_state["eval_actual"], activo_detalle)
                if resultado:
                    st.caption(f"ID: {resultado.get('id_activo')} | Impacto DIC: {resultado.get('impacto_d')}/{resultado.get('impacto_i')}/{resultado.get('impacto_c')}")
                    if DASHBOARD_DISPONIBLE:
                        render_detalle_activo(resultado)
                    else:
                        # Detalle básico
                        st.json(resultado)
    
    # Botón de refresco
    if st.button("Actualizar Dashboard", key="t4_refresh"):
        st.rerun()


# ==================== TAB 5: NIVEL DE MADUREZ ====================
with tab5:
    st.header("🎯 Nivel de Madurez de Ciberseguridad")
    
    if not st.session_state.get("eval_actual"):
        st.error("🚫 **EVALUACIÓN REQUERIDA**")
        st.warning("👉 Ve a la pestaña **🏠 Evaluaciones** y selecciona una evaluación primero.")
    else:
        st.success(f"📋 Evaluación: **{st.session_state['eval_nombre']}**")
        
        # Obtener madurez guardada primero
        madurez_data = get_madurez_evaluacion(st.session_state["eval_actual"])
        
        # Solo mostrar botón de calcular si NO hay datos o el usuario quiere recalcular
        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            if not madurez_data:
                if st.button("🔄 Calcular Nivel de Madurez", type="primary", key="t5_calc_madurez"):
                    with st.spinner("Calculando nivel de madurez..."):
                        resultado_madurez = calcular_madurez_evaluacion(st.session_state["eval_actual"])
                        if resultado_madurez:
                            guardar_madurez(resultado_madurez)
                            st.success("✅ Nivel de madurez calculado y guardado")
                            st.rerun()
                        else:
                            st.error("❌ No se pudo calcular la madurez. Verifique que hay activos y respuestas.")
            else:
                # Si ya hay datos, mostrar botón de refrescar (solo lee, no recalcula)
                if st.button("🔃 Refrescar Vista", key="t5_refresh_madurez"):
                    st.rerun()
        
        st.divider()
        
        if madurez_data:
            if DASHBOARD_DISPONIBLE:
                render_madurez_completo(madurez_data)
            else:
                # Visualización básica sin componentes
                st.subheader(f"Nivel: {madurez_data.get('Nivel_Madurez', 1)} - {madurez_data.get('Nombre_Nivel', 'Inicial')}")
                st.metric("Puntuación Total", f"{madurez_data.get('Puntuacion_Total', 0):.0f}%")
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Organizacional", f"{madurez_data.get('Dominio_Organizacional', 0):.0f}%")
                col2.metric("Personas", f"{madurez_data.get('Dominio_Personas', 0):.0f}%")
                col3.metric("Físico", f"{madurez_data.get('Dominio_Fisico', 0):.0f}%")
                col4.metric("Tecnológico", f"{madurez_data.get('Dominio_Tecnologico', 0):.0f}%")
                
                st.divider()
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Controles Implementados", madurez_data.get('Controles_Implementados', 0))
                col2.metric("Controles Parciales", madurez_data.get('Controles_Parciales', 0))
                col3.metric("% Activos Evaluados", f"{madurez_data.get('Pct_Activos_Evaluados', 0):.0f}%")
        else:
            st.info("ℹ️ No hay datos de madurez calculados. Haz clic en el botón de arriba para calcular.")
            st.markdown("""
            **El nivel de madurez se calcula basándose en:**
            - % de controles ISO 27002 implementados (30%)
            - % de controles medidos/monitoreados (25%)
            - % de riesgos críticos/altos mitigados (25%)
            - % de activos evaluados correctamente (20%)
            
            **Niveles:**
            1. **Inicial** (0-20%): Procesos ad-hoc, sin controles formales
            2. **Básico** (20-40%): Controles básicos, documentación mínima
            3. **Definido** (40-60%): Procesos documentados, controles estandarizados
            4. **Gestionado** (60-80%): Controles medidos y monitoreados
            5. **Optimizado** (80-100%): Mejora continua, automatización
            """)
        
        st.divider()
        
        # Sección de controles existentes
        st.subheader("🛡️ Controles Existentes Identificados")
        
        controles_data = get_controles_existentes_detallados(st.session_state["eval_actual"])
        
        if DASHBOARD_DISPONIBLE and controles_data.get("controles"):
            render_controles_existentes(controles_data)
        elif controles_data.get("controles"):
            # Visualización básica
            resumen = controles_data.get("resumen", {})
            col1, col2, col3 = st.columns(3)
            col1.metric("✅ Implementados", resumen.get("implementados", 0))
            col2.metric("⚠️ Parciales", resumen.get("parciales", 0))
            col3.metric("❌ No Implementados", resumen.get("no_implementados", 0))
            
            st.write("**Controles identificados:**")
            for ctrl in controles_data.get("controles", [])[:20]:
                icono = "✅" if ctrl["efectividad"] >= 0.66 else "⚠️" if ctrl["efectividad"] > 0 else "❌"
                st.write(f"{icono} **{ctrl['codigo']}**: {ctrl['nombre']} - {ctrl['nivel']}")
        else:
            st.info("No hay controles identificados. Complete los cuestionarios primero.")


# ==================== TAB MATRIZ MAGERIT: VISTA CONSOLIDADA ====================
with tab_matriz:
    st.header("Matriz MAGERIT - Vista Tecnica")
    
    if not st.session_state.get("eval_actual"):
        st.error("EVALUACION REQUERIDA")
        st.warning("Ve a la pestana Evaluaciones y selecciona una evaluacion primero.")
    else:
        st.success(f"Evaluacion: **{st.session_state['eval_nombre']}**")
        
        # Obtener todos los resultados MAGERIT
        resumen_magerit = get_resumen_evaluacion(st.session_state["eval_actual"])
        
        if resumen_magerit.empty:
            st.info("No hay evaluaciones completadas. Ve al tab Evaluacion con IA para evaluar activos.")
        else:
            # ========== MATRIZ 5x5 VISUAL (NUEVO) ==========
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
                for ctrl in controles_list[:3]:  # Max 3 controles
                    if isinstance(ctrl, dict):
                        # Es un diccionario: extraer código o nombre
                        codigo = ctrl.get("codigo", ctrl.get("control", ctrl.get("nombre", "")))
                        if codigo:
                            resultado.append(str(codigo))
                    elif isinstance(ctrl, str):
                        resultado.append(ctrl)
                return ", ".join(resultado)
            
            # ========== CONSTRUIR MATRIZ MAGERIT COMPLETA ==========
            # Cada fila = relación ACTIVO-AMENAZA
            
            matriz_rows = []
            for _, row in resumen_magerit.iterrows():
                resultado = get_resultado_magerit(st.session_state["eval_actual"], row["id_activo"])
                if resultado and resultado.get("amenazas"):
                    for amenaza in resultado["amenazas"]:
                        # Extraer controles existentes y recomendados
                        ctrl_existentes = amenaza.get("controles_existentes", [])
                        ctrl_recomendados = amenaza.get("controles_recomendados", [])
                        
                        # Construir fila con todas las columnas requeridas
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
                    # Activo sin amenazas identificadas
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
                st.markdown("### 🔍 Filtros")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Filtrar por activo
                    activos_unicos = ["Todos"] + matriz_df["Activo"].unique().tolist()
                    filtro_activo = st.selectbox("Filtrar por Activo:", activos_unicos, key="magerit_filtro_activo")
                
                with col2:
                    # Filtrar por nivel de riesgo
                    niveles_riesgo = ["Todos", "CRÍTICO", "ALTO", "MEDIO", "BAJO", "MUY BAJO"]
                    filtro_nivel = st.selectbox("Filtrar por Nivel de Riesgo:", niveles_riesgo, key="magerit_filtro_nivel")
                
                with col3:
                    # Ordenar por
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
                st.markdown("### 📊 Resumen de la Matriz")
                col1, col2, col3, col4, col5 = st.columns(5)
                
                col1.metric("Total Registros", len(df_filtrado))
                col2.metric("Activos Únicos", df_filtrado["ID Activo"].nunique())
                col3.metric("Amenazas Únicas", len(df_filtrado[df_filtrado["Código Amenaza"] != "-"]))
                
                # Contar críticos y altos
                criticos = (df_filtrado["Nivel Riesgo"].str.upper().isin(["CRÍTICO", "CRITICO"])).sum()
                altos = (df_filtrado["Nivel Riesgo"].str.upper() == "ALTO").sum()
                col4.metric("🔴 Críticos", criticos)
                col5.metric("🟠 Altos", altos)
                
                st.divider()
                
                # ========== MATRIZ MAGERIT PRINCIPAL ==========
                st.markdown("### 📋 Matriz MAGERIT v3 - Relación Activo-Amenaza")
                
                # Crear mapeo de colores por activo para diferenciarlos visualmente
                activos_unicos_lista = df_filtrado["ID Activo"].unique().tolist()
                colores_activos = {}
                paleta_colores = [
                    "#E3F2FD",  # Azul muy claro
                    "#FFF3E0",  # Naranja muy claro
                    "#E8F5E9",  # Verde muy claro
                    "#F3E5F5",  # Púrpura muy claro
                    "#FFFDE7",  # Amarillo muy claro
                    "#E0F7FA",  # Cyan muy claro
                    "#FCE4EC",  # Rosa muy claro
                    "#EFEBE9",  # Marrón muy claro
                    "#F5F5F5",  # Gris muy claro
                    "#E8EAF6",  # Índigo muy claro
                ]
                for i, activo in enumerate(activos_unicos_lista):
                    colores_activos[activo] = paleta_colores[i % len(paleta_colores)]
                
                # Función para colorear nivel de riesgo
                def colorear_nivel_riesgo(val):
                    if pd.isna(val):
                        return ''
                    val_str = str(val).upper()
                    if val_str in ["CRÍTICO", "CRITICO"]:
                        return 'background-color: #FF4444; color: white; font-weight: bold'
                    elif val_str == "ALTO":
                        return 'background-color: #FF8C00; color: white; font-weight: bold'
                    elif val_str == "MEDIO":
                        return 'background-color: #FFD700; color: black'
                    elif val_str == "BAJO":
                        return 'background-color: #90EE90; color: black'
                    elif val_str == "MUY BAJO":
                        return 'background-color: #32CD32; color: white'
                    return ''
                
                # Función para colorear filas alternadas por activo
                def colorear_por_activo(row):
                    activo_id = row["ID Activo"]
                    color_fondo = colores_activos.get(activo_id, "#FFFFFF")
                    return [f'background-color: {color_fondo}' for _ in row]
                
                # Aplicar estilos: primero por activo, luego nivel de riesgo
                styled_matriz = df_filtrado.style.apply(
                    colorear_por_activo, axis=1
                ).applymap(
                    colorear_nivel_riesgo,
                    subset=["Nivel Riesgo"]
                )
                
                # Leyenda de colores por activo
                st.markdown("**🎨 Leyenda de Activos:**")
                num_cols = min(5, len(activos_unicos_lista))
                if num_cols > 0:
                    cols_leyenda = st.columns(num_cols)
                    for i, activo in enumerate(activos_unicos_lista[:10]):  # Mostrar máx 10
                        nombre_activo = df_filtrado[df_filtrado["ID Activo"] == activo]["Activo"].values[0]
                        nombre_corto = nombre_activo[:25] + "..." if len(nombre_activo) > 25 else nombre_activo
                        with cols_leyenda[i % num_cols]:
                            st.markdown(
                                f"<div style='background-color:{colores_activos[activo]}; padding:8px; border-radius:5px; margin:2px; font-size:11px; border-left: 4px solid #333;'>"
                                f"<b>{activo}</b><br/>{nombre_corto}</div>",
                                unsafe_allow_html=True
                            )
                
                st.write("")  # Espaciado
                
                # Mostrar matriz completa
                st.dataframe(
                    styled_matriz, 
                    use_container_width=True, 
                    hide_index=True, 
                    height=500
                )
                
                st.divider()
                
                # ========== EXPORTAR ==========
                st.markdown("### 📥 Exportar Matriz")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Exportar a Excel
                    if st.button("📊 Generar Excel Completo", key="magerit_exportar_excel"):
                        import io
                        
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            # Hoja principal - Matriz MAGERIT
                            df_filtrado.to_excel(writer, sheet_name='Matriz_MAGERIT', index=False)
                            
                            # Hoja resumen por activo
                            resumen_activos = df_filtrado.groupby(["ID Activo", "Activo"]).agg({
                                "Riesgo Inherente": "max",
                                "Riesgo Residual": "max",
                                "D": "first",
                                "I": "first",
                                "C": "first"
                            }).reset_index()
                            resumen_activos.to_excel(writer, sheet_name='Resumen_Activos', index=False)
                            
                            # Hoja de amenazas agrupadas
                            if len(df_filtrado[df_filtrado["Código Amenaza"] != "-"]) > 0:
                                amenazas_group = df_filtrado[df_filtrado["Código Amenaza"] != "-"].groupby(
                                    ["Código Amenaza", "Amenaza", "Tipo Amenaza"]
                                ).size().reset_index(name="Frecuencia")
                                amenazas_group = amenazas_group.sort_values("Frecuencia", ascending=False)
                                amenazas_group.to_excel(writer, sheet_name='Amenazas_Frecuencia', index=False)
                        
                        st.download_button(
                            "⬇️ Descargar Matriz MAGERIT (.xlsx)",
                            data=buffer.getvalue(),
                            file_name=f"Matriz_MAGERIT_{st.session_state['eval_actual']}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_magerit_excel"
                        )
                
                with col2:
                    # Exportar a CSV
                    csv_data = df_filtrado.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📄 Descargar CSV",
                        data=csv_data,
                        file_name=f"Matriz_MAGERIT_{st.session_state['eval_actual']}.csv",
                        mime="text/csv",
                        key="download_magerit_csv"
                    )
                
                # ========== INFORMACIÓN METODOLÓGICA MAGERIT ==========
                with st.expander("ℹ️ Información Metodológica MAGERIT v3"):
                    st.markdown("""
                    **Esta matriz sigue la metodología MAGERIT v3 del CCN-CERT (Ministerio de Hacienda, España)**
                    
                    ---
                    
                    ### 📋 Columnas de la Matriz
                    
                    | Columna | Descripción |
                    |---------|-------------|
                    | **D, I, C** | Impacto en Disponibilidad, Integridad y Confidencialidad (escala 1-5) |
                    | **Impacto** | Valor de impacto de la amenaza sobre el activo |
                    | **Probabilidad** | Frecuencia estimada de materialización (1-5) |
                    | **Riesgo Inherente** | Probabilidad × Impacto (sin considerar controles) |
                    | **Riesgo Residual** | Riesgo después de aplicar salvaguardas existentes |
                    | **Nivel Riesgo** | Clasificación: CRÍTICO, ALTO, MEDIO, BAJO, MUY BAJO |
                    | **Controles Existentes** | Salvaguardas ISO 27002 ya implementadas |
                    | **Salvaguardas** | Controles recomendados para mitigar el riesgo |
                    | **Efectividad** | Porcentaje de efectividad de controles actuales |
                    
                    ---
                    
                    ### 🎯 Criterios de Valoración MAGERIT
                    
                    **Escala de Impacto (D, I, C):**
                    | Valor | Nivel | Descripción |
                    |-------|-------|-------------|
                    | 5 | Muy Alto | Daño muy grave, pérdida irreparable |
                    | 4 | Alto | Daño grave, recuperación costosa |
                    | 3 | Medio | Daño importante, recuperación posible |
                    | 2 | Bajo | Daño menor, recuperación sencilla |
                    | 1 | Muy Bajo | Daño insignificante |
                    
                    **Escala de Probabilidad:**
                    | Valor | Frecuencia | Descripción |
                    |-------|------------|-------------|
                    | 5 | Muy frecuente | Diariamente o casi |
                    | 4 | Frecuente | Semanalmente |
                    | 3 | Normal | Mensualmente |
                    | 2 | Poco frecuente | Anualmente |
                    | 1 | Muy raro | Cada varios años |
                    
                    ---
                    
                    ### ⚠️ Clasificación de Amenazas MAGERIT
                    
                    | Código | Tipo | Descripción |
                    |--------|------|-------------|
                    | **[N]** | Naturales | Desastres naturales (fuego, inundación, terremotos) |
                    | **[I]** | Industriales | Fallos de origen industrial (eléctricos, climatización) |
                    | **[E]** | Errores | Errores humanos no intencionales |
                    | **[A]** | Ataques | Acciones deliberadas (malware, intrusión, robo) |
                    
                    ---
                    
                    ### 🛡️ Salvaguardas (Controles ISO 27002:2022)
                    
                    | Dominio | Código | Descripción |
                    |---------|--------|-------------|
                    | Organizacional | 5.x | Políticas, roles, gestión de activos |
                    | Personas | 6.x | Concienciación, formación, disciplina |
                    | Físico | 7.x | Perímetro, áreas seguras, equipos |
                    | Tecnológico | 8.x | Endpoint, red, cifrado, desarrollo |
                    
                    ---
                    
                    ### 📊 Niveles de Riesgo y Tratamiento
                    
                    | Nivel | Rango | Color | Tratamiento Sugerido |
                    |-------|-------|-------|---------------------|
                    | 🔴 **CRÍTICO** | ≥20 | Rojo | Acción inmediata, escalamiento a dirección |
                    | 🟠 **ALTO** | 15-19 | Naranja | Plan de tratamiento prioritario (<30 días) |
                    | 🟡 **MEDIO** | 10-14 | Amarillo | Seguimiento y controles adicionales |
                    | 🟢 **BAJO** | 5-9 | Verde claro | Aceptable con controles básicos |
                    | 🟢 **MUY BAJO** | <5 | Verde | Riesgo aceptable, monitoreo rutinario |
                    
                    ---
                    
                    ### 📖 Opciones de Tratamiento del Riesgo
                    
                    - **Mitigar**: Implementar salvaguardas para reducir probabilidad o impacto
                    - **Transferir**: Trasladar el riesgo a terceros (seguros, outsourcing)
                    - **Aceptar**: Asumir el riesgo conscientemente (documentado)
                    - **Evitar**: Eliminar la actividad que genera el riesgo
                    """)
            else:
                st.warning("No se pudieron generar datos para la matriz. Verifique que los activos tengan evaluación MAGERIT completada.")


# ==================== TAB IA AVANZADA: FUNCIONALIDADES INTELIGENTES ====================
with tab_ia_adv:
    if not IA_AVANZADA_DISPONIBLE:
        st.error("❌ El módulo de IA Avanzada no está disponible.")
    else:
        render_ia_avanzada_ui()


# ==================== TAB 6: COMPARATIVAS ====================
with tab6:
    st.header("🔄 Comparativas entre Evaluaciones")
    
    st.markdown("""
    Compara dos evaluaciones para identificar:
    - Cambios en el inventario de activos
    - Evolución de riesgos MAGERIT
    - Efectividad de controles implementados
    """)
    
    # Obtener todas las evaluaciones
    evaluaciones = get_evaluaciones()
    
    if len(evaluaciones) < 2:
        st.warning("⚠️ Necesitas al menos 2 evaluaciones para hacer comparativas")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            eval_1 = st.selectbox(
                "📋 Evaluación 1 (Anterior)",
                evaluaciones["ID_Evaluacion"].tolist(),
                key="t5_eval1"
            )
        
        with col2:
            eval_2 = st.selectbox(
                "📋 Evaluación 2 (Actual)",
                [e for e in evaluaciones["ID_Evaluacion"].tolist() if e != eval_1],
                key="t5_eval2"
            )
        
        if st.button("🔍 Comparar Evaluaciones MAGERIT", key="t5_comparar", type="primary"):
            # Cargar resúmenes MAGERIT
            resumen_1 = get_resumen_evaluacion(eval_1)
            resumen_2 = get_resumen_evaluacion(eval_2)
            
            activos_1 = get_activos_por_evaluacion(eval_1)
            activos_2 = get_activos_por_evaluacion(eval_2)
            
            st.markdown(f"### Comparativa: {eval_1} vs {eval_2}")
            
            # Comparar inventario
            st.markdown("#### 📦 Cambios en Inventario")
            col1, col2, col3 = st.columns(3)
            
            col1.metric("Activos Eval 1", len(activos_1))
            col2.metric("Activos Eval 2", len(activos_2))
            col3.metric("Diferencia", len(activos_2) - len(activos_1), delta=len(activos_2) - len(activos_1))
            
            # Activos nuevos/eliminados
            activos_1_ids = set(activos_1["Nombre_Activo"].tolist()) if not activos_1.empty else set()
            activos_2_ids = set(activos_2["Nombre_Activo"].tolist()) if not activos_2.empty else set()
            
            nuevos = activos_2_ids - activos_1_ids
            eliminados = activos_1_ids - activos_2_ids
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Activos Nuevos**")
                if nuevos:
                    for activo in nuevos:
                        st.success(f"➕ {activo}")
                else:
                    st.info("Sin cambios")
            
            with col2:
                st.markdown("**Activos Eliminados**")
                if eliminados:
                    for activo in eliminados:
                        st.error(f"➖ {activo}")
                else:
                    st.info("Sin cambios")
            
            # Comparar evaluaciones MAGERIT
            if not resumen_1.empty and not resumen_2.empty:
                st.markdown("#### 🎯 Evolución de Riesgos MAGERIT")
                
                col1, col2, col3 = st.columns(3)
                
                riesgo_prom_1 = resumen_1["riesgo_inherente_global"].mean()
                riesgo_prom_2 = resumen_2["riesgo_inherente_global"].mean()
                delta_riesgo = riesgo_prom_2 - riesgo_prom_1
                
                col1.metric("Riesgo Inherente Prom. Eval 1", f"{riesgo_prom_1:.1f}")
                col2.metric("Riesgo Inherente Prom. Eval 2", f"{riesgo_prom_2:.1f}")
                col3.metric("Cambio", f"{delta_riesgo:+.1f}", delta=f"{delta_riesgo:+.1f}")
                
                # Comparativo de riesgo residual
                col1, col2, col3 = st.columns(3)
                
                res_prom_1 = resumen_1["riesgo_residual_global"].mean()
                res_prom_2 = resumen_2["riesgo_residual_global"].mean()
                delta_res = res_prom_2 - res_prom_1
                
                col1.metric("Riesgo Residual Prom. Eval 1", f"{res_prom_1:.1f}")
                col2.metric("Riesgo Residual Prom. Eval 2", f"{res_prom_2:.1f}")
                col3.metric("Cambio", f"{delta_res:+.1f}", delta=f"{delta_res:+.1f}")
                
                # Gráfico comparativo
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name=f"{eval_1} - Inherente",
                    x=["Riesgo Promedio"],
                    y=[riesgo_prom_1],
                    marker_color="#FF6347"
                ))
                fig.add_trace(go.Bar(
                    name=f"{eval_2} - Inherente",
                    x=["Riesgo Promedio"],
                    y=[riesgo_prom_2],
                    marker_color="#FF9999"
                ))
                fig.add_trace(go.Bar(
                    name=f"{eval_1} - Residual",
                    x=["Riesgo Promedio"],
                    y=[res_prom_1],
                    marker_color="#32CD32"
                ))
                fig.add_trace(go.Bar(
                    name=f"{eval_2} - Residual",
                    x=["Riesgo Promedio"],
                    y=[res_prom_2],
                    marker_color="#90EE90"
                ))
                fig.update_layout(barmode='group', title="Comparativa de Riesgos entre Evaluaciones")
                st.plotly_chart(fig, use_container_width=True, key="t6_comparativa_riesgos")
                
                # Activos en común y su evolución
                st.markdown("#### 📊 Evolución de Activos en Común")
                
                activos_comunes = set(resumen_1["nombre_activo"].tolist()) & set(resumen_2["nombre_activo"].tolist())
                
                if activos_comunes:
                    evolucion_data = []
                    for nombre in activos_comunes:
                        r1 = resumen_1[resumen_1["nombre_activo"] == nombre].iloc[0]
                        r2 = resumen_2[resumen_2["nombre_activo"] == nombre].iloc[0]
                        
                        evolucion_data.append({
                            "Activo": nombre,
                            "R.Inh. Eval1": r1["riesgo_inherente_global"],
                            "R.Inh. Eval2": r2["riesgo_inherente_global"],
                            "Δ Inherente": r2["riesgo_inherente_global"] - r1["riesgo_inherente_global"],
                            "R.Res. Eval1": r1["riesgo_residual_global"],
                            "R.Res. Eval2": r2["riesgo_residual_global"],
                            "Δ Residual": r2["riesgo_residual_global"] - r1["riesgo_residual_global"]
                        })
                    
                    df_evolucion = pd.DataFrame(evolucion_data)
                    st.dataframe(df_evolucion, use_container_width=True, hide_index=True)
                else:
                    st.info("No hay activos en común entre las evaluaciones")
                
                # ====== SECCIÓN: CONTROLES IMPLEMENTADOS EN REEVALUACIÓN ======
                st.divider()
                st.markdown("#### 🛡️ Controles Implementados (Justificación de Mejora)")
                
                st.info("""
                📋 **Esta sección muestra los controles que fueron RECOMENDADOS en la evaluación anterior**
                y permite identificar cuáles se implementaron para justificar la reducción del riesgo.
                """)
                
                # Obtener amenazas con controles recomendados de Eval1
                if IA_AVANZADA_DISPONIBLE:
                    try:
                        amenazas_eval1 = obtener_amenazas_evaluacion(eval_1)
                        amenazas_eval2 = obtener_amenazas_evaluacion(eval_2)
                        
                        if not amenazas_eval1.empty:
                            # Extraer controles recomendados únicos de Eval1
                            controles_recomendados_eval1 = []
                            for _, row in amenazas_eval1.iterrows():
                                ctrls = row.get("controles_recomendados", [])
                                if isinstance(ctrls, str):
                                    try:
                                        ctrls = json.loads(ctrls)
                                    except:
                                        ctrls = []
                                for ctrl in ctrls:
                                    if isinstance(ctrl, dict):
                                        ctrl_info = {
                                            "codigo": ctrl.get("codigo", ""),
                                            "nombre": ctrl.get("nombre", ""),
                                            "prioridad": ctrl.get("prioridad", "MEDIA"),
                                            "amenaza": row.get("amenaza", ""),
                                            "activo": row.get("nombre_activo", "")
                                        }
                                        # Evitar duplicados
                                        if ctrl_info["codigo"] and ctrl_info not in controles_recomendados_eval1:
                                            controles_recomendados_eval1.append(ctrl_info)
                            
                            if controles_recomendados_eval1:
                                st.markdown(f"**📌 Controles recomendados en {eval_1} (evaluación anterior):**")
                                
                                # Extraer controles existentes de Eval2 (los que SÍ se implementaron)
                                controles_existentes_eval2 = set()
                                for _, row in amenazas_eval2.iterrows():
                                    ctrls_exist = row.get("controles_existentes", [])
                                    if isinstance(ctrls_exist, str):
                                        ctrls_exist = [c.strip() for c in ctrls_exist.split(",") if c.strip()]
                                    elif isinstance(ctrls_exist, list):
                                        pass
                                    for c in ctrls_exist:
                                        if isinstance(c, str):
                                            controles_existentes_eval2.add(c)
                                        elif isinstance(c, dict):
                                            controles_existentes_eval2.add(c.get("codigo", ""))
                                
                                # Mostrar tabla de controles con estado de implementación
                                tabla_controles = []
                                for ctrl in controles_recomendados_eval1:
                                    implementado = ctrl["codigo"] in controles_existentes_eval2
                                    tabla_controles.append({
                                        "Código": ctrl["codigo"],
                                        "Control": ctrl["nombre"],
                                        "Prioridad": ctrl["prioridad"],
                                        "Amenaza": ctrl["amenaza"],
                                        "Activo": ctrl["activo"],
                                        "Estado": "✅ IMPLEMENTADO" if implementado else "⏳ Pendiente"
                                    })
                                
                                df_controles = pd.DataFrame(tabla_controles)
                                
                                # Resumen
                                total_recomendados = len(tabla_controles)
                                implementados = len([c for c in tabla_controles if "IMPLEMENTADO" in c["Estado"]])
                                pct_implementados = (implementados / total_recomendados * 100) if total_recomendados > 0 else 0
                                
                                col1, col2, col3 = st.columns(3)
                                col1.metric("Controles Recomendados", total_recomendados)
                                col2.metric("Implementados", implementados)
                                col3.metric("% Cumplimiento", f"{pct_implementados:.0f}%")
                                
                                # Mostrar dataframe con colores
                                st.dataframe(
                                    df_controles.style.apply(
                                        lambda row: [
                                            'background-color: #c8e6c9' if 'IMPLEMENTADO' in str(row['Estado']) else 'background-color: #fff9c4'
                                            for _ in row
                                        ], axis=1
                                    ),
                                    use_container_width=True,
                                    hide_index=True
                                )
                                
                                # Justificación de la reducción de riesgo
                                if implementados > 0 and delta_res < 0:
                                    st.success(f"""
                                    ✅ **Justificación de mejora:**  
                                    Se implementaron **{implementados}** de {total_recomendados} controles recomendados ({pct_implementados:.0f}%),  
                                    lo cual contribuyó a reducir el riesgo residual promedio en **{abs(delta_res):.1f}** puntos.
                                    """)
                                elif implementados == 0:
                                    st.warning("""
                                    ⚠️ **Nota:** No se detectaron controles implementados de los recomendados.  
                                    La reducción de riesgo puede deberse a otros factores o ajustes en la valoración.
                                    """)
                            else:
                                st.info(f"No se encontraron controles recomendados en {eval_1}")
                        else:
                            st.info(f"No hay datos de amenazas para {eval_1}")
                    except Exception as e:
                        st.warning(f"No se pudo cargar información de controles: {e}")
                else:
                    st.info("Módulo IA Avanzada no disponible para análisis de controles")
            
            else:
                st.info("Una o ambas evaluaciones no tienen resultados MAGERIT")
            
            # Comparativa de Madurez
            st.divider()
            st.markdown("#### 🎯 Comparativa de Nivel de Madurez")
            
            comparativa_madurez = comparar_madurez(eval_1, eval_2)
            
            if comparativa_madurez:
                if DASHBOARD_DISPONIBLE:
                    render_comparativa_madurez(comparativa_madurez)
                else:
                    # Visualización básica
                    st.info(comparativa_madurez.get("mensaje_resumen", ""))
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Δ Puntuación", f"{comparativa_madurez.get('delta_puntuacion', 0):+.1f}%")
                    col2.metric("Δ Nivel", comparativa_madurez.get('delta_nivel', 0))
                    col3.metric("Δ Riesgo Residual", f"{comparativa_madurez.get('delta_riesgo_residual', 0):+.1f}")
                    
                    # Mejoras
                    mejoras = comparativa_madurez.get("mejoras", [])
                    if mejoras:
                        st.write("**✅ Mejoras:**")
                        for m in mejoras:
                            st.success(m)
                    
                    # Retrocesos
                    retrocesos = comparativa_madurez.get("retrocesos", [])
                    if retrocesos:
                        st.write("**⚠️ Retrocesos:**")
                        for r in retrocesos:
                            st.error(r)
                    
                    # Recomendaciones
                    recomendaciones = comparativa_madurez.get("recomendaciones", [])
                    if recomendaciones:
                        st.write("**💡 Recomendaciones:**")
                        for rec in recomendaciones:
                            st.write(f"• {rec}")
            else:
                st.info("No hay datos de madurez para comparar. Calcule la madurez en el tab 🎯 Madurez primero.")


# ==================== TAB IA: VALIDACIÓN DE IA LOCAL (AL FINAL) ====================
with tab_ia:
    st.header("🛡️ Validación y Preparación de IA Local")
    
    try:
        # Importar directamente las funciones necesarias
        from services.ia_validation_service import obtener_estado_ia, verificar_ollama_local
        from services.knowledge_base_service import obtener_resumen_catalogos
        
        st.markdown("""
        Este módulo valida que la IA funciona **100% local** con Ollama y sin conexión a Internet.
        """)
        
        # Dividir en columnas
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔍 Estado Actual")
            ia_ready, last_validation, canary_nonce = obtener_estado_ia()
            
            if ia_ready:
                st.success("✅ IA Validada y Lista")
                st.info(f"Última validación: {last_validation}")
            else:
                st.warning("⚠️ IA No Validada - Ejecute validación")
            
            # Verificar Ollama
            st.subheader("🖥️ Ollama Local")
            is_local, endpoint, modelos, error = verificar_ollama_local()
            
            if is_local:
                st.success(f"✅ Conectado: {endpoint}")
                st.caption(f"Modelos: {', '.join(modelos[:5])}")
            else:
                st.error(f"❌ No conectado: {error}")
        
        with col2:
            st.subheader("📚 Knowledge Base")
            resumen = obtener_resumen_catalogos()
            
            st.metric("Amenazas MAGERIT", resumen["total_amenazas"])
            st.metric("Controles ISO 27002", resumen["total_controles"])
            
            if resumen["total_amenazas"] >= 50 and resumen["total_controles"] >= 90:
                st.success("✅ Catálogos cargados correctamente")
            else:
                st.warning("⚠️ Catálogos incompletos")
        
        st.divider()
        
        # Botón de validación
        if VALIDACION_IA_DISPONIBLE:
            from services.ia_validation_service import ejecutar_validacion_completa
            if st.button("🔄 Ejecutar Validación Completa", type="primary", key="btn_validar_ia"):
                with st.spinner("Ejecutando validación..."):
                    resultado = ejecutar_validacion_completa()
                    if resultado.ia_ready:
                        st.success("✅ IA VALIDADA Y LISTA")
                    else:
                        st.error("❌ Validación fallida")
                        for err in resultado.errors:
                            st.write(f"- {err}")
                    st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error: {e}")
        import traceback
        st.code(traceback.format_exc())


# Footer
st.divider()
st.caption("🛡️ Proyecto TITA v3.0 - Motor MAGERIT v3 + ISO 27002:2022 | 52 Amenazas | 93 Controles | Madurez CMMI")
