import collections, sys
import v4_build as B
from v4_fams import FAMS
def tier(m):
    if m['func'] == '08B': return 'L'
    bp = m['bp']
    return None if bp <= 1 else 'E' if 40 <= bp <= 65 else 'M' if 70 <= bp <= 85 else 'L' if bp >= 90 else None
def mech(m):
    f = m['func']
    if f == '0': f = '000'
    if m['prio'] > 0 and f == '000': k = 'prio+'
    elif f == '000': k = 'crit' if 'h' in m['flags'] else 'plain'
    elif f == '0C0' and 'h' in m['flags']: k = 'multicrit'
    else: k = B.CODE2FAM.get(f, 'u' + f)
    if f in ('010',): k = 'flinch'
    if f in ('008', '009'): k = 'para' if f == '008' else 'u009'
    if f == '00D': k = 'freeze'
    if 'h' in m['flags'] and k not in ('crit', 'multicrit'): k += '+h'
    if f in ('007','00A','00C','013','005','006') and 30 <= m['addl'] < 100: k += '~hi'
    if m['addl'] == 100 and f in ('007','00A','00C','013','00F','005','042','043','044','045','046','047','04F'): k += '!'
    return (k, m['target'] not in ('00',) , 1 if m['prio'] else 0)
def run():
    atk = [m for m in B.new if not m['sig'] and m['cat'] != 'Status']
    rep = {}
    rep['acc_bad'] = [(m['internal'], m['acc']) for m in atk if m['acc'] not in (0, 90, 95, 100) and m['internal'] not in B.NUKE85 and m['internal'] not in B.EXEMPT]
    rep['acc85'] = [m['internal'] for m in atk if m['acc'] == 85 and m['internal'] not in B.NUKE85]
    coll = []
    for t in B.TYPES if hasattr(B, 'TYPES') else engine_types():
        for c in ('Physical', 'Special'):
            g = [m for m in atk if m['type'] == t and m['cat'] == c and m['bp'] >= 50 or (m['type'] == t and m['cat'] == c and m['func'] == '08B')]
            for i, a in enumerate(g):
                for b in g[i + 1:]:
                    if abs(a['bp'] - b['bp']) <= 10 and mech(a) == mech(b) and a['bp'] > 1 and b['bp'] > 1: coll.append((t, c, a['internal'], b['internal'], mech(a)[0], a['bp'], b['bp']))
    rep['collisions'] = coll
    rep['plain50'] = [(m['internal'], m['bp']) for m in atk if m['bp'] >= 50 and mech(m)[0] == 'plain']
    clumps = []
    for t in engine_types():
        for c in ('Physical', 'Special'):
            cnt = collections.Counter(m['bp'] for m in atk if m['type'] == t and m['cat'] == c and m['bp'] >= 40 and not m['prio'])
            clumps += [(t, c, bp, n) for bp, n in cnt.items() if n >= 3]
    PROT=set('SOLARBEAM SOLARBLADE SKULLBASH SKYATTACK METEORBEAM PHANTOMFORCE FLY BOUNCE DIG DIVE HYPERBEAM GIGAIMPACT ROCKWRECKER DOUBLEEDGE FLAREBLITZ BRAVEBIRD WOODHAMMER WILDCHARGE VOLTTACKLE TAKEDOWN SUBMISSION HEADCHARGE HEADSMASH CLOSECOMBAT SUPERPOWER OVERHEAT DRACOMETEOR LEAFSTORM HAMMERARM JUMPKICK HIGHJUMPKICK FOCUSPUNCH OUTRAGE THRASH PETALDANCE RAGINGFURY ERUPTION WATERSPOUT MULTIATTACK LASTRESORT DYNAMICPUNCH'.split())
    rep['clumps'] = [c for c in clumps if sum(1 for m in atk if m['type']==c[0] and m['cat']==c[1] and m['bp']==c[2] and m['internal'] not in PROT and not m['prio'])>=5]
    cov = collections.defaultdict(collections.Counter)
    for m in atk:
        tr = tier(m)
        if tr: cov[m['type'], m['cat']][tr] += 1
    rep['empty'] = [(t, c, k) for t in engine_types() for c in ('Physical', 'Special') for k in 'EML' if cov[t, c][k] == 0]
    rep['thin'] = [(t, c, k, cov[t, c][k]) for t in engine_types() for c in ('Physical', 'Special') for k in 'EML' if cov[t, c][k] == 1]
    return rep, cov
def engine_types():
    import engine; return engine.TYPES
if __name__ == '__main__':
    rep, cov = run()
    atk = [m for m in B.new if not m['sig'] and m['cat'] != 'Status']
    print('attacks changed', sum(B.changed(m) for m in atk), 'of', len(atk))
    for k, v in rep.items(): print(k, len(v), v[:60])
