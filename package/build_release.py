#!/usr/bin/env python3
"""
package/build_release.py - Generador Profesional de Builds y Distribución Multiplataforma.

Soporta:
- Windows: Ejecutable .exe portable (onefile o onedir) empaquetando binarios locales (bin/ffmpeg.exe, etc.).
- Linux: Binario ELF standalone (onefile o onedir) integrando PySide6, mutagen, numpy, soundfile.
"""

import sys
import os
import shutil
import subprocess
import argparse
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"


def check_pyinstaller() -> bool:
    """Verifica la disponibilidad de PyInstaller."""
    try:
        res = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[+] PyInstaller detectado: v{res.stdout.strip()}")
            return True
    except Exception:
        pass
    return False


def build_release(mode: str = "onedir", windowed: bool = True):
    print("=" * 75)
    print(">>> AUDIOMASTER - PROCESO DE COMPILACIÓN Y EMPAQUETADO MULTIPLATAFORMA")
    print("=" * 75)

    if not check_pyinstaller():
        print("[!] ERROR: PyInstaller no está instalado en el entorno de Python.")
        print("    Ejecute: pip install pyinstaller")
        return False

    is_windows = sys.platform.startswith("win")
    sep = ";" if is_windows else ":"
    target_name = "AudioMaster"

    # Preparar parámetros de PyInstaller optimizados
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name", target_name,
        f"--{mode}",
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtGui",
        "--hidden-import", "PySide6.QtWidgets",
        "--exclude-module", "PySide6.QtWebEngineCore",
        "--exclude-module", "PySide6.QtWebEngineWidgets",
        "--exclude-module", "PySide6.QtWebEngineQuick",
        "--exclude-module", "PySide6.QtQml",
        "--exclude-module", "PySide6.QtQuick",
        "--exclude-module", "PySide6.Qt3DCore",
        "--exclude-module", "PySide6.Qt3DRender",
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--collect-all", "mutagen",
        "--collect-all", "soundfile",
        "--collect-all", "numpy",
    ]

    if windowed:
        cmd.append("--windowed")
        if is_windows:
            cmd.append("--noconsole")

    # Añadir módulos de core y gui
    cmd.extend([
        "--add-data", f"{ROOT_DIR / 'core'}{sep}core",
        "--add-data", f"{ROOT_DIR / 'gui'}{sep}gui",
    ])

    # Si existe carpeta bin, incluirla en el paquete
    bin_folder = ROOT_DIR / "bin"
    if bin_folder.exists():
        cmd.extend(["--add-data", f"{bin_folder}{sep}bin"])

    # Archivo de entrada principal
    cmd.append(str(ROOT_DIR / "app.py"))

    print(f"[*] Compilando en modo '{mode}' para {'Windows' if is_windows else 'Linux'}...")
    print("    Comando:", " ".join(cmd))
    res = subprocess.run(cmd)

    if res.returncode != 0:
        print("[!] Error durante la compilación con PyInstaller.")
        return False

    print("\n[+] Compilación completada con éxito.")
    bundle_target = DIST_DIR / target_name
    print(f"    Directorio de distribución: {bundle_target}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compilador PyInstaller para AudioMaster Suite")
    parser.add_argument("--mode", choices=["onedir", "onefile"], default="onedir", help="Modo de empaquetado")
    parser.add_argument("--console", action="store_true", help="Mantener ventana de consola para depuración")
    args = parser.parse_args()

    build_release(mode=args.mode, windowed=not args.console)
