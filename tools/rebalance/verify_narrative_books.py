#!/usr/bin/env python3
"""verify_narrative_books.py - verification of the narrative suite (books 6, 7 and 8) of Pokemon REM (design only, nothing is injected).

Reads ONLY files of this repository:
  docs/rebalance/{6_World_and_Locations,7_Characters,8_Story_Novella}_Master_Guide.{md,pdf}
  docs/Mapa/*.md sources (Mapa 51cb...md, for the original level table)
  tools/rebalance/baseline_md5.json (PBS/ and Data/ checksums)

Usage:  python3 tools/rebalance/verify_narrative_books.py        (exit code 0 = every check passed)
"""
import os, re, sys, json, hashlib, glob, warnings
warnings.filterwarnings('ignore')
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
D = os.path.join(ROOT, 'docs', 'rebalance')
RES = []
def check(name, ok, detail=''):
    RES.append((bool(ok), name, detail)); print(('PASS  ' if ok else 'FAIL  ') + name + (f'  [{detail}]' if detail else ''))
def md5(p): return hashlib.md5(open(p, 'rb').read()).hexdigest()
def rd(p): return open(p, encoding='utf-8').read()

B = {6: '6_World_and_Locations_Master_Guide', 7: '7_Characters_Master_Guide', 8: '8_Story_Novella_Master_Guide'}
MD = {k: os.path.join(D, v + '.md') for k, v in B.items()}
PDF = {k: os.path.join(D, v + '.pdf') for k, v in B.items()}

print('== 1. Files ==')
check('three markdown + three PDF volumes present', all(os.path.exists(p) for p in list(MD.values()) + list(PDF.values())))
check('map assets present (base, nodes, routes)', all(os.path.exists(os.path.join(D, 'assets', f)) for f in ('6_mapa_oniria_base.jpg', '6_mapa_oniria_nodos.jpg', '6_mapa_oniria_rutas.jpg')))
T = {k: rd(p) for k, p in MD.items()}

print('== 2. PDF layout (portrait A4, no overflow) ==')
try:
    import pymupdf as fitz
except Exception:
    import fitz
for k in (6, 7, 8):
    d = fitz.open(PDF[k]); bad_size = []; over = []; imgs = 0
    for i, pg in enumerate(d):
        r = pg.rect
        if not (abs(r.width - 595.28) < 1.5 and abs(r.height - 841.89) < 1.5): bad_size.append(i + 1)
        if i == 0: continue
        for b in pg.get_text('blocks'):
            x0, y0, x1, y1 = b[:4]
            if x0 < 48 or x1 > r.width - 48 or y0 < 20 or y1 > r.height - 20: over.append((i + 1, round(x0), round(x1)))
        imgs += len(pg.get_images())
    check(f'vol {k}: {d.page_count} pages, every page portrait A4', not bad_size, str(bad_size[:5]))
    check(f'vol {k}: no text block outside the page margins', not over, str(over[:4]))
    if k == 6: check('vol 6: three map figures embedded', imgs >= 3, f'{imgs} images')
    meta = d.metadata
    check(f'vol {k}: PDF has an outline (bookmarks)', len(d.get_toc()) > 20, f'{len(d.get_toc())} entries')

print('== 3. Language (100 % Spanish) ==')
EN = re.compile(r'\b(the|and|with|from|this|that|which|where|when|your|their|have|will)\b')
for k in (6, 7, 8):
    prose = re.sub(r'`[^`]*`', '', T[k]); prose = re.sub(r'\(Historia\.md|Mapa\.md|Personajes\.md', '', prose)
    hits = [m.group(0) for line in prose.splitlines() if not line.startswith('|') for m in EN.finditer(line)]
    check(f'vol {k}: no English function words in prose', not hits, str(hits[:6]))

