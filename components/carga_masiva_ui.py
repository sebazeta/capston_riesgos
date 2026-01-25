"""
Componente UI para Carga Masiva de Activos - Proyecto TITA
Interfaz Streamlit para importar activos desde JSON o Excel
"""
import streamlit as st
import pandas as pd
import io
from typing import Optional

from services.carga_masiva_service import (
    procesar_json,
    procesar_excel,
    generar_plantilla_json,
    generar_plantilla_excel,
    get_campos_info,
    ResultadoCarga
)


def render_carga_masiva(eval_id: str, eval_nombre: str):
    """
    Renderiza la interfaz completa de carga masiva de activos
    
    Args:
        eval_id: ID de la evaluación destino
        eval_nombre: Nombre de la evaluación para mostrar
    """
    st.markdown("## 📤 Carga Masiva de Activos")
    st.info(f"📋 Evaluación destino: **{eval_nombre}** (`{eval_id}`)")
    
    # Tabs para diferentes formatos
    tab_json, tab_excel, tab_ayuda = st.tabs([
        "📄 JSON (Recomendado)", 
        "📊 Excel",
        "❓ Ayuda y Plantillas"
    ])
    
    with tab_json:
        _render_carga_json(eval_id)
    
    with tab_excel:
        _render_carga_excel(eval_id)
    
    with tab_ayuda:
        _render_ayuda_plantillas()


def _render_carga_json(eval_id: str):
    """Renderiza la sección de carga JSON"""
    st.markdown("### 📄 Importar desde JSON")
    
    st.markdown("""
    **Formato JSON** es el recomendado porque:
    - ✅ Validación estricta de tipos
    - ✅ Sin riesgo de macros o fórmulas
    - ✅ Auditable (se genera hash del archivo)
    - ✅ Preparado para integración API futura
    """)
    
    # Opción 1: Subir archivo
    st.markdown("#### Opción 1: Subir archivo JSON")
    archivo_json = st.file_uploader(
        "Selecciona un archivo .json",
        type=["json"],
        key="json_uploader",
        help="Archivo JSON con la estructura de activos"
    )
    
    if archivo_json:
        contenido = archivo_json.read().decode('utf-8')
        
        # Mostrar preview
        with st.expander("👁️ Vista previa del archivo", expanded=False):
            st.code(contenido[:2000] + ("..." if len(contenido) > 2000 else ""), language="json")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🚀 Procesar JSON", type="primary", key="btn_procesar_json"):
                with st.spinner("Procesando archivo JSON..."):
                    resultado = procesar_json(contenido, eval_id)
                    _mostrar_resultado(resultado)
    
    st.divider()
    
    # Opción 2: Pegar JSON
    st.markdown("#### Opción 2: Pegar contenido JSON")
    
    json_texto = st.text_area(
        "Pega el contenido JSON aquí:",
        height=200,
        key="json_textarea",
        placeholder='{\n  "activos": [\n    {\n      "nombre_activo": "Servidor BD",\n      ...\n    }\n  ]\n}'
    )
    
    if json_texto.strip():
        if st.button("🚀 Procesar JSON Pegado", type="primary", key="btn_procesar_json_texto"):
            with st.spinner("Procesando JSON..."):
                resultado = procesar_json(json_texto, eval_id)
                _mostrar_resultado(resultado)


def _render_carga_excel(eval_id: str):
    """Renderiza la sección de carga Excel"""
    st.markdown("### 📊 Importar desde Excel")
    
    st.warning("""
    **⚠️ Excel es formato de compatibilidad.**  
    Recomendamos JSON para mayor seguridad y validación.
    
    **Precauciones aplicadas:**
    - Solo se leen valores (no fórmulas)
    - Se sanitizan todos los campos
    - Se valida estructura antes de insertar
    """)
    
    archivo_excel = st.file_uploader(
        "Selecciona un archivo Excel (.xlsx)",
        type=["xlsx"],
        key="excel_uploader",
        help="Archivo Excel con columnas: nombre_activo, tipo_activo, ubicacion, propietario, tipo_servicio"
    )
    
    if archivo_excel:
        try:
            # Preview del archivo
            df_preview = pd.read_excel(archivo_excel, engine='openpyxl', nrows=5)
            
            with st.expander("👁️ Vista previa (primeras 5 filas)", expanded=True):
                st.dataframe(df_preview, use_container_width=True)
            
            # Resetear posición del archivo
            archivo_excel.seek(0)
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("🚀 Procesar Excel", type="primary", key="btn_procesar_excel"):
                    with st.spinner("Procesando archivo Excel..."):
                        archivo_bytes = archivo_excel.read()
                        resultado = procesar_excel(archivo_bytes, eval_id)
                        _mostrar_resultado(resultado)
        
        except Exception as e:
            st.error(f"❌ Error al leer el archivo: {str(e)}")


