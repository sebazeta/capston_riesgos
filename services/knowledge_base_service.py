"""
KNOWLEDGE BASE SERVICE - PROYECTO TITA
=======================================
Gestión del conocimiento local para inyección en IA.
Incluye:
- Carga de catálogos desde BD
- Generación de system prompts
- Few-shot examples
- Context injection para evaluación MAGERIT

100% LOCAL - Sin conexiones externas.
"""
import json
import datetime as dt
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from services.database_service import read_table, get_connection


# ==================== MODELOS ====================

@dataclass
class KnowledgeContext:
    """Contexto de conocimiento para inyectar en prompts"""
    amenazas_magerit: List[Dict]
    controles_iso: List[Dict]
    criterios_dic: Dict[str, List[Dict]]
    few_shot_examples: List[Dict]
    system_prompt: str
    version: str
    timestamp: str


# ==================== CARGA DE CATÁLOGOS ====================

def cargar_catalogo_amenazas() -> List[Dict]:
    """Carga todas las amenazas MAGERIT desde BD"""
    try:
        amenazas = read_table("CATALOGO_AMENAZAS_MAGERIT")
        if amenazas is not None and not amenazas.empty:
            return amenazas.to_dict('records')
        return []
    except Exception as e:
        print(f"Error cargando amenazas: {e}")
        return []


def cargar_catalogo_controles() -> List[Dict]:
    """Carga todos los controles ISO 27002 desde BD"""
    try:
        controles = read_table("CATALOGO_CONTROLES_ISO27002")
        if controles is not None and not controles.empty:
            return controles.to_dict('records')
        return []
    except Exception as e:
        print(f"Error cargando controles: {e}")
        return []


def cargar_criterios_dic() -> Dict[str, List[Dict]]:
    """Carga criterios D/I/C desde BD"""
    criterios = {
        "disponibilidad": [],
        "integridad": [],
        "confidencialidad": []
    }
    
    try:
        for tabla, clave in [
            ("CRITERIOS_DISPONIBILIDAD", "disponibilidad"),
            ("CRITERIOS_INTEGRIDAD", "integridad"),
            ("CRITERIOS_CONFIDENCIALIDAD", "confidencialidad")
        ]:
            datos = read_table(tabla)
            if datos is not None and not datos.empty:
                criterios[clave] = datos.to_dict('records')
    except Exception as e:
        print(f"Error cargando criterios: {e}")
    
    return criterios


# ==================== SYSTEM PROMPT ====================

SYSTEM_PROMPT_MAGERIT = """Eres TITA-MAGERIT, un analista experto en evaluación de riesgos según la metodología MAGERIT v3 y controles ISO 27002:2022.

## TU ROL
Eres parte del sistema de evaluación de riesgos TITA (Transformación Integral de TI y Activos) de una universidad. Tu función es analizar activos tecnológicos e identificar amenazas según el catálogo oficial MAGERIT y recomendar controles ISO 27002.

## REGLAS ABSOLUTAS
1. SOLO puedes identificar amenazas que existan en el catálogo MAGERIT proporcionado
2. SOLO puedes recomendar controles que existan en el catálogo ISO 27002:2022 proporcionado
3. SIEMPRE debes responder en formato JSON válido
4. NUNCA inventes códigos de amenazas o controles
5. Los códigos de amenazas tienen formato: [CATEGORIA].[SUBCATEGORIA] (ej: D.1, I.5, A.11)
6. Los códigos de controles tienen formato: X.X o X.XX (ej: 5.1, 8.16)

## ESCALA DE EVALUACIÓN MAGERIT
- Probabilidad: 1 (Muy Baja) a 5 (Muy Alta)
- Impacto: 1 (Muy Bajo) a 5 (Muy Alto)
- Riesgo = Probabilidad × Impacto (escala 1-25)

## NIVELES DE RIESGO
- MUY BAJO: 1-4
- BAJO: 5-8
- MEDIO: 9-12
- ALTO: 13-20
- CRÍTICO: 21-25

## CATEGORÍAS DE AMENAZAS MAGERIT
- [D] Desastres naturales: Fenómenos naturales que afectan infraestructura
- [I] De origen industrial: Fallos de servicios, infraestructura, equipamiento
- [E] Errores y fallos no intencionados: Errores humanos, de configuración, software
- [A] Ataques intencionados: Acciones maliciosas deliberadas

## CATEGORÍAS DE CONTROLES ISO 27002:2022
- 5.X: Controles Organizacionales (37 controles)
- 6.X: Controles de Personas (8 controles)
- 7.X: Controles Físicos (14 controles)
- 8.X: Controles Tecnológicos (34 controles)

## CRITERIOS D/I/C
Al evaluar impacto, considera:
- Disponibilidad (D): ¿Cuánto afecta la interrupción del servicio?
- Integridad (I): ¿Cuánto afecta la alteración de la información?
- Confidencialidad (C): ¿Cuánto afecta la divulgación no autorizada?

## CONTEXTO ACADÉMICO
Este sistema es para trabajo de titulación. Las evaluaciones deben ser:
- Técnicamente rigurosas
- Bien fundamentadas
- Trazables a catálogos oficiales
- Reproducibles y auditables"""


