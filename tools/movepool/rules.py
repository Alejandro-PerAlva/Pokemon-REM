"""Curated data for the movepool rebalance: signature list, hand-tuned overrides, new moves.

Override keys: bp acc pp cat prio func addl  (None/absent = unchanged)
               fadd / fdel  flag letters to add / remove (a contact, b protect, e mirror, f king's rock, h high crit ...)
               fx   = proposed rework / new effect (human text)   why = design rationale
"""

SIGNATURE = """AEROBLAST SACREDFIRE DOOMDESIRE SPACIALREND DARKVOID ORIGINPULSE SPECTRALTHIEF PRECIPICEBLADES ROAROFTIME
SHADOWFORCE JUDGMENT CRUSHGRIP LUSTERPURGE MISTBALL PSYSTRIKE FUSIONFLARE FUSIONBOLT BOLTSTRIKE BLUEFLARE GLACIATE
FREEZESHOCK ICEBURN VCREATE SEEDFLARE HYPERSPACEHOLE HYPERSPACEFURY DIAMONDSTORM STEAMERUPTION LIGHTOFRUIN
THOUSANDARROWS THOUSANDWAVES ETERNABEAM DYNAMAXCANNON BEHEMOTHBLADE BEHEMOTHBASH SECRETSWORD SACREDSWORD RELICSONG
TECHNOBLAST GEOMANCY NATURESMADNESS MINDBLOWN SHELLTRAP CLANGOROUSSOUL CLANGINGSCALES COREENFORCER DRAGONENERGY
PRISMATICLASER PHOTONGEYSER SUNSTEELSTRIKE MOONGEISTBEAM SEARINGSHOT PSYCHOBOOST MAGMASTORM BLASTBURN FRENZYPLANT
HYDROCANNON ASTRALBARRAGE GLACIALLANCE WICKEDBLOW SURGINGSTRIKES CHLOROBLAST AURAWHEEL OBLIVIONWING PLASMAFISTS
FLEURCANNON METEORASSAULT DRAGONASCENT BLEAKWINDSTORM WILDBOLTSTORM SPRINGTIDESTORM SANDSEARSTORM LANDSWRATH
FORESTSCURSE LUNARDANCE DECORATE PURIFY SKETCH TRANSFORM SPLASH STRUGGLE POLTERGEIST SUNSTEELSTRIKE""".split()

# Quality-of-life notes for signature moves (annex only). Same override keys.
PP_CHANGES = {'SILVERWIND', 'ANCIENTPOWER', 'OMINOUSWIND', 'FISSURE'}

