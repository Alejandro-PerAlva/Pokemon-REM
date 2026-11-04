#!/usr/bin/env python3
"""Fondos "Oniria Noir" de la Pokédex (lista y ficha). Originales en tools/ui/orig/pokedex/.
Uso: python3 tools/ui/gen_pokedex_noir.py. La geometría debe coincidir con rem_ui.rb (REM_UI::DEX_*)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
import gen_summary_noir as S
G = S.G
hexc, save = G.hexc, G.save
SILVER, WELL, DIV, PANEL = G.SILVER, S.WELL, S.DIV, S.PANEL

def silver_box(im, b, fill=S.OBS, r=7):
    x0, y0, x1, y1 = b
    S.box(im, b, SILVER, None, r)
    S.box(im, (x0 + 1, y0 + 1, x1 - 1, y1 - 1), hexc("1B1E28"), None, r - 1)
    S.box(im, (x0 + 2, y0 + 2, x1 - 2, y1 - 2), fill, None, r - 2)

def listbg():
    im = S.base_bg()
    S.card(im, (8, 8, 222, 376))
    S.card(im, (232, 8, 504, 376), PANEL)
    S.box(im, (20, 20, 210, 236), WELL, DIV, 6)                  # pozo del sprite
    S.box(im, (20, 322, 210, 366), WELL, DIV, 6)                 # contador Vistos / Capturados
    ImageDraw.Draw(im).line([(115, 328), (115, 360)], fill=DIV)
    save(im, "pokedexbg")

def entrybg():
    im = S.base_bg()
    silver_box(im, (8, 8, 222, 56)); silver_box(im, (8, 62, 222, 98))
    silver_box(im, (8, 104, 222, 232), hexc("0F1117"))
    silver_box(im, (8, 240, 222, 376), hexc("12141B"))
    for b, title_h in (((232, 8, 504, 224), 28), ((232, 232, 504, 376), 28)):
        silver_box(im, b, PANEL)
        x0, y0, x1, y1 = b
        S.box(im, (x0 + 3, y0 + 3, x1 - 3, y0 + title_h), hexc("12141B"), None, 4)
    for i in range(6):                                          # pistas de las barras de estadísticas
        y = 40 + 30 * i
        S.box(im, (338, y + 8, 492, y + 20), WELL, DIV, 3)
    save(im, "pokedexEntry")

def blank():
    save(Image.new("RGBA", (512, 384), (0, 0, 0, 0)), "pokedexBlank")

if __name__ == "__main__":
    listbg(); entrybg(); blank()
