#!/usr/bin/env python3
"""build_items_shops.py - genera PBS/rem_location_items.txt y PBS/rem_shops.txt (Fase 1, agente rem-items).

Fuentes (solo lectura, todo dentro del repositorio):
  docs/rebalance/9_Items_and_Economy_Master_Guide.md   Cap. 5 (775 filas por ubicacion), 3.2 (Poke Mart por medallas),
                                                       3.2.1 (donde hay Poke Mart), 3.3 (8 tiendas especiales), 3.4 (29 misiones de Pia)
  docs/rebalance/proposed_items.txt                    simbolos PBS de los 414 objetos (MT = TM01..TM100)
  tools/codex/location_keys.json                       las 64 claves LOC_KEY
  docs/rebalance/6_World_and_Locations_Master_Guide.md (solo --check) tablas de objetos de cada ficha y frase de Poke Mart

Contrato: tools/codex/SPEC.md (2.3 y 2.4). Salida: UTF-8 con BOM + CRLF. No toca ningun otro fichero.

Uso:
  python3 tools/rebalance/phase1/build_items_shops.py            genera los dos ficheros y ejecuta la validacion
  python3 tools/rebalance/phase1/build_items_shops.py --check    solo valida (no escribe); sale con 1 si algo falla
  python3 tools/rebalance/phase1/build_items_shops.py --check --json RUTA/vol9_by_loc.json   cuadre extra con el JSON de trabajo

Decisiones de transcripcion (todas se aplican igual en cada ejecucion):
  * Se quita la marca de dato provisional "\\*" del md y la nota "—" (sin nota) queda vacia.
  * Zone nunca lleva comas (el parseo de ItemN usa maxsplit=4): ", " dentro de Zone se escribe " · " (separador propio de las zonas).
  * Qty sale de "Objeto xN" (1 por defecto). Las MT salen como TMxx.
  * Tiendas: un ItemN por objeto (las celdas multiobjeto del md se expanden; "35 bayas:" -> 35 lineas). El precio es la columna
    «Precio de compra» del md tal cual. Claves extra (permitidas por SPEC): Locations (marts), UniqueItems, ItemNote (tiendas),
    MissionInfoN (misiones).
"""
import argparse
import csv
import io
import json
import os
import re
import sys
import unicodedata
from collections import OrderedDict, Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'codex'))
import remini_ref  # noqa: E402

MD9 = os.path.join(ROOT, 'docs', 'rebalance', '9_Items_and_Economy_Master_Guide.md')
MD6 = os.path.join(ROOT, 'docs', 'rebalance', '6_World_and_Locations_Master_Guide.md')
ITEMS_TXT = os.path.join(ROOT, 'docs', 'rebalance', 'proposed_items.txt')
LOCKEYS = os.path.join(ROOT, 'tools', 'codex', 'location_keys.json')
OUT_ITEMS = os.path.join(ROOT, 'PBS', 'rem_location_items.txt')
OUT_SHOPS = os.path.join(ROOT, 'PBS', 'rem_shops.txt')
DEFAULT_JSON = ('/private/tmp/claude-502/-Users-a-perezalvarez-Documents-notion/285284a2-47ac-4049-b444-bc02040390e5/'
                'scratchpad/v10/vol9_by_loc.json')

METHODS = 'BHCNEJPS'
METHOD_NAMES = {'B': 'Poké Ball visible', 'H': 'Objeto oculto', 'C': 'Cofre', 'N': 'Regalo de PNJ', 'E': 'Evento / misión',
                'J': 'Botín de jefe o líder', 'P': 'Misión de Pía', 'S': 'Tienda (stock único)'}
EXPECTED_ROWS = 775
EXPECTED_MARTS = 9
EXPECTED_SHOPS = 8
EXPECTED_MISSIONS = 29


# --------------------------------------------------------------------------------------------- helpers
def nfc(s):
    return unicodedata.normalize('NFC', s)


def plain(s):
    """Texto del md -> texto de datos: sin escapes markdown, sin la marca provisional, '—' = sin dato."""
    s = nfc(s).strip()
    s = s.replace('\\*', '')
    s = s.replace('\\|', '|')
    s = s.strip()
    return '' if s == '—' else s


def split_row(line):
    """Celdas de una fila de tabla markdown (respeta \\|)."""
    cells = re.split(r'(?<!\\)\|', line.strip())
    return [c.strip() for c in cells[1:-1]]


def read_lines(path):
    with open(path, encoding='utf-8-sig') as f:
        return f.read().replace('\r\n', '\n').split('\n')


def load_items():
    """sym -> dict(id, name, price) y nombre(NFC) -> sym, desde proposed_items.txt."""
    items, by_name = OrderedDict(), {}
    with open(ITEMS_TXT, encoding='utf-8-sig') as f:
        for line in f:
            line = line.rstrip('\r\n')
            if not line or line.startswith('#'):
                continue
            row = next(csv.reader(io.StringIO(line)))
            sym = row[1]
            items[sym] = dict(id=int(row[0]), name=nfc(row[2]), price=int(row[5]), pocket=int(row[4]))
            if nfc(row[2]) in by_name:
                raise SystemExit('Nombre de objeto duplicado en proposed_items.txt: ' + row[2])
            by_name[nfc(row[2])] = sym
    return items, by_name


