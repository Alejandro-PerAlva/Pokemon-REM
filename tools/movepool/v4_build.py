import os, sys, re, csv, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE)); RB = os.path.join(ROOT, 'docs', 'rebalance')
os.makedirs(RB, exist_ok=True); sys.path.insert(0, HERE)
import engine, v2_data as D
from rules import SIGNATURE
from v4_fams import FAMS
import v4_atk, v4_sta
from xml.sax.saxutils import escape as esc

import subprocess, tempfile
_TMP = os.path.join(tempfile.gettempdir(), 'rem_scripts_extract')
SCRIPT = os.path.join(_TMP, '083_PokeBattle_MoveEffects.rb')
if not os.path.exists(SCRIPT):   # decompile Data/Scripts.rxdata with the read-only extractor
    subprocess.run(['ruby', os.path.join(ROOT, 'tools', 'extract_scripts.rb'), os.path.join(ROOT, 'Data', 'Scripts.rxdata'), _TMP], check=True, stdout=subprocess.DEVNULL)
CODES = set(re.findall(r'class PokeBattle_Move_(\w+)', open(SCRIPT, encoding='utf-8', errors='replace').read()))
NUKE85 = {'FIREBLAST', 'HYDROPUMP', 'THUNDER', 'BLIZZARD', 'HURRICANE', 'FOCUSBLAST', 'GUNKSHOT', 'MEGAHORN'}
EXEMPT = {'DYNAMICPUNCH', 'INFERNO', 'ZAPCANNON'}
K = ('type', 'cat', 'bp', 'acc', 'prio', 'func', 'addl', 'flags', 'target')
SIG = set(SIGNATURE)
ES = D.ES_TYPE
CODE2FAM = {}
for n, f in FAMS.items():
    if f[0] != '000' and f[0] not in CODE2FAM: CODE2FAM[f[0]] = n

old, lines = engine.parse()
orig = {m['internal']: m for m in old}
new = []
for o in old:
    m = dict(o); m['old'] = {k: o[k] for k in K + ('pp',)}; m['sig'] = o['internal'] in SIG; m['why'] = ''; m['newdesc'] = None; m['fam'] = None; m['fx'] = ''
    new.append(m)
bm = {m['internal']: m for m in new}

def lore(m):
    d = m['desc'].strip().strip('"')
    sents = [x.strip().rstrip('.') for x in re.split(r'(?<=[.!?])\s+', d) if x.strip()]
    eff = re.compile(r"(puede|también|baja|sube|aumenta|reduce|disminuye|probabilidad|siempre|retroceder|quema|paraliz|envenen|conge|confund|crítico|prioridad|%|doble|potencia|recupera|restaur|descans|turno|cura|intercambia|impide|evita|cambia)", re.I)
    keep = [s for s in sents if not eff.search(s)]
    if keep: return keep[0] + '.'
    if sents:
        head = re.split(r',? y (?:puede|también)|, (?:puede|aunque)| que (?:puede|también)| puede ', sents[0], flags=re.I)[0].strip()
        if len(head) > 10 and not eff.search(head): return head + '.'
    return f"Un movimiento de tipo {ES[m['type']]}."

def apply_fam(m, name, chance):
    f = FAMS[name]
    m['func'] = f[0]
    m['addl'] = chance if chance is not None else f[1]
    if f[6] is not None: m['prio'] = f[6]
    fl = m['flags']
    for c in f[4]:
        if c not in fl: fl += c
    for c in f[5]: fl = fl.replace(c, '')
    m['flags'] = fl
    m['fam'] = name

def parse_atk():
    seen = set()
    for raw in v4_atk.ATK.split('\n'):
        raw = raw.strip()
        if not raw or raw.startswith('#'): continue
        body, _, why = raw.partition('#')
        t = body.split(); name = t[0]; t = t[1:]
        assert name in bm, name
        seen.add(name)
        m = bm[name]; typ = cat = None; fadd = fdel = ''
        pos = []
        forig = False
        for x in t:
            if x == 'forig': forig = True
            elif x.startswith('>'): typ = x[1:]
            elif x.startswith('~'): cat = x[1:]
            elif x.startswith('f+'): fadd += x[2:]
            elif x.startswith('f-'): fdel += x[2:]
            else: pos.append(x)
        assert len(pos) == 3, (name, pos)
        bp, acc, fam = pos
        if typ: m['type'] = typ
        if cat: m['cat'] = cat
        if bp != '=': m['bp'] = int(bp)
        if acc != '=': m['acc'] = int(acc)
        if forig: m['flags'] = m['old']['flags']
        if fam == 'orig' or fam.startswith('orig:'):
            m['func'] = m['old']['func']; m['addl'] = int(fam.split(':')[1]) if ':' in fam else m['old']['addl']; m['fam'] = None; m['fx'] = 'original function restored'
        elif fam.startswith('=:'):
            m['addl'] = int(fam[2:]); m['fx'] = 'effect chance set to ' + fam[2:]
        elif fam != '=':
            fn, _, ch = fam.partition(':')
            apply_fam(m, fn, int(ch) if ch else None)
            m['fx'] = FAMS[fn][2]
        for c in fadd:
            if c not in m['flags']: m['flags'] += c
        for c in fdel: m['flags'] = m['flags'].replace(c, '')
        m['why'] = why.strip()
        o = m['old']
        m['newdesc'] = None
        if (m['func'], m['addl']) != (o['func'], o['addl']) and m['fam'] and FAMS[m['fam']][3] and name not in ('RAZORWIND',):
            m['newdesc'] = (lore(m) + ' ' + FAMS[m['fam']][3]).replace('"', '')
        if m['func'] != o['func'] and m['fam'] in ('hpscale',):
            m['newdesc'] = (lore(m) + ' ' + FAMS['hpscale'][3]).replace('"', '')
        if name == 'RAZORWIND': m['newdesc'] = None
parse_atk()
DESC_FIX = {'FISSURE': 'Abre una grieta en el suelo y lanza al objetivo contra ella. El usuario debe descansar en el turno siguiente.',
            'GUILLOTINE': 'Corta al objetivo con unas pinzas afiladísimas. Suele ser crítico, pero el usuario sufre 1/3 del daño causado.',
            'HORNDRILL': 'Taladra al objetivo con el cuerno, ignorando los cambios de Defensa y Evasión que haya sufrido.',
            'SHEERCOLD': 'Lanza un frío polar devastador sobre el objetivo. Baja mucho el Ataque Especial del usuario.'}
for k, v in DESC_FIX.items(): bm[k]['newdesc'] = v
exec(open(os.path.join(HERE, 'v4_sta_apply.py')).read()) if os.path.exists(os.path.join(HERE, 'v4_sta_apply.py')) else None

exec(open(os.path.join(HERE, 'v6_desc.py'), encoding='utf-8').read())

def changed(m): return any(m[k] != m['old'][k] for k in K) or bool(m['newdesc'])