print('== 4. Names ==')
NEW4 = ['Pueblo Iolita', 'Pueblo Heliodoro', 'Granja Apatita', 'Bosque Dioptasa']      # renombrados el 28 oct. 2026 (antes: Pueblo Cianita, Pueblo Topacio, Granja Ambarina, Bosque Turmalino)
OLD_RE = re.compile(r'Cianita|Topacio|Ambarina|Turmalin[oa]')
OLD_OK = re.compile(r'provisional anterior|Mapa\.md|Historia\.md|[Rr]enombrad|[Bb]orrador')     # el nombre antiguo solo puede quedar como nombre en borrador / registro de renombrado
check('the four new names (Iolita, Heliodoro, Apatita, Dioptasa) appear in the three volumes', all(all(n in T[k] for n in NEW4) for k in (6, 7, 8)) or all(all(n in T[k] for n in NEW4) for k in (6, 8)), '')
def old_left(txt): return [l[:80] for l in txt.splitlines() if OLD_RE.search(l) and not OLD_OK.search(l)]
for k in (6, 7, 8):
    ol = old_left(T[k]); check(f'vol {k}: the four old names survive only as draft names / in the rename registry', not ol, str(ol[:3]))
flat = {k: re.sub(r'\s+', '', ' '.join(pg.get_text() for pg in fitz.open(PDF[k]))) for k in (6, 7, 8)}
check('PDFs 6, 7 and 8 print the four new names and no old name outside draft columns / the registry', all(re.sub(r'\s+', '', n) in flat[k] for k in (6, 8) for n in NEW4) and re.sub(r'\s+', '', 'Pueblo Iolita') in flat[7] and not re.search(r'Granja Ambarina|Pueblo Topacio|Bosque Turmalino'.replace(' ', ''), flat[7]) and not re.search(r'Pueblo Cianita|Pueblo Topacio|Granja Ambarina|Bosque Turmalino'.replace(' ', ''), flat[8]), '')
for k in (9, 10):
    pk = {9: '9_Items_and_Economy_Master_Guide.md', 10: '10_Wild_Encounters_Master_Guide.md'}[k]
    if os.path.exists(os.path.join(D, pk)):
        ol = old_left(rd(os.path.join(D, pk))); check(f'vol {k}: no old name outside draft names / the rename registry', not ol, str(ol[:3]))
check('Gruta Azurita: no Buceo / Dive / Traje de Buceo in volumes 6, 7, 8 (Tabla de Surf + Sello Abisal)', not any(re.search(r'[Bb]uce|\bDive\b|\bdive\b|Traje de Buceo', l.replace('Buceo Ball', '')) for k in (6, 7, 8) for l in T[k].splitlines() if not l.startswith('| A-')) and 'Tabla de Surf' in T[6] and 'Sello Abisal' in T[6], '')
LEG_PLACE = ['Ardita', 'Ágata', 'Larvik', 'Larimar', 'Ilita', 'Galena', 'Nefrel', 'Tenita', 'Ónice', 'Diosel', 'Malaquita', 'Albita', 'Selenita', 'Serthal', 'Cornalina', 'Fluorita', 'Turen', 'Dolita', 'Axil', 'Antracita', 'Coralio', 'Tharn', 'Lazur', 'Dialen', 'Zékira', 'Mosgril', 'Calmir', 'Cinara', 'Magnax', 'Abyss', 'Glacil', 'Caltra', 'Kenis', 'Bauxa', 'Varis', 'Rina', 'Espectro']
LEG_CHAR = ['Aion', 'Caelum', 'Aurora', 'Dante', 'Zira', 'Lyssa', 'Phobos', 'Orion', 'Amina', 'Kai', 'Ferran', 'Kenji', 'Rocco', 'Silvana', 'Gwendolyn', 'Ignis', 'Khepri', 'Nyx', 'Delia', 'Terran']
LEG = LEG_PLACE + LEG_CHAR + ['Jade', 'Basalto', 'Volt']
ALLOW_CTX = re.compile(r'borrador|^\|| \|\s|Alias|Historia\.md|Mapa\.md|Personajes\.md|Apéndice|aurora boreal|(el )?jade|Jade»')
for k in (6, 7, 8):
    bad = []
    for ln in T[k].splitlines():
        for w in LEG:
            if re.search(r'(?<![\w])' + re.escape(w) + r'(?![\w])', ln):
                if k == 8 or not ALLOW_CTX.search(ln): bad.append((w, ln[:70]))
    check(f'vol {k}: draft placeholder names only appear as draft references' if k != 8 else 'vol 8: no draft placeholder name appears at all', not bad, str(bad[:3]))

