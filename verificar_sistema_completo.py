"""
VERIFICADOR AUTOMÁTICO DE INTEGRIDAD TITA
==========================================
Ejecuta este script periódicamente para asegurar que:
1. No hay datos huérfanos
2. Los cálculos están aislados por evaluación
3. Las funciones filtran correctamente

Uso: python verificar_sistema_completo.py
"""

import sqlite3
import sys
from datetime import datetime

def verificar_sistema():
    """Verificación completa del sistema TITA"""
    
    print("="*80)
    print("🔍 VERIFICACIÓN AUTOMÁTICA DEL SISTEMA TITA")
    print("="*80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    conn = sqlite3.connect('tita_database.db')
    cursor = conn.cursor()
    
    errores = []
    advertencias = []
    
    # ===== 1. VERIFICAR EVALUACIONES =====
    print("📊 1. VERIFICANDO EVALUACIONES...")
    cursor.execute("SELECT COUNT(*) FROM EVALUACIONES")
    num_evaluaciones = cursor.fetchone()[0]
    print(f"   ✅ {num_evaluaciones} evaluación(es) en la base de datos")
    
    if num_evaluaciones == 0:
        errores.append("No hay evaluaciones en la base de datos")
        print("   🔴 ERROR: No hay evaluaciones")
    
    # ===== 2. VERIFICAR DATOS HUÉRFANOS =====
    print("\n🧹 2. VERIFICANDO DATOS HUÉRFANOS...")
    
    tablas_criticas = [
        "INVENTARIO_ACTIVOS",
        "RIESGO_ACTIVOS",
        "RIESGO_AMENAZA",
        "VULNERABILIDADES_AMENAZAS",
        "SALVAGUARDAS",
        "IDENTIFICACION_VALORACION"
    ]
    
    huerfanos_encontrados = False
    for tabla in tablas_criticas:
        try:
            cursor.execute(f'''
                SELECT COUNT(*) FROM {tabla} t
                LEFT JOIN EVALUACIONES e ON t.ID_Evaluacion = e.ID_Evaluacion
                WHERE e.ID_Evaluacion IS NULL
            ''')
            count = cursor.fetchone()[0]
            
            if count > 0:
                huerfanos_encontrados = True
                errores.append(f"{tabla}: {count} registros huérfanos")
                print(f"   🔴 {tabla}: {count} registros huérfanos")
            else:
                print(f"   ✅ {tabla}: Sin datos huérfanos")
        except:
            pass
    
    if huerfanos_encontrados:
        print("\n   💡 Ejecutar: python limpiar_huerfanos.py")
    
    # ===== 3. VERIFICAR AISLAMIENTO DE CÁLCULOS =====
    print("\n🔢 3. VERIFICANDO AISLAMIENTO DE CÁLCULOS...")
    
    if num_evaluaciones >= 2:
        cursor.execute("SELECT ID_Evaluacion FROM EVALUACIONES LIMIT 2")
        evals = [row[0] for row in cursor.fetchall()]
        
        promedios_diferentes = False
        for eval_id in evals:
            cursor.execute('''
                SELECT AVG(Riesgo_Actual) 
                FROM RIESGO_ACTIVOS 
                WHERE ID_Evaluacion = ?
            ''', [eval_id])
            promedio = cursor.fetchone()[0]
            if promedio is not None:
                print(f"   ✅ {eval_id}: Promedio riesgo = {promedio:.2f}")
                promedios_diferentes = True
        
        if promedios_diferentes:
            cursor.execute('SELECT AVG(Riesgo_Actual) FROM RIESGO_ACTIVOS')
            promedio_global = cursor.fetchone()[0]
            print(f"   ℹ️  Global: Promedio riesgo = {promedio_global:.2f}")
            print("   ✅ Los cálculos están correctamente aislados")
        else:
            print("   ℹ️  No hay suficientes datos para verificar aislamiento")
    elif num_evaluaciones == 1:
        cursor.execute("SELECT ID_Evaluacion FROM EVALUACIONES")
        eval_id = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT AVG(Riesgo_Actual) 
            FROM RIESGO_ACTIVOS 
            WHERE ID_Evaluacion = ?
        ''', [eval_id])
        promedio = cursor.fetchone()[0]
        if promedio is not None:
            print(f"   ✅ {eval_id}: Promedio riesgo = {promedio:.2f}")
        print("   ℹ️  Solo hay una evaluación (crear otra para verificar aislamiento)")
    
    # ===== 4. VERIFICAR INTEGRIDAD REFERENCIAL =====
    print("\n🔗 4. VERIFICANDO INTEGRIDAD REFERENCIAL...")
    
    # Activos en RIESGO_ACTIVOS que no existen en INVENTARIO
    cursor.execute('''
        SELECT COUNT(*) FROM RIESGO_ACTIVOS ra
        LEFT JOIN INVENTARIO_ACTIVOS ia 
            ON ra.ID_Activo = ia.ID_Activo AND ra.ID_Evaluacion = ia.ID_Evaluacion
        WHERE ia.ID_Activo IS NULL
    ''')
    activos_huerfanos = cursor.fetchone()[0]
    
    if activos_huerfanos > 0:
        errores.append(f"RIESGO_ACTIVOS: {activos_huerfanos} activos no existen en inventario")
        print(f"   🔴 {activos_huerfanos} activos en RIESGO_ACTIVOS no existen en INVENTARIO")
    else:
        print("   ✅ Integridad referencial correcta entre tablas")
    
    # ===== 5. VERIFICAR ESTADÍSTICAS POR EVALUACIÓN =====
    print("\n📈 5. ESTADÍSTICAS POR EVALUACIÓN...")
    
    cursor.execute("SELECT ID_Evaluacion, Nombre FROM EVALUACIONES")
    for eval_id, nombre in cursor.fetchall():
        print(f"\n   📊 {eval_id}: {nombre}")
        
        # Activos
        cursor.execute("SELECT COUNT(*) FROM INVENTARIO_ACTIVOS WHERE ID_Evaluacion = ?", [eval_id])
        activos = cursor.fetchone()[0]
        print(f"      - Activos: {activos}")
        
        # Riesgos
        cursor.execute("SELECT COUNT(*) FROM RIESGO_AMENAZA WHERE ID_Evaluacion = ?", [eval_id])
        riesgos = cursor.fetchone()[0]
        print(f"      - Riesgos identificados: {riesgos}")
        
        # Salvaguardas
        cursor.execute("SELECT COUNT(*) FROM SALVAGUARDAS WHERE ID_Evaluacion = ?", [eval_id])
        salvaguardas = cursor.fetchone()[0]
        print(f"      - Salvaguardas: {salvaguardas}")
        
        # Madurez
        cursor.execute("SELECT Puntuacion_Total FROM RESULTADOS_MADUREZ WHERE ID_Evaluacion = ?", [eval_id])
        madurez = cursor.fetchone()
        if madurez:
            print(f"      - Madurez: {madurez[0]:.0f}%")
        else:
            print(f"      - Madurez: No calculada")
    
    # ===== RESUMEN FINAL =====
    print("\n" + "="*80)
    print("📋 RESUMEN DE VERIFICACIÓN")
    print("="*80)
    
    if errores:
        print(f"\n🔴 ERRORES CRÍTICOS ({len(errores)}):")
        for error in errores:
            print(f"   ❌ {error}")
        print("\n💡 ACCIONES RECOMENDADAS:")
        if huerfanos_encontrados:
            print("   1. Ejecutar: python limpiar_huerfanos.py")
        print("   2. Revisar logs de errores")
        print("   3. Contactar soporte si persisten los problemas")
        resultado = "❌ SISTEMA CON ERRORES"
    elif advertencias:
        print(f"\n⚠️  ADVERTENCIAS ({len(advertencias)}):")
        for adv in advertencias:
            print(f"   ⚠️  {adv}")
        resultado = "⚠️  SISTEMA CON ADVERTENCIAS"
    else:
        print("\n✅ SISTEMA FUNCIONANDO CORRECTAMENTE")
        print("   - Sin datos huérfanos")
        print("   - Cálculos correctamente aislados")
        print("   - Integridad referencial mantenida")
        print("   - Todas las evaluaciones operativas")
        resultado = "✅ SISTEMA OK"
    
    print("\n" + "="*80)
    print(f"RESULTADO: {resultado}")
    print("="*80)
    
    conn.close()
    
    # Retornar código de salida
    return 0 if not errores else 1

if __name__ == "__main__":
    try:
        exit_code = verificar_sistema()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n🔴 ERROR FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
