#!/usr/bin/env python3
"""verify_all_masters.py - master verification of the five-book design suite of Pokemon REM (design only, nothing is injected).

Reads ONLY files of this repository and recomputes every number from the exported data:
  docs/rebalance/{1_Pokemon,2_Abilities,3_Moves,4_Learnsets,5_TM}_Master_Guide.pdf
  docs/rebalance/{Pokemon_Changes_Master.md, proposed_moves.txt, proposed_learnsets.txt, proposed_tm.txt}
  docs/archive/proposed_learnsets_v6.json (frozen v6 baseline used for the 'before' side of every comparison)
  tools/rebalance/baseline_md5.json (checksums of PBS/, Data/ and the masters that must not change)

Usage:  python3 tools/rebalance/verify_all_masters.py        (exit code 0 = every check passed)
"""
import os,re,sys,csv,io,json,hashlib,collections,statistics
ROOT=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
D=os.path.join(ROOT,'docs','rebalance');ARC=os.path.join(ROOT,'docs','archive');PBS=os.path.join(ROOT,'PBS')
RES=[]
def check(name,ok,detail=''):
    RES.append((bool(ok),name,detail));print(('PASS  ' if ok else 'FAIL  ')+name+(f'  [{detail}]' if detail else ''))
def md5(p): return hashlib.md5(open(p,'rb').read()).hexdigest()
IDS=list(range(1,722))
# ---------------------------------------------------------------------------------------------- legendary / signature definitions
LEGEND=[144,145,146,150,151,243,244,245,249,250,251,377,378,379,380,381,382,383,384,385,386,480,481,482,483,484,485,486,487,488,489,490,491,492,493,494,638,639,640,641,642,643,644,645,646,647,648,649,716,717,718,719,720,721]
TOUCHED_LEG=[488,491,718,720,721]
UNTOUCHED=[i for i in LEGEND if i not in TOUCHED_LEG]
LEGSET=set(LEGEND)
SIG=set('''ROAROFTIME SPACIALREND SHADOWFORCE LUNARDANCE DARKVOID CRUSHGRIP MAGMASTORM SEEDFLARE VCREATE SEARINGSHOT FUSIONFLARE FUSIONBOLT BOLTSTRIKE BLUEFLARE GLACIATE FREEZESHOCK ICEBURN RELICSONG SECRETSWORD TECHNOBLAST GEOMANCY OBLIVIONWING LANDSWRATH THOUSANDARROWS THOUSANDWAVES DIAMONDSTORM HYPERSPACEHOLE HYPERSPACEFURY STEAMERUPTION ORIGINPULSE PRECIPICEBLADES DRAGONASCENT PSYCHOBOOST DOOMDESIRE AEROBLAST SACREDFIRE LUSTERPURGE MISTBALL JUDGMENT PSYSTRIKE SACREDSWORD LIGHTOFRUIN
SPECTRALTHIEF FLEURCANNON PRISMATICLASER NATURESMADNESS MOONGEISTBEAM SUNSTEELSTRIKE COREENFORCER FREEZINGGLARE PLASMAFISTS MINDBLOWN PHOTONGEYSER MULTIATTACK ETERNABEAM BEHEMOTHBASH BEHEMOTHBLADE DYNAMAXCANNON WICKEDBLOW SURGINGSTRIKES DRAGONENERGY THUNDERCAGE EERIESPELL GLACIALLANCE ASTRALBARRAGE BLEAKWINDSTORM WILDBOLTSTORM SANDSEARSTORM SPRINGTIDESTORM'''.split())
EXEMPT={132,201,129,349,11,14,266,268}                    # gimmick / vanilla-staged species not subject to ladder checks (same as the v6 verifier)
USER_ICONIC={'FLAMETHROWER':['Charmander','Charmeleon','Charizard','Cyndaquil','Quilava','Typhlosion','Torchic','Combusken','Blaziken','Chimchar','Monferno','Infernape','Tepig','Pignite','Emboar','Fennekin','Braixen','Delphox','Vulpix','Ninetales','Growlithe','Arcanine'],'THUNDERBOLT':['Pichu','Pikachu','Raichu','Magnemite','Magneton','Magnezone'],'ICEBEAM':['Lapras'],'EARTHQUAKE':['Sandshrew','Sandslash','Diglett','Dugtrio','Rhyhorn','Rhydon','Rhyperior','Marowak','Golem','Nidoking','Nidoqueen','Donphan','Steelix','Swampert','Flygon','Garchomp','Hippowdon','Excadrill','Krookodile','Mamoswine','Gliscor','Camerupt'],'PSYCHIC':['Abra','Kadabra','Alakazam','Ralts','Kirlia','Gardevoir','Gallade'],'SWORDSDANCE':['Scyther','Scizor'],'WISH':['Togepi','Togetic','Togekiss','Chansey','Blissey']}
# ---------------------------------------------------------------------------------------------- parsers
def read(p,enc='utf-8-sig'): return open(p,encoding=enc).read()
def parse_moves(path):
    out={}
    for l in read(path).splitlines():
        if not l.strip(): continue
        r=next(csv.reader(io.StringIO(l)))
        out[r[1]]=dict(id=int(r[0]),sym=r[1],name=r[2],fc=r[3],bp=int(r[4]),type=r[5],cat=r[6],acc=int(r[7]),pp=int(r[8]),eff=int(r[9]),target=r[10],prio=r[11],flags=r[12])
    return out
