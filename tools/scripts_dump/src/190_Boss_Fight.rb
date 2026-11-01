Boss = 96

def pbBossFight(species1,level1,forma=0,variable=nil,canescape=true,canlose=false)
  if (Input.press?(Input::CTRL) && $DEBUG) || $Trainer.pokemonCount==0
    if $Trainer.pokemonCount>0
      Kernel.pbMessage(_INTL("SALTANDO BATALLA..."))
    end
    pbSet(variable,1)
    $PokemonGlobal.nextBattleBGM=nil
    $PokemonGlobal.nextBattleME=nil
    $PokemonGlobal.nextBattleBack=nil
    return true
  end
  if species1.is_a?(String) || species1.is_a?(Symbol)
    species1=getID(PBSpecies,species1)
  end
  currentlevels=[]
  for i in $Trainer.party
    currentlevels.push(i.level)
  end
  genwildpoke=pbGenerateWildPokemon(species1,level1)
  genwildpoke.form=forma
  Events.onStartBattle.trigger(nil,genwildpoke)
  scene=pbNewBattleScene
  if $PokemonGlobal.partner
    othertrainer=PokeBattle_Trainer.new(
       $PokemonGlobal.partner[1],$PokemonGlobal.partner[0])
    othertrainer.id=$PokemonGlobal.partner[2]
    othertrainer.party=$PokemonGlobal.partner[3]
    combinedParty=[]
    for i in 0...$Trainer.party.length
      combinedParty[i]=$Trainer.party[i]
    end
    for i in 0...othertrainer.party.length
      combinedParty[6+i]=othertrainer.party[i]
    end
    battle=PokeBattle_Battle.new(scene,combinedParty,[genwildpoke],
       [$Trainer,othertrainer],nil)
    battle.fullparty1=true
  else
    battle=PokeBattle_Battle.new(scene,$Trainer.party,[genwildpoke],
       $Trainer,nil)
    battle.fullparty1=false
  end
  battle.internalbattle=true
  battle.doublebattle=battle.pbDoubleBattleAllowed?()
  battle.doublebattle=true if $Trainer.ablePokemonCount>1 || $game_switches[135]
  battle.cantescape=!canescape
  pbPrepareBattle(battle)
  decision=0
  pbBattleAnimation(pbGetWildBattleBGM(species1)) {
     pbSceneStandby {
        decision=battle.pbStartBattle(canlose)
     }
     for i in $Trainer.party
       if true
         (i.makeUnmega rescue nil); (i.makeUnprimal rescue nil); (i.revertOtherForms rescue nil)
       end
     end
     if $PokemonGlobal.partner
       pbHealAll
       for i in $PokemonGlobal.partner[3]
         i.heal
         if i.isMega?
           (i.makeUnmega rescue nil); (i.makeUnprimal rescue nil); (i.revertOtherForms rescue nil)
         end
       end
     end
     if decision==2 || decision==5
       if canlose
         for i in $Trainer.party; i.heal; end
         for i in 0...10
           Graphics.update
         end
#       else
#         $game_system.bgm_unpause
#         $game_system.bgs_unpause
#         Kernel.pbStartOver
       end
     end
     Events.onEndBattle.trigger(nil,decision,canlose)
  }
  Input.update
  pbSet(variable,decision)
  return (decision !=2 && decision !=5)
end



