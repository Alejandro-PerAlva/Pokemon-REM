"""Clean Graphics/Battlebacks/ and generate the 64 battlebg + 128 base placeholders.

Exact counts:
  - 12 exterior sky-bearing bases x 3 (Day, Eve, Night) = 36
  - 2 exterior boss bases (fixed) = 2
  - 6 cave bases = 6
  - 20 indoor bases (8 Gyms + 4 Elite + Champion + 5 Special + 2 Generic) = 20
Total: 64 battlebg (512x288), 64 enemybase (256x128), 64 playerbase (512x64) = 192 PNGs.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BB_DIR = ROOT / "Graphics" / "Battlebacks"

# (internal_id, category, spanish_label, has_time_variants)
BASES = [
    # 1. Rutas / Campo (4)
    ("Field", "ruta", "Ruta normal (pradera)", True),
    ("FieldAlt", "ruta", "Ruta (2o color cesped)", True),
    ("Snow", "ruta", "Ruta nevada", True),
    ("Autumn", "ruta", "Ruta otonal / anaranjada", True),
    # 2. Cuevas (6)
    ("Cave", "cueva", "Cueva normal", False),
    ("CaveLush", "cueva", "Cueva frondosa (bosque/selva)", False),
    ("CaveIce", "cueva", "Cueva de hielo (Gruta Labrador)", False),
    ("CaveVolcano", "cueva", "Cueva volcanica (Gruta Piral)", False),
    ("CaveCrystal", "cueva", "Cueva de cristales (Gruta Hialina)", False),
    ("CaveWater", "cueva", "Cueva con agua (Gruta Azur)", False),
    # 3. Biomas de entorno (6)
    ("Mountain", "bioma", "Montana normal", True),
    ("MountainSnow", "bioma", "Montana nevada", True),
    ("Forest", "bioma", "Bosque (Bosque Dioptasa)", True),
    ("Swamp", "bioma", "Pantano / Cienaga Limonar", True),
    ("Beach", "bioma", "Playa (Playa Sepiola)", True),
    ("Desert", "bioma", "Desierto (Desierto Halar)", True),
    # 4. Rutas especiales (2)
    ("Water", "especial_ext", "Ruta marina / Mar abierto", True),
    ("Bridge", "especial_ext", "Puente (Puente Dolomar)", True),
    # 5. Jefes de exterior (2, sin variante horaria)
    ("PeakAzogue", "jefe_ext", "Cumbre Monte Azogue (Ambrosio/Eliseo)", False),
    ("IslandBoss", "jefe_ext", "Jefe de las Islas (Sueno/Pesadilla)", False),
    # 6. Gimnasios 1-8 (8)
    ("Gym01Normal", "gym", "Gimnasio 1 - Matilde (Normal)", False),
    ("Gym02Water", "gym", "Gimnasio 2 - Ismael (Agua)", False),
    ("Gym03Steel", "gym", "Gimnasio 3 - Greta (Acero)", False),
    ("Gym04Fighting", "gym", "Gimnasio 4 - Genzo (Lucha)", False),
    ("Gym05Rock", "gym", "Gimnasio 5 - Fausto (Roca)", False),
    ("Gym06Grass", "gym", "Gimnasio 6 - Hildegarda (Planta)", False),
    ("Gym07Ice", "gym", "Gimnasio 7 - Isolda (Hielo)", False),
    ("Gym08Fire", "gym", "Gimnasio 8 - Beltran (Fuego)", False),
    # 7. Alto Mando y Campeona (5)
    ("EliteA", "liga", "Alto Mando 1 - Nicodemo (Bicho)", False),
    ("EliteB", "liga", "Alto Mando 2 - Oriana (Psiquico)", False),
    ("EliteC", "liga", "Alto Mando 3 - Anteo (Siniestro)", False),
    ("EliteD", "liga", "Alto Mando 4 - Leucotea (Tierra)", False),
    ("Champion", "liga", "Campeona - Rolanda Altamira", False),
    # 8. Interiores especiales / historia (5)
    ("Lab", "interior_esp", "Laboratorio (Combate inicial)", False),
    ("PowerPlant", "interior_esp", "Central Electrica (Central Fulgor)", False),
    ("Temple", "interior_esp", "Templo / Ruinas antiguas", False),
    ("Mansion", "interior_esp", "Mansion encantada (Villa Adular)", False),
    ("Sewers", "interior_esp", "Cloacas / Alcantarillas Azabache", False),
    # 9. Interiores genericos (2)
    ("IndoorA", "interior_gen", "Indoor general A (Casas)", False),
    ("IndoorB", "interior_gen", "Indoor general B (Academia/Hotel/Museo)", False),
]

CAT_COLORS = {
    "ruta": ((64, 118, 76), (112, 168, 114)),
    "bioma": ((66, 108, 128), (114, 152, 168)),
    "especial_ext": ((54, 98, 150), (92, 144, 198)),
    "jefe_ext": ((84, 46, 106), (138, 78, 156)),
    "cueva": ((62, 58, 70), (102, 96, 114)),
    "gym": ((44, 68, 112), (82, 118, 174)),
    "liga": ((92, 68, 34), (168, 128, 56)),
    "interior_esp": ((78, 62, 86), (124, 102, 134)),
    "interior_gen": ((96, 86, 76), (146, 132, 116)),
}

TIME_TINTS = {
    "": ("DIA", (0, 0, 0)),
    "Eve": ("ATARDECER (Eve)", (52, 12, -32)),
    "Night": ("NOCHE (Night)", (-34, -36, 18)),
}


def clamp(v: int) -> int:
    return max(0, min(255, v))


def tint(rgb: tuple[int, int, int], delta: tuple[int, int, int]) -> tuple[int, int, int]:
    return (clamp(rgb[0] + delta[0]), clamp(rgb[1] + delta[1]), clamp(rgb[2] + delta[2]))


def make_battlebg(name: str, cat: str, desc: str, suffix: str) -> Image.Image:
    bg_c, acc_c = CAT_COLORS[cat]
    t_label, delta = TIME_TINTS[suffix]
    bg_c = tint(bg_c, delta)
    acc_c = tint(acc_c, delta)

    im = Image.new("RGBA", (512, 288), (*bg_c, 255))
    draw = ImageDraw.Draw(im)

    # Horizon band
    horizon_c = tint(bg_c, (-16, -16, -16))
    draw.rectangle([0, 170, 511, 287], fill=(*horizon_c, 255))
    draw.line([(0, 170), (511, 170)], fill=(*acc_c, 255), width=2)

    # Subtle diagonal placeholder grid
    grid_c = (*acc_c, 65)
    for x in range(0, 512, 32):
        draw.line([(x, 0), (x, 287)], fill=grid_c)
    for y in range(0, 288, 32):
        draw.line([(0, y), (511, y)], fill=grid_c)

    draw.rectangle([4, 4, 507, 283], outline=(*acc_c, 255), width=2)

    # Center text badge
    draw.rectangle([56, 62, 456, 146], fill=(18, 20, 28, 210), outline=(*acc_c, 255), width=2)
    font = ImageFont.load_default()
    draw.text((74, 74), f"PLACEHOLDER: battlebg{name}{suffix}.png", fill=(255, 255, 255, 255), font=font)
    draw.text((74, 96), f"Zona: {desc}", fill=(220, 230, 240, 255), font=font)
    draw.text((74, 118), f"Franja: {t_label}  |  512x288", fill=(237, 189, 98, 255), font=font)
    return im


def make_enemybase(name: str, cat: str, suffix: str) -> Image.Image:
    _, acc_c = CAT_COLORS[cat]
    _, delta = TIME_TINTS[suffix]
    fill_c = tint(acc_c, delta)
    edge_c = tint(fill_c, (-40, -40, -40))

    im = Image.new("RGBA", (256, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.ellipse([16, 44, 240, 120], fill=(*fill_c, 225), outline=(*edge_c, 255), width=4)
    draw.ellipse([28, 52, 228, 112], outline=(245, 248, 252, 160), width=2)
    draw.text((48, 76), f"enemybase{name}{suffix}", fill=(255, 255, 255, 255), font=ImageFont.load_default())
    return im


def make_playerbase(name: str, cat: str, suffix: str) -> Image.Image:
    _, acc_c = CAT_COLORS[cat]
    _, delta = TIME_TINTS[suffix]
    fill_c = tint(acc_c, delta)
    edge_c = tint(fill_c, (-40, -40, -40))

    im = Image.new("RGBA", (512, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw.ellipse([16, 8, 496, 60], fill=(*fill_c, 230), outline=(*edge_c, 255), width=4)
    draw.ellipse([36, 14, 476, 54], outline=(245, 248, 252, 160), width=2)
    draw.text((170, 28), f"playerbase{name}{suffix}", fill=(255, 255, 255, 255), font=ImageFont.load_default())
    return im


def main():
    BB_DIR.mkdir(parents=True, exist_ok=True)
    removed = 0
    for old in BB_DIR.iterdir():
        if old.is_file():
            old.unlink()
            removed += 1

    created = []
    for name, cat, desc, has_time in BASES:
        suffixes = ["", "Eve", "Night"] if has_time else [""]
        for sfx in suffixes:
            bg = make_battlebg(name, cat, desc, sfx)
            eb = make_enemybase(name, cat, sfx)
            pb = make_playerbase(name, cat, sfx)

            p_bg = BB_DIR / f"battlebg{name}{sfx}.png"
            p_eb = BB_DIR / f"enemybase{name}{sfx}.png"
            p_pb = BB_DIR / f"playerbase{name}{sfx}.png"

            bg.save(p_bg)
            eb.save(p_eb)
            pb.save(p_pb)
            created.extend([p_bg.name, p_eb.name, p_pb.name])

    print(f"Removed {removed} old files. Created {len(created)} placeholder PNGs in {BB_DIR}.")


if __name__ == "__main__":
    main()
