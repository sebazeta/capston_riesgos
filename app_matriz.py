"""
PROYECTO TITA - Matriz de Riesgos MAGERIT
Versión: Matriz de Referencia

Replica exactamente la estructura de la matriz Excel de referencia:
1. CRITERIOS DE VALORACIÓN - Escalas de medición
2. ACTIVOS - Inventario de infraestructura  
3. IDENTIFICACION_VALORACION - Valoración D/I/C + Criticidad
4. VULNERABILIDADES_AMENAZAS - Vulnerabilidades + Degradación + Impacto
5. RIESGO - Frecuencia × Impacto por amenaza
6. MAPA_RIESGOS - Visualización matriz
7. RIESGO_ACTIVOS - Agregación: Actual, Objetivo, Límite
8. SALVAGUARDAS - Controles recomendados
9. DASHBOARDS - Visualización ejecutiva
10. NIVEL_MADUREZ - Cálculo de madurez organizacional
11. COMPARATIVAS - Reevaluación vs evaluación anterior
12. MATRIZ_EXCEL - Exportación y visualización completa
13. RESUMEN_EJECUTIVO - Informe para gerencia generado por IA
"""
import json
import datetime as dt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
import io
import time

# Importar servicios
from services.database_service import get_connection, read_table
from services.evaluacion_service import crear_evaluacion, get_evaluaciones
from services.activo_service import crear_activo, editar_activo, eliminar_activo, get_activo
from services.cuestionario_dic_service import (
    get_banco_preguntas_tipo, procesar_cuestionario_dic,
    guardar_respuestas_dic, get_respuestas_previas, get_estadisticas_banco,
    BANCO_PREGUNTAS_DIC
)
from services.carga_masiva_service import (
    procesar_json,
    procesar_excel,
    generar_plantilla_json,
    generar_plantilla_excel,
    get_campos_info,
    ResultadoCarga
)
from services.matriz_service import (
    init_matriz_tables,
    # Constantes
    ESCALA_DISPONIBILIDAD, ESCALA_INTEGRIDAD, ESCALA_CONFIDENCIALIDAD,
    ESCALA_CRITICIDAD, ESCALA_FRECUENCIA, ESCALA_DEGRADACION,
    VALOR_DIC, VALOR_DIC_INVERSO, VALOR_FREQ, LIMITE_RIESGO, FACTOR_REDUCCION,
    # Criterios
    get_criterios_valoracion, get_escala_degradacion,
    # Activos
    get_activos_matriz,
    # Valoración
    guardar_valoracion_dic, get_valoraciones_evaluacion, get_valoracion_activo,
    # Vulnerabilidades
    agregar_vulnerabilidad_amenaza, actualizar_vulnerabilidad_amenaza,
    eliminar_vulnerabilidad_amenaza, get_vulnerabilidades_activo,
    get_vulnerabilidades_evaluacion,
    # Riesgo
    calcular_riesgo_amenaza, get_riesgos_activo, get_riesgos_evaluacion,
    # Mapa
    generar_mapa_riesgos, get_mapa_riesgos,
    # Riesgo Activos
    calcular_riesgo_activo, get_riesgos_activos_evaluacion,
    recalcular_todos_riesgos_activos,
    # Salvaguardas
    agregar_salvaguarda, actualizar_estado_salvaguarda, eliminar_salvaguarda,
    get_salvaguardas_activo, get_salvaguardas_evaluacion,
    # Estadísticas
    get_estadisticas_evaluacion_matriz,
    # Exportar
    exportar_matriz_excel
)

# Servicios adicionales para nuevos tabs
from services.maturity_service import (
    calcular_madurez_evaluacion, guardar_madurez, get_madurez_evaluacion,
    comparar_madurez, guardar_reevaluacion, get_historial_reevaluaciones
)
from services.ia_advanced_service import generar_resumen_ejecutivo

# Importar catálogos para Tab 1
from services.ollama_magerit_service import get_catalogo_amenazas, get_catalogo_controles

# ==================== CONFIGURACIÓN ====================

st.set_page_config(
    page_title="TITA - Matriz MAGERIT",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar tablas
init_matriz_tables()

# ==================== ESTILOS ====================

st.markdown("""
<style>
    /* Tema general */
    .main { padding: 1rem 2rem; }
    
    /* Headers de tab */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        font-weight: 600;
    }
    
    /* Cards de métricas */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .metric-card h2 { margin: 0; font-size: 2.5rem; }
    .metric-card p { margin: 0; opacity: 0.9; }
    
    /* Colores de criticidad */
    .criticidad-alta { background-color: #ff4444 !important; color: white !important; }
    .criticidad-media { background-color: #ffbb33 !important; color: black !important; }
    .criticidad-baja { background-color: #00C851 !important; color: white !important; }
    .criticidad-nula { background-color: #33b5e5 !important; color: white !important; }
    
    /* Tablas estilizadas */
    .dataframe { font-size: 0.9rem; }
    
    /* Badge de estado */
    .badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-urgente { background: #ff4444; color: white; }
    .badge-atencion { background: #ffbb33; color: black; }
    .badge-aceptable { background: #00C851; color: white; }
</style>
""", unsafe_allow_html=True)


# ==================== SIDEBAR ====================

with st.sidebar:
    st.title("🛡️ TITA Matriz")
    st.markdown("---")
    
    # Selector de evaluación
    st.subheader("📋 Evaluación")
    evaluaciones = get_evaluaciones()
    
    if evaluaciones.empty:
        st.warning("No hay evaluaciones. Crea una nueva.")
        with st.expander("➕ Crear Evaluación", expanded=True):
            nombre_eval = st.text_input("Nombre", key="nueva_eval_nombre")
            desc_eval = st.text_area("Descripción", key="nueva_eval_desc")
            responsable_eval = st.text_input("Responsable", key="nueva_eval_responsable")
            if st.button("Crear Evaluación", type="primary"):
                if nombre_eval and responsable_eval:
                    eval_id = crear_evaluacion(nombre_eval, desc_eval, responsable_eval)
                    st.success(f"✅ Evaluación creada: {eval_id}")
                    st.rerun()
                else:
                    st.error("Ingresa nombre y responsable")
        st.stop()
    
    # Seleccionar evaluación activa
    opciones_eval = evaluaciones["Nombre"].tolist()
    ids_eval = evaluaciones["ID_Evaluacion"].tolist()
    
    idx_seleccionado = st.selectbox(
        "Seleccionar evaluación",
        range(len(opciones_eval)),
        format_func=lambda i: opciones_eval[i],
        key="eval_selector"
    )
    
    ID_EVALUACION = ids_eval[idx_seleccionado]
    NOMBRE_EVALUACION = opciones_eval[idx_seleccionado]
    
    st.info(f"📌 **ID:** {ID_EVALUACION}")
    
    # Editar o eliminar evaluación actual
    col_edit, col_del = st.columns(2)
    with col_edit:
        if st.button("✏️ Editar", key="btn_editar_eval", use_container_width=True):
            st.session_state["mostrar_editar_eval"] = True
    with col_del:
        if st.button("🗑️ Eliminar", key="btn_eliminar_eval", type="secondary", use_container_width=True):
            st.session_state["mostrar_confirmar_eliminar"] = True
    
    # Modal para editar evaluación
    if st.session_state.get("mostrar_editar_eval", False):
        with st.expander("✏️ Editar Evaluación", expanded=True):
            eval_actual = evaluaciones[evaluaciones["ID_Evaluacion"] == ID_EVALUACION].iloc[0]
            
            nuevo_nombre = st.text_input("Nombre", value=eval_actual["Nombre"], key="edit_nombre")
            nueva_desc = st.text_area("Descripción", value=eval_actual.get("Descripcion", ""), key="edit_desc")
            nuevo_resp = st.text_input("Responsable", value=eval_actual.get("Responsable", ""), key="edit_resp")
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("💾 Guardar", key="save_edit", type="primary", use_container_width=True):
                    if nuevo_nombre and nuevo_resp:
                        from services.evaluacion_service import actualizar_evaluacion
                        if actualizar_evaluacion(ID_EVALUACION, nuevo_nombre, nueva_desc, nuevo_resp):
                            st.success("✅ Evaluación actualizada")
                            st.session_state["mostrar_editar_eval"] = False
                            st.rerun()
                        else:
                            st.error("❌ Error al actualizar")
                    else:
                        st.error("⚠️ Nombre y responsable son obligatorios")
            with col_cancel:
                if st.button("❌ Cancelar", key="cancel_edit", use_container_width=True):
                    st.session_state["mostrar_editar_eval"] = False
                    st.rerun()
    
    # Modal para confirmar eliminación
    if st.session_state.get("mostrar_confirmar_eliminar", False):
        with st.expander("⚠️ Confirmar Eliminación", expanded=True):
            st.warning(f"""
            **¿Estás seguro de eliminar la evaluación "{NOMBRE_EVALUACION}"?**
            
            Se eliminarán:
            - Todos los activos de la evaluación
            - Todas las respuestas del cuestionario
            - Todos los análisis de riesgo
            - Todos los resultados MAGERIT
            - Datos de madurez
            
            **Esta acción NO se puede deshacer.**
            """)
            
            col_confirm, col_cancel = st.columns(2)
            with col_confirm:
                if st.button("🗑️ SÍ, ELIMINAR", key="confirm_delete", type="primary", use_container_width=True):
                    from services.evaluacion_service import eliminar_evaluacion
                    if eliminar_evaluacion(ID_EVALUACION):
                        st.success("✅ Evaluación eliminada")
                        st.session_state["mostrar_confirmar_eliminar"] = False
                        st.rerun()
                    else:
                        st.error("❌ Error al eliminar")
            with col_cancel:
                if st.button("❌ Cancelar", key="cancel_delete", use_container_width=True):
                    st.session_state["mostrar_confirmar_eliminar"] = False
                    st.rerun()
    
    # Crear nueva evaluación
    with st.expander("➕ Nueva Evaluación"):
        nombre_eval = st.text_input("Nombre", key="sidebar_eval_nombre")
        desc_eval = st.text_area("Descripción", key="sidebar_eval_desc")
        responsable_eval = st.text_input("Responsable", key="sidebar_eval_responsable", placeholder="Nombre del responsable")
        if st.button("Crear", key="sidebar_crear_eval"):
            if nombre_eval and responsable_eval:
                eval_id = crear_evaluacion(nombre_eval, desc_eval, responsable_eval)
                st.success(f"✅ Creada: {eval_id}")
                st.rerun()
            elif not responsable_eval:
                st.error("⚠️ El campo Responsable es obligatorio")
    
    st.markdown("---")
    
    # ==================== FILTRO GLOBAL DE ACTIVOS ====================
    st.subheader("🎯 Filtro de Activo")
    st.caption("Aplica a todos los tabs")
    
    # Inicializar variable de session_state
    if "activo_filtro_global" not in st.session_state:
        st.session_state["activo_filtro_global"] = "TODOS"
    
    activos_eval = get_activos_matriz(ID_EVALUACION)
    if not activos_eval.empty:
        # Crear lista con opción "TODOS" al inicio
        opciones_activos = ["TODOS"] + activos_eval["ID_Activo"].tolist()
        activos_dict_filtro = {"TODOS": "🌐 Todos los activos"}
        activos_dict_filtro.update(dict(zip(activos_eval["ID_Activo"], activos_eval["Nombre_Activo"])))
        
        activo_filtro_sel = st.selectbox(
            "Seleccionar activo",
            opciones_activos,
            format_func=lambda x: activos_dict_filtro.get(x, x),
            index=opciones_activos.index(st.session_state["activo_filtro_global"]) if st.session_state["activo_filtro_global"] in opciones_activos else 0,
            key="filtro_activo_sidebar",
            label_visibility="collapsed"
        )
        
        st.session_state["activo_filtro_global"] = activo_filtro_sel
        
        # Mostrar badge del filtro activo
        if activo_filtro_sel == "TODOS":
            st.info("📊 **Todos los activos**")
        else:
            st.success(f"🎯 **Filtrado:**\n{activos_dict_filtro[activo_filtro_sel][:30]}...")
    else:
        st.warning("Sin activos")
        st.session_state["activo_filtro_global"] = "TODOS"
    
    st.markdown("---")
    
    # Estadísticas rápidas
    stats = get_estadisticas_evaluacion_matriz(ID_EVALUACION)
    st.subheader("📊 Resumen")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Activos", stats["total_activos"])
        st.metric("Vulnerab.", stats["total_vulnerabilidades"])
    with col2:
        st.metric("Valorados", f"{stats['pct_valorados']:.0f}%")
        st.metric("Urgentes", stats["activos_urgentes"])
    
    if stats["riesgo_promedio"] > 0:
        color = "🔴" if stats["riesgo_promedio"] > LIMITE_RIESGO else "🟢"
        st.metric(f"{color} Riesgo Prom.", f"{stats['riesgo_promedio']:.2f}")
    
    st.markdown("---")
    
    # Exportar
    st.subheader("📥 Exportar")
    if st.button("📊 Descargar Excel", type="secondary"):
        excel_bytes = exportar_matriz_excel(ID_EVALUACION, NOMBRE_EVALUACION)
        st.download_button(
            "💾 Guardar Excel",
            data=excel_bytes,
            file_name=f"Matriz_{NOMBRE_EVALUACION}_{dt.date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# ==================== TABS PRINCIPALES ====================

# Los 13 tabs que replican las hojas de la matriz + extras
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "📏 1. Criterios",
    "📦 2. Activos",
    "⚖️ 3. Valoración D/I/C",
    "🔓 4. Vulnerabilidades",
    "⚡ 5. Riesgo",
    "🗺️ 6. Mapa Riesgos",
    "📊 7. Riesgo Activos",
    "🛡️ 8. Salvaguardas",
    "🎯 9. Madurez",
    "🔄 10. Comparativa"
])


# ==================== TAB 1: CRITERIOS DE VALORACIÓN ====================

