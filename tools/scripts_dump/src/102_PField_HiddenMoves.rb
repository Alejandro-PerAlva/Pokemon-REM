##################################################################################
# Empleo de los Movimientos Ocultos (MO) fuera de batalla
################################################################################
#===============================================================================
# Interpolators
#===============================================================================
class RectInterpolator
  def initialize(oldrect,newrect,frames)
    restart(oldrect,newrect,frames)
  end

  def restart(oldrect,newrect,frames)
    @oldrect=oldrect
    @newrect=newrect
    @frames=[frames,1].max
    @curframe=0
    @rect=oldrect.clone
  end

  def set(rect)
    rect.set(@rect.x,@rect.y,@rect.width,@rect.height)
  end

  def done?
    @curframe>@frames
  end

  def update
    return if done?
    t=(@curframe*1.0/@frames)
    x1=@oldrect.x
    x2=@newrect.x
    x=x1+t*(x2-x1)
    y1=@oldrect.y
    y2=@newrect.y
    y=y1+t*(y2-y1)
    rx1=@oldrect.x+@oldrect.width
    rx2=@newrect.x+@newrect.width
    rx=rx1+t*(rx2-rx1)
    ry1=@oldrect.y+@oldrect.height
    ry2=@newrect.y+@newrect.height
    ry=ry1+t*(ry2-ry1)
    minx=x<rx ? x : rx
    maxx=x>rx ? x : rx
    miny=y<ry ? y : ry
    maxy=y>ry ? y : ry
    @rect.set(minx,miny,maxx-minx,maxy-miny)
    @curframe+=1
  end
end



class PointInterpolator
  def initialize(oldx,oldy,newx,newy,frames)
    restart(oldx,oldy,newx,newy,frames)
  end

  def restart(oldx,oldy,newx,newy,frames)
    @oldx=oldx
    @oldy=oldy
    @newx=newx
    @newy=newy
    @frames=frames
    @curframe=0
    @x=oldx
    @y=oldy
  end

  def x; @x;end
  def y; @y;end

  def done?
    @curframe>@frames
  end

  def update
    return if done?
    t=(@curframe*1.0/@frames)
    rx1=@oldx
    rx2=@newx
    @x=rx1+t*(rx2-rx1)
    ry1=@oldy
    ry2=@newy
    @y=ry1+t*(ry2-ry1)
    @curframe+=1
  end
end



#===============================================================================
# Controladores de movimientos ocultos
#===============================================================================
class MoveHandlerHash < HandlerHash
  def initialize
    super(:PBMoves)
  end
end



module HiddenMoveHandlers
  CanUseMove=MoveHandlerHash.new
  UseMove=MoveHandlerHash.new

  def self.addCanUseMove(item,proc)
    CanUseMove.add(item,proc)
  end

  def self.addUseMove(item,proc)
    UseMove.add(item,proc)
  end 

  def self.hasHandler(item)
    return CanUseMove[item]!=nil && UseMove[item]!=nil
  end

  def self.triggerCanUseMove(item,pokemon)
    # Determina si puede usarse un movimiento
    if !CanUseMove[item]
      return false
    else
      return CanUseMove.trigger(item,pokemon)
    end
  end

  def self.triggerUseMove(item,pokemon)
    # Determina si se utilizó un movimiento
    if !UseMove[item]
      return false
    else
      return UseMove.trigger(item,pokemon)
    end
  end
end



def Kernel.pbCanUseHiddenMove?(pkmn,move)
  return HiddenMoveHandlers.triggerCanUseMove(move,pkmn)
end

def Kernel.pbUseHiddenMove(pokemon,move)
  return HiddenMoveHandlers.triggerUseMove(move,pokemon)
end

def Kernel.pbHiddenMoveEvent
  Events.onAction.trigger(nil)
end

