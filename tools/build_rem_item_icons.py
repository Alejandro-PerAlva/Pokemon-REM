#!/usr/bin/env python3
"""
Build and port all missing/placeholder item icons in Graphics/Icons/ for Pokémon REM.

- Ports 22 authentic sprites from Pokémon Añil (7 Gen 9 / tool icons + 15 Mints),
  ensuring exact 48x48 dimensions required by rem_ui.rb (Rect.new(0,0,48,48)).
- Draws 20 custom 24x24-native (48x48 2x2) pixel-art icons for REM key/quest/QOL items:
  * 688 SHEARS, 690 GLOVES, 691 SURFBOARD (matching surfboard overworld!)
  * 716 POKEVIAL, 717 INFINITECANDY, 700 PSYCROWN
  * 682 CALMHERB, 683 CRACKEDWATCH
  * 674..676 NIGHTMAREFRAG1..3, 677..679 LUNARFRAG1..3, 680 DREAMORB, 681 NIGHTMAREORB
  * 684..687 SEALCRYSTAL, SEALABYSS, SEALGLACIER, SEALVOLCANO
"""

import argparse
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS_DIR = os.path.join(ROOT, "Graphics", "Icons")
PREV_DIR = os.path.join(ROOT, "previews")
ANIL_ITEMS = r"C:\Users\apera\Documents\Juegos Rateo\Pokemon Anil v4.14\Graphics\Items"

T = (0, 0, 0, 0)


def px2(img, x, y, col):
    """Set a 2x2 block using 24x24 native grid coordinates (nx, ny in 0..23)."""
    if col[3] == 0 or not (0 <= x < 24 and 0 <= y < 24):
        return
    p = img.load()
    xx, yy = x * 2, y * 2
    p[xx, yy] = col
    p[xx + 1, yy] = col
    p[xx, yy + 1] = col
    p[xx + 1, yy + 1] = col


def draw_grid(grid, cmap):
    """Render a 24x24 character grid onto a crisp 48x48 2x2 RGBA image."""
    im = Image.new("RGBA", (48, 48), T)
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch != "." and ch in cmap:
                px2(im, x, y, cmap[ch])
    return im


def make_auto_outline(grid, bg="."):
    """Optional helper for debugging; all grids define explicit crisp outlines."""
    return grid


# ---------------------------------------------------------------------------
# Custom 24x24 native pixel-art item icons -> crisp 48x48 (2x2)
# ---------------------------------------------------------------------------

def icon_shears():
    # 688 SHEARS: garden bypass pruning shears / tijeras de podar (hawk-beak curved blade + hook anvil, spring, green grips)
    grid = [
        "........................",
        "........................",
        ".........###............",
        ".......##SSs#...........",
        "......#SSSss#....##.....",
        "......#SSs#.....#ss#....",
        "......#SSs#....#sss#....",
        ".......#SS#...#sss#.....",
        ".......#SSs###sss#......",
        "........#ssGGsss#.......",
        "........#ssGGss#........",
        ".......###s##s###.......",
        "......#LHH#ss#HHh#......",
        ".....#LHH#s##s#HHh#.....",
        ".....#LHh#.ss.#hHH#.....",
        "....#LHh#......#hHH#....",
        "....#LHh#......#hHH#....",
        "....#HHh#......#hHH#....",
        ".....#HHh#....#hHH#.....",
        ".....#HHh#....#hHH#.....",
        "......#HHh#..#hHH#......",
        ".......###....###.......",
        "........................",
        "........................",
    ]
    cmap = {
        "#": (20, 26, 36, 255),
        "S": (232, 244, 255, 255),
        "s": (146, 170, 196, 255),
        "G": (244, 200, 68, 255),
        "L": (92, 206, 126, 255),
        "H": (44, 152, 88, 255),
        "h": (24, 96, 56, 255),
    }
    return draw_grid(grid, cmap)


