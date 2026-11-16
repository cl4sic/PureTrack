#!/usr/bin/env python3
"""
core/common_utils.py - Utilidades de Compatibilidad Multiplataforma (Windows/Linux/macOS).

Proporciona:
1. Localización autónoma de binarios externos (ffmpeg, ffprobe, fpcalc) priorizando ./bin/ y bundles PyInstaller.
2. Saneamiento estricto de nombres de archivo para compatibilidad NTFS en Windows (WinError 123).
3. Manejo de rutas largas en Windows mediante prefijo \\?\\.
4. Estandarización de rutas mediante pathlib.Path y codificación UTF-8.
"""

import sys
import os
import shutil
import re
import subprocess
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


def to_extended_length_path(path: Union[str, Path]) -> str:
    """
    Añade el prefijo \\?\\ a rutas absolutas en Windows para superar el límite MAX_PATH (260 chars).
    En sistemas POSIX (Linux/macOS), devuelve la ruta normalizada sin modificar.
    """
    p_str = os.path.abspath(str(path))
    if sys.platform.startswith("win"):
        if not p_str.startswith("\\\\?\\") and not p_str.startswith("\\\\.\\"):
            if p_str.startswith("\\\\"):
                # UNC path: \\server\share -> \\?\UNC\server\share
                return "\\\\?\\UNC" + p_str[1:]
            return "\\\\?\\" + p_str
    return p_str


def resolve_binary(binary_name: str, search_dir: Optional[Union[str, Path]] = None) -> str:
    """
    Localiza de forma autónoma la ruta al binario ejecutable (ffmpeg, ffprobe, fpcalc).
    
    Orden de resolución de prioridad:
    1. Bundle congelado de PyInstaller (sys._MEIPASS / bin / binary_name).
    2. Directorio ./bin/ local adyacente al ejecutable o al script principal.
    3. Directorio ./bin/ en el search_dir o en el directorio de trabajo actual.
    4. PATH global del sistema operativo (shutil.which).
    
    Soporta automáticamente extensiones con o sin '.exe' en Windows.
    """
    is_windows = sys.platform.startswith("win")
    
    # Construcción ordenada de candidatos
    def get_search_paths(name: str) -> List[Path]:
        c: List[Path] = []
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            bf = Path(sys._MEIPASS)
            c.extend([bf / "bin" / name, bf / name])
        if getattr(sys, "frozen", False):
            ep = Path(sys.executable).resolve().parent
            c.extend([ep / "bin" / name, ep / name])
        if search_dir:
            sp = Path(search_dir).resolve()
            c.extend([sp / name, sp / "bin" / name])
            if sp.is_dir():
                for sub in sp.glob("bin*"):
                    if sub.is_dir():
                        c.append(sub / name)
        mr = Path(__file__).resolve().parent.parent
        c.extend([mr / "bin" / name, mr / name])
        cwd = Path.cwd()
        c.extend([cwd / "bin" / name, cwd / name])
        return c

    if is_windows:
        # En Windows preferir .exe primero
        names_to_try = [f"{binary_name}.exe" if not binary_name.lower().endswith(".exe") else binary_name, binary_name]
        for name in names_to_try:
            for cand in get_search_paths(name):
                if cand.is_file():
                    return str(cand.resolve())
            w = shutil.which(name)
            if w:
                return str(Path(w).resolve())
    else:
        # En Linux/macOS preferir binarios nativos (sin .exe)
        native_name = binary_name[:-4] if binary_name.lower().endswith(".exe") else binary_name
        for cand in get_search_paths(native_name):
            if cand.is_file():
                return str(cand.resolve())
        w_native = shutil.which(native_name)
        if w_native:
            return str(Path(w_native).resolve())

        # Fallback para pruebas o entornos emulados (.exe)
        exe_name = f"{native_name}.exe"
        for cand in get_search_paths(exe_name):
            if cand.is_file():
                return str(cand.resolve())
        w_exe = shutil.which(exe_name)
        if w_exe:
            return str(Path(w_exe).resolve())

    # Fallback predeterminado si no se localiza
    return binary_name


def get_hidden_subprocess_kwargs() -> dict:
    """
    Retorna los flags de creación y startupinfo necesarios para evitar que aparezcan
    ventanas negras de consola emergentes en Windows al ejecutar subprocesos
    (como ffmpeg.exe, ffprobe.exe, fpcalc.exe).
    """
    kwargs = {}
    if sys.platform == "win32" or sys.platform.startswith("win"):
        # CREATE_NO_WINDOW = 0x08000000
        create_no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        kwargs["creationflags"] = create_no_window
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        kwargs["startupinfo"] = startupinfo
    return kwargs


def run_hidden_subprocess(cmd: Union[List[str], str], **kwargs) -> subprocess.CompletedProcess:
    """
    Ejecuta un subproceso de forma silenciosa garantizando que en Windows
    no aparezca ninguna ventana de consola negra parpadeante (cmd.exe).
    Garantiza codificación UTF-8 con reemplazo de caracteres para prevenir UnicodeDecodeError en Windows.
    """
    hidden_kwargs = get_hidden_subprocess_kwargs()
    if "creationflags" in kwargs and "creationflags" in hidden_kwargs:
        kwargs["creationflags"] |= hidden_kwargs["creationflags"]
    elif "creationflags" in hidden_kwargs:
        kwargs["creationflags"] = hidden_kwargs["creationflags"]

    if "startupinfo" not in kwargs and "startupinfo" in hidden_kwargs:
        kwargs["startupinfo"] = hidden_kwargs["startupinfo"]

    if kwargs.get("text") or kwargs.get("universal_newlines"):
        if "encoding" not in kwargs:
            kwargs["encoding"] = "utf-8"
        if "errors" not in kwargs:
            kwargs["errors"] = "replace"

    return subprocess.run(cmd, **kwargs)
