"""
Generator for Pokémon REM Itemfinder Overworld Accessory
Creates 4 states:
  state_0_idle.png   - Standby / No items in range
  state_1_near.png   - Detecting item in range (pulsing cyan)
  state_2_facing.png - Near and facing the item (glowing golden-amber, angling forward)
  state_3_target.png - Right in front / target acquired (blazing red-white flare)

Each sheet is 256x256 (64x64 per cell, 4 directions x 4 patterns).
Native pixel art is drawn at 32x32 per cell, then scaled 2x nearest-neighbor.
"""

from PIL import Image, ImageDraw
import os

def create_pixel_grid():
    return Image.new('RGBA', (32, 32), (0, 0, 0, 0))

# Palette
DARK_OUTLINE = (32, 36, 48, 255)
METAL_BASE   = (150, 160, 175, 255)
METAL_LIGHT  = (210, 220, 235, 255)
METAL_DARK   = (90, 100, 115, 255)

ACCENT_RED   = (220, 60, 60, 255)
ACCENT_BLUE  = (50, 120, 220, 255)

# LED Colors per state
# State 0: Idle
S0_LED_OFF = (80, 100, 125, 255)
S0_LED_ON  = (100, 160, 220, 255)

# State 1: Near (Cyan)
S1_LED_CORE_A = (80, 230, 240, 255)
S1_LED_AURA_A = (40, 160, 220, 180)
S1_LED_CORE_B = (240, 255, 255, 255)
S1_LED_AURA_B = (100, 240, 255, 220)

# State 2: Facing (Amber / Gold)
S2_LED_CORE_A = (255, 210, 50, 255)
S2_LED_AURA_A = (230, 140, 30, 180)
S2_LED_CORE_B = (255, 255, 200, 255)
S2_LED_AURA_B = (255, 180, 40, 230)

# State 3: Target (Red Alert / Flare)
S3_LED_CORE_A = (255, 70, 70, 255)
S3_LED_AURA_A = (220, 30, 30, 200)
S3_LED_CORE_B = (255, 255, 255, 255)
S3_LED_AURA_B = (255, 50, 50, 240)

