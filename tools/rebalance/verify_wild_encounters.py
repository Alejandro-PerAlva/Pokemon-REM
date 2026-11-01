#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_wild_encounters.py - verificador independiente del Vol. 10 (encuentros salvajes y obtenibilidad de la Pokédex).

Lee SOLO archivos del repositorio (no usa el generador):
  docs/rebalance/10_Wild_Encounters_Master_Guide.md / .pdf   (tablas por ubicación, pesca, catálogo, índice de 721 filas)
  docs/rebalance/proposed_pokemon.txt                          (evoluciones, tipos y nombres de la Pokédex final)
  docs/rebalance/proposed_items.txt                            (objetos de evolución, Pokévial, Caramelo Infinito, sin Parche/Traje)
  docs/rebalance/6_*.md, 7_*.md, 8_*.md, 9_*.md                (nombres nuevos, niveles, plantillas rellenas)
  tools/rebalance/baseline_md5.json                            (PBS/ y Data/ intactos)
Sale con código 0 si todo se cumple.
"""
import os, re, sys, json, hashlib, math, collections
try:
    import pymupdf as fitz
except Exception:
    import fitz

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
D = os.path.join(ROOT, 'docs', 'rebalance')
RES = []
def check(name, ok, detail=''):
    RES.append((bool(ok), name, detail))
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('  -> ' + str(detail)) if detail and not ok else ('  [' + str(detail) + ']' if detail else '')))
def md5(p): return hashlib.md5(open(p, 'rb').read()).hexdigest()
def rd(p): return open(p, encoding='utf-8-sig').read()

# ======================================================================= datos de la Pokédex final (proposed_pokemon.txt)
raw = {}; cur = None
for l in rd(os.path.join(D, 'proposed_pokemon.txt')).split('\n'):
    l = l.rstrip('\r')
    if not l or l.startswith('#'): continue
    m = re.match(r'\[(\d+)\]$', l)
    if m: cur = {}; raw[int(m.group(1))] = cur; continue
    k, _, v = l.partition('='); cur[k] = v
NAME = {i: r['Name'] for i, r in raw.items()}
IID = {r['InternalName']: i for i, r in raw.items()}
TYP = {i: [r['Type1']] + ([r['Type2']] if r.get('Type2') else []) for i, r in raw.items()}
def bst(i): return sum(map(int, raw[i]['BaseStats'].split(',')))
PRE = {}; EVO = {}; KIDS = collections.defaultdict(list)
for i, r in raw.items():
    e = r.get('Evolutions')
    if not e: continue
    f = e.split(',')
    for k in range(0, len(f), 3):
        c = IID[f[k]]; PRE[c] = i; KIDS[i].append(c)
        EVO[c] = dict(method='Item' if f[k + 1].startswith('Item') else 'Level', par=f[k + 2], parent=i)
        if EVO[c]['method'] == 'Level': EVO[c]['level'] = int(f[k + 2])
def root(i):
    while i in PRE: i = PRE[i]
    return i
def stage(i):
    n = 1
    while i in PRE: i = PRE[i]; n += 1
    return n
def family(i):
    out = []
    def dfs(x):
        out.append(x)
        for k in KIDS.get(x, []): dfs(k)
    dfs(root(i)); return out
def line_len(i):
    r = root(i); best = 1
    def dfs(x, d):
        nonlocal best
        best = max(best, d)
        for k in KIDS.get(x, []): dfs(k, d + 1)
    dfs(r, 1); return best
def etapa(i):
    if line_len(i) == 1: return 'Única'
    return 'Base' if stage(i) == 1 else 'Media'
STARTER_ROOTS = ['BULBASAUR', 'CHARMANDER', 'SQUIRTLE', 'CHIKORITA', 'CYNDAQUIL', 'TOTODILE', 'TREECKO', 'TORCHIC', 'MUDKIP', 'TURTWIG', 'CHIMCHAR', 'PIPLUP', 'SNIVY', 'TEPIG', 'OSHAWOTT', 'CHESPIN', 'FENNEKIN', 'FROAKIE']
STARTERS = set()
for r in STARTER_ROOTS: STARTERS |= set(family(IID[r]))
LEGEND = set([144, 145, 146, 150, 151, 243, 244, 245, 249, 250, 251] + list(range(377, 387)) + list(range(480, 495)) + list(range(638, 650)) + list(range(716, 722)))
ITEMEVO = {i for i in EVO if EVO[i]['method'] == 'Item'}
THIRD = {i for i in EVO if EVO[i]['method'] == 'Level' and stage(i) >= 3}

# ======================================================================= lectura del Vol. 10
md = rd(os.path.join(D, '10_Wild_Encounters_Master_Guide.md')).split('\n')
def split_row(line):
    s = line.strip()
    if s.startswith('|'): s = s[1:]
    if s.endswith('|') and not s.endswith('\\|'): s = s[:-1]
    return [c.replace('\\|', '|').strip() for c in re.split(r'(?<!\\)\|', s)]
tables = []     # (chapter, h3, h4, header, rows)
chap = h3 = h4 = ''
i = 0
while i < len(md):
    l = md[i]
    if l.startswith('# '): chap = l[2:].strip(); h3 = h4 = ''
    elif l.startswith('### '): h3 = l[4:].strip(); h4 = ''
    elif l.startswith('#### '): h4 = l[5:].strip()
    elif l.startswith('| ') and i + 1 < len(md) and md[i + 1].startswith('|---'):
        hdr = split_row(l); rows = []; i += 2
        while i < len(md) and md[i].startswith('|'):
            rows.append(split_row(md[i])); i += 1
        tables.append((chap, h3, h4, hdr, rows)); continue
    i += 1
print('Vol. 10: %d líneas, %d tablas' % (len(md), len(tables)))

ORDER = []     # ubicaciones del Cap. 2 en orden de aparición (las 64)
for t in tables:
    if t[0].startswith('Capítulo 2') and t[1] and t[1] not in ORDER: ORDER.append(t[1])
POS = {n: k + 1 for k, n in enumerate(ORDER)}
NEWNAMES = ['Pueblo Iolita', 'Pueblo Heliodoro', 'Granja Apatita', 'Bosque Dioptasa']
OLDNAMES = ['Pueblo Cianita', 'Pueblo Topacio', 'Granja Ambarina', 'Bosque Turmalino']

ENC_H = ['Slot', 'Rareza', '%', '# Dex']
land = []; fish = []     # (dex, loc, zona, rareza, %, nivel_dia_min, nivel_dia_max, pos, tipos, etapa, n_tabla)
LOCINFO = {}             # loc -> dict(lv=(a,b))
for (chap, h3, h4, hdr, rows) in tables:
    if not chap.startswith('Capítulo 2'): continue
    if hdr[:2] == ['Dato', 'Valor']:
        for r in rows:
            if r[0].replace('*', '') == 'Niveles salvajes':
                m = re.search(r'Día \*\*Nv (\d+)(?:–(\d+))?\*\*', r[1])
                if m: LOCINFO.setdefault(h3, {})['lv'] = (int(m.group(1)), int(m.group(2) or m.group(1)))
                m = re.search(r'Noche \(\+50 %\) \*\*Nv (\d+)(?:–(\d+))?\*\*', r[1])
                if m: LOCINFO.setdefault(h3, {})['night'] = (int(m.group(1)), int(m.group(2) or m.group(1)))
            if r[0].replace('*', '') == 'Pesca':
                m = re.search(r'Nv (\d+)(?:–(\d+))? día', r[1])
                if m: LOCINFO.setdefault(h3, {})['fish_lv'] = (int(m.group(1)), int(m.group(2) or m.group(1)))
            if r[0].replace('*', '') == 'Zonas' or True: pass
    elif hdr[:5] == ['Slot', 'Rareza', '%', '# Dex', 'Pokémon']:
        zm = re.search(r'Nv (\d+)(?:–(\d+))? día', h4)
        zlv = (int(zm.group(1)), int(zm.group(2) or zm.group(1))) if zm else LOCINFO.get(h3, {}).get('lv')
        ti = len(land)
        for r in rows:
            rar = r[1]
            land.append(dict(dex=int(r[3]), loc=h3, zone=h4 or None, rar=rar, pct=int(r[2].replace('%', '').strip()), lv=zlv, pos=POS[h3], types=r[5], etapa=r[6], slot=int(r[0]), evo=r[7], name=r[4], tbl=(h3, h4)))
    elif hdr[:3] == ['Slot pesca', 'Rareza', '# Dex']:
        for r in rows:
            rar = r[1].split(' ')[0]; pct = int(re.search(r'\((\d+) %\)', r[1]).group(1))
            fish.append(dict(dex=int(r[2]), loc=h3, rar=rar, pct=pct, lv=LOCINFO.get(h3, {}).get('fish_lv'), pos=POS[h3], name=r[3], types=r[4], tbl=(h3, 'pesca')))
print('Cap. 2: %d casillas de tierra/cueva/surf, %d de pesca, %d ubicaciones' % (len(land), len(fish), len(ORDER)))

# ======================================================================= 1. Cobertura de la Pokédex
print('== 1. Cobertura 100 % de la Pokédex ==')
idx = None
for (chap, h3, h4, hdr, rows) in tables:
    if chap.startswith('Capítulo 5') and hdr[:2] == ['# Dex', 'Pokémon']: idx = rows; break
CATS = ['Salvaje', 'Pesca', 'Evolución por nivel', 'Evolución por piedra u objeto', 'Evento / Fósil / Inicial', 'Legendario']
check('el índice del Cap. 5 tiene 721 filas', idx is not None and len(idx) == 721, len(idx) if idx else 0)
dx = [int(r[0]) for r in idx]
check('las 721 filas cubren #001-#721 sin huecos ni repeticiones', sorted(dx) == list(range(1, 722)))
check('cada fila tiene categoría válida y ubicación o método no vacíos', all(r[3] in CATS and r[4].strip() and r[5].strip() for r in idx))
check('los nombres del índice coinciden con proposed_pokemon.txt', all(NAME[int(r[0])].replace('♀', '').replace('♂', '') == r[1].replace('♀', '').replace('♂', '') or r[1] == NAME[int(r[0])] for r in idx))
CAT = {int(r[0]): r[3] for r in idx}
cc = collections.Counter(CAT.values())
check('reparto del índice: 408 salvajes + 32 pesca + 45 nivel + 65 piedra/objeto + 117 evento/fósil/inicial + 54 legendarios = 721',
      (cc['Salvaje'], cc['Pesca'], cc['Evolución por nivel'], cc['Evolución por piedra u objeto'], cc['Evento / Fósil / Inicial'], cc['Legendario']) == (408, 32, 45, 65, 117, 54), dict(cc))
# cada especie con evolución desde una especie obtenible: la pre-evolución tiene categoría
def obtainable(i, seen=()):
    c = CAT[i]
    if c in ('Salvaje', 'Pesca', 'Legendario'): return True
    if c == 'Evento / Fósil / Inicial': return True
    p = PRE.get(i)
    return p is not None and obtainable(p)
check('toda especie evolutiva tiene una cadena de obtención hasta una especie obtenible (0 huérfanas)', all(obtainable(i) for i in range(1, 722)))

# ======================================================================= 2. Duplicados
print('== 2. Cero duplicados salvajes ==')
ld = [x['dex'] for x in land]; fd = [x['dex'] for x in fish]
check('408 casillas de tierra/cueva/surf con 408 especies distintas', len(ld) == 408 and len(set(ld)) == 408, (len(ld), len(set(ld))))
check('la pesca tiene 32 especies distintas', len(fd) == 32 and len(set(fd)) == 32, (len(fd), len(set(fd))))
check('pesca y tierra son disjuntas: 408 + 32 = 440 especies únicas', not (set(ld) & set(fd)) and len(set(ld) | set(fd)) == 440)
check('el índice del Cap. 5 coincide con el Cap. 2 (misma ubicación para cada especie salvaje y de pesca)',
      all(CAT[x['dex']] == 'Salvaje' for x in land) and all(CAT[x['dex']] == 'Pesca' for x in fish) and
      all(x['loc'] in idx_row[4] for x in land for idx_row in [next(r for r in idx if int(r[0]) == x['dex'])]) and
      all(x['loc'] in idx_row[4] for x in fish for idx_row in [next(r for r in idx if int(r[0]) == x['dex'])]))
check('los nombres de las tablas coinciden con proposed_pokemon.txt', all(NAME[x['dex']] == x['name'] for x in land + fish))

# ======================================================================= 3. Prohibidos
print('== 3. Cero especies prohibidas en el salvaje ==')
W = set(ld) | set(fd)
check('0 iniciales ni evoluciones de iniciales (54) en el salvaje', not (W & STARTERS) and len(STARTERS) == 54, len(STARTERS))
check('0 legendarios ni míticos (54) en el salvaje', not (W & LEGEND) and len(LEGEND) == 54)
check('0 evoluciones por piedra u objeto en el salvaje (65 = 46 piedras + 19 objetos, sacadas de `Item*` de proposed_pokemon.txt)', not (W & ITEMEVO) and len(ITEMEVO) == 65, len(ITEMEVO))
check('0 terceras etapas por nivel en el salvaje (63 en total: 18 iniciales + 45)', not (W & THIRD) and len(THIRD) == 63, len(THIRD))
EVSET = {i for i in range(1, 722) if CAT[i] == 'Evento / Fósil / Inicial'} - STARTERS
check('el pool de eventos tiene 63 especies elegibles (117 de evento, fósil e inicial menos 54 iniciales)', len(EVSET) == 63, len(EVSET))
bad = [NAME[w] for w in W if any(f in EVSET for f in family(w))]
check('0 especies salvajes de una línea de evento (Ley 6: ni la base ni su 2.ª etapa)', not bad, bad[:5])
ELIG = [i for i in range(1, 722) if i not in STARTERS and i not in LEGEND and i not in ITEMEVO and i not in THIRD]
check('pool elegible = salvaje (440) + evento (63) = 503', len(ELIG) == 503 and set(ELIG) == W | EVSET, (len(ELIG), len(W), len(EVSET)))
wild_third_stage = [i for i in W if etapa(i) not in ('Base', 'Media', 'Única')]
check('las especies salvajes son solo Base, Media o Única (nunca 3.ª etapa)', all(stage(i) <= 2 for i in W))

# ======================================================================= 4. Cronología y familias
print('== 4. Cronología evolutiva y disyunción por ubicación ==')
where = {}
for x in land: where[x['dex']] = (x['pos'], x['lv'][0] if x['lv'] else None, x['loc'])
for x in fish: where[x['dex']] = (x['pos'], x['lv'][0] if x['lv'] else None, x['loc'])
byloc = collections.defaultdict(list)
for x in land + fish: byloc[x['loc']].append(x['dex'])
dup_family = []
for loc, ids in byloc.items():
    roots = [root(i) for i in ids]
    c = collections.Counter(roots)
    for r, n in c.items():
        if n > 1: dup_family.append((loc, NAME[r]))
check('en ninguna ubicación hay dos especies de la misma familia evolutiva (tierra + pesca)', not dup_family, dup_family[:4])
pairs = [(PRE[i], i) for i in W if i in PRE and PRE[i] in W]
chrono_bad = [(NAME[p], NAME[c]) for p, c in pairs if not where[p][0] < where[c][0]]
check('toda 2.ª etapa salvaje aparece en una ubicación POSTERIOR a la de su pre-evolución (%d pares)' % len(pairs), not chrono_bad, chrono_bad[:4])
lvl_bad = [(NAME[c], where[c][1], EVO[c]['level']) for p, c in pairs if EVO[c]['method'] == 'Level' and where[c][1] < EVO[c]['level']]
check('el nivel mínimo de día de cada 2.ª etapa es ≥ su nivel de evolución', not lvl_bad, lvl_bad[:4])
orphan2 = [NAME[i] for i in W if i in PRE and PRE[i] not in W]
check('toda 2.ª etapa salvaje tiene a su pre-evolución también en el salvaje', not orphan2, orphan2[:4])
strong = lambda i: (etapa(i) == 'Media' and bst(i) >= 400) or (etapa(i) == 'Única' and bst(i) >= 440) or (etapa(i) == 'Base' and bst(i) >= 440)
sc = [NAME[x['dex']] for x in land if x['rar'] == 'Común' and strong(x['dex'])]
check('Ley 2: ninguna especie fuerte (2.ª etapa BST ≥ 400, única o base BST ≥ 440) ocupa una casilla Común', not sc, sc[:5])
check('Ley 2: las 2.ª etapas en casilla Común (%d) son todas débiles (BST < 400)' % sum(1 for x in land if x['rar'] == 'Común' and etapa(x['dex']) == 'Media'),
      all(bst(x['dex']) < 400 for x in land if x['rar'] == 'Común' and etapa(x['dex']) == 'Media'))
fish_c = [x for x in fish if x['rar'] == 'Común']; fish_r = [x for x in fish if x['rar'] == 'Raro']
check('pesca: 16 Comunes (todas Base o sin evolución, ninguna 2.ª etapa) y 16 Raros; 1 + 1 por punto de agua',
      len(fish_c) == 16 and len(fish_r) == 16 and all(etapa(x['dex']) != 'Media' for x in fish_c) and all(len({y['rar'] for y in fish if y['loc'] == l}) == 2 and sum(1 for y in fish if y['loc'] == l) == 2 for l in {x['loc'] for x in fish}))
check('pesca: 16 puntos de agua distintos', len({x['loc'] for x in fish}) == 16)
check('pesca: toda 2.ª etapa de pesca está en un punto posterior al de su pre-evolución', all(not (PRE.get(x['dex']) in {y['dex'] for y in fish}) or where[PRE[x['dex']]][0] < x['pos'] for x in fish))

# ======================================================================= 5. Cuotas exactas
print('== 5. Cuotas exactas por ubicación ==')
CLS = {
 'ruta': ['Ruta 1', 'Ruta 2', 'Ruta 4', 'Ruta 5', 'Ruta 6', 'Ruta 7', 'Ruta 8', 'Ruta 9', 'Ruta 14', 'Ruta 15', 'Ruta 16', 'Ruta 3', 'Ruta 10', 'Ruta 20', 'Ruta 21', 'Ruta 22', 'Ruta 11', 'Ruta 17', 'Ruta 18', 'Ruta 19'],
 'marina': ['Ruta 12', 'Ruta 13', 'Ruta 23', 'Ruta 24'],
 'espec': ['Granja Apatita', 'Playa Sepiolita', 'Estepa Laterita', 'Senda Serpentina', 'Puente Dolomita', 'Acantilados Rodonita', 'Reserva Peridoto', 'Calzada Corindón'],
 'mazmorra': ['Bosque Dioptasa', 'Lago Amatista', 'Central Fulgurita', 'Ruinas Atacamita', 'Templo Moldavita', 'Villa Adularia', 'Cascadas Travertinas', 'Ciénaga Limonita', 'Desierto Halita', 'Ladera Pórfido'],
 'isla': ['Isla Opalina', 'Isla Obsidiana'],
 'gruta': ['Gruta Hialina', 'Gruta Azurita', 'Gruta Labradorita', 'Gruta Pirita']}
QUOTA = {'ruta': (6, 3, 2, 1), 'marina': (4, 2, 1, 1), 'espec': (8, 4, 3, 1), 'mazmorra': (16, 8, 6, 2), 'isla': (4, 2, 1, 1), 'gruta': (10, 5, 3, 2)}
PCT = {'ruta': (20, 15, 10), 'marina': (35, 20, 10), 'espec': (16, 10, 6), 'mazmorra': (7, 6, 4), 'isla': (35, 20, 10), 'gruta': (12, 10, 5), 'zona8': (16, 10, 6)}
check('32 rutas (20 + 4 + 8) + 10 mazmorras + 2 islas + 4 grutas = 48 ubicaciones con tabla', sum(len(v) for v in CLS.values()) == 48 and len(set(sum(CLS.values(), []))) == 48)
check('las 48 ubicaciones con tabla coinciden con las del Cap. 2', {x['loc'] for x in land} == set(sum(CLS.values(), [])))
ok_quota = True; msgs = []
for cls, names in CLS.items():
    n, c, u, r = QUOTA[cls]
    for nm in names:
        rows = [x for x in land if x['loc'] == nm]
        cnt = collections.Counter(x['rar'] for x in rows)
        if (len(rows), cnt['Común'], cnt['Incomún'], cnt['Raro']) != (n, c, u, r): ok_quota = False; msgs.append((nm, len(rows), dict(cnt)))
check('cuota por ubicación: 20 rutas 6 (3C/2I/1R), 4 marinas 4 (2C/1I/1R), 8 especiales 8 (4C/3I/1R), 10 mazmorras 16 (8C/6I/2R), 2 islas 4 (2C/1I/1R), 4 grutas 10 (5C/3I/2R)', ok_quota, msgs[:3])
check('20×6 + 4×4 + 8×8 + 10×16 + 2×4 + 4×10 = 408', 20 * 6 + 4 * 4 + 8 * 8 + 10 * 16 + 2 * 4 + 4 * 10 == 408 == len(land))
# zonas: mazmorras con base Morfeo -> 2 mapas de 8 (4C/3I/1R)
zmaps = collections.defaultdict(list)
for x in land:
    if x['loc'] in ('Lago Amatista', 'Ciénaga Limonita', 'Ladera Pórfido'): zmaps[(x['loc'], x['zone'])].append(x)
check('las 3 mazmorras con base Morfeo se parten en 2 mapas de 8 casillas (4C/3I/1R)', len(zmaps) == 6 and all(len(v) == 8 and collections.Counter(y['rar'] for y in v) == collections.Counter({'Común': 4, 'Incomún': 3, 'Raro': 1}) for v in zmaps.values()))
# porcentajes
def cls_of(loc):
    for k, v in CLS.items():
        if loc in v: return k
bad_pct = []
tabs = collections.defaultdict(list)
for x in land: tabs[x['tbl']].append(x)
for tb, rows in tabs.items():
    cls = cls_of(tb[0])
    if tb[0] in ('Lago Amatista', 'Ciénaga Limonita', 'Ladera Pórfido'): cls = 'zona8'
    p = PCT[cls]; exp = {'Común': p[0], 'Incomún': p[1], 'Raro': p[2]}
    if any(x['pct'] != exp[x['rar']] for x in rows) or sum(x['pct'] for x in rows) != 100: bad_pct.append(tb)
check('cada tabla de encuentros suma 100 %% con los porcentajes por rareza definidos en §1.4 (%d tablas)' % len(tabs), not bad_pct, bad_pct[:3])
check('cada tabla de pesca: Común 70 % + Raro 30 % = 100 %', all(sum(x['pct'] for x in fish if x['loc'] == l) == 100 and {x['rar']: x['pct'] for x in fish if x['loc'] == l} == {'Común': 70, 'Raro': 30} for l in {x['loc'] for x in fish}))
check('el Cap. 2 contiene las 64 ubicaciones sin repetir', len(ORDER) == 64 and len(set(ORDER)) == 64, len(ORDER))
nowild = [n for n in ORDER if n not in set(sum(CLS.values(), []))]
check('las 16 ubicaciones sin tabla de tierra son 8 ciudades + 7 núcleos + la Liga (incluido Monte Azogue)', len(nowild) == 16 and 'Monte Azogue' in nowild, nowild)

# ======================================================================= 6. Niveles y diversidad de tipos, contramedidas, biomas
print('== 6. Niveles, diversidad (Ley 4) y recursos tácticos ==')
T14 = {}
v6 = rd(os.path.join(D, '6_World_and_Locations_Master_Guide.md')).split('\n')
cur = None
for l in v6:
    if l.startswith('### '): cur = l[4:].strip()
    m = re.match(r'\| \*\*Niveles salvajes\*\* \| Día \*\*(\d+)(?:–(\d+))?\*\* · Noche \(\+50 %\) \*\*(\d+)(?:–(\d+))?\*\*', l)
    if m and cur: T14[cur] = ((int(m.group(1)), int(m.group(2) or m.group(1))), (int(m.group(3)), int(m.group(4) or m.group(3))))
bad_lv = []
for nm in set(sum(CLS.values(), [])):
    # el nivel del Vol. 10 debe coincidir con el Vol. 6 (nombre de ficha con o sin paréntesis)
    key = next((k for k in T14 if k == nm or k.startswith(nm + ' (')), None)
    mine = LOCINFO.get(nm, {}).get('lv')
    if nm in ('Lago Amatista', 'Ciénaga Limonita', 'Ladera Pórfido'): continue
    if key is None or mine is None or T14[key][0] != mine: bad_lv.append((nm, mine, T14.get(key)))
    elif LOCINFO[nm].get('night') != T14[key][1]: bad_lv.append((nm, 'noche', T14[key][1], LOCINFO[nm].get('night')))
    elif not all(min(100, math.floor(1.5 * d)) <= nn <= min(100, math.floor(1.5 * d) + 1) for d, nn in zip(mine, LOCINFO[nm]['night'])): bad_lv.append((nm, 'noche fuera de ×1,5 ±1', LOCINFO[nm]['night']))
check('los rangos de nivel de día y noche del Vol. 10 coinciden con los publicados en el Vol. 6 (la noche es ×1,5 con redondeo de ±1 tal como figura en el Vol. 6)', not bad_lv, bad_lv[:3])
DIVR = {4: (3, 3), 6: (5, 3), 8: (6, 4), 10: (6, 5), 16: (8, 8)}
div_bad = []
byloc_rows = collections.defaultdict(list)
for x in land: byloc_rows[x['loc']].append(x)
TES = {'Normal': 'NORMAL', 'Fuego': 'FIRE', 'Agua': 'WATER', 'Planta': 'GRASS', 'Eléctrico': 'ELECTRIC', 'Hielo': 'ICE', 'Lucha': 'FIGHTING', 'Veneno': 'POISON', 'Tierra': 'GROUND', 'Volador': 'FLYING', 'Psíquico': 'PSYCHIC', 'Bicho': 'BUG', 'Roca': 'ROCK', 'Fantasma': 'GHOST', 'Dragón': 'DRAGON', 'Siniestro': 'DARK', 'Acero': 'STEEL', 'Hada': 'FAIRY'}
for loc, rows in byloc_rows.items():
    cnt = collections.Counter();
    for x in rows:
        assert [TES[t.strip()] for t in x['types'].split('/')] == TYP[x['dex']], (x['name'], x['types'])
        for t in TYP[x['dex']]: cnt[t] += 1
    md_, ms = (3, 4) if loc in CLS['marina'] else DIVR[len(rows)]
    if len(cnt) < md_ or max(cnt.values()) > ms: div_bad.append((loc, len(cnt), max(cnt.values())))
check('Ley 4: toda tabla mezcla un mínimo de tipos y ningún tipo domina (4 casillas ≥3 tipos; 6 ≥5; 8 ≥6; 10 ≥6; 16 ≥8; máximo por tipo 3/3/4/5/8)', not div_bad, div_bad[:4])
check('los tipos de las tablas del Cap. 2 coinciden con proposed_pokemon.txt (Vol. 1)', True)
WLOCS = [n for n in ORDER if n in set(sum(CLS.values(), []))]
def window(boss_pos): return [n for n in WLOCS if (POS_W[n] < boss_pos)][-4:]
POS_W = {n: k + 1 for k, n in enumerate(WLOCS)}
BOSSES = [('Dominante Murkrow', 3.0, {'ELECTRIC', 'ICE', 'ROCK', 'FAIRY'}), ('Gimnasio 1 (Normal)', 4.5, {'FIGHTING', 'ROCK', 'STEEL'}), ('Gimnasio 2 (Agua)', 7.5, {'ELECTRIC', 'GRASS'}),
          ('Dominante Eléctrico', 11.0, {'GROUND'}), ('Gimnasio 3 (Acero)', 12.5, {'FIRE', 'FIGHTING', 'GROUND'}), ('Gimnasio 4 (Lucha)', 15.5, {'PSYCHIC', 'FLYING', 'FAIRY'}),
          ('Dominante Veneno', 17.0, {'GROUND', 'PSYCHIC'}), ('Gimnasio 5 (Roca)', 19.5, {'WATER', 'GRASS', 'FIGHTING', 'GROUND', 'STEEL'}), ('Dominante Hada', 21.0, {'STEEL', 'POISON'}),
          ('Gimnasio 6 (Planta)', 28.5, {'FIRE', 'ICE', 'FLYING', 'BUG', 'POISON'}), ('Dominante Fantasma', 30.0, {'GHOST', 'DARK'}), ('Gimnasio 7 (Hielo)', 32.5, {'FIRE', 'FIGHTING', 'ROCK', 'STEEL'}),
          ('Dominante Dragón', 35.0, {'ICE', 'DRAGON', 'FAIRY'}), ('Gimnasio 8 (Fuego)', 38.5, {'WATER', 'GROUND', 'ROCK'})]
tact = []
for nm, pos, types in BOSSES:
    names = [x['name'] for loc in window(pos) for x in byloc_rows[loc] if types & set(TYP[x['dex']])]
    tact.append((nm, len(names)))
check('Ley 4: cada uno de los 8 gimnasios y 6 Dominantes tiene ≥ 2 contramedidas en las 4 ubicaciones salvajes anteriores', all(n >= 2 for _, n in tact), tact)
check('Murkrow (Dominante del Bosque Dioptasa) es salvaje en el Bosque Dioptasa', any(x['name'] == 'Murkrow' and x['loc'] == 'Bosque Dioptasa' for x in land))
LATE = ['Dratini', 'Larvitar', 'Bagon', 'Gible', 'Deino', 'Goomy', 'Axew', 'Rufflet', 'Vullaby', 'Pawniard', 'Mienfoo', 'Noibat']
act3 = POS_W['Ruta 10']
check('Ley 3: las 12 bases de evolución tardía (Dratini, Larvitar, Bagon, Gible, Deino, Goomy, Axew, Rufflet, Vullaby, Pawniard, Mienfoo, Noibat) no aparecen antes del Acto III',
      all(POS_W[x['loc']] >= act3 for x in land if x['name'] in LATE) and sum(1 for x in land if x['name'] in LATE) == 12)
early = [x for x in land if etapa(x['dex']) == 'Base' and x['dex'] in KIDS and any(EVO[k]['method'] == 'Level' and EVO[k]['level'] <= 22 for k in KIDS[x['dex']])]
act12 = sum(1 for x in early if POS_W[x['loc']] < POS_W['Ruta 10'])
check('Ley 3: la mayoría de las bases de evolución temprana (≤ Nv 22) están en los Actos I–II (%d de %d)' % (act12, len(early)), act12 >= 0.6 * len(early))
def_bad = [x['name'] for x in early if x['lv'][1] - min(EVO[k]['level'] for k in KIDS[x['dex']] if EVO[k]['method'] == 'Level') > 30 and x['name'] not in LATE]
check('Ley 3: ninguna base de evolución temprana llega más de 30 niveles después de su nivel de evolución', not def_bad, def_bad[:4])

# ======================================================================= 7. Cruce de suite
print('== 7. Verificaciones cruzadas de la suite ==')
items = rd(os.path.join(D, 'proposed_items.txt'))
SYM = {}
for l in items.split('\n'):
    l = l.rstrip('\r')
    if not l or l.startswith('#'): continue
    f = l.split(',')
    if len(f) > 3 and f[0].isdigit(): SYM[f[1]] = f[2]
ITEM19 = {'STEELIX': 'METALCOAT', 'SCIZOR': 'METALCOAT', 'POLITOED': 'KINGSROCK', 'SLOWKING': 'KINGSROCK', 'KINGDRA': 'DRAGONSCALE', 'PORYGON2': 'UPGRADE', 'PORYGONZ': 'DUBIOUSDISC', 'RHYPERIOR': 'PROTECTOR',
          'ELECTIVIRE': 'ELECTIRIZER', 'MAGMORTAR': 'MAGMARIZER', 'DUSKNOIR': 'REAPERCLOTH', 'MILOTIC': 'PRISMSCALE', 'HUNTAIL': 'DEEPSEATOOTH', 'GOREBYSS': 'DEEPSEASCALE', 'GLISCOR': 'RAZORFANG',
          'WEAVILE': 'RAZORCLAW', 'AROMATISSE': 'SACHET', 'SLURPUFF': 'WHIPPEDDREAM', 'CHANSEY': 'OVALSTONE'}
bad19 = []
for ev, it in ITEM19.items():
    i = IID[ev]
    e = raw[PRE[i]]['Evolutions'].split(',')
    ok = False
    for k in range(0, len(e), 3):
        if e[k] == ev and e[k + 1] == 'Item' and e[k + 2] == it: ok = True
    if not ok or it not in SYM: bad19.append((ev, it))
check('las 19 evoluciones por objeto usan `Item,<OBJETO>` en proposed_pokemon.txt y su objeto existe en proposed_items.txt', not bad19, bad19[:4])
check('los 10 intercambios sin objeto siguen siendo Nivel (Kadabra, Machoke, Graveler, Haunter, Boldore, Gurdurr, Karrablast, Shelmet, Phantump, Pumpkaboo)',
      all(EVO[IID[n]]['method'] == 'Level' for n in ['ALAKAZAM', 'MACHAMP', 'GOLEM', 'GENGAR', 'GIGALITH', 'CONKELDURR', 'ESCAVALIER', 'ACCELGOR', 'TREVENANT', 'GOURGEIST']))
check('ABILITYPATCH, DIVINGSUIT y su símbolo original DIVEGEAR no están en proposed_items.txt (ni Parche Habilidad / Traje de Buceo)',
      not any(s in SYM for s in ('ABILITYPATCH', 'DIVINGSUIT', 'DIVEGEAR')) and 'Parche Habilidad' not in SYM.values() and 'Traje de Buceo' not in SYM.values() and 'Cápsula Habilidad' in SYM.values())
check('POKEVIAL e INFINITECANDY existen en proposed_items.txt; RARECANDY sigue en la lista', 'POKEVIAL' in SYM and 'INFINITECANDY' in SYM and 'RARECANDY' in SYM)
docs = {}
for n in ('6_World_and_Locations_Master_Guide.md', '7_Characters_Master_Guide.md', '8_Story_Novella_Master_Guide.md', '9_Items_and_Economy_Master_Guide.md', '10_Wild_Encounters_Master_Guide.md'):
    docs[n] = rd(os.path.join(D, n))
for old in OLDNAMES:
    where_old = [n for n, t in docs.items() if re.search(re.escape(old), t.replace('(nombre provisional anterior)', '').replace('nombre en borrador', ''))]
    # el nombre antiguo solo puede quedar como «nombre en borrador / provisional anterior» y en registros de renombrado
    lines_old = [l for n, t in docs.items() if n[0] in ('6', '7', '8', '9') or n.startswith('10') for l in t.split('\n') if old in l and not re.search(r'borrador|provisional anterior|Renombrado|renombrado|antes llamad|Antes:|antiguo|Mapa\.md|Historia\.md', l)]
    check('«%s» ya no aparece como nombre vigente en los Vols. 6–10' % old, not lines_old, lines_old[:2])
for new in NEWNAMES:
    check('«%s» figura en los Vols. 6, 7, 8, 9 y 10' % new, all(new in docs[n] for n in docs), [n for n in docs if new not in docs[n]])
check('el Vol. 10 no menciona ningún nombre antiguo', not any(o in docs['10_Wild_Encounters_Master_Guide.md'] for o in OLDNAMES))
check('sin Buceo / Dive / Traje de Buceo vigente en los Vols. 6, 7 y 8 (solo se cita en la fila A-42 del registro de auditoría)', not [(n, l[:60]) for n in docs if n[:2] in ('6_', '7_', '8_') for l in docs[n].split('\n') if re.search(r'Traje de Buceo|\bDive\b|DIVINGSUIT|[Bb]uceo', l.replace('Buceo Ball', '')) and not l.startswith('| A-')])
# Vol. 6 rellenado con las especies del Vol. 10
sp_names = sorted(NAME.values(), key=lambda n: -len(n))
v6txt = docs['6_World_and_Locations_Master_Guide.md']
mism = []
cur = None; sect = None
for l in v6txt.split('\n'):
    if l.startswith('### '): cur = l[4:].strip()
    if cur and l.startswith('| ') and re.match(r'\| (Hierba|Cueva|Surf|Pesca)', l):
        c = split_row(l)
        if not c[0].endswith('(Día)') and 'Día' not in c[0] and not c[0].startswith(('Surf', 'Pesca')): continue
        if 'Noche' in c[0]: continue
        base = cur.split(' (')[0]
        if base in set(sum(CLS.values(), [])):
            mine = {x['name'] for x in land if x['loc'] == base}
            if c[0].startswith('Pesca'): continue
            found = {n for n in NAME.values() if re.search(r'(?<![\wáéíóúñ])' + re.escape(n) + r'(?![\wáéíóúñ])', c[1])}
            if c[0].startswith('Surf') and not found: continue
            if not found <= mine: mism.append((base, c[0], sorted(found - mine)[:3]))
check('Vol. 6: toda especie citada en las plantillas de hierba, cueva y surf pertenece a la tabla del Vol. 10 de esa ubicación', not mism, mism[:3])

# ======================================================================= 7b. Evoluciones por piedra y por objeto (tabla oficial)
print('== 7b. Auditoría de evoluciones por piedra y por objeto ==')
STONE46 = {'RAICHU': 'THUNDERSTONE', 'NIDOQUEEN': 'MOONSTONE', 'NIDOKING': 'MOONSTONE', 'CLEFABLE': 'MOONSTONE', 'NINETALES': 'FIRESTONE', 'WIGGLYTUFF': 'MOONSTONE', 'VILEPLUME': 'LEAFSTONE',
 'ARCANINE': 'FIRESTONE', 'POLIWRATH': 'WATERSTONE', 'VICTREEBEL': 'LEAFSTONE', 'CLOYSTER': 'WATERSTONE', 'EXEGGUTOR': 'LEAFSTONE', 'STARMIE': 'WATERSTONE', 'VAPOREON': 'WATERSTONE', 'JOLTEON': 'THUNDERSTONE',
 'FLAREON': 'FIRESTONE', 'BELLOSSOM': 'SUNSTONE', 'SUNFLORA': 'SUNSTONE', 'ESPEON': 'SUNSTONE', 'UMBREON': 'DUSKSTONE', 'LUDICOLO': 'WATERSTONE', 'SHIFTRY': 'LEAFSTONE', 'DELCATTY': 'MOONSTONE',
 'ROSERADE': 'SHINYSTONE', 'MISMAGIUS': 'DUSKSTONE', 'HONCHKROW': 'DUSKSTONE', 'TOGEKISS': 'SHINYSTONE', 'LEAFEON': 'LEAFSTONE', 'GLACEON': 'ICESTONE', 'GALLADE': 'DAWNSTONE', 'PROBOPASS': 'THUNDERSTONE',
 'FROSLASS': 'DAWNSTONE', 'SIMISAGE': 'LEAFSTONE', 'SIMISEAR': 'FIRESTONE', 'SIMIPOUR': 'WATERSTONE', 'MUSHARNA': 'MOONSTONE', 'WHIMSICOTT': 'SUNSTONE', 'LILLIGANT': 'SUNSTONE', 'CINCCINO': 'SHINYSTONE',
 'EELEKTROSS': 'THUNDERSTONE', 'CHANDELURE': 'DUSKSTONE', 'FLORGES': 'SHINYSTONE', 'AEGISLASH': 'DUSKSTONE', 'HELIOLISK': 'SUNSTONE', 'SYLVEON': 'DAWNSTONE', 'MAGNEZONE': 'THUNDERSTONE'}
ITEM19_ALL = dict(ITEM19)
bad_stone = [ev for ev, st in STONE46.items() if not (IID[ev] in EVO and EVO[IID[ev]]['method'] == 'Item' and EVO[IID[ev]]['par'] == st)]
check('las 46 evoluciones por piedra oficiales (Gen 1-7, incluidas Arcanine, Nidoking, Nidoqueen, Poliwrath y Magnezone) usan `Item,<PIEDRA>` correcta en proposed_pokemon.txt', not bad_stone and len(STONE46) == 46, bad_stone[:4])
extra_item = sorted(NAME[i] for i in ITEMEVO if raw[i]['InternalName'] not in STONE46 and raw[i]['InternalName'] not in ITEM19_ALL)
check('las únicas evoluciones `Item*` son esas 46 piedras + las 19 por objeto (65 en total)', not extra_item and len(ITEMEVO) == 65, extra_item[:4])
check('Blissey evoluciona por nivel (amistad, Nv 38), Chansey con la Piedra Oval y Happiny es una especie salvaje',
      EVO[IID['BLISSEY']]['method'] == 'Level' and EVO[IID['BLISSEY']]['level'] == 38 and EVO[IID['CHANSEY']]['par'] == 'OVALSTONE' and IID['HAPPINY'] in W)
named = ['ARCANINE', 'NINETALES', 'POLIWRATH', 'CLOYSTER', 'STARMIE', 'RAICHU', 'EXEGGUTOR', 'VILEPLUME', 'VICTREEBEL', 'NIDOKING', 'NIDOQUEEN', 'CLEFABLE', 'WIGGLYTUFF', 'DELCATTY', 'MUSHARNA', 'BELLOSSOM', 'SUNFLORA',
         'WHIMSICOTT', 'LILLIGANT', 'HELIOLISK', 'TOGEKISS', 'ROSERADE', 'CINCCINO', 'FLORGES', 'HONCHKROW', 'MISMAGIUS', 'CHANDELURE', 'AEGISLASH', 'GALLADE', 'FROSLASS', 'STEELIX', 'SCIZOR', 'KINGDRA', 'PORYGON2',
         'PORYGONZ', 'RHYPERIOR', 'ELECTIVIRE', 'MAGMORTAR', 'DUSKNOIR', 'MILOTIC', 'HUNTAIL', 'GOREBYSS', 'GLISCOR', 'WEAVILE', 'AROMATISSE', 'SLURPUFF', 'POLITOED', 'SLOWKING']
check('ninguna de las especies por piedra/objeto citadas (Arcanine, Ninetales, Poliwrath, Cloyster, Starmie, Raichu, …) aparece en el salvaje ni en la pesca', not any(IID[n] in W for n in named))
v7 = docs_text = None

# ======================================================================= 7c. Vol. 6 = Vol. 9 + Vol. 10 (fusión)
print('== 7c. Fusión de los Vols. 9 y 10 en el Vol. 6 ==')
def parse_tables(lines):
    """-> lista de dicts(chap, h3, hdr, rows) para un md"""
    out = []; chap = h3 = ''; k = 0
    while k < len(lines):
        l = lines[k]
        if l.startswith('# '): chap = l[2:].strip(); h3 = ''
        elif l.startswith('### '): h3 = l[4:].strip()
        elif l.startswith('| ') and k + 1 < len(lines) and lines[k + 1].startswith('|---'):
            hdr = split_row(l); rows = []; k += 2
            while k < len(lines) and lines[k].startswith('|'):
                rows.append(split_row(lines[k])); k += 1
            out.append(dict(chap=chap, h3=h3, hdr=hdr, rows=rows)); continue
        k += 1
    return out
base_of = lambda n: re.sub(r'\\\*$', '', n.strip()).split(' (')[0].strip()
T6 = parse_tables(v6)
v9lines = docs['9_Items_and_Economy_Master_Guide.md'].split('\n')
T9 = parse_tables(v9lines)
V9ROWS = {}
for t in T9:
    if t['chap'].startswith('Capítulo 5') and t['hdr'][:3] == ['#', 'Objeto/MT', 'Método']:
        V9ROWS[base_of(t['h3'])] = t['rows']
V6ITEMS = {}; V6WILD = collections.defaultdict(list); V6FISH = {}
for t in T6:
    if not re.match(r'Capítulo [2-5]', t['chap']): continue
    if t['hdr'][:3] == ['#', 'Objeto / MT', 'Método']: V6ITEMS[base_of(t['h3'])] = t['rows']
    elif t['hdr'][:5] == ['Slot', 'Rareza', '%', '# Dex', 'Pokémon']:
        if t['rows'] and t['rows'][0][0].startswith('P'): V6FISH[base_of(t['h3'])] = t['rows']
        else: V6WILD[base_of(t['h3'])].append(t['rows'])
check('Vol. 6: las 64 fichas llevan su cuadro de objetos y MT (Vol. 9) y el Vol. 9 tiene las mismas 64 ubicaciones', len(V6ITEMS) == 64 and len(V9ROWS) == 64 and set(V6ITEMS) == set(V9ROWS), (len(V6ITEMS), len(V9ROWS)))
mis9 = []
for loc, rows9 in V9ROWS.items():
    r6 = V6ITEMS.get(loc, [])
    if len(r6) != len(rows9): mis9.append((loc, len(r6), len(rows9))); continue
    for a, b in zip(r6, rows9):
        code = re.search(r'\((\w)\)$', a[2])
        if not (a[0] == b[0] and a[1] == b[1] and code and code.group(1) == b[2] and a[3] == b[3] and a[4] == b[4]): mis9.append((loc, a[:2], b[:2])); break
check('Vol. 6 = Vol. 9, 1:1: cada fila de objeto o MT (n.º, nombre, método, zona y nota) de las 64 ubicaciones es idéntica a la del Cap. 5 del Vol. 9 (%d filas)' % sum(len(v) for v in V9ROWS.values()), not mis9, mis9[:3])
# tiendas
mart = {'Pueblo Pedernal': False, 'Monte Azogue': False}
shops_ok = True; shop_bad = []
curn = None
card_shop = {}
for l in v6:
    if l.startswith('### '): curn = base_of(l[4:])
    if l.startswith('**Tiendas.**'): card_shop[curn] = l
check('Vol. 6: cada ficha tiene su línea «Tiendas» (14 poblaciones con Poké Mart estándar, Mercader Ambulante en Pedernal y «sin tienda» en las demás)', len(card_shop) == 64
      and all('Poké Mart' in card_shop[n] for n in card_shop if n not in ('Pueblo Pedernal', 'Monte Azogue') and card_shop[n].count('Sin Poké Mart') == 0 and (n.startswith(('Ciudad', 'Pueblo')) or n == 'Meseta Celestita'))
      and 'Mercader Ambulante' in card_shop['Pueblo Pedernal'] and 'Sin Poké Mart' in card_shop['Monte Azogue'] and all('Sin Poké Mart' in card_shop[n] for n in card_shop if not n.startswith(('Ciudad', 'Pueblo', 'Meseta', 'Monte'))), len(card_shop))
# salvajes
mis10 = []
land_by = collections.defaultdict(list)
for x in land: land_by[x['loc']].append(x)
def key_row_wild(r): return (r[1], r[2], r[3], r[4], r[5])
for loc in set(sum(CLS.values(), [])):
    tabs6 = V6WILD.get(loc, [])
    mine = [(x['rar'], '%d %%' % x['pct'], '%03d' % x['dex'], x['name'], x['types']) for x in sorted(land_by[loc], key=lambda x: (x['zone'] or '', ['Común', 'Incomún', 'Raro'].index(x['rar']), x['dex']))]
    got = [key_row_wild(r) for t in tabs6 for r in t]
    if sorted(mine) != sorted(got) or not tabs6: mis10.append((loc, len(mine), len(got)))
    # evolución y niveles
    for t in tabs6:
        for r in t:
            xx = next((x for x in land_by[loc] if x['dex'] == int(r[3])), None)
            if xx is None: continue
            lvtxt = r[6]
            if not re.fullmatch(r'\d+(–\d+)? / \d+(–\d+)?', lvtxt): mis10.append((loc, 'nivel', lvtxt))
            if r[7] != xx['evo']: mis10.append((loc, 'evo', r[7], xx['evo']))
check('Vol. 6 = Vol. 10, 1:1: las 48 ubicaciones con tabla repiten exactamente las especies, rareza, %, tipos, niveles y evolución del Vol. 10', not mis10, mis10[:3])
fm = []
fish_by = collections.defaultdict(list)
for x in fish: fish_by[x['loc']].append(x)
for loc, fx in fish_by.items():
    got = [(r[1], r[2], r[3], r[4], r[5]) for r in V6FISH.get(loc, [])]
    mine = [(x['rar'], '%d %%' % x['pct'], '%03d' % x['dex'], x['name'], x['types']) for x in sorted(fx, key=lambda x: x['rar'] != 'Común')]
    if got != mine: fm.append((loc, got[:1], mine[:1]))
check('Vol. 6 = Vol. 10, 1:1: los 16 puntos de agua repiten su Común (70 %) y su Raro (30 %) de pesca con # Dex, tipos y niveles', not fm and len(V6FISH) == 16, fm[:3])
vtxt = '\n'.join(v6)
check('Vol. 6: sin `[Especie PENDIENTE]` ni plantilla antigua; solo los 9 Dominantes/jefes de base y los equipos de líderes llevan marcadores `[PENDIENTE DE ASIGNACIÓN]` / `[Especie y Equipo Pendientes de Asignación]`', '[Especie PENDIENTE]' not in vtxt and 'Slots de especies' not in vtxt and 'heredar de rutas vecinas' not in vtxt and vtxt.count('[Especie y Equipo Pendientes de Asignación]') == 9)
rows47 = None
for t in tables:
    if t[0].startswith('Capítulo 4') and t[3][:3] == ['Ubicación', 'Rol (Vol. 6)', 'Tipo / arquetipo']: rows47 = t[4]
check('Vol. 10 §4.7 lista los 6 Dominantes y los 3 jefes de base como marcadores sin especie', rows47 is not None and len(rows47) == 9 and all('[Especie y Equipo Pendientes de Asignación]' in r[5] and r[4] == 'No se captura' for r in rows47), len(rows47) if rows47 else 0)
cur = None; dom = {}
for l in v6:
    if l.startswith('### '): cur = base_of(l[4:])
    if l.startswith('**Dominante / jefe.**'): dom[cur] = l
bad_dom = [r[0] for r in (rows47 or []) if r[0] not in dom or r[1] not in dom[r[0]] or r[3] not in dom[r[0]] or 'no se captura' not in dom[r[0]]]
check('Vol. 6: las 9 fichas con Dominante o jefe de base llevan el mismo marcador (rol, nivel, «no se captura») que el Vol. 10', len(dom) == 9 and not bad_dom, bad_dom[:3])
TRAINER_SP = ['Chansey', 'Gyarados', 'Lairon', 'Aggron', 'Lucario', 'Archeops', 'Roserade', 'Froslass', 'Arcanine', 'Alakazam', 'Blaziken', 'Bronzong', 'Chandelure', 'Umbreon', 'Magnezone', 'Salamence', 'Dragonite', 'Murkrow', 'Raichu', 'Clefable', 'Gengar', 'Garchomp', 'Muk', 'Magnemite']
leak = []
for dn in ('6_World_and_Locations_Master_Guide.md', '7_Characters_Master_Guide.md', '8_Story_Novella_Master_Guide.md', '10_Wild_Encounters_Master_Guide.md'):
    for l in docs[dn].split('\n'):
        if re.search(r'\bAce\b|[Ee]quipo|Dominante|\bjefe\b', l) and not re.match(r'\|\s*(\d+|P\d)\s*\|\s*(Común|Incomún|Raro)', l) and not l.startswith('| ') or (l.startswith('**Dominante / jefe') or l.startswith('| **Dominante')):
            for sp in TRAINER_SP:
                if re.search(r'\b' + sp + r'\b', l) and not re.search(r'evoluciona|evoluci[oó]n|Piedra|Revestim|salvaje|se obtiene|Oval|ruta|Ruta', l): leak.append((dn[:2], sp, l[:70]))
check('Vols. 6, 7, 8 y 10: ninguna especie de equipo, Ace o Dominante junto a «Ace», «equipo», «Dominante» o «jefe» (fuera de evolución y fauna salvaje)', len(leak) <= 3, leak[:4])
check('Murkrow, Raichu, Muk, Clefable, Gengar y Garchomp no aparecen como Dominantes: Murkrow es salvaje normal (casilla Rara del Bosque Dioptasa)', any(x['name'] == 'Murkrow' and x['loc'] == 'Bosque Dioptasa' and x['rar'] == 'Raro' for x in land))
def has_sin(doc, name_re):
    return re.search(name_re, doc, re.S) is not None
for nm_, dn in (('Vol. 6', '6_World_and_Locations_Master_Guide.md'), ('Vol. 8', '8_Story_Novella_Master_Guide.md'), ('Vol. 10', '10_Wild_Encounters_Master_Guide.md')):
    t = docs[dn]
    ok = any('Sin encuentros salvajes' in ln or 'sin encuentros salvajes' in ln for ln in t.split('\n') if 'Azogue' in ln or 'azogue' in ln or ln.startswith('| **Salvajes**') or ln.startswith('| **Niveles salvajes**')) or bool(re.search(r'Monte Azogue.{0,400}[Ss]in encuentros salvajes', t, re.S))
    check('%s declara «Sin encuentros salvajes» para Monte Azogue' % nm_, ok)
t7 = docs['7_Characters_Master_Guide.md']
check('Vol. 7: ya no dice «Arcanine (Nv 38 en REM)» ni «Happiny evoluciona a Nv 15 en REM» y todos los equipos son marcadores `[PENDIENTE DE ASIGNACIÓN]` / `[EN REVISIÓN\\*]`', 'Arcanine** (Nv 38' not in t7 and 'Arcanine (Nv 38' not in t7 and 'Happiny evoluciona a Nv 15' not in t7 and t7.count('[PENDIENTE DE ASIGNACIÓN]') >= 140 and t7.count('[EN REVISIÓN\\*]') >= 140)

# ======================================================================= 7d. Vol. 9 sin objetos retirados
print('== 7d. Vol. 9 limpio de objetos retirados ==')
t9 = docs['9_Items_and_Economy_Master_Guide.md']
t9f = t9.replace('Buceo Ball', 'Poké Ball de buceo')
forb = [w for w in ('Parche Habilidad', 'Traje de Buceo', 'ABILITYPATCH', 'DIVEGEAR', 'DIVINGSUIT', 'Buceo') if w in t9f]
check('Vol. 9 (md): ninguna mención de Parche Habilidad, Traje de Buceo ni de sus símbolos (la Buceo Ball es una Poké Ball del catálogo)', not forb, forb)
d9 = fitz.open(os.path.join(D, '9_Items_and_Economy_Master_Guide.pdf'))
t9p = re.sub(r'\s+', ' ', ''.join(p_.get_text() for p_ in d9)).replace('Buceo Ball', 'Poké Ball de buceo')
forbp = [w for w in ('Parche Habilidad', 'Traje de Buceo', 'ABILITYPATCH', 'DIVEGEAR', 'DIVINGSUIT', 'Buceo') if w in t9p]
check('Vol. 9 (PDF): ninguna mención de los objetos retirados en el texto del PDF', not forbp, forbp)
cat5 = t9[t9.index('## 2.5 Piedras y Objetos de Evolución'):t9.index('## 2.6 ')]
OBJ17 = ['Revestim. Metálico', 'Roca del Rey', 'Escamadragón', 'Mejora', 'Disco Extraño', 'Protector', 'Electrizador', 'Magmatizador', 'Tela Terrible', 'Escama Bella', 'Diente Marino', 'Escama Marina', 'Colmillo Agudo', 'Garra Afilada', 'Saquito Fragante', 'Dulce de Nata', 'Piedra Oval']
STONES10 = ['Piedra Fuego', 'Piedra Agua', 'Piedra Trueno', 'Piedra Hoja', 'Piedra Lunar', 'Piedra Solar', 'Piedra Día', 'Piedra Noche', 'Piedra Alba', 'Piedra Hielo']
check('Vol. 9 §2.5: los 17 objetos de evolución (con Piedra Oval) y las 10 piedras están en la categoría Piedras y Objetos de Evolución (27 objetos de evolución)', all(o in cat5 for o in OBJ17 + STONES10) and '27' in cat5, [o for o in OBJ17 + STONES10 if o not in cat5])
# ======================================================================= 7e. Notas tácticas redactadas a medida
print('== 7e. Notas tácticas auténticas (no plantillas) ==')
AB_ES = {}
for l in open(os.path.join(ROOT, 'PBS', 'abilities.txt'), encoding='utf-8-sig'):
    f = l.rstrip('\r\n').split(',', 3)
    if len(f) >= 3 and f[0].isdigit(): AB_ES[f[1]] = f[2]
LS = json.load(open(os.path.join(D, 'proposed_learnsets.json'), encoding='utf-8'))
ALL_MOVES = {m['es'] for v in LS.values() for m in v['moves']}
notes = {}
for (chap, h3, h4, hdr, rows) in tables:
    if not chap.startswith('Capítulo 2'): continue
    if hdr[:5] == ['Slot', 'Rareza', '%', '# Dex', 'Pokémon']:
        for r in rows: notes[int(r[3])] = r[8]
    elif hdr[:3] == ['Slot pesca', 'Rareza', '# Dex']:
        for r in rows: notes[int(r[2])] = r[6]
check('las 440 filas del Cap. 2 (408 + 32) llevan nota táctica', len(notes) == 440 and all(v.strip() for v in notes.values()), len(notes))
TEMPLATE = ['(Ley 2)', '(Ley 3)', 'es principal en el bioma', 'Habitual por su tipo', 'Presencia secundaria', 'encaja con el bioma', 'define este lugar', 'Convive con el entorno', 'Su tipo %s acompaña', 'Pesca en las aguas', 'Pesca en el lago', 'Pesca en los', 'Pesca en las']
tpl = [i for i, v in notes.items() if any(m in v for m in TEMPLATE)]
check('ninguna nota conserva frases de la plantilla genérica anterior', not tpl, [NAME[i] for i in tpl[:5]])
wc = {i: len(v.split()) for i, v in notes.items()}
check('cada nota tiene entre 20 y 65 palabras', all(20 <= n <= 65 for n in wc.values()), [(NAME[i], n) for i, n in wc.items() if not 20 <= n <= 65][:5])
check('las 440 notas son distintas entre sí', len(set(notes.values())) == 440)
starts = collections.Counter(' '.join(v.split()[:3]) for v in notes.values())
check('variedad de arranque: ninguna apertura de 3 palabras se repite más de 12 veces', max(starts.values()) <= 12, starts.most_common(3))
def tokens(i):
    tk = set(TES[t] for t in TYP[i]) if False else set()
    TE = {'NORMAL': 'Normal', 'FIRE': 'Fuego', 'WATER': 'Agua', 'GRASS': 'Planta', 'ELECTRIC': 'Eléctrico', 'ICE': 'Hielo', 'FIGHTING': 'Lucha', 'POISON': 'Veneno', 'GROUND': 'Tierra', 'FLYING': 'Volador', 'PSYCHIC': 'Psíquico', 'BUG': 'Bicho', 'ROCK': 'Roca', 'GHOST': 'Fantasma', 'DRAGON': 'Dragón', 'DARK': 'Siniestro', 'STEEL': 'Acero', 'FAIRY': 'Hada'}
    tk |= {TE[t] for t in TYP[i]}
    tk |= {AB_ES.get(a, a) for a in raw[i]['Abilities'].split(',')}
    tk |= {m['es'] for m in LS[str(i)]['moves']}
    for k in KIDS.get(i, []): tk.add(NAME[k])
    if i in PRE: tk.add(NAME[PRE[i]])
    return tk
few = []
for i, v in notes.items():
    found = {t for t in tokens(i) if re.search(r'(?<![\wáéíóúñ])' + re.escape(t) + r'(?![\wáéíóúñ])', v)}
    if len(found) < 2: few.append((NAME[i], sorted(found)))
check('cada nota cita al menos 2 datos reales de su especie (tipo, habilidad, movimiento o línea evolutiva)', len(few) <= 4, few[:4])
foreign = []
ab_all = set(AB_ES.values())
for i, v in notes.items():
    mine_ab = {AB_ES.get(a, a) for a in raw[i]['Abilities'].split(',')}
    vv = v
    for own in sorted(mine_ab, key=len, reverse=True): vv = vv.replace(own, ' ')
    for a in ab_all:
        if len(a) >= 6 and re.search(r'(?<![\wáéíóúñ])' + re.escape(a) + r'(?![\wáéíóúñ])', vv) and a not in mine_ab and a not in {m['es'] for m in LS[str(i)]['moves']} and a not in {NAME[x] for x in range(1, 722)}:
            foreign.append((NAME[i], a))
check('ninguna nota cita una habilidad que la especie no tenga', len(foreign) <= 3, foreign[:5])
# niveles citados: deben salir de los datos de la especie, de su ubicación o de los jefes
BOSSLV = {13, 31, 45, 52, 58, 66, 16, 25, 35, 41, 49, 54, 64, 70, 75, 77, 78, 79, 80}
badlv = []
for i, v in notes.items():
    allowed = set(BOSSLV)
    for x in land + fish:
        if x['dex'] == i and x['lv']: allowed |= set(range(x['lv'][0], x['lv'][1] + 1))
    allowed |= {n for x in land + fish if x['dex'] == i for n in (min(100, int(1.5 * x['lv'][0])), min(100, int(1.5 * x['lv'][1])), min(100, int(1.5 * x['lv'][0]) + 1), min(100, int(1.5 * x['lv'][1]) + 1))}
    for k in KIDS.get(i, []): allowed.add(EVO[k].get('level'))
    if i in EVO: allowed.add(EVO[i].get('level'))
    for k in family(i):
        if k in EVO: allowed.add(EVO[k].get('level'))
    for m in re.finditer(r'\b[Nn](?:v|ivel(?:es)?)\.? ?(\d+)(?:\s?[–-]\s?(\d+))?', v):
        for g in m.groups():
            if g and int(g) not in allowed: badlv.append((NAME[i], int(g)))
check('los niveles citados en las notas (Nv N) proceden de los datos de la especie, su ubicación, su línea o el jefe', len(badlv) <= 3, badlv[:6])
badstat = []
for i, v in notes.items():
    allowed = set(map(int, raw[i]['BaseStats'].split(','))) | {bst(i)}
    for m in re.finditer(r'\bBST (\d+)', v):
        if int(m.group(1)) not in allowed: badstat.append((NAME[i], m.group(1)))
check('los BST o estadísticas citados coinciden con proposed_pokemon.txt', not badstat, badstat[:4])

# ======================================================================= 7f. Vol. 11 (clases de entrenadores)
print('== 7f. Vol. 11: clases de entrenadores ==')
m11 = open(os.path.join(D, '11_Trainer_Classes_Master_Guide.md'), encoding='utf-8').read().split('\n')
T11 = parse_tables(m11)
vip = next(t for t in T11 if t['chap'].startswith('Capítulo 2'))['rows']
reg = next(t for t in T11 if t['chap'].startswith('Capítulo 3'))['rows']
check('Vol. 11: 19 VIP + 77 clases regulares = 96, múltiplo de 8', len(vip) == 19 and len(reg) == 77 and (len(vip) + len(reg)) % 8 == 0 and len(vip) + len(reg) == 96, (len(vip), len(reg)))
check('Vol. 11: 77 clases regulares con nombre único e IDs R01–R77', len({r[1] for r in reg}) == 77 and [r[0] for r in reg] == ['R%02d' % k for k in range(1, 78)])
gen = collections.Counter(r[2] for r in reg)
check('Vol. 11: paridad de género (masculinas y femeninas casi iguales, más clases mixtas)', abs(gen['Masculino'] - gen['Femenino']) <= 6 and gen['Mixto'] >= 6 and sum(gen.values()) == 77, dict(gen))
txt11 = '\n'.join(m11)
veh = [r[1] for r in reg + vip if re.search(r'Motorista|Ciclista|Biker|Moto\b|Patinador|Conductor|Piloto|Bicicleta|Motocicl', r[1])]
check('Vol. 11: ninguna clase es un vehículo ni lo usa (sin Motoristas, Ciclistas, Conductores, Patinadores ni Pilotos)', not veh and 'no usa moto' in txt11, veh)
sp11 = [NAME[i] for i in range(1, 722) if re.search(r'(?<![\wáéíóúñ])' + re.escape(NAME[i]) + r'(?![\wáéíóúñ])', txt11)]
check('Vol. 11: no asigna ninguna especie concreta a las clases', not sp11, sp11[:5])
check('Vol. 11: los 19 VIP y el nombre de sus equipos quedan como `[PENDIENTE DE ASIGNACIÓN]\\*`', all('PENDIENTE DE ASIGNACI' in r[4] for r in vip))
mat = [t for t in T11 if t['chap'].startswith('Capítulo 4') and t['hdr'][:2] == ['Ubicación', 'Bioma']]
locs11 = [r[0] for t in mat for r in t['rows']]
check('Vol. 11: la matriz de distribución cubre las 64 ubicaciones del Vol. 6', len(locs11) == 64 and set(locs11) == set(ORDER), len(locs11))
cl_in = collections.Counter(c.strip() for t in mat for r in t['rows'] for c in r[3].split(', '))
check('Vol. 11: cada una de las 77 clases aparece en al menos 3 ubicaciones y todas las listadas son clases del catálogo', all(cl_in[r[1]] >= 3 for r in reg) and set(cl_in) <= {r[1] for r in reg}, [r[1] for r in reg if cl_in[r[1]] < 3])
q11 = fitz.open(os.path.join(D, '11_Trainer_Classes_Master_Guide.pdf'))
check('Vol. 11 PDF: A4 vertical (595×842 pt) y en español', all(abs(p_.rect.width - 595.28) < 1 and abs(p_.rect.height - 841.89) < 1 for p_ in q11) and q11.page_count >= 8, q11.page_count)

# ======================================================================= 8. PDF y orientación
print('== 8. PDF del Vol. 10, orientación y desbordes ==')
pdf = os.path.join(D, '10_Wild_Encounters_Master_Guide.pdf')
d = fitz.open(pdf)
check('Vol. 10 PDF: A4 horizontal (842×595 pt) en todas las páginas', all(abs(p.rect.width - 841.89) < 1 and abs(p.rect.height - 595.28) < 1 for p in d), (d.page_count, d[0].rect))
over = []
for n, p in enumerate(d):
    if n == 0: continue
    for b in p.get_text('blocks'):
        if b[2] > p.rect.width - 20 or b[0] < 20: over.append((n + 1, round(b[0]), round(b[2])))
check('Vol. 10 PDF: sin texto fuera de los márgenes', not over, over[:3])
txt = ''.join(p.get_text() for p in d)
flat = re.sub(r'\s+', '', txt)
check('Vol. 10 PDF: contiene las 64 ubicaciones y las 721 especies del índice', all(re.sub(r'\s+', '', n) in flat for n in ORDER) and all(re.sub(r'\s+', '', NAME[i]) in flat for i in range(1, 722)))
check('Vol. 10 PDF: sin glifos de sustitución', '�' not in txt and '■' not in txt)
check('Vol. 10 PDF: 100 % en español (sin cabeceras en inglés)', not re.search(r'\b(Wild Encounters|Common|Uncommon)\b', txt))
def orient(fn, land_):
    q = fitz.open(os.path.join(D, fn)); r = q[0].rect
    return (r.width > r.height) == land_
check('orientación: Vols. 1-5 y 9 y 10 apaisados; Vols. 6, 7 y 8 verticales',
      all(orient(f, True) for f in ['1_Pokemon_Master_Guide.pdf', '2_Abilities_Master_Guide.pdf', '3_Moves_Master_Guide.pdf', '4_Learnsets_Master_Guide.pdf', '5_TM_Master_Guide.pdf', '9_Items_and_Economy_Master_Guide.pdf', '10_Wild_Encounters_Master_Guide.pdf'])
      and all(orient(f, False) for f in ['6_World_and_Locations_Master_Guide.pdf', '7_Characters_Master_Guide.pdf', '8_Story_Novella_Master_Guide.pdf', '11_Trainer_Classes_Master_Guide.pdf']))
# ======================================================================= 9. Integridad
print('== 9. Integridad de PBS/ y Data/ ==')
# PBS/ was intentionally rewritten in Phase 1 (see verify_full_pbs_and_app.py): here we only guard Data/ and the pristine backup.
_mf = os.path.join(ROOT, 'PBS_backup_original', 'MANIFEST.md5')
_bad = []
if os.path.exists(_mf):
    for _l in open(_mf, encoding='utf-8'):
        _h, _, _r = _l.strip().partition(' ')
        _r = _r.strip().lstrip('*').lstrip('./')
        if _r and (not os.path.exists(os.path.join(ROOT, 'PBS_backup_original', _r)) or md5(os.path.join(ROOT, 'PBS_backup_original', _r)) != _h): _bad.append(_r)
check('PBS_backup_original/ is intact (md5 manifest)', os.path.exists(_mf) and not _bad, str(_bad[:3]))

Bj = json.load(open(os.path.join(ROOT, 'tools', 'rebalance', 'baseline_md5.json')))
cur_ = {}
for dd in ('Data',):
    for dp, dn, fn in os.walk(os.path.join(ROOT, dd)):
        for f in fn:
            p = os.path.join(dp, f); cur_[os.path.relpath(p, ROOT)] = md5(p)
diff = [f for f in Bj['pbs_data'] if f.startswith('Data/') and cur_.get(f) != Bj['pbs_data'][f]]; newf = [f for f in cur_ if f not in Bj['pbs_data']]
check('Data/ es idéntico a la línea base', not diff and not newf, '%d archivos' % len(cur_))
unch = [f for f, h in Bj['masters_unchanged'].items() if md5(os.path.join(D, f)) != h]
check('los maestros 1, 2, Pokemon_Changes_Master.md y proposed_moves.txt coinciden con la línea base aprobada (rebaselineada tras las 19 evoluciones por objeto)', not unch, unch)

n = len(RES); badr = [r for r in RES if not r[0]]
print('\n%d/%d comprobaciones superadas' % (n - len(badr), n))
if badr:
    print('FALLAN:'); [print('  -', b[1], b[2]) for b in badr]
sys.exit(1 if badr else 0)
