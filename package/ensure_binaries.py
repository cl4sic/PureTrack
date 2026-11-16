#!/usr/bin/env python3
"""
package/ensure_binaries.py - Verificador y Descargador Autónomo de Binarios de Audio.

Garantiza la presencia de:
- Windows: bin/ffmpeg.exe, bin/ffprobe.exe, bin/fpcalc.exe
- Linux: bin/ffmpeg, bin/ffprobe, bin/fpcalc

Se invoca antes de empaquetar con PyInstaller para asegurar que los ejecutables autónomos
incluyan siempre el motor de análisis completo.
"""

import sys
import os
import shutil
import urllib.request
import zipfile
import tarfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
BIN_DIR = ROOT_DIR / "bin"


def ensure_bin_dir():
    BIN_DIR.mkdir(parents=True, exist_ok=True)


def setup_windows_binaries():
    print("[*] Comprobando binarios de audio para Windows en bin/...")
    ensure_bin_dir()

    ffmpeg_target = BIN_DIR / "ffmpeg.exe"
    ffprobe_target = BIN_DIR / "ffprobe.exe"
    fpcalc_target = BIN_DIR / "fpcalc.exe"

    # 1. FFmpeg y FFprobe
    if not ffmpeg_target.exists() or not ffprobe_target.exists():
        # Intentar localizar en el sistema
        sys_ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
        sys_ffprobe = shutil.which("ffprobe") or shutil.which("ffprobe.exe")

        if sys_ffmpeg and sys_ffprobe:
            print(f"[+] Copiando FFmpeg desde PATH del sistema: {sys_ffmpeg}")
            shutil.copy2(sys_ffmpeg, ffmpeg_target)
            print(f"[+] Copiando FFprobe desde PATH del sistema: {sys_ffprobe}")
            shutil.copy2(sys_ffprobe, ffprobe_target)
        else:
            print("[*] Descargando FFmpeg estático para Windows...")
            temp_zip = Path(os.environ.get("TEMP", "/tmp")) / "ffmpeg_dl.zip"
            # GitHub releases mirror confiable para FFmpeg Windows x64
            ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            try:
                urllib.request.urlretrieve(ffmpeg_url, str(temp_zip))
                with zipfile.ZipFile(temp_zip, 'r') as z:
                    for member in z.namelist():
                        if member.lower().endswith("ffmpeg.exe"):
                            with z.open(member) as source, open(ffmpeg_target, "wb") as dest:
                                shutil.copyfileobj(source, dest)
                        elif member.lower().endswith("ffprobe.exe"):
                            with z.open(member) as source, open(ffprobe_target, "wb") as dest:
                                shutil.copyfileobj(source, dest)
                print("[+] FFmpeg y FFprobe extraídos con éxito a bin/")
            except Exception as e:
                print(f"[!] Advertencia al descargar FFmpeg: {e}")

    # 2. fpcalc (Chromaprint)
    if not fpcalc_target.exists():
        sys_fpcalc = shutil.which("fpcalc") or shutil.which("fpcalc.exe")
        if sys_fpcalc:
            print(f"[+] Copiando fpcalc desde PATH: {sys_fpcalc}")
            shutil.copy2(sys_fpcalc, fpcalc_target)
        else:
            print("[*] Descargando fpcalc estático para Windows...")
            temp_fp = Path(os.environ.get("TEMP", "/tmp")) / "fpcalc_dl.zip"
            fp_url = "https://github.com/acoustid/chromaprint/releases/download/v1.5.1/chromaprint-fpcalc-1.5.1-windows-x86_64.zip"
            try:
                urllib.request.urlretrieve(fp_url, str(temp_fp))
                with zipfile.ZipFile(temp_fp, 'r') as z:
                    for member in z.namelist():
                        if member.lower().endswith("fpcalc.exe"):
                            with z.open(member) as source, open(fpcalc_target, "wb") as dest:
                                shutil.copyfileobj(source, dest)
                print("[+] fpcalc.exe extraído con éxito a bin/")
            except Exception as e:
                print(f"[!] Advertencia al descargar fpcalc: {e}")


def setup_linux_binaries():
    print("[*] Comprobando binarios de audio para Linux en bin/...")
    ensure_bin_dir()

    for bname in ["ffmpeg", "ffprobe", "fpcalc"]:
        target = BIN_DIR / bname
        if not target.exists():
            w = shutil.which(bname)
            if w:
                print(f"[+] Copiando {bname} desde sistema ({w}) a bin/...")
                shutil.copy2(w, target)
                target.chmod(0o755)
            else:
                print(f"[!] Aviso: {bname} no encontrado en PATH del sistema.")


def main():
    if sys.platform.startswith("win"):
        setup_windows_binaries()
    else:
        setup_linux_binaries()

    print("[✓] Verificación de binarios completada:")
    for f in BIN_DIR.iterdir():
        if f.is_file():
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"    - {f.name} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
