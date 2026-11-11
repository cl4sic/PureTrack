#!/usr/bin/env python3
"""
common_utils.py - Utilidades de Compatibilidad Multiplataforma (Windows/Linux/macOS).

Proporciona:
1. Localización autónoma de binarios externos (ffmpeg, ffprobe, fpcalc) priorizando ./bin/ y bundles PyInstaller.
2. Saneamiento estricto de nombres de archivo para compatibilidad NTFS en Windows (WinError 123).
3. Estandarización de rutas mediante pathlib.Path y codificación UTF-8.
"""

import sys
import shutil
import re
from pathlib import Path
from typing import Optional, Union, List


# Caracteres no permitidos en nombres de archivos NTFS / FAT en Windows: \ / : * ? " < > |
WINDOWS_FORBIDDEN_CHARS_PATTERN = re.compile(r'[\*\?<>\|]')
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10))
}


def sanitize_windows_filename(filename: str) -> str:
    """
    Sanea un nombre de archivo para evitar errores 'WinError 123' en Windows / NTFS.
    
    Reglas aplicadas:
    - Reemplaza ':' por ' -' (habitual en subtítulos y títulos musicales).
    - Reemplaza '/' y '\\' por '-'.
    - Reemplaza comillas dobles '"' por comillas simples "'".
    - Elimina '*', '?', '<', '>', '|'.
    - Elimina caracteres de control ASCII (0-31).
    - Elimina espacios o puntos finales en el nombre base (prohibidos en Windows).
    - Protege contra nombres de dispositivos reservados en DOS/Windows (CON, PRN, AUX, NUL, COM1-9, LPT1-9).
    - Limita la longitud del nombre a 240 caracteres para respetar MAX_PATH.
    """
    if not filename:
        return "unnamed_track.mp3"

    # Sustituciones semánticas limpias
    name = filename.replace(":", " -")
    name = name.replace("/", "-").replace("\\", "-")
    name = name.replace('"', "'")

    # Eliminación de caracteres estrictamente prohibidos
    name = WINDOWS_FORBIDDEN_CHARS_PATTERN.sub("", name)

    # Filtrar caracteres de control ASCII
    name = "".join(ch for ch in name if ord(ch) >= 32)

    # Normalizar espacios y guiones múltiples
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"-+", "-", name)
    name = name.strip()

    # Descomponer en stem y extensión mediante pathlib.Path
    p = Path(name)
    stem = p.stem.rstrip(". ")
    ext = p.suffix

    if not stem:
        stem = "audio_track"

    # Verificación de nombres reservados de Windows
    if stem.upper() in WINDOWS_RESERVED_NAMES:
        stem = f"_{stem}"

    # Limitar longitud para evitar rebasar MAX_PATH (260 caracteres)
    max_stem_length = 240 - len(ext)
    if len(stem) > max_stem_length:
        stem = stem[:max_stem_length].rstrip(". ")

    return f"{stem}{ext}".strip()


def resolve_binary(binary_name: str, search_dir: Optional[Union[str, Path]] = None) -> str:
    """
    Localiza de forma autónoma la ruta al binario ejecutable (ffmpeg, ffprobe, fpcalc).
    
    Orden de resolución de prioridad:
    1. Bundle congelado de PyInstaller (sys._MEIPASS / bin / binary_name).
    2. Directorio ./bin/ local adyacente al ejecutable o al script principal.
    3. Directorio ./bin/ en el search_dir o en el directorio de trabajo actual (Path.cwd() / 'bin').
    4. PATH global del sistema operativo (shutil.which).
    
    Soporta automáticamente extensiones con o sin '.exe' en Windows.
    """
    candidates: List[Path] = []
    # Posibles variantes de nombre (con y sin .exe)
    variants = [binary_name]
    if not binary_name.lower().endswith(".exe"):
        variants.append(f"{binary_name}.exe")

    # 1. Directorio temporal de PyInstaller (onefile / onedir)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_frozen = Path(sys._MEIPASS)
        for var in variants:
            candidates.append(base_frozen / "bin" / var)
            candidates.append(base_frozen / var)

    # 2. Directorio adyacente al ejecutable compilado (sys.executable)
    if getattr(sys, "frozen", False):
        exe_parent = Path(sys.executable).resolve().parent
        for var in variants:
            candidates.append(exe_parent / "bin" / var)
            candidates.append(exe_parent / var)

    # 3. Directorio adyacente al script actual (common_utils.py)
    script_dir = Path(__file__).resolve().parent
    for var in variants:
        candidates.append(script_dir / "bin" / var)

    # 4. Search dir si fue proporcionado
    if search_dir:
        s_path = Path(search_dir).resolve()
        for var in variants:
            candidates.append(s_path / "bin" / var)
            candidates.append(s_path / var)

    # 5. Directorio de trabajo actual (CWD)
    cwd = Path.cwd()
    for var in variants:
        candidates.append(cwd / "bin" / var)

    # Comprobar candidatos en orden
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate.resolve())

    # 6. Búsqueda en PATH del sistema
    for var in variants:
        found_path = shutil.which(var)
        if found_path:
            return str(Path(found_path).resolve())

    # Fallback predeterminado si no se localiza
    return binary_name


if __name__ == "__main__":
    # Verificaciones básicas de funcionamiento
    print("[*] Comprobando localización de binarios:")
    for b in ["ffmpeg", "ffprobe", "fpcalc"]:
        loc = resolve_binary(b)
        print(f"    - {b:7s} -> {loc}")

    print("\n[*] Comprobando saneamiento de nombres para Windows:")
    samples = [
        'Martin Garrix: Loop (Official) / Remix?.mp3',
        'Avicii feat. Aloe Blacc - SOS <Extended> | Version*.mp3',
        'CON.mp3',
        'Track with trailing space and dot. .mp3',
        'Quote "Test" & Slash \\ Name.mp3'
    ]
    for s in samples:
        print(f"    Original: {s}")
        print(f"    Saneado : {sanitize_windows_filename(s)}")