def generar_system_prompt_con_catalogos() -> str:
    """Genera el system prompt completo con catálogos embebidos"""
    amenazas = cargar_catalogo_amenazas()
    controles = cargar_catalogo_controles()
    
    # Formatear amenazas
    amenazas_txt = "## CATÁLOGO DE AMENAZAS MAGERIT\n"
    categoria_actual = ""
    for a in amenazas:
        if a.get("categoria") != categoria_actual:
            categoria_actual = a.get("categoria", "")
            amenazas_txt += f"\n### {categoria_actual}\n"
        amenazas_txt += f"- {a.get('codigo')}: {a.get('nombre')} - {a.get('descripcion', '')[:80]}\n"
    
    # Formatear controles
    controles_txt = "\n## CATÁLOGO DE CONTROLES ISO 27002:2022\n"
    categoria_actual = ""
    for c in controles:
        if c.get("categoria") != categoria_actual:
            categoria_actual = c.get("categoria", "")
            controles_txt += f"\n### {categoria_actual}\n"
        controles_txt += f"- {c.get('codigo')}: {c.get('nombre')}\n"
    
    return SYSTEM_PROMPT_MAGERIT + "\n\n" + amenazas_txt + "\n" + controles_txt


# ==================== FEW-SHOT EXAMPLES ====================

