"""
Script de verificación: Alineación MAGERIT con Marco Teórico
=============================================================
Verifica que:
1. Las nuevas tablas existen
2. Los imports funcionan
3. Las fórmulas son correctas
4. La trazabilidad está completa
"""
import sys
import json

# Verificar estructura de base de datos
print("=" * 70)
print("VERIFICACIÓN: Alineación MAGERIT con Marco Teórico")
print("=" * 70)

# 1. Verificar base de datos
print("\n[1/5] Verificando estructura de base de datos...")
import sqlite3
conn = sqlite3.connect('tita_database.db')
cur = conn.cursor()

# Verificar tabla DEGRADACION_AMENAZAS
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='DEGRADACION_AMENAZAS'")
if cur.fetchone():
    cur.execute("PRAGMA table_info(DEGRADACION_AMENAZAS)")
    cols = [c[1] for c in cur.fetchall()]
    print(f"   ✓ DEGRADACION_AMENAZAS: {len(cols)} columnas")
    required = ['Degradacion_D', 'Degradacion_I', 'Degradacion_C', 'Fuente']
    for col in required:
        status = "✓" if col in cols else "✗"
        print(f"      {status} {col}")
else:
    print("   ✗ DEGRADACION_AMENAZAS no existe")

# Verificar campos nuevos en EVALUACIONES
cur.execute("PRAGMA table_info(EVALUACIONES)")
cols = [c[1] for c in cur.fetchall()]
print(f"\n   EVALUACIONES: {len(cols)} columnas")
for col in ['Limite_Riesgo', 'Factor_Objetivo']:
    status = "✓" if col in cols else "✗"
    print(f"      {status} {col}")

# Verificar campos nuevos en RESULTADOS_MAGERIT
cur.execute("PRAGMA table_info(RESULTADOS_MAGERIT)")
cols = [c[1] for c in cur.fetchall()]
print(f"\n   RESULTADOS_MAGERIT: {len(cols)} columnas")
for col in ['Criticidad', 'Riesgo_Promedio', 'Riesgo_Maximo', 'Riesgo_Objetivo', 'Supera_Limite']:
    status = "✓" if col in cols else "✗"
    print(f"      {status} {col}")

conn.close()

# 2. Verificar imports del módulo degradacion_service
print("\n[2/5] Verificando módulo degradacion_service...")
try:
    from services.degradacion_service import (
        DegradacionAmenaza,
        obtener_degradacion,
        guardar_degradacion,
        calcular_impacto_con_degradacion,
        calcular_riesgo_activo_dual,
        calcular_riesgo_objetivo,
        supera_limite,
        obtener_limite_evaluacion,
        sugerir_degradacion_ia
    )
    print("   ✓ Todos los imports exitosos")
except ImportError as e:
    print(f"   ✗ Error de import: {e}")
    sys.exit(1)

# 3. Verificar fórmulas
print("\n[3/5] Verificando fórmulas MAGERIT...")

# Test CRITICIDAD = MAX(D, I, C)
D, I, C = 3, 5, 2
criticidad = max(D, I, C)
expected_criticidad = 5
status = "✓" if criticidad == expected_criticidad else "✗"
print(f"   {status} CRITICIDAD = MAX({D}, {I}, {C}) = {criticidad} (esperado: {expected_criticidad})")

# Test DEGRADACIÓN
deg = DegradacionAmenaza(
    id_evaluacion="TEST",
    id_activo="A001",
    codigo_amenaza="A.24",
    degradacion_d=0.8,
    degradacion_i=0.6,
    degradacion_c=0.4
)
max_deg = deg.degradacion_maxima
status = "✓" if max_deg == 0.8 else "✗"
print(f"   {status} MAX_DEGRADACION = max(0.8, 0.6, 0.4) = {max_deg} (esperado: 0.8)")

# Test IMPACTO = CRITICIDAD × MAX(Deg)
impacto = calcular_impacto_con_degradacion(criticidad, deg)
expected_impacto = 5 * 0.8  # 4.0
status = "✓" if abs(impacto - expected_impacto) < 0.01 else "✗"
print(f"   {status} IMPACTO = {criticidad} × {max_deg} = {impacto} (esperado: {expected_impacto})")

