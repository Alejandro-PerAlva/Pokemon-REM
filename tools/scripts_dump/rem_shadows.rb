#===============================================================================
# Overworld Shadows EX (Adaptado para Pokémon REM / Essentials v16-v18)
# Basado en el script de Pokémon Añil (por Golisopod User, Wolf PP, Marin).
# Adaptado para compatibilidad con RGSS1, PBTerrain y Following Pokémon.
#===============================================================================

module OWShadowSettings
  CASE_SENSITIVE_BLACKLISTS = false

  # Si el nombre del evento contiene una de estas palabras, no tendra sombra
  SHADOWLESS_EVENT_NAME = [
    "door", "puerta", "flechasalida", "nurse", "enfermera", "healing balls", 
    "balls curativas", "healing", "mart", "tendero", "smashrock", "rocarompible", 
    "strengthboulder", "piedrafuerza", "cuttree", "arbolcorte", "headbutttree", 
    "arbolgolpecabeza", "berryplant", "planta bayas", ".shadowless", ".noshadow", 
    ".sl", "entrada mazmorra bosque", "entrada cueva", "relic stone", "escalera", 
    "noshadow", "itemball", "objeto", "invisible", "cartel", "sign"
  ]

  # Si el nombre del archivo del sprite contiene esto, no tendra sombra
  SHADOWLESS_CHARACTER_NAME = ["nil", ""]

  # Grafico por defecto del jugador y eventos
  DEFAULT_SHADOW_FILENAME = "defaultShadow"
  PLAYER_SHADOW_FILENAME  = "defaultShadow"
  BIG_SHADOW_FILENAME     = "bigShadow"

  # Umbral de tamano para Following Pokemon y Pokemon overworld
  BIG_POKEMON_MIN_HEIGHT  = 1.9
  BIG_POKEMON_MIN_WEIGHT  = 130.0

  # Ajustes de centro [offset_x_mirando_izquierda, offset_y]
  # Para sprites con cuerpo desplazado respecto a la cabeza/origen del evento
  POKEMON_SHADOW_OFFSETS = {
    716 => [20, -6],   # Xerneas (patas y torso hacia atras)
    717 => [20, -14],  # Yveltal (alas y cuerpo levitando)
    718 => [24, -6],   # Zygarde (cola y masa corporal hacia atras)
    720 => [15, -6],   # Hoopa Desatado
  }
end

#-------------------------------------------------------------------------------
# Preservar el nombre "Dependent" en eventos acompanantes entre mapas y saves
#-------------------------------------------------------------------------------
class DependentEvents
  alias __ow_shadow__createEvent createEvent unless method_defined?(:__ow_shadow__createEvent)
  def createEvent(eventData)
    ret = __ow_shadow__createEvent(eventData)
    if ret && eventData && eventData[8]
      ret.instance_variable_get(:@event).name = eventData[8] rescue nil
    end
    return ret
  end
end

