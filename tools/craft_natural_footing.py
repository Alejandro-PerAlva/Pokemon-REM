
from PIL import Image, ImageDraw

bg = Image.open('Graphics/Battleback_Candidates/Berilo/battlebgField.png').convert('RGBA')
w, h = bg.size

# Palette sampled from Berilo field:
COL_HIGHLIGHT = (205, 232, 125, 255)
COL_GRASS_LIGHT = (185, 218, 108, 255)
COL_GRASS_MID = (165, 200, 92, 255)
COL_GRASS_SHADE = (120, 160, 70, 255)
COL_GRASS_DEEP = (85, 125, 52, 255)
COL_DIRT_LIGHT = (228, 195, 140, 255)
COL_DIRT_MID = (195, 162, 112, 255)
COL_DIRT_DARK = (155, 122, 80, 255)

# We will create TWO versions:
# Version A: Terraza Natural de Hierba (Grass knoll / promontory with shaded bank)
# Version B: Claro de Tierra/Sendero (Natural soil path & rocky ledge framing)

# --- VERSION A: Terraza de hierba acotada ---
v_a = bg.copy()
pix_a = v_a.load()

# Enemy spot anchor: cx=384, cy=176. Surface is an ellipse: rx=72, ry=22.
# Shaded lip below: cy + 10 to cy + 28
import math

# Enemy terrace
for dy in range(-25, 30):
    for dx in range(-80, 81):
        x = 384 + dx
        y = 176 + dy
        if 0 <= x < w and 0 <= y < h:
            # Normalized ellipse dist: (dx/rx)^2 + (dy/ry)^2
            d = (dx / 72.0)**2 + (dy / 20.0)**2
            if d <= 1.0:
                # Inside the surface: slightly flatter, cleaner tone with subtle rim
                if dy > 8:
                    # Shaded lip/front edge of the step
                    orig = pix_a[x, y]
                    pix_a[x, y] = (int(orig[0]*0.75 + COL_GRASS_DEEP[0]*0.25),
                                   int(orig[1]*0.75 + COL_GRASS_DEEP[1]*0.25),
                                   int(orig[2]*0.75 + COL_GRASS_DEEP[2]*0.25), 255)
                elif dy > 0:
                    orig = pix_a[x, y]
                    pix_a[x, y] = (int(orig[0]*0.85 + COL_GRASS_SHADE[0]*0.15),
                                   int(orig[1]*0.85 + COL_GRASS_SHADE[1]*0.15),
                                   int(orig[2]*0.85 + COL_GRASS_SHADE[2]*0.15), 255)
                else:
                    # Top surface: clear and leveled
                    orig = pix_a[x, y]
                    pix_a[x, y] = (int(orig[0]*0.85 + COL_HIGHLIGHT[0]*0.15),
                                   int(orig[1]*0.85 + COL_HIGHLIGHT[1]*0.15),
                                   int(orig[2]*0.85 + COL_HIGHLIGHT[2]*0.15), 255)
            elif 1.0 < d <= 1.35 and dy > 5:
                # Soft shadow under the terrace
                orig = pix_a[x, y]
                shadow_factor = 0.82
                pix_a[x, y] = (int(orig[0]*shadow_factor), int(orig[1]*shadow_factor), int(orig[2]*shadow_factor), 255)

# Player spot anchor: cx=128, cy=304. rx=120, ry=32
for dy in range(-35, 45):
    for dx in range(-130, 131):
        x = 128 + dx
        y = 304 + dy
        if 0 <= x < w and 0 <= y < h:
            d = (dx / 115.0)**2 + (dy / 30.0)**2
            if d <= 1.0:
                if dy > 12:
                    orig = pix_a[x, y]
                    pix_a[x, y] = (int(orig[0]*0.8 + COL_GRASS_DEEP[0]*0.2),
                                   int(orig[1]*0.8 + COL_GRASS_DEEP[1]*0.2),
                                   int(orig[2]*0.8 + COL_GRASS_DEEP[2]*0.2), 255)
                elif dy < -5:
                    orig = pix_a[x, y]
                    pix_a[x, y] = (int(orig[0]*0.85 + COL_HIGHLIGHT[0]*0.15),
                                   int(orig[1]*0.85 + COL_HIGHLIGHT[1]*0.15),
                                   int(orig[2]*0.85 + COL_HIGHLIGHT[2]*0.15), 255)

out_dir = 'C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/previews'
v_a.save(f'{out_dir}/field_acotado_terraza.png')

# Now composite battlers onto original vs terraza:
front = Image.open('Graphics/Battlers/448.png').convert('RGBA')
back = Image.open('Graphics/Battlers/448b.png').convert('RGBA')
fw, fh = front.size
bw, bh = back.size

comp_orig = bg.copy()
comp_orig.alpha_composite(front, (384 - fw//2, 176 - fh))
comp_orig.alpha_composite(back, (128 - bw//2, 304 - bh))
comp_orig.save(f'{out_dir}/staged_field_abierto_original.png')

comp_terraza = v_a.copy()
comp_terraza.alpha_composite(front, (384 - fw//2, 176 - fh))
comp_terraza.alpha_composite(back, (128 - bw//2, 304 - bh))
comp_terraza.save(f'{out_dir}/staged_field_acotado_terraza.png')

print('Generated terraza and staged comparisons!')
