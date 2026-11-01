import v4_build as B
from v4_fams import FAMS
def compensated(m):
    o = m['old']
    if m['addl'] > o['addl'] and m['func'] == o['func']: return 'chance up'
    if m['func'] != o['func']: return 'new mechanic'
    if m['prio'] > o['prio']: return 'priority'
    if 'h' in m['flags'] and 'h' not in o['flags']: return 'crit'
    if m['acc'] == 0 and o['acc'] != 0: return 'never miss'
    if o['acc'] != 0 and m['acc'] > o['acc'] and m['acc'] - o['acc'] >= 5: return 'accuracy'
    if o['type'] != m['type'] or o['cat'] != m['cat']: return 'retype/recat'
    return None
def nerfs():
    out = []
    for m in B.new:
        if m['sig'] or m['cat'] == 'Status': continue
        o = m['old']
        if o['bp'] > 1 and m['bp'] < o['bp'] and not compensated(m): out.append((m['en'], o['bp'], m['bp']))
    return out
if __name__ == '__main__':
    n = nerfs(); print(len(n), n)
    print('BP drops with compensation:', [(m['en'], m['old']['bp'], m['bp'], compensated(m)) for m in B.new if not m['sig'] and m['cat'] != 'Status' and m['old']['bp'] > 1 and m['bp'] < m['old']['bp'] and compensated(m)])
