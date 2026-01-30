"""
Script de migración para agregar columna Cod_Vulnerabilidad
a la tabla VULNERABILIDADES_AMENAZAS
"""
import sqlite3
import os

# Ruta absoluta a la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), "tita_database.db")

def migrar_agregar_cod_vulnerabilidad():
    """Agrega la columna Cod_Vulnerabilidad si no existe"""
    try:
        if not os.path.exists(DB_PATH):
            print(f"⚠️ Base de datos no encontrada: {DB_PATH}")
            return False
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='VULNERABILIDADES_AMENAZAS'")
        if not cursor.fetchone():
            print("⚠️ La tabla VULNERABILIDADES_AMENAZAS no existe aún")
            conn.close()
            return False
        
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(VULNERABILIDADES_AMENAZAS)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "Cod_Vulnerabilidad" not in columns:
            print("⏳ Agregando columna Cod_Vulnerabilidad...")
            cursor.execute('''
                ALTER TABLE VULNERABILIDADES_AMENAZAS 
                ADD COLUMN Cod_Vulnerabilidad TEXT
            ''')
            conn.commit()
            print("✅ Columna Cod_Vulnerabilidad agregada exitosamente")
        else:
            print("ℹ️  La columna Cod_Vulnerabilidad ya existe")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en migración: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"Base de datos: {DB_PATH}")
    migrar_agregar_cod_vulnerabilidad()