def _render_ayuda_plantillas():
    """Renderiza sección de ayuda y descarga de plantillas"""
    st.markdown("### ❓ Ayuda y Plantillas")
    
    # Información de campos
    campos_info = get_campos_info()
    
    st.markdown("#### 📋 Campos Requeridos")
    df_requeridos = pd.DataFrame(campos_info["requeridos"])
    st.dataframe(df_requeridos, use_container_width=True, hide_index=True)
    
    st.markdown("#### 📋 Campos Opcionales")
    df_opcionales = pd.DataFrame(campos_info["opcionales"])
    st.dataframe(df_opcionales, use_container_width=True, hide_index=True)
    
    st.markdown("#### 🏷️ Tipos de Activo Válidos")
    for tipo in campos_info["tipos_validos"]:
        st.markdown(f"- `{tipo}`")
    
    st.divider()
    
    # Descargar plantillas
    st.markdown("### 📥 Descargar Plantillas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Plantilla JSON")
        plantilla_json = generar_plantilla_json()
        st.download_button(
            label="⬇️ Descargar plantilla.json",
            data=plantilla_json,
            file_name="plantilla_activos.json",
            mime="application/json",
            key="download_json"
        )
        
        with st.expander("Ver contenido JSON"):
            st.code(plantilla_json, language="json")
    
    with col2:
        st.markdown("#### Plantilla Excel")
        df_plantilla = generar_plantilla_excel()
        
        # Convertir a bytes para descarga
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_plantilla.to_excel(writer, index=False, sheet_name='Activos')
        
        st.download_button(
            label="⬇️ Descargar plantilla.xlsx",
            data=buffer.getvalue(),
            file_name="plantilla_activos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel"
        )
        
        with st.expander("Ver contenido Excel"):
            st.dataframe(df_plantilla, use_container_width=True, hide_index=True)


def _mostrar_resultado(resultado: ResultadoCarga):
    """Muestra el resultado de una operación de carga"""
    
    # Mensaje principal
    if resultado.exito:
        st.success(resultado.mensaje)
    else:
        st.error(resultado.mensaje if resultado.mensaje else "❌ No se insertaron activos")
    
    # Métricas resumen
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📊 Procesados", resultado.total_procesados)
    col2.metric("✅ Insertados", resultado.total_insertados)
    col3.metric("⚠️ Duplicados", resultado.total_duplicados)
    col4.metric("❌ Errores", resultado.total_errores)
    
    # Detalles de auditoría
    with st.expander("🔍 Detalles de Auditoría", expanded=False):
        st.markdown(f"""
        - **Formato origen:** {resultado.formato_origen}
        - **Timestamp:** {resultado.timestamp}
        - **Hash archivo:** `{resultado.hash_archivo}`
        """)
    
    # Activos insertados
    if resultado.insertados:
        with st.expander(f"✅ Activos Insertados ({len(resultado.insertados)})", expanded=True):
            for activo in resultado.insertados:
                st.markdown(f"- {activo}")
    
    # Duplicados
    if resultado.duplicados:
        with st.expander(f"⚠️ Duplicados Omitidos ({len(resultado.duplicados)})", expanded=False):
            for dup in resultado.duplicados:
                st.warning(dup)
    
    # Errores de validación
    if resultado.errores:
        with st.expander(f"❌ Errores de Validación ({len(resultado.errores)})", expanded=True):
            for error in resultado.errores:
                st.error(f"**Fila {error.fila}** - Campo `{error.campo}`: {error.mensaje}")
                if error.valor_recibido:
                    st.caption(f"Valor recibido: `{error.valor_recibido}`")


def render_carga_masiva_modal(eval_id: str, eval_nombre: str) -> bool:
    """
    Versión simplificada para usar en modal/dialog
    
    Returns:
        True si se insertaron activos (para refrescar la vista)
    """
    st.markdown(f"### 📤 Carga Masiva → {eval_nombre}")
    
    formato = st.radio(
        "Selecciona formato:",
        ["JSON (Recomendado)", "Excel"],
        horizontal=True,
        key="formato_carga_modal"
    )
    
    if "JSON" in formato:
        archivo = st.file_uploader("Archivo JSON", type=["json"], key="modal_json")
        if archivo and st.button("Procesar", type="primary", key="modal_btn_json"):
            contenido = archivo.read().decode('utf-8')
            resultado = procesar_json(contenido, eval_id)
            _mostrar_resultado(resultado)
            return resultado.exito
    else:
        archivo = st.file_uploader("Archivo Excel", type=["xlsx"], key="modal_excel")
        if archivo and st.button("Procesar", type="primary", key="modal_btn_excel"):
            resultado = procesar_excel(archivo.read(), eval_id)
            _mostrar_resultado(resultado)
            return resultado.exito
    
    return False
