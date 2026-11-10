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
        _INTL("7. BattleMoreInfo (Combate táctico tecla A/X)"),
        _INTL("8. Preparar Equipo y Objetos"),
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
      
    when 6 # 7. BattleMoreInfo
      if !$Trainer || $Trainer.pokemonCount == 0
        pbAddPokemon(:LUCARIO, 25) if hasConst?(PBSpecies, :LUCARIO)
      end
      Kernel.pbMessage(_INTL("\\nm[Inspector Tester]BATTLEMOREINFO (Información en Combate):\\n\\nDurante el menú de comandos o de selección de movimientos, presiona la tecla A (o X) para desplegar la pantalla táctica."))
      Kernel.pbMessage(_INTL("\\nm[Inspector Tester]Podrás ver los cambios de características (+1 a +6), climas, turnos restantes, terrenos y pantallas de cada combatiente."))
      foe_sym = hasConst?(PBSpecies, :CORVIKNIGHT) ? :CORVIKNIGHT : (hasConst?(PBSpecies, :PIDGEOT) ? :PIDGEOT : :PIDGEY)
      pbWildBattle(getID(PBSpecies, foe_sym), 25)
      
    when 7 # 8. Preparar Equipo y Objetos
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


#===============================================================================
#                     Información de Combate (BattleMoreInfo)
#               Autor: Bezier | Tester: Clara | Adaptación: REM (Noir)
# Permite ver los cambios de estadísticas (+1 a +6), estados, clima, terreno y
# pantallas tácticas (Luz, Reflejo, Trampa Rocas, etc.) pulsando la tecla A/X.
#===============================================================================

BATTLEMOREINFO_PATH = "Graphics/Pictures/BattleMoreInfo/" unless defined?(BATTLEMOREINFO_PATH)

def pbShowBattleInfo(battle)
  return if !battle || !battle.battlers
  viewport = Viewport.new(0, 0, Graphics.width, Graphics.height)
  viewport.z = 9999999
  panel = 0
  showingScreen = true
  pokeUI = BattleInfo_PokemonUI.new(battle, viewport)
  pokeUI.opacity = 0
  pokeUI.selected = battle.doublebattle ? 2 : 1
  battleUI = BattleInfo_BattleUI.new(battle, viewport)
  battleUI.opacity = 0
  loop do
    Graphics.update
    if showingScreen
      if panel == 0 # Selector de Pokémon
        pokeUI.opacity += 25
        battleUI.opacity -= 25
        showingScreen = false if pokeUI.opacity >= 255
      elsif panel == 1 # Panel de combate detallado
        pokeUI.opacity -= 25
        battleUI.opacity += 25
        showingScreen = false if battleUI.opacity >= 255
      else # Salir
        pokeUI.opacity -= 25
        battleUI.opacity -= 25
        break if pokeUI.opacity <= 0 && battleUI.opacity <= 0
      end
    else
      if panel == 0
        ret = pokeUI.update
        if ret == -2
          panel = -1
          showingScreen = true
        elsif ret != -1
          is_boss = (defined?(BOSS_SWITCH) && $game_switches[BOSS_SWITCH]) || (battle.doublebattle && (battle.battlers[3].nil? || battle.battlers[3].pokemon.nil?))
          if battle.doublebattle
            if is_boss
              battleUI.selected = [0,2,1].index(ret) || 0
            else
              battleUI.selected = [0,2,1,3].index(ret) || 0
            end
          else
            battleUI.selected = ret
          end
          panel = 1
          showingScreen = true
        end
      else
        ret = battleUI.update
        if ret == -1
          is_boss = (defined?(BOSS_SWITCH) && $game_switches[BOSS_SWITCH]) || (battle.doublebattle && (battle.battlers[3].nil? || battle.battlers[3].pokemon.nil?))
          if battle.doublebattle
            if is_boss
              pokeUI.selected = [2,0,1].index(battleUI.selected) || 0
            else
              pokeUI.selected = [3,2,0,1].index(battleUI.selected) || 0
            end
          else
            pokeUI.selected = [1,0].index(battleUI.selected) || 0
          end
          panel = 0
          showingScreen = true
        end
      end
    end
  end
  pokeUI.dispose rescue nil
  battleUI.dispose rescue nil
  viewport.dispose rescue nil
