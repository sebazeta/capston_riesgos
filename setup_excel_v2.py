import os
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

EXCEL_PATH = "matriz_riesgos_v2.xlsx"

SHEETS = {
    "PORTADA": ["Campo", "Valor"],
    "EVALUACIONES": ["ID_Evaluacion", "Nombre", "Fecha", "Estado", "Descripcion"],

    "CRITERIOS_MAGERIT": ["Dimension", "Nivel(1-5)", "Descripcion", "Ejemplo"],
    "CATALOGO_AMENAZAS_MAGERIT": ["Cod_MAGERIT", "Categoria", "Amenaza", "Descripcion", "Dimension(D/I/C)", "Severidad_Base(1-5)"],
    "CATALOGO_ISO27002_2022": ["Control", "Nombre", "Dominio", "Descripcion"],

    "INVENTARIO_ACTIVOS": ["ID_Activo", "Nombre_Activo", "Tipo_Activo", "Subtipo", "Propietario", "Ubicacion",
                       "Criticidad_Negocio(1-5)", "Internet_Expuesto(0/1)", "Datos_Sensibles(0/1)",
                       "RTO_objetivo_horas", "RPO_objetivo_horas", "BIA_impacto(1-5)"],

    # NUEVO: Banco de preguntas base (estándar)
    "BANCO_PREGUNTAS": ["ID_Pregunta", "Tipo_Activo", "Dimension(D/I/C)", "Pregunta", "Tipo_Respuesta(0/1|1-5)", "Peso(1-5)"],

    # NUEVO: Cuestionario generado por IA para cada activo
    "CUESTIONARIO_GENERADO": ["ID_Evaluacion", "ID_Activo", "Fecha", "ID_Pregunta", "Pregunta", "Tipo_Respuesta", "Peso", "Fuente(IA/Base)"],

    # NUEVO: Respuestas del usuario
    "RESPUESTAS": ["ID_Evaluacion", "ID_Activo", "Fecha", "ID_Pregunta", "Respuesta"],

    "VALORACION_DIC": ["ID_Evaluacion", "ID_Activo", "Fecha", "Disponibilidad(1-5)", "Integridad(1-5)", "Confidencialidad(1-5)",
                       "Just_D", "Just_I", "Just_C"],

    "AMENAZAS_VULNERAB": ["ID_Evaluacion", "ID_Riesgo", "ID_Activo", "Fecha", "Cod_MAGERIT", "Amenaza",
                          "Vulnerabilidad", "Dimension(D/I/C)", "Severidad(1-5)"],

    "ANALISIS_RIESGO": ["ID_Evaluacion", "ID_Riesgo", "ID_Activo", "Fecha", "Probabilidad(1-5)", "Impacto(1-5)", "Riesgo_Inherente(1-25)"],

    "SALVAGUARDAS": ["ID_Evaluacion", "ID_Riesgo", "ID_Activo", "Fecha", "Control_ISO27002", "Nombre_Control", "Descripcion", "Efectividad(0-100)"],

    "RIESGO_RESIDUAL": ["ID_Evaluacion", "ID_Riesgo", "ID_Activo", "Fecha", "Riesgo_Inherente", "Efectividad", "Riesgo_Residual"],

    "HISTORICO": ["ID_Evaluacion", "Fecha", "Total_Activos", "Riesgo_Promedio_Residual", "Riesgos_Altos", "Riesgos_Medios", "Riesgos_Bajos"],
    "DASHBOARD": ["KPI", "Valor"],
    "COMPARATIVO": ["Evaluacion_A", "Evaluacion_B", "Metrica", "Valor_A", "Valor_B", "Diferencia"],
}

def autosize(ws):
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val = "" if cell.value is None else str(cell.value)
            max_len = max(max_len, len(val))
        ws.column_dimensions[col_letter].width = min(max_len + 2, 50)

def main():
    if os.path.exists(EXCEL_PATH):
        print(f"Ya existe {EXCEL_PATH}. No lo sobrescribo.")
        return

    wb = Workbook()
    wb.remove(wb.active)

    for name, headers in SHEETS.items():
        ws = wb.create_sheet(name)
        ws.append(headers)
        autosize(ws)

    wb.save(EXCEL_PATH)
    print(f"Creado {EXCEL_PATH} con pestañas completas.")

if __name__ == "__main__":
    main()

