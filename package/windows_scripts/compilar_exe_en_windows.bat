@echo off
:: =====================================================================
:: compilar_exe_en_windows.bat
:: Compila de forma nativa PureTrack.exe autónomo único con PyInstaller en Windows
:: =====================================================================
chcp 65001 >nul
title Compilador PureTrack para Windows
color 0A

echo ======================================================================
echo           COMPILADOR DE PURETRACK PARA WINDOWS (ONEFILE)
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
echo 2. Instalando PyInstaller y dependencias de PureTrack...
%PY_CMD% -m pip install --upgrade pip
%PY_CMD% -m pip install -r requirements.txt
%PY_CMD% -m pip install pyinstaller

echo.
echo 3. Compilando PureTrack.exe en un único archivo autónomo...
%PY_CMD% package/build_release.py --mode onefile

echo.
echo ======================================================================
echo  [+] COMPILACION FINALIZADA CON EXITO.
echo      El ejecutable autónomo único se encuentra en:
echo      dist\PureTrack.exe
echo ======================================================================
echo.
set /p ABRIR="Desea iniciar PureTrack ahora? (S/N): "
if /i "%ABRIR%"=="S" (
    echo Iniciando PureTrack...
    start "" "dist\PureTrack.exe"
)
exit /b 0
