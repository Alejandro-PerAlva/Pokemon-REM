#!/usr/bin/env python3
"""verify_items_master.py - verification of Master Volume #9 (Items & Economy) of Pokemon REM (design only, nothing is injected).

Reads ONLY files of this repository:
  docs/rebalance/{9_Items_and_Economy_Master_Guide.md, .pdf, proposed_items.txt}
  docs/rebalance/{proposed_tm.txt, proposed_moves.txt, Pokemon_Changes_Master.md}
  PBS/items.txt (the ORIGINAL item database, read-only), 6_ narrative volume (location names), proposed_pokemon.txt (item evolutions)
  tools/rebalance/baseline_md5.json (PBS/ and Data/ checksums)

Usage:  python3 tools/rebalance/verify_items_master.py        (exit code 0 = every check passed)
"""
import os, re, sys, json, csv, hashlib, collections, warnings
warnings.filterwarnings('ignore')
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
D = os.path.join(ROOT, 'docs', 'rebalance')
RES = []
def check(name, ok, detail=''):
    RES.append((bool(ok), name, detail)); print(('PASS  ' if ok else 'FAIL  ') + name + (f'  [{detail}]' if detail else ''))
def md5(p): return hashlib.md5(open(p, 'rb').read()).hexdigest()
def rd(p): return open(p, encoding='utf-8-sig').read()

MDP = os.path.join(D, '9_Items_and_Economy_Master_Guide.md')
PDFP = os.path.join(D, '9_Items_and_Economy_Master_Guide.pdf')
PBSP = os.path.join(D, 'proposed_items.txt')

print('== 1. Files ==')
check('9_Items_and_Economy_Master_Guide.md/.pdf and proposed_items.txt present', all(os.path.exists(p) for p in (MDP, PDFP, PBSP)))
MD = rd(MDP)

# ------------------------------------------------------------------ proposed_items.txt
print('== 2. proposed_items.txt (PBS syntax) ==')
raw = open(PBSP, 'rb').read()
check('UTF-8 with BOM, CRLF line endings only', raw[:3] == b'\xef\xbb\xbf' and raw.count(b'\r\n') == raw.count(b'\n'))
lines = [l for l in raw.decode('utf-8-sig').split('\r\n') if l.strip() and not l.startswith('#')]
ITEMS = {}      # sym -> dict
ORDER_IDS = []
problems = []
for l in lines:
    try:
        r = next(csv.reader([l]))
    except Exception as e:
        problems.append(('csv', l[:50])); continue
    if len(r) != 11:
        problems.append(('fields', l[:50], len(r))); continue
    try:
        i, sym, nm, pl, pk, pr, ds, fu, bu, sp = int(r[0]), r[1], r[2], r[3], int(r[4]), int(r[5]), r[6], int(r[7]), int(r[8]), int(r[9])
    except ValueError:
        problems.append(('int', l[:50])); continue
    if not re.fullmatch(r'[A-Z0-9]+', sym) or not nm or not pl or not ds or not (1 <= pk <= 8) or pr < 0 or '"' in ds or fu not in (0, 1, 2, 3, 4, 5) or bu not in (0, 1, 2) or sp not in (0, 1, 2, 3, 4, 5, 6):
        problems.append(('value', sym))
    ITEMS[sym] = dict(id=i, name=nm, plural=pl, pocket=pk, price=pr, desc=ds, fu=fu, bu=bu, sp=sp, move=r[10])
    ORDER_IDS.append(i)
check('every line parses (11 PBS fields, valid ranges, ASCII internal names, no quotes in descriptions)', not problems, str(problems[:4]))
check('IDs strictly ascending and unique; internal names unique', ORDER_IDS == sorted(set(ORDER_IDS)) and len(ITEMS) == len(ORDER_IDS), '%d items' % len(ITEMS))
check('display names unique', len({v['name'] for v in ITEMS.values()}) == len(ITEMS))
check('414 items, max ID 717', len(ITEMS) == 414 and max(ORDER_IDS) == 717, '%d items, max id %d' % (len(ITEMS), max(ORDER_IDS)))

# original database (read-only)
OR = {}
for l in rd(os.path.join(ROOT, 'PBS_backup_original', 'items.txt')).split('\n'):
    l = l.strip('\r')
    if not l or l.startswith('#'): continue
    r = next(csv.reader([l]))
    OR[r[1]] = dict(id=int(r[0]), name=r[2], pocket=int(r[4]))
kept = set(ITEMS) & set(OR)
new = set(ITEMS) - set(OR)
pruned = set(OR) - set(ITEMS)
check('every kept item keeps its original ID (save compatibility)', all(ITEMS[s]['id'] == OR[s]['id'] for s in kept))
check('43 new items use IDs 674-717 (692 is a free gap: no diving suit); 371 kept or restored; 280 pruned', len(new) == 43 and sorted(ITEMS[s]['id'] for s in new) == [i for i in range(674, 718) if i != 692] and len(kept) == 371 and len(pruned) == 280, '%d/%d/%d' % (len(new), len(kept), len(pruned)))
check('no HM (MO) and no pruned symbol in proposed_items.txt', not (pruned & set(ITEMS)) and not any(re.fullmatch(r'HM\d\d', s) for s in ITEMS))

# TMs vs proposed_tm.txt
tm_blocks = re.findall(r'^\[([A-Z0-9]+)\]', rd(os.path.join(D, 'proposed_tm.txt')), re.M)
MV = {}
for l in rd(os.path.join(D, 'proposed_moves.txt')).split('\n'):
    m = re.match(r'(\d+),([A-Z0-9]+),([^,]*),([^,]*),(\d+),([A-Z]+),(\w+),', l)
    if m: MV[m.group(2)] = dict(name=m.group(3), bp=int(m.group(5)), type=m.group(6), cat=m.group(7))
tm_items = [ITEMS.get('TM%02d' % n if n < 100 else 'TM100') for n in range(1, 101)]
check('100 TMs present (IDs 288-387) and bound, in order, to the 100 moves of proposed_tm.txt',
      None not in tm_items and [t['id'] for t in tm_items] == list(range(288, 388)) and [t['move'] for t in tm_items] == tm_blocks and len(tm_blocks) == 100)
check('every TM has FieldUse 3 and pocket 4; TM moves exist in proposed_moves.txt', all(t['fu'] == 3 and t['pocket'] == 4 and t['move'] in MV for t in tm_items))

# required content
STONES = 'FIRESTONE THUNDERSTONE WATERSTONE LEAFSTONE MOONSTONE SUNSTONE DUSKSTONE DAWNSTONE SHINYSTONE ICESTONE'.split()
chg = rd(os.path.join(D, 'Pokemon_Changes_Master.md'))
need_stones = set()
for l in chg.split('\n'):
    if l.startswith('- **Evolución:**'):
        v = re.sub(r'\(Antes:[^)]*\)', '', l.split(':**', 1)[1])
        need_stones |= set(re.findall(r'Piedra [A-Za-zÁ-ú]+', v))