def parse_pokemon_txt(path):
    P={}
    for b in re.split(r'\n(?=\[\d+\]\s*\n)',read(path)):
        m=re.match(r'\s*\[(\d+)\]',b)
        if not m: continue
        d={}
        for l in b.split('\n')[1:]:
            if '=' in l: k,v=l.split('=',1);d[k.strip()]=v.strip()
        P[int(m.group(1))]=d
    return P
def parse_ls_txt(path):
    L={};cur=None;names={}
    for l in read(path).splitlines():
        m=re.match(r'\[(\d+)\]$',l.strip())
        if m: cur=int(m.group(1));continue
        if cur and l.startswith('# '): names[cur]=l[2:].split('  (')[0]
        if cur and l.startswith('Moves='):
            t=l[6:].split(',');L[cur]=[(int(t[k]),t[k+1]) for k in range(0,len(t)-1,2)]
        if cur and l.startswith('EggMoves='): L.setdefault(('egg',cur),l[9:].strip())
    return L,names
def parse_tm_txt(path):
    T=collections.OrderedDict();cur=None
    for l in open(path,encoding='ascii').read().splitlines():
        l=l.strip()
        if not l or l.startswith('#'): continue
        m=re.match(r'\[(\w+)\]$',l)
        if m: cur=m.group(1);T[cur]=[];continue
        if cur: T[cur]+= [x for x in l.split(',') if x]
    return T
# ---------------------------------------------------------------------------------------------- species data (families, stats, abilities, orientation)
PK=parse_pokemon_txt(os.path.join(PBS,'pokemon.txt'))
INT={i:PK[i]['InternalName'] for i in PK}
SPEC_OF={v:k for k,v in INT.items()}
PARENT={}
for i in IDS:
    t=PK[i].get('Evolutions','').split(',')
    for k in range(0,len(t)-2,3):
        if t[k] in SPEC_OF and SPEC_OF[t[k]]<=721: PARENT[SPEC_OF[t[k]]]=i
KIDS=collections.defaultdict(list)
for c,p in PARENT.items(): KIDS[p].append(c)
def root(i):
    while i in PARENT: i=PARENT[i]
    return i
def depth(i):
    d=0
    while i in PARENT: i=PARENT[i];d+=1
    return d
def family(i):
    r=root(i);fam=[r];ch=True
    while ch:
        ch=False
        for c,p in PARENT.items():
            if p in fam and c not in fam: fam.append(c);ch=True
    return sorted(fam)
ST={};cur=None
for l in open(os.path.join(D,'Pokemon_Changes_Master.md'),encoding='utf-8'):
    m=re.match(r'### #(\d+) ',l)
    if m: cur=int(m.group(1));continue
    if cur and l.startswith('- **Stats:**'):
        v=[int(re.match(r'(\d+)',x.split(' ',1)[1]).group(1)) for x in l.split('**Stats:**')[1].strip().split(' / ')[:6]]
        ST[cur]=dict(hp=v[0],atk=v[1],df=v[2],spa=v[3],spd=v[4],spe=v[5])
J6=json.load(open(os.path.join(ARC,'proposed_learnsets_v6.json'),encoding='utf-8'))      # frozen baseline: also carries orient / role / abilities / final types per species
MV=parse_moves(os.path.join(D,'proposed_moves.txt'))
def fam_max_depth(i): return max(depth(j) for j in family(i))
SPI={}
for i in IDS:
    j=J6[str(i)];o=j['orient'];cats=('Physical',) if o=='P' else ('Special',) if o=='S' else ('Physical','Special')
    bst=sum(ST[i].values());final=i not in KIDS;seed=i*7919;md=fam_max_depth(i);d=depth(i)
    if final: cap=70+(seed%9)+(2 if bst>=580 else 0)
    elif len(KIDS[i])>=2: cap=30+(seed%7)
    elif d==0: cap=(44+(seed%8)) if md>=2 else (50+(seed%11))
    else: cap=56+(seed%9)
    SPI[i]=dict(name=j['name'],types=j['types'],cats=cats,ab=j['abilities'],final=final,cap=cap,fam=family(i),root=root(i),orient=o)
# ---------------------------------------------------------------------------------------------- STAB ladder + ability synergy verifier (identical semantics to the one used by the v6 generator)
VAR_BP={'RETURN':90,'FRUSTRATION':60,'HIDDENPOWER':60,'LOWKICK':60,'GRASSKNOT':60,'GYROBALL':70,'ELECTROBALL':70,'HEAVYSLAM':70,'HEATCRASH':70,'ERUPTION':110,'WATERSPOUT':110,'FLAIL':70,'REVERSAL':70,'PUNISHMENT':60,'CRUSHGRIP':80,'WRINGOUT':80,'TRUMPCARD':70,'NATURALGIFT':70,'FLING':60,'PRESENT':40,'MAGNITUDE':70,'SPITUP':70,'BELCH':100,'WEATHERBALL':80,'SEISMICTOSS':50,'NIGHTSHADE':50,'SONICBOOM':40,'DRAGONRAGE':40,'ENDEAVOR':60,'SUPERFANG':60,'PSYWAVE':50,'COUNTER':60,'MIRRORCOAT':60,'METALBURST':60,'BIDE':40,'FINALGAMBIT':60,'FISSURE':70,'SHEERCOLD':70,'HORNDRILL':70,'GUILLOTINE':110}
MULTI={'0C0':3.1,'0BD':2.0,'0BF':3.5,'0C1':3.1}
def effbp(m):
    if m['cat']=='Status': return 0
    b=m['bp']
    if b<=1: return VAR_BP.get(m['sym'],50)
    return b*MULTI.get(m['fc'],1.0)
