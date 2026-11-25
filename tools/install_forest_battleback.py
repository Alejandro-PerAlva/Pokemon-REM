"""Install Forest battleback (512x384 Day, Eve, Night) and matching Realidea Bosque platforms.

Replaces the 9 Forest files in Graphics/Battlebacks/:
  - battlebgForest{,Eve,Night}.png (512x384)
  - enemybaseForest{,Eve,Night}.png (256x128, Realidea enemybaseBosque geometry)
  - playerbaseForest{,Eve,Night}.png (512x64, Realidea playerbaseBosque geometry)
"""

from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SRC_FOREST = Path(
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795612761118_99a8b879.png"
)
REALIDEA_DIR = Path(r"C:\Users\apera\Downloads\Battlebacks")
BB_DIR = ROOT / "Graphics" / "Battlebacks"

# Realidea enemybaseBosque/playerbaseBosque (10 colors) -> uploaded Forest Day ground palette
BOSQUE_TO_FOREST_DAY = {
    # Grass blade highlights -> mid -> shadow
    (136, 224, 168): (78, 134, 108),   # bright highlight tip
    (120, 216, 152): (68, 124, 100),
    (160, 208, 80): (68, 124, 100),
    (96, 208, 128): (57, 112, 94),     # main forest grass
    (72, 184, 104): (46, 104, 76),     # mid forest grass
    (32, 160, 64): (35, 79, 62),       # deep grass shadow
    # Dirt rim -> olive-beige forest path
    (224, 192, 96): (145, 138, 112),   # rim light
    (192, 160, 72): (125, 124, 105),   # rim mid
    (144, 120, 48): (108, 111, 97),    # rim shadow
    (88, 72, 32): (38, 48, 44),        # crisp dark outline
}


def clamp(v: float) -> int:
    return max(0, min(255, int(round(v))))


def transform_eve(im: Image.Image, is_bg: bool = False) -> Image.Image:
    """Apply subtle, muted twilight shading between Day and Night (no bright orange blast!)."""
    out = im.copy()
    px = out.load()
    w, h = out.size
    cache: dict[tuple[int, int, int, int], tuple[int, int, int]] = {}
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b, a = px[x, y]
            if a != 255:
                continue
            is_distant_sky = is_bg and b > r + 8 and b > g
            key = (r, g, b, 1 if is_distant_sky else 0)
            if key not in cache:
                if is_distant_sky:
                    # Subtle muted dusty mauve/amber twilight filtering through deep canopy
                    nr = clamp(r * 1.10 + 18)
                    ng = clamp(g * 0.92 + 2)
                    nb = clamp(b * 0.86 + 4)
                else:
                    # Gentle muted warm-dusk midpoint between Day and Night
                    nr = clamp(r * 0.98 + 6)
                    ng = clamp(g * 0.90 - 2)
                    nb = clamp(b * 0.84 - 2)
                cache[key] = (nr, ng, nb)
            nr, ng, nb = cache[key]
            for oy in (0, 1):
                for ox in (0, 1):
                    if px[x + ox, y + oy][3] == 255:
                        px[x + ox, y + oy] = (nr, ng, nb, 255)
    return out


def transform_night(im: Image.Image) -> Image.Image:
    """Apply deep nocturnal blue-indigo shading consistently across Forest background & platforms."""
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


def add_forest_fireflies(im: Image.Image):
    """Add subtle 2x2 warm firefly glints in the dark background thicket of Forest Night."""
    px = im.load()
    spots = [(210, 48), (242, 76), (318, 36), (376, 62), (432, 44), (474, 82), (168, 92)]
    core = (232, 240, 156, 255)
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
    bg_day = Image.open(SRC_FOREST).convert("RGBA")
    bg_eve = transform_eve(bg_day, is_bg=True)
    bg_night = transform_night(bg_day)
    add_forest_fireflies(bg_night)

    eb_tpl = Image.open(REALIDEA_DIR / "enemybaseBosque.png").convert("RGBA")
    pb_tpl = Image.open(REALIDEA_DIR / "playerbaseBosque.png").convert("RGBA")

    eb_day = recolor_exact(eb_tpl, BOSQUE_TO_FOREST_DAY)
    eb_eve = transform_eve(eb_day, is_bg=False)
    eb_night = transform_night(eb_day)

    pb_day = recolor_exact(pb_tpl, BOSQUE_TO_FOREST_DAY)
    pb_eve = transform_eve(pb_day, is_bg=False)
    pb_night = transform_night(pb_day)

    outputs = [
        ("battlebgForest.png", bg_day),
        ("battlebgForestEve.png", bg_eve),
        ("battlebgForestNight.png", bg_night),
        ("enemybaseForest.png", eb_day),
        ("enemybaseForestEve.png", eb_eve),
        ("enemybaseForestNight.png", eb_night),
        ("playerbaseForest.png", pb_day),
        ("playerbaseForestEve.png", pb_eve),
        ("playerbaseForestNight.png", pb_night),
    ]
    for fname, im in outputs:
        im.save(BB_DIR / fname)

    prev = ROOT / "previews"
    prev.mkdir(exist_ok=True)
    sheet = Image.new("RGBA", (1560, 424), (22, 25, 34, 255))
    draw = ImageDraw.Draw(sheet)
    panels = [
        ("Forest - DIA (512x384)", bg_day, eb_day, pb_day),
        ("Forest - ATARDECER Eve (512x384)", bg_eve, eb_eve, pb_eve),
        ("Forest - NOCHE Night (512x384)", bg_night, eb_night, pb_night),
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

    sheet.save(prev / "forest_battleback_review.png")
    print("Installed 9 Forest files and saved previews/forest_battleback_review.png")


if __name__ == "__main__":
    main()
