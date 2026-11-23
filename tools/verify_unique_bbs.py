import os

# Base de datos de mapeo completo: 64 ubicaciones vs Fondos de Combate

LOCATIONS = [
    # CIUDADES (8)
    {"id": 1, "key": "CIUDAD_CALCEDONIA", "name": "Ciudad Calceda", "ext": "BB_Ruta_Pradera", "int": "BB_Gimnasio_1_Normal", "obs": "Combate de gimnasio en Academia (Normal). En calle: pradera urbana."},
    {"id": 2, "key": "CIUDAD_CALAITA", "name": "Ciudad Calaire", "ext": "BB_Playa_Costa", "int": "BB_Gimnasio_2_Agua", "obs": "Ciudad portuaria. Gimnasio de piscina olimpica."},
    {"id": 3, "key": "CIUDAD_MAGNETITA", "name": "Ciudad Magno", "ext": "BB_Central_Industrial", "int": "BB_Gimnasio_3_AceroElectrico", "obs": "Ciudad minera/industrial. Gimnasio hangar."},
    {"id": 4, "key": "CIUDAD_NEFRITA", "name": "Ciudad Nefral", "ext": "BB_Bambu_Oriental", "int": "BB_Gimnasio_4_Lucha", "obs": "Ciudad tradicional. Gimnasio dojo de lucha."},
    {"id": 5, "key": "CIUDAD_REJALGAR", "name": "Ciudad Rejalgar", "ext": "BB_Ruta_Montana", "int": "BB_Gimnasio_8_FuegoTierra", "obs": "Ciudad de canon adobe. Gimnasio forja volcanica."},
    {"id": 6, "key": "CIUDAD_AZABACHE", "name": "Ciudad Azabache", "ext": "BB_Gimnasio_5_Siniestro", "int": "BB_Gimnasio_5_Siniestro", "obs": "Ciudad nocturna de callejones y luces tenues."},
    {"id": 7, "key": "CIUDAD_VENTURINA", "name": "Ciudad Venturina", "ext": "BB_Ruta_Bosque", "int": "BB_Gimnasio_6_Planta", "obs": "Ciudad jardin. Gimnasio gran invernadero botanico."},
    {"id": 8, "key": "CIUDAD_ALABASTRO", "name": "Ciudad Alabastro", "ext": "BB_Ruta_Nieve", "int": "BB_Gimnasio_7_Hielo", "obs": "Ciudad de alta montana nevada. Gimnasio palacio glaciar."},

    # PUEBLOS Y NODOS (8)
    {"id": 9, "key": "PUEBLO_ALBOR", "name": "Pueblo Albor", "ext": "BB_Ruta_Pradera", "int": "BB_Interior_Edificios", "obs": "Pueblo inicial campestre."},
    {"id": 10, "key": "PUEBLO_HELIODORO", "name": "Pueblo Heliar", "ext": "BB_Ruta_Pradera", "int": "BB_Interior_Edificios", "obs": "Pueblo de llanura abierta soleada."},
    {"id": 11, "key": "PUEBLO_PEDERNAL", "name": "Pueblo Pedernal", "ext": "BB_Ruta_Montana", "int": "BB_Interior_Edificios", "obs": "Pueblo minero encajado en garganta de roca."},
    {"id": 12, "key": "PUEBLO_ESTEATITA", "name": "Pueblo Estea", "ext": "BB_Desierto_Estepa", "int": "BB_Interior_Edificios", "obs": "Pueblo oasis en meseta arida."},
    {"id": 13, "key": "PUEBLO_CASITERITA", "name": "Pueblo Casitero", "ext": "BB_Cueva_Roca", "int": "BB_Interior_Edificios", "obs": "Pueblo de canteras y fosiles."},
    {"id": 14, "key": "PUEBLO_NACAR", "name": "Pueblo Nacara", "ext": "BB_Playa_Costa", "int": "BB_Interior_Edificios", "obs": "Pueblo pesquero costero."},
    {"id": 15, "key": "MESETA_CELESTITA", "name": "Meseta Celeste", "ext": "BB_Ruta_Montana", "int": "BB_Liga_AltoMando", "obs": "Cumbre de la Liga. Interior: Alto Mando / Campeon."},
    {"id": 16, "key": "MONTE_AZOGUE", "name": "Monte Azogue", "ext": "BB_Ruta_Montana", "int": "BB_Templo_Sagrario", "obs": "Pico mas alto de Oniria. Cima sagrada."},

    # LUGARES ESPECIALES (16)
    {"id": 17, "key": "BOSQUE_DIOPTASA", "name": "Bosque Dioptasa", "ext": "BB_Ruta_Bosque", "int": "BB_Ruta_Bosque", "obs": "Bosque frondoso con niebla (Dominante 1)."},
    {"id": 18, "key": "LAGO_AMATISTA", "name": "Lago Amatista", "ext": "BB_Lago_Aguas", "int": "BB_Lago_Aguas", "obs": "Gran lago interior y orillas (Base Morfeo 1)."},
    {"id": 19, "key": "CENTRAL_FULGURITA", "name": "Central Fulgor", "ext": "BB_Central_Industrial", "int": "BB_Central_Industrial", "obs": "Interior y patio de central electrica."},
    {"id": 20, "key": "RUINAS_ATACAMITA", "name": "Ruinas Atacama", "ext": "BB_Ruinas_Ancestrales", "int": "BB_Ruinas_Ancestrales", "obs": "Ruinas de arenisca en el desierto."},
    {"id": 21, "key": "TEMPLO_MOLDAVITA", "name": "Templo Moldar", "ext": "BB_Templo_Sagrario", "int": "BB_Templo_Sagrario", "obs": "Santuario mitologico de piedra tallada."},
    {"id": 22, "key": "VILLA_ADULARIA", "name": "Villa Adular", "ext": "BB_Ruta_Bosque", "int": "BB_Interior_Edificios", "obs": "Villa fantasmal abandonada entre arboles."},
    {"id": 23, "key": "CASCADAS_TRAVERTINAS", "name": "Cascadas Travertinas", "ext": "BB_Lago_Aguas", "int": "BB_Lago_Aguas", "obs": "Saltos de agua cristalina y pozas de hada."},
    {"id": 24, "key": "CIENAGA_LIMONITA", "name": "Ciénaga Limonar", "ext": "BB_Cienaga_Pantano", "int": "BB_Cienaga_Pantano", "obs": "Humedal toxico con aguas oscuras y eneas."},
    {"id": 25, "key": "DESIERTO_HALITA", "name": "Desierto Halar", "ext": "BB_Desierto_Estepa", "int": "BB_Desierto_Estepa", "obs": "Dunas de arena y estepa arida."},
    {"id": 26, "key": "LADERA_PORFIDO", "name": "Ladera Porfiral", "ext": "BB_Ruta_Montana", "int": "BB_Cueva_Volcan", "obs": "Desfiladero rocoso volcanico y acceso a lava."},
    {"id": 27, "key": "GRUTA_PIRITA", "name": "Gruta Piral", "ext": "BB_Cueva_Volcan", "int": "BB_Cueva_Volcan", "obs": "Caverna volcanica de basalto y magma ardiente."},
    {"id": 28, "key": "GRUTA_AZURITA", "name": "Gruta Azur", "ext": "BB_Cueva_Submarina", "int": "BB_Cueva_Submarina", "obs": "Caverna marina abisal sumergida."},
    {"id": 29, "key": "GRUTA_LABRADORITA", "name": "Gruta Labrador", "ext": "BB_Cueva_Hielo", "int": "BB_Cueva_Hielo", "obs": "Cueva de hielo milenario con estalactitas."},
    {"id": 30, "key": "GRUTA_HIALINA", "name": "Gruta Hialina", "ext": "BB_Cueva_Cristal_Azul", "int": "BB_Cueva_Cristal_Rosa", "obs": "Caverna magica de geodas y cristales resplandecientes."},
    {"id": 31, "key": "ISLA_OBSIDIANA", "name": "Isla Pesadilla", "ext": "BB_Isla_Pesadilla", "int": "BB_Central_Industrial", "obs": "Fortaleza oscura de Morfeo y altar de Darkrai."},
    {"id": 32, "key": "ISLA_OPALINA", "name": "Isla Sueño", "ext": "BB_Isla_Suenio", "int": "BB_Isla_Suenio", "obs": "Isla de ensueño con hojas de arce otoñales (Cresselia)."},

    # RUTAS NORMALES (11)
    {"id": 33, "key": "RUTA_01", "name": "Ruta 1", "ext": "BB_Ruta_Pradera (Primavera)", "int": "Sin interiores", "obs": "Ruta inicial: pradera verde claro."},
    {"id": 34, "key": "RUTA_02", "name": "Ruta 2", "ext": "BB_Ruta_Pradera (Templado)", "int": "Sin interiores", "obs": "Ruta abierta hacia el Bosque Dioptasa."},
    {"id": 35, "key": "RUTA_04", "name": "Ruta 4", "ext": "BB_Ruta_Pradera (Templado)", "int": "Sin interiores", "obs": "Camino bordeando el lago."},
    {"id": 36, "key": "RUTA_05", "name": "Ruta 5", "ext": "BB_Ruta_Pradera (Templado)", "int": "Sin interiores", "obs": "Paso verde entre colinas."},
    {"id": 37, "key": "RUTA_06", "name": "Ruta 6", "ext": "BB_Ruta_Pradera (Templado)", "int": "Sin interiores", "obs": "Colinas abiertas estivales."},
    {"id": 38, "key": "RUTA_07", "name": "Ruta 7", "ext": "BB_Ruta_Bosque", "int": "Sin interiores", "obs": "Camino arbolado denso."},
    {"id": 39, "key": "RUTA_08", "name": "Ruta 8", "ext": "BB_Ruta_Bosque", "int": "Sin interiores", "obs": "Espesura de robles y maleza."},
    {"id": 40, "key": "RUTA_09", "name": "Ruta 9", "ext": "BB_Ruta_Bosque (Selva)", "int": "Sin interiores", "obs": "Vegetacion subtropical frondosa."},
    {"id": 41, "key": "RUTA_14", "name": "Ruta 14", "ext": "BB_Ruta_Bosque", "int": "Sin interiores", "obs": "Bosque templado de montana."},
    {"id": 42, "key": "RUTA_15", "name": "Ruta 15", "ext": "BB_Cienaga_Pantano", "int": "Sin interiores", "obs": "Riberas humedas y hierba palustre."},
    {"id": 43, "key": "RUTA_16", "name": "Ruta 16", "ext": "BB_Ruta_Bosque (Selva)", "int": "Sin interiores", "obs": "Senda en selva densa lluviosa."},

    # RUTAS ESPECIALES (8)
    {"id": 44, "key": "GRANJA_APATITA", "name": "Granja Apato", "ext": "BB_Granja_Cultivos", "int": "BB_Interior_Edificios", "obs": "Campos de trigo y establos rusticos."},
    {"id": 45, "key": "PLAYA_SEPIOLITA", "name": "Playa Sepiola", "ext": "BB_Playa_Costa", "int": "Sin interiores", "obs": "Playa de arena blanca y olas calmas."},
    {"id": 46, "key": "ESTEPA_LATERITA", "name": "Estepa Latera", "ext": "BB_Desierto_Estepa", "int": "Sin interiores", "obs": "Tierra arcillosa rojiza y matorral seco."},
    {"id": 47, "key": "SENDA_SERPENTINA", "name": "Senda Serpentina", "ext": "BB_Bambu_Oriental", "int": "Sin interiores", "obs": "Camino tradicional flanqueado por bambu."},
    {"id": 48, "key": "PUENTE_DOLOMITA", "name": "Puente Dolomar", "ext": "BB_Puente_Colosal", "int": "Sin interiores", "obs": "Puente colosal de piedra sobre el canon."},
    {"id": 49, "key": "ACANTILADOS_RODONITA", "name": "Acantilados Rodal", "ext": "BB_Playa_Costa", "int": "BB_Cueva_Roca", "obs": "Cornisa rocosa sobre el mar furioso."},
    {"id": 50, "key": "RESERVA_PERIDOTO", "name": "Reserva Peridoto", "ext": "BB_Ruta_Bosque", "int": "Sin interiores", "obs": "Parque natural protegido de flora intacta."},
    {"id": 51, "key": "CALZADA_CORINDON", "name": "Calzada Corindal", "ext": "BB_Ruta_Montana", "int": "Sin interiores", "obs": "Avenida monumental de losas hacia la Liga."},

    # RUTAS DE MONTAÑA (5)
    {"id": 52, "key": "RUTA_03", "name": "Ruta 3", "ext": "BB_Ruta_Montana", "int": "BB_Cueva_Roca", "obs": "Garganta rocosa con cuevas naturales."},
    {"id": 53, "key": "RUTA_10", "name": "Ruta 10", "ext": "BB_Ruta_Montana", "int": "BB_Cueva_Roca", "obs": "Paso de montana escarpado."},
    {"id": 54, "key": "RUTA_20", "name": "Ruta 20", "ext": "BB_Ruta_Montana", "int": "BB_Cueva_Volcan", "obs": "Canon de tierra y desfiladero calido."},
    {"id": 55, "key": "RUTA_21", "name": "Ruta 21", "ext": "BB_Ruta_Montana", "int": "Sin interiores", "obs": "Ruta de risco alto y viento."},
    {"id": 56, "key": "RUTA_22", "name": "Ruta 22", "ext": "BB_Ruta_Montana", "int": "Sin interiores", "obs": "Camino pedregoso agreste."},

    # RUTAS MARINAS (4)
    {"id": 57, "key": "RUTA_12", "name": "Ruta 12", "ext": "BB_Ruta_Mar", "int": "Sin interiores", "obs": "Mar abierto hacia el este."},
    {"id": 58, "key": "RUTA_13", "name": "Ruta 13", "ext": "BB_Ruta_Mar", "int": "Sin interiores", "obs": "Aguas profundas navegables."},
    {"id": 59, "key": "RUTA_23", "name": "Ruta 23", "ext": "BB_Ruta_Mar", "int": "Sin interiores", "obs": "Travesia marina neblinosa a Isla Sueño."},
    {"id": 60, "key": "RUTA_24", "name": "Ruta 24", "ext": "BB_Ruta_Mar", "int": "Sin interiores", "obs": "Travesia nocturna tormentosa a Isla Pesadilla."},

    # RUTAS NEVADAS (4)
    {"id": 61, "key": "RUTA_11", "name": "Ruta 11", "ext": "BB_Ruta_Nieve", "int": "Sin interiores", "obs": "Entrada a la zona helada con pinos con nieve."},
    {"id": 62, "key": "RUTA_17", "name": "Ruta 17", "ext": "BB_Ruta_Nieve", "int": "Sin interiores", "obs": "Camino de ventisca y neveros densos."},
    {"id": 63, "key": "RUTA_18", "name": "Ruta 18", "ext": "BB_Ruta_Nieve", "int": "Sin interiores", "obs": "Paso glaciar helado."},
    {"id": 64, "key": "RUTA_19", "name": "Ruta 19", "ext": "BB_Ruta_Nieve", "int": "BB_Cueva_Hielo", "obs": "Subida a la cumbre de Alabastro."}
]

# Recopilar todos los fondos unicos referenciados
unique_bbs = set()
for loc in LOCATIONS:
    unique_bbs.add(loc['ext'].split(' ')[0])
    if loc['int'] not in ['Sin interiores', 'BB_Interior_Edificios']:
        unique_bbs.add(loc['int'].split(' ')[0])
unique_bbs.add('BB_Interior_Edificios')
unique_bbs.add('BB_Liga_Campeon')
unique_bbs.add('BB_Altar_Marino_Legendario')

print(f"Total Fondos Base Unicos Requeridos: {len(unique_bbs)}")
for bb in sorted(unique_bbs):
    print(f" - {bb}")
