"""
Script para limpiar los datos de la base de datos TITA
Elimina todos los registros pero mantiene la estructura de las tablas
"""
import sqlite3

def limpiar_base_datos():
    conn = sqlite3.connect('tita_database.db')
    cursor = conn.cursor()
    
    # Obtener todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("=== TABLAS EN LA BASE DE DATOS ===")
    for t in tables:
        tabla = t[0]
        cursor.execute(f"SELECT COUNT(*) FROM [{tabla}]")
        count = cursor.fetchone()[0]
        print(f"{tabla}: {count} registros")
    
    print("\n=== LIMPIANDO DATOS ===")
    
    # Tablas de datos principales a limpiar (en orden para evitar FK issues)
    tablas_limpiar = [
        "SALVAGUARDAS_ACTIVO",
        "RIESGO_ACTIVOS_AGREGADO",
        "MAPA_RIESGOS",
        "RIESGO_CALCULADO",
        "VULNERABILIDADES_AMENAZAS",
        "VALORACION_DIC",
        "INVENTARIO_ACTIVOS",
        "EVALUACIONES",
        "AUDITORIA_CAMBIOS",
        "RESULTADOS_MAGERIT",
        "RESPUESTAS_CUESTIONARIO"
    ]
    
    for tabla in tablas_limpiar:
        try:
            cursor.execute(f"DELETE FROM [{tabla}]")
            print(f"✅ Limpiada: {tabla} ({cursor.rowcount} registros eliminados)")
        except Exception as e:
            print(f"⚠️ Error en {tabla}: {e}")
    
    conn.commit()
    
    print("\n=== ESTADO FINAL ===")
    for t in tables:
        tabla = t[0]
        cursor.execute(f"SELECT COUNT(*) FROM [{tabla}]")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"{tabla}: {count} registros (catálogo)")
        else:
            print(f"{tabla}: vacía")
    
    conn.close()
    print("\n✅ Base de datos limpiada exitosamente")

if __name__ == "__main__":
    limpiar_base_datos()
