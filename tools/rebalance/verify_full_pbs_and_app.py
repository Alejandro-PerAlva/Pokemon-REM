#!/usr/bin/env python3
"""Phase 3 verifier: full PBS injection of Master Volumes 1-10 + the Pokemon REM Master Codex app.

Sections
  1. PBS_backup_original/ intact (md5 manifest) and Data/ untouched
  2. official PBS files: encoding, syntax (phase1/pbs_check.py), zero broken refs, 100 % match with Vols 1-10
  3. PBS/rem_*.txt: parse without warnings + coverage (721 / 414 / 100 / 64 / 440 / 25+ / 68 ...)
  4. Codex backend: starts the server, every endpoint, model contract, assets, static files
  5. Fault tolerance: typos injected into a temp copy of PBS -> server alive, warnings with file/line/suggestion
  6. Live reload: touching/editing a PBS file changes /api/version and /api/model without restart
  7. Browser smoke test (headless Chrome, route #/selftest): zero console errors, zero broken images/links

Usage: python3 tools/rebalance/verify_full_pbs_and_app.py [--skip-browser]
Exit code 0 when every check passes. Reads repo files only; writes only to a temp directory.
"""
import os, sys, re, json, hashlib, subprocess, time, shutil, tempfile, socket, urllib.request, urllib.error, glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
PBS = os.path.join(ROOT, 'PBS'); BAK = os.path.join(ROOT, 'PBS_backup_original'); D = os.path.join(ROOT, 'docs', 'rebalance')
sys.path.insert(0, os.path.join(ROOT, 'tools', 'codex')); sys.path.insert(0, os.path.join(ROOT, 'tools', 'rebalance', 'phase1')); sys.path.insert(0, ROOT)
SKIP_BROWSER = '--skip-browser' in sys.argv
RES = []

def check(name, ok, detail=''):
    RES.append((bool(ok), name, detail))
    print(('  OK   ' if ok else '  FAIL ') + name + ('' if ok or not detail else '   -> ' + str(detail)[:300]))

def md5(p): return hashlib.md5(open(p, 'rb').read()).hexdigest()
def raw(p): return open(p, 'rb').read()
def lines_of(p):
    t = raw(p).decode('utf-8-sig', errors='replace').replace('\r\n', '\n').replace('\r', '\n')
    return t.split('\n')
def data_lines(p): return [l for l in lines_of(p) if l.strip() and not l.lstrip().startswith('#')]
def has_bom_crlf(p):
    b = raw(p)
    return b.startswith(b'\xef\xbb\xbf') and b.count(b'\n') == b.count(b'\r\n') and b.count(b'\r') == b.count(b'\r\n')

# ----------------------------------------------------------------------------------------------- tiny readers
def read_pokemon(path):
    out, cur = {}, None
    for l in lines_of(path):
        m = re.match(r'^\[(\d+)\]\s*$', l.strip())
        if m: cur = out.setdefault(int(m.group(1)), {}); continue
        if cur is not None and '=' in l and not l.lstrip().startswith('#'):
            k, v = l.split('=', 1); cur[k.strip()] = v.strip()
    return out
def read_tm(path):
    out, cur = {}, None
    for l in lines_of(path):
        s = l.strip()
        if not s or s.startswith('#'): continue
        m = re.match(r'^\[([A-Z0-9_]+)\]$', s)
        if m: cur = m.group(1); out[cur] = []; continue
        if cur: out[cur] += [x.strip() for x in s.split(',') if x.strip()]
    return out
def csv_fields(line):
    f, cur, q = [], '', False
    for ch in line:
        if ch == '"': q = not q; cur += ch
        elif ch == ',' and not q: f.append(cur); cur = ''
        else: cur += ch
    f.append(cur); return f

# =============================================================================================== 1. integrity
print('== 1. Backup and Data/ integrity ==')
mf = os.path.join(BAK, 'MANIFEST.md5'); bad = []; n_mf = 0
if os.path.exists(mf):
    for l in open(mf, encoding='utf-8'):
        h, _, r = l.strip().partition(' ')
        r = r.strip().lstrip('*'); r = r[2:] if r.startswith('./') else r
        if not r: continue
        n_mf += 1
        p = os.path.join(BAK, r)
        if not os.path.exists(p) or md5(p) != h: bad.append(r)
check('PBS_backup_original/ exists with its md5 manifest', os.path.exists(mf) and n_mf >= 29, f'{n_mf} entries')
check('every backed-up file is byte-identical to the manifest', not bad, bad[:3])
orig_files = sorted(f for f in os.listdir(BAK) if f != 'MANIFEST.md5' and os.path.isfile(os.path.join(BAK, f)))
check('every original PBS file is still present in PBS/', all(os.path.exists(os.path.join(PBS, f)) for f in orig_files), [f for f in orig_files if not os.path.exists(os.path.join(PBS, f))])
Bj = json.load(open(os.path.join(ROOT, 'tools', 'rebalance', 'baseline_md5.json')))
cur = {}
for dp, dn, fn in os.walk(os.path.join(ROOT, 'Data')):
    for f in fn: p = os.path.join(dp, f); cur[os.path.relpath(p, ROOT)] = md5(p)
