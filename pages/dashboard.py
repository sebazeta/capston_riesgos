"""
Página: Dashboard
Resumen visual del estado de riesgos y controles.
"""
import streamlit as st
import plotly.graph_objects as go
from services import (
    get_activos_por_evaluacion, get_resumen_evaluacion,
    get_resultado_magerit, get_madurez_evaluacion
)

# Importaciones condicionales de componentes de dashboard
try:
    from components.dashboard_magerit import (
        render_resumen_ejecutivo, render_ranking_activos_criticos,
        render_detalle_activo, render_dashboard_amenazas_mejorado,
        render_dashboard_controles_salvaguardas,
        render_activos_urgente_tratamiento,
        render_matriz_5x5_activos, render_madurez_completo
    )
    DASHBOARD_DISPONIBLE = True
except ImportError:
    DASHBOARD_DISPONIBLE = False


def render_dashboard(_styled_header):
    """Renderiza la página de Dashboard."""
    _styled_header("", "Dashboard de Evaluación", "Resumen visual del estado de riesgos y controles")

    if not st.session_state.get("eval_actual"):
        st.error("**EVALUACIÓN REQUERIDA**")
        st.warning("Ve a la sección **Evaluaciones** y selecciona una evaluación primero.")
    else:
        st.success(f"Evaluación: **{st.session_state['eval_nombre']}**")

        # Obtener resumen de evaluación MAGERIT
        resumen_magerit = get_resumen_evaluacion(st.session_state["eval_actual"])
        activos = get_activos_por_evaluacion(st.session_state["eval_actual"])

        # Obtener datos de madurez
        madurez_data = get_madurez_evaluacion(st.session_state["eval_actual"])

        if resumen_magerit.empty:
            st.info("No hay evaluaciones completadas. Ve a IA Evaluación para evaluar activos.")

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
                dash_tab1, dash_tab2, dash_tab3, dash_tab4 = st.tabs([
                    "Activos Criticos",
                    "Tratamiento Urgente",
                    "Amenazas MAGERIT",
                    "Controles y Salvaguardas"
                ])

                with dash_tab1:
                    render_ranking_activos_criticos(resumen_magerit)
                    st.divider()
                    render_resumen_ejecutivo(resumen_magerit)
                    st.divider()
                    render_matriz_5x5_activos(resumen_magerit, key_suffix="activos_criticos")

                with dash_tab2:
                    render_activos_urgente_tratamiento(resumen_magerit)

                with dash_tab3:
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
                        st.json(resultado)

    # Botón de refresco
    if st.button("Actualizar Dashboard", key="t4_refresh"):
        st.rerun()
