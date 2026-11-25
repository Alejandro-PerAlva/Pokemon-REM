"""Install Autumn battleback (512x384 Day, Eve, Night) and Realidea Pradera bases.

Replaces 9 files in Graphics/Battlebacks/:
  - battlebgAutumn{,Eve,Night}.png
  - enemybaseAutumn{,Eve,Night}.png
  - playerbaseAutumn{,Eve,Night}.png
"""

from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SRC_FIELD = Path(
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795615853629_b0463fd8.png"
)
REALIDEA_DIR = Path(r"C:\Users\apera\Downloads\Battlebacks")
BB_DIR = ROOT / "Graphics" / "Battlebacks"

# Field -> Autumn (orange grass + burnt-orange russet trees from user tileset)
FIELD_TO_AUTUMN = {
    # Ground grass -> autumn golden-orange grass
    (196, 225, 116): (228, 152, 68),
    (177, 216, 109): (212, 132, 54),
    (153, 199, 96): (188, 108, 42),
    (126, 178, 84): (158, 84, 34),
    (97, 160, 70): (132, 66, 28),
    # Foreground grass tufts & stems -> warm autumn orange-amber
    (118, 202, 77): (222, 138, 56),
    (83, 178, 74): (194, 108, 42),
    (61, 145, 62): (156, 78, 34),
    (78, 145, 61): (168, 88, 38),
    (57, 128, 64): (128, 62, 30),
    # Trees -> 5th tree set (burnt-orange / russet)
    (56, 154, 77): (188, 88, 49),
    (43, 128, 93): (173, 81, 47),
    (36, 107, 86): (139, 66, 43),
    (36, 104, 80): (139, 66, 43),
    (31, 89, 72): (114, 53, 43),
    (64, 143, 121): (162, 74, 46),
    (45, 122, 114): (134, 62, 42),
    (32, 91, 94): (106, 49, 40),
    (32, 94, 85): (106, 49, 40),
    # Slightly lighter sandy-cream path so it contrasts cleanly against orange grass
    (238, 206, 149): (244, 218, 172),
    (235, 200, 145): (236, 206, 158),
    (229, 191, 133): (222, 188, 138),
    (218, 175, 117): (202, 164, 116),
}

PRADERA_TO_AUTUMN = {
    (160, 176, 120): (228, 152, 68),
    (144, 168, 104): (212, 132, 54),
    (128, 160, 88): (188, 108, 42),
    (104, 144, 72): (158, 84, 34),
    (72, 128, 40): (128, 62, 30),
    (232, 152, 64): (244, 218, 172),
    (208, 128, 48): (236, 206, 158),
    (176, 160, 56): (222, 188, 138),
    (168, 96, 32): (202, 164, 116),
    (120, 56, 24): (114, 53, 43),
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
                nr = clamp(r * 0.94 + 12)
                ng = clamp(g * 0.80)
                nb = clamp(b * 0.72)
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
                nb = clamp(b * 0.84 + 18)
                cache[key] = (nr, ng, nb)
            nr, ng, nb = cache[key]
            for oy in (0, 1):
                for ox in (0, 1):
                    if px[x + ox, y + oy][3] == 255:
                        px[x + ox, y + oy] = (nr, ng, nb, 255)
    return out


def add_fireflies(im: Image.Image):
    px = im.load()
    for fx, fy in [(184, 72), (244, 58), (298, 96), (374, 114), (104, 128), (438, 86)]:
        for oy in (0, 1):
            for ox in (0, 1):
                px[fx + ox, fy + oy] = (232, 240, 156, 255)


def main():
    eb_tpl = Image.open(REALIDEA_DIR / "enemybasePradera.png").convert("RGBA")
    pb_tpl = Image.open(REALIDEA_DIR / "playerbasePradera.png").convert("RGBA")

    f_day = Image.open(SRC_FIELD).convert("RGBA")
    au_day = recolor_exact(f_day, FIELD_TO_AUTUMN)
    au_eve = transform_eve(au_day)
    au_night = transform_night(au_day)
    add_fireflies(au_night)

    eb_day = recolor_exact(eb_tpl, PRADERA_TO_AUTUMN)
    pb_day = recolor_exact(pb_tpl, PRADERA_TO_AUTUMN)
    eb_eve, pb_eve = transform_eve(eb_day), transform_eve(pb_day)
    eb_night, pb_night = transform_night(eb_day), transform_night(pb_day)

    outputs = [
        ("battlebgAutumn.png", au_day), ("battlebgAutumnEve.png", au_eve), ("battlebgAutumnNight.png", au_night),
        ("enemybaseAutumn.png", eb_day), ("enemybaseAutumnEve.png", eb_eve), ("enemybaseAutumnNight.png", eb_night),
        ("playerbaseAutumn.png", pb_day), ("playerbaseAutumnEve.png", pb_eve), ("playerbaseAutumnNight.png", pb_night),
    ]
    for name, img in outputs:
        img.save(BB_DIR / name)

    sheet = Image.new("RGBA", (1560, 424), (22, 25, 34, 255))
    draw = ImageDraw.Draw(sheet)
    for i, (label, bg, eb, pb) in enumerate([
        ("DIA", au_day, eb_day, pb_day),
        ("ATARDECER Eve", au_eve, eb_eve, pb_eve),
        ("NOCHE Night", au_night, eb_night, pb_night),
    ]):
        x0 = 10 + i * 518
        draw.text((x0 + 4, 6), f"Autumn - {label} (512x384)", fill=(237, 189, 98, 255))
        comp = bg.copy()
        comp.alpha_composite(eb, (256, 112))
        comp.alpha_composite(pb, (-128, 240))
        for dx in range(0, 512, 8):
            ImageDraw.Draw(comp).line([(dx, 304), (dx + 4, 304)], fill=(255, 255, 255, 110))
        sheet.alpha_composite(comp, (x0, 26))
    sheet.save(ROOT / "previews" / "autumn_battleback_review.png")
    print("Installed all 9 Autumn files cleanly.")


if __name__ == "__main__":
    main()
