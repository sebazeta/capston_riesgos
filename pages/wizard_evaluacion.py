"""
Wizard: Nueva Evaluación — Flujo Guiado en 4 Pasos
====================================================
Paso 1: Crear evaluación
Paso 2: Agregar activos
Paso 3: Responder cuestionarios por activo
Paso 4: Ejecutar evaluación con IA
"""
import datetime as dt
import pandas as pd
import streamlit as st
from services import (
    crear_evaluacion, get_evaluaciones,
    get_activos_por_evaluacion, crear_activo, eliminar_activo, get_activo,
    validar_duplicado,
    get_cuestionario, generar_cuestionario, guardar_respuestas,
    verificar_cuestionario_completo, verificar_respuestas_existentes,
    verificar_ollama_disponible,
)
from services.database_service import read_table, update_row
from services.process_log_service import registrar_proceso_rapido


# ─── CSS del stepper ────────────────────────────────────────────────────────
STEPPER_CSS = """
<style>
.wizard-stepper {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0;
    margin: 1.2rem 0 1.5rem 0;
    padding: 0 1rem;
}
.wizard-step {
    display: flex;
    align-items: center;
    gap: 0;
}
.wizard-node {
    width: 38px; height: 38px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 0.85rem;
    border: 2px solid #2a3a4a;
    color: #5a7a8a;
    background: #0c1a2e;
    transition: all 0.3s;
    flex-shrink: 0;
}
.wizard-node.active {
    border-color: #2ec4b6;
    color: #e0eff8;
    background: rgba(46,196,182,0.15);
    box-shadow: 0 0 12px rgba(46,196,182,0.25);
}
.wizard-node.done {
    border-color: #2ec4b6;
    color: #0c1a2e;
    background: #2ec4b6;
}
.wizard-label {
    font-size: 0.7rem;
    color: #5a7a8a;
    text-align: center;
    max-width: 90px;
    margin-top: 0.3rem;
    line-height: 1.2;
}
.wizard-label.active { color: #e0eff8; font-weight: 600; }
.wizard-label.done   { color: #2ec4b6; }
.wizard-line {
    width: 60px; height: 2px;
    background: #2a3a4a;
    margin: 0 4px;
    flex-shrink: 0;
}
.wizard-line.done { background: #2ec4b6; }
.wizard-col {
    display: flex; flex-direction: column; align-items: center;
}
</style>
"""

STEP_LABELS = ["Evaluación", "Activos", "Cuestionarios", "IA Evaluación"]


def _render_stepper(current: int):
    """Renderiza el stepper visual. current = 1..4"""
    html_parts = ['<div class="wizard-stepper">']
    for i, label in enumerate(STEP_LABELS, 1):
        cls_node = "done" if i < current else ("active" if i == current else "")
        cls_label = "done" if i < current else ("active" if i == current else "")
        cls_line = "done" if i < current else ""

        html_parts.append(f"""
        <div class="wizard-col">
            <div class="wizard-node {cls_node}">{i if i >= current else "✓"}</div>
            <div class="wizard-label {cls_label}">{label}</div>
        </div>""")
        if i < len(STEP_LABELS):
            html_parts.append(f'<div class="wizard-line {cls_line}"></div>')

    html_parts.append("</div>")
    st.markdown(STEPPER_CSS + "\n".join(html_parts), unsafe_allow_html=True)


def _guardar_fase(eval_id: str, fase: int):
    """Persiste la fase actual del wizard en la BD."""
    try:
        update_row("EVALUACIONES", {"Fase_Wizard": fase}, {"ID_Evaluacion": eval_id})
    except Exception:
        pass


def _cargar_fase(eval_id: str) -> int:
    """Carga la fase guardada de una evaluación."""
    evals = read_table("EVALUACIONES")
    if evals.empty:
        return 1
    row = evals[evals["ID_Evaluacion"] == eval_id]
    if row.empty:
        return 1
    return int(row.iloc[0].get("Fase_Wizard", 1) or 1)


