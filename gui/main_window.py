#!/usr/bin/env python3
"""
gui/main_window.py - Ventana Principal de la Suite AudioMaster (AIMP Dark Style).

Integra:
1. Selector de ruta origen/destino con soporte universal Drag & Drop (carpetas o archivos .mp3).
2. QSplitter redimensionable:
   - Izquierda: Tabla reactiva de pistas con Badges de estado, menú contextual y edición.
   - Derecha: Panel inspector colapsable con PatternBuilder y toggles de auditoría.
3. Panel inferior de telemetría, progreso dual, consola de logs y botones de acción.
4. Conexión no bloqueante con QThread workers (AuditWorker, EnrichWorker, ApplyWorker, RollbackWorker).
"""

from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QMenu,
    QDialog,
    QTextBrowser,
    QInputDialog,
    QApplication
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QAction, QIcon, QColor

from core.config_manager import ConfigManager
from core.common_utils import sanitize_windows_filename
from core.auditor import AudioAuditResult
from core.resolver import ResolvedMetadata
from gui.widgets.audio_badge import AudioBadge
from gui.widgets.inspector_panel import InspectorPanel
from gui.widgets.progress_panel import ProgressPanel
from gui.workers import AuditWorker, EnrichWorker, ApplyWorker, RollbackWorker
from gui.styles.theme_loader import load_stylesheet


class TrackDetailsDialog(QDialog):
    """Diálogo modal para inspección técnica exhaustiva de una pista."""

    def __init__(self, data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Inspección Técnica - {data.get('filename', 'Pista')}")
        self.resize(580, 480)
        layout = QVBoxLayout(self)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)

        res: Optional[AudioAuditResult] = data.get("audit_result")
        meta: Optional[ResolvedMetadata] = data.get("resolved_metadata")

        html = [
            f"<h2 style='color:#ff9800;'>{data.get('filename')}</h2>",
            f"<p><b>Ruta:</b> <span style='font-family:monospace;'>{data.get('filepath')}</span></p>",
            "<hr style='border:1px solid #2e3036;'>",
            "<h3>Diagnóstico Acústico (Auditoría)</h3>",
            "<ul>"
        ]

        if res:
            html.extend([
                f"<li><b>Veredicto:</b> {res.verdict} ({res.verdict_reason})</li>",
                f"<li><b>Bitrate:</b> {res.mutagen_bitrate_kbps} kbps ({res.bitrate_mode})</li>",
                f"<li><b>Duración:</b> {res.duration_sec} s | Frecuencia: {res.sample_rate_hz} Hz | Canales: {res.channels}</li>",
                f"<li><b>Integridad FFmpeg:</b> {'✔ Correcto' if res.ffmpeg_integrity_ok else '✖ Error: ' + res.ffmpeg_errors}</li>",
                f"<li><b>Nivel de Pico:</b> {res.peak_dbfs} dBFS | <b>RMS Total:</b> {res.rms_dbfs} dBFS</li>",
                f"<li><b>Rango Dinámico:</b> {res.dynamic_range_db} dB</li>",
                f"<li><b>Clipping / Saturación:</b> {res.clipping_pct}% ({res.clipping_samples_count} muestras saturadas)</li>",
                f"<li><b>RMS cola final (400ms):</b> {res.last_400ms_rms_dbfs} dBFS {'[Corte abrupto]' if res.has_abrupt_ending else '[Desvanecimiento normal]'}</li>",
                f"<li><b>Silencios anómalos:</b> {res.anomalous_silence_count} ({res.silence_details})</li>"
            ])
        else:
            html.append("<li><i>Pendiente de análisis.</i></li>")
        html.append("</ul>")

        html.extend([
            "<hr style='border:1px solid #2e3036;'>",
            "<h3>Metadatos y Proyección de Renombrado</h3>",
            "<ul>"
        ])

        if meta:
            html.extend([
                f"<li><b>Nombre Proyectado:</b> <span style='color:#00b4d8; font-family:monospace;'>{meta.new_filename}</span></li>",
                f"<li><b>Fuente:</b> {meta.source} (Confianza: {int(meta.confidence * 100)}%)</li>",
                f"<li><b>Artistas principales:</b> {', '.join(meta.main_artists)}</li>",
                f"<li><b>Artistas invitados/Feat:</b> {', '.join(meta.feat_artists) if meta.feat_artists else 'Ninguno'}</li>",
                f"<li><b>Título:</b> {meta.title} {f'({meta.remix_name})' if meta.remix_name else ''}</li>",
                f"<li><b>Álbum:</b> {meta.album} ({meta.year})</li>",
                f"<li><b>Género:</b> {meta.genre}</li>",
                f"<li><b>ID3 TIT2:</b> {meta.id3_tit2}</li>",
                f"<li><b>ID3 TPE1:</b> {meta.id3_tpe1}</li>",
                f"<li><b>ID3 TALB:</b> {meta.id3_talb}</li>",
                f"<li><b>ID3 TCON:</b> {meta.id3_tcon}</li>",
            ])
        else:
            html.append("<li><i>No se han resuelto los metadatos aún.</i></li>")
        html.append("</ul>")

        browser.setHtml("".join(html))
        layout.addWidget(browser)

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