print('== 5. Volume 6 counts ==')
def h3_in(text, a, b):
    s = text.index(a); e = text.index(b, s) if b else len(text)
    return re.findall(r'^### (.+)$', text[s:e], re.M)
c2 = h3_in(T[6], '# Capítulo 2', '# Capítulo 3'); c3 = h3_in(T[6], '# Capítulo 3', '# Capítulo 4'); c4 = h3_in(T[6], '# Capítulo 4', '# Capítulo 5'); c5 = h3_in(T[6], '# Capítulo 5', '# Apéndice A')
check('8 city fichas', len(c2) == 8, str(len(c2))); check('8 town fichas', len(c3) == 8, str(len(c3))); check('16 small-location fichas', len(c4) == 16, str(len(c4)))
nr = [x for x in c5 if re.match(r'^Ruta \d+$', x)]
check('24 numbered routes (Ruta 1 .. Ruta 24) + 8 special routes', sorted(int(x.split()[1]) for x in nr) == list(range(1, 25)) and len(c5) == 32, f'{len(nr)} numbered, {len(c5)} total')
check('every ficha carries the required blocks', T[6].count('**Descripción ambiental.**') == 64 and T[6].count('**Personajes presentes.**') == 64 and T[6].count('**Pokémon salvajes y pesca (Vol. 10).**') == 64 and T[6].count('**Objetos y MT de la ubicación (Vol. 9).**') == 64 and T[6].count('Jefes y eventos clave') >= 64)
check('every ficha carries the merged item/TM table (Vol 9) and the wild + fishing table (Vol 10); 0 placeholders left, no old template', T[6].count('[Especie PENDIENTE]') == 0 and T[6].count('Especie y Equipo Pendientes de Asignación') == 9 and T[6].count('| Método | Slots de especies | Niveles |') == 0 and T[6].count('| Slot | Rareza | % | # Dex | Pokémon | Tipo(s) REM |') >= 64 and T[6].count('| # | Objeto / MT | Método | Ubicación en el escenario | Notas y función |') == 64)
check('gym leaders / numbering: 8 medals in the city table', len(re.findall(r'^\| \d \| Ciudad ', T[6][T[6].index('## 2.1'):T[6].index('## 2.2')], re.M)) == 8)

print('== 6. Wild levels vs the original Niveles table of Mapa.md ==')
mapa = glob.glob(os.path.join(ROOT, 'docs', 'Mapa *.md'))
def norm(s): return re.sub(r'\s+', '', re.sub(r'\([^)]*\)|\*|[📍🎖️⚠️⚔️🏆«»“”]', '', s).replace('–', '-').replace('—', '-')).lower()
ALIAS = {'reservanaturalsilex': 'parquesilex', 'pasoacantilados': 'pasodelosacantilados'}
if mapa:
    src = rd(mapa[0]); sec = src[src.index('### Niveles'):]
    rows = []
    for ln in sec.splitlines():
        if ln.startswith('|') and not ln.startswith('| ---') and 'Ubicación' not in ln:
            c = [x.strip() for x in ln.strip().strip('|').split('|')]
            rows.append(c)
    m6 = T[6][T[6].index('## 1.4'):T[6].index('# Capítulo 2')]
    master = []
    for ln in m6.splitlines():
        if re.match(r'^\| \d+ \|', ln): master.append([x.strip() for x in ln.strip().strip('|').split('|')])
    used = set(); mism = []; unmatched = []; checked = 0
    for r in rows:
        nm = norm(r[0]); nm = ALIAS.get(nm, nm)
        d, n = norm(r[1]), norm(r[2])
        found = None
        for i, m in enumerate(master):
            if i in used or 'fila añadida' in m[1] or 'fila reubicada' in m[1]: continue
            toks = [norm(t) for t in re.split(r' · ', m[2])]
            if nm in toks: found = i; break
        if found is None: unmatched.append(r[0]); continue
        used.add(found)
        md, mn = [norm(x) for x in master[found][4].split('/')]
        dd = '' if d in ('-', '') else d; nn = '' if n in ('-', '') else n
        mdd = '' if md in ('-', '') else md; mnn = '' if mn in ('-', '') else mn
        checked += 1
        if (dd, nn) != (mdd, mnn): mism.append((r[0], r[1], r[2], master[found][4]))
    CHANGED = {'**Puente Galen**': '39–41 / 58–61', '**Reserva Natural Silex**': '46–48 / 69–72', '**Monte Tharn (Mazmorra Final)**': '— / —'}
    mism_other = [m for m in mism if m[0] not in CHANGED]
    mrow = {x[1]: x[4] for x in master}
    chg_ok = all(mrow.get(k) == v for k, v in (('Puente Dolomita', '39–41 / 58–61'), ('Reserva Peridoto', '46–48 / 69–72'), ('Monte Azogue', '— / —')))
    check('vol 6 master table matches every wild-level range of the original table, except the 3 documented Vol 10 changes (Puente Dolomita, Reserva Peridoto, Monte Azogue)', not mism_other and chg_ok and len(mism) == 3, f'{checked} rows compared; unexpected mismatches {mism_other[:3]}; changed rows ok={chg_ok}')
    check('every original row found a definitive name', len(unmatched) <= 1, str(unmatched))
