"""
Página: Cuestionarios
Responder las preguntas de seguridad para cada activo.
"""
import datetime as dt
import pandas as pd
import streamlit as st
from services import (
    get_activos_por_evaluacion, get_activo, read_sheet,
    get_cuestionario, generar_cuestionario, guardar_respuestas,
    verificar_cuestionario_completo, invalidar_analisis_ia,
    verificar_respuestas_existentes
)
from services.process_log_service import registrar_proceso_rapido


def render_cuestionarios(_styled_header, actualizar_estados_automaticos):
    """Renderiza la página de cuestionarios."""
    _styled_header("", "Cuestionarios", "Responde las preguntas de seguridad para cada activo")

    if not st.session_state.get("eval_actual"):
        st.error("**EVALUACIÓN REQUERIDA**")
        st.warning("Ve a la sección **Evaluaciones** y selecciona una evaluación primero.")
    else:
        st.success(f"Evaluación: **{st.session_state['eval_nombre']}**")

        activos = get_activos_por_evaluacion(st.session_state["eval_actual"])

        if activos.empty:
            st.warning("No hay activos registrados. Ve a **Activos** para crear uno.")
        else:
            # ===== Selector de activo con estado =====
            st.markdown("### Seleccionar Activo")

            # Crear diccionario para format_func y calcular estados
            activos_dict = dict(zip(activos["ID_Activo"], activos["Nombre_Activo"]))

            # Mostrar tabla de activos con estado
            datos_activos = []
            for _, activo in activos.iterrows():
                activo_id_temp = activo["ID_Activo"]
                cuest_temp = get_cuestionario(st.session_state["eval_actual"], activo_id_temp)
                resp_temp = read_sheet("RESPUESTAS")
                resp_activo = resp_temp[
                    (resp_temp["ID_Evaluacion"] == st.session_state["eval_actual"]) &
                    (resp_temp["ID_Activo"] == activo_id_temp)
                ] if not resp_temp.empty else pd.DataFrame()

                total_preg = len(cuest_temp)
                respondidas = len(resp_activo)

                if total_preg == 0:
                    estado = "Sin cuestionario"
                elif respondidas == 0:
                    estado = "Pendiente"
                elif respondidas < total_preg:
                    estado = f"En proceso ({respondidas}/{total_preg})"
                else:
                    estado = "Completado"

                datos_activos.append({
                    "ID": activo_id_temp,
                    "Nombre": activo["Nombre_Activo"],
                    "Tipo": activo.get("Tipo_Activo", "N/A"),
                    "Estado": estado
                })

            df_estados = pd.DataFrame(datos_activos)
            st.dataframe(df_estados, use_container_width=True, hide_index=True)

            # Selector
            activo_id = st.selectbox(
                "Seleccionar activo para responder cuestionario:",
                activos["ID_Activo"].tolist(),
                key="t2_activo",
                format_func=lambda x: f"{x} - {activos_dict.get(x, 'N/A')}"
            )

            activo_data = get_activo(st.session_state["eval_actual"], activo_id)

            st.divider()

            # ===== Verificar/Generar cuestionario automáticamente =====
            cuestionario_df = get_cuestionario(st.session_state["eval_actual"], activo_id)
            cuestionario_error = False

            if cuestionario_df.empty:
                with st.spinner(f"Cargando cuestionario del banco {activo_data.get('Tipo_Activo', 'N/A')}..."):
                    try:
                        exito, mensaje, num_preguntas = generar_cuestionario(
                            eval_id=st.session_state["eval_actual"],
                            activo=activo_data,
                            model=""
                        )
                        if exito:
                            actualizar_estados_automaticos(st.session_state["eval_actual"])
                            st.rerun()
                        else:
                            st.error(f"{mensaje}")
                            cuestionario_error = True
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        cuestionario_error = True

            if not cuestionario_error and not cuestionario_df.empty:
                # ===== Cargar respuestas existentes =====
                respuestas_df = read_sheet("RESPUESTAS")
                respuestas_existentes = respuestas_df[
                    (respuestas_df["ID_Evaluacion"] == st.session_state["eval_actual"]) &
                    (respuestas_df["ID_Activo"] == activo_id)
                ] if not respuestas_df.empty else pd.DataFrame()

                total_preguntas = len(cuestionario_df)
                respondidas = len(respuestas_existentes)
                progreso = int((respondidas / total_preguntas) * 100) if total_preguntas > 0 else 0

                # ===== Estado y progreso =====
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Preguntas", total_preguntas)
                with col2:
                    st.metric("Respondidas", respondidas)
                with col3:
                    if respondidas == 0:
                        st.warning("Pendiente")
                    elif respondidas < total_preguntas:
                        st.info("En proceso")
                    else:
                        st.success("Completado")

                st.progress(min(progreso / 100, 1.0))

                st.divider()

                # ===== Verificar si ya existen respuestas completas =====
                cuestionario_ya_guardado = verificar_respuestas_existentes(st.session_state["eval_actual"], activo_id)

                if cuestionario_ya_guardado:
                    st.success("**Cuestionario completado y guardado**")
                    st.info("Las respuestas ya fueron registradas para este activo. Puedes ir a **IA Evaluación**.")

                    # Mostrar respuestas en modo lectura
                    st.markdown(f"### Respuestas Guardadas - {activo_data.get('Tipo_Activo', 'Activo')}")

                    for idx, row in respuestas_existentes.iterrows():
                        with st.expander(f"**{row.get('ID_Pregunta', 'N/A')}** - {row.get('Bloque', '')}", expanded=False):
                            st.write(f"**Pregunta:** {row.get('Pregunta', 'N/A')}")
                            st.write(f"**Respuesta:** {row.get('Respuesta', 'N/A')}")
                            st.caption(f"Valor: {row.get('Valor_Numerico', 'N/A')} | Peso: {row.get('Peso', 'N/A')} | Dimensión: {row.get('Dimension', 'N/A')}")

                else:
                    # ===== Formulario de respuestas =====
                    st.markdown(f"### Responder Cuestionario - {activo_data.get('Tipo_Activo', 'Activo')}")

                    with st.form("form_cuestionario"):
                        respuestas = {}

                        # Agrupar por dimensión
                        dimensiones = {"D": "Disponibilidad", "I": "Integridad", "C": "Confidencialidad"}

                        for dim_code, dim_name in dimensiones.items():
                            preguntas_dim = cuestionario_df[cuestionario_df["Dimension"] == dim_code]
                            if not preguntas_dim.empty:
                                st.markdown(f"#### {dim_name}")

                                for idx, row in preguntas_dim.iterrows():
                                    id_pregunta = row.get('ID_Pregunta', f'P{idx}')
                                    pregunta_texto = row.get('Pregunta', 'N/A')
                                    bloque = row.get('Bloque', '')

                                    # Obtener las 4 opciones
                                    opciones = [
                                        str(row.get('Opcion_1', '')),
                                        str(row.get('Opcion_2', '')),
                                        str(row.get('Opcion_3', '')),
                                        str(row.get('Opcion_4', ''))
                                    ]
                                    opciones = [o for o in opciones if o and o != 'nan']

                                    st.markdown(f"**{id_pregunta}.** {pregunta_texto}")
                                    if bloque:
                                        st.caption(f"{bloque}")

                                    # Buscar respuesta existente
                                    resp_existente = respuestas_existentes[
                                        respuestas_existentes["ID_Pregunta"].astype(str) == str(id_pregunta)
                                    ] if not respuestas_existentes.empty else pd.DataFrame()

                                    valor_inicial = ""
                                    if not resp_existente.empty:
                                        valor_inicial = str(resp_existente.iloc[0]["Respuesta"])

                                    # Mostrar radio buttons con las 4 opciones
                                    if len(opciones) >= 4:
                                        # Determinar índice inicial
                                        idx_inicial = 3
                                        if valor_inicial:
                                            try:
                                                idx_inicial = opciones.index(valor_inicial)
                                            except ValueError:
                                                idx_inicial = 3
                                        else:
                                            bloque_upper = str(bloque).upper()
                                            if "IMPACTO" in bloque_upper or bloque_upper.startswith("A"):
                                                idx_inicial = 3
                                            elif "CONTINUIDAD" in bloque_upper or bloque_upper.startswith("B"):
                                                idx_inicial = 0
                                            elif "CONTROL" in bloque_upper or bloque_upper.startswith("C"):
                                                idx_inicial = 0
                                            elif "EXPOSICION" in bloque_upper or "AMENAZA" in bloque_upper or bloque_upper.startswith("D"):
                                                idx_inicial = 3
                                            elif "CAPACIDAD" in bloque_upper or bloque_upper.startswith("E"):
                                                idx_inicial = 0
                                            else:
                                                idx_inicial = 3

                                        opciones_formateadas = [f"{i+1}. {op}" for i, op in enumerate(opciones)]

                                        resp = st.radio(
                                            f"Respuesta {id_pregunta}",
                                            options=opciones_formateadas,
                                            index=idx_inicial,
                                            key=f"t2_resp_{id_pregunta}",
                                            horizontal=False,
                                            label_visibility="collapsed"
                                        )
                                        respuestas[id_pregunta] = resp.split(". ", 1)[1] if ". " in resp else resp
                                    else:
                                        respuestas[id_pregunta] = st.text_area(
                                            f"Respuesta {id_pregunta}",
                                            value=valor_inicial,
                                            key=f"t2_resp_{id_pregunta}",
                                            label_visibility="collapsed",
                                            height=80
                                        )

                                    st.caption(f"Peso: {row.get('Peso', 'N/A')} | Dimensión: {dim_code}")
                                    st.divider()

                        submitted = st.form_submit_button("Guardar Respuestas", type="primary", use_container_width=True)

                    if submitted:
                        respuestas_validas = {k: v for k, v in respuestas.items() if v and str(v).strip()}

                        if not respuestas_validas:
                            st.error("Debes responder al menos una pregunta")
                        else:
                            fecha_cuestionario = cuestionario_df.iloc[0].get("Fecha_Version", dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

                            respuestas_lista = []
                            for id_preg, respuesta_texto in respuestas_validas.items():
                                fila_preg = cuestionario_df[cuestionario_df["ID_Pregunta"] == id_preg]
                                if not fila_preg.empty:
                                    row = fila_preg.iloc[0]
                                    valor_numerico = 1
                                    for i, opt in enumerate(['Opcion_1', 'Opcion_2', 'Opcion_3', 'Opcion_4']):
                                        if str(row.get(opt, '')) == respuesta_texto:
                                            valor_numerico = i + 1
                                            break

                                    respuestas_lista.append({
                                        "ID_Pregunta": id_preg,
                                        "Pregunta": row.get("Pregunta", ""),
                                        "Respuesta": respuesta_texto,
                                        "Valor_Numerico": valor_numerico,
                                        "Peso": row.get("Peso", 3),
                                        "Dimension": row.get("Dimension", "I"),
                                        "Bloque": row.get("Bloque", "")
                                    })

                            # Verificar análisis previo
                            analisis_previo = read_sheet("ANALISIS_RIESGO")
                            tenia_analisis = not analisis_previo[
                                (analisis_previo["ID_Evaluacion"] == st.session_state["eval_actual"]) &
                                (analisis_previo["ID_Activo"] == activo_id)
                            ].empty if not analisis_previo.empty else False

                            exito = guardar_respuestas(
                                st.session_state["eval_actual"],
                                activo_id,
                                fecha_cuestionario,
                                respuestas_lista
                            )

                            if exito:
                                registrar_proceso_rapido(st.session_state["eval_actual"],
                                    "guardar_respuestas", "CUESTIONARIO",
                                    f"Cuestionario de {activo_id}: {len(respuestas_validas)} respuestas")
                                st.success(f"{len(respuestas_validas)} respuestas guardadas")

                                if tenia_analisis:
                                    invalidar_analisis_ia(st.session_state["eval_actual"], activo_id)
                                    st.warning("Respuestas modificadas invalidan el análisis IA anterior.")

                                actualizar_estados_automaticos(st.session_state["eval_actual"])

                                if verificar_cuestionario_completo(st.session_state["eval_actual"], activo_id):
                                    st.success("Cuestionario completo. Puedes ir a **IA Evaluación**.")

                                st.rerun()
                            else:
                                st.warning("Ya existen respuestas guardadas para este activo. No se permiten duplicados.")
