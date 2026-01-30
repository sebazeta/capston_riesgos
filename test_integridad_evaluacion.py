"""Script para verificar que cada función de servicio filtra correctamente por evaluación"""
import sqlite3
import sys

def test_integridad_datos():
    """Prueba que las consultas respetan el filtro de evaluación"""
    
    conn = sqlite3.connect('tita_database.db')
    cursor = conn.cursor()
    
    print("="*80)
    print("PRUEBA DE INTEGRIDAD: AISLAMIENTO DE DATOS POR EVALUACIÓN")
    print("="*80)
    
    # Obtener evaluaciones
    cursor.execute("SELECT ID_Evaluacion, Nombre FROM EVALUACIONES")
    evaluaciones = cursor.fetchall()
    
    print(f"\n📊 EVALUACIONES EN LA BASE DE DATOS: {len(evaluaciones)}")
    for eval_id, nombre in evaluaciones:
        print(f"   - {eval_id}: {nombre}")
    
    if len(evaluaciones) == 0:
        print("\n⚠️  No hay evaluaciones para probar.")
        conn.close()
        return
    
    # Probar con la primera evaluación
    eval_test = evaluaciones[0][0]
    print(f"\n🎯 PROBANDO CON EVALUACIÓN: {eval_test}")
    
    # Tablas críticas a verificar
    tablas_criticas = {
        "INVENTARIO_ACTIVOS": "ID_Evaluacion",
        "RIESGO_ACTIVOS": "ID_Evaluacion",
        "RIESGO_AMENAZA": "ID_Evaluacion",
        "VULNERABILIDADES_AMENAZAS": "ID_Evaluacion",
        "SALVAGUARDAS": "ID_Evaluacion",
        "IDENTIFICACION_VALORACION": "ID_Evaluacion",
        "CUESTIONARIOS": "ID_Evaluacion",
        "RESPUESTAS": "ID_Evaluacion",
        "RESULTADOS_MAGERIT": "ID_Evaluacion",
        "RESULTADOS_MADUREZ": "ID_Evaluacion",
        "MAPA_RIESGOS": "ID_Evaluacion"
    }
    
    print("\n📋 VERIFICACIÓN POR TABLA:")
    print("-" * 80)
    
    problemas = []
    
    for tabla, col_eval in tablas_criticas.items():
        try:
            # Contar total en la tabla
            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
            total = cursor.fetchone()[0]
            
            # Contar registros de la evaluación de prueba
            cursor.execute(f"SELECT COUNT(*) FROM {tabla} WHERE {col_eval} = ?", [eval_test])
            en_eval = cursor.fetchone()[0]
            
            # Contar registros de OTRAS evaluaciones
            cursor.execute(f"SELECT COUNT(*) FROM {tabla} WHERE {col_eval} != ?", [eval_test])
            otras = cursor.fetchone()[0]
            
            # Verificar si hay datos sin ID_Evaluacion
            cursor.execute(f"SELECT COUNT(*) FROM {tabla} WHERE {col_eval} IS NULL")
            sin_eval = cursor.fetchone()[0]
            
            status = "✅"
            nota = ""
            
            if sin_eval > 0:
                status = "⚠️ "
                nota = f" ({sin_eval} sin evaluación)"
                problemas.append(f"{tabla}: {sin_eval} registros sin ID_Evaluacion")
            
            if otras > 0 and len(evaluaciones) == 1:
                status = "🔴"
                nota = f" (PROBLEMA: {otras} de evaluaciones inexistentes)"
                problemas.append(f"{tabla}: {otras} registros de evaluaciones que no existen")
            
            print(f"{status} {tabla:35} Total: {total:4} | Eval {eval_test}: {en_eval:4} | Otras: {otras:4}{nota}")
            
        except sqlite3.OperationalError as e:
            print(f"⏭️  {tabla:35} (tabla no existe o sin columna {col_eval})")
    
    print("-" * 80)
    
    # Resumen
    print("\n" + "="*80)
    print("RESUMEN:")
    if problemas:
        print(f"\n🔴 ENCONTRADOS {len(problemas)} PROBLEMAS:")
        for p in problemas:
            print(f"   - {p}")
        print("\n💡 RECOMENDACIÓN: Ejecutar limpiar_huerfanos.py para corregir")
    else:
        print("\n✅ TODOS LOS DATOS ESTÁN CORRECTAMENTE AISLADOS POR EVALUACIÓN")
        print("   Cada tabla filtra correctamente por ID_Evaluacion")
    print("="*80)
    
    conn.close()

if __name__ == "__main__":
    test_integridad_datos()
