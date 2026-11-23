"""
V2 Generator for Pokémon REM Itemfinder Overworld Accessory
Features:
- Solid, substantial tech headset (earcups, visor band, rear strap, thick articulated antennas)
- Enhanced 3D depth on lateral profile (near + far antenna) and rear view
- Precise pattern tracking matching character walk/run bobbing
"""

from PIL import Image
import os

def create_pixel_grid():
    return Image.new('RGBA', (32, 32), (0, 0, 0, 0))

# Palette: Heavy Tech Metal
OUTLINE      = (26, 30, 42, 255)
METAL_SHADOW = (65, 75, 92, 255)
METAL_MID    = (135, 148, 168, 255)
METAL_LIGHT  = (195, 208, 225, 255)
METAL_SHEEN  = (240, 246, 255, 255)

# Far antenna shade (depth perspective)
FAR_METAL    = (95, 105, 122, 255)
FAR_LIGHT    = (150, 160, 178, 255)

# Temple Module Accents
RED_NODE     = (225, 50, 50, 255)
RED_SHADOW   = (140, 25, 25, 255)
BLUE_NODE    = (45, 125, 230, 255)
BLUE_SHADOW  = (20, 65, 145, 255)

# LED Colors per state
# State 0: Idle (Soft standby)
S0_CORE_OFF  = (70, 90, 115, 255)
S0_CORE_ON   = (100, 165, 230, 255)

# State 1: Near (Cyan Ping)
S1_CORE_A    = (70, 230, 245, 255)
S1_AURA_A    = (30, 150, 215, 180)
S1_CORE_B    = (245, 255, 255, 255)
S1_AURA_B    = (90, 235, 255, 230)

# State 2: Facing (Amber / Gold)
S2_CORE_A    = (255, 205, 40, 255)
S2_AURA_A    = (230, 130, 25, 190)
S2_CORE_B    = (255, 255, 190, 255)
S2_AURA_B    = (255, 180, 35, 240)

# State 3: Target (Red Alert Flare)
S3_CORE_A    = (255, 65, 65, 255)
S3_AURA_A    = (220, 25, 25, 210)
S3_CORE_B    = (255, 255, 255, 255)
S3_AURA_B    = (255, 45, 45, 250)

