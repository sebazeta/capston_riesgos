"""
Página: Activos
Inventario de activos de información de la evaluación.
"""
import streamlit as st
from services import (
    get_activos_por_evaluacion, crear_activo, editar_activo,
    eliminar_activo, get_activo, validar_duplicado
)
from services.process_log_service import registrar_proceso_rapido

# Importación condicional de carga masiva
try:
    from components.carga_masiva_ui import render_carga_masiva
    CARGA_MASIVA_DISPONIBLE = True
except ImportError:
    CARGA_MASIVA_DISPONIBLE = False


def render_activos(_styled_header, calcular_estado_activo, actualizar_estados_automaticos):
    """Renderiza la página de gestión de activos."""
    _styled_header("", "Gestión de Activos", "Inventario de activos de información de la evaluación")

    # VALIDACIÓN OBLIGATORIA
    if st.session_state.get("eval_actual"):
        st.success(f"Evaluación: **{st.session_state['eval_nombre']}** (`{st.session_state['eval_actual']}`)")

        # Actualizar estados automáticos al entrar
        actualizar_estados_automaticos(st.session_state["eval_actual"])

    actcol1, actcol2 = st.columns([2, 1])

    # COLUMNA 1: Listado de activos
    with actcol1:
        st.subheader("Inventario de Activos")

        activos = get_activos_por_evaluacion(st.session_state["eval_actual"])

        if activos.empty:
            st.info("No hay activos. **Crea el primero**.")
        else:
            # Filtros
            fcol1, fcol2, fcol3 = st.columns(3)
            with fcol1:
                tipos = ["Todos"] + activos["Tipo_Activo"].dropna().unique().tolist()
                tipo_filter = st.selectbox("Tipo", tipos, key="t1_tipo")
            with fcol2:
                ubicaciones = ["Todas"] + activos["Ubicacion"].dropna().unique().tolist()
                ubic_filter = st.selectbox("Ubicación", ubicaciones, key="t1_ubic")
            with fcol3:
                estados = ["Todos"] + activos["Estado"].dropna().unique().tolist()
                estado_filter = st.selectbox("Estado", estados, key="t1_estado")

            # Aplicar filtros
            activos_filtrados = activos.copy()
            if tipo_filter != "Todos":
                activos_filtrados = activos_filtrados[activos_filtrados["Tipo_Activo"] == tipo_filter]
            if ubic_filter != "Todas":
                activos_filtrados = activos_filtrados[activos_filtrados["Ubicacion"] == ubic_filter]
            if estado_filter != "Todos":
                activos_filtrados = activos_filtrados[activos_filtrados["Estado"] == estado_filter]

            # Tabla con estados coloreados
            st.dataframe(
                activos_filtrados[["ID_Activo", "Nombre_Activo", "Tipo_Activo", "Ubicacion", "Estado", "Tipo_Servicio"]],
                use_container_width=True,
                height=350
            )
            st.caption(f"Mostrando {len(activos_filtrados)} de {len(activos)} activos")

            # Acciones
            if not activos_filtrados.empty:
                st.markdown("### Acciones")
                activo_selec = st.selectbox(
                    "Seleccionar activo",
                    activos_filtrados["ID_Activo"].tolist(),
                    key="t1_activo_selec"
                )

                acol1, acol2 = st.columns(2)

                with acol1:
                    if st.button("Editar", key="t1_editar"):
                        st.session_state["editar_activo"] = activo_selec
                        st.rerun()

                with acol2:
                    if st.button("Eliminar", key="t1_eliminar"):
                        st.session_state["confirmar_eliminar"] = activo_selec
                        st.rerun()

                # Confirmación de eliminación
                if st.session_state.get("confirmar_eliminar"):
                    st.warning(f"¿Eliminar **{st.session_state['confirmar_eliminar']}**?")
                    ccol1, ccol2 = st.columns(2)
                    with ccol1:
                        if st.button("Sí, eliminar", key="t1_confirmar_si"):
                            exito, msg = eliminar_activo(
                                st.session_state["eval_actual"],
                                st.session_state["confirmar_eliminar"]
                            )
                            if exito:
                                st.success(msg)
                                st.session_state["confirmar_eliminar"] = None
                                actualizar_estados_automaticos(st.session_state["eval_actual"])
                                st.rerun()
                            else:
                                st.error(msg)
                    with ccol2:
                        if st.button("Cancelar", key="t1_confirmar_no"):
                            st.session_state["confirmar_eliminar"] = None
                            st.rerun()

                # Mostrar estado automático
                activo_data = get_activo(st.session_state["eval_actual"], activo_selec)
                estado_actual = calcular_estado_activo(st.session_state["eval_actual"], activo_selec)

                st.info(f"**Estado automático:** `{estado_actual}`")

                # Explicación del estado
                if estado_actual == "Pendiente":
                    st.caption("Sin cuestionario generado")
                elif estado_actual == "Incompleto":
                    st.caption("Cuestionario iniciado pero no completo")
                elif estado_actual == "Completo":
                    st.caption("Cuestionario completo, listo para evaluar con IA")
                elif estado_actual == "Evaluado":
                    st.caption("Evaluado con IA")

    # COLUMNA 2: Crear/Editar activo
    with actcol2:
        if st.session_state.get("editar_activo"):
            st.subheader("Editar Activo")
            activo_data = get_activo(st.session_state["eval_actual"], st.session_state["editar_activo"])

            with st.form("form_editar_activo"):
                nombre_act = st.text_input("Nombre *", value=activo_data.get("Nombre_Activo", ""))
                tipo_act = st.selectbox(
                    "Tipo *",
                    ["Servidor Físico", "Servidor Virtual"],
                    index=0 if activo_data.get("Tipo_Activo") == "Servidor Físico" else 1
                )
                ubicacion = st.selectbox(
                    "Ubicación *",
                    ["UdlaPark", "Granados"],
                    index=0 if activo_data.get("Ubicacion") == "UdlaPark" else 1
                )
                propietario = st.selectbox(
                    "Propietario *",
                    ["Infraestructura", "Seguridad de la Información", "Soporte"],
                    index=["Infraestructura", "Seguridad de la Información", "Soporte"].index(
                        activo_data.get("Propietario", "Infraestructura")
                    )
                )
                tipo_servicio = st.selectbox(
                    "Tipo Servicio *",
                    ["Base de datos", "Servidor web", "Servidor aplicaciones",
                     "Firewall", "Switch", "Router", "Storage", "Backup", "Otro"]
                )
                app_critica = st.radio(
                    "Aplicación Crítica",
                    ["Sí", "No"],
                    index=0 if activo_data.get("App_Critica") == "Sí" else 1,
                    horizontal=True
                )

                submitted_edit = st.form_submit_button("Guardar", type="primary")

            if submitted_edit:
                datos = {
                    "Nombre_Activo": nombre_act,
                    "Tipo_Activo": tipo_act,
                    "Ubicacion": ubicacion,
                    "Propietario": propietario,
                    "Tipo_Servicio": tipo_servicio,
                    "App_Critica": app_critica
                }
                exito, msg = editar_activo(
                    st.session_state["eval_actual"],
                    st.session_state["editar_activo"],
                    datos
                )
                if exito:
                    st.success(msg)
                    st.session_state["editar_activo"] = None
                    actualizar_estados_automaticos(st.session_state["eval_actual"])
                    st.rerun()
                else:
                    st.error(msg)

            if st.button("Cancelar", key="t1_cancelar_edit"):
                st.session_state["editar_activo"] = None
                st.rerun()

        else:
            st.subheader("Crear Activo")

            # Botón para carga masiva
            if CARGA_MASIVA_DISPONIBLE:
                if st.button("Carga Masiva (JSON/Excel)", key="t1_btn_carga_masiva", type="secondary"):
                    st.session_state["mostrar_carga_masiva"] = True
                    st.rerun()

            with st.form("form_crear_activo"):
                nombre_act = st.text_input("Nombre *", placeholder="Ej: Servidor DB Principal")
                tipo_act = st.selectbox("Tipo *", ["Servidor Físico", "Servidor Virtual"])
                ubicacion = st.selectbox("Ubicación *", ["UdlaPark", "Granados"])
                propietario = st.selectbox(
                    "Propietario *",
                    ["Infraestructura", "Seguridad de la Información", "Soporte"]
                )
                tipo_servicio = st.selectbox(
                    "Tipo Servicio *",
                    ["Base de datos", "Servidor web", "Servidor aplicaciones",
                     "Firewall", "Switch", "Router", "Storage", "Backup", "Otro"]
                )
                app_critica = st.radio("Aplicación Crítica", ["Sí", "No"], horizontal=True)

                submitted_create = st.form_submit_button("Crear", type="primary")

            if submitted_create:
                if not nombre_act:
                    st.error("Nombre obligatorio")
                else:
                    # Validar duplicados
                    es_duplicado, msg_dup = validar_duplicado(
                        st.session_state["eval_actual"],
                        nombre_act,
                        ubicacion,
                        tipo_servicio
                    )

                    if es_duplicado:
                        st.error(f"{msg_dup}")
                    else:
                        datos = {
                            "Nombre_Activo": nombre_act,
                            "Tipo_Activo": tipo_act,
                            "Ubicacion": ubicacion,
                            "Propietario": propietario,
                            "Tipo_Servicio": tipo_servicio,
                            "App_Critica": app_critica
                        }

                        exito, msg, nuevo_id = crear_activo(st.session_state["eval_actual"], datos)
                        if exito:
                            registrar_proceso_rapido(st.session_state["eval_actual"],
                                "crear_activo", "INVENTARIO",
                                f"Activo '{nombre_act}' creado (ID: {nuevo_id})")
                            st.success(msg)
                            actualizar_estados_automaticos(st.session_state["eval_actual"])
                            st.rerun()
                        else:
                            st.error(msg)

    # ===== SECCIÓN DE CARGA MASIVA (Modal-like) =====
    if st.session_state.get("mostrar_carga_masiva") and CARGA_MASIVA_DISPONIBLE:
        st.divider()

        col_header1, col_header2 = st.columns([6, 1])
        with col_header1:
            st.markdown("## Carga Masiva de Activos")
        with col_header2:
            if st.button("Cerrar", key="t1_cerrar_carga_masiva"):
                st.session_state["mostrar_carga_masiva"] = False
                st.rerun()

        render_carga_masiva(
            st.session_state["eval_actual"],
            st.session_state["eval_nombre"]
        )

    # ===== SECCIÓN VIDA ÚTIL =====
    if st.session_state.get("eval_actual"):
        st.divider()
        try:
            from components.vida_util_ui import render_vida_util
            render_vida_util(st.session_state["eval_actual"], st.session_state["eval_nombre"])
        except ImportError:
            pass
