"""Install Beach battleback (512x384 Day, Eve, Night) and matching Realidea Playa platforms.

Replaces the 9 Beach files in Graphics/Battlebacks/:
  - battlebgBeach{,Eve,Night}.png (512x384)
  - enemybaseBeach{,Eve,Night}.png (256x128, Realidea enemybasePlaya geometry)
  - playerbaseBeach{,Eve,Night}.png (512x64, Realidea playerbasePlaya geometry)
"""

from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SRC_BEACH = Path(
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795613483568_7d0ee237.png"
)
SRC_EVE_SKY = Path(
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795611441951_49363f9d.png"
)
SRC_NIGHT_SKY = Path(
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795611435773_d7d0332a.png"
)
REALIDEA_DIR = Path(r"C:\Users\apera\Downloads\Battlebacks")
BB_DIR = ROOT / "Graphics" / "Battlebacks"

SKY_COLORS = {
    (85, 212, 238), (99, 155, 255), (87, 182, 252),
    (213, 245, 250), (255, 255, 255), (151, 245, 221),
}

# Realidea Playa platform (9 colors) -> uploaded Beach Day sand palette
PLAYA_TO_BEACH_DAY = {
    (240, 224, 168): (251, 245, 202),
    (240, 216, 152): (251, 245, 202),
    (232, 208, 136): (250, 239, 192),
    (224, 200, 120): (249, 233, 183),
    (216, 192, 120): (247, 224, 164),
    (208, 184, 120): (245, 214, 145),
    (192, 176, 120): (235, 177, 121),
    (136, 120, 80): (207, 147, 99),
    (88, 64, 32): (158, 107, 70),
}

# Beach Day -> Eve palette (warm sunset reflection on water, palms, hills & sand)
BEACH_TO_EVE = {
    # Sand
    (251, 245, 202): (246, 214, 174),
    (250, 239, 192): (242, 205, 164),
    (249, 233, 183): (238, 196, 154),
    (247, 224, 164): (230, 184, 142),
    (245, 214, 145): (222, 172, 130),
    (235, 177, 121): (198, 138, 108),
    (207, 147, 99): (168, 108, 88),
    (158, 107, 70): (124, 78, 68),
    # Palm trunks & hills & foliage
    (150, 84, 52): (138, 70, 56),
    (122, 77, 60): (106, 62, 60),
    (111, 58, 51): (94, 46, 52),
    (116, 203, 37): (122, 166, 46),
    (71, 151, 47): (82, 124, 52),
    (47, 151, 48): (62, 118, 56),
    (60, 123, 56): (66, 98, 60),
    (56, 126, 75): (62, 98, 72),
    (51, 94, 66): (52, 74, 64),
    # Ocean & surf foam (sunset twilight reflection)
    (59, 59, 120): (82, 54, 98),
    (63, 68, 143): (96, 62, 114),
    (73, 85, 189): (118, 78, 134),
    (82, 117, 244): (148, 98, 146),
    (99, 155, 255): (186, 124, 148),
    (85, 212, 238): (216, 158, 154),
    (151, 245, 221): (238, 194, 174),
    (213, 245, 250): (248, 220, 198),
    (255, 255, 255): (255, 238, 222),
}

# Beach Day -> Night palette (moonlit cool ocean, muted nocturnal sand & dark foliage)
BEACH_TO_NIGHT = {
    # Sand (clearly cooler & darker nocturnal sand matching platforms 1:1)
    (251, 245, 202): (202, 198, 176),
    (250, 239, 192): (192, 188, 168),
    (249, 233, 183): (182, 178, 158),
    (247, 224, 164): (168, 164, 144),
    (245, 214, 145): (154, 148, 130),
    (235, 177, 121): (128, 122, 112),
    (207, 147, 99): (102, 98, 96),
    (158, 107, 70): (74, 72, 76),
    # Palm trunks & hills & foliage
    (150, 84, 52): (92, 62, 58),
    (122, 77, 60): (72, 52, 56),
    (111, 58, 51): (60, 40, 48),
    (116, 203, 37): (52, 108, 62),
    (71, 151, 47): (36, 82, 56),
    (47, 151, 48): (28, 76, 54),
    (60, 123, 56): (30, 66, 54),
    (56, 126, 75): (30, 68, 66),
    (51, 94, 66): (26, 50, 56),
    # Ocean & moonlit surf foam
    (59, 59, 120): (22, 30, 68),
    (63, 68, 143): (28, 38, 84),
    (73, 85, 189): (36, 50, 104),
    (82, 117, 244): (46, 68, 128),
    (99, 155, 255): (62, 92, 152),
    (85, 212, 238): (82, 128, 168),
    (151, 245, 221): (122, 164, 186),
    (213, 245, 250): (168, 196, 216),
    (255, 255, 255): (208, 222, 238),
}


