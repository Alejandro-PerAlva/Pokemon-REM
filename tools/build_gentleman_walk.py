"""Build complete 16-frame 256x256 walk spritesheet (zero shadow) for the burgundy-coat gentleman.

Matches Pokémon DS/Gen 4-5 256x256 (64x64 cell, native 32x32 2x2 pixel-art grid) mechanics
verified across trchar076, npc006, and trchar073:
  - Col 0 & Col 2: exact shadowless idle stand (y=2..29 in 32x32 native coords)
  - Col 1 & Col 3: -1 native px head/upper-torso upward bounce (y=1..16),
    natural opposite arm-leg swing, parting frock coat hems & grounded stride shoes.
  - Zero semi-transparent shadows or edge smudge pixels (strict alpha in {0, 255}).
"""

import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_PATH = (
    r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48"
    r"/.user_uploaded/media_1795594799755_8797eed4.png"
)
PREV_DIR = os.path.join(ROOT, "previews")

# Exact palette extracted from the uploaded Col 0 sprite (no invented colors)
PAL = {
    ".": (0, 0, 0, 0),
    "#": (0, 0, 0, 255),
    "d": (62, 29, 36, 255),       # burgundy coat dark shadow/edge
    "c": (114, 55, 68, 255),      # burgundy coat mid
    "m": (126, 71, 73, 255),      # sleeve/cuff burgundy tone
    "C": (147, 81, 96, 255),      # burgundy coat highlight
    "G": (203, 186, 93, 255),     # gold pocket-watch chain
    "S": (247, 207, 182, 255),    # skin highlight (hands)
    "s": (207, 150, 111, 255),    # skin shadow (hands)
    "W": (248, 248, 248, 255),    # white cravat/collar highlight
    "U": (145, 112, 149, 255),    # cravat/vest light
    "u": (98, 78, 101, 255),      # vest mid
    "v": (94, 76, 98, 255),       # vest/beard-neck dark
    "g": (134, 122, 129, 255),    # beard-collar light grey
    "k": (108, 85, 73, 255),      # beard mid
    "K": (77, 61, 53, 255),       # beard dark / side outline
    "z": (39, 31, 40, 255),       # back hair deep dark
    "P": (232, 216, 216, 255),    # cream trousers highlight
    "p": (194, 170, 170, 255),    # cream trousers mid
    "q": (123, 96, 96, 255),      # cream trousers shadow
    "B": (120, 72, 48, 255),      # brown shoe highlight
    "b": (73, 48, 40, 255),       # brown shoe dark
}


def load_clean_idle_cols():
    """Load Col 0 of the 4 rows at 32x32 native grids, removing all alpha < 255 shadows/smudges."""
    im = Image.open(SRC_PATH).convert("RGBA")
    px = im.load()
    rows = []
    for r in range(4):
        grid = []
        for ny in range(32):
            row_px = []
            for nx in range(32):
                c = px[nx * 2, r * 64 + ny * 2]
                row_px.append(c if c[3] == 255 else (0, 0, 0, 0))
            grid.append(row_px)
        rows.append(grid)
    return rows


def overlay_body(base_idle_grid, y_start, body_rows):
    """Build a 32x32 native stride frame: shift head+neck UP -1px, then paint body_rows at y_start..31."""
    # Start blank
    g = [[(0, 0, 0, 0) for _ in range(32)] for _ in range(32)]
    # Copy head (ny=0..y_start) shifted -1px UP
    for ny in range(1, y_start + 1):
        src_y = ny + 1
        if 0 <= src_y < 32:
            g[ny] = base_idle_grid[src_y][:]
    # Paint handcrafted body rows starting at y_start (nx=5..26, len=22)
    for idx, line in enumerate(body_rows):
        ny = y_start + idx
        if not (0 <= ny < 32):
            continue
        assert len(line) == 22, f"Row len {len(line)} != 22: {line}"
        for lx, ch in enumerate(line):
            nx = 5 + lx
            g[ny][nx] = PAL[ch]
    return g


