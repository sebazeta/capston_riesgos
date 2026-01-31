import sqlite3
import pandas as pd

conn = sqlite3.connect('tita_database.db')

print("="*60)
print("VERIFICACIÓN DE RESPUESTAS EN TODAS LAS TABLAS")
print("="*60)

# Tabla RESPUESTAS
try:
    count_respuestas = pd.read_sql("SELECT COUNT(*) as total FROM RESPUESTAS WHERE ID_Evaluacion = 'EVA-001'", conn)
    print(f"\n📋 RESPUESTAS: {count_respuestas['total'].iloc[0]} registros")
except:
    print("\n❌ Error al consultar RESPUESTAS")

# Tabla IDENTIFICACION_VALORACION
try:
    count_dic = pd.read_sql("SELECT COUNT(*) as total FROM IDENTIFICACION_VALORACION WHERE ID_Evaluacion = 'EVA-001'", conn)
    print(f"📋 IDENTIFICACION_VALORACION (DIC): {count_dic['total'].iloc[0]} registros")
    
    if count_dic['total'].iloc[0] > 0:
        print("\n✅ Encontré valoraciones DIC. Mostrando las primeras 5:")
        dic_sample = pd.read_sql("""
            SELECT ID_Activo, Nombre_Activo, D, I, C, Criticidad, Criticidad_Nivel
            FROM IDENTIFICACION_VALORACION 
            WHERE ID_Evaluacion = 'EVA-001'
            LIMIT 5
        """, conn)
        print(dic_sample.to_string(index=False))
except Exception as e:
    print(f"\n❌ Error al consultar IDENTIFICACION_VALORACION: {e}")

# Tabla IMPACTO_ACTIVOS
try:
    count_impacto = pd.read_sql("SELECT COUNT(*) as total FROM IMPACTO_ACTIVOS WHERE ID_Evaluacion = 'EVA-001'", conn)
    print(f"\n📋 IMPACTO_ACTIVOS: {count_impacto['total'].iloc[0]} registros")
except:
    print("\n❌ Error al consultar IMPACTO_ACTIVOS")

# Tabla CUESTIONARIOS (preguntas disponibles)
try:
    count_preguntas = pd.read_sql("SELECT COUNT(*) as total FROM CUESTIONARIOS WHERE ID_Evaluacion = 'EVA-001'", conn)
    print(f"📋 CUESTIONARIOS (preguntas): {count_preguntas['total'].iloc[0]} registros")
except:
    print("❌ Error al consultar CUESTIONARIOS")

# Banco de preguntas
try:
    count_fisicas = pd.read_sql("SELECT COUNT(*) as total FROM BANCO_PREGUNTAS_FISICAS", conn)
    count_virtuales = pd.read_sql("SELECT COUNT(*) as total FROM BANCO_PREGUNTAS_VIRTUALES", conn)
    print(f"\n📋 BANCO_PREGUNTAS_FISICAS: {count_fisicas['total'].iloc[0]} preguntas")
    print(f"📋 BANCO_PREGUNTAS_VIRTUALES: {count_virtuales['total'].iloc[0]} preguntas")
except:
    print("\n❌ Error al consultar bancos de preguntas")

conn.close()

print("\n" + "="*60)
print("CONCLUSIÓN")
print("="*60)
print("\nSi IDENTIFICACION_VALORACION tiene registros,")
print("significa que respondiste las valoraciones DIC (D, I, C).")
print("\nSi RESPUESTAS está vacía, faltan los cuestionarios")
print("completos (BIA, RTO, RPO, preguntas D/I/C detalladas).")