def draw_cell(direction, pattern, state, flash_phase=False):
    """
    direction: 0=Down, 1=Left, 2=Right, 3=Up
    pattern: 0=Walk1, 1=Stand1, 2=Walk2, 3=Stand2
    state: 0..3
    flash_phase: True for pattern 3 or flash pulse
    """
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    bob = 1 if pattern in (0, 2) else 0  # 1 native pixel down during walk steps

    # Determine LED colors for this state & phase
    if state == 0:
        c_core = S0_LED_ON if flash_phase else S0_LED_OFF
        c_aura = None
    elif state == 1:
        c_core = S1_LED_CORE_B if flash_phase else S1_LED_CORE_A
        c_aura = S1_LED_AURA_B if flash_phase else S1_LED_AURA_A
    elif state == 2:
        c_core = S2_LED_CORE_B if flash_phase else S2_LED_CORE_A
        c_aura = S2_LED_AURA_B if flash_phase else S2_LED_AURA_A
    else: # state == 3
        c_core = S3_LED_CORE_B if flash_phase else S3_LED_CORE_A
        c_aura = S3_LED_AURA_B if flash_phase else S3_LED_AURA_A

    def put(x, y, col):
        if 0 <= x < 32 and 0 <= y < 32 and col:
            img.putpixel((x, y), col)

    def draw_bulb(cx, cy):
        # 3x3 rounded bulb
        if c_aura:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    put(cx + dx, cy + dy, c_aura)
        put(cx, cy, c_core)
        put(cx - 1, cy, c_core)
        put(cx + 1, cy, c_core)
        put(cx, cy - 1, c_core)
        put(cx, cy + 1, c_core)
        # dark corners
        put(cx - 1, cy - 1, DARK_OUTLINE)
        put(cx + 1, cy - 1, DARK_OUTLINE)
        put(cx - 1, cy + 1, DARK_OUTLINE)
        put(cx + 1, cy + 1, DARK_OUTLINE)
        # bright center spec
        if flash_phase and state >= 1:
            put(cx, cy, (255, 255, 255, 255))

    # --- DIRECTION 0: DOWN (facing camera) ---
    if direction == 0:
        by = 6 + bob # band y
        # Headband across brow
        for x in range(11, 21):
            put(x, by, METAL_BASE)
            put(x, by + 1, DARK_OUTLINE)
        put(16, by, METAL_LIGHT) # central metallic shine
        # Red side node (left) & Blue side node (right)
        put(10, by, ACCENT_RED)
        put(10, by + 1, DARK_OUTLINE)
        put(9, by, DARK_OUTLINE)
        put(21, by, ACCENT_BLUE)
        put(21, by + 1, DARK_OUTLINE)
        put(22, by, DARK_OUTLINE)

        # Antenna rods and tips based on state
        if state in (0, 1):
            # Angled slightly outward
            # Left rod: (10, by-1) -> (9, by-3) -> bulb at (8, by-5)
            put(10, by - 1, METAL_BASE)
            put(9, by - 2, DARK_OUTLINE)
            put(9, by - 3, METAL_BASE)
            put(8, by - 4, DARK_OUTLINE)
            draw_bulb(8, by - 5)

            # Right rod: (21, by-1) -> (22, by-3) -> bulb at (23, by-5)
            put(21, by - 1, METAL_BASE)
            put(22, by - 2, DARK_OUTLINE)
            put(22, by - 3, METAL_BASE)
            put(23, by - 4, DARK_OUTLINE)
            draw_bulb(23, by - 5)

        elif state == 2:
            # Facing: Antennas perk up more vertical / slightly focused
            put(11, by - 1, METAL_BASE)
            put(10, by - 2, DARK_OUTLINE)
            put(10, by - 3, METAL_BASE)
            put(10, by - 4, DARK_OUTLINE)
            draw_bulb(10, by - 5)

            put(20, by - 1, METAL_BASE)
            put(21, by - 2, DARK_OUTLINE)
            put(21, by - 3, METAL_BASE)
            put(21, by - 4, DARK_OUTLINE)
            draw_bulb(21, by - 5)

        elif state == 3:
            # Target ahead! Antennas converge towards center-front!
            put(11, by - 1, METAL_BASE)
            put(12, by - 2, DARK_OUTLINE)
            put(13, by - 3, METAL_BASE)
            put(13, by - 4, DARK_OUTLINE)
            draw_bulb(13, by - 5)

            put(20, by - 1, METAL_BASE)
            put(19, by - 2, DARK_OUTLINE)
            put(18, by - 3, METAL_BASE)
            put(18, by - 4, DARK_OUTLINE)
            draw_bulb(18, by - 5)

            # Center target beacon flare / exclamation in phase B
            if flash_phase:
                put(15, by - 7, (255, 255, 255, 255))
                put(16, by - 7, (255, 255, 255, 255))
                put(15, by - 6, (255, 255, 255, 255))
                put(16, by - 6, (255, 255, 255, 255))
                put(15, by - 4, (255, 255, 255, 255))
                put(16, by - 4, (255, 255, 255, 255))

    # --- DIRECTION 1: LEFT (facing left) ---
    elif direction == 1:
        by = 6 + bob
        # Headband profile: wraps along left side from brow (x=10) to back (x=21)
        for x in range(11, 21):
            put(x, by, METAL_BASE)
            put(x, by + 1, DARK_OUTLINE)
        put(11, by, ACCENT_RED) # front node accent
        put(10, by, DARK_OUTLINE)
        put(21, by, METAL_DARK)

        if state in (0, 1):
            # Near antenna (prominent, angled slightly back):
            put(15, by - 1, METAL_BASE)
            put(16, by - 2, DARK_OUTLINE)
            put(16, by - 3, METAL_BASE)
            put(17, by - 4, DARK_OUTLINE)
            draw_bulb(17, by - 5)
            # Far antenna (fainter behind):
            put(19, by - 2, DARK_OUTLINE)
            put(20, by - 3, METAL_DARK)
            put(20, by - 4, c_core)

        elif state == 2:
            # Facing Left: Antennas angle forward towards LEFT!
            put(14, by - 1, METAL_BASE)
            put(13, by - 2, DARK_OUTLINE)
            put(12, by - 3, METAL_BASE)
            put(11, by - 4, DARK_OUTLINE)
            draw_bulb(11, by - 5)
            # Far antenna:
            put(16, by - 2, DARK_OUTLINE)
            put(15, by - 3, METAL_DARK)
            put(14, by - 4, c_core)

        elif state == 3:
            # Target: Antennas sharp forward-pointing towards left!
            put(14, by - 1, METAL_BASE)
            put(12, by - 2, DARK_OUTLINE)
            put(10, by - 3, METAL_BASE)
            put(9, by - 3, DARK_OUTLINE)
            draw_bulb(9, by - 4)
            # Far antenna pointing along:
            put(15, by - 2, DARK_OUTLINE)
            put(13, by - 3, METAL_DARK)
            put(11, by - 4, c_core)
            if flash_phase:
                put(7, by - 4, (255, 255, 255, 255))
                put(6, by - 4, (255, 200, 200, 220))

    # --- DIRECTION 2: RIGHT (facing right) ---
    elif direction == 2:
        # Perfectly mirrored from Left
        left_img = draw_cell(1, pattern, state, flash_phase)
        return left_img.transpose(Image.FLIP_LEFT_RIGHT)

    # --- DIRECTION 3: UP (facing away / back of head) ---
    elif direction == 3:
        by = 5 + bob # slightly higher back-of-head band
        for x in range(11, 21):
            put(x, by, METAL_BASE)
            put(x, by + 1, DARK_OUTLINE)
        put(10, by, ACCENT_BLUE)
        put(10, by + 1, DARK_OUTLINE)
        put(9, by, DARK_OUTLINE)
        put(21, by, ACCENT_RED)
        put(21, by + 1, DARK_OUTLINE)
        put(22, by, DARK_OUTLINE)

        if state in (0, 1):
            put(10, by - 1, METAL_BASE)
            put(9, by - 2, DARK_OUTLINE)
            put(9, by - 3, METAL_BASE)
            put(8, by - 4, DARK_OUTLINE)
            draw_bulb(8, by - 5)

            put(21, by - 1, METAL_BASE)
            put(22, by - 2, DARK_OUTLINE)
            put(22, by - 3, METAL_BASE)
            put(23, by - 4, DARK_OUTLINE)
            draw_bulb(23, by - 5)

        elif state == 2:
            put(11, by - 1, METAL_BASE)
            put(10, by - 2, DARK_OUTLINE)
            put(10, by - 3, METAL_BASE)
            put(10, by - 4, DARK_OUTLINE)
            draw_bulb(10, by - 5)

            put(20, by - 1, METAL_BASE)
            put(21, by - 2, DARK_OUTLINE)
            put(21, by - 3, METAL_BASE)
            put(21, by - 4, DARK_OUTLINE)
            draw_bulb(21, by - 5)

        elif state == 3:
            put(11, by - 1, METAL_BASE)
            put(12, by - 2, DARK_OUTLINE)
            put(13, by - 3, METAL_BASE)
            put(13, by - 4, DARK_OUTLINE)
            draw_bulb(13, by - 5)

            put(20, by - 1, METAL_BASE)
            put(19, by - 2, DARK_OUTLINE)
            put(18, by - 3, METAL_BASE)
            put(18, by - 4, DARK_OUTLINE)
            draw_bulb(18, by - 5)

            if flash_phase:
                put(15, by - 7, (255, 255, 255, 255))
                put(16, by - 7, (255, 255, 255, 255))
                put(15, by - 6, (255, 255, 255, 255))
                put(16, by - 6, (255, 255, 255, 255))

    return img

