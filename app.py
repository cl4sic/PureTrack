#!/usr/bin/env python3
"""
app.py - Punto de Entrada Principal para la Suite Desktop PureTrack.

Inicializa:
- QApplication con soporte High-DPI y codificación UTF-8.
- Gestor centralizado de configuración (ConfigManager).
- Motor de internacionalización y detección de idioma (TranslationManager).
- Tema AIMP Dark (Ámbar / Cian).
- Icono profesional multiplataforma (gui/assets/icon.png e icon.ico).
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
from core.i18n import get_i18n
from gui.main_window import MainWindow
from gui.styles.theme_loader import load_stylesheet


def resolve_puretrack_icon() -> QIcon:
    """Resuelve la ruta del icono de PureTrack tanto en desarrollo como dentro de PyInstaller."""
    candidates_dir = []
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        meipass = Path(sys._MEIPASS)
        candidates_dir.append(meipass / "gui" / "assets")
        candidates_dir.append(meipass / "assets")
        candidates_dir.append(meipass)

    candidates_dir.append(APP_ROOT / "gui" / "assets")
    candidates_dir.append(APP_ROOT / "assets")

    for ad in candidates_dir:
        if sys.platform.startswith("win"):
            ico_path = ad / "icon.ico"
            if ico_path.exists():
                return QIcon(str(ico_path))
        png_path = ad / "icon.png"
        if png_path.exists():
            return QIcon(str(png_path))
        ico_path = ad / "icon.ico"
        if ico_path.exists():
            return QIcon(str(ico_path))

    return QIcon()


def main():
    # En Windows, asociar App ID explícito para fijar el icono en la barra de tareas
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PureTrackLab.PureTrack.Suite.2.0")
        except Exception:
            pass

    # Configuración de atributos para renderizado nítido en pantallas modernas
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("PureTrack")
    app.setApplicationDisplayName("PureTrack")
    app.setOrganizationName("PureTrackLab")
    app.setOrganizationDomain("puretrack.local")

    # Cargar gestor de configuración persistente
    config_mgr = ConfigManager()

    # Inicializar motor de internacionalización i18n
    i18n = get_i18n()
    i18n.init_with_config(config_mgr)

    # Cargar y aplicar tema AIMP Dark
    theme = config_mgr.get("ui_preferences", "accent_theme", "amber")
    app.setStyleSheet(load_stylesheet(theme))

    # Configurar icono oficial para ventana y barra de tareas
    app_icon = resolve_puretrack_icon()
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
