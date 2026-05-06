"""
COMPONENTE UI DE VALIDACIÓN DE IA - PROYECTO TITA
==================================================
Interfaz Streamlit para:
- Validar que Ollama funciona localmente
- Ejecutar pruebas de canary token
- Preparar IA con Knowledge Base
- Mostrar evidencias de ejecución
- Bloquear si IA no está lista
"""
import streamlit as st
import datetime as dt
from typing import Dict, Optional, Tuple

# Imports de servicios
from services.ia_validation_service import (
    ejecutar_validacion_completa,
    obtener_estado_ia,
    obtener_evidencias_recientes,
    obtener_logs_validacion,
    verificar_ollama_local,
    IAValidationResult
)
from services.knowledge_base_service import (
    obtener_resumen_catalogos,
    construir_knowledge_context,
    exportar_knowledge_base_json
)


def render_estado_ia_badge() -> bool:
    """
    Renderiza un badge con el estado de la IA.
    Retorna True si IA está lista, False si no.
    """
    ia_ready, last_validation, canary_nonce = obtener_estado_ia()
    
    if ia_ready:
        st.success("✅ **IA VALIDADA Y LISTA** - Evaluaciones habilitadas")
        with st.expander("Detalles de validación"):
            st.write(f"🕐 Última validación: {last_validation}")
            st.write(f"🔐 Canary nonce: `{canary_nonce[:20]}...`" if canary_nonce else "")
        return True
    else:
        st.error("❌ **IA NO VALIDADA** - Ejecute validación primero")
        st.warning("⚠️ El botón 'Evaluar Activo' está bloqueado hasta validar la IA.")
        return False


def render_tab_validacion_ia():
    """Renderiza la pestaña completa de validación de IA"""
    from utils.ui_styles import styled_header
    styled_header("🛡️", "Validación de IA Local", "Verifica que Ollama funcione 100% local y sin Internet")
    
    st.markdown("""
    Este módulo valida que la IA funciona **100% local** con Ollama y sin conexión a Internet.
    
    ### Validaciones realizadas:
    1. ✅ Verificar que Ollama está corriendo en localhost
    2. ✅ Prueba de Canary Token (anti-falsificación)
    3. ✅ Prueba de variabilidad controlada
    4. ✅ Prueba de dependencia de input
    5. ✅ Verificación de catálogos cargados
    """)
    
    # Dividir en columnas
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔍 Estado Actual")
        ia_ready, last_validation, canary_nonce = obtener_estado_ia()
        
        if ia_ready:
            st.success("✅ IA Validada y Lista")
            st.info(f"Última validación: {last_validation}")
        else:
            st.warning("⚠️ IA No Validada")
            st.caption("Ejecute la validación para habilitar evaluaciones")
        
        # Verificar Ollama
        st.subheader("🖥️ Ollama Local")
        is_local, endpoint, modelos, error = verificar_ollama_local()
        
        if is_local:
            st.success(f"✅ Conectado: {endpoint}")
            st.caption(f"Modelos disponibles: {', '.join(modelos[:5])}")
        else:
            st.error(f"❌ No conectado: {error}")
            st.info("Inicie Ollama con: `ollama serve`")
    
    with col2:
        st.subheader("📚 Knowledge Base")
        resumen = obtener_resumen_catalogos()
        
        if resumen["total_amenazas"] >= 50 and resumen["total_controles"] >= 90:
            st.success("✅ Catálogos cargados correctamente")
        else:
            st.warning("⚠️ Catálogos incompletos")
        
        st.metric("Amenazas MAGERIT", resumen["total_amenazas"])
        st.metric("Controles ISO 27002", resumen["total_controles"])
        st.metric("Ejemplos Few-Shot", resumen["few_shot_examples"])
    
    st.divider()
    
    # Botones de acción
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("🔄 Ejecutar Validación Completa", type="primary", use_container_width=True):
            with st.spinner("Ejecutando validación..."):
                resultado = ejecutar_validacion_completa()
                st.session_state["ultima_validacion"] = resultado
                st.rerun()
    
    with col_btn2:
        if st.button("📥 Exportar Knowledge Base", use_container_width=True):
            filepath = "knowledge_base/knowledge_base_export.json"
            if exportar_knowledge_base_json(filepath):
                st.success(f"✅ Exportado a: {filepath}")
            else:
                st.error("❌ Error al exportar")
    
    with col_btn3:
        if st.button("🗑️ Limpiar Estado IA", use_container_width=True):
            from services.database_service import get_connection
            try:
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM IA_STATUS")
                st.success("Estado limpiado. Vuelva a validar.")
                st.rerun()
            except:
                st.error("Error al limpiar")
    
    # Mostrar resultado de última validación
    if "ultima_validacion" in st.session_state:
        resultado = st.session_state["ultima_validacion"]
        render_resultado_validacion(resultado)
    
    st.divider()
    
    # Sección de evidencias
    render_seccion_evidencias()


