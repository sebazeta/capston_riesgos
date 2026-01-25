"""
Script para corregir esquema de base de datos SQLite
"""
import sqlite3
import os

DB_PATH = "tita_database.db"

def fix_schema():
    print("=" * 50)
    print("CORRIGIENDO ESQUEMA DE BASE DE DATOS")
    print("=" * 50)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # ============ EVALUACIONES ============
    cursor.execute("PRAGMA table_info(EVALUACIONES)")
    cols_actuales = [row[1] for row in cursor.fetchall()]
    print(f"\nColumnas actuales EVALUACIONES: {cols_actuales}")
    
    columnas_eval = {
        "Fecha_Creacion": "TEXT",
        "Responsable": "TEXT", 
        "Origen_Re_Evaluacion": "TEXT"
    }
    
    for col_name, col_type in columnas_eval.items():
        if col_name not in cols_actuales:
            try:
                cursor.execute(f"ALTER TABLE EVALUACIONES ADD COLUMN {col_name} {col_type}")
                print(f"  + Agregada: {col_name}")
            except Exception as e:
                print(f"  ! Error: {e}")
        else:
            print(f"  ✓ Ya existe: {col_name}")
    
    # ============ INVENTARIO_ACTIVOS ============
    cursor.execute("PRAGMA table_info(INVENTARIO_ACTIVOS)")
    cols_activos = [row[1] for row in cursor.fetchall()]
    print(f"\nColumnas actuales INVENTARIO_ACTIVOS: {cols_activos}")
    
    cols_activos_necesarias = {
        "Descripcion": "TEXT",
        "Fecha_Creacion": "TEXT",
        "RTO": "TEXT",
        "RPO": "TEXT",
        "BIA": "TEXT",
        "Criticidad": "TEXT"
    }
    
    for col_name, col_type in cols_activos_necesarias.items():
        if col_name not in cols_activos:
            try:
                cursor.execute(f"ALTER TABLE INVENTARIO_ACTIVOS ADD COLUMN {col_name} {col_type}")
                print(f"  + Agregada: {col_name}")
            except Exception as e:
                print(f"  ! Error: {e}")
        else:
            print(f"  ✓ Ya existe: {col_name}")
    
    # ============ CUESTIONARIOS ============
    cursor.execute("PRAGMA table_info(CUESTIONARIOS)")
    cols_cuest = [row[1] for row in cursor.fetchall()]
    print(f"\nColumnas actuales CUESTIONARIOS: {cols_cuest}")
    
    cols_cuest_necesarias = {
        "ID_Evaluacion": "TEXT",
        "ID_Activo": "TEXT",
        "ID_Pregunta": "TEXT",
        "Pregunta": "TEXT",
        "Categoria": "TEXT",
        "Tipo_Respuesta": "TEXT",
        "Opciones": "TEXT",
        "Version": "INTEGER"
    }
    
    for col_name, col_type in cols_cuest_necesarias.items():
        if col_name not in cols_cuest:
            try:
                cursor.execute(f"ALTER TABLE CUESTIONARIOS ADD COLUMN {col_name} {col_type}")
                print(f"  + Agregada: {col_name}")
            except Exception as e:
                print(f"  ! Error: {e}")
        else:
            print(f"  ✓ Ya existe: {col_name}")
    
    # ============ RESPUESTAS ============
    cursor.execute("PRAGMA table_info(RESPUESTAS)")
    cols_resp = [row[1] for row in cursor.fetchall()]
    print(f"\nColumnas actuales RESPUESTAS: {cols_resp}")
    
    cols_resp_necesarias = {
        "ID_Evaluacion": "TEXT",
        "ID_Activo": "TEXT",
        "ID_Pregunta": "TEXT",
        "Respuesta": "TEXT",
        "Fecha_Respuesta": "TEXT",
        "Usuario": "TEXT"
    }
    
    for col_name, col_type in cols_resp_necesarias.items():
        if col_name not in cols_resp:
            try:
                cursor.execute(f"ALTER TABLE RESPUESTAS ADD COLUMN {col_name} {col_type}")
                print(f"  + Agregada: {col_name}")
            except Exception as e:
                print(f"  ! Error: {e}")
        else:
            print(f"  ✓ Ya existe: {col_name}")
    
    # ============ RESULTADOS_MAGERIT ============
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS RESULTADOS_MAGERIT (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_Evaluacion TEXT,
                ID_Activo TEXT,
                Nombre_Activo TEXT,
                Impacto_D INTEGER,
                Impacto_I INTEGER,
                Impacto_C INTEGER,
                Riesgo_Inherente REAL,
                Riesgo_Residual REAL,
                Nivel_Riesgo TEXT,
                Amenazas_JSON TEXT,
                Controles_JSON TEXT,
                Observaciones TEXT,
                Modelo_IA TEXT,
                Fecha_Evaluacion TEXT
            )
        ''')
        print("\n✓ Tabla RESULTADOS_MAGERIT verificada/creada")
    except Exception as e:
        print(f"\n! Error con RESULTADOS_MAGERIT: {e}")
    
    # ============ IA_STATUS ============
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS IA_STATUS (
                id INTEGER PRIMARY KEY,
                ia_ready INTEGER DEFAULT 0,
                last_validation TEXT,
                validation_result TEXT,
                canary_nonce TEXT,
                knowledge_version TEXT
            )
        ''')
        print("✓ Tabla IA_STATUS verificada/creada")
    except Exception as e:
        print(f"! Error con IA_STATUS: {e}")
    
    conn.commit()
    
    # Verificar resultado final
    print("\n" + "=" * 50)
    print("ESQUEMA FINAL:")
    for tabla in ["EVALUACIONES", "INVENTARIO_ACTIVOS", "CUESTIONARIOS", "RESPUESTAS"]:
        cursor.execute(f"PRAGMA table_info({tabla})")
        cols = [row[1] for row in cursor.fetchall()]
        print(f"  {tabla}: {len(cols)} columnas")
    
    conn.close()
    print("\n✅ Esquema corregido completamente")

if __name__ == "__main__":
    fix_schema()
