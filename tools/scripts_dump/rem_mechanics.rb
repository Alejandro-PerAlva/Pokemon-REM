#===============================================================================
# REM_Mechanics — día/noche manual, reglas nocturnas, combates Dominantes 2v1,
# Don Prodigio e intercambio por BST. Reutiliza: 184_Fake_Time (skipToHour,
# NTN_*), 110_PField_Time (PBDayNight), 190_Boss_Fight (pbBossFight, partner),
# 191_Wonder_Trade (TRADING_BLACKLIST), 146 (pbStartTrade).
# Fuente: tools/scripts_dump/rem_mechanics.rb (inyectado por build_scripts.rb)
# Compatible RGSS1 / Ruby 1.8 (sin sintaxis moderna).
#===============================================================================

#-------------------------------------------------------------------------------
# CONFIGURACIÓN
#-------------------------------------------------------------------------------
REM_NIGHT_LEVEL_MULT  = 1.25   # nivel salvaje nocturno x factor (redondeado)
REM_NIGHT_START_HOUR  = 22     # hora a la que salta pbSetNight(true)  (noche: 20-06)
REM_DAY_START_HOUR    = 8      # hora a la que salta pbSetNight(false)
REM_PRODIGIO_BST_SPAN = 30     # ± BST de Don Prodigio (se amplía si no hay candidatos)

class PokemonGlobalMetadata
  attr_accessor :remTimeFrozen
  if method_defined?(:addNewFrameCount)
    alias rem_orig_addNewFrameCount addNewFrameCount
    def addNewFrameCount
      return if @remTimeFrozen        # reloj congelado hasta el siguiente pbSetNight/pbRemTimeFree
      rem_orig_addNewFrameCount
    end
  end
end

class PokemonTemp
  attr_accessor :remMoveTypes          # tipos de movimiento usados por el jugador en el combate actual
  attr_accessor :remDominantMode       # nil o :hp_x2 / :all_x15 / :all_x2 durante un combate Dominante
end

#-------------------------------------------------------------------------------
# 1. DÍA / NOCHE MANUAL  (eventos de cama / descanso)
#   pbSetNight(true|false [,congelar=true])   pbToggleDayNight   pbRemTimeFree
#-------------------------------------------------------------------------------
def pbRemIsNight?
  return PBDayNight.isNight?
end

def pbRemTimeFree
  $PokemonGlobal.remTimeFrozen=false if $PokemonGlobal
end

def pbSetNight(night=true,freeze=true)
  $PokemonGlobal.remTimeFrozen=false
  if night!=PBDayNight.isNight?
    pbFadeOutIn(99999){
      skipToHour(night ? REM_NIGHT_START_HOUR : REM_DAY_START_HOUR)
      pbGetTimeNow                       # aplica los segundos extra
      $game_map.need_refresh=true
      for i in 0...10; Graphics.update; end   # refresca el tinte del mapa
    }
  end
  $PokemonGlobal.remTimeFrozen=freeze ? true : false
  return night
end

def pbToggleDayNight(freeze=true)
  return pbSetNight(!PBDayNight.isNight?,freeze)
end

#-------------------------------------------------------------------------------
# 2. REGLAS NOCTURNAS: nivel x factor y captura prohibida
#-------------------------------------------------------------------------------
Events.onWildPokemonCreate+=proc {|sender,e|
  pkmn=e[0]
  if pkmn && PBDayNight.isNight? && !$PokemonTemp.remDominantMode
    newlevel=[[(pkmn.level*REM_NIGHT_LEVEL_MULT).round,1].max,PBExperience::MAXLEVEL].min
    if newlevel!=pkmn.level
      pkmn.level_cap_level(newlevel)     # setter original: salta el Level_Cap del jugador
      pkmn.resetMoves
      pkmn.calcStats
      pkmn.hp=pkmn.totalhp
    end
  end
}

