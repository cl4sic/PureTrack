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

import shutil
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap

from core.config_manager import ConfigManager
from core.i18n import get_i18n
from gui.main_window import MainWindow
from gui.styles.theme_loader import load_stylesheet


def ensure_linux_desktop_integration(png_path: Path):
    """
    En Linux (Wayland y X11), instala la entrada de escritorio y el icono en hicolor
    para que el dock de GNOME/XFCE/KDE, el selector de ventanas y la barra de tareas
    muestren el icono oficial de PureTrack sin depender de lanzadores manuales.
    """
    if not sys.platform.startswith("linux"):
        return

    try:
        home = Path.home()
        apps_dir = home / ".local" / "share" / "applications"
        icons_dir = home / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps"
        apps_dir.mkdir(parents=True, exist_ok=True)
        icons_dir.mkdir(parents=True, exist_ok=True)

        target_icon = icons_dir / "puretrack.png"
        if not target_icon.exists() and png_path.exists():
            shutil.copy2(png_path, target_icon)

        desktop_file = apps_dir / "puretrack.desktop"
        exe_path = sys.executable if getattr(sys, "frozen", False) else f"{sys.executable} {APP_ROOT / 'app.py'}"
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=PureTrack
GenericName=Audio Sanitizer & Tagger
Comment=Suite profesional de auditoría técnica acústica y metadatos
Exec={exe_path}
Icon=puretrack
Terminal=false
Categories=AudioVideo;Audio;AudioVideoEditing;
StartupWMClass=PureTrack
"""
        if not desktop_file.exists():
            desktop_file.write_text(desktop_content, encoding="utf-8")
            desktop_file.chmod(0o755)
    except Exception:
        pass


def resolve_puretrack_icon() -> QIcon:
    """
    Resuelve y construye un QIcon multi-resolución (16px a 1024px)
    compatible con Windows (ICO/Shell), X11 (_NET_WM_ICON) y Wayland (app_id).
    """
    candidates_dir = []
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        meipass = Path(sys._MEIPASS)
        candidates_dir.append(meipass / "gui" / "assets")
        candidates_dir.append(meipass / "assets")
        candidates_dir.append(meipass)

    candidates_dir.append(APP_ROOT / "gui" / "assets")
    candidates_dir.append(APP_ROOT / "assets")

    png_found: Optional[Path] = None
    ico_found: Optional[Path] = None

    for ad in candidates_dir:
        p_png = ad / "icon.png"
        p_ico = ad / "icon.ico"
        if not png_found and p_png.exists():
            png_found = p_png
        if not ico_found and p_ico.exists():
            ico_found = p_ico

    icon = QIcon()

    # Cargar múltiples capas de resolución a partir del PNG maestro vectorial
    if png_found and png_found.exists():
        master_pixmap = QPixmap(str(png_found))
        if not master_pixmap.isNull():
            for size in (16, 24, 32, 48, 64, 128, 256, 512, 1024):
                scaled = master_pixmap.scaled(
                    size, size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                icon.addPixmap(scaled)

        # En Linux, asegurar integración con entorno de escritorio
        ensure_linux_desktop_integration(png_found)

    # En Windows, agregar capas del archivo .ico
    if ico_found and ico_found.exists():
        icon.addFile(str(ico_found))

    return icon


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
    app.setDesktopFileName("puretrack.desktop")

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
