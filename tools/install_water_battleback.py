"""Generate and install Water (Surf) battlebacks (512x384 Day, Eve, Night) and matching platforms.

Replaces the 9 Water files in Graphics/Battlebacks/:
  - battlebgWater{,Eve,Night}.png (512x384, strict 2x2 pixel grid, err2x2=0)
  - enemybaseWater{,Eve,Night}.png (256x128, Realidea Playa ellipse geometry, aqua ripple rings)
  - playerbaseWater{,Eve,Night}.png (512x64, Realidea Playa ellipse geometry, aqua ripple rings)
"""

import math
import random
from collections import deque
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
BB_DIR = ROOT / "Graphics" / "Battlebacks"
REALIDEA_DIR = Path(r"C:\Users\apera\Downloads\Battlebacks")

SKY_DAY_REF = BB_DIR / "battlebgDesert.png"
SKY_EVE_REF = BB_DIR / "battlebgDesertEve.png"
SKY_NIGHT_REF = BB_DIR / "battlebgDesertNight.png"

NW, NH = 256, 192
HORIZON_NY = 46  # y = 92

PALETTES = {
    "day": {
        "water_deep": (54, 58, 126),
        "water_navy": (63, 68, 148),
        "water_cobalt": (73, 88, 192),
        "water_royal": (80, 120, 240),
        "water_azure": (96, 158, 252),
        "water_cyan": (85, 206, 240),
        "water_aqua": (146, 242, 224),
        "foam_light": (213, 245, 250),
        "foam_white": (255, 255, 255),
        "dash_dark": (44, 48, 108),
        # Distant coastal island (matching Beach)
        "isl_out": (34, 62, 66),
        "isl_dk": (38, 114, 62),
        "isl_mid": (54, 152, 74),
        "isl_hi": (96, 194, 72),
        "isl_sand": (235, 195, 130),
        "isl_rock": (144, 120, 88),
        "isl_rock_dk": (104, 84, 64),
        # Craggy coastal reef rocks & flat coastal limestone/slate islet surfaces
        "rock_out": (38, 42, 58),
        "rock_wet": (60, 66, 88),
        "rock_dk": (84, 92, 114),
        "rock_mid": (116, 124, 146),
        "rock_hi": (154, 162, 182),
        "shelf_top": (176, 180, 192),
        "shelf_mid": (150, 156, 172),
        "shelf_sh": (124, 132, 150),
        "moss_dk": (36, 102, 78),
        "moss_hi": (66, 156, 98),
    },
    "eve": {
        "water_deep": (78, 52, 98),
        "water_navy": (96, 62, 116),
        "water_cobalt": (118, 78, 134),
        "water_royal": (148, 98, 146),
        "water_azure": (186, 124, 148),
        "water_cyan": (216, 158, 154),
        "water_aqua": (240, 198, 164),
        "foam_light": (250, 224, 192),
        "foam_white": (255, 244, 226),
        "dash_dark": (62, 40, 82),
        "isl_out": (54, 42, 64),
        "isl_dk": (64, 90, 68),
        "isl_mid": (94, 118, 74),
        "isl_hi": (142, 152, 76),
        "isl_sand": (212, 162, 116),
        "isl_rock": (144, 106, 94),
        "isl_rock_dk": (108, 76, 70),
        "rock_out": (48, 38, 54),
        "rock_wet": (74, 58, 78),
        "rock_dk": (102, 82, 98),
        "rock_mid": (136, 110, 118),
        "rock_hi": (176, 144, 138),
        "shelf_top": (196, 162, 146),
        "shelf_mid": (168, 134, 128),
        "shelf_sh": (138, 108, 112),
        "moss_dk": (58, 82, 66),
        "moss_hi": (96, 132, 78),
    },
    "night": {
        "water_deep": (22, 30, 68),
        "water_navy": (28, 38, 86),
        "water_cobalt": (36, 50, 106),
        "water_royal": (46, 68, 132),
        "water_azure": (62, 94, 156),
        "water_cyan": (82, 130, 172),
        "water_aqua": (122, 166, 192),
        "foam_light": (168, 198, 220),
        "foam_white": (214, 228, 244),
        "dash_dark": (16, 22, 54),
        "isl_out": (16, 24, 46),
        "isl_dk": (20, 48, 48),
        "isl_mid": (28, 66, 56),
        "isl_hi": (38, 84, 64),
        "isl_sand": (96, 98, 102),
        "isl_rock": (72, 70, 84),
        "isl_rock_dk": (50, 48, 64),
        "rock_out": (20, 24, 42),
        "rock_wet": (34, 40, 64),
        "rock_dk": (50, 58, 86),
        "rock_mid": (70, 80, 112),
        "rock_hi": (96, 108, 142),
        "shelf_top": (114, 126, 158),
        "shelf_mid": (92, 104, 136),
        "shelf_sh": (70, 80, 112),
        "moss_dk": (22, 64, 60),
        "moss_hi": (38, 100, 76),
    },
}