SIG_ADJ = {
 'MAGMASTORM': dict(acc=85, why='75% broke the accuracy floor; 85% keeps Heatran\'s trapping nuke risky but fair.'),
 'AEROBLAST':  dict(bp=100, acc=100, fx='Always crits vs. targets with a raised stat', why='95% acc contradicted the 80%+ floor spirit for a legendary-only move; flat 100% keeps the identity (high crit).'),
 'SACREDFIRE': dict(bp=100, acc=100, why='Legendary-exclusive move should not miss 1 time in 20; 50% burn chance retained.'),
 'DOOMDESIRE': dict(bp=120, acc=100, fx='Hits 2 turns later; now also ignores target protection', why='140 BP delayed move was unusable in practice; trimmed BP, kept delay.'),
 'SPACIALREND':dict(acc=100, why='Dragon-type legendary signature; accuracy floor made flat.'),
 'DARKVOID':   dict(acc=70, fx='Sleep for 2 turns max (like Rest-lite); fails if target holds Sleep immunity', why='50% sleep bomb is the most anti-fun move; raise accuracy, shorten sleep, keep Darkrai identity.'),
 'ORIGINPULSE':dict(bp=110, acc=90, why='Aligned with the 110 BP spread-nuke tier (Hydro Pump, Fire Blast).'),
 'ROAROFTIME': dict(bp=140, acc=90, why='Aligned to Hyper Beam-class power; recharge preserved.'),
 'ETERNABEAM': dict(bp=150, acc=90, why='Trimmed from 160 to Hyper Beam parity.'),
 'PRISMATICLASER': dict(bp=140, why='160 BP + recharge exceeded all other 5 PP nukes; align to 140.'),
 'VCREATE':    dict(bp=160, acc=90, why='180 BP with 95% acc is outside the curve; accept recoil on defenses/speed, drop to 160.'),
 'BOLTSTRIKE': dict(acc=90, why='Floor respected; 85% is already the cost of 130 BP.'),
 'BLUEFLARE':  dict(acc=90, why='Matches Fusion Bolt/Flare partner (100 BP, 100%); 130 BP with 90% is the trade-off.'),
 'ICEBURN':    dict(acc=90, why='Charge-turn move; acc aligned to partner Freeze Shock.'),
 'FREEZESHOCK':dict(acc=90, why='Keep partner Ice Burn symmetry (140 BP, 90%).'),
 'POLTERGEIST':dict(bp=105, acc=90, why='Keeps item-dependent accuracy gamble; BP trimmed slightly.'),
 'HYPERSPACEHOLE': dict(acc=0, why='Never-miss Z-style piercing move: avoid exposing Hoopa to accuracy gamble.'),
 'HYPERSPACEFURY': dict(acc=0, why='Same as Hyperspace Hole; sets Defense drop as the cost.'),
 'DRAGONENERGY': dict(bp=120, why='150 BP spread-by-HP is capped at 120 so it is not strictly better than Eruption.'),
 'SUNSTEELSTRIKE': dict(bp=110, why='Brought to the Steel physical late-tier ceiling (Iron Tail 100, Steel Roller 110).'),
 'MOONGEISTBEAM': dict(bp=110, why='Late-tier ceiling for Ghost special without a drawback; compensated by its ability-ignoring identity.'),
 'SPECTRALTHIEF': dict(bp=90, why='Steals boosts after hitting; BP fine.'),
 'PRECIPICEBLADES': dict(bp=120, acc=85, why='Spread move; keep high BP, accuracy over the floor.'),
 'JUDGMENT':   dict(bp=100, why='Unchanged: typed by Arceus plate; documented for completeness.'),
 'LANDSWRATH': dict(bp=90, why='Spread ground; unchanged.'),
 'SEEDFLARE':  dict(bp=120, acc=90, why='Floor respected, 40% SpD -2 effect keeps the risk-reward.'),
 'PSYSTRIKE':  dict(bp=100, why='Hits Defense; unchanged.'),
 'PSYCHOBOOST':dict(bp=130, why='Self SpA -2 is the trade-off; BP reduced from 140.'),
 'SHADOWFORCE':dict(bp=120, why='Two-turn charge; unchanged.'),
 'STEAMERUPTION': dict(bp=110, why='Burn 30%; unchanged.'),
 'DIAMONDSTORM': dict(bp=100, why='Spread; Defense +2 chance; unchanged.'),
 'GLACIATE':   dict(bp=65, why='Speed drop; unchanged.'),
 'SEARINGSHOT':dict(bp=100, why='Spread fire; unchanged.'),
 'FUSIONFLARE':dict(bp=100, why='Boosted after Fusion Bolt; unchanged.'),
 'FUSIONBOLT': dict(bp=100, why='Boosted after Fusion Flare; unchanged.'),
 'MINDBLOWN':  dict(bp=150, acc=100, why='Self 50% HP loss as cost; BP kept (no recharge).'),
 'ASTRALBARRAGE': dict(bp=120, why='Spread ghost; unchanged.'),
 'GLACIALLANCE': dict(bp=130, why='Spread ice; unchanged.'),
 'SURGINGSTRIKES': dict(bp=25, why='Always-crit triple hit; unchanged.'),
 'WICKEDBLOW': dict(bp=80, why='Always-crit; unchanged.'),
}

# ───────────────────────── Hand-tuned overrides (standard moves) ─────────────────────────
O = {}
def o(name, **kw): O[name] = kw

