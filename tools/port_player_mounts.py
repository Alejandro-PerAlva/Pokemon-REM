#!/usr/bin/env python3
"""
Port player mounts (Bicycle, Surfboard Surf, Land Fish, Surfboard Surf-Fishing) for Pokémon REM.

- Bicycle (`256x256`, `64x64`): mountain bike ported from Pokémon Añil.
- Surf (`384x320`, `96x80` `_offset`): REM Key Item Surfboard (Tabla de Surf) with gentle wave
  pitching + surf wake foam; Left/Right show classic surfer stance (front-facing planted torso/feet
  + head turned in travel direction), Down/Up show balanced surfer stance on longitudinal board.
- Land Fish (`512x512`, `128x128` `_offset`): cleaned/centered REM fishing sprite (`oy=112`).
- Surf-Fishing (`384x320`, `96x80` `_offset`): exact REM Land Fish animation standing on the floating Surfboard.
All output strictly enforces 100% 2x2 native pixel blocks.
"""

import argparse
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAR_DIR = os.path.join(ROOT, "Graphics", "Characters")
PREV_DIR = os.path.join(ROOT, "previews")

ANIL_DIR = r"C:\Users\apera\Documents\Juegos Rateo\Pokemon Anil v4.14\Graphics\Characters"

T = (0, 0, 0, 0)
OUTLINE = (0, 0, 0, 255)
OUTLINE_GIRL = (24, 23, 23, 255)

# Añil Bike hardware palette
B_BLK = (0, 0, 0, 255)
B_DK = (56, 32, 32, 255)
B_MR = (91, 46, 46, 255)
B_RD = (128, 32, 32, 255)
B_RB = (186, 25, 25, 255)
B_R2 = (192, 56, 56, 255)
B_TI = (56, 64, 64, 255)
B_BR = (112, 96, 64, 255)
B_S1 = (152, 152, 152, 255)
B_S2 = (207, 213, 224, 255)
B_S3 = (208, 184, 184, 255)

# REM character palettes (exact RGBA sampled from trchar000.png & trchar001.png)
BOY_SKIN_HI = (248, 208, 184, 255)
BOY_SKIN_SH = (208, 152, 112, 255)
BOY_TEAL_HI = (0, 130, 132, 255)
BOY_TEAL_DK = (13, 91, 92, 255)
BOY_PANT_HI = (88, 88, 104, 255)
BOY_PANT_DK = (56, 56, 56, 255)
BOY_SHOE_HI = (232, 112, 64, 255)
BOY_SHOE_MD = (184, 72, 40, 255)
BOY_BAG_GRY = (173, 191, 205, 255)

GIRL_SKIN_HI = (247, 207, 182, 255)
GIRL_SKIN_SH = (207, 150, 111, 255)
GIRL_TEAL_HI = (0, 130, 132, 255)
GIRL_TEAL_DK = (13, 91, 92, 255)
GIRL_SKIRT_HI = (232, 118, 151, 255)
GIRL_SKIRT_SH = (176, 68, 91, 255)
GIRL_PANT_DK = (48, 48, 56, 255)
GIRL_PANT_MD = (88, 88, 104, 255)
GIRL_SHOE_HI = (41, 112, 129, 255)
GIRL_SHOE_DK = (41, 67, 79, 255)

# Surfboard & Ocean Wake palette (crisp nautical fiberglass + coral stripe)
SB_OUT = (20, 34, 62, 255)        # deep navy surfboard hull outline
SB_DECK_HI = (244, 250, 255, 255)  # glossy white fiberglass highlight
SB_DECK_MD = (204, 232, 248, 255)  # pale sky-ice fiberglass deck
SB_RAIL = (108, 178, 224, 255)     # aqua board rail / bevel
SB_BELLY = (58, 112, 168, 255)     # shaded hull underside / fin
SB_STR_HI = (236, 84, 72, 255)     # coral-red racing stripe highlight
SB_STR_DK = (176, 44, 48, 255)     # coral-red racing stripe shade
SB_FOAM = (248, 252, 255, 255)     # pure white surf spray
SB_SPRAY = (144, 218, 248, 255)    # bright cyan wave crest
SB_WAKE = (72, 146, 214, 185)      # soft translucent water wake