#===============================================================================
# Animación de los movimientos ocultos
#===============================================================================
def pbHiddenMoveAnimation(pokemon)
  return false if !pokemon
  viewport=Viewport.new(0,0,0,0)
  viewport.z=99999
  bg=Sprite.new(viewport)
  bg.bitmap=BitmapCache.load_bitmap("Graphics/Pictures/hiddenMovebg")
  sprite=PokemonSprite.new(viewport)
  sprite.setPokemonBitmap(pokemon)
  sprite.z=1
  sprite.ox=sprite.bitmap.width/2
  sprite.oy=sprite.bitmap.height/2
  sprite.visible=false
  strobebitmap=AnimatedBitmap.new("Graphics/Pictures/hiddenMoveStrobes")
  strobes=[]
  15.times do |i|
    strobe=BitmapSprite.new(26*2,8*2,viewport)
    strobe.bitmap.blt(0,0,strobebitmap.bitmap,Rect.new(0,(i%2)*8*2,26*2,8*2))
    strobe.z=((i%2)==0 ? 2 : 0)
    strobe.visible=false
    strobes.push(strobe)
  end
  strobebitmap.dispose
  interp=RectInterpolator.new(
     Rect.new(0,Graphics.height/2,Graphics.width,0),
     Rect.new(0,(Graphics.height-bg.bitmap.height)/2,Graphics.width,bg.bitmap.height),
     10)
  ptinterp=nil
  phase=1
  frames=0
  begin
    Graphics.update
    Input.update
    sprite.update
    case phase
    when 1         # Expande altura del visor desde cero hasta el máximo
      interp.update
      interp.set(viewport.rect)
      bg.oy=(bg.bitmap.height-viewport.rect.height)/2
      if interp.done?
        phase=2
        ptinterp=PointInterpolator.new(
           Graphics.width+(sprite.bitmap.width/2),bg.bitmap.height/2,
           Graphics.width/2,bg.bitmap.height/2,
           16)
      end
    when 2         # Desplaza Pokémon desde la derecha hasta el centro
      ptinterp.update
      sprite.x=ptinterp.x
      sprite.y=ptinterp.y
      sprite.visible=true
      if ptinterp.done?
        phase=3
        pbPlayCry(pokemon)
        frames=0
      end
    when 3         # Espera
      frames+=1
      if frames>30
        phase=4
        ptinterp=PointInterpolator.new(
           Graphics.width/2,bg.bitmap.height/2,
           -(sprite.bitmap.width/2),bg.bitmap.height/2,
           16)
        frames=0
      end
    when 4         # Desplaza Pokémon desde el centro hasta salir por la izquierda
      ptinterp.update
      sprite.x=ptinterp.x
      sprite.y=ptinterp.y
      if ptinterp.done?
        phase=5
        sprite.visible=false
        interp=RectInterpolator.new(
           Rect.new(0,(Graphics.height-bg.bitmap.height)/2,Graphics.width,bg.bitmap.height),
           Rect.new(0,Graphics.height/2,Graphics.width,0),
           10)
      end
    when 5         # Reduce el visor desde su tamaño máximo hasta cero
      interp.update
      interp.set(viewport.rect)
      bg.oy=(bg.bitmap.height-viewport.rect.height)/2
      phase=6 if interp.done?    
    end
    for strobe in strobes
      strobe.ox=strobe.viewport.rect.x
      strobe.oy=strobe.viewport.rect.y
      if !strobe.visible
        randomY=16*(1+rand(bg.bitmap.height/16-2))
        strobe.y=randomY+(Graphics.height-bg.bitmap.height)/2
        strobe.x=rand(Graphics.width)
        strobe.visible=true
      elsif strobe.x<Graphics.width
        strobe.x+=32
      else
        randomY=16*(1+rand(bg.bitmap.height/16-2))
        strobe.y=randomY+(Graphics.height-bg.bitmap.height)/2
        strobe.x=-strobe.bitmap.width-rand(Graphics.width/4)
      end
    end
    pbUpdateSceneMap
  end while phase!=6
  sprite.dispose
  for strobe in strobes
    strobe.dispose
  end
  strobes.clear
  bg.dispose
  viewport.dispose
  return true
end

#===============================================================================
# Herramientas de Campo Clave (Tijeras, Pico, Guantes de Fuerza, Tabla de Surf)
# En Pokémon REM los obstáculos de campo se resuelven mediante Objetos Clave
# del inventario sin depender de movimientos de MO.
#===============================================================================

def canUseCut?
  facingEvent = $game_player.pbFacingEvent
  return facingEvent && (facingEvent.name == "Tree" || facingEvent.name.include?("Tree"))
end

def useCut
  Kernel.pbCut
end

def canUseRockSmash?
  facingEvent = $game_player.pbFacingEvent
  return facingEvent && (facingEvent.name == "Rock" || facingEvent.name.include?("Rock"))
end

def useRockSmash
  Kernel.pbRockSmash
end

def canUseStrength?
  facingEvent = $game_player.pbFacingEvent
  return facingEvent && (facingEvent.name == "Boulder" || facingEvent.name.include?("Boulder")) && !$PokemonMap.strengthUsed
end

def useStrength
  Kernel.pbStrength
end

def canUseSurf?
  terrain = Kernel.pbFacingTerrainTag
  notCliff = $game_map.passable?($game_player.x, $game_player.y, $game_player.direction)
  return PBTerrain.isSurfable?(terrain) && !$PokemonGlobal.surfing && 
         !pbGetMetadata($game_map.map_id, MetadataBicycleAlways) && notCliff
end

def useSurf
  Kernel.pbSurf
end

