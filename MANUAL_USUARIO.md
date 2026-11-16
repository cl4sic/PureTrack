# PureTrack Suite - Manual de Usuario

**PureTrack** es una suite de escritorio profesional para la auditoría técnica, normalización de metadatos y renombrado seguro de bibliotecas musicales en formato MP3. Desarrollada íntegramente con Python, PySide6 (Qt 6) y motores de análisis acústico en C/Audio (FFmpeg, Mutagen, SoundFile, Chromaprint, NumPy), cuenta con una interfaz pulida inspirada en la estética oscura de AIMP, soporte multi-idioma nativo (i18n) e icono profesional de alta resolución, funcionando de forma transparente y robusta tanto en Linux como en Windows.

---

## Índice de Contenidos
1. [Descripción General y Características Clave](#1-descripción-general-y-características-clave)
2. [Guía de la Interfaz Gráfica](#2-guía-de-la-interfaz-gráfica)
   - [Barra Superior: Selector de Idioma, Drag & Drop y Temas](#barra-superior-selector-de-idioma-drag--drop-y-temas)
   - [Panel Izquierdo: Tabla Reactiva de Pistas](#panel-izquierdo-tabla-reactiva-de-pistas)
   - [Panel Derecho: Inspector de Ajustes Colapsable](#panel-derecho-inspector-de-ajustes-colapsable)
   - [Constructor Visual de Patrones (Pattern Builder)](#constructor-visual-de-patrones-pattern-builder)
   - [Panel Inferior: Telemetría, Progreso Dual y Consola](#panel-inferior-telemetría-progreso-dual-y-consola)
3. [Flujo de Trabajo Operativo](#3-flujo-de-trabajo-operativo)
   - [Fase 1: Auditoría Técnica y Proyección Segura](#fase-1-auditoría-técnica-y-proyección-segura)
   - [Fase 2: Aplicación Segura en Disco](#fase-2-aplicación-segura-en-disco)
   - [Fase 3: Reversión Completa (Rollback)](#fase-3-reversión-completa-rollback)
4. [Sistema Multi-idioma (i18n) e Identidad Visual](#4-sistema-multi-idioma-i18n-e-identidad-visual)
5. [Configuración Persistente y Presets](#5-configuración-persistente-y-presets)
6. [Instalación y Uso en Windows y Linux](#6-instalación-y-uso-en-windows-y-linux)
7. [Preguntas Frecuentes (FAQ)](#7-preguntas-frecuentes-faq)

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

### Barra Superior: Selector de Idioma, Drag & Drop y Temas
- **Directorio Origen:** Muestra la ruta activa. Puedes introducir una ruta o pulsar **Examinar...** para seleccionarla con el explorador nativo.
- **Soporte Drag & Drop:** Arrastra una carpeta completa o una selección de archivos `.mp3` directamente a la ventana para cargarlos al instante.
- **Selector de Idioma (i18n):** Menú desplegable integrado (`Auto (Sistema)`, `Español`, `English`) que cambia instantáneamente el idioma de toda la interfaz en caliente sin reiniciar.
- **Recargar:** Actualiza la lista de archivos desde el directorio seleccionado.
- **Tema (Ámbar / Cian):** Alterna en caliente entre los estilos visuales Ámbar AIMP y Cian Tecnológico.

### Panel Izquierdo: Tabla Reactiva de Pistas
- **Badges de Calidad:**
  - <span style="color:#81c784;">● APTA / OK (Verde):</span> Pista íntegra, sin errores de decodificación y calidad óptima.
  - <span style="color:#ffd54f;">▲ ALERTA / WARNING (Amarillo):</span> Alerta de bitrate bajo, silencio en el cuerpo o corte abrupto.
  - <span style="color:#e57373;">✖ ERROR (Rojo):</span> Archivo corrupto, duración insuficiente o clipping severo.
  - <span style="color:#888888;">⊘ EXCLUIDA / EXCLUDED (Gris oscuro):</span> Canción excluida del procesamiento por el usuario.
  - <span style="color:#b0bec5;">○ PENDIENTE / PENDING (Gris):</span> Cargado en memoria, esperando auditoría.
  - <span style="color:#90e0ef;">✔ APLICADO / APPLIED (Cian):</span> Modificado con éxito en el disco.
- **Columnas Redimensionables:** Estado, Archivo Original, Nombre Proyectado, Bitrate (CBR/VBR), Duración, Clipping % y Acción/Diagnóstico. Todas las columnas pueden redimensionarse arrastrando sus divisores o con doble clic para auto-ajuste.
- **Menú Contextual (Clic Derecho):**
  - *Inspeccionar detalles técnicos:* Ventana modal con métricas detalladas de forma de onda, integridad FFmpeg y etiquetas ID3.
  - *Asignar nombre personalizado:* Permite sobreescribir manualmente el nombre de salida con pre-rellenado inteligente.
  - *Excluir del lote / Incluir en el lote:* Interruptor bidireccional dinámico para omitir canciones de forma selectiva.
  - *Restablecer a patrón automático:* Vuelve al patrón general si se había definido un nombre manual.

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

- **Gestor de Presets:**
  - Botón `+ Nuevo`: Crea un nuevo preset con nombre personalizado.
  - Botón `Guardar`: Guarda las modificaciones en el preset seleccionado.
  - Botón `Borrar`: Elimina un preset de la lista.

### Panel Inferior: Telemetría, Progreso Dual y Consola
- **Barra de Canción Actual:** Muestra la fase individual de procesamiento de la pista en curso.
- **Barra de Lote Global:** Muestra el porcentaje total, número de pistas procesadas, velocidad (canciones por segundo) y tiempo restante estimado (**ETA**).
- **Controles de Flujo:**
  - **Pausar / Reanudar:** Detiene de forma segura el worker sin interrumpir escrituras a medias.
  - **Cancelar:** Cancela limpiamente la tarea en ejecución y restablece los controles.
- **Consola de Registro:** Terminal integrada con código de colores según el nivel del mensaje (`[INFO]`, `[SUCCESS]`, `[WARNING]`, `[ERROR]`). Colapsable con el botón **Consola ▼**.

---

## 3. Flujo de Trabajo Operativo

### Fase 1: Auditoría Técnica y Proyección Segura
1. Carga tus pistas mediante Drag & Drop o con el botón **Examinar...**.
2. Ajusta tu patrón preferido en el **Pattern Builder** si deseas personalizarlo.
3. Pulsa **Auditar Biblioteca**.
4. El motor analizará cada pista en segundo plano, midiendo clipping, integridad, silencios y proyectando automáticamente los nuevos nombres limpios en la columna **Nombre Proyectado** sin tocar el disco.
5. Las insignias de la tabla se actualizarán dinámicamente con el veredicto de calidad.

### Fase 2: Aplicación Segura en Disco
1. Revisa los nombres proyectados y personaliza manualmente cualquiera si lo deseas.
2. Pulsa **Aplicar en Disco**.
3. Confirma el cuadro de diálogo de seguridad.
4. PureTrack:
   - Guardará el registro de operaciones en `output/rename_log.json`.
   - Escribirá los metadatos ID3v2.3 en UTF-8 preservando las carátulas.
   - Renombrará los archivos en disco aplicando el saneamiento NTFS y respetando nombres personalizados.
   - Verificará la integridad con FFmpeg tras el guardado.

### Fase 3: Reversión Completa (Rollback)
Si necesitas deshacer cualquier cambio:
1. Pulsa **Deshacer (Rollback)**.
2. Confirma la acción en el cuadro de diálogo.
3. PureTrack leerá el último registro transaccional y devolverá todos los archivos a sus nombres y etiquetas originales.

---

## 4. Sistema Multi-idioma (i18n) e Identidad Visual

- **Detección Automática de Idioma:** Al iniciar por primera vez, PureTrack detecta el idioma del sistema operativo (`QLocale`). Si el sistema está en español, la suite arranca automáticamente en español; de lo contrario, arranca en inglés.
- **Cambio en Caliente:** El selector en la barra superior permite conmutar entre `Auto (Sistema)`, `Español` e `English` en cualquier momento. Toda la interfaz se actualiza de inmediato sin necesidad de reiniciar la aplicación.
- **Icono Multiplataforma:** PureTrack incorpora un icono de alta definición estilo pulso acústico / ecualizador (`gui/assets/icon.png` e `icon.ico`), que se muestra en la ventana, barra de tareas de Windows y docks de Linux.

---

## 5. Configuración Persistente y Presets
Las preferencias se guardan automáticamente en formato JSON con codificación UTF-8:
- En Linux: `~/.config/PureTrack/config.json` (con respaldo en la carpeta local de la aplicación).
- En Windows: `%APPDATA%\PureTrack\config.json` (o `config.json` junto al ejecutable).

---

## 6. Instalación y Uso en Windows y Linux

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
# El ejecutable independiente se genera en: dist/PureTrack/PureTrack
```

### En Windows
1. Descarga y descomprime `PureTrack_Windows.zip`.
2. Haz doble clic en **`compilar_exe_en_windows.bat`**:
   - Comprueba e instala automáticamente dependencias en 1 clic.
   - Genera el ejecutable autónomo con icono e idiomas en `dist\PureTrack\PureTrack.exe`.
   - Al finalizar, te pregunta si deseas abrirlo de inmediato (escribe `S`).
3. Para iniciar la aplicación en el futuro, simplemente haz doble clic en:
   - **`ejecutar_PureTrack.bat`** (o abre directamente `dist\PureTrack\PureTrack.exe`).

---

## 7. Preguntas Frecuentes (FAQ)

**P: ¿Por qué ya no aparecen ventanas negras de consola CMD al auditar canciones en Windows?**  
R: PureTrack integra supresión automática de subprocesos (`CREATE_NO_WINDOW` y flags de ventana oculta) en todas las llamadas a FFmpeg, FFprobe y fpcalc.

**P: ¿Se recomprime o altera el audio de mis pistas?**  
R: **No.** PureTrack únicamente actualiza las etiquetas ID3v2 y el nombre del archivo en el sistema de archivos. Las muestras de audio permanecen 100% inalteradas.

**P: ¿Qué ocurre con las portadas o carátulas existentes en las canciones?**  
R: Se preservan íntegramente. El módulo de etiquetado respeta todos los marcos `APIC` existentes.

**P: Al ejecutar `PureTrack.exe` o el instalador en Windows, aparece la advertencia azul *"Windows protegió su PC / Microsoft Defender SmartScreen impidió el inicio de una aplicación no reconocida"*. ¿Es seguro?**  
R: **Sí, es 100% seguro.** Microsoft Defender SmartScreen muestra automáticamente este aviso preventivo para cualquier ejecutable nuevo de código abierto descargado de Internet que no cuente con un certificado digital de pago extendido (EV de más de 400€/año) o que aún no haya acumulado miles de descargas en la telemetría de Microsoft.

**Cómo ejecutarlo en 2 clics:**
1. En la ventana azul de SmartScreen, haz clic en el enlace subrayado **"Más información"** (*More info*).
2. Aparecerá el botón **"Ejecutar de todas formas"** (*Run anyway*). Haz clic en él y PureTrack se abrirá normalmente.
3. *Alternativa permanente:* Haz clic derecho sobre `PureTrack.exe` (o el archivo `.zip`) $\rightarrow$ **Propiedades** $\rightarrow$ en la pestaña *General* marca la casilla **"Desbloquear"** (*Unblock*) abajo a la derecha $\rightarrow$ pulsa **Aceptar**.

**P: ¿Cómo firmar el ejecutable localmente para que Windows no muestre "Editor desconocido"?**  
R: Hemos incluido un script PowerShell automatizado en `package/windows_scripts/sign_puretrack.ps1`. Al ejecutarlo, genera un certificado de confianza local y firma digitalmente `PureTrack.exe` con SHA-256 y marca de tiempo RFC 3161.

**P: ¿Cómo funciona el icono de PureTrack en Linux (Wayland y X11)?**  
R: Al iniciarse, PureTrack registra automáticamente la entrada de escritorio `puretrack.desktop` en `~/.local/share/applications/` y el icono oficial en `~/.local/share/icons/hicolor/256x256/apps/`. Además, el binario exporta un conjunto de pixmaps multi-resolución (16x16 a 1024x1024) para que la barra de tareas, el dock (GNOME / KDE / XFCE) y el selector Alt+Tab muestren siempre el icono nítido del vinilo.
