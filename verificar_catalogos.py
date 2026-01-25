"""
Verificar estructura de catálogos para implementar tabs
"""
import pandas as pd

EXCEL_PATH = "matriz_riesgos_v2.xlsx"

# CRITERIOS_MAGERIT
print("=" * 50)
print("CRITERIOS_MAGERIT (DIC)")
print("=" * 50)
crit = pd.read_excel(EXCEL_PATH, sheet_name="CRITERIOS_MAGERIT")
print(f"Columnas: {list(crit.columns)}")
print(f"Registros: {len(crit)}")
print("\nPrimeros 3 registros:")
print(crit.head(3).to_string())

# AMENAZAS_MAGERIT
print("\n" + "=" * 50)
print("AMENAZAS_MAGERIT")
print("=" * 50)
amen = pd.read_excel(EXCEL_PATH, sheet_name="AMENAZAS_MAGERIT")
print(f"Columnas: {list(amen.columns)}")
print(f"Registros: {len(amen)}")
print("\nPrimeros 3 registros:")
print(amen.head(3).to_string())

# CONTROLES_ISO27002
print("\n" + "=" * 50)
print("CONTROLES_ISO27002")
print("=" * 50)
ctrl = pd.read_excel(EXCEL_PATH, sheet_name="CONTROLES_ISO27002")
print(f"Columnas: {list(ctrl.columns)}")
print(f"Registros: {len(ctrl)}")
print("\nPrimeros 3 registros:")
print(ctrl.head(3).to_string())
