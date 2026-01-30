"""
SERVICIO DE IA PARA EVALUACIÓN MAGERIT
=======================================
Integración con Ollama para:
- Análisis de riesgo por activo
- Identificación de amenazas MAGERIT
- Recomendación de controles ISO 27002
- Validación JSON contra catálogos oficiales

El prompt fuerza respuestas JSON estructuradas.
La validación garantiza que solo se usen códigos del catálogo.

IMPORTANTE: Las DEGRADACIONES D/I/C se calculan por MOTOR (no IA)
usando el módulo degradacion_service.py con el catálogo MAGERIT v3.
"""
import json
import re
import requests
from typing import Dict, List, Optional, Tuple
import pandas as pd
from services.database_service import read_table

# Importar motor de degradación MAGERIT
from services.degradacion_service import (
    obtener_degradacion_motor,
    calcular_degradacion_amenazas,
    DEGRADACION_MAGERIT
)

# Importar contexto de entrenamiento MAGERIT
from services.ia_context_magerit import (
    get_contexto_completo_ia,
    get_amenazas_para_tipo_activo,
    get_controles_para_amenaza,
    construir_prompt_experto,
    MAPEO_AMENAZA_CONTROL,
    AMENAZAS_POR_TIPO_ACTIVO,
    DEGRADACION_TIPICA
)

# Importar contexto ENRIQUECIDO con todos los catálogos
from services.ia_context_enriquecido import get_contexto_completo_ia as get_contexto_enriquecido


# ==================== CONFIGURACIÓN ====================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO_DEFAULT = "llama3.2:1b"  # Usar modelo pequeño por defecto (más rápido)
TIMEOUT = 30  # Reducido a 30 segundos para fallar rápido

# Importar monitor de Ollama para garantizar disponibilidad 100%
from services.ollama_monitor import (
    verificar_ollama_disponible as verificar_ollama_con_monitor,
    llamar_ollama_con_reintentos,
    obtener_estado_sistema as obtener_estado_ollama
)


# ==================== CONTEXTO DE APLICACIONES CRÍTICAS UDLA ====================

APLICACIONES_CRITICAS_CONTEXTO = {
    "Banner": {
        "descripcion": "Sistema de Información Estudiantil (SIS) que almacena toda la información de estudiantes, docentes, personal administrativo, matrículas, calificaciones históricas, expedientes académicos y datos personales sensibles.",
        "datos_sensibles": ["Datos personales de estudiantes", "Calificaciones", "Historial académico", "Información de docentes", "Datos de contacto"],
        "impacto_negocio": "CRÍTICO - Afecta operaciones académicas completas",
        "usuarios": "Estudiantes, Docentes, Personal Administrativo",
        "amenazas_principales": ["Acceso no autorizado", "Fuga de datos personales", "Ransomware", "Inyección SQL"]
    },
    "Carpeta Online": {
        "descripcion": "Plataforma de almacenamiento y distribución de materiales académicos donde se almacenan datos de clases, horarios, syllabus, materiales de estudio y documentos compartidos entre docentes y estudiantes.",
        "datos_sensibles": ["Materiales académicos", "Horarios de clases", "Documentos de docentes", "Recursos educativos"],
        "impacto_negocio": "ALTO - Afecta continuidad de clases y acceso a materiales",
        "usuarios": "Docentes, Estudiantes",
        "amenazas_principales": ["Pérdida de datos", "Acceso no autorizado", "Malware en archivos", "Indisponibilidad del servicio"]
    },
    "D2L": {
        "descripcion": "Desire2Learn - Aula Virtual institucional donde se suben trabajos, pruebas, exámenes, calificaciones y se realiza toda la interacción académica virtual. Sistema crítico para educación híbrida y online.",
        "datos_sensibles": ["Calificaciones", "Exámenes", "Trabajos de estudiantes", "Retroalimentación docente", "Foros de discusión"],
        "impacto_negocio": "CRÍTICO - Paraliza educación virtual completamente",
        "usuarios": "Estudiantes, Docentes, Coordinadores académicos",
        "amenazas_principales": ["Indisponibilidad en época de exámenes", "Alteración de calificaciones", "Plagio/Integridad académica", "DDoS"]
    },
    "Página Web": {
        "descripcion": "Portal web institucional público de la universidad con información de carreras, admisiones, noticias, eventos y servicios. Representa la imagen pública de la institución.",
        "datos_sensibles": ["Información pública institucional", "Formularios de contacto", "Datos de prospectos"],
        "impacto_negocio": "MEDIO - Afecta imagen institucional y captación de estudiantes",
        "usuarios": "Público general, Prospectos, Comunidad universitaria",
        "amenazas_principales": ["Defacement", "DDoS", "Inyección de código", "SEO Spam"]
    },
    "Portal de Pagos": {
        "descripcion": "Sistema de pagos en línea que registra todas las transacciones financieras, matrículas, colegiaturas, pagos de servicios y estados de cuenta de estudiantes. Maneja datos financieros sensibles.",
        "datos_sensibles": ["Datos de tarjetas de crédito", "Información bancaria", "Estados de cuenta", "Historial de pagos", "Datos fiscales"],
        "impacto_negocio": "CRÍTICO - Afecta ingresos y operación financiera",
        "usuarios": "Estudiantes, Padres de familia, Área de Cobranza",
        "amenazas_principales": ["Fraude financiero", "Robo de datos de tarjetas", "PCI-DSS incumplimiento", "Phishing"]
    },
    "BX": {
        "descripcion": "Biblioteca Digital institucional que provee acceso a recursos bibliográficos, bases de datos académicas, revistas científicas, e-books y material de investigación para la comunidad universitaria.",
        "datos_sensibles": ["Historial de consultas", "Préstamos digitales", "Accesos a bases de datos"],
        "impacto_negocio": "MEDIO - Afecta investigación y recursos académicos",
        "usuarios": "Estudiantes, Docentes, Investigadores",
        "amenazas_principales": ["Acceso no autorizado a recursos pagados", "Descarga masiva ilegal", "Indisponibilidad de recursos"]
    },
    "Uni+": {
        "descripcion": "Aplicación móvil institucional que permite a estudiantes generar códigos de ingreso al campus, consultar horarios, calificaciones, notificaciones push y servicios universitarios desde el celular.",
        "datos_sensibles": ["Credenciales de acceso", "Códigos de ingreso físico", "Ubicación", "Datos personales"],
        "impacto_negocio": "ALTO - Afecta acceso físico al campus y servicios móviles",
        "usuarios": "Estudiantes, Personal",
        "amenazas_principales": ["Suplantación de identidad", "Acceso físico no autorizado", "Robo de credenciales", "Vulnerabilidades en app móvil"]
    },
    "Aprovisionamiento de Cuentas": {
        "descripcion": "Sistema de gestión de identidades (IAM) que automatiza la creación, modificación y eliminación de cuentas de usuario en todos los sistemas institucionales. Controla accesos y privilegios.",
        "datos_sensibles": ["Credenciales de usuarios", "Permisos de acceso", "Roles y privilegios", "Directorio de identidades"],
        "impacto_negocio": "CRÍTICO - Afecta acceso a todos los sistemas institucionales",
        "usuarios": "TI, Recursos Humanos, Administración",
        "amenazas_principales": ["Escalación de privilegios", "Cuentas huérfanas", "Acceso indebido", "Fallas en desprovisión"]
    },
    "UniAutorization": {
        "descripcion": "Sistema centralizado de autorización y control de acceso que gestiona permisos, roles y políticas de acceso a los diferentes sistemas y recursos institucionales basado en el principio de mínimo privilegio.",
        "datos_sensibles": ["Políticas de acceso", "Matrices de permisos", "Logs de autorización", "Configuración de roles"],
        "impacto_negocio": "CRÍTICO - Controla seguridad de acceso a toda la infraestructura",
        "usuarios": "Seguridad TI, Administradores de sistemas",
        "amenazas_principales": ["Bypass de controles", "Configuración incorrecta", "Falta de segregación de funciones"]
    },
    "SAP": {
        "descripcion": "Sistema ERP (Enterprise Resource Planning) que gestiona procesos financieros, contabilidad, recursos humanos, nómina, compras, inventarios y operaciones administrativas de toda la universidad.",
        "datos_sensibles": ["Información financiera", "Datos de nómina", "Información de proveedores", "Contratos", "Datos fiscales"],
        "impacto_negocio": "CRÍTICO - Afecta operaciones administrativas y financieras completas",
        "usuarios": "Finanzas, RRHH, Compras, Dirección",
        "amenazas_principales": ["Fraude interno", "Acceso no autorizado a datos financieros", "Ransomware", "Manipulación de datos contables"]
    }
}

