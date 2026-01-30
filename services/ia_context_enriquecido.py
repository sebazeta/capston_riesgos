"""
CONTEXTO ENRIQUECIDO PARA IA - VERSION COMPLETA
===============================================
Carga TODOS los catálogos y conocimiento del proyecto
para alimentar la IA con información completa.
"""

import json
from pathlib import Path
from typing import Dict, List
from services.database_service import read_table

# Directorio de conocimiento
KNOWLEDGE_DIR = Path("c:/capston_riesgos/knowledge_base")

def cargar_catalogo_completo_amenazas() -> Dict:
    """Carga el catálogo completo de amenazas desde JSON"""
    try:
        json_path = KNOWLEDGE_DIR / "amenazas_magerit_completo.json"
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    
    # Fallback: cargar desde base de datos
    amenazas_df = read_table("CATALOGO_AMENAZAS_MAGERIT")
    catalogo = {}
    for _, row in amenazas_df.iterrows():
        catalogo[row['codigo']] = {
            'amenaza': row['amenaza'],
            'tipo': row['tipo_amenaza'],
            'descripcion': row.get('descripcion', ''),
            'dimension': row.get('dimension_afectada', 'D')
        }
    return catalogo


def cargar_catalogo_completo_controles() -> Dict:
    """Carga el catálogo completo de controles ISO 27002 desde JSON"""
    try:
        json_path = KNOWLEDGE_DIR / "controles_iso27002_completo.json"
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    
    # Fallback: cargar desde base de datos
    controles_df = read_table("CATALOGO_CONTROLES_ISO27002")
    catalogo = {}
    for _, row in controles_df.iterrows():
        catalogo[row['codigo']] = {
            'nombre': row['nombre'],
            'categoria': row['categoria'],
            'descripcion': row.get('descripcion', '')
        }
    return catalogo


