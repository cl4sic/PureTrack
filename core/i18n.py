#!/usr/bin/env python3
"""
core/i18n.py - Motor Profesional de Internacionalización y Multi-idioma (i18n) para PureTrack.

Soporta:
- Carga de diccionarios JSON desde carpeta locales/ (locales/es.json y locales/en.json).
- Detección automática del idioma del sistema operativo (QLocale / locale de sistema).
- Soporte para fallback automático (idioma seleccionado -> inglés -> clave).
- Cambio de idioma en caliente sin reinicio mediante señales Qt y observadores.
- Resolución de rutas tanto en desarrollo como dentro de bundles congelados de PyInstaller.
"""

import sys
import os
import json
import locale
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List

from PySide6.QtCore import QObject, Signal, QLocale


class TranslationManager(QObject):
    """Gestor singleton de internacionalización y traducción reactiva."""

    sig_language_changed = Signal(str)  # Emite el nuevo código de idioma activo ('es', 'en')

    _instance: Optional["TranslationManager"] = None

    @classmethod
    def instance(cls) -> "TranslationManager":
        if cls._instance is None:
            cls._instance = TranslationManager()
        return cls._instance

    def __init__(self, parent=None):
        super().__init__(parent)
        self._locales_dir = self._find_locales_directory()
        self._translations: Dict[str, Dict[str, Any]] = {}
        self._configured_language: str = "auto"
        self._active_language: str = "en"
        self._config_manager = None
        self._callbacks: List[Callable[[str], None]] = []

        self._load_all_translations()
        self._active_language = self.detect_system_language()

    def _find_locales_directory(self) -> Path:
        """Localiza el directorio locales/ de forma agnóstica al entorno."""
        candidates: List[Path] = []
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            candidates.append(Path(sys._MEIPASS) / "locales")
            candidates.append(Path(sys.executable).resolve().parent / "locales")

        # Entorno de desarrollo local
        here = Path(__file__).resolve().parent.parent
        candidates.append(here / "locales")
        candidates.append(Path.cwd() / "locales")

        for cand in candidates:
            if cand.is_dir():
                return cand.resolve()

        return here / "locales"

    def _load_all_translations(self):
        """Carga en memoria todos los archivos .json encontrados en locales/."""
        self._translations.clear()
        if not self._locales_dir.exists():
            return

        for f in self._locales_dir.glob("*.json"):
            lang_code = f.stem.lower()
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    self._translations[lang_code] = json.load(fp)
            except Exception as e:
                print(f"[!] Error cargando diccionario {f.name}: {e}")

    def detect_system_language(self) -> str:
        """
        Detecta el idioma del sistema operativo.
        Si comienza por 'es', devuelve 'es'; para cualquier otro caso, devuelve 'en' por defecto.
        """
        # 1. Intentar mediante QLocale de PySide6
        try:
            sys_locale = QLocale.system().name().lower()
            if sys_locale.startswith("es"):
                return "es"
        except Exception:
            pass

        # 2. Intentar mediante locale estándar de Python
        try:
            loc = (locale.getdefaultlocale()[0] or "").lower()
            if loc.startswith("es"):
                return "es"
        except Exception:
            pass

        # 3. Intentar mediante variables de entorno del sistema
        for env_var in ["LANG", "LC_ALL", "LC_MESSAGES"]:
            val = os.environ.get(env_var, "").lower()
            if val.startswith("es"):
                return "es"

        return "en"

    def init_with_config(self, config_manager):
        """Inicializa la configuración de idioma a partir del ConfigManager."""
        self._config_manager = config_manager
        configured = config_manager.get("ui_preferences", "language", "auto")
        self.set_language(configured, save_to_config=False)

    def set_language(self, lang_code: str, save_to_config: bool = True):
        """
        Cambia el idioma activo en caliente.
        lang_code puede ser 'auto', 'es' o 'en'.
        """
        self._configured_language = lang_code
        if lang_code == "auto":
            new_active = self.detect_system_language()
        elif lang_code in self._translations:
            new_active = lang_code
        else:
            new_active = "en"

        self._active_language = new_active

        if save_to_config and self._config_manager:
            self._config_manager.set("ui_preferences", "language", self._configured_language)

        # Emitir señal de cambio y ejecutar callbacks registrados
        self.sig_language_changed.emit(self._active_language)
        for cb in self._callbacks:
            try:
                cb(self._active_language)
            except Exception as e:
                print(f"[!] Error ejecutando callback i18n: {e}")

    def get_language(self) -> str:
        """Devuelve el código de idioma activo ('es' o 'en')."""
        return self._active_language

    def get_configured_language(self) -> str:
        """Devuelve el valor configurado ('auto', 'es' o 'en')."""
        return self._configured_language

    def register_callback(self, callback: Callable[[str], None]):
        """Registra un callback a ejecutar inmediatamente al cambiar de idioma."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def t(self, key: str, default: str = "", **kwargs) -> str:
        """
        Traduce una clave con soporte para notación de puntos ('table.col_status')
        e interpolación de variables por palabra clave.
        Fallback: idioma activo -> 'en' -> default -> clave.
        """
        parts = key.split(".")

        # 1. Búsqueda en el idioma activo
        val = self._lookup(self._translations.get(self._active_language, {}), parts)

        # 2. Fallback a inglés ('en') si no existe en el idioma activo
        if val is None and self._active_language != "en":
            val = self._lookup(self._translations.get("en", {}), parts)

        # 3. Fallback a español ('es') si inglés tampoco lo tiene
        if val is None and self._active_language != "es":
            val = self._lookup(self._translations.get("es", {}), parts)

        # 4. Fallback a default o a la clave
        if val is None:
            val = default if default else key

        if not isinstance(val, str):
            return str(val)

        if kwargs:
            try:
                return val.format(**kwargs)
            except Exception:
                return val

        return val

    def _lookup(self, data: Dict[str, Any], parts: List[str]) -> Optional[Any]:
        curr = data
        for p in parts:
            if isinstance(curr, dict) and p in curr:
                curr = curr[p]
            else:
                return None
        return curr

    def get_badge_text(self, verdict_or_status: str) -> str:
        """Traduce de forma inteligente cualquier estado o veredicto de badge a la lengua activa."""
        st = verdict_or_status.upper().strip()
        if "EXCLUID" in st:
            return self.t("badges.excluida", "EXCLUIDA")
        if st in ("APTA", "OK"):
            return self.t("badges.apta", "APTA")
        if "REVIS" in st or "ALERT" in st or "WARN" in st:
            return self.t("badges.alerta", "ALERTA")
        if "ELIMIN" in st or "ERR" in st:
            return self.t("badges.error", "ERROR")
        if "APLIC" in st:
            return self.t("badges.aplicado", "APLICADO")
        if "PEND" in st:
            return self.t("badges.pending", "PENDIENTE")
        return st


# Helpers globales para conveniencia
def get_i18n() -> TranslationManager:
    return TranslationManager.instance()


def t(key: str, default: str = "", **kwargs) -> str:
    return TranslationManager.instance().t(key, default=default, **kwargs)


def tr(key: str, default: str = "", **kwargs) -> str:
    return TranslationManager.instance().t(key, default=default, **kwargs)
