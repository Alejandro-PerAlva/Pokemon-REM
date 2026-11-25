"""Generate and install battlebgSewers.png (512x384, strict 2x2 pixel grid, err2x2=0).

Diagonal 3/4 Perspective Sewers with Upper-Right Focal Light & Side-to-Side Grate:
  - Vanishing point & main light focus set in the upper-right (VX=252, HORIZ_Y=34)
  - Left angled masonry wall with 3D arched outfall culvert & parabolic slime waterfall into sunken canal
  - Diagonal cement walkway sweeping SW->NE directly along battle line (Player bottom-left <-> Opponent top-right),
    surrounded by murky green sewer water on BOTH left and bottom-right sides
  - Heavy flush steel drainage grate crossing the diagonal cement walkway completely from side to side
    ("atravesando de lado a lado") with crisp safety railings along the water edge
  - Sweeping Temple-style focal light shaft pouring from the upper-right arched grate down the diagonal bridge
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
BB_DIR = ROOT / "Graphics" / "Battlebacks"

NW, NH = 256, 192
CORNER_X = 64
WY_BACK = 64
CY_BACK = 10
# Single True 1-Point Vanishing Point shifted slightly right so Foe 1v1 (384,176) & Doubles (352..432) sit cleanly centered!
VX, HORIZ_Y = 255.0, 20.0
FLOOR_SLOPE_L = (WY_BACK - HORIZ_Y) / (CORNER_X - VX)
CEIL_SLOPE_L = (CY_BACK - HORIZ_Y) / (CORNER_X - VX)
PIER_H = 12  # 24px tall vertical masonry wall above water -> unmistakable bridge elevation!
BACK_PATH_Y = 72
WATER_SLOPE_L = ((BACK_PATH_Y + PIER_H) - HORIZ_Y) / ((CORNER_X + (BACK_PATH_Y - WY_BACK) / FLOOR_SLOPE_L) - VX)
NX_LEFT_JOIN = CORNER_X + (BACK_PATH_Y - WY_BACK) / FLOOR_SLOPE_L  # Exact pixel (~29) where back path hits left wall!


def value_noise_2d(x: float, y: float, seed: int = 13) -> float:
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

    return (h(ix, iy) * (1 - ux) + h(ix + 1, iy) * ux) * (1 - uy) + (
        h(ix, iy + 1) * (1 - ux) + h(ix + 1, iy + 1) * ux
    ) * uy


def fbm(x: float, y: float, octaves: int = 2, seed: int = 13) -> float:
    val = 0.0
    amp = 0.5
    freq = 1.0
    for o in range(octaves):
        val += amp * value_noise_2d(x * freq, y * freq, seed + o * 29)
        freq *= 2.05
        amp *= 0.5
    return val


def clamp(v: float) -> int:
    return max(0, min(255, int(round(v))))


def wall_floor_y(nx: int) -> int:
    if nx < CORNER_X:
        return int(round(WY_BACK + FLOOR_SLOPE_L * (nx - CORNER_X)))
    return WY_BACK


def wall_water_y(nx: int) -> int:
    """Waterline along receding left brick wall where open canal meets left wall (nx < NX_LEFT_JOIN)."""
    if nx < CORNER_X:
        return int(round(HORIZ_Y + WATER_SLOPE_L * (nx - VX)))
    return BACK_PATH_Y + PIER_H


def ceiling_arch_y(nx: int) -> int:
    if nx < CORNER_X:
        return int(round(CY_BACK + CEIL_SLOPE_L * (nx - CORNER_X)))
    return CY_BACK + int(round(2.0 * math.sin((nx - CORNER_X) / 192.0 * math.pi)))


def build_sewers() -> Image.Image:
    rgb = [[(0, 0, 0)] * NW for _ in range(NH)]
    emit = [[0.0] * NW for _ in range(NH)]
    shad = [[1.0] * NW for _ in range(NH)]

    DARK_OUT = (22, 24, 28)
    MORTAR = (44, 48, 54)
    ARCH_VOID = (14, 16, 20)
    BRICK_TONES = [(78, 86, 90), (88, 96, 98), (70, 76, 82), (96, 102, 104)]
    BRICK_SIDE = [(60, 68, 74), (68, 76, 82), (54, 60, 66)]
    MOSS_DK = (36, 80, 62)
    MOSS_MID = (56, 114, 84)
    MOSS_HI = (78, 142, 102)

    STONE_A = (134, 140, 134)
    STONE_B = (122, 128, 124)
    STONE_GROUT = (98, 104, 102)
    CURB_TOP = (150, 156, 148)
    RET_HI = (86, 94, 96)
    RET_DK = (48, 54, 58)
    RET_MID = (68, 76, 80)
    RET_WET = (28, 44, 42)

    PIPE_DK = (76, 52, 46)
    PIPE_MID = (114, 76, 60)
    PIPE_HI = (154, 108, 82)
    VERDIGRIS = (74, 154, 126)

    GRATE_DK = (40, 44, 52)
    GRATE_MID = (76, 84, 94)
    GRATE_HI = (112, 122, 132)

    WATER_DEEP = (16, 46, 42)
    WATER_MID = (28, 76, 64)
    WATER_SCUM = (48, 112, 80)
    WATER_FOAM = (136, 198, 148)

    # 1. Vaulted Ceiling + Receding Left Wall (0..CORNER_X) + Back Wall (CORNER_X..NW)
    for nx in range(NW):
        wy_deck = wall_floor_y(nx)
        wy_draw = wy_deck if nx >= int(round(NX_LEFT_JOIN)) else wall_water_y(nx)
        cy_top = ceiling_arch_y(nx)
        is_left = nx < CORNER_X

        for ny in range(wy_draw):
            if ny <= cy_top:
                if ny in (cy_top, cy_top - 1):
                    rgb[ny][nx] = DARK_OUT if ny == cy_top else (52, 58, 62)
                else:
                    rib = (nx % 38 in (0, 1, 2))
                    rgb[ny][nx] = (46, 50, 56) if not rib else (34, 38, 44)
                shad[ny][nx] = 0.75
                continue

            if nx >= int(round(NX_LEFT_JOIN)) and ny >= wy_deck - 4:
                # Stone baseboard sitting cleanly atop the elevated concrete T-path
                if ny in (wy_deck - 4, wy_deck - 1):
                    rgb[ny][nx] = DARK_OUT
                elif ny == wy_deck - 3:
                    rgb[ny][nx] = CURB_TOP if not is_left else STONE_GROUT
                else:
                    rgb[ny][nx] = RET_MID
                continue

            if nx < int(round(NX_LEFT_JOIN)) and ny >= wy_draw - 3:
                # Wet mossy stone waterline where open canal laps against left brick wall
                if ny == wy_draw - 1:
                    rgb[ny][nx] = DARK_OUT
                else:
                    rgb[ny][nx] = MOSS_DK if fbm(nx * 0.24, ny * 0.35, 2, seed=71) > 0.44 else RET_WET
                continue

            if nx in (CORNER_X - 1, CORNER_X):
                rgb[ny][nx] = DARK_OUT
                continue

            if is_left:
                # True perspective vertical brick projection anchored at (VX, HORIZ_Y)
                v_wall = (ny - cy_top) / max(1.0, (wy_deck - cy_top)) * 7.5
                row = math.floor(v_wall)
                by = v_wall - row
                z_left = 1800.0 / max(20.0, VX - nx)
                col_idx = math.floor(z_left * 0.42 + (0.5 if row % 2 else 0.0))
                bx = (z_left * 0.42 + (0.5 if row % 2 else 0.0)) - col_idx
                bricks = BRICK_SIDE
            else:
                row_f = (ny - cy_top) / 7.2
                row = math.floor(row_f)
                by = row_f - row
                col_idx = math.floor((nx - CORNER_X + (8 if row % 2 else 0)) / 16.0)
                bx = ((nx - CORNER_X + (8 if row % 2 else 0)) / 16.0) - col_idx
                bricks = BRICK_TONES

            if by < 0.14 or bx < 0.08:
                c = MORTAR
            else:
                h = ((col_idx * 73856093) ^ (row * 19349663)) & 0xFFFF
                bcol = bricks[h % len(bricks)]
                if by < 0.28:
                    c = (clamp(bcol[0] + 10), clamp(bcol[1] + 10), clamp(bcol[2] + 8))
                elif by > 0.85 or bx > 0.90:
                    c = (clamp(bcol[0] - 14), clamp(bcol[1] - 14), clamp(bcol[2] - 12))
                else:
                    c = bcol
                damp = fbm(nx * 0.14, ny * 0.08, 2, seed=44)
                if (ny > wy_draw - 14 and damp > 0.56) or damp > 0.68:
                    c = MOSS_MID if by >= 0.28 else MOSS_HI
            rgb[ny][nx] = c

    # 2. Buttress Pilasters Framing Left Bay & Focal Window (nx=66..78, 154..165, 246..255)
    for p_left, p_right in [(66, 78), (154, 165), (246, 255)]:
        wy_p = WY_BACK
        for ny in range(12, wy_p - 1):
            for sx in range(p_right + 1, min(NW, p_right + 4)):
                shad[ny][sx] *= 0.74
        for ny in range(11, wy_p):
            for nx in range(p_left, p_right + 1):
                is_side = nx >= p_right - 2 and p_right < 254
                if nx in (p_left, p_right) or ny in (11, 16, wy_p - 5, wy_p - 1):
                    rgb[ny][nx] = DARK_OUT
                elif ny < 16 or ny >= wy_p - 5:
                    rgb[ny][nx] = CURB_TOP if (ny in (12, wy_p - 4) and not is_side) else (RET_MID if is_side else STONE_B)
                elif is_side:
                    rgb[ny][nx] = MORTAR if (ny % 8 == 0) else RET_DK
                else:
                    row_b = (ny - 16) // 8
                    if (ny - 16) % 8 == 0:
                        rgb[ny][nx] = MORTAR
                    elif nx <= p_left + 2:
                        rgb[ny][nx] = STONE_B
                    else:
                        rgb[ny][nx] = BRICK_TONES[row_b % 2]

    # 3. Left-Center Wall Rusted Pipes & Valve Wheel (nx=79..153) + Lantern on Middle Pilaster (159, 31)
    for y_top, y_bot in [(22, 32), (40, 47)]:
        for ny in range(y_top, y_bot + 1):
            for nx in range(79, 154):
                if ny in (y_top, y_bot):
                    rgb[ny][nx] = DARK_OUT
                elif (nx - 79) % 28 in (0, 1, 2):
                    rgb[ny][nx] = DARK_OUT if (nx - 79) % 28 == 0 else VERDIGRIS
                elif ny <= y_top + 2:
                    rgb[ny][nx] = PIPE_HI
                elif ny <= (y_top + y_bot) // 2 + 1:
                    rgb[ny][nx] = PIPE_MID
                else:
                    rgb[ny][nx] = PIPE_DK
                if ny == y_bot and y_bot + 2 < WY_BACK - 1:
                    shad[y_bot + 1][nx] *= 0.65
                    shad[y_bot + 2][nx] *= 0.80

    for ny in range(28, 60):
        for nx in range(95, 102):
            if nx in (95, 101):
                rgb[ny][nx] = DARK_OUT
            elif nx <= 97:
                rgb[ny][nx] = PIPE_HI
            elif nx <= 99:
                rgb[ny][nx] = PIPE_MID
            else:
                rgb[ny][nx] = PIPE_DK

    for ny in range(35, 51):
        for nx in range(118, 133):
            d = math.hypot(nx - 125, ny - 43)
            if 5.2 <= d <= 7.2:
                rgb[ny][nx] = DARK_OUT if d > 6.3 or d < 5.7 else (178, 86, 56)
            elif d < 2.2:
                rgb[ny][nx] = CURB_TOP if d < 1.3 else DARK_OUT
            elif abs(nx - 125) <= 1 and d < 5.5 or abs(ny - 43) <= 1 and d < 5.5:
                rgb[ny][nx] = (144, 68, 48)

    # 3b. Warm Hanging Column Lanterns mounted cleanly on ALL THREE Brick Pilasters (nx=72, 159, 250)!
    LANTERNS = [(72, 31, 0.78), (159, 31, 1.05), (250, 31, 1.15)]
    for lx, ly, _lpow in LANTERNS:
        # Small top wrought-iron hanger bracket
        for by in range(ly - 8, ly - 5):
            if 0 <= lx < NW:
                rgb[by][lx] = DARK_OUT
        for ny in range(ly - 6, ly + 7):
            for nx in range(max(0, lx - 4), min(NW, lx + 5)):
                dx, dy = abs(nx - lx), abs(ny - ly)
                if dx == 4 or dy == 6:
                    rgb[ny][nx] = DARK_OUT
                elif dx == 3 or dy == 5:
                    rgb[ny][nx] = PIPE_MID
                elif dy in (0, 3) or nx == lx:
                    rgb[ny][nx] = (54, 48, 42)
                else:
                    rgb[ny][nx] = (255, 238, 164) if (dx < 2 and dy < 3) else (232, 182, 92)
                    emit[ny][nx] = 1.0

    # 4. RIGHT-BAY UNDERGROUND SEWER MANIFOLD (nx=166..245, NO outside window!):
    # Large cast-iron overhead main collector pipe -> elbow drop trunk, pressure gauge, sluice panel & slim copper lines!
    # 4A. Large bronze-copper overhead collector trunk (y=22..29, nx=166..238) turning vertical elbow down nx=227..237 -> y=59
    for ny in range(22, 30):
        for nx in range(166, 238):
            is_collar = (nx in (182, 183, 184, 210, 211, 212))
            if ny in (22, 29) or (is_collar and nx in (182, 184, 210, 212)):
                rgb[ny][nx] = DARK_OUT
            elif is_collar:
                rgb[ny][nx] = VERDIGRIS if ny <= 26 else PIPE_DK
            elif ny <= 24:
                rgb[ny][nx] = PIPE_HI
            elif ny <= 26:
                rgb[ny][nx] = PIPE_MID
            else:
                rgb[ny][nx] = PIPE_DK
            if ny == 29 and 31 < WY_BACK:
                shad[30][nx] *= 0.68
                shad[31][nx] *= 0.82
    for ny in range(23, 61):
        for nx in range(227, 238):
            flange = ny in (29, 30, 45, 46, 58, 59)
            if nx in (227, 237) or (ny == 22 and 227 <= nx <= 237) or (flange and ny in (29, 45, 58)):
                rgb[ny][nx] = DARK_OUT
            elif ny == 60:
                rgb[ny][nx] = DARK_OUT
            elif flange:
                rgb[ny][nx] = VERDIGRIS if nx <= 233 else PIPE_DK
            elif nx <= 230:
                rgb[ny][nx] = PIPE_HI
            elif nx <= 234:
                rgb[ny][nx] = PIPE_MID
            else:
                rgb[ny][nx] = PIPE_DK
    for ny in range(23, 59):
        if 238 <= NW - 1:
            shad[ny][238] *= 0.72
            shad[ny][239] *= 0.84

    # 4B. Twin slim horizontal copper feed lines connecting to collector trunk (y=36..40, y=48..52, nx=166..227)
    for y0, y1 in [(36, 40), (48, 52)]:
        for ny in range(y0, y1 + 1):
            for nx in range(166, 228):
                if ny in (y0, y1):
                    rgb[ny][nx] = DARK_OUT
                elif (nx - 166) % 24 in (0, 1):
                    rgb[ny][nx] = DARK_OUT if (nx - 166) % 24 == 0 else VERDIGRIS
                elif ny == y0 + 1:
                    rgb[ny][nx] = PIPE_HI
                elif ny == y0 + 2:
                    rgb[ny][nx] = PIPE_MID
                else:
                    rgb[ny][nx] = PIPE_DK
                if ny == y1 and y1 + 2 < WY_BACK:
                    shad[y1 + 1][nx] *= 0.72

    # 4C. Vertical drop riser (nx=179..184, y=28..60) + Recessed dark sluice inspection hatch (nx=194..206, y=31..46)
    for ny in range(28, 60):
        for nx in range(179, 185):
            if nx in (179, 184) or ny in (58, 59):
                rgb[ny][nx] = DARK_OUT
            elif nx <= 180:
                rgb[ny][nx] = PIPE_HI
            elif nx <= 182:
                rgb[ny][nx] = PIPE_MID
            else:
                rgb[ny][nx] = PIPE_DK

    for ny in range(30, 46):
        for nx in range(193, 207):
            if nx in (193, 206) or ny in (30, 45):
                rgb[ny][nx] = DARK_OUT
            elif nx in (194, 205) or ny in (31, 44):
                rgb[ny][nx] = GRATE_MID
            else:
                # Louvered dark interior maintenance vent (pure pitch interior, NO sky!)
                rgb[ny][nx] = (34, 40, 44) if (ny % 3 == 0) else (16, 20, 24)

    # 4D. Round Muted Steel-Bronze Pressure Gauge Dial on wall (nx=217, ny=34)
    gx, gy = 217, 34
    for ny in range(gy - 5, gy + 6):
        for nx in range(gx - 5, gx + 6):
            d = math.hypot(nx - gx, ny - gy)
            if 3.2 <= d <= 5.0:
                rgb[ny][nx] = DARK_OUT if d > 4.2 else (138, 102, 58)
            elif d < 3.2:
                if (nx == gx and ny == gy) or (nx == gx + 1 and ny == gy - 1):
                    rgb[ny][nx] = DARK_OUT
                else:
                    rgb[ny][nx] = (146, 154, 144) if d < 2.2 else (112, 120, 114)
    for ny in range(39, 49):
        rgb[ny][216] = DARK_OUT
        rgb[ny][217] = PIPE_HI
        rgb[ny][218] = DARK_OUT

    # 5. UNIFIED-PERSPECTIVE T-JUNCTION + HIGH-ELEVATION DIAGONAL WALKWAY + SIDE-TO-SIDE GRATE!
    # ALL edges, masonry waterlines, floor slabs & grate bars strictly vanish to (VX=255, HORIZ_Y=20)!
    # Walkable deck centered right through Foe (192,88) [136..235] AND Player (64,152) [24..215] (Doubles-safe too!)
    SLOPE_L = -1.75
    SLOPE_R = -0.30

    def bridge_left_x(ny: int) -> float:
        return VX + SLOPE_L * (ny - HORIZ_Y)

    def bridge_right_x(ny: int) -> float:
        return VX + SLOPE_R * (ny - HORIZ_Y)

    def back_wall_hit_x(ny: int) -> float:
        return CORNER_X + (ny - WY_BACK) / FLOOR_SLOPE_L

    GRATE_Y0, GRATE_Y1 = 104, 120

    def sample_concrete_floor(nx: int, ny: int) -> tuple[int, int, int]:
        dy = max(14.0, ny - HORIZ_Y)
        u_b = (nx - VX) / dy
        z_b = 580.0 / dy
        row_i = math.floor(z_b * 0.45)
        fz = (z_b * 0.45) - row_i
        col_i = math.floor(u_b * 2.2 + (0.5 if row_i % 2 else 0.0))
        fu = (u_b * 2.2 + (0.5 if row_i % 2 else 0.0)) - col_i
        if fz < 0.055 or fu < 0.045:
            return STONE_GROUT
        c = STONE_A if ((col_i + row_i) % 2 == 0) else STONE_B
        n = fbm(nx * 0.10, ny * 0.14, 2, seed=91)
        if n > 0.68:
            c = (clamp(c[0] + 6), clamp(c[1] + 6), clamp(c[2] + 4))
        elif n < 0.30:
            c = (clamp(c[0] - 6), clamp(c[1] - 6), clamp(c[2] - 4))
        return c

    xl_back_join = bridge_left_x(BACK_PATH_Y)
    xr_back_join = bridge_right_x(BACK_PATH_Y)
    nx_join_i = int(round(NX_LEFT_JOIN))
    water_mask = [[False] * NW for _ in range(NH)]

    for nx in range(NW):
        wy_deck = wall_floor_y(nx)
        wy_start = wy_deck if nx >= nx_join_i else wall_water_y(nx)
        ny_edge_r = HORIZ_Y + (nx - VX) / SLOPE_R
        h_persp_r = PIER_H * max(0.25, (ny_edge_r - HORIZ_Y) / max(1.0, (BACK_PATH_Y - HORIZ_Y)))
        for ny in range(wy_start, NH):
            xl = bridge_left_x(ny)
            xr = bridge_right_x(ny)
            on_back_band = (wy_deck <= ny <= BACK_PATH_Y) and (nx >= nx_join_i)
            on_bridge = (ny >= BACK_PATH_Y) and (xl <= nx <= xr)
            if on_back_band or on_bridge:
                # 1. Flush Steel Drainage Grate crossing diagonal walkway side-to-side (ny = 104..120)
                if on_bridge and GRATE_Y0 <= ny <= GRATE_Y1:
                    on_top_bot = (ny in (GRATE_Y0, GRATE_Y1, GRATE_Y0 + 1, GRATE_Y1 - 1))
                    on_side = (nx <= xl + 3.2) or (nx >= xr - 3.2)
                    if on_top_bot or on_side:
                        if ny in (GRATE_Y0, GRATE_Y1) or nx <= xl + 1.2 or nx >= xr - 1.2:
                            rgb[ny][nx] = DARK_OUT
                        elif ny == GRATE_Y0 + 1 or nx <= xl + 2.4:
                            rgb[ny][nx] = GRATE_HI
                        else:
                            rgb[ny][nx] = GRATE_MID
                    else:
                        u_bar = ((nx - VX) / max(12.0, ny - HORIZ_Y)) * 12.0
                        bar_phase = u_bar - math.floor(u_bar)
                        cross = (ny in (110, 111, 115))
                        if cross:
                            rgb[ny][nx] = DARK_OUT if ny == 111 else GRATE_HI
                        elif bar_phase < 0.35:
                            rgb[ny][nx] = GRATE_HI if bar_phase < 0.14 else GRATE_MID
                        else:
                            rip = fbm(nx * 0.08, ny * 0.14, 2, seed=88)
                            rgb[ny][nx] = (18, 48, 40) if rip > 0.56 else (9, 24, 22)
                            water_mask[ny][nx] = True
                    continue

                # 2. Pale stone coping curbs along water-facing edges ONLY (seamless T-neck, flush against left wall at nx=28!)
                curb = False
                dark_edge = False
                grout_edge = False
                if on_bridge:
                    if nx <= xl + 4.0:
                        curb = True
                        dark_edge = nx <= xl + 1.1
                        grout_edge = nx >= xl + 3.2
                    elif nx >= xr - 4.0:
                        curb = True
                        dark_edge = nx >= xr - 1.1
                        grout_edge = nx <= xr - 3.2
                elif on_back_band:
                    in_t_neck = (xl_back_join + 1.0 <= nx <= xr_back_join - 1.0)
                    if not in_t_neck and ny >= BACK_PATH_Y - 3:
                        curb = True
                        dark_edge = (ny == BACK_PATH_Y)
                        grout_edge = (ny == BACK_PATH_Y - 3)

                if curb:
                    rgb[ny][nx] = DARK_OUT if dark_edge else (STONE_GROUT if grout_edge else CURB_TOP)
                else:
                    rgb[ny][nx] = sample_concrete_floor(nx, ny)
                    if ny <= wy_deck + 1:
                        shad[ny][nx] *= 0.80  # Contact AO where floor meets back/left masonry skirting
                continue

            # B. High-Elevation Vertical Stone Masonry Quay Walls (with open water-pass gap beneath drainage grate!)
            in_left_wing_drop = (nx_join_i <= nx < xl_back_join + 1.0) and (BACK_PATH_Y < ny <= BACK_PATH_Y + PIER_H)
            in_right_wing_drop = (nx > xr_back_join - 1.0) and (BACK_PATH_Y < ny <= BACK_PATH_Y + PIER_H)
            in_diag_right_drop = (ny_edge_r >= BACK_PATH_Y) and (ny_edge_r < ny <= ny_edge_r + h_persp_r)
            in_grate_water_pass = in_diag_right_drop and (GRATE_Y0 - 0.5 <= ny_edge_r <= GRATE_Y1 + 0.5)

            if in_grate_water_pass:
                dw = ny - ny_edge_r
                t_h = dw / max(1.0, h_persp_r)
                if dw <= 2.2:
                    # Thin steel girder underside carrying the grate across the water pass!
                    rgb[ny][nx] = DARK_OUT if dw >= 1.5 else GRATE_MID
                elif t_h < 0.62:
                    # Open dark shadowed culvert void beneath the steel grate
                    rgb[ny][nx] = (10, 22, 22)
                    shad[ny][nx] *= 0.68
                else:
                    # Murky water flowing out underneath the grate gap directly into the right canal!
                    water_mask[ny][nx] = True
                    p_w = max(0.0, (ny - 64) / 128.0)
                    wz = 18.0 / (0.18 + p_w * 0.95)
                    rip = fbm(nx * 0.055, wz * 0.55, 2, seed=88)
                    rgb[ny][nx] = WATER_SCUM if rip > 0.48 else WATER_DEEP
                    shad[ny][nx] *= 0.82
                continue

            if in_left_wing_drop or in_right_wing_drop or in_diag_right_drop:
                if in_diag_right_drop:
                    dw = ny - ny_edge_r
                    h_tot = h_persp_r
                    z_flank = 1100.0 / max(18.0, ny_edge_r - HORIZ_Y)
                    is_pier = (int(math.floor(z_flank)) % 4 == 0)
                    v_joint = (abs(z_flank - round(z_flank)) < 0.08) or (abs(ny_edge_r - (GRATE_Y0 - 1.5)) <= 1.1) or (abs(ny_edge_r - (GRATE_Y1 + 1.5)) <= 1.1)
                else:
                    dw = ny - BACK_PATH_Y
                    h_tot = float(PIER_H)
                    is_pier = ((nx - nx_join_i) % 26) < 5
                    v_joint = ((nx - nx_join_i + (7 if dw > h_tot * 0.45 else 0)) % 14 == 0)

                t_h = dw / max(1.0, h_tot)
                if t_h >= 0.92:
                    rgb[ny][nx] = DARK_OUT  # Crisp bottom waterline
                elif t_h <= 0.14:
                    rgb[ny][nx] = (20, 24, 28)  # Deep under-coping overhang shadow!
                elif t_h >= 0.74:
                    moss_n = fbm(nx * 0.24, ny * 0.35, 2, seed=71)
                    rgb[ny][nx] = MOSS_DK if moss_n > 0.44 else RET_WET  # Organic damp waterline algae (no stripes!)
                elif 0.44 <= t_h <= 0.52 or (v_joint and not is_pier):
                    rgb[ny][nx] = MORTAR
                elif is_pier:
                    rgb[ny][nx] = RET_HI if t_h < 0.44 else RET_MID
                else:
                    rgb[ny][nx] = RET_MID if t_h < 0.44 else RET_DK
                continue

            # C. Deep Sunken Green Sewer Water + Strong Overhang Cast Shadows!
            water_mask[ny][nx] = True
            under_bridge_shad = (
                (ny <= wy_start + 3 and nx < nx_join_i)
                or (xl - 6.5 <= nx < xl and ny >= BACK_PATH_Y)
                or ((nx_join_i <= nx <= xl_back_join or nx >= xr_back_join) and BACK_PATH_Y + PIER_H < ny <= BACK_PATH_Y + PIER_H + 4)
                or (ny_edge_r >= BACK_PATH_Y and not (GRATE_Y0 - 0.5 <= ny_edge_r <= GRATE_Y1 + 0.5) and 0.0 < ny - (ny_edge_r + h_persp_r) <= 4.0)
            )
            p_w = max(0.0, (ny - 64) / 128.0)
            wz = 18.0 / (0.18 + p_w * 0.95)
            rip = fbm(nx * 0.055, wz * 0.55, 2, seed=88)
            wave = math.sin(wz * 1.15 + nx * 0.08 + rip * 2.5) * 0.5 + 0.5
            if under_bridge_shad:
                rgb[ny][nx] = (10, 28, 25)
                shad[ny][nx] *= 0.72
            elif rip > 0.68 and wave > 0.55:
                rgb[ny][nx] = WATER_FOAM
            elif rip > 0.52 or wave > 0.72:
                rgb[ny][nx] = WATER_SCUM
            elif rip < 0.34:
                rgb[ny][nx] = WATER_DEEP
            else:
                rgb[ny][nx] = WATER_MID

    # 6. Receding Left-Wall Outfall Culvert Arch & Waterfall into Open Foreground Pool (nx=3..22, completely clear of nx=28!)
    out_cx, out_cy = 12, 51
    for ny in range(28, 76):
        for nx in range(2, 23):
            dx_raw = nx - out_cx
            dy_sheared = (ny - out_cy) + dx_raw * (-FLOOR_SLOPE_L)
            dx = dx_raw / 8.0
            dy = dy_sheared / 14.5
            d2 = dx * dx + dy * dy
            if d2 <= 1.38:
                if d2 > 1.0:
                    ang = math.atan2(dy_sheared, dx_raw)
                    block_joint = abs((ang / 0.48) - round(ang / 0.48)) < 0.11
                    if d2 > 1.28 or d2 < 1.06 or block_joint:
                        rgb[ny][nx] = DARK_OUT
                    else:
                        rgb[ny][nx] = (92, 98, 96) if (dx_raw - dy_sheared * 0.5) < 0 else (66, 72, 74)
                elif d2 > 0.74:
                    rgb[ny][nx] = (46, 52, 54) if dy_sheared < 3 else (32, 42, 42)
                else:
                    # Deep arched sewer gallery: dark shadowed water bed at the bottom flowing out cleanly!
                    if dy_sheared >= 4.0 and abs(dx_raw) <= 5.5:
                        rgb[ny][nx] = (18, 46, 42) if dy_sheared < 8.5 else WATER_DEEP
                    else:
                        depth_g = max(0.0, 1.0 - math.hypot(dx * 0.9, dy * 0.9))
                        rgb[ny][nx] = (18, 26, 26) if depth_g > 0.35 else (28, 36, 38)
                        shad[ny][nx] = 0.78

    # Curved stone threshold apron seated neatly at lower tunnel rim
    for ny in range(54, 68):
        for nx in range(7, 18):
            lip_floor = 59.5 - (nx - 7) * (-FLOOR_SLOPE_L)
            if lip_floor <= ny <= lip_floor + 3.2:
                if ny >= lip_floor + 2.2 or nx in (7, 17):
                    rgb[ny][nx] = DARK_OUT
                elif ny <= lip_floor + 0.8:
                    rgb[ny][nx] = RET_MID
                else:
                    rgb[ny][nx] = MOSS_DK if fbm(nx * 0.3, ny * 0.3, 2, seed=71) > 0.48 else RET_DK

    # Parabolic Waterfall pouring smoothly from dark tunnel channel over stone lip (nx=12 -> splashing at nx=19, ny=93..105!)
    for ny in range(53, 98):
        t_fall = (ny - 53) / 44.0
        cx_arc = 12.0 + 7.5 * (1.0 - (1.0 - t_fall) ** 1.95)
        half_w = 4.0 + 2.1 * (t_fall ** 0.75)
        for nx in range(max(0, int(cx_arc - half_w - 2)), min(NW, int(cx_arc + half_w + 3))):
            dx = abs(nx - cx_arc)
            y_lip_stream = 57.5 - (nx - 7) * (-FLOOR_SLOPE_L)
            if ny < y_lip_stream:
                continue
            if dx <= half_w:
                n_s = value_noise_2d(nx * 0.65, ny * 0.25, seed=107)
                if t_fall > 0.86:
                    if n_s + (1.0 - dx / half_w) * 0.5 > 0.72:
                        rgb[ny][nx] = WATER_FOAM if n_s > 0.45 else WATER_SCUM
                    continue
                if dx > half_w - 1.0:
                    rgb[ny][nx] = DARK_OUT
                elif y_lip_stream <= ny <= y_lip_stream + 2.0 and dx < half_w - 1.2:
                    rgb[ny][nx] = WATER_FOAM if n_s > 0.35 else WATER_SCUM
                elif n_s > 0.62:
                    rgb[ny][nx] = WATER_FOAM
                elif n_s > 0.40:
                    rgb[ny][nx] = WATER_SCUM
                else:
                    rgb[ny][nx] = WATER_MID

    for ny in range(92, 108):
        for nx in range(4, 38):
            d_ring = math.hypot((nx - 19) * 0.46, (ny - 97) * 1.1)
            fn = fbm(nx * 0.38, ny * 0.44, 2, seed=313)
            if (2.0 < d_ring < 3.8 and fn > 0.36) or (5.0 < d_ring < 6.4 and fn > 0.52 and ny >= 96):
                rgb[ny][nx] = WATER_FOAM if fn > 0.55 else WATER_SCUM

    # 7. Solid 2-Pass Bronze Safety Railings anchored directly to Left Brick Wall (nx=29, ny=73) & T-Corners!
    def draw_solid_rail(slope: float, x_offset: float, y_start: int, y_end: int, step_posts: int = 16):
        steep = abs(slope) < 1.0
        points = []
        for ny in range(y_start, y_end + 1):
            if GRATE_Y0 - 1 <= ny <= GRATE_Y1 + 1:
                continue
            nx_c = int(round(VX + slope * (ny - HORIZ_Y) + x_offset))
            next_nx = int(round(VX + slope * (ny + 1 - HORIZ_Y) + x_offset))
            ry = ny - 6
            if ry >= 58:
                points.append((ry, nx_c, min(nx_c, next_nx), max(nx_c, next_nx)))

        for ry, nx_c, x_lo, x_hi in points:
            pad_l = 1 if steep else 0
            pad_r = 2 if steep else 0
            for x_px in range(max(0, x_lo - pad_l), min(NW, x_hi + pad_r + 1)):
                for oy in (-1, 0, 1, 2):
                    if 0 <= ry + oy < NH:
                        rgb[ry + oy][x_px] = DARK_OUT

        for ry, nx_c, x_lo, x_hi in points:
            if steep:
                if 0 <= nx_c < NW:
                    rgb[ry][nx_c] = PIPE_HI
                    if nx_c + 1 < NW:
                        rgb[ry][nx_c + 1] = PIPE_DK
            else:
                for x_px in range(max(0, x_lo), min(NW, x_hi + 1)):
                    rgb[ry][x_px] = PIPE_HI
                    rgb[ry + 1][x_px] = PIPE_DK

        anchors = [y for y in (y_start, GRATE_Y0 - 2, GRATE_Y1 + 2) if y_start <= y <= y_end]
        post_ys = list(anchors)
        for y in range(y_start, y_end + 1, step_posts):
            if all(abs(y - a) >= 9 for a in anchors):
                post_ys.append(y)
        for ny in post_ys:
            if GRATE_Y0 - 1 <= ny <= GRATE_Y1 + 1:
                continue
            nx = int(round(VX + slope * (ny - HORIZ_Y) + x_offset))
            if 2 <= nx < NW - 2:
                for ox in (-1, 0, 1):
                    for py in range(max(56, ny - 8), ny + 1):
                        rgb[py][nx + ox] = DARK_OUT if (ox != 0 or py == ny - 8) else PIPE_MID

    def draw_horiz_rail(x0: int, x1: int, y_base: int, post_step: int = 28):
        ry = y_base - 6
        for x_px in range(max(0, x0), min(NW, x1 + 1)):
            rgb[ry - 1][x_px] = DARK_OUT
            rgb[ry][x_px] = PIPE_HI
            rgb[ry + 1][x_px] = PIPE_DK
            rgb[ry + 2][x_px] = DARK_OUT
        n_spans = max(1, round((x1 - x0) / float(post_step)))
        posts = [int(round(x0 + (x1 - x0) * i / float(n_spans))) for i in range(n_spans + 1)]
        for px in posts:
            if 1 <= px < NW - 1:
                for ox in (-1, 0, 1):
                    for py in range(y_base - 8, y_base + 1):
                        rgb[py][px + ox] = DARK_OUT if (ox != 0 or py == y_base - 8) else PIPE_MID

    left_join_x = int(round(xl_back_join + 2.0))
    right_join_x = int(round(xr_back_join - 2.0))
    draw_horiz_rail(nx_join_i, left_join_x, BACK_PATH_Y, post_step=30)
    draw_horiz_rail(right_join_x, NW - 2, BACK_PATH_Y, post_step=18)
    draw_solid_rail(SLOPE_L, +2.0, BACK_PATH_Y, 168, step_posts=18)
    draw_solid_rail(SLOPE_R, -2.0, BACK_PATH_Y, 190, step_posts=24)

    # 8. Subterranean Temple-Style Lighting — 3 Warm Hanging Column Lanterns & Soft Overhead Diagonal Arena Glow!
    # Zero outdoor sky window; warm lanterns illuminate pillars, pipes & high stone pier above darker sunken canals!
    out = Image.new("RGBA", (NW * 2, NH * 2))
    opx = out.load()

    for ny in range(NH):
        for nx in range(NW):
            br, bg, bb = rgb[ny][nx]
            if emit[ny][nx] > 0.5:
                r, g, b = br, bg, bb
            else:
                # Accumulate warm subterranean glow cones from ALL 3 pilaster lanterns (72, 159, 250)
                lantern_strength = 0.0
                for lx_i, ly_i, l_pow in LANTERNS:
                    dl = math.hypot((nx - lx_i) * 0.62, (ny - ly_i - 6.0) * 0.72)
                    lantern_strength = max(lantern_strength, l_pow * math.exp(-1.45 * (dl / 54.0) ** 2))

                # Subtle overhead maintenance light shaft pouring along diagonal battle deck from upper-right ceiling lamp
                t_ray = max(0.0, min(1.35, (ny - 20) / 132.0))
                ray_cx = 232.0 - 134.0 * t_ray
                ray_w = 34.0 + 62.0 * t_ray
                d_beam = abs(nx - ray_cx) / ray_w
                beam_strength = 0.72 * math.exp(-1.55 * d_beam * d_beam) * (1.0 if ny >= 18 else math.exp(-0.25 * (18 - ny)))

                amb = 0.42 + 0.08 * max(0.0, (ny - 64) / 128.0)
                if nx < CORNER_X and ny < (wall_floor_y(nx) if nx >= nx_join_i else wall_water_y(nx)):
                    amb *= 0.84
                if water_mask[ny][nx]:
                    amb *= 0.78  # Deepen sunken water value so elevated walkway unmistakably stands higher!
                amb *= shad[ny][nx]

                light_r = amb + beam_strength * 0.64 + lantern_strength * 0.58
                light_g = amb + beam_strength * 0.70 + lantern_strength * 0.48
                light_b = amb + beam_strength * 0.58 + lantern_strength * 0.24

                r = clamp(br * light_r + beam_strength * 8 + lantern_strength * 12)
                g = clamp(bg * light_g + beam_strength * 10 + lantern_strength * 9)
                b = clamp(bb * light_b + beam_strength * 6 + lantern_strength * 3)

            c4 = (r, g, b, 255)
            x, y = nx * 2, ny * 2
            opx[x, y] = c4
            opx[x + 1, y] = c4
            opx[x, y + 1] = c4
            opx[x + 1, y + 1] = c4

    return out


def main():
    bg = build_sewers()
    bg.save(BB_DIR / "battlebgSewers.png")

    sheet = Image.new("RGBA", (532, 424), (22, 25, 34, 255))
    draw = ImageDraw.Draw(sheet)
    draw.text((14, 6), "Sewers v7 - Subterranean lanterns, unified VP & high pier (512x384)", fill=(237, 189, 98, 255))
    comp = bg.copy()
    for dx in range(0, 512, 8):
        ImageDraw.Draw(comp).line([(dx, 304), (dx + 4, 304)], fill=(255, 255, 255, 110))
    sheet.alpha_composite(comp, (10, 26))
    sheet.save(ROOT / "previews" / "sewers_battleback_review.png")
    print("Installed diagonal-perspective Sewers battleback cleanly.")


if __name__ == "__main__":
    main()