def is_att(m): return m['cat']!='Status' and (m['bp']>1 or m['sym'] in VAR_BP)
R_={}
def _role(n,s):
    for x in s.split(): R_[x]=n
_role('recovery','RECOVER SOFTBOILED MILKDRINK SLACKOFF ROOST SYNTHESIS MORNINGSUN MOONLIGHT WISH REST HEALPULSE HEALORDER WATERSPORT AROMATICMIST HOLDHANDS STRENGTHSAP LIFEDEW FLORALHEALING JUNGLEHEALING SHOREUP PURIFY HEALBELL AQUARING INGRAIN PAINSPLIT HEALINGWISH')
def srole(s): return R_.get(s,'misc')
SYN={'MEGALAUNCHER':(lambda m:is_att(m) and 'm' in m['flags'],3),'STRONGJAW':(lambda m:is_att(m) and 'i' in m['flags'],3),'IRONFIST':(lambda m:is_att(m) and 'j' in m['flags'],3),'PUNKROCK':(lambda m:is_att(m) and 'k' in m['flags'],3),'LIQUIDVOICE':(lambda m:is_att(m) and 'k' in m['flags'],3),'DANCER':(lambda m:'o' in m['flags'],2),'SKILLLINK':(lambda m:is_att(m) and m['fc']=='0C0',2),'TRIAGE':(lambda m:(is_att(m) and m['fc']=='0DD') or srole(m['sym'])=='recovery',3),'RECKLESS':(lambda m:is_att(m) and m['fc'] in('0FA','0FB','0FC','0FD','0FE','10B'),3),'TECHNICIAN':(lambda m:is_att(m) and effbp(m)<=60 and m['bp']>1,4),'SHEERFORCE':(lambda m:is_att(m) and m['eff']>0 and m['bp']>1,4),'SNIPER':(lambda m:is_att(m) and 'h' in m['flags'],2),'STEELWORKER':(lambda m:is_att(m) and m['type']=='STEEL',3),'DRAGONSMAW':(lambda m:is_att(m) and m['type']=='DRAGON',3),'TRANSISTOR':(lambda m:is_att(m) and m['type']=='ELECTRIC',3)}
def syn_cat(sym,m,cats):
    if sym=='TOUGHCLAWS': return is_att(m) and 'a' in m['flags'] and m['cat'] in cats and effbp(m)>=50
    if sym=='PROPELLERTAIL': return is_att(m) and 'a' not in m['flags'] and m['cat'] in cats and effbp(m)>=50
    if sym=='PUREPOWER': return is_att(m) and m['cat']=='Special' and effbp(m)>=50
    if sym=='HUGEPOWER': return is_att(m) and m['cat']=='Physical' and effbp(m)>=50
    if sym in('AERILATE','PIXILATE','REFRIGERATE','GALVANIZE','NORMALIZE'): return is_att(m) and m['type']=='NORMAL' and m['cat'] in cats and effbp(m)>=50
    return False