#===============================================================================
# Corte / Cut -> Tijeras (:SHEARS)
#===============================================================================
def Kernel.pbCut
  has_shears = ($DEBUG || ($PokemonBag && $PokemonBag.pbHasItem?(:SHEARS)))
  if has_shears
    Kernel.pbMessage(_INTL("Hay maleza y ramas que bloquean el camino.\\1"))
    if Kernel.pbConfirmMessage(_INTL("¿Quieres cortarlas con las Tijeras?"))
      pbSEPlay("PRSFX- Cut") rescue pbSEPlay("Cut") rescue nil
      Kernel.pbMessage(_INTL("¡Has usado las Tijeras para despejar el camino!"))
      facingEvent = $game_player.pbFacingEvent
      if facingEvent
        facingEvent.erase
        $PokemonMap.addErasedEvent(facingEvent.id) if $PokemonMap
      end
      return true
    end
  else
    Kernel.pbMessage(_INTL("Hay maleza y ramas bloqueando el paso. Con unas tijeras de podar se podría cortar fácilmente."))
  end
  return false
end

HiddenMoveHandlers::CanUseMove.add(:CUT, proc { |move, pkmn|
  return true
})

HiddenMoveHandlers::UseMove.add(:CUT, proc { |move, pokemon|
  Kernel.pbCut
  return true
})

#===============================================================================
# Golpe cabeza / Headbutt
#===============================================================================
def Kernel.pbHeadbuttEffect(event)
  a=((event.x*event.y+event.x*event.y)/5)%10
  b=($Trainer.id&0xFFFF)%10
  chance=1
  if a==b
    chance=8
  elsif a>b && (a-b).abs<5
    chance=5
  elsif a<b && (a-b).abs>5
    chance=5
  end
  if rand(10)>=chance
    Kernel.pbMessage(_INTL("No pasó nada..."))
  else
    if !pbEncounter(chance==1 ? EncounterTypes::HeadbuttLow : EncounterTypes::HeadbuttHigh)
      Kernel.pbMessage(_INTL("No pasó nada..."))
    end
  end
end

def Kernel.pbHeadbutt(event)
  movefinder=Kernel.pbCheckMove(:HEADBUTT)
  if $DEBUG || movefinder
    if Kernel.pbConfirmMessage(_INTL("Hay un árbol no demasiado grande. ¿Quieres utilizar Golpe cabeza?"))
      speciesname=!movefinder ? $Trainer.name : movefinder.name
      Kernel.pbMessage(_INTL("¡{1} ha usado Golpe cabeza!",speciesname))
      pbHiddenMoveAnimation(movefinder)
      Kernel.pbHeadbuttEffect(event)
    end
  else
    Kernel.pbMessage(_INTL("Un Pokémon podría esconderse en este árbol. Tal vez un Pokémon pueda sacudirlo."))
  end
  Input.update
  return
end

HiddenMoveHandlers::CanUseMove.add(:HEADBUTT,proc{|move,pkmn|
   facingEvent=$game_player.pbFacingEvent
   if !facingEvent || facingEvent.name!="HeadbuttTree"
     Kernel.pbMessage(_INTL("No se puede usar aquí."))
     return false
   end
   return true
})

HiddenMoveHandlers::UseMove.add(:HEADBUTT,proc{|move,pokemon|
   if !pbHiddenMoveAnimation(pokemon)
     Kernel.pbMessage(_INTL("¡{1} ha usado {2}!",pokemon.name,PBMoves.getName(move)))
   end
   facingEvent=$game_player.pbFacingEvent
   Kernel.pbHeadbuttEffect(facingEvent)
})

#===============================================================================
# Golpe roca  /  Rock Smash -> Pico (:PICKAXE)
#===============================================================================
def pbRockSmashRandomEncounter
  if rand(100) < 25
    pbEncounter(EncounterTypes::RockSmash)
  end
end

def Kernel.pbRockSmash
  has_pickaxe = ($DEBUG || ($PokemonBag && $PokemonBag.pbHasItem?(:PICKAXE)))
  if has_pickaxe
    Kernel.pbMessage(_INTL("Esta roca parece quebradiza y agrietada.\\1"))
    if Kernel.pbConfirmMessage(_INTL("¿Quieres picarla con el Pico?"))
      pbSEPlay("PRSFX- Rock Smash") rescue pbSEPlay("Rock Smash") rescue nil
      Kernel.pbMessage(_INTL("¡Has usado el Pico para quebrar la roca!"))
      facingEvent = $game_player.pbFacingEvent
      if facingEvent
        facingEvent.erase
        $PokemonMap.addErasedEvent(facingEvent.id) if $PokemonMap
      end
      pbRockSmashRandomEncounter
      return true
    end
  else
    Kernel.pbMessage(_INTL("Es una roca quebradiza y agrietada. Con un pico de minero se podría romper fácilmente."))
  end
  return false
end

HiddenMoveHandlers::CanUseMove.add(:ROCKSMASH, proc { |move, pkmn|
  return true
})

HiddenMoveHandlers::UseMove.add(:ROCKSMASH, proc { |move, pokemon|
  Kernel.pbRockSmash
  return true
})

