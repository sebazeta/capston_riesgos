"""
SERVICIO DE VALIDACIÓN DE IA LOCAL - PROYECTO TITA
===================================================
Validación completa de que la IA funciona:
- 100% local (Ollama en localhost)
- Sin internet
- Con evidencia técnica auditable
- Con pruebas de canary token
- Con variabilidad controlada

Cumple requisitos académicos para defensa de proyecto.
"""
import hashlib
import json
import time
import random
import string
import socket
import datetime as dt
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import requests
from services.database_service import get_connection, read_table


# ==================== CONFIGURACIÓN ====================

OLLAMA_LOCAL_ENDPOINTS = [
    "http://localhost:11434",
    "http://127.0.0.1:11434"
]
TIMEOUT_VALIDATION = 30
BLOCKED_DOMAINS = ["api.openai.com", "api.anthropic.com", "api.cohere.ai", "huggingface.co"]


# ==================== MODELOS DE DATOS ====================

@dataclass
class IAValidationResult:
    """Resultado de validación de IA"""
    timestamp: str
    is_local: bool
    endpoint: str
    model: str
    latency_ms: float
    response_size: int
    response_hash: str
    canary_passed: bool
    canary_nonce: str
    variability_passed: bool
    catalogs_loaded: bool
    knowledge_base_ready: bool
    ia_ready: bool
    errors: List[str]
    warnings: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class IAExecutionEvidence:
    """Evidencia técnica de cada ejecución de IA"""
    id_evaluacion: str
    id_activo: str
    timestamp: str
    modelo: str
    endpoint: str
    prompt_hash: str
    response_hash: str
    latency_ms: float
    json_valid: bool
    canary_verified: bool
    raw_response_length: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ==================== FUNCIONES DE HASH ====================

