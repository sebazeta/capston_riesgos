import sqlite3

conn = sqlite3.connect('tita_database.db')
cur = conn.cursor()

print("=== TABLAS EXISTENTES ===")
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
for t in cur.fetchall():
    print(f"  - {t[0]}")

print("\n=== ESTRUCTURA RESULTADOS_MAGERIT ===")
cur.execute("PRAGMA table_info(RESULTADOS_MAGERIT)")
for col in cur.fetchall():
    print(f"  {col[1]}: {col[2]}")

print("\n=== ESTRUCTURA EVALUACIONES ===")
cur.execute("PRAGMA table_info(EVALUACIONES)")
for col in cur.fetchall():
    print(f"  {col[1]}: {col[2]}")

conn.close()