#===============================================================================
# Fuerza  /  Strength -> Guantes de Fuerza (:GLOVES)
#===============================================================================
def Kernel.pbStrength
  if $PokemonMap.strengthUsed
    Kernel.pbMessage(_INTL("Los Guantes de Fuerza te permiten mover rocas pesadas."))
    return true
  end
  has_gloves = ($DEBUG || ($PokemonBag && $PokemonBag.pbHasItem?(:GLOVES)))
  if has_gloves
    Kernel.pbMessage(_INTL("Es una roca enorme y pesada.\\1"))
    if Kernel.pbConfirmMessage(_INTL("¿Quieres usar los Guantes de Fuerza para empujarla?"))
      pbSEPlay("PRSFX- Strength") rescue nil
      $PokemonMap.strengthUsed = true
      Kernel.pbMessage(_INTL("¡Te has equipado los Guantes de Fuerza! Ahora puedes mover rocas pesadas."))
      return true
    end
  else
    Kernel.pbMessage(_INTL("Es una roca enorme. Demasiado pesada para moverla con las manos desnudas."))
  end
  return false
end

HiddenMoveHandlers::CanUseMove.add(:STRENGTH, proc { |move, pkmn|
  return true
})

HiddenMoveHandlers::UseMove.add(:STRENGTH, proc { |move, pokemon|
  Kernel.pbStrength
  return true
})

#===============================================================================
# Surf -> Tabla de Surf (:SURFBOARD)
#===============================================================================
def Kernel.pbSurf
  if $game_player.pbHasDependentEvents?
    Kernel.pbMessage(_INTL("No puedes surfear mientras vas acompañado."))
    return false
  end
  if pbGetMetadata($game_map.map_id, MetadataBicycleAlways)
    Kernel.pbMessage(_INTL("¡No puedes surfear aquí!"))
    return false
  end
  has_board = ($DEBUG || ($PokemonBag && $PokemonBag.pbHasItem?(:SURFBOARD)))
  if has_board
    if Kernel.pbConfirmMessage(_INTL("El agua tiene buena pinta...\n¿Quieres navegar con la Tabla de Surf?"))
      pbSEPlay("PRSFX- Surf") rescue nil
      surfbgm = pbGetMetadata(0, MetadataSurfBGM)
      pbCueBGM(surfbgm, 0.5) if surfbgm
      Kernel.pbMessage(_INTL("¡Te subes a la Tabla de Surf!"))
      pbStartSurfing()
      return true
    end
  else
    Kernel.pbMessage(_INTL("El agua es profunda y cristalina. Necesitarías una tabla de surf para navegar sobre ella."))
  end
  return false
end

def pbStartSurfing()
  Kernel.pbCancelVehicles
  $PokemonEncounters.clearStepCount
  $PokemonGlobal.surfing = true
  Kernel.pbUpdateVehicle
  Kernel.pbJumpToward
  Kernel.pbUpdateVehicle
  $game_player.check_event_trigger_here([1, 2])
end

def pbEndSurf(xOffset, yOffset)
  return false if !$PokemonGlobal.surfing
  x = $game_player.x
  y = $game_player.y
  currentTag = $game_map.terrain_tag(x, y)
  facingTag = Kernel.pbFacingTerrainTag
  if PBTerrain.isSurfable?(currentTag) && !PBTerrain.isSurfable?(facingTag)
    if Kernel.pbJumpToward(1, false, true)
      $game_map.autoplayAsCue
      $game_player.increase_steps
      result = $game_player.check_event_trigger_here([1, 2])
      Kernel.pbOnStepTaken(result)
    end
    return true
  end
  return false
end

def Kernel.pbTransferSurfing(mapid, xcoord, ycoord, direction = $game_player.direction)
  pbFadeOutIn(99999) {
    $game_temp.player_new_map_id = mapid
    $game_temp.player_new_x = xcoord
    $game_temp.player_new_y = ycoord
    $game_temp.player_new_direction = direction
    Kernel.pbCancelVehicles
    $PokemonGlobal.surfing = true
    Kernel.pbUpdateVehicle
    $scene.transfer_player(false)
    $game_map.autoplay
    $game_map.refresh
  }
end

# Interacción directa con el botón de acción frente a obstáculos de campo
Events.onAction += proc { |sender, e|
  facingEvent = $game_player.pbFacingEvent
  if facingEvent
    ev_name = facingEvent.name.to_s
    if ev_name == "Tree" || ev_name.include?("Tree")
      Kernel.pbCut
      return
    elsif ev_name == "Rock" || ev_name.include?("Rock")
      Kernel.pbRockSmash
      return
    elsif ev_name == "Boulder" || ev_name.include?("Boulder")
      Kernel.pbStrength
      return
    end
  end

  terrain = Kernel.pbFacingTerrainTag
  notCliff = $game_map.passable?($game_player.x, $game_player.y, $game_player.direction)
  if PBTerrain.isSurfable?(terrain) && !$PokemonGlobal.surfing && 
     !pbGetMetadata($game_map.map_id, MetadataBicycleAlways) && notCliff
    Kernel.pbSurf
    return
  end
}

