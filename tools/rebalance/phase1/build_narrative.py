#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pokémon REM — generador de la capa narrativa (agente `rem-narrative`).

Produce, a partir de los volúmenes de diseño (solo lectura), tres archivos INI en `PBS/`:

    PBS/rem_progression.txt   68 pasos [STEP_01]..[STEP_68]      (Vol. 6 §1.4 + Vol. 9)
    PBS/rem_characters.txt    [CHAR_*] (todos los del Vol. 7)     (Vol. 7 + Vol. 6 «Personajes presentes»)
    PBS/rem_story.txt         [PRELUDE], [CHAPTER_01..68], [FRAGMENT_LEDGER]   (Vol. 8)

Uso:
    python3 tools/rebalance/phase1/build_narrative.py           # genera los tres archivos y valida
    python3 tools/rebalance/phase1/build_narrative.py --check   # no escribe: regenera en memoria, compara con
                                                                # el disco y ejecuta TODAS las validaciones
Solo usa la biblioteca estándar. Contrato: tools/codex/SPEC.md (§0, §1, §2.5, §2.6, §2.7, §6).
No toca ningún otro archivo de PBS/, ni PBS_backup_original/, ni Data/.

Reglas de normalización del texto (todas las salidas):
  * `\\*` (asterisco escapado de Markdown) -> `*` literal (así `[EN REVISIÓN\\*]` -> `[EN REVISIÓN*]`).
  * se eliminan los marcadores de énfasis `**negrita**` y `*cursiva*`; el texto no se resume ni se recorta.
  * un párrafo = una línea; los espacios se colapsan.
