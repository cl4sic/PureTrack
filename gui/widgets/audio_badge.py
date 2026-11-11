#!/usr/bin/env python3
"""
gui/widgets/audio_badge.py - Componente visual de Badge de Calidad / Estado (AIMP Style).

Estados soportados:
- APTA: Verde (#4caf50 / #81c784)
- REVISIÓN MANUAL: Amarillo (#ffc107 / #ffd54f)
- CANDIDATA A ELIMINACIÓN: Rojo (#f44336 / #e57373)
- PENDIENTE: Gris azulado (#607d8b)
- MODIFICADO / APLICADO: Cian (#00b4d8)
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class AudioBadge(QWidget):
    """Badge píldora estilizado con icono y texto de estado para la tabla de pistas."""

    COLORS = {
        "APTA": {"bg": "rgba(76, 175, 80, 0.18)", "border": "#4caf50", "text": "#81c784", "icon": "●"},
        "REVISIÓN MANUAL": {"bg": "rgba(255, 193, 7, 0.18)", "border": "#ffc107", "text": "#ffd54f", "icon": "▲"},
        "CANDIDATA A ELIMINACIÓN": {"bg": "rgba(244, 67, 54, 0.18)", "border": "#f44336", "text": "#e57373", "icon": "✖"},
        "PENDIENTE": {"bg": "rgba(96, 125, 139, 0.18)", "border": "#607d8b", "text": "#b0bec5", "icon": "○"},
        "APLICADO": {"bg": "rgba(0, 180, 216, 0.18)", "border": "#00b4d8", "text": "#90e0ef", "icon": "✔"},
    }

    def __init__(self, status: str = "PENDIENTE", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.set_status(status)

    def set_status(self, status: str):
        st = status.upper().strip()
        cfg = self.COLORS.get(st, self.COLORS["PENDIENTE"])
        display_text = "APTA" if st == "APTA" else ("REVISAR" if "REVISIÓN" in st else ("ELIMINAR" if "ELIMINACIÓN" in st else st))
        self.label.setText(f"{cfg['icon']} {display_text}")
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {cfg['bg']};
                border: 1px solid {cfg['border']};
                border-radius: 9px;
            }}
            QLabel {{
                background: transparent;
                border: none;
                color: {cfg['text']};
                font-size: 10px;
                font-weight: bold;
                padding: 1px 3px;
            }}
        """)
