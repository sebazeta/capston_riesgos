"""
CONTEXTO DE ENTRENAMIENTO PARA IA MAGERIT
==========================================
Este módulo proporciona el contexto completo para que la IA local (Ollama)
tenga todo el conocimiento necesario sobre MAGERIT v3, ISO 27002 y el sistema TITA.

La IA usa este contexto para:
1. Identificar amenazas apropiadas para cada tipo de activo
2. Sugerir controles ISO 27002 específicos
3. Calcular degradaciones realistas
4. Generar salvaguardas efectivas
5. Crear resúmenes ejecutivos profesionales
"""

from typing import Dict, List, Tuple
from services.database_service import read_table


# ==================== CONTEXTO MAGERIT v3 ====================

CONTEXTO_MAGERIT = """
## METODOLOGÍA MAGERIT v3 (Metodología de Análisis y Gestión de Riesgos de los Sistemas de Información)

MAGERIT es la metodología oficial española para gestión de riesgos de seguridad de la información.

### FÓRMULAS FUNDAMENTALES:

1. **CRITICIDAD** = MAX(Valor_D, Valor_I, Valor_C)
   - Valor más alto entre Disponibilidad, Integridad y Confidencialidad
   - Escala: 1 (Bajo), 2 (Medio), 3 (Alto), 4 (Crítico)

2. **IMPACTO** = MAX(Valor_D × Degradación_D, Valor_I × Degradación_I, Valor_C × Degradación_C)
   - Multiplicación del valor por la degradación en cada dimensión
   - Degradación: 0-100% según la amenaza

3. **RIESGO** = FRECUENCIA × IMPACTO
   - Frecuencia: 0.1 (Nula), 1 (Baja), 2 (Media), 3 (Alta)
   - Riesgo resultante: 0-12 aproximadamente

### DIMENSIONES DE SEGURIDAD:

- **[D] Disponibilidad**: ¿Qué pasa si el activo no está disponible?
  - Pregunta clave: ¿Cuánto tiempo puede estar sin funcionar?
  - RTO (Recovery Time Objective): Tiempo máximo de recuperación

- **[I] Integridad**: ¿Qué pasa si los datos son modificados incorrectamente?
  - Pregunta clave: ¿Qué tan grave sería una alteración no autorizada?
  - RPO (Recovery Point Objective): Pérdida máxima de datos aceptable

- **[C] Confidencialidad**: ¿Qué pasa si la información se filtra?
  - Pregunta clave: ¿Qué tan sensible es la información?
  - Clasificación: Pública, Interna, Confidencial, Secreta

### CATEGORÍAS DE AMENAZAS MAGERIT:

- **[N] Desastres Naturales**: Terremotos, inundaciones, incendios naturales
- **[I] Origen Industrial**: Fallos eléctricos, contaminación, accidentes
- **[E] Errores No Intencionados**: Errores de usuarios, configuración, mantenimiento
- **[A] Ataques Intencionados**: Hackers, malware, sabotaje, robo

### ZONAS DE RIESGO:

- **🟢 Bajo** (< 2): Riesgo aceptable, monitorear
- **🟡 Medio** (2-4): Requiere atención, planificar mitigación
- **🟠 Alto** (4-6): Prioridad alta, implementar controles
- **🔴 Crítico** (≥ 6): Urgente, acción inmediata requerida
"""


# ==================== CONTEXTO ISO 27002:2022 ====================

