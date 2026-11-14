# PureTrack Suite - User Manual

**PureTrack** is an advanced, professional desktop audio engineering and metadata normalization suite built with Python, PySide6 (Qt 6), and modern C/Audio analysis engines (FFmpeg, Mutagen, Chromaprint, SoundFile, NumPy). Designed with an AIMP-inspired high-contrast dark aesthetic, native internationalization (i18n), and a custom acoustic vector icon, it empowers DJs, audio curators, music producers, and audiophiles to audit, repair, enrich, and safely organize their music libraries across Windows and Linux.

---

## Table of Contents
1. [Overview & Key Features](#1-overview--key-features)
2. [User Interface Guide](#2-user-interface-guide)
   - [Top Bar: Language Selector, Drag-and-Drop & Theme](#top-bar-language-selector-drag-and-drop--theme)
   - [Tracks Table (Left Panel)](#tracks-table-left-panel)
   - [Inspector Panel (Right Panel)](#inspector-panel-right-panel)
   - [Pattern Builder & Dynamic Tokens](#pattern-builder--dynamic-tokens)
   - [Telemetry & Dual Progress Bar (Bottom Panel)](#telemetry--dual-progress-bar-bottom-panel)
3. [Core Capabilities & Workflows](#3-core-capabilities--workflows)
   - [Phase 1: Technical Acoustic Audit & Live Projection](#phase-1-technical-acoustic-audit--live-projection)
   - [Phase 2: Safe Disk Execution](#phase-2-safe-disk-execution)
   - [Phase 3: Instant 100% Reversible Rollback](#phase-3-instant-100-reversible-rollback)
4. [Multi-Language System (i18n) & Visual Identity](#4-multi-language-system-i18n--visual-identity)
5. [Customization & Presets](#5-customization--presets)
6. [Windows & Linux Distribution](#6-windows--linux-distribution)
7. [Troubleshooting & FAQ](#7-troubleshooting--faq)

---

## 1. Overview & Key Features

- **Non-Blocking Multithreaded Concurrency:** Powered by dedicated `QThread` workers. Decodes audio, executes FFmpeg integrity passes, computes Chromaprint fingerprints, and resolves online databases asynchronously without freezing the UI.
- **AIMP Dark Aesthetics:** Charcoal base (`#18191c`), card panels (`#222327`), subtle borders (`#2e3036`), and customizable dual accent palette (Classic AIMP Amber `#ff9800` or Modern Cyan `#00b4d8`).
- **Acoustic Diagnostic Engine:**
  - True stream bitrates (CBR/VBR discrimination via Mutagen and FFprobe).
  - Digital clipping and saturation detection ($\ge 0\text{ dBFS}$ / $\ge 0.999$ full-scale samples).
  - Dynamic range and total RMS calculations.
  - Abrupt ending detection (analyzing energy in the final 400 ms and 100 ms to detect tracks that cut off without a fade-out).
  - In-track anomalous silence detection (using FFmpeg's `silencedetect` while ignoring natural intro/outro silences).
- **Interactive Pattern Builder & Presets:** Dynamic string interpolation with real-time preview on a sample track while typing, plus a full preset manager to create, save, and delete user presets.
- **Strict Windows NTFS Sanitation:** Replaces forbidden characters (`\ / : * ? " < > |`), handles DOS device names (`CON`, `PRN`, `AUX`, `NUL`), prevents trailing dots/spaces (`WinError 123`), and supports extended-length paths (`\\?\`).
- **Hidden Windows Subprocesses:** Full suppression of CMD black console popups on Windows (`CREATE_NO_WINDOW` and hidden window flags) across all FFmpeg, FFprobe, and fpcalc calls.
- **Transactional Safety:** Generates a structured JSON log (`rename_log.json`) *before* touching files, ensuring 100% reversible rollbacks.

---

## 2. User Interface Guide

### Top Bar: Language Selector, Drag-and-Drop & Theme
- **Source Directory Input:** Shows the active music folder. You can type an absolute path or click **Examinar...** to browse your filesystem.
- **Drag-and-Drop Support:** Drag any folder or selection of `.mp3` files directly into the window from your file manager (Windows Explorer, Dolphin, Nautilus).
- **Language Selector (i18n):** Compact dropdown (`Auto (System)`, `Español`, `English`) that hot-switches the application language across all tables, headers, badges, and menus without restarting.
- **Recargar (Reload):** Refreshes the track list from the current folder.
- **Tema (Theme Toggle):** Instantly switches the UI accent color between **Amber** (`#ff9800`) and **Cyan** (`#00b4d8`).

### Tracks Table (Left Panel)
- **Status (Quality Badge):**
  - <span style="color:#81c784;">● APTA / OK (Green):</span> Clean, uncorrupted, optimal bitrate and dynamic range.
  - <span style="color:#ffd54f;">▲ ALERTA / WARNING (Yellow):</span> Minor warning (e.g., lower bitrate, abrupt ending, or in-track silence).
  - <span style="color:#e57373;">✖ ERROR (Red):</span> Corrupt audio stream, incomplete duration, or severe clipping.
  - <span style="color:#888888;">⊘ EXCLUIDA / EXCLUDED (Dark Gray):</span> Track excluded by the user from batch processing.
  - <span style="color:#b0bec5;">○ PENDIENTE / PENDING (Gray):</span> Track loaded, awaiting analysis.
  - <span style="color:#90e0ef;">✔ APLICADO / APPLIED (Cyan):</span> Tags written and filename safely updated on disk.
- **Columns:**
  - `Original Filename`
  - `Projected Filename` (dynamic preview according to active pattern)
  - `Bitrate` (e.g., `320 kbps (CBR)`)
  - `Duration` (`mm:ss`)
  - `Clipping %` (percentage of digital samples at 0 dBFS)
  - `Action / Verdict` (human-readable diagnostic reason)
- **Right-Click Context Menu:**
  - *Inspeccionar detalles técnicos:* Opens a modal with comprehensive waveform stats, FFmpeg status, and ID3 tags.
  - *Asignar nombre personalizado:* Override the projected filename for a specific track with smart prefill and disk persistence.
  - *Excluir del lote / Incluir en el lote:* Bidirectional toggle to selectively omit tracks from processing.
  - *Restablecer a patrón automático:* Reverts any manual name override back to the dynamic pattern.

### Inspector Panel (Right Panel)
Can be collapsed or expanded anytime via the **Ocultar Ajustes ▶** / **Mostrar Ajustes ◀** button.
- **Audit Criteria & Thresholds:**
  - Checkbox: *Clipping / Digital Saturation (> 0 dBFS)*
  - Checkbox: *Anomalous Silences (> 3.0s in body)*
  - Checkbox: *Abrupt Endings (without fade-out)*
  - Slider: *Minimum Acceptable Bitrate* (Range: 128 to 320 kbps)
  - Slider: *Minimum Track Duration* (Range: 10 to 120 seconds)
- **ID3v2 Tag Mapping:** Configure which dynamic token populates each tag:
  - `TIT2` (Title): `{title}{remix}`
  - `TPE1` (Lead / Contributing Artists): `{all_artists}`
  - `TALB` (Album): `{album}`
  - `TPE2` (Album Artist): `{album_artists}`
  - `TCON` (Genre): `{genre}`
  - `TDRC` (Release Year): `{year}`

### Pattern Builder & Dynamic Tokens
Click any token button to insert it at your cursor's position:
| Token | Description | Example |
| :--- | :--- | :--- |
| `{artist}` | Main artists separated by `&` | `Martin Garrix & DallasK` |
| `{feat}` | Featured artists prefixed with `feat.` | `feat. Sasha Alex Sloan` |
| `{guest}` | Guest artists prefixed with `&` | `& David Guetta` |
| `{title}` | Canonical track title | `Loop` |
| `{remix}` | Remix subtitle | `- Brooks Remix` |
| `{album}` | Official album or EP name | `Seven` |
| `{year}` | 4-digit release year | `2022` |
| `{genre}` | Primary musical genre | `Future Bounce` |
| `{all_artists}` | Comma-separated full lineup | `Martin Garrix, DallasK, Sasha Alex Sloan` |

- **Presets Manager:**
  - `+ Nuevo` button: Save current pattern as a new named preset.
  - `Guardar` button: Update the currently active preset with new changes.
  - `Borrar` button: Delete the selected preset.

### Telemetry & Dual Progress Bar (Bottom Panel)
- **Track Progress Bar:** Shows the individual processing stage of the current song.
- **Global Batch Progress Bar:** Shows overall queue completion percentage, items completed, items remaining, processing speed (files per second), and estimated time to arrival (**ETA**).
- **Execution Flow Controls:**
  - **Pausar / Reanudar:** Safely halts the worker thread without crashing or leaving half-written files.
  - **Cancelar:** Gracefully terminates the running batch and restores idle controls.
- **Compact Log Console:** Real-time log terminal with color-coded severity levels (`[INFO]`, `[SUCCESS]`, `[WARNING]`, `[ERROR]`). Can be collapsed or expanded via the **Consola ▼** button.

---

## 3. Core Capabilities & Workflows

### Phase 1: Technical Acoustic Audit & Live Projection
1. Load tracks via Drag & Drop or the **Examinar...** button.
2. Adjust your desired naming pattern in the **Pattern Builder** if you wish to customize it.
3. Click **Auditar Biblioteca**.
4. PureTrack analyzes every track in the background without console popup windows, verifying stream integrity, acoustic metrics, and automatically populating the **Nombre Proyectado** column with clean normalized filenames.
5. Each row updates its badge immediately upon completion.

### Phase 2: Safe Disk Execution
1. Review the projected names and customize any song manually if desired.
2. Click **Aplicar en Disco**.
3. A confirmation prompt displays the total number of files to modify.
4. PureTrack:
   - Writes the transaction manifest to `output/rename_log.json`.
   - Writes normalized ID3v2.3 tags with UTF-8 encoding (preserving embedded artwork).
   - Safely renames the files on disk using Windows NTFS sanitization, respecting custom name overrides.
   - Validates post-write integrity with FFmpeg.

### Phase 3: Instant 100% Reversible Rollback
If you ever want to revert all changes:
1. Click **Deshacer (Rollback)**.
2. Confirm the prompt.
3. PureTrack reads `output/rename_log.json` and restores all original filenames and ID3 tags.

---

## 4. Multi-Language System (i18n) & Visual Identity

- **Automatic Language Detection:** When set to `Auto`, PureTrack detects your operating system language via `QLocale`. Spanish systems automatically start in Spanish, while all other systems start in English.
- **Hot Language Switching:** You can change language on the fly (`Auto`, `Español`, `English`) from the top bar dropdown at any time. The entire UI updates immediately without needing to restart.
- **Cross-Platform Vector Icon:** PureTrack features a custom acoustic pulse and equalizer icon (`gui/assets/icon.png` and `gui/assets/icon.ico`) embedded into the binary and pinned to the Windows taskbar (`AppUserModelID`).

---

## 5. Customization & Presets
Configuration is saved automatically to `config.json` in UTF-8 format:
- On Linux: `~/.config/PureTrack/config.json` (with local portable fallback).
- On Windows: `%APPDATA%\PureTrack\config.json` (or `./config.json` next to the executable).

---

## 6. Windows & Linux Distribution

### Running on Linux
```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Run PureTrack GUI
python app.py
```

### Building Standalone Linux Binary
```bash
python package/build_release.py --mode onedir
# Binary generated in: dist/PureTrack/PureTrack
```

### Running on Windows
1. Download and extract `PureTrack_Windows.zip`.
2. Double-click **`compilar_exe_en_windows.bat`**:
   - Installs dependencies and PyInstaller in 1 click.
   - Generates the standalone executable in `dist\PureTrack\PureTrack.exe`.
   - Asks if you want to open PureTrack immediately.
3. For daily execution, double-click:
   - **`ejecutar_PureTrack.bat`** (or open `dist\PureTrack\PureTrack.exe` directly).

---

## 7. Troubleshooting & FAQ

**Q: Why don't black CMD console windows appear when auditing tracks on Windows?**  
A: PureTrack suppresses subprocess windows via `CREATE_NO_WINDOW` and hidden startup flags on all calls to FFmpeg, FFprobe, and fpcalc.

**Q: Does PureTrack re-encode or compress my audio?**  
A: **No.** PureTrack performs lossless metadata tagging and filesystem renaming. The audio stream itself is never recompressed or degraded.

**Q: Are existing album covers preserved?**  
A: **Yes.** PureTrack specifically preserves all existing `APIC` (Attached Picture) frames when updating ID3v2 tags.
