#!/usr/bin/env python3
"""Genera los assets de combate "Oniria Noir" en Graphics/Pictures/.
Uso (desde la raíz del proyecto): python3 tools/ui/gen_oniria_noir.py
Parte de los PNG originales (copiados a tools/ui/orig/ la primera vez) para conservar
siluetas, etiqueta PS, medidores y ranuras; todo es idempotente.
Franja de tipo: las cajas de datos llevan una ranura de 5 px (color #0D0E12) pegada al borde
oblicuo (derecha en rival, izquierda en jugador) entre las filas STRIPE_Y0..STRIPE_Y1;
rem_ui.rb la rellena en tiempo de ejecución con el color del tipo.
"""
import os, shutil, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PIC = os.path.join(ROOT, "Graphics", "Pictures")
ORIG = os.path.join(ROOT, "tools", "ui", "orig")
os.makedirs(ORIG, exist_ok=True)

def hexc(h, a=255):
    h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)

OBS_TOP, OBS_BOT = hexc("1D212A"), hexc("14161D")
SILVER, BEVEL = hexc("D6DBE4"), hexc("0D0E12")
STRIPE_Y0, STRIPE_Y1, STRIPE_W = 2, 52, 5   # debe coincidir con rem_ui.rb

TYPE_COL = ["A8A77A","C22E28","A98FF3","A33EA1","E2BF65","B6A136","A6B91A","735797","B7B7CE",
            "68A090","EE8130","6390F0","7AC74C","F7D02C","F95587","96D9D6","6F35FC","705746","D685AD"]
TYPE_COL = [hexc(c) for c in TYPE_COL]

def src(name):
    o = os.path.join(ORIG, name + ".png")
    if not os.path.exists(o):
        shutil.copy(os.path.join(PIC, name + ".png"), o)
    return Image.open(o).convert("RGBA")

def save(im, name):
    im.save(os.path.join(PIC, name + ".png"))
    print("ok", name, im.size)

def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(4))

def fill_color(v):
    t = max(0.0, min(1.0, (v - 150) / 80.0))
    return lerp(OBS_BOT, OBS_TOP, t)

# ------------------------------------------------------------------ databoxes
def databox(name, side, stripe=True):
    im = src(name); w, h = im.size; px = im.load(); out = Image.new("RGBA", im.size, (0, 0, 0, 0)); o = out.load()
    opaque = lambda x, y: 0 <= x < w and 0 <= y < h and px[x, y][3] > 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0: continue
            edge = not (opaque(x-1, y) and opaque(x+1, y) and opaque(x, y-1) and opaque(x, y+1))
            if r > 235 and g > 235 and b > 235 and edge: o[x, y] = SILVER       # halo exterior
            elif r > 235 and g > 235 and b > 235: o[x, y] = hexc("07080B")        # interior blanco = pista del medidor
            elif abs(r-g) < 12 and abs(g-b) < 12:
                v = r
                if v < 110: o[x, y] = BEVEL if not (36 <= y <= 48) else hexc("56606F")
                else: o[x, y] = fill_color(v)
            else: o[x, y] = (r, g, b, a)                                       # naranja de "PS"
    # contorno oscuro de la etiqueta PS: se mantiene bevel (no acero)
    for y in range(36, 49):
        for x in range(0, 114 if side == "foe" else 132):
            if o[x, y][:3] == (0x56, 0x60, 0x6F): o[x, y] = BEVEL
    # ranura de la franja de tipo
    for y in (range(STRIPE_Y0, STRIPE_Y1 + 1) if stripe else []):
        xs = [x for x in range(w) if o[x, y][3] > 0]
        if side == "foe":
            xe = max(xs); rng = range(xe - STRIPE_W, xe)
        else:
            xe = min(xs); rng = range(xe + 1, xe + 1 + STRIPE_W)
        for x in rng: o[x, y] = BEVEL
    # el borde plateado exterior siempre presente en la ranura
    save(out, name)

# ------------------------------------------------------------------ barras
def bar_base(w, h, accent=SILVER):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for y in range(h):
        d.line([(0, y), (w, y)], fill=lerp(OBS_TOP, OBS_BOT, y / (h - 1)))
    d.rectangle([0, 0, w-1, h-1], outline=BEVEL)
    d.line([(0, 0), (w-1, 0)], fill=SILVER)                # filo lunar superior
    d.line([(0, 1), (w-1, 1)], fill=hexc("2B303B"))
    return im

def panel(im, box, fill, border=SILVER, r=4):
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle(box, radius=r, fill=BEVEL, outline=None)
    x0, y0, x1, y1 = box
    d.rounded_rectangle((x0+1, y0+1, x1-1, y1-1), radius=max(r-1, 0), fill=fill, outline=border)

def make_command():
    im = bar_base(512, 96)
    panel(im, (5, 6, 247, 91), (10, 11, 15, 235))
    d = ImageDraw.Draw(im); d.line([(250, 10), (250, 88)], fill=hexc("2B303B"))
    save(im, "battleCommand")

