"""
Página: Validación IA
Verifica que Ollama esté listo para evaluaciones confiables.
"""
import traceback
import streamlit as st

# Importación condicional
try:
    from components.ia_validation_ui import render_boton_evaluar_bloqueado
    VALIDACION_IA_DISPONIBLE = True
except ImportError:
    VALIDACION_IA_DISPONIBLE = False


def render_validacion_ia(_styled_header):
    """Renderiza la página de validación de IA."""
    _styled_header("", "Validación de IA Local", "Verifica que Ollama esté listo para evaluaciones confiables")

    try:
        from services.ia_validation_service import obtener_estado_ia, verificar_ollama_local
        from services.knowledge_base_service import obtener_resumen_catalogos

        st.markdown("""
        Este módulo valida que la IA funciona **100% local** con Ollama y sin conexión a Internet.
        """)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Estado Actual")
            ia_ready, last_validation, canary_nonce = obtener_estado_ia()

            if ia_ready:
                st.success("IA Validada y Lista")
                st.info(f"Última validación: {last_validation}")
            else:
                st.warning("IA No Validada - Ejecute validación")

            st.subheader("Ollama Local")
            is_local, endpoint, modelos, error = verificar_ollama_local()

            if is_local:
                st.success(f"Conectado: {endpoint}")
                st.caption(f"Modelos: {', '.join(modelos[:5])}")
            else:
                st.error(f"No conectado: {error}")

        with col2:
            st.subheader("Knowledge Base")
            resumen = obtener_resumen_catalogos()

            st.metric("Amenazas MAGERIT", resumen["total_amenazas"])
            st.metric("Controles ISO 27002", resumen["total_controles"])

            if resumen["total_amenazas"] >= 50 and resumen["total_controles"] >= 90:
                st.success("Catálogos cargados correctamente")
            else:
                st.warning("Catálogos incompletos")

        st.divider()

        # Botón de validación
        if VALIDACION_IA_DISPONIBLE:
            from services.ia_validation_service import ejecutar_validacion_completa
            if st.button("Ejecutar Validación Completa", type="primary", key="btn_validar_ia"):
                with st.spinner("Ejecutando validación..."):
                    resultado = ejecutar_validacion_completa()
                if resultado.ia_ready:
                    st.success("IA VALIDADA Y LISTA")
                else:
                    st.error("Validación fallida")
                    for err in resultado.errors:
                        st.write(f"- {err}")
                st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")
        st.code(traceback.format_exc())