FEW_SHOT_EXAMPLES = [
    {
        "descripcion": "Servidor Web de Producción expuesto a Internet",
        "prompt": """Evalúa el siguiente activo tecnológico y devuelve un JSON con las amenazas identificadas y controles recomendados.

ACTIVO: Servidor Web de Producción
- Tipo: Servidor
- Criticidad: Alta
- Expuesto a Internet: Sí
- Datos que procesa: Información de estudiantes
- Respaldo: Semanal

Responde SOLO con JSON válido.""",
        "respuesta": {
            "activo": "Servidor Web de Producción",
            "evaluacion_dic": {
                "disponibilidad": 4,
                "integridad": 4,
                "confidencialidad": 5
            },
            "amenazas": [
                {
                    "codigo": "A.5",
                    "nombre": "Suplantación de la identidad del usuario",
                    "probabilidad": 4,
                    "impacto": 5,
                    "justificacion": "Expuesto a Internet sin mención de MFA"
                },
                {
                    "codigo": "A.11",
                    "nombre": "Acceso no autorizado",
                    "probabilidad": 4,
                    "impacto": 5,
                    "justificacion": "Servidor público con datos sensibles de estudiantes"
                },
                {
                    "codigo": "A.24",
                    "nombre": "Denegación de servicio",
                    "probabilidad": 3,
                    "impacto": 4,
                    "justificacion": "Servicio web público susceptible a DDoS"
                },
                {
                    "codigo": "E.21",
                    "nombre": "Errores de mantenimiento / actualización de programas",
                    "probabilidad": 3,
                    "impacto": 3,
                    "justificacion": "Sin información sobre parches o actualizaciones"
                },
                {
                    "codigo": "I.5",
                    "nombre": "Avería de origen físico o lógico",
                    "probabilidad": 2,
                    "impacto": 4,
                    "justificacion": "Respaldo solo semanal, posible pérdida de datos"
                }
            ],
            "controles_recomendados": [
                {
                    "codigo": "8.5",
                    "nombre": "Autenticación segura",
                    "prioridad": "ALTA"
                },
                {
                    "codigo": "8.16",
                    "nombre": "Actividades de seguimiento",
                    "prioridad": "ALTA"
                },
                {
                    "codigo": "8.8",
                    "nombre": "Gestión de vulnerabilidades técnicas",
                    "prioridad": "ALTA"
                },
                {
                    "codigo": "8.13",
                    "nombre": "Respaldo de la información",
                    "prioridad": "MEDIA"
                },
                {
                    "codigo": "8.20",
                    "nombre": "Seguridad de redes",
                    "prioridad": "ALTA"
                }
            ],
            "riesgo_global": "ALTO",
            "observaciones": "Activo crítico expuesto. Se requiere implementar controles de acceso robustos y mejorar frecuencia de respaldos."
        }
    },
    {
        "descripcion": "Base de datos interna con información financiera",
        "prompt": """Evalúa el siguiente activo tecnológico y devuelve un JSON con las amenazas identificadas y controles recomendados.

ACTIVO: Base de Datos Financiera
- Tipo: Base de Datos
- Criticidad: Muy Alta
- Expuesto a Internet: No
- Datos que procesa: Información financiera institucional
- Respaldo: Diario
- Cifrado: No implementado

Responde SOLO con JSON válido.""",
        "respuesta": {
            "activo": "Base de Datos Financiera",
            "evaluacion_dic": {
                "disponibilidad": 5,
                "integridad": 5,
                "confidencialidad": 5
            },
            "amenazas": [
                {
                    "codigo": "A.11",
                    "nombre": "Acceso no autorizado",
                    "probabilidad": 3,
                    "impacto": 5,
                    "justificacion": "Datos financieros sin cifrado, alto valor para atacantes internos"
                },
                {
                    "codigo": "A.15",
                    "nombre": "Modificación deliberada de la información",
                    "probabilidad": 2,
                    "impacto": 5,
                    "justificacion": "Datos financieros son objetivo de fraude"
                },
                {
                    "codigo": "E.15",
                    "nombre": "Alteración accidental de la información",
                    "probabilidad": 3,
                    "impacto": 4,
                    "justificacion": "Sin mención de controles de integridad"
                },
                {
                    "codigo": "E.19",
                    "nombre": "Fugas de información",
                    "probabilidad": 3,
                    "impacto": 5,
                    "justificacion": "Datos sin cifrar vulnerables a extracción"
                },
                {
                    "codigo": "I.5",
                    "nombre": "Avería de origen físico o lógico",
                    "probabilidad": 2,
                    "impacto": 4,
                    "justificacion": "Respaldo diario mitiga pero no elimina riesgo"
                }
            ],
            "controles_recomendados": [
                {
                    "codigo": "8.11",
                    "nombre": "Enmascaramiento de datos",
                    "prioridad": "ALTA"
                },
                {
                    "codigo": "8.24",
                    "nombre": "Uso de criptografía",
                    "prioridad": "CRÍTICA"
                },
                {
                    "codigo": "8.3",
                    "nombre": "Restricción de acceso a la información",
                    "prioridad": "ALTA"
                },
                {
                    "codigo": "5.15",
                    "nombre": "Control de acceso",
                    "prioridad": "ALTA"
                },
                {
                    "codigo": "8.4",
                    "nombre": "Acceso al código fuente",
                    "prioridad": "MEDIA"
                }
            ],
            "riesgo_global": "CRÍTICO",
            "observaciones": "Implementar cifrado en reposo es URGENTE. Datos financieros sin protección criptográfica representan riesgo inaceptable."
        }
    },
    {
        "descripcion": "Laptop de trabajo remoto",
        "prompt": """Evalúa el siguiente activo tecnológico y devuelve un JSON con las amenazas identificadas y controles recomendados.

ACTIVO: Laptop Trabajo Remoto
- Tipo: Equipo de Usuario
- Criticidad: Media
- Expuesto a Internet: Sí (uso doméstico)
- Datos que procesa: Documentos de trabajo
- Respaldo: En nube institucional
- Cifrado de disco: Sí

Responde SOLO con JSON válido.""",
        "respuesta": {
            "activo": "Laptop Trabajo Remoto",
            "evaluacion_dic": {
                "disponibilidad": 3,
                "integridad": 3,
                "confidencialidad": 4
            },
            "amenazas": [
                {
                    "codigo": "A.25",
                    "nombre": "Robo",
                    "probabilidad": 3,
                    "impacto": 3,
                    "justificacion": "Equipo móvil fuera de instalaciones"
                },
                {
                    "codigo": "E.1",
                    "nombre": "Errores de los usuarios",
                    "probabilidad": 3,
                    "impacto": 2,
                    "justificacion": "Uso en ambiente no controlado"
                },
                {
                    "codigo": "A.7",
                    "nombre": "Uso no previsto",
                    "probabilidad": 2,
                    "impacto": 3,
                    "justificacion": "Posible uso personal mezclado con laboral"
                },
                {
                    "codigo": "E.25",
                    "nombre": "Pérdida de equipos",
                    "probabilidad": 2,
                    "impacto": 2,
                    "justificacion": "Equipo móvil susceptible a pérdida"
                }
            ],
            "controles_recomendados": [
                {
                    "codigo": "6.7",
                    "nombre": "Trabajo a distancia",
                    "prioridad": "ALTA"
                },
                {
                    "codigo": "7.9",
                    "nombre": "Seguridad de activos fuera de las instalaciones",
                    "prioridad": "ALTA"
                },
                {
                    "codigo": "8.1",
                    "nombre": "Dispositivos de usuario final",
                    "prioridad": "MEDIA"
                },
                {
                    "codigo": "5.10",
                    "nombre": "Uso aceptable de información y activos",
                    "prioridad": "MEDIA"
                }
            ],
            "riesgo_global": "MEDIO",
            "observaciones": "El cifrado de disco mitiga riesgos de robo. Fortalecer políticas de trabajo remoto."
        }
    }
]


