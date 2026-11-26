"""Build clean Realidea-style VS transition assets (`vsSequenceSpecial`) for Pokémon REM.

Generates:
- `Graphics/Transitions/vs.png` (clean transparent brushed VS emblem from raw gray-keyed render)
- `Graphics/Transitions/vsBarSpecial<ID>.png` (512x384 supersampled HD themed backgrounds for all 20 key IDs)
- `Graphics/Transitions/vsTrainerSpecial<ID>.png` (384px-tall transparent anime cel-shaded mugshots)
- `previews/vs_special_review.png` (simulated in-game composition review sheet)
"""

from __future__ import annotations

import math
import os
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSITIONS_DIR = os.path.join(ROOT, "Graphics", "Transitions")
PREVIEWS_DIR = os.path.join(ROOT, "previews")
BRAIN_DIR = r"C:\Users\apera\.gemini\antigravity\brain\28b48a32-a6fe-4d6a-9bad-08a2c99f1d48"

VS_LOGO_RAW = os.path.join(BRAIN_DIR, "raw_vs_logo_final_1795646794070.jpg")

# Opcional: añadir aquí rutas de mugshots pixel art finales si se procesan por lote.
RAW_MUGSHOTS: Dict[int, Tuple[str, List[Tuple[float, float]]]] = {}


@dataclass(frozen=True)
class ThemeSpec:
    trainer_id: int
    name: str
    role: str
    c_dark: Tuple[int, int, int]
    c_mid: Tuple[int, int, int]
    c_accent: Tuple[int, int, int]
    motif: str


THEMES: List[ThemeSpec] = [
    ThemeSpec(2, "Lucián", "Rival · Psíquico", (18, 8, 44), (82, 34, 168), (217, 70, 239), "psychic"),
    ThemeSpec(3, "Guiomar", "Rival · Fuego/Lucha", (42, 10, 8), (180, 56, 18), (250, 176, 32), "fighting"),
    ThemeSpec(4, "Ambrosio", "Profesor · Acero/Psíquico", (12, 18, 36), (44, 62, 92), (212, 162, 68), "clockwork"),
    ThemeSpec(5, "Matilde", "Líder 1 · Normal", (24, 24, 58), (67, 56, 168), (242, 198, 56), "scholar"),
    ThemeSpec(6, "Ismael", "Líder 2 · Agua", (6, 28, 58), (8, 108, 168), (56, 224, 242), "water"),
    ThemeSpec(7, "Greta", "Líder 3 · Acero", (20, 24, 34), (56, 72, 92), (240, 106, 28), "steel"),
    ThemeSpec(8, "Genzo", "Líder 4 · Lucha", (22, 12, 16), (128, 26, 36), (220, 228, 240), "dojo"),
    ThemeSpec(9, "Fausto", "Líder 5 · Roca", (26, 18, 14), (118, 56, 22), (235, 148, 46), "rock"),
    ThemeSpec(10, "Hildegarda", "Líder 6 · Planta", (8, 34, 22), (24, 122, 62), (168, 224, 54), "grass"),
    ThemeSpec(11, "Isolda", "Líder 7 · Hielo", (10, 28, 56), (18, 122, 192), (192, 238, 255), "ice"),
    ThemeSpec(12, "Beltrán", "Líder 8 · Fuego", (28, 8, 12), (178, 28, 28), (255, 162, 52), "fire"),
    ThemeSpec(13, "Nicodemo", "Alto Mando 1 · Bicho", (10, 34, 28), (20, 114, 96), (174, 228, 48), "bug"),
    ThemeSpec(14, "Oriana", "Alto Mando 2 · Psíquico", (12, 14, 46), (76, 34, 142), (96, 200, 255), "astral"),
    ThemeSpec(15, "Anteo", "Alto Mando 3 · Siniestro", (26, 8, 18), (104, 20, 48), (176, 190, 210), "claw"),
    ThemeSpec(16, "Leucótea", "Alto Mando 4 · Tierra", (36, 20, 12), (154, 62, 24), (24, 174, 160), "earth"),
    ThemeSpec(17, "Rolanda", "Campeona", (10, 20, 52), (32, 78, 198), (252, 206, 56), "champion"),
    ThemeSpec(20, "Alarico", "Gral. Morfeo · Dragón/Volador", (10, 10, 30), (58, 46, 168), (226, 38, 56), "morfeo_dragon"),
    ThemeSpec(21, "Zenobia", "Gral. Morfeo · Eléc./Acero", (10, 14, 24), (14, 134, 168), (244, 64, 72), "morfeo_cyber"),
    ThemeSpec(22, "Ariadna", "Subcap. Morfeo · Siniestro", (18, 8, 24), (146, 24, 78), (244, 100, 178), "morfeo_rose"),
    ThemeSpec(23, "Eliseo", "Líder Morfeo · Fantasma/Fuego", (10, 8, 22), (56, 38, 128), (220, 48, 88), "morfeo_eclipse"),
]


