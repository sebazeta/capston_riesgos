import sqlite3
import pandas as pd

conn = sqlite3.connect('tita_database.db')

print("="*60)
print("ACTIVO FALTANTE")
print("="*60)

faltante = pd.read_sql("""
    SELECT a.ID_Activo, a.Nombre_Activo, a.Tipo_Activo
    FROM INVENTARIO_ACTIVOS a
    WHERE a.ID_Evaluacion = 'EVA-001'
    AND a.ID_Activo NOT IN (
        SELECT DISTINCT ID_Activo 
        FROM IDENTIFICACION_VALORACION 
        WHERE ID_Evaluacion = 'EVA-001'
    )
    ORDER BY a.ID_Activo
""", conn)

if faltante.empty:
    print("\n✅ ¡Todos los activos tienen valoración DIC!")
else:
    print(f"\n❌ Te falta responder {len(faltante)} activo(s):\n")
    for idx, row in faltante.iterrows():
        print(f"  🔴 {row['ID_Activo']}: {row['Nombre_Activo']} ({row['Tipo_Activo']})")

conn.close()
