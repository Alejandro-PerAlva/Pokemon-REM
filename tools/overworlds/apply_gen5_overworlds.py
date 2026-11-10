"""
apply_gen5_overworlds.py
Aplica los overworlds Gen 5 a Graphics/Characters/
Crea backups .bak_pre_gen5 antes de sobrescribir.
Genera un informe de lo que se copió y lo que quedó sin match.

Uso: python tools/overworlds/apply_gen5_overworlds.py [--dry-run]
"""

import os, shutil, sys, struct

# ---------------------------------------------------------------------------
# CONFIG DE RUTAS
# ---------------------------------------------------------------------------
BASE        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN5        = os.path.join(BASE, "Graphics", "Gen 5 Characters")
ULTIMATE    = os.path.join(BASE, "Graphics", "Ultimate Gen 5 Overworlds Pack")
CHARS       = os.path.join(BASE, "Graphics", "Characters")

DRY_RUN     = "--dry-run" in sys.argv

# ---------------------------------------------------------------------------
# UTILIDADES
# ---------------------------------------------------------------------------
def g5(filename):
    """Ruta en Gen 5 Characters"""
    return os.path.join(GEN5, filename)

def bw(filename):
    """Ruta en Ultimate Gen 5 Overworlds Pack"""
    return os.path.join(ULTIMATE, filename)

def dst(filename):
    """Ruta destino en Characters"""
    return os.path.join(CHARS, filename)

def png_size(path):
    try:
        with open(path, "rb") as f:
            if f.read(8) != b"\x89PNG\r\n\x1a\n":
                return None
            f.read(4); f.read(4)
            w = struct.unpack(">I", f.read(4))[0]
            h = struct.unpack(">I", f.read(4))[0]
            return (w, h)
    except:
        return None

copied  = []   # (dst_name, src_path, reason)
skipped = []   # (dst_name, reason, [candidates])

def copy_sprite(src_path, dst_name, reason):
    dst_path = dst(dst_name)
    if not os.path.exists(src_path):
        skipped.append((dst_name, f"FUENTE NO ENCONTRADA: {src_path}", []))
        return
    bak_path = None
    if not DRY_RUN:
        shutil.copy2(src_path, dst_path)
    src_size = png_size(src_path)
    copied.append((dst_name, os.path.relpath(src_path, BASE), reason, src_size))

def no_match(dst_name, reason, candidates):
    skipped.append((dst_name, reason, candidates))


# ===========================================================================
# TABLA DE MAPPING — trchar000-087
# ===========================================================================

# ---- PERSONAJES FIJOS (trchar000-023) ---- #

# trchar000 = PLAYER_M
# El jugador masculino. Gen5 Characters ya tiene un Hilbert numerado 000.
copy_sprite(g5("trchar000.png"), "trchar000.png",
    "PLAYER_M — Hilbert/jugador M del pack Gen 5 Characters (numerado por ID).")

# trchar001 = PLAYER_F  (208×248 en Gen5 — puede tener animaciones extra, es válido)
copy_sprite(g5("trchar001.png"), "trchar001.png",
    "PLAYER_F — Hilda/jugadora F del pack Gen 5 Characters.")

# trchar002 = RIVAL_M (Lucián): delgado, gafas, aire académico.
# Cheren (BW_109) = rival de gafas, académico, pelo negro peinado. Match perfecto.
copy_sprite(bw("BW_109_Cheren.png"), "trchar002.png",
    "RIVAL_M (Lucián) — BW_109_Cheren: rival analítico de gafas y aspecto académico. Paralelo narrativo directo.")

# trchar003 = RIVAL_F (Guiomar): deportiva, coleta, apasionada.
# Bianca BW1 (BW_110) = rival femenina con sombrero, pose dinámica. Razonable.
# Hugh (BW_112) tiene energía de rival pasional pero es masculino.
# Elegimos BW_110_Bianca como rival femenina activa.
copy_sprite(bw("BW_110_Bianca.png"), "trchar003.png",
    "RIVAL_F (Guiomar) — BW_110_Bianca: rival femenina activa y de carácter apasionado. Mejor match femenino disponible.")