def draw_cell_v2(direction, pattern, state, flash_phase=False):
    """
    direction: 0=Down, 1=Left, 2=Right, 3=Up
    pattern: 0=Walk1, 1=Stand1, 2=Walk2, 3=Stand2
    state: 0..3
    flash_phase: True for pattern 3
    """
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    bob = 1 if pattern in (0, 2) else 0

    if state == 0:
        c_core = S0_CORE_ON if flash_phase else S0_CORE_OFF
        c_aura = None
    elif state == 1:
        c_core = S1_CORE_B if flash_phase else S1_CORE_A
        c_aura = S1_AURA_B if flash_phase else S1_AURA_A
    elif state == 2:
        c_core = S2_CORE_B if flash_phase else S2_CORE_A
        c_aura = S2_AURA_B if flash_phase else S2_AURA_A
    else: # state == 3
        c_core = S3_CORE_B if flash_phase else S3_CORE_A
        c_aura = S3_AURA_B if flash_phase else S3_AURA_A

    def put(x, y, col):
        if 0 <= x < 32 and 0 <= y < 32 and col:
            img.putpixel((x, y), col)

    def draw_bulb(cx, cy, is_far=False):
        # Substantial 3x3 rounded sensor bulb with metallic socket at base
        core = FAR_LIGHT if is_far and state == 0 else c_core
        aura = None if is_far and state == 0 else c_aura

        if aura:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    put(cx + dx, cy + dy, aura)

        # Bulb body
        put(cx, cy, core)
        put(cx - 1, cy, core)
        put(cx + 1, cy, core)
        put(cx, cy - 1, core)
        put(cx, cy + 1, core)

        # Rim outline
        put(cx - 1, cy - 1, OUTLINE)
        put(cx + 1, cy - 1, OUTLINE)
        put(cx - 1, cy + 1, OUTLINE)
        put(cx + 1, cy + 1, OUTLINE)

        # Metallic socket base underneath
        put(cx - 1, cy + 2, OUTLINE)
        put(cx, cy + 2, METAL_MID if not is_far else FAR_METAL)
        put(cx + 1, cy + 2, OUTLINE)

        # Flash center
        if flash_phase and state >= 1 and not is_far:
            put(cx, cy, (255, 255, 255, 255))
            if state == 3:
                # Starburst cross
                put(cx - 2, cy, (255, 255, 255, 220))
                put(cx + 2, cy, (255, 255, 255, 220))
                put(cx, cy - 2, (255, 255, 255, 220))

    # =========================================================================
    # DIRECTION 0: DOWN (Frontal View)
    # =========================================================================
    if direction == 0:
        by = 6 + bob

        # 1. Main Visor Band (3 rows thick: highlight, body, shadow)
        for x in range(11, 22):
            put(x, by - 1, METAL_SHEEN)
            put(x, by, METAL_MID)
            put(x, by + 1, OUTLINE)
        put(16, by - 1, (255, 255, 255, 255)) # center gleam
        put(16, by, METAL_LIGHT)

        # 2. Left Temple / Earcup Module (x=8..10)
        for y in range(by - 1, by + 2):
            put(7, y, OUTLINE)
            put(8, y, METAL_LIGHT)
            put(9, y, METAL_MID)
            put(10, y, METAL_SHADOW)
        put(8, by, RED_NODE)
        put(8, by + 1, RED_SHADOW)
        put(8, by - 2, OUTLINE)
        put(9, by - 2, OUTLINE)

        # 3. Right Temple / Earcup Module (x=22..24)
        for y in range(by - 1, by + 2):
            put(22, y, METAL_SHADOW)
            put(23, y, METAL_MID)
            put(24, y, METAL_LIGHT)
            put(25, y, OUTLINE)
        put(24, by, BLUE_NODE)
        put(24, by + 1, BLUE_SHADOW)
        put(23, by - 2, OUTLINE)
        put(24, by - 2, OUTLINE)

        # 4. Antennas
        if state in (0, 1):
            # Angled outward
            # Left hinge & stem
            put(8, by - 2, METAL_LIGHT)
            put(9, by - 2, METAL_MID)
            put(7, by - 3, OUTLINE)
            put(8, by - 3, METAL_LIGHT)
            put(7, by - 4, OUTLINE)
            put(7, by - 5, METAL_MID)
            draw_bulb(7, by - 6)

            # Right hinge & stem
            put(23, by - 2, METAL_MID)
            put(24, by - 2, METAL_LIGHT)
            put(25, by - 3, OUTLINE)
            put(24, by - 3, METAL_LIGHT)
            put(25, by - 4, OUTLINE)
            put(25, by - 5, METAL_MID)
            draw_bulb(25, by - 6)

        elif state == 2:
            # Facing: Antennas perk upright & forward
            put(9, by - 2, METAL_LIGHT)
            put(9, by - 3, OUTLINE)
            put(9, by - 4, METAL_MID)
            put(9, by - 5, METAL_LIGHT)
            draw_bulb(9, by - 6)

            put(23, by - 2, METAL_LIGHT)
            put(23, by - 3, OUTLINE)
            put(23, by - 4, METAL_MID)
            put(23, by - 5, METAL_LIGHT)
            draw_bulb(23, by - 6)

        elif state == 3:
            # Target: Antennas converge inward
            put(9, by - 2, METAL_LIGHT)
            put(10, by - 3, OUTLINE)
            put(11, by - 4, METAL_MID)
            put(12, by - 5, METAL_LIGHT)
            draw_bulb(13, by - 6)

            put(23, by - 2, METAL_LIGHT)
            put(22, by - 3, OUTLINE)
            put(21, by - 4, METAL_MID)
            put(20, by - 5, METAL_LIGHT)
            draw_bulb(19, by - 6)

            if flash_phase:
                # Target alert beacon above brow
                put(16, by - 7, (255, 255, 255, 255))
                put(16, by - 6, (255, 255, 255, 255))
                put(16, by - 4, (255, 255, 255, 255))

    # =========================================================================
    # DIRECTION 1: LEFT (Side Profile facing Left)
    # =========================================================================
    elif direction == 1:
        by = 6 + bob

        # 1. Front Brow Visor (sweeping forward x=9..14)
        for x in range(9, 15):
            put(x, by - 1, METAL_SHEEN)
            put(x, by, METAL_MID)
            put(x, by + 1, OUTLINE)
        put(8, by, OUTLINE)
        put(9, by, METAL_LIGHT) # front nose/brow tip

        # 2. Rear Head Strap (wrapping back x=18..23)
        for x in range(18, 23):
            put(x, by, METAL_SHADOW)
            put(x, by + 1, OUTLINE)
        put(23, by, OUTLINE)

        # 3. Substantial Earcup Module (x=14..18, y=by-2..by+2)
        for x in range(14, 19):
            put(x, by - 2, OUTLINE)
            put(x, by + 2, OUTLINE)
        for y in range(by - 1, by + 2):
            put(13, y, OUTLINE)
            put(14, y, METAL_LIGHT)
            put(15, y, METAL_MID)
            put(16, y, METAL_MID)
            put(17, y, METAL_SHADOW)
            put(18, y, METAL_SHADOW)
            put(19, y, OUTLINE)
        # Center status node on earcup
        put(16, by, RED_NODE)
        put(16, by + 1, RED_SHADOW)

        # 4. Antennas in Profile (Near in foreground, Far peeking in depth)
        if state in (0, 1):
            # Far antenna (background, depth offset x+5, y-1)
            put(21, by - 3, OUTLINE)
            put(21, by - 4, FAR_LIGHT)
            draw_bulb(21, by - 5, is_far=True)

            # Near antenna (foreground, sturdy angled stem)
            put(15, by - 2, METAL_LIGHT)
            put(16, by - 2, METAL_MID)
            put(16, by - 3, OUTLINE)
            put(16, by - 4, METAL_LIGHT)
            put(17, by - 5, METAL_MID)
            draw_bulb(17, by - 6)

        elif state == 2:
            # Facing Left: Antennas angle forward towards LEFT!
            put(20, by - 3, OUTLINE)
            put(19, by - 4, FAR_LIGHT)
            draw_bulb(18, by - 5, is_far=True)

            put(15, by - 2, METAL_LIGHT)
            put(14, by - 3, OUTLINE)
            put(13, by - 4, METAL_LIGHT)
            put(12, by - 5, METAL_MID)
            draw_bulb(11, by - 6)

        elif state == 3:
            # Target: Both antennas sharp forward pointing towards left!
            put(18, by - 3, OUTLINE)
            put(16, by - 4, FAR_LIGHT)
            draw_bulb(14, by - 5, is_far=True)

            put(15, by - 2, METAL_LIGHT)
            put(13, by - 3, OUTLINE)
            put(11, by - 4, METAL_LIGHT)
            put(9, by - 4, METAL_MID)
            draw_bulb(8, by - 5)

            if flash_phase:
                put(5, by - 5, (255, 255, 255, 255))
                put(4, by - 5, (255, 180, 180, 220))

    # =========================================================================
    # DIRECTION 2: RIGHT (Side Profile facing Right)
    # =========================================================================
    elif direction == 2:
        # Mirror of Left, swap node to Blue
        left_cell = draw_cell_v2(1, pattern, state, flash_phase)
        mirrored = left_cell.transpose(Image.FLIP_LEFT_RIGHT)
        # recolor red node to blue node
        pix = mirrored.load()
        for x in range(32):
            for y in range(32):
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

        # 1. Sturdy Rear Occipital Brace (curving across back of head)
        for x in range(11, 22):
            put(x, by - 1, METAL_SHEEN)
            put(x, by, METAL_MID)
            put(x, by + 1, METAL_SHADOW)
            put(x, by + 2, OUTLINE)
        put(16, by - 1, (255, 255, 255, 255))

        # 2. Left Earcup from behind (gripping head at x=8..10)
        for y in range(by - 1, by + 2):
            put(7, y, OUTLINE)
            put(8, y, METAL_LIGHT)
            put(9, y, METAL_MID)
            put(10, y, METAL_SHADOW)
        put(7, by, BLUE_NODE) # rear view swaps left/right perspective
        put(7, by + 1, BLUE_SHADOW)

        # 3. Right Earcup from behind (gripping head at x=22..24)
        for y in range(by - 1, by + 2):
            put(22, y, METAL_SHADOW)
            put(23, y, METAL_MID)
            put(24, y, METAL_LIGHT)
            put(25, y, OUTLINE)
        put(25, by, RED_NODE)
        put(25, by + 1, RED_SHADOW)

        # 4. Antennas seen from behind
        if state in (0, 1):
            put(8, by - 2, METAL_LIGHT)
            put(9, by - 2, METAL_MID)
            put(7, by - 3, OUTLINE)
            put(8, by - 3, METAL_LIGHT)
            put(7, by - 4, OUTLINE)
            put(7, by - 5, METAL_MID)
            draw_bulb(7, by - 6)

            put(23, by - 2, METAL_MID)
            put(24, by - 2, METAL_LIGHT)
            put(25, by - 3, OUTLINE)
            put(24, by - 3, METAL_LIGHT)
            put(25, by - 4, OUTLINE)
            put(25, by - 5, METAL_MID)
            draw_bulb(25, by - 6)

        elif state == 2:
            put(9, by - 2, METAL_LIGHT)
            put(9, by - 3, OUTLINE)
            put(9, by - 4, METAL_MID)
            put(9, by - 5, METAL_LIGHT)
            draw_bulb(9, by - 6)

            put(23, by - 2, METAL_LIGHT)
            put(23, by - 3, OUTLINE)
            put(23, by - 4, METAL_MID)
            put(23, by - 5, METAL_LIGHT)
            draw_bulb(23, by - 6)

        elif state == 3:
            put(9, by - 2, METAL_LIGHT)
            put(10, by - 3, OUTLINE)
            put(11, by - 4, METAL_MID)
            put(12, by - 5, METAL_LIGHT)
            draw_bulb(13, by - 6)

            put(23, by - 2, METAL_LIGHT)
            put(22, by - 3, OUTLINE)
            put(21, by - 4, METAL_MID)
            put(20, by - 5, METAL_LIGHT)
            draw_bulb(19, by - 6)

            if flash_phase:
                put(16, by - 7, (255, 255, 255, 255))
                put(16, by - 6, (255, 255, 255, 255))

    return img

def build_v2_spritesheet(state):
    native_sheet = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    for dir_idx in range(4):
        for pat_idx in range(4):
            flash = (pat_idx == 3)
            cell = draw_cell_v2(dir_idx, pat_idx, state, flash_phase=flash)
            native_sheet.paste(cell, (pat_idx * 32, dir_idx * 32))
    return native_sheet.resize((256, 256), Image.NEAREST)

if __name__ == '__main__':
    out_dir = 'Graphics/Characters/Itemfinder'
    os.makedirs(out_dir, exist_ok=True)
    state_names = [
        ('state_0_idle.png', 0),
        ('state_1_near.png', 1),
        ('state_2_facing.png', 2),
        ('state_3_target.png', 3),
    ]
    for fname, st in state_names:
        sheet = build_v2_spritesheet(st)
        sheet.save(os.path.join(out_dir, fname))
        print(f'V2: Saved {fname}')
