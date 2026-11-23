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
REM_NIGHT_LEVEL_MULT  = 1.5    # nivel salvaje nocturno x factor (redondeo hacia abajo, tope MAXLEVEL)
REM_NIGHT_START_HOUR  = 22     # hora a la que salta pbSetNight(true)  (noche: 20-06)
REM_DAY_START_HOUR    = 8      # hora a la que salta pbSetNight(false)
REM_PRODIGIO_BST_SPAN = 30     # ± BST de Don Prodigio (se amplía si no hay candidatos)

class PBItems
  RELOJ = 720 unless defined?(RELOJ)
end

class PokemonGlobalMetadata
  attr_accessor :remTimeFrozen
  attr_accessor :itemfinderActive
  if method_defined?(:addNewFrameCount)
    alias rem_orig_addNewFrameCount addNewFrameCount
    def addNewFrameCount
      # El tiempo no avanza al inicio del juego hasta que el jugador recibe el Reloj Digital
      return if !($PokemonBag && hasConst?(PBItems,:RELOJ) && $PokemonBag.pbQuantity(getConst(PBItems,:RELOJ))>0)
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

def pbRemAdvanceTime(hours=1, minutes=0)
  secs = hours*3600 + minutes*60
  if defined?(NTN_EXTRASECONDS) && NTN_EXTRASECONDS > 0
    $game_variables[NTN_EXTRASECONDS] += secs
    pbFadeOutIn(99999){
      pbGetTimeNow
      $game_map.need_refresh = true if $game_map
      for i in 0...10; Graphics.update; end
    }
  end
end

ItemHandlers::UseFromBag.add(:RELOJ,proc{|item|
  time = pbGetTimeNow
  h_str = sprintf("%02d:%02d", time.hour, time.min)
  is_night = PBDayNight.isNight?(time)
  state_str = is_night ? _INTL("NOCHE") : _INTL("DÍA")
  sub = is_night ? _INTL("Amanece a las 06:00") : _INTL("Anochece a las 20:00")
  Kernel.pbMessage(_INTL("RELOJ DIGITAL DE ONIRIA\\nHora actual: {1} ({2})\\n{3}\\n\\nCiclo horario:\\n- DÍA: 06:00 a 19:59\\n- NOCHE: 20:00 a 05:59\\n\\nPuedes consultar la hora en cualquier momento abajo a la izquierda en el Menú de Pausa.", h_str, state_str, sub))
  next 1
})

