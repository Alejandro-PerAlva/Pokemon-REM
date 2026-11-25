"""Install Swamp battleback (512x384 Day, Eve, Night) and matching Realidea Bosque platforms.

Replaces the 9 Swamp files in Graphics/Battlebacks/:
  - battlebgSwamp{,Eve,Night}.png (512x384)
  - enemybaseSwamp{,Eve,Night}.png (256x128, Realidea enemybaseBosque geometry)
  - playerbaseSwamp{,Eve,Night}.png (512x64, Realidea playerbaseBosque geometry)
"""

from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SRC_SWAMP = Path(
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795615253221_01760fef.png"
)
REALIDEA_DIR = Path(r"C:\Users\apera\Downloads\Battlebacks")
BB_DIR = ROOT / "Graphics" / "Battlebacks"

# Realidea enemybaseBosque/playerbaseBosque (10 colors) -> uploaded Swamp Day mud & marsh grass palette
BOSQUE_TO_SWAMP_DAY = {
    (136, 224, 168): (62, 156, 108),
    (120, 216, 152): (52, 141, 98),
    (160, 208, 80): (52, 141, 98),
    (96, 208, 128): (43, 124, 88),
    (72, 184, 104): (31, 102, 73),
    (32, 160, 64): (22, 74, 52),
    (224, 192, 96): (106, 98, 95),
    (192, 160, 72): (94, 87, 85),
    (144, 120, 48): (81, 77, 75),
    (88, 72, 32): (42, 38, 36),
}


def clamp(v: float) -> int:
    return max(0, min(255, int(round(v))))


def transform_eve(im: Image.Image, is_bg: bool = False) -> Image.Image:
    """Apply subtle, muted twilight shading between Day and Night (matching Forest Eve)."""
    out = im.copy()
    px = out.load()
    w, h = out.size
    cache: dict[tuple[int, int, int, int], tuple[int, int, int]] = {}
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b, a = px[x, y]
            if a != 255:
                continue
            is_distant_mist = is_bg and (r, g, b) == (72, 105, 97)
            key = (r, g, b, 1 if is_distant_mist else 0)
            if key not in cache:
                if is_distant_mist:
                    nr = clamp(r * 1.18 + 20)
                    ng = clamp(g * 0.84 + 2)
                    nb = clamp(b * 0.82 + 4)
                else:
                    nr = clamp(r * 0.88 + 8)
                    ng = clamp(g * 0.80 - 2)
                    nb = clamp(b * 0.78 + 2)
                cache[key] = (nr, ng, nb)
            nr, ng, nb = cache[key]
            for oy in (0, 1):
                for ox in (0, 1):
                    if px[x + ox, y + oy][3] == 255:
                        px[x + ox, y + oy] = (nr, ng, nb, 255)
    return out


def transform_night(im: Image.Image) -> Image.Image:
    """Apply deep nocturnal blue-indigo shading consistently across Swamp background & platforms."""
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
                nr = clamp(r * 0.62 - 4)
                ng = clamp(g * 0.68 - 2)
                nb = clamp(b * 0.86 + 10)
                cache[key] = (nr, ng, nb)
            nr, ng, nb = cache[key]
            for oy in (0, 1):
                for ox in (0, 1):
                    if px[x + ox, y + oy][3] == 255:
                        px[x + ox, y + oy] = (nr, ng, nb, 255)
    return out


def add_swamp_fireflies(im: Image.Image):
    """Add subtle 2x2 warm firefly glints in the misty swamp thicket of Swamp Night."""
    px = im.load()
    spots = [(154, 46), (222, 64), (296, 38), (358, 56), (424, 42), (472, 74), (192, 178)]
    core = (224, 238, 152, 255)
    for fx, fy in spots:
        for oy in (0, 1):
            for ox in (0, 1):
                px[fx + ox, fy + oy] = core


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


def main():
    bg_day = Image.open(SRC_SWAMP).convert("RGBA")
    bg_eve = transform_eve(bg_day, is_bg=True)
    bg_night = transform_night(bg_day)
    add_swamp_fireflies(bg_night)

    eb_tpl = Image.open(REALIDEA_DIR / "enemybaseBosque.png").convert("RGBA")
    pb_tpl = Image.open(REALIDEA_DIR / "playerbaseBosque.png").convert("RGBA")

    eb_day = recolor_exact(eb_tpl, BOSQUE_TO_SWAMP_DAY)
    pb_day = recolor_exact(pb_tpl, BOSQUE_TO_SWAMP_DAY)
    eb_eve = transform_eve(eb_day, is_bg=False)
    pb_eve = transform_eve(pb_day, is_bg=False)
    eb_night = transform_night(eb_day)
    pb_night = transform_night(pb_day)

    outputs = [
        ("battlebgSwamp.png", bg_day),
        ("battlebgSwampEve.png", bg_eve),
        ("battlebgSwampNight.png", bg_night),
        ("enemybaseSwamp.png", eb_day),
        ("enemybaseSwampEve.png", eb_eve),
        ("enemybaseSwampNight.png", eb_night),
        ("playerbaseSwamp.png", pb_day),
        ("playerbaseSwampEve.png", pb_eve),
        ("playerbaseSwampNight.png", pb_night),
    ]
    for name, img in outputs:
        img.save(BB_DIR / name)

    # Render 3-panel 512x384 review sheet
    sheet = Image.new("RGBA", (1560, 424), (22, 25, 34, 255))
    draw = ImageDraw.Draw(sheet)
    panels = [
        ("Swamp - DIA (512x384)", bg_day, eb_day, pb_day),
        ("Swamp - ATARDECER Eve (512x384)", bg_eve, eb_eve, pb_eve),
        ("Swamp - NOCHE Night (512x384)", bg_night, eb_night, pb_night),
    ]
    for i, (label, bg, eb, pb) in enumerate(panels):
        x0 = 10 + i * 518
        draw.text((x0 + 4, 6), label, fill=(237, 189, 98, 255))
        comp = bg.copy()
        comp.alpha_composite(eb, (256, 112))
        comp.alpha_composite(pb, (-128, 240))
        for dx in range(0, 512, 8):
            ImageDraw.Draw(comp).line([(dx, 304), (dx + 4, 304)], fill=(255, 255, 255, 110))
        sheet.alpha_composite(comp, (x0, 26))

    out_preview = ROOT / "previews" / "swamp_battleback_review.png"
    sheet.save(out_preview)
    print("Installed all 9 Swamp files cleanly.")


if __name__ == "__main__":
    main()
