"""Shared 3D Projective Stadium Geometry, Volumetric Architecture & Uniform 1px Pixel-Art Primitives (v4).

v4 Architectural & Visual Coherence Principles (matching battlebgGym01Normal.png):
  1. True Vanishing Point Alignment (VP = (338, -15)):
     - NO flat horizontal screen-top bars! Upper frieze/capital bands follow `wall_y_from_h(nx, h)`
       along the exact perspective ray from left wall -> corner -> back wall.
     - Left-wall columns reveal a foreshortened LEFT depth return + bright corner crest + cast shadow;
       back-wall columns reveal a RIGHT depth return, matching Gym01Normal's exact camera projection.
     - Column plinths follow `wall_floor_y(nx)` diagonally (never flat horizontal boxes).
  2. Visual Coherence & Consistent Line Weight:
     - Architectural walls, trims & columns separate via crisp bevel highlight/shadow value planes
       rather than heavy black outlines wrapping every edge.
     - Foreground 3D objects placed in front of walls render through `paint_1px_prop_buffer`, guaranteeing
       a strictly uniform 1-native-pixel (2x2 screen) hue-shifted dark contour (no 2px staircase blobs)
       plus physical wall & floor cast shadows!
  3. Uniform-Width Elliptical Court Lines & Pokeball Rings:
     - Uses analytical gradient distance so curved Pokeball bands keep identical pixel thickness
       along shallow horizontal arcs and sharp vertical sides.
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
BB_DIR = ROOT / "Graphics" / "Battlebacks"
PREV_DIR = ROOT / "previews"

NW, NH = 256, 192
CORNER_X = 169
VP_WX, VP_WY = 338.0, -15.0
COLS = [(45, 57, True), (125, 131, True), (205, 211, False), (248, 255, False)]
BAYS = [(2, 43), (59, 123), (133, 203), (213, 246)]


def clamp(v: float) -> int:
    return max(0, min(255, int(round(v))))


def shade_col(c: tuple[int, int, int], factor: float, add: tuple[int, int, int] = (0, 0, 0)) -> tuple[int, int, int]:
    return (
        clamp(c[0] * factor + add[0]),
        clamp(c[1] * factor + add[1]),
        clamp(c[2] * factor + add[2]),
    )


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


def wall_floor_y(nx: float) -> float:
    if nx <= CORNER_X:
        return 67.0 - nx * (41.0 / CORNER_X)
    return 26.0 + (nx - CORNER_X) * (2.0 / 86.0)


def wall_stripe_y(nx: float) -> float:
    if nx <= CORNER_X:
        return 45.0 - nx * (30.0 / CORNER_X)
    return 15.0 + (nx - CORNER_X) * (1.0 / 86.0)


def wall_y_from_h(nx: float, h_frac: float) -> float:
    """Exact screen Y for a given perspective height fraction h_frac in [0..1]."""
    wy = wall_floor_y(nx)
    h_span = (wy - VP_WY) if nx <= CORNER_X else 41.0
    return wy - h_frac * h_span


def wall_uv(nx: float, ny: float) -> tuple[float, float, bool]:
    """Corner-continuous perspective coordinates across left wall & back wall."""
    wy = wall_floor_y(nx)
    if nx <= CORNER_X:
        d_left = (338.0 / max(24.0, VP_WX - nx) - 1.0) * 10.0  # 0.0 at x=0 -> 10.0 at corner
        h_left = (wy - ny) / max(10.0, wy - VP_WY)
        return d_left, h_left, False
    u_back = 10.0 + (nx - CORNER_X) * 0.11834
    h_back = (wy - ny) / 41.0
    return u_back, h_back, True


def court_mid_y(nx: float) -> float:
    return 103.0 + nx * 0.0863


# --- Exact 3x3 Projective Floor Homography ---
def _solve_h(src, dst):
    A, b = [], []
    for (u, v), (x, y) in zip(src, dst):
        A.append([u, v, 1, 0, 0, 0, -x * u, -x * v])
        b.append(x)
        A.append([0, 0, 0, u, v, 1, -y * u, -y * v])
        b.append(y)
    n = 8
    M = [A[i] + [b[i]] for i in range(n)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        M[col], M[piv] = M[piv], M[col]
        div = M[col][col]
        for k in range(col, n + 1):
            M[col][k] /= div
        for r in range(n):
            if r != col:
                f = M[r][col]
                for k in range(col, n + 1):
                    M[r][k] -= f * M[col][k]
    h = [M[i][n] for i in range(n)] + [1.0]
    m = [h[0:3], h[3:6], h[6:9]]
    det = (
        m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
        - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
        + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
    )
    return [
        [(m[1][1] * m[2][2] - m[1][2] * m[2][1]) / det, (m[0][2] * m[2][1] - m[0][1] * m[2][2]) / det, (m[0][1] * m[1][2] - m[0][2] * m[1][1]) / det],
        [(m[1][2] * m[2][0] - m[1][0] * m[2][2]) / det, (m[0][0] * m[2][2] - m[0][2] * m[2][0]) / det, (m[0][2] * m[1][0] - m[0][0] * m[1][2]) / det],
        [(m[1][0] * m[2][1] - m[1][1] * m[2][0]) / det, (m[0][1] * m[2][0] - m[0][0] * m[2][1]) / det, (m[0][0] * m[1][1] - m[0][1] * m[1][0]) / det],
    ]


_H_INV = _solve_h(
    [(0.0, 0.0), (4.0, 0.0), (0.0, 6.0), (4.0, 6.0)],
    [(169.0, 26.0), (255.0, 28.0), (0.0, 67.0), (161.5, 76.4)],
)

FLOOR_UV: list[list[tuple[float, float]]] = [[(0.0, 0.0)] * NW for _ in range(NH)]
for _y in range(NH):
    for _x in range(NW):
        _u = _H_INV[0][0] * _x + _H_INV[0][1] * _y + _H_INV[0][2]
        _v = _H_INV[1][0] * _x + _H_INV[1][1] * _y + _H_INV[1][2]
        _w = _H_INV[2][0] * _x + _H_INV[2][1] * _y + _H_INV[2][2]
        _w = _w if abs(_w) > 1e-4 else 1e-4
        FLOOR_UV[_y][_x] = (_u / _w, _v / _w)


def compute_grid_cells(su: float, sv: float, rotate45: bool = False):
    """Exact uniform 1-native-pixel grout seams without aliasing/gaps."""
    cells = [[(0, 0)] * NW for _ in range(NH)]
    edges = [[False] * NW for _ in range(NH)]
    for ny in range(NH):
        for nx in range(NW):
            u, v = FLOOR_UV[ny][nx]
            if rotate45:
                cu = math.floor(u * su + v * sv)
                cv = math.floor(u * su - v * sv)
            else:
                cu = math.floor(u * su)
                cv = math.floor(v * sv)
            cells[ny][nx] = (cu, cv)
    for ny in range(1, NH):
        for nx in range(1, NW):
            c = cells[ny][nx]
            if c != cells[ny][nx - 1] or c != cells[ny - 1][nx]:
                edges[ny][nx] = True
    return cells, edges


def floor_surface_light(nx: int, ny: int) -> float:
    u, v = FLOOR_UV[ny][nx]
    return fbm(u * 0.42, v * 0.42, 2, seed=21)


def is_standard_court_line(nx: int, ny: int, inset: float = 0.0) -> bool:
    ym = court_mid_y(nx)
    if abs(ny - ym) <= 0.92:
        dx = (nx - 120.0) / 50.0
        dy = (ny - 113.5) / 16.0
        if dx * dx + dy * dy > 0.96:
            return True
    y_b_left = 64.0 + inset - nx * (25.0 / 112.0)
    y_b_back = 39.0 + inset + (nx - 112.0) * (4.0 / 143.0)
    if nx <= 112:
        if abs(ny - y_b_left) <= 0.78:
            return True
    else:
        if abs(ny - y_b_back) <= 0.78:
            return True
    if nx >= 216:
        ys = 27.5 + inset + (nx - 216.0) * (8.5 / 39.0)
        if abs(ny - ys) <= 0.78:
            return True
    return False


# --- Universal Uniform 1-Native-Pixel Prop Compositor + Cast Shadow ---
def paint_1px_prop_buffer(
    rgb,
    pix: dict[tuple[int, int], tuple[int, int, int]],
    outline_col: tuple[int, int, int],
    shadow_dx: int = 2,
    shadow_dy: int = 1,
    wall_only_shadow: bool = False,
    clip_to_floor: bool = False,
):
    """Composites any 3D prop pixel dict onto rgb with:
      1) Realistic soft cast shadow thrown onto the wall/floor behind-right of the object
      2) Guaranteed uniform 1-native-pixel (4-neighbor) contour (never 2px blobs!)
      3) Interior shaded 3D planes cleanly rendered on top.
    """
    if not pix:
        return
    # 1. Cast shadow shifted (shadow_dx, shadow_dy) on empty background behind prop
    shadow_pts: set[tuple[int, int]] = set()
    for (px, py) in pix:
        sx, sy = px + shadow_dx, py + shadow_dy
        if (sx, sy) not in pix and 0 <= sx < NW and 0 <= sy < NH:
            if wall_only_shadow and sy >= wall_floor_y(sx) + 1:
                continue
            shadow_pts.add((sx, sy))
        # Subtle grounding floor shadow directly below base edge (`py+1`)
        if 0 <= px < NW and 0 <= py + 1 < NH and (px, py + 1) not in pix and py + 1 >= wall_floor_y(px):
            shadow_pts.add((px, py + 1))

    # 2. Strict 4-neighbor outer contour -> GUARANTEED uniform 1-native-pixel edge!
    contour: set[tuple[int, int]] = set()
    for (px, py) in pix:
        for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            qx, qy = px + ox, py + oy
            if (qx, qy) not in pix and 0 <= qx < NW and 0 <= qy < NH:
                if clip_to_floor and qy > wall_floor_y(qx) + 3:
                    continue
                contour.add((qx, qy))

    for sx, sy in shadow_pts:
        if (sx, sy) not in contour:
            rgb[sy][sx] = shade_col(rgb[sy][sx], 0.74)

    for cx, cy in contour:
        rgb[cy][cx] = outline_col

    for (px, py), col in pix.items():
        if 0 <= px < NW and 0 <= py < NH:
            rgb[py][px] = col


def draw_3d_box_prop(
    pix: dict[tuple[int, int], tuple[int, int, int]],
    x0: int,
    x1: int,
    y_top_front: int,
    y_bot_front: int,
    front_hi: tuple[int, int, int],
    front_dk: tuple[int, int, int],
    side_col: tuple[int, int, int],
    top_col: tuple[int, int, int],
    perspective_wall: str = "back",  # "left", "back", "corner"
    side_w: int = 3,
    top_h: int = 2,
):
    """Writes a true 3D prism (top lip + lit front plane + receding shaded side return) into prop pixel dict."""
    for px in range(x0, x1 + 1):
        # Perspective slant on Y if mounted along left wall vs back wall
        slope = -(px - x0) * 0.24 if perspective_wall == "left" else (0.0 if perspective_wall == "corner" else (px - x0) * 0.025)
        yt = int(round(y_top_front + slope))
        yb = int(round(y_bot_front + slope))
        # Top receding depth face
        for ty in range(yt - top_h, yt):
            tx_off = 1 if perspective_wall == "left" else (0 if perspective_wall == "corner" else -1)
            pix[(px + tx_off, ty)] = top_col
        # Front illuminated plane
        for py in range(yt, yb + 1):
            pix[(px, py)] = front_hi if px < (x0 + x1) * 0.65 and py == yt else front_dk

    # Receding side return plane (on right side for left/corner props, or left/right foreshortened)
    if side_w > 0:
        rx0 = x1 + 1 if perspective_wall in ("left", "corner") else x0 - side_w
        rx1 = x1 + side_w if perspective_wall in ("left", "corner") else x0 - 1
        base_x = x1 if perspective_wall in ("left", "corner") else x0
        slope_b = -(base_x - x0) * 0.24 if perspective_wall == "left" else 0.0
        yt0 = int(round(y_top_front + slope_b))
        yb0 = int(round(y_bot_front + slope_b))
        for k, sx in enumerate(range(rx0, rx1 + 1), start=1):
            dy_s = -k if perspective_wall == "left" else -(k // 2)
            for py in range(yt0 + dy_s, yb0 + dy_s + 1):
                pix[(sx, py)] = top_col if py < yt0 + max(-1, dy_s) else side_col


def apply_wall_architectural_volume(
    rgb,
    cornice_hi: tuple[int, int, int],
    cornice_dk: tuple[int, int, int],
    trim_hi: tuple[int, int, int],
    trim_mid: tuple[int, int, int],
    trim_dk: tuple[int, int, int],
    base_hi: tuple[int, int, int],
    base_dk: tuple[int, int, int],
    out_col: tuple[int, int, int],
    recess_upper: bool = True,
    upper_frieze: bool = True,
):
    """Adds subtle 3D architectural wall depth in Gym01Normal visual language (clean bevel planes, NO flat ceiling bars):
      - Back wall (nx > 169) shaded slightly deeper than left wall (nx <= 169) so the corner turns cleanly in 3D space!
      - Optional true-perspective upper frieze molding along `wall_y_from_h(nx, 0.56)` aiming right at VP=(338,-15)!
      - Beveled protruding mid-wall waist beam (`sy-1..sy+2`) casting a crisp 2px under-shadow down onto lower wall
      - Recessed upper bay side & top reveal bevels without heavy black lines
      - Clean floor baseboard (`wy-2..wy-1`) + 2px floor contact AO!
    """
    for nx in range(NW):
        wy = int(round(wall_floor_y(nx)))
        sy = wall_stripe_y(nx)
        is_back = nx > CORNER_X

        # 1. Back wall directional depth shading (matches Gym01Normal's lit left wall vs shaded back wall!)
        if is_back:
            for ny in range(0, wy):
                rgb[ny][nx] = shade_col(rgb[ny][nx], 0.87)

        # 2. Recessed upper bay niches (top shadow + left inner recess bevel)
        if recess_upper:
            y_hi_lim = max(0, int(round(wall_y_from_h(nx, 0.66)))) if upper_frieze else 1
            for bx0, bx1 in BAYS:
                if bx0 + 3 <= nx <= bx1 - 3:
                    y_pan_top = max(1, y_hi_lim + 2)
                    y_pan_bot = max(y_pan_top + 1, int(round(sy - 3)))
                    if nx == bx0 + 3:
                        for ny in range(y_pan_top, y_pan_bot + 1):
                            rgb[ny][nx] = shade_col(rgb[ny][nx], 0.80)
                    elif nx == bx1 - 3:
                        for ny in range(y_pan_top, y_pan_bot + 1):
                            rgb[ny][nx] = shade_col(rgb[ny][nx], 1.09)
                    if y_pan_top < y_pan_bot and y_hi_lim >= 0:
                        rgb[y_pan_top][nx] = shade_col(rgb[y_pan_top][nx], 0.82)
                        rgb[y_pan_bot][nx] = shade_col(rgb[y_pan_bot][nx], 1.10)

        # 3. True-perspective upper architectural frieze beam (vanishing toward VP=(338,-15), exits top near nx=135!)
        if upper_frieze:
            yc = wall_y_from_h(nx, 0.68)
            y_c0 = int(round(yc - 1.0))
            y_c1 = int(round(yc + 1.0))
            if y_c1 >= 0:
                for ny in range(max(0, y_c0), min(wy - 4, y_c1 + 3)):
                    if ny == y_c0:
                        rgb[ny][nx] = shade_col(cornice_hi, 0.88 if is_back else 1.0)
                    elif ny <= y_c1:
                        rgb[ny][nx] = shade_col(cornice_dk, 0.88 if is_back else 1.0)
                    elif ny == y_c1 + 1:
                        rgb[ny][nx] = shade_col(rgb[ny][nx], 0.72)  # Under-frieze cast shadow!
                    else:
                        rgb[ny][nx] = shade_col(rgb[ny][nx], 0.88)

        # 4. Protruding mid-wall waist beam ledge (clean bevel lip -> face -> underside shadow, ZERO black boxes!)
        y_top_l = int(round(sy - 1.5))
        y_bot_l = int(round(sy + 1.5))
        m_back = 0.88 if is_back else 1.0
        for ny in range(max(1, y_top_l), min(wy - 2, y_bot_l + 3)):
            if ny == y_top_l:
                rgb[ny][nx] = shade_col(trim_hi, m_back)  # Top lit upward bevel!
            elif ny < y_bot_l:
                rgb[ny][nx] = shade_col(trim_mid, m_back)
            elif ny == y_bot_l:
                rgb[ny][nx] = shade_col(trim_dk, m_back)  # Underside soffit bevel
            elif ny == y_bot_l + 1:
                rgb[ny][nx] = shade_col(rgb[ny][nx], 0.70)  # Cast under-beam shadow
            else:
                rgb[ny][nx] = shade_col(rgb[ny][nx], 0.86)

        # 5. Corner depth crease AO right at nx=169..170
        if nx in (CORNER_X, CORNER_X + 1):
            for ny in range(0, wy):
                rgb[ny][nx] = shade_col(rgb[ny][nx], 0.84 if nx == CORNER_X else 0.90)

        # 6. Clean floor baseboard trim (`wy-2..wy-1`) + 2px floor contact AO!
        for ny in range(max(0, wy - 2), wy):
            rgb[ny][nx] = shade_col(base_hi if ny == wy - 2 else base_dk, m_back)
        for fy in range(wy, min(NH, wy + 2)):
            rgb[fy][nx] = shade_col(rgb[fy][nx], 0.80 if fy == wy else 0.91)


def draw_volumetric_column(
    rgb,
    col_x0: int,
    col_x1: int,
    c_spec: tuple[int, int, int],
    c_lit: tuple[int, int, int],
    c_mid: tuple[int, int, int],
    c_shad: tuple[int, int, int],
    out_col: tuple[int, int, int],
    style: str = "cylinder",  # "cylinder" or "pier"
    cap_hi: tuple[int, int, int] | None = None,
    cap_dk: tuple[int, int, int] | None = None,
    fluted: bool = False,
    upper_frieze: bool = True,
):
    """Perspective-accurate 3D architectural column matching Gym01Normal camera angle!

    - Extends all the way cleanly from ny=0 down to wall_floor_y(nx) (base slopes along wy!).
    - Left-wall pillars reveal their LEFT return side face (1-2px shaded) + bright 1px corner crest
      + lit front plane + soft cast wall/floor shadow on the right!
    - Back-wall pillars reveal a crisp RIGHT return side face + right shadow.
    - Cylindrical pillars wrap smoothly in 3D and project a subtle curved rounded base 1px onto the floor.
    - Optional sculpted capital collar aligns strictly to perspective height hw=0.56 (NEVER flat horizontal)!
    """
    if cap_hi is None:
        cap_hi = c_lit
    if cap_dk is None:
        cap_dk = c_shad

    w = col_x1 - col_x0 + 1
    is_back = col_x0 >= CORNER_X
    # Cast shadow thrown down-right from column onto bay wall & floor
    shad_w = 3 if w >= 10 else 2
    for sx in range(col_x1 + 1, min(NW, col_x1 + shad_w + 1)):
        wy_s = int(round(wall_floor_y(sx)))
        fade = 0.78 if sx == col_x1 + 1 else (0.88 if sx == col_x1 + 2 else 0.94)
        for sy in range(0, min(NH, wy_s + 3)):
            rgb[sy][sx] = shade_col(rgb[sy][sx], fade)

    ret_w = 2 if w >= 10 else 1
    for nx in range(col_x0, col_x1 + 1):
        wy = wall_floor_y(nx)
        t_x = (nx - col_x0) / max(1.0, float(col_x1 - col_x0))
        dx_c = (nx - (col_x0 + col_x1) * 0.5) / max(1.0, w * 0.5)

        if style == "cylinder":
            # Smooth 3D round wrap + rounded elliptical floor base projection (+1px at column front curve)
            if not is_back:
                if t_x < 0.16:
                    shaft_c = c_mid
                elif t_x < 0.36:
                    shaft_c = c_spec
                elif t_x < 0.68:
                    shaft_c = c_lit
                elif t_x < 0.86:
                    shaft_c = c_mid
                else:
                    shaft_c = c_shad
            else:
                if t_x < 0.25:
                    shaft_c = c_spec
                elif t_x < 0.65:
                    shaft_c = c_lit
                elif t_x < 0.84:
                    shaft_c = c_mid
                else:
                    shaft_c = c_shad
            if fluted and (nx - col_x0) % 3 == 2 and t_x < 0.88:
                shaft_c = c_mid if t_x < 0.55 else c_shad
            base_drop = 1.4 * max(0.0, 1.0 - dx_c * dx_c)
        else:
            # Square angled pier matching Gym01Normal exact camera perspective!
            if not is_back:
                if nx < col_x0 + ret_w:
                    shaft_c = c_mid  # Left protruding return side facing bottom-left camera!
                elif nx == col_x0 + ret_w:
                    shaft_c = c_spec  # Bright 1px architectural front corner crest!
                elif nx < col_x1:
                    shaft_c = c_lit
                else:
                    shaft_c = c_mid if w >= 9 else c_lit
            else:
                if nx == col_x0:
                    shaft_c = c_spec
                elif nx <= col_x1 - ret_w:
                    shaft_c = c_lit
                else:
                    shaft_c = c_mid  # Right depth return on back wall!
            base_drop = 1.0

        y_col_bot = int(round(wy + base_drop))
        y_collar = int(round(wall_y_from_h(nx, 0.68)))

        for ny in range(0, min(NH, y_col_bot + 1)):
            if upper_frieze and y_collar >= 1 and (y_collar - 1 <= ny <= y_collar + 1):
                # Protruding collar wrap strictly along perspective ray (h=0.68)!
                if ny == y_collar - 1:
                    rgb[ny][nx] = cap_hi if t_x < 0.72 else cap_dk
                elif ny == y_collar:
                    rgb[ny][nx] = cap_hi if t_x < 0.45 else cap_dk
                else:
                    rgb[ny][nx] = shade_col(cap_dk, 0.82)
            elif upper_frieze and y_collar >= 1 and ny == y_collar + 2:
                rgb[ny][nx] = shade_col(shaft_c, 0.78)  # Subtle under-collar neck shadow
            elif ny >= y_col_bot - 2:
                # Perspective-sloped stepped base plinth following wy cleanly (NO flat box!)
                if ny == y_col_bot - 2:
                    rgb[ny][nx] = cap_hi if t_x < 0.70 else cap_dk
                elif ny == y_col_bot - 1:
                    rgb[ny][nx] = cap_dk
                else:
                    rgb[ny][nx] = shade_col(cap_dk, 0.65)
            else:
                rgb[ny][nx] = shaft_c

        # Clean floor contact shadow right below curved base
        if y_col_bot + 1 < NH:
            rgb[y_col_bot + 1][nx] = shade_col(rgb[y_col_bot + 1][nx], 0.74)


def draw_clean_banner(
    rgb,
    x0: int,
    x1: int,
    h0_bot: float,
    h1_top: float,
    main_hi: tuple[int, int, int],
    main_dk: tuple[int, int, int],
    trim_col: tuple[int, int, int],
    out_col: tuple[int, int, int],
    emblem: str = "crown",
):
    """Volumetric plumb-vertical banner with 3D rod, wall mounting brackets, cast shadow & uniform 1px edge!"""
    cx = (x0 + x1) * 0.5
    half_w = (x1 - x0) * 0.5
    pix: dict[tuple[int, int], tuple[int, int, int]] = {}
    trim_dk = shade_col(trim_col, 0.68)

    for nx in range(max(0, x0 - 2), min(NW, x1 + 3)):
        wy = wall_floor_y(nx)
        y_rod = max(4, int(round(wy - h1_top * (wy - VP_WY if nx <= CORNER_X else 41.0))))
        y_base_center = int(round(wy - h0_bot * (wy - VP_WY if nx <= CORNER_X else 41.0)))
        dx_abs = abs(nx - cx)
        # 3D Rod + rounded end finials protruding 2px wider than cloth
        if dx_abs <= half_w + 1.8 and 3 <= y_rod < wy - 4:
            is_fin = dx_abs > half_w + 0.3
            pix[(nx, y_rod)] = trim_col if nx <= cx else trim_dk
            if is_fin:
                pix[(nx, y_rod - 1)] = trim_col
        if dx_abs > half_w:
            continue
        v_bot = int(round(y_base_center - (half_w - dx_abs) * 0.42))
        h_in = v_bot - (y_rod + 1)
        for ny in range(y_rod + 1, min(int(wy) - 2, v_bot + 1)):
            if dx_abs >= half_w - 1.1 or ny == v_bot:
                pix[(nx, ny)] = trim_col if nx <= cx else trim_dk
            else:
                ty_b = (ny - (y_rod + 1)) / max(1.0, float(h_in))
                tx_b = (nx - x0) / max(1.0, float(x1 - x0))
                in_emb = False
                if h_in <= 10:
                    # Clean legible diamond/crest sigil for small back-wall banners (avoids cramped sub-pixel blobs!)
                    in_emb = abs(tx_b - 0.5) * 1.4 + abs(ty_b - 0.46) < 0.30
                elif emblem == "crown":
                    in_emb = (0.38 <= ty_b <= 0.56 and 0.25 <= tx_b <= 0.75) or (
                        0.23 <= ty_b < 0.38 and (abs(tx_b - 0.5) < 0.08 or abs(tx_b - 0.27) < 0.07 or abs(tx_b - 0.73) < 0.07)
                    )
                elif emblem == "cross":
                    in_emb = (abs(tx_b - 0.5) < 0.09 and 0.20 <= ty_b <= 0.72) or (abs(ty_b - 0.40) < 0.08 and 0.22 <= tx_b <= 0.78)
                if in_emb:
                    pix[(nx, ny)] = trim_col
                else:
                    pix[(nx, ny)] = main_dk if nx > cx + 1.0 else main_hi

    paint_1px_prop_buffer(rgb, pix, out_col, shadow_dx=2, shadow_dy=1, wall_only_shadow=True)


def draw_wall_panel_box(rgb, x0: int, x1: int, h0: float, h1: float, paint_fn):
    for nx in range(max(0, x0), min(NW, x1 + 1)):
        wy = wall_floor_y(nx)
        for ny in range(0, int(wy)):
            uw, hw, is_b = wall_uv(nx, ny)
            if h0 <= hw <= h1:
                tx = (nx - x0) / max(1.0, float(x1 - x0))
                ty = (hw - h0) / max(1e-4, h1 - h0)
                c = paint_fn(nx, ny, tx, ty, is_b)
                if c is not None:
                    rgb[ny][nx] = c


def draw_pokeball_emblem(
    rgb,
    top_col: tuple[int, int, int],
    bot_col: tuple[int, int, int],
    ring_col: tuple[int, int, int],
    center_fill: tuple[int, int, int],
    outer_rim_col: tuple[int, int, int] | None = None,
    cx: float = 120.0,
    cy: float = 113.5,
    rx: float = 49.0,
    ry: float = 15.5,
    gear: bool = False,
):
    """Uniform-thickness elliptical Pokeball court emblem (equal pixel border width on left/right/top/bottom!)."""
    if outer_rim_col is None:
        outer_rim_col = ring_col
    for ny in range(int(cy - ry - 4), int(cy + ry + 5)):
        for nx in range(int(cx - rx - 4), int(cx + rx + 5)):
            if not (0 <= nx < NW and 0 <= ny < NH):
                continue
            ym = court_mid_y(nx)
            nx_n = (nx - cx) / rx
            ny_n = (ny - cy) / ry
            d = math.hypot(nx_n, ny_n)
            # Analytical signed pixel distance to ellipse boundary (`d=1.0`)!
            grad = math.hypot(nx_n / rx, ny_n / ry)
            px_to_outer = (1.0 - d) / max(1e-4, grad)

            irx, iry = rx * 0.33, ry * 0.33
            inx_n = (nx - cx) / irx
            iny_n = (ny - cy) / iry
            di = math.hypot(inx_n, iny_n)
            igrad = math.hypot(inx_n / irx, iny_n / iry)
            px_to_inner = (1.0 - di) / max(1e-4, igrad)

            if gear and -2.2 <= px_to_outer <= 0.0:
                ang = math.atan2((ny - cy) * 3.1, nx - cx)
                if math.sin(ang * 12.0) > 0.35:
                    rgb[ny][nx] = outer_rim_col
                    continue
            if px_to_outer < -0.5:
                continue
            if px_to_inner >= 1.8:
                rgb[ny][nx] = center_fill
            elif px_to_inner >= -0.8:
                rgb[ny][nx] = ring_col
            elif px_to_outer <= 0.65:
                rgb[ny][nx] = outer_rim_col
            elif px_to_outer <= 2.2 or abs(ny - ym) <= 0.78:
                rgb[ny][nx] = ring_col
            elif ny < ym:
                rgb[ny][nx] = top_col
            else:
                rgb[ny][nx] = bot_col


def draw_door_base(rgb, frame_hi, frame_dk, void_col=(20, 18, 32), arch=False, wheel=False):
    frame_sh = shade_col(frame_hi, 0.68)
    for ny in range(8, 29):
        for nx in range(245, 256):
            if arch:
                dy = max(0.0, 14.0 - ny)
                dx = (nx - 252.0) / 3.6
                in_open = (ny >= 12) and (nx >= 249) and ((dy / 4.0) ** 2 + dx * dx <= 1.0 if ny < 15 else True)
                in_frame = (ny >= 10) and (nx >= 247) and ((max(0.0, 15.0 - ny) / 5.5) ** 2 + ((nx - 252.0) / 5.2) ** 2 <= 1.0 if ny < 15 else True)
            else:
                in_open = (12 <= ny <= 27) and (249 <= nx <= 255)
                in_frame = (10 <= ny <= 28) and (247 <= nx <= 255)
            if in_open:
                rgb[ny][nx] = void_col
            elif in_frame:
                if wheel and 17 <= ny <= 23 and 250 <= nx <= 254:
                    dw = math.hypot(nx - 252, ny - 20)
                    if 1.1 <= dw <= 2.3 or nx == 252 or ny == 20:
                        rgb[ny][nx] = frame_hi
                    else:
                        rgb[ny][nx] = (46, 54, 68)
                else:
                    rgb[ny][nx] = frame_sh if (nx == 247 and ny >= 14) or ny == 28 else frame_hi


def save_2x2(rgb: list[list[tuple[int, int, int]]], name: str, label: str, thumb_collect: list):
    im = Image.new("RGB", (NW, NH))
    px = im.load()
    for ny in range(NH):
        for nx in range(NW):
            px[nx, ny] = rgb[ny][nx]
    out_im = im.resize((NW * 2, NH * 2), Image.Resampling.NEAREST)
    out_path = BB_DIR / f"battlebg{name}.png"
    out_im.save(out_path)
    thumb_collect.append((name, label, out_im.convert("RGBA")))


def build_sheet(thumbs: list, out_path: Path):
    tw, th = 420, 315
    pad, hdr = 14, 24
    cols_n = 2
    rows_n = math.ceil(len(thumbs) / cols_n)
    W = cols_n * tw + (cols_n + 1) * pad
    H = rows_n * (th + hdr) + (rows_n + 1) * pad
    sheet = Image.new("RGBA", (W, H), (22, 24, 30, 255))
    draw = ImageDraw.Draw(sheet)
    for idx, (name, label, im_full) in enumerate(thumbs):
        r, c = idx // cols_n, idx % cols_n
        x0 = pad + c * (tw + pad)
        y0 = pad + r * (th + hdr + pad)
        draw.text((x0 + 2, y0 + 2), label, fill=(238, 224, 178, 255))
        t_im = im_full.resize((tw, th), Image.Resampling.NEAREST)
        sheet.alpha_composite(t_im, (x0, y0 + hdr))
    sheet.save(out_path)