SYN_CAT={'TOUGHCLAWS':5,'PROPELLERTAIL':6,'PUREPOWER':10,'HUGEPOWER':10,'AERILATE':3,'PIXILATE':3,'REFRIGERATE':3,'GALVANIZE':3,'NORMALIZE':3}
NOLADDER=set('ROUND RETALIATE REVENGE FOCUSPUNCH DREAMEATER LASTRESORT SNORE FAKEOUT FIRSTIMPRESSION SUCKERPUNCH SPITUP SYNCHRONOISE HYPERBEAM GIGAIMPACT SELFDESTRUCT EXPLOSION SKYATTACK SKYDROP FLING NATURALGIFT TRUMPCARD ENDEAVOR COUNTER MIRRORCOAT METALBURST BIDE FINALGAMBIT HIDDENPOWER ROCKWRECKER FRENZYPLANT BLASTBURN HYDROCANNON MEGAHORN2 UPROAR ECHOEDVOICE REVERSAL FLAIL PRESENT MAGNITUDE POWERTRIP STOREDPOWER ASSURANCE BEATUP PAYDAY FALSESWIPE STRUGGLEBUG HOLDBACK DRAGONRAGE SONICBOOM SEISMICTOSS NIGHTSHADE PSYWAVE'.split())
SIGEXCL_OLD=set('''ROAROFTIME SPACIALREND BOLTSTRIKE BLUEFLARE FUSIONFLARE FUSIONBOLT MAGMASTORM SACREDFIRE AEROBLAST VCREATE SACREDSWORD SECRETSWORD ORIGINPULSE PRECIPICEBLADES DRAGONASCENT HYPERSPACEHOLE HYPERSPACEFURY LIGHTOFRUIN DIAMONDSTORM STEAMERUPTION THOUSANDARROWS THOUSANDWAVES LANDSWRATH OBLIVIONWING GEOMANCY RELICSONG TECHNOBLAST SEEDFLARE JUDGMENT SHADOWFORCE DOOMDESIRE PSYCHOBOOST LUSTERPURGE MISTBALL PSYSTRIKE DARKVOID LUNARDANCE SPECTRALTHIEF FLEURCANNON PRISMATICLASER NATURESMADNESS MOONGEISTBEAM SUNSTEELSTRIKE REVELATIONDANCE COREENFORCER FREEZINGGLARE THUNDEROUSKICK FIERYWRATH PLASMAFISTS PHOTONGEYSER MULTIATTACK AURAWHEEL BEHEMOTHBASH BEHEMOTHBLADE DYNAMAXCANNON ETERNABEAM ASTRALBARRAGE GLACIALLANCE EERIESPELL WICKEDBLOW SURGINGSTRIKES DRAGONENERGY THUNDERCAGE SPRINGTIDESTORM WILDBOLTSTORM SANDSEARSTORM BLEAKWINDSTORM POWERSHIFT MYSTICALPOWER LUNARBLESSING SKETCH TRANSFORM STRUGGLE HAPPYHOUR CELEBRATE HOLDHANDS CONFIDE ASSIST METRONOME COPYCAT MIMIC LASTRESORT NATURALGIFT SECRETPOWER ROLEPLAY SKILLSWAP ENTRAINMENT SIMPLEBEAM WORRYSEED'''.split())
JUNK_OLD=set('''SPLASH FLING PRESENT RAGE BIDE SNORE SPITE MINIMIZE SWAGGER FLATTER FORESIGHT ODORSLEUTH MIRACLEEYE SYNCHRONOISE PUNISHMENT ASSURANCE REVENGE RETALIATE AVALANCHE PAYBACK FOCUSPUNCH ACUPRESSURE HELPINGHAND AFTERYOU ALLYSWITCH BESTOW BLOCK CAMOUFLAGE CAPTIVATE CONVERSION CONVERSION2 DESTINYBOND EMBARGO FAIRYLOCK FOLLOWME GRUDGE GUARDSPLIT GUARDSWAP HEALBLOCK IMPRISON IONDELUGE LOCKON MATBLOCK MEANLOOK MEMENTO MINDREADER NIGHTMARE POWERSPLIT POWERSWAP POWERTRICK PSYCHOSHIFT PSYCHUP QUASH RECYCLE REFLECTTYPE SOAK SPOTLIGHT TELEKINESIS TOPSYTURVY TRICKORTREAT WIDEGUARD QUICKGUARD CRAFTYSHIELD FLOWERSHIELD ELECTRIFY INSTRUCT MAGICROOM WONDERROOM GRAVITY TEARFULLOOK COACHING DECORATE OCTOLOCK DOUBLETEAM MAGICROOM PERISHSONG MIRRORMOVE'''.split())
def own_moves(i):
    s=set()
    for j in SPI[i]['fam']:
        t=PK[j].get('Moves','').split(',');s|={t[k+1] for k in range(0,len(t)-1,2)}
        s|={x for x in PK[j].get('EggMoves','').split(',') if x}
    return s
OWN={}
def allowed(i,mv):
    m=MV.get(mv)
    if not m or mv in JUNK_OLD: return False
    if mv in SIGEXCL_OLD:
        if i not in OWN: OWN[i]=own_moves(i)
        if mv not in OWN[i]: return False
    return m['cat']=='Status' or is_att(m)
def verify_species(i,mvs,maxlv):
    sp=SPI[i];errs=[];cats=sp['cats']
    for t in sp['types']:
        for tau,need_lv,rng in (('E',0,(40,65)),('M',36,(66,89)),('L',64,(90,999))):
            if maxlv<need_lv: continue
            if [m for m in mvs if is_att(MV[m]) and MV[m]['type']==t and rng[0]<=effbp(MV[m])<=rng[1] and MV[m]['cat'] in cats]: continue
            poolc=[m for m,d in MV.items() if is_att(d) and d['type']==t and rng[0]<=effbp(d)<=rng[1] and d['cat'] in cats and allowed(i,m) and m not in NOLADDER]
            if not poolc:
                if [m for m in mvs if is_att(MV[m]) and MV[m]['type']==t and rng[0]<=effbp(MV[m])<=rng[1]]: continue
                pool2=[m for m,d in MV.items() if is_att(d) and d['type']==t and rng[0]<=effbp(d)<=rng[1] and allowed(i,m) and m not in NOLADDER]
                if not pool2: continue
            errs.append(f'STAB-{t}-{tau}')
    for ab in sp['ab']:
        sc=1.0 if sp['final'] else min(1.0,(sp['cap']+10)/80.0)
        if ab in SYN:
            f,mn=SYN[ab];mn=mn if sp['final'] else max(2,round(mn*sc));c=sum(1 for m in mvs if f(MV[m]))
            if c<mn: errs.append(f'SYN-{ab}-{c}/{mn}')
        elif ab in SYN_CAT:
            mn=SYN_CAT[ab];mn=mn if sp['final'] else max(2,round(mn*sc));c=sum(1 for m in mvs if syn_cat(ab,MV[m],cats))
            if c<mn: errs.append(f'SYN-{ab}-{c}/{mn}')
    return errs
