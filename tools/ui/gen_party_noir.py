#!/usr/bin/env python3
"""Rediseño "Oniria Noir" de la pantalla de equipo Pokémon. Originales en tools/ui/orig/party/.
Uso (raíz del proyecto): python3 tools/ui/gen_party_noir.py
Conserva dimensiones y rejillas exactas. La ranura de la franja de tipo está en x=245..249, filas 15..88
de cada panel (rem_ui.rb la rellena)."""
import os, sys, math
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw, ImageFont
import gen_oniria_noir as G

ROOT, PIC = G.ROOT, G.PIC
OR = os.path.join(G.ORIG, "party")
hexc, lerp, save = G.hexc, G.lerp, G.save
BEVEL, SILVER, STEEL = G.BEVEL, G.SILVER, G.STEEL
X0, X1, Y0, Y1 = 2, 253, 8, 95                       # cuerpo del panel (sin selección)
SX, SY0, SY1, SW = 245, 15, 88, 5                      # ranura de la franja de tipo

def orig(name): return Image.open(os.path.join(OR, name + ".png")).convert("RGBA")

def body_mask(kind, grow=0, S=4):
    """Máscara (L) del cuerpo; Round = esquinas izquierdas redondas, Rect = chaflán superior izquierdo."""
    m = Image.new("L", (256 * S, 98 * S), 0); d = ImageDraw.Draw(m)
    a, b, c, e = (X0 - grow) * S, (Y0 - grow) * S, (X1 + 1 + grow) * S - 1, (Y1 + 1 + grow) * S - 1
    if kind == "Round":
        d.rounded_rectangle((a, b, c, e), radius=22 * S, fill=255, corners=(True, False, False, True))
    else:
        ch = 10 * S
        d.polygon([(a + ch, b), (c, b), (c, e), (a, e), (a, b + ch)], fill=255)
    return m.resize((256, 98), Image.LANCZOS)

def shrink(kind, n): return body_mask(kind, -n)

def vgrad(top, bot):
    im = Image.new("RGBA", (256, 98)); d = ImageDraw.Draw(im)
    for y in range(98): d.line([(0, y), (256, y)], fill=lerp(top, bot, min(1, max(0, (y - Y0) / (Y1 - Y0)))))
    return im

STATES = {  # borde, resplandor, cuerpo arriba, cuerpo abajo, grosor
    "":       ((110, 118, 138), None,          (31, 35, 45), (21, 23, 30), 1),
    "Sel":    ((226, 244, 255), (130, 205, 255), (38, 44, 57), (26, 30, 40), 2),
    "Fnt":    ((178, 52, 46),  None,           (54, 18, 22), (34, 12, 16), 1),
    "SelFnt": ((236, 84, 72),  (230, 60, 50),  (62, 22, 26), (40, 14, 18), 2),
    "Swap":   ((74, 150, 255), None,           (20, 35, 62), (14, 24, 44), 1),
    "SelSwap": ((150, 224, 255), (64, 172, 255), (28, 46, 82), (18, 32, 58), 2),
}

def panel(kind, st):
    bc, glow, top, bot, bw = STATES[st]
    out = Image.new("RGBA", (256, 98), (0, 0, 0, 0))
    if glow:                                            # resplandor exterior de 2 px
        for n, a in ((2, 90), (1, 170)):
            ring = body_mask(kind, n)
            out.paste(glow + (a,), (0, 0), ring)
    out.paste(bc + (255,), (0, 0), body_mask(kind))
    out.paste(BEVEL, (0, 0), shrink(kind, bw))
    inner = shrink(kind, bw + 1)
    out.paste(vgrad(top + (255,), bot + (255,)), (0, 0), inner)
    o = out.load(); m = inner.load()
    for x in range(256):                                # reflejo de 1 px superior
        for y in range(98):
            if m[x, y] > 128 and (y == 0 or m[x, y - 1] <= 128):
                o[x, y] = lerp(o[x, y], (255, 255, 255, 255), 0.16); break
    for y in range(SY0 - 1, SY1 + 2):                   # ranura-gema de la franja de tipo
        for x in range(SX - 1, SX + SW + 1):
            edge = x in (SX - 1, SX + SW) or y in (SY0 - 1, SY1 + 1)
            o[x, y] = STEEL if edge else BEVEL
    return out

