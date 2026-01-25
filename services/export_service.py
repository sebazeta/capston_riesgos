"""
SERVICIO DE EXPORTACIÓN PARA TITA
==================================
Genera documentos ejecutivos y datos para Power BI.
"""
import json
import os
from datetime import datetime
from typing import Dict, Optional, Tuple
import pandas as pd
from services.database_service import read_table
from services.ia_advanced_service import (
    obtener_amenazas_evaluacion,
    obtener_controles_evaluacion,
    ResumenEjecutivo
)


# ==================== EXPORTACIÓN DE RESUMEN EJECUTIVO ====================

def generar_documento_ejecutivo(
    resumen: ResumenEjecutivo,
    formato: str = "html"
) -> Tuple[bool, str, str]:
    """
    Genera un documento ejecutivo presentable.
    
    Args:
        resumen: Objeto ResumenEjecutivo
        formato: "html", "markdown" o "txt"
    
    Returns:
        (éxito, contenido, mensaje)
    """
    try:
        if formato == "html":
            contenido = _generar_html_ejecutivo(resumen)
        elif formato == "markdown":
            contenido = _generar_markdown_ejecutivo(resumen)
        else:
            contenido = _generar_texto_ejecutivo(resumen)
        
        return True, contenido, f"Documento generado en formato {formato}"
    except Exception as e:
        return False, "", f"Error generando documento: {str(e)}"