def get_contexto_aplicacion_critica(nombre_app: str) -> Dict:
    """Obtiene el contexto de una aplicación crítica para uso en evaluación de riesgos"""
    return APLICACIONES_CRITICAS_CONTEXTO.get(nombre_app, {})


# ==================== CARGA DE CATÁLOGOS ====================

def get_catalogo_amenazas() -> Dict[str, Dict]:
    """Carga el catálogo de amenazas MAGERIT desde SQLite"""
    try:
        df = read_table("CATALOGO_AMENAZAS_MAGERIT")
        catalogo = {}
        for _, row in df.iterrows():
            codigo = row["codigo"]
            catalogo[codigo] = {
                "amenaza": row["amenaza"],
                "tipo_amenaza": row["tipo_amenaza"],
                "dimension_afectada": row.get("dimension_afectada", "D"),
                "descripcion": row.get("descripcion", "")
            }
        return catalogo
    except:
        return {}


def get_catalogo_controles() -> Dict[str, Dict]:
    """Carga el catálogo de controles ISO 27002 desde SQLite"""
    try:
        df = read_table("CATALOGO_CONTROLES_ISO27002")
        catalogo = {}
        for _, row in df.iterrows():
            codigo = row["codigo"]
            catalogo[codigo] = {
                "nombre": row["nombre"],
                "categoria": row["categoria"]
            }
        return catalogo
    except:
        return {}


def get_catalogo_vulnerabilidades() -> Dict[str, Dict]:
    """
    Carga el catálogo de vulnerabilidades MAGERIT desde JSON.
    Retorna un diccionario con todas las vulnerabilidades organizadas por tipo de activo.
    """
    try:
        import os
        ruta_json = os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "vulnerabilidades_magerit.json")
        with open(ruta_json, "r", encoding="utf-8") as f:
            catalogo = json.load(f)
        return catalogo
    except Exception as e:
        print(f"Error cargando catálogo de vulnerabilidades: {e}")
        return {}


def obtener_vulnerabilidades_por_tipo(tipo_activo: str) -> List[Dict]:
    """
    Obtiene las vulnerabilidades aplicables a un tipo de activo específico.
    
    Args:
        tipo_activo: Tipo del activo (ej: "Servidor Virtual", "Aplicación Web")
    
    Returns:
        Lista de diccionarios con vulnerabilidades aplicables
    """
    catalogo = get_catalogo_vulnerabilidades()
    if not catalogo:
        return []
    
    # Mapeo de tipos de activos a categorías del catálogo
    tipo_lower = tipo_activo.lower()
    
    if any(x in tipo_lower for x in ["servidor", "equipo", "hardware", "físico", "switch", "router"]):
        categoria = "HW"
    elif any(x in tipo_lower for x in ["software", "aplicación", "aplicacion", "app", "sistema", "banner", "d2l"]):
        categoria = "SW"
    elif any(x in tipo_lower for x in ["red", "comunicación", "comunicacion", "firewall", "vpn", "wifi"]):
        categoria = "COM"
    elif any(x in tipo_lower for x in ["datos", "información", "informacion", "base de datos", "bd"]):
        categoria = "D"
    elif any(x in tipo_lower for x in ["servicio", "aula virtual", "portal"]):
        categoria = "S"
    elif any(x in tipo_lower for x in ["personal", "usuario", "empleado"]):
        categoria = "PS"
    elif any(x in tipo_lower for x in ["instalación", "instalacion", "edificio", "datacenter"]):
        categoria = "L"
    elif any(x in tipo_lower for x in ["ups", "generador", "aire", "auxiliar"]):
        categoria = "AUX"
    else:
        # Por defecto, devolver vulnerabilidades de SW si no se identifica
        categoria = "SW"
    
    if categoria in catalogo:
        return catalogo[categoria]["vulnerabilidades"]
    else:
        return []


# ==================== CONTEXTO DEL ACTIVO ====================

def construir_contexto_activo(
    activo: pd.Series,
    respuestas: pd.DataFrame
) -> str:
    """
    Construye el contexto textual de un activo para el prompt de IA.
    Incluye datos del activo y resumen de respuestas del cuestionario.
    También incluye contexto de la aplicación crítica si aplica.
    """
    # Datos del activo
    contexto = f"""
## ACTIVO A EVALUAR
- **ID**: {activo.get("ID_Activo", "")}
- **Nombre**: {activo.get("Nombre_Activo", "")}
- **Tipo**: {activo.get("Tipo_Activo", "")}
- **Descripción**: {activo.get("Descripcion", "")}
- **Propietario**: {activo.get("Propietario", "")}
- **Criticidad**: {activo.get("Criticidad", "")}
- **Ubicación**: {activo.get("Ubicacion", "")}
"""
    
    # Agregar contexto de aplicación crítica si existe
    app_critica = activo.get("App_Critica", "")
    if app_critica and app_critica not in ["No", "No Aplica", "", None]:
        contexto_app = get_contexto_aplicacion_critica(app_critica)
        if contexto_app:
            contexto += f"""
## APLICACIÓN CRÍTICA ASOCIADA: {app_critica}
- **Descripción**: {contexto_app.get('descripcion', '')}
- **Datos Sensibles**: {', '.join(contexto_app.get('datos_sensibles', []))}
- **Impacto de Negocio**: {contexto_app.get('impacto_negocio', '')}
- **Usuarios Afectados**: {contexto_app.get('usuarios', '')}
- **Amenazas Principales Conocidas**: {', '.join(contexto_app.get('amenazas_principales', []))}
"""
    
    # Resumen de respuestas por bloque
    if not respuestas.empty:
        contexto += "\n## RESPUESTAS DEL CUESTIONARIO BIA\n"
        
        # Agrupar por dimensión
        for dimension in ["D", "I", "C"]:
            resp_dim = respuestas[respuestas.get("Dimension", "") == dimension]
            if not resp_dim.empty:
                dim_nombre = {
                    "D": "Disponibilidad",
                    "I": "Integridad", 
                    "C": "Confidencialidad"
                }.get(dimension, dimension)
                
                contexto += f"\n### {dim_nombre}\n"
                for _, resp in resp_dim.iterrows():
                    pregunta = resp.get("Pregunta", "")
                    valor = resp.get("Valor_Numerico", 0)
                    texto = resp.get("Respuesta_Texto", "")
                    nivel = "Bajo" if valor <= 2 else "Alto"
                    contexto += f"- {pregunta}: **{nivel}** ({texto})\n"
    
    return contexto


# ==================== PROMPT ESTRUCTURADO ====================

def construir_prompt_magerit(
    contexto_activo: str,
    catalogo_amenazas: Dict[str, Dict],
    catalogo_controles: Dict[str, Dict]
) -> str:
    """
    Construye el prompt ENRIQUECIDO para que la IA analice el activo.
    
    NUEVA VERSIÓN: Usa el contexto completo con:
    - 52 amenazas MAGERIT con descripciones completas
    - 93 controles ISO 27002 con descripciones completas
    - 64 vulnerabilidades específicas por tipo
    - 7 aplicaciones críticas UDLA
    - Mapeos amenazas → controles
    - Degradaciones calibradas
    - Ejemplos de análisis correcto
    """
    # Obtener el contexto COMPLETO enriquecido
    contexto_base = get_contexto_enriquecido()
    
    # Construir prompt final con información del activo
    prompt = f"""{contexto_base}

---

## ACTIVO A ANALIZAR

{contexto_activo}

---

## TU TAREA

Analiza el activo proporcionado usando TODO el conocimiento disponible y genera una evaluación precisa.

**PASOS:**
1. Identifica el tipo de activo (aplicación, servidor, base de datos, etc.)
2. Revisa las respuestas BIA para entender su criticidad real
3. Identifica 3-7 amenazas MAGERIT más relevantes del catálogo
4. Para cada amenaza, determina la dimensión afectada (D/I/C)
5. Recomienda 1-3 controles ISO 27002 que mitigan cada amenaza
6. Calcula probabilidad general (1-5) según los controles existentes
7. Genera observaciones específicas y accionables

**RESPONDE CON JSON:**

```json
{{
  "probabilidad": 3,
  "amenazas": [
    {{
      "codigo": "A.24",
      "dimension": "D",
      "justificacion": "Explicación específica basada en las vulnerabilidades del activo",
      "controles_iso_recomendados": [
        {{
          "control": "8.20",
          "prioridad": "Alta",
          "motivo": "Cómo este control específico mitiga esta amenaza específica"
        }}
      ]
    }}
  ],
  "observaciones": "Análisis del perfil de riesgo con recomendaciones prioritarias"
}}
```

**IMPORTANTE:**
- USA SOLO códigos del catálogo (no inventes)
- Justificaciones específicas al activo (no genéricas)
- Controles deben mapear directamente a la amenaza
- Prioridades: "Alta", "Media", "Baja"
- Probabilidad: 1-5
- Dimensiones: D, I, C

Responde SOLO con el JSON, sin texto adicional:"""
    
    return prompt


