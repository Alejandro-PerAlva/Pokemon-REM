#!/usr/bin/env python3
"""Placeholders de eventos de campo: Poké Ball del suelo y fogata (apagada/encendida).
Hoja 256x256 = 4x4 fotogramas de 64 px (como trchar/npc). No sobrescribe PNG existentes (el diseñador los sustituye por arte final).
Uso: python3 tools/events/build_event_placeholders.py   (desde la raíz del proyecto)"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Graphics", "Characters")

def font(sz):
    return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", sz)

def sheet(draw_frame):
    im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for row in range(4):
        for col in range(4):
            draw_frame(d, col * 64, row * 64, col)
    return im

def ball(d, x, y, c):
    cx, cy = x + 32, y + 42
    d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=(236, 236, 240, 255), outline=(20, 22, 30, 255), width=2)
    d.pieslice([cx - 11, cy - 11, cx + 11, cy + 11], 180, 360, fill=(214, 60, 60, 255), outline=(20, 22, 30, 255), width=2)
    d.line([cx - 11, cy, cx + 11, cy], fill=(20, 22, 30, 255), width=2)
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(236, 236, 240, 255), outline=(20, 22, 30, 255), width=2)
    d.text((cx, y + 14), "ITEM", font=font(9), fill=(238, 238, 244, 255), anchor="mm")

def campfire(lit):
    def f(d, x, y, c):
        cx, by = x + 32, y + 54
        d.line([cx - 18, by, cx + 14, by - 8], fill=(92, 64, 40, 255), width=6)
        d.line([cx + 18, by, cx - 14, by - 8], fill=(112, 78, 48, 255), width=6)
        if lit:
            h = 22 + (c % 2) * 6
            d.polygon([(cx - 12, by - 6), (cx, by - 6 - h), (cx + 12, by - 6)], fill=(240, 140, 40, 255))
            d.polygon([(cx - 6, by - 6), (cx, by - 6 - h * 0.65), (cx + 6, by - 6)], fill=(252, 220, 90, 255))
        else:
            d.ellipse([cx - 8, by - 10, cx + 8, by - 2], fill=(60, 60, 66, 255))
        d.text((cx, y + 10), "FOGATA ON" if lit else "FOGATA OFF", font=font(8), fill=(238, 238, 244, 255), anchor="mm")
    return f

FILES = {
    "rem_itemball.png": lambda: sheet(lambda d, x, y, c: ball(d, x, y, c)),
    "rem_campfire_off.png": lambda: sheet(campfire(False)),
    "rem_campfire_on.png": lambda: sheet(campfire(True)),
}
for name, mk in FILES.items():
    p = os.path.join(OUT, name)
    if os.path.exists(p):
        print("respetado", name); continue
    mk().save(p); print("creado", name)