end

# Control base con sprites dentro de un viewport
class BattleInfo_Control
  WHITECOLOR = Color.new(245, 245, 250)
  DARKGRAYCOLOR = Color.new(15, 17, 23)

  attr_reader :viewport
  attr_reader :sprites
  attr_reader :disposed
  attr_accessor :x
  attr_accessor :y
  attr_accessor :z

  def initialize(x, y, viewport)
    @viewport = viewport
    @sprites = {}
    @disposed = false
    @x = x
    @y = y
    @z = 0
    @opacity = 255
  end

  def x; return @x; end
  def x=(value)
    dif = value - @x
    for s in @sprites.values
      s.x += dif if s && !s.disposed?
    end
    @x = value
  end

  def y; return @y; end
  def y=(value)
    dif = value - @y
    for s in @sprites.values
      s.y += dif if s && !s.disposed?
    end
    @y = value
  end

  def opacity; return @opacity; end
  def opacity=(value)
    @opacity = value
    @sprites.each { |k, s| s.opacity = value if s && !s.disposed? }
  end

  def addSprite(id, x, y, resource = nil, z = -1)
    if !resource; resource = BATTLEMOREINFO_PATH + id; end
    path = pbResolveBitmap(resource)
    if !path.nil?
      @sprites[id] = Sprite.new(@viewport) if !@sprites[id] || @sprites[id].disposed?
      @sprites[id].z = z if z != -1
      @sprites[id].x = x
      @sprites[id].y = y
      @sprites[id].bitmap = (BitmapCache.load_bitmap(path) rescue Bitmap.new(path))
      return @sprites[id]
    end
    return nil
  end

  def disposed?; return @disposed; end
  def dispose
    if !@disposed
      pbDisposeSpriteHash(@sprites)
      @disposed = true
    end
  end
end

# Botón de selección de Pokémon en combate
class BattleInfo_PokemonButton < BattleInfo_Control
  def initialize(battle, index, x, y, viewport)
    super(x, y, viewport)
    @battle = battle
    @index = index
    pokemon = @battle.battlers[index].pokemon rescue nil
    return if !pokemon
    @bg = addSprite("battler_sel", x, y)
    @bg.src_rect.height = @bg.bitmap.height / 2 if @bg && @bg.bitmap
    @icon = BI_PokemonIconSprite.new(pokemon, viewport)
    @sprites["icon"] = @icon
    @icon.x = x - 3
    @icon.y = y - 12
    @icon.active = false
    if index % 2 == 0 || (battle.opponent && index % 2 == 1)
      @trainer = addSprite("battler_owner", x + 36, y + 36)
    end
    if pokemon.gender != 2
      gender = addSprite("battler_gender", x + 140, y - 10)
      if gender && gender.bitmap
        gender.src_rect.width = gender.bitmap.width / 2
        gender.src_rect.x = pokemon.gender * gender.src_rect.width
      end
    end

    @overlay = BitmapSprite.new(120, 55, @viewport)
    @overlay.x = x + 42
    @overlay.y = y + 4
    @overlay.z = 999999
    @sprites["overlay"] = @overlay
    pbSetSmallFont(@overlay.bitmap)
    textpos = []
    textpos.push([pokemon.name, 69, 3, 2, WHITECOLOR, DARKGRAYCOLOR])
    if index % 2 == 0
      textpos.push([$Trainer.name, 59, 30, 2, WHITECOLOR, DARKGRAYCOLOR])
    elsif battle.opponent && index % 2 == 1
      textpos.push([battle.opponent.name, 59, 30, 2, WHITECOLOR, DARKGRAYCOLOR])
    end
    pbDrawTextPositions(@overlay.bitmap, textpos)
  end

  def selected?; return @bg && @bg.src_rect.y == @bg.src_rect.height; end
  def selected=(value)
    return if !@bg
    if value
      @bg.src_rect.y = @bg.src_rect.height
      @icon.active = true if @icon
    else
      @bg.src_rect.y = 0
      @icon.active = false if @icon
    end
  end

  def update
    @icon.update if @icon
  end

  def dispose
    @battle = nil
    @bg = nil
    @trainer = nil
    @icon = nil
    @overlay = nil
    super
  end
