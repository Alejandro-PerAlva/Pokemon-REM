#!/usr/bin/env python3
"""Rediseño "Oniria Noir" de la pantalla de Datos del Pokémon (4 páginas, sin cintas).
Originales en tools/ui/orig/summary/. Uso: python3 tools/ui/gen_summary_noir.py
La geometría de abajo debe coincidir con rem_ui.rb (REM_UI::SUM_*)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw, ImageFont
import gen_oniria_noir as G

hexc, lerp, save = G.hexc, G.lerp, G.save
SILVER, BEVEL, STEEL = G.SILVER, G.BEVEL, G.STEEL
INK = hexc("0D0E12"); OBS = hexc("14161D"); PANEL = hexc("181B24"); DIV = hexc("262B38"); WELL = hexc("0F1117")
FONT = G.FONT
CARD = (8, 48, 222, 376)            # tarjeta izquierda
PANEL_BOX = (232, 48, 504, 376)     # panel de datos derecho
STRIPE = (212, 58, 300, 5)          # x, y0, y1, ancho (franja de tipo en la tarjeta)
TABS = [("DATOS"), ("NOTAS"), ("STATS"), ("ATAQUES")]
TAB_X0, TAB_W, TAB_GAP, TAB_Y, TAB_H = 240, 62, 6, 8, 24
ROW_Y0, ROW_P, ROW_H, ROW_LABEL_W = 56, 34, 30, 100          # página 1
S3_HEAD_Y, S3_Y0, S3_P, S3_H = 56, 84, 32, 28                 # página 3
AB_Y, AB_H, KEY_Y, KEY_H = 284, 30, 326, 26
SLOT_X0, SLOT_X1, SLOT_Y0, SLOT_P, SLOT_H = 244, 488, 96, 64, 56   # página 4

def font(sz): return ImageFont.truetype(FONT, sz)

def base_bg():
    W, H = 512, 384
    bg = Image.new("RGBA", (W, H), (14, 16, 21, 255))
    rad = Image.radial_gradient("L").resize((W, H))
    bg = Image.composite(bg, Image.new("RGBA", (W, H), (22, 25, 34, 255)), rad)
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(grid)
    for x in range(0, W, 32): d.line([(x, 0), (x, H)], fill=(255, 255, 255, 8))
    for y in range(0, H, 32): d.line([(0, y), (W, y)], fill=(255, 255, 255, 8))
    return Image.alpha_composite(bg, grid)

def box(im, b, fill, border=None, r=4):
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle(b, radius=r, fill=fill, outline=border)

def card(im, b, fill=OBS):
    x0, y0, x1, y1 = b
    box(im, b, SILVER, None, 8)
    box(im, (x0 + 1, y0 + 1, x1 - 1, y1 - 1), hexc("1B1E28"), None, 7)
    box(im, (x0 + 2, y0 + 2, x1 - 2, y1 - 2), fill, None, 6)
    d = ImageDraw.Draw(im, "RGBA"); d.line([(x0 + 8, y0 + 3), (x1 - 8, y0 + 3)], fill=(255, 255, 255, 30))

def tabs(im, active):
    d = ImageDraw.Draw(im, "RGBA"); f = font(18)
    for i, t in enumerate(TABS):
        x = TAB_X0 + i * (TAB_W + TAB_GAP); on = (i == active)
        box(im, (x, TAB_Y, x + TAB_W - 1, TAB_Y + TAB_H - 1), SILVER if on else hexc("46506A"), None, 6)
        box(im, (x + 1, TAB_Y + 1, x + TAB_W - 2, TAB_Y + TAB_H - 2), hexc("2A3042") if on else OBS, None, 5)
        col = (255, 255, 255, 255) if on else (140, 150, 170, 255)
        hb = d.textbbox((0, 0), "H", font=f); tb = d.textbbox((0, 0), t, font=f)
        tx = x + (TAB_W - (tb[2] - tb[0])) / 2 - tb[0]; ty = TAB_Y + (TAB_H - (hb[3] - hb[1])) / 2 - hb[1]
        d.text((int(tx), int(ty) + 1), t, font=f, fill=INK); d.text((int(tx), int(ty)), t, font=f, fill=col)
        if on:
            d.line([(x + 8, TAB_Y + TAB_H + 2), (x + TAB_W - 9, TAB_Y + TAB_H + 2)], fill=(214, 219, 228, 255), width=2)

def showcase(im, stripe=True):
    """Pozo del sprite + plataforma + ranura de la franja de tipo."""
    box(im, (20, 124, 206, 284), WELL, DIV, 6)
    d = ImageDraw.Draw(im, "RGBA")
    d.ellipse((50, 250, 176, 274), fill=(30, 34, 46, 255), outline=(86, 96, 112, 255))
    d.ellipse((60, 254, 166, 270), fill=(20, 22, 29, 255))
    if stripe:
        x, y0, y1, w = STRIPE
        for y in range(y0 - 1, y1 + 2):
            for xx in range(x - 1, x + w + 1):
                edge = xx in (x - 1, x + w) or y in (y0 - 1, y1 + 1)
                d.point((xx, y), fill=STEEL if edge else BEVEL)
    # caja del objeto
    box(im, (16, 308, 214, 372), WELL, DIV, 5)
    d.line([(24, 332), (206, 332)], fill=DIV)

def row_box(im, x0, y, x1, h, lw):
    box(im, (x0, y, x1, y + h - 1), hexc("1B1F2A"), DIV, 4)
    box(im, (x0 + lw, y + 2, x1 - 3, y + h - 3), WELL, DIV, 3)

def panel(im, b=PANEL_BOX):
    card(im, b, PANEL)

def page_base(active, title_tabs=True):
    im = base_bg(); card(im, CARD); panel(im)
    if title_tabs: tabs(im, active)
    return im

def page1():
    im = page_base(0); showcase(im)
    for i in range(7): row_box(im, 240, ROW_Y0 + ROW_P * i, 496, ROW_H, ROW_LABEL_W)
    box(im, (240, 300, 496, 320), WELL, DIV, 4)                        # pista de EXP / medidor
    save(im, "summary1")

def page2():
    im = page_base(1); showcase(im)
    d = ImageDraw.Draw(im, "RGBA")
    box(im, (240, 56, 496, 370), hexc("12141B"), DIV, 4)
    for k in range(11): d.line([(248, 60 + 28 * k + 27), (488, 60 + 28 * k + 27)], fill=(255, 255, 255, 14))
    save(im, "summary2")

def page3():
    im = page_base(2); showcase(im)
    d = ImageDraw.Draw(im, "RGBA")
    for i in range(6):
        y = S3_Y0 + S3_P * i
        box(im, (240, y, 496, y + S3_H - 1), hexc("1B1F2A"), DIV, 4)
        box(im, (312, y + 2, 376, y + S3_H - 3), WELL, DIV, 3)        # Valor
        box(im, (380, y + 2, 436, y + S3_H - 3), WELL, DIV, 3)        # IV
        box(im, (440, y + 2, 492, y + S3_H - 3), WELL, DIV, 3)        # EV
    box(im, (240, AB_Y, 496, AB_Y + AB_H - 1), hexc("1B1F2A"), DIV, 4)
    box(im, (334, AB_Y + 2, 492, AB_Y + AB_H - 3), WELL, DIV, 3)
    box(im, (240, KEY_Y, 496, KEY_Y + KEY_H - 1), hexc("12141B"), DIV, 6)
    save(im, "summary3")

def slots(im, ys):
    for y in ys:
        box(im, (SLOT_X0, y, SLOT_X1, y + SLOT_H), hexc("1B1F2A"), DIV, 6)

def page4():
    im = page_base(3); showcase(im)
    slots(im, [SLOT_Y0 + SLOT_P * i for i in range(4)])
    save(im, "summary4")

def details(learning):
    im = base_bg(); card(im, CARD)
    panel(im, (232, 8 if learning else 48, 504, 376))
    d = ImageDraw.Draw(im, "RGBA")
    for i in range(3): row_box(im, 16, 120 + 32 * i, 214, 30, 104)
    box(im, (16, 222, 214, 372), WELL, DIV, 6)
    ys = ([22 + 64 * i for i in range(4)] + [298]) if learning else [SLOT_Y0 + SLOT_P * i for i in range(4)]
    slots(im, ys)
    save(im, "summary4learning" if learning else "summary4details")

def egg():
    im = base_bg(); card(im, CARD); panel(im); showcase(im, stripe=False)
    d = ImageDraw.Draw(im, "RGBA")
    box(im, (240, 56, 496, 370), hexc("12141B"), DIV, 4)
    save(im, "summaryEgg")

def movesel():
    """252x148: marco normal (platino) y marco de intercambio (ámbar); cada uno de 74 px de alto."""
    out = Image.new("RGBA", (252, 148), (0, 0, 0, 0)); d = ImageDraw.Draw(out)
    for i, (col, glow) in enumerate((((226, 244, 255), (130, 205, 255)), ((245, 165, 36), (245, 140, 20)))):
        y0 = 74 * i
        for n, a in ((3, 60), (2, 120)):
            d.rounded_rectangle((1 - n + 2, y0 + 1 - n + 2, 250 + n - 2, y0 + 63 + n - 2), radius=8, outline=glow + (a,), width=1)
        d.rounded_rectangle((1, y0 + 1, 250, y0 + 63), radius=7, outline=col + (255,), width=2)
    save(out, "summarymovesel")

def ability_card():
    w, h = 300, 176
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=10, fill=SILVER)
    d.rounded_rectangle((1, 1, w - 2, h - 2), radius=9, fill=BEVEL)
    d.rounded_rectangle((2, 2, w - 3, h - 3), radius=8, fill=(16, 18, 26, 246))
    d.line([(12, 40), (w - 13, 40)], fill=hexc("3A404D")); d.line([(12, 41), (w - 13, 41)], fill=BEVEL)
    save(im, "summaryAbilityCard")

if __name__ == "__main__":
    page1(); page2(); page3(); page4(); details(False); details(True); egg(); movesel(); ability_card()