names = {v['name'] for v in ITEMS.values()}
need_stones.discard('Piedra Oval')    # la Piedra Oval es un objeto de evolución por uso directo (Chansey), no una de las diez piedras
check('all evolution stones required by the final Pokedex (Pokemon_Changes_Master.md) exist: %s' % ', '.join(sorted(need_stones)), need_stones <= names and all(s in ITEMS for s in STONES) and len(need_stones) == 10, str(need_stones - names))
EVOITEMS = {'METALCOAT': 'Steelix Scizor', 'KINGSROCK': 'Politoed Slowking', 'DRAGONSCALE': 'Kingdra', 'UPGRADE': 'Porygon2', 'DUBIOUSDISC': 'Porygon-Z', 'PROTECTOR': 'Rhyperior', 'ELECTIRIZER': 'Electivire',
            'MAGMARIZER': 'Magmortar', 'REAPERCLOTH': 'Dusknoir', 'PRISMSCALE': 'Milotic', 'DEEPSEATOOTH': 'Huntail', 'DEEPSEASCALE': 'Gorebyss', 'RAZORFANG': 'Gliscor', 'RAZORCLAW': 'Weavile',
            'SACHET': 'Aromatisse', 'WHIPPEDDREAM': 'Slurpuff', 'OVALSTONE': 'Chansey'}
check('the 17 item-evolution items exist (category 5, Tier 3 list below), FieldUse 1 (used on the Pokemon like a stone) and keep their original PBS names', all(s in ITEMS and ITEMS[s]['fu'] == 1 and ITEMS[s]['pocket'] == 1 for s in EVOITEMS) and all(ITEMS[s]['name'] == OR[s]['name'] for s in EVOITEMS if s in OR) and len(EVOITEMS) == 17, str([s for s in EVOITEMS if s not in ITEMS]))
check('13 restored items keep their ORIGINAL PBS IDs', all(ITEMS[s]['id'] == OR[s]['id'] for s in 'DRAGONSCALE UPGRADE DUBIOUSDISC PROTECTOR ELECTIRIZER MAGMARIZER REAPERCLOTH PRISMSCALE OVALSTONE RAZORCLAW RAZORFANG SACHET WHIPPEDDREAM'.split()))
check('ABILITYPATCH (Parche Habilidad) and the diving suit (Traje de Buceo / DIVINGSUIT / DIVEGEAR) are absent from proposed_items.txt; Cápsula Habilidad stays',
      not any(x in ITEMS for x in ('ABILITYPATCH', 'DIVINGSUIT', 'DIVEGEAR')) and not any(n in names for n in ('Parche Habilidad', 'Traje de Buceo')) and 'ABILITYCAPSULE' in ITEMS
      and 'ABILITYPATCH' not in raw.decode('utf-8-sig') and 'DIVINGSUIT' not in raw.decode('utf-8-sig'))
check('POKEVIAL (716) and INFINITECANDY (717) exist as key items (pocket 8); Pokévial usable from the bag, Caramelo Infinito usable on a Pokémon', all(s in ITEMS and ITEMS[s]['pocket'] == 8 and ITEMS[s]['sp'] == 6 for s in ('POKEVIAL', 'INFINITECANDY')) and ITEMS['POKEVIAL']['id'] == 716 and ITEMS['INFINITECANDY']['id'] == 717 and ITEMS['POKEVIAL']['fu'] == 2 and ITEMS['INFINITECANDY']['fu'] == 1)
check('Caramelo Raro costs 100 and is usable on a Pokémon', ITEMS['RARECANDY']['price'] == 100 and ITEMS['RARECANDY']['fu'] == 1)
PPOKE = os.path.join(D, 'proposed_pokemon.txt')
if os.path.exists(PPOKE):
    ptxt0 = rd(PPOKE)
    evo_lines = re.findall(r'^Evolutions=(.*)$', ptxt0, re.M)
    item_evos = set()
    for ev in evo_lines:
        p_ = [x.strip() for x in ev.split(',')]
        for k in range(0, len(p_) - 2, 3):
            if p_[k + 1] in ('Item', 'ItemMale', 'ItemFemale'): item_evos.add(p_[k + 2])
    check('proposed_pokemon.txt: the 17 evolution items are used by Item evolutions and every Item,<OBJETO> in it exists in proposed_items.txt', set(EVOITEMS) <= item_evos and item_evos <= set(ITEMS), str((set(EVOITEMS) - item_evos, item_evos - set(ITEMS))))
else:
    check('proposed_pokemon.txt exists (delivered by the Pokedex pass)', False, 'missing')
frag = ['NIGHTMAREFRAG1', 'NIGHTMAREFRAG2', 'NIGHTMAREFRAG3', 'LUNARFRAG1', 'LUNARFRAG2', 'LUNARFRAG3']
check('6 fragments (Pesadilla I-III, Lunar I-III), Orbe del Sueño, Orbe de la Pesadilla, Hierba Calmante and Reloj Agrietado are key items', all(s in ITEMS and ITEMS[s]['sp'] == 6 and ITEMS[s]['pocket'] == 8 for s in frag + ['DREAMORB', 'NIGHTMAREORB', 'CALMHERB', 'CRACKEDWATCH']))
check('Psyduck item: Diadema Jaqueca (Psyduck, +50 % on five stats, no evolution)', 'PSYCROWN' in ITEMS and 'Psyduck' in ITEMS['PSYCROWN']['desc'] and '50 %' in ITEMS['PSYCROWN']['desc'] and 'no evoluciona' in ITEMS['PSYCROWN']['desc'])
modern = 'ABILITYCAPSULE ASSAULTVEST HEAVYDUTYBOOTS WEAKNESSPOLICY SAFETYGOGGLES THROATSPRAY ROOMSERVICE UTILITYUMBRELLA COVERTCLOAK CLEARAMULET LOADEDDICE MIRRORHERB PUNCHINGGLOVE EXPALL'.split()
mints = [s for s in ITEMS if s.endswith('MINT')]
check('modern competitive items present (Ability Capsule, Assault Vest, Boots, Policy, Goggles, Dice, Cloak, Amulet, Herb, Glove...) and 15 Mints',
      all(s in ITEMS for s in modern) and len(mints) == 15, str([s for s in modern if s not in ITEMS]))
check('renamed items use the requested Spanish names', ITEMS['SAFETYGOGGLES']['name'] == 'Gafas Protectoras' and ITEMS['UTILITYUMBRELLA']['name'] == 'Paraguas Multiuso' and ITEMS['THROATSPRAY']['name'] == 'Spray Bucal' and ITEMS['ROCKYHELMET']['name'] == 'Casco Dentado')
check('exactly four field key items replace the HMs (Tijeras, Pico, Guantes de Fuerza, Tabla de Surf); no Buceo', all(s in ITEMS and ITEMS[s]['pocket'] == 8 for s in ('SHEARS', 'PICKAXE', 'GLOVES', 'SURFBOARD')) and 'DIVEGEAR' not in ITEMS)