class << ItemHandlers
  alias rem_orig_triggerBattleUseOnBattler triggerBattleUseOnBattler
  def triggerBattleUseOnBattler(item,battler,scene)
    if pbIsPokeBall?(item)
      if $PokemonTemp.remDominantMode
        scene.pbDisplay(_INTL("¡Un Pokémon Dominante no puede ser capturado! Hay que debilitarlo."))
        return false                      # false = no se gasta la Ball
      end
      if PBDayNight.isNight? && !battler.battle.opponent
        scene.pbDisplay(_INTL("La agresividad nocturna impide capturar al Pokémon."))
        return false
      end
    end
    return rem_orig_triggerBattleUseOnBattler(item,battler,scene)
  end
end

#-------------------------------------------------------------------------------
# 3. COMBATE DOMINANTE 2v1 (jugador + aliado IA contra 1 salvaje)
#   pbDominantBattle(:ONIX,40,:LANCE,"Lance",0,:hp_x2)   -> true si gana
#   boost_mode: :hp_x2 | :all_x15 | :all_x2
#-------------------------------------------------------------------------------
class PokeBattle_Battle
  alias rem_orig_pbStartBattle pbStartBattle
  def pbStartBattle(canlose=false)
    if $PokemonTemp && $PokemonTemp.remDominantMode
      @doublebattle=true                  # 1 + aliado vs 1 Dominante
      @cantescape=true                    # prohibido huir
    end
    $PokemonTemp.remMoveTypes={} if $PokemonTemp
    ret=rem_orig_pbStartBattle(canlose)
    pbPiaCountWin if ret==1 && $PokemonTemp   # misión 4 de Pía: victoria usando movimientos del tipo
    return ret
  end
end

class PokeBattle_Battler
  alias rem_orig_pbInitPokemon pbInitPokemon
  def pbInitPokemon(pkmn,pkmnIndex)
    rem_orig_pbInitPokemon(pkmn,pkmnIndex)
    mode=$PokemonTemp ? $PokemonTemp.remDominantMode : nil
    if mode && (@index%2)==1 && !@battle.opponent    # solo el salvaje (lado rival)
      case mode
      when :hp_x2
        @totalhp*=2; @hp=@totalhp
      when :all_x15, :all_x2
        m=(mode==:all_x2) ? 2.0 : 1.5
        @totalhp=(@totalhp*m).floor; @hp=@totalhp
        @attack=(@attack*m).floor;   @defense=(@defense*m).floor
        @spatk=(@spatk*m).floor;     @spdef=(@spdef*m).floor
        @speed=(@speed*m).floor
      end
    end
  end
end

def pbDominantBattle(species,level,partner_trainer_type,partner_name,partner_party_id,boost_mode=:hp_x2)
  return false if $Trainer.ablePokemonCount==0
  boost_mode=:hp_x2 if ![:hp_x2,:all_x15,:all_x2].include?(boost_mode)
  oldpartner=$PokemonGlobal.partner
  pbRegisterPartner(partner_trainer_type,partner_name,partner_party_id)
  $PokemonTemp.remDominantMode=boost_mode
  ret=false
  begin
    ret=pbBossFight(species,level,0,nil,false,false)   # reutiliza el 2v1 con partner existente
  ensure
    $PokemonTemp.remDominantMode=nil
    $PokemonGlobal.partner=oldpartner
  end
  return ret
end

