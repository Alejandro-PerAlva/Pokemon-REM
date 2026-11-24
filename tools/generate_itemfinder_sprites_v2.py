"""
V3 Generator for Pokémon REM Itemfinder Overworld Accessory
Improvements over V2:
- Expanded canvas from 32x32 to 40x40 native (80x80 scaled cell, 320x320 total sheet)
  with OX=4, OY=8 anchor padding so antenna bulbs, top outlines, halos, and State 3 flare
  never clip at the top or side edges.
- Refined contoured visor curvature on Front/Back, rounded earcup pods on Lateral profile,
  clear near/far antenna separation, and sculpted 3-row rear strap (less boxy slab).
"""

from PIL import Image
import os

# Palette: Sleek Anodized Titanium & Dark Trim
OUTLINE      = (26, 30, 42, 255)
METAL_DEEP   = (58, 68, 84, 255)
METAL_SHADOW = (88, 98, 118, 255)
METAL_MID    = (146, 158, 178, 255)
METAL_LIGHT  = (204, 214, 230, 255)
METAL_SHEEN  = (232, 240, 250, 255)

# Far antenna depth tones (lateral perspective)
FAR_OUTLINE  = (42, 48, 62, 255)
FAR_METAL    = (98, 108, 126, 255)
FAR_LIGHT    = (148, 160, 178, 255)

# Side Module Indicator Nodes
RED_NODE     = (224, 54, 54, 255)
RED_SHADOW   = (142, 28, 34, 255)
BLUE_NODE    = (50, 132, 232, 255)
BLUE_SHADOW  = (24, 68, 148, 255)

# State 0: Idle (standby soft blue/slate)
S0_RIM       = (72, 86, 108, 255)
S0_CORE_OFF  = (112, 134, 160, 255)
S0_CORE_ON   = (124, 182, 232, 255)

# State 1: Near (Cyan radar pulse)
S1_RIM       = (34, 138, 194, 255)
S1_CORE_A    = (84, 228, 244, 255)
S1_AURA_A    = (46, 175, 228, 150)
S1_CORE_B    = (220, 252, 255, 255)
S1_AURA_B    = (96, 235, 255, 210)

# State 2: Facing (Warm Golden Amber)
S2_RIM       = (188, 112, 22, 255)
S2_CORE_A    = (252, 206, 54, 255)
S2_AURA_A    = (236, 150, 32, 160)
S2_CORE_B    = (255, 250, 185, 255)
S2_AURA_B    = (255, 192, 48, 220)

# State 3: Target (Crimson Red Alert Flare)
S3_RIM       = (185, 24, 28, 255)
S3_CORE_A    = (248, 56, 56, 255)
S3_AURA_A    = (220, 30, 34, 175)
S3_CORE_B    = (255, 68, 68, 255)
S3_AURA_B    = (255, 82, 40, 225)

# Canvas dimensions (native 40x40 per cell; original 32x32 origin shifted by +4, +8)
CELL_N = 40
OX = 4
OY = 8


