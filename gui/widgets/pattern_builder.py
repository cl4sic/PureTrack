#!/usr/bin/env python3
"""
gui/widgets/pattern_builder.py - Constructor Visual de Patrones Dinámicos.

Permite:
- Edición libre del patrón con tokens dinámicos ({artist}, {feat}, {title}, etc.).
- Inserción rápida mediante botones / chips interactivos.
- Selección de presets guardados.
- Previsualización dinámica en tiempo real con una pista de prueba.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QFrame,
    QScrollArea,
    QInputDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from core.config_manager import ConfigManager, SAMPLE_TRACK
from core.i18n import t, get_i18n


class PatternBuilder(QWidget):
    """Componente interactivo para construir patrones de renombrado y previsualizarlos en vivo."""

    pattern_changed = Signal(str)

    TOKENS = [
        ("{artist}", "Artista"),
        ("{feat}", "Feat"),
        ("{guest}", "Guest"),
        ("{title}", "Título"),
        ("{remix}", "Remix"),
        ("{album}", "Álbum"),
        ("{year}", "Año"),
        ("{genre}", "Género"),
    ]

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._init_ui()
        self.retranslate_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 1. Selector de Presets + Controles de Creación/Edición
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(6)
        self.lbl_preset = QLabel("Preset:")
        preset_layout.addWidget(self.lbl_preset)

        self.preset_combo = QComboBox()
        self._reload_presets_combo()
        self.preset_combo.currentTextChanged.connect(self._on_preset_selected)
        preset_layout.addWidget(self.preset_combo, stretch=1)

        self.btn_save_preset = QPushButton("Guardar")
        self.btn_save_preset.setStyleSheet("padding: 3px 8px; font-size: 11px;")
        self.btn_save_preset.clicked.connect(self._save_current_preset)
        preset_layout.addWidget(self.btn_save_preset)

        self.btn_new_preset = QPushButton("+ Nuevo")
        self.btn_new_preset.setStyleSheet("padding: 3px 8px; font-size: 11px;")
        self.btn_new_preset.clicked.connect(self._create_new_preset)
        preset_layout.addWidget(self.btn_new_preset)

        self.btn_delete_preset = QPushButton("Borrar")
        self.btn_delete_preset.setStyleSheet("padding: 3px 8px; font-size: 11px;")
        self.btn_delete_preset.clicked.connect(self._delete_current_preset)
        preset_layout.addWidget(self.btn_delete_preset)

        layout.addLayout(preset_layout)

        # 2. Campo de entrada de patrón
        self.pattern_input = QLineEdit()
        current_pattern = self.config_manager.get_pattern()
        self.pattern_input.setText(current_pattern)
        self.pattern_input.setPlaceholderText("Ej: {artist}{feat} - {title}{remix}")
        self.pattern_input.textChanged.connect(self._on_pattern_text_changed)
        layout.addWidget(self.pattern_input)

        # 3. Chips / Botones con tokens dinámicos
        self.chips_label = QLabel("Tokens dinámicos (clic para insertar):")
        self.chips_label.setStyleSheet("color: #8b8e98; font-size: 11px;")
        layout.addWidget(self.chips_label)

        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(5)
        chips_layout.setContentsMargins(0, 0, 0, 0)

        for token, tooltip in self.TOKENS:
            btn = QPushButton(token)
            btn.setToolTip(f"Insertar {tooltip}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a2c33;
                    color: #d1d5db;
                    border: 1px solid #373a44;
                    border-radius: 11px;
                    padding: 3px 8px;
                    font-size: 11px;
                    font-family: monospace;
                }
                QPushButton:hover {
                    background-color: #373a44;
                    border-color: #ff9800;
                    color: #ffffff;
                }
                QPushButton:pressed {
                    background-color: #ff9800;
                    color: #000000;
                }
            """)
            btn.clicked.connect(lambda checked=False, t=token: self._insert_token(t))
            chips_layout.addWidget(btn)

        chips_layout.addStretch()
        layout.addLayout(chips_layout)

        # 4. Tarjeta de Previsualización dinámica en vivo
        preview_box = QFrame()
        preview_box.setStyleSheet("""
            QFrame {
                background-color: #1a1b1f;
                border: 1px solid #2e3036;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        pb_layout = QVBoxLayout(preview_box)
        pb_layout.setContentsMargins(8, 6, 8, 6)
        pb_layout.setSpacing(4)

        self.prev_header = QLabel("Previsualización en tiempo real:")
        self.prev_header.setStyleSheet("color: #ff9800; font-size: 11px; font-weight: bold;")
        pb_layout.addWidget(self.prev_header)

        self.preview_label = QLabel()
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("color: #f0f0f0; font-family: monospace; font-size: 12px;")
        pb_layout.addWidget(self.preview_label)

        layout.addWidget(preview_box)

        # Actualizar previsualización inicial
        self._update_preview(self.pattern_input.text())

    def retranslate_ui(self):
        """Actualiza los textos del constructor de patrones según el idioma activo."""
        self.lbl_preset.setText(t("inspector.presets_label"))
        self.btn_save_preset.setText(t("buttons.save"))
        self.btn_save_preset.setToolTip(t("buttons.save"))
        self.btn_new_preset.setText(t("buttons.new"))
        self.btn_new_preset.setToolTip(t("buttons.new"))
        self.btn_delete_preset.setText(t("buttons.delete"))
        self.btn_delete_preset.setToolTip(t("buttons.delete"))
        self.chips_label.setText(t("inspector.tokens_label"))
        self.prev_header.setText(t("inspector.preview_label"))

    def _insert_token(self, token: str):
        """Inserta el token en la posición actual del cursor."""
        current_text = self.pattern_input.text()
        cursor_pos = self.pattern_input.cursorPosition()
        new_text = current_text[:cursor_pos] + token + current_text[cursor_pos:]
        self.pattern_input.setText(new_text)
        self.pattern_input.setCursorPosition(cursor_pos + len(token))
        self.pattern_input.setFocus()

    def _reload_presets_combo(self, select_preset: str = None):
        """Recarga el combobox con los presets guardados en la configuración."""
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        presets = self.config_manager.get_presets()
        active = select_preset or self.config_manager.get("naming", "active_preset", "Estándar EDM / Pop")
        for p_name in presets.keys():
            self.preset_combo.addItem(p_name)
        if active in presets:
            self.preset_combo.setCurrentText(active)
        elif self.preset_combo.count() > 0:
            self.preset_combo.setCurrentIndex(0)
        self.preset_combo.blockSignals(False)

    def _save_current_preset(self):
        """Guarda o actualiza el patrón actual en el preset seleccionado."""
        current_preset = self.preset_combo.currentText().strip()
        pattern = self.pattern_input.text().strip()
        if not current_preset or not pattern:
            return
        self.config_manager.set_pattern(pattern, current_preset)
        self.pattern_changed.emit(pattern)
        QMessageBox.information(
            self,
            "Preset Guardado",
            f"El preset '{current_preset}' ha sido actualizado con el patrón:\n\n{pattern}"
        )

    def _create_new_preset(self):
        """Pide un nombre al usuario y guarda un nuevo preset con el patrón actual."""
        pattern = self.pattern_input.text().strip()
        if not pattern:
            QMessageBox.warning(self, "Aviso", "El patrón no puede estar vacío.")
            return

        name, ok = QInputDialog.getText(
            self,
            "Nuevo Preset Personalizado",
            "Introduce el nombre para el nuevo preset:",
            text="Mi Preset Personalizado"
        )
        if ok and name.strip():
            preset_name = name.strip()
            self.config_manager.add_preset(preset_name, pattern)
            self._reload_presets_combo(select_preset=preset_name)
            self.pattern_changed.emit(pattern)
            QMessageBox.information(
                self,
                "Preset Creado",
                f"El preset '{preset_name}' se ha creado y guardado correctamente."
            )

    def _delete_current_preset(self):
        """Elimina el preset actualmente seleccionado."""
        current_preset = self.preset_combo.currentText().strip()
        if not current_preset:
            return

        presets = self.config_manager.get_presets()
        if len(presets) <= 1:
            QMessageBox.warning(self, "Aviso", "No se puede eliminar el único preset existente.")
            return

        confirm = QMessageBox.question(
            self,
            "Eliminar Preset",
            f"¿Estás seguro de que deseas eliminar el preset '{current_preset}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.config_manager.delete_preset(current_preset)
            self._reload_presets_combo()
            new_preset = self.preset_combo.currentText()
            new_pattern = self.config_manager.get_pattern()
            self.pattern_input.setText(new_pattern)
            self.pattern_changed.emit(new_pattern)

    def _on_preset_selected(self, preset_name: str):
        """Manejador cuando el usuario cambia el preset en el combobox."""
        presets = self.config_manager.get_presets()
        if preset_name in presets:
            pattern = presets[preset_name]
            self.pattern_input.setText(pattern)
            self.config_manager.set_pattern(pattern, preset_name)
            self.pattern_changed.emit(pattern)

    def _on_pattern_text_changed(self, text: str):
        self._update_preview(text)
        self.config_manager.set_pattern(text)
        self.pattern_changed.emit(text)

    def _update_preview(self, pattern: str):
        rendered = ConfigManager.render_pattern(pattern, SAMPLE_TRACK)
        self.preview_label.setText(rendered)

    def get_pattern(self) -> str:
        return self.pattern_input.text().strip()
