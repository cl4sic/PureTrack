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

from core.config_manager import ConfigManager
from gui.main_window import MainWindow
from gui.styles.theme_loader import load_stylesheet


def main():
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

    # Inicializar y mostrar ventana principal
    window = MainWindow(config_mgr)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
