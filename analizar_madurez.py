"""
Script para analizar el cálculo de madurez y encontrar el error
"""
from services.maturity_service import calcular_madurez_evaluacion, get_madurez_evaluacion
from services.matriz_service import get_riesgos_evaluacion, get_salvaguardas_evaluacion, get_activos_matriz

ID_EVALUACION = 'EVA-001'

# Obtener datos reales
activos = get_activos_matriz(ID_EVALUACION)
riesgos = get_riesgos_evaluacion(ID_EVALUACION)
salvaguardas = get_salvaguardas_evaluacion(ID_EVALUACION)

print('=== DATOS REALES DE LA EVALUACIÓN ===')
print(f'Total activos: {len(activos)}')
print(f'Total riesgos: {len(riesgos)}')
print(f'Total salvaguardas: {len(salvaguardas)}')

if not riesgos.empty:
    print(f'\nDistribución de riesgos:')
    riesgos_altos = len(riesgos[riesgos["Riesgo"] >= 6])
    riesgos_medios = len(riesgos[(riesgos["Riesgo"] >= 4) & (riesgos["Riesgo"] < 6)])
    riesgos_bajos = len(riesgos[riesgos["Riesgo"] < 4])
    print(f'  Riesgos >= 6 (ALTO): {riesgos_altos}')
    print(f'  Riesgos 4-5.99 (MEDIO): {riesgos_medios}')
    print(f'  Riesgos < 4 (BAJO): {riesgos_bajos}')
    print(f'  Riesgo promedio: {riesgos["Riesgo"].mean():.2f}')
    print(f'  Riesgo máximo: {riesgos["Riesgo"].max():.2f}')

if not salvaguardas.empty:
    print(f'\nEstado salvaguardas:')
    if 'Estado' in salvaguardas.columns:
        print(salvaguardas['Estado'].value_counts())
    else:
        print('  Sin columna Estado - todas pendientes/recomendadas')

# Calcular madurez
print('\n=== CÁLCULO DE MADUREZ ACTUAL ===')
resultado = calcular_madurez_evaluacion(ID_EVALUACION)
if resultado:
    print(f'Puntuación: {resultado.puntuacion_total}')
    print(f'Nivel: {resultado.nivel_madurez} - {resultado.nombre_nivel}')
    print(f'pct_salvaguardas: {resultado.pct_controles_implementados}%')
    print(f'pct_riesgos: {resultado.pct_controles_medidos}%')
    print(f'pct_activos: {resultado.pct_activos_evaluados}%')
    
    # Verificar cálculo manual
    print('\n=== VERIFICACIÓN MANUAL ===')
    total_activos = len(activos)
    salvaguardas_esperadas = total_activos * 3
    riesgos_esperados = total_activos * 5
    
    print(f'Meta salvaguardas: {salvaguardas_esperadas} (3 x {total_activos})')
    print(f'Meta riesgos: {riesgos_esperados} (5 x {total_activos})')
    
    pct_salv = min(100, (len(salvaguardas) / salvaguardas_esperadas * 100)) if salvaguardas_esperadas > 0 else 0
    pct_riesg = min(100, (len(riesgos) / riesgos_esperados * 100)) if riesgos_esperados > 0 else 0
    pct_activos = 100  # Asumiendo todos evaluados
    
    print(f'\nPorcentajes calculados:')
    print(f'  Salvaguardas: {len(salvaguardas)}/{salvaguardas_esperadas} = {pct_salv:.1f}%')
    print(f'  Riesgos: {len(riesgos)}/{riesgos_esperados} = {pct_riesg:.1f}%')
    print(f'  Activos: {pct_activos:.1f}%')
    
    puntuacion = (pct_salv * 0.40) + (pct_riesg * 0.30) + (pct_activos * 0.30)
    print(f'\nPuntuación manual: ({pct_salv:.1f}*0.4) + ({pct_riesg:.1f}*0.3) + ({pct_activos:.1f}*0.3) = {puntuacion:.1f}')
else:
    print('No se pudo calcular')

print('\n=== PROBLEMA IDENTIFICADO ===')
print('La fórmula actual mide COMPLETITUD de la evaluación, NO madurez real.')
print('Un sistema con muchos riesgos ALTOS y salvaguardas NO implementadas')
print('NO debería tener madurez 100%. La madurez debe medir:')
print('  1. % de riesgos CONTROLADOS (bajo vs alto)')
print('  2. % de salvaguardas IMPLEMENTADAS vs solo recomendadas')
print('  3. Nivel de riesgo residual promedio')