def _flood_mask_from_seeds(
    rgb_img: Image.Image,
    seeds: List[Tuple[int, int]],
    predicate,
) -> List[bool]:
    w, h = rgb_img.size
    px = rgb_img.load()
    visited = [False] * (w * h)
    q: deque[Tuple[int, int]] = deque()
    for sx, sy in seeds:
        if 0 <= sx < w and 0 <= sy < h:
            idx = sy * w + sx
            if not visited[idx] and predicate(px[sx, sy]):
                visited[idx] = True
                q.append((sx, sy))
    while q:
        x, y = q.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h:
                idx = ny * w + nx
                if not visited[idx] and predicate(px[nx, ny]):
                    visited[idx] = True
                    q.append((nx, ny))
    return visited


def _dehalo_rgba(rgb_img: Image.Image, bg_mask: List[bool], is_white_bg: bool) -> Image.Image:
    w, h = rgb_img.size
    rgba = rgb_img.convert("RGBA")
    src = rgb_img.load()
    dst = rgba.load()

    # Pass 1: erase flooded background
    for y in range(h):
        row = y * w
        for x in range(w):
            if bg_mask[row + x]:
                dst[x, y] = (0, 0, 0, 0)

    # Pass 2: soft-feather 1px fringe touching bg_mask to remove bright/gray JPEG halo
    for y in range(1, h - 1):
        row = y * w
        for x in range(1, w - 1):
            if bg_mask[row + x]:
                continue
            touches_bg = (
                bg_mask[row + x - 1]
                or bg_mask[row + x + 1]
                or bg_mask[row - w + x]
                or bg_mask[row + w + x]
            )
            if not touches_bg:
                continue
            r, g, b = src[x, y]
            spread = max(r, g, b) - min(r, g, b)
            if is_white_bg:
                lum = (r + g + b) / 3.0
                if lum >= 205 and spread <= 28:
                    # Bright neutral edge pixel: attenuate alpha and slightly darken toward ink
                    a = max(0, min(255, int((250.0 - lum) / 45.0 * 220)))
                    scale = 0.72 if a > 0 else 0.0
                    dst[x, y] = (int(r * scale), int(g * scale), int(b * scale), a)
            else:
                # Neutral #808080 gray halo touching exterior gray vs white sticker rim
                dist_gray = max(abs(r - 128), abs(g - 128), abs(b - 128))
                lum = (r + g + b) / 3.0
                if spread <= 24 and lum < 232:
                    if lum <= 155 and dist_gray <= 48:
                        dst[x, y] = (0, 0, 0, 0)
                    elif lum > 155:
                        a = max(0, min(255, int((lum - 150.0) / 82.0 * 255)))
                        dst[x, y] = (255, 255, 255, a)
    return rgba


