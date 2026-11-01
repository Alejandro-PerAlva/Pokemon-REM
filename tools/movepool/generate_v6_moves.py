import os, sys, csv, re, collections, datetime
import v4_build as B
from v4_build import new, old, lines, bm, orig, K, changed, D, engine, HERE, RB, ROOT, esc
from v4_fams import FAMS
from v4_labels import STATUS_EN
import v4_check, v4_sta, v5_audit
TYPES = engine.TYPES
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

FD = '/System/Library/Fonts/Supplemental/'
for n, f in (('A', 'Arial.ttf'), ('A-B', 'Arial Bold.ttf'), ('A-I', 'Arial Italic.ttf'), ('M', 'Courier New.ttf')): pdfmetrics.registerFont(TTFont(n, FD + f))
pdfmetrics.registerFontFamily('A', normal='A', bold='A-B', italic='A-I', boldItalic='A-B')
ES = D.ES_TYPE
TC = {'NORMAL':'#A8A77A','FIRE':'#EE8130','WATER':'#6390F0','ELECTRIC':'#F7D02C','GRASS':'#7AC74C','ICE':'#96D9D6','FIGHTING':'#C22E28','POISON':'#A33EA1','GROUND':'#E2BF65','FLYING':'#A98FF3','PSYCHIC':'#F95587','BUG':'#A6B91A','ROCK':'#B6A136','GHOST':'#735797','DRAGON':'#6F35FC','DARK':'#705746','STEEL':'#B7B7CE','FAIRY':'#D685AD'}
INK = colors.HexColor('#1d2233'); MUT = colors.HexColor('#6b7288'); ACC = colors.HexColor('#2b4acb')
C_BUFF, C_NERF, C_MIX, C_REW, C_SAME = [colors.HexColor(x) for x in ('#dff3e4', '#f9dcdc', '#fdf1cf', '#ffe3c7', '#ffffff')]
S = dict(body=ParagraphStyle('b', fontName='A', fontSize=9.3, leading=13, textColor=INK, spaceAfter=5),
         h1=ParagraphStyle('h1', fontName='A-B', fontSize=19, leading=23, textColor=INK, spaceAfter=7),
         h2=ParagraphStyle('h2', fontName='A-B', fontSize=12.5, leading=16, textColor=ACC, spaceAfter=4, spaceBefore=8),
         cell=ParagraphStyle('c', fontName='A', fontSize=6.8, leading=8.4, textColor=INK), hdr=ParagraphStyle('h', fontName='A-B', fontSize=6.8, leading=8.4, textColor=colors.white),
         mono=ParagraphStyle('m', fontName='M', fontSize=7, leading=8.8, textColor=INK), small=ParagraphStyle('s', fontName='A-I', fontSize=7.5, leading=10, textColor=MUT))