# ------------------------------------------------------------------ markdown parsing
print('== 3. Markdown structure ==')
def cells(line):
    s = line.strip()
    if s.startswith('|'): s = s[1:]
    if s.endswith('|') and not s.endswith('\\|'): s = s[:-1]
    return [c.replace('\\|', '|').replace('\\*', '').strip() for c in re.split(r'(?<!\\)\|', s)]
H1 = H2 = H3 = ''
TABLES = []     # dict(h1,h2,h3,header,rows)
paras = []      # (h1,h2,h3,text)
cur = None
fence = False
src = MD.split('\n')
i = 0
while i < len(src):
    ln = src[i]
    m = re.match(r'^(#{1,3})\s+(.*)$', ln)
    if m:
        lv, tx = len(m.group(1)), m.group(2).replace('\\*', '').strip()
        if lv == 1: H1, H2, H3 = tx, '', ''
        elif lv == 2: H2, H3 = tx, ''
        else: H3 = tx
        i += 1; continue
    if ln.strip().startswith('|'):
        blk = []
        while i < len(src) and src[i].strip().startswith('|'):
            blk.append(src[i]); i += 1
        rows = [cells(b) for b in blk if not re.match(r'^\s*\|?\s*:?-{2,}', b)]
        TABLES.append(dict(h1=H1, h2=H2, h3=H3, header=rows[0], rows=rows[1:]))
        continue
    if ln.strip() and not ln.startswith('<!--'):
        paras.append((H1, H2, H3, ln))
    i += 1
h1s = [t for t in re.findall(r'^# (.*)$', MD, re.M)]
check('six chapters plus guide and appendix (H1 structure)', [h.split(' — ')[0] for h in h1s if h.startswith('Cap')] == ['Capítulo %d' % k for k in range(1, 7)] and h1s[0] == 'Guía de lectura' and h1s[-1].startswith('Apéndice'), str(h1s))
check('document is in Spanish (no English sentences in prose)', not [p for p in paras if len(re.findall(r'\b(the|and|with|which|that|this|from|are|have)\b', p[3])) >= 3], '')

def chap(n): return [t for t in TABLES if t['h1'].startswith('Capítulo %d' % n)]
def find_table(h1n, header0, h2=None):
    return [t for t in chap(h1n) if t['header'][0] == header0 and (h2 is None or t['h2'].startswith(h2))]

# catalogue names (name -> sym), TMs by number
BYNAME = {v['name']: s for s, v in ITEMS.items() if not re.fullmatch(r'TM\d+', s)}
BYID = {v['id']: s for s, v in ITEMS.items()}
def sym_of(cell):
    m = re.match(r'^MT(\d{2,3})\s*·', cell)
    if m: return 'TM%02d' % int(m.group(1)) if int(m.group(1)) < 100 else 'TM100'
    return BYNAME.get(cell)

# ------------------------------------------------------------------ Chapter 2 catalogue
print('== 4. Chapter 2: catalogue ==')
cat_rows = [r for t in chap(2) if t['header'][:3] == ['ID', 'Nombre', 'Categoría'] for r in t['rows']]
cat_ids = [int(r[0]) for r in cat_rows]
non_tm_ids = sorted(v['id'] for s, v in ITEMS.items() if not re.fullmatch(r'TM\d+', s))
check('catalogue lists every non-TM item exactly once (314 items) and nothing else', sorted(cat_ids) == non_tm_ids, '%d rows' % len(cat_ids))
check('catalogue names and IDs match proposed_items.txt', all(ITEMS[BYID[int(r[0])]]['name'] == r[1] for r in cat_rows))
check('catalogue has the seven required columns', all(t['header'] == ['ID', 'Nombre', 'Categoría', 'Rareza', 'Precio Compra/Venta', 'Efecto Exacto', 'Método de Obtención'] for t in chap(2) if t['header'][0] == 'ID'))
TIER = {}
for r in cat_rows:
    t = r[3]
    TIER[BYID[int(r[0])]] = 'K' if t.startswith('Clave') else '1' if t.startswith('Tier 1') else '2' if t.startswith('Tier 2') else '3' if t.startswith('Tier 3') else 'L' if t.startswith('Legend') else '?'
check('every catalogue row has a valid rarity', '?' not in TIER.values())
for s in ITEMS:
    if re.fullmatch(r'TM\d+', s): TIER[s] = '1'
check('14 Tier 1 combat items + 8 species items (Deep Sea items moved to Tier 3) = 22 Tier 1 (without TMs); 29 legendary; 31 key (incl. Pokévial and Caramelo Infinito)', sum(1 for s, t in TIER.items() if t == '1' and not re.fullmatch(r'TM\d+', s)) == 22 and sum(1 for t in TIER.values() if t == 'L') == 29 and sum(1 for t in TIER.values() if t == 'K') == 31)
check('Chapter 2 gives the 10 category sections (Objetos Clave ... MT01–MT100) and an isolated legendary section', len(re.findall(r'^## 2\.(?:[1-9]|10) ', MD, re.M)) == 10 and '### 2.7.2 Objetos de Legendarios (aislados, solo postgame)' in MD)

# ------------------------------------------------------------------ Chapter 4: TMs
print('== 5. Chapter 4: the 100 TMs ==')
t4 = [t for t in chap(4) if t['header'][0] == 'MT'][0]
check('Chapter 4 table has the required columns', t4['header'] == ['MT', 'Movimiento', 'Tipo', 'Cat.', 'Poder', 'Ubicación', 'Método', 'Justificación'], str(t4['header']))
nums = [int(r[0][2:]) for r in t4['rows']]
check('every TM (MT01-MT100) appears exactly once in Chapter 4', sorted(nums) == list(range(1, 101)))
TYES = {'NORMAL': 'Normal', 'FIRE': 'Fuego', 'WATER': 'Agua', 'ELECTRIC': 'Eléctrico', 'GRASS': 'Planta', 'ICE': 'Hielo', 'FIGHTING': 'Lucha', 'POISON': 'Veneno', 'GROUND': 'Tierra', 'FLYING': 'Volador',
        'PSYCHIC': 'Psíquico', 'BUG': 'Bicho', 'ROCK': 'Roca', 'GHOST': 'Fantasma', 'DRAGON': 'Dragón', 'DARK': 'Siniestro', 'STEEL': 'Acero', 'FAIRY': 'Hada'}
CATES = {'Physical': 'Físico', 'Special': 'Especial', 'Status': 'Estado'}
bad = []
for r in t4['rows']:
    n = int(r[0][2:]); mv = MV[tm_blocks[n - 1]]
    exp_p = '—' if mv['cat'] == 'Status' else ('Var.' if mv['bp'] <= 1 else str(mv['bp']))
    if [r[1], r[2], r[3], r[4]] != [mv['name'], TYES[mv['type']], CATES[mv['cat']], exp_p]:
        bad.append((r[0], r[1:5]))
check('Chapter 4 move, type, category and power match proposed_moves.txt / proposed_tm.txt for all 100 TMs', not bad, str(bad[:3]))