def px2(img, x, y, color):
    if color[3] == 0 or not (0 <= x < img.width - 1 and 0 <= y < img.height - 1):
        return
    p = img.load()
    p[x, y] = color
    p[x + 1, y] = color
    p[x, y + 1] = color
    p[x + 1, y + 1] = color


def clear2(img, x, y):
    if not (0 <= x < img.width - 1 and 0 <= y < img.height - 1):
        return
    p = img.load()
    p[x, y] = T
    p[x + 1, y] = T
    p[x, y + 1] = T
    p[x + 1, y + 1] = T


def norm_rgba(im):
    out = im.convert("RGBA")
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            if px[x, y][3] == 0:
                px[x, y] = T
    return out


def verify_2x2(im, name="image"):
    px = im.load()
    bad = 0
    for y in range(0, im.height, 2):
        for x in range(0, im.width, 2):
            c = px[x, y]
            if px[x + 1, y] != c or px[x, y + 1] != c or px[x + 1, y + 1] != c:
                bad += 1
    if bad:
        raise AssertionError(f"{name}: {bad} 2x2 mismatches!")
    return True


def build_surfboard_cell(direction, col, is_calm=False):
    """
    Draw a 96x80 surfboard cell (center x=48, deck feet line y=62..64, waterline oy=64).
    direction: 0=Down, 1=Left, 2=Right, 3=Up
    col: 0..3 wave bobbing / gentle nose pitch cycle
    is_calm: True for FishSurf idle board underneath standing caster
    """
    cell = Image.new("RGBA", (96, 80), T)

    # Wave pitch/rocking on col 0..3 (subtle swell: 0=flat, 1=nose rises, 2=crest, 3=settle)
    nose_lift = 0 if is_calm else (-2 if col in (1, 2) else 0)
    tail_lift = 0 if is_calm else (-2 if col == 2 else 0)
    foam_shift = 0 if is_calm else ((col % 2) * 2)

    if direction in (1, 2):
        # Horizontal funboard/shortboard (Left orientation spans x=16..78; mirrored for Right)
        is_right = (direction == 2)

        def put(lx, ly, c):
            px2(cell, (94 - lx) if is_right else lx, ly, c)

        # Gentle curved deck height across x=16..78:
        # Nose tip at x=16..26 (pivots slightly up on wave crest), wide parallel mid x=28..64, tail x=66..76
        # Deck top sits at y=60..62 so trainer feet (y=62..64) plant solidly ON top of the white deck!
        # Cross-section per column x: (top_outline, deck_rows, rail_row, bottom_outline)
        cols = {}
        # Pointed curved nose (x=16..26) with nose_lift
        cols[16] = (58 + nose_lift, [60 + nose_lift], None, 62 + nose_lift)
        cols[18] = (58 + nose_lift, [60 + nose_lift], None, 62 + nose_lift)
        cols[20] = (56 + nose_lift, [58 + nose_lift, 60 + nose_lift], 62 + nose_lift, 64 + nose_lift)
        cols[22] = (56 + nose_lift, [58 + nose_lift, 60 + nose_lift], 62 + nose_lift, 64 + nose_lift)
        dl = tail_lift
        cols[24] = (58 + nose_lift, [60 + nose_lift], 62 + nose_lift, 64 + nose_lift)
        cols[26] = (58 + dl, [60 + dl, 62 + dl], 64 + dl, 66 + dl)
        # Parallel mid-board under feet (x=28..64, stable deck lift)
        for x in range(28, 66, 2):
            cols[x] = (58 + dl, [60 + dl, 62 + dl], 64 + dl, 66 + dl)
        # Tapered surf tail + subtle underside skeg fin (x=66..76)
        cols[66] = (58 + dl, [60 + dl, 62 + dl], 64 + dl, 66 + dl)
        cols[68] = (58 + dl, [60 + dl, 62 + dl], 64 + dl, 66 + dl)
        cols[70] = (58 + dl, [60 + dl], 62 + dl, 64 + dl)
        cols[72] = (58 + dl, [60 + dl], 62 + dl, 64 + dl)
        cols[74] = (58 + dl, [60 + dl], None, 62 + dl)
        cols[76] = (60 + dl, [], None, 62 + dl)

        # Draw soft water wake UNDER/AROUND hull first
        for wx in range(18, 78, 2):
            y_bot = cols[wx][3] if wx in cols else 64
            put(wx, y_bot, SB_WAKE)
            if wx >= 24:
                put(wx, y_bot + 2, SB_SPRAY if ((wx + foam_shift) % 6 == 0) else SB_WAKE)
        # Nose splash & tail wake foam across animation columns
        if not is_calm:
            if col in (1, 2):
                put(14, 62 + nose_lift, SB_FOAM)
                put(16, 64 + nose_lift, SB_SPRAY)
                put(20, 66, SB_FOAM)
            put(76 + foam_shift, 62 + dl, SB_FOAM)
            put(78 + foam_shift, 64 + dl, SB_SPRAY)
            if col in (2, 3):
                put(80, 62 + dl, SB_WAKE)
        else:
            put(16, 64, SB_SPRAY)
            put(76, 64, SB_SPRAY)

        # Draw surfboard body cleanly over wake
        for x, (t_y, d_ys, r_y, b_y) in cols.items():
            put(x, t_y, SB_OUT)
            for idx, dy in enumerate(d_ys):
                # Nose tip coral accent + sleek longitudinal racing stripe along middle row
                if x <= 22:
                    c = SB_STR_HI if idx == 0 else SB_STR_DK
                elif len(d_ys) >= 2 and idx == 1 and 28 <= x <= 68:
                    c = SB_STR_HI if 34 <= x <= 60 else SB_DECK_MD
                else:
                    c = SB_DECK_HI if idx == 0 else SB_DECK_MD
                put(x, dy, c)
            if r_y is not None:
                put(x, r_y, SB_BELLY if x >= 68 else SB_RAIL)
            put(x, b_y, SB_OUT)
        # Tiny surf fin peeking at tail underside
        put(68, 66 + dl, SB_BELLY)
        put(70, 66 + dl, SB_OUT)

        # White foam spray highlights lapping front rail
        for fx in (24 + foam_shift, 38 + foam_shift, 56 - foam_shift, 70):
            put(fx, 66 + (nose_lift if fx < 28 else dl), SB_FOAM)

    else:
        # Vertical foreshortened longitudinal surfboard (Down row=0, Up row=3)
        # Centered around x=48 (width x=36..58, fore-aft y=48..76)
        is_up = (direction == 3)
        dy_wave = nose_lift  # -2 on crest cols 1..2

        def put_v(vx, vy, c):
            # For Up (row=3), mirror vertically around y=62 so pointed nose leads UP/away (y=48) and squared tail sits DOWN/behind (y=72)!
            yy = (124 - vy) if is_up else vy
            px2(cell, vx, yy, c)

        # Down geometry: tail top at y=50..56 (behind heels), wide deck y=56..66, tapered pointed nose y=68..74
        # Per-y half-widths from center axis x=46..48:
        rows_v = {
            50: 4,   # squared surf tail
            52: 6,
            54: 8,
            56: 8,
            58: 10,  # wide mid deck under feet
            60: 10,
            62: 10,
            64: 10,
            66: 8,
            68: 8,
            70: 6,   # tapered surf nose curving into wave
            72: 4,
            74: 2,
        }
        # Wake ripples & bow spray outside hull
        for y, hw in rows_v.items():
            yl = y + (dy_wave if y >= 66 else tail_lift)
            put_v(46 - hw - 2, yl, SB_SPRAY if (y + foam_shift) % 4 == 0 else SB_WAKE)
            put_v(48 + hw + 2, yl, SB_SPRAY if (y + foam_shift) % 4 == 0 else SB_WAKE)
        if not is_up:
            put_v(46, 76 + dy_wave, SB_FOAM)
            put_v(48, 76 + dy_wave, SB_FOAM)
            put_v(42 - foam_shift, 74 + dy_wave, SB_SPRAY)
            put_v(52 + foam_shift, 74 + dy_wave, SB_SPRAY)
        else:
            put_v(46, 48 + dy_wave, SB_FOAM)
            put_v(48, 48 + dy_wave, SB_FOAM)
            put_v(44, 74 + tail_lift, SB_WAKE)
            put_v(50, 74 + tail_lift, SB_WAKE)

        # Draw longitudinal surfboard hull
        for y, hw in rows_v.items():
            yl = y + (dy_wave if y >= 66 else tail_lift)
            lx = 46 - hw
            rx = 48 + hw
            for x in range(lx, rx + 2, 2):
                if x in (lx, rx) or y in (50, 74):
                    col_p = SB_OUT
                elif y >= 72 or x in (46, 48):
                    # Nose coral tip + crisp center racing stripe
                    col_p = SB_STR_HI if (y >= 70 or (54 <= y <= 70 and x in (46, 48))) else SB_DECK_HI
                elif x in (lx + 2, rx - 2):
                    col_p = SB_RAIL
                else:
                    col_p = SB_DECK_HI if x in (42, 44, 50, 52) else SB_DECK_MD
                put_v(x, yl, col_p)

        # Outer foam dots at side rails
        put_v(36, 62 + foam_shift, SB_FOAM)
        put_v(58, 64 - foam_shift, SB_FOAM)

    return cell