def render_resultado_validacion(resultado: IAValidationResult):
    """Renderiza los resultados de una validación"""
    st.subheader("📋 Resultado de Validación")
    
    # Estado general
    if resultado.ia_ready:
        st.success("✅ **IA LISTA PARA USAR**")
    else:
        st.error("❌ **IA NO LISTA - REVISAR ERRORES**")
    
    # Detalles en columnas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🖥️ Conexión Local**")
        if resultado.is_local:
            st.success(f"✅ {resultado.endpoint}")
            st.caption(f"Modelo: {resultado.model}")
        else:
            st.error("❌ No conectado")
    
    with col2:
        st.markdown("**🔐 Canary Token**")
        if resultado.canary_passed:
            st.success("✅ Pasó")
            st.caption(f"Nonce: {resultado.canary_nonce[:15]}...")
        else:
            st.error("❌ Falló")
    
    with col3:
        st.markdown("**📊 Variabilidad**")
        if resultado.variability_passed:
            st.success("✅ Pasó")
        else:
            st.warning("⚠️ Revisar")
    
    # Métricas
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Latencia", f"{resultado.latency_ms:.0f} ms")
    col_m2.metric("Respuesta", f"{resultado.response_size} chars")
    col_m3.metric("Catálogos", "✅" if resultado.catalogs_loaded else "❌")
    
    # Errores y warnings
    if resultado.errors:
        st.error("**Errores encontrados:**")
        for error in resultado.errors:
            st.write(f"- ❌ {error}")
    
    if resultado.warnings:
        st.warning("**Advertencias:**")
        for warning in resultado.warnings:
            st.write(f"- ⚠️ {warning}")
    
    # Hash de respuesta
    if resultado.response_hash:
        st.caption(f"🔏 Hash de validación: `{resultado.response_hash[:32]}...`")


def render_seccion_evidencias():
    """Renderiza la sección de evidencias de ejecución"""
    st.subheader("📜 Evidencias de Ejecución IA")
    
    tab1, tab2 = st.tabs(["Ejecuciones Recientes", "Logs de Validación"])
    
    with tab1:
        evidencias = obtener_evidencias_recientes(10)
        
        if evidencias:
            for i, ev in enumerate(evidencias):
                with st.expander(f"Ejecución {ev.get('timestamp', 'N/A')[:19]} - Activo: {ev.get('id_activo', 'N/A')[:20]}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Modelo:** {ev.get('modelo')}")
                        st.write(f"**Latencia:** {ev.get('latency_ms', 0):.0f} ms")
                        st.write(f"**JSON válido:** {'✅' if ev.get('json_valid') else '❌'}")
                        st.write(f"**Canary OK:** {'✅' if ev.get('canary_verified') else '❌'}")
                    
                    with col2:
                        st.write(f"**Endpoint:** {ev.get('endpoint')}")
                        st.write(f"**Tamaño respuesta:** {ev.get('raw_response_length', 0)} chars")
                        st.caption(f"Prompt hash: `{ev.get('prompt_hash', '')[:24]}...`")
                        st.caption(f"Response hash: `{ev.get('response_hash', '')[:24]}...`")
        else:
            st.info("No hay ejecuciones registradas aún.")
    
    with tab2:
        logs = obtener_logs_validacion(20)
        
        if logs:
            for log in logs:
                emoji = "✅" if log.get("result") else "❌"
                with st.expander(f"{emoji} {log.get('validation_type')} - {log.get('timestamp', '')[:19]}"):
                    st.json(log.get("details", "{}"))
                    st.caption(f"Evidence hash: `{log.get('evidence_hash', '')[:32]}...`")
        else:
            st.info("No hay logs de validación aún.")


def render_boton_evaluar_bloqueado():
    """Renderiza un botón de evaluación bloqueado con mensaje"""
    st.button(
        "🔒 Evaluar Activo (Bloqueado)",
        disabled=True,
        use_container_width=True,
        help="Primero valide la IA en la pestaña '🛡️ Validación IA'"
    )
    st.caption("⚠️ Debe validar la IA antes de evaluar activos")


def verificar_ia_lista_para_evaluar() -> Tuple[bool, str]:
    """
    Verifica si la IA está lista para evaluar.
    
    Returns:
        (lista: bool, mensaje: str)
    """
    ia_ready, last_validation, _ = obtener_estado_ia()
    
    if not ia_ready:
        return False, "IA no validada. Vaya a la pestaña 'Validación IA' primero."
    
    # Verificar que la validación no sea muy antigua (máximo 24 horas)
    if last_validation:
        try:
            last_dt = dt.datetime.fromisoformat(last_validation)
            diff = dt.datetime.now() - last_dt
            if diff.total_seconds() > 86400:  # 24 horas
                return False, f"Validación expirada (hace {diff.days} días). Vuelva a validar."
        except:
            pass
    
    return True, "IA lista para evaluación"


def render_indicador_ia_en_header():
    """Renderiza un indicador pequeño del estado de IA para el header"""
    ia_ready, _, _ = obtener_estado_ia()
    
    if ia_ready:
        st.markdown(
            '<span style="background-color: #28a745; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 12px;">🤖 IA OK</span>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<span style="background-color: #dc3545; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 12px;">🤖 IA ⚠️</span>',
            unsafe_allow_html=True
        )
