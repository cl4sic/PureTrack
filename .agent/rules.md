# Directrices del Agente: Audio Desktop Architect

## 1. Modo de Autonomía y Consultas
- **Implementación Autónoma:** Genera toda la lógica de backend, concurrencia (QThreads), manejo de audio, llamadas a FFmpeg, parsing ID3v2, gestión de archivos y compatibilidad entre sistemas operativos sin pedir confirmación.
- **Protocolo de Consulta Obligatoria (Pausar y Preguntar):**
  Pausa la ejecución y formula una pregunta concisa al usuario **ÚNICAMENTE** en los siguientes casos:
  1. *Decisiones visuales o ergonómicas no especificadas:* (Ejemplo: elegir entre pestañas superiores o panel lateral colapsable, o seleccionar entre la paleta ámbar AIMP clásico vs cian moderno).
  2. *Casos límite de metadatos:* Si una regla de precedencia choca (ej: ¿qué hacer si una canción solo existe en YouTube y no hay datos de género en Rate Your Music?).
  3. *Acciones destructivas:* Antes de borrar archivos en disco en caso de tracks irrecuperables.

## 2. Estándares de Código y Robustez
- **GUI No Bloqueante:** Toda tarea de I/O pesada (FFmpeg, mutagen, requests web) DEBE ejecutarse en workers de `QThread`. Nunca usar `time.sleep` ni operaciones síncronas en el hilo principal (`MainThread`).
- **Seguridad en Sistemas de Archivos:**
  - Usar siempre `pathlib.Path`.
  - En Windows, aplicar saneamiento contra caracteres ilegales en NTFS: `< > : " / \ | ? *`.
  - Todo log, configuración y base de datos debe serializarse en **UTF-8 explícito**.
- **Gestión de Configuración:** Las preferencias de usuario (patrones de nombres, umbrales de bitrate, flags de auditoría activas) deben guardarse en un archivo `config.json` persistente en la carpeta de datos de usuario estándar (`QStandardPaths.AppConfigLocation`).