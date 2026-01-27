import sqlite3
import sys
sys.path.insert(0, 'c:/capston_riesgos')

conn = sqlite3.connect('tita_database.db')
cur = conn.cursor()

print("=== RESULTADOS_MAGERIT (EVA-003) ===")
cur.execute("SELECT ID_Evaluacion, ID_Activo FROM RESULTADOS_MAGERIT WHERE ID_Evaluacion = 'EVA-003'")
rows = cur.fetchall()
print(f"Total registros EVA-003: {len(rows)}")
for r in rows:
    print(r)

print("\n=== Test get_estadisticas_evaluacion ===")
from services.evaluacion_service import get_estadisticas_evaluacion
stats = get_estadisticas_evaluacion("EVA-003")
print(f"Stats EVA-003: {stats}")

conn.close()