# ==================== EVALUACIÓN HEURÍSTICA (FALLBACK) ====================

# ==================== ESCALA INTERNA MAGERIT v3 (CALIBRADA) ====================
ESCALA_MAGERIT = {1: 1, 2: 2, 3: 3, 4: 5}  # CALIBRADO: 3→3 en lugar de 3→4

def calcular_probabilidad_desde_respuestas(respuestas: pd.DataFrame) -> int:
    """
    Calcula la probabilidad MAGERIT (1-5) basándose en las respuestas del cuestionario.
    
    LÓGICA SIMPLIFICADA Y PREDECIBLE:
    - La probabilidad se calcula desde el promedio de los controles (bloques B, C, D, E)
    - Valor bajo en controles (1) = sin protección = probabilidad ALTA (5)
    - Valor alto en controles (4) = buena protección = probabilidad BAJA (1)
    - Se invierte la escala: promedio_controles → probabilidad invertida
    
    MAPEO:
    - Controles promedio 1.0-1.5 → Probabilidad 5 (Muy frecuente)
    - Controles promedio 1.5-2.0 → Probabilidad 4 (Frecuente)  
    - Controles promedio 2.0-2.5 → Probabilidad 3 (Normal)
    - Controles promedio 2.5-3.5 → Probabilidad 2 (Poco frecuente)
    - Controles promedio 3.5-4.0 → Probabilidad 1 (Muy raro)
    
    Returns:
        Probabilidad 1-5 según MAGERIT
    """
    if respuestas.empty:
        return 3  # Valor medio por defecto
    
    # Identificar preguntas de CONTROL (bloques B, C, D, E)
    # Estas son las que afectan la probabilidad
    valores_control = []
    
    for _, resp in respuestas.iterrows():
        id_pregunta = str(resp.get("ID_Pregunta", "")).upper()
        valor = int(resp.get("Valor_Numerico", 2))
        
        # Detectar si es pregunta de control (B, C, D, E)
        # Formatos: PF-B01, PV-B01, B-001, B01, etc.
        es_control = False
        for bloque in ['B', 'C', 'D', 'E']:
            if f"-{bloque}0" in id_pregunta or f"-{bloque}-0" in id_pregunta:
                es_control = True
                break
        
        if es_control:
            valores_control.append(valor)
    
    # Si no hay preguntas de control, usar probabilidad media
    if not valores_control:
        return 3
    
    # Calcular promedio de controles
    promedio_controles = sum(valores_control) / len(valores_control)
    
    # Mapear promedio a probabilidad (escala invertida)
    # Mejor control (4) → menor probabilidad (1)
    # Peor control (1) → mayor probabilidad (5)
    if promedio_controles >= 3.5:
        probabilidad = 1  # Muy raro - excelentes controles
    elif promedio_controles >= 2.75:
        probabilidad = 2  # Poco frecuente - buenos controles
    elif promedio_controles >= 2.25:
        probabilidad = 3  # Normal - controles moderados
    elif promedio_controles >= 1.5:
        probabilidad = 4  # Frecuente - controles débiles
    else:
        probabilidad = 5  # Muy frecuente - sin controles
    
    return probabilidad


def generar_evaluacion_heuristica(
    activo: pd.Series,
    respuestas: pd.DataFrame,
    catalogo_amenazas: Dict[str, Dict],
    catalogo_controles: Dict[str, Dict]
) -> Dict:
    """
    Genera una evaluación MAGERIT heurística cuando la IA falla.
    
    MAGERIT v3 - Lógica mejorada:
    - Selecciona amenazas según tipo de activo
    - Calcula probabilidad REAL desde respuestas (no hardcodeada)
    - Prioriza controles según gravedad
    """
    tipo_activo = str(activo.get("Tipo_Activo", "")).lower()
    
    # Mapeo de tipos de activo a amenazas típicas (ordenadas por criticidad)
    AMENAZAS_POR_TIPO = {
        "servidor": ["A.24", "A.11", "A.8", "A.5", "A.6", "E.2", "I.5"],
        "físico": ["A.24", "A.11", "A.8", "A.5", "A.25", "I.5", "N.1"],
        "virtual": ["A.24", "A.11", "A.8", "A.5", "A.6", "E.2", "I.9"],
        "base de datos": ["A.5", "A.6", "A.11", "A.15", "A.19", "E.1", "E.2"],
        "aplicación": ["A.5", "A.6", "A.8", "A.22", "E.1", "E.21"],
        "red": ["A.5", "A.9", "A.14", "A.24", "I.8", "E.9"],
        "usuario": ["A.30", "E.1", "E.2", "E.7", "E.15"],
        "documento": ["A.11", "A.15", "A.19", "E.1", "E.2"],
        "equipo": ["N.1", "N.2", "I.5", "A.25", "E.23"],
        "software": ["A.5", "A.6", "A.8", "A.22", "E.20", "E.21"],
    }
    
    # Mapeo de amenazas a controles típicos con prioridad
    CONTROLES_POR_AMENAZA = {
        "A.5": [("5.15", "Alta"), ("5.16", "Alta"), ("8.5", "Media")],
        "A.6": [("5.15", "Alta"), ("5.17", "Alta"), ("8.4", "Media")],
        "A.8": [("8.7", "Alta"), ("8.8", "Alta"), ("8.23", "Media")],
        "A.11": [("5.15", "Alta"), ("8.5", "Alta"), ("7.7", "Media")],
        "A.24": [("8.20", "Alta"), ("8.21", "Alta"), ("8.6", "Media")],
        "A.25": [("7.1", "Alta"), ("7.2", "Alta"), ("7.4", "Media")],
        "E.1": [("6.3", "Alta"), ("5.10", "Media"), ("8.9", "Media")],
        "E.2": [("6.3", "Alta"), ("8.9", "Alta"), ("8.2", "Media")],
        "I.5": [("7.11", "Alta"), ("8.14", "Alta"), ("7.13", "Media")],
        "I.9": [("5.19", "Alta"), ("5.22", "Media"), ("8.14", "Media")],
        "N.1": [("7.5", "Alta"), ("5.29", "Alta"), ("5.30", "Media")],
    }
    
    # Determinar amenazas aplicables
    amenazas_aplicables = []
    for key, codigos in AMENAZAS_POR_TIPO.items():
        if key in tipo_activo:
            amenazas_aplicables = codigos
            break
    
    if not amenazas_aplicables:
        # Default: amenazas genéricas para servidores
        amenazas_aplicables = ["A.24", "A.11", "A.8", "A.5", "E.2"]
    
    # CALCULAR PROBABILIDAD REAL desde respuestas (NO hardcodeada)
    probabilidad = calcular_probabilidad_desde_respuestas(respuestas)
    
    # Construir resultado con amenazas
    amenazas_resultado = []
    for codigo in amenazas_aplicables[:6]:  # Máximo 6 amenazas
        if codigo in catalogo_amenazas:
            info = catalogo_amenazas[codigo]
            controles_info = CONTROLES_POR_AMENAZA.get(codigo, [("5.1", "Media"), ("8.1", "Media")])[:3]
            controles_rec = []
            for ctrl_codigo, prioridad in controles_info:
                if ctrl_codigo in catalogo_controles:
                    controles_rec.append({
                        "control": ctrl_codigo,
                        "prioridad": prioridad,
                        "motivo": f"Control recomendado para mitigar amenaza {codigo}"
                    })
            
            # Determinar dimensión correctamente
            dim_raw = info.get("dimension_afectada", "D")
            if isinstance(dim_raw, str) and len(dim_raw) > 0:
                dimension = dim_raw[0].upper()
            else:
                dimension = "D"
            
            amenazas_resultado.append({
                "codigo": codigo,
                "dimension": dimension,
                "justificacion": f"Amenaza identificada para {tipo_activo} con probabilidad {probabilidad}/5",
                "controles_iso_recomendados": controles_rec
            })
    
    return {
        "probabilidad": probabilidad,  # Probabilidad CALCULADA, no hardcodeada
        "amenazas": amenazas_resultado,
        "observaciones": f"Evaluación heurística para {tipo_activo}. Probabilidad calculada: {probabilidad}/5 basada en exposición e historial."
    }


