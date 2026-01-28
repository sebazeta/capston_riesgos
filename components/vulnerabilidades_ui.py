"""
COMPONENTE UI: GESTIÓN DE VULNERABILIDADES
============================================
Permite gestionar vulnerabilidades por activo.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
from services import (
    crear_vulnerabilidad,
    obtener_vulnerabilidad,
    listar_vulnerabilidades_activo,
    listar_vulnerabilidades_evaluacion,
    actualizar_vulnerabilidad,
    eliminar_vulnerabilidad,
    sugerir_vulnerabilidades_ia,
    get_estadisticas_vulnerabilidades,
    Vulnerabilidad,
    SEVERIDADES,
    registrar_cambio
)
from services.database_service import get_connection


def render_vulnerabilidades_tab(id_evaluacion: str):
    """
    Renderiza el tab de gestión de vulnerabilidades.
    """
    st.header("🔓 Gestión de Vulnerabilidades")
    
    # Estadísticas generales
    stats = get_estadisticas_vulnerabilidades(id_evaluacion)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Vulnerabilidades", stats.get("total", 0))
    with col2:
        st.metric("Críticas", stats.get("por_severidad", {}).get("Critica", 0), 
                  delta=None, delta_color="inverse")
    with col3:
        st.metric("Altas", stats.get("por_severidad", {}).get("Alta", 0))
    with col4:
        st.metric("Activos Afectados", stats.get("activos_con_vulnerabilidades", 0))
    
    st.divider()
    
    # Tabs internos
    tab_lista, tab_nueva, tab_ia = st.tabs([
        "📋 Lista de Vulnerabilidades",
        "➕ Nueva Vulnerabilidad", 
        "🤖 Sugerencias IA"
    ])
    
    with tab_lista:
        render_lista_vulnerabilidades(id_evaluacion)
    
    with tab_nueva:
        render_formulario_vulnerabilidad(id_evaluacion)
    
    with tab_ia:
        render_sugerencias_ia(id_evaluacion)


def render_lista_vulnerabilidades(id_evaluacion: str):
    """Lista todas las vulnerabilidades de la evaluación"""
    
    # Obtener activos
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ID_Activo, Nombre_Activo, Tipo_Activo
            FROM INVENTARIO_ACTIVOS
            WHERE ID_Evaluacion = ?
            ORDER BY Nombre_Activo
        ''', [id_evaluacion])
        activos = cursor.fetchall()
    
    if not activos:
        st.info("No hay activos en esta evaluación.")
        return
    
    # Filtro por activo
    opciones_activos = ["Todos"] + [f"{a[1]} ({a[2]})" for a in activos]
    activo_sel = st.selectbox("Filtrar por activo:", opciones_activos, key="vuln_filter")
    
    id_activo_filtro = None
    if activo_sel != "Todos":
        idx = opciones_activos.index(activo_sel) - 1
        id_activo_filtro = activos[idx][0]
    
    # Obtener vulnerabilidades
    if id_activo_filtro:
        vulns = listar_vulnerabilidades_activo(id_activo_filtro)
    else:
        vulns = listar_vulnerabilidades_evaluacion(id_evaluacion)
    
    if not vulns:
        st.info("No hay vulnerabilidades registradas.")
        return
    
    # Convertir a DataFrame
    df_data = []
    for v in vulns:
        df_data.append({
            "ID": v.id,
            "Código": v.codigo,
            "Nombre": v.nombre,
            "Severidad": v.severidad,
            "CVSS": v.cvss_score if v.cvss_score else "-",
            "Estado": v.estado,
            "Fuente": v.fuente
        })
    
    df = pd.DataFrame(df_data)
    
    # Aplicar estilos por severidad
    def color_severidad(val):
        colores = {
            "Critica": "background-color: #ffcccc",
            "Alta": "background-color: #ffddcc",
            "Media": "background-color: #ffffcc",
            "Baja": "background-color: #ccffcc",
            "Info": "background-color: #cce5ff"
        }
        return colores.get(val, "")
    
    st.dataframe(
        df.style.map(color_severidad, subset=["Severidad"]),
        use_container_width=True,
        hide_index=True
    )
    
    # Detalle de vulnerabilidad seleccionada
    st.subheader("Detalle de Vulnerabilidad")
    
    vuln_ids = [v.id for v in vulns]
    vuln_names = [f"{v.codigo} - {v.nombre}" for v in vulns]
    
    if vuln_ids:
        vuln_sel = st.selectbox("Seleccionar vulnerabilidad:", vuln_names, key="vuln_detail_sel")
        idx = vuln_names.index(vuln_sel)
        vuln = vulns[idx]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Código:** {vuln.codigo}")
            st.markdown(f"**Nombre:** {vuln.nombre}")
            st.markdown(f"**Severidad:** {vuln.severidad}")
            st.markdown(f"**CVSS Score:** {vuln.cvss_score if vuln.cvss_score else 'N/A'}")
        
        with col2:
            st.markdown(f"**Estado:** {vuln.estado}")
            st.markdown(f"**Fuente:** {vuln.fuente}")
            st.markdown(f"**Fecha Registro:** {vuln.fecha_registro}")
        
        st.markdown("**Descripción:**")
        st.text_area("", value=vuln.descripcion, height=100, disabled=True, key="vuln_desc_view")
        
        if vuln.amenazas_asociadas:
            st.markdown("**Amenazas Asociadas:**")
            for amenaza in vuln.amenazas_asociadas.split(","):
                st.markdown(f"- {amenaza.strip()}")
        
        if vuln.controles_mitigantes:
            st.markdown("**Controles Mitigantes:**")
            for control in vuln.controles_mitigantes.split(","):
                st.markdown(f"- {control.strip()}")
        
        # Acciones
        col_edit, col_del = st.columns(2)
        
        with col_edit:
            if st.button("✏️ Editar", key=f"edit_vuln_{vuln.id}"):
                st.session_state["vuln_edit_mode"] = vuln.id
                st.rerun()
        
        with col_del:
            if st.button("🗑️ Eliminar", key=f"del_vuln_{vuln.id}"):
                if eliminar_vulnerabilidad(vuln.id):
                    registrar_cambio(
                        tabla="VULNERABILIDADES_ACTIVO",
                        id_registro=str(vuln.id),
                        accion="DELETE",
                        valores_anteriores={"codigo": vuln.codigo, "nombre": vuln.nombre}
                    )
                    st.success("Vulnerabilidad eliminada.")
                    st.rerun()
                else:
                    st.error("Error al eliminar.")


def render_formulario_vulnerabilidad(id_evaluacion: str, vuln_editar: Vulnerabilidad = None):
    """Formulario para crear/editar vulnerabilidad"""
    
    es_edicion = vuln_editar is not None
    
    st.subheader("➕ Nueva Vulnerabilidad" if not es_edicion else "✏️ Editar Vulnerabilidad")
    
    # Obtener activos
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ID_Activo, Nombre_Activo, Tipo_Activo
            FROM INVENTARIO_ACTIVOS
            WHERE ID_Evaluacion = ?
            ORDER BY Nombre_Activo
        ''', [id_evaluacion])
        activos = cursor.fetchall()
    
    if not activos:
        st.warning("Primero debe registrar activos.")
        return
    
    # Campos del formulario
    with st.form("form_vulnerabilidad"):
        # Activo
        opciones_activos = [f"{a[1]} ({a[2]})" for a in activos]
        idx_activo = 0
        if es_edicion:
            for i, a in enumerate(activos):
                if a[0] == vuln_editar.id_activo:
                    idx_activo = i
                    break
        
        activo_sel = st.selectbox("Activo:", opciones_activos, index=idx_activo)
        id_activo = activos[opciones_activos.index(activo_sel)][0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            codigo = st.text_input(
                "Código (CVE, ID interno):", 
                value=vuln_editar.codigo if es_edicion else ""
            )
            nombre = st.text_input(
                "Nombre:", 
                value=vuln_editar.nombre if es_edicion else ""
            )
            severidad = st.selectbox(
                "Severidad:",
                list(SEVERIDADES.keys()),
                index=list(SEVERIDADES.keys()).index(vuln_editar.severidad) if es_edicion and vuln_editar.severidad in SEVERIDADES else 0
            )
        
        with col2:
            cvss = st.number_input(
                "CVSS Score (0-10):",
                min_value=0.0,
                max_value=10.0,
                value=vuln_editar.cvss_score if es_edicion and vuln_editar.cvss_score else 0.0,
                step=0.1
            )
            fuente = st.text_input(
                "Fuente:",
                value=vuln_editar.fuente if es_edicion else "Manual"
            )
            estado = st.selectbox(
                "Estado:",
                ["Identificada", "En Análisis", "Confirmada", "Mitigada", "Aceptada"],
                index=["Identificada", "En Análisis", "Confirmada", "Mitigada", "Aceptada"].index(vuln_editar.estado) if es_edicion else 0
            )
        
        descripcion = st.text_area(
            "Descripción:",
            value=vuln_editar.descripcion if es_edicion else "",
            height=100
        )
        
        amenazas = st.text_input(
            "Amenazas asociadas (separadas por coma):",
            value=vuln_editar.amenazas_asociadas if es_edicion else ""
        )
        
        controles = st.text_input(
            "Controles mitigantes (separados por coma):",
            value=vuln_editar.controles_mitigantes if es_edicion else ""
        )
        
        submitted = st.form_submit_button("💾 Guardar")
        
        if submitted:
            if not codigo or not nombre:
                st.error("Código y Nombre son obligatorios.")
            else:
                vuln = Vulnerabilidad(
                    id=vuln_editar.id if es_edicion else None,
                    id_evaluacion=id_evaluacion,
                    id_activo=id_activo,
                    codigo=codigo,
                    nombre=nombre,
                    descripcion=descripcion,
                    severidad=severidad,
                    cvss_score=cvss if cvss > 0 else None,
                    amenazas_asociadas=amenazas,
                    controles_mitigantes=controles,
                    fuente=fuente,
                    estado=estado
                )
                
                if es_edicion:
                    if actualizar_vulnerabilidad(vuln):
                        registrar_cambio(
                            tabla="VULNERABILIDADES_ACTIVO",
                            id_registro=str(vuln.id),
                            accion="UPDATE",
                            valores_nuevos={"codigo": codigo, "nombre": nombre, "severidad": severidad}
                        )
                        st.success("✅ Vulnerabilidad actualizada.")
                        st.session_state.pop("vuln_edit_mode", None)
                        st.rerun()
                    else:
                        st.error("Error al actualizar.")
                else:
                    nuevo_id = crear_vulnerabilidad(vuln)
                    if nuevo_id:
                        registrar_cambio(
                            tabla="VULNERABILIDADES_ACTIVO",
                            id_registro=str(nuevo_id),
                            accion="INSERT",
                            valores_nuevos={"codigo": codigo, "nombre": nombre, "severidad": severidad}
                        )
                        st.success(f"✅ Vulnerabilidad creada (ID: {nuevo_id})")
                        st.rerun()
                    else:
                        st.error("Error al crear.")


def render_sugerencias_ia(id_evaluacion: str):
    """Sugerencias automáticas de vulnerabilidades por IA"""
    
    st.subheader("🤖 Sugerencias Automáticas de Vulnerabilidades")
    st.info("El sistema sugiere vulnerabilidades comunes basándose en el tipo de activo.")
    
    # Obtener activos
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ID_Activo, Nombre_Activo, Tipo_Activo
            FROM INVENTARIO_ACTIVOS
            WHERE ID_Evaluacion = ?
            ORDER BY Nombre_Activo
        ''', [id_evaluacion])
        activos = cursor.fetchall()
    
    if not activos:
        st.warning("No hay activos en esta evaluación.")
        return
    
    # Selección de activo
    opciones_activos = [f"{a[1]} ({a[2]})" for a in activos]
    activo_sel = st.selectbox("Seleccionar activo:", opciones_activos, key="ia_vuln_activo")
    
    idx = opciones_activos.index(activo_sel)
    id_activo = activos[idx][0]
    tipo_activo = activos[idx][2]
    
    if st.button("🔍 Generar Sugerencias", key="gen_sugerencias"):
        with st.spinner("Analizando tipo de activo..."):
            sugerencias = sugerir_vulnerabilidades_ia(tipo_activo)
        
        if sugerencias:
            st.success(f"Se encontraron {len(sugerencias)} vulnerabilidades sugeridas.")
            
            for i, sug in enumerate(sugerencias):
                with st.expander(f"📌 {sug['codigo']} - {sug['nombre']}", expanded=i==0):
                    st.markdown(f"**Severidad:** {sug['severidad']}")
                    st.markdown(f"**Descripción:** {sug['descripcion']}")
                    
                    if st.button(f"✅ Aplicar esta sugerencia", key=f"apply_sug_{i}"):
                        vuln = Vulnerabilidad(
                            id_evaluacion=id_evaluacion,
                            id_activo=id_activo,
                            codigo=sug['codigo'],
                            nombre=sug['nombre'],
                            descripcion=sug['descripcion'],
                            severidad=sug['severidad'],
                            fuente="IA Sugerencia",
                            estado="Identificada"
                        )
                        nuevo_id = crear_vulnerabilidad(vuln)
                        if nuevo_id:
                            registrar_cambio(
                                tabla="VULNERABILIDADES_ACTIVO",
                                id_registro=str(nuevo_id),
                                accion="IA_SUGERENCIA",
                                valores_nuevos={"codigo": sug['codigo'], "fuente": "IA"}
                            )
                            st.success(f"✅ Vulnerabilidad añadida (ID: {nuevo_id})")
                            st.rerun()
        else:
            st.info("No se encontraron sugerencias específicas para este tipo de activo.")