with tab1:
    st.header("📏 Criterios de Valoración")
    st.markdown("""
    **Propósito:** Define las escalas de medición para todo el modelo MAGERIT.
    Estas escalas son la referencia para valorar activos, degradación y frecuencia.
    """)
    
    # Mostrar escalas en columnas
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔵 Disponibilidad (D)")
        df_d = pd.DataFrame(ESCALA_DISPONIBILIDAD)
        st.dataframe(
            df_d.rename(columns={"nivel": "Nivel", "valor": "Valor", "descripcion": "Descripción"}),
            use_container_width=True,
            hide_index=True
        )
        
        st.subheader("🟢 Integridad (I)")
        df_i = pd.DataFrame(ESCALA_INTEGRIDAD)
        st.dataframe(
            df_i.rename(columns={"nivel": "Nivel", "valor": "Valor", "descripcion": "Descripción"}),
            use_container_width=True,
            hide_index=True
        )
    
    with col2:
        st.subheader("🟣 Confidencialidad (C)")
        df_c = pd.DataFrame(ESCALA_CONFIDENCIALIDAD)
        st.dataframe(
            df_c.rename(columns={"nivel": "Nivel", "valor": "Valor", "descripcion": "Descripción"}),
            use_container_width=True,
            hide_index=True
        )
        
        st.subheader("⭐ Criticidad")
        df_crit = pd.DataFrame(ESCALA_CRITICIDAD)
        st.dataframe(
            df_crit.rename(columns={"nivel": "Nivel", "valor": "Valor", "criterio": "Criterio"}),
            use_container_width=True,
            hide_index=True
        )
    
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("📅 Frecuencia")
        df_f = pd.DataFrame(ESCALA_FRECUENCIA)
        st.dataframe(
            df_f.rename(columns={"nivel": "Nivel", "valor": "Valor", "descripcion": "Descripción"}),
            use_container_width=True,
            hide_index=True
        )
    
    with col4:
        st.subheader("📉 Degradación")
        df_deg = pd.DataFrame(ESCALA_DEGRADACION)
        st.dataframe(
            df_deg.rename(columns={"rango": "Rango", "descripcion": "Descripción"}),
            use_container_width=True,
            hide_index=True
        )
    
    st.markdown("---")
    
    # Fórmulas clave
    st.subheader("📐 Fórmulas del Modelo")
    
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        st.markdown("""
        **Fórmulas de Cálculo:**
        
        1. **CRITICIDAD** = `MAX(D, I, C)`
        2. **IMPACTO** = `CRITICIDAD × MAX(Deg_D, Deg_I, Deg_C)`
        3. **RIESGO** = `FRECUENCIA × IMPACTO`
        4. **RIESGO_ACTIVO** = `PROMEDIO(todos los riesgos)`
        5. **OBJETIVO** = `RIESGO_ACTUAL × 0.5`
        """)
    
    with col_f2:
        st.markdown(f"""
        **Constantes Organizacionales:**
        
        - **Límite de Riesgo:** `{LIMITE_RIESGO}`
        - **Factor de Reducción:** `{FACTOR_REDUCCION * 100:.0f}%`
        
        **Regla de Decisión:**
        - Si `RIESGO > LÍMITE` → Tratamiento Urgente ⚠️
        - Si `RIESGO ≤ LÍMITE` → Aceptable ✅
        """)
    
    st.markdown("---")
    
    # ========== CATÁLOGOS MAGERIT E ISO 27002 ==========
    st.header("📚 Catálogos de Referencia")
    st.markdown("""
    Los siguientes catálogos son la base para identificar amenazas y recomendar controles.
    La IA utiliza estos catálogos para sus análisis.
    """)
    
    # Tabs internos para los catálogos
    cat_tab1, cat_tab2, cat_tab3, cat_tab4 = st.tabs([
        "⚠️ Amenazas",
        "🛡️ Controles ISO 27002",
        "🔒 Salvaguardas",
        "🔓 Vulnerabilidades"
    ])
    
    # ===== AMENAZAS =====
    with cat_tab1:
        st.subheader("⚠️ Catálogo de Amenazas")
        st.markdown("""
        **52 amenazas** clasificadas en 5 categorías:
        - **[N]** Desastres naturales
        - **[I]** De origen industrial
        - **[E]** Errores y fallos no intencionados
        - **[A]** Ataques intencionados
        """)
        
        # Cargar catálogo de amenazas
        catalogo_amenazas = get_catalogo_amenazas()
        
        if catalogo_amenazas:
            # Convertir a DataFrame
            data_amenazas = []
            for codigo, info in catalogo_amenazas.items():
                tipo = codigo[0] if codigo else ""
                tipo_nombre = {
                    "N": "🌊 Desastres Naturales",
                    "I": "🏭 Origen Industrial",
                    "E": "⚠️ Errores No Intencionados",
                    "A": "💀 Ataques Intencionados"
                }.get(tipo, "Otro")
                
                data_amenazas.append({
                    "Código": codigo,
                    "Amenaza": info.get("amenaza", ""),
                    "Descripción": info.get("descripcion", info.get("tipo_amenaza", "")),
                    "Tipo": tipo_nombre
                })
            
            df_amenazas = pd.DataFrame(data_amenazas)
            
            # Filtro por tipo
            tipos_unicos = df_amenazas["Tipo"].unique().tolist()
            filtro_tipo = st.multiselect(
                "Filtrar por tipo de amenaza:",
                tipos_unicos,
                default=tipos_unicos,
                key="filtro_tipo_amenaza"
            )
            
            df_filtrado = df_amenazas[df_amenazas["Tipo"].isin(filtro_tipo)]
            
            # Métricas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Amenazas", len(catalogo_amenazas))
            with col2:
                n_count = len([c for c in catalogo_amenazas.keys() if c.startswith("N")])
                st.metric("🌊 Naturales", n_count)
            with col3:
                e_count = len([c for c in catalogo_amenazas.keys() if c.startswith("E")])
                st.metric("⚠️ Errores", e_count)
            with col4:
                a_count = len([c for c in catalogo_amenazas.keys() if c.startswith("A")])
                st.metric("💀 Ataques", a_count)
            
            # Tabla
            st.dataframe(
                df_filtrado,
                use_container_width=True,
                hide_index=True,
                height=400
            )
            
            # Buscador
            with st.expander("🔍 Buscar amenaza específica"):
                buscar_amenaza = st.text_input("Buscar por código o nombre:", key="buscar_amenaza")
                if buscar_amenaza:
                    resultado = df_amenazas[
                        df_amenazas["Código"].str.contains(buscar_amenaza, case=False, na=False) |
                        df_amenazas["Amenaza"].str.contains(buscar_amenaza, case=False, na=False)
                    ]
                    if not resultado.empty:
                        st.dataframe(resultado, use_container_width=True, hide_index=True)
                    else:
                        st.warning("No se encontraron amenazas con ese criterio.")
        else:
            st.error("❌ No se pudo cargar el catálogo de amenazas. Ejecuta `seed_catalogos.py`")
    
    # ===== CONTROLES ISO 27002 =====
    with cat_tab2:
        st.subheader("🛡️ Catálogo de Controles ISO 27002:2022")
        st.markdown("""
        **93 controles** organizados en 4 dominios:
        - **5.x** Controles Organizacionales (37 controles)
        - **6.x** Controles de Personas (8 controles)
        - **7.x** Controles Físicos (14 controles)
        - **8.x** Controles Tecnológicos (34 controles)
        """)
        
        # Cargar catálogo de controles
        catalogo_controles = get_catalogo_controles()
        
        if catalogo_controles:
            # Convertir a DataFrame
            data_controles = []
            for codigo, info in catalogo_controles.items():
                # Determinar dominio por el número
                try:
                    num = int(codigo.split(".")[0])
                    dominio = {
                        5: "📋 Organizacionales",
                        6: "👥 Personas",
                        7: "🏢 Físicos",
                        8: "💻 Tecnológicos"
                    }.get(num, "Otro")
                except:
                    dominio = "Otro"
                
                data_controles.append({
                    "Código": codigo,
                    "Control": info.get("nombre", ""),
                    "Categoría": info.get("categoria", ""),
                    "Dominio": dominio
                })
            
            df_controles = pd.DataFrame(data_controles)
            
            # Filtro por dominio
            dominios_unicos = df_controles["Dominio"].unique().tolist()
            filtro_dominio = st.multiselect(
                "Filtrar por dominio:",
                dominios_unicos,
                default=dominios_unicos,
                key="filtro_dominio_control"
            )
            
            df_controles_filtrado = df_controles[df_controles["Dominio"].isin(filtro_dominio)]
            
            # Métricas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Controles", len(catalogo_controles))
            with col2:
                org = len([c for c in catalogo_controles.keys() if c.startswith("5.")])
                st.metric("📋 Organizacionales", org)
            with col3:
                fis = len([c for c in catalogo_controles.keys() if c.startswith("7.")])
                st.metric("🏢 Físicos", fis)
            with col4:
                tec = len([c for c in catalogo_controles.keys() if c.startswith("8.")])
                st.metric("💻 Tecnológicos", tec)
            
            # Tabla
            st.dataframe(
                df_controles_filtrado,
                use_container_width=True,
                hide_index=True,
                height=400
            )
            
            # Buscador
            with st.expander("🔍 Buscar control específico"):
                buscar_control = st.text_input("Buscar por código o nombre:", key="buscar_control")
                if buscar_control:
                    resultado = df_controles[
                        df_controles["Código"].str.contains(buscar_control, case=False, na=False) |
                        df_controles["Control"].str.contains(buscar_control, case=False, na=False)
                    ]
                    if not resultado.empty:
                        st.dataframe(resultado, use_container_width=True, hide_index=True)
                    else:
                        st.warning("No se encontraron controles con ese criterio.")
        else:
            st.error("❌ No se pudo cargar el catálogo de controles. Ejecuta `seed_catalogos.py`")
    
    # ===== SALVAGUARDAS =====
    with cat_tab3:
        st.subheader("🔒 Catálogo de Salvaguardas")
        st.markdown("""
        Las salvaguardas son medidas de protección para reducir el riesgo.
        Están organizadas por tipo de activo a proteger.
        """)
        
        # Catálogo completo de Salvaguardas
        salvaguardas_magerit = {
            "H": {
                "nombre": "Protecciones Generales",
                "descripcion": "Medidas de carácter general aplicables a toda la organización",
                "salvaguardas": [
                    {"codigo": "H.1", "nombre": "Política de seguridad", "descripcion": "Documento que establece el compromiso de la dirección y los objetivos de seguridad"},
                    {"codigo": "H.2", "nombre": "Normativa de seguridad", "descripcion": "Conjunto de normas que desarrollan la política de seguridad"},
                    {"codigo": "H.3", "nombre": "Procedimientos de seguridad", "descripcion": "Instrucciones detalladas para realizar tareas de seguridad"},
                    {"codigo": "H.4", "nombre": "Proceso de autorización", "descripcion": "Mecanismo formal para autorizar el acceso a recursos"},
                    {"codigo": "H.5", "nombre": "Auditorías de seguridad", "descripcion": "Revisiones periódicas del cumplimiento de la normativa"}
                ]
            },
            "D": {
                "nombre": "Protección de los Datos/Información",
                "descripcion": "Salvaguardas para proteger la información almacenada y procesada",
                "salvaguardas": [
                    {"codigo": "D.1", "nombre": "Clasificación de la información", "descripcion": "Etiquetado y tratamiento según nivel de confidencialidad"},
                    {"codigo": "D.2", "nombre": "Cifrado de información", "descripcion": "Uso de criptografía para proteger datos sensibles"},
                    {"codigo": "D.3", "nombre": "Copias de seguridad (backup)", "descripcion": "Respaldos periódicos de información crítica"},
                    {"codigo": "D.4", "nombre": "Borrado seguro", "descripcion": "Destrucción irrecuperable de información cuando ya no se necesita"},
                    {"codigo": "D.5", "nombre": "Firma electrónica", "descripcion": "Garantía de autenticidad e integridad de documentos"},
                    {"codigo": "D.6", "nombre": "Control de acceso a datos", "descripcion": "Restricción de acceso basada en necesidad de conocer"}
                ]
            },
            "S": {
                "nombre": "Protección de los Servicios",
                "descripcion": "Salvaguardas para proteger los servicios que presta la organización",
                "salvaguardas": [
                    {"codigo": "S.1", "nombre": "Disponibilidad del servicio", "descripcion": "Mecanismos de alta disponibilidad y redundancia"},
                    {"codigo": "S.2", "nombre": "Continuidad del servicio", "descripcion": "Planes de contingencia para mantener operación"},
                    {"codigo": "S.3", "nombre": "Monitorización del servicio", "descripcion": "Vigilancia continua del estado del servicio"},
                    {"codigo": "S.4", "nombre": "Gestión de incidentes", "descripcion": "Procedimiento para detectar, reportar y resolver incidentes"},
                    {"codigo": "S.5", "nombre": "SLA y acuerdos de nivel de servicio", "descripcion": "Compromisos formales de disponibilidad y rendimiento"}
                ]
            },
            "SW": {
                "nombre": "Protección de las Aplicaciones (Software)",
                "descripcion": "Salvaguardas para proteger el software y aplicaciones",
                "salvaguardas": [
                    {"codigo": "SW.1", "nombre": "Desarrollo seguro", "descripcion": "Metodología de desarrollo con seguridad integrada (SDLC)"},
                    {"codigo": "SW.2", "nombre": "Pruebas de seguridad", "descripcion": "Testing de vulnerabilidades antes de producción"},
                    {"codigo": "SW.3", "nombre": "Gestión de parches", "descripcion": "Actualización oportuna de software para corregir vulnerabilidades"},
                    {"codigo": "SW.4", "nombre": "Control de versiones", "descripcion": "Gestión de cambios y versiones del software"},
                    {"codigo": "SW.5", "nombre": "Antimalware", "descripcion": "Protección contra virus, ransomware y software malicioso"},
                    {"codigo": "SW.6", "nombre": "Control de instalación", "descripcion": "Restricción de software autorizado (whitelisting)"},
                    {"codigo": "SW.7", "nombre": "Análisis de código", "descripcion": "Revisión estática y dinámica del código fuente"}
                ]
            },
            "HW": {
                "nombre": "Protección de los Equipos (Hardware)",
                "descripcion": "Salvaguardas para proteger equipos físicos",
                "salvaguardas": [
                    {"codigo": "HW.1", "nombre": "Inventario de equipos", "descripcion": "Registro actualizado de todos los equipos"},
                    {"codigo": "HW.2", "nombre": "Mantenimiento preventivo", "descripcion": "Revisiones periódicas para prevenir fallos"},
                    {"codigo": "HW.3", "nombre": "Protección física", "descripcion": "Seguridad física contra robo y manipulación"},
                    {"codigo": "HW.4", "nombre": "Equipos de respaldo", "descripcion": "Hardware redundante para contingencias"},
                    {"codigo": "HW.5", "nombre": "Control de acceso físico", "descripcion": "Restricción de acceso a equipos críticos"},
                    {"codigo": "HW.6", "nombre": "Etiquetado y seguimiento", "descripcion": "Identificación y trazabilidad de equipos"}
                ]
            },
            "COM": {
                "nombre": "Protección de las Comunicaciones",
                "descripcion": "Salvaguardas para proteger redes y comunicaciones",
                "salvaguardas": [
                    {"codigo": "COM.1", "nombre": "Firewall perimetral", "descripcion": "Control de tráfico entrante y saliente"},
                    {"codigo": "COM.2", "nombre": "Segmentación de red", "descripcion": "Separación de redes por zonas de seguridad (VLANs)"},
                    {"codigo": "COM.3", "nombre": "VPN", "descripcion": "Túneles cifrados para comunicaciones remotas"},
                    {"codigo": "COM.4", "nombre": "IDS/IPS", "descripcion": "Sistemas de detección y prevención de intrusos"},
                    {"codigo": "COM.5", "nombre": "Control de acceso a red (NAC)", "descripcion": "Autenticación de dispositivos antes de conectar"},
                    {"codigo": "COM.6", "nombre": "Cifrado de comunicaciones (TLS/SSL)", "descripcion": "Protección de datos en tránsito"},
                    {"codigo": "COM.7", "nombre": "Protección WiFi", "descripcion": "Seguridad en redes inalámbricas (WPA3)"}
                ]
            },
            "SI": {
                "nombre": "Protección de los Soportes de Información",
                "descripcion": "Salvaguardas para medios de almacenamiento",
                "salvaguardas": [
                    {"codigo": "SI.1", "nombre": "Cifrado de discos", "descripcion": "Encriptación de dispositivos de almacenamiento"},
                    {"codigo": "SI.2", "nombre": "Control de medios extraíbles", "descripcion": "Política de uso de USB, discos externos"},
                    {"codigo": "SI.3", "nombre": "Destrucción segura de soportes", "descripcion": "Borrado certificado o destrucción física"},
                    {"codigo": "SI.4", "nombre": "Almacenamiento seguro", "descripcion": "Custodia física de medios sensibles"},
                    {"codigo": "SI.5", "nombre": "Inventario de soportes", "descripcion": "Registro de medios con información clasificada"}
                ]
            },
            "AUX": {
                "nombre": "Protección de Elementos Auxiliares",
                "descripcion": "Salvaguardas para infraestructura de soporte",
                "salvaguardas": [
                    {"codigo": "AUX.1", "nombre": "SAI/UPS", "descripcion": "Sistema de alimentación ininterrumpida"},
                    {"codigo": "AUX.2", "nombre": "Generador eléctrico", "descripcion": "Suministro eléctrico de respaldo"},
                    {"codigo": "AUX.3", "nombre": "Climatización", "descripcion": "Control de temperatura y humedad en datacenter"},
                    {"codigo": "AUX.4", "nombre": "Detección y extinción de incendios", "descripcion": "Sistemas automáticos de protección contra fuego"},
                    {"codigo": "AUX.5", "nombre": "Protección contra inundaciones", "descripcion": "Drenaje y detección de agua"},
                    {"codigo": "AUX.6", "nombre": "Cableado estructurado", "descripcion": "Organización y protección del cableado"}
                ]
            },
            "L": {
                "nombre": "Protección de las Instalaciones",
                "descripcion": "Seguridad física del entorno",
                "salvaguardas": [
                    {"codigo": "L.1", "nombre": "Control de acceso físico", "descripcion": "Tarjetas, biometría, torniquetes"},
                    {"codigo": "L.2", "nombre": "Vigilancia (CCTV)", "descripcion": "Videovigilancia y grabación"},
                    {"codigo": "L.3", "nombre": "Seguridad perimetral", "descripcion": "Cercas, barreras, iluminación exterior"},
                    {"codigo": "L.4", "nombre": "Áreas seguras", "descripcion": "Zonas restringidas para equipos críticos"},
                    {"codigo": "L.5", "nombre": "Registro de visitantes", "descripcion": "Control de acceso de personal externo"},
                    {"codigo": "L.6", "nombre": "Protección del datacenter", "descripcion": "Seguridad física especializada para CPD"}
                ]
            },
            "PS": {
                "nombre": "Gestión del Personal",
                "descripcion": "Salvaguardas relacionadas con las personas",
                "salvaguardas": [
                    {"codigo": "PS.1", "nombre": "Formación en seguridad", "descripcion": "Capacitación y concienciación del personal"},
                    {"codigo": "PS.2", "nombre": "Verificación de antecedentes", "descripcion": "Investigación previa a la contratación"},
                    {"codigo": "PS.3", "nombre": "Acuerdos de confidencialidad (NDA)", "descripcion": "Compromiso legal de no divulgación"},
                    {"codigo": "PS.4", "nombre": "Segregación de funciones", "descripcion": "Separación de tareas críticas"},
                    {"codigo": "PS.5", "nombre": "Proceso de baja/desvinculación", "descripcion": "Revocación de accesos al terminar relación"},
                    {"codigo": "PS.6", "nombre": "Gestión de vacaciones/ausencias", "descripcion": "Cobertura de funciones críticas"}
                ]
            },
            "BC": {
                "nombre": "Continuidad del Negocio",
                "descripcion": "Planes de continuidad y recuperación",
                "salvaguardas": [
                    {"codigo": "BC.1", "nombre": "Plan de Continuidad de Negocio (BCP)", "descripcion": "Estrategia para mantener operaciones críticas"},
                    {"codigo": "BC.2", "nombre": "Plan de Recuperación ante Desastres (DRP)", "descripcion": "Procedimientos para restaurar sistemas"},
                    {"codigo": "BC.3", "nombre": "Sitio alternativo", "descripcion": "Ubicación de respaldo para operaciones"},
                    {"codigo": "BC.4", "nombre": "Pruebas de continuidad", "descripcion": "Simulacros periódicos de recuperación"},
                    {"codigo": "BC.5", "nombre": "RTO/RPO definidos", "descripcion": "Objetivos de tiempo y punto de recuperación"}
                ]
            },
            "G": {
                "nombre": "Gestión de la Seguridad",
                "descripcion": "Salvaguardas organizativas y de gobierno",
                "salvaguardas": [
                    {"codigo": "G.1", "nombre": "Comité de seguridad", "descripcion": "Órgano de gobierno de seguridad de la información"},
                    {"codigo": "G.2", "nombre": "CISO/Responsable de seguridad", "descripcion": "Rol dedicado a la gestión de seguridad"},
                    {"codigo": "G.3", "nombre": "Gestión de riesgos", "descripcion": "Proceso formal de análisis y tratamiento de riesgos"},
                    {"codigo": "G.4", "nombre": "Cumplimiento normativo", "descripcion": "Verificación de requisitos legales y regulatorios"},
                    {"codigo": "G.5", "nombre": "Mejora continua", "descripcion": "Ciclo PDCA para evolucionar la seguridad"}
                ]
            },
            "E": {
                "nombre": "Relaciones con Terceros",
                "descripcion": "Gestión de proveedores y terceros",
                "salvaguardas": [
                    {"codigo": "E.1", "nombre": "Evaluación de proveedores", "descripcion": "Due diligence de seguridad antes de contratar"},
                    {"codigo": "E.2", "nombre": "Cláusulas de seguridad en contratos", "descripcion": "Requisitos de seguridad en acuerdos"},
                    {"codigo": "E.3", "nombre": "Auditoría de proveedores", "descripcion": "Verificación periódica del cumplimiento"},
                    {"codigo": "E.4", "nombre": "Gestión de accesos de terceros", "descripcion": "Control de acceso de personal externo"},
                    {"codigo": "E.5", "nombre": "Acuerdos de nivel de servicio (SLA)", "descripcion": "Compromisos de seguridad con proveedores"}
                ]
            },
            "AC": {
                "nombre": "Control de Acceso",
                "descripcion": "Gestión de identidades y accesos",
                "salvaguardas": [
                    {"codigo": "AC.1", "nombre": "Autenticación robusta", "descripcion": "Contraseñas fuertes, MFA, biometría"},
                    {"codigo": "AC.2", "nombre": "Gestión de identidades (IAM)", "descripcion": "Alta, baja y modificación de usuarios"},
                    {"codigo": "AC.3", "nombre": "Principio de mínimo privilegio", "descripcion": "Solo los permisos estrictamente necesarios"},
                    {"codigo": "AC.4", "nombre": "Revisión periódica de accesos", "descripcion": "Recertificación de permisos"},
                    {"codigo": "AC.5", "nombre": "Single Sign-On (SSO)", "descripcion": "Autenticación unificada"},
                    {"codigo": "AC.6", "nombre": "Gestión de cuentas privilegiadas (PAM)", "descripcion": "Control especial de administradores"}
                ]
            },
            "MON": {
                "nombre": "Monitorización y Detección",
                "descripcion": "Vigilancia y detección de incidentes",
                "salvaguardas": [
                    {"codigo": "MON.1", "nombre": "SIEM", "descripcion": "Correlación y análisis de eventos de seguridad"},
                    {"codigo": "MON.2", "nombre": "Logs y registros de auditoría", "descripcion": "Registro de actividades para trazabilidad"},
                    {"codigo": "MON.3", "nombre": "SOC (Centro de Operaciones de Seguridad)", "descripcion": "Monitorización 24x7"},
                    {"codigo": "MON.4", "nombre": "Alertas automatizadas", "descripcion": "Notificación de eventos sospechosos"},
                    {"codigo": "MON.5", "nombre": "Threat Intelligence", "descripcion": "Información de amenazas actuales"}
                ]
            }
        }
        
        # Mostrar como cards expandibles
        total_salvaguardas = sum(len(cat["salvaguardas"]) for cat in salvaguardas_magerit.values())
        st.metric("Total Salvaguardas", total_salvaguardas)
        
        for codigo_cat, info_cat in salvaguardas_magerit.items():
            with st.expander(f"**[{codigo_cat}]** {info_cat['nombre']} ({len(info_cat['salvaguardas'])} salvaguardas)", expanded=False):
                st.markdown(f"*{info_cat['descripcion']}*")
                st.markdown("---")
                
                # Tabla de salvaguardas de esta categoría
                data_cat = []
                for salv in info_cat["salvaguardas"]:
                    data_cat.append({
                        "Código": salv["codigo"],
                        "Salvaguarda": salv["nombre"],
                        "Descripción": salv["descripcion"]
                    })
                
                df_cat = pd.DataFrame(data_cat)
                st.dataframe(df_cat, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Tabla resumen de categorías
        st.subheader("📋 Resumen por Categoría")
        data_resumen = []
        for codigo, info in salvaguardas_magerit.items():
            data_resumen.append({
                "Código": codigo,
                "Categoría": info["nombre"],
                "Salvaguardas": len(info["salvaguardas"])
            })
        
        df_resumen = pd.DataFrame(data_resumen)
        st.dataframe(df_resumen, use_container_width=True, hide_index=True)

    # ===== VULNERABILIDADES =====
    with cat_tab4:
        st.subheader("🔓 Catálogo de Vulnerabilidades por Tipo de Activo")
        st.markdown("""
        Las **vulnerabilidades** son debilidades que pueden ser explotadas por las amenazas.
        Este catálogo muestra las vulnerabilidades más comunes para cada tipo de activo según MAGERIT.
        """)
        
        # Catálogo de Vulnerabilidades organizado por tipo de activo
        vulnerabilidades_catalogo = {
            "SW": {
                "nombre": "Software / Aplicaciones",
                "icono": "💻",
                "vulnerabilidades": [
                    {"codigo": "SW-V01", "nombre": "Software desactualizado", "descripcion": "Falta de parches de seguridad en aplicaciones", "nivel": "Alto"},
                    {"codigo": "SW-V02", "nombre": "Configuración por defecto", "descripcion": "Uso de credenciales y configuraciones predeterminadas", "nivel": "Alto"},
                    {"codigo": "SW-V03", "nombre": "Inyección SQL", "descripcion": "Vulnerabilidad a inyección de código en consultas SQL", "nivel": "Alto"},
                    {"codigo": "SW-V04", "nombre": "Cross-Site Scripting (XSS)", "descripcion": "Ejecución de scripts maliciosos en navegador", "nivel": "Alto"},
                    {"codigo": "SW-V05", "nombre": "Autenticación débil", "descripcion": "Mecanismos de autenticación insuficientes", "nivel": "Alto"},
                    {"codigo": "SW-V06", "nombre": "Falta de cifrado", "descripcion": "Datos sensibles sin encriptar", "nivel": "Alto"},
                    {"codigo": "SW-V07", "nombre": "Gestión insegura de sesiones", "descripcion": "Tokens de sesión predecibles o expuestos", "nivel": "Alto"},
                    {"codigo": "SW-V08", "nombre": "APIs expuestas", "descripcion": "Interfaces de programación sin autenticación adecuada", "nivel": "Alto"},
                    {"codigo": "SW-V09", "nombre": "Falta de validación de entrada", "descripcion": "No se validan datos de usuario", "nivel": "Alto"},
                    {"codigo": "SW-V10", "nombre": "Dependencias vulnerables", "descripcion": "Uso de librerías con vulnerabilidades conocidas", "nivel": "Medio"}
                ]
            },
            "HW": {
                "nombre": "Hardware / Equipos",
                "icono": "🖥️",
                "vulnerabilidades": [
                    {"codigo": "HW-V01", "nombre": "Firmware desactualizado", "descripcion": "BIOS/UEFI sin actualizaciones de seguridad", "nivel": "Alto"},
                    {"codigo": "HW-V02", "nombre": "Puertos USB habilitados", "descripcion": "Acceso físico a puertos sin control", "nivel": "Medio"},
                    {"codigo": "HW-V03", "nombre": "Falta de TPM", "descripcion": "Sin módulo de plataforma segura para cifrado", "nivel": "Medio"},
                    {"codigo": "HW-V04", "nombre": "Discos sin cifrar", "descripcion": "Almacenamiento local sin encriptación", "nivel": "Alto"},
                    {"codigo": "HW-V05", "nombre": "BIOS sin contraseña", "descripcion": "Configuración de hardware accesible", "nivel": "Medio"},
                    {"codigo": "HW-V06", "nombre": "Hardware obsoleto", "descripcion": "Equipos sin soporte del fabricante", "nivel": "Alto"},
                    {"codigo": "HW-V07", "nombre": "Sin protección física", "descripcion": "Equipos sin cerraduras o cables de seguridad", "nivel": "Bajo"}
                ]
            },
            "COM": {
                "nombre": "Comunicaciones / Red",
                "icono": "🌐",
                "vulnerabilidades": [
                    {"codigo": "COM-V01", "nombre": "Red sin segmentar", "descripcion": "Toda la red en un mismo segmento sin VLANs", "nivel": "Alto"},
                    {"codigo": "COM-V02", "nombre": "WiFi con WEP/WPA", "descripcion": "Protocolos de red inalámbrica obsoletos", "nivel": "Alto"},
                    {"codigo": "COM-V03", "nombre": "Puertos innecesarios abiertos", "descripcion": "Servicios expuestos sin necesidad", "nivel": "Alto"},
                    {"codigo": "COM-V04", "nombre": "Sin firewall", "descripcion": "Falta de control de tráfico perimetral", "nivel": "Alto"},
                    {"codigo": "COM-V05", "nombre": "Protocolos inseguros", "descripcion": "Uso de FTP, Telnet, HTTP sin cifrar", "nivel": "Alto"},
                    {"codigo": "COM-V06", "nombre": "DNS sin protección", "descripcion": "Vulnerable a DNS spoofing/poisoning", "nivel": "Medio"},
                    {"codigo": "COM-V07", "nombre": "Sin IDS/IPS", "descripcion": "Falta de detección de intrusiones", "nivel": "Medio"},
                    {"codigo": "COM-V08", "nombre": "VPN débil", "descripcion": "Uso de protocolos VPN obsoletos (PPTP)", "nivel": "Alto"}
                ]
            },
            "D": {
                "nombre": "Datos / Información",
                "icono": "📊",
                "vulnerabilidades": [
                    {"codigo": "D-V01", "nombre": "Datos sin clasificar", "descripcion": "Información sin etiquetas de confidencialidad", "nivel": "Medio"},
                    {"codigo": "D-V02", "nombre": "Backups sin cifrar", "descripcion": "Copias de seguridad en texto plano", "nivel": "Alto"},
                    {"codigo": "D-V03", "nombre": "Retención indefinida", "descripcion": "Datos que deberían eliminarse aún disponibles", "nivel": "Medio"},
                    {"codigo": "D-V04", "nombre": "Sin control de acceso", "descripcion": "Datos accesibles sin autorización", "nivel": "Alto"},
                    {"codigo": "D-V05", "nombre": "Transmisión sin cifrar", "descripcion": "Datos enviados en texto plano", "nivel": "Alto"},
                    {"codigo": "D-V06", "nombre": "Sin respaldo", "descripcion": "Información importante sin backup", "nivel": "Alto"},
                    {"codigo": "D-V07", "nombre": "Logs insuficientes", "descripcion": "Sin trazabilidad de acceso a datos", "nivel": "Medio"}
                ]
            },
            "S": {
                "nombre": "Servicios",
                "icono": "⚙️",
                "vulnerabilidades": [
                    {"codigo": "S-V01", "nombre": "Sin redundancia", "descripcion": "Servicio con punto único de fallo", "nivel": "Alto"},
                    {"codigo": "S-V02", "nombre": "Sin SLA definido", "descripcion": "Falta de compromisos de disponibilidad", "nivel": "Medio"},
                    {"codigo": "S-V03", "nombre": "Sin monitoreo", "descripcion": "Servicio sin vigilancia de estado", "nivel": "Alto"},
                    {"codigo": "S-V04", "nombre": "Dependencia de terceros", "descripcion": "Servicio crítico dependiente de proveedor externo", "nivel": "Medio"},
                    {"codigo": "S-V05", "nombre": "Sin plan de recuperación", "descripcion": "Falta de DRP para el servicio", "nivel": "Alto"},
                    {"codigo": "S-V06", "nombre": "Capacidad insuficiente", "descripcion": "Sin escalabilidad ante picos de demanda", "nivel": "Medio"}
                ]
            },
            "PS": {
                "nombre": "Personal",
                "icono": "👤",
                "vulnerabilidades": [
                    {"codigo": "PS-V01", "nombre": "Falta de formación", "descripcion": "Personal sin capacitación en seguridad", "nivel": "Alto"},
                    {"codigo": "PS-V02", "nombre": "Susceptibilidad a phishing", "descripcion": "Usuarios que caen en ingeniería social", "nivel": "Alto"},
                    {"codigo": "PS-V03", "nombre": "Contraseñas débiles", "descripcion": "Uso de contraseñas fáciles de adivinar", "nivel": "Alto"},
                    {"codigo": "PS-V04", "nombre": "Sin acuerdos de confidencialidad", "descripcion": "Personal sin NDA firmado", "nivel": "Medio"},
                    {"codigo": "PS-V05", "nombre": "Privilegios excesivos", "descripcion": "Usuarios con más permisos de los necesarios", "nivel": "Alto"},
                    {"codigo": "PS-V06", "nombre": "Rotación sin control", "descripcion": "Accesos no revocados al salir", "nivel": "Alto"}
                ]
            },
            "L": {
                "nombre": "Instalaciones",
                "icono": "🏢",
                "vulnerabilidades": [
                    {"codigo": "L-V01", "nombre": "Acceso físico no controlado", "descripcion": "Cualquiera puede entrar a áreas sensibles", "nivel": "Alto"},
                    {"codigo": "L-V02", "nombre": "Sin CCTV", "descripcion": "Falta de videovigilancia", "nivel": "Medio"},
                    {"codigo": "L-V03", "nombre": "Sin detección de incendios", "descripcion": "Falta de alarmas y extintores", "nivel": "Alto"},
                    {"codigo": "L-V04", "nombre": "Climatización inadecuada", "descripcion": "Datacenter sin control de temperatura", "nivel": "Alto"},
                    {"codigo": "L-V05", "nombre": "Sin protección eléctrica", "descripcion": "Falta de UPS y reguladores", "nivel": "Alto"},
                    {"codigo": "L-V06", "nombre": "Ubicación vulnerable", "descripcion": "Zona propensa a inundaciones o sismos", "nivel": "Medio"}
                ]
            },
            "AUX": {
                "nombre": "Servicios Auxiliares",
                "icono": "🔌",
                "vulnerabilidades": [
                    {"codigo": "AUX-V01", "nombre": "Sin UPS", "descripcion": "Equipos sin alimentación ininterrumpida", "nivel": "Alto"},
                    {"codigo": "AUX-V02", "nombre": "Sin generador", "descripcion": "Falta de respaldo eléctrico prolongado", "nivel": "Medio"},
                    {"codigo": "AUX-V03", "nombre": "Aire acondicionado único", "descripcion": "Sin redundancia de climatización", "nivel": "Medio"},
                    {"codigo": "AUX-V04", "nombre": "Cableado desordenado", "descripcion": "Infraestructura física sin organizar", "nivel": "Bajo"},
                    {"codigo": "AUX-V05", "nombre": "Conexión a internet única", "descripcion": "Sin ISP de respaldo", "nivel": "Alto"}
                ]
            }
        }
        
        # Resumen de vulnerabilidades
        total_vulns = sum(len(cat["vulnerabilidades"]) for cat in vulnerabilidades_catalogo.values())
        
        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            st.metric("Total Vulnerabilidades", total_vulns)
        with col_v2:
            altas = sum(1 for cat in vulnerabilidades_catalogo.values() 
                       for v in cat["vulnerabilidades"] if v["nivel"] == "Alto")
            st.metric("Altas", altas)
        with col_v3:
            medias = sum(1 for cat in vulnerabilidades_catalogo.values() 
                        for v in cat["vulnerabilidades"] if v["nivel"] == "Medio")
            st.metric("Medias", medias)
        
        st.markdown("---")
        
        # Filtros
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            nivel_filtro = st.multiselect(
                "Filtrar por nivel de riesgo:",
                ["Alto", "Medio", "Bajo", "Nulo"],
                default=["Alto", "Medio", "Bajo", "Nulo"],
                key="filtro_nivel_vuln"
            )
        
        with col_f2:
            tipos_activos = list(vulnerabilidades_catalogo.keys())
            tipo_filtro = st.multiselect(
                "Filtrar por tipo de activo:",
                tipos_activos,
                default=tipos_activos,
                format_func=lambda x: f"{vulnerabilidades_catalogo[x]['icono']} {vulnerabilidades_catalogo[x]['nombre']}",
                key="filtro_tipo_activo_vuln"
            )
        
        # Construir tabla unificada
        data_vulns_todas = []
        for codigo_cat, info_cat in vulnerabilidades_catalogo.items():
            if codigo_cat not in tipo_filtro:
                continue
                
            for vuln in info_cat["vulnerabilidades"]:
                if vuln["nivel"] not in nivel_filtro:
                    continue
                
                # Color según nivel
                if vuln["nivel"] == "Alto":
                    nivel_emoji = "🔴"
                elif vuln["nivel"] == "Medio":
                    nivel_emoji = "🟡"
                elif vuln["nivel"] == "Bajo":
                    nivel_emoji = "🟢"
                else:
                    nivel_emoji = "⚪"
                
                data_vulns_todas.append({
                    "Tipo_Activo": f"{info_cat['icono']} {info_cat['nombre']}",
                    "Código": vuln["codigo"],
                    "Vulnerabilidad": vuln["nombre"],
                    "Descripción": vuln["descripcion"],
                    "Nivel": f"{nivel_emoji} {vuln['nivel']}"
                })
        
        if data_vulns_todas:
            df_vulns_todas = pd.DataFrame(data_vulns_todas)
            
            # Buscador de texto
            buscar_vuln = st.text_input("🔍 Buscar vulnerabilidad:", placeholder="Buscar por código, nombre o descripción", key="buscar_vuln_cat")
            
            if buscar_vuln:
                mask = (
                    df_vulns_todas["Código"].str.contains(buscar_vuln, case=False, na=False) |
                    df_vulns_todas["Vulnerabilidad"].str.contains(buscar_vuln, case=False, na=False) |
                    df_vulns_todas["Descripción"].str.contains(buscar_vuln, case=False, na=False)
                )
                df_vulns_todas = df_vulns_todas[mask]
            
            # Mostrar tabla
            st.dataframe(
                df_vulns_todas,
                use_container_width=True,
                hide_index=True,
                height=500
            )
            
            st.caption(f"📊 Mostrando {len(df_vulns_todas)} vulnerabilidades")
        else:
            st.info("No hay vulnerabilidades que coincidan con los filtros seleccionados.")
        
        st.markdown("---")
        
        # Matriz resumen
        st.subheader("📊 Matriz de Vulnerabilidades por Tipo de Activo")
        
        data_matriz_v = []
        for codigo, info in vulnerabilidades_catalogo.items():
            altas = sum(1 for v in info["vulnerabilidades"] if v["nivel"] == "Alto")
            medias = sum(1 for v in info["vulnerabilidades"] if v["nivel"] == "Medio")
            bajas = sum(1 for v in info["vulnerabilidades"] if v["nivel"] == "Bajo")
            nulas = sum(1 for v in info["vulnerabilidades"] if v["nivel"] == "Nulo")
            
            data_matriz_v.append({
                "Tipo": f"{info['icono']} {info['nombre']}",
                "🔴 Altas": altas,
                "🟡 Medias": medias,
                "🟢 Bajas": bajas,
                "⚪ Nulas": nulas,
                "Total": len(info["vulnerabilidades"])
            })
        
        df_matriz_v = pd.DataFrame(data_matriz_v)
        st.dataframe(df_matriz_v, use_container_width=True, hide_index=True)


# ==================== TAB 2: ACTIVOS ====================

with tab2:
    st.header("📦 Inventario de Activos")
    st.markdown("""
    **Propósito:** Inventario detallado de activos físicos y virtuales.
    Aquí se registran todos los activos que serán evaluados.
    """)
    
    # Obtener activos de la evaluación
    activos = get_activos_matriz(ID_EVALUACION)
    
    # Obtener filtro global
    filtro_global = st.session_state.get("activo_filtro_global", "TODOS")
    
    # Aplicar filtro para métricas
    activos_metricas = activos.copy()
    if filtro_global != "TODOS" and not activos.empty:
        activos_metricas = activos_metricas[activos_metricas["ID_Activo"] == filtro_global]
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Activos", len(activos_metricas))
    with col2:
        if not activos_metricas.empty and "Tipo_Activo" in activos_metricas.columns:
            fisicos = len(activos_metricas[activos_metricas["Tipo_Activo"].str.contains("Físico", case=False, na=False)])
            st.metric("Físicos", fisicos)
    with col3:
        if not activos_metricas.empty and "Tipo_Activo" in activos_metricas.columns:
            virtuales = len(activos_metricas[activos_metricas["Tipo_Activo"].str.contains("Virtual", case=False, na=False)])
            st.metric("Virtuales", virtuales)
    
    st.markdown("---")
    
    # Tabs internos para agregar activos individual o masivo
    tab_individual, tab_masivo = st.tabs(["➕ Agregar Individual", "📤 Carga Masiva"])
    
    # ========== TAB AGREGAR INDIVIDUAL ==========
    with tab_individual:
        st.markdown("### Agregar Nuevo Activo")
        
        # Expanders para organizar campos por sección
        with st.form("form_nuevo_activo"):
            st.markdown("#### 📋 Información General")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                nombre_activo = st.text_input("Nombre del Activo *", key="nuevo_activo_nombre")
                tipo_activo = st.selectbox(
                    "Tipo de Activo *",
                    ["Servidor Físico", "Servidor Virtual", "Base de Datos", "Servidor Web", 
                     "Equipo de Red", "Almacenamiento", "UPS", "Otro"],
                    key="nuevo_activo_tipo"
                )
                ubicacion = st.selectbox(
                    "Ubicación *",
                    ["Granados", "UdlaPark"],
                    key="nuevo_activo_ubicacion"
                )
            
            with col2:
                propietario = st.selectbox(
                    "Área Responsable *",
                    ["Infraestructura", "Seguridad de la información", "Soporte IT", "Desarrollo", "Operaciones"],
                    key="nuevo_activo_propietario"
                )
                tipo_servicio = st.text_input("Finalidad de Uso *", key="nuevo_activo_servicio")
                app_critica = st.selectbox(
                    "Aplicación Crítica",
                    ["No Aplica", "Banner", "Carpeta Online", "D2L", "Página Web", "Portal de Pagos", 
                     "BX", "Uni+", "Aprovisionamiento de Cuentas", "UniAutorization", "SAP"],
                    key="nuevo_activo_app",
                    help="Selecciona la aplicación crítica asociada a este activo"
                )
            
            with col3:
                rack = st.text_input("Rack/Ubicación Física", key="nuevo_activo_rack")
                num_administradores = st.number_input("# Administradores", min_value=0, value=1, key="nuevo_activo_admins")
            
            st.markdown("---")
            st.markdown("#### 🖥️ Especificaciones Técnicas")
            col4, col5, col6 = st.columns(3)
            
            with col4:
                modelo = st.text_input("Modelo", key="nuevo_activo_modelo")
                serial = st.text_input("Serial", key="nuevo_activo_serial")
                fabricante = st.text_input("Fabricante", key="nuevo_activo_fabricante")
            
            with col5:
                sistema_operativo = st.text_input("Sistema Operativo", key="nuevo_activo_so")
                virtualizacion = st.selectbox(
                    "Plataforma Virtualización",
                    ["N/A", "VMware", "Hyper-V", "KVM", "Proxmox", "Citrix", "Otro"],
                    key="nuevo_activo_virtualizacion"
                )
                desc_hardware = st.text_area("Descripción Hardware", key="nuevo_activo_hw", height=68)
            
            with col6:
                dependencias = st.text_area("Dependencias (otros activos)", key="nuevo_activo_deps", height=68)
            
            st.markdown("---")
            st.markdown("#### 📅 Mantenimiento y Soporte")
            col7, col8, col9 = st.columns(3)
            
            with col7:
                fecha_instalacion = st.date_input("Fecha Instalación", value=None, key="nuevo_activo_fecha_inst")
                vigencia_tecnologica = st.selectbox(
                    "Vigencia Tecnológica",
                    ["Vigente", "Próximo a EOL", "EOL (End of Life)", "Obsoleto"],
                    key="nuevo_activo_vigencia"
                )
            
            with col8:
                fecha_garantia = st.date_input("Vencimiento Garantía", value=None, key="nuevo_activo_garantia")
                proveedor_mantenimiento = st.text_input("Proveedor Mantenimiento", key="nuevo_activo_proveedor")
            
            with col9:
                contrato_mantenimiento = st.selectbox(
                    "Contrato Mantenimiento",
                    ["Sí", "No", "Por renovar"],
                    key="nuevo_activo_contrato"
                )
            
            submitted = st.form_submit_button("✅ Agregar Activo", type="primary", use_container_width=True)
            if submitted:
                if nombre_activo and tipo_servicio:
                    datos_activo = {
                        "Nombre_Activo": nombre_activo,
                        "Tipo_Activo": tipo_activo,
                        "Ubicacion": ubicacion,
                        "Propietario": propietario,
                        "Tipo_Servicio": tipo_servicio,
                        "App_Critica": app_critica if app_critica != "No Aplica" else "No",
                        # Nuevos campos técnicos
                        "Modelo": modelo,
                        "Serial": serial,
                        "Fabricante": fabricante,
                        "Sistema_Operativo": sistema_operativo,
                        "Virtualizacion": virtualizacion,
                        "Desc_Hardware": desc_hardware,
                        "Dependencias": dependencias,
                        "Rack": rack,
                        "Num_Administradores": num_administradores,
                        # Campos de mantenimiento
                        "Fecha_Instalacion": str(fecha_instalacion) if fecha_instalacion else "",
                        "Vigencia_Tecnologica": vigencia_tecnologica,
                        "Fecha_Garantia": str(fecha_garantia) if fecha_garantia else "",
                        "Proveedor_Mantenimiento": proveedor_mantenimiento,
                        "Contrato_Mantenimiento": contrato_mantenimiento
                    }
                    exito, mensaje, nuevo_id = crear_activo(ID_EVALUACION, datos_activo)
                    if exito:
                        st.success(f"✅ Activo creado: {nuevo_id}")
                        st.rerun()
                    else:
                        st.error(mensaje)
                else:
                    st.error("❌ Nombre del activo y Finalidad de Uso son obligatorios")
    
    # ========== TAB CARGA MASIVA ==========
    with tab_masivo:
        st.markdown("### 📤 Carga Masiva de Activos")
        st.info(f"📋 Evaluación destino: **{NOMBRE_EVALUACION}** (`{ID_EVALUACION}`)")
        
        # Sub-tabs para JSON y Excel
        sub_tab_json, sub_tab_excel, sub_tab_ayuda = st.tabs([
            "📄 JSON (Recomendado)", 
            "📊 Excel",
            "❓ Ayuda y Plantillas"
        ])
        
        # ===== JSON =====
        with sub_tab_json:
            st.markdown("#### 📄 Importar desde JSON")
            st.markdown("""
            **Formato JSON** es el recomendado porque:
            - ✅ Validación estricta de tipos
            - ✅ Sin riesgo de macros o fórmulas
            - ✅ Auditable (se genera hash del archivo)
            """)
            
            # Opción 1: Subir archivo
            st.markdown("**Opción 1: Subir archivo JSON**")
            archivo_json = st.file_uploader(
                "Selecciona un archivo .json",
                type=["json"],
                key="json_uploader_matriz",
                help="Archivo JSON con la estructura de activos"
            )
            
            if archivo_json:
                contenido = archivo_json.read().decode('utf-8')
                with st.expander("👁️ Vista previa del archivo", expanded=False):
                    st.code(contenido[:2000] + ("..." if len(contenido) > 2000 else ""), language="json")
                
                if st.button("🚀 Procesar JSON", type="primary", key="btn_procesar_json_matriz"):
                    with st.spinner("Procesando archivo JSON..."):
                        resultado = procesar_json(contenido, ID_EVALUACION)
                        if resultado.exito:
                            st.success(f"✅ {resultado.mensaje}")
                            st.metric("Activos importados", resultado.total_procesados)
                            if resultado.errores:
                                with st.expander("⚠️ Advertencias"):
                                    for err in resultado.errores:
                                        st.warning(err)
                            st.rerun()
                        else:
                            st.error(f"❌ {resultado.mensaje}")
                            for err in resultado.errores:
                                st.error(err)
            
            st.divider()
            
            # Opción 2: Pegar JSON
            st.markdown("**Opción 2: Pegar contenido JSON**")
            json_texto = st.text_area(
                "Pega el contenido JSON aquí:",
                height=200,
                key="json_textarea_matriz",
                placeholder='{\n  "activos": [\n    {\n      "nombre_activo": "Servidor BD",\n      "tipo_activo": "Servidor Físico"\n    }\n  ]\n}'
            )
            
            if json_texto.strip():
                if st.button("🚀 Procesar JSON Pegado", type="primary", key="btn_procesar_json_texto_matriz"):
                    with st.spinner("Procesando JSON..."):
                        resultado = procesar_json(json_texto, ID_EVALUACION)
                        if resultado.exito:
                            st.success(f"✅ {resultado.mensaje}")
                            st.rerun()
                        else:
                            st.error(f"❌ {resultado.mensaje}")
        
        # ===== EXCEL =====
        with sub_tab_excel:
            st.markdown("#### 📊 Importar desde Excel")
            st.warning("""
            **⚠️ Excel es formato de compatibilidad.**  
            Recomendamos JSON para mayor seguridad y validación.
            """)
            
            archivo_excel = st.file_uploader(
                "Selecciona un archivo Excel (.xlsx)",
                type=["xlsx"],
                key="excel_uploader_matriz",
                help="Archivo Excel con columnas: nombre_activo, tipo_activo, ubicacion, propietario, tipo_servicio"
            )
            
            if archivo_excel:
                try:
                    df_preview = pd.read_excel(archivo_excel, engine='openpyxl', nrows=5)
                    with st.expander("👁️ Vista previa (primeras 5 filas)", expanded=True):
                        st.dataframe(df_preview, use_container_width=True)
                    
                    archivo_excel.seek(0)
                    
                    if st.button("🚀 Procesar Excel", type="primary", key="btn_procesar_excel_matriz"):
                        with st.spinner("Procesando archivo Excel..."):
                            archivo_bytes = archivo_excel.read()
                            resultado = procesar_excel(archivo_bytes, ID_EVALUACION)
                            if resultado.exito:
                                st.success(f"✅ {resultado.mensaje}")
                                st.rerun()
                            else:
                                st.error(f"❌ {resultado.mensaje}")
                except Exception as e:
                    st.error(f"❌ Error al leer el archivo: {str(e)}")
        
        # ===== AYUDA =====
        with sub_tab_ayuda:
            st.markdown("#### ❓ Ayuda y Plantillas")
            
            campos_info = get_campos_info()
            
            st.markdown("**📋 Campos Requeridos:**")
            df_requeridos = pd.DataFrame(campos_info["requeridos"])
            st.dataframe(df_requeridos, use_container_width=True, hide_index=True)
            
            st.markdown("**📋 Campos Opcionales:**")
            df_opcionales = pd.DataFrame(campos_info["opcionales"])
            st.dataframe(df_opcionales, use_container_width=True, hide_index=True)
            
            st.markdown("**🏷️ Tipos de Activo Válidos:**")
            st.write(", ".join([f"`{t}`" for t in campos_info["tipos_validos"]]))
            
            st.divider()
            
            st.markdown("### 📥 Descargar Plantillas")
            col_p1, col_p2 = st.columns(2)
            
            with col_p1:
                st.markdown("**Plantilla JSON:**")
                plantilla_json = generar_plantilla_json()
                st.download_button(
                    label="⬇️ Descargar plantilla.json",
                    data=plantilla_json,
                    file_name="plantilla_activos.json",
                    mime="application/json",
                    key="download_json_matriz"
                )
                with st.expander("Ver contenido JSON"):
                    st.code(plantilla_json, language="json")
            
            with col_p2:
                st.markdown("**Plantilla Excel:**")
                df_plantilla = generar_plantilla_excel()
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_plantilla.to_excel(writer, index=False, sheet_name='Activos')
                
                st.download_button(
                    label="⬇️ Descargar plantilla.xlsx",
                    data=buffer.getvalue(),
                    file_name="plantilla_activos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel_matriz"
                )
    
    st.markdown("---")
    
    # ========== LISTA DE ACTIVOS ==========
    # Refrescar lista de activos
    activos = get_activos_matriz(ID_EVALUACION)
    
    # Obtener filtro global
    filtro_global = st.session_state.get("activo_filtro_global", "TODOS")
    
    # Tabla de activos
    if not activos.empty:
        st.subheader("📋 Lista de Activos")
        
        # Aplicar filtro si no es TODOS
        activos_display = activos.copy()
        if filtro_global != "TODOS":
            activos_display = activos_display[activos_display["ID_Activo"] == filtro_global]
            if not activos_display.empty:
                st.info(f"🎯 Mostrando activo filtrado: **{activos_display['Nombre_Activo'].values[0]}**")
        
        if not activos_display.empty:
            # Columnas a mostrar (sin criticidad - eso se calcula en Tab 3)
            columnas_mostrar = [
                "Nombre_Activo", "Tipo_Activo", "Ubicacion", 
                "Area_Responsable", "Finalidad_Uso", "Estado"
            ]
            columnas_existentes = [c for c in columnas_mostrar if c in activos_display.columns]
            
            df_display = activos_display[columnas_existentes].copy()
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Editar/Eliminar activo
        with st.expander("✏️ Editar o Eliminar Activo"):
            # Obtener filtro global
            filtro_global = st.session_state.get("activo_filtro_global", "TODOS")
            
            # Si hay filtro aplicado, pre-seleccionar ese activo
            if filtro_global != "TODOS" and filtro_global in activos["ID_Activo"].tolist():
                st.info(f"🎯 Editando activo filtrado: **{activos[activos['ID_Activo'] == filtro_global]['Nombre_Activo'].values[0]}**")
                activo_sel = filtro_global
            else:
                activo_sel = st.selectbox(
                    "Seleccionar activo",
                    activos["ID_Activo"].tolist(),
                    format_func=lambda x: activos[activos["ID_Activo"] == x]["Nombre_Activo"].values[0],
                    key="tab2_edit_activo_sel"
                )
            
            if activo_sel:
                activo_data = get_activo(ID_EVALUACION, activo_sel)
                if activo_data:
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_nombre = st.text_input("Nombre", value=activo_data.get("Nombre_Activo", ""))
                        edit_tipo = st.selectbox(
                            "Tipo",
                            ["Servidor Físico", "Servidor Virtual", "Equipo de Red", "Almacenamiento", "UPS", "Otro"],
                            index=0
                        )
                    with col2:
                        edit_ubicacion = st.text_input("Ubicación", value=activo_data.get("Ubicacion", ""))
                        edit_propietario = st.text_input("Responsable", value=activo_data.get("Propietario", ""))
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("💾 Guardar Cambios", key="btn_edit_activo"):
                            editar_activo(
                                activo_sel, 
                                nombre=edit_nombre,
                                tipo=edit_tipo,
                                ubicacion=edit_ubicacion,
                                propietario=edit_propietario
                            )
                            st.success("✅ Activo actualizado")
                            st.rerun()
                    with col_btn2:
                        if st.button("🗑️ Eliminar Activo", type="secondary", key="btn_del_activo"):
                            eliminar_activo(ID_EVALUACION, activo_sel)
                            st.success("✅ Activo eliminado")
                            st.rerun()
    else:
        st.info("📭 No hay activos registrados. Agrega el primero arriba.")


# ==================== TAB 3: IDENTIFICACIÓN Y VALORACIÓN ====================

with tab3:
    st.header("⚖️ Identificación y Valoración")
    st.markdown("""
    **Propósito:** Valorar cada activo en las dimensiones D (Disponibilidad), 
    I (Integridad), C (Confidencialidad) mediante **cuestionario guiado por tipo de activo**.
    
    **Metodología:** Cada tipo de activo tiene preguntas específicas. Las respuestas determinan el nivel (N/B/M/A).  
    **Fórmula:** `CRITICIDAD = MAX(Valor_D, Valor_I, Valor_C)`
    
    ⚠️ **Importante:** Cada activo solo puede ser valorado una vez. La valoración D/I/C es la base de toda la evaluación de riesgos.
    """)
    
    activos = get_activos_matriz(ID_EVALUACION)
    
    if activos.empty:
        st.warning("⚠️ No hay activos. Ve a la pestaña 'Activos' para agregar primero.")
        st.stop()
    
    # Sub-tabs: Cuestionario vs Resumen
    tab_cuestionario, tab_resumen_val = st.tabs(["📝 Cuestionario D/I/C", "📊 Resumen Valoraciones"])
    
    with tab_cuestionario:
        # Obtener filtro global
        filtro_global = st.session_state.get("activo_filtro_global", "TODOS")
        
        # Selector de activo con filtro global
        if filtro_global != "TODOS" and filtro_global in activos["ID_Activo"].tolist():
            st.info(f"🎯 Valorando activo filtrado: **{activos[activos['ID_Activo'] == filtro_global]['Nombre_Activo'].values[0]}**")
            activo_sel = filtro_global
        else:
            activo_sel = st.selectbox(
                "🎯 Seleccionar Activo para Valorar",
                activos["ID_Activo"].tolist(),
                format_func=lambda x: f"{activos[activos['ID_Activo'] == x]['Nombre_Activo'].values[0]} ({activos[activos['ID_Activo'] == x]['Tipo_Activo'].values[0]})",
                key="valoracion_activo_sel"
            )
        
        if activo_sel:
            activo_info = activos[activos["ID_Activo"] == activo_sel].iloc[0]
            tipo_activo = activo_info['Tipo_Activo']
            
            # ===== DETECCIÓN DE ESTADO DEL ACTIVO =====
            valoracion_actual = get_valoracion_activo(ID_EVALUACION, activo_sel)
            esta_valorado = valoracion_actual is not None
            
            # Inicializar estado de edición en session_state
            key_edit = f"edit_mode_{activo_sel}"
            if key_edit not in st.session_state:
                st.session_state[key_edit] = False
            
            # Determinar estado actual
            if esta_valorado and not st.session_state[key_edit]:
                estado = "VALORADO"
            elif esta_valorado and st.session_state[key_edit]:
                estado = "EDITANDO"
            else:
                estado = "PENDIENTE"
            
            # Info del activo
            st.markdown("---")
            col_info1, col_info2, col_info3, col_info4 = st.columns(4)
            with col_info1:
                st.markdown(f"**📦 Activo:** {activo_info['Nombre_Activo']}")
            with col_info2:
                st.markdown(f"**🏷️ Tipo:** {tipo_activo}")
            with col_info3:
                st.markdown(f"**📍 Ubicación:** {activo_info['Ubicacion']}")
            with col_info4:
                # Badge de estado
                if estado == "VALORADO":
                    st.markdown("**📌 Estado:** 🟢 **Valorado**")
                elif estado == "EDITANDO":
                    st.markdown("**📌 Estado:** 🟡 **Editando**")
                else:
                    st.markdown("**📌 Estado:** ⚪ **Pendiente**")
            
            st.markdown("---")
            
            # ===== VISTA SEGÚN ESTADO =====
            
            # ===== ESTADO: VALORADO (Solo Lectura) =====
            if estado == "VALORADO":
                st.success("""
                ✅ **Valoración D/I/C Registrada con Éxito**
                
                Esta información es la base de la evaluación de riesgos de este activo.  
                Todas las vulnerabilidades, amenazas y salvaguardas se basan en estos valores.
                """)
                
                # Mostrar valores actuales en tarjetas grandes
                st.markdown("### 📊 Valoración Actual")
                
                col_d, col_i, col_c, col_crit = st.columns(4)
                
                with col_d:
                    d_nivel = valoracion_actual.get("D", "N")
                    d_valor = valoracion_actual.get("Valor_D", 0)
                    color_d = {"A": "🔴", "M": "🟡", "B": "🟢", "N": "⚪"}.get(d_nivel, "⚪")
                    st.markdown(f"""
                    <div style="padding: 1.5rem; border: 3px solid #3498db; border-radius: 10px; text-align: center; background: #3498db11;">
                        <h3>{color_d} Disponibilidad</h3>
                        <h1 style="color: #3498db; margin: 0;">{d_valor}</h1>
                        <p style="font-size: 1.2rem; margin: 0;">Nivel: <strong>{d_nivel}</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_i:
                    i_nivel = valoracion_actual.get("I", "N")
                    i_valor = valoracion_actual.get("Valor_I", 0)
                    color_i = {"A": "🔴", "M": "🟡", "B": "🟢", "N": "⚪"}.get(i_nivel, "⚪")
                    st.markdown(f"""
                    <div style="padding: 1.5rem; border: 3px solid #2ecc71; border-radius: 10px; text-align: center; background: #2ecc7111;">
                        <h3>{color_i} Integridad</h3>
                        <h1 style="color: #2ecc71; margin: 0;">{i_valor}</h1>
                        <p style="font-size: 1.2rem; margin: 0;">Nivel: <strong>{i_nivel}</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_c:
                    c_nivel = valoracion_actual.get("C", "N")
                    c_valor = valoracion_actual.get("Valor_C", 0)
                    color_c = {"A": "🔴", "M": "🟡", "B": "🟢", "N": "⚪"}.get(c_nivel, "⚪")
                    st.markdown(f"""
                    <div style="padding: 1.5rem; border: 3px solid #9b59b6; border-radius: 10px; text-align: center; background: #9b59b611;">
                        <h3>{color_c} Confidencialidad</h3>
                        <h1 style="color: #9b59b6; margin: 0;">{c_valor}</h1>
                        <p style="font-size: 1.2rem; margin: 0;">Nivel: <strong>{c_nivel}</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_crit:
                    crit_valor = valoracion_actual.get("Criticidad", 0)
                    crit_nivel = valoracion_actual.get("Criticidad_Nivel", "Nula")
                    color_crit_dict = {"Alta": "#e74c3c", "Media": "#f39c12", "Baja": "#2ecc71", "Nula": "#95a5a6"}
                    color_crit = color_crit_dict.get(crit_nivel, "#95a5a6")
                    emoji_crit = {"Alta": "🔴", "Media": "🟡", "Baja": "🟢", "Nula": "⚪"}.get(crit_nivel, "⚪")
                    st.markdown(f"""
                    <div style="padding: 1.5rem; border: 3px solid {color_crit}; border-radius: 10px; text-align: center; background: {color_crit}11;">
                        <h3>{emoji_crit} CRITICIDAD</h3>
                        <h1 style="color: {color_crit}; margin: 0;">{crit_valor}</h1>
                        <p style="font-size: 1.2rem; margin: 0;">Nivel: <strong>{crit_nivel}</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Mostrar valores RTO/RPO/BIA si existen
                if valoracion_actual.get("RTO_Tiempo") or valoracion_actual.get("RPO_Tiempo") or valoracion_actual.get("BIA_Nivel"):
                    st.markdown("---")
                    st.markdown("### ⏱️ Continuidad del Negocio (RTO/RPO/BIA)")
                    
                    col_rto, col_rpo, col_bia = st.columns(3)
                    
                    with col_rto:
                        rto_tiempo = valoracion_actual.get("RTO_Tiempo", "No definido")
                        rto_nivel = valoracion_actual.get("RTO_Nivel", "Bajo")
                        st.metric("⏱️ RTO (Recovery Time Objective)", rto_tiempo, delta=rto_nivel)
                    
                    with col_rpo:
                        rpo_tiempo = valoracion_actual.get("RPO_Tiempo", "No definido")
                        rpo_nivel = valoracion_actual.get("RPO_Nivel", "Bajo")
                        st.metric("💾 RPO (Recovery Point Objective)", rpo_tiempo, delta=rpo_nivel)
                    
                    with col_bia:
                        bia_nivel = valoracion_actual.get("BIA_Nivel", "Bajo")
                        st.metric("📊 BIA (Business Impact Analysis)", bia_nivel)
                
                st.markdown("---")
                
                # Mostrar respuestas del cuestionario en modo solo lectura
                with st.expander("📋 Ver Respuestas del Cuestionario (Solo Lectura)", expanded=False):
                    respuestas_previas = get_respuestas_previas(ID_EVALUACION, activo_sel)
                    preguntas = get_banco_preguntas_tipo(tipo_activo)
                    
                    if not preguntas:
                        preguntas = get_banco_preguntas_tipo("Servidor Físico")
                    
                    if respuestas_previas and preguntas:
                        # Mostrar por dimensión
                        tabs_lectura = st.tabs(["🔵 Disponibilidad", "🟢 Integridad", "🟣 Confidencialidad", "⏱️ RTO", "💾 RPO", "📊 BIA"])
                        
                        dimensiones = ["D", "I", "C", "RTO", "RPO", "BIA"]
                        for tab_idx, dim in enumerate(dimensiones):
                            with tabs_lectura[tab_idx]:
                                preguntas_dim = preguntas.get(dim, [])
                                for i, pregunta in enumerate(preguntas_dim):
                                    pregunta_id = pregunta["id"]
                                    if pregunta_id in respuestas_previas:
                                        valor_resp = respuestas_previas[pregunta_id]
                                        # Encontrar texto de la respuesta
                                        texto_resp = "No encontrado"
                                        for opt in pregunta["opciones"]:
                                            if opt["valor"] == valor_resp:
                                                texto_resp = opt["texto"]
                                                break
                                        
                                        st.markdown(f"""
                                        **{i+1}. {pregunta['pregunta']}**  
                                        ➜ **Respuesta:** ({valor_resp}) {texto_resp}
                                        """)
                                        st.markdown("---")
                    else:
                        st.info("No se encontraron respuestas del cuestionario.")
                
                st.markdown("---")
                
                # Botón para habilitar edición (con advertencia)
                st.warning("""
                ⚠️ **Advertencia sobre Edición**
                
                Modificar la valoración D/I/C afectará:
                - Todas las vulnerabilidades y amenazas identificadas
                - Los riesgos calculados (inherentes y residuales)
                - Las salvaguardas recomendadas
                - El mapa de riesgos completo
                
                **Solo edite si es absolutamente necesario.**
                """)
                
                col_edit1, col_edit2 = st.columns([1, 3])
                with col_edit1:
                    if st.button("✏️ Habilitar Edición", type="secondary", use_container_width=True):
                        st.session_state[key_edit] = True
                        st.rerun()
                
                with col_edit2:
                    st.caption("💡 Al habilitar la edición, podrá modificar las respuestas del cuestionario D/I/C.")
            
            # ===== ESTADO: PENDIENTE o EDITANDO (Formulario Editable) =====
            else:
                if estado == "EDITANDO":
                    st.warning("""
                    ⚠️ **Modo Edición Activado**
                    
                    Está modificando una valoración existente. Los cambios afectarán toda la evaluación de riesgos.  
                    Proceda con precaución.
                    """)
                
                respuestas_previas = get_respuestas_previas(ID_EVALUACION, activo_sel)
                
                # Obtener preguntas para este tipo
                preguntas = get_banco_preguntas_tipo(tipo_activo)
                
                if not preguntas:
                    st.warning(f"⚠️ No hay cuestionario específico para '{tipo_activo}'. Se usará el cuestionario genérico.")
                    preguntas = get_banco_preguntas_tipo("Servidor Físico")
                
                # Mostrar cuestionario por dimensión
                st.markdown("### 📋 Cuestionario de Valoración")
                st.info("💡 Responda las siguientes preguntas para calcular automáticamente los niveles D/I/C del activo.")
                
                respuestas = {}
                
                # Tabs por dimensión
                dim_d, dim_i, dim_c, dim_rto, dim_rpo, dim_bia = st.tabs([
                    "🔵 Disponibilidad (D)", 
                    "🟢 Integridad (I)", 
                    "🟣 Confidencialidad (C)",
                    "⏱️ RTO",
                    "💾 RPO",
                    "📊 BIA"
                ])
                
                # ===== DISPONIBILIDAD =====
                with dim_d:
                    st.markdown("#### ¿Qué tan crítico es que el activo esté disponible?")
                    for i, pregunta in enumerate(preguntas.get("D", [])):
                        pregunta_id = pregunta["id"]
                        opciones = [f"({opt['valor']}) {opt['texto']}" for opt in pregunta["opciones"]]
                        
                        default_idx = 0
                        if respuestas_previas and pregunta_id in respuestas_previas:
                            val_prev = respuestas_previas[pregunta_id]
                            for idx, opt in enumerate(pregunta["opciones"]):
                                if opt["valor"] == val_prev:
                                    default_idx = idx
                                    break
                        
                        seleccion = st.radio(
                            f"**{i+1}. {pregunta['pregunta']}**",
                            opciones,
                            index=default_idx,
                            key=f"q_{pregunta_id}_{estado}"
                        )
                        respuestas[pregunta_id] = int(seleccion.split(")")[0].replace("(", ""))
                
                # ===== INTEGRIDAD =====
                with dim_i:
                    st.markdown("#### ¿Qué tan crítico es mantener la integridad de los datos?")
                    for i, pregunta in enumerate(preguntas.get("I", [])):
                        pregunta_id = pregunta["id"]
                        opciones = [f"({opt['valor']}) {opt['texto']}" for opt in pregunta["opciones"]]
                        
                        default_idx = 0
                        if respuestas_previas and pregunta_id in respuestas_previas:
                            val_prev = respuestas_previas[pregunta_id]
                            for idx, opt in enumerate(pregunta["opciones"]):
                                if opt["valor"] == val_prev:
                                    default_idx = idx
                                    break
                        
                        seleccion = st.radio(
                            f"**{i+1}. {pregunta['pregunta']}**",
                            opciones,
                            index=default_idx,
                            key=f"q_{pregunta_id}_{estado}"
                        )
                        respuestas[pregunta_id] = int(seleccion.split(")")[0].replace("(", ""))
                
                # ===== CONFIDENCIALIDAD =====
                with dim_c:
                    st.markdown("#### ¿Qué nivel de confidencialidad requiere el activo?")
                    for i, pregunta in enumerate(preguntas.get("C", [])):
                        pregunta_id = pregunta["id"]
                        opciones = [f"({opt['valor']}) {opt['texto']}" for opt in pregunta["opciones"]]
                        
                        default_idx = 0
                        if respuestas_previas and pregunta_id in respuestas_previas:
                            val_prev = respuestas_previas[pregunta_id]
                            for idx, opt in enumerate(pregunta["opciones"]):
                                if opt["valor"] == val_prev:
                                    default_idx = idx
                                    break
                        
                        seleccion = st.radio(
                            f"**{i+1}. {pregunta['pregunta']}**",
                            opciones,
                            index=default_idx,
                            key=f"q_{pregunta_id}_{estado}"
                        )
                        respuestas[pregunta_id] = int(seleccion.split(")")[0].replace("(", ""))
                
                # ===== RTO =====
                with dim_rto:
                    st.markdown("#### ¿Cuál es el tiempo máximo aceptable de recuperación?")
                    st.info("🕐 RTO define cuánto tiempo puede estar inoperativo el activo antes de causar impacto inaceptable.")
                    for i, pregunta in enumerate(preguntas.get("RTO", [])):
                        pregunta_id = pregunta["id"]
                        opciones = [f"({opt['valor']}) {opt['texto']}" for opt in pregunta["opciones"]]
                        
                        default_idx = 0
                        if respuestas_previas and pregunta_id in respuestas_previas:
                            val_prev = respuestas_previas[pregunta_id]
                            for idx, opt in enumerate(pregunta["opciones"]):
                                if opt["valor"] == val_prev:
                                    default_idx = idx
                                    break
                        
                        seleccion = st.radio(
                            f"**{i+1}. {pregunta['pregunta']}**",
                            opciones,
                            index=default_idx,
                            key=f"q_{pregunta_id}_{estado}"
                        )
                        respuestas[pregunta_id] = int(seleccion.split(")")[0].replace("(", ""))
                
                # ===== RPO =====
                with dim_rpo:
                    st.markdown("#### ¿Cuánta pérdida de datos es aceptable?")
                    st.info("💾 RPO define cuántos datos (en tiempo) se pueden perder sin causar impacto inaceptable.")
                    for i, pregunta in enumerate(preguntas.get("RPO", [])):
                        pregunta_id = pregunta["id"]
                        opciones = [f"({opt['valor']}) {opt['texto']}" for opt in pregunta["opciones"]]
                        
                        default_idx = 0
                        if respuestas_previas and pregunta_id in respuestas_previas:
                            val_prev = respuestas_previas[pregunta_id]
                            for idx, opt in enumerate(pregunta["opciones"]):
                                if opt["valor"] == val_prev:
                                    default_idx = idx
                                    break
                        
                        seleccion = st.radio(
                            f"**{i+1}. {pregunta['pregunta']}**",
                            opciones,
                            index=default_idx,
                            key=f"q_{pregunta_id}_{estado}"
                        )
                        respuestas[pregunta_id] = int(seleccion.split(")")[0].replace("(", ""))
                
                # ===== BIA =====
                with dim_bia:
                    st.markdown("#### ¿Cuál es el impacto al negocio si este activo falla?")
                    st.info("📊 BIA analiza el impacto financiero, operacional y reputacional en caso de falla.")
                    for i, pregunta in enumerate(preguntas.get("BIA", [])):
                        pregunta_id = pregunta["id"]
                        opciones = [f"({opt['valor']}) {opt['texto']}" for opt in pregunta["opciones"]]
                        
                        default_idx = 0
                        if respuestas_previas and pregunta_id in respuestas_previas:
                            val_prev = respuestas_previas[pregunta_id]
                            for idx, opt in enumerate(pregunta["opciones"]):
                                if opt["valor"] == val_prev:
                                    default_idx = idx
                                    break
                        
                        seleccion = st.radio(
                            f"**{i+1}. {pregunta['pregunta']}**",
                            opciones,
                            index=default_idx,
                            key=f"q_{pregunta_id}_{estado}"
                        )
                        respuestas[pregunta_id] = int(seleccion.split(")")[0].replace("(", ""))
                
                st.markdown("---")
                
                # Previsualización del cálculo
                if respuestas:
                    resultado_preview = procesar_cuestionario_dic(tipo_activo, respuestas)
                    
                    st.markdown("### 📊 Vista Previa del Cálculo")
                    
                    # Fila 1: D/I/C/Criticidad
                    st.markdown("**Valoración D/I/C:**")
                    col_prev1, col_prev2, col_prev3, col_prev4 = st.columns(4)
                    
                    with col_prev1:
                        color_d = {"A": "🔴", "M": "🟡", "B": "🟢", "N": "⚪"}.get(resultado_preview["D"], "⚪")
                        st.metric(f"{color_d} Disponibilidad", f"{resultado_preview['Valor_D']} ({resultado_preview['D']})")
                    
                    with col_prev2:
                        color_i = {"A": "🔴", "M": "🟡", "B": "🟢", "N": "⚪"}.get(resultado_preview["I"], "⚪")
                        st.metric(f"{color_i} Integridad", f"{resultado_preview['Valor_I']} ({resultado_preview['I']})")
                    
                    with col_prev3:
                        color_c = {"A": "🔴", "M": "🟡", "B": "🟢", "N": "⚪"}.get(resultado_preview["C"], "⚪")
                        st.metric(f"{color_c} Confidencialidad", f"{resultado_preview['Valor_C']} ({resultado_preview['C']})")
                    
                    with col_prev4:
                        color_crit = {"Alta": "🔴", "Media": "🟡", "Baja": "🟢", "Nula": "⚪"}.get(resultado_preview["Criticidad_Nivel"], "⚪")
                        st.metric(f"{color_crit} CRITICIDAD", f"{resultado_preview['Criticidad']} ({resultado_preview['Criticidad_Nivel']})")
                    
                    # Fila 2: RTO/RPO/BIA
                    st.markdown("**Continuidad del Negocio (RTO/RPO/BIA):**")
                    col_rto, col_rpo, col_bia = st.columns(3)
                    
                    with col_rto:
                        rto_nivel = resultado_preview.get("RTO_Nivel", "Bajo")
                        rto_color = {"Alto": "🔴", "Medio": "🟡", "Bajo": "🟢", "Nulo": "⚪"}.get(rto_nivel, "⚪")
                        rto_tiempo = resultado_preview.get("RTO_Tiempo", "No definido")
                        st.metric(f"{rto_color} RTO", rto_tiempo, delta=rto_nivel)
                    
                    with col_rpo:
                        rpo_nivel = resultado_preview.get("RPO_Nivel", "Bajo")
                        rpo_color = {"Alto": "🔴", "Medio": "🟡", "Bajo": "🟢", "Nulo": "⚪"}.get(rpo_nivel, "⚪")
                        rpo_tiempo = resultado_preview.get("RPO_Tiempo", "No definido")
                        st.metric(f"{rpo_color} RPO", rpo_tiempo, delta=rpo_nivel)
                    
                    with col_bia:
                        bia_nivel = resultado_preview.get("BIA_Nivel", "Bajo")
                        bia_color = {"Alto": "🔴", "Medio": "🟡", "Bajo": "🟢", "Nulo": "⚪"}.get(bia_nivel, "⚪")
                        bia_valor = resultado_preview.get("BIA_Valor", 0)
                        st.metric(f"{bia_color} Impacto BIA", bia_nivel, delta=f"Nivel {bia_valor}")
                
                st.markdown("---")
                
                # Botones de acción
                col_btn1, col_btn2 = st.columns([2, 1])
                
                with col_btn1:
                    texto_boton = "💾 Guardar Cambios" if estado == "EDITANDO" else "💾 Guardar Valoración"
                    if st.button(texto_boton, type="primary", use_container_width=True):
                        try:
                            resultado = guardar_respuestas_dic(
                                id_evaluacion=ID_EVALUACION,
                                id_activo=activo_sel,
                                tipo_activo=tipo_activo,
                                respuestas=respuestas
                            )
                            
                            if estado == "EDITANDO":
                                st.success(f"""✅ Valoración actualizada exitosamente:
                                - **Criticidad D/I/C:** {resultado['Criticidad']} ({resultado['Criticidad_Nivel']})
                                - **RTO:** {resultado.get('RTO_Tiempo', 'N/A')} ({resultado.get('RTO_Nivel', 'N/A')})
                                - **RPO:** {resultado.get('RPO_Tiempo', 'N/A')} ({resultado.get('RPO_Nivel', 'N/A')})
                                - **BIA:** {resultado.get('BIA_Nivel', 'N/A')}
                                
                                ⚠️ Recuerde revisar las vulnerabilidades y riesgos en los siguientes tabs.
                                """)
                            else:
                                st.success(f"""✅ Valoración guardada exitosamente:
                                - **Criticidad D/I/C:** {resultado['Criticidad']} ({resultado['Criticidad_Nivel']})
                                - **RTO:** {resultado.get('RTO_Tiempo', 'N/A')} ({resultado.get('RTO_Nivel', 'N/A')})
                                - **RPO:** {resultado.get('RPO_Tiempo', 'N/A')} ({resultado.get('RPO_Nivel', 'N/A')})
                                - **BIA:** {resultado.get('BIA_Nivel', 'N/A')}
                                """)
                            
                            st.balloons()
                            
                            # Desactivar modo edición
                            st.session_state[key_edit] = False
                            
                            # Esperar un momento antes de recargar
                            time.sleep(1)
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error al guardar: {str(e)}")
                
                with col_btn2:
                    if estado == "EDITANDO":
                        if st.button("❌ Cancelar Edición", use_container_width=True):
                            st.session_state[key_edit] = False
                            st.rerun()

    
    # ===== RESUMEN DE VALORACIONES =====
    with tab_resumen_val:
        st.subheader("📋 Resumen de Valoraciones")
        
        # Obtener filtro global
        filtro_global = st.session_state.get("activo_filtro_global", "TODOS")
        
        # Estadísticas
        valoraciones = get_valoraciones_evaluacion(ID_EVALUACION)
        
        # Aplicar filtro si no es TODOS
        if filtro_global != "TODOS" and not valoraciones.empty:
            valoraciones = valoraciones[valoraciones["ID_Activo"] == filtro_global]
            activos_filtrados = activos[activos["ID_Activo"] == filtro_global]
            if not valoraciones.empty:
                st.info(f"🎯 Mostrando valoración del activo filtrado: **{activos_filtrados['Nombre_Activo'].values[0]}**")
        else:
            activos_filtrados = activos
        
        total_activos = len(activos_filtrados)
        valorados = len(valoraciones) if not valoraciones.empty else 0
        
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.metric("Total Activos", total_activos)
        with col_stat2:
            st.metric("Valorados", valorados)
        with col_stat3:
            pendientes = total_activos - valorados
            st.metric("Pendientes", pendientes)
        
        if not valoraciones.empty:
            st.markdown("---")
            
            # Agregar nombre del activo a las valoraciones
            valoraciones_display = valoraciones.copy()
            
            # Obtener nombres de activos
            for idx, row in valoraciones_display.iterrows():
                activo_data = activos[activos["ID_Activo"] == row["ID_Activo"]]
                if not activo_data.empty:
                    valoraciones_display.loc[idx, "Nombre_Activo"] = activo_data["Nombre_Activo"].values[0]
                else:
                    valoraciones_display.loc[idx, "Nombre_Activo"] = row["ID_Activo"]
            
            # Columnas a mostrar (incluyendo nombre y RTO/RPO/BIA)
            cols = ["Nombre_Activo", "D", "Valor_D", "I", "Valor_I", "C", "Valor_C", 
                    "Criticidad", "Criticidad_Nivel", "RTO_Tiempo", "RTO_Nivel", 
                    "RPO_Tiempo", "RPO_Nivel", "BIA_Nivel"]
            cols_existentes = [c for c in cols if c in valoraciones_display.columns]
            
            def colorear_criticidad(val):
                if val == "Alta": return "background-color: #ff4444; color: white"
                elif val == "Media": return "background-color: #ffbb33; color: black"
                elif val == "Baja": return "background-color: #00C851; color: white"
                return ""
            
            styled_df = valoraciones_display[cols_existentes].style.map(
                colorear_criticidad, subset=["Criticidad_Nivel"]
            )
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Gráfico de distribución
            st.markdown("---")
            st.subheader("📊 Distribución de Criticidad")
            
            if "Criticidad_Nivel" in valoraciones_display.columns:
                dist = valoraciones_display["Criticidad_Nivel"].value_counts().reset_index()
                dist.columns = ["Nivel", "Cantidad"]
                
                fig_crit = px.pie(
                    dist, 
                    values="Cantidad", 
                    names="Nivel",
                    color="Nivel",
                    color_discrete_map={
                        "Alta": "#ff4444",
                        "Media": "#ffbb33", 
                        "Baja": "#00C851",
                        "Nula": "#33b5e5"
                    }
                )
                st.plotly_chart(fig_crit, use_container_width=True)
        else:
            st.info("📭 No hay valoraciones registradas aún. Complete el cuestionario para cada activo.")


# ==================== TAB 4: VULNERABILIDADES Y AMENAZAS (IA LOCAL) ====================

with tab4:
    st.header("🔓 Vulnerabilidades y Amenazas (Identificación con IA)")
    st.markdown("""
    **Propósito:** La IA local identifica automáticamente vulnerabilidades y amenazas basándose en la **CRITICIDAD** del activo.
    
    **Proceso MAGERIT con IA:**
    1. La IA analiza el tipo de activo y su valoración D/I/C
    2. Identifica amenazas relevantes del catálogo MAGERIT
    3. Sugiere vulnerabilidades asociadas
    4. Calcula la degradación según la criticidad
    
    **Fórmulas:**
    - `Impacto_D = Valor_D × Degradación_D`
    - `Impacto_I = Valor_I × Degradación_I`  
    - `Impacto_C = Valor_C × Degradación_C`
    - `IMPACTO_TOTAL = MAX(Impacto_D, Impacto_I, Impacto_C)`
    
    ⚠️ **Importante:** El análisis IA se ejecuta una vez por activo. Los resultados alimentan el cálculo de riesgos y salvaguardas.
    """)
    
    # Importar función de análisis con IA
    from services.ollama_magerit_service import analizar_amenazas_por_criticidad, verificar_ollama_disponible
    from services.ollama_monitor import obtener_estado_sistema
    
    activos = get_activos_matriz(ID_EVALUACION)
    
    if activos.empty:
        st.warning("⚠️ No hay activos. Ve a la pestaña 'Activos' para agregar primero.")
        st.stop()
    
    # Verificar estado de Ollama CON DISPONIBILIDAD 100%
    ollama_disponible, modelos = verificar_ollama_disponible()
    
    # Panel de estado de IA
    with st.expander("🔍 Estado del Sistema de IA Local", expanded=False):
        estado_ia = obtener_estado_sistema()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if estado_ia['disponible']:
                st.metric("Estado", "🟢 Activo", delta="100%")
            else:
                st.metric("Estado", "🔴 Inactivo")
        with col2:
            st.metric("Modelos", len(estado_ia['modelos']))
        with col3:
            st.metric("Cache", estado_ia['archivos_cache'])
        with col4:
            st.metric("Reintentos", estado_ia['intentos_fallidos'])
        if estado_ia['disponible']:
            st.success(f"✅ {estado_ia['mensaje']}")
        else:
            st.warning(f"⚠️ {estado_ia['mensaje']}")
    
    if ollama_disponible:
        st.success(f"🟢 IA Local - **Disponibilidad 100%** garantizada - {len(modelos)} modelos")
    else:
        st.warning("⚠️ IA en recuperación automática. Usando análisis heurístico.")
    
    # ===== SELECCIÓN DE ACTIVO =====
    st.subheader("📦 Selección de Activo")
    
    # Obtener filtro global
    filtro_global = st.session_state.get("activo_filtro_global", "TODOS")
    
    # Selector de activo con filtro global
    # Opción para analizar todos los activos o uno individual
    if filtro_global == "TODOS":
        col_modo1, col_modo2 = st.columns([1, 3])
        with col_modo1:
            modo_analisis = st.radio(
                "Modo de Análisis",
                ["Individual", "Todos los Activos"],
                key="modo_analisis_ia"
            )
        with col_modo2:
            if modo_analisis == "Todos los Activos":
                st.info("📊 Se analizarán todos los activos con IA de forma secuencial. Esto puede tomar varios minutos.")
    else:
        modo_analisis = "Individual"
    
    # Si modo individual o filtro específico
    if modo_analisis == "Individual":
        if filtro_global != "TODOS" and filtro_global in activos["ID_Activo"].tolist():
            st.info(f"🎯 Analizando activo filtrado: **{activos[activos['ID_Activo'] == filtro_global]['Nombre_Activo'].values[0]}**")
            activo_sel = filtro_global
        else:
            activo_sel = st.selectbox(
                "🎯 Seleccionar Activo para Analizar",
                activos["ID_Activo"].tolist(),
                format_func=lambda x: f"{activos[activos['ID_Activo'] == x]['Nombre_Activo'].values[0]} ({activos[activos['ID_Activo'] == x]['Tipo_Activo'].values[0]})",
                key="vuln_activo_sel"
            )
    else:
        activo_sel = None  # Modo análisis masivo
    
    # ===== MODO ANÁLISIS MASIVO =====
    if modo_analisis == "Todos los Activos":
        st.markdown("---")
        st.markdown("### 🚀 Análisis Masivo con IA")
        
        # Estadísticas
        total_activos = len(activos)
        activos_analizados = len([a for a in activos["ID_Activo"].tolist() if not get_vulnerabilidades_activo(ID_EVALUACION, a).empty])
        activos_pendientes = total_activos - activos_analizados
        
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.metric("Total Activos", total_activos)
        with col_stat2:
            st.metric("Ya Analizados", activos_analizados, delta="✅")
        with col_stat3:
            st.metric("Pendientes", activos_pendientes, delta="⏳")
        
        st.markdown("---")
        
        if st.button("🤖 Analizar TODOS los activos con IA", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            log_container = st.container()
            
            exitos = 0
            errores = 0
            omitidos_analizados = 0
            omitidos_sin_dic = 0
            activos_sin_dic = []
            
            for idx, activo_id in enumerate(activos["ID_Activo"].tolist()):
                progress = (idx + 1) / total_activos
                progress_bar.progress(progress)
                status_text.text(f"Analizando {idx + 1}/{total_activos}: {activo_id}")
                
                # Verificar si ya está analizado
                vuln_existentes = get_vulnerabilidades_activo(ID_EVALUACION, activo_id)
                if not vuln_existentes.empty:
                    with log_container:
                        st.caption(f"⏭️ {activo_id}: Ya analizado, omitido")
                    omitidos_analizados += 1
                    continue
                
                # Obtener datos del activo
                activo_row = activos[activos["ID_Activo"] == activo_id].iloc[0]
                valoracion = get_valoracion_activo(ID_EVALUACION, activo_id)
                
                if not valoracion or valoracion.get("Criticidad", 0) == 0:
                    with log_container:
                        st.caption(f"⚠️ {activo_id}: Sin valoración DIC, omitido")
                    omitidos_sin_dic += 1
                    activos_sin_dic.append(f"{activo_id} ({activo_row['Nombre_Activo']})")
                    continue
                
                # Preparar datos
                activo_dict = {
                    "ID_Activo": activo_id,
                    "Nombre_Activo": activo_row['Nombre_Activo'],
                    "Tipo_Activo": activo_row['Tipo_Activo'],
                    "Descripcion": activo_row.get('Descripcion', ''),
                    "Ubicacion": activo_row.get('Ubicacion', '')
                }
                
                valoracion_dict = {
                    "Valor_D": valoracion.get("Valor_D", 0),
                    "Valor_I": valoracion.get("Valor_I", 0),
                    "Valor_C": valoracion.get("Valor_C", 0),
                    "D": valoracion.get("D", "N"),
                    "I": valoracion.get("I", "N"),
                    "C": valoracion.get("C", "N"),
                    "Criticidad": valoracion.get("Criticidad", 0),
                    "Criticidad_Nivel": valoracion.get("Criticidad_Nivel", "Sin valorar")
                }
                
                # Analizar con IA
                exito, amenazas, mensaje = analizar_amenazas_por_criticidad(activo_dict, valoracion_dict)
                
                if exito and amenazas:
                    # Guardar automáticamente cada amenaza
                    guardadas = 0
                    errores_guardar = 0
                    for am in amenazas:
                        try:
                            # CORREGIDO: Mapear campos correctamente desde IA
                            # La IA retorna: codigo_amenaza, codigo_vulnerabilidad, 
                            # nombre_amenaza, degradacion_d/i/c (valores 0-100)
                            
                            # Obtener código de amenaza
                            cod_amenaza = am.get('codigo_amenaza', am.get('codigo', am.get('cod_amenaza', '')))
                            
                            # Obtener código de vulnerabilidad
                            cod_vuln = am.get('codigo_vulnerabilidad', am.get('codigo_vuln', am.get('cod_vulnerabilidad', '')))
                            
                            # Obtener nombre de amenaza
                            nombre_amenaza = am.get('nombre_amenaza', am.get('nombre', am.get('amenaza', '')))
                            
                            # Obtener degradaciones (IA retorna 0-100, DB espera 0-1)
                            deg_d_raw = am.get('degradacion_d', am.get('deg_d', 0))
                            deg_i_raw = am.get('degradacion_i', am.get('deg_i', 0))
                            deg_c_raw = am.get('degradacion_c', am.get('deg_c', 0))
                            
                            # Convertir de 0-100 a 0-1 si es necesario
                            deg_d = deg_d_raw / 100 if deg_d_raw > 1 else deg_d_raw
                            deg_i = deg_i_raw / 100 if deg_i_raw > 1 else deg_i_raw
                            deg_c = deg_c_raw / 100 if deg_c_raw > 1 else deg_c_raw
                            
                            agregar_vulnerabilidad_amenaza(
                                id_evaluacion=ID_EVALUACION,
                                id_activo=activo_id,
                                nombre_activo=activo_row['Nombre_Activo'],
                                vulnerabilidad=am.get('vulnerabilidad', ''),
                                amenaza=nombre_amenaza,
                                cod_amenaza=cod_amenaza,
                                cod_vulnerabilidad=cod_vuln,
                                deg_d=deg_d,
                                deg_i=deg_i,
                                deg_c=deg_c
                            )
                            guardadas += 1
                        except Exception as e:
                            errores_guardar += 1
                    
                    if guardadas > 0:
                        with log_container:
                            st.caption(f"✅ {activo_id}: {guardadas} amenazas guardadas")
                        exitos += 1
                    else:
                        with log_container:
                            st.caption(f"❌ {activo_id}: Error al guardar ({errores_guardar} fallos)")
                        errores += 1
                else:
                    with log_container:
                        st.caption(f"❌ {activo_id}: {mensaje}")
                    errores += 1
            
            progress_bar.progress(1.0)
            status_text.text("✅ Análisis masivo completado")
            
            st.success(f"""
            **Análisis Masivo Finalizado**
            
            - ✅ Nuevos analizados: {exitos}
            - ❌ Errores: {errores}
            - ⏭️ Ya analizados: {omitidos_analizados}
            - ⚠️ Sin valoración DIC: {omitidos_sin_dic}
            """)
            
            # Mostrar activos sin DIC
            if activos_sin_dic:
                with st.expander(f"⚠️ Ver {omitidos_sin_dic} activos sin valoración DIC"):
                    st.warning("""
                    **Estos activos NO fueron analizados porque no tienen valoración DIC completa.**
                    
                    Ve al Tab 2 para completar su valoración D/I/C y luego vuelve a analizarlos.
                    """)
                    for activo_desc in activos_sin_dic:
                        st.write(f"• {activo_desc}")
            
            # Mostrar resumen en tabla
            st.markdown("---")
            st.markdown("### 📊 Resumen de Análisis")
            
            resumen_data = {
                "Categoría": ["✅ Nuevos analizados", "⏭️ Ya analizados", "⚠️ Sin valoración DIC", "❌ Errores", "📊 TOTAL"],
                "Cantidad": [exitos, omitidos_analizados, omitidos_sin_dic, errores, total_activos],
                "Porcentaje": [
                    f"{(exitos/total_activos*100):.1f}%",
                    f"{(omitidos_analizados/total_activos*100):.1f}%",
                    f"{(omitidos_sin_dic/total_activos*100):.1f}%",
                    f"{(errores/total_activos*100):.1f}%",
                    "100%"
                ]
            }
            
            st.dataframe(
                pd.DataFrame(resumen_data),
                use_container_width=True,
                hide_index=True
            )
            
            if st.button("🔄 Recargar para ver resultados", use_container_width=True):
                st.rerun()
        
        st.stop()  # Detener para no mostrar el análisis individual
    
    # ===== MODO INDIVIDUAL =====
    if activo_sel:
        activo_info = activos[activos["ID_Activo"] == activo_sel].iloc[0]
        valoracion = get_valoracion_activo(ID_EVALUACION, activo_sel)
        
        # ===== DETECCIÓN DE ESTADO DEL ACTIVO =====
        vulnerabilidades_existentes = get_vulnerabilidades_activo(ID_EVALUACION, activo_sel)
        ya_analizado = not vulnerabilidades_existentes.empty
        
        # Inicializar estado de re-análisis en session_state
        key_reanalizando = f"reanalizando_{activo_sel}"
        if key_reanalizando not in st.session_state:
            st.session_state[key_reanalizando] = False
        
        # Determinar estado actual
        if ya_analizado and not st.session_state[key_reanalizando]:
            estado_analisis = "ANALIZADO"
        elif ya_analizado and st.session_state[key_reanalizando]:
            estado_analisis = "RE-ANALIZANDO"
        else:
            estado_analisis = "PENDIENTE"
        
        # Extraer valores de criticidad
        criticidad = valoracion.get("Criticidad", 0) if valoracion else 0
        criticidad_nivel = valoracion.get("Criticidad_Nivel", "Sin valorar") if valoracion else "Sin valorar"
        valor_d = valoracion.get("Valor_D", 0) if valoracion else 0
        valor_i = valoracion.get("Valor_I", 0) if valoracion else 0
        valor_c = valoracion.get("Valor_C", 0) if valoracion else 0
        nivel_d = valoracion.get("D", "N") if valoracion else "N"
        nivel_i = valoracion.get("I", "N") if valoracion else "N"
        nivel_c = valoracion.get("C", "N") if valoracion else "N"
        
        # ===== INFORMACIÓN DEL ACTIVO =====
        st.markdown("---")
        st.markdown("### 📋 Información del Activo")
        
        col_id, col_tipo, col_ubic, col_estado = st.columns(4)
        with col_id:
            st.markdown(f"**ID Activo:** `{activo_sel}`")
        with col_tipo:
            st.markdown(f"**Tipo:** {activo_info['Tipo_Activo']}")
        with col_ubic:
            st.markdown(f"**Ubicación:** {activo_info.get('Ubicacion', 'N/A')}")
        with col_estado:
            # Badge de estado
            if estado_analisis == "ANALIZADO":
                st.markdown("**📌 Estado:** 🟢 **Analizado**")
            elif estado_analisis == "RE-ANALIZANDO":
                st.markdown("**📌 Estado:** 🟡 **Re-analizando**")
            else:
                st.markdown("**📌 Estado:** ⚪ **Pendiente**")
        
        # ===== VALORACIÓN D/I/C =====
        st.markdown("### 📊 Valoración del Activo (del Tab 3)")
        col_d, col_i, col_c, col_crit = st.columns(4)
        
        color_map = {"A": "🔴", "M": "🟡", "B": "🟢", "N": "⚪"}
        crit_color = {"Alta": "🔴", "Media": "🟡", "Baja": "🟢", "Nula": "⚪", "Sin valorar": "⚫"}
        
        with col_d:
            st.metric(f"{color_map.get(nivel_d, '⚪')} Disponibilidad", f"{valor_d} ({nivel_d})")
        with col_i:
            st.metric(f"{color_map.get(nivel_i, '⚪')} Integridad", f"{valor_i} ({nivel_i})")
        with col_c:
            st.metric(f"{color_map.get(nivel_c, '⚪')} Confidencialidad", f"{valor_c} ({nivel_c})")
        with col_crit:
            st.metric(f"{crit_color.get(criticidad_nivel, '⚫')} CRITICIDAD", f"{criticidad} ({criticidad_nivel})")
        
        if criticidad == 0:
            st.warning("⚠️ **Atención:** Este activo no tiene valoración D/I/C. Ve a la pestaña 'Valoración D/I/C' primero.")
            st.stop()
        
        st.markdown("---")
        
        # ===== VISTA SEGÚN ESTADO =====
        
        # ===== ESTADO: ANALIZADO (Solo Lectura) =====
        if estado_analisis == "ANALIZADO":
            st.success(f"""
            ✅ **Análisis de Amenazas y Vulnerabilidades Realizado**
            
            Se identificaron **{len(vulnerabilidades_existentes)} amenazas/vulnerabilidades** para este activo.  
            Los resultados alimentan el cálculo de riesgos (Tab 5), salvaguardas (Tab 6) y mapa de riesgos (Tab 7).
            """)
            
            # Mostrar resumen de amenazas
            st.markdown("### 📊 Amenazas Identificadas")
            
            # Calcular estadísticas
            impactos = []
            for idx, row in vulnerabilidades_existentes.iterrows():
                imp_d = valor_d * row.get("Degradacion_D", 0)
                imp_i = valor_i * row.get("Degradacion_I", 0)
                imp_c = valor_c * row.get("Degradacion_C", 0)
                impacto = max(imp_d, imp_i, imp_c)
                impactos.append(impacto)
            
            vulnerabilidades_existentes['Impacto'] = impactos
            
            # Métricas de impacto
            col_met1, col_met2, col_met3, col_met4 = st.columns(4)
            
            with col_met1:
                st.metric("Total Amenazas", len(vulnerabilidades_existentes))
            
            with col_met2:
                alto = sum(1 for i in impactos if i >= 2.0)
                st.metric("Impacto Alto", alto, delta="🔴" if alto > 0 else None)
            
            with col_met3:
                medio = sum(1 for i in impactos if 1.0 <= i < 2.0)
                st.metric("Impacto Medio", medio, delta="🟡" if medio > 0 else None)
            
            with col_met4:
                bajo = sum(1 for i in impactos if i < 1.0)
                st.metric("Impacto Bajo", bajo, delta="🟢" if bajo > 0 else None)
            
            # Tabla resumen
            st.markdown("#### 📋 Lista de Amenazas")
            
            df_display = vulnerabilidades_existentes[['Cod_Amenaza', 'Amenaza', 'Vulnerabilidad', 'Degradacion_D', 'Degradacion_I', 'Degradacion_C', 'Impacto']].copy()
            df_display['Degradacion_D'] = (df_display['Degradacion_D'] * 100).round(0).astype(int)
            df_display['Degradacion_I'] = (df_display['Degradacion_I'] * 100).round(0).astype(int)
            df_display['Degradacion_C'] = (df_display['Degradacion_C'] * 100).round(0).astype(int)
            df_display['Impacto'] = df_display['Impacto'].round(2)
            
            df_display.columns = ['Código', 'Amenaza', 'Vulnerabilidad', 'Deg D (%)', 'Deg I (%)', 'Deg C (%)', 'Impacto']
            
            # Colorear por impacto
            def colorear_impacto(row):
                if row['Impacto'] >= 2.0:
                    return ['background-color: #ff4444; color: white'] * len(row)
                elif row['Impacto'] >= 1.0:
                    return ['background-color: #ffbb33; color: black'] * len(row)
                elif row['Impacto'] >= 0.5:
                    return ['background-color: #00C851; color: white'] * len(row)
                return [''] * len(row)
            
            st.dataframe(
                df_display.style.apply(colorear_impacto, axis=1),
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("---")
            
            # Advertencia sobre re-análisis
            st.warning("""
            ⚠️ **Advertencia sobre Re-Análisis**
            
            Volver a ejecutar el análisis IA afectará:
            - Los riesgos calculados en el Tab 5 (Frecuencia × Impacto)
            - Las salvaguardas recomendadas en el Tab 6
            - El mapa de riesgos completo en el Tab 7
            - Todas las métricas derivadas de amenazas/vulnerabilidades
            
            **Solo re-analice si es absolutamente necesario** (ej: cambio en criticidad D/I/C, nueva información sobre vulnerabilidades).
            """)
            
            # Botón para habilitar re-análisis
            col_re1, col_re2 = st.columns([1, 3])
            with col_re1:
                if st.button("🔄 Habilitar Re-Análisis", type="secondary", use_container_width=True):
                    st.session_state[key_reanalizando] = True
                    st.rerun()
            
            with col_re2:
                st.caption("💡 Al habilitar el re-análisis, la IA volverá a identificar amenazas y vulnerabilidades desde cero.")
        
        # ===== ESTADO: PENDIENTE o RE-ANALIZANDO (Análisis IA Activo) =====
        else:
            if estado_analisis == "RE-ANALIZANDO":
                st.warning("""
                ⚠️ **Modo Re-Análisis Activado**
                
                Está volviendo a analizar un activo que ya tiene amenazas identificadas.  
                Los resultados anteriores serán reemplazados. Esta acción afectará el cálculo de riesgos completo.  
                Proceda con precaución.
                """)
            
            # ===== ANÁLISIS CON IA =====
            st.markdown("### 🤖 Análisis de Amenazas con IA Local")
            st.info("""
            💡 La IA analizará el activo y su criticidad para identificar automáticamente:
            - **Amenazas** del catálogo MAGERIT aplicables
            - **Vulnerabilidades** que permiten que las amenazas se materialicen
            - **Degradación** estimada para D/I/C
            """)
            
            # Usar session_state para almacenar resultados de IA
            key_amenazas = f"amenazas_ia_{activo_sel}"
            
            col_btn1, col_btn2 = st.columns([1, 3])
            with col_btn1:
                texto_boton = "🔍 Re-analizar con IA" if estado_analisis == "RE-ANALIZANDO" else "🔍 Analizar con IA"
                if st.button(texto_boton, type="primary", key="btn_analizar_ia"):
                    with st.spinner("🧠 Analizando activo con IA local..."):
                        # Preparar datos del activo
                        activo_dict = {
                            "ID_Activo": activo_sel,
                            "Nombre_Activo": activo_info['Nombre_Activo'],
                            "Tipo_Activo": activo_info['Tipo_Activo'],
                            "Descripcion": activo_info.get('Descripcion', ''),
                            "Ubicacion": activo_info.get('Ubicacion', '')
                        }
                        
                        valoracion_dict = {
                            "Valor_D": valor_d,
                            "Valor_I": valor_i,
                            "Valor_C": valor_c,
                            "D": nivel_d,
                            "I": nivel_i,
                            "C": nivel_c,
                            "Criticidad": criticidad,
                            "Criticidad_Nivel": criticidad_nivel
                        }
                        
                        # Llamar a la IA
                        exito, amenazas, mensaje = analizar_amenazas_por_criticidad(activo_dict, valoracion_dict)
                        
                        if exito:
                            st.session_state[key_amenazas] = amenazas
                            st.success(f"✅ Análisis completado: Se identificaron **{len(amenazas)} amenazas/vulnerabilidades** para este activo")
                            st.info(f"💡 {mensaje}")
                        else:
                            st.error(f"❌ Error: {mensaje}")
            
            with col_btn2:
                if estado_analisis == "RE-ANALIZANDO":
                    st.caption("⚠️ Este análisis reemplazará las amenazas existentes. La IA usa el catálogo MAGERIT v3.")
                else:
                    st.caption("La IA usa el catálogo MAGERIT v3 para identificar amenazas relevantes según el tipo y criticidad del activo.")
            
            # Botón para cancelar re-análisis
            if estado_analisis == "RE-ANALIZANDO":
                st.markdown("---")
                if st.button("❌ Cancelar Re-Análisis", use_container_width=True):
                    st.session_state[key_reanalizando] = False
                    # Limpiar resultados de IA si existen
                    if key_amenazas in st.session_state:
                        del st.session_state[key_amenazas]
                    st.rerun()
            
            # ===== MOSTRAR RESULTADOS DE IA =====
            if key_amenazas in st.session_state and st.session_state[key_amenazas]:
                amenazas_ia = st.session_state[key_amenazas]
                
                st.markdown("### 📋 Amenazas y Vulnerabilidades Identificadas por IA")
                st.caption(f"Se identificaron **{len(amenazas_ia)}** amenazas/vulnerabilidades para este activo.")
                
                # Mostrar cada amenaza con opción de ajustar y guardar
                amenazas_a_guardar = []
                
                for idx, am in enumerate(amenazas_ia):
                    with st.expander(f"🔴 [{am['codigo_amenaza']}] {am['nombre_amenaza']}", expanded=idx < 3):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown(f"**Tipo de Amenaza:** {am.get('tipo_amenaza', 'N/A')}")
                            st.markdown(f"**Vulnerabilidad Identificada:**")
                            vuln_editada = st.text_area(
                                "Vulnerabilidad",
                                value=am['vulnerabilidad'],
                                height=80,
                                key=f"vuln_{idx}_{activo_sel}_{estado_analisis}",
                                label_visibility="collapsed"
                            )
                            if am.get('justificacion'):
                                st.caption(f"💡 *{am['justificacion']}*")
                        
                        with col2:
                            st.markdown("**Degradación Sugerida:**")
                            deg_d = st.slider(f"D", 0, 100, am['degradacion_d'], 5, key=f"deg_d_{idx}_{activo_sel}_{estado_analisis}")
                            deg_i = st.slider(f"I", 0, 100, am['degradacion_i'], 5, key=f"deg_i_{idx}_{activo_sel}_{estado_analisis}")
                            deg_c = st.slider(f"C", 0, 100, am['degradacion_c'], 5, key=f"deg_c_{idx}_{activo_sel}_{estado_analisis}")
                            
                            # Calcular impacto
                            imp_d = valor_d * (deg_d / 100)
                            imp_i = valor_i * (deg_i / 100)
                            imp_c = valor_c * (deg_c / 100)
                            impacto = max(imp_d, imp_i, imp_c)
                            
                            if impacto >= 2.0:
                                st.error(f"Impacto: **{impacto:.2f}** (Alto)")
                            elif impacto >= 1.0:
                                st.warning(f"Impacto: **{impacto:.2f}** (Medio)")
                            elif impacto >= 0.5:
                                st.info(f"Impacto: **{impacto:.2f}** (Bajo)")
                            else:
                                st.success(f"Impacto: **{impacto:.2f}** (Nulo)")
                        
                        # Checkbox para incluir
                        incluir = st.checkbox("✅ Incluir esta amenaza", value=True, key=f"incluir_{idx}_{activo_sel}_{estado_analisis}")
                        
                        if incluir:
                            amenazas_a_guardar.append({
                                "codigo": am['codigo_amenaza'],
                                "codigo_vuln": am.get('codigo_vulnerabilidad', ''),
                                "nombre": am['nombre_amenaza'],
                                "vulnerabilidad": vuln_editada,
                                "deg_d": deg_d,
                                "deg_i": deg_i,
                                "deg_c": deg_c,
                                "impacto": impacto
                            })
                
                st.markdown("---")
                
                # Botón para guardar todas las amenazas seleccionadas
                st.markdown("### 💾 Guardar Amenazas Seleccionadas")
                
                if estado_analisis == "RE-ANALIZANDO":
                    st.warning(f"""
                    ⚠️ **Confirmación de Re-Análisis**
                    
                    Se eliminarán las **{len(vulnerabilidades_existentes)} amenazas existentes** y se guardarán **{len(amenazas_a_guardar)} nuevas amenazas**.
                    
                    Esta acción:
                    - Recalculará todos los riesgos en el Tab 5
                    - Regenerará las salvaguardas en el Tab 6
                    - Actualizará el mapa de riesgos en el Tab 7
                    """)
                
                col_save1, col_save2 = st.columns([1, 2])
                
                with col_save1:
                    texto_guardar = "💾 Confirmar Re-Análisis" if estado_analisis == "RE-ANALIZANDO" else "💾 Guardar Todas"
                    if st.button(texto_guardar, type="primary", key="btn_guardar_amenazas"):
                        # Si es re-análisis, eliminar amenazas existentes primero
                        if estado_analisis == "RE-ANALIZANDO":
                            with get_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    DELETE FROM VULNERABILIDADES_AMENAZAS 
                                    WHERE ID_Evaluacion = ? AND ID_Activo = ?
                                """, (ID_EVALUACION, activo_sel))
                                conn.commit()
                        
                        guardadas = 0
                        for am in amenazas_a_guardar:
                            try:
                                agregar_vulnerabilidad_amenaza(
                                    id_evaluacion=ID_EVALUACION,
                                    id_activo=activo_sel,
                                    nombre_activo=activo_info['Nombre_Activo'],
                                    vulnerabilidad=am['vulnerabilidad'],
                                    amenaza=am['nombre'],
                                    cod_amenaza=am['codigo'],
                                    cod_vulnerabilidad=am.get('codigo_vuln', ''),
                                    deg_d=am['deg_d'] / 100,
                                    deg_i=am['deg_i'] / 100,
                                    deg_c=am['deg_c'] / 100
                                )
                                guardadas += 1
                            except Exception as e:
                                st.error(f"Error guardando {am['codigo']}: {e}")
                        
                        if guardadas > 0:
                            if estado_analisis == "RE-ANALIZANDO":
                                st.success(f"✅ Re-análisis completado: Se guardaron {guardadas} amenazas/vulnerabilidades")
                                st.warning("⚠️ Recuerde revisar y recalcular los riesgos en el Tab 5.")
                            else:
                                st.success(f"✅ Se guardaron {guardadas} amenazas/vulnerabilidades")
                            
                            # Limpiar resultados de IA
                            del st.session_state[key_amenazas]
                            # Desactivar modo re-análisis
                            st.session_state[key_reanalizando] = False
                            
                            time.sleep(1)
                            st.rerun()
                
                with col_save2:
                    st.caption(f"Se guardarán **{len(amenazas_a_guardar)}** amenazas seleccionadas con sus degradaciones.")
    
    st.markdown("---")
    
    # ===== TABLA UNIFICADA DE VULNERABILIDADES/AMENAZAS =====
    st.subheader("📋 Registro de Vulnerabilidades y Amenazas")
    st.caption("💡 Pasa el mouse sobre Amenaza o Vulnerabilidad para ver la descripción completa")
    
    # Obtener filtro global
    filtro_global = st.session_state.get("activo_filtro_global", "TODOS")
    
    todas_vulns = get_vulnerabilidades_evaluacion(ID_EVALUACION)
    
    # Aplicar filtro si no es TODOS
    if filtro_global != "TODOS" and not todas_vulns.empty:
        todas_vulns = todas_vulns[todas_vulns["ID_Activo"] == filtro_global]
        if not todas_vulns.empty:
            st.info(f"🎯 Mostrando vulnerabilidades del activo filtrado: **{todas_vulns['Nombre_Activo'].values[0]}**")
    
    if not todas_vulns.empty:
        # Enriquecer con datos de valoración
        for idx, row in todas_vulns.iterrows():
            val = get_valoracion_activo(ID_EVALUACION, row["ID_Activo"])
            if val:
                todas_vulns.loc[idx, "Criticidad"] = val.get("Criticidad", 0)
                todas_vulns.loc[idx, "Criticidad_Nivel"] = val.get("Criticidad_Nivel", "N/A")
                v_d = val.get("Valor_D", 0)
                v_i = val.get("Valor_I", 0)
                v_c = val.get("Valor_C", 0)
                todas_vulns.loc[idx, "Impacto"] = max(
                    v_d * row.get("Degradacion_D", 0),
                    v_i * row.get("Degradacion_I", 0),
                    v_c * row.get("Degradacion_C", 0)
                )
            else:
                todas_vulns.loc[idx, "Criticidad"] = 0
                todas_vulns.loc[idx, "Criticidad_Nivel"] = "N/A"
                todas_vulns.loc[idx, "Impacto"] = 0
        
        # Función para escapar HTML
        def escape_html(text):
            return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
        
        # Construir tabla HTML con tooltips (estilo similar a st.dataframe)
        num_rows = len(todas_vulns)
        table_height = min(400, 45 + num_rows * 38)
        
        html_table = f'''
        <style>
            .st-table-container {{
                max-height: {table_height}px;
                overflow-y: auto;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }}
            .st-table {{
                width: 100%;
                border-collapse: collapse;
                font-family: "Source Sans Pro", sans-serif;
                font-size: 14px;
            }}
            .st-table th {{
                background-color: #fafafa;
                color: #31333F;
                padding: 8px 12px;
                text-align: left;
                font-weight: 600;
                border-bottom: 1px solid #e0e0e0;
                position: sticky;
                top: 0;
                z-index: 10;
            }}
            .st-table td {{
                padding: 8px 12px;
                border-bottom: 1px solid #f0f0f0;
                color: #31333F;
            }}
            .st-table tr:hover {{
                background-color: #f5f5f5;
            }}
            .tooltip-link {{
                color: #0068c9;
                text-decoration: none;
                border-bottom: 1px dotted #0068c9;
                cursor: help;
                position: relative;
            }}
            .tooltip-link:hover {{
                color: #0054a3;
            }}
        </style>
        <div class="st-table-container">
        <table class="st-table">
            <thead>
                <tr>
                    <th>Nombre_Activo</th>
                    <th>Criticidad</th>
                    <th>Cod_Amenaza</th>
                    <th>Cod_Vuln</th>
                    <th>Deg_D</th>
                    <th>Deg_I</th>
                    <th>Deg_C</th>
                    <th>Impacto</th>
                </tr>
            </thead>
            <tbody>
        '''
        
        # Cargar catálogo de amenazas para tooltips enriquecidos
        catalogo_amenazas_tab4 = get_catalogo_amenazas()
        
        for idx, row in todas_vulns.iterrows():
            nombre = escape_html(row.get("Nombre_Activo", "N/A"))
            crit = row.get("Criticidad_Nivel", "N/A")
            cod = escape_html(row.get("Cod_Amenaza", "N/A"))
            amenaza_nombre = escape_html(row.get("Amenaza", "Sin descripción"))
            
            # Tooltip enriquecido para amenaza: nombre + descripción del catálogo
            amenaza_tooltip_nombre = amenaza_nombre
            amenaza_tooltip_desc = ""
            if cod and catalogo_amenazas_tab4.get(cod):
                info_amenaza = catalogo_amenazas_tab4[cod]
                amenaza_tooltip_nombre = escape_html(info_amenaza.get('amenaza', amenaza_nombre))
                amenaza_tooltip_desc = escape_html(info_amenaza.get('descripcion', info_amenaza.get('tipo_amenaza', '')))
            
            # Tooltip para vulnerabilidad - simple como amenaza
            vuln_texto = row.get("Vulnerabilidad", "Sin descripción")
            vuln_tooltip = escape_html(vuln_texto)
            
            # Obtener código de vulnerabilidad del catálogo (si existe)
            cod_vuln = row.get("Cod_Vulnerabilidad", "")
            if not cod_vuln or cod_vuln == "":
                # Fallback: generar código temporal si no hay en BD
                cod_vuln = f"V{idx+1:03d}"
            
            deg_d = f"{row.get('Degradacion_D', 0)*100:.0f}%"
            deg_i = f"{row.get('Degradacion_I', 0)*100:.0f}%"
            deg_c = f"{row.get('Degradacion_C', 0)*100:.0f}%"
            impacto = f"{row.get('Impacto', 0):.2f}"
            
            html_table += f'''
                <tr>
                    <td>{nombre}</td>
                    <td>{crit}</td>
                    <td><span class="tooltip-link" title="{amenaza_tooltip_nombre} - {amenaza_tooltip_desc}">{cod}</span></td>
                    <td><span class="tooltip-link" title="{vuln_tooltip}">{cod_vuln}</span></td>
                    <td>{deg_d}</td>
                    <td>{deg_i}</td>
                    <td>{deg_c}</td>
                    <td>{impacto}</td>
                </tr>
            '''
        
        html_table += '''
            </tbody>
        </table>
        </div>
        '''
        
        components.html(html_table, height=table_height + 20, scrolling=False)
        
        # Estadísticas
        st.markdown("### 📈 Estadísticas")
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.metric("Total Registros", len(todas_vulns))
        with col_stat2:
            if "Impacto" in todas_vulns.columns:
                alto_impacto = len(todas_vulns[todas_vulns["Impacto"] >= 1.5])
                st.metric("Alto Impacto (≥1.5)", alto_impacto)
        with col_stat3:
            activos_afectados = todas_vulns["ID_Activo"].nunique()
            st.metric("Activos Afectados", activos_afectados)
        
        # Eliminar vulnerabilidad
        with st.expander("🗑️ Eliminar Vulnerabilidad/Amenaza"):
            vuln_a_eliminar = st.selectbox(
                "Seleccionar para eliminar",
                todas_vulns["id"].tolist(),
                format_func=lambda x: f"[{todas_vulns[todas_vulns['id'] == x]['Nombre_Activo'].values[0]}] {todas_vulns[todas_vulns['id'] == x]['Cod_Amenaza'].values[0]} - {str(todas_vulns[todas_vulns['id'] == x]['Vulnerabilidad'].values[0])[:30]}...",
                key="sel_eliminar_vuln_unificado"
            )
            if st.button("🗑️ Eliminar", type="secondary", key="btn_del_vuln_unificado"):
                eliminar_vulnerabilidad_amenaza(vuln_a_eliminar)
                st.success("✅ Vulnerabilidad/Amenaza eliminada")
                st.rerun()
    else:
        st.info("📭 No hay vulnerabilidades/amenazas registradas en esta evaluación.")


# ==================== TAB 5: RIESGO (FRECUENCIA AUTOMÁTICA) ====================

with tab5:
    st.header("⚡ Cálculo de Riesgo")
    st.markdown("""
    **Propósito:** Calcular el riesgo para cada par activo-amenaza identificado.
    
    **Fórmula MAGERIT:** `RIESGO = FRECUENCIA × IMPACTO`
    
    ⚠️ **Importante:** El cálculo de riesgos se ejecuta una vez. Los resultados alimentan el mapa de riesgos, agregaciones y salvaguardas.
    """)
    
    # Importar función de cálculo de frecuencia
    from services.cuestionario_dic_service import calcular_frecuencia_desde_cuestionario, calcular_frecuencia_todas_amenazas
    
    # Mostrar escalas de referencia
    with st.expander("📊 Ver Escalas de Referencia MAGERIT", expanded=False):
        col_ref1, col_ref2, col_ref3 = st.columns(3)
        
        with col_ref1:
            st.markdown("**📅 Frecuencia:**")
            st.markdown("""
            | Valor | Nivel | Descripción |
            |:-----:|:-----:|:------------|
            | 0.1 | Nula | Cada varios años |
            | 1 | Baja | 1 vez al año |
            | 2 | Media | Mensualmente |
            | 3 | Alta | A diario |
            """)
        
        with col_ref2:
            st.markdown("**💥 Impacto:**")
            st.markdown("""
            | Rango | Nivel |
            |:-----:|:-----:|
            | ≥ 2.0 | Alto 🔴 |
            | ≥ 1.0 | Medio 🟡 |
            | ≥ 0.5 | Bajo 🟢 |
            | < 0.5 | Nulo ⚪ |
            """)
        
        with col_ref3:
            st.markdown("**⚠️ Riesgo:**")
            st.markdown("""
            | Rango | Nivel |
            |:-----:|:-----:|
            | ≥ 6.0 | Alto 🔴 |
            | ≥ 4.0 | Medio 🟡 |
            | ≥ 2.0 | Bajo 🟢 |
            | < 2.0 | Nulo ⚪ |
            """)
    
    # Obtener vulnerabilidades
    todas_vulns = get_vulnerabilidades_evaluacion(ID_EVALUACION)
    activos = get_activos_matriz(ID_EVALUACION)
    
    # Obtener filtro global
    filtro_global = st.session_state.get("activo_filtro_global", "TODOS")
    
    if todas_vulns.empty:
        st.warning("⚠️ No hay vulnerabilidades/amenazas identificadas. Ve a la pestaña 'Vulnerabilidades y Amenazas' primero.")
        st.stop()
    
    st.markdown("---")
    
    # ===== DETECCIÓN DE ESTADO =====
    riesgos_existentes = get_riesgos_evaluacion(ID_EVALUACION)
    ya_calculado = not riesgos_existentes.empty
    
    # Estado de recálculo
    if "recalculando_riesgos" not in st.session_state:
        st.session_state.recalculando_riesgos = False
    
    if ya_calculado and not st.session_state.recalculando_riesgos:
        estado_calculo = "CALCULADO"
    elif ya_calculado and st.session_state.recalculando_riesgos:
        estado_calculo = "RECALCULANDO"
    else:
        estado_calculo = "PENDIENTE"
    
    # ===== CALCULAR RIESGOS PARA TODOS LOS ACTIVOS =====
    st.subheader("🔄 Calcular Riesgos")
    
    # Badge de estado
    if estado_calculo == "CALCULADO":
        st.success(f"✅ **Riesgos Calculados**: Se identificaron **{len(riesgos_existentes)} riesgos** en la evaluación. Los resultados alimentan el mapa de riesgos (Tab 6), agregación (Tab 7) y salvaguardas (Tab 8).")
    elif estado_calculo == "RECALCULANDO":
        st.warning("⚠️ **Modo Recálculo Activado**: Los riesgos existentes serán eliminados y recalculados. Esta acción afectará el mapa de riesgos y las salvaguardas.")
    
    # Aplicar filtro a activos si no es TODOS
    if filtro_global != "TODOS" and not activos.empty:
        activos_calc = activos[activos["ID_Activo"] == filtro_global]
        if not activos_calc.empty:
            st.info(f"🎯 Calculando riesgos para activo filtrado: **{activos_calc['Nombre_Activo'].values[0]}**")
    else:
        activos_calc = activos
    
    # ===== VISTA SEGÚN ESTADO =====
    if estado_calculo == "CALCULADO":
        # Mostrar resumen
        col_met1, col_met2, col_met3, col_met4 = st.columns(4)
        with col_met1:
            st.metric("Total Riesgos", len(riesgos_existentes))
        with col_met2:
            alto = sum(1 for _, r in riesgos_existentes.iterrows() if r.get("Riesgo", 0) >= 6.0)
            st.metric("Riesgo Alto", alto, delta="🔴" if alto > 0 else None)
        with col_met3:
            medio = sum(1 for _, r in riesgos_existentes.iterrows() if 4.0 <= r.get("Riesgo", 0) < 6.0)
            st.metric("Riesgo Medio", medio, delta="🟡" if medio > 0 else None)
        with col_met4:
            bajo = sum(1 for _, r in riesgos_existentes.iterrows() if r.get("Riesgo", 0) < 4.0)
            st.metric("Riesgo Bajo", bajo, delta="🟢" if bajo > 0 else None)
        
        st.markdown("---")
        
        # Advertencia sobre recálculo
        st.warning("""
        ⚠️ **Advertencia sobre Recálculo**
        
        Recalcular los riesgos afectará:
        - El mapa de riesgos en el Tab 6
        - La agregación de riesgos por activo en el Tab 7
        - Las salvaguardas recomendadas en el Tab 8
        - Todas las métricas derivadas de riesgos
        
        **Solo recalcule si cambió la frecuencia de amenazas o la valoración D/I/C.**
        """)
        
        # Botón para habilitar recálculo
        col_re1, col_re2 = st.columns([1, 3])
        with col_re1:
            if st.button("🔄 Habilitar Recálculo", type="secondary", use_container_width=True):
                st.session_state.recalculando_riesgos = True
                st.rerun()
        with col_re2:
            st.caption("💡 Al habilitar el recálculo, podrá ejecutar el cálculo de riesgos nuevamente.")
    
    else:
        # PENDIENTE o RECALCULANDO
        col_calc1, col_calc2 = st.columns([1, 2])
        with col_calc1:
            texto_boton = "⚡ Recalcular Todos los Riesgos" if estado_calculo == "RECALCULANDO" else "⚡ Calcular Todos los Riesgos"
            if st.button(texto_boton, type="primary", key="calc_all_risks"):
                # Si es recálculo, eliminar riesgos existentes
                if estado_calculo == "RECALCULANDO":
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM RIESGO_AMENAZA WHERE ID_Evaluacion = ?", (ID_EVALUACION,))
                        conn.commit()
                
                total_guardados = 0
                for _, activo in activos_calc.iterrows():
                    id_activo = activo["ID_Activo"]
                    amenazas = calcular_frecuencia_todas_amenazas(ID_EVALUACION, id_activo)
                    for am in amenazas:
                        calcular_riesgo_amenaza(
                            id_evaluacion=ID_EVALUACION,
                            id_activo=id_activo,
                            id_va=am['id_va'],
                            frecuencia=am['frecuencia']
                        )
                        total_guardados += 1
                
                if estado_calculo == "RECALCULANDO":
                    st.success(f"✅ Recálculo completado: {total_guardados} riesgos recalculados")
                    st.warning("⚠️ Recuerde revisar el mapa de riesgos (Tab 6) y salvaguardas (Tab 8).")
                else:
                    st.success(f"✅ Se calcularon y guardaron {total_guardados} riesgos")
                
                st.session_state.recalculando_riesgos = False
                time.sleep(1)
                st.rerun()
        
        with col_calc2:
            if estado_calculo == "RECALCULANDO":
                st.caption("⚠️ Este recálculo eliminará los riesgos existentes y los calculará nuevamente desde cero.")
            else:
                st.caption("Calcula automáticamente la frecuencia basándose en criticidad, RTO y BIA de cada activo.")
        
        # Botón cancelar si está recalculando
        if estado_calculo == "RECALCULANDO":
            st.markdown("---")
            if st.button("❌ Cancelar Recálculo", use_container_width=True):
                st.session_state.recalculando_riesgos = False
                st.rerun()
    
    st.markdown("---")
    
    # ===== TABLA UNIFICADA DE RIESGOS =====
    st.subheader("📋 Resumen de Riesgos")
    st.caption("💡 Pasa el mouse sobre la Amenaza para ver la descripción completa")
    
    riesgos = get_riesgos_evaluacion(ID_EVALUACION)
    
    # Aplicar filtro si no es TODOS
    if filtro_global != "TODOS" and not riesgos.empty:
        riesgos = riesgos[riesgos["ID_Activo"] == filtro_global]
        if not riesgos.empty:
            st.info(f"🎯 Mostrando riesgos del activo filtrado: **{riesgos['Nombre_Activo'].values[0]}**")
    
    if not riesgos.empty:
        # Función para escapar HTML
        def escape_html(text):
            return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
        
        # Tabla HTML con tooltip en Amenaza
        num_rows = len(riesgos)
        table_height = min(420, 45 + num_rows * 38)
        
        html_table = f'''
        <style>
            .risk-table-container {{
                max-height: {table_height}px;
                overflow-y: auto;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }}
            .risk-table {{
                width: 100%;
                border-collapse: collapse;
                font-family: "Source Sans Pro", sans-serif;
                font-size: 14px;
            }}
            .risk-table th {{
                background-color: #fafafa;
                color: #31333F;
                padding: 8px 12px;
                text-align: left;
                font-weight: 600;
                border-bottom: 1px solid #e0e0e0;
                position: sticky;
                top: 0;
                z-index: 10;
            }}
            .risk-table td {{
                padding: 8px 12px;
                border-bottom: 1px solid #f0f0f0;
                color: #31333F;
            }}
            .risk-table tr:hover {{
                background-color: #f5f5f5;
            }}
            .tooltip-link {{
                color: #0068c9;
                text-decoration: none;
                border-bottom: 1px dotted #0068c9;
                cursor: help;
            }}
            .tooltip-link:hover {{
                color: #0054a3;
            }}
        </style>
        <div class="risk-table-container">
        <table class="risk-table">
            <thead>
                <tr>
                    <th>Activo</th>
                    <th>Amenaza</th>
                    <th>Frecuencia</th>
                    <th>Impacto</th>
                    <th>Riesgo</th>
                </tr>
            </thead>
            <tbody>
        '''
        
        # Cargar catálogo de amenazas para tooltips enriquecidos
        catalogo_amenazas_tab5 = get_catalogo_amenazas()
        
        for _, row in riesgos.iterrows():
            nombre = escape_html(row.get("Nombre_Activo", "N/A"))
            cod_amenaza = escape_html(row.get("Cod_Amenaza", "N/A"))
            amenaza_nombre = escape_html(row.get("Amenaza", "Sin descripción"))
            
            # Tooltip enriquecido: nombre + descripción del catálogo (sin dimensión)
            amenaza_tooltip = amenaza_nombre
            if cod_amenaza and catalogo_amenazas_tab5.get(cod_amenaza):
                info_am = catalogo_amenazas_tab5[cod_amenaza]
                nombre_am = escape_html(info_am.get('amenaza', amenaza_nombre))
                desc_am = escape_html(info_am.get('descripcion', info_am.get('tipo_amenaza', '')))
                amenaza_tooltip = f"{nombre_am} - {desc_am}"
            
            freq = row.get("Frecuencia", 0)
            impacto = row.get("Impacto", 0)
            riesgo_val = row.get("Riesgo", 0)
            
            html_table += f'''
                <tr>
                    <td>{nombre}</td>
                    <td><span class="tooltip-link" title="{amenaza_tooltip}">{cod_amenaza}</span></td>
                    <td>{float(freq):.2f}</td>
                    <td>{float(impacto):.2f}</td>
                    <td>{float(riesgo_val):.2f}</td>
                </tr>
            '''
        
        html_table += '''
            </tbody>
        </table>
        </div>
        '''
        
        components.html(html_table, height=table_height + 20, scrolling=False)
        
        # Estadísticas
        st.markdown("### 📈 Estadísticas de Riesgo")
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("Total Riesgos", len(riesgos))
        with col_stat2:
            altos = len(riesgos[riesgos["Riesgo"] >= 6])
            st.metric("🔴 Altos (≥6)", altos)
        with col_stat3:
            medios = len(riesgos[(riesgos["Riesgo"] >= 4) & (riesgos["Riesgo"] < 6)])
            st.metric("🟡 Medios (4-6)", medios)
        with col_stat4:
            riesgo_promedio = riesgos["Riesgo"].mean()
            st.metric("📊 Promedio", f"{riesgo_promedio:.2f}")
    else:
        st.info("📭 No hay riesgos calculados. Presiona 'Calcular Todos los Riesgos' para generarlos.")


# ==================== TAB 6: MAPA DE RIESGOS ====================

with tab6:
    st.header("🗺️ Mapa de Riesgos")
    st.markdown("""
    **Propósito:** Matriz visual de riesgos (Impacto vs Frecuencia) como en Excel.
    
    **Los riesgos provienen de:**
    1. **Tab 4:** Identificación de amenazas/vulnerabilidades con degradación → IMPACTO
    2. **Tab 5:** Cálculo de frecuencia (automático) → RIESGO = FRECUENCIA × IMPACTO
    """)
    
    # Obtener filtro global
    filtro_global = st.session_state.get("activo_filtro_global", "TODOS")
    
    # Obtener riesgos calculados (del Tab 5)
    riesgos = get_riesgos_evaluacion(ID_EVALUACION)
    
    # Aplicar filtro si no es TODOS
    if filtro_global != "TODOS" and not riesgos.empty:
        riesgos = riesgos[riesgos["ID_Activo"] == filtro_global]
        if not riesgos.empty:
            st.info(f"🎯 Mostrando riesgos del activo filtrado: **{riesgos['Nombre_Activo'].iloc[0]}**")
        else:
            st.warning(f"⚠️ El activo filtrado `{filtro_global}` no tiene riesgos calculados.")
    
    if riesgos.empty:
        st.warning("⚠️ No hay riesgos calculados. Ve al Tab 5 (Riesgo) primero para calcular los riesgos.")
        st.info("""
        **Flujo para generar riesgos:**
        1. Tab 2: Agregar activos
        2. Tab 3: Completar cuestionario D/I/C (calcula criticidad)
        3. Tab 4: Identificar amenazas con IA (calcula impacto)
        4. Tab 5: Calcular riesgos (frecuencia × impacto)
        5. Tab 6: Ver mapa de riesgos ← **Estás aquí**
        """)
        st.stop()
    
    # ===== ESTADÍSTICAS RÁPIDAS =====
    st.markdown("### 📈 Resumen de Riesgos")
    
    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
    
    total = len(riesgos)
    altos_count = len(riesgos[riesgos["Riesgo"] >= 6])
    medios_count = len(riesgos[(riesgos["Riesgo"] >= 4) & (riesgos["Riesgo"] < 6)])
    bajos_count = len(riesgos[(riesgos["Riesgo"] >= 2) & (riesgos["Riesgo"] < 4)])
    nulos_count = len(riesgos[riesgos["Riesgo"] < 2])
    
    with col_s1:
        st.metric("📊 Total", total)
    with col_s2:
        st.metric("🔴 Altos", altos_count)
    with col_s3:
        st.metric("🟡 Medios", medios_count)
    with col_s4:
        st.metric("🟢 Bajos", bajos_count)
    with col_s5:
        st.metric("⚪ Nulos", nulos_count)
    
    st.markdown("---")
    
    # ===== MAPA DE CALOR (MATRIZ PROBABILIDAD × IMPACTO) =====
    st.markdown("### 🗺️ Matriz de Riesgos (Probabilidad × Impacto)")
    st.caption("Como en Excel: Las celdas muestran cuántos riesgos caen en cada zona.")
    
    # Crear matriz 4x4 (Frecuencia vs Impacto)
    # Frecuencia: 0.1 (Nula), 1 (Baja), 2 (Media), 3 (Alta)
    # Impacto: <0.5 (Nulo), 0.5-1.0 (Bajo), 1.0-2.0 (Medio), >=2.0 (Alto)
    
    # Clasificar cada riesgo en la matriz
    def clasificar_frecuencia(f):
        if f >= 2.5: return "Alta"
        elif f >= 1.5: return "Media"
        elif f >= 0.5: return "Baja"
        else: return "Nula"
    
    def clasificar_impacto(i):
        if i >= 2.0: return "Alto"
        elif i >= 1.0: return "Medio"
        elif i >= 0.5: return "Bajo"
        else: return "Nulo"
    
    riesgos["Freq_Nivel"] = riesgos["Frecuencia"].apply(clasificar_frecuencia)
    riesgos["Imp_Nivel"] = riesgos["Impacto"].apply(clasificar_impacto)
    
    # Contar riesgos por celda
    freq_niveles = ["Nula", "Baja", "Media", "Alta"]
    imp_niveles = ["Nulo", "Bajo", "Medio", "Alto"]
    
    # Crear matriz de conteo
    matriz_data = []
    for imp in reversed(imp_niveles):  # De arriba a abajo: Alto -> Nulo
        fila = {"Impacto": imp}
        for freq in freq_niveles:
            count = len(riesgos[(riesgos["Freq_Nivel"] == freq) & (riesgos["Imp_Nivel"] == imp)])
            fila[freq] = count
        matriz_data.append(fila)
    
    df_matriz = pd.DataFrame(matriz_data)
    df_matriz.set_index("Impacto", inplace=True)
    
    # Definir colores para cada celda de la matriz
    # Formato: [fila (impacto)][columna (frecuencia)]
    colores_matriz = {
        ("Alto", "Alta"): "#ff0000",        # Rojo intenso
        ("Alto", "Media"): "#ff4444",       # Rojo
        ("Alto", "Baja"): "#ff8800",        # Naranja
        ("Alto", "Nula"): "#ffbb33",        # Amarillo oscuro
        ("Medio", "Alta"): "#ff4444",       # Rojo
        ("Medio", "Media"): "#ff8800",      # Naranja
        ("Medio", "Baja"): "#ffbb33",       # Amarillo oscuro
        ("Medio", "Nula"): "#ffdd00",       # Amarillo
        ("Bajo", "Alta"): "#ff8800",        # Naranja
        ("Bajo", "Media"): "#ffbb33",       # Amarillo oscuro
        ("Bajo", "Baja"): "#ffdd00",        # Amarillo
        ("Bajo", "Nula"): "#99dd00",        # Verde amarillo
        ("Nulo", "Alta"): "#ffbb33",        # Amarillo oscuro
        ("Nulo", "Media"): "#ffdd00",       # Amarillo
        ("Nulo", "Baja"): "#99dd00",        # Verde amarillo
        ("Nulo", "Nula"): "#00C851",        # Verde
    }
    
    # Crear mapa de calor con Plotly
    z_values = df_matriz.values
    x_labels = ["Nula (0.1)", "Baja (1)", "Media (2)", "Alta (3)"]
    y_labels = ["Alto (≥2.0)", "Medio (1.0-2.0)", "Bajo (0.5-1.0)", "Nulo (<0.5)"]
    
    # Crear colores personalizados para cada celda
    colorscale = [
        [0, "#00C851"],      # Verde
        [0.25, "#99dd00"],   # Verde amarillo
        [0.5, "#ffdd00"],    # Amarillo
        [0.75, "#ff8800"],   # Naranja
        [1, "#ff0000"]       # Rojo
    ]
    
    # Calcular nivel de riesgo para cada celda (para colorear)
    z_colors = []
    for i, imp in enumerate(["Alto", "Medio", "Bajo", "Nulo"]):
        fila_colores = []
        for j, freq in enumerate(["Nula", "Baja", "Media", "Alta"]):
            # El color depende de la zona de riesgo (no del conteo)
            # Zona = posición en la matriz
            riesgo_zona = (3-i) + j  # 0-6 escala
            fila_colores.append(riesgo_zona)
        z_colors.append(fila_colores)
    
    # Crear texto para mostrar en cada celda
    text_values = []
    for i, imp in enumerate(reversed(imp_niveles)):
        fila_texto = []
        for freq in freq_niveles:
            count = df_matriz.loc[imp, freq]
            if count > 0:
                # Obtener los riesgos en esta celda
                riesgos_celda = riesgos[(riesgos["Freq_Nivel"] == freq) & (riesgos["Imp_Nivel"] == imp)]
                nombres = riesgos_celda["Nombre_Activo"].unique()[:3]
                if len(nombres) > 0:
                    texto = f"{count}\n" + "\n".join(nombres[:2])
                else:
                    texto = str(count)
            else:
                texto = "-"
            fila_texto.append(texto)
        text_values.append(fila_texto)
    
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=z_colors,
        x=x_labels,
        y=y_labels,
        text=z_values,
        texttemplate="%{text}",
        textfont={"size": 20, "color": "white"},
        colorscale=colorscale,
        showscale=False,
        hovertemplate="Impacto: %{y}<br>Frecuencia: %{x}<br>Cantidad: %{text}<extra></extra>"
    ))
    
    fig_heatmap.update_layout(
        title="Matriz de Riesgos - Impacto vs Frecuencia (Probabilidad)",
        xaxis_title="FRECUENCIA (Probabilidad)",
        yaxis_title="IMPACTO",
        height=400,
        xaxis=dict(side="bottom"),
        yaxis=dict(autorange="reversed")
    )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Leyenda
    col_leg1, col_leg2, col_leg3, col_leg4 = st.columns(4)
    with col_leg1:
        st.markdown("🟢 **Riesgo Nulo** - Aceptar/Monitorear")
    with col_leg2:
        st.markdown("🟡 **Riesgo Bajo** - Monitorear")
    with col_leg3:
        st.markdown("🟠 **Riesgo Medio** - Reducir si es posible")
    with col_leg4:
        st.markdown("🔴 **Riesgo Alto** - Acción inmediata")
    
    st.markdown("---")
    
    # ===== TABLA UNIFICADA DE RIESGOS =====
    st.markdown("### 📋 Lista de Riesgos")
    
    riesgos_display = riesgos.copy()
    riesgos_display["Riesgo_ID"] = riesgos_display.index.map(lambda x: f"R{x+1}")
    
    def construir_descripcion(row):
        activo = row.get("Nombre_Activo", "N/A")
        amenaza = row.get("Amenaza", "N/A")
        cod_amenaza = row.get("Cod_Amenaza", "")
        vulnerabilidad = row.get("Vulnerabilidad", "")
        
        descripcion = f"Riesgo en '{activo}' por amenaza {cod_amenaza}: {amenaza}"
        if vulnerabilidad and vulnerabilidad != "N/A" and len(str(vulnerabilidad)) > 5:
            descripcion += f". Vulnerabilidad: {str(vulnerabilidad)[:80]}..."
        return descripcion
    
    riesgos_display["Descripcion"] = riesgos_display.apply(construir_descripcion, axis=1)
    
    df_unificada = riesgos_display[["Riesgo_ID", "Impacto", "Frecuencia", "Riesgo", "Descripcion"]].copy()
    df_unificada["Impacto"] = df_unificada["Impacto"].apply(lambda x: f"{x:.2f}")
    df_unificada["Frecuencia"] = df_unificada["Frecuencia"].apply(lambda x: f"{x:.2f}")
    df_unificada["Riesgo"] = df_unificada["Riesgo"].apply(lambda x: f"{x:.2f}")
    
    st.dataframe(
        df_unificada,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Riesgo_ID": st.column_config.TextColumn("ID", width="small"),
            "Impacto": st.column_config.TextColumn("Impacto", width="small"),
            "Frecuencia": st.column_config.TextColumn("Frecuencia", width="small"),
            "Riesgo": st.column_config.TextColumn("Riesgo", width="small"),
            "Descripcion": st.column_config.TextColumn("Descripción", width="large")
        }
    )
    
    st.download_button(
        label="📥 Descargar Lista de Riesgos (CSV)",
        data=df_unificada.to_csv(index=False, encoding='utf-8-sig'),
        file_name="lista_riesgos.csv",
        mime="text/csv"
    )
    
    # ===== GUARDAR MAPA =====
    st.markdown("---")
    if st.button("💾 Guardar Mapa de Riesgos", type="primary"):
        generar_mapa_riesgos(ID_EVALUACION)
        st.success("✅ Mapa de riesgos guardado en la base de datos")



# ==================== TAB 7: RIESGO POR ACTIVOS ====================

with tab7:
    st.header("📊 Riesgos por Activo")
    st.markdown("""
    **Propósito:** Vista consolidada del riesgo por activo con objetivo y límite organizacional.
    
    **Columnas:**
    - **Riesgo Actual**: Promedio de todos los riesgos del activo
    - **Objetivo**: Meta de riesgo a alcanzar (Actual × 0.7)
    - **Límite**: Umbral máximo aceptable (constante: 4.0)
    - **Observaciones**: Recomendaciones generadas automáticamente
    
    ⚠️ **Importante:** La agregación de riesgos se calcula una vez. Recalcule solo si cambió el Tab 5 (Riesgos individuales).
    """)
    
    # Obtener filtro global
    filtro_global = st.session_state.get("activo_filtro_global", "TODOS")
    
    # ===== DETECCIÓN DE ESTADO =====
    riesgos_activos_existentes = get_riesgos_activos_evaluacion(ID_EVALUACION)
    ya_agregado = not riesgos_activos_existentes.empty
    
    # Estado de reagregación
    if "reagregando_riesgos" not in st.session_state:
        st.session_state.reagregando_riesgos = False
    
    if ya_agregado and not st.session_state.reagregando_riesgos:
        estado_agregacion = "AGREGADO"
    elif ya_agregado and st.session_state.reagregando_riesgos:
        estado_agregacion = "REAGREGANDO"
    else:
        estado_agregacion = "PENDIENTE"
    
    # ===== VISTA SEGÚN ESTADO =====
    if estado_agregacion == "AGREGADO":
        st.success(f"✅ **Riesgos Agregados**: Se calculó el riesgo consolidado para **{len(riesgos_activos_existentes)} activos**. Los resultados se usan en el mapa de riesgos y comparativas.")
        
        st.warning("""
        ⚠️ **Advertencia sobre Reagregación**
        
        Recalcular la agregación de riesgos afectará:
        - Los promedios de riesgo por activo
        - Los objetivos y límites calculados
        - Las observaciones automáticas generadas
        - Las visualizaciones del mapa radar
        
        **Solo reagregue si cambió los riesgos individuales en el Tab 5.**
        """)
        
        col_re1, col_re2 = st.columns([1, 3])
        with col_re1:
            if st.button("🔄 Habilitar Reagregación", type="secondary", use_container_width=True):
                st.session_state.reagregando_riesgos = True
                st.rerun()
        with col_re2:
            st.caption("💡 Al habilitar la reagregación, podrá recalcular los riesgos consolidados por activo.")
    
    elif estado_agregacion == "REAGREGANDO":
        st.warning("⚠️ **Modo Reagregación Activado**: Los riesgos agregados existentes serán recalculados desde los riesgos individuales (Tab 5).")
        
        col_calc1, col_calc2 = st.columns([1, 3])
        with col_calc1:
            if st.button("🔄 Recalcular Todos los Riesgos", type="primary"):
                # Eliminar agregaciones existentes
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM RIESGO_ACTIVOS WHERE ID_Evaluacion = ?", (ID_EVALUACION,))
                    conn.commit()
                
                count = recalcular_todos_riesgos_activos(ID_EVALUACION)
                st.success(f"✅ {count} activos reagregados correctamente")
                st.session_state.reagregando_riesgos = False
                time.sleep(1)
                st.rerun()
        with col_calc2:
            st.caption("⚠️ Este recálculo agregará los riesgos individuales desde el Tab 5.")
        
        st.markdown("---")
        if st.button("❌ Cancelar Reagregación", use_container_width=True):
            st.session_state.reagregando_riesgos = False
            st.rerun()
    
    else:
        # PENDIENTE
        st.info("📭 No hay riesgos agregados. Primero calcula los riesgos individuales (Tab 5) y luego agrega aquí.")
        
        if st.button("🔄 Agregar Riesgos por Activo", type="primary"):
            count = recalcular_todos_riesgos_activos(ID_EVALUACION)
            st.success(f"✅ {count} activos agregados")
            st.rerun()
    
    riesgos_activos = get_riesgos_activos_evaluacion(ID_EVALUACION)
    
    # Aplicar filtro si no es TODOS
    if filtro_global != "TODOS" and not riesgos_activos.empty:
        riesgos_activos = riesgos_activos[riesgos_activos["ID_Activo"] == filtro_global]
        if not riesgos_activos.empty:
            st.info(f"🎯 Mostrando riesgo del activo filtrado: **{riesgos_activos['Nombre_Activo'].iloc[0]}**")
        else:
            st.warning(f"⚠️ El activo filtrado `{filtro_global}` no tiene riesgo agregado calculado.")
    
    if riesgos_activos.empty:
        st.info("📭 No hay riesgos agregados. Primero calcula los riesgos individuales (Tab 5) y luego recalcula.")
        st.stop()
    
    # Métricas generales
    st.markdown("### 📈 Resumen General")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("📦 Total Activos", len(riesgos_activos))
    with col2:
        urgentes = len(riesgos_activos[riesgos_activos["Riesgo_Actual"] >= LIMITE_RIESGO])
        st.metric("🔴 Sobre Límite", urgentes)
    with col3:
        en_riesgo = len(riesgos_activos[(riesgos_activos["Riesgo_Actual"] >= 2) & (riesgos_activos["Riesgo_Actual"] < LIMITE_RIESGO)])
        st.metric("🟡 En Riesgo", en_riesgo)
    with col4:
        promedio = riesgos_activos["Riesgo_Actual"].mean()
        st.metric("📊 Promedio", f"{promedio:.2f}")
    with col5:
        st.metric("🎯 Límite Org.", LIMITE_RIESGO)
    
    st.markdown("---")
    
    # ===== TABLA PRINCIPAL =====
    st.markdown("### 📋 Tabla de Riesgos por Activo")
    
    # Preparar datos para la tabla
    tabla_riesgos = []
    for idx, row in riesgos_activos.iterrows():
        riesgo_actual = row.get("Riesgo_Actual", 0)
        riesgo_objetivo = row.get("Riesgo_Objetivo", riesgo_actual * FACTOR_REDUCCION)
        limite = LIMITE_RIESGO
        
        # Generar observaciones automáticas
        if riesgo_actual >= 6:
            observacion = "⚠️ ALTO: Tratamiento urgente requerido. Implementar salvaguardas inmediatamente."
        elif riesgo_actual >= limite:
            observacion = "🔴 Sobre límite: Priorizar mitigación. Revisar controles existentes."
        elif riesgo_actual >= riesgo_objetivo:
            observacion = "🟡 Atención: Requiere mejora continua para alcanzar objetivo."
        else:
            observacion = "🟢 Aceptable: Mantener monitoreo y controles actuales."
        
        # Estado de cumplimiento
        if riesgo_actual <= riesgo_objetivo:
            estado = "✅ Cumple objetivo"
        elif riesgo_actual <= limite:
            estado = "⚠️ Dentro de límite"
        else:
            estado = "❌ Excede límite"
        
        tabla_riesgos.append({
            "Nombre": row.get("Nombre_Activo", ""),
            "Riesgo Actual": round(riesgo_actual, 2),
            "Objetivo": round(riesgo_objetivo, 2),
            "Límite": limite,
            "Estado": estado,
            "Observaciones Recomendadas": observacion,
            "N° Amenazas": row.get("Num_Amenazas", 0)
        })
    
    df_tabla = pd.DataFrame(tabla_riesgos)
    
    # Mostrar tabla con estilo
    st.dataframe(
        df_tabla,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Nombre": st.column_config.TextColumn("Nombre Activo", width="medium"),
            "Riesgo Actual": st.column_config.NumberColumn("Riesgo Actual", format="%.2f"),
            "Objetivo": st.column_config.NumberColumn("Objetivo", format="%.2f"),
            "Límite": st.column_config.NumberColumn("Límite", format="%.1f"),
            "Estado": st.column_config.TextColumn("Estado", width="medium"),
            "Observaciones Recomendadas": st.column_config.TextColumn("Observaciones", width="large"),
            "N° Amenazas": st.column_config.NumberColumn("Amenazas", width="small")
        }
    )
    
    # Botón de descarga
    st.download_button(
        label="📥 Descargar Tabla de Riesgos (CSV)",
        data=df_tabla.to_csv(index=False, encoding='utf-8-sig'),
        file_name="riesgos_por_activo.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    
    # ===== GRÁFICO RADAR =====
    st.markdown("### 🎯 Mapa Radar de Riesgos")
    st.caption("Visualización comparativa de riesgo actual vs objetivo vs límite por activo")
    
    if len(riesgos_activos) > 0:
        # Preparar datos para radar
        nombres_activos = riesgos_activos["Nombre_Activo"].tolist()
        riesgos_actuales = riesgos_activos["Riesgo_Actual"].tolist()
        riesgos_objetivo = riesgos_activos["Riesgo_Objetivo"].tolist()
        limites = [LIMITE_RIESGO] * len(nombres_activos)
        
        # Cerrar el polígono
        nombres_activos_cerrado = nombres_activos + [nombres_activos[0]]
        riesgos_actuales_cerrado = riesgos_actuales + [riesgos_actuales[0]]
        riesgos_objetivo_cerrado = riesgos_objetivo + [riesgos_objetivo[0]]
        limites_cerrado = limites + [limites[0]]
        
        fig_radar = go.Figure()
        
        # Línea de límite (fondo rojo)
        fig_radar.add_trace(go.Scatterpolar(
            r=limites_cerrado,
            theta=nombres_activos_cerrado,
            fill='toself',
            fillcolor='rgba(255, 0, 0, 0.1)',
            line=dict(color='red', width=2, dash='dash'),
            name=f'Límite ({LIMITE_RIESGO})'
        ))
        
        # Línea de objetivo (amarillo)
        fig_radar.add_trace(go.Scatterpolar(
            r=riesgos_objetivo_cerrado,
            theta=nombres_activos_cerrado,
            fill='toself',
            fillcolor='rgba(255, 193, 7, 0.2)',
            line=dict(color='gold', width=2),
            name='Objetivo'
        ))
        
        # Línea de riesgo actual (azul)
        fig_radar.add_trace(go.Scatterpolar(
            r=riesgos_actuales_cerrado,
            theta=nombres_activos_cerrado,
            fill='toself',
            fillcolor='rgba(0, 123, 255, 0.3)',
            line=dict(color='blue', width=3),
            name='Riesgo Actual'
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(max(riesgos_actuales), LIMITE_RIESGO) + 1],
                    tickvals=[0, 2, 4, 6, 8],
                    ticktext=["0", "2", "4", "6", "8"]
                )
            ),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            height=500,
            title="Comparativo de Riesgos por Activo"
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)
    
    st.markdown("---")
    
    # ===== GRÁFICO DE BARRAS COMPARATIVO =====
    st.markdown("### 📊 Gráfico Comparativo Riesgo Actual vs Objetivo vs Límite")
    
    fig_bars = go.Figure()
    
    # Ordenar por riesgo actual
    df_sorted = riesgos_activos.sort_values("Riesgo_Actual", ascending=True)
    
    fig_bars.add_trace(go.Bar(
        y=df_sorted["Nombre_Activo"],
        x=df_sorted["Riesgo_Actual"],
        name="Riesgo Actual",
        orientation="h",
        marker_color="crimson"
    ))
    
    fig_bars.add_trace(go.Bar(
        y=df_sorted["Nombre_Activo"],
        x=df_sorted["Riesgo_Objetivo"],
        name="Riesgo Objetivo",
        orientation="h",
        marker_color="gold"
    ))
    
    # Línea de límite
    fig_bars.add_vline(x=LIMITE_RIESGO, line_dash="dash", line_color="red",
                  annotation_text=f"Límite ({LIMITE_RIESGO})")
    
    fig_bars.update_layout(
        barmode="group",
        height=400 + len(df_sorted) * 30,
        xaxis_title="Nivel de Riesgo",
        yaxis_title="Activo"
    )
    
    st.plotly_chart(fig_bars, use_container_width=True)
    
    # ===== INTERPRETACIÓN =====
    st.markdown("---")
    st.subheader("📖 Leyenda de Interpretación")
    col_int1, col_int2 = st.columns(2)
    with col_int1:
        st.markdown("""
        **En el Radar:**
        - 🔵 **Área Azul**: Riesgo actual de cada activo
        - 🟡 **Línea Amarilla**: Meta/Objetivo a alcanzar
        - 🔴 **Línea Roja**: Límite máximo aceptable
        """)
    with col_int2:
        st.markdown("""
        **Estados:**
        - ✅ **Cumple objetivo**: Riesgo ≤ Objetivo
        - ⚠️ **Dentro de límite**: Objetivo < Riesgo ≤ Límite
        - ❌ **Excede límite**: Riesgo > Límite (requiere acción urgente)
        """)


# ==================== TAB 8: SALVAGUARDAS ====================

with tab8:
    st.header("🛡️ Salvaguardas")
    st.markdown("""
    **Propósito:** Recomendaciones de controles/salvaguardas para mitigar riesgos.
    
    **La IA sugiere automáticamente:**
    - Salvaguardas específicas basadas en la amenaza y vulnerabilidad
    - Controles ISO 27002:2022 aplicables
    
    ⚠️ **Importante:** Las salvaguardas se generan una vez. Regenere solo si cambió los riesgos en el Tab 5.
    """)
    
    # Importar función de sugerencia de IA
    from services.ollama_magerit_service import sugerir_salvaguardas_ia, sugerir_salvaguardas_batch
    
    # Obtener filtro global
    filtro_global = st.session_state.get("activo_filtro_global", "TODOS")
    
    # ===== TABLA PRINCIPAL DE RIESGOS CON SALVAGUARDAS SUGERIDAS =====
    st.markdown("### 📋 Tabla de Riesgos con Salvaguardas Sugeridas")
    
    # Obtener todos los riesgos de la evaluación
    riesgos = get_riesgos_evaluacion(ID_EVALUACION)
    activos = get_activos_matriz(ID_EVALUACION)
    
    # Aplicar filtro si no es TODOS
    if filtro_global != "TODOS" and not riesgos.empty:
        riesgos = riesgos[riesgos["ID_Activo"] == filtro_global]
        if not riesgos.empty:
            st.info(f"🎯 Mostrando salvaguardas del activo filtrado: **{riesgos['Nombre_Activo'].iloc[0]}**")
        else:
            st.warning(f"⚠️ El activo filtrado `{filtro_global}` no tiene riesgos calculados.")
    
    if riesgos.empty:
        st.warning("⚠️ No hay riesgos calculados. Ve al Tab 5 (Riesgo) primero para calcular los riesgos.")
    else:
        # Combinar con datos de activos para obtener tipo
        if not activos.empty:
            riesgos = riesgos.merge(
                activos[["ID_Activo", "Tipo_Activo"]], 
                on="ID_Activo", 
                how="left"
            )
        else:
            riesgos["Tipo_Activo"] = ""
        
        # Cargar catálogos para tooltips
        catalogo_amenazas = get_catalogo_amenazas()
        catalogo_controles = get_catalogo_controles()
        
        # ===== DETECCIÓN DE ESTADO =====
        salvaguardas_existentes = get_salvaguardas_evaluacion(ID_EVALUACION)
        ya_generado = not salvaguardas_existentes.empty
        
        # Estado de regeneración
        if "regenerando_salvaguardas" not in st.session_state:
            st.session_state.regenerando_salvaguardas = False
        
        if ya_generado and not st.session_state.regenerando_salvaguardas:
            estado_generacion = "GENERADO"
        elif ya_generado and st.session_state.regenerando_salvaguardas:
            estado_generacion = "REGENERANDO"
        else:
            estado_generacion = "PENDIENTE"
        
        # ===== VISTA SEGÚN ESTADO =====
        if estado_generacion == "GENERADO":
            st.success(f"✅ **Salvaguardas Generadas**: Se crearon **{len(salvaguardas_existentes)} salvaguardas** para mitigar los riesgos identificados.")
            
            # Métricas de salvaguardas
            col_met1, col_met2, col_met3 = st.columns(3)
            with col_met1:
                st.metric("Total Salvaguardas", len(salvaguardas_existentes))
            with col_met2:
                prioridad_alta = sum(1 for _, s in salvaguardas_existentes.iterrows() if "Alta" in str(s.get("Prioridad", "")))
                st.metric("Prioridad Alta", prioridad_alta, delta="🔴" if prioridad_alta > 0 else None)
            with col_met3:
                implementadas = sum(1 for _, s in salvaguardas_existentes.iterrows() if s.get("Estado", "") == "Implementada")
                st.metric("Implementadas", implementadas)
            
            st.markdown("---")
            
            st.warning("""
            ⚠️ **Advertencia sobre Regeneración**
            
            Regenerar las salvaguardas afectará:
            - Las recomendaciones específicas por riesgo
            - Los controles ISO 27002 asignados
            - Las priorizaciones establecidas
            - El plan de tratamiento de riesgos
            
            **Solo regenere si cambió significativamente los riesgos en el Tab 5.**
            """)
            
            col_re1, col_re2 = st.columns([1, 3])
            with col_re1:
                if st.button("🔄 Habilitar Regeneración", type="secondary", use_container_width=True):
                    st.session_state.regenerando_salvaguardas = True
                    st.rerun()
            with col_re2:
                st.caption("💡 Al habilitar la regeneración, la IA volverá a analizar los riesgos y sugerirá nuevas salvaguardas.")
            
            # Mostrar tabla de salvaguardas existentes
            st.markdown("---")
            st.markdown("### 📋 Salvaguardas Actuales")
            st.dataframe(salvaguardas_existentes, use_container_width=True, hide_index=True)
        
        else:  # REGENERANDO o PENDIENTE
            if estado_generacion == "REGENERANDO":
                st.warning("⚠️ **Modo Regeneración Activado**: Las salvaguardas existentes serán eliminadas y la IA las generará nuevamente desde cero.")
            
            # Botón para generar/regenerar salvaguardas con IA
            col_btn1, col_btn2 = st.columns([1, 3])
            with col_btn1:
                texto_boton = "🤖 Regenerar Salvaguardas con IA" if estado_generacion == "REGENERANDO" else "🤖 Generar Salvaguardas con IA"
                generar_ia = st.button(texto_boton, type="primary")
            with col_btn2:
                if estado_generacion == "REGENERANDO":
                    st.caption("⚠️ Esto eliminará las salvaguardas existentes y las regenerará desde los riesgos actuales.")
                else:
                    st.caption("La IA analizará cada riesgo y sugerirá salvaguardas y controles ISO 27002")
            
            # Botón cancelar si está regenerando
            if estado_generacion == "REGENERANDO" and not generar_ia:
                st.markdown("---")
                if st.button("❌ Cancelar Regeneración", use_container_width=True):
                    st.session_state.regenerando_salvaguardas = False
                    st.rerun()
            
            # Session state para guardar resultados
            if "salvaguardas_generadas" not in st.session_state:
                st.session_state.salvaguardas_generadas = None
            
            if generar_ia:
                # Si es regeneración, eliminar salvaguardas existentes
                if estado_generacion == "REGENERANDO":
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM SALVAGUARDAS WHERE ID_Evaluacion = ?", (ID_EVALUACION,))
                        conn.commit()
                with st.spinner("🔄 Generando salvaguardas con IA... (puede tomar unos segundos)"):
                    try:
                        # Generar salvaguardas en batch
                        riesgos_con_salvaguardas = sugerir_salvaguardas_batch(riesgos)
                        st.session_state.salvaguardas_generadas = riesgos_con_salvaguardas
                        st.success("✅ Salvaguardas generadas correctamente")
                    except Exception as e:
                        st.error(f"Error al generar salvaguardas: {e}")
                        # Fallback: generar heurísticamente
                        from services.ollama_magerit_service import generar_salvaguarda_heuristica, sugerir_control_heuristico, get_catalogo_controles
                        catalogo = get_catalogo_controles()
                        salvaguardas = []
                        controles = []
                        for _, row in riesgos.iterrows():
                            zona = "ALTO" if row.get("Riesgo", 0) >= 6 else "MEDIO" if row.get("Riesgo", 0) >= 4 else "BAJO"
                            salvaguardas.append(generar_salvaguarda_heuristica(
                                row.get("Amenaza", ""), 
                                row.get("Vulnerabilidad", ""), 
                                zona
                            ))
                            controles.append(sugerir_control_heuristico(row.get("Amenaza", ""), catalogo))
                        riesgos["Salvaguarda_Sugerida"] = salvaguardas
                        riesgos["Control_ISO"] = controles
                        riesgos["Generado_IA"] = "🔧"
                        st.session_state.salvaguardas_generadas = riesgos
            
            # Usar datos guardados o generar heurísticamente
            if st.session_state.salvaguardas_generadas is not None:
                df_display = st.session_state.salvaguardas_generadas
            else:
                # Generar heurísticamente como fallback inicial
                from services.ollama_magerit_service import generar_salvaguarda_heuristica, sugerir_control_heuristico, get_catalogo_controles
                catalogo = get_catalogo_controles()
                salvaguardas = []
                controles = []
                for _, row in riesgos.iterrows():
                    zona = "ALTO" if row.get("Riesgo", 0) >= 6 else "MEDIO" if row.get("Riesgo", 0) >= 4 else "BAJO"
                    salvaguardas.append(generar_salvaguarda_heuristica(
                        row.get("Amenaza", ""), 
                        row.get("Vulnerabilidad", ""), 
                        zona
                    ))
                    controles.append(sugerir_control_heuristico(row.get("Amenaza", ""), catalogo))
                riesgos["Salvaguarda_Sugerida"] = salvaguardas
                riesgos["Control_ISO"] = controles
                riesgos["Generado_IA"] = "🔧"
                df_display = riesgos
            
            # ===== CONSTRUIR DATAFRAME PARA MOSTRAR =====
            df_display_salv = []
            for idx, row in df_display.iterrows():
                riesgo_val = row.get("Riesgo", 0)
                if riesgo_val >= 6:
                    prioridad = "🔴 Alta"
                elif riesgo_val >= 4:
                    prioridad = "🟡 Media"
                elif riesgo_val >= 2:
                    prioridad = "🟢 Baja"
                else:
                    prioridad = "⚪ Baja"
                
                # Obtener código de vulnerabilidad del catálogo (si existe)
                cod_vuln = row.get("Cod_Vulnerabilidad", "")
                if not cod_vuln or cod_vuln == "":
                    cod_vuln = f"V{idx+1:03d}"
                
                # Extraer código de control ISO
                control_iso_full = row.get("Control_ISO", "")
                control_codigo = control_iso_full.split(" - ")[0].strip() if " - " in control_iso_full else control_iso_full.split(" ")[0] if control_iso_full else ""
                
                df_display_salv.append({
                    "Activo": row.get("Nombre_Activo", ""),
                    "Amenaza": f"{row.get('Cod_Amenaza', '')}",
                    "Cod_Vuln": cod_vuln,
                    "Riesgo": f"{riesgo_val:.2f}",
                    "Salvaguarda": str(row.get("Salvaguarda_Sugerida", ""))[:80] + "..." if len(str(row.get("Salvaguarda_Sugerida", ""))) > 80 else str(row.get("Salvaguarda_Sugerida", "")),
                    "Control_ISO": control_codigo,
                    "Prioridad": prioridad,
                    "IA": row.get("Generado_IA", "🔧"),
                    "_vuln_full": str(row.get("Vulnerabilidad", "")),
                    "_control_full": control_iso_full,
                    "_amenaza_full": row.get("Amenaza", "")
                })
            
            df_salvaguardas = pd.DataFrame(df_display_salv)
            
            # Cargar catálogo de amenazas para tooltips
            catalogo_amenazas_tab8 = get_catalogo_amenazas()
            
            # Mostrar tabla
            st.dataframe(
                df_salvaguardas[["Activo", "Amenaza", "Cod_Vuln", "Riesgo", "Salvaguarda", "Control_ISO", "Prioridad", "IA"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Activo": st.column_config.TextColumn("Activo", width="medium"),
                    "Amenaza": st.column_config.TextColumn("Cod_Amenaza", width="small", help="Código de amenaza MAGERIT"),
                    "Cod_Vuln": st.column_config.TextColumn("Cod_Vuln", width="small", help="Código de vulnerabilidad"),
                    "Riesgo": st.column_config.TextColumn("Riesgo", width="small"),
                    "Salvaguarda": st.column_config.TextColumn("Salvaguarda Sugerida", width="large"),
                    "Control_ISO": st.column_config.TextColumn("Control ISO", width="small", help="Control ISO 27002:2022"),
                    "Prioridad": st.column_config.TextColumn("Prioridad", width="small"),
                    "IA": st.column_config.TextColumn("IA", width="small")
                }
            )
            
            st.caption("✅ = Generado por IA | 🔧 = Generado heurísticamente")
            
            # Tabla de referencia expandible
            with st.expander("📋 Ver Detalles Completos de Códigos"):
                st.markdown("**Códigos de Vulnerabilidad:**")
                for row_data in df_display_salv:
                    st.markdown(f"- **{row_data['Cod_Vuln']}**: {row_data['_vuln_full']}")
                
                st.markdown("---")
                st.markdown("**Códigos de Amenazas:**")
                amenazas_unicas = {}
                for row_data in df_display_salv:
                    cod = row_data['Amenaza']
                    if cod and cod not in amenazas_unicas:
                        amenazas_unicas[cod] = row_data['_amenaza_full']
                        if catalogo_amenazas_tab8.get(cod):
                            info = catalogo_amenazas_tab8[cod]
                            desc_completa = f"{info.get('amenaza', row_data['_amenaza_full'])} - {info.get('descripcion', '')}"
                            amenazas_unicas[cod] = desc_completa
                for cod, desc in amenazas_unicas.items():
                    st.markdown(f"- **{cod}**: {desc}")
                
                st.markdown("---")
                st.markdown("**Códigos de Controles ISO 27002:**")
                controles_unicos = {}
                for row_data in df_display_salv:
                    cod = row_data['Control_ISO']
                    if cod and cod not in controles_unicos:
                        controles_unicos[cod] = row_data['_control_full']
                for cod, desc in controles_unicos.items():
                    st.markdown(f"- **{cod}**: {desc}")
            
            # Preparar DataFrame para descarga
            df_download_salv = df_display.copy()
            df_download_salv = df_download_salv[[
                "Nombre_Activo", "Cod_Amenaza", "Amenaza", "Vulnerabilidad", 
                "Riesgo", "Salvaguarda_Sugerida", "Control_ISO"
            ]]
            df_download_salv.columns = [
                "Activo", "Codigo_Amenaza", "Amenaza", "Vulnerabilidad",
                "Riesgo", "Salvaguarda", "Control ISO"
            ]
            
            # Botón para guardar en base de datos
            st.markdown("---")
            st.markdown("### 💾 Guardar Salvaguardas en Base de Datos")
            st.info("💡 Las salvaguardas deben guardarse en la base de datos para poder usarlas en el Tab 10 (Comparativa)")
            
            col_save_btn, col_save_info = st.columns([1, 3])
            with col_save_btn:
                if st.button("💾 Guardar en Base de Datos", type="primary", key="btn_guardar_salvaguardas_db"):
                    with st.spinner("Guardando salvaguardas..."):
                        guardadas = 0
                        for _, row in df_display.iterrows():
                            try:
                                agregar_salvaguarda(
                                    id_evaluacion=ID_EVALUACION,
                                    id_activo=row["ID_Activo"],
                                    nombre_activo=row.get("Nombre_Activo", ""),
                                    salvaguarda=row.get("Salvaguarda_Sugerida", ""),
                                    riesgo_id=str(row.get("ID_Riesgo", "")),
                                    vulnerabilidad=row.get("Vulnerabilidad", ""),
                                    amenaza=row.get("Amenaza", ""),
                                    prioridad="Alta" if row.get("Riesgo", 0) >= 6 else "Media" if row.get("Riesgo", 0) >= 4 else "Baja",
                                    responsable="",
                                    fecha_limite=""
                                )
                                guardadas += 1
                            except Exception as e:
                                st.error(f"Error guardando salvaguarda: {e}")
                        
                        if guardadas > 0:
                            st.success(f"✅ Se guardaron {guardadas} salvaguardas en la base de datos")
                            st.balloons()
                        else:
                            st.warning("⚠️ No se pudo guardar ninguna salvaguarda")
            
            with col_save_info:
                salvaguardas_bd = get_salvaguardas_evaluacion(ID_EVALUACION)
                total_en_bd = len(salvaguardas_bd)
                st.caption(f"📊 Actualmente hay **{total_en_bd} salvaguardas** guardadas en la base de datos para esta evaluación")
            
            # Botón de descarga
            st.markdown("---")
            st.download_button(
                label="📥 Descargar Tabla de Salvaguardas (CSV)",
                data=df_download_salv.to_csv(index=False, encoding='utf-8-sig'),
                file_name="salvaguardas_sugeridas.csv",
                mime="text/csv"
            )


# ==================== TAB 9: NIVEL DE MADUREZ ====================

with tab9:
    st.header("🎯 Nivel de Madurez de Gestión de Riesgos")
    st.markdown("""
    **Propósito:** Evaluar el nivel de madurez de la gestión de riesgos de TI basado en la completitud de la evaluación.
    
    **Niveles de Madurez:**
    - **Nivel 1 - Inicial (0-19%)**: Evaluación mínima, sin análisis completo
    - **Nivel 2 - Básico (20-39%)**: Evaluación parcial, análisis básico de riesgos
    - **Nivel 3 - Definido (40-59%)**: Evaluación completa, riesgos identificados y documentados
    - **Nivel 4 - Gestionado (60-79%)**: Evaluación detallada con salvaguardas definidas
    - **Nivel 5 - Optimizado (80-100%)**: Evaluación exhaustiva con análisis completo y controles recomendados
    
    **Este es el nivel de madurez ACTUAL (inherente) - SIN considerar salvaguardas implementadas.**
    
    **La puntuación se basa en:**
    - 60% → Distribución de riesgos (% en zona BAJA vs ALTA)
    - 40% → Severidad del riesgo máximo identificado
    
    ⚠️ *Para ver el nivel de madurez CON los controles aplicados, ve al Tab 10 (Comparativa).*
    """)
    
    # Botón para calcular
    if st.button("🔄 Calcular Nivel de Madurez Actual", type="primary", use_container_width=True):
        with st.spinner("Calculando nivel de madurez ACTUAL (sin controles aplicados)..."):
            resultado = calcular_madurez_evaluacion(ID_EVALUACION, considerar_salvaguardas=False)
            if resultado:
                guardar_madurez(resultado)
                st.success("✅ Nivel de madurez calculado y guardado")
                st.rerun()
            else:
                st.error("❌ Error: No hay datos suficientes. Debes tener al menos 1 activo registrado.")
    
    st.markdown("---")
    
    # Obtener madurez guardada
    madurez = get_madurez_evaluacion(ID_EVALUACION)
    
    if madurez:
        # ===== INDICADOR PRINCIPAL =====
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            nivel = madurez.get("Nivel_Madurez", 1)
            nombre = madurez.get("Nombre_Nivel", "Inicial")
            puntuacion = madurez.get("Puntuacion_Total", 0)
            
            # Colores por nivel
            colores_nivel = {
                1: "#ff4444",
                2: "#ff8800",
                3: "#ffdd00",
                4: "#00aa00",
                5: "#0066ff"
            }
            color = colores_nivel.get(nivel, "#666")
            
            # Gráfico Gauge visual de madurez
            fig_gauge_tab9 = go.Figure()
            
            fig_gauge_tab9.add_trace(go.Indicator(
                mode="gauge+number",
                value=puntuacion,
                number={'suffix': '', 'font': {'size': 48}},
                title={'text': f"Madurez: {nombre}", 'font': {'size': 20}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1},
                    'bar': {'color': color, 'thickness': 0.3},
                    'bgcolor': 'white',
                    'borderwidth': 2,
                    'bordercolor': 'gray',
                    'steps': [
                        {'range': [0, 20], 'color': '#ff4444'},    # Nivel 1 - Rojo
                        {'range': [20, 40], 'color': '#ff8800'},   # Nivel 2 - Naranja
                        {'range': [40, 60], 'color': '#ffdd00'},   # Nivel 3 - Amarillo
                        {'range': [60, 80], 'color': '#00aa00'},   # Nivel 4 - Verde
                        {'range': [80, 100], 'color': '#0066ff'}   # Nivel 5 - Azul
                    ],
                    'threshold': {
                        'line': {'color': 'red', 'width': 4},
                        'thickness': 0.75,
                        'value': puntuacion
                    }
                }
            ))
            
            fig_gauge_tab9.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=50, b=20)
            )
            
            st.plotly_chart(fig_gauge_tab9, use_container_width=True)
            
            # Texto informativo del nivel
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem;">
                <h2 style="color: {color}; margin: 0;">NIVEL {nivel} - {nombre}</h2>
                <p style="font-size: 1.2rem; color: #666; margin-top: 0.5rem;">
                    <strong>{puntuacion:.1f}/100</strong> puntos
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ===== COMPONENTES DE LA PUNTUACIÓN =====
        st.subheader("📊 Componentes de la Puntuación")
        
        col1, col2, col3 = st.columns(3)
        
        # Valores reales mapeados a los componentes (nueva fórmula)
        # Obtener datos adicionales directamente de la base de datos para más precisión
        
        # Obtener estadísticas de riesgos directamente
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Riesgo FROM RIESGO_AMENAZA WHERE ID_Evaluacion = ?", [ID_EVALUACION])
            riesgos_rows = cursor.fetchall()
            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN Estado LIKE '%Implementada%' THEN 1 ELSE 0 END) FROM SALVAGUARDAS WHERE ID_Evaluacion = ?", [ID_EVALUACION])
            salv_row = cursor.fetchone()
        
        total_riesgos = len(riesgos_rows)
        riesgos_altos = sum(1 for r in riesgos_rows if (r[0] or 0) >= 6)
        riesgos_medios = sum(1 for r in riesgos_rows if 4 <= (r[0] or 0) < 6)
        riesgos_bajos = sum(1 for r in riesgos_rows if (r[0] or 0) < 4)
        riesgo_maximo = max((r[0] or 0) for r in riesgos_rows) if riesgos_rows else 0
        riesgo_promedio = sum((r[0] or 0) for r in riesgos_rows) / total_riesgos if total_riesgos > 0 else 0
        
        total_salvaguardas = salv_row[0] if salv_row else 0
        salvaguardas_impl = salv_row[1] if salv_row else 0
        salvaguardas_pendientes = total_salvaguardas - salvaguardas_impl
        
        # Tab 9: Solo 2 componentes (sin salvaguardas - madurez inherente)
        # Componente 1: Distribución de riesgos (60%)
        if riesgos_altos > 0 and total_riesgos > 0:
            proporcion_altos = riesgos_altos / total_riesgos
            factor_penalizacion = max(0, 1 - (proporcion_altos * 4))
            pct_riesgos_controlados = (riesgos_bajos / total_riesgos * 100) * factor_penalizacion
        else:
            pct_riesgos_controlados = (riesgos_bajos / total_riesgos * 100) if total_riesgos > 0 else 0
        
        # Componente 2: Severidad del riesgo (40%)
        riesgo_efectivo = riesgo_maximo * 0.8 + riesgo_promedio * 0.2
        pct_riesgo_bajo = max(0, (10 - riesgo_efectivo) / 10 * 100)
        
        with col1:
            st.metric(
                "📊 Distribución de Riesgos",
                f"{pct_riesgos_controlados:.1f}%",
                f"peso: 60%"
            )
            st.progress(min(pct_riesgos_controlados / 100, 1.0))
            st.caption(f"% de riesgos en zona BAJA. Riesgos ALTOS: {riesgos_altos}")
        
        with col2:
            st.metric(
                "⚠️ Severidad del Riesgo",
                f"{pct_riesgo_bajo:.1f}%",
                f"peso: 40%"
            )
            st.progress(min(pct_riesgo_bajo / 100, 1.0))
            st.caption("Menor riesgo máximo = mayor porcentaje")
        
        with col3:
            # Información adicional sobre salvaguardas (pero NO cuentan en la puntuación)
            st.metric(
                "🛡️ Salvaguardas",
                f"{salvaguardas_impl} implementadas",
                f"de {salvaguardas_pendientes + salvaguardas_impl} totales"
            )
            st.info("⚠️ Las salvaguardas se consideran en Tab 10 (Comparativa)")
        
        st.markdown("---")
        
        # ===== GRÁFICO DE BARRAS HORIZONTALES =====
        st.subheader("📈 Análisis de Componentes (Madurez Inherente)")
        
        # Crear gráfico de barras horizontales para los 2 componentes
        col_chart1, col_chart2 = st.columns([2, 1])
        
        with col_chart1:
            # Gráfico de barras horizontales con contribución a la puntuación
            fig_bars = go.Figure()
            
            componentes = ['Distribución de Riesgos (60%)', 'Severidad del Riesgo (40%)']
            valores_raw = [pct_riesgos_controlados, pct_riesgo_bajo]
            contribuciones = [pct_riesgos_controlados * 0.60, pct_riesgo_bajo * 0.40]
            colores = ['#3498db', '#2ecc71']
            
            # Barras de valor bruto
            fig_bars.add_trace(go.Bar(
                y=componentes,
                x=valores_raw,
                orientation='h',
                name='Valor (%)',
                marker_color=colores,
                text=[f'{v:.1f}%' for v in valores_raw],
                textposition='inside',
                textfont=dict(color='white', size=14)
            ))
            
            fig_bars.update_layout(
                title='Puntuación por Componente',
                xaxis_title='Porcentaje (%)',
                xaxis=dict(range=[0, 100]),
                height=250,
                showlegend=False,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            st.plotly_chart(fig_bars, use_container_width=True)
        
        with col_chart2:
            # Gráfico de contribución (dona)
            fig_dona = go.Figure(data=[go.Pie(
                values=contribuciones,
                labels=['Distribución<br>Riesgos', 'Severidad<br>Riesgo'],
                hole=0.6,
                marker_colors=colores,
                textinfo='value',
                texttemplate='%{value:.1f}',
                hovertemplate='%{label}<br>Contribución: %{value:.1f} puntos<extra></extra>'
            )])
            
            fig_dona.update_layout(
                title='Contribución a Puntuación',
                annotations=[dict(text=f'{puntuacion:.1f}', x=0.5, y=0.5, font_size=24, showarrow=False)],
                height=250,
                showlegend=True,
                legend=dict(orientation='h', yanchor='bottom', y=-0.3),
                margin=dict(l=10, r=10, t=40, b=40)
            )
            
            st.plotly_chart(fig_dona, use_container_width=True)
        
        # Resumen de distribución de riesgos
        st.markdown("##### 📊 Distribución Actual de Riesgos:")
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        with col_r1:
            st.metric("🔴 Riesgos ALTOS", riesgos_altos, help="Riesgo >= 6")
        with col_r2:
            st.metric("🟡 Riesgos MEDIOS", riesgos_medios, help="Riesgo 4-5.99")
        with col_r3:
            st.metric("🟢 Riesgos BAJOS", riesgos_bajos, help="Riesgo < 4")
        with col_r4:
            st.metric("📊 Riesgo Máximo", f"{riesgo_maximo:.1f}", help="Mayor valor de riesgo")
        
        st.markdown("---")
        
        # ===== INTERPRETACIÓN DEL NIVEL =====
        st.subheader("📋 Interpretación del Nivel de Madurez")
        
        interpretaciones = {
            1: {
                "emoji": "🔴",
                "titulo": "Nivel 1 - Inicial",
                "descripcion": "La gestión de riesgos de TI está en etapa inicial. Los riesgos identificados son mayormente ALTOS y no hay suficientes controles definidos.",
                "recomendaciones": [
                    "**Priorizar activos críticos:** Identificar los 10 activos más críticos para el negocio y enfocar la evaluación en ellos primero",
                    "**Reducir riesgos ALTOS:** Para cada riesgo >= 6, definir al menos 2 salvaguardas específicas que reduzcan probabilidad o impacto",
                    "**Implementar controles básicos:** Aplicar controles de seguridad esenciales como backups, control de acceso y actualizaciones de software",
                    "**Documentar amenazas:** Usar el análisis con IA para identificar vulnerabilidades y amenazas específicas de cada activo",
                    "**Capacitar al personal:** Realizar capacitación básica de seguridad informática para todo el personal de TI"
                ]
            },
            2: {
                "emoji": "🟠",
                "titulo": "Nivel 2 - Básico",
                "descripcion": "Existe un análisis básico de riesgos. Se han identificado riesgos pero aún hay varios en zona ALTA que requieren atención.",
                "recomendaciones": [
                    "**Tratar riesgos ALTOS restantes:** Implementar salvaguardas para cada riesgo >= 6 identificado en la evaluación",
                    "**Mejorar valoración DIC:** Revisar y ajustar la valoración de Disponibilidad, Integridad y Confidencialidad de cada activo",
                    "**Implementar controles técnicos:** Configurar firewalls, antivirus, IDS/IPS y monitoreo de logs en sistemas críticos",
                    "**Establecer políticas:** Crear políticas formales de seguridad de la información y gestión de incidentes",
                    "**Realizar análisis de impacto:** Documentar el impacto al negocio (BIA) de los activos más críticos"
                ]
            },
            3: {
                "emoji": "🟡",
                "titulo": "Nivel 3 - Definido",
                "descripcion": "La evaluación está completa con riesgos identificados y documentados. La mayoría están en zona BAJA o MEDIA.",
                "recomendaciones": [
                    "**Implementar salvaguardas pendientes:** Cambiar estado de salvaguardas 'Planificada' a 'Implementada' tras ejecutarlas",
                    "**Monitorear riesgos MEDIOS:** Establecer controles adicionales para que riesgos de 4-5.99 bajen a zona BAJA",
                    "**Automatizar controles:** Implementar herramientas de automatización para respaldos, parches y monitoreo",
                    "**Realizar pruebas de seguridad:** Ejecutar escaneos de vulnerabilidades y pruebas de penetración periódicas",
                    "**Documentar procedimientos:** Crear procedimientos operativos estándar (SOPs) para respuesta a incidentes"
                ]
            },
            4: {
                "emoji": "🟢",
                "titulo": "Nivel 4 - Gestionado",
                "descripcion": "Evaluación detallada con salvaguardas bien definidas. La gestión de riesgos es proactiva y estructurada.",
                "recomendaciones": [
                    "**Optimizar controles existentes:** Revisar la eficacia de los controles implementados y mejorar los que no funcionen",
                    "**Implementar métricas KRI:** Establecer Indicadores Clave de Riesgo para monitoreo continuo",
                    "**Realizar reevaluaciones:** Programar reevaluaciones trimestrales para detectar nuevos riesgos",
                    "**Integrar con gestión de cambios:** Vincular evaluación de riesgos con cada cambio en infraestructura TI",
                    "**Preparar para certificación:** Alinear controles con ISO 27001 o SOC 2 para futura certificación"
                ]
            },
            5: {
                "emoji": "🔵",
                "titulo": "Nivel 5 - Optimizado",
                "descripcion": "Excelencia en gestión de riesgos de TI. Análisis exhaustivo con controles completos y riesgos en niveles mínimos.",
                "recomendaciones": [
                    "**Mantener excelencia:** Continuar con reevaluaciones periódicas para mantener el nivel alcanzado",
                    "**Innovar en seguridad:** Explorar tecnologías emergentes como Zero Trust, SASE y automatización de seguridad",
                    "**Compartir conocimiento:** Documentar lecciones aprendidas y mejores prácticas para otras áreas",
                    "**Buscar certificaciones:** Obtener certificaciones ISO 27001, SOC 2 Type II o similares",
                    "**Implementar threat intelligence:** Integrar fuentes de inteligencia de amenazas para detección proactiva"
                ]
            }
        }
        
        info_nivel = interpretaciones.get(nivel, interpretaciones[1])
        
        st.markdown(f"### {info_nivel['emoji']} {info_nivel['titulo']}")
        st.info(info_nivel['descripcion'])
        
        st.markdown("#### 🎯 Recomendaciones para Mejorar:")
        for i, rec in enumerate(info_nivel['recomendaciones'], 1):
            st.markdown(f"{i}. {rec}")
        
        st.markdown("---")
        
        # ===== DETALLES TÉCNICOS =====
        with st.expander("🔍 Ver Detalles Técnicos del Cálculo"):
            st.markdown("### Fórmula de Cálculo (Nueva)")
            
            st.code(f"""
MADUREZ INHERENTE (Tab 9) - Sin Controles Aplicados
====================================================

Puntuación Total = 
    (Distribución Riesgos × 0.60) + 
    (Severidad Riesgo × 0.40)

Donde:
- Distribución de Riesgos (60%):
  % de riesgos en zona BAJA (< 4)
  Riesgos ALTOS penalizan severamente
  
  Total Riesgos: {total_riesgos}
  Riesgos ALTOS (>=6): {riesgos_altos}
  Riesgos MEDIOS (4-5.99): {riesgos_medios}
  Riesgos BAJOS (<4): {riesgos_bajos}
  
  Porcentaje = {pct_riesgos_controlados:.1f}%
  Contribución = {pct_riesgos_controlados * 0.60:.2f} puntos

- Severidad del Riesgo (40%):
  Inverso del riesgo máximo identificado
  Riesgo Máximo: {riesgo_maximo:.1f}
  Riesgo Promedio: {riesgo_promedio:.2f}
  
  Porcentaje = {pct_riesgo_bajo:.1f}%
  Contribución = {pct_riesgo_bajo * 0.40:.2f} puntos

TOTAL = {puntuacion:.1f} puntos → Nivel {nivel} ({nombre})

⚠️ Este es el estado ACTUAL sin considerar salvaguardas.
   Para ver el nivel CON controles aplicados, ve al Tab 10.
            """)
            
            st.markdown("### Umbrales de Niveles")
            umbrales_data = [
                {"Nivel": 1, "Nombre": "Inicial", "Rango": "0-19 puntos", "Estado": "Riesgos críticos sin tratar"},
                {"Nivel": 2, "Nombre": "Básico", "Rango": "20-39 puntos", "Estado": "Algunos riesgos altos"},
                {"Nivel": 3, "Nombre": "Definido", "Rango": "40-59 puntos", "Estado": "Mayoría en zona baja"},
                {"Nivel": 4, "Nombre": "Gestionado", "Rango": "60-79 puntos", "Estado": "Pocos riesgos altos"},
                {"Nivel": 5, "Nombre": "Optimizado", "Rango": "80-100 puntos", "Estado": "Sin riesgos críticos"},
            ]
            st.dataframe(pd.DataFrame(umbrales_data), use_container_width=True, hide_index=True)
    else:
        st.info("📭 No hay datos de madurez. Haz clic en 'Calcular Nivel de Madurez Actual' para generar el análisis.")
    
    # ===== HISTORIAL DE EVALUACIONES =====
    st.markdown("---")
    st.subheader("📜 Historial de Evaluaciones")
    st.caption("Consulta los datos de evaluaciones anteriores realizadas en el sistema")
    
    # Obtener todas las evaluaciones
    todas_evaluaciones = get_evaluaciones()
    
    if not todas_evaluaciones.empty:
        # Selector de evaluación para consultar
        opciones_hist = ["Selecciona una evaluación..."] + todas_evaluaciones["Nombre"].tolist()
        ids_hist = [""] + todas_evaluaciones["ID_Evaluacion"].tolist()
        
        eval_seleccionada_idx = st.selectbox(
            "📋 Selecciona una evaluación para ver su historial:",
            range(len(opciones_hist)),
            format_func=lambda i: opciones_hist[i],
            key="historial_eval_selector"
        )
        
        if eval_seleccionada_idx > 0:
            eval_id_hist = ids_hist[eval_seleccionada_idx]
            eval_nombre_hist = opciones_hist[eval_seleccionada_idx]
            
            st.markdown(f"### 📊 Datos de: **{eval_nombre_hist}**")
            
            # Obtener datos de la evaluación seleccionada
            with get_connection() as conn:
                # Información básica de la evaluación
                eval_info = pd.read_sql_query(
                    "SELECT * FROM EVALUACIONES WHERE ID_Evaluacion = ?",
                    conn, params=[eval_id_hist]
                )
                
                # Activos
                activos_hist = pd.read_sql_query(
                    "SELECT * FROM INVENTARIO_ACTIVOS WHERE ID_Evaluacion = ?",
                    conn, params=[eval_id_hist]
                )
                
                # Valoraciones
                valoraciones_hist = pd.read_sql_query(
                    "SELECT * FROM IDENTIFICACION_VALORACION WHERE ID_Evaluacion = ?",
                    conn, params=[eval_id_hist]
                )
                
                # Riesgos
                riesgos_hist = pd.read_sql_query(
                    "SELECT * FROM RIESGO_AMENAZA WHERE ID_Evaluacion = ?",
                    conn, params=[eval_id_hist]
                )
                
                # Salvaguardas
                salvaguardas_hist = pd.read_sql_query(
                    "SELECT * FROM SALVAGUARDAS WHERE ID_Evaluacion = ?",
                    conn, params=[eval_id_hist]
                )
                
                # Madurez
                madurez_hist = pd.read_sql_query(
                    "SELECT * FROM RESULTADOS_MADUREZ WHERE ID_Evaluacion = ?",
                    conn, params=[eval_id_hist]
                )
            
            # Métricas principales
            col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns(5)
            
            with col_h1:
                st.metric("📦 Activos", len(activos_hist))
            
            with col_h2:
                st.metric("⚖️ Valoraciones", len(valoraciones_hist))
            
            with col_h3:
                st.metric("⚡ Riesgos", len(riesgos_hist))
            
            with col_h4:
                st.metric("🛡️ Salvaguardas", len(salvaguardas_hist))
            
            with col_h5:
                if not madurez_hist.empty:
                    nivel_hist = madurez_hist["Nivel_Madurez"].iloc[0]
                    nombre_nivel_hist = madurez_hist["Nombre_Nivel"].iloc[0]
                    st.metric("🎯 Madurez", f"Nivel {nivel_hist}", help=nombre_nivel_hist)
                else:
                    st.metric("🎯 Madurez", "N/A")
            
            st.markdown("---")
            
            # Panel de madurez destacado
            if not madurez_hist.empty:
                row_mad = madurez_hist.iloc[0]
                puntuacion_hist = row_mad.get("Puntuacion_Total", 0)
                nivel_hist = row_mad.get("Nivel_Madurez", 1)
                nombre_nivel_hist = row_mad.get("Nombre_Nivel", "Inicial")
                
                colores_hist = {1: "#ff4444", 2: "#ff8800", 3: "#ffdd00", 4: "#00aa00", 5: "#0066ff"}
                color_hist = colores_hist.get(nivel_hist, "#666")
                
                col_gauge_h, col_info_h = st.columns([1, 1])
                
                with col_gauge_h:
                    # Gauge de madurez del historial
                    fig_gauge_hist = go.Figure()
                    fig_gauge_hist.add_trace(go.Indicator(
                        mode="gauge+number",
                        value=puntuacion_hist,
                        number={'suffix': '', 'font': {'size': 36}},
                        title={'text': f"Madurez: {nombre_nivel_hist}", 'font': {'size': 16}},
                        gauge={
                            'axis': {'range': [0, 100]},
                            'bar': {'color': color_hist, 'thickness': 0.3},
                            'steps': [
                                {'range': [0, 20], 'color': '#ff4444'},
                                {'range': [20, 40], 'color': '#ff8800'},
                                {'range': [40, 60], 'color': '#ffdd00'},
                                {'range': [60, 80], 'color': '#00aa00'},
                                {'range': [80, 100], 'color': '#0066ff'}
                            ]
                        }
                    ))
                    fig_gauge_hist.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
                    st.plotly_chart(fig_gauge_hist, use_container_width=True)
                
                with col_info_h:
                    st.markdown(f"""
                    #### 🏆 Nivel de Madurez: **{nivel_hist} - {nombre_nivel_hist}**
                    
                    **Puntuación:** {puntuacion_hist:.1f}/100 puntos
                    
                    **Componentes:**
                    - Controles Implementados: {row_mad.get('Pct_Controles_Implementados', 0):.1f}%
                    - Controles Medidos: {row_mad.get('Pct_Controles_Medidos', 0):.1f}%
                    - Riesgos Mitigados: {row_mad.get('Pct_Riesgos_Mitigados', 0):.1f}%
                    
                    **Fecha de cálculo:** {row_mad.get('Fecha_Calculo', 'N/A')}
                    """)
            
            # Tabs para ver detalles
            tab_hist_act, tab_hist_riesg, tab_hist_salv, tab_hist_comp = st.tabs([
                "📦 Activos", "⚡ Riesgos", "🛡️ Salvaguardas", "📋 Resumen Completo"
            ])
            
            with tab_hist_act:
                if not activos_hist.empty:
                    cols_mostrar_act = ["Nombre_Activo", "Tipo", "Ubicacion", "Responsable", "Descripcion"]
                    cols_disponibles = [c for c in cols_mostrar_act if c in activos_hist.columns]
                    st.dataframe(activos_hist[cols_disponibles], use_container_width=True, hide_index=True)
                else:
                    st.info("No hay activos registrados en esta evaluación")
            
            with tab_hist_riesg:
                if not riesgos_hist.empty:
                    # Estadísticas de riesgos
                    col_r1, col_r2, col_r3 = st.columns(3)
                    with col_r1:
                        riesgo_max_hist = riesgos_hist["Riesgo"].max() if "Riesgo" in riesgos_hist.columns else 0
                        st.metric("Riesgo Máximo", f"{riesgo_max_hist:.2f}")
                    with col_r2:
                        riesgo_prom_hist = riesgos_hist["Riesgo"].mean() if "Riesgo" in riesgos_hist.columns else 0
                        st.metric("Riesgo Promedio", f"{riesgo_prom_hist:.2f}")
                    with col_r3:
                        riesgos_altos_hist = len(riesgos_hist[riesgos_hist["Riesgo"] >= 6]) if "Riesgo" in riesgos_hist.columns else 0
                        st.metric("Riesgos ALTOS", riesgos_altos_hist)
                    
                    cols_mostrar_riesg = ["Nombre_Activo", "Amenaza", "Impacto", "Frecuencia", "Riesgo"]
                    cols_disponibles_r = [c for c in cols_mostrar_riesg if c in riesgos_hist.columns]
                    st.dataframe(riesgos_hist[cols_disponibles_r], use_container_width=True, hide_index=True)
                else:
                    st.info("No hay riesgos calculados en esta evaluación")
            
            with tab_hist_salv:
                if not salvaguardas_hist.empty:
                    # Estadísticas de salvaguardas
                    total_salv = len(salvaguardas_hist)
                    impl_salv = len(salvaguardas_hist[salvaguardas_hist["Estado"].str.contains("Implementada", case=False, na=False)]) if "Estado" in salvaguardas_hist.columns else 0
                    
                    col_s1, col_s2, col_s3 = st.columns(3)
                    with col_s1:
                        st.metric("Total Salvaguardas", total_salv)
                    with col_s2:
                        st.metric("Implementadas", impl_salv)
                    with col_s3:
                        pct_impl = (impl_salv / total_salv * 100) if total_salv > 0 else 0
                        st.metric("% Implementación", f"{pct_impl:.1f}%")
                    
                    cols_mostrar_salv = ["Nombre_Activo", "Salvaguarda", "Prioridad", "Estado"]
                    cols_disponibles_s = [c for c in cols_mostrar_salv if c in salvaguardas_hist.columns]
                    st.dataframe(salvaguardas_hist[cols_disponibles_s], use_container_width=True, hide_index=True)
                else:
                    st.info("No hay salvaguardas registradas en esta evaluación")
            
            with tab_hist_comp:
                st.markdown("#### 📋 Resumen Ejecutivo de la Evaluación")
                
                # Información de la evaluación
                if not eval_info.empty:
                    row_eval = eval_info.iloc[0]
                    st.markdown(f"""
                    **Nombre:** {row_eval.get('Nombre', 'N/A')}  
                    **Descripción:** {row_eval.get('Descripcion', 'N/A')}  
                    **Fecha de creación:** {row_eval.get('Fecha_Creacion', 'N/A')}  
                    """)
                
                # Tabla resumen
                resumen_data = {
                    "Métrica": ["Total Activos", "Total Valoraciones", "Total Riesgos", "Riesgo Promedio", 
                               "Riesgo Máximo", "Total Salvaguardas", "Salvaguardas Implementadas", 
                               "Nivel de Madurez", "Puntuación Madurez"],
                    "Valor": [
                        len(activos_hist),
                        len(valoraciones_hist),
                        len(riesgos_hist),
                        f"{riesgos_hist['Riesgo'].mean():.2f}" if not riesgos_hist.empty and 'Riesgo' in riesgos_hist.columns else "N/A",
                        f"{riesgos_hist['Riesgo'].max():.2f}" if not riesgos_hist.empty and 'Riesgo' in riesgos_hist.columns else "N/A",
                        len(salvaguardas_hist),
                        len(salvaguardas_hist[salvaguardas_hist["Estado"].str.contains("Implementada", case=False, na=False)]) if not salvaguardas_hist.empty and "Estado" in salvaguardas_hist.columns else 0,
                        f"Nivel {madurez_hist['Nivel_Madurez'].iloc[0]} - {madurez_hist['Nombre_Nivel'].iloc[0]}" if not madurez_hist.empty else "N/A",
                        f"{madurez_hist['Puntuacion_Total'].iloc[0]:.1f}%" if not madurez_hist.empty else "N/A"
                    ]
                }
                st.dataframe(pd.DataFrame(resumen_data), use_container_width=True, hide_index=True)
                
                # Botón para exportar
                if st.button("📥 Exportar Resumen de esta Evaluación", key="export_hist"):
                    df_export = pd.DataFrame(resumen_data)
                    st.download_button(
                        label="Descargar CSV",
                        data=df_export.to_csv(index=False, encoding='utf-8-sig'),
                        file_name=f"resumen_{eval_nombre_hist.replace(' ', '_')}.csv",
                        mime="text/csv",
                        key="download_hist_csv"
                    )
    else:
        st.info("No hay evaluaciones registradas en el sistema.")
    
    # ===== HISTORIAL DE REEVALUACIONES =====
    st.markdown("---")
    st.subheader("📈 Historial de Reevaluaciones")
    st.caption("Consulta todas las reevaluaciones realizadas con sus cambios de madurez y riesgo")
    
    # Obtener historial de reevaluaciones
    historial_reeval = get_historial_reevaluaciones()
    
    if not historial_reeval.empty:
        # Selector para filtrar por evaluación
        evals_con_reeval = historial_reeval["ID_Evaluacion"].unique().tolist()
        opciones_filtro = ["Todas las evaluaciones"] + evals_con_reeval
        
        filtro_reeval = st.selectbox(
            "🔍 Filtrar por evaluación:",
            opciones_filtro,
            key="filtro_historial_reeval"
        )
        
        # Aplicar filtro
        if filtro_reeval != "Todas las evaluaciones":
            historial_mostrar = historial_reeval[historial_reeval["ID_Evaluacion"] == filtro_reeval]
        else:
            historial_mostrar = historial_reeval
        
        # Métricas del historial
        col_hr1, col_hr2, col_hr3, col_hr4 = st.columns(4)
        with col_hr1:
            st.metric("📊 Total Reevaluaciones", len(historial_mostrar))
        with col_hr2:
            mejoras = len(historial_mostrar[historial_mostrar["Nivel_Nuevo"] > historial_mostrar["Nivel_Anterior"]])
            st.metric("✅ Mejoras de Nivel", mejoras)
        with col_hr3:
            reduccion_prom = (historial_mostrar["Riesgo_Anterior"] - historial_mostrar["Riesgo_Nuevo"]).mean()
            st.metric("📉 Reducción Riesgo Prom.", f"{reduccion_prom:.2f}" if not pd.isna(reduccion_prom) else "N/A")
        with col_hr4:
            salvaguardas_total = historial_mostrar["Salvaguardas_Implementadas"].sum()
            st.metric("🛡️ Salvaguardas Totales", int(salvaguardas_total))
        
        st.markdown("---")
        
        # Tabla de historial
        cols_mostrar_reeval = [
            "Fecha_Reevaluacion", "ID_Evaluacion", 
            "Riesgo_Anterior", "Riesgo_Nuevo",
            "Madurez_Anterior", "Madurez_Nueva",
            "Nivel_Anterior", "Nivel_Nuevo", "Nombre_Nivel",
            "Salvaguardas_Implementadas", "Total_Salvaguardas"
        ]
        cols_disponibles_reeval = [c for c in cols_mostrar_reeval if c in historial_mostrar.columns]
        
        # Renombrar columnas para mejor visualización
        df_hist_display = historial_mostrar[cols_disponibles_reeval].copy()
        df_hist_display.columns = [
            "Fecha", "Evaluación", 
            "Riesgo Ant.", "Riesgo Nuevo",
            "Madurez Ant.", "Madurez Nueva",
            "Nivel Ant.", "Nivel Nuevo", "Nombre Nivel",
            "Salvag. Impl.", "Total Salvag."
        ][:len(cols_disponibles_reeval)]
        
        st.dataframe(df_hist_display, use_container_width=True, hide_index=True)
        
        # Gráfico de evolución
        if len(historial_mostrar) >= 2:
            st.markdown("#### 📊 Evolución de Madurez en Reevaluaciones")
            
            fig_evol = go.Figure()
            
            # Ordenar por fecha
            hist_ordenado = historial_mostrar.sort_values("Fecha_Reevaluacion")
            
            fig_evol.add_trace(go.Scatter(
                x=hist_ordenado["Fecha_Reevaluacion"],
                y=hist_ordenado["Madurez_Nueva"],
                mode='lines+markers',
                name='Madurez',
                line=dict(color='#3498db', width=3),
                marker=dict(size=10)
            ))
            
            fig_evol.add_trace(go.Scatter(
                x=hist_ordenado["Fecha_Reevaluacion"],
                y=hist_ordenado["Riesgo_Nuevo"] * 10,  # Escalar para comparar
                mode='lines+markers',
                name='Riesgo (x10)',
                line=dict(color='#e74c3c', width=3, dash='dash'),
                marker=dict(size=10)
            ))
            
            fig_evol.update_layout(
                xaxis_title="Fecha de Reevaluación",
                yaxis_title="Puntuación",
                height=350,
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            
            st.plotly_chart(fig_evol, use_container_width=True)
        
        # Expander para ver detalles de cada reevaluación
        with st.expander("🔍 Ver detalles de reevaluaciones individuales"):
            for idx, row in historial_mostrar.iterrows():
                nivel_ant = row.get("Nivel_Anterior", 0)
                nivel_nuevo = row.get("Nivel_Nuevo", 0)
                delta_nivel = nivel_nuevo - nivel_ant
                
                emoji_cambio = "✅" if delta_nivel > 0 else "⚠️" if delta_nivel < 0 else "➡️"
                
                st.markdown(f"""
                **{row.get('Fecha_Reevaluacion', 'N/A')}** - {row.get('ID_Evaluacion', 'N/A')}
                - {emoji_cambio} Nivel: {nivel_ant} → {nivel_nuevo} ({row.get('Nombre_Nivel', '')})
                - Madurez: {row.get('Madurez_Anterior', 0):.1f}% → {row.get('Madurez_Nueva', 0):.1f}%
                - Riesgo: {row.get('Riesgo_Anterior', 0):.2f} → {row.get('Riesgo_Nuevo', 0):.2f}
                - Salvaguardas: {row.get('Salvaguardas_Implementadas', 0)}/{row.get('Total_Salvaguardas', 0)}
                - *{row.get('Observaciones', '')}*
                """)
                st.markdown("---")
        
        # Botón para exportar historial
        if st.button("📥 Exportar Historial de Reevaluaciones", key="export_hist_reeval"):
            csv_hist = historial_mostrar.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="Descargar CSV",
                data=csv_hist,
                file_name="historial_reevaluaciones.csv",
                mime="text/csv",
                key="download_hist_reeval_csv"
            )
    else:
        st.info("📭 No hay reevaluaciones registradas. Las reevaluaciones se guardan automáticamente cuando completas el proceso en el Tab 10.")


# ==================== TAB 10: REEVALUACIÓN Y COMPARATIVA ====================

with tab10:
    st.header("🔄 Reevaluación y Comparativa")
    st.markdown("""
    **Propósito:** Realizar una reevaluación periódica para comparar el estado actual vs anterior.
    
    **Este proceso incluye:**
    1. ✅ Verificar requisitos de la evaluación inicial
    2. 📦 Revisar cambios en el inventario de activos
    3. 🛡️ Evaluar implementación de salvaguardas
    4. 📊 Recalcular riesgos y madurez
    5. 📈 Comparar resultados
    """)
    
    # ===== OBTENER FILTRO GLOBAL =====
    filtro_global = st.session_state.get("activo_filtro_global", "TODOS")
    
    # ===== VERIFICAR REQUISITOS =====
    activos_eval = get_activos_matriz(ID_EVALUACION)
    riesgos_eval = get_riesgos_evaluacion(ID_EVALUACION)
    madurez_eval = get_madurez_evaluacion(ID_EVALUACION)
    salvaguardas_eval = get_salvaguardas_evaluacion(ID_EVALUACION)
    
    # Aplicar filtro si no es TODOS
    if filtro_global != "TODOS":
        if not activos_eval.empty:
            activos_eval = activos_eval[activos_eval["ID_Activo"] == filtro_global]
        if not riesgos_eval.empty:
            riesgos_eval = riesgos_eval[riesgos_eval["ID_Activo"] == filtro_global]
        if not salvaguardas_eval.empty:
            salvaguardas_eval = salvaguardas_eval[salvaguardas_eval["ID_Activo"] == filtro_global]
        
        # Mostrar info del filtro
        if not activos_eval.empty:
            nombre_activo = activos_eval["Nombre_Activo"].iloc[0] if not activos_eval.empty else filtro_global
            st.info(f"🎯 **Filtro activo:** Analizando solo el activo **{nombre_activo}**")
    
    # Estado de la evaluación inicial
    tiene_activos = not activos_eval.empty
    tiene_riesgos = not riesgos_eval.empty
    tiene_madurez = madurez_eval is not None
    tiene_salvaguardas = not salvaguardas_eval.empty
    
    evaluacion_completa = tiene_activos and tiene_riesgos and tiene_madurez
    
    # Panel de estado
    st.markdown("### 📋 Estado de la Evaluación Inicial")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if tiene_activos:
            st.success(f"✅ Activos: {len(activos_eval)}")
        else:
            st.error("❌ Sin activos")
    with col2:
        if tiene_riesgos:
            st.success(f"✅ Riesgos: {len(riesgos_eval)}")
        else:
            st.error("❌ Sin riesgos")
    with col3:
        if tiene_madurez:
            nivel = madurez_eval.get("Nivel_Madurez", 0)
            st.success(f"✅ Madurez: Nivel {nivel}")
        else:
            st.error("❌ Sin madurez")
    with col4:
        if tiene_salvaguardas:
            st.success(f"✅ Salvaguardas: {len(salvaguardas_eval)}")
        else:
            st.warning("⚠️ Sin salvaguardas")
    
    st.markdown("---")
    
    # ===== BLOQUEO SI NO HAY EVALUACIÓN COMPLETA =====
    if not evaluacion_completa:
        st.error("🔒 **Reevaluación bloqueada**: Debes completar la evaluación inicial primero.")
        st.warning("""
        **Pasos requeridos antes de la reevaluación:**
        1. **Tab 1**: Cargar inventario de activos
        2. **Tab 2**: Completar cuestionario DIC para cada activo
        3. **Tab 3**: Verificar valoración D/I/C
        4. **Tab 4**: Identificar vulnerabilidades/amenazas con IA
        5. **Tab 5**: Calcular riesgos
        6. **Tab 8**: Generar salvaguardas recomendadas (opcional pero recomendado)
        7. **Tab 9**: Calcular nivel de madurez
        """)
        
        # Mostrar progreso
        st.markdown("### 📊 Progreso de la Evaluación")
        pasos_completados = sum([tiene_activos, tiene_riesgos, tiene_madurez])
        progreso = pasos_completados / 3
        st.progress(progreso)
        st.caption(f"{pasos_completados} de 3 pasos obligatorios completados")
        
    else:
        # ===== REEVALUACIÓN HABILITADA =====
        st.success("✅ Evaluación inicial completa. Puedes iniciar la reevaluación.")
        
        # Inicializar estado de reevaluación
        if "reevaluacion_fase" not in st.session_state:
            st.session_state["reevaluacion_fase"] = 0
        
        # Detectar cambio de filtro para reinicializar datos
        filtro_reeval_actual = st.session_state.get("reevaluacion_filtro_aplicado", "TODOS")
        filtro_cambio = filtro_reeval_actual != filtro_global
        
        if "reevaluacion_datos" not in st.session_state or filtro_cambio:
            st.session_state["reevaluacion_datos"] = {
                "riesgo_anterior": riesgos_eval["Riesgo"].mean() if not riesgos_eval.empty else 0,
                "madurez_anterior": madurez_eval.get("Puntuacion_Total", 0) if madurez_eval else 0,
                "nivel_anterior": madurez_eval.get("Nivel_Madurez", 1) if madurez_eval else 1,
                "activos_anteriores": len(activos_eval),
                "cambios_activos": {"agregados": [], "eliminados": [], "editados": []},
                "salvaguardas_implementadas": []
            }
            st.session_state["reevaluacion_filtro_aplicado"] = filtro_global
            if filtro_cambio and st.session_state.get("reevaluacion_fase", 0) > 0:
                st.session_state["reevaluacion_fase"] = 0  # Reiniciar fase si cambió filtro
        
        fase = st.session_state["reevaluacion_fase"]
        
        # Botón para reiniciar reevaluación
        if fase > 0:
            if st.button("🔄 Reiniciar Reevaluación", key="btn_reiniciar_reeval"):
                st.session_state["reevaluacion_fase"] = 0
                st.session_state["reevaluacion_datos"] = {
                    "riesgo_anterior": riesgos_eval["Riesgo"].mean() if not riesgos_eval.empty else 0,
                    "madurez_anterior": madurez_eval.get("Puntuacion_Total", 0) if madurez_eval else 0,
                    "nivel_anterior": madurez_eval.get("Nivel_Madurez", 1) if madurez_eval else 1,
                    "activos_anteriores": len(activos_eval),
                    "cambios_activos": {"agregados": [], "eliminados": [], "editados": []},
                    "salvaguardas_implementadas": []
                }
                st.session_state["reevaluacion_filtro_aplicado"] = filtro_global
                st.session_state["salvaguardas_impl_reeval"] = {}  # Limpiar selecciones
                st.rerun()
        
        st.markdown("---")
        
        # ===== FASE 0: INICIO DE REEVALUACIÓN =====
        if fase == 0:
            st.markdown("### 🚀 Iniciar Proceso de Reevaluación")
            
            st.info("""
            **La reevaluación te permitirá:**
            - Registrar cambios en el inventario de activos (nuevos, eliminados, editados)
            - Evaluar qué salvaguardas fueron implementadas
            - Recalcular el nivel de riesgo y madurez
            - Comparar el estado actual vs el anterior
            """)
            
            # Mostrar métricas actuales
            st.markdown("#### 📊 Estado Actual (Evaluación Inicial)")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🎯 Riesgo Promedio", f"{st.session_state['reevaluacion_datos']['riesgo_anterior']:.2f}")
            with col2:
                st.metric("📊 Madurez", f"{st.session_state['reevaluacion_datos']['madurez_anterior']:.0f}%")
            with col3:
                st.metric("📦 Activos", st.session_state['reevaluacion_datos']['activos_anteriores'])
            
            if st.button("▶️ Iniciar Reevaluación", type="primary", use_container_width=True):
                st.session_state["reevaluacion_fase"] = 1
                st.rerun()
        
        # ===== FASE 1: CAMBIOS EN ACTIVOS =====
        elif fase == 1:
            st.markdown("### 📦 Fase 1: Cambios en el Inventario de Activos")
            
            st.markdown("#### ¿Hubo cambios en el inventario de activos desde la última evaluación?")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                nuevos_activos = st.radio(
                    "¿Se agregaron nuevos activos?",
                    ["No", "Sí"],
                    key="nuevos_activos_radio",
                    horizontal=True
                )
            
            with col2:
                activos_eliminados = st.radio(
                    "¿Se eliminaron activos?",
                    ["No", "Sí"],
                    key="eliminados_activos_radio",
                    horizontal=True
                )
            
            with col3:
                activos_editados = st.radio(
                    "¿Se modificaron activos existentes?",
                    ["No", "Sí"],
                    key="editados_activos_radio",
                    horizontal=True
                )
            
            # Si hay cambios, mostrar instrucciones
            if nuevos_activos == "Sí" or activos_eliminados == "Sí" or activos_editados == "Sí":
                st.markdown("---")
                st.warning("⚠️ **Debes realizar los cambios antes de continuar:**")
                
                if nuevos_activos == "Sí":
                    st.info("📥 **Agregar activos:** Ve al **Tab 1 (Activos)** para agregar nuevos activos al inventario.")
                
                if activos_eliminados == "Sí":
                    st.info("🗑️ **Eliminar activos:** Ve al **Tab 1 (Activos)** para eliminar activos que ya no aplican.")
                
                if activos_editados == "Sí":
                    st.info("✏️ **Editar activos:** Ve al **Tab 1 (Activos)** para modificar la información de activos existentes.")
                
                st.markdown("---")
                st.caption("Una vez realizados los cambios en el Tab 1, regresa aquí y continúa.")
            
            col_back, col_next = st.columns(2)
            with col_back:
                if st.button("⬅️ Volver", use_container_width=True):
                    st.session_state["reevaluacion_fase"] = 0
                    st.rerun()
            with col_next:
                if st.button("Continuar ➡️", type="primary", use_container_width=True):
                    # Guardar cambios reportados
                    st.session_state["reevaluacion_datos"]["hubo_cambios_activos"] = (
                        nuevos_activos == "Sí" or activos_eliminados == "Sí" or activos_editados == "Sí"
                    )
                    st.session_state["reevaluacion_fase"] = 2
                    st.rerun()
        
        # ===== FASE 2: SALVAGUARDAS IMPLEMENTADAS =====
        elif fase == 2:
            st.markdown("### 🛡️ Fase 2: Salvaguardas Implementadas")
            
            if salvaguardas_eval.empty:
                st.warning("⚠️ No hay salvaguardas recomendadas registradas.")
                st.info("Puedes ir al **Tab 8** para generar salvaguardas, o continuar sin esta información.")
                
                if st.button("Continuar sin salvaguardas ➡️", type="primary"):
                    st.session_state["reevaluacion_fase"] = 3
                    st.rerun()
            else:
                st.markdown("#### Marca las salvaguardas que fueron **implementadas** desde la última evaluación:")
                
                # Inicializar estado de implementación
                if "salvaguardas_impl_reeval" not in st.session_state:
                    st.session_state["salvaguardas_impl_reeval"] = {}
                
                # Agrupar por activo
                activos_unicos = salvaguardas_eval["Nombre_Activo"].unique()
                
                for activo in activos_unicos:
                    with st.expander(f"📦 {activo}", expanded=True):
                        salvs_activo = salvaguardas_eval[salvaguardas_eval["Nombre_Activo"] == activo]
                        
                        for idx, row in salvs_activo.iterrows():
                            salvaguarda = row.get("Salvaguarda", "Sin descripción")
                            prioridad = row.get("Prioridad", "Media")
                            amenaza = row.get("Amenaza", "")
                            
                            emoji = "🔴" if prioridad == "Alta" else "🟡" if prioridad == "Media" else "🟢"
                            
                            key = f"salv_impl_{idx}"
                            
                            col_check, col_info = st.columns([0.08, 0.92])
                            with col_check:
                                implementada = st.checkbox(
                                    "",
                                    value=st.session_state["salvaguardas_impl_reeval"].get(key, False),
                                    key=f"check_{key}",
                                    label_visibility="collapsed"
                                )
                                st.session_state["salvaguardas_impl_reeval"][key] = implementada
                            
                            with col_info:
                                texto = f"{emoji} **{prioridad}**: {salvaguarda[:70]}..." if len(salvaguarda) > 70 else f"{emoji} **{prioridad}**: {salvaguarda}"
                                st.markdown(texto)
                
                # Contador
                total = len(salvaguardas_eval)
                implementadas = sum(1 for v in st.session_state["salvaguardas_impl_reeval"].values() if v)
                st.info(f"📌 **{implementadas} de {total}** salvaguardas marcadas como implementadas")
            
            st.markdown("---")
            col_back, col_next = st.columns(2)
            with col_back:
                if st.button("⬅️ Volver", use_container_width=True, key="back_fase2"):
                    st.session_state["reevaluacion_fase"] = 1
                    st.rerun()
            with col_next:
                if st.button("Calcular Nueva Evaluación ➡️", type="primary", use_container_width=True):
                    st.session_state["reevaluacion_fase"] = 3
                    st.rerun()
        
        # ===== FASE 3: RECÁLCULO Y COMPARATIVA =====
        elif fase == 3:
            st.markdown("### 📊 Fase 3: Resultados de la Reevaluación")
            
            # Calcular nuevos valores
            activos_actuales = get_activos_matriz(ID_EVALUACION)
            riesgos_actuales = get_riesgos_evaluacion(ID_EVALUACION)
            
            # Aplicar filtro global si está activo
            if filtro_global != "TODOS":
                if not activos_actuales.empty:
                    activos_actuales = activos_actuales[activos_actuales["ID_Activo"] == filtro_global]
                if not riesgos_actuales.empty:
                    riesgos_actuales = riesgos_actuales[riesgos_actuales["ID_Activo"] == filtro_global]
            
            # Datos anteriores
            datos_ant = st.session_state["reevaluacion_datos"]
            riesgo_anterior = datos_ant["riesgo_anterior"]
            madurez_anterior = datos_ant["madurez_anterior"]
            nivel_anterior = datos_ant["nivel_anterior"]
            activos_anteriores = datos_ant["activos_anteriores"]
            
            # Calcular impacto de salvaguardas implementadas
            salvaguardas_impl = st.session_state.get("salvaguardas_impl_reeval", {})
            total_salvaguardas = len(salvaguardas_eval) if not salvaguardas_eval.empty else 1
            implementadas = sum(1 for v in salvaguardas_impl.values() if v)
            
            # Factor de reducción de riesgo basado en salvaguardas
            factor_reduccion = min(0.5, (implementadas / total_salvaguardas) * 0.5) if total_salvaguardas > 0 else 0
            
            # Nuevo riesgo
            riesgo_actual = riesgos_actuales["Riesgo"].mean() if not riesgos_actuales.empty else 0
            riesgo_nuevo = riesgo_actual * (1 - factor_reduccion)
            
            # Recalcular madurez CON salvaguardas implementadas
            from services.maturity_service import calcular_madurez_evaluacion
            resultado_madurez_nuevo = calcular_madurez_evaluacion(ID_EVALUACION, considerar_salvaguardas=True)
            
            if resultado_madurez_nuevo:
                madurez_nueva = resultado_madurez_nuevo.puntuacion_total
                nivel_nuevo = resultado_madurez_nuevo.nivel_madurez
                nombre_nivel = resultado_madurez_nuevo.nombre_nivel
            else:
                # Fallback si no se puede calcular
                madurez_nueva = madurez_anterior
                nivel_nuevo = nivel_anterior
                nombre_nivel = "Inicial" if nivel_anterior == 1 else "Básico" if nivel_anterior == 2 else "Definido" if nivel_anterior == 3 else "Gestionado" if nivel_anterior == 4 else "Optimizado"
            
            # ===== MÉTRICAS COMPARATIVAS =====
            st.markdown("#### 📈 Comparativa: Antes vs Después")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                delta_riesgo = riesgo_nuevo - riesgo_anterior
                st.metric(
                    "🎯 Riesgo Promedio",
                    f"{riesgo_nuevo:.2f}",
                    delta=f"{delta_riesgo:.2f}",
                    delta_color="inverse"
                )
            
            with col2:
                delta_madurez = madurez_nueva - madurez_anterior
                st.metric(
                    "📊 Madurez",
                    f"{madurez_nueva:.0f}%",
                    delta=f"+{delta_madurez:.0f}%" if delta_madurez > 0 else f"{delta_madurez:.0f}%"
                )
            
            with col3:
                delta_nivel = nivel_nuevo - nivel_anterior
                st.metric(
                    "🏆 Nivel Madurez",
                    f"Nivel {nivel_nuevo}",
                    delta=f"+{delta_nivel}" if delta_nivel > 0 else str(delta_nivel) if delta_nivel < 0 else "="
                )
            
            with col4:
                delta_activos = len(activos_actuales) - activos_anteriores
                st.metric(
                    "📦 Activos",
                    len(activos_actuales),
                    delta=f"+{delta_activos}" if delta_activos > 0 else str(delta_activos) if delta_activos < 0 else "="
                )
            
            st.markdown("---")
            
            # ===== GRÁFICOS =====
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                # Gráfico de barras: Antes vs Después
                fig_barras = go.Figure()
                
                categorias = ['Riesgo', 'Madurez (%)']
                valores_antes = [riesgo_anterior, madurez_anterior]
                valores_despues = [riesgo_nuevo, madurez_nueva]
                
                fig_barras.add_trace(go.Bar(
                    name='Antes (Evaluación Inicial)',
                    x=categorias,
                    y=valores_antes,
                    marker_color='#ff6b6b',
                    text=[f"{v:.1f}" for v in valores_antes],
                    textposition='auto'
                ))
                
                fig_barras.add_trace(go.Bar(
                    name='Después (Reevaluación)',
                    x=categorias,
                    y=valores_despues,
                    marker_color='#51cf66',
                    text=[f"{v:.1f}" for v in valores_despues],
                    textposition='auto'
                ))
                
                fig_barras.update_layout(
                    title="📊 Comparativa General",
                    barmode='group',
                    height=400,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                )
                
                st.plotly_chart(fig_barras, use_container_width=True)
            
            with col_g2:
                # Gauge de madurez
                fig_gauge = go.Figure()
                
                fig_gauge.add_trace(go.Indicator(
                    mode="gauge+number+delta",
                    value=madurez_nueva,
                    delta={'reference': madurez_anterior, 'relative': False},
                    title={'text': f"Madurez: {nombre_nivel}"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#3498db"},
                        'steps': [
                            {'range': [0, 30], 'color': "#ff6b6b"},
                            {'range': [30, 50], 'color': "#ffd93d"},
                            {'range': [50, 70], 'color': "#6bcb77"},
                            {'range': [70, 100], 'color': "#4d96ff"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': madurez_anterior
                        }
                    }
                ))
                
                fig_gauge.update_layout(height=400)
                st.plotly_chart(fig_gauge, use_container_width=True)
            
            st.markdown("---")
            
            # ===== TABLA COMPARATIVA DETALLADA =====
            st.markdown("#### 📋 Resumen Comparativo Detallado")
            
            # Crear tabla de comparación
            comparativa_data = [
                {"Métrica": "Riesgo Promedio", "Evaluación Inicial": f"{riesgo_anterior:.2f}", "Reevaluación": f"{riesgo_nuevo:.2f}", "Cambio": f"{delta_riesgo:+.2f}", "Estado": "✅ Mejora" if delta_riesgo < 0 else "⚠️ Empeoró" if delta_riesgo > 0 else "➡️ Sin cambio"},
                {"Métrica": "Puntuación Madurez", "Evaluación Inicial": f"{madurez_anterior:.0f}%", "Reevaluación": f"{madurez_nueva:.0f}%", "Cambio": f"{delta_madurez:+.0f}%", "Estado": "✅ Mejora" if delta_madurez > 0 else "⚠️ Empeoró" if delta_madurez < 0 else "➡️ Sin cambio"},
                {"Métrica": "Nivel de Madurez", "Evaluación Inicial": f"Nivel {nivel_anterior}", "Reevaluación": f"Nivel {nivel_nuevo}", "Cambio": f"{delta_nivel:+d}" if delta_nivel != 0 else "0", "Estado": "✅ Mejora" if delta_nivel > 0 else "⚠️ Empeoró" if delta_nivel < 0 else "➡️ Sin cambio"},
                {"Métrica": "Total Activos", "Evaluación Inicial": str(activos_anteriores), "Reevaluación": str(len(activos_actuales)), "Cambio": f"{delta_activos:+d}" if delta_activos != 0 else "0", "Estado": "ℹ️ Cambio" if delta_activos != 0 else "➡️ Sin cambio"},
                {"Métrica": "Salvaguardas Implementadas", "Evaluación Inicial": "0", "Reevaluación": str(implementadas), "Cambio": f"+{implementadas}", "Estado": "✅ Progreso" if implementadas > 0 else "⚠️ Sin avance"},
            ]
            
            df_comparativa = pd.DataFrame(comparativa_data)
            st.dataframe(df_comparativa, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # ===== GRÁFICO DE EVOLUCIÓN DE RIESGO POR ACTIVO =====
            if not riesgos_actuales.empty:
                st.markdown("#### 🎯 Evolución del Riesgo por Activo")
                
                # Calcular riesgo por activo (antes y después)
                activos_riesgo = riesgos_actuales.groupby("Nombre_Activo")["Riesgo"].max().reset_index()
                activos_riesgo.columns = ["Activo", "Riesgo_Antes"]
                activos_riesgo["Riesgo_Despues"] = activos_riesgo["Riesgo_Antes"] * (1 - factor_reduccion)
                
                # Limitar a 10 activos para legibilidad
                activos_riesgo = activos_riesgo.head(10)
                
                fig_activos = go.Figure()
                
                fig_activos.add_trace(go.Bar(
                    name='Antes',
                    x=activos_riesgo["Activo"],
                    y=activos_riesgo["Riesgo_Antes"],
                    marker_color='#ff6b6b',
                    text=[f"{v:.1f}" for v in activos_riesgo["Riesgo_Antes"]],
                    textposition='auto'
                ))
                
                fig_activos.add_trace(go.Bar(
                    name='Después',
                    x=activos_riesgo["Activo"],
                    y=activos_riesgo["Riesgo_Despues"],
                    marker_color='#51cf66',
                    text=[f"{v:.1f}" for v in activos_riesgo["Riesgo_Despues"]],
                    textposition='auto'
                ))
                
                fig_activos.update_layout(
                    title="Riesgo por Activo: Antes vs Después",
                    barmode='group',
                    height=400,
                    xaxis_tickangle=-45,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                )
                
                st.plotly_chart(fig_activos, use_container_width=True)
            
            st.markdown("---")
            
            # ===== GRÁFICO DE DISTRIBUCIÓN DE RIESGO =====
            col_dist1, col_dist2 = st.columns(2)
            
            with col_dist1:
                # Distribución de niveles de riesgo ANTES
                if not riesgos_actuales.empty:
                    niveles_antes = {"Alto": 0, "Medio": 0, "Bajo": 0, "Nulo": 0}
                    for _, row in riesgos_actuales.iterrows():
                        riesgo = row.get("Riesgo", 0)
                        if riesgo >= 6:
                            niveles_antes["Alto"] += 1
                        elif riesgo >= 4:
                            niveles_antes["Medio"] += 1
                        elif riesgo >= 2:
                            niveles_antes["Bajo"] += 1
                        else:
                            niveles_antes["Nulo"] += 1
                    
                    fig_pie_antes = go.Figure(data=[go.Pie(
                        labels=list(niveles_antes.keys()),
                        values=list(niveles_antes.values()),
                        hole=0.4,
                        marker_colors=['#ff6b6b', '#ffd93d', '#51cf66', '#74c0fc'],
                        title="ANTES"
                    )])
                    fig_pie_antes.update_layout(height=300, showlegend=True)
                    st.plotly_chart(fig_pie_antes, use_container_width=True)
            
            with col_dist2:
                # Distribución de niveles de riesgo DESPUÉS
                if not riesgos_actuales.empty:
                    niveles_despues = {"Alto": 0, "Medio": 0, "Bajo": 0, "Nulo": 0}
                    for _, row in riesgos_actuales.iterrows():
                        riesgo_nuevo_act = row.get("Riesgo", 0) * (1 - factor_reduccion)
                        if riesgo_nuevo_act >= 6:
                            niveles_despues["Alto"] += 1
                        elif riesgo_nuevo_act >= 4:
                            niveles_despues["Medio"] += 1
                        elif riesgo_nuevo_act >= 2:
                            niveles_despues["Bajo"] += 1
                        else:
                            niveles_despues["Nulo"] += 1
                    
                    fig_pie_despues = go.Figure(data=[go.Pie(
                        labels=list(niveles_despues.keys()),
                        values=list(niveles_despues.values()),
                        hole=0.4,
                        marker_colors=['#ff6b6b', '#ffd93d', '#51cf66', '#74c0fc'],
                        title="DESPUÉS"
                    )])
                    fig_pie_despues.update_layout(height=300, showlegend=True)
                    st.plotly_chart(fig_pie_despues, use_container_width=True)
            
            st.markdown("---")
            
            # ===== RESUMEN DE SALVAGUARDAS =====
            st.markdown("#### 🛡️ Salvaguardas Implementadas")
            
            if implementadas > 0 and not salvaguardas_eval.empty:
                detalles = []
                for idx, row in salvaguardas_eval.iterrows():
                    key = f"salv_impl_{idx}"
                    if salvaguardas_impl.get(key, False):
                        detalles.append({
                            "Activo": row.get("Nombre_Activo", ""),
                            "Salvaguarda": row.get("Salvaguarda", "")[:50] + "..." if len(str(row.get("Salvaguarda", ""))) > 50 else row.get("Salvaguarda", ""),
                            "Prioridad": row.get("Prioridad", "Media"),
                            "Estado": "✅ Implementada"
                        })
                
                if detalles:
                    st.dataframe(pd.DataFrame(detalles), use_container_width=True, hide_index=True)
                    
                    # Reducción de riesgo
                    reduccion_pct = factor_reduccion * 100
                    st.success(f"📉 La implementación de {implementadas} salvaguardas redujo el riesgo en aproximadamente **{reduccion_pct:.1f}%**")
            else:
                st.info("No se marcaron salvaguardas como implementadas.")
            
            # ===== CONCLUSIÓN =====
            st.markdown("---")
            st.markdown("#### 📝 Conclusión de la Reevaluación")
            
            if delta_riesgo < 0:
                st.success(f"✅ **Mejora detectada**: El riesgo promedio disminuyó de {riesgo_anterior:.2f} a {riesgo_nuevo:.2f}")
            elif delta_riesgo > 0:
                st.warning(f"⚠️ **Atención**: El riesgo promedio aumentó de {riesgo_anterior:.2f} a {riesgo_nuevo:.2f}")
            else:
                st.info("ℹ️ El nivel de riesgo se mantiene igual.")
            
            if delta_nivel > 0:
                st.success(f"🏆 **¡Nivel de madurez mejorado!** Pasó del Nivel {nivel_anterior} al Nivel {nivel_nuevo} ({nombre_nivel})")
            elif delta_nivel < 0:
                st.warning(f"⚠️ El nivel de madurez disminuyó del Nivel {nivel_anterior} al Nivel {nivel_nuevo}")
            
            # Botón para guardar reevaluación
            st.markdown("---")
            col_save, col_reset = st.columns(2)
            
            with col_save:
                if st.button("💾 Guardar Resultados de Reevaluación", type="primary", use_container_width=True):
                    # Actualizar madurez en la base de datos usando el resultado recalculado
                    try:
                        if resultado_madurez_nuevo:
                            # Usar los valores del nuevo cálculo
                            guardar_madurez(resultado_madurez_nuevo)
                        else:
                            # Fallback: crear resultado manualmente
                            nuevo_resultado = {
                                "ID_Evaluacion": ID_EVALUACION,
                                "Nivel_Madurez": nivel_nuevo,
                                "Nombre_Nivel": nombre_nivel,
                                "Puntuacion_Total": madurez_nueva,
                                "Dominio_Organizacional": 0,
                                "Dominio_Personas": 0,
                                "Dominio_Fisico": 0,
                                "Dominio_Tecnologico": 0,
                                "Controles_Totales": 0,
                                "Controles_Implementados": implementadas,
                                "Porcentaje_Cumplimiento": (implementadas / total_salvaguardas * 100) if total_salvaguardas > 0 else 0,
                                "Observaciones": f"Reevaluación: {implementadas} salvaguardas implementadas. Riesgo anterior: {riesgo_anterior:.2f}, nuevo: {riesgo_nuevo:.2f}"
                            }
                            guardar_madurez(nuevo_resultado)
                        
                        # Actualizar estado de salvaguardas
                        for idx, row in salvaguardas_eval.iterrows():
                            key = f"salv_impl_{idx}"
                            if salvaguardas_impl.get(key, False):
                                actualizar_estado_salvaguarda(row.get("id", 0), "Implementada")
                        
                        # Guardar en historial de reevaluaciones
                        observaciones_reeval = f"Salvaguardas implementadas: {implementadas}/{total_salvaguardas}. "
                        if delta_riesgo < 0:
                            observaciones_reeval += f"Riesgo reducido en {abs(delta_riesgo):.2f}. "
                        if delta_nivel > 0:
                            observaciones_reeval += f"Nivel de madurez mejoró de {nivel_anterior} a {nivel_nuevo}."
                        
                        guardar_reevaluacion(
                            eval_id=ID_EVALUACION,
                            riesgo_anterior=riesgo_anterior,
                            riesgo_nuevo=riesgo_nuevo,
                            madurez_anterior=madurez_anterior,
                            madurez_nueva=madurez_nueva,
                            nivel_anterior=nivel_anterior,
                            nivel_nuevo=nivel_nuevo,
                            nombre_nivel=nombre_nivel,
                            salvaguardas_implementadas=implementadas,
                            total_salvaguardas=total_salvaguardas,
                            factor_reduccion=factor_reduccion,
                            total_activos=len(activos_actuales),
                            total_riesgos=len(riesgos_actuales),
                            observaciones=observaciones_reeval
                        )
                        
                        st.success("✅ Resultados guardados correctamente en el historial")
                        st.balloons()
                        # Forzar recarga para mostrar el nuevo registro
                        st.session_state["mostrar_historial_reeval"] = True
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
            
            with col_reset:
                if st.button("🔄 Nueva Reevaluación", use_container_width=True):
                    st.session_state["reevaluacion_fase"] = 0
                    if "salvaguardas_impl_reeval" in st.session_state:
                        del st.session_state["salvaguardas_impl_reeval"]
                    st.session_state["reevaluacion_datos"] = {
                        "riesgo_anterior": riesgo_nuevo,
                        "madurez_anterior": madurez_nueva,
                        "nivel_anterior": nivel_nuevo,
                        "activos_anteriores": len(activos_actuales),
                        "cambios_activos": {"agregados": [], "eliminados": [], "editados": []},
                        "salvaguardas_implementadas": []
                    }
                    st.rerun()
        
        # ===== SECCIÓN: HISTORIAL DE REEVALUACIONES (Visible siempre) =====
        st.markdown("---")
        st.markdown("### 📜 Historial de Reevaluaciones Guardadas")
        st.caption("Consulta todas las reevaluaciones realizadas para esta evaluación")
        
        # Obtener historial de reevaluaciones de esta evaluación
        historial_reeval_tab10 = get_historial_reevaluaciones(ID_EVALUACION)
        
        if not historial_reeval_tab10.empty:
            st.success(f"📋 Se encontraron **{len(historial_reeval_tab10)}** reevaluaciones guardadas")
            
            # Mostrar tabla resumen
            tabla_historial = []
            for idx, row in historial_reeval_tab10.iterrows():
                fecha = row.get("Fecha_Reevaluacion", "")
                riesgo_ant = row.get("Riesgo_Anterior", 0)
                riesgo_new = row.get("Riesgo_Nuevo", 0)
                madurez_ant = row.get("Madurez_Anterior", 0)
                madurez_new = row.get("Madurez_Nueva", 0)
                nivel_ant = row.get("Nivel_Anterior", 1)
                nivel_new = row.get("Nivel_Nuevo", 1)
                salvs_impl = row.get("Salvaguardas_Implementadas", 0)
                total_salvs = row.get("Total_Salvaguardas", 0)
                
                # Calcular cambios
                delta_riesgo = riesgo_new - riesgo_ant
                delta_madurez = madurez_new - madurez_ant
                
                tabla_historial.append({
                    "📅 Fecha": fecha[:16] if len(str(fecha)) > 16 else fecha,
                    "📉 Riesgo Ant.": f"{riesgo_ant:.2f}",
                    "📈 Riesgo Nuevo": f"{riesgo_new:.2f}",
                    "Δ Riesgo": f"{delta_riesgo:+.2f}" if delta_riesgo != 0 else "0",
                    "🎯 Madurez Ant.": f"{madurez_ant:.0f}%",
                    "🎯 Madurez Nueva": f"{madurez_new:.0f}%",
                    "Δ Madurez": f"{delta_madurez:+.0f}%" if delta_madurez != 0 else "0",
                    "🛡️ Salvaguardas": f"{salvs_impl}/{total_salvs}",
                    "Estado": "✅ Mejora" if delta_riesgo < 0 else "⚠️ Empeoró" if delta_riesgo > 0 else "➡️ Igual"
                })
            
            df_historial_tab10 = pd.DataFrame(tabla_historial)
            st.dataframe(df_historial_tab10, use_container_width=True, hide_index=True)
            
            # Gráfico de evolución
            with st.expander("📊 Ver Gráfico de Evolución", expanded=False):
                if len(historial_reeval_tab10) >= 1:
                    fig_evolucion = go.Figure()
                    
                    # Agregar línea de riesgo
                    fechas = historial_reeval_tab10["Fecha_Reevaluacion"].tolist()
                    riesgos_nuevos = historial_reeval_tab10["Riesgo_Nuevo"].tolist()
                    madurez_nuevas = historial_reeval_tab10["Madurez_Nueva"].tolist()
                    
                    fig_evolucion.add_trace(go.Scatter(
                        x=fechas, y=riesgos_nuevos,
                        mode='lines+markers',
                        name='Riesgo',
                        line=dict(color='#ff6b6b', width=3),
                        marker=dict(size=10)
                    ))
                    
                    fig_evolucion.add_trace(go.Scatter(
                        x=fechas, y=madurez_nuevas,
                        mode='lines+markers',
                        name='Madurez (%)',
                        line=dict(color='#51cf66', width=3),
                        marker=dict(size=10),
                        yaxis='y2'
                    ))
                    
                    fig_evolucion.update_layout(
                        title="Evolución de Riesgo y Madurez en Reevaluaciones",
                        xaxis_title="Fecha de Reevaluación",
                        yaxis=dict(title="Riesgo", side="left", color="#ff6b6b"),
                        yaxis2=dict(title="Madurez (%)", side="right", overlaying="y", color="#51cf66"),
                        height=400,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                    )
                    
                    st.plotly_chart(fig_evolucion, use_container_width=True)
            
            # Botón de descarga
            st.download_button(
                label="📥 Descargar Historial (CSV)",
                data=historial_reeval_tab10.to_csv(index=False, encoding='utf-8-sig'),
                file_name=f"historial_reevaluaciones_{NOMBRE_EVALUACION}.csv",
                mime="text/csv"
            )
        else:
            st.info("📭 Aún no hay reevaluaciones guardadas para esta evaluación. Completa el proceso de reevaluación y guarda los resultados.")


# ==================== FOOTER ====================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <strong>TITA - Matriz de Riesgos</strong><br>
    Sistema de Evaluación de Riesgos basado en metodología MAGERIT v3<br>
    <em>Versión: Matriz de Referencia</em>
</div>
""", unsafe_allow_html=True)
