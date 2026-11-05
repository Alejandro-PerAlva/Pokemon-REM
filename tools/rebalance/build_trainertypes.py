#!/usr/bin/env python3
"""Genera PBS/trainertypes.txt (24 fijos + 72 comunes = 96), los placeholders
Graphics/Characters/trainerXXX.png que falten y los audios placeholder de los
24 primeros puestos. Fuente unica de la lista: TYPES (abajo).

Uso: python3 tools/rebalance/build_trainertypes.py   (desde la raiz del proyecto)
No sobrescribe PNG existentes (trainer000.png) ni audios existentes.
"""
import math, os, struct, wave, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# --- Audio: grupo -> (BGM, VictoryME) -------------------------------------
A_RIVAL = ("Combate Rival", "")
A_LEADER = ("Combate Lider", "Victoria Lider")
A_ELITE = ("Combate Alto Mando", "Victoria Liga")
A_CHAMP = ("Combate Campeona", "Victoria Liga")
A_RECRUIT = ("Combate Recluta Morfeo", "")
A_GENERAL = ("Combate General Morfeo", "")
A_BOSS = ("Combate Lider Morfeo", "")
N = ("", "")

# (simbolo, nombre ES, dinero base, genero, audio, grupo/nota)
FIXED = [
    ("PLAYER_M", "Entrenador", 60, "Male", N, "Personaje jugable M"),
    ("PLAYER_F", "Entrenadora", 60, "Female", N, "Personaje jugable F"),
    ("RIVAL_M", "Rival", 36, "Male", A_RIVAL, "Rival: Lucian"),
    ("RIVAL_F", "Rival", 36, "Female", A_RIVAL, "Rival: Guiomar"),
    ("PROFESSOR", "Profesor", 100, "Male", N, "Profesor Ambrosio"),
    ("LEADER_1", "Lider", 40, "Female", A_LEADER, "Gimnasio 1: Matilde (Normal)"),
    ("LEADER_2", "Lider", 50, "Male", A_LEADER, "Gimnasio 2: Ismael (Agua)"),
    ("LEADER_3", "Lider", 60, "Male", A_LEADER, "Gimnasio 3: Argos (Acero)"),
    ("LEADER_4", "Lider", 70, "Male", A_LEADER, "Gimnasio 4: Genzo (Lucha)"),
    ("LEADER_5", "Lider", 80, "Male", A_LEADER, "Gimnasio 5: Fausto (Roca)"),
    ("LEADER_6", "Lider", 90, "Female", A_LEADER, "Gimnasio 6: Hildegarda (Planta)"),
    ("LEADER_7", "Lider", 100, "Female", A_LEADER, "Gimnasio 7: Isolda (Hielo)"),
    ("LEADER_8", "Lider", 110, "Male", A_LEADER, "Gimnasio 8: Baltasar (Fuego)"),
    ("ELITE_1", "Alto Mando", 120, "Male", A_ELITE, "Alto Mando 1: Nicodemo (Roca/Hada)"),
    ("ELITE_2", "Alto Mando", 120, "Female", A_ELITE, "Alto Mando 2: Oriana (Hielo/Siniestro)"),
    ("ELITE_3", "Alto Mando", 120, "Male", A_ELITE, "Alto Mando 3: Anteo (Fuego/Tierra)"),
    ("ELITE_4", "Alto Mando", 120, "Female", A_ELITE, "Alto Mando 4: Leucotea (Agua/Fantasma)"),
    ("CHAMPION", "Campeona", 150, "Female", A_CHAMP, "Campeona: Rolanda Altamira (Dragon/Volador)"),
    ("MORFEO_RECRUIT_M", "Recluta Morfeo", 16, "Male", A_RECRUIT, "Recluta M del Equipo Morfeo"),
    ("MORFEO_RECRUIT_F", "Recluta Morfeo", 16, "Female", A_RECRUIT, "Recluta F del Equipo Morfeo"),
    ("MORFEO_GENERAL_M", "General", 100, "Male", A_GENERAL, "El General: Alarico Montenegro"),
    ("MORFEO_GENERAL_F", "General", 100, "Female", A_GENERAL, "La General: Zenobia Montenegro"),
    ("MORFEO_SUBCAPTAIN", "Subcapitana", 100, "Female", A_GENERAL, "Subcapitana: Nerea"),
    ("MORFEO_LEADER", "Lider Supremo", 150, "Male", A_BOSS, "Lider del Equipo Morfeo: Eliseo"),
]
# El PBS usa acentos; el dict mapea el nombre sin tilde a su forma correcta.
ACCENTS = {"Lider": "Líder", "Lider Supremo": "Líder Supremo"}