def _generar_html_ejecutivo(resumen: ResumenEjecutivo) -> str:
    """Genera documento HTML profesional para ejecutivos."""
    
    # Calcular estadísticas
    criticos = resumen.distribucion_riesgo.get("CRÍTICO", 0) + resumen.distribucion_riesgo.get("CRITICO", 0)
    altos = resumen.distribucion_riesgo.get("ALTO", 0)
    medios = resumen.distribucion_riesgo.get("MEDIO", 0)
    bajos = resumen.distribucion_riesgo.get("BAJO", 0)
    
    # Colores para niveles
    color_critico = "#dc3545"
    color_alto = "#fd7e14"
    color_medio = "#ffc107"
    color_bajo = "#28a745"
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resumen Ejecutivo - Evaluación de Riesgos MAGERIT</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: #f8f9fa; 
            color: #333; 
            line-height: 1.6;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; padding: 40px 20px; }}
        .header {{ 
            background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
            color: white; 
            padding: 40px; 
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .subtitle {{ opacity: 0.9; font-size: 16px; }}
        .header .date {{ 
            margin-top: 20px; 
            padding-top: 15px; 
            border-top: 1px solid rgba(255,255,255,0.3);
            font-size: 14px;
        }}
        .section {{ 
            background: white; 
            padding: 30px; 
            border-radius: 12px; 
            margin-bottom: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .section h2 {{ 
            color: #1a237e; 
            margin-bottom: 20px; 
            padding-bottom: 10px;
            border-bottom: 2px solid #e8eaf6;
        }}
        .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }}
        .metric {{ 
            text-align: center; 
            padding: 25px 15px;
            border-radius: 10px;
            background: #f8f9fa;
        }}
        .metric.critical {{ background: linear-gradient(135deg, {color_critico}22, {color_critico}11); border-left: 4px solid {color_critico}; }}
        .metric.high {{ background: linear-gradient(135deg, {color_alto}22, {color_alto}11); border-left: 4px solid {color_alto}; }}
        .metric.medium {{ background: linear-gradient(135deg, {color_medio}22, {color_medio}11); border-left: 4px solid {color_medio}; }}
        .metric.low {{ background: linear-gradient(135deg, {color_bajo}22, {color_bajo}11); border-left: 4px solid {color_bajo}; }}
        .metric .value {{ font-size: 36px; font-weight: bold; }}
        .metric.critical .value {{ color: {color_critico}; }}
        .metric.high .value {{ color: {color_alto}; }}
        .metric.medium .value {{ color: {color_medio}; }}
        .metric.low .value {{ color: {color_bajo}; }}
        .metric .label {{ font-size: 12px; color: #666; text-transform: uppercase; margin-top: 5px; }}
        .finding {{ 
            padding: 15px 20px; 
            margin: 10px 0; 
            background: #fff3e0; 
            border-left: 4px solid #ff9800;
            border-radius: 0 8px 8px 0;
        }}
        .recommendation {{ 
            padding: 15px 20px; 
            margin: 10px 0; 
            background: #e3f2fd; 
            border-left: 4px solid #2196f3;
            border-radius: 0 8px 8px 0;
        }}
        .asset-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        .asset-table th {{ 
            background: #1a237e; 
            color: white; 
            padding: 12px 15px; 
            text-align: left;
        }}
        .asset-table td {{ padding: 12px 15px; border-bottom: 1px solid #eee; }}
        .asset-table tr:hover {{ background: #f5f5f5; }}
        .risk-badge {{ 
            display: inline-block; 
            padding: 4px 12px; 
            border-radius: 20px; 
            font-size: 12px; 
            font-weight: bold; 
            color: white;
        }}
        .risk-critico {{ background: {color_critico}; }}
        .risk-alto {{ background: {color_alto}; }}
        .risk-medio {{ background: {color_medio}; color: #333; }}
        .risk-bajo {{ background: {color_bajo}; }}
        .summary-box {{ 
            background: linear-gradient(135deg, #e8eaf6, #c5cae9); 
            padding: 25px; 
            border-radius: 10px;
            margin-top: 20px;
        }}
        .summary-box h3 {{ color: #1a237e; margin-bottom: 15px; }}
        .investment {{ 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 20px; 
            margin-top: 20px;
        }}
        .investment-item {{ 
            background: white; 
            padding: 20px; 
            border-radius: 10px;
            text-align: center;
        }}
        .investment-item .icon {{ font-size: 30px; margin-bottom: 10px; }}
        .investment-item .value {{ font-size: 18px; font-weight: bold; color: #1a237e; }}
        .investment-item .label {{ font-size: 13px; color: #666; }}
        .footer {{ 
            text-align: center; 
            padding: 30px; 
            color: #666; 
            font-size: 12px;
        }}
        @media print {{
            body {{ background: white; }}
            .container {{ padding: 20px; }}
            .section {{ box-shadow: none; border: 1px solid #ddd; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Resumen Ejecutivo de Evaluación de Riesgos</h1>
            <div class="subtitle">Metodología MAGERIT v3 con ISO 27002:2022</div>
            <div class="date">
                <strong>Evaluación:</strong> {resumen.id_evaluacion} | 
                <strong>Fecha:</strong> {resumen.fecha_generacion}
            </div>
        </div>

        <div class="section">
            <h2>📈 Panorama General de Riesgos</h2>
            <div class="metrics">
                <div class="metric critical">
                    <div class="value">{criticos}</div>
                    <div class="label">Riesgos Críticos</div>
                </div>
                <div class="metric high">
                    <div class="value">{altos}</div>
                    <div class="label">Riesgos Altos</div>
                </div>
                <div class="metric medium">
                    <div class="value">{medios}</div>
                    <div class="label">Riesgos Medios</div>
                </div>
                <div class="metric low">
                    <div class="value">{bajos}</div>
                    <div class="label">Riesgos Bajos</div>
                </div>
            </div>
            <div class="investment">
                <div class="investment-item">
                    <div class="icon">📦</div>
                    <div class="value">{resumen.total_activos}</div>
                    <div class="label">Activos Evaluados</div>
                </div>
                <div class="investment-item">
                    <div class="icon">⚠️</div>
                    <div class="value">{resumen.total_amenazas}</div>
                    <div class="label">Amenazas Identificadas</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🔍 Hallazgos Principales</h2>
"""
    
    for i, hallazgo in enumerate(resumen.hallazgos_principales, 1):
        html += f'            <div class="finding"><strong>{i}.</strong> {hallazgo}</div>\n'
    
    html += """        </div>

        <div class="section">
            <h2>⚠️ Activos de Mayor Riesgo</h2>
            <table class="asset-table">
                <thead>
                    <tr>
                        <th>Activo</th>
                        <th>Tipo</th>
                        <th>Nivel de Riesgo</th>
                        <th>Valor</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for activo in resumen.activos_criticos[:5]:
        nivel = activo.get("nivel", "MEDIO")
        nivel_class = nivel.lower().replace("í", "i")
        html += f"""                    <tr>
                        <td><strong>{activo.get('nombre', 'N/A')}</strong></td>
                        <td>{activo.get('tipo', 'N/A')}</td>
                        <td><span class="risk-badge risk-{nivel_class}">{nivel}</span></td>
                        <td>{activo.get('riesgo', 0)}</td>
                    </tr>
"""
    
    html += """                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>💡 Recomendaciones Prioritarias</h2>
"""
    
    for i, rec in enumerate(resumen.recomendaciones_prioritarias, 1):
        html += f'            <div class="recommendation"><strong>{i}.</strong> {rec}</div>\n'
    
    html += f"""        </div>

        <div class="section">
            <h2>💰 Inversión y Retorno Esperado</h2>
            <div class="investment">
                <div class="investment-item">
                    <div class="icon">💵</div>
                    <div class="value">{resumen.inversion_estimada}</div>
                    <div class="label">Inversión Estimada</div>
                </div>
                <div class="investment-item">
                    <div class="icon">📉</div>
                    <div class="value">{resumen.reduccion_riesgo_esperada}</div>
                    <div class="label">Reducción de Riesgo Esperada</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>📋 Conclusión Ejecutiva</h2>
            <div class="summary-box">
                <p>{resumen.conclusion}</p>
            </div>
        </div>

        <div class="footer">
            <p>Generado por <strong>TITA - Tool for IT Assets Risk Assessment</strong></p>
            <p>Metodología MAGERIT v3 | Controles ISO 27002:2022</p>
            <p>Documento generado el {datetime.now().strftime("%d/%m/%Y a las %H:%M")}</p>
        </div>
    </div>
</body>
</html>"""
    
    return html


def _generar_markdown_ejecutivo(resumen: ResumenEjecutivo) -> str:
    """Genera documento Markdown."""
    
    criticos = resumen.distribucion_riesgo.get("CRÍTICO", 0) + resumen.distribucion_riesgo.get("CRITICO", 0)
    altos = resumen.distribucion_riesgo.get("ALTO", 0)
    medios = resumen.distribucion_riesgo.get("MEDIO", 0)
    bajos = resumen.distribucion_riesgo.get("BAJO", 0)
    
    md = f"""# 📊 Resumen Ejecutivo de Evaluación de Riesgos

**Evaluación:** {resumen.id_evaluacion}  
**Fecha:** {resumen.fecha_generacion}  
**Metodología:** MAGERIT v3 con ISO 27002:2022

---

## 📈 Panorama General

| Métrica | Valor |
|---------|-------|
| Activos Evaluados | {resumen.total_activos} |
| Amenazas Identificadas | {resumen.total_amenazas} |
| Riesgos Críticos | {criticos} |
| Riesgos Altos | {altos} |
| Riesgos Medios | {medios} |
| Riesgos Bajos | {bajos} |

---

## 🔍 Hallazgos Principales

"""
    
    for i, hallazgo in enumerate(resumen.hallazgos_principales, 1):
        md += f"{i}. {hallazgo}\n"
    
    md += """
---

## ⚠️ Activos de Mayor Riesgo

| Activo | Tipo | Nivel | Valor |
|--------|------|-------|-------|
"""
    
    for activo in resumen.activos_criticos[:5]:
        md += f"| {activo.get('nombre', 'N/A')} | {activo.get('tipo', 'N/A')} | {activo.get('nivel', 'N/A')} | {activo.get('riesgo', 0)} |\n"
    
    md += """
---

## 💡 Recomendaciones Prioritarias

"""
    
    for i, rec in enumerate(resumen.recomendaciones_prioritarias, 1):
        md += f"{i}. {rec}\n"
    
    md += f"""
---

## 💰 Inversión y Retorno

- **Inversión Estimada:** {resumen.inversion_estimada}
- **Reducción de Riesgo Esperada:** {resumen.reduccion_riesgo_esperada}

---

## 📋 Conclusión

{resumen.conclusion}

---

*Generado por TITA - Tool for IT Assets Risk Assessment*  
*{datetime.now().strftime("%d/%m/%Y %H:%M")}*
"""
    
    return md


def _generar_texto_ejecutivo(resumen: ResumenEjecutivo) -> str:
    """Genera documento en texto plano."""
    
    txt = f"""
================================================================================
                    RESUMEN EJECUTIVO DE EVALUACIÓN DE RIESGOS
================================================================================

Evaluación: {resumen.id_evaluacion}
Fecha: {resumen.fecha_generacion}
Metodología: MAGERIT v3 con ISO 27002:2022

--------------------------------------------------------------------------------
PANORAMA GENERAL
--------------------------------------------------------------------------------
• Activos Evaluados: {resumen.total_activos}
• Amenazas Identificadas: {resumen.total_amenazas}
• Distribución de Riesgos: {resumen.distribucion_riesgo}

--------------------------------------------------------------------------------
HALLAZGOS PRINCIPALES
--------------------------------------------------------------------------------
"""
    
    for i, hallazgo in enumerate(resumen.hallazgos_principales, 1):
        txt += f"{i}. {hallazgo}\n"
    
    txt += """
--------------------------------------------------------------------------------
ACTIVOS DE MAYOR RIESGO
--------------------------------------------------------------------------------
"""
    
    for activo in resumen.activos_criticos[:5]:
        txt += f"• {activo.get('nombre', 'N/A')} ({activo.get('tipo', 'N/A')}) - Riesgo: {activo.get('nivel', 'N/A')}\n"
    
    txt += """
--------------------------------------------------------------------------------
RECOMENDACIONES PRIORITARIAS
--------------------------------------------------------------------------------
"""
    
    for i, rec in enumerate(resumen.recomendaciones_prioritarias, 1):
        txt += f"{i}. {rec}\n"
    
    txt += f"""
--------------------------------------------------------------------------------
INVERSIÓN Y RETORNO
--------------------------------------------------------------------------------
• Inversión Estimada: {resumen.inversion_estimada}
• Reducción de Riesgo Esperada: {resumen.reduccion_riesgo_esperada}

--------------------------------------------------------------------------------
CONCLUSIÓN
--------------------------------------------------------------------------------
{resumen.conclusion}

================================================================================
Generado por TITA - Tool for IT Assets Risk Assessment
{datetime.now().strftime("%d/%m/%Y %H:%M")}
================================================================================
"""
    
    return txt


# ==================== EXPORTACIÓN PARA POWER BI ====================

def generar_datos_powerbi(eval_id: str) -> Tuple[bool, Dict[str, pd.DataFrame], str]:
    """
    Genera datasets optimizados para Power BI.
    
    Returns:
        (éxito, {nombre_tabla: dataframe}, mensaje)
    """
    try:
        datasets = {}
        
        # 1. Tabla de Activos
        activos = read_table("INVENTARIO_ACTIVOS")
        if not activos.empty and "ID_Evaluacion" in activos.columns:
            activos_eval = activos[activos["ID_Evaluacion"] == eval_id].copy()
            datasets["Activos"] = activos_eval
        
        # 2. Tabla de Resultados MAGERIT
        resultados = read_table("RESULTADOS_MAGERIT")
        if not resultados.empty:
            col_eval = "ID_Evaluacion" if "ID_Evaluacion" in resultados.columns else "id_evaluacion"
            if col_eval in resultados.columns:
                resultados_eval = resultados[resultados[col_eval] == eval_id].copy()
                # Limpiar columnas JSON para Power BI
                if "Amenazas_JSON" in resultados_eval.columns:
                    resultados_eval = resultados_eval.drop(columns=["Amenazas_JSON"])
                if "Controles_JSON" in resultados_eval.columns:
                    resultados_eval = resultados_eval.drop(columns=["Controles_JSON"])
                datasets["Resultados_MAGERIT"] = resultados_eval
        
        # 3. Tabla de Amenazas (desagregada)
        amenazas = obtener_amenazas_evaluacion(eval_id)
        if not amenazas.empty:
            # Limpiar columnas complejas
            if "controles_recomendados" in amenazas.columns:
                amenazas = amenazas.drop(columns=["controles_recomendados"])
            datasets["Amenazas"] = amenazas
        
        # 4. Tabla de Controles Recomendados
        controles = obtener_controles_evaluacion(eval_id)
        if not controles.empty:
            datasets["Controles_Recomendados"] = controles
        
        # 5. Tabla de Distribución de Riesgos (para gráficos)
        if not amenazas.empty and "nivel_riesgo" in amenazas.columns:
            distribucion = amenazas["nivel_riesgo"].value_counts().reset_index()
            distribucion.columns = ["Nivel_Riesgo", "Cantidad"]
            # Agregar orden para ordenar correctamente en Power BI
            orden_map = {"CRÍTICO": 1, "CRITICO": 1, "ALTO": 2, "MEDIO": 3, "BAJO": 4}
            distribucion["Orden"] = distribucion["Nivel_Riesgo"].map(orden_map).fillna(5)
            datasets["Distribucion_Riesgos"] = distribucion
        
        # 6. Tabla de Dimensiones de Impacto
        if not amenazas.empty and "dimension" in amenazas.columns:
            dim_impacto = amenazas.groupby("dimension").agg({
                "riesgo_inherente": "mean",
                "id_activo": "count"
            }).reset_index()
            dim_impacto.columns = ["Dimension", "Riesgo_Promedio", "Cantidad_Amenazas"]
            dim_impacto["Dimension_Nombre"] = dim_impacto["Dimension"].map({
                "D": "Disponibilidad",
                "I": "Integridad",
                "C": "Confidencialidad"
            })
            datasets["Impacto_Dimensiones"] = dim_impacto
        
        # 7. Tabla de Tipos de Amenaza
        if not amenazas.empty and "tipo_amenaza" in amenazas.columns:
            tipos = amenazas.groupby("tipo_amenaza").agg({
                "riesgo_inherente": ["mean", "max"],
                "id_activo": "count"
            }).reset_index()
            tipos.columns = ["Tipo_Amenaza", "Riesgo_Promedio", "Riesgo_Maximo", "Cantidad"]
            datasets["Tipos_Amenaza"] = tipos
        
        # 8. Tabla de Metadata
        metadata = pd.DataFrame([{
            "ID_Evaluacion": eval_id,
            "Fecha_Exportacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Total_Activos": len(datasets.get("Activos", pd.DataFrame())),
            "Total_Amenazas": len(datasets.get("Amenazas", pd.DataFrame())),
            "Total_Controles": len(datasets.get("Controles_Recomendados", pd.DataFrame())),
            "Generado_Por": "TITA - Tool for IT Assets"
        }])
        datasets["Metadata"] = metadata
        
        return True, datasets, f"Generados {len(datasets)} datasets para Power BI"
    
    except Exception as e:
        return False, {}, f"Error generando datos: {str(e)}"


def exportar_powerbi_excel(eval_id: str, ruta_archivo: str) -> Tuple[bool, str]:
    """
    Exporta datos a un archivo Excel optimizado para Power BI.
    
    Args:
        eval_id: ID de la evaluación
        ruta_archivo: Ruta donde guardar el archivo
    
    Returns:
        (éxito, mensaje)
    """
    try:
        exito, datasets, mensaje = generar_datos_powerbi(eval_id)
        if not exito:
            return False, mensaje
        
        # Crear archivo Excel con múltiples hojas
        with pd.ExcelWriter(ruta_archivo, engine='openpyxl') as writer:
            for nombre, df in datasets.items():
                if not df.empty:
                    df.to_excel(writer, sheet_name=nombre[:31], index=False)
        
        return True, f"Archivo exportado: {ruta_archivo}"
    
    except Exception as e:
        return False, f"Error exportando: {str(e)}"


def exportar_powerbi_csv(eval_id: str, directorio: str) -> Tuple[bool, str]:
    """
    Exporta datos a múltiples archivos CSV para Power BI.
    
    Args:
        eval_id: ID de la evaluación
        directorio: Directorio donde guardar los archivos
    
    Returns:
        (éxito, mensaje)
    """
    try:
        exito, datasets, mensaje = generar_datos_powerbi(eval_id)
        if not exito:
            return False, mensaje
        
        # Crear directorio si no existe
        os.makedirs(directorio, exist_ok=True)
        
        archivos = []
        for nombre, df in datasets.items():
            if not df.empty:
                ruta = os.path.join(directorio, f"{nombre}.csv")
                df.to_csv(ruta, index=False, encoding='utf-8-sig')
                archivos.append(ruta)
        
        return True, f"Exportados {len(archivos)} archivos CSV a {directorio}"
    
    except Exception as e:
        return False, f"Error exportando: {str(e)}"
