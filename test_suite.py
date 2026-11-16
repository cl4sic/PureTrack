#!/usr/bin/env python3
"""
test_suite.py - Batería de Pruebas Unitarias y de Integración.

Valida:
1. Saneamiento estricto de nombres de archivo para Windows NTFS (WinError 123).
2. Localización jerárquica de binarios (resolve_binary).
3. Estructuración y formato de etiquetas ID3v2 según especificaciones.
4. Consistencia del manifiesto transaccional de rollback (rename_log.json).
"""

import sys
import unittest
from pathlib import Path
import json

from core.common_utils import sanitize_windows_filename, resolve_binary, WINDOWS_RESERVED_NAMES
from core.resolver import MetadataResolver, ResolvedMetadata


class TestWindowsSanitization(unittest.TestCase):
    """Pruebas de saneamiento para evitar fallos WinError 123 en sistemas de archivos NTFS."""

    def test_forbidden_characters_replaced_or_removed(self):
        # Dos puntos sustituidos por guión
        self.assertEqual(
            sanitize_windows_filename("Artist: Song: Subtitle.mp3"),
            "Artist - Song - Subtitle.mp3"
        )
        # Comillas dobles convertidas a comillas simples
        self.assertEqual(
            sanitize_windows_filename('Artist - Song "Radio Edit".mp3'),
            "Artist - Song 'Radio Edit'.mp3"
        )
        # Barras convertidas a guión
        self.assertEqual(
            sanitize_windows_filename("Artist/Collaborator - Track.mp3"),
            "Artist-Collaborator - Track.mp3"
        )
        # Asterisco, interrogación y pipes eliminados
        self.assertEqual(
            sanitize_windows_filename("Song *Special? | Remastered <2025>.mp3"),
            "Song Special Remastered 2025.mp3"
        )

    def test_trailing_dots_and_spaces_stripped(self):
        # En Windows un archivo no puede terminar en punto ni en espacio antes de la extensión
        self.assertEqual(
            sanitize_windows_filename("My Song . .mp3"),
            "My Song.mp3"
        )
        self.assertEqual(
            sanitize_windows_filename("Trailing Space   .mp3"),
            "Trailing Space.mp3"
        )

    def test_reserved_device_names_protected(self):
        # Nombres como CON, PRN, AUX, NUL
        self.assertEqual(sanitize_windows_filename("CON.mp3"), "_CON.mp3")
        self.assertEqual(sanitize_windows_filename("aux.mp3"), "_aux.mp3")
        self.assertEqual(sanitize_windows_filename("nul.mp3"), "_nul.mp3")
        self.assertEqual(sanitize_windows_filename("com1.mp3"), "_com1.mp3")


class TestBinaryResolution(unittest.TestCase):
    """Pruebas de localización autónoma de ejecutables externos."""

    def test_system_fallback(self):
        # En este entorno ffmpeg y ffprobe existen en PATH
        ffmpeg = resolve_binary("ffmpeg")
        self.assertTrue(Path(ffmpeg).exists() or ffmpeg == "ffmpeg")

    def test_local_bin_priority(self):
        bin_dir = Path("bin_mock_test")
        bin_dir.mkdir(exist_ok=True)
        dummy_exe = bin_dir / "test_bin.exe"
        dummy_exe.touch()

        try:
            resolved = resolve_binary("test_bin", search_dir=bin_dir.parent)
            self.assertEqual(Path(resolved).resolve(), dummy_exe.resolve())
        finally:
            dummy_exe.unlink()
            bin_dir.rmdir()