# ------------------------------------------------------------------ Chapter 5: distribution
print('== 6. Chapter 5: distribution by location ==')
sec5 = []   # (location, act, header_para, header, rows)
cur_act = ''
t5 = [t for t in chap(5) if t['header'][0] == '#']
check('Chapter 5 tables have the required columns', all(t['header'] == ['#', 'Objeto/MT', 'Método', 'Coordenada/Zona conceptual', 'Notas'] for t in t5))
LOCS = [t['h3'] for t in t5]
check('64 locations, each with its own table, all distinct', len(LOCS) == 64 and len(set(LOCS)) == 64, str(len(LOCS)))
v6 = rd(os.path.join(D, '6_World_and_Locations_Master_Guide.md'))
check('every location name exists in Volume 6 (same canon names)', all(l in v6 for l in LOCS), str([l for l in LOCS if l not in v6]))
OLDN = ['Pueblo Cianita', 'Pueblo Topacio', 'Granja Ambarina', 'Bosque Turmalino']
NEWN = ['Pueblo Iolita', 'Pueblo Heliodoro', 'Granja Apatita', 'Bosque Dioptasa']
check('the four renamed locations: old names absent from Volume 9 and new names present as Chapter 5 sections and in Volume 6', not any(o in MD for o in OLDN) and all(n in LOCS for n in NEWN) and all(n in v6 for n in NEWN), str([o for o in OLDN if o in MD]))
ACT_OF = {}
for t in t5:
    ACT_OF[t['h3']] = t['h2'].split(' — ')[0]
check('five act groupings (Acto I-V) with 14/14/15/11/10 locations', [sum(1 for l in LOCS if ACT_OF[l] == a) for a in ('Acto I', 'Acto II', 'Acto III', 'Acto IV', 'Acto V y postgame')] == [14, 14, 15, 11, 10])
MAPM, MISM, SHOPM = set('BHC'), set('NEJP'), set('S')
cnt = collections.defaultdict(lambda: dict(map=0, mis=0, shop=0, locs=collections.Counter(), rows=[]))
bad_rows = []
declared = {}
for ln in MD.split('\n'):
    m = re.match(r'^\*\*(.*?)\*\* — (\d+) filas \((\d+) MT; mapa (\d+), PNJ/misión (\d+), tienda única (\d+)\)', ln)
    if m: declared.setdefault('list', []).append(tuple(int(x) for x in m.groups()[1:]))
for k, t in enumerate(t5):
    q = [0, 0, 0, 0, 0]
    for r in t['rows']:
        mm = re.match(r'^(.*?)(?: ×(\d+))?$', r[1])
        nm, qty = mm.group(1), int(mm.group(2) or 1)
        s = sym_of(nm)
        if not s or r[2] not in 'BHCNEJPS' or len(r[2]) != 1:
            bad_rows.append((t['h3'], r[1], r[2])); continue
        c = cnt[s]
        m = r[2]
        if m in MAPM: c['map'] += qty; q[2] += qty
        elif m in MISM: c['mis'] += qty; q[3] += qty
        else: c['shop'] += qty; q[4] += qty
        c['locs'][t['h3']] += qty; c['rows'].append((t['h3'], m, r))
        if re.fullmatch(r'TM\d+', s): q[1] += 1
    q[0] = len(t['rows'])
    if declared.get('list') and k < len(declared['list']) and declared['list'][k] != tuple(q):
        bad_rows.append(('summary-mismatch', t['h3'], declared['list'][k], tuple(q)))
check('every Chapter 5 row names a catalogue item with a valid method code, and each location summary line matches its table', not bad_rows and len(declared.get('list', [])) == 64, str(bad_rows[:3]))
check('every TM appears exactly once in Chapter 5', all((cnt['TM%02d' % n if n < 100 else 'TM100']['map'] + cnt['TM%02d' % n if n < 100 else 'TM100']['mis'] + cnt['TM%02d' % n if n < 100 else 'TM100']['shop']) == 1 for n in range(1, 101)))
# TM location chapter 4 == chapter 5
loc4 = {int(r[0][2:]): r[5] for r in t4['rows']}
loc5 = {}
for s, c in cnt.items():
    if re.fullmatch(r'TM\d+', s):
        loc5[int(s[2:])] = list(c['locs'])[0]
check('the TM location in Chapter 4 equals the location section of Chapter 5, for all 100 TMs', loc4 == loc5, str([(n, loc4[n], loc5.get(n)) for n in loc4 if loc4[n] != loc5.get(n)][:3]))
act_tab = [t for t in chap(4) if t['header'][0] == 'Acto'][0]
act_nums = [int(r[1]) for r in act_tab['rows'] if r[1].isdigit()]
check('Chapter 4.1 gives the TMs per act and they add up to 100 (Acts I-V)', len(act_nums) == 5 and sum(act_nums) == 100 and act_nums[0] >= 10, str(act_nums))
tm_act = {}
for n, l in loc5.items():
    tm_act[n] = 5 if n in (93, 100) else ['Acto I', 'Acto II', 'Acto III', 'Acto IV', 'Acto V y postgame'].index(ACT_OF[l]) + 1
PRIORITY = {'AQUAJET', 'ICESHARD', 'SUCKERPUNCH'}
def mvof(n): return MV[tm_blocks[n - 1]]
def offensive(n): return mvof(n)['cat'] != 'Status'
viol = []
for n in range(1, 101):
    a, mv, sym = tm_act[n], mvof(n), tm_blocks[n - 1]
    if a == 1 and ((offensive(n) and mv['bp'] >= 75) or sym in PRIORITY or sym in ('SUBSTITUTE', 'TOXIC')): viol.append(('A1', n, sym))
    if a <= 2 and offensive(n) and mv['bp'] >= 85: viol.append(('<A3 BP>=85', n, sym))
    if a == 2 and offensive(n) and mv['bp'] > 80: viol.append(('A2 BP>80', n, sym))
    if a == 1 and offensive(n) and mv['bp'] > 65 and n != 6: viol.append(('A1 BP>65', n, sym))
