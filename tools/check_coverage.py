import os

# Verificacion exacta: 35 fondos requeridos vs lo que existe en Berilo y Realidea

r_dir = 'Graphics/Battleback_Candidates'
b_dir = 'Graphics/Battleback_Candidates/Berilo'

r_files = [f.lower() for f in os.listdir(r_dir)]
b_files = [f.lower() for f in os.listdir(b_dir)]
all_files = set(r_files + b_files)

required_bb = {
    # EXTERIORES Y RUTAS (12)
    "BB_Ruta_Pradera": ["battlebgfield.png", "battlebgruta3.png", "battlebgruta5.png"],
    "BB_Ruta_Bosque": ["battlebgbosque.png", "battlebgforest.png"],
    "BB_Ruta_Montana": ["battlebgcordillera.png", "battlebgmountain.png"],
    "BB_Ruta_Nieve": ["battlebgfieldnieve.png", "battlebgnieve.png", "battlebgsnow.png"],
    "BB_Ruta_Mar": ["battlebgmar_pixelart.png", "battlebgwater.png"],
    "BB_Playa_Costa": ["battlebgplaya.png", "battlebgcosta.png"],
    "BB_Desierto_Estepa": ["battlebgdesierto.png"],
    "BB_Cienaga_Pantano": ["battlebgpantano.png"],
    "BB_Granja_Cultivos": ["battlebggranero.png"],
    "BB_Puente_Colosal": ["battlebgpuente.png"],
    "BB_Bambu_Oriental": ["battlebgbambu.png"],
    "BB_Lago_Aguas": ["anil_water_celeste_bg.png", "battlebgwater.png"],

    # CUEVAS Y SUBTERRANEOS (6)
    "BB_Cueva_Roca": ["battlebgcueva.png", "battlebgcueva2.png", "battlebgcave.png"],
    "BB_Cueva_Volcan": ["battlebgvolcan.png"],
    "BB_Cueva_Hielo": ["battlebgcuevahielo.png", "battlebgcuevahielo2.png"],
    "BB_Cueva_Cristal_Azul": ["battlebgcrystal.png", "battlebghialina.png"], # CANDIDATO A GENERAR?
    "BB_Cueva_Cristal_Rosa": ["battlebgcrystalpink.png"], # CANDIDATO A GENERAR?
    "BB_Cueva_Submarina": ["battlebgsubmarino.png", "battlebgunderwater.png"],

    # LUGARES ESPECIALES (6)
    "BB_Isla_Suenio": ["battlebgotonyo.png"],
    "BB_Isla_Pesadilla": ["battlebgnegro.png", "battlebgmetis.png"], # CANDIDATO A GENERAR?
    "BB_Ruinas_Ancestrales": ["battlebgruina.png", "ruinas.png"],
    "BB_Templo_Sagrario": ["battlebgtemploazelf.png", "battlebgtemplomesprit.png"],
    "BB_Central_Industrial": ["battlebgcentral.png", "battlebgcentralint.png"],
    "BB_Altar_Marino_Legendario": ["battlebgsara.png"],

    # INTERIORES Y GIMNASIOS (11)
    "BB_Interior_Edificios": ["battlebgindoor.png", "battlebgipoke.png", "battlebghotel.png"],
    "BB_Gimnasio_1_Normal": ["battlebgacademia.png", "battlebgclase.png"], # GIMNASIO 1 (Matilde - Academia Normal): FALTA!
    "BB_Gimnasio_2_Agua": ["battlebgpiscina.png"],
    "BB_Gimnasio_3_Acero": ["battlebghangar.png", "battlebgtaller.png"], # GIMNASIO 3 (Greta - Hangar Naval): FALTA!
    "BB_Gimnasio_4_Lucha": ["battlebgbaile.png", "battlebgkiritsu.png"], # Dojo tradicional
    "BB_Gimnasio_5_Roca": ["battlebgcasino.png", "battlebgfosil.png"], # GIMNASIO 5 (Fausto - Roca/Casino/Fósiles): FALTA!
    "BB_Gimnasio_6_Planta": ["battlebginvernadero.png", "battlebgindoorinv.png"], # Realidea tiene battlebgIndoorinv.png!
    "BB_Gimnasio_7_Hielo": ["battlebgcuevahielo.png", "battlebgnatasha.png"], # Natasha era lider de hielo en Realidea?
    "BB_Gimnasio_8_Fuego": ["battlebgbea.png", "battlebgedward.png", "battlebgvolcan.png"], # Bea/Edward
    "BB_Liga_AltoMando": ["battlebgelitea.png", "battlebgeliteb.png", "battlebgelitec.png", "battlebgelited.png"],
    "BB_Liga_Campeon": ["battlebgchampion.png", "battlebgaster.png"]
}

print("=== REVISIÓN DE COBERTURA ===")
missing = []
present = []

for name, candidates in required_bb.items():
    found = [c for c in candidates if c in all_files]
    if found:
        present.append((name, found))
    else:
        missing.append(name)

print(f"\nYa cubiertos con Pixel Art real existente: {len(present)} / {len(required_bb)}")
for name, found in present:
    print(f"  [OK] {name} -> {found[0]}")

print(f"\nFaltan (CANDIDATOS REALES A GENERAR): {len(missing)} / {len(required_bb)}")
for m in missing:
    print(f"  [PENDIENTE] {m}")
