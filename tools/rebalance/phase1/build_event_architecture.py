# -*- coding: utf-8 -*-
"""Arquitectura de eventos de Pokémon REM: Variables/Interruptores de System.rxdata, 40 sidequests locales,
obtenibilidad cerrada de las 721 especies y sincronización de PBS/rem_*.txt.
Uso (desde la raíz del proyecto):  python3 tools/rebalance/phase1/build_event_architecture.py
Idempotente: parte siempre de PBS/*.txt ya generados; las claves/ secciones que añade se reescriben en cada pasada.
Salidas: tools/rebalance/phase1/event_arch.json (lo lee tools/scripts_dump/build_system.rb y build_events_rb),
PBS/rem_variables_switches.txt, docs/rebalance/12_Variables_Switches_Reference.md y parches en rem_*.txt."""
import re, json, os, sys, unicodedata
sys.path.insert(0, os.path.dirname(__file__))
from event_arch_data import *

ROOT = os.getcwd()
P = lambda *a: os.path.join(ROOT, *a)

def rd(path):
    return open(P(path), encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')
def wr(path, text):
    open(P(path), 'w', encoding='utf-8-sig', newline='').write(text.replace('\n', '\r\n'))
def slug(s, up=True):
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'\(.*?\)', '', s)
    s = re.split(r'\s[—–-]\s', s)[0]
    s = re.sub(r'[^A-Za-z0-9]+', '_', s).strip('_')
    return s.upper() if up else s
def sections(text):
    parts = re.split(r'\n(?=\[)', text)
    head = parts[0]
    return head, [(re.match(r'\[([^\]]+)\]', b).group(1), b) for b in parts[1:]]
def getf(b, f):
    m = re.search(r'^' + f + r' = (.*)$', b, re.M)
    return m.group(1).strip() if m else ''
def setkeys(b, kv):
    """Reescribe/añade claves al final de la sección (antes de líneas en blanco finales)."""
    b = b.rstrip('\n')
    for k in kv:
        b = re.sub(r'^' + re.escape(k) + r' = .*\n?', '', b, flags=re.M)
    b = b.rstrip('\n') + '\n' + '\n'.join('%s = %s' % (k, v) for k, v in kv.items())
    return b + '\n'

# ------------------------------------------------------------------ lectura
loc_txt = rd('PBS/rem_locations.txt'); loc_head, locs = sections(loc_txt)
LOCS = {}
for k, b in locs:
    LOCS[k] = dict(key=k, name=getf(b, 'Name'), cat=getf(b, 'Category'), act=getf(b, 'Act'),
                   order=int(getf(b, 'ProgressionOrder') or 0), mapid=getf(b, 'MapID'))
assert len(LOCS) == 64
order = sorted(LOCS.values(), key=lambda d: (d['order'], d['key']))
KEY40 = [d for d in order if d['cat'] in ('Ciudad', 'Pueblo', 'Lugar especial', 'Ruta especial')]
assert len(KEY40) == 40 and set(d['key'] for d in KEY40) == set(SQ), set(SQ) ^ set(d['key'] for d in KEY40)
ACT_NUM = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5}
GIFT_LV = {1: 8, 2: 20, 3: 32, 4: 45, 5: 60}

prog_txt = rd('PBS/rem_progression.txt'); prog_head, steps = sections(prog_txt)
STEPS = []
frags = 0
for k, b in steps:
    n = int(getf(b, 'StepNumber'))
    ch = [int(c.split('_')[1]) for c in getf(b, 'Chapters').split(';') if c]
    ki = getf(b, 'KeyItemsUnlocked')
    frags += len(re.findall(r'(NIGHTMAREFRAG\d|LUNARFRAG\d)', ki))
    STEPS.append(dict(n=n, act=ACT_NUM[getf(b, 'Act')], loc=getf(b, 'LocationKey'), name=getf(b, 'StepName'),
                      capD=int(getf(b, 'LevelCapDay')), capN=int(getf(b, 'LevelCapNight')),
                      boss=getf(b, 'BossOrGymTitle'), medals=int(getf(b, 'MedalsAfterStep') or 0),
                      chapter=max(ch) if ch else 0, frags=frags))
assert [s['n'] for s in STEPS] == list(range(1, 69))

pk_txt = open(P('PBS/pokemon.txt'), encoding='utf-8-sig').read()
INTERNAL = {int(m.group(1)): m.group(2) for m in re.finditer(r'^\[(\d+)\]\n(?:.*\n)*?InternalName=(\w+)', pk_txt, re.M)}
enc_txt = rd('PBS/rem_encounters.txt')
i0 = enc_txt.index('[SPECIAL_OBTAINABILITY]')
OBT = {}
for l in enc_txt[i0:].splitlines()[1:]:
    m = re.match(r'(\d{3}) = (\w+),([^,]*),([^,]*),(.*)$', l)
    if m: OBT[int(m.group(1))] = [m.group(2), m.group(3), m.group(4), m.group(5)]
