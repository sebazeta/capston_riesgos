@echo off
REM Script de inicio automático de Ollama para Windows
REM Coloca este archivo en el menú Inicio para que se ejecute al arrancar Windows

echo ==========================================
echo   INICIANDO OLLAMA - IA LOCAL
echo ==========================================
echo.

REM Activar entorno virtual
call C:\capston_riesgos\.venv\Scripts\activate.bat

REM Iniciar Ollama
python C:\capston_riesgos\iniciar_ollama.py

REM Mantener ventana abierta si hay error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Presiona cualquier tecla para cerrar...
    pause >nul
)