# ─── Punto de entrada ───────────────────────────────────────────────────────
def render_wizard(_styled_header):
    """Renderiza el wizard de nueva evaluación."""
    _styled_header("", "Nueva Evaluación", "Asistente guiado para crear y completar una evaluación de riesgos")

    # ── Inicializar estado ──────────────────────────────────────────────────
    if "wiz_step" not in st.session_state:
        st.session_state["wiz_step"] = 1
    if "wiz_eval_id" not in st.session_state:
        st.session_state["wiz_eval_id"] = None

    # ── Reanudar evaluación en progreso ─────────────────────────────────────
    evals = get_evaluaciones()
    en_progreso = evals[
        (evals["Estado"] == "En Progreso") &
        (evals.get("Fase_Wizard", pd.Series(dtype="int")).fillna(0).astype(int) > 0)
    ] if not evals.empty and "Fase_Wizard" in evals.columns else pd.DataFrame()

    if not en_progreso.empty and st.session_state["wiz_eval_id"] is None:
        st.info("**Hay evaluaciones en progreso.** Puedes continuar donde lo dejaste o crear una nueva.")
        opciones = en_progreso["ID_Evaluacion"].tolist()
        sel = st.selectbox(
            "Continuar evaluación",
            ["-- Crear nueva --"] + opciones,
            format_func=lambda x: x if x == "-- Crear nueva --"
                else f"{x} — {evals[evals['ID_Evaluacion']==x].iloc[0]['Nombre']} (Fase {int(evals[evals['ID_Evaluacion']==x].iloc[0].get('Fase_Wizard', 1))})",
            key="wiz_resume_select"
        )
        if sel != "-- Crear nueva --":
            if st.button("Continuar", key="wiz_btn_resume", type="primary"):
                st.session_state["wiz_eval_id"] = sel
                st.session_state["wiz_step"] = _cargar_fase(sel)
                st.rerun()
            st.divider()

    step = st.session_state["wiz_step"]
    eval_id = st.session_state["wiz_eval_id"]

    _render_stepper(step)

    # ═════════════════════════════════════════════════════════════════════════
    #  PASO 1 — CREAR EVALUACIÓN
    # ═════════════════════════════════════════════════════════════════════════
    if step == 1:
        st.markdown("### Paso 1: Crear Evaluación")
        st.markdown("Define los datos generales de la nueva evaluación de riesgos.")

        with st.form("wiz_form_eval"):
            nombre = st.text_input("Nombre *", placeholder="Ej: Evaluación Q2 2026")
            responsable = st.text_input("Responsable *", placeholder="Ej: Juan Pérez")
            descripcion = st.text_area("Descripción", placeholder="Contexto y alcance de la evaluación...")
            submitted = st.form_submit_button("Crear y Continuar", type="primary", use_container_width=True)

        if submitted:
            if not nombre or not responsable:
                st.error("Los campos **Nombre** y **Responsable** son obligatorios.")
            else:
                nuevo_id = crear_evaluacion(nombre=nombre, descripcion=descripcion, responsable=responsable)
                _guardar_fase(nuevo_id, 1)
                registrar_proceso_rapido(nuevo_id, "wizard_paso1", "EVALUACION",
                    f"Wizard: Evaluación '{nombre}' creada por {responsable}")
                st.session_state["wiz_eval_id"] = nuevo_id
                st.session_state["wiz_step"] = 2
                # Guardar fase 2 para poder reanudar
                _guardar_fase(nuevo_id, 2)
                st.session_state["eval_actual"] = nuevo_id
                st.session_state["eval_nombre"] = nombre
                st.rerun()

    # ═════════════════════════════════════════════════════════════════════════
    #  PASO 2 — AGREGAR ACTIVOS
    # ═════════════════════════════════════════════════════════════════════════
    elif step == 2 and eval_id:
        st.markdown("### Paso 2: Agregar Activos")
        eval_data = evals[evals["ID_Evaluacion"] == eval_id].iloc[0] if not evals.empty else {}
        st.caption(f"Evaluación: **{eval_data.get('Nombre', eval_id)}** (`{eval_id}`)")

        # Tabla de activos existentes
        activos = get_activos_por_evaluacion(eval_id)
        if not activos.empty:
            st.markdown(f"**{len(activos)} activo(s) agregado(s)**")
            st.dataframe(
                activos[["ID_Activo", "Nombre_Activo", "Tipo_Activo", "Ubicacion", "Tipo_Servicio"]],
                use_container_width=True,
                hide_index=True,
                height=min(200, 50 + len(activos) * 35)
            )

            # Eliminar activo
            act_elim = st.selectbox("Eliminar activo", activos["ID_Activo"].tolist(), key="wiz_act_elim")
            if st.button("Eliminar", key="wiz_btn_elim_act"):
                eliminar_activo(eval_id, act_elim)
                st.rerun()
        else:
            st.info("Agrega al menos un activo para continuar.")

        st.divider()

        # Formulario para agregar activo
        st.markdown("#### Agregar activo")
        with st.form("wiz_form_activo"):
            nombre_act = st.text_input("Nombre del activo *", placeholder="Ej: Servidor DB Principal")
            c1, c2 = st.columns(2)
            with c1:
                tipo_act = st.selectbox("Tipo *", ["Servidor Físico", "Servidor Virtual"], key="wiz_tipo")
                ubicacion = st.selectbox("Ubicación *", ["UdlaPark", "Granados"], key="wiz_ubic")
            with c2:
                propietario = st.selectbox("Propietario *",
                    ["Infraestructura", "Seguridad de la Información", "Soporte"], key="wiz_prop")
                tipo_servicio = st.selectbox("Tipo Servicio *",
                    ["Base de datos", "Servidor web", "Servidor aplicaciones",
                     "Firewall", "Switch", "Router", "Storage", "Backup", "Otro"], key="wiz_serv")
            app_critica = st.radio("Aplicación Crítica", ["Sí", "No"], horizontal=True, key="wiz_crit")
            submitted_act = st.form_submit_button("Agregar Activo", type="primary", use_container_width=True)

        if submitted_act:
            if not nombre_act:
                st.error("El **Nombre** del activo es obligatorio.")
            else:
                es_dup, msg_dup = validar_duplicado(eval_id, nombre_act, ubicacion, tipo_servicio)
                if es_dup:
                    st.error(msg_dup)
                else:
                    datos = {
                        "Nombre_Activo": nombre_act, "Tipo_Activo": tipo_act,
                        "Ubicacion": ubicacion, "Propietario": propietario,
                        "Tipo_Servicio": tipo_servicio, "App_Critica": app_critica
                    }
                    exito, msg, nuevo_id_act = crear_activo(eval_id, datos)
                    if exito:
                        registrar_proceso_rapido(eval_id, "wizard_paso2", "INVENTARIO",
                            f"Wizard: Activo '{nombre_act}' agregado ({nuevo_id_act})")
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        # Navegación
        st.divider()
        nav1, nav2, nav3 = st.columns([1, 2, 1])
        with nav1:
            if st.button("Anterior", key="wiz_back_2", use_container_width=True):
                st.session_state["wiz_step"] = 1
                st.rerun()
        with nav2:
            if st.button("Guardar Progreso", key="wiz_save_2", use_container_width=True):
                _guardar_fase(eval_id, 2)
                st.success("Progreso guardado. Puedes cerrar y continuar luego.")
        with nav3:
            can_advance = not activos.empty if not isinstance(activos, type(None)) else False
            if st.button("Siguiente", key="wiz_next_2", type="primary",
                         use_container_width=True, disabled=not can_advance):
                st.session_state["wiz_step"] = 3
                _guardar_fase(eval_id, 3)
                st.rerun()

    # ═════════════════════════════════════════════════════════════════════════
    #  PASO 3 — CUESTIONARIOS
    # ═════════════════════════════════════════════════════════════════════════
    elif step == 3 and eval_id:
        st.markdown("### Paso 3: Cuestionarios")
        eval_data = evals[evals["ID_Evaluacion"] == eval_id].iloc[0] if not evals.empty else {}
        st.caption(f"Evaluación: **{eval_data.get('Nombre', eval_id)}**")

        activos = get_activos_por_evaluacion(eval_id)
        if activos.empty:
            st.warning("No hay activos. Regresa al paso anterior.")
        else:
            # Estado de cuestionarios por activo
            datos_estado = []
            todos_completos = True
            for _, activo in activos.iterrows():
                aid = activo["ID_Activo"]
                completo = verificar_respuestas_existentes(eval_id, aid)
                datos_estado.append({
                    "ID": aid,
                    "Nombre": activo["Nombre_Activo"],
                    "Tipo": activo.get("Tipo_Activo", "N/A"),
                    "Estado": "Completado" if completo else "Pendiente"
                })
                if not completo:
                    todos_completos = False

            df_estado = pd.DataFrame(datos_estado)
            st.dataframe(df_estado, use_container_width=True, hide_index=True)

            completados = sum(1 for d in datos_estado if d["Estado"] == "Completado")
            st.progress(completados / len(datos_estado))
            st.caption(f"{completados}/{len(datos_estado)} activos con cuestionario completado")

            if todos_completos:
                st.success("Todos los cuestionarios completados. Puedes continuar al paso 4.")
            else:
                # Seleccionar activo pendiente
                pendientes = [d["ID"] for d in datos_estado if d["Estado"] == "Pendiente"]
                activo_sel = st.selectbox(
                    "Seleccionar activo para responder",
                    pendientes,
                    format_func=lambda x: f"{x} — {activos[activos['ID_Activo']==x].iloc[0]['Nombre_Activo']}",
                    key="wiz_cuest_activo"
                )

                activo_data = get_activo(eval_id, activo_sel)

                # Auto-generar cuestionario si no existe
                cuestionario_df = get_cuestionario(eval_id, activo_sel)
                if cuestionario_df.empty:
                    with st.spinner(f"Generando cuestionario para {activo_data.get('Nombre_Activo', activo_sel)}..."):
                        exito_gen, msg_gen, _ = generar_cuestionario(eval_id=eval_id, activo=activo_data, model="")
                        if exito_gen:
                            st.rerun()
                        else:
                            st.error(msg_gen)

                cuestionario_df = get_cuestionario(eval_id, activo_sel)
                if not cuestionario_df.empty:
                    st.divider()
                    st.markdown(f"#### Cuestionario — {activo_data.get('Nombre_Activo', activo_sel)}")

                    # Formulario de respuestas
                    with st.form(f"wiz_form_cuest_{activo_sel}"):
                        respuestas = {}
                        dimensiones = {"D": "Disponibilidad", "I": "Integridad", "C": "Confidencialidad"}

                        for dim_code, dim_name in dimensiones.items():
                            preguntas_dim = cuestionario_df[cuestionario_df["Dimension"] == dim_code]
                            if not preguntas_dim.empty:
                                st.markdown(f"##### {dim_name}")
                                for idx, row in preguntas_dim.iterrows():
                                    id_preg = row.get("ID_Pregunta", f"P{idx}")
                                    pregunta = row.get("Pregunta", "")
                                    bloque = row.get("Bloque", "")
                                    opciones = [
                                        str(row.get(f"Opcion_{i}", "")) for i in range(1, 5)
                                    ]
                                    opciones = [o for o in opciones if o and o != "nan"]

                                    st.markdown(f"**{id_preg}.** {pregunta}")
                                    if bloque:
                                        st.caption(bloque)

                                    if len(opciones) >= 4:
                                        fmt = [f"{i+1}. {o}" for i, o in enumerate(opciones)]
                                        resp = st.radio(
                                            f"R-{id_preg}", fmt, index=0,
                                            key=f"wiz_r_{activo_sel}_{id_preg}",
                                            label_visibility="collapsed"
                                        )
                                        respuestas[id_preg] = resp.split(". ", 1)[1] if ". " in resp else resp
                                    else:
                                        respuestas[id_preg] = st.text_area(
                                            f"R-{id_preg}", key=f"wiz_r_{activo_sel}_{id_preg}",
                                            label_visibility="collapsed", height=60
                                        )
                                    st.caption(f"Peso: {row.get('Peso', 'N/A')} | Dimensión: {dim_code}")
                                    st.divider()

                        submitted_cuest = st.form_submit_button(
                            "Guardar Respuestas", type="primary", use_container_width=True
                        )

                    if submitted_cuest:
                        validas = {k: v for k, v in respuestas.items() if v and str(v).strip()}
                        if not validas:
                            st.error("Debes responder al menos una pregunta.")
                        else:
                            fecha_v = cuestionario_df.iloc[0].get(
                                "Fecha_Version", dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            )
                            lista_resp = []
                            for id_p, texto in validas.items():
                                fila = cuestionario_df[cuestionario_df["ID_Pregunta"] == id_p]
                                if not fila.empty:
                                    r = fila.iloc[0]
                                    val = 1
                                    for i, opt in enumerate(["Opcion_1", "Opcion_2", "Opcion_3", "Opcion_4"]):
                                        if str(r.get(opt, "")) == texto:
                                            val = i + 1
                                            break
                                    lista_resp.append({
                                        "ID_Pregunta": id_p, "Pregunta": r.get("Pregunta", ""),
                                        "Respuesta": texto, "Valor_Numerico": val,
                                        "Peso": r.get("Peso", 3), "Dimension": r.get("Dimension", "I"),
                                        "Bloque": r.get("Bloque", "")
                                    })

                            ok = guardar_respuestas(eval_id, activo_sel, fecha_v, lista_resp)
                            if ok:
                                registrar_proceso_rapido(eval_id, "wizard_paso3", "CUESTIONARIO",
                                    f"Wizard: Cuestionario de {activo_sel} completado ({len(validas)} respuestas)")
                                st.success(f"{len(validas)} respuestas guardadas para {activo_sel}")
                                st.rerun()
                            else:
                                st.warning("Ya existen respuestas para este activo.")

        # Navegación
        st.divider()
        nav1, nav2, nav3 = st.columns([1, 2, 1])
        with nav1:
            if st.button("Anterior", key="wiz_back_3", use_container_width=True):
                st.session_state["wiz_step"] = 2
                st.rerun()
        with nav2:
            if st.button("Guardar Progreso", key="wiz_save_3", use_container_width=True):
                _guardar_fase(eval_id, 3)
                st.success("Progreso guardado. Puedes cerrar y continuar luego.")
        with nav3:
            if st.button("Siguiente", key="wiz_next_3", type="primary",
                         use_container_width=True, disabled=not todos_completos):
                st.session_state["wiz_step"] = 4
                _guardar_fase(eval_id, 4)
                st.rerun()

    # ═════════════════════════════════════════════════════════════════════════
    #  PASO 4 — EVALUACIÓN CON IA
    # ═════════════════════════════════════════════════════════════════════════
    elif step == 4 and eval_id:
        st.markdown("### Paso 4: Evaluación con IA")
        eval_data = evals[evals["ID_Evaluacion"] == eval_id].iloc[0] if not evals.empty else {}
        st.caption(f"Evaluación: **{eval_data.get('Nombre', eval_id)}**")

        st.markdown("""
        Este paso ejecutará el **Análisis Completo** de riesgos MAGERIT:
        - Evaluación IA de amenazas por activo
        - Planes de tratamiento
        - Cálculo de nivel de madurez
        - Resumen ejecutivo
        - Priorización de controles
        """)

        # Verificar Ollama
        ollama_ok, modelos = verificar_ollama_disponible()
        if ollama_ok:
            st.success(f"Ollama conectado. Modelos: {', '.join(modelos[:3])}")
            modelo_ia = st.selectbox("Modelo IA", modelos, index=0, key="wiz_modelo_ia")
        else:
            st.error("Ollama no disponible. Se requiere para la evaluación con IA.")
            modelo_ia = None

        # Componente de análisis completo
        if modelo_ia:
            try:
                from components.analisis_completo_ui import render_analisis_completo
                render_analisis_completo(eval_id, eval_data.get("Nombre", eval_id), modelo_ia)
            except ImportError:
                st.error("Componente de análisis no disponible.")

        # Navegación
        st.divider()
        nav1, nav2, nav3 = st.columns([1, 2, 1])
        with nav1:
            if st.button("Anterior", key="wiz_back_4", use_container_width=True):
                st.session_state["wiz_step"] = 3
                st.rerun()
        with nav2:
            if st.button("Guardar Progreso", key="wiz_save_4", use_container_width=True):
                _guardar_fase(eval_id, 4)
                st.success("Progreso guardado.")
        with nav3:
            if st.button("Finalizar Evaluación", key="wiz_finish", type="primary",
                         use_container_width=True):
                # Marcar evaluación como completada
                update_row("EVALUACIONES",
                    {"Estado": "Completada", "Fase_Wizard": 0},
                    {"ID_Evaluacion": eval_id})
                registrar_proceso_rapido(eval_id, "wizard_finalizar", "EVALUACION",
                    f"Wizard: Evaluación '{eval_data.get('Nombre', eval_id)}' completada")

                # Activar evaluación
                st.session_state["eval_actual"] = eval_id
                st.session_state["eval_nombre"] = eval_data.get("Nombre", eval_id)

                # Limpiar wizard
                st.session_state["wiz_step"] = 1
                st.session_state["wiz_eval_id"] = None

                st.success("Evaluación completada exitosamente.")
                st.balloons()

                # Redirigir a Estadísticas
                st.session_state["nav_pagina"] = "Estadísticas"
                st.rerun()
