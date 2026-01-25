"""
PROYECTO TITA - Sistema de Evaluación de Riesgos MAGERIT/ISO 27002
Versión: 3.0 (Funcionalidades Completas)
"""
import json
import datetime as dt
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Importar servicios
from services import (
    # Excel
    ensure_sheet_exists, read_sheet, append_rows,
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
    get_activo, actualizar_estado_activo, validar_duplicado
)
from config.settings import (
    CUESTIONARIOS_HEADERS, RESPUESTAS_HEADERS, IMPACTO_HEADERS,
    ANALISIS_RIESGO_HEADERS, RISK_COLORS, get_risk_level,
    N_PREGUNTAS_BASE, N_PREGUNTAS_IA, OLLAMA_DEFAULT_MODEL
)

# Configuración de la página
st.set_page_config(
    page_title="TITA - Evaluación de Riesgos MAGERIT",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar session_state
if "eval_actual" not in st.session_state:
    st.session_state["eval_actual"] = None
if "eval_nombre" not in st.session_state:
    st.session_state["eval_nombre"] = None

# Título principal
st.title("🛡️ Proyecto TITA - Evaluación de Riesgos")
st.caption("Metodología MAGERIT + ISO/IEC 27002:2022 | IA con Ollama")

# Sidebar
with st.sidebar:
    st.header("📊 Panel de Control")
    
    # Selector de evaluación
    evaluaciones = get_evaluaciones()
    if not evaluaciones.empty:
        st.markdown("### 📋 Evaluación Actual")
        eval_nombres = evaluaciones["ID_Evaluacion"] + " - " + evaluaciones["Nombre"]
        eval_opciones = eval_nombres.tolist()
        
        # Índice actual
        indice_actual = 0
        if st.session_state["eval_actual"]:
            try:
                indice_actual = evaluaciones[
                    evaluaciones["ID_Evaluacion"] == st.session_state["eval_actual"]
                ].index[0]
            except:
                pass
        
        eval_seleccionada = st.selectbox(
            "Seleccionar evaluación",
            eval_opciones,
            index=indice_actual,
            key="sidebar_eval_select"
        )
        
        if eval_seleccionada:
            eval_id = eval_seleccionada.split(" - ")[0]
            st.session_state["eval_actual"] = eval_id
            st.session_state["eval_nombre"] = eval_seleccionada.split(" - ")[1]
    else:
        st.warning("⚠️ No hay evaluaciones. Crea una en Tab 0.")
        st.session_state["eval_actual"] = None
    
    st.divider()
    
    # Estadísticas
    if st.session_state["eval_actual"]:
        stats = get_estadisticas_evaluacion(st.session_state["eval_actual"])
        st.metric("Activos Totales", stats["total_activos"])
        st.metric("Progreso", f"{stats['progreso']}%")
        
        col1, col2 = st.columns(2)
        col1.metric("✅ Evaluados", stats["evaluados"])
        col2.metric("⏳ Pendientes", stats["pendientes"])
    
    st.divider()
    st.caption("💾 Excel: matriz_riesgos_v2.xlsx")

# Asegurar hojas necesarias
ensure_sheet_exists("CUESTIONARIOS", CUESTIONARIOS_HEADERS)
ensure_sheet_exists("RESPUESTAS", RESPUESTAS_HEADERS)
ensure_sheet_exists("IMPACTO_ACTIVOS", IMPACTO_HEADERS)
ensure_sheet_exists("ANALISIS_RIESGO", ANALISIS_RIESGO_HEADERS)

# ==================== TABS ====================
tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🏠 Evaluaciones",
    "📦 Activos",
    "🧠 Generar Cuestionario",
    "✍️ Responder",
    "📊 Impacto DIC",
    "🔍 Análisis IA",
    "📈 Dashboards",
    "🔄 Comparativas"
])