"""
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
DOCS = os.path.join(ROOT, 'docs', 'rebalance')
PBS = os.path.join(ROOT, 'PBS')
sys.path.insert(0, os.path.join(ROOT, 'tools', 'codex'))
import remini_ref  # noqa: E402  (lector de referencia del dialecto rem_*.txt)

OUT_PROG = os.path.join(PBS, 'rem_progression.txt')
OUT_CHAR = os.path.join(PBS, 'rem_characters.txt')
OUT_STORY = os.path.join(PBS, 'rem_story.txt')

# --------------------------------------------------------------------------------------------
# Utilidades de texto
# --------------------------------------------------------------------------------------------
_STAR = '\x00'


def clean(s):
    """Texto plano de una celda/párrafo Markdown (ver cabecera)."""
    s = s.replace('\\*', _STAR).replace('\\_', '_').replace('`', '')
    s = re.sub(r'\*\*(.+?)\*\*', r'\1', s)
    s = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', s)
    s = s.replace(_STAR, '*')
    return re.sub(r'\s+', ' ', s).strip()


def norm(s):
    """Normalización para comparar nombres (sin tildes, minúsculas)."""
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', s).casefold().strip()


def read_lines(path):
    with open(path, encoding='utf-8') as f:
        return f.read().split('\n')


def split_row(line):
    cells = line.strip()
    if cells.startswith('|'):
        cells = cells[1:]
    if cells.endswith('|'):
        cells = cells[:-1]
    return [c.strip() for c in cells.split('|')]


def is_sep_row(line):
    return bool(re.match(r'^\s*\|[\s:\-|]+\|\s*$', line))


def table_rows(lines):
    """Filas (listas de celdas crudas) de las líneas que forman una tabla; salta cabecera vacía y separador."""
    rows = []
    for l in lines:
        if not l.strip().startswith('|') or is_sep_row(l):
            continue
        rows.append(split_row(l))
    return rows


def kv_table(lines):
    """Tabla `| **Etiqueta** | valor |` -> dict (etiquetas sin asteriscos)."""
    d = {}
    for r in table_rows(lines):
        if len(r) >= 2 and r[0].startswith('**'):
            d[clean(r[0])] = r[1]
    return d


def cap1(s):
    s = s.strip()
    return s[:1].upper() + s[1:]


def roman(n):
    return {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V'}[n]


# --------------------------------------------------------------------------------------------
# Ubicaciones (claves canónicas, tools/codex/location_keys.json)
# --------------------------------------------------------------------------------------------
EXTRA_ALIASES = {
    'LAGO_AMATISTA': ['Geoda Hundida'],
    'CIENAGA_LIMONITA': ['Refugio de Turba'],
    'LADERA_PORFIDO': ['Bastión del Pórfido'],
    'MESETA_CELESTITA': ['Umbral de la Liga', 'Liga Pokémon'],
    'CALZADA_CORINDON': ['Calle Victoria'],
}


def load_locations():
    with open(os.path.join(ROOT, 'tools', 'codex', 'location_keys.json'), encoding='utf-8') as f:
        locs = json.load(f)
    keys = [l['key'] for l in locs]
    names = {l['key']: l['name'] for l in locs}
    pats = []
    for l in locs:
        als = {l['name']}
        m = re.match(r'^(.*?)\s*\((.*)\)\s*$', l['name'])
        if m:
            als.add(m.group(1))
            als.add(m.group(2))
        als.update(EXTRA_ALIASES.get(l['key'], []))
        for a in als:
            pats.append((len(a), l['key'], re.compile(r'(?<!\w)' + re.escape(a) + r'(?![\w])', re.I)))
    pats.sort(key=lambda t: -t[0])
    return keys, names, pats


LOC_KEYS, LOC_NAMES, _LOC_PATS = load_locations()
LOC_KEYSET = set(LOC_KEYS)


def locs_in_text(text):
    """LOC_KEYs mencionadas en `text`, en orden de aparición (sin repetir)."""
    found = []
    for _, key, rx in _LOC_PATS:
        for m in rx.finditer(text):
            found.append((m.start(), key))
    found.sort()
    out = []
    for _, k in found:
        if k not in out:
            out.append(k)
    return out


def loc_from_text(text):
    r = locs_in_text(text)
    return r[0] if r else None


# --------------------------------------------------------------------------------------------
# Fuentes
# --------------------------------------------------------------------------------------------
V6 = os.path.join(DOCS, '6_World_and_Locations_Master_Guide.md')
V7 = os.path.join(DOCS, '7_Characters_Master_Guide.md')
V8 = os.path.join(DOCS, '8_Story_Novella_Master_Guide.md')
V9 = os.path.join(DOCS, '9_Items_and_Economy_Master_Guide.md')
ITEMS = os.path.join(DOCS, 'proposed_items.txt')


def parse_v6_table_14():
    """68 filas de la Tabla Maestra 1.4 del Vol. 6."""
    lines = read_lines(V6)
    i0 = next(i for i, l in enumerate(lines) if l.startswith('## 1.4 Tabla Maestra'))
    i1 = next(i for i, l in enumerate(lines) if l.startswith('# Capítulo 2'))
    rows = []
    for r in table_rows(lines[i0:i1]):
        if len(r) == 6 and r[0].isdigit():
            rows.append(dict(n=int(r[0]), name=clean(r[1]), draft=clean(r[2]), cat=clean(r[3]),
                             wild=clean(r[4]), events=clean(r[5])))
    return rows


def parse_range(txt):
    """'3–5' -> (3,5); '100' -> (100,100); '—' -> None."""
    t = txt.strip().replace('–', '-').replace('—', '-')
    m = re.match(r'^(\d+)\s*-\s*(\d+)$', t)
    if m:
        return int(m.group(1)), int(m.group(2))
    if t.isdigit():
        return int(t), int(t)
    return None


def parse_v9_locations():
    """Cap. 5 del Vol. 9: {LOC_KEY: dict(act, tms=[n], items=[nombre])} + tabla 4.3 (MT -> LOC_KEY)."""
    lines = read_lines(V9)
    i0 = next(i for i, l in enumerate(lines) if l.startswith('# Capítulo 5'))
    i1 = next(i for i, l in enumerate(lines) if l.startswith('# Capítulo 6'))
    act = None
    cur = None
    by_loc = {}
    for l in lines[i0:i1]:
        m = re.match(r'^## Acto (I|II|III|IV|V)\b', l)
        if m:
            act = m.group(1)
            continue
        m = re.match(r'^### (.+?)\s*$', l)
        if m:
            name = clean(m.group(1).replace('\\*', ''))
            key = loc_from_text(name)
            cur = by_loc.setdefault(key, dict(act=act, tms=[], items=[], name=name))
            continue
        if cur is not None and l.startswith('|') and not is_sep_row(l):
            c = split_row(l)
            if len(c) >= 5 and c[0].isdigit():
                nm = clean(c[1])
                mt = re.match(r'^MT(\d+)\b', nm)
                if mt:
                    cur['tms'].append(int(mt.group(1)))
                cur['items'].append(re.sub(r'\s*×\d+$', '', nm))
    # tabla 4.3 (una MT, una ubicación)
    j0 = next(i for i, l in enumerate(lines) if l.startswith('## 4.3 Tabla maestra'))
    j1 = next(i for i, l in enumerate(lines) if l.startswith('# Capítulo 5'))
    tm_loc = {}
    for r in table_rows(lines[j0:j1]):
        if len(r) >= 8 and re.match(r'^MT\d+$', r[0]):
            tm_loc[int(r[0][2:])] = loc_from_text(clean(r[5]))
    return by_loc, tm_loc


def parse_item_symbols():
    """proposed_items.txt -> {SYMBOL: (id, nombre, bolsillo)}"""
    out = {}
    with open(ITEMS, encoding='utf-8-sig') as f:
        for l in f:
            if l.startswith('#') or not l.strip():
                continue
            m = re.match(r'^(\d+),([A-Z0-9_]+),([^,]*),([^,]*),(\d+),', l)
            if m:
                out[m.group(2)] = (int(m.group(1)), m.group(3), int(m.group(5)))
    return out


# --------------------------------------------------------------------------------------------
# PROGRESIÓN — datos de diseño por paso (lo que los volúmenes no dan en forma de tabla)
# --------------------------------------------------------------------------------------------
# ObjectiveSummary: UNA frase, sin spoilers (qué hace el jugador, no giros de trama).
SUMMARY = {
    1: 'Despídete de tu madre, recibe tu primer Pokémon en el laboratorio del Profesor y parte de viaje junto a Lucián y Guiomar.',
    2: 'Recorre la primera ruta practicando la captura y el combate con los Pokémon salvajes y los entrenadores novatos.',
    3: 'Atraviesa Pueblo Heliodoro, el pueblo de los molinos, y presencia la primera charla pública del Equipo Morfeo.',
    4: 'Visita la granja y su guardería Pokémon y mide tus fuerzas con tu rival Lucián.',
    5: 'Explora el bosque hasta el claro oculto y enfréntate al primer Dominante, guardián de un fragmento de orbe.',
    6: 'Sigue la ruta hacia Ciudad Calcedonia y afronta tu primer duelo serio contra Guiomar.',
    7: 'Llega a Ciudad Calcedonia, busca a la líder Matilde y, resuelto el aviso de la Ruta 3, conquista la Medalla 1 en su gimnasio de tipo Normal.',
    8: 'Recorre la cueva de la Ruta 3 junto a Matilde para despejar el paso de los intrusos que la ocupan.',
    9: 'Avanza por la Ruta 4 hacia el lago y acepta el combate de prueba que te propone una entrenadora desconocida.',
    10: 'Cruza la playa, conoce a un surfista rescatista y sigue la costa hacia el este.',
    11: 'Ayuda a Ciudad Calaíta frente a unos intrusos, convence a Ismael de abrir su gimnasio y gana la Medalla 2 (tipo Agua).',
    12: 'Sube por la ruta árida hacia el norte, donde te cruzas con una figura severa del Equipo Morfeo.',
    13: 'Descansa en el Pueblo Pedernal, conoce a un viajero de incógnito y acepta investigar los rumores del lago.',
    14: 'Investiga la orilla del lago Amatista junto a tu nuevo aliado hasta descubrir una entrada secreta.',
    15: 'Recorre la Geoda Hundida, la primera base del Equipo Morfeo, y derrota a su comandante.',
    16: 'Reencuéntrate con Lucián en la Ruta 6 y acude con él a la central eléctrica, que ha dejado de funcionar.',
    17: 'Entra en la central averiada y enfréntate, junto a Lucián, al segundo Dominante.',
    18: 'Sigue la Ruta 7 hacia Ciudad Magnetita y mide tus fuerzas con Guiomar.',
    19: 'Llega al puerto de Ciudad Magnetita y, tras el viaje a la Isla Opalina, conquista la Medalla 3 frente a Argos en su gimnasio de tipo Acero.',
    20: 'Viaja en barco a la Isla Opalina para buscar a Argos y recorre su mirador, un tramo sin Pokémon salvajes.',
    21: 'Cruza la Estepa Laterita rumbo al desierto, donde una vieja conocida pondrá a prueba tu progreso.',
    22: 'Atraviesa el Desierto Halita y observa desde lejos los movimientos del Equipo Morfeo antes de que la tormenta de arena lo cubra todo.',
    23: 'Continúa por la Ruta 8 hacia Ciudad Nefrita y presencia el entrenamiento del futuro líder de Lucha.',
    24: 'Supera al maestro Genzo en su dojo de Ciudad Nefrita, gana la Medalla 4 y reúnete con tus aliados.',
    25: 'Sigue la Senda Serpentina con Lucián y acepta su reto antes de explorar las ruinas cercanas.',
    26: 'Explora las Ruinas Atacamita hasta su corazón y enfréntate en solitario al tercer Dominante.',
    27: 'Recorre el tramo accesible de la Ruta 9, donde alguien se detiene a cuidar a los Pokémon heridos.',
    28: 'Cruza el Puente Dolomita y enfréntate a Guiomar, que te esperaba al otro lado.',
    29: 'Recorre la metrópolis de Ciudad Azabache, busca a Fausto en el casino y conquista la Medalla 5 (tipo Roca).',
    30: 'Asciende por las cuevas de la Ruta 10 y ayuda a desactivar el bloqueo de generadores que cierra el paso.',
    31: 'Descubre la cueva oculta tras la catarata y enfréntate, junto a Lucián, al cuarto Dominante.',
    32: 'Recorre los Acantilados Rodonita y conoce al primer guardián de las grutas, que te muestra una entrada sellada.',
    33: 'Visita el pueblo minero, recoge el premio de Fausto (un fósil a tu elección) y descubre cómo devolverlo a la vida.',
    34: 'Atraviesa el camino nevado de la Ruta 11 y encuentra a Guiomar, detenida por la nieve.',
    35: 'Surca la ruta marina de la Ruta 12: te espera un nuevo duelo frente al mar y la invitación de un viejo pescador.',
    36: 'Visita al pescador en Pueblo Nácar, recibe tu primera caña de pescar y escucha la leyenda de una isla temida.',
    37: 'Navega por la Ruta 13 y conoce a la segunda guardiana de las grutas, que te habla de una gruta submarina.',
    38: 'Viaja en barca a la Isla Obsidiana, escucha las voces de su niebla y huye de la isla junto a tus amigos.',
    39: 'Regresa a la costa este por la Ruta 14 y mide tu progreso en un duelo amistoso con Lucián mientras los Pokémon salvajes bloquean el camino al norte.',
    40: 'Visita la Reserva Peridoto y conoce a un cuidador que enseña a los niños a tratar con amabilidad a los Pokémon.',
    41: 'Llega a Ciudad Venturina y, tras ayudar a su líder Hildegarda con las hierbas de la Ruta 15, conquista la Medalla 6 en su gimnasio de tipo Planta.',
    42: 'Ayuda a Hildegarda a recolectar hierbas medicinales en la Ruta 15 antes de que acepte tu desafío.',
    43: 'Usa la hierba calmante para abrir el paso de la Ruta 16, donde te espera una conversación inesperada.',
    44: 'Explora la villa abandonada y derrota al Dominante que custodia su fragmento.',
    45: 'Infíltrate en la ciénaga junto a un aliado, asalta la segunda base del Equipo Morfeo y derrota a su comandante.',
    46: 'Sube al pueblo de montaña y acepta el duelo que te propone una vieja conocida.',
    47: 'Despeja la nieve de la Ruta 17 con la ayuda de Guiomar y de la líder del gimnasio de la ciudad.',
    48: 'Ahuyenta el alboroto de la plaza de Ciudad Alabastro, derrota a Isolda en su salón de baile helado y gana la Medalla 7 (tipo Hielo).',
    49: 'Sigue a los alborotadores por la Ruta 19, descubre la gruta helada y conoce a la tercera guardiana de las grutas.',
    50: 'Alcanza la Ruta 18 cuando un rugido del templo te obliga a decidir a quién ayudar primero.',
    51: 'Entra en el templo ancestral y calma, junto a Lucián, al sexto Dominante.',
    52: 'Asalta la última base del Equipo Morfeo en la ladera y derrota a su comandante.',
    53: 'Recorre la cueva de la Ruta 20 y acepta el duelo con el que Guiomar busca afirmarse.',
    54: 'Cruza la Ruta 21 y conoce al cuarto guardián de las grutas, que te señala la entrada de la gruta volcánica.',
    55: 'Gana la Medalla 8 contra Baltasar y reúnete con tus aliados antes del tramo final.',
    56: 'Avanza por la Ruta 22 entre oleadas de reclutas hasta el pie del Monte Azogue.',
    57: 'Asciende el Monte Azogue y afronta los combates decisivos de la cima, donde se juega el destino de los orbes.',
    58: 'Navega por la Ruta 23 hacia la Isla Opalina mientras el mar repite tus pensamientos.',
    59: 'Coloca la orbe lunar en el altar de la Isla Opalina y calma al guardián de la isla.',
    60: 'Cruza la Ruta 24 hacia la Isla Obsidiana, cada vez más pesada por las voces turbias del mar.',
    61: 'Coloca la orbe oscura en el altar de la Isla Obsidiana y calma al guardián de la isla.',
    62: 'Con las ocho medallas, explora la Gruta Hialina y busca al guardián del Alto Mando que la custodia.',
    63: 'Navega con la Tabla de Surf hasta la Gruta Azurita y busca a la guardiana del Alto Mando que la custodia.',
    64: 'Recorre la Gruta Labradorita, cubierta de hielo eterno, y busca a la guardiana del Alto Mando que la custodia.',
    65: 'Desciende a la Gruta Pirita, de fuego y roca, y busca al guardián del Alto Mando que la custodia.',
    66: 'Asciende por la Calzada Corindón y mide a tus dos amigos en sendos duelos finales.',
    67: 'Llega a las puertas de la Liga, donde alguien que ya conoces te espera para un último combate.',
    68: 'Cruza la Liga Pokémon, supera uno a uno a los cuatro del Alto Mando y desafía al Campeón.',
}

# Jefe/gimnasio del paso: (título, tipo, nivel). Los títulos y niveles se contrastan con la celda
# «Jefes y eventos clave» de la tabla 1.4 (ver check_progression). Sin entrada = sin combate de jefe.
BOSS = {
    4: ('Rival Lucián', '', 9),
    5: ('Dominante 1 (Siniestro/Volador)', 'Siniestro/Volador', 13),
    6: ('Rival Guiomar', '', 14),
    7: ('Gimnasio 1 — Matilde', 'Normal', 16),
    8: ('Reclutas del Equipo Morfeo', '', 15),
    9: ('Subcapitana Nerea', '', 19),
    11: ('Gimnasio 2 — Ismael', 'Agua', 25),
    15: ('General Zenobia', '', 28),
    16: ('Rival Lucián', '', 26),
    17: ('Dominante Eléctrico', 'Eléctrico', 31),
    18: ('Rival Guiomar', '', 32),
    19: ('Gimnasio 3 — Argos', 'Acero', 35),
    21: ('Subcapitana Nerea', '', 38),
    22: ('Reclutas del Equipo Morfeo', '', 36),
    24: ('Gimnasio 4 — Genzo', 'Lucha', 41),
    25: ('Rival Lucián', '', 42),
    26: ('Dominante Veneno', 'Veneno', 45),
    28: ('Rival Guiomar', '', 46),
    29: ('Gimnasio 5 — Fausto', 'Roca', 49),
    31: ('Dominante Hada', 'Hada', 52),
    35: ('Subcapitana Nerea', '', 55),
    39: ('Rival Lucián', '', 48),
    41: ('Gimnasio 6 — Hildegarda', 'Planta', 54),
    44: ('Dominante Fantasma', 'Fantasma', 58),
    45: ('General Zenobia (combate final)', '', 60),
    46: ('Subcapitana Nerea', '', 62),
    48: ('Gimnasio 7 — Isolda', 'Hielo', 64),
    51: ('Dominante Dragón', 'Dragón', 66),
    52: ('General Alarico (combate final)', '', 68),
    53: ('Rival Guiomar', '', 69),
    55: ('Gimnasio 8 — Baltasar', 'Fuego', 70),
    56: ('Oleadas de reclutas del Equipo Morfeo', '', 60),
    57: ('Prof. Ambrosio (Nv 73) / Líder Eliseo (Nv 75)', '', 75),
    59: ('Cresselia', 'Psíquico/Hada', 75),
    61: ('Darkrai', 'Siniestro/Fantasma', 75),
    66: ('Rivales Lucián y Guiomar', '', 76),
    67: ('Subcapitana Nerea (combate final)', '', 77),
    68: ('Alto Mando (Nv 77-79) y Campeón Roldán', '', 80),
}

# Objetos clave (ITEM_ID PBS de proposed_items.txt) que el jugador recibe en el paso (Vol. 9 Cap. 5 y §1.3.3).
# Se omiten los que dependen de misiones de Pía por nº de capturas (Buscaobjetos, Repartir Exp, Amuletos) y los
# objetos de legendarios opcionales (Espejo Veraz, Gracídea, Punta ADN, Vasija Castigo): no marcan progreso de historia.
KEY_ITEMS = {
    1: ['TOWNMAP', 'SHEARS', 'POKEVIAL', 'INFINITECANDY'],
    4: ['WAILMERPAIL'],
    5: ['NIGHTMAREFRAG1'],
    8: ['PICKAXE'],
    11: ['BICYCLE'],
    17: ['LUNARFRAG1'],
    19: ['SURFBOARD'],
    26: ['NIGHTMAREFRAG2'],
    29: ['COINCASE'],
    31: ['LUNARFRAG2'],
    35: ['GOODROD'],
    36: ['OLDROD'],
    41: ['GLOVES', 'CALMHERB'],
    44: ['NIGHTMAREFRAG3'],
    51: ['LUNARFRAG3'],
    57: ['DREAMORB', 'NIGHTMAREORB', 'CRACKEDWATCH'],
    61: ['SUPERROD'],
    62: ['SEALCRYSTAL'],
    63: ['SEALABYSS'],
    64: ['SEALGLACIER'],
    65: ['SEALVOLCANO'],
}
# Objetos cuyo cuadro de ubicación (Vol. 9) no coincide con la ubicación del paso donde se reciben.
KEY_ITEM_LOC_EXCEPTIONS = {(61, 'SUPERROD'): 'PUEBLO_NACAR'}

# Habilidades de campo que pasan a ser utilizables en el paso (objeto obtenido antes; umbral de medallas, Vol. 9 §1.3.3).
FIELD_ABILITIES = {
    11: ['Corte (Tijeras; 2 medallas)'],
    19: ['Golpe Roca (Pico; 3 medallas)'],
    24: ['Surf (Tabla de Surf; 4 medallas)'],
    35: ['Pesca (Caña Buena)'],
    36: ['Pesca (Caña Vieja)'],
    41: ['Fuerza (Guantes de Fuerza; 6 medallas)'],
}

# MT cuyo paso no es el de la primera visita a su ubicación (visitas múltiples; texto del Vol. 9 / Vol. 6).
TM_STEP_OVERRIDE = {
    25: 14,   # Reflejo: orilla del lago (paso 14); Pantalla Luz es botín de la Geoda (paso 15)
    24: 15,
    35: 20,   # Beso Drenaje: mirador de la primera visita
    100: 59,  # Deseo: regalo de Cresselia (altar, 2.ª visita)
    60: 38,   # Infortunio: orilla de la primera visita
    93: 61,   # Teletransporte: altar oscuro, 2.ª visita
    76: 68,   # tienda de la Liga (Meseta), no el Umbral
    97: 68,
}

# Capítulos del Vol. 8 que corresponden a cada paso (ver nota en el informe: los capítulos no siguen 1:1 los pasos).
STEP_CHAPTERS = {
    1: [1], 2: [2], 3: [3], 4: [4], 5: [5], 6: [6], 7: [7, 9], 8: [8], 9: [10], 10: [11], 11: [12], 12: [13],
    13: [14], 14: [15], 15: [15], 16: [16], 17: [17], 18: [18], 19: [19, 21], 20: [20], 21: [22], 22: [23],
    23: [24], 24: [25], 25: [26], 26: [27], 27: [28], 28: [29], 29: [30], 30: [31], 31: [32], 32: [33],
    33: [34], 34: [35], 35: [36], 36: [37], 37: [38], 38: [39], 39: [40], 40: [41], 41: [42, 44], 42: [43],
    43: [45], 44: [46], 45: [47], 46: [48], 47: [49], 48: [50], 49: [51], 50: [52], 51: [53], 52: [54],
    53: [55], 54: [56], 55: [57], 56: [58], 57: [59], 58: [60], 59: [61], 60: [62], 61: [63], 62: [64],
    63: [64], 64: [64], 65: [64], 66: [65], 67: [66], 68: [67, 68],
}

SPOILER_WORDS = ['Ambrosio', 'Eliseo', 'Zenobia', 'Alarico', 'Nerea', 'Darkrai', 'Cresselia', 'traidor', 'traición',
                 'traiciona', 'Archivista', 'redimid', 'redención', 'coronad', 'Campeón de Oniria', 'Líder Supremo',
                 'fuga', 'escapa', 'Reloj Agrietado', 'Roldán']


def build_progression():
    rows = parse_v6_table_14()
    assert [r['n'] for r in rows] == list(range(1, 69)), 'la tabla 1.4 debe tener 68 filas consecutivas'
    by_loc9, tm_loc = parse_v9_locations()
    # MT -> paso
    first_step = {}
    for r in rows:
        k = loc_from_text(r['name'])
        first_step.setdefault(k, r['n'])
    tm_step = {}
    for n in range(1, 101):
        k = tm_loc[n]
        tm_step[n] = TM_STEP_OVERRIDE.get(n, first_step[k])
    steps = []
    for r in rows:
        n = r['n']
        key = loc_from_text(r['name'])
        wd = parse_range(r['wild'].split('/')[0]) if '/' in r['wild'] else None
        wn = parse_range(r['wild'].split('/')[1]) if '/' in r['wild'] else None
        boss = BOSS.get(n)
        # acto: el de la ubicación en su primera visita; las revisitas son del Acto V
        if first_step[key] == n or key == 'LAGO_AMATISTA':
            act = by_loc9[key]['act']
        else:
            act = 'V'
        steps.append(dict(
            n=n, key=key, name=r['name'], act=act, summary=SUMMARY[n], wd=wd, wn=wn, events=r['events'],
            boss=boss, items=KEY_ITEMS.get(n, []), field=FIELD_ABILITIES.get(n, []),
            tms=sorted(t for t in range(1, 101) if tm_step[t] == n), chapters=STEP_CHAPTERS[n]))
    # medallas al terminar el paso (gimnasios = títulos «Gimnasio N — ...»)
    medals = 0
    for s in steps:
        if s['boss'] and s['boss'][0].startswith('Gimnasio '):
            medals += 1
        s['medals'] = medals
    # topes de nivel
    nxt = {}
    nb = None
    for i in range(68, 0, -1):
        nxt[i] = nb
        if steps[i - 1]['boss']:
            nb = steps[i - 1]['boss'][2]
    capd = capn = 0
    cum = 0
    for s in steps:
        i = s['n']
        c = [capd]
        if s['wd']:
            c.append(s['wd'][1])
        if s['boss']:
            c.append(s['boss'][2])
        if nxt[i]:
            c.append(nxt[i])
        capd = max(c)
        capn = max(capn, capd, s['wn'][1] if s['wn'] else 0)
        s['capd'], s['capn'] = capd, capn
        cum += len(s['tms'])
        s['tmcum'] = cum
    return steps, by_loc9, tm_loc


def fmt_range(r):
    if not r:
        return ''
    return str(r[0]) if r[0] == r[1] else '%d-%d' % r


HEADER_PROG = [
    '# Pokémon REM — Progresión del viaje: 68 pasos (Vol. 6 §1.4 + Vol. 9). Generado por tools/rebalance/phase1/build_narrative.py; no editar a mano.',
    '# Formato INI (UTF-8 BOM, CRLF): [STEP_NN] con «Clave = Valor». Listas separadas por «;». Rangos de nivel «a-b». LocationKey = LOC_KEY de tools/codex/location_keys.json.',
    '# LevelCapDay = máx(tope anterior, nivel salvaje máx. de día del paso, nivel del jefe del paso, nivel del siguiente jefe). LevelCapNight = máx(tope nocturno anterior, LevelCapDay, nivel salvaje máx. de noche del paso). Ambos monótonos.',
    '# RecommendedTMsAvailable = MT NUEVAS en este paso (Vol. 9 Cap. 5; recuento acumulado en RecommendedTMsCumulative). KeyItemsUnlocked = ITEM_ID PBS recibidos en el paso; FieldAbilitiesUnlocked = habilidades de campo que el paso hace utilizables.',
    '# BossOrGymTitle, BossType, BossLevelCap y KeyEvents reproducen el Vol. 6 (pueden revelar trama; la interfaz debe tratarlos como spoiler). ObjectiveSummary, en cambio, no contiene spoilers.',
    '# Chapters = capítulos del Vol. 8 asociados al paso (en [CHAPTER_NN] de rem_story.txt). Los pasos no coinciden 1:1 con los capítulos.',
]


def emit_progression(steps):
    out = list(HEADER_PROG)
    for s in steps:
        b = s['boss']
        out += [
            '',
            '[STEP_%02d]' % s['n'],
            'StepNumber = %d' % s['n'],
            'Act = %s' % s['act'],
            'LocationKey = %s' % s['key'],
            'StepName = %s' % s['name'],
            'ObjectiveSummary = %s' % s['summary'],
            'LevelCapDay = %d' % s['capd'],
            'LevelCapNight = %d' % s['capn'],
            'BossOrGymTitle = %s' % (b[0] if b else ''),
            'BossType = %s' % (b[1] if b else ''),
            'BossLevelCap = %s' % (b[2] if b else ''),
            'RecommendedTMsAvailable = %s' % ';'.join('TM%02d' % t for t in s['tms']),
            'RecommendedTMsCumulative = %d' % s['tmcum'],
            'KeyItemsUnlocked = %s' % ';'.join(s['items']),
            'FieldAbilitiesUnlocked = %s' % ';'.join(s['field']),
            'MedalsAfterStep = %d' % s['medals'],
            'WildLevelsDay = %s' % fmt_range(s['wd']),
            'WildLevelsNight = %s' % fmt_range(s['wn']),
            'KeyEvents = %s' % s['events'],
            'Chapters = %s' % ';'.join('CHAPTER_%02d' % c for c in s['chapters']),
        ]
    return out


# --------------------------------------------------------------------------------------------
# PERSONAJES (Vol. 7) — definición de la lista cerrada y extracción de fichas
# --------------------------------------------------------------------------------------------
# slug, sección del Vol. 7, categoría, alias de escena (nombres tal como aparecen en el Vol. 8 y variantes),
# nombres con los que se detecta la presencia en las fichas del Vol. 6 («Personajes presentes»).
CHAR_DEFS = [
    dict(slug='PROTAGONISTA', sec='1.4', cat='Protagonista',
         aliases=['Tú (Protagonista)', 'Tú', 'El Protagonista', 'Héroe Silencioso'], presence=[]),
    dict(slug='AMBROSIO', sec='1.1', cat='Aliado',
         aliases=['Ambrosio', 'Profesor Ambrosio', 'Prof. Ambrosio'], presence=['Ambrosio'],
         allegiance='Equipo Morfeo (en secreto; Archivista de Morfeo)'),
    dict(slug='LUCIAN', sec='1.2', cat='Rival', aliases=['Lucián'], presence=['Lucián']),
    dict(slug='GUIOMAR', sec='1.3', cat='Rival', aliases=['Guiomar'], presence=['Guiomar']),
    dict(slug='ELISEO', sec='2.1', cat='Equipo Morfeo', aliases=['Eliseo', 'Líder Eliseo', 'Líder Supremo Eliseo'],
         presence=['Eliseo']),
    dict(slug='NEREA', sec='2.2', cat='Equipo Morfeo', aliases=['Nerea', 'Subcapitana Nerea'], presence=['Nerea']),
    dict(slug='ZENOBIA', sec='2.3', cat='Equipo Morfeo',
         aliases=['Zenobia', 'Comandante Zenobia', 'General Zenobia'], presence=['Zenobia']),
    dict(slug='ALARICO', sec='2.4', cat='Equipo Morfeo',
         aliases=['Alarico', 'Comandante Alarico', 'General Alarico'], presence=['Alarico']),
    dict(slug='ROLDAN', sec='3.1', cat='Campeón', aliases=['Roldán', 'Campeón Roldán'], presence=['Roldán']),
    dict(slug='MATILDE', sec='4.1', cat='Líder de Gimnasio', aliases=['Matilde'], presence=['Matilde']),
    dict(slug='ISMAEL', sec='4.2', cat='Líder de Gimnasio', aliases=['Ismael'], presence=['Ismael']),
    dict(slug='ARGOS', sec='4.3', cat='Líder de Gimnasio', aliases=['Argos'], presence=['Argos']),
    dict(slug='GENZO', sec='4.4', cat='Líder de Gimnasio', aliases=['Genzo'], presence=['Genzo']),
    dict(slug='FAUSTO', sec='4.5', cat='Líder de Gimnasio', aliases=['Fausto'], presence=['Fausto']),
    dict(slug='HILDEGARDA', sec='4.6', cat='Líder de Gimnasio', aliases=['Hildegarda'], presence=['Hildegarda']),
    dict(slug='ISOLDA', sec='4.7', cat='Líder de Gimnasio', aliases=['Isolda'], presence=['Isolda']),
    dict(slug='BALTASAR', sec='4.8', cat='Líder de Gimnasio', aliases=['Baltasar'], presence=['Baltasar']),
    dict(slug='NICODEMO', sec='5.2', cat='Alto Mando', aliases=['Nicodemo'], presence=['Nicodemo']),
    dict(slug='LEUCOTEA', sec='5.3', cat='Alto Mando', aliases=['Leucótea'], presence=['Leucótea']),
    dict(slug='ORIANA', sec='5.4', cat='Alto Mando', aliases=['Oriana'], presence=['Oriana']),
    dict(slug='ANTEO', sec='5.5', cat='Alto Mando', aliases=['Anteo'], presence=['Anteo']),
    dict(slug='TELMO', sec='6.1', cat='PNJ', aliases=['Telmo', 'Viejo Pescador'], presence=['Telmo']),
    dict(slug='AMPARO', sec='6.2', cat='PNJ', aliases=['Amparo'], presence=['Amparo']),
    dict(slug='PIA', sec='6.3', cat='Aliado', aliases=['Pía'], presence=['Pía']),
    dict(slug='ELADIO_HORTENSIA', sec='6.4', cat='PNJ',
         aliases=['Eladio y Hortensia', 'Eladio', 'Hortensia'], presence=['Eladio', 'Hortensia']),
    dict(slug='VENDEDOR_AMBULANTE', sec='6.5:Vendedor ambulante', cat='PNJ',
         aliases=['Vendedor ambulante'], presence=['vendedor ambulante']),
    dict(slug='PADRE', sec='6.5:Padre', cat='PNJ', aliases=['Padre'], presence=[]),
    dict(slug='RECLUTAS', sec='6.5:Recluta', cat='Equipo Morfeo',
         aliases=['Reclutas', 'Recluta femenina', 'Recluta masculino', 'Reclutas del Equipo Morfeo'],
         presence=['recluta']),
]

# Dominantes: jefes de guion (Vol. 6 fichas, Vol. 8 libro de cuentas). No tienen perfil en el Vol. 7.
DOMINANTES = [
    dict(n=1, types='Siniestro/Volador', lvl=13, loc='BOSQUE_DIOPTASA', frag='F1', orb='Pesadilla'),
    dict(n=2, types='Eléctrico', lvl=31, loc='CENTRAL_FULGURITA', frag='F2', orb='Lunar'),
    dict(n=3, types='Veneno', lvl=45, loc='RUINAS_ATACAMITA', frag='F3', orb='Pesadilla'),
    dict(n=4, types='Hada', lvl=52, loc='CASCADAS_TRAVERTINAS', frag='F4', orb='Lunar'),
    dict(n=5, types='Fantasma', lvl=58, loc='VILLA_ADULARIA', frag='F5', orb='Pesadilla'),
    dict(n=6, types='Dragón', lvl=66, loc='TEMPLO_MOLDAVITA', frag='F6', orb='Lunar'),
]

CHAR_FIELD_ORDER = [
    'Name', 'NameNote', 'DraftNames', 'Title', 'Role', 'Category', 'Allegiance', 'Aliases', 'Age', 'NameMeaning', 'OneLiner',
    'Appearance', 'Personality', 'Light', 'Shadow', 'ThemeStance', 'ThemePosition', 'Backstory', 'Motivation',
    'Philosophy', 'Concept', 'GymScenario', 'GymNumber', 'Arc', 'FirstLocation', 'Locations', 'TypeSpecialty',
    'CombatIdentity', 'TeamNote', 'Team', 'VoiceStyle', 'Quotes', 'QuotesAbout', 'HiddenCluesIntro', 'HiddenClues', 'Chronology',
    'Appearances', 'Battles', 'Source',
]
REPEATABLE = {'Team', 'Quotes', 'QuotesAbout', 'Chronology', 'HiddenClues'}

HEADER_CHAR = [
    '# Pokémon REM — Personajes (Vol. 7 + Dominantes de los Vol. 6/8). Generado por tools/rebalance/phase1/build_narrative.py; no editar a mano.',
    '# Formato INI (UTF-8 BOM, CRLF): [CHAR_<SLUG>] con «Clave = Valor»; listas separadas por «;». FirstLocation/Locations = LOC_KEY (Vol. 7 cronología ∪ Vol. 6 «Personajes presentes», en orden de progresión).',
    '# Aliases = nombres de escena del Vol. 8 y variantes (para resolver CharactersInScene). Claves repetibles: Quotes, QuotesAbout, HiddenClues, Chronology, Team.',
    '# Team (una línea por casilla) = «Casilla | Especie | Nivel | Notas»: los marcadores [PENDIENTE DE ASIGNACIÓN] y [EN REVISIÓN*] se conservan literales; no se inventan especies.',
    '# Chronology = «n | Ubicación (texto del Vol. 7) | LOC_KEY | Evento | Rol en la escena | ¿Combate?». Appearances/Battles = Apéndice del Vol. 7. Source indica el origen.',
    '# Allegiance: lealtad real cuando difiere de la categoría pública (puede contener spoilers).',
]


def v7_sections():
    """{'1.1': lines, ... , '6.5': lines} por prefijo numérico de `## `."""
    lines = read_lines(V7)
    secs = {}
    cur = None
    for l in lines:
        m = re.match(r'^## (\d+\.\d+)\s+(.*)$', l)
        if m:
            cur = m.group(1)
            secs[cur] = [l]
            continue
        if l.startswith('# '):
            cur = None
            continue
        if cur:
            secs[cur].append(l)
    return secs, lines


def split_subs(lines):
    """Parte las líneas de una sección en (preámbulo, {titulo ####: líneas})."""
    pre, subs, cur = [], {}, None
    for l in lines:
        m = re.match(r'^#### (.*)$', l)
        if m:
            cur = m.group(1).strip()
            subs[cur] = []
            continue
        (subs[cur] if cur else pre).append(l)
    return pre, subs


def sub_by_prefix(subs, prefix):
    for k, v in subs.items():
        if k.startswith(prefix):
            return v
    return []


def md_paras(lines):
    """Párrafos de texto plano (sin tablas, viñetas, comentarios HTML ni reglas)."""
    out = []
    for l in lines:
        s = l.strip()
        if not s or s.startswith('|') or s.startswith('<!--') or s.startswith('- ') or s == '---':
            continue
        out.append(s)
    return out


def md_bullets(lines):
    return [l.strip()[2:].strip() for l in lines if l.strip().startswith('- ')]


def pick_quotes(raw):
    """Citas en cursiva `*«...»*` (las «...» sueltas son glosas, no citas)."""
    return [clean(q) for q in re.findall(r'\*(«[^»]+»)\*', raw)]


def split_arrow(s):
    return s


def parse_eje_tematico(lines):
    """Tabla «Personaje | Posición inicial | Herida o motor | Qué lo mueve» del Vol. 7."""
    i0 = next(i for i, l in enumerate(lines) if l.startswith('## El eje temático'))
    i1 = next(i for i, l in enumerate(lines) if l.startswith('# Capítulo 1'))
    out = {}
    for r in table_rows(lines[i0:i1]):
        if len(r) == 4 and r[0] not in ('Personaje',):
            out[norm(clean(r[0]))] = dict(pos=clean(r[1]), wound=clean(r[2]), moves=clean(r[3]))
    return out


def parse_v7_matrix(lines):
    i0 = next(i for i, l in enumerate(lines) if l.startswith('# Apéndice'))
    out = {}
    for r in table_rows(lines[i0:]):
        if len(r) == 5 and r[1].isdigit():
            out[norm(clean(r[0]))] = (int(r[1]), int(r[2]))
    return out


def parse_v6_presence():
    """{LOC_KEY: texto de «Personajes presentes»} de las fichas del Vol. 6."""
    lines = read_lines(V6)
    out = {}
    cur = None
    for i, l in enumerate(lines):
        if l.startswith('### ') and 200 < i < 4250:
            cur = loc_from_text(clean(l[4:]))
            continue
        m = re.match(r'^\*\*Personajes presentes\.\*\*\s*(.*)$', l)
        if m and cur:
            out[cur] = clean(m.group(1))
    return out


def parse_dramatis():
    lines = read_lines(V8)
    i0 = next(i for i, l in enumerate(lines) if l.startswith('## Dramatis personae'))
    i1 = next(i for i, l in enumerate(lines) if l.startswith('## El libro de cuentas'))
    out = {}
    for r in table_rows(lines[i0:i1]):
        if len(r) == 2 and r[0] != 'Personaje':
            out[clean(r[0])] = clean(r[1])
    return out


def build_char_from_section(d, secs, eje, matrix, dramatis):
    sec_id = d['sec']
    sub_key = None
    if ':' in sec_id:
        sec_id, sub_key = sec_id.split(':', 1)
    lines = secs[sec_id]
    head = lines[0]
    c = {'_slug': d['slug']}
    pre, subs = split_subs(lines[1:])
    kv = kv_table(pre)
    raw_name = kv.get('Nombre definitivo', '')
    drafts = re.findall(r'\*\(borrador: ([^)]+)\)\*', raw_name) or re.findall(r'\(borrador: ([^)]+)\)', head)
    c['DraftNames'] = ';'.join(drafts)
    nm = clean(re.sub(r'\*\(borrador:[^)]*\)\*', '', raw_name))
    c['Category'] = d['cat']
    if 'Allegiance' in d or d.get('allegiance'):
        c['Allegiance'] = d['allegiance']

    # ---- bloque 6.5 (listas con viñetas) ----
    if sub_key:
        bl = [b for b in md_bullets(lines) if clean(b).lower().startswith(sub_key.lower().split()[0])]
        raw = bl[0] if bl else ''
        text = clean(raw)
        title, _, rest = text.partition(':')
        c['Name'] = {'Recluta': 'Reclutas del Equipo Morfeo'}.get(sub_key, title.strip().capitalize())
        if sub_key == 'Recluta':
            c['Name'] = 'Reclutas del Equipo Morfeo'
            c['Role'] = 'Recluta femenina y recluta masculino: rostros intercambiables del Equipo Morfeo'
            c['Personality'] = 'Hablan siempre en la jerga de Eliseo.'
        elif sub_key == 'Vendedor ambulante':
            c['Name'] = 'Vendedor ambulante'
            c['Role'] = 'Tienda itinerante en el cruce de caminos del Pueblo Pedernal'
            c['Personality'] = cap1(rest)
        else:
            c['Name'] = 'Padre'
            c['Role'] = 'Padre del protagonista (NPC de ambientación)'
            c['Personality'] = cap1(rest)
        c['_text_locs'] = locs_in_text(text)
        c['_chron'] = []
        c['Source'] = 'Vol. 7 §6.5'
        return c

    c['Name'] = nm
    if sec_id == '1.4':
        c['Name'] = 'Protagonista'
        c['NameNote'] = nm
    if sec_id.startswith('6.') and not kv:
        # NPC sin tabla kv (6.2-6.4): párrafo + cronología
        txt = md_paras(lines[1:])
        title = clean(re.sub(r'^## \d+\.\d+\s+', '', head))
        who, _, role = title.partition(',')
        c['Name'] = who.strip()
        c['Role'] = cap1(role) if role else ''
        c['Personality'] = clean(txt[0]) if txt else ''
        c['Quotes'] = pick_quotes(txt[0]) if txt else []
    # ---- campos kv ----
    if 'Título' in kv:
        c['Title'] = clean(kv['Título'])
    if 'Título · edad' in kv:
        parts = clean(kv['Título · edad']).split(' · ')
        c['Title'] = ' · '.join(parts[:-1])
        c['Age'] = parts[-1]
    if 'Edad aproximada' in kv:
        c['Age'] = clean(kv['Edad aproximada'])
    if 'Rol en la historia' in kv:
        c['Role'] = clean(kv['Rol en la historia'])
    if 'Profesión y rol' in kv:
        c['Role'] = clean(kv['Profesión y rol'])
    if 'Rol' in kv:
        c['Role'] = clean(kv['Rol'])
    if 'Concepto' in kv:
        c['Concept'] = clean(kv['Concepto'])
    if 'Escenario' in kv:
        c['GymScenario'] = clean(kv['Escenario'])
    if 'Resonancia del nombre' in kv:
        c['NameMeaning'] = clean(kv['Resonancia del nombre'])

    # ---- subsecciones ----
    ap = sub_by_prefix(subs, 'Diseño')
    if ap:
        c['Appearance'] = ' '.join(clean(p) for p in md_paras(ap))
    psy = sub_by_prefix(subs, 'Psicolog')
    if psy:
        c['Personality'] = ' '.join(clean(p) for p in md_paras(psy))
        for b in md_bullets(psy):
            cb = clean(b)
            for lab, key in (('Luz:', 'Light'), ('Sombra:', 'Shadow'), ('Frente al tema:', 'ThemeStance')):
                if cb.startswith(lab):
                    c[key] = cb[len(lab):].strip()
    voz = sub_by_prefix(subs, 'Voz')
    if voz:
        ps = md_paras(voz)
        if ps:
            c['VoiceStyle'] = ' '.join(clean(p) for p in ps)
        c['Quotes'] = [clean(b) for b in md_bullets(voz)]
    pistas = sub_by_prefix(subs, 'Por qué su traición')
    if pistas:
        c['_pistas'] = [(clean(r[0]), clean(r[1])) for r in table_rows(pistas) if len(r) == 2 and r[0] != 'Dónde']
        c['HiddenCluesIntro'] = ' '.join(clean(p) for p in md_paras(pistas))
    prot = sub_by_prefix(subs, 'Diseño, psicología y voz')
    if prot:
        c['Appearance'] = ''
        c['Personality'] = ' '.join(clean(p) for p in md_paras(prot))
        qa = [clean(b) for b in md_bullets(prot)]
        c['QuotesAbout'] = [x.strip() for q in qa for x in re.sub(r'^[^:]*:\s*', '', q, count=1).split(' · ') if x.strip()]
        c.pop('Appearance')
    arco = sub_by_prefix(subs, 'Arco')
    if arco:
        if md_bullets(arco):
            c['Arc'] = ' '.join(clean(b) for b in md_bullets(arco))
        else:
            c['Arc'] = ' '.join(clean(p) for p in md_paras(arco))
    # hitos del protagonista (tabla «Hito | Ubicación | Medallas»)
    if sec_id == '1.4':
        hitos = [r for r in table_rows(arco) if len(r) == 3 and r[0] != 'Hito']
        c['_hitos'] = [(clean(r[0]), clean(r[1]), clean(r[2])) for r in hitos]
        c['Arc'] = ' '.join(clean(p) for p in md_paras(arco)) + ' Hitos: ' + ' → '.join('%s (%s; %s medallas)' % (h[0], h[1], h[2]) for h in c['_hitos'])
    # cronología
    cr = sub_by_prefix(subs, 'Cronolog') or pre
    chron = []
    for r in table_rows(cr):
        if len(r) == 5 and r[0].isdigit():
            chron.append(dict(n=int(r[0]), where=clean(r[1]), event=clean(r[2]), role=clean(r[3]), combat=clean(r[4])))
    c['_chron'] = chron
    # identidad de combate y equipo
    idc = sub_by_prefix(subs, 'Identidad de combate')
    if idc:
        ps = md_paras(idc)
        plain = [p for p in ps if not p.startswith('*')]
        caption = [p for p in ps if p.startswith('*')]
        if plain:
            c['CombatIdentity'] = ' '.join(clean(p) for p in plain)
        if caption:
            c['TeamNote'] = ' '.join(clean(p) for p in caption)
        team = []
        for r in table_rows(idc):
            if len(r) == 4 and (r[0].startswith('Slot') or r[0].startswith('Ace')):
                team.append(' | '.join(clean(x) for x in r))
        c['Team'] = team
    # Alto Mando / NPC con párrafos de «negrita-etiqueta»
    for p in md_paras(pre):
        m = re.match(r'^\*\*(.+?)\.\*\*\s*(.*)$', p)
        if not m:
            continue
        lab, body = m.group(1), m.group(2)
        if lab.startswith('Diseño'):
            c['Appearance'] = clean(body)
        elif lab.startswith('Psicolog'):
            c['Quotes'] = pick_quotes(body)
            c['Personality'] = clean(re.sub(r'\*«[^»]*»\*(\s*·\s*)?', '', body)).rstrip(' ·')
        elif lab.startswith('Arco'):
            c['Arc'] = clean(body)
    # texto libre de NPC con kv (Telmo): párrafo tras la tabla
    if sec_id == '6.1':
        ps = [p for p in md_paras(pre)]
        if ps:
            c['Personality'] = clean(ps[0])
            c['Quotes'] = pick_quotes(ps[0])
    if d['cat'] == 'Alto Mando':
        for r in table_rows(secs['5.1']):
            if len(r) == 7 and norm(clean(r[0])) == norm(c['Name']):
                gruta, tipo, filo, anuncia, liga = [clean(x) for x in (r[2], r[3], r[4], r[5], r[6])]
                c['Role'] = 'Alto Mando (%s): guardián de la %s; se anuncia en %s; combate en la Liga: %s' % (tipo, gruta, anuncia, liga)
                c['Philosophy'] = filo
    # tipo de especialidad
    m = re.search(r'tipo (\w+)', head)
    if d['cat'] == 'Líder de Gimnasio':
        mt = re.search(r', tipo ([^(]+?)\s*\(', head)
        c['TypeSpecialty'] = mt.group(1).strip() if mt else ''
        mg = re.search(r'Gimnasio (\d)', head)
        c['GymNumber'] = mg.group(1) if mg else ''
    elif d['cat'] == 'Alto Mando':
        mt = re.search(r'—\s*([^,]+),\s*Gruta', head)
        c['TypeSpecialty'] = mt.group(1).strip() if mt else ''
    elif c.get('Team'):
        ace = c['Team'][-1].split(' | ')[-1]
        c['TypeSpecialty'] = ace.replace('Tipo:', '').strip()
    # temática / dramatis
    e = eje.get(norm(d['aliases'][0].replace('Tú (Protagonista)', 'Protagonista')))
    if e:
        c['ThemePosition'] = e['pos']
        c['Backstory'] = '' if e['wound'] in ('—', '-') else e['wound']
        c['Motivation'] = e['moves']
    ap_ = matrix.get(norm(c['Name'])) or matrix.get(norm(c['Name'].split()[0])) if c.get('Name') else None
    if ap_:
        c['Appearances'], c['Battles'] = ap_
    for k, v in dramatis.items():
        if norm(k) == norm(c['Name']) or norm(k) == norm(d['aliases'][0]) or (d['slug'] == 'PROTAGONISTA' and k.startswith('Tú')) \
                or (d['slug'] == 'AMBROSIO' and k.startswith('Ambrosio')) or (d['slug'] == 'ROLDAN' and k.startswith('Roldán')):
            c['OneLiner'] = v
    c['Source'] = 'Vol. 7 §%s' % sec_id
    return c


def _dedupe(seq):
    out, seen = [], set()
    for x in seq:
        k = norm(x)
        if x and k not in seen:
            seen.add(k)
            out.append(x)
    return out


def _presence_locs(names, pres6):
    """LOC_KEYs de las fichas del Vol. 6 cuyo «Personajes presentes» menciona alguno de `names`."""
    out = []
    for loc, text in pres6.items():
        t = norm(text)
        for n in names:
            if re.search(r'(?<!\w)' + re.escape(norm(n)), t):
                out.append(loc)
                break
    return out


def build_characters(steps):
    secs, lines = v7_sections()
    eje = parse_eje_tematico(lines)
    matrix = parse_v7_matrix(lines)
    dramatis = parse_dramatis()
    pres6 = parse_v6_presence()
    order = {}
    for s in steps:
        order.setdefault(s['key'], s['n'])
    chars = []
    diffs = []   # (slug, solo Vol.7, solo Vol.6) para el informe
    for d in CHAR_DEFS:
        c = build_char_from_section(d, secs, eje, matrix, dramatis)
        # cronología -> LOC_KEY
        chron_lines, v7locs = [], []
        for e in c.get('_chron', []):
            k = loc_from_text(e['where'])
            if not k and e['where'] == 'Epílogo' and 'fuegos artificiales' in e['event']:
                k = 'MESETA_CELESTITA'
            if k:
                v7locs.append(k)
            chron_lines.append(' | '.join([str(e['n']), e['where'], k or '', e['event'], e['role'], e['combat']]))
        v7locs += c.get('_text_locs', [])
        if d['slug'] == 'PROTAGONISTA':
            for h in c.get('_hitos', []):
                for k in locs_in_text(h[1]):
                    v7locs.append(k)
            v7locs = v7locs[:]
        v6locs = _presence_locs(d['presence'], pres6) if d['presence'] else []
        if d['slug'] == 'PADRE':
            v6locs = ['PUEBLO_IOLITA']
        locs = sorted(set(v7locs) | set(v6locs), key=lambda k: (order.get(k, 999), k))
        diffs.append((d['slug'], sorted(set(v7locs) - set(v6locs), key=lambda k: order.get(k, 999)),
                      sorted(set(v6locs) - set(v7locs), key=lambda k: order.get(k, 999))))
        c['Chronology'] = chron_lines
        c['Locations'] = ';'.join(locs)
        c['FirstLocation'] = locs[0] if locs else ''
        c['Aliases'] = ';'.join(_dedupe(list(d['aliases']) + ([c['Name']] if c.get('Name') else [])))
        if c.get('_pistas'):
            c['HiddenClues'] = ['%s: %s' % (a, b) for a, b in c['_pistas']]
        c['_order'] = len(chars)
        chars.append(c)
    # Dominantes
    ledger = parse_ledger()
    for dm in DOMINANTES:
        n = dm['n']
        nm = 'Dominante %d (%s)' % (n, dm['types'])
        led = ledger[n - 1]
        alias = ['Dominante %d' % n, 'Dominante %s' % dm['types']]
        c = dict(
            _slug='DOMINANTE_%d' % n, Name=nm, Title='Dominante n.º %d' % n,
            Role='Jefe de guion: guardián del fragmento %s (Orbe de la %s); se derrota para recuperarlo y no se captura' % (dm['frag'], dm['orb']),
            Category='Dominante', Aliases=';'.join(_dedupe(alias + [nm])),
            Arc=led['dest'], FirstLocation=dm['loc'], Locations=dm['loc'], TypeSpecialty=dm['types'],
            CombatIdentity='Jefe de guion de tipo %s (Nv %d). Su especie y su equipo quedan pendientes de asignación; no resta especies al reparto salvaje (Vol. 10, §4.7).' % (dm['types'], dm['lvl']),
            Team=['%s | [Especie y Equipo Pendientes de Asignación] | Nv %d | Jefe de guion; no se captura' % (nm, dm['lvl'])],
            Chronology=['1 | %s | %s | Combate contra el %s (Nv %d) para recuperar el fragmento %s | Jefe | Sí — Nv %d' % (
                LOC_NAMES[dm['loc']], dm['loc'], nm, dm['lvl'], dm['frag'], dm['lvl'])],
            Appearances=1, Battles=1, Source='Vol. 6 (fichas) y Vol. 8 (libro de cuentas); sin perfil en el Vol. 7')
        c['_order'] = len(chars)
        chars.append(c)
    return chars, diffs


def emit_characters(chars):
    out = list(HEADER_CHAR)
    required = ['Name', 'Role', 'Category', 'Aliases', 'Age', 'Appearance', 'Personality', 'Backstory', 'Motivation',
                'Arc', 'FirstLocation', 'Locations', 'TypeSpecialty', 'Team']
    for c in chars:
        out += ['', '[CHAR_%s]' % c['_slug']]
        for k in CHAR_FIELD_ORDER:
            v = c.get(k)
            if isinstance(v, list):
                for x in v:
                    out.append('%s = %s' % (k, x))
            else:
                if v in (None, '') and k not in required:
                    continue
                out.append('%s = %s' % (k, '' if v is None else v))
    return out


# --------------------------------------------------------------------------------------------
# HISTORIA (Vol. 8)
# --------------------------------------------------------------------------------------------
CHAPTER_LOC_OVERRIDE = {   # capítulos sin ubicación única en la cabecera: (LOC principal, [alternativas], motivo)
    64: ('ISLA_OBSIDIANA', ['GRUTA_HIALINA', 'GRUTA_AZURITA', 'GRUTA_LABRADORITA', 'GRUTA_PIRITA'],
         'Interludio sin lugar propio: arranca en la orilla de la Isla Obsidiana y mira a las cuatro grutas'),
    68: ('MESETA_CELESTITA', ['PUEBLO_IOLITA'],
         'Epílogo: terraza de la Liga (Meseta Celestita), un bosque tranquilo y, al final, la loma de Pueblo Iolita'),
}

HEADER_STORY = [
    '# Pokémon REM — Crónicas de Oniria (Vol. 8): Preludio, 68 capítulos y libro de cuentas de los 6 fragmentos. Generado por tools/rebalance/phase1/build_narrative.py; no editar a mano.',
    '# Formato INI (UTF-8 BOM, CRLF): [PRELUDE], [CHAPTER_01..68], [FRAGMENT_LEDGER]. NarrativeText y Milestones son claves repetidas: UN párrafo (o viñeta) por línea, texto íntegro del volumen.',
    '# Se retiran los marcadores Markdown de énfasis (**negrita**, *cursiva*); no se resume ni se recorta nada. LocationKey = LOC_KEY; CharactersInScene = nombres tal como aparecen en la cabecera del capítulo (resolubles vía Aliases de rem_characters.txt).',
    '# Cada capítulo: Title, Act, LocationKey, MedalsEarned, FragmentsInPlay, WildLevels, CharactersInScene, NarrativeText (repetida), Milestones (repetida: «Hitos de gameplay»), WhyItMatters. ActTitle/ActIntro solo en el primer capítulo de cada acto.',
    '# Fragmentos del libro de cuentas: FragmentN = Nombre,Dominante,LOC_KEY,CHAPTER_NN,Nota (Nota = «Destino» del Vol. 8). OrbN = orbe a la que pertenece. Result = resumen del Vol. 6, Apéndice B.',
]


def parse_story():
    lines = read_lines(V8)
    # actos
    act_of_line = {}
    act_meta = {}
    cur_act = None
    for i, l in enumerate(lines):
        m = re.match(r'^# (Acto (I|II|III|IV|V) — .*)$', l)
        if m:
            cur_act = m.group(2)
            act_meta[cur_act] = dict(title=clean(m.group(1)), intro=[])
            j = i + 1
            while j < len(lines) and not lines[j].startswith('## '):
                if lines[j].strip():
                    act_meta[cur_act]['intro'].append(clean(lines[j]))
                j += 1
        act_of_line[i] = cur_act
    # preludio
    ip = next(i for i, l in enumerate(lines) if l.startswith('## Preludio'))
    jp = next(i for i in range(ip + 1, len(lines)) if lines[i].startswith('# '))
    prelude = dict(title=clean(lines[ip][3:]), paras=[clean(l) for l in lines[ip + 1:jp] if l.strip()])
    # capítulos
    heads = [i for i, l in enumerate(lines) if re.match(r'^## \d+\. ', l)]
    chapters = []
    first_of_act = set()
    for idx, h in enumerate(heads):
        end = heads[idx + 1] if idx + 1 < len(heads) else len(lines)
        # el último capítulo de un acto termina en el siguiente «# Acto»
        for j in range(h + 1, end):
            if lines[j].startswith('# '):
                end = j
                break
        m = re.match(r'^## (\d+)\. (.*)$', lines[h])
        n, title = int(m.group(1)), clean(m.group(2))
        body = lines[h + 1:end]
        ih = next((i for i, l in enumerate(body) if l.startswith('#### ')), len(body))
        kv = kv_table(body[:ih])
        # párrafos: todo lo que no es tabla, comentario ni línea vacía, antes de «Hitos»
        paras = [clean(l) for l in body[:ih] if l.strip() and not l.strip().startswith('|') and not l.strip().startswith('<!--')]
        bullets = [clean(l.strip()[2:]) for l in body[ih + 1:] if l.strip().startswith('- ')]
        why = [b for b in bullets if b.startswith('Por qué importa:')]
        miles = [b for b in bullets if not b.startswith('Por qué importa:')]
        act = act_of_line[h]
        ch = dict(n=n, title=title, act=act, kv=kv, paras=paras, miles=miles,
                  why=why[0][len('Por qué importa:'):].strip() if why else '')
        if act not in first_of_act:
            first_of_act.add(act)
            ch['act_title'] = act_meta[act]['title']
            ch['act_intro'] = ' '.join(act_meta[act]['intro'])
        chapters.append(ch)
    return prelude, chapters


def parse_ledger():
    """Libro de cuentas del Vol. 8 -> lista de 6 dicts (n, place, loc, dominant, orb, dest, intro)."""
    lines = read_lines(V8)
    i0 = next(i for i, l in enumerate(lines) if l.startswith('## El libro de cuentas'))
    i1 = next(i for i, l in enumerate(lines) if l.startswith('## Preludio'))
    intro = ' '.join(clean(l) for l in lines[i0 + 1:i1] if l.strip() and not l.strip().startswith('|') and not l.strip().startswith('<!--'))
    out = []
    for r in table_rows(lines[i0:i1]):
        if len(r) == 5 and re.match(r'^F\d$', r[0]):
            out.append(dict(n=int(r[0][1]), place=clean(r[1]), loc=loc_from_text(clean(r[1])), dominant=clean(r[2]),
                            orb=clean(r[3]), dest=clean(r[4]), intro=intro))
    return out


def v6_ledger_result():
    lines = read_lines(V6)
    i0 = next(i for i, l in enumerate(lines) if l.startswith('# Apéndice B'))
    for l in lines[i0:]:
        if l.startswith('**Resultado:**'):
            return clean(l).replace('Resultado:', '', 1).strip()
    return ''


def emit_story(prelude, chapters):
    items = parse_item_symbols()
    out = list(HEADER_STORY)
    out += ['', '[PRELUDE]', 'Title = %s' % prelude['title'], 'Act =', 'LocationKey =', 'CharactersInScene =']
    out += ['NarrativeText = %s' % p for p in prelude['paras']]
    loc_chapter = {}
    for ch in chapters:
        ch['loc'], ch['alt'], ch['note'] = chapter_location(ch)
        loc_chapter.setdefault(ch['loc'], ch['n'])
    for ch in chapters:
        kv = ch['kv']
        scene = [x.strip() for x in clean(kv.get('Personajes en escena', '')).split(',') if x.strip()]
        med = re.match(r'^(\d+) de 8', clean(kv.get('Medallas obtenidas', '')))
        out += ['', '[CHAPTER_%02d]' % ch['n'], 'Title = %s' % ch['title'], 'Act = %s' % ch['act']]
        if 'act_title' in ch:
            out += ['ActTitle = %s' % ch['act_title'], 'ActIntro = %s' % ch['act_intro']]
        out.append('LocationKey = %s' % ch['loc'])
        if ch['alt']:
            out.append('AltLocations = %s' % ';'.join(ch['alt']))
        if ch['note']:
            out.append('Summary = %s. Ubicación en el Vol. 8: %s.' % (ch['note'], clean(kv.get('Ubicación', ''))))
        out += ['MedalsEarned = %s' % (med.group(1) if med else ''),
                'FragmentsInPlay = %s' % clean(kv.get('Fragmentos de orbe en juego', '')),
                'WildLevels = %s' % clean(kv.get('Niveles salvajes', '')),
                'CharactersInScene = %s' % ';'.join(scene)]
        out += ['NarrativeText = %s' % p for p in ch['paras']]
        out += ['Milestones = %s' % m for m in ch['miles']]
        out.append('WhyItMatters = %s' % ch['why'])
    led = parse_ledger()
    result = v6_ledger_result()
    out += ['', '[FRAGMENT_LEDGER]', 'Title = El libro de cuentas de los fragmentos', 'Intro = %s' % led[0]['intro'], 'Result = %s' % result]
    for f in led:
        sym = ('NIGHTMAREFRAG%d' if f['orb'] == 'Pesadilla' else 'LUNARFRAG%d') % ((f['n'] + 1) // 2)
        name = items[sym][1]
        out.append('Fragment%d = %s,%s,%s,CHAPTER_%02d,%s' % (f['n'], name, f['dominant'], f['loc'], loc_chapter[f['loc']], f['dest']))
    for f in led:
        out.append('Orb%d = %s' % (f['n'], f['orb']))
    return out


SUBPLACES = ['Geoda Hundida', 'Refugio de Turba', 'Bastión del Pórfido', 'Umbral de la Liga']


def chapter_location(ch):
    """(LOC_KEY principal, [LOC_KEY alternativas], nota para `Summary`)."""
    n = ch['n']
    ub = clean(ch['kv'].get('Ubicación', ''))
    if n in CHAPTER_LOC_OVERRIDE:
        return CHAPTER_LOC_OVERRIDE[n]
    k = loc_from_text(ub)
    note = ''
    for sp in SUBPLACES:
        if sp.lower() in ub.lower() and k:
            note = 'Sub-lugar sin clave propia dentro de %s' % LOC_NAMES[k]
    return k, [], note


# --------------------------------------------------------------------------------------------
# E/S y orquestación
# --------------------------------------------------------------------------------------------
def to_bytes(lines):
    return ('﻿' + '\r\n'.join(lines) + '\r\n').encode('utf-8')


def write_lines(path, lines):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        f.write('\r\n'.join(lines) + '\r\n')


def generate():
    steps, by9, tmloc = build_progression()
    chars, diffs = build_characters(steps)
    prelude, chapters = parse_story()
    return dict(
        steps=steps, chars=chars, diffs=diffs, prelude=prelude, chapters=chapters, by9=by9, tmloc=tmloc,
        prog=emit_progression(steps), char=emit_characters(chars), story=emit_story(prelude, chapters))


# --------------------------------------------------------------------------------------------
# VALIDACIÓN
# --------------------------------------------------------------------------------------------
BOSS_TYPES = {'', 'Normal', 'Agua', 'Acero', 'Lucha', 'Roca', 'Planta', 'Hielo', 'Fuego', 'Siniestro/Volador', 'Eléctrico',
              'Veneno', 'Hada', 'Fantasma', 'Dragón', 'Psíquico/Hada', 'Siniestro/Fantasma'}
CHAR_CATEGORIES = {'Protagonista', 'Aliado', 'Rival', 'Líder de Gimnasio', 'Alto Mando', 'Campeón', 'Equipo Morfeo',
                   'Dominante', 'PNJ'}
ACT_BY_CHAPTER = [(1, 15, 'I'), (16, 30, 'II'), (31, 46, 'III'), (47, 57, 'IV'), (58, 68, 'V')]


def sig(text):
    """Firma independiente del formato: solo letras/dígitos en minúsculas (para comparar con el Markdown)."""
    return re.sub(r'[\W_]+', '', text, flags=re.U).casefold()


class Checker:
    def __init__(self):
        self.errors = []
        self.infos = []

    def err(self, msg):
        self.errors.append(msg)

    def info(self, msg):
        self.infos.append(msg)

    def ok(self, cond, msg):
        if not cond:
            self.err(msg)
        return cond


def _sections(path, ck, label):
    secs, warns = remini_ref.parse(path)
    ck.ok(not warns, '%s: remini_ref.parse devolvió %d avisos: %s' % (label, len(warns), warns[:3]))
    return secs


def check_files(g, ck):
    """BOM+CRLF, parseo limpio y reproducibilidad (el disco == lo que genera este script ahora)."""
    for path, key in ((OUT_PROG, 'prog'), (OUT_CHAR, 'char'), (OUT_STORY, 'story')):
        name = os.path.basename(path)
        if not ck.ok(os.path.exists(path), '%s no existe' % name):
            continue
        raw = open(path, 'rb').read()
        ck.ok(raw.startswith(b'\xef\xbb\xbf'), '%s: sin BOM UTF-8' % name)
        ck.ok(b'\n' not in raw.replace(b'\r\n', b''), '%s: finales de línea no CRLF' % name)
        ck.ok(raw.endswith(b'\r\n'), '%s: no termina en CRLF' % name)
        ck.ok(raw == to_bytes(g[key]), '%s: el disco difiere de lo que genera el script (regenerar)' % name)
        hdr = [l for l in raw.decode('utf-8-sig').split('\r\n')[:8] if l.startswith('#')]
        ck.ok(3 <= len(hdr) <= 6, '%s: la cabecera debe tener 3-6 líneas # (tiene %d)' % (name, len(hdr)))


def check_progression(g, ck):
    secs = _sections(OUT_PROG, ck, 'rem_progression.txt')
    ck.ok(len(secs) == 68, 'rem_progression: %d secciones (se esperaban 68)' % len(secs))
    items = parse_item_symbols()
    by9, tm_loc = g['by9'], g['tmloc']
    rows14 = parse_v6_table_14()
    prev_d = prev_n = 0
    prev_act = 'I'
    seen_tm = []
    chap_keys = set('CHAPTER_%02d' % i for i in range(1, 69))
    for i, s in enumerate(secs, 1):
        tag = s['key']
        ck.ok(tag == 'STEP_%02d' % i, '%s: clave de sección inesperada (esperada STEP_%02d)' % (tag, i))
        ck.ok(s.get('StepNumber') == str(i), '%s: StepNumber=%s' % (tag, s.get('StepNumber')))
        act = s.get('Act')
        ck.ok(act in ('I', 'II', 'III', 'IV', 'V'), '%s: Act inválido «%s»' % (tag, act))
        ck.ok(['I', 'II', 'III', 'IV', 'V'].index(act) >= ['I', 'II', 'III', 'IV', 'V'].index(prev_act),
              '%s: el acto retrocede (%s tras %s)' % (tag, act, prev_act))
        prev_act = act
        lk = s.get('LocationKey')
        ck.ok(lk in LOC_KEYSET, '%s: LocationKey inválida «%s»' % (tag, lk))
        # la fila 1.4 se asocia a esa ubicación
        ck.ok(loc_from_text(rows14[i - 1]['name']) == lk, '%s: LocationKey no corresponde a la fila 1.4 «%s»' % (tag, rows14[i - 1]['name']))
        try:
            cd, cn = int(s.get('LevelCapDay')), int(s.get('LevelCapNight'))
        except (TypeError, ValueError):
            ck.err('%s: topes de nivel no enteros' % tag)
            continue
        ck.ok(cd >= prev_d and cn >= prev_n, '%s: topes no monótonos (día %d<%d o noche %d<%d)' % (tag, cd, prev_d, cn, prev_n))
        ck.ok(cn >= cd, '%s: LevelCapNight < LevelCapDay' % tag)
        prev_d, prev_n = cd, cn
        # frase única, sin spoilers
        summ = s.get('ObjectiveSummary', '')
        ck.ok(bool(summ) and summ.endswith('.') and summ.count('. ') == 0, '%s: ObjectiveSummary debe ser UNA frase terminada en punto' % tag)
        hit = [w for w in SPOILER_WORDS if w.lower() in summ.lower()]
        ck.ok(not hit, '%s: ObjectiveSummary con palabras de spoiler %s' % (tag, hit))
        # jefe: tipo válido y nivel presente en la celda de eventos de la tabla 1.4
        bt = s.get('BossType', '')
        ck.ok(bt in BOSS_TYPES, '%s: BossType desconocido «%s»' % (tag, bt))
        bl = s.get('BossLevelCap', '')
        title = s.get('BossOrGymTitle', '')
        ck.ok(bool(title) == bool(bl), '%s: BossOrGymTitle y BossLevelCap deben ir juntos' % tag)
        if bl:
            nums = set(int(x) for x in re.findall(r'\d+', rows14[i - 1]['events']))
            rng = re.findall(r'Nv (\d+)[–-](\d+)', rows14[i - 1]['events'])
            for a, b2 in rng:
                nums.update(range(int(a), int(b2) + 1))
            ck.ok(int(bl) in nums, '%s: BossLevelCap %s no aparece en «%s»' % (tag, bl, rows14[i - 1]['events']))
            ck.ok(int(bl) <= cd, '%s: BossLevelCap %s supera LevelCapDay %d' % (tag, bl, cd))
        # MT
        tms = [t for t in s.get('RecommendedTMsAvailable', '').split(';') if t]
        for t in tms:
            ck.ok(re.match(r'^TM(0[1-9]|[1-9]\d|100)$', t) is not None, '%s: MT inválida %s' % (tag, t))
        seen_tm += tms
        # objetos clave
        for it in [x for x in s.get('KeyItemsUnlocked', '').split(';') if x]:
            ck.ok(it in items and items[it][2] == 8, '%s: objeto clave %s no existe (bolsillo 8) en proposed_items.txt' % (tag, it))
            if it in items:
                want = KEY_ITEM_LOC_EXCEPTIONS.get((i, it), lk)
                ck.ok(items[it][1] in by9.get(want, {}).get('items', []),
                      '%s: %s («%s») no figura en el cuadro de objetos de %s (Vol. 9)' % (tag, it, items[it][1], want))
        ck.ok(s.get('MedalsAfterStep', '').isdigit() and 0 <= int(s.get('MedalsAfterStep')) <= 8, '%s: MedalsAfterStep inválido' % tag)
        for c in [x for x in s.get('Chapters', '').split(';') if x]:
            ck.ok(c in chap_keys, '%s: capítulo inexistente %s' % (tag, c))
    exp = ['TM%02d' % n for n in range(1, 101)]
    ck.ok(len(seen_tm) == 100 and set(seen_tm) == set(exp), 'las MT por paso no cubren TM01..TM100 exactamente una vez (vistas %d, únicas %d)' % (len(seen_tm), len(set(seen_tm))))
    # coherencia con la tabla 4.3 del Vol. 9 y con Cap. 5
    for n in range(1, 101):
        ck.ok(tm_loc[n] is not None, 'MT%02d sin ubicación en la tabla 4.3 del Vol. 9' % n)
        ck.ok(('MT%02d' % n) in ' '.join(x.split(' · ')[0] for x in by9[tm_loc[n]]['items']),
              'MT%02d no figura en el cuadro de %s (Cap. 5 vs tabla 4.3)' % (n, tm_loc[n]))
    # tope de medallas = 8 gimnasios
    ck.ok(sum(1 for s in secs if s.get('BossOrGymTitle', '').startswith('Gimnasio ')) == 8, 'debe haber 8 gimnasios')
    ck.ok(secs[-1].get('MedalsAfterStep') == '8', 'el último paso debe cerrar con 8 medallas')
    # tabla acto -> nº de MT (Vol. 9 §4.1: 16/17/29/24/14)
    per_act = {}
    for s in secs:
        per_act[s.get('Act')] = per_act.get(s.get('Act'), 0) + len([t for t in s.get('RecommendedTMsAvailable', '').split(';') if t])
    ck.ok(per_act == {'I': 16, 'II': 17, 'III': 29, 'IV': 24, 'V': 14}, 'MT por acto distintas de la curva del Vol. 9: %s' % per_act)
    return secs


def expected_vol7_names():
    secs, lines = v7_sections()
    return secs, lines


def check_characters(g, ck, story_secs):
    secs = _sections(OUT_CHAR, ck, 'rem_characters.txt')
    ck.ok(len(secs) >= 25, 'rem_characters: %d personajes (mínimo 25)' % len(secs))
    keys = [s['key'] for s in secs]
    ck.ok(len(set(keys)) == len(keys), 'rem_characters: claves duplicadas')
    # todos los personajes del Vol. 7 están (28 definiciones: secciones 1.1-6.5)
    v7secs, v7lines = v7_sections()
    expected_secs = set(d['sec'].split(':')[0] for d in CHAR_DEFS)
    named = [k for k in v7secs if k != '5.1']
    ck.ok(set(named) <= expected_secs, 'secciones del Vol. 7 sin personaje: %s' % sorted(set(named) - expected_secs))
    alias2char = {}
    marker_out = {'P': 0, 'R': 0}
    for s in secs:
        tag = s['key']
        for f in ('Name', 'Role', 'Category'):
            ck.ok(bool(s.get(f)), '%s: falta %s' % (tag, f))
        ck.ok(s.get('Category') in CHAR_CATEGORIES, '%s: categoría desconocida «%s»' % (tag, s.get('Category')))
        locs = [x for x in s.get('Locations', '').split(';') if x]
        for l in locs + ([s.get('FirstLocation')] if s.get('FirstLocation') else []):
            ck.ok(l in LOC_KEYSET, '%s: LOC_KEY inválida «%s»' % (tag, l))
        ck.ok(bool(locs) and s.get('FirstLocation') == locs[0], '%s: FirstLocation debe ser la primera de Locations' % tag)
        for ch in s.all('Chronology'):
            k = ch.split(' | ')[2] if len(ch.split(' | ')) > 2 else ''
            ck.ok(k == '' or k in LOC_KEYSET, '%s: Chronology con LOC_KEY inválida «%s»' % (tag, k))
        for a in [x for x in s.get('Aliases', '').split(';') if x]:
            alias2char.setdefault(norm(a), set()).add(tag)
        for t in s.all('Team'):
            marker_out['P'] += t.count('[PENDIENTE DE ASIGNACIÓN]')
            marker_out['R'] += t.count('[EN REVISIÓN*]')
    # marcadores de equipo: recuento literal contra el Vol. 7 (filas Slot/Ace de las tablas de equipo)
    marker_md = {'P': 0, 'R': 0}
    for l in v7lines:
        if re.match(r'^\|\s*(Slot \d|Ace)', l):
            marker_md['P'] += l.count('[PENDIENTE DE ASIGNACIÓN]')
            marker_md['R'] += l.count('[EN REVISIÓN\\*]')
    dom = [s for s in secs if s.get('Category') == 'Dominante']
    ck.ok(marker_out['R'] == marker_md['R'], 'marcadores [EN REVISIÓN*]: salida %d != Vol. 7 %d' % (marker_out['R'], marker_md['R']))
    ck.ok(sum(t.count('[PENDIENTE DE ASIGNACIÓN]') for s in secs if s.get('Category') != 'Dominante' for t in s.all('Team')) == marker_md['P'],
          'marcadores [PENDIENTE DE ASIGNACIÓN] de personajes != Vol. 7')
    for s in dom:
        ck.ok(all('[Especie y Equipo Pendientes de Asignación]' in t for t in s.all('Team')), '%s: marcador de Dominante perdido' % s['key'])
    # cada Vol.7-cronología y cada «Personajes presentes» del Vol. 6 queda contenido en Locations
    pres6 = parse_v6_presence()
    by_slug = dict((s['key'], s) for s in secs)
    for d in CHAR_DEFS:
        s = by_slug['CHAR_%s' % d['slug']]
        have = set(x for x in s.get('Locations', '').split(';') if x)
        for loc in _presence_locs(d['presence'], pres6) if d['presence'] else []:
            ck.ok(loc in have, '%s: falta %s de «Personajes presentes» (Vol. 6)' % (s['key'], loc))
        for ch in s.all('Chronology'):
            k = ch.split(' | ')[2]
            ck.ok((not k) or k in have, '%s: falta %s de la cronología (Vol. 7)' % (s['key'], k))
    # los nombres de escena del Vol. 8 se resuelven a un único personaje
    unresolved = set()
    for s in story_secs:
        for nm in [x for x in s.get('CharactersInScene', '').split(';') if x]:
            r = alias2char.get(norm(nm), set())
            if len(r) != 1:
                unresolved.add(nm)
    ck.ok(not unresolved, 'nombres de escena sin personaje único: %s' % sorted(unresolved))
    return secs


def check_story(g, ck):
    secs = _sections(OUT_STORY, ck, 'rem_story.txt')
    keys = [s['key'] for s in secs]
    ck.ok(keys[0] == 'PRELUDE' and keys[-1] == 'FRAGMENT_LEDGER', 'rem_story: PRELUDE debe ir primero y FRAGMENT_LEDGER último')
    chap = [s for s in secs if s['key'].startswith('CHAPTER_')]
    ck.ok([c['key'] for c in chap] == ['CHAPTER_%02d' % i for i in range(1, 69)], 'rem_story: capítulos no son CHAPTER_01..68 consecutivos')
    ck.ok(len(secs) == 70, 'rem_story: %d secciones (esperadas 70)' % len(secs))
    # ---- integridad del texto contra el Markdown (extracción independiente) ----
    md = read_lines(V8)
    heads = [i for i, l in enumerate(md) if re.match(r'^## \d+\. ', l)]
    tot_md = tot_out = par_md = par_out = 0
    for idx, h in enumerate(heads):
        end = heads[idx + 1] if idx + 1 < len(heads) else len(md)
        for j in range(h + 1, end):
            if md[j].startswith('# '):
                end = j
                break
        seg = md[h + 1:end]
        ih = next((i for i, l in enumerate(seg) if l.startswith('#### ')), len(seg))
        ps = [l for l in seg[:ih] if l.strip() and not l.strip().startswith('|') and not l.strip().startswith('<!--')]
        bl = [l.strip()[2:] for l in seg[ih + 1:] if l.strip().startswith('- ')]
        c = chap[idx]
        out_p = c.all('NarrativeText')
        out_b = c.all('Milestones') + ([('Por qué importa: ' + c.get('WhyItMatters'))] if c.get('WhyItMatters') else [])
        ck.ok(len(out_p) == len(ps), '%s: %d párrafos en el .txt frente a %d en el .md' % (c['key'], len(out_p), len(ps)))
        ck.ok(sig(''.join(out_p)) == sig(''.join(ps)), '%s: el texto narrativo difiere del .md' % c['key'])
        ck.ok(len(out_b) == len(bl) and sig(''.join(out_b)) == sig(''.join(bl)), '%s: los hitos difieren del .md' % c['key'])
        par_md += len(ps)
        par_out += len(out_p)
        tot_md += len(sig(''.join(ps)))
        tot_out += len(sig(''.join(out_p)))
        # acto, ubicación, personajes
        want_act = next(a for lo, hi, a in ACT_BY_CHAPTER if lo <= idx + 1 <= hi)
        ck.ok(c.get('Act') == want_act, '%s: Act %s (esperado %s)' % (c['key'], c.get('Act'), want_act))
        ck.ok(c.get('LocationKey') in LOC_KEYSET, '%s: LocationKey inválida «%s»' % (c['key'], c.get('LocationKey')))
        for a in [x for x in c.get('AltLocations', '').split(';') if x]:
            ck.ok(a in LOC_KEYSET, '%s: AltLocations inválida %s' % (c['key'], a))
        ck.ok(bool(c.get('Title')) and bool(c.get('CharactersInScene')), '%s: sin título o sin personajes' % c['key'])
    ck.ok(par_md == par_out and tot_md == tot_out, 'párrafos/caracteres narrativos no cuadran (md %d/%d, txt %d/%d)' % (par_md, tot_md, par_out, tot_out))
    # preludio
    ip = next(i for i, l in enumerate(md) if l.startswith('## Preludio'))
    jp = next(i for i in range(ip + 1, len(md)) if md[i].startswith('# '))
    pm = [l for l in md[ip + 1:jp] if l.strip()]
    pre = secs[0]
    ck.ok(len(pre.all('NarrativeText')) == len(pm) and sig(''.join(pre.all('NarrativeText'))) == sig(''.join(pm)), 'PRELUDE: texto distinto del .md')
    # libro de cuentas
    led = secs[-1]
    chap_loc = dict((c['key'], c.get('LocationKey')) for c in chap)
    for n in range(1, 7):
        v = led.get('Fragment%d' % n)
        parts = v.split(',', 4)
        ck.ok(len(parts) == 5 and all(parts), 'FRAGMENT_LEDGER Fragment%d: formato Nombre,Dominante,LOC,CHAPTER,Nota' % n)
        if len(parts) == 5:
            ck.ok(parts[2] in LOC_KEYSET, 'Fragment%d: LOC inválida' % n)
            ck.ok(parts[3] in chap_loc and chap_loc[parts[3]] == parts[2], 'Fragment%d: el capítulo %s no transcurre en %s' % (n, parts[3], parts[2]))
    ck.ok(led.get('Fragment7', '') == '', 'el libro de cuentas debe tener exactamente 6 fragmentos')
    return secs, chap


def check_cross(prog, chap, ck):
    """Pasos <-> capítulos: cada capítulo asociado a un paso transcurre en la ubicación del paso (o la lista como alternativa)."""
    cl = dict((c['key'], c) for c in chap)
    for s in prog:
        for ck_ in [x for x in s.get('Chapters', '').split(';') if x]:
            c = cl[ck_]
            alts = [x for x in c.get('AltLocations', '').split(';') if x]
            ck.ok(c.get('LocationKey') == s.get('LocationKey') or s.get('LocationKey') in alts,
                  '%s -> %s: ubicación %s distinta de %s' % (s['key'], ck_, c.get('LocationKey'), s.get('LocationKey')))
            ck.ok(c.get('Act') == s.get('Act'), '%s -> %s: acto del paso (%s) distinto del del capítulo (%s)' % (
                s['key'], ck_, s.get('Act'), c.get('Act')))
    used = set(x for s in prog for x in s.get('Chapters', '').split(';') if x)
    ck.ok(used == set(cl), 'capítulos sin paso: %s' % sorted(set(cl) - used))


def run_check(g):
    ck = Checker()
    check_files(g, ck)
    prog = check_progression(g, ck)
    story, chap = check_story(g, ck)
    chars = check_characters(g, ck, chap)
    check_cross(prog, chap, ck)
    return ck, prog, chars, story, chap


def summarize(g, ck, prog, chars, story, chap):
    n_par = sum(len(c.all('NarrativeText')) for c in chap)
    n_chars = sum(len(p) for c in chap for p in c.all('NarrativeText'))
    print('rem_progression.txt : %d pasos | topes día %s..%s, noche %s..%s' % (
        len(prog), prog[0].get('LevelCapDay'), prog[-1].get('LevelCapDay'), prog[0].get('LevelCapNight'), prog[-1].get('LevelCapNight')))
    print('rem_characters.txt  : %d personajes (%s)' % (len(chars), ', '.join(
        '%s %d' % (k, sum(1 for c in chars if c.get('Category') == k)) for k in sorted(set(c.get('Category') for c in chars)))))
    print('rem_story.txt       : Preludio + %d capítulos + libro de cuentas (%d fragmentos) | %d párrafos, %d caracteres de narración'
          % (len(chap), sum(1 for i in range(1, 7) if story[-1].get('Fragment%d' % i)), n_par, n_chars))
    print('Palabras de spoiler vigiladas en ObjectiveSummary: ' + ', '.join(SPOILER_WORDS))
    for msg in ck.infos:
        print('  info:', msg)
    if ck.errors:
        print('\nERRORES (%d):' % len(ck.errors))
        for e in ck.errors:
            print('  -', e)
    else:
        print('\nVALIDACIÓN OK: 0 errores, 0 avisos de remini_ref.parse')


def main(argv):
    check_only = '--check' in argv
    g = generate()
    if not check_only:
        write_lines(OUT_PROG, g['prog'])
        write_lines(OUT_CHAR, g['char'])
        write_lines(OUT_STORY, g['story'])
        print('Escritos: %s, %s, %s' % tuple(os.path.relpath(p, ROOT) for p in (OUT_PROG, OUT_CHAR, OUT_STORY)))
    ck, prog, chars, story, chap = run_check(g)
    summarize(g, ck, prog, chars, story, chap)
    if '--diffs' in argv:
        for slug, only7, only6 in g['diffs']:
            if only7 or only6:
                print('  %-18s solo Vol.7: %s | solo Vol.6: %s' % (slug, ','.join(only7) or '-', ','.join(only6) or '-'))
    return 1 if ck.errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