def icon_gloves():
    # 690 GLOVES: heavy reinforced strength gauntlet with golden knuckle plates
    grid = [
        "........................",
        "........................",
        "........................",
        "........###.###.........",
        ".......#MM##MMm#........",
        "....####Mm##Mmm###......",
        "...#MMm#Mm##Mmm#Mm#.....",
        "...#Mmn#Mm##Mmm#mm#.....",
        "...#mmnGGGGGGGGmm#......",
        "....#mmGggGGggGmm#......",
        "....#mmmmmmmmmmmm#......",
        "...###mmmmmmmmmmm#......",
        "..#MMm#mmmmmmmmm#.......",
        "..#mmn#mmmmddmmm#.......",
        "...#mmndddddddd#........",
        "....##dddddddddd#.......",
        ".....#dCCCCCCCCd#.......",
        ".....#dCccCCccCd#.......",
        "......#dddddddd#........",
        ".......########.........",
        "........................",
        "........................",
        "........................",
        "........................",
    ]
    cmap = {
        "#": (20, 22, 32, 255),
        "M": (132, 144, 168, 255),
        "m": (86, 94, 114, 255),
        "n": (58, 64, 80, 255),
        "G": (248, 196, 64, 255),
        "g": (208, 128, 24, 255),
        "d": (56, 48, 60, 255),
        "C": (224, 124, 40, 255),
        "c": (160, 72, 24, 255),
    }
    return draw_grid(grid, cmap)


def icon_surfboard():
    # 691 SURFBOARD: broad top-down surfboard viewed from above (~45 deg) with white deck, sky-blue rails,
    # coral-red center stripe & dark traction pad (100% matches overworld surfboard colors!)
    c_outline = (20, 34, 62, 255)
    c_white_hi = (252, 254, 255, 255)
    c_white_sh = (224, 236, 248, 255)
    c_blue_hi = (118, 192, 236, 255)
    c_blue_sh = (68, 134, 186, 255)
    c_coral_hi = (242, 88, 76, 255)
    c_coral_sh = (188, 48, 52, 255)
    c_pad_hi = (52, 66, 94, 255)
    c_pad_sh = (34, 44, 68, 255)
    c_rail_3d = (146, 176, 206, 255)

    # First mark deck interior in 24x24 coordinates
    deck = [[None for _ in range(24)] for _ in range(24)]
    cx, cy = 11.5, 11.5
    inv_s2 = 1.0 / (2.0 ** 0.5)
    half_len = 8.9  # interior nose->tail span (~18 px + 2px outline = ~20 px diagonal)

    for y in range(24):
        for x in range(24):
            u = ((x - cx) - (y - cy)) * inv_s2  # + towards top-right nose, - towards bottom-left tail
            v = ((x - cx) + (y - cy)) * inv_s2  # + towards bottom-right rail, - towards top-left rail
            t = u / half_len
            if -1.0 <= t <= 1.0:
                if t >= 0.0:
                    # Pointed yet smooth surfboard nose taper
                    hw = 3.7 * (1.0 - (t ** 1.75)) + 0.15
                else:
                    # Gentle taper toward classic rounded-squash surf tail
                    hw = 3.7 * (1.0 - 0.52 * ((-t) ** 2.1))
                if abs(v) <= hw:
                    av = abs(v)
                    if -0.88 <= t <= -0.54 and av <= hw - 0.55:
                        # Clean ribbed dark traction grip pad at tail
                        deck[y][x] = c_pad_hi if v <= 0 else c_pad_sh
                    elif av <= 0.88 and t > -0.88:
                        # Iconic coral-red center racing stripe (stops cleanly at tail pad)
                        deck[y][x] = c_coral_hi if v <= 0.1 else c_coral_sh
                    elif av >= hw - 1.15:
                        # Sky-blue outer rails along curved edges
                        deck[y][x] = c_blue_hi if v <= 0 else c_blue_sh
                    else:
                        # Crisp white surfboard deck (and clean white tail lip below pad)
                        deck[y][x] = c_white_hi if v <= 0 else c_white_sh

    # Add subtle 1px 3D board rail underside beneath lower-right edge before outline
    body = [row[:] for row in deck]
    for y in range(1, 23):
        for x in range(1, 23):
            if deck[y][x] is None and (deck[y - 1][x] is not None or deck[y][x - 1] is not None):
                # Only under the shaded bottom-right edge for subtle surfboard thickness
                v = ((x - cx) + (y - cy)) * inv_s2
                if v > 1.2:
                    body[y][x] = c_rail_3d

    im = Image.new("RGBA", (48, 48), T)
    for y in range(24):
        for x in range(24):
            if body[y][x] is not None:
                px2(im, x, y, body[y][x])
            else:
                # 4-connected crisp outline
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 24 and 0 <= ny < 24 and body[ny][nx] is not None:
                        px2(im, x, y, c_outline)
                        break
    return im


