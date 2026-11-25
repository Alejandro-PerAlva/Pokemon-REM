"""Install Bridge battleback (512x384 Day, Eve, Night) and textured cobblestone platforms.

Replaces the 9 Bridge files in Graphics/Battlebacks/:
  - battlebgBridge{,Eve,Night}.png (512x384)
  - enemybaseBridge{,Eve,Night}.png (256x128, exact Realidea bbox=(4,36,252,96))
  - playerbaseBridge{,Eve,Night}.png (512x64, exact Realidea bbox=(36,14,476,64))
"""

from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SRC_BRIDGE_DAY = Path(
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795610306593_bba46856.png"
)
SRC_BRIDGE_NIGHT = Path(
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795610642993_aa8bf17a.png"
)
SRC_EVE_SKY = Path(
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795611441951_49363f9d.png"
)
REALIDEA_DIR = Path(r"C:\Users\apera\Downloads\Battlebacks")
BB_DIR = ROOT / "Graphics" / "Battlebacks"

# Bridge Day -> Eve palette swap
PAL_EVE = {
    (30, 153, 244): (138, 72, 118),
    (48, 127, 229): (108, 56, 108),
    (74, 145, 234): (162, 86, 114),
    (71, 162, 251): (208, 112, 98),
    (102, 178, 251): (236, 148, 92),
    (154, 202, 255): (246, 184, 118),
    (183, 215, 255): (248, 202, 156),
    (188, 212, 255): (212, 140, 142),
    (202, 220, 255): (236, 176, 154),
    (234, 240, 255): (255, 228, 196),
    (216, 210, 204): (220, 196, 180),
    (201, 195, 189): (206, 182, 168),
    (191, 185, 179): (188, 164, 152),
    (175, 169, 163): (166, 144, 136),
    (137, 139, 138): (126, 112, 114),
    (128, 122, 116): (118, 102, 100),
    (114, 107, 102): (104, 88, 86),
    (92, 85, 80): (84, 70, 70),
    (72, 68, 66): (64, 54, 56),
    (61, 59, 58): (52, 44, 48),
    (49, 49, 49): (42, 36, 42),
    (34, 34, 38): (30, 24, 34),
}

# Subtle cool moonlit stone tint for Night platforms (harmonizes with uploaded Night bridge stones)
PAL_NIGHT_PLAT = {
    (216, 210, 204): (194, 196, 208),
    (201, 195, 189): (178, 180, 192),
    (191, 185, 179): (162, 164, 178),
    (175, 169, 163): (144, 146, 160),
    (137, 139, 138): (114, 116, 130),
    (128, 122, 116): (102, 104, 118),
    (114, 107, 102): (90, 92, 106),
    (92, 85, 80): (74, 76, 88),
    (72, 68, 66): (56, 58, 70),
    (61, 59, 58): (48, 50, 60),
    (49, 49, 49): (38, 40, 48),
    (34, 34, 38): (26, 28, 36),
}

