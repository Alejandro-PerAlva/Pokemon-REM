import os
import colorsys
import random
from PIL import Image, ImageEnhance, ImageDraw

TARGET_DIR = r"C:\Users\apera\Desktop\BB\REM_Original_32_PixelArt"

def create_eve_variant(img):
    """Aplica atardecer calido con cielo crepuscular y luz dorada suave."""
    img_rgb = img.convert("RGB")
    w, h = img_rgb.size
    pixels = img_rgb.load()
    out = Image.new("RGB", (w, h))
    out_px = out.load()
    
    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            # Is sky? (top 45% and bluish/bright)
            if y < h * 0.45 and (b > r - 15) and (g > r - 25):
                # Sunset gradient: golden orange to dusk pink
                factor = y / (h * 0.45)
                nr = min(255, int(r * 1.25 + 35))
                ng = min(255, int(g * 0.95 + 10))
                nb = max(0, int(b * 0.65 - 15))
            else:
                # Terrain warm evening tint
                nr = min(255, int(r * 1.14 + 10))
                ng = min(255, int(g * 0.96 + 5))
                nb = max(0, int(b * 0.76 - 8))
            out_px[x, y] = (nr, ng, nb)
            
    enhancer = ImageEnhance.Color(out)
    return enhancer.enhance(1.15)

def create_starry_night_variant(img, seed=42):
    """Aplica noche estrellada limpia: cielo azul marino profundo sin nubes diurnas y estrellas nitidas."""
    img_rgb = img.convert("RGB")
    w, h = img_rgb.size
    pixels = img_rgb.load()
    night = Image.new("RGB", (w, h))
    night_px = night.load()
    
    # Precomputar estrellas con semilla fija
    random.seed(seed)
    stars = {}
    for _ in range(85):
        sx = random.randint(0, w - 1)
        sy = random.randint(0, int(h * 0.42))
        color = random.choice([
            (255, 255, 255), (230, 240, 255), (190, 220, 255), 
            (255, 250, 210), (180, 240, 255)
        ])
        size = random.choice([1, 1, 1, 2])
        stars[(sx, sy)] = (color, size)
        
    for y in range(h):
        # Gradiente de cielo nocturno
        sky_r = int(7 + (y / (h * 0.45)) * 14)
        sky_g = int(10 + (y / (h * 0.45)) * 20)
        sky_b = int(28 + (y / (h * 0.45)) * 36)
        
        for x in range(w):
            r, g, b = pixels[x, y]
            # Detectar cielo: zona superior donde predomina el azul/blanco de nubes
            is_sky = (y < h * 0.45) and (b > r - 10) and (g > r - 20) and not (g > r + 30 and g > b + 20)
            
            if is_sky:
                night_px[x, y] = (sky_r, sky_g, sky_b)
            else:
                # Terreno bajo luz de luna (sombras frias, brillo plateado/azul)
                lum = (r * 0.299 + g * 0.587 + b * 0.114) / 255.0
                nr = int(r * 0.24 * lum + 8)
                ng = int(g * 0.44 * lum + 14)
                nb = int(b * 0.68 * lum + 28)
                night_px[x, y] = (min(255, nr), min(255, ng), min(255, nb))
                
    # Dibujar estrellas sobre el cielo nocturno
    draw = ImageDraw.Draw(night)
    for (sx, sy), (color, size) in stars.items():
        r, g, b = night_px[sx, sy]
        if r < 35 and g < 45 and b < 80: # Solo si es cielo
            if size == 1:
                draw.point((sx, sy), fill=color)
            else:
                draw.point((sx, sy), fill=color)
                dim = (color[0]//2, color[1]//2, color[2]//2)
                if sx > 0: draw.point((sx-1, sy), fill=dim)
                if sx < w-1: draw.point((sx+1, sy), fill=dim)
                if sy > 0: draw.point((sx, sy-1), fill=dim)
                if sy < h-1: draw.point((sx, sy+1), fill=dim)
                
    return night

def process_all_exteriors():
    exteriores = [
        "01_Rutas_Pradera_Campo.png",
        "02_Rutas_Bosque_Frondoso.png",
        "03_Cienaga_Pantano_Charcas.png",
        "04_Isla_Suenio_Otonio.png",
        "05_Ciudad_Nefral_Bambu.png",
        "07_Rutas_Mar_Abierto.png",
        "08_Puente_Dolomita_Colosal.png",
        "09_Desierto_Estepa_Arida.png"
    ]
    for ext in exteriores:
        base_path = os.path.join(TARGET_DIR, ext)
        if not os.path.exists(base_path):
            continue
        name_no_ext = os.path.splitext(ext)[0]
        img = Image.open(base_path)
        
        # Guardar Eve
        eve = create_eve_variant(img)
        eve_path = os.path.join(TARGET_DIR, f"{name_no_ext}_Eve.png")
        eve.save(eve_path)
        
        # Guardar Night estrellado
        night = create_starry_night_variant(img)
        night_path = os.path.join(TARGET_DIR, f"{name_no_ext}_Night.png")
        night.save(night_path)
        print(f"Actualizado con cielo estrellado y atardecer: {ext}")

if __name__ == "__main__":
    process_all_exteriors()