def icon_pokevial():
    # 716 POKEVIAL: crystal portable flask with glowing aquamarine water + Poké-red cork/cap
    grid = [
        "........................",
        "........................",
        ".........######.........",
        "........#RRRRRR#........",
        "........#Rrrrrr#........",
        "........########........",
        "........#GGGGGG#........",
        ".........#GGGG#.........",
        "........#GggggG#........",
        "......###GggggG###......",
        ".....#GGggWWWWggGG#.....",
        "....#GGgCCCCCCCCggG#....",
        "....#GgCCWCCCCCCcgG#....",
        "....#GgCCWCCWWCCcgG#....",
        "....#GgCCCCCCCCccgG#....",
        "....#GgCCcccccccccG#....",
        "....#GgCccccccccccG#....",
        ".....#GcccccccccaG#.....",
        ".....#GaaaaaaaaaaG#.....",
        "......#GGGGGGGGGG#......",
        ".......##########.......",
        "........................",
        "........................",
        "........................",
    ]
    cmap = {
        "#": (22, 34, 52, 255),
        "R": (232, 64, 64, 255),
        "r": (160, 30, 38, 255),
        "G": (212, 240, 250, 255),
        "g": (136, 198, 224, 255),
        "W": (248, 254, 255, 255),
        "C": (64, 232, 242, 255),
        "c": (28, 176, 204, 255),
        "a": (18, 128, 164, 255),
    }
    return draw_grid(grid, cmap)


def icon_psycrown():
    # 700 PSYCROWN: silver circlet headband with bright amethyst gem (Psyduck relic)
    grid = [
        "........................",
        "........................",
        "........................",
        "........................",
        "..........####..........",
        ".........#SSss#.........",
        "....##..#SSPPss#..##....",
        "...#Ss##SSPWPPss##sS#...",
        "..#SsSSSssPPPPssSSssS#..",
        "..#SssSSsssPPsssSSssS#..",
        "..#SssssssssssssssssS#..",
        "...#Sss########sssSS#...",
        "...#ss#........#sss#....",
        "....###........###......",
        ".........W..............",
        "........WWW.............",
        ".........W..............",
        "........................",
        "........................",
        "........................",
        "........................",
        "........................",
        "........................",
        "........................",
    ]
    cmap = {
        "#": (28, 24, 44, 255),
        "S": (212, 222, 238, 255),
        "s": (126, 138, 162, 255),
        "P": (184, 72, 248, 255),
        "W": (244, 212, 255, 255),
    }
    return draw_grid(grid, cmap)


def icon_crackedwatch():
    # 683 CRACKEDWATCH: antique gold pocket watch with asymmetric hands & diagonal crack
    grid = [
        "........................",
        "..........####..........",
        ".........#GGGG#.........",
        ".........#G..G#.........",
        "..........####..........",
        ".........#GggG#.........",
        ".......###GGGG###.......",
        "......#GGGggggGGG#......",
        ".....#GGffffffffGG#.....",
        "....#GffXffffffffgG#....",
        "....#GfffXfffffffgG#....",
        "...#GfffffXfffffffgG#...",
        "...#GfffhffXhfffffgG#...",
        "...#GffffhfhXfffffgG#...",
        "...#GfffffffhXffffgG#...",
        "....#GffffffffXffgG#....",
        "....#GfffffffffXfgG#....",
        ".....#GGffffffffGG#.....",
        "......#GGGggggGGG#......",
        ".......###GGGG###.......",
        "..........####..........",
        "........................",
        "........................",
        "........................",
    ]
    cmap = {
        "#": (38, 26, 12, 255),
        "G": (246, 202, 72, 255),
        "g": (184, 122, 24, 255),
        "f": (248, 240, 214, 255),
        "h": (44, 60, 96, 255),
        "X": (36, 24, 48, 255),
    }
    return draw_grid(grid, cmap)


