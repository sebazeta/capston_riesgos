"""
COMPONENTE UI — VIDA ÚTIL DE ACTIVOS
======================================
Visualiza la vida útil restante de cada activo, con alertas
para activos próximos a fin de vida o ya obsoletos.
"""
import streamlit as st
import pandas as pd
import datetime as dt
import plotly.graph_objects as go
import plotly.express as px
from services.database_service import get_connection, read_table


# Vida útil por defecto según tipo de activo (en años)
VIDA_UTIL_POR_TIPO = {
    "Servidor Físico": 5,
    "Servidor Virtual": 7,
    "Firewall": 5,
    "Switch": 7,
    "Router": 7,
    "Storage": 5,
    "Backup": 5,
    "Base de datos": 8,
    "Servidor web": 6,
    "Servidor aplicaciones": 6,
    "Otro": 5,
}


def get_vida_util_default(tipo_activo: str, tipo_servicio: str) -> float:
    """Obtiene la vida útil por defecto según tipo de activo/servicio"""
    if tipo_servicio in VIDA_UTIL_POR_TIPO:
        return VIDA_UTIL_POR_TIPO[tipo_servicio]
    if tipo_activo in VIDA_UTIL_POR_TIPO:
        return VIDA_UTIL_POR_TIPO[tipo_activo]
    return 5.0


def calcular_vida_util_activos(eval_id: str) -> pd.DataFrame:
    """
    Calcula la vida útil restante de todos los activos de una evaluación.
    
    Returns:
        DataFrame con columnas: ID_Activo, Nombre_Activo, Tipo_Activo, Tipo_Servicio,
        Fecha_Adquisicion, Vida_Util_Anios, Fecha_Fin_Vida, Dias_Restantes,
        Pct_Vida_Restante, Estado_Vida
    """
    try:
        activos = read_table("INVENTARIO_ACTIVOS")
        if activos.empty:
            return pd.DataFrame()
        
        activos = activos[activos["ID_Evaluacion"].astype(str) == str(eval_id)]
        if activos.empty:
            return pd.DataFrame()
        
        hoy = dt.datetime.now()
        resultados = []
        
        for _, activo in activos.iterrows():
            tipo_activo = activo.get("Tipo_Activo", "Otro")
            tipo_servicio = activo.get("Tipo_Servicio", "Otro")
            
            # Vida útil: usar campo personalizado o default
            vida_util = activo.get("Vida_Util_Anios")
            if not vida_util or pd.isna(vida_util) or vida_util == 0:
                vida_util = get_vida_util_default(tipo_activo, tipo_servicio)
            vida_util = float(vida_util)
            
            # Fecha de adquisición: usar campo o fecha de creación
            fecha_adq_str = activo.get("Fecha_Adquisicion")
            if not fecha_adq_str or pd.isna(fecha_adq_str) or str(fecha_adq_str).strip() == "":
                fecha_adq_str = activo.get("Fecha_Creacion", hoy.strftime("%Y-%m-%d"))
            
            try:
                if isinstance(fecha_adq_str, str):
                    fecha_adq = dt.datetime.strptime(fecha_adq_str[:10], "%Y-%m-%d")
                else:
                    fecha_adq = hoy
            except:
                fecha_adq = hoy
            
            # Calcular fin de vida
            fecha_fin = fecha_adq + dt.timedelta(days=vida_util * 365.25)
            dias_restantes = (fecha_fin - hoy).days
            vida_total_dias = vida_util * 365.25
            pct_restante = max(0, min(100, (dias_restantes / vida_total_dias) * 100))
            
            # Estado
            if dias_restantes <= 0:
                estado = "🔴 Obsoleto"
            elif dias_restantes <= 180:
                estado = "🟠 Crítico (<6 meses)"
            elif dias_restantes <= 365:
                estado = "🟡 Próximo (<1 año)"
            elif pct_restante <= 30:
                estado = "🟡 Atención"
            else:
                estado = "🟢 Vigente"
            
            resultados.append({
                "ID_Activo": activo["ID_Activo"],
                "Nombre_Activo": activo["Nombre_Activo"],
                "Tipo_Activo": tipo_activo,
                "Tipo_Servicio": tipo_servicio,
                "Fabricante": activo.get("Fabricante", ""),
                "Modelo": activo.get("Modelo", ""),
                "Fecha_Adquisicion": fecha_adq.strftime("%Y-%m-%d"),
                "Vida_Util_Anios": vida_util,
                "Fecha_Fin_Vida": fecha_fin.strftime("%Y-%m-%d"),
                "Dias_Restantes": dias_restantes,
                "Pct_Vida_Restante": round(pct_restante, 1),
                "Estado_Vida": estado,
            })
        
        return pd.DataFrame(resultados)
    except Exception as e:
        print(f"Error calculando vida útil: {e}")
        return pd.DataFrame()


