"""
SERVICIO DE MONITOREO Y RECUPERACIÓN AUTOMÁTICA DE OLLAMA
=========================================================
Garantiza 100% de disponibilidad de la IA local mediante:
- Health checks automáticos
- Reintentos con backoff exponencial
- Auto-inicio de Ollama si está caído
- Logging detallado de eventos
- Cache de respuestas para resiliencia
"""
import requests
import time
import subprocess
import logging
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
import json
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración
OLLAMA_URL = "http://localhost:11434"
OLLAMA_API_URL = f"{OLLAMA_URL}/api/generate"
OLLAMA_TAGS_URL = f"{OLLAMA_URL}/api/tags"
MAX_REINTENTOS = 5
TIMEOUT_BASE = 5  # segundos
HEALTH_CHECK_INTERVAL = 30  # segundos

# Cache de respuestas (para resiliencia offline)
CACHE_DIR = Path("c:/capston_riesgos/.ollama_cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_DURATION = timedelta(hours=24)


class OllamaHealthMonitor:
    """Monitor de salud de Ollama con auto-recuperación"""
    
    def __init__(self):
        self.ultimo_check = None
        self.estado_actual = False
        self.intentos_fallidos = 0
        self.modelos_disponibles = []
    
    def verificar_salud(self) -> Tuple[bool, str]:
        """
        Verifica si Ollama está funcionando correctamente.
        
        Returns:
            (disponible: bool, mensaje: str)
        """
        try:
            response = requests.get(OLLAMA_TAGS_URL, timeout=3)
            if response.status_code == 200:
                data = response.json()
                self.modelos_disponibles = [m.get("name", "") for m in data.get("models", [])]
                self.estado_actual = True
                self.intentos_fallidos = 0
                self.ultimo_check = datetime.now()
                logger.info(f"✅ Ollama disponible. Modelos: {', '.join(self.modelos_disponibles[:3])}")
                return True, f"OK - {len(self.modelos_disponibles)} modelos disponibles"
            else:
                self.estado_actual = False
                return False, f"Error HTTP {response.status_code}"
        except requests.exceptions.ConnectionError:
            self.estado_actual = False
            self.intentos_fallidos += 1
            return False, "Ollama no está corriendo"
        except requests.exceptions.Timeout:
            self.estado_actual = False
            return False, "Timeout al conectar con Ollama"
        except Exception as e:
            self.estado_actual = False
            return False, f"Error: {str(e)}"
    
    def intentar_iniciar_ollama(self) -> bool:
        """
        Intenta iniciar Ollama automáticamente.
        
        Returns:
            bool: True si se inició exitosamente
        """
        logger.warning("⚠️ Intentando iniciar Ollama automáticamente...")
        
        try:
            # Intentar iniciar Ollama en segundo plano (Windows)
            # Nota: En producción, Ollama debería estar como servicio de Windows
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0
            )
            
            # Esperar 5 segundos para que inicie
            time.sleep(5)
            
            # Verificar si inició correctamente
            disponible, mensaje = self.verificar_salud()
            if disponible:
                logger.info("✅ Ollama iniciado exitosamente")
                return True
            else:
                logger.error(f"❌ Ollama no inició correctamente: {mensaje}")
                return False
        except FileNotFoundError:
            logger.error("❌ Comando 'ollama' no encontrado. Instala Ollama: https://ollama.ai")
            return False
        except Exception as e:
            logger.error(f"❌ Error al iniciar Ollama: {e}")
            return False
    
    def asegurar_disponibilidad(self) -> Tuple[bool, str]:
        """
        Asegura que Ollama esté disponible, intentando recuperarlo si es necesario.
        
        Returns:
            (disponible: bool, mensaje: str)
        """
        # Verificar estado actual
        disponible, mensaje = self.verificar_salud()
        
        if disponible:
            return True, mensaje
        
        # Si no está disponible, intentar recuperarlo
        logger.warning(f"⚠️ Ollama no disponible: {mensaje}")
        
        # Intentar iniciar Ollama
        if self.intentar_iniciar_ollama():
            return True, "Ollama recuperado exitosamente"
        
        return False, f"No se pudo recuperar Ollama después de {self.intentos_fallidos} intentos"


# Instancia global del monitor
_monitor = OllamaHealthMonitor()


def verificar_ollama_disponible() -> Tuple[bool, list]:
    """
    Verifica si Ollama está disponible y retorna los modelos.
    Con auto-recuperación integrada.
    
    Returns:
        (disponible: bool, modelos: list)
    """
    disponible, mensaje = _monitor.asegurar_disponibilidad()
    return disponible, _monitor.modelos_disponibles if disponible else []


