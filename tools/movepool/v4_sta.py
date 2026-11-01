# Format: NAME [>TYPE] ACC DONOR  # why     ('=' keeps; DONOR copies function/target/priority/flags/chance; ACC '=' keeps or number)
STA = r"""
# ---------- Normal status moves that belong to other types (retype only) ----------
ACUPRESSURE >FIGHTING = = # pressure points are martial arts: Fighting gets a self-buff
ATTRACT >FAIRY = = # infatuation is Fairy (charm), not Normal
BESTOW >FAIRY = = # gift-giving
AFTERYOU >FAIRY = = # politeness lets the ally move first
ENCORE >FAIRY = = # the crowd asks for an encore: Fairy
ENDURE >FIGHTING = = # sheer toughness: Fighting
FOCUSENERGY >FIGHTING = = # gathering ki
FOLLOWME >FAIRY = = # all eyes on the cute one
HELPINGHAND >FAIRY = = # lending a hand
HEALBELL >FAIRY = = # a cleansing bell chime
LUCKYCHANT >FAIRY = = # charms against crits
SAFEGUARD >FAIRY = = # a veil of protection
WISH >FAIRY = = # wishes are Fairy
LOVELYKISS >FAIRY 80 = # sleep kiss: Fairy; 75% -> 80%
SING >FAIRY 70 = # lullaby: Fairy; 55% -> 70%
TEETERDANCE >FAIRY = = # a dizzying dance that confuses everyone
BLOCK >ROCK = = # a wall of stone traps the target
HARDEN >ROCK = = # hardening is Rock
CAMOUFLAGE >BUG = = # insect mimicry
DISABLE >GHOST = = # a haunting
MEANLOOK >GHOST = = # an evil glare that traps
PAINSPLIT >GHOST = = # sharing pain
PERISHSONG >GHOST = = # a death knell
DOUBLETEAM >GHOST = = # afterimages
CONVERSION >PSYCHIC = = # mind over matter
CONVERSION2 >PSYCHIC = = # mind over matter
ENTRAINMENT >PSYCHIC = = # transferring ability by thought
PSYCHUP >PSYCHIC = = # copying stat changes mentally
REFLECTTYPE >PSYCHIC = = # copying type mentally
SIMPLEBEAM >PSYCHIC = = # rewriting an ability with a thought beam
MINDREADER >PSYCHIC = FOCUSENERGY # reads weak spots: crit stage +2 instead of the Lock-On clone
GLARE >DRAGON = = # the intimidating stare of a serpent
GROWTH >GRASS = = # plants grow
NATUREPOWER >GRASS = = # nature's call
MORNINGSUN >FIRE = = # the sun heals (Synthesis/Moonlight keep their types)
REFRESH >WATER = = # a refreshing dip cures status
SHELLSMASH >WATER = = # Cloyster/Shellder: Water gets its setup move
SHARPEN >STEEL = = # sharpened steel
ROAR >DARK = = # a fearsome roar forces a switch
SMOKESCREEN >FIRE = WORKUP # smoke is Fire; Accuracy -1 never mattered: now an Atk/SpA setup
STOCKPILE >POISON = = # Swalot's belly
SWALLOW >POISON = = # Swalot swallows
WHIRLWIND >FLYING = = # a gust forces a switch
SUPERSONIC >FLYING 80 = # bat screeches are Flying; 55% -> 80%
HOWL >DARK = COACHING # a pack howl rallies the ally (Atk/Def) instead of a solo Atk +1
CELEBRATE >FAIRY = CALMMIND # a joyful party: SpA/SpD +1
PLAYNICE >FAIRY = = # a friendly plea: Fairy keeps the never-miss Atk -1
HOLDHANDS = = LIFEDEW # shared warmth: heals user and ally 25%
MINIMIZE >FAIRY = = # shrinking is Fairy; original evasion effect untouched
SCARYFACE >GHOST = = # keeps its great identity: Speed -2 at 100%; Ghost retype only
CAPTIVATE >FAIRY = = # keeps the original SpA -2 (opposite gender) effect; charm is Fairy
HEALBLOCK >PSYCHIC = = # keeps the healing-block mechanic
FLASH >ELECTRIC = LASERFOCUS # a dazzling flash: Electric focus move, next attack crits (was a dead Accuracy -1)
FORESIGHT = = HONECLAWS # dead Normal-Ghost identify move: Atk/Acc +1
ODORSLEUTH = = STUFFCHEEKS # dead identify move: eats berry, Def +2
MIRACLEEYE = = NASTYPLOT # the psychic eye focuses the mind: SpA +2
LOCKON >STEEL = LASERFOCUS # targeting lock: next attack crits
LEER >DARK 90 SCREECH # a menacing glare: Def -2 (single stat) instead of duplicating Tail Whip
WITHDRAW = = DEFENDORDER # retreat into the shell: Def +1 and SpD +1, no Evasion
DEFENSECURL = = IRONDEFENSE # curling hardens the body: Def +2, no Evasion
SANDATTACK = 100 COSMICPOWER # sand armour: Def/SpD +1 (the Accuracy -1 never mattered)
MUDSPORT = = HONECLAWS # mud-caked claws: Atk/Acc +1
ROTOTILLER = = BULKUP # till and bulk up: Atk/Def +1
# ---------- other types: reworks of redundant / dead-weight status moves ----------
MEDITATE = = TAKEHEART # a calm mind: cure status and SpA/SpD +1 instead of Atk +1
MAGNETICFLUX = = NASTYPLOT # Plus/Minus-only effect: Electric SpA +2 setup
WATERSPORT = = RECOVER # a Water recovery move
GEARUP = = WORKUP # Plus/Minus-only effect: Steel Atk/SpA +1
AROMATICMIST = = JUNGLEHEALING # doubles-only SpD buff: heals 25% and cures status
MIST = 90 WILLOWISP # the Ice Will-O-Wisp: inflicts Frostbite at 90%
WILLOWISP = 90 = # 85% -> 90%, matching Mist
SWEETSCENT >GRASS = CONFIDE # blossom scent saps SpA (the old Evasion drop did nothing)
KINESIS = 100 TICKLE # Accuracy -1 was dead weight: a spoon-bending Atk/Def drop for Psychic
NOBLEROAR >DRAGON = = # a dragon's roar lowers Atk/SpA; Normal keeps Tearful Look
SOFTBOILED >FAIRY = = # Chansey's lucky egg heals: Fairy (Recover/Milk Drink/Slack Off stay Normal)
SPEEDSWAP >ELECTRIC = = # a swap of speed: Electric
HEARTSWAP >FAIRY = = # swapping hearts is Fairy
MAGICPOWDER >FAIRY = = # magic powder is Fairy
LUNARBLESSING >FAIRY = = # moonlight blessing, with Moonlight
# ---------- signature moves (annex) ----------
SPLASH >WATER = AGILITY # Magikarp's splash: Water Speed +2 setup instead of nothing
DARKVOID = 70 = # the 50% sleep coin flip: 70%, still the weakest sleep move
THUNDERWAVE = 100 = # 90% -> 100%, parity with Glare
TOXIC = 95 = # 90% -> 95%
GLARE = 100 = # unchanged accuracy, kept as Normal's paralysis stare
# ---------- v6: de-cloned status reworks ----------
FLASH >ELECTRIC = DRAGONDANCE flags=d # a dazzling flash of speed: Atk +1 and Speed +1 (a clean 2-stat Electric setup)
SMOKESCREEN >FIRE = TEARFULLOOK tgt=04 flags=bce # a smoke cover over all foes: Atk and SpA -1 (spread)
MUDSPORT = = DEFENDORDER # mud-caked guard: Def and SpD +1
SANDATTACK = 100 IRONDEFENSE # sand armour: Def +2
HOWL >DARK = WORKUP # a pack howl: Atk and SpA +1 (Coaching dropped: doubles-only)
MIRACLEEYE = = ORIG # keeps its psychic anti-Dark / evasion function
FORESIGHT >PSYCHIC = ORIG # keeps its identify-Ghost function
ODORSLEUTH = = ORIG # keeps its identify function (Stuff Cheeks dropped: fails without a berry)
LOCKON >STEEL = ORIG # keeps 'next attack never misses'; Steel retype
SWEETSCENT >GRASS = ORIG # keeps its original effect
# ---------- accuracy tidy-ups (sleep/status inducers: no longer 50-60%) ----------
HYPNOSIS = 75 = # 60% -> 75%
GRASSWHISTLE = 70 = # 55% -> 70%
SLEEPPOWDER = 80 = # 75% -> 80%
STUNSPORE = 90 = # 75% -> 90%
POISONPOWDER = 90 = # 75% -> 90%
SWEETKISS = 80 = # 75% -> 80%
SWAGGER = 90 = # 85% -> 90%
SCREECH = 90 = # 85% -> 90%
LEECHSEED = 95 = # 90% -> 95%
STRINGSHOT = 100 = # 95% -> 100%
METALSOUND = 90 = # 85% -> 90%
POISONGAS = 90 = # already 90
"""
# Spanish effect sentence of each donor (appended to the move's own lore sentence)
DONOR_ES = {
 'DRAGONDANCE': 'Sube el Ataque y la Velocidad del usuario.',
 'STUFFCHEEKS': 'El usuario se come su Baya y sube mucho su Defensa.',
 'SWORDSDANCE': 'Sube mucho el Ataque del usuario.', 'WORKUP': 'Sube el Ataque y el Ataque Especial del usuario.', 'CALMMIND': 'Sube el Ataque Especial y la Defensa Especial del usuario.',
 'SHIFTGEAR': 'Sube el Ataque y mucho la Velocidad del usuario.', 'NASTYPLOT': 'Sube mucho el Ataque Especial del usuario.', 'IRONDEFENSE': 'Sube mucho la Defensa del usuario.',
 'BULKUP': 'Sube el Ataque y la Defensa del usuario.', 'HONECLAWS': 'Sube el Ataque y la Precisión del usuario.', 'RECOVER': 'El usuario recupera la mitad de sus PS.',
 'EERIEIMPULSE': 'Baja mucho el Ataque Especial del objetivo.', 'WILLOWISP': 'Congela al objetivo (Congelación: daño residual y mitad de Ataque Especial).', 'LASERFOCUS': 'Su siguiente ataque será un golpe crítico.',
 'TAKEHEART': 'Cura los problemas de estado del usuario y sube su Ataque Especial y Defensa Especial.', 'SHELTER': 'Sube mucho la Defensa y la Evasión del usuario.', 'COACHING': 'Sube el Ataque y la Defensa del aliado.', 'CONFIDE': 'Baja el Ataque Especial del objetivo.',
 'STRENGTHSAP': 'Recupera PS según el Ataque del objetivo y se lo baja.', 'LIFEDEW': 'Recupera el 25% de los PS del usuario y de sus aliados.', 'JUNGLEHEALING': 'Recupera PS y cura los problemas de estado del usuario y sus aliados.',
 'FAKETEARS': 'Baja mucho la Defensa Especial del objetivo.', 'WISH': 'Al turno siguiente, el Pokémon en el lugar del usuario recupera la mitad de sus PS.', 'NOBLEROAR': 'Baja el Ataque y el Ataque Especial del objetivo.',
 'TICKLE': 'Baja el Ataque y la Defensa del objetivo.', 'FOCUSENERGY': 'Aumenta el índice de golpes críticos del usuario.', 'TEARFULLOOK': 'Baja el Ataque y el Ataque Especial del objetivo.',
 'COSMICPOWER': 'Sube la Defensa y la Defensa Especial del usuario.', 'SCREECH': 'Baja mucho la Defensa del objetivo.', 'AGILITY': 'Sube mucho la Velocidad del usuario.', 'DEFENDORDER': 'Sube la Defensa y la Defensa Especial del usuario.',
}