def obtener_few_shot_examples() -> List[Dict]:
    """Retorna los ejemplos few-shot para inyección"""
    return FEW_SHOT_EXAMPLES


def formatear_few_shot_para_prompt() -> str:
    """Formatea los ejemplos para incluir en prompt"""
    ejemplos_txt = "\n## EJEMPLOS DE EVALUACIONES ANTERIORES\n"
    ejemplos_txt += "Usa estos ejemplos como referencia de formato y nivel de detalle:\n\n"
    
    for i, ejemplo in enumerate(FEW_SHOT_EXAMPLES[:2], 1):  # Solo 2 para no hacer prompt muy largo
        ejemplos_txt += f"### Ejemplo {i}: {ejemplo['descripcion']}\n"
        ejemplos_txt += f"**Pregunta:**\n{ejemplo['prompt'][:300]}...\n\n"
        ejemplos_txt += f"**Respuesta JSON:**\n```json\n{json.dumps(ejemplo['respuesta'], indent=2, ensure_ascii=False)[:800]}...\n```\n\n"
    
    return ejemplos_txt


# ==================== CONSTRUCCIÓN DE CONTEXTO COMPLETO ====================

def construir_knowledge_context() -> KnowledgeContext:
    """Construye el contexto completo de conocimiento"""
    return KnowledgeContext(
        amenazas_magerit=cargar_catalogo_amenazas(),
        controles_iso=cargar_catalogo_controles(),
        criterios_dic=cargar_criterios_dic(),
        few_shot_examples=FEW_SHOT_EXAMPLES,
        system_prompt=generar_system_prompt_con_catalogos(),
        version="1.0.0",
        timestamp=dt.datetime.now().isoformat()
    )


def construir_prompt_evaluacion_activo(
    nombre_activo: str,
    tipo_activo: str,
    criticidad: str,
    caracteristicas: Dict,
    respuestas_cuestionario: Dict = None,
    include_few_shot: bool = True
) -> str:
    """
    Construye prompt completo para evaluación de activo.
    
    Args:
        nombre_activo: Nombre del activo
        tipo_activo: Tipo (Servidor, BD, etc)
        criticidad: Nivel de criticidad
        caracteristicas: Diccionario con características
        respuestas_cuestionario: Respuestas a preguntas de seguridad
        include_few_shot: Incluir ejemplos few-shot
    """
    prompt = ""
    
    # Añadir few-shot si aplica
    if include_few_shot:
        prompt += formatear_few_shot_para_prompt()
    
    # Prompt principal
    prompt += f"""
## TAREA DE EVALUACIÓN

Evalúa el siguiente activo tecnológico y devuelve un JSON con las amenazas identificadas según catálogo MAGERIT y controles recomendados según ISO 27002:2022.

### ACTIVO A EVALUAR
- **Nombre:** {nombre_activo}
- **Tipo:** {tipo_activo}
- **Criticidad:** {criticidad}
"""
    
    # Características
    if caracteristicas:
        prompt += "\n### CARACTERÍSTICAS\n"
        for k, v in caracteristicas.items():
            prompt += f"- {k}: {v}\n"
    
    # Respuestas de cuestionario
    if respuestas_cuestionario:
        prompt += "\n### RESPUESTAS DE CUESTIONARIO DE SEGURIDAD\n"
        for pregunta, respuesta in respuestas_cuestionario.items():
            prompt += f"- {pregunta}: {respuesta}\n"
    
    # Formato de respuesta esperado
    prompt += """
### FORMATO DE RESPUESTA REQUERIDO
Responde ÚNICAMENTE con un JSON válido con esta estructura:

```json
{
    "activo": "nombre del activo",
    "evaluacion_dic": {
        "disponibilidad": 1-5,
        "integridad": 1-5,
        "confidencialidad": 1-5
    },
    "amenazas": [
        {
            "codigo": "CÓDIGO MAGERIT EXACTO",
            "nombre": "nombre oficial de la amenaza",
            "probabilidad": 1-5,
            "impacto": 1-5,
            "justificacion": "razón técnica"
        }
    ],
    "controles_recomendados": [
        {
            "codigo": "CÓDIGO ISO 27002 EXACTO",
            "nombre": "nombre del control",
            "prioridad": "CRÍTICA/ALTA/MEDIA/BAJA"
        }
    ],
    "riesgo_global": "MUY BAJO/BAJO/MEDIO/ALTO/CRÍTICO",
    "observaciones": "análisis general"
}
```

IMPORTANTE:
1. SOLO usa códigos que existan en los catálogos proporcionados
2. Identifica mínimo 4 amenazas relevantes
3. Recomienda mínimo 4 controles
4. Las justificaciones deben ser técnicas y específicas al activo
5. NO incluyas texto antes o después del JSON
"""
    
    return prompt