#-------------------------------------------------------------------------------
# 2. REGLAS NOCTURNAS: nivel x factor y captura prohibida
#-------------------------------------------------------------------------------
Events.onWildPokemonCreate+=proc {|sender,e|
  pkmn=e[0]
  if pkmn && PBDayNight.isNight? && !$PokemonTemp.remDominantMode
    newlevel=[[(pkmn.level*REM_NIGHT_LEVEL_MULT).floor,1].max,PBExperience::MAXLEVEL].min
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
#    Y RESTAURACIÓN DE CONSUMIBLES TRAS COMBATE (QoL)
#   pbDominantBattle(:ONIX,40,:LANCE,"Lance",0,:hp_x2)   -> true si gana
#   boost_mode: :hp_x2 | :all_x15 | :all_x2
#-------------------------------------------------------------------------------
class PokeBattle_Battle
  attr_accessor :remBattleInitialItems

  def remRestorePartyItems
    return if !@remBattleInitialItems || !$Trainer || !$Trainer.party
    for pkmn in $Trainer.party
      next if !pkmn
      orig = @remBattleInitialItems[pkmn]
      if orig && orig > 0 && pkmn.item == 0
        pkmn.setItem(orig)
        PBDebug.log("[REM Item Restore] #{pkmn.name} recupero #{PBItems.getName(orig)} tras el combate") rescue nil
      end
    end
  end

  alias rem_orig_pbStartBattle pbStartBattle
  def pbStartBattle(canlose=false)
    if $PokemonTemp && $PokemonTemp.remDominantMode
      @doublebattle=true                  # 1 + aliado vs 1 Dominante
      @cantescape=true                    # prohibido huir
    end
    # Snapshot de objetos equipados del equipo antes de comenzar la batalla
    @remBattleInitialItems = {}
    if $Trainer && $Trainer.party
      for pkmn in $Trainer.party
        next if !pkmn
        @remBattleInitialItems[pkmn] = pkmn.item if pkmn.item > 0
      end
    end
    begin
      ret = rem_orig_pbStartBattle(canlose)
    ensure
      # Restaura consumibles (bayas, bandas focus, etc.) si se gastaron o desarmaron
      remRestorePartyItems
    end
    return ret
  end
end

class PokeBattle_Battler
  alias rem_orig_pbInitPokemon pbInitPokemon
  def pbInitPokemon(pkmn,pkmnIndex)
    rem_orig_pbInitPokemon(pkmn,pkmnIndex)
    @remPiaKO=false
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
# Matriz de objetivos por inicial (todos cuentan a la vez):
#  sym=>[[UNA especie/línea a derrotar x5], [UN Pokémon base a evolucionar x1], tipo a derrotar x10, tipo a capturar x3]
#  La línea del objetivo 1 nunca comparte tipo con el objetivo 3 ni con el propio inicial (cero solapes).
REM_PIA_QUESTS={
  :BULBASAUR=>[[:PIDGEY],[:ODDISH],:PSYCHIC,:POISON],
  :CHARMANDER=>[[:KRABBY],[:GROWLITHE],:ROCK,:DRAGON],
  :SQUIRTLE=>[[:BELLSPROUT],[:HORSEA],:ELECTRIC,:ICE],
  :CHIKORITA=>[[:SPEAROW],[:ROSELIA],:POISON,:FAIRY],
  :CYNDAQUIL=>[[:DIGLETT],[:SLUGMA],:WATER,:GROUND],
  :TOTODILE=>[[:VOLTORB],[:CARVANHA],:GRASS,:BUG],
  :TREECKO=>[[:SCYTHER],[:NINCADA],:ICE,:FLYING],
  :TORCHIC=>[[:PSYDUCK],[:MACHOP],:FLYING,:FIGHTING],
  :MUDKIP=>[[:ODDISH],[:WOOPER],:BUG,:ROCK],
  :TURTWIG=>[[:HOOTHOOT],[:PHANPY],:FIRE,:GRASS],
  :CHIMCHAR=>[[:ABRA],[:MANKEY],:GROUND,:FIRE],
  :PIPLUP=>[[:SHINX],[:ARON],:FIGHTING,:STEEL],
  :SNIVY=>[[:VENIPEDE],[:EKANS],:STEEL,:NORMAL],
  :TEPIG=>[[:ROGGENROLA],[:HOUNDOUR],:DRAGON,:ELECTRIC],
  :OSHAWOTT=>[[:FOONGUS],[:PAWNIARD],:NORMAL,:WATER],
  :CHESPIN=>[[:MURKROW],[:PINECO],:FAIRY,:GHOST],
  :FENNEKIN=>[[:SPINARAK],[:VULPIX],:GHOST,:PSYCHIC],
  :FROAKIE=>[[:SHROOMISH],[:ZORUA],:DARK,:DARK]
}
REM_PIA_GOALS=[5,1,10,3]

class PokemonGlobalMetadata
  attr_accessor :remPia
end

def pbRemPia
  if !$PokemonGlobal.remPia
    $PokemonGlobal.remPia={:first=>nil,:active=>nil,:ready=>{},:claimed=>{},:prog=>{},:v=>2}
  end
  if $PokemonGlobal.remPia[:v]!=2    # versión antigua de los objetivos: contadores nuevos
    $PokemonGlobal.remPia[:prog]={}; $PokemonGlobal.remPia[:v]=2
  end
  return $PokemonGlobal.remPia
end

def pbPiaGoals(sym)            # metas fijas: 5 / 1 / 10 / 3
  return REM_PIA_GOALS.clone
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

def pbPiaSpeciesList(list)
  ret=[]
  for s in list
    ret.push(getConst(PBSpecies,s)) if hasConst?(PBSpecies,s)
  end
  return ret
end

def pbPiaInFamily?(species,list)
  r=REM_Prodigio.root(species)
  for sp in pbPiaSpeciesList(list)
    return true if REM_Prodigio.root(sp)==r
  end
  return false
end

# kind: :defeat (derrotado) / :capture (capturado) / :evolve (evolucionado). Cuenta en paralelo los
# 4 objetivos del inicial en foco; el progreso de cada inicial se conserva al cambiar de foco.
def pbPiaEvent(kind,species,type1,type2)
  d=pbRemPia
  a=d[:active]
  return if !a || !$game_switches[REM_PIA_QUESTS_SWITCH]
  return if d[:ready][a] || d[:claimed][a]
  q=REM_PIA_QUESTS[a]
  return if !q
  hit=[]
  tys=[type1,type2]
  case kind
  when :defeat
    # un KO suma a UN solo objetivo: la especie objetivo (1) tiene prioridad sobre el tipo (3)
    if pbPiaInFamily?(species,q[0])
      hit.push(0)
    elsif hasConst?(PBTypes,q[2]) && tys.include?(getConst(PBTypes,q[2]))
      hit.push(2)
    end
  when :evolve
    hit.push(1) if pbPiaInFamily?(species,q[1])
  when :capture
    hit.push(3) if hasConst?(PBTypes,q[3]) && tys.include?(getConst(PBTypes,q[3]))
  end
  return if hit.length==0
  goals=pbPiaGoals(a)
  pr=pbPiaProg(a)
  for k in hit
    next if pr[k]>=goals[k]
    pr[k]+=1
  end
  if (0...4).all?{|i| pr[i]>=goals[i]}
    d[:ready][a]=true; d[:active]=nil
    Kernel.pbMessage(_INTL("¡Investigación de {1} completada! Ya puedes reclamarlo en Misiones.",PBSpecies.getName(getConst(PBSpecies,a))))
  end
end

# Tipos (ids) de un Battler o de un Pokémon, sin fallar nunca.
def pbRemTypeIds(obj)
  ret=[]
  begin
    obj=obj.pokemon if obj.respond_to?(:pokemon) && !obj.respond_to?(:type1) && obj.pokemon
    ret.push(obj.type1) if obj.respond_to?(:type1)
    ret.push(obj.type2) if obj.respond_to?(:type2)
  rescue
  end
  return ret
end
def pbRemTypeSyms(*ids)   # (compat) ids de tipo -> símbolos
  ret=[]
  begin
    for id in ids.flatten
      next if !id || id.is_a?(Symbol)
      for t in [:GRASS,:FIRE,:WATER]
        ret.push(t) if hasConst?(PBTypes,t) && getConst(PBTypes,t)==id
      end
    end
  rescue
  end
  return ret
end

# Refresca el gráfico del Pokémon acompañante (Following) sin poder fallar nunca.
def pbRemRefreshFollower
  begin
    $PokemonTemp.dependentEvents.refresh_sprite if $PokemonTemp && $PokemonTemp.dependentEvents
  rescue
  end
end

# Entrada segura para los hooks de combate: una comprobación de misión nunca rompe un combate.
def pbPiaHook(kind,obj)
  begin
    sp=obj.species
    t=pbRemTypeIds(obj)
    pbPiaEvent(kind,sp,t[0],t[1])
  rescue
  end
  return nil
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
    if (@index&1)==1 && @battle && @battle.internalbattle && !@remPiaKO
      @remPiaKO=true              # un único recuento por Pokémon derrotado
      pbPiaHook(:defeat,self)     # objetivos 1 y 3: derrotar
    end
    return ret
  end
end

class PokeBattle_Battle
  alias rem_orig_pbStorePokemon pbStorePokemon
  def pbStorePokemon(pokemon)
    pbPiaHook(:capture,pokemon)   # objetivo 4: capturar
    return rem_orig_pbStorePokemon(pokemon)
  end
end

class PokemonEvolutionScene
  alias rem_orig_pbEvolution pbEvolution
  def pbEvolution(cancancel=true)
    before=@pokemon.species
    ret=rem_orig_pbEvolution(cancancel)
    if @pokemon.species!=before
      pbPiaHook(:evolve,@pokemon)   # objetivo 2: evolucionar
      pbRemRefreshFollower          # el acompañante cambia de gráfico al instante
    end
    return ret
  end
end


# Vigilante del acompañante: si cambia la especie del líder (evolución por cualquier vía), refresca su gráfico.
class Game_Map
  alias rem_orig_update_follow update
  def update
    rem_orig_update_follow
    @remFollowTick=(@remFollowTick || 0)+1
    if @remFollowTick>=20
      @remFollowTick=0
      begin
        lead=$Trainer ? $Trainer.party[0] : nil
        key=lead ? [lead.species,lead.isShiny?,lead.isEgg?] : nil
        if key!=@remFollowKey
          @remFollowKey=key
          pbRemRefreshFollower
        end
      rescue
      end
    end
  end
end

#===============================================================================
#===============================================================================
# SERVICIO DE TRANSPORTE AÉREO DE CENTROS POKÉMON (Vuelo de Refugio a Refugio)
#===============================================================================
class PokemonGlobalMetadata
  attr_accessor :remAirTaxiIntroduced
  attr_accessor :remAirTaxiUnlocked
end

def pbRemAirTaxiUnlocked?
  return true if $DEBUG
  return $PokemonGlobal && $PokemonGlobal.remAirTaxiUnlocked
end

def pbRemUnlockAirTaxi
  $PokemonGlobal.remAirTaxiUnlocked = true if $PokemonGlobal
end

def pbRemAirTaxi
  $PokemonGlobal.remAirTaxiIntroduced ||= false
  
  if !$PokemonGlobal.remAirTaxiIntroduced
    Kernel.pbMessage(_INTL("¡Hola! Soy el piloto del Servicio de Transporte Aéreo de Oniria."))
    Kernel.pbMessage(_INTL("Puedo llevarte rápidamente entre los Centros Pokémon de las ciudades y pueblos que ya hayas visitado."))
    Kernel.pbMessage(_INTL("El servicio es completamente gratuito para los entrenadores."))
    $PokemonGlobal.remAirTaxiIntroduced = true
  end
  
  if Kernel.pbConfirmMessage(_INTL("¿Deseas volar a otro Centro Pokémon?"))
    scene = PokemonRegionMapScene.new(-1, false)
    screen = PokemonRegionMap.new(scene)
    ret = screen.pbStartFlyScreen
    if ret
      if ret[0] == $game_map.map_id
        Kernel.pbMessage(_INTL("¡Pero si ya estás aquí! Elige otra ciudad si deseas desplazarte."))
        return false
      end
      
      pbSEPlay("Fly") rescue pbSEPlay("PRSFX- Fly") rescue nil
      Kernel.pbMessage(_INTL("¡Excelente! Prepárate, despegamos hacia nuestro destino..."))
      pbFadeOutIn(99999) {
        Kernel.pbCancelVehicles
        $game_temp.player_new_map_id = ret[0]
        $game_temp.player_new_x = ret[1]
        $game_temp.player_new_y = ret[2]
        $game_temp.player_new_direction = 2
        $scene.transfer_player
        $game_map.autoplay
        $game_map.refresh
      }
      pbEraseEscapePoint
      Kernel.pbMessage(_INTL("¡Aterrizaje completado con éxito! Buen viaje, entrenador."))
      return true
    else
      Kernel.pbMessage(_INTL("Avísame si decides viajar más tarde."))
    end
  else
    Kernel.pbMessage(_INTL("Entendido. Aquí me encontrarás cuando necesites transporte."))
  end
  return false
end

# Menú de Banco de Pruebas (Testing de Sistemas de la Auditoría)
#===============================================================================
def pbDebugTestingMenu
  loop do
    has_inc = ($PokemonBag && $PokemonBag.pbHasItem?(:INCUBADORA)) ? "Sí" : "No"
    egg = $PokemonGlobal ? $PokemonGlobal.egg : nil
    egg_str = egg ? (egg.eggsteps == 0 ? "¡Listo para abrir!" : "#{egg.eggsteps} pasos") : "Vacía"
    has_clock = ($PokemonBag && $PokemonBag.pbHasItem?(:RELOJ)) ? "Sí" : "No"
    t_now = pbGetTimeNow
    time_str = sprintf("%02d:%02d", t_now.hour, t_now.min)
    phase_str = PBDayNight.isNight?(t_now) ? "Noche" : "Día"
    
    cmd = Kernel.pbMessage(
      _INTL("BANCO DE PRUEBAS REM\\n¿Qué sistema deseas verificar?"),
      [
        _INTL("1. Follower a Combate (Sin Ball 1vs1 y Doble) [NUEVO]"),
        _INTL("2. Salón de la Fama Gen 5 Noir [NUEVO]"),
        _INTL("3. Herramientas Clave (Tijeras, Pico, Guantes, Surf) [NUEVO]"),
        _INTL("4. Saco de Dormir Noir (Dormir en ruta y cargas) [NUEVO]"),
        _INTL("5. Transporte Aéreo de Centro Pokémon (Vuelo) [NUEVO]"),
        _INTL("6. Cartel de Ruta (pbRouteSign)"),
        _INTL("7. Incubadora Noir (Huevo, pasos y entrega)"),
        _INTL("8. Equipar Objetos a Pokémon (Icono bajo PS)"),
        _INTL("9. Probar IA Competitiva REM (Simulación de Combate) [NUEVO]"),
        _INTL("10. Preparar / Curar Equipo"),
        _INTL("11. Sistema de Misiones (Pía ON/OFF y Recado de Prueba)"),
        _INTL("12. Reloj Digital y Control Horario ({1} - {2} | Posee: {3}) [NUEVO]", time_str, phase_str, has_clock),
        _INTL("Salir")
      ]
    )
    
    case cmd
    when 0 # 1. Follower a Combate (1vs1 y Doble)
      fol_opts = [
        _INTL("Combate 1vs1 (Follower entra corriendo sin Pokéball)"),
        _INTL("Combate 2vs2 Doble (Follower sin Ball + 2º con Ball)"),
        _INTL("Activar / Reaparecer Follower en mapa"),
        _INTL("Volver")
      ]
      fol_cmd = Kernel.pbMessage(_INTL("PRUEBAS DE FOLLOWER EN COMBATE:\\nElige un modo:"), fol_opts, 0)
      case fol_cmd
      when 0 # 1vs1
        if !$Trainer || $Trainer.party.length == 0
          pbAddPokemon(:RIOLU, 20)
        end
        $Trainer.party[0].heal
        fswitch = defined?(FOLLOWER_SWITCH) ? FOLLOWER_SWITCH : 101
        $game_switches[fswitch] = true
        pbSpawnFollower if defined?(pbSpawnFollower)
        Kernel.pbMessage(_INTL("Iniciando combate 1vs1...\\n¡Observa cómo {1} entra directamente corriendo sin lanzar Pokéball!", $Trainer.party[0].name))
        pbWildBattle(getID(PBSpecies, :ZIGZAGOON), 5)
      when 1 # 2vs2 Doble
        while $Trainer.party.length < 2
          pbAddPokemon(:PIKACHU, 20)
        end
        $Trainer.party[0].heal
        $Trainer.party[1].heal
        fswitch = defined?(FOLLOWER_SWITCH) ? FOLLOWER_SWITCH : 101
        $game_switches[fswitch] = true
        pbSpawnFollower if defined?(pbSpawnFollower)
        Kernel.pbMessage(_INTL("Iniciando combate 2vs2 Doble...\\n¡Observa: {1} (slot 0) entra corriendo sin Ball, y {2} (slot 2) sale lanzado con su Pokéball!", $Trainer.party[0].name, $Trainer.party[1].name))
        p1 = getID(PBSpecies, :PIDGEY)
        p2 = getID(PBSpecies, :RATTATA)
        pbDoubleWildBattle(p1, 5, p2, 5)
      when 2 # Reaparecer follower
        fswitch = defined?(FOLLOWER_SWITCH) ? FOLLOWER_SWITCH : 101
        $game_switches[fswitch] = true
        pbSpawnFollower if defined?(pbSpawnFollower)
        Kernel.pbMessage(_INTL("Follower actualizado en el mapa."))
      end

    when 1 # 2. Salón de la Fama Gen 5 Noir
      if !$Trainer || $Trainer.party.length == 0
        pbAddPokemon(:LUCARIO, 55)
        pbAddPokemon(:GRENINJA, 54)
        pbAddPokemon(:CHARIZARD, 56)
      end
      Kernel.pbMessage(_INTL("Iniciando secuencia cinemática del Salón de la Fama Gen 5 Noir..."))
      pbHallOfFameEntry

    when 2 # 3. Herramientas Clave (Sustituto de MOs)
      has_shears = ($PokemonBag && $PokemonBag.pbHasItem?(:SHEARS)) ? "Sí" : "No"
      has_pickaxe = ($PokemonBag && $PokemonBag.pbHasItem?(:PICKAXE)) ? "Sí" : "No"
      has_gloves = ($PokemonBag && $PokemonBag.pbHasItem?(:GLOVES)) ? "Sí" : "No"
      has_board = ($PokemonBag && $PokemonBag.pbHasItem?(:SURFBOARD)) ? "Sí" : "No"
      
      tool_info = "Tijeras (Corte): #{has_shears} | Pico (Roca): #{has_pickaxe}\nGuantes (Fuerza): #{has_gloves} | Surf (Agua): #{has_board}"
      t_cmd = Kernel.pbMessage(
        _INTL("HERRAMIENTAS DE CAMPO CLAVE (Sustituto de MOs)\\n{1}\\nSelecciona una opción:", tool_info),
        [
          _INTL("Dar las 4 Herramientas Clave a la Mochila"),
          _INTL("Quitar las 4 Herramientas Clave"),
          _INTL("Volver")
        ]
      )
      case t_cmd
      when 0
        $PokemonBag.pbStoreItem(:SHEARS, 1) if hasConst?(PBItems, :SHEARS)
        $PokemonBag.pbStoreItem(:PICKAXE, 1) if hasConst?(PBItems, :PICKAXE)
        $PokemonBag.pbStoreItem(:GLOVES, 1) if hasConst?(PBItems, :GLOVES)
        $PokemonBag.pbStoreItem(:SURFBOARD, 1) if hasConst?(PBItems, :SURFBOARD)
        Kernel.pbMessage(_INTL("¡Has recibido las 4 Herramientas Clave!\\n- Tijeras (Corte de maleza)\\n- Pico (Golpe Roca en rocas agrietadas)\\n- Guantes de Fuerza (Empuje de rocas pesadas)\\n- Tabla de Surf (Navegación en agua)"))
      when 1
        $PokemonBag.pbDeleteItem(:SHEARS, 1) if hasConst?(PBItems, :SHEARS)
        $PokemonBag.pbDeleteItem(:PICKAXE, 1) if hasConst?(PBItems, :PICKAXE)
        $PokemonBag.pbDeleteItem(:GLOVES, 1) if hasConst?(PBItems, :GLOVES)
        $PokemonBag.pbDeleteItem(:SURFBOARD, 1) if hasConst?(PBItems, :SURFBOARD)
        Kernel.pbMessage(_INTL("Se han retirado las 4 Herramientas Clave de tu mochila para probar los diálogos cuando no se tienen los objetos."))
      end

    when 3 # 4. Saco de Dormir Noir
      has_bag = ($PokemonBag && $PokemonBag.pbHasItem?(:SLEEPINGBAG)) ? "Sí" : "No"
      cur_c = pbRemSleepBagCharges
      max_c = pbRemSleepBagMax
      is_n = PBDayNight.isNight? ? "Noche" : "Día"
      
      bag_menu = [
        _INTL("Dar / Quitar Saco de Dormir a la Mochila"),
        _INTL("Alternar Día / Noche (Actualmente: {1})", is_n),
        _INTL("Mejorar Cargas Máximas (+1 hasta 3) [Actual: {1}]", max_c),
        _INTL("Vaciar Cargas a 0 (Probar mensaje de sin cargas)"),
        _INTL("Rellenar Cargas al 100%"),
        _INTL("Volver")
      ]
      b_cmd = Kernel.pbMessage(
        _INTL("SACO DE DORMIR NOIR\\nPosee Saco: {1} | Cargas: {2}/{3} | Estado: {4}\\nSelecciona una prueba:", has_bag, cur_c, max_c, is_n),
        bag_menu, 0
      )
      case b_cmd
      when 0
        if $PokemonBag.pbHasItem?(:SLEEPINGBAG)
          $PokemonBag.pbDeleteItem(:SLEEPINGBAG, 1)
          Kernel.pbMessage(_INTL("Saco de Dormir retirado de la mochila."))
        else
          $PokemonBag.pbStoreItem(:SLEEPINGBAG, 1)
          Kernel.pbMessage(_INTL("¡Saco de Dormir añadido a la mochila!\\nAhora puedes verlo en el Menú de Pausa justo debajo del Pokévial."))
        end
      when 1
        pbToggleDayNight(false)
        Kernel.pbMessage(_INTL("Tiempo cambiado a: {1}.", PBDayNight.isNight? ? "NOCHE" : "DÍA"))
      when 2
        pbRemSleepBagUpgrade
        Kernel.pbMessage(_INTL("¡Cargas máximas del Saco de Dormir mejoradas a {1}/3!", pbRemSleepBagMax))
      when 3
        $PokemonGlobal.remSleepBagCharges = 0 if $PokemonGlobal
        Kernel.pbMessage(_INTL("Cargas del Saco de Dormir fijadas a 0/3 (Vacío)."))
      when 4
        pbRemSleepBagRefill
        Kernel.pbMessage(_INTL("Cargas del Saco de Dormir rellenadas al 100% ({1}/{2}).", pbRemSleepBagCharges, pbRemSleepBagMax))
      end

    when 4 # 5. Transporte Aéreo de Centro Pokémon (Vuelo)
      air_opts = [
        _INTL("Hablar con el Piloto / Iniciar Vuelo (pbRemAirTaxi)"),
        _INTL("Desbloquear Todos los Puntos de Vuelo en el Mapa"),
        _INTL("Volver")
      ]
      air_cmd = Kernel.pbMessage(_INTL("TRANSPORTE AÉREO ONÍRICO (Vuelo)\\nSelecciona una acción:"), air_opts, 0)
      case air_cmd
      when 0
        pbRemAirTaxi
      when 1
        meta = pbLoadMetadata
        count = 0
        for i in 1...meta.length
          if meta[i] && meta[i][MetadataMapPosition]
            $PokemonGlobal.visitedMaps[i] = true
            count += 1
          end
        end
        Kernel.pbMessage(_INTL("¡{1} puntos de mapa marcados como visitados para el vuelo de prueba!", count))
      end

    when 5 # 6. Cartel de Ruta (pbRouteSign)
      sign_opts = [
        _INTL("Probar Ruta 8 Pokes + 2 Pesca (Ej. Costa Sepiola)"),
        _INTL("Probar Ruta 6 Pokes (Ej. Bosque Dioptasa)"),
        _INTL("Probar Ruta 4 Pokes (Ej. Senda del Albor)"),
        _INTL("Alternar Pokédex Vistos (Siluetas Negras vs Color)"),
        _INTL("Probar pbRouteSign de este mapa actual"),
        _INTL("Volver")
      ]
      sign_cmd = Kernel.pbMessage(_INTL("VISOR DE CARTELES DE RUTA (pbRouteSign)\\nSelecciona una prueba:"), sign_opts, 0)
      case sign_cmd
      when 0
        land = [:PIDGEY, :RATTATA, :ZUBAT, :GEODUDE, :MANKEY, :GROWLITHE, :ABRA, :MACHOP].map { |s| getID(PBSpecies, s) }
        fish = [:MAGIKARP, :POLIWAG].map { |s| getID(PBSpecies, s) }
        pbRouteSign(nil, "Ruta 4 - Costa Sepiola", land, fish)
      when 1
        land = [:ZIGZAGOON, :TAILLOW, :WURMPLE, :POOCHYENA, :SHROOMISH, :SLAKOTH].map { |s| getID(PBSpecies, s) }
        pbRouteSign(nil, "Ruta 1 - Bosque Dioptasa", land, [])
      when 2
        land = [:STARLY, :BIDOOF, :KRICKETOT, :SHINX].map { |s| getID(PBSpecies, s) }
        pbRouteSign(nil, "Senda del Albor", land, [])
      when 3
        sample_pokes = [:PIDGEY, :RATTATA, :ZUBAT, :GEODUDE, :MANKEY, :GROWLITHE, :ABRA, :MACHOP, :MAGIKARP, :POLIWAG, :ZIGZAGOON, :TAILLOW]
        any_seen = sample_pokes.any? { |sp| $Trainer && $Trainer.hasSeen?(sp) }
        if any_seen
          sample_pokes.each do |sp|
            id = getID(PBSpecies, sp) rescue 0
            if id > 0 && $Trainer
              $Trainer.seen[id] = false
              $Trainer.owned[id] = false
            end
          end
          Kernel.pbMessage(_INTL("Pokédex de prueba restablecida.\\nLos Pokémon ahora se mostrarán como SILUETAS NEGRAS."))
        else
          sample_pokes.each_with_index do |sp, idx|
            if idx % 2 == 0 && $Trainer
              $Trainer.setSeen(sp)
            end
          end
          Kernel.pbMessage(_INTL("Pokédex de prueba actualizada.\\nLa mitad de los Pokémon ahora están VISTOS (a color) y la otra mitad en SILUETA NEGRA."))
        end
      when 4
        pbRouteSign
      end

    when 6 # 7. Pruebas de Incubadora
      inc_cmd = Kernel.pbMessage(
        _INTL("INCUBADORA NOIR\\nIncubadora: {1} | Huevo: {2}\\nSelecciona una acción:", has_inc, egg_str),
        [
          _INTL("Dar / Quitar Objeto Incubadora"),
          _INTL("Simular Entrega de Huevo (pbGenerateEgg)"),
          _INTL("Fijar Pasos a 0 (Probar botón [C] Eclosionar)"),
          _INTL("Fijar Pasos a 10 (Probar caminar para completar)"),
          _INTL("Vaciar Incubadora"),
          _INTL("Volver")
        ]
      )
      case inc_cmd
      when 0
        if $PokemonBag.pbHasItem?(:INCUBADORA)
          $PokemonBag.pbDeleteItem(:INCUBADORA)
          Kernel.pbMessage(_INTL("Incubadora retirada de la mochila."))
        else
          $PokemonBag.pbStoreItem(:INCUBADORA, 1)
          Kernel.pbMessage(_INTL("¡Incubadora añadida a los Objetos Clave de la mochila!"))
        end
      when 1
        spec = hasConst?(PBSpecies, :RIOLU) ? :RIOLU : (hasConst?(PBSpecies, :TOGEPI) ? :TOGEPI : :EEVEE)
        Kernel.pbMessage(_INTL("Un personaje te ofrece un Huevo de {1}...", PBSpecies.getName(getID(PBSpecies, spec))))
        res = pbGenerateEgg(spec, _INTL("Entregado por el Inspector Tester"))
        Kernel.pbMessage(_INTL("Resultado de la entrega: {1}", res ? "Aceptado y guardado en Incubadora" : "Cancelado / Rechazado"))
      when 2
        if $PokemonGlobal && $PokemonGlobal.egg
          $PokemonGlobal.egg.eggsteps = 0
          Kernel.pbMessage(_INTL("Pasos fijados a 0.\\n¡Abre el menú de Pokémon o la mochila para ver el aviso y abrir el huevo con [C]!"))
        else
          Kernel.pbMessage(_INTL("No hay ningún Huevo en la Incubadora."))
        end
      when 3
        if $PokemonGlobal && $PokemonGlobal.egg
          $PokemonGlobal.egg.eggsteps = 10
          Kernel.pbMessage(_INTL("Pasos fijados a 10.\\nDa 10 pasos en el mapa para que se complete la incubación."))
        else
          Kernel.pbMessage(_INTL("No hay ningún Huevo en la Incubadora."))
        end
      when 4
        $PokemonGlobal.egg = nil
        Kernel.pbMessage(_INTL("Incubadora vaciada."))
      end

    when 7 # 8. Equipar Objetos a Pokémon
      while $Trainer.party.length < 3
        pbAddPokemon(:LUCARIO, 25) if hasConst?(PBSpecies, :LUCARIO)
        pbAddPokemon(:GRENINJA, 25) if hasConst?(PBSpecies, :GRENINJA)
        pbAddPokemon(:CHARIZARD, 25) if hasConst?(PBSpecies, :CHARIZARD)
      end
      items = [:CHOICEBAND, :LEFTOVERS, :SITRUSBERRY, :ASSAULTVEST, :LIFEORB, :EXPSHARE]
      $Trainer.party.each_with_index do |pkmn, i|
        it = items[i % items.length]
        if hasConst?(PBItems, it)
          pkmn.setItem(getID(PBItems, it))
        end
      end
      Kernel.pbMessage(_INTL("¡Objetos equipados en tu equipo (Cinta Elegida, Restos, Baya Zidra...)!\\nAbre el menú de Pokémon para comprobar que sus iconos se muestran alineados justo debajo de 'PS'."))

    when 8 # 9. Probar IA Competitiva REM
      if !$Trainer || $Trainer.party.length == 0
        pbAddPokemon(:LUCARIO, 30)
      end
      for p in $Trainer.party; p.heal; end
      Kernel.pbMessage(_INTL("BANCO DE PRUEBAS IA:\\nVas a luchar contra un Entrenador con la nueva IA Competitiva REM.\\nComprueba: cálculo de 2HKO, anti-suicide setup y castigo si usas Danza Dragón / Danza Espada."))
      # Entrenador de prueba con skill competitivo
      trainer = PokeBattle_Trainer.new("Rival Táctico", PBTrainers::COOLTRAINER_M)
      p1 = PokeBattle_Pokemon.new(:GENGAR, 30, trainer)
      p1.pbLearnMove(:SHADOWBALL)
      p1.pbLearnMove(:SLUDGEBOMB)
      p1.pbLearnMove(:WILLOWISP)
      p1.pbLearnMove(:TAUNT)
      p2 = PokeBattle_Pokemon.new(:LUCARIO, 30, trainer)
      p2.pbLearnMove(:EXTREMESPEED)
      p2.pbLearnMove(:AURASPHERE)
      p2.pbLearnMove(:CLOSECOMBAT)
      p2.pbLearnMove(:SWORDSDANCE)
      trainer.party = [p1, p2]
      
      scene = pbNewBattleScene
      battle = PokeBattle_Battle.new(scene, $Trainer.party, trainer.party, $Trainer, trainer)
      battle.internalbattle = true
      battle.cantescape = true
      pbPrepareBattle(battle)
      decision = 0
      pbBattleAnimation(pbGetTrainerBattleBGM(trainer)) {
        pbSceneStandby {
          decision = battle.pbStartBattle(true)
        }
      }
      for p in $Trainer.party; p.heal; end

    when 9 # 10. Preparar / Curar Equipo
      if $Trainer && $Trainer.party
        for p in $Trainer.party; p.heal; end
      end
      $PokemonBag.pbStoreItem(:SITRUSBERRY, 5) if hasConst?(PBItems, :SITRUSBERRY)
      $PokemonBag.pbStoreItem(:POKEBALL, 20) if hasConst?(PBItems, :POKEBALL)
      Kernel.pbMessage(_INTL("¡Equipo curado al 100%! Bayas Zidra y 20 Poké Balls añadidas a la mochila."))

    when 10 # 11. Sistema de Misiones (Pía ON/OFF y Pruebas)
      sw = defined?(REM_PIA_QUESTS_SWITCH) ? REM_PIA_QUESTS_SWITCH : 400
      pia_on = $game_switches[sw]
      m_cmd = Kernel.pbMessage(
        _INTL("GESTIÓN DE MISIONES REM:\nPía: {1} | Recados activos: {2}", pia_on ? "ACTIVADA" : "DESACTIVADA", pbRemSidequests.length),
        [
          _INTL("Alternar Misiones de Pía (ON/OFF)"),
          _INTL("Añadir Recado de Prueba (Bruno - Procedural 3 Pasos)"),
          _INTL("Avanzar Paso Procedural"),
          _INTL("Fijar Recado de Prueba como LISTO"),
          _INTL("Completar Recado de Prueba"),
          _INTL("Resetear Recados y Auto-Interruptores"),
          _INTL("Volver")
        ]
      )
      case m_cmd
      when 0
        $game_switches[sw] = !$game_switches[sw]
        Kernel.pbMessage(_INTL("Misiones de Pía: {1}.", $game_switches[sw] ? "ACTIVADA (Pestaña visible)" : "DESACTIVADA (Oculta)"))
      when 1
        pbAddSidequest(
          :id => :recado_albor_01,
          :title => _INTL("El encargo del vecino"),
          :location => _INTL("Pueblo Albor"),
          :npc_name => _INTL("Vecino Bruno"),
          :npc_sprite => "npc008",
          :steps => [
            _INTL("El vecino Bruno te ha pedido que revises a fondo los alrededores de Pueblo Albor antes de iniciar tu aventura."),
            _INTL("Comprueba la salida hacia la Ruta 1 al norte de Pueblo Albor y asegúrate de que no haya peligros."),
            _INTL("Has inspeccionado la zona. Vuelve a la casa del vecino Bruno en Pueblo Albor para entregar el recado.")
          ],
          :summary => _INTL("Inspeccionaste los alrededores de Pueblo Albor y la salida a la Ruta 1 por encargo del vecino Bruno, asegurando el camino antes de iniciar tu aventura.")
        )
        $game_self_switches[[3, 14, "A"]] = true
        $game_self_switches[[3, 14, "B"]] = false
        $game_self_switches[[3, 14, "C"]] = false
        $game_map.need_refresh = true if $game_map
        pbRefreshQuestMarkers
        Kernel.pbMessage(_INTL("Recado añadido en Paso 1/3 (Interrogante amarillo)."))
      when 2
        pbAdvanceSidequest(:recado_albor_01)
        st = pbGetSidequestStep(:recado_albor_01)
        if pbRemSidequests[:recado_albor_01] && pbRemSidequests[:recado_albor_01][:state] == :ready
          $game_self_switches[[3, 14, "B"]] = true
          pbRefreshQuestMarkers
          Kernel.pbMessage(_INTL("Avanzado a Paso {1}/3. ¡Misión LISTA PARA ENTREGAR! (Interrogante verde).", st + 1))
        else
          Kernel.pbMessage(_INTL("Avanzado a Paso {1}/3.", st + 1))
        end
      when 3
        pbSetSidequestStep(:recado_albor_01, 2)
        pbSetSidequestState(:recado_albor_01, :ready)
        $game_self_switches[[3, 14, "B"]] = true
        $game_map.need_refresh = true if $game_map
        pbRefreshQuestMarkers
        Kernel.pbMessage(_INTL("Recado fijado como LISTA (Interrogante verde)."))
      when 4
        sum_txt = _INTL("Inspeccionaste los alrededores de Pueblo Albor y la salida a la Ruta 1 por encargo del vecino Bruno, asegurando el camino antes de iniciar tu aventura.")
        pbCompleteSidequest(:recado_albor_01, sum_txt)
        $game_self_switches[[3, 14, "C"]] = true
        $game_map.need_refresh = true if $game_map
        pbRefreshQuestMarkers
        Kernel.pbMessage(_INTL("Recado marcado como COMPLETADA (Sin interrogante)."))
      when 5
        pbRemSidequests.delete(:recado_albor_01)
        $game_self_switches[[3, 14, "A"]] = false
        $game_self_switches[[3, 14, "B"]] = false
        $game_self_switches[[3, 14, "C"]] = false
        $game_map.need_refresh = true if $game_map
        pbRefreshQuestMarkers
        Kernel.pbMessage(_INTL("Recado de prueba y auto-interruptores restablecidos (Interrogante azul)."))
      end

    when 11 # 12. Reloj Digital y Control Horario
      pbRemClockTestMenu

    else
      break
    end
  end
end

#-------------------------------------------------------------------------------
# BANCO DE PRUEBAS: CONTROL HORARIO Y RELOJ DIGITAL
#-------------------------------------------------------------------------------
def pbRemClockTestMenu
  loop do
    t_now = pbGetTimeNow
    time_str = sprintf("%02d:%02d", t_now.hour, t_now.min)
    phase_str = PBDayNight.isNight?(t_now) ? _INTL("NOCHE") : _INTL("DÍA")
    has_clock = ($PokemonBag && hasConst?(PBItems, :RELOJ) && $PokemonBag.pbQuantity(getConst(PBItems, :RELOJ)) > 0)
    clock_txt = has_clock ? _INTL("SÍ (En la Mochila)") : _INTL("NO (Sin reloj)")
    frozen_txt = has_clock ? _INTL("CORRIENDO NORMAL") : _INTL("CONGELADO (A primera hora de la mañana)")

    clk_cmd = Kernel.pbMessage(
      _INTL("CONTROL HORARIO Y RELOJ DIGITAL:\nHora actual: {1} ({2}) | ¿Posees Reloj?: {3}\nFlujo temporal: {4}\n\nElige una opción:"),
      [
        has_clock ? _INTL("1. Quitar Reloj Digital (Empezar sin él / Congelar tiempo)") : _INTL("1. ¡Recibir Reloj Digital! (Activa reloj 88:88 en Menú)"),
        _INTL("2. Avanzar +1 Hora"),
        _INTL("3. Avanzar +3 Horas"),
        _INTL("4. Avanzar +6 Horas"),
        _INTL("5. Saltar a Hora Específica (06:00, 08:00, 14:00, 19:59, 20:00, 00:00)"),
        _INTL("6. Alternar Día / Noche"),
        _INTL("Volver")
      ]
    )
    case clk_cmd
    when 0 # Dar / Quitar Reloj
      if has_clock
        $PokemonBag.pbDeleteItem(getConst(PBItems, :RELOJ), 1)
        Kernel.pbMessage(_INTL("Se ha retirado el Reloj Digital de tu mochila.\n\nComprobaciones:\n1. Abre el menú con la tecla X: verás que el reloj ha desaparecido de abajo a la izquierda.\n2. El tiempo interno vuelve a quedar congelado."))
      else
        Kernel.pbReceiveItem(getConst(PBItems, :RELOJ), 1)
        Kernel.pbMessage(_INTL("¡Has recibido el Reloj Digital!\n\nComprobaciones:\n1. Abre el menú con la tecla X: abajo a la izquierda verás los dígitos 88:88 grandes y centrados con 'DÍA' (amarillo) o 'NOCHE' (azul oscuro) y la previsión solar debajo.\n2. El tiempo interno ahora corre con normalidad."))
      end
    when 1 # +1 hora
      pbRemAdvanceTime(1, 0)
      t_new = pbGetTimeNow
      Kernel.pbMessage(_INTL("Tiempo avanzado +1 hora. Ahora son las {1} ({2}).", sprintf("%02d:%02d", t_new.hour, t_new.min), PBDayNight.isNight?(t_new) ? "NOCHE" : "DÍA"))
    when 2 # +3 horas
      pbRemAdvanceTime(3, 0)
      t_new = pbGetTimeNow
      Kernel.pbMessage(_INTL("Tiempo avanzado +3 horas. Ahora son las {1} ({2}).", sprintf("%02d:%02d", t_new.hour, t_new.min), PBDayNight.isNight?(t_new) ? "NOCHE" : "DÍA"))
    when 3 # +6 horas
      pbRemAdvanceTime(6, 0)
      t_new = pbGetTimeNow
      Kernel.pbMessage(_INTL("Tiempo avanzado +6 horas. Ahora son las {1} ({2}).", sprintf("%02d:%02d", t_new.hour, t_new.min), PBDayNight.isNight?(t_new) ? "NOCHE" : "DÍA"))
    when 4 # Saltar a hora específica
      h_cmd = Kernel.pbMessage(_INTL("Selecciona la hora a la que deseas saltar:"), [
        _INTL("06:00 (Amanecer / Inicio de Día)"),
        _INTL("08:00 (Hora Inicial de Aventura - Tiempo Congelado)"),
        _INTL("14:00 (Mediodía)"),
        _INTL("19:59 (Último minuto de luz diurna)"),
        _INTL("20:00 (Anochecer / Inicio de Noche)"),
        _INTL("00:00 (Medianoche / Noche cerrada)"),
        _INTL("Cancelar")
      ])
      target_hour = nil
      case h_cmd
      when 0 then target_hour = 6
      when 1 then target_hour = 8
      when 2 then target_hour = 14
      when 3 then target_hour = 19
      when 4 then target_hour = 20
      when 5 then target_hour = 0
      end
      if target_hour
        if defined?(skipToHour)
          skipToHour(target_hour)
          pbFadeOutIn(99999){
            pbGetTimeNow
            $game_map.need_refresh = true if $game_map
            for i in 0...10; Graphics.update; end
          }
        else
          t_curr = pbGetTimeNow
          diff = (target_hour - t_curr.hour) % 24
          diff = 24 if diff == 0
          pbRemAdvanceTime(diff, 0)
        end
        t_new = pbGetTimeNow
        Kernel.pbMessage(_INTL("Hora fijada en {1} ({2}).", sprintf("%02d:%02d", t_new.hour, t_new.min), PBDayNight.isNight?(t_new) ? "NOCHE" : "DÍA"))
      end
    when 5 # Alternar Día / Noche
      pbToggleDayNight(false)
      t_new = pbGetTimeNow
      Kernel.pbMessage(_INTL("Ciclo alternado. Ahora son las {1} ({2}).", sprintf("%02d:%02d", t_new.hour, t_new.min), PBDayNight.isNight?(t_new) ? "NOCHE" : "DÍA"))
    else
      break
    end
  end
end

def pbRefreshQuestMarkers
  $game_map.need_refresh = true if $game_map
end

# Diálogos y gestión del NPC de pruebas de recados en Casa del Jugador (Mapa 3, Evento 14)
def pbSidequestNPCDialogue(stage)
  sw = defined?(REM_PIA_QUESTS_SWITCH) ? REM_PIA_QUESTS_SWITCH : 400

  case stage
  when 0
    # Disponible (Interrogante Azul)
    Kernel.pbMessage(_INTL("Vecino Bruno: ¡Hola! Qué alegría verte antes de que salgas de viaje."))
    cmd = Kernel.pbMessage(_INTL("Opciones del vecino:"), [
      _INTL("Reloj Digital y Control Horario (Dar/Quitar y Cambiar hora) [NUEVO]"),
      _INTL("Banco de Pruebas General (Follower, Vuelo, IA, Herramientas...)"),
      _INTL("Aceptar encargo del vecino (Procedural 3 pasos)"),
      _INTL("Alternar Misiones de Pía (ON / OFF)"),
      _INTL("Ahora no")
    ], 0)
    case cmd
    when 0
      pbRemClockTestMenu
    when 1
      pbDebugTestingMenu
    when 2
      pbAddSidequest(
        :id => :recado_albor_01,
        :title => _INTL("El encargo del vecino"),
        :location => _INTL("Pueblo Albor"),
        :npc_name => _INTL("Vecino Bruno"),
        :npc_sprite => "npc008",
        :steps => [
          _INTL("El vecino Bruno te ha pedido que revises a fondo los alrededores de Pueblo Albor antes de iniciar tu aventura."),
          _INTL("Comprueba la salida hacia la Ruta 1 al norte de Pueblo Albor y asegúrate de que no haya peligros."),
          _INTL("Has inspeccionado la zona. Vuelve a la casa del vecino Bruno en Pueblo Albor para entregar el recado.")
        ],
        :summary => _INTL("Inspeccionaste los alrededores de Pueblo Albor y la salida a la Ruta 1 por encargo del vecino Bruno, asegurando el camino antes de iniciar tu aventura.")
      )
      $game_self_switches[[3, 14, "A"]] = true
      $game_self_switches[[3, 14, "B"]] = false
      $game_self_switches[[3, 14, "C"]] = false
      $game_map.need_refresh = true if $game_map
      pbRefreshQuestMarkers
      Kernel.pbMessage(_INTL("¡Has aceptado la misión '\\c[1]El encargo del vecino\\c[0]'!"))
      Kernel.pbMessage(_INTL("Observa cómo el interrogante sobre el vecino ahora es \\c[2]AMARILLO\\c[0] (En curso)."))
      Kernel.pbMessage(_INTL("Abre el menú de Misiones para consultar los detalles."))
    when 3
      $game_switches[sw] = !$game_switches[sw]
      st = $game_switches[sw] ? "ACTIVADA (Pestaña Pía visible en el menú)" : "DESACTIVADA (Pestaña Pía oculta)"
      Kernel.pbMessage(_INTL("Misiones de Pía: {1}.", st))
    end

  when 1
    # En curso (Interrogante Amarillo)
    cur_step = pbGetSidequestStep(:recado_albor_01)
    Kernel.pbMessage(_INTL("Vecino Bruno: ¿Cómo va ese encargo?"))
    if cur_step == 0
      Kernel.pbMessage(_INTL("Recuerda revisar primero los alrededores inmediatos de Pueblo Albor."))
    else
      Kernel.pbMessage(_INTL("Recuerda echar un ojo a la salida hacia la Ruta 1 antes de dar por cerrada la inspección."))
    end
    cmd = Kernel.pbMessage(_INTL("Gestión de misión (En curso):"), [
      _INTL("Reloj Digital y Control Horario (Dar/Quitar y Cambiar hora) [NUEVO]"),
      _INTL("Banco de Pruebas General"),
      _INTL("[Procedural] Actualizar al siguiente objetivo"),
      _INTL("[Simular] Cumplir todo (Lista para entregar)"),
      _INTL("Alternar Misiones de Pía (ON / OFF)"),
      _INTL("Volver")
    ], 0)
    case cmd
    when 0
      pbRemClockTestMenu
    when 1
      pbDebugTestingMenu
    when 2
      if cur_step < 1
        pbAdvanceSidequest(:recado_albor_01)
        pbRefreshQuestMarkers
        Kernel.pbMessage(_INTL("¡Objetivo de la misión actualizado!"))
        Kernel.pbMessage(_INTL("El cuaderno ahora muestra la nueva instrucción: revisar la salida a la Ruta 1."))
      else
        pbAdvanceSidequest(:recado_albor_01)
        $game_self_switches[[3, 14, "B"]] = true
        $game_map.need_refresh = true if $game_map
        pbRefreshQuestMarkers
        Kernel.pbMessage(_INTL("¡Has completado todos los pasos previos!"))
        Kernel.pbMessage(_INTL("Observa cómo el interrogante ahora es \\c[3]VERDE\\c[0] (Lista para entregar)."))
        Kernel.pbMessage(_INTL("Habla de nuevo con Bruno para entregarla y recibir tu recompensa sorpresa."))
      end
    when 3
      pbSetSidequestStep(:recado_albor_01, 2)
      pbSetSidequestState(:recado_albor_01, :ready)
      $game_self_switches[[3, 14, "B"]] = true
      $game_map.need_refresh = true if $game_map
      pbRefreshQuestMarkers
      Kernel.pbMessage(_INTL("¡Has cumplido el objetivo de '\\c[1]El encargo del vecino\\c[0]'!"))
      Kernel.pbMessage(_INTL("Observa cómo el interrogante ahora es \\c[3]VERDE\\c[0] (Lista para entregar)."))
      Kernel.pbMessage(_INTL("Vuelve a hablar con Bruno para entregarla y recibir tu recompensa sorpresa."))
    when 4
      $game_switches[sw] = !$game_switches[sw]
      st = $game_switches[sw] ? "ACTIVADA (Pestaña Pía visible en el menú)" : "DESACTIVADA (Pestaña Pía oculta)"
      Kernel.pbMessage(_INTL("Misiones de Pía: {1}.", st))
    end

  when 2
    # Lista para entregar (Interrogante Verde)
    Kernel.pbMessage(_INTL("Vecino Bruno: ¡Has vuelto! Y veo que has cumplido la tarea a la perfección."))
    cmd = Kernel.pbMessage(_INTL("Opciones del vecino:"), [
      _INTL("Entregar misión y reclamar recompensa"),
      _INTL("Reloj Digital y Control Horario [NUEVO]"),
      _INTL("Banco de Pruebas General"),
      _INTL("Alternar Misiones de Pía (ON / OFF)"),
      _INTL("Esperar un momento")
    ], 0)
    case cmd
    when 0
      Kernel.pbMessage(_INTL("Vecino Bruno: ¡Muchísimas gracias! Toma esto como agradecimiento."))
      Kernel.pbReceiveItem(PBItems::GREATBALL, 5)
      sum_txt = _INTL("Inspeccionaste los alrededores de Pueblo Albor y la salida a la Ruta 1 por encargo del vecino Bruno, asegurando el camino antes de iniciar tu aventura.")
      pbCompleteSidequest(:recado_albor_01, sum_txt)
      $game_self_switches[[3, 14, "C"]] = true
      $game_map.need_refresh = true if $game_map
      pbRefreshQuestMarkers
      Kernel.pbMessage(_INTL("¡Misión completada con éxito!"))
      Kernel.pbMessage(_INTL("El interrogante ha desaparecido porque ya no hay tareas pendientes."))
      Kernel.pbMessage(_INTL("La misión ahora figura al final de tu lista como '\\c[3]COMPLETADA\\c[0]'."))
      Kernel.pbMessage(_INTL("Recuerda que en el menú de Misiones puedes pulsar [D] para ocultarla o mostrarla."))
    when 1
      pbRemClockTestMenu
    when 2
      pbDebugTestingMenu
    when 3
      $game_switches[sw] = !$game_switches[sw]
      st = $game_switches[sw] ? "ACTIVADA (Pestaña Pía visible en el menú)" : "DESACTIVADA (Pestaña Pía oculta)"
      Kernel.pbMessage(_INTL("Misiones de Pía: {1}.", st))
    end

  when 3
    # Completada (Sin interrogante)
    Kernel.pbMessage(_INTL("Vecino Bruno: ¡Muchas gracias por tu ayuda con aquel encargo! Eres un entrenador con gran futuro."))
    cmd = Kernel.pbMessage(_INTL("Opciones del vecino:"), [
      _INTL("Reloj Digital y Control Horario (Dar/Quitar y Cambiar hora) [NUEVO]"),
      _INTL("Banco de Pruebas General"),
      _INTL("[Reiniciar] Volver a probar la misión"),
      _INTL("Alternar pestaña Pía (ON / OFF)"),
      _INTL("Charla normal"),
      _INTL("Salir")
    ], 0)
    case cmd
    when 0
      pbRemClockTestMenu
    when 1
      pbDebugTestingMenu
    when 2
      $game_self_switches[[3, 14, "A"]] = false
      $game_self_switches[[3, 14, "B"]] = false
      $game_self_switches[[3, 14, "C"]] = false
      $game_map.need_refresh = true if $game_map
      pbRemSidequests.delete(:recado_albor_01)
      pbRefreshQuestMarkers
      Kernel.pbMessage(_INTL("¡Misión y estados de prueba reiniciados! El interrogante azul vuelve a estar visible."))
    when 3
      $game_switches[sw] = !$game_switches[sw]
      st = $game_switches[sw] ? "ACTIVADA (Pestaña Pía visible en el menú)" : "DESACTIVADA (Pestaña Pía oculta)"
      Kernel.pbMessage(_INTL("Misiones de Pía: {1}.", st))
    when 4
      Kernel.pbMessage(_INTL("Vecino Bruno: Los caminos fuera de Pueblo Albor son peligrosos. ¡Lleva siempre a tus Pokémon preparados!"))
    end
  end
end

# Inyección dinámica del NPC de prueba en la Habitación del Jugador (Mapa 3, Pueblo Albor)
def pbRemEnsureTesterEvent
  return false if !$game_map || $game_map.map_id != 3
  return false if $game_map.events.has_key?(14) # Ya existe físicamente en Data/Map003.rxdata
  if !$game_map.events.has_key?(999)
    rpg_ev = RPG::Event.new(33, 9)
    rpg_ev.id = 999
    rpg_ev.x = 33
    rpg_ev.y = 9
    rpg_ev.name = "Tester"
    
    p0 = RPG::Event::Page.new
    p0.condition = RPG::Event::Page::Condition.new
    p0.trigger = 0 # Action button
    p0.through = false
    
    p0.graphic.character_name = "npc008"
    p0.graphic.direction = 8 # Mirando hacia arriba, hacia el jugador en (33, 8)
    p0.graphic.pattern = 0
    p0.graphic.opacity = 255
    p0.graphic.blend_type = 0
    
    p0.list = [
      RPG::EventCommand.new(108, 0, ["quest_marker blue"]),
      RPG::EventCommand.new(108, 0, ["255"]),
      RPG::EventCommand.new(108, 0, ["true"]),
      RPG::EventCommand.new(108, 0, ["false"]),
      RPG::EventCommand.new(355, 0, ["pbDebugTestingMenu"]),
      RPG::EventCommand.new(0, 0, [])
    ]
    rpg_ev.pages = [p0]
    
    ev = Game_Event.new(3, rpg_ev, $game_map)
    $game_map.events[999] = ev
    return true
  end
  return false
end

# Inyección dinámica del Entrenador de prueba en la Habitación del Jugador (Mapa 3, Pueblo Albor)
def pbRemEnsureTrainerTesterEvent
  return false if !$game_map || $game_map.map_id != 3
  if !$game_map.events.has_key?(998)
    rpg_ev = RPG::Event.new(25, 13)
    rpg_ev.id = 998
    rpg_ev.x = 25
    rpg_ev.y = 13
    rpg_ev.name = "Trainer(3)" # Entrenador con visión de 3 casillas hacia la izquierda
    
    # Página 1: Buscando pelea
    p0 = RPG::Event::Page.new
    p0.condition = RPG::Event::Page::Condition.new
    p0.trigger = 2 # Event Touch
    p0.through = false
    
    p0.graphic.character_name = "npc001"
    p0.graphic.direction = 4 # Mirando a la izquierda (hacia la zona donde pasa el jugador)
    p0.graphic.pattern = 0
    p0.graphic.opacity = 255
    p0.graphic.blend_type = 0
    
    p0.list = [
      RPG::EventCommand.new(355, 0, ["Kernel.pbNoticePlayer(get_character(0))"]),
      RPG::EventCommand.new(101, 0, ["¡Nuestras miradas se han cruzado! ¡A luchar!"]),
      RPG::EventCommand.new(355, 0, ["pbTrainerTesterBattle"]),
      RPG::EventCommand.new(0, 0, [])
    ]

    # Página 2: Derrotado (Self Switch A encendido)
    p1 = RPG::Event::Page.new
    p1.condition = RPG::Event::Page::Condition.new
    p1.condition.self_switch_valid = true
    p1.condition.self_switch_ch = "A"
    p1.trigger = 0 # Action Button
    p1.through = false

    p1.graphic.character_name = "npc001"
    p1.graphic.direction = 4 # Mirando a la izquierda
    p1.graphic.pattern = 0
    p1.graphic.opacity = 255
    p1.graphic.blend_type = 0

    p1.list = [
      RPG::EventCommand.new(355, 0, ["pbTrainerTesterDefeatedDialogue"]),
      RPG::EventCommand.new(0, 0, [])
    ]

    rpg_ev.pages = [p0, p1]
    
    ev = Game_Event.new(3, rpg_ev, $game_map)
    $game_map.events[998] = ev
    return true
  end
  return false
end

def pbTrainerTesterBattle
  Kernel.pbMessage(_INTL("Joven Marcos: ¡Demuéstrame el poder de tu equipo!"))
  if pbTrainerBattle(PBTrainers::YOUNGSTER, "Ben", _INTL("¡Menuda paliza me has dado!"), false, 0)
    $game_self_switches[[3, 998, "A"]] = true
    $game_map.need_refresh = true if $game_map
    Kernel.pbMessage(_INTL("Joven Marcos: ¡Increíble! Ahora que me has derrotado, las barras de alerta ya no se activarán conmigo."))
  end
end

def pbTrainerTesterDefeatedDialogue
  cmd = Kernel.pbMessage(_INTL("Joven Marcos: ¡Buen combate el de antes!"), [
    _INTL("Charla normal"),
    _INTL("Reiniciar alerta (para volver a probar las barras)"),
    _INTL("Salir")
  ], 0)
  if cmd == 1
    $game_self_switches[[3, 998, "A"]] = false
    $game_map.need_refresh = true if $game_map
    Kernel.pbMessage(_INTL("Joven Marcos: ¡Modo alerta reactivado! Aléjate y vuelve a acercarte para ver las barras cinematográficas."))
  end
end

#===============================================================================
#  SISTEMA DE BARRAS CINEMÁTICAS DE ALERTA DE ENTRENADOR (Sol y Luna / Añil)
#===============================================================================
module TrainerSensor
  RANGE_BARS_TRAINER = 4 # Distancia a la línea de visión para activar aviso
  BAR_SPEED          = 6 # Velocidad de deslizamiento en píxeles por frame
  BAR_BASE_OPACITY   = 160

  @top = nil
  @bottom = nil
  @triggered = false
  @current_dist = 4

  def self.bar_height
    return (Graphics.height / 8).round # 48 px en 384p
  end

  def self.init_sprites
    return if @top && !@top.disposed?
    h = bar_height
    
    # Barra superior
    @top = Sprite.new
    @top.z = 9999
    @top.bitmap = Bitmap.new(Graphics.width, h)
    @top.bitmap.fill_rect(0, 0, Graphics.width, h, Color.new(0, 0, 0, BAR_BASE_OPACITY))
    @top.bitmap.fill_rect(0, h - 2, Graphics.width, 2, Color.new(0, 0, 0, [BAR_BASE_OPACITY + 50, 255].min))
    @top.y = -h
    @top.visible = true

    # Barra inferior
    @bottom = Sprite.new
    @bottom.z = 9999
    @bottom.bitmap = Bitmap.new(Graphics.width, h)
    @bottom.bitmap.fill_rect(0, 0, Graphics.width, h, Color.new(0, 0, 0, BAR_BASE_OPACITY))
    @bottom.bitmap.fill_rect(0, 0, Graphics.width, 2, Color.new(0, 0, 0, [BAR_BASE_OPACITY + 50, 255].min))
    @bottom.y = Graphics.height
    @bottom.visible = true
  end

  def self.dispose
    if @top && !@top.disposed?
      @top.bitmap.dispose if @top.bitmap && !@top.bitmap.disposed?
      @top.dispose
      @top = nil
    end
    if @bottom && !@bottom.disposed?
      @bottom.bitmap.dispose if @bottom.bitmap && !@bottom.bitmap.disposed?
      @bottom.dispose
      @bottom = nil
    end
    @triggered = false
  end

  def self.show(dist)
    init_sprites
    @triggered = true
    if @current_dist != dist
      @current_dist = dist
      if @top && @top.bitmap && !@top.bitmap.disposed?
        alpha = [[120 + (4 - dist) * 28, 120].max, 220].min
        h = bar_height
        @top.bitmap.fill_rect(0, 0, Graphics.width, h, Color.new(0, 0, 0, alpha))
        @top.bitmap.fill_rect(0, h - 2, Graphics.width, 2, Color.new(0, 0, 0, [alpha + 35, 255].min))
        @bottom.bitmap.fill_rect(0, 0, Graphics.width, h, Color.new(0, 0, 0, alpha))
        @bottom.bitmap.fill_rect(0, 0, Graphics.width, 2, Color.new(0, 0, 0, [alpha + 35, 255].min))
      end
    end
  end

  def self.hide
    @triggered = false
  end

  def self.update
    return if !@top || @top.disposed? || !@bottom || @bottom.disposed?
    h = bar_height
    
    is_busy = ($game_temp && $game_temp.message_window_showing) ||
              ($game_system && $game_system.map_interpreter && $game_system.map_interpreter.running?)
    
    want_show = @triggered && !is_busy

    if want_show
      if @top.y < 0
        @top.y = [@top.y + BAR_SPEED, 0].min
      end
      target_bottom = Graphics.height - h
      if @bottom.y > target_bottom
        @bottom.y = [@bottom.y - BAR_SPEED, target_bottom].max
      end
    else
      if @top.y > -h
        @top.y = [@top.y - BAR_SPEED, -h].max
      end
      if @bottom.y < Graphics.height
        @bottom.y = [@bottom.y + BAR_SPEED, Graphics.height].min
      end
    end
  end
end

def pbUpdateTrainerWarningBars
  return if !$game_map || !$game_player
  
  if ($game_system && $game_system.map_interpreter && $game_system.map_interpreter.running?) ||
     ($game_temp && $game_temp.message_window_showing)
    TrainerSensor.hide
    TrainerSensor.update
    return
  end

  closest_dist = TrainerSensor::RANGE_BARS_TRAINER + 1

  for event in $game_map.events.values
    next if !event
    next if !event.name[/^Trainer\((\d+)\)$/i]
    next if $game_self_switches[[$game_map.map_id, event.id, "A"]] == true
    next if event.transparent || event.opacity == 0

    range = $~[1].to_i
    range = 3 if range <= 0
    dir = event.direction
    dx = (dir == 6 ? 1 : dir == 4 ? -1 : 0)
    dy = (dir == 2 ? 1 : dir == 8 ? -1 : 0)

    for i in 0..range
      target_x = event.x + (dx * i)
      target_y = event.y + (dy * i)
      
      if i > 0 && !event.passable?(target_x - dx, target_y - dy, dir)
        break
      end
      
      dist = ($game_player.x - target_x).abs + ($game_player.y - target_y).abs
      if dist < closest_dist
        closest_dist = dist
      end
    end
  end

  if closest_dist <= TrainerSensor::RANGE_BARS_TRAINER
    TrainerSensor.show(closest_dist)
  else
    TrainerSensor.hide
  end
  TrainerSensor.update
end

class Game_Map
  alias rem_setup_debug_tester setup unless method_defined?(:rem_setup_debug_tester)
  def setup(map_id)
    rem_setup_debug_tester(map_id)
    if map_id == 3
      pbRemEnsureTesterEvent
      pbRemEnsureTrainerTesterEvent
    end
  end
end

class Scene_Map
  alias rem_createSpritesets_debug createSpritesets unless method_defined?(:rem_createSpritesets_debug)
  def createSpritesets
    if $game_map && $game_map.map_id == 3
      pbRemEnsureTesterEvent
      pbRemEnsureTrainerTesterEvent
    end
    rem_createSpritesets_debug
  end

  alias rem_update_debug_tester update unless method_defined?(:rem_update_debug_tester)
  def update
    if $game_map && $game_map.map_id == 3
      if !$game_map.events.has_key?(998) && pbRemEnsureTrainerTesterEvent
        disposeSpritesets
        createSpritesets
      elsif !$game_map.events.has_key?(999) && pbRemEnsureTesterEvent
        disposeSpritesets
        createSpritesets
      end
    end
    rem_update_debug_tester
    pbUpdateTrainerWarningBars
  end

  alias rem_bars_main main unless method_defined?(:rem_bars_main)
  def main
    rem_bars_main
    TrainerSensor.dispose
  end
end



#===============================================================================
# 6. POKE AL EQUIPO (Jonas930 / Clara - Portado de Pokémon Berilo)
# Si el equipo está lleno (6) y capturas o recibes un Pokémon, permite
# enviarlo al equipo eligiendo qué miembro enviar al PC en su lugar.
#===============================================================================
module PokeBattle_BattleCommon
  def pbStorePokemon(pokemon)
    if !(pokemon.isShadow? rescue false)
      if pbDisplayConfirm(_INTL("¿Quieres ponerle un mote a {1}?", pokemon.name))
        species = PBSpecies.getName(pokemon.species)
        nickname = @scene.pbNameEntry(_INTL("¿Mote de {1}?", species), pokemon)
        pokemon.name = nickname if nickname != ""
      end
    end
    if self.pbPlayer.party.length < 6
      self.pbPlayer.party[self.pbPlayer.party.length] = pokemon
      return
    else
      pokemon2 = -1
      if pbDisplayConfirm(_INTL("¿Te gustaría añadir a {1} a tu equipo?", pokemon.name))
        pbDisplayPaused(_INTL("Selecciona un Pokémon para enviar al PC."))
        pbChoosePokemon(1, 2)
        poke = pbGet(1)
        if poke != -1
          pokemon2 = pokemon
          pokemon = self.pbPlayer.party[poke]
          if pbRemovePokemonAt(poke)
            self.pbPlayer.party[self.pbPlayer.party.length] = pokemon2
          else
            Kernel.pbMessage(_INTL("{1} no puede intercambiarse", pokemon.name))
            return
          end
        end
      end
      oldcurbox = @peer.pbCurrentBox()
      storedbox = @peer.pbStorePokemon(self.pbPlayer, pokemon)
      creator = @peer.pbGetStorageCreator()
      return if storedbox < 0
      curboxname = @peer.pbBoxName(oldcurbox)
      boxname = @peer.pbBoxName(storedbox)
      if storedbox != oldcurbox
        if creator
          pbDisplayPaused(_INTL("La caja \"{1}\" del PC de {2} está llena.", curboxname, creator))
        else
          pbDisplayPaused(_INTL("La caja \"{1}\" del PC de Alguien está llena.", curboxname))
        end
        pbDisplayPaused(_INTL("{1} fue transferido a la caja \"{2}\".", pokemon.name, boxname))
      else
        if creator
          pbDisplayPaused(_INTL("{1} fue transferido a la PC de {2}.", pokemon.name, creator))
        else
          pbDisplayPaused(_INTL("{1} fue transferido a la PC de Alguien.", pokemon.name))
        end
        pbDisplayPaused(_INTL("Fue guardado en la caja \"{1}\".", boxname))
      end
      if pokemon2 != -1
        pbSEPlay("PokemonGet")
        if pokemon2.isEgg?
          pbDisplayPaused(_INTL("¡Has añadido el huevo a tu equipo!"))
        else
          pbDisplayPaused(_INTL("¡{1} se une al equipo!\1", pokemon2.name))
        end
      end
    end
  end
end

def pbStorePokemon(pokemon)
  if pbBoxesFull?
    Kernel.pbMessage(_INTL("¡No hay más espacio para Pokémon!\1"))
    Kernel.pbMessage(_INTL("¡Las cajas del PC están llenas!"))
    return false
  end
  pokemon.pbRecordFirstMoves
  if $Trainer.party.length < 6
    $Trainer.party[$Trainer.party.length] = pokemon
    return true
  else
    pokemon2 = -1
    ret = false
    if pokemon.isEgg?
      ret = Kernel.pbConfirmMessageSerious(_INTL("¿Te gustaría añadir el huevo a tu equipo?"))
    else
      ret = Kernel.pbConfirmMessageSerious(_INTL("¿Te gustaría añadir a {1} a tu equipo?", pokemon.name))
    end
    if ret
      Kernel.pbMessage(_INTL("Selecciona un Pokémon para enviar al PC."))
      pbChoosePokemon(1, 2)
      poke = pbGet(1)
      if poke != -1
        pokemon2 = pokemon
        pokemon = $Trainer.party[poke]
        if pbRemovePokemonAt(poke)
          $Trainer.party[$Trainer.party.length] = pokemon2
        else
          Kernel.pbMessage(_INTL("{1} no puede salir del equipo", pokemon.name))
          return false
        end
      end
    end
    ret = false
    oldcurbox = $PokemonStorage.currentBox
    storedbox = $PokemonStorage.pbStoreCaught(pokemon)
    curboxname = $PokemonStorage[oldcurbox].name
    boxname = $PokemonStorage[storedbox].name
    creator = nil
    creator = Kernel.pbGetStorageCreator if $PokemonGlobal.seenStorageCreator
    pokeName = pokemon.isEgg? ? _INTL("El huevo") : pokemon.name
    if storedbox != oldcurbox
      if creator
        Kernel.pbMessage(_INTL("La caja \"{1}\" del PC de {2} está llena.", curboxname, creator))
      else
        Kernel.pbMessage(_INTL("La caja \"{1}\" del PC de Alguien está llena.", curboxname))
      end
      Kernel.pbMessage(_INTL("{1} fue transferido a la caja \"{2}\".", pokeName, boxname))
    else
      if creator
        Kernel.pbMessage(_INTL("{1} fue transferido a la PC de {2}.", pokeName, creator))
      else
        Kernel.pbMessage(_INTL("{1} fue transferido a la PC de Alguien.", pokeName))
      end
      Kernel.pbMessage(_INTL("Fue guardado en la caja \"{1}\".", boxname))
      ret = true
    end
    if pokemon2 != -1
      pbSEPlay("PokemonGet")
      if pokemon2.isEgg?
        Kernel.pbMessage(_INTL("¡Has añadido el huevo a tu equipo!"))
      else
        Kernel.pbMessage(_INTL("¡{1} se une al equipo!\1", pokeName))
      end
      ret = true
    end
  end
  return ret
end

#===============================================================================
# 7. MENOS LAG - OPTIMIZACIÓN BUSH DEPTH (Portado de Realidea / Essentials v19)
# Evita recalcular hierba alta y profundidad en cada frame gráfico inútilmente.
# Solo lo recalcula al iniciar o terminar un paso.
#===============================================================================
class Game_Character
  def bush_depth
    return @bush_depth || 0
  end

  def calculate_bush_depth
    if @tile_id > 0 || @always_on_top || jumping?
      @bush_depth = 0
    else
      deep_bush = regular_bush = false
      xbehind = @x + (@direction == 4 ? 1 : @direction == 6 ? -1 : 0)
      ybehind = @y + (@direction == 8 ? 1 : @direction == 2 ? -1 : 0)
      this_map = (self.map.valid?(@x, @y)) ? [self.map, @x, @y] : $MapFactory.getNewMap(@x, @y)
      if this_map && this_map[0].deepBush?(this_map[1], this_map[2]) && self.map.deepBush?(xbehind, ybehind)
        @bush_depth = Game_Map::TILEHEIGHT
      elsif this_map && this_map[0].bush?(this_map[1], this_map[2])
        @bush_depth = 12
      else
        @bush_depth = 0
      end
    end
  end

  alias rem_hotfixes_update update
  def update
    @stopped_last_frame = @stopped_this_frame
    rem_hotfixes_update
  end

  alias rem_hotfixes_update_move update_move
  def update_move
    rem_hotfixes_update_move
    if !jumping?
      calculate_bush_depth
      @stopped_this_frame = true
    elsif !@moved_last_frame || @stopped_last_frame
      calculate_bush_depth
      @stopped_this_frame = false
    end
  end

  alias rem_hotfixes_update_stop update_stop
  def update_stop
    rem_hotfixes_update_stop
    @stopped_this_frame = false
  end
end

class Game_Player < Game_Character
  def bush_depth
    return @bush_depth || 0
  end
end

#===============================================================================
# 8. FOLLOWER ENTRA EN COMBATE SIN POKÉBALL (Single y Double Battle)
# El primer Pokémon que acompaña al jugador entra corriendo directamente al
# campo de batalla sin lanzar Pokéball ni sonido de recall.
# En combates dobles: El follower (slot 0) entra corriendo, y el 2º Pokémon (slot 2)
# es lanzado con Pokéball por el entrenador.
# En cambios durante el combate: Salen de su Pokéball con normalidad.
#===============================================================================
class FollowerPlayerSendOutAnimation
  SPEED = 14

  def initialize(sprite, spritehash, pkmn, illusionpoke, doublebattle)
    @illusionpoke = illusionpoke
    @disposed = false
    @PokemonBattlerSprite = sprite
    @pkmn = pkmn
    @spritehash = spritehash
    if doublebattle
      @spritex = PokeBattle_SceneConstants::PLAYERBATTLERD1_X if pkmn.index == 0
      @spritex = PokeBattle_SceneConstants::PLAYERBATTLERD2_X if pkmn.index == 2
    else
      @spritex = PokeBattle_SceneConstants::PLAYERBATTLER_X
    end
    @spritey = 0
    if @illusionpoke
      @endspritey = adjustBattleSpriteY(sprite, @illusionpoke.species, pkmn.index)
    else
      @endspritey = adjustBattleSpriteY(sprite, pkmn.species, pkmn.index)
    end
    if doublebattle
      @spritey += PokeBattle_SceneConstants::PLAYERBATTLERD1_Y if pkmn.index == 0
      @spritey += PokeBattle_SceneConstants::PLAYERBATTLERD2_Y if pkmn.index == 2
      @endspritey += PokeBattle_SceneConstants::PLAYERBATTLERD1_Y if pkmn.index == 0
      @endspritey += PokeBattle_SceneConstants::PLAYERBATTLERD2_Y if pkmn.index == 2
    else
      @spritey += PokeBattle_SceneConstants::PLAYERBATTLER_Y
      @endspritey += PokeBattle_SceneConstants::PLAYERBATTLER_Y
    end
    # Posición inicial: corriendo desde la izquierda fuera de pantalla
    @current_x = @spritex - 180
    @PokemonBattlerSprite.visible = true
    @PokemonBattlerSprite.zoom_x = 1.0
    @PokemonBattlerSprite.zoom_y = 1.0
    @PokemonBattlerSprite.tone = Tone.new(0, 0, 0, 0)
    pbSpriteSetCenter(@PokemonBattlerSprite, @current_x, 0)
    @PokemonBattlerSprite.y = @endspritey
    @animdone = false
    @frame = 0
    @cry_played = false
  end

  def disposed?
    return @disposed
  end

  def animdone?
    return @animdone
  end

  def dispose
    return if disposed?
    @disposed = true
  end

  def update
    return if disposed?
    @frame += 1
    # Grito enérgico al entrar al combate
    if @frame >= 3 && !@cry_played
      if @illusionpoke
        pbPlayCry(@illusionpoke)
      else
        pbPlayCry(@pkmn.pokemon ? @pkmn.pokemon : @pkmn.species)
      end
      @cry_played = true
    end
    if @current_x < @spritex
      @current_x += SPEED
      @current_x = @spritex if @current_x > @spritex
      # Pequeño rebote de carrera
      bob = (@current_x < @spritex) ? ((@frame % 4 < 2) ? 4 : 0) : 0
      pbSpriteSetCenter(@PokemonBattlerSprite, @current_x, 0)
      @PokemonBattlerSprite.y = @endspritey - bob
    else
      pbSpriteSetCenter(@PokemonBattlerSprite, @spritex, 0)
      @PokemonBattlerSprite.y = @endspritey
      @animdone = true if @frame >= 14
    end
  end
end

class PokeBattle_Scene
  attr_accessor :remFollowerSendOut

  alias rem_orig_pbSendOut pbSendOut unless method_defined?(:rem_orig_pbSendOut)
  def pbSendOut(battlerindex, pkmn, is_follower = false)
    if is_follower
      while inPartyAnimation?; end
      illusionpoke = @battle.battlers[battlerindex].effects[PBEffects::Illusion]
      @sprites["battlebox#{battlerindex}"].visible = false
      @briefmessage = false
      fadeanim = nil
      if @showingplayer
        fadeanim = PlayerFadeAnimation.new(@sprites)
      end
      frame = 0
      @sprites["pokemon#{battlerindex}"].setPokemonBitmap(pkmn, true)
      if illusionpoke
        @sprites["pokemon#{battlerindex}"].setPokemonBitmap(illusionpoke, true)
      end
      sendout = FollowerPlayerSendOutAnimation.new(
        @sprites["pokemon#{battlerindex}"],
        @sprites,
        @battle.battlers[battlerindex],
        illusionpoke,
        @battle.doublebattle
      )
      loop do
        fadeanim.update if fadeanim
        frame += 1
        if frame > 4 && !@sprites["battlebox#{battlerindex}"].appearing
          @sprites["battlebox#{battlerindex}"].appear
        end
        sendout.update
        pbGraphicsUpdate
        pbInputUpdate
        pbFrameUpdate
        break if (!fadeanim || fadeanim.animdone?) && sendout.animdone? &&
                 !@sprites["battlebox#{battlerindex}"].appearing
      end
      sendout.dispose
      if @battle.battlers[battlerindex].isShiny? && @battle.battlescene
        pbCommonAnimation("Shiny", @battle.battlers[battlerindex], nil)
      end
      if @showingplayer
        @showingplayer = false
        pbDisposeSprite(@sprites, "player")
        pbDisposeSprite(@sprites, "partybarplayer")
        for i in 0...6
          pbDisposeSprite(@sprites, "player#{i}")
        end
      end
      pbRefresh
    else
      rem_orig_pbSendOut(battlerindex, pkmn)
    end
  end
end

class PokeBattle_Battle
  attr_accessor :remFollowerSendOut

  alias rem_follower_pbStartBattleCore pbStartBattleCore unless method_defined?(:rem_follower_pbStartBattleCore)
  def pbStartBattleCore(canlose)
    @remFollowerSendOut = false
    fswitch = defined?(FOLLOWER_SWITCH) ? FOLLOWER_SWITCH : 101
    if $game_switches && $game_switches[fswitch] && $Trainer && $Trainer.party.length > 0
      lead = $Trainer.party[0]
      if lead && !lead.isEgg? && lead.hp > 0
        @remFollowerSendOut = true
      end
    end
    rem_follower_pbStartBattleCore(canlose)
  end

  alias rem_follower_pbSendOut pbSendOut unless method_defined?(:rem_follower_pbSendOut)
  def pbSendOut(index, pokemon)
    pbSetSeen(pokemon)
    @peer.pbOnEnteringBattle(self, pokemon)
    if pbIsOpposing?(index)
      @scene.pbTrainerSendOut(index, pokemon)
    else
      is_follower = (@remFollowerSendOut && index == 0)
      if is_follower
        @remFollowerSendOut = false
        @scene.pbSendOut(index, pokemon, true)
      else
        @scene.pbSendOut(index, pokemon, false)
      end
    end
    @scene.pbResetMoveIndex(index)
  end
end

#===============================================================================
# Ajuste de altura para la animación de exclamación (! / Alerta de Entrenador)
# Alineada con la altura de los bocadillos de misión (Quest Markers)
#===============================================================================
class AnimationSprite < RPG::Sprite
  def initialize(animID,map,tileX,tileY,viewport=nil,tinting=false,offsetY=nil)
    super(viewport)
    @tileX=tileX
    @tileY=tileY
    @offsetY=offsetY.nil? ? ((defined?(EXCLAMATION_ANIMATION_ID) && animID == EXCLAMATION_ANIMATION_ID) ? 26 : 0) : offsetY
    self.bitmap=Bitmap.new(1,1)
    self.bitmap.clear
    @map=map
    self.x=((@tileX*Game_Map.realResX)-@map.display_x+3)/4+(Game_Map::TILEWIDTH/2)
    self.y=((@tileY*Game_Map.realResY)-@map.display_y+3)/4+(Game_Map::TILEHEIGHT)-@offsetY
    pbDayNightTint(self) if tinting
    self.animation($data_animations[animID],true)
  end

  def update
    if !self.disposed?
      self.x=((@tileX*Game_Map.realResX)-@map.display_x+3)/4+(Game_Map::TILEWIDTH/2)
      self.y=((@tileY*Game_Map.realResY)-@map.display_y+3)/4+(Game_Map::TILEHEIGHT)-(@offsetY || 0)
      super
      self.dispose if !self.effect?
    end
  end
end

class Spriteset_Map
  def addUserAnimation(animID,x,y,tinting=false,offsetY=nil)
    offsetY = (defined?(EXCLAMATION_ANIMATION_ID) && animID == EXCLAMATION_ANIMATION_ID ? 26 : 0) if offsetY.nil?
    viewport=Viewport.new(0,0,Graphics.width,Graphics.height)
    viewport.z=99999
    sprite=AnimationSprite.new(animID,$game_map,x,y,viewport,tinting,offsetY)
    addUserSprite(sprite)
    return sprite
  end
end

def pbExclaim(event,id=EXCLAMATION_ANIMATION_ID,tinting=false,offsetY=nil)
  if offsetY.nil?
    offsetY = 26
    target_ev = event.is_a?(Array) ? event.first : event
    if target_ev && target_ev.respond_to?(:character_name) && target_ev.character_name != ""
      begin
        hue = target_ev.respond_to?(:character_hue) ? target_ev.character_hue : 0
        bmp = RPG::Cache.character(target_ev.character_name, hue)
        ch = bmp.height / 4
        if ch > 64
          offsetY += (ch - 64)
        end
      rescue
      end
    end
  end
  if event.is_a?(Array)
    sprite=nil
    done=[]
    for i in event
      if !done.include?(i.id)
        sprite=$scene.spriteset.addUserAnimation(id,i.x,i.y,tinting,offsetY)
        done.push(i.id)
      end
    end
  else
    sprite=$scene.spriteset.addUserAnimation(id,event.x,event.y,tinting,offsetY)
  end
  while !sprite.disposed?
    Graphics.update
    Input.update
    pbUpdateSceneMap
  end
end

#===============================================================================
# 5. BUSCAOBJETOS V5/V6 OVERLAY ENGINE (Sprite_Itemfinder)
#    - Detección continua en segundo plano sin pausar el movimiento.
#    - Overlay dinámico en la cabeza sincronizado con pasos y dirección.
#    - 4 estados: 0=Idle, 1=Near (Cerca), 2=Facing (Orientado), 3=Target (Delante).
#    - Sonido adaptativo y auto-apagado al montar en bicicleta o surfear.
#===============================================================================

def pbItemfinderActive?
  return ($PokemonGlobal && $PokemonGlobal.itemfinderActive) ? true : false
end

def pbToggleItemfinder
  if !$PokemonBag || $PokemonBag.pbQuantity(getConst(PBItems, :ITEMFINDER)) <= 0
    Kernel.pbMessage(_INTL("No tienes el Buscaobjetos."))
    return
  end
  if $PokemonGlobal.bicycle
    Kernel.pbMessage(_INTL("No puedes usar el Buscaobjetos mientras vas en bicicleta."))
    return
  end
  if $PokemonGlobal.surfing
    Kernel.pbMessage(_INTL("No puedes usar el Buscaobjetos mientras haces Surf."))
    return
  end

  $PokemonGlobal.itemfinderActive = !$PokemonGlobal.itemfinderActive
  if $PokemonGlobal.itemfinderActive
    pbSEPlay("dexselect", 80, 100)
  else
    pbSEPlay("dexselect", 70, 75)
  end
end

def pbTurnOffItemfinder
  return if !$PokemonGlobal || !$PokemonGlobal.itemfinderActive
  $PokemonGlobal.itemfinderActive = false
end

def pbItemfinderDetect
  return nil if !$game_map || !$game_player
  playerX = $game_player.x
  playerY = $game_player.y
  closest = nil
  min_dist = 999

  for event in $game_map.events.values
    next if !event
    next if event.name != "HiddenItem" && !(event.name =~ /^HiddenItem/i)
    next if $game_self_switches[[$game_map.map_id, event.id, "A"]]

    dist_x = (playerX - event.x).abs
    dist_y = (playerY - event.y).abs
    next if dist_x > 8 || dist_y > 6

    dist = dist_x + dist_y
    if dist < min_dist
      min_dist = dist
      closest = event
    end
  end
  return closest
end

def pbItemfinderState(event)
  return 0 if !event

  dx = event.x - $game_player.x
  dy = event.y - $game_player.y
  dir = $game_player.direction

  # Estado 3: ¡Lo tienes justo delante o bajo los pies!
  if (dx == 0 && dy == 0) ||
     (dir == 2 && dx == 0 && dy == 1) ||
     (dir == 4 && dx == -1 && dy == 0) ||
     (dir == 6 && dx == 1 && dy == 0) ||
     (dir == 8 && dx == 0 && dy == -1)
    return 3
  end

  dist = dx.abs + dy.abs

  # Estado 2: Cerca (<= 4 casillas) y mirando en su dirección
  is_facing = false
  if dist <= 4
    if dx.abs >= dy.abs
      is_facing = (dx < 0 && dir == 4) || (dx > 0 && dir == 6)
    end
    if !is_facing && dy.abs >= dx.abs
      is_facing = (dy < 0 && dir == 8) || (dy > 0 && dir == 2)
    end
  end

  return 2 if is_facing

  # Estado 1: Detectado en rango (pero más lejos o mirando a otro lado)
  return 1
end

class Sprite_Itemfinder < RPG::Sprite
  def initialize(viewport, character)
    super(viewport)
    @character = character
    @state = -1
    @bitmaps = {}
    @head_offset = nil
    @last_char_name = nil
    self.visible = false
  end

  def detect_head_offset
    return 0 if !@character || !@character.character_name
    name = @character.character_name.downcase
    return 6 if name =~ /girl_run/
    return 6 if name =~ /boy_run|_run/
    return 4 if name =~ /trchar001|girl/
    return 0
  end

  def get_state_bitmap(st)
    fname = case st
      when 0 then "Graphics/Characters/Itemfinder/state_0_idle"
      when 1 then "Graphics/Characters/Itemfinder/state_1_near"
      when 2 then "Graphics/Characters/Itemfinder/state_2_facing"
      when 3 then "Graphics/Characters/Itemfinder/state_3_target"
      else "Graphics/Characters/Itemfinder/state_0_idle"
    end
    if !@bitmaps[st] || @bitmaps[st].disposed?
      path = pbResolveBitmap(fname)
      if path
        @bitmaps[st] = Bitmap.new(path)
      end
    end
    return @bitmaps[st]
  end

  def update
    super
    if !$PokemonGlobal || !$PokemonGlobal.itemfinderActive ||
       $PokemonGlobal.bicycle || $PokemonGlobal.surfing || $PokemonGlobal.diving ||
       !@character || @character.transparent
      self.visible = false
      return
    end

    event = pbItemfinderDetect
    new_state = pbItemfinderState(event)

    if new_state != @state || !self.bitmap || self.bitmap.disposed?
      @state = new_state
      self.bitmap = get_state_bitmap(@state)
      self.ox = 32
      self.oy = 64
    end

    return if !self.bitmap

    if @last_char_name != @character.character_name
      @last_char_name = @character.character_name
      @head_offset = detect_head_offset
    end

    self.visible = true
    self.x = @character.screen_x
    self.y = @character.screen_y + (@head_offset || 0)
    self.z = @character.screen_z(64) + 1

    cw = 64
    ch = 64
    dir = @character.direction
    sy = ((dir - 2) / 2) * ch

    # Sincronización exacta con el ciclo de marcha y parada del personaje:
    if @character.pattern != 1
      # En cualquier paso de movimiento (pattern 0, 2 o 3), seguir con precisión matemática su frame
      sx = @character.pattern * cw
    else
      # Cuando está quieto en reposo (pattern 1), alternar entre frame 1 y frame 3 para parpadear
      # Ambos frames tienen bob = 0 (altura estándar de reposo), garantizando cero desajuste vertical
      rate = (@state == 3) ? 10 : 20
      phase = ((Graphics.frame_count / rate) % 2 == 0) ? 1 : 3
      sx = phase * cw
    end

    self.src_rect.set(sx, sy, cw, ch)
    self.tone.set(0, 0, 0, 0)
  end

  def dispose
    @bitmaps.each_value { |b| b.dispose if b && !b.disposed? }
    @bitmaps.clear
    super
  end
end

class Sprite_Character < RPG::Sprite
  if !method_defined?(:itemfinder_orig_init)
    alias itemfinder_orig_init initialize
    def initialize(viewport, character = nil)
      itemfinder_orig_init(viewport, character)
      if @character == $game_player
        @itemfinder_sprite = Sprite_Itemfinder.new(viewport, @character)
      end
    end

    alias itemfinder_orig_update update
    def update
      itemfinder_orig_update
      @itemfinder_sprite.update if @itemfinder_sprite
    end

    alias itemfinder_orig_dispose dispose
    def dispose
      @itemfinder_sprite.dispose if @itemfinder_sprite
      @itemfinder_sprite = nil
      itemfinder_orig_dispose
    end
  end
end

Events.onStepTaken += proc {
  if $PokemonGlobal && $PokemonGlobal.itemfinderActive
    if $PokemonGlobal.bicycle || $PokemonGlobal.surfing || $PokemonGlobal.diving
      pbTurnOffItemfinder
    else
      event = pbItemfinderDetect
      st = pbItemfinderState(event)
      case st
      when 1
        pbSEPlay("MiningPing", 55, 85)
      when 2
        pbSEPlay("MiningPing", 70, 110)
      when 3
        pbSEPlay("MiningPing", 85, 140)
      end
    end
  end
}



