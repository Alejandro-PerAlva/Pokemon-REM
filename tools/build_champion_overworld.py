"""Build the Champion (Rolanda Altamira) 256x256 overworld spritesheet.

Genuine Gen-4 HGSS kitbash: combines trchar053's asymmetrical female head,
hair locks, and earrings with trchar061's draped cape walk-cycle body,
then deeply recolors and custom-sculpts Rolanda Altamira's signature details:
  - Voluminous sapphire/cobalt wavy asymmetrical hair + front S-lock + flowing high-right ponytail & gold clasp
  - Olive skin, emerald eyes, subtle muted coral-rose closed mouth, pearl drop earrings
  - Midnight-navy Admiral shoulder cape with upturned collar piping, compact gold epaulets & double hem braid
  - Crisp ice-white open blouse, brown belt with gold buckle, dark navy trousers
  - Chestnut riding boots with gold upper rim trim and cool silver-steel forward toes
"""

from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
REF_BATTLE = Path(
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795597451912_b8e8dd26.png"
)

BLACK = (0, 0, 0, 255)
INK_HAIR = (20, 23, 52, 255)
HAIR_DARK = (39, 43, 88, 255)      # #272b58
HAIR_MID = (53, 60, 129, 255)      # #353c81
HAIR_LIGHT = (78, 94, 185, 255)    # #4e5eb9
HAIR_SPEC = (103, 127, 220, 255)   # #677fdc

INK_SKIN = (74, 42, 40, 255)
SKIN_DEEP = (138, 88, 72, 255)
SKIN_SHADOW = (168, 121, 98, 255)
SKIN_BASE = (199, 161, 138, 255)   # #c7a18a
SKIN_LIGHT = (221, 185, 160, 255)
LIP_MUTED = (168, 88, 78, 255)     # subtle terracotta-rose lip matching battle sprite

EYE_TEAL = (24, 72, 66, 255)
EYE_EMERALD = (73, 155, 135, 255)  # #499b87
PEARL_LIGHT = (238, 238, 247, 255) # #eeeef7
PEARL_SHAD = (146, 167, 185, 255)  # #92a7b9

INK_GOLD = (94, 54, 16, 255)
GOLD_SHAD = (180, 109, 35, 255)    # #b46d23
GOLD_BRIGHT = (237, 189, 98, 255)  # #edbd62

CAPE_DARK = (35, 29, 54, 255)      # #231d36
CAPE_MID = (53, 51, 74, 255)       # #35334a
CAPE_LIGHT = (85, 90, 112, 255)    # #555a70

BLOUSE_WHITE = (238, 238, 247, 255)
BLOUSE_SHAD = (146, 167, 185, 255)

BOOT_DARK = (83, 36, 40, 255)      # #532428
BOOT_MID = (132, 74, 70, 255)
STEEL_LIGHT = (238, 238, 247, 255)
STEEL_SHAD = (146, 167, 185, 255)


def extract_native_cell(im: Image.Image, col: int, row: int) -> list[list[tuple]]:
    px = im.load()
    return [
        [
            px[col * 64 + nx * 2, row * 64 + ny * 2]
            if px[col * 64 + nx * 2, row * 64 + ny * 2][3] == 255
            else (0, 0, 0, 0)
            for nx in range(32)
        ]
        for ny in range(32)
    ]


def paint_px(grid: list[list[tuple]], x: int, y: int, col: tuple):
    if 0 <= x < 32 and 0 <= y < 32:
        grid[y][x] = col