def load_locs():
    keys = json.load(open(LOCKEYS, encoding='utf-8'))
    order = [k['key'] for k in keys]
    by_name = {}
    for k in keys:
        base = nfc(re.sub(r'\s*\(.*\)\s*$', '', k['name'])).strip()
        if base in by_name:
            raise SystemExit('Nombre base de ubicacion duplicado: ' + base)
        by_name[base] = k['key']
    return order, by_name, {k['key']: k['name'] for k in keys}


class Resolver:
    def __init__(self, by_name):
        self.by_name = by_name
        self.unresolved = []

    def sym(self, name, where=''):
        name = nfc(name).strip()
        m = re.match(r'^MT(\d{2,3})\b', name)
        if m:
            return 'TM%02d' % int(m.group(1))
        if name in self.by_name:
            return self.by_name[name]
        self.unresolved.append((name, where))
        return '[?%s]' % name


# --------------------------------------------------------------------------------------------- parseo del Vol. 9
def section(lines, start_pat, end_pat):
    s = next(i for i, l in enumerate(lines) if re.match(start_pat, l))
    e = next(i for i in range(s + 1, len(lines)) if re.match(end_pat, lines[i]))
    return lines[s:e]


def parse_chapter5(lines, res, loc_by_name):
    """-> (rows_by_loc OrderedDict[LOC_KEY] -> [row dict], intro dict[LOC_KEY] -> contadores del encabezado de acto)."""
    block = section(lines, r'^# Capítulo 5', r'^# Capítulo 6')
    rows, intro = OrderedDict(), {}
    cur, mode = None, None
    for l in block:
        m = re.match(r'^### (.+?)(?:\\\*)?\s*$', l)
        if m:
            name = nfc(m.group(1)).strip()
            if name not in loc_by_name:
                raise SystemExit('Cap. 5: ubicacion desconocida «%s»' % name)
            cur = loc_by_name[name]
            rows[cur] = []
            mode = None
            continue
        if l.startswith('## '):
            cur, mode = None, None
            continue
        if not l.startswith('|'):
            mode = None
            continue
        cells = split_row(l)
        if cells and cells[0] == '#' and 'Objeto/MT' in cells[1]:
            mode = 'items'
            continue
        if cells and cells[0].startswith('Ubicación') and 'Filas' in cells:
            mode = 'intro'
            continue
        if set(''.join(cells)) <= set('-: '):
            continue
        if mode == 'intro':
            name = nfc(cells[0].replace('\\*', '')).strip()
            intro[loc_by_name[name]] = dict(rows=int(cells[2]), mt=int(cells[3]), mapa=int(cells[4]),
                                            pnj=int(cells[5]), tienda=int(cells[6]))
        elif mode == 'items' and cur:
            if len(cells) != 5:
                raise SystemExit('Cap. 5 fila con %d celdas en %s: %s' % (len(cells), cur, l[:80]))
            n, obj, meth, zone, note = cells
            q = 1
            mq = re.match(r'^(.*?)\s*×\s*(\d+)$', obj)
            if mq:
                obj, q = mq.group(1), int(mq.group(2))
            rows[cur].append(dict(n=int(n), item_name=nfc(obj).strip(), qty=q, method=meth.strip(),
                                  zone=plain(zone), note=plain(note), loc=cur,
                                  sym=res.sym(obj, 'Cap.5 %s #%s' % (cur, n))))
    return rows, intro


def to_zone_field(zone):
    """Zone sin comas (maxsplit=4 en ItemN)."""
    return re.sub(r'\s*,\s*', ' · ', zone)


def parse_marts(lines, res, loc_by_name):
    """3.2 -> {medallas: [(sym, precio)]}; 3.2.1 -> [LOC_KEY] con Poke Mart estandar."""
    blk = section(lines, r'^## 3\.2 ', r'^### 3\.2\.1')
    marts = OrderedDict()
    for l in blk:
        if not l.startswith('|'):
            continue
        c = split_row(l)
        if len(c) != 2 or not c[0].isdigit():
            continue
        lst = []
        for nm, pr in re.findall(r'([^(),]+?)\s*\(([\d\s]+)\)', c[1]):
            lst.append((res.sym(nm, 'Mart %s' % c[0]), int(re.sub(r'\D', '', pr))))
        marts[int(c[0])] = lst
    blk = section(lines, r'^### 3\.2\.1', r'^## 3\.3 ')
    locs = []
    for l in blk:
        if not l.startswith('|'):
            continue
        c = split_row(l)
        if len(c) == 5 and c[2] == 'Sí':
            locs.append(loc_by_name[nfc(c[0].replace('\\*', '')).strip()])
    return marts, locs


