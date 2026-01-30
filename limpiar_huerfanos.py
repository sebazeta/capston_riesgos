"""Script para limpiar datos huérfanos de la base de datos"""
import sqlite3

def limpiar_datos_huerfanos():
    conn = sqlite3.connect('tita_database.db')
    cursor = conn.cursor()
    
    print("="*60)
    print("LIMPIEZA DE DATOS HUÉRFANOS EN LA BASE DE DATOS")
    print("="*60)
    
    # Lista de tablas que tienen referencia a ID_Evaluacion
    tablas_con_evaluacion = [
        'RIESGO_ACTIVOS',
        'RIESGO_AMENAZA', 
        'MAPA_RIESGOS',
        'SALVAGUARDAS',
        'VULNERABILIDADES_AMENAZAS',
        'IDENTIFICACION_VALORACION',
        'CUESTIONARIOS',
        'RESPUESTAS',
        'IMPACTO_ACTIVOS',
        'ANALISIS_RIESGO',
        'RESULTADOS_MAGERIT',
        'RESULTADOS_MADUREZ',
        'RESULTADOS_CONCENTRACION',
        'RIESGO_HEREDADO',
        'IA_RESULTADOS_AVANZADOS',
        'DEGRADACION_AMENAZAS',
        'VULNERABILIDADES',
        'VULNERABILIDADES_ACTIVO',
        'HISTORIAL_EVALUACIONES',
        'TRATAMIENTO_RIESGOS',
        'AUDITORIA_CAMBIOS',
        'CONFIGURACION_EVALUACION',
        'IA_STATUS',
        'IA_EXECUTION_EVIDENCE',
        'IA_VALIDATION_LOG',
        'INVENTARIO_ACTIVOS'
    ]
    
    total_eliminados = 0
    
    # 1. Eliminar registros de evaluaciones que no existen
    print("\n1. Limpiando registros de evaluaciones eliminadas...")
    for tabla in tablas_con_evaluacion:
        try:
            # Verificar si la tabla existe y tiene la columna ID_Evaluacion
            cursor.execute(f"PRAGMA table_info({tabla})")
            columnas = [col[1] for col in cursor.fetchall()]
            
            if 'ID_Evaluacion' not in columnas:
                continue
                
            # Contar registros huérfanos
            cursor.execute(f'''
                SELECT COUNT(*) FROM {tabla} t
                LEFT JOIN EVALUACIONES e ON t.ID_Evaluacion = e.ID_Evaluacion
                WHERE e.ID_Evaluacion IS NULL
            ''')
            count = cursor.fetchone()[0]
            
            if count > 0:
                # Eliminar registros huérfanos
                cursor.execute(f'''
                    DELETE FROM {tabla} 
                    WHERE ID_Evaluacion NOT IN (SELECT ID_Evaluacion FROM EVALUACIONES)
                ''')
                print(f"   ✅ {tabla}: {count} registros huérfanos eliminados")
                total_eliminados += count
            else:
                print(f"   ⏭️  {tabla}: sin registros huérfanos")
                
        except Exception as e:
            print(f"   ⚠️  {tabla}: Error - {str(e)[:50]}")
    
    # 2. Eliminar registros de activos que no existen en INVENTARIO_ACTIVOS
    print("\n2. Limpiando registros de activos eliminados...")
    
    tablas_con_activo = [
        'RIESGO_ACTIVOS',
        'IDENTIFICACION_VALORACION',
        'CUESTIONARIOS',
        'RESPUESTAS',
        'IMPACTO_ACTIVOS',
        'VULNERABILIDADES_AMENAZAS',
        'RIESGO_AMENAZA',
        'SALVAGUARDAS',
        'DEGRADACION_AMENAZAS',
        'VULNERABILIDADES_ACTIVO'
    ]
    
    for tabla in tablas_con_activo:
        try:
            cursor.execute(f"PRAGMA table_info({tabla})")
            columnas = [col[1] for col in cursor.fetchall()]
            
            if 'ID_Activo' not in columnas or 'ID_Evaluacion' not in columnas:
                continue
            
            # Contar registros con activos huérfanos
            cursor.execute(f'''
                SELECT COUNT(*) FROM {tabla} t
                LEFT JOIN INVENTARIO_ACTIVOS ia 
                    ON t.ID_Activo = ia.ID_Activo AND t.ID_Evaluacion = ia.ID_Evaluacion
                WHERE ia.ID_Activo IS NULL
            ''')
            count = cursor.fetchone()[0]
            
            if count > 0:
                # Eliminar registros con activos huérfanos
                cursor.execute(f'''
                    DELETE FROM {tabla} 
                    WHERE NOT EXISTS (
                        SELECT 1 FROM INVENTARIO_ACTIVOS ia 
                        WHERE ia.ID_Activo = {tabla}.ID_Activo 
                        AND ia.ID_Evaluacion = {tabla}.ID_Evaluacion
                    )
                ''')
                print(f"   ✅ {tabla}: {count} registros con activos huérfanos eliminados")
                total_eliminados += count
            else:
                print(f"   ⏭️  {tabla}: sin activos huérfanos")
                
        except Exception as e:
            print(f"   ⚠️  {tabla}: Error - {str(e)[:50]}")
    
    conn.commit()
    
    print("\n" + "="*60)
    print(f"LIMPIEZA COMPLETADA: {total_eliminados} registros eliminados en total")
    print("="*60)
    
    # Verificar estado final
    print("\n📊 ESTADO FINAL DE LA BASE DE DATOS:")
    
    cursor.execute("SELECT COUNT(*) FROM EVALUACIONES")
    print(f"   - Evaluaciones: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM INVENTARIO_ACTIVOS")
    print(f"   - Activos: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM RIESGO_ACTIVOS")
    print(f"   - Riesgo por Activos: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM RIESGO_AMENAZA")
    print(f"   - Riesgos (amenazas): {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM SALVAGUARDAS")
    print(f"   - Salvaguardas: {cursor.fetchone()[0]}")
    
    conn.close()
    print("\n✅ Base de datos limpia y consistente.")

if __name__ == "__main__":
    limpiar_datos_huerfanos()