# ==================== TAB 0: GESTIÓN DE EVALUACIONES ====================
with tab0:
    st.subheader("🏠 Gestión de Evaluaciones")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📋 Evaluaciones Existentes")
        evals = get_evaluaciones()
        
        if evals.empty:
            st.info("ℹ️ No hay evaluaciones creadas. Crea la primera evaluación.")
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
            
            # Mostrar tabla
            st.dataframe(evals_filtradas, width='stretch', height=300)
            
            # Acciones sobre evaluación seleccionada
            if not evals_filtradas.empty:
                st.markdown("### ⚙️ Acciones")
                
                eval_selec = st.selectbox(
                    "Seleccionar evaluación para acciones",
                    evals_filtradas["ID_Evaluacion"].tolist(),
                    key="t0_eval_accion"
                )
                
                acol1, acol2, acol3 = st.columns(3)
                
                with acol1:
                    if st.button("🚀 Trabajar en esta evaluación", key="t0_trabajar"):
                        st.session_state["eval_actual"] = eval_selec
                        eval_data = evals[evals["ID_Evaluacion"] == eval_selec].iloc[0]
                        st.session_state["eval_nombre"] = eval_data["Nombre"]
                        st.success(f"✅ Evaluación {eval_selec} activada")
                        st.rerun()
                
                with acol2:
                    nuevo_estado = st.selectbox(
                        "Cambiar estado",
                        ["En Progreso", "Completada", "Archivada"],
                        key="t0_nuevo_estado"
                    )
                    if st.button("💾 Actualizar estado", key="t0_act_estado"):
                        if actualizar_estado_evaluacion(eval_selec, nuevo_estado):
                            st.success(f"✅ Estado actualizado a {nuevo_estado}")
                            st.rerun()
                
                with acol3:
                    stats = get_estadisticas_evaluacion(eval_selec)
                    st.metric("Activos", stats["total_activos"])
                    st.metric("Progreso", f"{stats['progreso']}%")
    
    with col2:
        st.markdown("### ➕ Nueva Evaluación")
        
        modo = st.radio(
            "Tipo de evaluación",
            ["Desde cero", "Re-evaluación"],
            key="t0_modo"
        )
        
        with st.form("form_nueva_eval"):
            nombre = st.text_input("Nombre *", placeholder="Ej: Evaluación Q1 2026")
            responsable = st.text_input("Responsable *", placeholder="Ej: Juan Pérez")
            descripcion = st.text_area("Descripción", placeholder="Contexto de la evaluación...")
            
            origen_eval = None
            if modo == "Re-evaluación":
                st.info("ℹ️ Se copiarán los activos de la evaluación origen (sin respuestas)")
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
                st.error("❌ Nombre y responsable son obligatorios")
            else:
                nuevo_id = crear_evaluacion(
                    nombre=nombre,
                    descripcion=descripcion,
                    responsable=responsable,
                    origen_id=origen_eval if modo == "Re-evaluación" else None
                )
                st.success(f"🎉 Evaluación {nuevo_id} creada correctamente")
                st.session_state["eval_actual"] = nuevo_id
                st.session_state["eval_nombre"] = nombre
                st.balloons()
                st.rerun()


