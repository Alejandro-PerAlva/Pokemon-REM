import os
import shutil

def shift_npcs():
    char_dir = "Graphics/Characters"
    backup_dir = "Graphics/Characters_backup_npc_shift"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup all current npc files
    for i in range(1, 33):
        fname = f"npc{i:03d}.png"
        src = os.path.join(char_dir, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(backup_dir, fname))
    print("Backup de sprites npc completado.")

    # Shift sprites from 24 down to 4 by +2
    # So npc024 -> npc026, npc023 -> npc025, ..., npc004 -> npc006
    for i in range(24, 3, -1):
        old_name = f"npc{i:03d}.png"
        new_name = f"npc{i+2:03d}.png"
        src = os.path.join(backup_dir, old_name)
        dst = os.path.join(char_dir, new_name)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Desplazado: {old_name} -> {new_name}")

    # Copy the two new gatehouse sprites
    male_src = r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795375143169_b5c8c054.png"
    female_src = r"C:/Users/apera/.gemini/antigravity/brain/28b48a32-a6fe-4d6a-9bad-08a2c99f1d48/.user_uploaded/media_1795375143168_2bbfff12.png"

    shutil.copy2(male_src, os.path.join(char_dir, "npc004.png"))
    print("Instalado npc004.png: Oficial de pasarutas (chico)")
    shutil.copy2(female_src, os.path.join(char_dir, "npc005.png"))
    print("Instalado npc005.png: Oficial de pasarutas (chica)")

    # Update PBS/rem_overworlds.txt
    overworlds_path = "PBS/rem_overworlds.txt"
    with open(overworlds_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Build new rem_overworlds.txt content
    header = """# Pokémon REM — CATÁLOGO DE OVERWORLDS (sprites de personajes). Documento de trabajo para Claude: no lo lee el juego ni el Codex.
# Lo rellena el DISEÑADOR: qué es cada sprite npcNNN (Graphics/Characters/npcNNN.png). Claude elige los NPC de los eventos SOLO entre los definidos aquí (y entre los trchar de entrenador, ver abajo); no inventa sprites ni los asigna a ojo.
# Campos por sección [npcNNN]: Name = lo que es (p. ej. Pescador, Anciana, Niño) · Description = descripción breve · Gender = Male/Female/Mixed.
# Sprites de ENTRENADOR como overworld: cualquier clase de trainertypes.txt tiene su trcharNNN (NNN = ID de la clase, 000-087) y puede usarse como NPC sin combate (un evento normal con ese gráfico y sin pbTrainerBattle). Para elegirlos, vale el nombre y la descripción de la clase en trainertypes.txt.
# Formato: texto plano en español (UTF-8 BOM, CRLF), secciones [npcNNN] y comentarios con «#».

# Reparto (32 slots):
# - npc001-014 = 14 IDENTIFICABLES (NPC con función o historia propia; 7 Male + 7 Female).
# - npc015-026 = 12 GENÉRICOS organizados por edad (2 Niños pequeños, 4 Jóvenes, 4 Adultos, 2 Ancianos).
# - npc027-032 = 6 SLOTS DE REPUESTO (libres para asignar en el futuro según necesidades).
# Las profesiones (marinero, pescador, montañero, policía, etc.) NO usan hueco npc: salen de los trcharNNN de entrenador.

[npc001]
Name = Enfermera del Centro Pokémon
Description = Mujer con uniforme de enfermera y cofia. Cura al equipo en los Centros Pokémon y atiende el PC.
Gender = Female

[npc002]
Name = Dependiente (Poké Mart)
Description = Hombre con uniforme y gorra de tienda. Atiende el mostrador de los Poké Mart y de las tiendas especiales.
Gender = Male

[npc003]
Name = Dependienta (Poké Mart)
Description = Mujer con uniforme y gorra de tienda. Atiende el mostrador de los Poké Mart y de las tiendas especiales.
Gender = Female

[npc004]
Name = Oficial de pasarutas (chico)
Description = Joven con uniforme azul y gorra de plato con visera roja. Atiende el mostrador de las casetas de control entre rutas y ciudades.
Gender = Male

[npc005]
Name = Oficial de pasarutas (chica)
Description = Joven con uniforme azul, sombrero de copa corta y falda rosa. Atiende el mostrador de las casetas de control entre rutas y ciudades.
Gender = Female

[npc006]
Name = Julián (el padre)
Description = Hombre de aspecto sereno y ropa sobria. Padre del protagonista; punto de curación del hogar en Pueblo Albor y encargado de mejorar el Saco de Dormir.
Gender = Male

[npc007]
Name = Amparo (la madre)
Description = Mujer de unos 40 años, delantal y gesto cálido. Madre del protagonista; punto de curación del hogar en Pueblo Albor y encargada de entregar y mejorar el Pokévial.
Gender = Female

[npc008]
Name = Pía (ayudante del Profesor)
Description = Mujer joven con bata de laboratorio y gafas. Atiende el laboratorio de Pueblo Albor y gestiona las misiones secundarias del expediente del Profesor.
Gender = Female

[npc009]
Name = Hortensia (la Guardería)
Description = Anciana de aspecto dulce con delantal de flores. Regenta la Guardería Pokémon en el camino a Ciudad Calceda.
Gender = Female

[npc010]
Name = Telmo (el Viejo Pescador)
Description = Anciano con impermeable y barba blanca. Entrega la Caña Vieja y enseña a pescar en los muelles de Ciudad Calaire.
Gender = Male

[npc011]
Name = Ámbar (la Conservadora del Museo)
Description = Mujer de mediana edad con chaleco de expedición y lupa. Atiende el museo de Pueblo Casitero y revive los fósiles prehistóricos.
Gender = Female

[npc012]
Name = Silvestre (el Árbitro)
Description = Hombre atlético con uniforme a rayas y silbato. Árbitro oficial de la Liga presente a la entrada de cada gimnasio para dar consejos y agua fresca.
Gender = Male

[npc013]
Name = Don Prodigio (Intercambio Prodigio)
Description = Hombre excéntrico con chistera y capa de colores. Gestiona los intercambios sorpresa y funciones de intercambio en puntos clave.
Gender = Male

[npc014]
Name = Acampador de fogata
Description = Montañero con mochila grande y chaqueta térmica. Descansa junto a las fogatas de ruta, comparte leyendas locales y permite descansar.
Gender = Male

[npc015]
Name = Niño pequeño
Description = Niño de corta edad con peto vaquero y gorra hacia atrás. Corretea por plazas y parques.
Gender = Male

[npc016]
Name = Niña pequeña
Description = Niña de corta edad con vestido sencillo y lazo en el pelo. Juega en las calles de los pueblos.
Gender = Female

[npc017]
Name = Chico escolar
Description = Joven estudiante con uniforme de academia o mochila escolar. Frecuenta Ciudad Calceda y bibliotecas.
Gender = Male

[npc018]
Name = Chica escolar
Description = Joven estudiante con falda de tablas y libreta en mano. Frecuenta Ciudad Calceda y bibliotecas.
Gender = Female

[npc019]
Name = Joven informal
Description = Chico adolescente con camiseta y auriculares al cuello. Pasea por ciudades y muelles.
Gender = Male

[npc020]
Name = Joven con chaleco
Description = Chica adolescente con chaleco y zapatillas deportivas. Pasea por plazas y miradores.
Gender = Female

[npc021]
Name = Hombre adulto
Description = Ciudadano común de mediana edad con camisa de manga corta. Habitante de pueblos y ciudades.
Gender = Male

[npc022]
Name = Mujer adulta
Description = Ciudadana común de mediana edad con vestido informal. Habitante de pueblos y ciudades.
Gender = Female

[npc023]
Name = Hombre corpulento
Description = Hombre robusto de complexión ancha, aspecto bonachón y ropa cómoda. Frecuenta mercados y puertos.
Gender = Male

[npc024]
Name = Mujer de mercado
Description = Mujer de aspecto alegre con cesta de mimbre o delantal de comerciante. Frecuenta puestos y mercadillos.
Gender = Female

[npc025]
Name = Anciano
Description = Hombre de avanzada edad con bastón de madera y paso pausado. Descansa en bancos de plazas y jardines.
Gender = Male

[npc026]
Name = Anciana
Description = Mujer de avanzada edad con chal sobre los hombros y peinado recogido. Da consejos sabios en los pueblos.
Gender = Female

[npc027]
Name = (Repuesto 1)
Description = Slot libre para NPC identificable o genérico según necesidades futuras.
Gender = Mixed

[npc028]
Name = (Repuesto 2)
Description = Slot libre para NPC identificable o genérico según necesidades futuras.
Gender = Mixed

[npc029]
Name = (Repuesto 3)
Description = Slot libre para NPC identificable o genérico según necesidades futuras.
Gender = Mixed

[npc030]
Name = (Repuesto 4)
Description = Slot libre para NPC identificable o genérico según necesidades futuras.
Gender = Mixed

[npc031]
Name = (Repuesto 5)
Description = Slot libre para NPC identificable o genérico según necesidades futuras.
Gender = Mixed

[npc032]
Name = (Repuesto 6)
Description = Slot libre para NPC identificable o genérico según necesidades futuras.
Gender = Mixed
"""
    with open(overworlds_path, "w", encoding="utf-8") as f:
        f.write(header)
    print("rem_overworlds.txt actualizado con exito.")

if __name__ == "__main__":
    shift_npcs()
