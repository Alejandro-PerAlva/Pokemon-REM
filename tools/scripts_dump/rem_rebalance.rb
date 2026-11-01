#===============================================================================
# REM_Rebalance — mecánicas del rebalanceo de Pokémon REM (habilidades, Heladura,
# Nieve, objetos). Se carga después de todos los scripts del motor y antes de Main.
# Fuente: tools/scripts_dump/rem_rebalance.rb (inyectado por build_scripts.rb)
#===============================================================================

class PokeBattle_Battler
  # Sincronía también contagia la Heladura
  def pbCanFreezeSynchronize?(opponent)
    return false if isFainted? || self.status!=0
    return false if pbHasType?(:ICE)
    return false if @battle.pbWeather==PBWeather::SUNNYDAY || @battle.pbWeather==PBWeather::HARSHSUN
    return false if @battle.field.effects[PBEffects::MistyTerrain]>0 && !self.isAirborne?
    return false if hasWorkingAbility(:MAGMAARMOR) || hasWorkingAbility(:VITALSPIRIT) ||
                    hasWorkingAbility(:COMATOSE) || hasWorkingAbility(:SHIELDSDOWN)
    return false if pbOwnSide.effects[PBEffects::Safeguard]>0
    return true
  end

  # Bajada de característica al entrar en combate (Iluminación, Alerta, Recogemiel)
  def pbRemEntryDrop(src,stat,extrablockers=[])
    return false if isFainted?
    abname=PBAbilities.getName(src.ability)
    if effects[PBEffects::Substitute]>0
      @battle.pbDisplay(_INTL("¡El sustituto ha protegido a {1} de {3} de {2}!",pbThis,src.pbThis(true),abname))
      return false
    end
    if !src.hasWorkingAbility(:CONTRARY)
      if pbOwnSide.effects[PBEffects::Mist]>0
        @battle.pbDisplay(_INTL("¡{1} se ha protegido de {3} de {2} con Neblina!",pbThis,src.pbThis(true),abname))
        return false
      end
      blockers=[:CLEARBODY,:WHITESMOKE,:FULLMETALBODY]+extrablockers
      for b in blockers
        if hasWorkingAbility(b)
          @battle.pbDisplay(_INTL("¡{2} de {1} hizo ineficaz {4} de {3}!",pbThis,PBAbilities.getName(self.ability),src.pbThis(true),abname))
          return false
        end
      end
      if (hasWorkingAbility(:FLOWERVEIL) && pbHasType?(:GRASS)) ||
         (pbPartner.hasWorkingAbility(:FLOWERVEIL) && pbHasType?(:GRASS))
        @battle.pbDisplay(_INTL("¡Velo Flor de {1} hizo ineficaz {3} de {2}!",pbThis,src.pbThis(true),abname))
        return false
      end
    end
    return pbReduceStatWithCause(stat,1,src,abname)
  end

  alias rem_orig_pbAbilitiesOnSwitchIn pbAbilitiesOnSwitchIn
  def pbAbilitiesOnSwitchIn(onactive)
    rem_orig_pbAbilitiesOnSwitchIn(onactive)
    return if !onactive || isFainted?
    foes=[]
    for i in 0...4
      b=@battle.battlers[i]
      foes.push(b) if b && pbIsOpposing?(i) && !b.isFainted?
    end
    # Iluminación: -1 Precisión a los rivales
    if hasWorkingAbility(:ILLUMINATE)
      PBDebug.log("[Habilidad disparada] Iluminación de #{pbThis}")
      for b in foes; b.pbRemEntryDrop(self,PBStats::ACCURACY,[:KEENEYE]); end
    end
    # Alerta: -1 At. Esp. a los rivales
    if hasWorkingAbility(:FOREWARN)
      PBDebug.log("[Habilidad disparada] Alerta de #{pbThis}")
      for b in foes; b.pbRemEntryDrop(self,PBStats::SPATK); end
    end
    # Recogemiel: -1 Velocidad a los rivales
    if hasWorkingAbility(:HONEYGATHER)
      PBDebug.log("[Habilidad disparada] Recogemiel de #{pbThis}")
      for b in foes; b.pbRemEntryDrop(self,PBStats::SPEED); end
    end
    # Recogebolas: +1 Velocidad si algún miembro del equipo está debilitado
    if hasWorkingAbility(:BALLFETCH)
      party=@battle.pbParty(@index)
      fainted=false
      for p in party
        fainted=true if p && !p.isEgg? && p.hp<=0
      end
      pbIncreaseStatWithCause(PBStats::SPEED,1,self,PBAbilities.getName(self.ability)) if fainted
    end
  end

  # Hierba Copia: copia una vez las mejoras de características del rival
  alias rem_orig_pbIncreaseStatWithCause pbIncreaseStatWithCause
  def pbIncreaseStatWithCause(stat,increment,attacker,cause,showanim=true,showmessage=true,moldbreaker=false,ignoreContrary=false)
    ret=rem_orig_pbIncreaseStatWithCause(stat,increment,attacker,cause,showanim,showmessage,moldbreaker,ignoreContrary)
    if ret && !@rem_mirroring
      for i in 0...4
        b=@battle.battlers[i]
        next if !b || b.isFainted? || !pbIsOpposing?(i) || !b.hasWorkingItem(:MIRRORHERB)
        b.instance_variable_set(:@rem_mirroring,true)
        @rem_mirroring=true
        if b.pbIncreaseStatWithCause(stat,increment,b,PBItems.getName(b.item))
          b.pbConsumeItem
        end
        @rem_mirroring=false
        b.instance_variable_set(:@rem_mirroring,false)
      end
    end
    return ret
  end
