import csv, io, json, os, collections
from rules import SIGNATURE, SIG_ADJ, O, NEW, PP_CHANGES

HERE = os.path.dirname(os.path.abspath(__file__))
PBS = os.path.join(HERE, '..', '..', 'PBS', 'moves.txt')
TYPES = ['NORMAL','FIRE','WATER','ELECTRIC','GRASS','ICE','FIGHTING','POISON','GROUND','FLYING','PSYCHIC','BUG','ROCK','GHOST','DRAGON','DARK','STEEL','FAIRY']
EXEMPT_ACC = {'DYNAMICPUNCH', 'INFERNO'}   # 100% status infliction gambles
EN = json.load(open(os.path.join(HERE, 'english_names.json')))
F = dict(id=0, internal=1, es=2, func=3, bp=4, type=5, cat=6, acc=7, pp=8, addl=9, target=10, prio=11, flags=12, desc=13)

def parse():
    raw = open(PBS, encoding='utf-8', newline='').read().split('\n')
    moves, lines = [], []
    for ln in raw:
        if not ln.strip() or ln.startswith('#'):
            lines.append((None, ln)); continue
        row = next(csv.reader([ln.lstrip('\ufeff').rstrip('\r')]))
        m = dict(id=int(row[0]), internal=row[1], es=row[2], func=row[3], bp=int(row[4] or 0), type=row[5], cat=row[6],
                 acc=int(row[7] or 0), pp=int(row[8] or 0), addl=int(row[9] or 0), target=row[10], prio=int(row[11] or 0),
                 flags=row[12], desc=','.join(row[13:]), extra=len(row) > 14)
        m['en'] = EN.get(m['internal'], m['internal'].title())
        m['raw'] = ln; moves.append(m); lines.append((m, ln))
    return moves, lines

def fmt(m, raw=None):
    """PBS line for a move. Edits only columns 3-12 of the original raw line, so descriptions/line endings stay byte-identical."""
    if raw is None and m.get('raw') is not None: raw = m['raw']
    if raw is None:
        return f"{m['id']},{m['internal']},{m['es']},{m['func']},{m['bp']},{m['type']},{m['cat']},{m['acc']},{m['pp']},{m['addl']},{m['target']},{m['prio']},{m['flags']},\"{m['desc']}\""
    bom = raw.startswith('\ufeff'); p = raw.lstrip('\ufeff').split(',', 13)
    p[3:13] = [m['func'], str(m['bp']), m['type'], m['cat'], str(m['acc']), str(m['pp']), str(m['addl']), m['target'], str(m['prio']), m['flags']]
    if m.get('newdesc') and len(p) == 14:
        p[13] = '"' + m['newdesc'] + '"'
    return ('\ufeff' if bom else '') + ','.join(p)

KEYS = ['bp','acc','pp','cat','prio','func','addl','flags']

def is_attack(m): return m['cat'] != 'Status'

def apply(m, ov):
    for k in ('bp','acc','pp','cat','prio','func','addl'):
        if k == 'pp' and m['internal'] not in PP_CHANGES: continue   # PP is only changed where the rationale says so
        if k in ov and ov[k] is not None: m[k] = ov[k]
    fl = m['flags']
    for c in ov.get('fadd', ''):
        if c not in fl: fl += c
    for c in ov.get('fdel', ''):
        fl = fl.replace(c, '')
    m['flags'] = fl
    if 'fx' in ov: m['fx'] = ov['fx']
    if 'why' in ov: m['why'] = ov['why']

