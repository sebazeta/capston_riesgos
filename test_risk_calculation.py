"""
Script de validación del cálculo de riesgos TITA según MAGERIT v3.

Valida 3 escenarios:
1. PEOR CASO: Sin controles, máxima exposición → CRÍTICO esperado
2. INTERMEDIO: Algunos controles, impacto alto → ALTO/MEDIO esperado  
3. CONTROLADO: Controles implementados → BAJO esperado

Autor: Auditoría TITA
Fecha: 2026-01-26
"""

import pandas as pd
import sys
sys.path.insert(0, 'c:/capston_riesgos')

from services.magerit_engine import (
    calcular_impacto_desde_respuestas,
    calcular_riesgo_inherente,
    get_nivel_riesgo,
    PREGUNTAS_IMPACTO_DIRECTO,
    PREGUNTAS_CONTROL_INVERTIDO
)

def create_test_responses(scenario: str) -> pd.DataFrame:
    """
    Crea respuestas de prueba para los diferentes escenarios.
    
    Para preguntas en PREGUNTAS_IMPACTO_DIRECTO:
        - Valor 4 = Crítico/Expuesto/Frecuente = impacto alto
        - Valor 1 = Bajo/No expuesto/Nunca = impacto bajo
    
    Para preguntas en PREGUNTAS_CONTROL_INVERTIDO:
        - Valor 1 = No/Sin control = impacto alto (se invierte a 4)
        - Valor 4 = Sí completo = impacto bajo (se invierte a 1)
    """
    
    # Preguntas base del cuestionario Servidor Físico
    preguntas = [
        # Bloque A - Criticidad (IMPACTO_DIRECTO: 4=crítico)
        {"ID_Pregunta": "PF-A-001", "Dimension": "D", "Peso": 5},  # Disponibilidad crítica
        {"ID_Pregunta": "PF-A-002", "Dimension": "I", "Peso": 5},  # Integridad crítica
        {"ID_Pregunta": "PF-A-003", "Dimension": "C", "Peso": 5},  # Confidencialidad crítica
        {"ID_Pregunta": "PF-A-004", "Dimension": "D", "Peso": 4},  # Impacto económico
        {"ID_Pregunta": "PF-A-005", "Dimension": "D", "Peso": 4},  # Impacto reputacional
        
        # Bloque B - RTO/RPO (IMPACTO_DIRECTO: 4=>24h=peor)
        {"ID_Pregunta": "PF-B-001", "Dimension": "D", "Peso": 5},  # RTO
        {"ID_Pregunta": "PF-B-002", "Dimension": "D", "Peso": 5},  # RPO
        
        # Bloque B - Procedimientos (CONTROL_INVERTIDO: 1=No→impacto 4)
        {"ID_Pregunta": "PF-B-003", "Dimension": "D", "Peso": 4},  # Procedimiento DRP
        {"ID_Pregunta": "PF-B-004", "Dimension": "D", "Peso": 4},  # Procedimiento backup
        
        # Bloque C - Controles (CONTROL_INVERTIDO: 1=No→impacto 4)
        {"ID_Pregunta": "PF-C-001", "Dimension": "D", "Peso": 4},  # Control de acceso
        {"ID_Pregunta": "PF-C-002", "Dimension": "I", "Peso": 4},  # Monitoreo
        {"ID_Pregunta": "PF-C-003", "Dimension": "D", "Peso": 3},  # Redundancia
        {"ID_Pregunta": "PF-C-004", "Dimension": "C", "Peso": 4},  # Cifrado
        {"ID_Pregunta": "PF-C-005", "Dimension": "D", "Peso": 3},  # Mantenimiento
        
        # Bloque D - Ciberseguridad (CONTROL_INVERTIDO: 1=No→impacto 4)
        {"ID_Pregunta": "PF-D-001", "Dimension": "C", "Peso": 5},  # Antimalware
        {"ID_Pregunta": "PF-D-002", "Dimension": "C", "Peso": 5},  # Firewall
        {"ID_Pregunta": "PF-D-003", "Dimension": "I", "Peso": 4},  # Actualizaciones
        {"ID_Pregunta": "PF-D-004", "Dimension": "I", "Peso": 3},  # Logs
        
        # Bloque E - Exposición (IMPACTO_DIRECTO: 4=expuesto/frecuente/urgente)
        {"ID_Pregunta": "PF-E-001", "Dimension": "D", "Peso": 5},  # Exposición internet
        {"ID_Pregunta": "PF-E-002", "Dimension": "D", "Peso": 4},  # Historial incidentes
        {"ID_Pregunta": "PF-E-003", "Dimension": "D", "Peso": 3},  # Riesgo aceptable
    ]
    
    if scenario == "PEOR_CASO":
        # TODAS las respuestas en el peor valor
        for p in preguntas:
            if p["ID_Pregunta"] in PREGUNTAS_IMPACTO_DIRECTO:
                p["Valor_Numerico"] = 4  # Crítico/Expuesto/Frecuente
            else:  # CONTROL_INVERTIDO
                p["Valor_Numerico"] = 1  # No/Sin control → se invertirá a 4
                
    elif scenario == "INTERMEDIO":
        # Mezcla: Alto impacto pero ALGUNOS controles
        for p in preguntas:
            if p["ID_Pregunta"] in PREGUNTAS_IMPACTO_DIRECTO:
                p["Valor_Numerico"] = 3  # Alto pero no crítico
            else:  # CONTROL_INVERTIDO
                p["Valor_Numerico"] = 2  # Control parcial → se invertirá a 3
                
    elif scenario == "CONTROLADO":
        # Bajo impacto y buenos controles
        for p in preguntas:
            if p["ID_Pregunta"] in PREGUNTAS_IMPACTO_DIRECTO:
                p["Valor_Numerico"] = 1  # Bajo impacto
            else:  # CONTROL_INVERTIDO
                p["Valor_Numerico"] = 4  # Sí completo → se invertirá a 1
    
    return pd.DataFrame(preguntas)