# ---- NORMAL early game: four 40 BP clones become four different tools
o('TACKLE',   bp=50, acc=95, pp=30, fx='Heavier plain hit', why='Tackle is the only early Normal move without a gimmick: more BP, slightly less reliable.')
o('POUND',    bp=40, acc=100, pp=35, func='00F', addl=10, fx='10% flinch', why='Pound becomes the chip-and-flinch option instead of a Tackle clone.')
o('SCRATCH',  bp=40, acc=100, pp=35, fadd='h', fx='High critical-hit ratio', why='Claws find weak spots: Scratch becomes the crit option of the early game.')
o('QUICKATTACK', bp=40, acc=100, pp=30, why='Already differentiated by +1 priority; unchanged anchor of the family.')
o('CUT',      bp=55, acc=100, pp=30, func='0A9', fx='Ignores target stat boosts to Defense and Evasion', why='A field-move slash that cuts through bulk-up setups; no longer a 95% Scratch.')
o('HORNATTACK', bp=65, acc=100, pp=25, fx='None', why='Unchanged anchor: reliable 65 BP horn hit.')
o('STOMP',    bp=65, acc=100, pp=20, why='Flinch 30% retained; unchanged.')
o('HEADBUTT', bp=70, acc=100, pp=15, why='Mid-game flinch staple, unchanged.')
o('SLASH',    bp=70, acc=100, pp=20, why='Mid-game crit staple, unchanged.')
o('SLAM',     bp=85, acc=90, pp=15, func='010', addl=30, fx='30% flinch', why='Slam (80/75) was a worse Strength; now a slower, heavier flinch hit.')
o('STRENGTH', bp=80, acc=100, pp=15, why='Plain mid-game staple (80/100); unchanged.')
o('BODYSLAM', bp=85, acc=100, pp=15, why='30% paralysis retained, unchanged.')
o('MEGAPUNCH',bp=85, acc=90, pp=15, why='80/85 -> 85/90 keeps punching tier distinct from Mega Kick.')
o('MEGAKICK', bp=110, acc=85, pp=5, why='120/75 breaks the accuracy floor; 110/85 puts it in the same tier as Hyper Voice/Stone Edge.')
o('EGGBOMB',  bp=100, acc=85, pp=10, why='100/75 -> 100/85; Gen-1 evo-line tool now meets the floor.')
o('ROCKCLIMB',bp=90, acc=90, pp=15, why='Confusion 20% retained; accuracy trimmed to be a late-tier move with small penalty.')
o('TAKEDOWN', bp=90, acc=90, pp=15, why='Recoil 1/4 retained; 85 -> 90 keeps it distinct from Double-Edge (120/100, 1/3).')
o('DOUBLEEDGE', bp=110, acc=100, pp=15, why='120 BP + 1/3 recoil + 100% was the strongest Normal move; trimmed to the late-tier ceiling.')
o('HEADCHARGE', bp=110, acc=100, pp=15, why='Same cap as Double-Edge; recoil 1/4 retained.')
o('THRASH',   bp=110, acc=100, pp=10, why='Late-tier cap; lock-in confusion is the cost.')
o('MULTIATTACK', bp=110, acc=100, pp=10, why='Late-tier cap; memory-based typing retained.')
o('SKULLBASH',bp=110, acc=100, pp=10, why='Two-turn charge; capped at 110 BP.')
o('GIGAIMPACT', bp=140, acc=90, pp=5, why='Recharge move; aligned just below Hyper Beam (150).')
o('LASTRESORT', bp=130, acc=100, pp=5, why='Conditional; trimmed to avoid overlapping Hyper Beam damage.')
o('HYPERFANG',bp=80, acc=95, pp=15, why='Mid-game flinch bite; accuracy 95 -> reliable.')
o('CRUSHCLAW',bp=75, acc=100, pp=10, why='Defense -1 50%; 95 -> 100 mid-tier reliability.')
o('FURYSWIPES', bp=20, acc=90, pp=15, fadd='h', fx='High critical-hit ratio per hit', why='Fury Swipes/Comet Punch/Fury Attack were near clones; this is the crit multi-hitter.')
o('FURYATTACK', bp=18, acc=90, pp=20, why='The reliable multi-hitter: lower BP, high PP, no crit.')
o('COMETPUNCH', bp=25, acc=90, pp=15, why='Punching multi-hitter with higher BP.')
o('DOUBLESLAP', bp=18, acc=90, pp=15, fx='Hits 2-5 times', why='Aligned with the other multi-hit slaps and above the floor.')
o('BARRAGE',  bp=22, acc=90, pp=15, why='Aligned with the other multi-hit slaps (15/85 -> 22/90); the highest-BP of the group.')
o('BIND',     bp=35, acc=95, pp=20, why='Trapping move, 15 BP was too low to ever be chosen.')
o('WRAP',     bp=40, acc=95, pp=20, why='Trapping move, slightly stronger than Bind.')
o('TAILSLAP', bp=30, acc=90, pp=10, why='Multi-hit tail slap; 85 -> 90 acc.')
o('SPIKECANNON', bp=22, acc=100, pp=15, why='Non-contact multi-hit; stays as the safe version.')
o('DOUBLEHIT',bp=35, acc=95, pp=15, why='Always two hits; 90 -> 95 so it is a reliable low-tier option.')
o('RAGE',     bp=30, acc=100, pp=20, why='Early Normal "Attack +1 when hit" move; BP raised from 20.')
o('FALSESWIPE', bp=40, acc=100, pp=40, why='Utility: leaves target at 1 HP; unchanged.')
o('PAYDAY',   bp=45, acc=100, pp=20, why='Money-utility early move; +5 BP.')
o('COVET',    bp=60, acc=100, pp=25, why='Thief-style item steal; unchanged.')
o('RETALIATE',bp=70, acc=100, pp=5, why='Conditional; unchanged.')
o('CHIPAWAY', bp=70, acc=100, pp=20, why='Ignores stat changes; unchanged.')
o('FACADE',   bp=70, acc=100, pp=20, why='Conditional; unchanged.')
o('SECRETPOWER', bp=70, acc=100, pp=20, why='Terrain-based secondary; unchanged.')
o('DIZZYPUNCH', bp=75, acc=100, pp=10, why='Confusion 20%; 70 -> 75 BP.')
o('SMELLINGSALTS', bp=70, acc=100, pp=10, why='Para-cure/ double; unchanged.')
o('EXTREMESPEED', bp=80, acc=100, pp=5, why='+2 priority; unchanged anchor.')
o('RAZORWIND', bp=80, acc=100, pp=10, why='Two-turn move with high crit; unchanged.')
o('TRIATTACK', bp=80, acc=100, pp=10, why='Triple status chance; unchanged.')
o('HYPERVOICE', bp=90, acc=100, pp=10, why='Spread sound move; unchanged.')
o('UPROAR',   bp=90, acc=100, pp=10, why='Lock-in; unchanged.')
o('BOOMBURST',bp=130, acc=100, pp=10, why='Spread special nuke at 140 -> 130; pays for being the best Normal special.')
o('HYPERBEAM',bp=150, acc=90, pp=5, why='Reference recharge nuke; unchanged.')
o('EXPLOSION',bp=250, acc=100, pp=5, why='Unchanged self-KO.')
o('SELFDESTRUCT', bp=200, acc=100, pp=5, why='Unchanged self-KO.')