assert len(OBT) == 721

# ------------------------------------------------------------------ variables
VARS = {}   # id -> name
def V(i, n):
    assert i not in VARS, i
    VARS[i] = n
V(50, 'Tope_Nivel_Actual')
MACRO = [(101, 'Acto_Actual', '1..5, 6=Postgame'), (102, 'Capitulo_Global', '1..68 (Vol. 8)'),
         (103, 'Tramo_Actual', '1..68 = STEP_NN de rem_progression.txt; 69=Postgame'),
         (104, 'Fragmentos_Recuperados', '0..6'), (105, 'Medallas_Oniria', '0..8'),
         (106, 'Cargas_Pokevial_Max', '1..3'), (107, 'Cargas_Pokevial_Actual', '0..3'),
         (108, 'Foco_Mision_Pia', 'ID de la misión de Pía enfocada (0 = ninguna)'),
         (109, 'Contador_Huevos_Guarderia', '0..99 huevos entregados por la guardería'),
         (110, 'Contador_Fosiles_Revividos', '0..11'),
         (111, 'Tope_Nivel_Noche', 'tope de nivel con encuentros nocturnos (LevelCapNight)'),
         (112, 'Hito_Maximo_Alcanzado', '1..69: nunca decrece (anti-retroceso)'),
         (113, 'Dominantes_Derrotados', '0..6'), (114, 'Bases_Morfeo_Destruidas', '0..3'),
         (115, 'Sidequests_Completadas', '0..40'), (116, 'Legendarios_Obtenidos', '0..54'),
         (117, 'Rivales_Derrotados', '0..9'), (118, 'Reservada_Macro_118', 'libre'), (119, 'Reservada_Macro_119', 'libre')]
for i, n, _ in MACRO: V(i, n)
HVAR = {}
for j, d in enumerate(order):
    HVAR[d['key']] = 121 + j; V(121 + j, 'H_' + slug(d['name']))
assert 121 + len(order) - 1 == 184
QVAR = {}
for j, d in enumerate(KEY40):
    QVAR[d['key']] = 201 + j; V(201 + j, 'M_' + slug(d['name']))
assert 201 + 39 == 240

# ------------------------------------------------------------------ interruptores
SW = {}
def S(i, n):
    assert i not in SW, i
    SW[i] = n
BLOCKS = [('Bloque 1 · Jefes y Dominantes derrotados', 501, 580), ('Bloque 2 · Herramientas de campo y desbloqueos', 581, 620),
          ('Bloque 3 · Bloqueos y estados de mapa', 621, 680), ('Bloque 4 · Stock único de tienda y regalos únicos', 681, 760),
          ('Bloque 5 · Legendarios postgame', 761, 820)]
# Bloque 1
b1 = []
for s in STEPS:
    t = s['boss']
    if not t or t.startswith('Gimnasio') or t.startswith('Alto Mando') or t.startswith('Reclutas') or t.startswith('Oleadas'):
        continue
    b1.append('Jefe_P%02d_%s' % (s['n'], slug(t, False).replace('__', '_')))
b1 += ['Base_Morfeo_1_Geoda_Hundida', 'Base_Morfeo_2_Refugio_Turba', 'Base_Morfeo_3_Bastion_Porfiral',
       'Jefe_P56_Oleadas_Morfeo_Ruta22', 'Cima_Azogue_Climax_Completado', 'Altar_Lunar_Isla_Sueno', 'Altar_Oscuro_Isla_Pesadilla',
       'Alto_Mando_1', 'Alto_Mando_2', 'Alto_Mando_3', 'Alto_Mando_4', 'Campeon_Roldan', 'Liga_Completada_Postgame']
for j, n in enumerate(b1): S(501 + j, n)
assert 501 + len(b1) - 1 <= 580, len(b1)
for j, n in enumerate(TOOLS): S(581 + j, n)
for j, (n, d, lk) in enumerate(ROADBLOCKS): S(621 + j, n)
# Bloque 4: tiendas únicas + regalos únicos no-MT
items_txt = rd('PBS/rem_location_items.txt')
UNIQ = []
loc = None
for l in items_txt.splitlines():
    if l.startswith('['): loc = l[1:-1]
    m = re.match(r'Item\d+ = (\w+),(\d+),(\w),', l)
    if m and ((m.group(3) == 'S') or (m.group(3) == 'N' and not re.match(r'TM\d+$', m.group(1)))):
        if m.group(1) in ('CLEARAMULET','CHOICESCARF','LIFEORB','COVERTCLOAK','WEAKNESSPOLICY','CHOICEBAND','LEFTOVERS','EVIOLITE','FOCUSSASH'): continue   # pasan a sidequest
        UNIQ.append((m.group(3), loc, m.group(1)))
