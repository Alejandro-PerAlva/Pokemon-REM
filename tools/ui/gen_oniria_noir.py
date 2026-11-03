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
STRIPE_Y0, STRIPE_Y1, STRIPE_W = 9, 47, 5   # debe coincidir con rem_ui.rb

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

# ------------------------------------------------------------------ databoxes (estilo Gen 5, finas)
STEEL = hexc("56606F")
BODY = (19, 21, 28, 236)

def label_pixels():
    """Pixeles naranjas de 'PS' tomados del original (relativos a x=90,y=36)."""
    im = src("battleFoeBoxS").load(); pts = []
    for y in range(36, 49):
        for x in range(88, 113):
            r, g, b, a = im[x, y]
            if a and r > 200 and 120 < g < 200 and b < 80: pts.append((x - 88, y - 36))
    return pts

def databox(name, side, kind):
    """kind: 'S' (jugador con tab de EXP), 'D' o 'F' (rival)."""
    W, H = 260, (86 if (side == "player" and kind == "S") else 62)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); o = out.load()
    T, B = 6, (75 if (side == "player" and kind == "S") else 53)
    bx = 16 if side == "foe" else 34
    def edge(y):
        return 236 + int((y - T) * 0.25) if side == "foe" else 28 - int((y - T) * (0.25 if B > 60 else 0.3))
    for y in range(T, B + 1):
        e = edge(y); xs = range(0, e + 1) if side == "foe" else range(e, W)
        for x in xs: o[x, y] = BODY
        o[e, y] = SILVER                                   # canto oblicuo afilado
        if y == T:
            for x in xs:
                k = 1.0 if side == "foe" and x > 120 or side == "player" and x < 140 else max(0.35, 1 - abs(x - (e)) / 260.0)
                o[x, y] = SILVER[:3] + (int(255 * min(1.0, max(0.35, k))),)       # reflejo que se desvanece
        if y == T + 1:
            for x in xs: o[x, y] = lerp(BODY, (255, 255, 255, 255), 0.07)       # brillo suave bajo el canto
        if y == B:
            for x in xs: o[x, y] = STEEL
    # ranura de la franja de tipo (gema): tapas y filo interior en acero, fondo bisel
    for y in range(STRIPE_Y0 - 1, STRIPE_Y1 + 2):
        e = edge(y)
        rng = list(range(e - STRIPE_W, e)) if side == "foe" else list(range(e + 1, e + 1 + STRIPE_W))
        for x in rng: o[x, y] = BEVEL if STRIPE_Y0 <= y <= STRIPE_Y1 else STEEL
        xi = (e - STRIPE_W - 1) if side == "foe" else (e + STRIPE_W + 1)
        o[xi, y] = STEEL
        o[xi + (-1 if side == "foe" else 1), y] = BEVEL    # aro oscuro del engaste de la gema
    # etiqueta PS y pista del medidor
    lx, ly = bx + 74, 36
    for dx, dy in label_pixels(): o[lx + dx, ly + dy] = hexc("F8B000")
    x0, x1, y0, y1 = bx + 99, bx + 200, 38, 47
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            o[x, y] = STEEL if x in (x0, x1) or y in (y0, y1) else hexc("07080B")
    for x in range(x0 - 1, x1 + 2):                          # engaste: aro oscuro, labio inferior claro, sombra interior
        o[x, y0 - 1] = BEVEL; o[x, y1 + 1] = lerp(BEVEL, SILVER, 0.35)
    for y in range(y0, y1 + 2): o[x0 - 1, y] = BEVEL; o[x1 + 1, y] = lerp(BEVEL, SILVER, 0.2)
    for x in range(x0 + 1, x1): o[x, y0 + 1] = hexc("000000")
    if side == "player" and kind == "S":                    # pista de EXP
        for y in range(65, 73):                                # única barra de EXP pegada al fondo de la caja
            for x in range(38, 236):
                o[x, y] = STEEL if x in (38, 235) or y in (65, 72) else hexc("07080B")
    save(out, name)

def safari_retone():
    im = src("battlePlayerSafari"); w, h = im.size; px = im.load(); out = Image.new("RGBA", im.size, (0, 0, 0, 0)); o = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0: continue
            if abs(r-g) < 12 and abs(g-b) < 12:
                o[x, y] = SILVER if r > 235 else (BEVEL if r < 110 else fill_color(r))
            else: o[x, y] = (r, g, b, a)
    save(out, "battlePlayerSafari")

def fill_color(v):
    t = max(0.0, min(1.0, (v - 150) / 80.0)); return lerp(OBS_BOT, OBS_TOP, t)

# ------------------------------------------------------------------ insignias HD (tipos y estados)
TYPE_LABEL = ["NORMAL","LUCHA","VOLAD.","VENENO","TIERRA","ROCA","BICHO","FANT.","ACERO","???",
              "FUEGO","AGUA","PLANTA","ELÉCTR.","PSÍQ.","HIELO","DRAGÓN","SINIES.","HADA"]

def fit_size(texts, size, width):
    f = lambda t, z: ImageDraw.Draw(Image.new('RGBA', (1, 1))).textlength(t, font=ImageFont.truetype(FONT, z))
    while size > 10 and any(f(t, size) > width for t in texts): size -= 1
    return size

