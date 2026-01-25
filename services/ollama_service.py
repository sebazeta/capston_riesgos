"""
Servicio de integración con Ollama (IA Local)
"""
import json
import re
import requests
from typing import Dict, Any, List

OLLAMA_URL = "http://localhost:11434/api/generate"

FALLBACK_JSON = """
[
  {"Pregunta":"¿El sistema cuenta con redundancia que permita cumplir el RTO objetivo del activo?","Tipo_Respuesta":"1-5","Peso":4,"Dimension":"D"},
  {"Pregunta":"¿Los respaldos y replicación permiten minimizar la pérdida de datos dentro del umbral esperado?","Tipo_Respuesta":"1-5","Peso":4,"Dimension":"I"},
  {"Pregunta":"¿Hay controles para mantener la confidencialidad de datos durante contingencia y restauración?","Tipo_Respuesta":"1-5","Peso":3,"Dimension":"C"}
]
"""


def ollama_generate(model: str, prompt: str, timeout: int = 90):
    """
    Genera texto usando Ollama.
    
    Args:
        model: Modelo a usar (llama3, phi3, mistral)
        prompt: Texto del prompt
        timeout: Timeout en segundos
        
    Returns:
        Respuesta del modelo o código de error
    """
    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 350,
                    "temperature": 0.2
                }
            },
            timeout=timeout
        )
        r.raise_for_status()
        return r.json().get("response", "")
    except requests.exceptions.Timeout:
        return "__TIMEOUT__"
    except Exception as e:
        return f"__ERROR__:{str(e)}"


def extract_json_array(text: str) -> List[Dict]:
    """Extrae array JSON de texto con formato variable"""
    try:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return []
        arr = match.group(0)
        arr = re.sub(r",\s*}", "}", arr)
        arr = re.sub(r",\s*\]", "]", arr)
        return json.loads(arr)
    except Exception:
        return []


def validate_ia_questions(qs, n_ia: int) -> List[Dict]:
    """Valida y limpia preguntas generadas por IA"""
    cleaned = []
    if not isinstance(qs, list):
        return cleaned

    for item in qs:
        if not isinstance(item, dict):
            continue

        pregunta = item.get("Pregunta") or item.get("pregunta") or item.get("question")
        tr = item.get("Tipo_Respuesta") or item.get("tipo_respuesta") or item.get("answer_type")
        peso = item.get("Peso") or item.get("weight", 3)
        dim = item.get("Dimension") or item.get("dimension", "I")

        if not pregunta or tr is None:
            continue

        t = str(tr).strip().lower()
        if "0/1" in t or "0-1" in t or "si/no" in t or "sí/no" in t:
            tr = "0/1"
        elif "1-5" in t:
            tr = "1-5"
        else:
            if str(tr).strip().upper() in ["D", "I", "C"]:
                tr = "1-5"
            else:
                continue

        try:
            peso = int(peso)
        except:
            peso = 3
        peso = max(1, min(5, peso))

        dim = str(dim).strip().upper()
        if dim not in ["D", "I", "C"]:
            dim = "I"

        cleaned.append({
            "Pregunta": str(pregunta).strip(),
            "Tipo_Respuesta": tr,
            "Peso": peso,
            "Dimension": dim
        })

        if len(cleaned) >= n_ia:
            break

    return cleaned


def ollama_analyze_risk(contexto: Dict[str, Any], model: str = "llama3") -> Dict[str, Any]:
    """
    Analiza riesgos de un activo usando IA.
    
    Args:
        contexto: Dict con activo, respuestas e impactos DIC
        model: Modelo Ollama a usar
        
    Returns:
        Dict con probabilidad, impacto, amenazas, vulnerabilidades, salvaguardas
    """
    prompt = f"""
Eres un experto en análisis de riesgos siguiendo MAGERIT (Metodología española de análisis de riesgos).

CONTEXTO DEL ACTIVO:
{json.dumps(contexto.get('activo', {}), ensure_ascii=False)}

RESPUESTAS DEL CUESTIONARIO (muestra):
{json.dumps(contexto.get('respuestas_muestra', [])[:5], ensure_ascii=False)}

IMPACTOS DIMENSIÓN DIC:
- Disponibilidad (D): {contexto.get('impacto_d', 0)}/5
- Integridad (I): {contexto.get('impacto_i', 0)}/5
- Confidencialidad (C): {contexto.get('impacto_c', 0)}/5

TAREA:
Analiza el activo y devuelve SOLO un JSON con:
1. Probabilidad de materialización de amenazas (1-5)
2. Impacto potencial en el negocio (1-5)
3. Lista de 3-5 amenazas MAGERIT relevantes
4. Lista de 3-5 vulnerabilidades detectadas
5. Lista de 3-5 salvaguardas ISO 27002 recomendadas
6. Justificación breve

FORMATO OBLIGATORIO (devuelve SOLO esto):
{{
  "probabilidad": 3,
  "impacto": 4,
  "riesgo_inherente": 12,
  "amenazas": [
    {{"codigo": "A.25", "nombre": "Fallo de equipamiento", "descripcion": "Falla de hardware crítico", "probabilidad": "Media"}}
  ],
  "vulnerabilidades": [
    {{"nombre": "Falta de redundancia", "severidad": 4, "descripcion": "No hay componentes redundantes"}}
  ],
  "salvaguardas": [
    {{"control_iso": "8.13", "nombre": "Copias de seguridad", "descripcion": "Implementar backups automáticos", "prioridad": 5}}
  ],
  "justificacion": "El activo presenta riesgos moderados debido a..."
}}
"""
    
    raw = ollama_generate(model, prompt, timeout=120)
    
    if raw == "__TIMEOUT__" or (isinstance(raw, str) and raw.startswith("__ERROR__")):
        return {
            "probabilidad": 3,
            "impacto": 3,
            "riesgo_inherente": 9,
            "amenazas": [],
            "vulnerabilidades": [],
            "salvaguardas": [],
            "justificacion": "Error al contactar IA. Análisis manual requerido.",
            "error": True
        }
    
    # Intentar extraer JSON
    try:
        # Buscar JSON en la respuesta
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            result = json.loads(match.group(0))
            
            # Validar campos obligatorios
            if 'probabilidad' not in result:
                result['probabilidad'] = 3
            if 'impacto' not in result:
                result['impacto'] = 3
            if 'riesgo_inherente' not in result:
                result['riesgo_inherente'] = result['probabilidad'] * result['impacto']
            
            result['error'] = False
            return result
    except:
        pass
    
    # Fallback si no se pudo parsear
    return {
        "probabilidad": 3,
        "impacto": 3,
        "riesgo_inherente": 9,
        "amenazas": [],
        "vulnerabilidades": [],
        "salvaguardas": [],
        "justificacion": "No se pudo analizar con IA. Revisar manualmente.",
        "error": True,
        "raw_response": raw[:500]  # Primeros 500 chars para debug
    }