def mirror_grid(g):
    return [row[::-1] for row in g]


DOWN_COL1_BODY = [
    ".....#cc#vggv#cc#.....",  # y17: collar & beard bottom (lifted -1px)
    "....#cCCdkKKkdCCc#....",  # y18: upper coat shoulders + cravat top
    "...#cCCddWUUWddCCc#...",  # y19: shoulders smooth & connected
    "...#cc#ccduGdcG#cc#...",  # y20: BOTH upper burgundy sleeves clean (`zero skin twitch at y20!`)
    "...#cc#CCcddGGC#msSm..",  # y21: left sleeve going down; right hand lifted -1px cleanly (`with cuff!`)
    "..mSsm#CCcdCCCcdmSSm..",  # y22: left hand low; right hand bottom (`full 2x2 hand shape!`)
    "..mSSmdCCCcdCCCd#mm#..",  # y23: left hand low; right cuff closing softly (`y23`)
    "...mm#pdddqqdddp#.....",  # y24: left cuff closing; uniform dark coat trim across coat hem
    ".....#pPPp##pPPp#.....",  # y25: clean bright cream thighs on BOTH legs (`zero dark leg stain!`)
    "......#bB#..#pPq#.....",  # y26: tucked left shoe (`2px #bB#`); slimmed stepping thigh (`3px`)
    ".......##....#pq#.....",  # y27: tucked left sole (`##`) at y27; slim 2px right shin (`#pq#`)
    ".............#Bb#.....",  # y28: stepping right shoe (`2px #Bb#`)
    "..............##......",  # y29: stepping right sole at y29!
    "......................",  # y30
    "......................",  # y31
]


def make_down_col1(idle_down):
    return overlay_body(idle_down, 17, DOWN_COL1_BODY)


def make_down_col3(idle_down):
    # Exact outer silhouette mirror of DOWN_COL1_BODY (preserving gold watch chain `G` on viewer's right vest)
    mirrored = [line[::-1] for line in DOWN_COL1_BODY]
    mirrored[3] = DOWN_COL1_BODY[3]
    mirrored[4] = mirrored[4][:7] + "CCcddGGC" + mirrored[4][15:]
    mirrored[5] = mirrored[5][:7] + "cCCcdCCC" + mirrored[5][15:]
    return overlay_body(idle_down, 17, mirrored)


UP_COL1_BODY = [
    ".....#c#zzzzzz#c#.....",  # y17: upper coat & neck hair
    "....#cCC######CCc#....",  # y18: back shoulders
    "...#cCCdccccccdCCc#...",  # y19: back coat
    "...#cc#CccccccC#cc#...",  # y20: BOTH upper burgundy sleeves clean (`zero armpit hand twitch!`)
    "...#cc#dCCCccCCC#sSm..",  # y21: left sleeve lowering; right hand lifted -1px cleanly
    "..mSs#dCCCccCCCdmSSm..",  # y22: left hand low (`2x2`); right hand bottom (`2x2`)
    "..mSS#dcCCccCCcd#mm#..",  # y23: left hand low; right cuff closing softly
    "...mm#pddddddddp#.....",  # y24: uniform dark coat hem matching Col 0 (moved cleanly to y24!)
    ".....#pPPp##pPPp#.....",  # y25: BOTH legs bright cream (`zero weird black shadow on Up leg!`)
    "......#bB#..#pPq#.....",  # y26: tucked left shoe (`2px #bB#`); slimmed right stepping leg
    ".......##....#pq#.....",  # y27: tucked left sole (`##`) at y27; slim 2px right ankle
    ".............#Bb#.....",  # y28: stepping right shoe (`2px #Bb#`)
    "..............##......",  # y29: stepping right sole at y29
    "......................",  # y30
    "......................",  # y31
]


