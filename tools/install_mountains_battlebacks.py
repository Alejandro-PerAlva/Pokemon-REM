"""Install Mountain and MountainSnow battlebacks (512x384 Day, Eve, Night) and Realidea Monte bases.

Replaces 18 files in Graphics/Battlebacks/:
  - battlebgMountain{,Eve,Night}.png, enemybaseMountain{,Eve,Night}.png, playerbaseMountain{,Eve,Night}.png
  - battlebgMountainSnow{,Eve,Night}.png, enemybaseMountainSnow{,Eve,Night}.png, playerbaseMountainSnow{,Eve,Night}.png
"""

from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
BB_DIR = ROOT / "Graphics" / "Battlebacks"
REALIDEA_DIR = Path(r"C:\Users\apera\Downloads\Battlebacks")

SRC_M_DAY = Path(r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795614007507_bc59d091.png")
SRC_M_EVE = Path(r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795614007509_f91ee6cc.png")
SRC_M_NIGHT = Path(r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795614007509_719a7fa4.png")

SRC_MS_DAY = Path(r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795614007510_48dd23de.png")
SRC_MS_EVE = Path(r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795614007511_ea1fcaab.png")
SRC_MS_NIGHT = Path(r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795614007512_9254a30c.png")

SKY_DAY_REF = Path(r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795611441953_4b6ab8a0.png")
SKY_EVE_REF = Path(r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795611441951_49363f9d.png")
SKY_NIGHT_REF = Path(r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795611435773_d7d0332a.png")

# Strict sky RGB sets for Day and Night sources (excluding desert rocks/sand)
DESERT_DAY_SKY_RGB = {
    (30, 153, 244), (48, 127, 229), (74, 145, 234), (71, 162, 251),
    (102, 178, 251), (154, 202, 255), (183, 215, 255), (188, 212, 255),
    (202, 220, 255), (234, 240, 255), (255, 255, 255), (191, 224, 255),
}
DESERT_EVE_SKY_RGB = {
    (120, 149, 244), (195, 134, 153), (206, 158, 126), (221, 133, 94),
    (236, 148, 86), (255, 162, 126), (255, 198, 70), (255, 233, 144),
    (255, 227, 130), (242, 172, 112), (249, 194, 108), (239, 152, 107),
    (246, 178, 118), (255, 212, 102), (244, 164, 96), (232, 142, 92),
}

# Realidea enemybaseMonte / playerbaseMonte 15-color template mapping
# Surface: (192,160,144), (176,152,136), (168,144,112), (144,120,80)
# Pebbles/rim: (128,128,120), (104,104,96), (96,88,80), (88,80,64)
# Lower dirt/outline: (128,104,32), (112,96,32), (80,72,32), (48,32,16)
def build_monte_map(surf_hi, surf_mid, surf_sh, rock_hi, rock_mid, rock_dk, outline):
    return {
        (192, 160, 144): surf_hi,
        (176, 152, 136): surf_mid,
        (168, 144, 112): surf_mid,
        (144, 120, 80): surf_sh,
        (128, 128, 120): rock_hi,
        (104, 104, 96): rock_mid,
        (96, 88, 80): rock_mid,
        (88, 80, 64): rock_dk,
        (128, 104, 32): rock_hi,
        (112, 96, 32): surf_sh,
        (80, 72, 32): rock_dk,
        (48, 32, 16): outline,
    }


def recolor_monte(tpl: Image.Image, mapping: dict) -> Image.Image:
    out = tpl.copy()
    px = out.load()
    # Any leftover dark Monte color maps to outline/rock_dk cleanly
    fallback = mapping[(88, 80, 64)]
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a == 255:
                nr, ng, nb = mapping.get((r, g, b), fallback)
                px[x, y] = (nr, ng, nb, 255)
    return out


def recolor_palette(im: Image.Image, mapping: dict[tuple[int, int, int], tuple[int, int, int]]) -> Image.Image:
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            rep = mapping.get((r, g, b))
            if rep is not None:
                px[x, y] = (rep[0], rep[1], rep[2], a)
    return out


def build_sky_mask(m_day_raw: Image.Image) -> list[list[bool]]:
    """Flood-fill from top sky pixels on 2x2 grid using exact Mountain Day sky + distant haze RGBs.
    Since all 6 Mountain/MountainSnow variants share identical geometry, this mask is reused for all 6."""
    from collections import deque
    px = m_day_raw.load()
    nw, nh = 256, 192
    mask = [[False] * nw for _ in range(nh)]
    sky_and_haze_day_rgb = {
        (108, 170, 213), (121, 173, 213), (130, 187, 221), (131, 181, 206),
        (134, 147, 148), (158, 162, 162),
    }

    def is_sky_or_haze(nx: int, ny: int) -> bool:
        if ny >= 100:  # y >= 200 is always foreground ground/rock
            return False
        return px[nx * 2, ny * 2][:3] in sky_and_haze_day_rgb

    q = deque()
    for nx in range(nw):
        if is_sky_or_haze(nx, 0):
            mask[0][nx] = True
            q.append((nx, 0))

    while q:
        cx, cy = q.popleft()
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = cx + ox, cy + oy
            if 0 <= nx < nw and 0 <= ny < nh and not mask[ny][nx] and is_sky_or_haze(nx, ny):
                mask[ny][nx] = True
                q.append((nx, ny))
    return mask


def replace_sky_from_ref(
    bg_src: Image.Image,
    sky_src: Image.Image,
    mode: str,
    sky_mask: list[list[bool]],
    x_shift: int = 0,
) -> Image.Image:
    out = bg_src.copy()
    px = out.load()
    spx = sky_src.load()

    for ny in range(100):
        y = ny * 2
        for nx in range(256):
            if not sky_mask[ny][nx]:
                continue
            x = nx * 2
            sx = (x + x_shift) % 512
            sr, sg, sb, _ = spx[sx, y]
            if mode == "day":
                # Desert Day sky is clean down to ~y=114; below that, keep sky blues/clouds or use clean horizon blue
                if y <= 114 and sb >= sg and not (sr > 210 and sg < 170):
                    col = (sr, sg, sb, 255)
                elif sb >= 200 and sb >= sr:
                    col = (sr, sg, sb, 255)
                else:
                    col = (188, 212, 255, 255) if y > 136 else (154, 202, 255, 255)
            elif mode == "eve":
                # Desert Eve sky is clean down to ~y=114 (and golden horizon bands down to ~y=128)
                is_eve_rock = (sr < 195 and sg < 130) or (sb > sr + 10 and y > 40)
                if y <= 114 and not is_eve_rock:
                    col = (sr, sg, sb, 255)
                elif y <= 128 and sr >= 235 and sg >= 175 and sb <= 150:
                    col = (sr, sg, sb, 255)
                else:
                    col = (255, 227, 130, 255) if y > 138 else (255, 205, 61, 255)
            else:  # night
                # Desert Night sky is clean down to ~y=108; below that, strictly reject dunes/rocks
                is_pure_night = (sb >= 80 and sr <= 55 and sg <= 75) or (sr > 160 and sb > 200) or (sr > 200 and sg > 195 and sb > 160)
                if y <= 108 and (sb >= sr + 18 or is_pure_night):
                    col = (sr, sg, sb, 255)
                elif is_pure_night and y <= 130:
                    col = (sr, sg, sb, 255)
                else:
                    col = (28, 50, 110, 255) if y > 138 else (33, 31, 87, 255)
            for oy in (0, 1):
                for ox in (0, 1):
                    px[x + ox, y + oy] = col
    return out


def render_review(title: str, out_name: str, items: list[tuple[str, Image.Image, Image.Image, Image.Image]]):
    sheet = Image.new("RGBA", (1560, 424), (22, 25, 34, 255))
    draw = ImageDraw.Draw(sheet)
    for i, (label, bg, eb, pb) in enumerate(items):
        x0 = 10 + i * 518
        draw.text((x0 + 4, 6), f"{title} - {label} (512x384)", fill=(237, 189, 98, 255))
        comp = bg.copy()
        comp.alpha_composite(eb, (256, 112))
        comp.alpha_composite(pb, (-128, 240))
        for dx in range(0, 512, 8):
            ImageDraw.Draw(comp).line([(dx, 304), (dx + 4, 304)], fill=(255, 255, 255, 110))
        sheet.alpha_composite(comp, (x0, 26))
    sheet.save(ROOT / "previews" / out_name)


def main():
    sky_day = Image.open(SKY_DAY_REF).convert("RGBA")
    sky_eve = Image.open(SKY_EVE_REF).convert("RGBA")
    sky_night = Image.open(SKY_NIGHT_REF).convert("RGBA")

    eb_tpl = Image.open(REALIDEA_DIR / "enemybaseMonte.png").convert("RGBA")
    pb_tpl = Image.open(REALIDEA_DIR / "playerbaseMonte.png").convert("RGBA")

    # 1. Mountain
    m_day_raw = Image.open(SRC_M_DAY).convert("RGBA")
    m_eve_raw = Image.open(SRC_M_EVE).convert("RGBA")
    m_night_raw = Image.open(SRC_M_NIGHT).convert("RGBA")

    sky_mask = build_sky_mask(m_day_raw)

    # 2nd rock palette (warm earthy ochre-brown) for Mountain (no snow)
    m_day_rock_map = {
        (158, 83, 60): (173, 109, 67),
        (144, 72, 55): (147, 94, 61),
        (121, 58, 47): (129, 82, 58),
        (104, 46, 39): (110, 70, 52),
        (74, 31, 28): (76, 46, 36),
    }
    m_eve_rock_map = {
        (163, 117, 90): (178, 122, 80),
        (149, 105, 84): (154, 104, 70),
        (126, 89, 74): (132, 88, 62),
        (109, 74, 63): (112, 74, 54),
        (78, 53, 48): (78, 50, 38),
    }
    m_night_rock_map = {
        (118, 58, 90): (116, 74, 88),
        (109, 52, 84): (98, 62, 78),
        (92, 44, 74): (82, 52, 68),
        (79, 36, 63): (68, 42, 58),
        (57, 26, 48): (46, 28, 42),
    }

    m_day = recolor_palette(replace_sky_from_ref(m_day_raw, sky_day, "day", sky_mask), m_day_rock_map)
    m_eve = recolor_palette(replace_sky_from_ref(m_eve_raw, sky_eve, "eve", sky_mask), m_eve_rock_map)
    m_night = recolor_palette(replace_sky_from_ref(m_night_raw, sky_night, "night", sky_mask, x_shift=48), m_night_rock_map)

    m_day_map = build_monte_map((182, 114, 69), (173, 109, 67), (147, 94, 61), (147, 94, 61), (129, 82, 58), (110, 70, 52), (76, 46, 36))
    m_eve_map = build_monte_map((188, 132, 88), (178, 122, 80), (154, 104, 70), (154, 104, 70), (132, 88, 62), (112, 74, 54), (78, 50, 38))
    m_night_map = build_monte_map((126, 82, 96), (116, 74, 88), (98, 62, 78), (98, 62, 78), (82, 52, 68), (68, 42, 58), (46, 28, 42))

    m_eb_day, m_pb_day = recolor_monte(eb_tpl, m_day_map), recolor_monte(pb_tpl, m_day_map)
    m_eb_eve, m_pb_eve = recolor_monte(eb_tpl, m_eve_map), recolor_monte(pb_tpl, m_eve_map)
    m_eb_night, m_pb_night = recolor_monte(eb_tpl, m_night_map), recolor_monte(pb_tpl, m_night_map)

    # 2. MountainSnow
    ms_day_raw = Image.open(SRC_MS_DAY).convert("RGBA")
    ms_eve_raw = Image.open(SRC_MS_EVE).convert("RGBA")
    ms_night_raw = Image.open(SRC_MS_NIGHT).convert("RGBA")

    # 3rd rock palette (cool slate-grey) for MountainSnow
    ms_day_rock_map = {
        (163, 117, 90): (118, 120, 140),
        (149, 105, 84): (103, 105, 123),
        (126, 89, 74): (89, 91, 105),
        (109, 74, 63): (74, 76, 86),
        (78, 53, 48): (52, 54, 64),
    }
    ms_eve_rock_map = {
        (147, 80, 46): (126, 112, 124),
        (134, 71, 43): (110, 97, 110),
        (114, 60, 37): (94, 83, 96),
        (98, 50, 32): (78, 68, 82),
        (70, 36, 24): (54, 46, 58),
    }
    ms_night_rock_map = {
        (85, 58, 77): (78, 82, 116),
        (77, 52, 72): (66, 70, 102),
        (65, 44, 63): (56, 59, 88),
        (56, 36, 54): (46, 48, 74),
        (40, 26, 41): (32, 34, 54),
    }

    ms_day = recolor_palette(replace_sky_from_ref(ms_day_raw, sky_day, "day", sky_mask), ms_day_rock_map)
    ms_eve = recolor_palette(replace_sky_from_ref(ms_eve_raw, sky_eve, "eve", sky_mask), ms_eve_rock_map)
    ms_night = recolor_palette(replace_sky_from_ref(ms_night_raw, sky_night, "night", sky_mask, x_shift=48), ms_night_rock_map)

    ms_day_map = build_monte_map((255, 255, 255), (246, 240, 241), (236, 228, 229), (118, 120, 140), (103, 105, 123), (89, 91, 105), (52, 54, 64))
    ms_eve_map = build_monte_map((238, 184, 142), (229, 172, 131), (212, 154, 118), (126, 112, 124), (110, 97, 110), (94, 83, 96), (54, 46, 58))
    ms_night_map = build_monte_map((146, 140, 228), (133, 127, 218), (123, 113, 195), (78, 82, 116), (66, 70, 102), (56, 59, 88), (32, 34, 54))

    ms_eb_day, ms_pb_day = recolor_monte(eb_tpl, ms_day_map), recolor_monte(pb_tpl, ms_day_map)
    ms_eb_eve, ms_pb_eve = recolor_monte(eb_tpl, ms_eve_map), recolor_monte(pb_tpl, ms_eve_map)
    ms_eb_night, ms_pb_night = recolor_monte(eb_tpl, ms_night_map), recolor_monte(pb_tpl, ms_night_map)

    outputs = [
        ("battlebgMountain.png", m_day),
        ("battlebgMountainEve.png", m_eve),
        ("battlebgMountainNight.png", m_night),
        ("enemybaseMountain.png", m_eb_day),
        ("enemybaseMountainEve.png", m_eb_eve),
        ("enemybaseMountainNight.png", m_eb_night),
        ("playerbaseMountain.png", m_pb_day),
        ("playerbaseMountainEve.png", m_pb_eve),
        ("playerbaseMountainNight.png", m_pb_night),
        ("battlebgMountainSnow.png", ms_day),
        ("battlebgMountainSnowEve.png", ms_eve),
        ("battlebgMountainSnowNight.png", ms_night),
        ("enemybaseMountainSnow.png", ms_eb_day),
        ("enemybaseMountainSnowEve.png", ms_eb_eve),
        ("enemybaseMountainSnowNight.png", ms_eb_night),
        ("playerbaseMountainSnow.png", ms_pb_day),
        ("playerbaseMountainSnowEve.png", ms_pb_eve),
        ("playerbaseMountainSnowNight.png", ms_pb_night),
    ]
    for fname, im in outputs:
        im.save(BB_DIR / fname)

    (ROOT / "previews").mkdir(exist_ok=True)
    render_review("Mountain", "mountain_battleback_review.png", [
        ("DIA", m_day, m_eb_day, m_pb_day),
        ("ATARDECER Eve", m_eve, m_eb_eve, m_pb_eve),
        ("NOCHE Night", m_night, m_eb_night, m_pb_night),
    ])
    render_review("MountainSnow", "mountainsnow_battleback_review.png", [
        ("DIA", ms_day, ms_eb_day, ms_pb_day),
        ("ATARDECER Eve", ms_eve, ms_eb_eve, ms_pb_eve),
        ("NOCHE Night", ms_night, ms_eb_night, ms_pb_night),
    ])
    print("Installed all 18 Mountain + MountainSnow files cleanly.")


if __name__ == "__main__":
    main()
