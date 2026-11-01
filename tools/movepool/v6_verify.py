import csv, re, os
def load(p):
    return [next(csv.reader([l.rstrip('\r')])) for l in open(p, encoding='utf-8-sig', newline='').read().split('\n') if l.strip() and l[0] != '#']
def check_file(prop, pbs, scripts):
    codes = set(re.findall(r'class PokeBattle_Move_(\w+)', open(scripts, encoding='utf-8', errors='replace').read()))
    P = load(prop); O = load(pbs); by = {r[1]: r for r in P}; ob = {r[1]: r for r in O}
    R = []
    def ok(claim, cond): R.append((claim, bool(cond)))
    f = lambda n: by[n]
    def st(n): r = by[n]; return (r[3], int(r[4]), r[5], r[6], int(r[7]), int(r[9]), r[12], r[10])
    ok('765 lines, IDs 1-765 in order', len(P) == 765 and [int(r[0]) for r in P] == list(range(1, 766)))
    ok('names and PP identical to PBS/moves.txt (zero PP changes)', all(a[1] == b[1] and a[2] == b[2] and a[8] == b[8] for a, b in zip(O, P)))
    ok('every function code exists in 083', all(r[3] in codes or r[3] in ('0', '000') for r in P))
    ok('Fire Fang and Ice Fang chance = 100 (like Thunder Fang)', all(int(f(n)[9]) == 100 for n in ('FIREFANG', 'ICEFANG', 'THUNDERFANG')))
    ok('Thunder 008 110/85, Blizzard 00D 110/85, Hurricane 015 110/85', (f('THUNDER')[3], f('THUNDER')[4], f('THUNDER')[7]) == ('008', '110', '85') and (f('BLIZZARD')[3], f('BLIZZARD')[4], f('BLIZZARD')[7]) == ('00D', '110', '85') and (f('HURRICANE')[3], f('HURRICANE')[4], f('HURRICANE')[7]) == ('015', '110', '85'))
    ok('Hydro Pump / Fire Blast 110/85; Focus Blast, Gunk Shot, Megahorn 120/85', all((f(n)[4], f(n)[7]) == ('110', '85') for n in ('HYDROPUMP', 'FIREBLAST')) and all((f(n)[4], f(n)[7]) == ('120', '85') for n in ('FOCUSBLAST', 'GUNKSHOT', 'MEGAHORN')))
    ok('Twister 078, Stomp 010, Dragon Rush 010, Whirlpool 0D0 restored', [f(n)[3] for n in ('TWISTER', 'STOMP', 'DRAGONRUSH', 'WHIRLPOOL')] == ['078', '010', '010', '0D0'])
    ok('Headbutt 00F 30%, Spark 007 30%', (f('HEADBUTT')[3], f('HEADBUTT')[9]) == ('00F', '30') and (f('SPARK')[3], f('SPARK')[9]) == ('007', '30'))
    ok('Infestation Special without contact flag', f('INFESTATION')[6] == 'Special' and 'a' not in f('INFESTATION')[12])
    ok('Drain Punch Physical with punch flag; Mega Punch Normal', f('DRAINPUNCH')[6] == 'Physical' and 'j' in f('DRAINPUNCH')[12] and f('MEGAPUNCH')[5] == 'NORMAL')
    ok('Rock Slide, Rock Throw, Bonemerang, Icicle Spear, Thunderous Kick, Feint Attack, Bulldoze, Magnitude Physical', all(f(n)[6] == 'Physical' for n in ('ROCKSLIDE', 'ROCKTHROW', 'BONEMERANG', 'ICICLESPEAR', 'THUNDEROUSKICK', 'FEINTATTACK', 'BULLDOZE', 'MAGNITUDE')))
    ok('Spike Cannon Water Physical non-contact 100%; Wrap Poison; Hold Back Normal non-contact', (f('SPIKECANNON')[5], f('SPIKECANNON')[6], f('SPIKECANNON')[7]) == ('WATER', 'Physical', '100') and 'a' not in f('SPIKECANNON')[12] and f('WRAP')[5] == 'POISON' and f('HOLDBACK')[5] == 'NORMAL' and 'a' not in f('HOLDBACK')[12])
    rc = ('HYPERBEAM', 'GIGAIMPACT', 'FISSURE', 'ROCKWRECKER', 'ROAROFTIME', 'BLASTBURN', 'HYDROCANNON', 'FRENZYPLANT')
    ok('Recharge nukes all 150 / 90%', all((f(n)[3], f(n)[4], f(n)[7]) == ('0C2', '150', '90') for n in rc))
    ok('Pledge trio 80 / 100%', all((f(n)[4], f(n)[7]) == ('80', '100') for n in ('FIREPLEDGE', 'WATERPLEDGE', 'GRASSPLEDGE')))
    ok('Flamethrower, Ice Beam, Thunderbolt chance 10', all(int(f(n)[9]) == 10 for n in ('FLAMETHROWER', 'ICEBEAM', 'THUNDERBOLT')))
    ok('Scald, Body Slam, Discharge 30; Twineedle 20; Poison Fang 30; Heart Stamp, Needle Arm 30', [int(f(n)[9]) for n in ('SCALD', 'BODYSLAM', 'DISCHARGE', 'TWINEEDLE', 'POISONFANG', 'HEARTSTAMP', 'NEEDLEARM')] == [30, 30, 30, 20, 30, 30, 30])
    ok('Shadow Ball 80/100 chance 20; Night Daze 85/95 chance 40; Energy Ball 90/100', (f('SHADOWBALL')[4], f('SHADOWBALL')[7], f('SHADOWBALL')[9]) == ('80', '100', '20') and (f('NIGHTDAZE')[4], f('NIGHTDAZE')[7], f('NIGHTDAZE')[9]) == ('85', '95', '40') and (f('ENERGYBALL')[4], f('ENERGYBALL')[7]) == ('90', '100'))
    ok('Heal Block 0BB, Embargo 0F8, Corrosive Gas 1A1, Telekinesis 11A, Minimize 034, Scary Face 04D 100%', [f(n)[3] for n in ('HEALBLOCK', 'EMBARGO', 'CORROSIVEGAS', 'TELEKINESIS', 'MINIMIZE', 'SCARYFACE')] == ['0BB', '0F8', '1A1', '11A', '034', '04D'] and f('SCARYFACE')[7] == '100')
    ok('Mist = Frostbite status 00C at 90%; Water Sport heals (0D5); Mud Sport Def/SpD (02A)', (f('MIST')[3], f('MIST')[7]) == ('00C', '90') and f('WATERSPORT')[3] == '0D5' and f('MUDSPORT')[3] == '02A')
    ok('Flash = Atk/Speed (026), Smokescreen = foes Atk/SpA -1 (CF14, spread)', f('FLASH')[3] == '026' and f('SMOKESCREEN')[3] == 'CF14' and f('SMOKESCREEN')[10] == '04')
    ok('Miracle Eye original 0A8 kept', f('MIRACLEEYE')[3] == '0A8')
    changed_status = [r for r in P if r[6] == 'Status' and ob[r[1]][3] != r[3]]
    ok('no reworked status move uses an Evasion code (022/034/234) unless it was already original', all(r[3] not in ('022', '034', '234') or ob[r[1]][3] == r[3] for r in changed_status))
    ok('no reworked status move uses a 3-stat boost (02B/035/036/228/039/025)', all(r[3] not in ('02B', '035', '036', '228', '039', '025') for r in changed_status))
    ok('Razor Wind description no longer mentions a charge turn', 'turno' not in f('RAZORWIND')[13].lower() and 'prepara' not in f('RAZORWIND')[13].lower())
    ok('no generic placeholder descriptions', not any(r[13].startswith('Un movimiento de tipo') for r in P))
    return R
def check_pdf(text, facts):
    return [(f'PDF states: {k}', k in text) for k in facts]