def recolor_053_head(grid: list[list[tuple]], row: int) -> list[list[tuple]]:
    """Recolor trchar053 idle head cleanly into cobalt hair, olive skin, emerald eyes, subtle mouth & pearls."""
    h_map = {
        (139, 81, 46): HAIR_DARK,      # A
        (113, 72, 45): HAIR_DARK,      # K
        (200, 131, 70): HAIR_MID,      # B
        (255, 188, 118): HAIR_LIGHT,   # C
        (255, 207, 127): HAIR_LIGHT,   # V
        (255, 246, 180): HAIR_SPEC,    # E
        (63, 36, 28): INK_HAIR,        # D
        (63, 35, 28): INK_HAIR,        # F
        (0, 0, 0): INK_HAIR,           # J
        (13, 13, 15): INK_HAIR,        # S
        (207, 150, 111): SKIN_DEEP,    # G
        (222, 164, 123): SKIN_SHADOW,  # P
        (247, 207, 182): SKIN_BASE,    # H
        (255, 213, 189): SKIN_LIGHT,   # R
        (120, 64, 66): INK_SKIN,       # N
        (65, 58, 53): INK_SKIN,        # O
        (238, 238, 247): PEARL_LIGHT,  # I
        (206, 74, 57): PEARL_LIGHT,    # Q earrings -> pearl drop
        (163, 42, 26): HAIR_DARK,      # L
        (116, 0, 0): INK_SKIN,         # M chin shadow
    }
    out = [[(0, 0, 0, 0) for _ in range(32)] for _ in range(32)]
    max_y = 18 if row == 3 else 19
    for ny in range(max_y + 1):
        for nx in range(32):
            c = grid[ny][nx]
            if c[3] != 255:
                continue
            out[ny][nx] = h_map.get(c[:3], c)

    if row == 0:  # Down
        for ny in (14, 15):
            for nx in (12, 13, 18, 19):
                if out[ny][nx] == INK_HAIR:
                    out[ny][nx] = EYE_TEAL if ny == 14 else EYE_EMERALD
        if out[15][10] == PEARL_LIGHT:
            out[16][10] = PEARL_SHAD
        if out[15][21] == PEARL_LIGHT:
            out[16][21] = PEARL_SHAD
        # Smooth jaw + subtle muted 2x1 mouth right above the chin
        out[17][13] = SKIN_SHADOW
        out[17][14] = SKIN_BASE
        out[17][15] = LIP_MUTED
        out[17][16] = LIP_MUTED
        out[17][17] = SKIN_BASE
        out[17][18] = SKIN_SHADOW
        out[18][13] = INK_SKIN
        out[18][14] = INK_SKIN
        out[18][15] = SKIN_SHADOW
        out[18][16] = SKIN_SHADOW
        out[18][17] = INK_SKIN
        out[18][18] = INK_SKIN
        for nx in range(21, 25):
            out[19][nx] = (0, 0, 0, 0)
        for nx in (22, 23):
            if out[18][nx] != (0, 0, 0, 0):
                out[18][nx] = INK_HAIR
    elif row == 1:  # Left
        for ny in (14, 15):
            for nx in (13, 14):
                if out[ny][nx] == INK_HAIR:
                    out[ny][nx] = EYE_TEAL if ny == 14 else EYE_EMERALD
        # Pearl drop earring (trchar053 Left earring was L at 18,16)
        out[16][18] = PEARL_LIGHT
        out[17][18] = PEARL_SHAD
        # Keep outer jaw smooth (orig 11,17 -> shifted nx=10) & place subtle 1px closed mouth inset at (12,17 -> shifted 11,17)
        out[17][11] = SKIN_SHADOW
        out[17][12] = LIP_MUTED
        for nx in range(18, 25):
            out[19][nx] = (0, 0, 0, 0)
    elif row == 2:  # Right
        for ny in (14, 15):
            for nx in (17, 18):
                if out[ny][nx] == INK_HAIR:
                    out[ny][nx] = EYE_TEAL if ny == 14 else EYE_EMERALD
        out[16][13] = PEARL_LIGHT
        out[17][13] = PEARL_SHAD
        out[17][20] = SKIN_SHADOW
        out[17][19] = LIP_MUTED
        for nx in range(7, 14):
            out[19][nx] = (0, 0, 0, 0)
    elif row == 3:  # Up
        for nx in (7, 8, 23, 24):
            out[18][nx] = (0, 0, 0, 0)
        out[18][9] = INK_HAIR
        out[18][22] = INK_HAIR
        # Soft cohesive curved crown sheen sweeping cleanly up-right toward the ponytail clasp
        for nx in range(11, 20):
            out[7][nx] = HAIR_MID
        for nx in range(12, 19):
            out[6][nx] = HAIR_LIGHT
        for nx in (14, 15, 16, 17):
            out[5][nx] = HAIR_LIGHT
        out[6][17] = HAIR_SPEC
        out[6][18] = HAIR_SPEC
        out[7][18] = HAIR_LIGHT
        out[7][19] = HAIR_SPEC
        out[7][20] = HAIR_LIGHT
        out[8][10] = HAIR_MID
        out[8][11] = HAIR_LIGHT
        out[8][19] = HAIR_LIGHT
        out[8][20] = HAIR_SPEC
        out[9][10] = HAIR_MID
        out[9][21] = HAIR_MID

    return out