def blank():
    out = Image.new("RGBA", (256, 98), (0, 0, 0, 0))
    out.paste((24, 27, 35, 170), (0, 0), body_mask("Rect"))
    out.paste((12, 14, 18, 110), (0, 0), shrink("Rect", 1))
    return out

def background():
    W, H = 512, 384
    base = Image.new("RGBA", (W, H), (14, 16, 21, 255))
    rad = Image.radial_gradient("L").resize((W, H))               # 0 centro -> 255 bordes
    light = Image.new("RGBA", (W, H), (22, 25, 34, 255))
    base = Image.composite(base, light, rad)
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(grid)
    for x in range(0, W, 32): d.line([(x, 0), (x, H)], fill=(255, 255, 255, 9))
    for y in range(0, H, 32): d.line([(0, y), (W, y)], fill=(255, 255, 255, 9))
    save(Image.alpha_composite(base, grid), "partybg")

def hp_bar(st):
    """138x14: etiqueta PS + pista; la barra de color la dibuja el script en (32..127, 2..9)."""
    bc = {"": STEEL, "fnt": (150, 45, 45, 255), "swap": (70, 150, 255, 255)}[st]
    im = Image.new("RGBA", (138, 14), (0, 0, 0, 0)); o = im.load()
    pts = G.label_pixels(); minx = min(p[0] for p in pts); miny = min(p[1] for p in pts)
    for dx, dy in pts: o[3 + dx - minx, 1 + dy - miny] = hexc("F8B000")
    for y in range(0, 12):
        for x in range(30, 132):
            o[x, y] = bc if x in (30, 131) or y in (0, 11) else hexc("07080B")
    for x in range(31, 131): o[x, 1] = hexc("000000") if True else None
    return im

def cancel(w, h, sel):
    col = hexc("F5A524") if sel else (190, 198, 214, 255)
    return G.glow_button(w, h, col, sel, r=9, inset=1)

def tone(name, out, lo=(18, 20, 27), hi=(150, 158, 176)):
    im = orig(name); px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a:
                l = (0.3 * r + 0.59 * g + 0.11 * b) / 255.0
                px[x, y] = lerp(lo + (255,), hi + (255,), l)[:3] + (a,)
    save(im, out)

def statuses():
    cols = ["7A8594", "A24BC4", "F0592A", "F2B01E", "29B6E8", "C03028", "D060E0"]
    names = ["DOR", "ENV", "QUE", "PAR", "CON", "DEB", "PKRS"]
    z = G.fit_size(names, 17, 36)
    sheet = Image.new("RGBA", (44, 112), (0, 0, 0, 0))
    for i in range(7): sheet.paste(G.pill(44, 16, hexc(cols[i]), names[i], z, 1, 1, 42, 14), (0, 16 * i))
    save(sheet, "statuses")

def windowskin():
    im = orig("choice1"); px = im.load()
    for y in range(48):
        for x in range(48):
            r, g, b, a = px[x, y]
            if not a: continue
            l = (r + g + b) / 3.0
            if l > 225: px[x, y] = (18, 20, 27, 255)
            elif l > 190: px[x, y] = (40, 44, 56, 255)
            elif l > 110: px[x, y] = (96, 104, 122, 255)
            else: px[x, y] = (13, 14, 18, 255)
    im.save(os.path.join(ROOT, "Graphics", "Windowskins", "rem_noir_choice.png")); print("ok rem_noir_choice")

def selarrow():
    im = orig("selarrow"); px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a: px[x, y] = (236, 241, 248, 255) if r < 120 else (40, 44, 56, 255)
    save(im, "rem_selarrow")

if __name__ == "__main__":
    background()
    for kind in ("Round", "Rect"):
        for st in STATES: save(panel(kind, st), "partyPanel" + kind + st)
    save(blank(), "partyPanelBlank")
    for st, n in (("", "partyHP"), ("fnt", "partyHPfnt"), ("swap", "partyHPswap")): save(hp_bar(st), n)
    save(cancel(112, 48, False), "partyCancel"); save(cancel(112, 48, True), "partyCancelSel")
    save(cancel(112, 36, False), "partyCancelNarrow"); save(cancel(112, 36, True), "partyCancelSelNarrow")
    tone("partyBall", "partyBall"); tone("partyBallSel", "partyBallSel", (30, 34, 44), (200, 208, 224))
    statuses(); windowskin(); selarrow()
