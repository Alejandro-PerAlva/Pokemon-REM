"""Construye el modelo del Codex móvil: ModelBuilder del escritorio + saneado (sin historia/personajes/jefes/Pía)."""
import json, os, re, sys

def _scrub_text(s):
    return s

DROP_TOP = ['missions', 'progression', 'characters', 'story', 'prelude', 'ledger', 'ledgerMeta', 'prunedItems', 'changelogMeta']
BANNED = re.compile(r'Pía|Pia\b|Morfeo|Dominante|capítulo|cap[ií]tulo|Acto [IVX]', re.I)
KEEP_OBTAIN = ('WILD', 'FISHING', 'EVOLUTION_LEVEL', 'EVOLUTION_STONE', 'EVOLUTION_ITEM', 'THIRD_STAGE')

def _strip_story(t):
    t = re.sub(r'\s*\(línea inicial:.*\)\s*$', '', t or '')
    t = re.sub(r'\s*·?\s*\(?Acto [IVX]+\)?', '', t)
    return t.strip()

def sanitize(m):
    for k in DROP_TOP:
        if k in m:
            m[k] = [] if isinstance(m[k], list) else ({} if isinstance(m[k], dict) else None)
    meta = m.get('meta', {})
    meta['mobile'] = True
    for p in m['pokemon']:
        for k in ('role', 'notes', 'diffNotes'):
            p.pop(k, None)
        ob = []
        for o in p.get('obtain', []):
            if o.get('method') in KEEP_OBTAIN:
                o = dict(o); o['detail'] = _strip_story(o.get('detail')); ob.append(o)
            else:
                ob.append({'method': 'PENDIENTE', 'loc': None, 'level': None, 'detail': 'PENDIENTE'})
        seen = set(); p['obtain'] = [o for o in ob if not (o['method'] == 'PENDIENTE' and (o['method'] in seen or seen.add(o['method'])))]
        for w in p.get('wild', []):
            w.pop('note', None)
        for w in p.get('wildItems', []) if isinstance(p.get('wildItems'), list) else []:
            if isinstance(w, dict): w.pop('note', None)
    for l in m['locations']:
        for k in ('boss', 'chapters', 'charKeys', 'characters', 'events', 'steps', 'etymology', 'situation', 'description', 'draftNames', 'act', 'mapIdStatus'):
            if k in l: l[k] = [] if isinstance(l[k], list) else None
        for z in l.get('encounters', []) or []:
            for s in z.get('slots', []) or []: s.pop('note', None)
        for k in ('fishing',):
            for s in (l.get(k) or []):
                if isinstance(s, dict): s.pop('note', None)
        for it in l.get('items', []) or []:
            it.pop('note', None)
    for it in m['items']:
        it.pop('missions', None); it.pop('note', None)
        for w in it.get('where', []) or []: w.pop('note', None)
    for t in m['tms']:
        t.pop('missions', None)
        for w in t.get('where', []) or []: w.pop('note', None)
    for s in m['shops']:
        s['description'] = ''; s['requirement'] = ''
        s.pop('itemNotes', None)
    _final_scrub(m)
    m['warnings'] = []; m['files'] = []
    meta['health'] = {'status': 'ok', 'errors': 0, 'warnings': 0}
    for l in m['locations']:
        _drop_notes(l)
    m = _sweep(m)
    return m

_PAREN = re.compile(r'\s*\([^()]*(?:Morfeo|Dominante|Pía)[^()]*\)')
def _sweep_str(s):
    s = _PAREN.sub('', s)
    if BANNED.search(s):
        parts = re.split(r'(?<=[.!?»])\s+', s)
        s = ' '.join(x for x in parts if not BANNED.search(x))
    return s

def _drop_notes(o):
    if isinstance(o, dict):
        o.pop('note', None)
        for v in o.values(): _drop_notes(v)
    elif isinstance(o, list):
        for v in o: _drop_notes(v)

def _sweep(o):
    if isinstance(o, str): return _sweep_str(o)
    if isinstance(o, list): return [_sweep(v) for v in o]
    if isinstance(o, dict): return {k: _sweep(v) for k, v in o.items()}
    return o

def _clean_zone(z):
    if not isinstance(z, str): return z
    z = re.sub(r'\s*\([^)]*(Morfeo|Dominante)[^)]*\)', '', z)
    z = re.sub(r'^(Gimnasio \d+) · .*$', r'\1', z)
    if BANNED.search(z): return None
    return z

def _final_scrub(m):
    for coll in (m['items'], m['tms']):
        for it in coll:
            w = []
            for e in it.get('where', []) or []:
                if re.search(r'Pía|Pia\b', json.dumps(e, ensure_ascii=False)): continue
                if 'zone' in e: e['zone'] = _clean_zone(e['zone'])
                w.append(e)
            it['where'] = w
    for p in m['pokemon']:
        for w in p.get('wild', []) or []:
            if 'zoneName' in w: w['zoneName'] = _clean_zone(w['zoneName'])
    for l in m['locations']:
        for z in l.get('encounters', []) or []:
            if 'zoneName' in z: z['zoneName'] = _clean_zone(z['zoneName'])
        for k in ('items',):
            for e in list(l.get(k) or []):
                if re.search(r'Pía|Pia\b', json.dumps(e, ensure_ascii=False)): l[k].remove(e)
                elif 'zone' in e: e['zone'] = _clean_zone(e['zone'])
        for k in ('fishingZones', 'zoneList'):
            if isinstance(l.get(k), list):
                l[k] = [(_clean_zone(x) if isinstance(x, str) else x) for x in l[k]]

def build(pbs_dir, assets_json, root='/nonexistent'):
    here = os.path.dirname(os.path.abspath(__file__))
    from codex.model import ModelBuilder
    assets = json.load(open(assets_json, encoding='utf-8'))
    class MB(ModelBuilder):
        def get_assets(self, n_types): return json.loads(json.dumps(assets))
    mb = MB(pbs_dir, root=root, backup_dir='/nonexistent_backup')
    m = mb.build()
    if isinstance(m, tuple): m = m[0]
    return sanitize(m)

if __name__ == '__main__':
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    sys.path.insert(0, root)
    m = build(os.path.join(root, 'PBS'), os.path.join(root, 'tools', 'mobile', 'assets.json'), root)
    out = sys.argv[1]
    open(out, 'w', encoding='utf-8').write(json.dumps(m, ensure_ascii=False, separators=(',', ':')))
    s = json.dumps(m, ensure_ascii=False)
    print('bytes', len(s), 'banned hits:', collections_hits if False else [(w, len(re.findall(w, s, re.I))) for w in ['Pía', 'Morfeo', 'Dominante', 'capítulo', 'Acto ']])