def build_surfboard_surf_sheet(is_girl):
    """
    Build 384x320 (96x80, _offset oy=64) Surf sheet with surfboard underneath:
    - Row 0 (Down): trchar Down head+torso + planted balanced surfer stance on longitudinal board
    - Row 1 (Left): Front-facing surfer torso/stance (trchar Down) + head turned LEFT (trchar Left)
    - Row 2 (Right): Front-facing surfer torso/stance (trchar Down) + head turned RIGHT (trchar Right)
    - Row 3 (Up): trchar Up back+head + balanced surfer stance on longitudinal board
    Zero walking leg swing; surfboard gently bobs/pitches across col 0..3.
    """
    stand = norm_rgba(Image.open(os.path.join(CHAR_DIR, "trchar001.png" if is_girl else "trchar000.png")))
    out = Image.new("RGBA", (384, 320), T)

    skin_hi = GIRL_SKIN_HI if is_girl else BOY_SKIN_HI
    skin_sh = GIRL_SKIN_SH if is_girl else BOY_SKIN_SH
    teal_hi = GIRL_TEAL_HI if is_girl else BOY_TEAL_HI
    teal_dk = GIRL_TEAL_DK if is_girl else BOY_TEAL_DK
    edge = OUTLINE_GIRL if is_girl else OUTLINE

    # Build reusable static surfer poses per direction (64x64 space, feet bottom at y=64 -> pasted at (16, 0))
    def make_side_surfer(is_right):
        """
        Surfer stance matching Regular footing:
        - Moving RIGHT (row 2): front torso (Down row 0, y>=38) + head turned RIGHT (row 2)
        - Moving LEFT  (row 1): back torso (Up row 3, y>=38)   + head turned LEFT  (row 1)
        """
        pose = Image.new("RGBA", (64, 64), T)
        head_row = 2 if is_right else 1
        body_row = 0 if is_right else 3

        # 1. Body & legs from Down (Right) or Up (Left), shifted dy=+2 (feet -> y=64)
        body = stand.crop((0, body_row * 64, 64, (body_row + 1) * 64)).copy()
        for y in range(0, 38, 2):
            for x in range(0, 64, 2):
                clear2(body, x, y)
        # On Girl Down (Right), trim cheek braid ends above skirt/chest outside x=22..40; on Girl Up (Left), trim Up hair tips at x=38..44 y=38
        if is_girl and is_right:
            for y in range(38, 46, 2):
                for x in range(0, 64, 2):
                    if x < 22 or x > 40:
                        clear2(body, x, y)
        elif is_girl and not is_right:
            for x in range(20, 48, 2):
                if body.getpixel((x, 38)) not in (GIRL_SKIRT_SH, (184, 64, 61, 255), (108, 42, 40, 255)):
                    clear2(body, x, 38)
            clear2(body, 42, 40)  # remove stray Up hair-tip outline next to right shoulder
        pose.paste(body, (0, 2), body)

        # Widen/plant feet cleanly below waist (preserve Boy's white satchel at y=50..54 & Girl's pink skirt at y=52..54!)
        for y in range(56, 64, 2):
            for x in range(20, 44, 2):
                clear2(pose, x, y)
        if not is_girl:
            # Ensure hip continuity at y=54..56 for Boy (without overwriting satchel on Left!)
            if is_right:
                for fx in range(24, 38, 2):
                    px2(pose, fx, 54, BOY_PANT_DK if fx in (30, 32) else BOY_PANT_HI)
                px2(pose, 22, 54, edge); px2(pose, 38, 54, edge)
            lx_foot, rx_foot = (22, 36) if not is_right else (26, 40)
            for fx in (lx_foot, rx_foot):
                px2(pose, fx - 2, 56, edge); px2(pose, fx, 56, BOY_PANT_HI); px2(pose, fx + 2, 56, BOY_PANT_DK); px2(pose, fx + 4, 56, edge)
                px2(pose, fx - 2, 58, edge); px2(pose, fx, 58, BOY_SHOE_HI); px2(pose, fx + 2, 58, BOY_SHOE_MD); px2(pose, fx + 4, 58, edge)
                px2(pose, fx, 60, edge); px2(pose, fx + 2, 60, edge)
        else:
            if is_right:
                for fx in range(22, 42, 2):
                    px2(pose, fx, 54, GIRL_SKIRT_HI if fx in (26, 28, 30, 32, 34, 36) else (GIRL_SKIRT_SH if fx in (24, 38) else edge))
            lx_foot, rx_foot = (22, 36) if not is_right else (26, 38)
            for fx in (lx_foot, rx_foot):
                px2(pose, fx - 2, 56, edge); px2(pose, fx, 56, GIRL_PANT_DK); px2(pose, fx + 2, 56, GIRL_PANT_MD); px2(pose, fx + 4, 56, edge)
                px2(pose, fx - 2, 58, edge); px2(pose, fx, 58, GIRL_SHOE_HI); px2(pose, fx + 2, 58, GIRL_SHOE_DK); px2(pose, fx + 4, 58, edge)
                px2(pose, fx, 60, edge); px2(pose, fx + 2, 60, edge)

        # 2. Turned Head from trchar Left (row 1) / Right (row 2) col 0, aligned naturally over shoulders
        hcrop = stand.crop((0, head_row * 64, 64, head_row * 64 + 40)).copy()
        if is_girl:
            for x in range(24, 38, 2):
                if hcrop.getpixel((x, 38)) in (GIRL_TEAL_HI, GIRL_TEAL_DK):
                    clear2(hcrop, x, 38)
        else:
            for x in range(24, 38, 2):
                if hcrop.getpixel((x, 38)) in (BOY_TEAL_HI, BOY_TEAL_DK):
                    clear2(hcrop, x, 38)
        pose.paste(hcrop, (0, 2), hcrop)
        return pose

    def make_axial_surfer(direction_row):
        """Static balanced surfer stance on longitudinal surfboard for Down (row 0) & Up (row 3)."""
        pose = stand.crop((0, direction_row * 64, 64, (direction_row + 1) * 64)).copy()
        # Shift down +2 so feet reach y=64 on board deck, and stagger back/front foot slightly for surfer stance
        out_p = Image.new("RGBA", (64, 64), T)
        out_p.paste(pose.crop((0, 0, 64, 62)), (0, 2), pose.crop((0, 0, 64, 62)))
        # Raise rear right foot 2px cleanly so one foot steps slightly forward on deck
        for x in (34, 36, 38):
            col_bot = out_p.getpixel((x, 60))
            col_mid = out_p.getpixel((x, 58))
            if col_bot[3] > 0:
                px2(out_p, x, 58, col_bot)
                clear2(out_p, x, 62)
                px2(out_p, x, 60, edge)
        return out_p

    poses = {
        0: make_axial_surfer(0),
        1: make_side_surfer(is_right=False),
        2: make_side_surfer(is_right=True),
        3: make_axial_surfer(3),
    }

    for r in range(4):
        for c in range(4):
            cell = build_surfboard_cell(r, c, is_calm=False)
            # Subtle wave-deck lift ONLY on col 2 (tail_lift = -2) so rider feet stay glued to deck
            dy_deck = -2 if c == 2 else 0
            cell.paste(poses[r], (16, dy_deck), poses[r])
            out.paste(cell, (c * 96, r * 80))

    verify_2x2(out, f"{'girl' if is_girl else 'boy'}_surf_offset")
    return out


