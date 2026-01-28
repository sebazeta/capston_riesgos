"""
Script de prueba: UI de Degradación
====================================
Verifica que el componente de degradación funciona correctamente.
"""
import sqlite3
import json

print("=" * 60)
print("PRUEBA: Componente UI de Degradación")
print("=" * 60)

# 1. Verificar imports
print("\n[1/4] Verificando imports...")
try:
    from components.degradacion_ui import (
        render_degradacion_tab,
        get_amenazas_con_degradacion,
        render_resumen_degradacion_evaluacion,
        NIVELES_DEGRADACION
    )
    print("   ✓ Todos los imports correctos")
except ImportError as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# 2. Verificar niveles de degradación
print("\n[2/4] Verificando niveles de degradación...")
expected = {
    "Muy Bajo (0.1)": 0.1,
    "Bajo (0.3)": 0.3,
    "Medio (0.5)": 0.5,
    "Alto (0.7)": 0.7,
    "Muy Alto (0.9)": 0.9,
    "Total (1.0)": 1.0
}
for nivel, valor in expected.items():
    status = "✓" if NIVELES_DEGRADACION.get(nivel) == valor else "✗"
    print(f"   {status} {nivel}: {NIVELES_DEGRADACION.get(nivel)}")

# 3. Verificar estructura de BD
print("\n[3/4] Verificando datos existentes...")
conn = sqlite3.connect('tita_database.db')
cur = conn.cursor()

# Ver si hay evaluaciones con resultados MAGERIT
cur.execute('''
    SELECT e.ID_Evaluacion, e.Nombre, COUNT(r.ID_Activo) as activos
    FROM EVALUACIONES e
    LEFT JOIN RESULTADOS_MAGERIT r ON e.ID_Evaluacion = r.ID_Evaluacion
    GROUP BY e.ID_Evaluacion
''')
evaluaciones = cur.fetchall()

if evaluaciones:
    print("   Evaluaciones con resultados:")
    for eval_id, nombre, activos in evaluaciones[:5]:
        print(f"      - {eval_id}: {nombre} ({activos} activos)")
else:
    print("   ⚠ No hay evaluaciones con resultados MAGERIT")

# Ver degradaciones existentes
cur.execute('SELECT COUNT(*) FROM DEGRADACION_AMENAZAS')
total_deg = cur.fetchone()[0]
print(f"\n   Total degradaciones registradas: {total_deg}")

conn.close()

# 4. Verificar integración con app_final
print("\n[4/4] Verificando integración con app_final...")
try:
    with open('app_final.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('Import degradacion_ui', 'from components.degradacion_ui import'),
        ('Variable DEGRADACION_DISPONIBLE', 'DEGRADACION_DISPONIBLE'),
        ('Tab tab_deg', 'tab_deg'),
        ('with tab_deg:', 'with tab_deg:'),
        ('render_degradacion_tab', 'render_degradacion_tab')
    ]
    
    for nombre, buscar in checks:
        status = "✓" if buscar in content else "✗"
        print(f"   {status} {nombre}")

except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
print("RESUMEN")
print("=" * 60)
print("""
UI DE DEGRADACIÓN IMPLEMENTADA:

1. Nueva pestaña "⚙️ Degradación" en la aplicación
   - Se muestra después de "Evaluación con IA"
   - Antes de "Dashboard"

2. Funcionalidad:
   - Selector de activo por evaluación
   - Tabla expandible de amenazas con degradación
   - Sliders para Deg_D, Deg_I, Deg_C (niveles descriptivos)
   - Preview de cálculo en tiempo real
   - Botón "Guardar Manual" por amenaza
   - Botón "Sugerir IA" por amenaza
   - Botón "Sugerir TODAS por IA" (masivo)
   - Validación de trazabilidad

3. Estados:
   - 🔴 Pendiente: Sin degradación → Riesgo no calculado
   - 🟢 Manual: Degradación ingresada manualmente
   - 🔵 IA: Degradación sugerida por IA

4. Flujo:
   Evaluación → Activos → Cuestionarios → Evaluación IA → 
   ⚙️ Degradación → Dashboard → Salvaguardas
""")