end

# Panel de selección de Pokémon
class BattleInfo_PokemonUI < BattleInfo_Control
  def initialize(battle, viewport)
    super(0, 116, viewport)
    @battle = battle
    @bgpoke = addSprite("battler_sel_bg", 0, 116)
    @buttons = []
    @selected = 0
    @indexes = nil
    is_boss = (defined?(BOSS_SWITCH) && $game_switches[BOSS_SWITCH]) || (@battle.doublebattle && (@battle.battlers[3].nil? || @battle.battlers[3].pokemon.nil?))
    if @battle.doublebattle && is_boss
      @indexes = [1, 0, 2]
      @buttons << BattleInfo_PokemonButton.new(@battle, 1, 172, 128, viewport)
      @buttons << BattleInfo_PokemonButton.new(@battle, 0, 68, 204, viewport)
      @buttons << BattleInfo_PokemonButton.new(@battle, 2, 276, 204, viewport)
    elsif @battle.doublebattle
      @indexes = [3, 1, 0, 2]
      @buttons << BattleInfo_PokemonButton.new(@battle, 3, 68, 128, viewport)
      @buttons << BattleInfo_PokemonButton.new(@battle, 1, 276, 128, viewport)
      @buttons << BattleInfo_PokemonButton.new(@battle, 0, 68, 204, viewport)
      @buttons << BattleInfo_PokemonButton.new(@battle, 2, 276, 204, viewport)
    else
      @indexes = [1, 0]
      @buttons << BattleInfo_PokemonButton.new(@battle, 1, 173, 128, viewport)
      @buttons << BattleInfo_PokemonButton.new(@battle, 0, 173, 204, viewport)
    end
  end

  def opacity=(value)
    super(value)
    @buttons.each { |bt| bt.opacity = value if bt }
  end

  def selected; return @selected; end
  def selected=(index)
    index = [0, [index, @buttons.length - 1].min].max
    @buttons[@selected].selected = false if @buttons[@selected]
    @selected = index
    @buttons[@selected].selected = true if @buttons[@selected]
  end

  def update
    for b in @buttons
      b.update if b
    end
    Input.update
    is_boss = (defined?(BOSS_SWITCH) && $game_switches[BOSS_SWITCH]) || (@battle.doublebattle && (@battle.battlers[3].nil? || @battle.battlers[3].pokemon.nil?))
    if Input.trigger?(Input::UP)
      if @battle.doublebattle
        if is_boss
          if @selected == 1
            pbPlayCursorSE(); self.selected -= 1
          elsif @selected == 2
            pbPlayCursorSE(); self.selected -= 2
          end
        else
          if @selected > 1
            pbPlayCursorSE(); self.selected -= 2
          end
        end
      else
        if @selected == 1
          pbPlayCursorSE(); self.selected -= 1
        end
      end
    elsif Input.trigger?(Input::DOWN)
      if @battle.doublebattle
        if @selected < 2
          pbPlayCursorSE(); self.selected += 2
        end
      else
        if @selected == 0
          pbPlayCursorSE(); self.selected += 1
        end
      end
    elsif Input.trigger?(Input::LEFT)
      if @battle.doublebattle
        if is_boss
          if @selected == 2
            pbPlayCursorSE(); self.selected -= 1
          end
        else
          if (@selected - 1) % 2 == 0
            pbPlayCursorSE(); self.selected -= 1
          end
        end
      end
    elsif Input.trigger?(Input::RIGHT)
      if @battle.doublebattle
        if is_boss
          if @selected == 1
            pbPlayCursorSE(); self.selected += 1
          end
        else
          if (@selected + 1) % 2 == 1
            pbPlayCursorSE(); self.selected += 1
          end
        end
      end
    end
    if Input.trigger?(Input::B)
      pbPlayCancelSE()
      return -2
    elsif Input.trigger?(Input::C)
      pbPlayDecisionSE()
      return @indexes[@selected]
    end
    return -1
  end

  def dispose
    @battle = nil
    @bgpoke = nil
    for bt in @buttons
      bt.dispose if bt
    end
    @buttons.clear
    super
  end
end

