# AudioMaster Suite

[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-blue.svg)](https://github.com)
[![Framework](https://img.shields.io/badge/GUI-PySide6%20%28Qt%206%29-brightgreen.svg)](https://www.qt.io/)
[![Engine](https://img.shields.io/badge/Audio-FFmpeg%20%7C%20Mutagen%20%7C%20Chromaprint-orange.svg)](https://ffmpeg.org)
[![Theme](https://img.shields.io/badge/Theme-AIMP%20Dark-amber.svg)](https://www.aimp.ru)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

*Read this documentation in other languages:* [Español (README_ES.md)](README_ES.md) | [Manual de Usuario en Español (MANUAL_USUARIO.md)](MANUAL_USUARIO.md) | [Full User Manual in English (USER_MANUAL.md)](USER_MANUAL.md).

---

## Overview

**AudioMaster** is an advanced, professional desktop audio engineering and metadata normalization suite built with **Python**, **PySide6 (Qt 6)**, and modern audio analysis engines (**FFmpeg**, **Mutagen**, **Chromaprint**, **SoundFile**, **NumPy**). Designed with a sleek, high-contrast dark aesthetic inspired by **AIMP**, it empowers DJs, audio curators, music producers, and audiophiles to audit, repair, enrich, and safely organize their music libraries across **Windows and Linux**.

---

## Key Features

- **Non-Blocking Multithreaded Concurrency:** Powered by dedicated `QThread` workers with `QMutex` and `QWaitCondition` synchronization. Audit waveform metrics, calculate acoustic fingerprints, query local metadata caches, and apply disk transactions without ever freezing the UI. Supports live **Pause**, **Resume**, and **Cancel**.
- **AIMP Dark Aesthetics:** Charcoal background (`#18191c`), card panels (`#222327`), subtle borders (`#2e3036`), and dual accent themes (**Classic AIMP Amber `#ff9800`** and **Modern Tech Cyan `#00b4d8`**), switchable in real time.
- **Deep Acoustic Quality Diagnostics:**
  - True stream bitrates (discriminates between CBR and VBR via Mutagen and FFprobe).
  - Digital clipping and saturation detection ($\ge 0\text{ dBFS}$ / $\ge 0.999$ full-scale samples).
  - Dynamic range and total RMS calculations.
  - Abrupt ending detection (analyzing energy in the final 400 ms and 100 ms to detect cutoff tracks).
  - In-track anomalous silence detection using FFmpeg `silencedetect` (ignores natural intros/outros).
- **Interactive Pattern Builder:** Text entry with clickable dynamic token chips (`{artist}`, `{feat}`, `{title}`, `{remix}`, `{album}`, `{year}`, `{genre}`) and live real-time preview on a sample track while typing.
- **Configurable ID3v2 Mapping:** Define custom token mappings for ID3v2.3 tags (`TIT2`, `TPE1`, `TALB`, `TPE2`, `TCON`, `TDRC`) with explicit UTF-8 encoding while preserving existing album artwork (`APIC`).
- **Strict Windows NTFS Sanitation:** Cleanses forbidden characters (`\ / : * ? " < > |`), handles DOS device names (`CON`, `PRN`, `AUX`, `NUL`), prevents trailing dots/spaces (`WinError 123`), and supports extended-length paths (`\\?\`).
- **100% Reversible Rollback:** Pre-writes every operation into `output/rename_log.json` before touching disk, allowing instantaneous 1-click rollback of filenames and tags.

---

## Project Architecture

```
AudioMaster/
├── core/
│   ├── auditor.py         # Technical acoustic analysis (FFmpeg, mutagen, clipping, silences, cuts)
│   ├── resolver.py        # Metadata resolution, MusicBrainz/catalogs, and persistent SQLite cache
│   ├── tagger.py          # Mutagen ID3v2 UTF-8, NTFS sanitization, atomic transactions, rollback
│   ├── config_manager.py  # Presets, patterns, and thresholds saved to config.json
│   └── common_utils.py    # Autonomous binary locator, long paths (\\?\), NTFS sanitization
├── gui/
│   ├── main_window.py     # Main window, Drag & Drop, resizable splitter, context menus
│   ├── widgets/
│   │   ├── audio_badge.py      # Quality status badges (Green: Apta, Yellow: Review, Red: Corrupt)
│   │   ├── pattern_builder.py  # Interactive token chips and live preview
│   │   ├── inspector_panel.py  # Collapsible panel with audit toggles, sliders, and ID3 mapping
│   │   └── progress_panel.py   # Dual progress bar (track/batch), ETA, console, and action buttons
│   ├── workers.py         # Concurrent QThread workers (AuditWorker, EnrichWorker, ApplyWorker, RollbackWorker)
│   └── styles/
│       ├── aimp_dark.qss       # High-contrast AIMP Dark QSS stylesheet
│       └── theme_loader.py     # Dynamic Amber/Cyan palette switcher
├── bin/                   # Portable external binaries (ffmpeg.exe, ffprobe.exe, fpcalc.exe)
├── package/
│   └── build_release.py   # Standalone PyInstaller release builder
├── app.py                 # Application entry point
├── requirements.txt       # Dependencies
├── USER_MANUAL.md         # Detailed user manual (English)
├── MANUAL_USUARIO.md      # Detailed user manual (Spanish)
└── test_suite.py          # Comprehensive test suite (11/11 tests passing)
```

---

## Quick Start Guide

### Running on Linux
```bash
# 1. Clone or enter the repository
cd music-sanitizer-Cl4sic

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Launch AudioMaster
python app.py
```

### Running on Windows (Portable 1-Click Package)
1. Download **`AudioMaster_Windows.zip`** from this repository.
2. Unzip the folder anywhere on your computer.
3. Double-click **`iniciar_AudioMaster.bat`** (or `run_AudioMaster.bat`).
   *External binaries (`ffmpeg.exe`, `ffprobe.exe`, `fpcalc.exe`) are already pre-bundled in the `bin/` folder!*

---

## Building Standalone Executables (PyInstaller)

### On Linux (Standalone ELF binary)
```bash
python package/build_release.py --mode onedir
# Distribution output created in: dist/AudioMaster/AudioMaster
```

### On Windows (Native .exe)
Simply double-click:
```cmd
compilar_exe_en_windows.bat
# Executable created in: dist\AudioMaster\AudioMaster.exe
```

---

## Quality Verdict Badges

| Badge | Status | Description |
| :---: | :--- | :--- |
| <span style="color:#81c784;">●</span> **APTA** | **Fit / Optimal** | Zero FFmpeg decoding errors, optimal bitrate ($\ge 190\text{ kbps}$), clean waveform, no abrupt ending. |
| <span style="color:#ffd54f;">▲</span> **REVISAR** | **Review Needed** | Low bitrate ($< 190\text{ kbps}$), in-track anomalous silence, or ungraceful cut-off at the end. |
| <span style="color:#e57373;">✖</span> **ELIMINAR** | **Critical / Corrupt** | FFmpeg stream decoding failure, truncated duration ($< 60\text{s}$), or unrecoverable clipping. |
| <span style="color:#90e0ef;">✔</span> **APLICADO** | **Updated on Disk** | Successfully tagged with ID3v2 UTF-8 metadata and safely renamed. |

---

## Running the Automated Test Suite

To verify cross-platform binary resolution, NTFS sanitization, QThread concurrency, and metadata consistency:
```bash
python test_suite.py
# Ran 11 tests in 0.530s -> OK
```

---

## Documentation

- **[Full User Manual in English (USER_MANUAL.md)](USER_MANUAL.md)**
- **[Manual de Usuario Completo en Español (MANUAL_USUARIO.md)](MANUAL_USUARIO.md)**
- **[Spanish README (README_ES.md)](README_ES.md)**
