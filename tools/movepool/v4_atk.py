# Format: NAME [>TYPE] [~Physical|~Special] BP ACC FAM[:CHANCE] [f+x] [f-x]  # rationale
# '=' keeps the original value / function.  ACC must be 90/95/100/0 (never-miss) except the 85% nuke list.
ATK = r"""
# ===================== NORMAL =====================
DOUBLEHIT = 100 = # Early 2-hit precision move: the 90% roll removed
RAGE >DARK 50 100 = # Rage (Attack rises when hit) is Dark/Fighting flavour; 20 BP was unusable
BARRAGE >PSYCHIC ~Special 20 100 = f-a # Exeggcute's thrown eggs are psychic projectiles: Psychic gets an early multi-hit Special
BIND 40 100 = # 15 BP never justified a trapping turn
WRAP >DRAGON 40 100 = # Dratini/Dragonair wrap: Dragon gets a trapper; Normal keeps Bind
CONSTRICT 40 100 = # 10 BP -> Early band; still slows 100%
TAILSLAP >WATER 25 90 = # Azumarill/Poliwhirl tail: Water multi-hit
FURYATTACK >FLYING 15 95 = # beak/horn jabs of Fearow/Spearow/Doduo: Flying multi-hit
FURYSWIPES >DARK 18 90 multicrit # claw swipes of Meowth/Sneasel/Ursaring: Dark multi-hit with crit per hit
DOUBLESLAP 20 90 = # keeps the Normal 2-5 hit role (Fury Attack/Swipes/Comet Punch left)
COMETPUNCH >FAIRY 20 90 = f+j # star-punch barrage of Clefairy/Clefable: Fairy multi-hit punch
SPIKECANNON >STEEL 20 100 = # fired spikes are Steel; the only 100%-accurate multi-hitter
COVET >FAIRY 60 100 = # coaxing, cute item grab: early Fairy Physical
VICEGRIP >BUG 55 100 brine # pincers are Bug; a finisher (doubles vs. <=50% HP)
CUT >GRASS 60 100 ignore # blades/leaves: Grass; slices through Def/Evasion boosts
HOLDBACK 45 100 = f-a # was an exact False Swipe clone; non-contact now
RAPIDSPIN 55 100 = # 50 -> 55 to step between Early and Mid; hazard clearing kept
SECRETPOWER 70 100 = # terrain-based side effect kept; spreads the Normal 70 BP pile-up; original power kept (staircase fixed by moving neighbours up, not this move down)
RETALIATE 70 100 = # conditional double; moved out of the 70 BP pile-up; original power kept (staircase fixed by moving neighbours up, not this move down)
HORNATTACK 65 100 atkdrop:30 # goring horn weakens the target's Attack
CHIPAWAY 70 100 = # boost-ignoring jab sits below the 70 BP staples; original power kept (staircase fixed by moving neighbours up, not this move down)
SMELLINGSALTS 70 100 = # double vs. paralysed (cures it)
SLASH 75 100 = # crit staple one step above the 70 BP pile-up
HEADBUTT 75 100 flinch:30 # flinch staple at 75
CRUSHCLAW 75 95 defdrop:50 # claws shred Defense (50%)
MEGAPUNCH 85 95 atkdrop:30 # a numbing haymaker; 85/85 -> 85/95
SLAM 80 95 defdrop:30 # tail slam cracks guard; 80/75 was a strictly worse Strength
HYPERFANG 80 95 flinch:30 f+i # bite flag for Strong Jaw; 30% flinch
STRENGTH >ROCK 80 100 selfatk:30 # boulder-pushing is Rock; pumps the user's Attack
MEGAKICK 120 95 dropSpe # 120/75 was unplayable; a big kick that leaves the user off-balance (Speed -1); original power kept (staircase fixed by moving neighbours up, not this move down)
ROCKCLIMB 90 95 = # confusion 20%; 85% -> 95%
TAKEDOWN 90 95 = # recoil is the cost; extra 85% accuracy was a double penalty
EGGBOMB >FAIRY 100 90 = # Chansey's lucky egg: Fairy late Physical (bomb flag kept)
DIZZYPUNCH >PSYCHIC 70 100 = # confusion is Psychic; early Psychic Physical (it had only Heart Stamp); original power kept (staircase fixed by moving neighbours up, not this move down)
FRUSTRATION >DARK 1 100 = # power from low friendship: spite is Dark; Return stays Normal
NATURALGIFT >GRASS 1 100 = # berry-powered gift: Grass
PRESENT >FAIRY 1 95 = # a gift that may heal or hurt: Fairy
HORNDRILL 100 90 ignore # OHKO removed: drills through Def/Evasion boosts
GUILLOTINE >DARK 110 100 rcl13 f+h # OHKO removed: crit-prone execution with 1/3 recoil; Dark's missing late Physical
WRINGOUT >POISON 1 100 = # Ekans/Seviper constriction scaled on target HP: Poison variable-power Special
SPITUP >POISON 1 100 = # Stockpile/Spit Up (Swalot): Poison
SONICBOOM >STEEL 40 100 prio1 f+k # fixed 20 damage was obsolete: a +1 priority sonic shock wave (Steel)
RAZORWIND >FLYING 80 100 crit # wind blades: one-turn 80 BP high-crit Flying Special (no charge)
POUND ~Special 40 100 = f-a # clean basic Special Normal hit (Tackle is the Physical one)
SNORE 55 100 = # only usable asleep; one step above the 50 BP band
WEATHERBALL 50 100 = # keeps weather/typing identity
TERRAINPULSE 55 100 = f+m # terrain identity; pulse flag for Mega Launcher
ROUND 60 100 = # ramps with repeated use
HIDDENPOWER 65 100 = # IV-typed Special; 60 -> 65 de-clumps the Special band
HYPERVOICE 90 100 = f+k # spread sound, kept
REVELATIONDANCE 95 100 = # 90 -> 95: dance flag, type of the user
UPROAR 90 100 = # lock-in sound, kept
# ===================== FIRE =====================
FLAMEWHEEL 60 100 burn:20 # thaws the user; , burn 10% -> 20%; original power kept (staircase fixed by moving neighbours up, not this move down)
FIREFANG 65 100 = # Data bug fix: addl 100 (code 00B has its own 10% roll): 10% burn + 10% flinch
FIREPUNCH 75 100 = # unchanged role: burn 10% punch
FIRELASH 80 100 defdrop:100 # whip lowers Defense every time
BLAZEKICK 90 95 = # crit + burn 10%; stepped up to 90
PYROBALL 120 100 = # ball: no drawback, so; original power kept (staircase fixed by moving neighbours up, not this move down)
FIRESPIN 45 90 trap # trapper: 35/85 -> 45/90
INCINERATE 60 100 = # spread: burns berries and gems; original power kept (staircase fixed by moving neighbours up, not this move down)
FLAMEBURST 70 100 = # splash damage on the target's ally; original power kept (staircase fixed by moving neighbours up, not this move down)
BURNINGJEALOUSY 70 100 = # burns targets that raised their stats; original power kept (staircase fixed by moving neighbours up, not this move down)
MYSTICALFIRE 75 100 spadrop:100 # guaranteed SpA -1; original power kept (staircase fixed by moving neighbours up, not this move down)
FIREPLEDGE 80 100 = # combines with Grass/Water Pledge; original power kept (staircase fixed by moving neighbours up, not this move down)
FIERYDANCE 85 100 selfspa:50 # 50% SpA +1; dance
HEATWAVE 95 90 = # spread burn, 90% accuracy
# ===================== WATER =====================
CLAMP 45 90 trap # 35/85 trapper -> 45/90
WHIRLPOOL 45 90 trap # special trapper that hits divers
FLIPTURN 60 100 = # pivot:; original power kept (staircase fixed by moving neighbours up, not this move down)
WATERPULSE 60 100 confuse:20 f+m # pulse flag; confusion kept; original power kept (staircase fixed by moving neighbours up, not this move down)
BRINE 65 100 = # double vs. targets at half HP; original power kept (staircase fixed by moving neighbours up, not this move down)
BUBBLEBEAM 65 100 freeze:10 # frigid foam: Frostbite 10% (Water's cold move)
OCTAZOOKA 70 90 accdrop:50 # ink blinds: 65/85 -> 70/90
RAZORSHELL 75 100 defdrop:50 # shell blades shred Defense:; original power kept (staircase fixed by moving neighbours up, not this move down)
WAVECRASH 75 100 = # 1/3 recoil
WATERPLEDGE 80 100 = # pledge combos; original power kept (staircase fixed by moving neighbours up, not this move down)
SCALD 80 100 = # burn 30%
WATERFALL 80 100 flinch:20 # flinch 20%
LIQUIDATION 85 100 defdrop:20 # Def -1 20%
SNIPESHOT 85 100 = # crit, ignores redirection
FISHIOUSREND 90 100 = # doubles if the user moves first
AQUATAIL 95 95 atkdrop:30 # a tail slam saps Attack; 90/90 -> 95/95
SPARKLINGARIA 95 100 = # cures burns; 90 -> 95
# ===================== ELECTRIC =====================
NUZZLE 40 100 para:30 # Electric had no early Physical: 20 BP / 100% para -> 40 / 30%
SPARK 65 100 spedrop:30 # static cling slows (65 BP paralysis clone removed); original power kept (staircase fixed by moving neighbours up, not this move down)
THUNDERFANG 65 100 = # addl 100 = 10% para + 10% flinch (correct for 009); original power kept (staircase fixed by moving neighbours up, not this move down)
THUNDERPUNCH 75 100 para:10 # punch; paralysis 10%
ZINGZAP 80 100 = # flinch 30%
BOLTBEAK 90 100 = # doubles if the user moves first
CHARGEBEAM 50 100 = # SpA +1 70%
ELECTROWEB 55 100 = # spread Speed -1
PARABOLICCHARGE 65 100 = # spread drain
RISINGVOLTAGE 75 100 = # doubles on Electric Terrain
OVERDRIVE 80 100 spadrop:30 f+k # sound guitar riff weakens SpA (spread)
THUNDERCAGE 85 90 trap # trapping
THUNDER 110 85 = # nuke tier
# ===================== GRASS =====================
SNAPTRAP 45 100 trap # 35 -> 45 trapper
RAZORLEAF 55 100 crit # 95% -> 100%
NEEDLEARM 60 100 flinch:30 # flinch 30%
TROPKICK 70 100 atkdrop:100 # Atk -1 every hit
GRASSYGLIDE 70 100 = # terrain priority glide
HORNLEECH 75 100 = # drain
SEEDBOMB 80 100 poison:30 # poisonous seeds: the Grass poison source
DRUMBEATING 80 100 = # Speed -1 100%
GRAVAPPLE 85 100 = # Def -1, boosted in Gravity
PETALBLIZZARD 90 100 confuse:20 # swirling petals confuse (spread); original power kept (staircase fixed by moving neighbours up, not this move down)
LEAFBLADE 90 100 = # crit
POWERWHIP 120 90 = # 120/85 -> 120/90 (85% reserved for nukes)
ABSORB 40 100 = # 20 BP drain -> Early band
MEGADRAIN 60 100 = # 40 -> 60; Absorb/Mega Drain/Giga Drain staircase 40/60/75
LEAFTORNADO 65 90 = # Accuracy -1 50%
APPLEACID 80 100 = # SpD -1 100%; original power kept (staircase fixed by moving neighbours up, not this move down)
GRASSPLEDGE 80 100 = # pledge
# ===================== ICE (Frostbite = Burn for the Special side) =====================
ICESHARD 40 100 = # +1 priority
AVALANCHE 60 100 = # doubles if hit first; original power kept (staircase fixed by moving neighbours up, not this move down)
ICEFANG 65 100 = # Data bug fix: addl Frostbite + 10% flinch (as Fire Fang's burn); original power kept (staircase fixed by moving neighbours up, not this move down)
ICEPUNCH 75 100 = # Frostbite 10% punch
ICICLECRASH 85 95 = # flinch 30%
MOUNTAINGALE 100 90 freeze:30 # dedicated frostbite heavy hitter: , Frostbite 30%; original power kept (staircase fixed by moving neighbours up, not this move down)
ICEHAMMER 100 90 = # Speed -1 user: unchanged
POWDERSNOW 40 100 freeze:20 # dedicated Frostbite spread: 10% -> 20%
ICYWIND 55 100 = # spread Speed -1
FROSTBREATH 60 100 = # always crits
FREEZEDRY 70 100 = # super effective vs Water
AURORABEAM 75 100 atkdrop:20 # Ice Special mid slot; Atk -1 20%
# ===================== FIGHTING =====================
KARATECHOP 50 100 = # crit
TRIPLEARROWS 50 100 = # Def -1 + flinch
ROCKSMASH >ROCK 45 100 defdrop:50 # smashing rocks: Rock early Physical
ROLLINGKICK 60 95 flinch:30 # original power kept (staircase fixed by moving neighbours up, not this move down)
CIRCLETHROW 60 90 = # forces a switch
STORMTHROW 60 100 = # always crits
REVENGE 65 100 = # doubles if hurt first
LOWSWEEP 65 100 = # Speed -1 100%
WAKEUPSLAP 70 100 = # double vs. sleeping
BRICKBREAK 75 100 = # screen breaker
DRAINPUNCH 75 100 = # drain
SUBMISSION 80 90 = # 1/4 recoil; 80% -> 90%
BODYPRESS 80 100 = # uses Defense
SKYUPPERCUT 85 95 = # hits airborne
THUNDEROUSKICK 90 100 = # Def -1
CROSSCHOP 100 90 = # crit; 80% -> 90%
FLYINGPRESS 100 100 = # Fighting+Flying; original power kept (staircase fixed by moving neighbours up, not this move down)
FORCEPALM ~Special 60 100 = f-a # shock-wave palm is a ki attack: Fighting's second early Special
FOCUSBLAST 120 85 = # nuke tier, 120 BP kept
VACUUMWAVE 40 100 = # +1 priority Special
# ===================== POISON =====================
POISONSTING 40 100 poison:30 # 15 -> 40 BP
POISONFANG 50 100 = # badly poison
POISONTAIL 55 100 = # crit + poison
DIRECLAW 60 100 = # poison/para/sleep
BARBBARRAGE 70 100 = # double vs. poisoned + poison
CROSSPOISON 75 100 = # crit + poison 10%
POISONJAB 85 100 poison:30 # 80 -> 85
GUNKSHOT 120 85 = # nuke tier, 120 BP kept
SMOG 40 100 poison:40 # 30/70 was below the floor
ACID 45 100 = # spread SpD -1 10%
ACIDSPRAY 50 100 = # SpD -2 guaranteed
CLEARSMOG 55 100 = # resets stats
VENOSHOCK 65 100 = # double vs poisoned
SLUDGE 70 100 = # poison 30
SLUDGEBOMB 90 100 = # poison 30
SLUDGEWAVE 95 100 = # spread poison 10
BELCH 1 100 hpscale # needed a berry; becomes an HP-scaling toxic overflow (08B)
# ===================== GROUND =====================
SANDTOMB 45 90 trap # trapper 35/85 -> 45/90
BONEMERANG 50 95 = # two hits
BONECLUB 65 95 atkdrop:30 # club blows weaken Attack; original power kept (staircase fixed by moving neighbours up, not this move down)
STOMP >GROUND 65 100 flinch:30 # stomping feet: Ground flinch
STOMPINGTANTRUM 75 100 = # doubles after a failed move
DRILLRUN 85 100 = # crit; 80/95 -> 85/100
HIGHHORSEPOWER 95 100 defdrop:30 # hooves crush Defense; 95/95 -> 95/100
BULLDOZE ~Special 60 100 = f-a # the shaking ground is a spread Special
MUDSLAP 40 100 = # 20 -> 40, Accuracy -1 100%
MUDSHOT 55 100 = # Speed -1; original power kept (staircase fixed by moving neighbours up, not this move down)
MUDBOMB 65 90 = # Accuracy -1 30%
SCORCHINGSANDS 70 100 = # burn 30
MAGNITUDE 1 100 hpscale # random power -> HP-scaling (08B), second user after Eruption/Water Spout
FISSURE 120 90 recharge # OHKO removed: recharge nuke
# ===================== FLYING =====================
PECK 40 100 = # 35 -> 40
DUALWINGBEAT 40 95 = # two hits
ACROBATICS 55 100 = # doubles with no item
PLUCK 60 100 = # eats berry; original power kept (staircase fixed by moving neighbours up, not this move down)
WINGATTACK 60 100 flinch:20 # wing buffet can flinch
SKYDROP 60 100 = # carries the target
AERIALACE 65 0 = # never misses; 60 -> 65
DRILLPECK 80 100 ignore # a boring beak pierces Def/Evasion boosts
GUST 40 100 = # hits fliers
AIRCUTTER 60 95 freeze:20 f+h # frigid wind blades: Frostbite 20% spread, high crit
CHATTER 65 100 = # confusion 100%
AIRSLASH 75 95 = # flinch 30%
# ===================== PSYCHIC =====================
HEARTSTAMP 60 100 = # flinch 30
PSYCHOCUT 70 100 = # crit; original power kept (staircase fixed by moving neighbours up, not this move down)
PSYSHIELDBASH 75 100 = # Def/SpD? +1 on hit
ZENHEADBUTT 90 90 = # flinch 20; late Psychic Physical
PSYCHICFANGS 85 100 = # screen breaker
CONFUSION 50 100 = # confusion 10
PSYBEAM 65 100 = # confusion 10; original power kept (staircase fixed by moving neighbours up, not this move down)
EXTRASENSORY 80 100 flinch:20 # flinch; original power kept (staircase fixed by moving neighbours up, not this move down)
ESPERWING 80 100 = # crit + Speed +1
PSYSHOCK 80 100 = # hits Defense
EXPANDINGFORCE 85 100 = # terrain boosted spread
PSYCHIC 90 100 = # unchanged staple (SpD -1 10%)
FREEZINGGLARE 95 100 freeze:20 # Psychic Frostbite: 90/10% -> 95/20%
EERIESPELL 80 100 = # drains PP; original power kept (staircase fixed by moving neighbours up, not this move down)
# ===================== BUG =====================
INFESTATION 40 100 trap # 20 BP trapper
FURYCUTTER 40 100 = # chain
FELLSTINGER 50 100 = # +3 Atk on KO
BUGBITE 60 100 = # eats berry
STEAMROLLER 65 100 = # flinch 30
SKITTERSMACK 75 100 = # SpA -1 100%
XSCISSOR 80 100 screen # scissors cut through barriers
LEECHLIFE 80 100 = # drain
LUNGE 85 100 = # Atk -1 100%
ATTACKORDER 90 100 = # crit
POLLENPUFF 90 100 = # heals allies; original power kept (staircase fixed by moving neighbours up, not this move down)
SILVERWIND 60 100 selfall:30 # all-stat +1 chance 10 -> 30%
SIGNALBEAM 75 100 = # confusion 10
# ===================== ROCK =====================
ROCKTHROW 55 95 accdrop:30 # dust in the eyes; 50/90 -> 55/95
ROCKBLAST ~Special 25 95 = f-a # a projectile volley: Rock's second Special
ROCKTOMB ~Special 60 100 = f-a # rain of boulders: Special; slows; original power kept (staircase fixed by moving neighbours up, not this move down)
ROCKSLIDE 75 95 = # spread flinch
STONEAXE 65 95 = # Stealth Rock on hit
STONEEDGE 100 90 = # crit; 80% -> 90%
HEADSMASH 150 90 = # 1/2 recoil; acc raised (not nerfed)
ANCIENTPOWER 60 100 selfall:30 # 10 -> 30%: a real setup attack
POWERGEM 80 100 spddrop:20 # shard debris lowers SpD
# ===================== GHOST =====================
ASTONISH 40 100 flinch:30 # 30 -> 40
LICK 45 100 para:30 # 30 -> 45
SHADOWPUNCH 60 0 = # never misses
SHADOWCLAW 70 100 = # crit
SPIRITSHACKLE 80 100 = # trap
SHADOWBONE 85 100 = # Def -1
BITTERMALICE 60 100 = # Frostbite + double vs status; original power kept (staircase fixed by moving neighbours up, not this move down)
OMINOUSWIND 60 100 selfall:30 # 10 -> 30%: eerie wind empowers
INFERNALPARADE 65 100 = # burn + double vs status
HEX 70 100 = # double vs status
SHADOWBALL 80 100 spddrop:20 # SpD -1 20%
DREAMEATER >GHOST 100 100 = # eating dreams is Ghost: Ghost's late Special
# ===================== DRAGON =====================
DUALCHOP 40 95 = # two hits
DRAGONDARTS 50 100 = # two hits, retarget
BREAKINGSWIPE 60 100 = # spread Atk -1; original power kept (staircase fixed by moving neighbours up, not this move down)
DRAGONTAIL 60 90 = # forces a switch
DRAGONCLAW 80 100 crit # claws: crit
DRAGONHAMMER 90 100 defdrop:30 # crushing hammer lowers Defense
DRAGONRUSH 100 90 flinch:20 # nuke-tier acc 75 -> 90; flinch 20
TWISTER 40 100 = # spread flinch, hits fliers
DRAGONBREATH 60 100 = # paralysis 30
DRAGONRAGE 70 100 crit f+m # real 70 BP pulse with crit, replaces fixed 40 damage
DRAGONPULSE 85 100 spadrop:20 # pulse; SpA -1 20%
# ===================== DARK =====================
PURSUIT 40 100 = # punishes switching
PAYBACK 55 100 = # double if moving last
BITE 60 100 = # flinch 30
ASSURANCE 60 100 = # double if hurt
THIEF 60 100 = # steals
BRUTALSWING 65 100 atkdrop:30 # spread swing weakens Attack
KNOCKOFF 65 100 = # item removal
CEASELESSEDGE 70 100 = # crit + trap
SUCKERPUNCH 70 100 = # +1 priority
NIGHTSLASH 75 100 = # crit
LASHOUT 75 100 = # doubles after a stat drop
THROATCHOP 80 100 = # blocks sound
JAWLOCK 80 100 = # traps both
CRUNCH 80 100 defdrop:30 # Def -1 20 -> 30
FALSESURRENDER 85 0 = # never misses
DARKESTLARIAT 85 100 = # ignores boosts
FOULPLAY 95 100 = # unchanged staple
SNARL 55 100 = # spread SpA -1
DARKPULSE 80 100 = f+m # flinch 20; pulse
NIGHTDAZE 85 95 = # Accuracy -1 40
FIERYWRATH 90 100 = # spread flinch
# ===================== STEEL =====================
BULLETPUNCH 40 100 = # +1 priority punch
METALCLAW 50 100 selfatk:30 # 10 -> 30%: claws sharpen
GEARGRIND 50 95 = # two hits
DOUBLEIRONBASH 60 100 = # two hits + flinch
MAGNETBOMB ~Special 60 0 = f-a # hurled magnetic charge: Steel early Special, never misses
MIRRORSHOT 65 100 = # Accuracy -1 30
STEELWING 70 100 selfdef:30 # Def +1 10 -> 30%
SMARTSTRIKE 75 0 = # never misses
IRONHEAD 80 100 = # flinch 30
ANCHORSHOT 80 100 = # traps
FLASHCANNON 85 100 = # SpD -1 10
METEORMASH 90 95 selfatk:20 # Atk +1 20
IRONTAIL 100 90 defdrop:30 # Def -1 30; 75% -> 90%
# ===================== FAIRY =====================
SPIRITBREAK 75 100 = # SpA -1 100%
PLAYROUGH 90 90 atkdrop:10 # unchanged staple
FAIRYWIND 40 100 = # basic Special
DISARMINGVOICE 45 0 = # never-miss spread sound
DRAININGKISS 50 100 = # 75% drain
DAZZLINGGLEAM 80 100 accdrop:30 # spread; blinding light
MOONBLAST 95 100 = # SpA -1 30
STRANGESTEAM 95 95 confuse:20 # original power kept (staircase fixed by moving neighbours up, not this move down)
MISTYEXPLOSION 100 100 = # self-KO

# ===================== SECOND PASS: collisions, clumps, plain moves, thin cells =====================
BOUNCE 85 95 = # two-turn + paralysis already pay for 85 BP; accuracy 85 -> 95
MUDDYWATER 90 90 = # spread Accuracy -1 30%; 85% -> 90%
RAGINGFURY 120 100 = # lock-in confusion is the drawback: restored to 120/100
SHEERCOLD 130 90 dropSpA # OHKO removed: Overheat-class Ice nuke (SpA -2 on the user)
MEGAHORN 120 85 crit # nuke tier; a horn thrust that crits
POWERWHIP 120 90 defdrop:30 # lashing vines; 85% -> 90%, now crushes Defense 30%
EGGBOMB >FAIRY 100 90 flinch:20 # lucky egg shatters: 20% flinch (bomb flag kept)
HYPERVOICE 90 100 confuse:10 f+k # spread sound; confusion 10%; original power kept (staircase fixed by moving neighbours up, not this move down)
BOOMBURST 140 100 flinch:20 f+k # deafening: flinch 20% on a no-drawback spread nuke
HYDROPUMP 110 85 spedrop:30 # 110/85 nuke; the soaking blast slows 30%
HEADBUTT 70 100 confuse:20 # head trauma confuses; original power kept (staircase fixed by moving neighbours up, not this move down)
SLAM 85 95 dropSpe # heavy slam leaves the user slow (Speed -1)
MEGAPUNCH >FIGHTING 85 95 atkdrop:30 f+j # a punch belongs to Fighting; numbing haymaker
BLAZEKICK 90 95 crit # kick with a high crit ratio (burn left to Pyro Ball)
PYROBALL 120 100 burn:10 # unchanged burn ball; original power kept (staircase fixed by moving neighbours up, not this move down)
CONFUSION 50 100 = # basic early Psychic Special; original power kept (staircase fixed by moving neighbours up, not this move down)
PSYBEAM 65 100 confuse:30 # beam: confusion 30%; original power kept (staircase fixed by moving neighbours up, not this move down)
VENOSHOCK 75 100 = # double vs poisoned; 65 -> 75 fills the Poison Special mid slot
POISONJAB 90 100 poison:30 # late-tier Poison Physical
SLUDGE 70 100 poison:30 # Poison mid Special
MUDBOMB 75 90 = # Accuracy -1 30%; 65 -> 75 fills the Ground Special mid slot
PSYCHICFANGS 95 100 screen # fang crush through screens; 85 -> 95 gives Psychic a second late Physical
POLLENPUFF 90 100 = # Bug late Special (heals allies)
SHADOWBONE 90 100 defdrop:20 # Ghost late Physical
DRAGONHAMMER 90 100 defdrop:30 # Dragon mid Physical; original power kept (staircase fixed by moving neighbours up, not this move down)
MIRRORSHOT 70 100 accdrop:30 # Steel mid Special
HOLDBACK >FAIRY 45 100 = f-a # a gentle blow that leaves 1 HP: early Fairy Physical
# --- Dark staircase 50..110, no more than two moves per step ---
THIEF 60 100 = # steals; original power kept (staircase fixed by moving neighbours up, not this move down)
CEASELESSEDGE 70 100 = # crit + trap
SUCKERPUNCH 70 100 = # +1 priority
LASHOUT 75 100 = # doubles after a stat drop
CRUNCH 85 100 defdrop:30 # Def -1 20% -> 30%; 80 -> 85
FALSESURRENDER 85 0 = # never misses
DARKESTLARIAT 90 100 = # ignores boosts; 85 -> 90

# ===================== THIRD PASS: staircase gaps & clumps =====================
MEGAPUNCH 95 95 atkdrop:30 f+j # stays Normal (a punch need not be Fighting); 85 -> 95 so it stops piling on Body Slam/Slam
PAYDAY 45 100 = # coin-scatter early move: 40 -> 45
SCRATCH 45 100 = # basic claw: 40 -> 45 (still no side effect)
CONSTRICT 50 100 = # coiling squeeze: Speed -1 100% at 50
BIND 50 100 = # trapper at 50
FEINTATTACK 60 0 = # never-miss feint: , out of the Dark 60 pile; original power kept (staircase fixed by moving neighbours up, not this move down)
RAZORSHELL 75 100 defdrop:50 # closes the Water Physical gap between 55 and 70; original power kept (staircase fixed by moving neighbours up, not this move down)
SPARK 65 100 spedrop:30 # closes the Electric Physical 40-60 gap; original power kept (staircase fixed by moving neighbours up, not this move down)
MEGADRAIN 55 100 = # Grass drain staircase 40/55/75
ICEFANG 65 100 = # Ice Physical gap 60-75 (addl fixed to 100)
AURORABEAM 80 100 atkdrop:20 # Ice Special gap 75-90
DRAGONTAIL 65 90 = # Dragon Physical gap 60-80
DISARMINGVOICE 65 0 = # Fairy Special gap 50-80 (never-miss spread sound)
SIGNALBEAM 75 100 confuse:20 # confusion chance 10 -> 20%
DARKPULSE 80 100 flinch:30 f+m # flinch 20 -> 30%
FIERYWRATH 90 100 flinch:30 # flinch 20 -> 30% (spread)

# ===================== FOURTH PASS: chance buffs, canon category fixes =====================
INFESTATION ~Special 40 100 trap # Infestation is a swarm of bugs, a Special trapper; Bug's third early Special
FIREBLAST 110 85 burn:20 # nuke tier: burn 10 -> 20% (Frostbite on Blizzard matches)
BLIZZARD 110 85 freeze:20 # nuke tier: Frostbite 10 -> 20%, same generosity as Fire Blast's burn
HEATWAVE 95 90 burn:20 # spread burn 10 -> 20%
SLUDGEWAVE 95 100 poison:20 # spread poison 10 -> 20%
THUNDER 110 85 para:30 # nuke tier: paralysis 30% kept
PSYCHOCUT 70 100 crit # Psychic Physical mid slot (65 -> 70)
POLLENPUFF 90 100 = # Bug Special mid slot; heals allies; original power kept (staircase fixed by moving neighbours up, not this move down)
MAGMASTORM 100 90 = # annex: 75% broke the floor; 90% keeps it a risky trapping nuke

# ===================== v5: parity fixes =====================
FISSURE 150 90 recharge # OHKO removed: same 150/90 recharge nuke as Giga Impact, Rock Wrecker, Hyper Beam
HURRICANE 110 85 = # v4 left it at 70%: joins Thunder, Blizzard, Fire Blast, Hydro Pump at 110/85
FIREPLEDGE 80 100 = # Pledge trio symmetric: 80/100 each, pledge combo identity kept
WATERPLEDGE 80 100 = # Pledge trio symmetric
GRASSPLEDGE 80 100 = # Pledge trio symmetric
MEGAKICK 120 90 dropSpe # 120/75 -> 120/90; the Speed -1 on the user is the cost
HEADBUTT 70 100 = # classic flinch kept (v4 had replaced it with confusion)
HYPERFANG 80 95 atkdrop:30 f+i # bite flag; gnawing saps Attack, so Headbutt keeps flinch alone
SECRETPOWER 75 100 = # +5: terrain-based effect; spreads the Normal 70 pile-up upwards
SMELLINGSALTS 75 100 = # +5: doubles vs. paralysed and cures it
RAZORSHELL 75 100 defdrop:50 # shell blades shred Defense; accuracy 95 -> 100
LIQUIDATION 90 100 defdrop:30 # +5 BP and Def -1 20 -> 30%
APPLEACID 80 100 = # SpD -1 100% (the Grass special that always lowers SpD)
ENERGYBALL 95 100 spddrop:20 # +5 BP, SpD -1 10 -> 20%: gap to Apple Acid
SPARK 65 100 = # original: paralysis 30 (v4 had nerfed it)
THUNDERFANG 65 100 = # original 65; accuracy 95 -> 100, data fix addl 100
ICEFANG 65 100 = # original 65; data fix addl 100
CONFUSION 50 100 confuse:20 # confusion chance 10 -> 20% instead of a BP cut
DIZZYPUNCH >PSYCHIC 60 100 confuse:40 # -10 BP is paid for by a doubled confusion chance (20 -> 40%)
# ===================== v5: Physical -> Special conversions (lore: projectile, shock-wave, tremor, swarm, spectral) =====================
TRIPLEARROWS ~Special 50 100 = f-a # a volley of ki arrows is a projectile
DRAINPUNCH ~Special 75 100 = f-a # a ki-draining blast: Fighting's mid Special (Aura Sphere is the other)
THUNDEROUSKICK ~Special 90 100 = f-a # a kick that releases a thunderous shock wave: Fighting's late Special
MAGNITUDE ~Special 1 100 = f-a # earth tremor: a Special HP-scaling quake
SANDTOMB ~Special 45 90 trap f-a # swirling sand engulfs the target
BONEMERANG ~Special 50 95 = f-a # a hurled bone is a projectile; two hits
ATTACKORDER ~Special 90 100 = f-a # the swarm commanded by Vespiquen is a Special assault
PINMISSILE ~Special 25 100 = f-a # a volley of needles
STRUGGLEBUG 70 100 = # +20: Bug had no mid Special; spread SpA -1 100% stays
ROCKSLIDE ~Special 75 95 = f-a # a rockfall wave
ROCKTHROW ~Special 55 95 accdrop:30 f-a # hurled stones kick up dust
SPIRITSHACKLE ~Special 80 100 = f-a # spectral arrows that pin the target
FEINTATTACK ~Special 60 0 = f-a # a shadow feint that never misses: Dark's early Special
DRAGONDARTS ~Special 50 100 = f-a # darts of draconic energy
SPIKECANNON ~Special 20 100 = f-a # a cannon of spikes is a projectile
BULLETSEED ~Special 25 100 = f-a # seeds fired in a burst
ICICLESPEAR ~Special 25 100 = f-a # shards of ice flung in a burst
UPROAR >FLYING 90 100 = f+k # a raucous song of birds: Flying's late Special
SWIFT 70 0 = # +10: never-miss star burst; Normal Special mid slot
HIDDENPOWER 70 100 = # +5 to step above Swift
DISARMINGVOICE 70 0 = # +5: Fairy Special mid slot (never-miss spread)
DRAGONBREATH 70 100 para:30 # +10: Dragon Special mid slot
DRAGONPULSE 90 100 spadrop:30 f+m # +5 BP, SpA -1 20 -> 30%: Dragon's second late Special
DRAGONTAIL 70 95 = # +5 BP, accuracy 90 -> 95: Dragon Physical mid slot
SHADOWBALL 90 100 spddrop:30 # +10 BP, SpD -1 20 -> 30%: Ghost's late Special
FIERYWRATH 95 100 flinch:30 # +5: Dark late Special
FLASHCANNON 85 100 spddrop:30 # SpD -1 10 -> 30%
POLLENPUFF 90 100 = # Bug late Special (heals allies)
# ===================== v5: effect-chance upgrades (no nerfs) =====================
THUNDERBOLT 90 100 para:20 # paralysis 10 -> 20%, in line with Thunder's 30% and Discharge
FLAMETHROWER 90 100 burn:20 # burn 10 -> 20%, parity with Fire Blast / Lava Plume
ICEBEAM 90 100 freeze:20 # Frostbite 10 -> 20%, as Fire's burn
PSYCHIC 90 100 spddrop:20 # SpD -1 10 -> 20%
EARTHPOWER 90 100 spddrop:20 # SpD -1 10 -> 20%
BUGBUZZ 90 100 spddrop:20 f+k # SpD -1 10 -> 20%; sound flag
MOONBLAST 95 100 spadrop:30 # SpA -1 10 -> 30%
PLAYROUGH 90 95 atkdrop:30 # Atk -1 10 -> 30%; accuracy 90 -> 95
FIREPUNCH 75 100 burn:20 # burn 10 -> 20%
ICEPUNCH 75 100 freeze:20 # Frostbite 10 -> 20%
THUNDERPUNCH 75 100 para:20 # paralysis 10 -> 20%
WATERFALL 80 100 flinch:30 # flinch 20 -> 30%
POISONFANG 50 100 bpoison:50 # badly-poison 30 -> 50%
CIRCLETHROW 60 95 = # accuracy 90 -> 95
THUNDERCAGE 85 95 trap # accuracy 90 -> 95
MUDDYWATER 90 95 = # accuracy 90 -> 95
STONEEDGE 100 95 = # accuracy 90 -> 95 (crit kept)
CROSSCHOP 100 95 = # accuracy 90 -> 95 (crit kept)
SUBMISSION 80 95 = # accuracy 90 -> 95
ICEHAMMER 100 95 = # accuracy 90 -> 95
METEORMASH 90 95 selfatk:30 # Atk +1 20 -> 30%
METALCLAW 50 100 selfatk:30 f+h # claws: Atk +1 30% and a high crit ratio
RAZORSHELL 75 100 defdrop:50 f+h # blades: crit ratio added
STONEAXE 70 95 = # +5: Stealth Rock on hit; Rock Physical mid slot
SHADOWBONE 85 100 defdrop:20 # original power; Ghost Physical mid slot

# ===================== v5: buffs for untouched moves (never nerfs) =====================
TWINEEDLE 25 100 = # two hits: poison chance 20 -> 50%, so the pair of needles matters
BUGBITE 65 100 = # +5: berry-stealing bite; spreads the Bug 60 band
STEAMROLLER 70 100 = # +5: flinch 30% steamroll
FELLSTINGER 55 100 = # +5: the Attack +3 on KO stays the identity
NIGHTDAZE 90 100 accdrop:50 # +5 BP, accuracy 95 -> 100, Accuracy -1 40 -> 50%: Dark late Special
ASSURANCE 65 100 = # +5: doubles if the target was already hurt
THIEF 65 100 = # +5: item thief; moves out of the Dark 60 pile upwards
KNOCKOFF 70 100 = # +5: item removal is the Dark identity
JAWLOCK 85 100 = f+i # +5 and the bite flag (Strong Jaw)
LASHOUT 80 100 = # +5: doubles after a stat drop
THROATCHOP 85 100 = f+k # +5; the chop blocks sound moves (sound flag)
PURSUIT 45 100 = # +5 early punisher of switches
TWISTER 40 100 flinch:30 # spread flinch 20 -> 30%
SCALESHOT 25 95 = # accuracy 90 -> 95
VOLTSWITCH 75 100 = # +5 pivot
PARABOLICCHARGE 70 100 = # +5 spread drain
ZINGZAP 85 100 flinch:30 # +5 BP; flinch 30%
KARATECHOP 55 100 = # +5 crit chop
STORMTHROW 65 100 = # +5 always-crit throw
BRICKBREAK 80 100 = # +5 screen breaker
WAKEUPSLAP 75 100 = # +5 doubles vs sleeping
VITALTHROW 75 0 = # +5 never-miss throw (-1 priority)
BODYPRESS 85 100 = # +5 uses Defense
AURASPHERE 85 0 = f+m # +5 never-miss aura (pulse flag)
FLAMECHARGE 55 100 = # +5 Speed +1 on hit
INCINERATE 65 100 = # +5 spread berry/gem burn
BURNINGJEALOUSY 75 100 = # +5 burns boosted targets
FIRELASH 85 100 = # +5 Def -1 100%
AIRSLASH 75 100 flinch:30 # accuracy 95 -> 100
PLUCK 65 100 = # +5 berry eater
ACROBATICS 60 100 = # +5 doubles without an item
SKYDROP 65 100 = # +5 two-turn carry
SHADOWCLAW 75 100 = # +5 crit claw
SHADOWPUNCH 65 0 = f+j # +5 never-miss punch (punch flag)
BITTERMALICE 65 100 = # +5 Frostbite + double vs. status
LEAFBLADE 95 100 = # +5 crit blade
LEAFTORNADO 70 95 accdrop:30 # +5 BP, accuracy 90 -> 95
NEEDLEARM 65 100 flinch:40 # +5 BP, flinch 30 -> 40%
TROPKICK 75 100 = # +5 Atk -1
DRUMBEATING 85 100 = # +5 Speed -1 100%
GRASSYGLIDE 75 100 = # +5 terrain glide
BONERUSH 25 95 = # accuracy 90 -> 95
SCORCHINGSANDS 75 100 = # +5 burn 30% scorching sand
STOMPINGTANTRUM 80 100 = # +5 doubles after a failed move
AVALANCHE 65 100 = # +5 doubles if hurt first
FREEZEDRY 75 100 freeze:20 # +5 BP, Frostbite 10 -> 20% (it doubles vs Water)
ICEBALL 30 95 = # accuracy 90 -> 95
TRIPLEAXEL 20 95 = # accuracy 90 -> 95
TRIATTACK 85 100 = # +5 BP; tri-status
CRUSHCLAW 75 100 defdrop:50 # accuracy 95 -> 100
RETALIATE 80 100 = # +10 doubles after an ally faints
ROUND 65 100 = # +5 ramps with repeated use
WEATHERBALL 55 100 = # +5 weather-typed
SLUDGEBOMB 90 100 poison:40 # poison 30 -> 40%
DIRECLAW 65 100 = # +5 poison/para/sleep 50%
PSYCHOCUT 75 100 crit # +5 crit blade
HEARTSTAMP 65 100 flinch:40 # +5 BP; flinch 30 -> 40%
SMACKDOWN 55 100 = # +5 grounding smash
ROLLOUT 30 95 = # accuracy 90 -> 95
IRONHEAD 85 100 flinch:30 # +5 BP
DOUBLEIRONBASH 65 100 = # +5 two hits + flinch
BRINE 70 100 = # +5 doubles at half HP
WATERPULSE 65 100 confuse:30 f+m # +5 BP, confusion 20 -> 30%, pulse flag
FLIPTURN 65 100 = # +5 pivot
WAVECRASH 80 100 = # +5 1/3 recoil
CRABHAMMER 100 95 = # accuracy 90 -> 95
DRAININGKISS 55 100 = # +5 75% drain
STRANGESTEAM 95 100 confuse:30 # accuracy 95 -> 100, confusion 20 -> 30%
SPIRITBREAK 80 100 = # +5 SpA -1 100%
LAVAPLUME 85 100 burn:30 # +5: the spread burner steps above Fire Pledge
BODYSLAM 85 100 para:40 # paralysis 30 -> 40%
DISCHARGE 80 100 para:40 # spread paralysis 30 -> 40%
PSYSHOCK 85 100 = # +5: Psychic Special mid slot (hits Defense)
EERIESPELL 85 100 = # +5: drains PP; Psychic Special mid slot
MYSTICALFIRE 80 100 spadrop:100 # +5 and keeps its guaranteed SpA -1
SCALD 80 100 burn:40 # burn 30 -> 40%
STEELBEAM 140 100 = # accuracy 95 -> 100; the 50% HP cost is its drawback
BEAKBLAST 100 100 burn:30 # burn 20 -> 30% for the charging beak
SHELLSIDEARM 90 100 = f+n # bomb flag; poison/physical-special hybrid
LAVAPLUME 80 100 burn:40 # spread burn 30 -> 40% (stays below Heat Wave)

# ===================== v6: engine / code bug fixes =====================
FIREFANG 65 100 =:100 # data bug: addl 100 so code 00B's own 10% roll gives 10% burn + 10% flinch (as Thunder Fang)
ICEFANG 65 100 =:100 # same fix: 10% Frostbite + 10% flinch
THUNDER 110 85 orig # code 008 restored: never misses in rain, 50% in sun
BLIZZARD 110 85 orig:20 # code 00D restored: never misses in hail; Frostbite 20% on the nuke
HURRICANE 110 85 orig # code 015 (rain/sun accuracy, hits fliers), 110/85
TWISTER 40 100 orig # code 078 restored: doubles vs. Fly / Bounce / Sky Drop
HEADBUTT 70 100 orig # the iconic 30% flinch (code 00F) restored
SPARK 65 100 orig # 30% paralysis restored
STOMP >GROUND 65 100 orig # code 010 restored: flinch and double damage vs. Minimize
DRAGONRUSH 100 90 orig # code 010 restored: flinch 20% and double vs. Minimize; accuracy 75 -> 90
WHIRLPOOL 45 90 orig # code 0D0 restored: traps and hits divers
FREEZEDRY 75 100 orig # code 135 restored: super effective vs. Water
BLAZEKICK 90 95 orig # burn 10% and high crit restored
INFESTATION ~Special 40 100 trap f-a # Special now, so no contact flag
DRAINPUNCH ~Physical 75 100 = forig # stays a Physical punch (Iron Fist)
MEGAPUNCH >NORMAL 85 95 atkdrop:30 forig # back to Normal; a numbing haymaker
# ===================== v6: revert awkward conversions =====================
ROCKSLIDE ~Physical 75 95 orig forig # a rockslide is physical impact; Rock keeps Power Gem, Rock Tomb, Rock Blast, Meteor Beam as Specials
ROCKTHROW ~Physical 55 95 accdrop:30 forig # thrown stones are physical
BONEMERANG ~Physical 50 95 = forig # a hurled bone is Physical, like Bone Rush
ICICLESPEAR ~Physical 25 100 = forig # icicles are physical projectiles
THUNDEROUSKICK ~Physical 90 100 orig forig # a kick is physical
FEINTATTACK ~Physical 60 0 orig forig # a sneak strike is physical
BULLDOZE ~Physical 60 100 orig forig # ends the Bulldoze / Mud Shot Speed -1 clone pair
MAGNITUDE ~Physical 1 100 orig forig # random-power quake restored; no 150 BP spread Special next to Earthquake
SPIKECANNON >WATER ~Physical 25 100 = forig # Cloyster / Omastar / Corsola: Water multi-hit, non-contact, 100%
WRAP >POISON 45 100 trap # Arbok / Seviper / Tentacool wrap: Poison trapper
HOLDBACK >NORMAL 45 100 = forig f-a # stays Normal: non-contact False Swipe alternative
# ===================== v6: multi-hit diversity =====================
TAILSLAP >NORMAL 25 90 = forig # Normal contact 2-5 hits (Azumarill's tail is now just this)
DOUBLESLAP >NORMAL 55 100 screen # a two-palm slap that smashes Reflect / Light Screen first
FURYATTACK >FLYING 15 95 multicrit # piercing beak: every hit has a high crit chance
# ===================== v6: tone down inflated chances / stacked buffs =====================
FLAMETHROWER 90 100 burn:10 # back to the clean 10%
ICEBEAM 90 100 freeze:10 # clean 10% Frostbite
THUNDERBOLT 90 100 para:10 # clean 10%
FIREPUNCH 75 100 burn:10 # punches back to 10% too
ICEPUNCH 75 100 freeze:10 # same
THUNDERPUNCH 75 100 para:10 # same
SCALD 80 100 burn:30 # capped at 30%
BODYSLAM 85 100 para:30 # capped at 30%
DISCHARGE 80 100 para:30 # capped at 30%
POISONFANG 50 100 bpoison:30 # badly-poison capped at 30%
HEARTSTAMP 65 100 flinch:30 # flinch capped at 30%
NEEDLEARM 65 100 flinch:30 # flinch capped at 30%
LAVAPLUME 80 100 burn:30 # original 30%
HEATWAVE 95 90 burn:10 # original 10%; the 20% is only for the nukes
SLUDGEBOMB 90 100 poison:30 # original 30%
SLUDGEWAVE 95 100 poison:10 # original 10%
PSYCHIC 90 100 spddrop:10 # original 10%
EARTHPOWER 90 100 spddrop:10 # original 10%
BUGBUZZ 90 100 spddrop:10 f+k # original 10%; sound flag
ENERGYBALL 90 100 spddrop:10 # back to 90 BP / 10%
MOONBLAST 90 100 spadrop:20 # 95 -> 90 BP is paid for by SpA -1 10 -> 20%
SHADOWBALL 80 100 spddrop:20 # original 80 BP / 20%: it no longer outclasses Psychic
DRAGONPULSE 85 100 spadrop:20 f+m # 85 BP kept; SpA -1 20% gives it an identity
FLASHCANNON 80 100 spddrop:10 # original
FIERYWRATH 90 100 flinch:20 # original power and chance
NIGHTDAZE 85 95 accdrop:40 # original 85 / 95% / 40%
CRUSHCLAW 75 95 defdrop:50 # original accuracy
AQUATAIL 90 90 atkdrop:30 # one buff only: Atk -1 30%
SLAM 80 90 dropSpe # 80/75 -> 80/90; Speed -1 on the user is the cost
CUT 55 95 ignore # +5 BP only; boost-ignoring is the new identity
METALCLAW 50 95 selfatk:20 f-h # Atk +1 chance 10 -> 20%, no crit
GUILLOTINE 110 100 rcl13 f-h # OHKO removed: 110 BP with 1/3 recoil, no crit
STRUGGLEBUG 70 100 = # kept
MEGAPUNCH >NORMAL 85 95 flinch:30 forig # back to Normal; a flinching haymaker (Hyper Fang keeps the Atk drop)
PLAYROUGH 90 90 atkdrop:10 # classic staple restored exactly (90/90, Atk -1 10%)
"""
