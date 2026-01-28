"""
COMPONENTE UI: Gestión de Degradación MAGERIT
==============================================
Permite capturar/editar manualmente la degradación por (activo, amenaza).
Implementa el flujo del Marco Teórico MAGERIT.
"""
import streamlit as st
import pandas as pd
import json
import datetime as dt
from typing import Dict, List, Optional, Any

from services.database_service import get_connection, read_table
from services.degradacion_service import (
    DegradacionAmenaza,
    obtener_degradacion,
    guardar_degradacion,
    obtener_degradaciones_activo,
    eliminar_degradacion,
    calcular_impacto_con_degradacion,
    calcular_riesgo_objetivo,
    supera_limite,
    obtener_limite_evaluacion,
    sugerir_degradacion_ia,
    validar_trazabilidad_completa
)


# Mapeo de niveles descriptivos a valores float
NIVELES_DEGRADACION = {
    "Muy Bajo (0.1)": 0.1,
    "Bajo (0.3)": 0.3,
    "Medio (0.5)": 0.5,
    "Alto (0.7)": 0.7,
    "Muy Alto (0.9)": 0.9,
    "Total (1.0)": 1.0
}

NIVELES_DEGRADACION_INV = {v: k for k, v in NIVELES_DEGRADACION.items()}


def get_nivel_from_float(valor: float) -> str:
    """Convierte un float a su nivel descriptivo más cercano"""
    if valor <= 0.15:
        return "Muy Bajo (0.1)"
    elif valor <= 0.4:
        return "Bajo (0.3)"
    elif valor <= 0.6:
        return "Medio (0.5)"
    elif valor <= 0.8:
        return "Alto (0.7)"
    elif valor < 1.0:
        return "Muy Alto (0.9)"
    else:
        return "Total (1.0)"


def get_color_estado(estado: str) -> str:
    """Retorna color según estado"""
    colores = {
        "Pendiente": "#FFA500",  # Naranja
        "Calculado": "#32CD32",  # Verde
        "IA": "#1E90FF",         # Azul
        "Manual": "#228B22"       # Verde oscuro
    }
    return colores.get(estado, "#808080")


