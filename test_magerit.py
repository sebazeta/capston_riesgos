#!/usr/bin/env python
"""Script de prueba para el motor MAGERIT"""
import pandas as pd
from services.ollama_magerit_service import (
    generar_evaluacion_heuristica, 
    get_catalogo_amenazas, 
    get_catalogo_controles
)
from services.magerit_engine import (
    evaluar_activo_magerit, 
    guardar_resultado_magerit,
    get_resumen_evaluacion
)
from services.database_service import read_table

print("=" * 50)
print("TEST MOTOR MAGERIT")
print("=" * 50)

# 1. Cargar catálogos
print("\n1. Cargando catálogos...")
cat_amenazas = get_catalogo_amenazas()
cat_controles = get_catalogo_controles()
print(f"   Amenazas: {len(cat_amenazas)}")
print(f"   Controles: {len(cat_controles)}")

# 2. Obtener activo
print("\n2. Obteniendo activo...")
activos = read_table('INVENTARIO_ACTIVOS')
if activos.empty:
    print("   ERROR: No hay activos")
    exit(1)
    
activo = activos.iloc[0]
print(f"   ID: {activo['ID_Activo']}")
print(f"   Nombre: {activo['Nombre_Activo']}")
print(f"   Tipo: {activo['Tipo_Activo']}")

# 3. Generar evaluación heurística
print("\n3. Generando evaluación heurística...")
resultado_heur = generar_evaluacion_heuristica(
    activo, 
    pd.DataFrame(), 
    cat_amenazas, 
    cat_controles
)
print(f"   Amenazas: {len(resultado_heur['amenazas'])}")
print(f"   Probabilidad: {resultado_heur['probabilidad']}")
for am in resultado_heur['amenazas']:
    print(f"   - {am['codigo']}: {am['dimension']}")

# 4. Evaluar con motor MAGERIT
print("\n4. Ejecutando motor MAGERIT...")
resultado_magerit = evaluar_activo_magerit(
    'EVA-001',
    activo['ID_Activo'],
    resultado_heur['amenazas'],
    resultado_heur['probabilidad'],
    resultado_heur['observaciones'],
    'heuristic-test'
)
print(f"   Impacto D: {resultado_magerit.impacto.disponibilidad}")
print(f"   Impacto I: {resultado_magerit.impacto.integridad}")
print(f"   Impacto C: {resultado_magerit.impacto.confidencialidad}")
print(f"   Riesgo Inherente: {resultado_magerit.riesgo_inherente_global}")
print(f"   Riesgo Residual: {resultado_magerit.riesgo_residual_global}")
print(f"   Nivel: {resultado_magerit.nivel_riesgo_inherente_global}")

# 5. Guardar resultado
print("\n5. Guardando resultado...")
guardado = guardar_resultado_magerit(resultado_magerit)
print(f"   Guardado: {guardado}")

# 6. Verificar en BD
print("\n6. Verificando en BD...")
resumen = get_resumen_evaluacion('EVA-001')
print(f"   Filas en resumen: {len(resumen)}")
if not resumen.empty:
    print(resumen[['id_activo', 'nombre_activo', 'riesgo_inherente_global']].to_string())

print("\n" + "=" * 50)
print("TEST COMPLETADO")
print("=" * 50)
