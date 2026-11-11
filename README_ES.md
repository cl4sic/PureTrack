# AudioMaster Suite (Español)

[![Plataforma](https://img.shields.io/badge/Plataforma-Windows%20%7C%20Linux-blue.svg)](https://github.com)
[![Framework](https://img.shields.io/badge/GUI-PySide6%20%28Qt%206%29-brightgreen.svg)](https://www.qt.io/)
[![Motor](https://img.shields.io/badge/Audio-FFmpeg%20%7C%20Mutagen%20%7C%20Chromaprint-orange.svg)](https://ffmpeg.org)
[![Tema](https://img.shields.io/badge/Tema-AIMP%20Dark-amber.svg)](https://www.aimp.ru)
[![Licencia](https://img.shields.io/badge/Licencia-MIT-purple.svg)](LICENSE)

*Documentación en otros idiomas:* [English README (README.md)](README.md) | [Manual de Usuario en Español (MANUAL_USUARIO.md)](MANUAL_USUARIO.md) | [Full User Manual in English (USER_MANUAL.md)](USER_MANUAL.md).

---

## Descripción General

**AudioMaster** es una suite de escritorio profesional para la auditoría técnica acústica, normalización de metadatos y renombrado seguro de colecciones musicales MP3. Desarrollada con **Python**, **PySide6 (Qt 6)** y motores de análisis acústico en C/Audio (**FFmpeg**, **Mutagen**, **Chromaprint**, **SoundFile**, **NumPy**), ofrece una estética oscura de alto contraste inspirada en **AIMP** para DJs, curadores musicales, productores y audiófilos en **Windows y Linux**.

---

## Características Principales

- **Concurrencia Total con QThread:** La auditoría de ondas, cálculo de huellas Chromaprint, peticiones a catálogos y escrituras en disco se ejecutan en segundo plano mediante hilos sincronizados (`QMutex`, `QWaitCondition`). Permite **Pausar**, **Reanudar** y **Cancelar** en cualquier instante sin congelar la ventana.
- **Estética AIMP Dark:** Fondo carbón (`#18191c`), tarjetas y paneles `#222327`, bordes `#2e3036`, y conmutación en caliente entre **Ámbar Clásico** (`#ff9800`) y **Cian Tecnológico** (`#00b4d8`).
- **Diagnóstico Acústico Profundo:**
  - Bitrate exacto (discriminación precisa CBR y VBR vía Mutagen y FFprobe).
  - Detección de clipping y saturación digital ($\ge 0\text{ dBFS}$ / $\ge 0.999$).
  - Cálculo de rango dinámico y nivel RMS global.
  - Detección de cortes abruptos finales evaluando los últimos 400 ms y 100 ms de audio.
  - Detección de silencios anómalos en el cuerpo del tema mediante el filtro `silencedetect` de FFmpeg (ignorando silencios naturales en intro y outro).
- **Constructor de Patrones Interactivo:** Campo de texto editable acompañado de chips clickeables con tokens dinámicos (`{artist}`, `{feat}`, `{title}`, `{remix}`, `{album}`, `{year}`, `{genre}`) y previsualización en tiempo real con una canción de muestra.
- **Mapeo Personalizable ID3v2:** Asignación flexible de marcos ID3v2.3 (`TIT2`, `TPE1`, `TALB`, `TPE2`, `TCON`, `TDRC`) en UTF-8 explícito preservando las carátulas incrustadas (`APIC`).
- **Saneamiento Estricto para Windows NTFS:** Sustitución de caracteres prohibidos (`\ / : * ? " < > |`), protección contra nombres de dispositivos DOS (`CON`, `PRN`, `AUX`, `NUL`), eliminación de puntos y espacios finales (`WinError 123`) y compatibilidad con rutas largas (`\\?\`).
- **Rollback 100% Reversible:** Registro previo estructurado en `output/rename_log.json` antes de realizar cualquier cambio físico en el disco, permitiendo revertir nombres y tags con un solo clic.

---

## Arquitectura Modular del Proyecto

```
AudioMaster/
├── core/
│   ├── auditor.py         # Análisis técnico (FFmpeg, mutagen, clipping, silencios, cortes)
│   ├── resolver.py        # Resolución de metadatos, MusicBrainz y caché persistente SQLite
│   ├── tagger.py          # Mutagen ID3v2 UTF-8, saneamiento NTFS, transacciones y rollback
│   ├── config_manager.py  # Presets, patrones y umbrales guardados en config.json
│   └── common_utils.py    # Localizador autónomo de binarios, rutas largas (\\?\), saneamiento NTFS
├── gui/
│   ├── main_window.py     # Ventana principal, Drag & Drop, splitter, menús contextuales
│   ├── widgets/
│   │   ├── audio_badge.py      # Badges visuales de calidad (Verde: Apta, Amarillo: Revisar, Rojo: Eliminar)
│   │   ├── pattern_builder.py  # Chips interactivos y previsualización en vivo
│   │   ├── inspector_panel.py  # Panel colapsable con toggles de auditoría, sliders y mapeo ID3
│   │   └── progress_panel.py   # Barra de progreso dual (pista/lote), ETA, consola y botones de acción
│   ├── workers.py         # Workers concurrentes QThread (AuditWorker, EnrichWorker, ApplyWorker, RollbackWorker)
│   └── styles/
│       ├── aimp_dark.qss       # Hoja de estilos AIMP Dark en QSS
│       └── theme_loader.py     # Conmutador dinámico de paleta Ámbar/Cian
├── bin/                   # Binarios autónomos portables (ffmpeg.exe, ffprobe.exe, fpcalc.exe)
├── package/
│   └── build_release.py   # Compilador PyInstaller multiplataforma
├── app.py                 # Punto de entrada de la aplicación
├── requirements.txt       # Dependencias del proyecto
├── USER_MANUAL.md         # Manual de usuario en inglés
├── MANUAL_USUARIO.md      # Manual de usuario en español
└── test_suite.py          # Batería de pruebas automatizadas (11/11 tests superados)
```

---

## Guía de Inicio Rápido

### En Linux
```bash
# 1. Activar el entorno virtual
source .venv/bin/activate

# 2. Iniciar AudioMaster
python app.py
```

### En Windows (Paquete Portable en 1 Clic)
1. Descarga el archivo **`AudioMaster_Windows.zip`** de este repositorio.
2. Descomprímelo en cualquier carpeta de tu ordenador.
3. Haz doble clic en **`iniciar_AudioMaster.bat`**.
   *Los binarios externos (`ffmpeg.exe`, `ffprobe.exe`, `fpcalc.exe`) ya están preinstalados dentro de la carpeta `bin/`.*

---

## Compilación de Ejecutables Autónomos (PyInstaller)

### En Linux (Binario ELF independiente)
```bash
python package/build_release.py --mode onedir
# El ejecutable compilado se crea en: dist/AudioMaster/AudioMaster
```

### En Windows (Ejecutable .exe nativo)
Simplemente haz doble clic en:
```cmd
compilar_exe_en_windows.bat
# Ejecutable creado en: dist\AudioMaster\AudioMaster.exe
```

---

## Insignias de Calidad y Diagnóstico

| Insignia | Estado | Significado Técnico |
| :---: | :--- | :--- |
| <span style="color:#81c784;">●</span> **APTA** | **Apta / Calidad Óptima** | Cero errores de decodificación FFmpeg, bitrate adecuado ($\ge 190\text{ kbps}$), forma de onda limpia, sin corte abrupto. |
| <span style="color:#ffd54f;">▲</span> **REVISAR** | **Revisión Manual** | Bitrate deficiente ($< 190\text{ kbps}$), pausas o silencios anómalos en el cuerpo, o terminación abrupta sin fade-out. |
| <span style="color:#e57373;">✖</span> **ELIMINAR** | **Crítica / Corrupta** | Fallo grave de decodificación en FFmpeg, fragmento incompleto ($< 60\text{s}$) o clipping/saturación severa. |
| <span style="color:#90e0ef;">✔</span> **APLICADO** | **Actualizado en Disco** | Etiquetas ID3v2 normalizadas con éxito y archivo renombrado en disco. |

---

## Ejecución de la Batería de Pruebas

Para validar el saneamiento NTFS, la resolución de binarios, la concurrencia en QThread y la integridad de metadatos:
```bash
python test_suite.py
# Ran 11 tests in 0.530s -> OK
```

---

## Documentación Completa

- **[Manual de Usuario Completo en Español (MANUAL_USUARIO.md)](MANUAL_USUARIO.md)**
- **[Full User Manual in English (USER_MANUAL.md)](USER_MANUAL.md)**
- **[README Principal en Inglés (README.md)](README.md)**
