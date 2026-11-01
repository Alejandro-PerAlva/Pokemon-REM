"""Inventario de gráficos disponibles en ``Graphics/`` (iconos, sprites de combate, iconos de objeto, hojas de tipos)."""
import os
import re
import struct

_RE_ICON = re.compile(r"^icon(\d{3,4})\.png$", re.I)
_RE_BATTLER = re.compile(r"^(\d{3,4})(b|s|sb)?\.png$", re.I)
_RE_ITEM = re.compile(r"^item(\d{3,4})\.png$", re.I)


def png_size(path):
    """(ancho, alto) de un PNG leyendo solo la cabecera IHDR; None si no es PNG."""
    try:
        with open(path, "rb") as f:
            h = f.read(24)
        if h[:8] == b"\x89PNG\r\n\x1a\n" and h[12:16] == b"IHDR":
            w, hh = struct.unpack(">II", h[16:24])
            return int(w), int(hh)
    except OSError:
        pass
    return None


def _scan(d):
    try:
        with os.scandir(d) as it:
            return [e.name for e in it if e.is_file()]
    except OSError:
        return []


def dir_stamp(graphics_dir):
    """Marca barata de cambios (mtimes de las carpetas) para invalidar el inventario."""
    out = []
    for sub in ("Icons", "Battlers", "Pictures"):
        p = os.path.join(graphics_dir, sub)
        try:
            st = os.stat(p)
            out.append((sub, st.st_mtime_ns))
        except OSError:
            out.append((sub, 0))
    return tuple(out)


def _sprite_sheet(graphics_dir, rel, n_types):
    p = os.path.join(graphics_dir, *rel.split("/"))
    sz = png_size(p)
    return {"file": rel, "exists": sz is not None, "w": sz[0] if sz else 0, "h": sz[1] if sz else 0}


def scan_assets(graphics_dir, n_types=19):
    icons, battlers, back, shiny, shiny_back, item_icons = set(), set(), set(), set(), set(), []
    for name in _scan(os.path.join(graphics_dir, "Icons")):
        m = _RE_ICON.match(name)
        if m:
            icons.add(int(m.group(1)))
            continue
        if _RE_ITEM.match(name):
            item_icons.append(name)
    for name in _scan(os.path.join(graphics_dir, "Battlers")):
        m = _RE_BATTLER.match(name)
        if not m:
            continue
        n = int(m.group(1))
        suf = (m.group(2) or "").lower()
        {"": battlers, "b": back, "s": shiny, "sb": shiny_back}[suf].add(n)
    # hojas de tipos: filas por tipo (tipos.png y pokedexTypes.png comparten número de filas)
    tp = _sprite_sheet(graphics_dir, "Pictures/types.png", n_types)
    pd = _sprite_sheet(graphics_dir, "Pictures/pokedexTypes.png", n_types)
    cat = _sprite_sheet(graphics_dir, "Pictures/category.png", n_types)
    rows = None
    for n in range(max(n_types, 1), 64):
        ok = True
        for sh in (tp, pd):
            if sh["exists"] and (sh["h"] % n != 0 or sh["h"] // n < 14):
                ok = False
        if ok and (tp["exists"] or pd["exists"]):
            rows = n
            break
    for sh in (tp, pd):
        sh["rows"] = rows if (rows and sh["exists"]) else 0
        sh["rowH"] = (sh["h"] // rows) if (rows and sh["exists"]) else 0
    cat["rows"] = 3 if cat["exists"] else 0
    cat["rowH"] = (cat["h"] // 3) if cat["exists"] else 0
    item_icons.sort()
    return {"icons": sorted(icons), "battlers": sorted(battlers), "battlersBack": sorted(back),
            "battlersShiny": sorted(shiny), "battlersShinyBack": sorted(shiny_back),
            "itemIcons": item_icons,
            "sprites": {"types": tp, "pokedexTypes": pd, "category": cat},
            "missing": []}