DESERT_DAY_SKY_RGB = {
    (30, 153, 244), (48, 127, 229), (74, 145, 234), (71, 162, 251),
    (102, 178, 251), (154, 202, 255), (183, 215, 255), (188, 212, 255),
    (202, 220, 255), (234, 240, 255), (255, 255, 255), (191, 224, 255),
}


def value_noise_2d(x: float, y: float, seed: int = 17) -> float:
    ix = math.floor(x)
    iy = math.floor(y)
    fx = x - ix
    fy = y - iy
    ux = fx * fx * (3 - 2 * fx)
    uy = fy * fy * (3 - 2 * fy)

    def h(a: int, b: int) -> float:
        n = (a * 374761393 + b * 668265263 + seed * 1442695041) & 0xFFFFFFFF
        n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
        return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0

    v00 = h(ix, iy)
    v10 = h(ix + 1, iy)
    v01 = h(ix, iy + 1)
    v11 = h(ix + 1, iy + 1)
    return (v00 * (1 - ux) + v10 * ux) * (1 - uy) + (v01 * (1 - ux) + v11 * ux) * uy


def fbm(x: float, y: float, octaves: int = 3, seed: int = 17) -> float:
    val = 0.0
    amp = 0.5
    freq = 1.0
    for o in range(octaves):
        val += amp * value_noise_2d(x * freq, y * freq, seed + o * 31)
        freq *= 2.05
        amp *= 0.5
    return val


def build_desert_sky_mask() -> list[list[bool]]:
    """Flood-fill exact pure sky region of battlebgDesert.png from y=0 down to horizon."""
    im = Image.open(SKY_DAY_REF).convert("RGB")
    px = im.load()
    mask = [[False] * NW for _ in range(HORIZON_NY)]

    def is_sky(nx: int, ny: int) -> bool:
        return px[nx * 2, ny * 2] in DESERT_DAY_SKY_RGB

    q = deque()
    for nx in range(NW):
        if is_sky(nx, 0):
            mask[0][nx] = True
            q.append((nx, 0))
    while q:
        cx, cy = q.popleft()
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = cx + ox, cy + oy
            if 0 <= nx < NW and 0 <= ny < HORIZON_NY and not mask[ny][nx] and is_sky(nx, ny):
                mask[ny][nx] = True
                q.append((nx, ny))
    return mask


def build_sky_grid(mode: str, sky_mask: list[list[bool]]) -> tuple[list[list[tuple[int, int, int]]], int]:
    """Return (NW x HORIZON_NY sky RGBs, reflection_nx_center) cleanly free of sand/rocks."""
    path = {"day": SKY_DAY_REF, "eve": SKY_EVE_REF, "night": SKY_NIGHT_REF}[mode]
    px = Image.open(path).convert("RGB").load()

    grid = [[(0, 0, 0)] * NW for _ in range(HORIZON_NY)]
    for ny in range(HORIZON_NY):
        for nx in range(NW):
            if sky_mask[ny][nx]:
                grid[ny][nx] = px[nx * 2, ny * 2]
            else:
                # Reflect cleanly into unobstructed clean-sky zone without touching far-right dunes
                mx = max(0, min(168, 336 - nx))
                while not sky_mask[ny][mx] and mx > 0:
                    mx -= 1
                grid[ny][nx] = px[mx * 2, ny * 2]

    if mode == "night":
        # Smooth mirror extension on left (no wrap seam!) so crescent moon shifts away from left island
        shifted = [[(0, 0, 0)] * NW for _ in range(HORIZON_NY)]
        shift_n = 24
        for ny in range(HORIZON_NY):
            for nx in range(NW):
                sx = abs(nx - shift_n)
                if sx >= NW:
                    sx = 2 * NW - 2 - sx
                shifted[ny][nx] = grid[ny][sx]
        grid = shifted
        return grid, 102

    if mode == "eve":
        return grid, 130
    return grid, 128