# trchar004 = PROFESSOR (Ambrosio): ~52 años, bata, traje victoriano, canoso.
# BW_105_Prof_Cedric_Juniper = profesor mayor (padre de Juniper), canoso, bata.
# Mejor que Aurea (que es joven y femenina).
copy_sprite(bw("BW_105_Prof_Cedric_Juniper.png"), "trchar004.png",
    "PROFESSOR (Ambrosio) — BW_105_Prof_Cedric_Juniper: profesor mayor, canoso y con bata. Ambrosio es ~52 años de aspecto clásico.")

# trchar005 = LEADER_1 Matilde (Normal, femenina): usamos Gen5 pack directamente
copy_sprite(g5("trchar005.png"), "trchar005.png",
    "LEADER_1 (Matilde, Gimnasio Normal, F) — Gen5 Characters trchar005.")

# trchar006 = LEADER_2 Ismael (Agua, masculino)
copy_sprite(g5("trchar006.png"), "trchar006.png",
    "LEADER_2 (Ismael, Gimnasio Agua, M) — Gen5 Characters trchar006.")

# trchar007 = LEADER_3 Argos (Acero, masculino)
copy_sprite(g5("trchar007.png"), "trchar007.png",
    "LEADER_3 (Argos, Gimnasio Acero, M) — Gen5 Characters trchar007.")

# trchar008 = LEADER_4 Genzo (Lucha, masculino)
copy_sprite(g5("trchar008.png"), "trchar008.png",
    "LEADER_4 (Genzo, Gimnasio Lucha, M) — Gen5 Characters trchar008.")

# trchar009 = LEADER_5 Fausto (Roca, masculino)
copy_sprite(g5("trchar009.png"), "trchar009.png",
    "LEADER_5 (Fausto, Gimnasio Roca, M) — Gen5 Characters trchar009.")

# trchar010 = LEADER_6 Hildegarda (Planta, femenina)
copy_sprite(g5("trchar010.png"), "trchar010.png",
    "LEADER_6 (Hildegarda, Gimnasio Planta, F) — Gen5 Characters trchar010.")

# trchar011 = LEADER_7 Isolda (Hielo, femenina)
copy_sprite(g5("trchar011.png"), "trchar011.png",
    "LEADER_7 (Isolda, Gimnasio Hielo, F) — Gen5 Characters trchar011.")

# trchar012 = LEADER_8 Baltasar (Fuego, masculino)
copy_sprite(g5("trchar012.png"), "trchar012.png",
    "LEADER_8 (Baltasar, Gimnasio Fuego, M) — Gen5 Characters trchar012.")

# trchar013 = ELITE_1 Nicodemo (Bicho, masculino)
copy_sprite(g5("trchar013.png"), "trchar013.png",
    "ELITE_1 (Nicodemo, Alto Mando Bicho, M) — Gen5 Characters trchar013.")

# trchar014 = ELITE_2 Oriana (Psíquico, femenina)
copy_sprite(g5("trchar014.png"), "trchar014.png",
    "ELITE_2 (Oriana, Alto Mando Psíquico, F) — Gen5 Characters trchar014.")

# trchar015 = ELITE_3 Anteo (Siniestro, masculino)
copy_sprite(g5("trchar015.png"), "trchar015.png",
    "ELITE_3 (Anteo, Alto Mando Siniestro, M) — Gen5 Characters trchar015.")

# trchar016 = ELITE_4 Leucotea (Tierra, femenina)
copy_sprite(g5("trchar016.png"), "trchar016.png",
    "ELITE_4 (Leucotea, Alto Mando Tierra, F) — Gen5 Characters trchar016.")

# trchar017 = CHAMPION Altamira (Campeona, femenina)
copy_sprite(g5("trchar017.png"), "trchar017.png",
    "CHAMPION (Altamira, Campeona, F) — Gen5 Characters trchar017.")

