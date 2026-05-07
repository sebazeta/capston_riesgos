"""
Pagina: Evaluaciones
Listado de evaluaciones de riesgo existentes (consulta y eliminacion).
La seleccion/activacion de evaluaciones se realiza desde el sidebar.
"""
import streamlit as st
from services import (
    get_evaluaciones
)
from services.process_log_service import registrar_proceso_rapido


def render_evaluaciones(_styled_header):
    """Renderiza la pagina de gestion de evaluaciones."""
    _styled_header("", "Gestion de Evaluaciones", "Consulta y administra las evaluaciones de riesgo")
    st.markdown("""
    Las **Evaluaciones** son el contenedor principal del sistema. Todo activo, cuestionario
    y analisis debe pertenecer a una evaluacion.
    Para activar una evaluacion, usa el selector en la barra lateral.""")

    evals = get_evaluaciones()

    # Listado de evaluaciones
    st.subheader("Evaluaciones Existentes")

    if evals.empty:
        st.info("No hay evaluaciones creadas. **Crea la primera evaluacion** desde el menu Nueva Evaluacion.")
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

        # Eliminacion de evaluaciones
        if not evals_filtradas.empty:
            st.markdown("---")
            st.subheader("Eliminar Evaluacion")

            del_col1, del_col2 = st.columns([3, 1])
            with del_col1:
                eval_selec = st.selectbox(
                    "Seleccionar evaluacion a eliminar",
                    evals_filtradas["ID_Evaluacion"].tolist(),
                    key="t0_eval_eliminar",
                    format_func=lambda x: f"{x} - {evals[evals['ID_Evaluacion']==x].iloc[0]['Nombre']}"
                )
            with del_col2:
                st.write("")  # Espaciador
                st.write("")
                if st.button("Eliminar", key="t0_eliminar", type="secondary", use_container_width=True):
                    st.session_state["eval_a_eliminar"] = eval_selec

            # Dialogo de confirmacion para eliminar
            if st.session_state.get("eval_a_eliminar") == eval_selec:
                st.warning(f"Seguro que deseas eliminar la evaluacion **{eval_selec}**? Esta accion eliminara todos sus activos, cuestionarios y resultados.")
                dcol1, dcol2 = st.columns(2)
                with dcol1:
                    if st.button("Si, eliminar", key="t0_confirmar_elim", type="primary"):
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
                        st.success(f"Evaluacion **{eval_selec}** eliminada correctamente")
                        st.rerun()
                with dcol2:
                    if st.button("Cancelar", key="t0_cancelar_elim"):
                        st.session_state["eval_a_eliminar"] = None
                        st.rerun()