<p align="center">
  <img src="gui/assets/icon.png" width="130" height="130" alt="Icono de PureTrack">
</p>

<h1 align="center">PureTrack Suite (Español)</h1>

<p align="center">
  <b>Suite de Escritorio Avanzada para Auditoría Acústica, Normalización de Metadatos y Saneamiento Musical</b>
  <br>
  <i>Desarrollada con Python, PySide6 (Qt 6), FFmpeg, Chromaprint, Mutagen, SoundFile y NumPy</i>
</p>

<p align="center">
  <a href="https://github.com"><img src="https://img.shields.io/badge/Plataforma-Windows%20%7C%20Linux-blue.svg" alt="Plataforma"></a>
  <a href="https://www.qt.io/"><img src="https://img.shields.io/badge/GUI-PySide6%20%28Qt%206%29-brightgreen.svg" alt="Framework"></a>
  <a href="https://ffmpeg.org"><img src="https://img.shields.io/badge/Audio-FFmpeg%20%7C%20Mutagen%20%7C%20Chromaprint-orange.svg" alt="Motor"></a>
  <a href="https://www.aimp.ru"><img src="https://img.shields.io/badge/Tema-AIMP%20Dark-amber.svg" alt="Tema"></a>
  <a href="locales/"><img src="https://img.shields.io/badge/i18n-Auto%20%7C%20ES%20%7C%20EN-cyan.svg" alt="i18n"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/Licencia-GPLv3-blue.svg" alt="Licencia"></a>
</p>

<p align="center">
  <a href="README.md"><b>English README (README.md)</b></a> | 
  <a href="MANUAL_USUARIO.md"><b>Manual de Usuario en Español (MANUAL_USUARIO.md)</b></a> | 
  <a href="USER_MANUAL.md"><b>Full User Manual in English (USER_MANUAL.md)</b></a>
</p>

---

## Descripción General

**PureTrack** es una suite de escritorio profesional para la auditoría técnica acústica, normalización de metadatos y renombrado seguro de colecciones musicales MP3. Desarrollada con **Python**, **PySide6 (Qt 6)** y motores de análisis acústico en C/Audio (**FFmpeg**, **Mutagen**, **Chromaprint**, **SoundFile**, **NumPy**), ofrece una estética oscura de alto contraste inspirada en **AIMP** para DJs, curadores musicales, productores y audiófilos en **Windows y Linux**.

---

## Capturas de Pantalla e Interfaz de Usuario

PureTrack fusiona rigor técnico acústico con una interfaz intuitiva y oscura estilo AIMP de alto contraste, ofreciendo doble acento de color (Ámbar `#ff9800` y Cian `#00b4d8`) y diseño colapsable dinámico:

### 1. Procesamiento Acústico y de Metadatos en Tiempo Real
*Vista del procesado en ejecución mostrando barras duales sincronizadas (Lote y Pista actual), análisis acústico en tiempo real (clipping, bitrates reales, duración, silencios) y consola integrada de actividad técnica.*

<p align="center">
  <img src="docs/images/puretrack_processing.jpg" width="100%" alt="PureTrack Procesando en Tiempo Real">
</p>

### 2. Panel Inspector Completo (Constructor de Patrones y Reglas Acústicas)
*Configuración de patrones dinámicos mediante chips interactivos, previsualización en vivo sobre una pista de muestra y controles de umbrales acústicos (clipping, silencios anómalos, cortes abruptos, bitrate mínimo y duración mínima).*

<p align="center">
  <img src="docs/images/puretrack_inspector.png" width="100%" alt="PureTrack Panel Inspector Completo">
</p>

### 3. Vista de Biblioteca Optimizada (Tabla Expandida)
*Panel inspector colapsado para maximizar el área visible de la biblioteca musical, ideal para colecciones masivas de DJ y pantallas panorámicas.*

<p align="center">
  <img src="docs/images/puretrack_table.png" width="100%" alt="PureTrack Vista Optimizada de Tabla">
</p>

---

## Descargas (GitHub Releases)

Los usuarios finales pueden descargar los ejecutables únicos autónomos (`--onefile`) y los paquetes comprimidos directamente desde la sección **[Releases](../../releases)** de GitHub:

