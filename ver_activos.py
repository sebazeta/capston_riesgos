import sqlite3
import pandas as pd

conn = sqlite3.connect('tita_database.db')

# Ver evaluaciones
print("="*60)
print("EVALUACIONES ACTIVAS")
print("="*60)
df_eval = pd.read_sql("SELECT ID_Evaluacion, COUNT(*) as Total_Activos FROM INVENTARIO_ACTIVOS GROUP BY ID_Evaluacion", conn)
print(df_eval.to_string(index=False))

# Ver primeros 10 activos
print("\n" + "="*60)
print("PRIMEROS 10 ACTIVOS")
print("="*60)
df_activos = pd.read_sql("SELECT ID_Activo, Nombre_Activo, Tipo_Activo FROM INVENTARIO_ACTIVOS ORDER BY ID_Activo LIMIT 10", conn)
print(df_activos.to_string(index=False))

# Ver si hay valoraciones DIC
print("\n" + "="*60)
print("VALORACIONES DIC")
print("="*60)
df_dic = pd.read_sql("SELECT COUNT(*) as Total_Valoraciones FROM IDENTIFICACION_VALORACION", conn)
print(f"Total valoraciones DIC: {df_dic['Total_Valoraciones'].iloc[0]}")

# Ver tipo de activos
print("\n" + "="*60)
print("DISTRIBUCIÓN POR TIPO")
print("="*60)
df_tipos = pd.read_sql("SELECT Tipo_Activo, COUNT(*) as Cantidad FROM INVENTARIO_ACTIVOS GROUP BY Tipo_Activo", conn)
print(df_tipos.to_string(index=False))

conn.close()