a2_80 = [n for n in range(1, 101) if tm_act[n] == 2 and offensive(n) and mvof(n)['bp'] == 80]
check('tactical TM curve: Act I has no offensive TM >= 75 BP (only MT06 at 70), no priority TM, no Sustituto/Tóxico; no offensive TM >= 85 BP before Act III; Act II holds at most one 80 BP TM', not viol and len(a2_80) <= 1, str(viol[:4] + a2_80))
check('priority TMs (Aqua Jet, Canto Helado, Golpe Bajo) sit in Act II or later', all(tm_act[n] >= 2 for n in range(1, 101) if tm_blocks[n - 1] in PRIORITY) and sum(1 for n in range(1, 101) if tm_blocks[n - 1] in PRIORITY) == 3)
check('Sustituto and Tóxico sit in Act III or later', tm_act[2] >= 3 and tm_act[5] >= 3, str((tm_act[2], tm_act[5])))
gym_exp = [(6, 'Ciudad Calcedonia'), (11, 'Ciudad Calaíta'), (72, 'Ciudad Magnetita'), (50, 'Ciudad Nefrita'), (29, 'Ciudad Azabache'), (16, 'Ciudad Venturina'), (48, 'Ciudad Alabastro'), (79, 'Ciudad Rejalgar')]
gym_ok = all(loc5[n] == l and any(x[1] == 'J' for x in cnt['TM%02d' % n]['rows']) for n, l in gym_exp)
bps = [mvof(n)['bp'] for n, _ in gym_exp]
check('the 8 gym TMs are MT06, MT11, MT72, MT50, MT29, MT16, MT48, MT79 and scale from 65-70 BP to 110 BP', gym_ok and bps[-1] == 110 and bps[0] <= 70 and bps[3] == bps[4] == bps[2] == 75 and bps[6] == 90, str(bps))
check('Chapter 4 counter-tooling table: every listed type has at least one TM before each combat',
      all(len(r[2].split(' | ')) == len(r[1].split(' · ')) and all(re.search(r'MT\d\d', p) for p in r[2].split(' | ')) for t in chap(4) if t['header'][0] == 'Combate' for r in t['rows']) and sum(len(t['rows']) for t in chap(4) if t['header'][0] == 'Combate') == 14)
# counter-tooling positions: every MT listed must be located before the combat
ORDER_LOCS = LOCS
pos = {l: k for k, l in enumerate(ORDER_LOCS)}
comb_loc = {'Gimnasio 1': 'Ciudad Calcedonia', 'Gimnasio 2': 'Ciudad Calaíta', 'Gimnasio 3': 'Ciudad Magnetita', 'Gimnasio 4': 'Ciudad Nefrita', 'Gimnasio 5': 'Ciudad Azabache',
            'Gimnasio 6': 'Ruta 15', 'Gimnasio 7': 'Ciudad Alabastro', 'Gimnasio 8': 'Ciudad Rejalgar', 'Dominante Eléctrico': 'Central Fulgurita', 'Dominante Veneno': 'Ruinas Atacamita',
            'Dominante Hada': 'Cascadas Travertinas', 'Dominante Fantasma': 'Villa Adularia', 'Dominante Dragón': 'Templo Moldavita', 'Monte Azogue': 'Monte Azogue'}
late = []
for t in chap(4):
    if t['header'][0] != 'Combate': continue
    for r in t['rows']:
        key = next(k for k in comb_loc if r[0].startswith(k))
        lim = pos[comb_loc[key]] + (0.5 if key == 'Gimnasio 6' else 0)
        for n in re.findall(r'MT(\d\d)', r[2]):
            p = pos[loc4[int(n)]]
            if not (p < lim or (key == 'Gimnasio 6' and p <= pos['Ruta 15'])):
                late.append((key, n))
check('every counter-tooling TM is placed before the combat it prepares (gyms 1-8, five Dominants, Monte Azogue)', not late, str(late[:3]))

# ------------------------------------------------------------------ Chapter 6
print('== 7. Chapter 6: global frequency / rarity control ==')
t6 = [t for t in chap(6) if t['header'][0] == 'Nombre']
check('Chapter 6 tables have the required columns', all(t['header'] == ['Nombre', 'Categoría', 'Copias en Mapa', 'Copias por Misión/NPC', '¿Tienda?', 'Total', 'Ubicaciones'] for t in t6))
rows6 = {}
dup6 = []
for t in t6:
    for r in t['rows']:
        s = sym_of(r[0])
        if s in rows6: dup6.append(r[0])
        rows6[s] = r
check('Chapter 6 lists every one of the 414 items exactly once', len(rows6) == 414 and not dup6 and None not in rows6 and set(rows6) == set(ITEMS), '%d rows' % len(rows6))
def tot(r):
    m = re.fullmatch(r'(\d+)(\+∞)?', r[5]); return int(m.group(1)), bool(m.group(2))
mism = []
for s, r in rows6.items():
    c = cnt[s]
    shop = r[4]
    exp_tot = c['map'] + c['mis'] + c['shop']
    n, inf = tot(r)
    if int(r[2]) != c['map'] or int(r[3]) != c['mis'] or n != exp_tot or inf != (shop == 'Infinito') or (c['shop'] and shop == 'No'):
        mism.append((s, r[2:6], (c['map'], c['mis'], c['shop'])))
check('Chapter 6 columns agree, item by item, with an independent recount of the Chapter 5 rows', not mism, str(mism[:3]))
t1 = [s for s in ITEMS if TIER[s] == '1']
bad1 = [(s, rows6[s][5]) for s in t1 if rows6[s][5] not in ('1',) and not (s == 'FOCUSSASH' and rows6[s][5] == '1+∞')]
check('every Tier 1 item (100 TMs + 22 elite/species items) has exactly 1 copy (Banda Focus: 1 + postgame shop)', not bad1 and len(t1) == 122, str(bad1[:4]))
check('all 100 TMs have map/mission/shop total = 1 and no infinite shop', all(rows6['TM%02d' % n if n < 100 else 'TM100'][5] == '1' for n in range(1, 101)))
badL = [(s, rows6[s][5]) for s in ITEMS if TIER[s] in ('L', 'K') and rows6[s][5] != '1']
check('every key item and every legendary item has exactly 1 copy', not badL and sum(1 for s in ITEMS if TIER[s] in ('L', 'K')) == 60, str(badL[:3]))
bad2 = [(s, rows6[s][5]) for s in ITEMS if TIER[s] == '2' and s != 'MASTERBALL' and not (2 <= tot(rows6[s])[0] <= 5)]
check('every Tier 2 item has 2-5 copies in map/missions (Master Ball: exactly 1)', not bad2 and rows6['MASTERBALL'][5] == '1', str(bad2[:3]))
bad3 = [s for s in ITEMS if TIER[s] == '3' and tot(rows6[s])[0] == 0 and rows6[s][4] != 'Infinito']
check('every Tier 3 item can be obtained (map copy or infinite shop)', not bad3, str(bad3[:3]))
check('Tier 1 shop rule: elite items are never infinite (except Banda Focus after the League)', all(rows6[s][4] in ('No', 'Stock Único') for s in t1 if s != 'FOCUSSASH') and rows6['FOCUSSASH'][4] == 'Infinito')
exp_loc = {'LEFTOVERS': 'Desierto Halita', 'EVIOLITE': 'Senda Serpentina', 'ROCKYHELMET': 'Pueblo Casiterita', 'ASSAULTVEST': 'Ciudad Azabache', 'HEAVYDUTYBOOTS': 'Ciudad Azabache', 'LOADEDDICE': 'Ciudad Azabache',
           'FOCUSSASH': 'Cascadas Travertinas', 'WEAKNESSPOLICY': 'Ruta 16', 'COVERTCLOAK': 'Villa Adularia', 'CLEARAMULET': 'Ciudad Alabastro', 'LIFEORB': 'Templo Moldavita', 'CHOICEBAND': 'Ruta 20',
           'CHOICESPECS': 'Pueblo Iolita', 'CHOICESCARF': 'Calzada Corindón', 'PSYCROWN': 'Lago Amatista', 'MASTERBALL': 'Monte Azogue'}