def pill(w, h, col, text, size, fx=0, fy=0, fw=None, fh=None):
    """Píldora plana: relleno del color canónico, micro-borde más oscuro, texto blanco con sombra."""
    S = 4                                              # supersampling para bordes suaves
    fw = fw or w; fh = fh or h
    big = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
    dark = tuple(int(c * 0.55) for c in col[:3]) + (255,)
    box = (fx * S, fy * S, (fx + fw) * S - 1, (fy + fh) * S - 1)
    d.rounded_rectangle(box, radius=(fh * S) // 2 if fh <= 24 else 5 * S, fill=dark)
    d.rounded_rectangle((box[0] + S, box[1] + S, box[2] - S, box[3] - S), radius=max(fh * S // 2 - S, 2), fill=col)
    im = big.resize((w, h), Image.LANCZOS)
    f = ImageFont.truetype(FONT, size); dd = ImageDraw.Draw(im)
    hb = dd.textbbox((0, 0), "H", font=f); tb = dd.textbbox((0, 0), text, font=f)
    tx = fx + (fw - (tb[2] - tb[0])) / 2 - tb[0]; ty = fy + (fh - (hb[3] - hb[1])) / 2 - hb[1]
    tx, ty = int(round(tx)), int(round(ty))
    dd.text((tx, ty + 1), text, font=f, fill=(0, 0, 0, 150))      # sombra suave
    dd.text((tx, ty), text, font=f, fill=(255, 255, 255, 255))
    return im

def make_types():
    sheet = src("types").copy()                       # conserva las filas extra (19..23) del original
    sheet.paste((0, 0, 0, 0), (0, 0, 64, 28 * 19))
    z = fit_size(TYPE_LABEL, 21, 54)                        # un único tamaño para todas
    for t in range(19):
        sheet.paste(pill(64, 28, TYPE_COL[t], TYPE_LABEL[t], z, 1, 3, 62, 22), (0, 28 * t))
    save(sheet, "types")

def make_statuses():
    cols = ["7A8594", "A24BC4", "F0592A", "F2B01E", "29B6E8"]      # dormido, envenenado, quemado, paralizado, congelado
    names = ["DOR", "ENV", "QUE", "PAR", "CON"]
    sheet = Image.new("RGBA", (44, 80), (0, 0, 0, 0))
    z = fit_size(names, 17, 36)
    for i in range(5):
        sheet.paste(pill(44, 16, hexc(cols[i]), names[i], z, 1, 1, 42, 14), (0, 16 * i))
    save(sheet, "battleStatuses")

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
FONT = os.path.join(ROOT, "Fonts", "pkmnemn.ttf")

def rrect_mask(w, h, r):
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w-1, h-1), radius=r, fill=255); return m

def glow_button(w, h, col, selected, r=9):
    """Cuerpo grafito; borde luminoso de 1 px que se enciende (con resplandor interior) al seleccionar."""
    mask = rrect_mask(w, h, r)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); px = im.load()
    top, bot = (hexc("262B36"), hexc("191C24")) if selected else (hexc("1F232D"), hexc("14161D"))
    rings = [rrect_and_shrink(mask, n, r).load() for n in range(1, 6)]
    mp = mask.load(); glow = [0.55, 0.32, 0.17, 0.08] if selected else [0.0] * 4
    k = 1.0 if selected else 0.5
    for y in range(h):
        for x in range(w):
            if mp[x, y] == 0: continue
            body = lerp(top, bot, y / (h - 1))
            if rings[0][x, y] == 0:
                px[x, y] = tuple(int(col[i] * k + 13 * (1 - k)) for i in range(3)) + (255,)
            else:
                d = next((i for i in range(1, 5) if rings[i][x, y] == 0), 5)  # profundidad 1..4
                px[x, y] = lerp(body, col, glow[d - 1]) if d <= 4 else body
    return im

def rrect_and_shrink(mask, n, r):
    w, h = mask.size
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((n, n, w-1-n, h-1-n), radius=max(r-n, 1), fill=255)
    return m

def label(im, text, x0, w, h, size=27):
    f = ImageFont.truetype(FONT, size); d = ImageDraw.Draw(im)
    hb = d.textbbox((0, 0), "H", font=f); tb = d.textbbox((0, 0), text, font=f)
    tx = x0 + (w - (tb[2] - tb[0])) / 2 - tb[0]
    ty = (h - (hb[3] - hb[1])) / 2 - hb[1]                # centro vertical según altura de mayúscula
    tx, ty = int(round(tx)), int(round(ty))
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
    w, h = 320, 120
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w-1, h-1), radius=10, fill=SILVER)
    d.rounded_rectangle((1, 1, w-2, h-2), radius=9, fill=BEVEL)
    d.rounded_rectangle((2, 2, w-3, h-3), radius=8, fill=(16, 18, 26, 240))
    ln = hexc("3A404D")
    d.line([(10, 53), (w-11, 53)], fill=ln); d.line([(10, 54), (w-11, 54)], fill=BEVEL)
    for x in (107, 213): d.line([(x, 8), (x, 47)], fill=ln)            # 3 celdas
    save(im, "battleMoveInfo")

if __name__ == "__main__":
    databox("battleFoeBoxS", "foe", "F"); databox("battleFoeBoxD", "foe", "F")
    databox("battlePlayerBoxS", "player", "S"); databox("battlePlayerBoxD", "player", "D")
    safari_retone()
    make_command(); make_message(); make_fight()
    make_command_buttons(); make_fight_buttons(); make_move_info(); make_types(); make_statuses()