def paint_distant_islands(grid: list[list[str]]):
    """Paint Beach-style distant dual-peak coastal island ridge on left & tiny sea stack on right."""
    # Back-left tropical island hills (nx = 2..94, horizon base ny = 46)
    for nx in range(2, 95):
        t = (nx - 2) / 93.0
        h_back = 7.5 * math.exp(-((t - 0.30) ** 2) / 0.045)
        h_main = 11.0 * math.exp(-((t - 0.62) ** 2) / 0.048)
        h_tail = 4.2 * math.exp(-((t - 0.88) ** 2) / 0.014)
        n = (fbm(nx * 0.32, 2.3, 2, seed=41) - 0.5) * 1.4
        top_y = HORIZON_NY - int(round(max(0.0, max(h_back, h_main) + h_tail * 0.4 + n)))
        if top_y >= HORIZON_NY:
            continue
        for ny in range(top_y, HORIZON_NY):
            dy = ny - top_y
            if ny == HORIZON_NY - 1 and (28 <= nx <= 84):
                grid[ny][nx] = "isl_sand"
            elif dy <= 2:
                grid[ny][nx] = "isl_hi" if (nx + dy) % 3 != 0 else "isl_mid"
            elif dy <= 6:
                grid[ny][nx] = "isl_mid"
            else:
                grid[ny][nx] = "isl_dk"

    # Outline slopes of left island cleanly
    for nx in range(2, 95):
        for ny in range(30, HORIZON_NY):
            if grid[ny][nx].startswith("isl_") and grid[ny][nx] != "isl_sand":
                if nx in (2, 94) or not grid[ny - 1][nx].startswith("isl_") or not grid[ny][nx - 1].startswith("isl_") or not grid[ny][nx + 1].startswith("isl_"):
                    grid[ny][nx] = "isl_out"

    # Far-right rocky sea stack (nx = 216..240)
    for nx in range(216, 241):
        t = (nx - 216) / 24.0
        peak = 8.5 * math.exp(-((t - 0.44) ** 2) / 0.065) + 4.8 * math.exp(-((t - 0.78) ** 2) / 0.026)
        n = (fbm(nx * 0.38, 6.7, 2, seed=91) - 0.5) * 1.2
        top_y = HORIZON_NY - int(round(max(0.0, peak + n)))
        for ny in range(top_y, HORIZON_NY):
            dy = ny - top_y
            grid[ny][nx] = "isl_rock" if dy <= 2 else "isl_rock_dk"
    for nx in range(216, 241):
        for ny in range(32, HORIZON_NY - 1):
            if grid[ny][nx].startswith("isl_") and grid[ny][nx] != "isl_out":
                if nx in (216, 240) or not grid[ny - 1][nx].startswith("isl_") or not grid[ny][nx - 1].startswith("isl_") or not grid[ny][nx + 1].startswith("isl_"):
                    grid[ny][nx] = "isl_out"


