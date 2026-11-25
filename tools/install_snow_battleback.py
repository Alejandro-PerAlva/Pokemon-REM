"""Install Snow battleback (512x384 Day, Eve, Night) and Realidea Pradera bases.

Built by editing the user's Field base (media_1795615853629_b0463fd8.png) with a snow palette,
snow-capped tree crowns, winter-teal foliage, and matching platforms.
Replaces 9 files in Graphics/Battlebacks/:
  - battlebgSnow{,Eve,Night}.png
  - enemybaseSnow{,Eve,Night}.png
  - playerbaseSnow{,Eve,Night}.png
"""

from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SRC_FIELD = Path(
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795615853629_b0463fd8.png"
)
REALIDEA_DIR = Path(r"C:\Users\apera\Downloads\Battlebacks")
BB_DIR = ROOT / "Graphics" / "Battlebacks"

FIELD_TO_SNOW = {
    # Grass ground -> crisp cool snow
    (196, 225, 116): (244, 240, 245),
    (177, 216, 109): (234, 228, 236),
    (153, 199, 96): (218, 206, 218),
    (126, 178, 84): (198, 182, 198),
    (97, 160, 70): (172, 156, 174),
    # Foreground grass tufts & flower stems -> cool winter-pine teal
    (118, 202, 77): (68, 182, 146),
    (83, 178, 74): (50, 156, 128),
    (61, 145, 62): (36, 124, 108),
    (78, 145, 61): (44, 138, 118),
    (57, 128, 64): (32, 108, 94),
    # Tree canopies -> winter-teal pine
    (56, 154, 77): (48, 144, 114),
    (43, 128, 93): (34, 116, 102),
    (36, 107, 86): (28, 96, 86),
    (36, 104, 80): (28, 96, 86),
    (31, 89, 72): (24, 78, 72),
    (64, 143, 121): (44, 128, 120),
    (45, 122, 114): (34, 106, 104),
    (32, 91, 94): (26, 80, 84),
    (32, 94, 85): (26, 80, 84),
}

# Snow-cap colors for upper tree crowns (built on 2x2 grid from original canopy shades)
TREE_TOP_TO_SNOWCAP = {
    (56, 154, 77): (234, 240, 246),
    (43, 128, 93): (212, 222, 234),
    (36, 107, 86): (186, 198, 214),
    (36, 104, 80): (186, 198, 214),
    (31, 89, 72): (162, 176, 196),
    (64, 143, 121): (226, 234, 242),
    (45, 122, 114): (202, 214, 228),
    (32, 91, 94): (176, 190, 208),
    (32, 94, 85): (176, 190, 208),
}

PRADERA_TO_SNOW = {
    (160, 176, 120): (244, 240, 245),
    (144, 168, 104): (234, 228, 236),
    (128, 160, 88): (218, 206, 218),
    (104, 144, 72): (198, 182, 198),
    (72, 128, 40): (148, 134, 154),
    (232, 152, 64): (238, 206, 149),
    (208, 128, 48): (235, 200, 145),
    (176, 160, 56): (229, 191, 133),
    (168, 96, 32): (218, 175, 117),
    (120, 56, 24): (133, 91, 78),
}


def clamp(v: float) -> int:
    return max(0, min(255, int(round(v))))


def recolor_exact(im: Image.Image, pal: dict[tuple[int, int, int], tuple[int, int, int]]) -> Image.Image:
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a == 255 and (r, g, b) in pal:
                nr, ng, nb = pal[(r, g, b)]
                px[x, y] = (nr, ng, nb, 255)
    return out


def build_snow_day(src: Image.Image) -> Image.Image:
    import math
    out = src.copy()
    px = out.load()
    # Include bright canopy highlight specks (74,178,125) and (104,185,103) in snow cap
    snowcap_map = dict(TREE_TOP_TO_SNOWCAP)
    snowcap_map[(74, 178, 125)] = (234, 240, 246)
    snowcap_map[(104, 185, 103)] = (234, 240, 246)

    for y in range(0, out.height, 2):
        for x in range(0, out.width, 2):
            rgb = px[x, y][:3]
            # Organic scalloped snow-cap contour on tree crowns (skipping big trunk x in 310..390)
            scallop = 44 + int(round(5 * math.sin(x * 0.15) + 3 * math.cos(x * 0.07)))
            if x >= 390:
                scallop -= 4
            is_upper_crown = (
                y < scallop
                and (x < 310 or x >= 390)
                and not (x < 30 and y >= 28)  # protect top-left yellow flower
            )
            if is_upper_crown and rgb in snowcap_map:
                rep = snowcap_map[rgb]
            else:
                rep = FIELD_TO_SNOW.get(rgb)
            if rep is not None:
                for oy in (0, 1):
                    for ox in (0, 1):
                        px[x + ox, y + oy] = (rep[0], rep[1], rep[2], 255)
    return out


