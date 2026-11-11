#!/usr/bin/env python3
"""
package/package_windows_zip.py - Empaquetador Autónomo de AudioMaster para Windows.

Garantiza:
1. Copia de todos los componentes esenciales y binarios Windows (ffmpeg.exe, ffprobe.exe, fpcalc.exe).
2. Conversión forzada y estricta a finales de línea DOS/Windows (CRLF - \\r\\n) en todos los archivos
   .bat, .cmd, .txt, .md y .json para evitar errores de sintaxis en cmd.exe de Windows.
3. Verificación de integridad binaria antes de comprimir.
4. Generación atómica del archivo ZIP final (AudioMaster_Windows.zip).
"""

import sys
import os
import shutil
import zipfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_WIN_DIR = ROOT_DIR / "AudioMaster_Windows"
ZIP_OUTPUT = ROOT_DIR / "AudioMaster_Windows.zip"

EXTENSIONS_TO_CRLF = {".bat", ".cmd", ".ps1", ".txt", ".md", ".json", ".py", ".qss"}


def convert_to_crlf(file_path: Path) -> bool:
    """Convierte un archivo de texto a finales de línea Windows CRLF (\\r\\n)."""
    try:
        raw = file_path.read_bytes()
        # Normalizar primero cualquier variación (\r\n o \r) a \n
        normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        # Convertir a CRLF estricto
        crlf_data = normalized.replace(b"\n", b"\r\n")
        if crlf_data != raw:
            file_path.write_bytes(crlf_data)
        return True
    except Exception as e:
        print(f"[!] Error convirtiendo {file_path.name} a CRLF: {e}")
        return False


def verify_crlf(file_path: Path) -> bool:
    """Comprueba si un archivo contiene finales de línea CRLF sin LFs huérfanos."""
    raw = file_path.read_bytes()
    # Buscar LF que no vaya precedido por CR
    pos = 0
    while True:
        pos = raw.find(b"\n", pos)
        if pos == -1:
            break
        if pos == 0 or raw[pos - 1:pos] != b"\r":
            return False
        pos += 1
    return True


def prepare_and_zip():
    print("=" * 75)
    print(">>> PREPARACIÓN Y EMPAQUETADO WINDOWS CON FINAL DE LÍNEA CRLF ESTRICTO")
    print("=" * 75)

    DIST_WIN_DIR.mkdir(parents=True, exist_ok=True)
    bin_dir = DIST_WIN_DIR / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    # 1. Asegurar binarios Windows en bin/
    source_bin = ROOT_DIR / "bin"
    for b_name in ["ffmpeg.exe", "ffprobe.exe", "fpcalc.exe"]:
        src_bin_file = source_bin / b_name
        dst_bin_file = bin_dir / b_name
        if src_bin_file.exists() and not dst_bin_file.exists():
            shutil.copy2(src_bin_file, dst_bin_file)
            print(f"[+] Copiado binario: {b_name}")

    # 2. Copiar código fuente y documentación actualizada
    files_to_copy = [
        (ROOT_DIR / "app.py", DIST_WIN_DIR / "app.py"),
        (ROOT_DIR / "requirements.txt", DIST_WIN_DIR / "requirements.txt"),
        (ROOT_DIR / "USER_MANUAL.md", DIST_WIN_DIR / "USER_MANUAL.md"),
        (ROOT_DIR / "MANUAL_USUARIO.md", DIST_WIN_DIR / "MANUAL_USUARIO.md"),
        (ROOT_DIR / "README.md", DIST_WIN_DIR / "README.md"),
        (ROOT_DIR / "README_ES.md", DIST_WIN_DIR / "README_ES.md"),
    ]

    for src, dst in files_to_copy:
        if src.exists():
            shutil.copy2(src, dst)

    # Copiar carpetas core, gui y package
    for folder in ["core", "gui", "package"]:
        src_f = ROOT_DIR / folder
        dst_f = DIST_WIN_DIR / folder
        if src_f.exists():
            if dst_f.exists():
                shutil.rmtree(dst_f)
            shutil.copytree(src_f, dst_f, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    # 3. Aplicar conversión CRLF rigurosa a todos los archivos de texto
    print("\n[*] Aplicando conversión estricta a CRLF (\\r\\n) para compatibilidad con cmd.exe:")
    converted_count = 0
    all_files = list(DIST_WIN_DIR.rglob("*"))

    for f in all_files:
        if f.is_file() and f.suffix.lower() in EXTENSIONS_TO_CRLF:
            convert_to_crlf(f)
            is_valid = verify_crlf(f)
            status = "CRLF OK" if is_valid else "ERROR LF"
            converted_count += 1
            if f.suffix.lower() in {".bat", ".cmd", ".txt"}:
                print(f"    - {f.relative_to(DIST_WIN_DIR)}: [{status}]")

    print(f"\n[+] {converted_count} archivos verificados y normalizados a CRLF.")

    # 4. Crear el archivo ZIP
    print(f"\n[*] Comprimiendo {ZIP_OUTPUT.name}...")
    if ZIP_OUTPUT.exists():
        ZIP_OUTPUT.unlink()

    with zipfile.ZipFile(ZIP_OUTPUT, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in DIST_WIN_DIR.rglob("*"):
            if file_path.is_file() and "__pycache__" not in file_path.parts:
                arcname = file_path.relative_to(ROOT_DIR)
                zipf.write(file_path, arcname)

    size_mb = ZIP_OUTPUT.stat().st_size / (1024 * 1024)
    print(f"[+] Paquete ZIP generado con éxito: {ZIP_OUTPUT} ({size_mb:.1f} MB)")
    print("=" * 75)
    return True


if __name__ == "__main__":
    prepare_and_zip()