def slugify(name):
    s = re.sub(r'\s*\(.*?\)', '', name)
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    words = [w for w in re.split(r'[^A-Za-z0-9]+', s.upper()) if w and w not in ('DE', 'DEL', 'LA', 'EL')]
    return '_'.join(words)


def parse_special_shops(lines, res, loc_by_name):
    blk = section(lines, r'^## 3\.3 ', r'^## 3\.4 ')
    shops, cur, mode = [], None, None
    for l in blk:
        m = re.match(r'^### (.+?) — (.+?)(?:\\\*)?\s*$', l)
        if m:
            cur = dict(name=nfc(m.group(1)).strip(), loc=loc_by_name[nfc(m.group(2)).strip()], desc='', req='',
                       items=[], groups=[])
            cur['slug'] = 'SHOP_' + slugify(cur['name'])
            shops.append(cur)
            mode = None
            continue
        if cur is None:
            continue
        if l.strip() and not l.startswith('|') and not l.startswith('<!--') and not cur['desc']:
            body = plain(l.replace('**Disponible:**', '\u0001'))
            a, _, b = body.partition('\u0001')
            cur['desc'], cur['req'] = a.strip(), b.strip()
            continue
        if not l.startswith('|'):
            continue
        c = split_row(l)
        if c and c[0] == 'Objetos':
            mode = 'items'
            continue
        if mode != 'items' or set(''.join(c)) <= set('-: '):
            continue
        cell, price, stock, note = c
        cell = plain(cell) if cell != '—' else ''
        mc = re.match(r'^(\d+) bayas:\s*(.*)$', cell)
        expect = None
        if mc:
            expect, cell = int(mc.group(1)), mc.group(2)
        names = [x.strip() for x in cell.split(', ')]
        if expect is not None and len(names) != expect:
            raise SystemExit('%s: la celda anuncia %d bayas y trae %d' % (cur['name'], expect, len(names)))
        price = int(re.sub(r'\D', '', price))
        unique = nfc(stock).strip().lower().startswith('stock')
        for nm in names:
            sym = res.sym(nm, 'Tienda %s' % cur['name'])
            cur['items'].append(dict(sym=sym, price=price, unique=unique, note=plain(note), name=nm))
    return shops


def parse_missions(lines, res, loc_by_name):
    blk = section(lines, r'^## 3\.4 ', r'^### 3\.4\.1')
    out = []
    for l in blk:
        if not l.startswith('|'):
            continue
        c = split_row(l)
        if len(c) != 7 or not c[0].isdigit():
            continue
        n, act, tipo, title, req, reward, where = c
        reward_item = reward.split(' + ')[0].strip()
        out.append(dict(n=int(n), act=act.strip(), tipo=plain(tipo).upper(), title=plain(title), req=plain(req),
                        reward=plain(reward), sym=res.sym(reward_item, 'Mision %s' % n),
                        loc=loc_by_name[nfc(where.replace('\\*', '')).strip()]))
    return out


# --------------------------------------------------------------------------------------------- construccion
class Data:
    pass


def load_all():
    d = Data()
    d.items, by_name = load_items()
    d.order, d.loc_by_name, d.loc_names = load_locs()
    d.res = Resolver(by_name)
    lines = read_lines(MD9)
    d.rows, d.intro = parse_chapter5(lines, d.res, d.loc_by_name)
    d.marts, d.mart_locs = parse_marts(lines, d.res, d.loc_by_name)
    d.shops = parse_special_shops(lines, d.res, d.loc_by_name)
    d.missions = parse_missions(lines, d.res, d.loc_by_name)
    # Mision -> fila del Cap. 5
    d.mission_row = {}
    for loc in d.order:
        for r in d.rows.get(loc, []):
            m = re.search(r'Misión n\.º (\d+) de Pía «([^»]+)»', r['zone'] + ' ' + r['note'])
            if m:
                d.mission_row.setdefault(int(m.group(1)), []).append((r, nfc(m.group(2))))
    return d


def mission_captured(m):
    if m['tipo'] != 'HITO':
        return 0
    mm = re.search(r'(\d+)\s+especies', m['req'])
    return int(mm.group(1)) if mm else 0