#-------------------------------------------------------------------------------
# 4. DON PRODIGIO: intercambio por BST similar
#   pbDonProdigio  -> true si hubo intercambio
#-------------------------------------------------------------------------------
module REM_Prodigio
  HM_MOVES=[:CUT,:FLY,:SURF,:STRENGTH,:ROCKSMASH,:WATERFALL,:DIVE,:ROCKCLIMB,:FLASH,:DEFOG,:WHIRLPOOL]
  LEGENDARIES=[144,145,146,150,151,243,244,245,249,250,251,377,378,379,380,381,382,383,
               384,385,386,480,481,482,483,484,485,486,487,488,489,490,491,492,493,494,
               638,639,640,641,642,643,644,645,646,647,648,649,716,717,718,719,720,721]
  @bst=nil

  def self.maxSpecies
    return [PBSpecies.maxValue,721].min
  end

  def self.bst(species)
    if !@bst
      @bst=[0]
      for i in 1..self.maxSpecies
        @bst[i]=PokeBattle_Pokemon.new(i,5).baseStats.inject(0){|s,v| s+v}
      end
    end
    return @bst[species] || 0
  end

  def self.root(species)
    n=0
    loop do
      prev=pbGetPreviousForm(species)
      break if prev==species || n>5
      species=prev; n+=1
    end
    return species
  end

  def self.blacklist
    list=LEGENDARIES.clone
    if defined?(TRADING_BLACKLIST)
      for s in TRADING_BLACKLIST
        list.push(s.is_a?(Symbol) ? (hasConst?(PBSpecies,s) ? getConst(PBSpecies,s) : 0) : s)
      end
    end
    return list
  end

  # Etapa coherente: ya existe a este nivel y su evolución por nivel aún no.
  def self.coherent?(species,level)
    return false if pbGetMinimumLevel(species)>level
    for e in pbGetEvolvedFormData(species)
      return false if e[2]<=self.maxSpecies && pbGetMinimumLevel(e[2])<=level
    end
    return true
  end

  def self.lockedReason(pkmn,index)
    return _INTL("No se pueden intercambiar huevos.") if pkmn.isEgg?
    return _INTL("Ese Pokémon no se puede intercambiar.") if (pkmn.isShadow? rescue false)
    if pkmn.hp>0 && $Trainer.ablePokemonCount<=1
      return _INTL("¡Es tu único Pokémon en condiciones de luchar!")
    end
    for m in HM_MOVES
      next if !hasConst?(PBMoves,m)
      mv=getConst(PBMoves,m)
      next if !pkmn.hasMove?(mv)
      others=0
      for i in 0...$Trainer.party.length
        p=$Trainer.party[i]
        others+=1 if i!=index && p && !p.isEgg? && p.hasMove?(mv)
      end
      return _INTL("{1} es el único que conoce {2}, lo necesitas.",pkmn.name,PBMoves.getName(mv)) if others==0
    end
    return nil
  end

  def self.candidates(pkmn)
    base=self.bst(pkmn.species)
    myroot=self.root(pkmn.species)
    black=self.blacklist
    for span in [REM_PRODIGIO_BST_SPAN,REM_PRODIGIO_BST_SPAN+15,REM_PRODIGIO_BST_SPAN+30]
      list=[]
      for i in 1..self.maxSpecies
        next if black.include?(i) || self.root(i)==myroot
        next if (self.bst(i)-base).abs>span
        next if !self.coherent?(i,pkmn.level)
        list.push(i)
      end
      return list if list.length>0
    end
    return []
  end
end

def pbDonProdigio
  Kernel.pbMessage(_INTL("¡Soy Don Prodigio! Cambio tu Pokémon por otro de poder parecido."))
  return false if !Kernel.pbConfirmMessage(_INTL("¿Quieres hacer un intercambio prodigioso?"))
  idx=-1
  loop do
    chosen=-1
    pbFadeOutIn(99999){
      scene=PokemonScreen_Scene.new
      screen=PokemonScreen.new(scene,$Trainer.party)
      screen.pbStartScene(_INTL("Elige un Pokémon."),false)
      chosen=screen.pbChoosePokemon
      screen.pbEndScene
    }
    return false if chosen<0
    reason=REM_Prodigio.lockedReason($Trainer.party[chosen],chosen)
    if reason
      Kernel.pbMessage(reason)
      next
    end
    idx=chosen
    break
  end
  give=$Trainer.party[idx]
  list=REM_Prodigio.candidates(give)
  if list.length==0
    Kernel.pbMessage(_INTL("Hmm... hoy no tengo nada a la altura de {1}.",give.name))
    return false
  end
  newspecies=list[rand(list.length)]
  return false if !Kernel.pbConfirmMessage(_INTL("¿Entregas a {1} (Nv. {2})?",give.name,give.level))
  pbStartTrade(idx,newspecies,PBSpecies.getName(newspecies),"Don Prodigio")
  Kernel.pbMessage(_INTL("¡Cuídalo mucho!"))
  return true
end