#-------------------------------------------------------------------------------
# Clase Sprite_OWShadow
#-------------------------------------------------------------------------------
class Sprite_OWShadow
  attr_reader :visible

  def initialize(sprite, event, viewport = nil)
    @rsprite  = sprite
    @event    = event
    @viewport = viewport
    @sprite   = Sprite.new(viewport)
    @disposed = false
    @current_bitmap_name = ""
    @current_species = nil
    @last_checked_species = nil
    @cached_is_big = false

    update_bitmap_selection
    update
  end

  def is_following_pokemon?
    return true if @event.respond_to?(:name) && @event.name == "Dependent"
    if $PokemonTemp && $PokemonTemp.dependentEvents && $PokemonTemp.dependentEvents.realEvents
      return true if $PokemonTemp.dependentEvents.realEvents.include?(@event)
    end
    return false
  end

  def pokemon_is_big?(species, pkmn = nil)
    return false if !species || species <= 0
    if @last_checked_species == species
      return @cached_is_big
    end

    @last_checked_species = species
    is_big = false

    if pkmn && pkmn.respond_to?(:height) && pkmn.respond_to?(:weight)
      begin
        h = pkmn.height / 10.0
        w = pkmn.weight / 10.0
        is_big = ((h >= OWShadowSettings::BIG_POKEMON_MIN_HEIGHT && w >= 35.0) || w >= OWShadowSettings::BIG_POKEMON_MIN_WEIGHT || h >= 3.0)
      rescue
      end
    end

    if !is_big
      begin
        dexdata = pbOpenDexData
        pbDexDataOffset(dexdata, species, 33)
        h = dexdata.fgetw / 10.0
        pbDexDataOffset(dexdata, species, 35)
        w = dexdata.fgetw / 10.0
        dexdata.close
        is_big = ((h >= OWShadowSettings::BIG_POKEMON_MIN_HEIGHT && w >= 35.0) || w >= OWShadowSettings::BIG_POKEMON_MIN_WEIGHT || h >= 3.0)
      rescue
      end
    end

    @cached_is_big = is_big
    return @cached_is_big
  end

  def calculate_shadow_offset(species, cw, ch)
    off_x = 0
    off_y = 0

    dir = @event.respond_to?(:direction) ? @event.direction : 2

    if species && OWShadowSettings::POKEMON_SHADOW_OFFSETS.key?(species)
      data = OWShadowSettings::POKEMON_SHADOW_OFFSETS[species]
      base_x = data[0]
      base_y = data[1]

      case dir
      when 4 # Mirando a la izquierda: cuerpo hacia la derecha
        off_x = base_x
        off_y = base_y
      when 6 # Mirando a la derecha: cuerpo hacia la izquierda
        off_x = -base_x
        off_y = base_y
      when 8 # Mirando arriba: cuerpo hacia abajo
        off_x = 0
        off_y = base_y
      when 2 # Mirando abajo: cuerpo hacia arriba
        off_x = 0
        off_y = base_y
      end

    elsif is_following_pokemon? && @current_bitmap_name == OWShadowSettings::BIG_SHADOW_FILENAME
      # Para cualquier otro seguidor grande, evitar que la sombra invada el espacio del jugador
      case dir
      when 4
        off_x = 6
      when 6
        off_x = -6
      when 8
        off_y = 4
      when 2
        off_y = -4
      end
    end

    return [off_x, off_y]
  end

  def update_bitmap_selection
    name = OWShadowSettings::DEFAULT_SHADOW_FILENAME

    if @event == $game_player
      name = OWShadowSettings::PLAYER_SHADOW_FILENAME
      @current_species = nil
    else
      ev_name = (@event.respond_to?(:name) && @event.name) ? @event.name.to_s : ""

      # 1. Comprobacion de tag manual explicito en el nombre del evento: shdw(nombre)
      if ev_name[/shdw\((.*?)\)/i]
        name = $~[1]
        @current_species = nil
      else
        # 2. Identificar si es un Pokemon (Following Pokemon o NPC Pokemon en mapa)
        species = nil
        pkmn_obj = nil

        if is_following_pokemon?
          if $Trainer && $Trainer.party.length > 0
            pkmn = $Trainer.party[0]
            if pkmn && (!pkmn.respond_to?(:isEgg?) || !pkmn.isEgg?)
              pkmn_obj = pkmn
              species = pkmn.species rescue nil
            end
          end
        end

        # Si todavia no tenemos especie o para eventos con sprite de Pokemon (ej. "716", "054", "716s")
        char_name = @event.character_name.to_s
        if (!species || species <= 0) && char_name =~ /^(\d+)/
          species = $1.to_i
        end

        @current_species = species

        if species && species > 0
          if pokemon_is_big?(species, pkmn_obj)
            name = OWShadowSettings::BIG_SHADOW_FILENAME
          else
            name = OWShadowSettings::DEFAULT_SHADOW_FILENAME
          end
        else
          name = OWShadowSettings::DEFAULT_SHADOW_FILENAME
        end
      end
    end

    name = OWShadowSettings::DEFAULT_SHADOW_FILENAME if name.nil? || name.empty?

    if @current_bitmap_name != name
      set_bitmap(name)
    end
  end

  def set_bitmap(name)
    path = "Graphics/Characters/Shadows/" + name
    return if !pbResolveBitmap(path)
    @ow_shadow_bitmap.dispose if @ow_shadow_bitmap
    @ow_shadow_bitmap = AnimatedBitmap.new(path)
    @current_bitmap_name = name
    if @sprite && !@sprite.disposed?
      @sprite.bitmap = @ow_shadow_bitmap.bitmap
    end
  end

  def dispose
    return if @disposed
    @sprite.dispose if @sprite
    @sprite = nil
    @ow_shadow_bitmap.dispose if @ow_shadow_bitmap
    @ow_shadow_bitmap = nil
    @disposed = true
  end

  def disposed?
    return @disposed
  end

  def shows_shadow?
    return false if !@event
    return false if @event.transparent
    char_name = @event.character_name.to_s
    return false if char_name.empty? || char_name == "nil"
    return false if @event.tile_id && @event.tile_id > 0

    # Surf o Buceo del jugador
    if @event == $game_player
      return false if $PokemonGlobal && ($PokemonGlobal.surfing || $PokemonGlobal.diving)
    end

    # Hierba alta
    return false if @event.bush_depth > 0

    # Comprobacion de terreno (Agua / Surf)
    if @event.respond_to?(:terrain_tag)
      t = @event.terrain_tag
      return false if (PBTerrain.isWater?(t) rescue false)
    end

    # Lista negra de eventos
    if @event.respond_to?(:name) && @event.name
      ev_name = @event.name.to_s.downcase
      return false if ev_name.include?("shdw(none)") || ev_name.include?("shdw(no)")
      for s in OWShadowSettings::SHADOWLESS_EVENT_NAME
        return false if ev_name.include?(s.downcase)
      end
    end

    return true
  end

  def update
    return if disposed? || !$scene.is_a?(Scene_Map)
    @sprite = Sprite.new(@viewport) if !@sprite

    # Comprobar si ha cambiado el grafico o el Pokemon acompanante
    update_bitmap_selection

    if !@rsprite.visible || !shows_shadow?
      @sprite.visible = false
      return
    end

    return if !@ow_shadow_bitmap || !@ow_shadow_bitmap.bitmap

    @ow_shadow_bitmap.update
    @sprite.bitmap = @ow_shadow_bitmap.bitmap

    @sprite.ox = @ow_shadow_bitmap.width / 2
    @sprite.oy = @ow_shadow_bitmap.height - 2

    # Calcular compensacion para centrar la sombra exactamente bajo el cuerpo
    cw = @rsprite.src_rect ? @rsprite.src_rect.width : 64
    ch = @rsprite.src_rect ? @rsprite.src_rect.height : 64
    off_x, off_y = calculate_shadow_offset(@current_species, cw, ch)

    @sprite.x = @rsprite.x + off_x

    # Nivel de suelo real (en saltos, la sombra permanece en el suelo)
    ground_y = @event.respond_to?(:screen_y_ground) ? @event.screen_y_ground : @rsprite.y
    @sprite.y = ground_y + off_y
    @sprite.z = @rsprite.z - 1

    # Escala y fisica de salto
    zoom_x = @rsprite.zoom_x
    zoom_y = @rsprite.zoom_y

    if @event.jumping?
      jump_height = [ground_y - @rsprite.y, 0].max
      scale = [1.0 - (jump_height / 120.0), 0.4].max
      zoom_x *= scale
      zoom_y *= scale
      @sprite.opacity = [(@rsprite.opacity * scale).to_i, 40].max
    else
      @sprite.opacity = @rsprite.opacity
    end

    @sprite.zoom_x = zoom_x
    @sprite.zoom_y = zoom_y
    @sprite.blend_type = @rsprite.blend_type
    @sprite.tone = @rsprite.tone if @rsprite.respond_to?(:tone)
    @sprite.visible = true
  end
end

#-------------------------------------------------------------------------------
# Inicializacion y ciclo de vida de la sombra en Sprite_Character
#-------------------------------------------------------------------------------
class Sprite_Character
  attr_accessor :ow_shadow

  alias __ow_shadow__initialize initialize unless method_defined?(:__ow_shadow__initialize)
  def initialize(*args)
    __ow_shadow__initialize(*args)
    @ow_shadow = Sprite_OWShadow.new(self, args[1], args[0])
  end

  alias __ow_shadow__dispose dispose unless method_defined?(:__ow_shadow__dispose)
  def dispose(*args)
    @ow_shadow.dispose if @ow_shadow
    @ow_shadow = nil
    __ow_shadow__dispose(*args)
  end

  alias __ow_shadow__update update unless method_defined?(:__ow_shadow__update)
  def update(*args)
    __ow_shadow__update(*args)
    @ow_shadow.update if @ow_shadow
  end
end
