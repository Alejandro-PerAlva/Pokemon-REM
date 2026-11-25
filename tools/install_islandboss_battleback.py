"""Install IslandBoss battleback (512x384 fixed) and moonlit water platforms.

Replaces the 3 IslandBoss files in Graphics/Battlebacks/:
  - battlebgIslandBoss.png (512x384)
  - enemybaseIslandBoss.png (256x128, exact Realidea bbox=(4,36,252,96))
  - playerbaseIslandBoss.png (512x64, exact Realidea bbox=(36,14,476,64))
"""

from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SRC_ISLAND = Path(
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795613768063_e9922658.png"
)
REALIDEA_DIR = Path(r"C:\Users\apera\Downloads\Battlebacks")
BB_DIR = ROOT / "Graphics" / "Battlebacks"


def make_moonlit_water_base(tpl_path: Path) -> Image.Image:
    """Use exact Realidea Astral silhouette/bbox and render a moonlit translucent water-ripple disc."""
    tpl = Image.open(tpl_path).convert("RGBA")
    w, h = tpl.size
    tpx = tpl.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = out.load()

    # Smooth translucent moonlit water-halo disc without artificial dot patterns
    cx = (w - 1) / 2.0
    cy = 66.0 if h == 128 else 39.0
    rx = 124.0 if h == 128 else 220.0
    ry = 30.0 if h == 128 else 25.0

    for y in range(h):
        for x in range(w):
            r, g, b, a = tpx[x, y]
            if a == 0:
                continue
            d = (((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2) ** 0.5
            if (r, g, b) == (152, 112, 48):
                px[x, y] = (176, 206, 248, 220)
            elif (r, g, b) == (216, 176, 88):
                px[x, y] = (238, 228, 172, 195)
            else:
                # Subtle radial gradient: darker sapphire center fading into soft cyan-gold rim glow
                alpha = int(85 + min(1.0, d) * 65)
                px[x, y] = (62, 102, 184, alpha) if d > 0.72 else (38, 68, 146, alpha)
    return out


def main():
    bg = Image.open(SRC_ISLAND).convert("RGBA")
    eb = make_moonlit_water_base(REALIDEA_DIR / "enemybaseAstral.png")
    pb = make_moonlit_water_base(REALIDEA_DIR / "playerbaseAstral.png")

    bg.save(BB_DIR / "battlebgIslandBoss.png")
    eb.save(BB_DIR / "enemybaseIslandBoss.png")
    pb.save(BB_DIR / "playerbaseIslandBoss.png")

    prev = ROOT / "previews"
    prev.mkdir(exist_ok=True)
    comp = bg.copy()
    comp.alpha_composite(eb, (256, 112))
    comp.alpha_composite(pb, (-128, 240))
    for dx in range(0, 512, 8):
        ImageDraw.Draw(comp).line([(dx, 304), (dx + 4, 304)], fill=(255, 255, 255, 110))

    sheet = Image.new("RGBA", (532, 424), (22, 25, 34, 255))
    ImageDraw.Draw(sheet).text((12, 6), "IslandBoss - Isla Sueno / Isla Pesadilla (512x384 fija)", fill=(237, 189, 98, 255))
    sheet.alpha_composite(comp, (10, 26))
    sheet.save(prev / "islandboss_battleback_review.png")
    print("Installed 3 IslandBoss files and saved previews/islandboss_battleback_review.png")


if __name__ == "__main__":
    main()