o('HOLDBACK', bp=45, acc=100, pp=40, fdel='a', fx='Non-contact; leaves 1 HP', why='Hold Back was an exact False Swipe clone; non-contact + 5 BP gives it a role vs. Rough Skin/Iron Barbs.')

# ---- OHKO reworks (user mandate C)
o('FISSURE',   bp=120, acc=85, pp=5, func='0C2', cat='Physical', fx='Huge ground hit; user must recharge next turn', why='OHKO removed: Fissure is now a recharge nuke (Hyper Beam class) that keeps the "split the earth" fantasy.')
o('GUILLOTINE',bp=110, acc=85, pp=5, func='0FB', fadd='h', fx='1/3 recoil + high crit', why='OHKO removed: Guillotine is a massive, risky blade strike that crits often but punishes the user.')
o('HORNDRILL', bp=100, acc=85, pp=5, func='0A9', fx='Ignores target Defense/Evasion boosts', why='OHKO removed: Horn Drill drills through defensive setup, rewarding it against stall.')
o('SHEERCOLD', bp=130, acc=85, pp=5, func='03F', addl=0, fx='User SpA -2 after use; 30% freeze chance on targets with high HP', why='OHKO removed: Sheer Cold becomes the Overheat of Ice; extreme power with a stat drop.')

# ---- Asymmetric trio / big special accuracy normalisation (110 BP / 85%)
o('BLIZZARD',  bp=110, acc=85, pp=5,  fx='Never misses in Hail', why='70% was the odd one out of the Fire Blast / Thunder / Blizzard trio; all now 110/85.')
o('THUNDER',   bp=110, acc=85, pp=10, fx='Never misses in Rain', why='Same trio fix; keeps rain synergy.')
o('FIREBLAST', bp=110, acc=85, pp=5,  why='Reference of the trio; unchanged.')
o('HYDROPUMP', bp=110, acc=85, pp=5,  why='80 -> 85: matches the other 110 BP nukes.')
o('HURRICANE', bp=110, acc=85, pp=10, fx='Never misses in Rain', why='70% -> 85%; same 110/85 curve as the elemental trio.')
o('ZAPCANNON', bp=100, acc=80, pp=5, why='Guaranteed paralysis kept; 50% acc was un-fun, 80% is the floor and BP trimmed from 120.')
o('INFERNO',   bp=100, acc=50, pp=5, why='Exempt gamble (100% burn): unchanged by the floor rule.')
o('DYNAMICPUNCH', bp=100, acc=50, pp=5, why='Exempt gamble (100% confusion): unchanged by the floor rule.')

# ---- Priority / micro-effect families
o('MACHPUNCH', bp=40, acc=100, pp=30, why='+1 priority punch, unchanged.')
o('BULLETPUNCH', bp=40, acc=100, pp=30, why='+1 priority steel punch, unchanged.')
o('AQUAJET', bp=40, acc=100, pp=20, why='+1 priority water, unchanged.')
o('ICESHARD',bp=40, acc=100, pp=30, why='+1 priority ice, unchanged.')
o('SHADOWSNEAK', bp=40, acc=100, pp=30, why='+1 priority ghost, unchanged.')
o('ACCELEROCK', bp=40, acc=100, pp=20, why='+1 priority rock, unchanged.')

# ---- GRASS
o('BULLETSEED', bp=25, acc=100, pp=30, why='Multi-hit; unchanged.')
o('VINEWHIP', bp=45, acc=100, pp=25, why='Early grass staple; unchanged.')
o('RAZORLEAF',bp=55, acc=100, pp=25, fadd='h', why='95 -> 100 acc: early-tier moves should be reliable; high crit retained.')
o('LEAFAGE',  bp=40, acc=100, pp=40, why='Unchanged high-PP early move.')
o('SEEDBOMB', bp=80, acc=100, pp=15, why='Mid staple; unchanged.')
o('LEAFBLADE',bp=90, acc=100, pp=15, why='High crit; unchanged.')
o('POWERWHIP',bp=110, acc=90, pp=10, why='120/85 -> 110/90: late-tier physical Grass accuracy risk, less spike.')
o('WOODHAMMER', bp=110, acc=100, pp=15, why='120 -> 110 with 1/3 recoil.')
o('SOLARBLADE', bp=110, acc=100, pp=10, why='125 -> 110: still a charge move, same cap as other late-game moves.')
o('LEAFSTORM', bp=120, acc=90, pp=5, why='-2 SpA is the cost; 130 -> 120 to sit with other late nukes.')
o('PETALDANCE', bp=100, acc=100, pp=10, why='120 -> 100: lock-in confusion drawback compensated by 20 BP less.')
o('SOLARBEAM',bp=110, acc=100, pp=10, why='Charge turn (sun skips); 120 -> 110 cap.')
o('SLEEPPOWDER', acc=85, fx='Sleep powder (grass-immune)', why='Grass Powder moves: 75% -> 85% so they are playable but not auto-sleep.')
o('STUNSPORE', acc=85, why='75 -> 85.')
o('GRASSWHISTLE', acc=70, why='55 -> 70 (sleep, sound).')
o('LEECHSEED', acc=95, why='90 -> 95; the seed hits almost always.')