badp = [(s, list(cnt[s]['locs']), l) for s, l in exp_loc.items() if list(cnt[s]['locs']) != [l]]
check('Tier 1 placements follow the design brief (Restos in the desert, Vidasfera in the temple, Chaleco/Botas in the Azabache mall, Psyduck item at Lago Amatista...)', not badp, str(badp[:3]))
shop_methods = {s: [r[1] for r in cnt[s]['rows']] for s in cnt}
check('Casco Dentado, Chaleco Asalto, Botas Gruesas and Dado Trucado are single-stock shop copies', all(shop_methods[s] == ['S'] for s in ('ROCKYHELMET', 'ASSAULTVEST', 'HEAVYDUTYBOOTS', 'LOADEDDICE')))

# ------------------------------------------------------------------ pruned items must not appear in distribution
print('== 8. Pruned items ==')
pr_names = {s: OR[s]['name'] for s in pruned}
sec1 = [t for t in chap(1) if t['h2'].startswith('1.2')]
listed = set()
for t in sec1:
    for r in t['rows']:
        for n in r[3].split(', '): listed.add(n.strip())
def is_listed(s): return pr_names[s] in listed or ('%s [%s]' % (pr_names[s], s)) in listed
RETIRED = {'ABILITYPATCH'}      # objeto retirado por decisión de diseño: no figura (ni su nombre) en el volumen
check('the discard table (1.2) lists the 279 pruned items by name (ambiguous names carry their symbol); the 280th original item is retired and not named: 651 = 279 + 371 + 1', len(sec1) == 1 and len(pruned) == 280 and (pruned & RETIRED) == RETIRED and all(is_listed(s) for s in pruned - RETIRED) and len(OR) == 651 and len(pruned) - len(RETIRED) + len(kept) + len(RETIRED) == 651 and '**279 descartados**' in MD and '**371 conservados o restaurados**' in MD and '**1 retirado**' in MD, str([s for s in pruned - RETIRED if not is_listed(s)][:5]))
kept_names = sorted(names, key=len, reverse=True)
scan_chunks = []
NAMECOL = {'ID': 1, 'Nombre': 0, '#': 1, 'Objetos': 0, 'Medallas': 1, 'N.º': 5}
for t in TABLES:
    if re.match(r'Capítulo [2-6]', t['h1']) and not t['h2'].startswith('6.4') and t['header'][0] in NAMECOL:
        k = NAMECOL[t['header'][0]]
        for r in t['rows']:
            scan_chunks.append(r[k])
hits = []
for ch in scan_chunks:
    t = ch
    for kn in kept_names:
        t = t.replace(kn, '·')
    for pn in set(pr_names.values()):
        if re.search(r'(?<![\wÁ-ú])%s(?![\wÁ-ú])' % re.escape(pn), t):
            hits.append((pn, ch[:60]))
check('no discarded item name appears in Chapters 2-6 (catalogue, shops, TMs, locations, control table)', not hits, str(hits[:4]))
check('no pruned item is bought, placed or listed by symbol in the placement tables', not [s for s in cnt if s in pruned])

# ------------------------------------------------------------------ shops & missions
print('== 9. Shops and Pía missions ==')
mart = [t for t in chap(3) if t['header'][0] == 'Medallas']
check('standard Poké Mart table covers 0-8 badges, cumulative', len(mart) == 1 and [r[0] for r in mart[0]['rows']] == [str(k) for k in range(9)])
shops = [t for t in chap(3) if t['header'][0] == 'Objetos']
shop_names = [t['h3'] for t in shops]
need = ['Mercader Ambulante', 'Casino de Azabache', 'Centro Comercial de Azabache', 'Herbolario de Venturina', 'Mercado Minero', 'Especialidades Termales', 'Tienda de la Liga', 'Mercado del Puerto']
check('the special shops exist (Mercader Pedernal, Azabache casino and mall, Herbolario Venturina, Mercado Minero, Termas Rejalgar, Tienda de la Liga)', all(any(n in s for s in shop_names) for n in need), str(shop_names))
single = set()
for t in shops:
    for r in t['rows']:
        if r[2] == 'Stock único':
            for n in r[0].split(', '):
                single.add(sym_of(n.strip()))
placed_S = {s for s, c in cnt.items() if c['shop']}
check('items with a single-stock shop line in Chapter 3 are exactly the "S" rows of Chapter 5', single == placed_S and None not in single, str(single ^ placed_S))
infinite_items = set()
for t in shops:
    for r in t['rows']:
        if r[2] == 'Infinito':
            for n in re.sub(r'^\d+ bayas: ', '', r[0]).split(', '):
                s = sym_of(n.strip())
                if s: infinite_items.add(s)
mart_items = set()
for r in mart[0]['rows']:
    for n in re.findall(r'([^,()]+?) \(\d[\d ]*\)', r[1]):
        s = sym_of(n.strip())
        if s: mart_items.add(s)
check('every item shown as "Infinito" in Chapter 6 is sold in an infinite shop of Chapter 3 and vice versa', {s for s, r in rows6.items() if r[4] == 'Infinito'} == infinite_items | mart_items, str(({s for s, r in rows6.items() if r[4] == 'Infinito'} ^ (infinite_items | mart_items))))
check('Caramelo Raro is sold in the standard Poké Mart from 0 medals at 100 (Tier 3, infinite stock)', 'RARECANDY' in {sym_of(n.strip()) for n in re.findall(r'([^,()]+?) \(\d[\d ]*\)', mart[0]['rows'][0][1])} and TIER['RARECANDY'] == '3' and 'Caramelo Raro (100)' in mart[0]['rows'][0][1] and rows6['RARECANDY'][4] == 'Infinito')
ev_bad = [(s_, TIER[s_], rows6[s_][4], rows6[s_][5]) for s_ in EVOITEMS if TIER[s_] != '3' or rows6[s_][4] != 'Infinito' or int(rows6[s_][2]) < 1]
cat5 = [r for t in chap(2) if t['header'][:3] == ['ID', 'Nombre', 'Categoría'] for r in t['rows'] if r[2] == 'Evolución']
check('the 17 evolution items are Tier 3 with an infinite shop (Centro Comercial de Azabache or Mercado Minero) and at least one map copy; all in category 5', not ev_bad and {BYID[int(r[0])] for r in cat5} >= set(EVOITEMS), str(ev_bad[:3]))
sold_in = collections.defaultdict(set)
for t in shops:
    for r in t['rows']:
        if r[2] == 'Infinito':
            for n in r[0].split(', '):
                s2 = sym_of(n.strip())
                if s2 in EVOITEMS: sold_in[s2].add(t['h3'].split(' — ')[0])
