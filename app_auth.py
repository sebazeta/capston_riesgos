"""
PROYECTO TITA - Sistema de Evaluación de Riesgos MAGERIT/ISO 27002
Versión: 2.0 (Con Autenticación)
"""
import json
import datetime as dt
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# NOTA: Para habilitar autenticación, instala: pip install streamlit-authenticator pyyaml
# Descomentar estas líneas cuando se instale la dependencia:
# import streamlit_authenticator as stauth
# from config.auth_config import get_auth_config, has_permission
# from utils.auth_helpers import check_permission, render_user_badge

# Importar servicios
from services import (
    ensure_sheet_exists, read_sheet, append_rows,
    set_eval_active, update_cuestionarios_version,
    ollama_generate, ollama_analyze_risk,
    extract_json_array, validate_ia_questions
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

# ==================== AUTENTICACIÓN ====================
# DESCOMENTAR ESTE BLOQUE CUANDO SE INSTALE streamlit-authenticator
"""
auth_config = get_auth_config()
authenticator = stauth.Authenticate(
    auth_config['credentials'],
    auth_config['cookie']['name'],
    auth_config['cookie']['key'],
    auth_config['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status == False:
    st.error('❌ Usuario/contraseña incorrectos')
    st.stop()
elif authentication_status == None:
    st.warning('🔒 Por favor ingresa tus credenciales')
    st.info('**Usuarios demo:** admin/admin123 | analista/analista123 | auditor/auditor123')
    st.stop()

# Usuario autenticado - guardar rol
if 'role' not in st.session_state:
    user_data = auth_config['credentials']['usernames'].get(username, {})
    st.session_state['role'] = user_data.get('role', 'auditor')
"""

# Título principal
st.title("🛡️ Proyecto TITA - Evaluación de Riesgos")
st.caption("Metodología MAGERIT + ISO/IEC 27002:2022 | IA con Ollama")

# Sidebar
with st.sidebar:
    # DESCOMENTAR cuando se habilite auth:
    # render_user_badge()
    # authenticator.logout('Cerrar Sesión', 'sidebar')
    # st.divider()
    
    st.header("📊 Panel de Control")
    st.info("💾 Excel: matriz_riesgos_v2.xlsx")
    st.divider()
    
    # Métricas rápidas
    try:
        evals = read_sheet("EVALUACIONES")
        activos = read_sheet("INVENTARIO_ACTIVOS")
        st.metric("Evaluaciones", len(evals) if not evals.empty else 0)
        st.metric("Activos", len(activos) if not activos.empty else 0)
    except:
        pass

# Asegurar que existen las hojas necesarias
ensure_sheet_exists("CUESTIONARIOS", CUESTIONARIOS_HEADERS)
ensure_sheet_exists("RESPUESTAS", RESPUESTAS_HEADERS)
ensure_sheet_exists("IMPACTO_ACTIVOS", IMPACTO_HEADERS)
ensure_sheet_exists("ANALISIS_RIESGO", ANALISIS_RIESGO_HEADERS)

# Fallback para preguntas IA
FALLBACK_JSON = """
[
  {"Pregunta":"¿El sistema cuenta con redundancia que permita cumplir el RTO objetivo del activo?","Tipo_Respuesta":"1-5","Peso":4,"Dimension":"D"},
  {"Pregunta":"¿Los respaldos y replicación permiten minimizar la pérdida de datos dentro del umbral esperado?","Tipo_Respuesta":"1-5","Peso":4,"Dimension":"I"},
  {"Pregunta":"¿Hay controles para mantener la confidencialidad de datos durante contingencia y restauración?","Tipo_Respuesta":"1-5","Peso":3,"Dimension":"C"}
]
"""

# ==================== TABS ====================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📦 Inventario",
    "🧠 Generar Cuestionario",
    "✍️ Responder",
    "📊 Impacto DIC",
    "🔍 Análisis de Riesgos IA",
    "📈 Dashboards",
    "🔄 Comparativas"
])

# ==================== TAB 1: INVENTARIO ====================
with tab1:
    st.subheader("📦 Inventario de Activos Críticos")
    
    inv = read_sheet("INVENTARIO_ACTIVOS")
    if inv.empty:
        st.warning("⚠️ No hay activos registrados.")
        st.info("💡 Crea activos manualmente en la hoja `INVENTARIO_ACTIVOS` del archivo Excel.")
    else:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            if "Tipo_Activo" in inv.columns:
                tipos = ["Todos"] + inv["Tipo_Activo"].dropna().unique().tolist()
                tipo_filter = st.selectbox("Filtrar por tipo", tipos)
        with col2:
            if "Ubicacion" in inv.columns:
                ubicaciones = ["Todas"] + inv["Ubicacion"].dropna().unique().tolist()
                ubic_filter = st.selectbox("Filtrar por ubicación", ubicaciones)
        
        # Aplicar filtros
        inv_filtered = inv.copy()
        if tipo_filter != "Todos":
            inv_filtered = inv_filtered[inv_filtered["Tipo_Activo"] == tipo_filter]
        if ubic_filter != "Todas":
            inv_filtered = inv_filtered[inv_filtered["Ubicacion"] == ubic_filter]
        
        st.dataframe(inv_filtered, width='stretch', height=400)
        st.caption(f"📊 Mostrando {len(inv_filtered)} de {len(inv)} activos")