def recolor_061_body(grid: list[list[tuple]], row: int, col: int) -> list[list[tuple]]:
    """Extract and recolor trchar061 body (ny >= 18) into midnight-navy Admiral cape & attire."""
    b_map = {
        (0, 0, 0): BLACK,
        (41, 43, 84): CAPE_DARK,       # E cape deep navy
        (55, 56, 111): CAPE_DARK,      # L cape deep navy
        (67, 70, 139): CAPE_MID,       # F cape slate navy
        (86, 91, 208): CAPE_LIGHT,     # G cape cool highlight
        (43, 43, 43): CAPE_DARK,       # Q dark navy trousers / lower boot
        (83, 83, 83): CAPE_MID,        # R trousers mid
        (75, 75, 75): CAPE_LIGHT,      # X chest detail
        (162, 66, 66): CAPE_DARK,      # S inner cape flap -> deep navy
        (245, 104, 94): CAPE_MID,      # U inner cape fold -> slate navy
        (228, 233, 237): BLOUSE_WHITE, # P white sleeve
        (189, 197, 205): BLOUSE_SHAD,  # N white sleeve shadow
        (232, 232, 248): BLOUSE_WHITE, # K
        (194, 189, 217): BLOUSE_SHAD,  # I
        (222, 164, 123): SKIN_SHADOW,  # H hand
        (224, 167, 124): SKIN_SHADOW,  # W hand
        (255, 213, 189): SKIN_BASE,    # M hand light
        (254, 214, 191): SKIN_BASE,    # Y hand light
        (112, 56, 56): INK_SKIN,       # J hand outline
        (120, 64, 64): INK_SKIN,       # O collar outline
        (153, 94, 85): INK_SKIN,       # A
        (103, 63, 56): CAPE_DARK,      # V nape under cape collar
    }
    out = [[(0, 0, 0, 0) for _ in range(32)] for _ in range(32)]
    for ny in range(18, 32):
        for nx in range(32):
            c = grid[ny][nx]
            if c[3] != 255:
                continue
            rgb = c[:3]
            if rgb == (248, 217, 104):
                out[ny][nx] = STEEL_LIGHT if ny >= 27 else CAPE_MID
            else:
                out[ny][nx] = b_map.get(rgb, c)
    return out