check('every evolution item is sold only in the Centro Comercial de Azabache and/or the Mercado Minero (METALCOAT in the mall type-booster row)', set(sold_in) == set(EVOITEMS) and all(v <= {'Centro Comercial de Azabache', 'Mercado Minero'} for v in sold_in.values()), str({k: v for k, v in sold_in.items() if not v <= {'Centro Comercial de Azabache', 'Mercado Minero'}}))
pv_tab = [t for t in chap(3) if t['header'][0] == 'Cargas']
check('Pokévial progression table: 1 charge (Act I, Amparo), 2 charges (Act III, Pía mission 6), 3 charges (Act IV, Pía mission 17); the key item has exactly 1 copy', len(pv_tab) == 1 and [r[0] for r in pv_tab[0]['rows']] == ['1', '2', '3'] and [r[1] for r in pv_tab[0]['rows']] == ['I', 'III', 'IV'] and 'n.º 6' in pv_tab[0]['rows'][1][2] and 'n.º 17' in pv_tab[0]['rows'][2][2] and rows6['POKEVIAL'][5] == '1' and rows6['INFINITECANDY'][5] == '1' and ACT_OF[list(cnt['POKEVIAL']['locs'])[0]] == 'Acto I' and ACT_OF[list(cnt['INFINITECANDY']['locs'])[0]] == 'Acto I')
pia = [t for t in chap(3) if t['header'][0] == 'N.º']
check('Pía missions table exists with at least 20 missions', len(pia) == 1 and len(pia[0]['rows']) >= 20, str(len(pia[0]['rows']) if pia else 0))
rew = collections.Counter()
mis_bad = []
for r in pia[0]['rows']:
    no = int(r[0])
    s = sym_of(r[5].split(' + ')[0].split(' ×')[0])
    rew[s] += 1
    found = [x for x in cnt.get(s, {'rows': []})['rows'] if 'Misión n.º %d de Pía' % no in x[2][3]]
    if not found: mis_bad.append((no, r[5]))
check('every Pía mission reward is placed exactly as a P/E row of Chapter 5 that cites the mission number', not mis_bad, str(mis_bad[:3]))
check('Pía rewards cover evolution stones, Mints, Ability Capsule/Patch, a Tier 1 competitive item and the Psyduck item',
      any('STONE' in s for s in rew) and any(s.endswith('MINT') for s in rew) and 'ABILITYCAPSULE' in rew and 'CHOICESPECS' in rew and 'PSYCROWN' in rew and 'SACREDASH' in rew)
check('story key items are placed once: 6 fragments, 2 orbs, Hierba Calmante, Reloj Agrietado, the 4 seals, the 4 field tools, Pokévial and Caramelo Infinito', all(sum(cnt[s][k] for k in ('map', 'mis', 'shop')) == 1 for s in frag + ['DREAMORB', 'NIGHTMAREORB', 'CALMHERB', 'CRACKEDWATCH', 'SEALCRYSTAL', 'SEALABYSS', 'SEALGLACIER', 'SEALVOLCANO', 'SHEARS', 'PICKAXE', 'GLOVES', 'SURFBOARD', 'POKEVIAL', 'INFINITECANDY']))
POST = {'Gruta Hialina', 'Gruta Azurita', 'Gruta Labradorita', 'Gruta Pirita', 'Pueblo Esteatita', 'Ruinas Atacamita', 'Isla Opalina', 'Isla Obsidiana', 'Reserva Peridoto', 'Lago Amatista'}
check('legendary items are isolated in postgame zones (4 grottoes, mountain village, hidden lab, island altars, Reserva, Lago)', all(l in POST for s in ITEMS if TIER[s] == 'L' for l in cnt[s]['locs']) and all(all(x[1] in 'ECH' for x in cnt[s]['rows']) for s in ITEMS if TIER[s] == 'L'))
# act curve
curve = []
MACT = {int(r[0]): {'I': 'Acto I', 'II': 'Acto II', 'III': 'Acto III', 'IV': 'Acto IV', 'V': 'Acto V y postgame'}[r[1]] for r in pia[0]['rows']}
for s_, c in cnt.items():
    for (l, m, r) in c['rows']:
        a = ACT_OF[l]
        mm = re.search(r'Misión n\.º (\d+) de Pía', r[3])
        if mm: a = MACT[int(mm.group(1))]
        if s_ in ('FULLRESTORE', 'MAXREVIVE', 'MAXELIXIR', 'LIFEORB') and a in ('Acto I', 'Acto II', 'Acto III'): curve.append((s_, l))
        if s_ == 'ULTRABALL' and a == 'Acto I': curve.append((s_, l))
        if s_.endswith('MINT') and a in ('Acto I', 'Acto II'): curve.append((s_, l))
r1 = {sym_of(re.sub(r' ×\d+$', '', r[1])) for t in t5 if t['h3'] == 'Ruta 1' for r in t['rows']}
check('act curve: no Restaura Todo, Revivir Máximo, Elixir Máximo or Vidasfera before Act IV; no Ultra Ball in Act I; no Mints before Act III; Route 1 has no Restaura Todo, Ultra Ball or Vidasfera', not curve and not (r1 & {'FULLRESTORE', 'ULTRABALL', 'LIFEORB'}), str(curve[:3]))

# ------------------------------------------------------------------ PDF
print('== 9b. Evolution objects, Poké Mart locations, banned words ==')
evt = [t for t in chap(2) if t['header'][0] == 'Objeto de evolución']
EVO27 = STONES + list(EVOITEMS)
if os.path.exists(PPOKE) and len(evt) == 1:
    secs_ = []
    cs = None
    for l_ in rd(PPOKE).split('\n'):
        l_ = l_.rstrip('\r')
        if re.match(r'^\[\d+\]$', l_):
            cs = {}; secs_.append(cs); continue
        if cs is not None and '=' in l_ and not l_.startswith('#'):
            k_, v_ = l_.split('=', 1); cs[k_] = v_
    nm_of = {x['InternalName']: x['Name'] for x in secs_}
    src_ev = collections.defaultdict(list)
    for x in secs_:
        pe = [y.strip() for y in x.get('Evolutions', '').split(',')] if x.get('Evolutions') else []
        for k in range(0, len(pe) - 2, 3):
            if pe[k + 1] in ('Item', 'ItemMale', 'ItemFemale'): src_ev[pe[k + 2]].append('%s → %s%s' % (x['Name'], nm_of[pe[k]], {'ItemMale': ' (macho)', 'ItemFemale': ' (hembra)'}.get(pe[k + 1], '')))
    body = [r for r in evt[0]['rows'] if 'Total' not in r[0]]
    tot_row = [r for r in evt[0]['rows'] if 'Total' in r[0]][0]
    names27 = {ITEMS[s_]['name'] for s_ in EVO27}
    n_st = sum(len(src_ev[s_]) for s_ in STONES); n_it = sum(len(src_ev[s_]) for s_ in EVOITEMS)
    ok_rows = len(body) == 27 and {r[0] for r in body} == names27
    ok_ev = all(set(r[4].split(' · ')) == set(src_ev[BYNAME[r[0]]]) and int(r[5]) == len(src_ev[BYNAME[r[0]]]) for r in body)
    ok_tot = tot_row[5].strip('*') == str(n_st + n_it) and ('%d evoluciones por piedra + %d por objeto' % (n_st, n_it)) in tot_row[4]
    check('Section 2.5.1: one table of the 27 evolution objects (10 stones + 17 objects incl. Piedra Oval) with the species of every Item,<SÍMBOLO> evolution from proposed_pokemon.txt (%d by stone + %d by object = %d)' % (n_st, n_it, n_st + n_it),
          ok_rows and ok_ev and ok_tot and set(src_ev) == set(EVO27), str((ok_rows, ok_ev, ok_tot, set(src_ev) ^ set(EVO27))))
    check('Category 5 has 28 entries = the 27 evolution objects + Piedra Eterna; Piedra Oval sits with the other evolution objects; the text says 27 evolution objects (not 28)',
          len(cat5) == 28 and {BYID[int(r[0])] for r in cat5} == set(EVO27) | {'EVERSTONE'} and 'Piedra Oval' in {r[1] for r in cat5} and 'Hay por tanto **27 objetos que evolucionan Pokémon**' in MD)