def recolor_image(im: Image.Image, pal: dict[tuple[int, int, int], tuple[int, int, int]]) -> Image.Image:
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a == 255 and (r, g, b) in pal:
                nr, ng, nb = pal[(r, g, b)]
                px[x, y] = (nr, ng, nb, 255)
    return out


def apply_sky_transplant(bg_day: Image.Image, bg_recolored: Image.Image, sky_src: Image.Image, is_eve: bool) -> Image.Image:
    out = bg_recolored.copy()
    dpx = bg_day.load()
    opx = out.load()
    spx = sky_src.load()
    # For Night: shift the sky horizontally by -64px (even 2x2 step, wrap around) so the moon sits cleanly over the open sea
    x_shift = 0 if is_eve else 64
    for y in range(0, 78, 2):
        for x in range(0, 512, 2):
            if dpx[x, y][:3] in SKY_COLORS:
                sx = (x + x_shift) % 512
                sr, sg, sb, _ = spx[sx, y]
                if is_eve and ((sb > sg + 5 and sr < 210) or (sr < 205 and sg < 150)):
                    col = (236, 148, 86, 255)
                else:
                    col = (sr, sg, sb, 255)
                for oy in (0, 1):
                    for ox in (0, 1):
                        if dpx[x + ox, y + oy][:3] in SKY_COLORS:
                            opx[x + ox, y + oy] = col
    return out


def main():
    bg_day = Image.open(SRC_BEACH).convert("RGBA")
    sky_eve = Image.open(SRC_EVE_SKY).convert("RGBA")
    sky_night = Image.open(SRC_NIGHT_SKY).convert("RGBA")

    bg_eve = apply_sky_transplant(bg_day, recolor_image(bg_day, BEACH_TO_EVE), sky_eve, is_eve=True)
    bg_night = apply_sky_transplant(bg_day, recolor_image(bg_day, BEACH_TO_NIGHT), sky_night, is_eve=False)

    eb_tpl = Image.open(REALIDEA_DIR / "enemybasePlaya.png").convert("RGBA")
    pb_tpl = Image.open(REALIDEA_DIR / "playerbasePlaya.png").convert("RGBA")

    eb_day = recolor_image(eb_tpl, PLAYA_TO_BEACH_DAY)
    eb_eve = recolor_image(eb_day, BEACH_TO_EVE)
    eb_night = recolor_image(eb_day, BEACH_TO_NIGHT)

    pb_day = recolor_image(pb_tpl, PLAYA_TO_BEACH_DAY)
    pb_eve = recolor_image(pb_day, BEACH_TO_EVE)
    pb_night = recolor_image(pb_day, BEACH_TO_NIGHT)

    outputs = [
        ("battlebgBeach.png", bg_day),
        ("battlebgBeachEve.png", bg_eve),
        ("battlebgBeachNight.png", bg_night),
        ("enemybaseBeach.png", eb_day),
        ("enemybaseBeachEve.png", eb_eve),
        ("enemybaseBeachNight.png", eb_night),
        ("playerbaseBeach.png", pb_day),
        ("playerbaseBeachEve.png", pb_eve),
        ("playerbaseBeachNight.png", pb_night),
    ]
    for fname, im in outputs:
        im.save(BB_DIR / fname)

    prev = ROOT / "previews"
    prev.mkdir(exist_ok=True)
    sheet = Image.new("RGBA", (1560, 424), (22, 25, 34, 255))
    draw = ImageDraw.Draw(sheet)
    panels = [
        ("Beach - DIA (512x384)", bg_day, eb_day, pb_day),
        ("Beach - ATARDECER Eve (512x384)", bg_eve, eb_eve, pb_eve),
        ("Beach - NOCHE Night (512x384)", bg_night, eb_night, pb_night),
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

    sheet.save(prev / "beach_battleback_review.png")
    print("Installed 9 Beach files and saved previews/beach_battleback_review.png")


if __name__ == "__main__":
    main()