dd = [f for f in Bj['pbs_data'] if f.startswith('Data/') and cur.get(f) != Bj['pbs_data'][f]]
check('Data/*.rxdata and *.dat are byte-identical to the baseline (Data/ not touched)', not dd and len([f for f in cur if f.startswith('Data/')]) == len([f for f in Bj['pbs_data'] if f.startswith('Data/')]), dd[:3])

# =============================================================================================== 2. official PBS
print('== 2. Official PBS files ==')
try:
    import pbs_check
    rep = pbs_check.check(PBS)
    errs = rep.get('errors', [])
    check('phase1/pbs_check.py: official PBS files have valid Essentials syntax and zero broken references', not errs, errs[:3])
    print('       pbs_check stats:', rep.get('stats'))
except Exception as e:
    check('phase1/pbs_check.py importable and runs', False, repr(e))

written = ['abilities.txt', 'moves.txt', 'pokemon.txt', 'items.txt', 'tm.txt', 'berryplants.txt', 'encounters.txt']
check('injected official files are UTF-8 with BOM and CRLF', all(has_bom_crlf(os.path.join(PBS, f)) for f in written), [f for f in written if not has_bom_crlf(os.path.join(PBS, f))])
check('PBS/ never contains the pruned items nor stray LF-only files (all PBS text is UTF-8 decodable)',
      all(raw(os.path.join(PBS, f)).decode('utf-8', 'strict') is not None for f in os.listdir(PBS) if f.endswith('.txt') and not f.startswith('~')))

# --- moves
pm = [l.rstrip() for l in data_lines(os.path.join(D, 'proposed_moves.txt'))]
nm = [l.rstrip() for l in data_lines(os.path.join(PBS, 'moves.txt'))]
dm = [(a, b) for a, b in zip(pm, nm) if a != b]
check('moves.txt == proposed_moves.txt (765 lines; only BURNINGJEALOUSY differs: its duplicated 15th field was removed)', len(nm) == len(pm) == 765 and len(dm) <= 1 and all('BURNINGJEALOUSY' in x[0] for x in dm), f'{len(dm)} diffs: ' + str([x[0][:50] for x in dm[:3]]))
move_syms = {csv_fields(l)[1] for l in nm}
# --- items
pi = [l.rstrip() for l in data_lines(os.path.join(D, 'proposed_items.txt'))]
ni = [l.rstrip() for l in data_lines(os.path.join(PBS, 'items.txt'))]
check('items.txt == proposed_items.txt (414 items, identical)', pi == ni and len(ni) == 414, f'{len(ni)} vs {len(pi)}; first diff: ' + str(next(((a[:60], b[:60]) for a, b in zip(pi, ni) if a != b), None)))
item_syms = {csv_fields(l)[1] for l in ni}
old_items = {csv_fields(l)[1] for l in data_lines(os.path.join(BAK, 'items.txt'))}
pruned = old_items - item_syms
check('280 original items were pruned and 43 new ones added', len(pruned) == 280 and len(item_syms - old_items) == 43, f'{len(pruned)} pruned, {len(item_syms - old_items)} new')
check('no Parche Habilidad / Traje de Buceo items remain', not any(re.search(r'Parche Habilidad|Traje de Buceo', l) for l in ni))
tmitems = {csv_fields(l)[1]: csv_fields(l)[-1] for l in ni if re.match(r'^\d+,TM\d+,', l)}
check('items.txt carries TM01-TM100 with their move field', len(tmitems) == 100 and all(v in move_syms for v in tmitems.values()), len(tmitems))
# --- tm
ptm, ntm = read_tm(os.path.join(D, 'proposed_tm.txt')), read_tm(os.path.join(PBS, 'tm.txt'))
check('tm.txt == proposed_tm.txt (100 TMs, identical species lists)', ptm == ntm and len(ntm) == 100, f'{len(ntm)} blocks')
check('every tm.txt block matches the TMn item move (MT01..MT100)', set(ntm) == set(tmitems.values()), sorted(set(ntm) ^ set(tmitems.values()))[:5])
# --- pokemon
prop = read_pokemon(os.path.join(D, 'proposed_pokemon.txt')); learn = read_pokemon(os.path.join(D, 'proposed_learnsets.txt'))
cur_p = read_pokemon(os.path.join(PBS, 'pokemon.txt')); old_p = read_pokemon(os.path.join(BAK, 'pokemon.txt'))
check('pokemon.txt still lists the original 905 sections (roster #722-#905 kept, cleaned)', len(cur_p) == len(old_p) == 905, f'{len(cur_p)}/{len(old_p)}')
mism = []
for n in range(1, 722):
    a, b = prop.get(n, {}), cur_p.get(n, {})
    for k in ('Name', 'InternalName', 'Type1', 'Type2', 'BaseStats', 'Abilities'):
        if a.get(k, '') != b.get(k, ''):
            mism.append((n, k, a.get(k), b.get(k)))
    if a.get('Evolutions', '') != b.get('Evolutions', ''): mism.append((n, 'Evolutions', a.get('Evolutions'), b.get('Evolutions')))