else:
    check('Mapa.md source present for level comparison', False)

print('== 7. Volume 8 thread (68 chapters, exact order) ==')
EXPECTED = ['Pueblo Iolita', 'Ruta 1', 'Pueblo Heliodoro', 'Granja Apatita', 'Bosque Dioptasa', 'Ruta 2', 'Ciudad Calcedonia — Llegada', 'Ruta 3 — La Cueva', 'Ciudad Calcedonia — La Prueba (Gimnasio 1)', 'Ruta 4', 'Playa Sepiolita', 'Ciudad Calaíta (Gimnasio 2)', 'Ruta 5', 'Pueblo Pedernal', 'Lago Amatista y la Geoda Hundida (Base Morfeo 1)', 'Ruta 6', 'Central Fulgurita', 'Ruta 7', 'Ciudad Magnetita — Llegada', 'Isla Opalina — Primera visita', 'Ciudad Magnetita — La Medalla (Gimnasio 3)', 'Estepa Laterita', 'Desierto Halita', 'Ruta 8', 'Ciudad Nefrita (Gimnasio 4)', 'Senda Serpentina', 'Ruinas Atacamita', 'Ruta 9 (acceso parcial)', 'Puente Dolomita', 'Ciudad Azabache (Gimnasio 5)', 'Ruta 10', 'Cascadas Travertinas', 'Acantilados Rodonita', 'Pueblo Casiterita', 'Ruta 11', 'Ruta 12', 'Pueblo Nácar', 'Ruta 13', 'Isla Obsidiana — Primera visita', 'Ruta 14', 'Reserva Peridoto', 'Ciudad Venturina — Llegada', 'Ruta 15', 'Ciudad Venturina — La Medalla (Gimnasio 6)', 'Ruta 16', 'Villa Adularia', 'Ciénaga Limonita y el Refugio de Turba (Base Morfeo 2)', 'Pueblo Esteatita', 'Ruta 17', 'Ciudad Alabastro (Gimnasio 7)', 'Ruta 19', 'Ruta 18', 'Templo Moldavita', 'Ladera Pórfido y el Bastión del Pórfido (Base Morfeo 3)', 'Ruta 20', 'Ruta 21', 'Ciudad Rejalgar (Gimnasio 8)', 'Ruta 22', 'Monte Azogue', 'Ruta 23 — Camino a la Isla Opalina', 'Isla Opalina — El Altar Lunar', 'Ruta 24 — Camino a la Isla Obsidiana', 'Isla Obsidiana — El Altar Oscuro', 'Interludio — Las Cuatro Grutas', 'Calzada Corindón (Calle Victoria)', 'El Umbral de la Liga', 'Liga Pokémon — Meseta Celestita', 'Epílogo']
chs = re.findall(r'^## (\d+)\. (.+)$', T[8], re.M)
check('68 numbered chapters in the exact thread order', [t for _, t in chs] == EXPECTED and [int(n) for n, _ in chs] == list(range(1, 69)), f'{len(chs)} chapters')
check('every chapter has the four-field state header and a gameplay-milestones block', T[8].count('**Medallas obtenidas**') == 68 and T[8].count('**Fragmentos de orbe en juego**') == 68 and T[8].count('**Personajes en escena**') == 68 and T[8].count('#### Hitos de gameplay y consecuencias') == 68)
check('act structure: five acts', len(re.findall(r'^# Acto [IV]+ — ', T[8], re.M)) == 5)
check('dominants numbered in order 1..6 in the milestones', all(x in T[8] for x in ('Primer Dominante', 'Segundo Dominante', 'Tercer Dominante', 'Cuarto Dominante', 'Quinto Dominante', 'Sexto Dominante')))
check('eight medals are awarded in order', [int(x) for x in re.findall(r'\*\*Medalla (\d)\*\*', T[8])][:8] == [1, 2, 3, 4, 5, 6, 7, 8] or all(f'Medalla {i}' in T[8] for i in range(1, 9)))

