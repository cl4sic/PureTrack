@echo off
:: =====================================================================
:: compilar_exe_en_windows.bat
:: Compila AudioSanitizer.exe de forma nativa en un PC con Windows
:: =====================================================================
chcp 65001 >nul
title Compilador de AudioSanitizer para Windows
color 0A

echo ======================================================================
echo           COMPILADOR DE AUDIOSANITIZER PARA WINDOWS
echo ======================================================================
echo.
echo 1. Comprobando instalación de Python...
where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        echo [!] ERROR: Python no esta instalado en este equipo.
        echo     Descarga e instala Python desde: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    set "PY_CMD=py"
) else (
    set "PY_CMD=python"
)

echo [+] Python detectado.
echo.
echo 2. Instalando PyInstaller y dependencias necesarias...
%PY_CMD% -m pip install --upgrade pip
%PY_CMD% -m pip install -r requirements.txt
%PY_CMD% -m pip install pyinstaller

echo.
echo 3. Iniciando compilación de AudioSanitizer.exe...
%PY_CMD% package_windows.py

echo.
echo ======================================================================
echo  [+] COMPILACIÓN FINALIZADA.
echo      El ejecutable se ha creado en la carpeta 'dist/AudioSanitizer/'.
echo ======================================================================
echo.
pause
