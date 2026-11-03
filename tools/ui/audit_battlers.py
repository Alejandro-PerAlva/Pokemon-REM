#!/usr/bin/env python3
"""Auditoría de colocación de sprites de combate (misma matemática que rem_ui.rb / BitmapWrapperEX).
Para cada especie mide el arte del primer fotograma y predice dónde quedan pies y cabeza.
Jugador: pies en y=294 (304-10); rival: pies en y=176 (menos altitud). Pantalla 512x384, menú desde y=288."""
import os, re, sys
from PIL import Image
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
B = os.path.join(ROOT, "Graphics", "Battlers")
res = {"front": [], "back": []}
for f in sorted(os.listdir(B)):
    m = re.fullmatch(r"(\d{3})(b?)\.png", f)           # solo formas base
    if not m: continue
    im = Image.open(os.path.join(B, f)).convert("RGBA"); h = im.height
    bb = im.crop((0, 0, min(h, im.width), h)).split()[3].point(lambda v: 255 if v > 10 else 0).getbbox()
    if not bb: res["back" if m.group(2) else "front"].append((m.group(1), "vacío", 0, 0)); continue
    sc = 3 if m.group(2) else 2
    art_h = (bb[3] - bb[1]) * sc; art_w = (bb[2] - bb[0]) * sc
    res["back" if m.group(2) else "front"].append((m.group(1), "ok", art_h, art_w))
for side, feet, limit in (("back", 294, 294 - 4), ("front", 176, 176 - 4)):
    L = res[side]; bad = [x for x in L if x[1] == "vacío" or x[2] > limit]
    print(f"{side}: {len(L)} especies, tope visible (altura de arte máx. {limit}px): {len(bad)} fuera")
    for x in bad[:20]: print("   ", x)
    hs = sorted(x[2] for x in L if x[1] == "ok")
    if hs: print("    altura de arte: min", hs[0], "mediana", hs[len(hs)//2], "máx", hs[-1])
