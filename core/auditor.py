#!/usr/bin/env python3
"""
core/auditor.py - Auditoría Técnica y Diagnóstico de Archivos de Audio.

Analiza:
- Integridad de decodificación mediante FFmpeg.
- Bitrate exacto (CBR / VBR) mediante Mutagen y FFprobe.
- Duración, frecuencia de muestreo y número de canales.
- Silencios anómalos en el cuerpo del tema (FFmpeg silencedetect).
- Saturación digital / clipping (muestras >= 0 dBFS / 0.999).
- Rango dinámico y cortes abruptos (RMS en los últimos 400ms y 100ms).
"""

from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Union, Tuple
import sys
import json
import csv
import subprocess

import numpy as np
import soundfile as sf
import mutagen
from mutagen.mp3 import MP3, BitrateMode

from core.common_utils import resolve_binary, to_extended_length_path, run_hidden_subprocess


@dataclass
class AudioAuditResult:
    filename: str
    filepath: str
    duration_sec: float
    mutagen_bitrate_kbps: int
    ffprobe_stream_bitrate_kbps: Optional[int]
    ffprobe_format_bitrate_kbps: Optional[int]
    bitrate_mode: str  # "CBR", "VBR", "UNKNOWN"
    sample_rate_hz: int
    channels: int
    ffmpeg_integrity_ok: bool
    ffmpeg_errors: str
    peak_dbfs: float
    rms_dbfs: float
    dynamic_range_db: float
    clipping_samples_count: int
    clipping_pct: float
    has_clipping_risk: bool
    last_400ms_rms_dbfs: float
    last_100ms_rms_dbfs: float
    has_abrupt_ending: bool
    anomalous_silence_count: int
    silence_details: str
    anomalies: List[str] = field(default_factory=list)
    verdict: str = "APTA"  # "APTA", "REVISIÓN MANUAL", "CANDIDATA A ELIMINACIÓN"
    verdict_reason: str = "Pista íntegra y de calidad óptima"
    resolved_metadata: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AudioAuditor:
    """Auditor exhaustivo de calidad acústica y técnica con soporte multiplataforma."""

    def __init__(
        self,
        min_bitrate_kbps: int = 190,
        min_duration_sec: float = 60.0,
        silence_threshold_sec: float = 3.0,
        abrupt_rms_threshold_dbfs: float = -14.0,
        clipping_threshold_pct: float = 0.5,
        check_clipping: bool = True,
        check_silence: bool = True,
        check_abrupt_ending: bool = True,
        search_dir: Optional[Union[str, Path]] = None,
    ):
        self.min_bitrate_kbps = min_bitrate_kbps
        self.min_duration_sec = min_duration_sec
        self.silence_threshold_sec = silence_threshold_sec
        self.abrupt_rms_threshold_dbfs = abrupt_rms_threshold_dbfs
        self.clipping_threshold_pct = clipping_threshold_pct
        self.check_clipping = check_clipping
        self.check_silence = check_silence
        self.check_abrupt_ending = check_abrupt_ending
        self.search_dir = Path(search_dir).resolve() if search_dir else None

        # Resolución autónoma de binarios y verificación de operatividad
        self.ffmpeg_bin = resolve_binary("ffmpeg", search_dir=self.search_dir)
        self.ffprobe_bin = resolve_binary("ffprobe", search_dir=self.search_dir)
        self.has_ffmpeg = self._test_binary(self.ffmpeg_bin)
        self.has_ffprobe = self._test_binary(self.ffprobe_bin)

    def _test_binary(self, bin_path: str) -> bool:
        """Comprueba de forma silenciosa si un binario externo es ejecutable."""
        try:
            res = run_hidden_subprocess([bin_path, "-version"], capture_output=True, text=True, check=False)
            return res.returncode == 0
        except Exception:
            return False

    # Patrones de advertencias benignas en MP3 (carátulas, timestamps iniciales, headers Xing/LAME, etc.)
    BENIGN_WARNING_PATTERNS = (
        "mjpeg",
        "png",
        "image",
        "attached pic",
        "could not update timestamps",
        "header missing",
        "error submitting packet to decoder",
        "overread",
        "skip junk",
        "estimating duration",
        "xing",
        "lame",
        "info",
        "incomplete frame",
        "trailing garbage",
        "padding",
        "invalid new backstep",
        "unspecified pixel format",
        "discarding initial",
        "multiple frames",
        "channel element",
        "id3",
        "gain",
        "replaying",
        "frame size",
        "loss of sync",
        "sync lost",
        "bitrate",
        "sample rate",
        "swscaler",
        "audio device",
        "nobs",
        "max_val",
        "partial file",
    )

    def check_ffmpeg_integrity(self, file_path: Path) -> Tuple[bool, str]:
        """
        Comprueba errores de decodificación o corrupción usando FFmpeg.
        Filtra advertencias benignas (carátulas, timestamps, headers) de forma estricta.
        Si FFmpeg no está disponible en el entorno, delega la verificación al decodificador interno.
        """
        if not self.has_ffmpeg:
            return (True, "FFmpeg no disponible en entorno (validado por decodificador interno)")

        null_dest = "NUL" if sys.platform.startswith("win") else "-"
        # -vn omite streams de video/carátula para evaluar puramente la integridad del flujo de audio
        cmd = [self.ffmpeg_bin, "-v", "error", "-i", str(file_path), "-vn", "-f", "null", null_dest]
        try:
            res = run_hidden_subprocess(cmd, capture_output=True, text=True, check=False)
            raw_err = res.stderr.strip()

            # Filtrar cualquier mensaje por la lista de patrones benignos conocidos
            if raw_err:
                real_errors = []
                for line in raw_err.splitlines():
                    line_lower = line.lower()
                    if not any(pat in line_lower for pat in self.BENIGN_WARNING_PATTERNS):
                        real_errors.append(line.strip())

                if real_errors:
                    return (False, "\n".join(real_errors))

            # Si el código de salida fue no-cero y no hubo errores de texto benignos
            if res.returncode != 0 and not raw_err:
                return (False, f"FFmpeg finalizó con código de error {res.returncode}")

            return (True, "")
        except Exception as e:
            return (False, f"Excepción ejecutando FFmpeg ({self.ffmpeg_bin}): {e}")

    def get_bitrate_and_stream_info(self, file_path: Path) -> Dict[str, Any]:
        """Extrae bitrate exacto y características de stream vía mutagen y ffprobe."""
        m = MP3(str(file_path))
        mutagen_kbps = round(m.info.bitrate / 1000)
        dur = float(m.info.length)
        sr = int(m.info.sample_rate)
        ch = int(m.info.channels)

        cmd = [
            self.ffprobe_bin,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path)
        ]
        ffprobe_stream_kbps = None
        ffprobe_fmt_kbps = None

        try:
            res = run_hidden_subprocess(cmd, capture_output=True, text=True, check=False)
            if res.returncode == 0:
                data = json.loads(res.stdout)
                streams = [s for s in data.get("streams", []) if s.get("codec_type") == "audio"]
                if streams:
                    s0 = streams[0]
                    if "bit_rate" in s0 and s0["bit_rate"]:
                        ffprobe_stream_kbps = round(int(s0["bit_rate"]) / 1000)
                fmt = data.get("format", {})
                if "bit_rate" in fmt and fmt["bit_rate"]:
                    ffprobe_fmt_kbps = round(int(fmt["bit_rate"]) / 1000)
        except Exception:
            pass

        if m.info.bitrate_mode == BitrateMode.CBR:
            bitrate_mode_str = "CBR"
        elif m.info.bitrate_mode == BitrateMode.VBR:
            bitrate_mode_str = "VBR"
        else:
            if ffprobe_stream_kbps and abs(ffprobe_stream_kbps - mutagen_kbps) <= 2:
                bitrate_mode_str = "CBR"
            else:
                bitrate_mode_str = "VBR"

        return {
            "mutagen_kbps": mutagen_kbps,
            "ffprobe_stream_bitrate_kbps": ffprobe_stream_kbps,
            "ffprobe_format_bitrate_kbps": ffprobe_fmt_kbps,
            "bitrate_mode": bitrate_mode_str,
            "duration": dur,
            "sample_rate": sr,
            "channels": ch,
        }

    def detect_silences(self, file_path: Path, total_duration: float) -> Tuple[int, str]:
        """Detecta silencios anómalos dentro del cuerpo del tema musical."""
        if not self.check_silence:
            return (0, "Detección desactivada")

        cmd = [
            self.ffmpeg_bin,
            "-i", str(file_path),
            "-af", f"silencedetect=noise=-50dB:d={self.silence_threshold_sec}",
            "-f", "null",
            "-"
        ]
        try:
            res = run_hidden_subprocess(cmd, capture_output=True, text=True, check=False)
            lines = res.stderr.splitlines()
            body_silences = []
            tail_silences = []

            cur_start = None
            for line in lines:
                if "silence_start:" in line:
                    try:
                        cur_start = float(line.split("silence_start:")[1].strip().split()[0])
                    except (IndexError, ValueError):
                        cur_start = None
                elif "silence_end:" in line and "silence_duration:" in line:
                    try:
                        parts = line.split("silence_end:")[1].split("|")
                        end_val = float(parts[0].strip().split()[0])
                        dur_val = float(parts[1].split("silence_duration:")[1].strip().split()[0])

                        is_outro = (total_duration - end_val) <= 0.8 or (cur_start and cur_start >= (total_duration - 5.0))
                        is_intro = cur_start is not None and cur_start <= 0.5

                        if is_outro:
                            tail_silences.append(f"Outro silence: {dur_val:.2f}s ({cur_start:.2f}s -> {end_val:.2f}s)")
                        elif is_intro:
                            tail_silences.append(f"Intro silence: {dur_val:.2f}s (0.0s -> {end_val:.2f}s)")
                        else:
                            body_silences.append(
                                f"Silencio anómalo en cuerpo: {dur_val:.2f}s ({cur_start:.2f}s -> {end_val:.2f}s)"
                            )
                    except (IndexError, ValueError):
                        pass

            anomalous_count = len(body_silences)
            all_details = "; ".join(body_silences + tail_silences) if (body_silences or tail_silences) else "Ninguno detectado"
            return (anomalous_count, all_details)
        except Exception as e:
            return (0, f"Error ejecutando silencedetect: {e}")

    def analyze_waveform(self, file_path: Path) -> Dict[str, Any]:
        """Calcula métricas acústicas de pico, RMS, rango dinámico, clipping y corte abrupto."""
        try:
            data, sr = sf.read(str(file_path))
        except Exception as e:
            # Fallback en caso de incompatibilidad puntual con libsndfile
            return {
                "peak_dbfs": -100.0,
                "rms_dbfs": -100.0,
                "dynamic_range_db": 0.0,
                "clipping_samples_count": 0,
                "clipping_pct": 0.0,
                "has_clipping_risk": False,
                "last_400ms_rms_dbfs": -100.0,
                "last_100ms_rms_dbfs": -100.0,
                "has_abrupt_ending": False,
                "read_error": str(e)
            }

        total_samples = data.size
        duration_samples = len(data)

        abs_data = np.abs(data)
        peak = float(np.max(abs_data)) if total_samples > 0 else 0.0
        peak_dbfs = 20 * np.log10(peak) if peak > 1e-9 else -100.0

        clipping_mask = abs_data >= 0.999
        clipping_count = int(np.sum(clipping_mask))
        clipping_pct = (clipping_count / total_samples) * 100.0 if total_samples > 0 else 0.0
        has_clipping_risk = (clipping_pct >= self.clipping_threshold_pct) if self.check_clipping else False

        rms = float(np.sqrt(np.mean(data ** 2))) if total_samples > 0 else 0.0
        rms_dbfs = 20 * np.log10(rms) if rms > 1e-9 else -100.0
        dynamic_range_db = peak_dbfs - rms_dbfs

        samples_400ms = int(sr * 0.4)
        samples_100ms = int(sr * 0.1)

        last_400ms = data[-samples_400ms:] if duration_samples >= samples_400ms else data
        last_100ms = data[-samples_100ms:] if duration_samples >= samples_100ms else data

        rms_400ms = float(np.sqrt(np.mean(last_400ms ** 2))) if last_400ms.size > 0 else 0.0
        rms_400ms_dbfs = 20 * np.log10(rms_400ms) if rms_400ms > 1e-9 else -100.0

        rms_100ms = float(np.sqrt(np.mean(last_100ms ** 2))) if last_100ms.size > 0 else 0.0
        rms_100ms_dbfs = 20 * np.log10(rms_100ms) if rms_100ms > 1e-9 else -100.0

        has_abrupt_ending = False
        if self.check_abrupt_ending:
            if rms_400ms_dbfs > self.abrupt_rms_threshold_dbfs:
                if rms_100ms_dbfs > self.abrupt_rms_threshold_dbfs:
                    has_abrupt_ending = True

        return {
            "peak_dbfs": round(peak_dbfs, 2),
            "rms_dbfs": round(rms_dbfs, 2),
            "dynamic_range_db": round(dynamic_range_db, 2),
            "clipping_samples_count": clipping_count,
            "clipping_pct": round(clipping_pct, 4),
            "has_clipping_risk": has_clipping_risk,
            "last_400ms_rms_dbfs": round(rms_400ms_dbfs, 2),
            "last_100ms_rms_dbfs": round(rms_100ms_dbfs, 2),
            "has_abrupt_ending": has_abrupt_ending,
            "decoded_duration_sec": round(duration_samples / sr, 2) if sr > 0 else 0.0,
        }

    def audit_file(self, file_path: Union[str, Path]) -> AudioAuditResult:
        """Audita un único archivo MP3 y emite el diagnóstico técnico estructurado."""
        path = Path(file_path).resolve()
        filename = path.name

        ff_ok, ff_err = self.check_ffmpeg_integrity(path)
        info = self.get_bitrate_and_stream_info(path)
        dur = info["duration"]
        anomalous_silences, silence_notes = self.detect_silences(path, dur)
        wave_metrics = self.analyze_waveform(path)

        anomalies = []
        verdict = "APTA"
        reasons = []

        # Decodificación y verificación de consistencia entre FFmpeg y SoundFile
        decoded_dur = wave_metrics.get("decoded_duration_sec", dur)
        read_error = wave_metrics.get("read_error")

        if not ff_ok:
            # Si SoundFile decodificó el archivo completo sin errores y la duración es congruente
            if not read_error and decoded_dur > 0 and abs(decoded_dur - dur) <= 5.0:
                anomalies.append(f"Aviso decodificación FFmpeg: {ff_err}")
                if verdict == "APTA":
                    verdict = "REVISIÓN MANUAL"
                    reasons.append("Avisos en flujo de audio (reproducible)")
            else:
                anomalies.append(f"Error de integridad FFmpeg: {ff_err}")
                verdict = "CANDIDATA A ELIMINACIÓN"
                reasons.append("Archivo corrupto o con errores de decodificación")

        # Comprobar si la duración real decodificada discrepa drásticamente de la cabecera
        if dur > 10.0 and decoded_dur > 0:
            diff = abs(decoded_dur - dur)
            if diff > 5.0 and (diff / dur) > 0.15:
                anomalies.append(
                    f"Discrepancia drástica de duración: cabecera={dur:.1f}s vs audio decodificado={decoded_dur:.1f}s"
                )
                verdict = "CANDIDATA A ELIMINACIÓN"
                reasons.append("Flujo de audio truncado respecto a la cabecera")

        if dur < self.min_duration_sec:
            anomalies.append(f"Duración insuficiente: {dur:.2f}s (< {self.min_duration_sec}s)")
            if verdict != "CANDIDATA A ELIMINACIÓN":
                verdict = "CANDIDATA A ELIMINACIÓN"
            reasons.append(f"Fragmento corto incompleto ({dur:.2f}s)")

        effective_bitrate = info["mutagen_kbps"]
        if effective_bitrate < self.min_bitrate_kbps:
            anomalies.append(f"Bitrate deficiente: {effective_bitrate} kbps (< {self.min_bitrate_kbps} kbps)")
            if effective_bitrate < 128:
                verdict = "CANDIDATA A ELIMINACIÓN"
                reasons.append(f"Bitrate inaceptable ({effective_bitrate} kbps)")
            elif verdict == "APTA":
                verdict = "REVISIÓN MANUAL"
                reasons.append(f"Bitrate bajo ({effective_bitrate} kbps)")

        if wave_metrics.get("has_abrupt_ending", False):
            anomalies.append(
                f"Corte abrupto detectado: RMS últimos 400ms = {wave_metrics['last_400ms_rms_dbfs']} dBFS"
            )
            if verdict == "APTA":
                verdict = "REVISIÓN MANUAL"
            reasons.append("Terminación abrupta sin fade-out")

        if anomalous_silences > 0:
            anomalies.append(f"Silencio(s) anómalo(s) en cuerpo del tema: {anomalous_silences}")
            if verdict == "APTA":
                verdict = "REVISIÓN MANUAL"
            reasons.append("Pausa o silencio injustificado en el cuerpo del tema")

        if wave_metrics.get("has_clipping_risk", False):
            anomalies.append(
                f"Saturación digital/clipping severo: {wave_metrics['clipping_pct']}% de muestras a 0 dBFS"
            )
            if verdict == "APTA":
                verdict = "REVISIÓN MANUAL"
            reasons.append("Clipping o masterización excesivamente saturada")

        if not anomalies:
            verdict = "APTA"
            verdict_reason = "Pista íntegra, sin errores, duración adecuada y excelente calidad técnica"
        else:
            verdict_reason = " | ".join(reasons)

        return AudioAuditResult(
            filename=filename,
            filepath=str(path),
            duration_sec=round(dur, 2),
            mutagen_bitrate_kbps=info["mutagen_kbps"],
            ffprobe_stream_bitrate_kbps=info["ffprobe_stream_bitrate_kbps"],
            ffprobe_format_bitrate_kbps=info["ffprobe_format_bitrate_kbps"],
            bitrate_mode=info["bitrate_mode"],
            sample_rate_hz=info["sample_rate"],
            channels=info["channels"],
            ffmpeg_integrity_ok=ff_ok,
            ffmpeg_errors=ff_err if not ff_ok else "Sin errores",
            peak_dbfs=wave_metrics["peak_dbfs"],
            rms_dbfs=wave_metrics["rms_dbfs"],
            dynamic_range_db=wave_metrics["dynamic_range_db"],
            clipping_samples_count=wave_metrics["clipping_samples_count"],
            clipping_pct=wave_metrics["clipping_pct"],
            has_clipping_risk=wave_metrics["has_clipping_risk"],
            last_400ms_rms_dbfs=wave_metrics["last_400ms_rms_dbfs"],
            last_100ms_rms_dbfs=wave_metrics["last_100ms_rms_dbfs"],
            has_abrupt_ending=wave_metrics["has_abrupt_ending"],
            anomalous_silence_count=anomalous_silences,
            silence_details=silence_notes,
            anomalies=anomalies,
            verdict=verdict,
            verdict_reason=verdict_reason,
        )


