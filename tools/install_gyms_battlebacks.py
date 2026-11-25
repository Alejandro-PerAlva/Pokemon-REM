"""Generate and install v4 Gym Battlebacks (Gym02Water..Gym08Fire, 512x384, strict 2x2).

Upgrades v4:
  - Architectural volume matching battlebgGym01Normal.png camera projection & clean bevel separation
  - True 3D protruding foreground props with visible top/side planes, 3/4 perspective,
    wall & floor cast shadows, and uniform 1-native-pixel contours via `paint_1px_prop_buffer`
  - Uniform-width elliptical Pokeball court rings & zero flat 2D wall stickers
"""

import math
from stadium_core import (
    NW,
    NH,
    CORNER_X,
    PREV_DIR,
    COLS,
    clamp,
    shade_col,
    wall_floor_y,
    wall_stripe_y,
    wall_y_from_h,
    wall_uv,
    court_mid_y,
    FLOOR_UV,
    compute_grid_cells,
    floor_surface_light,
    is_standard_court_line,
    paint_1px_prop_buffer,
    draw_3d_box_prop,
    apply_wall_architectural_volume,
    draw_volumetric_column,
    draw_wall_panel_box,
    draw_pokeball_emblem,
    draw_door_base,
    save_2x2,
    build_sheet,
)


# ---------------------------------------------------------------------------
# GYM 02 WATER - Ismael (Piscina olímpica: escaleras 3D, tabla en caballete, salvavidas)
# ---------------------------------------------------------------------------
def build_gym02_water() -> list[list[tuple[int, int, int]]]:
    rgb = [[(0, 0, 0)] * NW for _ in range(NH)]
    WALL_TOP = (176, 208, 236)
    WALL_A = (158, 194, 226)
    WALL_B = (146, 182, 216)
    GROUT = (118, 154, 194)
    STRIPE_HI = (92, 168, 238)
    STRIPE_MID = (48, 114, 204)
    STRIPE_DK = (34, 82, 156)

    DECK_LIGHT = (148, 226, 238)
    DECK_MID = (124, 208, 226)
    DECK_SHAD = (102, 186, 210)
    DECK_GROUT = (82, 162, 190)
    CURB_W = (244, 250, 254)
    CURB_SH = (182, 206, 222)

    POOL_HI = (78, 196, 234)
    POOL_MID = (46, 152, 210)
    POOL_DEEP = (28, 116, 180)
    FOAM = (224, 248, 255)
    OUT = (38, 58, 92)

    cells, edges = compute_grid_cells(2.6, 2.0)

    for nx in range(NW):
        wy = int(round(wall_floor_y(nx)))
        moat_bot = int(round(wy + 11.5))
        for ny in range(NH):
            if ny < wy:
                uw, hw, _ = wall_uv(nx, ny)
                row_t = math.floor(hw * 7.0)
                col_t = math.floor(uw * 1.45)
                fh = hw * 7.0 - row_t
                fu = uw * 1.45 - col_t
                if fh < 0.13 or fu < 0.11:
                    rgb[ny][nx] = GROUT
                else:
                    rgb[ny][nx] = WALL_TOP if hw > 0.30 else (WALL_A if (row_t + col_t) % 2 == 0 else WALL_B)
            elif ny < moat_bot:
                if ny <= wy + 1:
                    rgb[ny][nx] = (30, 82, 140)
                elif ny >= moat_bot - 3:
                    rgb[ny][nx] = (44, 96, 148) if ny == moat_bot - 1 else (CURB_W if ny == moat_bot - 3 else CURB_SH)
                else:
                    u, v = FLOOR_UV[ny][nx]
                    w_band = math.sin(u * 2.8 + v * 3.5)
                    if ny == wy + 2 and w_band > 0.25:
                        rgb[ny][nx] = FOAM
                    elif w_band > 0.35:
                        rgb[ny][nx] = POOL_HI
                    elif w_band > -0.35:
                        rgb[ny][nx] = POOL_MID
                    else:
                        rgb[ny][nx] = POOL_DEEP
            else:
                if edges[ny][nx]:
                    rgb[ny][nx] = DECK_GROUT
                else:
                    p = floor_surface_light(nx, ny)
                    rgb[ny][nx] = DECK_LIGHT if p > 0.57 else (DECK_MID if p > 0.42 else DECK_SHAD)

    apply_wall_architectural_volume(
        rgb, CURB_W, CURB_SH, STRIPE_HI, STRIPE_MID, STRIPE_DK, CURB_W, CURB_SH, OUT,
        recess_upper=True, upper_frieze=False,
    )

    for nx in range(NW):
        for ny in range(int(wall_floor_y(nx) + 11.5), NH):
            if is_standard_court_line(nx, ny, inset=11.5):
                rgb[ny][nx] = CURB_W

    draw_pokeball_emblem(rgb, CURB_W, (36, 128, 214), (164, 190, 210), DECK_MID, outer_rim_col=OUT)

    # 3D Chrome Pool Ladders arching over the curb down into the water moat (`nx=84, 222`)
    for lx in (84, 222):
        wy_l = int(round(wall_floor_y(lx)))
        mb = wy_l + 11
        pix_lad: dict[tuple[int, int], tuple[int, int, int]] = {}
        # Two perspective-offset arched rails curving UP and BACK over the white pool curb
        for rx_off, depth_dx in [(0, 0), (8, -2)]:
            rx_front = lx + rx_off
            rx_back = rx_front + depth_dx
            # Submerged/vertical front rail rising out of pool curb (`mb-9 .. mb-1`)
            for py in range(mb - 9, mb - 1):
                pix_lad[(rx_front, py)] = (242, 248, 255)
            # Top curved grab loop retreating onto deck behind rail
            pix_lad[(rx_front + (0 if depth_dx >= 0 else -1), mb - 10)] = (242, 248, 255)
            pix_lad[(rx_back, mb - 10)] = (176, 206, 228)
            pix_lad[(rx_back, mb - 9)] = (138, 170, 196)
            pix_lad[(rx_back, mb - 8)] = (98, 132, 162)
        # Beveled horizontal chrome treads receding slightly right/up
        for ty in (mb - 7, mb - 4):
            for px in range(lx + 1, lx + 8):
                pix_lad[(px, ty)] = (224, 238, 250)
        paint_1px_prop_buffer(rgb, pix_lad, OUT, shadow_dx=2, shadow_dy=1)

    # Volumetric Cylindrical Lighthouse Pillars + 3D Torus Lifebuoys (strict 1px outline)
    for c0, c1, _ in COLS:
        draw_volumetric_column(
            rgb, c0, c1,
            (252, 254, 255), (236, 242, 248), (192, 206, 222), (144, 162, 184),
            OUT, style="cylinder", cap_hi=(232, 82, 82), cap_dk=(148, 46, 52), upper_frieze=False,
        )
        for nx in range(c0, c1 + 1):
            wy = int(round(wall_floor_y(nx)))
            t_x = (nx - c0) / max(1.0, float(c1 - c0))
            for ny in range(2, wy - 3):
                # Red lighthouse bands follow perspective stripe angle slightly!
                hw_band = (wy - ny) / max(10.0, wy + 15.0)
                if int(math.floor(hw_band * 6.5)) % 2 == 1:
                    if t_x < 0.36:
                        rgb[ny][nx] = (244, 114, 114)
                    elif t_x < 0.72:
                        rgb[ny][nx] = (218, 68, 74)
                    else:
                        rgb[ny][nx] = (148, 46, 54)
        if c0 in (125, 205):
            bx = (c0 + c1) // 2
            by = int(round(wall_floor_y(bx))) - 10
            pix_buoy: dict[tuple[int, int], tuple[int, int, int]] = {}
            for py in range(by - 4, by + 5):
                for px in range(bx - 3, bx + 4):
                    d = math.hypot((px - bx) * 1.15, py - by)
                    if 1.3 <= d <= 3.6:
                        q = (abs(px - bx) > abs(py - by))
                        col_b = (244, 114, 52) if q else (252, 252, 254)
                        if px > bx + 1 or py > by + 1:
                            col_b = shade_col(col_b, 0.74)
                        pix_buoy[(px, py)] = col_b
            paint_1px_prop_buffer(rgb, pix_buoy, OUT, shadow_dx=1, shadow_dy=1, wall_only_shadow=True)

    # 3D Surfboard leaning on Teak A-Frame Stand in Corner Alcove (`nx=156..172`)
    pix_surf: dict[tuple[int, int], tuple[int, int, int]] = {}
    # Teak rack rear support leg & deck cross-rail first
    for px in range(158, 171):
        pix_surf[(px, 28)] = (128, 84, 48)
    for py in range(24, 30):
        pix_surf[(160, py)] = (148, 98, 56)
        pix_surf[(168, py)] = (98, 62, 34)
    # Tilted surfboard body with visible 3D right fiberglass depth rail + gold nose stripe
    for py in range(6, 28):
        cx_s = 165.0 - (28 - py) * 0.36
        t_s = max(0.0, min(1.0, (py - 6) / 22.0))
        w_s = 3.8 * math.sin(t_s * math.pi * 0.88 + 0.14)
        for px in range(int(round(cx_s - w_s)), int(round(cx_s + w_s)) + 1):
            dx = px - cx_s
            if dx > w_s - 1.1:
                pix_surf[(px, py)] = (182, 128, 36)  # 3D Shaded Right Edge Rail!
            elif abs(dx) < 0.75:
                pix_surf[(px, py)] = (42, 134, 224)  # Center racing stripe
            elif dx < -0.5:
                pix_surf[(px, py)] = (254, 222, 86)  # Lit wax top deck
            else:
                pix_surf[(px, py)] = (236, 182, 54)
    paint_1px_prop_buffer(rgb, pix_surf, (46, 36, 28), shadow_dx=2, shadow_dy=1)

    draw_door_base(rgb, (238, 248, 255), OUT, void_col=(20, 32, 54), arch=True)
    return rgb


