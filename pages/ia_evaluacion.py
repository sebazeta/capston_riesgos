"""
Página: IA Evaluación
Análisis automatizado de amenazas, controles y riesgos MAGERIT.
"""
import pandas as pd
import streamlit as st
from services import (
    get_activos_por_evaluacion, get_activo, read_table,
    get_cuestionario, get_resultado_magerit,
    verificar_ollama_disponible, crear_evaluacion_manual,
    get_catalogo_amenazas, get_catalogo_controles,
    evaluar_activo_magerit, guardar_resultado_magerit,
    get_controles_existentes_detallados
)

# Importación condicional de validación IA
try:
    from components.ia_validation_ui import (
        render_boton_evaluar_bloqueado, verificar_ia_lista_para_evaluar
    )
    VALIDACION_IA_DISPONIBLE = True
except ImportError:
    VALIDACION_IA_DISPONIBLE = False


def render_ia_evaluacion(_styled_header):
    """Renderiza la página de evaluación con IA."""
    _styled_header("", "Evaluación con IA", "Análisis automatizado de amenazas, controles y riesgos MAGERIT")

    if not st.session_state.get("eval_actual"):
        st.error("**EVALUACIÓN REQUERIDA**")
        st.warning("Ve a la sección **Evaluaciones** y selecciona una evaluación primero.")
    else:
        st.success(f"Evaluación: **{st.session_state['eval_nombre']}**")

        st.markdown("""
        **Este módulo ejecutará una Evaluación de Riesgos usando IA:**
        - Impacto DIC será calculado desde las respuestas del cuestionario
        - La IA identificará amenazas del catálogo oficial (52 amenazas)
        - Se recomendarán controles ISO 27002:2022 (93 controles oficiales)
        - Se sugerirán salvaguardas para reducir el riesgo
        - Se calcularán Riesgo Inherente y Residual

        **Antes de evaluar:** Asegúrate de haber completado el cuestionario de cada activo.
        """)

        # Verificar Ollama
        ollama_ok, modelos_disponibles = verificar_ollama_disponible()

        if ollama_ok:
            st.success(f"Ollama conectado. Modelos: {', '.join(modelos_disponibles[:5])}")
            modelo_ia = st.selectbox("Modelo IA", modelos_disponibles, index=0, key="t3_modelo")
        else:
            st.warning("Ollama no disponible. Se usará modo manual.")
            modelo_ia = None

        # ===== ANÁLISIS COMPLETO CON UN SOLO BOTÓN =====
        try:
            from components.analisis_completo_ui import render_analisis_completo
            render_analisis_completo(
                st.session_state["eval_actual"],
                st.session_state["eval_nombre"],
                modelo_ia
            )
        except ImportError:
            pass

        # Verificar catálogos
        catalogo_amenazas = get_catalogo_amenazas()
        catalogo_controles = get_catalogo_controles()

        if not catalogo_amenazas or not catalogo_controles:
            st.error("Catálogos no cargados. Ejecuta: `python seed_catalogos_magerit.py`")
        else:
            st.caption(f"Catálogos: {len(catalogo_amenazas)} amenazas MAGERIT | {len(catalogo_controles)} controles ISO 27002")

            st.divider()

            # Obtener activos y sus estados
            activos = get_activos_por_evaluacion(st.session_state["eval_actual"])

            if activos.empty:
                st.warning("No hay activos. Crea uno en la sección Activos.")
            else:
                respuestas_df = read_table("RESPUESTAS")

                # Calcular estados
                datos_activos = []
                activos_listos = []
                activos_evaluados = []

                for _, activo in activos.iterrows():
                    activo_id = activo["ID_Activo"]

                    # Verificar cuestionario
                    cuest = get_cuestionario(st.session_state["eval_actual"], activo_id)
                    resp_activo = respuestas_df[
                        (respuestas_df["ID_Evaluacion"] == st.session_state["eval_actual"]) &
                        (respuestas_df["ID_Activo"] == activo_id)
                    ] if not respuestas_df.empty else pd.DataFrame()

                    # Verificar resultado MAGERIT existente
                    resultado_existente = get_resultado_magerit(st.session_state["eval_actual"], activo_id)

                    total_preg = len(cuest)
                    respondidas = len(resp_activo)

                    if resultado_existente:
                        estado = "Evaluado"
                        activos_evaluados.append(activo_id)
                        listo = False
                    elif total_preg == 0:
                        estado = "Sin cuestionario"
                        listo = False
                    elif respondidas < total_preg:
                        estado = f"Incompleto ({respondidas}/{total_preg})"
                        listo = False
                    else:
                        estado = "Listo para evaluar"
                        listo = True
                        activos_listos.append(activo_id)

                    datos_activos.append({
                        "ID": activo_id,
                        "Nombre": activo["Nombre_Activo"],
                        "Tipo": activo.get("Tipo_Activo", "N/A"),
                        "Estado": estado
                    })

                df_estados = pd.DataFrame(datos_activos)
                st.dataframe(df_estados, use_container_width=True, hide_index=True)

                st.divider()

                # Verificar si IA está validada (bloqueo de seguridad)
                ia_validada_para_evaluar = True
                mensaje_bloqueo = ""

                if VALIDACION_IA_DISPONIBLE:
                    ia_validada_para_evaluar, mensaje_bloqueo = verificar_ia_lista_para_evaluar()
                    if not ia_validada_para_evaluar:
                        st.warning(f"**Evaluación bloqueada:** {mensaje_bloqueo}")
                        st.info("Vaya a la sección **Validación IA** para validar la IA primero.")
                        render_boton_evaluar_bloqueado()

                if activos_listos and ollama_ok and ia_validada_para_evaluar:
                    st.info("Usa el botón **Ejecutar Análisis Completo** de arriba para evaluar todos los activos.")

                elif activos_listos and not ollama_ok:
                    st.markdown("### Evaluación Manual (Ollama no disponible)")

                    activo_manual = st.selectbox(
                        "Seleccionar activo",
                        activos_listos,
                        format_func=lambda x: f"{x} - {df_estados[df_estados['ID']==x]['Nombre'].values[0]}"
                    )

                    # Selector de amenazas manual
                    st.write("**Seleccionar amenazas aplicables:**")
                    amenazas_por_tipo = {}
                    for codigo, info in catalogo_amenazas.items():
                        tipo = info["tipo_amenaza"]
                        if tipo not in amenazas_por_tipo:
                            amenazas_por_tipo[tipo] = []
                        amenazas_por_tipo[tipo].append((codigo, info["amenaza"]))

                    amenazas_seleccionadas = []
                    for tipo, lista in amenazas_por_tipo.items():
                        with st.expander(f"{tipo}"):
                            for codigo, nombre in lista:
                                if st.checkbox(f"{codigo}: {nombre}", key=f"am_{codigo}"):
                                    amenazas_seleccionadas.append(codigo)

                    prob_manual = st.slider("Probabilidad general (1-5)", 1, 5, 3)
                    obs_manual = st.text_area("Observaciones")

                    if st.button("Guardar Evaluación Manual", type="primary") and amenazas_seleccionadas:
                        activo_data = get_activo(st.session_state["eval_actual"], activo_manual)
                        eval_manual = crear_evaluacion_manual(
                            activo_data, amenazas_seleccionadas, prob_manual, obs_manual
                        )

                        resultado = evaluar_activo_magerit(
                            st.session_state["eval_actual"],
                            activo_manual,
                            eval_manual["amenazas"],
                            eval_manual["probabilidad"],
                            eval_manual["observaciones"],
                            "manual"
                        )
                        guardar_resultado_magerit(resultado)
                        st.success(f"Evaluación guardada: {len(resultado.amenazas)} amenazas")
                        st.rerun()

                else:
                    st.info("No hay activos listos para evaluar. Completa los cuestionarios primero.")

                st.divider()

                # Mostrar resultados existentes
                if activos_evaluados:
                    st.markdown("### Resultados de Evaluación MAGERIT")

                    for activo_id in activos_evaluados:
                        resultado = get_resultado_magerit(st.session_state["eval_actual"], activo_id)
                        if resultado:
                            nombre = resultado.get("nombre_activo", activo_id)
                            nivel_inh = resultado.get("nivel_riesgo_inherente_global", "N/A")
                            nivel_res = resultado.get("nivel_riesgo_residual_global", "N/A")

                            with st.expander(f"{activo_id} - {nombre} | Inherente: {nivel_inh} | Residual: {nivel_res}"):
                                # Impacto DIC
                                impacto = resultado.get("impacto", {})
                                col1, col2, col3, col4 = st.columns(4)
                                col1.metric("Disponibilidad", impacto.get("disponibilidad", "-"))
                                col2.metric("Integridad", impacto.get("integridad", "-"))
                                col3.metric("Confidencialidad", impacto.get("confidencialidad", "-"))
                                col4.metric("Impacto Global", max(
                                    impacto.get("disponibilidad", 0),
                                    impacto.get("integridad", 0),
                                    impacto.get("confidencialidad", 0)
                                ))

                                st.caption(f"D: {impacto.get('justificacion_d', '')} | I: {impacto.get('justificacion_i', '')} | C: {impacto.get('justificacion_c', '')}")

                                # Riesgos
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric(
                                        "Riesgo Inherente",
                                        f"{resultado.get('riesgo_inherente_global', 0)} ({nivel_inh})"
                                    )
                                with col2:
                                    st.metric(
                                        "Riesgo Residual",
                                        f"{resultado.get('riesgo_residual_global', 0)} ({nivel_res})"
                                    )

                                # Controles existentes identificados
                                controles_exist = resultado.get("controles", [])
                                if controles_exist:
                                    st.markdown("**Controles existentes identificados:**")
                                    for ctrl_code in controles_exist[:8]:
                                        st.markdown(f"- `{ctrl_code}`")
                                    if len(controles_exist) > 8:
                                        st.caption(f"... y {len(controles_exist) - 8} más")
                                else:
                                    ctrl_detalle = get_controles_existentes_detallados(
                                        st.session_state["eval_actual"], activo_id
                                    )
                                    if ctrl_detalle.get("controles"):
                                        st.markdown("**Controles existentes identificados:**")
                                        resumen = ctrl_detalle.get("resumen", {})
                                        st.caption(f"Implementados: {resumen.get('implementados', 0)} | Parciales: {resumen.get('parciales', 0)}")
                                        for ctrl in ctrl_detalle["controles"][:5]:
                                            icono = "+" if ctrl["efectividad"] >= 0.66 else "~"
                                            st.markdown(f"- {icono} `{ctrl['codigo']}`: {ctrl['nombre'][:40]}...")
                                    else:
                                        st.caption("Complete el cuestionario para identificar controles")

                                # Amenazas
                                amenazas = resultado.get("amenazas", [])
                                if amenazas:
                                    st.markdown("**Amenazas identificadas:**")
                                    for am in amenazas:
                                        nivel = am.get("nivel_riesgo", "")
                                        st.markdown(f"- **{am.get('codigo', '')}**: {am.get('amenaza', '')} (R={am.get('riesgo_inherente', 0)} -> R.Res={am.get('riesgo_residual', 0)}) - {am.get('tratamiento', '')}")

                                # Controles recomendados
                                controles_rec = resultado.get("controles_recomendados_global", [])
                                if controles_rec:
                                    st.markdown("**Controles recomendados:**")
                                    for ctrl in controles_rec[:10]:
                                        st.markdown(f"- **{ctrl.get('codigo', '')}**: {ctrl.get('nombre', '')} ({ctrl.get('prioridad', '')})")

                                # Observaciones
                                if resultado.get("observaciones"):
                                    st.info(f"{resultado.get('observaciones')}")
