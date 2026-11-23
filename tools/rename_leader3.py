import os
import re

def update_argos_to_greta():
    # 1. trainertypes.txt
    with open('PBS/trainertypes.txt', 'r', encoding='utf-8') as f:
        tt = f.read()
    tt = tt.replace('# Gimnasio 3: Argos (Acero)\n7,LEADER_3,Líder,60,Combate Lider,Victoria Lider,,Male,100,',
                    '# Gimnasio 3: Greta (Acero)\n7,LEADER_3,Líder,60,Combate Lider,Victoria Lider,,Female,100,')
    with open('PBS/trainertypes.txt', 'w', encoding='utf-8') as f:
        f.write(tt)
    print("trainertypes.txt actualizado (Female, Greta).")

    # 2. tools/rebalance/build_trainertypes.py
    if os.path.exists('tools/rebalance/build_trainertypes.py'):
        with open('tools/rebalance/build_trainertypes.py', 'r', encoding='utf-8') as f:
            btt = f.read()
        btt = btt.replace('("LEADER_3", "Lider", 60, "Male", A_LEADER, "Gimnasio 3: Argos (Acero)")',
                          '("LEADER_3", "Lider", 60, "Female", A_LEADER, "Gimnasio 3: Greta (Acero)")')
        with open('tools/rebalance/build_trainertypes.py', 'w', encoding='utf-8') as f:
            f.write(btt)
        print("tools/rebalance/build_trainertypes.py actualizado.")

    # 3. PBS/rem_characters.txt
    with open('PBS/rem_characters.txt', 'r', encoding='utf-8') as f:
        rc = f.read()
    rc = rc.replace('[CHAR_ARGOS]', '[CHAR_GRETA]')
    rc = rc.replace('Name = Argos', 'Name = Greta')
    rc = rc.replace('Aliases = Argos', 'Aliases = Greta')
    rc = rc.replace('Argos fue a la Isla Sueño', 'Greta fue a la Isla Sueño')
    rc = rc.replace('Argos trabaja en la isla', 'Greta trabaja en la isla')
    rc = rc.replace('Buscar a Argos en el faro', 'Buscar a Greta en el faro')
    with open('PBS/rem_characters.txt', 'w', encoding='utf-8') as f:
        f.write(rc)
    print("rem_characters.txt actualizado.")

    # 4. PBS/rem_locations.txt
    with open('PBS/rem_locations.txt', 'r', encoding='utf-8') as f:
        rl = f.read()
    rl = rl.replace('Argos (Líder del Gimnasio 3)', 'Greta (Líder del Gimnasio 3)')
    rl = rl.replace('Gimnasio 3 — Argos', 'Gimnasio 3 — Greta')
    rl = rl.replace('Argos trabaja en la isla', 'Greta trabaja en la isla')
    rl = rl.replace('CharactersPresent = Argos;', 'CharactersPresent = Greta;')
    with open('PBS/rem_locations.txt', 'w', encoding='utf-8') as f:
        f.write(rl)
    print("rem_locations.txt actualizado.")

    # 5. PBS/rem_story.txt
    with open('PBS/rem_story.txt', 'r', encoding='utf-8') as f:
        rs = f.read()
    rs = rs.replace('Encontráis a Argos subido a una torre', 'Encontráis a Greta subida a una torre')
    rs = rs.replace('Argos trabaja en el faro', 'Greta trabaja en el faro')
    rs = rs.replace('Argos os sigue', 'Greta os sigue')
    rs = rs.replace('Cuando cae, Argos asiente', 'Cuando cae, Greta asiente')
    rs = rs.replace('Gimnasio 3 (Acero) — Argos', 'Gimnasio 3 (Acero) — Greta')
    rs = rs.replace('Argos entrega la advertencia', 'Greta entrega la advertencia')
    rs = rs.replace('CharactersInScene = Tú (Protagonista);Lucián;Argos', 'CharactersInScene = Tú (Protagonista);Lucián;Greta')
    rs = rs.replace('CharactersInScene = Tú (Protagonista);Argos', 'CharactersInScene = Tú (Protagonista);Greta')
    with open('PBS/rem_story.txt', 'w', encoding='utf-8') as f:
        f.write(rs)
    print("rem_story.txt actualizado.")

    # 6. PBS/rem_progression.txt
    with open('PBS/rem_progression.txt', 'r', encoding='utf-8') as f:
        rp = f.read()
    rp = rp.replace('Gimnasio 3 — Argos', 'Gimnasio 3 — Greta')
    rp = rp.replace('para buscar a Argos', 'para buscar a Greta')
    with open('PBS/rem_progression.txt', 'w', encoding='utf-8') as f:
        f.write(rp)
    print("rem_progression.txt actualizado.")

    # 7. PBS/rem_location_items.txt
    with open('PBS/rem_location_items.txt', 'r', encoding='utf-8') as f:
        rli = f.read()
    rli = rli.replace('Gimnasio 3 · Argos', 'Gimnasio 3 · Greta')
    rli = rli.replace('Tabla de Surf del constructor', 'Tabla de Surf de la constructora')
    with open('PBS/rem_location_items.txt', 'w', encoding='utf-8') as f:
        f.write(rli)
    print("rem_location_items.txt actualizado.")

    # 8. PBS/rem_variables_switches.txt
    with open('PBS/rem_variables_switches.txt', 'r', encoding='utf-8') as f:
        rvs = f.read()
    rvs = rvs.replace('Gimnasio 3 — Argos', 'Gimnasio 3 — Greta')
    with open('PBS/rem_variables_switches.txt', 'w', encoding='utf-8') as f:
        f.write(rvs)
    print("rem_variables_switches.txt actualizado.")

    # 9. tools/rebalance/phase1/build_narrative.py
    if os.path.exists('tools/rebalance/phase1/build_narrative.py'):
        with open('tools/rebalance/phase1/build_narrative.py', 'r', encoding='utf-8') as f:
            bn = f.read()
        bn = bn.replace('para buscar a Argos', 'para buscar a Greta')
        bn = bn.replace("('Gimnasio 3 — Argos', 'Acero', 35)", "('Gimnasio 3 — Greta', 'Acero', 35)")
        bn = bn.replace("slug='ARGOS'", "slug='GRETA'")
        bn = bn.replace("aliases=['Argos']", "aliases=['Greta']")
        bn = bn.replace("presence=['Argos']", "presence=['Greta']")
        with open('tools/rebalance/phase1/build_narrative.py', 'w', encoding='utf-8') as f:
            f.write(bn)
        print("tools/rebalance/phase1/build_narrative.py actualizado.")

    # 10. tools/rebalance/verify_narrative_books.py
    if os.path.exists('tools/rebalance/verify_narrative_books.py'):
        with open('tools/rebalance/verify_narrative_books.py', 'r', encoding='utf-8') as f:
            vnb = f.read()
        vnb = vnb.replace("'Argos'", "'Greta'")
        vnb = vnb.replace("'Argos': 35", "'Greta': 35")
        with open('tools/rebalance/verify_narrative_books.py', 'w', encoding='utf-8') as f:
            f.write(vnb)
        print("tools/rebalance/verify_narrative_books.py actualizado.")

    # 11. tools/overworlds/apply_gen5_overworlds.py & apply_gen5_curated.py
    if os.path.exists('tools/overworlds/apply_gen5_overworlds.py'):
        with open('tools/overworlds/apply_gen5_overworlds.py', 'r', encoding='utf-8') as f:
            ago = f.read()
        ago = ago.replace("Argos (Acero, masculino)", "Greta (Acero, femenina)")
        ago = ago.replace("Argos, Gimnasio Acero, M", "Greta, Gimnasio Acero, F")
        with open('tools/overworlds/apply_gen5_overworlds.py', 'w', encoding='utf-8') as f:
            f.write(ago)
        print("tools/overworlds/apply_gen5_overworlds.py actualizado.")

    if os.path.exists('tools/overworlds/apply_gen5_curated.py'):
        with open('tools/overworlds/apply_gen5_curated.py', 'r', encoding='utf-8') as f:
            agc = f.read()
        agc = agc.replace("Argos, Lider de Acero", "Greta, Lider de Acero")
        with open('tools/overworlds/apply_gen5_curated.py', 'w', encoding='utf-8') as f:
            f.write(agc)
        print("tools/overworlds/apply_gen5_curated.py actualizado.")

if __name__ == '__main__':
    update_argos_to_greta()
