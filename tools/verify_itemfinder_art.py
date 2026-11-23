"""
Verifies and renders animated GIFs and comparisons of the 4 Itemfinder states (V2)
showing Down, Left, Right, Up across walking and standing.
"""

from PIL import Image
import os, shutil

def generate_previews():
    os.makedirs('previews', exist_ok=True)
    
    tr_m = Image.open('Graphics/Characters/trchar000.png').convert('RGBA')
    tr_f = Image.open('Graphics/Characters/trchar001.png').convert('RGBA')
    
    states = ['state_0_idle.png', 'state_1_near.png', 'state_2_facing.png', 'state_3_target.png']
    state_labels = ['0_Idle', '1_Near', '2_Facing', '3_Target']
    
    # 1. 4-Direction Grid Comparison for Male & Female
    # 4 columns (States 0..3), 4 rows (Down, Left, Right, Up)
    grid_img = Image.new('RGBA', (64 * 4, 64 * 4), (20, 24, 36, 255))
    
    for st_idx, st_file in enumerate(states):
        acc = Image.open(f'Graphics/Characters/Itemfinder/{st_file}').convert('RGBA')
        for dir_idx in range(4):
            # Crop standing frame (pattern 1)
            char_crop = tr_m.crop((64, dir_idx * 64, 128, (dir_idx + 1) * 64))
            acc_crop = acc.crop((64, dir_idx * 64, 128, (dir_idx + 1) * 64))
            comp = Image.alpha_composite(char_crop, acc_crop)
            grid_img.paste(comp, (st_idx * 64, dir_idx * 64), comp)
            
    grid_enlarged = grid_img.resize((grid_img.width * 2, grid_img.height * 2), Image.NEAREST)
    grid_enlarged.save('previews/itemfinder_v2_4directions.png')

    # 2. Side-by-side standing comparison (Down)
    comp_sheet = Image.new('RGBA', (64 * 4, 64 * 2), (20, 24, 36, 255))
    for i, st_file in enumerate(states):
        acc = Image.open(f'Graphics/Characters/Itemfinder/{st_file}').convert('RGBA')
        
        # Male standing down
        m_frame = tr_m.crop((64, 0, 128, 64))
        acc_m = acc.crop((64, 0, 128, 64))
        cell_m = Image.alpha_composite(m_frame, acc_m)
        comp_sheet.paste(cell_m, (i * 64, 0), cell_m)
        
        # Female standing down (head offset 4px)
        f_frame = tr_f.crop((64, 0, 128, 64))
        acc_f = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        acc_f.paste(acc.crop((64, 0, 128, 64)), (0, 4))
        cell_f = Image.alpha_composite(f_frame, acc_f)
        comp_sheet.paste(cell_f, (i * 64, 64), cell_f)
        
    comp_sheet.resize((comp_sheet.width * 2, comp_sheet.height * 2), Image.NEAREST).save('previews/itemfinder_states_comparison.png')

    # 3. Create animated walk cycle preview for all 4 directions in State 2 (Facing)
    acc2 = Image.open('Graphics/Characters/Itemfinder/state_2_facing.png').convert('RGBA')
    for dir_idx, d_name in enumerate(['Down', 'Left', 'Right', 'Up']):
        frames = []
        for pat in [0, 1, 2, 3]:
            m_crop = tr_m.crop((pat * 64, dir_idx * 64, (pat + 1) * 64, (dir_idx + 1) * 64))
            a_crop = acc2.crop((pat * 64, dir_idx * 64, (pat + 1) * 64, (dir_idx + 1) * 64))
            c = Image.alpha_composite(m_crop, a_crop)
            frames.append(c.resize((128, 128), Image.NEAREST))
            
        frames[0].save(
            f'previews/itemfinder_walk_{d_name}.gif',
            save_all=True,
            append_images=frames[1:],
            duration=160,
            loop=0
        )

    # 4. Copy to artifact directory
    art_dir = r'C:\Users\apera\.gemini\antigravity\brain\28b48a32-a6fe-4d6a-9bad-08a2c99f1d48'
    os.makedirs(os.path.join(art_dir, 'previews'), exist_ok=True)
    for f in os.listdir('previews'):
        if f.startswith('itemfinder_'):
            shutil.copy2(os.path.join('previews', f), os.path.join(art_dir, 'previews', f))

    print('V2 Previews and walk animations generated and copied to artifact directory!')

if __name__ == '__main__':
    generate_previews()
