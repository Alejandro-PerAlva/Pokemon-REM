#!/usr/bin/env python3
"""Mochila "Oniria Noir": fondo (bagNoir.png) y mochilas recoloreadas (bag1..8 y bag1f..8f).
Originales en tools/ui/orig/bag/. Uso: python3 tools/ui/gen_bag_noir.py
Geometría compartida con rem_ui.rb (REM_UI::BAG_*)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image
import gen_summary_noir as S
import gen_pokedex_noir as D
G = S.G

def recolor(name_in, name_out):
    """Mochila oscura: luminosidad invertida (cuerpo grafito, trazos plata); el segmento rojo del bolsillo pasa a cian."""
    im = Image.open(os.path.join(G.ORIG, "bag", name_in.lower() + ".png")).convert("RGBA"); px = im.load()
    dark, silver = (30, 34, 44), (214, 219, 228)
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if not a: continue
            if r > g + 40 and r > b + 30:
                px[x, y] = (70, 214, 240, a); continue
            l = (0.3 * r + 0.59 * g + 0.11 * b) / 255.0
            px[x, y] = tuple(int(silver[i] + (dark[i] - silver[i]) * l) for i in range(3)) + (a,)
    G.save(im, name_out)

def main():
    im = S.base_bg()
    D.silver_box(im, (8, 8, 198, 48))                       # título del bolsillo
    D.silver_box(im, (8, 56, 198, 288))                     # mochila
    S.box(im, (20, 64, 186, 232), S.WELL, S.DIV, 6)         # pozo de la mochila
    D.silver_box(im, (206, 8, 504, 288))                    # lista
    D.silver_box(im, (8, 296, 504, 376))                    # pie: icono + descripción
    S.box(im, (16, 308, 72, 364), S.WELL, S.DIV, 5)         # pedestal del icono (57x57)
    G.save(im, "bagNoir")
    for i in range(1, 9):
        for suf in ("", "f"):
            n = "bag%d%s" % (i, suf)
            if os.path.exists(os.path.join(G.ORIG, "bag", n + ".png")): recolor(n, n)

if __name__ == "__main__":
    main()
