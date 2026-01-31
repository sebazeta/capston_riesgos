import sqlite3

conn = sqlite3.connect('tita_database.db')
cursor = conn.cursor()

print("="*60)
print("TABLAS EN LA BASE DE DATOS")
print("="*60)

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tablas = cursor.fetchall()

for tabla in tablas:
    print(f"  • {tabla[0]}")

print("\n" + "="*60)
print("TABLAS RELACIONADAS CON CUESTIONARIOS/RESPUESTAS")
print("="*60)

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%CUESTION%' OR name LIKE '%RESPUESTA%' OR name LIKE '%DIC%')")
tablas_relacionadas = cursor.fetchall()

for tabla in tablas_relacionadas:
    print(f"\n📋 Tabla: {tabla[0]}")
    cursor.execute(f"PRAGMA table_info({tabla[0]})")
    columnas = cursor.fetchall()
    print("   Columnas:")
    for col in columnas[:5]:  # Primeras 5 columnas
        print(f"      - {col[1]} ({col[2]})")

conn.close()
