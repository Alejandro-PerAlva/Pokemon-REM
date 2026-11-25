"""Install all 6 Cave battlebacks (512x384, no Eve/Night) and Realidea Cueva platforms.

Replaces 18 files in Graphics/Battlebacks/:
  - CaveVolcano (Cueva B Volcan rock + lava)
  - CaveWater   (Cueva A Generica rock + underground water replacing lava)
  - CaveIce     (Cueva B Hielo rock + frozen ice sheet replacing lava)
  - CaveCrystal (Cueva A Generica rock + glowing cyan crystals)
  - Cave        (Cueva A Generica rock)
  - CaveLush    (Cueva A Frondosa earthy brown rock + hanging emerald vines & moss)
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
BB_DIR = ROOT / "Graphics" / "Battlebacks"
REALIDEA_DIR = Path(r"C:\Users\apera\Downloads\Battlebacks")

SRC_VOLC = Path(r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795618293977_5811fe39.png")
SRC_CRYS = Path(r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795618366191_4f1b990f.png")
SRC_BASE = Path(r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795618413239_8d179d3f.png")

# Realidea enemybaseCueva / playerbaseCueva 10 colors (ordered dark->light)
def build_cueva_base_map(outline, rim_dk, rim_mid, rim_hi, surf_dk, surf_mid, surf_hi, surf_top):
    return {
        (48, 16, 16): outline,
        (64, 44, 40): rim_dk,
        (72, 64, 56): rim_mid,
        (80, 76, 72): rim_mid,
        (80, 80, 64): rim_hi,
        (96, 92, 72): rim_hi,
        (120, 104, 72): surf_dk,
        (144, 112, 80): surf_mid,
        (144, 124, 88): surf_hi,
        (144, 120, 96): surf_top,
    }


def recolor_cueva_base(tpl: Image.Image, mapping: dict) -> Image.Image:
    out = tpl.copy()
    px = out.load()
    fallback = mapping[(72, 64, 56)]
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a == 255:
                nr, ng, nb = mapping.get((r, g, b), fallback)
                px[x, y] = (nr, ng, nb, 255)
    return out


def recolor_exact_2x2(im: Image.Image, mapping: dict[tuple[int, int, int], tuple[int, int, int]]) -> Image.Image:
    out = im.copy()
    px = out.load()
    for y in range(0, out.height, 2):
        for x in range(0, out.width, 2):
            r, g, b, a = px[x, y]
            rep = mapping.get((r, g, b))
            if rep is not None:
                c4 = (rep[0], rep[1], rep[2], a)
                for oy in (0, 1):
                    for ox in (0, 1):
                        px[x + ox, y + oy] = c4
    return out


def clean_lava_steam_vent(im: Image.Image, floor_hi: tuple[int, int, int], floor_mid: tuple[int, int, int]):
    """Replace the floor steam puff in Volc_src (x=70..136, y=196..276) with surrounding rock floor."""
    px = im.load()
    for y in range(196, 276, 2):
        for x in range(70, 136, 2):
            r, g, b, _ = px[x, y]
            # Steam pixels are neutral grey above the floor rock
            if r > 76 and g > 76 and b > 76 and (max(r, g, b) - min(r, g, b) < 20):
                col = floor_hi if (x + y) % 4 == 0 else floor_mid
                c4 = (col[0], col[1], col[2], 255)
                for oy in (0, 1):
                    for ox in (0, 1):
                        px[x + ox, y + oy] = c4


def recolor_volc_variant(
    volc_src: Image.Image,
    rock_map: dict[tuple[int, int, int], tuple[int, int, int]],
    liquid_stops: list[tuple[int, int, int]],
) -> Image.Image:
    """Recolor Volc_src rocks by exact dict and ALL warm lava/ember pixels smoothly by luminance."""
    out = recolor_exact_2x2(volc_src, rock_map)
    px = out.load()
    for y in range(0, out.height, 2):
        for x in range(0, out.width, 2):
            r, g, b, _ = px[x, y]
            # Catch every lava/ember pixel (warm red/orange/yellow)
            if r > 80 and r > b * 1.7 and (r - b) > 40:
                t = max(0.0, min(1.0, (r * 0.4 + g * 0.6 - 45.0) / 170.0))
                idx = min(len(liquid_stops) - 1, int(round(t * (len(liquid_stops) - 1))))
                col = liquid_stops[idx]
                c4 = (col[0], col[1], col[2], 255)
                for oy in (0, 1):
                    for ox in (0, 1):
                        px[x + ox, y + oy] = c4
    return out


def build_cave_crystal(src: Image.Image) -> Image.Image:
    """Shift Crys_src rock tones to Cueva A Generica slate-grey while preserving cyan crystals & glow."""
    out = Image.new("RGBA", src.size)
    spx = src.load()
    opx = out.load()
    for y in range(0, src.height, 2):
        for x in range(0, src.width, 2):
            r, g, b, _ = spx[x, y]
            # Bright cyan crystal core & strong blue-cyan halo -> keep crisp & glowing
            is_crystal = (b >= 175 and g >= 120 and b > r + 40) or (r > 180 and g > 210 and b > 235)
            if is_crystal:
                nr, ng, nb = r, g, b
            else:
                # Shift dark indigo-blue cave rock -> Cueva A Generica slate-grey (slightly greenish-teal slate)
                glow = max(0.0, (b - r - 18) / 90.0)
                lum = (r * 0.299 + g * 0.587 + b * 0.114)
                # Cueva A Generica target: R ~ lum*0.86, G ~ lum*1.02, B ~ lum*1.12
                nr = int(round(lum * 0.86))
                ng = int(round(lum * 1.01 + glow * 16))
                nb = int(round(lum * 1.12 + glow * 28))
                nr = max(12, min(255, nr))
                ng = max(14, min(255, ng))
                nb = max(16, min(255, nb))
            c4 = (nr, ng, nb, 255)
            for oy in (0, 1):
                for ox in (0, 1):
                    opx[x + ox, y + oy] = c4
    return out


def add_lush_vines_and_moss(im: Image.Image):
    """Add Cueva A Frondosa wall-clinging creeping ivy & leafy tendrils strictly onto cave walls/rocks."""
    import random
    px = im.load()
    out_c = (20, 19, 17, 255)
    void_c = (40, 34, 29, 255)
    v_dk = (29, 62, 51, 255)
    v_mid = (46, 88, 64, 255)
    v_hi = (70, 132, 88, 255)

    def is_wall_rock(nx: int, ny: int) -> bool:
        if not (0 <= nx < 256 and 0 <= ny < 192):
            return False
        c = px[nx * 2, ny * 2]
        # Only cling to lit/mid rock faces, never dark cave void or outlines
        return c not in (out_c, void_c, v_dk, v_mid, v_hi)

    def set2(nx: int, ny: int, col):
        if 0 <= nx < 256 and 0 <= ny < 192:
            c = px[nx * 2, ny * 2]
            if c in (out_c, void_c):
                return
            x, y = nx * 2, ny * 2
            for oy in (0, 1):
                for ox in (0, 1):
                    px[x + ox, y + oy] = col

    rng = random.Random(4242)

    def draw_creeping_vine(start_nx: int, start_ny: int, length: int, drift: float, branch_prob: float = 0.24):
        cx = float(start_nx)
        for step in range(length):
            ny = start_ny + step
            if ny >= 190:
                break
            cx += drift + math.sin(step * 0.45 + start_nx) * 0.45
            nx = int(round(cx))
            if not is_wall_rock(nx, ny):
                continue
            # Main creeping stem + leaf fleck
            set2(nx, ny, v_mid)
            if step % 3 == 0:
                set2(nx, max(0, ny - 1), v_hi)
            if is_wall_rock(nx - 1, ny):
                set2(nx - 1, ny, v_dk)
            # Organic leaf clusters hugging the wall like Cueva A tileset
            if rng.random() < 0.65:
                lx = nx + rng.choice((-1, 1))
                ly = ny + rng.choice((0, 1))
                if is_wall_rock(lx, ly):
                    set2(lx, ly, v_hi if rng.random() < 0.45 else v_mid)
                    if is_wall_rock(lx, ly + 1) and rng.random() < 0.55:
                        set2(lx, ly + 1, v_dk)
            # Secondary branching tendril along the rock face
            if step > 4 and step < length - 5 and rng.random() < branch_prob:
                bdir = rng.choice((-1, 1))
                bx = nx
                for bstep in range(rng.randint(4, 10)):
                    bx += bdir * (1 if bstep % 2 == 0 else 0)
                    by = ny + bstep
                    if is_wall_rock(bx, by):
                        set2(bx, by, v_mid if bstep % 2 == 0 else v_hi)
                        if is_wall_rock(bx, by + 1):
                            set2(bx, by + 1, v_dk)

    # 1. Dense creeping vines across upper cave ceiling & left/center/right walls (matching Cueva A wall ivy)
    wall_vines = [
        # Left upper wall & arch flank
        (6, 0, 38, 0.08), (14, 0, 34, 0.10), (24, 0, 26, -0.05), (38, 0, 22, 0.05),
        # Center-left rock pillar (nx ~ 68..112)
        (64, 0, 44, 0.12), (76, 0, 68, 0.10), (86, 0, 82, 0.06), (96, 0, 74, -0.08),
        (106, 0, 52, -0.10), (82, 52, 46, 0.08), (94, 48, 48, -0.06),
        # Upper arch & right cave wall
        (118, 0, 36, 0.05), (132, 0, 30, -0.05), (146, 0, 28, 0.08),
        (164, 0, 22, 0.05), (186, 0, 18, -0.05), (206, 0, 24, 0.06),
        (224, 0, 32, 0.08), (238, 0, 46, -0.06), (248, 0, 58, -0.08),
        # Right wall clinging ivy below arch (nx ~ 228..252, ny ~ 56..115)
        (232, 58, 42, 0.10), (244, 64, 46, -0.08), (220, 72, 32, 0.12),
    ]
    for sx, sy, ln, dr in wall_vines:
        draw_creeping_vine(sx, sy, ln, dr, branch_prob=0.28)

    # 2. Delicate moss & creeping vine tendrils hugging the bottom-right foreground cliff rocks (nx=180..254, ny=145..190)
    fg_vines = [
        (194, 152, 22, 0.25), (208, 146, 26, 0.15), (222, 142, 30, 0.10),
        (236, 148, 28, -0.12), (248, 156, 24, -0.15),
    ]
    for sx, sy, ln, dr in fg_vines:
        draw_creeping_vine(sx, sy, ln, dr, branch_prob=0.35)


def make_mirror_ice_river(im: Image.Image):
    """Turn the choppy river pixels in CaveIce into a smooth, glassy mirror-like ice sheet with diagonal shine."""
    px = im.load()
    ice_set = {
        (84, 134, 178), (99, 151, 195), (115, 167, 211),
        (134, 186, 228), (158, 206, 242), (186, 226, 252), (218, 244, 255),
    }
    base_ice = (144, 198, 238, 255)
    mid_ice = (164, 214, 248, 255)
    shine_1 = (206, 238, 255, 255)
    shine_2 = (238, 250, 255, 255)
    crack_c = (112, 164, 208, 255)

    # First collect exact ice-river pixel mask on 2x2 grid
    mask = [[px[nx * 2, ny * 2][:3] in ice_set for nx in range(256)] for ny in range(192)]

    for ny in range(192):
        for nx in range(256):
            if not mask[ny][nx]:
                continue
            # Check distance to shoreline rock edge for crisp frost bevel
            near_edge = any(
                0 <= nx + ox < 256 and 0 <= ny + oy < 192 and not mask[ny + oy][nx + ox]
                for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
            if near_edge:
                col = shine_1 if ny < 140 else crack_c
            else:
                # Diagonal glassy mirror reflection bands across the ice surface (45 deg)
                diag = (nx + ny * 1.45) % 44
                diag2 = (nx * 0.85 + ny * 1.35) % 68
                if 8 <= diag <= 11 or 28 <= diag2 <= 30:
                    col = shine_2
                elif 6 <= diag <= 14 or 26 <= diag2 <= 33:
                    col = shine_1
                elif (nx + ny * 2) % 37 == 0 and (nx % 3 == 0):
                    col = crack_c
                elif (nx * 0.12 + ny * 0.18) % 6 < 2.2:
                    col = mid_ice
                else:
                    col = base_ice
            x, y = nx * 2, ny * 2
            for oy in (0, 1):
                for ox in (0, 1):
                    px[x + ox, y + oy] = col


def render_review(out_name: str, items: list[tuple[str, Image.Image, Image.Image, Image.Image]]):
    sheet = Image.new("RGBA", (1560, 424), (22, 25, 34, 255))
    draw = ImageDraw.Draw(sheet)
    for i, (label, bg, eb, pb) in enumerate(items):
        x0 = 10 + i * 518
        draw.text((x0 + 4, 6), f"{label} (512x384)", fill=(237, 189, 98, 255))
        comp = bg.copy()
        comp.alpha_composite(eb, (256, 112))
        comp.alpha_composite(pb, (-128, 240))
        for dx in range(0, 512, 8):
            ImageDraw.Draw(comp).line([(dx, 304), (dx + 4, 304)], fill=(255, 255, 255, 110))
        sheet.alpha_composite(comp, (x0, 26))
    sheet.save(ROOT / "previews" / out_name)


def main():
    volc_src = Image.open(SRC_VOLC).convert("RGBA")
    crys_src = Image.open(SRC_CRYS).convert("RGBA")
    base_src = Image.open(SRC_BASE).convert("RGBA")

    eb_tpl = Image.open(REALIDEA_DIR / "enemybaseCueva.png").convert("RGBA")
    pb_tpl = Image.open(REALIDEA_DIR / "playerbaseCueva.png").convert("RGBA")

    # 1. CaveVolcano (Cueva B Volcan rock + original lava & steam)
    volc_rock_map = {
        (116, 105, 136): (94, 66, 77),
        (101, 88, 122): (88, 63, 75),
        (87, 76, 110): (81, 57, 69),
        (72, 64, 90): (76, 52, 64),
        (59, 55, 76): (58, 40, 51),
        (45, 44, 58): (43, 29, 37),
        (16, 15, 21): (26, 20, 26),
    }
    bg_volc = recolor_exact_2x2(volc_src, volc_rock_map)
    volc_base_map = build_cueva_base_map((26, 20, 26), (43, 29, 37), (58, 40, 51), (69, 49, 57), (76, 52, 64), (81, 57, 69), (88, 63, 75), (94, 66, 77))
    eb_volc, pb_volc = recolor_cueva_base(eb_tpl, volc_base_map), recolor_cueva_base(pb_tpl, volc_base_map)

    # 2. CaveWater (Cueva A Generica slate rock + water replacing lava)
    gen_rock_only = {
        (116, 105, 136): (82, 96, 108),
        (101, 88, 122): (70, 83, 93),
        (87, 76, 110): (66, 78, 87),
        (72, 64, 90): (55, 65, 73),
        (59, 55, 76): (44, 49, 54),
        (45, 44, 58): (33, 39, 43),
        (16, 15, 21): (16, 16, 19),
    }
    water_stops = [
        (24, 50, 88), (32, 72, 122), (42, 98, 156),
        (54, 122, 184), (72, 148, 210), (96, 176, 232), (132, 206, 244),
    ]
    bg_water = recolor_volc_variant(volc_src, gen_rock_only, water_stops)
    clean_lava_steam_vent(bg_water, (70, 83, 93), (66, 78, 87))
    gen_base_map = build_cueva_base_map((16, 16, 19), (33, 39, 43), (44, 49, 54), (55, 65, 73), (62, 72, 81), (66, 78, 87), (70, 83, 93), (82, 96, 108))
    eb_gen, pb_gen = recolor_cueva_base(eb_tpl, gen_base_map), recolor_cueva_base(pb_tpl, gen_base_map)

    # 3. CaveIce (Cueva B Hielo rock + frozen ice replacing lava)
    ice_rock_only = {
        (116, 105, 136): (210, 230, 248),
        (101, 88, 122): (198, 217, 244),
        (87, 76, 110): (185, 202, 228),
        (72, 64, 90): (167, 182, 207),
        (59, 55, 76): (141, 149, 171),
        (45, 44, 58): (119, 125, 143),
        (16, 15, 21): (32, 38, 46),
    }
    ice_stops = [
        (84, 134, 178), (99, 151, 195), (115, 167, 211),
        (134, 186, 228), (158, 206, 242), (186, 226, 252), (218, 244, 255),
    ]
    bg_ice = recolor_volc_variant(volc_src, ice_rock_only, ice_stops)
    clean_lava_steam_vent(bg_ice, (198, 217, 244), (185, 202, 228))
    make_mirror_ice_river(bg_ice)
    ice_base_map = build_cueva_base_map((32, 38, 46), (119, 125, 143), (141, 149, 171), (158, 172, 194), (167, 182, 207), (185, 202, 228), (198, 217, 244), (210, 230, 248))
    eb_ice, pb_ice = recolor_cueva_base(eb_tpl, ice_base_map), recolor_cueva_base(pb_tpl, ice_base_map)

    # 4. CaveCrystal (Cueva A Generica rock + cyan crystals)
    bg_crys = build_cave_crystal(crys_src)

    # 5. Cave (Base_src -> Cueva A Generica)
    base_to_gen = {
        (180, 148, 124): (82, 96, 108),
        (165, 130, 102): (70, 83, 93),
        (152, 113, 87): (66, 78, 87),
        (126, 96, 78): (55, 65, 73),
        (108, 80, 71): (44, 49, 54),
        (58, 50, 48): (33, 39, 43),
        (41, 34, 32): (16, 16, 19),
    }
    bg_cave = recolor_exact_2x2(base_src, base_to_gen)

    # 6. CaveLush (Base_src -> Cueva A Frondosa + hanging emerald vines & moss)
    base_to_lush = {
        (180, 148, 124): (96, 86, 72),
        (165, 130, 102): (83, 73, 61),
        (152, 113, 87): (75, 66, 55),
        (126, 96, 78): (70, 63, 51),
        (108, 80, 71): (61, 54, 43),
        (58, 50, 48): (40, 34, 29),
        (41, 34, 32): (20, 19, 17),
    }
    bg_lush = recolor_exact_2x2(base_src, base_to_lush)
    add_lush_vines_and_moss(bg_lush)
    lush_base_map = build_cueva_base_map((20, 19, 17), (40, 34, 29), (50, 43, 36), (46, 88, 64), (70, 63, 51), (75, 66, 55), (83, 73, 61), (96, 86, 72))
    eb_lush, pb_lush = recolor_cueva_base(eb_tpl, lush_base_map), recolor_cueva_base(pb_tpl, lush_base_map)

    sets = [
        ("CaveVolcano", bg_volc, eb_volc, pb_volc),
        ("CaveWater", bg_water, eb_gen, pb_gen),
        ("CaveIce", bg_ice, eb_ice, pb_ice),
        ("CaveCrystal", bg_crys, eb_gen, pb_gen),
        ("Cave", bg_cave, eb_gen, pb_gen),
        ("CaveLush", bg_lush, eb_lush, pb_lush),
    ]
    for name, bg, eb, pb in sets:
        bg.save(BB_DIR / f"battlebg{name}.png")
        eb.save(BB_DIR / f"enemybase{name}.png")
        pb.save(BB_DIR / f"playerbase{name}.png")

    render_review("caves_elemental_review.png", sets[:3])
    render_review("caves_normal_review.png", sets[3:])
    print("Installed all 18 Cave files cleanly.")


if __name__ == "__main__":
    main()