def build_fish_offset_sheet(is_girl):
    """Repack 522x522 REM fish sheet into exact 512x512 (128x128) _offset synced to oy=112."""
    src_fn = "girl_fish.png" if is_girl else "boy_fish.png"
    src_path = os.path.join(CHAR_DIR, src_fn)
    if not os.path.exists(src_path):
        fallback = os.path.join(CHAR_DIR, "girl_fish_offset.png" if is_girl else "boy_fish_offset.png")
        im = norm_rgba(Image.open(fallback))
        verify_2x2(im, os.path.basename(fallback))
        return im

    src = norm_rgba(Image.open(src_path))
    out = Image.new("RGBA", (512, 512), T)
    row_dy = [4, 4, 2, 2] if is_girl else [0, 0, 0, 0]

    for r in range(4):
        for c in range(4):
            x0, y0 = c * 130, r * 130
            cell130 = src.crop((x0, y0, min(522, x0 + 130), min(522, y0 + 130)))
            dst = Image.new("RGBA", (128, 128), T)
            dy = row_dy[r]
            for y in range(0, 128, 2):
                for x in range(2, 128, 2):
                    nx = x - 2
                    ny = y + dy
                    if not (0 <= ny < 128):
                        continue
                    if x < cell130.width - 1 and y < cell130.height - 1:
                        samples = [
                            cell130.getpixel((x, y)),
                            cell130.getpixel((x + 1, y)),
                            cell130.getpixel((x, y + 1)),
                            cell130.getpixel((x + 1, y + 1)),
                        ]
                        opaque = [s for s in samples if s[3] > 0]
                        if len(opaque) >= 2:
                            chosen = max(set(opaque), key=opaque.count)
                            px2(dst, nx, ny, chosen)
            out.paste(dst, (c * 128, r * 128))

    verify_2x2(out, f"{'girl' if is_girl else 'boy'}_fish_offset")
    return out


