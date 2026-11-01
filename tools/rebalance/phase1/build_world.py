#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_world.py - agente rem-world del proyecto Pokemon REM (Essentials v16, region Oniria).

Genera, de forma reproducible y solo con la libreria estandar de Python 3:

  PBS/rem_locations.txt   64 secciones [LOC_KEY]                       (SPEC 2.1)
  PBS/rem_encounters.txt  48 tablas de encuentros (408 casillas) + 32 de pesca + [SPECIAL_OBTAINABILITY] (721) (SPEC 2.2)
  PBS/encounters.txt      encounters.txt OFICIAL de Essentials v16 con las mismas tablas

Fuentes (solo lectura):
  docs/rebalance/6_World_and_Locations_Master_Guide.md   fichas, tabla 1.4, cruces 1.3, leyenda de nodos
  docs/rebalance/10_Wild_Encounters_Master_Guide.md      Cap. 2 (tablas), Cap. 3 (pesca), Cap. 4/5 (obtencion de las 721)
  docs/rebalance/proposed_pokemon.txt                    InternalName y evoluciones
  PBS_backup_original/encounters.txt                     tablas del prototipo (mapas 1-24) que se conservan tal cual
  tools/codex/location_keys.json                         las 64 claves canonicas

Uso:
  python3 tools/rebalance/phase1/build_world.py            # genera los 3 archivos y ejecuta la validacion
  python3 tools/rebalance/phase1/build_world.py --check    # solo valida los archivos ya generados (no escribe nada)
  python3 tools/rebalance/phase1/build_world.py --dry-run  # construye en memoria y valida, sin escribir

Nada en PBS_backup_original/ ni en Data/ se toca. Los tres archivos se escriben UTF-8 con BOM y CRLF.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / 'docs' / 'rebalance'
PBS = ROOT / 'PBS'
VOL6 = DOCS / '6_World_and_Locations_Master_Guide.md'
VOL10 = DOCS / '10_Wild_Encounters_Master_Guide.md'
PROPOSED_POKEMON = DOCS / 'proposed_pokemon.txt'
KEYS_JSON = ROOT / 'tools' / 'codex' / 'location_keys.json'
LEGACY_ENC = ROOT / 'PBS_backup_original' / 'encounters.txt'
OUT_LOC = PBS / 'rem_locations.txt'
OUT_ENC = PBS / 'rem_encounters.txt'
OUT_PBS = PBS / 'encounters.txt'

sys.path.insert(0, str(ROOT / 'tools' / 'codex'))

MAP_W, MAP_H = 480, 320

# ----------------------------------------------------------------------------------------------------------------------
# Constantes del motor (Essentials v16, 103_PField_Encounters.rb)
# ----------------------------------------------------------------------------------------------------------------------
LAND_W = [20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1]       # Land / Cave / LandDay / LandNight / LandMorning
WATER_W = [60, 30, 5, 4, 1]
ROD_W = {'OldRod': [70, 30], 'GoodRod': [60, 20, 20], 'SuperRod': [40, 40, 15, 4, 1]}
ENC_LEN = {'Land': 12, 'Cave': 12, 'Water': 5, 'RockSmash': 5, 'OldRod': 2, 'GoodRod': 3, 'SuperRod': 5,
           'HeadbuttLow': 8, 'HeadbuttHigh': 8, 'LandMorning': 12, 'LandDay': 12, 'LandNight': 12, 'BugContest': 12}
ENC_WEIGHTS = {'Land': LAND_W, 'Cave': LAND_W, 'Water': WATER_W, 'OldRod': ROD_W['OldRod'], 'GoodRod': ROD_W['GoodRod'],
               'SuperRod': ROD_W['SuperRod'], 'LandNight': LAND_W, 'LandDay': LAND_W, 'LandMorning': LAND_W}
ENC_WRITE_ORDER = ['Land', 'LandNight', 'Cave', 'Water', 'OldRod', 'GoodRod', 'SuperRod']
DENSITY_LINE = '25,10,10'          # Land/Cave/Water: valores por defecto de EnctypeDensities (EnctypeCompileDens = [1,2,3,...])
MAXLEVEL = 100

CATEGORY_MAP = {'CIUDAD': 'Ciudad', 'PUEBLO': 'Pueblo', 'ESPECIAL': 'Lugar especial', 'RUTA_NORMAL': 'Ruta normal',
                'RUTA_ESPECIAL': 'Ruta especial', 'RUTA_MONTANA': 'Ruta de montaña', 'RUTA_MARINA': 'Ruta marina',
                'RUTA_NEVADA': 'Ruta nevada'}
ROUTE_LABELS = {'GRANJA_APATITA': 'E1', 'PLAYA_SEPIOLITA': 'E2', 'ESTEPA_LATERITA': 'E3', 'SENDA_SERPENTINA': 'E4',
                'PUENTE_DOLOMITA': 'E5', 'ACANTILADOS_RODONITA': 'E6', 'RESERVA_PERIDOTO': 'E7', 'CALZADA_CORINDON': 'E8'}
ZONES = {   # ubicaciones con dos mapas de 8 casillas (SPEC 1): clave -> letras de zona
    'LAGO_AMATISTA': ['A', 'B'], 'CIENAGA_LIMONITA': ['A', 'B'], 'LADERA_PORFIDO': ['A', 'B']}
ZONE_B_MAP_IDS = {'LAGO_AMATISTA': 969, 'CIENAGA_LIMONITA': 970, 'LADERA_PORFIDO': 971}
PROVISIONAL_BASE = 900              # mapID provisional = 900 + ProgressionOrder (zonas B: 969, 970, 971)
NO_WILD_BUT_SECTIONS = []           # (reservado)

# Mapas del prototipo (Data/MapInfos.rxdata, lectura): id -> (nombre, id del padre). Solo para documentar la correspondencia.
PROTOTYPE_MAPS = {
    1: ('Intro', 0), 2: ('Pueblo Cianita', 0), 3: ('Casa Player', 2), 4: ('Laboratorio', 2), 5: ('Casas', 2), 6: ('Ruta 1', 0),
    7: ('Pasa Ruta H', 1), 8: ('Centro Pokémon', 1), 9: ('Pueblo Topacio', 0), 10: ('Pasa Ruta', 6), 11: ('Centro Pokémon', 9),
    12: ('Granja Ambarina', 0), 13: ('Torre del Reloj', 9), 14: ('Pozo', 2), 15: ('Casas', 9), 16: ('Guardería', 12),
    17: ('Granero', 12), 18: ('Bosque Turmalino', 0), 19: ('Claro del Bosque', 18), 20: ('Profundidades', 18), 21: ('Cueva', 18),
    22: ('Ruta 2', 0), 23: ('Pasa Ruta V', 1), 24: ('Pasa Ruta', 22)}
# Mapas principales del prototipo que corresponden CON CERTEZA a una de las 64 ubicaciones (el nombre del mapa es un nombre en
# borrador / provisional de la ficha del Vol. 6). Se verifica en check_mapping(): nombre del mapa in {Name, DraftNames} de la ficha.
PROTOTYPE_TO_LOC = {2: 'PUEBLO_IOLITA', 6: 'RUTA_01', 9: 'PUEBLO_HELIODORO', 12: 'GRANJA_APATITA', 18: 'BOSQUE_DIOPTASA', 22: 'RUTA_02'}

# Aliases de lugares para localizar un LOC_KEY dentro de un texto del Vol. 10 (regalos, eventos, legendarios).
PLACE_ALIASES = {'Centro Comercial de Azabache': 'CIUDAD_AZABACHE', 'Mercado Minero': 'PUEBLO_CASITERITA',
                 'Museo de Fósiles': 'PUEBLO_CASITERITA'}

# Geometria de la red de caminos (graph.json del Vol. 6, simplificada a esquinas). Cada ruta agrupa uno o varios tramos
# (polilineas de segmentos horizontales/verticales sobre el mapa de 480x320). Fuente: grafo canonico del Vol. 6 (51 tramos).
ROUTE_CHAINS = {
    'RUTA_01': [[(136, 232), (136, 264)], [(136, 264), (184, 264)]],
    'RUTA_02': [[(232, 280), (296, 280), (296, 264)]],
    'RUTA_04': [[(296, 264), (344, 264), (344, 248)]],
    'RUTA_05': [[(392, 200), (392, 248)]],
    'RUTA_06': [[(344, 168), (344, 200), (392, 200)], [(344, 168), (344, 152), (360, 152)]],
    'RUTA_07': [[(392, 200), (408, 200), (408, 152)]],
    'RUTA_08': [[(184, 152), (216, 152), (216, 168)], [(216, 168), (216, 200)], [(216, 168), (264, 168)]],
    'RUTA_09': [[(152, 152), (184, 152)], [(152, 152), (152, 120), (216, 120)]],
    'RUTA_14': [[(376, 120), (392, 120), (392, 152), (408, 152)]],
    'RUTA_15': [[(216, 120), (264, 120)], [(264, 120), (264, 136), (312, 136)], [(264, 88), (264, 120)]],
    'RUTA_16': [[(344, 88), (376, 88), (376, 120)]],
    'GRANJA_APATITA': [[(184, 264), (232, 264), (232, 280)]],
    'PLAYA_SEPIOLITA': [[(344, 248), (392, 248)]],
    'ESTEPA_LATERITA': [[(264, 168), (344, 168)]],
    'SENDA_SERPENTINA': [[(168, 184), (184, 184), (184, 152)]],
    'PUENTE_DOLOMITA': [[(88, 152), (152, 152)]],
    'ACANTILADOS_RODONITA': [[(120, 72), (120, 88)], [(120, 88), (184, 88)], [(120, 88), (120, 120)]],
    'RESERVA_PERIDOTO': [[(312, 136), (312, 120), (376, 120)]],
    'CALZADA_CORINDON': [[(56, 56), (56, 104)]],
    'RUTA_03': [[(280, 200), (280, 232), (296, 232), (296, 264)]],
    'RUTA_10': [[(56, 104), (56, 120), (88, 120)], [(88, 120), (88, 152)], [(88, 120), (120, 120)]],
    'RUTA_20': [[(136, 232), (184, 232), (184, 216), (216, 216)]],
    'RUTA_21': [[(216, 200), (216, 216)], [(216, 216), (216, 232), (248, 232)]],
    'RUTA_22': [[(216, 200), (280, 200)], [(280, 200), (312, 200)]],
    'RUTA_12': [[(72, 200), (72, 152), (88, 152)]],
    'RUTA_13': [[(72, 200), (104, 200)], [(104, 200), (120, 200), (120, 184)], [(104, 200), (104, 232), (136, 232)]],
    'RUTA_23': [[(408, 152), (424, 152), (424, 72)]],
    'RUTA_24': [[(72, 264), (72, 280), (136, 280), (136, 264)]],
    'RUTA_11': [[(184, 88), (232, 88), (232, 56)]],
    'RUTA_17': [[(264, 88), (296, 88), (296, 56)]],
    'RUTA_18': [[(200, 40), (232, 40), (232, 56)], [(232, 56), (296, 56)]],
    'RUTA_19': [[(296, 56), (344, 56)], [(344, 56), (344, 88)], [(344, 40), (344, 56)]],
}
LAKE_STUB = [(344, 232), (344, 248)]       # acceso al lago: pertenece al nodo Lago Amatista, no a una ruta


# ----------------------------------------------------------------------------------------------------------------------
# Utilidades de texto / markdown
# ----------------------------------------------------------------------------------------------------------------------
def read_text(path):
    return Path(path).read_text(encoding='utf-8-sig').replace('\r\n', '\n')


def clean_md(s):
    """Quita el marcado markdown (negritas, cursivas, <br>) conservando los asteriscos provisionales escapados (\\*)."""
    s = s.replace('\\*', '\x00')
    s = re.sub(r'\*\*(.+?)\*\*', r'\1', s)
    s = re.sub(r'(?<![\w\x00])\*(?=\S)([^*\n]+?)(?<=\S)\*(?!\w)', r'\1', s)
    s = s.replace('<br>', '; ').replace('`', '')
    s = s.replace('\x00', '*')
    return re.sub(r'\s+', ' ', s).strip()


