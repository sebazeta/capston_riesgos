"""
COMPONENTE UI: TRATAMIENTO DE RIESGOS
======================================
Permite gestionar decisiones de tratamiento por activo/riesgo.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
from services import (
    crear_tratamiento,
    obtener_tratamiento,
    listar_tratamientos_activo,
    listar_tratamientos_evaluacion,
    actualizar_tratamiento,
    eliminar_tratamiento,
    sugerir_tratamiento,
    get_estadisticas_tratamiento,
    TratamientoRiesgo,
    TIPOS_TRATAMIENTO,
    registrar_cambio
)
from services.database_service import get_connection


def render_tratamiento_tab(id_evaluacion: str):
    """
    Renderiza el tab de tratamiento de riesgos.
    """
    st.header("🛡️ Tratamiento de Riesgos")
    
    # Estadísticas generales
    stats = get_estadisticas_tratamiento(id_evaluacion)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Decisiones", stats.get("total", 0))
    with col2:
        st.metric("Mitigar", stats.get("por_tipo", {}).get("Mitigar", 0))
    with col3:
        st.metric("Aceptar", stats.get("por_tipo", {}).get("Aceptar", 0))
    with col4:
        st.metric("Activos con Plan", stats.get("activos_con_tratamiento", 0))
    
    st.divider()
    
    # Tabs internos
    tab_lista, tab_nuevo, tab_sugerencias = st.tabs([
        "📋 Decisiones de Tratamiento",
        "➕ Nueva Decisión", 
        "💡 Sugerencias"
    ])
    
    with tab_lista:
        render_lista_tratamientos(id_evaluacion)
    
    with tab_nuevo:
        render_formulario_tratamiento(id_evaluacion)
    
    with tab_sugerencias:
        render_sugerencias_tratamiento(id_evaluacion)


def render_lista_tratamientos(id_evaluacion: str):
    """Lista todas las decisiones de tratamiento"""
    
    # Obtener tratamientos
    tratamientos = listar_tratamientos_evaluacion(id_evaluacion)
    
    if not tratamientos:
        st.info("No hay decisiones de tratamiento registradas.")
        st.markdown("""
        **Tipos de tratamiento según MAGERIT:**
        - **Mitigar**: Implementar controles para reducir el riesgo
        - **Aceptar**: Asumir el riesgo conscientemente
        - **Transferir**: Trasladar el riesgo (seguros, terceros)
        - **Evitar**: Eliminar la actividad que genera el riesgo
        """)
        return
    
    # Obtener nombres de activos
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ID_Activo, Nombre_Activo
            FROM INVENTARIO_ACTIVOS
            WHERE ID_Evaluacion = ?
        ''', [id_evaluacion])
        nombres_activos = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Convertir a DataFrame
    df_data = []
    for t in tratamientos:
        df_data.append({
            "ID": t.id,
            "Activo": nombres_activos.get(t.id_activo, t.id_activo),
            "Tipo": t.tipo_tratamiento,
            "Estado": t.estado,
            "Riesgo Actual": t.riesgo_actual if t.riesgo_actual else "-",
            "Riesgo Objetivo": t.riesgo_objetivo if t.riesgo_objetivo else "-",
            "Fecha": t.fecha_decision
        })
    
    df = pd.DataFrame(df_data)
    
    # Aplicar estilos por tipo
    def color_tipo(val):
        colores = {
            "Mitigar": "background-color: #cce5ff",
            "Aceptar": "background-color: #ffffcc",
            "Transferir": "background-color: #e5ccff",
            "Evitar": "background-color: #ffcccc"
        }
        return colores.get(val, "")
    
    st.dataframe(
        df.style.map(color_tipo, subset=["Tipo"]),
        use_container_width=True,
        hide_index=True
    )
    
    # Detalle de tratamiento seleccionado
    st.subheader("Detalle de Decisión")
    
    if tratamientos:
        trat_names = [f"{nombres_activos.get(t.id_activo, t.id_activo)} - {t.tipo_tratamiento}" for t in tratamientos]
        trat_sel = st.selectbox("Seleccionar decisión:", trat_names, key="trat_detail_sel")
        idx = trat_names.index(trat_sel)
        trat = tratamientos[idx]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Activo:** {nombres_activos.get(trat.id_activo, trat.id_activo)}")
            st.markdown(f"**Tipo de Tratamiento:** {trat.tipo_tratamiento}")
            st.markdown(f"**{TIPOS_TRATAMIENTO.get(trat.tipo_tratamiento, '')}**")
        
        with col2:
            st.markdown(f"**Estado:** {trat.estado}")
            st.markdown(f"**Riesgo Actual:** {trat.riesgo_actual if trat.riesgo_actual else 'N/A'}")
            st.markdown(f"**Riesgo Objetivo:** {trat.riesgo_objetivo if trat.riesgo_objetivo else 'N/A'}")
        
        st.markdown("**Justificación:**")
        st.text_area("", value=trat.justificacion, height=100, disabled=True, key="trat_just_view")
        
        if trat.controles_propuestos:
            st.markdown("**Controles Propuestos:**")
            st.text_area("", value=trat.controles_propuestos, height=80, disabled=True, key="trat_ctrl_view")
        
        if trat.responsable:
            st.markdown(f"**Responsable:** {trat.responsable}")
        
        if trat.fecha_objetivo:
            st.markdown(f"**Fecha Objetivo:** {trat.fecha_objetivo}")
        
        # Acciones
        col_edit, col_del = st.columns(2)
        
        with col_edit:
            if st.button("✏️ Editar", key=f"edit_trat_{trat.id}"):
                st.session_state["trat_edit_mode"] = trat.id
                st.rerun()
        
        with col_del:
            if st.button("🗑️ Eliminar", key=f"del_trat_{trat.id}"):
                if eliminar_tratamiento(trat.id):
                    registrar_cambio(
                        tabla="TRATAMIENTO_RIESGOS",
                        id_registro=str(trat.id),
                        accion="DELETE",
                        valores_anteriores={"tipo": trat.tipo_tratamiento}
                    )
                    st.success("Decisión eliminada.")
                    st.rerun()
                else:
                    st.error("Error al eliminar.")


def render_formulario_tratamiento(id_evaluacion: str, trat_editar: TratamientoRiesgo = None):
    """Formulario para crear/editar tratamiento"""
    
    es_edicion = trat_editar is not None
    
    st.subheader("➕ Nueva Decisión" if not es_edicion else "✏️ Editar Decisión")
    
    # Obtener activos con sus riesgos
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.ID_Activo, a.Nombre_Activo, a.Tipo_Activo,
                   COALESCE(r.Riesgo_Promedio, r.Riesgo_Inherente, 0) as Riesgo
            FROM INVENTARIO_ACTIVOS a
            LEFT JOIN RESULTADOS_MAGERIT r ON a.ID_Activo = r.ID_Activo
            WHERE a.ID_Evaluacion = ?
            ORDER BY Riesgo DESC
        ''', [id_evaluacion])
        activos = cursor.fetchall()
    
    if not activos:
        st.warning("Primero debe registrar activos y ejecutar evaluación MAGERIT.")
        return
    
    # Campos del formulario
    with st.form("form_tratamiento"):
        # Activo
        opciones_activos = [f"{a[1]} ({a[2]}) - Riesgo: {round(a[3] or 0, 2)}" for a in activos]
        idx_activo = 0
        if es_edicion:
            for i, a in enumerate(activos):
                if a[0] == trat_editar.id_activo:
                    idx_activo = i
                    break
        
        activo_sel = st.selectbox("Activo:", opciones_activos, index=idx_activo)
        idx = opciones_activos.index(activo_sel)
        id_activo = activos[idx][0]
        riesgo_actual = activos[idx][3] or 0
        
        col1, col2 = st.columns(2)
        
        with col1:
            tipo_tratamiento = st.selectbox(
                "Tipo de Tratamiento:",
                list(TIPOS_TRATAMIENTO.keys()),
                index=list(TIPOS_TRATAMIENTO.keys()).index(trat_editar.tipo_tratamiento) if es_edicion and trat_editar.tipo_tratamiento in TIPOS_TRATAMIENTO else 0
            )
            
            # Mostrar descripción del tipo
            st.caption(TIPOS_TRATAMIENTO[tipo_tratamiento])
            
            riesgo_obj = st.number_input(
                "Riesgo Objetivo:",
                min_value=0.0,
                max_value=10.0,
                value=trat_editar.riesgo_objetivo if es_edicion and trat_editar.riesgo_objetivo else riesgo_actual * 0.5,
                step=0.1
            )
        
        with col2:
            estado = st.selectbox(
                "Estado:",
                ["Propuesto", "Aprobado", "En Implementación", "Implementado", "Verificado"],
                index=["Propuesto", "Aprobado", "En Implementación", "Implementado", "Verificado"].index(trat_editar.estado) if es_edicion else 0
            )
            
            responsable = st.text_input(
                "Responsable:",
                value=trat_editar.responsable if es_edicion else ""
            )
            
            fecha_objetivo = st.date_input(
                "Fecha Objetivo:",
                value=None
            )
        
        justificacion = st.text_area(
            "Justificación de la decisión:",
            value=trat_editar.justificacion if es_edicion else "",
            height=100,
            placeholder="Explique por qué se seleccionó este tipo de tratamiento..."
        )
        
        controles = st.text_area(
            "Controles propuestos (si aplica):",
            value=trat_editar.controles_propuestos if es_edicion else "",
            height=80,
            placeholder="Liste los controles a implementar..."
        )
        
        submitted = st.form_submit_button("💾 Guardar")
        
        if submitted:
            if not justificacion:
                st.error("La justificación es obligatoria.")
            else:
                trat = TratamientoRiesgo(
                    id=trat_editar.id if es_edicion else None,
                    id_evaluacion=id_evaluacion,
                    id_activo=id_activo,
                    tipo_tratamiento=tipo_tratamiento,
                    justificacion=justificacion,
                    riesgo_actual=round(riesgo_actual, 2),
                    riesgo_objetivo=round(riesgo_obj, 2),
                    controles_propuestos=controles,
                    responsable=responsable,
                    fecha_objetivo=str(fecha_objetivo) if fecha_objetivo else None,
                    estado=estado
                )
                
                if es_edicion:
                    if actualizar_tratamiento(trat):
                        registrar_cambio(
                            tabla="TRATAMIENTO_RIESGOS",
                            id_registro=str(trat.id),
                            accion="UPDATE",
                            valores_nuevos={"tipo": tipo_tratamiento, "estado": estado}
                        )
                        st.success("✅ Decisión actualizada.")
                        st.session_state.pop("trat_edit_mode", None)
                        st.rerun()
                    else:
                        st.error("Error al actualizar.")
                else:
                    nuevo_id = crear_tratamiento(trat)
                    if nuevo_id:
                        registrar_cambio(
                            tabla="TRATAMIENTO_RIESGOS",
                            id_registro=str(nuevo_id),
                            accion="INSERT",
                            valores_nuevos={"tipo": tipo_tratamiento, "id_activo": id_activo}
                        )
                        st.success(f"✅ Decisión registrada (ID: {nuevo_id})")
                        st.rerun()
                    else:
                        st.error("Error al crear.")


def render_sugerencias_tratamiento(id_evaluacion: str):
    """Sugerencias automáticas de tratamiento basadas en nivel de riesgo"""
    
    st.subheader("💡 Sugerencias de Tratamiento")
    st.info("El sistema sugiere el tratamiento apropiado basándose en el nivel de riesgo del activo.")
    
    # Obtener activos con riesgo ordenados
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.ID_Activo, a.Nombre_Activo, a.Tipo_Activo,
                   COALESCE(r.Riesgo_Promedio, r.Riesgo_Inherente, 0) as Riesgo,
                   r.Nivel_Riesgo
            FROM INVENTARIO_ACTIVOS a
            LEFT JOIN RESULTADOS_MAGERIT r ON a.ID_Activo = r.ID_Activo
            WHERE a.ID_Evaluacion = ?
            ORDER BY Riesgo DESC
        ''', [id_evaluacion])
        activos = cursor.fetchall()
    
    if not activos:
        st.warning("No hay activos evaluados en esta evaluación.")
        return
    
    # Filtrar por nivel de riesgo
    filtro_nivel = st.selectbox(
        "Filtrar por nivel de riesgo:",
        ["Todos", "Crítico", "Muy Alto", "Alto", "Medio", "Bajo"],
        key="filtro_nivel_trat"
    )
    
    activos_filtrados = activos
    if filtro_nivel != "Todos":
        activos_filtrados = [a for a in activos if a[4] == filtro_nivel]
    
    if not activos_filtrados:
        st.info(f"No hay activos con nivel de riesgo '{filtro_nivel}'.")
        return
    
    st.markdown(f"**{len(activos_filtrados)} activos encontrados**")
    
    for activo in activos_filtrados[:10]:  # Limitar a 10
        id_activo, nombre, tipo, riesgo, nivel = activo
        
        # Obtener sugerencia
        sugerencia = sugerir_tratamiento(riesgo)
        
        with st.expander(f"📊 {nombre} - Riesgo: {round(riesgo, 2)} ({nivel})", expanded=riesgo >= 6):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Tipo de activo:** {tipo}")
                st.markdown(f"**Riesgo calculado:** {round(riesgo, 2)}")
                st.markdown(f"**Nivel:** {nivel}")
                
                st.markdown("---")
                st.markdown(f"**💡 Tratamiento sugerido: {sugerencia['tipo']}**")
                st.markdown(f"*{sugerencia['descripcion']}*")
                st.markdown(f"**Justificación:** {sugerencia['justificacion']}")
            
            with col2:
                # Verificar si ya tiene tratamiento
                tratamientos_existentes = listar_tratamientos_activo(id_activo)
                
                if tratamientos_existentes:
                    st.warning(f"⚠️ Ya tiene {len(tratamientos_existentes)} decisión(es)")
                else:
                    if st.button(f"✅ Aplicar sugerencia", key=f"apply_trat_{id_activo}"):
                        trat = TratamientoRiesgo(
                            id_evaluacion=id_evaluacion,
                            id_activo=id_activo,
                            tipo_tratamiento=sugerencia['tipo'],
                            justificacion=sugerencia['justificacion'],
                            riesgo_actual=round(riesgo, 2),
                            riesgo_objetivo=round(riesgo * 0.5, 2),
                            estado="Propuesto"
                        )
                        nuevo_id = crear_tratamiento(trat)
                        if nuevo_id:
                            registrar_cambio(
                                tabla="TRATAMIENTO_RIESGOS",
                                id_registro=str(nuevo_id),
                                accion="IA_SUGERENCIA",
                                valores_nuevos={"tipo": sugerencia['tipo'], "fuente": "Sugerencia Sistema"}
                            )
                            st.success("✅ Tratamiento aplicado")
                            st.rerun()