def build_fishsurf_surfboard_sheet(is_girl, fish_offset_sheet):
    """
    Build 384x320 (96x80, _offset oy=64) Surf-Fishing sheet:
    Literally the exact Land Fish spritesheet (boy_fish_offset / girl_fish_offset)
    standing face-forward in the fishing direction atop the calm floating Surfboard!
    """
    out = Image.new("RGBA", (384, 320), T)

    for r in range(4):
        board = build_surfboard_cell(r, col=0, is_calm=True)
        for c in range(4):
            cell = board.copy()
            # Map 128x128 fish_offset (feet oy=112, cx=64) onto 96x80 (deck oy=64, cx=48):
            # dx = -16, dy = -48 -> feet land at y=64 right on the surfboard deck!
            fcell = fish_offset_sheet.crop((c * 128, r * 128, (c + 1) * 128, (r + 1) * 128))
            fcrop = fcell.crop((16, 48, 112, 128))
            cell.paste(fcrop, (0, 0), fcrop)
            out.paste(cell, (c * 96, r * 80))

    verify_2x2(out, f"{'girl' if is_girl else 'boy'}_fishsurf_offset")
    return out


def make_grid_preview(img, cell_w, cell_h, zoom=2):
    w, h = img.size
    canvas = Image.new("RGBA", (w * zoom, h * zoom), (218, 232, 248, 255))
    scaled = img.resize((w * zoom, h * zoom), Image.NEAREST)
    canvas.paste(scaled, (0, 0), scaled)
    d = ImageDraw.Draw(canvas)
    for c in range(1, 4):
        d.line([(c * cell_w * zoom, 0), (c * cell_w * zoom, h * zoom)], fill=(155, 178, 210, 255))
    for r in range(1, 4):
        d.line([(0, r * cell_h * zoom), (w * zoom, r * cell_h * zoom)], fill=(155, 178, 210, 255))
    return canvas