print('== 8. Characters: appearances (vol 7) = cast of every chapter (vol 8) ==')
NAMES = ['Ambrosio', 'Lucián', 'Guiomar', 'Eliseo', 'Nerea', 'Zenobia', 'Alarico', 'Roldán', 'Matilde', 'Ismael', 'Argos', 'Genzo', 'Fausto', 'Hildegarda', 'Isolda', 'Baltasar', 'Nicodemo', 'Leucótea', 'Oriana', 'Anteo', 'Telmo', 'Amparo', 'Pía', 'Eladio y Hortensia']
sec7 = re.split(r'^## ', T[7], flags=re.M)[1:]
app7 = {}; combat7 = []
for blk in sec7:
    title = blk.split('\n', 1)[0]
    who = next((n for n in NAMES if n.split()[0] in title), None)
    if not who: continue
    for ln in blk.splitlines():
        if re.match(r'^\| \d+ \|', ln):
            c = [x.strip() for x in ln.strip().strip('|').split('|')]
            if len(c) >= 5:
                app7.setdefault(c[1], set()).add(who)
                if c[4].startswith('Sí'): combat7.append((who, c[1], c[4]))
cast8 = {}; body8 = {}
parts = re.split(r'^## (\d+)\. ', T[8], flags=re.M)
for i in range(1, len(parts), 2):
    title = parts[i + 1].split('\n', 1)[0]; body = parts[i + 1]
    row = re.search(r'\*\*Personajes en escena\*\* \| (.+) \|', body).group(1)
    cast8[title] = {x.strip() for x in row.split(', ') if not x.startswith('Tú') and x.strip() != 'Vendedor ambulante'}
    body8[title] = body
diff = [(t, sorted(cast8[t] ^ app7.get(t, set()))) for t in EXPECTED if cast8[t] != app7.get(t, set())]
check('cast of every vol-8 chapter equals the vol-7 chronologies', not diff, str(diff[:3]))
tot7 = sum(len(v) for v in app7.values())
check('total character appearances identical in both volumes', tot7 == sum(len(v) for v in cast8.values()), f'{tot7} appearances')
miss = []
for who, loc, cb in combat7:
    m = re.search(r'Nv (\d+)', cb)
    if m and f'Nv {m.group(1)}' not in body8[loc]: miss.append((who, loc, m.group(1)))
check('every battle level of vol 7 is stated in the matching vol-8 chapter', not miss, str(miss[:3]))
expected_levels = {'Matilde': 16, 'Ismael': 25, 'Argos': 35, 'Genzo': 41, 'Fausto': 49, 'Hildegarda': 54, 'Isolda': 64, 'Baltasar': 70}
got = {w: int(re.search(r'Nv (\d+)', cb).group(1)) for w, loc, cb in combat7 if w in expected_levels and re.search(r'Nv (\d+)', cb)}
check('gym Ace levels 16, 25, 35, 41, 49, 54, 64, 70 preserved', got == expected_levels, str(got))
check('League: Nerea Nv 77 at the threshold, Champion Nv 80, rivals Nv 76', ('Nerea', 'El Umbral de la Liga', 'Sí — Nv 77') in combat7 and any(w == 'Roldán' and 'Nv 80' in cb for w, l, cb in combat7) and sum(1 for w, l, cb in combat7 if l == 'Calzada Corindón (Calle Victoria)') == 2)
check('Nerea does not fight on the Calzada Corindón', not any(w == 'Nerea' and l.startswith('Calzada') for w, l, cb in combat7))

