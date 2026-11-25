"""Create and install battlebgPowerPlant.png (512x384, err2x2=0) integrated seamlessly with the room.

Strictly preserves the exact silhouette, wall-floor perspective line, and adjacent floor drum bounds
of media_1795621868311_391740de.png, converting only interior locker surfaces and lab props into
Power Plant gears, copper transformer windings, voltage diagnostics, and electric plasma dynamo.
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
BB_DIR = ROOT / "Graphics" / "Battlebacks"
SRC_BASE = Path(
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795621868311_391740de.png"
)


def set2(px, nx: int, ny: int, col: tuple[int, int, int]):
    if 0 <= nx < 256 and 0 <= ny < 192:
        c = (col[0], col[1], col[2], 255)
        x, y = nx * 2, ny * 2
        px[x, y] = c
        px[x + 1, y] = c
        px[x, y + 1] = c
        px[x + 1, y + 1] = c


def build_powerplant() -> Image.Image:
    src = Image.open(SRC_BASE).convert("RGBA")
    im = src.copy()
    spx = src.load()
    px = im.load()

    # Exact native palette from media_1795621868311_391740de.png
    OUT = (53, 53, 53)
    STEEL_DK = (64, 64, 66)
    STEEL_SH = (78, 92, 98)
    STEEL_MID = (110, 126, 138)
    STEEL_HI = (131, 150, 161)
    STEEL_LT = (165, 173, 181)

    SLATE_BLUE_DK = (68, 79, 132)
    SLATE_BLUE = (86, 99, 158)

    COPPER_DK = (122, 82, 56)
    COPPER_MID = (161, 105, 65)
    COPPER_HI = (196, 138, 86)
    AMBER_ACC = (218, 174, 86)

    PLASMA_BG = (34, 48, 78)
    PLASMA_MID = (44, 72, 122)
    PLASMA_BLUE = (24, 142, 248)
    PLASMA_CYAN = (104, 212, 248)
    PLASMA_WHT = (224, 244, 255)

    # 1. Harmonize far-left cabinet edge (nx=0..6, ny=13..65) -> industrial steel
    for ny in range(13, 66):
        for nx in range(0, 8):
            cur = spx[nx * 2, ny * 2][:3]
            if cur == (86, 99, 184):
                set2(px, nx, ny, STEEL_SH)
            elif cur == (106, 134, 219):
                set2(px, nx, ny, STEEL_MID)
            elif cur == (120, 152, 232):
                set2(px, nx, ny, STEEL_HI)
            elif cur in ((68, 79, 150), (56, 62, 114)):
                set2(px, nx, ny, STEEL_DK)

    # 2. Replace green cloning fluid inside cylinder (nx=116..145, ny=0..56) -> Electric Dynamo Chamber
    for ny in range(0, 56):
        for nx in range(116, 146):
            r0, g0, b0 = spx[nx * 2, ny * 2][:3]
            in_green_vat = (g0 > r0 + 18 and g0 > 120) or (117 <= nx <= 142 and 5 <= ny <= 54)
            if not in_green_vat:
                continue
            if nx <= 116 or nx >= 143:
                c = OUT if (nx == 143 and ny >= 5) else (STEEL_SH if nx == 144 else (184, 192, 200))
                set2(px, nx, ny, c)
                continue
            if ny < 5:
                continue
            if nx in (120, 121):
                c = (116, 178, 224)
            elif nx == 139:
                c = (64, 110, 168)
            else:
                c = PLASMA_MID if (122 <= nx <= 137) else PLASMA_BG

            if 127 <= nx <= 132:
                if nx in (127, 132):
                    c = OUT
                elif ny % 4 == 0:
                    c = COPPER_DK
                elif ny % 4 == 1:
                    c = COPPER_HI
                else:
                    c = COPPER_MID
                if ny in (13, 14, 29, 30, 45, 46):
                    c = STEEL_LT if nx in (128, 129) else STEEL_HI
            set2(px, nx, ny, c)

    for nx in range(118, 142):
        set2(px, nx, 5, STEEL_DK)
        set2(px, nx, 6, STEEL_HI if nx < 134 else STEEL_MID)
        set2(px, nx, 54, STEEL_DK)
        set2(px, nx, 53, STEEL_MID if nx < 134 else STEEL_SH)

    for ax, ay in [
        (123, 12), (124, 13), (125, 14), (124, 15), (123, 16), (125, 18), (126, 19),
        (134, 21), (136, 22), (137, 23), (135, 24), (134, 25), (136, 26), (134, 27),
        (125, 33), (123, 34), (122, 35), (124, 36), (126, 37),
        (134, 40), (136, 41), (137, 42), (135, 43), (133, 44),
    ]:
        set2(px, ax, ay, PLASMA_WHT if ay % 2 == 0 else PLASMA_CYAN)
        set2(px, ax - 1, ay, PLASMA_BLUE)

    # 3. Recolor ONLY the original blue cabinet pixels (nx=146..216, ny=18..59) IN-PLACE!
    # Preserves 100% of original sloped floor baseboard perspective AND NEVER overlaps the floor drum (nx=213..227)!
    cabinet_blue_set = {(86, 99, 184), (106, 134, 219), (120, 152, 232), (68, 79, 150), (56, 62, 114), (79, 102, 184), (92, 116, 200)}
    is_cab = [[False] * 256 for _ in range(70)]
    for ny in range(18, 62):
        for nx in range(146, 217):
            c = spx[nx * 2, ny * 2][:3]
            # Strictly identify blue cabinet pixels; stop before the grey floor drum at nx>=213, ny>=44!
            if ny >= 44 and nx >= 213:
                continue
            if c in cabinet_blue_set or (c[2] > c[0] + 40 and c[0] < 130):
                is_cab[ny][nx] = True
                # Map exact cabinet face tones cleanly into muted steel/slate while preserving original 3D side shading!
                if c == (120, 152, 232):
                    set2(px, nx, ny, STEEL_HI)
                elif c == (86, 99, 184) and nx >= 205:
                    set2(px, nx, ny, SLATE_BLUE_DK)
                elif c == (86, 99, 184):
                    set2(px, nx, ny, STEEL_SH)
                else:
                    set2(px, nx, ny, SLATE_BLUE)

    # Paint gears & transformer details strictly inside the upper front cabinet doors (respecting perspective bottom margin!)
    def cab_bot_y(nx: int) -> int:
        # Exact bottom edge of front cabinet slopes slightly down-right following wall baseboard perspective
        # Left nx=148 ends around ny=54; right nx=205 ends around ny=58!
        return 54 + int(round((nx - 148) * 4.0 / 57.0))

    # Left bay (nx=151..171, ny=23..cab_bot_y-3): Recessed Steel Gear Bay
    for ny in range(23, 55):
        for nx in range(151, 172):
            if not is_cab[ny][nx] or ny > cab_bot_y(nx) - 3:
                continue
            if ny == 23 or nx == 151:
                set2(px, nx, ny, STEEL_DK)
            elif ny == cab_bot_y(nx) - 3 or nx == 171:
                set2(px, nx, ny, STEEL_HI)
            else:
                set2(px, nx, ny, (46, 52, 64))

    def draw_cog(cx: int, cy: int, r_in: float, r_out: float, teeth: int, hi, mid, dk):
        for ny in range(max(24, cy - int(r_out) - 2), min(54, cy + int(r_out) + 2)):
            for nx in range(max(152, cx - int(r_out) - 2), min(171, cx + int(r_out) + 2)):
                if not is_cab[ny][nx] or ny > cab_bot_y(nx) - 4:
                    continue
                dx, dy = nx - cx, ny - cy
                dist = math.hypot(dx, dy)
                ang = math.atan2(dy, dx)
                rad = r_out if math.cos(ang * teeth) > 0.15 else r_in
                if dist <= rad:
                    if dist <= 1.5:
                        set2(px, nx, ny, STEEL_LT if dx <= 0 else STEEL_DK)
                    elif 2.3 <= dist <= r_in - 2.2 and abs(dx) > 1.1 and abs(dy) > 1.1:
                        continue
                    elif dist > rad - 1.0:
                        set2(px, nx, ny, OUT)
                    elif dx + dy < -1.4:
                        set2(px, nx, ny, hi)
                    elif dx + dy > 2.0:
                        set2(px, nx, ny, dk)
                    else:
                        set2(px, nx, ny, mid)

    draw_cog(cx=159, cy=40, r_in=6.0, r_out=7.6, teeth=8, hi=COPPER_HI, mid=COPPER_MID, dk=COPPER_DK)
    draw_cog(cx=166, cy=30, r_in=3.9, r_out=5.2, teeth=6, hi=STEEL_LT, mid=STEEL_HI, dk=STEEL_SH)

    # Right bay (nx=177..203, ny=23..cab_bot_y-3): Copper Transformer Coils + Digital Meter (zero touching nx>=206!)
    for ny in range(25, 55):
        for nx in range(179, 189):
            if not is_cab[ny][nx] or ny > cab_bot_y(nx) - 4:
                continue
            if nx in (179, 188) or ny == 25 or ny >= cab_bot_y(nx) - 4:
                set2(px, nx, ny, STEEL_DK)
            elif ny % 4 == 0:
                set2(px, nx, ny, COPPER_DK)
            elif nx <= 182:
                set2(px, nx, ny, COPPER_HI if ny % 4 == 1 else COPPER_MID)
            else:
                set2(px, nx, ny, COPPER_MID)

    for ny in range(26, 36):
        for nx in range(191, 200):
            if not is_cab[ny][nx]:
                continue
            if nx in (191, 199) or ny in (26, 35):
                set2(px, nx, ny, STEEL_DK)
            else:
                set2(px, nx, ny, (24, 62, 128))
    for wx, wy in [(193, 31), (194, 30), (195, 32), (196, 29), (197, 30), (198, 31)]:
        set2(px, wx, wy, PLASMA_CYAN)

    for ny in range(39, 53):
        for nx in range(191, 200):
            if not is_cab[ny][nx] or ny > cab_bot_y(nx) - 4:
                continue
            if ny in (40, 42, 44):
                set2(px, nx, ny, SLATE_BLUE_DK)
            elif ny == 48 and 194 <= nx <= 196:
                set2(px, nx, ny, AMBER_ACC)
            elif ny == 49 and nx == 195:
                set2(px, nx, ny, AMBER_ACC)

    # Subtle steel divider seam between left & right generator bay (nx=174)
    for ny in range(20, 56):
        if is_cab[ny][174]:
            set2(px, 174, ny, STEEL_DK)

    # Crisp exterior contour outline (53, 53, 53) strictly along outer perimeter & 3D right corner edge of cabinet
    for ny in range(18, 62):
        for nx in range(146, 217):
            if not is_cab[ny][nx]:
                continue
            is_outer = (
                not is_cab[ny - 1][nx]
                or not is_cab[ny + 1][nx]
                or not is_cab[ny][nx - 1]
                or (not is_cab[ny][nx + 1] and nx < 212)  # preserve clean drum boundary in front on right
                or (nx == 206 and ny >= 20)                # crisp 3D front-to-side corner edge
            )
            if is_outer:
                set2(px, nx, ny, OUT)

    # Keep right-side floor drum (nx=213..227, ny=44..61) 100% original silhouette!
    # Just add two crisp subtle blue indicator LEDs & copper top collar strictly INSIDE original drum lid (nx=216..223)
    for nx in range(216, 224):
        if spx[nx * 2, 46 * 2][:3] in ((165, 173, 181), (184, 192, 200), (208, 217, 224)):
            set2(px, nx, 46, COPPER_HI if nx < 220 else COPPER_MID)

    # 4. Replace desk books (nx=60..84, ny=30..44) with Flush Oscilloscope Box
    for ny in range(30, 44):
        for nx in range(60, 84):
            cur = spx[nx * 2, ny * 2][:3]
            if (cur[0] > cur[2] + 8) or cur in {(24, 206, 112), (24, 136, 127), (146, 104, 81), (131, 150, 161), (184, 122, 74)}:
                if ny <= 39:
                    set2(px, nx, ny, (184, 192, 200))
                elif ny <= 41:
                    set2(px, nx, ny, (176, 192, 224))
                else:
                    set2(px, nx, ny, STEEL_SH)

    for ny in range(33, 41):
        for nx in range(63, 79):
            if ny in (33, 40) or nx in (63, 78):
                set2(px, nx, ny, OUT)
            elif 65 <= nx <= 72 and 35 <= ny <= 38:
                set2(px, nx, ny, (24, 62, 128))
            elif nx >= 74:
                set2(px, nx, ny, COPPER_HI if ny in (35, 37) else STEEL_SH)
            else:
                set2(px, nx, ny, STEEL_HI if ny == 34 else STEEL_MID)
    for wx, wy in [(66, 37), (67, 36), (68, 37), (69, 36), (70, 38), (71, 36)]:
        set2(px, wx, wy, PLASMA_CYAN)

    return im


def main():
    bg = build_powerplant()
    bg.save(BB_DIR / "battlebgPowerPlant.png")

    sheet = Image.new("RGBA", (532, 424), (22, 25, 34, 255))
    draw = ImageDraw.Draw(sheet)
    draw.text((14, 6), "PowerPlant - Perspectiva pared & sin pisar (512x384)", fill=(237, 189, 98, 255))
    comp = bg.copy()
    for dx in range(0, 512, 8):
        ImageDraw.Draw(comp).line([(dx, 304), (dx + 4, 304)], fill=(255, 255, 255, 110))
    sheet.alpha_composite(comp, (10, 26))
    sheet.save(ROOT / "previews" / "powerplant_battleback_review.png")
    print("Installed perspective-locked battlebgPowerPlant.png cleanly.")


if __name__ == "__main__":
    main()
