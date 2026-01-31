"""
Script para corregir la indentación del Tab 8 en app_matriz.py
"""

with open('app_matriz.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar la línea con "# ===== VISTA SEGÚN ESTADO ====="
# y corregir la indentación desde ahí

for i, line in enumerate(lines):
    if '# ===== VISTA SEGÚN ESTADO =====' in line and i > 3600:
        print(f"Encontrada línea de estado en: {i+1}")
        
        # Asegurar que las líneas siguientes estén correctamente indentadas
        # Desde esta línea hasta el else:, todo debe estar con 8 espacios de indentación base
        
        # Línea actual: "        # ===== VISTA SEGÚN ESTADO ====="
        if not line.startswith('        '):
            lines[i] = '        ' + line.lstrip()
        
        # Siguiente línea: "        if estado_generacion == "GENERADO":"
        if i+1 < len(lines):
            if 'if estado_generacion == "GENERADO"' in lines[i+1]:
                if not lines[i+1].startswith('        '):
                    lines[i+1] = '        ' + lines[i+1].lstrip()
                print(f"Corregida línea {i+2}: if estado_generacion")
        
        # Buscar todas las líneas hasta encontrar el else:
        j = i + 2
        dentro_del_if = True
        while j < len(lines) and dentro_del_if:
            # Si encontramos el else: al mismo nivel que el if
            if lines[j].strip().startswith('else:') and '# REGENERANDO o PENDIENTE' in lines[j]:
                # Este else debe estar al mismo nivel que el if (8 espacios)
                lines[j] = '        else:  # REGENERANDO o PENDIENTE - Mostrar interfaz de generación\n'
                print(f"Corregida línea {j+1}: else REGENERANDO")
                dentro_del_if = False
                break
            
            # Las líneas dentro del if deben tener 12 espacios mínimo
            if lines[j].strip():  # Si no es línea vacía
                # Contar espacios actuales
                espacios = len(lines[j]) - len(lines[j].lstrip())
                
                # Si tiene menos de 12 espacios y no es un comentario o línea vacía
                if espacios < 12 and lines[j].strip():
                    # Calcular cuántos espacios agregar
                    contenido = lines[j].lstrip()
                    
                    # Determinar indentación correcta basada en el contenido
                    if contenido.startswith('st.') or contenido.startswith('col_') or contenido.startswith('#'):
                        # Elementos de primer nivel dentro del if: 12 espacios
                        lines[j] = '            ' + contenido
                    elif contenido.startswith('with ') or contenido.startswith('if '):
                        # Bloques with/if dentro del if: 12 espacios
                        lines[j] = '            ' + contenido
                    elif '"""' in contenido or contenido.startswith('-'):
                        # Contenido de strings multilínea o listas
                        lines[j] = '            ' + contenido
            
            j += 1
            if j > i + 100:  # Límite de seguridad
                break
        
        break

# Guardar el archivo
with open('app_matriz.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Corrección completada")
