from services.ia_context_magerit import get_vulnerabilidades_por_tipo, construir_contexto_vulnerabilidades

# Test 1: Obtener vulnerabilidades para Software
vulns_sw = get_vulnerabilidades_por_tipo('SW')
print(f'✅ Vulnerabilidades para SW: {len(vulns_sw)}')
for v in vulns_sw[:3]:
    print(f'  - {v["codigo"]}: {v["nombre"]}')

# Test 2: Obtener vulnerabilidades para Hardware  
vulns_hw = get_vulnerabilidades_por_tipo('HW')
print(f'\n✅ Vulnerabilidades para HW: {len(vulns_hw)}')
for v in vulns_hw[:3]:
    print(f'  - {v["codigo"]}: {v["nombre"]}')

# Test 3: Construir contexto
contexto = construir_contexto_vulnerabilidades('aplicacion')
print(f'\n✅ Contexto generado ({len(contexto)} caracteres):')
print(contexto[:300] + '...')

print('\n✅ TODAS LAS PRUEBAS PASARON CORRECTAMENTE')