COMMON = [  # simbolo, nombre, dinero, genero, nota (tipos / bioma)
    ("YOUNGSTER", "Joven", 16, "Male", "Normal; pradera/pueblo; Acto I"),
    ("LASS", "Chica", 16, "Female", "Normal; pradera/pueblo; Acto I"),
    ("SCHOOLBOY", "Colegial", 16, "Male", "Normal/Bicho/Psiquico; ciudad"),
    ("SCHOOLGIRL", "Colegiala", 16, "Female", "Normal/Bicho/Psiquico; ciudad"),
    ("CAMPER", "Campista", 16, "Male", "Normal/Planta/Bicho; bosque/granja"),
    ("PICNICKER", "Excursionista", 16, "Female", "Normal/Planta/Bicho; bosque/granja"),
    ("BUGCATCHER", "Cazabichos", 16, "Male", "Bicho; bosque temprano"),
    ("BIRDKEEPER", "Cazapájaros", 32, "Male", "Volador; montana/pradera"),
    ("POKEFAN_M", "Pokéfan", 32, "Male", "Normal/Hada; pueblo/reserva"),
    ("POKEFAN_F", "Pokéfan", 32, "Female", "Normal/Hada; pueblo/reserva"),
    ("BACKPACKER_M", "Mochilero", 32, "Male", "Normal/Roca/Planta; rutas largas"),
    ("BACKPACKER_F", "Mochilera", 32, "Female", "Normal/Roca/Planta; rutas largas"),
    ("HIKER", "Montañero", 32, "Male", "Roca/Tierra/Lucha; cueva/montana"),
    ("SWIMMER_M", "Nadador", 16, "Male", "Agua; costas y lagos"),
    ("SWIMMER_F", "Nadadora", 16, "Female", "Agua; costas y lagos"),
    ("FISHERMAN", "Pescador", 32, "Male", "Agua; muelles/orillas"),
    ("SAILOR", "Marinero", 32, "Male", "Agua/Lucha; puertos, islas"),
    ("SCUBADIVER", "Buceador", 32, "Male", "Agua; gruta Azurita, rutas marinas"),
    ("TUBER_M", "Playero", 4, "Male", "Agua; playa"),
    ("TUBER_F", "Playera", 4, "Female", "Agua; playa"),
    ("BLACKBELT", "Karateka", 32, "Male", "Lucha; calzada/montana"),
    ("CRUSHGIRL", "Luchadora", 24, "Female", "Lucha; calzada/montana"),
    ("SCIENTIST", "Científico", 48, "Male", "Electrico/Acero/Veneno; industrial"),
    ("ENGINEER", "Ingeniero", 48, "Male", "Electrico/Acero; industrial"),
    ("WORKER", "Obrero", 32, "Male", "Acero/Tierra; central y minas"),
    ("SUPERNERD", "Friki", 48, "Male", "Electrico/Veneno/Psiquico; ruinas"),
    ("GUITARIST", "Guitarrista", 32, "Male", "Electrico/Normal/Siniestro; ciudad/playa"),
    ("ROCKER", "Rockero", 24, "Male", "Electrico/Siniestro/Fuego; ciudad"),
    ("PSYCHIC_M", "Psíquico", 32, "Male", "Psiquico/Fantasma; templo/cristal"),
    ("PSYCHIC_F", "Psíquica", 32, "Female", "Psiquico/Fantasma; templo/cristal"),
    ("MEDIUM", "Médium", 32, "Female", "Fantasma/Psiquico; ruinas"),
    ("HEXMANIAC", "Bruja", 32, "Female", "Fantasma/Psiquico/Siniestro; bosque, isla"),
    ("SKIER_M", "Esquiador", 32, "Male", "Hielo; nieve"),
    ("SKIER_F", "Esquiadora", 32, "Female", "Hielo; nieve"),
    ("TAMER", "Domador", 40, "Male", "Normal/Siniestro/Lucha; desierto/reserva"),
    ("DRAGONTAMER", "Domadragón", 60, "Male", "Dragon; final del juego"),
    ("RUINMANIAC", "Arqueólogo", 48, "Male", "Tierra/Roca/Psiquico; ruinas, desierto"),
    ("POKEMANIAC", "Poké Maniaco", 64, "Male", "Normal/Roca/Veneno; cueva/pantano"),
    ("JUGGLER", "Malabarista", 32, "Male", "Fantasma/Psiquico; puente/templo"),
    ("BURGLAR", "Ladrón", 88, "Male", "Siniestro/Veneno; ruinas/cueva"),
    ("GAMBLER", "Apostador", 72, "Male", "Normal/Siniestro; ciudad"),
    ("KINDLER", "Escupefuego", 32, "Male", "Fuego; volcan"),
    ("GENTLEMAN", "Caballero", 72, "Male", "Normal/Hada/Psiquico; ciudad"),
    ("LADY", "Dama", 160, "Female", "Normal/Hada/Psiquico; ciudad"),
    ("BEAUTY", "Bella", 56, "Female", "Normal/Agua/Hada; playa"),
    ("AROMALADY", "Chica Aroma", 32, "Female", "Planta/Veneno/Hada; bosque/pantano"),
    ("KIMONOGIRL", "Chica Kimono", 48, "Female", "Fantasma/Psiquico/Hada; templo"),
    ("PARASOLLADY", "Dama Parasol", 40, "Female", "Planta/Hada; pradera/reserva"),
    ("BREEDER_M", "Criador", 48, "Male", "Normal/Hada; granja/pueblo"),
    ("BREEDER_F", "Criadora", 48, "Female", "Normal/Hada; granja/pueblo"),
    ("COOLTRAINER_M", "Entre. Guay", 60, "Male", "Mixto; calzada/ciudad"),
    ("COOLTRAINER_F", "Entre. Guay", 60, "Female", "Mixto; calzada/ciudad"),
    ("VETERAN_M", "Veterano", 72, "Male", "Mixto; recta final"),
    ("VETERAN_F", "Veterana", 72, "Female", "Mixto; recta final"),
    ("DOCTOR", "Doctor", 48, "Male", "Normal/Hada/Psiquico; ciudad"),
    ("NURSE", "Enfermera", 48, "Female", "Normal/Hada/Psiquico; ciudad"),
    ("SAGE", "Sabio", 48, "Male", "Psiquico/Fantasma; templo"),
    ("POKEMONRANGER", "Guardabosques", 60, "Male", "Planta/Bicho/Normal; bosque/reserva"),
    ("MAID", "Sirvienta", 32, "Female", "Fantasma/Normal; villas y ruinas"),
    ("GARDENER", "Jardinero", 32, "Male", "Planta/Bicho; jardines y reserva"),
    ("RANCHER", "Ganadero", 32, "Male", "Normal/Tierra; granja/estepa"),
    ("WAITER", "Camarero", 32, "Male", "Normal/Hada; ciudad/pueblo"),
    ("WAITRESS", "Camarera", 32, "Female", "Normal/Hada; ciudad/pueblo"),
    ("PAINTER", "Pintor", 16, "Male", "Normal/Psiquico/Hada; ciudad/reserva"),
    ("ROUGHNECK", "Matón", 40, "Male", "Siniestro/Lucha; ciudad, calzada"),
    ("PUNKGUY", "Gamberro", 24, "Male", "Siniestro/Veneno/Fuego; ciudad"),
    ("BUGMANIAC", "Bichómano", 48, "Male", "Bicho; bosque y ruinas, Acto II-III"),
    ("CHEF", "Cocinero", 48, "Male", "Fuego/Normal; ciudad industrial"),
    ("POLICEMAN", "Policía", 48, "Male", "Siniestro/Normal; ciudad, entorno Morfeo"),
    ("NINJABOY", "Ninja", 32, "Male", "Veneno/Siniestro/Bicho; ruinas y cuevas"),
    ("EXPERT", "Experto", 64, "Male", "Lucha/Psiquico; calzada, final del juego"),
    ("COLLECTOR", "Coleccionista", 64, "Male", "Dragon/Roca/Acero; ruinas, final del juego"),
]
ORDER = ['YOUNGSTER', 'LASS', 'SCHOOLBOY', 'SCHOOLGIRL', 'CAMPER', 'PICNICKER', 'BUGCATCHER', 'BIRDKEEPER', 'POKEFAN_M', 'POKEFAN_F', 'GARDENER', 'RANCHER', 'PARASOLLADY', 'BREEDER_M', 'BREEDER_F', 'BACKPACKER_M', 'BACKPACKER_F', 'HIKER', 'SWIMMER_M', 'SWIMMER_F', 'FISHERMAN', 'TUBER_M', 'TUBER_F', 'BEAUTY', 'SAILOR', 'SCUBADIVER', 'SCIENTIST', 'ENGINEER', 'WORKER', 'SUPERNERD', 'GUITARIST', 'ROCKER', 'DOCTOR', 'NURSE', 'RUINMANIAC', 'POKEMANIAC', 'AROMALADY', 'POKEMONRANGER', 'BUGMANIAC', 'SKIER_M', 'SKIER_F', 'JUGGLER', 'MAID', 'PSYCHIC_M', 'PSYCHIC_F', 'MEDIUM', 'HEXMANIAC', 'KIMONOGIRL', 'SAGE', 'PAINTER', 'WAITER', 'WAITRESS', 'CHEF', 'BLACKBELT', 'CRUSHGIRL', 'TAMER', 'BURGLAR', 'NINJABOY', 'GAMBLER', 'KINDLER', 'PUNKGUY', 'ROUGHNECK', 'POLICEMAN', 'GENTLEMAN', 'LADY', 'EXPERT', 'COOLTRAINER_M', 'COOLTRAINER_F', 'VETERAN_M', 'VETERAN_F', 'DRAGONTAMER', 'COLLECTOR']
COMMON.sort(key=lambda t: ORDER.index(t[0]))  # orden de progresion: Acto I -> final; sin dobles
assert len(FIXED) == 24 and len(COMMON) == 72 and len(COMMON) % 8 == 0
assert len({t[0] for t in FIXED + COMMON}) == 96

