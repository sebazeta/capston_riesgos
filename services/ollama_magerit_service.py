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
"""
import json
import re
import requests
from typing import Dict, List, Optional, Tuple
import pandas as pd
from services.database_service import read_table


# ==================== CONFIGURACIÓN ====================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO_DEFAULT = "llama3.2:1b"  # Usar modelo pequeño por defecto (más rápido)
TIMEOUT = 30  # Reducido a 30 segundos para fallar rápido


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
                "dimension_afectada": row.get("dimension_afectada", "D")
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


# ==================== CONTEXTO DEL ACTIVO ====================

def construir_contexto_activo(
    activo: pd.Series,
    respuestas: pd.DataFrame
) -> str:
    """
    Construye el contexto textual de un activo para el prompt de IA.
    Incluye datos del activo y resumen de respuestas del cuestionario.
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
    Construye el prompt para que la IA analice el activo y genere
    evaluación MAGERIT estructurada.
    """
    # Listar amenazas disponibles por categoría
    amenazas_por_tipo = {}
    for codigo, info in catalogo_amenazas.items():
        tipo = info["tipo_amenaza"]
        if tipo not in amenazas_por_tipo:
            amenazas_por_tipo[tipo] = []
        amenazas_por_tipo[tipo].append(f"{codigo}: {info['amenaza']}")
    
    amenazas_texto = ""
    for tipo, lista in amenazas_por_tipo.items():
        amenazas_texto += f"\n**{tipo}:**\n"
        for a in lista[:20]:  # Limitar para no exceder contexto
            amenazas_texto += f"  - {a}\n"
    
    # Listar controles disponibles por categoría
    controles_por_cat = {}
    for codigo, info in catalogo_controles.items():
        cat = info["categoria"]
        if cat not in controles_por_cat:
            controles_por_cat[cat] = []
        controles_por_cat[cat].append(f"{codigo}: {info['nombre']}")
    
    controles_texto = ""
    for cat, lista in controles_por_cat.items():
        controles_texto += f"\n**{cat}:**\n"
        for c in lista[:15]:  # Limitar
            controles_texto += f"  - {c}\n"
    
    prompt = f"""Eres un experto en seguridad de la información y gestión de riesgos bajo la metodología MAGERIT v3.

{contexto_activo}

## CATÁLOGO DE AMENAZAS MAGERIT v3 DISPONIBLES
Solo puedes usar códigos de esta lista:
{amenazas_texto}

## CATÁLOGO DE CONTROLES ISO 27002:2022 DISPONIBLES
Solo puedes recomendar códigos de esta lista:
{controles_texto}

## TU TAREA
1. Analiza el activo y sus respuestas del cuestionario BIA
2. Identifica las 3-7 amenazas MAGERIT más relevantes para este activo
3. Determina la probabilidad general (1-5) basándote en:
   - 1: Muy improbable (una vez cada 10+ años)
   - 2: Improbable (una vez cada 5 años)
   - 3: Posible (una vez al año)
   - 4: Probable (varias veces al año)
   - 5: Muy probable (mensual o más frecuente)
4. Para cada amenaza, recomienda 1-3 controles ISO 27002 que la mitigan

## FORMATO DE RESPUESTA OBLIGATORIO
Responde ÚNICAMENTE con un JSON válido, sin texto adicional antes ni después:

```json
{{
  "probabilidad": 3,
  "amenazas": [
    {{
      "codigo": "A.24",
      "dimension": "D",
      "justificacion": "Breve explicación de por qué aplica esta amenaza",
      "controles_iso_recomendados": [
        {{
          "control": "8.20",
          "prioridad": "Alta",
          "motivo": "Por qué este control mitiga la amenaza"
        }}
      ]
    }}
  ],
  "observaciones": "Resumen general del perfil de riesgo del activo"
}}
```

## REGLAS CRÍTICAS
1. **NO inventes códigos de amenaza** - solo usa los del catálogo
2. **NO inventes códigos de control** - solo usa los del catálogo
3. **Dimensiones válidas**: D (Disponibilidad), I (Integridad), C (Confidencialidad)
4. **Prioridades válidas**: "Alta", "Media", "Baja"
5. Probabilidad debe ser un número del 1 al 5
6. Justificaciones deben ser específicas al activo, no genéricas

