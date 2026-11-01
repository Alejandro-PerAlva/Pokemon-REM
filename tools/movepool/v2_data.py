"""v2 data: mechanic families, per-type preferences, hand overrides, conversions and new moves."""
# family: func code, allowed categories, allowed tiers, effect chance by tier, spanish sentence, english label, extras
F = {
 'flinch':  dict(func='00F', t='EML', ad={'E':20,'M':30,'L':20}, es='Puede hacer retroceder al objetivo.', en='flinch chance'),
 'para':    dict(func='007', t='EML', ad={'E':20,'M':20,'L':30}, es='Puede paralizar al objetivo.', en='paralysis chance'),
 'burn':    dict(func='00A', t='EML', ad={'E':10,'M':20,'L':30}, es='Puede quemar al objetivo.', en='burn chance'),
 'poison':  dict(func='005', t='EML', ad={'E':30,'M':30,'L':30}, es='Puede envenenar al objetivo.', en='poison chance'),
 'freeze':  dict(func='00C', t='EML', ad={'E':10,'M':10,'L':10}, es='Puede congelar al objetivo.', en='freeze chance'),
 'confuse': dict(func='013', t='EML', ad={'E':10,'M':20,'L':20}, es='Puede confundir al objetivo.', en='confusion chance'),
 'atkdrop': dict(func='042', t='EML', ad={'E':30,'M':30,'L':30}, es='Puede bajar el Ataque del objetivo.', en='target Atk -1'),
 'defdrop': dict(func='043', t='EML', ad={'E':30,'M':30,'L':30}, es='Puede bajar la Defensa del objetivo.', en='target Def -1'),
 'spedrop': dict(func='044', t='EML', ad={'E':100,'M':100,'L':30}, es='Baja la Velocidad del objetivo.', en='target Speed -1'),
 'spadrop': dict(func='045', t='EML', ad={'E':30,'M':30,'L':30}, es='Puede bajar el Ataque Especial del objetivo.', en='target SpA -1'),
 'spddrop': dict(func='046', t='EML', ad={'E':30,'M':20,'L':30}, es='Puede bajar la Defensa Especial del objetivo.', en='target SpD -1'),
 'accdrop': dict(func='047', t='EM',  ad={'E':50,'M':30,'L':30}, es='Puede bajar la Precisión del objetivo.', en='target Accuracy -1'),
 'selfatk': dict(func='01C', t='EM',  ad={'E':30,'M':30,'L':30}, es='Puede subir el Ataque del usuario.', en='user Atk +1 chance'),
 'selfdef': dict(func='01D', t='EM',  ad={'E':30,'M':30,'L':30}, es='Puede subir la Defensa del usuario.', en='user Def +1 chance'),
 'selfspe': dict(func='01F', t='EM',  ad={'E':100,'M':100,'L':100}, es='Sube la Velocidad del usuario.', en='user Speed +1'),
 'selfspa': dict(func='020', t='EM',  ad={'E':50,'M':50,'L':50}, es='Puede subir el Ataque Especial del usuario.', en='user SpA +1 chance'),
 'rcl14':   dict(func='0FA', t='ML',  ad={}, es='El usuario sufre 1/4 del daño causado como retroceso.', en='1/4 recoil', cost=True),
 'rcl13':   dict(func='0FB', t='L',   ad={}, es='El usuario sufre 1/3 del daño causado como retroceso.', en='1/3 recoil', cost=True),
 'rcl12':   dict(func='0FC', t='L',   ad={}, es='El usuario sufre la mitad del daño causado como retroceso.', en='1/2 recoil', cost=True),
 'recharge':dict(func='0C2', t='L',   ad={}, es='El usuario debe descansar en el turno siguiente.', en='recharge turn', cost=True),
 'charge':  dict(func='0C3', t='L',   ad={}, es='Primer turno: prepara. Segundo turno: ataca.', en='two-turn charge', cost=True),
 'dropAD':  dict(func='03B', t='ML',  ad={}, es='Baja el Ataque y la Defensa del usuario.', en='user Atk/Def -1', cost=True),
 'dropDS':  dict(func='03C', t='ML',  ad={}, es='Baja la Defensa y la Def. Esp. del usuario.', en='user Def/SpD -1', cost=True),
 'dropSpe': dict(func='03E', t='ML',  ad={}, es='Baja la Velocidad del usuario.', en='user Speed -1', cost=True),
 'dropSpA': dict(func='03F', t='L',   ad={}, es='Baja mucho el Ataque Especial del usuario.', en='user SpA -2', cost=True, cats=('Special',)),
 'drain':   dict(func='0DD', t='EML', ad={}, es='El usuario recupera la mitad del daño causado.', en='HP drain'),
 'pivot':   dict(func='0EE', t='EM',  ad={}, es='Tras atacar, el usuario vuelve para dar paso a otro Pokémon.', en='pivot'),
 'ignore':  dict(func='0A9', t='EM',  ad={}, es='Ignora los cambios de Defensa y Evasión del objetivo.', en='ignores stat boosts'),
 'screen':  dict(func='10A', t='EM',  ad={}, es='Destruye Pantalla de Luz y Reflejo antes de atacar.', en='breaks screens'),
 'knock':   dict(func='0F0', t='EM',  ad={}, es='Hace caer el objeto del objetivo y hace más daño si lo lleva.', en='item removal'),
 'acrit':   dict(func='0A0', t='EM',  ad={}, es='Siempre asesta un golpe crítico.', en='always crits', bp=50),
 'trap':    dict(func='0CF', t='E',   ad={}, es='Atrapa al objetivo entre 4 y 5 turnos.', en='traps target', bp=40),
 'double':  dict(func='0BD', t='E',   ad={}, es='Golpea dos veces seguidas.', en='two guaranteed hits', bp=35),
 'multi':   dict(func='0C0', t='E',   ad={}, es='Golpea de dos a cinco veces seguidas.', en='2-5 hits', bp=20),
 'hexlike': dict(func='07F', t='EM',  ad={}, es='Hace el doble de daño si el objetivo sufre un problema de estado.', en='double vs. status', bp=55),
 'venom':   dict(func='07B', t='EM',  ad={}, es='Hace el doble de daño si el objetivo está envenenado.', en='double vs. poisoned', bp=55),
 'brine':   dict(func='080', t='EM',  ad={}, es='Hace el doble de daño si el objetivo tiene la mitad de PS o menos.', en='double vs. <=50% HP', bp=55),
 'payback': dict(func='084', t='EM',  ad={}, es='Hace el doble de daño si el usuario ataca después del objetivo.', en='double if user moved last', bp=55),
 'assure':  dict(func='082', t='EM',  ad={}, es='Hace el doble de daño si el objetivo ya fue herido en el turno.', en='double if target hurt', bp=55),
 'pursuit': dict(func='088', t='E',   ad={}, es='Hace el doble de daño si el objetivo se va a cambiar.', en='punishes switches', bp=40),
 'crit':    dict(func='000', t='EML', ad={}, es='Tiene un índice alto de golpes críticos.', en='high crit ratio', flag='h'),
 'prio':    dict(func='000', t='E',   ad={}, es='Este movimiento siempre ataca primero.', en='+1 priority', prio=1, bp=40),
}
COST = {k for k, v in F.items() if v.get('cost')}
FUNC2FAM = {v['func']: k for k, v in F.items() if v['func'] != '000'}