def get_amenazas_con_degradacion(eval_id: str, activo_id: str) -> pd.DataFrame:
    """
    Obtiene todas las amenazas identificadas para un activo con su degradación.
    Combina datos de RESULTADOS_MAGERIT con DEGRADACION_AMENAZAS.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener amenazas del resultado MAGERIT
            cursor.execute('''
                SELECT Amenazas_JSON, Impacto_D, Impacto_I, Impacto_C
                FROM RESULTADOS_MAGERIT
                WHERE ID_Evaluacion = ? AND ID_Activo = ?
            ''', [eval_id, activo_id])
            
            row = cursor.fetchone()
            if not row or not row[0]:
                return pd.DataFrame()
            
            amenazas_json = json.loads(row[0])
            impacto_d, impacto_i, impacto_c = row[1], row[2], row[3]
            criticidad = max(impacto_d or 1, impacto_i or 1, impacto_c or 1)
            
            # Obtener degradaciones
            degradaciones = obtener_degradaciones_activo(eval_id, activo_id)
            deg_dict = {d.codigo_amenaza: d for d in degradaciones}
            
            # Construir DataFrame
            data = []
            for amenaza in amenazas_json:
                codigo = amenaza.get("codigo", "")
                deg = deg_dict.get(codigo)
                
                if deg:
                    # Tiene degradación → calcular
                    max_deg = deg.degradacion_maxima
                    impacto_calc = round(criticidad * max_deg, 2)
                    frecuencia = amenaza.get("probabilidad", 3)
                    riesgo_calc = round(frecuencia * impacto_calc, 2)
                    estado = "Manual" if deg.fuente == "manual" else "IA"
                else:
                    # Sin degradación → Pendiente
                    max_deg = None
                    impacto_calc = None
                    riesgo_calc = None
                    estado = "Pendiente"
                
                data.append({
                    "Código": codigo,
                    "Amenaza": amenaza.get("amenaza", "")[:40],
                    "Tipo": amenaza.get("tipo_amenaza", ""),
                    "Frecuencia": amenaza.get("probabilidad", 3),
                    "Deg_D": deg.degradacion_d if deg else None,
                    "Deg_I": deg.degradacion_i if deg else None,
                    "Deg_C": deg.degradacion_c if deg else None,
                    "Max_Deg": max_deg,
                    "Fuente": deg.fuente if deg else None,
                    "Impacto": impacto_calc,
                    "Riesgo": riesgo_calc,
                    "Estado": estado,
                    "Criticidad": criticidad,
                    "Justificacion": deg.justificacion if deg else ""
                })
            
            return pd.DataFrame(data)
            
    except Exception as e:
        st.error(f"Error obteniendo amenazas: {e}")
        return pd.DataFrame()


def render_degradacion_tab(eval_id: str):
    """
    Renderiza la pestaña completa de gestión de degradación.
    """
    st.header("⚙️ Gestión de Degradación")
    
    st.markdown("""
    La **Degradación** representa el daño potencial que una amenaza puede causar sobre un activo
    en cada dimensión (Disponibilidad, Integridad, Confidencialidad).
    
    📌 **Fórmula MAGERIT:**
    - `IMPACTO = CRITICIDAD × MAX(Deg_D, Deg_I, Deg_C)`
    - `RIESGO = FRECUENCIA × IMPACTO`
    
    ⚠️ Los riesgos con estado **Pendiente** no se calculan hasta definir la degradación.
    """)
    
    # Obtener activos de la evaluación
    activos = read_table("INVENTARIO_ACTIVOS")
    activos_eval = activos[activos["ID_Evaluacion"] == eval_id]
    
    if activos_eval.empty:
        st.warning("⚠️ No hay activos en esta evaluación. Ve a la pestaña **Activos** para crearlos.")
        return
    
    # Selector de activo
    col1, col2 = st.columns([2, 1])
    with col1:
        opciones_activos = activos_eval.apply(
            lambda x: f"{x['ID_Activo']} - {x['Nombre_Activo']}", axis=1
        ).tolist()
        
        activo_seleccionado = st.selectbox(
            "📦 Seleccionar Activo",
            opciones_activos,
            key="deg_activo_select"
        )
        
        if activo_seleccionado:
            activo_id = activo_seleccionado.split(" - ")[0]
    
    with col2:
        limite = obtener_limite_evaluacion(eval_id)
        st.metric("Límite de Riesgo", f"{limite:.1f}", help="Configurado por evaluación")
    
    if not activo_seleccionado:
        return
    
    st.divider()
    
    # Obtener datos del activo
    activo_data = activos_eval[activos_eval["ID_Activo"] == activo_id].iloc[0]
    tipo_activo = activo_data.get("Tipo_Activo", "")
    
    # Mostrar info del activo
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Activo:** {activo_data.get('Nombre_Activo', '')}")
    with col2:
        st.info(f"**Tipo:** {tipo_activo}")
    with col3:
        # Obtener criticidad
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT Impacto_D, Impacto_I, Impacto_C FROM RESULTADOS_MAGERIT
                WHERE ID_Evaluacion = ? AND ID_Activo = ?
            ''', [eval_id, activo_id])
            row = cursor.fetchone()
            if row:
                criticidad = max(row[0] or 1, row[1] or 1, row[2] or 1)
                st.info(f"**Criticidad:** {criticidad} (MAX D/I/C)")
            else:
                st.warning("Sin valoración DIC")
    
    # Obtener amenazas con degradación
    df_amenazas = get_amenazas_con_degradacion(eval_id, activo_id)
    
    if df_amenazas.empty:
        st.warning("⚠️ No hay amenazas identificadas para este activo. Ejecuta primero la **Evaluación con IA**.")
        return
    
    # Resumen de estados
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total = len(df_amenazas)
        st.metric("Total Amenazas", total)
    with col2:
        pendientes = len(df_amenazas[df_amenazas["Estado"] == "Pendiente"])
        st.metric("Pendientes", pendientes, delta=f"-{pendientes}" if pendientes > 0 else None,
                  delta_color="inverse" if pendientes > 0 else "off")
    with col3:
        manuales = len(df_amenazas[df_amenazas["Fuente"] == "manual"])
        st.metric("Manuales", manuales)
    with col4:
        ia = len(df_amenazas[df_amenazas["Fuente"] == "IA"])
        st.metric("Sugeridos IA", ia)
    
    st.divider()
    
    # ================== TABLA DE AMENAZAS ==================
    st.subheader("📋 Degradación por Amenaza")
    
    # Mostrar tabla con formato
    for idx, row in df_amenazas.iterrows():
        with st.expander(
            f"{'🔴' if row['Estado'] == 'Pendiente' else '🟢'} {row['Código']} - {row['Amenaza']} | "
            f"Estado: **{row['Estado']}** | Riesgo: **{row['Riesgo'] if row['Riesgo'] else 'N/A'}**",
            expanded=row['Estado'] == 'Pendiente'
        ):
            render_fila_degradacion(
                eval_id=eval_id,
                activo_id=activo_id,
                tipo_activo=tipo_activo,
                amenaza_row=row,
                limite=limite
            )
    
    st.divider()
    
    # ================== ACCIONES MASIVAS ==================
    st.subheader("⚡ Acciones Masivas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🤖 Sugerir TODAS por IA", type="secondary", use_container_width=True):
            pendientes_df = df_amenazas[df_amenazas["Estado"] == "Pendiente"]
            if pendientes_df.empty:
                st.info("No hay amenazas pendientes")
            else:
                progress = st.progress(0)
                for i, (_, row) in enumerate(pendientes_df.iterrows()):
                    sugerencia = sugerir_degradacion_ia(
                        tipo_activo=tipo_activo,
                        codigo_amenaza=row["Código"],
                        tipo_amenaza=row["Tipo"]
                    )
                    sugerencia.id_evaluacion = eval_id
                    sugerencia.id_activo = activo_id
                    sugerencia.justificacion = f"Sugerencia automática basada en tipo '{row['Tipo']}'"
                    guardar_degradacion(sugerencia)
                    progress.progress((i + 1) / len(pendientes_df))
                
                st.success(f"✅ {len(pendientes_df)} degradaciones sugeridas por IA")
                st.rerun()
    
    with col2:
        if st.button("📊 Validar Trazabilidad", use_container_width=True):
            validacion = validar_trazabilidad_completa(eval_id, activo_id)
            if validacion["valido"]:
                st.success("✅ Trazabilidad completa verificada")
            if validacion["errores"]:
                for err in validacion["errores"]:
                    st.error(f"❌ {err}")
            if validacion["advertencias"]:
                for adv in validacion["advertencias"]:
                    st.warning(f"⚠️ {adv}")
    
    with col3:
        if st.button("🔄 Refrescar", use_container_width=True):
            st.rerun()


def render_fila_degradacion(
    eval_id: str,
    activo_id: str,
    tipo_activo: str,
    amenaza_row: pd.Series,
    limite: float
):
    """
    Renderiza los controles de edición para una fila de amenaza.
    """
    codigo = amenaza_row["Código"]
    criticidad = amenaza_row["Criticidad"]
    frecuencia = amenaza_row["Frecuencia"]
    
    # Info de la amenaza
    col1, col2 = st.columns([2, 1])
    with col1:
        st.caption(f"**Tipo:** {amenaza_row['Tipo']}")
    with col2:
        st.caption(f"**Frecuencia:** {frecuencia} | **Criticidad:** {criticidad}")
    
    # Obtener degradación actual o defaults
    deg_actual = obtener_degradacion(eval_id, activo_id, codigo)
    
    # Valores actuales o defaults
    deg_d_actual = deg_actual.degradacion_d if deg_actual else 0.5
    deg_i_actual = deg_actual.degradacion_i if deg_actual else 0.5
    deg_c_actual = deg_actual.degradacion_c if deg_actual else 0.5
    justificacion_actual = deg_actual.justificacion if deg_actual else ""
    
    st.markdown("**Degradación por Dimensión:**")
    
    # Controles de degradación con sliders
    col1, col2, col3 = st.columns(3)
    
    with col1:
        deg_d = st.select_slider(
            "🔴 Disponibilidad",
            options=list(NIVELES_DEGRADACION.keys()),
            value=get_nivel_from_float(deg_d_actual),
            key=f"deg_d_{codigo}"
        )
        deg_d_val = NIVELES_DEGRADACION[deg_d]
    
    with col2:
        deg_i = st.select_slider(
            "🟡 Integridad",
            options=list(NIVELES_DEGRADACION.keys()),
            value=get_nivel_from_float(deg_i_actual),
            key=f"deg_i_{codigo}"
        )
        deg_i_val = NIVELES_DEGRADACION[deg_i]
    
    with col3:
        deg_c = st.select_slider(
            "🔵 Confidencialidad",
            options=list(NIVELES_DEGRADACION.keys()),
            value=get_nivel_from_float(deg_c_actual),
            key=f"deg_c_{codigo}"
        )
        deg_c_val = NIVELES_DEGRADACION[deg_c]
    
    # Justificación
    justificacion = st.text_area(
        "📝 Justificación",
        value=justificacion_actual,
        placeholder="Explique por qué estos valores de degradación...",
        key=f"just_{codigo}",
        height=80
    )
    
    # Preview del cálculo
    max_deg = max(deg_d_val, deg_i_val, deg_c_val)
    impacto_preview = round(criticidad * max_deg, 2)
    riesgo_preview = round(frecuencia * impacto_preview, 2)
    sobre_limite = riesgo_preview > limite
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("MAX(Deg)", f"{max_deg:.2f}")
    with col2:
        st.metric("Impacto", f"{impacto_preview:.2f}")
    with col3:
        color = "inverse" if sobre_limite else "off"
        st.metric("Riesgo", f"{riesgo_preview:.2f}", 
                  delta="Sobre límite" if sobre_limite else None,
                  delta_color=color)
    with col4:
        nivel = get_nivel_riesgo_simple(riesgo_preview)
        st.metric("Nivel", nivel)
    
    # Botones de acción
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Guardar Manual", key=f"save_{codigo}", type="primary", use_container_width=True):
            # Validar rangos
            if not (0.0 <= deg_d_val <= 1.0 and 0.0 <= deg_i_val <= 1.0 and 0.0 <= deg_c_val <= 1.0):
                st.error("❌ Valores de degradación deben estar entre 0.0 y 1.0")
                return
            
            nueva_deg = DegradacionAmenaza(
                id_evaluacion=eval_id,
                id_activo=activo_id,
                codigo_amenaza=codigo,
                degradacion_d=deg_d_val,
                degradacion_i=deg_i_val,
                degradacion_c=deg_c_val,
                justificacion=justificacion,
                fuente="manual"
            )
            
            if guardar_degradacion(nueva_deg):
                # Actualizar RESULTADOS_MAGERIT con nuevo cálculo
                actualizar_resultado_con_degradacion(eval_id, activo_id)
                st.success("✅ Degradación guardada y riesgo recalculado")
                st.rerun()
            else:
                st.error("❌ Error guardando degradación")
    
    with col2:
        if st.button("🤖 Sugerir IA", key=f"ia_{codigo}", use_container_width=True):
            # Verificar datos mínimos
            if not tipo_activo or not amenaza_row["Tipo"]:
                st.error("❌ Información insuficiente para sugerir degradación")
                return
            
            with st.spinner("Generando sugerencia..."):
                sugerencia = sugerir_degradacion_ia(
                    tipo_activo=tipo_activo,
                    codigo_amenaza=codigo,
                    tipo_amenaza=amenaza_row["Tipo"]
                )
                
                if sugerencia:
                    st.info(f"""
                    **Sugerencia IA:**
                    - Deg_D: {sugerencia.degradacion_d:.2f}
                    - Deg_I: {sugerencia.degradacion_i:.2f}
                    - Deg_C: {sugerencia.degradacion_c:.2f}
                    
                    *{sugerencia.justificacion}*
                    """)
                    
                    if st.button("✅ Aceptar Sugerencia", key=f"accept_{codigo}"):
                        sugerencia.id_evaluacion = eval_id
                        sugerencia.id_activo = activo_id
                        sugerencia.justificacion += f" | Aceptada: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        guardar_degradacion(sugerencia)
                        actualizar_resultado_con_degradacion(eval_id, activo_id)
                        st.success("✅ Sugerencia IA aceptada")
                        st.rerun()
    
    with col3:
        if deg_actual:
            if st.button("🗑️ Eliminar", key=f"del_{codigo}", use_container_width=True):
                eliminar_degradacion(eval_id, activo_id, codigo)
                st.warning("Degradación eliminada - Estado: Pendiente")
                st.rerun()


def get_nivel_riesgo_simple(valor: float) -> str:
    """Determina el nivel de riesgo según el valor"""
    if valor >= 20:
        return "CRÍTICO"
    elif valor >= 12:
        return "ALTO"
    elif valor >= 6:
        return "MEDIO"
    elif valor >= 3:
        return "BAJO"
    else:
        return "MUY BAJO"


def actualizar_resultado_con_degradacion(eval_id: str, activo_id: str):
    """
    Recalcula y actualiza los campos de riesgo en RESULTADOS_MAGERIT
    después de modificar degradación.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener datos actuales
            cursor.execute('''
                SELECT Amenazas_JSON, Impacto_D, Impacto_I, Impacto_C
                FROM RESULTADOS_MAGERIT
                WHERE ID_Evaluacion = ? AND ID_Activo = ?
            ''', [eval_id, activo_id])
            
            row = cursor.fetchone()
            if not row:
                return
            
            amenazas = json.loads(row[0]) if row[0] else []
            criticidad = max(row[1] or 1, row[2] or 1, row[3] or 1)
            
            # Obtener degradaciones
            degradaciones = obtener_degradaciones_activo(eval_id, activo_id)
            deg_dict = {d.codigo_amenaza: d for d in degradaciones}
            
            # Recalcular riesgos
            riesgos = []
            amenazas_actualizadas = []
            
            for amenaza in amenazas:
                codigo = amenaza.get("codigo", "")
                frecuencia = amenaza.get("probabilidad", 3)
                
                deg = deg_dict.get(codigo)
                if deg:
                    max_deg = deg.degradacion_maxima
                    impacto = round(criticidad * max_deg, 2)
                    riesgo = round(frecuencia * impacto, 2)
                    
                    amenaza["impacto"] = impacto
                    amenaza["riesgo_inherente"] = riesgo
                    riesgos.append(riesgo)
                
                amenazas_actualizadas.append(amenaza)
            
            # Calcular agregaciones
            if riesgos:
                riesgo_promedio = round(sum(riesgos) / len(riesgos), 2)
                riesgo_maximo = round(max(riesgos), 2)
            else:
                riesgo_promedio = 0
                riesgo_maximo = 0
            
            limite = obtener_limite_evaluacion(eval_id)
            riesgo_objetivo = calcular_riesgo_objetivo(riesgo_promedio, 0.5)
            sobre_limite = 1 if supera_limite(riesgo_promedio, limite) else 0
            
            # Actualizar BD
            cursor.execute('''
                UPDATE RESULTADOS_MAGERIT SET
                    Amenazas_JSON = ?,
                    Riesgo_Inherente = ?,
                    Criticidad = ?,
                    Riesgo_Promedio = ?,
                    Riesgo_Maximo = ?,
                    Riesgo_Objetivo = ?,
                    Supera_Limite = ?
                WHERE ID_Evaluacion = ? AND ID_Activo = ?
            ''', [
                json.dumps(amenazas_actualizadas, ensure_ascii=False),
                riesgo_promedio,
                criticidad,
                riesgo_promedio,
                riesgo_maximo,
                riesgo_objetivo,
                sobre_limite,
                eval_id,
                activo_id
            ])
            
    except Exception as e:
        st.error(f"Error actualizando resultado: {e}")