def build_water_tokens(mode: str, reflect_nx: int) -> list[list[str]]:
    """Create semantic token grid (NW x NH) for perspective pixel ocean, caustics & reef rocks."""
    grid = [["sky"] * NW for _ in range(NH)]

    # 1. Ocean perspective gradient + stretched cellular caustic wave ribbons
    for ny in range(HORIZON_NY, NH):
        p = (ny - HORIZON_NY) / (NH - HORIZON_NY)  # 0 at horizon, 1 at foreground bottom
        wz = 18.0 / (0.14 + p * 1.38)
        for nx in range(NW):
            u = nx / NW
            # Depth progresses predominantly horizon->foreground with subtle turquoise shallow bay sweep on bottom-right
            bay_curve = 0.045 * math.sin(u * 3.8 - 0.6) + 0.065 * (u ** 1.6) * p
            noise_edge = (fbm(u * 5.0, p * 5.5, 2, seed=12) - 0.5) * 0.06
            shoal = p * 0.94 + bay_curve + noise_edge

            wx = (u - 0.48) * wz * 1.45
            n1 = value_noise_2d(wx * 0.28 + 0.25 * math.sin(wz * 0.55), wz * 0.62, seed=5)
            n2 = value_noise_2d(wx * 0.21 - 2.1, wz * 0.72 + 1.9, seed=29)
            ridge = 1.0 - abs(n1 - 0.5) * 2.0
            ridge2 = 1.0 - abs(n2 - 0.5) * 2.0
            swell = math.sin(wz * 1.15 + n2 * 2.6) * 0.5 + 0.5

            if shoal < 0.16:
                tok = "water_deep"
            elif shoal < 0.30:
                tok = "water_navy"
            elif shoal < 0.46:
                tok = "water_cobalt"
            elif shoal < 0.64:
                tok = "water_royal"
            elif shoal < 0.80:
                tok = "water_azure"
            elif shoal < 0.93:
                tok = "water_cyan"
            else:
                tok = "water_aqua"

            # Thin crisp cellular water ribbons & wave crests
            if shoal >= 0.32 and ridge > 0.87:
                if shoal < 0.48:
                    tok = "water_royal"
                elif shoal < 0.68:
                    tok = "water_azure"
                elif shoal < 0.86:
                    tok = "water_cyan"
                else:
                    tok = "water_aqua"
            elif shoal >= 0.42 and ridge2 > 0.92 and swell > 0.52:
                tok = "water_aqua" if shoal > 0.68 else "water_cyan"

            grid[ny][nx] = tok

    # 2. Broken horizontal pixel wave dashes across open water
    rng = random.Random(2026)
    for _ in range(180):
        wy = rng.randint(HORIZON_NY + 1, NH - 10)
        p = (wy - HORIZON_NY) / (NH - HORIZON_NY)
        wx = rng.randint(2, NW - 12)
        wlen = rng.randint(2, 4) if p < 0.35 else rng.randint(3, 7)
        if p < 0.22:
            tok = "dash_dark" if rng.random() < 0.45 else "water_cobalt"
        elif p < 0.55:
            tok = "water_azure" if rng.random() < 0.65 else "water_cobalt"
        else:
            tok = "foam_light" if rng.random() < 0.35 else "water_aqua"
        for dx in range(wlen):
            if 0 <= wx + dx < NW:
                grid[wy][wx + dx] = tok

    # 3. Shimmering broken horizontal wave-glint dashes for Sunset (Eve) & Moonlight (Night) — NO solid blocks!
    if mode in ("eve", "night"):
        r2 = random.Random(777 if mode == "eve" else 888)
        for wy in range(HORIZON_NY + 2, NH - 4):
            p = (wy - HORIZON_NY) / (NH - HORIZON_NY)
            if wy % 2 == 1 and p < 0.65:
                continue
            half_spread = int(4 + p * (20 if mode == "eve" else 14))
            num_glints = 2 if p < 0.45 else 3
            for _ in range(num_glints):
                if r2.random() > (0.60 if p < 0.55 else 0.52):
                    continue
                gx = reflect_nx + int(r2.gauss(0, half_spread * 0.48))
                glen = r2.randint(2, 4 if p < 0.4 else 6)
                tok = "foam_white" if (abs(gx - reflect_nx) < half_spread * 0.30 and r2.random() < 0.38) else "foam_light"
                for dx in range(glen):
                    if 0 <= gx + dx < NW:
                        grid[wy][gx + dx] = tok

    # 4. Distant horizon islands + crisp waterline surf foam
    paint_distant_islands(grid)
    for nx in range(2, 95):
        if grid[HORIZON_NY - 1][nx].startswith("isl_"):
            grid[HORIZON_NY][nx] = "foam_white" if nx % 4 == 0 else "foam_light"
    for nx in range(216, 241):
        if grid[HORIZON_NY - 1][nx].startswith("isl_"):
            grid[HORIZON_NY][nx] = "foam_white" if nx % 3 == 0 else "foam_light"

    # 5. Foreground craggy coastal reef rocks in bottom-right corner + frothy circular surf lace
    def draw_reef_rock(cx: float, cy: float, rx: float, ry: float, seed: int):
        mask = [[False] * NW for _ in range(NH)]
        for ny in range(max(0, int(cy - ry - 6)), NH):
            for nx in range(max(0, int(cx - rx - 6)), NW):
                dx = (nx - cx) / rx
                dy = (ny - cy) / ry
                ang = math.atan2(dy, dx)
                facet = 0.14 * math.cos(ang * 5.0 + seed) + 0.22 * (fbm(nx * 0.18, ny * 0.20, 2, seed=seed) - 0.5)
                if dx * dx + dy * dy + facet < 1.0:
                    mask[ny][nx] = True

        # Frothy lacy surf collar in shallow water around rock base
        for ny in range(max(0, int(cy - ry - 6)), NH):
            for nx in range(max(0, int(cx - rx - 12)), NW):
                if mask[ny][nx]:
                    continue
                dmin = 99.0
                for oy in range(-3, 4):
                    for ox in range(-6, 7):
                        tx, ty = nx + ox, ny + oy
                        if 0 <= tx < NW and 0 <= ty < NH and mask[ty][tx]:
                            d = math.hypot(ox * 0.55, oy)
                            if d < dmin:
                                dmin = d
                if ny >= cy - 4 and dmin <= 1.2:
                    grid[ny][nx] = "foam_white"
                elif ny >= cy - 3 and dmin <= 3.6:
                    foam_n = fbm(nx * 0.36, ny * 0.42, 2, seed=seed + 19)
                    if dmin <= 2.2 and foam_n > 0.38:
                        grid[ny][nx] = "foam_white" if foam_n > 0.56 else "foam_light"
                    elif foam_n > 0.52:
                        grid[ny][nx] = "foam_light"
                    elif grid[ny][nx] not in ("rock_out", "rock_dk", "rock_mid", "rock_hi", "rock_wet"):
                        grid[ny][nx] = "water_aqua"

        # Shade faceted rock body with organic strata & wet glossy tidal base
        for ny in range(max(0, int(cy - ry - 6)), NH):
            for nx in range(max(0, int(cx - rx - 6)), NW):
                if not mask[ny][nx]:
                    continue
                edge = any(
                    0 <= nx + ox < NW and 0 <= ny + oy < NH and not mask[ny + oy][nx + ox]
                    for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1))
                )
                if edge:
                    grid[ny][nx] = "rock_out"
                    continue
                dy = (ny - cy) / ry
                dx = (nx - cx) / rx
                n = fbm(nx * 0.26, ny * 0.26, 2, seed=seed + 3)
                lit = -dy * 0.65 - dx * 0.42 + (n - 0.5) * 0.72
                # Organic craggy fracture crevices
                crevice = fbm(nx * 0.32 + dy * 2.0, ny * 0.20, 2, seed=seed + 51)
                if dy > 0.36:
                    grid[ny][nx] = "rock_wet" if n > 0.32 else "rock_out"
                elif crevice > 0.74:
                    grid[ny][nx] = "rock_out" if dy > 0.05 else "rock_dk"
                elif lit > 0.40:
                    grid[ny][nx] = "rock_hi"
                elif lit > 0.06:
                    grid[ny][nx] = "rock_mid"
                else:
                    grid[ny][nx] = "rock_dk"

                if -0.10 < dy < 0.32 and fbm(nx * 0.42, ny * 0.42, 2, seed=seed + 77) > 0.66:
                    grid[ny][nx] = "moss_hi" if lit > 0.10 else "moss_dk"

    def draw_flat_reef_islet(
        lobes: list[tuple[float, float, float, float]],
        rim_thickness: int,
        seed: int,
        moss_side: str = "left",
        add_pebbles: bool = True,
    ):
        """Draw an organic multi-lobe flat-topped rocky reef shelf integrated cleanly into ocean water."""
        min_x = max(0, int(min(cx - rx for cx, cy, rx, ry in lobes) - 10))
        max_x = min(NW, int(max(cx + rx for cx, cy, rx, ry in lobes) + 10))
        min_y = max(HORIZON_NY + 2, int(min(cy - ry for cx, cy, rx, ry in lobes) - 6))
        max_y = min(NH, int(max(cy + ry for cx, cy, rx, ry in lobes) + 8))

        mask = [[False] * NW for _ in range(NH)]
        for ny in range(min_y, max_y):
            for nx in range(min_x, max_x):
                n = (fbm(nx * 0.22, ny * 0.28, 2, seed=seed) - 0.5) * 0.34
                inside = False
                for cx, cy, rx, ry in lobes:
                    dx = (nx - cx) / rx
                    dy = (ny - cy) / ry
                    ang = math.atan2(dy, dx)
                    facet = 0.09 * math.cos(ang * 5.0 + seed) + 0.06 * math.sin(ang * 3.0 - seed)
                    if dx * dx + dy * dy + facet + n < 1.0:
                        inside = True
                        break
                mask[ny][nx] = inside

        # 1. Frothy seafoam & shallow turquoise water collar hugging the coastline
        for ny in range(min_y, min(NH, max_y + 2)):
            for nx in range(max(0, min_x - 4), min(NW, max_x + 4)):
                if mask[ny][nx]:
                    continue
                dmin = 99.0
                above_rock = False
                for oy in range(-3, 2):
                    for ox in range(-4, 5):
                        tx, ty = nx + ox, ny + oy
                        if 0 <= tx < NW and 0 <= ty < NH and mask[ty][tx]:
                            d = math.hypot(ox * 0.52, oy)
                            if d < dmin:
                                dmin = d
                            if oy < 0:
                                above_rock = True
                if dmin <= 1.15 and above_rock:
                    grid[ny][nx] = "foam_white"
                elif dmin <= 1.25:
                    grid[ny][nx] = "foam_light" if (nx + ny) % 3 != 0 else "foam_white"
                elif dmin <= 2.6 and above_rock:
                    fn = fbm(nx * 0.38, ny * 0.44, 2, seed=seed + 19)
                    if fn > 0.46:
                        grid[ny][nx] = "foam_white" if fn > 0.62 else "foam_light"
                    elif grid[ny][nx] not in ("rock_out", "rock_dk", "rock_wet"):
                        grid[ny][nx] = "water_aqua"

        # 2. Vertical rocky cliff rim (bottom face height = rim_thickness) vs flat top shelf
        # Compute per-column bottom-most rock ny so the stepped cliff ledge wraps the front contour cleanly
        bot_ny = {}
        top_ny = {}
        for nx in range(min_x, max_x):
            ys = [ny for ny in range(min_y, max_y) if mask[ny][nx]]
            if ys:
                top_ny[nx] = min(ys)
                bot_ny[nx] = max(ys)

        for ny in range(min_y, max_y):
            for nx in range(min_x, max_x):
                if not mask[ny][nx]:
                    continue
                edge = any(
                    0 <= nx + ox < NW and 0 <= ny + oy < NH and not mask[ny + oy][nx + ox]
                    for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1))
                )
                if edge:
                    grid[ny][nx] = "rock_out"
                    continue
                dbot = bot_ny[nx] - ny
                dtop = ny - top_ny[nx]
                n = fbm(nx * 0.25, ny * 0.32, 2, seed=seed + 7)
                if dbot <= rim_thickness:
                    # Wet rocky tidal face & bevel edge
                    if dbot <= 1:
                        grid[ny][nx] = "rock_wet"
                    elif dbot == rim_thickness and n > 0.35:
                        grid[ny][nx] = "rock_mid"
                    else:
                        grid[ny][nx] = "rock_dk"
                elif ddb := (dbot == rim_thickness + 1):
                    # Crisp upper shelf bevel highlight edge
                    grid[ny][nx] = "rock_hi" if n > 0.28 else "shelf_mid"
                else:
                    # Smooth calm coastal stone terrace planes (matching Bridge/Mountain rock shading, low noise)
                    zone = fbm(nx * 0.08, ny * 0.11, 2, seed=seed + 7)
                    crack = fbm(nx * 0.24 + ny * 0.12, ny * 0.22, 2, seed=seed + 53)
                    tx_norm = (nx - min_x) / max(1, (max_x - min_x))
                    in_moss = (
                        ((moss_side == "left" and tx_norm < 0.24) or (moss_side == "right" and tx_norm > 0.74))
                        and dtop <= 5
                        and zone > 0.50
                    )
                    if in_moss:
                        grid[ny][nx] = "moss_hi" if dtop <= 2 else "moss_dk"
                    elif crack > 0.80 and dbot > rim_thickness + 2:
                        grid[ny][nx] = "rock_dk"
                    elif zone > 0.56 or dtop <= 2:
                        grid[ny][nx] = "shelf_top"
                    elif zone > 0.36:
                        grid[ny][nx] = "shelf_mid"
                    else:
                        grid[ny][nx] = "shelf_sh"

        # 3. Optional small eroded pebble cluster inside the top terrace
        if add_pebbles:
            prng = random.Random(seed + 99)
            cx0 = sum(cx for cx, _, _, _ in lobes) / len(lobes)
            cy0 = sum(cy for _, cy, _, _ in lobes) / len(lobes)
            for _ in range(3):
                px = int(cx0 + prng.randint(-18, 18))
                py = int(cy0 + prng.randint(-4, 3))
                if 2 <= px < NW - 3 and 2 <= py < NH - 3 and all(mask[py + dy][px + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                    grid[py][px] = "rock_hi"
                    grid[py][px + 1] = "rock_mid"
                    grid[py + 1][px] = "rock_dk"

    # Enemy reef islet (centered at FOEBATTLER nx=192, ny=88 with natural multi-lobe spur + small stepping rock)
    draw_flat_reef_islet(
        lobes=[(186, 86, 36, 12), (208, 89, 24, 9), (166, 90, 16, 7)],
        rim_thickness=3,
        seed=501,
        moss_side="left",
        add_pebbles=True,
    )
    draw_reef_rock(cx=142, cy=93, rx=8, ry=4, seed=509)

    # Player coastal rock shelf (supporting PLAYERBATTLER nx=64, ny=124..152, integrated cleanly into lower-left foreground)
    draw_flat_reef_islet(
        lobes=[(54, 141, 46, 16), (86, 144, 34, 12), (24, 146, 28, 14)],
        rim_thickness=4,
        seed=601,
        moss_side="left",
        add_pebbles=True,
    )

    # Bottom-right craggy reef rock rising clearly above the y=304 (ny=152) battle menu line!
    draw_reef_rock(cx=234, cy=150, rx=28, ry=26, seed=101)
    draw_reef_rock(cx=204, cy=156, rx=14, ry=10, seed=205)
    # Subtle small sea rock in mid-left open water above player islet
    draw_reef_rock(cx=16, cy=88, rx=11, ry=6, seed=309)

    return grid


def build_battlebg(mode: str, sky_mask: list[list[bool]]) -> Image.Image:
    sky, reflect_nx = build_sky_grid(mode, sky_mask)
    if mode == "night":
        # Measure exact horizontal moon center in shifted sky grid
        mxs = [nx for ny in range(HORIZON_NY) for nx in range(NW) if sky[ny][nx][0] > 210 and sky[ny][nx][1] > 210]
        if mxs:
            reflect_nx = sum(mxs) // len(mxs)
    tokens = build_water_tokens(mode, reflect_nx)
    pal = PALETTES[mode]

    im = Image.new("RGBA", (NW * 2, NH * 2))
    px = im.load()
    for ny in range(NH):
        for nx in range(NW):
            tok = tokens[ny][nx]
            if tok == "sky" and ny < HORIZON_NY:
                r, g, b = sky[ny][nx]
            else:
                r, g, b = pal[tok]
            col = (r, g, b, 255)
            x, y = nx * 2, ny * 2
            px[x, y] = col
            px[x + 1, y] = col
            px[x, y + 1] = col
            px[x + 1, y + 1] = col
    return im


def build_water_platforms(mode: str, eb_tpl: Image.Image, pb_tpl: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Use Realidea Playa oval geometry with calm aqua surface & horizontal wave shimmer (no whirlpools)."""
    pal = PALETTES[mode]

    def transform_base(tpl: Image.Image, cx: float, cy: float, rx: float, ry: float) -> Image.Image:
        out = tpl.copy()
        px = out.load()
        w, h = out.size
        outline_orig = (88, 64, 32)
        rim_light_orig = (240, 224, 168)
        # Playa wavy interior colors -> calm horizontal-shimmer aqua palette
        wave_dark_orig = {(192, 176, 120), (208, 184, 120), (136, 120, 80)}
        for y in range(0, h, 2):
            for x in range(0, w, 2):
                r, g, b, a = px[x, y]
                if a != 255:
                    continue
                dx = (x + 1 - cx) / rx
                dy = (y + 1 - cy) / ry
                d = math.sqrt(dx * dx + dy * dy)
                if (r, g, b) == outline_orig:
                    col = pal["water_cobalt"] if y + 1 < cy else pal["water_navy"]
                elif (r, g, b) == rim_light_orig or d > 0.90:
                    col = pal["foam_white"] if (y + 1 < cy and d > 0.92) else pal["foam_light"]
                elif d > 0.80:
                    col = pal["water_aqua"]
                else:
                    # Subtle horizontal wave-shimmer dashes across a calm cyan-azure water surface
                    shimmer = math.sin((y * 0.42) + math.sin(x * 0.045) * 1.4)
                    if (r, g, b) in wave_dark_orig:
                        col = pal["water_azure"] if shimmer > -0.2 else pal["water_royal"]
                    elif shimmer > 0.72 and ((x // 2) % 9 < 5):
                        col = pal["water_aqua"]
                    else:
                        col = pal["water_cyan"]
                c4 = (col[0], col[1], col[2], 255)
                for oy in (0, 1):
                    for ox in (0, 1):
                        if px[x + ox, y + oy][3] == 255:
                            px[x + ox, y + oy] = c4
        return out

    eb = transform_base(eb_tpl, 128.0, 66.0, 124.0, 30.0)
    pb = transform_base(pb_tpl, 256.0, 44.0, 220.0, 30.0)
    return eb, pb


def main():
    sky_mask = build_desert_sky_mask()

    results = {}
    for mode, suffix in [("day", ""), ("eve", "Eve"), ("night", "Night")]:
        bg = build_battlebg(mode, sky_mask)
        bg.save(BB_DIR / f"battlebgWater{suffix}.png")
        results[mode] = bg

    sheet = Image.new("RGBA", (1560, 424), (22, 25, 34, 255))
    draw = ImageDraw.Draw(sheet)
    for i, (label, key) in enumerate([
        ("DIA", "day"),
        ("ATARDECER Eve", "eve"),
        ("NOCHE Night", "night"),
    ]):
        bg = results[key]
        x0 = 10 + i * 518
        draw.text((x0 + 4, 6), f"Water - {label} (512x384, sin plataformas)", fill=(237, 189, 98, 255))
        comp = bg.copy()
        for dx in range(0, 512, 8):
            ImageDraw.Draw(comp).line([(dx, 304), (dx + 4, 304)], fill=(255, 255, 255, 110))
        sheet.alpha_composite(comp, (x0, 26))

    sheet.save(ROOT / "previews" / "water_battleback_review.png")
    print("Installed all 9 Water files cleanly (with integrated reef islets and transparent bases).")


if __name__ == "__main__":
    main()
