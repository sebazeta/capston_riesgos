"""
COMPONENTE UI PARA FUNCIONALIDADES DE IA AVANZADA
===================================================
Interfaz de usuario para:
1. Generador de Planes de Tratamiento
2. Chatbot Consultor MAGERIT
3. Resumen Ejecutivo Automático
4. Predicción de Riesgo Futuro
5. Priorización Inteligente de Controles
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from services.ia_advanced_service import (
    generar_plan_tratamiento,
    generar_planes_evaluacion,
    consultar_chatbot_magerit,
    generar_resumen_ejecutivo,
    generar_prediccion_riesgo,
    generar_priorizacion_controles,
    verificar_ia_disponible,
    guardar_resultado_ia,
    cargar_resultado_ia,
    ResumenEjecutivo,
    PrediccionRiesgo,
    ControlPriorizado,
    PlanTratamiento
)
from services.database_service import read_table
import json


def _obtener_amenazas_evaluacion(eval_id: str) -> pd.DataFrame:
    """
    Extrae las amenazas de una evaluación desde RESULTADOS_MAGERIT.Amenazas_JSON.
    Retorna un DataFrame con las amenazas desagregadas.
    """
    resultados = read_table("RESULTADOS_MAGERIT")
    if resultados.empty:
        return pd.DataFrame()
    
    # Normalizar nombre de columna
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


def render_ia_avanzada_ui():
    """Renderiza la interfaz completa de IA Avanzada."""
    
    st.title("🧠 IA Avanzada - Funcionalidades Inteligentes")
    
    # Verificar evaluación seleccionada
    eval_id = st.session_state.get("eval_actual")
    if not eval_id:
        st.warning("⚠️ Selecciona una evaluación en la barra lateral para usar las funcionalidades de IA.")
        return
    
    # Verificar disponibilidad de IA
    ia_disponible, mensaje_ia = verificar_ia_disponible()
    
    if ia_disponible:
        st.success(f"✅ {mensaje_ia}")
    else:
        st.warning(f"⚠️ {mensaje_ia} - Se usarán métodos heurísticos como fallback")
    
    # Selector de modelo
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"📋 Evaluación activa: **{eval_id}**")
    with col2:
        modelo = st.selectbox(
            "Modelo IA",
            ["llama3.2:1b", "llama3:latest", "tinyllama:latest"],
            index=0,
            help="Selecciona el modelo de IA a usar"
        )
    
    st.divider()
    
    # Tabs para cada funcionalidad
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Planes de Tratamiento",
        "💬 Chatbot MAGERIT",
        "📋 Resumen Ejecutivo",
        "🔮 Predicción de Riesgo",
        "🎯 Priorización de Controles"
    ])
    
    with tab1:
        _render_planes_tratamiento(eval_id, modelo)
    
    with tab2:
        _render_chatbot(eval_id, modelo)
    
    with tab3:
        _render_resumen_ejecutivo(eval_id, modelo)
    
    with tab4:
        _render_prediccion_riesgo(eval_id, modelo)
    
    with tab5:
        _render_priorizacion_controles(eval_id, modelo)


# ==================== 1. PLANES DE TRATAMIENTO ====================

def _render_planes_tratamiento(eval_id: str, modelo: str):
    """Renderiza la sección de planes de tratamiento."""
    
    st.markdown("### 📝 Generador de Planes de Tratamiento")
    st.markdown("""
    Genera planes de acción detallados para mitigar amenazas específicas.
    Incluye acciones a corto, mediano y largo plazo con responsables y costos estimados.
    """)
    
    # Cargar planes guardados
    resultado_guardado = cargar_resultado_ia(eval_id, "planes_tratamiento")
    planes_guardados = []
    
    if resultado_guardado:
        datos = resultado_guardado["datos"]
        if "planes" in datos and datos["planes"]:
            for p in datos["planes"]:
                planes_guardados.append(PlanTratamiento(
                    id_activo=p.get("id_activo", ""),
                    codigo_amenaza=p.get("codigo_amenaza", ""),
                    nombre_amenaza=p.get("nombre_amenaza", ""),
                    nivel_riesgo=p.get("nivel_riesgo", ""),
                    acciones_corto_plazo=p.get("acciones_corto_plazo", []),
                    acciones_mediano_plazo=p.get("acciones_mediano_plazo", []),
                    acciones_largo_plazo=p.get("acciones_largo_plazo", []),
                    responsable_general=p.get("responsable_general", ""),
                    presupuesto_total=p.get("presupuesto_total", ""),
                    kpis=p.get("kpis", []),
                    modelo_ia=p.get("modelo_ia", modelo)
                ))
    
    # Obtener amenazas desde RESULTADOS_MAGERIT.Amenazas_JSON
    amenazas_eval = _obtener_amenazas_evaluacion(eval_id)
    
    # Validar que hay datos
    if amenazas_eval.empty:
        st.info("ℹ️ No hay amenazas identificadas para esta evaluación. Primero ejecuta la evaluación MAGERIT.")
        st.markdown("""
        **Pasos para generar amenazas:**
        1. Ve a la pestaña **📦 Activos** y registra activos
        2. Ve a la pestaña **📝 Cuestionarios** y responde las preguntas
        3. Ve a la pestaña **🤖 Evaluación MAGERIT** y ejecuta la evaluación
        4. Regresa aquí para generar planes de tratamiento
        """)
        return
    
    # Filtrar amenazas de alto riesgo
    amenazas_criticas = amenazas_eval[
        amenazas_eval["nivel_riesgo"].isin(["ALTO", "CRÍTICO", "CRITICO"])
    ]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Amenazas", len(amenazas_eval))
    with col2:
        st.metric("Amenazas Críticas/Altas", len(amenazas_criticas))
    
    # Mostrar planes guardados si existen
    if planes_guardados:
        st.success(f"✅ {len(planes_guardados)} planes guardados (generados el {resultado_guardado['fecha'][:10]})")
    
    st.divider()
    
    # Opción 1: Generar plan individual
    st.markdown("#### 🎯 Generar Plan Individual")
    
    # Crear opciones para selectbox
    opciones_amenazas = []
    for _, row in amenazas_eval.iterrows():
        opcion = f"{row['codigo']} - {row.get('amenaza', 'N/A')[:40]} ({row['nivel_riesgo']}) - {row['id_activo']}"
        opciones_amenazas.append((opcion, row['id_activo'], row['codigo']))
    
    if opciones_amenazas:
        seleccion = st.selectbox(
            "Selecciona una amenaza:",
            options=[o[0] for o in opciones_amenazas],
            index=0
        )
        
        # Encontrar activo_id y codigo_amenaza
        idx = [o[0] for o in opciones_amenazas].index(seleccion)
        activo_id = opciones_amenazas[idx][1]
        codigo_amenaza = opciones_amenazas[idx][2]
        
        if st.button("🔧 Generar Plan de Tratamiento", type="primary"):
            with st.spinner("Generando plan de tratamiento con IA..."):
                exito, plan, mensaje = generar_plan_tratamiento(
                    eval_id, activo_id, codigo_amenaza, modelo
                )
            
            if exito and plan:
                st.success(f"✅ {mensaje}")
                _mostrar_plan_tratamiento(plan)
            else:
                st.error(f"❌ {mensaje}")
    
    st.divider()
    
    # Opción 2: Generar todos los planes
    st.markdown("#### 📚 Generar Todos los Planes (Riesgos Altos/Críticos)")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        btn_label = "🚀 Generar Todos los Planes" if not planes_guardados else "🔄 Regenerar Todos los Planes"
        generar_todos = st.button(btn_label, use_container_width=True, type="primary" if not planes_guardados else "secondary")
    with col2:
        if planes_guardados:
            st.caption(f"📅 {resultado_guardado['fecha'][:10]}")
    
    if generar_todos:
        with st.spinner(f"Generando planes para {len(amenazas_criticas)} amenazas críticas..."):
            planes = generar_planes_evaluacion(eval_id, modelo)
        
        if planes:
            # Guardar en BD
            datos_guardar = {"planes": [p.__dict__ for p in planes]}
            guardar_resultado_ia(eval_id, "planes_tratamiento", datos_guardar, modelo)
            st.success(f"✅ Se generaron {len(planes)} planes de tratamiento")
            st.rerun()
        else:
            st.info("ℹ️ No se encontraron amenazas de nivel ALTO o CRÍTICO")
    
    # Mostrar planes guardados
    if planes_guardados:
        st.markdown("---")
        st.markdown("#### 📋 Planes de Tratamiento Guardados")
        for i, plan in enumerate(planes_guardados):
            with st.expander(f"📄 Plan {i+1}: {plan.codigo_amenaza} - {plan.nombre_amenaza[:40]}"):
                _mostrar_plan_tratamiento(plan)


def _mostrar_plan_tratamiento(plan):
    """Muestra un plan de tratamiento formateado."""
    
    st.markdown(f"""
    **Activo:** {plan.id_activo}  
    **Amenaza:** [{plan.codigo_amenaza}] {plan.nombre_amenaza}  
    **Nivel de Riesgo:** {plan.nivel_riesgo}  
    **Modelo IA:** {plan.modelo_ia}
    """)
    
    # Acciones corto plazo
    st.markdown("##### ⚡ Acciones a Corto Plazo (1-2 semanas)")
    for accion in plan.acciones_corto_plazo:
        st.markdown(f"""
        - **{accion.get('accion', '')}**
          - Responsable: {accion.get('responsable', 'N/A')}
          - Plazo: {accion.get('plazo', 'N/A')}
          - Costo: {accion.get('costo', 'N/A')}
        """)
    
    # Acciones mediano plazo
    st.markdown("##### 🔄 Acciones a Mediano Plazo (1-2 meses)")
    for accion in plan.acciones_mediano_plazo:
        st.markdown(f"""
        - **{accion.get('accion', '')}**
          - Responsable: {accion.get('responsable', 'N/A')}
          - Plazo: {accion.get('plazo', 'N/A')}
          - Costo: {accion.get('costo', 'N/A')}
        """)
    
    # Acciones largo plazo
    st.markdown("##### 🎯 Acciones a Largo Plazo (3-6 meses)")
    for accion in plan.acciones_largo_plazo:
        st.markdown(f"""
        - **{accion.get('accion', '')}**
          - Responsable: {accion.get('responsable', 'N/A')}
          - Plazo: {accion.get('plazo', 'N/A')}
          - Costo: {accion.get('costo', 'N/A')}
        """)
    
    # KPIs y estimaciones
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 📊 KPIs de Seguimiento")
        for kpi in plan.kpis_seguimiento:
            st.markdown(f"- {kpi}")
    
    with col2:
        st.markdown("##### 💰 Estimaciones")
        st.markdown(f"- **Inversión:** {plan.inversion_estimada}")
        st.markdown(f"- **Reducción de riesgo:** {plan.reduccion_riesgo_esperada}")


# ==================== 2. CHATBOT MAGERIT ====================

def _render_chatbot(eval_id: str, modelo: str):
    """Renderiza el chatbot consultor MAGERIT."""
    
    st.markdown("### 💬 Chatbot Consultor MAGERIT")
    st.markdown("""
    Pregunta sobre tu evaluación de riesgos. El asistente conoce todos los datos
    de tus activos, amenazas y controles.
    """)
    
    # Inicializar historial
    if "chatbot_historial" not in st.session_state:
        st.session_state.chatbot_historial = []
    
    # Mostrar historial
    for msg in st.session_state.chatbot_historial:
        if msg["rol"] == "user":
            st.chat_message("user").write(msg["contenido"])
        else:
            st.chat_message("assistant").write(msg["contenido"])
    
    # Input de usuario
    pregunta = st.chat_input("Escribe tu pregunta sobre la evaluación...")
    
    if pregunta:
        # Mostrar pregunta del usuario
        st.chat_message("user").write(pregunta)
        
        # Generar respuesta
        with st.spinner("Pensando..."):
            exito, respuesta, historial = consultar_chatbot_magerit(
                eval_id,
                pregunta,
                st.session_state.chatbot_historial,
                modelo
            )
        
        # Mostrar respuesta
        st.chat_message("assistant").write(respuesta)
        
        # Actualizar historial
        st.session_state.chatbot_historial = historial
    
    # Botón para limpiar historial
    if st.session_state.chatbot_historial:
        if st.button("🗑️ Limpiar conversación"):
            st.session_state.chatbot_historial = []
            st.rerun()
    
    # Sugerencias de preguntas
    st.divider()
    st.markdown("##### 💡 Preguntas sugeridas:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("¿Cuál es el activo más crítico?", use_container_width=True):
            _enviar_pregunta_sugerida(eval_id, modelo, "¿Cuál es el activo más crítico de mi evaluación?")
        if st.button("¿Qué controles faltan?", use_container_width=True):
            _enviar_pregunta_sugerida(eval_id, modelo, "¿Qué controles me faltan implementar?")
    
    with col2:
        if st.button("Dame un resumen general", use_container_width=True):
            _enviar_pregunta_sugerida(eval_id, modelo, "Dame un resumen general de la evaluación")
        if st.button("¿Cuáles son las amenazas más frecuentes?", use_container_width=True):
            _enviar_pregunta_sugerida(eval_id, modelo, "¿Cuáles son las amenazas más frecuentes?")


def _enviar_pregunta_sugerida(eval_id: str, modelo: str, pregunta: str):
    """Envía una pregunta sugerida al chatbot."""
    with st.spinner("Procesando..."):
        exito, respuesta, historial = consultar_chatbot_magerit(
            eval_id,
            pregunta,
            st.session_state.get("chatbot_historial", []),
            modelo
        )
    st.session_state.chatbot_historial = historial
    st.rerun()


# ==================== 3. RESUMEN EJECUTIVO ====================

def _render_resumen_ejecutivo(eval_id: str, modelo: str):
    """Renderiza la sección de resumen ejecutivo."""
    
    st.markdown("### 📋 Resumen Ejecutivo Automático")
    st.markdown("""
    Genera un informe ejecutivo profesional listo para presentar a la alta gerencia.
    Incluye hallazgos principales, recomendaciones prioritarias y estimaciones de inversión.
    """)
    
    # Intentar cargar resultado guardado en BD
    resultado_guardado = cargar_resultado_ia(eval_id, "resumen_ejecutivo")
    resumen_actual = None
    
    if resultado_guardado:
        # Reconstruir objeto ResumenEjecutivo desde los datos guardados
        datos = resultado_guardado["datos"]
        resumen_actual = ResumenEjecutivo(
            id_evaluacion=datos.get("id_evaluacion", eval_id),
            fecha_generacion=resultado_guardado["fecha"],
            total_activos=datos.get("total_activos", 0),
            total_amenazas=datos.get("total_amenazas", 0),
            distribucion_riesgo=datos.get("distribucion_riesgo", {}),
            hallazgos_principales=datos.get("hallazgos_principales", []),
            activos_criticos=datos.get("activos_criticos", []),
            recomendaciones_prioritarias=datos.get("recomendaciones_prioritarias", []),
            inversion_estimada=datos.get("inversion_estimada", ""),
            reduccion_riesgo_esperada=datos.get("reduccion_riesgo_esperada", ""),
            conclusion=datos.get("conclusion", ""),
            modelo_ia=resultado_guardado["modelo"]
        )
    
    # Mostrar botones
    col1, col2 = st.columns([3, 1])
    with col1:
        generar = st.button(
            "📄 Generar Resumen Ejecutivo" if not resumen_actual else "🔄 Regenerar Resumen",
            type="primary" if not resumen_actual else "secondary",
            use_container_width=True
        )
    with col2:
        if resumen_actual:
            st.caption(f"📅 Generado: {resultado_guardado['fecha'][:10]}")
    
    if generar:
        with st.spinner("Generando resumen ejecutivo con IA..."):
            exito, resumen, mensaje = generar_resumen_ejecutivo(eval_id, modelo)
        
        if exito and resumen:
            # Guardar en BD
            guardar_resultado_ia(eval_id, "resumen_ejecutivo", resumen.to_dict(), modelo)
            resumen_actual = resumen
            st.success(f"✅ {mensaje}")
            st.rerun()
        else:
            st.error(f"❌ {mensaje}")
    
    # Mostrar resumen si existe
    if resumen_actual:
        _mostrar_resumen_ejecutivo(resumen_actual)


def _mostrar_resumen_ejecutivo(resumen):
    """Muestra el resumen ejecutivo formateado."""
    
    # Encabezado
    st.markdown(f"""
    ---
    ## 📊 RESUMEN EJECUTIVO
    **Evaluación:** {resumen.id_evaluacion}  
    **Fecha:** {resumen.fecha_generacion}  
    **Generado por:** {resumen.modelo_ia}
    
    ---
    """)
    
    # Métricas principales
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Activos", resumen.total_activos)
    with col2:
        st.metric("Total Amenazas", resumen.total_amenazas)
    with col3:
        criticos = resumen.distribucion_riesgo.get("CRÍTICO", 0) + resumen.distribucion_riesgo.get("CRITICO", 0)
        st.metric("Riesgos Críticos", criticos)
    
    # Distribución de riesgos (gráfico)
    if resumen.distribucion_riesgo:
        # Usar colores personalizados para niveles de riesgo
        colores_riesgo = {
            "CRÍTICO": "#d62728",
            "CRITICO": "#d62728", 
            "ALTO": "#ff7f0e",
            "MEDIO": "#ffbb78",
            "BAJO": "#2ca02c"
        }
        nombres = list(resumen.distribucion_riesgo.keys())
        colores = [colores_riesgo.get(n, "#1f77b4") for n in nombres]
        
        fig = px.pie(
            names=nombres,
            values=list(resumen.distribucion_riesgo.values()),
            title="Distribución de Niveles de Riesgo",
            color_discrete_sequence=colores
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Hallazgos principales
    st.markdown("### 🔍 Hallazgos Principales")
    for i, hallazgo in enumerate(resumen.hallazgos_principales, 1):
        st.markdown(f"{i}. {hallazgo}")
    
    # Activos críticos
    st.markdown("### ⚠️ Activos Más Críticos")
    if resumen.activos_criticos:
        df_criticos = pd.DataFrame(resumen.activos_criticos)
        st.dataframe(df_criticos, use_container_width=True)
    
    # Recomendaciones
    st.markdown("### 💡 Recomendaciones Prioritarias")
    for i, rec in enumerate(resumen.recomendaciones_prioritarias, 1):
        st.markdown(f"{i}. {rec}")
    
    # Estimaciones
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"💰 **Inversión Estimada:** {resumen.inversion_estimada}")
    with col2:
        st.info(f"📉 **Reducción de Riesgo Esperada:** {resumen.reduccion_riesgo_esperada}")
    
    # Conclusión
    st.markdown("### 📝 Conclusión")
    st.markdown(f"> {resumen.conclusion}")
    
    st.divider()
    
    # Sección de Exportación
    st.markdown("### 📥 Exportar Documento Ejecutivo")
    
    col1, col2, col3 = st.columns(3)
    
    # Importar servicio de exportación
    from services.export_service import generar_documento_ejecutivo, generar_datos_powerbi
    
    with col1:
        # Exportar HTML
        exito_html, html_content, _ = generar_documento_ejecutivo(resumen, "html")
        if exito_html:
            st.download_button(
                "📄 Descargar HTML",
                data=html_content,
                file_name=f"resumen_ejecutivo_{resumen.id_evaluacion}.html",
                mime="text/html",
                use_container_width=True,
                help="Documento HTML profesional para abrir en navegador o imprimir"
            )
    
    with col2:
        # Exportar Markdown
        exito_md, md_content, _ = generar_documento_ejecutivo(resumen, "markdown")
        if exito_md:
            st.download_button(
                "📝 Descargar Markdown",
                data=md_content,
                file_name=f"resumen_ejecutivo_{resumen.id_evaluacion}.md",
                mime="text/markdown",
                use_container_width=True,
                help="Documento Markdown para edición"
            )
    
    with col3:
        # Exportar JSON
        import json
        resumen_json = json.dumps(resumen.to_dict(), indent=2, ensure_ascii=False)
        st.download_button(
            "🔧 Descargar JSON",
            data=resumen_json,
            file_name=f"resumen_ejecutivo_{resumen.id_evaluacion}.json",
            mime="application/json",
            use_container_width=True,
            help="Datos estructurados para integración"
        )
    
    # Sección Power BI
    st.markdown("### 📊 Datos para Power BI")
    st.markdown("Exporta datasets optimizados para crear dashboards en Power BI.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Generar Datos Power BI", use_container_width=True):
            with st.spinner("Generando datasets..."):
                exito_pbi, datasets, mensaje_pbi = generar_datos_powerbi(resumen.id_evaluacion)
            
            if exito_pbi:
                st.success(f"✅ {mensaje_pbi}")
                
                # Mostrar preview de datasets
                with st.expander("👀 Vista previa de datasets", expanded=False):
                    for nombre, df in datasets.items():
                        st.markdown(f"**{nombre}** ({len(df)} registros)")
                        st.dataframe(df.head(3), use_container_width=True)
                
                # Guardar en session_state para descarga
                st.session_state["powerbi_datasets"] = datasets
            else:
                st.error(f"❌ {mensaje_pbi}")
    
    with col2:
        if "powerbi_datasets" in st.session_state:
            import io
            # Crear Excel en memoria
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                for nombre, df in st.session_state["powerbi_datasets"].items():
                    if not df.empty:
                        df.to_excel(writer, sheet_name=nombre[:31], index=False)
            
            st.download_button(
                "⬇️ Descargar Excel para Power BI",
                data=buffer.getvalue(),
                file_name=f"powerbi_data_{resumen.id_evaluacion}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                help="Archivo Excel con múltiples hojas listo para importar en Power BI"
            )


# ==================== 4. PREDICCIÓN DE RIESGO ====================

def _render_prediccion_riesgo(eval_id: str, modelo: str):
    """Renderiza la sección de predicción de riesgo."""
    
    st.markdown("### 🔮 Predicción de Evolución del Riesgo")
    st.markdown("""
    Proyecta cómo evolucionará el riesgo en los próximos meses,
    tanto si se implementan controles como si no se toman acciones.
    """)
    
    # Cargar resultado guardado
    resultado_guardado = cargar_resultado_ia(eval_id, "prediccion_riesgo")
    prediccion_actual = None
    
    if resultado_guardado:
        datos = resultado_guardado["datos"]
        prediccion_actual = PrediccionRiesgo(
            id_evaluacion=datos.get("id_evaluacion", eval_id),
            fecha_generacion=resultado_guardado["fecha"],
            riesgo_actual=datos.get("riesgo_actual", 10.0),
            proyeccion_sin_controles=datos.get("proyeccion_sin_controles", []),
            proyeccion_con_controles=datos.get("proyeccion_con_controles", []),
            factores_incremento=datos.get("factores_incremento", []),
            factores_mitigacion=datos.get("factores_mitigacion", []),
            recomendacion=datos.get("recomendacion", ""),
            modelo_ia=resultado_guardado["modelo"]
        )
    
    meses = st.slider("Meses de proyección:", min_value=3, max_value=12, value=6)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        generar = st.button(
            "📈 Generar Predicción" if not prediccion_actual else "🔄 Regenerar Predicción",
            type="primary" if not prediccion_actual else "secondary",
            use_container_width=True
        )
    with col2:
        if prediccion_actual:
            st.caption(f"📅 {resultado_guardado['fecha'][:10]}")
    
    if generar:
        with st.spinner("Analizando tendencias y generando predicción..."):
            exito, prediccion, mensaje = generar_prediccion_riesgo(eval_id, meses, modelo)
        
        if exito and prediccion:
            guardar_resultado_ia(eval_id, "prediccion_riesgo", prediccion.to_dict(), modelo)
            st.success(f"✅ {mensaje}")
            st.rerun()
        else:
            st.error(f"❌ {mensaje}")
    
    if prediccion_actual:
        _mostrar_prediccion_riesgo(prediccion_actual)


def _mostrar_prediccion_riesgo(prediccion):
    """Muestra la predicción de riesgo con gráficos."""
    
    st.markdown(f"**Riesgo Actual:** {prediccion.riesgo_actual:.1f} / 25")
    st.markdown(f"**Modelo:** {prediccion.modelo_ia}")
    
    # Crear gráfico de proyección
    df_sin = pd.DataFrame(prediccion.proyeccion_sin_controles)
    df_con = pd.DataFrame(prediccion.proyeccion_con_controles)
    
    fig = go.Figure()
    
    # Línea sin controles
    if not df_sin.empty:
        fig.add_trace(go.Scatter(
            x=df_sin["mes"],
            y=df_sin["riesgo"],
            mode='lines+markers',
            name='Sin controles',
            line=dict(color='red', width=3),
            marker=dict(size=10)
        ))
    
    # Línea con controles
    if not df_con.empty:
        fig.add_trace(go.Scatter(
            x=df_con["mes"],
            y=df_con["riesgo"],
            mode='lines+markers',
            name='Con controles',
            line=dict(color='green', width=3),
            marker=dict(size=10)
        ))
    
    # Línea de riesgo actual
    fig.add_hline(
        y=prediccion.riesgo_actual,
        line_dash="dash",
        line_color="blue",
        annotation_text=f"Riesgo actual: {prediccion.riesgo_actual:.1f}"
    )
    
    # Zonas de riesgo
    fig.add_hrect(y0=20, y1=25, fillcolor="red", opacity=0.1, annotation_text="CRÍTICO")
    fig.add_hrect(y0=12, y1=20, fillcolor="orange", opacity=0.1, annotation_text="ALTO")
    fig.add_hrect(y0=6, y1=12, fillcolor="yellow", opacity=0.1, annotation_text="MEDIO")
    fig.add_hrect(y0=0, y1=6, fillcolor="green", opacity=0.1, annotation_text="BAJO")
    
    fig.update_layout(
        title="Proyección de Riesgo",
        xaxis_title="Meses",
        yaxis_title="Nivel de Riesgo",
        yaxis=dict(range=[0, 25]),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tablas de proyección
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ❌ Sin Implementar Controles")
        if not df_sin.empty:
            st.dataframe(df_sin, use_container_width=True)
    
    with col2:
        st.markdown("#### ✅ Con Controles Implementados")
        if not df_con.empty:
            st.dataframe(df_con, use_container_width=True)
    
    # Factores
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Factores de Incremento")
        for factor in prediccion.factores_incremento:
            st.markdown(f"- ⚠️ {factor}")
    
    with col2:
        st.markdown("#### 📉 Factores de Mitigación")
        for factor in prediccion.factores_mitigacion:
            st.markdown(f"- ✅ {factor}")
    
    # Recomendación
    st.info(f"💡 **Recomendación:** {prediccion.recomendacion}")


# ==================== 5. PRIORIZACIÓN DE CONTROLES ====================

def _render_priorizacion_controles(eval_id: str, modelo: str):
    """Renderiza la sección de priorización de controles."""
    
    st.markdown("### 🎯 Priorización Inteligente de Controles")
    st.markdown("""
    Ordena los controles recomendados por su retorno de inversión en seguridad (ROI).
    Considera el número de riesgos que mitiga, el costo y tiempo de implementación.
    """)
    
    # Cargar resultado guardado
    resultado_guardado = cargar_resultado_ia(eval_id, "priorizacion_controles")
    controles_actual = None
    
    if resultado_guardado:
        datos = resultado_guardado["datos"]
        if "controles" in datos and datos["controles"]:
            controles_actual = [
                ControlPriorizado(
                    codigo=c.get("codigo", ""),
                    nombre=c.get("nombre", ""),
                    categoria=c.get("categoria", ""),
                    riesgos_que_mitiga=c.get("riesgos_que_mitiga", 0),
                    activos_afectados=c.get("activos_afectados", []),
                    costo_estimado=c.get("costo_estimado", "MEDIO"),
                    tiempo_implementacion=c.get("tiempo_implementacion", ""),
                    roi_seguridad=c.get("roi_seguridad", 3),
                    justificacion=c.get("justificacion", ""),
                    orden_prioridad=c.get("orden_prioridad", 0)
                ) for c in datos["controles"]
            ]
    
    col1, col2 = st.columns([3, 1])
    with col1:
        generar = st.button(
            "⚡ Generar Priorización" if not controles_actual else "🔄 Regenerar Priorización",
            type="primary" if not controles_actual else "secondary",
            use_container_width=True
        )
    with col2:
        if controles_actual:
            st.caption(f"📅 {resultado_guardado['fecha'][:10]}")
    
    if generar:
        with st.spinner("Analizando controles y calculando prioridades..."):
            exito, controles, mensaje = generar_priorizacion_controles(eval_id, modelo)
        
        if exito and controles:
            # Guardar en BD
            datos_guardar = {"controles": [c.__dict__ for c in controles]}
            guardar_resultado_ia(eval_id, "priorizacion_controles", datos_guardar, modelo)
            st.success(f"✅ {mensaje}")
            st.rerun()
        else:
            st.error(f"❌ {mensaje}")
    
    if controles_actual:
        _mostrar_priorizacion_controles(controles_actual)


def _mostrar_priorizacion_controles(controles):
    """Muestra la lista priorizada de controles."""
    
    # Métricas resumen
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Controles", len(controles))
    with col2:
        roi_5 = sum(1 for c in controles if c.roi_seguridad == 5)
        st.metric("Controles ROI Máximo", roi_5)
    with col3:
        bajo_costo = sum(1 for c in controles if c.costo_estimado == "BAJO")
        st.metric("Bajo Costo", bajo_costo)
    
    st.divider()
    
    # Lista de controles
    for ctrl in controles[:15]:  # Mostrar top 15
        with st.expander(
            f"#{ctrl.orden_prioridad} [{ctrl.codigo}] {ctrl.nombre} | ROI: {'⭐' * ctrl.roi_seguridad}"
        ):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"**Categoría:** {ctrl.categoria}")
                st.markdown(f"**Riesgos que mitiga:** {ctrl.riesgos_que_mitiga}")
            
            with col2:
                color_costo = "🟢" if ctrl.costo_estimado == "BAJO" else "🟡" if ctrl.costo_estimado == "MEDIO" else "🔴"
                st.markdown(f"**Costo:** {color_costo} {ctrl.costo_estimado}")
                st.markdown(f"**Tiempo:** {ctrl.tiempo_implementacion}")
            
            with col3:
                st.markdown(f"**ROI Seguridad:** {'⭐' * ctrl.roi_seguridad}")
            
            st.markdown(f"**Justificación:** {ctrl.justificacion}")
            st.markdown(f"**Activos afectados:** {', '.join(ctrl.activos_afectados[:5])}")
    
    # Gráfico de ROI vs Costo
    df_controles = pd.DataFrame([{
        "Código": c.codigo,
        "Nombre": c.nombre[:30],
        "ROI": c.roi_seguridad,
        "Costo": {"BAJO": 1, "MEDIO": 2, "ALTO": 3}.get(c.costo_estimado, 2),
        "Riesgos": c.riesgos_que_mitiga
    } for c in controles[:10]])
    
    if not df_controles.empty:
        fig = px.scatter(
            df_controles,
            x="Costo",
            y="ROI",
            size="Riesgos",
            hover_name="Nombre",
            color="ROI",
            title="Análisis Costo-Beneficio de Controles",
            labels={"Costo": "Costo (1=Bajo, 3=Alto)", "ROI": "ROI de Seguridad"},
            color_continuous_scale="RdYlGn"
        )
        fig.update_layout(
            xaxis=dict(tickvals=[1, 2, 3], ticktext=["BAJO", "MEDIO", "ALTO"])
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Resumen de implementación
    st.markdown("### 📋 Resumen de Implementación Sugerida")
    
    prioridad_1 = [c for c in controles if c.roi_seguridad >= 4 and c.costo_estimado == "BAJO"]
    prioridad_2 = [c for c in controles if c.roi_seguridad >= 4 and c.costo_estimado == "MEDIO"]
    prioridad_3 = [c for c in controles if c.roi_seguridad >= 3 and c.costo_estimado == "ALTO"]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🚀 Fase 1 (Quick Wins)")
        st.markdown("*Bajo costo, alto impacto*")
        for c in prioridad_1[:5]:
            st.markdown(f"- [{c.codigo}] {c.nombre[:25]}")
    
    with col2:
        st.markdown("#### 📈 Fase 2 (Mediano Plazo)")
        st.markdown("*Inversión moderada*")
        for c in prioridad_2[:5]:
            st.markdown(f"- [{c.codigo}] {c.nombre[:25]}")
    
    with col3:
        st.markdown("#### 🎯 Fase 3 (Estratégico)")
        st.markdown("*Proyectos mayores*")
        for c in prioridad_3[:5]:
            st.markdown(f"- [{c.codigo}] {c.nombre[:25]}")