class MainWindow(QMainWindow):
    """Ventana Principal AudioMaster Suite."""

    COL_STATUS = 0
    COL_ORIGINAL = 1
    COL_PROJECTED = 2
    COL_BITRATE = 3
    COL_DURATION = 4
    COL_CLIPPING = 5
    COL_ACTION = 6

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.current_worker = None

        # Estructura de pistas en memoria: dict {filepath: data_dict}
        self.tracks_data: Dict[str, Dict[str, Any]] = {}
        self.selected_directory: Optional[Path] = None

        self.setWindowTitle("AudioMaster - Suite Profesional de Sanación y Etiquetado")
        self.resize(1260, 780)
        self.setAcceptDrops(True)

        self._init_ui()
        self._load_initial_directory()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 8)
        main_layout.setSpacing(8)

        # -------------------------------------------------------------
        # 1. ZONA SUPERIOR: RUTA Y DRAG & DROP
        # -------------------------------------------------------------
        top_frame = QWidget()
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)

        lbl_dir = QLabel("Directorio Origen:")
        lbl_dir.setStyleSheet("font-weight: bold; color: #ff9800;")
        top_layout.addWidget(lbl_dir)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Arrastre una carpeta o archivos MP3 aquí, o examine...")
        self.path_input.returnPressed.connect(self._on_path_entered)
        top_layout.addWidget(self.path_input, stretch=1)

        btn_browse = QPushButton("Examinar...")
        btn_browse.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogOpenButton))
        btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_browse.clicked.connect(self._browse_directory)
        top_layout.addWidget(btn_browse)

        btn_refresh = QPushButton("Recargar")
        btn_refresh.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_BrowserReload))
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.clicked.connect(self._reload_current_directory)
        top_layout.addWidget(btn_refresh)

        # Selector de Tema (Ámbar / Cian)
        self.btn_theme = QPushButton("Tema: Ámbar")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.clicked.connect(self._toggle_theme)
        top_layout.addWidget(self.btn_theme)

        main_layout.addWidget(top_frame)

        # -------------------------------------------------------------
        # 2. ZONA CENTRAL: SPLITTER REDIMENSIONABLE (TABLA + INSPECTOR)
        # -------------------------------------------------------------
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        # Panel Izquierdo: Tabla de pistas
        table_container = QWidget()
        tc_layout = QVBoxLayout(table_container)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        tc_layout.setSpacing(4)

        table_header_layout = QHBoxLayout()
        self.lbl_table_count = QLabel("Pistas detectadas: 0")
        self.lbl_table_count.setStyleSheet("color: #8b8e98; font-weight: bold;")
        table_header_layout.addWidget(self.lbl_table_count)
        table_header_layout.addStretch()

        self.btn_toggle_inspector = QPushButton("Ocultar Ajustes ▶")
        self.btn_toggle_inspector.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        self.btn_toggle_inspector.clicked.connect(self._toggle_inspector_panel)
        table_header_layout.addWidget(self.btn_toggle_inspector)
        tc_layout.addLayout(table_header_layout)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Estado", "Archivo Original", "Nombre Proyectado", "Bitrate", "Duración", "Clipping %", "Acción"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        header.setSectionsMovable(True)
        header.sectionDoubleClicked.connect(self.table.resizeColumnToContents)

        # Anchos iniciales generosos y ajustables interactivamente por el usuario
        self.table.setColumnWidth(self.COL_STATUS, 120)
        self.table.setColumnWidth(self.COL_ORIGINAL, 340)
        self.table.setColumnWidth(self.COL_PROJECTED, 340)
        self.table.setColumnWidth(self.COL_BITRATE, 85)
        self.table.setColumnWidth(self.COL_DURATION, 85)
        self.table.setColumnWidth(self.COL_CLIPPING, 95)
        self.table.setColumnWidth(self.COL_ACTION, 120)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.doubleClicked.connect(self._on_table_row_double_click)

        tc_layout.addWidget(self.table)
        self.splitter.addWidget(table_container)

        # Panel Derecho: Inspector de Ajustes
        self.inspector = InspectorPanel(self.config_manager)
        self.inspector.setMinimumWidth(320)
        self.inspector.settings_changed.connect(self._on_settings_changed)
        self.splitter.addWidget(self.inspector)

        # Proporción inicial: 65% tabla, 35% inspector
        self.splitter.setSizes([780, 420])
        main_layout.addWidget(self.splitter, stretch=1)

        # -------------------------------------------------------------
        # 3. ZONA INFERIOR: PROGRESS PANEL (TELEMETRÍA + CONSOLA + ACCIONES)
        # -------------------------------------------------------------
        self.progress_panel = ProgressPanel()
        self.progress_panel.audit_requested.connect(self.start_audit)
        self.progress_panel.dry_run_requested.connect(self.start_dry_run)
        self.progress_panel.apply_requested.connect(self.start_apply)
        self.progress_panel.rollback_requested.connect(self.start_rollback)
        self.progress_panel.pause_requested.connect(self._pause_worker)
        self.progress_panel.resume_requested.connect(self._resume_worker)
        self.progress_panel.cancel_requested.connect(self._cancel_worker)
        main_layout.addWidget(self.progress_panel)

    # -----------------------------------------------------------------
    # GESTIÓN DE DRAG & DROP
    # -----------------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if not urls:
            return

        file_paths = []
        for url in urls:
            p = Path(url.toLocalFile())
            if p.is_dir():
                file_paths.extend(sorted(p.glob("*.mp3")))
                self.selected_directory = p
            elif p.suffix.lower() == ".mp3":
                file_paths.append(p)
                if not self.selected_directory:
                    self.selected_directory = p.parent

        if file_paths:
            if self.selected_directory:
                self.path_input.setText(str(self.selected_directory))
                self.config_manager.set("ui_preferences", "last_source_dir", str(self.selected_directory))
            self._load_files_into_table(file_paths)

    def _browse_directory(self):
        initial = self.selected_directory or Path.cwd()
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta con Archivos MP3", str(initial))
        if folder:
            p = Path(folder)
            self.selected_directory = p
            self.path_input.setText(str(p))
            self.config_manager.set("ui_preferences", "last_source_dir", str(p))
            self._load_directory(p)

    def _on_path_entered(self):
        text = self.path_input.text().strip()
        if text:
            p = Path(text)
            if p.is_dir():
                self.selected_directory = p
                self._load_directory(p)

    def _reload_current_directory(self):
        if self.selected_directory and self.selected_directory.is_dir():
            self._load_directory(self.selected_directory)

    def _load_initial_directory(self):
        last_dir = self.config_manager.get("ui_preferences", "last_source_dir", "")
        if last_dir and Path(last_dir).is_dir():
            target = Path(last_dir)
        else:
            target = Path.cwd()

        # Comprobar si hay archivos mp3 en target
        mp3s = list(target.glob("*.mp3"))
        if mp3s:
            self.selected_directory = target
            self.path_input.setText(str(target))
            self._load_files_into_table(mp3s)

    def _load_directory(self, folder: Path):
        files = sorted(folder.glob("*.mp3"))
        self._load_files_into_table(files)

    def _load_files_into_table(self, files: List[Path]):
        self.table.setRowCount(0)
        self.tracks_data.clear()

        for idx, f in enumerate(files):
            f_str = str(f.resolve())
            self.tracks_data[f_str] = {
                "filepath": f_str,
                "filename": f.name,
                "audit_result": None,
                "resolved_metadata": None,
                "status": "PENDIENTE",
                "excluded": False
            }

            self.table.insertRow(idx)

            # Badge Estado
            badge = AudioBadge("PENDIENTE")
            self.table.setCellWidget(idx, self.COL_STATUS, badge)

            # Archivo Original
            item_orig = QTableWidgetItem(f.name)
            item_orig.setData(Qt.ItemDataRole.UserRole, f_str)
            item_orig.setToolTip(f"{f.name}\nRuta: {f_str}")
            self.table.setItem(idx, self.COL_ORIGINAL, item_orig)

            # Nombre Proyectado
            item_proj = QTableWidgetItem("—")
            item_proj.setToolTip("Doble clic para editar o asignar un nombre personalizado")
            self.table.setItem(idx, self.COL_PROJECTED, item_proj)

            # Bitrate
            self.table.setItem(idx, self.COL_BITRATE, QTableWidgetItem("—"))

            # Duración
            self.table.setItem(idx, self.COL_DURATION, QTableWidgetItem("—"))

            # Clipping %
            self.table.setItem(idx, self.COL_CLIPPING, QTableWidgetItem("—"))

            # Acción
            self.table.setItem(idx, self.COL_ACTION, QTableWidgetItem("En espera"))

        self.lbl_table_count.setText(f"Pistas detectadas: {len(files)}")
        self.progress_panel.append_log("INFO", f"Cargados {len(files)} archivos MP3 desde {self.selected_directory or 'lista'}")

    # -----------------------------------------------------------------
    # CONTROL DE WORKERS Y CONCURRENCIA
    # -----------------------------------------------------------------
    def start_audit(self):
        """Inicia el análisis de calidad acústica e integridad sin bloquear la UI."""
        files = [Path(fp) for fp, d in self.tracks_data.items() if not d.get("excluded", False)]
        if not files:
            QMessageBox.information(self, "Sin pistas", "No hay archivos MP3 disponibles para auditar.")
            return

        self.progress_panel.set_operation_active(True)
        self.progress_panel.reset_progress()

        audit_settings = self.inspector.get_audit_settings()
        pattern = self.inspector.get_pattern()
        self.current_worker = AuditWorker(files, audit_settings=audit_settings, naming_pattern=pattern)
        self.current_worker.sig_track_audited.connect(self._on_track_audited)
        self.current_worker.sig_progress.connect(self.progress_panel.update_global_progress)
        self.current_worker.sig_item_progress.connect(self.progress_panel.update_item_progress)
        self.current_worker.sig_eta.connect(self.progress_panel.update_eta)
        self.current_worker.sig_log.connect(self.progress_panel.append_log)
        self.current_worker.sig_finished.connect(self._on_worker_finished)
        self.current_worker.start()

    def start_dry_run(self):
        """Simula la resolución de metadatos y el renombrado."""
        files = [Path(fp) for fp, d in self.tracks_data.items() if not d.get("excluded", False)]
        if not files:
            QMessageBox.information(self, "Sin pistas", "No hay archivos para simular.")
            return

        self.progress_panel.set_operation_active(True)
        self.progress_panel.reset_progress()

        pattern = self.inspector.get_pattern()
        self.current_worker = EnrichWorker(files, naming_pattern=pattern)
        self.current_worker.sig_track_resolved.connect(self._on_track_resolved)
        self.current_worker.sig_progress.connect(self.progress_panel.update_global_progress)
        self.current_worker.sig_item_progress.connect(self.progress_panel.update_item_progress)
        self.current_worker.sig_eta.connect(self.progress_panel.update_eta)
        self.current_worker.sig_log.connect(self.progress_panel.append_log)
        self.current_worker.sig_finished.connect(self._on_enrich_finished_for_dry_run)
        self.current_worker.start()

    def start_apply(self):
        """Aplica las modificaciones físicas de renombrado y tags ID3 en disco."""
        operations: List[Tuple[ResolvedMetadata, Path, Path]] = []
        for fp, d in self.tracks_data.items():
            if d.get("excluded", False):
                continue
            meta: Optional[ResolvedMetadata] = d.get("resolved_metadata")
            src_path = Path(fp)
            if not meta:
                # Si no fue resuelto previamente, resolver en el momento
                from core.resolver import MetadataResolver
                r = MetadataResolver(search_dir=self.selected_directory)
                meta = r.resolve_track_metadata(src_path, custom_pattern=self.inspector.get_pattern())
                d["resolved_metadata"] = meta

            # Garantizar que cualquier nombre personalizado elegido por el usuario se respete 100%
            if d.get("has_custom_name") and d.get("custom_filename"):
                meta.new_filename = d["custom_filename"]

            dest_path = src_path.parent / meta.new_filename
            operations.append((meta, src_path, dest_path))

        if not operations:
            QMessageBox.warning(self, "Aviso", "No hay operaciones válidas para aplicar.")
            return

        # Confirmación de seguridad
        confirm = QMessageBox.question(
            self,
            "Confirmar Escritura en Disco",
            f"Se aplicarán modificaciones y renombrado en {len(operations)} archivo(s).\n\n"
            "Se creará automáticamente un log transaccional previo para permitir Rollback.\n\n"
            "¿Desea continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.progress_panel.set_operation_active(True)
        self.progress_panel.reset_progress()

        self.current_worker = ApplyWorker(operations, dry_run=False, search_dir=self.selected_directory)
        self.current_worker.sig_track_applied.connect(self._on_track_applied)
        self.current_worker.sig_progress.connect(self.progress_panel.update_global_progress)
        self.current_worker.sig_item_progress.connect(self.progress_panel.update_item_progress)
        self.current_worker.sig_log.connect(self.progress_panel.append_log)
        self.current_worker.sig_finished.connect(self._on_apply_finished)
        self.current_worker.start()

    def start_rollback(self):
        """Ejecuta la restauración / reversión a partir del archivo de registro."""
        confirm = QMessageBox.warning(
            self,
            "Confirmar Rollback",
            "¿Desea restaurar los nombres de archivo y etiquetas originales a partir del último registro?\n\n"
            "Esta operación revertirá los cambios aplicados.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.progress_panel.set_operation_active(True)
        self.progress_panel.reset_progress()

        self.current_worker = RollbackWorker(search_dir=self.selected_directory)
        self.current_worker.sig_log.connect(self.progress_panel.append_log)
        self.current_worker.sig_finished.connect(self._on_rollback_finished)
        self.current_worker.start()

    def _pause_worker(self):
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.pause()

    def _resume_worker(self):
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.resume()

    def _cancel_worker(self):
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()

    # -----------------------------------------------------------------
    # ACTUALIZACIÓN REACTIVA DE LA TABLA
    # -----------------------------------------------------------------
    def _get_row_filepath(self, row: int) -> Optional[str]:
        orig_item = self.table.item(row, self.COL_ORIGINAL)
        if orig_item:
            stored = orig_item.data(Qt.ItemDataRole.UserRole)
            if stored:
                return str(stored)
            return orig_item.text()
        return None

    def _get_row_track_data(self, row: int) -> Dict[str, Any]:
        fpath = self._get_row_filepath(row)
        if fpath:
            if fpath in self.tracks_data:
                return self.tracks_data[fpath]
            try:
                resolved = str(Path(fpath).resolve())
                if resolved in self.tracks_data:
                    return self.tracks_data[resolved]
            except Exception:
                pass
            fname = Path(fpath).name
            for k, v in self.tracks_data.items():
                if v.get("filename") == fname:
                    return v
        return {}

    def _find_row_by_filepath(self, filepath: str) -> Optional[int]:
        try:
            target = Path(filepath).resolve()
        except Exception:
            target = None

        for row in range(self.table.rowCount()):
            item = self.table.item(row, self.COL_ORIGINAL)
            if item:
                stored = item.data(Qt.ItemDataRole.UserRole)
                if stored and target:
                    try:
                        if Path(stored).resolve() == target:
                            return row
                    except Exception:
                        pass
                if target and item.text() == target.name:
                    return row
                if not target and item.text() == str(filepath):
                    return row
        return None

    def _on_track_audited(self, res: AudioAuditResult):
        row = self._find_row_by_filepath(res.filepath)
        if row is None:
            return

        fp_key = str(Path(res.filepath).resolve())
        data = self.tracks_data.get(fp_key)
        if data is None:
            data = self._get_row_track_data(row)

        data["audit_result"] = res
        data["status"] = res.verdict

        # Actualizar Badge Estado en tiempo real
        badge = AudioBadge(res.verdict)
        self.table.setCellWidget(row, self.COL_STATUS, badge)

        # Actualizar Nombre Proyectado si se resolvió y no hay override manual fijado por el usuario
        resolved_meta = getattr(res, "resolved_metadata", None)
        if resolved_meta:
            if not data.get("has_custom_name"):
                data["resolved_metadata"] = resolved_meta
                item_proj = QTableWidgetItem(resolved_meta.new_filename)
                item_proj.setToolTip(f"Proyectado: {resolved_meta.new_filename}\nFuente: {resolved_meta.source}")
                self.table.setItem(row, self.COL_PROJECTED, item_proj)
            else:
                custom_name = data.get("custom_filename", resolved_meta.new_filename)
                item_proj = self.table.item(row, self.COL_PROJECTED)
                if not item_proj or item_proj.text() == "—":
                    item_proj = QTableWidgetItem(custom_name)
                    item_proj.setForeground(QColor("#ff9800"))
                    font = item_proj.font()
                    font.setBold(True)
                    item_proj.setFont(font)
                    self.table.setItem(row, self.COL_PROJECTED, item_proj)

        # Bitrate
        self.table.setItem(row, self.COL_BITRATE, QTableWidgetItem(f"{res.mutagen_bitrate_kbps} kbps ({res.bitrate_mode})"))

        # Duración
        mins, secs = divmod(int(res.duration_sec), 60)
        self.table.setItem(row, self.COL_DURATION, QTableWidgetItem(f"{mins}:{secs:02d}"))

        # Clipping %
        item_clip = QTableWidgetItem(f"{res.clipping_pct:.3f}%")
        if res.has_clipping_risk:
            item_clip.setForeground(Qt.GlobalColor.red)
        self.table.setItem(row, self.COL_CLIPPING, item_clip)

        # Acción / Veredicto
        if not data.get("has_custom_name"):
            self.table.setItem(row, self.COL_ACTION, QTableWidgetItem(res.verdict_reason[:35] + ("..." if len(res.verdict_reason) > 35 else "")))
        else:
            item_act = QTableWidgetItem("Personalizado")
            item_act.setForeground(QColor("#00b4d8"))
            self.table.setItem(row, self.COL_ACTION, item_act)

    def _on_track_resolved(self, meta: ResolvedMetadata):
        row = self._find_row_by_filepath(meta.original_path)
        if row is None:
            return

        fp_key = str(Path(meta.original_path).resolve())
        data = self.tracks_data.get(fp_key)
        if data is None:
            data = self._get_row_track_data(row)

        if data.get("has_custom_name") and data.get("custom_filename"):
            meta.new_filename = data["custom_filename"]
            data["resolved_metadata"] = meta
            return

        data["resolved_metadata"] = meta

        item_proj = QTableWidgetItem(meta.new_filename)
        item_proj.setToolTip(f"Proyectado: {meta.new_filename}\nFuente: {meta.source}")
        self.table.setItem(row, self.COL_PROJECTED, item_proj)
        if not data.get("has_custom_name"):
            self.table.setItem(row, self.COL_ACTION, QTableWidgetItem("Proyectado"))

    def _on_track_applied(self, orig_name: str, new_name: str, success: bool, message: str):
        # Localizar fila por nombre original
        for row in range(self.table.rowCount()):
            item = self.table.item(row, self.COL_ORIGINAL)
            if item and item.text() == orig_name:
                badge = AudioBadge("APLICADO" if success else "ERROR")
                self.table.setCellWidget(row, self.COL_STATUS, badge)

                # Actualizar columna Nombre Proyectado con el nombre definitivo aplicado
                item_proj = QTableWidgetItem(new_name)
                item_proj.setToolTip(f"Renombrado en disco: {new_name}")
                item_proj.setForeground(QColor("#90e0ef"))
                font = item_proj.font()
                font.setBold(True)
                item_proj.setFont(font)
                self.table.setItem(row, self.COL_PROJECTED, item_proj)

                # Acción
                act_item = QTableWidgetItem("Actualizado en disco" if success else message)
                act_item.setForeground(QColor("#4caf50" if success else "#f44336"))
                self.table.setItem(row, self.COL_ACTION, act_item)

                data = self._get_row_track_data(row)
                if data:
                    data["status"] = "APLICADO" if success else "ERROR"
                break

    def _on_worker_finished(self, success: bool, summary: str):
        self.progress_panel.set_operation_active(False)
        self.current_worker = None

    def _on_enrich_finished_for_dry_run(self, success: bool, summary: str):
        self.progress_panel.set_operation_active(False)
        self.current_worker = None
        self.progress_panel.append_log("SUCCESS", "[DRY-RUN] Simulación completa. Nombres proyectados visibles en la tabla.")

    def _on_apply_finished(self, success: bool, summary: str):
        self.progress_panel.set_operation_active(False)
        self.current_worker = None
        self.progress_panel.append_log("SUCCESS" if success else "ERROR", summary)
        QMessageBox.information(self, "Proceso Finalizado", summary)
        # No recargar la tabla para conservar las filas visualmente en estado APLICADO y sus nombres finales

    def _on_rollback_finished(self, success: bool, summary: str):
        self.progress_panel.set_operation_active(False)
        self.current_worker = None
        if success:
            QMessageBox.information(self, "Rollback Exitoso", summary)
            self._reload_current_directory()
        else:
            QMessageBox.critical(self, "Error en Rollback", summary)

    # -----------------------------------------------------------------
    # MENÚ CONTEXTUAL E INTERACCIÓN
    # -----------------------------------------------------------------
    def _show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return

        row = item.row()
        orig_item = self.table.item(row, self.COL_ORIGINAL)
        if not orig_item:
            return

        data = self._get_row_track_data(row)
        is_excluded = data.get("excluded", False)

        menu = QMenu(self)
        action_inspect = QAction("🔍 Inspeccionar detalles técnicos", self)
        action_inspect.triggered.connect(lambda: self._inspect_track(data))
        menu.addAction(action_inspect)

        action_edit = QAction("✏️ Asignar nombre personalizado...", self)
        action_edit.triggered.connect(lambda: self._edit_track_manually(row, data))
        menu.addAction(action_edit)

        if data.get("has_custom_name"):
            action_revert = QAction("🔄 Restablecer a patrón automático", self)
            action_revert.triggered.connect(lambda: self._revert_to_pattern(row, data))
            menu.addAction(action_revert)

        menu.addSeparator()

        # Interruptor dinámico bidireccional Excluir / Incluir
        if is_excluded:
            action_exclude = QAction("➕ Incluir en el lote", self)
        else:
            action_exclude = QAction("⊘ Excluir del lote", self)

        action_exclude.triggered.connect(lambda: self._toggle_exclude_track(row, data))
        menu.addAction(action_exclude)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _on_table_row_double_click(self, index):
        row = index.row()
        col = index.column()
        data = self._get_row_track_data(row)

        # Si el usuario hace doble clic sobre la columna de Nombre Proyectado, abre directamente el editor
        if col == self.COL_PROJECTED:
            self._edit_track_manually(row, data)
        else:
            self._inspect_track(data)

    def _inspect_track(self, data: Dict[str, Any]):
        dlg = TrackDetailsDialog(data, self)
        dlg.exec()

    def _edit_track_manually(self, row: int, data: Dict[str, Any]):
        if not data:
            data = self._get_row_track_data(row)

        proj_item = self.table.item(row, self.COL_PROJECTED)
        orig_item = self.table.item(row, self.COL_ORIGINAL)

        # Determinar el nombre actual para pre-rellenar el diálogo:
        # Pre-rellenar con Nombre Proyectado (si != "—") o Archivo Original, siempre sin .mp3
        current = ""
        if proj_item and proj_item.text().strip() and proj_item.text().strip() != "—":
            current = proj_item.text().strip()
        elif orig_item and orig_item.text().strip():
            current = orig_item.text().strip()
        elif data.get("filename"):
            current = data.get("filename")

        if current.lower().endswith(".mp3"):
            current = current[:-4]

        new_name, ok = QInputDialog.getText(
            self,
            "Editar Nombre Personalizado",
            "Introduce el nuevo nombre para esta pista (sin extensión):\n"
            "(Este nombre quedará fijado y se aplicará tal cual en disco)",
            text=current
        )
        if ok and new_name.strip():
            clean = sanitize_windows_filename(new_name.strip())
            if not clean.lower().endswith(".mp3"):
                clean += ".mp3"

            # Marcar la pista con nombre personalizado protegido en el modelo
            data["custom_filename"] = clean
            data["has_custom_name"] = True

            meta = data.get("resolved_metadata")
            if meta:
                meta.new_filename = clean
            else:
                src_path = Path(data.get("filepath", data.get("path", "")))
                if not src_path.name and orig_item:
                    src_path = Path(self.selected_directory or ".") / orig_item.text()
                from core.resolver import MetadataResolver
                r = MetadataResolver(search_dir=self.selected_directory)
                meta = r.resolve_track_metadata(src_path, custom_pattern=self.inspector.get_pattern())
                meta.new_filename = clean
                data["resolved_metadata"] = meta

            # Actualizar celda en la tabla con estilo visual ámbar distintivo
            item_proj = QTableWidgetItem(clean)
            item_proj.setToolTip(f"Nombre fijado manualmente por el usuario:\n{clean}")
            item_proj.setForeground(QColor("#ff9800"))
            font = item_proj.font()
            font.setBold(True)
            item_proj.setFont(font)
            self.table.setItem(row, self.COL_PROJECTED, item_proj)

            item_act = QTableWidgetItem("Personalizado")
            item_act.setForeground(QColor("#00b4d8"))
            self.table.setItem(row, self.COL_ACTION, item_act)

            disp_name = data.get("filename", orig_item.text() if orig_item else "Pista")
            self.progress_panel.append_log("INFO", f"Nombre personalizado fijado para '{disp_name}': {clean}")

    def _revert_to_pattern(self, row: int, data: Dict[str, Any]):
        """Restablece el nombre de una pista al patrón dinámico generado automáticamente."""
        if not data:
            data = self._get_row_track_data(row)
        data["has_custom_name"] = False
        data.pop("custom_filename", None)
        meta = data.get("resolved_metadata")
        if meta:
            pattern = self.inspector.get_pattern()
            track_dict = {
                "main_artists": meta.main_artists,
                "guest_artists": meta.guest_artists,
                "feat_artists": meta.feat_artists,
                "remix_artists": meta.remix_artists,
                "title": meta.title,
                "remix_name": meta.remix_name,
                "album": meta.album,
                "album_artists": meta.album_artists,
                "genre": meta.genre,
                "year": meta.year,
            }
            recomputed = ConfigManager.render_pattern(pattern, track_dict)
            meta.new_filename = recomputed
            item_proj = QTableWidgetItem(recomputed)
            item_proj.setToolTip(f"Proyectado: {recomputed}\nFuente: {meta.source}")
            self.table.setItem(row, self.COL_PROJECTED, item_proj)
            self.table.setItem(row, self.COL_ACTION, QTableWidgetItem("Activo"))
            self.progress_panel.append_log("INFO", f"Pista '{data.get('filename')}' restablecida a patrón automático.")

    def _toggle_exclude_track(self, row: int, data: Dict[str, Any]):
        if not data:
            data = self._get_row_track_data(row)
        was_excluded = data.get("excluded", False)
        is_exc = not was_excluded
        data["excluded"] = is_exc

        if is_exc:
            data["pre_exclude_status"] = data.get("status", "PENDIENTE")
            for col in range(self.table.columnCount()):
                it = self.table.item(row, col)
                if it:
                    it.setForeground(QColor("#666666"))

            badge = AudioBadge("EXCLUIDA")
            self.table.setCellWidget(row, self.COL_STATUS, badge)
            self.table.setItem(row, self.COL_ACTION, QTableWidgetItem("Excluido"))
            self.progress_panel.append_log("WARNING", f"Pista excluida del lote: '{data.get('filename')}'")
        else:
            restored_status = data.get("pre_exclude_status", data.get("status", "PENDIENTE"))
            data["status"] = restored_status

            for col in range(self.table.columnCount()):
                it = self.table.item(row, col)
                if it:
                    it.setForeground(Qt.GlobalColor.white)

            if data.get("has_custom_name"):
                proj_it = self.table.item(row, self.COL_PROJECTED)
                if proj_it:
                    proj_it.setForeground(QColor("#ff9800"))
                    f = proj_it.font()
                    f.setBold(True)
                    proj_it.setFont(f)
                act_it = self.table.item(row, self.COL_ACTION)
                if act_it:
                    act_it.setForeground(QColor("#00b4d8"))
                    act_it.setText("Personalizado")
            else:
                act_text = "En espera" if restored_status == "PENDIENTE" else "Activo"
                self.table.setItem(row, self.COL_ACTION, QTableWidgetItem(act_text))

            badge = AudioBadge(restored_status)
            self.table.setCellWidget(row, self.COL_STATUS, badge)
            self.progress_panel.append_log("INFO", f"Pista reincorporada al lote: '{data.get('filename')}'")

    def _on_settings_changed(self):
        """Al cambiar el patrón o ajustes en el inspector, actualiza las proyecciones si ya fueron resueltas."""
        pattern = self.inspector.get_pattern()
        for row in range(self.table.rowCount()):
            data = self._get_row_track_data(row)
            # Si el usuario fijó un nombre personalizado, protegerlo contra sobreescritura
            if data.get("has_custom_name"):
                continue

            meta = data.get("resolved_metadata")
            if meta:
                track_dict = {
                    "main_artists": meta.main_artists,
                    "guest_artists": meta.guest_artists,
                    "feat_artists": meta.feat_artists,
                    "remix_artists": meta.remix_artists,
                    "title": meta.title,
                    "remix_name": meta.remix_name,
                    "album": meta.album,
                    "album_artists": meta.album_artists,
                    "genre": meta.genre,
                    "year": meta.year,
                }
                updated_name = ConfigManager.render_pattern(pattern, track_dict)
                meta.new_filename = updated_name
                self.table.setItem(row, self.COL_PROJECTED, QTableWidgetItem(updated_name))

    def _toggle_inspector_panel(self):
        visible = self.inspector.isVisible()
        self.inspector.setVisible(not visible)
        self.btn_toggle_inspector.setText("Mostrar Ajustes ◀" if visible else "Ocultar Ajustes ▶")

    def _toggle_theme(self):
        current_theme = self.config_manager.get("ui_preferences", "accent_theme", "amber")
        new_theme = "cyan" if current_theme == "amber" else "amber"
        self.config_manager.set("ui_preferences", "accent_theme", new_theme)
        self.btn_theme.setText("Tema: Cian" if new_theme == "cyan" else "Tema: Ámbar")
        app = QApplication.instance()
        if app:
            app.setStyleSheet(load_stylesheet(new_theme))
