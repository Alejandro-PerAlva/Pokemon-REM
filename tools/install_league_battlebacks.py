"""Generate and install v4 Elite Four + Champion Stadium Battlebacks (512x384, strict 2x2).

Upgrades v4:
  - Architectural volume matching battlebgGym01Normal.png perspective, lighting & clean bevel separation
  - Every protruding object in front of the wall renders with 3D front/top/side planes, wall & floor cast shadows,
    and strictly uniform 1-native-pixel contours via `paint_1px_prop_buffer`
  - Consistent vanishing-point alignment for beams, wall niches, banners, floating gaps & monuments
"""

import math
from PIL import Image, ImageDraw
from stadium_core import (
    NW,
    NH,
    CORNER_X,
    PREV_DIR,
    COLS,
    clamp,
    shade_col,
    fbm,
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
    draw_clean_banner,
    draw_pokeball_emblem,
    draw_door_base,
    save_2x2,
    build_sheet,
)


# ---------------------------------------------------------------------------
# ELITE A - Nicodemo (Bicho: Colmena ambarina 3D, faroles con brazo, altar escarabajo)
# ---------------------------------------------------------------------------
def build_elite_a_bug() -> list[list[tuple[int, int, int]]]:
    rgb = [[(0, 0, 0)] * NW for _ in range(NH)]
    GLASS_HI = (232, 188, 96)
    GLASS_MID = (206, 160, 74)
    GLASS_SH = (180, 134, 58)
    OAK_HI = (134, 92, 54)
    OAK_MID = (104, 68, 38)
    OAK_DK = (70, 44, 24)
    LEAF_T = (76, 150, 74)
    LEAF_L = (102, 178, 92)
    LEAF_D = (46, 98, 48)

    HEX_HI = (206, 166, 94)
    HEX_MID = (194, 154, 84)
    HEX_SH = (180, 142, 76)
    HEX_GROUT = (142, 102, 52)
    MOSS_APRON = (64, 118, 58)
    MOSS_DK = (42, 82, 42)
    CREAM_L = (242, 232, 188)
    OUT = (42, 28, 20)

    parquet_id = [[(0, 0)] * NW for _ in range(NH)]
    for ny in range(NH):
        for nx in range(NW):
            u, v = FLOOR_UV[ny][nx]
            rv = math.floor(v * 1.45)
            cu = math.floor(u * 1.30 + (0.5 if rv % 2 else 0.0))
            parquet_id[ny][nx] = (cu, rv)

    for nx in range(NW):
        wy = int(round(wall_floor_y(nx)))
        for ny in range(NH):
            if ny < wy:
                uw, hw, _ = wall_uv(nx, ny)
                row_c = math.floor(hw * 5.2)
                fh = hw * 5.2 - row_c
                u_off = uw * 1.45 + (0.5 if row_c % 2 else 0.0)
                col_c = math.floor(u_off)
                fu = u_off - col_c
                if hw > 0.34:
                    if fh < 0.13 or fu < 0.10:
                        rgb[ny][nx] = OAK_DK
                    elif fh > 0.78:
                        rgb[ny][nx] = GLASS_HI
                    elif (row_c + col_c) % 2 == 0:
                        rgb[ny][nx] = GLASS_MID
                    else:
                        rgb[ny][nx] = GLASS_SH
                else:
                    plank = int(math.floor(uw * 1.6)) % 2
                    rgb[ny][nx] = OAK_MID if plank == 0 else OAK_HI
            else:
                if ny <= wy + 5.5:
                    if ny >= wy + 4.8:
                        rgb[ny][nx] = MOSS_DK
                    elif ny <= wy + 1.5:
                        rgb[ny][nx] = LEAF_T
                    else:
                        rgb[ny][nx] = MOSS_APRON
                else:
                    cu, rv = parquet_id[ny][nx]
                    is_seam = (
                        parquet_id[ny][max(0, nx - 1)] != (cu, rv)
                        or parquet_id[max(0, ny - 1)][nx] != (cu, rv)
                    )
                    if is_seam:
                        rgb[ny][nx] = HEX_GROUT
                    else:
                        p = floor_surface_light(nx, ny)
                        base = HEX_HI if (cu + rv) % 2 == 0 else HEX_MID
                        rgb[ny][nx] = HEX_SH if p < 0.35 else base

    apply_wall_architectural_volume(
        rgb, (162, 114, 66), OAK_DK, LEAF_L, LEAF_T, LEAF_D, OAK_HI, OAK_DK, OUT,
        recess_upper=True, upper_frieze=False,
    )

    for nx in range(NW):
        for ny in range(int(wall_floor_y(nx) + 5.5), NH):
            if is_standard_court_line(nx, ny, inset=5.5):
                rgb[ny][nx] = CREAM_L if abs(ny - court_mid_y(nx)) <= 1.1 else LEAF_T

    draw_pokeball_emblem(rgb, (238, 198, 92), (76, 154, 72), CREAM_L, HEX_MID, outer_rim_col=OUT)

    for c0, c1, _ in COLS:
        draw_volumetric_column(
            rgb, c0, c1,
            (188, 138, 76), OAK_HI, OAK_MID, OAK_DK, OUT,
            style="cylinder", cap_hi=(238, 198, 92), cap_dk=OAK_DK, upper_frieze=False,
        )

    # Subtle translucent geometric silk corner webs stretched softly behind column junctions
    SILK = (224, 218, 194)
    for ax, side, span in [(58, 1, 10), (212, 1, 9)]:
        y0 = 2
        for step in range(1, span + 1):
            px_d, py_d = ax + side * step, y0 + step
            if 2 <= py_d < 15 and 0 <= px_d < NW:
                rgb[py_d][px_d] = SILK
        for rad in (4.5, 8.5):
            steps = int(rad * 3)
            for k in range(steps + 1):
                t = k / float(steps)
                if t <= 0.5:
                    u = t * 2.0
                    px, py = ax + side * (rad * (1.0 - 0.30 * u)), y0 + (rad * 0.70 * u)
                else:
                    u = (t - 0.5) * 2.0
                    px, py = ax + side * (rad * 0.70 * (1.0 - u)), y0 + rad * (0.70 + 0.30 * u)
                ipx, ipy = int(round(px)), int(round(py))
                if 2 <= ipy < 15 and 0 <= ipx < NW:
                    rgb[ipy][ipx] = SILK

    # 3D Suspended Amber Silk-Cocoon Lanterns on Wrought Oak Brackets (`nx=88, 226`) with Wall Shadow!
    for lx, ly0 in [(88, 6), (226, 4)]:
        pix_l: dict[tuple[int, int], tuple[int, int, int]] = {}
        for py in range(1, ly0):
            pix_l[(lx, py)] = OAK_DK
        # Wooden cap & ribbed elliptical cocoon glowing amber from center outward
        for px in range(lx - 1, lx + 2):
            pix_l[(px, ly0)] = OAK_HI if px <= lx else OAK_DK
        for py in range(ly0 + 1, ly0 + 10):
            for px in range(lx - 3, lx + 4):
                d = math.hypot((px - lx) * 1.15, (py - (ly0 + 5)) * 0.78)
                if d <= 3.1:
                    if py == ly0 + 4 or py == ly0 + 6:
                        pix_l[(px, py)] = (212, 162, 62) if px >= lx else (246, 214, 114)  # Silk rib hoops
                    elif px < lx and py < ly0 + 5:
                        pix_l[(px, py)] = (254, 244, 178)
                    elif px > lx + 1:
                        pix_l[(px, py)] = (182, 134, 48)
                    else:
                        pix_l[(px, py)] = (238, 198, 92)
        paint_1px_prop_buffer(rgb, pix_l, OUT, shadow_dx=2, shadow_dy=1, wall_only_shadow=True)

    # 3D Sculpted Golden Stag-Beetle Trophy on Stepped Moss-and-Oak Pedestal (`nx=156..174`)
    pix_btl: dict[tuple[int, int], tuple[int, int, int]] = {}
    draw_3d_box_prop(
        pix_btl, 159, 168, 23, 29,
        OAK_HI, OAK_MID, OAK_DK, MOSS_APRON, perspective_wall="corner", side_w=3, top_h=2,
    )
    # 3D Golden Stag-Beetle upright with open horn mandibles, emerald eyes, domed carapace & right shade
    for py in range(10, 22):
        for px in range(160, 170):
            dx = abs(px - 164.5)
            if 10 <= py <= 13 and 1.2 <= dx <= 3.2:
                pix_btl[(px, py)] = (252, 222, 124) if px <= 165 else (178, 126, 48)
            elif 14 <= py <= 21 and dx <= 3.6:
                if py in (14, 15) and 1.4 <= dx <= 2.4:
                    pix_btl[(px, py)] = (104, 218, 134)
                elif px < 164:
                    pix_btl[(px, py)] = (248, 206, 94)
                elif px <= 165:
                    pix_btl[(px, py)] = (218, 166, 68)
                else:
                    pix_btl[(px, py)] = (158, 108, 42)
    paint_1px_prop_buffer(rgb, pix_btl, OUT, shadow_dx=2, shadow_dy=1)

    draw_door_base(rgb, (226, 178, 86), OUT, void_col=(24, 20, 14), arch=True)
    return rgb


