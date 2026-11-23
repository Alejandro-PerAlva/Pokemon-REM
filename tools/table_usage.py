import os

# Categorizacion de uso: Cuantas ubicaciones de las 64 usan cada fondo
bb_usage = {
    # EXTERIORES Y RUTAS
    "BB_Ruta_Pradera": {
        "tipo": "Troncal (Exteriores)",
        "locs": ["Ruta 1", "Ruta 2", "Ruta 4", "Ruta 5", "Ruta 6", "Pueblo Albor", "Pueblo Heliar", "Ciudad Calceda (exterior)"],
        "desc": "Pradera y campo abierto. Usa las 4 paletas de suelo de la chuleta (Primavera, Templado, Bosque, Selva) + Dia/Tarde/Noche."
    },
    "BB_Ruta_Bosque": {
        "tipo": "Troncal (Exteriores)",
        "locs": ["Bosque Dioptasa", "Ruta 7", "Ruta 8", "Ruta 9", "Ruta 14", "Ruta 16", "Reserva Peridoto", "Villa Adular (exterior)", "Ciudad Venturina (exterior)"],
        "desc": "Espesura forestal y robledales frondosos. Dia/Tarde/Noche."
    },
    "BB_Ruta_Montana": {
        "tipo": "Troncal (Exteriores)",
        "locs": ["Ruta 3", "Ruta 10", "Ruta 20", "Ruta 21", "Ruta 22", "Pueblo Pedernal", "Ciudad Rejalgar (exterior)", "Calzada Corindal", "Ladera Porfiral", "Meseta Celeste (exterior)", "Monte Azogue (exterior)"],
        "desc": "Desfiladeros de roca, riscos y puertos de alta montana. Dia/Tarde/Noche."
    },
    "BB_Ruta_Nieve": {
        "tipo": "Semi-Troncal (Zona Nieve)",
        "locs": ["Ruta 11", "Ruta 17", "Ruta 18", "Ruta 19", "Ciudad Alabastro (exterior)"],
        "desc": "Rutas alpinas nevadas, ventisca y pinares con escarcha. Dia/Tarde/Noche."
    },
    "BB_Ruta_Mar": {
        "tipo": "Semi-Troncal (Zona Marina)",
        "locs": ["Ruta 12", "Ruta 13", "Ruta 23", "Ruta 24"],
        "desc": "Mar abierto para navegacion y surf. Dia/Tarde/Noche."
    },
    "BB_Desierto_Estepa": {
        "tipo": "Semi-Troncal (Zona Arida)",
        "locs": ["Desierto Halar", "Estepa Latera", "Pueblo Estea"],
        "desc": "Dunas de arena y estepas aridas rojizas. Dia/Tarde/Noche."
    },
    "BB_Playa_Costa": {
        "tipo": "Semi-Troncal (Litoral)",
        "locs": ["Playa Sepiola", "Pueblo Nacara", "Acantilados Rodal", "Ciudad Calaire (exterior)"],
        "desc": "Litoral arenoso continuo sin pedestales. Dia/Tarde/Noche."
    },
    "BB_Cienaga_Pantano": {
        "tipo": "Semi-Troncal (Humedal)",
        "locs": ["Ciénaga Limonar", "Ruta 15"],
        "desc": "Aguas estancadas, lodo y eneas. Dia/Tarde/Noche."
    },
    "BB_Lago_Aguas": {
        "tipo": "Concreto / Tematico",
        "locs": ["Lago Amatista", "Cascadas Travertinas"],
        "desc": "Orillas de lago cristalino y cascadas sagradas."
    },
    "BB_Bambu_Oriental": {
        "tipo": "Concreto / Tematico",
        "locs": ["Senda Serpentina", "Ciudad Nefral (exterior)"],
        "desc": "Arboleda de bambu tradicional y camino empedrado."
    },
    "BB_Granja_Cultivos": {
        "tipo": "Puntual (1 Ubicacion)",
        "locs": ["Granja Apato"],
        "desc": "Campos de trigo, molino y cercas de madera rustica."
    },
    "BB_Puente_Colosal": {
        "tipo": "Puntual (1 Ubicacion)",
        "locs": ["Puente Dolomar"],
        "desc": "Gran puente de silleria sobre cañon profundo."
    },

    # CUEVAS Y SUBTERRANEOS
    "BB_Cueva_Roca": {
        "tipo": "Troncal (Cuevas Comunes)",
        "locs": ["Cuevas de Rutas 3, 10", "Pueblo Casitero (minas)", "Acantilados Rodal (interiores)", "Pasos cavernarios"],
        "desc": "Cueva natural de pizarra gris-azulada (tonos Cueva A)."
    },
    "BB_Cueva_Volcan": {
        "tipo": "Concreto / Especial",
        "locs": ["Gruta Piral", "Ladera Porfiral (interior)", "Ruta 20 (interior)"],
        "desc": "Caverna volcanica, basalto y fisuras de lava activa."
    },
    "BB_Cueva_Hielo": {
        "tipo": "Concreto / Especial",
        "locs": ["Gruta Labrador", "Ruta 19 (interior)"],
        "desc": "Caverna glaciar de hielo azul y estalactitas congeladas."
    },
    "BB_Cueva_Cristal_Azul": {
        "tipo": "Concreto / Especial",
        "locs": ["Gruta Hialina (zona exterior/celeste)"],
        "desc": "Geodas luminosas celestes y zafiros."
    },
    "BB_Cueva_Cristal_Rosa": {
        "tipo": "Concreto / Especial",
        "locs": ["Gruta Hialina (zona interior/profunda)"],
        "desc": "Amatistas purpuras y cuarzo rosa brillante."
    },
    "BB_Cueva_Submarina": {
        "tipo": "Concreto / Especial",
        "locs": ["Gruta Azur (Abisal)"],
        "desc": "Fondo oceanico profundo, corales y rayos de sol acuaticos."
    },

    # LUGARES ESPECIALES / CLIMAX
    "BB_Isla_Suenio": {
        "tipo": "Puntual (Legendario)",
        "locs": ["Isla Sueño (Cresselia)"],
        "desc": "Claro otoñal con hojas de arce doradas y aura magica."
    },
    "BB_Isla_Pesadilla": {
        "tipo": "Puntual (Legendario)",
        "locs": ["Isla Pesadilla (Darkrai)"],
        "desc": "Paisaje nocturno sombrio con niebla oscura y espinas de piedra."
    },
    "BB_Ruinas_Ancestrales": {
        "tipo": "Puntual (Lugar Especial)",
        "locs": ["Ruinas Atacama"],
        "desc": "Pilares caidos de arenisca y jeroglificos del desierto."
    },
    "BB_Templo_Sagrario": {
        "tipo": "Puntual (Lugar Especial)",
        "locs": ["Templo Moldar", "Monte Azogue (altar de la cumbre)"],
        "desc": "Santuario mitologico tallado en piedra con pebeteros de fuego."
    },
    "BB_Central_Industrial": {
        "tipo": "Puntual (Lugar Especial)",
        "locs": ["Central Fulgor", "Isla Pesadilla (laboratorios Morfeo)"],
        "desc": "Instalacion electrica pesada con rejillas metalicas y turbinas."
    },
    "BB_Altar_Marino_Legendario": {
        "tipo": "Puntual (Encuentro Mitico)",
        "locs": ["Encuentros misticos en altamar"],
        "desc": "Plataforma sagrada sobre el mar con bruma estelar."
    },

    # INTERIORES Y GIMNASIOS
    "BB_Interior_Edificios": {
        "tipo": "Troncal (Interiores Urbanos)",
        "locs": ["Casas de los 8 pueblos", "Tiendas Pokémon", "Centros Pokémon", "Edificios genericos"],
        "desc": "Suelo de tablones de madera pulida, estanterias y mostradores del tileset."
    },
    "BB_Gimnasio_1_Normal": {
        "tipo": "Puntual (Gimnasio 1)",
        "locs": ["Gimnasio Calceda (Matilde - Normal)"],
        "desc": "Aula de academia de combate con parquet deportivo y pizarra tactica."
    },
    "BB_Gimnasio_2_Agua": {
        "tipo": "Puntual (Gimnasio 2)",
        "locs": ["Gimnasio Calaire (Ismael - Agua)"],
        "desc": "Recinto olimpico con foso de agua turquesa y baldosas de piscina."
    },
    "BB_Gimnasio_3_Acero": {
        "tipo": "Puntual (Gimnasio 3)",
        "locs": ["Gimnasio Magno (Argos - Acero)"],
        "desc": "Hangar/taller naval con chapas de acero remachadas, chispas y herramientas."
    },
    "BB_Gimnasio_4_Lucha": {
        "tipo": "Puntual (Gimnasio 4)",
        "locs": ["Gimnasio Nefral (Genzo - Lucha)"],
        "desc": "Dojo tradicional oriental de tatami pulcro, madera de cedro y biombos."
    },
    "BB_Gimnasio_5_Roca": {
        "tipo": "Puntual (Gimnasio 5)",
        "locs": ["Gimnasio Azabache (Fausto - Roca/Fosiles)"],
        "desc": "Arena subterranea de rocas fosilizadas y estrado de casino/coleccionismo de lujo."
    },
    "BB_Gimnasio_6_Planta": {
        "tipo": "Puntual (Gimnasio 6)",
        "locs": ["Gimnasio Venturina (Hildegarda - Planta)"],
        "desc": "Gran invernadero botanico con suelo continuo de tierra y flora medicinal sin pedestales."
    },
    "BB_Gimnasio_7_Hielo": {
        "tipo": "Puntual (Gimnasio 7)",
        "locs": ["Gimnasio Alabastro (Isolda - Hielo)"],
        "desc": "Palacio gélido señorial con columnas de hielo tallado y suelo de escarcha."
    },
    "BB_Gimnasio_8_Fuego": {
        "tipo": "Puntual (Gimnasio 8)",
        "locs": ["Gimnasio Rejalgar (Beltrán - Fuego)"],
        "desc": "Forja y cocina termal con hornos incandescentes y suelo de losas refractarias."
    },
    "BB_Liga_AltoMando": {
        "tipo": "Puntual (Climax Liga)",
        "locs": ["Camaras de los 4 miembros del Alto Mando"],
        "desc": "Arena ceremonial de mármol blanco, detalles dorados y estandartes oficiales."
    },
    "BB_Liga_Campeon": {
        "tipo": "Puntual (Combate Final)",
        "locs": ["Sala del Campeon Roldan (Meseta Celeste)"],
        "desc": "Camara estelar del trono con suelo de obsidiana pulida y ventanal al horizonte."
    }
}

# Imprimir ordenado por tipo y conteo de ubicaciones
items = list(bb_usage.items())
items.sort(key=lambda x: (0 if "Troncal" in x[1]["tipo"] else 1 if "Semi-Troncal" in x[1]["tipo"] else 2 if "Concreto" in x[1]["tipo"] else 3, -len(x[1]["locs"])))

for name, data in items:
    print(f"{name:26} | {data['tipo']:28} | {len(data['locs']):2d} ubicaciones")
