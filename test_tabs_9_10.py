"""
Script de prueba para verificar errores en Tabs 9 y 10
"""
import sys
import traceback

# Intentar importar todo lo necesario
try:
    print("=== VERIFICANDO IMPORTS ===")
    import pandas as pd
    print("✅ pandas")
    import streamlit as st
    print("✅ streamlit")
    import plotly.graph_objects as go
    print("✅ plotly.graph_objects")
    import time
    print("✅ time")
    
    print("\n=== VERIFICANDO SERVICIOS ===")
    from services.maturity_service import calcular_madurez_evaluacion, get_madurez_evaluacion, guardar_madurez
    print("✅ maturity_service imports")
    
    from services.matriz_service import get_activos_matriz, get_riesgos_evaluacion, get_salvaguardas_evaluacion
    print("✅ matriz_service imports")
    
    print("\n=== VERIFICANDO FUNCIONES ESPECÍFICAS ===")
    
    # Simular llamada a funciones con una evaluación de prueba
    ID_EVAL = "EVA-001"
    
    try:
        resultado = calcular_madurez_evaluacion(ID_EVAL)
        print(f"✅ calcular_madurez_evaluacion() retornó: {type(resultado)}")
    except Exception as e:
        print(f"❌ calcular_madurez_evaluacion() falló: {e}")
        traceback.print_exc()
    
    try:
        madurez = get_madurez_evaluacion(ID_EVAL)
        print(f"✅ get_madurez_evaluacion() retornó: {type(madurez)}")
    except Exception as e:
        print(f"❌ get_madurez_evaluacion() falló: {e}")
        traceback.print_exc()
    
    try:
        activos = get_activos_matriz(ID_EVAL)
        print(f"✅ get_activos_matriz() retornó: {type(activos)} con {len(activos)} filas")
    except Exception as e:
        print(f"❌ get_activos_matriz() falló: {e}")
        traceback.print_exc()
    
    try:
        riesgos = get_riesgos_evaluacion(ID_EVAL)
        print(f"✅ get_riesgos_evaluacion() retornó: {type(riesgos)} con {len(riesgos)} filas")
    except Exception as e:
        print(f"❌ get_riesgos_evaluacion() falló: {e}")
        traceback.print_exc()
    
    try:
        salvaguardas = get_salvaguardas_evaluacion(ID_EVAL)
        print(f"✅ get_salvaguardas_evaluacion() retornó: {type(salvaguardas)} con {len(salvaguardas)} filas")
    except Exception as e:
        print(f"❌ get_salvaguardas_evaluacion() falló: {e}")
        traceback.print_exc()
    
    print("\n=== TODAS LAS VERIFICACIONES COMPLETADAS ===")
    
except Exception as e:
    print(f"\n❌ ERROR FATAL: {e}")
    traceback.print_exc()
    sys.exit(1)