def acc(name):
    return ACCENTS.get(name, name)

ALL = []
for i, (sym, name, money, gen, audio, note) in enumerate(FIXED):
    ALL.append((i, sym, acc(name), money, gen, audio, note, "fixed"))
for j, (sym, name, money, gen, note) in enumerate(COMMON):
    ALL.append((24 + j, sym, name, money, gen, N, note, "common"))

# --- PBS ---------------------------------------------------------------------
def write_pbs():
    lines = ["﻿# Consulta la documentación de la wiki para aprender a modificar este archivo.",
             "# Generado por tools/rebalance/build_trainertypes.py: 24 fijos (000-023) + 64 comunes (024-087) = 88.",
             "# Formato: ID,Símbolo,Nombre,DineroBase,MúsicaCombate,MEVictoria,MEIntro,Género,Habilidad,CódigosHab"]
    for i, sym, name, money, gen, audio, note, kind in ALL:
        if i == 0: lines.append("# --- Fijos 000-023 ---")
        if i == 24: lines.append("# --- Comunes 024-095 (audio vacío = música por defecto del mapa) ---")
        if kind == "fixed": lines.append("# %s" % note)
        lines.append("%d,%s,%s,%d,%s,%s,,%s,," % (i, sym, name, money, audio[0], audio[1], gen))
    with open(os.path.join(ROOT, "PBS", "trainertypes.txt"), "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(lines) + "\r\n")

# --- PNG ---------------------------------------------------------------------
GROUP_COL = {"PLAYER": (90, 140, 200), "RIVAL": (210, 150, 60), "PROFESSOR": (120, 180, 120),
             "LEADER": (200, 90, 90), "ELITE": (160, 100, 200), "CHAMPION": (230, 200, 70),
             "MORFEO": (120, 60, 160)}

def col(sym):
    for k, c in GROUP_COL.items():
        if sym.startswith(k): return c
    return (90, 100, 120)

def font(sz):
    return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", sz)

def wrap(draw, text, f, width):
    words, out, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=f) <= width: cur = t
        else:
            if cur: out.append(cur)
            cur = w
    if cur: out.append(cur)
    return out

