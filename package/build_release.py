#!/usr/bin/env python3
"""
package/build_release.py - Generador Autónomo de Ejecutable Único (--onefile) para PureTrack.

Soporta:
- Windows: Ejecutable único autónomo PureTrack.exe / PureTrack-Windows-x64.exe (--onefile, --windowed, --icon).
  Incrusta ffmpeg.exe, ffprobe.exe y fpcalc.exe con --add-binary para extracción automática en sys._MEIPASS.
- Linux: Binario standalone PureTrack / PureTrack-Linux-x64 (--onefile, --windowed).
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


def build_release(name: str = "PureTrack", mode: str = "onefile", windowed: bool = True):
    print("=" * 75)
    print(">>> PURETRACK - COMPILACIÓN DE EJECUTABLE ÚNICO AUTÓNOMO")
    print("=" * 75)

    if not check_pyinstaller():
        print("[!] ERROR: PyInstaller no está instalado en el entorno de Python.")
        print("    Ejecute: pip install pyinstaller")
        return False

    is_windows = sys.platform.startswith("win")
    sep = ";" if is_windows else ":"
    target_name = name

    # Garantizar presencia de binarios de audio en bin/
    try:
        from package.ensure_binaries import main as ensure_binaries_main
        ensure_binaries_main()
    except Exception as e:
        print(f"[!] Aviso al asegurar binarios de audio: {e}")

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

    # Archivo de recursos y metadatos PE para Windows (mitiga SmartScreen de publisher desconocido)
    version_file = ROOT_DIR / "package" / "version_info.txt"
    if is_windows and version_file.exists():
        cmd.extend(["--version-file", str(version_file)])
        print(f"[+] Aplicando metadatos de versión de Windows: {version_file.name}")

    # Icono oficial multiplataforma
    ico_path = ROOT_DIR / "gui" / "assets" / "icon.ico"
    png_path = ROOT_DIR / "gui" / "assets" / "icon.png"
    if is_windows and ico_path.exists():
        cmd.extend(["--icon", str(ico_path)])
    elif png_path.exists():
        cmd.extend(["--icon", str(png_path)])

    if windowed:
        cmd.append("--windowed")
        if is_windows:
            cmd.append("--noconsole")

    # Añadir módulos de core, gui y locales
    cmd.extend([
        "--add-data", f"{ROOT_DIR / 'core'}{sep}core",
        "--add-data", f"{ROOT_DIR / 'gui'}{sep}gui",
        "--add-data", f"{ROOT_DIR / 'locales'}{sep}locales",
    ])

    # Si existen binarios en bin/, incrustarlos usando --add-binary para que queden disponibles en sys._MEIPASS
    bin_folder = ROOT_DIR / "bin"
    if bin_folder.exists():
        for b_file in bin_folder.iterdir():
            if b_file.is_file() and b_file.name != "README.md":
                cmd.extend(["--add-binary", f"{b_file}{sep}bin"])
                print(f"[+] Incrustando binario autónomo: {b_file.name}")

    # Archivo de entrada principal
    cmd.append(str(ROOT_DIR / "app.py"))

    print(f"[*] Compilando ejecutable único en modo '{mode}' para {'Windows' if is_windows else 'Linux'}...")
    print("    Comando:", " ".join(cmd))
    res = subprocess.run(cmd)

    if res.returncode != 0:
        print("[!] Error durante la compilación con PyInstaller.")
        return False

    print("\n[+] Compilación completada con éxito.")
    output_ext = ".exe" if is_windows else ""
    if mode == "onefile":
        out_file = DIST_DIR / f"{target_name}{output_ext}"
        print(f"    Ejecutable generado: {out_file}")
    else:
        out_dir = DIST_DIR / target_name
        print(f"    Directorio generado: {out_dir}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compilador PyInstaller para PureTrack Suite")
    parser.add_argument("--name", default="PureTrack", help="Nombre del ejecutable de salida")
    parser.add_argument("--mode", choices=["onefile", "onedir"], default="onefile", help="Modo de empaquetado (por defecto onefile)")
    parser.add_argument("--console", action="store_true", help="Mantener ventana de consola para depuración")
    args = parser.parse_args()

    build_release(name=args.name, mode=args.mode, windowed=not args.console)