for j, (mt, lk, it) in enumerate(UNIQ):
    S(681 + j, ('Tienda_Unica_' if mt == 'S' else 'Regalo_Unico_') + '%s_%s' % (slug(LOCS[lk]['name']).title().replace('_', ''), it))
assert 681 + len(UNIQ) - 1 <= 760, len(UNIQ)
# Bloque 5
LEG = sorted(d for d, v in OBT.items() if v[0] == 'LEGENDARY')
assert len(LEG) == 54
LSW = {}
for j, d in enumerate(LEG):
    LSW[d] = 761 + j; S(761 + j, 'Legendario_%03d_%s' % (d, INTERNAL[d].title()))

# ------------------------------------------------------------------ sidequests: reparto + obtenibilidad
EV = sorted(d for d, v in OBT.items() if v[0] == 'EVENT')
reward_mons = {}
for k, q in SQ.items():
    for r in q['reward']:
        if r[0] == 'MON': reward_mons[r[1]] = (k, r)
assert set(reward_mons) == set(EV), (set(EV) ^ set(reward_mons))
NEWOBT = {}
for d, (k, r) in reward_mons.items():
    act = ACT_NUM[LOCS[k]['act']]
    lv = 5 if r[3] == 'Huevo' else r[2]
    q = SQ[k]
    NEWOBT[d] = ['EVENT', k, str(lv),
        'Sidequest local «%s» · %s (Acto %s) · Variable M_%s (%d) = 99 · %s%s' %
        (q['title'], LOCS[k]['name'], LOCS[k]['act'], slug(LOCS[k]['name']), QVAR[k], r[3],
         ' (eclosiona a Nv 5)' if r[3] == 'Huevo' else '')]
for d in LEG:
    typ, lk, lv, det = OBT[d]
    cond = DEX_COND.get(d) or LOC_COND.get(lk) or DEFAULT_LEG_COND
    place = re.sub(r'\s*\(propuesto\)\s*$', '', det.split(' · Condición:')[0]).replace('Encuentro fijo · ', '')
    NEWOBT[d] = ['LEGENDARY', lk, lv, 'Encuentro fijo · %s · Condición: %s · Interruptor %d (Legendario_%03d_%s)' %
                 (place, cond, LSW[d], d, INTERNAL[d].title())]
for d in OBT:
    if d in NEWOBT: continue
    t = OBT[d]
    det = re.sub(r'\s*\(propuesto\)\s*$', '', t[3])
    NEWOBT[d] = [t[0], t[1], t[2], det]

# ------------------------------------------------------------------ PBS: rem_encounters (SPECIAL_OBTAINABILITY)
lines = enc_txt[i0:].splitlines()
out = [lines[0]]
for l in lines[1:]:
    m = re.match(r'(\d{3}) = ', l)
    if m and int(m.group(1)) in NEWOBT and int(m.group(1)) in (set(EV) | set(LEG) | {d for d in OBT if '(propuesto)' in OBT[d][3]}):
        d = int(m.group(1)); t = NEWOBT[d]
        out.append('%03d = %s,%s,%s,%s' % (d, t[0], t[1], t[2], t[3]))
    else:
        out.append(l)
enc_new = enc_txt[:i0] + '\n'.join(out)
if not enc_new.endswith('\n'): enc_new += '\n'
enc_new = enc_new if '(cerrada: 0' in enc_new else re.sub(r'(# \[SPECIAL_OBTAINABILITY\]:)', r'\1 (cerrada: las 721 especies con método definitivo; EVENT = sidequest local M_*; LEGENDARY = condición + interruptor 761-814)', enc_new, count=1)
wr('PBS/rem_encounters.txt', enc_new)

# ------------------------------------------------------------------ PBS: rem_location_items
MOVE = {'CLEARAMULET': 'GRUTA_LABRADORITA', 'LIFEORB': 'GRUTA_PIRITA', 'COVERTCLOAK': 'ISLA_OBSIDIANA',
        'WEAKNESSPOLICY': 'CIENAGA_LIMONITA', 'CHOICEBAND': 'GRUTA_HIALINA', 'LEFTOVERS': 'DESIERTO_HALITA',
        'EVIOLITE': 'SENDA_SERPENTINA', 'FOCUSSASH': 'CASCADAS_TRAVERTINAS', 'CHOICESCARF': 'CALZADA_CORINDON'}
