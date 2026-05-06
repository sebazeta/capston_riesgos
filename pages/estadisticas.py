"""
Página: Estadísticas (Principal)
Muestra el resumen de la evaluación activa y progreso general.
"""
import streamlit as st
from services import get_estadisticas_evaluacion


def render_estadisticas(_styled_header):
    """Renderiza la página principal de estadísticas."""
    _styled_header("", "Estadísticas", "Resumen de la evaluación activa y progreso general")

    if st.session_state["eval_actual"]:
        st.markdown(f"""
        <div style="background:rgba(46,196,182,0.06); border:1px solid rgba(46,196,182,0.15);
                    border-radius:10px; padding:0.8rem 1rem; margin:0.4rem 0 1rem 0;">
            <div style="color:#7eb8c9; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.8px; margin-bottom:0.3rem;">Evaluación Activa</div>
            <div style="color:#e0eff8; font-weight:700; font-size:1.1rem;">{st.session_state['eval_nombre']}</div>
            <div style="color:#5a8898; font-size:0.75rem; margin-top:0.2rem; font-family:monospace;">{st.session_state['eval_actual']}</div>
        </div>
        """, unsafe_allow_html=True)

        stats = get_estadisticas_evaluacion(st.session_state["eval_actual"])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Activos", stats["total_activos"])
        c2.metric("Progreso", f"{stats['progreso']}%")
        c3.metric("Evaluados", stats["evaluados"])
        c4.metric("Pendientes", stats["pendientes"])

        if st.button("Cambiar Evaluación", use_container_width=False):
            st.session_state["eval_actual"] = None
            st.session_state["eval_nombre"] = None
            st.rerun()
    else:
        st.warning("**Sin Evaluación Seleccionada**")
        st.info("Ve a la sección **Evaluaciones** del menú para seleccionar o crear una.")
