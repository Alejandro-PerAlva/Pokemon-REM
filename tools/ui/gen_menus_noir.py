#!/usr/bin/env python3
"""Oniria Noir: ficha de entrenador, opciones, título, carga/guardado y marco de diálogo global.
Originales en tools/ui/orig/menus/. Uso: python3 tools/ui/gen_menus_noir.py
La geometría debe coincidir con rem_ui.rb (REM_UI::TC_*, OPT_*, LOAD_*)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw, ImageFont
import gen_summary_noir as S
import gen_pokedex_noir as D
G = S.G
hexc, lerp = G.hexc, G.lerp
ORIGM = os.path.join(G.ORIG, "menus")

def save_to(im, rel):
    path = os.path.join(G.ROOT, rel)
    im.save(path, format="PNG"); print("ok", rel, im.size)

# ---------- ficha de entrenador ----------
TC_ROWS = [(56, 34, 38)]   # y0, alto, paso
def trainercard():
    im = S.base_bg()
    D.silver_box(im, (8, 8, 504, 48))                         # cabecera
    S.box(im, (368, 14, 498, 42), S.WELL, S.DIV, 6)           # insignia de ID
    for i in range(5):                                        # filas de datos
        y = 56 + 38 * i
        S.row_box(im, 8, y, 300, 34, 96)
    D.silver_box(im, (308, 56, 504, 250), hexc("0F1117"))     # retrato
    D.silver_box(im, (8, 258, 504, 376))                      # medallero
    S.box(im, (16, 264, 498, 288), hexc("12141B"), None, 4)
    for i in range(8):
        x = 20 + 60 * i
        S.box(im, (x, 298, x + 51, 349), S.WELL, S.DIV, 6)
    save_to(im, "Graphics/Pictures/trainercard.PNG")
    save_to(im, "Graphics/Pictures/trainercardf.PNG")
    tile = Image.new("RGBA", (8, 8), (14, 16, 21, 255))
    save_to(tile, "Graphics/Pictures/trainercardbg.png"); save_to(tile, "Graphics/Pictures/trainercardbgf.png")

# ---------- opciones ----------
def options():
    im = S.base_bg()
    D.silver_box(im, (8, 48, 504, 296))
    for i in range(7):
        y = 56 + 34 * i
        S.box(im, (16, y, 496, y + 31), hexc("1B1F2A"), S.DIV, 4)
    D.silver_box(im, (8, 304, 504, 376))
    save_to(im, "Graphics/Pictures/optionsNoir.png")

# ---------- botones en cápsula (menú principal y título) ----------
def pill_button(w, h, selected, box=None):
    """Cápsula obsidiana con bisel: borde, aro grafito, cuerpo en degradado y reflejo superior.
    box=(x0,y0,x1,y1) dentro de un lienzo (w,h); la selección añade halo platino-cian."""
    S4 = 4
    x0, y0, x1, y1 = box or (0, 0, w - 1, h - 1)
    big = Image.new("RGBA", (w * S4, h * S4), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
    def rr(i, col, grow=0):
        d.rounded_rectangle(((x0 + i - grow) * S4, (y0 + i - grow) * S4, (x1 + 1 - i + grow) * S4 - 1, (y1 + 1 - i + grow) * S4 - 1),
                            radius=((y1 - y0 + 1) // 2 + grow) * S4, fill=col)
    if selected:
        rr(0, (130, 215, 255, 55), 3); rr(0, (130, 215, 255, 120), 1.5)
    rr(0, (235, 247, 255, 255) if selected else (110, 118, 138, 255))
    rr(2, (30, 34, 45, 255))
    rr(3, (21, 23, 30, 255))
    im = big.resize((w, h), Image.LANCZOS); px = im.load()
    bh = y1 - y0
    for y in range(y0 + 3, y1 - 2):                       # degradado del cuerpo
        t = (y - y0 - 3) / max(1, bh - 6)
        col = lerp((36, 41, 54, 255), (21, 23, 30, 255), t)
        for x in range(x0, x1 + 1):
            if px[x, y][3] > 200 and px[x, y][:3] == (21, 23, 30): px[x, y] = col
    for x in range(x0 + bh // 2, x1 - bh // 2):           # reflejo de 1 px
        px[x, y0 + 4] = lerp(px[x, y0 + 4], (255, 255, 255, 255), 0.16)
    return im

# ---------- carga ----------
def loadscreen():
    save_to(S.base_bg(), "Graphics/Pictures/loadbg.png")
    W = 408; sheet = Image.new("RGBA", (W, 536), (0, 0, 0, 0))
    def panel(h, selected):
        p = Image.new("RGBA", (W, h), (0, 0, 0, 0))
        S.card(p, (0, 0, W - 1, h - 1), hexc("14161D"))
        d = ImageDraw.Draw(p, "RGBA")
        d.rounded_rectangle((3, 3, W - 4, h - 4), radius=6, outline=(30, 34, 45, 255), width=1)   # marco grafito interior
        if selected:
            for n, a in ((3, 60), (2, 120)):
                d.rounded_rectangle((n - 1, n - 1, W - n, h - n), radius=9, outline=(130, 215, 255, a), width=1)
            d.rounded_rectangle((0, 0, W - 1, h - 1), radius=8, outline=(235, 247, 255, 255), width=2)
        if h > 100:
            S.box(p, (6, 6, W - 7, 36), hexc("181B24"), None, 5)                        # tira superior
            S.box(p, (14, 46, 110, 160), S.WELL, S.DIV, 6)                              # retrato
            for (x0, y0, x1, y1) in ((124, 62, 250, 90), (124, 116, 250, 144), (262, 62, 394, 90), (262, 116, 394, 144)):
                S.box(p, (x0, y0, x1, y1), S.WELL, S.DIV, 5)                            # celdas: etiqueta + valor
            S.box(p, (118, 150, 394, 208), hexc("12141B"), S.DIV, 6)                    # fila del equipo
            for i in range(6):
                S.box(p, (122 + 46 * i, 154, 163 + 46 * i, 204), hexc("1B1F2A"), None, 8)  # píldoras
        return p
    sheet.paste(panel(222, False), (0, 0)); sheet.paste(panel(222, True), (0, 222))
    for k, sel in ((444, False), (490, True)):             # opciones del menú: cápsulas más estrechas
        sheet.paste(pill_button(W, 46, sel, (56, 5, 351, 40)), (0, k))
    save_to(sheet, "Graphics/Pictures/loadPanels.png")

# ---------- título ----------
def title():
    save_to(S.base_bg(), "Graphics/Titles/custom_background.png")
    save_to(Image.new("RGBA", (512, 384), (0, 0, 0, 0)), "Graphics/Titles/custom_plane.png")
    w, h = 250, 34
    im = pill_button(w, h, True, (3, 3, w - 4, h - 4))
    d = ImageDraw.Draw(im); f = S.font(22)
    t = "PULSA ENTER PARA EMPEZAR"
    hb = d.textbbox((0, 0), "H", font=f); tb = d.textbbox((0, 0), t, font=f)
    tx = (w - (tb[2] - tb[0])) / 2 - tb[0]; ty = (h - (hb[3] - hb[1])) / 2 - hb[1]
    d.text((int(tx), int(ty) + 1), t, font=f, fill=hexc("0D0E12")); d.text((int(tx), int(ty)), t, font=f, fill=(255, 255, 255, 255))
    save_to(im, "Graphics/Titles/pokestart.png")

# ---------- marco de diálogo global ----------
def speech_skin():
    """Recolorea speech hgss 1.png (96x48) conservando su estructura: fondo obsidiana, borde plata."""
    im = Image.open(os.path.join(ORIGM, "speech_hgss_1.png")).convert("RGBA"); px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if not a: continue
            l = (0.3 * r + 0.59 * g + 0.11 * b) / 255.0
            if r > 200 and b < 130: px[x, y] = (214, 219, 228, a) if g > 190 else (150, 158, 176, a)
            elif l < 0.30: px[x, y] = (13, 14, 18, a)
            elif b > 140 and l < 0.75: px[x, y] = (86, 96, 112, a)
            else: px[x, y] = (20, 22, 29, a)
    save_to(im, "Graphics/Windowskins/rem_noir_speech.png")

if __name__ == "__main__":
    trainercard(); options(); loadscreen(); title(); speech_skin()
