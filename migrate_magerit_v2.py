"""
Script de migración para alinear TITA con Marco Teórico MAGERIT
================================================================
Cambios:
1. Crear tabla DEGRADACION_AMENAZAS
2. Agregar campos a EVALUACIONES (Limite_Riesgo)
3. Agregar campos a RESULTADOS_MAGERIT (Riesgo_Promedio, Riesgo_Maximo, Riesgo_Objetivo)
"""
import sqlite3
import json
from datetime import datetime

def migrate_database():
    conn = sqlite3.connect('tita_database.db')
    cur = conn.cursor()
    
    print("=" * 60)
    print("MIGRACIÓN: Alineación con Marco Teórico MAGERIT")
    print("=" * 60)
    
    # =========================================================
    # 1. CREAR TABLA DEGRADACION_AMENAZAS
    # =========================================================
    print("\n[1/4] Creando tabla DEGRADACION_AMENAZAS...")
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS DEGRADACION_AMENAZAS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_Evaluacion TEXT NOT NULL,
            ID_Activo TEXT NOT NULL,
            Codigo_Amenaza TEXT NOT NULL,
            Degradacion_D REAL DEFAULT 0.5,
            Degradacion_I REAL DEFAULT 0.5,
            Degradacion_C REAL DEFAULT 0.5,
            Justificacion TEXT,
            Fuente TEXT DEFAULT 'manual',
            Fecha_Registro TEXT,
            UNIQUE(ID_Evaluacion, ID_Activo, Codigo_Amenaza)
        )
    ''')
    print("   ✓ Tabla DEGRADACION_AMENAZAS creada")
    
    # =========================================================
    # 2. AGREGAR CAMPOS A EVALUACIONES (Limite_Riesgo)
    # =========================================================
    print("\n[2/4] Agregando campos a EVALUACIONES...")
    
    # Verificar si la columna ya existe
    cur.execute("PRAGMA table_info(EVALUACIONES)")
    columnas = [col[1] for col in cur.fetchall()]
    
    if 'Limite_Riesgo' not in columnas:
        cur.execute('ALTER TABLE EVALUACIONES ADD COLUMN Limite_Riesgo REAL DEFAULT 7.0')
        print("   ✓ Columna Limite_Riesgo agregada (default=7.0)")
    else:
        print("   - Columna Limite_Riesgo ya existe")
    
    if 'Factor_Objetivo' not in columnas:
        cur.execute('ALTER TABLE EVALUACIONES ADD COLUMN Factor_Objetivo REAL DEFAULT 0.5')
        print("   ✓ Columna Factor_Objetivo agregada (default=0.5)")
    else:
        print("   - Columna Factor_Objetivo ya existe")
    
    # =========================================================
    # 3. AGREGAR CAMPOS A RESULTADOS_MAGERIT
    # =========================================================
    print("\n[3/4] Agregando campos a RESULTADOS_MAGERIT...")
    
    cur.execute("PRAGMA table_info(RESULTADOS_MAGERIT)")
    columnas_rm = [col[1] for col in cur.fetchall()]
    
    nuevas_columnas = [
        ('Criticidad', 'INTEGER DEFAULT 3'),
        ('Riesgo_Promedio', 'REAL'),
        ('Riesgo_Maximo', 'REAL'),
        ('Riesgo_Objetivo', 'REAL'),
        ('Supera_Limite', 'INTEGER DEFAULT 0'),
    ]
    
    for col_name, col_def in nuevas_columnas:
        if col_name not in columnas_rm:
            cur.execute(f'ALTER TABLE RESULTADOS_MAGERIT ADD COLUMN {col_name} {col_def}')
            print(f"   ✓ Columna {col_name} agregada")
        else:
            print(f"   - Columna {col_name} ya existe")
    
    # =========================================================
    # 4. CREAR TABLA VULNERABILIDADES (para trazabilidad completa)
    # =========================================================
    print("\n[4/4] Creando tabla VULNERABILIDADES...")
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS VULNERABILIDADES (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_Evaluacion TEXT NOT NULL,
            ID_Activo TEXT NOT NULL,
            Codigo_Vulnerabilidad TEXT,
            Descripcion TEXT NOT NULL,
            Amenazas_Asociadas TEXT,
            Fecha_Identificacion TEXT,
            Fuente TEXT DEFAULT 'manual'
        )
    ''')
    print("   ✓ Tabla VULNERABILIDADES creada")
    
    # =========================================================
    # COMMIT Y VERIFICACIÓN
    # =========================================================
    conn.commit()
    
    print("\n" + "=" * 60)
    print("VERIFICACIÓN POST-MIGRACIÓN")
    print("=" * 60)
    
    # Verificar tablas
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tablas = [t[0] for t in cur.fetchall()]
    
    tablas_requeridas = ['DEGRADACION_AMENAZAS', 'VULNERABILIDADES', 'RESULTADOS_MAGERIT', 'EVALUACIONES']
    for t in tablas_requeridas:
        status = "✓" if t in tablas else "✗"
        print(f"  {status} {t}")
    
    # Verificar columnas de RESULTADOS_MAGERIT
    cur.execute("PRAGMA table_info(RESULTADOS_MAGERIT)")
    cols = [col[1] for col in cur.fetchall()]
    print(f"\nColumnas RESULTADOS_MAGERIT: {len(cols)}")
    for col in ['Criticidad', 'Riesgo_Promedio', 'Riesgo_Maximo', 'Riesgo_Objetivo', 'Supera_Limite']:
        status = "✓" if col in cols else "✗"
        print(f"  {status} {col}")
    
    conn.close()
    print("\n✅ Migración completada exitosamente")


if __name__ == "__main__":
    migrate_database()