HiddenMoveHandlers::CanUseMove.add(:SURF, proc { |move, pkmn|
  return true
})

HiddenMoveHandlers::UseMove.add(:SURF, proc { |move, pokemon|
  Kernel.pbSurf
  return true
})

#===============================================================================
# Cascada  /  Waterfall
#===============================================================================
def Kernel.pbAscendWaterfall(event=nil)
  event=$game_player if !event
  return if !event
  return if event.direction!=8      # No puede subir si no está de frente
  oldthrough=event.through
  oldmovespeed=event.move_speed
  terrain=Kernel.pbFacingTerrainTag
  return if terrain!=PBTerrain::Waterfall && terrain!=PBTerrain::WaterfallCrest
  event.through=true
  event.move_speed=2
  loop do
    event.move_up
    terrain=pbGetTerrainTag(event)
    break if terrain!=PBTerrain::Waterfall && terrain!=PBTerrain::WaterfallCrest
  end
  event.through=oldthrough
  event.move_speed=oldmovespeed
end

def Kernel.pbDescendWaterfall(event=nil)
  event=$game_player if !event
  return if !event
  return if event.direction!=2      # No puede subir si no está de frente
  oldthrough=event.through
  oldmovespeed=event.move_speed
  terrain=Kernel.pbFacingTerrainTag
  return if terrain!=PBTerrain::Waterfall && terrain!=PBTerrain::WaterfallCrest
  event.through=true
  event.move_speed=2
  loop do
    event.move_down
    terrain=pbGetTerrainTag(event)
    break if terrain!=PBTerrain::Waterfall && terrain!=PBTerrain::WaterfallCrest
  end
  event.through=oldthrough
  event.move_speed=oldmovespeed
end

def Kernel.pbWaterfall
  if $DEBUG ||
    (HIDDENMOVESCOUNTBADGES ? $Trainer.numbadges>=BADGEFORWATERFALL : $Trainer.badges[BADGEFORWATERFALL])
    movefinder=Kernel.pbCheckMove(:WATERFALL)
    if $DEBUG || movefinder
      if Kernel.pbConfirmMessage(_INTL("Es una gran catarata. ¿Quieres utilizar Cascada?"))
        speciesname=!movefinder ? $Trainer.name : movefinder.name
        Kernel.pbMessage(_INTL("¡{1} ha usado Cascada!",speciesname))
        pbHiddenMoveAnimation(movefinder)
        pbAscendWaterfall
        return true
      end
    else
      Kernel.pbMessage(_INTL("Una columna de agua desciende con una gran fuerza."))
    end
  else
    Kernel.pbMessage(_INTL("Una columna de agua desciende con una gran fuerza."))
  end
  return false
end

Events.onAction+=proc{|sender,e|
   terrain=Kernel.pbFacingTerrainTag
   if terrain==PBTerrain::Waterfall
     Kernel.pbWaterfall
     return
   end
   if terrain==PBTerrain::WaterfallCrest
     Kernel.pbMessage(_INTL("Una columna de agua desciende con una gran fuerza."))
     return
   end
}

HiddenMoveHandlers::CanUseMove.add(:WATERFALL,proc{|move,pkmn|
   if !$DEBUG &&
      !(HIDDENMOVESCOUNTBADGES ? $Trainer.numbadges>=BADGEFORWATERFALL : $Trainer.badges[BADGEFORWATERFALL])
     Kernel.pbMessage(_INTL("No tienes el número necesario de medallas."))
     return false
   end
   terrain=Kernel.pbFacingTerrainTag
   if terrain!=PBTerrain::Waterfall
     Kernel.pbMessage(_INTL("No se puede usar aquí."))
     return false
   end
   return true
})

HiddenMoveHandlers::UseMove.add(:WATERFALL,proc{|move,pokemon|
   if !pbHiddenMoveAnimation(pokemon)
     Kernel.pbMessage(_INTL("¡{1} ha usado {2}!",pokemon.name,PBMoves.getName(move)))
   end
   Kernel.pbAscendWaterfall
   return true
})

