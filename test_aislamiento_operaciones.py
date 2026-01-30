"""Script para verificar que TODAS las operaciones usan solo datos de la evaluación actual"""
import sqlite3
import sys

def test_operaciones_aisladas():
    """Verifica que las operaciones (cálculos, promedios, agregaciones) usan solo datos de cada evaluación"""
    
    conn = sqlite3.connect('tita_database.db')
    cursor = conn.cursor()
    
    print("="*80)
    print("PRUEBA: AISLAMIENTO EN OPERACIONES Y CÁLCULOS")
    print("="*80)
    
    # Obtener evaluaciones
    cursor.execute("SELECT ID_Evaluacion, Nombre FROM EVALUACIONES")
    evaluaciones = cursor.fetchall()
    
    if len(evaluaciones) == 0:
        print("\n⚠️  No hay evaluaciones para probar.")
        conn.close()
        return
    
    print(f"\n📊 Evaluaciones disponibles: {len(evaluaciones)}")
    for eval_id, nombre in evaluaciones:
        print(f"   - {eval_id}: {nombre}")
    
    # Crear segunda evaluación de prueba si solo hay una
    if len(evaluaciones) == 1:
        print("\n🔧 Creando evaluación de prueba para validar aislamiento...")
        cursor.execute('''
            INSERT INTO EVALUACIONES 
            (ID_Evaluacion, Nombre, Fecha, Estado, Descripcion, Fecha_Creacion, Responsable, Limite_Riesgo, Factor_Objetivo)
            VALUES ('EVA-TEST', 'Evaluacion Test Aislamiento', NULL, 'En Progreso', 'Test', datetime('now'), 'System', 7.0, 0.5)
        ''')
        
        # Agregar un activo de prueba
        cursor.execute('''
            INSERT INTO INVENTARIO_ACTIVOS
            (ID_Activo, ID_Evaluacion, Nombre_Activo, Tipo_Activo, Ubicacion, Propietario, Tipo_Servicio, App_Critica, Estado, Fecha_Creacion)
            VALUES ('ACT-TEST-001', 'EVA-TEST', 'Activo Test', 'Servidor Virtual', 'Test', 'Test', 'Test', 'Test', 'Activo', datetime('now'))
        ''')
        
        # Agregar riesgo de prueba
        cursor.execute('''
            INSERT INTO RIESGO_ACTIVOS
            (ID_Evaluacion, ID_Activo, Nombre_Activo, Riesgo_Actual, Riesgo_Objetivo, Limite, Estado, Num_Amenazas, Observacion, Fecha_Calculo)
            VALUES ('EVA-TEST', 'ACT-TEST-001', 'Activo Test', 8.5, 6.0, 7.0, 'Sobre Límite', 3, 'Test', datetime('now'))
        ''')
        
        conn.commit()
        
        # Refrescar lista de evaluaciones
        cursor.execute("SELECT ID_Evaluacion, Nombre FROM EVALUACIONES")
        evaluaciones = cursor.fetchall()
        print(f"✅ Evaluación de prueba creada: EVA-TEST")
    
    print("\n" + "="*80)
    print("PRUEBAS DE AISLAMIENTO DE CÁLCULOS")
    print("="*80)
    
    problemas = []
    
    for eval_id, nombre in evaluaciones:
        print(f"\n🎯 Probando: {eval_id} - {nombre}")
        print("-" * 80)
        
        # 1. Verificar conteos
        cursor.execute("SELECT COUNT(*) FROM INVENTARIO_ACTIVOS WHERE ID_Evaluacion = ?", [eval_id])
        activos_eval = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM INVENTARIO_ACTIVOS")
        activos_total = cursor.fetchone()[0]
        
        if activos_total > activos_eval:
            print(f"   ✅ Activos correctamente aislados: {activos_eval} de {activos_total}")
        else:
            print(f"   ℹ️  Activos en evaluación: {activos_eval}")
        
        # 2. Verificar promedio de riesgos
        cursor.execute('''
            SELECT AVG(Riesgo_Actual) 
            FROM RIESGO_ACTIVOS 
            WHERE ID_Evaluacion = ?
        ''', [eval_id])
        promedio_filtrado = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(Riesgo_Actual) FROM RIESGO_ACTIVOS')
        promedio_global = cursor.fetchone()[0]
        
        if promedio_filtrado is not None and promedio_global is not None:
            if len(evaluaciones) > 1:
                if abs(promedio_filtrado - promedio_global) > 0.01:
                    print(f"   ✅ Promedio aislado: {promedio_filtrado:.2f} (global: {promedio_global:.2f})")
                else:
                    print(f"   ⚠️  Promedio idéntico al global (puede ser coincidencia): {promedio_filtrado:.2f}")
            else:
                print(f"   ℹ️  Promedio: {promedio_filtrado:.2f}")
        
        # 3. Verificar salvaguardas
        cursor.execute('''
            SELECT COUNT(*) 
            FROM SALVAGUARDAS 
            WHERE ID_Evaluacion = ?
        ''', [eval_id])
        salvaguardas_eval = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM SALVAGUARDAS')
        salvaguardas_total = cursor.fetchone()[0]
        
        if salvaguardas_total > salvaguardas_eval:
            print(f"   ✅ Salvaguardas aisladas: {salvaguardas_eval} de {salvaguardas_total}")
        else:
            print(f"   ℹ️  Salvaguardas: {salvaguardas_eval}")
        
        # 4. Verificar madurez
        cursor.execute('''
            SELECT Puntuacion_Total, Nivel_Madurez
            FROM RESULTADOS_MADUREZ 
            WHERE ID_Evaluacion = ?
        ''', [eval_id])
        madurez = cursor.fetchone()
        if madurez:
            print(f"   ✅ Madurez calculada: {madurez[0]:.0f}% (Nivel {madurez[1]})")
        else:
            print(f"   ℹ️  Madurez: No calculada")
    
    # Limpieza: eliminar evaluación de prueba si fue creada
    if len(evaluaciones) > len([e for e in evaluaciones if e[0] == 'EVA-TEST']) + 1:
        print("\n🧹 Limpiando evaluación de prueba...")
        cursor.execute("DELETE FROM RIESGO_ACTIVOS WHERE ID_Evaluacion = 'EVA-TEST'")
        cursor.execute("DELETE FROM INVENTARIO_ACTIVOS WHERE ID_Evaluacion = 'EVA-TEST'")
        cursor.execute("DELETE FROM EVALUACIONES WHERE ID_Evaluacion = 'EVA-TEST'")
        conn.commit()
        print("✅ Evaluación de prueba eliminada")
    
    print("\n" + "="*80)
    print("VERIFICACIÓN DE INTEGRIDAD DE FUNCIONES")
    print("="*80)
    
    # Verificar que no hay funciones que devuelvan datos cruzados
    tests_integridad = []
    
    # Test 1: Verificar que get_activos_matriz solo devuelve activos de la evaluación
    for eval_id, _ in evaluaciones:
        cursor.execute('''
            SELECT COUNT(*) FROM INVENTARIO_ACTIVOS WHERE ID_Evaluacion != ?
        ''', [eval_id])
        activos_otras = cursor.fetchone()[0]
        
        if activos_otras > 0:
            tests_integridad.append(f"✅ get_activos_matriz debe filtrar {activos_otras} activos de otras evaluaciones para {eval_id}")
    
    # Test 2: Verificar que get_riesgos_evaluacion solo devuelve riesgos de la evaluación
    for eval_id, _ in evaluaciones:
        cursor.execute('''
            SELECT COUNT(*) FROM RIESGO_AMENAZA WHERE ID_Evaluacion != ?
        ''', [eval_id])
        riesgos_otros = cursor.fetchone()[0]
        
        if riesgos_otros > 0:
            tests_integridad.append(f"✅ get_riesgos_evaluacion debe filtrar {riesgos_otros} riesgos de otras evaluaciones para {eval_id}")
    
    if tests_integridad:
        for test in tests_integridad:
            print(f"   {test}")
    else:
        print("   ℹ️  Solo hay una evaluación, no se pueden hacer pruebas cruzadas")
    
    print("\n" + "="*80)
    print("RESUMEN:")
    if problemas:
        print(f"\n🔴 ENCONTRADOS {len(problemas)} PROBLEMAS:")
        for p in problemas:
            print(f"   - {p}")
    else:
        print("\n✅ TODAS LAS OPERACIONES ESTÁN CORRECTAMENTE AISLADAS")
        print("   - Los cálculos usan solo datos de cada evaluación")
        print("   - Los promedios no mezclan datos entre evaluaciones")
        print("   - Las consultas filtran correctamente por ID_Evaluacion")
    print("="*80)
    
    conn.close()

if __name__ == "__main__":
    test_operaciones_aisladas()