def build_texts(d):
    # ---------------- rem_location_items.txt
    L = ['# Pokémon REM - rem_location_items.txt (generado por tools/rebalance/phase1/build_items_shops.py; no editar a mano).',
         '# Formato INI de SPEC.md 2.3: una sección [LOC_KEY] por ubicación (64) y una línea por fila del Vol. 9, Cap. 5 (775 filas).',
         '# ItemN = ITEM_ID,Qty,Method,Zone,Note   (parseo con maxsplit=4: Zone no lleva comas; Note es texto libre y puede llevarlas).',
         '# ITEM_ID = símbolo PBS de proposed_items.txt (las MT son TM01..TM100). Method: B Poké Ball visible, H oculto, C cofre,',
         '# N regalo de PNJ, E evento/misión, J botín de jefe o líder, P misión de Pía, S tienda de stock único. Note vacía = sin nota.',
         '# Las comas de Zone se escriben « · » y se omite la marca de dato provisional (*) del volumen impreso.',
         '']
    for loc in d.order:
        rows = d.rows.get(loc, [])
        L.append('# %s - %d filas' % (d.loc_names[loc], len(rows)))
        L.append('[%s]' % loc)
        if not rows:
            L.append('# (sin objetos en esta ubicación)')
        for i, r in enumerate(rows, 1):
            L.append('Item%d = %s,%d,%s,%s,%s' % (i, r['sym'], r['qty'], r['method'], to_zone_field(r['zone']), r['note']))
        L.append('')
    items_txt = '\r\n'.join(L).rstrip('\r\n') + '\r\n'

    # ---------------- rem_shops.txt
    S = ['# Pokémon REM - rem_shops.txt (generado por tools/rebalance/phase1/build_items_shops.py; no editar a mano).',
         '# Formato INI de SPEC.md 2.4. [MART_n_MEDALS] (n=0..8) = Poké Mart estándar ACUMULATIVO: cada sección lista solo los objetos NUEVOS',
         '# a ese nivel (stock con n medallas = unión de 0..n). ItemN = ITEM_ID,Precio. [SHOP_*] = 8 tiendas especiales (Vol. 9, 3.3).',
         '# [PIA_MISSIONS]: MissionN = CAPTURADAS,ITEM_ID,Qty,Título,Nota (CAPTURADAS=0 en los encargos de campo, que no son hitos de Pokédex).',
         '# Claves extra: Locations (marts), UniqueItems y ItemNote = ITEM_ID,nota (tiendas), MissionInfoN = ACTO,TIPO,LOC_KEY,Requisito.',
         '# En el Casino de Azabache el precio es el de la columna «Precio de compra» del Vol. 9; las fichas reales van en ItemNote.',
         '']
    mart_locs = [k for k in d.order if k in set(d.mart_locs)]
    for n in sorted(d.marts):
        S.append('[MART_%d_MEDALS]' % n)
        S.append('Name = Poké Mart (%d medalla%s)' % (n, '' if n == 1 else 's'))
        S.append('Medals = %d' % n)
        S.append('Cumulative = yes')
        for i, (sym, price) in enumerate(d.marts[n], 1):
            S.append('Item%d = %s,%d' % (i, sym, price))
        S.append('Locations = ' + ';'.join(mart_locs))
        S.append('')
    for sh in d.shops:
        S.append('[%s]' % sh['slug'])
        S.append('Name = %s' % sh['name'])
        S.append('Location = %s' % sh['loc'])
        S.append('Description = %s' % sh['desc'])
        S.append('Requirement = %s' % sh['req'])
        for i, it in enumerate(sh['items'], 1):
            S.append('Item%d = %s,%d' % (i, it['sym'], it['price']))
        uniq = [it['sym'] for it in sh['items'] if it['unique']]
        if uniq:
            S.append('UniqueItems = ' + ';'.join(uniq))
        for it in sh['items']:
            if it['note']:
                S.append('ItemNote = %s,%s' % (it['sym'], it['note']))
        S.append('')
    S.append('[PIA_MISSIONS]')
    for m in d.missions:
        cand = d.mission_row.get(m['n'], [])
        note = cand[0][0]['note'] if len(cand) == 1 else ''
        qty = cand[0][0]['qty'] if len(cand) == 1 else 1
        S.append('Mission%d = %d,%s,%d,%s,%s' % (m['n'], mission_captured(m), m['sym'], qty, m['title'], note))
    for m in d.missions:
        S.append('MissionInfo%d = %s,%s,%s,%s' % (m['n'], m['act'], m['tipo'], m['loc'], m['req']))
    S.append('')
    shops_txt = '\r\n'.join(S).rstrip('\r\n') + '\r\n'
    return items_txt, shops_txt


def write_utf8_bom_crlf(path, text):
    assert '\n' not in text.replace('\r\n', '')
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(text)


# --------------------------------------------------------------------------------------------- validacion
class Checker:
    def __init__(self):
        self.fail = 0

    def ok(self, name, cond, detail=''):
        if not cond:
            self.fail += 1
        print(('PASS  ' if cond else 'FAIL  ') + name + ('  [%s]' % detail if detail else ''))

    def info(self, text):
        print('INFO  ' + text)


def parse_vol6_tables(loc_by_name):
    """Tablas de objetos de las fichas del Vol. 6 -> {LOC_KEY: [(n, item, qty, method, zone, note)]}."""
    lines = read_lines(MD6)
    out, cur, mode = {}, None, False
    for l in lines:
        m = re.match(r'^### (.+?)\s*$', l)
        if m:
            nm = nfc(re.sub(r'\s*\(.*\)\s*$', '', m.group(1))).strip()
            cur = loc_by_name.get(nm)
            mode = False
            continue
        if not l.startswith('|'):
            mode = False
            continue
        c = split_row(l)
        if c and c[0] == '#' and len(c) == 5 and 'Objeto' in c[1]:
            mode = True
            out.setdefault(cur, [])
            continue
        if mode and cur and len(c) == 5 and c[0].isdigit():
            obj = c[1]
            q = 1
            mq = re.match(r'^(.*?)\s*×\s*(\d+)$', obj)
            if mq:
                obj, q = mq.group(1), int(mq.group(2))
            mm = re.search(r'\((\w)\)\s*$', c[2])
            out[cur].append((int(c[0]), nfc(obj).strip(), q, mm.group(1) if mm else c[2], plain(c[3]), plain(c[4])))
    return out