# ---------------------------------------------------------------------------
# ELITE B - Oriana (Psíquico: Cristales 3D multifaceta, medallones relievo, pilares partidos)
# ---------------------------------------------------------------------------
def build_elite_b_psychic() -> list[list[tuple[int, int, int]]]:
    rgb = [[(0, 0, 0)] * NW for _ in range(NH)]
    WALL_A = (54, 44, 96)
    WALL_B = (44, 36, 82)
    ASTRAL_HI = (232, 188, 255)
    ASTRAL_LILAC = (188, 118, 238)
    ASTRAL_MAG = (232, 98, 198)
    ASTRAL_DK = (96, 46, 138)

    FLOOR_A = (92, 74, 142)
    FLOOR_B = (80, 64, 128)
    FLOOR_C = (68, 54, 112)
    GROUT_P = (48, 36, 86)
    GLYPH_HI = (224, 182, 255)
    OUT = (28, 18, 52)

    cells, edges = compute_grid_cells(1.3, 1.3)

    for nx in range(NW):
        wy = int(round(wall_floor_y(nx)))
        for ny in range(NH):
            if ny < wy:
                uw, hw, _ = wall_uv(nx, ny)
                if hw > 0.34:
                    col_p = math.floor(uw * 1.15)
                    fu = uw * 1.15 - col_p
                    rgb[ny][nx] = WALL_B if fu < 0.08 or (col_p % 2 == 1) else WALL_A
                else:
                    rgb[ny][nx] = WALL_B
            else:
                if edges[ny][nx]:
                    rgb[ny][nx] = GROUT_P
                else:
                    p = floor_surface_light(nx, ny)
                    iu, iv = cells[ny][nx]
                    base = FLOOR_A if ((iu + iv) % 2 == 0) else FLOOR_B
                    rgb[ny][nx] = FLOOR_C if p < 0.34 else base

    apply_wall_architectural_volume(
        rgb, (132, 108, 184), OUT, ASTRAL_HI, ASTRAL_LILAC, ASTRAL_DK, ASTRAL_LILAC, OUT, OUT,
        recess_upper=True, upper_frieze=False,
    )

    for nx in range(NW):
        for ny in range(int(wall_floor_y(nx)), NH):
            if is_standard_court_line(nx, ny):
                rgb[ny][nx] = GLYPH_HI
            d_outer = math.hypot((nx - 120.0) / 62.0, (ny - 113.5) / 20.5)
            if 0.97 <= d_outer <= 1.015:
                rgb[ny][nx] = ASTRAL_MAG if abs(d_outer - 1.0) < 0.012 else ASTRAL_LILAC
            for gx, gy in [(42, 74), (206, 52)]:
                dg = math.hypot((nx - gx) / 11.0, (ny - gy) / 4.0)
                if 0.87 <= dg <= 1.02:
                    rgb[ny][nx] = ASTRAL_LILAC

    draw_pokeball_emblem(rgb, (238, 222, 252), ASTRAL_MAG, GLYPH_HI, FLOOR_A, outer_rim_col=ASTRAL_LILAC)

    # Relief 3D Gold-Bezel Astrolabe Mirrors mounted with Depth Rim + Cast Wall Shadow (`nx=26, 227`)!
    for mcx, mcy, rx_m, ry_m in [(26, 25, 6.2, 8.2), (227, 8, 4.4, 4.6)]:
        pix_med: dict[tuple[int, int], tuple[int, int, int]] = {}
        # Extruded depth rim behind right side (+1px)
        for py in range(int(mcy - ry_m - 1), int(mcy + ry_m + 2)):
            for px in range(int(mcx - rx_m - 1), int(mcx + rx_m + 2)):
                dys = (py - mcy) + ((px - mcx) * 0.22 if mcx < CORNER_X else 0.0)
                if math.hypot((px - mcx) / rx_m, dys / ry_m) <= 1.0:
                    pix_med[(px + 1, py + 1)] = (144, 102, 42)
        for py in range(int(mcy - ry_m - 1), int(mcy + ry_m + 2)):
            for px in range(int(mcx - rx_m - 1), int(mcx + rx_m + 2)):
                dys = (py - mcy) + ((px - mcx) * 0.22 if mcx < CORNER_X else 0.0)
                dm = math.hypot((px - mcx) / rx_m, dys / ry_m)
                if dm <= 1.0:
                    if dm >= 0.72:
                        pix_med[(px, py)] = (248, 216, 126) if px <= mcx else (182, 134, 52)
                    elif dm <= 0.34:
                        pix_med[(px, py)] = (255, 226, 255) if px <= mcx else ASTRAL_MAG
                    else:
                        pix_med[(px, py)] = ASTRAL_LILAC if px <= mcx else ASTRAL_DK
        paint_1px_prop_buffer(rgb, pix_med, OUT, shadow_dx=2, shadow_dy=1, wall_only_shadow=True)

    # Volumetric Cylindrical Obsidian & Amethyst Pillars split along exact perspective ray `hw=0.38`!
    for c0, c1, _ in COLS:
        draw_volumetric_column(
            rgb, c0, c1,
            (168, 134, 216), (116, 86, 174), (74, 52, 124), (42, 28, 78),
            OUT, style="cylinder", cap_hi=ASTRAL_LILAC, cap_dk=OUT, upper_frieze=False,
        )
        for nx in range(c0, c1 + 1):
            gap_y = int(round(wall_y_from_h(nx, 0.38)))
            if gap_y > 4:
                for ny in range(gap_y - 2, gap_y + 3):
                    if ny == gap_y:
                        rgb[ny][nx] = (255, 228, 255) if (c0 < nx < c1) else ASTRAL_MAG
                    elif abs(ny - gap_y) == 1:
                        rgb[ny][nx] = ASTRAL_MAG if (c0 < nx < c1) else OUT
                    else:
                        rgb[ny][nx] = OUT

    # Cast dark floor ellipses beneath floating 3D crystal obelisks (`nx=88, 164`)
    for sx, sy, srad in [(89, 48, 5), (165, 30, 5)]:
        for py in range(sy - 1, sy + 2):
            for px in range(sx - srad, sx + srad + 1):
                if abs(px - sx) / float(srad) + abs(py - sy) * 0.5 < 1.0 and 0 <= py < NH:
                    rgb[py][px] = shade_col(rgb[py][px], 0.64)

    # True 3D Hexagonal Faceted Crystal Obelisks (bright left bevel, lit front, shaded right bevel, wall shadows!)
    for fcx, fcy, h_c, w_c in [(88, 23, 7, 3.6), (164, 15, 9, 4.4), (173, 20, 5, 2.8)]:
        pix_cr: dict[tuple[int, int], tuple[int, int, int]] = {}
        for py in range(fcy - h_c, fcy + h_c + 1):
            for px in range(int(fcx - w_c - 1), int(fcx + w_c + 2)):
                d_dia = abs(px - fcx) / w_c + abs(py - fcy) / float(h_c)
                if d_dia <= 1.0:
                    dx = px - fcx
                    if dx <= -1.2:
                        pix_cr[(px, py)] = (255, 228, 255)  # Left lit crystal facet
                    elif dx <= 0.8:
                        pix_cr[(px, py)] = ASTRAL_MAG if py <= fcy + 1 else (196, 68, 178)  # Front prism facet
                    else:
                        pix_cr[(px, py)] = (138, 42, 146)  # Dark right prism facet
        paint_1px_prop_buffer(rgb, pix_cr, OUT, shadow_dx=2, shadow_dy=1, wall_only_shadow=True)

    draw_door_base(rgb, GLYPH_HI, OUT, void_col=(18, 12, 34), arch=True)
    return rgb