# ==================== LLAMADA A OLLAMA ====================

def llamar_ollama(prompt: str, modelo: str = None) -> Tuple[bool, str]:
    """
    Llama a Ollama y obtiene la respuesta.
    CON REINTENTOS AUTOMÁTICOS Y RECUPERACIÓN para garantizar 100% disponibilidad.
    
    Returns:
        (éxito: bool, respuesta_o_error: str)
    """
    # Usar el sistema de reintentos automáticos del monitor
    return llamar_ollama_con_reintentos(prompt, modelo or MODELO_DEFAULT)
    modelo_usar = modelo or MODELO_DEFAULT
    
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": modelo_usar,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Más determinista
                    "num_predict": 2000
                }
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            resultado = response.json()
            return True, resultado.get("response", "")
        else:
            return False, f"Error HTTP {response.status_code}: {response.text}"
    
    except requests.exceptions.ConnectionError:
        return False, "No se pudo conectar con Ollama. Verifica que esté ejecutándose."
    except requests.exceptions.Timeout:
        return False, f"Timeout después de {TIMEOUT} segundos"
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"


# ==================== PARSING Y VALIDACIÓN ====================

def extraer_json_de_respuesta(respuesta: str) -> Optional[str]:
    """Extrae el bloque JSON de la respuesta de la IA"""
    
    # Intentar extraer JSON entre ```json y ```
    match = re.search(r'```json\s*([\s\S]*?)\s*```', respuesta)
    if match:
        return match.group(1).strip()
    
    # Intentar extraer JSON entre ``` y ```
    match = re.search(r'```\s*([\s\S]*?)\s*```', respuesta)
    if match:
        contenido = match.group(1).strip()
        # Verificar si es JSON válido
        if contenido.startswith('{'):
            return contenido
    
    # Manejar caso donde IA retorna JavaScript: const request = {...};
    match = re.search(r'(?:const|let|var)\s+\w+\s*=\s*(\{[\s\S]*?\});', respuesta)
    if match:
        return match.group(1).strip()
    
    # Intentar encontrar objeto JSON directo (el primer { hasta el último })
    match = re.search(r'(\{[\s\S]*\})', respuesta)
    if match:
        json_str = match.group(1).strip()
        # Limpiar posibles caracteres extra al final
        # Encontrar el cierre correcto del JSON
        depth = 0
        for i, char in enumerate(json_str):
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return json_str[:i+1]
        return json_str
    
    return None


def validar_respuesta_ia(
    respuesta_json: Dict,
    catalogo_amenazas: Dict[str, Dict],
    catalogo_controles: Dict[str, Dict]
) -> Tuple[bool, Dict, List[str]]:
    """
    Valida que la respuesta de la IA use solo códigos del catálogo.
    
    Returns:
        (válido: bool, respuesta_limpia: Dict, errores: List[str])
    """
    errores = []
    respuesta_limpia = {
        "probabilidad": 3,
        "amenazas": [],
        "observaciones": ""
    }
    
    # Validar probabilidad
    prob = respuesta_json.get("probabilidad", 3)
    if isinstance(prob, int) and 1 <= prob <= 5:
        respuesta_limpia["probabilidad"] = prob
    else:
        errores.append(f"Probabilidad inválida: {prob}")
        respuesta_limpia["probabilidad"] = 3
    
    # Validar observaciones (manejar variantes de nombre)
    obs = respuesta_json.get("observaciones", "") or respuesta_json.get("observation", "") or respuesta_json.get("summary", "")
    respuesta_limpia["observaciones"] = str(obs)
    
    # Validar amenazas (manejar nombres alternativos que la IA podría usar)
    amenazas = (
        respuesta_json.get("amenazas", []) or 
        respuesta_json.get("amenaza_sugeridas", []) or
        respuesta_json.get("threats", []) or
        respuesta_json.get("amenazas_identificadas", []) or
        []
    )
    if not isinstance(amenazas, list):
        errores.append("'amenazas' debe ser una lista")
        amenazas = []
    
    for i, amenaza in enumerate(amenazas):
        codigo = amenaza.get("codigo", "") or amenaza.get("code", "") or amenaza.get("threat_code", "")
        
        # Validar código de amenaza
        if codigo not in catalogo_amenazas:
            errores.append(f"Amenaza[{i}]: código '{codigo}' no existe en catálogo")
            continue
        
        # Validar dimensión (manejar variantes: dimension, dimensión)
        dimension = str(
            amenaza.get("dimension", "") or 
            amenaza.get("dimensión", "") or 
            "D"
        ).upper()
        if dimension not in ["D", "I", "C"]:
            errores.append(f"Amenaza[{i}]: dimensión '{dimension}' inválida")
            dimension = "D"
        
        # Procesar controles (manejar variantes de nombres)
        controles_validos = []
        controles_rec = (
            amenaza.get("controles_iso_recomendados", []) or
            amenaza.get("controles_iso_recomendado", []) or
            amenaza.get("controls", []) or
            amenaza.get("controles", []) or
            []
        )
        if not isinstance(controles_rec, list):
            controles_rec = []
        
        for j, ctrl in enumerate(controles_rec):
            codigo_ctrl = str(ctrl.get("control", "") or ctrl.get("codigo", "") or ctrl.get("code", ""))
            if codigo_ctrl not in catalogo_controles:
                errores.append(f"Amenaza[{i}].Control[{j}]: '{codigo_ctrl}' no existe en catálogo")
                continue
            
            prioridad = str(ctrl.get("prioridad", "Media"))
            if prioridad not in ["Alta", "Media", "Baja"]:
                prioridad = "Media"
            
            controles_validos.append({
                "control": codigo_ctrl,
                "prioridad": prioridad,
                "motivo": str(ctrl.get("motivo", ""))
            })
        
        # Agregar amenaza validada
        justificacion = str(
            amenaza.get("justificacion", "") or
            amenaza.get("justificación", "") or
            amenaza.get("reason", "") or
            ""
        )
        respuesta_limpia["amenazas"].append({
            "codigo": codigo,
            "dimension": dimension,
            "justificacion": justificacion,
            "controles_iso_recomendados": controles_validos
        })
    
    es_valido = len(respuesta_limpia["amenazas"]) > 0
    if not es_valido:
        errores.append("No se identificaron amenazas válidas")
    
    return es_valido, respuesta_limpia, errores


# ==================== FUNCIÓN PRINCIPAL ====================

def analizar_activo_con_ia(
    eval_id: str,
    activo_id: str,
    modelo: str = None
) -> Tuple[bool, Dict, str]:
    """
    Analiza un activo usando IA y retorna la evaluación MAGERIT.
    
    Args:
        eval_id: ID de la evaluación
        activo_id: ID del activo
        modelo: Modelo de Ollama a usar (opcional)
    
    Returns:
        (éxito: bool, resultado: Dict, mensaje: str)
    """
    modelo_usar = modelo or MODELO_DEFAULT
    
    # 1. Cargar catálogos
    catalogo_amenazas = get_catalogo_amenazas()
    catalogo_controles = get_catalogo_controles()
    
    if not catalogo_amenazas:
        return False, {}, "Error: Catálogo de amenazas no cargado. Ejecute seed_catalogos_magerit.py"
    if not catalogo_controles:
        return False, {}, "Error: Catálogo de controles no cargado. Ejecute seed_catalogos_magerit.py"
    
    # 2. Obtener datos del activo
    activos = read_table("INVENTARIO_ACTIVOS")
    activo = activos[activos["ID_Activo"] == activo_id]
    if activo.empty:
        return False, {}, f"Activo {activo_id} no encontrado"
    activo = activo.iloc[0]
    
    # 3. Obtener respuestas del cuestionario
    respuestas = read_table("RESPUESTAS")
    respuestas_activo = respuestas[
        (respuestas["ID_Evaluacion"] == eval_id) &
        (respuestas["ID_Activo"] == activo_id)
    ]
    
    # 4. Construir contexto y prompt
    contexto = construir_contexto_activo(activo, respuestas_activo)
    prompt = construir_prompt_magerit(contexto, catalogo_amenazas, catalogo_controles)
    
    # 5. Llamar a Ollama
    exito, respuesta_texto = llamar_ollama(prompt, modelo_usar)
    
    usa_fallback = False
    respuesta_limpia = None
    errores = []
    
    if not exito:
        # La IA falló, usar fallback heurístico
        usa_fallback = True
    else:
        # 6. Extraer JSON
        json_texto = extraer_json_de_respuesta(respuesta_texto)
        if not json_texto:
            usa_fallback = True
        else:
            # 7. Parsear JSON
            try:
                respuesta_json = json.loads(json_texto)
                # 8. Validar contra catálogos
                es_valido, respuesta_limpia, errores = validar_respuesta_ia(
                    respuesta_json, catalogo_amenazas, catalogo_controles
                )
                if not es_valido:
                    usa_fallback = True
            except json.JSONDecodeError:
                usa_fallback = True
    
    # Si la IA falló, usar evaluación heurística
    if usa_fallback:
        respuesta_limpia = generar_evaluacion_heuristica(
            activo, respuestas_activo, catalogo_amenazas, catalogo_controles
        )
        respuesta_limpia["modelo_ia"] = f"{modelo_usar} (fallback heurístico)"
        respuesta_limpia["errores_validacion"] = ["IA no disponible o respuesta inválida - se usó evaluación heurística"]
        mensaje = f"Análisis heurístico: {len(respuesta_limpia['amenazas'])} amenazas identificadas (IA no disponible)"
        return True, respuesta_limpia, mensaje
    
    # 9. Agregar metadata
    respuesta_limpia["modelo_ia"] = modelo_usar
    respuesta_limpia["errores_validacion"] = errores
    
    mensaje = f"Análisis IA completado: {len(respuesta_limpia['amenazas'])} amenazas identificadas"
    if errores:
        mensaje += f" ({len(errores)} códigos corregidos)"
    
    return True, respuesta_limpia, mensaje


