"""
MIGRACIÓN COMPLETA - Refactorización MAGERIT v2.0
==================================================
Implementa todas las extensiones del modelo de datos.
"""
import sqlite3
import json
from datetime import datetime

def migrate_complete():
    conn = sqlite3.connect('tita_database.db')
    cur = conn.cursor()
    
    print("=" * 70)
    print("MIGRACIÓN COMPLETA - Refactorización MAGERIT v2.0")
    print("=" * 70)
    
    # =========================================================================
    # FASE 1.1: EXTENDER INVENTARIO_ACTIVOS
    # =========================================================================
    print("\n[FASE 1.1] Extendiendo INVENTARIO_ACTIVOS...")
    
    cur.execute("PRAGMA table_info(INVENTARIO_ACTIVOS)")
    columnas_existentes = [col[1] for col in cur.fetchall()]
    
    nuevas_columnas_activos = [
        ("Ubicacion_Fisica", "TEXT"),
        ("Ubicacion_Logica", "TEXT"),
        ("Host_Fisico", "TEXT"),
        ("Servicio_Aplicacion", "TEXT"),
        ("Propietario", "TEXT"),
        ("Nivel_Exposicion", "TEXT DEFAULT 'Interno'"),
        ("Dependencias_JSON", "TEXT"),
        ("Criticidad_Negocio", "TEXT DEFAULT 'Media'"),
        ("Fecha_Alta", "TEXT"),
        ("Ultima_Modificacion", "TEXT"),
    ]
    
    for col_name, col_def in nuevas_columnas_activos:
        if col_name not in columnas_existentes:
            try:
                cur.execute(f"ALTER TABLE INVENTARIO_ACTIVOS ADD COLUMN {col_name} {col_def}")
                print(f"   + {col_name}")
            except Exception as e:
                print(f"   - {col_name} (ya existe o error: {e})")
        else:
            print(f"   = {col_name} (existente)")
    
    # =========================================================================
    # FASE 1.2: CREAR/ACTUALIZAR VULNERABILIDADES_ACTIVO
    # =========================================================================
    print("\n[FASE 1.2] Creando VULNERABILIDADES_ACTIVO...")
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS VULNERABILIDADES_ACTIVO (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_Evaluacion TEXT NOT NULL,
            ID_Activo TEXT NOT NULL,
            Codigo_Vulnerabilidad TEXT,
            Nombre TEXT,
            Descripcion TEXT NOT NULL,
            Severidad TEXT DEFAULT 'Media',
            CVSS_Score REAL,
            Amenazas_Asociadas_JSON TEXT,
            Controles_Mitigantes_JSON TEXT,
            Fuente TEXT DEFAULT 'manual',
            Fecha_Identificacion TEXT,
            Fecha_Remediacion TEXT,
            Estado TEXT DEFAULT 'Abierta',
            Responsable_Remediacion TEXT,
            Observaciones TEXT,
            UNIQUE(ID_Evaluacion, ID_Activo, Codigo_Vulnerabilidad)
        )
    ''')
    print("   + VULNERABILIDADES_ACTIVO creada/verificada")
    
    # =========================================================================
    # FASE 1.3: CREAR HISTORIAL_EVALUACIONES
    # =========================================================================
    print("\n[FASE 1.3] Creando HISTORIAL_EVALUACIONES...")
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS HISTORIAL_EVALUACIONES (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_Evaluacion_Origen TEXT NOT NULL,
            ID_Evaluacion_Destino TEXT NOT NULL,
            Tipo_Comparacion TEXT DEFAULT 'reevaluacion',
            Fecha_Comparacion TEXT,
            Resumen_Cambios TEXT,
            Total_Activos_Origen INTEGER,
            Total_Activos_Destino INTEGER,
            Riesgo_Promedio_Origen REAL,
            Riesgo_Promedio_Destino REAL,
            Delta_Riesgo_Promedio REAL,
            Riesgo_Maximo_Origen REAL,
            Riesgo_Maximo_Destino REAL,
            Delta_Riesgo_Maximo REAL,
            Activos_Mejorados INTEGER DEFAULT 0,
            Activos_Deteriorados INTEGER DEFAULT 0,
            Activos_Sin_Cambio INTEGER DEFAULT 0,
            Detalle_Mejoras_JSON TEXT,
            Detalle_Deterioros_JSON TEXT,
            Observaciones TEXT
        )
    ''')
    print("   + HISTORIAL_EVALUACIONES creada/verificada")
    
    # =========================================================================
    # FASE 1.4: CREAR TRATAMIENTO_RIESGOS
    # =========================================================================
    print("\n[FASE 1.4] Creando TRATAMIENTO_RIESGOS...")
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS TRATAMIENTO_RIESGOS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_Evaluacion TEXT NOT NULL,
            ID_Activo TEXT NOT NULL,
            Codigo_Amenaza TEXT,
            Tipo_Tratamiento TEXT NOT NULL,
            Justificacion TEXT,
            Riesgo_Actual REAL,
            Riesgo_Objetivo REAL,
            Controles_Propuestos_JSON TEXT,
            Responsable TEXT,
            Fecha_Limite TEXT,
            Estado TEXT DEFAULT 'Pendiente',
            Fecha_Cierre TEXT,
            Observaciones TEXT,
            UNIQUE(ID_Evaluacion, ID_Activo, Codigo_Amenaza)
        )
    ''')
    print("   + TRATAMIENTO_RIESGOS creada/verificada")
    
    # =========================================================================
    # FASE 1.5: CREAR AUDITORIA_CAMBIOS
    # =========================================================================
    print("\n[FASE 1.5] Creando AUDITORIA_CAMBIOS...")
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS AUDITORIA_CAMBIOS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Tabla_Afectada TEXT NOT NULL,
            ID_Registro TEXT,
            Tipo_Operacion TEXT NOT NULL,
            Valores_Anteriores_JSON TEXT,
            Valores_Nuevos_JSON TEXT,
            Usuario TEXT DEFAULT 'sistema',
            Fecha_Hora TEXT NOT NULL,
            IP_Origen TEXT,
            Motivo TEXT
        )
    ''')
    print("   + AUDITORIA_CAMBIOS creada/verificada")
    
    # =========================================================================
    # FASE 1.6: CREAR CONFIGURACION_EVALUACION
    # =========================================================================
    print("\n[FASE 1.6] Creando CONFIGURACION_EVALUACION...")
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS CONFIGURACION_EVALUACION (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_Evaluacion TEXT NOT NULL UNIQUE,
            Limite_Riesgo_Aceptable REAL DEFAULT 7.0,
            Factor_Riesgo_Objetivo REAL DEFAULT 0.5,
            Metodo_Agregacion TEXT DEFAULT 'promedio',
            Incluir_Riesgo_Heredado INTEGER DEFAULT 1,
            Incluir_Concentracion INTEGER DEFAULT 1,
            Umbral_Critico REAL DEFAULT 20.0,
            Umbral_Alto REAL DEFAULT 12.0,
            Umbral_Medio REAL DEFAULT 6.0,
            Umbral_Bajo REAL DEFAULT 3.0,
            Modelo_IA_Preferido TEXT DEFAULT 'llama3.2',
            Fecha_Configuracion TEXT
        )
    ''')
    print("   + CONFIGURACION_EVALUACION creada/verificada")
    
    # =========================================================================
    # FASE 1.7: ÍNDICES PARA RENDIMIENTO
    # =========================================================================
    print("\n[FASE 1.7] Creando índices...")
    
    indices = [
        ("idx_activos_eval", "INVENTARIO_ACTIVOS", "ID_Evaluacion"),
        ("idx_activos_tipo", "INVENTARIO_ACTIVOS", "Tipo_Activo"),
        ("idx_resultados_eval", "RESULTADOS_MAGERIT", "ID_Evaluacion"),
        ("idx_resultados_activo", "RESULTADOS_MAGERIT", "ID_Activo"),
        ("idx_degradacion_eval", "DEGRADACION_AMENAZAS", "ID_Evaluacion"),
        ("idx_vuln_eval", "VULNERABILIDADES_ACTIVO", "ID_Evaluacion"),
        ("idx_vuln_activo", "VULNERABILIDADES_ACTIVO", "ID_Activo"),
        ("idx_tratamiento_eval", "TRATAMIENTO_RIESGOS", "ID_Evaluacion"),
        ("idx_auditoria_tabla", "AUDITORIA_CAMBIOS", "Tabla_Afectada"),
        ("idx_auditoria_fecha", "AUDITORIA_CAMBIOS", "Fecha_Hora"),
    ]
    
    for idx_name, tabla, columna in indices:
        try:
            cur.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {tabla}({columna})")
            print(f"   + {idx_name}")
        except Exception as e:
            print(f"   - {idx_name}: {e}")
    
    # =========================================================================
    # FASE 1.8: MIGRAR DATOS EXISTENTES
    # =========================================================================
    print("\n[FASE 1.8] Configurando valores por defecto...")
    
    # Actualizar activos existentes con fecha
    cur.execute('''
        UPDATE INVENTARIO_ACTIVOS 
        SET Fecha_Alta = ?, Nivel_Exposicion = 'Interno'
        WHERE Fecha_Alta IS NULL
    ''', [datetime.now().strftime("%Y-%m-%d")])
    
    # Crear configuración para evaluaciones existentes
    cur.execute("SELECT ID_Evaluacion FROM EVALUACIONES")
    evaluaciones = cur.fetchall()
    for (eval_id,) in evaluaciones:
        cur.execute('''
            INSERT OR IGNORE INTO CONFIGURACION_EVALUACION 
            (ID_Evaluacion, Fecha_Configuracion)
            VALUES (?, ?)
        ''', [eval_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    
    print(f"   + {len(evaluaciones)} evaluaciones configuradas")
    
    # =========================================================================
    # COMMIT Y VERIFICACIÓN
    # =========================================================================
    conn.commit()
    
    print("\n" + "=" * 70)
    print("VERIFICACIÓN POST-MIGRACIÓN")
    print("=" * 70)
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tablas = [t[0] for t in cur.fetchall()]
    
    tablas_requeridas = [
        'INVENTARIO_ACTIVOS', 'EVALUACIONES', 'RESULTADOS_MAGERIT',
        'DEGRADACION_AMENAZAS', 'VULNERABILIDADES_ACTIVO',
        'HISTORIAL_EVALUACIONES', 'TRATAMIENTO_RIESGOS',
        'AUDITORIA_CAMBIOS', 'CONFIGURACION_EVALUACION'
    ]
    
    print(f"\nTablas totales: {len(tablas)}")
    print("\nTablas del modelo MAGERIT:")
    for t in tablas_requeridas:
        status = "OK" if t in tablas else "FALTA"
        print(f"   [{status}] {t}")
    
    # Verificar columnas de INVENTARIO_ACTIVOS
    cur.execute("PRAGMA table_info(INVENTARIO_ACTIVOS)")
    cols = [col[1] for col in cur.fetchall()]
    print(f"\nColumnas INVENTARIO_ACTIVOS: {len(cols)}")
    
    nuevas = ['Ubicacion_Fisica', 'Host_Fisico', 'Propietario', 'Nivel_Exposicion']
    for col in nuevas:
        status = "OK" if col in cols else "FALTA"
        print(f"   [{status}] {col}")
    
    conn.close()
    print("\n" + "=" * 70)
    print("MIGRACIÓN FASE 1 COMPLETADA")
    print("=" * 70)


if __name__ == "__main__":
    migrate_complete()