# ---------------------------------------------------------------------------
# ELITE C - Anteo (Siniestro: antorchas 3D, estandartes con sombra y luna 3D sobre plinto)
# ---------------------------------------------------------------------------
def build_elite_c_dark() -> list[list[tuple[int, int, int]]]:
    rgb = [[(0, 0, 0)] * NW for _ in range(NH)]
    WALL_A = (40, 38, 54)
    WALL_B = (32, 30, 44)
    CRIM_HI = (204, 52, 74)
    CRIM_MID = (154, 34, 56)
    CRIM_DK = (96, 20, 36)
    STEEL_HI = (146, 152, 176)
    STEEL_DK = (68, 70, 92)
    VIO_FIRE = (168, 92, 232)

    OBSID_A = (62, 60, 76)
    OBSID_B = (50, 48, 64)
    OBSID_C = (38, 36, 50)
    OBSID_LINE = (146, 152, 176)
    OUT = (18, 16, 26)

    cells, edges = compute_grid_cells(1.15, 1.05, rotate45=True)

    for nx in range(NW):
        wy = int(round(wall_floor_y(nx)))
        for ny in range(NH):
            if ny < wy:
                uw, hw, _ = wall_uv(nx, ny)
                row_b = math.floor(hw * 4.5)
                col_b = math.floor(uw * 1.15 + (0.5 if row_b % 2 else 0.0))
                fh = hw * 4.5 - row_b
                fu = (uw * 1.15 + (0.5 if row_b % 2 else 0.0)) - col_b
                if fh < 0.12 or fu < 0.10:
                    rgb[ny][nx] = (24, 22, 34)
                else:
                    rgb[ny][nx] = WALL_A if (row_b + col_b) % 2 == 0 else WALL_B
            else:
                if edges[ny][nx]:
                    rgb[ny][nx] = OUT
                else:
                    p = floor_surface_light(nx, ny)
                    iu, iv = cells[ny][nx]
                    base = OBSID_A if ((iu + iv) % 2 == 0) else OBSID_B
                    rgb[ny][nx] = OBSID_C if p < 0.36 else base
                if abs((nx * 0.65 - ny) - 55) < 9 or abs((nx * 0.65 - ny) - 115) < 7:
                    rgb[ny][nx] = shade_col(rgb[ny][nx], 1.0, (12, 14, 22))

    apply_wall_architectural_volume(
        rgb, STEEL_HI, STEEL_DK, CRIM_HI, CRIM_MID, CRIM_DK, CRIM_MID, OUT, OUT,
        recess_upper=True, upper_frieze=True,
    )

    for nx in range(NW):
        for ny in range(int(wall_floor_y(nx)), NH):
            if is_standard_court_line(nx, ny):
                rgb[ny][nx] = OBSID_LINE if abs(ny - court_mid_y(nx)) <= 1.2 else CRIM_HI

    draw_pokeball_emblem(rgb, CRIM_HI, OBSID_B, OBSID_LINE, OBSID_A, outer_rim_col=OUT)

    for c0, c1, _ in COLS:
        draw_volumetric_column(
            rgb, c0, c1,
            (116, 118, 144), (78, 76, 102), (50, 48, 68), (28, 26, 42),
            OUT, style="cylinder", cap_hi=STEEL_HI, cap_dk=STEEL_DK, upper_frieze=True,
        )

    # Volumetric Vertical Banners mounted cleanly below slanting perspective beam
    for bx0, bx1, h_top in [(80, 94, 0.63), (221, 232, 0.56)]:
        draw_clean_banner(rgb, bx0, bx1, 0.36, h_top, CRIM_HI, CRIM_DK, STEEL_HI, OUT, emblem="cross")

    # 3D Projecting Wrought-Iron Torch Brazier Sconces (`nx=66, 144`) with Violet Flame & Wall Shadow!
    for tx, ty in [(66, 22), (144, 14)]:
        pix_sc: dict[tuple[int, int], tuple[int, int, int]] = {}
        # Flared 3D iron torch cup (`py=ty..ty+2`) + bracket tang down to wall mount (`py+3..py+4`)
        for px in range(tx - 2, tx + 3):
            pix_sc[(px, ty)] = STEEL_HI if px <= tx else STEEL_DK
        for px in range(tx - 1, tx + 2):
            pix_sc[(px, ty + 1)] = (108, 112, 134) if px <= tx else STEEL_DK
        pix_sc[(tx, ty + 2)] = STEEL_DK
        pix_sc[(tx, ty + 3)] = STEEL_DK
        # Multi-layered violet flame rising from inside brazier cup
        for px in (tx - 1, tx, tx + 1):
            pix_sc[(px, ty - 1)] = (238, 204, 255) if px == tx else VIO_FIRE
            pix_sc[(px, ty - 2)] = (248, 228, 255) if px == tx else VIO_FIRE
        pix_sc[(tx, ty - 3)] = VIO_FIRE
        paint_1px_prop_buffer(rgb, pix_sc, OUT, shadow_dx=2, shadow_dy=1, wall_only_shadow=True)

    # Extruded 3D Obsidian Crescent-Moon Totem on Stepped Gothic Pedestal (`nx=157..173`)
    pix_moon: dict[tuple[int, int], tuple[int, int, int]] = {}
    draw_3d_box_prop(
        pix_moon, 160, 168, 25, 29,
        OBSID_A, OBSID_B, OBSID_C, STEEL_HI, perspective_wall="corner", side_w=3, top_h=2,
    )
    # 3D Extruded crescent moon: draw deep back extrusion shifted +2px right first, then crisp lit front crescent!
    for shift_x, is_back in [(2, True), (0, False)]:
        for py in range(11, 24):
            for px in range(158, 171):
                dx = px - 164.0
                d1 = math.hypot(dx, py - 17.5)
                d2 = math.hypot(dx - 2.6, py - 16.5)
                if d1 <= 5.5 and d2 > 3.7:
                    if is_back:
                        pix_moon[(px + shift_x, py)] = (88, 20, 36)  # Deep extruded dark crimson-obsidian rim!
                    else:
                        pix_moon[(px, py)] = (182, 188, 212) if dx < -2.2 else ((136, 142, 166) if dx < -0.5 else CRIM_HI)
    paint_1px_prop_buffer(rgb, pix_moon, OUT, shadow_dx=2, shadow_dy=1)

    draw_door_base(rgb, OBSID_LINE, OUT, void_col=(10, 8, 16), arch=True)
    return rgb


