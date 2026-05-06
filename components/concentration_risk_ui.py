"""
Componente UI para Riesgo por Concentración - Proyecto TITA
============================================================
Interfaz de usuario para:
- Asignar dependencias Host-VM
- Visualizar blast radius
- Dashboard de concentración
- Alertas SPOF
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from services.database_service import read_table
from services.concentration_risk_service import (
    init_concentration_tables,
    asignar_host_a_vm,
    get_vms_de_host,
    get_hosts_evaluacion,
    calcular_concentracion_evaluacion,
    calcular_herencia_evaluacion,
    get_hosts_spof,
    get_ranking_hosts_blast_radius,
    get_vms_con_riesgo_heredado,
    get_resumen_concentracion
)


def render_asignacion_dependencias(eval_id: str):
    """Renderiza el panel para asignar dependencias Host-VM"""
    st.subheader("🔗 Asignación de Dependencias Host-VM")
    
    # Inicializar tablas
    init_concentration_tables()
    
    activos = read_table("INVENTARIO_ACTIVOS")
    activos_eval = activos[activos["ID_Evaluacion"] == eval_id] if not activos.empty else pd.DataFrame()
    
    if activos_eval.empty:
        st.info("No hay activos registrados en esta evaluación.")
        return
    
    # Separar hosts y VMs
    hosts = activos_eval[activos_eval["Tipo_Activo"] == "Servidor Físico"]
    vms = activos_eval[activos_eval["Tipo_Activo"] == "Servidor Virtual"]
    
    if hosts.empty:
        st.warning("⚠️ No hay Servidores Físicos (hosts) registrados. El modelo de concentración requiere hosts físicos.")
        return
    
    if vms.empty:
        st.info("ℹ️ No hay Servidores Virtuales (VMs) registrados. Puede agregar VMs para configurar dependencias.")
        return
    
    # Crear opciones para selectores
    host_options = {
        row["ID_Activo"]: f"{row['Nombre_Activo']} ({row['ID_Activo']})"
        for _, row in hosts.iterrows()
    }
    
    vm_options = {
        row["ID_Activo"]: f"{row['Nombre_Activo']} ({row['ID_Activo']}) - Host: {row.get('ID_Host', 'Sin asignar')}"
        for _, row in vms.iterrows()
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Asignar VM a Host")
        
        selected_vm = st.selectbox(
            "Seleccionar VM",
            options=list(vm_options.keys()),
            format_func=lambda x: vm_options[x],
            key="vm_select"
        )
        
        selected_host = st.selectbox(
            "Asignar a Host",
            options=list(host_options.keys()),
            format_func=lambda x: host_options[x],
            key="host_select"
        )
        
        tipo_dependencia = st.radio(
            "Tipo de Dependencia",
            options=["total", "parcial", "ninguna"],
            horizontal=True,
            help="""
            - **Total**: La VM depende completamente del host (peso 1.0)
            - **Parcial**: Puede migrar a otro host (peso 0.5)  
            - **Ninguna**: Independiente del host (peso 0.0)
            """
        )
        
        if st.button("💾 Asignar Dependencia", type="primary"):
            success, msg = asignar_host_a_vm(eval_id, selected_vm, selected_host, tipo_dependencia)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    
    with col2:
        st.markdown("### Dependencias Actuales")
        
        deps = []
        for _, vm in vms.iterrows():
            id_host = vm.get("ID_Host")
            host_nombre = "(Sin asignar)"
            
            if id_host and pd.notna(id_host):
                host_match = hosts[hosts["ID_Activo"] == id_host]
                if not host_match.empty:
                    host_nombre = host_match.iloc[0]["Nombre_Activo"]
            
            deps.append({
                "VM": vm["Nombre_Activo"],
                "Host": host_nombre,
                "Dependencia": vm.get("Tipo_Dependencia", "total")
            })
        
        df_deps = pd.DataFrame(deps)
        st.dataframe(df_deps, use_container_width=True, hide_index=True)


def render_dashboard_concentracion(eval_id: str):
    """Renderiza el dashboard de riesgo por concentración"""
    st.subheader("📊 Dashboard de Riesgo por Concentración")
    
    # Botón para recalcular
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
        if st.button("🔄 Recalcular", type="primary"):
            with st.spinner("Calculando riesgo por concentración..."):
                # Fase 1: Blast Radius
                resultados = calcular_concentracion_evaluacion(eval_id)
                
                # Fase 2: Herencia
                herencias = calcular_herencia_evaluacion(eval_id)
                
                st.success(f"✅ Calculado: {len(resultados)} hosts, {len(herencias)} VMs")
    
    # Métricas resumen
    resumen = get_resumen_concentracion(eval_id)
    
    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1:
        st.metric("Hosts Físicos", resumen["total_hosts"])
    
    with c2:
        st.metric(
            "Hosts SPOF", 
            resumen["hosts_spof"],
            delta=None if resumen["hosts_spof"] == 0 else "⚠️ Crítico",
            delta_color="inverse" if resumen["hosts_spof"] > 0 else "normal"
        )
    
    with c3:
        st.metric("Max Blast Radius", f"{resumen['max_blast_radius']:.1f}")
    
    with c4:
        st.metric("VMs con Herencia", resumen["vms_afectadas"])
    
    with c5:
        st.metric("Riesgo Prom. Ajust.", f"{resumen['riesgo_promedio_ajustado']:.1f}")
    
    # Alertas SPOF
    spofs = get_hosts_spof(eval_id)
    if not spofs.empty:
        st.error("### ⚠️ ALERTAS: Single Points of Failure (SPOF)")
        for _, spof in spofs.iterrows():
            st.warning(f"""
            **{spof['Nombre_Host']}** ({spof['ID_Host']})
            - VMs dependientes: {spof['Num_VMs_Dependientes']}
            - Blast Radius: {spof['Blast_Radius']:.1f}
            - Factor de Concentración: +{spof['Factor_Concentracion']}
            - Riesgo Ajustado: {spof['Riesgo_Ajustado']:.1f}
            """)
    
    # Tabs para visualización
    tab1, tab2, tab3 = st.tabs(["📈 Ranking Hosts", "🔗 VMs Heredadas", "📊 Gráficos"])
    
    with tab1:
        render_ranking_hosts(eval_id)
    
    with tab2:
        render_vms_heredadas(eval_id)
    
    with tab3:
        render_graficos_concentracion(eval_id)


def render_ranking_hosts(eval_id: str):
    """Muestra ranking de hosts por blast radius"""
    st.markdown("#### Ranking de Hosts por Blast Radius")
    
    ranking = get_ranking_hosts_blast_radius(eval_id)
    
    if ranking.empty:
        st.info("No hay datos de concentración. Haga clic en 'Recalcular'.")
        return
    
    # Agregar indicadores visuales
    ranking_display = ranking.copy()
    ranking_display["Estado"] = ranking_display.apply(
        lambda r: "🔴 SPOF" if r.get("Es_SPOF") else (
            "🟡 Medio" if r.get("Factor_Concentracion", 0) >= 1 else "🟢 OK"
        ), axis=1
    )
    
    ranking_display["Δ Impacto"] = ranking_display.apply(
        lambda r: f"+{r['Impacto_D_Ajustado'] - r['Impacto_D_Original']}" 
        if r['Impacto_D_Ajustado'] > r['Impacto_D_Original'] else "0", axis=1
    )
    
    st.dataframe(
        ranking_display[[
            "Estado", "Nombre_Host", "Num_VMs_Dependientes",
            "Blast_Radius", "Factor_Concentracion", "Δ Impacto", 
            "Riesgo_Ajustado"
        ]].rename(columns={
            "Nombre_Host": "Host",
            "Num_VMs_Dependientes": "VMs",
            "Blast_Radius": "Blast Radius",
            "Factor_Concentracion": "Factor Conc.",
            "Riesgo_Ajustado": "Riesgo Ajustado"
        }),
        use_container_width=True,
        hide_index=True
    )


def render_vms_heredadas(eval_id: str):
    """Muestra VMs cuyo riesgo fue ajustado por herencia"""
    st.markdown("#### VMs con Riesgo Heredado del Host")
    
    vms = get_vms_con_riesgo_heredado(eval_id)
    
    if vms.empty:
        st.info("No hay VMs con riesgo heredado (el riesgo propio supera al heredado).")
        return
    
    for _, vm in vms.iterrows():
        with st.expander(f"🖥️ {vm.get('ID_Activo')} - Riesgo Final: {vm['Riesgo_Final']:.1f}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Riesgo Propio VM", f"{vm['Riesgo_VM_Propio']:.1f}")
                st.metric("Riesgo Host", f"{vm['Riesgo_Host']:.1f}")
            
            with col2:
                st.metric("Riesgo Heredado", f"{vm['Riesgo_Heredado']:.1f}")
                st.metric(
                    "Riesgo Final", 
                    f"{vm['Riesgo_Final']:.1f}",
                    delta=f"+{(vm['Riesgo_Final'] - vm['Riesgo_VM_Propio']):.1f}" 
                    if vm['Ajuste_Aplicado'] else "Sin ajuste"
                )
            
            st.caption(f"📝 {vm['Justificacion']}")


def render_graficos_concentracion(eval_id: str):
    """Renderiza gráficos de concentración"""
    st.markdown("#### Visualización de Concentración")
    
    ranking = get_ranking_hosts_blast_radius(eval_id)
    
    if ranking.empty:
        st.info("No hay datos para graficar.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras - Blast Radius por Host
        fig_bar = px.bar(
            ranking,
            x="Nombre_Host",
            y="Blast_Radius",
            color="Es_SPOF",
            color_discrete_map={0: "#4CAF50", 1: "#F44336"},
            title="Blast Radius por Host",
            labels={"Nombre_Host": "Host", "Blast_Radius": "Blast Radius", "Es_SPOF": "SPOF"}
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        # Gráfico de dispersión - VMs vs Riesgo
        fig_scatter = px.scatter(
            ranking,
            x="Num_VMs_Dependientes",
            y="Riesgo_Ajustado",
            size="Blast_Radius",
            color="Factor_Concentracion",
            hover_name="Nombre_Host",
            title="Concentración vs Riesgo",
            labels={
                "Num_VMs_Dependientes": "# VMs Dependientes",
                "Riesgo_Ajustado": "Riesgo Ajustado",
                "Factor_Concentracion": "Factor Conc."
            },
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Mapa de calor de riesgo
    if len(ranking) > 1:
        st.markdown("##### Mapa de Calor: Factor de Concentración")
        
        fig_heat = go.Figure(data=go.Heatmap(
            z=[ranking["Factor_Concentracion"].tolist()],
            x=ranking["Nombre_Host"].tolist(),
            y=["Factor Conc."],
            colorscale="RdYlGn_r",
            zmin=0,
            zmax=4
        ))
        fig_heat.update_layout(height=150, margin=dict(t=30, b=30))
        st.plotly_chart(fig_heat, use_container_width=True)


def render_concentracion_mini_card(eval_id: str):
    """Renderiza una mini tarjeta de resumen para el dashboard principal"""
    resumen = get_resumen_concentracion(eval_id)
    
    if resumen["total_hosts"] == 0:
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if resumen["hosts_spof"] > 0:
            st.error(f"⚠️ {resumen['hosts_spof']} SPOF")
        else:
            st.success("✅ Sin SPOF")
    
    with col2:
        st.metric("Max Blast", f"{resumen['max_blast_radius']:.0f}")
    
    with col3:
        st.metric("VMs Afectadas", resumen["vms_afectadas"])


def render_concentracion_tab(eval_id: str):
    """Renderiza el tab completo de concentración"""
    from utils.ui_styles import styled_header
    styled_header("🎯", "Riesgo por Concentración", "Análisis de dependencias host-VM y blast radius")
    
    st.markdown("""
    El **riesgo por concentración** analiza cómo las dependencias entre hosts físicos y 
    máquinas virtuales afectan el perfil de riesgo general.
    
    **Modelo Híbrido implementado:**
    1. **Blast Radius** (VM → Host): El host hereda criticidad de sus VMs
    2. **Herencia** (Host → VM): Las VMs heredan riesgo del host comprometido
    """)
    
    tabs = st.tabs(["🔗 Asignar Dependencias", "📊 Dashboard"])
    
    with tabs[0]:
        render_asignacion_dependencias(eval_id)
    
    with tabs[1]:
        render_dashboard_concentracion(eval_id)