# ---- FIRE
o('EMBER',    bp=45, acc=100, pp=25, why='Early fire; +5 BP to be competitive with Water Gun / Vine Whip.')
o('FLAMEWHEEL',bp=60, acc=100, pp=25, why='Early physical fire; unchanged.')
o('FIREPUNCH',bp=75, acc=100, pp=15, why='Mid physical fire; unchanged.')
o('FLAMETHROWER', bp=90, acc=100, pp=15, why='Reference; unchanged.')
o('HEATWAVE', bp=95, acc=90, pp=10, why='Spread fire; 90% matches the trade-off.')
o('OVERHEAT', bp=120, acc=90, pp=5, why='130 -> 120 (SpA -2 cost remains).')
o('FLAREBLITZ', bp=110, acc=100, pp=15, why='120 -> 110 with 1/3 recoil.')
o('BLAZEKICK', bp=85, acc=90, pp=10, fadd='h', why='High crit; unchanged.')
o('RAGINGFURY', bp=100, acc=90, pp=10, why='Lock-in; 90 -> 100 BP with confusion cost.')
o('PYROBALL', bp=110, acc=90, pp=5, why='Ball physical fire; 120 -> 110.')
o('ERUPTION', bp=150, acc=100, pp=5, why='HP-scaled; unchanged.')
o('WILLOWISP', acc=90, why='85 -> 90; burn is status-only.')

# ---- WATER
o('WATERGUN', bp=40, acc=100, pp=25, why='Unchanged.')
o('BUBBLE',   bp=40, acc=100, pp=30, why='Spread; unchanged.')
o('WATERPULSE', bp=60, acc=100, pp=20, why='Confusion 20%; unchanged.')
o('SURF',     bp=90, acc=100, pp=15, why='Spread; unchanged.')
o('SCALD',    bp=80, acc=100, pp=15, why='Burn 30%; unchanged.')
o('WATERFALL',bp=80, acc=100, pp=15, why='Flinch 20%; unchanged.')
o('AQUATAIL', bp=90, acc=90, pp=10, why='Physical late-tier with accuracy penalty; unchanged.')
o('CRABHAMMER', bp=100, acc=90, pp=10, why='High crit + 90% accuracy trade-off; unchanged.')
o('MUDDYWATER', bp=90, acc=85, pp=10, why='Spread with accuracy drop; unchanged.')
o('WATERSPOUT', bp=150, acc=100, pp=5, why='HP-scaled; unchanged.')

# ---- ELECTRIC
o('NUZZLE',   bp=40, acc=100, pp=20, addl=30, fx='30% paralysis', why='Electric had no early physical move (20 BP / 100% para). Now a true early option.')
o('THUNDERPUNCH', bp=75, acc=100, pp=15, why='Mid physical electric; unchanged.')
o('SPARK',    bp=65, acc=100, pp=20, why='Para 30%; unchanged.')
o('ZINGZAP',  bp=80, acc=100, pp=10, why='Flinch 30%; unchanged.')
o('WILDCHARGE', bp=100, acc=100, pp=15, why='90 -> 100 BP with recoil 1/4 (late-tier parity).')
o('VOLTTACKLE', bp=110, acc=100, pp=15, why='120 -> 110 with 1/3 recoil, 10% para.')
o('THUNDERBOLT', bp=90, acc=100, pp=15, why='Reference; unchanged.')
o('THUNDERWAVE', acc=95, why='90 -> 95; Ground immunity remains the counterplay.')

# ---- ICE
o('ICEBEAM',  bp=90, acc=100, pp=10, why='Reference; unchanged.')
o('ICEPUNCH', bp=75, acc=100, pp=15, why='Mid physical ice; unchanged.')
o('ICICLECRASH', bp=85, acc=95, pp=10, why='90 -> 95 acc (flinch 30%).')
o('ICEHAMMER', bp=100, acc=90, pp=10, why='Speed -1 cost; unchanged.')
o('TRIPLEAXEL', bp=20, acc=95, pp=10, why='Escalating 3-hit; 90 -> 95.')
o('AVALANCHE', bp=60, acc=100, pp=10, why='Revenge-style; unchanged.')