def make_png(path, i, sym, name):
    S = 180
    im = Image.new("RGBA", (S, S), (14, 16, 24, 255))
    d = ImageDraw.Draw(im)
    c = col(sym)
    d.rectangle([0, 0, S - 1, S - 1], outline=c + (255,), width=3)
    d.rectangle([3, 3, S - 4, 26], fill=c + (255,))
    d.text((S // 2, 15), "trainer%03d" % i, font=font(15), fill=(10, 10, 16), anchor="mm")
    d.text((S // 2, 44), sym, font=font(11), fill=(170, 176, 196), anchor="mm")
    y = 68
    f = font(20)
    for ln in wrap(d, name.upper(), f, S - 16)[:3]:
        d.text((S // 2, y), ln, font=f, fill=(238, 238, 244), anchor="mm")
        y += 24
    d.text((S // 2, S - 14), "PLACEHOLDER · ONIRIA NOIR", font=font(8), fill=(110, 116, 140), anchor="mm")
    im.save(path)

# --- Overworld placeholder: hoja 256x256 = 4x4 fotogramas de 64 px (abajo, izq, der, arriba) ---
def make_char_png(path, label, color):
    im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = font(11)
    for row in range(4):          # direccion: 0 abajo, 1 izquierda, 2 derecha, 3 arriba
        for c in range(4):        # 4 fotogramas de la animacion de paso
            x, y = c * 64, row * 64
            bob = 2 if c % 2 else 0
            d.rounded_rectangle([x + 20, y + 30 - bob, x + 44, y + 54], 6, fill=(26, 30, 44, 255), outline=color + (255,), width=2)
            d.ellipse([x + 22, y + 8 - bob, x + 42, y + 28 - bob], fill=(38, 44, 64, 255), outline=color + (255,), width=2)
            cx, cy = x + 32, y + 18 - bob
            tri = {0: [(cx - 4, cy), (cx + 4, cy), (cx, cy + 5)], 1: [(cx - 6, cy), (cx, cy - 4), (cx, cy + 4)],
                   2: [(cx + 6, cy), (cx, cy - 4), (cx, cy + 4)], 3: [(cx - 4, cy + 3), (cx + 4, cy + 3), (cx, cy - 3)]}[row]
            d.polygon(tri, fill=color + (255,))
            d.text((x + 32, y + 42 - bob), label, font=f, fill=(238, 238, 244), anchor="mm")
    im.save(path)

# --- Audio placeholder (WAV 16-bit mono 22.05 kHz, tono muy bajo, bucle limpio) --
def make_wav(path, freq, secs):
    rate = 22050
    n = int(rate * secs)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        fr = bytearray()
        cyc = max(1, round(freq * secs))  # numero entero de ciclos -> bucle sin clic
        for k in range(n):
            fr += struct.pack("<h", int(1500 * math.sin(2 * math.pi * cyc * k / n)))
        w.writeframes(bytes(fr))

def main():
    write_pbs()
    chars = os.path.join(ROOT, "Graphics", "Characters")
    made, kept = [], []
    for i, sym, name, money, gen, audio, note, kind in ALL:
        p = os.path.join(chars, "trainer%03d.png" % i)
        if os.path.exists(p) and not (kind == 'common' and '--regen-commons' in sys.argv): kept.append(p); continue
        make_png(p, i, sym, name); made.append(p)
    regen = "--regen-commons" in sys.argv
    ch_made = []
    for i, sym, name, money, gen, audio, note, kind in ALL:   # overworld del entrenador
        p = os.path.join(chars, "trchar%03d.png" % i)
        if os.path.exists(p) and not (kind == "common" and regen): continue
        make_char_png(p, "%03d" % i, col(sym)); ch_made.append(p)
    npc_made = []
    for n in range(1, 33):                                    # 32 NPC sin nombre (3 digitos: el motor usa %03d)
        p = os.path.join(chars, "npc%03d.png" % n)
        if os.path.exists(p): continue
        make_char_png(p, "N%02d" % n, (150, 160, 180)); npc_made.append(p)
    print("trchar nuevos: %d | npc nuevos: %d" % (len(ch_made), len(npc_made)))
    audio_made = []
    for k, (bgm, me) in enumerate([A_RIVAL, A_LEADER, A_ELITE, A_CHAMP, A_RECRUIT, A_GENERAL, A_BOSS]):
        p = os.path.join(ROOT, "Audio", "BGM", bgm + ".wav")
        if not any(os.path.exists(os.path.join(ROOT, "Audio", "BGM", bgm + e)) for e in (".wav", ".ogg", ".mid", ".mp3")):
            make_wav(p, 110 + 22 * k, 4.0); audio_made.append(p)
    for me in ("Victoria Lider", "Victoria Liga"):
        p = os.path.join(ROOT, "Audio", "ME", me + ".wav")
        if not any(os.path.exists(os.path.join(ROOT, "Audio", "ME", me + e)) for e in (".wav", ".ogg", ".mid", ".mp3")):
            make_wav(p, 330 if me.endswith("Lider") else 392, 2.5); audio_made.append(p)
    print("PBS escrito: %d tipos" % len(ALL))
    print("PNG nuevos: %d | respetados: %s" % (len(made), [os.path.basename(x) for x in kept]))
    print("Audio nuevo: %s" % [os.path.relpath(x, ROOT) for x in audio_made])

if __name__ == "__main__":
    main()
