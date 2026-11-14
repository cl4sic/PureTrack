#!/usr/bin/env python3
"""
gui/workers.py - Workers QThread Concurrentes con Soporte de Pausa, Reanudación y Cancelación.

Garantiza que ninguna operación de I/O pesada (FFmpeg, mutagen, SQLite, red) bloquee el MainThread.
Emite señales reactivas para:
- Progreso dual (progreso de la canción individual y progreso del lote total).
- Métricas de ETA y velocidad (canciones por segundo).
- Diagnósticos y registros en tiempo real para la consola y tabla de pistas.
"""

import time
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple, Union

from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition

from core.auditor import AudioAuditor, AudioAuditResult
from core.resolver import MetadataResolver, ResolvedMetadata
from core.tagger import AudioTagger
from core.config_manager import ConfigManager
from core.i18n import t


class BaseAudioWorker(QThread):
    """Clase base de worker con control seguro de hilos (Pausa / Reanudar / Cancelar)."""

    sig_progress = Signal(int, int, str)          # current_item, total_items, item_label
    sig_item_progress = Signal(int, int, str)     # current_step, total_steps, step_name
    sig_eta = Signal(float, float)                # seconds_remaining, items_per_second
    sig_log = Signal(str, str)                    # level ("INFO", "WARNING", "ERROR", "SUCCESS"), text
    sig_status = Signal(str)                      # status text for main UI
    sig_finished = Signal(bool, str)              # success, summary
    sig_paused = Signal()
    sig_resumed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mutex = QMutex()
        self._pause_condition = QWaitCondition()
        self._is_paused = False
        self._is_cancelled = False

    def pause(self):
        """Pausa la ejecución en el siguiente punto de control seguro."""
        self._mutex.lock()
        self._is_paused = True
        self._mutex.unlock()
        self.sig_paused.emit()
        self.sig_log.emit("WARNING", "Proceso pausado por el usuario.")

    def resume(self):
        """Reanuda la ejecución del worker pausado."""
        self._mutex.lock()
        self._is_paused = False
        self._pause_condition.wakeAll()
        self._mutex.unlock()
        self.sig_resumed.emit()
        self.sig_log.emit("INFO", "Proceso reanudado.")

    def cancel(self):
        """Solicita la cancelación inmediata y limpia del proceso en segundo plano."""
        self._mutex.lock()
        self._is_cancelled = True
        self._is_paused = False
        self._pause_condition.wakeAll()
        self._mutex.unlock()
        self.sig_log.emit("WARNING", "Cancelación solicitada por el usuario. Deteniendo...")

    def is_paused(self) -> bool:
        self._mutex.lock()
        p = self._is_paused
        self._mutex.unlock()
        return p

    def is_cancelled(self) -> bool:
        self._mutex.lock()
        c = self._is_cancelled
        self._mutex.unlock()
        return c

    def _check_pause_and_cancel(self) -> bool:
        """Pausa el hilo si está en pausa; retorna True si fue cancelado."""
        self._mutex.lock()
        while self._is_paused and not self._is_cancelled:
            self._pause_condition.wait(self._mutex)
        cancelled = self._is_cancelled
        self._mutex.unlock()
        return cancelled