def run_check(json_path=None):
    ck = Checker()
    d = load_all()
    print('== Fuentes ==')
    ck.ok('todos los nombres de objeto del Vol. 9 se resuelven a un símbolo PBS', not d.res.unresolved, str(d.res.unresolved[:5]))
    items_txt, shops_txt = build_texts(d)

    print('== Ficheros ==')
    for path in (OUT_ITEMS, OUT_SHOPS):
        raw = open(path, 'rb').read() if os.path.exists(path) else b''
        rel = os.path.relpath(path, ROOT)
        ck.ok('%s existe, BOM UTF-8 y CRLF' % rel, raw.startswith(b'\xef\xbb\xbf') and b'\n' not in raw.replace(b'\r\n', b''))
    ck.ok('rem_location_items.txt == salida reproducible del generador',
          os.path.exists(OUT_ITEMS) and open(OUT_ITEMS, 'rb').read() == b'\xef\xbb\xbf' + items_txt.encode('utf-8'))
    ck.ok('rem_shops.txt == salida reproducible del generador',
          os.path.exists(OUT_SHOPS) and open(OUT_SHOPS, 'rb').read() == b'\xef\xbb\xbf' + shops_txt.encode('utf-8'))
    secs_i, warn_i = remini_ref.parse(OUT_ITEMS)
    secs_s, warn_s = remini_ref.parse(OUT_SHOPS)
    ck.ok('remini_ref.parse(rem_location_items.txt) sin warnings', not warn_i, str(warn_i[:3]))
    ck.ok('remini_ref.parse(rem_shops.txt) sin warnings', not warn_s, str(warn_s[:3]))

    # ------------------------------------------------------------------ rem_location_items.txt
    print('== rem_location_items.txt ==')
    ck.ok('64 secciones', len(secs_i) == 64, str(len(secs_i)))
    ck.ok('las secciones son exactamente las 64 claves de location_keys.json y en su orden',
          [s['key'] for s in secs_i] == d.order)
    parsed = {}      # LOC_KEY -> [(sym, qty, method, zone, note)]
    bad_fmt, bad_seq = [], []
    for s in secs_i:
        lst = []
        keys = [(k, v) for _, k, v in s['items']]
        for idx, (k, v) in enumerate(keys, 1):
            if k != 'item%d' % idx:
                bad_seq.append((s['key'], k, idx))
                continue
            f = v.split(',', 4)
            if len(f) != 5 or not f[1].isdigit() or int(f[1]) < 1 or f[2] not in METHODS or not f[3]:
                bad_fmt.append((s['key'], idx, v[:60]))
                continue
            lst.append((f[0], int(f[1]), f[2], f[3], f[4]))
        parsed[s['key']] = lst
    ck.ok('claves Item1..ItemN consecutivas en cada sección', not bad_seq, str(bad_seq[:3]))
    ck.ok('cada línea tiene 5 campos válidos (Qty entero >= 1, Method en B/H/C/N/E/J/P/S, Zone no vacía)', not bad_fmt, str(bad_fmt[:3]))
    allrows = [(k,) + r for k, lst in parsed.items() for r in lst]
    ck.ok('%d filas exactas' % EXPECTED_ROWS, len(allrows) == EXPECTED_ROWS, str(len(allrows)))
    ck.ok('ningún ITEM_ID con marca de no resuelto [?...]', not any(r[1].startswith('[?') for r in allrows))
    ck.ok('todo ITEM_ID existe en proposed_items.txt', all(r[1] in d.items for r in allrows),
          str([r[1] for r in allrows if r[1] not in d.items][:5]))
    tms = Counter(r[1] for r in allrows if re.match(r'^TM\d+$', r[1]))
    want_tms = ['TM%02d' % i for i in range(1, 101)]
    ck.ok('100 MT (TM01..TM100) colocadas al menos una vez', all(tms[t] >= 1 for t in want_tms), 'faltan %s' % [t for t in want_tms if not tms[t]])
    ck.ok('cada MT exactamente una vez (objeto Tier 1)', all(tms[t] == 1 for t in want_tms), str([t for t in tms if tms[t] != 1]))
    present = set(r[1] for r in allrows)
    ck.info('objetos distintos colocados en el mapa: %d de %d (sin colocar: %s)' % (
        len(present), len(d.items), sorted(set(d.items) - present)[:10]))
    m_cnt = Counter(r[3] for r in allrows)
    ck.info('filas por método: ' + ', '.join('%s=%d' % (k, m_cnt[k]) for k in METHODS) + ' | copias en mapa (B+H+C con Qty)=%d' %
            sum(r[2] for r in allrows if r[3] in 'BHC'))
    mt_m = Counter(r[3] for r in allrows if r[1] in tms)
    ck.info('MT por método (tiendas/misiones incluidas): ' + ', '.join('%s=%d' % (k, mt_m[k]) for k in METHODS if mt_m[k]))
    ck.ok('ninguna Zone contiene comas ni saltos de línea', all(',' not in r[4] and '\n' not in r[4] for r in allrows))
    ck.ok('ninguna Note contiene saltos de línea ni la marca \\*', all('\n' not in r[5] and '\\' not in r[5] for r in allrows))
    # cuadre con el md (Cap. 5) y con las cabeceras de acto
    mism = []
    for loc in d.order:
        exp = [(r['sym'], r['qty'], r['method'], to_zone_field(r['zone']), r['note']) for r in d.rows[loc]]
        if exp != parsed.get(loc):
            mism.append(loc)
    ck.ok('cuadre fila a fila con el Cap. 5 del Vol. 9 (64 ubicaciones)', not mism, str(mism[:5]))
    bad_intro = []
    for loc in d.order:
        rws = d.rows[loc]
        got = dict(rows=len(rws), mt=sum(1 for r in rws if re.match(r'^MT\d', r['item_name'])),
                   mapa=sum(r['qty'] for r in rws if r['method'] in 'BHC'),
                   pnj=sum(r['qty'] for r in rws if r['method'] in 'NEJP'), tienda=sum(r['qty'] for r in rws if r['method'] == 'S'))
        if d.intro.get(loc) != got:
            bad_intro.append((loc, d.intro.get(loc), got))
    ck.ok('recuentos de cada ubicación (filas / MT / mapa / PNJ-misión / tienda única) = tablas de cabecera de acto',
          not bad_intro and len(d.intro) == 64, str(bad_intro[:2]))
    tot = dict(mapa=sum(r[2] for r in allrows if r[3] in 'BHC'), pnj=sum(r[2] for r in allrows if r[3] in 'NEJP'),
               tienda=sum(r[2] for r in allrows if r[3] == 'S'))
    ck.ok('resumen ejecutivo: mapa 684 · PNJ/misión 105 · tienda única 13', tot == dict(mapa=684, pnj=105, tienda=13), str(tot))
    # cuadre con el Vol. 6
    v6 = parse_vol6_tables(d.loc_by_name)
    ck.ok('el Vol. 6 tiene la tabla de objetos de las 64 fichas', len([k for k in v6 if k]) == 64, str(len(v6)))
    mism6 = []
    for loc in d.order:
        a = [(r['n'], r['item_name'], r['qty'], r['method'], r['zone'], r['note']) for r in d.rows[loc]]
        if a != v6.get(loc):
            mism6.append(loc)
    ck.ok('cuadre fila a fila con las tablas del Vol. 6 (misma fuente de las fichas)', not mism6, str(mism6[:5]))
    # cuadre con el JSON de trabajo
    json_path = json_path or DEFAULT_JSON
    if os.path.exists(json_path):
        js = json.load(open(json_path, encoding='utf-8'))
        mism_js, n_js = [], 0
        for name, v in js.items():
            loc = d.loc_by_name[nfc(name)]
            n_js += len(v['rows'])
            exp = [(r['sym'], r['qty'], r['method'], to_zone_field(r['zone_plain']), r['note_plain']) for r in v['rows']]
            if exp != parsed.get(loc):
                mism_js.append(loc)
        ck.ok('cuadre con vol9_by_loc.json (%d ubicaciones, %d filas)' % (len(js), n_js), not mism_js and n_js == EXPECTED_ROWS, str(mism_js[:5]))
        shops_js = {d.loc_by_name[nfc(n)]: v['shops'] for n, v in js.items() if v['shops']}
        exp_locs = set(d.mart_locs) | {sh['loc'] for sh in d.shops}
        ck.ok('las ubicaciones con tienda del JSON (Poké Mart + especiales) = las del Vol. 9 (3.2.1 y 3.3)',
              set(shops_js) == exp_locs, 'json-md=%s md-json=%s' % (sorted(set(shops_js) - exp_locs), sorted(exp_locs - set(shops_js))))
    else:
        ck.info('SKIP cuadre con vol9_by_loc.json (no existe %s)' % json_path)

    # ------------------------------------------------------------------ rem_shops.txt
    print('== rem_shops.txt ==')
    by = OrderedDict((s['key'], s) for s in secs_s)
    marts = [k for k in by if re.match(r'^MART_\d_MEDALS$', k)]
    specials = [k for k in by if k.startswith('SHOP_')]
    ck.ok('9 marts [MART_0_MEDALS]..[MART_8_MEDALS]', marts == ['MART_%d_MEDALS' % i for i in range(9)], str(marts))
    ck.ok('8 tiendas especiales', len(specials) == EXPECTED_SHOPS, str(specials))
    ck.ok('1 sección [PIA_MISSIONS]', 'PIA_MISSIONS' in by and len(by) == 9 + 8 + 1, str(len(by)))
    ck.ok('slugs de tienda únicos', len(set(specials)) == len(specials))

    def pairs(sec, prefix='item'):
        vals = {k: v for _, k, v in sec['items']}
        out, n = [], 1
        while '%s%d' % (prefix, n) in vals:
            out.append(vals['%s%d' % (prefix, n)])
            n += 1
        return out

    new_by_n, cum_err = {}, []
    seen = set()
    for n in range(9):
        sec = by['MART_%d_MEDALS' % n]
        ck_ok = sec.get('medals') == str(n) and sec.get('cumulative') == 'yes' and sec.get('name').startswith('Poké Mart (')
        if not ck_ok:
            cum_err.append(n)
        new = []
        for v in pairs(sec):
            sym, _, price = v.partition(',')
            new.append((sym, int(price)))
            if sym in seen:
                cum_err.append(('repetido', n, sym))
            seen.add(sym)
        new_by_n[n] = new
    ck.ok('cada mart: Medals=n, Cumulative=yes, Name y objetos sin repetir entre niveles', not cum_err, str(cum_err[:3]))
    acc, stock = [], {}
    for n in range(9):
        acc = acc + new_by_n[n]
        stock[n] = list(acc)
    ck.ok('los marts solo listan objetos NUEVOS por nivel (sin objetos repetidos)', len(seen) == sum(len(v) for v in new_by_n.values()))
    # expectativa independiente: tabla 3.2 del md
    exp_acc, mism_m = [], []
    for n in range(9):
        exp_acc = exp_acc + d.marts[n]
        if stock[n] != exp_acc:
            mism_m.append(n)
    ck.ok('stock acumulado de n medallas = unión de 0..n = Vol. 9 §3.2 (n=0..8)', not mism_m, str(mism_m))
    sizes = [len(stock[n]) for n in range(9)]
    ck.info('tamaño del mostrador acumulado por medallas: %s' % sizes)
    # expectativa de la frase del Vol. 6 (0 medallas y 8 medallas)
    zero = ['POKEBALL', 'POTION', 'ANTIDOTE', 'PARLYZHEAL', 'AWAKENING', 'RARECANDY']
    eight = ['MAXREVIVE', 'MAXETHER', 'MAXELIXIR']
    ck.ok('0 medallas = Poké Ball, Poción, Antídoto, Antiparalizante, Despertar, Caramelo Raro (frase del Vol. 6)',
          sorted(s for s, _ in new_by_n[0]) == sorted(zero))
    ck.ok('8 medallas añade Revivir Máximo, Éter Máximo, Elixir Máximo (frase del Vol. 6)',
          sorted(s for s, _ in new_by_n[8]) == sorted(eight))
    badp = [(s, p, d.items[s]['price']) for n in range(9) for s, p in new_by_n[n] if s in d.items and d.items[s]['price'] != p]
    ck.ok('precio de mart = precio base de proposed_items.txt', not badp, str(badp[:3]))
    ck.ok('Locations de los marts = 14 poblaciones con Poké Mart (3.2.1)',
          all(by['MART_%d_MEDALS' % n].get('locations').split(';') == [k for k in d.order if k in set(d.mart_locs)]
              for n in range(9)) and len(d.mart_locs) == 14, str(len(d.mart_locs)))
    # tiendas especiales
    unique_by_loc = defaultdict(list)
    shop_summary = []
    mism_sh = []
    for sh in d.shops:
        sec = by.get(sh['slug'])
        if sec is None:
            mism_sh.append(('falta', sh['slug']))
            continue
        got = [tuple([v.split(',')[0], int(v.split(',')[1])]) for v in pairs(sec)]
        exp = [(it['sym'], it['price']) for it in sh['items']]
        if got != exp:
            mism_sh.append(('items', sh['slug']))
        if (sec.get('name'), sec.get('location'), sec.get('description'), sec.get('requirement')) != (sh['name'], sh['loc'], sh['desc'], sh['req']):
            mism_sh.append(('campos', sh['slug']))
        if sh['loc'] not in d.order:
            mism_sh.append(('loc', sh['slug']))
        for sym in (sec.get('uniqueitems') or '').split(';'):
            if sym:
                unique_by_loc[sh['loc']].append(sym)
        shop_summary.append('%s=%d' % (sh['slug'][5:], len(got)))
    ck.ok('8 tiendas = tablas de 3.3 (objetos, precios exactos, Name/Location/Description/Requirement; Location es LOC_KEY válida)',
          not mism_sh and len(d.shops) == EXPECTED_SHOPS, str(mism_sh[:3]))
    ck.info('objetos por tienda especial: ' + ', '.join(shop_summary))
    ck.ok('todos los ITEM_ID de tiendas existen en proposed_items.txt',
          all(v.split(',')[0] in d.items for k in specials for v in pairs(by[k])) and all(s in d.items for s, _ in stock[8]))
    ck.ok('ningún precio de tienda vacío o no numérico', all(re.match(r'^[A-Z0-9_]+,\d+$', v) for k in specials + marts for v in pairs(by[k])))
    # stock unico <-> filas S del Cap. 5
    s_rows = defaultdict(list)
    for loc in d.order:
        for r in d.rows[loc]:
            if r['method'] == 'S':
                s_rows[loc].append(r['sym'])
    ck.ok('UniqueItems de las tiendas = filas de método S del Cap. 5 (13), misma ubicación y mismos objetos',
          {k: sorted(v) for k, v in unique_by_loc.items()} == {k: sorted(v) for k, v in s_rows.items()} and
          sum(len(v) for v in s_rows.values()) == 13,
          'tiendas=%s caps=%s' % (dict(unique_by_loc), dict(s_rows)))
    shop_tms = sorted(s for v in unique_by_loc.values() for s in v if re.match(r'^TM\d+$', s))
    ck.info('MT que se venden en tiendas (stock único, y contadas igual en las 775 filas con método S): %d -> %s' % (len(shop_tms), shop_tms))
    # misiones
    msec = by.get('PIA_MISSIONS')
    miss = {}
    bad_m = []
    for _, k, v in msec['items']:
        mm = re.match(r'^mission(\d+)$', k)
        if mm:
            f = v.split(',', 4)
            if len(f) != 5 or not f[0].isdigit() or f[1] not in d.items or not f[2].isdigit():
                bad_m.append(k)
            else:
                miss[int(mm.group(1))] = f
    ck.ok('29 misiones Mission1..Mission29 con 5 campos válidos (ITEM_ID existe, Título sin comas)',
          sorted(miss) == list(range(1, 30)) and not bad_m, str(bad_m[:3]))
    mism_ms = []
    for m in d.missions:
        f = miss.get(m['n'])
        cand = d.mission_row.get(m['n'], [])
        if not f or len(cand) != 1:
            mism_ms.append((m['n'], 'sin fila única en Cap. 5'))
            continue
        row, title = cand[0]
        if (f[1], int(f[2]), f[3]) != (m['sym'], row['qty'], m['title']) or row['sym'] != m['sym'] or title != m['title']:
            mism_ms.append((m['n'], f[:4], m['sym'], title))
        if f[4] != row['note']:
            mism_ms.append((m['n'], 'nota'))
    ck.ok('misiones = tabla 3.4 y filas del Cap. 5 (objeto, Qty, título, nota)', not mism_ms and len(d.missions) == EXPECTED_MISSIONS, str(mism_ms[:3]))
    hitos = [int(miss[m['n']][0]) for m in d.missions if m['tipo'] == 'HITO']
    ck.ok('CAPTURADAS de los 19 hitos crecientes (5..721) y 0 en los 10 encargos de campo',
          hitos == sorted(hitos) and len(hitos) == 19 and hitos[0] == 5 and hitos[-1] == 721 and
          sum(1 for m in d.missions if m['tipo'] == 'CAMPO' and miss[m['n']][0] == '0') == 10, str(hitos))
    ck.ok('MissionInfo1..29 presentes con LOC_KEY válida',
          all(len(msec.get('missioninfo%d' % n).split(',', 3)) == 4 and msec.get('missioninfo%d' % n).split(',')[2] in d.order for n in range(1, 30)))
    mt_in_missions = sorted(miss[n][1] for n in miss if re.match(r'^TM\d+$', miss[n][1]))
    ck.info('MT entregadas como misión de Pía: %s' % mt_in_missions)
    ck.info('resumen: %d filas, %d secciones de ubicación, %d marts (%d objetos), %d tiendas especiales (%d líneas de objeto), %d misiones' % (
        len(allrows), len(secs_i), len(marts), len(stock[8]), len(specials), sum(len(pairs(by[k])) for k in specials), len(miss)))
    print('\n%s (%d fallos)' % ('VALIDACIÓN OK' if not ck.fail else 'VALIDACIÓN CON FALLOS', ck.fail))
    return ck.fail


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true', help='solo valida los ficheros existentes (no escribe)')
    ap.add_argument('--json', default=None, help='ruta de vol9_by_loc.json para el cuadre extra (opcional)')
    a = ap.parse_args()
    if not a.check:
        d = load_all()
        if d.res.unresolved:
            print('AVISO: nombres sin resolver (se escriben como [?nombre]):', d.res.unresolved)
        items_txt, shops_txt = build_texts(d)
        write_utf8_bom_crlf(OUT_ITEMS, items_txt)
        write_utf8_bom_crlf(OUT_SHOPS, shops_txt)
        print('Escritos:', os.path.relpath(OUT_ITEMS, ROOT), os.path.relpath(OUT_SHOPS, ROOT))
    sys.exit(1 if run_check(a.json) else 0)


if __name__ == '__main__':
    main()