def build_vs_logo() -> None:
    """Build crisp 2x2 pixel-art brushed VS emblem (136x116 RGBA)."""
    if not os.path.exists(VS_LOGO_RAW):
        raise FileNotFoundError(f"Missing raw VS logo: {VS_LOGO_RAW}")
    im = Image.open(VS_LOGO_RAW).convert("RGB")
    w, h = im.size
    border_seeds: List[Tuple[int, int]] = []
    for x in range(w):
        border_seeds.append((x, 0))
        border_seeds.append((x, h - 1))
    for y in range(h):
        border_seeds.append((0, y))
        border_seeds.append((w - 1, y))

    def is_gray_bg(c: Tuple[int, int, int]) -> bool:
        r, g, b = c
        spread = max(r, g, b) - min(r, g, b)
        return spread <= 24 and 85 <= (r + g + b) / 3.0 <= 185

    bg_mask = _flood_mask_from_seeds(im, border_seeds, is_gray_bg)
    rgba = im.convert("RGBA")
    dst = rgba.load()
    for y in range(h):
        for x in range(w):
            if bg_mask[y * w + x]:
                dst[x, y] = (0, 0, 0, 0)
    bbox = rgba.getbbox()
    if bbox:
        rgba = rgba.crop(bbox)

    # Downscale to 2x2 DS native grid (64x54 inside 68x58) -> quantize -> 1px dark outline -> 2x NEAREST
    nw_half = 64
    nh_half = max(1, int(round(rgba.height * (nw_half / rgba.width))))
    if nh_half > 54:
        nh_half = 54
        nw_half = max(1, int(round(rgba.width * (nh_half / rgba.height))))
    small = rgba.resize((nw_half, nh_half), Image.LANCZOS)
    sp = small.load()
    for y in range(nh_half):
        for x in range(nw_half):
            r, g, b, a = sp[x, y]
            if a < 140:
                sp[x, y] = (0, 0, 0, 0)
            elif max(r, g, b) > 210 and (max(r, g, b) - min(r, g, b)) < 35:
                sp[x, y] = (248, 250, 255, 255)
            else:
                qr = (r // 32) * 32
                qg = (g // 32) * 32
                qb = min(255, (b // 32) * 32 + 16)
                sp[x, y] = (qr, qg, qb, 255)

    small_out = small.copy()
    op = small_out.load()
    for y in range(nh_half):
        for x in range(nw_half):
            if sp[x, y][3] == 0:
                if any(
                    0 <= x + dx < nw_half and 0 <= y + dy < nh_half and sp[x + dx, y + dy][3] > 0
                    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))
                ):
                    op[x, y] = (14, 18, 34, 255)

    canvas = Image.new("RGBA", (68, 58), (0, 0, 0, 0))
    canvas.paste(small_out, ((68 - nw_half) // 2, (58 - nh_half) // 2), small_out)
    out = canvas.resize((136, 116), Image.NEAREST)
    out_path = os.path.join(TRANSITIONS_DIR, "vs.png")
    out.save(out_path)
    print(f"[OK] Saved pixel-art {out_path} ({out.size})")


def build_template_placeholder() -> None:
    """Create a 384x384 transparent pixel-art template guide for vsTrainerSpecial<ID>.png."""
    W, H = 384, 384
    tpl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tpl, "RGBA")
    font = _load_bold_font(14)
    font_sm = _load_bold_font(12)

    # Outer canvas border (exact alignment: right edge = screen x=512, bottom = screen y=384)
    draw.rectangle([0, 0, W - 1, H - 1], outline=(0, 220, 255, 190), width=2)

    def outline_text(pos: Tuple[int, int], txt: str, fnt, fg: Tuple[int, int, int, int]) -> None:
        tx, ty = pos
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                if ox or oy:
                    draw.text((tx + ox, ty + oy), txt, font=fnt, fill=(10, 14, 24, 240))
        draw.text((tx, ty), txt, font=fnt, fill=fg)

    # Top diagonal border danger zone hint (y=0..48) and bottom border zone (y=328..384)
    draw.rectangle([2, 2, W - 3, 20], fill=(220, 40, 40, 80))
    draw.line([(2, 20), (W - 3, 20)], fill=(255, 90, 90, 220), width=1)
    outline_text((10, 4), "Margen superior libre (~16-20 px)", font_sm, (255, 220, 220, 255))

    # Safe bust silhouette zone (right-aligned, flush to bottom y=383)
    draw.rectangle([64, 24, W - 10, H - 1], fill=(0, 140, 180, 48), outline=(0, 200, 240, 220), width=2)
    # Crosshair center & head guide
    cx = (64 + W - 10) // 2
    draw.ellipse([cx - 52, 42, cx + 52, 152], outline=(255, 210, 60, 230), width=2)
    draw.arc([cx - 120, 155, cx + 120, 390], start=180, end=360, fill=(255, 210, 60, 210), width=2)

    # Name overlap reference on screen left (trainer x starts at 512-384 = 128)
    draw.rectangle([2, 220, 130, 270], fill=(200, 120, 20, 85), outline=(255, 180, 40, 220), width=1)
    outline_text((8, 226), "Zona nombre", font_sm, (255, 230, 160, 255))
    outline_text((8, 244), "(y=222..270)", font_sm, (255, 230, 160, 255))

    outline_text((76, 178), "PLANTILLA vsTrainerSpecial<ID>.png", font, (255, 255, 255, 255))
    outline_text((76, 198), "384 x 384 px | Escala pixel 2x2 (192x192 nativo)", font_sm, (190, 245, 255, 255))
    outline_text((76, 356), "Base del torso a ras de y=384 (borde inferior)", font_sm, (190, 245, 255, 255))

    out_path = os.path.join(TRANSITIONS_DIR, "vsTrainerSpecial_PLANTILLA_384x384.png")
    tpl.save(out_path)
    print(f"[OK] Saved {out_path} ({tpl.size})")


def process_mugshot(trainer_id: int, raw_path: str, extra_seeds: List[Tuple[float, float]]) -> None:
    im = Image.open(raw_path).convert("RGB")
    w, h = im.size
    seeds: List[Tuple[int, int]] = []
    for x in range(w):
        seeds.append((x, 0))
        seeds.append((x, h - 1))
    for y in range(h):
        seeds.append((0, y))
        seeds.append((w - 1, y))
    for fx, fy in extra_seeds:
        seeds.append((int(fx * (w - 1)), int(fy * (h - 1))))

    def is_white_bg(c: Tuple[int, int, int]) -> bool:
        r, g, b = c
        return min(r, g, b) >= 234 and (max(r, g, b) - min(r, g, b)) <= 20

    bg_mask = _flood_mask_from_seeds(im, seeds, is_white_bg)
    rgba = _dehalo_rgba(im, bg_mask, is_white_bg=True)

    # Crop tightly on left/top/right; keep bottom flush to opaque torso bottom
    bbox = rgba.getbbox()
    if not bbox:
        raise RuntimeError(f"Empty bbox after matting {raw_path}")
    cropped = rgba.crop(bbox)

    # Fit height with crisp headroom (~18px at top so hair sits neatly under top diagonal border)
    target_h = 384
    top_margin = 16
    draw_h = target_h - top_margin
    scale = draw_h / float(cropped.height)
    nw = max(1, int(round(cropped.width * scale)))
    nh = draw_h
    resized = cropped.resize((nw, nh), Image.LANCZOS)

    # Keep canvas width compact & right-aligned (316..420) so sprite slides cleanly on right half
    canvas_w = max(316, min(429, nw + 24))
    out = Image.new("RGBA", (canvas_w, target_h), (0, 0, 0, 0))
    paste_x = max(0, canvas_w - nw - 8)
    out.paste(resized, (paste_x, top_margin), resized)

    out_path = os.path.join(TRANSITIONS_DIR, f"vsTrainerSpecial{trainer_id}.png")
    out.save(out_path)
    print(f"[OK] Saved {out_path} ({out.size})")


def _lerp_color(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def build_background(spec: ThemeSpec) -> Image.Image:
    # Render at 2x resolution (1024x768) for clean anti-aliased vector quality -> LANCZOS to 512x384
    W, H = 1024, 768
    img = Image.new("RGBA", (W, H), (*spec.c_dark, 255))
    draw = ImageDraw.Draw(img, "RGBA")

    # 1. Diagonal gradient sweep (dark rich left -> vibrant mid -> bright glow right)
    for step in range(0, W + H + 8, 3):
        t = step / float(W + H)
        if t < 0.55:
            col = _lerp_color(spec.c_dark, spec.c_mid, t / 0.55)
        else:
            col = _lerp_color(spec.c_mid, spec.c_accent, (t - 0.55) / 0.45 * 0.42)
        draw.line([(step, 0), (0, step)], fill=(*col, 255), width=8)

    # 2. Radial spotlight glow centered behind the opponent on the right side (x=720, y=380)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow, "RGBA")
    cx, cy = 735, 370
    for r in range(460, 20, -18):
        alpha = int(14 + 34 * (1.0 - r / 460.0) ** 2)
        col = _lerp_color(spec.c_mid, spec.c_accent, 0.72)
        gdraw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*col, min(64, alpha)))
    glow = glow.filter(ImageFilter.GaussianBlur(28))
    img = Image.alpha_composite(img, glow)

    # 3. Left contrast vignette so white VS text & logo stay razor-legible
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vig, "RGBA")
    for x in range(0, 560, 8):
        alpha = int(130 * (1.0 - x / 560.0) ** 1.4)
        vdraw.line([(x, 0), (x, H)], fill=(*spec.c_dark, alpha), width=9)
    img = Image.alpha_composite(img, vig)

    # 4. Crisp kinetic diagonal speed bands & motif accents
    fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fdraw = ImageDraw.Draw(fx, "RGBA")

    # Universal dynamic diagonal light slashes (clean anime energy sweep)
    slash_specs = [
        (-120, 480, 1140, 120, 44, 28),
        (-120, 560, 1140, 200, 14, 52),
        (-80, 680, 1180, 320, 62, 18),
        (160, 790, 1120, 450, 22, 34),
    ]
    for x1, y1, x2, y2, w_px, a_px in slash_specs:
        fdraw.line([(x1, y1), (x2, y2)], fill=(*spec.c_accent, a_px), width=w_px)

    # Signature thematic motifs rendered smoothly around center-right (cx, cy)
    hi = _lerp_color(spec.c_accent, (255, 255, 255), 0.45)
    m = spec.motif
    if m in ("psychic", "astral", "champion", "morfeo_eclipse"):
        for r, lw, al in [(320, 5, 58), (245, 3, 72), (185, 8, 34), (118, 2, 80)]:
            fdraw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(*hi, al), width=lw)
        # Starburst rays
        num_rays = 16 if m == "champion" else 12
        for i in range(num_rays):
            ang = math.radians(i * (360.0 / num_rays) + 12)
            r0 = 90 if i % 2 == 0 else 140
            r1 = 440 if i % 2 == 0 else 310
            p1 = (cx + math.cos(ang) * r0, cy + math.sin(ang) * r0)
            p2 = (cx + math.cos(ang) * r1, cy + math.sin(ang) * r1)
            fdraw.line([p1, p2], fill=(*hi, 40 if i % 2 == 0 else 22), width=4 if i % 2 == 0 else 2)
    elif m == "clockwork":
        # Ambrosio: sleek clock dial & partial interlocking gear circles
        for gx, gy, gr, teeth in [(cx, cy, 240, 16), (420, 540, 160, 12)]:
            fdraw.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], outline=(*hi, 52), width=6)
            fdraw.ellipse([gx - gr * 0.72, gy - gr * 0.72, gx + gr * 0.72, gy + gr * 0.72], outline=(*spec.c_accent, 38), width=3)
            for t_i in range(teeth):
                ang = math.radians(t_i * (360.0 / teeth))
                p1 = (gx + math.cos(ang) * (gr - 4), gy + math.sin(ang) * (gr - 4))
                p2 = (gx + math.cos(ang) * (gr + 22), gy + math.sin(ang) * (gr + 22))
                fdraw.line([p1, p2], fill=(*hi, 48), width=14)
    elif m in ("water", "grass", "morfeo_rose"):
        # Smooth organic arcs / sweeping ripples
        for r, off in [(180, -30), (260, 20), (350, 70), (430, 120)]:
            fdraw.arc([cx - r, cy - r + off, cx + r, cy + r + off], start=190, end=350, fill=(*hi, 64), width=5)
            fdraw.arc([cx - r, cy - r - off, cx + r, cy + r - off], start=15, end=165, fill=(*spec.c_accent, 44), width=4)
        for bx, by, br in [(560, 190, 26), (860, 220, 18), (620, 540, 20), (880, 520, 32), (470, 310, 12)]:
            fdraw.ellipse([bx - br, by - br, bx + br, by + br], outline=(*hi, 68), width=3)
    elif m in ("bug", "steel", "morfeo_cyber"):
        # Crisp hex / cyber panel lattice around right-center
        hex_r = 66
        dx = hex_r * 1.68
        dy = hex_r * 1.48
        for row in range(1, 6):
            for col in range(4, 10):
                hx = col * dx + (dx * 0.5 if row % 2 else 0)
                hy = row * dy
                if 430 <= hx <= 990 and 80 <= hy <= 690:
                    pts = [
                        (hx + math.cos(math.radians(60 * k + 30)) * (hex_r - 8),
                         hy + math.sin(math.radians(60 * k + 30)) * (hex_r - 8))
                        for k in range(6)
                    ]
                    fdraw.polygon(pts, outline=(*hi, 44), width=3)
    elif m in ("ice", "rock", "morfeo_dragon", "dojo", "fighting", "fire", "claw", "earth", "scholar"):
        # Faceted angular shards / dramatic geometric beams
        shards = [
            [(520, 140), (740, 240), (610, 340)],
            [(760, 110), (960, 210), (830, 390)],
            [(640, 420), (890, 340), (790, 610)],
            [(460, 470), (650, 520), (540, 690)],
        ]
        for poly in shards:
            fdraw.polygon(poly, fill=(*spec.c_accent, 22), outline=(*hi, 55), width=3)
        for ox, oy, sr in [(640, 180, 7), (810, 260, 9), (530, 520, 6), (900, 490, 8)]:
            pts = [(ox, oy - sr * 2), (ox + sr, oy), (ox, oy + sr * 2), (ox - sr, oy)]
            fdraw.polygon(pts, fill=(*hi, 120))

    # Diagonal grid micro-texture near corners (clean vector dots)
    for gx in range(36, 460, 32):
        for gy in range(440, 740, 32):
            fdraw.ellipse([gx - 2, gy - 2, gx + 2, gy + 2], fill=(*hi, 34))

    img = Image.alpha_composite(img, fx)
    final_bg = img.resize((512, 384), Image.LANCZOS).convert("RGB")
    out_path = os.path.join(TRANSITIONS_DIR, f"vsBarSpecial{spec.trainer_id}.png")
    final_bg.save(out_path)
    return final_bg