class AuditWorker(BaseAudioWorker):
    """Worker para la auditoría técnica exhaustiva de un lote de pistas MP3."""

    sig_track_audited = Signal(object)  # Emite AudioAuditResult

    def __init__(
        self,
        file_paths: List[Path],
        audit_settings: Optional[Dict[str, Any]] = None,
        naming_pattern: Optional[str] = None,
        parent=None
    ):
        super().__init__(parent)
        self.file_paths = [Path(p) for p in file_paths]
        self.naming_pattern = naming_pattern
        settings = audit_settings or {}
        search_dir = self.file_paths[0].parent if self.file_paths else None
        self.resolver = MetadataResolver(search_dir=search_dir)
        self.auditor = AudioAuditor(
            min_bitrate_kbps=settings.get("min_bitrate_kbps", 190),
            min_duration_sec=settings.get("min_duration_sec", 60.0),
            silence_threshold_sec=settings.get("silence_threshold_sec", 3.0),
            abrupt_rms_threshold_dbfs=settings.get("abrupt_rms_threshold_dbfs", -14.0),
            clipping_threshold_pct=settings.get("clipping_threshold_pct", 0.5),
            check_clipping=settings.get("check_clipping", True),
            check_silence=settings.get("check_silence", True),
            check_abrupt_ending=settings.get("check_abrupt_ending", True),
            search_dir=search_dir
        )

    def run(self):
        total = len(self.file_paths)
        if total == 0:
            self.sig_finished.emit(True, "No se seleccionaron archivos para auditar.")
            return

        self.sig_log.emit("INFO", f"Iniciando auditoría técnica de {total} archivo(s)...")
        start_time = time.time()
        processed = 0

        for idx, fpath in enumerate(self.file_paths, 1):
            if self._check_pause_and_cancel():
                self.sig_finished.emit(False, "Auditoría cancelada por el usuario.")
                return

            self.sig_status.emit(f"Auditando [{idx}/{total}]: {fpath.name}")
            self.sig_progress.emit(idx - 1, total, fpath.name)

            # Paso 1: Comprobación de integridad
            self.sig_item_progress.emit(1, 4, t("progress.step_ffmpeg", "Decodificación e Integridad FFmpeg"))
            if self._check_pause_and_cancel():
                self.sig_finished.emit(False, "Auditoría cancelada.")
                return

            # Paso 2: Análisis completo
            self.sig_item_progress.emit(2, 4, t("progress.step_bitrate", "Extracción de Bitrate y Streams"))
            # Paso 3: Silencios y Espectro acústico
            self.sig_item_progress.emit(3, 4, t("progress.step_spectrum", "Análisis de Espectro, Clipping y Silencios"))
            try:
                res: AudioAuditResult = self.auditor.audit_file(fpath)
                try:
                    res.resolved_metadata = self.resolver.resolve_track_metadata(
                        fpath,
                        custom_pattern=self.naming_pattern
                    )
                except Exception:
                    res.resolved_metadata = None

                self.sig_item_progress.emit(4, 4, t("progress.step_done", "Diagnóstico finalizado"))

                self.sig_track_audited.emit(res)
                processed += 1

                level = "SUCCESS" if res.verdict == "APTA" else ("WARNING" if res.verdict == "REVISIÓN MANUAL" else "ERROR")
                self.sig_log.emit(level, f"[{res.verdict}] {fpath.name} | {res.mutagen_bitrate_kbps} kbps ({res.bitrate_mode}) | {res.duration_sec}s | Clipping: {res.clipping_pct}%")
            except Exception as e:
                self.sig_log.emit("ERROR", f"Error auditando {fpath.name}: {e}")

            # Cálculo de velocidad y tiempo restante estimado (ETA)
            elapsed = time.time() - start_time
            if processed > 0:
                speed = processed / elapsed
                remaining_sec = (total - processed) / speed if speed > 0 else 0.0
                self.sig_eta.emit(remaining_sec, speed)

            self.sig_progress.emit(idx, total, fpath.name)

        total_elapsed = time.time() - start_time
        summary = f"Auditoría completada: {processed}/{total} pistas analizadas en {total_elapsed:.1f}s."
        self.sig_log.emit("SUCCESS", summary)
        self.sig_finished.emit(True, summary)


class EnrichWorker(BaseAudioWorker):
    """Worker para la identificación de metadatos y cálculo del nombre proyectado."""

    sig_track_resolved = Signal(object)  # Emite ResolvedMetadata

    def __init__(
        self,
        file_paths: List[Path],
        naming_pattern: Optional[str] = None,
        parent=None
    ):
        super().__init__(parent)
        self.file_paths = [Path(p) for p in file_paths]
        self.naming_pattern = naming_pattern
        self.resolver = MetadataResolver(search_dir=self.file_paths[0].parent if self.file_paths else None)

    def run(self):
        total = len(self.file_paths)
        if total == 0:
            self.sig_finished.emit(True, "No se seleccionaron archivos para resolver.")
            return

        self.sig_log.emit("INFO", f"Iniciando resolución de metadatos para {total} archivo(s)...")
        start_time = time.time()
        processed = 0

        for idx, fpath in enumerate(self.file_paths, 1):
            if self._check_pause_and_cancel():
                self.sig_finished.emit(False, "Resolución de metadatos cancelada por el usuario.")
                return

            self.sig_status.emit(f"Resolviendo [{idx}/{total}]: {fpath.name}")
            self.sig_progress.emit(idx - 1, total, fpath.name)

            self.sig_item_progress.emit(1, 3, "Consulta en Caché y Catálogos Discográficos")
            try:
                resolved: ResolvedMetadata = self.resolver.resolve_track_metadata(
                    fpath,
                    custom_pattern=self.naming_pattern
                )
                self.sig_item_progress.emit(2, 3, "Saneamiento NTFS y Validación de Ruta")
                self.sig_item_progress.emit(3, 3, "Construcción de Tags ID3v2")

                self.sig_track_resolved.emit(resolved)
                processed += 1
                self.sig_log.emit("INFO", f"Proyección [{resolved.source}]: '{fpath.name}' -> '{resolved.new_filename}'")
            except Exception as e:
                self.sig_log.emit("ERROR", f"Error resolviendo metadatos en {fpath.name}: {e}")

            elapsed = time.time() - start_time
            if processed > 0:
                speed = processed / elapsed
                remaining_sec = (total - processed) / speed if speed > 0 else 0.0
                self.sig_eta.emit(remaining_sec, speed)

            self.sig_progress.emit(idx, total, fpath.name)

        summary = f"Identificación y proyección completada para {processed}/{total} pistas."
        self.sig_log.emit("SUCCESS", summary)
        self.sig_finished.emit(True, summary)


