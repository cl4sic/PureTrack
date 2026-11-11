#!/usr/bin/env python3
"""
package/generate_icons.py - Generador Autónomo de Iconos 100% Transparentes y Nítidos (Sin Blur).

Genera iconos modernos con bordes limpios y afilados (tipo vector), sin halo difuminado,
sin fondo gris y con transparencia pura para Windows (.ico) y Linux (.png).
"""

import sys
import struct
from pathlib import Path
from PySide6.QtCore import Qt, QBuffer, QIODevice
from PySide6.QtGui import (
    QGuiApplication,
    QImage,
    QColor,
    QPainter,
)


ROOT_DIR = Path(__file__).resolve().parent.parent
ICONS_DIR = ROOT_DIR / "gui" / "icons"


def create_ico_from_qimage(source_qimage: QImage, output_path: Path, sizes=(16, 24, 32, 48, 64, 128, 256)):
    """Genera un archivo .ico de Windows con payloads PNG embebidos para cada resolución."""
    images_png = []
    for s in sizes:
        scaled = source_qimage.scaled(s, s, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        square = QImage(s, s, QImage.Format_ARGB32_Premultiplied)
        square.fill(Qt.transparent)
        p = QPainter(square)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.drawImage((s - scaled.width()) // 2, (s - scaled.height()) // 2, scaled)
        p.end()

        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        square.save(buf, "PNG")
        png_bytes = buf.data().data()
        buf.close()
        images_png.append((s, png_bytes))

    num_images = len(images_png)
    ico_data = bytearray(struct.pack("<HHH", 0, 1, num_images))
    offset = 6 + 16 * num_images

    for s, png_bytes in images_png:
        w_byte = 0 if s == 256 else s
        h_byte = 0 if s == 256 else s
        ico_data += struct.pack(
            "<BBBBHHII",
            w_byte,
            h_byte,
            0,  # bColorCount
            0,  # bReserved
            1,  # wPlanes
            32,  # wBitCount
            len(png_bytes),
            offset,
        )
        offset += len(png_bytes)

    for _, png_bytes in images_png:
        ico_data += png_bytes

    output_path.write_bytes(ico_data)
    print(f"[+] Generado .ico ({output_path.name}): {len(ico_data):,} bytes con {num_images} resoluciones.")


def generate_all():
    app = QGuiApplication(sys.argv)
    source_img_path = ICONS_DIR / "concept_b_lettermark.jpg"
    if not source_img_path.exists():
        print(f"[!] No existe {source_img_path}")
        return False

    source_img = QImage(str(source_img_path))
    cw, ch = 565, 305
    crop = source_img.copy(230, 355, cw, ch)

    # 1. Extracción con bordes afilados y limpios (eliminación completa del difuminado / blur)
    crisp_img = QImage(cw, ch, QImage.Format_ARGB32_Premultiplied)
    crisp_img.fill(0)

    cutoff = 88
    ramp = 8.0

    for y in range(ch):
        for x in range(cw):
            c = crop.pixelColor(x, y)
            r, g, b = c.red(), c.green(), c.blue()
            val = max(r, g, b)
            min_v = min(r, g, b)
            sat = (val - min_v) / max(1, val)

            is_amber = (r > 65 and r > b + 20 and sat > 0.25)
            is_cyan = (b > 65 and g > 55 and b > r + 15 and sat > 0.25)
            is_white_core = (val > 170 and min_v > 100)

            if is_white_core:
                crisp_img.setPixelColor(x, y, QColor(r, g, b, 255))
            elif is_amber or is_cyan:
                if val < cutoff:
                    # Todo el halo difuminado exterior pasa a transparencia pura
                    crisp_img.setPixelColor(x, y, QColor(0, 0, 0, 0))
                elif val < cutoff + ramp:
                    # Anti-alias sutil de 1 píxel para evitar bordes dentados
                    alpha = int((val - cutoff) / ramp * 255)
                    crisp_img.setPixelColor(x, y, QColor(r, g, b, alpha))
                else:
                    crisp_img.setPixelColor(x, y, QColor(r, g, b, 255))
            else:
                crisp_img.setPixelColor(x, y, QColor(0, 0, 0, 0))

    # 2. Renderizado a 512x512 completamente transparente
    target_size = 512
    fill_ratio = 0.94
    final_img = QImage(target_size, target_size, QImage.Format_ARGB32_Premultiplied)
    final_img.fill(Qt.transparent)

    p = QPainter(final_img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)

    desired_w = int(target_size * fill_ratio)
    desired_h = int(desired_w * (ch / cw))
    scaled = crisp_img.scaled(desired_w, desired_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    pos_x = (target_size - scaled.width()) // 2
    pos_y = (target_size - scaled.height()) // 2

    p.drawImage(pos_x, pos_y, scaled)
    p.end()

    # Guardar versiones nítidas sin blur
    frameless_png_path = ICONS_DIR / "icon_concept_b_cyberwave.png"
    final_img.save(str(frameless_png_path), "PNG")
    print(f"[+] Guardado {frameless_png_path.name} (512x512, nítido sin blur)")

    app_icon_png = ICONS_DIR / "app_icon.png"
    final_img.save(str(app_icon_png), "PNG")
    print(f"[+] Actualizado {app_icon_png.name} (512x512, nítido sin blur)")

    # Generar contenedores .ico multirresolución de Windows
    frameless_ico_path = ICONS_DIR / "icon_concept_b_cyberwave.ico"
    create_ico_from_qimage(final_img, frameless_ico_path)
    app_icon_ico = ICONS_DIR / "app_icon.ico"
    create_ico_from_qimage(final_img, app_icon_ico)

    print("[*] Iconos nítidos sin blur generados con éxito.")
    return True


if __name__ == "__main__":
    generate_all()
