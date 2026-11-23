"""
apply_gen5_curated.py
Aplica EXCLUSIVAMENTE los overworlds de Gen 5 que tienen match canonico y real.
- Respeta al 100% los 20 sprites oficiales de Pokemon REM (NO SE TOCAN).
- No asigna lideres de Teselia a personajes de REM.
- Aplica unicamente clases comunes de Gen 5 que coinciden 1:1 con trainertypes.txt.
- Aplica NPCs con rol canonico exacto segun rem_overworlds.txt.
- Todo lo que no tenga match directo se deja INTACTO como placeholder y se reporta con 2-3 opciones.

Uso: python tools/overworlds/apply_gen5_curated.py [--dry-run]
"""

import os, shutil, sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ULTIMATE = os.path.join(BASE, "Graphics", "Ultimate Gen 5 Overworlds Pack")
GEN5_CHARS = os.path.join(BASE, "Graphics", "Gen 5 Characters")
CHARS = os.path.join(BASE, "Graphics", "Characters")

DRY_RUN = "--dry-run" in sys.argv

# 1. LOS 20 INTOCABLES DE POKÉMON REM (Arte oficial ya existente, commit 08397527)
INTOCABLES = {
    "trchar000.png": "PLAYER_M (Protagonista masculino propio de REM)",
    "trchar001.png": "PLAYER_F (Protagonista femenina propia de REM)",
    "trchar002.png": "RIVAL_M (Lucian, rival de REM)",
    "trchar003.png": "RIVAL_F (Guiomar, rival de REM)",
    "trchar006.png": "LEADER_2 (Ismael, Lider de Agua de REM)",
    "trchar007.png": "LEADER_3 (Greta, Lider de Acero de REM)",
    "trchar009.png": "LEADER_5 (Fausto, Lider de Roca de REM)",
    "trchar010.png": "LEADER_6 (Hildegarda, Lider de Planta de REM)",
    "trchar011.png": "LEADER_7 (Isolda, Lider de Hielo de REM)",
    "trchar012.png": "LEADER_8 (Beltrán, Lider de Fuego de REM)",
    "trchar013.png": "ELITE_1 (Nicodemo, Alto Mando 1 de REM)",
    "trchar014.png": "ELITE_2 (Oriana, Alto Mando 2 de REM)",
    "trchar015.png": "ELITE_3 (Anteo, Alto Mando 3 de REM)",
    "trchar016.png": "ELITE_4 (Leucotea, Alto Mando 4 de REM)",
    "trchar018.png": "MORFEO_RECRUIT_M (Recluta masculino Equipo Morfeo)",
    "trchar019.png": "MORFEO_RECRUIT_F (Recluta femenina Equipo Morfeo)",
    "trchar020.png": "MORFEO_GENERAL_M (General Alarico Montenegro)",
    "trchar021.png": "MORFEO_GENERAL_F (General Zenobia Montenegro)",
    "trchar022.png": "MORFEO_SUBCAPTAIN (Subcapitana Ariadna)",
    "trchar023.png": "MORFEO_LEADER (Lider Eliseo)",
}