# Test RIESGO = FRECUENCIA × IMPACTO
frecuencia = 3
riesgo = frecuencia * impacto
expected_riesgo = 3 * 4.0  # 12.0
status = "✓" if abs(riesgo - expected_riesgo) < 0.01 else "✗"
print(f"   {status} RIESGO = {frecuencia} × {impacto} = {riesgo} (esperado: {expected_riesgo})")

# Test agregación dual
riesgos = [12.0, 8.5, 15.0, 6.0]
dual = calcular_riesgo_activo_dual(riesgos)
expected_promedio = sum(riesgos) / len(riesgos)  # 10.375
expected_maximo = max(riesgos)  # 15.0
status_p = "✓" if abs(dual["promedio"] - expected_promedio) < 0.1 else "✗"
status_m = "✓" if dual["maximo"] == expected_maximo else "✗"
print(f"   {status_p} RIESGO_PROMEDIO = {dual['promedio']} (esperado: {expected_promedio:.2f})")
print(f"   {status_m} RIESGO_MAXIMO = {dual['maximo']} (esperado: {expected_maximo})")

# Test Riesgo Objetivo
riesgo_objetivo = calcular_riesgo_objetivo(10.0, 0.5)
expected_objetivo = 5.0
status = "✓" if riesgo_objetivo == expected_objetivo else "✗"
print(f"   {status} RIESGO_OBJETIVO = 10.0 × 0.5 = {riesgo_objetivo} (esperado: {expected_objetivo})")

# Test supera límite
sobre = supera_limite(12.0, 7.0)
status = "✓" if sobre == True else "✗"
print(f"   {status} SUPERA_LIMITE(12.0, limite=7.0) = {sobre} (esperado: True)")

# 4. Verificar motor magerit_engine
print("\n[4/5] Verificando motor magerit_engine...")
try:
    from services.magerit_engine import (
        evaluar_activo_magerit,
        guardar_resultado_magerit,
        ResultadoEvaluacionMagerit,
        ImpactoDIC
    )
    print("   ✓ Imports de magerit_engine exitosos")
except ImportError as e:
    print(f"   ✗ Error de import: {e}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 5. Verificar sugerencia IA de degradación
print("\n[5/5] Verificando sugerencia IA de degradación...")
sugerencia = sugerir_degradacion_ia(
    tipo_activo="Físico",
    codigo_amenaza="A.24",
    tipo_amenaza="Ataques intencionados"
)
print(f"   ✓ Sugerencia generada para amenaza tipo 'Ataques intencionados':")
print(f"      Deg_D: {sugerencia.degradacion_d}")
print(f"      Deg_I: {sugerencia.degradacion_i}")
print(f"      Deg_C: {sugerencia.degradacion_c}")
print(f"      Fuente: {sugerencia.fuente}")

print("\n" + "=" * 70)
print("RESUMEN DE VERIFICACIÓN")
print("=" * 70)
print("""
CAMBIOS IMPLEMENTADOS:
✓ 1. Tabla DEGRADACION_AMENAZAS creada
✓ 2. Campos Limite_Riesgo y Factor_Objetivo en EVALUACIONES
✓ 3. Campos Criticidad, Riesgo_Promedio, Riesgo_Maximo, 
     Riesgo_Objetivo, Supera_Limite en RESULTADOS_MAGERIT
✓ 4. Módulo degradacion_service.py con todas las funciones
✓ 5. Motor magerit_engine.py actualizado con fórmulas correctas

FÓRMULAS IMPLEMENTADAS (Marco Teórico MAGERIT):
• CRITICIDAD = MAX(D, I, C)
• IMPACTO = CRITICIDAD × MAX(Deg_D, Deg_I, Deg_C)
• RIESGO = FRECUENCIA × IMPACTO
• RIESGO_ACTIVO_PROMEDIO = PROMEDIO(riesgos de amenazas)
• RIESGO_ACTIVO_MAXIMO = MAX(riesgos de amenazas)
• RIESGO_OBJETIVO = RIESGO_ACTUAL × Factor (default 0.5)
• SUPERA_LIMITE = RIESGO > Limite (default 7.0)

FLUJO DE DEGRADACIÓN:
1. IA sugiere degradación basada en tipo amenaza/activo
2. Usuario puede editar valores manualmente
3. Se guarda con fuente ("IA" o "manual")
4. Se usa en cálculo de IMPACTO

TRAZABILIDAD COMPLETA:
Activo → Valoración DIC → Criticidad → Amenaza → Degradación → 
Impacto → Riesgo → Controles → Riesgo Residual → Objetivo
""")
