#!/usr/bin/env python3
"""
core/config_manager.py - Gestor de Configuración, Presets y Preferencias Persistentes.

Maneja la persistencia en formato JSON (UTF-8) para:
- Patrones de renombrado dinámicos ({artist}, {feat}, {title}, {remix}, {album}, {year}, {genre}).
- Mapeo configurable de etiquetas ID3v2.
- Umbrales y toggles de auditoría técnica (clipping, silencios, cortes abruptos, bitrate, duración).
- Preferencias de interfaz (idioma, tema ámbar/cian, última carpeta utilizada, dry-run).

Prioridad de almacenamiento:
1. Archivo local config.json (modo portable si existe).
2. QStandardPaths.AppConfigLocation / PureTrack / config.json.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from PySide6.QtCore import QStandardPaths
    HAS_QT = True
except ImportError:
    HAS_QT = False


DEFAULT_CONFIG: Dict[str, Any] = {
    "version": "1.0.0",
    "naming": {
        "current_pattern": "{artist}{feat} - {title}{remix}",
        "active_preset": "Estándar EDM / Pop",
        "presets": {
            "Estándar EDM / Pop": "{artist}{feat} - {title}{remix}",
            "Estricto Artista - Título": "{artist} - {title}",
            "Álbum y Año": "{year} - {album} - {artist} - {title}{remix}",
            "DJ Extended / Remix": "{artist}{feat} - {title} ({remix})"
        }
    },
    "id3_mapping": {
        "TIT2": "{title}{remix}",
        "TPE1": "{all_artists}",
        "TALB": "{album}",
        "TPE2": "{album_artists}",
        "TCON": "{genre}",
        "TDRC": "{year}"
    },
    "audit_thresholds": {
        "check_clipping": True,
        "clipping_threshold_pct": 0.5,
        "check_silence": True,
        "silence_threshold_sec": 3.0,
        "check_abrupt_ending": True,
        "abrupt_rms_threshold_dbfs": -14.0,
        "min_bitrate_kbps": 190,
        "min_duration_sec": 60.0
    },
    "ui_preferences": {
        "language": "auto",       # "auto", "es", "en"
        "accent_theme": "amber",  # "amber" (#ff9800) o "cyan" (#00b4d8)
        "last_source_dir": "",
        "last_target_dir": "",
        "dry_run_default": True,
        "auto_backup": True,
        "max_threads": 4
    }
}

SAMPLE_TRACK = {
    "main_artists": ["Martin Garrix", "DallasK"],
    "guest_artists": [],
    "feat_artists": ["Sasha Alex Sloan"],
    "remix_artists": ["Brooks"],
    "title": "Loop",
    "remix_name": "Brooks Remix",
    "album": "Loop (Remixes)",
    "album_artists": ["Martin Garrix", "DallasK"],
    "genre": "Future Bounce",
    "year": "2022",
    "bitrate_kbps": 320,
    "duration_sec": 194.5
}


class ConfigManager:
    """Administrador centralizado de configuración con guardado atómico en UTF-8."""

    def __init__(self, custom_path: Optional[Path] = None):
        self.config_path = self._resolve_config_path(custom_path)
        self.config_data: Dict[str, Any] = {}
        self.load()

    def _resolve_config_path(self, custom_path: Optional[Path]) -> Path:
        if custom_path:
            return Path(custom_path).resolve()

        # 1. Comprobar modo portable (config.json en el directorio raíz de la app)
        app_dir = Path(__file__).resolve().parent.parent
        portable_config = app_dir / "config.json"
        if portable_config.exists():
            return portable_config

        # 2. Intentar ruta estándar de usuario del sistema operativo
        try:
            if HAS_QT:
                base_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
                target_dir = Path(base_dir) / "PureTrack"
            else:
                if sys.platform.startswith("win"):
                    appdata = os.getenv("APPDATA", str(Path.home() / "AppData" / "Roaming"))
                    target_dir = Path(appdata) / "PureTrack"
                else:
                    target_dir = Path.home() / ".config" / "PureTrack"

            # Migración automática transparente si existe configuración previa de AudioMaster
            old_dirs = []
            if HAS_QT:
                old_dirs.append(Path(base_dir) / "AudioMaster")
            if sys.platform.startswith("win"):
                old_dirs.append(Path(os.getenv("APPDATA", "")) / "AudioMaster")
            else:
                old_dirs.append(Path.home() / ".config" / "AudioMaster")

            for od in old_dirs:
                if od.exists() and (od / "config.json").exists() and not (target_dir / "config.json").exists():
                    target_dir.mkdir(parents=True, exist_ok=True)
                    import shutil
                    shutil.copy2(od / "config.json", target_dir / "config.json")
                    break

            target_dir.mkdir(parents=True, exist_ok=True)
            # Verificar permiso real de escritura
            test_file = target_dir / ".write_test"
            test_file.touch()
            test_file.unlink()
            return target_dir / "config.json"
        except (OSError, PermissionError):
            # Fallback limpio al directorio de la aplicación (modo local/portátil)
            return app_dir / "config.json"

    def load(self) -> Dict[str, Any]:
        """Carga la configuración desde el archivo JSON o crea la predeterminada."""
        if not self.config_path.exists():
            self.config_data = self._deep_copy(DEFAULT_CONFIG)
            self.save()
            return self.config_data

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            # Fusión profunda con valores por defecto para asegurar todas las claves
            self.config_data = self._deep_merge(self._deep_copy(DEFAULT_CONFIG), loaded)
        except Exception:
            # En caso de corrupción, recupera valores por defecto
            self.config_data = self._deep_copy(DEFAULT_CONFIG)
            self.save()

        return self.config_data

    def save(self) -> bool:
        """Guarda la configuración atómicamente con indentación y UTF-8 explícito."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self.config_path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            tmp_path.replace(self.config_path)
            return True
        except Exception as e:
            print(f"[!] Error guardando configuración en {self.config_path}: {e}")
            return False

    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """Obtiene un valor de una sección específica."""
        sec_data = self.config_data.get(section, {})
        if key is None:
            return sec_data
        if isinstance(sec_data, dict):
            return sec_data.get(key, default)
        return default

    def set(self, section: str, key: str, value: Any, auto_save: bool = True):
        """Asigna y opcionalmente persiste un valor."""
        if section not in self.config_data or not isinstance(self.config_data[section], dict):
            self.config_data[section] = {}
        self.config_data[section][key] = value
        if auto_save:
            self.save()

    def set_pattern(self, pattern: str, preset_name: Optional[str] = None):
        """Actualiza el patrón activo y opcionalmente el nombre de preset."""
        if "naming" not in self.config_data:
            self.config_data["naming"] = {}
        self.config_data["naming"]["current_pattern"] = pattern
        if preset_name:
            self.config_data["naming"]["active_preset"] = preset_name
            if "presets" not in self.config_data["naming"]:
                self.config_data["naming"]["presets"] = {}
            self.config_data["naming"]["presets"][preset_name] = pattern
        self.save()

    def get_presets(self) -> Dict[str, str]:
        """Obtiene el diccionario de todos los presets disponibles."""
        return dict(self.config_data.get("naming", {}).get("presets", DEFAULT_CONFIG["naming"]["presets"]))

    def add_preset(self, name: str, pattern: str) -> bool:
        """Crea o guarda un nuevo preset personalizado y lo marca como activo."""
        if not name or not pattern:
            return False
        if "naming" not in self.config_data:
            self.config_data["naming"] = {}
        if "presets" not in self.config_data["naming"]:
            self.config_data["naming"]["presets"] = {}
        self.config_data["naming"]["presets"][name] = pattern
        self.config_data["naming"]["active_preset"] = name
        self.config_data["naming"]["current_pattern"] = pattern
        self.save()
        return True

    def delete_preset(self, name: str) -> bool:
        """Elimina un preset existente asegurando que quede al menos uno activo."""
        presets = self.config_data.get("naming", {}).get("presets", {})
        if name in presets:
            if len(presets) <= 1:
                return False  # No eliminar el único preset existente
            del presets[name]
            if self.config_data.get("naming", {}).get("active_preset") == name:
                new_active = next(iter(presets.keys()))
                self.config_data["naming"]["active_preset"] = new_active
                self.config_data["naming"]["current_pattern"] = presets[new_active]
            self.save()
            return True
        return False

    def get_pattern(self) -> str:
        return self.config_data.get("naming", {}).get("current_pattern", "{artist}{feat} - {title}{remix}")

    def reset_defaults(self):
        """Restaura los valores por defecto."""
        self.config_data = self._deep_copy(DEFAULT_CONFIG)
        self.save()

    @staticmethod
    def render_pattern(pattern: str, track_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Interpola tokens dinámicos para construir el nombre del archivo.
        Tokens: {artist}, {feat}, {guest}, {title}, {remix}, {album}, {year}, {genre}, {all_artists}
        """
        data = track_data or SAMPLE_TRACK

        main_artists = data.get("main_artists", ["Artist"])
        feat_artists = data.get("feat_artists", [])
        guest_artists = data.get("guest_artists", [])
        remix_artists = data.get("remix_artists", [])
        title = data.get("title", "Track")
        remix_name = data.get("remix_name", "")
        album = data.get("album", "Album")
        album_artists = data.get("album_artists", main_artists)
        genre = data.get("genre", "Electronic")
        year = str(data.get("year", "2025"))

        # Formateo de tokens
        artist_str = " & ".join(main_artists) if main_artists else "Unknown Artist"
        feat_str = f" feat. {' & '.join(feat_artists)}" if feat_artists else ""
        guest_str = f" & {' & '.join(guest_artists)}" if guest_artists else ""
        remix_str = f" - {remix_name}" if remix_name else ""

        all_p = []
        for a in main_artists + guest_artists + feat_artists + remix_artists:
            if a not in all_p:
                all_p.append(a)
        all_artists_str = ", ".join(all_p) if all_p else artist_str
        album_artists_str = ", ".join(album_artists) if album_artists else artist_str

        replacements = {
            "{artist}": artist_str,
            "{feat}": feat_str,
            "{guest}": guest_str,
            "{title}": title,
            "{remix}": remix_str,
            "{album}": album,
            "{year}": year,
            "{genre}": genre,
            "{all_artists}": all_artists_str,
            "{album_artists}": album_artists_str,
        }

        result = pattern
        for token, val in replacements.items():
            result = result.replace(token, val)

        # Normalizar espacios duplicados y guiones colgantes
        result = re.sub(r"\s+", " ", result)
        result = re.sub(r"\s-\s-\s", " - ", result)
        result = result.strip(" -")
        if not result.lower().endswith(".mp3"):
            result += ".mp3"

        return result

    def _deep_copy(self, d: Dict[str, Any]) -> Dict[str, Any]:
        return json.loads(json.dumps(d))

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                base[k] = self._deep_merge(base[k], v)
            else:
                base[k] = v
        return base