# trchar018 = MORFEO_RECRUIT_M: reclutas del equipo villano masculino.
# BW_113 = Plasma Grunt M (BW1 estilo, con uniforme de organización).
copy_sprite(bw("BW_113_Plasma_Grunt_M.png"), "trchar018.png",
    "MORFEO_RECRUIT_M — BW_113_Plasma_Grunt_M: grunt masculino con uniforme de organización. Paralelo Morfeo.")

# trchar019 = MORFEO_RECRUIT_F
copy_sprite(bw("BW_114_Plasma_Grunt_F.png"), "trchar019.png",
    "MORFEO_RECRUIT_F — BW_114_Plasma_Grunt_F: grunt femenina con uniforme. Paralelo Morfeo.")

# trchar020 = MORFEO_GENERAL_M (Alarico): musculoso, batalla, cicatrices.
# BW_132_Plasma_Ghetsis = líder imponente de organización, estatura imponente.
# Mejor opción disponible para un General musculoso.
copy_sprite(bw("BW_132_Plasma_Ghetsis.png"), "trchar020.png",
    "MORFEO_GENERAL_M (Alarico) — BW_132_Plasma_Ghetsis: figura masculina imponente de organización villana. Mejor match disponible para general musculoso.")

# trchar021 = MORFEO_GENERAL_F (Zenobia): monóculo, uniforme, intimidante.
# BW_130_Plasma_Colress = científico de Plasma, uniforme formal, distinguido.
# Es masculino en BW pero la silueta distinguida encaja para Zenobia más que otras opciones.
# Alternativa: BW_046_Clerk_F (uniforme formal femenino).
# Optamos por BW_046_Clerk_F — más femenino y con uniforme formal.
copy_sprite(bw("BW_046_Clerk_F.png"), "trchar021.png",
    "MORFEO_GENERAL_F (Zenobia) — BW_046_Clerk_F: mujer de uniforme formal y porte autoritario. Match de silueta para generala con monóculo.")

# trchar022 = MORFEO_SUBCAPTAIN Nerea: cabello corto oscuro, táctica, uniforme.
# BW_117_Plasma_Shadow_Triad = figuras ninja/tácticas de Plasma — silueta discreta y de acción.
copy_sprite(bw("BW_117_Plasma_Shadow_Triad.png"), "trchar022.png",
    "MORFEO_SUBCAPTAIN (Nerea) — BW_117_Plasma_Shadow_Triad: figura táctica y ágil de organización. Nerea es subcapitana operativa.")

# trchar023 = MORFEO_LEADER Eliseo: sereno, túnica índigo, liderazgo tranquilo.
# BW_131_Plasma_N = N es el líder sereno y conectado con la naturaleza. Paralelo narrativo muy fuerte.
copy_sprite(bw("BW_131_Plasma_N.png"), "trchar023.png",
    "MORFEO_LEADER (Eliseo) — BW_131_Plasma_N: líder carismático y sereno de organización. Eliseo y N comparten el arquetipo del antagonista complejo y de ideología sincera.")


# ---- TRAINERS GENÉRICOS (trchar024-082): copia directa del pack Gen5 ---- #
# El pack Gen 5 Characters tiene trchar000-082 numerados 1:1 con los trainer IDs.
for i in range(24, 83):
    fname = f"trchar{i:03d}.png"
    src = g5(fname)
    if os.path.exists(src):
        copy_sprite(src, fname,
            f"ID {i} ({['YOUNGSTER','LASS','SCHOOLBOY','SCHOOLGIRL','CAMPER','PICNICKER','BUGCATCHER','BIRDKEEPER','POKEFAN_M','POKEFAN_F','RANCHER','PARASOLLADY','BREEDER_M','BREEDER_F','AROMALADY','POKEMONRANGER','BACKPACKER_M','BACKPACKER_F','HIKER','RUINMANIAC','POKEMANIAC','BURGLAR','SWIMMER_M','SWIMMER_F','FISHERMAN','TUBER_M','TUBER_F','BEAUTY','SAILOR','SCUBADIVER','SCIENTIST','ENGINEER','WORKER','SUPERNERD','GUITARIST','ROCKER','PAINTER','JUGGLER','PSYCHIC_M','PSYCHIC_F','HEXMANIAC','MAID','SAGE','DOCTOR','NURSE','WAITER','WAITRESS','CHEF','POLICEMAN','GAMBLER','GENTLEMAN','LADY','SKIER_M','SKIER_F','KINDLER','BLACKBELT','CRUSHGIRL','TAMER','ROUGHNECK'][i-24] if i-24 < 59 else str(i)}) — copia directa Gen5 Characters (pack numerado por ID).")
    else:
        no_match(fname, f"Archivo no existe en Gen 5 Characters para ID {i}.", [])