def verificar_ollama_disponible() -> Tuple[bool, List[str]]:
    """
    Verifica si Ollama está disponible y lista los modelos.
    CON AUTO-RECUPERACIÓN integrada para garantizar 100% disponibilidad.
    
    Returns:
        (disponible: bool, modelos: List[str])
    """
    # Usar el monitor con auto-recuperación
    return verificar_ollama_con_monitor()


# ==================== RESPUESTA MANUAL (SIN IA) ====================

def crear_evaluacion_manual(
    activo: pd.Series,
    amenazas_seleccionadas: List[str],
    probabilidad: int,
    observaciones: str
) -> Dict:
    """
    Crea una estructura de evaluación manual (sin IA).
    
    Args:
        activo: Series con datos del activo
        amenazas_seleccionadas: Lista de códigos de amenazas
        probabilidad: Probabilidad 1-5
        observaciones: Texto libre
    
    Returns:
        Dict con estructura compatible con el motor MAGERIT
    """
    catalogo_amenazas = get_catalogo_amenazas()
    
    amenazas = []
    for codigo in amenazas_seleccionadas:
        if codigo in catalogo_amenazas:
            info = catalogo_amenazas[codigo]
            amenazas.append({
                "codigo": codigo,
                "dimension": info.get("dimension_afectada", "D")[0],  # Primera letra
                "justificacion": f"Selección manual para {activo.get('Nombre_Activo', '')}",
                "controles_iso_recomendados": []
            })
    
    return {
        "probabilidad": min(5, max(1, probabilidad)),
        "amenazas": amenazas,
        "observaciones": observaciones,
        "modelo_ia": "manual"
    }


# ==================== ANÁLISIS DE AMENAZAS POR CRITICIDAD (IA) ====================

def construir_prompt_amenazas_criticidad(
    activo_info: Dict,
    valoracion: Dict,
    catalogo_amenazas: Dict[str, Dict]
) -> str:
    """
    Construye el prompt para identificar amenazas/vulnerabilidades basándose en la criticidad.
    MEJORADO: Usa el contexto de entrenamiento MAGERIT completo.
    """
    tipo_activo = str(activo_info.get("Tipo_Activo", "")).lower()
    
    # Obtener amenazas típicas para este tipo de activo del contexto de entrenamiento
    amenazas_tipicas = get_amenazas_para_tipo_activo(tipo_activo)
    amenazas_tipicas_texto = "\n".join([f"  - {a}" for a in amenazas_tipicas])
    
    # Obtener contexto completo de MAGERIT
    contexto_magerit = get_contexto_completo_ia()
    
    # Preparar lista de amenazas por tipo del catálogo
    amenazas_por_tipo = {}
    for codigo, info in catalogo_amenazas.items():
        tipo = info.get("tipo_amenaza", "Otros")
        if tipo not in amenazas_por_tipo:
            amenazas_por_tipo[tipo] = []
        amenazas_por_tipo[tipo].append(f"{codigo}: {info['amenaza']}")
    
    amenazas_texto = ""
    for tipo, lista in amenazas_por_tipo.items():
        amenazas_texto += f"\n**{tipo}:**\n"
        for a in lista:
            amenazas_texto += f"  - {a}\n"
    
    # Obtener degradaciones típicas por categoría
    degradacion_info = ""
    for categoria, rangos in DEGRADACION_TIPICA.items():
        degradacion_info += f"  - {categoria}: D={rangos['D']}%, I={rangos['I']}%, C={rangos['C']}%\n"
    
    prompt = f"""Eres un experto certificado en seguridad de la información y gestión de riesgos bajo la metodología MAGERIT v3 del CCN (Centro Criptológico Nacional de España).

## CONTEXTO METODOLÓGICO MAGERIT v3
{contexto_magerit}

## ACTIVO A ANALIZAR
- **ID**: {activo_info.get('ID_Activo', '')}
- **Nombre**: {activo_info.get('Nombre_Activo', '')}
- **Tipo**: {activo_info.get('Tipo_Activo', '')}
- **Descripción**: {activo_info.get('Descripcion', 'N/A')}
- **Ubicación**: {activo_info.get('Ubicacion', 'N/A')}

## VALORACIÓN D/I/C DEL ACTIVO
- **Disponibilidad (D)**: {valoracion.get('Valor_D', 0)} - Nivel: {valoracion.get('D', 'N')}
- **Integridad (I)**: {valoracion.get('Valor_I', 0)} - Nivel: {valoracion.get('I', 'N')}
- **Confidencialidad (C)**: {valoracion.get('Valor_C', 0)} - Nivel: {valoracion.get('C', 'N')}
- **CRITICIDAD**: {valoracion.get('Criticidad', 0)} - Nivel: {valoracion.get('Criticidad_Nivel', 'Sin valorar')}

## AMENAZAS TÍPICAS PARA ACTIVOS TIPO "{activo_info.get('Tipo_Activo', 'General').upper()}"
{amenazas_tipicas_texto}

## CATÁLOGO COMPLETO DE AMENAZAS MAGERIT v3 (USAR SOLO ESTOS CÓDIGOS)
{amenazas_texto}

## DEGRADACIÓN TÍPICA POR CATEGORÍA DE AMENAZA
{degradacion_info}

## TU TAREA
Basándote en la CRITICIDAD del activo, su tipo y la metodología MAGERIT v3, identifica las amenazas más relevantes.
Para cada amenaza, debes:
1. Indicar la VULNERABILIDAD específica que permite que la amenaza se materialice
2. Estimar la DEGRADACIÓN (0-100%) para D, I, C según la criticidad del activo y la categoría de amenaza

**Reglas para DEGRADACIÓN según CRITICIDAD:**
- Criticidad ALTA (>=3): Degradaciones altas (60-100%)
- Criticidad MEDIA (2): Degradaciones medias (30-60%)
- Criticidad BAJA (1): Degradaciones bajas (10-30%)
- Sin valorar (0): Degradación mínima (5-15%)

## FORMATO DE RESPUESTA OBLIGATORIO
Responde ÚNICAMENTE con un JSON válido:

```json
{{
  "amenazas_identificadas": [
    {{
      "codigo_amenaza": "A.24",
      "nombre_amenaza": "Denegación de servicio",
      "vulnerabilidad": "Descripción específica de la vulnerabilidad",
      "degradacion_d": 80,
      "degradacion_i": 20,
      "degradacion_c": 10,
      "justificacion": "Justificación técnica basada en MAGERIT"
    }}
  ],
  "resumen_analisis": "Resumen del análisis según metodología MAGERIT v3"
}}
```

## REGLAS CRÍTICAS OBLIGATORIAS
1. **SOLO usa códigos de amenaza del catálogo MAGERIT proporcionado (N.*, I.*, E.*, A.*)**
2. **Prioriza las amenazas típicas para el tipo de activo indicado**
3. **Identifica entre 3 y 7 amenazas relevantes** según el tipo y criticidad
4. **Las degradaciones deben ser números entre 0 y 100**
5. **Las vulnerabilidades deben ser específicas y técnicas**
6. **Aplica las fórmulas MAGERIT: Impacto = MAX(D×DegD, I×DegI, C×DegC)**

Responde SOLO con el JSON, sin explicaciones adicionales:"""
    
    return prompt