CONTEXTO_ISO27002 = """
## CONTROLES ISO 27002:2022

ISO 27002 proporciona 93 controles de seguridad organizados en 4 dominios:

### DOMINIOS:

**5.x - Controles Organizacionales (37 controles)**
- Políticas de seguridad
- Roles y responsabilidades
- Gestión de activos
- Control de acceso
- Relaciones con proveedores

**6.x - Controles de Personas (8 controles)**
- Selección de personal
- Concienciación y formación
- Proceso disciplinario
- Teletrabajo

**7.x - Controles Físicos (14 controles)**
- Perímetro de seguridad
- Controles de entrada física
- Protección contra amenazas
- Trabajo en áreas seguras
- Escritorio y pantalla limpios

**8.x - Controles Tecnológicos (34 controles)**
- Dispositivos de punto final
- Gestión de acceso privilegiado
- Restricción de acceso a información
- Acceso a código fuente
- Autenticación segura
- Gestión de capacidad
- Protección contra malware
- Gestión de vulnerabilidades
- Gestión de configuración
- Eliminación de información
- Enmascaramiento de datos
- Prevención de fuga de datos
- Copias de seguridad
- Redundancia
- Registro de actividad
- Monitoreo
- Sincronización de relojes
- Gestión de software
- Seguridad de redes
- Servicios de red
- Segregación de redes
- Filtrado web
- Uso de criptografía
- Ciclo de vida de desarrollo seguro
- Requisitos de seguridad
- Arquitectura segura
- Codificación segura
- Pruebas de seguridad
- Desarrollo externalizado
- Separación de entornos
- Gestión de cambios
- Datos de prueba
- Auditoría de sistemas
"""


# ==================== MAPEO AMENAZAS → CONTROLES ====================

MAPEO_AMENAZA_CONTROL = {
    # Desastres Naturales
    "N.1": ["7.5", "7.11", "8.14"],   # Fuego → Protección física, Redundancia
    "N.2": ["7.5", "7.11", "8.14"],   # Daños por agua → Protección física
    "N.*": ["7.5", "5.29", "5.30"],   # General → Continuidad de negocio
    
    # Origen Industrial
    "I.1": ["7.11", "8.14"],          # Fuego industrial → Redundancia
    "I.2": ["7.5", "7.11"],           # Daños por agua industrial
    "I.3": ["7.5", "7.12"],           # Contaminación mecánica
    "I.4": ["7.5", "7.12"],           # Contaminación electromagnética
    "I.5": ["7.11", "8.14"],          # Avería origen físico → Redundancia
    "I.6": ["7.13", "7.11"],          # Corte suministro eléctrico
    "I.7": ["7.14", "7.11"],          # Condiciones inadecuadas
    "I.8": ["8.20", "8.21", "8.22"],  # Fallo de comunicaciones → Seguridad red
    "I.9": ["5.22", "5.23"],          # Interrupción servicios → Proveedores
    "I.10": ["8.6", "8.9"],           # Degradación soportes
    "I.11": ["8.25", "8.29"],         # Emanaciones electromagnéticas
    
    # Errores No Intencionados
    "E.1": ["6.3", "5.10"],           # Errores usuarios → Formación
    "E.2": ["6.3", "8.9"],            # Errores administrador → Formación, Config
    "E.3": ["5.37", "8.9"],           # Errores monitorización
    "E.4": ["5.9", "8.9"],            # Errores configuración
    "E.7": ["5.12", "5.14"],          # Deficiencias organización
    "E.8": ["8.1", "8.9"],            # Difusión software dañino
    "E.9": ["8.20", "8.21"],          # Errores encaminamiento
    "E.10": ["8.20", "8.21"],         # Errores secuencia
    "E.14": ["5.12", "5.10"],         # Escapes información → Clasificación
    "E.15": ["8.9", "8.32"],          # Alteración accidental
    "E.18": ["8.13", "8.14"],         # Destrucción información → Backup
    "E.19": ["8.10", "7.10"],         # Fugas información
    "E.20": ["8.12", "7.10"],         # Vulnerabilidades programas
    "E.21": ["8.8", "8.32"],          # Errores mantenimiento/actualización
    "E.23": ["8.6", "7.13"],          # Errores mantenimiento equipos
    "E.24": ["5.33", "8.15"],         # Caída sistema por agotamiento
    "E.25": ["8.2", "8.5"],           # Pérdida de equipos
    "E.28": ["5.14", "6.3"],          # Indisponibilidad personal
    
    # Ataques Intencionados
    "A.3": ["8.15", "8.16"],          # Manipulación registros → Logs
    "A.4": ["8.24", "8.5"],           # Manipulación configuración
    "A.5": ["8.5", "5.15", "5.16"],   # Suplantación identidad → Autenticación
    "A.6": ["5.15", "5.18", "8.2"],   # Abuso privilegios → Control acceso
    "A.7": ["8.3", "5.15"],           # Uso no previsto
    "A.8": ["8.7", "8.8"],            # Difusión software dañino → Antimalware
    "A.9": ["8.20", "8.21", "8.22"],  # Re-encaminamiento → Seguridad red
    "A.10": ["8.20", "8.21"],         # Alteración secuencia
    "A.11": ["7.1", "7.2", "7.4"],    # Acceso no autorizado → Control físico
    "A.12": ["8.16", "8.15"],         # Análisis tráfico
    "A.13": ["8.5", "8.3"],           # Repudio
    "A.14": ["8.24", "8.20"],         # Interceptación → Cifrado
    "A.15": ["8.24", "8.11", "8.10"], # Modificación deliberada → Cifrado
    "A.18": ["8.13", "8.14"],         # Destrucción información
    "A.19": ["8.10", "5.12"],         # Divulgación información
    "A.22": ["8.28", "8.29"],         # Manipulación programas
    "A.23": ["8.28", "8.29"],         # Manipulación equipos
    "A.24": ["8.22", "8.6"],          # Denegación servicio → Segmentación
    "A.25": ["7.1", "7.2", "7.5"],    # Robo → Control físico
    "A.26": ["7.1", "7.5", "8.1"],    # Ataque destructivo
    "A.27": ["7.4", "7.1"],           # Ocupación enemiga
    "A.28": ["5.5", "5.6"],           # Indisponibilidad personal
    "A.29": ["5.19", "5.20"],         # Extorsión
    "A.30": ["5.7", "8.16"],          # Ingeniería social
}


