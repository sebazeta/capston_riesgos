"""
Página: Evaluaciones
Gestión de evaluaciones de riesgo (crear, seleccionar, eliminar).
"""
import streamlit as st
from services import (
    get_evaluaciones
)
from services.process_log_service import registrar_proceso_rapido


def render_evaluaciones(_styled_header):
    """Renderiza la página de gestión de evaluaciones."""
    _styled_header("", "Gestión de Evaluaciones", "Selecciona y administra las evaluaciones de riesgo")
    st.markdown("""
    Las **Evaluaciones** son el contenedor principal del sistema. Todo activo, cuestionario
    y análisis debe pertenecer a una evaluación.""")

    evals = get_evaluaciones()

    # Listado de evaluaciones
    st.subheader("Evaluaciones Existentes")

    if evals.empty:
        st.info("No hay evaluaciones creadas. **Crea la primera evaluación**.")
    else:
        # Filtros
        fcol1, fcol2 = st.columns(2)
        with fcol1:
            buscar = st.text_input("Buscar", placeholder="Nombre o ID...", key="t0_buscar")
        with fcol2:
            filtro_estado = st.selectbox(
                "Filtrar por estado",
                ["Todos", "En Progreso", "Completada", "Archivada"],
                key="t0_filtro_estado"
            )

        # Aplicar filtros
        evals_filtradas = evals.copy()
        if filtro_estado != "Todos":
            evals_filtradas = evals_filtradas[evals_filtradas["Estado"] == filtro_estado]
        if buscar:
            evals_filtradas = evals_filtradas[
                evals_filtradas["ID_Evaluacion"].str.contains(buscar, case=False, na=False) |
                evals_filtradas["Nombre"].str.contains(buscar, case=False, na=False)
            ]

        # Tabla (usar solo columnas existentes)
        columnas_mostrar = ["ID_Evaluacion", "Nombre", "Estado"]
        if "Fecha_Creacion" in evals_filtradas.columns:
            columnas_mostrar.insert(2, "Fecha_Creacion")
        if "Responsable" in evals_filtradas.columns:
            columnas_mostrar.insert(3, "Responsable")

        st.dataframe(
            evals_filtradas[columnas_mostrar],
            use_container_width=True,
            height=300
        )

        # Seleccionar y trabajar
        if not evals_filtradas.empty:
            st.markdown("---")

            scol1, scol2, scol3 = st.columns([2, 1, 1])
            with scol1:
                eval_selec = st.selectbox(
                    "Seleccionar evaluación",
                    evals_filtradas["ID_Evaluacion"].tolist(),
                    key="t0_eval_accion",
                    format_func=lambda x: f"{x} - {evals[evals['ID_Evaluacion']==x].iloc[0]['Nombre']}"
                )

            eval_data = evals[evals["ID_Evaluacion"] == eval_selec].iloc[0]
            eval_name = eval_data["Nombre"]

            with scol2:
                st.write("")  # Espaciador
                st.write("")
                if st.button("**Activar**", key="t0_trabajar", type="primary", use_container_width=True):
                    st.session_state["eval_actual"] = eval_selec
                    st.session_state["eval_nombre"] = eval_name
                    st.success(f"Evaluación **{eval_selec}** activada")
                    st.rerun()
            with scol3:
                st.write("")
                st.write("")
                if st.button("Eliminar", key="t0_eliminar", type="secondary", use_container_width=True):
                    st.session_state["eval_a_eliminar"] = eval_selec

            st.markdown("---")
            st.markdown("#### Acciones Rápidas")
            st.markdown(f"Accede directamente a los módulos para la evaluación **{eval_selec}**:")

            c1, c2, c3, c4, c5, c6 = st.columns(6)
            
            def _navigate_to(page_name):
                st.session_state["eval_actual"] = eval_selec
                st.session_state["eval_nombre"] = eval_name
                st.session_state["nav_pagina"] = page_name
                st.rerun()

            with c1:
                if st.button("🖴 Activos", key="btn_activos", use_container_width=True):
                    _navigate_to("Activos")
            with c2:
                if st.button("📋 Cuest.", key="btn_cuestionarios", use_container_width=True):
                    _navigate_to("Cuestionarios")
            with c3:
                if st.button("📉 Degrad.", key="btn_degradacion", use_container_width=True):
                    _navigate_to("Degradación")
            with c4:
                if st.button("🛡️ Vuln.", key="btn_vuln", use_container_width=True):
                    _navigate_to("Vulnerabilidades")
            with c5:
                if st.button("🏅 Madurez", key="btn_madurez", use_container_width=True):
                    _navigate_to("Madurez")
            with c6:
                if st.button("🩹 Tratam.", key="btn_tratamiento", use_container_width=True):
                    _navigate_to("Tratamiento")

            # Diálogo de confirmación para eliminar
            if st.session_state.get("eval_a_eliminar") == eval_selec:
                st.warning(f"¿Seguro que deseas eliminar la evaluación **{eval_selec}**? Esta acción eliminará todos sus activos, cuestionarios y resultados.")
                dcol1, dcol2 = st.columns(2)
                with dcol1:
                    if st.button("Sí, eliminar", key="t0_confirmar_elim", type="primary"):
                        from services.database_service import delete_rows
                        # Eliminar datos relacionados (todas las tablas)
                        tablas_a_limpiar = [
                            "RESPUESTAS", "CUESTIONARIOS", "IMPACTO_ACTIVOS",
                            "RESULTADOS_MAGERIT", "ANALISIS_RIESGO",
                            "IDENTIFICACION_VALORACION", "VULNERABILIDADES_AMENAZAS",
                            "RIESGO_AMENAZA", "MAPA_RIESGOS", "RIESGO_ACTIVOS",
                            "SALVAGUARDAS", "RESULTADOS_MADUREZ",
                            "HISTORIAL_REEVALUACIONES", "RESULTADOS_CONCENTRACION",
                            "RIESGO_HEREDADO", "IA_RESULTADOS_AVANZADOS",
                            "VULNERABILIDADES_ACTIVO", "TRATAMIENTO_RIESGOS",
                            "HISTORIAL_EVALUACIONES", "LOG_PROCESOS",
                            "INVENTARIO_ACTIVOS", "EVALUACIONES",
                        ]
                        for tabla in tablas_a_limpiar:
                            try:
                                delete_rows(tabla, {"ID_Evaluacion": eval_selec})
                            except Exception:
                                try:
                                    delete_rows(tabla, {"id_evaluacion": eval_selec})
                                except Exception:
                                    pass  # Tabla no existe o no tiene esa columna
                        # Limpiar estado
                        if st.session_state.get("eval_actual") == eval_selec:
                            st.session_state["eval_actual"] = None
                            st.session_state["eval_nombre"] = None
                        st.session_state["eval_a_eliminar"] = None
                        st.success(f"Evaluación **{eval_selec}** eliminada correctamente")
                        st.rerun()
                with dcol2:
                    if st.button("Cancelar", key="t0_cancelar_elim"):
                        st.session_state["eval_a_eliminar"] = None
                        st.rerun()