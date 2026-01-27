"""
DASHBOARD DE EVALUACIÓN MAGERIT
================================
Componentes visuales para:
- Mapa de calor de riesgos (5x5)
- Ranking de activos por riesgo
- Comparativo inherente vs residual
- Distribución de amenazas
- Cobertura de controles
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import json


# ==================== COLORES ====================

COLORES_RIESGO = {
    "CRÍTICO": "#DC143C",    # Crimson
    "ALTO": "#FF6347",       # Tomato
    "MEDIO": "#FFA500",      # Orange
    "BAJO": "#90EE90",       # Light Green
    "MUY BAJO": "#32CD32"    # Lime Green
}

COLORES_MATRIZ = [
    ["#32CD32", "#90EE90", "#FFA500", "#FF6347", "#DC143C"],
    ["#32CD32", "#90EE90", "#FFA500", "#FF6347", "#DC143C"],
    ["#90EE90", "#FFA500", "#FFA500", "#FF6347", "#DC143C"],
    ["#90EE90", "#FFA500", "#FF6347", "#DC143C", "#DC143C"],
    ["#FFA500", "#FF6347", "#FF6347", "#DC143C", "#DC143C"]
]


# ==================== MAPA DE CALOR 5x5 ====================

def render_mapa_calor_riesgos(amenazas: pd.DataFrame, titulo: str = "Matriz de Riesgos 5×5"):
    """
    Renderiza mapa de calor de riesgos con amenazas posicionadas.
    
    Args:
        amenazas: DataFrame con columnas probabilidad, impacto, codigo_amenaza
        titulo: Título del gráfico
    """
    st.subheader(f"🔥 {titulo}")
    
    # Matriz base de niveles
    niveles_texto = [
        ["MUY BAJO\n(1)", "BAJO\n(2)", "MEDIO\n(3)", "MEDIO\n(4)", "ALTO\n(5)"],
        ["MUY BAJO\n(2)", "BAJO\n(4)", "MEDIO\n(6)", "ALTO\n(8)", "ALTO\n(10)"],
        ["BAJO\n(3)", "MEDIO\n(6)", "MEDIO\n(9)", "ALTO\n(12)", "CRÍTICO\n(15)"],
        ["BAJO\n(4)", "MEDIO\n(8)", "ALTO\n(12)", "CRÍTICO\n(16)", "CRÍTICO\n(20)"],
        ["MEDIO\n(5)", "ALTO\n(10)", "ALTO\n(15)", "CRÍTICO\n(20)", "CRÍTICO\n(25)"]
    ]
    
    # Crear matriz de valores para el heatmap
    valores = np.array([
        [1, 2, 3, 4, 5],
        [2, 4, 6, 8, 10],
        [3, 6, 9, 12, 15],
        [4, 8, 12, 16, 20],
        [5, 10, 15, 20, 25]
    ])
    
    # Crear figura
    fig = go.Figure()
    
    # Añadir heatmap base
    fig.add_trace(go.Heatmap(
        z=valores,
        colorscale=[
            [0, "#32CD32"],
            [0.2, "#90EE90"],
            [0.4, "#FFA500"],
            [0.7, "#FF6347"],
            [1, "#DC143C"]
        ],
        showscale=True,
        colorbar=dict(
            title="Riesgo",
            tickvals=[1, 6, 12, 20, 25],
            ticktext=["MUY BAJO", "BAJO", "MEDIO", "ALTO", "CRÍTICO"]
        )
    ))
    
    # Añadir anotaciones de niveles
    for i in range(5):
        for j in range(5):
            fig.add_annotation(
                x=j, y=i,
                text=niveles_texto[i][j],
                showarrow=False,
                font=dict(size=10, color="black")
            )
    
    # Añadir puntos de amenazas
    if not amenazas.empty:
        for _, row in amenazas.iterrows():
            prob = int(row.get("probabilidad", 1)) - 1
            imp = int(row.get("impacto", 1)) - 1
            codigo = row.get("codigo_amenaza", "?")
            
            # Añadir marcador
            fig.add_trace(go.Scatter(
                x=[imp],
                y=[prob],
                mode="markers+text",
                marker=dict(size=20, color="white", line=dict(color="black", width=2)),
                text=[codigo],
                textposition="middle center",
                name=codigo,
                hovertemplate=f"<b>{codigo}</b><br>Prob: {prob+1}<br>Imp: {imp+1}<extra></extra>"
            ))
    
    # Configurar layout
    fig.update_layout(
        xaxis=dict(
            title="IMPACTO",
            tickvals=[0, 1, 2, 3, 4],
            ticktext=["1-Muy Bajo", "2-Bajo", "3-Medio", "4-Alto", "5-Muy Alto"],
            side="bottom"
        ),
        yaxis=dict(
            title="PROBABILIDAD",
            tickvals=[0, 1, 2, 3, 4],
            ticktext=["1-Muy Baja", "2-Baja", "3-Media", "4-Alta", "5-Muy Alta"]
        ),
        height=500,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True, key="mapa_calor_riesgos")


# ==================== RANKING DE ACTIVOS ====================

def render_ranking_activos(evaluaciones: pd.DataFrame, por: str = "inherente"):
    """
    Renderiza ranking de activos ordenados por riesgo.
    
    Args:
        evaluaciones: DataFrame con evaluaciones MAGERIT
        por: "inherente" o "residual"
    """
    columna_riesgo = "riesgo_inherente_global" if por == "inherente" else "riesgo_residual_global"
    columna_nivel = "nivel_riesgo_inherente" if por == "inherente" else "nivel_riesgo_residual"
    titulo = "Riesgo Inherente" if por == "inherente" else "Riesgo Residual"
    
    st.subheader(f"📊 Ranking de Activos por {titulo}")
    
    if evaluaciones.empty:
        st.info("No hay evaluaciones disponibles")
        return
    
    # Ordenar por riesgo descendente
    df = evaluaciones.sort_values(columna_riesgo, ascending=False).head(20)
    
    # Crear gráfico de barras horizontal
    fig = go.Figure()
    
    colores = [COLORES_RIESGO.get(nivel, "#808080") for nivel in df[columna_nivel]]
    
    fig.add_trace(go.Bar(
        y=df["nombre_activo"],
        x=df[columna_riesgo],
        orientation='h',
        marker_color=colores,
        text=df[columna_nivel],
        textposition="auto",
        hovertemplate="<b>%{y}</b><br>Riesgo: %{x}<br><extra></extra>"
    ))
    
    fig.update_layout(
        xaxis_title="Nivel de Riesgo (1-25)",
        yaxis=dict(autorange="reversed"),
        height=max(400, len(df) * 30),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True, key=f"ranking_{por}")


# ==================== COMPARATIVO INHERENTE VS RESIDUAL ====================

def render_comparativo_riesgos(evaluaciones: pd.DataFrame):
    """
    Renderiza comparativo de riesgo inherente vs residual.
    """
    st.subheader("⚖️ Comparativo: Riesgo Inherente vs Residual")
    
    if evaluaciones.empty:
        st.info("No hay evaluaciones disponibles")
        return
    
    df = evaluaciones.copy()
    
    # Asegurar que las columnas de riesgo sean numéricas
    df["riesgo_inherente_global"] = pd.to_numeric(df["riesgo_inherente_global"], errors='coerce').fillna(0)
    df["riesgo_residual_global"] = pd.to_numeric(df["riesgo_residual_global"], errors='coerce').fillna(0)
    
    df = df.sort_values("riesgo_inherente_global", ascending=False).head(15)
    
    fig = go.Figure()
    
    # Barras de riesgo inherente
    fig.add_trace(go.Bar(
        name="Riesgo Inherente",
        y=df["nombre_activo"],
        x=df["riesgo_inherente_global"],
        orientation='h',
        marker_color="#FF6347",
        text=df["riesgo_inherente_global"].round(1),
        textposition="auto"
    ))
    
    # Barras de riesgo residual
    fig.add_trace(go.Bar(
        name="Riesgo Residual",
        y=df["nombre_activo"],
        x=df["riesgo_residual_global"],
        orientation='h',
        marker_color="#32CD32",
        text=df["riesgo_residual_global"].round(1),
        textposition="auto"
    ))
    
    # Calcular reducción
    df["reduccion"] = df["riesgo_inherente_global"] - df["riesgo_residual_global"]
    reduccion_promedio = df["reduccion"].mean()
    
    fig.update_layout(
        barmode='group',
        xaxis_title="Nivel de Riesgo",
        yaxis=dict(autorange="reversed"),
        height=max(400, len(df) * 40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
    st.plotly_chart(fig, use_container_width=True, key="comparativo_riesgos")
    
    # Métricas de reducción
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Reducción Promedio", f"{reduccion_promedio:.1f} puntos")
    with col2:
        pct_reduccion = (reduccion_promedio / df["riesgo_inherente_global"].mean()) * 100
        st.metric("% Reducción", f"{pct_reduccion:.1f}%")
    with col3:
        activos_mejorados = (df["reduccion"] > 0).sum()
        st.metric("Activos Mejorados", f"{activos_mejorados}/{len(df)}")


# ==================== DISTRIBUCIÓN DE AMENAZAS ====================

def render_distribucion_amenazas(amenazas: pd.DataFrame):
    """
    Renderiza distribución de amenazas por tipo y nivel de riesgo.
    """
    st.subheader("🎯 Distribución de Amenazas")
    
    if amenazas.empty:
        st.info("No hay amenazas identificadas")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Por tipo de amenaza
        if "tipo_amenaza" in amenazas.columns:
            conteo_tipo = amenazas["tipo_amenaza"].value_counts()
            fig1 = px.pie(
                values=conteo_tipo.values,
                names=conteo_tipo.index,
                title="Por Tipo de Amenaza",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig1.update_traces(textinfo="percent+label")
            st.plotly_chart(fig1, use_container_width=True, key="dist_tipo_amenaza")
    
    with col2:
        # Por nivel de riesgo
        if "nivel_riesgo" in amenazas.columns:
            conteo_nivel = amenazas["nivel_riesgo"].value_counts()
            # Ordenar por severidad
            orden = ["CRÍTICO", "ALTO", "MEDIO", "BAJO", "MUY BAJO"]
            conteo_nivel = conteo_nivel.reindex([n for n in orden if n in conteo_nivel.index])
            
            fig2 = px.bar(
                x=conteo_nivel.index,
                y=conteo_nivel.values,
                title="Por Nivel de Riesgo",
                color=conteo_nivel.index,
                color_discrete_map=COLORES_RIESGO
            )
            fig2.update_layout(showlegend=False, xaxis_title="", yaxis_title="Cantidad")
            st.plotly_chart(fig2, use_container_width=True, key="dist_nivel_riesgo")


# ==================== COBERTURA DE CONTROLES ====================

def render_cobertura_controles(evaluaciones: pd.DataFrame, controles_detalle: pd.DataFrame = None):
    """
    Renderiza análisis de cobertura de controles ISO 27002.
    """
    st.subheader("🛡️ Cobertura de Controles ISO 27002")
    
    if evaluaciones.empty:
        st.info("No hay evaluaciones disponibles")
        return
    
    # Extraer controles existentes de todas las evaluaciones
    todos_controles = []
    for _, row in evaluaciones.iterrows():
        try:
            controles = json.loads(row.get("controles_existentes", "[]"))
            todos_controles.extend(controles)
        except:
            pass
    
    if not todos_controles:
        st.warning("No se identificaron controles existentes")
        return
    
    # Contar frecuencia de controles
    from collections import Counter
    conteo = Counter(todos_controles)
    
    # Top 20 controles más implementados
    top_controles = conteo.most_common(20)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[c[1] for c in top_controles],
        y=[c[0] for c in top_controles],
        orientation='h',
        marker_color="#4169E1"
    ))
    
    fig.update_layout(
        title="Top 20 Controles Más Implementados",
        xaxis_title="Frecuencia",
        yaxis=dict(autorange="reversed"),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True, key="cobertura_controles")
    
    # Métricas
    total_controles = len(set(todos_controles))
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Controles Únicos Implementados", total_controles)
    with col2:
        cobertura = (total_controles / 93) * 100
        st.metric("Cobertura ISO 27002", f"{cobertura:.1f}%")


# ==================== RESUMEN EJECUTIVO ====================

def render_resumen_ejecutivo(evaluaciones: pd.DataFrame, amenazas: pd.DataFrame = None):
    """
    Renderiza el resumen ejecutivo de la evaluación.
    """
    st.subheader("📋 Resumen Ejecutivo")
    
    if evaluaciones.empty:
        st.info("No hay evaluaciones para mostrar")
        return
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_activos = len(evaluaciones)
        st.metric("Activos Evaluados", total_activos)
    
    with col2:
        riesgo_max = evaluaciones["riesgo_inherente_global"].max()
        st.metric("Riesgo Máximo", f"{riesgo_max:.1f}")
    
    with col3:
        criticos = (evaluaciones["nivel_riesgo_inherente"] == "CRÍTICO").sum()
        altos = (evaluaciones["nivel_riesgo_inherente"] == "ALTO").sum()
        st.metric("Críticos + Altos", f"{criticos + altos}")
    
    with col4:
        riesgo_residual_prom = evaluaciones["riesgo_residual_global"].mean()
        st.metric("Riesgo Residual Prom.", f"{riesgo_residual_prom:.1f}")
    
    # Tabla resumen por nivel
    st.write("**Distribución por Nivel de Riesgo Inherente:**")
    conteo = evaluaciones["nivel_riesgo_inherente"].value_counts()
    for nivel in ["CRÍTICO", "ALTO", "MEDIO", "BAJO", "MUY BAJO"]:
        cantidad = conteo.get(nivel, 0)
        color = COLORES_RIESGO.get(nivel, "#808080")
        pct = (cantidad / total_activos) * 100 if total_activos > 0 else 0
        st.markdown(f"<span style='color:{color};font-weight:bold'>●</span> {nivel}: {cantidad} ({pct:.0f}%)", unsafe_allow_html=True)


# ==================== DETALLE DE ACTIVO ====================

def render_detalle_activo(resultado: Dict):
    """
    Renderiza el detalle de evaluación MAGERIT de un activo.
    
    Args:
        resultado: Dict con estructura de get_resultado_magerit()
    """
    if not resultado:
        st.warning("No hay datos para mostrar")
        return
    
    st.subheader(f"📊 {resultado.get('nombre_activo', 'Activo')}")
    
    # Impacto DIC - adaptado a estructura de get_resultado_magerit
    col1, col2, col3, col4 = st.columns(4)
    
    impacto_d = resultado.get("impacto_d", resultado.get("impacto", {}).get("disponibilidad", "-"))
    impacto_i = resultado.get("impacto_i", resultado.get("impacto", {}).get("integridad", "-"))
    impacto_c = resultado.get("impacto_c", resultado.get("impacto", {}).get("confidencialidad", "-"))
    
    with col1:
        st.metric("Disponibilidad (D)", impacto_d)
    with col2:
        st.metric("Integridad (I)", impacto_i)
    with col3:
        st.metric("Confidencialidad (C)", impacto_c)
    with col4:
        try:
            impacto_global = max(int(impacto_d or 0), int(impacto_i or 0), int(impacto_c or 0))
        except:
            impacto_global = "-"
        st.metric("Impacto Global", impacto_global)
    
    # Riesgos - adaptado a estructura de get_resultado_magerit
    st.write("---")
    col1, col2 = st.columns(2)
    
    riesgo_inh = resultado.get("riesgo_inherente", resultado.get("riesgo_inherente_global", 0))
    nivel_inh = resultado.get("nivel_riesgo", resultado.get("nivel_riesgo_inherente_global", ""))
    riesgo_res = resultado.get("riesgo_residual", resultado.get("riesgo_residual_global", 0))
    nivel_res = resultado.get("nivel_riesgo_residual", resultado.get("nivel_riesgo_residual_global", nivel_inh))
    
    # Formatear valores para mostrar
    riesgo_inh_str = f"{riesgo_inh:.1f}" if isinstance(riesgo_inh, (int, float)) else str(riesgo_inh)
    riesgo_res_str = f"{riesgo_res:.1f}" if isinstance(riesgo_res, (int, float)) else str(riesgo_res)
    
    with col1:
        color_inh = COLORES_RIESGO.get(nivel_inh.upper() if nivel_inh else "", "#808080")
        st.markdown(f"""
        <div style='background-color:{color_inh};padding:20px;border-radius:10px;text-align:center'>
            <h3 style='color:white;margin:0'>Riesgo Inherente</h3>
            <h1 style='color:white;margin:0'>{riesgo_inh_str}</h1>
            <p style='color:white;margin:0'>{nivel_inh}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        color_res = COLORES_RIESGO.get(nivel_res.upper() if nivel_res else "", "#808080")
        st.markdown(f"""
        <div style='background-color:{color_res};padding:20px;border-radius:10px;text-align:center'>
            <h3 style='color:white;margin:0'>Riesgo Residual</h3>
            <h1 style='color:white;margin:0'>{riesgo_res_str}</h1>
            <p style='color:white;margin:0'>{nivel_res}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Amenazas identificadas
    st.write("---")
    st.write("**⚠️ Amenazas Identificadas:**")
    
    amenazas = resultado.get("amenazas", [])
    if amenazas:
        for amenaza in amenazas:
            nivel = amenaza.get("nivel_riesgo", "")
            color = COLORES_RIESGO.get(nivel, "#808080")
            
            with st.expander(f"{amenaza.get('codigo', '')} - {amenaza.get('amenaza', '')} [{nivel}]"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Probabilidad:** {amenaza.get('probabilidad', '-')}")
                with col2:
                    st.write(f"**Impacto:** {amenaza.get('impacto', '-')}")
                with col3:
                    st.write(f"**Riesgo:** {amenaza.get('riesgo_inherente', '-')}")
                
                st.write(f"**Dimensión afectada:** {amenaza.get('dimension_afectada', '')}")
                st.write(f"**Justificación:** {amenaza.get('justificacion', '')}")
                st.write(f"**Tratamiento sugerido:** {amenaza.get('tratamiento', '')}")
                
                # Controles recomendados
                controles_rec = amenaza.get("controles_recomendados", [])
                if controles_rec:
                    st.write("**Controles recomendados:**")
                    for ctrl in controles_rec:
                        st.write(f"  - **{ctrl.get('codigo', '')}**: {ctrl.get('nombre', '')} ({ctrl.get('prioridad', '')})")
    else:
        st.info("No se identificaron amenazas")
    
    # Observaciones
    obs = resultado.get("observaciones", "")
    if obs:
        st.write("---")
        st.write("**📝 Observaciones:**")
        st.info(obs)


# ==================== GAUGE DE RIESGO ====================

def render_gauge_riesgo(valor: float, titulo: str = "Nivel de Riesgo"):
    """Renderiza un gauge de riesgo"""
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': titulo},
        gauge={
            'axis': {'range': [None, 25]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 3], 'color': "#32CD32"},
                {'range': [3, 6], 'color': "#90EE90"},
                {'range': [6, 12], 'color': "#FFA500"},
                {'range': [12, 20], 'color': "#FF6347"},
                {'range': [20, 25], 'color': "#DC143C"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': valor
            }
        }
    ))
    
    fig.update_layout(height=250)
    return fig


# ==================== NIVEL DE MADUREZ ====================

COLORES_MADUREZ = {
    1: "#DC143C",  # Inicial - Rojo
    2: "#FFA500",  # Básico - Naranja
    3: "#FFD700",  # Definido - Amarillo
    4: "#90EE90",  # Gestionado - Verde claro
    5: "#32CD32"   # Optimizado - Verde
}

NOMBRES_MADUREZ = {
    1: "Inicial",
    2: "Básico",
    3: "Definido",
    4: "Gestionado",
    5: "Optimizado"
}


def render_gauge_madurez(puntuacion: float, nivel: int, nombre_nivel: str):
    """Renderiza un gauge de madurez de ciberseguridad"""
    
    color = COLORES_MADUREZ.get(nivel, "#808080")
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=puntuacion,
        number={'suffix': "%"},
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Nivel de Madurez: {nombre_nivel}"},
        gauge={
            'axis': {'range': [0, 100], 'ticksuffix': "%"},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 20], 'color': "#FFCCCC"},
                {'range': [20, 40], 'color': "#FFE5CC"},
                {'range': [40, 60], 'color': "#FFFFCC"},
                {'range': [60, 80], 'color': "#E5FFCC"},
                {'range': [80, 100], 'color': "#CCFFCC"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': puntuacion
            }
        }
    ))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True, key="gauge_madurez")


def render_radar_dominios(dominio_org: float, dominio_per: float, 
                          dominio_fis: float, dominio_tec: float):
    """Renderiza gráfico radar con cobertura por dominios ISO 27002"""
    
    categorias = ['Organizacional\n(5.x)', 'Personas\n(6.x)', 
                  'Físico\n(7.x)', 'Tecnológico\n(8.x)']
    valores = [dominio_org, dominio_per, dominio_fis, dominio_tec]
    
    # Cerrar el polígono
    categorias = categorias + [categorias[0]]
    valores = valores + [valores[0]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=valores,
        theta=categorias,
        fill='toself',
        name='Cobertura Actual',
        fillcolor='rgba(65, 105, 225, 0.3)',
        line=dict(color='#4169E1', width=2)
    ))
    
    # Línea de referencia (100%)
    fig.add_trace(go.Scatterpolar(
        r=[100, 100, 100, 100, 100],
        theta=categorias,
        name='Meta (100%)',
        line=dict(color='gray', dash='dash', width=1)
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix='%'
            )
        ),
        showlegend=True,
        title="Cobertura por Dominios ISO 27002:2022",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True, key="radar_dominios")


def render_madurez_completo(resultado_madurez: Dict):
    """Renderiza la vista completa de madurez de ciberseguridad"""
    
    if not resultado_madurez:
        st.warning("No hay datos de madurez disponibles. Ejecute la evaluación primero.")
        return
    
    st.subheader("🎯 Nivel de Madurez de Ciberseguridad")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    # Soportar tanto minúsculas (dataclass) como mayúsculas (DB)
    nivel = resultado_madurez.get("nivel_madurez") or resultado_madurez.get("Nivel_Madurez", 1)
    nombre = resultado_madurez.get("nombre_nivel") or resultado_madurez.get("Nombre_Nivel", "Inicial")
    puntuacion = resultado_madurez.get("puntuacion_total") or resultado_madurez.get("Puntuacion_Total", 0)
    
    with col1:
        st.metric("Nivel", f"{nivel} - {nombre}")
    with col2:
        st.metric("Puntuación", f"{puntuacion:.0f}%")
    with col3:
        controles_impl = resultado_madurez.get('controles_implementados') or resultado_madurez.get('Controles_Implementados', 0)
        st.metric("Controles Implementados", f"{controles_impl}")
    with col4:
        pct_eval = resultado_madurez.get('pct_activos_evaluados') or resultado_madurez.get('Pct_Activos_Evaluados', 0)
        st.metric("Activos Evaluados", f"{pct_eval:.0f}%")
    
    st.divider()
    
    # Gauge y Radar
    col1, col2 = st.columns(2)
    
    with col1:
        render_gauge_madurez(puntuacion, nivel, nombre)
    
    with col2:
        dom_org = resultado_madurez.get("dominio_organizacional") or resultado_madurez.get("Dominio_Organizacional", 0)
        dom_per = resultado_madurez.get("dominio_personas") or resultado_madurez.get("Dominio_Personas", 0)
        dom_fis = resultado_madurez.get("dominio_fisico") or resultado_madurez.get("Dominio_Fisico", 0)
        dom_tec = resultado_madurez.get("dominio_tecnologico") or resultado_madurez.get("Dominio_Tecnologico", 0)
        render_radar_dominios(dom_org, dom_per, dom_fis, dom_tec)
    
    st.divider()
    
    # Métricas detalladas
    st.write("**📊 Métricas de Madurez**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pct_impl = resultado_madurez.get("pct_controles_implementados") or resultado_madurez.get("Pct_Controles_Implementados", 0)
        st.metric("% Controles Implementados", f"{pct_impl:.0f}%")
    with col2:
        pct_med = resultado_madurez.get("pct_controles_medidos") or resultado_madurez.get("Pct_Controles_Medidos", 0)
        st.metric("% Controles Medidos", f"{pct_med:.0f}%")
    with col3:
        pct_mit = resultado_madurez.get("pct_riesgos_mitigados") or resultado_madurez.get("Pct_Riesgos_Mitigados") or resultado_madurez.get("pct_riesgos_criticos_mitigados", 0)
        st.metric("% Riesgos Críticos Mitigados", f"{pct_mit:.0f}%")
    with col4:
        parciales = resultado_madurez.get("controles_parciales") or resultado_madurez.get("Controles_Parciales", 0)
        st.metric("Controles Parciales", parciales)
    
    # Tabla de dominios
    st.write("**🔷 Cobertura por Dominio ISO 27002:2022**")
    
    dominios_data = [
        {"Dominio": "5.x Organizacional", 
         "Cobertura": f"{dom_org:.0f}%",
         "Descripción": "Políticas, roles, responsabilidades, gestión de activos"},
        {"Dominio": "6.x Personas", 
         "Cobertura": f"{dom_per:.0f}%",
         "Descripción": "Concienciación, formación, ciclo de vida del personal"},
        {"Dominio": "7.x Físico", 
         "Cobertura": f"{dom_fis:.0f}%",
         "Descripción": "Perímetro, áreas seguras, equipos, servicios de apoyo"},
        {"Dominio": "8.x Tecnológico", 
         "Cobertura": f"{dom_tec:.0f}%",
         "Descripción": "Endpoint, red, cifrado, desarrollo, monitoreo"}
    ]
    
    st.dataframe(pd.DataFrame(dominios_data), use_container_width=True, hide_index=True)
    
    # Escala de niveles
    st.write("**📈 Escala de Niveles de Madurez**")
    
    niveles_info = [
        {"Nivel": "1 - Inicial", "Rango": "0-20%", 
         "Descripción": "Procesos ad-hoc, sin controles formales, reactivo"},
        {"Nivel": "2 - Básico", "Rango": "20-40%", 
         "Descripción": "Controles básicos, documentación mínima, dependiente de individuos"},
        {"Nivel": "3 - Definido", "Rango": "40-60%", 
         "Descripción": "Procesos documentados, controles estandarizados, proactivo"},
        {"Nivel": "4 - Gestionado", "Rango": "60-80%", 
         "Descripción": "Controles medidos y monitoreados, métricas establecidas"},
        {"Nivel": "5 - Optimizado", "Rango": "80-100%", 
         "Descripción": "Mejora continua, automatización, excelencia operacional"}
    ]
    
    df_niveles = pd.DataFrame(niveles_info)
    
    # Resaltar nivel actual
    def highlight_nivel(row):
        if f"{nivel} -" in row["Nivel"]:
            return ['background-color: #90EE90'] * len(row)
        return [''] * len(row)
    
    st.dataframe(df_niveles.style.apply(highlight_nivel, axis=1), 
                 use_container_width=True, hide_index=True)


def render_comparativa_madurez(comparativa: Dict):
    """Renderiza comparativa de madurez entre dos evaluaciones"""
    
    if not comparativa:
        st.warning("No hay datos de comparativa disponibles")
        return
    
    st.subheader("📊 Comparativa de Madurez entre Evaluaciones")
    
    # Mensaje resumen
    st.info(comparativa.get("mensaje_resumen", ""))
    
    # Métricas de cambio
    col1, col2, col3 = st.columns(3)
    
    with col1:
        delta_punt = comparativa.get("delta_puntuacion", 0)
        st.metric("Δ Puntuación", f"{delta_punt:+.1f}%", 
                  delta=f"{delta_punt:+.1f}%")
    with col2:
        delta_nivel = comparativa.get("delta_nivel", 0)
        st.metric("Δ Nivel", delta_nivel, delta=delta_nivel)
    with col3:
        delta_riesgo = comparativa.get("delta_riesgo_residual", 0)
        st.metric("Δ Riesgo Residual", f"{delta_riesgo:+.1f}", 
                  delta=f"{delta_riesgo:.1f}", delta_color="inverse")
    
    st.divider()
    
    # Comparativa visual
    madurez_1 = comparativa.get("madurez_1", {})
    madurez_2 = comparativa.get("madurez_2", {})
    
    eval_1 = comparativa.get("eval_1", "Eval 1")
    eval_2 = comparativa.get("eval_2", "Eval 2")
    
    # Gráfico de barras comparativo
    categorias = ['Puntuación Total', 'Organizacional', 'Personas', 'Físico', 'Tecnológico']
    
    valores_1 = [
        madurez_1.get("puntuacion_total", 0),
        madurez_1.get("dominio_organizacional", 0),
        madurez_1.get("dominio_personas", 0),
        madurez_1.get("dominio_fisico", 0),
        madurez_1.get("dominio_tecnologico", 0)
    ]
    
    valores_2 = [
        madurez_2.get("puntuacion_total", 0),
        madurez_2.get("dominio_organizacional", 0),
        madurez_2.get("dominio_personas", 0),
        madurez_2.get("dominio_fisico", 0),
        madurez_2.get("dominio_tecnologico", 0)
    ]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name=eval_1, x=categorias, y=valores_1, marker_color='#FF6347'))
    fig.add_trace(go.Bar(name=eval_2, x=categorias, y=valores_2, marker_color='#32CD32'))
    
    fig.update_layout(
        barmode='group',
        title="Evolución de Madurez por Dominio",
        yaxis_title="Porcentaje (%)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True, key="comparativa_madurez_barras")
    
    # Mejoras y retrocesos
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**✅ Mejoras**")
        mejoras = comparativa.get("mejoras", [])
        if mejoras:
            for m in mejoras:
                st.success(m)
        else:
            st.info("Sin mejoras significativas")
    
    with col2:
        st.write("**⚠️ Retrocesos**")
        retrocesos = comparativa.get("retrocesos", [])
        if retrocesos:
            for r in retrocesos:
                st.error(r)
        else:
            st.info("Sin retrocesos detectados")
    
    # Recomendaciones
    recomendaciones = comparativa.get("recomendaciones", [])
    if recomendaciones:
        st.divider()
        st.write("**💡 Recomendaciones para Mejorar**")
        for i, rec in enumerate(recomendaciones, 1):
            st.write(f"{i}. {rec}")


def render_controles_existentes(controles_data: Dict):
    """Renderiza los controles existentes identificados desde el cuestionario"""
    
    if not controles_data or not controles_data.get("controles"):
        st.warning("No se han identificado controles. Complete el cuestionario primero.")
        return
    
    st.subheader("Controles ISO 27002 Identificados")
    
    resumen = controles_data.get("resumen", {})
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Implementados", resumen.get("implementados", 0))
    with col2:
        st.metric("Parciales", resumen.get("parciales", 0))
    with col3:
        st.metric("No Implementados", resumen.get("no_implementados", 0))
    with col4:
        total = resumen.get("implementados", 0) + resumen.get("parciales", 0)
        st.metric("Total Identificados", total)
    
    st.divider()
    
    # Por dominio
    por_dominio = controles_data.get("por_dominio", {})
    
    for dominio, controles_dom in por_dominio.items():
        if controles_dom:
            dominio_nombre = {
                "organizacional": "5.x Organizacional",
                "personas": "6.x Personas",
                "fisico": "7.x Fisico",
                "tecnologico": "8.x Tecnologico"
            }.get(dominio, dominio)
            
            with st.expander(f"{dominio_nombre} ({len(controles_dom)} controles)"):
                for ctrl in controles_dom:
                    nivel = ctrl.get("nivel", "")
                    efectividad = ctrl.get("efectividad", 0)
                    codigo = ctrl.get("codigo", "")
                    nombre = ctrl.get("nombre", "")
                    
                    # Color según efectividad
                    if efectividad >= 0.66:
                        icono = "[OK]"
                    elif efectividad > 0:
                        icono = "[!]"
                    else:
                        icono = "[X]"
                    
                    st.markdown(f"{icono} **{codigo}**: {nombre}")
                    st.caption(f"   Estado: {nivel} | Efectividad: {efectividad*100:.0f}%")


# ==================== MATRIZ 5x5 VISUAL MAGERIT ====================

def render_matriz_5x5_activos(resultados: pd.DataFrame, key_suffix: str = ""):
    """
    Renderiza la matriz visual 5x5 de Probabilidad x Impacto con activos posicionados.
    Colores oficiales MAGERIT v3.
    """
    st.subheader("Matriz de Riesgos 5x5 - MAGERIT v3")
    
    if resultados.empty:
        st.info("No hay datos para mostrar la matriz")
        return
    
    # Preparar datos: calcular probabilidad e impacto promedio por activo
    # Usamos el riesgo inherente para posicionar (riesgo = prob x impacto)
    df = resultados.copy()
    
    # Normalizar nombres de columnas
    col_riesgo = "Riesgo_Inherente" if "Riesgo_Inherente" in df.columns else "riesgo_inherente_global"
    col_nombre = "Nombre_Activo" if "Nombre_Activo" in df.columns else "nombre_activo"
    col_nivel = "Nivel_Riesgo" if "Nivel_Riesgo" in df.columns else "nivel_riesgo_inherente"
    col_id = "ID_Activo" if "ID_Activo" in df.columns else "id_activo"
    
    if col_riesgo not in df.columns:
        st.warning("No se encontro columna de riesgo inherente")
        return
    
    df[col_riesgo] = pd.to_numeric(df[col_riesgo], errors='coerce').fillna(0)
    
    # Calcular probabilidad e impacto desde el riesgo (asumiendo que riesgo = prob * imp)
    # Para simplificar: prob e impacto se estiman como sqrt(riesgo) redondeado
    df["prob_estimada"] = np.clip(np.round(np.sqrt(df[col_riesgo])), 1, 5).astype(int)
    df["imp_estimado"] = np.clip(np.round(df[col_riesgo] / df["prob_estimada"].replace(0, 1)), 1, 5).astype(int)
    
    # Crear matriz de conteo
    matriz_conteo = np.zeros((5, 5), dtype=int)
    matriz_activos = [[[] for _ in range(5)] for _ in range(5)]
    
    for _, row in df.iterrows():
        prob = int(row["prob_estimada"]) - 1  # 0-indexed
        imp = int(row["imp_estimado"]) - 1
        prob = max(0, min(4, prob))
        imp = max(0, min(4, imp))
        matriz_conteo[prob][imp] += 1
        nombre = str(row.get(col_nombre, row.get(col_id, "?")))[:20]
        matriz_activos[prob][imp].append(nombre)
    
    # Colores MAGERIT oficiales para cada celda
    colores_matriz = [
        ["#32CD32", "#90EE90", "#FFD700", "#FFD700", "#FF6347"],  # Prob 1
        ["#32CD32", "#90EE90", "#FFD700", "#FF6347", "#FF6347"],  # Prob 2
        ["#90EE90", "#FFD700", "#FFD700", "#FF6347", "#DC143C"],  # Prob 3
        ["#90EE90", "#FFD700", "#FF6347", "#DC143C", "#DC143C"],  # Prob 4
        ["#FFD700", "#FF6347", "#FF6347", "#DC143C", "#DC143C"]   # Prob 5
    ]
    
    niveles_matriz = [
        ["MUY BAJO", "BAJO", "MEDIO", "MEDIO", "ALTO"],
        ["MUY BAJO", "BAJO", "MEDIO", "ALTO", "ALTO"],
        ["BAJO", "MEDIO", "MEDIO", "ALTO", "CRITICO"],
        ["BAJO", "MEDIO", "ALTO", "CRITICO", "CRITICO"],
        ["MEDIO", "ALTO", "ALTO", "CRITICO", "CRITICO"]
    ]
    
    valores_riesgo = [
        [1, 2, 3, 4, 5],
        [2, 4, 6, 8, 10],
        [3, 6, 9, 12, 15],
        [4, 8, 12, 16, 20],
        [5, 10, 15, 20, 25]
    ]
    
    # Crear figura con Plotly
    fig = go.Figure()
    
    # Crear heatmap base
    z_values = np.array(valores_riesgo)
    
    fig.add_trace(go.Heatmap(
        z=z_values,
        colorscale=[
            [0, "#32CD32"],      # Verde (Muy Bajo)
            [0.15, "#90EE90"],   # Verde claro (Bajo)
            [0.35, "#FFD700"],   # Amarillo (Medio)
            [0.6, "#FF6347"],    # Rojo (Alto)
            [1, "#DC143C"]       # Rojo oscuro (Critico)
        ],
        showscale=True,
        colorbar=dict(
            title="Riesgo",
            tickvals=[1, 5, 10, 15, 25],
            ticktext=["MUY BAJO", "BAJO", "MEDIO", "ALTO", "CRITICO"]
        ),
        hoverinfo='skip'
    ))
    
    # Agregar anotaciones con conteo y nivel
    for i in range(5):
        for j in range(5):
            conteo = matriz_conteo[i][j]
            nivel = niveles_matriz[i][j]
            valor = valores_riesgo[i][j]
            
            # Texto de la celda
            if conteo > 0:
                texto = f"{nivel}\n({valor})\n\n[{conteo} activos]"
            else:
                texto = f"{nivel}\n({valor})"
            
            # Color del texto segun el fondo
            text_color = "white" if valor >= 15 else "black"
            
            fig.add_annotation(
                x=j, y=i,
                text=texto,
                showarrow=False,
                font=dict(size=10, color=text_color, family="Arial"),
                align="center"
            )
    
    # Configurar layout
    fig.update_layout(
        title=dict(text="Matriz de Riesgos 5x5 - Posicion de Activos", x=0.5),
        xaxis=dict(
            title="IMPACTO",
            tickvals=[0, 1, 2, 3, 4],
            ticktext=["1-Muy Bajo", "2-Bajo", "3-Medio", "4-Alto", "5-Muy Alto"],
            side="bottom",
            showgrid=False
        ),
        yaxis=dict(
            title="PROBABILIDAD",
            tickvals=[0, 1, 2, 3, 4],
            ticktext=["1-Muy Baja", "2-Baja", "3-Media", "4-Alta", "5-Muy Alta"],
            showgrid=False
        ),
        height=500,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True, key=f"matriz_5x5_{key_suffix}")
    
    # Mostrar detalle de activos por celda con expanders
    st.write("**Detalle de Activos por Celda:**")
    
    # Filtrar solo celdas con activos
    celdas_con_activos = []
    for i in range(5):
        for j in range(5):
            if matriz_activos[i][j]:
                nivel = niveles_matriz[i][j]
                celdas_con_activos.append({
                    "prob": i + 1,
                    "imp": j + 1,
                    "nivel": nivel,
                    "activos": matriz_activos[i][j],
                    "riesgo": valores_riesgo[i][j]
                })
    
    # Ordenar por riesgo descendente
    celdas_con_activos.sort(key=lambda x: x["riesgo"], reverse=True)
    
    for celda in celdas_con_activos:
        color = COLORES_RIESGO.get(celda["nivel"], "#808080")
        with st.expander(f"[{celda['nivel']}] Prob={celda['prob']} x Imp={celda['imp']} = {celda['riesgo']} ({len(celda['activos'])} activos)"):
            for activo in celda["activos"]:
                st.markdown(f"- {activo}")


# ==================== NUEVOS DASHBOARDS DE EVALUACION ====================

def render_ranking_activos_criticos(evaluaciones: pd.DataFrame):
    """
    Renderiza ranking de los activos más críticos ordenados por nivel de riesgo.
    """
    st.subheader("Ranking de Activos Mas Criticos")
    
    if evaluaciones.empty:
        st.info("No hay evaluaciones disponibles")
        return
    
    # Filtrar y ordenar por riesgo
    df = evaluaciones.copy()
    df["Riesgo_Inherente"] = pd.to_numeric(df.get("Riesgo_Inherente", df.get("riesgo_inherente_global", 0)), errors='coerce').fillna(0)
    df = df.sort_values("Riesgo_Inherente", ascending=False).head(15)
    
    # Determinar nombre del activo
    col_nombre = "Nombre_Activo" if "Nombre_Activo" in df.columns else "nombre_activo"
    col_nivel = "Nivel_Riesgo" if "Nivel_Riesgo" in df.columns else "nivel_riesgo_inherente"
    
    # Crear gráfico de barras horizontal con colores por nivel
    colores = [COLORES_RIESGO.get(str(nivel).upper(), "#808080") for nivel in df[col_nivel]]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df[col_nombre],
        x=df["Riesgo_Inherente"],
        orientation='h',
        marker_color=colores,
        text=df[col_nivel],
        textposition="auto",
        hovertemplate="<b>%{y}</b><br>Riesgo: %{x}<br>Nivel: %{text}<extra></extra>"
    ))
    
    fig.update_layout(
        xaxis_title="Nivel de Riesgo (1-25)",
        yaxis=dict(autorange="reversed"),
        height=max(400, len(df) * 35),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True, key="ranking_criticos")
    
    # Tabla resumen
    st.write("**Resumen de Activos Criticos:**")
    criticos = (df[col_nivel] == "CRITICO").sum() if "CRITICO" in df[col_nivel].values else (df[col_nivel] == "CRÍTICO").sum()
    altos = (df[col_nivel] == "ALTO").sum()
    st.markdown(f"- **CRITICOS:** {criticos} activos requieren atencion inmediata")
    st.markdown(f"- **ALTOS:** {altos} activos en riesgo elevado")


def render_activos_urgente_tratamiento(evaluaciones: pd.DataFrame, amenazas_df: pd.DataFrame = None):
    """
    Renderiza activos que requieren tratamiento urgente basado en:
    - Sin controles implementados
    - Riesgo alto/crítico
    - Sin salvaguardas efectivas
    """
    st.subheader("Activos con Requerimiento Urgente de Tratamiento")
    
    if evaluaciones.empty:
        st.info("No hay evaluaciones disponibles")
        return
    
    df = evaluaciones.copy()
    
    # Normalizar nombres de columnas
    col_nombre = "Nombre_Activo" if "Nombre_Activo" in df.columns else "nombre_activo"
    col_nivel = "Nivel_Riesgo" if "Nivel_Riesgo" in df.columns else "nivel_riesgo_inherente"
    col_riesgo = "Riesgo_Inherente" if "Riesgo_Inherente" in df.columns else "riesgo_inherente_global"
    col_residual = "Riesgo_Residual" if "Riesgo_Residual" in df.columns else "riesgo_residual_global"
    
    df[col_riesgo] = pd.to_numeric(df[col_riesgo], errors='coerce').fillna(0)
    df[col_residual] = pd.to_numeric(df[col_residual], errors='coerce').fillna(0)
    
    # Filtrar activos urgentes (CRITICO o ALTO con riesgo residual similar al inherente)
    df["Gap_Reduccion"] = df[col_riesgo] - df[col_residual]
    
    # Activos urgentes: alto riesgo con poca reduccion (controles inefectivos)
    urgentes = df[
        ((df[col_nivel].isin(["CRITICO", "CRÍTICO", "ALTO"])) & (df["Gap_Reduccion"] <= 2))
    ].sort_values(col_riesgo, ascending=False).head(15)
    
    if urgentes.empty:
        st.success("No hay activos que requieran tratamiento urgente")
        return
    
    # Indicadores de urgencia
    col1, col2, col3 = st.columns(3)
    with col1:
        n_criticos = urgentes[col_nivel].isin(["CRITICO", "CRÍTICO"]).sum()
        st.metric("Criticos Sin Proteccion", n_criticos, delta=None)
    with col2:
        n_altos = (urgentes[col_nivel] == "ALTO").sum()
        st.metric("Altos Sin Mitigacion", n_altos, delta=None)
    with col3:
        riesgo_prom = urgentes[col_riesgo].mean()
        st.metric("Riesgo Promedio", f"{riesgo_prom:.1f}", delta=None)
    
    # Lista de activos urgentes con indicador visual
    st.write("---")
    st.write("**Activos Prioritarios:**")
    
    for idx, row in urgentes.iterrows():
        nivel = row[col_nivel]
        color = COLORES_RIESGO.get(str(nivel).upper(), "#808080")
        nombre = row[col_nombre]
        riesgo = row[col_riesgo]
        gap = row["Gap_Reduccion"]
        
        urgencia = "CRITICA" if nivel in ["CRITICO", "CRÍTICO"] else "ALTA"
        icono = "[!!!]" if urgencia == "CRITICA" else "[!!]"
        
        st.markdown(f"""
        <div style='background-color:{color}20;border-left:4px solid {color};padding:10px;margin:5px 0;border-radius:5px'>
            <strong>{icono} {nombre}</strong><br>
            Riesgo: {riesgo:.0f} | Nivel: {nivel} | Reduccion actual: {gap:.0f} pts<br>
            <em>Urgencia: {urgencia} - Requiere controles inmediatos</em>
        </div>
        """, unsafe_allow_html=True)


def render_dashboard_amenazas(amenazas_df: pd.DataFrame = None, resultados: pd.DataFrame = None):
    """
    Dashboard detallado de amenazas identificadas.
    """
    st.subheader("Analisis de Amenazas")
    
    if amenazas_df is not None and not amenazas_df.empty:
        df = amenazas_df.copy()
    elif resultados is not None and not resultados.empty:
        # Extraer amenazas de los resultados si están almacenados como JSON
        all_amenazas = []
        for _, row in resultados.iterrows():
            try:
                amenazas_str = row.get("Amenazas", row.get("amenazas", "[]"))
                if amenazas_str and amenazas_str != "[]":
                    amenazas = json.loads(amenazas_str) if isinstance(amenazas_str, str) else amenazas_str
                    for a in amenazas:
                        a["activo"] = row.get("Nombre_Activo", row.get("nombre_activo", ""))
                        all_amenazas.append(a)
            except:
                pass
        df = pd.DataFrame(all_amenazas)
    else:
        st.info("No hay datos de amenazas disponibles")
        return
    
    if df.empty:
        st.info("No se identificaron amenazas en la evaluacion")
        return
    
    # Métricas generales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Amenazas", len(df))
    with col2:
        criticas = df[df.get("nivel_riesgo", pd.Series()).isin(["CRITICO", "CRÍTICO"])].shape[0] if "nivel_riesgo" in df.columns else 0
        st.metric("Amenazas Criticas", criticas)
    with col3:
        altas = df[df.get("nivel_riesgo", pd.Series()) == "ALTO"].shape[0] if "nivel_riesgo" in df.columns else 0
        st.metric("Amenazas Altas", altas)
    with col4:
        tipos = df.get("tipo_amenaza", df.get("categoria", pd.Series())).nunique()
        st.metric("Tipos de Amenaza", tipos)
    
    st.write("---")
    st.info("Para ver graficos detallados de amenazas, use la funcion render_dashboard_amenazas_mejorado")


def render_dashboard_amenazas_mejorado(resultados: pd.DataFrame, eval_id: str):
    """
    Dashboard de AMENAZAS MAGERIT - Muestra catalogo de amenazas y matriz 5x5.
    Enfocado en amenazas, no en riesgos de activos.
    """
    import sqlite3
    
    st.subheader("🎯 Catalogo de Amenazas MAGERIT v3")
    
    # Cargar catalogo de amenazas desde BD
    try:
        conn = sqlite3.connect("tita_database.db")
        amenazas_cat = pd.read_sql_query("SELECT * FROM CATALOGO_AMENAZAS_MAGERIT", conn)
        conn.close()
    except Exception as e:
        st.error(f"Error al cargar catalogo de amenazas: {e}")
        amenazas_cat = pd.DataFrame()
    
    if not amenazas_cat.empty:
        # Metricas del catalogo
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Amenazas", len(amenazas_cat))
        with col2:
            desastres = len(amenazas_cat[amenazas_cat["tipo_amenaza"] == "Desastres Naturales"])
            st.metric("🌊 Desastres Naturales", desastres)
        with col3:
            industrial = len(amenazas_cat[amenazas_cat["tipo_amenaza"] == "Origen Industrial"])
            st.metric("🏭 Origen Industrial", industrial)
        with col4:
            errores = len(amenazas_cat[amenazas_cat["tipo_amenaza"] == "Errores no Intencionados"])
            st.metric("⚠️ Errores", errores)
        
        col1b, col2b, col3b, col4b = st.columns(4)
        with col1b:
            ataques = len(amenazas_cat[amenazas_cat["tipo_amenaza"] == "Ataques Intencionados"])
            st.metric("🎯 Ataques Intencionados", ataques)
        
        st.divider()
        
        # Fila 1: Grafico de amenazas por tipo y tabla
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("**Distribucion de Amenazas por Tipo:**")
            tipo_counts = amenazas_cat["tipo_amenaza"].value_counts()
            
            colores_tipo = {
                "Desastres Naturales": "#3498db",
                "Origen Industrial": "#e67e22", 
                "Errores no Intencionados": "#f1c40f",
                "Ataques Intencionados": "#e74c3c"
            }
            
            fig1 = go.Figure(data=[go.Pie(
                labels=tipo_counts.index.tolist(),
                values=tipo_counts.values.tolist(),
                hole=0.4,
                marker_colors=[colores_tipo.get(t, "#808080") for t in tipo_counts.index]
            )])
            fig1.update_traces(textinfo="percent+value", textposition="outside")
            fig1.update_layout(height=400, showlegend=True, title="Amenazas por Categoria MAGERIT")
            st.plotly_chart(fig1, use_container_width=True, key="amenazas_tipo_pie")
        
        with col2:
            st.write("**Amenazas por Tipo (Barras):**")
            fig2 = go.Figure(go.Bar(
                x=tipo_counts.values.tolist(),
                y=tipo_counts.index.tolist(),
                orientation='h',
                marker_color=[colores_tipo.get(t, "#808080") for t in tipo_counts.index],
                text=tipo_counts.values.tolist(),
                textposition='auto'
            ))
            fig2.update_layout(
                height=400, 
                yaxis=dict(autorange="reversed"),
                xaxis_title="Cantidad de Amenazas",
                title="Amenazas MAGERIT por Categoria"
            )
            st.plotly_chart(fig2, use_container_width=True, key="amenazas_cat_bar")
        
        st.divider()
        
        # Explorador de amenazas por categoria
        st.write("**🔍 Explorador de Amenazas MAGERIT:**")
        
        tipo_seleccionado = st.selectbox(
            "Seleccionar tipo de amenaza:",
            ["Todos"] + amenazas_cat["tipo_amenaza"].unique().tolist(),
            key="select_tipo_amenaza"
        )
        
        if tipo_seleccionado == "Todos":
            df_filtrado = amenazas_cat
        else:
            df_filtrado = amenazas_cat[amenazas_cat["tipo_amenaza"] == tipo_seleccionado]
        
        # Mostrar tabla de amenazas
        st.dataframe(
            df_filtrado[["codigo", "amenaza", "tipo_amenaza", "descripcion", "aplicable_a"]].rename(columns={
                "codigo": "Codigo",
                "amenaza": "Amenaza",
                "tipo_amenaza": "Tipo",
                "descripcion": "Descripcion",
                "aplicable_a": "Aplicable a"
            }),
            use_container_width=True,
            hide_index=True,
            height=300
        )
    else:
        st.warning("No hay catalogo de amenazas disponible")


def render_dashboard_controles_salvaguardas(resultados: pd.DataFrame = None, madurez: Dict = None):
    """
    Dashboard de controles y salvaguardas implementadas.
    Grafico de implementacion prominente.
    """
    st.subheader("🛡️ Estado de Controles y Salvaguardas ISO 27002")
    
    # Métricas de madurez de controles
    if madurez:
        impl = madurez.get("Controles_Implementados", madurez.get("controles_implementados", 0))
        parciales = madurez.get("Controles_Parciales", madurez.get("controles_parciales", 0))
        no_impl = madurez.get("Controles_No_Implementados", madurez.get("controles_no_implementados", 0))
        total = impl + parciales + no_impl
        pct = (impl / total * 100) if total > 0 else 0
        
        # Metricas destacadas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("✅ Implementados", impl)
        with col2:
            st.metric("🔄 Parciales", parciales)
        with col3:
            st.metric("❌ No Implementados", no_impl)
        with col4:
            delta_color = "normal" if pct >= 50 else "inverse" if pct < 20 else "off"
            st.metric("📊 Cobertura Total", f"{pct:.0f}%")
        
        st.divider()
        
        # GRAFICO PRINCIPAL DE IMPLEMENTACION - Ancho completo y mas alto
        st.write("### 📈 Estado de Implementacion de Controles")
        
        fig_impl = go.Figure(data=[go.Pie(
            labels=['Implementados', 'Parciales', 'No Implementados'],
            values=[impl, parciales, no_impl],
            hole=0.5,
            marker_colors=['#27ae60', '#f39c12', '#e74c3c'],
            textinfo='percent+value',
            textfont=dict(size=16),
            pull=[0.05, 0, 0]  # Destacar implementados
        )])
        
        fig_impl.update_layout(
            height=450,  # Mas alto
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=14)
            ),
            annotations=[dict(
                text=f'<b>{pct:.0f}%</b><br>Cobertura',
                x=0.5, y=0.5,
                font_size=24,
                showarrow=False
            )],
            title=dict(
                text="Estado de Implementacion de Controles ISO 27002",
                font=dict(size=18),
                x=0.5
            )
        )
        
        st.plotly_chart(fig_impl, use_container_width=True, key="controles_dona_grande")
        
        st.divider()
        
        # Fila con grafico de barras y recomendaciones
        col1, col2 = st.columns([1.5, 1])
        
        with col1:
            st.write("**Cobertura por Dominio ISO 27002:2022:**")
            
            dominios = {
                "5.x Organizacional": madurez.get("Dominio_Organizacional", madurez.get("dominio_organizacional", 0)),
                "6.x Personas": madurez.get("Dominio_Personas", madurez.get("dominio_personas", 0)),
                "7.x Fisico": madurez.get("Dominio_Fisico", madurez.get("dominio_fisico", 0)),
                "8.x Tecnologico": madurez.get("Dominio_Tecnologico", madurez.get("dominio_tecnologico", 0))
            }
            
            # Grafico de barras para dominios
            dom_nombres = list(dominios.keys())
            dom_valores = list(dominios.values())
            dom_colores = ["#27ae60" if v >= 60 else "#f39c12" if v >= 30 else "#e74c3c" for v in dom_valores]
            
            fig_dom = go.Figure(go.Bar(
                x=dom_valores,
                y=dom_nombres,
                orientation='h',
                marker_color=dom_colores,
                text=[f"{v:.0f}%" for v in dom_valores],
                textposition='auto'
            ))
            
            fig_dom.update_layout(
                height=300,
                xaxis=dict(title="Cobertura (%)", range=[0, 100]),
                yaxis=dict(autorange="reversed"),
                showlegend=False,
                title="Cobertura por Dominio"
            )
            
            st.plotly_chart(fig_dom, use_container_width=True, key="dominios_bar")
        
        with col2:
            st.write("**📋 Recomendaciones:**")
            if pct < 20:
                st.error("🚨 Nivel CRITICO")
                st.markdown("""
                - ⚡ Implementar controles basicos de acceso
                - 📜 Establecer politicas de seguridad minimas
                - 👥 Capacitar al personal urgentemente
                - 🔒 Proteger activos criticos primero
                """)
            elif pct < 40:
                st.warning("⚠️ Nivel BASICO")
                st.markdown("""
                - 📝 Documentar procedimientos existentes
                - 💻 Implementar controles tecnologicos
                - 🔄 Establecer procesos de backup
                """)
            elif pct < 60:
                st.info("📊 Nivel DEFINIDO")
                st.markdown("""
                - 📋 Estandarizar controles
                - 📡 Implementar monitoreo continuo
                - 🎯 Mejorar deteccion de incidentes
                """)
            else:
                st.success("✅ Nivel GESTIONADO")
                st.markdown("""
                - 🔄 Mantener mejora continua
                - 📈 Medir efectividad de controles
                - 🎯 Optimizar procesos existentes
                """)
        
        st.divider()
        
        # Barras de progreso para dominios (visual alternativo)
        st.write("**📊 Progreso Visual por Dominio:**")
        
        for dominio, pct_dom in dominios.items():
            color = "#27ae60" if pct_dom >= 60 else "#f39c12" if pct_dom >= 30 else "#e74c3c"
            icono = "✅" if pct_dom >= 60 else "🔄" if pct_dom >= 30 else "❌"
            st.markdown(f"""
            <div style='margin:10px 0'>
                <strong>{icono} {dominio}:</strong> {pct_dom:.0f}%
                <div style='background-color:#e0e0e0;border-radius:10px;height:25px;width:100%'>
                    <div style='background-color:{color};width:{min(pct_dom, 100)}%;height:100%;border-radius:10px;display:flex;align-items:center;justify-content:center'>
                        <span style='color:white;font-weight:bold;font-size:12px'>{pct_dom:.0f}%</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No hay datos de madurez disponibles. Complete el cuestionario de controles primero.")


def render_dashboard_evaluacion_completo(evaluaciones: pd.DataFrame, madurez: Dict = None):
    """
    Renderiza el dashboard completo de evaluación con todos los componentes.
    """
    if evaluaciones.empty:
        st.warning("No hay evaluaciones disponibles")
        return
    
    # Tab layout para organizar dashboards
    tab1, tab2, tab3, tab4 = st.tabs([
        "Ranking Criticos", 
        "Tratamiento Urgente",
        "Amenazas",
        "Controles y Salvaguardas"
    ])
    
    with tab1:
        render_ranking_activos_criticos(evaluaciones)
    
    with tab2:
        render_activos_urgente_tratamiento(evaluaciones)
    
    with tab3:
        render_dashboard_amenazas(resultados=evaluaciones)
    
    with tab4:
        render_dashboard_controles_salvaguardas(resultados=evaluaciones, madurez=madurez)
