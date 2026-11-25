"""Install PeakAzogue battleback (512x384) and matching Realidea Monte platforms.

Replaces the 3 PeakAzogue files in Graphics/Battlebacks/:
  - battlebgPeakAzogue.png (512x384)
  - enemybasePeakAzogue.png (256x128, Realidea enemybaseMonte geometry)
  - playerbasePeakAzogue.png (512x64, Realidea playerbaseMonte geometry)
"""

from collections import deque
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SRC_PEAK = Path(
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795615567725_7f89fa94.png"
)
REALIDEA_DIR = Path(r"C:\Users\apera\Downloads\Battlebacks")
BB_DIR = ROOT / "Graphics" / "Battlebacks"

# Warm sunset ochre-brown mountain summit palette (matching MountainEve 2nd rock)
GROUND_TO_SUMMIT = {
    (239, 181, 69): (178, 122, 80),
    (234, 155, 62): (166, 113, 75),
    (240, 129, 56): (154, 104, 70),
    (200, 141, 2): (132, 88, 62),
    (166, 95, 0): (112, 74, 54),
    (142, 83, 4): (96, 62, 46),
    (130, 87, 31): (96, 62, 46),
    (118, 69, 6): (78, 50, 38),
    (98, 70, 6): (78, 50, 38),
}

# Realidea enemybaseMonte / playerbaseMonte 15-color template mapping
MONTE_TO_PEAK = {
    (192, 160, 144): (188, 132, 88),
    (176, 152, 136): (178, 122, 80),
    (168, 144, 112): (178, 122, 80),
    (144, 120, 80): (154, 104, 70),
    (128, 128, 120): (154, 104, 70),
    (104, 104, 96): (132, 88, 62),
    (96, 88, 80): (132, 88, 62),
    (88, 80, 64): (112, 74, 54),
    (128, 104, 32): (154, 104, 70),
    (112, 96, 32): (154, 104, 70),
    (80, 72, 32): (112, 74, 54),
    (48, 32, 16): (78, 50, 38),
}


def build_sky_mask(im: Image.Image) -> list[list[bool]]:
    """Flood-fill sky & sunset clouds from y=0 down to the horizon ridge and pines."""
    px = im.load()
    nw, nh = 256, 192
    mask = [[False] * nw for _ in range(nh)]
    stop_colors = {(166, 95, 0), (142, 83, 4), (118, 69, 6), (98, 70, 6), (59, 45, 48)}

    def is_sky(nx: int, ny: int) -> bool:
        if ny >= 80:
            return False
        return px[nx * 2, ny * 2][:3] not in stop_colors

    q = deque()
    for nx in range(nw):
        if is_sky(nx, 0):
            mask[0][nx] = True
            q.append((nx, 0))
    while q:
        cx, cy = q.popleft()
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = cx + ox, cy + oy
            if 0 <= nx < nw and 0 <= ny < nh and not mask[ny][nx] and is_sky(nx, ny):
                mask[ny][nx] = True
                q.append((nx, ny))
    return mask


def recolor_monte(tpl: Image.Image, mapping: dict) -> Image.Image:
    out = tpl.copy()
    px = out.load()
    fallback = mapping[(88, 80, 64)]
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a == 255:
                nr, ng, nb = mapping.get((r, g, b), fallback)
                px[x, y] = (nr, ng, nb, 255)
    return out


def main():
    src = Image.open(SRC_PEAK).convert("RGBA")
    sky_mask = build_sky_mask(src)
    bg = src.copy()
    px = bg.load()

    pine_protected = {(142, 83, 4), (130, 87, 31), (118, 69, 6), (98, 70, 6)}
    for ny in range(192):
        y = ny * 2
        for nx in range(256):
            if sky_mask[ny][nx]:
                continue
            x = nx * 2
            r, g, b, a = px[x, y]
            if a != 255:
                continue
            in_pine_box = (x < 140 and y < 186) or (x > 452 and y < 176)
            if in_pine_box and (r, g, b) in pine_protected:
                continue
            rep = GROUND_TO_SUMMIT.get((r, g, b))
            if rep is not None:
                for oy in (0, 1):
                    for ox in (0, 1):
                        px[x + ox, y + oy] = (rep[0], rep[1], rep[2], 255)

    eb = recolor_monte(Image.open(REALIDEA_DIR / "enemybaseMonte.png").convert("RGBA"), MONTE_TO_PEAK)
    pb = recolor_monte(Image.open(REALIDEA_DIR / "playerbaseMonte.png").convert("RGBA"), MONTE_TO_PEAK)

    bg.save(BB_DIR / "battlebgPeakAzogue.png")
    eb.save(BB_DIR / "enemybasePeakAzogue.png")
    pb.save(BB_DIR / "playerbasePeakAzogue.png")

    sheet = Image.new("RGBA", (532, 424), (22, 25, 34, 255))
    draw = ImageDraw.Draw(sheet)
    draw.text((14, 6), "PeakAzogue - (512x384)", fill=(237, 189, 98, 255))
    comp = bg.copy()
    comp.alpha_composite(eb, (256, 112))
    comp.alpha_composite(pb, (-128, 240))
    for dx in range(0, 512, 8):
        ImageDraw.Draw(comp).line([(dx, 304), (dx + 4, 304)], fill=(255, 255, 255, 110))
    sheet.alpha_composite(comp, (10, 26))
    sheet.save(ROOT / "previews" / "peakazogue_battleback_review.png")
    print("Installed PeakAzogue cleanly.")


if __name__ == "__main__":
    main()