def add_hair_volume_and_ponytail(grid: list[list[tuple]], row: int, dy_step: int):
    """Add rich wavy volume, extra left-cheek S-lock, and high-right gold-clasped ponytail."""
    def s(x, y, c):
        paint_px(grid, x, y + dy_step, c)

    if row == 0:  # Down
        # Subtle lofted top crown + curved specular wave
        for nx in range(13, 19):
            s(nx, 2, INK_HAIR)
        s(12, 3, HAIR_MID); s(13, 3, HAIR_LIGHT); s(14, 3, HAIR_LIGHT); s(15, 3, HAIR_SPEC)
        s(16, 3, HAIR_LIGHT); s(17, 3, HAIR_MID); s(18, 3, HAIR_MID)
        # Lush curved outer-left S-wave lock (smooth organic curve without straight block step)
        s(8, 6, HAIR_MID); s(7, 7, INK_HAIR); s(8, 7, HAIR_LIGHT)
        s(6, 8, INK_HAIR); s(7, 8, HAIR_LIGHT); s(8, 8, HAIR_SPEC)
        s(6, 9, INK_HAIR); s(7, 9, HAIR_SPEC); s(8, 9, HAIR_LIGHT)
        s(7, 10, HAIR_LIGHT); s(8, 10, HAIR_LIGHT)
        s(7, 14, HAIR_LIGHT); s(8, 14, HAIR_LIGHT)
        s(6, 15, INK_HAIR); s(7, 15, HAIR_MID)
        s(6, 16, INK_HAIR); s(7, 16, HAIR_MID)
        s(7, 17, INK_HAIR); s(8, 17, HAIR_DARK)
        # Taper front left curl gracefully onto shoulder edge
        s(7, 18, INK_HAIR); s(8, 18, HAIR_MID); s(9, 18, HAIR_DARK)
        # Gold ribbon clasp + fuller cascading right ponytail lock
        s(19, 2, INK_GOLD); s(20, 2, GOLD_BRIGHT); s(21, 2, INK_GOLD)
        s(19, 3, GOLD_SHAD); s(20, 3, GOLD_BRIGHT); s(21, 3, GOLD_BRIGHT); s(22, 3, INK_GOLD)
        s(20, 4, GOLD_SHAD); s(21, 4, GOLD_SHAD); s(22, 4, GOLD_BRIGHT); s(23, 4, INK_HAIR)
        s(22, 5, HAIR_SPEC); s(23, 5, HAIR_SPEC); s(24, 5, HAIR_LIGHT); s(25, 5, INK_HAIR)
        s(23, 6, HAIR_LIGHT); s(24, 6, HAIR_LIGHT); s(25, 6, HAIR_MID); s(26, 6, INK_HAIR)
        s(23, 7, HAIR_MID); s(24, 7, HAIR_MID); s(25, 7, HAIR_DARK); s(26, 7, INK_HAIR)
        s(23, 8, HAIR_MID); s(24, 8, HAIR_DARK); s(25, 8, HAIR_DARK); s(26, 8, INK_HAIR)
        s(24, 9, HAIR_DARK); s(25, 9, INK_HAIR)
    elif row == 1:  # Left
        # Top crown slight lift & wave volume
        for nx in range(13, 19):
            s(nx, 2, INK_HAIR)
        s(12, 3, HAIR_MID); s(13, 3, HAIR_LIGHT); s(14, 3, HAIR_LIGHT); s(15, 3, HAIR_SPEC)
        s(16, 3, HAIR_LIGHT); s(17, 3, HAIR_MID); s(18, 3, HAIR_MID)
        # Plug 1px hole under band (orig nx=21, ny=5 -> after dx_head=-1 is nx=20)
        s(20, 5, HAIR_SPEC)
        # Fuller front wispy wave curl + gold ribbon clasp + flowing curved back ponytail
        s(7, 9, HAIR_MID); s(7, 10, HAIR_LIGHT); s(8, 10, HAIR_LIGHT)
        s(7, 11, INK_HAIR); s(8, 11, HAIR_MID)
        s(19, 3, INK_GOLD); s(20, 3, GOLD_BRIGHT); s(21, 3, GOLD_SHAD); s(22, 3, INK_GOLD)
        s(20, 4, GOLD_SHAD); s(21, 4, GOLD_BRIGHT); s(22, 4, GOLD_SHAD); s(23, 4, INK_GOLD)
        s(21, 5, HAIR_SPEC); s(22, 5, HAIR_SPEC); s(23, 5, HAIR_LIGHT); s(24, 5, HAIR_MID); s(25, 5, INK_HAIR)
        s(21, 6, HAIR_LIGHT); s(22, 6, HAIR_LIGHT); s(23, 6, HAIR_LIGHT); s(24, 6, HAIR_MID); s(25, 6, HAIR_DARK); s(26, 6, INK_HAIR)
        s(21, 7, HAIR_MID); s(22, 7, HAIR_MID); s(23, 7, HAIR_MID); s(24, 7, HAIR_DARK); s(25, 7, HAIR_DARK); s(26, 7, INK_HAIR)
        s(21, 8, HAIR_MID); s(22, 8, HAIR_MID); s(23, 8, HAIR_DARK); s(24, 8, HAIR_DARK); s(25, 8, INK_HAIR)
        s(22, 9, HAIR_DARK); s(23, 9, HAIR_MID); s(24, 9, HAIR_DARK); s(25, 9, INK_HAIR)
        s(22, 10, HAIR_DARK); s(23, 10, HAIR_DARK); s(24, 10, INK_HAIR)
        s(23, 11, HAIR_DARK); s(24, 11, INK_HAIR)
    elif row == 2:  # Right (exact mirror of Left)
        for nx in range(13, 19):
            s(nx, 2, INK_HAIR)
        s(19, 3, HAIR_MID); s(18, 3, HAIR_LIGHT); s(17, 3, HAIR_LIGHT); s(16, 3, HAIR_SPEC)
        s(15, 3, HAIR_LIGHT); s(14, 3, HAIR_MID); s(13, 3, HAIR_MID)
        s(11, 5, HAIR_SPEC)
        s(24, 9, HAIR_MID); s(24, 10, HAIR_LIGHT); s(23, 10, HAIR_LIGHT)
        s(24, 11, INK_HAIR); s(23, 11, HAIR_MID)
        s(12, 3, INK_GOLD); s(11, 3, GOLD_BRIGHT); s(10, 3, GOLD_SHAD); s(9, 3, INK_GOLD)
        s(11, 4, GOLD_SHAD); s(10, 4, GOLD_BRIGHT); s(9, 4, GOLD_SHAD); s(8, 4, INK_GOLD)
        s(10, 5, HAIR_SPEC); s(9, 5, HAIR_SPEC); s(8, 5, HAIR_LIGHT); s(7, 5, HAIR_MID); s(6, 5, INK_HAIR)
        s(10, 6, HAIR_LIGHT); s(9, 6, HAIR_LIGHT); s(8, 6, HAIR_LIGHT); s(7, 6, HAIR_MID); s(6, 6, HAIR_DARK); s(5, 6, INK_HAIR)
        s(10, 7, HAIR_MID); s(9, 7, HAIR_MID); s(8, 7, HAIR_MID); s(7, 7, HAIR_DARK); s(6, 7, HAIR_DARK); s(5, 7, INK_HAIR)
        s(10, 8, HAIR_MID); s(9, 8, HAIR_MID); s(8, 8, HAIR_DARK); s(7, 8, HAIR_DARK); s(6, 8, INK_HAIR)
        s(9, 9, HAIR_DARK); s(8, 9, HAIR_MID); s(7, 9, HAIR_DARK); s(6, 9, INK_HAIR)
        s(9, 10, HAIR_DARK); s(8, 10, HAIR_DARK); s(7, 10, INK_HAIR)
        s(8, 11, HAIR_DARK); s(7, 11, INK_HAIR)
    elif row == 3:  # Up
        for nx in range(13, 19):
            s(nx, 2, INK_HAIR)
        s(12, 3, HAIR_MID); s(13, 3, HAIR_MID); s(14, 3, HAIR_LIGHT); s(15, 3, HAIR_LIGHT)
        s(16, 3, HAIR_LIGHT); s(17, 3, HAIR_MID); s(18, 3, HAIR_MID)
        # Subtle extra left-side wavy lock silhouette for back-view volume
        s(6, 12, INK_HAIR); s(7, 12, HAIR_MID)
        s(6, 13, INK_HAIR); s(7, 13, HAIR_MID)
        s(6, 14, INK_HAIR); s(7, 14, HAIR_DARK)
        # Gold butterfly clasp + lush multi-layered cascading ponytail on right back
        s(18, 3, INK_GOLD); s(19, 3, GOLD_BRIGHT); s(20, 3, INK_GOLD)
        s(18, 4, INK_GOLD); s(19, 4, GOLD_BRIGHT); s(20, 4, GOLD_SHAD); s(21, 4, INK_GOLD)
        s(18, 5, GOLD_SHAD); s(19, 5, GOLD_BRIGHT); s(20, 5, GOLD_SHAD); s(21, 5, INK_GOLD)
        s(21, 5, HAIR_SPEC); s(22, 5, HAIR_LIGHT); s(23, 5, INK_HAIR)
        s(20, 6, HAIR_SPEC); s(21, 6, HAIR_SPEC); s(22, 6, HAIR_LIGHT); s(23, 6, HAIR_LIGHT); s(24, 6, INK_HAIR)
        s(21, 7, INK_HAIR); s(22, 7, HAIR_SPEC); s(23, 7, HAIR_LIGHT); s(24, 7, HAIR_MID); s(25, 7, INK_HAIR)
        s(21, 8, INK_HAIR); s(22, 8, HAIR_LIGHT); s(23, 8, HAIR_LIGHT); s(24, 8, HAIR_MID); s(25, 8, HAIR_DARK); s(26, 8, INK_HAIR)
        s(22, 9, INK_HAIR); s(23, 9, HAIR_LIGHT); s(24, 9, HAIR_MID); s(25, 9, HAIR_DARK); s(26, 9, INK_HAIR)
        s(22, 10, INK_HAIR); s(23, 10, HAIR_MID); s(24, 10, HAIR_MID); s(25, 10, HAIR_DARK); s(26, 10, INK_HAIR)
        s(22, 11, INK_HAIR); s(23, 11, HAIR_MID); s(24, 11, HAIR_DARK); s(25, 11, INK_HAIR)
        s(22, 12, INK_HAIR); s(23, 12, HAIR_MID); s(24, 12, HAIR_DARK); s(25, 12, INK_HAIR)
        s(22, 13, INK_HAIR); s(23, 13, HAIR_DARK); s(24, 13, HAIR_DARK); s(25, 13, INK_HAIR)
        s(22, 14, INK_HAIR); s(23, 14, HAIR_DARK); s(24, 14, INK_HAIR)
        s(22, 15, HAIR_DARK); s(23, 15, HAIR_MID); s(24, 15, INK_HAIR)
        s(21, 16, HAIR_DARK); s(22, 16, HAIR_MID); s(23, 16, INK_HAIR)
        s(21, 17, HAIR_DARK); s(22, 17, INK_HAIR)