class TestMetadataEnrichmentRules(unittest.TestCase):
    """Pruebas de formato de nombres y estructura de etiquetas ID3v2."""

    def setUp(self):
        self.enricher = MetadataResolver()

    def test_format_conventions(self):
        # Formato de referencia 1: Martin Garrix & DallasK feat. Sasha Alex Sloan - Loop.mp3
        p = Path("Martin Garrix & DallasK feat. Sasha Alex Sloan - Loop.mp3")
        res = self.enricher.resolve_track_metadata(p)
        self.assertEqual(res.new_filename, "Martin Garrix & DallasK feat. Sasha Alex Sloan - Loop.mp3")
        self.assertEqual(res.id3_tit2, "Loop")
        self.assertIn("Martin Garrix", res.id3_tpe1)
        self.assertIn("DallasK", res.id3_tpe1)
        self.assertIn("Sasha Alex Sloan", res.id3_tpe1)
        self.assertEqual(res.id3_tcon, "Dance Pop")

    def test_remix_naming_convention(self):
        # Formato de referencia: [Artista] - [Título] - [Nombre del remix].mp3
        p = Path("Martin Garrix & Dua Lipa - Scared To Be Lonely - Brooks Remix.mp3")
        res = self.enricher.resolve_track_metadata(p)
        self.assertEqual(res.new_filename, "Martin Garrix & Dua Lipa - Scared To Be Lonely - Brooks Remix.mp3")
        self.assertEqual(res.id3_tit2, "Scared To Be Lonely - Brooks Remix")
        self.assertEqual(res.album, "Scared To Be Lonely (Remixes Vol. 1)")
        self.assertEqual(res.genre, "Future Bounce")


class TestRollbackManifestIntegrity(unittest.TestCase):
    """Verifica la estructura y consistencia del archivo rename_log.json."""

    def test_manifest_structure(self):
        log_path = Path("output/rename_log.json")
        if not log_path.exists():
            log_path = Path("rename_log.json")

        self.assertTrue(log_path.exists(), "Debe existir rename_log.json")
        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("timestamp", data)
        self.assertIn("operations", data)
        self.assertGreater(len(data["operations"]), 0)

        for op in data["operations"]:
            self.assertIn("original_path", op)
            self.assertIn("new_path", op)
            self.assertIn("old_tags", op)
            self.assertIn("new_tags", op)


class TestModularAudioMasterCore(unittest.TestCase):
    """Pruebas de la arquitectura modular AudioMaster (core y gui)."""

    def test_config_manager_and_pattern_builder(self):
        from core.config_manager import ConfigManager
        cm = ConfigManager()
        self.assertIsNotNone(cm.config_data)
        pattern = "{artist}{feat} - {title}{remix}"
        rendered = ConfigManager.render_pattern(pattern)
        self.assertIn("Martin Garrix", rendered)
        self.assertIn("Loop", rendered)
        self.assertTrue(rendered.endswith(".mp3"))

        # Prueba de gestión de presets personalizados
        success_add = cm.add_preset("Preset Test EDM", "{artist} - {title} [{year}]")
        self.assertTrue(success_add)
        self.assertIn("Preset Test EDM", cm.get_presets())
        self.assertEqual(cm.get_pattern(), "{artist} - {title} [{year}]")
        success_del = cm.delete_preset("Preset Test EDM")
        self.assertTrue(success_del)
        self.assertNotIn("Preset Test EDM", cm.get_presets())

    def test_modular_resolver(self):
        from core.resolver import MetadataResolver
        resolver = MetadataResolver()
        p = Path("Martin Garrix feat. Jex - Told You So.mp3")
        res = resolver.resolve_track_metadata(p)
        self.assertEqual(res.title, "Told You So")
        self.assertIn("Martin Garrix", res.main_artists)
        self.assertIn("Jex", res.feat_artists)

        # Prueba de prevención de falso positivo: Ocean Deep de Thomas Newson no debe mutar a Martin Garrix
        p_newson = Path("Thomas Newson - Ocean Deep.mp3")
        res_newson = resolver.resolve_track_metadata(p_newson)
        self.assertEqual(res_newson.title, "Ocean Deep")
        self.assertIn("Thomas Newson", res_newson.main_artists)
        self.assertNotIn("Martin Garrix", res_newson.main_artists)

    def test_worker_instantiation_and_concurrency(self):
        from gui.workers import AuditWorker, EnrichWorker
        p = Path("Martin Garrix feat. Jex - Told You So.mp3")
        worker = AuditWorker([p])
        self.assertFalse(worker.is_paused())
        self.assertFalse(worker.is_cancelled())
        worker.pause()
        self.assertTrue(worker.is_paused())
        worker.resume()
        self.assertFalse(worker.is_paused())
        worker.cancel()
        self.assertTrue(worker.is_cancelled())