def ini_text(s):
    """Texto apto para un valor INI de una sola linea (sin saltos; el '#' o '=' interiores son parte del valor)."""
    return re.sub(r'\s+', ' ', s.replace('\r', ' ').replace('\n', ' ')).strip()


def list_text(s):
    """Elemento de una lista separada por ';' : los ';' internos pasan a ','."""
    return ini_text(s).replace(';', ',')


def short_name(name):
    return re.sub(r'\s*\(.*?\)\s*$', '', name).strip()


def parse_range(s):
    """'3–5' | '100' | '3-5' -> (3, 5)."""
    m = re.match(r'^\s*(\d+)\s*(?:[–-]\s*(\d+))?\s*$', s)
    if not m:
        return None
    a = int(m.group(1))
    return (a, int(m.group(2)) if m.group(2) else a)


def fmt_range(r):
    if not r:
        return ''
    return str(r[0]) if r[0] == r[1] else '%d-%d' % (r[0], r[1])


def md_cells(line):
    s = line.strip()
    if not s.startswith('|'):
        return None
    return [c.strip() for c in s.strip('|').split('|')]


def opposite_word(d):
    return {'Norte': 'Sur', 'Sur': 'Norte', 'Este': 'Oeste', 'Oeste': 'Este'}[d]


DIR_LETTER = {'Norte': 'N', 'Sur': 'S', 'Este': 'E', 'Oeste': 'O'}