def rebalance():
    old, lines = parse()
    new = []
    for o_ in old:
        m = dict(o_); m['old'] = {k: o_[k] for k in KEYS}; m['sig'] = o_['internal'] in SIGNATURE
        m['fx'] = ''; m['why'] = ''; m['auto'] = []
        if m['sig']:
            if m['internal'] in SIG_ADJ: apply(m, SIG_ADJ[m['internal']])
        elif m['internal'] in O:
            apply(m, O[m['internal']])
        new.append(m)
    # --- automatic passes on everything not hand-tuned ---
    for m in new:
        if m['sig'] or m['internal'] in O: continue
        a = m['acc']; bp = m['bp']
        if is_attack(m):
            if 0 < a < 80 and m['internal'] not in EXEMPT_ACC:
                m['acc'] = 80
                if bp >= 60 and a <= 75: m['bp'] = bp - 5
                m['why'] = f"Accuracy floor: {a}% -> 80%" + (f", BP {bp} -> {m['bp']} to pay for it." if m['bp'] != bp else '.')
            elif 70 <= bp <= 80 and m['func'] == '000' and a in (90, 95):
                m['acc'] = 100
                m['why'] = 'Mid-game staples must be reliable (70-80 BP at 100%).'
    # status accuracy
    for m in new:
        if m['cat'] != 'Status' or m['sig'] or m['internal'] in O: continue
        a = m['acc']
        if 0 < a < 80:
            sleepish = m['func'] in ('003', '013', '004')
            m['acc'] = (75 if a < 75 else 80) if sleepish else 85
            m['why'] = f"Status accuracy floor: {a}% -> {m['acc']}%" + (' (sleep/confusion stay <= 80: Sleep Clause is the counterplay).' if sleepish else '.')
    # final safety: no standard attack under 80
    for m in new:
        if m['sig'] or not is_attack(m): continue
        if 0 < m['acc'] < 80 and m['internal'] not in EXEMPT_ACC:
            m['acc'] = 80; m['why'] += ' (floor enforced)'
    nid = max(m['id'] for m in old) + 1
    for n in NEW:
        m = dict(id=nid, internal=n['internal'], es=n['es'], en=n['en'], func=n['func'], bp=n['bp'], type=n['type'], cat=n['cat'],
                 acc=n['acc'], pp=n['pp'], addl=n['addl'], target=n['target'], prio=n['prio'], flags=n['flags'], desc=n['desc'], extra=False)
        m.update(old={k: None for k in KEYS}, sig=False, fx='NEW MOVE: ' + n['desc'], why=n['why'], auto=[], isnew=True)
        new.append(m); nid += 1
    for m in new:
        if is_attack(m) and not m['why'] and not changed(m):
            m['why'] = 'Kept. Niche: ' + role(m) + '.'
    return old, lines, new

FUNC_ROLE = {'0C0':'multi-hit (2-5)','0BD':'double hit','0BE':'triple hit','0FA':'1/4 recoil','0FB':'1/3 recoil','0FC':'1/2 recoil','0C2':'recharge turn',
 '00F':'flinch chance','010':'flinch chance','005':'poison chance','006':'badly-poison','007':'paralysis chance','008':'paralysis chance','009':'paralysis chance','00A':'burn chance','00B':'burn chance',
 '00C':'freeze chance','00D':'freeze chance','013':'confusion chance','0DD':'HP drain','0EE':'pivot after hit','03F':'self SpA -2','03B':'self Atk/Def -1','042':'target Atk -1','043':'target Def -1','044':'target Speed -1',
 '045':'target SpA -1','046':'target SpD -1','047':'target Accuracy -1','0A9':'ignores stat boosts','0CF':'traps target','0C3':'two-turn move','0C4':'two-turn move','0C5':'two-turn move','0C6':'two-turn move','0CA':'two-turn (Dig)','0CB':'two-turn (Dive)'}
def role(m):
    r = []
    if m['prio'] > 0: r.append(f"+{m['prio']} priority")
    elif m['prio'] < 0: r.append(f"{m['prio']} priority")
    if 'h' in m['flags']: r.append('high crit ratio')
    if m['func'] in FUNC_ROLE: r.append(FUNC_ROLE[m['func']])
    if m['target'] not in ('00', '10'): r.append('spread/multi-target')
    if 'a' not in m['flags'] and m['cat'] == 'Physical': r.append('non-contact')
    if m['acc'] == 0: r.append('never misses')
    return ', '.join(r) if r else 'plain reliable hit'

def changed(m):
    if m.get('isnew'): return True
    if m.get('type0') and m['type0'] != m['type']: return True
    return any(m[k] != m['old'][k] for k in KEYS)

def clusters(new):
    g = collections.defaultdict(list)
    for m in new:
        if m['sig'] or not is_attack(m) or m['bp'] <= 1: continue
        g[(m['type'], m['cat'], m['func'], m['bp'], m['acc'], m['pp'], m['prio'], m['addl'], m['flags'], m['target'])].append(m)
    return {k: v for k, v in g.items() if len(v) > 1}

if __name__ == '__main__':
    old, lines, new = rebalance()
    print(len(old), sum(changed(m) for m in new), 'changed;', sum(m['sig'] for m in new), 'sig')
    cl = clusters(new)
    print(len(cl), 'clone clusters')
    for k, v in cl.items(): print(k[:5], [m['internal'] for m in v])
    late = [m for m in new if is_attack(m) and not m['sig'] and 90 <= m['bp'] <= 110 and m['acc'] == 100 and m['func'] == '000' and m['target'] == '00' and 'h' not in m['flags']]
    print('late-tier free hits:', [(m['internal'], m['bp']) for m in late])
    print('auto:', [(m['internal'], m['why'][:40]) for m in new if m['why'] and m['internal'] not in O and not m['sig']])