# ---------------------------------------------------------------------------
# ELITE D - Leucótea (Tierra: Estela solar saliente 3D, ánforas con boca 3D y asas)
# ---------------------------------------------------------------------------
def build_elite_d_ground() -> list[list[tuple[int, int, int]]]:
    rgb = [[(0, 0, 0)] * NW for _ in range(NH)]
    ADOBE_HI = (198, 132, 86)
    ADOBE_MID = (174, 110, 70)
    ADOBE_DK = (140, 84, 52)
    MORTAR_G = (98, 56, 36)
    SAND_TRIM = (232, 194, 128)
    SAND_MID = (192, 140, 78)
    OCHRE_DK = (128, 64, 34)

    CLAY_A = (214, 148, 94)
    CLAY_B = (196, 132, 80)
    CLAY_C = (178, 114, 68)
    SAND_LINE = (244, 222, 174)
    OUT = (52, 30, 22)

    cells, edges = compute_grid_cells(1.3, 1.35)

    for nx in range(NW):
        wy = int(round(wall_floor_y(nx)))
        for ny in range(NH):
            if ny < wy:
                uw, hw, _ = wall_uv(nx, ny)
                layer = math.floor(hw * 5.0)
                col_b = math.floor(uw * 1.15 + (0.5 if layer % 2 else 0.0))
                fh = hw * 5.0 - layer
                fu = (uw * 1.15 + (0.5 if layer % 2 else 0.0)) - col_b
                if fh < 0.13 or fu < 0.09:
                    rgb[ny][nx] = MORTAR_G
                else:
                    rgb[ny][nx] = ADOBE_HI if (layer + col_b) % 2 == 0 else ADOBE_MID
            else:
                if edges[ny][nx]:
                    rgb[ny][nx] = MORTAR_G
                else:
                    p = floor_surface_light(nx, ny)
                    iu, iv = cells[ny][nx]
                    base = CLAY_A if ((iu + iv) % 2 == 0) else CLAY_B
                    rgb[ny][nx] = CLAY_C if p < 0.34 else base

    apply_wall_architectural_volume(
        rgb, SAND_TRIM, OCHRE_DK, SAND_TRIM, SAND_MID, OCHRE_DK, ADOBE_HI, MORTAR_G, OUT,
        recess_upper=True, upper_frieze=True,
    )

    for nx in range(NW):
        wy = int(round(wall_floor_y(nx)))
        for ny in range(max(0, wy - 20), wy):
            uw, hw, _ = wall_uv(nx, ny)
            if 0.13 <= hw <= 0.21:
                if int(math.floor(uw * 2.2)) % 2 == 0:
                    rgb[ny][nx] = SAND_TRIM if hw > 0.16 else SAND_MID

    for nx in range(NW):
        for ny in range(int(wall_floor_y(nx)), NH):
            if is_standard_court_line(nx, ny):
                rgb[ny][nx] = SAND_LINE

    draw_pokeball_emblem(rgb, SAND_LINE, (186, 86, 44), SAND_TRIM, CLAY_B, outer_rim_col=OUT)

    for c0, c1, _ in COLS:
        draw_volumetric_column(
            rgb, c0, c1,
            (226, 174, 118), ADOBE_HI, ADOBE_MID, ADOBE_DK, OUT,
            style="pier", cap_hi=SAND_TRIM, cap_dk=OCHRE_DK, upper_frieze=True,
        )

    # Protruding 3D Carved Sandstone Sun-Spiral Tablet Stele mounted on Left Wall (`nx=74..102`)!
    pix_stele: dict[tuple[int, int], tuple[int, int, int]] = {}
    for nx in range(74, 103):
        y_top_s = int(round(wall_y_from_h(nx, 0.62)))
        y_bot_s = int(round(wall_y_from_h(nx, 0.36)))
        tx = (nx - 74) / 28.0
        for ny in range(y_top_s, y_bot_s + 1):
            ty = (ny - y_top_s) / max(1.0, float(y_bot_s - y_top_s))
            if tx > 0.90:
                pix_stele[(nx, ny)] = ADOBE_DK  # Shaded 3D right thickness bevel of stone slab!
            elif ty < 0.12 or tx < 0.10:
                pix_stele[(nx, ny)] = SAND_LINE  # Lit protruding top/left chamfer
            elif ty > 0.88 or tx > 0.80:
                pix_stele[(nx, ny)] = SAND_MID
            else:
                in_sun = (
                    0.18 <= math.hypot(tx - 0.46, ty - 0.50) <= 0.28
                    or math.hypot(tx - 0.46, ty - 0.50) <= 0.10
                    or (abs(tx - 0.46) < 0.05 and 0.16 <= ty <= 0.84)
                    or (abs(ty - 0.50) < 0.06 and 0.15 <= tx <= 0.77)
                )
                pix_stele[(nx, ny)] = SAND_TRIM if in_sun else OCHRE_DK
    paint_1px_prop_buffer(rgb, pix_stele, OUT, shadow_dx=2, shadow_dy=2, wall_only_shadow=True)

    # Twin 3D Painted Terracotta Amphora Urns with Open Dark Rim Oval & Clay Handles (`nx=155..176`)
    pix_urns: dict[tuple[int, int], tuple[int, int, int]] = {}
    for ucx, uy_top, uy_bot, rad in [(162, 13, 29, 4.4), (171, 18, 28, 3.2)]:
        for py in range(uy_top, uy_bot + 1):
            t_y = (py - uy_top) / max(1.0, (uy_bot - uy_top))
            w_u = rad * (0.48 if t_y < 0.20 else (math.sin(t_y * math.pi) * 0.92 + 0.26))
            for px in range(int(round(ucx - w_u)), int(round(ucx + w_u)) + 1):
                dx = px - ucx
                if py == uy_top:
                    pix_urns[(px, py)] = SAND_LINE if abs(dx) >= w_u * 0.6 else (48, 26, 20)  # Dark hollow urn opening!
                elif py == uy_top + 1:
                    pix_urns[(px, py)] = (236, 132, 74) if dx <= 0 else (154, 72, 38)  # Lip curve
                elif 0.42 <= t_y <= 0.53:
                    pix_urns[(px, py)] = SAND_LINE if dx <= 1 else SAND_MID  # Painted belly waist stripe!
                elif dx < -1:
                    pix_urns[(px, py)] = (232, 128, 72)
                elif dx <= 1:
                    pix_urns[(px, py)] = (204, 98, 52)
                else:
                    pix_urns[(px, py)] = (142, 64, 34)
        # Side amphora loop handles (`t_y ~ 0.18..0.38`)
        hy0 = int(round(uy_top + (uy_bot - uy_top) * 0.18))
        hy1 = int(round(uy_top + (uy_bot - uy_top) * 0.36))
        for py in range(hy0, hy1 + 1):
            pix_urns[(int(round(ucx - rad * 0.72)), py)] = (224, 118, 66)
            pix_urns[(int(round(ucx + rad * 0.72)), py)] = (142, 64, 34)
    paint_1px_prop_buffer(rgb, pix_urns, OUT, shadow_dx=2, shadow_dy=1)

    draw_door_base(rgb, SAND_TRIM, OUT, void_col=(28, 18, 14), arch=False)
    return rgb