def make_message():
    im = bar_base(512, 96)
    panel(im, (6, 8, 505, 90), (10, 11, 15, 235))
    save(im, "battleMessage")

def make_fight():
    im = bar_base(512, 96)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 4, 383, 93), radius=5, fill=hexc("0F1117"), outline=hexc("2B303B"))
    panel(im, (388, 6, 506, 90), (10, 11, 15, 235))
    save(im, "battleFight")

# ------------------------------------------------------------------ botones
FONT = os.path.join(ROOT, "Fonts", "pkmnem.ttf")

def rrect_mask(w, h, r):
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w-1, h-1), radius=r, fill=255); return m

def glow_button(w, h, col, selected, r=9):
    """Cuerpo grafito sólido; el color vive solo en el bisel (más intenso al seleccionar)."""
    mask = rrect_mask(w, h, r)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); px = im.load()
    body_top, body_bot = (hexc("2A2F3B"), hexc("1B1E27")) if selected else (hexc("1F232D"), hexc("14161D"))
    inner = mask.copy(); inner = Image.eval(rrect_and_shrink(mask, 2, r), lambda v: v)
    ring2 = rrect_and_shrink(mask, 3, r)
    mp, ip, rp = mask.load(), inner.load(), ring2.load()
    k = 1.0 if selected else 0.62
    for y in range(h):
        for x in range(w):
            if mp[x, y] == 0: continue
            if ip[x, y] == 0:                      # borde exterior 2 px: color de acción
                c = tuple(int(col[i] * k + 13 * (1 - k)) for i in range(3)) if not selected else col[:3]
                px[x, y] = c + (255,)
            elif rp[x, y] == 0:                    # halo interior (resplandor)
                a = 0.55 if selected else 0.22
                bc = lerp(body_top, col, a); px[x, y] = bc
            else:
                px[x, y] = lerp(body_top, body_bot, y / (h - 1))
    if selected:                                    # destello superior
        for x in range(r, w - r): px[x, 3] = lerp(px[x, 3], SILVER, 0.35)
    return im

def rrect_and_shrink(mask, n, r):
    w, h = mask.size
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((n, n, w-1-n, h-1-n), radius=max(r-n, 1), fill=255)
    return m

def label(im, text, x0, w, h, size=16):
    f = ImageFont.truetype(FONT, size); d = ImageDraw.Draw(im)
    tw = d.textlength(text, font=f); tx = x0 + (w - tw) / 2; ty = (h - size) / 2 - 2
    for dx, dy in ((1, 1), (0, 1), (1, 0), (-1, 0), (0, -1), (-1, -1), (1, -1), (-1, 1)):
        d.text((tx+dx, ty+dy), text, font=f, fill=BEVEL)
    d.text((tx, ty), text, font=f, fill=(255, 255, 255, 255))

def make_command_buttons():
    cols = {"LUCHAR": "E0243C", "POKéMON": "22C070", "MOCHILA": "F5A524", "HUIR": "22C8E8",
            "LLAMAR": "22C8E8", "BALL": "E0243C", "ROCA": "22C070", "CEBO": "F5A524", "BALL2": "F5A524"}
    names = ["LUCHAR", "POKéMON", "MOCHILA", "HUIR", "LLAMAR", "BALL", "ROCA", "CEBO", "BALL2"]
    sheet = Image.new("RGBA", (260, 414), (0, 0, 0, 0))
    for i, n in enumerate(names):
        for s in (0, 1):
            b = glow_button(130, 46, hexc(cols[n]), bool(s))
            label(b, n.replace("2", ""), 0, 130, 46)
            sheet.paste(b, (130 * s, 46 * i))
    save(sheet, "battleCommandButtons")

def make_fight_buttons():
    sheet = Image.new("RGBA", (384, 874), (0, 0, 0, 0))
    for t in range(19):
        for s in (0, 1):
            sheet.paste(glow_button(192, 46, TYPE_COL[t], bool(s)), (192 * s, 46 * t))
    save(sheet, "battleFightButtons")

# ------------------------------------------------------------------ tarjeta de info
def make_move_info():
    w, h = 320, 140
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w-1, h-1), radius=10, fill=SILVER)                     # borde platino
    d.rounded_rectangle((1, 1, w-2, h-2), radius=9, fill=BEVEL)                       # bisel interior
    d.rounded_rectangle((2, 2, w-3, h-3), radius=8, fill=(16, 18, 26, 240))
    d.line([(10, 33), (w-11, 33)], fill=hexc("3A404D")); d.line([(10, 34), (w-11, 34)], fill=BEVEL)  # separador
    save(im, "battleMoveInfo")

if __name__ == "__main__":
    for n, s in (("battleFoeBoxS", "foe"), ("battleFoeBoxD", "foe"), ("battlePlayerBoxS", "player"), ("battlePlayerBoxD", "player")):
        databox(n, s)
    databox("battlePlayerSafari", "player", stripe=False)
    make_command(); make_message(); make_fight()
    make_command_buttons(); make_fight_buttons(); make_move_info()