def llamar_ollama_con_reintentos(
    prompt: str, 
    modelo: str = "llama3.2:1b",
    max_reintentos: int = MAX_REINTENTOS
) -> Tuple[bool, str]:
    """
    Llama a Ollama con reintentos automáticos y backoff exponencial.
    
    Args:
        prompt: Texto del prompt
        modelo: Modelo a usar
        max_reintentos: Número máximo de reintentos
    
    Returns:
        (exito: bool, respuesta_o_error: str)
    """
    for intento in range(max_reintentos):
        try:
            # Asegurar que Ollama esté disponible
            if intento > 0:
                logger.info(f"🔄 Reintento {intento + 1}/{max_reintentos}")
                disponible, mensaje = _monitor.asegurar_disponibilidad()
                if not disponible:
                    logger.warning(f"⚠️ Ollama no disponible en intento {intento + 1}: {mensaje}")
                    time.sleep(2 ** intento)  # Backoff exponencial
                    continue
            
            # Timeout progresivo (más tiempo en cada reintento)
            timeout = TIMEOUT_BASE * (intento + 1)
            
            # Llamar a Ollama
            payload = {
                "model": modelo,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            response = requests.post(
                OLLAMA_API_URL,
                json=payload,
                timeout=timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                respuesta = data.get("response", "").strip()
                
                # Guardar en cache para resiliencia
                guardar_en_cache(prompt, respuesta, modelo)
                
                logger.info(f"✅ Respuesta recibida de Ollama (intento {intento + 1})")
                return True, respuesta
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.warning(f"⚠️ Error en llamada a Ollama: {error_msg}")
                
                if intento < max_reintentos - 1:
                    time.sleep(2 ** intento)
                    continue
                else:
                    return False, error_msg
        
        except requests.exceptions.Timeout:
            logger.warning(f"⏱️ Timeout en intento {intento + 1} (timeout={timeout}s)")
            if intento < max_reintentos - 1:
                time.sleep(2 ** intento)
                continue
            else:
                return False, f"Timeout después de {max_reintentos} intentos"
        
        except requests.exceptions.ConnectionError:
            logger.warning(f"🔌 Error de conexión en intento {intento + 1}")
            # Intentar recuperar Ollama
            _monitor.asegurar_disponibilidad()
            if intento < max_reintentos - 1:
                time.sleep(2 ** intento)
                continue
            else:
                return False, f"No se pudo conectar después de {max_reintentos} intentos"
        
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            if intento < max_reintentos - 1:
                time.sleep(2 ** intento)
                continue
            else:
                return False, f"Error: {str(e)}"
    
    # Si llegamos aquí, todos los reintentos fallaron
    # Intentar usar cache como último recurso
    respuesta_cache = obtener_de_cache(prompt, modelo)
    if respuesta_cache:
        logger.info("♻️ Usando respuesta desde cache")
        return True, respuesta_cache
    
    return False, f"Todos los reintentos fallaron ({max_reintentos} intentos)"


def guardar_en_cache(prompt: str, respuesta: str, modelo: str):
    """Guarda una respuesta en cache para resiliencia"""
    try:
        # Crear hash del prompt para nombre de archivo
        import hashlib
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        cache_file = CACHE_DIR / f"{modelo}_{prompt_hash}.json"
        
        cache_data = {
            "prompt": prompt[:500],  # Solo primeros 500 chars
            "respuesta": respuesta,
            "modelo": modelo,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"No se pudo guardar en cache: {e}")


def obtener_de_cache(prompt: str, modelo: str) -> Optional[str]:
    """Obtiene una respuesta del cache si existe y no ha expirado"""
    try:
        import hashlib
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        cache_file = CACHE_DIR / f"{modelo}_{prompt_hash}.json"
        
        if not cache_file.exists():
            return None
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Verificar si no ha expirado
        timestamp = datetime.fromisoformat(cache_data["timestamp"])
        if datetime.now() - timestamp > CACHE_DURATION:
            return None
        
        return cache_data["respuesta"]
    except Exception as e:
        logger.warning(f"No se pudo leer del cache: {e}")
        return None


def limpiar_cache():
    """Limpia el cache de respuestas antiguas"""
    try:
        count = 0
        for cache_file in CACHE_DIR.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                timestamp = datetime.fromisoformat(cache_data["timestamp"])
                if datetime.now() - timestamp > CACHE_DURATION:
                    cache_file.unlink()
                    count += 1
            except:
                pass
        
        if count > 0:
            logger.info(f"🧹 Limpiado {count} archivos de cache antiguos")
    except Exception as e:
        logger.warning(f"Error limpiando cache: {e}")


def obtener_estado_sistema() -> Dict[str, Any]:
    """
    Obtiene el estado completo del sistema de IA.
    
    Returns:
        Dict con estado detallado
    """
    disponible, mensaje = _monitor.verificar_salud()
    
    return {
        "disponible": disponible,
        "mensaje": mensaje,
        "modelos": _monitor.modelos_disponibles,
        "ultimo_check": _monitor.ultimo_check.isoformat() if _monitor.ultimo_check else None,
        "intentos_fallidos": _monitor.intentos_fallidos,
        "cache_dir": str(CACHE_DIR),
        "archivos_cache": len(list(CACHE_DIR.glob("*.json")))
    }


# Limpiar cache al importar el módulo
limpiar_cache()