# ---------------------------------------------------------------------------
# GYM 03 STEEL - Greta (Acería naval 3D: engranajes extruidos, cilindros con válvula, yunque 3/4)
# ---------------------------------------------------------------------------
def build_gym03_steel() -> list[list[tuple[int, int, int]]]:
    rgb = [[(0, 0, 0)] * NW for _ in range(NH)]
    WALL_HI = (106, 118, 132)
    WALL_MID = (86, 98, 112)
    WALL_SH = (70, 80, 94)
    HAZ_Y = (234, 186, 56)
    HAZ_D = (42, 46, 54)

    FLOOR_A = (138, 148, 160)
    FLOOR_B = (126, 136, 148)
    FLOOR_C = (116, 126, 138)
    SEAM_DK = (76, 84, 96)
    IRON_HI = (168, 180, 194)
    IRON_LIT = (128, 140, 154)
    IRON_MID = (84, 94, 108)
    IRON_DARK = (46, 52, 62)
    OUT = (28, 32, 40)

    cells, edges = compute_grid_cells(1.4, 1.3)

    for nx in range(NW):
        wy = int(round(wall_floor_y(nx)))
        for ny in range(NH):
            if ny < wy:
                uw, hw, _ = wall_uv(nx, ny)
                panel_b = int(math.floor(uw * 1.4))
                seam = abs(uw * 1.4 - round(uw * 1.4)) < 0.06
                if seam:
                    rgb[ny][nx] = WALL_SH
                else:
                    rgb[ny][nx] = WALL_HI if hw > 0.31 else (WALL_MID if panel_b % 2 == 0 else WALL_SH)
            else:
                if edges[ny][nx]:
                    rgb[ny][nx] = SEAM_DK
                else:
                    p = floor_surface_light(nx, ny)
                    iu, iv = cells[ny][nx]
                    base = FLOOR_A if ((iu + iv) % 2 == 0) else FLOOR_B
                    rgb[ny][nx] = FLOOR_C if p < 0.35 else base
                    u, v = FLOOR_UV[ny][nx]
                    fu, fv = (u * 1.4) % 1.0, (v * 1.3) % 1.0
                    if (0.08 < fu < 0.14 or 0.86 < fu < 0.92) and (0.10 < fv < 0.16 or 0.84 < fv < 0.90):
                        rgb[ny][nx] = SEAM_DK

    apply_wall_architectural_volume(
        rgb, IRON_HI, IRON_DARK, HAZ_Y, (186, 144, 44), IRON_DARK, IRON_LIT, IRON_DARK, OUT,
        recess_upper=True, upper_frieze=True,
    )
    for nx in range(NW):
        sy = wall_stripe_y(nx)
        y_top_l, y_bot_l = int(round(sy - 1.5)), int(round(sy + 1.5))
        uw, _, _ = wall_uv(nx, sy)
        for ny in range(max(2, y_top_l), min(int(wall_floor_y(nx)) - 2, y_bot_l)):
            chev = int(math.floor(uw * 2.6 + (ny - y_top_l) * 0.45)) % 2 == 0
            rgb[ny][nx] = HAZ_Y if chev else HAZ_D

    for nx in range(NW):
        for ny in range(int(wall_floor_y(nx)), NH):
            if is_standard_court_line(nx, ny):
                if abs(ny - court_mid_y(nx)) <= 1.0:
                    rgb[ny][nx] = HAZ_Y if ((nx // 6) % 2 == 0) else IRON_MID
                else:
                    rgb[ny][nx] = HAZ_Y if ((nx // 5) % 2 == 0) else HAZ_D

    draw_pokeball_emblem(rgb, (216, 224, 232), (222, 128, 44), IRON_MID, FLOOR_B, outer_rim_col=OUT, gear=True)

    for c0, c1, _ in COLS:
        draw_volumetric_column(rgb, c0, c1, IRON_HI, IRON_LIT, IRON_MID, IRON_DARK, OUT, style="pier", cap_hi=IRON_HI, cap_dk=IRON_DARK, upper_frieze=True)
        if c0 in (45, 125, 205):
            mid = (c0 + c1) // 2
            wy = int(round(wall_floor_y(mid)))
            for ny in range(4, wy - 4):
                for px in range(c0 + 3, c1 - 2):
                    rgb[ny][px] = IRON_MID if ny % 12 < 2 else IRON_DARK

    # Extruded 3D Perspective Gears mounted on Left Wall (thickness rim + axle hub + wall shadow!)
    for gcx, gcy, grx, gry, c_spec, c_hi, c_dk in [
        (83, 21, 5.8, 7.2, (236, 178, 92), (198, 136, 68), (118, 74, 34)),
        (96, 17, 4.2, 5.0, (210, 220, 232), IRON_HI, IRON_MID),
    ]:
        pix_g: dict[tuple[int, int], tuple[int, int, int]] = {}
        # First write extruded depth side body shifted (+2, +1) behind front face
        for dy_s in range(0, 2):
            for dx_s in range(1, 3):
                for py in range(int(gcy - gry - 2), int(gcy + gry + 3)):
                    for px in range(int(gcx - grx - 2), int(gcx + grx + 3)):
                        dys = (py - gcy) + (px - gcx) * 0.20
                        d = math.hypot((px - gcx) / grx, dys / gry)
                        ang = math.atan2(dys / gry, (px - gcx) / grx)
                        r_lim = 1.0 + (0.20 if math.sin(ang * 8.0) > 0.25 else 0.0)
                        if 0.30 <= d <= r_lim:
                            pix_g[(px + dx_s, py + dy_s)] = c_dk
        # Front lit gear face + central protruding axle nut
        for py in range(int(gcy - gry - 2), int(gcy + gry + 3)):
            for px in range(int(gcx - grx - 2), int(gcx + grx + 3)):
                dys = (py - gcy) + (px - gcx) * 0.20
                d = math.hypot((px - gcx) / grx, dys / gry)
                ang = math.atan2(dys / gry, (px - gcx) / grx)
                r_lim = 1.0 + (0.20 if math.sin(ang * 8.0) > 0.25 else 0.0)
                if 0.34 <= d <= r_lim:
                    pix_g[(px, py)] = c_spec if (px < gcx - 1 and py < gcy) else c_hi
                elif d < 0.28:
                    pix_g[(px, py)] = IRON_HI if px <= gcx else IRON_MID
        paint_1px_prop_buffer(rgb, pix_g, OUT, shadow_dx=2, shadow_dy=1, wall_only_shadow=True)

    # 3D Cylindrical Welding Tanks seated strictly on floor height wall_floor_y(cx) + Valve Guards!
    pix_tanks: dict[tuple[int, int], tuple[int, int, int]] = {}
    for cx_t, h_t, tc_hi, tc_mid, tc_dk in [
        (10, 25, (214, 78, 62), (168, 48, 42), (108, 30, 30)),
        (19, 20, (82, 154, 212), (48, 102, 156), (32, 68, 108)),
    ]:
        yb = min(65, int(round(wall_floor_y(cx_t))) + 1)
        yt = yb - h_t
        for py in range(yt, yb + 1):
            for px in range(cx_t - 3, cx_t + 4):
                dx = px - cx_t
                # Tapered dome shoulder near top + rounded bottom floor contact
                if py < yt + 3 and abs(dx) > (py - yt) + 1:
                    continue
                if py == yb and abs(dx) == 3:
                    continue
                if py <= yt + 1 and abs(dx) <= 1:
                    pix_tanks[(px, py)] = (232, 190, 76)
                elif py == yt + 3:
                    pix_tanks[(px, py)] = IRON_HI if dx <= 0 else IRON_DARK  # Metal collar band
                elif dx < -1:
                    pix_tanks[(px, py)] = tc_hi
                elif dx <= 1:
                    pix_tanks[(px, py)] = tc_mid
                else:
                    pix_tanks[(px, py)] = tc_dk
    paint_1px_prop_buffer(rgb, pix_tanks, OUT, shadow_dx=2, shadow_dy=1)

    # True 3/4 Perspective Steel Blacksmith Anvil on Stepped 3D Oak Stump (`nx=154..175`)
    pix_anv: dict[tuple[int, int], tuple[int, int, int]] = {}
    # Oak timber block (lit front x=158..168, shaded right side return x=169..172)
    draw_3d_box_prop(
        pix_anv, 158, 168, 24, 30,
        (152, 98, 56), (134, 84, 46), (88, 52, 30), (176, 120, 74),
        perspective_wall="corner", side_w=3, top_h=2,
    )
    # 3D Blacksmith Anvil atop stump (bright top angled face + dark front waist + shaded right heel return!)
    for px in range(154, 174):
        # Tapered conical horn (154..158), wide flat top anvil face (159..171), rear heel (172..173)
        if 154 <= px <= 158:
            # Conical horn pointing front-left
            t_h = (px - 154) / 4.0
            for py in range(int(round(18 - t_h)), int(round(19 + t_h * 0.8)) + 1):
                pix_anv[(px, py)] = IRON_HI if py == int(round(18 - t_h)) else IRON_MID
        elif 159 <= px <= 171:
            # Top angled anvil table (py=16..18 sloped slightly to reveal 3D top surface!)
            pix_anv[(px, 16)] = IRON_HI if px < 169 else IRON_LIT
            pix_anv[(px, 17)] = (196, 206, 218) if px < 168 else IRON_MID
            for py in range(18, 22):
                # Waist narrows at py=19..20
                if (19 <= py <= 20 and 160 <= px <= 167) or (py >= 21 and 158 <= px <= 169):
                    pix_anv[(px, py)] = IRON_LIT if px < 165 else IRON_DARK
                elif py == 18:
                    pix_anv[(px, py)] = IRON_MID if px < 166 else IRON_DARK
            # Foot base bevel (`py=22..23`) + right side return depth (`168..171`)
            for py in (22, 23):
                if 158 <= px <= 170:
                    pix_anv[(px, py)] = IRON_MID if px < 166 else IRON_DARK
        else:
            pix_anv[(px, 17)] = IRON_DARK
            pix_anv[(px, 18)] = IRON_DARK
    paint_1px_prop_buffer(rgb, pix_anv, OUT, shadow_dx=2, shadow_dy=1)

    draw_door_base(rgb, IRON_HI, OUT, void_col=(20, 24, 34), wheel=True)
    return rgb


# ---------------------------------------------------------------------------
# GYM 04 FIGHTING - Genzo (Dojo 3D: saco con soporte y sombra, armero 3/4, farol andon 3D)
# ---------------------------------------------------------------------------
def build_gym04_fighting() -> list[list[tuple[int, int, int]]]:
    rgb = [[(0, 0, 0)] * NW for _ in range(NH)]
    SHOJI_A = (242, 232, 208)
    SHOJI_B = (226, 214, 186)
    WOOD_SPEC = (176, 114, 66)
    WOOD_HI = (142, 88, 50)
    WOOD_L = (112, 68, 38)
    WOOD_D = (72, 42, 24)
    WOOD_OUT = (46, 26, 18)
    CRIMSON_HI = (206, 62, 56)
    CRIMSON_A = (176, 46, 44)
    CRIMSON_D = (124, 30, 30)

    TATAMI_A = (208, 190, 124)
    TATAMI_B = (194, 176, 110)
    TATAMI_C = (182, 164, 100)
    TATAMI_BIND = (44, 58, 88)
    APRON_WOOD = (146, 92, 54)
    APRON_SH = (114, 68, 40)
    CHALK = (246, 242, 230)

    for nx in range(NW):
        wy = int(round(wall_floor_y(nx)))
        for ny in range(NH):
            if ny < wy:
                uw, hw, _ = wall_uv(nx, ny)
                fu = abs(uw * 1.35 - round(uw * 1.35))
                fh = abs(hw * 6.4 - round(hw * 6.4))
                if fu < 0.13 or fh < 0.16:
                    rgb[ny][nx] = WOOD_L
                else:
                    rgb[ny][nx] = SHOJI_A if hw > 0.30 else SHOJI_B
            else:
                if ny <= wy + 7.5:
                    u, _ = FLOOR_UV[ny][nx]
                    plank = int(math.floor(u * 2.0)) % 2
                    rgb[ny][nx] = WOOD_D if ny >= wy + 6.8 else (APRON_WOOD if plank == 0 else APRON_SH)
                else:
                    u, v = FLOOR_UV[ny][nx]
                    rv = math.floor(v * 1.25)
                    cu = math.floor(u * 1.05 + (0.5 if rv % 2 else 0.0))
                    up, vp = FLOOR_UV[ny][max(0, nx - 1)]
                    rv_p = math.floor(vp * 1.25)
                    cu_p = math.floor(up * 1.05 + (0.5 if rv_p % 2 else 0.0))
                    uu, vu = FLOOR_UV[max(0, ny - 1)][nx]
                    rv_u = math.floor(vu * 1.25)
                    cu_u = math.floor(uu * 1.05 + (0.5 if rv_u % 2 else 0.0))
                    if (cu, rv) != (cu_p, rv_p) or (cu, rv) != (cu_u, rv_u):
                        rgb[ny][nx] = TATAMI_BIND
                    else:
                        p = floor_surface_light(nx, ny)
                        base = TATAMI_A if (cu + rv) % 2 == 0 else TATAMI_B
                        rgb[ny][nx] = TATAMI_C if p < 0.35 else base

    apply_wall_architectural_volume(
        rgb, WOOD_HI, WOOD_D, CRIMSON_HI, CRIMSON_A, CRIMSON_D, APRON_WOOD, WOOD_D, WOOD_OUT,
        recess_upper=True, upper_frieze=False,
    )

    for nx in range(NW):
        for ny in range(int(wall_floor_y(nx) + 7.5), NH):
            if is_standard_court_line(nx, ny, inset=7.5):
                rgb[ny][nx] = CHALK

    draw_pokeball_emblem(rgb, CHALK, CRIMSON_A, (226, 214, 186), TATAMI_A, outer_rim_col=WOOD_D)

    for c0, c1, _ in COLS:
        draw_volumetric_column(rgb, c0, c1, WOOD_SPEC, WOOD_HI, WOOD_L, WOOD_D, WOOD_OUT, style="pier", upper_frieze=False)

    # 3D Cylindrical Crimson Punching Bag suspended from Wall Iron Bracket + Cast Shoji Shadow!
    pix_bag: dict[tuple[int, int], tuple[int, int, int]] = {}
    # Projecting wrought-iron arm anchored into wall at (24, 5)
    for px in range(21, 25):
        pix_bag[(px, 6)] = (78, 84, 96)
    pix_bag[(23, 7)] = (58, 62, 74)
    pix_bag[(21, 7)] = (78, 84, 96)
    pix_bag[(21, 8)] = (58, 62, 74)
    pix_bag[(21, 9)] = (78, 84, 96)
    pix_bag[(21, 10)] = (58, 62, 74)
    # 3D Leather Cylinder Bag with curved elliptical top crown + brass straps + bottom seam
    for py in range(11, 41):
        half = 4 if py in (11, 40) else 5
        for px in range(21 - half, 21 + half + 1):
            dx = px - 21
            if py in (12, 13) and abs(dx) <= 4:
                pix_bag[(px, py)] = (214, 72, 62) if dx < 1 else CRIMSON_D
            elif py in (16, 36):
                pix_bag[(px, py)] = (234, 190, 74) if dx < 2 else (144, 108, 40)
            elif dx <= -2:
                pix_bag[(px, py)] = CRIMSON_HI
            elif dx <= 2:
                pix_bag[(px, py)] = CRIMSON_A
            else:
                pix_bag[(px, py)] = CRIMSON_D
    paint_1px_prop_buffer(rgb, pix_bag, WOOD_OUT, shadow_dx=3, shadow_dy=2, wall_only_shadow=True)

    # 3D Perspective Wooden Bo-Staff Stand + 3D Shoji Box Andon Lantern in Corner (`nx=152..176`)
    pix_dojo: dict[tuple[int, int], tuple[int, int, int]] = {}
    # Angled wooden trestle feet resting on floor apron + upright posts + back depth upright
    for py in range(11, 29):
        pix_dojo[(154, py)] = WOOD_HI
        pix_dojo[(164, py)] = WOOD_L
    # Forward projecting wooden feet (`29..30`) + receding back rail
    for fx in range(153, 157):
        pix_dojo[(fx, 29)] = WOOD_D
    for fx in range(163, 167):
        pix_dojo[(fx, 29)] = WOOD_D
    for py in (14, 24):
        for px in range(154, 165):
            pix_dojo[(px, py)] = WOOD_SPEC if py == 14 else WOOD_HI
    for sx, top_s in [(156, 7), (159, 6), (162, 7)]:
        for py in range(top_s, 28):
            pix_dojo[(sx, py)] = WOOD_SPEC if py % 3 == 0 else WOOD_HI

    # 3D Rectangular Wooden Andon Paper Lantern (`front plane 167..172 + right shaded return plane 173..174`)
    draw_3d_box_prop(
        pix_dojo, 167, 172, 16, 29,
        (255, 236, 164), (242, 214, 126), (194, 152, 82), WOOD_SPEC,
        perspective_wall="corner", side_w=2, top_h=1,
    )
    # Walnut corner framing posts & base sill on the lantern
    for py in range(16, 30):
        pix_dojo[(167, py)] = WOOD_L
        pix_dojo[(172, py)] = WOOD_D
    for px in range(167, 175):
        pix_dojo[(px, 27)] = WOOD_D
        pix_dojo[(px, 28)] = WOOD_D
    paint_1px_prop_buffer(rgb, pix_dojo, WOOD_OUT, shadow_dx=2, shadow_dy=1)

    # 3D Mounted Martial Calligraphy Scroll with Cylindrical Walnut Rollers & Cast Shadow (`nx=219..234`)
    pix_scr: dict[tuple[int, int], tuple[int, int, int]] = {}
    for ny in range(5, 16):
        is_rod = ny in (5, 15)
        x_lo, x_hi = (218, 235) if is_rod else (220, 233)
        for nx in range(x_lo, x_hi + 1):
            if is_rod:
                pix_scr[(nx, ny)] = (232, 224, 198) if nx in (218, 235) else (WOOD_HI if nx <= 228 else WOOD_D)
            elif ny in (6, 14):
                pix_scr[(nx, ny)] = CRIMSON_A if nx <= 228 else CRIMSON_D
            else:
                tx = (nx - 220) / 13.0
                ty = (ny - 6) / 8.0
                ink = (abs(tx - 0.5) < 0.09 and 0.22 <= ty <= 0.78) or (abs(ty - 0.45) < 0.11 and 0.25 <= tx <= 0.75)
                pix_scr[(nx, ny)] = (38, 30, 26) if ink else (246, 238, 214)
    paint_1px_prop_buffer(rgb, pix_scr, WOOD_OUT, shadow_dx=2, shadow_dy=1, wall_only_shadow=True)

    draw_door_base(rgb, WOOD_HI, WOOD_OUT, void_col=(24, 16, 16), arch=False)
    return rgb


# ---------------------------------------------------------------------------
# GYM 05 ROCK - Fausto (Vitrina 3D en esquina con cara lateral y tapa, cuarzo poliédrico)
# ---------------------------------------------------------------------------
def build_gym05_rock() -> list[list[tuple[int, int, int]]]:
    rgb = [[(0, 0, 0)] * NW for _ in range(NH)]
    WALL_SPEC = (138, 120, 102)
    WALL_HI = (118, 102, 86)
    WALL_MID = (94, 80, 68)
    WALL_DK = (68, 56, 48)
    MORTAR = (46, 38, 34)
    GOLD_HI = (244, 204, 94)
    GOLD_MID = (198, 154, 58)
    GOLD_DK = (128, 92, 34)

    SLAB_A = (208, 180, 136)
    SLAB_B = (194, 164, 120)
    SLAB_C = (178, 148, 106)
    GROUT_S = (138, 114, 82)
    OUT = (38, 30, 26)

    cells, edges = compute_grid_cells(1.35, 1.35)

    for nx in range(NW):
        wy = int(round(wall_floor_y(nx)))
        for ny in range(NH):
            if ny < wy:
                uw, hw, _ = wall_uv(nx, ny)
                row = math.floor(hw * 5.8)
                col = math.floor(uw * 1.15 + (0.5 if row % 2 else 0.0))
                fh = hw * 5.8 - row
                fu = (uw * 1.15 + (0.5 if row % 2 else 0.0)) - col
                if fh < 0.14 or fu < 0.09:
                    rgb[ny][nx] = MORTAR
                else:
                    h = ((col * 173 + row * 97) & 3)
                    rgb[ny][nx] = [WALL_HI, WALL_MID, WALL_DK, WALL_MID][h]
            else:
                if edges[ny][nx]:
                    rgb[ny][nx] = GROUT_S
                else:
                    p = floor_surface_light(nx, ny)
                    iu, iv = cells[ny][nx]
                    base = SLAB_A if ((iu + iv) % 2 == 0) else SLAB_B
                    u, v = FLOOR_UV[ny][nx]
                    vein = abs(math.sin(u * 1.4 + v * 1.9))
                    if vein < 0.045:
                        rgb[ny][nx] = (164, 136, 98)
                    elif p < 0.35:
                        rgb[ny][nx] = SLAB_C
                    else:
                        rgb[ny][nx] = base

    apply_wall_architectural_volume(
        rgb, WALL_SPEC, WALL_DK, GOLD_HI, GOLD_MID, GOLD_DK, GOLD_MID, GOLD_DK, OUT,
        recess_upper=True, upper_frieze=True,
    )

    for nx in range(NW):
        for ny in range(int(wall_floor_y(nx)), NH):
            if is_standard_court_line(nx, ny):
                rgb[ny][nx] = GOLD_HI

    draw_pokeball_emblem(rgb, (238, 224, 192), (174, 114, 60), GOLD_MID, SLAB_B, outer_rim_col=OUT)

    for c0, c1, _ in COLS:
        draw_volumetric_column(rgb, c0, c1, WALL_SPEC, WALL_HI, WALL_MID, WALL_DK, OUT, style="pier", cap_hi=GOLD_HI, cap_dk=GOLD_DK, upper_frieze=True)
        if c0 in (45, 125, 205):
            cx_c = (c0 + c1) // 2
            gy = int(round(wall_y_from_h(cx_c, 0.44)))
            gem_hi = (232, 68, 92) if c0 == 45 else (74, 214, 152)
            pix_gem: dict[tuple[int, int], tuple[int, int, int]] = {}
            for dy in (-2, -1, 0, 1, 2):
                for dx in (-1, 0, 1):
                    if abs(dx) + abs(dy) <= 2:
                        pix_gem[(cx_c + dx, gy + dy)] = (255, 220, 225) if (dx == 0 and dy == -1) else (GOLD_HI if dy < 0 else gem_hi)
            paint_1px_prop_buffer(rgb, pix_gem, OUT, shadow_dx=1, shadow_dy=1, wall_only_shadow=True)

    # True 3D Illuminated Glass Fossil Vitrine in Corner (`nx=152..176`, with receding right glass & wood return!)
    pix_vit: dict[tuple[int, int], tuple[int, int, int]] = {}
    # Bottom Mahogany & Gold Pedestal Box (`front x=153..170 + right shaded return x=171..174`)
    draw_3d_box_prop(
        pix_vit, 153, 170, 22, 30,
        (164, 44, 58), (138, 34, 46), (88, 22, 32), GOLD_HI,
        perspective_wall="corner", side_w=4, top_h=2,
    )
    # 3D Glass Display Hood above pedestal (`top tilted glass lid + lit front window + right receding teal side glass`)
    for px in range(154, 170):
        # Tilted top glass cover receding up-right (`py=5..6`)
        pix_vit[(px + 2, 5)] = (182, 228, 238)
        pix_vit[(px + 1, 6)] = (146, 204, 220)
        # Interior front glass wall (`py=7..20`) + Helix Fossil inside!
        for py in range(7, 21):
            if px in (154, 169):
                pix_vit[(px, py)] = GOLD_MID
            else:
                dx, dy = px - 161.5, py - 14.0
                r_f = math.hypot(dx, dy * 1.05)
                ang = math.atan2(dy, dx)
                is_fossil = (r_f <= 4.6) and (abs(math.sin(r_f * 1.35 + ang)) > 0.25 or r_f < 2.0)
                if is_fossil:
                    pix_vit[(px, py)] = (242, 224, 182) if (py < 14 and px < 163) else (178, 156, 114)
                else:
                    glint = abs((px - 157) + (py - 8)) <= 1
                    pix_vit[(px, py)] = (194, 236, 244) if glint else (58, 92, 108)
    # Shaded right-side receding glass return panel (`x=170..173, py=6..20`)
    for sx in range(170, 174):
        dy_s = -(sx - 170)
        for py in range(7 + dy_s, 21 + dy_s):
            pix_vit[(sx, py)] = GOLD_DK if sx == 173 else (46, 74, 90)
    paint_1px_prop_buffer(rgb, pix_vit, OUT, shadow_dx=2, shadow_dy=1)

    # Polyhedral Multi-Facet Quartz Crystal Cluster & Limestone Prisms (`nx=4..28`) via 1px contour
    pix_cryst: dict[tuple[int, int], tuple[int, int, int]] = {}
    for cx_r, top_r, hw, is_q in [(6, 45, 6.5, True), (15, 42, 7.5, False), (24, 48, 5.2, True)]:
        bot_r = min(65, int(round(wall_floor_y(cx_r))) + 1)
        for py in range(top_r, bot_r + 1):
            t_b = (py - top_r) / max(1.0, bot_r - top_r)
            span = max(1.0, (t_b * 0.85 + 0.15) * hw) if not is_q else max(1.0, t_b * hw)
            for px in range(max(0, int(round(cx_r - span))), min(NW, int(round(cx_r + span)) + 1)):
                dx = px - cx_r
                if is_q:
                    c_col = (248, 224, 146) if dx < -1.0 else ((214, 172, 92) if dx <= 1.2 else (142, 104, 46))
                else:
                    c_col = (176, 156, 128) if dx < -1.0 else ((134, 114, 92) if dx <= 1.5 else (86, 72, 60))
                pix_cryst[(px, py)] = c_col
    paint_1px_prop_buffer(rgb, pix_cryst, OUT, shadow_dx=2, shadow_dy=1)

    draw_door_base(rgb, GOLD_HI, OUT, void_col=(24, 20, 22), arch=True)
    return rgb


# ---------------------------------------------------------------------------
# GYM 06 GRASS - Hildegarda (Invernadero: cesta 3D con suelo/cadenas, maceta estilo Gym01)
# ---------------------------------------------------------------------------
def build_gym06_grass() -> list[list[tuple[int, int, int]]]:
    rgb = [[(0, 0, 0)] * NW for _ in range(NH)]
    GLASS_HI = (178, 228, 188)
    GLASS_MID = (146, 204, 158)
    FOL_BG = (86, 152, 94)
    MUNTIN = (92, 66, 44)
    WOOD_SPEC = (176, 126, 76)
    WOOD_L = (138, 96, 56)
    WOOD_D = (84, 56, 34)
    SAGE_HI = (94, 174, 92)
    SAGE_TRIM = (76, 148, 78)
    SAGE_DK = (48, 102, 54)

    TURF_HI = (134, 204, 112)
    TURF_MID = (114, 186, 94)
    TURF_SH = (98, 166, 82)
    STONE_CURB = (212, 206, 184)
    STONE_SH = (164, 156, 134)
    CREAM_LINE = (244, 240, 218)
    OUT = (38, 42, 32)

    cells, _ = compute_grid_cells(1.6, 1.4)

    for nx in range(NW):
        wy = int(round(wall_floor_y(nx)))
        for ny in range(NH):
            if ny < wy:
                uw, hw, _ = wall_uv(nx, ny)
                if hw > 0.31:
                    fu = abs(uw * 1.35 - round(uw * 1.35))
                    fh = abs(hw * 4.2 - round(hw * 4.2))
                    if fu < 0.12 or fh < 0.14:
                        rgb[ny][nx] = MUNTIN
                    else:
                        hill = 0.44 + 0.08 * math.sin(uw * 1.8) + 0.04 * math.sin(uw * 4.2)
                        rgb[ny][nx] = FOL_BG if hw < hill else (GLASS_HI if hw > 0.68 else GLASS_MID)
                else:
                    rgb[ny][nx] = WOOD_L if (int(math.floor(uw * 2.0)) % 2 == 0) else WOOD_D
            else:
                if ny <= wy + 6.5:
                    if ny >= wy + 5.8:
                        rgb[ny][nx] = SAGE_DK
                    else:
                        u, _ = FLOOR_UV[ny][nx]
                        rgb[ny][nx] = STONE_CURB if (math.floor(u * 2.2) % 2 == 0) else STONE_SH
                else:
                    iu, _ = cells[ny][nx]
                    p = floor_surface_light(nx, ny)
                    base = TURF_HI if (iu % 2 == 0) else TURF_MID
                    rgb[ny][nx] = TURF_SH if p < 0.34 else base

    apply_wall_architectural_volume(
        rgb, MUNTIN, OUT, SAGE_HI, SAGE_TRIM, SAGE_DK, STONE_CURB, STONE_SH, OUT,
        recess_upper=True, upper_frieze=False,
    )

    for nx in range(NW):
        for ny in range(int(wall_floor_y(nx) + 6.5), NH):
            if is_standard_court_line(nx, ny, inset=6.5):
                rgb[ny][nx] = CREAM_LINE

    draw_pokeball_emblem(rgb, CREAM_LINE, (62, 152, 72), STONE_SH, TURF_MID, outer_rim_col=(42, 84, 46))

    for c0, c1, _ in COLS:
        draw_volumetric_column(rgb, c0, c1, WOOD_SPEC, WOOD_L, (108, 72, 42), WOOD_D, OUT, style="cylinder", cap_hi=MUNTIN, cap_dk=OUT, upper_frieze=False)
        for nx in range(c0, c1 + 1):
            wy = int(round(wall_floor_y(nx)))
            for ny in range(3, wy - 3):
                vine_y = ((nx - c0) * 1.3 + ny * 0.45) % 9.5
                if vine_y < 3.0:
                    fl = ((nx + ny) % 11 == 0)
                    rgb[ny][nx] = (248, 128, 160) if fl else ((88, 182, 86) if vine_y < 1.8 else (48, 114, 54))

    # 3D Hanging Wicker Flower Basket on 3 Chains (`nx=92..110`) with Wall Shadow!
    pix_bask: dict[tuple[int, int], tuple[int, int, int]] = {}
    for py in range(1, 11):
        t_c = (10 - py) / 9.0
        for cx_c in (int(round(101 - 4 * t_c)), 101, int(round(101 + 4 * t_c))):
            pix_bask[(cx_c, py)] = (96, 84, 72)
    # Tapered cylindrical wicker pot with curved 3D rim + foliage clusters + pink blossoms
    for py in range(11, 19):
        if py <= 13:
            w_b = 5.5
            for px in range(int(round(101 - w_b)), int(round(101 + w_b)) + 1):
                pix_bask[(px, py)] = (206, 146, 86) if px < 102 else (148, 98, 52)
        else:
            w_b = max(1.5, 5.2 - (py - 13) * 0.72)
            for px in range(int(round(101 - w_b)), int(round(101 + w_b)) + 1):
                pix_bask[(px, py)] = (176, 118, 66) if px <= 101 else (122, 78, 42)
    for py in range(7, 13):
        for px in range(94, 109):
            d = math.hypot((px - 101) * 0.72, py - 10.2)
            if d < 4.8:
                is_r = (px in (98, 102, 105) and py in (9, 11)) or (px == 100 and py == 8)
                pix_bask[(px, py)] = (250, 124, 162) if is_r else ((96, 192, 92) if (py < 10 and px < 103) else (48, 116, 52))
    paint_1px_prop_buffer(rgb, pix_bask, OUT, shadow_dx=2, shadow_dy=1, wall_only_shadow=True)

    # 3D Cylindrical Terracotta Pot (elliptical rim + soil + topiary shrub clusters just like Gym01Normal!)
    pix_top: dict[tuple[int, int], tuple[int, int, int]] = {}
    for py in range(21, 31):
        half_w = 5 if py <= 24 else 4
        for px in range(164 - half_w, 164 + half_w + 1):
            dx = px - 164
            if py == 21:
                pix_top[(px, py)] = (212, 114, 76) if abs(dx) >= 3 else (94, 72, 56)  # Soil oval opening!
            elif py == 22:
                pix_top[(px, py)] = (224, 126, 84) if dx <= 1 else (142, 68, 44)  # Elliptical front rim lip!
            elif py == 23:
                pix_top[(px, py)] = (168, 82, 52) if dx <= 1 else (112, 52, 34)  # Under-rim shadow
            else:
                pix_top[(px, py)] = (196, 98, 62) if dx < -1 else ((162, 78, 50) if dx <= 1 else (114, 54, 36))
    # Sculpted 3D spherical topiary bush with clustered sunlit & shaded foliage lobes
    for py in range(9, 22):
        for px in range(157, 172):
            d = math.hypot((px - 164) * 0.78, py - 15.0)
            if d < 5.5 and py <= 21:
                is_bl = (px in (160, 167) and py in (13, 16)) or (px == 164 and py == 11)
                if is_bl:
                    pix_top[(px, py)] = (250, 122, 158)
                elif px < 165 and py < 16:
                    pix_top[(px, py)] = (104, 198, 98)
                elif d < 3.6:
                    pix_top[(px, py)] = (74, 158, 74)
                else:
                    pix_top[(px, py)] = (44, 108, 50)
    paint_1px_prop_buffer(rgb, pix_top, (56, 36, 26), shadow_dx=2, shadow_dy=1)

    for fx, fy, fcol in [(10, 61, (252, 214, 88)), (22, 58, (246, 116, 156)), (34, 55, (252, 214, 88)), (230, 31, (246, 116, 156))]:
        pix_fl: dict[tuple[int, int], tuple[int, int, int]] = {}
        for oy in (-1, 0, 1):
            for ox in (-2, -1, 0, 1, 2):
                if abs(ox) + abs(oy) <= 2:
                    pix_fl[(fx + ox, fy + oy)] = (46, 114, 52) if oy >= 1 else fcol
        pix_fl[(fx, fy - 1)] = (255, 246, 212)
        paint_1px_prop_buffer(rgb, pix_fl, (36, 48, 30), shadow_dx=1, shadow_dy=1)

    draw_door_base(rgb, WOOD_L, OUT, void_col=(20, 32, 22), arch=True)
    return rgb


# ---------------------------------------------------------------------------
# GYM 07 ICE - Isolda (Salón helado: araña cristal 3D, fuente hexagonal 3D, reflejos suaves)
# ---------------------------------------------------------------------------
def build_gym07_ice() -> list[list[tuple[int, int, int]]]:
    rgb = [[(0, 0, 0)] * NW for _ in range(NH)]
    WALL_TOP = (172, 202, 234)
    WALL_A = (158, 190, 224)
    WALL_PAN = (140, 174, 212)
    SILVER_HI = (238, 246, 254)
    SILVER_DK = (94, 128, 168)

    ICE_HI = (206, 238, 252)
    ICE_MID = (178, 224, 246)
    ICE_SH = (150, 204, 232)
    LINE_ICE = (248, 252, 255)
    ALAB_SPEC = (250, 253, 255)
    ALAB_HI = (232, 244, 254)
    ALAB_MID = (188, 218, 246)
    ALAB_DK = (128, 166, 206)
    OUT = (52, 74, 108)

    cells, edges = compute_grid_cells(1.25, 1.25)

    for nx in range(NW):
        wy = int(round(wall_floor_y(nx)))
        for ny in range(NH):
            if ny < wy:
                uw, hw, _ = wall_uv(nx, ny)
                fu = uw * 0.85 - math.floor(uw * 0.85)
                in_pan = (0.18 < fu < 0.82) and (0.36 < hw < 0.65)
                rgb[ny][nx] = WALL_PAN if in_pan else (WALL_TOP if hw > 0.30 else WALL_A)
            else:
                if edges[ny][nx]:
                    rgb[ny][nx] = (136, 186, 220)
                else:
                    p = floor_surface_light(nx, ny)
                    base_c = ICE_HI if p > 0.56 else (ICE_MID if p > 0.38 else ICE_SH)
                    refl_t = max(0.0, 1.0 - max(0, ny - wy) / 68.0)
                    refl_w = 4.2 * refl_t
                    in_col_refl = refl_w > 0.6 and any(abs((nx - ny * 0.12) - cx_c) < refl_w for cx_c in (48, 126, 204))
                    if in_col_refl:
                        rgb[ny][nx] = shade_col(base_c, 1.0, (int(28 * refl_t), int(20 * refl_t), int(10 * refl_t)))
                    else:
                        rgb[ny][nx] = base_c
                    if abs((nx * 0.55 + ny) - 185) < 5 or abs((nx * 0.55 + ny) - 235) < 3:
                        rgb[ny][nx] = shade_col(rgb[ny][nx], 1.0, (14, 10, 6))

    apply_wall_architectural_volume(
        rgb, SILVER_HI, SILVER_DK, SILVER_HI, (132, 182, 232), SILVER_DK, SILVER_HI, SILVER_DK, OUT,
        recess_upper=True, upper_frieze=True,
    )

    for nx in range(NW):
        for ny in range(int(wall_floor_y(nx)), NH):
            if is_standard_court_line(nx, ny):
                rgb[ny][nx] = LINE_ICE

    draw_pokeball_emblem(rgb, LINE_ICE, (74, 166, 228), SILVER_DK, ICE_HI, outer_rim_col=OUT)

    for c0, c1, _ in COLS:
        draw_volumetric_column(rgb, c0, c1, ALAB_SPEC, ALAB_HI, ALAB_MID, ALAB_DK, OUT, style="cylinder", fluted=True, upper_frieze=True)

    # Faceted Icicles hanging ONLY beneath the true-perspective upper cornice beam (nx=4..122, zero flat bar!)
    for ix in range(6, 120, 9):
        if any(c0 - 2 <= ix <= c1 + 2 for c0, c1, _ in COLS):
            continue
        y0_ice = int(round(wall_y_from_h(ix, 0.68))) + 1
        if y0_ice < 2:
            continue
        ilen = 4 if ix < 65 else 3
        pix_ic: dict[tuple[int, int], tuple[int, int, int]] = {}
        for dy in range(ilen):
            pix_ic[(ix, y0_ice + dy)] = ALAB_HI if dy < 2 else (126, 198, 242)
            if dy < ilen - 1:
                pix_ic[(ix + 1, y0_ice + dy)] = ALAB_MID
        paint_1px_prop_buffer(rgb, pix_ic, OUT, shadow_dx=1, shadow_dy=1, wall_only_shadow=True)

    # Solid Cohesive 3D Crystal Chandelier suspended in front of Left Wall Bay (`nx=80..102, y=2..21`)
    pix_chand: dict[tuple[int, int], tuple[int, int, int]] = {}
    for py in range(1, 8):
        pix_chand[(91, py)] = SILVER_DK
    # Upper crown ring
    for px in range(86, 97):
        pix_chand[(px, 8)] = SILVER_HI if px <= 91 else SILVER_DK
    # Central faceted ice shaft (`8..16`) + bottom pendant prism (`17..20`)
    for py in range(9, 20):
        w_p = 1 if py < 16 else max(0, 19 - py)
        for px in range(91 - w_p, 91 + w_p + 1):
            pix_chand[(px, py)] = (196, 236, 255) if py < 16 else (120, 204, 248)
    # 3D elliptical lower ring (front bar curved 1px lower than rear sides + 5 warm candles!)
    for px in range(81, 102):
        dx_c = (px - 91) / 10.0
        y_ring = int(round(12.0 + (1.0 - dx_c * dx_c) * 1.6))
        pix_chand[(px, y_ring)] = ALAB_SPEC if px < 92 else SILVER_DK
        pix_chand[(px, y_ring - 1)] = (98, 178, 228) if abs(px - 91) % 4 == 0 else SILVER_HI
    for cx_b in (82, 86, 91, 96, 100):
        dx_c = (cx_b - 91) / 10.0
        yb_c = int(round(11.0 + (1.0 - dx_c * dx_c) * 1.4))
        pix_chand[(cx_b, yb_c - 1)] = ALAB_SPEC
        pix_chand[(cx_b, yb_c - 2)] = (255, 246, 194)
        pix_chand[(cx_b, yb_c + 2)] = (126, 208, 250)  # Hanging crystal drops below ring
    paint_1px_prop_buffer(rgb, pix_chand, OUT, shadow_dx=2, shadow_dy=1, wall_only_shadow=True)

    # 3D Hexagonal Sculpted Ice Fountain in Corner Alcove (`nx=156..174`, elliptical bowl + water + shadow!)
    pix_fnt: dict[tuple[int, int], tuple[int, int, int]] = {}
    # Pedestal octagonal column (`y=21..29`)
    draw_3d_box_prop(
        pix_fnt, 161, 167, 22, 29,
        ALAB_HI, ALAB_MID, ALAB_DK, ALAB_SPEC, perspective_wall="corner", side_w=2, top_h=1,
    )
    # Flared 3D elliptical upper ice basin (`y=15..21`) showing translucent water surface oval inside
    for py in range(16, 22):
        for px in range(157, 173):
            d_bowl = math.hypot((px - 164.5) / 7.2, (py - 17.5) / 2.6)
            if d_bowl <= 1.0:
                if py <= 18 and d_bowl < 0.72:
                    pix_fnt[(px, py)] = (102, 198, 248)  # Water pool surface oval!
                elif py <= 18:
                    pix_fnt[(px, py)] = ALAB_SPEC  # Lit inner ice rim
                elif px <= 165:
                    pix_fnt[(px, py)] = ALAB_HI
                else:
                    pix_fnt[(px, py)] = ALAB_DK
    # Central spire + cascading frozen water jet plumes
    for py in range(11, 18):
        pix_fnt[(164, py)] = ALAB_SPEC
        pix_fnt[(165, py)] = ALAB_MID
    pix_fnt[(162, 13)] = (224, 248, 255)
    pix_fnt[(167, 13)] = (224, 248, 255)
    paint_1px_prop_buffer(rgb, pix_fnt, OUT, shadow_dx=2, shadow_dy=1)

    draw_door_base(rgb, ALAB_HI, OUT, void_col=(24, 34, 58), arch=True)
    return rgb


# ---------------------------------------------------------------------------
# GYM 08 FIRE - Beltrán (Cocina termal 3D: campana con fondo 3D, olla cobre con sopa y vapor)
# ---------------------------------------------------------------------------
def build_gym08_fire() -> list[list[tuple[int, int, int]]]:
    rgb = [[(0, 0, 0)] * NW for _ in range(NH)]
    WALL_HI = (84, 72, 74)
    WALL_MID = (66, 56, 58)
    WALL_DK = (48, 40, 44)
    MORTAR_F = (30, 24, 28)
    EMBER_HI = (248, 162, 54)
    EMBER_RED = (218, 72, 38)
    BRASS_SPEC = (242, 186, 108)
    BRASS_HI = (206, 144, 76)
    BRASS_MID = (162, 102, 52)
    BRASS_DK = (108, 64, 34)
    STEEL_HOOD = (146, 154, 168)
    STEEL_HOOD_LIT = (176, 186, 198)
    STEEL_HOOD_DK = (76, 84, 96)

    SLATE_A = (88, 78, 80)
    SLATE_B = (76, 68, 70)
    SLATE_C = (64, 56, 58)
    GROUT_D = (42, 34, 38)
    OUT = (28, 22, 24)

    cells, edges = compute_grid_cells(1.4, 1.4)

    for nx in range(NW):
        wy = int(round(wall_floor_y(nx)))
        trench_bot = int(round(wy + 6.5))
        for ny in range(NH):
            if ny < wy:
                uw, hw, _ = wall_uv(nx, ny)
                row = math.floor(hw * 6.0)
                col = math.floor(uw * 1.3 + (0.5 if row % 2 else 0.0))
                fh = hw * 6.0 - row
                fu = (uw * 1.3 + (0.5 if row % 2 else 0.0)) - col
                if fh < 0.14 or fu < 0.09:
                    rgb[ny][nx] = MORTAR_F
                else:
                    rgb[ny][nx] = WALL_HI if hw > 0.30 else (WALL_MID if (row + col) % 2 == 0 else WALL_DK)
            elif ny < trench_bot:
                u, _ = FLOOR_UV[ny][nx]
                if ny >= trench_bot - 2:
                    rgb[ny][nx] = STEEL_HOOD_DK if ny == trench_bot - 2 else (36, 30, 34)
                else:
                    phase_u = (u * 2.2) % 1.0
                    if phase_u < 0.24 or ny <= wy + 1:
                        rgb[ny][nx] = (42, 38, 44)
                    else:
                        rgb[ny][nx] = (248, 198, 74) if ny == wy + 2 else ((234, 104, 38) if ny == wy + 3 else (172, 46, 28))
            else:
                if edges[ny][nx]:
                    rgb[ny][nx] = GROUT_D
                else:
                    p = floor_surface_light(nx, ny)
                    iu, iv = cells[ny][nx]
                    base = SLATE_A if ((iu + iv) % 2 == 0) else SLATE_B
                    rgb[ny][nx] = SLATE_C if p < 0.34 else base

    apply_wall_architectural_volume(
        rgb, BRASS_HI, MORTAR_F, EMBER_HI, EMBER_RED, BRASS_DK, BRASS_MID, OUT, OUT,
        recess_upper=True, upper_frieze=False,
    )

    for nx in range(NW):
        for ny in range(int(wall_floor_y(nx) + 6.5), NH):
            if is_standard_court_line(nx, ny, inset=6.5):
                rgb[ny][nx] = EMBER_HI if abs(ny - court_mid_y(nx)) <= 1.2 else EMBER_RED

    draw_pokeball_emblem(rgb, (226, 74, 42), (48, 42, 46), EMBER_HI, SLATE_B, outer_rim_col=OUT)

    for c0, c1, _ in COLS:
        draw_volumetric_column(rgb, c0, c1, BRASS_SPEC, BRASS_HI, BRASS_MID, BRASS_DK, OUT, style="cylinder", upper_frieze=False)
        if c0 in (45, 125, 205):
            cx_c = (c0 + c1) // 2
            sy_c = int(round(wall_y_from_h(cx_c, 0.44)))
            pix_lan: dict[tuple[int, int], tuple[int, int, int]] = {}
            for dy in (-2, -1, 0, 1, 2):
                for dx in (-1, 0, 1):
                    if dy in (-2, 2):
                        pix_lan[(cx_c + dx, sy_c + dy)] = STEEL_HOOD_DK
                    else:
                        pix_lan[(cx_c + dx, sy_c + dy)] = (254, 224, 98) if dx == 0 else EMBER_RED
            paint_1px_prop_buffer(rgb, pix_lan, OUT, shadow_dx=1, shadow_dy=1, wall_only_shadow=True)

    # True 3D Extruded Stainless Extractor Hood on Left Wall (`nx=74..104`) following wall perspective!
    pix_hood: dict[tuple[int, int], tuple[int, int, int]] = {}
    # Vertical chimney duct with receding right shadow return (`px=84..94`)
    for px in range(84, 94):
        y_hood_top = int(round(wall_y_from_h(px, 0.56)))
        for py in range(0, y_hood_top):
            pix_hood[(px, py)] = STEEL_HOOD_LIT if px < 89 else (STEEL_HOOD if px < 92 else STEEL_HOOD_DK)
    # Flared 3D canopy pyramid aligned along wall slope + dark underside recessed intake cavity!
    for px in range(74, 104):
        t_x = (px - 74) / 30.0
        y_top_c = int(round(wall_y_from_h(px, 0.57)))
        y_bot_c = int(round(wall_y_from_h(px, 0.37)))
        # Slope narrows at top to chimney (`t_x in 0.33..0.67`), wide along canopy rim (`t_x in 0..1`)
        in_x_hi = 0.32 <= t_x <= 0.68
        for py in range(y_top_c, y_bot_c + 1):
            ty_c = (py - y_top_c) / max(1.0, float(y_bot_c - y_top_c))
            x_half = 0.18 + ty_c * 0.32
            if abs(t_x - 0.50) <= x_half:
                if py >= y_bot_c - 1:
                    pix_hood[(px, py)] = (38, 42, 50) if 0.12 < t_x < 0.88 else STEEL_HOOD  # Recessed intake underside!
                elif py == y_bot_c - 2:
                    pix_hood[(px, py)] = STEEL_HOOD_LIT
                elif t_x < 0.58:
                    pix_hood[(px, py)] = STEEL_HOOD_LIT if ty_c < 0.4 else STEEL_HOOD
                else:
                    pix_hood[(px, py)] = STEEL_HOOD_DK  # Right angled receding side wing!
    paint_1px_prop_buffer(rgb, pix_hood, OUT, shadow_dx=3, shadow_dy=2, wall_only_shadow=True)

    # Stove burner rail & glowing pilot jets right underneath the hood rim
    for jx in (80, 88, 96):
        jy = int(round(wall_stripe_y(jx))) - 2
        rgb[jy][jx] = EMBER_RED
        rgb[jy - 1][jx] = EMBER_HI
        rgb[jy - 2][jx] = (254, 232, 118)

    # 3D Hammered Copper Cauldron / Stockpot with Soup Rim, Handles & Steam (`nx=156..173`)
    pix_pot: dict[tuple[int, int], tuple[int, int, int]] = {}
    for py in range(18, 30):
        half_p = 5 if py <= 27 else 4
        for px in range(165 - half_p, 165 + half_p + 1):
            dx = px - 165
            if py == 18:
                pix_pot[(px, py)] = BRASS_SPEC if abs(dx) >= 4 else (228, 134, 62)  # Bubbling soup oval top!
            elif py == 19:
                pix_pot[(px, py)] = BRASS_HI if dx <= 2 else BRASS_DK  # Brass rolled front rim!
            elif py == 21 and abs(dx) == 5:
                continue
            elif dx < -1:
                pix_pot[(px, py)] = BRASS_SPEC if dx == -3 else BRASS_HI
            elif dx <= 1:
                pix_pot[(px, py)] = BRASS_MID
            else:
                pix_pot[(px, py)] = BRASS_DK
        # Left/Right 3D Loop Brass Handles (`y=20..22`)
        if py in (20, 21):
            pix_pot[(159, py)] = BRASS_HI
            pix_pot[(171, py)] = BRASS_DK
    paint_1px_prop_buffer(rgb, pix_pot, OUT, shadow_dx=2, shadow_dy=1)

    # Cohesive smooth 2-wisp steam ribbons curling softly above stockpot
    for py, sx in [(15, 163), (14, 164), (13, 164), (12, 163), (15, 167), (14, 168), (13, 167)]:
        rgb[py][sx] = (208, 218, 226) if py >= 14 else (178, 188, 198)

    # 3D Hanging Copper Skillets on Iron Rack (`nx=218..240`, cast shadows + angled pan rims!)
    pix_pans: dict[tuple[int, int], tuple[int, int, int]] = {}
    for px in range(219, 239):
        pix_pans[(px, 6)] = STEEL_HOOD_DK
    for px_pan in (223, 229, 235):
        for py in range(6, 13):
            if py <= 9:
                pix_pans[(px_pan, py)] = STEEL_HOOD
            else:
                for ox in (-2, -1, 0, 1, 2):
                    if math.hypot(ox * 0.9, py - 11.0) <= 2.3:
                        pix_pans[(px_pan + ox, py)] = BRASS_SPEC if ox == -1 else (BRASS_HI if ox <= 0 else BRASS_DK)
    paint_1px_prop_buffer(rgb, pix_pans, OUT, shadow_dx=2, shadow_dy=1, wall_only_shadow=True)

    draw_door_base(rgb, STEEL_HOOD, OUT, void_col=(28, 18, 16), wheel=True)
    return rgb


def main():
    thumbs_b1, thumbs_b2 = [], []
    b1_specs = [
        ("Gym02Water", "Gym 02 - Agua (Ismael)", build_gym02_water),
        ("Gym03Steel", "Gym 03 - Acero (Greta)", build_gym03_steel),
        ("Gym04Fighting", "Gym 04 - Lucha (Genzo)", build_gym04_fighting),
        ("Gym05Rock", "Gym 05 - Roca (Fausto)", build_gym05_rock),
    ]
    b2_specs = [
        ("Gym06Grass", "Gym 06 - Planta (Hildegarda)", build_gym06_grass),
        ("Gym07Ice", "Gym 07 - Hielo (Isolda)", build_gym07_ice),
        ("Gym08Fire", "Gym 08 - Fuego (Beltran)", build_gym08_fire),
    ]
    for name, label, fn in b1_specs:
        save_2x2(fn(), name, label, thumbs_b1)
    for name, label, fn in b2_specs:
        save_2x2(fn(), name, label, thumbs_b2)

    build_sheet(thumbs_b1, PREV_DIR / "gyms_batch1_review.png")
    build_sheet(thumbs_b2, PREV_DIR / "gyms_batch2_review.png")
    print("Installed refined v4 Gym Battlebacks (Gym02Water..Gym08Fire) cleanly.")


if __name__ == "__main__":
    main()
