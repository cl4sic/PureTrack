# PureTrack Suite

[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-blue.svg)](https://github.com)
[![Framework](https://img.shields.io/badge/GUI-PySide6%20%28Qt%206%29-brightgreen.svg)](https://www.qt.io/)
[![Engine](https://img.shields.io/badge/Audio-FFmpeg%20%7C%20Mutagen%20%7C%20Chromaprint-orange.svg)](https://ffmpeg.org)
[![Theme](https://img.shields.io/badge/Theme-AIMP%20Dark-amber.svg)](https://www.aimp.ru)
[![i18n](https://img.shields.io/badge/i18n-Auto%20%7C%20ES%20%7C%20EN-cyan.svg)](locales/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

*Read this documentation in other languages:* [Español (README_ES.md)](README_ES.md) | [Manual de Usuario en Español (MANUAL_USUARIO.md)](MANUAL_USUARIO.md) | [Full User Manual in English (USER_MANUAL.md)](USER_MANUAL.md).

---

## Overview

**PureTrack** is an advanced, professional desktop audio engineering and metadata normalization suite built with **Python**, **PySide6 (Qt 6)**, and modern audio analysis engines (**FFmpeg**, **Mutagen**, **Chromaprint**, **SoundFile**, **NumPy**). Designed with a sleek, high-contrast dark aesthetic inspired by **AIMP**, it empowers DJs, audio curators, music producers, and audiophiles to audit, repair, enrich, and safely organize their music libraries across **Windows and Linux**.

---

## Downloads (GitHub Releases)

For end users, standalone single-file executables (`--onefile`) are published on every release under the **[Releases](../../releases)** tab:
- **Windows x64:** `PureTrack-Windows-x64.exe` (Standalone portable single `.exe` with embedded FFmpeg & Chromaprint).
- **Linux x64:** `PureTrack-Linux-x64` (Standalone ELF executable).

No external dependencies or console scripts are required; simply download and run.

---

## Key Features

- **Professional Multi-Language System (i18n):** Native internationalization with automatic OS system language detection (`Auto`). Supports hot live language switching between **Español** and **English** across all UI controls, badges, inspector panels, context menus, and dialogs without restarting.
- **Dedicated High-Resolution Branding:** Distinctive high-resolution acoustic vinyl record + ID3 tag icon (`gui/assets/icon.png` 1024x1024 with 100% transparent RGBA background, and `gui/assets/icon.ico` multi-resolution 16–256px) integrated directly into the window manager and Windows taskbar (`AppUserModelID`).
- **Non-Blocking Multithreaded Concurrency:** Powered by dedicated `QThread` workers with `QMutex` and `QWaitCondition` synchronization. Audit waveform metrics, calculate acoustic fingerprints, query local metadata caches, and apply disk transactions without ever freezing the UI. Supports live **Pause**, **Resume**, and **Cancel**.
- **AIMP Dark Aesthetics:** Charcoal background (`#18191c`), card panels (`#222327`), subtle borders (`#2e3036`), and dual accent themes (**Classic AIMP Amber `#ff9800`** and **Modern Tech Cyan `#00b4d8`**), switchable in real time.
- **Deep Acoustic Quality Diagnostics:**
  - True stream bitrates (discriminates between CBR and VBR via Mutagen and FFprobe).
  - Digital clipping and saturation detection ($\ge 0\text{ dBFS}$ / $\ge 0.999$ full-scale samples).
  - Dynamic range and total RMS calculations.
  - Abrupt ending detection (analyzing energy in the final 400 ms and 100 ms to detect cutoff tracks).
  - In-track anomalous silence detection using FFmpeg `silencedetect` (ignores natural intros/outros).
  - Robust corruption analysis with benign packet warning suppression (Xing, LAME, cover-art MJPEG/PNG streams).
- **Interactive Pattern Builder:** Text entry with clickable dynamic token chips (`{artist}`, `{feat}`, `{title}`, `{remix}`, `{album}`, `{year}`, `{genre}`) and live real-time preview on a sample track while typing.
- **Custom Naming & Manual Overrides:** Ability to manually override projected filenames before applying changes to disk, prefilling current projected or original names and guaranteeing persistence without pattern overwrites.
- **Configurable ID3v2 Mapping:** Define custom token mappings for ID3v2.3 tags (`TIT2`, `TPE1`, `TALB`, `TPE2`, `TCON`, `TDRC`) with explicit UTF-8 encoding while preserving existing album artwork (`APIC`).
- **Strict Windows NTFS Sanitation:** Cleanses forbidden characters (`\ / : * ? " < > |`), handles DOS device names (`CON`, `PRN`, `AUX`, `NUL`), prevents trailing dots/spaces (`WinError 123`), and supports extended-length paths (`\\?\`).
- **Hidden Subprocess Windows:** All external binary calls (`ffmpeg`, `ffprobe`, `fpcalc`) run with `CREATE_NO_WINDOW` and hidden startup flags on Windows, preventing CMD black popups.
- **100% Reversible Rollback:** Pre-writes every operation into `output/rename_log.json` before touching disk, allowing instantaneous 1-click rollback of filenames and tags.

---

## Project Architecture

```
PureTrack/
├── .github/
│   └── workflows/
│       └── release.yml    # Automated CI/CD release workflow for Windows & Linux
├── core/
│   ├── auditor.py         # Technical acoustic analysis (FFmpeg, mutagen, clipping, silences, cuts)
│   ├── common_utils.py    # Autonomous binary locator, long paths (\\?\), NTFS sanitization, hidden subprocesses
│   ├── config_manager.py  # Presets, patterns, and thresholds saved to config.json
│   ├── i18n.py            # TranslationManager singleton, locale detection & live hot-reload
│   ├── resolver.py        # Metadata resolution, MusicBrainz/catalogs, and persistent SQLite cache
│   └── tagger.py          # Mutagen ID3v2 UTF-8, NTFS sanitization, atomic transactions, rollback
├── gui/
│   ├── assets/
│   │   ├── icon.ico       # Windows multi-resolution icon (16x16 up to 256x256)
│   │   └── icon.png       # Master 1024x1024 high-res transparent application icon
│   ├── main_window.py     # Main window, Drag & Drop, resizable splitter, context menus, i18n switcher
│   ├── widgets/
│   │   ├── audio_badge.py      # Quality status badges (Localized: APTA/OK, ALERTA/WARNING, ERROR, EXCLUIDA/EXCLUDED)
│   │   ├── pattern_builder.py  # Interactive token chips, presets manager, live preview
│   │   ├── inspector_panel.py  # Collapsible panel with audit toggles, sliders, and ID3 mapping
│   │   └── progress_panel.py   # Dual progress bar (track/batch), ETA, console, and action buttons
│   ├── workers.py         # Concurrent QThread workers (AuditWorker, EnrichWorker, ApplyWorker, RollbackWorker)
│   └── styles/
│       ├── aimp_dark.qss       # High-contrast AIMP Dark QSS stylesheet
│       └── theme_loader.py     # Dynamic Amber/Cyan palette switcher
├── locales/
│   ├── en.json            # English translations
│   └── es.json            # Spanish translations
├── bin/
│   └── README.md          # Guide for local audio binaries (ffmpeg, ffprobe, fpcalc)
├── package/
│   └── build_release.py   # Standalone PyInstaller release builder for PureTrack (--onefile)
├── app.py                 # Application entry point
├── requirements.txt       # Dependencies
├── LICENSE                # GNU General Public License v3.0 (GPLv3)
├── USER_MANUAL.md         # Detailed user manual (English)
├── MANUAL_USUARIO.md      # Detailed user manual (Spanish)
└── test_suite.py          # Comprehensive test suite
```

---

## Quick Start Guide

### Running from Source on Linux
```bash
# 1. Clone or enter the repository
cd music-sanitizer-Cl4sic

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Launch PureTrack
python app.py
```

### Building Standalone Executables Locally (PyInstaller)
```bash
# Standalone single-file binary (--onefile)
python package/build_release.py --mode onefile
```

---

## Quality Verdict Badges

| Badge | Status (ES / EN) | Description |
| :---: | :--- | :--- |
| <span style="color:#81c784;">●</span> **APTA / OK** | **Fit / Optimal** | Zero FFmpeg decoding errors, optimal bitrate ($\ge 190\text{ kbps}$), clean waveform, no abrupt ending. |
| <span style="color:#ffd54f;">▲</span> **ALERTA / WARNING** | **Review Needed** | Low bitrate ($< 190\text{ kbps}$), in-track anomalous silence, or ungraceful cut-off at the end. |
| <span style="color:#e57373;">✖</span> **ERROR** | **Critical / Corrupt** | FFmpeg stream decoding failure, truncated duration ($< 60\text{s}$), or unrecoverable clipping. |
| <span style="color:#888888;">⊘</span> **EXCLUIDA / EXCLUDED** | **Excluded** | Track excluded from batch processing via right-click contextual toggle. |
| <span style="color:#90e0ef;">✔</span> **APLICADO / APPLIED** | **Updated on Disk** | Successfully tagged with ID3v2 UTF-8 metadata and safely renamed. |

---

## Running the Automated Test Suite

To verify cross-platform binary resolution, NTFS sanitization, QThread concurrency, i18n translations, and metadata consistency:
```bash
QT_QPA_PLATFORM=offscreen python test_suite.py
```

---

## License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**. See the [LICENSE](LICENSE) file for details.