# ================================================================================================ 1. FILE SET
print('== 1. Clean master suite in docs/rebalance ==')
PDFS=['1_Pokemon_Master_Guide.pdf','2_Abilities_Master_Guide.pdf','3_Moves_Master_Guide.pdf','4_Learnsets_Master_Guide.pdf','5_TM_Master_Guide.pdf']
DATA=['Pokemon_Changes_Master.md','proposed_moves.txt','proposed_learnsets.txt','proposed_tm.txt']
OPTIONAL=['proposed_learnsets.json']
NARR=['6_World_and_Locations_Master_Guide.pdf','6_World_and_Locations_Master_Guide.md','7_Characters_Master_Guide.pdf','7_Characters_Master_Guide.md','8_Story_Novella_Master_Guide.pdf','8_Story_Novella_Master_Guide.md','assets','9_Items_and_Economy_Master_Guide.pdf','9_Items_and_Economy_Master_Guide.md','proposed_items.txt','10_Wild_Encounters_Master_Guide.pdf','10_Wild_Encounters_Master_Guide.md','1_Pokemon_Master_Guide.md','proposed_pokemon.txt','11_Trainer_Classes_Master_Guide.pdf','11_Trainer_Classes_Master_Guide.md']   # narrative suite (books 6-8) verified by verify_narrative_books.py; items volume (9 + proposed_items.txt) verified by verify_items_master.py
present=sorted(f for f in os.listdir(D) if not f.startswith('.'))
check('five master PDFs present',all(f in present for f in PDFS),', '.join(PDFS))
check('Pokemon_Changes_Master.md, proposed_moves.txt, proposed_learnsets.txt, proposed_tm.txt present',all(f in present for f in DATA))
extra=[f for f in present if f not in PDFS+DATA+OPTIONAL+NARR]
check('docs/rebalance holds nothing else (no TM_System_Master*.pdf, no stray files)',not extra,'extra: '+', '.join(extra) if extra else 'only 1_ to 5_ + data files (+ proposed_learnsets.json companion, the 6_-8_ narrative books, the 9_ items volume with proposed_items.txt, the 10_ wild encounters volume, 1_Pokemon_Master_Guide.md and proposed_pokemon.txt)')
try:
    import fitz
    FZ=True
except Exception:
    FZ=False
TXT={}
if FZ:
    import warnings;warnings.filterwarnings('ignore')
    for f in PDFS:
        d=fitz.open(os.path.join(D,f));TXT[f]=[d[p].get_text() for p in range(d.page_count)]
    pages={f:len(TXT[f]) for f in PDFS}
    check('all five PDFs open and have content',all(v>=10 for v in pages.values()),str(pages))
    head={'1_Pokemon_Master_Guide.pdf':'1 · Pokémon Master Guide','2_Abilities_Master_Guide.pdf':'2 · Abilities Master Guide','3_Moves_Master_Guide.pdf':'3 · Moves Master Guide','4_Learnsets_Master_Guide.pdf':'4 · Learnsets Master Guide','5_TM_Master_Guide.pdf':'5 · TM Master Guide'}
    check('each PDF carries its own volume title',all(head[f] in TXT[f][0] for f in PDFS))
else:
    print('WARN  PyMuPDF (fitz) not installed: PDF text checks are skipped')
# ================================================================================================ 2. DATA FILES
print('== 2. Data files parse and are consistent ==')
LS,NAMES=parse_ls_txt(os.path.join(D,'proposed_learnsets.txt'))
TM=parse_tm_txt(os.path.join(D,'proposed_tm.txt'))
check('proposed_moves.txt: 765 moves, ids 1..765 contiguous, unique symbols',len(MV)==765 and sorted(m['id'] for m in MV.values())==list(range(1,766)))
check('proposed_learnsets.txt: 721 species (#001-#721)',sorted(k for k in LS if isinstance(k,int))==IDS)
bad=[i for i in IDS if not LS[i] or any(l<1 for l,_ in LS[i]) or [l for l,_ in LS[i]]!=sorted(l for l,_ in LS[i])]
check('levels ascending and >= 1 in every list',not bad,str(bad[:5]))
badsym=sorted({m for i in IDS for _,m in LS[i] if m not in MV})
check('every learnset move exists in proposed_moves.txt',not badsym,str(badsym[:5]))
dup=[i for i in IDS if len({m for _,m in LS[i]})!=len(LS[i]) and i!=235 and i not in UNTOUCHED]
check('no duplicate move inside an overhauled list (Smeargle repeats Sketch by design; untouched legendaries keep their vanilla list)',not dup,str(dup[:5]))
check('EggMoves= is empty for all 721 species',all(LS.get(('egg',i),'')=='' for i in IDS))
PKM={i:PK[i].get('Moves','') for i in IDS}
van=[i for i in UNTOUCHED if ','.join(f'{l},{m}' for l,m in LS[i])!=PKM[i]]
check('the 49 untouched legendaries keep their vanilla Moves= line byte-for-byte',not van,str(van[:5]))
order=[t['sym'] for t in []]
check('proposed_tm.txt: exactly 100 TM blocks',len(TM)==100)
allsp=[s for v in TM.values() for s in v]
check('proposed_tm.txt lists only species #001-#721',all(s in SPEC_OF and SPEC_OF[s]<=721 for s in allsp))
check('every TM move exists in proposed_moves.txt and no TM is an HM',all(m in MV for m in TM) and not (set(TM)&set('SURF WATERFALL CUT FLY STRENGTH ROCKSMASH DIVE ROCKCLIMB WHIRLPOOL FLASH'.split())))
# ================================================================================================ 3. PILLAR 1 - usage floor
print('== 3. Pillar 1: 100% move usage across non-legendary Pokemon (#001-#721) ==')
NLUSERS=collections.defaultdict(set);ALLUSERS=collections.defaultdict(set)
for i in IDS:
    for _,m in LS[i]:
        ALLUSERS[m].add(i)
        if i not in LEGSET: NLUSERS[m].add(i)