def make_up_col1(idle_up):
    return overlay_body(idle_up, 17, UP_COL1_BODY)


def make_up_col3(idle_up):
    # Exact mirror of UP_COL1_BODY (preserving idle_up head crown asymmetry shifted -1px UP).
    return overlay_body(idle_up, 17, [line[::-1] for line in UP_COL1_BODY])


def make_left_col1(idle_left):
    # Left Col 1 (Subtle Phase A):
    #   Near arm shifts gently 1-2px forward over lower coat, keeping exact 2x2 rounded hand (`Ss`/`SS`).
    #   Compact grounded stride (`1-2px` separation), rounded 2px brown shoes capped neatly with `#` on toes!
    body = [
        ".....KK.uWdd#.........",  # y17: beard tip + cravat top
        ".......dWdccd.........",  # y18: collar + shoulder root
        ".......ddCCccd........",  # y19: upper coat + gold chain start
        "......dGCCmCccd.......",  # y20: chest + watch chain clean; near sleeve shifting slightly forward
        "......dcGGmmcc#.......",  # y21: chain bottom; forearm subtly forward over coat
        "......#c#SsmCc#.......",  # y22: near wrist/hand (`Ss`) centered gently forward on hip
        ".......##SS#dc#.......",  # y23: near hand (`SS`) bottom + coat waist
        ".......#cCcd###.......",  # y24: coat skirt draping cleanly over stride
        ".......#pPP##pq#......",  # y25: front hip + rear hip cleanly tucked under coat
        ".......#pP#.#pq#......",  # y26: slim 2px front leg + 1px clean air gap + slim 2px rear leg
        "......##pP#..#pq#.....",  # y27: rounded front toe-cap `#` + slim ankles (`2px gap`)
        "......#Bb#...#bb#.....",  # y28: compact 2px front shoe (`#Bb#`); compact 2px rear shoe (`#bb#`)
        ".......##.....##......",  # y29: both feet cleanly grounded at y29
        "......................",  # y30
        "......................",  # y31
    ]
    return overlay_body(idle_left, 17, body)


def make_left_col3(idle_left):
    # Left Col 3 (Subtle Phase B):
    #   Near arm swings ONLY ~1px back (never sticking far behind torso outline!), keeping full 2x2 hand.
    #   Opposite compact stride with exact 2px rounded brown shoes & grounded soles at y29.
    body = [
        ".....KK.uWdd#.........",  # y17
        ".......dWdccd.........",  # y18
        ".......ddCCccd........",  # y19
        "......dGCCmCccd.......",  # y20: watch chain clean; near shoulder pivoting subtly back
        "......dcGG#mCcd.......",  # y21: watch chain bottom; sleeve moving ~1px back inside coat
        "......#cCc#mSsd.......",  # y22: front coat edge; near cuff & full hand kept inside rear hip line (`nx<=19`)
        ".......#cCc#SSd.......",  # y23: front coat + full 2x2 hand (`SS`) cleanly bounded at rear edge!
        ".......#cCcd###.......",  # y24: coat skirt draping neatly above legs
        ".......#pq##pPP#......",  # y25: front hip + back hip cleanly under coat
        ".......#pP#.#pP#......",  # y26: slim 2px front shin + 1px air gap + slim 2px rear shin
        "......##pq#..#pq#.....",  # y27: rounded front toe-cap `#` + slim ankles (`2px gap`)
        "......#bb#...#Bb#.....",  # y28: compact 2px front shoe (`#bb#`); compact 2px rear shoe (`#Bb#`)
        ".......##.....##......",  # y29: both feet cleanly grounded at y29!
        "......................",  # y30
        "......................",  # y31
    ]
    return overlay_body(idle_left, 17, body)