# ==================== TAB 2: GENERAR CUESTIONARIO ====================
with tab2:
    st.subheader("🧠 Generar Cuestionario con IA")
    
    # DESCOMENTAR para verificar permisos:
    # if not check_permission('can_generate_ia'):
    #     st.error("⛔ No tienes permisos para generar cuestionarios con IA")
    #     st.stop()
    
    inv = read_sheet("INVENTARIO_ACTIVOS")
    bank = read_sheet("BANCO_PREGUNTAS")
    cu = read_sheet("CUESTIONARIOS")
    
    if inv.empty:
        st.error("❌ No hay activos en INVENTARIO_ACTIVOS.")
        st.stop()
    if bank.empty:
        st.warning("⚠️ BANCO_PREGUNTAS está vacío. Ejecuta `seed_catalogos.py`")
        st.stop()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        activo_id = st.selectbox("🎯 Activo", inv["ID_Activo"].tolist(), key="t2_activo")
    with col2:
        eval_id = st.text_input("🆔 ID Evaluación", value="EVA-001", key="t2_eval_id")
    with col3:
        model = st.selectbox("🤖 Modelo Ollama", ["llama3", "phi3", "mistral"], index=0, key="t2_model")
    
    eval_name = st.text_input("📝 Nombre Evaluación", value="Evaluación desde GUI", key="t2_eval_name")
    
    cu_act = cu[
        (cu["ID_Evaluacion"].astype(str) == str(eval_id)) &
        (cu["ID_Activo"].astype(str) == str(activo_id))
    ].copy() if not cu.empty else pd.DataFrame()
    
    versiones = sorted(cu_act["Fecha"].dropna().astype(str).unique().tolist()) if (not cu_act.empty and "Fecha" in cu_act.columns) else []
    ultima_version = versiones[-1] if versiones else None
    
    st.markdown("### 📌 Estado del cuestionario")
    box1, box2, box3 = st.columns(3)
    box1.metric("Versiones totales", len(versiones))
    box2.metric("Última versión", ultima_version if ultima_version else "—")
    box3.metric("Preguntas en última", int(len(cu_act[cu_act["Fecha"].astype(str) == str(ultima_version)])) if ultima_version else 0)
    
    st.divider()
    
    if not versiones:
        opciones = ["Generar primera versión"]
    else:
        opciones = ["Usar la última versión (no generar)", "Generar nueva versión (crear otra Fecha)"]
    
    accion = st.radio("¿Qué hacer?", opciones, index=0, key="t2_accion")
    
    if st.button("🚀 Ejecutar", key="t2_btn_run", type="primary"):
        if "Usar la última versión" in accion:
            st.session_state["go_to_tab3"] = True
            st.session_state["resp_eval"] = str(eval_id)
            st.session_state["resp_act"] = str(activo_id)
            st.session_state["resp_fecha"] = str(ultima_version)
            
            st.success(f"✅ Usarás la versión existente: **{ultima_version}**")
            st.info("👉 Ve a **Tab 3 (Responder)** para completar el cuestionario.")
            st.rerun()
        
        # Generar nueva versión
        fecha_version = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        arow = inv[inv["ID_Activo"].astype(str) == str(activo_id)].iloc[0].to_dict()
        tipo = str(arow.get("Tipo_Activo", "General")).lower()
        
        # Preguntas base
        b = bank.copy()
        b["Tipo_Activo"] = b.get("Tipo_Activo", "").fillna("").astype(str)
        match = b[b["Tipo_Activo"].str.lower() == tipo]
        base_sel = match.head(N_PREGUNTAS_BASE)
        
        if len(base_sel) < N_PREGUNTAS_BASE:
            base_sel = pd.concat(
                [base_sel, b[~b.index.isin(base_sel.index)].head(N_PREGUNTAS_BASE - len(base_sel))],
                ignore_index=True
            )
        
        base_rows = []
        for _, r in base_sel.iterrows():
            base_rows.append({
                "ID_Evaluacion": str(eval_id),
                "ID_Activo": str(activo_id),
                "Fecha": fecha_version,
                "ID_Pregunta": str(r.get("ID_Pregunta", f"P-{dt.datetime.now().strftime('%H%M%S')}")),
                "Pregunta": str(r.get("Pregunta", "")),
                "Tipo_Respuesta": str(r.get("Tipo_Respuesta(0/1|1-5)", "0/1")).replace(" ", ""),
                "Peso": int(r.get("Peso(1-5)", 3)),
                "Dimension": str(r.get("Dimension", "I")).strip().upper() if "Dimension" in r else "I",
                "Fuente(IA/Base)": "Base"
            })
        
        # Preguntas IA
        prompt = f"""
Devuelve SOLO un JSON válido. NO texto adicional.
Genera EXACTAMENTE {N_PREGUNTAS_IA} preguntas TÉCNICAS para continuidad (RTO/RPO/BIA):
- arquitectura, HA, redundancia, backups, replicación, dependencias, restauración, pruebas.
- NO preguntes literalmente "¿Cuál es el RTO/RPO?".
Formato obligatorio:
[
  {{
    "Pregunta": "texto",
    "Tipo_Respuesta": "0/1" o "1-5",
    "Peso": 1-5,
    "Dimension": "D" o "I" o "C"
  }}
]
Contexto: {json.dumps(arow, ensure_ascii=False)}
"""
        
        with st.spinner("🧠 Ollama generando preguntas..."):
            raw = ollama_generate(model, prompt)
        
        if raw == "__TIMEOUT__" or (isinstance(raw, str) and raw.startswith("__ERROR__")):
            st.error("⚠️ Ollama falló. Usando fallback.")
            raw = FALLBACK_JSON
        
        with st.expander("🔍 Ver respuesta cruda (debug)"):
            st.code(raw, language="json")
        
        parsed = extract_json_array(raw)
        ia_valid = validate_ia_questions(parsed, n_ia=N_PREGUNTAS_IA)
        st.success(f"✅ Generadas {len(ia_valid)} preguntas IA válidas")
        
        ia_rows = []
        for i, q in enumerate(ia_valid, start=1):
            ia_rows.append({
                "ID_Evaluacion": str(eval_id),
                "ID_Activo": str(activo_id),
                "Fecha": fecha_version,
                "ID_Pregunta": f"IA-{dt.datetime.now().strftime('%H%M%S')}-{i}",
                "Pregunta": q["Pregunta"],
                "Tipo_Respuesta": q["Tipo_Respuesta"],
                "Peso": q["Peso"],
                "Dimension": q["Dimension"],
                "Fuente(IA/Base)": "IA"
            })
        
        append_rows("CUESTIONARIOS", base_rows + ia_rows)
        set_eval_active(str(eval_id), str(eval_name))
        
        st.balloons()
        st.success(f"📥 Cuestionario guardado. Versión: {fecha_version}")
        st.rerun()


