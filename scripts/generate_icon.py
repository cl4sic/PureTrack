#!/usr/bin/env python3
"""
scripts/generate_icon.py - Generador Profesional del Icono Multiplataforma PureTrack.

Genera:
- gui/assets/icon.png (1024x1024 RGBA con fondo 100% transparente y antialiasing)
- gui/assets/icon.ico (Icono multi-resolución para Windows: 16, 32, 48, 64, 128, 256 px)

Diseño:
Vinilo Técnico + Etiqueta ID3:
- Disco de vinilo oscuro minimalista (#18191c / #222327) con surcos concéntricos sutiles.
- Reflejos diagonales suaves tipo estudio (anisotropía de vinilo).
- Centro limpio con spindle hole.
- Etiqueta geométrica moderna en la esquina inferior derecha en color ámbar (#ff9800)
  con líneas minimalistas que simbolizan metadatos ordenados.
- Fondo exterior 100% transparente.
"""

import os
import sys
import struct
from pathlib import Path

# Configurar plataforma offscreen para Qt
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import Qt, QRectF, QPointF, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import (
    QGuiApplication,
    QImage,
    QPainter,
    QPainterPath,
    QColor,
    QLinearGradient,
    QRadialGradient,
    QPen,
    QBrush,
    QPolygonF
)