#-------------------------------------------------------------------------------
# 5. MISIONES DE PÍA — 18 iniciales x 4 misiones, un único inicial en foco
#   Switch del menú:  REM_PIA_QUESTS_SWITCH   (ON = aparece "Misiones" en el menú)
#   pbPiaMarkFirst(:CHARMANDER)   inicial elegido al empezar (excluido); si no se
#                                 llama, se detecta solo por el primer Pokémon.
#   pbPiaQuestPanel               abre el panel (el menú de pausa lo llama solo)
#   pbPiaSelect(:SQUIRTLE)        fija el inicial en foco (nil = ninguno)
#   pbClaimPiaStarter([:SQUIRTLE]) entrega un inicial listo (sin parámetro: elige)
# Misiones por inicial (tipo T del inicial): 1 derrotar salvajes T, 2 capturar T,
# 3 evolucionar T, 4 ganar combates usando movimientos T. Solo suma el foco activo.
#-------------------------------------------------------------------------------
REM_PIA_QUESTS_SWITCH = 400
REM_PIA_STARTERS=[
  [:BULBASAUR,:GRASS],[:CHARMANDER,:FIRE],[:SQUIRTLE,:WATER],
  [:CHIKORITA,:GRASS],[:CYNDAQUIL,:FIRE],[:TOTODILE,:WATER],
  [:TREECKO,:GRASS],[:TORCHIC,:FIRE],[:MUDKIP,:WATER],
  [:TURTWIG,:GRASS],[:CHIMCHAR,:FIRE],[:PIPLUP,:WATER],
  [:SNIVY,:GRASS],[:TEPIG,:FIRE],[:OSHAWOTT,:WATER],
  [:CHESPIN,:GRASS],[:FENNEKIN,:FIRE],[:FROAKIE,:WATER]
]
REM_PIA_KINDS=["Derrotar Pokémon salvajes de tipo %s","Capturar Pokémon de tipo %s",
               "Evolucionar Pokémon de tipo %s","Ganar combates usando movimientos %s"]
REM_PIA_TYPENAMES={:GRASS=>"Planta",:FIRE=>"Fuego",:WATER=>"Agua"}

class PokemonGlobalMetadata
  attr_accessor :remPia
end

def pbRemPia
  if !$PokemonGlobal.remPia
    $PokemonGlobal.remPia={:first=>nil,:active=>nil,:ready=>{},:claimed=>{},:prog=>{}}
  end
  return $PokemonGlobal.remPia
end

def pbPiaGoals(sym)            # metas crecen con la generación del trío
  k=pbPiaIndex(sym)/3
  return [10+3*k,3+k,1+k/2,5+k]
end

def pbPiaIndex(sym)
  for i in 0...REM_PIA_STARTERS.length
    return i if REM_PIA_STARTERS[i][0]==sym
  end
  return 0
end

def pbPiaProg(sym)
  d=pbRemPia
  d[:prog][sym]=[0,0,0,0] if !d[:prog][sym]
  return d[:prog][sym]
end

def pbPiaMarkFirst(sym)
  pbRemPia[:first]=sym
  pbRemPia[:active]=nil if pbRemPia[:active]==sym
end

def pbPiaFirst
  d=pbRemPia
  if !d[:first] && $Trainer && $Trainer.party[0]
    r=REM_Prodigio.root($Trainer.party[0].species)
    for s in REM_PIA_STARTERS
      d[:first]=s[0] if hasConst?(PBSpecies,s[0]) && getConst(PBSpecies,s[0])==r
    end
  end
  return d[:first]
end

def pbPiaState(sym)            # :first :claimed :ready :active :idle
  d=pbRemPia
  return :first if pbPiaFirst==sym
  return :claimed if d[:claimed][sym]
  return :ready if d[:ready][sym]
  return :active if d[:active]==sym
  return :idle
end

def pbPiaSelect(sym)
  if sym && [:first,:claimed,:ready].include?(pbPiaState(sym))
    Kernel.pbMessage(_INTL("Ese inicial ya no necesita seguimiento."))
    return false
  end
  pbRemPia[:active]=sym
  return true
end