def tailor_admiral_body(grid: list[list[tuple]], row: int, dy_step: int, col: int):
    """Tailor midnight-navy Admiral mantle, upturned collar piping, double gold cuffs & steel-toe boots."""
    def s(x, y, c):
        paint_px(grid, x, y + dy_step, c)

    if row == 0:  # Down
        # Upturned Admiral high collar framing neck & ice-white blouse opening
        s(12, 18, CAPE_DARK); s(13, 18, GOLD_SHAD)
        s(18, 18, GOLD_SHAD); s(19, 18, CAPE_DARK)
        s(13, 19, GOLD_SHAD); s(14, 19, BLOUSE_WHITE); s(15, 19, SKIN_BASE); s(16, 19, SKIN_BASE); s(17, 19, BLOUSE_WHITE); s(18, 19, GOLD_SHAD)
        # Compact crisp 2-px gold epaulets
        s(10, 19, BLACK); s(11, 19, GOLD_SHAD); s(12, 19, GOLD_BRIGHT)
        s(19, 19, GOLD_BRIGHT); s(20, 19, GOLD_SHAD); s(21, 19, BLACK)
        s(10, 20, CAPE_DARK); s(11, 20, GOLD_BRIGHT); s(12, 20, CAPE_DARK)
        s(19, 20, CAPE_DARK); s(20, 20, GOLD_BRIGHT); s(21, 20, CAPE_DARK)
        # Open white V-blouse + small gold top pin
        s(13, 20, GOLD_SHAD); s(14, 20, BLOUSE_WHITE); s(15, 20, GOLD_BRIGHT); s(16, 20, BLOUSE_WHITE); s(17, 20, BLOUSE_SHAD); s(18, 20, GOLD_SHAD)
        s(13, 21, CAPE_MID); s(14, 21, BLOUSE_WHITE); s(15, 21, BLOUSE_WHITE); s(16, 21, BLOUSE_SHAD); s(17, 21, CAPE_MID); s(18, 21, CAPE_DARK)
        # Cape flaps & cuff braid kept strictly inside silhouette
        if col in (0, 2):
            s(8, 22, BLOUSE_WHITE); s(9, 22, BLOUSE_WHITE); s(10, 22, CAPE_MID)
            s(21, 22, CAPE_MID); s(22, 22, BLOUSE_WHITE); s(23, 22, BLOUSE_WHITE)
            s(10, 23, GOLD_SHAD); s(11, 23, CAPE_DARK); s(20, 23, CAPE_DARK); s(21, 23, GOLD_SHAD)
            s(8, 24, CAPE_MID); s(9, 24, CAPE_DARK); s(10, 24, CAPE_DARK)
            s(21, 24, CAPE_DARK); s(22, 24, CAPE_DARK); s(23, 24, CAPE_MID)
            s(9, 25, GOLD_BRIGHT); s(10, 25, GOLD_SHAD)
            s(21, 25, GOLD_SHAD); s(22, 25, GOLD_BRIGHT)
        elif col == 1:
            # Stay cleanly inside Down1 silhouette (cols 9..10 left, cols 21..22 right — zero floating pixels!)
            s(9, 24, CAPE_DARK); s(10, 24, GOLD_SHAD)
            s(21, 23, GOLD_SHAD); s(22, 24, GOLD_BRIGHT)
        else:
            s(9, 24, GOLD_BRIGHT); s(10, 23, GOLD_SHAD)
            s(21, 24, GOLD_SHAD); s(22, 24, CAPE_DARK)
        # Belt & buckle
        s(13, 22, BOOT_DARK); s(14, 22, GOLD_SHAD); s(15, 22, GOLD_BRIGHT); s(16, 22, GOLD_BRIGHT); s(17, 22, GOLD_SHAD); s(18, 22, BOOT_DARK)
        s(14, 23, CAPE_MID); s(15, 23, CAPE_DARK); s(16, 23, CAPE_DARK); s(17, 23, CAPE_MID)
        # Chestnut boot shafts + subtle V-gold boot cuff rim above steel toes
        for y in (27, 28, 29):
            for x in range(10, 22):
                if grid[y][x] in (CAPE_DARK, CAPE_MID):
                    if y + 1 < 32 and grid[y + 1][x] == STEEL_LIGHT:
                        grid[y][x] = BOOT_MID
                        if y - 1 >= 26 and grid[y - 1][x] == CAPE_DARK:
                            grid[y - 1][x] = BOOT_DARK
        # Subtle outer 1px bronze-gold rim accent at top boot notch (keeps legs slim, never striped!)
        if col in (0, 2):
            s(12, 26, GOLD_SHAD)
            s(19, 26, GOLD_SHAD)
        elif col == 1:
            s(13, 27, GOLD_SHAD)
        else:
            s(18, 27, GOLD_SHAD)
    elif row == 1:  # Left
        s(17, 18, CAPE_DARK); s(14, 19, GOLD_SHAD); s(15, 19, GOLD_BRIGHT); s(16, 19, GOLD_SHAD); s(17, 19, CAPE_MID)
        # Clearly visible ice-white open front blouse + gold lapel trim + waist belt + shirt tail (matching Down!)
        s(13, 20, BLOUSE_WHITE); s(14, 20, BLOUSE_WHITE); s(15, 20, GOLD_SHAD)
        s(13, 21, BLOUSE_WHITE); s(14, 21, BLOUSE_SHAD); s(15, 21, CAPE_DARK)
        if col in (0, 2):
            s(12, 22, BLOUSE_WHITE); s(13, 22, BLACK)
            s(12, 23, GOLD_BRIGHT)  # front waist belt buckle glint
            s(12, 24, BLOUSE_SHAD)  # subtle white blouse tail peeking under belt
            # Subtle double gold sleeve/mantle band on cape drape + gold boot cuff accent
            s(18, 22, GOLD_SHAD); s(19, 22, GOLD_BRIGHT)
            s(17, 24, GOLD_SHAD); s(18, 24, GOLD_BRIGHT); s(19, 24, GOLD_SHAD)
            s(12, 27, BOOT_MID); s(13, 27, GOLD_BRIGHT); s(14, 27, GOLD_SHAD); s(15, 27, BOOT_DARK)
            s(13, 28, STEEL_SHAD); s(14, 28, STEEL_LIGHT)
        elif col == 1:
            # Arm swinging forward: keep chest & upper front torso crisp white blouse!
            s(13, 21, BLOUSE_WHITE); s(14, 21, BLOUSE_WHITE); s(15, 21, BLOUSE_SHAD)
            s(13, 22, BLOUSE_WHITE); s(14, 22, GOLD_BRIGHT); s(15, 22, BLOUSE_SHAD)
            s(13, 23, BLOUSE_SHAD); s(14, 23, CAPE_MID)
            s(21, 22, GOLD_SHAD); s(22, 22, GOLD_BRIGHT)
            s(21, 24, GOLD_SHAD); s(22, 24, GOLD_BRIGHT); s(23, 24, GOLD_SHAD)
            s(11, 27, GOLD_SHAD)
        else:
            # Arm swinging backward: open white shirt front fully visible!
            s(12, 22, BLOUSE_WHITE); s(13, 22, BLACK)
            s(12, 23, GOLD_BRIGHT)
            s(21, 22, GOLD_SHAD); s(22, 22, GOLD_BRIGHT)
            s(20, 24, GOLD_SHAD); s(21, 24, GOLD_BRIGHT); s(22, 24, GOLD_SHAD)
            s(11, 27, GOLD_SHAD)
    elif row == 2:  # Right (exact mirror of Left)
        s(14, 18, CAPE_DARK); s(17, 19, GOLD_SHAD); s(16, 19, GOLD_BRIGHT); s(15, 19, GOLD_SHAD); s(14, 19, CAPE_MID)
        s(18, 20, BLOUSE_WHITE); s(17, 20, BLOUSE_WHITE); s(16, 20, GOLD_SHAD)
        s(18, 21, BLOUSE_WHITE); s(17, 21, BLOUSE_SHAD); s(16, 21, CAPE_DARK)
        if col in (0, 2):
            s(19, 22, BLOUSE_WHITE); s(18, 22, BLACK)
            s(19, 23, GOLD_BRIGHT)
            s(19, 24, BLOUSE_SHAD)
            s(13, 22, GOLD_SHAD); s(12, 22, GOLD_BRIGHT)
            s(14, 24, GOLD_SHAD); s(13, 24, GOLD_BRIGHT); s(12, 24, GOLD_SHAD)
            s(19, 27, BOOT_MID); s(18, 27, GOLD_BRIGHT); s(17, 27, GOLD_SHAD); s(16, 27, BOOT_DARK)
            s(18, 28, STEEL_LIGHT); s(17, 28, STEEL_SHAD)
        elif col == 1:
            s(18, 21, BLOUSE_WHITE); s(17, 21, BLOUSE_WHITE); s(16, 21, BLOUSE_SHAD)
            s(18, 22, BLOUSE_WHITE); s(17, 22, GOLD_BRIGHT); s(16, 22, BLOUSE_SHAD)
            s(18, 23, BLOUSE_SHAD); s(17, 23, CAPE_MID)
            s(10, 22, GOLD_SHAD); s(9, 22, GOLD_BRIGHT)
            s(10, 24, GOLD_SHAD); s(9, 24, GOLD_BRIGHT); s(8, 24, GOLD_SHAD)
            s(20, 27, GOLD_SHAD)
        else:
            s(19, 22, BLOUSE_WHITE); s(18, 22, BLACK)
            s(19, 23, GOLD_BRIGHT)
            s(10, 22, GOLD_SHAD); s(9, 22, GOLD_BRIGHT)
            s(11, 24, GOLD_SHAD); s(10, 24, GOLD_BRIGHT); s(9, 24, GOLD_SHAD)
            s(20, 27, GOLD_SHAD)
    elif row == 3:  # Up
        for nx in range(13, 19):
            s(nx, 19, CAPE_DARK)
        s(10, 19, BLACK); s(11, 19, GOLD_SHAD); s(12, 19, GOLD_BRIGHT)
        s(19, 19, GOLD_BRIGHT); s(20, 19, GOLD_SHAD); s(21, 19, BLACK)
        s(9, 20, BLACK); s(10, 20, GOLD_SHAD); s(11, 20, CAPE_MID)
        s(20, 20, CAPE_MID); s(21, 20, GOLD_SHAD); s(22, 20, BLACK)
        # Clean double gold Admiral cuff band accent near back cape bottom hem
        if col in (0, 2):
            s(10, 24, GOLD_SHAD); s(11, 24, GOLD_BRIGHT); s(20, 24, GOLD_BRIGHT); s(21, 24, GOLD_SHAD)
            for nx in range(11, 21):
                if nx not in (15, 16):
                    s(nx, 26, GOLD_BRIGHT if nx in (12, 13, 18, 19) else GOLD_SHAD)
        elif col == 1:
            s(11, 24, GOLD_SHAD); s(12, 24, GOLD_BRIGHT); s(21, 24, GOLD_BRIGHT)
            for nx in (11, 12, 13, 21, 22):
                s(nx, 26, GOLD_BRIGHT if nx in (12, 21) else GOLD_SHAD)
        elif col == 3:
            s(10, 24, GOLD_BRIGHT); s(19, 24, GOLD_BRIGHT); s(20, 24, GOLD_SHAD)
            for nx in (9, 10, 18, 19, 20):
                s(nx, 26, GOLD_BRIGHT if nx in (10, 19) else GOLD_SHAD)
        for y in range(27, 31):
            for x in range(32):
                if grid[y][x] == STEEL_LIGHT:
                    grid[y][x] = BOOT_MID

    if row in (1, 2) and col in (1, 3):
        for y in range(27, 31):
            for x in range(32):
                if grid[y][x] == STEEL_LIGHT:
                    is_front = (x <= 15) if row == 1 else (x >= 16)
                    grid[y][x] = STEEL_LIGHT if is_front else BOOT_MID
                elif grid[y][x] in (CAPE_DARK, CAPE_MID) and y >= 28:
                    grid[y][x] = BOOT_DARK


