# executed inside v4_build namespace: applies status DSL and the ability-synergy flag audit
def parse_sta():
    for raw in v4_sta.STA.split('\n'):
        raw = raw.strip()
        if not raw or raw.startswith('#'): continue
        body, _, why = raw.partition('#')
        t = body.split(); name = t[0]; t = t[1:]
        assert name in bm, name
        m = bm[name]; typ = None; pos = []; tgt = fl = None
        for x in t:
            if x.startswith('>'): typ = x[1:]
            elif x.startswith('tgt='): tgt = x[4:]
            elif x.startswith('flags='): fl = x[6:]
            else: pos.append(x)
        assert len(pos) in (2, 3), (name, pos)
        acc, donor = pos[-2], pos[-1]
        if typ: m['type'] = typ
        if donor == 'ORIG':
            o = m['old']
            m['func'], m['target'], m['prio'], m['addl'], m['flags'] = o['func'], o['target'], o['prio'], o['addl'], o['flags']; m['acc'] = o['acc']; m['donor'] = None; m['newdesc'] = None
            m['fx'] = 'original mechanic kept'
        elif donor != '=':
            d = orig[donor]
            m['func'], m['target'], m['prio'], m['addl'], m['flags'] = d['func'], d['target'], d['prio'], d['addl'], d['flags']
            m['acc'] = d['acc']; m['donor'] = donor
            m['fx'] = 'Rework: ' + v4_sta.DONOR_ES.get(donor, '').rstrip('.')
            l = lore(m) if m['cat'] == 'Status' else ''
            m['newdesc'] = (l + ' ' + v4_sta.DONOR_ES[donor]).replace('"', '')
        if tgt: m['target'] = tgt
        if fl: m['flags'] = fl
        if name == 'MIST': m['func'] = '00C'      # Will-O-Wisp's target/flags, but the Frostbite (freeze) function
        if acc != '=': m['acc'] = int(acc)
        m['why'] = why.strip()
parse_sta()

# ---- ability-synergy flag audit (Iron Fist, Strong Jaw, Mega Launcher, Punk Rock, bomb/dance users) ----
SYN = {
 'j': ('punch (Iron Fist)', 'FIREPUNCH ICEPUNCH THUNDERPUNCH DRAINPUNCH MACHPUNCH MEGAPUNCH DIZZYPUNCH DYNAMICPUNCH BULLETPUNCH HAMMERARM POWERUPPUNCH FOCUSPUNCH METEORMASH SHADOWPUNCH SKYUPPERCUT COMETPUNCH ICEHAMMER'),
 'i': ('bite (Strong Jaw)', 'BITE CRUNCH FIREFANG ICEFANG THUNDERFANG POISONFANG PSYCHICFANGS HYPERFANG SUPERFANG JAWLOCK'),
 'k': ('sound (Punk Rock)', 'BOOMBURST HYPERVOICE SNARL BUGBUZZ CHATTER ECHOEDVOICE ROUND SPARKLINGARIA UPROAR DISARMINGVOICE OVERDRIVE SNORE SING SUPERSONIC GRASSWHISTLE METALSOUND SCREECH GROWL ROAR PERISHSONG NOBLEROAR RELICSONG'),
 'm': ('pulse (Mega Launcher)', 'AURASPHERE DARKPULSE DRAGONPULSE WATERPULSE ORIGINPULSE TERRAINPULSE'),
 'n': ('bomb/ball (Bulletproof)', 'ACIDSPRAY AURASPHERE BARRAGE BULLETSEED EGGBOMB ELECTROBALL ENERGYBALL FOCUSBLAST GYROBALL ICEBALL MAGNETBOMB MUDBOMB OCTAZOOKA POLLENPUFF PYROBALL ROCKBLAST ROCKWRECKER SEEDBOMB SHADOWBALL SLUDGEBOMB WEATHERBALL ZAPCANNON'),
 'o': ('dance (Dancer)', 'FIERYDANCE PETALDANCE REVELATIONDANCE FEATHERDANCE DRAGONDANCE QUIVERDANCE SWORDSDANCE TEETERDANCE VICTORYDANCE'),
}
syn_added = []
for fl, (label, names) in SYN.items():
    for n in names.split():
        m = bm.get(n)
        if not m or m['sig']: continue
        if fl not in m['flags']:
            m['flags'] += fl; syn_added.append((n, fl))
            tag = f'Ability-synergy audit: {label} flag was missing.'
            m['why'] = (m['why'] + ' ' + tag).strip() if m['why'] else tag