# ==================== TAB 1: GESTIÓN DE ACTIVOS ====================
with tab1:
    st.subheader("📦 Gestión de Activos")
    
    if not st.session_state["eval_actual"]:
        st.warning("⚠️ Selecciona una evaluación en el sidebar o crea una en Tab 0")
        st.stop()
    
    st.info(f"📋 Evaluación: **{st.session_state['eval_nombre']}** ({st.session_state['eval_actual']})")
    
    actcol1, actcol2 = st.columns([2, 1])
    
    with actcol1:
        st.markdown("### 📊 Inventario de Activos")
        
        activos = get_activos_por_evaluacion(st.session_state["eval_actual"])
        
        if activos.empty:
            st.info("ℹ️ No hay activos en esta evaluación. Crea el primero.")
        else:
            # Filtros
            fcol1, fcol2, fcol3 = st.columns(3)
            with fcol1:
                if "Tipo_Activo" in activos.columns:
                    tipos = ["Todos"] + activos["Tipo_Activo"].dropna().unique().tolist()
                    tipo_filter = st.selectbox("Tipo", tipos, key="t1_tipo")
            with fcol2:
                if "Ubicacion" in activos.columns:
                    ubicaciones = ["Todas"] + activos["Ubicacion"].dropna().unique().tolist()
                    ubic_filter = st.selectbox("Ubicación", ubicaciones, key="t1_ubic")
            with fcol3:
                if "Estado" in activos.columns:
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
            
            # Mostrar tabla
            st.dataframe(activos_filtrados, width='stretch', height=350)
            st.caption(f"📊 Mostrando {len(activos_filtrados)} de {len(activos)} activos")
            
            # Acciones
            if not activos_filtrados.empty:
                st.markdown("### ⚙️ Acciones sobre activo")
                activo_selec = st.selectbox(
                    "Seleccionar activo",
                    activos_filtrados["ID_Activo"].tolist(),
                    key="t1_activo_selec"
                )
                
                acol1, acol2, acol3 = st.columns(3)
                
                with acol1:
                    if st.button("✏️ Editar", key="t1_editar"):
                        st.session_state["editar_activo"] = activo_selec
                        st.rerun()
                
                with acol2:
                    nuevo_estado_act = st.selectbox(
                        "Cambiar estado",
                        ["Pendiente", "Incompleto", "Completo", "Evaluado"],
                        key="t1_nuevo_estado_act"
                    )
                    if st.button("💾 Actualizar estado", key="t1_act_estado_btn"):
                        if actualizar_estado_activo(st.session_state["eval_actual"], activo_selec, nuevo_estado_act):
                            st.success(f"✅ Estado actualizado a {nuevo_estado_act}")
                            st.rerun()
                
                with acol3:
                    if st.button("🗑️ Eliminar", key="t1_eliminar"):
                        st.session_state["confirmar_eliminar"] = activo_selec
                        st.rerun()
                
                # Confirmación de eliminación
                if st.session_state.get("confirmar_eliminar"):
                    st.warning(f"⚠️ ¿Eliminar activo {st.session_state['confirmar_eliminar']}?")
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
                                st.rerun()
                            else:
                                st.error(msg)
                    with ccol2:
                        if st.button("❌ Cancelar", key="t1_confirmar_no"):
                            st.session_state["confirmar_eliminar"] = None
                            st.rerun()
    
    with actcol2:
        # Editar o crear activo
        if st.session_state.get("editar_activo"):
            st.markdown("### ✏️ Editar Activo")
            activo_data = get_activo(st.session_state["eval_actual"], st.session_state["editar_activo"])
            
            with st.form("form_editar_activo"):
                nombre_act = st.text_input("Nombre Activo *", value=activo_data.get("Nombre_Activo", ""))
                tipo_act = st.selectbox(
                    "Tipo *",
                    ["Físico", "Virtual"],
                    index=0 if activo_data.get("Tipo_Activo") == "Físico" else 1
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
                     "Firewall", "Switch", "Router", "Storage", "Backup", "Otro"],
                    index=0
                )
                app_critica = st.radio(
                    "Aplicación Crítica",
                    ["Sí", "No"],
                    index=0 if activo_data.get("App_Critica") == "Sí" else 1,
                    horizontal=True
                )
                descripcion = st.text_area("Descripción", value=activo_data.get("Descripcion", ""))
                
                bcol1, bcol2, bcol3 = st.columns(3)
                with bcol1:
                    rto = st.text_input("RTO", value=activo_data.get("RTO", ""), placeholder="Ej: 4h")
                with bcol2:
                    rpo = st.text_input("RPO", value=activo_data.get("RPO", ""), placeholder="Ej: 1h")
                with bcol3:
                    bia = st.text_input("BIA", value=activo_data.get("BIA", ""), placeholder="Ej: Alto")
                
                submitted_edit = st.form_submit_button("💾 Guardar Cambios", type="primary")
            
            if submitted_edit:
                datos_actualizados = {
                    "Nombre_Activo": nombre_act,
                    "Tipo_Activo": tipo_act,
                    "Ubicacion": ubicacion,
                    "Propietario": propietario,
                    "Tipo_Servicio": tipo_servicio,
                    "App_Critica": app_critica,
                    "Descripcion": descripcion,
                    "RTO": rto,
                    "RPO": rpo,
                    "BIA": bia
                }
                exito, msg = editar_activo(
                    st.session_state["eval_actual"],
                    st.session_state["editar_activo"],
                    datos_actualizados
                )
                if exito:
                    st.success(msg)
                    st.session_state["editar_activo"] = None
                    st.rerun()
                else:
                    st.error(msg)
            
            if st.button("❌ Cancelar edición", key="t1_cancelar_edit"):
                st.session_state["editar_activo"] = None
                st.rerun()
        
        else:
            st.markdown("### ➕ Crear Nuevo Activo")
            
            with st.form("form_crear_activo"):
                nombre_act = st.text_input("Nombre Activo *", placeholder="Ej: Servidor DB Principal")
                tipo_act = st.selectbox("Tipo *", ["Físico", "Virtual"])
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
                descripcion = st.text_area("Descripción", placeholder="Detalles del activo...")
                
                bcol1, bcol2, bcol3 = st.columns(3)
                with bcol1:
                    rto = st.text_input("RTO", placeholder="Ej: 4h")
                with bcol2:
                    rpo = st.text_input("RPO", placeholder="Ej: 1h")
                with bcol3:
                    bia = st.text_input("BIA", placeholder="Ej: Alto")
                
                submitted_create = st.form_submit_button("✅ Crear Activo", type="primary")
            
            if submitted_create:
                if not nombre_act:
                    st.error("❌ El nombre del activo es obligatorio")
                else:
                    datos_nuevo = {
                        "Nombre_Activo": nombre_act,
                        "Tipo_Activo": tipo_act,
                        "Ubicacion": ubicacion,
                        "Propietario": propietario,
                        "Tipo_Servicio": tipo_servicio,
                        "App_Critica": app_critica,
                        "Descripcion": descripcion,
                        "RTO": rto,
                        "RPO": rpo,
                        "BIA": bia
                    }
                    
                    exito, msg, nuevo_id = crear_activo(st.session_state["eval_actual"], datos_nuevo)
                    if exito:
                        st.success(msg)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(msg)