# ==================== MAPEO TIPO ACTIVO → AMENAZAS TÍPICAS ====================

AMENAZAS_POR_TIPO_ACTIVO = {
    "servidor": {
        "amenazas": ["A.24", "A.5", "A.6", "A.8", "I.5", "I.6", "E.2", "E.21"],
        "descripcion": "Servidores físicos y virtuales",
        "criticidad_tipica": "Alta"
    },
    "base de datos": {
        "amenazas": ["A.5", "A.6", "A.15", "A.19", "E.1", "E.2", "E.15", "E.18"],
        "descripcion": "Sistemas gestores de bases de datos",
        "criticidad_tipica": "Crítica"
    },
    "aplicacion": {
        "amenazas": ["A.5", "A.6", "A.8", "A.22", "E.1", "E.20", "E.21"],
        "descripcion": "Software y aplicaciones de negocio",
        "criticidad_tipica": "Alta"
    },
    "red": {
        "amenazas": ["A.9", "A.12", "A.14", "A.24", "I.8", "E.9"],
        "descripcion": "Equipos de red (routers, switches, firewalls)",
        "criticidad_tipica": "Alta"
    },
    "estacion": {
        "amenazas": ["A.5", "A.8", "A.25", "E.1", "E.25"],
        "descripcion": "Estaciones de trabajo y laptops",
        "criticidad_tipica": "Media"
    },
    "almacenamiento": {
        "amenazas": ["A.11", "A.15", "A.18", "A.19", "I.5", "I.10", "E.18"],
        "descripcion": "Sistemas de almacenamiento (SAN, NAS, backup)",
        "criticidad_tipica": "Crítica"
    },
    "comunicacion": {
        "amenazas": ["A.12", "A.14", "I.8", "E.9", "E.10"],
        "descripcion": "Sistemas de comunicación (VoIP, email)",
        "criticidad_tipica": "Alta"
    },
    "cloud": {
        "amenazas": ["A.5", "A.6", "A.19", "I.9", "E.2"],
        "descripcion": "Servicios en la nube",
        "criticidad_tipica": "Alta"
    },
    "iot": {
        "amenazas": ["A.5", "A.8", "A.11", "A.24", "E.2", "I.5"],
        "descripcion": "Dispositivos IoT y sensores",
        "criticidad_tipica": "Media"
    },
    "persona": {
        "amenazas": ["A.28", "A.29", "A.30", "E.28"],
        "descripcion": "Personal clave de la organización",
        "criticidad_tipica": "Alta"
    },
    "instalacion": {
        "amenazas": ["A.11", "A.25", "A.26", "A.27", "N.1", "N.2", "I.1", "I.2"],
        "descripcion": "Instalaciones físicas (CPD, oficinas)",
        "criticidad_tipica": "Crítica"
    }
}


