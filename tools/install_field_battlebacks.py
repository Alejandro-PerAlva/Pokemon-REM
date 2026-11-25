"""Install Field and FieldAlt battlebacks (512x384 Day, Eve, Night) and Realidea Pradera bases.

Replaces 18 files in Graphics/Battlebacks/:
  - battlebgField{,Eve,Night}.png, enemybaseField{,Eve,Night}.png, playerbaseField{,Eve,Night}.png
  - battlebgFieldAlt{,Eve,Night}.png, enemybaseFieldAlt{,Eve,Night}.png, playerbaseFieldAlt{,Eve,Night}.png
"""

from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SRC_FIELD = Path(
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795615853629_b0463fd8.png"
)
REALIDEA_DIR = Path(r"C:\Users\apera\Downloads\Battlebacks")
BB_DIR = ROOT / "Graphics" / "Battlebacks"

# FieldAlt: 2nd grass tone + 2nd emerald-teal tree set from user tileset
FIELD_TO_ALT = {
    # Ground grass (1st tone -> 2nd olive-meadow tone)
    (196, 225, 116): (148, 178, 102),
    (177, 216, 109): (133, 164, 86),
    (153, 199, 96): (118, 149, 74),
    (126, 178, 84): (98, 128, 60),
    (97, 160, 70): (78, 108, 48),
    # Foreground grass tufts & stems
    (118, 202, 77): (104, 146, 68),
    (83, 178, 74): (76, 122, 58),
    (61, 145, 62): (52, 96, 46),
    (78, 145, 61): (64, 108, 52),
    (57, 128, 64): (44, 88, 48),
    # Trees (1st tree -> 2nd emerald-teal tree)
    (56, 154, 77): (34, 134, 98),
    (43, 128, 93): (24, 110, 84),
    (36, 107, 86): (18, 92, 72),
    (36, 104, 80): (18, 92, 72),
    (31, 89, 72): (14, 74, 58),
    (64, 143, 121): (28, 118, 96),
    (45, 122, 114): (20, 96, 82),
    (32, 91, 94): (14, 72, 66),
    (32, 94, 85): (14, 72, 66),
}

# Realidea enemybasePradera / playerbasePradera 10 colors -> Field Day
PRADERA_TO_FIELD = {
    (160, 176, 120): (196, 225, 116),
    (144, 168, 104): (177, 216, 109),
    (128, 160, 88): (153, 199, 96),
    (104, 144, 72): (126, 178, 84),
    (72, 128, 40): (57, 128, 64),
    (232, 152, 64): (238, 206, 149),
    (208, 128, 48): (235, 200, 145),
    (176, 160, 56): (229, 191, 133),
    (168, 96, 32): (218, 175, 117),
    (120, 56, 24): (133, 91, 78),
}

# Realidea enemybasePradera / playerbasePradera 10 colors -> FieldAlt Day
PRADERA_TO_ALT = {
    (160, 176, 120): (148, 178, 102),
    (144, 168, 104): (133, 164, 86),
    (128, 160, 88): (118, 149, 74),
    (104, 144, 72): (98, 128, 60),
    (72, 128, 40): (44, 88, 48),
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


def transform_eve(im: Image.Image) -> Image.Image:
    """Warm golden-amber late-afternoon twilight shading (2x2-clean)."""
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
                nr = clamp(r * 0.96 + 16)
                ng = clamp(g * 0.84 + 2)
                nb = clamp(b * 0.72 - 2)
                cache[key] = (nr, ng, nb)
            nr, ng, nb = cache[key]
            for oy in (0, 1):
                for ox in (0, 1):
                    if px[x + ox, y + oy][3] == 255:
                        px[x + ox, y + oy] = (nr, ng, nb, 255)
    return out


def transform_night(im: Image.Image) -> Image.Image:
    """Cool deep indigo-blue moonlight shading (2x2-clean)."""
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
                ng = clamp(g * 0.62 - 2)
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
    eb_tpl = Image.open(REALIDEA_DIR / "enemybasePradera.png").convert("RGBA")
    pb_tpl = Image.open(REALIDEA_DIR / "playerbasePradera.png").convert("RGBA")

    f_day = Image.open(SRC_FIELD).convert("RGBA")
    f_eve = transform_eve(f_day)
    f_night = transform_night(f_day)
    add_fireflies(f_night)

    f_eb_day = recolor_exact(eb_tpl, PRADERA_TO_FIELD)
    f_pb_day = recolor_exact(pb_tpl, PRADERA_TO_FIELD)
    f_eb_eve, f_pb_eve = transform_eve(f_eb_day), transform_eve(f_pb_day)
    f_eb_night, f_pb_night = transform_night(f_eb_day), transform_night(f_pb_day)

    a_day = recolor_exact(f_day, FIELD_TO_ALT)
    a_eve = transform_eve(a_day)
    a_night = transform_night(a_day)
    add_fireflies(a_night)

    a_eb_day = recolor_exact(eb_tpl, PRADERA_TO_ALT)
    a_pb_day = recolor_exact(pb_tpl, PRADERA_TO_ALT)
    a_eb_eve, a_pb_eve = transform_eve(a_eb_day), transform_eve(a_pb_day)
    a_eb_night, a_pb_night = transform_night(a_eb_day), transform_night(a_pb_day)

    outputs = [
        ("battlebgField.png", f_day), ("battlebgFieldEve.png", f_eve), ("battlebgFieldNight.png", f_night),
        ("enemybaseField.png", f_eb_day), ("enemybaseFieldEve.png", f_eb_eve), ("enemybaseFieldNight.png", f_eb_night),
        ("playerbaseField.png", f_pb_day), ("playerbaseFieldEve.png", f_pb_eve), ("playerbaseFieldNight.png", f_pb_night),
        ("battlebgFieldAlt.png", a_day), ("battlebgFieldAltEve.png", a_eve), ("battlebgFieldAltNight.png", a_night),
        ("enemybaseFieldAlt.png", a_eb_day), ("enemybaseFieldAltEve.png", a_eb_eve), ("enemybaseFieldAltNight.png", a_eb_night),
        ("playerbaseFieldAlt.png", a_pb_day), ("playerbaseFieldAltEve.png", a_pb_eve), ("playerbaseFieldAltNight.png", a_pb_night),
    ]
    for name, img in outputs:
        img.save(BB_DIR / name)

    render_review("Field", "field_battleback_review.png", [
        ("DIA", f_day, f_eb_day, f_pb_day),
        ("ATARDECER Eve", f_eve, f_eb_eve, f_pb_eve),
        ("NOCHE Night", f_night, f_eb_night, f_pb_night),
    ])
    render_review("FieldAlt", "fieldalt_battleback_review.png", [
        ("DIA", a_day, a_eb_day, a_pb_day),
        ("ATARDECER Eve", a_eve, a_eb_eve, a_pb_eve),
        ("NOCHE Night", a_night, a_eb_night, a_pb_night),
    ])
    print("Installed all 18 Field + FieldAlt files cleanly.")


if __name__ == "__main__":
    main()