def test_scenario(name: str, expected_min_level: str, expected_max_level: str = None):
    """Ejecuta un escenario de prueba y valida el resultado."""
    print(f"\n{'='*60}")
    print(f"ESCENARIO: {name}")
    print(f"{'='*60}")
    
    responses = create_test_responses(name)
    
    # 1. Calcular impacto
    impacto = calcular_impacto_desde_respuestas(responses)
    print(f"\n📊 IMPACTO DIC:")
    print(f"   D (Disponibilidad): {impacto.disponibilidad}/5 - {impacto.justificacion_d}")
    print(f"   I (Integridad):     {impacto.integridad}/5 - {impacto.justificacion_i}")
    print(f"   C (Confidencialidad): {impacto.confidencialidad}/5 - {impacto.justificacion_c}")
    
    impacto_max = max(impacto.disponibilidad, impacto.integridad, impacto.confidencialidad)
    print(f"   → Impacto máximo: {impacto_max}/5")
    
    # 2. Calcular probabilidad (simulada según exposición)
    # En el escenario real, viene del servicio Ollama
    if name == "PEOR_CASO":
        probabilidad = 5  # Máxima exposición + incidentes frecuentes
    elif name == "INTERMEDIO":
        probabilidad = 3  # Media
    else:
        probabilidad = 2  # Baja
    
    print(f"\n📈 PROBABILIDAD: {probabilidad}/5")
    
    # 3. Calcular riesgo inherente
    riesgo_inherente, _, _ = calcular_riesgo_inherente(impacto, probabilidad)
    nivel_riesgo = get_nivel_riesgo(riesgo_inherente)
    
    print(f"\n⚠️  RIESGO INHERENTE:")
    print(f"   Cálculo: {probabilidad} × {impacto_max} = {riesgo_inherente}")
    print(f"   Nivel: {nivel_riesgo}")
    
    # 4. Validar resultado
    niveles_validos = [expected_min_level]
    if expected_max_level:
        niveles_validos.append(expected_max_level)
    
    if nivel_riesgo in niveles_validos:
        print(f"\n✅ RESULTADO CORRECTO: {nivel_riesgo} está en niveles esperados {niveles_validos}")
        return True
    else:
        print(f"\n❌ ERROR: Se esperaba {niveles_validos}, se obtuvo {nivel_riesgo}")
        return False


def main():
    print("\n" + "="*70)
    print("   VALIDACIÓN DE CÁLCULO DE RIESGOS TITA - MAGERIT v3")
    print("="*70)
    
    print("\n📋 Umbrales de riesgo MAGERIT v3:")
    print("   CRÍTICO: ≥20 (riesgo extremo)")
    print("   ALTO:    ≥12 (riesgo significativo)")
    print("   MEDIO:   ≥6  (riesgo moderado)")
    print("   BAJO:    ≥3  (riesgo menor)")
    print("   MUY BAJO: <3 (riesgo mínimo)")
    
    results = []
    
    # Escenario 1: Peor caso → CRÍTICO esperado
    results.append(test_scenario("PEOR_CASO", "CRÍTICO"))
    
    # Escenario 2: Intermedio → ALTO o MEDIO esperado
    results.append(test_scenario("INTERMEDIO", "ALTO", "MEDIO"))
    
    # Escenario 3: Controlado → BAJO o MUY BAJO esperado
    results.append(test_scenario("CONTROLADO", "BAJO", "MUY BAJO"))
    
    print("\n" + "="*70)
    print("   RESUMEN DE VALIDACIÓN")
    print("="*70)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"\n✅ TODAS LAS PRUEBAS PASARON ({passed}/{total})")
        print("   El sistema de cálculo de riesgos funciona correctamente.")
    else:
        print(f"\n❌ ALGUNAS PRUEBAS FALLARON ({passed}/{total})")
        print("   Revisar los escenarios marcados con ❌")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