class TestWindowsConsoleSuppression(unittest.TestCase):
    """Prueba que el helper centralizado aplique flags silenciosos sin consolas emergentes."""

    def test_hidden_subprocess_kwargs_structure(self):
        from core.common_utils import get_hidden_subprocess_kwargs
        kwargs = get_hidden_subprocess_kwargs()
        if sys.platform == "win32" or sys.platform.startswith("win"):
            self.assertIn("creationflags", kwargs)
            self.assertIn("startupinfo", kwargs)
        else:
            self.assertEqual(kwargs, {})

    def test_run_hidden_subprocess_execution(self):
        from core.common_utils import run_hidden_subprocess
        res = run_hidden_subprocess([sys.executable, "-c", "print('silent_ok')"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertEqual(res.stdout.strip(), "silent_ok")


class TestMainWindowTableAndInteractions(unittest.TestCase):
    """Pruebas de la lógica reactiva de la tabla, toggle de exclusión y persistencia de nombres personalizados."""

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        if not QApplication.instance():
            cls.app = QApplication(["--platform", "offscreen"])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        from core.config_manager import ConfigManager
        from gui.main_window import MainWindow
        from core.i18n import get_i18n
        get_i18n().set_language("es", save_to_config=False)
        self.cfg = ConfigManager()
        self.win = MainWindow(self.cfg)

    def tearDown(self):
        self.win.close()

    def test_audio_badge_statuses(self):
        from gui.widgets.audio_badge import AudioBadge
        for st, expected_display in [
            ("APTA", "APTA"),
            ("REVISIÓN MANUAL", "ALERTA"),
            ("ALERTA", "ALERTA"),
            ("CANDIDATA A ELIMINACIÓN", "ERROR"),
            ("ERROR", "ERROR"),
            ("APLICADO", "APLICADO"),
            ("EXCLUIDA", "EXCLUIDA"),
            ("PENDIENTE", "PENDIENTE")
        ]:
            b = AudioBadge(st)
            self.assertIn(expected_display, b.label.text())

    def test_table_row_tracking_and_audit_signal(self):
        from core.auditor import AudioAuditResult
        from core.resolver import ResolvedMetadata
        from PySide6.QtCore import Qt

        test_files = [Path("/tmp/music_test/Test Artist - Test Track.mp3")]
        self.win._load_files_into_table(test_files)
        self.assertEqual(self.win.table.rowCount(), 1)

        # Verificar UserRole data
        item_orig = self.win.table.item(0, self.win.COL_ORIGINAL)
        self.assertEqual(item_orig.data(Qt.ItemDataRole.UserRole), str(test_files[0].resolve()))

        # Simular señal de auditoría
        res = AudioAuditResult(
            filename="Test Artist - Test Track.mp3",
            filepath=str(test_files[0].resolve()),
            duration_sec=185.0,
            mutagen_bitrate_kbps=320,
            ffprobe_stream_bitrate_kbps=320,
            ffprobe_format_bitrate_kbps=320,
            bitrate_mode="CBR",
            sample_rate_hz=44100,
            channels=2,
            ffmpeg_integrity_ok=True,
            ffmpeg_errors="",
            peak_dbfs=-0.5,
            rms_dbfs=-8.2,
            dynamic_range_db=7.7,
            clipping_samples_count=0,
            clipping_pct=0.0,
            has_clipping_risk=False,
            last_400ms_rms_dbfs=-18.0,
            last_100ms_rms_dbfs=-22.0,
            has_abrupt_ending=False,
            anomalous_silence_count=0,
            silence_details="",
            verdict="APTA",
            verdict_reason="Pista íntegra y de calidad óptima"
        )
        res.resolved_metadata = ResolvedMetadata(
            original_path=str(test_files[0].resolve()),
            original_filename="Test Artist - Test Track.mp3",
            new_filename="Test Artist - Test Track Proyectado.mp3",
            main_artists=["Test Artist"],
            guest_artists=[],
            feat_artists=[],
            remix_artists=[],
            title="Test Track Proyectado",
            remix_name=None,
            album="Test Album",
            album_artists=["Test Artist"],
            genre="Electronic",
            year="2025",
            id3_tit2="Test Track Proyectado",
            id3_tpe1="Test Artist",
            id3_talb="Test Album",
            id3_tpe2="Test Artist",
            id3_tcon="Electronic",
            id3_tdrc="2025",
            source="Test"
        )

        self.win._on_track_audited(res)

        # Verificar que la fila se actualizó reactivamente
        badge_widget = self.win.table.cellWidget(0, self.win.COL_STATUS)
        self.assertIn("APTA", badge_widget.label.text())
        self.assertEqual(self.win.table.item(0, self.win.COL_PROJECTED).text(), "Test Artist - Test Track Proyectado.mp3")
        self.assertIn("320 kbps", self.win.table.item(0, self.win.COL_BITRATE).text())
        self.assertEqual(self.win.table.item(0, self.win.COL_DURATION).text(), "3:05")
        self.assertEqual(self.win.table.item(0, self.win.COL_CLIPPING).text(), "0.000%")

    def test_bidirectional_toggle_exclude_include(self):
        test_files = [Path("/tmp/music_test/Song_A.mp3")]
        self.win._load_files_into_table(test_files)
        data = self.win._get_row_track_data(0)
        data["status"] = "APTA"

        # 1. Excluir pista
        self.win._toggle_exclude_track(0, data)
        self.assertTrue(data.get("excluded"))
        badge = self.win.table.cellWidget(0, self.win.COL_STATUS)
        self.assertIn("EXCLUIDA", badge.label.text())
        self.assertEqual(self.win.table.item(0, self.win.COL_ACTION).text(), "Excluido")

        # 2. Re-incluir pista (restaura estado original "APTA")
        self.win._toggle_exclude_track(0, data)
        self.assertFalse(data.get("excluded"))
        badge_restored = self.win.table.cellWidget(0, self.win.COL_STATUS)
        self.assertIn("APTA", badge_restored.label.text())
        self.assertEqual(self.win.table.item(0, self.win.COL_ACTION).text(), "Activo")

    def test_custom_name_override_persistence(self):
        test_files = [Path("/tmp/music_test/Original Song.mp3")]
        self.win._load_files_into_table(test_files)
        data = self.win._get_row_track_data(0)

        # Simular asignación de nombre personalizado
        data["custom_filename"] = "Custom Name Override.mp3"
        data["has_custom_name"] = True
        self.win.table.item(0, self.win.COL_PROJECTED).setText("Custom Name Override.mp3")

        # Comprobar que _on_settings_changed NO sobreescribe el nombre personalizado
        self.win._on_settings_changed()
        self.assertEqual(self.win.table.item(0, self.win.COL_PROJECTED).text(), "Custom Name Override.mp3")

        # Simular aplicación en disco
        self.win._on_track_applied("Original Song.mp3", "Custom Name Override.mp3", True, "OK")
        badge = self.win.table.cellWidget(0, self.win.COL_STATUS)
        self.assertIn("APLICADO", badge.label.text())
        self.assertEqual(self.win.table.item(0, self.win.COL_PROJECTED).text(), "Custom Name Override.mp3")
        self.assertEqual(self.win.table.item(0, self.win.COL_ACTION).text(), "Actualizado en disco")

    def test_custom_name_prefill_and_sanitization(self):
        from unittest.mock import patch

        test_files = [Path("/tmp/music_test/My Track: Special Edition.mp3")]
        self.win._load_files_into_table(test_files)
        data = self.win._get_row_track_data(0)

        # Caso 1: Sin proyectar ("—"), debe pre-rellenar con el nombre original sin .mp3
        with patch("gui.main_window.QInputDialog.getText", return_value=("Custom Track Edit", True)) as mock_dialog:
            self.win._edit_track_manually(0, data)
            mock_dialog.assert_called_once()
            args, kwargs = mock_dialog.call_args
            self.assertEqual(kwargs.get("text"), "My Track: Special Edition")

        self.assertEqual(data.get("custom_filename"), "Custom Track Edit.mp3")
        self.assertTrue(data.get("has_custom_name"))
        self.assertEqual(self.win.table.item(0, self.win.COL_PROJECTED).text(), "Custom Track Edit.mp3")

        # Caso 2: Con nombre ya proyectado, debe pre-rellenar con ese nombre sin .mp3
        with patch("gui.main_window.QInputDialog.getText", return_value=("Renamed <Clean> Track: Final", True)) as mock_dialog:
            self.win._edit_track_manually(0, data)
            args, kwargs = mock_dialog.call_args
            self.assertEqual(kwargs.get("text"), "Custom Track Edit")

        # Verificar que se sanearon los caracteres prohibidos (<>:) y se aseguró .mp3
        self.assertEqual(data.get("custom_filename"), "Renamed Clean Track - Final.mp3")
        self.assertEqual(self.win.table.item(0, self.win.COL_PROJECTED).text(), "Renamed Clean Track - Final.mp3")


class TestPureTrackI18n(unittest.TestCase):
    """Pruebas del motor de internacionalización y multi-idioma (i18n)."""

    def setUp(self):
        from core.i18n import get_i18n
        self.i18n = get_i18n()

    def test_translation_dictionaries_loaded(self):
        self.assertIn("es", self.i18n._translations)
        self.assertIn("en", self.i18n._translations)
        self.assertGreater(len(self.i18n._translations["es"]), 5)
        self.assertGreater(len(self.i18n._translations["en"]), 5)

    def test_hot_switching_and_signal(self):
        received_langs = []
        self.i18n.sig_language_changed.connect(lambda lang: received_langs.append(lang))

        self.i18n.set_language("en", save_to_config=False)
        self.assertEqual(self.i18n.get_language(), "en")
        self.assertEqual(self.i18n.t("top_bar.browse_btn"), "Browse...")
        self.assertEqual(self.i18n.t("buttons.audit"), "Audit Library")
        self.assertEqual(self.i18n.get_badge_text("APTA"), "OK")
        self.assertEqual(self.i18n.get_badge_text("ALERTA"), "WARNING")
        self.assertEqual(self.i18n.get_badge_text("EXCLUIDA"), "EXCLUDED")
        self.assertEqual(self.i18n.get_badge_text("APLICADO"), "APPLIED")

        self.i18n.set_language("es", save_to_config=False)
        self.assertEqual(self.i18n.get_language(), "es")
        self.assertEqual(self.i18n.t("top_bar.browse_btn"), "Examinar...")
        self.assertEqual(self.i18n.t("buttons.audit"), "Auditar Biblioteca")
        self.assertEqual(self.i18n.get_badge_text("APTA"), "APTA")
        self.assertEqual(self.i18n.get_badge_text("ALERTA"), "ALERTA")
        self.assertEqual(self.i18n.get_badge_text("EXCLUIDA"), "EXCLUIDA")
        self.assertEqual(self.i18n.get_badge_text("APLICADO"), "APLICADO")

        self.assertIn("en", received_langs)
        self.assertIn("es", received_langs)

    def test_fallback_and_formatting(self):
        self.i18n.set_language("en", save_to_config=False)
        formatted = self.i18n.t("progress.eta", eta="45", speed="2.5")
        self.assertIn("45", formatted)
        self.assertIn("2.5", formatted)

        # Clave inexistente devuelve fallback por defecto o la propia clave
        missing = self.i18n.t("non_existent_key", default="Fallback Default")
        self.assertEqual(missing, "Fallback Default")


class TestPureTrackIcon(unittest.TestCase):
    """Pruebas de presencia e integridad de los iconos multiplataforma."""

    def test_icon_assets_exist_and_valid(self):
        from pathlib import Path
        from PySide6.QtGui import QIcon, QImage

        assets_dir = Path(__file__).resolve().parent / "gui" / "assets"
        png_path = assets_dir / "icon.png"
        ico_path = assets_dir / "icon.ico"

        self.assertTrue(png_path.exists(), "icon.png no existe en gui/assets/")
        self.assertTrue(ico_path.exists(), "icon.ico no existe en gui/assets/")
        self.assertGreater(png_path.stat().st_size, 5000, "icon.png es demasiado pequeño o está corrupto")
        self.assertGreater(ico_path.stat().st_size, 5000, "icon.ico es demasiado pequeño o está corrupto")

        # Verificar carga en QImage y dimensiones
        img = QImage(str(png_path))
        self.assertFalse(img.isNull(), "QImage no pudo cargar icon.png")
        self.assertEqual(img.width(), 1024)
        self.assertEqual(img.height(), 1024)
        self.assertEqual(img.pixelColor(10, 10).alpha(), 0, "El fondo de icon.png debe ser 100% transparente")

        # Verificar carga en QIcon
        ico = QIcon(str(ico_path))
        self.assertFalse(ico.isNull(), "QIcon no pudo cargar icon.ico")
        sizes = [s.width() for s in ico.availableSizes()]
        for expected_size in [16, 32, 48, 64, 128, 256]:
            self.assertIn(expected_size, sizes, f"icon.ico no contiene la resolución requerida {expected_size}x{expected_size}")


class TestAuditorIntegrityAndCorruptionFilter(unittest.TestCase):
    """Pruebas de filtrado de falsos positivos en auditoría acústica."""

    def setUp(self):
        from core.auditor import AudioAuditor
        self.auditor = AudioAuditor()

    def test_benign_warnings_filtered(self):
        """Verifica que patrones benignos en stderr de FFmpeg no fallen la comprobación de integridad."""
        from unittest.mock import patch, MagicMock

        # Simular salida de FFmpeg con retorno 0 pero stderr con advertencias benignas típicas
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stderr = (
            "[mp3float @ 0x556] Header missing\n"
            "[aist#0:0/mp3 @ 0x556] [dec:mp3float @ 0x556] Error submitting packet to decoder: Invalid data found when processing input\n"
            "[mjpeg @ 0x556] overread, skip\n"
            "Could not update timestamps for skipped samples\n"
        )

        with patch("core.auditor.run_hidden_subprocess", return_value=mock_res):
            ok, err = self.auditor.check_ffmpeg_integrity(Path("/fake/track.mp3"))
            self.assertTrue(ok, "Los avisos benignos deben filtrarse y marcar ok=True")
            self.assertEqual(err, "")

    def test_fatal_errors_not_filtered(self):
        """Verifica que fallos reales de FFmpeg (returncode != 0 o errores no benignos) se marquen como fallo."""
        from unittest.mock import patch, MagicMock

        mock_res = MagicMock()
        mock_res.returncode = 183
        mock_res.stderr = "Failed to find two consecutive MPEG audio frames.\nError opening input: Invalid data found when processing input"

        with patch("core.auditor.run_hidden_subprocess", return_value=mock_res):
            ok, err = self.auditor.check_ffmpeg_integrity(Path("/fake/corrupt.mp3"))
            self.assertFalse(ok, "Un fallo con returncode != 0 debe marcar ok=False")
            self.assertIn("Error opening input", err)

    def test_uploaded_audio_files_evaluated_as_apta(self):
        """Verifica que los archivos MP3 reales adjuntos por el usuario sean auditados como APTA sin falsos positivos."""
        uploaded_dir = Path("/home/cl4sic/.gemini/antigravity/brain/9c655c3a-371c-444a-8060-35f03d9ee538/.user_uploaded")
        mp3_files = list(uploaded_dir.glob("*.mp3"))
        if not mp3_files:
            self.skipTest("No se encontraron archivos .mp3 en la carpeta de subidas de usuario.")

        for mp3_path in mp3_files:
            res = self.auditor.audit_file(mp3_path)
            self.assertTrue(res.ffmpeg_integrity_ok, f"Falso positivo en integridad FFmpeg para {mp3_path.name}: {res.ffmpeg_errors}")
            self.assertEqual(res.verdict, "APTA", f"La pista {mp3_path.name} debe ser APTA, no {res.verdict} (Motivo: {res.verdict_reason})")

    def test_missing_ffmpeg_graceful_fallback(self):
        """Verifica que si FFmpeg no está disponible, no marque erróneamente un archivo válido como corrupto."""
        from core.auditor import AudioAuditor
        auditor_no_ff = AudioAuditor()
        auditor_no_ff.has_ffmpeg = False

        uploaded_dir = Path("/home/cl4sic/.gemini/antigravity/brain/9c655c3a-371c-444a-8060-35f03d9ee538/.user_uploaded")
        mp3_files = list(uploaded_dir.glob("*.mp3"))
        if mp3_files:
            res = auditor_no_ff.audit_file(mp3_files[0])
            self.assertNotEqual(res.verdict, "CANDIDATA A ELIMINACIÓN", "No debe marcarse como corrupta si FFmpeg falta pero SoundFile decodifica")
            self.assertIn(res.verdict, ("APTA", "REVISIÓN MANUAL"))

    def test_multi_resolution_icon_and_desktop_integration(self):
        """Verifica que resolve_puretrack_icon construya un QIcon con múltiples tamaños (16 a 1024)."""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(["--platform", "offscreen"])
        from app import resolve_puretrack_icon
        icon = resolve_puretrack_icon()
        self.assertFalse(icon.isNull(), "resolve_puretrack_icon devolvió un icono nulo")
        sizes = [s.width() for s in icon.availableSizes()]
        self.assertTrue(len(sizes) >= 3, f"Se esperaban múltiples resoluciones, se obtuvieron: {sizes}")
        self.assertTrue(any(s >= 256 for s in sizes), "Falta resolución de alta densidad (>= 256px)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