def transform_eve(im: Image.Image) -> Image.Image:
    out = im.copy()
    px = out.load()
    w, h = out.size
    cache: dict[tuple[int, int, int], tuple[int, int, int]] = {}
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b, a = px[x, y]
            if a != 255:
                continue
            key = (r, g, b)
            if key not in cache:
                nr = clamp(r * 0.96 + 12)
                ng = clamp(g * 0.80 - 2)
                nb = clamp(b * 0.76 - 2)
                cache[key] = (nr, ng, nb)
            nr, ng, nb = cache[key]
            for oy in (0, 1):
                for ox in (0, 1):
                    if px[x + ox, y + oy][3] == 255:
                        px[x + ox, y + oy] = (nr, ng, nb, 255)
    return out


def transform_night(im: Image.Image) -> Image.Image:
    out = im.copy()
    px = out.load()
    w, h = out.size
    cache: dict[tuple[int, int, int], tuple[int, int, int]] = {}
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b, a = px[x, y]
            if a != 255:
                continue
            key = (r, g, b)
            if key not in cache:
                nr = clamp(r * 0.56 - 2)
                ng = clamp(g * 0.60 - 2)
                nb = clamp(b * 0.88 + 20)
                cache[key] = (nr, ng, nb)
            nr, ng, nb = cache[key]
            for oy in (0, 1):
                for ox in (0, 1):
                    if px[x + ox, y + oy][3] == 255:
                        px[x + ox, y + oy] = (nr, ng, nb, 255)
    return out


def add_snow_sparkles(im: Image.Image):
    px = im.load()
    for sx, sy in [(184, 72), (244, 58), (298, 96), (374, 114), (104, 128), (438, 86)]:
        for oy in (0, 1):
            for ox in (0, 1):
                px[sx + ox, sy + oy] = (214, 228, 255, 255)


def main():
    eb_tpl = Image.open(REALIDEA_DIR / "enemybasePradera.png").convert("RGBA")
    pb_tpl = Image.open(REALIDEA_DIR / "playerbasePradera.png").convert("RGBA")

    src = Image.open(SRC_FIELD).convert("RGBA")
    sn_day = build_snow_day(src)
    sn_eve = transform_eve(sn_day)
    sn_night = transform_night(sn_day)
    add_snow_sparkles(sn_night)

    eb_day = recolor_exact(eb_tpl, PRADERA_TO_SNOW)
    pb_day = recolor_exact(pb_tpl, PRADERA_TO_SNOW)
    eb_eve, pb_eve = transform_eve(eb_day), transform_eve(pb_day)
    eb_night, pb_night = transform_night(eb_day), transform_night(pb_day)

    outputs = [
        ("battlebgSnow.png", sn_day), ("battlebgSnowEve.png", sn_eve), ("battlebgSnowNight.png", sn_night),
        ("enemybaseSnow.png", eb_day), ("enemybaseSnowEve.png", eb_eve), ("enemybaseSnowNight.png", eb_night),
        ("playerbaseSnow.png", pb_day), ("playerbaseSnowEve.png", pb_eve), ("playerbaseSnowNight.png", pb_night),
    ]
    for name, img in outputs:
        img.save(BB_DIR / name)

    sheet = Image.new("RGBA", (1560, 424), (22, 25, 34, 255))
    draw = ImageDraw.Draw(sheet)
    for i, (label, bg, eb, pb) in enumerate([
        ("DIA", sn_day, eb_day, pb_day),
        ("ATARDECER Eve", sn_eve, eb_eve, pb_eve),
        ("NOCHE Night", sn_night, eb_night, pb_night),
    ]):
        x0 = 10 + i * 518
        draw.text((x0 + 4, 6), f"Snow - {label} (512x384)", fill=(237, 189, 98, 255))
        comp = bg.copy()
        comp.alpha_composite(eb, (256, 112))
        comp.alpha_composite(pb, (-128, 240))
        for dx in range(0, 512, 8):
            ImageDraw.Draw(comp).line([(dx, 304), (dx + 4, 304)], fill=(255, 255, 255, 110))
        sheet.alpha_composite(comp, (x0, 26))
    sheet.save(ROOT / "previews" / "snow_battleback_review.png")
    print("Installed all 9 Snow files cleanly.")


if __name__ == "__main__":
    main()