def icon_calmherb():
    # 682 CALMHERB: calming aromatic lavender & sage herbal sprig
    grid = [
        "........................",
        "........................",
        ".............###........",
        "............#LLL#.......",
        ".........###LllL#.......",
        "........#LLLl#LL#.......",
        ".......#LllLL#G#........",
        "........#LllG#G###......",
        "......###G##GG#LLL#.....",
        ".....#SSgG#G#LllL#......",
        ".....#SssGG##LL##.......",
        "......##GGGsG##.........",
        ".......#GsGssG#.........",
        "......#GG#G###..........",
        ".....#GG#SssG#..........",
        "......###SSgG#..........",
        "......#GG###............",
        ".....#GG#...............",
        "....#GG#................",
        ".....##.................",
        "........................",
        "........................",
        "........................",
        "........................",
    ]
    cmap = {
        "#": (24, 34, 28, 255),
        "G": (68, 148, 108, 255),
        "g": (42, 104, 72, 255),
        "S": (124, 204, 158, 255),
        "s": (84, 168, 124, 255),
        "L": (204, 172, 252, 255),
        "l": (146, 102, 218, 255),
    }
    return draw_grid(grid, cmap)


def make_shard(palette_dict):
    # Base jagged crystal shard silhouette (distinguished clearly by mineral style/glyph)
    grid = [
        "........................",
        "........................",
        ".............###........",
        "............#AAA#.......",
        "...........#AAaaA#......",
        "..........#AAAaaa#......",
        ".........#AWAAaaa#......",
        "........#AWWAAaaB#......",
        ".......#AAWAAaaaB#......",
        "......#AAAaaAAaaB#......",
        "......#AAaaBBBBBB#......",
        ".....#AAaaBBBBBB#.......",
        ".....#AaaBBBBbBB#.......",
        ".....#AaBBBBbbB#........",
        "......#aBBBbbB#.........",
        "......#BBBBbb#..........",
        ".......#BBBB#...........",
        "........#BB#............",
        ".........##.............",
        "........................",
        "........................",
        "........................",
        "........................",
        "........................",
    ]
    return draw_grid(grid, palette_dict)


def make_crescent_shard(palette_dict):
    # Distinct curved lunar fragment silhouette
    grid = [
        "........................",
        "........................",
        ".............####.......",
        "..........###AWWA#......",
        "........##AAWWWW#.......",
        ".......#AAWWAAa#........",
        "......#AWWAaa##.........",
        ".....#AWAAa##....G......",
        "....#AAAaa#.....GGG.....",
        "....#AAaa#.......G......",
        "....#AAaa#..............",
        "....#AaaBB#.............",
        ".....#AaBBB##...........",
        "......#aBBBB###.........",
        ".......#BBBBbBBA#.......",
        "........##BBBBb#........",
        "..........#####.........",
        "........................",
        "........................",
        "........................",
        "........................",
        "........................",
        "........................",
        "........................",
    ]
    return draw_grid(grid, palette_dict)


def make_orb(c_out, c_hi, c_mid, c_sh, c_glyph, glyph_type="moon"):
    # Luminous spherical orb with distinct inner symbol
    grid = [
        "........................",
        "........................",
        "........................",
        ".........######.........",
        ".......##HHHHHH##.......",
        "......#HHWWWWMMMM#......",
        ".....#HHWWMMMMMMMM#.....",
        "....#HHWMMGGGGMMSSS#....",
        "....#HMMGGGMMMSSSSS#....",
        "...#HMMGGMMMMSSSSSSS#...",
        "...#HMMGGMMMMSSSSSSS#...",
        "...#MMMGGGMMMMSSSSSS#...",
        "...#MMMMGGGGGSSSSSSS#...",
        "....#MMMMMMSSSSSSSS#....",
        "....#SSSSSSSSSSSSSS#....",
        ".....#SSSSSSSSSSSS#.....",
        "......#SSSSSSSSSS#......",
        ".......##SSSSSS##.......",
        ".........######.........",
        "........................",
        "........................",
        "........................",
        "........................",
        "........................",
    ]
    if glyph_type == "nightmare":
        # Swirl/crack dark mist core instead of crescent moon
        grid[7]  = "....#HHWMMSSGGGSSSS#...."
        grid[8]  = "....#HMMGGGGMGSSSSS#...."
        grid[9]  = "...#HMMGGMMGGMSSSSSS#..."
        grid[10] = "...#MMMGGMMGGMSSSSSS#..."
        grid[11] = "...#SMMMGGGGMMSSSSSS#..."
        grid[12] = "...#SSSMMGGGGGSSSSSS#..."
    cmap = {
        "#": c_out,
        "H": c_hi,
        "W": (255, 255, 255, 255),
        "M": c_mid,
        "S": c_sh,
        "G": c_glyph,
    }
    return draw_grid(grid, cmap)