# kind: 0 derrotar, 1 capturar, 2 evolucionar, 3 victoria con movimientos del tipo
def pbPiaCount(kind,types)     # types = array de símbolos de tipo del Pokémon/movimiento
  d=pbRemPia
  a=d[:active]
  return if !a || !$game_switches[REM_PIA_QUESTS_SWITCH]
  return if d[:ready][a] || d[:claimed][a]
  t=REM_PIA_STARTERS[pbPiaIndex(a)][1]
  return if !types.include?(t)
  goals=pbPiaGoals(a)
  pr=pbPiaProg(a)
  return if pr[kind]>=goals[kind]
  pr[kind]+=1
  if pr[kind]>=goals[kind]
    if (0...4).all?{|i| pr[i]>=goals[i]}
      d[:ready][a]=true; d[:active]=nil
      Kernel.pbMessage(_INTL("¡Misiones de {1} completadas! Pía puede entregártelo.",PBSpecies.getName(getConst(PBSpecies,a))))
    else
      Kernel.pbMessage(_INTL("Misión de Pía cumplida: {1}.",sprintf(REM_PIA_KINDS[kind],REM_PIA_TYPENAMES[t])))
    end
  end
end

def pbRemTypeSyms(*ids)
  ret=[]
  for id in ids
    next if !id || id<0
    for t in [:GRASS,:FIRE,:WATER]
      ret.push(t) if hasConst?(PBTypes,t) && getConst(PBTypes,t)==id
    end
  end
  return ret
end

def pbPiaCountWin
  return if !$PokemonTemp.remMoveTypes
  pbPiaCount(3,$PokemonTemp.remMoveTypes.keys)
end

def pbClaimPiaStarter(sym=nil)
  d=pbRemPia
  ready=REM_PIA_STARTERS.map{|s| s[0]}.select{|s| d[:ready][s] && !d[:claimed][s]}
  if ready.length==0
    Kernel.pbMessage(_INTL("No tienes ningún inicial listo para reclamar."))
    return false
  end
  if !sym
    names=ready.map{|s| PBSpecies.getName(getConst(PBSpecies,s))}
    names.push(_INTL("Cancelar"))
    c=Kernel.pbShowCommands(nil,names,-1)
    return false if c<0 || c>=ready.length
    sym=ready[c]
  end
  return false if !ready.include?(sym)
  d[:claimed][sym]=true
  pbAddPokemon(getConst(PBSpecies,sym),5)
  return true
end

# --- hooks de progreso -------------------------------------------------------
class PokeBattle_Battler
  alias rem_orig_pbFaint pbFaint
  def pbFaint(showMessage=true)
    ret=rem_orig_pbFaint(showMessage)
    if (@index&1)==1 && @battle && !@battle.opponent && @battle.internalbattle
      pbPiaCount(0,pbRemTypeSyms(@type1,@type2))     # misión 1: derrotar salvajes
    end
    return ret
  end

  alias rem_orig_pbUseMove pbUseMove
  def pbUseMove(choice,specialusage=false)
    if (@index&1)==0 && choice && choice[2] && $PokemonTemp && $PokemonTemp.remMoveTypes
      for t in pbRemTypeSyms(choice[2].type)
        $PokemonTemp.remMoveTypes[t]=true
      end
    end
    return rem_orig_pbUseMove(choice,specialusage)
  end
end

class PokeBattle_Battle
  alias rem_orig_pbStorePokemon pbStorePokemon
  def pbStorePokemon(pokemon)
    pbPiaCount(1,pbRemTypeSyms(pokemon.type1,pokemon.type2))   # misión 2: capturar
    return rem_orig_pbStorePokemon(pokemon)
  end
end

class PokemonEvolutionScene
  alias rem_orig_pbEvolution pbEvolution
  def pbEvolution(cancancel=true)
    before=@pokemon.species
    ret=rem_orig_pbEvolution(cancancel)
    if @pokemon.species!=before
      pbPiaCount(2,pbRemTypeSyms(@pokemon.type1,@pokemon.type2))   # misión 3: evolucionar
    end
    return ret
  end
end