def grid_to_64(grid):
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    px = im.load()
    for ny in range(32):
        for nx in range(32):
            c = grid[ny][nx]
            px[nx * 2, ny * 2] = c
            px[nx * 2 + 1, ny * 2] = c
            px[nx * 2, ny * 2 + 1] = c
            px[nx * 2 + 1, ny * 2 + 1] = c
    return im


def main():
    os.makedirs(PREV_DIR, exist_ok=True)
    idle_rows = load_clean_idle_cols()
    idle_down, idle_left, idle_right, idle_up = idle_rows

    # Verify Right idle matches Left idle mirror so Left->Right mirroring is 100% consistent
    assert idle_right == mirror_grid(idle_left), "Expected Right idle == mirror(Left idle)"

    left_c1 = make_left_col1(idle_left)
    left_c3 = make_left_col3(idle_left)

    frames = [
        [idle_down, make_down_col1(idle_down), idle_down, make_down_col3(idle_down)],
        [idle_left, left_c1, idle_left, left_c3],
        [idle_right, mirror_grid(left_c1), idle_right, mirror_grid(left_c3)],
        [idle_up, make_up_col1(idle_up), idle_up, make_up_col3(idle_up)],
    ]

    sheet = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    for r in range(4):
        for c in range(4):
            cell = grid_to_64(frames[r][c])
            sheet.paste(cell, (c * 64, r * 64))

    out_sheet = os.path.join(PREV_DIR, "gentleman_noblesheet.png")
    sheet.save(out_sheet)

    # Validation checks: strict 2x2 grid + zero partial alpha shadows anywhere
    spx = sheet.load()
    err2x2 = 0
    partial_alpha = 0
    for y in range(0, 256, 2):
        for x in range(0, 256, 2):
            c = spx[x, y]
            if px_mismatch := (spx[x + 1, y] != c or spx[x, y + 1] != c or spx[x + 1, y + 1] != c):
                err2x2 += 1
            if c[3] not in (0, 255):
                partial_alpha += 1
    assert err2x2 == 0, f"2x2 parity errors: {err2x2}"
    assert partial_alpha == 0, f"Residual shadow/alpha pixels: {partial_alpha}"

    # Build 2x labeled review sheet on medium slate + checkerboard grass tile simulation
    review = Image.new("RGBA", (560, 560), (42, 46, 58, 255))
    d = ImageDraw.Draw(review)
    d.text((12, 8), "Gentleman Walk Sheet (2x) - No Shadows - Col0 Idle | Col1 StepA | Col2 Idle | Col3 StepB", fill=(235, 242, 255, 255))
    big = sheet.resize((512, 512), Image.NEAREST)
    review.paste(big, (24, 34), big)
    for idx, nm in enumerate(["Down", "Left", "Right", "Up"]):
        d.text((4, 34 + idx * 128 + 56), nm[:2], fill=(180, 200, 230, 255))
    review.save(os.path.join(PREV_DIR, "gentleman_review_sheet.png"))

    # Save animated GIFs for all 4 directions (2x scale, 155ms/frame) + tiled walk contact sheet!
    for r, nm in enumerate(["Down", "Left", "Right", "Up"]):
        gif_frames = []
        for c in range(4):
            tile = Image.new("RGBA", (128, 128), (116, 176, 108, 255))  # meadow green BG to judge natural motion cleanly!
            cell = sheet.crop((c * 64, r * 64, (c + 1) * 64, (r + 1) * 64)).resize((128, 128), Image.NEAREST)
            tile.paste(cell, (0, 0), cell)
            gif_frames.append(tile.convert("P", palette=Image.ADAPTIVE))
        gif_frames[0].save(
            os.path.join(PREV_DIR, f"anim_gentleman_{nm}.gif"),
            save_all=True,
            append_images=gif_frames[1:],
            duration=155,
            loop=0,
        )

    print("Built gentleman_noblesheet.png + review sheet + 4 animated GIFs (2x2_err=0, partial_alpha=0).")


if __name__ == "__main__":
    main()
