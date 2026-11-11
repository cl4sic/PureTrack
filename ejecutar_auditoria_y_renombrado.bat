@echo off
:: =====================================================================
:: ejecutar_auditoria_y_renombrado.bat
:: Lanzador autónomo para usuarios de Windows (AudioSanitizer)
:: =====================================================================
setlocal enabledelayedexpansion
chcp 65001 >nul
title AudioSanitizer - Suite de Auditoría y Normalización de Audio MP3
color 0B

:: Determinar directorio base del script
set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

:: 1. Detección del motor ejecutable (Compilado .exe o Entorno Python)
set "RUNNER="

if exist "%BASE_DIR%AudioSanitizer.exe" (
    set "RUNNER="%BASE_DIR%AudioSanitizer.exe""
) else if exist "%BASE_DIR%dist\AudioSanitizer\AudioSanitizer.exe" (
    set "RUNNER="%BASE_DIR%dist\AudioSanitizer\AudioSanitizer.exe""
) else (
    :: Comprobar si existe el launcher de Windows 'py' o el binario 'python'
    where py >nul 2>nul
    if !errorlevel! equ 0 (
        set "PY_CMD=py"
    ) else (
        where python >nul 2>nul
        if !errorlevel! equ 0 (
            set "PY_CMD=python"
        ) else (
            set "PY_CMD="
        )
    )

    if not "!PY_CMD!"=="" (
        :: Comprobar si las librerías necesarias están instaladas
        !PY_CMD! -c "import mutagen, soundfile, numpy" >nul 2>nul
        if !errorlevel! neq 0 (
            echo.
            echo ======================================================================
            echo  [CONFIGURACION INICIAL] Instalando librerias necesarias...
            echo ======================================================================
            echo  Instalando dependencias de audio desde requirements.txt...
            !PY_CMD! -m pip install -r requirements.txt
            if !errorlevel! neq 0 (
                echo [!] Hubo un problema instalando las dependencias.
                pause
                exit /b 1
            )
            echo [+] Instalacion completada con exito.
        )
        set "RUNNER=!PY_CMD! "%BASE_DIR%pipeline.py""
    )
)

if "%RUNNER%"=="" (
    echo.
    echo ======================================================================
    echo  [!] ERROR: No se encontro el ejecutable AudioSanitizer.exe ni Python.
    echo ======================================================================
    echo  Para ejecutar esta herramienta en Windows:
    echo  1. Instala Python desde https://www.python.org/downloads/
    echo     (Recuerda marcar la casilla: "Add python.exe to PATH")
    echo  2. O ejecuta previamente 'compilar_exe_en_windows.bat' en un PC con Python.
    echo.
    pause
    exit /b 1
)

:: 2. Verificación de binarios en ./bin/
set "FFMPEG_FOUND=0"
if exist "%BASE_DIR%bin\ffmpeg.exe" set "FFMPEG_FOUND=1"
where ffmpeg >nul 2>nul
if %errorlevel% equ 0 set "FFMPEG_FOUND=1"

:MENU
cls
echo ======================================================================
echo           AUDIO SANITIZER - SUITE PROFESIONAL DE AUDIO MP3
echo               Auditoría Acústica y Normalización ID3v2
echo ======================================================================
echo.
if %FFMPEG_FOUND% equ 0 (
    echo  [!] AVISO: No se detecto 'bin\ffmpeg.exe'.
    echo      Recomendado: coloca 'ffmpeg.exe' en la carpeta 'bin/' para
    echo      analizar integridad y silencios sin depender del sistema.
    echo ----------------------------------------------------------------------
)
echo  Colección a procesar: Archivos .mp3 en esta carpeta
echo.
echo  [1] Auditar Colección (Diagnóstico pasivo: bitrate, duración, clipping)
echo  [2] Simular Renombrado y Metadatos (Modo Dry-Run seguro, no altera nada)
echo  [3] APLICAR RENOMBRADO Y METADATOS OFICIALES (Ejecución real en disco)
echo  [4] Deshacer Cambios (Rollback instantáneo al estado previo)
echo  [5] Salir
echo.
echo ======================================================================
set /p "OPCION=Selecciona una opción [1-5] y presiona ENTER: "

if "%OPCION%"=="1" goto OP_AUDIT
if "%OPCION%"=="2" goto OP_DRYRUN
if "%OPCION%"=="3" goto OP_APPLY
if "%OPCION%"=="4" goto OP_ROLLBACK
if "%OPCION%"=="5" goto SALIR

echo.
echo Opción inválida. Presiona cualquier tecla para reintentar...
pause >nul
goto MENU

:OP_AUDIT
cls
echo ======================================================================
echo  EJECUTANDO FASE 1: AUDITORÍA TÉCNICA Y DIAGNÓSTICO
echo ======================================================================
echo.
%RUNNER% --phase audit
echo.
echo [INFO] Informes generados en 'output/informe_auditoria.md' y '.csv'.
echo.
pause
goto MENU

:OP_DRYRUN
cls
echo ======================================================================
echo  EJECUTANDO FASE 2 & 3: SIMULACIÓN DE METADATOS Y RENOMBRADO (DRY-RUN)
echo ======================================================================
echo.
%RUNNER%
echo.
echo [INFO] Esta simulación NO modificó ningún archivo.
echo        Revisa la propuesta arriba. Si estás conforme, elige la opción [3].
echo.
pause
goto MENU

:OP_APPLY
cls
echo ======================================================================
echo  EJECUTANDO APLICACIÓN REAL DE METADATOS Y RENOMBRADO
echo ======================================================================
echo.
echo  ADVERTENCIA: Esta acción escribirá las etiquetas oficiales ID3v2 y
echo  renombrará los archivos en disco. Se guardará un respaldo para rollback.
echo.
set /p "CONFIRMAR=¿Deseas continuar? (S/N): "
if /i not "%CONFIRMAR%"=="S" (
    echo Operación cancelada por el usuario.
    pause
    goto MENU
)
echo.
%RUNNER% --apply
echo.
echo [INFO] Respaldo de seguridad guardado en 'output/rename_log.json'.
echo.
pause
goto MENU

:OP_ROLLBACK
cls
echo ======================================================================
echo  REVERSIÓN DE SEGURIDAD (ROLLBACK)
echo ======================================================================
echo.
%RUNNER% --rollback
echo.
pause
goto MENU

:SALIR
cls
echo Gracias por usar AudioSanitizer.
timeout /t 2 >nul
exit /b 0