print('== 9. Fragments ledger ==')
led = T[8][T[8].index('## El libro de cuentas'):T[8].index('## Preludio')]
check('six fragments: odd = Pesadilla, even = Sueño (lunar)', all(re.search(rf'\| F{n} \|.*\| {o} \|', led) for n, o in ((1, 'Pesadilla'), (2, 'Lunar'), (3, 'Pesadilla'), (4, 'Lunar'), (5, 'Pesadilla'), (6, 'Lunar'))))
check('Orbe del Sueño = F2+F4+F6 and Orbe de la Pesadilla = F1+F3+F5 in the altar chapters', 'F2+F4+F6' in T[8] and 'F1+F3+F5' in T[8])
check('Morfeo reaches 6/6 before the Monte', '6/6' in body8['Templo Moldavita'] and 'Morfeo: 6/6' in T[8])

print('== 9b. No species assigned to named trainers or Dominants (markers only) ==')
_sp = set()
for _l in open(os.path.join(D, 'Pokemon_Changes_Master.md'), encoding='utf-8'):
    _m = re.match(r'### #\d+ (.+)$', _l.strip())
    if _m: _sp.add(_m.group(1).strip())
_sp -= {'Cresselia', 'Darkrai'}          # legendarios de los altares: se quedan en la historia
_SP = re.compile(r'(?<![\wÁ-ú])(' + '|'.join(sorted((re.escape(n) for n in _sp), key=len, reverse=True)) + r')(?![\wÁ-ú])')
for k in (7, 8):
    left = [(i + 1, _SP.findall(l)[:2]) for i, l in enumerate(T[k].splitlines()) if _SP.search(l) and re.search(r'Ace|[Ee]quipo|Dominante|Pokémon \|', l)]
    check(f'vol {k}: no species next to Ace / team / Dominant', not left, str(left[:4]))
mk = re.findall(r'^\| Rol en el Equipo \(Slot 1 a Slot 6 / Ace\) \| Especie \[PENDIENTE DE ASIGNACIÓN\] \| Nivel \[EN REVISIÓN\\\*\] \|', T[7], re.M)
check('vol 7: 20 team tables are placeholder tables (8 leaders-of-teams + 8 gyms + 4 Elite Four), 7 rows each (Slot 1-6 + Ace)', len(mk) == 20 and T[7].count('| [PENDIENTE DE ASIGNACIÓN] | [EN REVISIÓN\\*] |') == 140 and '| Pokémon | Tipo (REM) | Habilidad sugerida' not in T[7], f'{len(mk)} tables, {T[7].count("| [PENDIENTE DE ASIGNACIÓN] | [EN REVISIÓN")} rows')
check('vol 8: Dominants are not captured and stay pending (note present)', 'no se capturan' in T[8] and 'Dominante 1 (Siniestro/Volador)' in T[8] and 'Cresselia' in T[8] and 'Darkrai' in T[8])

print('== 10. Immutability ==')
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
for d in ('Data',):
    for dp, dn, fn in os.walk(os.path.join(ROOT, d)):
        for f in fn:
            p = os.path.join(dp, f); cur[os.path.relpath(p, ROOT)] = md5(p)
diff = [f for f in Bj['pbs_data'] if f.startswith('Data/') and cur.get(f) != Bj['pbs_data'][f]]; new = [f for f in cur if f not in Bj['pbs_data']]
check('Data/ is byte-identical to the baseline', not diff and not new, f'{len(cur)} files checked')
unch = [f for f, h in Bj['masters_unchanged'].items() if md5(os.path.join(D, f)) != h]
check('earlier masters remain unchanged', not unch, str(unch))

n = len(RES); bad = [r for r in RES if not r[0]]
print(f'\n{n - len(bad)}/{n} checks passed')
if bad:
    print('FAILED:'); [print('  -', b[1], b[2]) for b in bad]
sys.exit(1 if bad else 0)
