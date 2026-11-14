#!/usr/bin/env python3
"""
scripts/generate_icon.py - Generador Autónomo del Icono Multiplataforma PureTrack.

Genera:
- gui/assets/icon.png (1024x1024 RGBA con antialiasing)
- gui/assets/icon.ico (Icono multi-resolución para Windows: 16, 32, 48, 64, 128, 256 px)

Diseño:
AIMP Dark Style (#18191c) con barras de ecualizador acústico y pulso que forman
un checkmark minimalista (#ff9800 ámbar a #00b4d8 cian eléctrico).
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
    QBrush
)


def create_puretrack_image(size: int = 1024) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    scale = size / 1024.0

    # 1. Fondo Squircle AIMP Dark (#18191c) con degradado e iluminación sutil
    bg_margin = 64.0 * scale
    bg_size = size - (2 * bg_margin)
    bg_radius = 210.0 * scale

    bg_path = QPainterPath()
    bg_rect = QRectF(bg_margin, bg_margin, bg_size, bg_size)
    bg_path.addRoundedRect(bg_rect, bg_radius, bg_radius)

    # Sombra exterior y resplandor difuso
    glow_pen = QPen(QColor(0, 180, 216, 25), 18 * scale)
    painter.setPen(glow_pen)
    painter.drawPath(bg_path)

    glow_pen2 = QPen(QColor(255, 152, 0, 20), 10 * scale)
    painter.setPen(glow_pen2)
    painter.drawPath(bg_path)

    # Relleno del contenedor oscuro elegante
    bg_grad = QLinearGradient(0, bg_margin, 0, bg_margin + bg_size)
    bg_grad.setColorAt(0.0, QColor("#22242a"))
    bg_grad.setColorAt(0.5, QColor("#18191c"))
    bg_grad.setColorAt(1.0, QColor("#121315"))
    painter.fillPath(bg_path, QBrush(bg_grad))

    # Borde fino pulido
    border_pen = QPen(QColor("#2f333d"), 3.5 * scale)
    painter.setPen(border_pen)
    painter.drawPath(bg_path)

    # Resplandor radial interno acústico
    center_glow = QRadialGradient(size * 0.5, size * 0.52, size * 0.42)
    center_glow.setColorAt(0.0, QColor(0, 180, 216, 22))
    center_glow.setColorAt(0.4, QColor(255, 152, 0, 12))
    center_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
    painter.fillPath(bg_path, QBrush(center_glow))

    # 2. Anillo de pulso sutil / onda acústica de fondo
    ring_pen = QPen(QColor("#272a33"), 2.0 * scale, Qt.PenStyle.DashLine)
    painter.setPen(ring_pen)
    ring_radius = 270.0 * scale
    painter.drawEllipse(QPointF(size * 0.5, size * 0.5), ring_radius, ring_radius)

    c_ring = QColor("#00b4d8")
    c_ring.setAlpha(35)
    ring_pen2 = QPen(c_ring, 1.5 * scale)
    painter.setPen(ring_pen2)
    ring_radius2 = 330.0 * scale
    painter.drawEllipse(QPointF(size * 0.5, size * 0.5), ring_radius2, ring_radius2)

    # 3. Barras de ecualizador que configuran el Checkmark Acústico
    # 9 barras con anchos y alturas diseñadas para crear una curva de verificación nítida
    bar_width = 40.0 * scale
    bar_gap = 21.0 * scale
    bar_radius = bar_width * 0.5

    # Parámetros: (x_center_ratio, y_top_ratio, y_bottom_ratio, color_top, color_bottom)
    bars_data = [
        # Rama izquierda (Ámbar cálido descendente hacia el vértice)
        (280, 420, 640, "#ffb74d", "#ff9800"),
        (341, 480, 650, "#ffa726", "#f57c00"),
        (402, 540, 660, "#ff9800", "#e65100"),
        # Vértice inferior del checkmark (Punto de inflexión - Ámbar a Cian)
        (463, 610, 680, "#ffd54f", "#00b4d8"),
        # Rama derecha ascendente (Cian eléctrico subiendo con energía y pureza)
        (524, 490, 660, "#48cae4", "#0096c7"),
        (585, 370, 640, "#00b4d8", "#0077b6"),
        (646, 250, 620, "#90e0ef", "#0096c7"),
        (707, 130, 600, "#ade8f4", "#00b4d8"),
        (768, 220, 560, "#caf0f8", "#48cae4"),
    ]

    for x_c, y_t, y_b, c_top, c_bot in bars_data:
        x = (x_c * scale) - bar_radius
        y = y_t * scale
        h = (y_b - y_t) * scale

        bar_rect = QRectF(x, y, bar_width, h)
        bar_path = QPainterPath()
        bar_path.addRoundedRect(bar_rect, bar_radius, bar_radius)

        # Resplandor de la barra
        bar_glow = QPen(QColor(c_top), 6 * scale)
        bar_glow.setColor(QColor(QColor(c_top).red(), QColor(c_top).green(), QColor(c_top).blue(), 40))
        painter.setPen(bar_glow)
        painter.drawPath(bar_path)

        # Gradiente vertical de cada barra
        grad = QLinearGradient(x, y, x, y + h)
        grad.setColorAt(0.0, QColor(c_top))
        grad.setColorAt(1.0, QColor(c_bot))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.fillPath(bar_path, QBrush(grad))

        # Reflejo especular blanco en la cápsula superior de cada barra
        cap_rect = QRectF(x + 5 * scale, y + 4 * scale, bar_width - 10 * scale, (bar_width - 10 * scale) * 0.9)
        painter.setBrush(QColor(255, 255, 255, 85))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cap_rect)

    # 4. Línea de horizonte de pulso base acústica (onda de sonido sutil a los pies)
    pulse_pen = QPen(QColor("#2e323b"), 2.5 * scale, Qt.PenStyle.SolidLine)
    painter.setPen(pulse_pen)
    y_base = 730 * scale
    painter.drawLine(QPointF(220 * scale, y_base), QPointF(320 * scale, y_base))
    painter.drawLine(QPointF(720 * scale, y_base), QPointF(820 * scale, y_base))

    # Punto de pulso central
    painter.setBrush(QColor("#00b4d8"))
    painter.drawEllipse(QPointF(524 * scale, y_base), 3 * scale, 3 * scale)

    painter.end()
    return image


def save_png_and_ico(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / "icon.png"
    ico_path = output_dir / "icon.ico"

    print(f"[*] Generando icono vectorial de alta resolución (1024x1024)...")
    app = QGuiApplication.instance()
    if not app:
        app = QGuiApplication(["--platform", "offscreen"])

    img_1024 = create_puretrack_image(1024)
    img_1024.save(str(png_path), "PNG")
    print(f"[+] Icono PNG guardado: {png_path} ({png_path.stat().st_size / 1024:.1f} KB)")

    # Generar multi-resolución para Windows ICO: 256, 128, 64, 48, 32, 16
    resolutions = [256, 128, 64, 48, 32, 16]
    png_buffers = []

    for res in resolutions:
        scaled = img_1024.scaled(
            res, res,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        scaled.save(buf, "PNG")
        buf.close()
        png_buffers.append((res, bytes(ba)))

    # Empaquetar en formato ICO estándar de Windows (PNG compresión)
    # Header: 6 bytes (Reserved 2B=0, Type 2B=1, Count 2B=len)
    ico_data = bytearray()
    ico_data.extend(struct.pack("<HHH", 0, 1, len(png_buffers)))

    # Directorio de entradas (16 bytes cada una)
    # Offset inicial tras el header (6) + tabla de entradas (16 * count)
    offset = 6 + (16 * len(png_buffers))

    for res, png_bytes in png_buffers:
        width_byte = 0 if res >= 256 else res
        height_byte = 0 if res >= 256 else res
        bColorCount = 0
        bReserved = 0
        wPlanes = 1
        wBitCount = 32
        dwBytesInRes = len(png_bytes)
        dwImageOffset = offset

        ico_data.extend(struct.pack(
            "<BBBBHHII",
            width_byte,
            height_byte,
            bColorCount,
            bReserved,
            wPlanes,
            wBitCount,
            dwBytesInRes,
            dwImageOffset
        ))
        offset += len(png_bytes)

    # Escribir payloads PNG
    for _, png_bytes in png_buffers:
        ico_data.extend(png_bytes)

    ico_path.write_bytes(ico_data)
    print(f"[+] Icono ICO multi-resolución generado: {ico_path} ({ico_path.stat().st_size / 1024:.1f} KB)")
    print(f"    Resoluciones incrustadas: {resolutions}")


if __name__ == "__main__":
    assets_dir = Path(__file__).resolve().parent.parent / "gui" / "assets"
    save_png_and_ico(assets_dir)