def create_puretrack_image(size: int = 1024) -> QImage:
    """Renderiza el icono maestro con antialiasing a resolución nativa y fondo transparente."""
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    scale = size / 1024.0

    # Coordenadas del centro del vinilo
    cx = 460.0 * scale
    cy = 470.0 * scale
    vinyl_radius = 420.0 * scale

    # -------------------------------------------------------------
    # 1. SOMBRA SUAVE DEL VINILO
    # -------------------------------------------------------------
    shadow_path = QPainterPath()
    shadow_path.addEllipse(QPointF(cx + 8 * scale, cy + 14 * scale), vinyl_radius, vinyl_radius)
    shadow_color = QColor(0, 0, 0, 80)
    painter.fillPath(shadow_path, QBrush(shadow_color))

    # -------------------------------------------------------------
    # 2. CUERPO DEL VINILO (#18191c / #222327)
    # -------------------------------------------------------------
    vinyl_path = QPainterPath()
    vinyl_path.addEllipse(QPointF(cx, cy), vinyl_radius, vinyl_radius)

    vinyl_grad = QRadialGradient(cx, cy, vinyl_radius)
    vinyl_grad.setColorAt(0.0, QColor("#222327"))
    vinyl_grad.setColorAt(0.5, QColor("#1c1d21"))
    vinyl_grad.setColorAt(0.85, QColor("#18191c"))
    vinyl_grad.setColorAt(1.0, QColor("#121315"))
    painter.fillPath(vinyl_path, QBrush(vinyl_grad))

    # Borde exterior del vinilo
    rim_pen = QPen(QColor("#2e3036"), 3.5 * scale)
    painter.setPen(rim_pen)
    painter.drawPath(vinyl_path)

    # -------------------------------------------------------------
    # 3. REFLEJOS DIAGONALES SUAVES TIPO ESTUDIO (Sheen)
    # -------------------------------------------------------------
    painter.save()
    painter.setClipPath(vinyl_path)

    # Cono de luz diagonal superior-izquierdo a inferior-derecho
    refl_grad = QLinearGradient(cx - vinyl_radius, cy - vinyl_radius, cx + vinyl_radius, cy + vinyl_radius)
    refl_grad.setColorAt(0.0, QColor(255, 255, 255, 22))
    refl_grad.setColorAt(0.2, QColor(255, 255, 255, 8))
    refl_grad.setColorAt(0.5, QColor(0, 0, 0, 0))
    refl_grad.setColorAt(0.8, QColor(0, 180, 216, 14))
    refl_grad.setColorAt(1.0, QColor(255, 255, 255, 20))
    painter.fillPath(vinyl_path, QBrush(refl_grad))

    # Cono perpendicular sutil
    refl_cross = QLinearGradient(cx - vinyl_radius, cy + vinyl_radius, cx + vinyl_radius, cy - vinyl_radius)
    refl_cross.setColorAt(0.0, QColor(255, 255, 255, 12))
    refl_cross.setColorAt(0.5, QColor(0, 0, 0, 0))
    refl_cross.setColorAt(1.0, QColor(255, 255, 255, 14))
    painter.fillPath(vinyl_path, QBrush(refl_cross))

    # -------------------------------------------------------------
    # 4. SURCOS CONCÉNTRICOS SUTILES (Grooves)
    # -------------------------------------------------------------
    for r_int in range(150, 410, 12):
        r = r_int * scale
        alpha_groove = 24 if (r_int % 24 == 0) else 12
        groove_pen = QPen(QColor(255, 255, 255, alpha_groove), 1.0 * scale)
        painter.setPen(groove_pen)
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # Surco oscuro de sombra
        dark_groove_pen = QPen(QColor(0, 0, 0, 35), 0.8 * scale)
        painter.setPen(dark_groove_pen)
        painter.drawEllipse(QPointF(cx, cy), r + 1.2 * scale, r + 1.2 * scale)

    # -------------------------------------------------------------
    # 5. GALLETA / CENTRO DEL VINILO
    # -------------------------------------------------------------
    center_radius = 135.0 * scale
    center_path = QPainterPath()
    center_path.addEllipse(QPointF(cx, cy), center_radius, center_radius)

    center_grad = QRadialGradient(cx, cy, center_radius)
    center_grad.setColorAt(0.0, QColor("#1e2024"))
    center_grad.setColorAt(0.8, QColor("#16171a"))
    center_grad.setColorAt(1.0, QColor("#0f1012"))
    painter.fillPath(center_path, QBrush(center_grad))

    # Anillo decorativo cian/ámbar en la galleta central
    inner_ring_pen = QPen(QColor(0, 180, 216, 70), 2.0 * scale)
    painter.setPen(inner_ring_pen)
    painter.drawEllipse(QPointF(cx, cy), 115.0 * scale, 115.0 * scale)

    inner_ring_pen2 = QPen(QColor(255, 152, 0, 110), 2.5 * scale)
    painter.setPen(inner_ring_pen2)
    painter.drawEllipse(QPointF(cx, cy), 75.0 * scale, 75.0 * scale)

    # Orificio central (Spindle hole)
    spindle_radius = 32.0 * scale
    spindle_pen = QPen(QColor("#2e3036"), 2.5 * scale)
    painter.setPen(spindle_pen)
    painter.setBrush(QBrush(QColor("#0a0a0c")))
    painter.drawEllipse(QPointF(cx, cy), spindle_radius, spindle_radius)

    painter.restore()

    # -------------------------------------------------------------
    # 6. ETIQUETA GEOMÉTRICA MODERNA ID3 (#ff9800) EN ESQUINA INFERIOR DERECHA
    # -------------------------------------------------------------
    # Tarjeta geométrica con perspectiva limpia y metadatos estructurados
    tag_x = 580.0 * scale
    tag_y = 570.0 * scale
    tag_w = 380.0 * scale
    tag_h = 360.0 * scale
    tag_radius = 42.0 * scale

    # Sombra de la etiqueta sobre el vinilo y el fondo
    tag_shadow = QPainterPath()
    tag_shadow.addRoundedRect(QRectF(tag_x + 6 * scale, tag_y + 12 * scale, tag_w, tag_h), tag_radius, tag_radius)
    painter.fillPath(tag_shadow, QBrush(QColor(0, 0, 0, 150)))

    # Contenedor de la etiqueta ID3
    tag_path = QPainterPath()
    tag_rect = QRectF(tag_x, tag_y, tag_w, tag_h)
    tag_path.addRoundedRect(tag_rect, tag_radius, tag_radius)

    tag_grad = QLinearGradient(tag_x, tag_y, tag_x + tag_w, tag_y + tag_h)
    tag_grad.setColorAt(0.0, QColor("#ffa726"))   # Ámbar brillante
    tag_grad.setColorAt(0.45, QColor("#ff9800"))  # Ámbar canónico AIMP
    tag_grad.setColorAt(1.0, QColor("#e65100"))   # Ámbar profundo
    painter.fillPath(tag_path, QBrush(tag_grad))

    # Borde de realce de la etiqueta
    tag_border = QPen(QColor(255, 236, 179, 180), 3.0 * scale)
    painter.setPen(tag_border)
    painter.drawPath(tag_path)

    # Orificio metálico de la etiqueta (Eyelet)
    eyelet_cx = tag_x + 48.0 * scale
    eyelet_cy = tag_y + 48.0 * scale
    eyelet_r = 16.0 * scale
    painter.setPen(QPen(QColor(255, 255, 255, 220), 2.5 * scale))
    painter.setBrush(QBrush(QColor("#18191c")))
    painter.drawEllipse(QPointF(eyelet_cx, eyelet_cy), eyelet_r, eyelet_r)

    # -------------------------------------------------------------
    # 7. LÍNEAS MINIMALISTAS QUE SIMBOLIZAN METADATOS ORDENADOS
    # -------------------------------------------------------------
    # Línea 1: Título de la pista (Track Title)
    line1_x = tag_x + 85.0 * scale
    line1_y = tag_y + 40.0 * scale
    line1_w = 230.0 * scale
    line1_h = 16.0 * scale
    p1 = QPainterPath()
    p1.addRoundedRect(QRectF(line1_x, line1_y, line1_w, line1_h), 8.0 * scale, 8.0 * scale)
    painter.fillPath(p1, QBrush(QColor("#ffffff")))

    # Línea 2: Artistas principales (Artist Line)
    line2_x = tag_x + 46.0 * scale
    line2_y = tag_y + 95.0 * scale
    line2_w = 280.0 * scale
    line2_h = 13.0 * scale
    p2 = QPainterPath()
    p2.addRoundedRect(QRectF(line2_x, line2_y, line2_w, line2_h), 6.5 * scale, 6.5 * scale)
    painter.fillPath(p2, QBrush(QColor("#fff8e1")))

    # Línea 3: Álbum y Año (Album & Year)
    line3_x = tag_x + 46.0 * scale
    line3_y = tag_y + 135.0 * scale
    line3_w = 210.0 * scale
    line3_h = 13.0 * scale
    p3 = QPainterPath()
    p3.addRoundedRect(QRectF(line3_x, line3_y, line3_w, line3_h), 6.5 * scale, 6.5 * scale)
    painter.fillPath(p3, QBrush(QColor("#ffe082")))

    # Separador sutil
    div_pen = QPen(QColor(255, 255, 255, 80), 2.0 * scale)
    painter.setPen(div_pen)
    painter.drawLine(
        QPointF(tag_x + 46.0 * scale, tag_y + 185.0 * scale),
        QPointF(tag_x + 334.0 * scale, tag_y + 185.0 * scale)
    )

    # Línea 4: Bloques técnicos (Bitrate / Quality Badge / Checkmark)
    # Bloque 1: Badge CBR 320 kbps
    b1_rect = QRectF(tag_x + 46.0 * scale, tag_y + 215.0 * scale, 120.0 * scale, 34.0 * scale)
    b1_path = QPainterPath()
    b1_path.addRoundedRect(b1_rect, 10.0 * scale, 10.0 * scale)
    painter.fillPath(b1_path, QBrush(QColor("#18191c")))

    # Texto o barras simétricas en el badge
    bar_pen = QPen(QColor("#00b4d8"), 4.0 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(bar_pen)
    painter.drawLine(
        QPointF(tag_x + 65.0 * scale, tag_y + 232.0 * scale),
        QPointF(tag_x + 145.0 * scale, tag_y + 232.0 * scale)
    )

    # Bloque 2: Checkmark de Calidad Verificada
    chk_cx = tag_x + 280.0 * scale
    chk_cy = tag_y + 255.0 * scale
    chk_circle = QPainterPath()
    chk_circle.addEllipse(QPointF(chk_cx, chk_cy), 45.0 * scale, 45.0 * scale)
    painter.fillPath(chk_circle, QBrush(QColor("#18191c")))
    painter.setPen(QPen(QColor(255, 255, 255, 180), 2.5 * scale))
    painter.drawPath(chk_circle)

    # Trazo de checkmark nítido en color verde esmeralda / blanco
    chk_pen = QPen(QColor("#81c784"), 6.0 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(chk_pen)
    chk_path = QPainterPath()
    chk_path.moveTo(chk_cx - 20 * scale, chk_cy + 2 * scale)
    chk_path.lineTo(chk_cx - 6 * scale, chk_cy + 16 * scale)
    chk_path.lineTo(chk_cx + 22 * scale, chk_cy - 16 * scale)
    painter.drawPath(chk_path)

    painter.end()
    return image


def save_multiresolution_ico(png_images: list[tuple[int, bytes]], output_ico_path: Path):
    """
    Empaqueta múltiples representaciones PNG en un archivo ICO multi-resolución estándar para Windows.
    png_images es una lista de (size, png_bytes).
    """
    num_images = len(png_images)
    header = struct.pack("<HHH", 0, 1, num_images)

    entries = []
    offset = 6 + (16 * num_images)
    image_data_blocks = []

    for s, data in png_images:
        width_byte = 0 if s >= 256 else s
        height_byte = 0 if s >= 256 else s
        data_len = len(data)

        entry = struct.pack(
            "<BBBBHHII",
            width_byte,
            height_byte,
            0,
            0,
            1,
            32,
            data_len,
            offset
        )
        entries.append(entry)
        image_data_blocks.append(data)
        offset += data_len

    with open(output_ico_path, "wb") as f:
        f.write(header)
        for e in entries:
            f.write(e)
        for b in image_data_blocks:
            f.write(b)


def main():
    print("=" * 70)
    print(">>> PURETRACK: GENERACIÓN DEL ICONO DEFINITIVO TRANSPARENTE")
    print("=" * 70)

    # Asegurar QApplication offscreen
    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication(["--platform", "offscreen"])

    assets_dir = Path(__file__).resolve().parent.parent / "gui" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    png_path = assets_dir / "icon.png"
    ico_path = assets_dir / "icon.ico"

    # 1. Renderizar imagen maestra a 1024x1024
    print("[*] Renderizando icono vectorial maestro 1024x1024 (Vinilo Técnico + Etiqueta ID3)...")
    master_img = create_puretrack_image(1024)

    # Verificar píxeles exteriores para garantizar transparencia
    corner_pixel = master_img.pixelColor(10, 10)
    print(f"    - Color esquina (10, 10): RGBA({corner_pixel.red()}, {corner_pixel.green()}, {corner_pixel.blue()}, {corner_pixel.alpha()})")
    assert corner_pixel.alpha() == 0, "Error: El fondo exterior debe ser 100% transparente."

    # Guardar PNG maestro
    if master_img.save(str(png_path), "PNG"):
        size_kb = png_path.stat().st_size / 1024.0
        print(f"[+] Archivo PNG guardado: {png_path} ({size_kb:.1f} KB)")
    else:
        print("[!] ERROR al guardar icon.png")
        sys.exit(1)

    # 2. Generar resoluciones para Windows ICO
    ico_sizes = [16, 32, 48, 64, 128, 256]
    png_buffers = []

    print(f"[*] Generando capas multi-resolución para icon.ico ({ico_sizes})...")
    for s in ico_sizes:
        scaled = master_img.scaled(
            s, s,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        scaled.save(buf, "PNG")
        buf.close()
        png_buffers.append((s, bytes(ba)))

    save_multiresolution_ico(png_buffers, ico_path)
    ico_size_kb = ico_path.stat().st_size / 1024.0
    print(f"[+] Archivo ICO guardado: {ico_path} ({ico_size_kb:.1f} KB)")

    print("=" * 70)
    print("[✓] Iconos definitivos generados y verificados con éxito.")


if __name__ == "__main__":
    main()
