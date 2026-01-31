"""
Script para probar las dos fórmulas de madurez:
- Tab 9: Madurez inherente (sin salvaguardas)
- Tab 10: Madurez con controles (con salvaguardas)
"""
from services.maturity_service import calcular_madurez_evaluacion
from services.matriz_service import get_riesgos_evaluacion, get_salvaguardas_evaluacion, get_activos_matriz

ID_EVALUACION = 'EVA-001'

# Obtener datos reales
activos = get_activos_matriz(ID_EVALUACION)
riesgos = get_riesgos_evaluacion(ID_EVALUACION)
salvaguardas = get_salvaguardas_evaluacion(ID_EVALUACION)

print('='*60)
print('DATOS REALES DE LA EVALUACIÓN')
print('='*60)
print(f'Total activos: {len(activos)}')
print(f'Total riesgos: {len(riesgos)}')
print(f'Total salvaguardas: {len(salvaguardas)}')

if not riesgos.empty:
    riesgos_altos = len(riesgos[riesgos["Riesgo"] >= 6])
    riesgos_medios = len(riesgos[(riesgos["Riesgo"] >= 4) & (riesgos["Riesgo"] < 6)])
    riesgos_bajos = len(riesgos[riesgos["Riesgo"] < 4])
    print(f'\nDistribución de riesgos:')
    print(f'  🔴 ALTO (>=6): {riesgos_altos}')
    print(f'  🟡 MEDIO (4-6): {riesgos_medios}')
    print(f'  🟢 BAJO (<4): {riesgos_bajos}')
    print(f'  Riesgo promedio: {riesgos["Riesgo"].mean():.2f}')
    print(f'  Riesgo máximo: {riesgos["Riesgo"].max():.2f}')

if not salvaguardas.empty and 'Estado' in salvaguardas.columns:
    print(f'\nEstado salvaguardas:')
    print(salvaguardas['Estado'].value_counts().to_string())

# ===== TAB 9: MADUREZ INHERENTE =====
print('\n' + '='*60)
print('TAB 9: MADUREZ INHERENTE (Sin Salvaguardas)')
print('='*60)
resultado_inherente = calcular_madurez_evaluacion(ID_EVALUACION, considerar_salvaguardas=False)
if resultado_inherente:
    print(f'📊 Puntuación: {resultado_inherente.puntuacion_total} puntos')
    print(f'🎯 Nivel: {resultado_inherente.nivel_madurez} - {resultado_inherente.nombre_nivel}')
    print(f'\nComponentes:')
    print(f'  - Distribución Riesgos (60%): {resultado_inherente.pct_controles_medidos}%')
    print(f'  - Severidad Riesgo (40%): {resultado_inherente.pct_riesgos_criticos_mitigados}%')

# ===== TAB 10: MADUREZ CON CONTROLES =====
print('\n' + '='*60)
print('TAB 10: MADUREZ CON CONTROLES (Con Salvaguardas)')
print('='*60)
resultado_controles = calcular_madurez_evaluacion(ID_EVALUACION, considerar_salvaguardas=True)
if resultado_controles:
    print(f'📊 Puntuación: {resultado_controles.puntuacion_total} puntos')
    print(f'🎯 Nivel: {resultado_controles.nivel_madurez} - {resultado_controles.nombre_nivel}')
    print(f'\nComponentes:')
    print(f'  - Riesgos Controlados (40%): {resultado_controles.pct_controles_medidos}%')
    print(f'  - Salvaguardas Impl. (35%): {resultado_controles.pct_controles_implementados}%')
    print(f'  - Riesgo Residual (25%): {resultado_controles.pct_riesgos_criticos_mitigados}%')

# ===== COMPARATIVA =====
print('\n' + '='*60)
print('COMPARATIVA')
print('='*60)
if resultado_inherente and resultado_controles:
    delta = resultado_controles.puntuacion_total - resultado_inherente.puntuacion_total
    print(f'Tab 9 (Inherente):   {resultado_inherente.puntuacion_total:5.1f} pts → Nivel {resultado_inherente.nivel_madurez} ({resultado_inherente.nombre_nivel})')
    print(f'Tab 10 (Con Ctrl):   {resultado_controles.puntuacion_total:5.1f} pts → Nivel {resultado_controles.nivel_madurez} ({resultado_controles.nombre_nivel})')
    print(f'\n{"📈" if delta > 0 else "📉"} Diferencia por salvaguardas: {delta:+.1f} puntos')
    
    if delta > 0:
        print(f'\n✅ Las salvaguardas implementadas ({resultado_controles.controles_implementados}) mejoran la madurez.')
    else:
        print(f'\n⚠️ Las salvaguardas aún no impactan significativamente.')