# ---- FIGHTING
o('FOCUSBLAST', bp=110, acc=85, pp=5, why='Fighting had no late special: 120/70 -> 110/85, SpD -1 10% retained.')
o('AURASPHERE', bp=80, acc=0, pp=20, why='Never-miss special; unchanged.')
o('CLOSECOMBAT', bp=110, acc=100, pp=5, why='120 -> 110 with Def/SpD -1 cost.')
o('SUPERPOWER', bp=110, acc=100, pp=5, why='120 -> 110 with Atk/Def -1 cost.')
o('HIGHJUMPKICK', bp=120, acc=90, pp=10, why='Crash damage on miss; 130 -> 120.')
o('JUMPKICK', bp=100, acc=95, pp=10, why='Crash damage on miss; unchanged.')
o('CROSSCHOP', bp=100, acc=80, pp=5, fadd='h', why='High crit; 80% retained = exactly the floor.')
o('SUBMISSION', bp=80, acc=100, pp=15, fx='1/4 recoil', why='80 BP/80% acc with recoil; accuracy to 100 as a mid-tier staple.')
o('ROLLINGKICK', bp=60, acc=95, pp=15, why='Flinch 30%; 85 -> 95 early reliable.')
o('SKYUPPERCUT', bp=85, acc=95, pp=15, why='Hits flying/semi-invulnerable; 90 -> 95.')
o('HAMMERARM', bp=100, acc=90, pp=10, why='Speed -1 cost; unchanged.')
o('FOCUSPUNCH', bp=150, acc=100, pp=20, why='Priority -3 nuke; unchanged.')
o('VACUUMWAVE', bp=40, acc=100, pp=30, why='+1 priority special fighting; unchanged (rare Special fighting early).')

# ---- POISON
o('GUNKSHOT', bp=110, acc=80, pp=5, why='Poison needed a late-tier physical: 120 -> 110 keeps the 80% trade-off.')
o('SLUDGE',   bp=75, acc=100, pp=15, why='Poison had no mid special at 100%: Sludge 65 -> 75 fills the slot.')
o('SMOG',     bp=40, acc=100, pp=20, addl=40, why='30 BP/70% was below the floor: 40 BP/100% with 40% poison.') 
o('POISONSTING', bp=30, acc=100, pp=35, why='15 BP was below the Early band; 30 BP makes it a usable early poison poke.')
o('POISONJAB', bp=80, acc=100, pp=20, why='Reference mid physical; unchanged.')
o('VENOSHOCK', bp=65, acc=100, pp=10, why='Double vs. poisoned; unchanged.')
o('POISONGAS', acc=90, why='90 matches Toxic.')
o('POISONPOWDER', acc=85, why='75 -> 85.')
o('TOXIC', acc=95, why='90 -> 95; Poison-type always hits.')

# ---- GROUND
o('EARTHQUAKE', bp=100, acc=100, pp=10, why='Reference spread move: trade-off is hitting allies; unchanged.')
o('DIG',      bp=80, acc=100, pp=10, why='Two-turn; unchanged.')
o('MUDBOMB',  bp=65, acc=90, pp=10, why='85 -> 90 acc; special mid-early Ground.')
o('EARTHPOWER', bp=90, acc=100, pp=10, why='Reference; unchanged.')
o('MUDSHOT',  bp=55, acc=95, pp=15, why='Speed -1; unchanged.')
o('SANDTOMB', bp=35, acc=90, pp=15, why='Trapping; 85 -> 90.')
o('BONERUSH', bp=25, acc=95, pp=10, why='Multi-hit; 90 -> 95.')
o('HIGHHORSEPOWER', bp=95, acc=95, pp=10, why='Unchanged; accuracy 95.')

# ---- FLYING
o('GUST',     bp=40, acc=100, pp=35, why='Early special flying; unchanged.')
o('AIRCUTTER', bp=60, acc=95, pp=25, fadd='h', why='Spread high-crit; unchanged.')
o('AIRSLASH', bp=75, acc=95, pp=15, fadd='', why='Flinch 30%; unchanged.')
o('DRILLPECK', bp=80, acc=100, pp=20, why='Mid physical; unchanged.')
o('FLY',      bp=90, acc=95, pp=15, why='Two-turn; unchanged.')
o('BRAVEBIRD', bp=110, acc=100, pp=15, why='120 -> 110 with 1/3 recoil.')
o('SKYATTACK', bp=130, acc=90, pp=5, why='Two-turn crit move; 140 -> 130.')
o('BOUNCE',   bp=85, acc=90, pp=5, why='Two-turn para 30%; accuracy 85 -> 90 as a modest reliability lift.')

