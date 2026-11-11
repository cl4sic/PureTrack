#!/usr/bin/env python3
"""
common_utils.py - Backward compatibility shim forwarding to core.common_utils.
"""
from core.common_utils import (
    WINDOWS_FORBIDDEN_CHARS_PATTERN,
    WINDOWS_RESERVED_NAMES,
    sanitize_windows_filename,
    to_extended_length_path,
    resolve_binary,
)

__all__ = [
    "WINDOWS_FORBIDDEN_CHARS_PATTERN",
    "WINDOWS_RESERVED_NAMES",
    "sanitize_windows_filename",
    "to_extended_length_path",
    "resolve_binary",
]

if __name__ == "__main__":
    import core.common_utils as ccu
    print("[*] Comprobando localización de binarios:")
    for b in ["ffmpeg", "ffprobe", "fpcalc"]:
        loc = ccu.resolve_binary(b)
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
        print(f"    Saneado : {ccu.sanitize_windows_filename(s)}")