| Archivo Distribuible | Sistema Operativo | Arquitectura | Descripción |
| :--- | :--- | :--- | :--- |
| **`PureTrack-Windows-x64.exe`** | Windows 10 / 11 | x86_64 | Ejecutable portable autónomo `.exe` con FFmpeg, FFprobe y Chromaprint incrustados. No requiere instalación. |
| **`PureTrack-Windows-x64.zip`** | Windows 10 / 11 | x86_64 | Paquete ZIP que contiene el ejecutable único para distribución rápida. |
| **`PureTrack-Linux-x64`** | Distribuciones Linux | x86_64 | Binario independiente ELF con la suite completa de análisis acústico. |
| **`PureTrack-Linux-x64.tar.gz`** | Distribuciones Linux | x86_64 | Archivo tarball comprimido para entornos Linux. |

---

## Características Principales

- **Sistema Multi-idioma Profesional (i18n):** Detección automática del idioma del sistema operativo (`Auto`) y selector en caliente en la barra superior (`Español` / `English`), traduciendo al instante toda la interfaz, tablas, barras de progreso, badges y diálogos sin necesidad de reiniciar.
- **Identidad Visual Profesional y Transparente:** Icono vectorial de alta resolución de vinilo técnico con etiqueta ID3 (`gui/assets/icon.png` a 1024x1024 con fondo 100% transparente RGBA, y `gui/assets/icon.ico` multi-resolución 16–256px) integrado en la ventana y anclado a la barra de tareas de Windows (`AppUserModelID`).
- **Concurrencia Total con QThread:** La auditoría de ondas, cálculo de huellas Chromaprint, peticiones a catálogos y escrituras en disco se ejecutan en segundo plano mediante hilos sincronizados (`QMutex`, `QWaitCondition`). Permite **Pausar**, **Reanudar** y **Cancelar** en cualquier instante sin congelar la ventana.
- **Estética AIMP Dark:** Fondo carbón (`#18191c`), tarjetas y paneles `#222327`, bordes `#2e3036`, y conmutación en caliente entre **Ámbar Clásico** (`#ff9800`) y **Cian Tecnológico** (`#00b4d8`).
- **Diagnóstico Acústico Profundo y Robusto:**
  - Bitrate exacto (discriminación precisa CBR y VBR vía Mutagen y FFprobe).
  - Detección de clipping y saturación digital ($\ge 0\text{ dBFS}$ / $\ge 0.999$).
  - Cálculo de rango dinámico y nivel RMS global.
  - Detección de cortes abruptos finales evaluando los últimos 400 ms y 100 ms de audio.
  - Detección de silencios anómalos en el cuerpo del tema mediante el filtro `silencedetect` de FFmpeg (ignorando silencios naturales en intro y outro).
  - Eliminación de falsos positivos: filtrado estricto de advertencias benignas (paquetes Xing, LAME, carátulas MJPEG/PNG y timestamps).
