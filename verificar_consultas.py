"""Script para verificar que todas las consultas filtran por ID_Evaluacion"""
import os
import re

def verificar_consultas_sql():
    """Verifica que las consultas SQL críticas filtren por ID_Evaluacion"""
    
    services_dir = "services"
    problemas = []
    
    # Tablas que SIEMPRE deben filtrar por ID_Evaluacion
    tablas_criticas = [
        "INVENTARIO_ACTIVOS",
        "RIESGO_ACTIVOS",
        "RIESGO_AMENAZA",
        "VULNERABILIDADES_AMENAZAS",
        "SALVAGUARDAS",
        "IDENTIFICACION_VALORACION",
        "CUESTIONARIOS",
        "RESPUESTAS",
        "RESULTADOS_MAGERIT",
        "RESULTADOS_MADUREZ",
        "RESULTADOS_CONCENTRACION",
        "MAPA_RIESGOS",
        "DEGRADACION_AMENAZAS",
        "RIESGO_HEREDADO"
    ]
    
    # Patrones de consultas peligrosas (SELECT sin WHERE)
    patron_select = re.compile(r'SELECT\s+.*?\s+FROM\s+(' + '|'.join(tablas_criticas) + r')(?!\s+WHERE)', re.IGNORECASE)
    patron_read_table = re.compile(r'read_table\(["\'](' + '|'.join(tablas_criticas) + r')["\']\)', re.IGNORECASE)
    
    print("="*80)
    print("VERIFICACIÓN DE CONSULTAS SQL - FILTRADO POR EVALUACIÓN")
    print("="*80)
    
    for filename in os.listdir(services_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(services_dir, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                contenido = f.read()
                lineas = contenido.split('\n')
                
                # Buscar consultas problemáticas
                for i, linea in enumerate(lineas, 1):
                    # Ignorar comentarios
                    if linea.strip().startswith('#'):
                        continue
                    
                    # Buscar SELECT sin WHERE
                    match_select = patron_select.search(linea)
                    if match_select:
                        tabla = match_select.group(1)
                        # Verificar contexto (puede tener WHERE en líneas siguientes)
                        contexto = '\n'.join(lineas[max(0,i-1):min(len(lineas),i+5)])
                        if 'WHERE' not in contexto and 'ID_Evaluacion' not in contexto:
                            problemas.append({
                                'archivo': filename,
                                'linea': i,
                                'tabla': tabla,
                                'codigo': linea.strip(),
                                'tipo': 'SELECT sin WHERE'
                            })
                    
                    # Buscar read_table sin filtro posterior
                    match_read = patron_read_table.search(linea)
                    if match_read:
                        tabla = match_read.group(1)
                        # Verificar si en líneas siguientes se filtra por ID_Evaluacion
                        contexto = '\n'.join(lineas[i:min(len(lineas),i+10)])
                        if 'ID_Evaluacion' not in contexto and 'id_evaluacion' not in contexto:
                            problemas.append({
                                'archivo': filename,
                                'linea': i,
                                'tabla': tabla,
                                'codigo': linea.strip(),
                                'tipo': 'read_table sin filtro visible'
                            })
    
    if problemas:
        print(f"\n⚠️  ENCONTRADOS {len(problemas)} POSIBLES PROBLEMAS:\n")
        
        for p in problemas:
            print(f"📁 {p['archivo']}:{p['linea']}")
            print(f"   Tabla: {p['tabla']}")
            print(f"   Tipo: {p['tipo']}")
            print(f"   Código: {p['codigo'][:100]}")
            print()
    else:
        print("\n✅ No se encontraron problemas evidentes en las consultas.")
        print("   Nota: Esta verificación es básica. Revise manualmente para confirmar.")
    
    print("="*80)
    print("RESUMEN:")
    print(f"  - Tablas críticas revisadas: {len(tablas_criticas)}")
    print(f"  - Archivos analizados: {len([f for f in os.listdir(services_dir) if f.endswith('.py')])}")
    print(f"  - Problemas potenciales: {len(problemas)}")
    print("="*80)

if __name__ == "__main__":
    verificar_consultas_sql()