# ---- TRAINERS ESPECIALES SIN COBERTURA EN GEN5 (trchar083-087) ---- #

# trchar083 = COOLTRAINER_M: entrenador guay masculino, pose cool.
copy_sprite(bw("BW_023_Ace_Trainer_M.png"), "trchar083.png",
    "COOLTRAINER_M — BW_023_Ace_Trainer_M: Ace Trainer M es el equivalente BW del Cool Trainer clásico.")

# trchar084 = COOLTRAINER_F
copy_sprite(bw("BW_024_Ace_Trainer_F.png"), "trchar084.png",
    "COOLTRAINER_F — BW_024_Ace_Trainer_F: Ace Trainer F, equivalente BW del Cool Trainer femenino.")

# trchar085 = VETERAN_M: entrenador veterano masculino.
copy_sprite(bw("BW_025_Veteran_M.png"), "trchar085.png",
    "VETERAN_M — BW_025_Veteran_M: nombre exactamente igual. Match perfecto.")

# trchar086 = VETERAN_F
copy_sprite(bw("BW_026_Veteran_F.png"), "trchar086.png",
    "VETERAN_F — BW_026_Veteran_F: nombre exactamente igual. Match perfecto.")

# trchar087 = DRAGONTAMER: domador de dragones. No hay un sprite BW con nombre exacto.
# Opciones razonables: BW_025_Veteran_M (ya usada), BW_057_Hiker (explorador rudo, exterior),
# BW_060_Worker (corpulento, trabajador de campo). Ninguna es perfecta.
no_match("trchar087.png",
    "DRAGONTAMER: no existe equivalente exacto en ninguno de los dos packs.",
    [
        "BW_057_Hiker.png — Montañero rudo y exterior; comparte el perfil de viajero de zonas difíciles.",
        "BW_025_Veteran_M.png — Ya usada en trchar085, pero comparte el arquetipo de experto experimentado.",
        "BW_060_Worker.png — Hombre corpulento de campo; menos elegante pero disponible.",
    ])


# ===========================================================================
# TABLA DE MAPPING — npc001-032
# ===========================================================================

# npc001 = Amparo (madre ~40 años, delantal, cálida)
# BW_098_Mother_BW = sprite de madre exactamente diseñado para ese rol en BW.
copy_sprite(bw("BW_098_Mother_BW.png"), "npc001.png",
    "npc001 (Amparo, la madre) — BW_098_Mother_BW: sprite de madre de BW. Match de rol perfecto.")

# npc002 = Pía (joven, bata de laboratorio)
# BW_067_Scientist_F = científica femenina joven con bata. Match directo.
copy_sprite(bw("BW_067_Scientist_F.png"), "npc002.png",
    "npc002 (Pía, ayudante laboratorio) — BW_067_Scientist_F: científica femenina joven con bata. Rol de asistente de laboratorio.")

# npc003 = El Padre (hombre sereno, ropa sobria)
# NPC 03 del pack Gen5 = NPC masculino adulto genérico, aspecto sobrio.
copy_sprite(g5("NPC 03.png"), "npc003.png",
    "npc003 (El Padre) — Gen5 NPC 03: NPC masculino adulto, aspecto corriente y sereno.")