#===============================================================================
# Buceo  /  Dive
#===============================================================================
def Kernel.pbDive
  divemap=pbGetMetadata($game_map.map_id,MetadataDiveMap)
  return false if !divemap
  if $DEBUG ||
    (HIDDENMOVESCOUNTBADGES ? $Trainer.numbadges>=BADGEFORDIVE : $Trainer.badges[BADGEFORDIVE])
    movefinder=Kernel.pbCheckMove(:DIVE)
    if $DEBUG || movefinder
      if Kernel.pbConfirmMessage(_INTL("El mar es profundo por aquí. ¿Quieres sumergirte?"))
        speciesname=!movefinder ? $Trainer.name : movefinder.name
        Kernel.pbMessage(_INTL("¡{1} ha usado Buceo!",speciesname))
        pbHiddenMoveAnimation(movefinder)
        pbFadeOutIn(99999){
           $game_temp.player_new_map_id=divemap
           $game_temp.player_new_x=$game_player.x
           $game_temp.player_new_y=$game_player.y
           $game_temp.player_new_direction=$game_player.direction
           Kernel.pbCancelVehicles
           $PokemonGlobal.diving=true
           Kernel.pbUpdateVehicle
           $scene.transfer_player(false)
           $game_map.autoplay
           $game_map.refresh
        }
        return true
      end
    else
      Kernel.pbMessage(_INTL("El mar es profundo por aquí. Un Pokémon podría ser capaz de sumergirse."))
    end
  else
    Kernel.pbMessage(_INTL("El mar es profundo por aquí. Un Pokémon podría ser capaz de sumergirse."))
  end
  return false
end

def Kernel.pbSurfacing
  return if !$PokemonGlobal.diving
  divemap=nil
  meta=pbLoadMetadata
  for i in 0...meta.length
    if meta[i] && meta[i][MetadataDiveMap]
      if meta[i][MetadataDiveMap]==$game_map.map_id
        divemap=i
        break
      end
    end
  end
  return if !divemap
  movefinder=Kernel.pbCheckMove(:DIVE)
  if $DEBUG || (movefinder &&
    (HIDDENMOVESCOUNTBADGES ? $Trainer.numbadges>=BADGEFORDIVE : $Trainer.badges[BADGEFORDIVE]) )
    if Kernel.pbConfirmMessage(_INTL("Se está filtrando luz desde arriba. ¿Quieres utilizar Buceo?"))
      speciesname=!movefinder ? $Trainer.name : movefinder.name
      Kernel.pbMessage(_INTL("¡{1} ha usado Buceo!",speciesname))
      pbHiddenMoveAnimation(movefinder)
      pbFadeOutIn(99999){
         $game_temp.player_new_map_id=divemap
         $game_temp.player_new_x=$game_player.x
         $game_temp.player_new_y=$game_player.y
         $game_temp.player_new_direction=$game_player.direction
         Kernel.pbCancelVehicles
         $PokemonGlobal.surfing=true
         Kernel.pbUpdateVehicle
         $scene.transfer_player(false)
         surfbgm=pbGetMetadata(0,MetadataSurfBGM)
         if surfbgm
           pbBGMPlay(surfbgm)
         else
           $game_map.autoplayAsCue
         end
         $game_map.refresh
      }
      return true
    end
  else
    Kernel.pbMessage(_INTL("Se está filtrando luz desde arriba. Un Pokémon podría ser capaz de emerger aquí."))
  end
  return false
end

def Kernel.pbTransferUnderwater(mapid,xcoord,ycoord,direction=$game_player.direction)
  pbFadeOutIn(99999){
     $game_temp.player_new_map_id=mapid
     $game_temp.player_new_x=xcoord
     $game_temp.player_new_y=ycoord
     $game_temp.player_new_direction=direction
     Kernel.pbCancelVehicles
     $PokemonGlobal.diving=true
     Kernel.pbUpdateVehicle
     $scene.transfer_player(false)
     $game_map.autoplay
     $game_map.refresh
  }
end

Events.onAction+=proc{|sender,e|
   terrain=$game_player.terrain_tag
   if terrain==PBTerrain::DeepWater
     Kernel.pbDive
     return
   end
   if $PokemonGlobal.diving
     if DIVINGSURFACEANYWHERE
       Kernel.pbSurfacing
       return
     else
       divemap=nil
       meta=pbLoadMetadata
       for i in 0...meta.length
         if meta[i] && meta[i][MetadataDiveMap]
           if meta[i][MetadataDiveMap]==$game_map.map_id
             divemap=i
             break
           end
         end
       end
       if $MapFactory.getTerrainTag(divemap,$game_player.x,$game_player.y)==PBTerrain::DeepWater
         Kernel.pbSurfacing
         return
       end
     end
   end
}

HiddenMoveHandlers::CanUseMove.add(:DIVE,proc{|move,pkmn|
   if !$DEBUG &&
      !(HIDDENMOVESCOUNTBADGES ? $Trainer.numbadges>=BADGEFORDIVE : $Trainer.badges[BADGEFORDIVE])
     Kernel.pbMessage(_INTL("No tienes el número necesario de medallas."))
     return false
   end
   if $PokemonGlobal.diving
     return true if DIVINGSURFACEANYWHERE
     divemap=nil
     meta=pbLoadMetadata
     for i in 0...meta.length
       if meta[i] && meta[i][MetadataDiveMap]
         if meta[i][MetadataDiveMap]==$game_map.map_id
           divemap=i
           break
         end
       end
     end
     if $MapFactory.getTerrainTag(divemap,$game_player.x,$game_player.y)==PBTerrain::DeepWater
       return true
     else
       Kernel.pbMessage(_INTL("No se puede usar aquí."))
       return false
     end
   end
   if $game_player.terrain_tag!=PBTerrain::DeepWater
     Kernel.pbMessage(_INTL("No se puede usar aquí."))
     return false
   end
   if !pbGetMetadata($game_map.map_id,MetadataDiveMap)
     Kernel.pbMessage(_INTL("No se puede usar aquí."))
     return false
   end
   return true
})