# ==================== RESUMEN DE CATÁLOGOS ====================

def obtener_resumen_catalogos() -> Dict:
    """Obtiene resumen de catálogos cargados"""
    amenazas = cargar_catalogo_amenazas()
    controles = cargar_catalogo_controles()
    
    # Contar por categoría
    amenazas_por_cat = {}
    for a in amenazas:
        cat = a.get("categoria", "Sin categoría")
        amenazas_por_cat[cat] = amenazas_por_cat.get(cat, 0) + 1
    
    controles_por_cat = {}
    for c in controles:
        cat = c.get("categoria", "Sin categoría")
        controles_por_cat[cat] = controles_por_cat.get(cat, 0) + 1
    
    return {
        "total_amenazas": len(amenazas),
        "total_controles": len(controles),
        "amenazas_por_categoria": amenazas_por_cat,
        "controles_por_categoria": controles_por_cat,
        "few_shot_examples": len(FEW_SHOT_EXAMPLES),
        "version": "MAGERIT v3 + ISO 27002:2022"
    }


# ==================== VALIDACIÓN DE CÓDIGOS ====================

def validar_codigo_amenaza(codigo: str) -> bool:
    """Verifica que un código de amenaza exista en el catálogo"""
    amenazas = cargar_catalogo_amenazas()
    return any(a.get("codigo") == codigo for a in amenazas)


def validar_codigo_control(codigo: str) -> bool:
    """Verifica que un código de control exista en el catálogo"""
    controles = cargar_catalogo_controles()
    return any(c.get("codigo") == codigo for c in controles)


def validar_respuesta_ia_contra_catalogos(respuesta: Dict) -> Tuple[bool, List[str]]:
    """
    Valida que todos los códigos en la respuesta IA existan en catálogos.
    
    Returns:
        (es_valida: bool, errores: List[str])
    """
    errores = []
    
    # Validar amenazas
    for amenaza in respuesta.get("amenazas", []):
        codigo = amenaza.get("codigo", "")
        if not validar_codigo_amenaza(codigo):
            errores.append(f"Amenaza inexistente: {codigo}")
    
    # Validar controles
    for control in respuesta.get("controles_recomendados", []):
        codigo = control.get("codigo", "")
        if not validar_codigo_control(codigo):
            errores.append(f"Control inexistente: {codigo}")
    
    return len(errores) == 0, errores


# ==================== EXPORTACIÓN JSON ====================

def exportar_knowledge_base_json(filepath: str) -> bool:
    """Exporta toda la knowledge base a archivo JSON"""
    try:
        context = construir_knowledge_context()
        
        data = {
            "version": context.version,
            "timestamp": context.timestamp,
            "amenazas_magerit": context.amenazas_magerit,
            "controles_iso27002": context.controles_iso,
            "criterios_dic": context.criterios_dic,
            "few_shot_examples": context.few_shot_examples
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Error exportando KB: {e}")
        return False
