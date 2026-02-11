"""
Script para obtener datos de la evaluación para documentación
"""
from services.database_service import get_connection
import pandas as pd

with get_connection() as conn:
    print("=" * 60)
    print("DATOS PARA DOCUMENTACIÓN DEL PROYECTO TITA")
    print("=" * 60)
    
    # Evaluaciones
    print("\n=== 1. EVALUACIONES ===")
    evals = pd.read_sql_query('SELECT * FROM EVALUACIONES', conn)
    for _, e in evals.iterrows():
        print(f"  ID: {e['ID_Evaluacion']}")
        print(f"  Nombre: {e['Nombre']}")
        print(f"  Estado: {e['Estado']}")
        print(f"  Fecha: {e['Fecha_Creacion']}")
    
    # Activos
    print("\n=== 2. ACTIVOS ===")
    activos = pd.read_sql_query('SELECT * FROM INVENTARIO_ACTIVOS', conn)
    print(f"  Total activos: {len(activos)}")
    for _, a in activos.iterrows():
        nombre = a.get('Nombre_Activo', a.get('Nombre', 'N/A'))
        tipo = a.get('Tipo_Activo', a.get('Tipo', 'N/A'))
        print(f"    - {nombre} ({tipo})")
    
    # Valoraciones DIC
    print("\n=== 3. VALORACIONES DIC ===")
    valoraciones = pd.read_sql_query('SELECT * FROM IDENTIFICACION_VALORACION', conn)
    print(f"  Total valoraciones: {len(valoraciones)}")
    
    # Riesgos
    print("\n=== 4. RIESGOS ===")
    riesgos = pd.read_sql_query('SELECT * FROM RIESGO_AMENAZA', conn)
    print(f"  Total riesgos: {len(riesgos)}")
    if not riesgos.empty:
        print(f"  Riesgo promedio: {riesgos['Riesgo'].mean():.2f}")
        print(f"  Riesgo máximo: {riesgos['Riesgo'].max():.2f}")
        print(f"  Riesgo mínimo: {riesgos['Riesgo'].min():.2f}")
        
        altos = len(riesgos[riesgos['Riesgo'] >= 6])
        medios = len(riesgos[(riesgos['Riesgo'] >= 4) & (riesgos['Riesgo'] < 6)])
        bajos = len(riesgos[riesgos['Riesgo'] < 4])
        print(f"  Distribución:")
        print(f"    - ALTOS (>=6): {altos}")
        print(f"    - MEDIOS (4-5.99): {medios}")
        print(f"    - BAJOS (<4): {bajos}")
    
    # Salvaguardas
    print("\n=== 5. SALVAGUARDAS ===")
    salvs = pd.read_sql_query('SELECT * FROM SALVAGUARDAS', conn)
    print(f"  Total salvaguardas: {len(salvs)}")
    if not salvs.empty and 'Estado' in salvs.columns:
        impl = len(salvs[salvs['Estado'].str.contains('Implementada', case=False, na=False)])
        print(f"  Implementadas: {impl}")
        print(f"  Pendientes: {len(salvs) - impl}")
    
    # Madurez
    print("\n=== 6. MADUREZ ===")
    madurez = pd.read_sql_query('SELECT * FROM RESULTADOS_MADUREZ', conn)
    if not madurez.empty:
        m = madurez.iloc[0]
        print(f"  Puntuación: {m.get('Puntuacion_Total', 0):.1f}/100")
        print(f"  Nivel: {m.get('Nivel_Madurez', 0)} - {m.get('Nombre_Nivel', 'N/A')}")
        print(f"  Pct Controles Implementados: {m.get('Pct_Controles_Implementados', 0):.1f}%")
        print(f"  Pct Controles Medidos: {m.get('Pct_Controles_Medidos', 0):.1f}%")
        print(f"  Pct Riesgos Mitigados: {m.get('Pct_Riesgos_Mitigados', 0):.1f}%")
    else:
        print("  No hay datos de madurez")
    
    # Historial de reevaluaciones
    print("\n=== 7. HISTORIAL REEVALUACIONES ===")
    try:
        historial = pd.read_sql_query('SELECT * FROM HISTORIAL_REEVALUACIONES ORDER BY Fecha_Reevaluacion DESC', conn)
        if not historial.empty:
            print(f"  Total reevaluaciones: {len(historial)}")
            for _, h in historial.iterrows():
                print(f"\n  Reevaluación: {h.get('Fecha_Reevaluacion', 'N/A')}")
                print(f"    Riesgo: {h.get('Riesgo_Anterior', 0):.2f} -> {h.get('Riesgo_Nuevo', 0):.2f}")
                print(f"    Madurez: {h.get('Madurez_Anterior', 0):.1f}% -> {h.get('Madurez_Nueva', 0):.1f}%")
                print(f"    Nivel: {h.get('Nivel_Anterior', 0)} -> {h.get('Nivel_Nuevo', 0)} ({h.get('Nombre_Nivel', '')})")
                print(f"    Salvaguardas: {h.get('Salvaguardas_Implementadas', 0)}/{h.get('Total_Salvaguardas', 0)}")
                print(f"    Observaciones: {h.get('Observaciones', '')}")
        else:
            print("  No hay reevaluaciones registradas")
    except Exception as e:
        print(f"  No hay tabla de historial: {e}")
    
    print("\n" + "=" * 60)