def analizar_amenazas_por_criticidad(
    activo_info: Dict,
    valoracion: Dict,
    modelo: str = None
) -> Tuple[bool, List[Dict], str]:
    """
    Usa la IA local para identificar amenazas y vulnerabilidades
    basándose en la criticidad del activo.
    
    Args:
        activo_info: Diccionario con información del activo
        valoracion: Diccionario con valoración D/I/C
        modelo: Modelo de Ollama a usar
    
    Returns:
        (éxito: bool, amenazas: List[Dict], mensaje: str)
    """
    modelo_usar = modelo or MODELO_DEFAULT
    
    # Datos para el motor de degradación
    tipo_activo = str(activo_info.get("Tipo_Activo", ""))
    criticidad = valoracion.get("Criticidad", 3)
    
    # Cargar catálogo de amenazas
    catalogo_amenazas = get_catalogo_amenazas()
    if not catalogo_amenazas:
        return False, [], "Error: Catálogo de amenazas no disponible"
    
    # Construir prompt
    prompt = construir_prompt_amenazas_criticidad(activo_info, valoracion, catalogo_amenazas)
    
    # Llamar a Ollama
    exito, respuesta_texto = llamar_ollama(prompt, modelo_usar)
    
    if not exito:
        # Usar fallback heurístico
        amenazas = generar_amenazas_heuristicas(activo_info, valoracion, catalogo_amenazas)
        # Recalcular degradaciones con MOTOR
        amenazas = calcular_degradacion_amenazas(amenazas, tipo_activo, criticidad)
        return True, amenazas, "Análisis heurístico + Motor MAGERIT (Ollama no disponible)"
    
    # Extraer JSON
    json_texto = extraer_json_de_respuesta(respuesta_texto)
    if not json_texto:
        amenazas = generar_amenazas_heuristicas(activo_info, valoracion, catalogo_amenazas)
        # Recalcular degradaciones con MOTOR
        amenazas = calcular_degradacion_amenazas(amenazas, tipo_activo, criticidad)
        return True, amenazas, "Análisis heurístico + Motor MAGERIT (respuesta IA inválida)"
    
    try:
        respuesta_json = json.loads(json_texto)
        amenazas_raw = respuesta_json.get("amenazas_identificadas", [])
        
        # Obtener vulnerabilidades del catálogo según tipo de activo
        vulnerabilidades_tipo = obtener_vulnerabilidades_por_tipo(activo_info.get("Tipo_Activo", ""))
        
        # Validar y limpiar amenazas (IA solo selecciona amenazas, MOTOR calcula degradación)
        amenazas_validas = []
        for idx, am in enumerate(amenazas_raw):
            codigo = am.get("codigo_amenaza", "")
            if codigo in catalogo_amenazas:
                # MOTOR MAGERIT calcula las degradaciones (no la IA)
                deg_d, deg_i, deg_c, justificacion = obtener_degradacion_motor(
                    codigo, tipo_activo, criticidad
                )
                
                # Obtener código de vulnerabilidad del catálogo
                vuln_texto_ia = am.get("vulnerabilidad", "Vulnerabilidad no especificada")
                if vulnerabilidades_tipo:
                    # Buscar la vulnerabilidad más similar o usar la primera
                    vuln_idx = idx % len(vulnerabilidades_tipo)
                    vuln_catalogo = vulnerabilidades_tipo[vuln_idx]
                    cod_vuln = vuln_catalogo["codigo"]
                    vulnerabilidad_completa = f"{vuln_catalogo['nombre']}: {vuln_catalogo['descripcion']}"
                else:
                    cod_vuln = f"V{idx+1:03d}"
                    vulnerabilidad_completa = vuln_texto_ia
                
                amenazas_validas.append({
                    "codigo_amenaza": codigo,
                    "codigo_vulnerabilidad": cod_vuln,
                    "nombre_amenaza": am.get("nombre_amenaza", catalogo_amenazas[codigo]["amenaza"]),
                    "vulnerabilidad": vulnerabilidad_completa,
                    "degradacion_d": int(deg_d * 100),
                    "degradacion_i": int(deg_i * 100),
                    "degradacion_c": int(deg_c * 100),
                    "justificacion": justificacion,
                    "justificacion_ia": am.get("justificacion", ""),
                    "tipo_amenaza": catalogo_amenazas[codigo].get("tipo_amenaza", ""),
                    "fuente_degradacion": "MOTOR_MAGERIT"
                })
        
        if amenazas_validas:
            resumen = respuesta_json.get("resumen_analisis", "")
            return True, amenazas_validas, f"IA identificó {len(amenazas_validas)} amenazas. Degradación por Motor MAGERIT. {resumen}"
        else:
            amenazas = generar_amenazas_heuristicas(activo_info, valoracion, catalogo_amenazas)
            # Recalcular degradaciones con MOTOR
            amenazas = calcular_degradacion_amenazas(amenazas, tipo_activo, criticidad)
            return True, amenazas, "Análisis heurístico + Motor MAGERIT (ninguna amenaza válida de IA)"
    
    except json.JSONDecodeError:
        amenazas = generar_amenazas_heuristicas(activo_info, valoracion, catalogo_amenazas)
        # Recalcular degradaciones con MOTOR
        amenazas = calcular_degradacion_amenazas(amenazas, tipo_activo, criticidad)
        return True, amenazas, "Análisis heurístico + Motor MAGERIT (JSON inválido)"