# ---- PSYCHIC
o('PSYCHICFANGS', bp=100, acc=95, pp=10, why='Psychic had no late physical; breaks screens retained.')
o('ZENHEADBUTT', bp=80, acc=100, pp=15, why='80/90 -> 80/100: mid-tier staples should be reliable; flinch 20%.')
o('PSYCHIC',  bp=90, acc=100, pp=10, why='Reference; unchanged.')
o('FUTURESIGHT', bp=110, acc=100, pp=10, why='Delayed 2 turns; 120 -> 110.')
o('SYNCHRONOISE', bp=100, acc=100, pp=10, why='Same-type only; 120 -> 100.')
o('DREAMEATER', bp=100, acc=100, pp=15, why='Conditional on sleep; unchanged.')
o('KINESIS',  acc=85, why='80 -> 85 evasion lowering.')
o('HYPNOSIS', acc=75, why='Sleep: 60 -> 75%. Sleep Clause remains the counterplay.')
o('PSYSHIELDBASH', bp=70, acc=100, pp=10, why='90 -> 100 acc; Def +1 on hit.')

# ---- BUG
o('XSCISSOR', bp=80, acc=100, pp=15, why='Reference; unchanged.')
o('MEGAHORN', bp=110, acc=90, pp=10, why='120/85 -> 110/90 (late tier, accuracy cost).')
o('FIRSTIMPRESSION', bp=90, acc=100, pp=10, why='+2 priority first-turn; unchanged.')
o('LUNGE',    bp=80, acc=100, pp=15, why='Atk -1 on target; unchanged.')
o('LEECHLIFE', bp=80, acc=100, pp=10, why='Drain 1/2; unchanged.')
o('BUGBUZZ',  bp=90, acc=100, pp=10, why='Late-tier special bug; unchanged. SpD -1 10%.')
o('SIGNALBEAM', bp=75, acc=100, pp=15, why='Confusion 10%; unchanged.')
o('SILVERWIND', bp=60, acc=100, pp=5, why='Stat-boost 10%; PP 5 -> 10.')
o('PINMISSILE', bp=25, acc=95, pp=20, why='Multi-hit; 95 stays.')
o('FURYCUTTER', bp=40, acc=95, pp=20, why='Chain boosting; unchanged.')
o('STRINGSHOT', acc=100, why='95 -> 100 (speed drop utility).')

# ---- ROCK
o('STONEEDGE', bp=100, acc=80, pp=5, why='High crit; floor kept at 80.')
o('ROCKSLIDE', bp=75, acc=90, pp=10, why='Spread flinch; unchanged.')
o('ROCKTHROW', bp=50, acc=95, pp=15, why='90 -> 95 early.')
o('ROCKBLAST', bp=25, acc=90, pp=10, why='Multi-hit; unchanged.')
o('POWERGEM', bp=80, acc=100, pp=20, why='Reference special rock; unchanged.')
o('ANCIENTPOWER', bp=60, acc=100, pp=5, why='All-stat boost 10%; PP 5 -> 10 for early-game use.')
o('METEORBEAM', bp=110, acc=90, pp=10, why='Rock lacked a late-tier special: 120 -> 110, charge turn + SpA +1 retained.')
o('HEADSMASH', bp=140, acc=80, pp=5, why='1/2 recoil; 150 -> 140.')
o('ROCKWRECKER', bp=140, acc=90, pp=5, why='Recharge; 150 -> 140.')
o('ROLLOUT',  bp=30, acc=90, pp=20, why='Doubling lock-in; unchanged.')

# ---- GHOST
o('SHADOWBALL', bp=80, acc=100, pp=15, why='Reference; unchanged.')
o('SHADOWCLAW', bp=70, acc=100, pp=15, fadd='h', why='High crit; unchanged.')
o('PHANTOMFORCE', bp=90, acc=100, pp=10, why='Two-turn; unchanged.')
o('LICK',     bp=30, acc=100, pp=30, why='Para 30%; unchanged.')
o('ASTONISH', bp=30, acc=100, pp=15, why='Flinch 30%; unchanged.')
o('HEX',      bp=65, acc=100, pp=10, why='Double vs. status; unchanged.')
o('BITTERMALICE', bp=60, acc=100, pp=15, why='Atk -1 chance; unchanged.')
o('OMINOUSWIND', bp=60, acc=100, pp=5, why='Stat-boost 10%; PP 5 -> 10.')

# ---- DRAGON
o('DRAGONPULSE', bp=80, acc=100, pp=10, why='Dragon had no mid special: 85 -> 80 shifts into the 70–80 tier.')
o('DRAGONCLAW', bp=80, acc=100, pp=15, why='Reference physical; unchanged.')
o('DRAGONBREATH', bp=60, acc=100, pp=20, why='Para 30%; unchanged.')
o('OUTRAGE',  bp=110, acc=100, pp=10, why='Lock-in confusion; 120 -> 110.')
o('DRAGONRUSH', bp=100, acc=80, pp=10, why='Flinch 20%; 75% -> 80% floor, BP 100.')
o('DRACOMETEOR', bp=110, acc=90, pp=5, why='SpA -2 cost; 130 -> 110 so Dragon has a late special inside the 90-110 band.')
o('DRAGONRAGE', bp=1, acc=100, pp=10, why='Fixed 40 damage: unchanged.')
o('TWISTER',  bp=40, acc=100, pp=20, why='Flinch 20%, spread; unchanged.')
o('SCALESHOT', bp=25, acc=90, pp=20, why='Multi-hit; Spe +1/Def -1.')
o('DRAGONHAMMER', bp=90, acc=100, pp=15, why='Reference physical; unchanged.')

