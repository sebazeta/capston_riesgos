import sqlite3
import pandas as pd

conn = sqlite3.connect('tita_database.db')

print("="*60)
print("VERIFICACIÓN DE DATOS EN VULNERABILIDADES_AMENAZAS")
print("="*60)

# Ver estructura de la tabla
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(VULNERABILIDADES_AMENAZAS)")
columnas = cursor.fetchall()
print("\n📋 Columnas de la tabla:")
for col in columnas:
    print(f"  • {col[1]} ({col[2]})")

# Ver primeros 10 registros
print("\n" + "="*60)
print("PRIMEROS 10 REGISTROS")
print("="*60)

df = pd.read_sql("""
    SELECT ID_Activo, Cod_Amenaza, Amenaza, Cod_Vulnerabilidad, Vulnerabilidad, 
           Degradacion_D, Degradacion_I, Degradacion_C
    FROM VULNERABILIDADES_AMENAZAS
    WHERE ID_Evaluacion = 'EVA-001'
    LIMIT 10
""", conn)

print(df.to_string(index=False))

# Verificar valores de degradación
print("\n" + "="*60)
print("ESTADÍSTICAS DE DEGRADACIÓN")
print("="*60)

stats = pd.read_sql("""
    SELECT 
        COUNT(*) as Total,
        SUM(CASE WHEN Degradacion_D > 0 THEN 1 ELSE 0 END) as Con_Deg_D,
        SUM(CASE WHEN Degradacion_I > 0 THEN 1 ELSE 0 END) as Con_Deg_I,
        SUM(CASE WHEN Degradacion_C > 0 THEN 1 ELSE 0 END) as Con_Deg_C,
        SUM(CASE WHEN Cod_Amenaza IS NOT NULL AND Cod_Amenaza != '' THEN 1 ELSE 0 END) as Con_Cod_Amenaza,
        AVG(Degradacion_D) as Avg_Deg_D,
        AVG(Degradacion_I) as Avg_Deg_I,
        AVG(Degradacion_C) as Avg_Deg_C
    FROM VULNERABILIDADES_AMENAZAS
    WHERE ID_Evaluacion = 'EVA-001'
""", conn)

print(f"\nTotal registros: {stats['Total'].iloc[0]}")
print(f"Con Cod_Amenaza: {stats['Con_Cod_Amenaza'].iloc[0]}")
print(f"Con Degradación D > 0: {stats['Con_Deg_D'].iloc[0]}")
print(f"Con Degradación I > 0: {stats['Con_Deg_I'].iloc[0]}")
print(f"Con Degradación C > 0: {stats['Con_Deg_C'].iloc[0]}")
print(f"\nPromedio Deg_D: {stats['Avg_Deg_D'].iloc[0]}")
print(f"Promedio Deg_I: {stats['Avg_Deg_I'].iloc[0]}")
print(f"Promedio Deg_C: {stats['Avg_Deg_C'].iloc[0]}")

# Ver códigos únicos
print("\n" + "="*60)
print("CÓDIGOS ÚNICOS DE AMENAZAS Y VULNERABILIDADES")
print("="*60)

codigos_amenaza = pd.read_sql("""
    SELECT DISTINCT Cod_Amenaza 
    FROM VULNERABILIDADES_AMENAZAS 
    WHERE ID_Evaluacion = 'EVA-001' AND Cod_Amenaza IS NOT NULL
    LIMIT 20
""", conn)

print("\nCod_Amenaza únicos (primeros 20):")
for idx, row in codigos_amenaza.iterrows():
    print(f"  • {row['Cod_Amenaza']}")

codigos_vuln = pd.read_sql("""
    SELECT DISTINCT Cod_Vulnerabilidad 
    FROM VULNERABILIDADES_AMENAZAS 
    WHERE ID_Evaluacion = 'EVA-001' AND Cod_Vulnerabilidad IS NOT NULL
    LIMIT 20
""", conn)

print("\nCod_Vulnerabilidad únicos (primeros 20):")
for idx, row in codigos_vuln.iterrows():
    print(f"  • {row['Cod_Vulnerabilidad']}")

conn.close()