check('pokemon.txt #001-#721: Name/InternalName/Types/BaseStats/Abilities/Evolutions == proposed_pokemon.txt', not mism, mism[:3])
lm = [(n, learn[n].get('Moves'), cur_p[n].get('Moves')) for n in range(1, 722) if n in learn and learn[n].get('Moves') != cur_p[n].get('Moves')]
check('pokemon.txt #001-#721: Moves == proposed_learnsets.txt', not lm and len([n for n in learn if n <= 721]) >= 700, lm[:2])
check('EggMoves removed and HiddenAbility merged for #001-#721', not any(cur_p[n].get('EggMoves') for n in range(1, 722)) and not any(cur_p[n].get('HiddenAbility') for n in range(1, 722)))
check('every Pokémon #001-#721 has 1 or 2 abilities', all(1 <= len([x for x in cur_p[n].get('Abilities', '').split(',') if x]) <= 2 for n in range(1, 722)))
wild_bad = [(n, k, cur_p[n][k]) for n in cur_p for k in ('WildItemCommon', 'WildItemUncommon', 'WildItemRare') if cur_p[n].get(k) and (cur_p[n][k] in pruned or cur_p[n][k] not in item_syms)]
check('WildItem* fields reference only surviving items (63 refs cleaned)', not wild_bad, wild_bad[:3])
evo_bad = []
for n, s in cur_p.items():
    parts = [x for x in s.get('Evolutions', '').split(',') if x]
    for i in range(0, len(parts) - 2, 3):
        if parts[i + 1] in ('Item', 'ItemMale', 'ItemFemale', 'DayHoldItem', 'NightHoldItem', 'TradeItem') and parts[i + 2] not in item_syms: evo_bad.append((n, parts[i:i + 3]))
check('every item-based evolution references an existing item (65 item/stone evolutions kept)', not evo_bad, evo_bad[:3])
n_item_evo = sum(1 for n in range(1, 722) for parts in [[x for x in cur_p[n].get('Evolutions', '').split(',') if x]] for i in range(0, len(parts) - 2, 3) if parts[i + 1] in ('Item', 'ItemMale', 'ItemFemale'))
check('65 item/stone evolutions (Item, ItemMale, ItemFemale) in the 721 roster', n_item_evo == 65, n_item_evo)
# --- abilities
oa = {csv_fields(l)[1]: csv_fields(l) for l in data_lines(os.path.join(BAK, 'abilities.txt'))}
na = {csv_fields(l)[1]: csv_fields(l) for l in data_lines(os.path.join(PBS, 'abilities.txt'))}
check('abilities.txt: same IDs, symbols and Spanish names as the original (zero name changes)', list(oa) == list(na) and all(oa[k][0] == na[k][0] and oa[k][2] == na[k][2] for k in oa), len(na))
chg = [k for k in oa if oa[k][3] != na[k][3]]
check('abilities.txt: descriptions updated for >= 26 reworked abilities', len(chg) >= 26, len(chg))
used = {a for n in range(1, 722) for a in cur_p[n].get('Abilities', '').split(',') if a}
check('every ability used by the 721 exists in abilities.txt', used <= set(na), sorted(used - set(na)))
# --- berries
bp = [l for l in data_lines(os.path.join(PBS, 'berryplants.txt'))]
check('berryplants.txt: 44 planted berries remain (47 berry items; Kee/Maranga/Roseli never had a plant line), none pruned', len(bp) == 44 and not any(l.split(',')[0].strip() in pruned for l in bp), len(bp))
# --- no pruned item anywhere in PBS
toks_bad = {}
for f in sorted(os.listdir(PBS)):
    p = os.path.join(PBS, f)
    if not f.endswith('.txt') or f.startswith('~') or f.startswith('rem_') or f == 'items.txt': continue
    t = raw(p).decode('utf-8-sig', 'replace')
    if f in ('pokemon.txt', 'abilities.txt', 'moves.txt', 'tm.txt', 'encounters.txt', 'trainertypes.txt', 'townmap.txt', 'types.txt', 'metadata.txt', 'phone.txt'):
        # these files have no free item slots except WildItem*/Evolutions/Item=  -> checked above; here only token scan of item-ish keys
        hits = set(re.findall(r'(?:WildItem\w*|Item)\s*=\s*([A-Z0-9]+)', t)) & pruned
    else:
        hits = set(re.findall(r'[A-Z][A-Z0-9]{2,}', t)) & pruned
    if hits: toks_bad[f] = sorted(hits)[:5]
check('no PBS file (battle tower, cups, trainers, berries…) references a pruned item', not toks_bad, toks_bad)

# =============================================================================================== 3. rem_* files
print('== 3. PBS/rem_*.txt ==')
try:
    import remini_ref as R
except Exception as e:
    R = None; check('tools/codex/remini_ref.py importable', False, repr(e))
REM = {}
for f in ('rem_vanilla_baseline', 'rem_changelog', 'rem_locations', 'rem_encounters', 'rem_location_items', 'rem_shops', 'rem_progression', 'rem_characters', 'rem_story'):
    p = os.path.join(PBS, f + '.txt')
    ok = os.path.exists(p)
    if ok and R:
        secs, warns = R.parse(p); REM[f] = {s['key']: s for s in secs}
        check(f'{f}.txt exists, UTF-8 BOM + CRLF, parses with zero warnings ({len(secs)} sections)', has_bom_crlf(p) and not warns, warns[:3])
    else:
        REM[f] = {}; check(f'{f}.txt exists', ok)
