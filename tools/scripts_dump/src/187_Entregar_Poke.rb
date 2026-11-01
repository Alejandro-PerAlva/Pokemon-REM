def pbEntregarPokemon(especie, apodo_npc = "Investigadora")
  if $Trainer.pokemon_count <= 1
    pbMessage(_INTL("\\tg[{1}]¡Pero solo tienes ese Pokémon!", apodo_npc))
    return false
  end

  encontrado = false
  for i in 0...$Trainer.party.length
    pkmn = $Trainer.party[i]
    if pkmn && !pkmn.isEgg? && pkmn.species == especie
      pbRemovePokemonAt(i)
      pbMessage(_INTL("\\tg[{1}]¡Genial, muchas gracias por el {2}!", apodo_npc, PBSpecies.getName(especie)))
      encontrado = true
      break
    end
  end

  if !encontrado
    pbMessage(_INTL("\\tg[{1}]Vaya, parece que no tienes ningún {2} contigo...", apodo_npc, PBSpecies.getName(especie)))
    return false
  end

  return true
end