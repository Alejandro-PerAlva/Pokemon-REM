class PokeBattle_Pokemon
  alias level_cap_exp exp=
  def exp=(value)
    cap = ($game_variables && $game_variables[50] > 0) ? $game_variables[50] : PBExperience::MAXLEVEL
    max_exp = PBExperience.pbGetStartExperience(cap, self.growthrate)
    value = max_exp if value > max_exp
    level_cap_exp(value)
  end

  alias level_cap_level level=
  def level=(value)
    cap = ($game_variables && $game_variables[50] > 0) ? $game_variables[50] : PBExperience::MAXLEVEL
    value = cap if value > cap
    level_cap_level(value)
  end
end

# Sobreescribimos el efecto del Caramelo Raro para que NO funcione si alcanza el CAP
ItemHandlers::UseOnPokemon.add(:RARECANDY,proc{|item,pokemon,scene|
   cap = ($game_variables && $game_variables[50] > 0) ? $game_variables[50] : PBExperience::MAXLEVEL
   if pokemon.level >= cap || pokemon.hp==0 || (pokemon.isShadow? rescue false)
     scene.pbDisplay(_INTL("No tendrá ningún efecto."))
     next false
   else
     pbChangeLevel(pokemon,pokemon.level+1,scene)
     scene.pbHardRefresh
     next true
   end
})