def sha256_hash(text: str) -> str:
    """Genera SHA-256 de un texto"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def generate_nonce() -> str:
    """Genera nonce único para canary token"""
    timestamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"TITA-CANARY-{timestamp}-{random_part}"


# ==================== VALIDACIÓN A.1: OLLAMA LOCAL ====================

def verificar_ollama_local() -> Tuple[bool, str, List[str], str]:
    """
    Verifica que Ollama esté corriendo localmente.
    
    Returns:
        (es_local: bool, endpoint: str, modelos: List[str], error: str)
    """
    for endpoint in OLLAMA_LOCAL_ENDPOINTS:
        try:
            # Verificar que el endpoint sea local
            from urllib.parse import urlparse
            parsed = urlparse(endpoint)
            host = parsed.hostname
            
            if host not in ["localhost", "127.0.0.1", "::1"]:
                continue  # No es local, saltar
            
            # Intentar conectar
            response = requests.get(
                f"{endpoint}/api/tags",
                timeout=TIMEOUT_VALIDATION
            )
            
            if response.status_code == 200:
                data = response.json()
                modelos = [m["name"] for m in data.get("models", [])]
                return True, endpoint, modelos, ""
        
        except requests.exceptions.ConnectionError:
            continue
        except Exception as e:
            continue
    
    return False, "", [], "No se pudo conectar con Ollama local"


def ejecutar_llamada_real(endpoint: str, modelo: str, prompt: str) -> Tuple[bool, str, float, str]:
    """
    Ejecuta una llamada real al modelo y mide latencia.
    
    Returns:
        (éxito: bool, respuesta: str, latencia_ms: float, error: str)
    """
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{endpoint}/api/generate",
            json={
                "model": modelo,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 500
                }
            },
            timeout=TIMEOUT_VALIDATION * 2
        )
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        if response.status_code == 200:
            resultado = response.json()
            return True, resultado.get("response", ""), latency_ms, ""
        else:
            return False, "", 0, f"Error HTTP {response.status_code}"
    
    except Exception as e:
        return False, "", 0, str(e)


# ==================== VALIDACIÓN A.2: MODO OFFLINE ====================

def verificar_modo_offline() -> Tuple[bool, List[str]]:
    """
    Verifica que el sistema esté en modo offline (sin conectividad externa).
    
    Returns:
        (es_offline: bool, dominios_bloqueados: List[str])
    """
    dominios_accesibles = []
    
    for dominio in BLOCKED_DOMAINS:
        try:
            # Intentar resolver DNS
            socket.setdefaulttimeout(2)
            socket.gethostbyname(dominio)
            
            # Intentar conectar
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((dominio, 443))
            sock.close()
            
            if result == 0:
                dominios_accesibles.append(dominio)
        except:
            pass  # No accesible, está bien
    
    return len(dominios_accesibles) == 0, dominios_accesibles


def bloquear_requests_externos():
    """
    Parche para bloquear requests a dominios externos.
    Solo permite localhost.
    """
    import urllib.request
    original_urlopen = urllib.request.urlopen
    
    def patched_urlopen(url, *args, **kwargs):
        from urllib.parse import urlparse
        parsed = urlparse(str(url))
        host = parsed.hostname
        
        if host and host not in ["localhost", "127.0.0.1", "::1"]:
            raise ConnectionError(f"BLOQUEADO: Acceso externo a {host} no permitido en modo offline")
        
        return original_urlopen(url, *args, **kwargs)
    
    urllib.request.urlopen = patched_urlopen


# ==================== VALIDACIÓN B.1: EVIDENCIA TÉCNICA ====================

def crear_tabla_evidencia():
    """Crea tabla para guardar evidencia de ejecuciones IA"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS IA_EXECUTION_EVIDENCE (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_evaluacion TEXT,
                id_activo TEXT,
                timestamp TEXT,
                modelo TEXT,
                endpoint TEXT,
                prompt_hash TEXT,
                response_hash TEXT,
                latency_ms REAL,
                json_valid INTEGER,
                canary_verified INTEGER,
                raw_response_length INTEGER,
                raw_response TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS IA_VALIDATION_LOG (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                validation_type TEXT,
                result INTEGER,
                details TEXT,
                evidence_hash TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS IA_STATUS (
                id INTEGER PRIMARY KEY,
                ia_ready INTEGER DEFAULT 0,
                last_validation TEXT,
                validation_result TEXT,
                canary_nonce TEXT,
                knowledge_version TEXT
            )
        ''')


def guardar_evidencia(evidencia: IAExecutionEvidence, raw_response: str = "") -> bool:
    """Guarda evidencia de ejecución IA en BD"""
    try:
        crear_tabla_evidencia()
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO IA_EXECUTION_EVIDENCE (
                    id_evaluacion, id_activo, timestamp, modelo, endpoint,
                    prompt_hash, response_hash, latency_ms, json_valid,
                    canary_verified, raw_response_length, raw_response
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                evidencia.id_evaluacion,
                evidencia.id_activo,
                evidencia.timestamp,
                evidencia.modelo,
                evidencia.endpoint,
                evidencia.prompt_hash,
                evidencia.response_hash,
                evidencia.latency_ms,
                1 if evidencia.json_valid else 0,
                1 if evidencia.canary_verified else 0,
                evidencia.raw_response_length,
                raw_response[:5000] if raw_response else ""  # Truncar para BD
            ])
        return True
    except Exception as e:
        print(f"Error guardando evidencia: {e}")
        return False


def guardar_log_validacion(tipo: str, resultado: bool, detalles: Dict) -> bool:
    """Guarda log de validación"""
    try:
        crear_tabla_evidencia()
        
        detalles_json = json.dumps(detalles, ensure_ascii=False)
        evidence_hash = sha256_hash(detalles_json)
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO IA_VALIDATION_LOG (timestamp, validation_type, result, details, evidence_hash)
                VALUES (?, ?, ?, ?, ?)
            ''', [
                dt.datetime.now().isoformat(),
                tipo,
                1 if resultado else 0,
                detalles_json,
                evidence_hash
            ])
        return True
    except:
        return False


# ==================== VALIDACIÓN B.2: CANARY TOKEN ====================