def generar_amenazas_heuristicas(
    activo_info: Dict,
    valoracion: Dict,
    catalogo_amenazas: Dict[str, Dict]
) -> List[Dict]:
    """
    Genera amenazas de forma heurística cuando la IA no está disponible.
    Basado en el tipo de activo y la criticidad.
    NOTA: Las degradaciones se calculan posteriormente por calcular_degradacion_amenazas()
    usando el MOTOR MAGERIT, no se calculan aquí.
    """
    tipo_activo = str(activo_info.get("Tipo_Activo", "")).lower()
    criticidad_nivel = valoracion.get("Criticidad_Nivel", "Sin valorar")
    
    # Usar mapeo de amenazas del contexto de entrenamiento
    amenazas_tipicas = get_amenazas_para_tipo_activo(tipo_activo)
    
    # Vulnerabilidades típicas por amenaza (mejorado con contexto experto)
    VULNERABILIDADES = {
        "N.1": "Falta de protección contra desastres naturales, ubicación en zona de riesgo sísmico/inundable, sin plan de contingencia ante catástrofes",
        "N.2": "Ausencia de sistemas de detección y extinción de incendios, materiales inflamables cercanos, sin procedimientos de evacuación",
        "N.*": "Instalaciones sin medidas de protección ambiental, ausencia de estudios de riesgo natural",
        "I.1": "Ausencia de protección contra tormentas eléctricas, sin pararrayos ni supresores de sobretensión",
        "I.2": "Equipos sin protección térmica adecuada, falta de climatización redundante",
        "I.5": "Falta de sistemas de respaldo de energía (UPS), sin generador de emergencia, tiempo de autonomía insuficiente",
        "I.6": "Deficiencias en climatización del CPD, sin monitoreo 24/7 de temperatura y humedad",
        "I.7": "Instalación eléctrica sin certificar, cableado sin protección contra EMI",
        "I.8": "Falla en equipos de comunicaciones, sin redundancia en enlaces, SLA inadecuados",
        "I.9": "Dependencia de un único proveedor cloud sin SLA adecuado, sin plan de migración alternativo",
        "I.*": "Infraestructura sin mantenimiento preventivo, ausencia de contratos de soporte",
        "E.1": "Personal sin capacitación en seguridad, falta de concienciación, procedimientos de actuación no documentados",
        "E.2": "Procedimientos de configuración inadecuados, documentación desactualizada, falta de control de cambios",
        "E.3": "Monitorización insuficiente, logs no revisados, alertas no configuradas",
        "E.4": "Control de versiones deficiente, sin trazabilidad de cambios, software no versionado",
        "E.7": "Datos de producción en entornos de desarrollo, sin anonimización de datos de prueba",
        "E.8": "Falta de validación en cambios de routing, sin pruebas de conectividad",
        "E.9": "Fallos en enrutamiento, errores de configuración de red, tablas de routing no verificadas",
        "E.10": "Red sin segmentación, broadcast no controlado, VLANs mal configuradas",
        "E.14": "Fuga de información por metadatos, sin limpieza de documentos, logs expuestos",
        "E.15": "Software obsoleto con vulnerabilidades conocidas, parches no aplicados, EOL no gestionado",
        "E.18": "Falta de procedimientos de destrucción segura, medios reutilizados sin borrado",
        "E.19": "Disclosure de información por error, emails a destinatarios incorrectos",
        "E.20": "Vulnerabilidades de software no parcheadas, CVEs conocidos sin remediar",
        "E.21": "Errores en mantenimiento de software, sin pruebas de regresión, cambios no documentados",
        "E.23": "Falta de mantenimiento preventivo, equipos obsoletos, contratos de soporte vencidos",
        "E.24": "Pérdida de equipos portátiles, dispositivos sin cifrado, sin MDM",
        "E.25": "Robo interno de equipos, control de inventario deficiente, sin etiquetado de activos",
        "A.3": "Interceptación de información por keyloggers, sniffers no detectados, monitoreo no autorizado",
        "A.4": "Modificación maliciosa de información, acceso con privilegios elevados no justificado",
        "A.5": "Falta de autenticación robusta, credenciales débiles, sin MFA, passwords por defecto",
        "A.6": "Configuraciones de acceso inadecuadas, privilegios excesivos, sin revisión periódica de permisos",
        "A.7": "Acceso no autorizado a locales, tarjetas clonadas, accesos compartidos",
        "A.8": "Software malicioso instalado, parches de seguridad no aplicados, antivirus desactualizado",
        "A.9": "Tráfico de red sin cifrar, ausencia de segmentación, puertos innecesarios abiertos",
        "A.10": "Saturación deliberada de recursos, ataques de amplificación, falta de rate limiting",
        "A.11": "Falta de controles de acceso físico, sin registro de visitantes, sin CCTV",
        "A.12": "Análisis de tráfico no detectado, sin cifrado de metadata, patrones de uso expuestos",
        "A.13": "Repudio de transacciones, sin firma digital, logs no protegidos",
        "A.14": "Interceptación de comunicaciones, MitM posible, certificados no validados",
        "A.15": "Ausencia de cifrado en almacenamiento, datos sensibles en texto plano, claves expuestas",
        "A.18": "Destrucción maliciosa de información, sin backups offline, ransomware",
        "A.19": "Falta de procedimientos de borrado seguro, medios no destruidos, datos recuperables",
        "A.22": "Inyección de código, XSS, CSRF, falta de validación de entrada, WAF no configurado",
        "A.23": "Manipulación de logs, sin protección de integridad, syslog no asegurado",
        "A.24": "Sin protección DDoS, falta de redundancia geográfica, sin CDN, sin plan de contingencia",
        "A.25": "Robo de equipos, acceso físico no controlado, sin cables de seguridad, sin tracking",
        "A.26": "Ingeniería social exitosa, phishing no detectado, pretexting, vishing",
        "A.28": "Falta de protección contra fuerza bruta, sin bloqueo de cuentas, sin CAPTCHA",
        "A.29": "Extorsión/chantaje, sin protocolo de gestión de crisis, datos sensibles expuestos",
        "A.30": "Ataque interno malicioso, segregación de funciones inadecuada, sin DLP",
    }
    
    # Extraer códigos de amenazas de las típicas
    amenazas_codigos = []
    for amenaza_texto in amenazas_tipicas[:6]:
        # Extraer el código (ej: "N.1: Fuego" -> "N.1")
        if ": " in amenaza_texto:
            codigo = amenaza_texto.split(":")[0].strip()
            if codigo in catalogo_amenazas:
                amenazas_codigos.append(codigo)
    
    if not amenazas_codigos:
        # Default para cualquier activo
        amenazas_codigos = ["A.24", "A.11", "A.5", "A.8", "E.1", "E.2"]
    
    # Obtener vulnerabilidades del catálogo según tipo de activo
    vulnerabilidades_tipo = obtener_vulnerabilidades_por_tipo(activo_info.get("Tipo_Activo", ""))
    
    # Generar lista de amenazas (las degradaciones serán calculadas por el MOTOR después)
    amenazas = []
    for idx, codigo in enumerate(amenazas_codigos):
        if codigo in catalogo_amenazas:
            info = catalogo_amenazas[codigo]
            
            # Seleccionar vulnerabilidad del catálogo (rotar entre las disponibles)
            if vulnerabilidades_tipo:
                vuln_idx = idx % len(vulnerabilidades_tipo)
                vuln_catalogo = vulnerabilidades_tipo[vuln_idx]
                cod_vuln = vuln_catalogo["codigo"]
                vulnerabilidad_texto = f"{vuln_catalogo['nombre']}: {vuln_catalogo['descripcion']}"
            else:
                # Fallback si no hay vulnerabilidades en catálogo
                cod_vuln = f"V{idx+1:03d}"
                vulnerabilidad_texto = VULNERABILIDADES.get(codigo, f"Vulnerabilidad asociada a {info['amenaza']}")
            
            # Valores placeholder - serán sobrescritos por calcular_degradacion_amenazas()
            amenazas.append({
                "codigo_amenaza": codigo,
                "codigo_vulnerabilidad": cod_vuln,
                "nombre_amenaza": info["amenaza"],
                "vulnerabilidad": vulnerabilidad_texto,
                "degradacion_d": 0,  # Será calculado por MOTOR
                "degradacion_i": 0,  # Será calculado por MOTOR
                "degradacion_c": 0,  # Será calculado por MOTOR
                "justificacion": f"Amenaza típica para {tipo_activo} con criticidad {criticidad_nivel}",
                "tipo_amenaza": info.get("tipo_amenaza", "")
            })
    
    return amenazas


# ==================== SUGERENCIA DE SALVAGUARDAS CON IA ====================

