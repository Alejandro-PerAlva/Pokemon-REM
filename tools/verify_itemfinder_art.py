"""
Verifies and renders animated GIFs and comparisons of the 4 Itemfinder states (V3)
using dynamic cell alignment (cw/2, ch) matching Sprite_Itemfinder in game.
"""

from PIL import Image
import os
import shutil


def composite_cell(char_cell, acc_cell, head_offset=0):
    """Composites accessory cell onto 64x64 character cell with ox=cw/2, oy=ch alignment."""
    cw, ch = acc_cell.size
    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    # Character (64x64, anchored bottom-center) sits at (cw - 64)//2, ch - 64
    px = (cw - char_cell.width) // 2
    py = ch - char_cell.height
    canvas.paste(char_cell, (px, py), char_cell)
    acc_shifted = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    acc_shifted.paste(acc_cell, (0, head_offset))
    return Image.alpha_composite(canvas, acc_shifted)


def generate_previews():
    os.makedirs("previews", exist_ok=True)

    tr_m = Image.open("Graphics/Characters/trchar000.png").convert("RGBA")
    tr_f = Image.open("Graphics/Characters/trchar001.png").convert("RGBA")
    tr_brun = Image.open("Graphics/Characters/boy_run.png").convert("RGBA")

    states = ["state_0_idle.png", "state_1_near.png", "state_2_facing.png", "state_3_target.png"]
    sample_acc = Image.open(f"Graphics/Characters/Itemfinder/{states[0]}").convert("RGBA")
    cw, ch = sample_acc.width // 4, sample_acc.height // 4

    # 1. 4-Direction x 4-State Grid for Male standing (pattern 3 shows pulse!)
    grid_img = Image.new("RGBA", (cw * 4, ch * 4), (20, 24, 36, 255))
    for st_idx, st_file in enumerate(states):
        acc = Image.open(f"Graphics/Characters/Itemfinder/{st_file}").convert("RGBA")
        for dir_idx in range(4):
            char_crop = tr_m.crop((3 * 64, dir_idx * 64, 4 * 64, (dir_idx + 1) * 64))
            acc_crop = acc.crop((3 * cw, dir_idx * ch, 4 * cw, (dir_idx + 1) * ch))
            comp = composite_cell(char_crop, acc_crop, head_offset=0)
            grid_img.paste(comp, (st_idx * cw, dir_idx * ch), comp)

    grid_img.resize((grid_img.width * 2, grid_img.height * 2), Image.NEAREST).save(
        "previews/itemfinder_v2_4directions.png"
    )

    # 2. Male vs Female vs Running comparison (Down, flash frame)
    comp_sheet = Image.new("RGBA", (cw * 4, ch * 3), (20, 24, 36, 255))
    for i, st_file in enumerate(states):
        acc = Image.open(f"Graphics/Characters/Itemfinder/{st_file}").convert("RGBA")
        acc_cell = acc.crop((3 * cw, 0, 4 * cw, ch))

        m_cell = composite_cell(tr_m.crop((3 * 64, 0, 4 * 64, 64)), acc_cell, head_offset=0)
        f_cell = composite_cell(tr_f.crop((3 * 64, 0, 4 * 64, 64)), acc_cell, head_offset=4)
        r_cell = composite_cell(tr_brun.crop((3 * 64, 0, 4 * 64, 64)), acc_cell, head_offset=6)

        comp_sheet.paste(m_cell, (i * cw, 0), m_cell)
        comp_sheet.paste(f_cell, (i * cw, ch), f_cell)
        comp_sheet.paste(r_cell, (i * cw, 2 * ch), r_cell)

    comp_sheet.resize((comp_sheet.width * 2, comp_sheet.height * 2), Image.NEAREST).save(
        "previews/itemfinder_states_comparison.png"
    )

    # 3. Walk cycle GIFs for all 4 directions in State 2 (Facing) and State 3 (Target)
    acc2 = Image.open("Graphics/Characters/Itemfinder/state_2_facing.png").convert("RGBA")
    for dir_idx, d_name in enumerate(["Down", "Left", "Right", "Up"]):
        frames = []
        for pat in [0, 1, 2, 3]:
            m_crop = tr_m.crop((pat * 64, dir_idx * 64, (pat + 1) * 64, (dir_idx + 1) * 64))
            a_crop = acc2.crop((pat * cw, dir_idx * ch, (pat + 1) * cw, (dir_idx + 1) * ch))
            c = composite_cell(m_crop, a_crop, head_offset=0)
            bg = Image.new("RGBA", c.size, (20, 24, 36, 255))
            bg.paste(c, (0, 0), c)
            frames.append(bg.resize((cw * 2, ch * 2), Image.NEAREST))

        frames[0].save(
            f"previews/itemfinder_walk_{d_name}.gif",
            save_all=True,
            append_images=frames[1:],
            duration=160,
            loop=0,
        )

    art_dir = r"C:\Users\apera\.gemini\antigravity\brain\28b48a32-a6fe-4d6a-9bad-08a2c99f1d48"
    os.makedirs(os.path.join(art_dir, "previews"), exist_ok=True)
    for f in os.listdir("previews"):
        if f.startswith("itemfinder_"):
            shutil.copy2(os.path.join("previews", f), os.path.join(art_dir, "previews", f))

    print("V3 Previews generated successfully!")


if __name__ == "__main__":
    generate_previews()