ITEM_REWARDS = []   # (loc, id, qty, title)
for k, q in SQ.items():
    for r in q['reward']:
        if r[0] == 'ITEM': ITEM_REWARDS.append((k, r[1], r[2], q['title']))
ih, isec = sections(items_txt)
SEC = {}
ORDER = []
for k, b in isec:
    rows = re.findall(r'^Item\d+ = (.*)$', b, re.M)
    pre = b.split('\n')[0]
    SEC[k] = rows; ORDER.append(k)
for k in SEC:   # quitar copias previas de los Tier 1 (se recolocan como recompensa de sidequest)
    SEC[k] = [r for r in SEC[k] if not (r.split(',')[0] in MOVE and r.split(',')[2] in ('H', 'B', 'N', 'E', 'C') and r.split(',')[0] != 'POKEVIAL')]
for (lk, it, qty, title) in ITEM_REWARDS:
    SEC[lk] = [r for r in SEC[lk] if not (r.split(',')[0] == it and r.split(',')[2] == 'E' and 'Sidequest' in r)]
    q = SQ[lk]
    note = 'Recompensa final de la sidequest local «%s» (M_%s = 99). Ejemplar único (Tier 1): no se repone.' % (title, slug(LOCS[lk]['name'])) \
        if it in MOVE else 'Recompensa final de la sidequest local «%s» (M_%s = 99).' % (title, slug(LOCS[lk]['name']))
    SEC[lk].append('%s,%d,E,%s · Sidequest «%s»,%s' % (it, qty, LOCS[lk]['name'], title, note))
ih = re.sub(r'\n# [^\n]* - \d+ filas\s*$', '', ih)
new_items = ih.rstrip('\n') + '\n'
total = 0
for k in ORDER:
    rows = SEC[k]; total += len(rows)
    new_items += '\n# %s - %d filas\n[%s]\n' % (LOCS[k]['name'], len(rows), k)
    for j, r in enumerate(rows, 1): new_items += 'Item%d = %s\n' % (j, r)
new_items = re.sub(r'\(\d+ filas\)', '(%d filas)' % total, new_items, count=1) if re.search(r'\(\d+ filas\)', new_items) else new_items
new_items = re.sub(r'(\d+) filas del Vol\. 9', '%d filas del Vol. 9' % total, new_items, count=1)
wr('PBS/rem_location_items.txt', new_items)

# ------------------------------------------------------------------ PBS: rem_locations (claves nuevas)
loc_head = re.sub(r'\n# StoryVar = .*', '', loc_head)
res = [loc_head.rstrip('\n') + '\n# StoryVar = variable H_* de temporalidad corta del mapa (0 sin iniciar, 1..N pasos, 99 completado). SidequestVar = variable M_* de la sidequest local (0,1,2,3,99); solo las 40 ubicaciones clave. Generado por build_event_architecture.py.\n']
for k, b in locs:
    kv = {'StoryVar': HVAR[k], 'StoryVarName': VARS[HVAR[k]]}
    if k in QVAR:
        q = SQ[k]
        rw = '; '.join(('%s Nv %s (%s)' % (INTERNAL[r[1]].title(), r[2] if r[3] != 'Huevo' else '5', r[3])) if r[0] == 'MON' else
                       ('Pokévial a %d cargas' % r[1] if r[0] == 'VIAL' else '%s x%d' % (r[1], r[2])) for r in q['reward'])
        kv.update({'SidequestVar': QVAR[k], 'SidequestVarName': VARS[QVAR[k]], 'SidequestTitle': q['title'],
                   'SidequestSteps': ' | '.join([q['s1'], q['s2'], q['s3']]), 'SidequestReward': rw})
    res.append(setkeys(b, kv))
wr('PBS/rem_locations.txt', '\n'.join(res))

# ------------------------------------------------------------------ PBS: rem_progression (claves nuevas)
boss_sw = {}
for sw_id, n in SW.items():
    m = re.match(r'Jefe_P(\d\d)_', n)
    if m: boss_sw[int(m.group(1))] = sw_id
