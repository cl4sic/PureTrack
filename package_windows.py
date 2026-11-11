#!/usr/bin/env python3
"""
package_windows.py - Generador de Bundle y Empaquetado para Windows (PyInstaller).

Prepara la distribución autónoma para usuarios de Windows sin Python instalado:
1. Verifica la presencia de PyInstaller (o guía su instalación).
2. Compila el ejecutable 'AudioSanitizer.exe' integrando dependencias (mutagen, soundfile, numpy).
3. Estructura el directorio final 'dist/AudioSanitizer/' con:
   - AudioSanitizer.exe
   - Carpeta ./bin/ preparada para ffmpeg.exe, ffprobe.exe y fpcalc.exe
   - ejecutar_auditoria_y_renombrado.bat
   - INSTRUCCIONES_WINDOWS.txt
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
BUNDLE_DIR = DIST_DIR / "AudioSanitizer"
BIN_DIR = BUNDLE_DIR / "bin"


def check_pyinstaller() -> bool:
    """Verifica si PyInstaller está disponible en el entorno."""
    try:
        res = subprocess.run(["pyinstaller", "--version"], capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[+] PyInstaller detectado: v{res.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass

    try:
        import PyInstaller  # noqa: F401
        print("[+] Módulo PyInstaller detectado en Python.")
        return True
    except ImportError:
        pass

    return False


def build_bundle(mode: str = "onedir"):
    """Ejecuta PyInstaller para compilar el proyecto."""
    print("=" * 70)
    print(">>> PREPARACIÓN DE DISTRIBUCIÓN AUTÓNOMA PARA WINDOWS")
    print("=" * 70)

    if not check_pyinstaller():
        print("\n[!] ERROR: PyInstaller no está instalado en este entorno.")
        print("    Para instalarlo, ejecuta:")
        print("        pip install pyinstaller")
        print("\n    En Windows, también puedes instalarlo ejecutando:")
        print("        python -m pip install pyinstaller\n")
        return False

    print("\n[*] Limpiando artefactos previos de compilación...")
    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR, ignore_errors=True)

    # Parámetros de compilación para PyInstaller
    # Separador de add-data según plataforma (: en Linux, ; en Windows)
    sep = ";" if sys.platform.startswith("win") else ":"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name", "AudioSanitizer",
        f"--{mode}",
        "--collect-all", "mutagen",
        "--collect-all", "soundfile",
        "--collect-all", "numpy",
        "--add-data", f"{ROOT_DIR / 'common_utils.py'}{sep}.",
        "--add-data", f"{ROOT_DIR / 'audit_audio.py'}{sep}.",
        "--add-data", f"{ROOT_DIR / 'enrich_metadata.py'}{sep}.",
        str(ROOT_DIR / "pipeline.py"),
    ]

    print(f"[*] Ejecutando PyInstaller ({mode})...")
    print("    Comando:", " ".join(cmd))
    res = subprocess.run(cmd)

    if res.returncode != 0:
        print("[!] Error durante la compilación con PyInstaller.")
        return False

    print("\n[+] Compilación base finalizada con éxito.")

    # Crear estructura final de distribución
    print("[*] Creando estructura de distribución en dist/AudioSanitizer/...")
    BIN_DIR.mkdir(parents=True, exist_ok=True)

    # Copiar archivo .bat a la raíz del bundle para el usuario final
    bat_src = ROOT_DIR / "ejecutar_auditoria_y_renombrado.bat"
    if bat_src.exists():
        shutil.copy2(bat_src, BUNDLE_DIR / "ejecutar_auditoria_y_renombrado.bat")
        print("    - Copiado: ejecutar_auditoria_y_renombrado.bat")

    # Copiar README o crear INSTRUCCIONES_WINDOWS.txt
    instructions_path = BUNDLE_DIR / "INSTRUCCIONES_WINDOWS.txt"
    instructions_content = """========================================================================
 GUIA RÁPIDA DE USO PARA WINDOWS - AudioSanitizer
========================================================================

¡Hola! Esta herramienta audita, repara metadatos oficiales y renombra tus archivos .mp3
sin alterar su calidad ni requerir instalaciones complicadas.

------------------------------------------------------------------------
 PASO 1: BINARIOS REQUERIDOS (Solo la primera vez)
------------------------------------------------------------------------
Para funcionar de forma 100% autónoma, coloca en la carpeta 'bin/' los siguientes
tres archivos ejecutables para Windows:

1. ffmpeg.exe   (Descarga desde: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip)
2. ffprobe.exe  (Viene dentro del mismo ZIP de ffmpeg, carpeta bin/)
3. fpcalc.exe   (Descarga desde: https://acoustid.org/chromaprint -> Windows binario)

(Nota: Si ya tienes FFmpeg instalado en tu sistema y en el PATH, funcionará automáticamente).

------------------------------------------------------------------------
 PASO 2: CÓMO USAR
------------------------------------------------------------------------
1. Coloca tus archivos .mp3 en esta misma carpeta (junto a ejecutar_auditoria_y_renombrado.bat).
2. Haz DOBLE CLIC sobre:
      ejecutar_auditoria_y_renombrado.bat
3. Selecciona una opción del menú interactivo:
      [1] Auditar Colección (Verifica errores, duración y bitrate)
      [2] Simular Renombrado (Dry-Run seguro sin modificar nada)
      [3] Aplicar Renombrado y Metadatos Oficiales
      [4] Deshacer Cambios (Rollback instantáneo al estado original)
      [5] Salir

¡Listo! Todos los informes y respaldos se guardarán en la carpeta 'output/'.
========================================================================
"""
    with open(instructions_path, "w", encoding="utf-8") as f:
        f.write(instructions_content)
    print("    - Generado: INSTRUCCIONES_WINDOWS.txt")

    print("\n" + "=" * 70)
    print(">>> PAQUETE PARA WINDOWS PREPARADO CON ÉXITO")
    print("=" * 70)
    print(f"Ruta del paquete listo para distribuir: {BUNDLE_DIR}")
    print("Contenido:")
    for item in sorted(BUNDLE_DIR.iterdir()):
        print(f"  - {item.name}{'/' if item.is_dir() else ''}")
    print("\nSiguiente paso: Colocar ffmpeg.exe, ffprobe.exe y fpcalc.exe en 'dist/AudioSanitizer/bin/'")
    print("y comprimir 'dist/AudioSanitizer/' en un archivo ZIP para compartir.")
    return True


if __name__ == "__main__":
    mode_arg = "onedir"
    if "--onefile" in sys.argv:
        mode_arg = "onefile"
    build_bundle(mode=mode_arg)