def build_state_spritesheet(state):
    """
    Builds a 256x256 RGBA image (4 rows x 4 columns of 64x64 cells).
    Row 0: Down (sy=0)
    Row 1: Left (sy=64)
    Row 2: Right (sy=128)
    Row 3: Up (sy=192)
    Col 0: Pattern 0 (Walk 1, bob=1)
    Col 1: Pattern 1 (Stand 1, bob=0, flash_phase=False)
    Col 2: Pattern 2 (Walk 2, bob=1)
    Col 3: Pattern 3 (Stand 2, bob=0, flash_phase=True -> Pulse LED)
    """
    native_sheet = Image.new('RGBA', (128, 128), (0, 0, 0, 0))

    for dir_idx in range(4):
        for pat_idx in range(4):
            flash = (pat_idx == 3) # pattern 3 is the flash phase
            cell = draw_cell(dir_idx, pat_idx, state, flash_phase=flash)
            native_sheet.paste(cell, (pat_idx * 32, dir_idx * 32))

    # Scale 2x nearest-neighbor to exactly match 256x256 character grid
    scaled_sheet = native_sheet.resize((256, 256), Image.NEAREST)
    return scaled_sheet

if __name__ == '__main__':
    state_names = [
        ('state_0_idle.png', 0),
        ('state_1_near.png', 1),
        ('state_2_facing.png', 2),
        ('state_3_target.png', 3),
    ]

    out_dir = 'Graphics/Characters/Itemfinder'
    os.makedirs(out_dir, exist_ok=True)

    for fname, st in state_names:
        sheet = build_state_spritesheet(st)
        sheet.save(os.path.join(out_dir, fname))
        print(f'Saved {out_dir}/{fname} (256x256)')

    print('All 4 Itemfinder state sheets generated successfully!')