def make_seal(c_out, c_hi, c_mid, c_sh, c_glyph):
    # Carved hexagonal grotto stone seal with bright glowing center rune
    grid = [
        "........................",
        "........................",
        "........................",
        ".........######.........",
        "........#HHHHHH#........",
        ".......#HMMMMMMH#.......",
        "......#HMHHGGHHMS#......",
        ".....#HMMHGGGGHMSS#.....",
        "....#HMMMGGWWGGMMSS#....",
        "....#HMMGGWGGWGGMSS#....",
        "....#HMMGGWGGWGGMSS#....",
        "....#HMMMGGWWGGMMSS#....",
        ".....#SMMHGGGGHMSS#.....",
        "......#SMHHGGHHSS#......",
        ".......#SSSSSSSS#.......",
        "........#SSSSSS#........",
        ".........######.........",
        "........................",
        "........................",
        "........................",
        "........................",
        "........................",
        "........................",
        "........................",
    ]
    cmap = {
        "#": c_out,
        "H": c_hi,
        "M": c_mid,
        "S": c_sh,
        "G": c_glyph,
        "W": (248, 254, 255, 255),
    }
    return draw_grid(grid, cmap)


def icon_sleepingbag():
    # 719 SLEEPINGBAG: cozy quilted indigo sleeping bag with cream pillow hood, warm amber collar & gold zipper
    grid = [
        "........................",
        "........................",
        "............######......",
        "..........##BBBBbb#.....",
        ".........#BB#WWWW#b#....",
        "........#BB#WWWCCC#b#...",
        ".......#BB#WWCCoOO#b#...",
        "......#BB#ooOOOOoo#bd#..",
        ".....#BB#oOOOOoo#bbd#...",
        "....#BBb##oooo##bbbd#...",
        "...#BBbbb######bbbG#....",
        "...#BbbbdddddddbbGG#....",
        "..#BBbbbbbbbbbbbdd#.....",
        "..#Bbbbbdddddbbbd#......",
        "..#dbbbbbbbbbbbd#.......",
        "..#Bbbbddddbbbd#........",
        "...#bbbbbbbbbd#.........",
        "...#ddbbbbddd#..........",
        "....#bbbdddd#...........",
        ".....#######............",
        "........................",
        "........................",
        "........................",
        "........................",
    ]
    cmap = {
        "#": (18, 24, 44, 255),
        "B": (96, 144, 212, 255),
        "b": (54, 92, 158, 255),
        "d": (34, 58, 112, 255),
        "W": (250, 244, 228, 255),
        "C": (222, 206, 176, 255),
        "O": (244, 152, 64, 255),
        "o": (198, 102, 34, 255),
        "G": (246, 208, 78, 255),
    }
    return draw_grid(grid, cmap)


