"""Script para verificar el estado de la base de datos"""
import sqlite3
import pandas as pd

conn = sqlite3.connect('tita_database.db')
cursor = conn.cursor()

# Ver todas las tablas
print('='*60)
print('TABLAS EN LA BASE DE DATOS:')
print('='*60)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
for table in cursor.fetchall():
    print(f'  - {table[0]}')

print('\n' + '='*60)
print('ESTRUCTURA DE EVALUACIONES:')
print('='*60)
cursor.execute('PRAGMA table_info(EVALUACIONES)')
for col in cursor.fetchall():
    print(f'  {col[1]} ({col[2]})')

print('\n' + '='*60)
print('ESTRUCTURA DE RIESGO_ACTIVOS:')
print('='*60)
cursor.execute('PRAGMA table_info(RIESGO_ACTIVOS)')
for col in cursor.fetchall():
    print(f'  {col[1]} ({col[2]})')

print('\n' + '='*60)
print('DATOS EN EVALUACIONES:')
print('='*60)
evals = pd.read_sql_query('SELECT * FROM EVALUACIONES', conn)
print(evals.to_string())

print('\n' + '='*60)
print('ACTIVOS POR EVALUACION:')
print('='*60)
activos = pd.read_sql_query('''
SELECT ID_Evaluacion, COUNT(*) as Total_Activos 
FROM INVENTARIO_ACTIVOS 
GROUP BY ID_Evaluacion
''', conn)
print(activos.to_string() if not activos.empty else 'No hay activos')

print('\n' + '='*60)
print('RIESGO_ACTIVOS POR EVALUACION:')
print('='*60)
riesgos_activos = pd.read_sql_query('''
SELECT ID_Evaluacion, COUNT(*) as Total_Registros 
FROM RIESGO_ACTIVOS 
GROUP BY ID_Evaluacion
''', conn)
print(riesgos_activos.to_string() if not riesgos_activos.empty else 'No hay riesgos')

print('\n' + '='*60)
print('EVALUACIONES EN RIESGO_ACTIVOS QUE NO EXISTEN EN EVALUACIONES:')
print('='*60)
huerfanos = pd.read_sql_query('''
SELECT DISTINCT ra.ID_Evaluacion, COUNT(*) as Registros_Huerfanos
FROM RIESGO_ACTIVOS ra
LEFT JOIN EVALUACIONES e ON ra.ID_Evaluacion = e.ID_Evaluacion
WHERE e.ID_Evaluacion IS NULL
GROUP BY ra.ID_Evaluacion
''', conn)
print(huerfanos.to_string() if not huerfanos.empty else 'No hay registros huerfanos')

print('\n' + '='*60)
print('ACTIVOS EN RIESGO_ACTIVOS QUE NO EXISTEN EN INVENTARIO_ACTIVOS:')
print('='*60)
activos_huerfanos = pd.read_sql_query('''
SELECT ra.ID_Evaluacion, ra.ID_Activo, ra.Nombre_Activo
FROM RIESGO_ACTIVOS ra
LEFT JOIN INVENTARIO_ACTIVOS ia ON ra.ID_Activo = ia.ID_Activo AND ra.ID_Evaluacion = ia.ID_Evaluacion
WHERE ia.ID_Activo IS NULL
''', conn)
print(activos_huerfanos.to_string() if not activos_huerfanos.empty else 'No hay activos huerfanos')

print('\n' + '='*60)
print('DETALLE DE RIESGO_ACTIVOS (todos los registros):')
print('='*60)
all_riesgos = pd.read_sql_query('SELECT ID_Evaluacion, ID_Activo, Nombre_Activo, Riesgo_Actual FROM RIESGO_ACTIVOS', conn)
print(all_riesgos.to_string() if not all_riesgos.empty else 'No hay registros')

conn.close()
