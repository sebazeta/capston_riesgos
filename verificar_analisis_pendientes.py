import sqlite3
import pandas as pd

conn = sqlite3.connect('tita_database.db')

print("="*60)
print("ANÁLISIS DE VULNERABILIDADES")
print("="*60)

# Total activos
total = pd.read_sql("SELECT COUNT(*) as total FROM INVENTARIO_ACTIVOS WHERE ID_Evaluacion = 'EVA-001'", conn)
print(f"\nTotal activos: {total['total'].iloc[0]}")

# Activos con vulnerabilidades
con_vuln = pd.read_sql("""
    SELECT COUNT(DISTINCT ID_Activo) as total 
    FROM VULNERABILIDADES_AMENAZAS 
    WHERE ID_Evaluacion = 'EVA-001'
""", conn)
print(f"Activos con amenazas analizadas: {con_vuln['total'].iloc[0]}")

# Activos pendientes
print("\n" + "="*60)
print("ACTIVOS PENDIENTES (sin amenazas)")
print("="*60)

pendientes = pd.read_sql("""
    SELECT a.ID_Activo, a.Nombre_Activo, a.Tipo_Activo,
           v.D, v.I, v.C, v.Criticidad, v.Criticidad_Nivel
    FROM INVENTARIO_ACTIVOS a
    LEFT JOIN IDENTIFICACION_VALORACION v ON a.ID_Activo = v.ID_Activo AND a.ID_Evaluacion = v.ID_Evaluacion
    WHERE a.ID_Evaluacion = 'EVA-001'
    AND a.ID_Activo NOT IN (
        SELECT DISTINCT ID_Activo 
        FROM VULNERABILIDADES_AMENAZAS 
        WHERE ID_Evaluacion = 'EVA-001'
    )
    ORDER BY a.ID_Activo
""", conn)

if pendientes.empty:
    print("\n✅ Todos los activos tienen amenazas analizadas")
else:
    print(f"\n❌ {len(pendientes)} activos pendientes:\n")
    for idx, row in pendientes.iterrows():
        crit = row['Criticidad'] if pd.notna(row['Criticidad']) else 'Sin DIC'
        print(f"  • {row['ID_Activo']}: {row['Nombre_Activo']} (Criticidad: {crit})")

# Estadísticas de amenazas
print("\n" + "="*60)
print("ESTADÍSTICAS DE AMENAZAS")
print("="*60)

stats = pd.read_sql("""
    SELECT 
        COUNT(*) as Total_Amenazas,
        COUNT(DISTINCT ID_Activo) as Activos_Con_Amenazas,
        AVG(CASE WHEN Degradacion_D > 0 OR Degradacion_I > 0 OR Degradacion_C > 0 THEN 1 ELSE 0 END) * 100 as Pct_Con_Degradacion
    FROM VULNERABILIDADES_AMENAZAS
    WHERE ID_Evaluacion = 'EVA-001'
""", conn)

print(f"\nTotal amenazas registradas: {stats['Total_Amenazas'].iloc[0]}")
print(f"Activos con amenazas: {stats['Activos_Con_Amenazas'].iloc[0]}")
print(f"% con degradación: {stats['Pct_Con_Degradacion'].iloc[0]:.1f}%")

# Promedio de amenazas por activo
avg = pd.read_sql("""
    SELECT ID_Activo, COUNT(*) as Num_Amenazas
    FROM VULNERABILIDADES_AMENAZAS
    WHERE ID_Evaluacion = 'EVA-001'
    GROUP BY ID_Activo
""", conn)

print(f"\nPromedio amenazas por activo: {avg['Num_Amenazas'].mean():.1f}")
print(f"Máximo amenazas en un activo: {avg['Num_Amenazas'].max()}")
print(f"Mínimo amenazas en un activo: {avg['Num_Amenazas'].min()}")

conn.close()
