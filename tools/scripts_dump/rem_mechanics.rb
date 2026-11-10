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
# Menú de Banco de Pruebas (Testing de Sistemas de la Auditoría)
#===============================================================================
def pbDebugTestingMenu
  loop do
    hora_str = sprintf("%02d:%02d", pbGetTimeNow.hour, pbGetTimeNow.min)
    noche_str = pbRemIsNight? ? "Noche (x1.5 Lv)" : "Día"
    congelado_str = ($PokemonGlobal && $PokemonGlobal.remTimeFrozen) ? " [Tiempo Congelado]" : ""
    
    cmd = Kernel.pbMessage(
      _INTL("BANCO DE PRUEBAS REM\\nHora: {1} ({2}){3}\\n¿Qué sistema deseas verificar?", hora_str, noche_str, congelado_str),
      [
        _INTL("1. Tiempo Irreal (Día/Noche)"),
        _INTL("2. Combate 2vs1 (Con selector de Aura)"),
        _INTL("3. Don Prodigio (Wonder Trade BST)"),
        _INTL("4. Poke al equipo (Captura con equipo lleno)"),
        _INTL("5. Quest Markers (Info e Icono)"),
        _INTL("6. NameBox Bezier (Test diálogo con nombre)"),
        _INTL("7. Preparar Equipo y Objetos"),
        _INTL("Salir")
      ]
    )
    
    case cmd
    when 0 # 1. Tiempo Irreal
      sub = Kernel.pbMessage(
        _INTL("TIEMPO IRREAL\\n¿Qué acción deseas ejecutar?"),
        [
          _INTL("Alternar Día / Noche (Forzar)"),
          _INTL("Avanzar 3 horas"),
          _INTL("Congelar / Descongelar tiempo"),
          _INTL("Volver")
        ]
      )
      case sub
      when 0
        pbToggleDayNight(true)
        Kernel.pbMessage(_INTL("Estado cambiado a: {1}.", pbRemIsNight? ? "Noche" : "Día"))
      when 1
        skipToHour((pbGetTimeNow.hour + 3) % 24)
        Kernel.pbMessage(_INTL("Hora avanzada a las {1}.", sprintf("%02d:00", pbGetTimeNow.hour)))
      when 2
        $PokemonGlobal.remTimeFrozen = !$PokemonGlobal.remTimeFrozen
        Kernel.pbMessage(_INTL("Tiempo {1}.", $PokemonGlobal.remTimeFrozen ? "CONGELADO" : "DESCONGELADO"))
      end
      
    when 1 # 2. Combate 2vs1 con selector de Aura
      if !$Trainer || $Trainer.pokemonCount < 2
        Kernel.pbMessage(_INTL("Para un combate 2vs1 necesitas al menos 2 Pokémon. Añadiendo equipo de prueba..."))
        pbAddPokemon(:LUCARIO, 25) if hasConst?(PBSpecies, :LUCARIO)
        pbAddPokemon(:GRENINJA, 25) if hasConst?(PBSpecies, :GRENINJA)
        for p in $Trainer.party; p.heal; end
      end
      aura_opts = [
        _INTL("1. Normal (Estadísticas base Nv25)"),
        _INTL("2. Aura Dominante PS x2 (Doble vida)"),
        _INTL("3. Aura Dominante Total x1.5 (+50% stats)"),
        _INTL("4. Aura Dominante Total x2.0 (+100% stats)")
      ]
      aura_sel = Kernel.pbMessage(_INTL("¿Qué modificador de estadísticas deseas aplicar al Jefe?"), aura_opts, 0)
      boost = case aura_sel
      when 1 then :hp_x2
      when 2 then :all_x15
      when 3 then :all_x2
      else nil
      end
      species_sym = hasConst?(PBSpecies, :URSALUNA) ? :URSALUNA : :SNORLAX
      species_id = getID(PBSpecies, species_sym)
      species_name = PBSpecies.getName(species_id)
      Kernel.pbMessage(_INTL("Iniciando combate 2vs1 contra {1} Nv25...", species_name))
      if boost
        $PokemonTemp.remDominantMode = boost
        begin
          pbBossFight(species_id, 25, 0, nil, false, false)
        ensure
          $PokemonTemp.remDominantMode = nil
        end
      else
        pbBossFight(species_id, 25, 0, nil, false, false)
      end
      Kernel.pbMessage(_INTL("Combate finalizado. Los consumibles usados se han restaurado automáticamente."))
      
    when 2 # 3. Don Prodigio
      if !$Trainer || $Trainer.pokemonCount == 0
        Kernel.pbMessage(_INTL("Necesitas al menos 1 Pokémon en el equipo para intercambiar. Añadiendo a Eevee..."))
        pbAddPokemon(:EEVEE, 15) if hasConst?(PBSpecies, :EEVEE)
      end
      pbDonProdigio
      
    when 3 # 4. Poke al equipo (Test con equipo de 6)
      while $Trainer.party.length < 6
        pbAddPokemon(:PIKACHU, 10) if hasConst?(PBSpecies, :PIKACHU)
      end
      Kernel.pbMessage(_INTL("Tu equipo ahora tiene 6 Pokémon completos.\\nSe te entregará un Eevee para probar el sistema 'Poke al equipo'."))
      eevee = PokeBattle_Pokemon.new(:EEVEE, 15, $Trainer) rescue nil
      if eevee
        pbStorePokemon(eevee)
      end
      
    when 4 # 5. Quest Markers
      Kernel.pbMessage(_INTL("QUEST MARKERS:\\nEl icono que flota sobre la cabeza de este NPC es un Quest Marker animado cargado desde Graphics/Pictures/Quest Markers/blue.png.\\n\\nSe activa colocando en la primera línea del evento un comentario con la sintaxis:\\nquest_marker [archivo]\\n[opacidad 0-255]\\n[rebote true/false]\\n[parpadeo true/false]"))
      
    when 5 # 6. NameBox Bezier
      Kernel.pbMessage(_INTL("\\nm[Inspector Tester]¡Saludos, agente!\\nEste cuadro superior con mi nombre es el NameBox Bezier integrado con la estética Noir de Pokémon REM."))
      Kernel.pbMessage(_INTL("\\nm[Inspector Tester]Funciona tanto con la etiqueta \\nm[Nombre] en diálogos, como mediante NameBox.load(\"Nombre\") en eventos de RPG Maker XP."))
      
    when 6 # 7. Preparar Equipo y Objetos
      pbAddPokemon(:LUCARIO, 25) if hasConst?(PBSpecies, :LUCARIO)
      pbAddPokemon(:GRENINJA, 25) if hasConst?(PBSpecies, :GRENINJA)
      $PokemonBag.pbStoreItem(:SITRUSBERRY, 5) if hasConst?(PBItems, :SITRUSBERRY)
      $PokemonBag.pbStoreItem(:POKEBALL, 20) if hasConst?(PBItems, :POKEBALL)
      Kernel.pbMessage(_INTL("¡Equipo de prueba, Bayas Zidra y 20 Poké Balls añadidas!"))
    else
      break
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

class Game_Map
  alias rem_setup_debug_tester setup
  def setup(map_id)
    rem_setup_debug_tester(map_id)
    pbRemEnsureTesterEvent if map_id == 3
  end
end

class Scene_Map
  alias rem_createSpritesets_debug createSpritesets
  def createSpritesets
    pbRemEnsureTesterEvent
    rem_createSpritesets_debug
  end

  alias rem_update_debug_tester update
  def update
    if $game_map && $game_map.map_id == 3 && !$game_map.events.has_key?(999)
      if pbRemEnsureTesterEvent
        disposeSpritesets
        createSpritesets
      end
    end
    rem_update_debug_tester
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
