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

from common_utils import sanitize_windows_filename, resolve_binary, WINDOWS_RESERVED_NAMES
from enrich_metadata import MetadataEnricher, ResolvedMetadata


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
        self.enricher = MetadataEnricher()

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

    def test_modular_resolver(self):
        from core.resolver import MetadataResolver
        resolver = MetadataResolver()
        p = Path("Martin Garrix feat. Jex - Told You So.mp3")
        res = resolver.resolve_track_metadata(p)
        self.assertEqual(res.title, "Told You So")
        self.assertIn("Martin Garrix", res.main_artists)
        self.assertIn("Jex", res.feat_artists)

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
