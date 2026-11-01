#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_baseline.py - genera PBS/rem_vanilla_baseline.txt y PBS/rem_changelog.txt (SPEC.md §2.8).

BASELINE  = valores ORIGINALES (vanilla) leidos EXCLUSIVAMENTE de PBS_backup_original/ (solo lectura):
            pokemon.txt (#001-#721), moves.txt, abilities.txt, items.txt y, resumida en conteos, tm.txt.
CHANGELOG = notas de diseno en espanol (el «por que»; las cifras las calcula la app) extraidas de docs/rebalance/:
            1_Pokemon_Master_Guide.md (rol, retipados, deltas, evoluciones, habilidades), vol. 2 (habilidades, texto
            propio aqui), proposed_moves.txt + 3_Moves_Master_Guide.pdf (movimientos), proposed_items.txt +
            9_Items_and_Economy_Master_Guide.md (objetos), proposed_items.txt (MT, Vol. 5).

Uso:
    python3 tools/rebalance/phase1/build_baseline.py            # genera los dos archivos en PBS/
    python3 tools/rebalance/phase1/build_baseline.py --check    # regenera en memoria, compara con disco y valida
    python3 tools/rebalance/phase1/build_baseline.py --date 2026-10-28   # fija la fecha [META] Generated

Python 3 stdlib. PyMuPDF (fitz) es opcional: solo se usa en --check para cruzar estados con los PDF.
Nunca se lee nada de PBS/ (solo se escribe alli); nunca se toca PBS_backup_original/ ni Data/.
"""
import argparse
import csv
import datetime
import hashlib
import io
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ORIG = ROOT / 'PBS_backup_original'           # unica fuente de valores vanilla
DOCS = ROOT / 'docs' / 'rebalance'
OUT_BASELINE = ROOT / 'PBS' / 'rem_vanilla_baseline.txt'
OUT_CHANGELOG = ROOT / 'PBS' / 'rem_changelog.txt'
sys.path.insert(0, str(ROOT / 'tools' / 'codex'))

MAX_DEX = 721
FLAG_NAMES = {'a': 'contacto', 'b': 'protección', 'c': 'capa mágica', 'd': 'robo', 'e': 'copia', 'f': 'roca del rey',
              'g': 'descongela', 'h': 'crítico alto', 'i': 'mordisco', 'j': 'puñetazo', 'k': 'sonido',
              'l': 'polvo', 'm': 'pulso', 'n': 'bomba', 'o': 'baile'}
CAT_ES = {'Physical': 'Físico', 'Special': 'Especial', 'Status': 'Estado'}


# ----------------------------------------------------------------------------------------------------------------
# Lectura de PBS_backup_original (port fiel de csvfield! de 178_Compiler.rb)
# ----------------------------------------------------------------------------------------------------------------
def read_text(path):
    raw = Path(path).read_bytes()
    return raw.decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')


def md5_of(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def csvfield(s):
    """Devuelve (campo, resto). Campos entre comillas con escape '\\"'; sin comillas hasta la coma (rstrip)."""
    s = s.lstrip()
    if s[:1] == '"':
        s = s[1:]
        ret, escaped, consumed = [], False, 0
        for ch in s:
            consumed += 1
            if ch == '"' and not escaped:
                break
            if ch == '\\' and not escaped:
                escaped = True
            else:
                ret.append(ch)
                escaped = False
        rest = s[consumed:]
        m = re.match(r'^\s*,', rest)
        if m:
            rest = rest[m.end():]
        elif re.match(r'^\s*$', rest):
            rest = ''
        else:
            raise ValueError('campo entrecomillado invalido: ' + rest[:40])
        return ''.join(ret), rest
    if ',' in s:
        pre, post = s.split(',', 1)
        return pre.rstrip(), post
    return s.rstrip(), ''


def csv_record(line, nfields):
    """Primeros nfields campos (rellena con '') y la lista de campos sobrantes (extra)."""
    rest, out = line, []
    for _ in range(nfields):
        f, rest = csvfield(rest)
        out.append(f)
    extra = []
    while rest.strip():
        f, rest = csvfield(rest)
        extra.append(f)
    return out, extra


def csv_lines(path):
    for ln in read_text(path).split('\n'):
        ln = ln.rstrip()
        if ln.strip() and not ln.lstrip().startswith('#'):
            yield ln


MOVE_COLS = ['ID', 'SYM', 'Name', 'FunctionCode', 'Power', 'Type', 'Category', 'Accuracy', 'PP', 'AddlEffect', 'Target',
             'Priority', 'Flags', 'Description']
ABILITY_COLS = ['ID', 'SYM', 'Name', 'Description']
ITEM_COLS = ['ID', 'SYM', 'Name', 'Plural', 'Pocket', 'Price', 'Description', 'FieldUse', 'BattleUse', 'Special', 'Move']


def load_table(path, cols):
    """dict SYM -> dict de columnas (+ '_extra'); conserva el orden del archivo (dict ordenado)."""
    out = {}
    for ln in csv_lines(path):
        rec, extra = csv_record(ln, len(cols))
        d = dict(zip(cols, rec))
        d['_extra'] = extra
        if d['SYM'] in out:
            raise ValueError('simbolo duplicado en %s: %s' % (path, d['SYM']))
        out[d['SYM']] = d
    return out


def load_moves(base=ORIG):
    return load_table(base / 'moves.txt', MOVE_COLS)


def load_abilities(base=ORIG):
    return load_table(base / 'abilities.txt', ABILITY_COLS)


def load_items(base=ORIG):
    return load_table(base / 'items.txt', ITEM_COLS)


def load_types(base=ORIG):
    """INTERNALNAME -> nombre en espanol (types.txt original)."""
    out, cur = {}, {}
    for ln in read_text(base / 'types.txt').split('\n') + ['[END]']:
        ln = ln.strip()
        if ln.startswith('['):
            if cur.get('InternalName'):
                out[cur['InternalName']] = cur.get('Name', cur['InternalName'])
            cur = {}
        elif '=' in ln:
            k, v = ln.split('=', 1)
            cur[k.strip()] = v.strip()
    return out


def load_pokemon(base=ORIG, maxdex=MAX_DEX):
    """dex -> dict clave PBS -> valor crudo (solo #001-#maxdex)."""
    parts = re.split(r'^\[(\d+)\]\s*$', read_text(base / 'pokemon.txt'), flags=re.M)
    out = {}
    for i in range(1, len(parts), 2):
        n = int(parts[i])
        if n > maxdex:
            continue
        kv = {}
        for ln in parts[i + 1].split('\n'):
            if '=' in ln:
                k, v = ln.split('=', 1)
                kv[k.strip()] = v.strip()
        out[n] = kv
    return out


def load_tm_counts(base=ORIG):
    """MOVIMIENTO -> numero de especies que aprendian la MT original (tm.txt)."""
    counts, cur = {}, None
    for ln in read_text(base / 'tm.txt').split('\n'):
        ln = ln.strip()
        if not ln or ln.startswith('#'):
            continue
        m = re.match(r'^\[([A-Z0-9_]+)\]$', ln)
        if m:
            cur = m.group(1)
            counts[cur] = 0
        elif cur:
            counts[cur] += len([x for x in ln.split(',') if x.strip()])
    return counts


# ----------------------------------------------------------------------------------------------------------------
# Escritura INI
# ----------------------------------------------------------------------------------------------------------------
class Ini:
    def __init__(self, header):
        self.header = header
        self.lines = []

    def comment(self, text):
        self.lines.append('# ' + text)

    def section(self, key, items):
        """items: lista de (clave, valor); valor puede ser '' (clave vacia)."""
        self.lines.append('[%s]' % key)
        for k, v in items:
            v = '' if v is None else str(v)
            if '\n' in v or '\r' in v:
                raise ValueError('salto de linea en %s.%s' % (key, k))
            self.lines.append(('%s = %s' % (k, v)).rstrip() if v == '' else '%s = %s' % (k, v))
        self.lines.append('')

    def dumps(self):
        return '\r\n'.join(list(self.header) + [''] + self.lines).rstrip('\r\n') + '\r\n'


def write_ini(path, text):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(text)


# ----------------------------------------------------------------------------------------------------------------
# BASELINE
# ----------------------------------------------------------------------------------------------------------------
def build_baseline_text():
    pk = load_pokemon()
    mv = load_moves()
    ab = load_abilities()
    it = load_items()
    tm = load_tm_counts()
    hdr = [
        '# rem_vanilla_baseline.txt - valores VANILLA (PBS_backup_original/) de Pokémon #001-#721, movimientos, habilidades y objetos. Generado por tools/rebalance/phase1/build_baseline.py; no editar a mano.',
        '# Formato INI (SPEC §2): [POKEMON_NNN] [MOVE_SIMBOLO] [ABILITY_SIMBOLO] [ITEM_SIMBOLO]; «Clave = Valor» sin comillas; copia fiel del PBS original (claves ausentes en origen = valor vacío).',
        '# Pokémon: Types = A,B | BaseStats = HP,ATK,DEF,SPE,SPA,SPD (orden PBS) | Abilities y HiddenAbility tal cual | Evolutions = HIJO,Método,Param,... | Moves = nv,MOV,nv,MOV,... | EggMoves y WildItem* crudos.',
        '# Movimiento: ID, Name, Type, Category, Power, Accuracy, PP, Priority, FunctionCode, AddlEffect, Target, Flags, Description. Objeto: ID, Name, Plural, Pocket, Price, Description, FieldUse, BattleUse, Special, Move.',
        '# [TM_VANILLA_COUNTS]: MOVIMIENTO = nº de especies que aprendían la MT original (las listas completas, 374 KB, siguen en PBS_backup_original/tm.txt; se omiten aquí por tamaño).',
        '# Origen (md5): pokemon=%s moves=%s abilities=%s items=%s tm=%s' % tuple(
            md5_of(ORIG / (n + '.txt'))[:12] for n in ('pokemon', 'moves', 'abilities', 'items', 'tm')),
    ]
    ini = Ini(hdr)
    for n in sorted(pk):
        d = pk[n]
        types = ','.join(t for t in (d.get('Type1', ''), d.get('Type2', '')) if t)
        ini.section('POKEMON_%03d' % n, [
            ('Name', d.get('Name', '')),
            ('InternalName', d.get('InternalName', '')),
            ('Types', types),
            ('BaseStats', d.get('BaseStats', '')),
            ('Abilities', d.get('Abilities', '')),
            ('HiddenAbility', d.get('HiddenAbility', '')),
            ('Evolutions', d.get('Evolutions', '')),
            ('Moves', d.get('Moves', '')),
            ('EggMoves', d.get('EggMoves', '')),
            ('WildItemCommon', d.get('WildItemCommon', '')),
            ('WildItemUncommon', d.get('WildItemUncommon', '')),
            ('WildItemRare', d.get('WildItemRare', '')),
        ])
    for s, d in mv.items():
        items = [('ID', d['ID']), ('Name', d['Name']), ('Type', d['Type']), ('Category', d['Category']),
                 ('Power', d['Power']), ('Accuracy', d['Accuracy']), ('PP', d['PP']), ('Priority', d['Priority']),
                 ('FunctionCode', d['FunctionCode']), ('AddlEffect', d['AddlEffect']), ('Target', d['Target']),
                 ('Flags', d['Flags']), ('Description', d['Description'])]
        if d['_extra']:
            # linea con campos sobrantes en el original (p. ej. BURNINGJEALOUSY): el motor los ignora; se conservan aqui
            items.append(('ExtraFields', ','.join(d['_extra'])))
        ini.section('MOVE_' + s, items)
    for s, d in ab.items():
        ini.section('ABILITY_' + s, [('ID', d['ID']), ('Name', d['Name']), ('Description', d['Description'])])
    for s, d in it.items():
        ini.section('ITEM_' + s, [(k, d[k]) for k in ('ID', 'Name', 'Plural', 'Pocket', 'Price', 'Description',
                                                       'FieldUse', 'BattleUse', 'Special', 'Move')])
    ini.section('TM_VANILLA_COUNTS', [(m, c) for m, c in tm.items()])
    return ini.dumps()


# ----------------------------------------------------------------------------------------------------------------
# Utilidades de markdown (docs/rebalance)
# ----------------------------------------------------------------------------------------------------------------
def md_clean(s):
    s = s.replace('\\*', '').replace('**', '').replace('`', '')
    s = s.replace('\\|', '|').replace('\\_', '_')
    return re.sub(r'\s+', ' ', s).strip()


def md_tables(text):
    """Lista de (encabezado_previo, cabecera[], filas[[]]) de todas las tablas |...| del markdown."""
    out, heading, cur, hdr = [], '', None, None
    for ln in text.split('\n') + ['']:
        if ln.startswith('#'):
            heading = ln.lstrip('#').strip()
        if ln.startswith('|'):
            cells = [md_clean(c) for c in re.split(r'(?<!\\)\|', ln.strip())[1:-1]]
            if cur is None:
                cur, hdr = [], cells
            elif all(re.match(r'^:?-{2,}:?$', c) for c in cells):
                pass
            else:
                cur.append(cells)
        else:
            if cur is not None:
                out.append((heading, hdr, cur))
            cur, hdr = None, None
    return out


def find_table(tables, heading_prefix, first_col=None, nth=0):
    hits = [t for t in tables if t[0].startswith(heading_prefix) and (first_col is None or t[1][0].startswith(first_col))]
    return hits[nth]


# ----------------------------------------------------------------------------------------------------------------
# CHANGELOG: Pokemon
# ----------------------------------------------------------------------------------------------------------------
def parse_pokemon_doc():
    text = (DOCS / '1_Pokemon_Master_Guide.md').read_text(encoding='utf-8')
    head, _, body = text.partition('## Generación 1')
    # metodos de evolucion por piedra/objeto (tablas de cabecera del volumen)
    methods = set()
    for h, hdr, rows in md_tables(head):
        if hdr and hdr[0] in ('Piedra', 'Objeto'):
            methods.update(r[0] for r in rows)
    ents = {}
    parts = re.split(r'^### #(\d+) (.*)$', body, flags=re.M)
    for i in range(1, len(parts), 3):
        dex, name, blk = int(parts[i]), parts[i + 1].strip(), parts[i + 2]
        e = {'name': name, 'extra': []}
        for ln in blk.split('\n'):
            m = re.match(r'^- \*\*(.+?):\*\* ?(.*)$', ln)
            if not m:
                continue
            label, val = m.group(1), md_clean(m.group(2))
            if label.startswith('Cambio de habilidad'):
                e['extra'].append((label, val))
            else:
                e[label] = val
        ents[dex] = e
    return ents, methods


STAT_RE = re.compile(r'^(PS|Atq|Def|AEsp|DEsp|Vel|Total) (\d+)(?: \(([+-]\d+)\))?$')


def pokemon_notes(e, methods):
    notes = []
    tipo = e.get('Tipo', '')
    if '(Antes:' in tipo:
        notes.append('Retipado: ' + tipo)
    deltas = []
    for part in e.get('Stats', '').split(' / '):
        m = STAT_RE.match(part.strip())
        if m and m.group(3):
            deltas.append('%s %s (%s)' % (m.group(1), m.group(2), m.group(3)))
    if deltas:
        notes.append('Stats modificados respecto al original: ' + ', '.join(deltas))
    evo = e.get('Evolución', '')
    mm = re.match(r'^Desde [^:]+: (.+?)(?: \(|\s→|$)', evo)
    method = mm.group(1).strip() if mm else ''
    if method in methods:
        notes.append('Evolución por piedra/objeto (se usa sobre el Pokémon): ' + evo)
    elif '(Antes:' in evo:
        notes.append('Evolución modificada: ' + evo)
    hab = e.get('Habilidades', '')
    if '(Antes:' in hab:
        notes.append('Habilidades modificadas: ' + hab.replace(' ★', ''))
    for label, val in e['extra']:
        m = re.match(r'^Cambio de habilidad (v\d) \(slot (\d)\)$', label)
        notes.append('Cambio de habilidad %s (ranura %s), justificación del Vol. 1 (en inglés en el original): %s' % (m.group(1), m.group(2), val) if m else '%s: %s' % (label, val))
    return notes


def pokemon_role(e):
    rol = e.get('Rol / Diseño', '')
    rol = re.sub(r'\.?\s*Retipado \(ver tipos\)', '', rol).strip(' .')
    return rol


# ----------------------------------------------------------------------------------------------------------------
# CHANGELOG: habilidades (Vol. 2; texto del efecto nuevo traducido del Vol. 2, «antes» = descripcion PBS original)
# ----------------------------------------------------------------------------------------------------------------
# {A:SIMBOLO}, {M:SIMBOLO}, {I:SIMBOLO} se sustituyen por el nombre espanol del PBS original.
ABILITY_REWORK = {
    'ILLUMINATE': ('Reworked', 'Al entrar en combate, baja 1 nivel la Precisión de todos los rivales. Lo bloquean {A:CLEARBODY}, {A:WHITESMOKE}, {A:FULLMETALBODY}, {A:KEENEYE}, {A:FLOWERVEIL} (tipo Planta), {M:MIST} y {M:SUBSTITUTE}. Se conserva la mejora de encuentros salvajes.'),
    'FOREWARN': ('Reworked', 'Al entrar en combate, baja 1 nivel el Ataque Especial de todos los rivales (una Intimidación especial). Activa {A:DEFIANT}/{A:COMPETITIVE} y se invierte con {A:CONTRARY}; lo bloquean {A:CLEARBODY}, {A:WHITESMOKE}, {A:FULLMETALBODY}, {A:FLOWERVEIL} (tipo Planta), {M:MIST} y {M:SUBSTITUTE}.'),
    'PUREPOWER': ('Reworked', 'Duplica el Ataque Especial (x2,0) en lugar del Ataque físico, como espejo especial de {A:HUGEPOWER}. Asignada a Dustox, Bunnelby y Diggersby (Ataque Especial efectivo 120 / 106 / 170).'),
    'PROPELLERTAIL': ('Reworked', 'Los movimientos dañinos sin contacto hacen x1,20 de daño (espejo a distancia de {A:TOUGHCLAWS}, x1,30). Pierde el antiguo efecto de ignorar los movimientos o habilidades que atraen ataques, que conserva {A:STALWART}.'),
    'SHELLARMOR': ('Reworked', 'Recibe x0,85 de daño de los movimientos físicos (ya no bloquea los golpes críticos). {A:BATTLEARMOR} mantiene la inmunidad total a los críticos.'),
    'VITALSPIRIT': ('Reworked', 'Impide el sueño y también la Congelación/Heladura (el estado de daño residual y mitad de Ataque Especial del Vol. 2).'),
    'SANDVEIL': ('Reworked', 'En tormenta de arena, Defensa x1,25. Se elimina la Evasión aleatoria.'),
    'SNOWCLOAK': ('Reworked', 'Con Nieve (Gen 9, sustituye al Granizo), Defensa Especial x1,20, simétrica a {A:SANDVEIL}. Se elimina la Evasión aleatoria.'),
    'RUNAWAY': ('Reworked', 'Velocidad x1,25 mientras sus PS sean el 50 % o menos. Se conserva la huida de Pokémon salvajes.'),
    'HONEYGATHER': ('Reworked', 'Al entrar en combate, baja 1 nivel la Velocidad de todos los rivales. Se conserva la Miel fuera de combate.'),
    'BALLFETCH': ('Reworked', 'Al entrar en combate, +1 Velocidad si algún miembro del equipo está debilitado (individuales y dobles). Se conserva la recuperación de Poké Balls tras el combate.'),
    'PASTELVEIL': ('Reworked', '+1 Defensa Especial al recibir un movimiento especial (espejo especial de {A:STAMINA}).'),
    'CURIOUSMEDICINE': ('Reworked', 'Al entrar en combate, restablece a 0 todos los cambios de características de los Pokémon rivales (una {M:HAZE} que solo afecta a los rivales; el bando propio conserva sus mejoras). Nada lo bloquea y {M:SUBSTITUTE} no lo detiene.'),
    'FLAREBOOST': ('Buffed', 'Ataque Especial x1,5 con Quemadura o Heladura, y queda exento de la mitad de Ataque Especial que impone la Heladura (igual que {A:GUTS} con la Quemadura).'),
    'SYNCHRONIZE': ('Buffed', 'Contagia Quemadura, Veneno, Parálisis y Heladura al atacante (la Heladura es nueva).'),
    'PLUS': ('Buffed', 'Ataque Especial x1,5 con un aliado {A:PLUS} o {A:MINUS}; x1,25 si está solo.'),
    'MINUS': ('Buffed', 'Ataque Especial x1,5 con un aliado {A:PLUS} o {A:MINUS}; Defensa Especial x1,20 si está solo.'),
    'STENCH': ('Buffed', '15 % de probabilidad de retroceso en movimientos dañinos cuando ataca primero (antes 10 %).'),
    'DAMP': ('Buffed', 'Impide los movimientos explosivos y recibe x0,80 de daño de los movimientos de tipo Fuego.'),
    'FRIENDGUARD': ('Buffed', 'Los aliados reciben x0,75 de daño (se mantiene) y el propio usuario recibe x0,90 en combates individuales.'),
    'LIGHTMETAL': ('Buffed', 'Peso a la mitad (se mantiene) y Velocidad x1,10.'),
    'HEAVYMETAL': ('Buffed', 'Peso doble (se mantiene) y Defensa x1,10.'),
    'HEALER': ('Buffed', 'Al final del turno recupera 1/8 de los PS máximos si tiene un estado alterado mayor (Quemadura, Heladura, Parálisis, Veneno o Sueño); conserva la cura del 30 % a un aliado en dobles.'),
    'KLUTZ': ('Buffed', 'Se mantiene el bloqueo del objeto equipado (aspecto negativo) y todos los movimientos dañinos hacen x1,20 de daño.'),
    'ICESCALES': ('Buffed', 'Daño especial recibido x0,5 (sustituye al efecto actual del motor, Defensa Especial x1,5).'),
    'ANTICIPATION': ('Buffed', 'Al entrar en combate, si algún rival conoce un movimiento supereficaz, +1 Velocidad.'),
}
# Las 11 habilidades que el Vol. 2 declara «explicitamente mantenidas»
ABILITY_KEPT = {
    'HUGEPOWER': 'Se mantiene sin cambios (duplica el Ataque físico). Su espejo especial es {A:PUREPOWER}: paridad de categoría.',
    'STALWART': 'Se mantiene: conserva la capacidad de ignorar los movimientos o habilidades que atraen ataques, que {A:PROPELLERTAIL} deja de tener.',
    'MAGMAARMOR': 'Se mantiene: su inmunidad a la congelación pasa a cubrir también la Heladura (y la cura si llega a sufrirla).',
    'ICEBODY': 'Se mantiene: con Nieve (Gen 9, sustituye al Granizo) recupera 1/16 de los PS al final del turno.',
    'RAINDISH': 'Se mantiene sin cambios (explícitamente conservada en el Vol. 2).',
    'SLUSHRUSH': 'Se mantiene y sigue funcionando con la Nieve de Gen 9, que sustituye al Granizo.',
    'SNOWWARNING': 'Se mantiene y sigue funcionando con la Nieve de Gen 9, que sustituye al Granizo.',
    'PICKUP': 'Se mantiene: la recogida de objetos funciona solo durante el combate (copia temporal del objeto) y nunca toca los datos permanentes del equipo.',
    'TURBOBLAZE': 'Se mantiene sin cambios (explícitamente conservada en el Vol. 2).',
    'TERAVOLT': 'Se mantiene sin cambios (explícitamente conservada en el Vol. 2).',
    'KEENEYE': 'Se mantiene: sigue impidiendo la bajada de Precisión, incluida la de la nueva {A:ILLUMINATE}.',
}
# Habilidades vanilla sin cambio de efecto pero con una nota util del Vol. 2 (Heladura)
ABILITY_UNTOUCHED_NOTES = {
    'LEAFGUARD': 'Sin cambios de efecto; su protección contra la congelación se aplica ahora a la Heladura (Vol. 2, pbCanFreeze?).',
    'FLOWERVEIL': 'Sin cambios de efecto; su protección de los Pokémon tipo Planta contra la congelación se aplica ahora a la Heladura (Vol. 2, pbCanFreeze?).',
}
# IDs de las 16 «firmas inactivas» del Vol. 2 (sin portadores Gen 1-6)
ABILITY_INACTIVE_IDS = [189, 190, 191, 213, 227, 229, 230, 231, 233, 240, 248, 254, 263, 264, 266, 267]


def resolve_names(text, ab, mv, it):
    def rep(m):
        kind, sym = m.group(1), m.group(2)
        tbl = {'A': ab, 'M': mv, 'I': it}[kind]
        return tbl[sym]['Name']
    return re.sub(r'\{([AMI]):([A-Z0-9_]+)\}', rep, text)


# ----------------------------------------------------------------------------------------------------------------
# CHANGELOG: movimientos
# ----------------------------------------------------------------------------------------------------------------
def fc_int(x):
    try:
        return int(x, 16)
    except ValueError:
        return x


def num(x):
    try:
        return int(x)
    except ValueError:
        return None


def tm_map(items):
    """numero de MT (int) -> simbolo de movimiento, para los objetos TMnn."""
    out = {}
    for s, d in items.items():
        m = re.match(r'^TM(\d+)$', s)
        if m and d['Move']:
            out[int(m.group(1))] = d['Move']
    return out


SPECIAL_MOVE_NOTES = {
    'BOOMBURST': 'Ajuste final del Vol. 3: 125 de potencia y 100 % de precisión, código de función 000 (movimiento de sonido de área simple, sin retroceso).',
    'POWERWHIP': 'Ajuste final del Vol. 3: 120 de potencia y 85 % de precisión, con su 30 % de bajar la Defensa.',
    'THROATCHOP': 'Ajuste final del Vol. 3: se deja sin bandera de sonido.',
    'DIZZYPUNCH': 'Vol. 3: bajada de potencia compensada (las bajadas de potencia solo se admiten donde se compensan).',
    'MOONBLAST': 'Vol. 3: bajada de potencia compensada (las bajadas de potencia solo se admiten donde se compensan).',
    'BELCH': 'Vol. 3: bajada de potencia compensada (las bajadas de potencia solo se admiten donde se compensan); sigue siendo el movimiento de tipo Veneno cuya potencia depende de los PS.',
    'MIST': 'Vol. 2/3: Neblina pasa a ser un movimiento de estado que inflige Heladura.',
}


def move_notes(sym, a, b, types, tm_old, tm_new, mv_names):
    notes = []
    status = b['Category'] == 'Status'
    if a['Type'] != b['Type']:
        kind = 'movimiento de estado' if status else 'ataque'
        notes.append('Retipado de %s (Vol. 3): %s → %s.' % (kind, types.get(a['Type'], a['Type']), types.get(b['Type'], b['Type'])))
    if a['Category'] != b['Category']:
        t = 'Cambia de categoría (Vol. 3): %s → %s.' % (CAT_ES[a['Category']], CAT_ES[b['Category']])
        if 'a' in a['Flags'] and 'a' not in b['Flags']:
            t += ' Pierde la bandera de contacto.'
        notes.append(t)
    if fc_int(a['FunctionCode']) != fc_int(b['FunctionCode']):
        if a['Description'] != b['Description']:
            if status:
                notes.append('Efecto de estado rediseñado (Vol. 3; ninguno de los 20 rediseñados sube tres características ni da Evasión): antes «%s»; ahora «%s»' % (a['Description'], b['Description']))
            else:
                notes.append('Efecto modificado (Vol. 3): antes «%s»; ahora «%s»' % (a['Description'], b['Description']))
        else:
            notes.append('Cambia el código de función (efecto) respecto al original (Vol. 3).')
    adj = []
    for f, label in (('Power', 'potencia'), ('Accuracy', 'precisión'), ('AddlEffect', 'probabilidad del efecto adicional')):
        x, y = num(a[f]), num(b[f])
        if x is not None and y is not None and x != y:
            adj.append('%s (%s)' % (label, 'sube' if y > x else 'baja'))
    if a['Flags'] != b['Flags']:
        add = [FLAG_NAMES[c] for c in b['Flags'] if c not in a['Flags']]
        rem = [FLAG_NAMES[c] for c in a['Flags'] if c not in b['Flags']]
        bits = (['+' + x for x in add] + ['-' + x for x in rem])
        adj.append('indicadores (%s)' % ', '.join(bits))
    if a['Target'] != b['Target']:
        adj.append('objetivo')
    if a['Priority'] != b['Priority']:
        adj.append('prioridad')
    if adj:
        notes.append('Ajustes del Vol. 3: ' + ', '.join(adj) + '.')
    if sym in SPECIAL_MOVE_NOTES:
        notes.append(SPECIAL_MOVE_NOTES[sym])
    return notes


def move_tm_notes(sym, tm_old, tm_new):
    old = sorted(n for n, m in tm_old.items() if m == sym)
    new = sorted(n for n, m in tm_new.items() if m == sym)
    if old == new:
        return []
    if new and not old:
        return ['Vol. 5: pasa a enseñarse como MT%02d (repertorio clásico de 100 MT; antes no era MT).' % new[0]]
    if old and not new:
        return ['Vol. 5: deja de ser MT (antes MT%02d).' % old[0]]
    return ['Vol. 5: cambia de número de MT (antes MT%02d, ahora MT%02d).' % (old[0], new[0])]


# ----------------------------------------------------------------------------------------------------------------
# CHANGELOG: objetos (Vol. 9)
# ----------------------------------------------------------------------------------------------------------------
def build_item_notes(it_old, it_new, mv_old, mv_new):
    """Devuelve (notes: dict SYM -> [Note], pruned: [(SYM, nombre vanilla)], stats)."""
    text = (DOCS / '9_Items_and_Economy_Master_Guide.md').read_text(encoding='utf-8')
    tabs = md_tables(text)
    notes = {}
    by_name = {}
    for s, d in it_old.items():
        by_name.setdefault(d['Name'].lower(), []).append(s)
    by_name_new = {}
    for s, d in it_new.items():
        by_name_new.setdefault(d['Name'].lower(), []).append(s)
    by_id_new = {int(d['ID']): s for s, d in it_new.items()}
    problems = []

    def add(sym, txt):
        notes.setdefault(sym, []).append(txt)

    def sym_of(name, pools=(by_name, by_name_new)):
        m = re.search(r'\[([A-Z0-9_]+)\]\s*$', name)
        if m:
            return m.group(1)
        nm = re.sub(r'\s*\[[A-Z0-9_]+\]\s*$', '', name).strip().lower()
        for pool in pools:
            if nm in pool:
                if len(pool[nm]) != 1:
                    problems.append('ambiguo: ' + name)
                    return None
                return pool[nm][0]
        problems.append('sin simbolo: ' + name)
        return None

    # 1.2 podados con motivo
    h, hdr, rows = find_table(tabs, '1.2 Tabla de Objetos Descartados', 'Código')
    reasons = {}
    n_pruned_doc = 0
    for code, reason, nn, names in rows:
        lst = [x.strip() for x in names.split(', ')]
        if len(lst) != int(nn):
            problems.append('recuento %s: %d != %s' % (code, len(lst), nn))
        for nm in lst:
            s = sym_of(nm, (by_name,))
            if s:
                reasons[s] = (code, reason)
                n_pruned_doc += 1
    pruned = [(s, d['Name']) for s, d in it_old.items() if s not in it_new]
    for s, nm in pruned:
        if s in reasons:
            code, reason = reasons[s]
            add(s, 'Podado (Vol. 9 §1.2, motivo %s): %s.' % (code, reason))
        else:
            add(s, 'Retirado del catálogo por decisión de diseño (Vol. 9 §1.2): sin motivo de poda ni sustituto.')
    # 1.3 nuevos
    h, hdr, rows = find_table(tabs, '1.3 Nuevas adiciones', 'ID')
    for r in rows:
        iid, nombre, cat, rar, efecto, impl = r[:6]
        s = by_id_new.get(int(iid))
        if not s:
            problems.append('id nuevo desconocido ' + iid)
            continue
        add(s, 'Objeto nuevo en REM (Vol. 9 §1.3, ID %s): categoría %s, rareza %s.' % (iid, cat, rar))
        add(s, 'Implementación: ' + impl + '.')
    # 1.3.5 Pokevial / Caramelo Infinito / Caramelo Raro
    h, hdr, rows = find_table(tabs, '1.3.5', 'Objeto')
    for r in rows:
        nombre, iid, rar, como, obt = r[:5]
        s = sym_of(nombre)
        if s:
            add(s, 'Comodidad de viaje (Vol. 9 §1.3.5): %s' % como.rstrip('.') + '.')
            add(s, 'Cómo se obtiene: %s' % obt.rstrip('.') + '.')
    # 1.3.6 objetos de evolucion por uso directo
    h, hdr, rows = find_table(tabs, '1.3.6', 'Objeto')
    for r in rows:
        nombre, iid, evo, antes, precio, donde, copias, efecto = r[:8]
        s = sym_of(nombre)
        if not s:
            continue
        if s not in it_new or int(it_new[s]['ID']) != int(iid):
            problems.append('id evolutivo %s: %s' % (nombre, iid))
        add(s, 'Objeto de evolución por uso directo (Vol. 9 §1.3.6; Tier 3, stock ilimitado): %s. Antes: %s.' % (evo, antes))
        add(s, 'Compra / venta: %s. Se vende en: %s. Efecto de combate que conserva: %s.' % (precio, donde, efecto.rstrip('.')))
    # 1.4 rebalanceo
    h, hdr, rows = find_table(tabs, '1.4 Rebalanceo', 'Objeto')
    plates = [s for s in it_old if s.endswith('PLATE')]
    for r in rows:
        objeto, viejo, nuevo, motivo = r[:4]
        syms = []
        m = re.match(r'^(\d+) (.+?) \((.+)\)$', objeto)
        if m and m.group(2).startswith('Potenciadores'):
            syms = [sym_of(x.strip()) for x in m.group(3).split(', ')]
        elif objeto.startswith('17 Tablas'):
            syms = plates
        else:
            syms = [sym_of(objeto)]
        for s in syms:
            if s:
                add(s, 'Rebalanceado (Vol. 9 §1.4): %s → %s. Motivo: %s.' % (viejo.rstrip('.'), nuevo.rstrip('.'), motivo.rstrip('.')))
    # Renombrados
    h, hdr, rows = find_table(tabs, 'Renombrados', 'Símbolo')
    for sym, viejo, nuevo in [r[:3] for r in rows]:
        add(sym, 'Renombrado (Vol. 9 §1.4): «%s» → «%s».' % (viejo, nuevo))
    # Precios por grupo con simbolos conocidos
    boosters = [s for s in notes if any('17 Potenciadores' in x or 'Potenciadores de tipo' in x for x in [])]
    h, hdr, rows = find_table(tabs, 'Rebalanceo de precios', 'Grupo')
    price_rows = {r[0]: r for r in rows}
    g = price_rows.get('Potenciadores de tipo y Pluma Hada')
    if g:
        h2, hdr2, rows2 = find_table(tabs, '1.4 Rebalanceo', 'Objeto')
        grp = [r for r in rows2 if r[0].startswith('17 Potenciadores')][0]
        mm = re.match(r'^\d+ .+? \((.+)\)$', grp[0])
        syms = [sym_of(x.strip()) for x in mm.group(1).split(', ')] + [sym_of('Pluma Hada')]
        for s in syms:
            if s:
                add(s, 'Precio (Vol. 9 §1.4): %s → %s. %s.' % (g[1].replace(' (algunos 9 800)', ''), g[2], g[3].rstrip('.')))
    g = price_rows.get('Caramelo Raro')
    if g:
        add('RARECANDY', 'Precio (Vol. 9 §1.4): %s → %s. %s.' % (g[1], g[2], g[3].rstrip('.')))
    # Capitulo 2: ficha de catalogo (categoria y rareza/tier) de los objetos conservados (los nuevos y las MT ya tienen su nota)
    rarity = {'Clave': 'Clave', 'Tier 2': 'Tier 2 · Raro', 'Tier 3': 'Tier 3 · Común', 'Tier 1 ·U': 'Tier 1 · Único',
              'Legendario ·U': 'Legendario · Único', 'Tier 1': 'Tier 1 · Único', 'Legendario': 'Legendario · Único'}
    new_ids = {int(d['ID']) for sy, d in it_new.items() if sy not in it_old}
    n_cat = 0
    for h, hdr, rows in tabs:
        if not (re.match(r'^2\.\d', h) and hdr and hdr[0] == 'ID' and len(hdr) >= 4 and hdr[3] == 'Rareza'):
            continue
        sec = h.split(' ')[0]
        for r in rows:
            iid = int(r[0])
            sy = by_id_new.get(iid)
            if sy is None:
                problems.append('catalogo: ID %s sin objeto' % r[0])
                continue
            if iid in new_ids:
                continue
            n_cat += 1
            notes.setdefault(sy, []).insert(0, 'Catálogo REM (Vol. 9 §%s): categoría %s · rareza %s.' % (sec, r[2], rarity.get(r[3], r[3])))
    # 4.3 MT: roster Vol. 5 + justificacion de reparto
    h, hdr, rows = find_table(tabs, '4.3 Tabla maestra', 'MT')
    tm_o, tm_n = tm_map(it_old), tm_map(it_new)
    for r in rows:
        mt, mov, tipo, cat, poder, ubic, metodo, just = r[:8]
        n = int(mt[2:])
        s = 'TM%02d' % n
        if s not in it_new:
            problems.append('MT sin objeto ' + s)
            continue
        mvs = tm_n.get(n)
        old = tm_o.get(n)
        t = 'Repertorio clásico de 100 MT (Vol. 5/Vol. 9 §4): %s enseña %s' % (mt, mv_new[mvs]['Name'] if mvs in mv_new else mov)
        if old and old != mvs:
            t += ' (en vanilla enseñaba %s)' % mv_old[old]['Name']
        add(s, t + '.')
        add(s, 'Reparto (%s, %s): %s' % (ubic, metodo, just))
    return notes, pruned, problems, n_pruned_doc


# ----------------------------------------------------------------------------------------------------------------
# CHANGELOG: ensamblado
# ----------------------------------------------------------------------------------------------------------------
def build_changelog_text(date_iso):
    pk = load_pokemon()
    mv_old = load_moves()
    ab = load_abilities()
    it_old = load_items()
    types = load_types()
    mv_new = load_table(DOCS / 'proposed_moves.txt', MOVE_COLS)
    it_new = load_table(DOCS / 'proposed_items.txt', ITEM_COLS)
    ents, methods = parse_pokemon_doc()
    hdr = [
        '# rem_changelog.txt - notas de diseño en español de Pokémon REM (Vol. 1-10): el «por qué» de cada cambio; las cifras (stats, potencias, precios...) las calcula la app comparando el baseline vanilla con el PBS actual.',
        '# Formato INI (SPEC §2.8): [META]; [POKEMON_NNN] Role + Note (repetible); [ABILITY_SIMBOLO] Status = Reworked|Buffed|Kept|Untouched + Note; [MOVE_SIMBOLO] y [ITEM_SIMBOLO] Note (repetible); [PRUNED_ITEMS] Item1..N = SIMBOLO,Nombre vanilla.',
        '# Fuentes: Pokémon = 1_Pokemon_Master_Guide.md; habilidades = Vol. 2 (antes = descripción PBS original); movimientos = Vol. 3 (+ proposed_moves.txt) y Vol. 5; objetos = Vol. 9 (+ proposed_items.txt). Generado por tools/rebalance/phase1/build_baseline.py.',
    ]
    ini = Ini(hdr)
    ini.section('META', [('Volumes', '1-10'), ('Generated', date_iso),
                         ('Description', 'Notas de diseño de Pokémon REM (región de Oniria, roster #001-#721): rol y cambios por especie, estado y efecto antiguo→nuevo por habilidad, rediseño de movimientos y de objetos, y lista de los 280 objetos podados. Complementa a rem_vanilla_baseline.txt.')])
    # Pokemon
    for n in sorted(pk):
        e = ents[n]
        items = [('Role', pokemon_role(e))] + [('Note', t) for t in pokemon_notes(e, methods)]
        ini.comment('#%03d %s' % (n, e['name']))
        ini.section('POKEMON_%03d' % n, items)
    # Habilidades
    inactive = {s for s, d in ab.items() if int(d['ID']) in ABILITY_INACTIVE_IDS}
    for s, d in ab.items():
        if s in ABILITY_REWORK:
            st, new = ABILITY_REWORK[s]
            note = 'Antes: %s → Ahora: %s' % (d['Description'], resolve_names(new, ab, mv_old, it_old))
            ini.section('ABILITY_' + s, [('Status', st), ('Note', note)])
        elif s in ABILITY_KEPT:
            ini.section('ABILITY_' + s, [('Status', 'Kept'), ('Note', resolve_names(ABILITY_KEPT[s], ab, mv_old, it_old))])
        else:
            items = [('Status', 'Untouched')]
            if s in ABILITY_UNTOUCHED_NOTES:
                items.append(('Note', ABILITY_UNTOUCHED_NOTES[s]))
            if s in inactive:
                items.append(('Note', 'Habilidad firma sin portadores en el plantel Gen 1-6 (inactiva en el Vol. 2): se conserva vanilla.'))
            ini.section('ABILITY_' + s, items)
    # Movimientos
    tm_old, tm_new = tm_map(it_old), tm_map(it_new)
    n_move_notes = 0
    for s, a in mv_old.items():
        b = mv_new[s]
        notes = move_notes(s, a, b, types, tm_old, tm_new, mv_old) + move_tm_notes(s, tm_old, tm_new)
        if notes:
            n_move_notes += 1
            ini.section('MOVE_' + s, [('Note', t) for t in notes])
    # Objetos
    inotes, pruned, problems, _ = build_item_notes(it_old, it_new, mv_old, mv_new)
    if problems:
        raise SystemExit('Problemas al resolver objetos del Vol. 9:\n  ' + '\n  '.join(problems))
    order = [s for s in it_old] + [s for s in it_new if s not in it_old]
    for s in order:
        if s in inotes:
            ini.section('ITEM_' + s, [('Note', t) for t in inotes[s]])
    ini.section('PRUNED_ITEMS', [('Item%d' % (i + 1), '%s,%s' % (s, nm)) for i, (s, nm) in enumerate(pruned)])
    return ini.dumps()


# ----------------------------------------------------------------------------------------------------------------
# CHECK
# ----------------------------------------------------------------------------------------------------------------
class Checker:
    def __init__(self):
        self.errors, self.oks = [], []

    def ok(self, cond, msg, detail=''):
        (self.oks if cond else self.errors).append(msg + ((' -> ' + detail) if (detail and not cond) else ''))
        print(('  OK   ' if cond else '  FAIL ') + msg + ((' -> ' + detail) if (detail and not cond) else ''))


def run_check(date_iso):
    import remini_ref
    c = Checker()
    print('== Fuentes originales intactas (md5 vs MANIFEST.md5)')
    man = {}
    for ln in (ORIG / 'MANIFEST.md5').read_text().splitlines():
        parts = ln.split()
        if len(parts) == 2:
            man[parts[1].lstrip('./')] = parts[0]
    for n in ('pokemon.txt', 'moves.txt', 'abilities.txt', 'items.txt', 'tm.txt', 'types.txt'):
        c.ok(man.get(n) == md5_of(ORIG / n), 'md5 %s coincide con el manifiesto' % n)
    print('== Archivos de salida')
    for p in (OUT_BASELINE, OUT_CHANGELOG):
        c.ok(p.exists(), 'existe ' + p.name)
        if not p.exists():
            return c
        raw = p.read_bytes()
        c.ok(raw.startswith(b'\xef\xbb\xbf'), p.name + ': BOM UTF-8')
        c.ok(b'\n' not in raw.replace(b'\r\n', b''), p.name + ': solo CRLF')
        c.ok(b'\xef\xbb\xbf' not in raw[3:], p.name + ': un unico BOM')
        _, warns = remini_ref.parse(str(p))
        c.ok(not warns, p.name + ': remini_ref.parse sin warnings', str(warns[:3]))
    # reproducibilidad
    meta_date = date_iso
    secs_c, _ = remini_ref.parse(str(OUT_CHANGELOG))
    for s in secs_c:
        if s['key'] == 'META':
            meta_date = s.get('generated') or date_iso
    print('== Reproducibilidad (regeneracion en memoria == disco)')
    c.ok(build_baseline_text().encode('utf-8-sig') == OUT_BASELINE.read_bytes(), 'baseline regenerado == archivo en disco')
    c.ok(build_changelog_text(meta_date).encode('utf-8-sig') == OUT_CHANGELOG.read_bytes(), 'changelog regenerado == archivo en disco')

    print('== Baseline vs PBS_backup_original (parseo independiente)')
    secs_b, _ = remini_ref.parse(str(OUT_BASELINE))
    sb = {s['key']: s for s in secs_b}
    pk_secs = [k for k in sb if k.startswith('POKEMON_')]
    c.ok(len(pk_secs) == 721, '721 secciones [POKEMON_NNN] en baseline', str(len(pk_secs)))
    c.ok(pk_secs == ['POKEMON_%03d' % i for i in range(1, 722)], 'POKEMON_001..721 consecutivas y en orden')
    # parseo independiente (regex por secciones, sin reutilizar load_pokemon)
    parts = re.split(r'^\[(\d+)\]\s*$', read_text(ORIG / 'pokemon.txt'), flags=re.M)
    raw_pk = {}
    for i in range(1, len(parts), 2):
        raw_pk[int(parts[i])] = dict(l.split('=', 1) for l in parts[i + 1].split('\n') if '=' in l)
    bad = []
    for n in range(1, 722):
        r, s = raw_pk[n], sb['POKEMON_%03d' % n]
        exp = {'name': r['Name'], 'internalname': r['InternalName'],
               'types': ','.join(t for t in (r['Type1'], r.get('Type2', '')) if t), 'basestats': r['BaseStats'],
               'abilities': r['Abilities'], 'hiddenability': r.get('HiddenAbility', ''), 'evolutions': r.get('Evolutions', ''),
               'moves': r['Moves'], 'eggmoves': r.get('EggMoves', ''), 'wilditemcommon': r.get('WildItemCommon', ''),
               'wilditemuncommon': r.get('WildItemUncommon', ''), 'wilditemrare': r.get('WildItemRare', '')}
        for k, v in exp.items():
            if s.get(k) != v.strip():
                bad.append('%d.%s' % (n, k))
    c.ok(not bad, 'los 721 Pokémon coinciden campo a campo (Name, Types, BaseStats, Abilities, HiddenAbility, Evolutions, Moves, EggMoves, WildItem*)', str(bad[:5]))
    c.ok(all(len(sb['POKEMON_%03d' % n].get('basestats').split(',')) == 6 for n in range(1, 722)), 'BaseStats con 6 valores en todos')
    # moves
    mv_secs = [k for k in sb if k.startswith('MOVE_')]
    c.ok(len(mv_secs) == 765, '765 movimientos en baseline', str(len(mv_secs)))
    mv_lines = [l for l in read_text(ORIG / 'moves.txt').split('\n') if l.strip() and not l.startswith('#')]
    c.ok(len(mv_lines) == 765, '765 líneas de movimiento en el original')
    badm = []
    for ln in mv_lines:
        row = next(csv.reader([ln]))
        s = sb['MOVE_' + row[1]]
        exp = {'id': row[0], 'name': row[2], 'functioncode': row[3], 'power': row[4], 'type': row[5], 'category': row[6],
               'accuracy': row[7], 'pp': row[8], 'addleffect': row[9], 'target': row[10], 'priority': row[11], 'flags': row[12]}
        for k, v in exp.items():
            if s.get(k) != v:
                badm.append(row[1] + '.' + k)
        if row[1] != 'RAZORWIND' and len(row) == 14 and s.get('description') != row[13]:
            badm.append(row[1] + '.description')
    c.ok(not badm, 'los 765 movimientos coinciden campo a campo con el original', str(badm[:5]))
    # abilities
    ab_lines = [l for l in read_text(ORIG / 'abilities.txt').split('\n') if l.strip()]
    ab_secs = [k for k in sb if k.startswith('ABILITY_')]
    c.ok(len(ab_secs) == len(ab_lines) == 267, 'todas las habilidades originales (267)', '%d/%d' % (len(ab_secs), len(ab_lines)))
    bada = []
    for ln in ab_lines:
        row = next(csv.reader([ln]))
        s = sb['ABILITY_' + row[1]]
        if (s.get('id'), s.get('name'), s.get('description')) != (row[0], row[2], row[3]):
            bada.append(row[1])
    c.ok(not bada, 'las 267 habilidades coinciden (ID, Name, Description)', str(bada[:5]))
    # items
    it_lines = [l for l in read_text(ORIG / 'items.txt').split('\n') if l.strip() and not l.startswith('#')]
    it_secs = [k for k in sb if k.startswith('ITEM_')]
    c.ok(len(it_secs) == len(it_lines) == 651, 'los 651 objetos originales', '%d/%d' % (len(it_secs), len(it_lines)))
    badi = []
    for ln in it_lines:
        row = next(csv.reader([ln]))
        row += [''] * (11 - len(row))
        s = sb['ITEM_' + row[1]]
        exp = dict(zip(['id', 'name', 'plural', 'pocket', 'price', 'description', 'fielduse', 'battleuse', 'special', 'move'],
                       [row[0], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]]))
        for k, v in exp.items():
            if s.get(k) != v:
                badi.append(row[1] + '.' + k)
    c.ok(not badi, 'los 651 objetos coinciden campo a campo', str(badi[:5]))
    # TM
    tmc = load_tm_counts()
    sect = sb.get('TM_VANILLA_COUNTS')
    c.ok(sect is not None and all(int(sect.get(m.lower())) == n for m, n in tmc.items()) and len(tmc) > 0,
         '[TM_VANILLA_COUNTS] con %d MT y conteos correctos' % len(tmc))
    # sin datos de PBS/: auditoria en tiempo de ejecucion de todas las lecturas durante la regeneracion
    opened = []
    orig_rb, orig_rt = Path.read_bytes, Path.read_text
    Path.read_bytes = lambda self: (opened.append(str(self)), orig_rb(self))[1]
    Path.read_text = lambda self, *a, **k: (opened.append(str(self)), orig_rt(self, *a, **k))[1]
    try:
        build_baseline_text()
        build_changelog_text(meta_date)
    finally:
        Path.read_bytes, Path.read_text = orig_rb, orig_rt
    pbs_dir = str(ROOT / 'PBS') + os.sep
    c.ok(opened and not [x for x in opened if x.startswith(pbs_dir)],
         'ninguna lectura en PBS/ al regenerar (%d archivos leídos, todos de PBS_backup_original/ o docs/rebalance/)' % len(set(opened)),
         str([x for x in opened if x.startswith(pbs_dir)][:3]))

    print('== Changelog')
    sc = {s['key']: s for s in secs_c}
    c.ok(sorted(k for k in sc if k.startswith('POKEMON_')) == ['POKEMON_%03d' % i for i in range(1, 722)], '721 [POKEMON_NNN] en changelog')
    c.ok(all(sc['POKEMON_%03d' % i].get('role') for i in range(1, 722)), 'todos los Pokémon con Role')
    npk_notes = sum(1 for i in range(1, 722) if sc['POKEMON_%03d' % i].all('note'))
    m = sc.get('META')
    c.ok(m is not None and m.get('volumes') == '1-10' and re.match(r'^\d{4}-\d\d-\d\d$', m.get('generated', '')) and m.get('description'), '[META] Volumes/Generated/Description')
    abk = [s for k, s in sc.items() if k.startswith('ABILITY_')]
    c.ok(len(abk) == 267, '267 [ABILITY_*] en changelog', str(len(abk)))
    stc = {}
    for s in abk:
        stc[s.get('status')] = stc.get(s.get('status'), 0) + 1
    c.ok(stc == {'Reworked': 13, 'Buffed': 13, 'Kept': 11, 'Untouched': 230}, 'estados de habilidad: 13 Reworked + 13 Buffed + 11 Kept + 230 Untouched', str(stc))
    c.ok(all(k[8:] in {s['SYM'] for s in load_abilities().values()} for k in sc if k.startswith('ABILITY_')), 'todos los ABILITY_* existen en el original')
    mvk = [k for k in sc if k.startswith('MOVE_')]
    c.ok(all(k in sb for k in mvk), 'todos los MOVE_* del changelog existen en el baseline', str([k for k in mvk if k not in sb][:3]))
    itk = [k for k in sc if k.startswith('ITEM_')]
    it_new = load_table(DOCS / 'proposed_items.txt', ITEM_COLS)
    c.ok(all(k in sb or k[5:] in it_new for k in itk), 'todos los ITEM_* existen en el baseline o en proposed_items.txt')
    pr = sc.get('PRUNED_ITEMS')
    prl = pr.all('item1') if False else [v for _, k, v in pr['items']] if pr else []
    exp_pruned = [s for s in load_items() if s not in it_new]
    c.ok(len(prl) == len(exp_pruned) == 280 and [x.split(',', 1)[0] for x in prl] == exp_pruned, '[PRUNED_ITEMS]: 280 objetos = original - proposed_items.txt')
    c.ok(all(('ITEM_' + x.split(',', 1)[0]) in sb and sc.get('ITEM_' + x.split(',', 1)[0]) is not None for x in prl), 'cada objeto podado tiene baseline y nota de motivo')
    n_new = sum(1 for s in it_new if s not in load_items())
    c.ok(n_new == 43 and all(sc.get('ITEM_' + s) is not None for s in it_new if s not in load_items()), '43 objetos nuevos con nota')
    # PDF opcional
    print('== Cruce opcional con los PDF (PyMuPDF)')
    try:
        import warnings
        warnings.simplefilter('ignore')
        import fitz
        d = fitz.open(str(DOCS / '2_Abilities_Master_Guide.pdf'))
        pdf = {}
        for pn in range(d.page_count):
            for t in d[pn].find_tables().tables:
                r = t.extract()
                if r and r[0] and r[0][0] == 'ID' and 'Status' in r[0]:
                    for row in r[1:]:
                        last = row[1].split('\n')[-1].strip() if row[1] else ''
                        if row[0] and row[0].strip().isdigit() and row[2] in ('Reworked', 'Buffed') and re.match(r'^[A-Z0-9]+$', last):
                            pdf[last] = row[2]
        mine = {s: v[0] for s, v in ABILITY_REWORK.items()}
        c.ok(pdf == mine, 'estados Reworked/Buffed == tablas del PDF del Vol. 2 (%d)' % len(pdf), str(set(pdf.items()) ^ set(mine.items())))
        d = fitz.open(str(DOCS / '3_Moves_Master_Guide.pdf'))
        tags = set()
        for pn in range(d.page_count):
            for t in d[pn].find_tables().tables:
                for row in t.extract():
                    if row and len(row) > 1 and row[1] and '[reworked]' in row[1]:
                        tags.add(row[1].split('\n')[-1].replace('[reworked]', '').strip())
        mv_old, mv_new = load_moves(), load_table(DOCS / 'proposed_moves.txt', MOVE_COLS)
        mine = {s for s, a in mv_old.items() if mv_new[s]['Category'] == 'Status' and fc_int(a['FunctionCode']) != fc_int(mv_new[s]['FunctionCode'])}
        c.ok(tags == mine, 'movimientos de estado rediseñados == etiquetas [reworked] del PDF del Vol. 3 (%d)' % len(tags), str(tags ^ mine))
    except ImportError:
        print('  (PyMuPDF no instalado: cruce omitido)')
    print('\nResumen: %d OK, %d FALLOS' % (len(c.oks), len(c.errors)))
    stats = {'pokemon_con_notas': npk_notes, 'moves_con_notas': len(mvk), 'items_con_notas': len(itk)}
    print('Cobertura de notas:', stats)
    return c


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true', help='valida los archivos de PBS/ contra PBS_backup_original/ y los regenera en memoria')
    ap.add_argument('--date', default=None, help='fecha ISO para [META] Generated (por defecto, hoy)')
    args = ap.parse_args()
    date_iso = args.date or datetime.date.today().isoformat()
    if args.check:
        c = run_check(date_iso)
        sys.exit(1 if c.errors else 0)
    write_ini(OUT_BASELINE, build_baseline_text())
    write_ini(OUT_CHANGELOG, build_changelog_text(date_iso))
    print('Escrito', OUT_BASELINE, OUT_BASELINE.stat().st_size, 'bytes')
    print('Escrito', OUT_CHANGELOG, OUT_CHANGELOG.stat().st_size, 'bytes')


if __name__ == '__main__':
    main()
