"""
SCRIPT DE INICIO AUTOMÁTICO DE OLLAMA
=====================================
Asegura que Ollama esté siempre corriendo al iniciar el sistema.
"""
import subprocess
import time
import requests
import sys

def verificar_ollama():
    """Verifica si Ollama está corriendo"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def iniciar_ollama():
    """Inicia Ollama si no está corriendo"""
    if verificar_ollama():
        print("✅ Ollama ya está corriendo")
        return True
    
    print("🚀 Iniciando Ollama...")
    try:
        # Iniciar Ollama en segundo plano
        proceso = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        
        # Esperar a que inicie (máximo 10 segundos)
        for i in range(10):
            time.sleep(1)
            if verificar_ollama():
                print(f"✅ Ollama iniciado exitosamente (PID: {proceso.pid})")
                return True
            print(f"⏳ Esperando... ({i+1}/10)")
        
        print("❌ Ollama no inició en 10 segundos")
        return False
    except FileNotFoundError:
        print("❌ Comando 'ollama' no encontrado")
        print("   Instala Ollama desde: https://ollama.ai")
        return False
    except Exception as e:
        print(f"❌ Error al iniciar Ollama: {e}")
        return False

if __name__ == "__main__":
    if iniciar_ollama():
        print("\n🎉 Sistema listo para usar IA")
        sys.exit(0)
    else:
        print("\n⚠️ No se pudo iniciar Ollama")
        print("   Inicia manualmente con: ollama serve")
        sys.exit(1)