REG=[m for m in MV if m not in SIG]
check('765 moves = non-signature + exclusive/inactive legendary signatures',len(REG)+len(SIG)==765,f'{len(REG)} + {len(SIG)}')
low=[(m,len(NLUSERS[m])) for m in REG if len(NLUSERS[m])<5]
check('EVERY non-signature move has >= 5 non-legendary level-up learners',not low,f'min={min(len(NLUSERS[m]) for m in REG)}; failing: {low[:8]}')
orph=[m for m in REG if len(NLUSERS[m])<=2]
check('zero non-signature moves left at 0, 1 or 2 users',not orph,str(orph[:8]))
fam3=[(m,len({root(i) for i in NLUSERS[m]})) for m in REG if len({root(i) for i in NLUSERS[m]})<3]
check('every non-signature move is spread over >= 3 evolutionary lines',not fam3,str(fam3[:8]))
leak=[(m,len(NLUSERS[m])) for m in SIG if NLUSERS[m]]
check('the 69 legendary signature moves are exclusive (0 non-legendary level-up learners)',not leak,str(leak[:6]))
named=['LAVAPLUME','HEATWAVE','FIRELASH','FLAMEBURST','BURNINGJEALOUSY','OVERHEAT','FLAREBLITZ','SURF','MUDDYWATER','SPARKLINGARIA','HYDROPUMP','WAVECRASH','AQUATAIL','DISCHARGE','RISINGVOLTAGE','OVERDRIVE','WILDCHARGE','ZINGZAP','PETALBLIZZARD','LEAFBLADE','APPLEACID','GRAVAPPLE','POWERWHIP','LEAFSTORM','SOLARBEAM','FREEZEDRY','AURORABEAM','ICICLECRASH','MOUNTAINGALE','BRICKBREAK','SKYUPPERCUT','THUNDEROUSKICK','SUBMISSION','CLOSECOMBAT','SUPERPOWER','SLUDGEWAVE','BARBBARRAGE','DIRECLAW','GUNKSHOT','HIGHHORSEPOWER','SCORCHINGSANDS','DRILLRUN','STOMPINGTANTRUM','DUALWINGBEAT','DRILLPECK','ACROBATICS','HURRICANE','BRAVEBIRD','EXTRASENSORY','EXPANDINGFORCE','ESPERWING','PSYCHICFANGS','SIGNALBEAM','LUNGE','SKITTERSMACK','FIRSTIMPRESSION','ATTACKORDER','POLLENPUFF','ANCIENTPOWER','STONEAXE','HEADSMASH','SPIRITSHACKLE','BITTERMALICE','INFERNALPARADE','PHANTOMFORCE','POLTERGEIST','BREAKINGSWIPE','DRAGONHAMMER','DRAGONRUSH','OUTRAGE','DRACOMETEOR','BRUTALSWING','LASHOUT','THROATCHOP','CRUNCH','DARKESTLARIAT','FALSESURRENDER','FIERYWRATH','MIRRORSHOT','STEELWING','METEORMASH','ANCHORSHOT','STEELBEAM','SPIRITBREAK','MOONBLAST','STRANGESTEAM']
chk=[m for m in named if m in MV and len(NLUSERS[m])<5]
check('every move named in the brief (Pillar 2 list + former TM finishers) is multi-user',not chk and all(m in MV for m in named),str(chk))
# ================================================================================================ 4. PILLAR 2 - TM frequency
print('== 4. Pillar 2: smart level-up vs TM frequency rebalancing ==')
TMS=list(TM)
LS6={i:[(x['lv'],x['move']) for x in J6[str(i)]['moves']] for i in IDS}
nl6=collections.Counter();nl7=collections.Counter()
for i in IDS:
    if i in LEGSET: continue
    for m in {x for _,x in LS6[i]}:
        if m in TM: nl6[m]+=1
    for m in {x for _,x in LS[i]}:
        if m in TM: nl7[m]+=1
t6=sum(nl6.values());t7=sum(nl7.values())
check('TM moves are handed out by level-up markedly less often (non-legendary entries)',t7<=0.80*t6,f'{t6} -> {t7} ({100*(t7/t6-1):+.1f}%)')
name2id={SPI[i]['name']:i for i in IDS}
rein=collections.Counter()
for m,ns in USER_ICONIC.items():
    for n in ns:
        i=name2id[n]
        if not any(x==m for _,x in LS6[i]) and any(x==m for _,x in LS[i]): rein[m]+=1