# ==================== DEGRADACIÓN POR TIPO DE AMENAZA ====================

DEGRADACION_TIPICA = {
    # Desastres naturales - alta degradación en disponibilidad
    "N": {"D": 90, "I": 30, "C": 10},
    
    # Origen industrial - afecta principalmente disponibilidad
    "I": {"D": 70, "I": 20, "C": 10},
    
    # Errores no intencionados - afecta integridad y disponibilidad
    "E": {"D": 40, "I": 60, "C": 30},
    
    # Ataques intencionados - puede afectar todo
    "A": {"D": 60, "I": 70, "C": 80},
}


# ==================== FUNCIÓN PARA OBTENER CONTEXTO COMPLETO ====================

def get_contexto_completo_ia() -> str:
    """
    Genera el contexto completo para la IA incluyendo todos los catálogos.
    """
    # Cargar catálogos de la base de datos
    amenazas_df = read_table("CATALOGO_AMENAZAS_MAGERIT")
    controles_df = read_table("CATALOGO_CONTROLES_ISO27002")
    
    # Construir lista de amenazas
    amenazas_texto = "\n## CATÁLOGO COMPLETO DE AMENAZAS MAGERIT v3:\n"
    amenazas_texto += "DEBES usar SOLO estos códigos de amenaza:\n\n"
    
    if not amenazas_df.empty:
        for tipo in ["N", "I", "E", "A"]:
            amenazas_tipo = amenazas_df[amenazas_df["codigo"].str.startswith(tipo)]
            if not amenazas_tipo.empty:
                tipo_nombre = {
                    "N": "[N] DESASTRES NATURALES",
                    "I": "[I] ORIGEN INDUSTRIAL", 
                    "E": "[E] ERRORES NO INTENCIONADOS",
                    "A": "[A] ATAQUES INTENCIONADOS"
                }.get(tipo, tipo)
                amenazas_texto += f"\n### {tipo_nombre}:\n"
                for _, row in amenazas_tipo.iterrows():
                    dim = row.get("dimension_afectada", "D")
                    amenazas_texto += f"- **{row['codigo']}**: {row['amenaza']} [afecta: {dim}]\n"
    
    # Construir lista de controles
    controles_texto = "\n## CATÁLOGO COMPLETO DE CONTROLES ISO 27002:2022:\n"
    controles_texto += "DEBES usar SOLO estos códigos de control:\n\n"
    
    if not controles_df.empty:
        categorias = controles_df["categoria"].unique()
        for cat in sorted(categorias):
            controles_cat = controles_df[controles_df["categoria"] == cat]
            controles_texto += f"\n### {cat}:\n"
            for _, row in controles_cat.iterrows():
                controles_texto += f"- **{row['codigo']}**: {row['nombre']}\n"
    
    # Combinar todo
    contexto = f"""
{CONTEXTO_MAGERIT}

{CONTEXTO_ISO27002}

{amenazas_texto}

{controles_texto}

## REGLAS CRÍTICAS PARA LA IA:
1. SOLO usa códigos de amenaza del catálogo anterior (N.1, N.2, I.1, ... A.30)
2. SOLO usa códigos de control del catálogo anterior (5.1, 5.2, ... 8.34)
3. NO inventes códigos nuevos
4. Siempre justifica por qué una amenaza aplica al activo específico
5. Relaciona controles con amenazas de forma lógica
6. Usa el mapeo AMENAZA → CONTROL proporcionado
7. Considera el tipo de activo para seleccionar amenazas relevantes
"""
    
    return contexto