def draw_cell_v3(direction, pattern, state, flash_phase=False):
    """
    direction: 0=Down, 1=Left, 2=Right, 3=Up
    pattern: 0=Walk1, 1=Stand1, 2=Walk2, 3=Stand2
    state: 0..3
    flash_phase: True for pattern 3 (pulse bright phase)
    """
    img = Image.new("RGBA", (CELL_N, CELL_N), (0, 0, 0, 0))
    bob = 1 if pattern in (0, 2) else 0

    if state == 0:
        c_core = S0_CORE_ON if flash_phase else S0_CORE_OFF
        c_rim = S0_RIM
        c_aura = None
    elif state == 1:
        c_core = S1_CORE_B if flash_phase else S1_CORE_A
        c_rim = S1_RIM
        c_aura = S1_AURA_B if flash_phase else S1_AURA_A
    elif state == 2:
        c_core = S2_CORE_B if flash_phase else S2_CORE_A
        c_rim = S2_RIM
        c_aura = S2_AURA_B if flash_phase else S2_AURA_A
    else:
        c_core = S3_CORE_B if flash_phase else S3_CORE_A
        c_rim = S3_RIM
        c_aura = S3_AURA_B if flash_phase else S3_AURA_A

    def put(x, y, col):
        nx, ny = x + OX, y + OY
        if 0 <= nx < CELL_N and 0 <= ny < CELL_N and col:
            img.putpixel((nx, ny), col)

    def put_halo(x, y, col):
        """Draw translucent halo only onto empty background pixels so outlines stay crisp."""
        nx, ny = x + OX, y + OY
        if 0 <= nx < CELL_N and 0 <= ny < CELL_N and col:
            if img.getpixel((nx, ny))[3] == 0:
                img.putpixel((nx, ny), col)

    def draw_bulb(cx, cy, is_far=False):
        """Rounded 3x3 emissive sensor dome with full top outline & metallic socket collar."""
        core = (FAR_LIGHT if (is_far and state == 0) else c_core)
        rim = (FAR_OUTLINE if (is_far and state == 0) else c_rim)
        out = FAR_OUTLINE if is_far else OUTLINE
        aura = None if is_far else c_aura

        # Optional soft radial halo behind dome on active states (bright pulse only to keep idle clean)
        if aura and (flash_phase or state >= 2):
            for dx, dy in ((-2, 0), (2, 0), (0, -2)):
                put_halo(cx + dx, cy + dy, aura)

        # Dome outer rim (complete top outline, never clipped)
        put(cx, cy - 2, out)
        put(cx - 1, cy - 1, out if state == 0 else rim)
        put(cx + 1, cy - 1, out if state == 0 else rim)
        put(cx - 2, cy, out)
        put(cx + 2, cy, out)
        put(cx - 1, cy + 1, out)
        put(cx + 1, cy + 1, out)

        # Glowing / shaded sphere interior
        put(cx, cy - 1, core)
        put(cx - 1, cy, core)
        put(cx + 1, cy, rim if (is_far and state == 0) else core)
        if flash_phase and state >= 1 and not is_far:
            put(cx, cy, (255, 255, 255, 255))
        else:
            put(cx, cy, core)
        put(cx, cy + 1, rim)

        # Metallic socket collar beneath sphere
        put(cx - 1, cy + 2, out)
        put(cx, cy + 2, FAR_METAL if is_far else METAL_MID)
        put(cx + 1, cy + 2, out)

        # State 3 top peak flare attached cleanly to dome
        if state == 3 and flash_phase and not is_far:
            put(cx, cy - 2, (255, 220, 120, 255))
            put_halo(cx, cy - 3, (255, 80, 60, 220))

    # =========================================================================
    # DIRECTION 0: DOWN (Frontal View)
    # =========================================================================
    if direction == 0:
        by = 6 + bob

        # 1. Slim Curved Visor Arch (3px sleek thickness matching rear Up strap: 1px core + top/bottom OUTLINE)
        # Smooth upward parabolic curve across forehead (temples by -> mid by-1 -> crown peak by-2)
        # with a subtle central micro sensor notch on (16, by) so it reads sculpted without bulkiness.
        arch_offsets = {
            10: 0,
            11: 0,
            12: -1,
            13: -1,
            14: -1,
            15: -1,
            16: -1,
            17: -1,
            18: -1,
            19: -1,
            20: -1,
            21: 0,
            22: 0,
        }
        for x, dy in arch_offsets.items():
            yy = by + dy
            put(x, yy - 1, OUTLINE)
            if 15 <= x <= 17:
                put(x, yy, METAL_SHEEN)
            elif 12 <= x <= 20:
                put(x, yy, METAL_LIGHT)
            else:
                put(x, yy, METAL_MID)
            put(x, yy + 1, OUTLINE)
        # Tiny sleek center brow bridge node (1px lower at x=16 only)
        put(16, by, c_core if state >= 1 else METAL_MID)
        put(16, by + 1, OUTLINE)

        # 2. Left Temple Earcup Pod (x=8..10, red LED accent)
        for y in range(by - 1, by + 2):
            put(7, y, OUTLINE)
            put(8, y, METAL_LIGHT)
            put(9, y, METAL_MID)
            put(10, y, METAL_SHADOW)
        put(8, by - 2, OUTLINE)
        put(9, by - 2, OUTLINE)
        put(8, by + 2, OUTLINE)
        put(9, by + 2, OUTLINE)
        put(8, by, RED_NODE)
        put(8, by + 1, RED_SHADOW)

        # 3. Right Temple Earcup Pod (x=22..24, blue LED accent)
        for y in range(by - 1, by + 2):
            put(22, y, METAL_SHADOW)
            put(23, y, METAL_MID)
            put(24, y, METAL_LIGHT)
            put(25, y, OUTLINE)
        put(23, by - 2, OUTLINE)
        put(24, by - 2, OUTLINE)
        put(23, by + 2, OUTLINE)
        put(24, by + 2, OUTLINE)
        put(24, by, BLUE_NODE)
        put(24, by + 1, BLUE_SHADOW)

        # 4. Antennas
        if state in (0, 1):
            # Angled outward symmetrically
            put(8, by - 2, METAL_LIGHT)
            put(9, by - 2, METAL_MID)
            put(7, by - 3, OUTLINE)
            put(8, by - 3, METAL_LIGHT)
            put(9, by - 3, OUTLINE)
            put(6, by - 4, OUTLINE)
            put(7, by - 4, METAL_LIGHT)
            put(8, by - 4, OUTLINE)
            draw_bulb(7, by - 6)

            put(23, by - 2, METAL_MID)
            put(24, by - 2, METAL_LIGHT)
            put(23, by - 3, OUTLINE)
            put(24, by - 3, METAL_LIGHT)
            put(25, by - 3, OUTLINE)
            put(24, by - 4, OUTLINE)
            put(25, by - 4, METAL_LIGHT)
            put(26, by - 4, OUTLINE)
            draw_bulb(25, by - 6)

        elif state == 2:
            # Focused upright / forward-aligned
            for sy_off in (-2, -3, -4):
                put(8, by + sy_off, OUTLINE)
                put(9, by + sy_off, METAL_LIGHT)
                put(10, by + sy_off, OUTLINE)
            draw_bulb(9, by - 6)

            for sy_off in (-2, -3, -4):
                put(22, by + sy_off, OUTLINE)
                put(23, by + sy_off, METAL_LIGHT)
                put(24, by + sy_off, OUTLINE)
            draw_bulb(23, by - 6)

        elif state == 3:
            # Converging inward sharply toward center
            put(9, by - 2, METAL_LIGHT)
            put(10, by - 2, OUTLINE)
            put(9, by - 3, OUTLINE)
            put(10, by - 3, METAL_LIGHT)
            put(11, by - 3, OUTLINE)
            put(11, by - 4, METAL_LIGHT)
            put(12, by - 4, OUTLINE)
            draw_bulb(12, by - 6)

            put(22, by - 2, OUTLINE)
            put(23, by - 2, METAL_LIGHT)
            put(21, by - 3, OUTLINE)
            put(22, by - 3, METAL_LIGHT)
            put(23, by - 3, OUTLINE)
            put(20, by - 4, OUTLINE)
            put(21, by - 4, METAL_LIGHT)
            draw_bulb(20, by - 6)

    # =========================================================================
    # DIRECTION 1: LEFT (Profile Facing Left)
    # =========================================================================
    elif direction == 1:
        by = 6 + bob

        # 1. Curved Front Brow Visor (sweeps cleanly across left brow)
        put(9, by, OUTLINE)
        put(10, by - 1, OUTLINE)
        put(10, by, METAL_LIGHT)
        put(10, by + 1, OUTLINE)
        for x in range(11, 14):
            put(x, by - 1, METAL_SHEEN)
            put(x, by, METAL_MID)
            put(x, by + 1, OUTLINE)

        # 2. Rear Temple Strap (hugs skull cleanly back to x=22)
        for x in range(19, 23):
            put(x, by - 1, OUTLINE)
            put(x, by, METAL_SHADOW)
            put(x, by + 1, OUTLINE)
        put(23, by, OUTLINE)

        # 3. Rounded Beveled Earcup Module (x=14..18, y=by-2..by+2)
        for x in range(14, 19):
            put(x, by - 2, OUTLINE)
            put(x, by + 2, OUTLINE)
        for y in range(by - 1, by + 2):
            put(13, y, OUTLINE)
            put(14, y, METAL_LIGHT)
            put(15, y, METAL_MID)
            put(16, y, METAL_MID)
            put(17, y, METAL_SHADOW)
            put(18, y, METAL_DEEP)
            put(19, y, OUTLINE)
        # Top metallic curve bevel & center Ruby node
        put(15, by - 1, METAL_SHEEN)
        put(16, by - 1, METAL_LIGHT)
        put(16, by, RED_NODE)
        put(16, by + 1, RED_SHADOW)

        # 4. Dual Perspective Antennas (Far behind crown, Near from earcup)
        if state in (0, 1):
            # Far antenna peeking slightly back-right with depth occlusion
            put(20, by - 2, FAR_OUTLINE)
            put(21, by - 2, FAR_METAL)
            put(21, by - 3, FAR_LIGHT)
            put(22, by - 3, FAR_OUTLINE)
            draw_bulb(22, by - 5, is_far=True)

            # Near antenna rising cleanly with swivel collar
            put(15, by - 2, METAL_LIGHT)
            put(16, by - 2, METAL_MID)
            put(15, by - 3, OUTLINE)
            put(16, by - 3, METAL_LIGHT)
            put(17, by - 3, OUTLINE)
            put(16, by - 4, OUTLINE)
            put(17, by - 4, METAL_LIGHT)
            put(18, by - 4, OUTLINE)
            draw_bulb(17, by - 6)

        elif state == 2:
            # Facing Left: both antennas tilt forward towards LEFT!
            put(18, by - 2, FAR_OUTLINE)
            put(17, by - 3, FAR_LIGHT)
            put(18, by - 3, FAR_OUTLINE)
            draw_bulb(17, by - 5, is_far=True)

            put(14, by - 2, METAL_LIGHT)
            put(15, by - 2, METAL_MID)
            put(12, by - 3, OUTLINE)
            put(13, by - 3, METAL_LIGHT)
            put(14, by - 3, OUTLINE)
            put(11, by - 4, OUTLINE)
            put(12, by - 4, METAL_LIGHT)
            put(13, by - 4, OUTLINE)
            draw_bulb(11, by - 6)

        elif state == 3:
            # Target Left: both thrust diagonally forward-left!
            put(17, by - 2, FAR_OUTLINE)
            put(15, by - 3, FAR_LIGHT)
            put(16, by - 3, FAR_OUTLINE)
            draw_bulb(14, by - 5, is_far=True)

            put(14, by - 2, METAL_LIGHT)
            put(15, by - 2, METAL_MID)
            put(11, by - 3, OUTLINE)
            put(12, by - 3, METAL_LIGHT)
            put(13, by - 3, OUTLINE)
            put(9, by - 4, OUTLINE)
            put(10, by - 4, METAL_LIGHT)
            put(11, by - 4, OUTLINE)
            draw_bulb(8, by - 5)

            if flash_phase:
                # Subtle glow right on tip side, no extra floating dots
                put_halo(5, by - 5, (255, 80, 50, 200))

    # =========================================================================
    # DIRECTION 2: RIGHT (Profile Facing Right)
    # =========================================================================
    elif direction == 2:
        left_cell = draw_cell_v3(1, pattern, state, flash_phase)
        mirrored = left_cell.transpose(Image.FLIP_LEFT_RIGHT)
        pix = mirrored.load()
        for x in range(CELL_N):
            for y in range(CELL_N):
                if pix[x, y][:3] == RED_NODE[:3]:
                    pix[x, y] = BLUE_NODE
                elif pix[x, y][:3] == RED_SHADOW[:3]:
                    pix[x, y] = BLUE_SHADOW
        return mirrored

    # =========================================================================
    # DIRECTION 3: UP (Rear View of Head)
    # =========================================================================
    elif direction == 3:
        by = 6 + bob

        # 1. Sculpted 3-row Occipital Strap (lighter & contoured instead of heavy slab)
        for x in range(11, 22):
            arch = -1 if 13 <= x <= 19 else 0
            put(x, by + arch - 1, OUTLINE)
            put(x, by + arch, METAL_LIGHT if 13 <= x <= 19 else METAL_MID)
            put(x, by + arch + 1, OUTLINE)
        put(15, by - 1, METAL_SHEEN)
        put(16, by - 1, METAL_SHEEN)
        put(17, by - 1, METAL_SHEEN)

        # 2. Left Ear Module from behind (x=8..10, Blue node tucked neatly inside rim)
        for y in range(by - 1, by + 2):
            put(7, y, OUTLINE)
            put(8, y, METAL_LIGHT)
            put(9, y, METAL_MID)
            put(10, y, METAL_SHADOW)
        put(8, by - 2, OUTLINE)
        put(9, by - 2, OUTLINE)
        put(8, by + 2, OUTLINE)
        put(9, by + 2, OUTLINE)
        put(8, by, BLUE_NODE)
        put(8, by + 1, BLUE_SHADOW)

        # 3. Right Ear Module from behind (x=22..24, Red node tucked neatly inside rim)
        for y in range(by - 1, by + 2):
            put(22, y, METAL_SHADOW)
            put(23, y, METAL_MID)
            put(24, y, METAL_LIGHT)
            put(25, y, OUTLINE)
        put(23, by - 2, OUTLINE)
        put(24, by - 2, OUTLINE)
        put(23, by + 2, OUTLINE)
        put(24, by + 2, OUTLINE)
        put(24, by, RED_NODE)
        put(24, by + 1, RED_SHADOW)

        # 4. Rear Antennas
        if state in (0, 1):
            put(8, by - 2, METAL_LIGHT)
            put(9, by - 2, METAL_MID)
            put(7, by - 3, OUTLINE)
            put(8, by - 3, METAL_LIGHT)
            put(9, by - 3, OUTLINE)
            put(6, by - 4, OUTLINE)
            put(7, by - 4, METAL_LIGHT)
            put(8, by - 4, OUTLINE)
            draw_bulb(7, by - 6)

            put(23, by - 2, METAL_MID)
            put(24, by - 2, METAL_LIGHT)
            put(23, by - 3, OUTLINE)
            put(24, by - 3, METAL_LIGHT)
            put(25, by - 3, OUTLINE)
            put(24, by - 4, OUTLINE)
            put(25, by - 4, METAL_LIGHT)
            put(26, by - 4, OUTLINE)
            draw_bulb(25, by - 6)

        elif state == 2:
            for sy_off in (-2, -3, -4):
                put(8, by + sy_off, OUTLINE)
                put(9, by + sy_off, METAL_LIGHT)
                put(10, by + sy_off, OUTLINE)
            draw_bulb(9, by - 6)

            for sy_off in (-2, -3, -4):
                put(22, by + sy_off, OUTLINE)
                put(23, by + sy_off, METAL_LIGHT)
                put(24, by + sy_off, OUTLINE)
            draw_bulb(23, by - 6)

        elif state == 3:
            put(9, by - 2, METAL_LIGHT)
            put(10, by - 2, OUTLINE)
            put(9, by - 3, OUTLINE)
            put(10, by - 3, METAL_LIGHT)
            put(11, by - 3, OUTLINE)
            put(11, by - 4, METAL_LIGHT)
            put(12, by - 4, OUTLINE)
            draw_bulb(12, by - 6)

            put(22, by - 2, OUTLINE)
            put(23, by - 2, METAL_LIGHT)
            put(21, by - 3, OUTLINE)
            put(22, by - 3, METAL_LIGHT)
            put(23, by - 3, OUTLINE)
            put(20, by - 4, OUTLINE)
            put(21, by - 4, METAL_LIGHT)
            draw_bulb(20, by - 6)

    return img


def build_v3_spritesheet(state):
    native_sheet = Image.new("RGBA", (CELL_N * 4, CELL_N * 4), (0, 0, 0, 0))
    for dir_idx in range(4):
        for pat_idx in range(4):
            flash = (pat_idx == 3)
            cell = draw_cell_v3(dir_idx, pat_idx, state, flash_phase=flash)
            native_sheet.paste(cell, (pat_idx * CELL_N, dir_idx * CELL_N))
    return native_sheet.resize((CELL_N * 8, CELL_N * 8), Image.NEAREST)


if __name__ == "__main__":
    out_dir = "Graphics/Characters/Itemfinder"
    os.makedirs(out_dir, exist_ok=True)
    state_names = [
        ("state_0_idle.png", 0),
        ("state_1_near.png", 1),
        ("state_2_facing.png", 2),
        ("state_3_target.png", 3),
    ]
    for fname, st in state_names:
        sheet = build_v3_spritesheet(st)
        sheet.save(os.path.join(out_dir, fname))
        print(f"V3: Saved {fname} ({sheet.size[0]}x{sheet.size[1]})")
