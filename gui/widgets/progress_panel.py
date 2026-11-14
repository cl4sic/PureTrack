#!/usr/bin/env python3
"""
gui/widgets/progress_panel.py - Panel Inferior de Control, Progreso Dual y Consola (AIMP Style).

Incluye:
1. Barra de progreso dual: Canción individual en curso y progreso global del lote.
2. Indicador dinámico de velocidad (pistas/seg) y tiempo restante estimado (ETA).
3. Botones de acción principales: Auditar, Aplicar, Deshacer y controles de flujo (Pausar/Reanudar/Cancelar).
4. Consola de registro colapsable con coloreado sintáctico según severidad.
5. Soporte completo multi-idioma (i18n) con actualización reactiva en caliente.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor, QColor
from core.i18n import t, get_i18n


class ProgressPanel(QWidget):
    """Panel de ejecución, telemetría y consola para operaciones por lotes."""

    audit_requested = Signal()
    apply_requested = Signal()
    rollback_requested = Signal()
    pause_requested = Signal()
    resume_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_paused = False
        self._is_active = False
        self._current_step_desc: str = ""
        self._global_current: int = 0
        self._global_total: int = 0
        self._global_label: str = ""
        self._last_eta_str: str = "ETA: --:-- | 0.0 fps"

        self._init_ui()
        self.retranslate_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 10)
        layout.setSpacing(8)

        # -------------------------------------------------------------
        # 1. BARRAS DE PROGRESO DUALES
        # -------------------------------------------------------------
        bars_frame = QFrame()
        bars_frame.setStyleSheet("""
            QFrame {
                background-color: #222327;
                border: 1px solid #2e3036;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        bf_layout = QVBoxLayout(bars_frame)
        bf_layout.setContentsMargins(8, 6, 8, 6)
        bf_layout.setSpacing(6)

        # Barra Canción Actual
        track_row = QHBoxLayout()
        self.lbl_current_track = QLabel()
        self.lbl_current_track.setStyleSheet("color: #d1d5db; font-size: 11px;")
        self.lbl_track_pct = QLabel("0%")
        self.lbl_track_pct.setStyleSheet("color: #ff9800; font-family: monospace; font-size: 11px;")
        track_row.addWidget(self.lbl_current_track, stretch=1)
        track_row.addWidget(self.lbl_track_pct)
        bf_layout.addLayout(track_row)

        self.bar_current_track = QProgressBar()
        self.bar_current_track.setFixedHeight(8)
        self.bar_current_track.setTextVisible(False)
        self.bar_current_track.setRange(0, 100)
        self.bar_current_track.setValue(0)
        self.bar_current_track.setStyleSheet("""
            QProgressBar {
                background-color: #18191c;
                border: 1px solid #2e3036;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #ff9800;
                border-radius: 3px;
            }
        """)
        bf_layout.addWidget(self.bar_current_track)

        # Barra Global del Lote
        global_row = QHBoxLayout()
        self.lbl_global_status = QLabel()
        self.lbl_global_status.setStyleSheet("color: #d1d5db; font-size: 11px; font-weight: bold;")
        self.lbl_eta = QLabel("ETA: --:-- | 0.0 fps")
        self.lbl_eta.setStyleSheet("color: #8b8e98; font-family: monospace; font-size: 11px;")
        self.lbl_global_pct = QLabel("0%")
        self.lbl_global_pct.setStyleSheet("color: #00b4d8; font-family: monospace; font-size: 11px; font-weight: bold;")
        global_row.addWidget(self.lbl_global_status, stretch=1)
        global_row.addWidget(self.lbl_eta)
        global_row.addSpacing(10)
        global_row.addWidget(self.lbl_global_pct)
        bf_layout.addLayout(global_row)

        self.bar_global = QProgressBar()
        self.bar_global.setFixedHeight(12)
        self.bar_global.setTextVisible(False)
        self.bar_global.setRange(0, 100)
        self.bar_global.setValue(0)
        self.bar_global.setStyleSheet("""
            QProgressBar {
                background-color: #18191c;
                border: 1px solid #2e3036;
                border-radius: 6px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff9800, stop:1 #00b4d8);
                border-radius: 5px;
            }
        """)
        bf_layout.addWidget(self.bar_global)

        layout.addWidget(bars_frame)

        # -------------------------------------------------------------
        # 2. BOTONES DE ACCIÓN Y CONTROL
        # -------------------------------------------------------------
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        self.btn_audit = QPushButton()
        self.btn_audit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_audit.clicked.connect(self.audit_requested.emit)
        actions_layout.addWidget(self.btn_audit)

        self.btn_apply = QPushButton()
        self.btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_apply.setObjectName("btnApply")
        self.btn_apply.clicked.connect(self.apply_requested.emit)
        actions_layout.addWidget(self.btn_apply)

        self.btn_rollback = QPushButton()
        self.btn_rollback.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_rollback.clicked.connect(self.rollback_requested.emit)
        actions_layout.addWidget(self.btn_rollback)

        actions_layout.addSpacing(15)

        # Controles de Flujo de Trabajo
        self.btn_pause = QPushButton()
        self.btn_pause.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self._toggle_pause)
        actions_layout.addWidget(self.btn_pause)

        self.btn_cancel = QPushButton()
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_requested.emit)
        actions_layout.addWidget(self.btn_cancel)

        actions_layout.addStretch()

        # Botón colapsar/expandir consola
        self.btn_toggle_log = QPushButton()
        self.btn_toggle_log.setCheckable(True)
        self.btn_toggle_log.setChecked(True)
        self.btn_toggle_log.setStyleSheet("font-size: 11px; padding: 4px 8px;")
        self.btn_toggle_log.toggled.connect(self._toggle_log_console)
        actions_layout.addWidget(self.btn_toggle_log)

        layout.addLayout(actions_layout)

        # -------------------------------------------------------------
        # 3. CONSOLA DE REGISTRO COMPACTA COLAPSABLE
        # -------------------------------------------------------------
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setFixedHeight(95)
        self.log_console.setStyleSheet("""
            QTextEdit {
                background-color: #121315;
                color: #d1d5db;
                font-family: monospace;
                font-size: 11px;
                border: 1px solid #2e3036;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        layout.addWidget(self.log_console)

    def _toggle_pause(self):
        if not self._is_paused:
            self._is_paused = True
            self.btn_pause.setText(t("buttons.resume"))
            self.pause_requested.emit()
        else:
            self._is_paused = False
            self.btn_pause.setText(t("buttons.pause"))
            self.resume_requested.emit()

    def _toggle_log_console(self, checked: bool):
        self.log_console.setVisible(checked)
        c_name = t("progress.console_title", "Consola").split()[0]
        self.btn_toggle_log.setText(f"{c_name} ▼" if checked else f"{c_name} ▲")

    def set_operation_active(self, active: bool):
        """Habilita o deshabilita botones según si hay una tarea en curso."""
        self._is_active = active
        self.btn_audit.setEnabled(not active)
        self.btn_apply.setEnabled(not active)
        self.btn_rollback.setEnabled(not active)

        self.btn_pause.setEnabled(active)
        self.btn_cancel.setEnabled(active)
        if not active:
            self._is_paused = False
            self.btn_pause.setText(t("buttons.pause"))

    def update_item_progress(self, current_step: int, total_steps: int, step_desc: str):
        pct = int((current_step / total_steps) * 100) if total_steps > 0 else 0
        self.bar_current_track.setValue(pct)
        self.lbl_track_pct.setText(f"{pct}%")
        self._current_step_desc = step_desc
        self.lbl_current_track.setText(f"{t('progress.current_step')} {step_desc}")

    def update_global_progress(self, current: int, total: int, label: str):
        pct = int((current / total) * 100) if total > 0 else 0
        self.bar_global.setValue(pct)
        self.lbl_global_pct.setText(f"{pct}%")
        self._global_current = current
        self._global_total = total
        self._global_label = label
        proc_text = t("progress.processing", count=current, total=total)
        self.lbl_global_status.setText(f"{proc_text}: {label}")

    def update_eta(self, remaining_sec: float, speed_fps: float):
        m, s = divmod(int(remaining_sec), 60)
        self._last_eta_str = f"ETA: {m:02d}:{s:02d} | {speed_fps:.2f} fps"
        self.lbl_eta.setText(self._last_eta_str)

    def append_log(self, level: str, message: str):
        """Añade un mensaje con formateo de color según severidad."""
        color_map = {
            "INFO": "#90caf9",
            "SUCCESS": "#81c784",
            "WARNING": "#ffd54f",
            "ERROR": "#e57373",
        }
        color = color_map.get(level.upper(), "#d1d5db")
        html = f"<span style='color:{color};'>[{level.upper()}]</span> {message}"
        self.log_console.append(html)
        self.log_console.moveCursor(QTextCursor.MoveOperation.End)

    def reset_progress(self):
        self._current_step_desc = ""
        self._global_current = 0
        self._global_total = 0
        self._global_label = ""
        self._is_active = False
        self.bar_current_track.setValue(0)
        self.bar_global.setValue(0)
        self.lbl_track_pct.setText("0%")
        self.lbl_global_pct.setText("0%")
        self.lbl_current_track.setText(f"{t('progress.current_item')} {t('table.empty_pending')}")
        self.lbl_global_status.setText(f"{t('progress.overall')} {t('progress.ready')}")
        self.lbl_eta.setText("ETA: --:-- | 0.0 fps")

    def retranslate_ui(self):
        """Actualiza los textos del panel de progreso y botones según el idioma activo."""
        self.btn_audit.setText(t("buttons.audit"))
        self.btn_apply.setText(t("buttons.apply"))
        self.btn_rollback.setText(t("buttons.rollback"))
        self.btn_pause.setText(t("buttons.resume") if self._is_paused else t("buttons.pause"))
        self.btn_cancel.setText(t("buttons.cancel"))
        is_visible = self.log_console.isVisible()
        c_name = t("progress.console_title", "Consola").split()[0]
        self.btn_toggle_log.setText(f"{c_name} ▼" if is_visible else f"{c_name} ▲")

        if self._is_active and self._global_total > 0:
            proc_text = t("progress.processing", count=self._global_current, total=self._global_total)
            self.lbl_global_status.setText(f"{proc_text}: {self._global_label}")
            if self._current_step_desc:
                self.lbl_current_track.setText(f"{t('progress.current_step')} {self._current_step_desc}")
            else:
                self.lbl_current_track.setText(f"{t('progress.current_item')} {t('table.empty_pending')}")
        else:
            self.lbl_current_track.setText(f"{t('progress.current_item')} {t('table.empty_pending')}")
            self.lbl_global_status.setText(f"{t('progress.overall')} {t('progress.ready')}")
