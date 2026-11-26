"""Generate clean, non-blocky VS intro bars and trainer portraits (256x128) for Pokémon REM.

Generates Graphics/Transitions/vsBar<ID>.png and vsTrainer<ID>.png for:
  - Protagonists: 0 (PLAYER_M), 1 (PLAYER_F)
  - 20 Key Opponents:
      2 RIVAL_M (Lucian), 3 RIVAL_F (Guiomar), 4 PROFESSOR (Ambrosio),
      5..12 LEADER_1..8 (Matilde..Beltran),
      13..16 ELITE_1..4 (Nicodemo, Oriana, Anteo, Leucotea),
      17 CHAMPION (Rolanda Altamira),
      20 MORFEO_GENERAL_M (Alarico), 21 MORFEO_GENERAL_F (Zenobia),
      22 MORFEO_SUBCAPTAIN (Ariadna), 23 MORFEO_LEADER (Eliseo).

Technique:
  - Preserves original sprite art cleanly without blurry smudging or 4x4 mosaic blocks:
      * 2x2 sprites downsample to native 1x1 -> double Scale2x (EPX) -> smooth Lanczos crop + crisp alpha edge
      * Fine 1x1 sprites run single Scale2x (EPX) -> smooth Lanczos crop + crisp alpha edge
  - Seamless 256px horizontal AnimatedPlane speed bars matching REM Noir border + character palette.
  - Frames characters away from the center VS logo zone so faces and weapons/props remain unobscured.
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
CHAR_DIR = ROOT / "Graphics" / "Characters"
TR_DIR = ROOT / "Graphics" / "Transitions"
PREV_DIR = ROOT / "previews"

NOIR_BG = (13, 14, 18)


def scale2x(im: Image.Image) -> Image.Image:
    """AdvMAME2x / EPX pixel-art scaler preserving sharp outlines and smooth diagonals."""
    w, h = im.size
    p = im.load()
    out = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    op = out.load()
    for y in range(h):
        ym = max(0, y - 1)
        yp = min(h - 1, y + 1)
        for x in range(w):
            xm = max(0, x - 1)
            xp = min(w - 1, x + 1)
            P = p[x, y]
            A = p[x, ym]
            B = p[xp, y]
            C = p[xm, y]
            D = p[x, yp]
            if A != D and C != B:
                e0 = A if C == A else P
                e1 = B if A == B else P
                e2 = C if D == C else P
                e3 = D if B == D else P
            else:
                e0 = e1 = e2 = e3 = P
            op[2 * x, 2 * y] = e0
            op[2 * x + 1, 2 * y] = e1
            op[2 * x, 2 * y + 1] = e2
            op[2 * x + 1, 2 * y + 1] = e3
    return out


def measure_err2x2(im: Image.Image) -> int:
    px = im.load()
    w, h = im.size
    return sum(
        1
        for y in range(0, h - 1, 2)
        for x in range(0, w - 1, 2)
        if not (px[x, y] == px[x + 1, y] == px[x, y + 1] == px[x + 1, y + 1])
    )


def prepare_bust(
    tid: int,
    crop_frac: float = 0.68,
    flip: bool = False,
    target_h: int = 116,
    offset_y_frac: float = 0.0,
) -> Image.Image:
    """Produces a crisp, high-resolution bust crop without 4x4 pixelation or broken edges."""
    raw = Image.open(CHAR_DIR / f"trainer{tid:03d}.png").convert("RGBA")
    if flip:
        raw = raw.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    bb = raw.getbbox()
    spr = raw.crop(bb)

    err2 = measure_err2x2(spr)
    if err2 <= 35:
        # True 2x2 grid sprite -> extract native 1x1 then smooth twice via Scale2x
        nat = spr.resize((max(1, spr.width // 2), max(1, spr.height // 2)), Image.Resampling.NEAREST)
        hi = scale2x(scale2x(nat))
    else:
        # Already fine 1x1 detail -> single Scale2x pass preserves eye/hair clarity
        hi = scale2x(spr)

    y0 = int(round(hi.height * offset_y_frac))
    y1 = min(hi.height, int(round(hi.height * (offset_y_frac + crop_frac))))
    bust = hi.crop((0, y0, hi.width, max(y0 + 16, y1)))

    # Scale cleanly to target card height while avoiding extreme width overflow (>194px)
    scale = target_h / float(bust.height)
    tw = int(round(bust.width * scale))
    if tw > 194:
        scale = 194.0 / float(bust.width)
        tw = 194
        target_h = int(round(bust.height * scale))

    resized = bust.resize((tw, target_h), Image.Resampling.LANCZOS)
    px = resized.load()
    # Hard crisp sprite edge cleanup (avoids muddy semi-transparent grey fringes)
    for y in range(target_h):
        for x in range(tw):
            r, g, b, a = px[x, y]
            if a >= 130:
                px[x, y] = (r, g, b, 255)
            else:
                px[x, y] = (0, 0, 0, 0)
    return resized


def make_vs_bar(
    c_dark: tuple[int, int, int],
    c_mid: tuple[int, int, int],
    c_glow: tuple[int, int, int],
    trim: tuple[int, int, int],
    seed: int = 1,
) -> Image.Image:
    """Creates a seamless 256x128 horizontally tiling VS speed bar with REM Noir top/bottom framing."""
    im = Image.new("RGBA", (256, 128), (*NOIR_BG, 255))
    px = im.load()

    # Smooth central energy gradient + multi-layer seamless horizontal speed streaks (exact period 256px)
    for y in range(6, 122):
        # Vertical energy envelope peaking along mid-band (y=64)
        dy = abs((y - 64.0) / 58.0)
        core = max(0.0, 1.0 - dy) ** 1.28
        horizon_glow = max(0.0, 1.0 - abs(y - 64.0) / 14.0) ** 2.0

        # Deterministic per-row streak amplitude so streaks feel dynamic and seamless at x=0..255
        row_hash = ((y * 1103515245 + seed * 12345) >> 16) & 0xFF
        is_streak = (row_hash % 7) in (0, 1)
        phase1 = (row_hash * 0.13 + seed * 0.7) * math.pi
        phase2 = (row_hash * 0.29 - seed * 0.4) * math.pi

        for x in range(256):
            ang1 = 2.0 * math.pi * (x / 256.0) + phase1
            ang2 = 2.0 * math.pi * ((x * 2) / 256.0) + phase2
            wave1 = max(0.0, math.sin(ang1)) ** 4
            wave2 = max(0.0, math.cos(ang2)) ** 5

            streak_boost = (0.42 * wave1 + 0.24 * wave2) if is_streak else (0.10 * wave1)
            mix = min(1.0, core * 0.78 + horizon_glow * 0.28 + streak_boost)

            r = int(c_dark[0] * (1.0 - mix) + c_mid[0] * mix)
            g = int(c_dark[1] * (1.0 - mix) + c_mid[1] * mix)
            b = int(c_dark[2] * (1.0 - mix) + c_mid[2] * mix)

            glow_k = min(1.0, max(0.0, (horizon_glow * 0.65 + streak_boost * 0.85)))
            r = min(255, int(r + (c_glow[0] - r) * glow_k * 0.75))
            g = min(255, int(g + (c_glow[1] - g) * glow_k * 0.75))
            b = min(255, int(b + (c_glow[2] - b) * glow_k * 0.75))
            px[x, y] = (r, g, b, 255)

    # Crisp Noir double metallic top/bottom border (`y=0..5` and `y=122..127`)
    trim_dk = (int(trim[0] * 0.55), int(trim[1] * 0.55), int(trim[2] * 0.55))
    for x in range(256):
        px[x, 0] = (*NOIR_BG, 255)
        px[x, 1] = (*NOIR_BG, 255)
        px[x, 2] = (*trim_dk, 255)
        px[x, 3] = (*trim, 255)
        px[x, 4] = (*trim_dk, 255)
        px[x, 5] = (*NOIR_BG, 255)

        px[x, 122] = (*NOIR_BG, 255)
        px[x, 123] = (*trim_dk, 255)
        px[x, 124] = (*trim, 255)
        px[x, 125] = (*trim_dk, 255)
        px[x, 126] = (*NOIR_BG, 255)
        px[x, 127] = (*NOIR_BG, 255)

    return im


def draw_emblem(card: Image.Image, side: str, kind: str, trim: tuple[int, int, int], glow: tuple[int, int, int]):
    """Draws a crisp subtle geometric emblem + diagonal slash accent in the outer corner."""
    ov = Image.new("RGBA", (256, 128), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)

    # Outer corner Noir diagonal badge backing behind the character (never cuts across hands or faces!)
    if side == "right":
        poly = [(196, 6), (255, 6), (255, 121), (170, 121)]
        ex, ey = 228, 28
    else:
        poly = [(0, 6), (60, 6), (86, 121), (0, 121)]
        ex, ey = 28, 28
    dr.polygon(poly, fill=(13, 14, 18, 95))

    # Diagonal bright hairline accent framing the outer emblem wedge
    if side == "right":
        dr.line([(196, 6), (170, 121)], fill=(*trim, 145), width=2)
    else:
        dr.line([(60, 6), (86, 121)], fill=(*trim, 145), width=2)

    # Crisp clean outer-corner faction/rank sigil (`crown`, `morfeo`, `clock`, `star`, `pokeball`, `badge`)
    col_ring = (*trim, 185)
    col_fill = (*glow, 55)
    dr.ellipse([ex - 14, ey - 14, ex + 14, ey + 14], fill=col_fill, outline=col_ring, width=2)

    if kind == "crown":
        pts = [(ex - 9, ey + 5), (ex - 9, ey - 4), (ex - 4, ey + 1), (ex, ey - 7), (ex + 4, ey + 1), (ex + 9, ey - 4), (ex + 9, ey + 5)]
        dr.polygon(pts, fill=(*trim, 215))
    elif kind == "morfeo":
        # Stylized Team Morfeo crescent + eye dot
        dr.pieslice([ex - 9, ey - 9, ex + 9, ey + 9], 35, 325, fill=(*trim, 205))
        dr.ellipse([ex - 4, ey - 6, ex + 8, ey + 6], fill=(13, 14, 18, 180))
        dr.ellipse([ex + 2, ey - 2, ex + 6, ey + 2], fill=(*glow, 225))
    elif kind == "clock":
        dr.ellipse([ex - 8, ey - 8, ex + 8, ey + 8], outline=(*trim, 220), width=2)
        dr.line([(ex, ey), (ex, ey - 6)], fill=(*glow, 230), width=2)
        dr.line([(ex, ey), (ex + 5, ey + 2)], fill=(*glow, 230), width=2)
    elif kind == "star":
        pts = []
        for k in range(10):
            ang = -math.pi / 2 + k * math.pi / 5
            rad = 9 if k % 2 == 0 else 4
            pts.append((ex + rad * math.cos(ang), ey + rad * math.sin(ang)))
        dr.polygon(pts, fill=(*trim, 215))
    elif kind == "badge":
        # Crisp octagonal Pokémon league gem/badge
        pts = [(ex - 4, ey - 9), (ex + 4, ey - 9), (ex + 9, ey - 4), (ex + 9, ey + 4),
               (ex + 4, ey + 9), (ex - 4, ey + 9), (ex - 9, ey + 4), (ex - 9, ey - 4)]
        dr.polygon(pts, outline=(*trim, 215), fill=(*glow, 85))
        dr.ellipse([ex - 3, ey - 3, ex + 3, ey + 3], fill=(*trim, 225))
    else:  # "pokeball"
        dr.arc([ex - 8, ey - 8, ex + 8, ey + 8], 0, 360, fill=(*trim, 210), width=2)
        dr.line([(ex - 8, ey), (ex + 8, ey)], fill=(*trim, 210), width=2)
        dr.ellipse([ex - 3, ey - 3, ex + 3, ey + 3], fill=(*glow, 230), outline=(*trim, 220))

    # Clip emblem cleanly inside [6..121] band
    ep = ov.load()
    for y in list(range(0, 6)) + list(range(122, 128)):
        for x in range(256):
            ep[x, y] = (0, 0, 0, 0)
    card.alpha_composite(ov)


def silhouette_tint(spr: Image.Image, col: tuple[int, int, int], alpha: int) -> Image.Image:
    sh = Image.new("RGBA", spr.size, (0, 0, 0, 0))
    sp, dp = spr.load(), sh.load()
    w, h = spr.size
    for y in range(h):
        for x in range(w):
            if sp[x, y][3] > 128:
                dp[x, y] = (*col, alpha)
    return sh


def make_vs_trainer(
    tid: int,
    side: str,  # "left" for player, "right" for boss/rival
    flip: bool,
    crop_frac: float,
    offset_y_frac: float,
    c_glow: tuple[int, int, int],
    trim: tuple[int, int, int],
    emblem: str,
    x_center: int | None = None,
) -> Image.Image:
    card = Image.new("RGBA", (256, 128), (0, 0, 0, 0))
    draw_emblem(card, side, emblem, trim, c_glow)

    bust = prepare_bust(tid, crop_frac=crop_frac, flip=flip, target_h=115, offset_y_frac=offset_y_frac)
    bw, bh = bust.size

    if x_center is None:
        # Leave x=0..62 (right) and x=194..255 (left) clear of central VS splash!
        x_center = 104 if side == "left" else 152

    px0 = max(4, min(252 - bw, x_center - bw // 2))
    py0 = 122 - bh

    # Directional rim glow + Noir drop shadow behind portrait for 3D separation
    glow_sh = silhouette_tint(bust, c_glow, 130)
    dark_sh = silhouette_tint(bust, (10, 12, 16), 190)

    gx = -3 if side == "right" else 3
    sx = 5 if side == "right" else -5
    card.alpha_composite(glow_sh, (max(0, px0 + gx), max(0, py0 - 1)))
    card.alpha_composite(dark_sh, (max(0, px0 + sx), max(0, py0 + 2)))
    card.alpha_composite(bust, (px0, py0))

    # Clean clip at y=122 so it rests right on the bottom bar trim (`y=122..127`) without obscuring frame
    cp = card.load()
    for y in range(122, 128):
        for x in range(256):
            cp[x, y] = (0, 0, 0, 0)
    return card


# Full specification: (id, label, side, flip, crop_frac, offset_y, c_dark, c_mid, c_glow, trim, emblem, x_center)
SPECS = [
    # Protagonists (mirrored left-to-right so they face the rival on the right!)
    (0, "Prota M", "left", True, 0.65, 0.0, (14, 24, 38), (38, 92, 128), (118, 224, 232), (168, 232, 238), "pokeball", 102),
    (1, "Prota F", "left", True, 0.64, 0.0, (32, 16, 30), (116, 48, 84), (244, 136, 178), (242, 186, 206), "pokeball", 102),
    # 20 Key Opponents
    (2, "Rival: Lucian", "right", False, 0.64, 0.0, (16, 26, 48), (44, 84, 146), (132, 198, 250), (168, 214, 248), "star", 148),
    (3, "Rival: Guiomar", "right", True, 0.63, 0.0, (44, 18, 12), (162, 66, 24), (252, 178, 68), (248, 196, 98), "star", 148),
    (4, "Prof. Ambrosio", "right", False, 0.64, 0.0, (34, 16, 28), (94, 42, 68), (218, 176, 114), (222, 188, 108), "clock", 148),
    (5, "Lider 1: Matilde (Normal)", "right", True, 0.62, 0.0, (42, 28, 28), (154, 78, 72), (242, 218, 168), (238, 214, 158), "badge", 150),
    (6, "Lider 2: Ismael (Agua)", "right", False, 0.62, 0.0, (12, 30, 58), (28, 106, 176), (104, 224, 244), (146, 232, 248), "badge", 158),
    (7, "Lider 3: Greta (Acero)", "right", True, 0.66, 0.0, (24, 28, 36), (78, 92, 112), (236, 178, 66), (210, 218, 228), "badge", 148),
    (8, "Lider 4: Genzo (Lucha)", "right", True, 0.64, 0.0, (42, 14, 16), (138, 36, 38), (238, 126, 94), (222, 198, 162), "badge", 150),
    (9, "Lider 5: Fausto (Roca)", "right", True, 0.65, 0.0, (38, 24, 18), (112, 72, 46), (238, 194, 96), (232, 192, 102), "badge", 148),
    (10, "Lider 6: Hildegarda (Planta)", "right", False, 0.64, 0.0, (14, 38, 22), (44, 122, 62), (148, 228, 118), (168, 226, 134), "badge", 152),
    (11, "Lider 7: Isolda (Hielo)", "right", True, 0.64, 0.0, (18, 34, 58), (68, 134, 198), (196, 240, 255), (218, 244, 255), "badge", 150),
    (12, "Lider 8: Beltran (Fuego)", "right", False, 0.62, 0.0, (42, 16, 12), (176, 58, 24), (252, 192, 64), (246, 164, 62), "badge", 152),
    (13, "Alto Mando 1: Nicodemo", "right", True, 0.64, 0.0, (36, 28, 12), (126, 94, 34), (176, 218, 94), (224, 188, 86), "badge", 150),
    (14, "Alto Mando 2: Oriana", "right", False, 0.64, 0.0, (24, 18, 52), (82, 54, 146), (228, 118, 232), (206, 152, 248), "badge", 148),
    (15, "Alto Mando 3: Anteo", "right", False, 0.64, 0.0, (20, 16, 28), (84, 26, 46), (214, 62, 86), (176, 182, 206), "badge", 150),
    (16, "Alto Mando 4: Leucotea", "right", False, 0.60, 0.0, (44, 22, 14), (148, 76, 42), (236, 188, 114), (232, 194, 128), "badge", 144),
    (17, "Campeona: Rolanda Altamira", "right", False, 0.64, 0.0, (16, 26, 66), (48, 76, 154), (248, 214, 98), (246, 212, 92), "crown", 148),
    (20, "General Morfeo: Alarico", "right", True, 0.64, 0.0, (22, 16, 30), (96, 24, 42), (228, 68, 84), (192, 62, 78), "morfeo", 148),
    (21, "General Morfeo: Zenobia", "right", True, 0.64, 0.0, (16, 20, 34), (58, 32, 86), (114, 216, 244), (214, 72, 92), "morfeo", 148),
    (22, "Subcapitana: Ariadna", "right", False, 0.66, 0.0, (28, 16, 32), (104, 44, 88), (242, 148, 188), (228, 134, 174), "morfeo", 150),
    (23, "Lider Supremo: Eliseo", "right", False, 0.64, 0.0, (18, 14, 34), (68, 40, 114), (206, 158, 250), (226, 194, 118), "morfeo", 148),
]


def main():
    TR_DIR.mkdir(parents=True, exist_ok=True)
    PREV_DIR.mkdir(parents=True, exist_ok=True)

    composed = []
    for tid, label, side, flip, crop_f, off_y, c0, c1, cg, tr, emb, xc in SPECS:
        bar = make_vs_bar(c0, c1, cg, tr, seed=tid + 7)
        trn = make_vs_trainer(tid, side, flip, crop_f, off_y, cg, tr, emb, xc)
        bar.save(TR_DIR / f"vsBar{tid}.png")
        trn.save(TR_DIR / f"vsTrainer{tid}.png")

        comp = bar.copy()
        comp.alpha_composite(trn)
        composed.append((tid, label, comp))

    # Build a crisp review contact sheet of all 22 VS cards (protagonists + all 20 bosses/rivals)
    cols = 4
    rows = math.ceil(len(composed) / cols)
    cw, ch = 266, 150
    sheet = Image.new("RGBA", (cols * cw + 14, rows * ch + 14), (20, 22, 28, 255))
    dr = ImageDraw.Draw(sheet)
    for idx, (tid, label, comp) in enumerate(composed):
        r, c = idx // cols, idx % cols
        x0, y0 = 10 + c * cw, 10 + r * ch
        dr.text((x0 + 2, y0 + 2), f"#{tid:02d} {label}", fill=(240, 230, 184, 255))
        sheet.alpha_composite(comp, (x0, y0 + 18))
    sheet.save(PREV_DIR / "vs_cards_review.png")
    print(f"Installed {len(SPECS)} VS card pairs in Graphics/Transitions and built previews/vs_cards_review.png.")


if __name__ == "__main__":
    main()