# preferences: first usable family wins; generic fallback appended automatically
GEN = ['flinch','crit','atkdrop','defdrop','spedrop','spadrop','spddrop','accdrop','para','burn','poison','confuse','freeze','drain','pivot','ignore','screen','knock','selfatk','selfdef','selfspe','selfspa','hexlike','venom','brine','payback','assure','pursuit','acrit','trap','rcl14','rcl13','dropAD','dropDS','dropSpe','dropSpA','rcl12','recharge','charge','prio','double','multi']
PREF = {
 'NORMAL': ['flinch','crit','defdrop','atkdrop','spedrop','rcl14','pivot','para','confuse','ignore','screen','drain','knock','selfatk'],
 'FIRE': ['burn','spadrop','selfspe','rcl14','selfspa','spddrop','flinch','crit','trap','dropSpA','defdrop'],
 'WATER': ['spedrop','confuse','pivot','accdrop','defdrop','flinch','drain','spddrop','crit','brine'],
 'ELECTRIC': ['para','pivot','spadrop','spedrop','flinch','selfspa','crit','rcl14','drain'],
 'GRASS': ['drain','spddrop','poison','defdrop','para','selfdef','crit','flinch','accdrop'],
 'ICE': ['freeze','spedrop','flinch','defdrop','crit','atkdrop','selfdef'],
 'FIGHTING': ['defdrop','crit','selfatk','flinch','spedrop','drain','dropDS','pivot','rcl13','ignore','screen'],
 'POISON': ['poison','spddrop','spadrop','defdrop','accdrop','atkdrop','flinch','venom','pivot','drain'],
 'GROUND': ['spedrop','accdrop','trap','defdrop','flinch','crit','rcl13','selfspe'],
 'FLYING': ['crit','spedrop','atkdrop','pivot','flinch','selfspe','drain','accdrop','confuse'],
 'PSYCHIC': ['confuse','spddrop','flinch','spadrop','screen','selfspa','drain','pivot','crit','para'],
 'BUG': ['pivot','spedrop','drain','poison','atkdrop','crit','trap','flinch','spadrop'],
 'ROCK': ['defdrop','flinch','spedrop','accdrop','crit','selfdef','rcl13','atkdrop','charge','ignore'],
 'GHOST': ['spddrop','flinch','confuse','crit','drain','spadrop','atkdrop','hexlike','burn'],
 'DRAGON': ['flinch','para','atkdrop','spadrop','crit','dropAD','rcl13','confuse','burn','spddrop'],
 'DARK': ['flinch','knock','atkdrop','spddrop','crit','pivot','drain','payback','defdrop','accdrop'],
 'STEEL': ['selfdef','spddrop','atkdrop','crit','flinch','rcl13','selfatk','ignore','screen','defdrop'],
 'FAIRY': ['spadrop','atkdrop','drain','spddrop','flinch','crit','confuse','pivot','selfspa'],
}

