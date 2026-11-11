# Skill: PySide6 Professional Audio App Engineering

## Objetivo
Guiar el diseño, arquitectura visual y empaquetado de una suite de análisis y retiquetado de audio profesional estilo AIMP.

## Componentes UI Clave (AIMP Aesthetics)
1. **Paleta de Colores:**
   - Fondo Base: `#18191c` (Gris carbón oscuro).
   - Paneles/Tarjetas: `#222327` y bordes sutiles en `#2e3036`.
   - Acento Principal: `#ff9800` (Ámbar AIMP) o `#00d2ff` (Cian tecnológico).
   - Texto: Principal `#f0f0f0`, Secundario `#8b8e98`.
   - Badges de Calidad: Verde `#4caf50` (Apto), Amarillo `#ffc107` (Alerta/Revisar), Rojo `#f44336` (Corrupto/Clipping).
2. **Componente: Constructor Visual de Patrones (Pattern Builder):**
   - Barra de entrada de texto editable con "chips" o botones clickeables con tokens: `{artist}`, `{title}`, `{remix}`, `{feat}`, `{album}`, `{genre}`.
   - Vista previa dinámica en tiempo real que muestre cómo quedará una canción de muestra al escribir el patrón.
3. **Componente: Inspector de Auditoría y Filtros:**
   - Switches/Checkboxes modernos para activar/desactivar:
     - [ ] Detección de clipping (> 0 dBFS).
     - [ ] Detección de silencios anómalos (> N segundos).
     - [ ] Umbral mínimo de Bitrate (slider de 128 a 320 kbps).
     - [ ] Duración mínima (slider de 10s a 120s).
4. **Componente: Tabla de Pistas Reactiva:**
   - Columnas: Estado (Badge), Archivo Original, Nombre Proyectado, Bitrate, Duración, Clipping %, Acción.
   - Menú contextual con clic derecho: "Reproducir preview", "Inspeccionar espectro", "Excluir", "Editar manualmente".
5. **Componente: Barra Inferior de Control:**
   - Botón de Auditoría [Iniciar Análisis].
   - Botón de [Dry-Run (Simulación)].
   - Botón de [Aplicar Cambios].
   - Botón de [Deshacer / Rollback].
   - Barra de progreso dual (Pista actual / Lote global) con ETA y velocidad.