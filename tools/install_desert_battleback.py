"""Install Desert battleback (512x384 Day, Eve, Night) and matching Realidea sand platforms.

Replaces the 9 Desert files in Graphics/Battlebacks/:
  - battlebgDesert{,Eve,Night}.png (512x384)
  - enemybaseDesert{,Eve,Night}.png (256x128, exact Realidea enemybaseDesierto geometry)
  - playerbaseDesert{,Eve,Night}.png (512x64, exact Realidea playerbaseDesierto geometry)
"""

from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SRC_DAY = Path(
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795611441953_4b6ab8a0.png"
)
SRC_EVE = Path(
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795611441951_49363f9d.png"
)
SRC_NIGHT = Path(
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795611435773_d7d0332a.png"
)
REALIDEA_DIR = Path(r"C:\Users\apera\Downloads\Battlebacks")
BB_DIR = ROOT / "Graphics" / "Battlebacks"

# Exact Realidea Desierto platform 9-color ramp -> uploaded Desert Day/Eve/Night sand palettes
DESERT_DAY_MAP = {
    (240, 207, 168): (249, 217, 114),
    (240, 195, 152): (249, 217, 114),
    (232, 186, 136): (245, 203, 96),
    (224, 176, 120): (241, 189, 79),
    (216, 170, 120): (226, 168, 64),
    (208, 163, 120): (211, 147, 49),
    (192, 159, 120): (188, 124, 45),
    (136, 106, 80): (160, 102, 30),
    (88, 50, 32): (123, 81, 31),
}

DESERT_EVE_MAP = {
    (240, 207, 168): (246, 210, 162),
    (240, 195, 152): (246, 210, 162),
    (232, 186, 136): (240, 193, 146),
    (224, 176, 120): (234, 177, 131),
    (216, 170, 120): (212, 153, 115),
    (208, 163, 120): (191, 130, 100),
    (192, 159, 120): (159, 105, 95),
    (136, 106, 80): (124, 83, 76),
    (88, 50, 32): (83, 62, 77),
}

DESERT_NIGHT_MAP = {
    (240, 207, 168): (216, 194, 152),
    (240, 195, 152): (216, 194, 152),
    (232, 186, 136): (205, 182, 140),
    (224, 176, 120): (194, 170, 128),
    (216, 170, 120): (170, 151, 113),
    (208, 163, 120): (146, 132, 98),
    (192, 159, 120): (114, 112, 92),
    (136, 106, 80): (82, 92, 76),
    (88, 50, 32): (46, 70, 74),
}

# Cool moonlit sand adjustment applied to battlebgDesertNight sand only (sky/cactus/rocks untouched)
BG_NIGHT_SAND_TINT = {
    (243, 217, 166): (216, 194, 152),
    (226, 189, 136): (194, 170, 128),
    (170, 147, 105): (146, 132, 98),
    (132, 124, 100): (114, 112, 92),
    (93, 102, 81): (82, 92, 76),
    (53, 81, 82): (46, 70, 74),
}


def recolor_image(im: Image.Image, pal: dict[tuple[int, int, int], tuple[int, int, int]]) -> Image.Image:
    out = im.copy()
    px = out.load()
    w, h = out.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 255 and (r, g, b) in pal:
                nr, ng, nb = pal[(r, g, b)]
                px[x, y] = (nr, ng, nb, 255)
    return out


def main():
    bg_day = Image.open(SRC_DAY).convert("RGBA")
    bg_eve = Image.open(SRC_EVE).convert("RGBA")
    bg_night = recolor_image(Image.open(SRC_NIGHT).convert("RGBA"), BG_NIGHT_SAND_TINT)

    eb_tpl = Image.open(REALIDEA_DIR / "enemybaseDesierto.png").convert("RGBA")
    pb_tpl = Image.open(REALIDEA_DIR / "playerbaseDesierto.png").convert("RGBA")

    eb_day = recolor_image(eb_tpl, DESERT_DAY_MAP)
    eb_eve = recolor_image(eb_tpl, DESERT_EVE_MAP)
    eb_night = recolor_image(eb_tpl, DESERT_NIGHT_MAP)

    pb_day = recolor_image(pb_tpl, DESERT_DAY_MAP)
    pb_eve = recolor_image(pb_tpl, DESERT_EVE_MAP)
    pb_night = recolor_image(pb_tpl, DESERT_NIGHT_MAP)

    outputs = [
        ("battlebgDesert.png", bg_day),
        ("battlebgDesertEve.png", bg_eve),
        ("battlebgDesertNight.png", bg_night),
        ("enemybaseDesert.png", eb_day),
        ("enemybaseDesertEve.png", eb_eve),
        ("enemybaseDesertNight.png", eb_night),
        ("playerbaseDesert.png", pb_day),
        ("playerbaseDesertEve.png", pb_eve),
        ("playerbaseDesertNight.png", pb_night),
    ]
    for fname, im in outputs:
        im.save(BB_DIR / fname)

    prev = ROOT / "previews"
    prev.mkdir(exist_ok=True)
    sheet = Image.new("RGBA", (1560, 424), (22, 25, 34, 255))
    draw = ImageDraw.Draw(sheet)
    panels = [
        ("Desert - DIA (512x384)", bg_day, eb_day, pb_day),
        ("Desert - ATARDECER Eve (512x384)", bg_eve, eb_eve, pb_eve),
        ("Desert - NOCHE Night (512x384)", bg_night, eb_night, pb_night),
    ]
    for i, (title, bg, eb, pb) in enumerate(panels):
        x0 = 10 + i * 518
        draw.text((x0 + 4, 6), title, fill=(237, 189, 98, 255))
        comp = bg.copy()
        comp.alpha_composite(eb, (256, 112))
        comp.alpha_composite(pb, (-128, 240))
        for dx in range(0, 512, 8):
            ImageDraw.Draw(comp).line([(dx, 304), (dx + 4, 304)], fill=(255, 255, 255, 110))
        sheet.alpha_composite(comp, (x0, 26))

    sheet.save(prev / "desert_battleback_review.png")
    print("Installed 9 Desert files (512x384 + Realidea sand bases) and saved previews/desert_battleback_review.png")


if __name__ == "__main__":
    main()