def compose_champion_sheet() -> Image.Image:
    im53 = Image.open(ROOT / "Graphics/Characters/trchar053.png").convert("RGBA")
    im61 = Image.open(ROOT / "Graphics/Characters/trchar061.png").convert("RGBA")

    sheet = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    px_out = sheet.load()

    for row in range(4):
        head_raw = extract_native_cell(im53, 0, row)
        head_base = recolor_053_head(head_raw, row)
        dx_head = -1 if row == 1 else (1 if row == 2 else 0)

        for col in range(4):
            dy_step = 1 if col in (1, 3) else 0
            body_raw = extract_native_cell(im61, col, row)
            cell = recolor_061_body(body_raw, row, col)

            for ny in range(32):
                for nx in range(32):
                    c = head_base[ny][nx]
                    if c[3] != 255:
                        continue
                    tx, ty = nx + dx_head, ny + dy_step
                    if 0 <= tx < 32 and 0 <= ty < 32:
                        cell[ty][tx] = c

            add_hair_volume_and_ponytail(cell, row, dy_step)
            tailor_admiral_body(cell, row, dy_step, col)

            for ny in range(32):
                for nx in range(32):
                    rgba = cell[ny][nx]
                    if rgba[3] == 255:
                        x0 = col * 64 + nx * 2
                        y0 = row * 64 + ny * 2
                        px_out[x0, y0] = rgba
                        px_out[x0 + 1, y0] = rgba
                        px_out[x0, y0 + 1] = rgba
                        px_out[x0 + 1, y0 + 1] = rgba

    return sheet