def render_resumen_degradacion_evaluacion(eval_id: str):
    """
    Renderiza un resumen de degradación para toda la evaluación.
    Útil para mostrar en dashboards.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Contar totales
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT ID_Activo) as total_activos,
                    SUM(json_array_length(Amenazas_JSON)) as total_amenazas
                FROM RESULTADOS_MAGERIT
                WHERE ID_Evaluacion = ?
            ''', [eval_id])
            row = cursor.fetchone()
            total_activos = row[0] or 0
            
            # Contar degradaciones
            cursor.execute('''
                SELECT COUNT(*), 
                       SUM(CASE WHEN Fuente = 'manual' THEN 1 ELSE 0 END),
                       SUM(CASE WHEN Fuente = 'IA' THEN 1 ELSE 0 END)
                FROM DEGRADACION_AMENAZAS
                WHERE ID_Evaluacion = ?
            ''', [eval_id])
            row = cursor.fetchone()
            total_deg = row[0] or 0
            deg_manual = row[1] or 0
            deg_ia = row[2] or 0
            
            # Contar sobre límite
            cursor.execute('''
                SELECT SUM(Supera_Limite) FROM RESULTADOS_MAGERIT
                WHERE ID_Evaluacion = ?
            ''', [eval_id])
            sobre_limite = cursor.fetchone()[0] or 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Activos Evaluados", total_activos)
            with col2:
                st.metric("Degradaciones", total_deg, 
                          help=f"Manual: {deg_manual} | IA: {deg_ia}")
            with col3:
                st.metric("Sobre Límite", sobre_limite,
                          delta=f"+{sobre_limite}" if sobre_limite > 0 else None,
                          delta_color="inverse" if sobre_limite > 0 else "off")
            with col4:
                cobertura = (total_deg / max(1, total_activos * 5)) * 100  # Aprox 5 amenazas por activo
                st.metric("Cobertura Aprox", f"{min(100, cobertura):.0f}%")
                
    except Exception as e:
        st.error(f"Error en resumen: {e}")