- **Constructor de Patrones Interactivo y Presets:** Gestor para crear, guardar y cargar presets personalizados, con chips dinámicos (`{artist}`, `{feat}`, `{title}`, `{remix}`, `{album}`, `{year}`, `{genre}`) y previsualización en vivo.
- **Nombres Personalizados y Modos de Edición:** Capacidad de personalizar manualmente el nombre proyectado de cualquier pista antes de aplicar en disco, con pre-rellenado inteligente y persistencia frente a cambios de patrones.
- **Mapeo Personalizable ID3v2:** Asignación flexible de marcos ID3v2.3 (`TIT2`, `TPE1`, `TALB`, `TPE2`, `TCON`, `TDRC`) en UTF-8 explícito preservando las carátulas incrustadas (`APIC`).
- **Saneamiento Estricto para Windows NTFS:** Sustitución de caracteres prohibidos (`\ / : * ? " < > |`), protección contra nombres de dispositivos DOS (`CON`, `PRN`, `AUX`, `NUL`), eliminación de puntos y espacios finales (`WinError 123`) y compatibilidad con rutas largas (`\\?\`).
- **Subprocesos Silenciosos en Windows:** Supresión completa de ventanas emergentes de consola CMD (`CREATE_NO_WINDOW` y flags de ocultación de ventana) en todas las ejecuciones de FFmpeg, FFprobe y fpcalc.
- **Rollback 100% Reversible:** Registro previo estructurado en `output/rename_log.json` antes de realizar cualquier cambio físico en el disco, permitiendo revertir nombres y tags con un solo clic.

---

## Arquitectura Modular del Proyecto

```
PureTrack/
├── .github/
│   └── workflows/
│       └── release.yml    # Compilación y publicación automatizada en GitHub Actions
├── docs/
│   └── images/            # Capturas de pantalla en alta resolución y diagramas
├── core/
│   ├── auditor.py         # Análisis técnico (FFmpeg, mutagen, clipping, silencios, cortes)
│   ├── common_utils.py    # Localizador autónomo de binarios, rutas largas (\\?\), saneamiento NTFS, subprocesos ocultos
│   ├── config_manager.py  # Presets, patrones y umbrales guardados en config.json
│   ├── i18n.py            # Motor TranslationManager, detección de sistema y hot-reload
│   ├── resolver.py        # Resolución de metadatos, MusicBrainz y caché persistente SQLite
│   └── tagger.py          # Mutagen ID3v2 UTF-8, saneamiento NTFS, transacciones y rollback
├── gui/
│   ├── assets/
│   │   ├── icon.ico       # Icono Windows multi-resolución (16x16 a 256x256)
│   │   └── icon.png       # Icono maestro transparente de alta resolución 1024x1024
│   ├── main_window.py     # Ventana principal, Drag & Drop, splitter, menús contextuales, selector de idioma
│   ├── widgets/
│   │   ├── audio_badge.py      # Badges visuales de calidad (APTA/OK, ALERTA/WARNING, ERROR, EXCLUIDA/EXCLUDED)
│   │   ├── pattern_builder.py  # Chips interactivos, gestor de presets y previsualización en vivo
│   │   ├── inspector_panel.py  # Panel colapsable con toggles de auditoría, sliders y mapeo ID3
│   │   └── progress_panel.py   # Barra de progreso dual (pista/lote), ETA, consola y botones de acción
│   ├── workers.py         # Workers concurrentes QThread (AuditWorker, EnrichWorker, ApplyWorker, RollbackWorker)
│   └── styles/
│       ├── aimp_dark.qss       # Hoja de estilos AIMP Dark en QSS
│       └── theme_loader.py     # Conmutador dinámico de paleta Ámbar/Cian
├── locales/
│   ├── en.json            # Diccionario de traducción al inglés
│   └── es.json            # Diccionario de traducción al español
├── bin/
│   └── README.md          # Guía de binarios de audio locales (ffmpeg, ffprobe, fpcalc)
├── package/
│   └── build_release.py   # Compilador PyInstaller multiplataforma para PureTrack (--onefile)
├── app.py                 # Punto de entrada de la aplicación
├── requirements.txt       # Dependencias del proyecto
├── LICENSE                # Licencia GNU General Public License v3.0 (GPLv3)
├── USER_MANUAL.md         # Manual de usuario en inglés
├── MANUAL_USUARIO.md      # Manual de usuario en español
└── test_suite.py          # Batería de pruebas automatizadas
```

---

## Guía de Inicio Rápido

### En Linux (Desde Código Fuente)
```bash
# 1. Activar el entorno virtual
source .venv/bin/activate

# 2. Iniciar PureTrack
python app.py
```

### Compilación Local de Ejecutable Único (PyInstaller)
```bash
python package/build_release.py --mode onefile
```

---

## Insignias de Calidad y Diagnóstico

| Insignia | Estado (ES / EN) | Significado Técnico |
| :---: | :--- | :--- |
| <span style="color:#81c784;">●</span> **APTA / OK** | **Apta / Calidad Óptima** | Cero errores de decodificación FFmpeg, bitrate adecuado ($\ge 190\text{ kbps}$), forma de onda limpia, sin corte abrupto. |
| <span style="color:#ffd54f;">▲</span> **ALERTA / WARNING** | **Revisión Manual** | Bitrate deficiente ($< 190\text{ kbps}$), pausas o silencios anómalos en el cuerpo, o terminación abrupta sin fade-out. |
| <span style="color:#e57373;">✖</span> **ERROR** | **Crítica / Corrupta** | Fallo grave de decodificación en FFmpeg, fragmento incompleto ($< 60\text{s}$) o clipping/saturación severa. |
| <span style="color:#888888;">⊘</span> **EXCLUIDA / EXCLUDED** | **Excluida del Lote** | Canción excluida del procesado mediante clic derecho en la tabla. |
| <span style="color:#90e0ef;">✔</span> **APLICADO / APPLIED** | **Actualizado en Disco** | Etiquetas ID3v2 normalizadas con éxito y archivo renombrado en disco. |

---

## Ejecución de la Batería de Pruebas

Para validar el saneamiento NTFS, la resolución de binarios, la concurrencia en QThread, el soporte multi-idioma (i18n) y la integridad de metadatos:
```bash
QT_QPA_PLATFORM=offscreen python test_suite.py
```

---

## Licencia

Este proyecto está bajo la licencia **GNU General Public License v3.0 (GPLv3)**. Consulta el archivo [LICENSE](LICENSE) para más detalles.