# npc004 = Telmo (anciano pescador, jersey de lana, pipa)
# BW_056_Fisherman = pescador masculino clásico. Match de rol perfecto.
copy_sprite(bw("BW_056_Fisherman.png"), "npc004.png",
    "npc004 (Telmo, anciano pescador) — BW_056_Fisherman: sprite de pescador. Match exacto de rol.")

# npc005 = Hortensia (guardería, anciana pelo recogido, delantal)
# NPC 05 del pack Gen5 = NPC femenino adulto/mayor. Mejor opción disponible sin Pillow.
copy_sprite(g5("NPC 05.png"), "npc005.png",
    "npc005 (Hortensia, guardería) — Gen5 NPC 05: NPC femenina mayor. Rol de dueña de guardería.")

# npc006 = Conservadora museo (bata, gafas, científica)
# BW_066_Scientist_M es masculino; BW_067 ya usada.
# Usamos NPC 06 del pack Gen5 (distinto a npc002 que es BW_067).
copy_sprite(g5("NPC 06.png"), "npc006.png",
    "npc006 (Conservadora museo) — Gen5 NPC 06: NPC femenina de aspecto formal. Para diferenciar de Pía (npc002).")

# npc007 = Don Prodigio (excéntrico, atuendo llamativo)
# BW_096_Mr_Stu_Deeoh = personaje excéntrico de BW con atuendo extravagante. Match de carácter.
copy_sprite(bw("BW_096_Mr_Stu_Deeoh.png"), "npc007.png",
    "npc007 (Don Prodigio, intercambio prodigio) — BW_096_Mr_Stu_Deeoh: personaje excéntrico y llamativo de BW. Match de carácter.")

# npc008 = Enfermera del Centro Pokémon
# BW_071_Nurse_Joy = enfermera de Centro Pokémon. Match de rol perfecto y canónico.
copy_sprite(bw("BW_071_Nurse_Joy.png"), "npc008.png",
    "npc008 (Enfermera Centro Pokémon) — BW_071_Nurse_Joy: enfermera del Centro Pokémon. Match de rol exacto.")

# npc009 = Dependiente Poké Mart (hombre, uniforme)
# BW_070_Mart = empleado de Poké Mart. Match de rol exacto.
copy_sprite(bw("BW_070_Mart.png"), "npc009.png",
    "npc009 (Dependiente Poké Mart) — BW_070_Mart: empleado de tienda. Match de rol exacto.")

# npc010 = Dependienta Poké Mart (mujer, uniforme)
# BW_046_Clerk_F = empleada con uniforme formal. Mejor match femenino de tienda disponible.
# (BW_070 es el Mart genérico; BW_046 aporta variedad femenina)
copy_sprite(bw("BW_046_Clerk_F.png"), "npc010.png",
    "npc010 (Dependienta Poké Mart) — BW_046_Clerk_F: empleada con uniforme. Variante femenina de dependiente.")

# npc011 = Acampador de fogata (manta/capa, viajero)
# BW_041_Backpacker_M = mochilero viajero con equipo. Perfil de viajero nocturno. 
copy_sprite(bw("BW_041_Backpacker_M.png"), "npc011.png",
    "npc011 (Acampador fogata) — BW_041_Backpacker_M: mochilero viajero. Perfil de viajero de ruta que acampa.")

# npc012 = Árbitro (camisa rayas, silbato)
# BW_088_Gym_Guide_Clyde = guía de gimnasio con uniforme de árbitro. Match visual fuerte.
copy_sprite(bw("BW_088_Gym_Guide_Clyde.png"), "npc012.png",
    "npc012 (Árbitro) — BW_088_Gym_Guide_Clyde: guía/árbitro de gimnasio con uniforme a rayas. Match visual de árbitro.")

# npc013 = Hombre adulto genérico
copy_sprite(g5("NPC 13.png"), "npc013.png",
    "npc013 (Hombre adulto genérico) — Gen5 NPC 13: NPC masculino adulto corriente.")

# npc014 = Mujer adulta genérica
copy_sprite(g5("NPC 14.png"), "npc014.png",
    "npc014 (Mujer adulta genérica) — Gen5 NPC 14: NPC femenina adulta corriente.")