prog_head = re.sub(r'\n# MilestoneID = .*', '', prog_head)
res = [prog_head.rstrip('\n') + '\n# MilestoneID = paso (pbAdvanceMilestone). Var50Cap = LevelCapDay → Variable 50; Var111Cap = LevelCapNight → Variable 111. ActVar/ChapterVar/TramoVar/MedalsVar/FragmentsVar = valores de las variables macro 101-105 al ENTRAR en el paso. BossSwitch = interruptor del bloque 1 (0 = sin jefe de bloque 1: gimnasios usan S4-S11, Alto Mando S12). Generado por build_event_architecture.py.\n']
for (k, b), s in zip(steps, STEPS):
    kv = {'MilestoneID': s['n'], 'Var50Cap': s['capD'], 'Var111Cap': s['capN'], 'ActVar': s['act'], 'ChapterVar': s['chapter'],
          'TramoVar': s['n'], 'MedalsVar': s['medals'], 'FragmentsVar': s['frags'], 'BossSwitch': boss_sw.get(s['n'], 0),
          'StoryVarID': HVAR[s['loc']]}
    res.append(setkeys(b, kv))
wr('PBS/rem_progression.txt', '\n'.join(res))

# ------------------------------------------------------------------ JSON para Ruby
arch = dict(vars={str(i): n for i, n in sorted(VARS.items())}, switches={str(i): n for i, n in sorted(SW.items())},
            var_len=251, switch_len=831,
            milestones=[dict(id=s['n'], act=s['act'], chapter=s['chapter'], capD=s['capD'], capN=s['capN'], medals=s['medals'],
                             frags=s['frags'], boss=boss_sw.get(s['n'], 0), loc=s['loc']) for s in STEPS],
            hvar=HVAR, qvar=QVAR, legsw={str(d): i for d, i in LSW.items()},
            quest_vial={k: [r[1] for r in q['reward'] if r[0] == 'VIAL'][0] for k, q in SQ.items() if any(r[0] == 'VIAL' for r in q['reward'])})
