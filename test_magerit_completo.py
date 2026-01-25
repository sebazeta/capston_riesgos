"""
Test script para verificar toda la funcionalidad MAGERIT + Madurez
=================================================================
Este script prueba:
1. Cálculo de impacto DIC desde respuestas
2. Identificación de controles existentes
3. Cálculo de riesgo inherente y residual
4. Recomendación de controles ISO 27002
5. Cálculo de nivel de madurez
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.database_service import read_table, get_connection
from services.magerit_engine import (
    calcular_impacto_desde_respuestas,
    identificar_controles_existentes,
    evaluar_activo_magerit,
    guardar_resultado_magerit,
    get_resultado_magerit,
    get_nivel_riesgo
)
from services.maturity_service import (
    calcular_madurez_evaluacion,
    guardar_madurez,
    get_controles_existentes_detallados,
    analizar_controles_desde_respuestas
)
from services.ollama_magerit_service import (
    analizar_activo_con_ia,
    generar_evaluacion_heuristica,
    get_catalogo_amenazas,
    get_catalogo_controles
)

def print_separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def test_catalogos():
    """Verifica que los catálogos estén cargados"""
    print_separator("1. Verificando Catálogos")
    
    amenazas = get_catalogo_amenazas()
    controles = get_catalogo_controles()
    
    print(f"✅ Catálogo de Amenazas: {len(amenazas)} amenazas cargadas")
    print(f"✅ Catálogo de Controles ISO 27002: {len(controles)} controles cargados")
    
    # Mostrar algunos ejemplos
    if amenazas:
        ejemplo = list(amenazas.items())[0]
        print(f"   Ejemplo amenaza: {ejemplo[0]} - {ejemplo[1]['amenaza']}")
    
    if controles:
        ejemplo = list(controles.items())[0]
        print(f"   Ejemplo control: {ejemplo[0]} - {ejemplo[1]['nombre']}")
    
    return len(amenazas) > 0 and len(controles) > 0

def test_respuestas_existentes():
    """Busca respuestas existentes para hacer pruebas"""
    print_separator("2. Buscando Respuestas Existentes")
    
    respuestas = read_table("RESPUESTAS")
    
    if respuestas.empty:
        print("⚠️ No hay respuestas en la base de datos")
        print("   Para probar completamente, cree activos y responda cuestionarios")
        return None, None
    
    # Obtener primera evaluación con respuestas
    eval_id = respuestas.iloc[0]["ID_Evaluacion"]
    activo_id = respuestas.iloc[0]["ID_Activo"]
    
    respuestas_filtradas = respuestas[
        (respuestas["ID_Evaluacion"] == eval_id) &
        (respuestas["ID_Activo"] == activo_id)
    ]
    
    print(f"✅ Encontradas {len(respuestas_filtradas)} respuestas")
    print(f"   Evaluación: {eval_id}")
    print(f"   Activo: {activo_id}")
    
    return eval_id, activo_id

def test_impacto_dic(respuestas):
    """Prueba el cálculo de impacto DIC"""
    print_separator("3. Calculando Impacto DIC")
    
    if respuestas.empty:
        print("⚠️ Sin respuestas para calcular impacto")
        return None
    
    impacto = calcular_impacto_desde_respuestas(respuestas)
    
    print(f"✅ Impacto Calculado:")
    print(f"   Disponibilidad (D): {impacto.disponibilidad}/5 - {impacto.justificacion_d}")
    print(f"   Integridad (I):     {impacto.integridad}/5 - {impacto.justificacion_i}")
    print(f"   Confidencialidad (C): {impacto.confidencialidad}/5 - {impacto.justificacion_c}")
    print(f"   Impacto Global: {impacto.impacto_global}/5")
    
    return impacto

def test_controles_existentes(respuestas):
    """Prueba la identificación de controles existentes"""
    print_separator("4. Identificando Controles Existentes")
    
    if respuestas.empty:
        print("⚠️ Sin respuestas para identificar controles")
        return None
    
    controles, efectividad, detalle = identificar_controles_existentes(respuestas)
    
    print(f"✅ Controles Identificados: {len(controles)}")
    print(f"   Efectividad promedio: {efectividad*100:.1f}%")
    print(f"   Implementados: {len(detalle['controles_implementados'])}")
    print(f"   Parciales: {len(detalle['controles_parciales'])}")
    print(f"   No implementados: {len(detalle['controles_no_implementados'])}")
    
    if controles:
        print(f"\n   Controles implementados/parciales:")
        for ctrl in controles[:10]:
            print(f"   - {ctrl}")
    
    return controles, efectividad, detalle

def test_evaluacion_heuristica(eval_id, activo_id):
    """Prueba la evaluación heurística (fallback)"""
    print_separator("5. Evaluación Heurística (sin IA)")
    
    activos = read_table("INVENTARIO_ACTIVOS")
    activo = activos[activos["ID_Activo"] == activo_id]
    
    if activo.empty:
        print("⚠️ Activo no encontrado")
        return None
    
    activo = activo.iloc[0]
    respuestas = read_table("RESPUESTAS")
    respuestas_activo = respuestas[
        (respuestas["ID_Evaluacion"] == eval_id) &
        (respuestas["ID_Activo"] == activo_id)
    ]
    
    catalogo_amenazas = get_catalogo_amenazas()
    catalogo_controles = get_catalogo_controles()
    
    resultado = generar_evaluacion_heuristica(
        activo, respuestas_activo, catalogo_amenazas, catalogo_controles
    )
    
    print(f"✅ Evaluación Heurística Generada:")
    print(f"   Probabilidad: {resultado.get('probabilidad', 0)}/5")
    print(f"   Amenazas identificadas: {len(resultado.get('amenazas', []))}")
    
    for am in resultado.get("amenazas", []):
        print(f"   - {am['codigo']}: Dimensión {am['dimension']}")
        for ctrl in am.get("controles_iso_recomendados", [])[:2]:
            print(f"     → Control: {ctrl['control']} ({ctrl['prioridad']})")
    
    return resultado

def test_motor_magerit(eval_id, activo_id, amenazas_ia, probabilidad):
    """Prueba el motor MAGERIT completo"""
    print_separator("6. Motor MAGERIT Completo")
    
    try:
        resultado = evaluar_activo_magerit(
            eval_id, activo_id, amenazas_ia, probabilidad,
            "Evaluación de prueba", "heuristic-test"
        )
        
        print(f"✅ Evaluación MAGERIT Completada:")
        print(f"   Activo: {resultado.nombre_activo}")
        print(f"   Impacto DIC: D={resultado.impacto.disponibilidad} I={resultado.impacto.integridad} C={resultado.impacto.confidencialidad}")
        print(f"   Amenazas procesadas: {len(resultado.amenazas)}")
        print(f"   Riesgo Inherente: {resultado.riesgo_inherente_global} ({resultado.nivel_riesgo_inherente_global})")
        print(f"   Riesgo Residual: {resultado.riesgo_residual_global} ({resultado.nivel_riesgo_residual_global})")
        print(f"   Controles existentes: {len(resultado.controles_existentes_global)}")
        print(f"   Controles recomendados: {len(resultado.controles_recomendados_global)}")
        
        # Mostrar detalle de amenazas
        for am in resultado.amenazas[:3]:
            print(f"\n   Amenaza: {am.codigo} - {am.amenaza[:50]}...")
            print(f"   - Dimensión: {am.dimension_afectada}, P={am.probabilidad}, I={am.impacto}")
            print(f"   - R.Inherente: {am.riesgo_inherente} ({am.nivel_riesgo})")
            print(f"   - R.Residual: {am.riesgo_residual} ({am.nivel_riesgo_residual})")
            print(f"   - Tratamiento: {am.tratamiento}")
            if am.controles_recomendados:
                print(f"   - Controles: {[c['codigo'] for c in am.controles_recomendados[:3]]}")
        
        # Guardar resultado
        guardado = guardar_resultado_magerit(resultado)
        print(f"\n   Guardado en BD: {'✅ Sí' if guardado else '❌ No'}")
        
        return resultado
    
    except Exception as e:
        print(f"❌ Error en evaluación MAGERIT: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_madurez(eval_id):
    """Prueba el cálculo de nivel de madurez"""
    print_separator("7. Nivel de Madurez de Ciberseguridad")
    
    resultado = calcular_madurez_evaluacion(eval_id)
    
    if not resultado:
        print("⚠️ No se pudo calcular la madurez (¿hay activos y respuestas?)")
        return None
    
    print(f"✅ Nivel de Madurez Calculado:")
    print(f"   Nivel: {resultado.nivel_madurez} - {resultado.nombre_nivel}")
    print(f"   Puntuación: {resultado.puntuacion_total:.1f}%")
    print(f"\n   Dominios ISO 27002:")
    print(f"   - Organizacional (5.x): {resultado.dominio_organizacional:.1f}%")
    print(f"   - Personas (6.x): {resultado.dominio_personas:.1f}%")
    print(f"   - Físico (7.x): {resultado.dominio_fisico:.1f}%")
    print(f"   - Tecnológico (8.x): {resultado.dominio_tecnologico:.1f}%")
    print(f"\n   Métricas:")
    print(f"   - % Controles implementados: {resultado.pct_controles_implementados:.1f}%")
    print(f"   - % Controles medidos: {resultado.pct_controles_medidos:.1f}%")
    print(f"   - % Riesgos críticos mitigados: {resultado.pct_riesgos_criticos_mitigados:.1f}%")
    print(f"   - % Activos evaluados: {resultado.pct_activos_evaluados:.1f}%")
    print(f"\n   Controles: {resultado.controles_implementados} impl. + {resultado.controles_parciales} parciales")
    
    # Guardar
    guardado = guardar_madurez(resultado)
    print(f"   Guardado en BD: {'✅ Sí' if guardado else '❌ No'}")
    
    return resultado

def test_controles_detallados(eval_id, activo_id):
    """Prueba la obtención de controles detallados"""
    print_separator("8. Controles Existentes Detallados")
    
    resultado = get_controles_existentes_detallados(eval_id, activo_id)
    
    if not resultado.get("controles"):
        print("⚠️ No se encontraron controles (¿hay respuestas?)")
        return None
    
    resumen = resultado.get("resumen", {})
    print(f"✅ Controles Analizados:")
    print(f"   Implementados: {resumen.get('implementados', 0)}")
    print(f"   Parciales: {resumen.get('parciales', 0)}")
    print(f"   No implementados: {resumen.get('no_implementados', 0)}")
    
    print(f"\n   Top 10 controles identificados:")
    for ctrl in resultado.get("controles", [])[:10]:
        efectividad = ctrl.get("efectividad", 0)
        icono = "✅" if efectividad >= 0.66 else "⚠️" if efectividad > 0 else "❌"
        print(f"   {icono} {ctrl['codigo']}: {ctrl['nombre'][:40]} ({ctrl['nivel']})")
    
    print(f"\n   Por dominio:")
    for dominio, controles in resultado.get("por_dominio", {}).items():
        if controles:
            print(f"   - {dominio}: {len(controles)} controles")
    
    return resultado

def run_all_tests():
    """Ejecuta todas las pruebas"""
    print("\n" + "="*60)
    print("  TEST COMPLETO: MAGERIT + MADUREZ + CONTROLES")
    print("="*60)
    
    # 1. Verificar catálogos
    if not test_catalogos():
        print("\n❌ FALLO: Catálogos no cargados. Ejecute seed_catalogos_magerit.py")
        return False
    
    # 2. Buscar respuestas existentes
    eval_id, activo_id = test_respuestas_existentes()
    
    if not eval_id:
        print("\n⚠️ No hay datos para pruebas completas.")
        print("   Cree una evaluación, activos y responda cuestionarios primero.")
        return False
    
    # Obtener respuestas
    respuestas = read_table("RESPUESTAS")
    respuestas_activo = respuestas[
        (respuestas["ID_Evaluacion"] == eval_id) &
        (respuestas["ID_Activo"] == activo_id)
    ]
    
    # 3. Probar impacto DIC
    impacto = test_impacto_dic(respuestas_activo)
    
    # 4. Probar controles existentes
    test_controles_existentes(respuestas_activo)
    
    # 5. Probar evaluación heurística
    eval_heuristica = test_evaluacion_heuristica(eval_id, activo_id)
    
    if eval_heuristica:
        # 6. Probar motor MAGERIT
        test_motor_magerit(
            eval_id, activo_id,
            eval_heuristica.get("amenazas", []),
            eval_heuristica.get("probabilidad", 3)
        )
    
    # 7. Probar madurez
    test_madurez(eval_id)
    
    # 8. Probar controles detallados
    test_controles_detallados(eval_id, activo_id)
    
    print_separator("RESUMEN DE PRUEBAS")
    print("✅ Todas las pruebas completadas")
    print("\nPara ver los resultados en la interfaz:")
    print("1. Ejecute: streamlit run app_final.py")
    print("2. Vaya al tab 📈 Dashboard Riesgos")
    print("3. Vaya al tab 🎯 Madurez")
    
    return True

if __name__ == "__main__":
    run_all_tests()
