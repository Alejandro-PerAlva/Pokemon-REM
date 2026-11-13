#===============================================================================
# REM_AI — Motor de Inteligencia Artificial Competitiva y Táctica de Pokémon REM
# Basado en la filosofía de alta dificultad y juego limpio (Cero Input Reading):
# 1. Suelo de inteligencia mínimo para todo el juego (nadie ataca a inmunidades).
# 2. Visión y cálculo de 2HKO (matar en 2 turnos con iniciativa).
# 3. Prohibición estricta de Setup Suicida (no boostearse a punto de morir).
# 4. Anti-Sweeper: Castigo severo si el jugador se boostea (+2 en Atk/SpAtk/Speed).
# 5. Reemplazo quirúrgico tras KO (pbChooseBestNewEnemy evalúa Supervivencia + Daño + Velocidad).
# 6. Instinto Depredador en Pokémon Salvajes (agresividad táctica sin jugadas absurdas).
# 7. Control de Peligros de Entrada (Hazards / Trampa Rocas) en cambios voluntarios.
# 8. Cero Input Reading (toma de decisiones honesta con información visible del campo).
# Compatible con RGSS1 / Ruby 1.8.
#===============================================================================

class PokeBattle_Battle
  #-----------------------------------------------------------------------------
  # 1. Obtener la destreza efectiva (Skill) del combatiente
  #-----------------------------------------------------------------------------
  def remEffectiveSkill(index)
    return PBTrainerAI.mediumSkill if !@opponent # Salvajes: Instinto base táctico (32)
    
    owner = pbGetOwner(index)
    
    # Bosses (Líderes, Alto Mando, Campeona y Alto Mando de Morfeo): Nivel Boss (100)
    if owner && owner.trainertype
      tt = owner.trainertype
      if (defined?(PBTrainers::LEADER_1) && tt >= PBTrainers::LEADER_1 && tt <= PBTrainers::LEADER_8) ||
         (defined?(PBTrainers::ELITE_1) && tt >= PBTrainers::ELITE_1 && tt <= PBTrainers::ELITE_4) ||
         (defined?(PBTrainers::CHAMPION) && tt == PBTrainers::CHAMPION) ||
         (defined?(PBTrainers::MORFEO_GENERAL_M) && tt == PBTrainers::MORFEO_GENERAL_M) ||
         (defined?(PBTrainers::MORFEO_GENERAL_F) && tt == PBTrainers::MORFEO_GENERAL_F) ||
         (defined?(PBTrainers::MORFEO_SUBCAPTAIN) && tt == PBTrainers::MORFEO_SUBCAPTAIN) ||
         (defined?(PBTrainers::MORFEO_LEADER) && tt == PBTrainers::MORFEO_LEADER)
        return PBTrainerAI.bestSkill # 100
      end
    end
    
    # Todos los entrenadores normales del juego tienen el mismo nivel unificado (70)
    return 70
  end

  #-----------------------------------------------------------------------------
  # 2. Estimación de amenaza del oponente hacia el atacante (Anti-Suicidio)
  #-----------------------------------------------------------------------------
  def remEstimateOpponentDamage(attacker, opponent, skill)
    return 0 if !opponent || opponent.isFainted?
    max_dmg = 0
    
    for m in opponent.moves
      next if m.id == 0 || m.basedamage == 0
      dmg = pbRoughDamage(m, opponent, attacker, skill, pbBetterBaseDamage(m, opponent, attacker, skill, m.basedamage))
      max_dmg = dmg if dmg > max_dmg
    end
    
    # Si aún no se conocen movimientos con daño del rival, estimar por tipo STAB
    if max_dmg == 0
      eff1 = PBTypes.getCombinedEffectiveness(opponent.type1, attacker.type1, attacker.type2)
      eff2 = opponent.type2 ? PBTypes.getCombinedEffectiveness(opponent.type2, attacker.type1, attacker.type2) : 8
      max_eff = [eff1, eff2].max
      max_dmg = (attacker.totalhp * 0.35 * (max_eff / 8.0)).round
    end
    
    return max_dmg
  end

  #-----------------------------------------------------------------------------
  # 3. Envoltura de pbGetMoveScore: 2HKO, Anti-Suicide, Anti-Sweeper e Inmunidades
  #-----------------------------------------------------------------------------
  alias rem_orig_pbGetMoveScore pbGetMoveScore
  def pbGetMoveScore(move, attacker, opponent, skill=100)
    # Asegurar destreza efectiva
    skill = remEffectiveSkill(attacker.index) if attacker
    
    # Puntuación base original de Essentials
    score = rem_orig_pbGetMoveScore(move, attacker, opponent, skill)
    return 0 if score <= 0
    opponent = attacker.pbOppositeOpposing if !opponent
    return score if !opponent || opponent.isFainted?

    # --- PILAR A: Inmunidad Absoluta (Nadie ataca a inmunidades evidentes) ---
    if move.basedamage > 0
      typemod = pbTypeModifier(move.type, attacker, opponent)
      return 0 if typemod == 0 # Fantasma a Normal, Tierra a Volador, etc.
    end

    # --- PILAR B: Eliminación de Spam de Stats redundantes ---
    # Gruñido / Ataque -6
    if (move.function == 0x42 || move.function == 0x43) && opponent.stages[PBStats::ATTACK] <= -6
      return 0
    end
    # Látigo / Chirrido / Defensa -6
    if (move.function == 0x44 || move.function == 0x45) && opponent.stages[PBStats::DEFENSE] <= -6
      return 0
    end
    # Reducción de Velocidad / Velocidad -6
    if (move.function == 0x46 || move.function == 0x47) && opponent.stages[PBStats::SPEED] <= -6
      return 0
    end

    aspeed = pbRoughStat(attacker, PBStats::SPEED, skill)
    ospeed = pbRoughStat(opponent, PBStats::SPEED, skill)
    threat = remEstimateOpponentDamage(attacker, opponent, skill)

    # --- PILAR C: Visión y Cálculo de 2HKO (Matar en dos turnos con iniciativa) ---
    if move.basedamage > 0 && opponent.hp > 0
      real_dmg = pbRoughDamage(move, attacker, opponent, skill, pbBetterBaseDamage(move, attacker, opponent, skill, move.basedamage))
      dmg_pct = (real_dmg * 100.0 / opponent.hp)
      
      # Si no mata de 1 turno (no OHKO) pero quita >= 50% de la vida actual (2HKO)
      if dmg_pct < 100 && (dmg_pct * 2.0) >= 100
        # Si la IA ataca primero o el ataque tiene prioridad, y la IA sobrevive al siguiente golpe
        if (aspeed >= ospeed || move.priority > 0) && (threat < attacker.hp)
          score += 25 # Gran bonificación por cerrar la partida en 2 turnos
        end
      end
    end

    # --- PILAR D: Prohibición de Setup Suicida (Anti-Suicide Setup) ---
    # Códigos de subida de stats sin daño (Danza Espada, Paz Mental, etc.) o recuperación lenta
    is_setup_move = (move.basedamage == 0 && (
      (move.function >= 0x1C && move.function <= 0x3B) || # Subidas de stats de usuario
      move.function == 0xD4 || # Recuperación / Respiro / Deseo
      move.function == 0x2C    # Danza Espada
    ))
    
    if is_setup_move
      # Si el rival es más rápido y tiene daño para liquidar a la IA en este turno,
      # o si la salud de la IA es crítica (< 25%) y el rival la amenaza:
      if (aspeed < ospeed && threat >= attacker.hp) || (attacker.hp <= (attacker.totalhp * 0.25).floor && threat >= attacker.hp * 0.7)
        # Cancelar por completo el setup: suicidarse aquí es pésimo
        score = [score - 140, 0].max
      end
    end

    # --- PILAR E: Anti-Sweeper (Castigo severo al Boost del Jugador) ---
    atk_stg = opponent.stages[PBStats::ATTACK]
    spa_stg = opponent.stages[PBStats::SPATK]
    spe_stg = opponent.stages[PBStats::SPEED]
    is_player_sweeper = (atk_stg >= 2 || spa_stg >= 2 || spe_stg >= 2)

    if is_player_sweeper && skill >= PBTrainerAI.mediumSkill
      # 1. Reseteo / Phasing
      case move.function
      when 0x51 # Niebla (Haze)
        score += 70
      when 0xEB # Remolino / Rugido (Phasing, borra todos los boosts del rival)
        score += 70
      when 0xB9 # Mofa (Taunt, frena setup continuo)
        score += 45
      when 0xBB # Otra Vez (Encore)
        score += 55
      when 0x0A # Fuego Fatuo (quemar para partir a la mitad el ataque físico)
        if atk_stg >= 2 && opponent.pbCanBurn?(attacker, false)
          score += 55
        end
      when 0x07, 0x08, 0x09, 0xC5 # Parálisis (arruina la velocidad del sweeper)
        if spe_stg >= 2 && opponent.pbCanParalyze?(attacker, false)
          score += 55
        end
      end

      # 2. Movimientos de Prioridad frente a Sweeper más rápido
      if move.priority > 0 && move.basedamage > 0 && aspeed < ospeed
        score += 35 # Asegurar arañar daño antes de ser debilitado
      end
    end

    return score
  end

  #-----------------------------------------------------------------------------
  # 4. Selección de Movimientos: Instinto Salvaje y Precisión de Élite
  #-----------------------------------------------------------------------------
  alias rem_orig_pbChooseMoves pbChooseMoves
  def pbChooseMoves(index)
    attacker = @battlers[index]
    wildbattle = !@opponent && pbIsOpposing?(index)
    
    if wildbattle
      # Pokémon Salvajes en Pokémon REM: Instinto Depredador Ofensivo
      # No asignamos 100 planos al azar: calculan daño real y van a degüello
      scores = [0, 0, 0, 0]
      myChoices = []
      totalscore = 0
      opponent = attacker.pbOppositeOpposing
      
      for i in 0...4
        if pbCanChooseMove?(index, i, false)
          s = pbGetMoveScore(attacker.moves[i], attacker, opponent, PBTrainerAI.mediumSkill)
          scores[i] = [s, 0].max
          myChoices.push(i)
          totalscore += scores[i]
        end
      end
      
      maxscore = 0
      for s in scores
        maxscore = s if s > maxscore
      end
      
      if maxscore <= 0
        if myChoices.length > 0
          pbRegisterMove(index, myChoices[pbAIRandom(myChoices.length)], false)
        else
          pbAutoChooseMove(index)
        end
        return
      end
      
      # Si hay un movimiento letal o muy superior (KO a tiro), 85% de probabilidad de elegirlo
      best_moves = []
      for i in 0...4
        if attacker.moves[i].id != 0 && scores[i] >= (maxscore * 0.85)
          best_moves.push(i)
          best_moves.push(i) if scores[i] == maxscore # Doble peso al mejor
        end
      end
      
      if best_moves.length > 0 && pbAIRandom(100) < 85
        chosen = best_moves[pbAIRandom(best_moves.length)]
        pbRegisterMove(index, chosen, false)
        return
      end
      
      # Ruleta ponderada si hay opciones parejas
      randnum = pbAIRandom(totalscore)
      cumtotal = 0
      for i in 0...4
        if scores[i] > 0
          cumtotal += scores[i]
          if randnum < cumtotal
            pbRegisterMove(index, i, false)
            return
          end
        end
      end
      pbRegisterMove(index, myChoices[0], false)
      return
    else
      # Combates de entrenadores: usar el método optimizado original
      rem_orig_pbChooseMoves(index)
    end
  end

  #-----------------------------------------------------------------------------
  # 5. Reconstrucción de Salida tras KO: Supervivencia + Amenaza + Iniciativa
  #-----------------------------------------------------------------------------
  def pbChooseBestNewEnemy(index, party, enemies)
    return -1 if !enemies || enemies.length == 0
    $PokemonTemp = PokemonTemp.new if !$PokemonTemp
    
    opp = @battlers[index].pbOppositeOpposing
    opp = opp.pbPartner if opp && opp.isFainted?
    return enemies[0] if !opp || opp.isFainted?
    
    opp_speed = opp.pbSpeed rescue 0
    opp_type3 = (opp.effects && opp.effects[PBEffects::Type3]) ? opp.effects[PBEffects::Type3] : -1
    
    best = -1
    best_score = -9999
    
    for e in enemies
      pkmn = party[e]
      next if !pkmn || pkmn.isFainted?
      
      score = 100 # Base
      
      # A. Supervivencia Defensiva (¿Aguanta el tipo del rival?)
      eff1 = PBTypes.getCombinedEffectiveness(opp.type1, pkmn.type1, pkmn.type2)
      eff2 = opp.type2 ? PBTypes.getCombinedEffectiveness(opp.type2, pkmn.type1, pkmn.type2) : 8
      incoming_eff = [eff1, eff2].max
      
      if incoming_eff == 0
        score += 55 # Inmunidad limpia a un STAB del rival
      elsif incoming_eff <= 4
        score += 35 # Resistencia sólida (x0.5 o x0.25)
      elsif incoming_eff >= 16
        score -= 50 # Debilidad elemental severa, riesgo de OHKO
      end
      
      # B. Amenaza Ofensiva (¿Puede golpear fuerte al rival?)
      best_move_eff = 0
      has_stab = false
      for move in pkmn.moves
        next if move.id == 0
        md = PBMoveData.new(move.id)
        next if md.basedamage == 0
        m_eff = PBTypes.getCombinedEffectiveness(md.type, opp.type1, opp.type2, opp_type3)
        best_move_eff = m_eff if m_eff > best_move_eff
        if (md.type == pkmn.type1 || md.type == pkmn.type2) && m_eff >= 8
          has_stab = true
        end
      end
      
      if best_move_eff >= 16
        score += 45 # Ataque supereficaz
        score += 25 if has_stab # Con STAB es una amenaza inmediata
      elsif best_move_eff >= 8
        score += 20 # Daño neutro respetable
      elsif best_move_eff == 0
        score -= 40 # No puede tocar al rival
      end
      
      # C. Iniciativa / Velocidad
      if pkmn.speed >= opp_speed
        score += 25 # Golpea primero
      end
      
      # D. Estado de Salud Restante
      hp_ratio = pkmn.hp.to_f / pkmn.totalhp.to_f
      if hp_ratio <= 0.25
        score -= 30 # Muy débil, no sacarlo salvo que no haya alternativa
      elsif hp_ratio >= 0.9
        score += 15 # Fresco y en óptimas condiciones
      end
      
      # E. Control de Trampa Rocas
      if @battlers[index].pbOwnSide.effects[PBEffects::StealthRock]
        rock_type = getConst(PBTypes, :ROCK) || -1
        if rock_type >= 0
          rock_eff = PBTypes.getCombinedEffectiveness(rock_type, pkmn.type1, pkmn.type2)
          rock_pct = (rock_eff / 32.0)
          if rock_pct >= 0.25 && hp_ratio <= 0.35
            score -= 45 # Moriría o quedaría en coma al pisar las rocas
          end
        end
      end
      
      if score > best_score
        best_score = score
        best = e
      end
    end
    
    return best != -1 ? best : enemies[0]
  end

  #-----------------------------------------------------------------------------
  # 6. Cambios Voluntarios: Filtro estricto de Trampa Rocas y Púas
  #-----------------------------------------------------------------------------
  alias rem_orig_pbEnemyShouldWithdrawEx? pbEnemyShouldWithdrawEx?
  def pbEnemyShouldWithdrawEx?(index, alwaysSwitch)
    # Si hay Trampa Rocas en nuestro campo, verificar que el relevo no muera al entrar
    if @battlers[index].pbOwnSide.effects[PBEffects::StealthRock]
      rock_type = getConst(PBTypes, :ROCK) || -1
      if rock_type >= 0
        party = pbParty(index)
        safe_candidates = 0
        for i in 0...party.length
          next if !pbCanSwitch?(index, i, false)
          pkmn = party[i]
          rock_eff = PBTypes.getCombinedEffectiveness(rock_type, pkmn.type1, pkmn.type2)
          rock_dmg = (pkmn.totalhp * (rock_eff / 32.0)).round
          safe_candidates += 1 if rock_dmg < pkmn.hp
        end
        # Si ningún Pokémon en el banquillo sobrevive al daño de entrada de rocas, no cambiar
        return false if safe_candidates == 0 && !alwaysSwitch
      end
    end
    
    return rem_orig_pbEnemyShouldWithdrawEx?(index, alwaysSwitch)
  end
end
