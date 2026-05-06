"""
UTILIDADES DE ESTILO — Proyecto TITA
=====================================
Funciones compartidas de estilo visual para todas las componentes UI.
"""
import streamlit as st


def styled_header(icon: str, title: str, subtitle: str = ""):
    """Genera un header estilizado con gradiente y borde teal."""
    sub_html = f'<p style="color:#5a8898; font-size:0.82rem; margin:0;">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(46,196,182,0.08) 0%, rgba(12,26,46,0.4) 100%);
                border: 1px solid rgba(46,196,182,0.12); border-radius:12px;
                padding:1.2rem 1.5rem; margin-bottom:1rem;">
        <h2 style="color:#e0eff8; font-weight:700; margin:0 0 0.2rem 0; font-size:1.4rem; border:none; padding:0;">
            {icon} {title}
        </h2>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def eval_badge(eval_nombre: str):
    """Muestra un badge estilizado de la evaluación activa."""
    st.markdown(f"""
    <div style="background:rgba(46,196,182,0.06); border-left:3px solid #2ec4b6;
                border-radius:0 8px 8px 0; padding:0.6rem 1rem; margin-bottom:1rem;
                display:flex; align-items:center; gap:0.8rem;">
        <span style="font-size:1.3rem;">📋</span>
        <div>
            <span style="color:#7eb8c9; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.8px;">Evaluación activa</span><br>
            <span style="color:#e0eff8; font-weight:700; font-size:0.95rem;">{eval_nombre}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def section_card(icon: str, title: str, content_html: str = ""):
    """Una card estilizada para secciones internas."""
    st.markdown(f"""
    <div style="background:rgba(12,26,46,0.4); border:1px solid rgba(46,196,182,0.1);
                border-radius:10px; padding:1rem 1.2rem; margin:0.5rem 0;">
        <h3 style="color:#b0cad8; font-weight:600; margin:0 0 0.3rem 0; font-size:1.05rem; border:none; padding:0;">
            {icon} {title}
        </h3>
        {content_html}
    </div>
    """, unsafe_allow_html=True)