def sugerir_salvaguardas_ia(
    nombre_activo: str,
    tipo_activo: str,
    amenaza: str,
    vulnerabilidad: str,
    riesgo: float,
    modelo: str = None
) -> Tuple[str, str, bool]:
    """
    Sugiere salvaguardas y controles ISO 27002 para mitigar un riesgo específico.
    MEJORADO: Usa el contexto de entrenamiento MAGERIT para mapeos precisos.
    
    Args:
        nombre_activo: Nombre del activo
        tipo_activo: Tipo del activo
        amenaza: Descripción de la amenaza
        vulnerabilidad: Descripción de la vulnerabilidad
        riesgo: Valor del riesgo calculado
        modelo: Modelo de Ollama a usar
    
    Returns:
        (salvaguarda_sugerida, control_iso_sugerido, usó_ia)
    """
    modelo_usar = modelo or MODELO_DEFAULT
    catalogo_controles = get_catalogo_controles()
    
    # Obtener controles recomendados del mapeo de entrenamiento
    controles_recomendados = get_controles_para_amenaza(amenaza)
    controles_recomendados_texto = ""
    if controles_recomendados:
        controles_recomendados_texto = f"""
## CONTROLES RECOMENDADOS PARA ESTA AMENAZA (PRIORIZAR ESTOS)
{chr(10).join(['- ' + c for c in controles_recomendados])}
"""
    
    # Obtener contexto ISO 27002
    from services.ia_context_magerit import CONTEXTO_ISO27002
    
    # Construir lista completa de controles disponibles
    controles_texto = "\n".join([
        f"- {codigo}: {info['nombre']} ({info['categoria']})"
        for codigo, info in list(catalogo_controles.items())[:60]
    ])
    
    # Determinar zona de riesgo
    if riesgo >= 6:
        zona = "CRÍTICO"
        urgencia = "Implementación URGENTE e INMEDIATA"
    elif riesgo >= 4:
        zona = "ALTO"
        urgencia = "Implementación prioritaria a corto plazo"
    elif riesgo >= 2:
        zona = "MEDIO"
        urgencia = "Planificar implementación a mediano plazo"
    else:
        zona = "BAJO"
        urgencia = "Monitorear y evaluar periódicamente"
    
    prompt = f"""Eres un experto certificado en ciberseguridad y gestión de riesgos MAGERIT v3 / ISO 27002:2022.

## CONTEXTO ISO 27002:2022
{CONTEXTO_ISO27002}

## CONTEXTO DEL RIESGO A MITIGAR
- **Activo:** {nombre_activo} ({tipo_activo})
- **Amenaza:** {amenaza}
- **Vulnerabilidad:** {vulnerabilidad}
- **Nivel de Riesgo:** {riesgo:.2f} ({zona})
- **Urgencia:** {urgencia}
{controles_recomendados_texto}

## CATÁLOGO COMPLETO DE CONTROLES ISO 27002:2022 (USAR SOLO ESTOS CÓDIGOS)
{controles_texto}

## TU TAREA
Recomienda UNA salvaguarda específica y UN control ISO 27002 para mitigar este riesgo.
IMPORTANTE: Prioriza los controles recomendados para esta amenaza si están disponibles.

Responde ÚNICAMENTE con un JSON válido:
```json
{{
  "salvaguarda": "Descripción concreta de la medida a implementar (máximo 150 caracteres)",
  "control_iso": "X.XX",
  "justificacion": "Por qué este control mitiga el riesgo según ISO 27002"
}}
```

REGLAS OBLIGATORIAS:
1. El control_iso DEBE ser un código válido del catálogo (5.xx, 6.xx, 7.xx, 8.xx)
2. La salvaguarda debe ser específica y accionable
3. Considerar la urgencia según el nivel de riesgo

Responde SOLO con el JSON:"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": modelo_usar,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3}
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            texto = response.json().get("response", "")
            
            # Extraer JSON
            json_match = re.search(r'\{[^{}]*\}', texto, re.DOTALL)
            if json_match:
                resultado = json.loads(json_match.group())
                salvaguarda = resultado.get("salvaguarda", "Implementar medida de control")
                control = resultado.get("control_iso", "")
                
                # Validar que el control existe
                if control and control in catalogo_controles:
                    control_info = catalogo_controles[control]
                    control_completo = f"{control}: {control_info['nombre']}"
                else:
                    # Usar control del mapeo de entrenamiento
                    control_completo = sugerir_control_heuristico(amenaza, catalogo_controles)
                
                return salvaguarda, control_completo, True
    except Exception as e:
        pass
    
    # Fallback heurístico usando el mapeo de entrenamiento
    salvaguarda = generar_salvaguarda_heuristica(amenaza, vulnerabilidad, zona)
    control = sugerir_control_heuristico(amenaza, catalogo_controles)
    return salvaguarda, control, False


def generar_salvaguarda_heuristica(amenaza: str, vulnerabilidad: str, zona: str) -> str:
    """Genera salvaguarda heurística basada en palabras clave"""
    amenaza_lower = amenaza.lower()
    
    # Mapeo de palabras clave a salvaguardas
    SALVAGUARDAS = {
        "suplantación": "Implementar autenticación multifactor (MFA) y políticas de contraseñas robustas",
        "acceso": "Establecer control de acceso basado en roles (RBAC) con principio de mínimo privilegio",
        "denegación": "Implementar protección DDoS, WAF y balanceo de carga con redundancia",
        "malware": "Desplegar solución antimalware/EDR con actualizaciones automáticas",
        "robo": "Implementar cifrado de datos en reposo y tránsito con gestión de claves",
        "fuga": "Implementar DLP y clasificación de información con controles de salida",
        "incendio": "Instalar sistemas de detección y extinción automática de incendios",
        "inundación": "Ubicar equipos en zonas elevadas con sensores de humedad",
        "fallo eléctrico": "Instalar UPS y generador de respaldo con mantenimiento preventivo",
        "error": "Implementar procedimientos documentados y capacitación del personal",
        "configuración": "Establecer gestión de cambios y revisiones de configuración periódicas",
        "interceptación": "Implementar cifrado TLS/SSL en todas las comunicaciones",
        "modificación": "Implementar controles de integridad y firmas digitales",
        "destrucción": "Establecer copias de seguridad 3-2-1 con pruebas de restauración",
        "indisponibilidad": "Implementar alta disponibilidad con clustering y failover",
    }
    
    for keyword, salvaguarda in SALVAGUARDAS.items():
        if keyword in amenaza_lower:
            return salvaguarda
    
    # Salvaguarda genérica según zona
    if zona == "CRÍTICO":
        return "Implementar controles técnicos y organizativos inmediatos para mitigar el riesgo"
    elif zona == "ALTO":
        return "Establecer medidas de protección prioritarias según análisis de vulnerabilidad"
    else:
        return "Evaluar e implementar controles preventivos apropiados"


def sugerir_control_heuristico(amenaza: str, catalogo: Dict) -> str:
    """
    Sugiere un control ISO 27002 basado en el mapeo de entrenamiento MAGERIT.
    MEJORADO: Usa MAPEO_AMENAZA_CONTROL del contexto de entrenamiento.
    """
    amenaza_lower = amenaza.lower()
    
    # Primero intentar usar el mapeo de entrenamiento
    controles_entrenamiento = get_controles_para_amenaza(amenaza)
    if controles_entrenamiento:
        # Extraer el código del primer control recomendado
        primer_control = controles_entrenamiento[0]
        # Formato: "5.15: Control de acceso" -> extraer "5.15"
        if ": " in primer_control:
            codigo = primer_control.split(":")[0].strip()
            if codigo in catalogo:
                info = catalogo[codigo]
                return f"{codigo}: {info['nombre']}"
    
    # Mapeo de respaldo basado en palabras clave (extendido)
    MAPEO_CONTROLES = {
        # Amenazas de acceso/autenticación
        "suplantación": "8.5",      # Autenticación segura
        "identity": "8.5",
        "credencial": "8.5",
        "password": "8.5",
        "contraseña": "8.5",
        "acceso no autorizado": "5.15",  # Control de acceso
        "acceso": "5.15",
        "privilegio": "5.18",       # Derechos de acceso privilegiado
        
        # Amenazas de disponibilidad
        "denegación": "8.22",       # Segmentación de red
        "ddos": "8.22",
        "indisponibilidad": "8.14", # Redundancia
        "interrupción": "8.14",
        
        # Amenazas de malware
        "malware": "8.7",           # Protección contra malware
        "virus": "8.7",
        "ransomware": "8.7",
        "código malicioso": "8.7",
        
        # Amenazas de datos
        "robo": "7.10",             # Medios de almacenamiento
        "fuga": "5.12",             # Clasificación de información
        "exfiltración": "5.12",
        "leak": "5.12",
        
        # Amenazas criptográficas
        "cifrado": "8.24",          # Uso de criptografía
        "interceptación": "8.24",
        "escucha": "8.24",
        "sniffing": "8.24",
        
        # Amenazas físicas
        "incendio": "7.5",          # Protección contra amenazas físicas
        "fuego": "7.5",
        "inundación": "7.5",
        "desastre natural": "7.5",
        
        # Amenazas de configuración/cambios
        "fallo": "8.14",            # Redundancia
        "error": "6.3",             # Concientización
        "configuración": "8.9",     # Gestión de configuración
        "modificación": "8.4",      # Acceso a código fuente
        
        # Amenazas de continuidad
        "destrucción": "8.13",      # Copias de seguridad
        "pérdida": "8.13",
        "backup": "8.13",
        
        # Vulnerabilidades técnicas
        "vulnerabilidad": "8.8",    # Gestión de vulnerabilidades técnicas
        "parche": "8.8",
        "actualización": "8.8",
        
        # Red y comunicaciones
        "red": "8.20",              # Seguridad de redes
        "comunicación": "8.20",
        "tráfico": "8.22",          # Segmentación de red
        
        # Ingeniería social
        "phishing": "6.3",          # Concientización
        "ingeniería social": "6.3",
        "engaño": "6.3",
    }
    
    for keyword, codigo in MAPEO_CONTROLES.items():
        if keyword in amenaza_lower:
            if codigo in catalogo:
                info = catalogo[codigo]
                return f"{codigo}: {info['nombre']}"
    
    # Control por defecto
    if "5.1" in catalogo:
        return "5.1: Políticas de seguridad de la información"
    return "8.1: Dispositivos de punto final de usuario"


def sugerir_salvaguardas_batch(riesgos_df: pd.DataFrame, modelo: str = None) -> pd.DataFrame:
    """
    Sugiere salvaguardas para múltiples riesgos en batch.
    
    Args:
        riesgos_df: DataFrame con columnas: Nombre_Activo, Tipo_Activo, Amenaza, Vulnerabilidad, Riesgo
        modelo: Modelo de Ollama a usar
    
    Returns:
        DataFrame con columnas adicionales: Salvaguarda_Sugerida, Control_ISO, Generado_Por_IA
    """
    resultados = []
    
    for idx, row in riesgos_df.iterrows():
        salvaguarda, control, usó_ia = sugerir_salvaguardas_ia(
            nombre_activo=row.get("Nombre_Activo", ""),
            tipo_activo=row.get("Tipo_Activo", ""),
            amenaza=row.get("Amenaza", ""),
            vulnerabilidad=row.get("Vulnerabilidad", ""),
            riesgo=row.get("Riesgo", 0),
            modelo=modelo
        )
        resultados.append({
            "Salvaguarda_Sugerida": salvaguarda,
            "Control_ISO": control,
            "Generado_IA": "✅" if usó_ia else "🔧"
        })
    
    return pd.concat([riesgos_df.reset_index(drop=True), pd.DataFrame(resultados)], axis=1)

