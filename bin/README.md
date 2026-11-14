# Binarios Autónomos de Audio para PureTrack (bin/)

Esta carpeta está destinada a albergar los ejecutables autónomos de alto rendimiento que PureTrack utiliza para la decodificación, análisis acústico y cálculo de huellas digitales de audio.

## Binarios soportados

| Binario | Propósito | Plataforma | Fuente Recomendada |
| :--- | :--- | :--- | :--- |
| **`ffmpeg.exe`** / **`ffmpeg`** | Decodificación de audio, verificación de integridad y detección de silencios | Windows / Linux | [ffmpeg.org](https://ffmpeg.org/download.html) o [Gyan.dev](https://www.gyan.dev/ffmpeg/builds/) |
| **`ffprobe.exe`** / **`ffprobe`** | Extracción precisa de streams, formatos y bitrates CBR/VBR | Windows / Linux | Incluido en las distribuciones de FFmpeg |
| **`fpcalc.exe`** / **`fpcalc`** | Generación de huellas acústicas Chromaprint para identificación en MusicBrainz / AcoustID | Windows / Linux | [AcoustID Chromaprint](https://acoustid.org/chromaprint) |

---

## Compilación y Empaquetado Automático

- **En GitHub Actions:** Los binarios se descargan automáticamente durante el flujo de integración continua (`.github/workflows/release.yml`) y se incrustan dentro del ejecutable único (`--onefile`).
- **En Linux Local:** Si estos binarios no están en esta carpeta, PureTrack los localizará automáticamente desde el `$PATH` del sistema si están instalados (ej. `sudo pacman -S ffmpeg chromaprint` o `sudo apt install ffmpeg libchromaprint-tools`).
- **En Windows Local:** Para compilar un binario autónomo que los contenga, coloca `ffmpeg.exe`, `ffprobe.exe` y `fpcalc.exe` en esta carpeta antes de ejecutar `package/build_release.py`.