def actualizar_vida_util_activo(activo_id: str, fecha_adquisicion: str = None,
                                 vida_util_anios: float = None,
                                 fabricante: str = None, modelo: str = None) -> bool:
    """Actualiza los datos de vida útil de un activo"""
    try:
        with get_connection() as conn:
            updates = []
            params = []
            if fecha_adquisicion is not None:
                updates.append("Fecha_Adquisicion = ?")
                params.append(fecha_adquisicion)
            if vida_util_anios is not None:
                updates.append("Vida_Util_Anios = ?")
                params.append(vida_util_anios)
            if fabricante is not None:
                updates.append("Fabricante = ?")
                params.append(fabricante)
            if modelo is not None:
                updates.append("Modelo = ?")
                params.append(modelo)
            
            if updates:
                query = f"UPDATE INVENTARIO_ACTIVOS SET {', '.join(updates)} WHERE ID_Activo = ?"
                params.append(activo_id)
                conn.execute(query, params)
        return True
    except Exception as e:
        print(f"Error actualizando vida útil: {e}")
        return False


# ==================== RENDER UI ====================

def render_vida_util(eval_id: str, eval_nombre: str):
    """Renderiza la sección de vida útil de activos"""
    
    st.subheader("⏳ Vida Útil de Activos")
    st.caption("Visualiza cuánto tiempo de vida útil le resta a cada activo de infraestructura.")
    
    df = calcular_vida_util_activos(eval_id)
    
    if df.empty:
        st.info("No hay activos registrados en esta evaluación.")
        return
    
    # ===== MÉTRICAS RESUMEN =====
    total = len(df)
    obsoletos = len(df[df["Dias_Restantes"] <= 0])
    criticos = len(df[(df["Dias_Restantes"] > 0) & (df["Dias_Restantes"] <= 180)])
    proximos = len(df[(df["Dias_Restantes"] > 180) & (df["Dias_Restantes"] <= 365)])
    vigentes = total - obsoletos - criticos - proximos
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🟢 Vigentes", vigentes)
    with c2:
        st.metric("🟡 Próximos (< 1 año)", proximos + len(df[df["Estado_Vida"] == "🟡 Atención"]))
    with c3:
        st.metric("🟠 Críticos (< 6 meses)", criticos, delta=f"-{criticos}" if criticos > 0 else None, delta_color="inverse")
    with c4:
        st.metric("🔴 Obsoletos", obsoletos, delta=f"-{obsoletos}" if obsoletos > 0 else None, delta_color="inverse")
    
    st.markdown("---")
    
    # ===== GRÁFICO GAUGE POR ACTIVO =====
    st.markdown("#### 📊 Vida Útil Restante por Activo")
    
    # Gráfico de barras horizontal
    df_sorted = df.sort_values("Pct_Vida_Restante", ascending=True)
    
    colores = []
    for _, row in df_sorted.iterrows():
        pct = row["Pct_Vida_Restante"]
        if pct <= 0:
            colores.append("#ff4444")
        elif pct <= 20:
            colores.append("#ff8800")
        elif pct <= 40:
            colores.append("#ffcc00")
        else:
            colores.append("#00cc66")
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_sorted["Nombre_Activo"],
        x=df_sorted["Pct_Vida_Restante"],
        orientation='h',
        marker_color=colores,
        text=[f"{p:.0f}% ({d} días)" for p, d in
              zip(df_sorted["Pct_Vida_Restante"], df_sorted["Dias_Restantes"])],
        textposition='auto',
        hovertemplate="<b>%{y}</b><br>Vida restante: %{x:.0f}%<br>Días: %{customdata[0]}<br>Fin de vida: %{customdata[1]}<extra></extra>",
        customdata=list(zip(df_sorted["Dias_Restantes"], df_sorted["Fecha_Fin_Vida"]))
    ))
    fig.update_layout(
        title="% de Vida Útil Restante",
        xaxis_title="% Restante",
        yaxis_title="",
        height=max(300, len(df) * 40),
        xaxis=dict(range=[0, 100]),
        margin=dict(l=10)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ===== TABLA DETALLADA =====
    st.markdown("#### 📋 Detalle de Vida Útil")
    
    df_display = df[["Nombre_Activo", "Tipo_Servicio", "Fecha_Adquisicion",
                      "Vida_Util_Anios", "Fecha_Fin_Vida", "Dias_Restantes",
                      "Pct_Vida_Restante", "Estado_Vida"]].copy()
    df_display.columns = ["Activo", "Tipo", "Adquisición", "Vida Útil (años)",
                           "Fin de Vida", "Días Restantes", "% Restante", "Estado"]
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # ===== EDITAR DATOS DE VIDA ÚTIL =====
    st.markdown("---")
    st.markdown("#### ✏️ Actualizar Datos de Vida Útil")
    st.caption("Puedes ajustar la fecha de adquisición y vida útil estimada de cada activo.")
    
    activo_edit = st.selectbox(
        "Seleccionar activo",
        df["ID_Activo"].tolist(),
        format_func=lambda x: df[df["ID_Activo"] == x]["Nombre_Activo"].values[0],
        key="vida_util_edit_activo"
    )
    
    row_edit = df[df["ID_Activo"] == activo_edit].iloc[0]
    
    with st.form("form_vida_util"):
        col_a, col_b = st.columns(2)
        with col_a:
            fecha_adq = st.date_input(
                "Fecha de Adquisición",
                value=dt.datetime.strptime(row_edit["Fecha_Adquisicion"], "%Y-%m-%d"),
                key="vu_fecha"
            )
            fabricante = st.text_input("Fabricante", value=row_edit.get("Fabricante", "") or "",
                                        key="vu_fabricante")
        with col_b:
            vida_anios = st.number_input(
                "Vida Útil (años)", min_value=1.0, max_value=20.0,
                value=float(row_edit["Vida_Util_Anios"]), step=0.5, key="vu_anios"
            )
            modelo_hw = st.text_input("Modelo", value=row_edit.get("Modelo", "") or "",
                                       key="vu_modelo")
        
        if st.form_submit_button("💾 Guardar", type="primary"):
            ok = actualizar_vida_util_activo(
                activo_edit,
                fecha_adquisicion=fecha_adq.strftime("%Y-%m-%d"),
                vida_util_anios=vida_anios,
                fabricante=fabricante,
                modelo=modelo_hw
            )
            if ok:
                st.success("✅ Datos de vida útil actualizados")
                st.rerun()
            else:
                st.error("Error al actualizar")
    
    # ===== ALERTAS =====
    if obsoletos > 0 or criticos > 0:
        st.markdown("---")
        st.markdown("#### ⚠️ Alertas de Vida Útil")
        
        alertas = df[df["Dias_Restantes"] <= 180].sort_values("Dias_Restantes")
        for _, row in alertas.iterrows():
            if row["Dias_Restantes"] <= 0:
                st.error(f"🔴 **{row['Nombre_Activo']}** — Obsoleto desde {abs(row['Dias_Restantes'])} días. Reemplazo urgente.")
            else:
                st.warning(f"🟠 **{row['Nombre_Activo']}** — {row['Dias_Restantes']} días restantes. Planificar renovación.")