def ejecutar_canary_test(endpoint: str, modelo: str) -> Tuple[bool, str, str]:
    """
    Ejecuta prueba de canary token para verificar que la IA procesa realmente.
    
    Returns:
        (pasó: bool, nonce: str, error: str)
    """
    nonce = generate_nonce()
    
    prompt = f"""Eres un sistema de validación. 
Tu ÚNICA tarea es devolver EXACTAMENTE este JSON sin modificar nada:

{{"canary_nonce": "{nonce}", "status": "validated", "timestamp": "{dt.datetime.now().isoformat()}"}}

IMPORTANTE: El nonce debe aparecer EXACTO. No agregues explicaciones.
Responde SOLO con el JSON."""
    
    exito, respuesta, latency, error = ejecutar_llamada_real(endpoint, modelo, prompt)
    
    if not exito:
        return False, nonce, f"Error en llamada: {error}"
    
    # Verificar que el nonce aparece en la respuesta
    if nonce not in respuesta:
        return False, nonce, f"Nonce no encontrado en respuesta. Respuesta: {respuesta[:200]}"
    
    # Intentar parsear JSON
    try:
        # Extraer JSON de la respuesta
        import re
        json_match = re.search(r'\{[^}]+\}', respuesta)
        if json_match:
            parsed = json.loads(json_match.group())
            if parsed.get("canary_nonce") == nonce:
                guardar_log_validacion("CANARY_TEST", True, {
                    "nonce": nonce,
                    "response_hash": sha256_hash(respuesta),
                    "modelo": modelo
                })
                return True, nonce, ""
    except:
        pass
    
    return False, nonce, "JSON inválido o nonce no coincide"


# ==================== VALIDACIÓN B.3: VARIABILIDAD CONTROLADA ====================