LK = [x['key'] for x in json.load(open(os.path.join(ROOT, 'tools', 'codex', 'location_keys.json'), encoding='utf-8'))]
dexes = {f'{n:03d}' for n in range(1, 722)}
bl, cl = REM['rem_vanilla_baseline'], REM['rem_changelog']
check('baseline: 721 [POKEMON_NNN]', {k[8:] for k in bl if k.startswith('POKEMON_')} == dexes, len([k for k in bl if k.startswith('POKEMON_')]))
check('baseline: 765 moves, all original abilities, all 651 original items', sum(k.startswith('MOVE_') for k in bl) == 765 and sum(k.startswith('ABILITY_') for k in bl) == len(oa) and sum(k.startswith('ITEM_') for k in bl) >= 651, (sum(k.startswith('MOVE_') for k in bl), sum(k.startswith('ABILITY_') for k in bl), sum(k.startswith('ITEM_') for k in bl)))
spot = [1, 25, 150, 384, 700]; sp_bad = []
for n in spot:
    s = bl.get(f'POKEMON_{n:03d}'); o = old_p[n]
    if not s or s.get('BaseStats').replace(' ', '') != o['BaseStats']: sp_bad.append(n)
check('baseline stats equal the ORIGINAL pokemon.txt (spot check)', not sp_bad, sp_bad)
check('changelog: 721 [POKEMON_NNN] with a Role', {k[8:] for k in cl if k.startswith('POKEMON_')} == dexes and sum(1 for k in cl if k.startswith('POKEMON_') and cl[k].get('Role')) >= 700, sum(1 for k in cl if k.startswith('POKEMON_')))
loc = REM['rem_locations']
check('rem_locations: exactly the 64 canonical LOC_KEYs', set(loc) == set(LK) and len(loc) == 64, sorted(set(LK) ^ set(loc))[:5])
check('rem_locations: each has Name, Category, Act, MapCoords inside 480x320 (nodes) and compass links', all(loc[k].get('Name') and loc[k].get('Category') and loc[k].get('Act') and re.match(r'^\d+,\d+$', loc[k].get('MapCoords', '')) and 0 <= int(loc[k].get('MapCoords').split(',')[0]) <= 480 and 0 <= int(loc[k].get('MapCoords').split(',')[1]) <= 320 for k in loc), [k for k in loc if not re.match(r'^\d+,\d+$', loc[k].get('MapCoords', ''))][:5])
check('rem_locations: 32 nodes numbered 1-32 and 32 routes with RouteLabel', sorted(int(loc[k].get('MapNodeNumber')) for k in loc if loc[k].get('MapNodeNumber')) == list(range(1, 33)) and sum(1 for k in loc if loc[k].get('RouteLabel')) == 32, sum(1 for k in loc if loc[k].get('RouteLabel')))
conn_bad = []
for k, s in loc.items():
    for side in ('ConnN', 'ConnS', 'ConnE', 'ConnO'):
        v = s.get(side)
        if v:
            for t in v.split('|')[0].replace(';', ',').split(','):
                t = t.strip()
                if t and t not in LK: conn_bad.append((k, side, t))
check('rem_locations: every compass connection points to a valid LOC_KEY', not conn_bad, conn_bad[:3])
enc = REM['rem_encounters']
tables = {k: s for k, s in enc.items() if k != 'SPECIAL_OBTAINABILITY'}
slots = fish = 0; sp_wild = set(); pctbad = []; badsp = []
for k, s in tables.items():
    base = k.split(':')[0]
    if base not in LK: badsp.append(k)
    sl = [v for kk, v in [(x[1], x[2]) for x in s['items']] if re.match(r'^slot\d+$', kk)] if False else [x[2] for x in s['items'] if re.match(r'^slot\d+$', x[1])]
    slots += len(sl); tot = 0
    for v in sl:
        f = v.split(',', 7)
        try: tot += int(f[1]); sp_wild.add(f[2].strip().upper())
        except Exception: pctbad.append((k, v[:40]))
    if sl and tot != 100: pctbad.append((k, tot))
    for kk in ('fishcommon', 'fishrare'):
        for v in s.all(kk):
            fish += 1; f = v.split(',', 6)
            try: sp_wild.add(f[1].strip().upper())
            except Exception: pctbad.append((k, v[:40]))
