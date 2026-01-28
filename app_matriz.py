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
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
import io

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
    comparar_madurez
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
    
    # Crear nueva evaluación
    with st.expander("➕ Nueva Evaluación"):
        nombre_eval = st.text_input("Nombre", key="sidebar_eval_nombre")
        desc_eval = st.text_area("Descripción", key="sidebar_eval_desc")
        if st.button("Crear", key="sidebar_crear_eval"):
            if nombre_eval:
                eval_id = crear_evaluacion(nombre_eval, desc_eval)
                st.success(f"✅ Creada: {eval_id}")
                st.rerun()
    
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
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13 = st.tabs([
    "📏 1. Criterios",
    "📦 2. Activos",
    "⚖️ 3. Valoración D/I/C",
    "🔓 4. Vulnerabilidades",
    "⚡ 5. Riesgo",
    "🗺️ 6. Mapa Riesgos",
    "📊 7. Riesgo Activos",
    "🛡️ 8. Salvaguardas",
    "📈 9. Dashboards",
    "🎯 10. Madurez",
    "🔄 11. Comparativa",
    "📑 12. Matriz Excel",
    "📋 13. Resumen Ejecutivo"
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
    cat_tab1, cat_tab2, cat_tab3 = st.tabs([
        "⚠️ Amenazas MAGERIT",
        "🛡️ Controles ISO 27002",
        "🔒 Salvaguardas MAGERIT"
    ])
    
    # ===== AMENAZAS MAGERIT =====
    with cat_tab1:
        st.subheader("⚠️ Catálogo de Amenazas MAGERIT v3")
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
                    "Tipo": tipo_nombre,
                    "Dimensión": info.get("dimension_afectada", "D")
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
    
    # ===== SALVAGUARDAS MAGERIT =====
    with cat_tab3:
        st.subheader("🔒 Catálogo de Salvaguardas MAGERIT v3")
        st.markdown("""
        Las salvaguardas MAGERIT están alineadas con los controles ISO 27002.
        Se organizan en las siguientes categorías:
        """)
        
        # Definir salvaguardas MAGERIT (mapeo a ISO 27002)
        salvaguardas_magerit = {
            "H": {
                "nombre": "Protecciones Generales",
                "descripcion": "Medidas de carácter general que afectan a toda la organización",
                "controles_iso": ["5.1", "5.2", "5.3", "5.4", "5.5"]
            },
            "D": {
                "nombre": "Protección de Datos/Información",
                "descripcion": "Salvaguardas para proteger la información",
                "controles_iso": ["5.10", "5.12", "5.13", "5.14", "8.10", "8.11", "8.12"]
            },
            "K": {
                "nombre": "Gestión de Claves Criptográficas",
                "descripcion": "Protección mediante criptografía",
                "controles_iso": ["8.24"]
            },
            "S": {
                "nombre": "Protección de Servicios",
                "descripcion": "Salvaguardas para servicios de TI",
                "controles_iso": ["8.6", "8.13", "8.14", "8.15", "8.16"]
            },
            "SW": {
                "nombre": "Protección del Software",
                "descripcion": "Salvaguardas para aplicaciones",
                "controles_iso": ["8.25", "8.26", "8.27", "8.28", "8.29", "8.30", "8.31"]
            },
            "HW": {
                "nombre": "Protección del Hardware",
                "descripcion": "Salvaguardas para equipamiento",
                "controles_iso": ["7.8", "7.9", "7.10", "7.11", "7.12", "7.13"]
            },
            "COM": {
                "nombre": "Protección de Comunicaciones",
                "descripcion": "Salvaguardas para redes y comunicaciones",
                "controles_iso": ["8.20", "8.21", "8.22", "8.23"]
            },
            "SI": {
                "nombre": "Protección de Soportes de Información",
                "descripcion": "Salvaguardas para medios de almacenamiento",
                "controles_iso": ["7.10", "7.14", "8.10"]
            },
            "AUX": {
                "nombre": "Elementos Auxiliares",
                "descripcion": "Protección de instalaciones auxiliares",
                "controles_iso": ["7.5", "7.6", "7.7", "7.11", "7.12"]
            },
            "L": {
                "nombre": "Protección de Instalaciones",
                "descripcion": "Seguridad física del entorno",
                "controles_iso": ["7.1", "7.2", "7.3", "7.4"]
            },
            "PS": {
                "nombre": "Gestión del Personal",
                "descripcion": "Salvaguardas relacionadas con el personal",
                "controles_iso": ["6.1", "6.2", "6.3", "6.4", "6.5", "6.6", "6.7", "6.8"]
            },
            "G": {
                "nombre": "Organización",
                "descripcion": "Salvaguardas organizativas",
                "controles_iso": ["5.1", "5.2", "5.3", "5.4"]
            },
            "BC": {
                "nombre": "Continuidad del Negocio",
                "descripcion": "Planes de continuidad y recuperación",
                "controles_iso": ["5.29", "5.30"]
            },
            "E": {
                "nombre": "Relaciones Externas",
                "descripcion": "Gestión de proveedores y terceros",
                "controles_iso": ["5.19", "5.20", "5.21", "5.22", "5.23"]
            },
            "NEW": {
                "nombre": "Adquisición y Desarrollo",
                "descripcion": "Seguridad en adquisición y desarrollo",
                "controles_iso": ["5.8", "8.25", "8.26", "8.27", "8.28", "8.29", "8.30", "8.31", "8.32", "8.33", "8.34"]
            }
        }
        
        # Mostrar como cards
        for codigo, info in salvaguardas_magerit.items():
            with st.expander(f"**[{codigo}]** {info['nombre']}", expanded=False):
                st.markdown(f"**Descripción:** {info['descripcion']}")
                st.markdown("**Controles ISO 27002 relacionados:**")
                
                # Mostrar controles relacionados
                controles_relacionados = info["controles_iso"]
                if catalogo_controles:
                    for ctrl_code in controles_relacionados:
                        ctrl_info = catalogo_controles.get(ctrl_code, {})
                        nombre_ctrl = ctrl_info.get("nombre", "Control no encontrado")
                        st.markdown(f"- `{ctrl_code}`: {nombre_ctrl}")
                else:
                    st.markdown(", ".join([f"`{c}`" for c in controles_relacionados]))
        
        st.markdown("---")
        
        # Tabla resumen
        st.subheader("📋 Resumen de Categorías")
        data_salvaguardas = []
        for codigo, info in salvaguardas_magerit.items():
            data_salvaguardas.append({
                "Código": codigo,
                "Categoría": info["nombre"],
                "Descripción": info["descripcion"],
                "# Controles ISO": len(info["controles_iso"])
            })
        
        df_salvaguardas = pd.DataFrame(data_salvaguardas)
        st.dataframe(df_salvaguardas, use_container_width=True, hide_index=True)


# ==================== TAB 2: ACTIVOS ====================

with tab2:
    st.header("📦 Inventario de Activos")
    st.markdown("""
    **Propósito:** Inventario detallado de activos físicos y virtuales.
    Aquí se registran todos los activos que serán evaluados.
    """)
    
    # Obtener activos de la evaluación
    activos = get_activos_matriz(ID_EVALUACION)
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Activos", len(activos))
    with col2:
        if not activos.empty and "Tipo_Activo" in activos.columns:
            fisicos = len(activos[activos["Tipo_Activo"].str.contains("Físico", case=False, na=False)])
            st.metric("Físicos", fisicos)
    with col3:
        if not activos.empty and "Tipo_Activo" in activos.columns:
            virtuales = len(activos[activos["Tipo_Activo"].str.contains("Virtual", case=False, na=False)])
            st.metric("Virtuales", virtuales)
    with col4:
        valorados = len(activos[activos["Criticidad_Nivel"] != "Pendiente"]) if not activos.empty else 0
        st.metric("Valorados", valorados)
    
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
                app_critica = st.text_input("Aplicación Crítica", key="nuevo_activo_app")
            
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
                        "App_Critica": app_critica if app_critica else "No",
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
    
    # Tabla de activos
    if not activos.empty:
        st.subheader("📋 Lista de Activos")
        
        # Columnas a mostrar (formato matriz)
        columnas_mostrar = [
            "Nombre_Activo", "Tipo_Activo", "Ubicacion", 
            "Area_Responsable", "Finalidad_Uso", "Criticidad_Nivel", "Estado"
        ]
        columnas_existentes = [c for c in columnas_mostrar if c in activos.columns]
        
        # Aplicar estilos por criticidad
        def colorear_criticidad(val):
            if val == "Alta":
                return "background-color: #ff4444; color: white"
            elif val == "Media":
                return "background-color: #ffbb33; color: black"
            elif val == "Baja":
                return "background-color: #00C851; color: white"
            elif val == "Nula":
                return "background-color: #33b5e5; color: white"
            return ""
        
        df_display = activos[columnas_existentes].copy()
        if "Criticidad_Nivel" in df_display.columns:
            styled_df = df_display.style.map(colorear_criticidad, subset=["Criticidad_Nivel"])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Editar/Eliminar activo
        with st.expander("✏️ Editar o Eliminar Activo"):
            activo_sel = st.selectbox(
                "Seleccionar activo",
                activos["ID_Activo"].tolist(),
                format_func=lambda x: activos[activos["ID_Activo"] == x]["Nombre_Activo"].values[0]
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
                            eliminar_activo(activo_sel)
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
    """)
    
    activos = get_activos_matriz(ID_EVALUACION)
    
    if activos.empty:
        st.warning("⚠️ No hay activos. Ve a la pestaña 'Activos' para agregar primero.")
        st.stop()
    
    # Sub-tabs: Cuestionario vs Resumen
    tab_cuestionario, tab_resumen_val = st.tabs(["📝 Cuestionario D/I/C", "📊 Resumen Valoraciones"])
    
    with tab_cuestionario:
        # Selector de activo
        activo_sel = st.selectbox(
            "🎯 Seleccionar Activo para Valorar",
            activos["ID_Activo"].tolist(),
            format_func=lambda x: f"{activos[activos['ID_Activo'] == x]['Nombre_Activo'].values[0]} ({activos[activos['ID_Activo'] == x]['Tipo_Activo'].values[0]})",
            key="valoracion_activo_sel"
        )
        
        if activo_sel:
            activo_info = activos[activos["ID_Activo"] == activo_sel].iloc[0]
            tipo_activo = activo_info['Tipo_Activo']
            valoracion_actual = get_valoracion_activo(ID_EVALUACION, activo_sel)
            respuestas_previas = get_respuestas_previas(ID_EVALUACION, activo_sel)
            
            # Info del activo
            st.markdown("---")
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.markdown(f"**📦 Activo:** {activo_info['Nombre_Activo']}")
            with col_info2:
                st.markdown(f"**🏷️ Tipo:** {tipo_activo}")
            with col_info3:
                st.markdown(f"**📍 Ubicación:** {activo_info['Ubicacion']}")
            
            # Obtener preguntas para este tipo
            preguntas = get_banco_preguntas_tipo(tipo_activo)
            
            if not preguntas:
                st.warning(f"⚠️ No hay cuestionario específico para '{tipo_activo}'. Se usará el cuestionario genérico.")
                # Usar Servidor Físico como genérico
                preguntas = get_banco_preguntas_tipo("Servidor Físico")
            
            # Mostrar cuestionario por dimensión
            st.markdown("---")
            st.markdown("### 📋 Cuestionario de Valoración")
            st.info("💡 Responda las siguientes preguntas para calcular automáticamente los niveles D/I/C del activo.")
            
            respuestas = {}
            
            # Tabs por dimensión (ahora con RTO, RPO y BIA)
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
                    
                    # Valor previo si existe
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
                        key=f"q_{pregunta_id}"
                    )
                    # Extraer valor de la selección
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
                        key=f"q_{pregunta_id}"
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
                        key=f"q_{pregunta_id}"
                    )
                    respuestas[pregunta_id] = int(seleccion.split(")")[0].replace("(", ""))
            
            # ===== RTO (Recovery Time Objective) =====
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
                        key=f"q_{pregunta_id}"
                    )
                    respuestas[pregunta_id] = int(seleccion.split(")")[0].replace("(", ""))
            
            # ===== RPO (Recovery Point Objective) =====
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
                        key=f"q_{pregunta_id}"
                    )
                    respuestas[pregunta_id] = int(seleccion.split(")")[0].replace("(", ""))
            
            # ===== BIA (Business Impact Analysis) =====
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
                        key=f"q_{pregunta_id}"
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
                    rto_color = {"Crítico": "🔴", "Alto": "🟠", "Medio": "🟡", "Bajo": "🟢"}.get(rto_nivel, "⚪")
                    rto_tiempo = resultado_preview.get("RTO_Tiempo", "No definido")
                    st.metric(f"{rto_color} RTO", rto_tiempo, delta=rto_nivel)
                
                with col_rpo:
                    rpo_nivel = resultado_preview.get("RPO_Nivel", "Bajo")
                    rpo_color = {"Crítico": "🔴", "Alto": "🟠", "Medio": "🟡", "Bajo": "🟢"}.get(rpo_nivel, "⚪")
                    rpo_tiempo = resultado_preview.get("RPO_Tiempo", "No definido")
                    st.metric(f"{rpo_color} RPO", rpo_tiempo, delta=rpo_nivel)
                
                with col_bia:
                    bia_nivel = resultado_preview.get("BIA_Nivel", "Bajo")
                    bia_color = {"Crítico": "🔴", "Alto": "🟠", "Medio": "🟡", "Bajo": "🟢"}.get(bia_nivel, "⚪")
                    bia_valor = resultado_preview.get("BIA_Valor", 0)
                    st.metric(f"{bia_color} Impacto BIA", bia_nivel, delta=f"Nivel {bia_valor}")
            
            # Botón guardar
            if st.button("💾 Guardar Valoración", type="primary", use_container_width=True):
                try:
                    resultado = guardar_respuestas_dic(
                        id_evaluacion=ID_EVALUACION,
                        id_activo=activo_sel,
                        tipo_activo=tipo_activo,
                        respuestas=respuestas
                    )
                    st.success(f"""✅ Valoración guardada exitosamente:
                    - **Criticidad D/I/C:** {resultado['Criticidad']} ({resultado['Criticidad_Nivel']})
                    - **RTO:** {resultado.get('RTO_Tiempo', 'N/A')} ({resultado.get('RTO_Nivel', 'N/A')})
                    - **RPO:** {resultado.get('RPO_Tiempo', 'N/A')} ({resultado.get('RPO_Nivel', 'N/A')})
                    - **BIA:** {resultado.get('BIA_Nivel', 'N/A')}
                    """)
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error al guardar: {str(e)}")
            
            # Mostrar valoración actual si existe
            if valoracion_actual:
                with st.expander("📈 Valoración Actual Guardada", expanded=False):
                    st.json({
                        "D": valoracion_actual.get("D"),
                        "Valor_D": valoracion_actual.get("Valor_D"),
                        "I": valoracion_actual.get("I"),
                        "Valor_I": valoracion_actual.get("Valor_I"),
                        "C": valoracion_actual.get("C"),
                        "Valor_C": valoracion_actual.get("Valor_C"),
                        "Criticidad": valoracion_actual.get("Criticidad"),
                        "Criticidad_Nivel": valoracion_actual.get("Criticidad_Nivel"),
                        "RTO_Tiempo": valoracion_actual.get("RTO_Tiempo"),
                        "RTO_Nivel": valoracion_actual.get("RTO_Nivel"),
                        "RPO_Tiempo": valoracion_actual.get("RPO_Tiempo"),
                        "RPO_Nivel": valoracion_actual.get("RPO_Nivel"),
                        "BIA_Nivel": valoracion_actual.get("BIA_Nivel")
                    })
    
    # ===== RESUMEN DE VALORACIONES =====
    with tab_resumen_val:
        st.subheader("📋 Resumen de Valoraciones")
        
        # Estadísticas
        valoraciones = get_valoraciones_evaluacion(ID_EVALUACION)
        total_activos = len(activos)
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
            
            # Columnas a mostrar (incluyendo RTO/RPO/BIA)
            cols = ["Nombre_Activo", "D", "Valor_D", "I", "Valor_I", "C", "Valor_C", 
                    "Criticidad", "Criticidad_Nivel", "RTO_Tiempo", "RTO_Nivel", 
                    "RPO_Tiempo", "RPO_Nivel", "BIA_Nivel"]
            cols_existentes = [c for c in cols if c in valoraciones.columns]
            
            def colorear_criticidad(val):
                if val == "Alta": return "background-color: #ff4444; color: white"
                elif val == "Media": return "background-color: #ffbb33; color: black"
                elif val == "Baja": return "background-color: #00C851; color: white"
                return ""
            
            styled_df = valoraciones[cols_existentes].style.map(
                colorear_criticidad, subset=["Criticidad_Nivel"]
            )
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Gráfico de distribución
            st.markdown("---")
            st.subheader("📊 Distribución de Criticidad")
            
            if "Criticidad_Nivel" in valoraciones.columns:
                dist = valoraciones["Criticidad_Nivel"].value_counts().reset_index()
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
    """)
    
    # Importar función de análisis con IA
    from services.ollama_magerit_service import analizar_amenazas_por_criticidad, verificar_ollama_disponible
    
    activos = get_activos_matriz(ID_EVALUACION)
    
    if activos.empty:
        st.warning("⚠️ No hay activos. Ve a la pestaña 'Activos' para agregar primero.")
        st.stop()
    
    # Verificar estado de Ollama
    ollama_disponible, modelos = verificar_ollama_disponible()
    if ollama_disponible:
        st.success(f"🟢 IA Local (Ollama) conectada. Modelos: {', '.join(modelos[:3])}")
    else:
        st.warning("⚠️ Ollama no disponible. Se usará análisis heurístico basado en reglas MAGERIT.")
    
    # ===== SELECCIÓN DE ACTIVO =====
    st.subheader("📦 Selección de Activo")
    
    activo_sel = st.selectbox(
        "🎯 Seleccionar Activo para Analizar",
        activos["ID_Activo"].tolist(),
        format_func=lambda x: f"{activos[activos['ID_Activo'] == x]['Nombre_Activo'].values[0]} ({activos[activos['ID_Activo'] == x]['Tipo_Activo'].values[0]})",
        key="vuln_activo_sel"
    )
    
    if activo_sel:
        activo_info = activos[activos["ID_Activo"] == activo_sel].iloc[0]
        valoracion = get_valoracion_activo(ID_EVALUACION, activo_sel)
        
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
        
        col_id, col_tipo, col_ubic = st.columns(3)
        with col_id:
            st.markdown(f"**ID Activo:** `{activo_sel}`")
        with col_tipo:
            st.markdown(f"**Tipo:** {activo_info['Tipo_Activo']}")
        with col_ubic:
            st.markdown(f"**Ubicación:** {activo_info.get('Ubicacion', 'N/A')}")
        
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
            if st.button("🔍 Analizar con IA", type="primary", key="btn_analizar_ia"):
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
                        st.success(f"✅ {mensaje}")
                    else:
                        st.error(f"❌ Error: {mensaje}")
        
        with col_btn2:
            st.caption("La IA usa el catálogo MAGERIT v3 para identificar amenazas relevantes según el tipo y criticidad del activo.")
        
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
                            key=f"vuln_{idx}_{activo_sel}",
                            label_visibility="collapsed"
                        )
                        if am.get('justificacion'):
                            st.caption(f"💡 *{am['justificacion']}*")
                    
                    with col2:
                        st.markdown("**Degradación Sugerida:**")
                        deg_d = st.slider(f"D", 0, 100, am['degradacion_d'], 5, key=f"deg_d_{idx}_{activo_sel}")
                        deg_i = st.slider(f"I", 0, 100, am['degradacion_i'], 5, key=f"deg_i_{idx}_{activo_sel}")
                        deg_c = st.slider(f"C", 0, 100, am['degradacion_c'], 5, key=f"deg_c_{idx}_{activo_sel}")
                        
                        # Calcular impacto
                        imp_d = valor_d * (deg_d / 100)
                        imp_i = valor_i * (deg_i / 100)
                        imp_c = valor_c * (deg_c / 100)
                        impacto = max(imp_d, imp_i, imp_c)
                        
                        if impacto >= 2.5:
                            st.error(f"Impacto: **{impacto:.2f}** (Crítico)")
                        elif impacto >= 1.5:
                            st.warning(f"Impacto: **{impacto:.2f}** (Alto)")
                        elif impacto >= 0.5:
                            st.info(f"Impacto: **{impacto:.2f}** (Medio)")
                        else:
                            st.success(f"Impacto: **{impacto:.2f}** (Bajo)")
                    
                    # Checkbox para incluir
                    incluir = st.checkbox("✅ Incluir esta amenaza", value=True, key=f"incluir_{idx}_{activo_sel}")
                    
                    if incluir:
                        amenazas_a_guardar.append({
                            "codigo": am['codigo_amenaza'],
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
            col_save1, col_save2 = st.columns([1, 2])
            
            with col_save1:
                if st.button("💾 Guardar Todas", type="primary", key="btn_guardar_amenazas"):
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
                                deg_d=am['deg_d'] / 100,
                                deg_i=am['deg_i'] / 100,
                                deg_c=am['deg_c'] / 100
                            )
                            guardadas += 1
                        except Exception as e:
                            st.error(f"Error guardando {am['codigo']}: {e}")
                    
                    if guardadas > 0:
                        st.success(f"✅ Se guardaron {guardadas} amenazas/vulnerabilidades")
                        # Limpiar resultados de IA
                        del st.session_state[key_amenazas]
                        st.rerun()
            
            with col_save2:
                st.caption(f"Se guardarán **{len(amenazas_a_guardar)}** amenazas seleccionadas con sus degradaciones.")
        
        st.markdown("---")
        
        # ===== VULNERABILIDADES REGISTRADAS =====
        vulns = get_vulnerabilidades_activo(ID_EVALUACION, activo_sel)
        
        if not vulns.empty:
            st.subheader(f"📋 Vulnerabilidades/Amenazas Guardadas: {activo_info['Nombre_Activo']}")
            
            # Calcular impactos
            vulns["Impacto"] = vulns.apply(
                lambda row: max(
                    valor_d * row.get("Degradacion_D", 0),
                    valor_i * row.get("Degradacion_I", 0),
                    valor_c * row.get("Degradacion_C", 0)
                ), axis=1
            )
            
            # Formatear degradación
            vulns_display = vulns.copy()
            for col in ["Degradacion_D", "Degradacion_I", "Degradacion_C"]:
                if col in vulns_display.columns:
                    vulns_display[col] = vulns_display[col].apply(lambda x: f"{x*100:.0f}%" if pd.notna(x) else "0%")
            
            cols = ["Cod_Amenaza", "Vulnerabilidad", "Amenaza", 
                    "Degradacion_D", "Degradacion_I", "Degradacion_C", "Impacto"]
            cols_existentes = [c for c in cols if c in vulns_display.columns]
            
            def colorear_impacto(val):
                try:
                    v = float(val)
                    if v >= 2.5: return "background-color: #ff4444; color: white"
                    elif v >= 1.5: return "background-color: #ff8800; color: white"
                    elif v >= 0.5: return "background-color: #ffbb33; color: black"
                    return "background-color: #00C851; color: white"
                except:
                    return ""
            
            if "Impacto" in cols_existentes:
                styled_df = vulns_display[cols_existentes].style.map(colorear_impacto, subset=["Impacto"])
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
            else:
                st.dataframe(vulns_display[cols_existentes], use_container_width=True, hide_index=True)
            
            # Eliminar vulnerabilidad
            with st.expander("🗑️ Eliminar Vulnerabilidad/Amenaza"):
                vuln_a_eliminar = st.selectbox(
                    "Seleccionar para eliminar",
                    vulns["id"].tolist(),
                    format_func=lambda x: f"[{vulns[vulns['id'] == x]['Cod_Amenaza'].values[0]}] {vulns[vulns['id'] == x]['Vulnerabilidad'].values[0][:50]}..."
                )
                if st.button("🗑️ Eliminar", type="secondary", key="btn_del_vuln"):
                    eliminar_vulnerabilidad_amenaza(vuln_a_eliminar)
                    st.success("✅ Vulnerabilidad/Amenaza eliminada")
                    st.rerun()
        else:
            st.info("📭 No hay vulnerabilidades/amenazas registradas. Usa el botón 'Analizar con IA' para identificar automáticamente.")
    
    st.markdown("---")
    
    # ===== RESUMEN GENERAL =====
    st.subheader("📋 Resumen: Todas las Vulnerabilidades/Amenazas de la Evaluación")
    todas_vulns = get_vulnerabilidades_evaluacion(ID_EVALUACION)
    
    if not todas_vulns.empty:
        for idx, row in todas_vulns.iterrows():
            val = get_valoracion_activo(ID_EVALUACION, row["ID_Activo"])
            if val:
                todas_vulns.loc[idx, "Criticidad"] = val.get("Criticidad", 0)
                v_d = val.get("Valor_D", 0)
                v_i = val.get("Valor_I", 0)
                v_c = val.get("Valor_C", 0)
                todas_vulns.loc[idx, "Impacto"] = max(
                    v_d * row.get("Degradacion_D", 0),
                    v_i * row.get("Degradacion_I", 0),
                    v_c * row.get("Degradacion_C", 0)
                )
        
        cols = ["Nombre_Activo", "Criticidad", "Cod_Amenaza", "Vulnerabilidad", "Amenaza", 
                "Degradacion_D", "Degradacion_I", "Degradacion_C", "Impacto"]
        cols_existentes = [c for c in cols if c in todas_vulns.columns]
        
        todas_vulns_display = todas_vulns.copy()
        for col in ["Degradacion_D", "Degradacion_I", "Degradacion_C"]:
            if col in todas_vulns_display.columns:
                todas_vulns_display[col] = todas_vulns_display[col].apply(lambda x: f"{float(x)*100:.0f}%" if pd.notna(x) else "0%")
        
        st.dataframe(todas_vulns_display[cols_existentes], use_container_width=True, hide_index=True)
        
        # Estadísticas
        st.markdown("### 📈 Estadísticas")
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.metric("Total Vulnerabilidades", len(todas_vulns))
        with col_stat2:
            if "Impacto" in todas_vulns.columns:
                alto_impacto = len(todas_vulns[todas_vulns["Impacto"] >= 1.5])
                st.metric("Alto Impacto (≥1.5)", alto_impacto)
        with col_stat3:
            activos_afectados = todas_vulns["ID_Activo"].nunique()
            st.metric("Activos Afectados", activos_afectados)
    else:
        st.info("📭 No hay vulnerabilidades/amenazas registradas en esta evaluación.")


# ==================== TAB 5: RIESGO (FRECUENCIA AUTOMÁTICA) ====================

with tab5:
    st.header("⚡ Cálculo de Riesgo")
    st.markdown("""
    **Propósito:** Calcular el riesgo para cada par activo-amenaza identificado.
    
    **Fórmula MAGERIT:** `RIESGO = FRECUENCIA × IMPACTO`
    
    **💡 La FRECUENCIA se calcula automáticamente** basándose en:
    - Criticidad del activo (D/I/C)
    - RTO (Tiempo de Recuperación)
    - BIA (Impacto al Negocio)
    - Tipo de amenaza
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
            | ≥ 2.5 | Crítico 🔴 |
            | ≥ 1.5 | Alto 🟠 |
            | ≥ 0.5 | Medio 🟡 |
            | < 0.5 | Bajo 🟢 |
            """)
        
        with col_ref3:
            st.markdown("**⚠️ Riesgo:**")
            st.markdown("""
            | Rango | Nivel |
            |:-----:|:-----:|
            | ≥ 6.0 | Crítico 🔴 |
            | ≥ 4.0 | Alto 🟠 |
            | ≥ 2.0 | Medio 🟡 |
            | < 2.0 | Bajo 🟢 |
            """)
    
    st.markdown("---")
    
    # Obtener vulnerabilidades
    todas_vulns = get_vulnerabilidades_evaluacion(ID_EVALUACION)
    
    if todas_vulns.empty:
        st.warning("⚠️ No hay vulnerabilidades/amenazas identificadas. Ve a la pestaña 'Vulnerabilidades y Amenazas' primero.")
        st.stop()
    
    # Obtener activos
    activos = get_activos_matriz(ID_EVALUACION)
    
    # ===== SELECTOR DE ACTIVO =====
    st.subheader("📦 Selección de Activo")
    
    activo_sel = st.selectbox(
        "🎯 Seleccionar Activo para Calcular Riesgo",
        activos["ID_Activo"].tolist(),
        format_func=lambda x: f"{activos[activos['ID_Activo'] == x]['Nombre_Activo'].values[0]} ({activos[activos['ID_Activo'] == x]['Tipo_Activo'].values[0]})",
        key="riesgo_activo_sel"
    )
    
    if activo_sel:
        activo_info = activos[activos["ID_Activo"] == activo_sel].iloc[0]
        vulns_activo = get_vulnerabilidades_activo(ID_EVALUACION, activo_sel)
        valoracion = get_valoracion_activo(ID_EVALUACION, activo_sel)
        
        # Valores D/I/C
        valor_d = valoracion.get("Valor_D", 0) if valoracion else 0
        valor_i = valoracion.get("Valor_I", 0) if valoracion else 0
        valor_c = valoracion.get("Valor_C", 0) if valoracion else 0
        criticidad = valoracion.get("Criticidad", 0) if valoracion else 0
        criticidad_nivel = valoracion.get("Criticidad_Nivel", "Sin valorar") if valoracion else "Sin valorar"
        rto_nivel = valoracion.get("RTO_Nivel", "N/A") if valoracion else "N/A"
        bia_nivel = valoracion.get("BIA_Nivel", "N/A") if valoracion else "N/A"
        
        # ===== INFORMACIÓN DEL ACTIVO =====
        st.markdown("---")
        st.markdown("### 📋 Información del Activo")
        
        col_info1, col_info2, col_info3, col_info4 = st.columns(4)
        with col_info1:
            st.markdown(f"**ID:** `{activo_sel}`")
        with col_info2:
            st.markdown(f"**Nombre:** {activo_info['Nombre_Activo']}")
        with col_info3:
            st.markdown(f"**Tipo:** {activo_info['Tipo_Activo']}")
        with col_info4:
            crit_color = {"Alta": "🔴", "Media": "🟡", "Baja": "🟢"}.get(criticidad_nivel, "⚪")
            st.markdown(f"**Criticidad:** {crit_color} {criticidad} ({criticidad_nivel})")
        
        # Valoración D/I/C + RTO/BIA
        col_v1, col_v2, col_v3, col_v4, col_v5 = st.columns(5)
        with col_v1:
            st.metric("D", valor_d)
        with col_v2:
            st.metric("I", valor_i)
        with col_v3:
            st.metric("C", valor_c)
        with col_v4:
            st.metric("RTO", rto_nivel)
        with col_v5:
            st.metric("BIA", bia_nivel)
        
        # ===== FRECUENCIA CALCULADA AUTOMÁTICAMENTE =====
        st.markdown("---")
        st.markdown("### 🤖 Frecuencia Calculada Automáticamente")
        
        freq_base, freq_nivel, freq_detalles = calcular_frecuencia_desde_cuestionario(ID_EVALUACION, activo_sel)
        
        col_freq1, col_freq2 = st.columns([1, 2])
        with col_freq1:
            freq_color = {"Alta": "🔴", "Media": "🟡", "Baja": "🟢", "Nula": "⚪"}.get(freq_nivel, "⚪")
            st.metric(f"{freq_color} Frecuencia Base", f"{freq_base} ({freq_nivel})")
        
        with col_freq2:
            st.info(f"""
            **Factores considerados:**
            - Criticidad: {freq_detalles.get('factores', {}).get('criticidad_aporte', 'N/A')}
            - RTO: {freq_detalles.get('factores', {}).get('rto_aporte', 'N/A')}
            - BIA: {freq_detalles.get('factores', {}).get('bia_aporte', 'N/A')}
            """)
        
        st.markdown("---")
        
        if vulns_activo.empty:
            st.warning("⚠️ Este activo no tiene vulnerabilidades/amenazas registradas. Ve al Tab 4 primero.")
        else:
            st.markdown("### ⚡ Riesgo por Amenaza")
            
            # Calcular frecuencia y riesgo para todas las amenazas
            amenazas_con_riesgo = calcular_frecuencia_todas_amenazas(ID_EVALUACION, activo_sel)
            
            if amenazas_con_riesgo:
                st.success(f"✅ Se calcularon automáticamente **{len(amenazas_con_riesgo)}** riesgos basados en el cuestionario.")
                
                # Mostrar tabla resumen
                df_riesgos = pd.DataFrame(amenazas_con_riesgo)
                
                # Formatear columnas
                df_display = df_riesgos[["cod_amenaza", "amenaza", "impacto", "frecuencia", "frecuencia_nivel", "riesgo"]].copy()
                df_display.columns = ["Código", "Amenaza", "Impacto", "Frecuencia", "Freq. Nivel", "RIESGO"]
                df_display["Impacto"] = df_display["Impacto"].apply(lambda x: f"{x:.2f}")
                df_display["RIESGO"] = df_display["RIESGO"].apply(lambda x: f"{x:.2f}")
                
                # Colorear riesgo
                def colorear_riesgo(val):
                    try:
                        v = float(val)
                        if v >= 6: return "background-color: #ff4444; color: white"
                        elif v >= 4: return "background-color: #ff8800; color: white"
                        elif v >= 2: return "background-color: #ffbb33; color: black"
                        return "background-color: #00C851; color: white"
                    except:
                        return ""
                
                styled_df = df_display.style.map(colorear_riesgo, subset=["RIESGO"])
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                
                # Mostrar detalle expandible de cada amenaza
                st.markdown("#### 📋 Detalle por Amenaza")
                for am in amenazas_con_riesgo:
                    riesgo = am["riesgo"]
                    if riesgo >= 6:
                        icon = "🔴"
                    elif riesgo >= 4:
                        icon = "🟠"
                    elif riesgo >= 2:
                        icon = "🟡"
                    else:
                        icon = "🟢"
                    
                    with st.expander(f"{icon} [{am['cod_amenaza']}] {am['amenaza']} - Riesgo: {riesgo:.2f}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Vulnerabilidad:** {am['vulnerabilidad'][:200]}...")
                            st.markdown(f"**Impacto:** {am['impacto']:.2f}")
                        with col2:
                            st.markdown(f"**Frecuencia:** {am['frecuencia']} ({am['frecuencia_nivel']})")
                            st.markdown(f"**Cálculo:** {am['frecuencia']} × {am['impacto']:.2f} = **{riesgo:.2f}**")
                            
                            # Ajuste manual si se desea
                            freq_manual = st.select_slider(
                                "Ajustar frecuencia (opcional)",
                                options=[0.1, 1, 2, 3],
                                value=am['frecuencia'],
                                key=f"freq_adj_{am['id_va']}",
                                format_func=lambda x: f"{x} - {['Nula', 'Baja', 'Media', 'Alta'][int(x) if x >= 1 else 0]}"
                            )
                            
                            if freq_manual != am['frecuencia']:
                                nuevo_riesgo = freq_manual * am['impacto']
                                st.info(f"Riesgo ajustado: {freq_manual} × {am['impacto']:.2f} = **{nuevo_riesgo:.2f}**")
                
                # Botón para guardar todos los riesgos
                st.markdown("---")
                col_save1, col_save2 = st.columns([1, 2])
                
                with col_save1:
                    if st.button("💾 Guardar Todos los Riesgos", type="primary", key="save_all_risks"):
                        guardados = 0
                        for am in amenazas_con_riesgo:
                            # Verificar si hay ajuste manual
                            freq_ajustada = st.session_state.get(f"freq_adj_{am['id_va']}", am['frecuencia'])
                            calcular_riesgo_amenaza(
                                id_evaluacion=ID_EVALUACION,
                                id_activo=activo_sel,
                                id_va=am['id_va'],
                                frecuencia=freq_ajustada
                            )
                            guardados += 1
                        st.success(f"✅ Se guardaron {guardados} riesgos calculados automáticamente")
                        st.rerun()
                
                with col_save2:
                    st.caption("Guarda los riesgos con la frecuencia calculada automáticamente (o ajustada manualmente).")
    
    st.markdown("---")
    
    # ===== RESUMEN DE TODOS LOS RIESGOS =====
    st.subheader("📋 Resumen: Todos los Riesgos de la Evaluación")
    riesgos = get_riesgos_evaluacion(ID_EVALUACION)
    
    if not riesgos.empty:
        # Mostrar tabla con colores
        cols = ["Nombre_Activo", "Amenaza", "Impacto", "Frecuencia", "Frecuencia_Nivel", "Riesgo"]
        cols_existentes = [c for c in cols if c in riesgos.columns]
        
        def colorear_riesgo_tabla(val):
            try:
                v = float(val)
                if v >= 6: return "background-color: #ff4444; color: white"
                elif v >= 4: return "background-color: #ff8800; color: white"
                elif v >= 2: return "background-color: #ffbb33; color: black"
                else: return "background-color: #00C851; color: white"
            except:
                return ""
        
        if "Riesgo" in cols_existentes:
            styled_df = riesgos[cols_existentes].style.map(colorear_riesgo_tabla, subset=["Riesgo"])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(riesgos[cols_existentes], use_container_width=True, hide_index=True)
        
        # Estadísticas
        st.markdown("### 📈 Estadísticas de Riesgo")
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("Total Riesgos", len(riesgos))
        with col_stat2:
            criticos = len(riesgos[riesgos["Riesgo"] >= 6])
            st.metric("🔴 Críticos (≥6)", criticos)
        with col_stat3:
            altos = len(riesgos[(riesgos["Riesgo"] >= 4) & (riesgos["Riesgo"] < 6)])
            st.metric("🟠 Altos (4-6)", altos)
        with col_stat4:
            riesgo_promedio = riesgos["Riesgo"].mean()
            st.metric("📊 Promedio", f"{riesgo_promedio:.2f}")
        
        # Límite de riesgo organizacional
        st.markdown("---")
        st.markdown("### 🎯 Límite de Riesgo Organizacional")
        limite_riesgo = 7.0
        riesgos_sobre_limite = len(riesgos[riesgos["Riesgo"] > limite_riesgo])
        
        if riesgos_sobre_limite > 0:
            st.error(f"⚠️ **{riesgos_sobre_limite}** riesgos superan el límite organizacional de **{limite_riesgo}**. Requieren tratamiento urgente.")
        else:
            st.success(f"✅ Todos los riesgos están dentro del límite organizacional ({limite_riesgo})")
    else:
        st.info("📭 No hay riesgos guardados aún. Seleccione un activo y guarde los riesgos calculados.")


# ==================== TAB 6: MAPA DE RIESGOS ====================

with tab6:
    st.header("🗺️ Mapa de Riesgos")
    st.markdown("""
    **Propósito:** Matriz visual de riesgos (Impacto vs Frecuencia) como en Excel.
    
    **Los riesgos provienen de:**
    1. **Tab 4:** Identificación de amenazas/vulnerabilidades con degradación → IMPACTO
    2. **Tab 5:** Cálculo de frecuencia (automático) → RIESGO = FRECUENCIA × IMPACTO
    """)
    
    # Obtener riesgos calculados (del Tab 5)
    riesgos = get_riesgos_evaluacion(ID_EVALUACION)
    
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
    criticos = len(riesgos[riesgos["Riesgo"] >= 6])
    altos = len(riesgos[(riesgos["Riesgo"] >= 4) & (riesgos["Riesgo"] < 6)])
    medios = len(riesgos[(riesgos["Riesgo"] >= 2) & (riesgos["Riesgo"] < 4)])
    bajos = len(riesgos[riesgos["Riesgo"] < 2])
    
    with col_s1:
        st.metric("📊 Total", total)
    with col_s2:
        st.metric("🔴 Críticos", criticos)
    with col_s3:
        st.metric("🟠 Altos", altos)
    with col_s4:
        st.metric("🟡 Medios", medios)
    with col_s5:
        st.metric("🟢 Bajos", bajos)
    
    st.markdown("---")
    
    # ===== MAPA DE CALOR (MATRIZ PROBABILIDAD × IMPACTO) =====
    st.markdown("### 🗺️ Matriz de Riesgos (Probabilidad × Impacto)")
    st.caption("Como en Excel: Las celdas muestran cuántos riesgos caen en cada zona.")
    
    # Crear matriz 4x4 (Frecuencia vs Impacto)
    # Frecuencia: 0.1 (Nula), 1 (Baja), 2 (Media), 3 (Alta)
    # Impacto: <0.5 (Bajo), 0.5-1.5 (Medio), 1.5-2.5 (Alto), >=2.5 (Crítico)
    
    # Clasificar cada riesgo en la matriz
    def clasificar_frecuencia(f):
        if f >= 2.5: return "Alta"
        elif f >= 1.5: return "Media"
        elif f >= 0.5: return "Baja"
        else: return "Nula"
    
    def clasificar_impacto(i):
        if i >= 2.5: return "Crítico"
        elif i >= 1.5: return "Alto"
        elif i >= 0.5: return "Medio"
        else: return "Bajo"
    
    riesgos["Freq_Nivel"] = riesgos["Frecuencia"].apply(clasificar_frecuencia)
    riesgos["Imp_Nivel"] = riesgos["Impacto"].apply(clasificar_impacto)
    
    # Contar riesgos por celda
    freq_niveles = ["Nula", "Baja", "Media", "Alta"]
    imp_niveles = ["Bajo", "Medio", "Alto", "Crítico"]
    
    # Crear matriz de conteo
    matriz_data = []
    for imp in reversed(imp_niveles):  # De arriba a abajo: Crítico -> Bajo
        fila = {"Impacto": imp}
        for freq in freq_niveles:
            count = len(riesgos[(riesgos["Freq_Nivel"] == freq) & (riesgos["Imp_Nivel"] == imp)])
            fila[freq] = count
        matriz_data.append(fila)
    
    df_matriz = pd.DataFrame(matriz_data)
    df_matriz.set_index("Impacto", inplace=True)
    
    # Definir colores para cada celda de la matriz (MAGERIT)
    # Formato: [fila (impacto)][columna (frecuencia)]
    colores_matriz = {
        ("Crítico", "Alta"): "#ff0000",      # Rojo intenso
        ("Crítico", "Media"): "#ff4444",     # Rojo
        ("Crítico", "Baja"): "#ff8800",      # Naranja
        ("Crítico", "Nula"): "#ffbb33",      # Amarillo oscuro
        ("Alto", "Alta"): "#ff4444",         # Rojo
        ("Alto", "Media"): "#ff8800",        # Naranja
        ("Alto", "Baja"): "#ffbb33",         # Amarillo oscuro
        ("Alto", "Nula"): "#ffdd00",         # Amarillo
        ("Medio", "Alta"): "#ff8800",        # Naranja
        ("Medio", "Media"): "#ffbb33",       # Amarillo oscuro
        ("Medio", "Baja"): "#ffdd00",        # Amarillo
        ("Medio", "Nula"): "#99dd00",        # Verde amarillo
        ("Bajo", "Alta"): "#ffbb33",         # Amarillo oscuro
        ("Bajo", "Media"): "#ffdd00",        # Amarillo
        ("Bajo", "Baja"): "#99dd00",         # Verde amarillo
        ("Bajo", "Nula"): "#00C851",         # Verde
    }
    
    # Crear mapa de calor con Plotly
    z_values = df_matriz.values
    x_labels = ["Nula (0.1)", "Baja (1)", "Media (2)", "Alta (3)"]
    y_labels = ["Crítico (≥2.5)", "Alto (1.5-2.5)", "Medio (0.5-1.5)", "Bajo (<0.5)"]
    
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
    for i, imp in enumerate(["Crítico", "Alto", "Medio", "Bajo"]):
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
        st.markdown("🟢 **Riesgo Bajo** - Aceptar/Monitorear")
    with col_leg2:
        st.markdown("🟡 **Riesgo Medio** - Reducir si es posible")
    with col_leg3:
        st.markdown("🟠 **Riesgo Alto** - Tratar prioritario")
    with col_leg4:
        st.markdown("🔴 **Riesgo Crítico** - Acción inmediata")
    
    st.markdown("---")
    
    # ===== GRÁFICO DE DISPERSIÓN =====
    st.markdown("### 📊 Gráfico de Dispersión (Detalle)")
    
    # Crear figura con zonas de color
    fig = go.Figure()
    
    # Agregar zonas de fondo
    # Zona Verde (Bajo)
    fig.add_shape(type="rect", x0=0, y0=0, x1=1, y1=0.5,
                  fillcolor="rgba(0, 200, 81, 0.3)", line_width=0)
    fig.add_shape(type="rect", x0=0, y0=0, x1=0.5, y1=1,
                  fillcolor="rgba(0, 200, 81, 0.3)", line_width=0)
    
    # Zona Amarilla (Medio)
    fig.add_shape(type="rect", x0=0.5, y0=0.5, x1=2, y1=1.5,
                  fillcolor="rgba(255, 221, 0, 0.3)", line_width=0)
    
    # Zona Naranja (Alto)
    fig.add_shape(type="rect", x0=1.5, y0=1.5, x1=2.5, y1=2.5,
                  fillcolor="rgba(255, 136, 0, 0.3)", line_width=0)
    
    # Zona Roja (Crítico)
    fig.add_shape(type="rect", x0=2, y0=2, x1=3.5, y1=3.5,
                  fillcolor="rgba(255, 0, 0, 0.3)", line_width=0)
    
    # Determinar color de cada punto
    def color_riesgo(r):
        if r >= 6: return "red"
        elif r >= 4: return "orange"
        elif r >= 2: return "gold"
        else: return "green"
    
    colores = riesgos["Riesgo"].apply(color_riesgo)
    
    # Agregar puntos
    fig.add_trace(go.Scatter(
        x=riesgos["Frecuencia"],
        y=riesgos["Impacto"],
        mode="markers+text",
        marker=dict(
            size=riesgos["Riesgo"] * 5 + 10,  # Tamaño proporcional al riesgo
            color=colores,
            line=dict(width=2, color="white"),
            opacity=0.8
        ),
        text=riesgos.apply(lambda r: f"R{r.name+1}", axis=1),
        textposition="top center",
        textfont=dict(size=10),
        hovertemplate="<b>%{customdata[0]}</b><br>" +
                      "Amenaza: %{customdata[1]}<br>" +
                      "Impacto: %{y:.2f}<br>" +
                      "Frecuencia: %{x:.2f}<br>" +
                      "Riesgo: %{customdata[2]:.2f}<extra></extra>",
        customdata=riesgos[["Nombre_Activo", "Amenaza", "Riesgo"]].values
    ))
    
    fig.update_layout(
        title="Dispersión de Riesgos",
        xaxis_title="Frecuencia (Probabilidad)",
        yaxis_title="Impacto",
        xaxis=dict(range=[0, 3.5], tickvals=[0.1, 1, 2, 3], 
                   ticktext=["Nula", "Baja", "Media", "Alta"]),
        yaxis=dict(range=[0, 3.5]),
        height=450,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ===== LISTA DE RIESGOS =====
    st.markdown("### 📋 Lista de Riesgos")
    
    # Agregar columna de zona de riesgo
    def zona_riesgo(r):
        if r >= 6: return "🔴 Crítico"
        elif r >= 4: return "🟠 Alto"
        elif r >= 2: return "🟡 Medio"
        else: return "🟢 Bajo"
    
    riesgos_display = riesgos.copy()
    riesgos_display["Zona"] = riesgos_display["Riesgo"].apply(zona_riesgo)
    riesgos_display["ID"] = riesgos_display.index.map(lambda x: f"R{x+1}")
    
    # Ordenar por riesgo descendente
    riesgos_display = riesgos_display.sort_values("Riesgo", ascending=False)
    
    # Seleccionar columnas a mostrar
    cols_mostrar = ["ID", "Nombre_Activo", "Amenaza", "Impacto", "Frecuencia", "Frecuencia_Nivel", "Riesgo", "Zona"]
    cols_existentes = [c for c in cols_mostrar if c in riesgos_display.columns]
    
    # Formatear valores numéricos
    df_show = riesgos_display[cols_existentes].copy()
    if "Impacto" in df_show.columns:
        df_show["Impacto"] = df_show["Impacto"].apply(lambda x: f"{x:.2f}")
    if "Riesgo" in df_show.columns:
        df_show["Riesgo"] = df_show["Riesgo"].apply(lambda x: f"{x:.2f}")
    
    st.dataframe(df_show, use_container_width=True, hide_index=True)
    
    # ===== CUADRO DESCRIPTIVO DE RIESGOS =====
    st.markdown("---")
    st.markdown("### 📝 Cuadro Descriptivo de Riesgos")
    st.caption("Tabla con número de riesgo y su descripción completa")
    
    # Crear tabla descriptiva con ID, descripción del riesgo
    tabla_descriptiva = []
    for idx, row in riesgos_display.iterrows():
        id_riesgo = row["ID"]
        activo = row.get("Nombre_Activo", "N/A")
        amenaza = row.get("Amenaza", "N/A")
        vulnerabilidad = row.get("Vulnerabilidad", "N/A")
        impacto = row.get("Impacto", 0)
        frecuencia = row.get("Frecuencia", 0)
        riesgo_val = row.get("Riesgo", 0)
        zona = row.get("Zona", "N/A")
        
        # Construir descripción
        descripcion = f"El activo '{activo}' está expuesto a la amenaza '{amenaza}'"
        if vulnerabilidad and vulnerabilidad != "N/A":
            descripcion += f", con vulnerabilidad: {vulnerabilidad}"
        
        tabla_descriptiva.append({
            "N° Riesgo": id_riesgo,
            "Activo": activo,
            "Amenaza": amenaza,
            "Descripción/Vulnerabilidad": vulnerabilidad if vulnerabilidad else "Sin especificar",
            "Impacto": f"{impacto:.2f}" if isinstance(impacto, (int, float)) else impacto,
            "Frecuencia": f"{frecuencia:.2f}" if isinstance(frecuencia, (int, float)) else frecuencia,
            "Valor Riesgo": f"{riesgo_val:.2f}" if isinstance(riesgo_val, (int, float)) else riesgo_val,
            "Zona de Riesgo": zona
        })
    
    df_descripcion = pd.DataFrame(tabla_descriptiva)
    
    # Mostrar tabla con estilo
    st.dataframe(
        df_descripcion, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "N° Riesgo": st.column_config.TextColumn("N° Riesgo", width="small"),
            "Activo": st.column_config.TextColumn("Activo", width="medium"),
            "Amenaza": st.column_config.TextColumn("Amenaza", width="medium"),
            "Descripción/Vulnerabilidad": st.column_config.TextColumn("Descripción/Vulnerabilidad", width="large"),
            "Impacto": st.column_config.TextColumn("Impacto", width="small"),
            "Frecuencia": st.column_config.TextColumn("Frecuencia", width="small"),
            "Valor Riesgo": st.column_config.TextColumn("Riesgo", width="small"),
            "Zona de Riesgo": st.column_config.TextColumn("Zona", width="small"),
        }
    )
    
    # Opción para descargar la tabla
    st.download_button(
        label="📥 Descargar Cuadro de Riesgos (CSV)",
        data=df_descripcion.to_csv(index=False, encoding='utf-8-sig'),
        file_name="cuadro_riesgos.csv",
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
    """)
    
    # Botón para recalcular todos
    if st.button("🔄 Recalcular Todos los Riesgos", type="primary"):
        count = recalcular_todos_riesgos_activos(ID_EVALUACION)
        st.success(f"✅ {count} activos recalculados")
        st.rerun()
    
    riesgos_activos = get_riesgos_activos_evaluacion(ID_EVALUACION)
    
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
            observacion = "⚠️ CRÍTICO: Tratamiento urgente requerido. Implementar salvaguardas inmediatamente."
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
            "ID_Activo": row.get("ID_Activo", f"ACT-{idx+1}"),
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
            "ID_Activo": st.column_config.TextColumn("ID Activo", width="small"),
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
    """)
    
    # Importar función de sugerencia de IA
    from services.ollama_magerit_service import sugerir_salvaguardas_ia, sugerir_salvaguardas_batch
    
    # ===== TABLA PRINCIPAL DE RIESGOS CON SALVAGUARDAS SUGERIDAS =====
    st.markdown("### 📋 Tabla de Riesgos con Salvaguardas Sugeridas")
    
    # Obtener todos los riesgos de la evaluación
    riesgos = get_riesgos_evaluacion(ID_EVALUACION)
    activos = get_activos_matriz(ID_EVALUACION)
    
    if riesgos.empty:
        st.warning("⚠️ No hay riesgos calculados. Ve al Tab 5 (Riesgo) primero para calcular los riesgos.")
        st.stop()
    
    # Combinar con datos de activos para obtener tipo
    if not activos.empty:
        riesgos = riesgos.merge(
            activos[["ID_Activo", "Tipo_Activo"]], 
            on="ID_Activo", 
            how="left"
        )
    else:
        riesgos["Tipo_Activo"] = ""
    
    # Botón para generar salvaguardas con IA
    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        generar_ia = st.button("🤖 Generar Salvaguardas con IA", type="primary")
    with col_btn2:
        st.caption("La IA analizará cada riesgo y sugerirá salvaguardas y controles ISO 27002")
    
    # Session state para guardar resultados
    if "salvaguardas_generadas" not in st.session_state:
        st.session_state.salvaguardas_generadas = None
    
    if generar_ia:
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
                    zona = "CRÍTICO" if row.get("Riesgo", 0) >= 6 else "ALTO" if row.get("Riesgo", 0) >= 4 else "MEDIO"
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
            zona = "CRÍTICO" if row.get("Riesgo", 0) >= 6 else "ALTO" if row.get("Riesgo", 0) >= 4 else "MEDIO"
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
    
    # Preparar tabla para mostrar
    tabla_salvaguardas = []
    for idx, row in df_display.iterrows():
        riesgo_val = row.get("Riesgo", 0)
        if riesgo_val >= 6:
            zona = "🔴 Crítico"
            prioridad = "Alta"
        elif riesgo_val >= 4:
            zona = "🟠 Alto"
            prioridad = "Alta"
        elif riesgo_val >= 2:
            zona = "🟡 Medio"
            prioridad = "Media"
        else:
            zona = "🟢 Bajo"
            prioridad = "Baja"
        
        tabla_salvaguardas.append({
            "ID Activo": row.get("ID_Activo", ""),
            "Nombre Activo": row.get("Nombre_Activo", ""),
            "Riesgo": round(riesgo_val, 2),
            "Zona": zona,
            "Vulnerabilidad": row.get("Vulnerabilidad", "")[:50] + "..." if len(str(row.get("Vulnerabilidad", ""))) > 50 else row.get("Vulnerabilidad", ""),
            "Amenaza": row.get("Amenaza", ""),
            "Salvaguarda Sugerida": row.get("Salvaguarda_Sugerida", ""),
            "Control ISO 27002": row.get("Control_ISO", ""),
            "Prioridad": prioridad,
            "IA": row.get("Generado_IA", "🔧")
        })
    
    df_tabla_salv = pd.DataFrame(tabla_salvaguardas)
    
    # Ordenar por riesgo descendente
    df_tabla_salv = df_tabla_salv.sort_values("Riesgo", ascending=False)
    
    st.dataframe(
        df_tabla_salv,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID Activo": st.column_config.TextColumn("ID", width="small"),
            "Nombre Activo": st.column_config.TextColumn("Activo", width="medium"),
            "Riesgo": st.column_config.NumberColumn("Riesgo", format="%.2f", width="small"),
            "Zona": st.column_config.TextColumn("Zona", width="small"),
            "Vulnerabilidad": st.column_config.TextColumn("Vulnerabilidad", width="medium"),
            "Amenaza": st.column_config.TextColumn("Amenaza", width="medium"),
            "Salvaguarda Sugerida": st.column_config.TextColumn("Salvaguarda", width="large"),
            "Control ISO 27002": st.column_config.TextColumn("Control ISO", width="medium"),
            "Prioridad": st.column_config.TextColumn("Prioridad", width="small"),
            "IA": st.column_config.TextColumn("", width="small")
        }
    )
    
    # Leyenda
    st.caption("✅ = Generado por IA | 🔧 = Generado heurísticamente")
    
    # Botón de descarga
    st.download_button(
        label="📥 Descargar Tabla de Salvaguardas (CSV)",
        data=df_tabla_salv.to_csv(index=False, encoding='utf-8-sig'),
        file_name="salvaguardas_sugeridas.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    
    # ===== SECCIÓN DE GESTIÓN DE SALVAGUARDAS =====
    st.markdown("### ⚙️ Gestión de Salvaguardas")
    
    activos = get_activos_matriz(ID_EVALUACION)
    
    if not activos.empty:
        # Selector de activo
        activo_sel = st.selectbox(
            "Seleccionar Activo para gestionar salvaguardas",
            activos["ID_Activo"].tolist(),
            format_func=lambda x: activos[activos["ID_Activo"] == x]["Nombre_Activo"].values[0],
            key="salv_activo_sel"
        )
        
        if activo_sel:
            activo_info = activos[activos["ID_Activo"] == activo_sel].iloc[0]
            
            st.subheader(f"📦 {activo_info['Nombre_Activo']}")
            
            # Obtener vulnerabilidades para contexto
            vulns = get_vulnerabilidades_activo(ID_EVALUACION, activo_sel)
            
            # Formulario para agregar salvaguarda manual
            with st.expander("➕ Agregar Salvaguarda Manual", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Seleccionar vulnerabilidad si hay
                    if not vulns.empty:
                        vuln_sel = st.selectbox(
                            "Relacionar con Vulnerabilidad",
                            ["-- Sin relación --"] + vulns["Vulnerabilidad"].tolist()
                        )
                        amenaza_sel = ""
                        if vuln_sel != "-- Sin relación --":
                            amenaza_sel = vulns[vulns["Vulnerabilidad"] == vuln_sel]["Amenaza"].values[0]
                    else:
                        vuln_sel = ""
                        amenaza_sel = ""
                    
                    salvaguarda = st.text_area(
                        "Salvaguarda / Control *",
                        placeholder="Descripción detallada del control a implementar..."
                    )
                
                with col2:
                    prioridad = st.selectbox(
                        "Prioridad",
                        ["Alta", "Media", "Baja"]
                    )
                    responsable = st.text_input("Responsable")
                    fecha_limite = st.date_input("Fecha Límite", value=None)
                
                if st.button("✅ Agregar Salvaguarda", type="primary", key="btn_add_salv"):
                    if salvaguarda:
                        agregar_salvaguarda(
                            id_evaluacion=ID_EVALUACION,
                            id_activo=activo_sel,
                            nombre_activo=activo_info['Nombre_Activo'],
                            salvaguarda=salvaguarda,
                            vulnerabilidad=vuln_sel if vuln_sel != "-- Sin relación --" else "",
                            amenaza=amenaza_sel,
                            prioridad=prioridad,
                            responsable=responsable,
                            fecha_limite=str(fecha_limite) if fecha_limite else ""
                        )
                        st.success("✅ Salvaguarda agregada")
                        st.rerun()
                    else:
                        st.error("❌ La salvaguarda es obligatoria")
            
            # Salvaguardas del activo
            salvs = get_salvaguardas_activo(ID_EVALUACION, activo_sel)
            
            if not salvs.empty:
                st.markdown(f"**Salvaguardas registradas para {activo_info['Nombre_Activo']}:**")
                
                for idx, salv in salvs.iterrows():
                    estado_icon = {
                        "Pendiente": "⏳",
                        "En Proceso": "🔄",
                        "Implementada": "✅"
                    }.get(salv["Estado"], "⏳")
                    
                    prioridad_icon = {
                        "Alta": "🔴",
                        "Media": "🟡",
                        "Baja": "🟢"
                    }.get(salv["Prioridad"], "🟡")
                    
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.markdown(f"**{prioridad_icon} {salv['Salvaguarda']}**")
                            if salv["Vulnerabilidad"]:
                                st.caption(f"Vulnerabilidad: {salv['Vulnerabilidad']}")
                            if salv["Responsable"]:
                                st.caption(f"Responsable: {salv['Responsable']}")
                        
                        with col2:
                            nuevo_estado = st.selectbox(
                                "Estado",
                                ["Pendiente", "En Proceso", "Implementada"],
                                index=["Pendiente", "En Proceso", "Implementada"].index(salv["Estado"]),
                                key=f"estado_salv_{salv['id']}"
                            )
                            if nuevo_estado != salv["Estado"]:
                                actualizar_estado_salvaguarda(salv["id"], nuevo_estado)
                                st.rerun()
                        
                        with col3:
                            st.markdown(f"{estado_icon} **{salv['Estado']}**")
                            if st.button("🗑️", key=f"del_salv_{salv['id']}"):
                                eliminar_salvaguarda(salv["id"])
                                st.rerun()
                        
                        st.markdown("---")
            else:
                st.info("📭 No hay salvaguardas registradas para este activo.")
    
    st.markdown("---")
    
    # ===== RESUMEN DE SALVAGUARDAS =====
    st.subheader("📋 Resumen de Salvaguardas Registradas")
    todas_salvs = get_salvaguardas_evaluacion(ID_EVALUACION)
    
    if not todas_salvs.empty:
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", len(todas_salvs))
        with col2:
            pendientes = len(todas_salvs[todas_salvs["Estado"] == "Pendiente"])
            st.metric("⏳ Pendientes", pendientes)
        with col3:
            en_proceso = len(todas_salvs[todas_salvs["Estado"] == "En Proceso"])
            st.metric("🔄 En Proceso", en_proceso)
        with col4:
            implementadas = len(todas_salvs[todas_salvs["Estado"] == "Implementada"])
            st.metric("✅ Implementadas", implementadas)
        
        # Gráfico de progreso
        if len(todas_salvs) > 0:
            fig_progreso = go.Figure(data=[
                go.Pie(
                    labels=["Pendiente", "En Proceso", "Implementada"],
                    values=[pendientes, en_proceso, implementadas],
                    hole=0.4,
                    marker_colors=["#ffbb33", "#3498db", "#00C851"]
                )
            ])
            fig_progreso.update_layout(
                title="Estado de Implementación de Salvaguardas",
                height=300
            )
            st.plotly_chart(fig_progreso, use_container_width=True)
    else:
        st.info("📭 No hay salvaguardas registradas en esta evaluación.")


# ==================== TAB 9: DASHBOARDS ====================

with tab9:
    st.header("📈 Dashboards Ejecutivos")
    st.markdown("""
    **Propósito:** Visualizaciones ejecutivas de los activos más críticos, amenazas, vulnerabilidades y riesgos.
    """)
    
    # Obtener datos
    activos = get_activos_matriz(ID_EVALUACION)
    riesgos = get_riesgos_evaluacion(ID_EVALUACION)
    vulnerabilidades = get_vulnerabilidades_evaluacion(ID_EVALUACION)
    riesgos_activos = get_riesgos_activos_evaluacion(ID_EVALUACION)
    
    if activos.empty:
        st.warning("⚠️ No hay datos para mostrar. Agrega activos y completa el flujo de evaluación.")
        st.stop()
    
    # ===== MÉTRICAS GENERALES =====
    st.markdown("### 📊 Métricas Generales")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📦 Activos", len(activos))
    with col2:
        st.metric("⚠️ Vulnerabilidades", len(vulnerabilidades) if not vulnerabilidades.empty else 0)
    with col3:
        st.metric("🎯 Riesgos", len(riesgos) if not riesgos.empty else 0)
    with col4:
        criticos = len(riesgos[riesgos["Riesgo"] >= 6]) if not riesgos.empty else 0
        st.metric("🔴 Críticos", criticos)
    with col5:
        promedio = riesgos["Riesgo"].mean() if not riesgos.empty else 0
        st.metric("📈 Riesgo Prom.", f"{promedio:.2f}")
    
    st.markdown("---")
    
    # ===== SUB-TABS PARA DASHBOARDS =====
    dash_tab1, dash_tab2, dash_tab3, dash_tab4 = st.tabs([
        "🔥 Activos Críticos",
        "⚡ Amenazas",
        "🔓 Vulnerabilidades",
        "📊 Riesgos"
    ])
    
    # ----- Dashboard: Activos Críticos -----
    with dash_tab1:
        st.subheader("🔥 Top 10 Activos Más Críticos")
        
        if not riesgos_activos.empty:
            top_activos = riesgos_activos.sort_values("Riesgo_Actual", ascending=False).head(10)
            
            # Gráfico de barras
            fig = go.Figure()
            
            colores = ["#ff0000" if r >= 6 else "#ff8800" if r >= 4 else "#ffdd00" if r >= 2 else "#00C851" 
                       for r in top_activos["Riesgo_Actual"]]
            
            fig.add_trace(go.Bar(
                x=top_activos["Nombre_Activo"],
                y=top_activos["Riesgo_Actual"],
                marker_color=colores,
                text=top_activos["Riesgo_Actual"].apply(lambda x: f"{x:.2f}"),
                textposition="outside"
            ))
            
            fig.add_hline(y=LIMITE_RIESGO, line_dash="dash", line_color="red", 
                         annotation_text=f"Límite ({LIMITE_RIESGO})")
            
            fig.update_layout(
                title="Riesgo por Activo (Top 10)",
                xaxis_title="Activo",
                yaxis_title="Nivel de Riesgo",
                height=450
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla resumen
            st.dataframe(
                top_activos[["Nombre_Activo", "Riesgo_Actual", "Riesgo_Objetivo", "Num_Amenazas"]].rename(columns={
                    "Nombre_Activo": "Activo",
                    "Riesgo_Actual": "Riesgo",
                    "Riesgo_Objetivo": "Objetivo",
                    "Num_Amenazas": "Amenazas"
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Recalcula los riesgos en Tab 7 para ver los activos críticos.")
    
    # ----- Dashboard: Amenazas -----
    with dash_tab2:
        st.subheader("⚡ Distribución de Amenazas")
        
        if not riesgos.empty and "Amenaza" in riesgos.columns:
            # Contar amenazas
            amenazas_count = riesgos["Amenaza"].value_counts().head(15)
            
            # Gráfico de barras horizontales
            fig = go.Figure(go.Bar(
                y=amenazas_count.index,
                x=amenazas_count.values,
                orientation="h",
                marker_color="#3498db"
            ))
            fig.update_layout(
                title="Top 15 Amenazas Más Frecuentes",
                xaxis_title="Frecuencia",
                yaxis_title="Amenaza",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Tipo de amenaza si está disponible
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribución por zona de riesgo de las amenazas
                def get_zona(r):
                    if r >= 6: return "Crítico"
                    elif r >= 4: return "Alto"
                    elif r >= 2: return "Medio"
                    return "Bajo"
                
                riesgos["Zona"] = riesgos["Riesgo"].apply(get_zona)
                zona_count = riesgos["Zona"].value_counts()
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=zona_count.index,
                    values=zona_count.values,
                    marker_colors=["#ff0000", "#ff8800", "#ffdd00", "#00C851"],
                    hole=0.3
                )])
                fig_pie.update_layout(title="Distribución por Zona de Riesgo", height=350)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Top amenazas por riesgo promedio
                amenaza_riesgo = riesgos.groupby("Amenaza")["Riesgo"].mean().sort_values(ascending=False).head(10)
                
                fig_bar = go.Figure(go.Bar(
                    y=amenaza_riesgo.index,
                    x=amenaza_riesgo.values,
                    orientation="h",
                    marker_color="#e74c3c"
                ))
                fig_bar.update_layout(
                    title="Amenazas por Riesgo Promedio",
                    xaxis_title="Riesgo Promedio",
                    height=350
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No hay amenazas identificadas. Completa el Tab 4 (Vulnerabilidades).")
    
    # ----- Dashboard: Vulnerabilidades -----
    with dash_tab3:
        st.subheader("🔓 Análisis de Vulnerabilidades")
        
        if not vulnerabilidades.empty:
            # Contar vulnerabilidades por activo
            vuln_por_activo = vulnerabilidades.groupby("Nombre_Activo").size().sort_values(ascending=False)
            
            fig = go.Figure(go.Bar(
                x=vuln_por_activo.index[:15],
                y=vuln_por_activo.values[:15],
                marker_color="#9b59b6"
            ))
            fig.update_layout(
                title="Vulnerabilidades por Activo (Top 15)",
                xaxis_title="Activo",
                yaxis_title="N° Vulnerabilidades",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Degradación promedio por dimensión
            col1, col2, col3 = st.columns(3)
            
            with col1:
                deg_d = vulnerabilidades["Degradacion_D"].mean() if "Degradacion_D" in vulnerabilidades.columns else 0
                st.metric("📊 Degradación D", f"{deg_d:.0f}%")
            with col2:
                deg_i = vulnerabilidades["Degradacion_I"].mean() if "Degradacion_I" in vulnerabilidades.columns else 0
                st.metric("🔐 Degradación I", f"{deg_i:.0f}%")
            with col3:
                deg_c = vulnerabilidades["Degradacion_C"].mean() if "Degradacion_C" in vulnerabilidades.columns else 0
                st.metric("🔒 Degradación C", f"{deg_c:.0f}%")
            
            # Tabla de vulnerabilidades principales
            st.markdown("#### Top Vulnerabilidades por Impacto")
            if "Impacto" in vulnerabilidades.columns:
                top_vuln = vulnerabilidades.sort_values("Impacto", ascending=False).head(10)
                st.dataframe(
                    top_vuln[["Nombre_Activo", "Amenaza", "Vulnerabilidad", "Impacto"]],
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("No hay vulnerabilidades identificadas. Completa el Tab 4.")
    
    # ----- Dashboard: Riesgos -----
    with dash_tab4:
        st.subheader("📊 Panorama de Riesgos")
        
        if not riesgos.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Histograma de distribución de riesgos
                fig = go.Figure(data=[go.Histogram(
                    x=riesgos["Riesgo"],
                    nbinsx=20,
                    marker_color="#3498db"
                )])
                fig.update_layout(
                    title="Distribución de Valores de Riesgo",
                    xaxis_title="Nivel de Riesgo",
                    yaxis_title="Frecuencia",
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Scatter plot Impacto vs Frecuencia
                fig = go.Figure(data=[go.Scatter(
                    x=riesgos["Frecuencia"],
                    y=riesgos["Impacto"],
                    mode="markers",
                    marker=dict(
                        size=10,
                        color=riesgos["Riesgo"],
                        colorscale="RdYlGn_r",
                        showscale=True,
                        colorbar=dict(title="Riesgo")
                    ),
                    text=riesgos["Nombre_Activo"]
                )])
                fig.update_layout(
                    title="Impacto vs Frecuencia",
                    xaxis_title="Frecuencia",
                    yaxis_title="Impacto",
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Tendencia de riesgos (si hay datos temporales)
            st.markdown("#### 📈 Resumen Estadístico")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Máximo", f"{riesgos['Riesgo'].max():.2f}")
            with col2:
                st.metric("Mínimo", f"{riesgos['Riesgo'].min():.2f}")
            with col3:
                st.metric("Promedio", f"{riesgos['Riesgo'].mean():.2f}")
            with col4:
                st.metric("Desv. Estándar", f"{riesgos['Riesgo'].std():.2f}")
        else:
            st.info("No hay riesgos calculados. Completa el Tab 5 (Riesgo).")


# ==================== TAB 10: NIVEL DE MADUREZ ====================

with tab10:
    st.header("🎯 Nivel de Madurez de Ciberseguridad")
    st.markdown("""
    **Propósito:** Calcular el nivel de madurez organizacional basado en CMMI/ISO.
    
    **Niveles de Madurez:**
    - **1 - Inicial**: Procesos ad-hoc, sin controles formales
    - **2 - Básico**: Controles básicos, documentación mínima
    - **3 - Definido**: Procesos documentados, controles estandarizados
    - **4 - Gestionado**: Controles medidos y monitoreados
    - **5 - Optimizado**: Mejora continua, controles automatizados
    """)
    
    # Botón para calcular
    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        if st.button("🔄 Calcular Nivel de Madurez", type="primary"):
            with st.spinner("Calculando nivel de madurez..."):
                resultado = calcular_madurez_evaluacion(ID_EVALUACION)
                if resultado:
                    guardar_madurez(resultado)
                    st.success("✅ Nivel de madurez calculado y guardado")
                    st.rerun()
                else:
                    st.error("❌ Error al calcular. Asegúrate de tener activos y respuestas.")
    
    # Obtener madurez guardada
    madurez = get_madurez_evaluacion(ID_EVALUACION)
    
    if madurez:
        st.markdown("---")
        
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
            
            st.markdown(f"""
            <div style="text-align: center; padding: 2rem; border: 4px solid {color}; border-radius: 20px; background: linear-gradient(135deg, {color}22, {color}11);">
                <h1 style="color: {color}; margin: 0; font-size: 4rem;">Nivel {nivel}</h1>
                <h2 style="color: {color}; margin: 0.5rem 0;">{nombre}</h2>
                <p style="font-size: 1.5rem; color: #666;">Puntuación: <strong>{puntuacion:.1f}/100</strong></p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ===== MÉTRICAS POR DOMINIO =====
        st.subheader("📊 Madurez por Dominio ISO 27002")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            org = madurez.get("Dominio_Organizacional", 0)
            st.metric("🏢 Organizacional", f"{org:.0f}%")
            st.progress(org / 100)
        with col2:
            per = madurez.get("Dominio_Personas", 0)
            st.metric("👥 Personas", f"{per:.0f}%")
            st.progress(per / 100)
        with col3:
            fis = madurez.get("Dominio_Fisico", 0)
            st.metric("🏗️ Físico", f"{fis:.0f}%")
            st.progress(fis / 100)
        with col4:
            tec = madurez.get("Dominio_Tecnologico", 0)
            st.metric("💻 Tecnológico", f"{tec:.0f}%")
            st.progress(tec / 100)
        
        # Gráfico radar de dominios
        categorias = ["Organizacional", "Personas", "Físico", "Tecnológico"]
        valores = [org, per, fis, tec]
        valores_cerrado = valores + [valores[0]]
        categorias_cerrado = categorias + [categorias[0]]
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=valores_cerrado,
            theta=categorias_cerrado,
            fill="toself",
            fillcolor="rgba(52, 152, 219, 0.3)",
            line=dict(color="#3498db", width=2),
            name="Madurez Actual"
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            height=400,
            title="Radar de Madurez por Dominio"
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        
        st.markdown("---")
        
        # ===== MÉTRICAS DETALLADAS =====
        st.subheader("📈 Métricas Detalladas")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📋 Controles Impl.", madurez.get("Controles_Implementados", 0))
        with col2:
            st.metric("⚠️ Controles Parciales", madurez.get("Controles_Parciales", 0))
        with col3:
            st.metric("❌ Sin Implementar", madurez.get("Controles_No_Implementados", 0))
        with col4:
            st.metric("📊 % Activos Evaluados", f"{madurez.get('Pct_Activos_Evaluados', 0):.0f}%")
        
        # ===== TABLA DE NIVELES =====
        st.markdown("---")
        st.subheader("📋 Tabla de Identificación de Niveles")
        
        niveles_tabla = [
            {"Nivel": 1, "Nombre": "Inicial", "Puntuación": "0-19", "Descripción": "Procesos ad-hoc, sin controles formales, respuesta reactiva"},
            {"Nivel": 2, "Nombre": "Básico", "Puntuación": "20-39", "Descripción": "Controles básicos implementados, documentación mínima"},
            {"Nivel": 3, "Nombre": "Definido", "Puntuación": "40-59", "Descripción": "Procesos documentados, controles estandarizados"},
            {"Nivel": 4, "Nombre": "Gestionado", "Puntuación": "60-79", "Descripción": "Controles medidos y monitoreados, métricas definidas"},
            {"Nivel": 5, "Nombre": "Optimizado", "Puntuación": "80-100", "Descripción": "Mejora continua, controles automatizados, proactivo"},
        ]
        
        df_niveles = pd.DataFrame(niveles_tabla)
        
        # Destacar nivel actual
        def highlight_nivel(row):
            if row["Nivel"] == nivel:
                return ["background-color: #3498db; color: white"] * len(row)
            return [""] * len(row)
        
        st.dataframe(
            df_niveles.style.apply(highlight_nivel, axis=1),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("📭 No hay datos de madurez. Haz clic en 'Calcular Nivel de Madurez' para generar el análisis.")


# ==================== TAB 11: COMPARATIVA / REEVALUACIÓN ====================

with tab11:
    st.header("🔄 Comparativa entre Evaluaciones")
    st.markdown("""
    **Propósito:** Comparar el estado actual con una evaluación anterior para medir el progreso.
    """)
    
    # Obtener todas las evaluaciones
    todas_evaluaciones = get_evaluaciones()
    
    if len(todas_evaluaciones) < 2:
        st.warning("⚠️ Necesitas al menos 2 evaluaciones para hacer comparativas.")
        st.info("Crea una nueva evaluación desde la barra lateral para tener datos comparables.")
        st.stop()
    
    # Selectores de evaluaciones
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Evaluación Anterior")
        eval_1 = st.selectbox(
            "Seleccionar evaluación base",
            [e["id_evaluacion"] for e in todas_evaluaciones],
            format_func=lambda x: next((e["nombre"] for e in todas_evaluaciones if e["id_evaluacion"] == x), x),
            key="comp_eval_1"
        )
    
    with col2:
        st.subheader("📅 Evaluación Actual")
        otras_evals = [e["id_evaluacion"] for e in todas_evaluaciones if e["id_evaluacion"] != eval_1]
        if otras_evals:
            eval_2 = st.selectbox(
                "Seleccionar evaluación a comparar",
                otras_evals,
                format_func=lambda x: next((e["nombre"] for e in todas_evaluaciones if e["id_evaluacion"] == x), x),
                index=len(otras_evals) - 1 if otras_evals else 0,
                key="comp_eval_2"
            )
        else:
            st.warning("Selecciona una evaluación diferente")
            st.stop()
    
    if st.button("🔄 Comparar Evaluaciones", type="primary"):
        with st.spinner("Comparando evaluaciones..."):
            comparativa = comparar_madurez(eval_1, eval_2)
            
            if comparativa:
                st.session_state.comparativa_resultado = comparativa
                st.success("✅ Comparativa generada")
            else:
                st.error("❌ No se pudo generar la comparativa. Asegúrate de que ambas evaluaciones tengan datos.")
    
    # Mostrar resultados
    if "comparativa_resultado" in st.session_state:
        comp = st.session_state.comparativa_resultado
        
        st.markdown("---")
        st.markdown(f"### 📊 Resultado: {comp.get('mensaje_resumen', '')}")
        
        # Métricas de cambio
        col1, col2, col3 = st.columns(3)
        
        with col1:
            delta_punt = comp.get("delta_puntuacion", 0)
            color = "normal" if delta_punt >= 0 else "inverse"
            st.metric(
                "Δ Puntuación",
                f"{comp['madurez_2']['puntuacion_total']:.1f}",
                delta=f"{delta_punt:+.1f}",
                delta_color=color
            )
        
        with col2:
            delta_nivel = comp.get("delta_nivel", 0)
            color = "normal" if delta_nivel >= 0 else "inverse"
            st.metric(
                "Δ Nivel Madurez",
                comp['madurez_2']['nivel_madurez'],
                delta=f"{delta_nivel:+d}",
                delta_color=color
            )
        
        with col3:
            delta_riesgo = comp.get("delta_riesgo_residual", 0)
            color = "inverse" if delta_riesgo <= 0 else "normal"  # Menos riesgo es mejor
            st.metric(
                "Δ Riesgo Residual",
                f"{delta_riesgo:+.2f}",
                delta="Reducción" if delta_riesgo < 0 else "Incremento",
                delta_color=color
            )
        
        st.markdown("---")
        
        # Gráfico comparativo de dominios
        st.subheader("📊 Comparativa por Dominio")
        
        dominios = ["Organizacional", "Personas", "Físico", "Tecnológico"]
        madurez_1 = comp["madurez_1"]
        madurez_2 = comp["madurez_2"]
        
        valores_1 = [
            madurez_1["dominio_organizacional"],
            madurez_1["dominio_personas"],
            madurez_1["dominio_fisico"],
            madurez_1["dominio_tecnologico"]
        ]
        valores_2 = [
            madurez_2["dominio_organizacional"],
            madurez_2["dominio_personas"],
            madurez_2["dominio_fisico"],
            madurez_2["dominio_tecnologico"]
        ]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Evaluación Anterior", x=dominios, y=valores_1, marker_color="#95a5a6"))
        fig.add_trace(go.Bar(name="Evaluación Actual", x=dominios, y=valores_2, marker_color="#3498db"))
        fig.update_layout(
            barmode="group",
            title="Madurez por Dominio: Antes vs Después",
            yaxis_title="Porcentaje (%)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Mejoras y retrocesos
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✅ Mejoras")
            if comp.get("mejoras"):
                for mejora in comp["mejoras"]:
                    st.success(mejora)
            else:
                st.info("Sin mejoras significativas detectadas")
        
        with col2:
            st.subheader("⚠️ Áreas de Atención")
            if comp.get("retrocesos"):
                for retroceso in comp["retrocesos"]:
                    st.warning(retroceso)
            else:
                st.info("Sin retrocesos detectados")
        
        # Recomendaciones
        st.markdown("---")
        st.subheader("💡 Recomendaciones")
        if comp.get("recomendaciones"):
            for rec in comp["recomendaciones"]:
                st.info(f"📌 {rec}")


# ==================== TAB 12: MATRIZ EXCEL COMPLETA ====================

with tab12:
    st.header("📑 Matriz Excel Completa")
    st.markdown("""
    **Propósito:** Visualización interactiva de toda la matriz y descarga en formato Excel.
    """)
    
    # ===== BOTÓN DE DESCARGA PRINCIPAL =====
    st.markdown("### 📥 Descargar Matriz Completa")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("📊 Generar Excel", type="primary"):
            with st.spinner("Generando archivo Excel..."):
                excel_bytes = exportar_matriz_excel(ID_EVALUACION, NOMBRE_EVALUACION)
                st.download_button(
                    "💾 Descargar Excel",
                    data=excel_bytes,
                    file_name=f"Matriz_MAGERIT_{NOMBRE_EVALUACION}_{dt.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    with col2:
        st.caption("El archivo Excel incluye todas las hojas: Criterios, Activos, Valoración, Vulnerabilidades, Riesgos, Mapa, Salvaguardas.")
    
    st.markdown("---")
    
    # ===== VISUALIZACIÓN INTERACTIVA =====
    st.markdown("### 📋 Vista Previa de la Matriz")
    
    # Sub-tabs para cada hoja
    hoja1, hoja2, hoja3, hoja4, hoja5, hoja6 = st.tabs([
        "📦 Activos",
        "⚖️ Valoración",
        "🔓 Vulnerabilidades",
        "⚡ Riesgos",
        "📊 Riesgos Activos",
        "🛡️ Salvaguardas"
    ])
    
    with hoja1:
        activos = get_activos_matriz(ID_EVALUACION)
        if not activos.empty:
            st.dataframe(activos, use_container_width=True, height=400)
            st.download_button(
                "📥 Descargar Activos (CSV)",
                data=activos.to_csv(index=False, encoding='utf-8-sig'),
                file_name="activos.csv"
            )
        else:
            st.info("No hay activos registrados.")
    
    with hoja2:
        valoraciones = get_valoraciones_evaluacion(ID_EVALUACION)
        if not valoraciones.empty:
            st.dataframe(valoraciones, use_container_width=True, height=400)
            st.download_button(
                "📥 Descargar Valoraciones (CSV)",
                data=valoraciones.to_csv(index=False, encoding='utf-8-sig'),
                file_name="valoraciones.csv"
            )
        else:
            st.info("No hay valoraciones registradas.")
    
    with hoja3:
        vulns = get_vulnerabilidades_evaluacion(ID_EVALUACION)
        if not vulns.empty:
            st.dataframe(vulns, use_container_width=True, height=400)
            st.download_button(
                "📥 Descargar Vulnerabilidades (CSV)",
                data=vulns.to_csv(index=False, encoding='utf-8-sig'),
                file_name="vulnerabilidades.csv"
            )
        else:
            st.info("No hay vulnerabilidades registradas.")
    
    with hoja4:
        riesgos = get_riesgos_evaluacion(ID_EVALUACION)
        if not riesgos.empty:
            st.dataframe(riesgos, use_container_width=True, height=400)
            st.download_button(
                "📥 Descargar Riesgos (CSV)",
                data=riesgos.to_csv(index=False, encoding='utf-8-sig'),
                file_name="riesgos.csv"
            )
        else:
            st.info("No hay riesgos calculados.")
    
    with hoja5:
        riesgos_act = get_riesgos_activos_evaluacion(ID_EVALUACION)
        if not riesgos_act.empty:
            st.dataframe(riesgos_act, use_container_width=True, height=400)
            st.download_button(
                "📥 Descargar Riesgos por Activo (CSV)",
                data=riesgos_act.to_csv(index=False, encoding='utf-8-sig'),
                file_name="riesgos_activos.csv"
            )
        else:
            st.info("No hay riesgos agregados por activo.")
    
    with hoja6:
        salvs = get_salvaguardas_evaluacion(ID_EVALUACION)
        if not salvs.empty:
            st.dataframe(salvs, use_container_width=True, height=400)
            st.download_button(
                "📥 Descargar Salvaguardas (CSV)",
                data=salvs.to_csv(index=False, encoding='utf-8-sig'),
                file_name="salvaguardas.csv"
            )
        else:
            st.info("No hay salvaguardas registradas.")
    
    st.markdown("---")
    
    # ===== DATOS PARA POWER BI =====
    st.markdown("### 📊 Exportar para Power BI")
    st.caption("Exporta los datos en formato optimizado para importar en Power BI.")
    
    if st.button("📤 Generar Dataset para Power BI"):
        # Crear un Excel con formato plano para Power BI
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja de hechos (fact table)
            riesgos = get_riesgos_evaluacion(ID_EVALUACION)
            if not riesgos.empty:
                riesgos["Fecha_Evaluacion"] = dt.date.today().isoformat()
                riesgos["ID_Evaluacion"] = ID_EVALUACION
                riesgos["Nombre_Evaluacion"] = NOMBRE_EVALUACION
                riesgos.to_excel(writer, sheet_name="FACT_RIESGOS", index=False)
            
            # Dimensión activos
            activos = get_activos_matriz(ID_EVALUACION)
            if not activos.empty:
                activos.to_excel(writer, sheet_name="DIM_ACTIVOS", index=False)
            
            # Dimensión madurez
            madurez = get_madurez_evaluacion(ID_EVALUACION)
            if madurez:
                pd.DataFrame([madurez]).to_excel(writer, sheet_name="DIM_MADUREZ", index=False)
        
        output.seek(0)
        st.download_button(
            "💾 Descargar Dataset Power BI",
            data=output.getvalue(),
            file_name=f"PowerBI_Dataset_{NOMBRE_EVALUACION}_{dt.date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# ==================== TAB 13: RESUMEN EJECUTIVO ====================

with tab13:
    st.header("📋 Resumen Ejecutivo")
    st.markdown("""
    **Propósito:** Informe ejecutivo generado por IA para presentar a la alta gerencia.
    
    Incluye:
    - Hallazgos principales
    - Activos más críticos
    - Recomendaciones prioritarias
    - Inversión estimada
    - Reducción de riesgo esperada
    """)
    
    # Botón para generar
    col1, col2 = st.columns([1, 2])
    with col1:
        generar = st.button("🤖 Generar Resumen con IA", type="primary")
    with col2:
        modelo_ia = st.selectbox(
            "Modelo IA",
            ["llama3.2:1b", "llama3.2:3b", "llama3:8b"],
            index=0,
            help="Modelos más grandes generan mejores resúmenes pero son más lentos"
        )
    
    if generar:
        with st.spinner("🔄 Generando resumen ejecutivo con IA... (puede tomar 30-60 segundos)"):
            exito, resumen, mensaje = generar_resumen_ejecutivo(ID_EVALUACION, modelo_ia)
            
            if exito and resumen:
                st.session_state.resumen_ejecutivo = resumen
                st.success(mensaje)
            else:
                st.error(f"Error: {mensaje}")
    
    # Mostrar resumen si existe
    if "resumen_ejecutivo" in st.session_state:
        resumen = st.session_state.resumen_ejecutivo
        
        st.markdown("---")
        
        # Encabezado
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 2rem; border-radius: 10px; color: white; margin-bottom: 1rem;">
            <h2 style="margin: 0;">📊 Resumen Ejecutivo - Evaluación de Riesgos</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.8;">Evaluación: {NOMBRE_EVALUACION} | Fecha: {resumen.fecha_generacion}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📦 Activos Evaluados", resumen.total_activos)
        with col2:
            st.metric("⚠️ Amenazas Identificadas", resumen.total_amenazas)
        with col3:
            st.metric("💰 Inversión Estimada", resumen.inversion_estimada)
        with col4:
            st.metric("📉 Reducción Esperada", resumen.reduccion_riesgo_esperada)
        
        st.markdown("---")
        
        # Hallazgos principales
        st.subheader("🔍 Hallazgos Principales")
        for i, hallazgo in enumerate(resumen.hallazgos_principales, 1):
            st.markdown(f"**{i}.** {hallazgo}")
        
        st.markdown("---")
        
        # Activos críticos
        st.subheader("🔥 Activos Más Críticos")
        if resumen.activos_criticos:
            tabla_criticos = pd.DataFrame(resumen.activos_criticos)
            st.dataframe(tabla_criticos, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Distribución de riesgos
        if resumen.distribucion_riesgo:
            st.subheader("📊 Distribución de Riesgos")
            dist = resumen.distribucion_riesgo
            
            # Gráfico de pastel
            fig = go.Figure(data=[go.Pie(
                labels=list(dist.keys()),
                values=list(dist.values()),
                marker_colors=["#ff0000", "#ff8800", "#ffdd00", "#00C851"],
                hole=0.4
            )])
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Recomendaciones
        st.subheader("💡 Recomendaciones Prioritarias")
        for i, rec in enumerate(resumen.recomendaciones_prioritarias, 1):
            st.info(f"**{i}.** {rec}")
        
        st.markdown("---")
        
        # Conclusión
        st.subheader("📝 Conclusión")
        st.markdown(f"> {resumen.conclusion}")
        
        st.markdown("---")
        
        # Descarga del informe
        st.subheader("📥 Descargar Informe")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Generar texto del informe
            informe_texto = f"""
RESUMEN EJECUTIVO - EVALUACIÓN DE RIESGOS MAGERIT
=================================================
Evaluación: {NOMBRE_EVALUACION}
Fecha: {resumen.fecha_generacion}
Generado por: TITA - Sistema de Gestión de Riesgos

MÉTRICAS PRINCIPALES
--------------------
- Activos Evaluados: {resumen.total_activos}
- Amenazas Identificadas: {resumen.total_amenazas}
- Inversión Estimada: {resumen.inversion_estimada}
- Reducción de Riesgo Esperada: {resumen.reduccion_riesgo_esperada}

HALLAZGOS PRINCIPALES
---------------------
"""
            for i, h in enumerate(resumen.hallazgos_principales, 1):
                informe_texto += f"{i}. {h}\n"
            
            informe_texto += "\nRECOMENDACIONES PRIORITARIAS\n----------------------------\n"
            for i, r in enumerate(resumen.recomendaciones_prioritarias, 1):
                informe_texto += f"{i}. {r}\n"
            
            informe_texto += f"\nCONCLUSIÓN\n----------\n{resumen.conclusion}\n"
            
            st.download_button(
                "📄 Descargar Informe (TXT)",
                data=informe_texto,
                file_name=f"Resumen_Ejecutivo_{NOMBRE_EVALUACION}.txt",
                mime="text/plain"
            )
        
        with col2:
            # JSON para Power BI
            informe_json = {
                "evaluacion": NOMBRE_EVALUACION,
                "fecha": resumen.fecha_generacion,
                "metricas": {
                    "activos": resumen.total_activos,
                    "amenazas": resumen.total_amenazas,
                    "inversion": resumen.inversion_estimada,
                    "reduccion_riesgo": resumen.reduccion_riesgo_esperada
                },
                "hallazgos": resumen.hallazgos_principales,
                "activos_criticos": resumen.activos_criticos,
                "recomendaciones": resumen.recomendaciones_prioritarias,
                "conclusion": resumen.conclusion,
                "distribucion_riesgo": resumen.distribucion_riesgo
            }
            
            st.download_button(
                "📊 Descargar JSON (Power BI)",
                data=json.dumps(informe_json, indent=2, ensure_ascii=False),
                file_name=f"Resumen_Ejecutivo_{NOMBRE_EVALUACION}.json",
                mime="application/json"
            )
    else:
        st.info("📭 Haz clic en 'Generar Resumen con IA' para crear el informe ejecutivo.")


# ==================== FOOTER ====================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <strong>TITA - Matriz de Riesgos MAGERIT</strong><br>
    Sistema de Evaluación de Riesgos basado en MAGERIT v3<br>
    <em>Versión: Matriz de Referencia</em>
</div>
""", unsafe_allow_html=True)