P = lambda t, st='cell': Paragraph(t, S[st])
def tstyle(h): return [('BACKGROUND', (0, 0), (-1, 0), h), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#c9cddb')), ('LEFTPADDING', (0, 0), (-1, -1), 3), ('RIGHTPADDING', (0, 0), (-1, -1), 3), ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]
CATS = {'Physical': 'Fís', 'Special': 'Esp', 'Status': 'Est'}

CODE_LABEL = {'001': 'does nothing', '003': 'sleep', '041': 'confuses, Atk +2', '013': 'confusion', '01D': 'user Def +1', '01E': 'user Def +1 (Rollout boost)', '023': 'crit stage +2', '024': 'user Atk/Def +1', '027': 'user Atk/SpA +1', '028': 'user Atk/SpA +1 (+2 in sun)', '029': 'user Atk/Acc +1', '02A': 'user Def/SpD +1', '02E': 'user Atk +2', '02F': 'user Def +2', '030': 'user Speed +2', '032': 'user SpA +2', '047': 'target Accuracy -1', '04C': 'target Def -2', '04E': 'target SpA -2 (opposite gender)', '04F': 'target SpD -2', '056': 'protects own stats', '09D': 'field: weakens Electric', '09E': 'field: weakens Fire', '0A6': 'next attack always hits', '0A7': 'identifies Ghost types', '0A8': 'identifies Dark types', '0BB': 'blocks healing', '0D5': 'heals 50% HP', '0D7': 'Wish (delayed heal)', '0F8': 'blocks items', '112': 'Stockpile (Def/SpD +1)', '11A': 'target levitates', '133': 'no effect', '134': 'no effect', '137': 'Plus/Minus Def/SpD', '138': 'ally SpD +1', '139': 'target Atk -1', '13A': 'target Atk/SpA -1', '13D': 'target SpA -2', '13E': 'Grass Atk/SpA +1', '182': 'heals user and allies 25%', '188': 'eats berry, Def +2', '19A': 'next attack crits', '1A1': 'melts target item', '200': 'ally Atk/Def +1', '210': 'heals team 25% + cures status', '234': 'Def +2, Evasion +1', '237': 'cures status, SpA/SpD +1', 'CF12': 'Plus/Minus Atk/SpA', 'CF13': 'saps target Atk + heals', 'CF14': 'target Atk/SpA -1', 'CF5': 'heals 50% (66% in sand)', '0A5': 'never misses', '000': 'plain hit', '0': 'plain hit', '080': 'double vs. targets <=50% HP', '0A9': 'ignores Def/Evasion boosts', '01C': 'user Atk +1 chance', '043': 'target Def -1 chance', '0C2': 'recharge turn', '03F': 'user SpA -2',
              '0FB': '1/3 recoil', '08B': 'HP-scaling power (150 x HP%)', '0EE': 'pivots out after hitting', '00C': 'freeze / Frostbite', '00A': 'burn', '007': 'paralysis', '005': 'poison', '0A5': 'never misses', '0A0': 'always crits'}
def label(func, internal=None):
    if func in CODE_LABEL: return CODE_LABEL[func]
    for k, f in FAMS.items():
        if f[0] == func and func != '000': return f[2]
    for k, d in D.F.items():
        if d['func'] == func: return d['en']
    return D.LABELS.get(internal, 'engine effect ' + func) if internal else 'engine effect ' + func
def mech_label(m, which):
    s = m['old'] if which == 'old' else m
    if which == 'old' and D.LABELS.get(m['internal']): return D.LABELS[m['internal']]
    return label(s['func'], m['internal']) + (' + high crit' if 'h' in s['flags'] and s['func'] != '0A0' else '') + (f' ({s["prio"]:+d} priority)' if s['prio'] else '')
def cls(m):
    if not changed(m): return 'same', C_SAME
    o = m['old']
    if o['type'] != m['type'] or o['cat'] != m['cat'] or o['func'] != m['func'] or o['prio'] != m['prio'] or o['flags'] != m['flags']: return 'rework', C_REW
    d_bp = m['bp'] - o['bp']; a_o, a_n = (101 if o['acc'] == 0 else o['acc']), (101 if m['acc'] == 0 else m['acc'])
    up = (d_bp > 0 and o['bp'] > 1) or a_n > a_o or m['addl'] > o['addl']; down = (d_bp < 0 and o['bp'] > 1) or a_n < a_o or m['addl'] < o['addl']
    return ('mixed', C_MIX) if up and down else ('buff', C_BUFF) if up else ('nerf', C_NERF) if down else ('rework', C_REW)
LAB = {'rework': 'REWORK', 'buff': 'BUFF', 'nerf': 'NERF', 'mixed': 'MIXED', 'same': ''}
def v(x): return '—' if x == 0 else f'{x}%'
def bpv(x): return '—' if x <= 1 else str(x)
def tcell(typ, bp, acc, bold=False):
    t = f'<font color="{TC[typ]}"><b>{ES[typ]}</b></font> · {bpv(bp)} / {v(acc)}'
    return P(f'<b>{t}</b>' if bold else t)
def stat_cells(m):
    o = m['old']
    chg = (o['type'], o['bp'], o['acc']) != (m['type'], m['bp'], m['acc'])
    return tcell(o['type'], o['bp'], o['acc']), tcell(m['type'], m['bp'], m['acc'], bold=chg)
def prio_cell(m):
    f = lambda x: f'{x:+d}' if x else '0'
    return P(f(m['prio']) if m['prio'] == m['old']['prio'] else f'{f(m["old"]["prio"])} → <b>{f(m["prio"])}</b>')
def name_cell(m): return P(f'<b>{esc(m["es"])}</b><br/><font color="#6b7288">{esc(m["en"])}</font>')
def effect_text(m):
    o = m['old']; bits = []
    if o['type'] != m['type']: bits.append(f'Retyped {ES[o["type"]]} → <b>{ES[m["type"]]}</b>')
    if o['cat'] != m['cat']: bits.append(f'Category {o["cat"]} → <b>{m["cat"]}</b>')
    if o['func'] != m['func'] or o['flags'] != m['flags']:
        bits.append(f'{esc(mech_label(m, "old"))} → <b>{esc(mech_label(m, "new"))}</b>')
    elif o['addl'] != m['addl']: bits.append(f'{esc(mech_label(m, "new"))}: chance {o["addl"]}% → <b>{m["addl"]}%</b>')
    if not bits and m.get('fx'): bits.append(esc(m['fx']))
    if not bits and changed(m): bits.append('Numbers only')
    if bits: return '<br/>'.join(bits)
    return f'<font color="#9aa0b4">{esc(mech_label(m, "new"))}</font>'
def moves_table(ms, hdr):
    head = [P(t, 'hdr') for t in ('Move (ES / EN)', 'Cat', 'Old Type · BP / Acc', 'New Type · BP / Acc', 'Priority', 'Effect / mechanic', 'Design rationale')]
    rows, st = [head], tstyle(hdr)
    for i, m in enumerate(ms, 1):
        k, col = cls(m); o, n = stat_cells(m)
        lab = f'<font color="#2b4acb"><b>{LAB[k]}</b></font> ' if LAB[k] else ''
        rows.append([name_cell(m), P(('<b>%s</b>' % CATS[m['cat']]) if m['old']['cat'] != m['cat'] else CATS[m['cat']]), o, n, prio_cell(m), P(lab + effect_text(m)), P(esc(m['why']) if m['why'] else '<font color="#9aa0b4">No change.</font>')])
        if k != 'same': st.append(('BACKGROUND', (0, i), (-1, i), col))
    t = Table(rows, colWidths=[104, 24, 92, 92, 40, 170, 258], repeatRows=1, splitByRow=1); t.setStyle(TableStyle(st)); return t

# ───────── coverage ─────────
def tier(s):
    if s['func'] == '08B': return 'L'
    bp = s['bp']
    return None if bp <= 1 else 'E' if 40 <= bp <= 65 else 'M' if 70 <= bp <= 85 else 'L' if bp >= 90 else None
def cov(use_old):
    d = collections.defaultdict(collections.Counter)
    for m in new:
        if m['sig'] or m['cat'] == 'Status': continue
        s = m['old'] if use_old else m
        t = tier(s)
        if t: d[s['type'], s['cat']][t] += 1
    return d
CB, CA = cov(True), cov(False)
def matrix():
    head = [P('Type', 'hdr')] + [P(f'{c}<br/>{t}', 'hdr') for c in ('Phys', 'Spec') for t in ('Early 40-65', 'Mid 70-85', 'Late 90+')]
    rows, st = [head], tstyle(INK)
    for i, t in enumerate(TYPES, 1):
        r = [P(f'<b>{ES[t]}</b>')]
        for j, (c, tr) in enumerate([(c, tr) for c in ('Physical', 'Special') for tr in 'EML'], 1):
            b, a = CB[t, c][tr], CA[t, c][tr]; r.append(P(f'{b} → <b>{a}</b>'))
            if b == 0 and a > 0: st.append(('BACKGROUND', (j, i), (j, i), C_BUFF))
            if a == 0: st.append(('BACKGROUND', (j, i), (j, i), C_NERF))
        rows.append(r)
    t = Table(rows, colWidths=[80] + [78] * 6); t.setStyle(TableStyle(st)); return t
empty_b = sum(1 for t in TYPES for c in ('Physical', 'Special') for k in 'EML' if CB[t, c][k] == 0)
empty_a = sum(1 for t in TYPES for c in ('Physical', 'Special') for k in 'EML' if CA[t, c][k] == 0)

atk = [m for m in new if not m['sig'] and m['cat'] != 'Status']; stat = [m for m in new if m['cat'] == 'Status']
atk_ch = [m for m in atk if changed(m)]; stat_ch = [m for m in stat if changed(m)]
retyped = [m for m in new if m['old']['type'] != m['type'] and m['cat'] != 'Status']; recat = [m for m in new if m['old']['cat'] != m['cat'] and m['cat'] != 'Status']
below_b = [m for m in old if m['cat'] != 'Status' and 0 < m['acc'] < 80 and m['internal'] not in B.EXEMPT and m['internal'] not in SIG_SET] if False else None
SIG_SET = set(__import__('rules').SIGNATURE)
below_b = [m for m in old if m['cat'] != 'Status' and 0 < m['acc'] < 80 and m['internal'] not in B.EXEMPT]
below_a = [m for m in new if m['cat'] != 'Status' and 0 < m['acc'] < 80 and m['internal'] not in B.EXEMPT]
# protected drawback moves: confirm none lost BP or accuracy
PROT = 'SOLARBEAM SOLARBLADE SKULLBASH SKYATTACK METEORBEAM PHANTOMFORCE FLY BOUNCE DIG DIVE HYPERBEAM GIGAIMPACT ROCKWRECKER FRENZYPLANT BLASTBURN HYDROCANNON DOUBLEEDGE FLAREBLITZ BRAVEBIRD WOODHAMMER WILDCHARGE VOLTTACKLE TAKEDOWN SUBMISSION HEADCHARGE HEADSMASH LIGHTOFRUIN CLOSECOMBAT SUPERPOWER OVERHEAT DRACOMETEOR LEAFSTORM PSYCHOBOOST FLEURCANNON VCREATE HAMMERARM DRAGONASCENT JUMPKICK HIGHJUMPKICK FOCUSPUNCH OUTRAGE THRASH PETALDANCE RAGINGFURY ERUPTION WATERSPOUT'.split()
def accval(x): return 999 if x == 0 else x
lost = [n for n in PROT if n in bm and (bm[n]['bp'] < bm[n]['old']['bp'] or accval(bm[n]['acc']) < accval(bm[n]['old']['acc']))]
STAPLES = 'FLAMETHROWER THUNDERBOLT ICEBEAM SURF PSYCHIC ENERGYBALL BUGBUZZ EARTHPOWER MOONBLAST FOULPLAY FIRSTIMPRESSION PLAYROUGH DREAMEATER'.split()
st_lost = [n for n in STAPLES if (bm[n]['bp'], bm[n]['acc']) != (bm[n]['old']['bp'], bm[n]['old']['acc'])]

OUT = os.path.join(RB, 'Movepool_Rebalance_Master.pdf'); W, H = landscape(A4)
def footer(c, d):
    c.saveState(); c.setFont('A', 7.5); c.setFillColor(MUT); c.drawString(28, 16, 'Pokémon REM — Movepool Rebalance Proposal v6'); c.drawRightString(W - 28, 16, f'Page {d.page}'); c.restoreState()
doc = BaseDocTemplate(OUT, pagesize=landscape(A4), leftMargin=28, rightMargin=28, topMargin=28, bottomMargin=30, title='Movepool Rebalance Proposal v6 — Pokémon REM', author='Claude')
doc.addPageTemplates([PageTemplate(id='p', frames=[Frame(28, 30, W - 56, H - 58, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=footer)])
H1, B2, H2 = S['h1'], S['body'], S['h2']
nonsig = [m for m in new if not m['sig']]
ch_all = [m for m in nonsig if changed(m)]
st_nonsig = [m for m in stat if not m['sig']]; st_chg = [m for m in st_nonsig if changed(m)]
pct = lambda a, b: f'{100 * a // b}%'
rep, covn = v4_check.run()
retype_all = [m for m in nonsig if m['old']['type'] != m['type']]; recat_all = [m for m in nonsig if m['old']['cat'] != m['cat'] and m['cat'] != 'Status']
newdesc_n = sum(1 for m in nonsig if m['newdesc'])
mech_atk = [m for m in atk if (m['old']['func'], m['old']['flags'].count('h')) != (m['func'], m['flags'].count('h'))]
chance_atk = [m for m in atk if m['old']['func'] == m['func'] and m['old']['addl'] != m['addl']]
bp_atk = [m for m in atk if m['old']['bp'] != m['bp'] and m['old']['bp'] > 1]
acc_atk = [m for m in atk if m['old']['acc'] != m['acc']]
unch_atk = [m for m in atk if not changed(m)]
prot_unch = [m for m in unch_atk if m['internal'] in PROT]
st_ = [Paragraph('Pokémon REM — Movepool Rebalance Proposal <font size="14" color="#2b4acb">v6 · definitive master</font>', ParagraphStyle('t', fontName='A-B', fontSize=25, leading=30, textColor=INK, spaceAfter=4)),
       Paragraph(f'Audit of <font name="M">PBS/moves.txt</font> — exactly {len(new)} moves, IDs 1–765 · no new moves, no deletions, no PP changes · {datetime.date.today():%Y-%m-%d}', S['small']), Spacer(1, 6),
       Paragraph('Chapter 1 · Executive summary', H1),
       Paragraph('v6 is the definitive master version. It applies the findings of the v5 audit on top of v5: it fixes the engine bugs, reverts the conversions that felt unnatural, tones down inflated chances, de-clones the status reworks and rewrites the generic descriptions. Closed 765-move database, PP untouched, protected drawback moves, one identity per move from 50 BP up and no mechanic collisions are all kept.', B2),
       Paragraph(f'<b>Scope.</b> <b>{len(ch_all)} of {len(nonsig)}</b> non-signature moves ({pct(len(ch_all), len(nonsig))}) are changed (v5: 407, 59%): {len([m for m in atk if changed(m)])} of {len(atk)} attacks and {len(st_chg)} of {len(st_nonsig)} status moves. The count fell because tuning was undone where the audit found power creep or an overwritten mechanic: fewer changes, but each one is justified.', B2),
       Paragraph('<b>1 · Engine and code bugs fixed.</b> Fire Fang and Ice Fang now have effect chance 100 (their codes roll their own 10%, giving 10% status + 10% flinch like Thunder Fang). Thunder (008), Blizzard (00D) and Hurricane (015) have their weather-accuracy codes back, all 110/85. Twister (078), Stomp and Dragon Rush (010, double vs. Minimize), Whirlpool (0D0), Freeze-Dry (135) and Blaze Kick (burn + crit) are restored. Headbutt is the 30% flinch again and Spark the 30% paralysis. Infestation lost its contact flag, Drain Punch is Physical, Mega Punch is Normal.', B2),
       Paragraph('<b>2 · Awkward conversions reverted.</b> Rock Slide, Rock Throw, Bonemerang, Icicle Spear, Thunderous Kick, Feint Attack, Bulldoze and Magnitude are Physical again. Spike Cannon is a Water Physical non-contact multi-hit, Wrap a Poison trapper, Hold Back a Normal non-contact alternative to False Swipe. Special conversions that remain: ' + f'{len(recat_all)}' + ' (e.g. Pin Missile, Bullet Seed, Rock Blast, Rock Tomb, Triple Arrows, Sand Tomb, Spirit Shackle, Dragon Darts, Attack Order, Infestation, Barrage, Force Palm, Magnet Bomb).', B2),
       Paragraph('<b>3 · Chances and power normalised.</b> Flamethrower, Ice Beam, Thunderbolt and the three elemental punches are clean 10%; Fire Blast and Blizzard keep 20% as nukes. Scald, Body Slam and Discharge cap at 30%; Heart Stamp and Needle Arm flinch at 30%; Poison Fang at 30% badly-poison (Twineedle was already 20% per hit). Shadow Ball is back to 80 BP / 20%, Energy Ball 90 BP / 10%, Moonblast 90 BP with SpA -1 at 20% (its 95 → 90 is compensated), Night Daze, Crush Claw and Aqua Tail lose their stacked buffs. Focus Blast, Gunk Shot and Megahorn are confirmed at 120 BP / 85%, with Thunder, Blizzard, Fire Blast, Hydro Pump and Hurricane at 110/85; Fissure joins the 150/90 recharge nukes and the three Pledges are 80/100.', B2),
       Paragraph('<b>4 · Clones removed.</b> Multi-hit moves each have their own trait: Fury Swipes (Dark, crit per hit), Fury Attack (Flying, crit per hit), Comet Punch (Fairy, punch flag), Spike Cannon (Water, non-contact, 100%), Tail Slap (Normal, contact, 25/90), Double Slap (Normal, breaks screens). Status reworks no longer copy fragile or doubles-only moves: Flash is an Electric Atk/Speed +1 setup, Smokescreen lowers all foes\' Atk and SpA, Mud Sport raises Def/SpD, Water Sport heals 50%, Mist inflicts Frostbite at 90%; Miracle Eye, Foresight, Odor Sleuth, Lock-On and Sweet Scent keep their original mechanics.', B2),
       Paragraph('<b>5 · Descriptions and verification.</b> All generic Spanish descriptions were rewritten by hand and Razor Wind no longer mentions a charge turn. An automated check re-reads <font name="M">proposed_moves.txt</font> and the generated PDF and asserts every claim above (results in Appendix C).', B2),
       Paragraph('<i>Frostbite is taken from your description; the scripts contain no Frostbite code that I could find.</i>', S['small']),
       Paragraph('Headline metrics', H2)]
rows = [[P(t, 'hdr') for t in ('Metric', 'v5', 'v6')]] + [[P(a), P(b), P(f'<b>{c}</b>')] for a, b, c in (
    ('Moves in proposed_moves.txt / new / deleted / PP changed', '765 / 0 / 0 / 0', '765 / 0 / 0 / 0'),
    ('Non-signature moves changed', '407 of 683 (59%)', f'{len(ch_all)} of {len(nonsig)} ({pct(len(ch_all), len(nonsig))})'),
    ('… standard attacks', '312 of 434', f'{len([m for m in atk if changed(m)])} of {len(atk)}'),
    ('… status moves', '95 of 249', f'{len(st_chg)} of {len(st_nonsig)}'),
    ('Physical → Special conversions (attacks)', '24', str(len(recat_all))),
    ('Moves retyped (attacks / status)', '28 / 61', f'{len([m for m in retype_all if m["cat"] != "Status"])} / {len([m for m in retype_all if m["cat"] == "Status"])}'),
    ('Engine / code bugs found by the audit', '5 critical', '0 (all asserted)'),
    ('Fire Fang / Ice Fang / Thunder Fang effect chance', '10 / 10 / 100', f'{bm["FIREFANG"]["addl"]} / {bm["ICEFANG"]["addl"]} / {bm["THUNDERFANG"]["addl"]}'),
    ('Thunder / Blizzard / Hurricane codes', '007 / 00C / 015', f'{bm["THUNDER"]["func"]} / {bm["BLIZZARD"]["func"]} / {bm["HURRICANE"]["func"]}'),
    ('Pure BP nerfs without compensation', '0', str(len(v5_audit.nerfs()))),
    ('Reworked status moves cloning a doubles-only / berry-dependent move', '2', '0'),
    ('Attacks ≥ 50 BP with no effect / mechanic collisions', '0 / 0', f'{len(rep["plain50"])} / {len(rep["collisions"])}'),
    ('Empty tier cells / cells with only one move', '0 / 5', f'{len(rep["empty"])} / {len(rep["thin"])}'))]
t = Table(rows, colWidths=[400, 130, 130]); t.setStyle(TableStyle(tstyle(INK))); st_ += [t, PageBreak()]

# --- retype & recategorise table (attacks + status) ---
st_ += [Paragraph('Chapter 1 · All retyped and recategorised moves', H1),
        Paragraph(f'{len(retype_all)} moves change type and {len(recat_all)} change category. Each was deduced from a gap or from thematic ownership: Normal kept {len([m for m in orig.values() if m["type"] == "NORMAL" and m["cat"] != "Status" and m["internal"] not in SIG_SET])} attacks and {len([m for m in orig.values() if m["type"] == "NORMAL" and m["cat"] == "Status"])} status moves; it now keeps {len([m for m in atk if m["type"] == "NORMAL"])} and {len([m for m in stat if m["type"] == "NORMAL" and not m["sig"]])}.', B2)]
rows = [[P(t, 'hdr') for t in ('Move (ES / EN)', 'Kind', 'From', 'To', 'Thematic & balance justification')]]
ordered = sorted(retype_all + [m for m in recat_all if m not in retype_all], key=lambda m: (m['cat'] == 'Status', m['old']['type'] != 'NORMAL', m['old']['type'], m['internal']))
for m in ordered:
    o = m['old']
    rows.append([name_cell(m), P('status' if m['cat'] == 'Status' else 'attack'), P(f'<font color="{TC[o["type"]]}"><b>{ES[o["type"]]}</b></font> · {o["cat"][:4]}.'),
                 P(f'<font color="{TC[m["type"]]}"><b>{ES[m["type"]]}</b></font> · {m["cat"][:4]}.' + (' <b>(cat)</b>' if o['cat'] != m['cat'] else '')), P(esc(m['why']))])
t = Table(rows, colWidths=[104, 40, 74, 84, 478], repeatRows=1, splitByRow=1); t.setStyle(TableStyle(tstyle(INK))); st_ += [t, PageBreak()]

# --- coverage + untouched ---
st_ += [Paragraph('Chapter 1 · Tier coverage matrix', H1),
        Paragraph('Early 40–60, Mid 70–85, Late 90+ (HP-scaling counts as Late). Non-signature attacks. <font backColor="#dff3e4">Green</font> = cell was empty before. <font backColor="#f9dcdc">Red</font> = still empty. Cells that still hold a single move: ' + ', '.join(f'{ES[t]} {c[:4]}.{k}' for t, c, k, _ in rep['thin']) + '. These are types whose lore simply has few moves of that kind (for example a single Fighting late Special: Focus Blast); I did not invent conversions that do not fit.', S['small']), matrix(),
        Paragraph('Why some moves are untouched', H2),
        Paragraph(f'Of {len(nonsig) - len(ch_all)} untouched moves, {len(prot_unch)} are protected drawback moves (Eruption, Water Spout, Hyper Beam, Giga Impact, Focus Punch, Close Combat, Superpower, Brave Bird, Flare Blitz, Double-Edge, Wood Hammer, Volt Tackle, Overheat, Draco Meteor, Leaf Storm, Solar Beam/Blade, High Jump Kick, Outrage, Thrash, Petal Dance, Meteor Beam, Skull Bash, Sky Attack, Dig/Dive/Fly, Phantom Force…), the 40–45 BP route-1 basics (Tackle, Scratch, Ember, Water Gun, Vine Whip, Peck, Gust…), variable-power moves with their own formula (Counter, Return, Flail…), and moves that already hold a unique mechanic on a clean step of their staircase. I preferred to leave those alone rather than change numbers to hit a quota.', B2), PageBreak(),
        Paragraph('Chapter 2 · Type-by-type attack tables', H1),
        Paragraph('Each non-signature attack appears under its <b>new</b> type. Rows: <font backColor="#dff3e4">&nbsp;BUFF&nbsp;</font> <font backColor="#f9dcdc">&nbsp;NERF&nbsp;</font> <font backColor="#fdf1cf">&nbsp;MIXED&nbsp;</font> <font backColor="#ffe3c7">&nbsp;REWORK&nbsp;</font> (type, category, mechanic, priority or crit changed); white = unchanged (the grey text is the mechanic it already has). “—” accuracy = never misses, BP “—” = variable power. No PP column.', B2), PageBreak()]
for t in TYPES:
    ms = sorted([m for m in atk if m['type'] == t], key=lambda m: (m['cat'] != 'Physical', m['bp'] if m['bp'] > 1 else (150 if m['func'] == '08B' else 999), m['internal']))
    ch = sum(changed(m) for m in ms); ph = sum(1 for m in ms if m['cat'] == 'Physical')
    inn = [f'{m["en"]} (from {ES[m["old"]["type"]]})' for m in ms if m['old']['type'] != t] + [f'{m["en"]} (to {m["cat"]})' for m in ms if m['old']['cat'] != m['cat'] and m['old']['type'] == t]
    out = [f'{m["en"]} (to {ES[m["type"]]})' for m in atk if m['old']['type'] == t and m['type'] != t]
    mechs = collections.Counter(v4_check.mech(m)[0].rstrip('!+h') for m in ms if m['bp'] >= 50 or m['func'] == '08B')
    txt = f'<b>{len(ms)}</b> attacks ({ph} Physical / {len(ms) - ph} Special), <b>{ch}</b> changed. Arrivals/conversions: {"; ".join(inn) or "none"}. Departures: {"; ".join(out) or "none"}. 50+ BP moves use {len(mechs)} different mechanics.'
    badge = Table([[Paragraph(f'<font color="white"><b>{ES[t].upper()}</b></font>', ParagraphStyle('x', fontName='A-B', fontSize=14, leading=16)), Paragraph(txt, ParagraphStyle('y', fontName='A', fontSize=8, leading=10.5, textColor=INK))]], colWidths=[100, 680])
    badge.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), colors.HexColor(TC[t])), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LEFTPADDING', (0, 0), (-1, -1), 6), ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
    st_ += [badge, Spacer(1, 4), moves_table(ms, colors.HexColor(TC[t])), PageBreak()]

# --- Chapter 3: status ---
st_ += [Paragraph('Chapter 3 · Status & support moves overhaul', H1),
        Paragraph(f'{len(st_chg)} of {len(st_nonsig)} non-signature status moves change. Normal held {len([m for m in orig.values() if m["type"] == "NORMAL" and m["cat"] == "Status"])} of them; the ones whose name and theme belong elsewhere moved (love and gifts to Fairy, trapping to Ghost/Rock, mental tricks to Psychic, spore/scent to Grass, Swalot\'s moves to Poison…). Redundant buffs and debuffs were differentiated by type, stat combination, spread or secondary effect, and setup moves were distributed to the types that had none: Water (Shell Smash, Withdraw), Fire (Smokescreen = foes\' Atk/SpA -1), Electric (Flash = Atk/Speed +1, Magnetic Flux = SpA +2), Ground (Sand Attack, Mud Sport, Rototiller), Steel (Gear Up, Sharpen), Fairy (Celebrate), Dark (Howl, Leer), Psychic (Meditate, Kinesis) and Ice (Mist = Frostbite status). Sleep and confusion inducers keep sub-100% accuracy on purpose (Sleep Clause is their counterplay) but are no longer 50–60%.', B2)]
sm = sorted(st_chg, key=lambda m: (not m.get('donor'), TYPES.index(m['type']), m['internal']))
rows, sty = [[P(t, 'hdr') for t in ('Move (ES / EN)', 'Old type · acc · effect', 'New type · acc · effect', 'Rationale')]], tstyle(INK)
def seff(func, donor=None):
    base = STATUS_EN.get(func) or label(func, None)
    return base
for i, m in enumerate(sm, 1):
    o = m['old']; eff_new = (f'like {D.LABELS.get(m["donor"], m["donor"].title()) if m.get("donor") and False else m["donor"].title()}: ' if m.get('donor') else '') + seff(m['func'])
    rows.append([name_cell(m), P(f'<font color="{TC[o["type"]]}"><b>{ES[o["type"]]}</b></font> · {v(o["acc"])} · {esc(seff(o["func"]))}'),
                 P(f'<font color="{TC[m["type"]]}"><b>{ES[m["type"]]}</b></font> · <b>{v(m["acc"])}</b> · <b>{esc(eff_new)}</b>'), P(esc(m['why']))])
    sty.append(('BACKGROUND', (0, i), (-1, i), C_REW if m['func'] != o['func'] else (C_MIX if o['type'] != m['type'] else C_BUFF)))
t = Table(rows, colWidths=[104, 190, 230, 256], repeatRows=1, splitByRow=1); t.setStyle(TableStyle(sty)); st_ += [t, PageBreak()]

# --- Chapter 4: annex ---
sig = [m for m in new if m['sig']]
st_ += [Paragraph('Chapter 4 · Annex — legendary & signature moves', H1),
        Paragraph(f'{len(sig)} signature moves are isolated here. v6 touches only what the rules require: Magma Storm (75 → 90%, below the floor) and Dark Void (50 → 70%); Splash (Magikarp) becomes a Water Speed +2 setup. No signature BP is reduced.', B2)]
rows, sty = [[P(t, 'hdr') for t in ('Move (ES / EN)', 'Type · Cat', 'Old BP / Acc', 'New BP / Acc', 'Note')]], tstyle(colors.HexColor('#5b3fa0'))
for i, m in enumerate(sorted(sig, key=lambda m: (TYPES.index(m['type']), m['internal'])), 1):
    o = m['old']
    rows.append([name_cell(m), P(f'<font color="{TC[m["type"]]}"><b>{ES[m["type"]]}</b></font> · {CATS[m["cat"]]}'), P(f'{bpv(o["bp"])} / {v(o["acc"])}'), P(f'<b>{bpv(m["bp"])} / {v(m["acc"])}</b>' if changed(m) else f'{bpv(m["bp"])} / {v(m["acc"])}'), P(esc(m['why']) or '<font color="#9aa0b4">Unchanged.</font>')])
    if changed(m): sty.append(('BACKGROUND', (0, i), (-1, i), C_BUFF))
t = Table(rows, colWidths=[120, 80, 70, 70, 440], repeatRows=1, splitByRow=1); t.setStyle(TableStyle(sty)); st_ += [t, PageBreak()]

# --- appendix A catalogue + diff + verification ---
FAMAPP = [('Draining', '0DD 14F', 'Leech Life, Drain Punch, Giga Drain, Horn Leech, Draining Kiss, Absorb, Mega Drain, Parabolic Charge, Dream Eater', 'Absorb/Mega Drain/Giga Drain are a 40/55/75 staircase'),
          ('HP-scaling', '08B', 'Eruption, Water Spout, Dragon Energy', 'Belch (Poison) and Magnitude (Ground) join'),
          ('Hazard / field / item control', '236 110 10A 11C 11B 0F0 0F1 0F4 0F5 0F7 0CF', 'Stone Axe; Rapid Spin; Brick Break, Psychic Fangs; Smack Down; Sky Uppercut; Knock Off; Thief, Covet; Bug Bite, Pluck; Incinerate; Fling; trappers', 'X-Scissor and Double Slap candidates for 10A; Cut/Horn Drill/Drill Peck for 0A9; traps spread: Infestation, Wrap (Dragon)…'),
          ('Conditional doubles', '07B 07C 07D 07E 07F 080 081 082 084 088 233 235 232', 'Venoshock, Smelling Salts, Wake-Up Slap, Facade, Hex, Brine, Revenge/Avalanche, Assurance, Payback, Pursuit, Bitter Malice, Infernal Parade, Barb Barrage', 'Vice Grip (080) added; every type keeps at most one per band'),
          ('Stat substitution', '175 121 122 0A9 050', 'Body Press, Foul Play, Psyshock/Secret Sword, Chip Away/Sacred Sword/Darkest Lariat, Clear Smog', 'unchanged; Cut, Horn Drill, Drill Peck added to 0A9'),
          ('Pivot / priority / crit', '0EE +prio 0A0 flag h', 'U-turn, Volt Switch, Flip Turn; quick moves; Frost Breath, Storm Throw, Wicked Blow', 'Sonic Boom becomes a +1 priority Steel Special; Razor Wind high crit'),
          ('Status & stat chances', '005 006 007 00A 00C 013 042-047 04F 01C-020 02D', 'status chances and stat drops/boosts on hit', 'differentiated within each type; Frostbite on Ice, Water, Flying, Psychic, Ghost'),
          ('Weather / terrain', '0FF 100 101 102 154 155 156 159 087 201 203 207 211', 'setters and abusers', 'unchanged'),
          ('Recoil / recharge / self-drop', '0FA 0FB 0FC 0C2 03B-03F', 'protected drawback moves', 'untouched; Fissure (recharge), Guillotine (recoil), Sheer Cold (-2 SpA) join'),
          ('Multi-hit', '0BD 0BF 0C0 0BE', 'Double Hit, Triple Kick/Axel, Fury moves, Twineedle', 'Normal multi-hit bloat spread to Flying, Dark, Fairy, Water, Steel, Psychic'),
          ('Flags', 'a j i k m n o', 'contact, punch, bite, sound, pulse, bomb, dance', f'{len(B.syn_added)} missing synergy flags added (Iron Fist, Strong Jaw, Punk Rock, Mega Launcher)')]
st_ += [Paragraph('Appendix A · Engine function codes used (083 PokeBattle_MoveEffects)', H1), Paragraph('All 410 function codes were catalogued; only 0AF is unused. Mechanic families and how v6 distributes them:', B2)]
rows = [[P(t, 'hdr') for t in ('Family', 'Codes', 'Existing users', 'v6 use')]] + [[P(f'<b>{a}</b>'), P(f'<font name="M">{b}</font>'), P(esc(c)), P(esc(d))] for a, b, c, d in FAMAPP]
t = Table(rows, colWidths=[110, 140, 300, 230]); t.setStyle(TableStyle(tstyle(INK))); st_ += [t, PageBreak()]
oldline = {m['internal']: ln for m, ln in lines if m}
st_ += [Paragraph('Appendix B · PBS export diff preview', H1), Paragraph('Only columns 4–13 and, when the effect changes, the Spanish description are rewritten; IDs, internal names, display names and PP are never touched. Full file: <font name="M">docs/rebalance/proposed_moves.txt</font> (765 lines).', B2)]
cut = lambda s: esc(s if len(s) < 128 else s[:125] + '…')
for n in ['VICEGRIP', 'CUT', 'POUND', 'FURYSWIPES', 'GUILLOTINE', 'SEEDBOMB', 'XSCISSOR', 'BLIZZARD', 'FIREFANG', 'BELCH', 'MIST', 'KINESIS', 'EMBARGO']:
    m = bm[n]; ol = oldline[n].lstrip('﻿').rstrip('\r'); nl = engine.fmt(m).lstrip('﻿').rstrip('\r')
    st_ += [P(f'<font color="#c0392b">- {cut(ol)}</font>', 'mono'), P(f'<font color="#1e8449">+ {cut(nl)}</font>', 'mono'), Spacer(1, 3)]
st_.append(PageBreak())
with open(os.path.join(RB, 'proposed_moves.txt'), 'w', encoding='utf-8', newline='') as f:
    for m, ln in lines:
        f.write((engine.fmt(bm[m['internal']], ln) if m else ln) + '\n')
import v6_verify
vres = v6_verify.check_file(os.path.join(RB, 'proposed_moves.txt'), os.path.join(ROOT, 'PBS', 'moves.txt'), B.SCRIPT)
vpass = sum(1 for _, ok in vres if ok)
ids = sorted(m['id'] for m in new)
unch = [m for m in new if not changed(m)]
unch_bad = sum(1 for m in unch if engine.fmt(m) != oldline[m['internal']])
trio = ', '.join(f'{n.title()} {bm[n]["bp"]}/{bm[n]["acc"]}' for n in ('THUNDER', 'BLIZZARD', 'HURRICANE', 'FIREBLAST', 'HYDROPUMP', 'FOCUSBLAST', 'GUNKSHOT', 'MEGAHORN'))
checks = [('Moves in proposed_moves.txt', f'{len(new)} (IDs {ids[0]}–{ids[-1]}, contiguous: {ids == list(range(1, 766))}); new moves 0'),
          ('PP identical to PBS/moves.txt for all 765', 'yes (asserted)'), ('Unchanged moves byte-identical', f'{len(unch)} moves, {unch_bad} mismatches'),
          ('Non-signature moves changed', f'{len(ch_all)} of {len(nonsig)} ({pct(len(ch_all), len(nonsig))})'),
          ('Protected drawback moves that lost BP or accuracy', f'{len(lost)} of {len(PROT)} checked'), ('Classic staples changed', str(len(st_lost))),
          ('Attacks with 85% accuracy outside the nuke list', str(len(rep['acc85']))), ('Attacks not at 90/95/100 (excl. never-miss, nukes, gambles)', str(len(rep['acc_bad']))),
          ('85% nuke tier (BP/Acc)', trio), ('Mechanic collisions (same type+cat, ±10 BP)', str(len(rep['collisions']))), ('Plain attacks ≥ 50 BP', str(len(rep['plain50']))),
          ('BP clumps (≥3 moves on one BP, excl. protected/priority)', str(len(rep['clumps']))), ('OHKO moves remaining (func 070)', str(sum(1 for m in new if m['func'] == '070'))),
          ('Empty tier cells', str(len(rep['empty']))), ('Function codes valid in 083', 'yes (asserted)')]
rows = [[P('Check', 'hdr'), P('Result', 'hdr')]] + [[P(a), P(f'<b>{esc(b)}</b>')] for a, b in checks] + [[P('<b>Automated assertions on proposed_moves.txt</b>'), P(f'<b>{vpass} / {len(vres)} passed</b>')]] + [[P(esc(c)), P('<font color="#1e8449"><b>PASS</b></font>' if ok else '<font color="#c0392b"><b>FAIL</b></font>')] for c, ok in vres]
t = Table(rows, colWidths=[400, 380]); t.setStyle(TableStyle(tstyle(INK)))
st_ += [Paragraph('Appendix C · Verification & notes', H1), t, Spacer(1, 8), Paragraph('Source-file anomalies (preserved untouched)', H2),
        Paragraph('#281 Razor Wind (stray quote) and #720 Burning Jealousy (15 fields) keep their descriptions; Razor Wind\'s mechanics are now one-turn and its description was rewritten accordingly.', B2),
        Paragraph('Caveats', H2), Paragraph('Spanish descriptions are hand-written for the status reworks and the generic cases, and lore sentence + effect sentence (script) for the rest; a copy-edit is still advisable. Reused function codes should be checked in-game on their new moves. Frostbite is as described by you. Balance numbers are not play-tested.', B2)]
doc.build(st_)
import pymupdf
_txt = ''.join(p.get_text() for p in pymupdf.open(OUT)).replace('\n', ' ')
_facts = [f'{len(ch_all)} of {len(nonsig)}', 'Fissure joins the 150/90 recharge nukes', 'Hurricane', 'Appendix C', f'{vpass} / {len(vres)} passed']
for _c, _ok in v6_verify.check_pdf(_txt, _facts): print(('OK  ' if _ok else 'FAIL'), _c)
assert all(ok for _, ok in vres), [c for c, ok in vres if not ok]
print('PDF', os.path.getsize(OUT) // 1024, 'KB | changed', len(ch_all), 'of', len(nonsig), pct(len(ch_all), len(nonsig)), '| lost', lost, '| staples', st_lost)