# ---- DARK
o('BITE',     bp=60, acc=100, pp=25, why='Flinch 30%; unchanged.')
o('CRUNCH',   bp=80, acc=100, pp=15, why='Def -1 20%; unchanged.')
o('DARKPULSE',bp=80, acc=100, pp=15, why='Flinch 20%; unchanged.')
o('NIGHTSLASH', bp=70, acc=100, pp=15, fadd='h', why='High crit; unchanged.')
o('SUCKERPUNCH', bp=70, acc=100, pp=5, why='+1 priority conditional; unchanged.')
o('FOULPLAY', bp=95, acc=100, pp=15, why='Uses target Attack; unchanged.')
o('FIERYWRATH', bp=90, acc=100, pp=10, why='Flinch 20% spread; unchanged.')
o('BRUTALSWING', bp=60, acc=100, pp=20, why='Spread dark; unchanged.')
o('PURSUIT',  bp=40, acc=100, pp=20, why='Hits switching foes; unchanged.')
o('THIEF',    bp=60, acc=100, pp=25, why='Steals item; unchanged.')

# ---- STEEL
o('FLASHCANNON', bp=80, acc=100, pp=10, why='Reference; unchanged.')
o('MIRRORSHOT', bp=60, acc=90, pp=10, why='Steel had no early special; 65/85 -> 60/90.')
o('STEELBEAM', bp=110, acc=95, pp=5, why='Steel needed a late special: 140 -> 110 with 50% max-HP cost.')
o('IRONHEAD', bp=80, acc=100, pp=15, why='Flinch 30%; unchanged.')
o('IRONTAIL', bp=100, acc=80, pp=15, why='Def -1 30%; 75 -> 80% floor.')
o('METEORMASH', bp=90, acc=90, pp=10, why='Atk +1 20%; unchanged.')
o('STEELWING', bp=70, acc=100, pp=25, why='Def +1 10%; accuracy 90 -> 100 mid tier.')
o('GEARGRIND', bp=50, acc=85, pp=15, why='Two hits; unchanged.')
o('METALCLAW', bp=50, acc=100, pp=35, why='Atk +1 10%; accuracy 95 -> 100 early.')
o('ANCHORSHOT', bp=80, acc=100, pp=20, why='Trap; unchanged.')
o('STEELROLLER', bp=110, acc=100, pp=5, why='Terrain-removal; 130 -> 110.')

# ---- FAIRY
o('PLAYROUGH', bp=90, acc=90, pp=10, why='Atk -1 10%; unchanged.')
o('SPIRITBREAK', bp=75, acc=100, pp=15, why='SpA -1 100%; unchanged.')
o('DAZZLINGGLEAM', bp=80, acc=100, pp=10, why='Spread; unchanged.')
o('MOONBLAST', bp=95, acc=100, pp=15, why='SpA -1 30%; unchanged.')
o('DRAININGKISS', bp=50, acc=100, pp=10, why='Drain 75%; unchanged.')
o('FAIRYWIND', bp=40, acc=100, pp=30, why='Early special; unchanged.')
o('STRANGESTEAM', bp=90, acc=95, pp=10, why='BP 95 -> 90 to separate it from Moonblast (95/100) now that both are Fairy specials with a 20-30% side effect.')
o('MISTYEXPLOSION', bp=100, acc=100, pp=5, why='Self-KO; unchanged.')
o('CHARM',    acc=100, why='Unchanged.')


# ───────────────────────── New moves proposed to close archetype holes ─────────────────────────
# fields: internal, name_es, name_en, func, bp, type, cat, acc, pp, addl, target, prio, flags, desc, why
NEW = [
 dict(internal='FEYNIP', es='Pellizco Feérico', en='Fey Nip', func='043', bp=50, type='FAIRY', cat='Physical', acc=100, pp=25,
      addl=10, target='00', prio=0, flags='abef', desc='Pellizca al rival con una fuerza traviesa. Puede bajar su Defensa.',
      why='Fairy had zero early-tier physical options (only Spirit Break 75 and Play Rough 90).'),
 dict(internal='BANSHEEWAIL', es='Alarido Espectral', en='Banshee Wail', func='00F', bp=95, type='GHOST', cat='Special', acc=90, pp=10,
      addl=20, target='00', prio=0, flags='bef', desc='Un lamento sobrenatural que hiela el alma. Puede hacer retroceder al objetivo.',
      why='Ghost specials had nothing between Shadow Ball (80) and signature nukes; a late-tier special with 90% acc and flinch.'),
]