end

#===============================================================================
# Objetos
#===============================================================================
# Evolución por objeto: Colmillo Agudo, Garra Afilada, Piedra Oval
ItemHandlers::UseOnPokemon.copy(:FIRESTONE,:RAZORFANG,:RAZORCLAW,:OVALSTONE)

# Caramelo Infinito: como el Caramelo Raro (respeta el tope de nivel) y no se gasta
ItemHandlers::UseOnPokemon.copy(:RARECANDY,:INFINITECANDY)

# Mentas: cambian la Naturaleza efectiva
%w(ADAMANT JOLLY MODEST TIMID BOLD CALM IMPISH CAREFUL BRAVE QUIET RELAXED SASSY NAIVE HASTY SERIOUS).each do |nm|
  ItemHandlers::UseOnPokemon.add((nm+"MINT").to_sym,proc{|item,pokemon,scene|
    natid=getConst(PBNatures,nm.to_sym)
    if natid==nil || pokemon.isEgg? || pokemon.nature==natid
      scene.pbDisplay(_INTL("No tendrá ningún efecto."))
      next false
    end
    pokemon.natureflag=natid
    pokemon.calcStats
    scene.pbRefresh
    scene.pbDisplay(_INTL("La Naturaleza efectiva de {1} ahora es {2}.",pokemon.name,PBNatures.getName(natid)))
    next true
  })
end

# Pokévial: cura al equipo; empieza con 1 carga (máx. 3) y se recarga en el Centro Pokémon
class PokemonGlobalMetadata
  attr_accessor :remVialMax
  attr_accessor :remVialCharges
end
def pbRemVialMax
  return ($PokemonGlobal && $PokemonGlobal.remVialMax) ? [[$PokemonGlobal.remVialMax,1].max,3].min : 1
end
def pbRemVialCharges
  return pbRemVialMax if !$PokemonGlobal || $PokemonGlobal.remVialCharges==nil
  return [$PokemonGlobal.remVialCharges,pbRemVialMax].min
end
def pbRemVialUpgrade   # +1 carga máxima (hasta 3); para usar desde eventos
  $PokemonGlobal.remVialMax=[pbRemVialMax+1,3].min
  $PokemonGlobal.remVialCharges=$PokemonGlobal.remVialMax
end
def pbRemVialRefill
  $PokemonGlobal.remVialCharges=pbRemVialMax if $PokemonGlobal
end
ItemHandlers::UseFromBag.add(:POKEVIAL,proc{|item|
  cur=pbRemVialCharges
  if cur<=0
    Kernel.pbMessage(_INTL("El Pokévial está vacío. Se recarga en un Centro Pokémon."))
    next 0
  end
  hurt=false
  for p in $Trainer.party
    hurt=true if p && !p.isEgg? && (p.hp<p.totalhp || p.status!=0)
  end
  if !hurt
    Kernel.pbMessage(_INTL("No hay nada que curar."))
    next 0
  end
  pbHealAll
  $PokemonGlobal.remVialCharges=cur-1
  Kernel.pbMessage(_INTL("¡El equipo se ha curado! Cargas restantes: {1}/{2}.",cur-1,pbRemVialMax))
  next 1
})
alias rem_orig_pbHealAll pbHealAll
def pbHealAll
  rem_orig_pbHealAll
  pbRemVialRefill
end
