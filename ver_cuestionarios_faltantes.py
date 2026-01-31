import sqlite3
import pandas as pd

conn = sqlite3.connect('tita_database.db')

# Total de activos
print("="*60)
print("RESUMEN DE CUESTIONARIOS")
print("="*60)

total_activos = pd.read_sql("SELECT COUNT(*) as total FROM INVENTARIO_ACTIVOS WHERE ID_Evaluacion = 'EVA-001'", conn)
print(f"Total activos en EVA-001: {total_activos['total'].iloc[0]}")

# Activos con cuestionario respondido
activos_con_cuest = pd.read_sql("""
    SELECT COUNT(DISTINCT ID_Activo) as total 
    FROM RESPUESTAS 
    WHERE ID_Evaluacion = 'EVA-001'
""", conn)
print(f"Activos con cuestionario respondido: {activos_con_cuest['total'].iloc[0]}")

# Identificar el activo que falta
print("\n" + "="*60)
print("ACTIVO(S) SIN CUESTIONARIO")
print("="*60)

activos_faltantes = pd.read_sql("""
    SELECT a.ID_Activo, a.Nombre_Activo, a.Tipo_Activo
    FROM INVENTARIO_ACTIVOS a
    WHERE a.ID_Evaluacion = 'EVA-001'
    AND a.ID_Activo NOT IN (
        SELECT DISTINCT ID_Activo 
        FROM RESPUESTAS 
        WHERE ID_Evaluacion = 'EVA-001'
    )
    ORDER BY a.ID_Activo
""", conn)

if activos_faltantes.empty:
    print("✅ ¡Todos los activos tienen cuestionario respondido!")
else:
    print(f"\n❌ Faltan {len(activos_faltantes)} activo(s):\n")
    for idx, row in activos_faltantes.iterrows():
        print(f"  • {row['ID_Activo']}: {row['Nombre_Activo']} ({row['Tipo_Activo']})")

# Verificar cuántas respuestas tiene cada activo
print("\n" + "="*60)
print("DETALLE DE RESPUESTAS POR ACTIVO")
print("="*60)

respuestas_por_activo = pd.read_sql("""
    SELECT ID_Activo, COUNT(*) as Num_Respuestas
    FROM RESPUESTAS
    WHERE ID_Evaluacion = 'EVA-001'
    GROUP BY ID_Activo
    ORDER BY Num_Respuestas
    LIMIT 10
""", conn)

print("\nActivos con menos respuestas (primeros 10):")
print(respuestas_por_activo.to_string(index=False))

conn.close()