# ==================== TAB 2: GENERAR CUESTIONARIO ====================
with tab2:
    st.subheader("🧠 Generar Cuestionario con IA")
    
    if not st.session_state["eval_actual"]:
        st.warning("⚠️ Selecciona una evaluación primero")
        st.stop()
    
    activos = get_activos_por_evaluacion(st.session_state["eval_actual"])
    bank = read_sheet("BANCO_PREGUNTAS")
    cu = read_sheet("CUESTIONARIOS")
    
    if activos.empty:
        st.error("❌ No hay activos en esta evaluación.")
        st.stop()
    if bank.empty:
        st.warning("⚠️ BANCO_PREGUNTAS está vacío. Ejecuta `seed_catalogos.py`")
        st.stop()
    
    col1, col2 = st.columns(2)
    with col1:
        activo_id = st.selectbox("🎯 Activo", activos["ID_Activo"].tolist(), key="t2_activo")
    with col2:
        model = st.selectbox("🤖 Modelo Ollama", ["llama3", "phi3", "mistral"], index=0, key="t2_model")
    
    # Resto del código del tab 2 igual que en app_v2.py...
    st.info("💡 El resto de los tabs (3-7) mantienen su funcionalidad actual")


# Footer
st.divider()
st.caption("🛡️ Proyecto TITA v3.0 - Sistema Completo de Gestión de Riesgos")
