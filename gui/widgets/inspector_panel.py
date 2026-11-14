#!/usr/bin/env python3
"""
gui/widgets/inspector_panel.py - Panel de Ajustes y Auditoría Colapsable (AIMP Style).

Contiene:
1. Constructor visual de patrones y tokens dinámicos (PatternBuilder).
2. Mapeo configurable de etiquetas ID3v2 (TIT2, TPE1, TALB, etc.).
3. Toggles y sliders de umbrales acústicos (clipping, silencios, bitrate, duración).
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QSlider,
    QGroupBox,
    QScrollArea,
    QFrame,
    QLineEdit,
    QPushButton
)
from PySide6.QtCore import Qt, Signal
from core.config_manager import ConfigManager
from core.i18n import t, get_i18n
from gui.widgets.pattern_builder import PatternBuilder


class InspectorPanel(QWidget):
    """Panel lateral derecho con ajustes de normalización y auditoría."""

    settings_changed = Signal()

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._init_ui()
        self.retranslate_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Contenedor desplazable para permitir interfaces compactas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        # -------------------------------------------------------------
        # 1. SECCIÓN: CONSTRUCTOR DE PATRONES
        # -------------------------------------------------------------
        self.pattern_group = QGroupBox("Formato de Nombres (Pattern Builder)")
        pg_layout = QVBoxLayout(self.pattern_group)
        pg_layout.setContentsMargins(10, 14, 10, 10)
        pg_layout.setSpacing(8)

        self.pattern_builder = PatternBuilder(self.config_manager)
        self.pattern_builder.pattern_changed.connect(lambda: self.settings_changed.emit())
        pg_layout.addWidget(self.pattern_builder)
        layout.addWidget(self.pattern_group)

        # -------------------------------------------------------------
        # 2. SECCIÓN: UMBRALES Y TOGGLES DE AUDITORÍA ACÚSTICA
        # -------------------------------------------------------------
        self.audit_group = QGroupBox("Criterios de Auditoría y Diagnóstico")
        ag_layout = QVBoxLayout(self.audit_group)
        ag_layout.setContentsMargins(10, 14, 10, 10)
        ag_layout.setSpacing(10)

        thresholds = self.config_manager.get("audit_thresholds", default={})

        # Checkbox Clipping
        self.chk_clipping = QCheckBox("Detectar Clipping / Saturación digital (> 0 dBFS)")
        self.chk_clipping.setChecked(thresholds.get("check_clipping", True))
        self.chk_clipping.toggled.connect(self._on_audit_toggle_changed)
        ag_layout.addWidget(self.chk_clipping)

        # Checkbox Silencios
        self.chk_silence = QCheckBox("Detectar Silencios anómalos (> 3.0s en cuerpo)")
        self.chk_silence.setChecked(thresholds.get("check_silence", True))
        self.chk_silence.toggled.connect(self._on_audit_toggle_changed)
        ag_layout.addWidget(self.chk_silence)

        # Checkbox Corte Abrupto
        self.chk_abrupt = QCheckBox("Detectar Corte Abrupto final (sin fade-out)")
        self.chk_abrupt.setChecked(thresholds.get("check_abrupt_ending", True))
        self.chk_abrupt.toggled.connect(self._on_audit_toggle_changed)
        ag_layout.addWidget(self.chk_abrupt)

        # Slider Bitrate Mínimo
        br_val = thresholds.get("min_bitrate_kbps", 190)
        br_layout = QHBoxLayout()
        self.lbl_bitrate = QLabel(f"Bitrate mínimo aceptable: {br_val} kbps")
        self.lbl_bitrate.setStyleSheet("color: #d1d5db; font-size: 11px;")
        br_layout.addWidget(self.lbl_bitrate)
        ag_layout.addLayout(br_layout)

        self.slider_bitrate = QSlider(Qt.Orientation.Horizontal)
        self.slider_bitrate.setRange(128, 320)
        self.slider_bitrate.setSingleStep(32)
        self.slider_bitrate.setValue(br_val)
        self.slider_bitrate.valueChanged.connect(self._on_bitrate_slider_changed)
        ag_layout.addWidget(self.slider_bitrate)

        # Slider Duración Mínima
        dur_val = int(thresholds.get("min_duration_sec", 60.0))
        dur_layout = QHBoxLayout()
        self.lbl_duration = QLabel(f"Duración mínima de pista: {dur_val}s")
        self.lbl_duration.setStyleSheet("color: #d1d5db; font-size: 11px;")
        dur_layout.addWidget(self.lbl_duration)
        ag_layout.addLayout(dur_layout)

        self.slider_duration = QSlider(Qt.Orientation.Horizontal)
        self.slider_duration.setRange(10, 120)
        self.slider_duration.setSingleStep(5)
        self.slider_duration.setValue(dur_val)
        self.slider_duration.valueChanged.connect(self._on_duration_slider_changed)
        ag_layout.addWidget(self.slider_duration)

        layout.addWidget(self.audit_group)

        # -------------------------------------------------------------
        # 3. SECCIÓN: MAPEO CONFIGURABLE DE ETIQUETAS ID3v2
        # -------------------------------------------------------------
        self.id3_group = QGroupBox("Mapeo de Etiquetas ID3v2")
        id3_layout = QVBoxLayout(self.id3_group)
        id3_layout.setContentsMargins(10, 14, 10, 10)
        id3_layout.setSpacing(6)

        id3_cfg = self.config_manager.get("id3_mapping", default={})
        self.tag_inputs = {}
        for tag, default_val in [
            ("TIT2 (Título)", id3_cfg.get("TIT2", "{title}{remix}")),
            ("TPE1 (Artistas)", id3_cfg.get("TPE1", "{all_artists}")),
            ("TALB (Álbum)", id3_cfg.get("TALB", "{album}")),
            ("TPE2 (Artista Álbum)", id3_cfg.get("TPE2", "{album_artists}")),
            ("TCON (Género)", id3_cfg.get("TCON", "{genre}")),
            ("TDRC (Año)", id3_cfg.get("TDRC", "{year}")),
        ]:
            row = QHBoxLayout()
            tag_lbl = QLabel(tag.split()[0] + ":")
            tag_lbl.setFixedWidth(50)
            tag_lbl.setStyleSheet("color: #8b8e98; font-family: monospace; font-size: 11px;")
            line = QLineEdit(default_val)
            line.setStyleSheet("font-family: monospace; font-size: 11px;")
            line.textChanged.connect(self._on_tag_mapping_changed)
            self.tag_inputs[tag.split()[0]] = line
            row.addWidget(tag_lbl)
            row.addWidget(line)
            id3_layout.addLayout(row)

        layout.addWidget(self.id3_group)
        layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def retranslate_ui(self):
        """Actualiza los textos del panel de ajustes e inspector según el idioma activo."""
        self.pattern_group.setTitle(t("inspector.naming_title"))
        self.audit_group.setTitle(t("inspector.audit_rules_title"))
        self.id3_group.setTitle(t("inspector.title"))
        self.chk_clipping.setText(t("inspector.chk_clipping"))
        self.chk_silence.setText(t("inspector.chk_silence"))
        self.chk_abrupt.setText(t("inspector.chk_abrupt"))
        self.lbl_bitrate.setText(f"{t('inspector.min_bitrate')} {self.slider_bitrate.value()} kbps")
        self.lbl_duration.setText(f"{t('inspector.min_duration')} {self.slider_duration.value()}s")
        self.pattern_builder.retranslate_ui()

    def _on_audit_toggle_changed(self):
        self.config_manager.set("audit_thresholds", "check_clipping", self.chk_clipping.isChecked(), auto_save=False)
        self.config_manager.set("audit_thresholds", "check_silence", self.chk_silence.isChecked(), auto_save=False)
        self.config_manager.set("audit_thresholds", "check_abrupt_ending", self.chk_abrupt.isChecked(), auto_save=True)
        self.settings_changed.emit()

    def _on_bitrate_slider_changed(self, value: int):
        self.lbl_bitrate.setText(f"Bitrate mínimo aceptable: {value} kbps")
        self.config_manager.set("audit_thresholds", "min_bitrate_kbps", value, auto_save=True)
        self.settings_changed.emit()

    def _on_duration_slider_changed(self, value: int):
        self.lbl_duration.setText(f"Duración mínima de pista: {value}s")
        self.config_manager.set("audit_thresholds", "min_duration_sec", float(value), auto_save=True)
        self.settings_changed.emit()

    def _on_tag_mapping_changed(self):
        for tag, input_widget in self.tag_inputs.items():
            self.config_manager.set("id3_mapping", tag, input_widget.text(), auto_save=False)
        self.config_manager.save()
        self.settings_changed.emit()

    def get_audit_settings(self) -> dict:
        return self.config_manager.get("audit_thresholds", default={})

    def get_pattern(self) -> str:
        return self.pattern_builder.get_pattern()