# ---------------------------------------------------------------------------
# CHAMPION - Rolanda Altamira (Mármol, Terciopelo Carmesí, Candelabros 3D, Corona Real 3D)
# ---------------------------------------------------------------------------
def build_champion_royal() -> list[list[tuple[int, int, int]]]:
    rgb = [[(0, 0, 0)] * NW for _ in range(NH)]
    ROYAL_NAVY_HI = (46, 58, 114)
    ROYAL_NAVY_A = (38, 48, 98)
    ROYAL_NAVY_B = (30, 38, 82)
    GOLD_SPEC = (255, 244, 174)
    GOLD_HI = (250, 212, 92)
    GOLD_MID = (212, 160, 52)
    GOLD_DK = (138, 94, 28)

    CRIMSON_HI = (186, 36, 58)
    CRIMSON_MID = (158, 28, 48)
    CRIMSON_DK = (118, 18, 36)

    MARBLE_HI = (242, 238, 232)
    MARBLE_A = (230, 226, 220)
    MARBLE_B = (218, 212, 206)
    MARBLE_VEIN = (190, 184, 178)
    OUT = (30, 24, 42)

    cells, edges = compute_grid_cells(1.3, 1.3)

    for nx in range(NW):
        wy = int(round(wall_floor_y(nx)))
        for ny in range(NH):
            if ny < wy:
                uw, hw, _ = wall_uv(nx, ny)
                col_p = math.floor(uw * 1.15)
                fu = uw * 1.15 - col_p
                if hw > 0.34:
                    rgb[ny][nx] = ROYAL_NAVY_B if (fu < 0.08 or col_p % 2 == 1) else ROYAL_NAVY_HI
                else:
                    rgb[ny][nx] = ROYAL_NAVY_A if col_p % 2 == 0 else ROYAL_NAVY_B
            else:
                u, v = FLOOR_UV[ny][nx]
                fu, fv = (u * 1.3) % 1.0, (v * 1.3) % 1.0
                in_stud = min(fu, 1.0 - fu) < 0.015 and min(fv, 1.0 - fv) < 0.022
                if in_stud:
                    rgb[ny][nx] = GOLD_MID
                elif edges[ny][nx]:
                    rgb[ny][nx] = MARBLE_VEIN
                else:
                    vein = abs(math.sin(u * 1.1 + v * 1.5 + fbm(u * 0.6, v * 0.6, 2, 19) * 3.5))
                    p = floor_surface_light(nx, ny)
                    if vein < 0.042:
                        rgb[ny][nx] = MARBLE_VEIN
                    elif p > 0.57:
                        rgb[ny][nx] = MARBLE_HI
                    elif p < 0.35:
                        rgb[ny][nx] = MARBLE_B
                    else:
                        rgb[ny][nx] = MARBLE_A

    apply_wall_architectural_volume(
        rgb, GOLD_HI, GOLD_DK, GOLD_HI, GOLD_MID, GOLD_DK, GOLD_MID, GOLD_DK, OUT,
        recess_upper=True, upper_frieze=True,
    )

    for nx in range(NW):
        for ny in range(int(wall_floor_y(nx)), NH):
            if is_standard_court_line(nx, ny):
                rgb[ny][nx] = GOLD_HI if abs(ny - court_mid_y(nx)) <= 1.2 else GOLD_MID

    draw_pokeball_emblem(rgb, (252, 248, 240), CRIMSON_HI, GOLD_MID, MARBLE_HI, outer_rim_col=GOLD_DK)

    for c0, c1, _ in COLS:
        draw_volumetric_column(
            rgb, c0, c1,
            (254, 252, 248), MARBLE_HI, MARBLE_A, (176, 170, 174),
            OUT, style="cylinder", cap_hi=GOLD_HI, cap_dk=GOLD_DK, fluted=True, upper_frieze=True,
        )

    # Volumetric Royal Crimson & 24k Gold Crown Heraldic Banners cleanly below diagonal cornice beam
    for bx0, bx1, h_top in [(14, 28, 0.64), (78, 93, 0.63), (220, 232, 0.56)]:
        draw_clean_banner(rgb, bx0, bx1, 0.37, h_top, CRIMSON_HI, CRIMSON_DK, GOLD_HI, OUT, emblem="crown")

    # 3D Twin-Branch Golden Candelabra Wall Sconces (`nx=66, 144`) with Cast Shadows!
    for sx, sy in [(66, 22), (144, 14)]:
        pix_cand: dict[tuple[int, int], tuple[int, int, int]] = {}
        # Wall backplate + outward curving candle crossbar + left/right lit wax candles & flames
        pix_cand[(sx, sy + 2)] = GOLD_DK
        pix_cand[(sx, sy + 1)] = GOLD_MID
        for px in range(sx - 2, sx + 3):
            pix_cand[(px, sy)] = GOLD_HI if px <= sx else GOLD_DK
        for cx_f in (sx - 2, sx + 2):
            pix_cand[(cx_f, sy - 1)] = MARBLE_HI
            pix_cand[(cx_f, sy - 2)] = GOLD_SPEC
        pix_cand[(sx, sy - 1)] = GOLD_HI
        paint_1px_prop_buffer(rgb, pix_cand, OUT, shadow_dx=2, shadow_dy=1, wall_only_shadow=True)

    # Illuminated 3D Royal Museum Glass Vitrine showcasing Sovereign 24k Crown (`nx=152..176`)
    # Replicates the exact 3/4 perspective structure of Gym05Rock's fossil vitrine so it integrates 100%!
    pix_mon: dict[tuple[int, int], tuple[int, int, int]] = {}
    # 1. Bottom 3D Royal Marble & Crimson Pedestal Base (`front 153..170 + receding right side return 171..174`)
    draw_3d_box_prop(
        pix_mon, 153, 170, 22, 29,
        CRIMSON_HI, CRIMSON_MID, CRIMSON_DK, GOLD_HI,
        perspective_wall="corner", side_w=4, top_h=2,
    )
    # Marble wainscot band & 24k gold base border wrapping front + right side return cleanly
    for px in range(153, 175):
        dy_c = 0 if px <= 170 else -((px - 170) // 2)
        if (px, 24 + dy_c) in pix_mon:
            pix_mon[(px, 24 + dy_c)] = MARBLE_HI if px < 166 else (MARBLE_A if px <= 170 else MARBLE_B)
            pix_mon[(px, 25 + dy_c)] = MARBLE_A if px <= 170 else MARBLE_B
            pix_mon[(px, 28 + dy_c)] = GOLD_MID if px <= 170 else GOLD_DK
            pix_mon[(px, 29 + dy_c)] = GOLD_DK

    # 2. Upper 3D Glass Display Hood (`y=5..20`) with tilted crystal lid, shaded right glass pane & crown inside!
    for px in range(154, 170):
        # Tilted top sapphire crystal lid receding up-right (`y=5..6`)
        pix_mon[(px + 2, 5)] = (194, 232, 248)
        pix_mon[(px + 1, 6)] = (148, 202, 228)
        for py in range(7, 21):
            if px in (154, 169):
                pix_mon[(px, py)] = GOLD_MID  # Vertical golden corner frame mullions
            else:
                # Interior backlit sapphire showcase housing the 24k Sovereign Crown on crimson cushion
                in_cush = (157 <= px <= 166) and (18 <= py <= 19)
                dx_cr = px - 161.5
                in_band = (157 <= px <= 166) and (15 <= py <= 17)
                in_spire = (12 <= py <= 14) and (
                    (px in (157, 158) and py >= 13)
                    or (px in (161, 162) and py >= 12)
                    or (px in (165, 166) and py >= 13)
                )
                in_ruby = (px in (161, 162) and py == 16)
                glint = abs((px - 157) + (py - 8)) <= 1
                if in_ruby:
                    pix_mon[(px, py)] = CRIMSON_HI
                elif in_band or in_spire:
                    if glint:
                        pix_mon[(px, py)] = GOLD_SPEC
                    elif px <= 163:
                        pix_mon[(px, py)] = GOLD_HI
                    else:
                        pix_mon[(px, py)] = GOLD_MID
                elif in_cush:
                    pix_mon[(px, py)] = CRIMSON_HI if px <= 163 else CRIMSON_DK
                elif glint:
                    pix_mon[(px, py)] = (182, 226, 244)
                else:
                    pix_mon[(px, py)] = (42, 68, 96) if py < 14 else (34, 54, 82)
    # Receding right-side glass return panel (`x=170..173`, darker shaded crystal + flush rear gold mullion)
    for sx in range(170, 174):
        dy_s = -((sx - 169) // 2)
        for py in range(max(5, 6 + dy_s), 21 + dy_s):
            pix_mon[(sx, py)] = GOLD_DK if sx == 173 else (32, 52, 78)

    paint_1px_prop_buffer(rgb, pix_mon, OUT, shadow_dx=2, shadow_dy=1)

    # Subtle contact shadow grounding the vitrine plinth onto the crimson carpet
    for py, x0_s, x1_s, f_s in [(30, 154, 175, 0.72), (31, 156, 174, 0.84)]:
        for px in range(x0_s, x1_s + 1):
            if 0 <= px < NW and 0 <= py < NH:
                rgb[py][px] = shade_col(rgb[py][px], f_s)

    draw_door_base(rgb, GOLD_HI, OUT, void_col=(18, 16, 36), arch=True)
    return rgb


def main():
    thumbs_elite, thumbs_champ = [], []
    elite_specs = [
        ("EliteA", "Alto Mando 1 - Bicho (Nicodemo)", build_elite_a_bug),
        ("EliteB", "Alto Mando 2 - Psiquico (Oriana)", build_elite_b_psychic),
        ("EliteC", "Alto Mando 3 - Siniestro (Anteo)", build_elite_c_dark),
        ("EliteD", "Alto Mando 4 - Tierra (Leucotea)", build_elite_d_ground),
    ]
    for name, label, fn in elite_specs:
        save_2x2(fn(), name, label, thumbs_elite)
    save_2x2(build_champion_royal(), "Champion", "Campeona - Rolanda Altamira (Realeza)", thumbs_champ)

    build_sheet(thumbs_elite, PREV_DIR / "league_elite_review.png")
    cw, ch = 532, 424
    c_sheet = Image.new("RGBA", (cw, ch), (20, 22, 30, 255))
    cdraw = ImageDraw.Draw(c_sheet)
    cdraw.text((14, 6), "Campeona - Rolanda Altamira (Realeza / Oro) (512x384)", fill=(252, 218, 98, 255))
    c_sheet.alpha_composite(thumbs_champ[0][2], (10, 26))
    c_sheet.save(PREV_DIR / "champion_review.png")
    print("Installed refined v4 League + Champion Battlebacks cleanly.")


if __name__ == "__main__":
    main()