def get_amenazas_para_tipo_activo(tipo_activo: str) -> List[str]:
    """
    Obtiene las amenazas típicas para un tipo de activo.
    """
    tipo_lower = tipo_activo.lower()
    
    for key, info in AMENAZAS_POR_TIPO_ACTIVO.items():
        if key in tipo_lower:
            return info["amenazas"]
    
    # Default: amenazas genéricas
    return ["A.5", "A.6", "A.8", "A.24", "E.1", "E.2", "I.5"]


def get_controles_para_amenaza(codigo_amenaza: str) -> List[str]:
    """
    Obtiene los controles recomendados para una amenaza específica.
    """
    # Buscar coincidencia exacta
    if codigo_amenaza in MAPEO_AMENAZA_CONTROL:
        return MAPEO_AMENAZA_CONTROL[codigo_amenaza]
    
    # Buscar por categoría (N.*, I.*, etc.)
    categoria = codigo_amenaza[0] if codigo_amenaza else ""
    clave_categoria = f"{categoria}.*"
    if clave_categoria in MAPEO_AMENAZA_CONTROL:
        return MAPEO_AMENAZA_CONTROL[clave_categoria]
    
    # Default
    return ["5.1", "5.15", "8.9"]


def get_degradacion_tipica(codigo_amenaza: str) -> Dict[str, int]:
    """
    Obtiene la degradación típica para una amenaza.
    """
    categoria = codigo_amenaza[0] if codigo_amenaza else "E"
    return DEGRADACION_TIPICA.get(categoria, {"D": 50, "I": 50, "C": 50})


# ==================== PROMPT MEJORADO PARA IA ====================

def construir_prompt_experto(
    activo_nombre: str,
    activo_tipo: str,
    criticidad: int,
    valoracion_d: int,
    valoracion_i: int,
    valoracion_c: int
) -> str:
    """
    Construye un prompt optimizado para que la IA identifique amenazas.
    """
    # Obtener amenazas sugeridas para el tipo
    amenazas_sugeridas = get_amenazas_para_tipo_activo(activo_tipo)
    
    # Obtener contexto de catálogos
    amenazas_df = read_table("CATALOGO_AMENAZAS_MAGERIT")
    
    # Construir lista de amenazas del catálogo
    lista_amenazas = ""
    if not amenazas_df.empty:
        for _, row in amenazas_df.iterrows():
            lista_amenazas += f"- {row['codigo']}: {row['amenaza']}\n"
    
    prompt = f"""Eres un experto certificado en MAGERIT v3 e ISO 27002:2022.

## ACTIVO A ANALIZAR:
- **Nombre**: {activo_nombre}
- **Tipo**: {activo_tipo}
- **Criticidad**: {criticidad}/4
- **Valoración D/I/C**: D={valoracion_d}, I={valoracion_i}, C={valoracion_c}

## AMENAZAS SUGERIDAS PARA ESTE TIPO DE ACTIVO:
{', '.join(amenazas_sugeridas)}

## CATÁLOGO COMPLETO DE AMENAZAS (USA SOLO ESTOS CÓDIGOS):
{lista_amenazas}

## TU TAREA:
1. Selecciona 4-6 amenazas RELEVANTES para este activo específico
2. Para cada amenaza, calcula la degradación D/I/C (0-100%)
3. Considera: tipo de activo, criticidad, y dimensión más valorada

## FORMATO DE RESPUESTA (JSON VÁLIDO):
```json
{{
  "amenazas": [
    {{
      "codigo_amenaza": "A.5",
      "nombre_amenaza": "Suplantación de identidad",
      "vulnerabilidad": "Descripción de la vulnerabilidad asociada",
      "degradacion_d": 30,
      "degradacion_i": 60,
      "degradacion_c": 80,
      "justificacion": "Por qué esta amenaza aplica a este activo"
    }}
  ]
}}
```

## REGLAS:
1. USA SOLO códigos del catálogo proporcionado
2. Degradaciones: 0-100, siendo 100 destrucción total
3. Ajusta degradación según la criticidad ({criticidad}/4)
4. Prioriza dimensión con mayor valoración

Responde SOLO con el JSON, sin explicaciones adicionales:"""

    return prompt