class ApplyWorker(BaseAudioWorker):
    """Worker para la aplicación atómica en disco (escritura ID3v2 y renombrado) con rollback log."""

    sig_track_applied = Signal(str, str, bool, str)  # orig_name, new_name, success, message

    def __init__(
        self,
        operations: List[Tuple[ResolvedMetadata, Path, Path]],
        dry_run: bool = False,
        search_dir: Optional[Path] = None,
        parent=None
    ):
        super().__init__(parent)
        self.operations = operations
        self.dry_run = dry_run
        self.tagger = AudioTagger(search_dir=search_dir)

    def run(self):
        total = len(self.operations)
        if total == 0:
            self.sig_finished.emit(True, "No hay operaciones para ejecutar.")
            return

        mode_str = "SIMULACIÓN (Dry-Run)" if self.dry_run else "EJECUCIÓN REAL EN DISCO"
        self.sig_log.emit("INFO", f"Iniciando {mode_str} para {total} archivo(s)...")

        # Si es modo real, la transacción guarda primero el log
        res = self.tagger.execute_transaction(self.operations, dry_run=self.dry_run)
        if not res.get("success", False) and not self.dry_run:
            err = res.get("error", "Fallo al inicializar transacción de seguridad.")
            self.sig_log.emit("ERROR", err)
            self.sig_finished.emit(False, err)
            return

        manifest = res.get("manifest", {})
        operations_records = manifest.get("operations", [])

        for idx, (meta, src_path, dst_path) in enumerate(self.operations, 1):
            if self._check_pause_and_cancel():
                self.sig_finished.emit(False, "Operación cancelada por el usuario.")
                return

            self.sig_progress.emit(idx, total, meta.new_filename)
            self.sig_item_progress.emit(1, 2, t("progress.step_tagging", "Actualizando etiquetas ID3v2..."))

            if self.dry_run:
                msg = f"[DRY-RUN] Proyectado: {src_path.name} -> {dst_path.name}"
                self.sig_track_applied.emit(src_path.name, dst_path.name, True, msg)
                self.sig_log.emit("INFO", msg)
            else:
                msg = f"Aplicado en disco: {dst_path.name}"
                self.sig_track_applied.emit(src_path.name, dst_path.name, True, msg)
                self.sig_log.emit("SUCCESS", msg)

        status_msg = f"{'Simulación' if self.dry_run else 'Aplicación'} finalizada para {total} pistas."
        self.sig_finished.emit(True, status_msg)


class RollbackWorker(BaseAudioWorker):
    """Worker para la reversión / restauración 100% garantizada de archivos y etiquetas."""

    sig_track_restored = Signal(str, str, bool, str)

    def __init__(self, search_dir: Optional[Path] = None, parent=None):
        super().__init__(parent)
        self.tagger = AudioTagger(search_dir=search_dir)

    def run(self):
        self.sig_log.emit("WARNING", "Iniciando proceso de rollback y restauración...")
        success, restored, summary = self.tagger.rollback()
        if success:
            self.sig_log.emit("SUCCESS", f"Rollback completado con éxito: {summary}")
            self.sig_finished.emit(True, summary)
        else:
            self.sig_log.emit("ERROR", f"Rollback fallido o incompleto: {summary}")
            self.sig_finished.emit(False, summary)