SKIP_BP = {'EXPLOSION','SELFDESTRUCT','MISTYEXPLOSION'}   # left on their own scale
RECHARGE_MAX = 130

# conversions of redundant physical moves into Special (lore permitting) and vice versa
CONV = {}
# new moves: filled in v2_new.py

LABELS = {k.strip(): v for k, v in (l.split(':', 1) for l in """SNORE:only usable while asleep
FAKEOUT:first-turn flinch (+3 priority)
CHATTER:confusion (sound)
HURRICANE:never misses in rain, hits fliers
TRIATTACK:burn/para/freeze chance
PSYSHIELDBASH:user Def +1 on hit
SILVERWIND:all-stat +1 chance
OMINOUSWIND:all-stat +1 chance
ANCIENTPOWER:all-stat +1 chance
ACIDSPRAY:target SpD -2
CLEARSMOG:resets target stat changes
SONICBOOM:fixed 20 damage
DRAGONRAGE:fixed 40 damage
SUPERFANG:halves target HP
SEISMICTOSS:damage equals user level
NIGHTSHADE:damage equals user level
ENDEAVOR:brings target HP down to user HP
PSYWAVE:random level-based damage
COUNTER:returns double physical damage
MIRRORCOAT:returns double special damage
METALBURST:returns 1.5x damage
FLAMEBURST:splash damage on target's ally
SURF:spread, double vs diving
EARTHQUAKE:spread, double vs digging
GUST:hits fliers, double vs Fly
TWISTER:hits fliers, flinch chance
SMELLINGSALTS:double vs paralysed, cures it
WAKEUPSLAP:double vs sleeping, wakes it
FACADE:double when user is statused
REVENGE:double if user was hurt this turn
AVALANCHE:double if user was hurt first
ROUND:stronger when used repeatedly
RETALIATE:stronger after an ally faints
ACROBATICS:double without a held item
WEATHERBALL:type and power follow weather
RETURN:friendship-scaled power
FRUSTRATION:inverse-friendship power
ERUPTION:power scales with user HP
WATERSPOUT:power scales with user HP
WRINGOUT:power scales with target HP
GYROBALL:power scales with target speed advantage
STOREDPOWER:power scales with user boosts
POWERTRIP:power scales with user boosts
PUNISHMENT:power scales with target boosts
HIDDENPOWER:type set by IVs
FURYCUTTER:power doubles on consecutive use
ECHOEDVOICE:power builds across turns
RAGE:Attack rises when hit
RAGINGFURY:locks in 2-3 turns, then confuses
PRESENT:random heal or damage
MAGNITUDE:random power
NATURALGIFT:berry-dependent power
TRUMPCARD:power scales with remaining PP
REVERSAL:power scales with low HP
FLAIL:power scales with low HP
ELECTROBALL:power scales with speed advantage
LOWKICK:weight-based power
GRASSKNOT:weight-based power
HEATCRASH:weight-ratio power
HEAVYSLAM:weight-ratio power
MULTIATTACK:type follows held memory
SECRETPOWER:terrain-based side effect
FEINT:breaks Protect
TWINEEDLE:two hits + poison chance
TRIPLEKICK:three escalating hits
TRIPLEAXEL:three escalating hits
BEATUP:one hit per party member
SKYATTACK:two-turn, high crit, flinch chance
SKULLBASH:two-turn, Def +1 on charge
FLY:two-turn, semi-invulnerable
BOUNCE:two-turn, semi-invulnerable, paralysis
DIG:two-turn, underground
DIVE:two-turn, underwater
SKYDROP:two-turn, carries target
WHIRLPOOL:traps, hits divers
UPROAR:lock-in sound, prevents sleep
OUTRAGE:locks in 2-3 turns, then confuses
PETALDANCE:locks in 2-3 turns, then confuses
THRASH:locks in 2-3 turns, then confuses
ICEBALL:five-turn doubling lock-in
ROLLOUT:five-turn doubling lock-in
BIDE:stores and returns damage
DREAMEATER:only vs sleeping, drains
EXPLOSION:user faints
SELFDESTRUCT:user faints
FINALGAMBIT:deals user HP, user faints
FALSESWIPE:leaves 1 HP
DRAGONTAIL:forces target to switch
CIRCLETHROW:forces target to switch
THIEF:steals target item
COVET:steals target item
BUGBITE:eats target berry
PLUCK:eats target berry
INCINERATE:burns berries and gems
FLING:throws held item
VOLTTACKLE:1/3 recoil + paralysis
FLAREBLITZ:1/3 recoil + burn
GRASSPLEDGE:combines with other Pledge moves
WATERPLEDGE:combines with other Pledge moves
PAYDAY:earns money
HIGHJUMPKICK:crash damage on miss
JUMPKICK:crash damage on miss
RAPIDSPIN:clears hazards, user Speed +1
FUTURESIGHT:hits two turns later
SPITUP:uses Stockpile
FOCUSPUNCH:needs focus (-3 priority)
SUCKERPUNCH:+1 priority, only vs attackers
SKYUPPERCUT:hits airborne targets
SMACKDOWN:grounds the target
FOULPLAY:uses target's Attack
PSYSHOCK:hits Defense
SYNCHRONOISE:hits same-type targets only
LASTRESORT:needs all moves used
FREEZEDRY:super effective vs Water
FLYINGPRESS:Fighting + Flying damage
PHANTOMFORCE:two-turn, breaks Protect
DRAININGKISS:drains 75%
FELLSTINGER:Attack +3 on KO
BELCH:needs a berry eaten
FIRSTIMPRESSION:+2 priority, first turn only
BODYPRESS:uses Defense as Attack
FISHIOUSREND:double if user moves first
BOLTBEAK:double if user moves first
SNIPESHOT:ignores redirection, high crit
JAWLOCK:traps both battlers
METEORBEAM:two-turn, SpA +1 on charge
DOUBLEIRONBASH:two hits + flinch chance
REVELATIONDANCE:type follows user
BEAKBLAST:-3 priority, burns contact
BURNUP:removes user's Fire type
RISINGVOLTAGE:double on Electric Terrain
MISTYEXPLOSION:user faints
TERRAINPULSE:type/power follow terrain
STEELROLLER:fails without terrain, removes it
SHELLSIDEARM:physical or special, whichever hurts more
EXPANDINGFORCE:boosted in Psychic Terrain
LASHOUT:double after a stat drop
BURNINGJEALOUSY:burns boosted targets
GRASSYGLIDE:+1 priority on Grassy Terrain
DRAGONDARTS:two hits, retargets
GRAVAPPLE:Def -1, boosted in Gravity
STEELBEAM:user loses half max HP
EERIESPELL:drains target PP
DIRECLAW:poison/para/sleep chance
WAVECRASH:1/3 recoil
BARBBARRAGE:double vs poisoned + poison chance
BITTERMALICE:target Atk -1
INFERNALPARADE:burn chance, double vs statused
STONEAXE:sets Stealth Rock
SPIRITSHACKLE:traps target
ANCHORSHOT:traps target
THROATCHOP:blocks sound moves
POLLENPUFF:heals allies instead
STOMPINGTANTRUM:double after a failed move
SPARKLINGARIA:cures burns
FIREFANG:burn or flinch chance
ICEFANG:freeze or flinch chance
THUNDERFANG:paralysis or flinch chance
POISONFANG:badly-poison chance
FEINTATTACK:never misses
SHOCKWAVE:never misses
AURASPHERE:never misses
VITALTHROW:never misses, -1 priority
AERIALACE:never misses
SHADOWPUNCH:never misses
MAGICALLEAF:never misses
SWIFT:never misses, spread
MAGNETBOMB:never misses
DISARMINGVOICE:never misses, spread
SMARTSTRIKE:never misses
FALSESURRENDER:never misses
SOLARBEAM:two-turn (instant in sun)
SOLARBLADE:two-turn (instant in sun)""".split('\n'))}
ES_TYPE = {'NORMAL':'Normal','FIRE':'Fuego','WATER':'Agua','ELECTRIC':'Eléctrico','GRASS':'Planta','ICE':'Hielo','FIGHTING':'Lucha','POISON':'Veneno','GROUND':'Tierra','FLYING':'Volador','PSYCHIC':'Psíquico','BUG':'Bicho','ROCK':'Roca','GHOST':'Fantasma','DRAGON':'Dragón','DARK':'Siniestro','STEEL':'Acero','FAIRY':'Hada'}