else:
    check('Section 2.5.1 evolution objects table and proposed_pokemon.txt are present', False, 'missing')
mt = [t for t in chap(3) if t['header'][0] == 'Población']
check('Section 3.2.1: Poké Mart standard in 14 of the 16 settlements (all cities and towns except Pedernal, replaced by the Mercader Ambulante, and Monte Azogue)', len(mt) == 1 and len(mt[0]['rows']) == 16 and sum(1 for r in mt[0]['rows'] if r[2] == 'Sí') == 14 and [r[0] for r in mt[0]['rows'] if r[2] != 'Sí'] == ['Pueblo Pedernal', 'Monte Azogue'], str([r[:3] for r in mt[0]['rows']][:3]) if mt else 'no table')
BAN = re.compile(r'Parche|Traje de Buceo|ABILITYPATCH|DIVEGEAR|DIVINGSUIT|[Bb]ucear|[Bb]uceo(?! Ball)|ability patch|diving suit', re.I)
md_hits = BAN.findall(MD.replace('Buceo Ball', 'Ball'))
check('banned words (Parche Habilidad, Traje de Buceo, ABILITYPATCH, DIVEGEAR, DIVINGSUIT, any Buceo other than the Buceo Ball Poké Ball) appear nowhere in the Volume 9 markdown', not md_hits, str(md_hits[:4]))
raw_all = raw.decode('utf-8-sig')
check('and nowhere in proposed_items.txt (including its comments)', not BAN.findall(raw_all.replace('Buceo Ball', 'Ball')) and 'DIVEBALL' in ITEMS, str(BAN.findall(raw_all)[:3]))
SPB = re.compile(r'(Murkrow Dominante|\\bLairon\\b|\\bAggron\\b|Dominante[^|\n]{0,40}\b(Murkrow|Chansey|Gyarados|Lucario|Archeops|Roserade|Froslass|Arcanine|Alakazam|Blaziken|Bronzong|Chandelure|Umbreon|Magnezone|Salamence|Dragonite)\b|\bAce\b[^|\n]{0,40}\b(Chansey|Gyarados|Lucario|Archeops|Roserade|Froslass|Arcanine|Alakazam|Blaziken|Bronzong|Chandelure|Umbreon|Magnezone|Salamence|Dragonite)\b)')
check('no species is assigned to a Dominante, leader, rival or Ace anywhere in Volume 9 (Dominante 1 is pending, never named)', not SPB.findall(MD) and 'Dominante 1 (Siniestro/Volador)' in MD, str(SPB.findall(MD)[:3]))
print('== 10. PDF layout ==')
try:
    import pymupdf as fitz
except Exception:
    import fitz
d = fitz.open(PDFP)
sizes = [i + 1 for i, pg in enumerate(d) if not (abs(pg.rect.width - 841.89) < 1.5 and abs(pg.rect.height - 595.28) < 1.5)]
check('every page is landscape A4, 842 x 595 (%d pages)' % d.page_count, not sizes and 60 <= d.page_count <= 220, str(sizes[:3]))
over = []
for i, pg in enumerate(d):
    if i == 0: continue
    for b in pg.get_text('dict')['blocks']:
        for ln in b.get('lines', []):
            for sp in ln['spans']:
                x0, y0, x1, y1 = sp['bbox']
                if sp['text'].strip() and (x0 < 26 or x1 > 816 or (y1 > 546 and y0 < 546)):
                    over.append((i + 1, sp['text'][:20]))
check('no text overflows the page margins', not over, str(over[:3]))
ptxt = ' '.join(pg.get_text() for pg in d)
flat = re.sub(r'\s+', '', ptxt)
miss = [s for s in rows6 if re.sub(r'\s+', '', ITEMS[s]['name'] if not re.fullmatch(r'TM\d+', s) else 'MT%02d' % int(s[2:])) not in flat]
check('PDF text contains every item name and every TM number', not miss, str(miss[:4]))
check('PDF contains all 64 location headings and the Psyduck item showcase', all(re.sub(r'\s+', '', l) in flat for l in LOCS) and 'DiademaJaqueca' in flat and 'Psyduck' in ptxt)
check('PDF has no replacement glyphs', '�' not in ptxt and '■' not in ptxt)
check('banned words appear nowhere in the PDF text either', not BAN.findall(re.sub(r'\s+', ' ', ptxt).replace('Buceo Ball', 'Ball')) and not re.search('ParcheHabilidad|TrajedeBuceo', flat), str(BAN.findall(ptxt)[:3]))
check('PDF uses the four new location names and none of the old ones', all(re.sub(r'\s+', '', n) in flat for n in NEWN) and not any(re.sub(r'\s+', '', o) in flat for o in OLDN))

# ------------------------------------------------------------------ integrity
print('== 11. Integrity ==')
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
cur = {}
for dd in ('Data',):
    for dp, dn, fn in os.walk(os.path.join(ROOT, dd)):
        for f in fn:
            p = os.path.join(dp, f); cur[os.path.relpath(p, ROOT)] = md5(p)
diff = [f for f in Bj['pbs_data'] if f.startswith('Data/') and cur.get(f) != Bj['pbs_data'][f]]; newf = [f for f in cur if f not in Bj['pbs_data']]
check('Data/ is byte-identical to the baseline', not diff and not newf, '%d files checked' % len(cur))
unch = [f for f, h in Bj['masters_unchanged'].items() if md5(os.path.join(D, f)) != h]
check('earlier masters 1, 2, Pokemon_Changes_Master.md and proposed_moves.txt remain unchanged', not unch, str(unch))
check('the cross-suite renames reached Volumes 6, 7 and 8 (the four new names appear in each)', all(all(n in rd(os.path.join(D, f)) for n in NEWN) for f in ('6_World_and_Locations_Master_Guide.md', '7_Characters_Master_Guide.md', '8_Story_Novella_Master_Guide.md')))

n = len(RES); badr = [r for r in RES if not r[0]]
print('\n%d/%d checks passed' % (n - len(badr), n))
if badr:
    print('FAILED:'); [print('  -', b[1], b[2]) for b in badr]
sys.exit(1 if badr else 0)
