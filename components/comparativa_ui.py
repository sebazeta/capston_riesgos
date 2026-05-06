"""
COMPONENTE UI: COMPARATIVA DE EVALUACIONES
===========================================
Permite comparar evaluaciones y ver tendencias de riesgo.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List
from services import (
    comparar_evaluaciones,
    listar_historial_comparativas,
    get_tendencia_riesgo,
    ComparativaEvaluacion
)
from services.database_service import get_connection


def render_comparativa_tab(id_evaluacion_actual: str):
    """
    Renderiza el tab de comparativa de evaluaciones.
    """
    from utils.ui_styles import styled_header
    styled_header("📊", "Comparativa de Evaluaciones", "Compara resultados entre evaluaciones")
    
    # Obtener todas las evaluaciones disponibles
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ID_Evaluacion, Nombre, Fecha, Estado
            FROM EVALUACIONES
            ORDER BY Fecha DESC
        ''')
        evaluaciones = cursor.fetchall()
    
    if len(evaluaciones) < 2:
        st.info("Se requieren al menos 2 evaluaciones para comparar.")
        st.markdown("""
        **¿Por qué comparar evaluaciones?**
        - Medir la evolución del nivel de riesgo
        - Identificar activos que mejoraron o empeoraron
        - Validar la efectividad de los controles implementados
        - Documentar el progreso para auditorías
        """)
        return
    
    # Tabs internos
    tab_comparar, tab_historial, tab_tendencia = st.tabs([
        "🔄 Comparar",
        "📜 Historial",
        "📈 Tendencia"
    ])
    
    with tab_comparar:
        render_comparacion(evaluaciones, id_evaluacion_actual)
    
    with tab_historial:
        render_historial()
    
    with tab_tendencia:
        render_tendencia(evaluaciones)


def render_comparacion(evaluaciones: List, id_evaluacion_actual: str):
    """Comparar dos evaluaciones"""
    
    st.subheader("🔄 Comparar Evaluaciones")
    
    opciones = [f"{e[1]} ({e[2]}) - {e[3]}" for e in evaluaciones]
    ids = [e[0] for e in evaluaciones]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Evaluación Base (anterior)**")
        # Seleccionar por defecto la segunda más reciente
        idx_base = 1 if len(evaluaciones) > 1 else 0
        eval_base = st.selectbox("", opciones, index=idx_base, key="eval_base")
        id_base = ids[opciones.index(eval_base)]
    
    with col2:
        st.markdown("**Evaluación Actual (comparar)**")
        # Seleccionar por defecto la más reciente o la actual
        idx_actual = 0
        for i, e in enumerate(evaluaciones):
            if e[0] == id_evaluacion_actual:
                idx_actual = i
                break
        eval_actual = st.selectbox("", opciones, index=idx_actual, key="eval_actual")
        id_actual = ids[opciones.index(eval_actual)]
    
    if id_base == id_actual:
        st.warning("Seleccione dos evaluaciones diferentes para comparar.")
        return
    
    if st.button("📊 Ejecutar Comparación", key="btn_comparar"):
        with st.spinner("Comparando evaluaciones..."):
            resultado = comparar_evaluaciones(id_base, id_actual)
        
        if resultado:
            render_resultado_comparativa(resultado)
        else:
            st.error("Error al comparar evaluaciones. Verifique que ambas tengan resultados MAGERIT.")


def render_resultado_comparativa(comp: ComparativaEvaluacion):
    """Muestra el resultado de la comparación"""
    
    st.success(f"✅ Comparación completada: {comp.fecha_comparacion}")
    
    # Métricas principales
    st.markdown("### Resumen Ejecutivo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta_color = "normal" if comp.delta_riesgo_promedio <= 0 else "inverse"
        st.metric(
            "Riesgo Promedio",
            f"{comp.riesgo_promedio_destino:.2f}",
            delta=f"{comp.delta_riesgo_promedio:+.2f}",
            delta_color=delta_color
        )
    
    with col2:
        delta_color = "normal" if comp.delta_riesgo_maximo <= 0 else "inverse"
        st.metric(
            "Riesgo Máximo",
            f"{comp.riesgo_maximo_destino:.2f}",
            delta=f"{comp.delta_riesgo_maximo:+.2f}",
            delta_color=delta_color
        )
    
    with col3:
        st.metric(
            "Activos Mejorados",
            comp.activos_mejorados,
            delta=None
        )
    
    with col4:
        st.metric(
            "Activos Deteriorados",
            comp.activos_deteriorados,
            delta=None
        )
    
    # Indicador visual
    if comp.delta_riesgo_promedio < 0:
        st.success(f"📉 **El riesgo promedio disminuyó un {abs(comp.delta_riesgo_promedio / comp.riesgo_promedio_origen * 100):.1f}%**")
    elif comp.delta_riesgo_promedio > 0:
        st.error(f"📈 **El riesgo promedio aumentó un {abs(comp.delta_riesgo_promedio / comp.riesgo_promedio_origen * 100):.1f}%**")
    else:
        st.info("➡️ **El riesgo promedio se mantuvo estable**")
    
    # Detalle de cambios
    st.markdown("---")
    
    col_mej, col_det = st.columns(2)
    
    with col_mej:
        st.markdown("### ✅ Activos Mejorados")
        if comp.detalle_mejoras:
            df_mejoras = pd.DataFrame(comp.detalle_mejoras)
            df_mejoras.columns = ["ID", "Activo", "Anterior", "Actual", "Delta", "% Mejora"]
            st.dataframe(df_mejoras, use_container_width=True, hide_index=True)
        else:
            st.info("No hay activos con mejoras significativas.")
    
    with col_det:
        st.markdown("### ⚠️ Activos Deteriorados")
        if comp.detalle_deterioros:
            df_det = pd.DataFrame(comp.detalle_deterioros)
            df_det.columns = ["ID", "Activo", "Anterior", "Actual", "Delta", "% Aumento"]
            st.dataframe(df_det, use_container_width=True, hide_index=True)
        else:
            st.success("No hay activos con deterioro significativo.")
    
    # Activos sin cambio
    st.markdown(f"**Activos sin cambio significativo:** {comp.activos_sin_cambio}")


def render_historial():
    """Muestra el historial de comparaciones"""
    
    st.subheader("📜 Historial de Comparaciones")
    
    historial = listar_historial_comparativas()
    
    if not historial:
        st.info("No hay comparaciones previas registradas.")
        return
    
    df_data = []
    for h in historial:
        df_data.append({
            "Eval. Base": h["eval_origen"][:20] + "...",
            "Eval. Comparada": h["eval_destino"][:20] + "...",
            "Fecha": h["fecha"],
            "Delta Promedio": h["delta_promedio"],
            "Mejorados": h["mejorados"],
            "Deteriorados": h["deteriorados"]
        })
    
    df = pd.DataFrame(df_data)
    
    def color_delta(val):
        if isinstance(val, (int, float)):
            if val < 0:
                return "background-color: #ccffcc"
            elif val > 0:
                return "background-color: #ffcccc"
        return ""
    
    st.dataframe(
        df.style.map(color_delta, subset=["Delta Promedio"]),
        use_container_width=True,
        hide_index=True
    )


def render_tendencia(evaluaciones: List):
    """Muestra la tendencia de riesgo a lo largo del tiempo"""
    
    st.subheader("📈 Tendencia de Riesgo")
    
    if len(evaluaciones) < 2:
        st.info("Se requieren al menos 2 evaluaciones para mostrar tendencia.")
        return
    
    # Seleccionar evaluaciones a incluir
    st.markdown("**Seleccione las evaluaciones a incluir en la tendencia:**")
    
    eval_ids = []
    for e in evaluaciones[:10]:  # Máximo 10 evaluaciones
        if st.checkbox(f"{e[1]} ({e[2]})", value=True, key=f"trend_{e[0]}"):
            eval_ids.append(e[0])
    
    if len(eval_ids) < 2:
        st.warning("Seleccione al menos 2 evaluaciones.")
        return
    
    if st.button("📊 Generar Tendencia", key="btn_tendencia"):
        with st.spinner("Calculando tendencia..."):
            tendencia = get_tendencia_riesgo(eval_ids)
        
        if tendencia:
            # Crear DataFrame para gráfico
            df_trend = pd.DataFrame(tendencia)
            
            if not df_trend.empty:
                st.markdown("### Evolución del Riesgo")
                
                # Gráfico de línea
                st.line_chart(
                    df_trend.set_index("evaluacion")[["riesgo_promedio", "riesgo_maximo"]],
                    use_container_width=True
                )
                
                # Tabla detalle
                st.markdown("### Detalle por Evaluación")
                st.dataframe(df_trend, use_container_width=True, hide_index=True)
                
                # Análisis
                primera = df_trend.iloc[-1]["riesgo_promedio"] if len(df_trend) > 0 else 0
                ultima = df_trend.iloc[0]["riesgo_promedio"] if len(df_trend) > 0 else 0
                
                if ultima < primera:
                    reduccion = ((primera - ultima) / primera) * 100
                    st.success(f"📉 **Tendencia positiva:** Reducción del {reduccion:.1f}% en el riesgo promedio")
                elif ultima > primera:
                    aumento = ((ultima - primera) / primera) * 100
                    st.error(f"📈 **Tendencia negativa:** Aumento del {aumento:.1f}% en el riesgo promedio")
                else:
                    st.info("➡️ **Tendencia estable:** Sin cambios significativos")
        else:
            st.error("No se pudo calcular la tendencia.")
