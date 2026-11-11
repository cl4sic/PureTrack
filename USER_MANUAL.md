# AudioMaster Suite - User Manual

**AudioMaster** is an advanced, professional desktop audio engineering and metadata normalization suite built with Python, PySide6 (Qt 6), and modern C/Audio analysis engines (FFmpeg, Mutagen, Chromaprint, SoundFile, NumPy). Designed with an AIMP-inspired high-contrast dark aesthetic, it empowers DJs, audio curators, music producers, and audiophiles to audit, repair, enrich, and safely organize their music libraries across Windows and Linux.

---

## Table of Contents
1. [Overview & Key Features](#1-overview--key-features)
2. [User Interface Guide](#2-user-interface-guide)
   - [Top Bar & Drag-and-Drop](#top-bar--drag-and-drop)
   - [Tracks Table (Left Panel)](#tracks-table-left-panel)
   - [Inspector Panel (Right Panel)](#inspector-panel-right-panel)
   - [Pattern Builder & Dynamic Tokens](#pattern-builder--dynamic-tokens)
   - [Telemetry & Dual Progress Bar (Bottom Panel)](#telemetry--dual-progress-bar-bottom-panel)
3. [Core Capabilities & Workflows](#3-core-capabilities--workflows)
   - [Phase 1: Technical Acoustic Audit](#phase-1-technical-acoustic-audit)
   - [Phase 2: Metadata Resolution & Live Projection](#phase-2-metadata-resolution--live-projection)
   - [Phase 3: Safe Disk Execution & Dry-Run](#phase-3-safe-disk-execution--dry-run)
   - [Phase 4: Instant 100% Reversible Rollback](#phase-4-instant-100-reversible-rollback)
4. [Customization & Presets](#4-customization--presets)
5. [Windows & Linux Distribution](#5-windows--linux-distribution)
6. [Troubleshooting & FAQ](#6-troubleshooting--faq)

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
- **Interactive Pattern Builder:** Dynamic string interpolation with real-time preview on a sample track while typing.
- **Strict Windows NTFS Sanitation:** Replaces forbidden characters (`\ / : * ? " < > |`), handles DOS device names (`CON`, `PRN`, `AUX`, `NUL`), prevents trailing dots/spaces (`WinError 123`), and supports extended-length paths (`\\?\`).
- **Transactional Safety:** Generates a structured JSON log (`rename_log.json`) *before* touching files, ensuring 100% reversible rollbacks.

---

## 2. User Interface Guide

### Top Bar & Drag-and-Drop
- **Source Directory Input:** Shows the active music folder. You can type an absolute path or click **Examinar...** to browse your filesystem.
- **Drag-and-Drop Support:** Drag any folder or selection of `.mp3` files directly into the window from your file manager (Dolphin, Nautilus, COSMIC Files, Windows Explorer). AudioMaster automatically parses and populates the table.
- **Recargar (Reload):** Refreshes the track list from the current folder.
- **Tema (Theme Toggle):** Instantly switches the UI accent color between **Amber** (`#ff9800`) and **Cyan** (`#00b4d8`).

### Tracks Table (Left Panel)
- **Estado (Quality Badge):**
  - <span style="color:#81c784;">● APTA (Green):</span> Clean, uncorrupted, optimal bitrate and dynamic range.
  - <span style="color:#ffd54f;">▲ REVISAR (Yellow):</span> Minor warning (e.g., lower bitrate, abrupt ending, or in-track silence).
  - <span style="color:#e57373;">✖ ELIMINAR (Red):</span> Corrupt audio stream, incomplete duration, or severe clipping.
  - <span style="color:#b0bec5;">○ PENDIENTE (Gray):</span> Track loaded, awaiting analysis.
  - <span style="color:#90e0ef;">✔ APLICADO (Cyan):</span> Tags written and filename safely updated on disk.
- **Columns:**
  - `Original Filename`
  - `Projected Filename` (dynamic preview according to active pattern)
  - `Bitrate` (e.g., `320 kbps (CBR)`)
  - `Duration` (`mm:ss`)
  - `Clipping %` (percentage of digital samples at 0 dBFS)
  - `Action / Verdict` (human-readable diagnostic reason)
- **Right-Click Context Menu:**
  - *Inspeccionar detalles técnicos:* Opens a modal with comprehensive waveform stats, FFmpeg status, and ID3 tags.
  - *Editar manualmente nombre proyectado:* Override the projected filename for a specific track.
  - *Excluir del lote / Re-incluir:* Temporarily ignore individual tracks during batch operations.

### Inspector Panel (Right Panel)
Can be collapsed or expanded anytime via the **Ocultar Ajustes ▶** / **Mostrar Ajustes ◀** button.
- **Audit Criteria & Thresholds:**
  - Checkbox: *Detectar Clipping / Saturación digital (> 0 dBFS)*
  - Checkbox: *Detectar Silencios anómalos (> 3.0s en cuerpo)*
  - Checkbox: *Detectar Corte Abrupto final (sin fade-out)*
  - Slider: *Bitrate mínimo aceptable* (Range: 128 to 320 kbps)
  - Slider: *Duración mínima de pista* (Range: 10 to 120 seconds)
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

- **Presets:** Quick selector containing standard industry presets:
  - *Estándar EDM / Pop:* `{artist}{feat} - {title}{remix}`
  - *Estricto Artista - Título:* `{artist} - {title}`
  - *Álbum y Año:* `{year} - {album} - {artist} - {title}{remix}`
  - *DJ Extended / Remix:* `{artist}{feat} - {title} ({remix})`

### Telemetry & Dual Progress Bar (Bottom Panel)
- **Track Progress Bar:** Shows the individual processing stage of the current song (FFmpeg decode $\rightarrow$ Stream analysis $\rightarrow$ Waveform & clipping $\rightarrow$ Complete).
- **Global Batch Progress Bar:** Shows overall queue completion percentage, items completed, items remaining, processing speed (files per second), and estimated time to arrival (**ETA**).
- **Execution Flow Controls:**
  - **Pausar / Reanudar:** Safely halts the worker thread without crashing or leaving half-written files.
  - **Cancelar:** Gracefully terminates the running batch and restores idle controls.
- **Compact Log Console:** Real-time log terminal with color-coded severity levels (`[INFO]`, `[SUCCESS]`, `[WARNING]`, `[ERROR]`). Can be collapsed or expanded via the **Consola ▼** button.

---

## 3. Core Capabilities & Workflows

### Phase 1: Technical Acoustic Audit
1. Load tracks via Drag & Drop or the **Examinar...** button.
2. Click **Auditar Biblioteca**.
3. AudioMaster analyzes every track in the background:
   - Verifies MP3 stream headers with FFmpeg.
   - Measures digital clipping and dynamic range.
   - Scans for ungraceful cuts and silences.
4. Each row updates its badge immediately upon completion.

### Phase 2: Metadata Resolution & Live Projection
1. Adjust your desired naming pattern in the **Pattern Builder**.
2. Click **Simular (Dry-Run)**.
3. AudioMaster queries the local persistent SQLite cache (`output/metadata_cache.db`), matches canonical catalogs, calculates Chromaprint fingerprints, and populates the **Nombre Proyectado** column.
4. Review the projected names before committing any changes.

### Phase 3: Safe Disk Execution
1. Click **Aplicar en Disco**.
2. A confirmation prompt displays the total number of files to modify.
3. AudioMaster:
   - Writes the transaction manifest to `output/rename_log.json`.
   - Writes normalized ID3v2.3 tags with UTF-8 encoding (preserving embedded artwork).
   - Safely renames the files on disk using Windows NTFS sanitization and extended-length path compatibility.
   - Validates post-write integrity with FFmpeg.

### Phase 4: Instant 100% Reversible Rollback
If you ever want to revert all changes:
1. Click **Deshacer (Rollback)**.
2. Confirm the prompt.
3. AudioMaster reads `output/rename_log.json` and restores all original filenames and ID3 tags.

---

## 4. Customization & Presets
Configuration is saved automatically to `config.json` in UTF-8 format:
- On Linux: `~/.config/AudioMaster/config.json` (with local portable fallback).
- On Windows: `%APPDATA%\AudioMaster\config.json` (or `./config.json` next to the executable).

---

## 5. Windows & Linux Distribution

### Running on Linux
```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Run AudioMaster GUI
python app.py
```

### Building Standalone Linux Binary
```bash
python package/build_release.py --mode onedir
# Binary generated in: dist/AudioMaster/AudioMaster
```

### Running on Windows
Download `AudioMaster_Windows.zip`, extract it anywhere, and double-click:
- **`iniciar_AudioMaster.bat`**: 1-click launcher.
- Or compile a standalone native `.exe` by double-clicking **`compilar_exe_en_windows.bat`**.

---

## 6. Troubleshooting & FAQ

**Q: Why were some icons showing up as empty squares (`▯`) on Linux?**  
A: Certain Linux desktop environments (such as COSMIC DE or minimal window managers without `noto-fonts-emoji`) do not map Unicode emoji glyphs by default. AudioMaster uses clean Qt standard vector icons and universal typography to guarantee crisp rendering on all platforms.

**Q: Does AudioMaster re-encode or compress my audio?**  
A: **No.** AudioMaster performs lossless metadata tagging and filesystem renaming. The audio stream itself is never recompressed or degraded.

**Q: Are existing album covers preserved?**  
A: **Yes.** AudioMaster specifically preserves all existing `APIC` (Attached Picture) frames when updating ID3v2 tags.
