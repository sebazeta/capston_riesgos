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
    
    df = evaluaciones.sort_values("riesgo_inherente_global", ascending=False).head(15)
    
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
        resultado: Dict con estructura ResultadoEvaluacionMagerit
    """
    st.subheader(f"📊 {resultado.get('nombre_activo', 'Activo')}")
    
    # Impacto DIC
    impacto = resultado.get("impacto", {})
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Disponibilidad", impacto.get("disponibilidad", "-"))
    with col2:
        st.metric("Integridad", impacto.get("integridad", "-"))
    with col3:
        st.metric("Confidencialidad", impacto.get("confidencialidad", "-"))
    with col4:
        impacto_global = max(
            impacto.get("disponibilidad", 0),
            impacto.get("integridad", 0),
            impacto.get("confidencialidad", 0)
        )
        st.metric("Impacto Global", impacto_global)
    
    # Riesgos
    st.write("---")
    col1, col2 = st.columns(2)
    
    with col1:
        nivel_inh = resultado.get("nivel_riesgo_inherente_global", "")
        color_inh = COLORES_RIESGO.get(nivel_inh, "#808080")
        st.markdown(f"""
        <div style='background-color:{color_inh};padding:20px;border-radius:10px;text-align:center'>
            <h3 style='color:white;margin:0'>Riesgo Inherente</h3>
            <h1 style='color:white;margin:0'>{resultado.get('riesgo_inherente_global', 0)}</h1>
            <p style='color:white;margin:0'>{nivel_inh}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        nivel_res = resultado.get("nivel_riesgo_residual_global", "")
        color_res = COLORES_RIESGO.get(nivel_res, "#808080")
        st.markdown(f"""
        <div style='background-color:{color_res};padding:20px;border-radius:10px;text-align:center'>
            <h3 style='color:white;margin:0'>Riesgo Residual</h3>
            <h1 style='color:white;margin:0'>{resultado.get('riesgo_residual_global', 0)}</h1>
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
    
    nivel = resultado_madurez.get("nivel_madurez", 1)
    nombre = resultado_madurez.get("nombre_nivel", "Inicial")
    puntuacion = resultado_madurez.get("puntuacion_total", 0)
    
    with col1:
        st.metric("Nivel", f"{nivel} - {nombre}")
    with col2:
        st.metric("Puntuación", f"{puntuacion:.0f}%")
    with col3:
        st.metric("Controles Implementados", 
                  f"{resultado_madurez.get('controles_implementados', 0)}")
    with col4:
        st.metric("Activos Evaluados", 
                  f"{resultado_madurez.get('pct_activos_evaluados', 0):.0f}%")
    
    st.divider()
    
    # Gauge y Radar
    col1, col2 = st.columns(2)
    
    with col1:
        render_gauge_madurez(puntuacion, nivel, nombre)
    
    with col2:
        render_radar_dominios(
            resultado_madurez.get("dominio_organizacional", 0),
            resultado_madurez.get("dominio_personas", 0),
            resultado_madurez.get("dominio_fisico", 0),
            resultado_madurez.get("dominio_tecnologico", 0)
        )
    
    st.divider()
    
    # Métricas detalladas
    st.write("**📊 Métricas de Madurez**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pct_impl = resultado_madurez.get("pct_controles_implementados", 0)
        st.metric("% Controles Implementados", f"{pct_impl:.0f}%")
    with col2:
        pct_med = resultado_madurez.get("pct_controles_medidos", 0)
        st.metric("% Controles Medidos", f"{pct_med:.0f}%")
    with col3:
        pct_mit = resultado_madurez.get("pct_riesgos_mitigados", 
                  resultado_madurez.get("pct_riesgos_criticos_mitigados", 0))
        st.metric("% Riesgos Críticos Mitigados", f"{pct_mit:.0f}%")
    with col4:
        parciales = resultado_madurez.get("controles_parciales", 0)
        st.metric("Controles Parciales", parciales)
    
    # Tabla de dominios
    st.write("**🔷 Cobertura por Dominio ISO 27002:2022**")
    
    dominios_data = [
        {"Dominio": "5.x Organizacional", 
         "Cobertura": f"{resultado_madurez.get('dominio_organizacional', 0):.0f}%",
         "Descripción": "Políticas, roles, responsabilidades, gestión de activos"},
        {"Dominio": "6.x Personas", 
         "Cobertura": f"{resultado_madurez.get('dominio_personas', 0):.0f}%",
         "Descripción": "Concienciación, formación, ciclo de vida del personal"},
        {"Dominio": "7.x Físico", 
         "Cobertura": f"{resultado_madurez.get('dominio_fisico', 0):.0f}%",
         "Descripción": "Perímetro, áreas seguras, equipos, servicios de apoyo"},
        {"Dominio": "8.x Tecnológico", 
         "Cobertura": f"{resultado_madurez.get('dominio_tecnologico', 0):.0f}%",
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
    
    st.subheader("🛡️ Controles ISO 27002 Identificados")
    
    resumen = controles_data.get("resumen", {})
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("✅ Implementados", resumen.get("implementados", 0))
    with col2:
        st.metric("⚠️ Parciales", resumen.get("parciales", 0))
    with col3:
        st.metric("❌ No Implementados", resumen.get("no_implementados", 0))
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
                "fisico": "7.x Físico",
                "tecnologico": "8.x Tecnológico"
            }.get(dominio, dominio)
            
            with st.expander(f"📁 {dominio_nombre} ({len(controles_dom)} controles)"):
                for ctrl in controles_dom:
                    nivel = ctrl.get("nivel", "")
                    efectividad = ctrl.get("efectividad", 0)
                    codigo = ctrl.get("codigo", "")
                    nombre = ctrl.get("nombre", "")
                    
                    # Color según efectividad
                    if efectividad >= 0.66:
                        icono = "✅"
                        color = "green"
                    elif efectividad > 0:
                        icono = "⚠️"
                        color = "orange"
                    else:
                        icono = "❌"
                        color = "red"
                    
                    st.markdown(f"{icono} **{codigo}**: {nombre}")
                    st.caption(f"   Estado: {nivel} | Efectividad: {efectividad*100:.0f}%")
