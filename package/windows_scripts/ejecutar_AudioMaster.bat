@echo off
:: =====================================================================
:: ejecutar_AudioMaster.bat
:: Lanzador directo de 1 clic para AudioMaster.exe en Windows
:: =====================================================================
chcp 65001 >nul
title AudioMaster Suite

if exist "dist\AudioMaster\AudioMaster.exe" (
    start "" "dist\AudioMaster\AudioMaster.exe"
    exit /b 0
)

echo ======================================================================
echo           AUDIOMASTER SUITE - EJECUTABLE NO ENCONTRADO
echo ======================================================================
echo.
echo  El ejecutable autonomo aun no ha sido compilado.
echo  Iniciando proceso de compilacion automatica de 1 clic...
echo.
call compilar_exe_en_windows.bat