# ==================== TAB 3: RESPONDER ====================
with tab3:
    st.subheader("✍️ Responder Cuestionario")
    
    cu = read_sheet("CUESTIONARIOS")
    if cu.empty:
        st.warning("No hay cuestionarios. Ve a Tab 2 para generar uno.")
        st.stop()
    
    auto_mode = st.session_state.get("go_to_tab3", False)
    auto_eval = st.session_state.get("resp_eval", None)
    auto_act = st.session_state.get("resp_act", None)
    auto_fecha = st.session_state.get("resp_fecha", None)
    
    evals = sorted(cu["ID_Evaluacion"].dropna().astype(str).unique().tolist())
    if not evals:
        st.warning("No hay evaluaciones.")
        st.stop()
    
    eval_index = evals.index(str(auto_eval)) if (auto_mode and auto_eval in evals) else 0
    eval_sel = st.selectbox("Evaluación", evals, index=eval_index, key="resp_eval_sel")
    
    acts = sorted(cu[cu["ID_Evaluacion"].astype(str) == str(eval_sel)]["ID_Activo"].dropna().astype(str).unique().tolist())
    if not acts:
        st.warning("No hay activos para esta evaluación.")
        st.stop()
    
    act_index = acts.index(str(auto_act)) if (auto_mode and auto_act in acts) else 0
    act_sel = st.selectbox("Activo", acts, index=act_index, key="resp_act_sel")
    
    fechas = sorted(
        cu[
            (cu["ID_Evaluacion"].astype(str) == str(eval_sel)) &
            (cu["ID_Activo"].astype(str) == str(act_sel))
        ]["Fecha"].dropna().astype(str).unique().tolist()
    )
    
    if not fechas:
        st.warning("No hay versiones.")
        st.stop()
    
    fecha_index = fechas.index(str(auto_fecha)) if (auto_mode and auto_fecha in fechas) else len(fechas) - 1
    fecha_sel = st.selectbox("Versión cuestionario", fechas, index=fecha_index, key="resp_fecha_sel")
    
    st.session_state["fecha_sel"] = str(fecha_sel)
    st.session_state["go_to_tab3"] = False
    
    preguntas = cu[
        (cu["ID_Evaluacion"].astype(str) == str(eval_sel)) &
        (cu["ID_Activo"].astype(str) == str(act_sel)) &
        (cu["Fecha"].astype(str) == str(fecha_sel))
    ].copy()
    
    if preguntas.empty:
        st.warning("No hay preguntas para esa versión.")
        st.stop()
    
    for col in ["Pregunta", "Tipo_Respuesta", "Fuente(IA/Base)"]:
        if col in preguntas.columns:
            preguntas[col] = preguntas[col].astype(str)
    
    subset_cols = [c for c in ["Pregunta", "Tipo_Respuesta", "Peso", "Dimension", "Fuente(IA/Base)"] if c in preguntas.columns]
    if subset_cols:
        preguntas = preguntas.drop_duplicates(subset=subset_cols, keep="first").reset_index(drop=True)
    
    st.info(f"📋 Total de preguntas: **{len(preguntas)}**")
    
    st.markdown("### ✏️ Editar preguntas (opcional)")
    editar = st.toggle("Habilitar edición", value=False, key="t3_edit_toggle")
    if editar:
        cols_show = [c for c in ["ID_Pregunta", "Pregunta", "Tipo_Respuesta", "Peso", "Dimension", "Fuente(IA/Base)"] if c in preguntas.columns]
        df_edit = preguntas[cols_show].copy()
        edited = st.data_editor(df_edit, num_rows="fixed", width='stretch', key="t3_editor")
        
        if st.button("💾 Guardar edición", key="t3_save_edit"):
            updated = update_cuestionarios_version(eval_sel, act_sel, str(fecha_sel), edited)
            st.success(f"✅ Filas actualizadas: {updated}")
            st.rerun()
    
    st.divider()
    st.markdown("### 📝 Responder cuestionario")
    
    respuestas_rows = []
    form_id = f"form_{eval_sel}_{act_sel}_{fecha_sel}".replace(" ", "_").replace(":", "").replace("/", "-")
    
    with st.form(form_id):
        for i, q in enumerate(preguntas.to_dict("records")):
            st.markdown(f"**{i+1}. {q.get('Pregunta','')}**")
            
            tipo_resp = str(q.get("Tipo_Respuesta", "1-5")).strip()
            dim_val = str(q.get("Dimension", "I")).strip().upper()
            if dim_val not in ["D", "I", "C"]:
                dim_val = "I"
            
            widget_key = f"{eval_sel}|{act_sel}|{fecha_sel}|{q.get('ID_Pregunta','NA')}|{i}"
            
            if tipo_resp == "0/1":
                resp_txt = st.radio("Respuesta", ["No", "Sí"], key=widget_key, horizontal=True)
                valor = 1 if resp_txt == "Sí" else 0
            else:
                valor = st.slider("Respuesta (1–5)", 1, 5, 3, key=widget_key)
            
            try:
                peso_val = int(q.get("Peso", 3))
            except:
                peso_val = 3
            peso_val = max(1, min(5, peso_val))
            
            respuestas_rows.append({
                "ID_Evaluacion": str(eval_sel),
                "ID_Activo": str(act_sel),
                "Fecha_Cuestionario": str(fecha_sel),
                "ID_Pregunta": str(q.get("ID_Pregunta", f"Q-{i+1}")),
                "Pregunta": str(q.get("Pregunta", "")),
                "Respuesta": valor,
                "Tipo_Respuesta": tipo_resp,
                "Peso": peso_val,
                "Dimension": dim_val,
                "Fecha": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        submitted = st.form_submit_button("💾 Guardar respuestas", type="primary")
    
    if submitted:
        append_rows("RESPUESTAS", respuestas_rows)
        st.success("✅ Respuestas guardadas correctamente.")
        st.balloons()


# ==================== TAB 4: IMPACTO DIC ====================
with tab4:
    st.subheader("📊 Cálculo de Impacto MAGERIT (DIC)")
    
    resp = read_sheet("RESPUESTAS")
    if resp.empty:
        st.warning("No hay respuestas. Responde en Tab 3.")
        st.stop()
    
    if "Fecha_Cuestionario" not in resp.columns:
        st.error("RESPUESTAS no tiene Fecha_Cuestionario.")
        st.stop()
    
    for col in ["Respuesta", "Peso"]:
        if col in resp.columns:
            resp[col] = pd.to_numeric(resp[col], errors="coerce").fillna(0)
    
    if "Dimension" not in resp.columns:
        resp["Dimension"] = "I"
    
    col1, col2, col3 = st.columns(3)
    evals = sorted(resp["ID_Evaluacion"].dropna().astype(str).unique().tolist())
    with col1:
        eval_sel = st.selectbox("Evaluación", evals, key="t4_eval")
    
    acts = sorted(resp[resp["ID_Evaluacion"].astype(str) == str(eval_sel)]["ID_Activo"].dropna().astype(str).unique().tolist())
    if not acts:
        st.warning("No hay activos.")
        st.stop()
    with col2:
        act_sel = st.selectbox("Activo", acts, key="t4_act")
    
    versiones = sorted(
        resp[(resp["ID_Evaluacion"].astype(str) == str(eval_sel)) & (resp["ID_Activo"].astype(str) == str(act_sel))]["Fecha_Cuestionario"]
        .dropna().astype(str).unique().tolist()
    )
    if not versiones:
        st.warning("No hay versiones respondidas.")
        st.stop()
    with col3:
        fecha_c = st.selectbox("Versión", versiones, key="t4_fecha")
    
    data = resp[
        (resp["ID_Evaluacion"].astype(str) == str(eval_sel)) &
        (resp["ID_Activo"].astype(str) == str(act_sel)) &
        (resp["Fecha_Cuestionario"].astype(str) == str(fecha_c))
    ].copy()
    
    if data.empty:
        st.warning("No hay respuestas.")
        st.stop()
    
    data["Valor_Ponderado"] = data["Respuesta"] * data["Peso"]
    
    impactos = {}
    for dim in ["D", "I", "C"]:
        d = data[data["Dimension"].astype(str).str.upper().str.strip() == dim]
        impactos[dim] = round(float(d["Valor_Ponderado"].mean()), 2) if not d.empty else 0.0
    
    impacto_global = max(impactos.values())
    
    st.markdown("### 📊 Resultados Impacto DIC")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Disponibilidad (D)", impactos["D"])
    m2.metric("Integridad (I)", impactos["I"])
    m3.metric("Confidencialidad (C)", impactos["C"])
    m4.metric("Impacto Global", impacto_global)
    
    if st.button("💾 Guardar impacto", key="t4_save", type="primary"):
        append_rows("IMPACTO_ACTIVOS", [{
            "ID_Evaluacion": str(eval_sel),
            "ID_Activo": str(act_sel),
            "Fecha_Cuestionario": str(fecha_c),
            "Impacto_D": impactos["D"],
            "Impacto_I": impactos["I"],
            "Impacto_C": impactos["C"],
            "Impacto_Global": impacto_global,
            "Fecha_Calculo": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])
        st.success("✅ Impacto guardado en IMPACTO_ACTIVOS.")


# ==================== TAB 5: ANÁLISIS IA ====================
with tab5:
    st.subheader("🔍 Análisis de Riesgos con IA")
    st.caption("Análisis automático de amenazas, vulnerabilidades y salvaguardas")
    
    # Cargar datos
    resp = read_sheet("RESPUESTAS")
    impactos = read_sheet("IMPACTO_ACTIVOS")
    inv = read_sheet("INVENTARIO_ACTIVOS")
    
    if resp.empty:
        st.warning("⚠️ No hay respuestas. Completa cuestionarios en Tab 3.")
        st.stop()
    
    if impactos.empty:
        st.warning("⚠️ No hay impactos calculados. Calcula en Tab 4.")
        st.stop()
    
    # Selectores
    col1, col2, col3 = st.columns(3)
    
    evals_disponibles = sorted(resp["ID_Evaluacion"].dropna().astype(str).unique().tolist())
    with col1:
        eval_sel = st.selectbox("Evaluación", evals_disponibles, key="t5_eval")
    
    activos_disponibles = sorted(resp[resp["ID_Evaluacion"].astype(str) == str(eval_sel)]["ID_Activo"].dropna().astype(str).unique().tolist())
    with col2:
        act_sel = st.selectbox("Activo", activos_disponibles, key="t5_act")
    
    with col3:
        model_sel = st.selectbox("Modelo IA", ["llama3", "phi3", "mistral"], key="t5_model")
    
    # Botón analizar
    if st.button("🤖 Analizar con IA", key="t5_analyze", type="primary"):
        with st.spinner("🧠 Analizando riesgos con IA... Esto puede tardar 1-2 minutos..."):
            # Construir contexto
            activo_info = inv[inv["ID_Activo"] == act_sel].iloc[0].to_dict() if not inv.empty else {}
            respuestas_activo = resp[
                (resp["ID_Evaluacion"].astype(str) == str(eval_sel)) &
                (resp["ID_Activo"].astype(str) == str(act_sel))
            ].to_dict('records')
            
            impacto_activo = impactos[
                (impactos["ID_Evaluacion"].astype(str) == str(eval_sel)) &
                (impactos["ID_Activo"].astype(str) == str(act_sel))
            ]
            
            impacto_d = float(impacto_activo["Impacto_D"].iloc[0]) if not impacto_activo.empty else 3
            impacto_i = float(impacto_activo["Impacto_I"].iloc[0]) if not impacto_activo.empty else 3
            impacto_c = float(impacto_activo["Impacto_C"].iloc[0]) if not impacto_activo.empty else 3
            
            contexto = {
                'activo': activo_info,
                'respuestas_muestra': respuestas_activo[:10],  # Primeras 10 para no saturar
                'impacto_d': impacto_d,
                'impacto_i': impacto_i,
                'impacto_c': impacto_c
            }
            
            # Llamar servicio IA
            resultado = ollama_analyze_risk(contexto, model=model_sel)
            
            if resultado.get('error', False):
                st.error(f"⚠️ Error en análisis: {resultado.get('justificacion', 'Error desconocido')}")
                if 'raw_response' in resultado:
                    with st.expander("🔍 Ver respuesta cruda"):
                        st.code(resultado['raw_response'])
            else:
                st.success("✅ Análisis completado correctamente")
                
                # Mostrar resultados
                st.markdown("### 📊 Métricas de Riesgo")
                col1, col2, col3, col4 = st.columns(4)
                
                prob = resultado.get('probabilidad', 3)
                imp = resultado.get('impacto', 3)
                riesgo = resultado.get('riesgo_inherente', prob * imp)
                nivel = get_risk_level(riesgo)
                
                col1.metric("Probabilidad", f"{prob}/5")
                col2.metric("Impacto", f"{imp}/5")
                col3.metric("Riesgo Inherente", f"{riesgo}/25")
                col4.metric("Nivel", nivel, delta_color="inverse")
                
                # Justificación
                st.markdown("### 📝 Justificación")
                st.info(resultado.get('justificacion', 'No disponible'))
                
                # Amenazas
                st.markdown("### ⚠️ Amenazas Identificadas")
                amenazas = resultado.get('amenazas', [])
                if amenazas:
                    for am in amenazas:
                        with st.expander(f"🔴 {am.get('codigo', 'N/A')} - {am.get('nombre', 'Sin nombre')}"):
                            st.write(f"**Descripción:** {am.get('descripcion', 'N/A')}")
                            st.write(f"**Probabilidad:** {am.get('probabilidad', 'N/A')}")
                else:
                    st.warning("No se identificaron amenazas específicas")
                
                # Vulnerabilidades
                st.markdown("### 🔓 Vulnerabilidades Detectadas")
                vulns = resultado.get('vulnerabilidades', [])
                if vulns:
                    for vul in vulns:
                        sev = vul.get('severidad', 3)
                        color = "🔴" if sev >= 4 else "🟡" if sev >= 3 else "🟢"
                        st.write(f"{color} **{vul.get('nombre', 'Sin nombre')}** (Severidad: {sev}/5)")
                        st.caption(vul.get('descripcion', 'Sin descripción'))
                else:
                    st.warning("No se detectaron vulnerabilidades específicas")
                
                # Salvaguardas
                st.markdown("### 🛡️ Salvaguardas Recomendadas (ISO 27002)")
                salvaguardas = resultado.get('salvaguardas', [])
                if salvaguardas:
                    for sal in salvaguardas:
                        prio = sal.get('prioridad', 3)
                        urgencia = "🔥 Alta" if prio >= 4 else "⚡ Media" if prio >= 3 else "📌 Baja"
                        st.write(f"**{sal.get('control_iso', 'N/A')}** - {sal.get('nombre', 'Sin nombre')} ({urgencia})")
                        st.caption(sal.get('descripcion', 'Sin descripción'))
                else:
                    st.warning("No se propusieron salvaguardas específicas")
                
                # Guardar resultado
                st.divider()
                if st.button("💾 Guardar Análisis", key="t5_save"):
                    append_rows("ANALISIS_RIESGO", [{
                        "ID_Evaluacion": str(eval_sel),
                        "ID_Activo": str(act_sel),
                        "Fecha_Analisis": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Probabilidad": prob,
                        "Impacto": imp,
                        "Riesgo_Inherente": riesgo,
                        "Amenazas_JSON": json.dumps(amenazas, ensure_ascii=False),
                        "Vulnerabilidades_JSON": json.dumps(vulns, ensure_ascii=False),
                        "Salvaguardas_JSON": json.dumps(salvaguardas, ensure_ascii=False),
                        "Justificacion": resultado.get('justificacion', ''),
                        "Modelo_IA": model_sel
                    }])
                    st.success("✅ Análisis guardado en ANALISIS_RIESGO")
                    st.balloons()


# ==================== TAB 6: DASHBOARDS ====================
with tab6:
    st.subheader("📈 Dashboards y Visualizaciones")
    
    analisis = read_sheet("ANALISIS_RIESGO")
    impactos_data = read_sheet("IMPACTO_ACTIVOS")
    
    if analisis.empty:
        st.warning("⚠️ No hay análisis de riesgos. Analiza activos en Tab 5.")
        st.info("💡 Los dashboards se generarán automáticamente después de realizar análisis de riesgos.")
        st.stop()
    
    # Dashboard 1: Mapa de Calor
    st.markdown("### 🔥 Mapa de Calor de Riesgos (Probabilidad × Impacto)")
    
    if not analisis.empty and 'Probabilidad' in analisis.columns and 'Impacto' in analisis.columns:
        # Preparar datos
        analisis['Nivel_Riesgo'] = analisis['Riesgo_Inherente'].apply(get_risk_level)
        
        fig_heatmap = px.scatter(
            analisis,
            x='Impacto',
            y='Probabilidad',
            size='Riesgo_Inherente',
            color='Nivel_Riesgo',
            hover_data=['ID_Activo', 'Riesgo_Inherente'],
            color_discrete_map=RISK_COLORS,
            title='Matriz de Riesgos',
            labels={'Impacto': 'Impacto (1-5)', 'Probabilidad': 'Probabilidad (1-5)'}
        )
        
        fig_heatmap.update_layout(
            xaxis=dict(range=[0, 6], dtick=1),
            yaxis=dict(range=[0, 6], dtick=1),
            height=500
        )
        
        st.plotly_chart(fig_heatmap, width='stretch')
    
    # Dashboard 2: Ranking de Activos
    st.markdown("### 🏆 Ranking de Activos Críticos")
    
    if not analisis.empty:
        top_activos = analisis.nlargest(10, 'Riesgo_Inherente')
        
        fig_ranking = px.bar(
            top_activos,
            y='ID_Activo',
            x='Riesgo_Inherente',
            orientation='h',
            color='Riesgo_Inherente',
            color_continuous_scale='Reds',
            title='Top 10 Activos por Nivel de Riesgo',
            labels={'Riesgo_Inherente': 'Riesgo Inherente (1-25)', 'ID_Activo': 'Activo'}
        )
        
        fig_ranking.update_layout(height=400)
        st.plotly_chart(fig_ranking, width='stretch')
    
    # Dashboard 3: Distribución DIC
    st.markdown("### 📊 Distribución de Impactos DIC")
    
    if not impactos_data.empty:
        dic_promedio = {
            'Dimensión': ['Disponibilidad', 'Integridad', 'Confidencialidad'],
            'Promedio': [
                impactos_data['Impacto_D'].mean(),
                impactos_data['Impacto_I'].mean(),
                impactos_data['Impacto_C'].mean()
            ]
        }
        
        fig_dic = px.bar(
            dic_promedio,
            x='Dimensión',
            y='Promedio',
            color='Dimensión',
            title='Impacto Promedio por Dimensión DIC',
            color_discrete_sequence=['#17a2b8', '#ffc107', '#dc3545']
        )
        
        fig_dic.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_dic, width='stretch')
    
    # Dashboard 4: Distribución de Niveles de Riesgo
    st.markdown("### 🎯 Distribución por Nivel de Riesgo")
    
    if not analisis.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            dist_riesgo = analisis['Nivel_Riesgo'].value_counts().reset_index()
            dist_riesgo.columns = ['Nivel', 'Cantidad']
            
            fig_pie = px.pie(
                dist_riesgo,
                values='Cantidad',
                names='Nivel',
                title='Distribución de Activos por Nivel de Riesgo',
                color='Nivel',
                color_discrete_map=RISK_COLORS
            )
            
            st.plotly_chart(fig_pie, width='stretch')
        
        with col2:
            st.markdown("#### 📊 Estadísticas Generales")
            st.metric("Total Activos Analizados", len(analisis))
            st.metric("Riesgo Promedio", f"{analisis['Riesgo_Inherente'].mean():.2f}/25")
            st.metric("Riesgo Máximo", f"{analisis['Riesgo_Inherente'].max()}/25")
            
            criticos = len(analisis[analisis['Nivel_Riesgo'] == 'Crítico'])
            altos = len(analisis[analisis['Nivel_Riesgo'] == 'Alto'])
            
            st.metric("Activos Críticos", criticos, delta=f"+{criticos}" if criticos > 0 else "0", delta_color="inverse")
            st.metric("Activos Alto Riesgo", altos, delta=f"+{altos}" if altos > 0 else "0", delta_color="inverse")


# ==================== TAB 7: COMPARATIVAS ====================
with tab7:
    st.subheader("🔄 Comparar Evaluaciones")
    st.caption("Análisis de evolución temporal de riesgos")
    
    analisis = read_sheet("ANALISIS_RIESGO")
    
    if analisis.empty:
        st.warning("⚠️ No hay análisis de riesgos para comparar.")
        st.stop()
    
    # Verificar que hay múltiples evaluaciones
    evals_disponibles = analisis["ID_Evaluacion"].dropna().unique().tolist()
    
    if len(evals_disponibles) < 2:
        st.info("ℹ️ Se necesitan al menos 2 evaluaciones para realizar comparaciones.")
        st.write(f"**Evaluaciones disponibles:** {len(evals_disponibles)}")
        st.stop()
    
    col1, col2 = st.columns(2)
    with col1:
        eval_a = st.selectbox("📅 Evaluación A (anterior)", evals_disponibles, key="comp_eval_a")
    with col2:
        eval_b = st.selectbox("📅 Evaluación B (posterior)", [e for e in evals_disponibles if e != eval_a], key="comp_eval_b")
    
    if st.button("🔍 Comparar", key="comp_analyze", type="primary"):
        # Filtrar análisis
        analisis_a = analisis[analisis["ID_Evaluacion"] == eval_a]
        analisis_b = analisis[analisis["ID_Evaluacion"] == eval_b]
        
        st.markdown("### 📊 Métricas Comparativas")
        
        col1, col2, col3 = st.columns(3)
        
        riesgo_a = analisis_a["Riesgo_Inherente"].mean()
        riesgo_b = analisis_b["Riesgo_Inherente"].mean()
        delta_riesgo = riesgo_b - riesgo_a
        
        col1.metric("Eval A - Riesgo Promedio", f"{riesgo_a:.2f}/25")
        col2.metric("Eval B - Riesgo Promedio", f"{riesgo_b:.2f}/25")
        col3.metric("Diferencia", f"{delta_riesgo:+.2f}", delta_color="inverse")
        
        # Activos comunes
        activos_a = set(analisis_a["ID_Activo"].tolist())
        activos_b = set(analisis_b["ID_Activo"].tolist())
        activos_comunes = activos_a.intersection(activos_b)
        
        st.markdown(f"### 🔗 Activos Comunes: {len(activos_comunes)}")
        
        if activos_comunes:
            # Crear tabla comparativa
            comparacion = []
            for activo in activos_comunes:
                ra_val = analisis_a[analisis_a["ID_Activo"] == activo]["Riesgo_Inherente"].iloc[0]
                rb_val = analisis_b[analisis_b["ID_Activo"] == activo]["Riesgo_Inherente"].iloc[0]
                comparacion.append({
                    "Activo": activo,
                    "Riesgo_A": ra_val,
                    "Riesgo_B": rb_val,
                    "Diferencia": rb_val - ra_val,
                    "Evolución": "⬆️ Aumentó" if rb_val > ra_val else "⬇️ Disminuyó" if rb_val < ra_val else "➡️ Sin cambio"
                })
            
            df_comp = pd.DataFrame(comparacion)
            df_comp = df_comp.sort_values("Diferencia", ascending=False)
            
            st.dataframe(df_comp, width='stretch', height=400)
            
            # Gráfico de evolución
            st.markdown("### 📈 Evolución de Riesgos")
            
            fig_evol = go.Figure()
            
            fig_evol.add_trace(go.Bar(
                name='Evaluación A',
                x=df_comp['Activo'],
                y=df_comp['Riesgo_A'],
                marker_color='lightblue'
            ))
            
            fig_evol.add_trace(go.Bar(
                name='Evaluación B',
                x=df_comp['Activo'],
                y=df_comp['Riesgo_B'],
                marker_color='darkblue'
            ))
            
            fig_evol.update_layout(
                title='Comparación de Riesgo Inherente por Activo',
                xaxis_title='Activo',
                yaxis_title='Riesgo Inherente',
                barmode='group',
                height=500
            )
            
            st.plotly_chart(fig_evol, width='stretch')
            
            # Resumen ejecutivo
            st.markdown("### 📋 Resumen Ejecutivo")
            
            mejoraron = len(df_comp[df_comp["Diferencia"] < 0])
            empeoraron = len(df_comp[df_comp["Diferencia"] > 0])
            sin_cambio = len(df_comp[df_comp["Diferencia"] == 0])
            
            col1, col2, col3 = st.columns(3)
            col1.metric("✅ Mejoraron", mejoraron)
            col2.metric("⚠️ Empeoraron", empeoraron)
            col3.metric("➡️ Sin cambio", sin_cambio)
            
            if mejoraron > empeoraron:
                st.success(f"🎉 Tendencia positiva: {mejoraron} activos mejoraron su nivel de riesgo")
            elif empeoraron > mejoraron:
                st.warning(f"⚠️ Atención requerida: {empeoraron} activos empeoraron su nivel de riesgo")
            else:
                st.info("ℹ️ Situación estable: no hay cambios significativos")
        else:
            st.warning("No hay activos comunes entre ambas evaluaciones para comparar.")

# Footer
st.divider()
st.caption("🛡️ Proyecto TITA - Sistema de Evaluación de Riesgos MAGERIT/ISO 27002 | Versión 2.0")
