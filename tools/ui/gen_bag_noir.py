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


def pocket_icons():
    """bagPockets.png (128x32): 8 siluetas de 16x16; fila 0 = inactivas (grafito, ~60 %), fila 1 = activas (plata)."""
    from PIL import ImageDraw
    def mk():
        return Image.new("L", (16, 16), 0)
    icons = []
    m = mk(); d = ImageDraw.Draw(m)                                    # 1 Objetos: bolsita
    d.ellipse((2, 5, 13, 15), fill=255); d.rectangle((6, 2, 9, 6), fill=255); d.rectangle((5, 1, 10, 2), fill=255)
    d.line([(4, 6), (11, 6)], fill=0); icons.append(m)
    m = mk(); d = ImageDraw.Draw(m)                                    # 2 Medicinas: frasco
    d.rectangle((6, 1, 9, 5), fill=255); d.rectangle((5, 1, 10, 2), fill=255)
    d.rounded_rectangle((3, 5, 12, 15), radius=3, fill=255)
    d.rectangle((7, 8, 8, 12), fill=0); d.rectangle((5, 10, 10, 10), fill=0); icons.append(m)
    m = mk(); d = ImageDraw.Draw(m)                                    # 3 Poké Ball
    d.ellipse((1, 1, 14, 14), fill=255); d.rectangle((1, 7, 14, 8), fill=0)
    d.ellipse((5, 5, 10, 10), fill=0); d.ellipse((6, 6, 9, 9), fill=255); icons.append(m)
    m = mk(); d = ImageDraw.Draw(m)                                    # 4 MT/MO: disco
    d.ellipse((1, 1, 14, 14), fill=255); d.ellipse((5, 5, 10, 10), fill=0); d.arc((3, 3, 12, 12), 200, 290, fill=0); icons.append(m)
    m = mk(); d = ImageDraw.Draw(m)                                    # 5 Bayas
    d.ellipse((2, 5, 13, 15), fill=255); d.polygon([(8, 5), (13, 1), (14, 5), (10, 7)], fill=255)
    d.line([(8, 5), (8, 2)], fill=255); d.point((5, 8), fill=0); icons.append(m)
    m = mk(); d = ImageDraw.Draw(m)                                    # 6 Cartas
    d.rectangle((1, 3, 14, 12), fill=255); d.line([(1, 3), (7, 8), (14, 3)], fill=0); icons.append(m)
    m = mk(); d = ImageDraw.Draw(m)                                    # 7 Combate
    d.line([(2, 2), (13, 13)], fill=255, width=3); d.line([(13, 2), (2, 13)], fill=255, width=3); icons.append(m)
    m = mk(); d = ImageDraw.Draw(m)                                    # 8 Objetos Clave: llave
    d.ellipse((1, 4, 8, 11), fill=255); d.ellipse((3, 6, 6, 9), fill=0)
    d.rectangle((8, 6, 14, 8), fill=255); d.rectangle((11, 9, 12, 12), fill=255); d.rectangle((14, 9, 14, 11), fill=255)
    icons.append(m)
    sheet = Image.new("RGBA", (128, 32), (0, 0, 0, 0))
    for i, m in enumerate(icons):
        for row, (col, a) in enumerate((((80, 86, 102), 150), ((214, 219, 228), 255))):
            layer = Image.new("RGBA", (16, 16), col + (255,))
            layer.putalpha(m.point(lambda v, a=a: a if v > 0 else 0))
            sheet.paste(layer, (16 * i, 16 * row))
    G.save(sheet, "bagPockets")


if __name__ == "__main__":
    pocket_icons()