# Panel con estadísticas detalladas del combate
class BattleInfo_BattleUI < BattleInfo_Control
  TERRAIN_POS_0 = [261, 157]

  def initialize(battle, viewport)
    super(0, 0, viewport)
    @battle = battle
    @battlers = []
    @battlers << battle.battlers[0] if battle.battlers[0] && battle.battlers[0].pokemon
    @battlers << battle.battlers[2] if battle.battlers[2] && battle.battlers[2].pokemon
    @battlers << battle.battlers[1] if battle.battlers[1] && battle.battlers[1].pokemon
    @battlers << battle.battlers[3] if battle.battlers[3] && battle.battlers[3].pokemon
    @selected = -1
    @sprites = {}

    @bg = addSprite("battle_info_bg", 0, 0)
    @bgui = addSprite("battle_info_ui", 0, 0)

    @trainername = addSprite("trainer_name", -5, 27, BATTLEMOREINFO_PATH + "battler_owner")

    @poke = BI_PokemonIconSprite.new(nil, viewport)
    @poke.x = 19
    @poke.y = 47
    @sprites["poke"] = @poke
    @gender = addSprite("battler_gender", 164, 47)
    @gender.src_rect.width = 22 if @gender

    @status = addSprite("status", 130, 124, "Graphics/Pictures/statuses")
    if @status && @status.bitmap
      @status.src_rect.height = @status.bitmap.height / 7
      @status.src_rect.y = -@status.src_rect.height
    end

    @type1 = addSprite("type1", 193, 53, "Graphics/Pictures/types")
    @type2 = addSprite("type2", 193, 85, "Graphics/Pictures/types")
    @type1.src_rect.height = @type2.src_rect.height = 28 if @type1 && @type2

    @pokeps = addSprite("pokeps", 58, 98, BATTLEMOREINFO_PATH + "battler_owner")

    @ability = addSprite("ability", 261, 61, BATTLEMOREINFO_PATH + "battle_info_panel")
    @ability.src_rect.height = @ability.bitmap.height / 3 if @ability && @ability.bitmap

    @item = addSprite("item", 261, 85, BATTLEMOREINFO_PATH + "battle_info_panel")
    @item.src_rect.height = @item.bitmap.height / 3 if @item && @item.bitmap

    bmp_infopanel = (BitmapCache.load_bitmap(pbResolveBitmap(BATTLEMOREINFO_PATH + "battle_info_panel")) rescue Bitmap.new(pbResolveBitmap(BATTLEMOREINFO_PATH + "battle_info_panel")))
    h_2 = bmp_infopanel.height / 3
    @fieldPanel2 = Bitmap.new(bmp_infopanel.width, h_2)
    @fieldPanel3 = Bitmap.new(bmp_infopanel.width, h_2)
    @fieldPanel2.blt(0, 0, bmp_infopanel, Rect.new(0, h_2, bmp_infopanel.width, h_2))
    @fieldPanel3.blt(0, 0, bmp_infopanel, Rect.new(0, h_2 * 2, bmp_infopanel.width, h_2))

    @overlay = BitmapSprite.new(Graphics.width, Graphics.height, @viewport)
    @overlay.z = 999999
    @sprites["overlay"] = @overlay
    pbSetSmallFont(@overlay.bitmap)

    @overlayOffset = 0
    stat_path = pbResolveBitmap(BATTLEMOREINFO_PATH + "battler_stats")
    @updownStats = (BitmapCache.load_bitmap(stat_path) rescue Bitmap.new(stat_path))

    @overlayFix = BitmapSprite.new(Graphics.width, Graphics.height, @viewport)
    @overlayFix.z = 999999
    @sprites["overlayFix"] = @overlayFix
    pbSetSmallFont(@overlayFix.bitmap)
    drawFixTexts

    self.selected = 0
  end

  def isMyPartner?(selected)
    return selected < (@battle.doublebattle ? 2 : 1)
  end

  def selected; return @selected; end
  def selected=(value)
    return if @battlers.empty?
    @selected = [0, [value, @battlers.length - 1].min].max
    battler = @battlers[@selected]
    return if !battler || !battler.pokemon

    @trainername.visible = isMyPartner?(@selected) if @trainername
    @pokemon = battler.pokemon
    @poke.pokemon = @pokemon if @poke
    @gender.src_rect.x = @pokemon.gender * @gender.src_rect.width if @gender

    if battler.type1
      @type1.src_rect.y = @type1.src_rect.height * battler.type1
    else
      @type1.src_rect.y = -@type1.src_rect.height
    end

    if battler.type2 && battler.type1 != battler.type2
      @type2.src_rect.y = @type2.src_rect.height * battler.type2
      @type2.visible = true
    else
      @type2.visible = false
    end

    @pokeps.visible = isMyPartner?(@selected) if @pokeps
    if battler.hp == 0 || battler.status > 0
      st = (battler.hp == 0) ? 5 : battler.status - 1
      @status.src_rect.y = @status.src_rect.height * st
      @status.visible = true
    else
      @status.visible = false
    end

    @ability.visible = isMyPartner?(@selected) if @ability
    @item.visible = isMyPartner?(@selected) if @item

    drawTexts
  end

  def getPartner(battler)
    is_boss = (defined?(BOSS_SWITCH) && $game_switches[BOSS_SWITCH]) || (@battle.doublebattle && (@battle.battlers[3].nil? || @battle.battlers[3].pokemon.nil?))
    if @battle.doublebattle && is_boss
      return @battlers[1] if @battlers[0] == battler
      return @battlers[0] if @battlers[1] == battler
      return @battlers[1] if @battlers[2] == battler
      return @battlers[2] if @battlers[1] == battler
    elsif @battle.doublebattle
      return @battlers[1] if @battlers[0] == battler
      return @battlers[0] if @battlers[1] == battler
      return @battlers[3] if @battlers[2] == battler
      return @battlers[2] if @battlers[3] == battler
    end
    return battler
  end

  def getWeatherText
    text = ""
    case @battle.weather
    when PBWeather::SUNNYDAY; text += _INTL("Soleado")
    when PBWeather::RAINDANCE; text += _INTL("Lluvia")
    when PBWeather::SANDSTORM; text += _INTL("Tormenta arena")
    when PBWeather::HAIL; text += _INTL("Granizo")
    when PBWeather::HEAVYRAIN; text += _INTL("Diluvio")
    when PBWeather::HARSHSUN; text += _INTL("Sol abrasador")
    when PBWeather::STRONGWINDS; text += _INTL("Turbulencias")
    when (defined?(PBWeather::SHADOWSKY) && PBWeather::SHADOWSKY); text += _INTL("Cielo Oscuro")
    when (defined?(PBWeather::NIEBLA) && PBWeather::NIEBLA); text += _INTL("Niebla")
    when (defined?(PBWeather::SNOW) && PBWeather::SNOW); text += _INTL("Nieve")
    else text += @battle.weather.to_s
    end
    return text
  end

  def getPokemonEffectText(effect)
    case effect
    when PBEffects::AquaRing; _INTL("Acua Aro")
    when (defined?(PBEffects::Metronome) && PBEffects::Metronome); _INTL("Metrónomo")
    when (defined?(PBEffects::LashOut) && PBEffects::LashOut); _INTL("Desahogo")
    else effect.to_s
    end
  end

  def getSideText(effect)
    case effect
    when PBEffects::CraftyShield; _INTL("Truco defensa")
    when PBEffects::EchoedVoiceCounter, PBEffects::EchoedVoiceUsed; _INTL("Eco voz")
    when PBEffects::LastRoundFainted; _INTL("Compañero debilitado")
    when PBEffects::LightScreen; _INTL("Pantalla luz")
    when PBEffects::LuckyChant; _INTL("Conjuro")
    when PBEffects::MatBlock; _INTL("Escudo tatami")
    when PBEffects::Mist; _INTL("Neblina")
    when PBEffects::QuickGuard; _INTL("Anticipo")
    when PBEffects::Rainbow; _INTL("Arcoiris")
    when PBEffects::Reflect; _INTL("Reflejo")
    when PBEffects::Round; _INTL("Canon")
    when PBEffects::Safeguard; _INTL("Velo sagrado")
    when PBEffects::SeaOfFire; _INTL("Mar de llamas")
    when PBEffects::Spikes; _INTL("Púas")
    when PBEffects::StealthRock; _INTL("Trampa rocas")
    when PBEffects::StickyWeb; _INTL("Red viscosa")
    when PBEffects::Swamp; _INTL("Pantano")
    when PBEffects::Tailwind; _INTL("Viento afín")
    when PBEffects::ToxicSpikes; _INTL("Púas tóxicas")
    when PBEffects::WideGuard; _INTL("Vasta guardia")
    when (defined?(PBEffects::AuroraVeil) && PBEffects::AuroraVeil); _INTL("Velo aurora")
    else effect.to_s
    end
  end

  def getFieldText(effect)
    case effect
    when PBEffects::ElectricTerrain; _INTL("Campo eléctrico")
    when PBEffects::FairyLock; _INTL("Cerrojo feérico")
    when PBEffects::FusionBolt; _INTL("Rayo fusión")
    when PBEffects::FusionFlare; _INTL("Llama fusión")
    when PBEffects::GrassyTerrain; _INTL("Campo de hierba")
    when PBEffects::Gravity; _INTL("Gravedad")
    when PBEffects::IonDeluge; _INTL("Cortina plasma")
    when PBEffects::MagicRoom; _INTL("Zona mágica")
    when PBEffects::MistyTerrain; _INTL("Campo de niebla")
    when PBEffects::MudSportField; _INTL("Chapoteo lodo")
    when PBEffects::TrickRoom; _INTL("Espacio raro")
    when PBEffects::WaterSportField; _INTL("Hidrochorro")
    when PBEffects::WonderRoom; _INTL("Zona extraña")
    when (defined?(PBEffects::PsychicTerrain) && PBEffects::PsychicTerrain); _INTL("Campo psíquico")
    when (defined?(PBEffects::PlasmaFists) && PBEffects::PlasmaFists); _INTL("Puños plasma")
    else effect.to_s
    end
  end

  def drawFixTexts
    @overlayFix.bitmap.clear
    textpos = []
    textpos.push([_INTL("Turno {1}", @battle.turncount + 1), 452, 24, 2, WHITECOLOR, DARKGRAYCOLOR])
    textpos.push([_INTL("Ataque"), 43, 159, 0, WHITECOLOR, DARKGRAYCOLOR])
    textpos.push([_INTL("Defensa"), 43, 182, 0, WHITECOLOR, DARKGRAYCOLOR])
    textpos.push([_INTL("Atq. Esp."), 43, 206, 0, WHITECOLOR, DARKGRAYCOLOR])
    textpos.push([_INTL("Def. Esp."), 43, 229, 0, WHITECOLOR, DARKGRAYCOLOR])
    textpos.push([_INTL("Velocidad"), 43, 252, 0, WHITECOLOR, DARKGRAYCOLOR])
    textpos.push([_INTL("Precisión"), 43, 275, 0, WHITECOLOR, DARKGRAYCOLOR])
    textpos.push([_INTL("Evasión"), 43, 298, 0, WHITECOLOR, DARKGRAYCOLOR])
    textpos.push([_INTL("Críticos"), 43, 321, 0, WHITECOLOR, DARKGRAYCOLOR])
    pbDrawTextPositions(@overlayFix.bitmap, textpos)
  end

  def drawFieldInfo(x, y, text, value, textpos, maxValue, bmp)
    @overlay.bitmap.blt(x, y, bmp, bmp.rect)
    textpos.push([text, x + 10, y - 2, 0, WHITECOLOR, DARKGRAYCOLOR])
    if value.is_a?(Numeric) && value > 0
      if maxValue > 0
        textpos.push([_INTL("{1}/{2}", value, maxValue), x + 198, y - 2, 2, WHITECOLOR, DARKGRAYCOLOR])
      else
        textpos.push([_INTL("{1}", value), x + 198, y - 2, 2, WHITECOLOR, DARKGRAYCOLOR])
      end
    end
  end

  def drawTexts
    battler = @battlers[@selected]
    return if !battler || !battler.pokemon

    @overlay.bitmap.clear
    textpos = []
    if isMyPartner?(@selected)
      textpos.push([$Trainer.name, 57, 24, 2, WHITECOLOR, DARKGRAYCOLOR])
      textpos.push([_INTL("{1}/{2}", battler.hp, battler.totalhp), 122, 94, 2, WHITECOLOR, DARKGRAYCOLOR])
      textpos.push([_INTL("Habil."), 269, 59, 0, WHITECOLOR, DARKGRAYCOLOR])
      textpos.push([_INTL("{1}", PBAbilities.getName(battler.ability)), 407, 59, 2, WHITECOLOR, DARKGRAYCOLOR])
      textpos.push([_INTL("Objeto"), 269, 83, 0, WHITECOLOR, DARKGRAYCOLOR])
      item_name = battler.item > 0 ? PBItems.getName(battler.item) : _INTL("Ninguno")
      textpos.push([_INTL("{1}", item_name), 407, 83, 2, WHITECOLOR, DARKGRAYCOLOR])
    elsif @battle.opponent
      @trainername.visible = true if @trainername
      textpos.push([@battle.opponent.name, 57, 24, 2, WHITECOLOR, DARKGRAYCOLOR])
    end

    textpos.push([battler.name, 126, 64, 2, WHITECOLOR, DARKGRAYCOLOR])
    textpos.push([_INTL("Nivel: {1}", battler.level), 36, 120, 0, WHITECOLOR, DARKGRAYCOLOR])

    if battler.lastMoveUsed && battler.lastMoveUsed != -1
      for i in 0...battler.moves.length
        if battler.moves[i].id == battler.lastMoveUsed
          yultimo = 120
          yultimo = 114 if $MKXP
          textpos.push([_INTL("Último movimiento: {1}", battler.moves[i].name), 192, yultimo, 0, WHITECOLOR, DARKGRAYCOLOR])
          break
        end
      end
    end

    x = TERRAIN_POS_0[0]
    y = TERRAIN_POS_0[1]
    h = @fieldPanel2.height
    maxy = y + 168

    if @overlayOffset == 0
      if @battle.weather > 0 || @battle.weatherduration > 0
        drawFieldInfo(x, y, getWeatherText, @battle.weatherduration, textpos, 5, @fieldPanel2)
        y += h
      end
    end

    if @battle.field && @battle.field.effects
      ieffect = 0
      ieffect += (@overlayOffset - 1) if @overlayOffset > 1
      if ieffect < @battle.field.effects.length
        for i in ieffect...@battle.field.effects.length
          if (@battle.field.effects[i].is_a?(Numeric) && @battle.field.effects[i] > 0) || @battle.field.effects[i].is_a?(TrueClass)
            maxValue = 5
            maxValue = 2 if i == PBEffects::FairyLock
            if (battler.hasWorkingItem(:TERRAINEXTENDER) || getPartner(battler).hasWorkingItem(:TERRAINEXTENDER)) &&
               (i == PBEffects::ElectricTerrain || i == PBEffects::GrassyTerrain || i == PBEffects::MistyTerrain || (defined?(PBEffects::PsychicTerrain) && i == PBEffects::PsychicTerrain))
              maxValue = 8
            end
            drawFieldInfo(x, y, getFieldText(i), @battle.field.effects[i], textpos, maxValue, @fieldPanel2)
            y += h
            break if y > maxy
          end
        end
      end
    end

    if y < maxy && battler.effects
      for i in 0...battler.effects.length
        effect = battler.effects[i]
        if (effect.is_a?(Numeric) && effect > 0) || effect.is_a?(TrueClass)
          next if i == PBEffects::ProtectRate && effect == 1
          maxValue = 5
          drawFieldInfo(x, y, getPokemonEffectText(i), effect, textpos, maxValue, @fieldPanel2)
          y += h
          break if y > maxy
        end
      end
    end

    if y <= maxy && @battle.sides
      side_idx = isMyPartner?(@selected) ? 0 : 1
      if @battle.sides[side_idx] && @battle.sides[side_idx].effects
        side = @battle.sides[side_idx].effects
        ecoedvoice = false
        ecoedvoicecount = -1
        for i in 0...side.length
          value = side[i]
          maxValue = 5
          if i == PBEffects::LastRoundFainted
            if value != -1 && value == @battle.turncount - 1
              maxValue = -1
              value = true
              drawFieldInfo(x, y, getSideText(i), value, textpos, maxValue, @fieldPanel3)
              y += h
              break if y > maxy
            end
          elsif i == PBEffects::EchoedVoiceUsed
            ecoedvoice = true
          elsif i == PBEffects::EchoedVoiceCounter
            ecoedvoicecount = value
          elsif (value.is_a?(Numeric) && value > 0) || value == true
            if (i == PBEffects::LightScreen || i == PBEffects::Reflect) &&
               (battler.hasWorkingItem(:LIGHTCLAY) || getPartner(battler).hasWorkingItem(:LIGHTCLAY))
              maxValue = 8
            elsif i == PBEffects::Rainbow || i == PBEffects::SeaOfFire || i == PBEffects::Swamp || i == PBEffects::Tailwind
              maxValue = 4
            elsif i == PBEffects::Spikes || i == PBEffects::ToxicSpikes || i == PBEffects::Round
              maxValue = -1
            end
            bmp = (value == true) ? @fieldPanel2 : @fieldPanel3
            drawFieldInfo(x, y, getSideText(i), value, textpos, maxValue, bmp)
            y += h
            break if y > maxy
          end

          if ecoedvoice && ecoedvoicecount > 0
            drawFieldInfo(x, y, getSideText(i), ecoedvoicecount, textpos, -1, @fieldPanel2)
            y += h
            ecoedvoice = false
            ecoedvoicecount = -1
          end
          break if y > maxy
        end
      end
    end

    # Estadísticas y subidas/bajadas (Attack, Defense, SpAtk, SpDef, Speed, Acc, Eva)
    x = 133
    y = 160
    [PBStats::ATTACK, PBStats::DEFENSE,
     PBStats::SPATK, PBStats::SPDEF,
     PBStats::SPEED, PBStats::ACCURACY, PBStats::EVASION].each do |s|
      stg = (battler.stages && battler.stages[s]) ? battler.stages[s] : 0
      max = stg.abs
      low = stg < 0
      rect = Rect.new(low ? 18 : 0, 0, 18, 18)
      for i in 0...max
        @overlay.bitmap.blt(x + i * 18, y, @updownStats, rect)
      end
      y += 24
    end

    drawHP(battler)
    pbDrawTextPositions(@overlay.bitmap, textpos)
  end

  def drawHP(battler)
    hpGaugeSize = 96
    hpgauge = battler.totalhp == 0 ? 0 : (battler.hp * hpGaugeSize / battler.totalhp)
    hpgauge = 2 if hpgauge == 0 && battler.hp > 0
    hpzone = 0
    hpzone = 1 if battler.hp <= (battler.totalhp / 2).floor
    hpzone = 2 if battler.hp <= (battler.totalhp / 4).floor
    hpcolors = [
      PokeBattle_SceneConstants::HPCOLORGREENDARK,
      PokeBattle_SceneConstants::HPCOLORGREEN,
      PokeBattle_SceneConstants::HPCOLORYELLOWDARK,
      PokeBattle_SceneConstants::HPCOLORYELLOW,
      PokeBattle_SceneConstants::HPCOLORREDDARK,
      PokeBattle_SceneConstants::HPCOLORRED
    ]
    @overlay.bitmap.fill_rect(80, 88, hpgauge, 2, hpcolors[hpzone * 2])
    @overlay.bitmap.fill_rect(80, 90, hpgauge, 4, hpcolors[hpzone * 2 + 1])
  end

  def update
    Input.update
    @poke.update if @poke
    if Input.trigger?(Input::B)
      pbPlayCancelSE()
      return -1
    end
    if Input.trigger?(Input::LEFT)
      if (@selected - 1) >= 0
        pbPlayCursorSE()
        self.selected = @selected - 1
      end
    elsif Input.trigger?(Input::RIGHT)
      if (@selected + 1) < @battlers.length && @battlers[@selected + 1] && @battlers[@selected + 1].pokemon
        pbPlayCursorSE()
        self.selected = @selected + 1
      end
    end
    return 0
  end

  def dispose
    @battle = nil
    @battlers.clear
    @bg = nil
    @bgui = nil
    @trainername = nil
    @poke = nil
    @gender = nil
    @status = nil
    @type1 = nil
    @type2 = nil
    @pokeps = nil
    @overlay = nil
    @overlayFix = nil
    super
  end
end

# Icono de Pokémon adaptado
class BI_PokemonIconSprite < PokemonIconSprite
  def update
    return if !@pokemon
    super
  end
end