Responde SOLO con el JSON, sin explicaciones adicionales:"""
    
    return prompt


# ==================== EVALUACIÓN HEURÍSTICA (FALLBACK) ====================

def generar_evaluacion_heuristica(
    activo: pd.Series,
    respuestas: pd.DataFrame,
    catalogo_amenazas: Dict[str, Dict],
    catalogo_controles: Dict[str, Dict]
) -> Dict:
    """
    Genera una evaluación MAGERIT heurística cuando la IA falla.
    Usa el tipo de activo para seleccionar amenazas comunes.
    """
    tipo_activo = str(activo.get("Tipo_Activo", "")).lower()
    
    # Mapeo de tipos de activo a amenazas típicas
    AMENAZAS_POR_TIPO = {
        "servidor": ["A.24", "A.5", "A.6", "A.11", "E.2", "E.8"],
        "base de datos": ["A.5", "A.6", "A.11", "A.15", "E.1", "E.2"],
        "aplicación": ["A.5", "A.6", "A.8", "A.22", "E.1", "E.21"],
        "red": ["A.5", "A.12", "A.14", "A.24", "I.8", "E.9"],
        "usuario": ["A.30", "E.1", "E.2", "E.7", "E.15"],
        "documento": ["A.11", "A.15", "A.19", "E.1", "E.2"],
        "equipo": ["N.1", "N.2", "I.5", "A.25", "E.23"],
        "software": ["A.5", "A.6", "A.8", "A.22", "E.20", "E.21"],
    }
    
    # Mapeo de amenazas a controles típicos
    CONTROLES_POR_AMENAZA = {
        "A.5": ["5.1", "5.2", "5.15"],
        "A.6": ["5.15", "5.17", "8.4"],
        "A.11": ["7.7", "8.1", "8.10"],
        "A.24": ["8.20", "8.21", "8.22"],
        "E.1": ["6.3", "7.13", "8.7"],
        "E.2": ["8.9", "8.13", "8.15"],
    }
    
    # Determinar amenazas aplicables
    amenazas_aplicables = []
    for key, codigos in AMENAZAS_POR_TIPO.items():
        if key in tipo_activo:
            amenazas_aplicables = codigos
            break
    
    if not amenazas_aplicables:
        # Default: amenazas genéricas de software
        amenazas_aplicables = ["A.5", "A.6", "E.1", "E.2", "A.22"]
    
    # Construir resultado
    amenazas_resultado = []
    for codigo in amenazas_aplicables[:5]:  # Máximo 5 amenazas
        if codigo in catalogo_amenazas:
            info = catalogo_amenazas[codigo]
            controles = CONTROLES_POR_AMENAZA.get(codigo, ["5.1", "8.1"])[:2]
            controles_rec = []
            for ctrl in controles:
                if ctrl in catalogo_controles:
                    controles_rec.append({
                        "control": ctrl,
                        "prioridad": "Media",
                        "motivo": f"Control estándar para mitigar {codigo}"
                    })
            
            amenazas_resultado.append({
                "codigo": codigo,
                "dimension": info.get("dimension_afectada", "D")[0],
                "justificacion": f"Amenaza típica para activos tipo {tipo_activo}",
                "controles_iso_recomendados": controles_rec
            })
    
    return {
        "probabilidad": 3,  # Valor medio por defecto
        "amenazas": amenazas_resultado,
        "observaciones": f"Evaluación heurística basada en tipo de activo: {tipo_activo}. Considere ajustar manualmente."
    }


# ==================== LLAMADA A OLLAMA ====================

def llamar_ollama(prompt: str, modelo: str = None) -> Tuple[bool, str]:
    """
    Llama a Ollama y obtiene la respuesta.
    
    Returns:
        (éxito: bool, respuesta_o_error: str)
    """
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
    
    Returns:
        (disponible: bool, modelos: List[str])
    """
    try:
        response = requests.get(
            "http://localhost:11434/api/tags",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            modelos = [m["name"] for m in data.get("models", [])]
            return True, modelos
        return False, []
    except:
        return False, []


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