HiddenMoveHandlers::UseMove.add(:DIVE,proc{|move,pokemon|
   wasdiving=$PokemonGlobal.diving
   if $PokemonGlobal.diving
     divemap=nil
     meta=pbLoadMetadata
     for i in 0...meta.length
       if meta[i] && meta[i][MetadataDiveMap]
         if meta[i][MetadataDiveMap]==$game_map.map_id
           divemap=i
           break
         end
       end
     end
   else
     divemap=pbGetMetadata($game_map.map_id,MetadataDiveMap)
   end
   return false if !divemap
   if !pbHiddenMoveAnimation(pokemon)
     Kernel.pbMessage(_INTL("¡{1} ha usado {2}!",pokemon.name,PBMoves.getName(move)))
   end
   pbFadeOutIn(99999){
      $game_temp.player_new_map_id=divemap
      $game_temp.player_new_x=$game_player.x
      $game_temp.player_new_y=$game_player.y
      $game_temp.player_new_direction=$game_player.direction
      Kernel.pbCancelVehicles
      if wasdiving
        $PokemonGlobal.surfing=true
      else
        $PokemonGlobal.diving=true
      end
      Kernel.pbUpdateVehicle
      $scene.transfer_player(false)
      $game_map.autoplay
      $game_map.refresh
   }
   return true
})

#===============================================================================
# Vuelo  /  Fly
#===============================================================================
HiddenMoveHandlers::CanUseMove.add(:FLY,proc{|move,pkmn|
   if !$DEBUG &&
      !(HIDDENMOVESCOUNTBADGES ? $Trainer.numbadges>=BADGEFORFLY : $Trainer.badges[BADGEFORFLY])
     Kernel.pbMessage(_INTL("No tienes el número necesario de medallas."))
     return false
   end
   if $game_player.pbHasDependentEvents?
     Kernel.pbMessage(_INTL("No se puede utilizar cuando estás con alguien."))
     return false
   end
   if !pbGetMetadata($game_map.map_id,MetadataOutdoor)
     Kernel.pbMessage(_INTL("No se puede usar aquí."))
     return false
   end
   return true
})

HiddenMoveHandlers::UseMove.add(:FLY,proc{|move,pokemon|
   if !$PokemonTemp.flydata
     Kernel.pbMessage(_INTL("No se puede usar aquí."))
   end
   if !pbHiddenMoveAnimation(pokemon)
     Kernel.pbMessage(_INTL("¡{1} ha usado {2}!",pokemon.name,PBMoves.getName(move)))
   end
   pbFadeOutIn(99999){
      Kernel.pbCancelVehicles
      $game_temp.player_new_map_id=$PokemonTemp.flydata[0]
      $game_temp.player_new_x=$PokemonTemp.flydata[1]
      $game_temp.player_new_y=$PokemonTemp.flydata[2]
      $PokemonTemp.flydata=nil
      $game_temp.player_new_direction=2
      $scene.transfer_player
      $game_map.autoplay
      $game_map.refresh
   }
   pbEraseEscapePoint
   return true
})

#===============================================================================
# Destello  /  Flash
#===============================================================================
HiddenMoveHandlers::CanUseMove.add(:FLASH,proc{|move,pkmn|
   if !$DEBUG &&
      !(HIDDENMOVESCOUNTBADGES ? $Trainer.numbadges>=BADGEFORFLASH : $Trainer.badges[BADGEFORFLASH])
     Kernel.pbMessage(_INTL("Lo siento, necesitas una medalla nueva."))
     return false
   end
   if !pbGetMetadata($game_map.map_id,MetadataDarkMap)
     Kernel.pbMessage(_INTL("No se puede usar aquí."))
     return false
   end
   if $PokemonGlobal.flashUsed
     Kernel.pbMessage(_INTL("Ya se está utilizando."))
     return false
   end
   return true
})

HiddenMoveHandlers::UseMove.add(:FLASH,proc{|move,pokemon|
   darkness=$PokemonTemp.darknessSprite
   return false if !darkness || darkness.disposed?
   if !pbHiddenMoveAnimation(pokemon)
     Kernel.pbMessage(_INTL("¡{1} ha usado {2}!",pokemon.name,PBMoves.getName(move)))
   end
   $PokemonGlobal.flashUsed=true
   while darkness.radius<176
     Graphics.update
     Input.update
     pbUpdateSceneMap
     darkness.radius+=4
   end
   return true
})

