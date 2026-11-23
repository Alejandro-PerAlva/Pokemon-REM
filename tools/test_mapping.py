import os

# Categorizacion de las 64 ubicaciones a fondos de combate

LOCATIONS_MAPPING = [
    # --- CIUDADES (8) ---
    ("CIUDAD_CALCEDONIA", "Ciudad Calceda", "Exterior: Urbana Calceda / Interior: Gimnasio 1 Normal (Academia)"),
    ("CIUDAD_CALAITA", "Ciudad Calaire", "Exterior: Costera Calaire / Interior: Gimnasio 2 Agua (Piscina)"),
    ("CIUDAD_MAGNETITA", "Ciudad Magno", "Exterior: Urbana Industrial / Interior: Gimnasio 3 Acero/Electrico (Hangar)"),
    ("CIUDAD_NEFRITA", "Ciudad Nefral", "Exterior: Bambu Oriental / Interior: Gimnasio 4 Lucha (Dojo)"),
    ("CIUDAD_REJALGAR", "Ciudad Rejalgar", "Exterior: Canon Adobe / Interior: Gimnasio 8 Fuego/Tierra (Forja)"),
    ("CIUDAD_AZABACHE", "Ciudad Azabache", "Exterior: Callejón Nocturno / Interior: Gimnasio 5 Siniestro (Club Urbano)"),
    ("CIUDAD_VENTURINA", "Ciudad Venturina", "Exterior: Jardin Ciudad / Interior: Gimnasio 6 Planta (Invernadero)"),
    ("CIUDAD_ALABASTRO", "Ciudad Alabastro", "Exterior: Nieve / Interior: Gimnasio 7 Hielo (Palacio Glaciar)"),

    # --- PUEBLOS Y NODOS (8) ---
    ("PUEBLO_ALBOR", "Pueblo Albor", "Exterior: Pradera Campo / Interior: Casas y Lab"),
    ("PUEBLO_HELIODORO", "Pueblo Heliar", "Exterior: Pradera Campo / Interior: Casas"),
    ("PUEBLO_PEDERNAL", "Pueblo Pedernal", "Exterior: Montana Rocosa / Interior: Casas"),
    ("PUEBLO_ESTEATITA", "Pueblo Estea", "Exterior: Estepa Arida / Interior: Casas"),
    ("PUEBLO_CASITERITA", "Pueblo Casitero", "Exterior: Cueva/Cantera / Interior: Casas"),
    ("PUEBLO_NACAR", "Pueblo Nacara", "Exterior: Playa Costa / Interior: Casas"),
    ("MESETA_CELESTITA", "Meseta Celeste", "Exterior: Calzada Corindon / Interior: Liga Alto Mando y Campeon"),
    ("MONTE_AZOGUE", "Monte Azogue", "Exterior: Pico Montana Sagrado / Interior: Santuario Final"),

    # --- LUGARES ESPECIALES (16) ---
    ("BOSQUE_DIOPTASA", "Bosque Dioptasa", "Bosque Frondoso con Bruma"),
    ("LAGO_AMATISTA", "Lago Amatista", "Lago de Aguas Cristalinas"),
    ("CENTRAL_FULGURITA", "Central Fulgor", "Central Fulgor Industrial"),
    ("RUINAS_ATACAMITA", "Ruinas Atacama", "Ruinas Atacamita Ancestrales"),
    ("TEMPLO_MOLDAVITA", "Templo Moldar", "Templo Sagrario Moldar"),
    ("VILLA_ADULARIA", "Villa Adular", "Villa Espectral / Bosque Nebuloso"),
    ("CASCADAS_TRAVERTINAS", "Cascadas Travertinas", "Cascadas y Rio de Montaña"),
    ("CIENAGA_LIMONITA", "Ciénaga Limonar", "Ciénaga Pantano Charcas"),
    ("DESIERTO_HALITA", "Desierto Halar", "Desierto Estepa Arida"),
    ("LADERA_PORFIDO", "Ladera Porfiral", "Ladera Rocosa Volcanica"),
    ("GRUTA_PIRITA", "Gruta Piral", "Gruta Piral Volcan (Lava/Magma)"),
    ("GRUTA_AZURITA", "Gruta Azur", "Gruta Azur Submarina (Abisal)"),
    ("GRUTA_LABRADORITA", "Gruta Labrador", "Gruta Labrador Hielo (Glaciar)"),
    ("GRUTA_HIALINA", "Gruta Hialina", "Gruta Hialina Cristales"),
    ("ISLA_OBSIDIANA", "Isla Pesadilla", "Isla Pesadilla Equipo Morfeo"),
    ("ISLA_OPALINA", "Isla Sueño", "Isla Sueño Otoño Mistico"),

    # --- RUTAS NORMALES (11) ---
    ("RUTA_01", "Ruta 1", "Pradera Campo (Paleta Suelo Primavera)"),
    ("RUTA_02", "Ruta 2", "Pradera Campo (Paleta Suelo Templado)"),
    ("RUTA_04", "Ruta 4", "Pradera Campo (Hacia Lago)"),
    ("RUTA_05", "Ruta 5", "Pradera Campo (Paleta Suelo Templado)"),
    ("RUTA_06", "Ruta 6", "Pradera Campo / Colinas"),
    ("RUTA_07", "Ruta 7", "Bosque Frondoso (Paleta Bosque)"),
    ("RUTA_08", "Ruta 8", "Bosque Frondoso (Paleta Bosque)"),
    ("RUTA_09", "Ruta 9", "Bosque Frondoso (Paleta Selva)"),
    ("RUTA_14", "Ruta 14", "Bosque Frondoso (Paleta Bosque)"),
    ("RUTA_15", "Ruta 15", "Humedal / Ribera Frondosa"),
    ("RUTA_16", "Ruta 16", "Bosque Frondoso (Paleta Selva)"),

    # --- RUTAS ESPECIALES (8) ---
    ("GRANJA_APATITA", "Granja Apato", "Campos de Cultivo y Granja"),
    ("PLAYA_SEPIOLITA", "Playa Sepiola", "Playa Litoral Costa"),
    ("ESTEPA_LATERITA", "Estepa Latera", "Desierto Estepa Arida"),
    ("SENDA_SERPENTINA", "Senda Serpentina", "Ciudad Nefral Bambu"),
    ("PUENTE_DOLOMITA", "Puente Dolomar", "Puente Dolomita Colosal"),
    ("ACANTILADOS_RODONITA", "Acantilados Rodal", "Acantilados Costa Rocosa"),
    ("RESERVA_PERIDOTO", "Reserva Peridoto", "Reserva Natural Protegida"),
    ("CALZADA_CORINDON", "Calzada Corindal", "Calzada Corindon Ceremonial"),

    # --- RUTAS DE MONTAÑA (5) ---
    ("RUTA_03", "Ruta 3", "Montaña Rocosa / Canon"),
    ("RUTA_10", "Ruta 10", "Montaña Rocosa / Cumbres"),
    ("RUTA_20", "Ruta 20", "Montaña Rocosa / Canon Adobe"),
    ("RUTA_21", "Ruta 21", "Montaña Rocosa / Paso Alto"),
    ("RUTA_22", "Ruta 22", "Montaña Rocosa / Desfiladero"),

    # --- RUTAS MARINAS (4) ---
    ("RUTA_12", "Ruta 12", "Mar Abierto"),
    ("RUTA_13", "Ruta 13", "Mar Abierto"),
    ("RUTA_23", "Ruta 23", "Mar Abierto / Bruma Crepuscular"),
    ("RUTA_24", "Ruta 24", "Mar Abierto / Noche Oscura"),

    # --- RUTAS NEVADAS (4) ---
    ("RUTA_11", "Ruta 11", "Nieve Alta Montaña (Pinar Nevado)"),
    ("RUTA_17", "Ruta 17", "Nieve Alta Montaña (Ventisca)"),
    ("RUTA_18", "Ruta 18", "Nieve Alta Montaña (Glaciar)"),
    ("RUTA_19", "Ruta 19", "Nieve Alta Montaña (Cumbre)")
]

print(f"Total ubicaciones mapeadas: {len(LOCATIONS_MAPPING)}")