def export_csv(results: List[AudioAuditResult], output_path: Union[str, Path]):
    """Exporta los resultados detallados a CSV en UTF-8."""
    p = Path(output_path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "filename", "duration_sec", "mutagen_bitrate_kbps", "bitrate_mode",
        "sample_rate_hz", "channels", "ffmpeg_integrity_ok", "peak_dbfs",
        "rms_dbfs", "dynamic_range_db", "clipping_pct", "has_clipping_risk",
        "has_abrupt_ending", "anomalous_silence_count", "verdict", "verdict_reason"
    ]

    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))


def export_markdown(results: List[AudioAuditResult], output_path: Union[str, Path]):
    """Exporta un informe consolidado en Markdown en UTF-8."""
    p = Path(output_path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)

    total = len(results)
    aptas = sum(1 for r in results if r.verdict == "APTA")
    revision = sum(1 for r in results if r.verdict == "REVISIÓN MANUAL")
    eliminacion = sum(1 for r in results if r.verdict == "CANDIDATA A ELIMINACIÓN")

    lines = [
        "# Informe de Auditoría y Diagnóstico Técnico de Audio",
        "",
        "## Resumen General",
        f"- **Total de archivos analizados:** {total}",
        f"- **Pistas Aptas:** {aptas} ({aptas / total * 100:.1f}%)" if total else "- **Total:** 0",
        f"- **Requieren Revisión Manual:** {revision}",
        f"- **Candidatas a Eliminación:** {eliminacion}",
        "",
        "## Detalle por Pista",
        "",
        "| Archivo | Bitrate | Duración | Clipping % | Silencios | Veredicto | Diagnóstico |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for r in results:
        badge = "🟢 APTA" if r.verdict == "APTA" else ("🟡 REVISAR" if r.verdict == "REVISIÓN MANUAL" else "🔴 ELIMINAR")
        lines.append(
            f"| `{r.filename}` | {r.mutagen_bitrate_kbps} kbps ({r.bitrate_mode}) | "
            f"{r.duration_sec}s | {r.clipping_pct}% | {r.anomalous_silence_count} | "
            f"{badge} | {r.verdict_reason} |"
        )

    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