def verify_sheet(im: Image.Image) -> tuple[int, int, int]:
    px = im.load()
    w, h = im.size
    err2 = sum(
        1
        for y in range(0, h, 2)
        for x in range(0, w, 2)
        if not (px[x, y] == px[x + 1, y] == px[x, y + 1] == px[x + 1, y + 1])
    )
    pa = sum(1 for y in range(h) for x in range(w) if 0 < px[x, y][3] < 255)
    cols = len({px[x, y] for y in range(h) for x in range(w) if px[x, y][3] == 255})
    return err2, pa, cols


def save_outputs(sheet: Image.Image):
    prev = ROOT / "previews"
    prev.mkdir(exist_ok=True)
    sheet.save(prev / "champion_trchar017.png")

    im53 = Image.open(ROOT / "Graphics/Characters/trchar053.png").convert("RGBA")
    im61 = Image.open(ROOT / "Graphics/Characters/trchar061.png").convert("RGBA")
    ref = Image.open(REF_BATTLE).convert("RGBA")

    canvas = Image.new("RGBA", (820, 560), (34, 40, 52, 255))
    draw = ImageDraw.Draw(canvas)
    draw.text((14, 8), "Campeona Rolanda Altamira V6 (Subtle Mouth, Extra Hair Volume & Admiral Trim) - 2x", fill=(238, 240, 245, 255))
    canvas.alpha_composite(sheet.resize((512, 512), Image.NEAREST), (14, 30))

    draw.text((545, 30), "Battle Sprite Ref:", fill=(237, 189, 98, 255))
    canvas.alpha_composite(ref, (555, 52))

    draw.text((545, 232), "1:1 Scale Check:", fill=(180, 200, 230, 255))
    for i in range(4):
        cell = sheet.crop((0, i * 64, 64, (i + 1) * 64))
        canvas.alpha_composite(cell, (545 + (i % 2) * 85, 252 + (i // 2) * 70))

    draw.text((545, 400), "Bases vs Result (2x):", fill=(180, 220, 190, 255))
    for i, (label, src) in enumerate([("053", im53), ("061", im61), ("Rolanda", sheet)]):
        c2 = src.crop((0, 0, 64, 64)).resize((96, 96), Image.NEAREST)
        canvas.alpha_composite(c2, (535 + i * 92, 424))
        draw.text((565 + i * 92, 525), label, fill=(210, 215, 225, 255))

    canvas.save(prev / "champion_review_sheet.png")

    for r, d in enumerate(["Down", "Left", "Right", "Up"]):
        frames = []
        for c in range(4):
            fr = Image.new("RGBA", (128, 128), (112, 168, 108, 255))
            cell = sheet.crop((c * 64, r * 64, (c + 1) * 64, (r + 1) * 64)).resize((128, 128), Image.NEAREST)
            fr.alpha_composite(cell)
            frames.append(fr.convert("P", palette=Image.ADAPTIVE))
        frames[0].save(
            prev / f"anim_champion_{d}.gif",
            save_all=True,
            append_images=frames[1:],
            duration=190,
            loop=0,
        )


if __name__ == "__main__":
    sheet = compose_champion_sheet()
    err2, pa, cols = verify_sheet(sheet)
    assert err2 == 0 and pa == 0, f"Invalid sprite sheet: err2={err2}, pa={pa}"
    save_outputs(sheet)
    print(f"Generated Champion V6 cleanly (err2x2={err2}, partial_alpha={pa}, opaque_colors={cols}).")