def construir_contexto_completo_ia() -> str:
    """
    Construye el contexto COMPLETO para la IA con TODA la información disponible.
    Este es el contexto más rico y detallado posible.
    """
    amenazas = cargar_catalogo_completo_amenazas()
    controles = cargar_catalogo_completo_controles()
    
    contexto = """
# SISTEMA TITA - CONTEXTO COMPLETO PARA IA
## Sistema de Análisis de Riesgos de Seguridad de la Información

Eres un experto en seguridad de la información especializado en:
- Metodología MAGERIT v3 (España)
- ISO/IEC 27002:2022 (Controles de seguridad)
- ISO/IEC 27005 (Gestión de riesgos)
- Análisis de Impacto al Negocio (BIA)
- Evaluación de riesgos de TI

---

## CATÁLOGO COMPLETO DE AMENAZAS MAGERIT v3

Tienes acceso al catálogo OFICIAL de 52 amenazas MAGERIT v3:

"""
    
    # Agrupar amenazas por tipo
    amenazas_por_tipo = {}
    for codigo, info in amenazas.items():
        tipo = info.get('tipo', 'Otros')
        if tipo not in amenazas_por_tipo:
            amenazas_por_tipo[tipo] = []
        amenazas_por_tipo[tipo].append((codigo, info))
    
    # Añadir amenazas por categoría
    for tipo, lista_amenazas in sorted(amenazas_por_tipo.items()):
        contexto += f"\n### {tipo} ({len(lista_amenazas)} amenazas)\n\n"
        for codigo, info in sorted(lista_amenazas, key=lambda x: x[0]):
            contexto += f"**{codigo}**: {info['amenaza']}\n"
            if info.get('descripcion'):
                contexto += f"  → {info['descripcion']}\n"
            contexto += f"  → Dimensión: {info.get('dimension', 'D')}\n\n"
    
    contexto += """
---

## CATÁLOGO COMPLETO DE CONTROLES ISO 27002:2022

Tienes acceso al catálogo OFICIAL de 93 controles ISO 27002:2022:

"""
    
    # Agrupar controles por categoría
    controles_por_cat = {}
    for codigo, info in controles.items():
        cat = info.get('categoria', 'Otros')
        if cat not in controles_por_cat:
            controles_por_cat[cat] = []
        controles_por_cat[cat].append((codigo, info))
    
    # Añadir controles por categoría
    for categoria, lista_controles in sorted(controles_por_cat.items()):
        contexto += f"\n### {categoria} ({len(lista_controles)} controles)\n\n"
        for codigo, info in sorted(lista_controles, key=lambda x: x[0]):
            contexto += f"**{codigo}**: {info['nombre']}\n"
            if info.get('descripcion'):
                desc = info['descripcion']
                if len(desc) > 150:
                    desc = desc[:150] + "..."
                contexto += f"  → {desc}\n\n"
    
    contexto += """
---

## MAPEO AMENAZAS → CONTROLES ISO 27002

### Relaciones Clave:

#### Amenazas de Disponibilidad → Controles
- **A.24 (Denegación de Servicio)** → 8.20 (Seguridad de redes), 8.22 (Segmentación), 8.14 (Redundancia)
- **N.1 (Fuego)** → 7.5 (Protección física), 8.14 (Redundancia), 5.29 (Continuidad)
- **I.5 (Avería de origen físico)** → 7.11 (Servicios de apoyo), 8.14 (Alta disponibilidad)

#### Amenazas de Confidencialidad → Controles
- **E.1 (Errores de usuario)** → 6.3 (Concientización), 8.9 (Gestión configuración)
- **E.2 (Errores de administrador)** → 5.18 (Privilegios), 8.2 (Derechos acceso), 6.3 (Capacitación)
- **A.15 (Alteración de información)** → 8.24 (Criptografía), 8.16 (Monitoreo), 5.12 (Clasificación)

#### Amenazas de Integridad → Controles
- **A.5 (Suplantación de identidad)** → 5.15 (Control acceso), 5.16 (Gestión identidades), 8.5 (Autenticación)
- **A.6 (Abuso de privilegios)** → 5.18 (Privilegios), 8.2 (Derechos), 8.16 (Monitoreo)
- **A.8 (Software malicioso)** → 8.7 (Antimalware), 8.8 (Vulnerabilidades), 8.23 (Filtrado web)

#### Amenazas Técnicas → Controles
- **A.22 (Manipulación de equipo)** → 7.7 (Trabajo seguro), 7.4 (Monitoreo físico)
- **A.29 (Indisponibilidad del personal)** → 6.6 (Acuerdos confidencialidad), 5.7 (Inteligencia amenazas)
- **E.20 (Fuga de información)** → 5.12 (Clasificación), 8.11 (Enmascaramiento datos), 8.10 (Borrado)

---

## VULNERABILIDADES POR TIPO DE ACTIVO

### Software (SW) - 10 vulnerabilidades
- SW-V01: Sin autenticación multifactor (MFA)
- SW-V02: Configuración por defecto
- SW-V03: Sin actualizaciones de seguridad
- SW-V04: Sin cifrado de datos en tránsito
- SW-V05: Sin cifrado de datos en reposo
- SW-V06: Falta de logging y auditoría
- SW-V07: Inyección SQL/XSS sin mitigar
- SW-V08: Sin gestión de sesiones segura
- SW-V09: Exposición de información sensible
- SW-V10: Sin validación de entrada

### Hardware (HW) - 7 vulnerabilidades
- HW-V01: Sin redundancia de hardware
- HW-V02: Firmware desactualizado
- HW-V03: Acceso físico sin control
- HW-V04: Sin sistema de respaldo energético (UPS)
- HW-V05: Sin monitoreo de temperatura/humedad
- HW-V06: Componentes fuera de garantía/EOL
- HW-V07: Sin protección contra sobretensión

### Comunicaciones (COM) - 8 vulnerabilidades
- COM-V01: Tráfico sin cifrar
- COM-V02: Red sin segmentación (VLANs)
- COM-V03: Sin firewall o IDS/IPS
- COM-V04: Sin protección DDoS
- COM-V05: Falta de redundancia geográfica
- COM-V06: Ancho de banda insuficiente
- COM-V07: Sin VPN para acceso remoto
- COM-V08: WiFi sin WPA3 o 802.1X

### Datos (D) - 8 vulnerabilidades
- D-V01: Sin backups automatizados
- D-V02: Backups no probados
- D-V03: Sin cifrado de backups
- D-V04: RPO/RTO no definidos
- D-V05: Sin control de versiones
- D-V06: Sin clasificación de datos
- D-V07: Sin DLP (Data Loss Prevention)
- D-V08: Sin anonimización/pseudonimización

### Servicios (S) - 8 vulnerabilidades
- S-V01: Sin SLA definido
- S-V02: Sin monitoreo 24/7
- S-V03: Dependencia de un solo proveedor
- S-V04: Sin plan de continuidad (DRP)
- S-V05: Sin redundancia geográfica
- S-V06: Sin balanceo de carga
- S-V07: Tiempo de respuesta no garantizado
- S-V08: Sin plan de escalamiento

### Personal (PS) - 8 vulnerabilidades
- PS-V01: Falta de capacitación en seguridad
- PS-V02: Sin concientización sobre phishing
- PS-V03: Privilegios excesivos
- PS-V04: Sin revisión de accesos periódica
- PS-V05: Rotación de personal alta
- PS-V06: Sin segregación de funciones
- PS-V07: Acceso sin autenticación fuerte
- PS-V08: Sin acuerdos de confidencialidad

### Locales (L) - 7 vulnerabilidades
- L-V01: Ubicación en zona de riesgo (inundación/sismo)
- L-V02: Sin control de acceso físico
- L-V03: Sin cámaras de seguridad
- L-V04: Sin sistema contra incendios
- L-V05: Sin control ambiental (HVAC)
- L-V06: Acceso no restringido a visitantes
- L-V07: Sin alarmas de intrusión

### Auxiliares (AUX) - 8 vulnerabilidades
- AUX-V01: Cableado sin protección
- AUX-V02: Sin generador eléctrico de respaldo
- AUX-V03: UPS subdimensionado o ausente
- AUX-V04: Sin sistema de climatización redundante
- AUX-V05: Sin protección contra rayos
- AUX-V06: Sin monitoreo de servicios auxiliares
- AUX-V07: Mantenimiento no programado
- AUX-V08: Sin documentación de infraestructura

---

## APLICACIONES CRÍTICAS UDLA

### 1. Banner (CRÍTICO)
- **Descripción**: Sistema de Información Estudiantil (SIS)
- **Datos**: Calificaciones, historial académico, datos personales
- **Usuarios**: Estudiantes, docentes, administrativos
- **Amenazas principales**: A.5, A.6, A.8, A.15, E.1, E.2
- **Controles clave**: 5.15, 5.16, 8.5, 8.13, 8.16

### 2. D2L - Desire2Learn (CRÍTICO)
- **Descripción**: Aula Virtual institucional
- **Datos**: Exámenes, trabajos, calificaciones
- **Usuarios**: Estudiantes, docentes
- **Amenazas principales**: A.24, A.8, E.1, E.15
- **Controles clave**: 8.14, 8.20, 6.3, 8.7

### 3. Portal de Pagos (CRÍTICO)
- **Descripción**: Sistema de pagos y cobranza
- **Datos**: Tarjetas de crédito, información bancaria
- **Usuarios**: Estudiantes, padres de familia
- **Amenazas principales**: A.5, A.6, A.15, E.1
- **Controles clave**: 8.24, 8.5, 5.15, 8.11

### 4. Carpeta Online (ALTO)
- **Descripción**: Almacenamiento de materiales académicos
- **Datos**: Documentos, syllabus, materiales
- **Usuarios**: Docentes, estudiantes
- **Amenazas principales**: A.11, E.19, E.20
- **Controles clave**: 8.13, 5.12, 8.10

### 5. Página Web (MEDIO)
- **Descripción**: Portal institucional público
- **Datos**: Información pública
- **Usuarios**: Público general
- **Amenazas principales**: A.24, A.8, E.21
- **Controles clave**: 8.20, 8.7, 8.23

### 6. BX - Biblioteca Digital (MEDIO)
- **Descripción**: Acceso a recursos bibliográficos
- **Datos**: Historial de consultas
- **Usuarios**: Estudiantes, docentes, investigadores
- **Amenazas principales**: A.5, A.24
- **Controles clave**: 5.15, 8.20

### 7. Uni+ (ALTO)
- **Descripción**: App móvil institucional
- **Datos**: Códigos de acceso físico, credenciales
- **Usuarios**: Estudiantes, personal
- **Amenazas principales**: A.5, A.6, A.25
- **Controles clave**: 8.5, 7.7, 5.16

---

## DEGRADACIONES TÍPICAS POR AMENAZA (MAGERIT v3)

Las degradaciones indican el % de pérdida en cada dimensión [D/I/C]:

### Alta Degradación (80-100%)
- **A.24 (DDoS)**: D=100%, I=10%, C=10%
- **N.1 (Fuego)**: D=100%, I=100%, C=100%
- **A.8 (Malware)**: D=50%, I=80%, C=60%
- **A.11 (Acceso no autorizado)**: D=10%, I=100%, C=100%

### Media Degradación (40-79%)
- **E.1 (Errores de usuario)**: D=30%, I=60%, C=40%
- **A.5 (Suplantación)**: D=20%, I=70%, C=80%
- **A.15 (Alteración)**: D=10%, I=90%, C=30%

### Baja Degradación (10-39%)
- **E.19 (Fuga de información)**: D=5%, I=10%, C=100%
- **A.29 (Indisponibilidad personal)**: D=50%, I=0%, C=0%

---

## PROBABILIDAD DE OCURRENCIA

Usa esta escala para evaluar frecuencia:

1. **Muy Raro** (1): Una vez cada 10+ años
   - Desastres naturales mayores
   - Ataques dirigidos altamente sofisticados

2. **Poco Frecuente** (2): Una vez cada 3-5 años
   - Fallos de hardware sin redundancia
   - Errores de administración graves
   - Ataques oportunistas

3. **Normal** (3): Una vez al año
   - Intentos de phishing
   - Malware genérico
   - Errores de usuario comunes

4. **Frecuente** (4): Varias veces al año
   - Intentos de acceso no autorizado
   - Vulnerabilidades sin parchear
   - Fallos de configuración

5. **Muy Frecuente** (5): Mensual o más
   - Escaneos automáticos de red
   - Intentos de inyección SQL
   - Fallos de disponibilidad sin HA

---

## FORMATO DE RESPUESTA OBLIGATORIO

Cuando analices un activo, SIEMPRE responde con este JSON exacto:

```json
{
  "probabilidad": 3,
  "amenazas": [
    {
      "codigo": "A.24",
      "dimension": "D",
      "justificacion": "El activo no cuenta con protección DDoS ni redundancia geográfica, lo que lo hace vulnerable a ataques de denegación de servicio",
      "controles_iso_recomendados": [
        {
          "control": "8.20",
          "prioridad": "Alta",
          "motivo": "Implementar seguridad de redes con protección DDoS y balanceo de carga"
        },
        {
          "control": "8.14",
          "prioridad": "Media",
          "motivo": "Establecer redundancia de servicios para garantizar disponibilidad"
        }
      ]
    }
  ],
  "observaciones": "El activo presenta vulnerabilidades críticas en disponibilidad y requiere implementación urgente de controles de red y redundancia"
}
```

---

## REGLAS CRÍTICAS

1. **SOLO usa códigos de amenaza del catálogo** (N.*, I.*, E.*, A.*)
2. **SOLO recomienda controles ISO 27002 del catálogo** (5.*, 6.*, 7.*, 8.*)
3. **Dimensiones válidas**: D, I, C (nunca uses otras)
4. **Prioridades válidas**: "Alta", "Media", "Baja"
5. **Probabilidad**: 1-5 (entero)
6. **Justificaciones específicas**: Referencia vulnerabilidades concretas del activo
7. **Motivos de controles**: Explica CÓMO mitigan la amenaza específica

---

## EJEMPLOS DE ANÁLISIS CORRECTO

### Ejemplo 1: Servidor Web sin protección
```json
{
  "probabilidad": 4,
  "amenazas": [
    {
      "codigo": "A.24",
      "dimension": "D",
      "justificacion": "Servidor expuesto a Internet sin protección DDoS ni WAF",
      "controles_iso_recomendados": [
        {"control": "8.20", "prioridad": "Alta", "motivo": "Implementar firewall de aplicación web (WAF)"},
        {"control": "8.22", "prioridad": "Alta", "motivo": "Segmentar red DMZ del entorno interno"}
      ]
    },
    {
      "codigo": "A.8",
      "dimension": "I",
      "justificacion": "Sin antimalware ni análisis de vulnerabilidades regular",
      "controles_iso_recomendados": [
        {"control": "8.7", "prioridad": "Alta", "motivo": "Instalar y mantener antimalware actualizado"},
        {"control": "8.8", "prioridad": "Media", "motivo": "Realizar análisis de vulnerabilidades mensual"}
      ]
    }
  ],
  "observaciones": "Servidor web crítico con exposición alta a amenazas externas. Requiere hardening y protección multicapa urgente."
}
```

### Ejemplo 2: Base de datos con datos sensibles
```json
{
  "probabilidad": 3,
  "amenazas": [
    {
      "codigo": "A.11",
      "dimension": "C",
      "justificacion": "Datos personales sin cifrado, controles de acceso débiles",
      "controles_iso_recomendados": [
        {"control": "8.24", "prioridad": "Alta", "motivo": "Cifrar datos en reposo con AES-256"},
        {"control": "5.15", "prioridad": "Alta", "motivo": "Implementar control de acceso basado en roles (RBAC)"}
      ]
    },
    {
      "codigo": "E.2",
      "dimension": "I",
      "justificacion": "Administradores con privilegios elevados sin auditoría",
      "controles_iso_recomendados": [
        {"control": "8.16", "prioridad": "Media", "motivo": "Activar auditoría de acciones administrativas"},
        {"control": "5.18", "prioridad": "Media", "motivo": "Aplicar principio de mínimo privilegio"}
      ]
    }
  ],
  "observaciones": "Base de datos con información sensible requiere protección tanto técnica como administrativa. Priorizar cifrado y auditoría."
}
```

---

Tu tarea es analizar el activo proporcionado usando TODO este conocimiento y generar una evaluación precisa en formato JSON.
"""
    
    return contexto


