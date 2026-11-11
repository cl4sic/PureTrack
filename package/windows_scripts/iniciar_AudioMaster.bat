@echo off
:: =====================================================================
:: iniciar_AudioMaster.bat
:: Lanzador autónomo de 1 clic para Windows (AudioMaster Suite)
:: =====================================================================
chcp 65001 >nul
title AudioMaster Suite
color 0F

echo ======================================================================
echo             AUDIOMASTER SUITE - INICIANDO APLICACIÓN
echo ======================================================================
echo.

:: 1. Comprobar instalación de Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        echo [!] ERROR: Python no esta instalado en este equipo.
        echo.
        echo     Por favor, descarga e instala Python 3.10 o superior:
        echo     https://www.python.org/downloads/
        echo.
        echo     (IMPORTANTE: Marca la casilla "Add python.exe to PATH" durante la instalacion)
        echo.
        pause
        exit /b 1
    )
    set "PY_CMD=py"
) else (
    set "PY_CMD=python"
)

:: 2. Comprobar dependencias requeridas (PySide6, mutagen, etc.)
%PY_CMD% -c "import PySide6, mutagen, soundfile, numpy" >nul 2>nul
if %errorlevel% neq 0 (
    echo [*] Verificando e instalando componentes necesarios (primera ejecucion)...
    %PY_CMD% -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [!] Error al instalar las dependencias con pip.
        pause
        exit /b 1
    )
    echo [+] Componentes instalados correctamente.
    echo.
)

:: 3. Lanzar la aplicación
echo [+] Lanzando AudioMaster Desktop Suite...
start "" %PY_CMD% app.py
exit /b 0
