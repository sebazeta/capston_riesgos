"""
COMPONENTE UI: AUDITORÍA Y TRAZABILIDAD
========================================
Permite visualizar el historial de cambios del sistema.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List
from services import (
    obtener_historial,
    obtener_historial_activo,
    obtener_estadisticas_auditoria,
    limpiar_auditoria_antigua,
    RegistroAuditoria,
    ACCIONES
)


def render_auditoria_tab():
    """
    Renderiza el tab de auditoría y trazabilidad.
    """
    st.header("📋 Auditoría y Trazabilidad")
    
    # Estadísticas generales
    stats = obtener_estadisticas_auditoria()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Registros", stats.get("total_registros", 0))
    with col2:
        st.metric("Modificaciones", stats.get("por_accion", {}).get("UPDATE", 0))
    with col3:
        st.metric("Creaciones", stats.get("por_accion", {}).get("INSERT", 0))
    with col4:
        st.metric("Sugerencias IA", stats.get("por_accion", {}).get("IA_SUGERENCIA", 0))
    
    st.divider()
    
    # Tabs internos
    tab_historial, tab_buscar, tab_stats, tab_admin = st.tabs([
        "📜 Historial Reciente",
        "🔍 Buscar",
        "📊 Estadísticas",
        "⚙️ Administración"
    ])
    
    with tab_historial:
        render_historial_reciente()
    
    with tab_buscar:
        render_busqueda()
    
    with tab_stats:
        render_estadisticas(stats)
    
    with tab_admin:
        render_administracion()


def render_historial_reciente():
    """Muestra el historial reciente de cambios"""
    
    st.subheader("📜 Últimos Cambios")
    
    # Filtro por acción
    acciones = ["Todas"] + list(ACCIONES.keys())
    accion_sel = st.selectbox("Filtrar por tipo de acción:", acciones, key="filter_accion")
    
    accion_filtro = None if accion_sel == "Todas" else accion_sel
    
    # Obtener historial
    historial = obtener_historial(accion=accion_filtro, limite=50)
    
    if not historial:
        st.info("No hay registros de auditoría.")
        return
    
    # Convertir a DataFrame
    df_data = []
    for reg in historial:
        accion_desc = ACCIONES.get(reg.accion, reg.accion)
        df_data.append({
            "Timestamp": reg.timestamp,
            "Tabla": reg.tabla_afectada,
            "ID Registro": reg.id_registro[:30] + "..." if len(reg.id_registro) > 30 else reg.id_registro,
            "Acción": accion_desc,
            "Usuario": reg.usuario
        })
    
    df = pd.DataFrame(df_data)
    
    # Aplicar estilos por acción
    def color_accion(val):
        colores = {
            "Creación": "background-color: #ccffcc",
            "Modificación": "background-color: #cce5ff",
            "Eliminación": "background-color: #ffcccc",
            "Sugerencia IA": "background-color: #e5ccff",
            "Validación IA": "background-color: #ffe5cc",
            "Evaluación MAGERIT": "background-color: #ccffff"
        }
        return colores.get(val, "")
    
    st.dataframe(
        df.style.map(color_accion, subset=["Acción"]),
        use_container_width=True,
        hide_index=True
    )
    
    # Detalle de registro seleccionado
    if historial:
        st.markdown("---")
        st.subheader("Detalle de Registro")
        
        reg_names = [f"{r.timestamp} - {r.tabla_afectada} - {ACCIONES.get(r.accion, r.accion)}" for r in historial]
        reg_sel = st.selectbox("Seleccionar registro:", reg_names, key="audit_detail")
        
        idx = reg_names.index(reg_sel)
        reg = historial[idx]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Información General**")
            st.markdown(f"- **Timestamp:** {reg.timestamp}")
            st.markdown(f"- **Tabla:** {reg.tabla_afectada}")
            st.markdown(f"- **ID Registro:** {reg.id_registro}")
            st.markdown(f"- **Acción:** {ACCIONES.get(reg.accion, reg.accion)}")
            st.markdown(f"- **Usuario:** {reg.usuario}")
        
        with col2:
            if reg.valores_anteriores:
                st.markdown("**Valores Anteriores**")
                st.json(reg.valores_anteriores)
            
            if reg.valores_nuevos:
                st.markdown("**Valores Nuevos**")
                st.json(reg.valores_nuevos)


def render_busqueda():
    """Búsqueda avanzada en el historial"""
    
    st.subheader("🔍 Búsqueda Avanzada")
    
    col1, col2 = st.columns(2)
    
    with col1:
        tabla = st.text_input("Tabla:", placeholder="INVENTARIO_ACTIVOS, RESULTADOS_MAGERIT...")
        id_registro = st.text_input("ID del Registro:", placeholder="ID del activo, evaluación...")
        accion = st.selectbox("Tipo de Acción:", ["Todas"] + list(ACCIONES.keys()), key="search_accion")
    
    with col2:
        fecha_desde = st.date_input("Desde:", value=None, key="search_desde")
        fecha_hasta = st.date_input("Hasta:", value=None, key="search_hasta")
        limite = st.number_input("Máximo resultados:", min_value=10, max_value=500, value=100)
    
    if st.button("🔍 Buscar", key="btn_buscar_audit"):
        with st.spinner("Buscando..."):
            resultados = obtener_historial(
                tabla=tabla if tabla else None,
                id_registro=id_registro if id_registro else None,
                accion=None if accion == "Todas" else accion,
                fecha_desde=str(fecha_desde) if fecha_desde else None,
                fecha_hasta=str(fecha_hasta) if fecha_hasta else None,
                limite=limite
            )
        
        if resultados:
            st.success(f"Se encontraron {len(resultados)} registros.")
            
            df_data = []
            for reg in resultados:
                df_data.append({
                    "Timestamp": reg.timestamp,
                    "Tabla": reg.tabla_afectada,
                    "ID Registro": reg.id_registro,
                    "Acción": ACCIONES.get(reg.accion, reg.accion),
                    "Usuario": reg.usuario
                })
            
            st.dataframe(pd.DataFrame(df_data), use_container_width=True, hide_index=True)
        else:
            st.info("No se encontraron registros con los criterios especificados.")
    
    # Búsqueda por activo
    st.markdown("---")
    st.subheader("🔍 Historial de un Activo")
    
    id_activo = st.text_input("ID del Activo:", placeholder="Pegue el ID del activo aquí...")
    
    if id_activo and st.button("🔍 Buscar Historial del Activo", key="btn_buscar_activo"):
        historial_activo = obtener_historial_activo(id_activo)
        
        if historial_activo:
            st.success(f"Se encontraron {len(historial_activo)} registros para este activo.")
            
            for reg in historial_activo:
                with st.expander(f"{reg.timestamp} - {ACCIONES.get(reg.accion, reg.accion)}"):
                    st.markdown(f"**Tabla:** {reg.tabla_afectada}")
                    st.markdown(f"**Usuario:** {reg.usuario}")
                    
                    if reg.valores_anteriores:
                        st.markdown("**Antes:**")
                        st.json(reg.valores_anteriores)
                    
                    if reg.valores_nuevos:
                        st.markdown("**Después:**")
                        st.json(reg.valores_nuevos)
        else:
            st.info("No se encontró historial para este activo.")


def render_estadisticas(stats: Dict):
    """Muestra estadísticas de auditoría"""
    
    st.subheader("📊 Estadísticas de Auditoría")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Por Tipo de Acción")
        if stats.get("por_accion"):
            df_acciones = pd.DataFrame([
                {"Acción": ACCIONES.get(k, k), "Cantidad": v}
                for k, v in stats["por_accion"].items()
            ])
            st.bar_chart(df_acciones.set_index("Acción"))
        else:
            st.info("Sin datos")
    
    with col2:
        st.markdown("### Por Tabla")
        if stats.get("por_tabla"):
            df_tablas = pd.DataFrame([
                {"Tabla": k, "Cantidad": v}
                for k, v in list(stats["por_tabla"].items())[:10]  # Top 10
            ])
            st.bar_chart(df_tablas.set_index("Tabla"))
        else:
            st.info("Sin datos")
    
    st.markdown("### Actividad Últimos 7 Días")
    if stats.get("ultimos_7_dias"):
        df_dias = pd.DataFrame(stats["ultimos_7_dias"])
        st.line_chart(df_dias.set_index("fecha"))
    else:
        st.info("Sin actividad reciente")
    
    st.markdown("### Por Usuario")
    if stats.get("por_usuario"):
        for usuario, cantidad in list(stats["por_usuario"].items())[:10]:
            st.markdown(f"- **{usuario}**: {cantidad} acciones")


def render_administracion():
    """Administración de la auditoría"""
    
    st.subheader("⚙️ Administración")
    
    st.warning("⚠️ Las acciones en esta sección son irreversibles.")
    
    st.markdown("### Limpieza de Registros Antiguos")
    st.markdown("Elimina registros de auditoría más antiguos que el número de días especificado.")
    
    dias = st.number_input(
        "Días a retener:",
        min_value=30,
        max_value=365,
        value=90,
        help="Se eliminarán registros más antiguos que este número de días"
    )
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        confirmar = st.checkbox("Confirmo esta acción")
    
    with col2:
        if st.button("🗑️ Limpiar Registros Antiguos", disabled=not confirmar):
            with st.spinner("Limpiando registros..."):
                eliminados = limpiar_auditoria_antigua(dias)
            
            if eliminados > 0:
                st.success(f"✅ Se eliminaron {eliminados} registros antiguos.")
            else:
                st.info("No había registros antiguos para eliminar.")
    
    st.markdown("---")
    st.markdown("### Exportar Auditoría")
    st.info("Próximamente: Exportación de registros de auditoría a Excel/CSV")