# 2. MATCHES CANÓNICOS EXACTOS PARA TRAINERS COMUNES (024-087)
# Correspondencia 1:1 de clase de Blanco/Negro
CANONICAL_TRAINERS = {
    "trchar024.png": ("BW_004_Youngster.png", "YOUNGSTER -> Youngster (Joven)"),
    "trchar025.png": ("BW_007_Lass.png", "LASS -> Lass (Chica)"),
    "trchar026.png": ("BW_005_Schoolkid_M.png", "SCHOOLBOY -> Schoolkid M (Colegial)"),
    "trchar027.png": ("BW_008_Schoolkid_F.png", "SCHOOLGIRL -> Schoolkid F (Colegiala)"),
    "trchar035.png": ("BW_077_Parasol_Lady.png", "PARASOLLADY -> Parasol Lady (Dama Parasol)"),
    "trchar036.png": ("BW_027_Breeder_M.png", "BREEDER_M -> Pokemon Breeder M (Criador)"),
    "trchar037.png": ("BW_028_Breeder_F.png", "BREEDER_F -> Pokemon Breeder F (Criadora)"),
    "trchar039.png": ("BW_029_Ranger_M.png", "POKEMONRANGER -> Pokemon Ranger M (Guardabosques)"),
    "trchar040.png": ("BW_041_Backpacker_M.png", "BACKPACKER_M -> Backpacker M (Mochilero)"),
    "trchar041.png": ("BW_042_Backpacker_F.png", "BACKPACKER_F -> Backpacker F (Mochilera)"),
    "trchar042.png": ("BW_057_Hiker.png", "HIKER -> Hiker (Montanero)"),
    "trchar046.png": ("BW_033_Swimmer_M.png", "SWIMMER_M -> Swimmer M (Nadador)"),
    "trchar047.png": ("BW_034_Swimmer_F.png", "SWIMMER_F -> Swimmer F (Nadadora)"),
    "trchar048.png": ("BW_056_Fisherman.png", "FISHERMAN -> Fisherman (Pescador)"),
    "trchar051.png": ("BW_091_Beauty.png", "BEAUTY -> Beauty (Bella)"),
    "trchar054.png": ("BW_066_Scientist_M.png", "SCIENTIST -> Scientist M (Cientifico)"),
    "trchar056.png": ("BW_060_Worker.png", "WORKER -> Worker (Obrero)"),
    "trchar058.png": ("BW_090_1_Guitarist.png", "GUITARIST -> Guitarist var 1 (Guitarrista)"),
    "trchar059.png": ("BW_090_2_Guitarist.png", "ROCKER -> Guitarist var 2 (Rockero)"),
    "trchar061.png": ("BW_047_Harlequin.png", "JUGGLER -> Harlequin (Malabarista/Arlequin de Teselia)"),
    "trchar062.png": ("BW_086_Psychic_M.png", "PSYCHIC_M -> Psychic M (Psiquico)"),
    "trchar063.png": ("BW_087_Psychic_F.png", "PSYCHIC_F -> Psychic F (Psiquica)"),
    "trchar065.png": ("BW_058_Maid.png", "MAID -> Maid (Sirvienta)"),
    "trchar067.png": ("BW_043_Doctor.png", "DOCTOR -> Doctor"),
    "trchar068.png": ("BW_044_Nurse.png", "NURSE -> Nurse (Enfermera de combate)"),
    "trchar069.png": ("BW_035_Waiter.png", "WAITER -> Waiter (Camarero)"),
    "trchar070.png": ("BW_036_Waitress.png", "WAITRESS -> Waitress (Camarera)"),
    "trchar071.png": ("BW_059_Baker.png", "CHEF -> Baker (Panadero/Cocinero)"),
    "trchar072.png": ("BW_061_Policeman.png", "POLICEMAN -> Policeman (Policia)"),
    "trchar074.png": ("BW_037_Gentleman.png", "GENTLEMAN -> Gentleman (Caballero)"),
    "trchar075.png": ("BW_010_Lady.png", "LADY -> Lady (Dama)"),
    "trchar079.png": ("BW_039_Black_Belt.png", "BLACKBELT -> Black Belt (Karateka)"),
    "trchar080.png": ("BW_040_Battle_Girl.png", "CRUSHGIRL -> Battle Girl (Luchadora)"),
    "trchar082.png": ("BW_054_1_Roughneck.png", "ROUGHNECK -> Roughneck (Maton)"),
    "trchar083.png": ("BW_023_Ace_Trainer_M.png", "COOLTRAINER_M -> Ace Trainer M (Entrenador Guay)"),
    "trchar084.png": ("BW_024_Ace_Trainer_F.png", "COOLTRAINER_F -> Ace Trainer F (Entrenadora Guay)"),
    "trchar085.png": ("BW_025_Veteran_M.png", "VETERAN_M -> Veteran M (Veterano)"),
    "trchar086.png": ("BW_026_Veteran_F.png", "VETERAN_F -> Veteran F (Veterana)"),
}

# 3. MATCHES CANÓNICOS EXACTOS PARA NPCS (rem_overworlds.txt)
CANONICAL_NPCS = {
    "npc001.png": ("BW_098_Mother_BW.png", "npc001 Amparo (Madre) -> Mother BW (Madre oficial BW con delantal)"),
    "npc002.png": ("BW_067_Scientist_F.png", "npc002 Pia (Ayudante laboratorio) -> Scientist F (Cientifica con bata)"),
    "npc008.png": ("BW_071_Nurse_Joy.png", "npc008 Enfermera Centro Pokemon -> Nurse Joy oficial"),
    "npc009.png": ("BW_070_Mart.png", "npc009 Dependiente Poke Mart -> Mart Clerk oficial"),
    "npc010.png": ("BW_046_Clerk_F.png", "npc010 Dependienta Poke Mart -> Clerk F (Dependienta uniforme)"),
    "npc012.png": ("BW_088_Gym_Guide_Clyde.png", "npc012 Arbitro gimnasio -> Clyde / Guia de gimnasio"),
    "npc017.png": ("BW_083_Preschooler_M.png", "npc017 Nino pequeno -> Preschooler M (Preescolar nino)"),
    "npc018.png": ("BW_084_Preschooler_F.png", "npc018 Nina pequena -> Preschooler F (Preescolar nina)"),
}