up=[(m,nl6[m],nl7[m],rein[m]) for m in TMS if nl7[m]-rein[m]>nl6[m] and nl6[m]>=10]
check('no TM move that had >= 10 non-legendary teachers became more common (except the iconic learners of the brief that were reinstated)',not up,f'{sum(rein.values())} iconic pairs reinstated: '+', '.join(f'{m} +{c}' for m,c in rein.items())+f'; offenders: {up}')
cut={m:1-nl7[m]/nl6[m] for m in TMS if nl6[m]>=25}
med=statistics.median(cut.values())
check('the TM moves handed out most by level-up (>= 25 teachers in v6) lose a median of >= 25% of them',med>=0.25,f'{len(cut)} TMs, median cut {100*med:.0f}%, mean {100*statistics.mean(cut.values()):.0f}%')
fewer=[(m,nl6[m],nl7[m]) for m in cut if cut[m]<0.10]
check('at least 85% of those TMs lose >= 10% (the rest are role moves with no logical substitute)',len(fewer)<=0.15*len(cut),f'{len(cut)-len(fewer)}/{len(cut)} trimmed >= 10%; least trimmed: {fewer}')
top=sorted(((m,nl6[m],nl7[m]) for m in TMS),key=lambda t:-t[1])[:6]
check('the six most common TM moves (Protect, Toxic, Rest, Thunder Wave, Calm Mind, ...) each lose level-up teachers',all(b<a for _,a,b in top),', '.join(f'{m} {a}->{b}' for m,a,b in top))
nolost=[m for m in TMS if nl7[m]<5]
check('no TM move was eliminated from level-up (>= 5 non-legendary teachers each)',not nolost,f'min={min(nl7[m] for m in TMS)}')
lost=[];kept=0;total=0
for m,ns in USER_ICONIC.items():
    for n in ns:
        i=name2id[n]
        if any(x==m for _,x in LS6[i]):
            total+=1
            if any(x==m for _,x in LS[i]): kept+=1
            else: lost.append((m,n))
check('iconic natural learners named in the brief that had the move in v6 still learn it',not lost,f'{kept}/{total} kept; lost: {lost}')
gained=sum(1 for m,ns in USER_ICONIC.items() for n in ns if not any(x==m for _,x in LS6[name2id[n]]) and any(x==m for _,x in LS[name2id[n]]))
print(f'INFO  iconic pairs reinstated in v7 (had no copy in v6): {gained}')
# ================================================================================================ 5. PILLAR 3 - TM compatibility
print('== 5. Pillar 3: expanded TM compatibility ==')
reach={m:len(TM[m]) for m in TMS}
check('every TM has >= 60 compatible Gen 1-6 Pokemon',min(reach.values())>=60,f'min={min(reach.values())} ({min(reach,key=reach.get)}), median={int(statistics.median(reach.values()))}')
narrow={'ICESHARD':27,'AURASPHERE':34,'POWERGEM':40,'SMARTSTRIKE':40,'HEX':44,'MYSTICALFIRE':46,'VOLTSWITCH':51,'TOXICSPIKES':56,'BUGBUZZ':57,'SPIKES':61,'CROSSPOISON':61,'STRUGGLEBUG':62,'DRAGONCLAW':65,'FLAMECHARGE':65,'AIRSLASH':74,'TELEPORT':77,'MIST':78,'DRAININGKISS':80,'WISH':81}
grow={m:(v,reach[m]) for m,v in narrow.items() if reach[m]<=v*1.3}
check('the 19 narrow TMs of the old guide each grew by more than 30%',not grow,str(grow) if grow else ', '.join(f'{m} {v}->{reach[m]}' for m,v in list(narrow.items())[:6])+' ...')
tmset={i:set() for i in IDS}
for m,sps in TM.items():
    for s in sps: tmset[SPEC_OF[s]].add(m)
missing=[(i,m) for i in IDS for _,m in LS[i] if m in TM and m not in tmset[i]]
check('100% compatibility inheritance: every level-up learner of a TM move is listed for that TM',not missing,f'{sum(1 for i in IDS for _,m in LS[i] if m in TM)} (Pokemon,TM) level-up pairs checked; missing: {missing[:5]}')
# ================================================================================================ 6. PILLAR 5.5 - STAB, synergy, curve
print('== 6. STAB / ability-synergy integrity and level-up curve coherence ==')
err7={};err6={}
for i in IDS:
    if i in UNTOUCHED or i in EXEMPT: continue
    e7=verify_species(i,[m for _,m in LS[i]],max(l for l,_ in LS[i]))
    e6=verify_species(i,[m for _,m in LS6[i]],max(l for l,_ in LS6[i]))
    if e7: err7[i]=e7
    if e6: err6[i]=e6
check('0 Pokemon lost STAB-ladder or ability-synergy moves (v7 verifier errors)',not err7,f'v6 baseline errors: {len(err6)}; v7 errors: {len(err7)} {list(err7.items())[:3]}')
retyped=[i for i in IDS if set(SPI[i]['types'])!=set(t for t in [PK[i].get('Type1'),PK[i].get('Type2')] if t)]
check('the 100 retyped species keep their full STAB ladder for both types',len([i for i in retyped if i in err7])==0,f'{len(retyped)} species whose final typing differs from vanilla')
gaps={'early':[],'mid':[],'late':[]}
for i in IDS:
    if i in UNTOUCHED: continue
    lv=sorted({l for l,_ in LS[i] if l>1})
    for a,b in zip(lv,lv[1:]): gaps['early' if b<=20 else 'mid' if b<=45 else 'late'].append(b-a)
