# Suite de Auditoría, Identificación y Normalización de Audio MP3 (Multiplataforma)

Herramienta modular en Python para la inspección acústica exhaustiva, saneamiento, consulta de metadatos oficiales y renombrado seguro de colecciones musicales MP3.

Diseñada con **compatibilidad total para Windows (NTFS), Linux y macOS**, con soporte para distribución autónoma en Windows sin necesidad de Python ni conocimientos técnicos.

---

## 📁 Arquitectura del Proyecto

```
.
├── common_utils.py        # Utilidades: resolución de binarios (./bin/, bundle, PATH) y saneamiento NTFS
├── audit_audio.py         # Fase 1: Auditoría acústica, diagnóstico y reportes UTF-8 (pathlib.Path)
├── enrich_metadata.py     # Fase 2: Consulta de catálogo, normalización ID3v2 y formateo saneado
├── pipeline.py            # Fase 3: Orquestador CLI con dry-run, ejecución y rollback
├── package_windows.py     # Compilador y empaquetador autónomo con PyInstaller
├── ejecutar_auditoria_y_renombrado.bat  # Lanzador interactivo de doble clic para Windows
├── bin/                   # Carpeta para binarios locales autónomos (ffmpeg.exe, ffprobe.exe, fpcalc.exe)
├── output/                # Directorio de reportes y registros
│   ├── informe_auditoria.md   # Informe técnico ejecutivo en Markdown
│   ├── informe_auditoria.csv  # Base diagnóstica tabular completa
│   └── rename_log.json        # Registro transaccional para reversión (rollback)
└── *.mp3                  # Colección musical
```

---

## 🪟 Distribución para Usuarios de Windows (Sin Python)

Para compartir esta herramienta con personas que no tienen Python instalado:

### 1. Colocar los Binarios Autónomos en `bin/`
Descarga y copia los siguientes tres ejecutables en la carpeta `bin/`:
1. `ffmpeg.exe`: Descárgalo desde [gyan.dev FFmpeg builds](https://www.gyan.dev/ffmpeg/builds/) (archivo `ffmpeg-release-essentials.zip`, carpeta `bin/`).
2. `ffprobe.exe`: Incluido en el mismo paquete ZIP de FFmpeg anterior.
3. `fpcalc.exe`: Descárgalo desde [AcoustID Chromaprint](https://acoustid.org/chromaprint) (binario oficial de Windows).

### 2. Generar el Paquete Distribuible con PyInstaller
En una máquina con Python, ejecuta:
```bash
pip install pyinstaller
python package_windows.py
```
Esto creará la carpeta autónoma `dist/AudioSanitizer/` con todo preconfigurado.

### 3. Uso por el Usuario Final
El usuario solo debe:
1. Descomprimir el ZIP con la carpeta `AudioSanitizer`.
2. Pegar sus canciones `.mp3` dentro de la carpeta.
3. Hacer doble clic sobre `ejecutar_auditoria_y_renombrado.bat` y elegir la opción deseada del menú interactivo.

---

## 🚀 Uso mediante Consola / Línea de Comandos

### 1. Auditoría Técnica (Fase 1)
```bash
python audit_audio.py
```

### 2. Simulación de Metadatos y Renombrado (Fase 2 & 3 - Dry Run)
```bash
python pipeline.py
```

### 3. Aplicación Real de Cambios
```bash
python pipeline.py --apply
```

### 4. Reversión Instantánea (Rollback)
```bash
python pipeline.py --rollback
```

---

## 🛡️ Robustez y Compatibilidad NTFS

1. **Rutas Normalizadas:** Todo el código emplea `pathlib.Path` de forma consistente, eliminando incompatibilidades de barras y separadores.
2. **Saneamiento Anti-`WinError 123`:** La función `sanitize_windows_filename()` filtra caracteres reservados (`\ / : * ? " < > |`), caracteres de control ASCII (0-31), espacios/puntos finales y nombres de dispositivo de DOS (`CON`, `PRN`, `AUX`, `NUL`, etc.).
3. **Codificación Universal:** Todos los accesos a disco, informes Markdown, CSV y registros JSON se leen y escriben con `encoding="utf-8"` explícito.