CIUDAD_TO_BRIDGE_DAY = {
    (232, 224, 232): (191, 185, 179),
    (224, 216, 224): (191, 185, 179),
    (216, 208, 216): (191, 185, 179),
    (208, 200, 208): (175, 169, 163),
    (200, 192, 200): (175, 169, 163),
    (184, 168, 184): (137, 139, 138),
    (168, 152, 160): (114, 107, 102),
    (136, 120, 128): (92, 85, 80),
    (96, 80, 96): (72, 68, 66),
    (64, 48, 64): (49, 49, 49),
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


def clean_stray_purple(im: Image.Image) -> Image.Image:
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            if px[x, y][:3] == (118, 70, 240):
                px[x, y] = (34, 34, 38, 255)
    return out


def add_cobble_detail(tpl_im: Image.Image, is_player: bool) -> Image.Image:
    """Apply subtle carved stone bevel, upper highlight rim, and organic cobble seams on 2x2 grid."""
    base = recolor_image(tpl_im, CIUDAD_TO_BRIDGE_DAY)
    w, h = base.size
    nw, nh = w // 2, h // 2
    px = base.load()

    HIGH_EDGE = (216, 210, 204, 255)
    HIGH = (201, 195, 189, 255)
    BASE = (191, 185, 179, 255)
    SHAD = (175, 169, 163, 255)
    SEAM = (128, 122, 116, 255)

    # Read top-face mask (where template was bright face (232/224/216/208/200))
    tpx = tpl_im.load()
    face = [[False] * nw for _ in range(nh)]
    for ny in range(nh):
        for nx in range(nw):
            rgb = tpx[nx * 2, ny * 2][:3]
            if rgb in ((232, 224, 232), (224, 216, 224), (216, 208, 216), (208, 200, 208), (200, 192, 200)):
                face[ny][nx] = True

    # Subtle Voronoi-like stone slab centers in native pixels (for organic rounded flagstones)
    if not is_player:
        centers = [(28, 28), (64, 25), (100, 29), (44, 38), (84, 37)]
    else:
        centers = [(44, 15), (92, 13), (144, 14), (196, 16), (70, 25), (124, 24), (178, 25)]

    def put_2x2(nx: int, ny: int, rgba: tuple[int, int, int, int]):
        for oy in (0, 1):
            for ox in (0, 1):
                px[nx * 2 + ox, ny * 2 + oy] = rgba

    for ny in range(nh):
        for nx in range(nw):
            if not face[ny][nx]:
                continue
            # Check vertical neighbors to add top rim highlight & bottom inner lip shadow
            above_face = ny > 0 and face[ny - 1][nx]
            below_face = ny + 1 < nh and face[ny + 1][nx]
            if not above_face:
                put_2x2(nx, ny, HIGH_EDGE)
                continue
            if not below_face:
                put_2x2(nx, ny, SHAD)
                continue

            # Distance to nearest and 2nd-nearest stone center (anisotropic for perspective!)
            dists = sorted(((nx - cx) * 0.55) ** 2 + ((ny - cy) * 1.35) ** 2 for cx, cy in centers)
            d1, d2 = dists[0] ** 0.5, dists[1] ** 0.5
            diff = d2 - d1
            if diff < 0.72:
                put_2x2(nx, ny, SEAM)
            elif diff < 1.65:
                # Light side on top-left of each slab, slight shadow on bottom-right
                put_2x2(nx, ny, HIGH if (ny < 32 if not is_player else ny < 19) else BASE)
            else:
                put_2x2(nx, ny, HIGH if (ny % 7 == 0 and nx % 11 == 0) else BASE)

    return base


def main():
    bg_day = clean_stray_purple(Image.open(SRC_BRIDGE_DAY).convert("RGBA"))
    bg_eve = recolor_image(bg_day, PAL_EVE)
    # Transplant genuine elongated-cloud sunset sky onto Bridge Eve above parapet
    # (keep strictly sky/cloud colors so desert rocks/dunes at horizon never leak in!)
    sky_eve = Image.open(SRC_EVE_SKY).convert("RGBA")
    sky_colors = {
        (30, 153, 244), (48, 127, 229), (74, 145, 234), (71, 162, 251),
        (102, 178, 251), (154, 202, 255), (183, 215, 255), (188, 212, 255),
        (202, 220, 255), (234, 240, 255),
    }
    # Strict whitelist of genuine sunset sky & cloud RGBs from Desert Eve (never rocks/dunes!)
    eve_sky_rgb = {
        (120, 149, 244), (195, 134, 153), (206, 158, 126), (221, 133, 94),
        (236, 148, 86), (255, 162, 126), (255, 198, 70), (255, 233, 144),
        (255, 227, 130), (242, 172, 112), (249, 194, 108), (239, 152, 107),
        (246, 178, 118), (255, 212, 102), (244, 164, 96), (232, 142, 92),
    }
    dpx = bg_day.load()
    epx = bg_eve.load()
    spx = sky_eve.load()
    for y in range(0, 250, 2):
        for x in range(0, 512, 2):
            if dpx[x, y][:3] in sky_colors:
                sr, sg, sb, _ = spx[x, y]
                # Reject any rock/sand pixel (violet/reddish rock or dark sand) and fill with warm sunset cloud/horizon
                is_rock_or_sand = (sr, sg, sb) not in eve_sky_rgb and (
                    (sb > sg + 5 and sr < 210) or (sr < 205 and sg < 150) or y > 120
                )
                if is_rock_or_sand:
                    col = (255, 233, 144, 255) if y > 125 else ((255, 198, 70, 255) if y > 70 else (236, 148, 86, 255))
                else:
                    col = (sr, sg, sb, 255)
                for oy in (0, 1):
                    for ox in (0, 1):
                        if dpx[x + ox, y + oy][:3] in sky_colors:
                            epx[x + ox, y + oy] = col

    bg_night_raw = clean_stray_purple(Image.open(SRC_BRIDGE_NIGHT).convert("RGBA"))
    bg_night = recolor_image(bg_night_raw, PAL_NIGHT_PLAT)  # tint bridge stone to match Night platforms!

    eb_tpl = Image.open(REALIDEA_DIR / "enemybaseCiudad.png").convert("RGBA")
    pb_tpl = Image.open(REALIDEA_DIR / "playerbaseCiudad.png").convert("RGBA")

    eb_day = add_cobble_detail(eb_tpl, is_player=False)
    eb_eve = recolor_image(eb_day, PAL_EVE)
    eb_night = recolor_image(eb_day, PAL_NIGHT_PLAT)

    pb_day = add_cobble_detail(pb_tpl, is_player=True)
    pb_eve = recolor_image(pb_day, PAL_EVE)
    pb_night = recolor_image(pb_day, PAL_NIGHT_PLAT)

    outputs = [
        ("battlebgBridge.png", bg_day),
        ("battlebgBridgeEve.png", bg_eve),
        ("battlebgBridgeNight.png", bg_night),
        ("enemybaseBridge.png", eb_day),
        ("enemybaseBridgeEve.png", eb_eve),
        ("enemybaseBridgeNight.png", eb_night),
        ("playerbaseBridge.png", pb_day),
        ("playerbaseBridgeEve.png", pb_eve),
        ("playerbaseBridgeNight.png", pb_night),
    ]
    for fname, im in outputs:
        im.save(BB_DIR / fname)

    prev = ROOT / "previews"
    prev.mkdir(exist_ok=True)
    sheet = Image.new("RGBA", (1560, 424), (22, 25, 34, 255))
    draw = ImageDraw.Draw(sheet)
    panels = [
        ("Bridge - DIA (512x384)", bg_day, eb_day, pb_day),
        ("Bridge - ATARDECER Eve (512x384)", bg_eve, eb_eve, pb_eve),
        ("Bridge - NOCHE Night (512x384)", bg_night, eb_night, pb_night),
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

    sheet.save(prev / "bridge_battleback_review.png")
    print("Updated Bridge platforms with cobblestone texture & Day/Eve/Night polish.")


if __name__ == "__main__":
    main()