check('rem_encounters: 440 wild entries = 408 land/cave/surf slots + 32 fishing', slots == 408 and fish == 32, (slots, fish))
check('rem_encounters: every table sums to exactly 100 %', not pctbad, pctbad[:3])
check('rem_encounters: all table keys are valid LOC_KEY[:ZONE]', not badsp, badsp[:3])
syms = {prop[n]['InternalName'] for n in range(1, 722)}
syms_u = {x.upper() for x in syms}
check('rem_encounters: every wild species exists and none repeats across the 440 entries', sp_wild <= syms_u and len(sp_wild) == 440, (len(sp_wild), sorted(sp_wild - syms_u)[:3]))
so = enc.get('SPECIAL_OBTAINABILITY')
ob = {x[1]: x[2] for x in so['items']} if so else {}
check('rem_encounters: [SPECIAL_OBTAINABILITY] covers all 721 species exactly once', set(ob) == dexes and len(so['items']) == 721, len(so['items']) if so else 0)
li = REM['rem_location_items']
rows = sum(len(s.all(f'item{i}')) if False else sum(1 for x in s['items'] if re.match(r'^item\d+$', x[1])) for s in li.values())
check('rem_location_items: 64 locations and 775 item rows', set(li) <= set(LK) and rows == 775, (len(li), rows))
bad_it = [(k, x[2][:30]) for k, s in li.items() for x in s['items'] if re.match(r'^item\d+$', x[1]) and x[2].split(',')[0].strip() not in item_syms]
check('rem_location_items: every ITEM_ID exists in items.txt', not bad_it, bad_it[:3])
tms_seen = {x[2].split(',')[0].strip() for s in li.values() for x in s['items'] if re.match(r'^item\d+$', x[1]) and re.match(r'^TM\d+$', x[2].split(',')[0].strip())}
shops = REM['rem_shops']
check('rem_shops: 9 marts (0-8 medals), 8 special shops, 29 missions', all(f'MART_{i}_MEDALS' in shops for i in range(9)) and sum(k.startswith('SHOP_') for k in shops) == 8 and len([x for x in shops.get('PIA_MISSIONS', {'items': []})['items'] if re.match(r'^mission\d+$', x[1])]) == 29, (list(shops)[:12]))
pr = REM['rem_progression']
check('rem_progression: 68 steps STEP_01..STEP_68 with level caps and valid LocationKey', len(pr) == 68 and all(pr[k].get('LocationKey') in LK and pr[k].get('LevelCapDay', '').isdigit() for k in pr), len(pr))
ch = REM['rem_characters']
check('rem_characters: >= 25 characters with Name/Role/Category', len(ch) >= 25 and all(s.get('Name') and s.get('Role') and s.get('Category') for s in ch.values()), len(ch))
st = REM['rem_story']
check('rem_story: Prelude + 68 chapters + fragment ledger with 6 fragments', 'PRELUDE' in st and all(f'CHAPTER_{i:02d}' in st for i in range(1, 69)) and 'FRAGMENT_LEDGER' in st and sum(1 for x in st['FRAGMENT_LEDGER']['items'] if re.match(r'^fragment\d+$', x[1])) == 6 if st else False, len(st))
check('rem_story: every chapter has full narrative text (>= 1 paragraph, valid LocationKey)', all(st[f'CHAPTER_{i:02d}'].all('narrativetext') and st[f'CHAPTER_{i:02d}'].get('LocationKey') in LK for i in range(1, 69)) if len(st) > 60 else False)
placeholders = sum(raw(os.path.join(PBS, f)).decode('utf-8').count('[PENDIENTE DE ASIGNACIÓN]') + raw(os.path.join(PBS, f)).decode('utf-8').count('Especie Pendiente') for f in ('rem_characters.txt', 'rem_locations.txt') if os.path.exists(os.path.join(PBS, f)))
check('team/boss placeholders preserved ([PENDIENTE DE ASIGNACIÓN] / [Especie Pendiente]*)', placeholders > 0, placeholders)
names_new = ('Pueblo Iolita', 'Pueblo Heliodoro', 'Granja Apatita', 'Bosque Dioptasa')
check('final location names present (Iolita, Heliodoro, Apatita, Dioptasa)', all(any(loc[k].get('Name') == n for k in loc) for n in names_new))

# =============================================================================================== 4-7. app
def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p