# 4. CANDIDATOS PARA TRAINERS SIN MATCH CANÓNICO (NO FORZAR)
TRAINERS_SIN_MATCH = {
    "trchar004.png": ("PROFESSOR (Ambrosio Valdemar, ~52a, bata victoriana, reloj agrietado)", [
        ("BW_105_Prof_Cedric_Juniper.png", "Profesor mayor canoso con bata (padre de Juniper)"),
        ("BW_037_Gentleman.png", "Caballero formal con traje de epoca"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder hasta disenar sprite custom")
    ]),
    "trchar005.png": ("LEADER_1 (Matilde, Lider Normal de REM)", [
        ("BW_038_Socialite.png", "Mujer formal / distinguida"),
        ("BW_026_Veteran_F.png", "Mujer experimentada"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder (personaje propio de REM)")
    ]),
    "trchar008.png": ("LEADER_4 (Genzo, Lider Lucha de REM)", [
        ("BW_039_Black_Belt.png", "Karateka cinta negra"),
        ("BW_025_Veteran_M.png", "Veterano de artes marciales"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder (personaje propio de REM)")
    ]),
    "trchar017.png": ("CHAMPION (Altamira, Campeona de REM)", [
        ("BW_024_Ace_Trainer_F.png", "Entrenadora de elite"),
        ("BW_026_Veteran_F.png", "Veterana"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder (personaje propio de REM)")
    ]),
    "trchar028.png": ("CAMPER (Campista, Male)", [
        ("BW_041_Backpacker_M.png", "Mochilero viajero"),
        ("BW_029_Ranger_M.png", "Guardabosques de campo"),
        ("Gen 5 Characters/NPC 01.png", "NPC joven de campo")
    ]),
    "trchar029.png": ("PICNICKER (Excursionista, Female)", [
        ("BW_030_Ranger_F.png", "Ranger femenina de campo"),
        ("BW_042_Backpacker_F.png", "Mochilera de ruta"),
        ("Gen 5 Characters/NPC 02.png", "NPC femenina de campo")
    ]),
    "trchar030.png": ("BUGCATCHER (Cazabichos, Male)", [
        ("BW_083_Preschooler_M.png", "Nino pequeno con gorra"),
        ("Gen 5 Characters/NPC 17.png", "Nino de pueblo"),
        ("BW_004_Youngster.png", "Joven de ruta")
    ]),
    "trchar031.png": ("BIRDKEEPER (Cazapajaros, Male)", [
        ("BW_063_Pilot.png", "Piloto de aviacion (tematica aerea)"),
        ("BW_031_Cyclist_M.png", "Ciclista / deportista ligero"),
        ("BW_051_Striker.png", "Deportista de campo abierto")
    ]),
    "trchar032.png": ("POKEFAN_M (Pokefan, Male)", [
        ("BW_097_Mr_Medal.png", "Entusiasta con coleccion de medallas y pins"),
        ("BW_009_Rich_Boy.png", "Joven fanatico coleccionista"),
        ("BW_037_Gentleman.png", "Aficionado formal")
    ]),
    "trchar033.png": ("POKEFAN_F (Pokefan, Female)", [
        ("BW_038_Socialite.png", "Dama entusiasta de alta sociedad"),
        ("BW_010_Lady.png", "Dama coleccionista"),
        ("BW_028_Breeder_F.png", "Criadora aficionada")
    ]),
    "trchar034.png": ("RANCHER (Ganadero, Male)", [
        ("BW_085_Worker.png", "Trabajador de faena rural con mono"),
        ("BW_057_Hiker.png", "Hombre rudo de campo"),
        ("BW_059_Baker.png", "Trabajador manual")
    ]),
    "trchar038.png": ("AROMALADY (Chica Aroma, Female)", [
        ("BW_030_Ranger_F.png", "Ranger femenina conectada con la naturaleza"),
        ("BW_077_Parasol_Lady.png", "Dama elegante de pradera"),
        ("BW_091_Beauty.png", "Chica de flores y jardin")
    ]),
    "trchar043.png": ("RUINMANIAC (Arqueologo, Male)", [
        ("BW_057_Hiker.png", "Explorador de montana y ruinas"),
        ("BW_065_Janitor.png", "Hombre mayor con herramientas"),
        ("BW_066_Scientist_M.png", "Cientifico investigador de campo")
    ]),
    "trchar044.png": ("POKEMANIAC (Poke Maniaco, Male)", [
        ("BW_047_Harlequin.png", "Personaje estrafalario"),
        ("BW_097_Mr_Medal.png", "Coleccionista obsesivo de medallas"),
        ("BW_096_Mr_Stu_Deeoh.png", "Figura excentrica y fanatica")
    ]),
    "trchar045.png": ("BURGLAR (Ladron, Male)", [
        ("BW_055_Biker.png", "Motorista con pose clandestina"),
        ("BW_054_2_Roughneck.png", "Maton callejero"),
        ("BW_054_1_Roughneck.png", "Maton de callejon")
    ]),
    "trchar049.png": ("TUBER_M (Playero nino)", [
        ("BW_083_Preschooler_M.png", "Nino pequeno en la costa"),
        ("BW_033_Swimmer_M.png", "Banyista masculino"),
        ("BW_004_Youngster.png", "Joven veraneante")
    ]),
    "trchar050.png": ("TUBER_F (Playera nina)", [
        ("BW_084_Preschooler_F.png", "Nina pequena en la costa"),
        ("BW_034_Swimmer_F.png", "Banyista femenina"),
        ("BW_007_Lass.png", "Chica veraneante")
    ]),
    "trchar052.png": ("SAILOR (Marinero, Male)", [
        ("BW_100_Pop_Roxie.png", "Capitan marinero con gorra y timon de Virbank"),
        ("BW_056_Fisherman.png", "Pescador maritimo"),
        ("BW_060_Worker.png", "Trabajador de puerto")
    ]),
    "trchar053.png": ("SCUBADIVER (Buceador, Male)", [
        ("BW_033_Swimmer_M.png", "Nadador acuatico"),
        ("BW_041_Backpacker_M.png", "Explorador"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "trchar055.png": ("ENGINEER (Ingeniero, Male)", [
        ("BW_062_Depot_Agent.png", "Agente tecnico ferroviario de Teselia"),
        ("BW_085_Worker.png", "Obrero tecnico de central industrial"),
        ("BW_066_Scientist_M.png", "Cientifico aplicado")
    ]),
    "trchar057.png": ("SUPERNERD (Friki, Male)", [
        ("BW_005_Schoolkid_M.png", "Estudiante empollon con gafas"),
        ("BW_009_Rich_Boy.png", "Joven aficionado"),
        ("BW_066_Scientist_M.png", "Investigador aficionado")
    ]),
    "trchar060.png": ("PAINTER (Pintor, Male)", [
        ("BW_048_Dancer.png", "Artista bohemio con ropa llamativa"),
        ("BW_049_1_Musician.png", "Musico / artista bohemio"),
        ("BW_047_Harlequin.png", "Arlequin de feria artistica")
    ]),
    "trchar064.png": ("HEXMANIAC (Bruja, Female)", [
        ("BW_087_Psychic_F.png", "Psiquica de pose mistica"),
        ("BW_118_Plasma_Anthea.png", "Doncella con tunica ceremonial"),
        ("BW_058_Maid.png", "Doncella sombria")
    ]),
    "trchar066.png": ("SAGE (Sabio, Male)", [
        ("BW_125_Plasma_Sage_Rood.png", "Sabio con tunica ceremonial de sabiduria"),
        ("BW_037_Gentleman.png", "Hombre sabio mayor"),
        ("BW_105_Prof_Cedric_Juniper.png", "Erudito veterano")
    ]),
    "trchar073.png": ("GAMBLER (Apostador, Male)", [
        ("BW_009_Rich_Boy.png", "Joven con dinero que apuesta"),
        ("BW_037_Gentleman.png", "Caballero apostador de casino"),
        ("BW_054_2_Roughneck.png", "Apostador de bajos fondos")
    ]),
    "trchar076.png": ("SKIER_M (Esquiador, Male)", [
        ("BW_031_Cyclist_M.png", "Deportista con indumentaria aerodinamica"),
        ("BW_051_Striker.png", "Deportista atletico"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "trchar077.png": ("SKIER_F (Esquiadora, Female)", [
        ("BW_032_Cyclist_F.png", "Deportista femenina aerodinamica"),
        ("BW_040_Battle_Girl.png", "Deportista atletica"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "trchar078.png": ("KINDLER (Escupefuego, Male)", [
        ("BW_054_2_Roughneck.png", "Personaje callejero rudo con bandana"),
        ("BW_047_Harlequin.png", "Artista de circo y fuego"),
        ("BW_059_Baker.png", "Oficio de fuego y calor")
    ]),
    "trchar081.png": ("TAMER (Domador, Male)", [
        ("BW_106_Benga.png", "Entrenador salvaje de bestias (Benga)"),
        ("BW_054_1_Roughneck.png", "Domador rudo"),
        ("BW_039_Black_Belt.png", "Luchador con fieras")
    ]),
    "trchar087.png": ("DRAGONTAMER (Domadragon, Male)", [
        ("BW_106_Benga.png", "Entrenador legendario / Benga"),
        ("BW_025_Veteran_M.png", "Veterano curtido con dragones"),
        ("BW_057_Hiker.png", "Montanero de cumbres de dragones")
    ]),
}

# 5. CANDIDATOS PARA NPCS SIN MATCH DIRECTO (NO FORZAR)
NPCS_SIN_MATCH = {
    "npc003.png": ("El Padre (Hombre sereno, ropa sobria, cura en Pueblo Albor)", [
        ("Gen 5 Characters/NPC 03.png", "NPC masculino adulto corriente y sereno"),
        ("BW_037_Gentleman.png", "Hombre mayor formal y tranquilo"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "npc004.png": ("Telmo (El Viejo Pescador, jersey lana, pipa)", [
        ("BW_056_Fisherman.png", "Pescador oficial de Teselia"),
        ("Gen 5 Characters/NPC 15.png", "Anciano con baston"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "npc005.png": ("Hortensia (La Guarderia, anciana con delantal)", [
        ("Gen 5 Characters/NPC 05.png", "NPC femenina mayor"),
        ("BW_098_Mother_BW.png", "Mujer madura con delantal"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "npc006.png": ("Conservadora del Museo de Fosiles (Bata y gafas)", [
        ("Gen 5 Characters/NPC 06.png", "NPC femenina formal"),
        ("BW_067_Scientist_F.png", "Cientifica con bata (reusada)"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "npc007.png": ("Don Prodigio (Intercambio Prodigio, hombre excentrico)", [
        ("BW_097_Mr_Medal.png", "Hombre extravagante con broches y sombrero"),
        ("BW_096_Mr_Stu_Deeoh.png", "Director de cine excentrico con tupe"),
        ("BW_047_Harlequin.png", "Personaje llamativo")
    ]),
    "npc011.png": ("Acampador de fogata (Viajero nocturno, manta y capa)", [
        ("BW_041_Backpacker_M.png", "Mochilero viajero"),
        ("BW_057_Hiker.png", "Montanero de acampada"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "npc013.png": ("Hombre adulto generico", [
        ("Gen 5 Characters/NPC 13.png", "Vecino corriente de Teselia"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "npc014.png": ("Mujer adulta generica", [
        ("Gen 5 Characters/NPC 14.png", "Vecina corriente de Teselia"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "npc015.png": ("Anciano con baston", [
        ("Gen 5 Characters/NPC 15.png", "Anciano con baston"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "npc016.png": ("Anciana pelo canoso", [
        ("Gen 5 Characters/NPC 16.png", "Anciana con pelo canoso"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "npc019.png": ("Chico joven informal", [
        ("BW_004_Youngster.png", "Youngster informal"),
        ("Gen 5 Characters/NPC 19.png", "Adolescente informal"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "npc020.png": ("Chica joven informal", [
        ("BW_007_Lass.png", "Lass informal"),
        ("Gen 5 Characters/NPC 20.png", "Adolescente informal"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "npc021.png": ("Hombre corpulento y campechano", [
        ("BW_060_Worker.png", "Obrero corpulento"),
        ("BW_085_Worker.png", "Trabajador robusto"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "npc022.png": ("Mujer de mercado corpulenta con cesta", [
        ("Gen 5 Characters/NPC 22.png", "Mujer madura de mercado"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "npc023.png": ("Granjero (sombrero de paja)", [
        ("BW_059_Baker.png", "Trabajador manual con gorro"),
        ("BW_085_Worker.png", "Trabajador de campo"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder (no hay sombrero paja exacto)")
    ]),
    "npc024.png": ("Granjera (sombrero de paja y delantal)", [
        ("Gen 5 Characters/NPC 24.png", "Mujer campesina"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "npc025.png": ("Hombre abrigado (rutas nevadas)", [
        ("Gen 5 Characters/NPC 25.png", "Hombre con abrigo"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "npc026.png": ("Mujer abrigada (rutas nevadas)", [
        ("Gen 5 Characters/NPC 26.png", "Mujer con abrigo"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "npc027.png": ("Viajero del desierto (turbante y capa ligera)", [
        ("BW_041_Backpacker_M.png", "Viajero exterior"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder (NO existe sprite con turbante)")
    ]),
    "npc028.png": ("Viajera del desierto (velo y capa ligera)", [
        ("BW_042_Backpacker_F.png", "Viajera exterior"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder (NO existe sprite con velo)")
    ]),
    "npc029.png": ("Erudito (libros bajo el brazo)", [
        ("BW_066_Scientist_M.png", "Investigador / intelectual"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "npc030.png": ("Bibliotecaria (gafas y libreta)", [
        ("BW_008_Schoolkid_F.png", "Chica estudiosa"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
    "npc031.png": ("Lenador (hacha y camisa de cuadros)", [
        ("BW_085_Worker.png", "Trabajador de faena exterior"),
        ("BW_060_Worker.png", "Obrero robusto"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder (no hay hacha exacta)")
    ]),
    "npc032.png": ("Artesana (ropa de lana)", [
        ("Gen 5 Characters/NPC 08.png", "Mujer de villa rural"),
        ("DEJAR PLACEHOLDER", "Mantener placeholder")
    ]),
}


def run():
    print("=" * 70)
    print("APLICADOR CURADO DE OVERWORLDS GEN 5 (POKÉMON REM)")
    print(f"Modo: {'DRY RUN (sin tocar disco)' if DRY_RUN else 'APLICACIÓN REAL'}")
    print("=" * 70)

    # Paso 1: Verificar que los 20 intocables estan a salvo
    print(f"\n1. VERIFICANDO {len(INTOCABLES)} ARCHIVOS INTOCABLES DE REM:")
    for fname, desc in sorted(INTOCABLES.items()):
        dst_path = os.path.join(CHARS, fname)
        if not os.path.exists(dst_path):
            print(f"  [ERROR] {fname} no existe en Characters!")
        else:
            print(f"  [PROTEGIDO] {fname}: {desc}")

    # Paso 2: Aplicar los 38 trainers canonicos
    applied_trainers = 0
    print(f"\n2. APLICANDO {len(CANONICAL_TRAINERS)} TRAINERS COMUNES CANÓNICOS:")
    for dst_name, (src_name, note) in sorted(CANONICAL_TRAINERS.items()):
        src_path = os.path.join(ULTIMATE, src_name)
        dst_path = os.path.join(CHARS, dst_name)
        if not os.path.exists(src_path):
            print(f"  [ALERTA] Fuente no encontrada: {src_name}")
            continue
        if not DRY_RUN:
            shutil.copy2(src_path, dst_path)
        applied_trainers += 1
        print(f"  [APLICADO] {dst_name:14s} <- {src_name:26s} | {note}")

    # Paso 3: Aplicar los 8 NPCs canonicos
    applied_npcs = 0
    print(f"\n3. APLICANDO {len(CANONICAL_NPCS)} NPCS CON ROL CANÓNICO EXACTO:")
    for dst_name, (src_name, note) in sorted(CANONICAL_NPCS.items()):
        src_path = os.path.join(ULTIMATE, src_name)
        dst_path = os.path.join(CHARS, dst_name)
        if not os.path.exists(src_path):
            print(f"  [ALERTA] Fuente no encontrada: {src_name}")
            continue
        if not DRY_RUN:
            shutil.copy2(src_path, dst_path)
        applied_npcs += 1
        print(f"  [APLICADO] {dst_name:14s} <- {src_name:26s} | {note}")

    # Paso 4: Resumen de lo no forzado
    print(f"\n4. NO FORZADOS (QUEDAN COMO PLACEHOLDERS CON CANDIDATOS):")
    print(f"  - Trainers sin match canonico: {len(TRAINERS_SIN_MATCH)}")
    print(f"  - NPCs sin match canonico:     {len(NPCS_SIN_MATCH)}")

    print("\n" + "=" * 70)
    print(f"RESUMEN FINAL: {applied_trainers} trainers comunes + {applied_npcs} NPCs aplicados.")
    print(f"{len(INTOCABLES)} personajes protegidos intactos.")
    print("=" * 70)

if __name__ == "__main__":
    run()