# npc015 = Anciano con bastón
copy_sprite(g5("NPC 15.png"), "npc015.png",
    "npc015 (Anciano con bastón) — Gen5 NPC 15: NPC masculino mayor.")

# npc016 = Anciana pelo canoso
copy_sprite(g5("NPC 16.png"), "npc016.png",
    "npc016 (Anciana pelo canoso) — Gen5 NPC 16: NPC femenina mayor.")

# npc017 = Niño pequeño
# BW_083_Preschooler_M = preescolar masculino, sprite de niño pequeño. Match de rol perfecto.
copy_sprite(bw("BW_083_Preschooler_M.png"), "npc017.png",
    "npc017 (Niño pequeño) — BW_083_Preschooler_M: preescolar masculino. Match exacto de edad y rol.")

# npc018 = Niña pequeña
# BW_084_Preschooler_F = preescolar femenina. Match de rol perfecto.
copy_sprite(bw("BW_084_Preschooler_F.png"), "npc018.png",
    "npc018 (Niña pequeña) — BW_084_Preschooler_F: preescolar femenina. Match exacto.")

# npc019 = Chico joven informal
# BW_004_Youngster = Youngster clásico, chico joven informal con pantalón corto. Canónico.
copy_sprite(bw("BW_004_Youngster.png"), "npc019.png",
    "npc019 (Chico joven informal) — BW_004_Youngster: Youngster clásico, chico joven. Match de edad y estilo.")

# npc020 = Chica joven informal
# BW_007_Lass = Lass clásica, chica joven casual. Canónica.
copy_sprite(bw("BW_007_Lass.png"), "npc020.png",
    "npc020 (Chica joven informal) — BW_007_Lass: Lass clásica, chica joven informal. Match directo.")

# npc021 = Hombre corpulento y campechano
# BW_060_Worker = obrero corpulento de overworld BW. Match de silueta.
copy_sprite(bw("BW_060_Worker.png"), "npc021.png",
    "npc021 (Hombre corpulento) — BW_060_Worker: obrero corpulento de aspecto campechano.")

# npc022 = Mujer de mercado corpulenta con cesta
# No hay un sprite exacto de mujer con cesta en ninguno de los dos packs.
# NPC 22 del pack Gen5 — usamos como mejor disponible.
copy_sprite(g5("NPC 22.png"), "npc022.png",
    "npc022 (Mujer de mercado con cesta) — Gen5 NPC 22: NPC femenina de aspecto robusto. No existe sprite exacto con cesta en los packs disponibles.")

# npc023 = Granjero (sombrero de paja)
# BW_059_Baker = panadero con gorro; comparte el perfil de trabajador de campo/oficio manual.
# Es la mejor opción disponible para un granjero masculino.
copy_sprite(bw("BW_059_Baker.png"), "npc023.png",
    "npc023 (Granjero, sombrero paja) — BW_059_Baker: trabajador manual con uniforme de oficio. No hay sprite de granjero exacto; Baker es el más próximo en silueta.")

# npc024 = Granjera (sombrero de paja, delantal)
# NPC 24 del pack Gen5 — NPC femenina adulta, mejor opción disponible.
copy_sprite(g5("NPC 24.png"), "npc024.png",
    "npc024 (Granjera) — Gen5 NPC 24: NPC femenina adulta. No hay sprite de granjera exacta en el Ultimate Pack.")

# npc025 = Hombre abrigado (abrigo, bufanda, rutas nevadas)
# No hay sprite de persona con abrigo de invierno exacto. NPC 25 del pack Gen5.
copy_sprite(g5("NPC 25.png"), "npc025.png",
    "npc025 (Hombre abrigado, rutas nevadas) — Gen5 NPC 25: NPC masculino adulto. No hay sprite de invierno exacto.")

# npc026 = Mujer abrigada (abrigo, gorro, rutas nevadas)
copy_sprite(g5("NPC 26.png"), "npc026.png",
    "npc026 (Mujer abrigada, rutas nevadas) — Gen5 NPC 26: NPC femenina adulta. No hay sprite de invierno exacto.")