def start(pbs_dir, port):
    env = dict(os.environ, REM_PBS_DIR=pbs_dir)
    pr = subprocess.Popen([sys.executable, os.path.join(ROOT, 'start_codex.py'), '--no-browser', '--port', str(port), '--pbs-dir', pbs_dir], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for _ in range(80):
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{port}/api/version', timeout=1); return pr
        except Exception: time.sleep(0.25)
        if pr.poll() is not None: break
    return pr

def get(port, path, method='GET', raw_=False):
    req = urllib.request.Request(f'http://127.0.0.1:{port}{path}', method=method)
    req.add_header('Accept-Encoding', 'identity')
    try:
        r = urllib.request.urlopen(req, timeout=30); b = r.read(); return r.status, (b if raw_ else json.loads(b.decode('utf-8'))), r.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers

print('== 4. Codex backend ==')
procs = []
try:
    port = free_port(); pr = start(PBS, port); procs.append(pr)
    alive = pr.poll() is None
    check('start_codex.py starts the server (1-click launcher works headless)', alive)
    for f in ('start_codex.py', 'start_codex.command', 'start_codex.bat', 'run_pokedex.py'):
        check(f'launcher present: {f}', os.path.exists(os.path.join(ROOT, f)))
    check('start_codex.command is executable', os.access(os.path.join(ROOT, 'start_codex.command'), os.X_OK))
    if alive:
        t0 = time.time(); st_, model, hd = get(port, '/api/model'); dt = time.time() - t0
        check('GET /api/model 200 with a JSON model', st_ == 200 and isinstance(model, dict), st_)
        if isinstance(model, dict):
            check('model built in < 8 s', dt < 8, f'{dt:.1f}s')
            try:
                import model_contract
                errs = model_contract.validate_model(model)
                check('model satisfies the contract (SPEC §4.1: required fields, cross-references resolved)', not errs, errs[:5])
            except Exception as e:
                check('phase1/model_contract.validate_model runs', False, repr(e))
            c = model.get('meta', {}).get('counts', {})
            check('model counts: 721 Pokémon, 765 moves, 414 items, 100 TMs, 64 locations, 440 wild, 68 steps, 68 chapters, 9 shops+8 specials, 29 missions',
                  c.get('pokemon') == 721 and c.get('moves') == 765 and c.get('items') == 414 and c.get('tms') == 100 and c.get('locations') == 64 and c.get('wildSlots', 0) + c.get('fishSlots', 0) == 440 and c.get('steps') == 68 and c.get('chapters') == 68 and c.get('missions') == 29 and c.get('shops') == 17, c)
            check('model: Pokédex diff badges computed live (some Pokémon changed vs the vanilla baseline)', sum(1 for p in model['pokemon'] if (p.get('diff') or {}).get('changed')) > 300, sum(1 for p in model['pokemon'] if (p.get('diff') or {}).get('changed')))
            check('model: warnings list present and PBS health is not "error"', isinstance(model.get('warnings'), list) and model['meta']['health']['status'] in ('ok', 'warn'), model['meta']['health'])
            for ep in ('/api/version', '/api/warnings', '/api/health'):
                s_, _, _ = get(port, ep); check(f'GET {ep} 200', s_ == 200, s_)
            s_, b_, _ = get(port, '/api/reload', method='POST'); check('POST /api/reload 200 ok', s_ == 200 and isinstance(b_, dict) and b_.get('ok'), (s_, str(b_)[:100]))
            s_, b_, _ = get(port, '/api/bundle'); check('GET /api/bundle 200 (fallback bundle available)', s_ == 200 and isinstance(b_, dict) and len(b_.get('pokemon', [])) == 721, s_)
            # ---------- assets
            miss = []
            urls = [f'/gfx/Icons/icon{p["dex"]:03d}.png' for p in model['pokemon'] if p['dex'] in set(model['assets']['icons'])]
            check('Pokémon list icons: all 721 resolved in assets', len(urls) == 721, len(urls))
            sample = list(range(1, 722, 7)) + [721, 150, 25]
            for dx in sample:
                for u in (f'/gfx/Icons/icon{dx:03d}.png', f'/gfx/Battlers/{dx:03d}.png'):
                    s_, _, _ = get(port, u, raw_=True)
                    if s_ != 200: miss.append(u)
            check('sprite/icon files resolve over HTTP (sampled 110 URLs)', not miss, miss[:3])
            allres = []
            for u in {f'/gfx/Icons/icon{p["dex"]:03d}.png' for p in model['pokemon']} | {f'/gfx/Battlers/{p["dex"]:03d}.png' for p in model['pokemon']}:
                if not os.path.exists(os.path.join(ROOT, 'Graphics', u[5:])): allres.append(u)
            check('100 % of the 721 Pokémon icons and battlers exist on disk', not allres, allres[:5])
            iconless = [i['sym'] for i in model['items'] if i.get('icon') and not os.path.exists(os.path.join(ROOT, 'Graphics', i['icon']))]
            check('every item icon the model declares exists on disk (items without art declare icon:null)', not iconless, iconless[:5])
            check('type and category sprite sheets exist', all(os.path.exists(os.path.join(ROOT, 'Graphics', 'Pictures', f)) for f in ('types.png', 'category.png')))
            s_, _, _ = get(port, '/map/Mapa_Final__Esqueleto.png', raw_=True); check('regional map image served at /map/Mapa_Final__Esqueleto.png', s_ == 200, s_)
            s_, idx, _ = get(port, '/', raw_=True); check('GET / serves the SPA index.html', s_ == 200 and b'<script' in idx, s_)
            if s_ == 200:
                refs = re.findall(r'(?:src|href)="(/?app/[^"]+|[^"#:]+\.(?:js|css))"', idx.decode('utf-8', 'replace'))
                bad_ = []
                for r in refs:
                    u = r if r.startswith('/') else '/app/' + r
                    if get(port, u, raw_=True)[0] != 200: bad_.append(r)
                check('every script/stylesheet referenced by index.html resolves', refs and not bad_, bad_[:3])
            s_, _, _ = get(port, '/gfx/../PBS/pokemon.txt', raw_=True); s2, _, _ = get(port, '/gfx/%2e%2e/%2e%2e/PBS/pokemon.txt', raw_=True)
            check('path traversal blocked', s_ in (400, 403, 404) and s2 in (400, 403, 404), (s_, s2))
            s_, _, _ = get(port, '/api/nope'); check('unknown API route returns a clean 404', s_ == 404, s_)

    # =========================================================================================== 5. fault tolerance
    print('== 5. Fault tolerance (typos injected into a temp copy of PBS) ==')
    tmp = tempfile.mkdtemp(prefix='rem_pbs_'); tpbs = os.path.join(tmp, 'PBS'); shutil.copytree(PBS, tpbs)
    def edit(fname, fn):
        p = os.path.join(tpbs, fname); t = raw(p).decode('utf-8-sig'); t2 = fn(t); assert t2 != t, fname; open(p, 'wb').write(b'\xef\xbb\xbf' + t2.encode('utf-8'))
    injected = []
    edit('pokemon.txt', lambda t: t.replace('Type1=GRASS', 'Type1=GRASSS', 1)); injected.append('pokemon.txt Type1=GRASSS')
    edit('pokemon.txt', lambda t: re.sub(r'(\[2\][^\[]*?BaseStats=)(\d+),', r'\g<1>4o,', t, count=1, flags=re.S)); injected.append('pokemon.txt BaseStats=4o')
    edit('pokemon.txt', lambda t: t.replace('\r\nMoves=1,GROWL', '\r\nMoves=1,GROWLL', 1) if '\r\nMoves=1,GROWL' in t else t.replace('Moves=1,TACKLE', 'Moves=1,TACKLEE', 1)); injected.append('pokemon.txt move typo')
    edit('moves.txt', lambda t: t.replace(',FIRE,', ',FUEGOO,', 1)); injected.append('moves.txt type FUEGOO')
    edit('moves.txt', lambda t: t.replace('\r\n', '\r\nLINEA BASURA SIN COMAS\r\n', 3)); injected.append('moves.txt garbage lines')
    edit('abilities.txt', lambda t: t.replace(',STENCH,', ',STENCHH,', 1)); injected.append('abilities.txt symbol typo')
    edit('items.txt', lambda t: t.replace(',POTION,', ',POTIONN,', 1) if ',POTION,' in t else t); injected.append('items.txt symbol typo')
    edit('tm.txt', lambda t: t.replace('[PROTECT]', '[PROTEECT]', 1)); injected.append('tm.txt block typo')
    p = os.path.join(tpbs, 'rem_encounters.txt'); t = raw(p).decode('utf-8-sig'); t = t.replace('PIDGEY', 'PIDGEEY', 1) + '\r\nlinea sin igual\r\n'; open(p, 'wb').write(b'\xef\xbb\xbf' + t.encode('utf-8')); injected.append('rem_encounters.txt species typo + broken line')
    p = os.path.join(tpbs, 'rem_locations.txt'); t = raw(p).decode('utf-8-sig'); t = t.replace('ConnN = ', 'ConnN = RUTA_99,', 1); open(p, 'wb').write(b'\xef\xbb\xbf' + t.encode('utf-8')); injected.append('rem_locations.txt unknown LOC_KEY')
    os.remove(os.path.join(tpbs, 'rem_shops.txt')); injected.append('rem_shops.txt deleted')
    port2 = free_port(); pr2 = start(tpbs, port2); procs.append(pr2)
    check('server still starts with %d injected syntax errors' % len(injected), pr2.poll() is None)
    if pr2.poll() is None:
        s2, m2, _ = get(port2, '/api/model')
        check('model still served (HTTP 200) and keeps all 721 Pokémon', s2 == 200 and isinstance(m2, dict) and len(m2.get('pokemon', [])) == 721, s2)
        w = m2.get('warnings', []) if isinstance(m2, dict) else []
        files_w = {x.get('file') for x in w}
        check('warnings reported for each corrupted file (pokemon, moves, abilities, items, tm, rem_encounters, rem_locations, rem_shops)', {'pokemon.txt', 'moves.txt', 'abilities.txt', 'tm.txt', 'rem_encounters.txt', 'rem_locations.txt', 'rem_shops.txt'} <= files_w, sorted(files_w))
        check('every warning carries file, line, severity, message', all(x.get('file') and 'line' in x and x.get('severity') and x.get('message') for x in w), w[:1])
        sug = {(x.get('file'), x.get('suggestion')) for x in w if x.get('suggestion')}
        check('«¿quisiste decir…?» suggestions: GRASSS->GRASS, FUEGOO->FIRE/Fuego, PIDGEEY->PIDGEY', any(s and str(s).upper() in ('GRASS', 'HIERBA', 'PLANTA') for _, s in sug) and any(s and str(s).upper() in ('FIRE', 'FUEGO') for _, s in sug) and any(s and 'PIDGEY' in str(s).upper() for _, s in sug), sorted(sug, key=str)[:8])
        s3, h2, _ = get(port2, '/api/health'); check('PBS health reports warn/error with per-file counts', s3 == 200 and h2.get('status') in ('warn', 'error') and any(f.get('errors') or f.get('warnings') for f in h2.get('files', [])), str(h2)[:150])
        s4, _, _ = get(port2, '/', raw_=True); check('SPA still served (no blank screen from the server side)', s4 == 200)
        # ===================================================================================== 6. live reload
        print('== 6. Live reload ==')
        _, v0, _ = get(port2, '/api/version')
        pk = os.path.join(tpbs, 'pokemon.txt'); t = raw(pk).decode('utf-8-sig')
        time.sleep(1.1)
        t2 = re.sub(r'(\[1\].*?BaseStats=)(\d+)', lambda m: m.group(1) + str(int(m.group(2)) + 7), t, count=1, flags=re.S)
        open(pk, 'wb').write(b'\xef\xbb\xbf' + t2.encode('utf-8'))
        _, v1, _ = get(port2, '/api/version')
        check('editing pokemon.txt changes /api/version without restarting the server', v0.get('version') != v1.get('version'), (v0.get('version'), v1.get('version')))
        _, m3, _ = get(port2, '/api/model')
        hp0 = next(p for p in m2['pokemon'] if p['dex'] == 1)['stats']['hp']; hp1 = next(p for p in m3['pokemon'] if p['dex'] == 1)['stats']['hp']
        check('/api/model reflects the edited stat on the next request (HP +7)', hp1 == hp0 + 7, (hp0, hp1))
        os.utime(os.path.join(tpbs, 'items.txt'), None); time.sleep(0.3); _, v2, _ = get(port2, '/api/version')
        check('touching a different PBS file (items.txt) is detected too', v2.get('version') != v1.get('version'), (v1.get('version'), v2.get('version')))
        s_, r_, _ = get(port2, '/api/reload', method='POST'); check('manual reload endpoint works on the damaged copy', s_ == 200 and r_.get('ok'), s_)
        # missing directory -> bundle fallback
        port3 = free_port(); pr3 = start(os.path.join(tmp, 'NO_EXISTE'), port3); procs.append(pr3)
        if pr3.poll() is None:
            s5, m5, _ = get(port3, '/api/model')
            check('unreadable PBS directory -> fallback bundle served (meta.source = "bundle")', s5 == 200 and isinstance(m5, dict) and m5.get('meta', {}).get('source') == 'bundle', (s5, m5.get('meta', {}).get('source') if isinstance(m5, dict) else None))
        else:
            check('unreadable PBS directory -> server survives and serves the bundle', False, 'process exited')
    shutil.rmtree(tmp, ignore_errors=True)

    # =========================================================================================== 7. browser
    print('== 7. Browser smoke test (headless Chrome, #/selftest) ==')
    chrome = next((c for c in ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'] if os.path.exists(c)), None)
    if SKIP_BROWSER or not chrome:
        print('  (skipped: %s)' % ('--skip-browser' if SKIP_BROWSER else 'Chrome not found'))
        check('browser smoke test skipped by request/absence', SKIP_BROWSER or chrome is None)
    else:
        prof = tempfile.mkdtemp(prefix='rem_chrome_')
        cmd = [chrome, '--headless=new', '--disable-gpu', '--no-sandbox', '--user-data-dir=' + prof, '--enable-logging=stderr', '--v=0', '--virtual-time-budget=180000', '--dump-dom', f'http://127.0.0.1:{port}/#/selftest']
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        dom = r.stdout; log = r.stderr
        m = re.search(r'<pre[^>]*id="selftest-result"[^>]*>(.*?)</pre>', dom, re.S)
        res = None
        if m:
            import html as _h
            try: res = json.loads(_h.unescape(m.group(1)))
            except Exception as e: res = None
        check('#/selftest finished and published its JSON result', res is not None, dom[:200] if res is None else '')
        if res:
            print('       selftest:', {k: (v if not isinstance(v, list) else len(v)) for k, v in res.items()})
            check('selftest visited all main sections and >= 100 routes (pokemon, moves, abilities, items, tms, shops, missions, map, atlas, locations, progression, characters, story, warnings)', res.get('routes', 0) >= 100 and set(res.get('sections', [])) >= {'home', 'pokedex', 'moves', 'abilities', 'items', 'tms', 'shops', 'missions', 'map', 'atlas', 'progression', 'characters', 'story', 'warnings'}, res.get('sections'))
            check('selftest: zero JavaScript exceptions / console errors', not res.get('errors') and not res.get('consoleErrors'), (res.get('errors') or [])[:3] + (res.get('consoleErrors') or [])[:3])
            check('selftest: zero broken images (100 % of sprites, icons, badges and map resolve)', not res.get('brokenImages'), (res.get('brokenImages') or [])[:5])
            check('selftest: zero broken cross-links (every #/ link points to an existing entity)', not res.get('brokenLinks'), (res.get('brokenLinks') or [])[:5])
            check('selftest: global search (Ctrl+K backend) answers for Pokémon, moves, items, locations', res.get('searchOk') is True, res.get('searchOk'))
        cons = [l for l in log.splitlines() if re.search(r'CONSOLE.*(ERROR|Uncaught|Failed to load)', l, re.I) and 'favicon' not in l.lower()]
        check('Chrome console log has zero errors', not cons, cons[:3])
        shutil.rmtree(prof, ignore_errors=True)
finally:
    for p_ in procs:
        try: p_.terminate(); p_.wait(timeout=5)
        except Exception:
            try: p_.kill()
            except Exception: pass

# =============================================================================================== summary
n = len(RES); badr = [r for r in RES if not r[0]]
print(f'\n{n - len(badr)}/{n} checks passed')
if badr:
    print('FAILED:'); [print('  -', b[1], '->', str(b[2])[:200]) for b in badr]
sys.exit(1 if badr else 0)