def icon_reloj():
    # 720 RELOJ: sleek 24h digital wristwatch with sculpted straps, gunmetal chamfered bezel & crisp cyan 12:00
    grid = [
        "........................",
        "......###########.......",
        ".....#SSsssssssSs#......",
        ".....#SdddddddddS#......",
        ".....#SsssGGGsssS#......",
        "..###################...",
        ".#MMMMMMMMMMMMMMMMMMm#..",
        ".#MKKKKKKKKKKKKKKKKKm#..",
        ".#MGGKKKKKKKKKKKKKYKm##.",
        ".#MGKKKKKKKKKKKKKKKKmB#.",
        ".#MKCKCCCKKKCCCKCCCKm##.",
        ".#MKCKKKCKCKCKCKCKCKm#..",
        ".#MKCKCCCKKKCKCKCKCKm#..",
        ".#MKCKCKKKCKCKCKCKCKm##.",
        ".#MKCKCCCKKKCCCKCCCKmB#.",
        ".#MKKKKKKKKKKKKKKKKKm##.",
        ".#mKKKKKKKKKKKKKKKKKm#..",
        ".#mmmmmmmmmmmmmmmmmmm#..",
        "..###################...",
        ".....#SsssGGGsssS#......",
        ".....#SdddddddddS#......",
        ".....#SsssssssssS#......",
        "......###########.......",
        "........................",
    ]
    cmap = {
        "#": (16, 20, 32, 255),
        "S": (72, 84, 108, 255),
        "s": (52, 60, 80, 255),
        "d": (34, 40, 56, 255),
        "M": (132, 148, 174, 255),
        "m": (82, 94, 118, 255),
        "B": (188, 204, 226, 255),
        "K": (10, 14, 24, 255),
        "G": (82, 116, 152, 255),
        "Y": (248, 208, 84, 255),
        "C": (86, 228, 255, 255),
    }
    return draw_grid(grid, cmap)


def build_custom_icons():
    return {
        674: make_shard({"#": (18, 12, 32, 255), "A": (98, 60, 152, 255), "a": (58, 34, 96, 255), "B": (38, 22, 68, 255), "b": (24, 16, 46, 255), "W": (188, 148, 240, 255)}),
        675: make_shard({"#": (14, 28, 24, 255), "A": (72, 168, 132, 255), "a": (42, 112, 86, 255), "B": (26, 74, 58, 255), "b": (18, 48, 38, 255), "W": (160, 236, 200, 255)}),
        676: make_shard({"#": (16, 14, 20, 255), "A": (84, 76, 108, 255), "a": (54, 48, 72, 255), "B": (34, 30, 44, 255), "b": (22, 18, 28, 255), "W": (148, 136, 180, 255)}),
        677: make_crescent_shard({"#": (40, 48, 68, 255), "A": (212, 224, 244, 255), "a": (152, 172, 204, 255), "B": (112, 132, 168, 255), "b": (76, 92, 124, 255), "W": (250, 254, 255, 255), "G": (255, 220, 96, 255)}),
        678: make_crescent_shard({"#": (44, 62, 88, 255), "A": (232, 244, 255, 255), "a": (180, 212, 242, 255), "B": (132, 178, 224, 255), "b": (92, 138, 188, 255), "W": (255, 255, 255, 255), "G": (144, 228, 255, 255)}),
        679: make_crescent_shard({"#": (32, 48, 42, 255), "A": (196, 218, 210, 255), "a": (128, 168, 152, 255), "B": (72, 156, 112, 255), "b": (44, 104, 72, 255), "W": (240, 255, 246, 255), "G": (96, 232, 148, 255)}),
        680: make_orb((36, 48, 76, 255), (224, 238, 255, 255), (168, 198, 236, 255), (108, 144, 196, 255), (255, 244, 188, 255), glyph_type="moon"),
        681: make_orb((20, 14, 28, 255), (96, 84, 118, 255), (64, 52, 80, 255), (36, 28, 48, 255), (172, 92, 236, 255), glyph_type="nightmare"),
        682: icon_calmherb(),
        683: icon_crackedwatch(),
        684: make_seal((32, 52, 76, 255), (218, 244, 255, 255), (144, 206, 242, 255), (84, 152, 204, 255), (112, 236, 255, 255)),
        685: make_seal((14, 22, 52, 255), (72, 128, 224, 255), (36, 76, 176, 255), (22, 46, 124, 255), (80, 228, 255, 255)),
        686: make_seal((22, 34, 48, 255), (104, 144, 178, 255), (66, 98, 132, 255), (42, 64, 92, 255), (84, 240, 172, 255)),
        687: make_seal((48, 28, 12, 255), (242, 196, 72, 255), (204, 136, 36, 255), (148, 86, 20, 255), (255, 112, 40, 255)),
        688: icon_shears(),
        690: icon_gloves(),
        691: icon_surfboard(),
        700: icon_psycrown(),
        716: icon_pokevial(),
        719: icon_sleepingbag(),
        720: icon_reloj(),
    }