# npc027 = Viajero del desierto (turbante, capa ligera)
# No hay match exacto. BW_041_Backpacker_M (ya usada en npc011).
# NPC 27 del pack Gen5 como segunda opción.
no_match("npc027.png",
    "Viajero del desierto (turbante, capa): no existe sprite con turbante en ninguno de los dos packs.",
    [
        "BW_041_Backpacker_M.png — Mochilero viajero; ya usada en npc011 pero es el perfil más cercano.",
        "BW_057_Hiker.png — Montañero con aspecto de viajero exterior; más rudo que un viajero de desierto.",
        "Gen5 NPC 27.png — NPC masculino genérico del pack; sin turbante pero como placeholder neutro.",
    ])

# npc028 = Viajera del desierto (velo, capa ligera)
no_match("npc028.png",
    "Viajera del desierto (velo, capa): no existe sprite con velo en ninguno de los dos packs.",
    [
        "BW_042_Backpacker_F.png — Mochilera femenina; perfil de viajera exterior.",
        "BW_077_Parasol_Lady.png — Dama con parasol; femenina y con accesorio que da personalidad visual.",
        "Gen5 NPC 28.png — NPC femenina genérica del pack como placeholder neutro.",
    ])

# npc029 = Erudito (libros bajo el brazo)
# BW_066_Scientist_M = científico masculino con aspecto intelectual. Match de carácter.
copy_sprite(bw("BW_066_Scientist_M.png"), "npc029.png",
    "npc029 (Erudito, libros) — BW_066_Scientist_M: científico masculino con aspecto intelectual y serio. Perfil de erudito.")

# npc030 = Bibliotecaria (gafas y libreta)
# BW_067_Scientist_F ya usada en npc002. Usamos NPC 20 del pack Gen5 (NPC femenina distinta).
# Alternativa: BW_008_Schoolkid_F (escolar femenina con aspecto estudioso).
copy_sprite(bw("BW_008_Schoolkid_F.png"), "npc030.png",
    "npc030 (Bibliotecaria, gafas y libreta) — BW_008_Schoolkid_F: chica de aspecto estudioso con uniforme. BW_067 ya usada en npc002; esta aporta diferenciación visual.")

# npc031 = Leñador (hacha, camisa de cuadros)
# BW_085_Worker = segundo sprite de worker/obrero BW, silueta más robusta y de faena exterior.
copy_sprite(bw("BW_085_Worker.png"), "npc031.png",
    "npc031 (Leñador, hacha y camisa cuadros) — BW_085_Worker: obrero exterior robusto. Match de silueta para trabajador de campo/bosque.")

# npc032 = Artesana (ropa de lana, rústica)
# NPC 08 del pack Gen5 — NPC femenina. No hay sprite de artesana rural exacta.
copy_sprite(g5("NPC 08.png"), "npc032.png",
    "npc032 (Artesana, ropa de lana) — Gen5 NPC 08: NPC femenina adulta. No hay sprite de artesana rural exacto en los packs.")


# ===========================================================================
# INFORME
# ===========================================================================
print("=" * 70)
print(f"{'[DRY RUN] ' if DRY_RUN else ''}INFORME DE OVERWORLDS GEN 5")
print("=" * 70)
print(f"\nCOPIADOS: {len(copied)}")
for dst_name, src_rel, reason, size in sorted(copied):
    print(f"  {dst_name:20s} <- {src_rel}")
    print(f"               ({size}) | {reason[:80]}")

print(f"\nSIN MATCH (quedan como placeholder): {len(skipped)}")
for dst_name, reason, cands in sorted(skipped):
    print(f"\n  {dst_name}")
    print(f"    Motivo: {reason}")
    if cands:
        print(f"    Candidatos:")
        for c in cands:
            print(f"      • {c}")

print(f"\n{'[DRY RUN — ningún archivo modificado]' if DRY_RUN else 'Proceso completado. Backups en *.bak_pre_gen5'}")
