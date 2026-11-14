@echo off
:: =====================================================================
:: ejecutar_PureTrack.bat
:: Lanzador directo de 1 clic para PureTrack.exe en Windows
:: =====================================================================
chcp 65001 >nul
title PureTrack Suite

if exist "dist\PureTrack\PureTrack.exe" (
    start "" "dist\PureTrack\PureTrack.exe"
    exit /b 0
)

echo ======================================================================
echo           PURETRACK SUITE - EJECUTABLE NO ENCONTRADO
echo ======================================================================
echo.
echo  El ejecutable autonomo aun no ha sido compilado.
echo  Iniciando proceso de compilacion automatica de 1 clic...
echo.
call compilar_exe_en_windows.bat
