"""
Página: Madurez
Evaluación del nivel de madurez de ciberseguridad ISO/IEC 27002.
"""
import streamlit as st
from services import (
    get_madurez_evaluacion, get_controles_existentes_detallados,
    calcular_madurez_evaluacion, guardar_madurez
)
from services.process_log_service import registrar_proceso_rapido

# Importaciones condicionales
try:
    from components.dashboard_magerit import (
        render_madurez_completo, render_controles_existentes
    )
    DASHBOARD_DISPONIBLE = True
except ImportError:
    DASHBOARD_DISPONIBLE = False


def render_madurez(_styled_header):
    """Renderiza la página de nivel de madurez."""
    _styled_header("", "Nivel de Madurez de Ciberseguridad", "Evaluación del nivel de madurez ISO/IEC 27002")

    if not st.session_state.get("eval_actual"):
        st.error("**EVALUACIÓN REQUERIDA**")
        st.warning("Ve a la sección **Evaluaciones** y selecciona una evaluación primero.")
    else:
        st.success(f"Evaluación: **{st.session_state['eval_nombre']}**")

        # Obtener madurez guardada primero
        madurez_data = get_madurez_evaluacion(st.session_state["eval_actual"])

        # Solo mostrar botón de calcular si NO hay datos o el usuario quiere recalcular
        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            if not madurez_data:
                if st.button("Calcular Nivel de Madurez", type="primary", key="t5_calc_madurez"):
                    with st.spinner("Calculando nivel de madurez..."):
                        resultado_madurez = calcular_madurez_evaluacion(st.session_state["eval_actual"])
                        if resultado_madurez:
                            guardar_madurez(resultado_madurez)
                            registrar_proceso_rapido(st.session_state["eval_actual"],
                                "calcular_madurez", "MADUREZ",
                                f"Madurez calculada: {resultado_madurez.puntuacion_total}% - {resultado_madurez.nombre_nivel}")
                            st.success("Nivel de madurez calculado y guardado")
                            st.rerun()
                        else:
                            st.error("No se pudo calcular la madurez. Verifique que hay activos y respuestas.")
            else:
                if st.button("Recalcular Madurez", key="t5_calc_madurez"):
                    with st.spinner("Recalculando nivel de madurez..."):
                        resultado_madurez = calcular_madurez_evaluacion(st.session_state["eval_actual"])
                        if resultado_madurez:
                            guardar_madurez(resultado_madurez)
                            registrar_proceso_rapido(st.session_state["eval_actual"],
                                "recalcular_madurez", "MADUREZ",
                                f"Madurez recalculada: {resultado_madurez.puntuacion_total}% - {resultado_madurez.nombre_nivel}")
                            st.success("Nivel de madurez recalculado")
                            st.rerun()
                        else:
                            st.error("No se pudo recalcular la madurez.")
        with col_btn2:
            st.caption("El botón **Análisis Completo** en IA Evaluación ya incluye el cálculo de madurez (Fase 3).")

        st.divider()

        if madurez_data:
            if DASHBOARD_DISPONIBLE:
                render_madurez_completo(madurez_data)
            else:
                # Visualización básica sin componentes
                st.subheader(f"Nivel: {madurez_data.get('Nivel_Madurez', 1)} - {madurez_data.get('Nombre_Nivel', 'Inicial')}")
                st.metric("Puntuación Total", f"{madurez_data.get('Puntuacion_Total', 0):.0f}%")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Organizacional", f"{madurez_data.get('Dominio_Organizacional', 0):.0f}%")
                col2.metric("Personas", f"{madurez_data.get('Dominio_Personas', 0):.0f}%")
                col3.metric("Físico", f"{madurez_data.get('Dominio_Fisico', 0):.0f}%")
                col4.metric("Tecnológico", f"{madurez_data.get('Dominio_Tecnologico', 0):.0f}%")

                st.divider()

                col1, col2, col3 = st.columns(3)
                col1.metric("Controles Implementados", madurez_data.get('Controles_Implementados', 0))
                col2.metric("Controles Parciales", madurez_data.get('Controles_Parciales', 0))
                col3.metric("% Activos Evaluados", f"{madurez_data.get('Pct_Activos_Evaluados', 0):.0f}%")
        else:
            st.info("No hay datos de madurez calculados. Haz clic en el botón de arriba para calcular.")
            st.markdown("""
            **El nivel de madurez se calcula basándose en:**
            - % de controles ISO 27002 implementados (30%)
            - % de controles medidos/monitoreados (25%)
            - % de riesgos críticos/altos mitigados (25%)
            - % de activos evaluados correctamente (20%)

            **Niveles:**
            1. **Inicial** (0-20%): Procesos ad-hoc, sin controles formales
            2. **Básico** (20-40%): Controles básicos, documentación mínima
            3. **Definido** (40-60%): Procesos documentados, controles estandarizados
            4. **Gestionado** (60-80%): Controles medidos y monitoreados
            5. **Optimizado** (80-100%): Mejora continua, automatización
            """)

        st.divider()

        # Sección de controles existentes
        st.subheader("Controles Existentes Identificados")

        controles_data = get_controles_existentes_detallados(st.session_state["eval_actual"])

        if DASHBOARD_DISPONIBLE and controles_data.get("controles"):
            render_controles_existentes(controles_data)
        elif controles_data.get("controles"):
            resumen = controles_data.get("resumen", {})
            col1, col2, col3 = st.columns(3)
            col1.metric("Implementados", resumen.get("implementados", 0))
            col2.metric("Parciales", resumen.get("parciales", 0))
            col3.metric("No Implementados", resumen.get("no_implementados", 0))

            st.write("**Controles identificados:**")
            for ctrl in controles_data.get("controles", [])[:20]:
                icono = "+" if ctrl["efectividad"] >= 0.66 else "~" if ctrl["efectividad"] > 0 else "-"
                st.write(f"{icono} **{ctrl['codigo']}**: {ctrl['nombre']} - {ctrl['nivel']}")
        else:
            st.info("No hay controles identificados. Complete los cuestionarios primero.")