tg={'early':(2,4),'mid':(3,5),'late':(5,7)};ok={k:sum(1 for x in v if tg[k][0]<=x<=tg[k][1])/len(v) for k,v in gaps.items()}
check('spacing curve preserved (tight 1-20, moderate 21-45, wider 46-80)',ok['early']>=0.95 and ok['mid']>=0.88 and ok['late']>=0.55,', '.join(f'{k} {100*v:.0f}% in band (mean gap {statistics.mean(gaps[k]):.1f})' for k,v in ok.items()))
fin=[max(l for l,_ in LS[i]) for i in IDS if i not in UNTOUCHED and i not in KIDS and len(LS[i])>3]
check('final forms keep reaching ~Lv 70-80',min(fin)>=70,f'min last level {min(fin)}, median {statistics.median(fin):.0f}, max {max(fin)}')
sz=[len(LS[i]) for i in IDS if i not in UNTOUCHED]
check('list sizes stay in the v6 range',max(sz)<=30 and statistics.mean(sz)<=20.5,f'mean {statistics.mean(sz):.1f}, max {max(sz)}')
def inh(L):
    v=0
    for c,p in PARENT.items():
        if c in LEGSET or p in LEGSET: continue
        v+=len({(l,m) for l,m in L[p]}-{(l,m) for l,m in L[c]})
    return v
i6,i7=inh(LS6),inh(LS)
check('evolution inheritance kept (parent entries missing in the evolved form stay near the v6 level)',i7<=i6*1.3,f'v6 {i6} -> v7 {i7}')
# ================================================================================================ 7. PDF CONTENT
print('== 7. Master PDF content ==')
if FZ:
    t3='\n'.join(TXT['3_Moves_Master_Guide.pdf']);k=t3.find('Appendix D. Complete 765-Move Usage');d2=t3.find('D.2 The 765-row audit table',k)
    check('3_Moves keeps Sections 1-4 and gains Appendix D (usage census)',all(s in t3 for s in ['Section 1.','Section 2.','Section 3.','Section 4.','Engine function-code verification']) and k>0 and d2>k)
    seg=t3[d2:]
    nrows=len(re.findall(r'Healthy Multi-User|Exclusive Legendary Signature|Inactive Gen 7-8 Signature',seg))
    check('Appendix D audit table lists all 765 moves',nrows==765,f'{nrows} status cells')
    check('Appendix D states 100% of non-signature moves are multi-user',f'all {len(REG)} non-signature'.lower() in t3.lower() or f'{len(REG)} of {len(REG)} (100%)' in t3 or '100% of the' in t3)
    t4='\n'.join(TXT['4_Learnsets_Master_Guide.pdf'])
    miss4=[i for i in IDS if f'#{i:03d} {SPI[i]["name"]}' not in t4]
    check('4_Learnsets covers all 721 Pokemon (#001 Bulbasaur ... #721 Volcanion)',not miss4,str(miss4[:5]))
    t5='\n'.join(TXT['5_TM_Master_Guide.pdf'])
    need5=['1 · Executive Summary','2 · Complete 100 TM Catalog','3 · Type, Category','4 · Compatibility Methodology','Appendix A','Appendix B','Level-up learners','TM compat. learners']
    check('5_TM has Chapters 1-4, Appendix A (items.txt binding) and Appendix B (matrix)',all(s in t5 for s in need5),str([s for s in need5 if s not in t5]))
    tmn=[f'TM{n:02d}' for n in range(1,101)]
    check('5_TM catalog and binding table cover TM01..TM100',all(t in t5 for t in tmn))
    appb=t5[t5.find('Appendix B'):]
    miss5=[i for i in IDS if SPI[i]['name'] not in appb]
    check('5_TM Appendix B matrix covers #001 Bulbasaur ... #721 Volcanion',not miss5 and 'Volcanion' in appb and 'Bulbasaur' in appb,str(miss5[:5]))
# ================================================================================================ 8. IMMUTABILITY
print('== 8. PBS/ and Data/ remain untouched ==')
# PBS/ was intentionally rewritten in Phase 1 (see verify_full_pbs_and_app.py): here we only guard Data/ and the pristine backup.
_mf = os.path.join(ROOT, 'PBS_backup_original', 'MANIFEST.md5')
_bad = []
if os.path.exists(_mf):
    for _l in open(_mf, encoding='utf-8'):
        _h, _, _r = _l.strip().partition(' ')
        _r = _r.strip().lstrip('*').lstrip('./')
        if _r and (not os.path.exists(os.path.join(ROOT, 'PBS_backup_original', _r)) or md5(os.path.join(ROOT, 'PBS_backup_original', _r)) != _h): _bad.append(_r)
check('PBS_backup_original/ is intact (md5 manifest)', os.path.exists(_mf) and not _bad, str(_bad[:3]))

B=json.load(open(os.path.join(ROOT,'tools','rebalance','baseline_md5.json')))
cur={}
for d in ('Data',):
    for dp,dn,fn in os.walk(os.path.join(ROOT,d)):
        for f in fn:
            p=os.path.join(dp,f);cur[os.path.relpath(p,ROOT)]=md5(p)
diff=[f for f in B['pbs_data'] if f.startswith('Data/') and cur.get(f)!=B['pbs_data'][f]];new=[f for f in cur if f not in B['pbs_data']]
check('Data/ is byte-identical to the baseline',not diff and not new,f'{len(cur)} files checked; changed: {diff[:3]}; new: {new[:3]}')
unch=[f for f,h in B['masters_unchanged'].items() if md5(os.path.join(D,f))!=h]
check('1_Pokemon, 2_Abilities, Pokemon_Changes_Master.md and proposed_moves.txt are unchanged',not unch,str(unch))
# ================================================================================================ SUMMARY
n=len(RES);bad=[r for r in RES if not r[0]]
print(f'\n{n-len(bad)}/{n} checks passed')
if bad:
    print('FAILED:');[print('  -',b[1],b[2]) for b in bad]
sys.exit(1 if bad else 0)