def dir_between(p, q):
    """Rumbo general (eje dominante) de p a q."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    if abs(dy) > abs(dx):
        return 'Sur' if dy > 0 else 'Norte'
    return 'Este' if dx > 0 else 'Oeste'


# ----------------------------------------------------------------------------------------------------------------------
# Claves y especies
# ----------------------------------------------------------------------------------------------------------------------
def load_keys():
    keys = json.load(open(KEYS_JSON, encoding='utf-8'))
    for k in keys:
        k['cat'] = CATEGORY_MAP[k['category']]
    return keys


def load_pokemon():
    """proposed_pokemon.txt -> {dex: dict(sym, name, evo=[(child_sym, method, param)])}."""
    text = read_text(PROPOSED_POKEMON)
    mons, cur = {}, None
    for line in text.split('\n'):
        s = line.strip()
        m = re.match(r'^\[(\d+)\]$', s)
        if m:
            cur = int(m.group(1))
            mons[cur] = {'dex': cur, 'sym': None, 'name': None, 'evo': [], 'types': []}
            continue
        if cur is None or s.startswith('#') or '=' not in s:
            continue
        k, v = s.split('=', 1)
        k = k.strip().lower()
        v = v.strip()
        if k == 'internalname':
            mons[cur]['sym'] = v
        elif k == 'name':
            mons[cur]['name'] = v
        elif k in ('type1', 'type2'):
            mons[cur]['types'].append(v)
        elif k == 'evolutions':
            f = [x.strip() for x in v.split(',')]
            mons[cur]['evo'] = [tuple(f[i:i + 3]) for i in range(0, len(f), 3)]
    return mons


# ----------------------------------------------------------------------------------------------------------------------
# Vol. 6: fichas, tabla 1.4, leyenda de nodos, cruces
# ----------------------------------------------------------------------------------------------------------------------
SLOT_RE6 = re.compile(r'^\|\s*(\d+)\s*\|\s*(Común|Incomún|Raro)\s*\|\s*(\d+) %\s*\|\s*(\d{3})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$')
FISH_RE6 = re.compile(r'^\|\s*(P[12])\s*\|\s*(Común|Raro)\s*\|\s*(\d+) %\s*\|\s*(\d{3})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$')


def parse_vol6(keys):
    lines = read_text(VOL6).split('\n')
    by_name = {k['name']: k['key'] for k in keys}
    res = {'ficha': {}, 'table14': [], 'legend': {}, 'junctions': {}}

    # tabla 1.4 (68 filas)
    i14 = next(i for i, l in enumerate(lines) if l.startswith('## 1.4'))
    iend = next(i for i, l in enumerate(lines) if l.startswith('# Capítulo 2'))
    for l in lines[i14:iend]:
        c = md_cells(l)
        if c and len(c) == 6 and re.match(r'^\d+$', c[0]):
            res['table14'].append({'n': int(c[0]), 'name': clean_md(c[1]), 'day_night': c[4], 'boss': clean_md(c[5])})
    # leyenda de nodos (figura 2) y cruces (1.3)
    i11 = next(i for i, l in enumerate(lines) if l.startswith('## 1.1'))
    for l in lines[i11:i14]:
        c = md_cells(l)
        if c and len(c) == 8 and re.match(r'^\d+$', c[0]):
            for off in (0, 4):
                res['legend'][clean_md(c[off + 1])] = (int(c[off]), c[off + 3].strip())
        if c and len(c) == 3 and (c[0].startswith('Cruce') or c[0].startswith('Nexo')):
            m = re.match(r'^\((\d+),\s*(\d+)\)$', c[1])
            if m:
                res['junctions'][(int(m.group(1)), int(m.group(2)))] = clean_md(c[0])

    # fichas
    ic2 = next(i for i, l in enumerate(lines) if l.startswith('# Capítulo 2'))
    iapa = next(i for i, l in enumerate(lines) if l.startswith('# Apéndice A'))
    heads = [i for i in range(ic2, iapa) if lines[i].startswith('### ') and i + 1 < len(lines) and lines[i + 1].strip() == '<!-- kv -->']
    for hi, start in enumerate(heads):
        end = heads[hi + 1] if hi + 1 < len(heads) else iapa
        # la ficha termina en el siguiente encabezado de nivel 1-3
        for j in range(start + 1, end):
            if re.match(r'^#{1,3} ', lines[j]):
                end = j
                break
        name = lines[start][4:].strip()
        body = lines[start:end]
        f = {'name': name, 'kv': {}, 'events': [], 'slots': [], 'fish': [], 'desc': '', 'chars': '', 'dom': ''}
        in_ev = False
        for l in body:
            m = re.match(r'^\|\s*\*\*(.+?)\*\*\s*\|\s*(.*?)\s*\|\s*$', l)
            if m:
                f['kv'][m.group(1)] = m.group(2)
                continue
            if l.startswith('**Descripción ambiental.**'):
                f['desc'] = l[len('**Descripción ambiental.**'):].strip()
            elif l.startswith('**Personajes presentes.**'):
                f['chars'] = l[len('**Personajes presentes.**'):].strip()
            elif l.startswith('**Dominante / jefe.**'):
                f['dom'] = l[len('**Dominante / jefe.**'):].strip()
            if l.startswith('**Eventos principales'):
                in_ev = True
                continue
            if in_ev:
                if l.startswith('- '):
                    f['events'].append(l[2:].strip())
                elif l.strip() == '':
                    continue
                else:
                    in_ev = False
            m = SLOT_RE6.match(l)
            if m:
                f['slots'].append({'slot': int(m.group(1)), 'rar': m.group(2), 'pct': int(m.group(3)), 'dex': int(m.group(4)),
                                   'name': m.group(5), 'lv': m.group(7)})
            m = FISH_RE6.match(l)
            if m:
                f['fish'].append({'slot': m.group(1), 'rar': m.group(2), 'pct': int(m.group(3)), 'dex': int(m.group(4)),
                                  'name': m.group(5), 'lv': m.group(7)})
        res['ficha'][by_name[name]] = f
    return res


def split_people(text):
    """'Matilde (Líder del Gimnasio 1), Guiomar; estudiantes y bibliotecarios como ambientación.' -> lista."""
    t = clean_md(text).rstrip('.').strip()
    if not t or t in ('—', '-'):
        return []
    out, depth, cur = [], 0, ''
    for ch in t:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        if ch in ',;' and depth == 0:
            if cur.strip():
                out.append(cur.strip())
            cur = ''
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    res = []
    for p in out:
        m = re.match(r'^([A-ZÁÉÍÓÚÑ]\w+) y ([A-ZÁÉÍÓÚÑ]\w+)$', p)      # 'Eladio y Hortensia' -> dos nombres propios
        if m:
            res += [m.group(1), m.group(2)]
        else:
            res.append(p)
    return res


# ----------------------------------------------------------------------------------------------------------------------
# Geometria de rutas
# ----------------------------------------------------------------------------------------------------------------------
def seg_len(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def chain_len(c):
    return sum(seg_len(c[i], c[i + 1]) for i in range(len(c) - 1))


def route_walk(chains):
    """Recorre todos los tramos de una ruta en una sola polilinea. En nudos de 3 ramales se recorre primero el ramal mas corto
    y se retrocede por el mismo trazado al nudo (la polilinea repite esos puntos). Devuelve (puntos, tramos_en_orden_unico)."""
    pts_count = {}
    for c in chains:
        for p in (c[0], c[-1]):
            pts_count[p] = pts_count.get(p, 0) + 1
    leaves = sorted(p for p, n in pts_count.items() if n == 1)
    start = leaves[0] if leaves else chains[0][0]
    used = [False] * len(chains)
    walk = [start]
    order = []

    def go(p):
        inc = [i for i, c in enumerate(chains) if not used[i] and (c[0] == p or c[-1] == p)]
        inc.sort(key=lambda i: chain_len(chains[i]))
        for n, i in enumerate(inc):
            if used[i]:
                continue
            used[i] = True
            c = chains[i] if chains[i][0] == p else list(reversed(chains[i]))
            order.append(c)
            walk.extend(c[1:])
            go(c[-1])
            remaining = [j for j in inc[n + 1:] if not used[j]]
            if remaining:                       # retroceder al nudo para el siguiente ramal
                walk.extend(reversed(c[:-1]))
    go(start)
    assert all(used), 'tramos sin recorrer'
    return walk, order


def point_at(order, dist):
    """Punto situado a 'dist' px de longitud de trazado a lo largo de la concatenacion de tramos."""
    acc = 0
    for c in order:
        for i in range(len(c) - 1):
            L = seg_len(c[i], c[i + 1])
            if acc + L >= dist:
                f = dist - acc
                dx = (c[i + 1][0] > c[i][0]) - (c[i + 1][0] < c[i][0])
                dy = (c[i + 1][1] > c[i][1]) - (c[i + 1][1] < c[i][1])
                return (c[i][0] + dx * f, c[i][1] + dy * f)
            acc += L
    return order[-1][-1]


def first_dir(c):
    """Rumbo con el que el tramo c sale de c[0]."""
    return dir_between(c[0], c[1])


def route_midpoint(chains):
    """Punto medio del trazado de una ruta: punto medio (por longitud) del camino mas largo entre dos extremos (diametro del
    arbol de tramos). En rutas de un solo camino es el punto medio de la polilinea; en rutas ramificadas cae sobre el tronco."""
    adj = {}
    for c in chains:
        adj.setdefault(c[0], []).append((c[-1], c))
        adj.setdefault(c[-1], []).append((c[0], list(reversed(c))))
    leaves = sorted(p for p, e in adj.items() if len(e) == 1)
    best = None
    for u in leaves:
        stack = [(u, None, [], 0)]
        while stack:
            v, par, path, dist = stack.pop()
            if v != u and v in leaves:
                cand = ((-dist, tuple(sorted((u, v)))), path, dist)
                if best is None or cand[0] < best[0]:
                    best = cand
            for w, c in adj[v]:
                if w != par:
                    stack.append((w, v, path + [c], dist + chain_len(c)))
    return point_at(best[1], best[2] // 2)


# ----------------------------------------------------------------------------------------------------------------------
# Vol. 10: tablas por ubicacion (Cap. 2), pesca (Cap. 3), obtencion de las 721 (Cap. 4/5)
# ----------------------------------------------------------------------------------------------------------------------
SLOT_RE10 = re.compile(r'^\|\s*(\d+)\s*\|\s*(Común|Incomún|Raro)\s*\|\s*(\d+) %\s*\|\s*(\d{3})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(Base|Media|Única)\s*\|\s*([^|]*?)\s*\|\s*(.*?)\s*\|\s*$')
FISH_RE10 = re.compile(r'^\|\s*(P[12])\s*\|\s*(Común|Raro) \((\d+) %\)\s*\|\s*(\d{3})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*(.*?)\s*\|\s*$')
RARITY_EN = {'Común': 'COMMON', 'Incomún': 'UNCOMMON', 'Raro': 'RARE'}
RARITY_ES = {'Común': 'Común', 'Incomún': 'Incomún', 'Raro': 'Raro'}


def lv_pair(text):
    """'Día **Nv 3–5** · Noche (+50 %) **Nv 4–7**' -> ((3,5),(4,7)); 'Nv 17–19 día / 25–28 noche' -> ((17,19),(25,28))."""
    m = re.search(r'Nv\s+(\d+)(?:–(\d+))?\s*día\s*/\s*(\d+)(?:–(\d+))?\s*noche', text)
    if m:
        a, b, c, d = m.groups()
        return (int(a), int(b or a)), (int(c), int(d or c))
    ms = re.findall(r'Nv\s+(\d+)(?:–(\d+))?', text)
    if len(ms) >= 2:
        return (int(ms[0][0]), int(ms[0][1] or ms[0][0])), (int(ms[1][0]), int(ms[1][1] or ms[1][0]))
    return None, None


def parse_vol10(keys, mons):
    lines = read_text(VOL10).split('\n')
    by_short = {}
    for k in keys:
        by_short[k['name']] = k['key']
        by_short[short_name(k['name'])] = k['key']
    ic2 = next(i for i, l in enumerate(lines) if l.startswith('# Capítulo 2'))
    ic3 = next(i for i, l in enumerate(lines) if l.startswith('# Capítulo 3'))
    secs = {}
    cur = None
    for l in lines[ic2:ic3]:
        if l.startswith('### '):
            nm = l[4:].strip()
            cur = {'key': by_short[nm], 'name': nm, 'kv': {}, 'zones': [{'name': None, 'day': None, 'night': None, 'slots': []}], 'fish': []}
            secs[cur['key']] = cur
            continue
        if cur is None:
            continue
        m = re.match(r'^####\s+Mapa\s+\d+\s+—\s+(.+?)\s+\(Nv\s+(.+?)\)\s*$', l)
        if m:
            d, n = lv_pair('Nv ' + m.group(2))
            z = {'name': m.group(1), 'day': d, 'night': n, 'slots': []}
            if len(cur['zones']) == 1 and not cur['zones'][0]['slots'] and cur['zones'][0]['name'] is None:
                cur['zones'][0] = z
            else:
                cur['zones'].append(z)
            continue
        m = re.match(r'^\|\s*\*\*(.+?)\*\*\s*\|\s*(.*?)\s*\|\s*$', l)
        if m:
            cur['kv'][m.group(1)] = m.group(2)
            continue
        m = SLOT_RE10.match(l)
        if m:
            cur['zones'][-1]['slots'].append({
                'slot': int(m.group(1)), 'rar': m.group(2), 'pct': int(m.group(3)), 'dex': int(m.group(4)),
                'name': m.group(5), 'stage': m.group(7), 'note': m.group(9)})
            continue
        m = FISH_RE10.match(l)
        if m:
            cur['fish'].append({'slot': m.group(1), 'rar': m.group(2), 'pct': int(m.group(3)), 'dex': int(m.group(4)),
                                'name': m.group(5), 'note': m.group(8)})
    # niveles, tipo de tabla y pesca por ubicacion
    for key, s in secs.items():
        kv = s['kv']
        cat = kv.get('Categoría (Vol. 6)', '')
        m = re.search(r'tabla de (hierba y cueva|hierba|cueva|surf)', cat)
        s['table_kind'] = m.group(1) if m else None
        s['etype'] = {'hierba': 'Land', 'hierba y cueva': 'Land', 'cueva': 'Cave', 'surf': 'Surf'}.get(s['table_kind'])
        s['act_text'] = kv.get('Posición', '')
        s['biome'] = clean_md(kv.get('Bioma (Ley 5)', ''))
        if 'Niveles salvajes' in kv:
            s['day'], s['night'] = lv_pair(kv['Niveles salvajes'])
        else:
            s['day'] = s['night'] = None
        pesca = kv.get('Pesca', '')
        s['fish_ok'] = pesca.startswith('Sí')
        s['fish_day'], s['fish_night'] = lv_pair(pesca) if s['fish_ok'] else (None, None)
        if len(s['zones']) == 1 and s['zones'][0]['day'] is None:
            s['zones'][0]['day'], s['zones'][0]['night'] = s['day'], s['night']
    return secs


def parse_vol10_ch5(keys):
    """Cap. 5: indice de las 721 especies -> {dex: dict(name, cat, loc_text, rar_text)}; Cap. 4.5: mecanismo piedra/objeto."""
    lines = read_text(VOL10).split('\n')
    i5 = next(i for i, l in enumerate(lines) if l.startswith('# Capítulo 5'))
    ia = next(i for i, l in enumerate(lines) if l.startswith('# Apéndice A'))
    idx = {}
    for l in lines[i5:ia]:
        c = md_cells(l)
        if c and len(c) == 6 and re.match(r'^\d{3}$', c[0]):
            idx[int(c[0])] = {'name': c[1], 'types': c[2], 'cat': c[3], 'loc': clean_md(c[4]), 'rar': clean_md(c[5])}
    i45 = next(i for i, l in enumerate(lines) if l.startswith('## 4.5'))
    i46 = next(i for i, l in enumerate(lines) if l.startswith('## 4.6'))
    mech = {}
    for l in lines[i45:i46]:
        c = md_cells(l)
        if c and len(c) == 7 and re.match(r'^\d{3}$', c[0]):
            mech[int(c[0])] = {'from': c[3], 'item': c[4], 'mech': c[5]}
    i31 = next(i for i, l in enumerate(lines) if l.startswith('## 3.1'))
    i32 = next(i for i, l in enumerate(lines) if l.startswith('## 3.2'))
    water = {}
    by_short = {short_name(k['name']): k['key'] for k in keys}
    by_short.update({k['name']: k['key'] for k in keys})
    for l in lines[i31:i32]:
        c = md_cells(l)
        if c and len(c) == 6 and c[0] in by_short:
            mc = re.match(r'^.*\((\d+)\)$', c[3])
            mr = re.match(r'^.*\((\d+)\)$', c[4])
            water[by_short[c[0]]] = {'common': int(mc.group(1)), 'rare': int(mr.group(1)), 'lv': c[2]}
    return idx, mech, water


def place_in_text(text, keys):
    """LOC_KEY del primer lugar canonico que aparece en el texto (coincidencia de nombre mas larga)."""
    cands = {}
    for k in keys:
        cands[k['name']] = k['key']
        cands[short_name(k['name'])] = k['key']
    cands.update(PLACE_ALIASES)
    best = None
    for nm, key in cands.items():
        for m in re.finditer(r'(?<![\w])' + re.escape(nm) + r'(?![\w])', text):
            cand = (m.start(), -len(nm), key)
            if best is None or cand < best:
                best = cand
    return best[2] if best else ''


# ----------------------------------------------------------------------------------------------------------------------
# Ajuste de porcentajes exactos a las casillas fijas del motor (programacion dinamica sobre clases de casillas)
# ----------------------------------------------------------------------------------------------------------------------
_FIT_CACHE = {}


def fit_slots(targets, weights, allow_drop=False, drop_bias=None):
    """Reparte las casillas del motor (pesos 'weights', suma 100) entre especies con porcentaje objetivo 'targets' (enteros;
    ambos en las mismas unidades) minimizando el error absoluto total sum|logrado - objetivo| (desempate: error cuadratico,
    y que las primeras especies usen menos casillas). Cada especie recibe >= 1 casilla salvo que allow_drop=True (entonces
    puede quedar fuera, con coste = su objetivo x drop_bias[i]; asi se descartan primero las de menor sesgo y, a igualdad, las ultimas).
    Devuelve lista de listas de indices de casilla."""
    ck = (tuple(targets), tuple(weights), allow_drop, tuple(drop_bias) if drop_bias else None)
    if ck in _FIT_CACHE:
        return _FIT_CACHE[ck]
    import itertools
    classes = sorted(set(weights), reverse=True)
    cap = tuple(weights.count(w) for w in classes)
    n = len(targets)
    zero = tuple(0 for _ in classes)
    maxdrop = max(0, n - len(weights)) if allow_drop else 0
    dp = [dict() for _ in range(n + 1)]
    dp[0][(zero, 0)] = ((0, 0, 0), None)
    for i, t in enumerate(targets):
        for (state, drops), (cost, _) in dp[i].items():
            rem = [c - s_ for c, s_ in zip(cap, state)]
            for k in itertools.product(*[range(r + 1) for r in rem]):
                nk = sum(k)
                nd = drops + (1 if nk == 0 else 0)
                if nk == 0 and (not allow_drop or nd > maxdrop):
                    continue
                a = sum(kj * w for kj, w in zip(k, classes))
                d = abs(a - t) if nk else int(t * (drop_bias[i] if drop_bias else 1))
                c = (cost[0] + d, cost[1] + d * d, cost[2] + 1000 * i * a + (n - i) * nk)
                ns = (tuple(s_ + kj for s_, kj in zip(state, k)), nd)
                old = dp[i + 1].get(ns)
                if old is None or c < old[0]:
                    dp[i + 1][ns] = (c, ((state, drops), k))
    final = (cap, maxdrop)
    assert final in dp[n], 'sin solucion de ajuste'
    ks = [None] * n
    st = final
    for i in range(n, 0, -1):
        _, (prev, k) = dp[i][st]
        ks[i - 1] = k
        st = prev
    pools = {w: [j for j, ww in enumerate(weights) if ww == w] for w in classes}
    nxt = {w: 0 for w in classes}
    out = []
    for k in ks:
        idxs = []
        for w, kj in zip(classes, k):
            idxs += pools[w][nxt[w]:nxt[w] + kj]
            nxt[w] += kj
        out.append(sorted(idxs))
    _FIT_CACHE[ck] = out
    return out


def slots_to_rows(assign, weights):
    """Lista de listas de indices -> lista (len(weights)) con el indice de especie de cada casilla."""
    rows = [None] * len(weights)
    for sp, idxs in enumerate(assign):
        for j in idxs:
            rows[j] = sp
    assert all(r is not None for r in rows)
    return rows


NIGHT_TYPES = {'DARK', 'GHOST'}
NIGHT_SOFT = {'PSYCHIC', 'POISON'}
DAY_TYPES = {'GRASS', 'FIRE', 'NORMAL', 'FLYING', 'FAIRY', 'WATER', 'ELECTRIC'}


def choose_time_split(rows, types):
    """Para una tabla de 16 especies (no caben en las 12 casillas): devuelve (solo_noche, solo_dia): 4 y 4 especies que se
    excluyen de la tabla de dia (Land) y de la de noche (LandNight) respectivamente, para que las 16 sean obtenibles. Las Raras
    estan siempre en ambas. Criterio: nocturnas = tipo Siniestro/Fantasma (o Psiquico/Veneno); diurnas = Planta/Fuego/Normal/Volador/..."""
    cand = [r for r in rows if r['rar'] != 'Raro']

    def nscore(r):
        t = set(types[r['dex']])
        return 3 * len(t & NIGHT_TYPES) + len(t & NIGHT_SOFT)

    def dscore(r):
        t = set(types[r['dex']])
        return 2 * len(t & DAY_TYPES) - 3 * len(t & NIGHT_TYPES) - len(t & NIGHT_SOFT)
    night = sorted(cand, key=lambda r: (-nscore(r), r['slot']))[:4]
    left = [r for r in cand if r not in night]
    day = sorted(left, key=lambda r: (-dscore(r), r['slot']))[:4]
    return [r['dex'] for r in night], [r['dex'] for r in day]


# ----------------------------------------------------------------------------------------------------------------------
# Construccion del modelo: ubicaciones
# ----------------------------------------------------------------------------------------------------------------------
def level_pair_ficha(text):
    ms = re.findall(r'\*\*(\d+(?:–\d+)?)\*\*', text)
    if len(ms) >= 2:
        return parse_range(ms[0]), parse_range(ms[1])
    return None, None


def row_to_key(name, keys):
    """Nombre de una fila de la tabla 1.4 -> LOC_KEY (None si es un sub-lugar: Geoda Hundida, Umbral de la Liga)."""
    n = clean_md(name)
    n = re.split(r'\s+—\s+', n)[0]
    n = re.sub(r'\s*\((fila [^)]*)\)\s*$', '', n).strip()
    for k in keys:
        if n == k['name'] or n == short_name(k['name']):
            return k['key']
    return None


def build_arms():
    arms = {}
    for rk, chains in ROUTE_CHAINS.items():
        for ci, c in enumerate(chains):
            arms.setdefault(c[0], []).append((rk, ci))
            arms.setdefault(c[-1], []).append((rk, ci))
    for p in (LAKE_STUB[0], LAKE_STUB[-1]):
        arms.setdefault(p, []).append(('LAKE', 0))
    return arms


def parse_node_conn(text, name2key):
    """'**Norte**: Ruta 3 → Cruce de las Rutas 3 y 22; **Este**: ...' -> {'N': (keys, texto), ...}."""
    out = {}
    parts = re.split(r';\s*(?=\*\*(?:Norte|Sur|Este|Oeste)\*\*)', text)
    for part in parts:
        m = re.match(r'^\*\*(Norte|Sur|Este|Oeste)\*\*:\s*(.+)$', part.strip())
        if not m:
            raise ValueError('conexion no reconocida: ' + part)
        d, body = DIR_LETTER[m.group(1)], clean_md(m.group(2))
        ks = []
        if '→' in body:
            left, right = [x.strip() for x in body.split('→', 1)]
            if left in name2key:
                ks.append(name2key[left])
            dest = re.sub(r'\s*\(rumbo general \w+\)\s*$', '', right).strip()
            if dest in name2key:
                ks.append(name2key[dest])
        else:                                   # p.ej. 'Nexo del Lago (Ruta 4 y Playa Sepiolita)': rutas que confluyen
            inner = re.search(r'\((.+)\)', body)
            if inner:
                for tok in re.split(r',\s*|\s+y\s+(?=[A-ZÁÉÍÓÚÑ])', inner.group(1)):
                    if tok.strip() in name2key:
                        ks.append(name2key[tok.strip()])
        out[d] = (ks, body)
    return out


def merge_conn(entries):
    """entries: lista de (dir_letter, keys, text) -> {'N': (keys, text), ...} fusionando las que comparten rumbo."""
    out = {}
    for d, ks, tx in entries:
        cur = out.setdefault(d, ([], []))
        for k in ks:
            if k not in cur[0]:
                cur[0].append(k)
        if tx not in cur[1]:
            cur[1].append(tx)
    return {d: (v[0], '; '.join(v[1])) for d, v in out.items()}


def build_locations(keys, v6, v10, mons):
    by_name = {k['name']: k['key'] for k in keys}
    name_of = {k['key']: k['name'] for k in keys}
    first_row = {}
    for r in v6['table14']:
        key = row_to_key(r['name'], keys)
        if key and key not in first_row:
            first_row[key] = r['n']
    locs = {}
    node_xy, xy_node = {}, {}
    for k in keys:
        f = v6['ficha'][k['key']]
        sit = f['kv'].get('Situación en el mapa')
        if sit:
            m = re.search(r'coordenadas \((\d+),\s*(\d+)\)', sit)
            node_xy[k['key']] = (int(m.group(1)), int(m.group(2)))
            xy_node[node_xy[k['key']]] = k['key']
    arms = build_arms()
    junc = v6['junctions']
    for k in keys:
        key = k['key']
        f = v6['ficha'][key]
        kv = f['kv']
        L = {'key': key, 'name': k['name'], 'cat': k['cat'], 'raw_cat': k['category']}
        L['drafts'] = [clean_md(x) for x in kv['Nombre(s) en borrador'].split(' · ')]
        L['order'] = first_row[key]
        is_node = key in node_xy
        L['node'] = v6['legend'][k['name']][0] if is_node else None
        L['label'] = ('R%d' % int(key.split('_')[1]) if key.startswith('RUTA_') else ROUTE_LABELS.get(key)) if not is_node else None
        if is_node:
            L['act'] = v6['legend'][k['name']][1]
        else:
            m = re.search(r'Acto (I{1,3}|IV|V)\b', v10[key]['act_text'])
            L['act'] = m.group(1)
        L['day'], L['night'] = level_pair_ficha(kv['Niveles salvajes'])
        et_ = clean_md(kv.get('Etimología') or kv.get('Carácter geológico') or '')
        L['etym'] = et_[:1].upper() + et_[1:]
        sit = kv.get('Situación en el mapa') or kv.get('Situación y conexiones exactas (N/S/E/O)')
        sit = sit.replace(': <br>', ': ')
        L['situation'] = clean_md(sit)
        L['desc'] = clean_md(f['desc'])
        L['events'] = [list_text(clean_md(e)) for e in f['events']]
        L['chars'] = [list_text(x) for x in split_people(f['chars'])]
        boss = clean_md(kv.get('Jefes y eventos clave', ''))
        boss = '' if boss in ('—', '-') else boss
        if f['dom']:
            dom = clean_md(f['dom'])
            if boss:        # el nombre del jefe ya esta en «Jefes y eventos clave»: se anade solo el marcador pendiente y la nota
                dom = dom.split(' — ', 1)[1] if ' — ' in dom else dom
                boss = boss + ' — ' + dom
            else:
                boss = dom
        L['boss'] = boss
        if is_node:
            L['coords'] = node_xy[key]
            L['path'] = None
            L['conn'] = parse_node_conn(kv['Conexiones exactas (N/S/E/O)'], {**by_name, **{short_name(n): kk for n, kk in by_name.items()}})
        locs[key] = L
    # rutas: geometria y conexiones
    for key, chains in ROUTE_CHAINS.items():
        L = locs[key]
        walk, _order = route_walk([list(c) for c in chains])
        mid = route_midpoint([list(c) for c in chains])
        L['coords'] = mid
        L['path'] = walk
        entries = []
        ends = []
        for c in chains:
            for p in (c[0], c[-1]):
                if p not in ends:
                    ends.append(p)
        for p in ends:
            d = DIR_LETTER[dir_between(mid, p)]
            if p in xy_node:
                entries.append((d, [xy_node[p]], name_of[xy_node[p]]))
            else:
                other = [a for a in arms.get(p, []) if a[0] != key]
                if not other:
                    continue                      # cruce interno de la propia ruta
                ks = []
                for rk, _ in other:
                    kk = 'LAGO_AMATISTA' if rk == 'LAKE' else rk
                    if kk not in ks:
                        ks.append(kk)
                entries.append((d, ks, junc[p]))
        L['conn'] = merge_conn(entries)
    for key, L in locs.items():
        L.setdefault('conn', {})
    return locs, node_xy, xy_node


# ----------------------------------------------------------------------------------------------------------------------
# Construccion del modelo: encuentros
# ----------------------------------------------------------------------------------------------------------------------
def build_sections(keys, v10, mons, locs):
    """Una seccion por tabla (LOC_KEY o LOC_KEY:ZONA) + secciones solo de pesca. Orden de progresion."""
    sections = []
    for k in sorted(keys, key=lambda k: locs[k['key']]['order']):
        key = k['key']
        s = v10[key]
        has_table = s['etype'] is not None
        zl = ZONES.get(key)
        first = True
        if has_table:
            for zi, z in enumerate(s['zones']):
                sec = {'key': key if not zl else '%s:%s' % (key, zl[zi]), 'loc': key, 'zone': zl[zi] if zl else None,
                       'zone_name': z['name'] if zl else None, 'etype': s['etype'], 'table_kind': s['table_kind'],
                       'day': z['day'], 'night': z['night'], 'biome': s['biome'], 'fish': None, 'rows': []}
                for r in z['slots']:
                    m = mons[r['dex']]
                    sec['rows'].append({'slot': r['slot'], 'rar': r['rar'], 'pct': r['pct'], 'dex': r['dex'], 'sym': m['sym'],
                                        'name': m['name'], 'note': r['note']})
                if zl and zi > 0:
                    sec['fish'] = None
                sections.append(sec)
            if s['fish_ok']:
                sections[-len(s['zones'])]['fish'] = _fish_of(s, mons)
        elif s['fish_ok']:
            sections.append({'key': key, 'loc': key, 'zone': None, 'zone_name': None, 'etype': None, 'table_kind': None,
                             'day': s['fish_day'], 'night': s['fish_night'], 'biome': '', 'fish': _fish_of(s, mons), 'rows': []})
    return sections


def _fish_of(s, mons):
    out = {'day': s['fish_day'], 'night': s['fish_night']}
    for f in s['fish']:
        m = mons[f['dex']]
        out['common' if f['slot'] == 'P1' else 'rare'] = {'pct': f['pct'], 'dex': f['dex'], 'sym': m['sym'], 'name': m['name'], 'note': f['note']}
    assert 'common' in out and 'rare' in out
    return out


def make_pbs_tables(sec, mons):
    """Tablas del encounters.txt oficial para una seccion. Devuelve (tablas, info) con tablas = {tipo: [(sym, min, max)]}."""
    tables, info = {}, {'notes': []}
    rows = sec['rows']
    if rows:
        et = sec['etype']
        n = len(rows)
        if et == 'Surf':
            tgt = [r['pct'] * 100 for r in rows]
            a = fit_slots(tgt, [w * 100 for w in WATER_W])
            tables['Water'] = _expand(rows, a, WATER_W, sec['day'])
            info['ach'] = _achieved(rows, a, WATER_W)
        elif n <= 12:
            tgt = [r['pct'] * 100 for r in rows]
            a = fit_slots(tgt, [w * 100 for w in LAND_W])
            if et == 'Land':
                tables['Land'] = _expand(rows, a, LAND_W, sec['day'])
                tables['LandNight'] = _expand(rows, a, LAND_W, sec['night'])
            else:
                tables['Cave'] = _expand(rows, a, LAND_W, sec['day'])
            info['ach'] = _achieved(rows, a, LAND_W)
        else:                                  # 16 especies: no caben en 12 casillas
            if et == 'Land':
                night_only, day_only = SPLIT_OVERRIDE.get(sec['key']) or choose_time_split(rows, {r['dex']: mons[r['dex']]['types'] for r in rows})
                info['split'] = (night_only, day_only)
                for tname, excl, lv in (('Land', night_only, sec['day']), ('LandNight', day_only, sec['night'])):
                    sub = [r for r in rows if r['dex'] not in excl]
                    tot = sum(r['pct'] for r in sub)
                    tgt = [round(r['pct'] * 10000.0 / tot) for r in sub]
                    a = fit_slots(tgt, [w * 100 for w in LAND_W])
                    tables[tname] = _expand(sub, a, LAND_W, lv)
                    info['ach_' + tname] = (sub, _achieved(sub, a, LAND_W), tot)
            else:
                tgt = [r['pct'] * 100 for r in rows]
                evolved = evolved_dexes(mons)
                bias = [0.3 if r['dex'] in evolved else 3.0 for r in rows]       # se descartan primero las especies que evolucionan de otra (siguen siendo obtenibles)
                a = fit_slots(tgt, [w * 100 for w in LAND_W], allow_drop=True, drop_bias=bias)
                tables['Cave'] = _expand(rows, a, LAND_W, sec['day'])
                info['dropped'] = [r['dex'] for r, idxs in zip(rows, a) if not idxs]
                info['ach'] = _achieved(rows, a, LAND_W)
    if sec['fish']:
        fl = sec['fish']
        lv = fl['day']
        C, R = fl['common']['sym'], fl['rare']['sym']
        tables['OldRod'] = [(C, lv[0], lv[1]), (R, lv[0], lv[1])]
        tables['GoodRod'] = [(C, lv[0], lv[1]), (R, lv[0], lv[1]), (R, lv[0], lv[1])]
        tables['SuperRod'] = [(C, lv[0], lv[1]), (R, lv[0], lv[1]), (C, lv[0], lv[1]), (C, lv[0], lv[1]), (C, lv[0], lv[1])]
    return tables, info


def evolved_dexes(mons):
    sym2dex = {m['sym']: d for d, m in mons.items()}
    return {sym2dex[c] for m in mons.values() for c, _, _ in m['evo']}


def _expand(rows, assign, weights, lv):
    sp = slots_to_rows(assign, weights)
    return [(rows[i]['sym'], lv[0], lv[1]) for i in sp]


def _achieved(rows, assign, weights):
    return [sum(weights[j] for j in idxs) for idxs in assign]


# Reparto de dia/noche para las tablas de 16 especies de tipo hierba (si hace falta forzarlo: clave de seccion -> (dex_solo_noche, dex_solo_dia)).
# Criterio tematico (nocturnas: aves nocturnas, murcielagos, fantasmas, arañas...; diurnas: plantas, insectos de dia, aves de presa...).
SPLIT_OVERRIDE = {
    'BOSQUE_DIOPTASA':      ([163, 167, 509, 261], [406, 540, 664, 209]),   # Hoothoot, Spinarak, Purrloin, Poochyena | Budew, Sewaddle, Scatterbug, Snubbull
    'DESIERTO_HALITA':      ([92, 96, 510, 262], [27, 231, 111, 660]),      # Gastly, Drowzee, Liepard, Mightyena | Sandshrew, Phanpy, Rhyhorn, Diggersby
    'CASCADAS_TRAVERTINAS': ([528, 281, 54, 558], [188, 193, 580, 421]),    # Swoobat, Kirlia, Psyduck, Crustle | Skiploom, Yanma, Ducklett, Cherrim
    'VILLA_ADULARIA':       ([562, 607, 708, 200], [191, 78, 436, 597]),    # Yamask, Litwick, Phantump, Misdreavus | Sunkern, Rapidash, Bronzor, Ferroseed
    'TEMPLO_MOLDAVITA':     ([714, 343, 578, 203], [627, 334, 234, 304]),   # Noibat, Baltoy, Duosion, Girafarig | Rufflet, Altaria, Stantler, Aron
}


# ----------------------------------------------------------------------------------------------------------------------
# [SPECIAL_OBTAINABILITY]: una linea por especie (721)
# ----------------------------------------------------------------------------------------------------------------------
METHODS = ['WILD', 'FISHING', 'STARTER', 'FOSSIL', 'EVENT', 'LEGENDARY', 'EVOLUTION_LEVEL', 'EVOLUTION_ITEM', 'EVOLUTION_STONE', 'THIRD_STAGE']


def evo_text(t):
    """Reescribe el texto del Cap. 5 de evoluciones: 'Evoluciona de X nivel N ...' / 'Evoluciona de X con <objeto> ...'."""
    t = re.sub(r'^Evoluciona desde (.+?) en Nv (\d+) \((.+)\)$', r'Evoluciona de \1 nivel \2 (\3)', t)
    t = re.sub(r'^Evoluciona desde (.+?) \(Nv (\d+)\); (.+)$', r'Evoluciona de \1 nivel \2; \3', t)
    t = re.sub(r'^Usar (.+?) sobre (.+?) \((.+)\)$', r'Evoluciona de \2 con \1 (\3)', t)
    t = re.sub(r'^Usar (.+?) sobre (.+)$', r'Evoluciona de \2 con \1', t)
    return t


def build_obtain(keys, idx, mech, mons, sections):
    sym2dex = {m['sym']: d for d, m in mons.items()}
    parent = {}
    for d, m in mons.items():
        for child, method, param in m['evo']:
            parent[sym2dex[child]] = (d, method, param)
    wild = {}
    for sec in sections:
        for r in sec['rows']:
            det = '%s (%d %%) · Nv %s día / %s noche' % (r['rar'], r['pct'], fmt_range(sec['day']).replace('-', '–'), fmt_range(sec['night']).replace('-', '–'))
            if sec['zone_name']:
                det += ' · ' + sec['zone_name']
            wild[r['dex']] = ('WILD', sec['loc'], fmt_range(sec['day']), det)
        if sec['fish']:
            fl = sec['fish']
            for kind, nm in (('common', 'Común'), ('rare', 'Raro')):
                f = fl[kind]
                det = 'Pesca con caña · %s (%d %%) · Nv %s día / %s noche' % (nm, f['pct'], fmt_range(fl['day']).replace('-', '–'), fmt_range(fl['night']).replace('-', '–'))
                wild[f['dex']] = ('FISHING', sec['loc'], fmt_range(fl['day']), det)
    out = {}
    for dex in range(1, 722):
        r = idx[dex]
        cat, lt, rt = r['cat'], r['loc'], r['rar']
        if cat in ('Salvaje', 'Pesca'):
            out[dex] = wild[dex]
        elif cat == 'Legendario':
            lv = re.search(r'Nv (\d+)', rt)
            out[dex] = ('LEGENDARY', place_in_text(lt, keys), lv.group(1) if lv else '', lt)
        elif cat == 'Evolución por nivel':
            lv = re.search(r'Nv (\d+)', rt)
            out[dex] = ('THIRD_STAGE', '', lv.group(1), evo_text(lt))
        elif cat == 'Evolución por piedra u objeto':
            meth = 'EVOLUTION_STONE' if mech[dex]['mech'] == 'Piedra' else 'EVOLUTION_ITEM'
            out[dex] = (meth, '', '', evo_text(lt))
        else:   # Evento / Fósil / Inicial
            if lt.startswith('Evoluciona desde'):
                lv = re.search(r'Nv (\d+)', rt)
                out[dex] = ('EVOLUTION_LEVEL', '', lv.group(1), evo_text(lt))
            elif rt.startswith('Evolución por nivel desde el inicial'):
                pd, pm, pp = parent[dex]
                pname = idx[pd]['name']
                out[dex] = ('EVOLUTION_LEVEL', '', pp if pm == 'Level' else '',
                            'Evoluciona de %s nivel %s (línea inicial: %s)' % (pname, pp, lt))
            elif 'Museo de Fósiles' in lt:
                lv = re.search(r'Nv (\d+)', rt)
                out[dex] = ('FOSSIL', place_in_text(lt, keys), lv.group(1), lt)
            elif rt.startswith('Inicial') or rt == 'Nv según misión':
                lv = re.search(r'Nv (\d+)', rt)
                out[dex] = ('STARTER', place_in_text(lt, keys), lv.group(1) if lv else '', lt)
            else:
                m = re.search(r'Nv (\d+)–(\d+)', rt)
                out[dex] = ('EVENT', place_in_text(lt, keys), '%s-%s' % m.groups() if m else '', lt)
    return out


# ----------------------------------------------------------------------------------------------------------------------
# Escritura
# ----------------------------------------------------------------------------------------------------------------------
def write_pbs(path, lines):
    data = '\r\n'.join(lines) + '\r\n'
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(data)


def map_id_for(key, order, zone=None):
    inv = {v: k for k, v in PROTOTYPE_TO_LOC.items()}
    if zone == 'B':
        return ZONE_B_MAP_IDS[key]
    return inv.get(key, PROVISIONAL_BASE + order)


def conn_value(conn, d):
    if d not in conn:
        return ''
    ks, tx = conn[d]
    return '%s | %s' % (','.join(ks), tx)


def write_locations(keys, locs):
    out = [
        '# rem_locations.txt - Pokemon REM: las 64 ubicaciones de Oniria (SPEC 2.1). GENERADO por tools/rebalance/phase1/build_world.py desde los Vol. 6 y 10; no editar a mano.',
        '# Formato INI: [LOC_KEY] y Clave = Valor (listas con «;»; rangos de nivel «a-b»; sin comentarios a final de linea). Coordenadas en px sobre Mapa_Final__Esqueleto.png (480x320).',
        '# Nodos: MapCoords = centro del nodo. Rutas: MapCoords = punto medio del trazado y MapPath = polilinea «x,y;x,y;...» de sus tramos (en rutas ramificadas la polilinea retrocede por el nudo y repite sus puntos).',
        '# ConnN/S/E/O = «claves LOC_KEY | texto»: en nodos, la ruta (y el nodo destino) que sale por ese lado; en rutas, el vecino en esa direccion (rumbo general desde el punto medio). Un cruce sin ubicacion propia lista las rutas que confluyen (o ninguna) y su nombre en el texto.',
        '# Etymology: en las 24 rutas numeradas recoge el «Carácter geológico» de la ficha. Claves extra: MapID (ID de mapa de Essentials; MapIDStatus = Existing|Provisional), Zones (ubicaciones de dos mapas). BossInfo conserva los marcadores [Especie y Equipo Pendientes de Asignación].',
    ]
    for k in keys:
        L = locs[k['key']]
        out.append('')
        out.append('[%s]' % L['key'])
        out.append('Name = %s' % L['name'])
        out.append('DraftNames = %s' % '; '.join(L['drafts']))
        out.append('Category = %s' % L['cat'])
        out.append('Act = %s' % L['act'])
        out.append('ProgressionOrder = %d' % L['order'])
        out.append('MapNodeNumber = %s' % (L['node'] if L['node'] else ''))
        out.append('RouteLabel = %s' % (L['label'] or ''))
        out.append('MapCoords = %d,%d' % L['coords'])
        out.append('MapPath = %s' % (';'.join('%d,%d' % p for p in L['path']) if L['path'] else ''))
        for d in 'NSEO':
            out.append('Conn%s = %s' % (d, conn_value(L['conn'], d)))
        out.append('LevelRangeDay = %s' % fmt_range(L['day']))
        out.append('LevelRangeNight = %s' % fmt_range(L['night']))
        out.append('Etymology = %s' % ini_text(L['etym']))
        out.append('Situation = %s' % ini_text(L['situation']))
        out.append('Description = %s' % ini_text(L['desc']))
        out.append('EventsSummary = %s' % '; '.join(L['events']))
        out.append('CharactersPresent = %s' % '; '.join(L['chars']))
        out.append('BossInfo = %s' % ini_text(L['boss']))
        out.append('MapID = %d' % L['mapid'])
        out.append('MapIDStatus = %s' % ('Existing' if L['mapid'] < PROVISIONAL_BASE else 'Provisional'))
        if k['key'] in ZONES:
            zs = L['zones']
            out.append('Zones = %s' % '; '.join('%s:%s (Nv %s día / %s noche; mapa %d)' % (z['zone'], z['name'], fmt_range(z['day']), fmt_range(z['night']), z['mapid']) for z in zs))
    write_pbs(OUT_LOC, out)


def write_encounters(sections, obtain, locs, mons):
    out = [
        '# rem_encounters.txt - Pokemon REM: tablas de encuentros salvajes del Vol. 10 con los porcentajes EXACTOS (SPEC 2.2). GENERADO por tools/rebalance/phase1/build_world.py; no editar a mano.',
        '# Una seccion por tabla: [LOC_KEY] o [LOC_KEY:ZONA] (Lago Amatista, Ciénaga Limonita y Ladera Pórfido tienen dos mapas de 8 casillas). Type = Land|Cave|Surf (vacio si la seccion solo tiene pesca); SlotCount = especies de la tabla.',
        '# SlotN = RAREZA(COMMON|UNCOMMON|RARE),PCT,ESPECIE,MinDia,MaxDia,MinNoche,MaxNoche,Nota tactica (texto libre: puede llevar comas). FishCommon/FishRare = PCT,ESPECIE,MinDia,MaxDia,MinNoche,MaxNoche,Nota (70/30). Claves extra: Zone, LevelDay, LevelNight, Biome, MapID.',
        '# 48 ubicaciones con tabla = 408 casillas (tierra/cueva/surf) + 32 de pesca en 16 puntos de agua (12 con tabla + 4 solo pesca: Ciudad Calaíta, Ciudad Magnetita, Ciudad Azabache, Pueblo Nácar) = 440 especies salvajes, todas distintas.',
        '# [SPECIAL_OBTAINABILITY]: DEX3 = METHOD,LOC_KEY,LEVEL,Detalle para las 721 especies (METHOD en WILD, FISHING, STARTER, FOSSIL, EVENT, LEGENDARY, EVOLUTION_LEVEL, EVOLUTION_ITEM, EVOLUTION_STONE, THIRD_STAGE; LOC_KEY vacio en evoluciones).',
    ]
    for sec in sections:
        loc = sec['loc']
        out.append('')
        out.append('[%s]' % sec['key'])
        out.append('Type = %s' % (sec['etype'] or ''))
        if sec['zone']:
            out.append('Zone = %s' % sec['zone'])
            out.append('ZoneName = %s' % sec['zone_name'])
        out.append('SlotCount = %d' % len(sec['rows']))
        out.append('LevelDay = %s' % fmt_range(sec['day']))
        out.append('LevelNight = %s' % fmt_range(sec['night']))
        if sec['biome']:
            out.append('Biome = %s' % ini_text(sec['biome']))
        out.append('MapID = %d' % sec['mapid'])
        for i, r in enumerate(sec['rows'], 1):
            out.append('Slot%d = %s,%d,%s,%d,%d,%d,%d,%s' % (i, RARITY_EN[r['rar']], r['pct'], r['sym'], sec['day'][0], sec['day'][1],
                                                           sec['night'][0], sec['night'][1], ini_text(r['note'])))
        if sec['fish']:
            fl = sec['fish']
            for key, nm in (('common', 'FishCommon'), ('rare', 'FishRare')):
                f = fl[key]
                out.append('%s = %d,%s,%d,%d,%d,%d,%s' % (nm, f['pct'], f['sym'], fl['day'][0], fl['day'][1], fl['night'][0], fl['night'][1], ini_text(f['note'])))
    out.append('')
    out.append('[SPECIAL_OBTAINABILITY]')
    for dex in range(1, 722):
        meth, loc, lv, det = obtain[dex]
        out.append('%03d = %s,%s,%s,%s' % (dex, meth, loc, lv, ini_text(det)))
    write_pbs(OUT_ENC, out)


def legacy_blocks():
    """Bloques del encounters.txt original del prototipo (PBS_backup_original): {mapid: [lineas]}."""
    blocks, cur = {}, None
    for line in read_text(LEGACY_ENC).split('\n'):
        if line.startswith('#####'):
            cur = None
            continue
        m = re.match(r'^(\d+)\b', line)
        if m and (cur is None):
            cur = int(m.group(1))
            blocks[cur] = []
        if cur is not None and line.strip() != '':
            blocks[cur].append(line.rstrip())
    return blocks


def _err_stats(sec, info):
    """(L1 total en puntos porcentuales, error maximo por especie, nombre de la tabla) de la aproximacion de una seccion."""
    stats = []
    if 'ach' in info:
        tg = [r['pct'] for r in sec['rows']]
        stats.append(('', [abs(a - t) for a, t in zip(info['ach'], tg)]))
    for tn in ('Land', 'LandNight'):
        if 'ach_' + tn in info:
            sub, ach, tot = info['ach_' + tn]
            stats.append((tn, [abs(a - r['pct'] * 100.0 / tot) for a, r in zip(ach, sub)]))
    return stats


def write_pbs_encounters(sections, pbs, locs, mons):
    legacy = legacy_blocks()
    replaced = set(PROTOTYPE_TO_LOC)
    kept = sorted(m for m in legacy if m not in replaced)
    # estadisticas de aproximacion por tipo/tamano de tabla
    groups, order_g = {}, []
    notes_drop, notes_split = [], []
    sym2dex = {m['sym']: d for d, m in mons.items()}
    for sec in sections:
        tables, info = pbs[sec['key']]
        n = len(sec['rows'])
        if sec['etype'] == 'Surf':
            label = 'Water (surf) %d especies' % n
        elif n == 16 and sec['etype'] == 'Land':
            label = 'Land 16 especies -> Land + LandNight (12 + 12)'
        elif n == 16:
            label = 'Cave 16 especies -> 12 casillas (4 descartadas)'
        elif sec['etype']:
            label = '%s %d especies' % ('Land+LandNight' if sec['etype'] == 'Land' else 'Cave', n)
        else:
            continue
        for tn, errs in _err_stats(sec, info):
            if tn == 'LandNight':
                continue            # mismas especies/casillas que Land en la tabla partida; se cuenta una vez por tabla horaria
            ach = info['ach'] if 'ach' in info else info['ach_' + tn][1]
            tgt = [r['pct'] for r in sec['rows']] if 'ach' in info else [round(r['pct'] * 100.0 / info['ach_' + tn][2]) for r in info['ach_' + tn][0]]
            if label not in groups:
                groups[label] = {'n': 0, 'errs': [], 'ex': '%s -> %s' % ('/'.join(str(t) for t in tgt), '/'.join(str(a) for a in ach))}
                order_g.append(label)
            groups[label]['n'] += 1
            groups[label]['errs'].append(sum(errs))
        if 'dropped' in info:
            par = {sym2dex[c]: d for d, pm in mons.items() for c, _, _ in pm['evo']}
            notes_drop.append('%s: %s' % (sec['key'], ', '.join('%s (desde %s)' % (mons[d]['name'], mons[par[d]]['name']) if d in par else '%s (SIN RUTA ALTERNATIVA)' % mons[d]['name'] for d in info['dropped'])))
        if 'split' in info:
            no, do = info['split']
            notes_split.append('%s: solo de noche = %s; solo de dia = %s' % (sec['key'], ', '.join(mons[d]['name'] for d in no), ', '.join(mons[d]['name'] for d in do)))
    out = []
    A = out.append
    A('# encounters.txt - Pokemon REM (Essentials v16). GENERADO por tools/rebalance/phase1/build_world.py; no editar a mano: se regenera con ese script.')
    A('# LOS PORCENTAJES EXACTOS del Vol. 10 (6 casillas 20/15/10; 4 -> 35/20/10; 8 -> 16/10/6; 10 -> 12/10/5; 16 -> 7/6/4; pesca 70/30) estan en PBS/rem_encounters.txt.')
    A('# Aqui cada tabla se ajusta a las casillas FIJAS del motor: Land/Cave/LandNight = 12 casillas [20,20,10,10,10,10,5,5,4,4,1,1]; Water = 5 [60,30,5,4,1]; OldRod = [70,30]; GoodRod = [60,20,20]; SuperRod = [40,40,15,4,1].')
    A('# Metodo: cada casilla del motor se asigna a una especie de modo que el error absoluto total respecto al porcentaje del Vol. 10 sea minimo (cada especie conserva >= 1 casilla). Tablas de 6 especies: EXACTAS (20/20/10+10/10+5/10+5/4+4+1+1).')
    A('# Aproximacion por tipo de tabla (error = suma de |logrado - objetivo| en puntos porcentuales; «objetivo -> logrado» de la primera tabla del grupo, en orden de casilla):')
    for label in order_g:
        g = groups[label]
        mean = sum(g['errs']) / len(g['errs'])
        A('#   %s (%d tablas): %s %s' % (label, g['n'], 'EXACTA' if max(g['errs']) < 0.5 else 'error medio %.1f, maximo %.1f;' % (mean, max(g['errs'])), g['ex']))
    A('# Tierra: Land = niveles de DIA y LandNight = niveles de NOCHE con las mismas especies. Cave/Water/OldRod/GoodRod/SuperRod no tienen variante nocturna en Essentials v16: se emiten los niveles de DIA (los de noche estan en rem_encounters.txt).')
    A('# Pesca: OldRod = 70/30 EXACTO (Comun/Rara); GoodRod = [C,R,R] y SuperRod = [C,R,C,C,C] = 60/40 (con [60,20,20] y [40,40,15,4,1] el 70/30 es imposible); asi las tres canas funcionan. Surf = Water (4 rutas marinas). Densidad 25,10,10 = valores por defecto.')
    A('# Calzada Corindon (hierba y cueva en el Vol. 10) = Land: Essentials no admite Land y Cave en el mismo mapa. Monte Azogue y las ciudades/pueblos sin agua no tienen tabla.')
    if notes_split:
        A('# 16 especies > 12 casillas (tablas de hierba): se reparten entre Land (dia) y LandNight (noche) para que las 16 sean obtenibles; las Raras estan en ambas, 4 especies son solo nocturnas y 4 solo diurnas:')
        for n in notes_split:
            A('#     ' + n)
    if notes_drop:
        A('# 16 especies en tablas de CUEVA (Cave no tiene variante horaria): solo caben 12. Se descartan 4 especies que evolucionan de otra especie salvaje (siguen obtenibles por evolucion; estan en rem_encounters.txt). DECISION PENDIENTE del diseno (p. ej. pasar la mazmorra a Land con terreno de hierba):')
        for n in notes_drop:
            A('#     ' + n)
    A('# CORRESPONDENCIA CON LOS MAPAS DEL PROTOTIPO (Data/MapInfos.rxdata + PBS/metadata.txt, solo lectura):')
    for mid, key in sorted(PROTOTYPE_TO_LOC.items()):
        nm = PROTOTYPE_MAPS[mid][0]
        has = key in {s['loc'] for s in sections}
        legacy_has = mid in legacy
        A('#   mapa %03d «%s» = %s%s' % (mid, nm, key, ' -> tablas del Vol. 10 (sustituyen a las del prototipo)' if has else
                                        (' -> sin salvajes ni pesca en el diseno: se retira su tabla del prototipo' if legacy_has else ' -> sin salvajes ni pesca en el diseno (el prototipo no tenia tabla)')))
    A('#   Mapas hijos/interiores del prototipo (1, 3, 4, 5, 7, 8, 10, 11, 13-17, 19, 20, 21, 23, 24) no son ubicaciones: sus entradas (005 «Casas», 021 «Cueva») y los restos del encounters.txt vanilla sin Map###.rxdata (028-075) se conservan TAL CUAL.')
    A('# MAPAS PROVISIONALES para el resto: ID = 900 + ProgressionOrder (p. ej. RUTA_03 = 908) y 969/970/971 para la 2.a zona de Lago Amatista (Geoda Hundida), Ciénaga Limonita (Refugio de Turba) y Ladera Pórfido (Bastión del Pórfido). Sustituir por el ID real al crear cada mapa.')
    entries = {}
    for m in kept:
        entries[m] = legacy[m]
    for sec in sections:
        tables, info = pbs[sec['key']]
        lines = []
        nm = locs[sec['loc']]['name'] + (' (%s)' % sec['zone_name'] if sec['zone_name'] else '')
        lines.append('%03d # %s - %s' % (sec['mapid'], sec['key'], nm))
        lines.append(DENSITY_LINE)
        for t in ENC_WRITE_ORDER:
            if t in tables:
                lines.append(t)
                for sym, a, b in tables[t]:
                    lines.append('%s,%d,%d' % (sym, a, b))
        entries[sec['mapid']] = lines
    assert len(entries) == len(kept) + len(sections), 'ID de mapa repetido'
    for mid in sorted(entries):
        A('#########################')
        out.extend(entries[mid])
    write_pbs(OUT_PBS, out)
    return entries


# ----------------------------------------------------------------------------------------------------------------------
# Validacion (--check)
# ----------------------------------------------------------------------------------------------------------------------
def parse_encounters_txt(path):
    """Lector estricto del formato de encounters.txt (port de pbCompileEncounters). -> {mapid: (densidades, {tipo: [(esp, min, max)]})}"""
    raw = open(path, 'rb').read()
    errs = []
    if not raw.startswith(b'\xef\xbb\xbf'):
        errs.append('encounters.txt sin BOM')
    text = raw.decode('utf-8-sig')
    lines = []
    for ln in text.replace('\r\n', '\n').split('\n'):
        ln = re.sub(r'\s*#.*$', '', ln)
        ln = re.sub(r'\s+$', '', ln)
        if ln:
            lines.append(ln)
    res, cur, cur_id, need_dens, i = {}, None, None, False, 0
    while i < len(lines):
        ln = lines[i]
        if re.match(r'^\d+$', ln):
            cur_id = int(ln)
            if cur_id in res:
                errs.append('mapa %d repetido' % cur_id)
            cur = [None, {}]
            res[cur_id] = cur
            need_dens = True
            i += 1
            continue
        if ln in ENC_LEN:
            need_dens = False
            n = ENC_LEN[ln]
            rows = []
            for j in range(i + 1, i + 1 + n):
                if j >= len(lines):
                    errs.append('mapa %s: fin de archivo en %s' % (cur_id, ln))
                    break
                f = [x.strip() for x in lines[j].split(',')]
                if len(f) < 2 or not re.match(r'^[A-Za-z0-9]+$', f[0]) or not all(x.isdigit() for x in f[1:3]):
                    errs.append('mapa %s %s: fila invalida «%s»' % (cur_id, ln, lines[j]))
                    break
                lo = int(f[1])
                hi = int(f[2]) if len(f) > 2 else lo
                if not (1 <= lo <= hi <= MAXLEVEL):
                    errs.append('mapa %s %s: niveles invalidos «%s»' % (cur_id, ln, lines[j]))
                rows.append((f[0], lo, hi))
            cur[1][ln] = rows
            i += 1 + n
            continue
        if need_dens:
            nums = ln.split(',')
            if len(nums) < 3:
                errs.append('mapa %s: densidades invalidas «%s»' % (cur_id, ln))
            cur[0] = [int(x) for x in nums if x.strip().isdigit()]
            need_dens = False
            i += 1
            continue
        errs.append('linea no reconocida «%s»' % ln)
        i += 1
    for mid, (d, t) in res.items():
        if any(k in t for k in ('Land', 'LandMorning', 'LandDay', 'LandNight', 'BugContest')) and 'Cave' in t:
            errs.append('mapa %d: Land y Cave en la misma area' % mid)
    return res, errs


def check_files(keys, mons):
    """Validacion de los tres archivos generados contra las fuentes. Devuelve lista de errores (vacia = OK) y un dict de recuentos."""
    import remini_ref
    errs, info = [], {}

    def E(msg):
        errs.append(msg)

    # --- formato de archivos
    for p in (OUT_LOC, OUT_ENC, OUT_PBS):
        if not p.exists():
            E('falta %s' % p.name)
            return errs, info
        raw = p.read_bytes()
        if not raw.startswith(b'\xef\xbb\xbf'):
            E('%s: sin BOM UTF-8' % p.name)
        if b'\n' in raw.replace(b'\r\n', b''):
            E('%s: hay LF sin CR' % p.name)
        if not raw.endswith(b'\r\n'):
            E('%s: no termina en CRLF' % p.name)
    secs_loc, w1 = remini_ref.parse(str(OUT_LOC))
    secs_enc, w2 = remini_ref.parse(str(OUT_ENC))
    for w in w1:
        E('rem_locations.txt: aviso del lector: %s' % (w,))
    for w in w2:
        E('rem_encounters.txt: aviso del lector: %s' % (w,))
    info['sections_loc'] = len(secs_loc)
    # --- 64 ubicaciones con las claves canonicas
    if [s['key'] for s in secs_loc] != [k['key'] for k in keys]:
        E('rem_locations.txt: las 64 secciones no coinciden (orden o claves) con location_keys.json')
    loc = {s['key']: s for s in secs_loc}
    keyset = set(loc)
    pokesyms = {m['sym'] for m in mons.values()}
    sym2dex = {m['sym']: d for d, m in mons.items()}
    # --- rem_locations: coordenadas, conexiones, niveles
    n_nodes = n_routes = 0
    for k in keys:
        s = loc.get(k['key'])
        if s is None:
            continue
        mc = re.match(r'^(\d+),(\d+)$', s.get('MapCoords'))
        if not mc or not (0 <= int(mc.group(1)) < MAP_W and 0 <= int(mc.group(2)) < MAP_H):
            E('%s: MapCoords fuera de %dx%d: %s' % (k['key'], MAP_W, MAP_H, s.get('MapCoords')))
        path = s.get('MapPath')
        is_route = bool(s.get('RouteLabel'))
        if is_route:
            n_routes += 1
            if not path:
                E('%s: ruta sin MapPath' % k['key'])
        else:
            n_nodes += 1
            if path:
                E('%s: nodo con MapPath' % k['key'])
            if not s.get('MapNodeNumber'):
                E('%s: nodo sin MapNodeNumber' % k['key'])
        for pt in [p for p in path.split(';') if p]:
            m = re.match(r'^(\d+),(\d+)$', pt)
            if not m or int(m.group(1)) >= MAP_W or int(m.group(2)) >= MAP_H:
                E('%s: punto de MapPath fuera del mapa: %s' % (k['key'], pt))
        for d in 'NSEO':
            v = s.get('Conn' + d)
            if not v:
                continue
            ks, _, tx = v.partition('|')
            ks = [x for x in ks.strip().split(',') if x]
            tx = tx.strip()
            for kk in ks:
                if kk not in keyset:
                    E('%s: Conn%s apunta a clave inexistente %s' % (k['key'], d, kk))
            if not ks and not re.search(r'Cruce|Nexo', tx):
                E('%s: Conn%s sin claves ni texto de cruce: %s' % (k['key'], d, v))
            if not tx:
                E('%s: Conn%s sin texto' % (k['key'], d))
        if k['cat'] not in ('Ciudad', 'Pueblo') or s.get('LevelRangeDay'):
            pass
        if not s.get('Act') or s.get('Act') not in ('I', 'II', 'III', 'IV', 'V'):
            E('%s: Act invalido' % k['key'])
        if not s.get('ProgressionOrder'):
            E('%s: sin ProgressionOrder' % k['key'])
    info['nodes'], info['routes'] = n_nodes, n_routes
    if (n_nodes, n_routes) != (32, 32):
        E('se esperaban 32 nodos y 32 rutas, hay %d y %d' % (n_nodes, n_routes))
    # --- rem_encounters: secciones, 440 casillas, unicidad, niveles
    enc_secs = [s for s in secs_enc if s['key'] != 'SPECIAL_OBTAINABILITY']
    obt = [s for s in secs_enc if s['key'] == 'SPECIAL_OBTAINABILITY']
    if len(obt) != 1:
        E('falta [SPECIAL_OBTAINABILITY]')
    slots, fish, wild_syms = 0, 0, []
    land_tables = set()
    for s in enc_secs:
        key = s['key']
        base = key.split(':')[0]
        if base not in keyset:
            E('%s: seccion de encuentros con clave inexistente' % key)
            continue
        zone = key.split(':')[1] if ':' in key else None
        if (zone is not None) != (base in ZONES):
            E('%s: zona incoherente' % key)
        et = s.get('Type')
        sl = [(int(k[4:]), v) for _, k, v in s['items'] if re.match(r'^slot\d+$', k)]
        sl.sort()
        if et and et not in ('Land', 'Cave', 'Surf'):
            E('%s: Type invalido %s' % (key, et))
        if sl and not et:
            E('%s: casillas sin Type' % key)
        if len(sl) != int(s.get('SlotCount') or 0):
            E('%s: SlotCount (%s) != numero de casillas (%d)' % (key, s.get('SlotCount'), len(sl)))
        if et:
            land_tables.add(key)
        # niveles de referencia: zona -> LevelDay/Night de la propia seccion; sin zona -> los de la ubicacion
        ld, ln = s.get('LevelDay'), s.get('LevelNight')
        if zone in (None, 'A'):
            if et and (ld != loc[base].get('LevelRangeDay') or ln != loc[base].get('LevelRangeNight')):
                E('%s: LevelDay/Night de la seccion (%s / %s) != LevelRangeDay/Night de la ubicacion (%s / %s)' % (
                    key, ld, ln, loc[base].get('LevelRangeDay'), loc[base].get('LevelRangeNight')))
        pct_sum, prev = 0, None
        for n, v in sl:
            f = v.split(',', 7)
            if len(f) != 8 or f[0] not in ('COMMON', 'UNCOMMON', 'RARE') or f[2] not in pokesyms:
                E('%s: Slot%d invalido: %s' % (key, n, v[:80]))
                continue
            pct_sum += int(f[1])
            lvd = (int(f[3]), int(f[4]))
            lvn = (int(f[5]), int(f[6]))
            if fmt_range(lvd) != ld or fmt_range(lvn) != ln:
                E('%s: Slot%d niveles %s/%s != %s/%s de la seccion' % (key, n, fmt_range(lvd), fmt_range(lvn), ld, ln))
            if not f[7]:
                E('%s: Slot%d sin nota' % (key, n))
            if f[2] in wild_syms:
                E('%s: especie salvaje repetida %s' % (key, f[2]))
            wild_syms.append(f[2])
        if sl and pct_sum != 100:
            E('%s: los porcentajes suman %d, no 100' % (key, pct_sum))
        slots += len(sl)
        fc, fr = s.get('FishCommon'), s.get('FishRare')
        if bool(fc) != bool(fr):
            E('%s: pesca incompleta' % key)
        if fc:
            fish += 2
            a = fc.split(',', 6)
            b = fr.split(',', 6)
            if int(a[0]) != 70 or int(b[0]) != 30:
                E('%s: pesca no es 70/30' % key)
            for f in (a, b):
                if len(f) != 7 or f[1] not in pokesyms:
                    E('%s: linea de pesca invalida %s' % (key, ','.join(f)[:60]))
                    continue
                if f[1] in wild_syms:
                    E('%s: especie de pesca repetida %s' % (key, f[1]))
                wild_syms.append(f[1])
                lvd = (int(f[2]), int(f[3]))
                lvn = (int(f[4]), int(f[5]))
                if lvd[0] > lvd[1] or lvn[0] > lvn[1]:
                    E('%s: niveles de pesca invalidos' % key)
                if zone in (None, 'A') and not et:
                    pass
    info['slots'], info['fish_slots'] = slots, fish
    info['encounter_sections'] = len(enc_secs)
    info['land_tables'] = len(land_tables)
    if slots != 408:
        E('casillas de tierra/cueva/surf: %d (se esperaban 408)' % slots)
    if fish != 32:
        E('casillas de pesca: %d (se esperaban 32)' % fish)
    if len(wild_syms) != 440 or len(set(wild_syms)) != 440:
        E('especies salvajes distintas: %d de %d (se esperaban 440 / 440)' % (len(set(wild_syms)), len(wild_syms)))
    # tablas con casillas por ubicacion: 48 ubicaciones
    locs_with_table = {k.split(':')[0] for k in land_tables}
    info['locations_with_table'] = len(locs_with_table)
    if len(locs_with_table) != 48:
        E('ubicaciones con tabla de tierra/cueva/surf: %d (se esperaban 48)' % len(locs_with_table))
    # 16 puntos de agua con pesca
    fish_locs = {s['key'].split(':')[0] for s in enc_secs if s.get('FishCommon')}
    info['water_points'] = len(fish_locs)
    if len(fish_locs) != 16:
        E('puntos de pesca: %d (se esperaban 16)' % len(fish_locs))
    if 'MONTE_AZOGUE' in {s['key'].split(':')[0] for s in enc_secs}:
        E('Monte Azogue no debe tener tabla')
    # --- SPECIAL_OBTAINABILITY
    seen = {}
    if obt:
        from collections import Counter
        meth = Counter()
        for _, k, v in obt[0]['items']:
            if not re.match(r'^\d{3}$', k):
                E('SPECIAL_OBTAINABILITY: clave invalida %s' % k)
                continue
            f = v.split(',', 3)
            dex = int(k)
            if dex in seen:
                E('SPECIAL_OBTAINABILITY: %s repetida' % k)
            seen[dex] = f
            if len(f) != 4 or f[0] not in METHODS:
                E('SPECIAL_OBTAINABILITY %s: metodo invalido «%s»' % (k, v[:50]))
                continue
            meth[f[0]] += 1
            if f[1] and f[1] not in keyset:
                E('SPECIAL_OBTAINABILITY %s: LOC_KEY inexistente %s' % (k, f[1]))
            if f[0] in ('WILD', 'FISHING', 'STARTER', 'FOSSIL', 'LEGENDARY') and not f[1]:
                E('SPECIAL_OBTAINABILITY %s: %s sin LOC_KEY' % (k, f[0]))
            if f[0].startswith('EVOLUTION') or f[0] == 'THIRD_STAGE':
                if f[1]:
                    E('SPECIAL_OBTAINABILITY %s: evolucion con LOC_KEY' % k)
                if not f[3].startswith('Evoluciona de'):
                    E('SPECIAL_OBTAINABILITY %s: detalle de evolucion inesperado: %s' % (k, f[3][:50]))
        info['obtain'] = len(seen)
        info['obtain_methods'] = dict(meth)
        if sorted(seen) != list(range(1, 722)):
            E('SPECIAL_OBTAINABILITY: no cubre exactamente #001-#721 (%d filas)' % len(seen))
        # coherencia entre las tablas y la obtencion
        for s in enc_secs:
            base = s['key'].split(':')[0]
            for _, k, v in s['items']:
                if re.match(r'^slot\d+$', k):
                    sym = v.split(',', 3)[2]
                    d = sym2dex[sym]
                    if seen.get(d, [''])[0] != 'WILD' or seen[d][1] != base:
                        E('%s: %s no figura como WILD en %s' % (s['key'], sym, base))
                elif k in ('fishcommon', 'fishrare'):
                    sym = v.split(',', 2)[1]
                    d = sym2dex[sym]
                    if seen.get(d, [''])[0] != 'FISHING' or seen[d][1] != base:
                        E('%s: %s no figura como FISHING en %s' % (s['key'], sym, base))
        nw = sum(1 for f in seen.values() if f[0] == 'WILD')
        nf = sum(1 for f in seen.values() if f[0] == 'FISHING')
        if (nw, nf) != (408, 32):
            E('SPECIAL_OBTAINABILITY: %d WILD y %d FISHING (se esperaban 408 y 32)' % (nw, nf))
    # --- encounters.txt oficial
    pbs, perrs = parse_encounters_txt(OUT_PBS)
    errs.extend('encounters.txt: ' + e for e in perrs)
    info['pbs_maps'] = len(pbs)
    ids_seen = set()
    for s in enc_secs:
        mid = int(s.get('MapID'))
        if mid in ids_seen:
            E('%s: MapID %d repetido' % (s['key'], mid))
        ids_seen.add(mid)
        if mid not in pbs:
            E('%s: MapID %d no esta en encounters.txt' % (s['key'], mid))
            continue
        dens, tables = pbs[mid]
        spec_syms = {v.split(',', 3)[2] for _, k, v in s['items'] if re.match(r'^slot\d+$', k)}
        fs = {v.split(',', 2)[1] for _, k, v in s['items'] if k in ('fishcommon', 'fishrare')}
        got = set()
        for t, rows in tables.items():
            if len(rows) != ENC_LEN[t]:
                E('mapa %d %s: %d filas (el motor espera %d)' % (mid, t, len(rows), ENC_LEN[t]))
            if t in ENC_WEIGHTS and sum(ENC_WEIGHTS[t]) != 100:
                E('mapa %d %s: las casillas del motor no suman 100' % (mid, t))
            for sym, a, b in rows:
                if sym not in pokesyms:
                    E('mapa %d %s: especie desconocida %s' % (mid, t, sym))
                got.add(sym)
        if got - spec_syms - fs:
            E('mapa %d: especies en encounters.txt que no estan en rem_encounters.txt: %s' % (mid, sorted(got - spec_syms - fs)))
        # niveles: Land/Cave/Water/rods = dia; LandNight = noche
        ld = parse_range(s.get('LevelDay') or '')
        ln = parse_range(s.get('LevelNight') or '')
        for t, rows in tables.items():
            for sym, a, b in rows:
                if t == 'LandNight':
                    if (a, b) != ln:
                        E('mapa %d LandNight: niveles %s != noche %s' % (mid, (a, b), ln))
                elif t in ('Land', 'Cave', 'Water') and (a, b) != ld:
                    E('mapa %d %s: niveles %s != dia %s' % (mid, t, (a, b), ld))
        # cobertura: sin tablas partidas, todas las especies de la tabla estan en el motor
        missing = spec_syms - got
        if missing:
            info.setdefault('not_in_engine', {})[s['key']] = sorted(missing)
        if s.get('Type') == 'Land' and 'Land' in tables and 'LandNight' not in tables:
            E('mapa %d: Land sin LandNight' % mid)
        for t in ('OldRod', 'GoodRod', 'SuperRod'):
            if fs and t not in tables:
                E('mapa %d: pesca sin %s' % (mid, t))
    info['legacy_maps_kept'] = sorted(m for m in pbs if m < PROVISIONAL_BASE and m not in PROTOTYPE_TO_LOC.values() and m not in PROTOTYPE_TO_LOC)
    return errs, info


def check_sources(keys, v6, v10, mons, locs, sections):
    """Comprobaciones cruzadas Vol. 6 <-> Vol. 10 (ficha vs tabla): especies, porcentajes y niveles por casilla."""
    errs = []
    for sec in sections:
        pass
    for k in keys:
        f6 = v6['ficha'][k['key']]
        s10 = v10[k['key']]
        rows10 = [r for z in s10['zones'] for r in z['slots']]
        if len(f6['slots']) != len(rows10):
            errs.append('%s: %d casillas en el Vol. 6 y %d en el Vol. 10' % (k['key'], len(f6['slots']), len(rows10)))
            continue
        zi = 0
        flat = []
        for zi, z in enumerate(s10['zones']):
            for r in z['slots']:
                flat.append((z, r))
        for a, (z, b) in zip(f6['slots'], flat):
            if (a['dex'], a['pct'], a['rar']) != (b['dex'], b['pct'], b['rar']):
                errs.append('%s: casilla %d difiere (Vol. 6 %s vs Vol. 10 %s)' % (k['key'], a['slot'], (a['dex'], a['pct']), (b['dex'], b['pct'])))
            m = re.match(r'^(\d+(?:–\d+)?)\s*/\s*(\d+(?:–\d+)?)$', a['lv'])
            if not m or parse_range(m.group(1)) != z['day'] or parse_range(m.group(2)) != z['night']:
                errs.append('%s: niveles de la casilla %d (%s) != zona %s/%s' % (k['key'], a['slot'], a['lv'], z['day'], z['night']))
        fl = {f['slot']: f for f in f6['fish']}
        if s10['fish_ok']:
            for sl in ('P1', 'P2'):
                f10 = next(f for f in s10['fish'] if f['slot'] == sl)
                if sl not in fl or fl[sl]['dex'] != f10['dex']:
                    errs.append('%s: pesca %s difiere entre Vol. 6 y Vol. 10' % (k['key'], sl))
        elif f6['fish']:
            errs.append('%s: pesca en el Vol. 6 pero no en el Vol. 10' % k['key'])
    return errs


def check_mapping(keys, locs):
    """Verifica que cada mapa del prototipo declarado como equivalente tiene un nombre que es el Name o un DraftName de la ficha."""
    errs = []
    for mid, key in PROTOTYPE_TO_LOC.items():
        nm = PROTOTYPE_MAPS[mid][0]
        L = locs[key]
        names = {L['name'], short_name(L['name'])} | {short_name(d) for d in L['drafts']}
        if nm not in names:
            errs.append('mapa %d «%s» no coincide con %s (%s)' % (mid, nm, key, sorted(names)))
    return errs


# ----------------------------------------------------------------------------------------------------------------------
# Orquestacion
# ----------------------------------------------------------------------------------------------------------------------
def build_all():
    keys = load_keys()
    mons = load_pokemon()
    v6 = parse_vol6(keys)
    v10 = parse_vol10(keys, mons)
    locs, node_xy, xy_node = build_locations(keys, v6, v10, mons)
    for k in keys:
        L = locs[k['key']]
        L['mapid'] = map_id_for(k['key'], L['order'])
        if k['key'] in ZONES:
            L['zones'] = []
            for zl, z in zip(ZONES[k['key']], v10[k['key']]['zones']):
                L['zones'].append({'zone': zl, 'name': z['name'], 'day': z['day'], 'night': z['night'],
                                   'mapid': map_id_for(k['key'], L['order'], zl)})
    sections = build_sections(keys, v10, mons, locs)
    for sec in sections:
        sec['mapid'] = map_id_for(sec['loc'], locs[sec['loc']]['order'], sec['zone'])
    pbs = {sec['key']: make_pbs_tables(sec, mons) for sec in sections}
    idx, mech, water = parse_vol10_ch5(keys)
    obtain = build_obtain(keys, idx, mech, mons, sections)
    return {'keys': keys, 'mons': mons, 'v6': v6, 'v10': v10, 'locs': locs, 'sections': sections, 'pbs': pbs,
            'idx': idx, 'mech': mech, 'water': water, 'obtain': obtain}


def cross_checks(D):
    """Coherencia entre fuentes (Vol. 6 vs Vol. 10, Cap. 3/5, prototipo)."""
    errs = []
    keys, mons, v6, v10, locs, sections = D['keys'], D['mons'], D['v6'], D['v10'], D['locs'], D['sections']
    errs += check_sources(keys, v6, v10, mons, locs, sections)
    errs += check_mapping(keys, locs)
    # Cap. 3.1: pesca = Cap. 2
    for key, w in D['water'].items():
        sec = next((s for s in sections if s['loc'] == key and s['fish']), None)
        if not sec or sec['fish']['common']['dex'] != w['common'] or sec['fish']['rare']['dex'] != w['rare']:
            errs.append('Cap. 3.1 y Cap. 2 difieren en la pesca de %s' % key)
    if len(D['water']) != 16:
        errs.append('Cap. 3.1: %d puntos de agua' % len(D['water']))
    # Cap. 5 vs tablas: ubicacion por nombre
    name_by_key = {k['key']: k['name'] for k in keys}
    for dex, (meth, loc, lv, det) in D['obtain'].items():
        if meth == 'WILD':
            r5 = D['idx'][dex]
            if r5['cat'] != 'Salvaje' or (short_name(name_by_key[loc]) != r5['loc'] and name_by_key[loc] != r5['loc']):
                if not r5['loc'].startswith(short_name(name_by_key[loc])):
                    errs.append('#%03d: Cap. 5 dice «%s» y las tablas «%s»' % (dex, r5['loc'], name_by_key[loc]))
        elif meth == 'FISHING':
            if D['idx'][dex]['cat'] != 'Pesca':
                errs.append('#%03d: Cap. 5 no lo clasifica como Pesca' % dex)
    # prototipo: nombre de cada mapa del prototipo existente (MapInfos) vs metadata.txt
    meta = PBS / 'metadata.txt'
    if meta.exists():
        cur = None
        for line in read_text(meta).split('\n'):
            m = re.match(r'^\[(\d+)\]$', line.strip())
            if m:
                cur = int(m.group(1))
            elif line.startswith('# ') and cur in PROTOTYPE_MAPS and line[2:].strip() != PROTOTYPE_MAPS[cur][0]:
                errs.append('metadata.txt: mapa %d se llama «%s» y MapInfos dice «%s»' % (cur, line[2:].strip(), PROTOTYPE_MAPS[cur][0]))
    return errs


def summarize(D):
    pbs, sections, mons = D['pbs'], D['sections'], D['mons']
    lines = []
    for sec in sections:
        tables, info = pbs[sec['key']]
        for tn, errs in _err_stats(sec, info):
            lines.append((sec['key'] + (':' + tn if tn else ''), len(errs), sum(errs), max(errs)))
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true', help='solo valida los archivos ya generados (no escribe)')
    ap.add_argument('--dry-run', action='store_true', help='construye en memoria y valida sin escribir')
    ap.add_argument('--verbose', '-v', action='store_true')
    args = ap.parse_args(argv)
    D = build_all()
    errs = cross_checks(D)
    if not args.check:
        if not args.dry_run:
            write_locations(D['keys'], D['locs'])
            write_encounters(D['sections'], D['obtain'], D['locs'], D['mons'])
            write_pbs_encounters(D['sections'], D['pbs'], D['locs'], D['mons'])
            print('escritos: %s, %s, %s' % (OUT_LOC.relative_to(ROOT), OUT_ENC.relative_to(ROOT), OUT_PBS.relative_to(ROOT)))
    if args.dry_run and not args.check:
        print('--dry-run: no se escribe nada; la validacion de archivos se omite (usa el modo normal o --check).')
        file_errs, info = [], {}
    else:
        file_errs, info = check_files(D['keys'], D['mons'])
    errs += file_errs
    print('--- recuentos ---')
    for k, v in sorted(info.items()):
        print('  %-22s %s' % (k, v))
    if args.verbose:
        for row in summarize(D):
            print('  aproximacion %-34s especies=%2d L1=%6.2f max=%6.2f' % row)
    if errs:
        print('--- %d ERRORES ---' % len(errs))
        for e in errs:
            print('  ERROR', e)
        return 1
    print('VALIDACION OK (0 errores)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