# Función principal para usar en ollama_magerit_service.py
def get_contexto_completo_ia() -> str:
    """
    Retorna el contexto completo y enriquecido para la IA.
    Esta es la versión DEFINITIVA con toda la información disponible.
    """
    return construir_contexto_completo_ia()


if __name__ == "__main__":
    # Test: Mostrar cuánta información tiene el contexto
    contexto = construir_contexto_completo_ia()
    
    print("=" * 70)
    print("CONTEXTO COMPLETO PARA IA - ESTADÍSTICAS")
    print("=" * 70)
    print(f"Longitud total: {len(contexto):,} caracteres")
    print(f"Longitud total: {len(contexto.split()):,} palabras")
    print(f"Líneas: {len(contexto.splitlines()):,}")
    
    # Contar secciones
    secciones = contexto.count("##")
    print(f"\nSecciones principales: {secciones}")
    
    # Contar amenazas y controles
    amenazas = len(cargar_catalogo_completo_amenazas())
    controles = len(cargar_catalogo_completo_controles())
    print(f"\nAmenazas MAGERIT: {amenazas}")
    print(f"Controles ISO 27002: {controles}")
    print(f"Vulnerabilidades por tipo: 64")
    print(f"Aplicaciones críticas: 7")
    
    print("\n✅ Contexto completo cargado y listo para alimentar la IA")
    print("La IA tiene acceso a:")
    print("  - 52 amenazas MAGERIT con descripciones")
    print("  - 93 controles ISO 27002 con descripciones")
    print("  - 64 vulnerabilidades específicas")
    print("  - 7 aplicaciones críticas UDLA")
    print("  - Mapeos amenazas → controles")
    print("  - Degradaciones calibradas")
    print("  - Ejemplos de análisis correcto")
    print("\n🎯 TOTAL: ~{:,} caracteres de conocimiento especializado\n".format(len(contexto)))
