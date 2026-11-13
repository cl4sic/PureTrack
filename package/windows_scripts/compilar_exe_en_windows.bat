@echo off
:: =====================================================================
:: compilar_exe_en_windows.bat
:: Compila de forma nativa AudioMaster.exe portable con PyInstaller en Windows
:: =====================================================================
chcp 65001 >nul
title Compilador AudioMaster para Windows
color 0A

echo ======================================================================
echo           COMPILADOR DE AUDIOMASTER PARA WINDOWS
echo ======================================================================
echo.
echo 1. Comprobando instalacion de Python...
where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        echo [!] ERROR: Python no esta instalado en este equipo.
        echo     Descarga e instala Python desde: https://www.python.org/downloads/
        echo     (Marca la casilla "Add Python to PATH")
        pause
        exit /b 1
    )
    set "PY_CMD=py"
) else (
    set "PY_CMD=python"
)

echo [+] Python detectado.
echo.
echo 2. Instalando PyInstaller y dependencias de AudioMaster...
%PY_CMD% -m pip install --upgrade pip
%PY_CMD% -m pip install -r requirements.txt
%PY_CMD% -m pip install pyinstaller

echo.
echo 3. Compilando AudioMaster.exe...
%PY_CMD% package/build_release.py --mode onedir

echo.
echo ======================================================================
echo  [+] COMPILACION FINALIZADA CON EXITO.
echo      El ejecutable autonomo se encuentra en:
echo      dist\AudioMaster\AudioMaster.exe
echo ======================================================================
echo.
set /p ABRIR="Desea iniciar AudioMaster ahora? (S/N): "
if /i "%ABRIR%"=="S" (
    echo Iniciando AudioMaster...
    start "" "dist\AudioMaster\AudioMaster.exe"
)
exit /b 0