#===============================================================================
# Teletransporte  /  Teleport
#===============================================================================
HiddenMoveHandlers::CanUseMove.add(:TELEPORT,proc{|move,pkmn|
   if !pbGetMetadata($game_map.map_id,MetadataOutdoor)
     Kernel.pbMessage(_INTL("No se puede usar aquí."))
     return false
   end
   if $game_player.pbHasDependentEvents?
     Kernel.pbMessage(_INTL("No se puede utilizar cuando estás con alguien."))
     return false
   end
   healing=$PokemonGlobal.healingSpot
   if !healing
     healing=pbGetMetadata(0,MetadataHome) # Home
   end
   if healing
     mapname=pbGetMapNameFromId(healing[0])
     if Kernel.pbConfirmMessage(_INTL("¿Quieres regresar al último lugar de curación en {1}?",mapname))
       return true
     end
     return false
   else
     Kernel.pbMessage(_INTL("No se puede usar aquí."))
     return false
   end
})

HiddenMoveHandlers::UseMove.add(:TELEPORT,proc{|move,pokemon|
   healing=$PokemonGlobal.healingSpot
   if !healing
     healing=pbGetMetadata(0,MetadataHome)
   end
   if healing
     if !pbHiddenMoveAnimation(pokemon)
       Kernel.pbMessage(_INTL("¡{1} ha usado {2}!",pokemon.name,PBMoves.getName(move)))
     end
     pbFadeOutIn(99999){
        Kernel.pbCancelVehicles
        $game_temp.player_new_map_id=healing[0]
        $game_temp.player_new_x=healing[1]
        $game_temp.player_new_y=healing[2]
        $game_temp.player_new_direction=2
        $scene.transfer_player
        $game_map.autoplay
        $game_map.refresh
     }
     pbEraseEscapePoint
     return true
   end
   return false
})

#===============================================================================
# Excavar  /  Dig
#===============================================================================
HiddenMoveHandlers::CanUseMove.add(:DIG,proc{|move,pkmn|
   escape=($PokemonGlobal.escapePoint rescue nil)
   if !escape || escape==[]
     Kernel.pbMessage(_INTL("No se puede usar aquí."))
     return false
   end
   if $game_player.pbHasDependentEvents?
     Kernel.pbMessage(_INTL("No se puede utilizar cuando estás con alguien."))
     return false
   end
   mapname=pbGetMapNameFromId(escape[0])
   if Kernel.pbConfirmMessage(_INTL("¿Quieres escapar de aquí y regresar a {1}?",mapname))
     return true
   end
   return false
})

HiddenMoveHandlers::UseMove.add(:DIG,proc{|move,pokemon|
   escape=($PokemonGlobal.escapePoint rescue nil)
   if escape
     if !pbHiddenMoveAnimation(pokemon)
       Kernel.pbMessage(_INTL("¡{1} ha usado {2}!",pokemon.name,PBMoves.getName(move)))
     end
     pbFadeOutIn(99999){
        Kernel.pbCancelVehicles
        $game_temp.player_new_map_id=escape[0]
        $game_temp.player_new_x=escape[1]
        $game_temp.player_new_y=escape[2]
        $game_temp.player_new_direction=escape[3]
        $scene.transfer_player
        $game_map.autoplay
        $game_map.refresh
     }
     pbEraseEscapePoint
     return true
   end
   return false
})

#===============================================================================
# Dulce Aroma  /  Sweet Scent
#===============================================================================
def pbSweetScent
  if $game_screen.weather_type!=PBFieldWeather::None
    Kernel.pbMessage(_INTL("El dulce aroma se desvaneció por alguna razón..."))
    return
  end
  viewport=Viewport.new(0,0,Graphics.width,Graphics.height)
  viewport.z=99999
  count=0
  viewport.color.alpha-=10 
  begin
    if viewport.color.alpha<128 && count==0
      viewport.color.red=255
      viewport.color.green=0
      viewport.color.blue=0
      viewport.color.alpha+=8
    else
      count+=1
      if count>10
        viewport.color.alpha-=8 
      end
    end
    Graphics.update
    Input.update
    pbUpdateSceneMap
  end until viewport.color.alpha<=0
  viewport.dispose
  encounter=nil
  enctype=nil
  enctype=$PokemonEncounters.pbEncounterType
  if enctype<0 || !$PokemonEncounters.isEncounterPossibleHere?() ||
     !pbEncounter(enctype)
    Kernel.pbMessage(_INTL("Parece que no hay nada aquí..."))
  end
end

HiddenMoveHandlers::CanUseMove.add(:SWEETSCENT,proc{|move,pkmn|
   return true
})

HiddenMoveHandlers::UseMove.add(:SWEETSCENT,proc{|move,pokemon|
   if !pbHiddenMoveAnimation(pokemon)
     Kernel.pbMessage(_INTL("¡{1} ha usado {2}!",pokemon.name,PBMoves.getName(move)))
   end
   pbSweetScent
   return true
})