def _load_bold_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def build_review_sheet() -> None:
    os.makedirs(PREVIEWS_DIR, exist_ok=True)
    # Remove stale card previews from superseded flat-bar approach
    for stale in ("vs_cards_review.png", "vs_mockup_clash.png"):
        sp = os.path.join(PREVIEWS_DIR, stale)
        if os.path.exists(sp):
            os.remove(sp)

    vs_logo = Image.open(os.path.join(TRANSITIONS_DIR, "vs.png")).convert("RGBA")
    border_top = Image.open(os.path.join(TRANSITIONS_DIR, "vsBorder.png")).convert("RGBA")
    border_bot = border_top.rotate(180)
    light_overlay = Image.open(os.path.join(TRANSITIONS_DIR, "vsSpecialLight.png")).convert("RGBA")
    # Make light subtle just like AnimatedPlane scroll shimmer
    r, g, b, a = light_overlay.split()
    a = a.point(lambda v: int(v * 0.25))
    light_overlay = Image.merge("RGBA", (r, g, b, a))

    font_name = _load_bold_font(34)
    font_tag = _load_bold_font(15)
    font_pending = _load_bold_font(18)

    cols = 4
    rows = 5
    card_w, card_h = 512, 384
    thumb_w, thumb_h = 384, 288
    pad = 16
    sheet = Image.new("RGB", (cols * thumb_w + (cols + 1) * pad, rows * thumb_h + (rows + 1) * pad), (18, 20, 28))

    for idx, spec in enumerate(THEMES):
        frame = Image.open(os.path.join(TRANSITIONS_DIR, f"vsBarSpecial{spec.trainer_id}.png")).convert("RGBA")
        frame = Image.alpha_composite(frame, light_overlay)

        # VS shadow & logo centered at (110, 132) (z=0)
        vs_shadow = Image.new("RGBA", vs_logo.size, (0, 0, 0, 0))
        vs_shadow.paste((0, 0, 0, 130), (0, 0), vs_logo)
        frame.paste(vs_shadow, (110 + 16 - vs_logo.width // 2, 132 + 16 - vs_logo.height // 2), vs_shadow)
        frame.paste(vs_logo, (110 - vs_logo.width // 2, 132 - vs_logo.height // 2), vs_logo)

        # Trainer drop shadow (z=0, shifted +22,+22)
        mug_path = os.path.join(TRANSITIONS_DIR, f"vsTrainerSpecial{spec.trainer_id}.png")
        has_mug = os.path.exists(mug_path)
        mug = None
        tx = 0
        if has_mug:
            mug = Image.open(mug_path).convert("RGBA")
            mug_shadow = Image.new("RGBA", mug.size, (0, 0, 0, 0))
            mug_shadow.paste((0, 0, 0, 128), (0, 0), mug)
            tx = card_w - mug.width
            frame.paste(mug_shadow, (tx + 22, 22), mug_shadow)

        # Borders at settled positions: border1.y = 70 - 258 = -188 (width 614), border2 rotated bottom (z=102)
        b_scaled = border_top.resize((614, 258), Image.BILINEAR)
        b_bot_scaled = border_bot.resize((614, 258), Image.BILINEAR)
        frame.paste(b_scaled, (0, 70 - 258), b_scaled)
        frame.paste(b_bot_scaled, (512 - 614, 384 - 70), b_bot_scaled)

        # Trainer mugshot on top of borders (z=103)
        if mug is not None:
            frame.paste(mug, (tx, 0), mug)

        # Trainer Name con estilo épico (Impact inclinada + degradado cobalto + doble borde sticker)
        epic_f = ImageFont.truetype(r"C:\Windows\Fonts\impact.ttf", 46) if os.path.exists(r"C:\Windows\Fonts\impact.ttf") else font_name
        tmp = Image.new("RGBA", (380, 84), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        td.text((22, 10), spec.name, font=epic_f, fill=(255, 255, 255, 255))
        tmp = tmp.transform(tmp.size, Image.AFFINE, (1, 0.22, -12, 0, 1, 0), Image.BILINEAR)
        tpx = tmp.load()
        tw, th = tmp.size
        tmask = [[tpx[x, y][3] > 115 for x in range(tw)] for y in range(th)]
        tout = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        top_px = tout.load()
        for yy in range(4, th - 4):
            for xx in range(4, tw - 4):
                if any(tmask[yy + dy][xx + dx] for dy in range(-4, 5) for dx in range(-4, 5) if dx * dx + dy * dy <= 17):
                    top_px[xx, yy] = (10, 14, 28, 255)
        for yy in range(2, th - 2):
            for xx in range(2, tw - 2):
                if any(tmask[yy + dy][xx + dx] for dy in range(-2, 3) for dx in range(-2, 3) if dx * dx + dy * dy <= 5):
                    top_px[xx, yy] = (248, 250, 255, 255)
        tys = [yy for yy in range(th) if any(tmask[yy])]
        if tys:
            ty0, ty1 = min(tys), max(tys)
            for yy in range(ty0, ty1 + 1):
                tt = (yy - ty0) / max(1, ty1 - ty0)
                if tt < 0.45:
                    kk = tt / 0.45
                    tcol = (int(16 - 10 * kk), int(118 - 62 * kk), 255, 255)
                else:
                    kk = (tt - 0.45) / 0.55
                    tcol = (int(6 - 2 * kk), int(56 - 44 * kk), int(255 - 210 * kk), 255)
                for xx in range(tw):
                    if tmask[yy][xx]:
                        top_px[xx, yy] = tcol
        tbbox = tout.getbbox()
        if tbbox:
            tcropped = tout.crop(tbbox)
            tshadow = Image.new("RGBA", tcropped.size, (0, 0, 0, 0))
            tshadow.paste((0, 0, 0, 135), (0, 0), tcropped)
            frame.paste(tshadow, (52 + 5, 218 + 5), tshadow)
            frame.paste(tcropped, (52, 218), tcropped)

        fdraw = ImageDraw.Draw(frame, "RGBA")

        # Status badge in corner for preview readability
        fdraw.text((14, 10), f"#{spec.trainer_id:03d} {spec.role}", font=font_tag, fill=(215, 225, 245, 230))
        if not has_mug:
            fdraw.rounded_rectangle([246, 152, 492, 208], radius=8, fill=(10, 12, 20, 185), outline=(0, 220, 255, 210), width=2)
            fdraw.text((260, 170), f"vsTrainerSpecial{spec.trainer_id}.png", font=font_tag, fill=(180, 240, 255, 245))

        thumb = frame.convert("RGB").resize((thumb_w, thumb_h), Image.LANCZOS)
        r_idx, c_idx = divmod(idx, cols)
        sheet.paste(thumb, (pad + c_idx * (thumb_w + pad), pad + r_idx * (thumb_h + pad)))

    review_path = os.path.join(PREVIEWS_DIR, "vs_special_review.png")
    sheet.save(review_path)
    print(f"[OK] Saved {review_path} ({sheet.size})")


def main() -> None:
    os.makedirs(TRANSITIONS_DIR, exist_ok=True)
    build_vs_logo()
    build_template_placeholder()
    for spec in THEMES:
        build_background(spec)
    print(f"[OK] Built all {len(THEMES)} vsBarSpecial<ID>.png backgrounds")

    for tid, (raw_path, seeds) in sorted(RAW_MUGSHOTS.items()):
        if os.path.exists(raw_path):
            process_mugshot(tid, raw_path, seeds)
        else:
            print(f"[WARN] Missing raw mugshot {tid}: {raw_path}")

    build_review_sheet()


if __name__ == "__main__":
    main()
