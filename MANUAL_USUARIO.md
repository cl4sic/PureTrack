# AudioMaster Suite - Manual de Usuario

**AudioMaster** es una suite de escritorio profesional para la auditoría técnica, normalización de metadatos y renombrado seguro de bibliotecas musicales en formatos MP3. Desarrollada íntegramente con Python, PySide6 (Qt 6) y motores de análisis acústico en C/Audio (FFmpeg, Mutagen, SoundFile, Chromaprint, NumPy), cuenta con una interfaz pulida inspirada en la estética oscura de AIMP y está diseñada para funcionar de forma transparente y robusta tanto en Linux como en Windows.

---

## Índice de Contenidos
1. [Descripción General y Características Clave](#1-descripción-general-y-características-clave)
2. [Guía de la Interfaz Gráfica](#2-guía-de-la-interfaz-gráfica)
   - [Barra Superior y Drag & Drop](#barra-superior-y-drag--drop)
   - [Panel Izquierdo: Tabla Reactiva de Pistas](#panel-izquierdo-tabla-reactiva-de-pistas)
   - [Panel Derecho: Inspector de Ajustes Colapsable](#panel-derecho-inspector-de-ajustes-colapsable)
   - [Constructor Visual de Patrones (Pattern Builder)](#constructor-visual-de-patrones-pattern-builder)
   - [Panel Inferior: Telemetría, Progreso Dual y Consola](#panel-inferior-telemetría-progreso-dual-y-consola)
3. [Flujo de Trabajo Operativo](#3-flujo-de-trabajo-operativo)
   - [Fase 1: Auditoría Técnica y Diagnóstico](#fase-1-auditoría-técnica-y-diagnóstico)
   - [Fase 2: Resolución de Metadatos y Simulación (Dry-Run)](#fase-2-resolución-de-metadatos-y-simulación-dry-run)
   - [Fase 3: Aplicación Segura en Disco](#fase-3-aplicación-segura-en-disco)
   - [Fase 4: Reversión Completa (Rollback)](#fase-4-reversión-completa-rollback)
4. [Configuración Persistente y Presets](#4-configuración-persistente-y-presets)
5. [Instalación y Uso en Windows y Linux](#5-instalación-y-uso-en-windows-y-linux)
6. [Preguntas Frecuentes (FAQ)](#6-preguntas-frecuentes-faq)

---

## 1. Descripción General y Características Clave

- **Concurrencia Total con QThread:** Ninguna llamada de red, lectura de audio, cálculo de huella acústica ni ejecución de FFmpeg bloquea la interfaz de usuario (`MainThread`).
- **Diseño AIMP Dark:** Fondo carbón (`#18191c`), tarjetas y paneles en `#222327`, bordes sutiles en `#2e3036`, y paleta de acento seleccionable: **Ámbar Clásico** (`#ff9800`) o **Cian Tecnológico** (`#00b4d8`).
- **Diagnóstico Acústico Exhaustivo:**
  - Discriminación exacta de bitrate CBR/VBR mediante Mutagen y FFprobe.
  - Detección de clipping digital y saturación ($\ge 0\text{ dBFS}$ / $\ge 0.999$).
  - Cálculo de RMS global y rango dinámico.
  - Detección de cortes abruptos evaluando los últimos 400 ms y 100 ms de audio.
  - Detección de silencios anómalos en el cuerpo de la canción con el filtro `silencedetect` de FFmpeg (ignorando silencios naturales en intro y outro).
- **Constructor de Patrones en Tiempo Real:** Entrada editable con chips dinámicos clickeables y vista previa inmediata con una canción de muestra.
- **Saneamiento Estricto para Windows NTFS:** Sustitución de caracteres prohibidos (`\ / : * ? " < > |`), protección frente a nombres de dispositivos DOS (`CON`, `PRN`, `AUX`, `NUL`), eliminación de puntos y espacios finales, y soporte para rutas largas (`\\?\`).
- **Seguridad Transaccional:** Registro estructurado previo en `output/rename_log.json` para garantizar un **Rollback 100% reversible**.

---

## 2. Guía de la Interfaz Gráfica

### Barra Superior y Drag & Drop
- **Directorio Origen:** Muestra la ruta activa. Puedes introducir una ruta o pulsar **Examinar...** para seleccionarla con el explorador nativo.
- **Soporte Drag & Drop:** Arrastra una carpeta completa o una selección de archivos `.mp3` directamente a la ventana para cargarlos al instante.
- **Recargar:** Actualiza la lista de archivos desde el directorio seleccionado.
- **Tema (Ámbar / Cian):** Alterna en caliente entre los estilos visuales Ámbar AIMP y Cian Tecnológico.

### Panel Izquierdo: Tabla Reactiva de Pistas
- **Badges de Calidad:**
  - <span style="color:#81c784;">● APTA (Verde):</span> Pista íntegra, sin errores de decodificación y calidad óptima.
  - <span style="color:#ffd54f;">▲ REVISAR (Amarillo):</span> Alerta de bitrate bajo, silencio en el cuerpo o corte abrupto.
  - <span style="color:#e57373;">✖ ELIMINAR (Rojo):</span> Archivo corrupto, duración insuficiente o clipping severo.
  - <span style="color:#b0bec5;">○ PENDIENTE (Gris):</span> Cargado en memoria, esperando auditoría.
  - <span style="color:#90e0ef;">✔ APLICADO (Cian):</span> Modificado con éxito en el disco.
- **Columnas:** Estado, Archivo Original, Nombre Proyectado, Bitrate (CBR/VBR), Duración, Clipping % y Acción/Diagnóstico.
- **Menú Contextual (Clic Derecho):**
  - *Inspeccionar detalles técnicos:* Ventana modal con métricas detalladas de forma de onda, integridad FFmpeg y etiquetas ID3.
  - *Editar manualmente nombre proyectado:* Permite sobreescribir el nombre de salida para una pista específica.
  - *Excluir del lote / Re-incluir:* Permite omitir canciones concretas del proceso masivo.

### Panel Derecho: Inspector de Ajustes Colapsable
Puede ocultarse o mostrarse con el botón **Ocultar Ajustes ▶** / **Mostrar Ajustes ◀**.
- **Criterios de Auditoría y Umbrales:**
  - Casillas para activar/desactivar detección de clipping, silencios y cortes abruptos.
  - Control deslizante de Bitrate Mínimo (128 a 320 kbps).
  - Control deslizante de Duración Mínima (10 a 120 segundos).
- **Mapeo de Etiquetas ID3v2:** Asigna qué token dinámico se escribe en cada marco estándar (`TIT2`, `TPE1`, `TALB`, `TPE2`, `TCON`, `TDRC`).

### Constructor Visual de Patrones (Pattern Builder)
Haz clic en cualquier token dinámico para insertarlo en la posición del cursor:
| Token | Significado | Ejemplo |
| :--- | :--- | :--- |
| `{artist}` | Artistas principales unidos por `&` | `Martin Garrix & DallasK` |
| `{feat}` | Colaboradores con prefijo `feat.` | `feat. Sasha Alex Sloan` |
| `{guest}` | Artistas invitados con prefijo `&` | `& David Guetta` |
| `{title}` | Título oficial de la obra | `Loop` |
| `{remix}` | Subtítulo del remix si existe | `- Brooks Remix` |
| `{album}` | Nombre del álbum o EP oficial | `Seven` |
| `{year}` | Año de publicación (4 dígitos) | `2022` |
| `{genre}` | Género musical canónico | `Future Bounce` |
| `{all_artists}` | Lista completa de artistas | `Martin Garrix, DallasK, Sasha Alex Sloan` |

- **Presets Rápidos:**
  - *Estándar EDM / Pop:* `{artist}{feat} - {title}{remix}`
  - *Estricto Artista - Título:* `{artist} - {title}`
  - *Álbum y Año:* `{year} - {album} - {artist} - {title}{remix}`
  - *DJ Extended / Remix:* `{artist}{feat} - {title} ({remix})`

### Panel Inferior: Telemetría, Progreso Dual y Consola
- **Barra de Canción Actual:** Muestra la fase individual de procesamiento de la pista en curso.
- **Barra de Lote Global:** Muestra el porcentaje total, número de pistas procesadas, velocidad (canciones por segundo) y tiempo restante estimado (**ETA**).
- **Controles de Flujo:**
  - **Pausar / Reanudar:** Detiene de forma segura el worker sin interrumpir escrituras a medias.
  - **Cancelar:** Cancela limpiamente la tarea en ejecución y restablece los controles.
- **Consola de Registro:** Terminal integrada con código de colores según el nivel del mensaje (`[INFO]`, `[SUCCESS]`, `[WARNING]`, `[ERROR]`). Colapsable con el botón **Consola ▼**.

---

## 3. Flujo de Trabajo Operativo

### Fase 1: Auditoría Técnica y Diagnóstico
1. Carga tus pistas mediante Drag & Drop o con el botón **Examinar...**.
2. Pulsa **Auditar Biblioteca**.
3. El motor analizará cada pista en segundo plano, midiendo clipping, integridad y silencios.
4. Las insignias de la tabla se actualizarán dinámicamente con el veredicto de calidad.

### Fase 2: Resolución de Metadatos y Simulación (Dry-Run)
1. Ajusta tu patrón preferido en el **Pattern Builder**.
2. Pulsa **Simular (Dry-Run)**.
3. El sistema consultará la base canónica local, la caché SQLite (`output/metadata_cache.db`) y calculará las huellas Chromaprint.
4. En la columna **Nombre Proyectado** verás el resultado exacto sin modificar ningún archivo físico.

### Fase 3: Aplicación Segura en Disco
1. Pulsa **Aplicar en Disco**.
2. Confirma el cuadro de diálogo de seguridad.
3. AudioMaster:
   - Guardará el registro de operaciones en `output/rename_log.json`.
   - Escribirá los metadatos ID3v2.3 en UTF-8 preservando las carátulas.
   - Renombrará los archivos en disco aplicando el saneamiento NTFS.
   - Verificará la integridad con FFmpeg tras el guardado.

### Fase 4: Reversión Completa (Rollback)
Si necesitas deshacer cualquier cambio:
1. Pulsa **Deshacer (Rollback)**.
2. Confirma la acción en el cuadro de diálogo.
3. AudioMaster leerá el último registro transaccional y devolverá todos los archivos a sus nombres y etiquetas originales.

---

## 4. Configuración Persistente y Presets
Las preferencias se guardan automáticamente en formato JSON con codificación UTF-8:
- En Linux: `~/.config/AudioMaster/config.json` (con respaldo en la carpeta local de la aplicación).
- En Windows: `%APPDATA%\AudioMaster\config.json` (o `config.json` junto al ejecutable).

---

## 5. Instalación y Uso en Windows y Linux

### En Linux
```bash
# Activar entorno virtual
source .venv/bin/activate

# Iniciar la interfaz gráfica
python app.py
```

### Generación de Binario Autónomo en Linux
```bash
python package/build_release.py --mode onedir
# El ejecutable independiente se genera en: dist/AudioMaster/AudioMaster
```

### En Windows
1. Descarga y descomprime `AudioMaster_Windows.zip`.
2. Haz doble clic en **`compilar_exe_en_windows.bat`**:
   - Comprueba e instala automáticamente dependencias en 1 clic.
   - Genera el ejecutable autónomo en `dist\AudioMaster\AudioMaster.exe`.
   - Al finalizar, te pregunta si deseas abrirlo de inmediato (escribe `S`).
3. Para iniciar la aplicación en el futuro, simplemente haz doble clic en:
   - **`ejecutar_AudioMaster.bat`** (o abre directamente `dist\AudioMaster\AudioMaster.exe`).

---

## 6. Funcionalidades Avanzadas de Interfaz

### Columnas Redimensionables en la Tabla
- Todas las columnas de la tabla son interactivas: puedes hacer clic y arrastrar cualquier divisor del encabezado para ensanchar o reducir columnas como "Archivo Original" o "Nombre Proyectado" para leer títulos largos.
- **Auto-ajuste:** Haz doble clic sobre la línea divisoria del encabezado para ajustar automáticamente la columna al ancho exacto del texto más largo.
- **Scroll horizontal:** Si amplías las columnas más allá de la ventana, la tabla cuenta con barra de desplazamiento horizontal suave.

### Gestión de Presets Personalizados (Crear, Guardar y Editar)
- **Crear nuevo preset (`+ Nuevo`):** Diseña un patrón con los tokens dinámicos y pulsa `+ Nuevo`. Se te pedirá un nombre y quedará guardado permanentemente en `config.json`.
- **Guardar cambios (`Guardar`):** Modifica el patrón del preset actual y pulsa `Guardar` para actualizarlo.
- **Eliminar preset (`Borrar`):** Elimina el preset seleccionado (siempre se conserva al menos uno activo).

### Asignación de Nombres Personalizados (Protección en Disco)
- **Edición rápida:** Haz doble clic directamente sobre la celda de la columna **"Nombre Proyectado"** de cualquier canción (o haz clic derecho y selecciona *✏️ Asignar nombre personalizado...*).
- **Protección contra sobreescritura:** Al fijar un nombre personalizado, este se resalta en **color ámbar** y queda protegido; no será reemplazado al cambiar patrones en el inspector ni durante la auditoría.
- **Aplicación en disco:** Al pulsar **[Aplicar en Disco]**, las pistas con nombre personalizado se renombrarán con el nombre exacto que tú elegiste.
- **Restablecer:** Si cambias de opinión, haz clic derecho sobre la pista y selecciona *🔄 Restablecer a patrón automático*.

---

## 7. Preguntas Frecuentes (FAQ)

**P: ¿Por qué en algunas distribuciones Linux (como Arch COSMIC) aparecían cuadrados vacíos (`▯`) en los botones?**  
R: Algunos entornos de escritorio no tienen fuentes de emojis configuradas por defecto en las fuentes del sistema de Qt. En AudioMaster se utilizan iconos vectoriales estándar de Qt y tipografía universal, garantizando que todos los controles se vean nítidos e idénticos en cualquier sistema.

**P: ¿Se recomprime o altera el audio de mis pistas?**  
R: **No.** AudioMaster únicamente actualiza las etiquetas ID3v2 y el nombre del archivo en el sistema de archivos. Las muestras de audio permanecen 100% inalteradas.

**P: ¿Qué ocurre con las portadas o carátulas existentes en las canciones?**  
R: Se preservan íntegramente. El módulo de etiquetado respeta todos los marcos `APIC` existentes.