def fit_anil_mint_48(src_path):
    """Fit 52x52 Añil Mint neatly into crisp 48x48 matching rem_ui.rb Rect(0,0,48,48)."""
    im = Image.open(src_path).convert("RGBA")
    # Añil mints are 52x38 inside 52x52 -> clean aspect-preserving resize to 46x34 -> centered in 48x48
    bb = im.getbbox()
    cropped = im.crop(bb)  # 52x38
    resized = cropped.resize((46, 34), Image.NEAREST)
    canvas = Image.new("RGBA", (48, 48), T)
    canvas.paste(resized, (1, 7), resized)
    return canvas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write all 42 icons to Graphics/Icons/")
    args = parser.parse_args()

    os.makedirs(PREV_DIR, exist_ok=True)
    icons = build_custom_icons()

    # Exact 48x48 native Añil ports
    anil_48 = {
        689: "ROCKSMASHITEM.png",
        694: "COVERTCLOAK.png",
        695: "CLEARAMULET.png",
        696: "LOADEDDICE.png",
        697: "MIRRORHERB.png",
        698: "PUNCHINGGLOVE.png",
        699: "FAIRYFEATHER.png",
    }
    for iid, fn in anil_48.items():
        icons[iid] = Image.open(os.path.join(ANIL_ITEMS, fn)).convert("RGBA")

    # 15 Mints fitted neatly into 48x48
    mints = {
        701: "ADAMANTMINT.png",
        702: "JOLLYMINT.png",
        703: "MODESTMINT.png",
        704: "TIMIDMINT.png",
        705: "BOLDMINT.png",
        706: "CALMMINT.png",
        707: "IMPISHMINT.png",
        708: "CAREFULMINT.png",
        709: "BRAVEMINT.png",
        710: "QUIETMINT.png",
        711: "RELAXEDMINT.png",
        712: "SASSYMINT.png",
        713: "NAIVEMINT.png",
        714: "HASTYMINT.png",
        715: "SERIOUSMINT.png",
    }
    for iid, fn in mints.items():
        icons[iid] = fit_anil_mint_48(os.path.join(ANIL_ITEMS, fn))

    # Assert strict 48x48 on every output!
    for iid, im in sorted(icons.items()):
        assert im.size == (48, 48), f"item{iid:03d} size {im.size} != (48, 48)"

    # Build combined visual inspection sheet (dark REM Bag style background + light labels)
    ordered_ids = sorted(icons.keys())
    cols = 7
    rows = (len(ordered_ids) + cols - 1) // cols
    cell = 96
    preview = Image.new("RGBA", (cols * cell, rows * cell), (24, 27, 36, 255))
    d = ImageDraw.Draw(preview)

    # Read names for clean preview labels
    id_names = {}
    for line in open(os.path.join(ROOT, "PBS", "items.txt"), encoding="utf-8-sig"):
        p = line.strip().split(",", 6)
        if p[0].isdigit():
            id_names[int(p[0])] = p[2]

    for idx, iid in enumerate(ordered_ids):
        r, c = divmod(idx, cols)
        x0, y0 = c * cell, r * cell
        d.rectangle([x0 + 4, y0 + 4, x0 + cell - 4, y0 + cell - 4], fill=(32, 36, 48, 255), outline=(54, 62, 82, 255))
        im = icons[iid]
        # Draw both 48x48 full view and 24x24 mini Bag list view!
        preview.paste(im, (x0 + 10, y0 + 26), im)
        mini = im.resize((24, 24), Image.NEAREST)
        preview.paste(mini, (x0 + 64, y0 + 38), mini)
        d.text((x0 + 8, y0 + 8), f"{iid} {id_names.get(iid, '')[:11]}", fill=(224, 232, 244, 255))

    preview.save(os.path.join(PREV_DIR, "all_new_item_icons.png"))
    print(f"Generated {len(icons)} icons and previews/all_new_item_icons.png cleanly.")

    if args.apply:
        for iid, im in sorted(icons.items()):
            out_path = os.path.join(ICONS_DIR, f"item{iid:03d}.png")
            im.save(out_path)
        print(f"Applied all {len(icons)} icons into Graphics/Icons/.")


if __name__ == "__main__":
    main()