def save_walk_gif(sheet, row, cell_w, cell_h, out_path, duration=150):
    frames = []
    for c in range(4):
        f = Image.new("RGBA", (cell_w * 3, cell_h * 3), (72, 152, 224, 255))
        cell = sheet.crop((c * cell_w, row * cell_h, (c + 1) * cell_w, (row + 1) * cell_h))
        up = cell.resize((cell_w * 3, cell_h * 3), Image.NEAREST)
        f.paste(up, (0, 0), up)
        frames.append(f)
    frames[0].save(out_path, save_all=True, append_images=frames[1:], duration=duration, loop=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write final sheets into Graphics/Characters/")
    args = parser.parse_args()

    os.makedirs(PREV_DIR, exist_ok=True)

    boy_surf = build_surfboard_surf_sheet(False)
    girl_surf = build_surfboard_surf_sheet(True)

    boy_fish = build_fish_offset_sheet(False)
    girl_fish = build_fish_offset_sheet(True)

    boy_fishsurf = build_fishsurf_surfboard_sheet(False, boy_fish)
    girl_fishsurf = build_fishsurf_surfboard_sheet(True, girl_fish)

    outputs = {
        "boy_surf_offset.png": (boy_surf, 96, 80),
        "girl_surf_offset.png": (girl_surf, 96, 80),
        "boy_fishsurf_offset.png": (boy_fishsurf, 96, 80),
        "girl_fishsurf_offset.png": (girl_fishsurf, 96, 80),
    }

    for fname, (img, cw, ch) in outputs.items():
        stem = os.path.splitext(fname)[0]
        img.save(os.path.join(PREV_DIR, f"{stem}_proto.png"))
        make_grid_preview(img, cw, ch, zoom=2).save(os.path.join(PREV_DIR, f"{stem}_zoom.png"))
        if args.apply:
            img.save(os.path.join(CHAR_DIR, fname))

    for kind, sh in [
        ("surf_boy", boy_surf),
        ("surf_girl", girl_surf),
        ("fishsurf_boy", boy_fishsurf),
        ("fishsurf_girl", girl_fishsurf),
    ]:
        for r, dname in enumerate(["Down", "Left", "Right", "Up"]):
            save_walk_gif(sh, r, 96, 80, os.path.join(PREV_DIR, f"anim_{kind}_{dname}.gif"))

    print("Surfboard Surf + Surf-Fishing sheets generated cleanly (2x2 verified).")
    if args.apply:
        print("Applied Surf & Surf-Fishing spritesheets to Graphics/Characters/.")


if __name__ == "__main__":
    main()
