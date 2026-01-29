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
    "🎯 9. Madurez",
    "📈 10. Dashboards (Standby)",
    "🔄 11. Comparativa (Standby)",
    "📑 12. Matriz Excel",
    "📋 13. Resumen (Standby)"
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
        "⚠️ Amenazas MAGERIT",
        "🛡️ Controles ISO 27002",
        "🔒 Salvaguardas",
        "🔓 Vulnerabilidades"
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
    
    # Métricas
    col1, col2, col3 = st.columns(3)
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
    
    # Tabla de activos
    if not activos.empty:
        st.subheader("📋 Lista de Activos")
        
        # Columnas a mostrar (sin criticidad - eso se calcula en Tab 3)
        columnas_mostrar = [
            "Nombre_Activo", "Tipo_Activo", "Ubicacion", 
            "Area_Responsable", "Finalidad_Uso", "Estado"
        ]
        columnas_existentes = [c for c in columnas_mostrar if c in activos.columns]
        
        df_display = activos[columnas_existentes].copy()
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
                        
                        if impacto >= 2.0:
                            st.error(f"Impacto: **{impacto:.2f}** (Alto)")
                        elif impacto >= 1.0:
                            st.warning(f"Impacto: **{impacto:.2f}** (Medio)")
                        elif impacto >= 0.5:
                            st.info(f"Impacto: **{impacto:.2f}** (Bajo)")
                        else:
                            st.success(f"Impacto: **{impacto:.2f}** (Nulo)")
                    
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
        
        # Mostrar mensaje si hay vulnerabilidades del activo actual
        vulns = get_vulnerabilidades_activo(ID_EVALUACION, activo_sel)
        
        if not vulns.empty:
            st.success(f"✅ **{activo_info['Nombre_Activo']}** tiene {len(vulns)} vulnerabilidades/amenazas registradas. Ver tabla unificada abajo.")
        else:
            st.info("📭 No hay vulnerabilidades/amenazas registradas para este activo. Usa el botón 'Analizar con IA' para identificar automáticamente.")
    
    st.markdown("---")
    
    # ===== TABLA UNIFICADA DE VULNERABILIDADES/AMENAZAS =====
    st.subheader("📋 Registro de Vulnerabilidades y Amenazas")
    st.caption("💡 Pasa el mouse sobre Amenaza o Vulnerabilidad para ver la descripción completa")
    
    todas_vulns = get_vulnerabilidades_evaluacion(ID_EVALUACION)
    
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
            
            # Generar código de vulnerabilidad basado en índice
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
    
    if todas_vulns.empty:
        st.warning("⚠️ No hay vulnerabilidades/amenazas identificadas. Ve a la pestaña 'Vulnerabilidades y Amenazas' primero.")
        st.stop()
    
    st.markdown("---")
    
    # ===== CALCULAR RIESGOS PARA TODOS LOS ACTIVOS =====
    st.subheader("🔄 Calcular Riesgos")
    
    col_calc1, col_calc2 = st.columns([1, 2])
    with col_calc1:
        if st.button("⚡ Calcular Todos los Riesgos", type="primary", key="calc_all_risks"):
            total_guardados = 0
            for _, activo in activos.iterrows():
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
            st.success(f"✅ Se calcularon y guardaron {total_guardados} riesgos")
            st.rerun()
    
    with col_calc2:
        st.caption("Calcula automáticamente la frecuencia basándose en criticidad, RTO y BIA de cada activo.")
    
    st.markdown("---")
    
    # ===== TABLA UNIFICADA DE RIESGOS =====
    st.subheader("📋 Resumen de Riesgos")
    st.caption("💡 Pasa el mouse sobre la Amenaza para ver la descripción completa")
    
    riesgos = get_riesgos_evaluacion(ID_EVALUACION)
    
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
    
    # ===== GRÁFICO RADAR DE RIESGO POR ACTIVO =====
    st.markdown("### 🕸️ Mapa Radar de Riesgo por Activo")
    st.caption("Compara el riesgo ACTUAL vs OBJETIVO vs LÍMITE para cada activo")
    
    # Debug: mostrar columnas disponibles
    # st.write("Columnas disponibles:", riesgos.columns.tolist())
    
    # Identificar la columna de nombre del activo
    col_nombre = None
    for posible in ["Nombre_Activo", "nombre_activo", "Activo", "activo", "ID_Activo", "id_activo"]:
        if posible in riesgos.columns:
            col_nombre = posible
            break
    
    if col_nombre is None:
        st.warning("⚠️ No se encontró columna de nombre de activo en los datos de riesgo.")
        st.write("Columnas disponibles:", riesgos.columns.tolist())
    elif len(riesgos) >= 3:
        # Agrupar riesgos por activo (tomar el máximo riesgo por activo)
        riesgos_por_activo = riesgos.groupby(col_nombre).agg({
            "Riesgo": "max"
        }).reset_index()
        
        # Limitar a los primeros 10 activos con mayor riesgo para el radar
        top_activos = riesgos_por_activo.nlargest(min(10, len(riesgos_por_activo)), "Riesgo")
        
        if len(top_activos) >= 3:
            # Preparar datos para el radar
            activos_nombres = top_activos[col_nombre].tolist()
            riesgo_actual = top_activos["Riesgo"].tolist()
            
            # Acortar nombres largos para el radar
            activos_nombres_cortos = [n[:25] + "..." if len(str(n)) > 25 else str(n) for n in activos_nombres]
            
            # Calcular objetivo (50% del actual, mínimo 1)
            riesgo_objetivo = [max(1.0, r * 0.5) for r in riesgo_actual]
            
            # Límite de tolerancia (por ejemplo, 7 para todos o basado en criticidad)
            riesgo_limite = [7.0] * len(activos_nombres_cortos)
            
            # Cerrar el polígono (repetir el primer valor al final)
            activos_nombres_closed = activos_nombres_cortos + [activos_nombres_cortos[0]]
            riesgo_actual_closed = riesgo_actual + [riesgo_actual[0]]
            riesgo_objetivo_closed = riesgo_objetivo + [riesgo_objetivo[0]]
            riesgo_limite_closed = riesgo_limite + [riesgo_limite[0]]
            
            # Crear gráfico radar
            fig_radar = go.Figure()
        
            # Línea ACTUAL (verde)
            fig_radar.add_trace(go.Scatterpolar(
                r=riesgo_actual_closed,
                theta=activos_nombres_closed,
                fill='toself',
                fillcolor='rgba(76, 175, 80, 0.3)',
                line=dict(color='#4CAF50', width=2),
                marker=dict(size=8, color='#4CAF50'),
                name='ACTUAL'
            ))
            
            # Línea OBJETIVO (azul)
            fig_radar.add_trace(go.Scatterpolar(
                r=riesgo_objetivo_closed,
                theta=activos_nombres_closed,
                fill='toself',
                fillcolor='rgba(33, 150, 243, 0.2)',
                line=dict(color='#2196F3', width=2),
                marker=dict(size=8, color='#2196F3'),
                name='OBJETIVO'
            ))
            
            # Línea LÍMITE (amarillo/naranja)
            fig_radar.add_trace(go.Scatterpolar(
                r=riesgo_limite_closed,
                theta=activos_nombres_closed,
                fill='none',
                line=dict(color='#FFC107', width=3),
                marker=dict(size=6, color='#FFC107'),
                name='LÍMITE'
            ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 8],
                        tickvals=[1, 2, 3, 4, 5, 6, 7],
                        tickfont=dict(size=10)
                    ),
                    angularaxis=dict(
                        tickfont=dict(size=11)
                    )
                ),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.05,
                    xanchor="center",
                    x=0.5
                ),
                title=dict(
                    text="RIESGO POR ACTIVO",
                    font=dict(size=16),
                    x=0.5
                ),
                height=500
            )
            
            st.plotly_chart(fig_radar, use_container_width=True)
            
            # Tabla resumen del radar
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown("**📊 Leyenda del Radar:**")
                st.markdown("- 🟢 **ACTUAL**: Nivel de riesgo calculado actualmente")
                st.markdown("- 🔵 **OBJETIVO**: Meta de reducción (50% del actual)")
                st.markdown("- 🟡 **LÍMITE**: Tolerancia máxima aceptable (7)")
            
            with col_r2:
                st.markdown("**📋 Activos en el Radar:**")
                for i, (activo, riesgo) in enumerate(zip(activos_nombres_cortos, riesgo_actual)):
                    zona = "🔴" if riesgo >= 6 else "🟠" if riesgo >= 4 else "🟡" if riesgo >= 2 else "🟢"
                    st.markdown(f"{zona} {activo}: **{riesgo:.2f}**")
        else:
            st.info("Se necesitan al menos 3 activos únicos con riesgos para mostrar el radar.")
    
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
    
    # Cargar catálogos para tooltips
    catalogo_amenazas = get_catalogo_amenazas()
    catalogo_controles = get_catalogo_controles()
    
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
        
        # Generar código de vulnerabilidad
        cod_vuln = f"V{idx+1:03d}"
        
        # Extraer código de control ISO (solo el código, ej: "5.1")
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
            # Guardar datos completos para tooltip/referencia
            "_vuln_full": str(row.get("Vulnerabilidad", "")),
            "_control_full": control_iso_full,
            "_amenaza_full": row.get("Amenaza", "")
        })
    
    df_salvaguardas = pd.DataFrame(df_display_salv)
    
    # Mostrar tabla
    st.dataframe(
        df_salvaguardas[["Activo", "Amenaza", "Cod_Vuln", "Riesgo", "Salvaguarda", "Control_ISO", "Prioridad", "IA"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Activo": st.column_config.TextColumn("Activo", width="medium"),
            "Amenaza": st.column_config.TextColumn("Cod_Amenaza", width="small"),
            "Cod_Vuln": st.column_config.TextColumn("Cod_Vuln", width="small"),
            "Riesgo": st.column_config.TextColumn("Riesgo", width="small"),
            "Salvaguarda": st.column_config.TextColumn("Salvaguarda Sugerida", width="large"),
            "Control_ISO": st.column_config.TextColumn("Control ISO", width="small"),
            "Prioridad": st.column_config.TextColumn("Prioridad", width="small"),
            "IA": st.column_config.TextColumn("IA", width="small")
        }
    )
    
    st.caption("✅ = Generado por IA | 🔧 = Generado heurísticamente | 💡 Códigos de vulnerabilidad (V001, V002...) y controles ISO (5.1, 8.2...) para referencia rápida")
    
    # Tabla de referencia expandible con tooltips
    with st.expander("📋 Ver Detalles Completos de Vulnerabilidades y Controles"):
        st.markdown("**Códigos de Vulnerabilidad:**")
        for idx, row_data in enumerate(df_display_salv):
            st.markdown(f"- **{row_data['Cod_Vuln']}**: {row_data['_vuln_full']}")
        
        st.markdown("---")
        st.markdown("**Códigos de Amenazas:**")
        amenazas_unicas = {}
        for row_data in df_display_salv:
            cod = row_data['Amenaza']
            if cod and cod not in amenazas_unicas:
                amenazas_unicas[cod] = row_data['_amenaza_full']
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
    
    # Botón de descarga
    st.download_button(
        label="📥 Descargar Tabla de Salvaguardas (CSV)",
        data=df_download_salv.to_csv(index=False, encoding='utf-8-sig'),
        file_name="salvaguardas_sugeridas.csv",
        mime="text/csv"
    )


# ==================== TAB 10: DASHBOARDS (STANDBY) ====================

with tab10:
    st.header("📈 Dashboards Ejecutivos")
    st.info("""
    🚧 **Módulo en Standby**
    
    Este módulo está temporalmente deshabilitado mientras se completan las mejoras en otros tabs.
    
    **Funcionalidades planificadas:**
    - Visualizaciones ejecutivas de activos críticos
    - Análisis de amenazas y vulnerabilidades
    - Distribución de riesgos
    - Resúmenes estadísticos
    
    ⏳ *Disponible próximamente...*
    """)


# ==================== TAB 9: NIVEL DE MADUREZ ====================

with tab9:
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


# ==================== TAB 11: COMPARATIVA (STANDBY) ====================

with tab11:
    st.header("🔄 Comparativa entre Evaluaciones")
    st.info("""
    🚧 **Módulo en Standby**
    
    Este módulo está temporalmente deshabilitado mientras se completan las mejoras en otros tabs.
    
    **Funcionalidades planificadas:**
    - Comparación entre evaluaciones
    - Análisis de progreso en el tiempo
    - Detección de mejoras y retrocesos
    - Recomendaciones basadas en tendencias
    
    ⏳ *Disponible próximamente...*
    """)


# ==================== TAB 12: MATRIZ EXCEL (STANDBY) ====================

with tab12:
    st.header("📑 Matriz Excel Completa")
    st.info("""
    🚧 **Módulo en Standby**
    
    Este módulo está temporalmente deshabilitado mientras se completan las mejoras en otros tabs.
    
    **Funcionalidades planificadas:**
    - Visualización unificada de todas las tablas
    - Descarga en formato Excel completo
    - Exportación para Power BI
    - Resumen de métricas
    
    ⏳ *Disponible próximamente...*
    """)


# ==================== TAB 13: RESUMEN EJECUTIVO (STANDBY) ====================

with tab13:
    st.header("📋 Resumen Ejecutivo")
    st.info("""
    🚧 **Módulo en Standby**
    
    Este módulo está temporalmente deshabilitado mientras se completan las mejoras en otros tabs.
    
    **Funcionalidades planificadas:**
    - Informe ejecutivo para alta gerencia
    - Hallazgos principales automatizados
    - Activos más críticos
    - Recomendaciones prioritarias
    - Distribución de riesgos con gráficos
    - Exportación a PDF/Word
    
    ⏳ *Disponible próximamente...*
    """)


# ==================== FOOTER ====================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <strong>TITA - Matriz de Riesgos MAGERIT</strong><br>
    Sistema de Evaluación de Riesgos basado en MAGERIT v3<br>
    <em>Versión: Matriz de Referencia</em>
</div>
""", unsafe_allow_html=True)