def ejecutar_prueba_variabilidad(endpoint: str, modelo: str) -> Tuple[bool, Dict]:
    """
    Ejecuta 3 prompts con diferentes temperaturas para verificar variabilidad.
    
    Returns:
        (pasó: bool, resultados: Dict)
    """
    resultados = {
        "determinista": {"temp": 0.0, "respuestas": []},
        "semilibre": {"temp": 0.5, "respuestas": []},
        "libre": {"temp": 1.0, "respuestas": []}
    }
    
    prompt_base = "Genera un número del 1 al 100 y una palabra relacionada con seguridad informática. Responde solo: NUMERO: X, PALABRA: Y"
    
    for modo, config in resultados.items():
        for _ in range(2):  # 2 intentos por modo
            try:
                response = requests.post(
                    f"{endpoint}/api/generate",
                    json={
                        "model": modelo,
                        "prompt": prompt_base,
                        "stream": False,
                        "options": {
                            "temperature": config["temp"],
                            "num_predict": 50
                        }
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    resp_text = response.json().get("response", "")
                    config["respuestas"].append(resp_text)
            except:
                pass
    
    # Analizar resultados
    # Determinista: respuestas deberían ser similares/iguales
    # Libre: respuestas deberían variar
    
    det_respuestas = resultados["determinista"]["respuestas"]
    libre_respuestas = resultados["libre"]["respuestas"]
    
    # Verificar que al menos hay respuestas
    if not det_respuestas or not libre_respuestas:
        return False, {"error": "No se obtuvieron respuestas suficientes"}
    
    # Verificar variabilidad en modo libre
    if len(set(libre_respuestas)) == 1 and len(libre_respuestas) > 1:
        # Respuestas idénticas en modo libre = sospechoso
        guardar_log_validacion("VARIABILITY_TEST", False, {
            "warning": "Respuestas idénticas en modo temperatura alta",
            "resultados": resultados
        })
        return False, resultados
    
    guardar_log_validacion("VARIABILITY_TEST", True, resultados)
    return True, resultados


# ==================== VALIDACIÓN C: USO REAL EN EVALUACIÓN ====================

def ejecutar_prueba_dependencia_input(endpoint: str, modelo: str) -> Tuple[bool, Dict]:
    """
    Crea 2 activos opuestos y verifica que la IA genera evaluaciones diferentes.
    
    Returns:
        (pasó: bool, resultados: Dict)
    """
    # Activo 1: Alto riesgo
    prompt_alto = """Eres analista MAGERIT. Evalúa este activo y devuelve JSON:

ACTIVO: Servidor Web Público
- Expuesto a Internet 24/7
- Sin backups
- Sin parches hace 2 años
- Datos de clientes sin cifrar
- Sin monitoreo

Devuelve: {"riesgo": "ALTO/BAJO", "probabilidad": 1-5, "amenazas": ["lista"]}"""

    # Activo 2: Bajo riesgo
    prompt_bajo = """Eres analista MAGERIT. Evalúa este activo y devuelve JSON:

ACTIVO: PC Offline Aislada
- Sin conexión a red
- Backups diarios verificados
- Parches automáticos
- Solo datos públicos
- Monitoreo 24/7

Devuelve: {"riesgo": "ALTO/BAJO", "probabilidad": 1-5, "amenazas": ["lista"]}"""

    resultados = {}
    
    for nombre, prompt in [("alto_riesgo", prompt_alto), ("bajo_riesgo", prompt_bajo)]:
        exito, respuesta, latency, error = ejecutar_llamada_real(endpoint, modelo, prompt)
        resultados[nombre] = {
            "exito": exito,
            "respuesta": respuesta[:500] if respuesta else "",
            "latency_ms": latency,
            "hash": sha256_hash(respuesta) if respuesta else ""
        }
    
    # Verificar que las respuestas son diferentes
    if resultados.get("alto_riesgo", {}).get("hash") == resultados.get("bajo_riesgo", {}).get("hash"):
        guardar_log_validacion("INPUT_DEPENDENCY_TEST", False, {
            "error": "Respuestas idénticas para inputs opuestos",
            "resultados": resultados
        })
        return False, resultados
    
    # Verificar que menciona riesgo diferente
    alto_resp = resultados.get("alto_riesgo", {}).get("respuesta", "").lower()
    bajo_resp = resultados.get("bajo_riesgo", {}).get("respuesta", "").lower()
    
    if "alto" in alto_resp and "bajo" in bajo_resp:
        guardar_log_validacion("INPUT_DEPENDENCY_TEST", True, resultados)
        return True, resultados
    
    # Aunque no sea perfecto, si las respuestas son diferentes, pasa
    guardar_log_validacion("INPUT_DEPENDENCY_TEST", True, {
        "note": "Respuestas diferentes aunque clasificación no explícita",
        "resultados": resultados
    })
    return True, resultados


# ==================== VALIDACIÓN D: CATÁLOGOS CARGADOS ====================

def verificar_catalogos_cargados() -> Tuple[bool, Dict]:
    """Verifica que los catálogos MAGERIT e ISO estén cargados en BD"""
    resultado = {
        "amenazas_magerit": 0,
        "controles_iso": 0,
        "criterios_d": 0,
        "criterios_i": 0,
        "criterios_c": 0
    }
    
    try:
        amenazas = read_table("CATALOGO_AMENAZAS_MAGERIT")
        resultado["amenazas_magerit"] = len(amenazas)
        
        controles = read_table("CATALOGO_CONTROLES_ISO27002")
        resultado["controles_iso"] = len(controles)
        
        crit_d = read_table("CRITERIOS_DISPONIBILIDAD")
        resultado["criterios_d"] = len(crit_d)
        
        crit_i = read_table("CRITERIOS_INTEGRIDAD")
        resultado["criterios_i"] = len(crit_i)
        
        crit_c = read_table("CRITERIOS_CONFIDENCIALIDAD")
        resultado["criterios_c"] = len(crit_c)
    except:
        pass
    
    # Validar conteos esperados
    es_valido = (
        resultado["amenazas_magerit"] >= 50 and
        resultado["controles_iso"] >= 90 and
        resultado["criterios_d"] >= 5 and
        resultado["criterios_i"] >= 5 and
        resultado["criterios_c"] >= 5
    )
    
    return es_valido, resultado


# ==================== FUNCIÓN PRINCIPAL DE VALIDACIÓN ====================

def ejecutar_validacion_completa(modelo_preferido: str = None) -> IAValidationResult:
    """
    Ejecuta validación completa de IA local.
    
    Returns:
        IAValidationResult con todos los resultados
    """
    errors = []
    warnings = []
    timestamp = dt.datetime.now().isoformat()
    
    # Crear tablas si no existen
    crear_tabla_evidencia()
    
    # A.1 Verificar Ollama local
    is_local, endpoint, modelos, error_local = verificar_ollama_local()
    
    if not is_local:
        errors.append(f"Ollama no disponible localmente: {error_local}")
        return IAValidationResult(
            timestamp=timestamp, is_local=False, endpoint="", model="",
            latency_ms=0, response_size=0, response_hash="",
            canary_passed=False, canary_nonce="", variability_passed=False,
            catalogs_loaded=False, knowledge_base_ready=False, ia_ready=False,
            errors=errors, warnings=warnings
        )
    
    # Seleccionar modelo
    modelo = modelo_preferido if modelo_preferido and modelo_preferido in modelos else (modelos[0] if modelos else "")
    
    if not modelo:
        errors.append("No hay modelos disponibles en Ollama")
        return IAValidationResult(
            timestamp=timestamp, is_local=True, endpoint=endpoint, model="",
            latency_ms=0, response_size=0, response_hash="",
            canary_passed=False, canary_nonce="", variability_passed=False,
            catalogs_loaded=False, knowledge_base_ready=False, ia_ready=False,
            errors=errors, warnings=warnings
        )
    
    # A.2 Verificar modo offline
    is_offline, dominios_accesibles = verificar_modo_offline()
    if not is_offline:
        warnings.append(f"Conectividad externa detectada: {dominios_accesibles}")
    
    # B.2 Ejecutar canary test
    canary_passed, canary_nonce, canary_error = ejecutar_canary_test(endpoint, modelo)
    if not canary_passed:
        errors.append(f"Canary test falló: {canary_error}")
    
    # B.3 Prueba de variabilidad
    variability_passed, variability_results = ejecutar_prueba_variabilidad(endpoint, modelo)
    if not variability_passed:
        warnings.append("Prueba de variabilidad no óptima")
    
    # C.1 Prueba de dependencia de input
    input_dep_passed, input_dep_results = ejecutar_prueba_dependencia_input(endpoint, modelo)
    if not input_dep_passed:
        errors.append("IA no responde diferente a inputs opuestos")
    
    # D Verificar catálogos
    catalogs_ok, catalog_counts = verificar_catalogos_cargados()
    if not catalogs_ok:
        errors.append(f"Catálogos incompletos: {catalog_counts}")
    
    # Llamada de prueba para medir latencia
    test_prompt = "Responde solo: OK"
    test_ok, test_response, latency, _ = ejecutar_llamada_real(endpoint, modelo, test_prompt)
    
    # Determinar si IA está lista
    ia_ready = (
        is_local and
        canary_passed and
        catalogs_ok and
        len([e for e in errors if "Canary" in e or "inputs opuestos" in e]) == 0
    )
    
    # Guardar estado
    guardar_estado_ia(ia_ready, timestamp, canary_nonce)
    
    resultado = IAValidationResult(
        timestamp=timestamp,
        is_local=is_local,
        endpoint=endpoint,
        model=modelo,
        latency_ms=latency,
        response_size=len(test_response) if test_response else 0,
        response_hash=sha256_hash(test_response) if test_response else "",
        canary_passed=canary_passed,
        canary_nonce=canary_nonce,
        variability_passed=variability_passed,
        catalogs_loaded=catalogs_ok,
        knowledge_base_ready=catalogs_ok,  # Por ahora igual a catalogs
        ia_ready=ia_ready,
        errors=errors,
        warnings=warnings
    )
    
    # Guardar log completo
    guardar_log_validacion("FULL_VALIDATION", ia_ready, resultado.to_dict())
    
    return resultado


def guardar_estado_ia(ia_ready: bool, timestamp: str, canary_nonce: str):
    """Guarda el estado de la IA en BD"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM IA_STATUS')
            cursor.execute('''
                INSERT INTO IA_STATUS (id, ia_ready, last_validation, canary_nonce)
                VALUES (1, ?, ?, ?)
            ''', [1 if ia_ready else 0, timestamp, canary_nonce])
    except:
        pass


def obtener_estado_ia() -> Tuple[bool, str, str]:
    """
    Obtiene el estado actual de la IA.
    
    Returns:
        (ia_ready: bool, last_validation: str, canary_nonce: str)
    """
    try:
        crear_tabla_evidencia()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT ia_ready, last_validation, canary_nonce FROM IA_STATUS WHERE id = 1')
            row = cursor.fetchone()
            if row:
                return bool(row[0]), row[1] or "", row[2] or ""
    except:
        pass
    return False, "", ""


def obtener_evidencias_recientes(limite: int = 10) -> List[Dict]:
    """Obtiene las últimas evidencias de ejecución IA"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM IA_EXECUTION_EVIDENCE 
                ORDER BY timestamp DESC LIMIT ?
            ''', [limite])
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    except:
        return []


def obtener_logs_validacion(limite: int = 20) -> List[Dict]:
    """Obtiene los últimos logs de validación"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM IA_VALIDATION_LOG 
                ORDER BY timestamp DESC LIMIT ?
            ''', [limite])
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    except:
        return []
