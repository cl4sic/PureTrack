#!/usr/bin/env python3
"""
gui/styles/theme_loader.py - Cargador dinámico de estilos con soporte para paletas AIMP Ámbar y Cian.
"""

from pathlib import Path

THEME_COLORS = {
    "amber": {
        "accent": "#ff9800",
        "accent_hover": "#ffa726",
        "accent_pressed": "#f57c00",
        "accent_glow": "rgba(255, 152, 0, 0.25)",
        "name": "Ámbar AIMP Clásico"
    },
    "cyan": {
        "accent": "#00b4d8",
        "accent_hover": "#48cae4",
        "accent_pressed": "#0096c7",
        "accent_glow": "rgba(0, 180, 216, 0.25)",
        "name": "Cian Tecnológico Moderno"
    }
}


def load_stylesheet(palette: str = "amber") -> str:
    """Carga y adapta dinámicamente el stylesheet QSS con la paleta de acento seleccionada."""
    qss_path = Path(__file__).resolve().parent / "aimp_dark.qss"
    if not qss_path.exists():
        return ""

    with open(qss_path, "r", encoding="utf-8") as f:
        content = f.read()

    color_cfg = THEME_COLORS.get(palette.lower(), THEME_COLORS["amber"])
    if palette.lower() == "cyan":
        content = content.replace("#ff9800", color_cfg["accent"])
        content = content.replace("#ffa726", color_cfg["accent_hover"])
        content = content.replace("#f57c00", color_cfg["accent_pressed"])
        content = content.replace("rgba(255, 152, 0, 0.25)", color_cfg["accent_glow"])

    return content