json.dump(arch, open(P('tools/rebalance/phase1/event_arch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ------------------------------------------------------------------ PBS/rem_variables_switches.txt
def sw_block_rows(lo, hi):
    return [(i, SW[i]) for i in sorted(SW) if lo <= i <= hi]
o = ['# Pokémon REM - rem_variables_switches.txt: mapa completo de Variables e Interruptores de Data/System.rxdata (para eventing en RPG Maker XP).',
     '# Generado por tools/rebalance/phase1/build_event_architecture.py; no editar a mano. Formato INI: [BLOQUE] y «ID = Nombre | Rango/Descripción».',
     '# Reservados por Essentials y scripts propios (NO reutilizar): Variables 1-14 (temporales/Essentials), 50 (Tope de nivel); Interruptores 1-58, 72, 100-101, 135 (Boss_Fight doble), 287 (Wonder Trade), 368, 400 (REM_PIA_QUESTS_SWITCH).',
     '# Gimnasios: S4-S11 (Defeated Gym 1-8); Alto Mando: S12. No se duplican en el bloque 1.', '']
o.append('[VARS_TOPE_NIVEL]'); o.append('050 = Tope_Nivel_Actual | Tope de nivel activo (LevelCapDay del hito vigente; lo lee 194_Level_Cap)'); o.append('')
o.append('[VARS_MACRO]')
for i, n, d in MACRO: o.append('%03d = %s | %s' % (i, n, d))
o += ['', '[VARS_TOPE_NIVEL_POR_HITO]', '# Hito = STEP_NN: Día / Noche / Acto / Capítulo global / Medallas / Fragmentos / Interruptor de jefe']
for s in STEPS:
    o.append('M%02d = cap %d / %d | Acto %d | Cap. %d | Med. %d | Frag. %d | Jefe S%s | %s%s' %
             (s['n'], s['capD'], s['capN'], s['act'], s['chapter'], s['medals'], s['frags'], boss_sw.get(s['n'], '—'), s['name'],
              (' | ' + s['boss']) if s['boss'] else ''))
o += ['', '[VARS_HISTORIA_LOCAL_64]', '# 0 = Sin iniciar · 1..N = pasos intermedios · 99 = Evento de historia completado']
for d in order: o.append('%03d = %s | %s · %s · Acto %s · mapa %s' % (HVAR[d['key']], VARS[HVAR[d['key']]], d['key'], d['cat'], d['act'], d['mapid']))
o += ['', '[VARS_SIDEQUESTS_40]', '# 0 = No iniciada · 1 = Activa / Paso 1 · 2 = Paso 2 (puzle o combate local) · 3 = Lista para entregar · 99 = Completada']
for d in KEY40:
    q = SQ[d['key']]
    rw = '; '.join(('%s Nv %s' % (INTERNAL[r[1]].title(), r[2] if r[3] != 'Huevo' else '5 (huevo)')) if r[0] == 'MON' else
                   ('Pokévial %d cargas' % r[1] if r[0] == 'VIAL' else '%s x%d' % (r[1], r[2])) for r in q['reward'])
    o.append('%03d = %s | %s · «%s» · %s' % (QVAR[d['key']], VARS[QVAR[d['key']]], d['key'], q['title'], rw))
for (title, lo, hi), tag in zip(BLOCKS, ['BOSSES', 'TOOLS', 'ROADBLOCKS', 'UNIQUE', 'LEGENDARIES']):
    o += ['', '[SWITCHES_%s]' % tag, '# %s (rango %d-%d)' % (title, lo, hi)]
    for i, n in sw_block_rows(lo, hi):
        extra = ''
        if tag == 'ROADBLOCKS':
            extra = ' | ' + [d for nn, d, lk in ROADBLOCKS if nn == n][0] + ' · ' + [lk for nn, d, lk in ROADBLOCKS if nn == n][0]
        if tag == 'LEGENDARIES':
            dx = int(n.split('_')[1]); extra = ' | %s · %s' % (NEWOBT[dx][1], NEWOBT[dx][3].split('Condición: ')[1].split(' · ')[0])
        o.append('%03d = %s%s' % (i, n, extra))
wr('PBS/rem_variables_switches.txt', '\n'.join(o) + '\n')

# ------------------------------------------------------------------ docs/rebalance/12_Variables_Switches_Reference.md
md = ['# 12 · Variables, Interruptores y Sidequests — Referencia de eventing', '',
      'Consulta rápida para RPG Maker XP. Fuente única: `PBS/rem_variables_switches.txt` (generado por `tools/rebalance/phase1/build_event_architecture.py`; se inyecta en `Data/System.rxdata` con `tools/scripts_dump/build_system.rb`).', '',
      '**Reservados (no reutilizar):** Variables 1-14 y 50; Interruptores 1-58, 72, 100-101, 135, 287, 368, 400 (`REM_PIA_QUESTS_SWITCH`). Gimnasios = S4-S11; Alto Mando = S12.', '',
      '## 1. Macro-control (Variables 50 y 101-119)', '', '| ID | Nombre | Rango |', '|---|---|---|', '| 050 | Tope_Nivel_Actual | tope de nivel (lo fija `pbAdvanceMilestone`) |']
for i, n, d in MACRO: md.append('| %03d | %s | %s |' % (i, n, d))
md += ['', '## 2. Tabla de hitos y tope de nivel (`pbAdvanceMilestone(n)`)', '',
       '`pbAdvanceMilestone(n)` fija V50 = tope de día, V111 = tope de noche, V101 acto, V102 capítulo, V103 tramo, V104 fragmentos, V105 medallas, V112 hito máximo, y activa el interruptor de jefe del hito anterior. Hito 69 = Postgame (tope 100).', '',
       '| Hito | Acto | Cap. | Tope día | Tope noche | Medallas | Frag. | Int. jefe | Tramo / jefe |', '|---|---|---|---|---|---|---|---|---|']
for s in STEPS:
    md.append('| %d | %d | %d | %d | %d | %d | %d | %s | %s%s |' % (s['n'], s['act'], s['chapter'], s['capD'], s['capN'], s['medals'], s['frags'],
              ('S%d' % boss_sw[s['n']]) if s['n'] in boss_sw else '—', s['name'], (' — ' + s['boss']) if s['boss'] else ''))
md += ['', '## 3. Historia local — 64 variables (121-184)', '', '0 = sin iniciar · 1..N = pasos · 99 = completado. Nombre `H_` = nombre actual del mapa (ver LOC_KEY por si el nombre cambió respecto a borradores).', '',
       '| Var | Nombre | LOC_KEY | Categoría | Acto |', '|---|---|---|---|---|']
for d in order: md.append('| %d | %s | %s | %s | %s |' % (HVAR[d['key']], VARS[HVAR[d['key']]], d['key'], d['cat'], d['act']))
md += ['', '## 4. Sidequests locales — 40 variables (201-240)', '', '0 = no iniciada · 1 = paso 1 · 2 = paso 2 (puzle/combate local) · 3 = lista para entregar · 99 = completada.', '',
       '| Var | Nombre | Sidequest | Mini-mecánica (paso 2) | Recompensa final |', '|---|---|---|---|---|']
for d in KEY40:
    q = SQ[d['key']]
    rw = '; '.join(('%s Nv %s' % (INTERNAL[r[1]].title(), r[2] if r[3] != 'Huevo' else '5 (huevo)')) if r[0] == 'MON' else
                   ('Pokévial %d cargas' % r[1] if r[0] == 'VIAL' else '%s x%d' % (r[1], r[2])) for r in q['reward'])
    md.append('| %d | %s | %s | %s | %s |' % (QVAR[d['key']], VARS[QVAR[d['key']]], q['title'], q['s2'].replace('|', '/'), rw))
for (title, lo, hi), tag in zip(BLOCKS, ['BOSSES', 'TOOLS', 'ROADBLOCKS', 'UNIQUE', 'LEGENDARIES']):
    md += ['', '## %d. Interruptores — %s (%d-%d)' % (5 + ['BOSSES', 'TOOLS', 'ROADBLOCKS', 'UNIQUE', 'LEGENDARIES'].index(tag), title, lo, hi), '', '| ID | Nombre |', '|---|---|']
    for i, n in sw_block_rows(lo, hi): md.append('| %d | %s |' % (i, n))
md += ['', '## 10. Obtenibilidad cerrada de Pokémon de evento y legendarios', '',
       'Las 25 especies EVENT salen de las sidequests (sección 4); las 54 LEGENDARY tienen condición e interruptor (bloque 5). Las 18 iniciales las gestiona Pía, los 11 fósiles el Museo Minero. No queda ninguna especie sin método (0/721 con «propuesto» o PENDIENTE).', '',
       '| Dex | Especie | Método | Ubicación | Detalle |', '|---|---|---|---|---|']
for d in sorted(NEWOBT):
    if NEWOBT[d][0] in ('EVENT', 'LEGENDARY'):
        md.append('| %03d | %s | %s | %s | %s |' % (d, INTERNAL[d].title(), NEWOBT[d][0], NEWOBT[d][1], NEWOBT[d][3].replace('|', '/')))
open(P('docs/rebalance/12_Variables_Switches_Reference.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(md) + '\n')
print('vars', len(VARS), 'switches', len(SW), 'b1', len(b1), 'uniq', len(UNIQ), 'items rows', total, 'event', len(EV), 'legend', len(LEG))

# ------------------------------------------------------------------ tools/scripts_dump/rem_events.rb (Ruby 1.8 / RGSS1)
rb = ['#===============================================================================',
      '# REM_Events — hitos, tope de nivel y variables de eventos. GENERADO por',
      '# tools/rebalance/phase1/build_event_architecture.py; no editar a mano.',
      '# IDs: Variables 50/101-119/121-184/201-240; Interruptores 501-820 (ver PBS/rem_variables_switches.txt).',
      '#===============================================================================',
      'REM_VAR_CAP=50', 'REM_VAR_ACTO=101', 'REM_VAR_CAPITULO=102', 'REM_VAR_TRAMO=103', 'REM_VAR_FRAGMENTOS=104', 'REM_VAR_MEDALLAS=105',
      'REM_VAR_VIAL_MAX=106', 'REM_VAR_VIAL_ACTUAL=107', 'REM_VAR_CAP_NOCHE=111', 'REM_VAR_HITO_MAX=112', 'REM_VAR_DOMINANTES=113',
      'REM_VAR_BASES=114', 'REM_VAR_SIDEQUESTS=115', 'REM_VAR_LEGENDARIOS=116', 'REM_VAR_RIVALES=117', '',
      '# Hito = paso STEP_NN. Fila: [acto, capitulo, tope_dia, tope_noche, medallas, fragmentos, interruptor_jefe]. Hito 69 = Postgame.',
      'REM_MILESTONES=[nil,']
for s in STEPS:
    rb.append(' [%d,%d,%d,%d,%d,%d,%d],' % (s['act'], s['chapter'], s['capD'], s['capN'], s['medals'], s['frags'], boss_sw.get(s['n'], 0)))
rb.append(' [6,68,100,100,8,6,0]]')
rb.append('REM_STORY_VAR={' + ','.join(':%s=>%d' % (k, v) for k, v in HVAR.items()) + '}')
rb.append('REM_QUEST_VAR={' + ','.join(':%s=>%d' % (k, v) for k, v in QVAR.items()) + '}')
rb.append('REM_QUEST_VIAL={' + ','.join(':%s=>%d' % (k, v) for k, v in arch['quest_vial'].items()) + '}')
rb.append('REM_LEGEND_SWITCH={' + ','.join('%d=>%d' % (d, i) for d, i in LSW.items()) + '}')
rb += ['REM_DOMINANT_STEPS=[5,17,26,31,44,51]', 'REM_BASE_STEPS=[15,45,52]', 'REM_RIVAL_STEPS=[%s]' % ','.join(str(s['n']) for s in STEPS if s['boss'].startswith('Rival')), '',
'# Avanza al hito m (1..69): fija tope de nivel, acto, capítulo, medallas, fragmentos y marca los jefes de los hitos anteriores.',
'# Nunca retrocede: si m es menor que el hito máximo ya alcanzado, no hace nada.',
'def pbAdvanceMilestone(m)',
'  m=m.to_i',
'  m=1 if m<1',
'  m=REM_MILESTONES.length-1 if m>REM_MILESTONES.length-1',
'  return false if m<$game_variables[REM_VAR_HITO_MAX]',
'  if m>1',
'    for i in 1...m',
'      b=REM_MILESTONES[i][6]',
'      $game_switches[b]=true if b>0',
'    end',
'    $game_variables[REM_VAR_DOMINANTES]=REM_DOMINANT_STEPS.select{|s| s<m}.length',
'    $game_variables[REM_VAR_BASES]=REM_BASE_STEPS.select{|s| s<m}.length',
'    $game_variables[REM_VAR_RIVALES]=REM_RIVAL_STEPS.select{|s| s<m}.length',
'  end',
'  e=REM_MILESTONES[m]',
'  $game_variables[REM_VAR_CAP]=e[2]',
'  $game_variables[REM_VAR_CAP_NOCHE]=e[3]',
'  $game_variables[REM_VAR_ACTO]=e[0]',
'  $game_variables[REM_VAR_CAPITULO]=e[1]',
'  $game_variables[REM_VAR_TRAMO]=m',
'  $game_variables[REM_VAR_MEDALLAS]=e[4]',
'  $game_variables[REM_VAR_FRAGMENTOS]=e[5]',
'  $game_variables[REM_VAR_HITO_MAX]=m',
'  pbRemEnsureVialVars',
'  $game_map.need_refresh=true if $game_map',
'  return true',
'end',
'',
'# Tope de nivel vigente según la hora del juego (noche usa la variable 111).',
'def pbRemCurrentLevelCap',
'  night=(PBDayNight.isNight? rescue false)',
'  v=$game_variables[night ? REM_VAR_CAP_NOCHE : REM_VAR_CAP]',
'  return v>0 ? v : $game_variables[REM_VAR_CAP]',
'end',
'',
'# Sincroniza las variables de Pokévial (106/107) con el estado real del objeto.',
'def pbRemEnsureVialVars',
'  $game_variables[REM_VAR_VIAL_MAX]=pbRemVialMax',
'  $game_variables[REM_VAR_VIAL_ACTUAL]=pbRemVialCharges',
'end',
'# Sube el máximo del Pokévial a n cargas como mínimo (idempotente con las misiones n.º 6 y 17 de Pía).',
'def pbRemVialSetMin(n)',
'  return if !$PokemonGlobal',
'  n=[[n,1].max,3].min',
'  return if pbRemVialMax>=n',
'  $PokemonGlobal.remVialMax=n',
'  $PokemonGlobal.remVialCharges=n',
'  pbRemEnsureVialVars',
'end',
'',
'# Historia local (variables H_*, 121-184). loc = símbolo LOC_KEY, p. ej. :PUEBLO_IOLITA.',
'def pbStoryVar(loc)',
'  id=REM_STORY_VAR[loc]',
'  return id ? $game_variables[id] : 0',
'end',
'def pbSetStoryVar(loc,n)',
'  id=REM_STORY_VAR[loc]',
'  return if !id',
'  $game_variables[id]=n',
'  $game_map.need_refresh=true if $game_map',
'end',
'',
'# Sidequests locales (variables M_*, 201-240): 0 no iniciada, 1 paso 1, 2 paso 2, 3 lista para entregar, 99 completada.',
'def pbQuestState(loc)',
'  id=REM_QUEST_VAR[loc]',
'  return id ? $game_variables[id] : 0',
'end',
'def pbSetQuestState(loc,n)',
'  id=REM_QUEST_VAR[loc]',
'  return false if !id',
'  old=$game_variables[id]',
'  return false if old==99',
'  $game_variables[id]=n',
'  if n==99',
'    $game_variables[REM_VAR_SIDEQUESTS]+=1',
'    pbRemVialSetMin(REM_QUEST_VIAL[loc]) if REM_QUEST_VIAL[loc]',
'  end',
'  $game_map.need_refresh=true if $game_map',
'  return true',
'end',
'',
'# Legendarios (interruptores 761-814): marca la especie dex como obtenida una sola vez.',
'def pbMarkLegendary(dex)',
'  id=REM_LEGEND_SWITCH[dex]',
'  return false if !id || $game_switches[id]',
'  $game_switches[id]=true',
'  $game_variables[REM_VAR_LEGENDARIOS]+=1',
'  return true',
'end', '']
open(P('tools/scripts_dump/rem_events.rb'), 'w', encoding='utf-8', newline='\n').write('\n'.join(rb))
print('rem_events.rb ok')
