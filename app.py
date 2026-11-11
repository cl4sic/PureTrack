#!/usr/bin/env python3
"""
app.py - Punto de Entrada Principal para la Suite Desktop AudioMaster.

Inicializa:
- QApplication con soporte High-DPI y codificación UTF-8.
- Gestor centralizado de configuración (ConfigManager).
- Tema AIMP Dark (Ámbar / Cian).
- Ventana principal reactiva (MainWindow).
"""

import sys
import os
from pathlib import Path

# Garantizar que el directorio raíz de la app se encuentre en sys.path
APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from core.config_manager import ConfigManager
from gui.main_window import MainWindow
from gui.styles.theme_loader import load_stylesheet


def resolve_app_icon(icon_style: str = "b_cyberwave") -> QIcon:
    """Resuelve la ruta del icono de la aplicación según el estilo seleccionado."""
    style_map = {
        "a_disc": "icon_concept_a_disc",
        "b_cyberwave": "icon_concept_b_cyberwave",
        "c_shield": "icon_concept_c_shield",
    }
    base_name = style_map.get(icon_style, "icon_concept_b_cyberwave")
    icons_dir = APP_ROOT / "gui" / "icons"

    # En Windows preferir .ico si existe para soporte multirresolución en la barra de tareas
    if sys.platform.startswith("win"):
        ico_file = icons_dir / f"{base_name}.ico"
        if ico_file.exists():
            return QIcon(str(ico_file))

    png_file = icons_dir / f"{base_name}.png"
    if png_file.exists():
        return QIcon(str(png_file))

    # Fallback genérico
    fallback = icons_dir / "app_icon.png"
    if fallback.exists():
        return QIcon(str(fallback))

    return QIcon()


def main():
    # En Windows, asociar App ID explícito para fijar el icono en la barra de tareas
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AudioMasterLab.AudioMaster.Suite.2.0")
        except Exception:
            pass

    # Configuración de atributos para renderizado nítido en pantallas modernas
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("AudioMaster")
    app.setApplicationDisplayName("AudioMaster Suite")
    app.setOrganizationName("AudioMasterLab")
    app.setOrganizationDomain("audiomaster.local")

    # Cargar gestor de configuración persistente
    config_mgr = ConfigManager()

    # Cargar y aplicar tema AIMP Dark
    theme = config_mgr.get("ui_preferences", "accent_theme", "amber")
    app.setStyleSheet(load_stylesheet(theme))

    # Configurar icono oficial para ventana y barra de tareas
    icon_style = config_mgr.get("ui_preferences", "icon_style", "b_cyberwave")
    app_icon = resolve_app_icon(icon_style)
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    # Inicializar y mostrar ventana principal
    window = MainWindow(config_mgr)
    if not app_icon.isNull():
        window.setWindowIcon(app_icon)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
