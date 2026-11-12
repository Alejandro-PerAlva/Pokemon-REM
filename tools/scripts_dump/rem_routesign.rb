#===============================================================================
# REM_RouteSign - Visor de Encuentros en Carteles de Ruta (Estilo Oniria Noir)
#===============================================================================
# Ventana modal inferior inspirada en paneles de ruta de senderismo / carreteras.
# - Se activa al interactuar con el letrero de la ruta (pbRouteSign).
# - Muestra el nombre de la ruta y la categoría ENCUENTROS.
# - Bloque principal: 2 filas x 2, 3 o 4 columnas (hasta 8 Pokémon de suelo/cueva/surf).
# - Columna derecha de Pesca: icono de caña (item505) + 2 filas x 1 columna (máx 2 pokes).
# - Si no hay pesca, la columna no aparece y el bloque principal ocupa todo el ancho.
# - Estado Pokédex:
#     * No visto: Silueta completamente negra (Tone.new(-255, -255, -255, 0)).
#     * Visto / Capturado: Mini sprite a todo color original.
# - Se cierra limpiamente con Espacio, C, B o Escape como un diálogo.
#===============================================================================

class REM_RouteSign_Scene
  def initialize(map_id=nil, title=nil, custom_land=nil, custom_fish=nil)
    @map_id = map_id || ($game_map ? $game_map.map_id : 1)
    @title  = title || ($game_map ? $game_map.name : _INTL("Ruta Desconocida"))

    if custom_land || custom_fish
      @land_species = (custom_land || [])[0...8]
      @fish_species = (custom_fish || [])[0...2]
    else
      @land_species, @fish_species = pbGetRouteEncountersData(@map_id)
    end

    @viewport = Viewport.new(0, 0, Graphics.width, Graphics.height)
    @viewport.z = 99999
    @sprites = {}
  end

  def pbStart
    # Dimensiones y anclaje en el tercio inferior (tipo diálogo / cartel expandido)
    box_w = 464
    box_h = 164
    box_x = (Graphics.width - box_w) / 2
    box_y = Graphics.height - box_h - 14

    has_fish = (@fish_species && @fish_species.length > 0)
    divider_x = box_w - 74 # Posición de la línea divisoria si hay pesca

    # 1. Fondo y marcos de la caja del cartel
    @sprites["box"] = BitmapSprite.new(box_w, box_h, @viewport)
    @sprites["box"].x = box_x
    @sprites["box"].y = box_y
    @sprites["box"].z = @viewport.z + 1
    bmp = @sprites["box"].bitmap

    silver = defined?(REM_UI::SILVER) ? REM_UI::SILVER : Color.new(214, 219, 228)
    ink    = defined?(REM_UI::INK) ? REM_UI::INK : Color.new(13, 14, 18)

    # Fondo Noir translúcido
    bmp.fill_rect(2, 2, box_w - 4, box_h - 4, Color.new(14, 17, 24, 245))

    # Trama sutil de fondo
    y_scan = 4
    while y_scan < box_h - 4
      bmp.fill_rect(2, y_scan, box_w - 4, 1, Color.new(20, 26, 38, 120))
      y_scan += 4
    end

    # Marcos biselados plata
    bmp.fill_rect(0, 0, box_w, 1, silver)
    bmp.fill_rect(0, box_h - 1, box_w, 1, silver)
    bmp.fill_rect(0, 0, 1, box_h, silver)
    bmp.fill_rect(box_w - 1, 0, 1, box_h, silver)
    bmp.fill_rect(1, 1, box_w - 2, 1, Color.new(35, 42, 58))
    bmp.fill_rect(1, box_h - 2, box_w - 2, 1, Color.new(35, 42, 58))

    # Cabecera
    pbSetNarrowFont(bmp)
    bmp.font.size = 18
    pbDrawTextPositions(bmp, [
      [@title.upcase, 16, 7, 0, Color.new(255, 255, 255), ink]
    ])

    bmp.font.size = 15
    tag_x = has_fish ? (divider_x - 14) : (box_w - 18)
    pbDrawTextPositions(bmp, [
      [_INTL("ENCUENTROS"), tag_x, 8, 1, Color.new(110, 195, 255), ink]
    ])

    # Separador horizontal de cabecera
    bmp.fill_rect(12, 31, box_w - 24, 1, Color.new(50, 58, 76))

    # 2. Bloque de Pesca (si existe en esta ruta)
    if has_fish
      # Separador vertical
      bmp.fill_rect(divider_x, 32, 1, box_h - 36, Color.new(50, 58, 76))

      # Icono de la caña de pescar (item505) en la parte superior de la columna
      rod_icon = AnimatedBitmap.new("Graphics/Icons/item505") rescue nil
      col_center_x = divider_x + (box_w - divider_x) / 2
      if rod_icon && rod_icon.bitmap
        bmp.stretch_blt(Rect.new(col_center_x - 14, 35, 28, 28), rod_icon.bitmap, Rect.new(0, 0, rod_icon.width, rod_icon.height))
        rod_icon.dispose
      end

      # Sprites de Pokémon de pesca (2 filas x 1 columna)
      @fish_species.each_with_index do |specie, i|
        next if i >= 2
        sp_x = box_x + col_center_x
        sp_y = box_y + (i == 0 ? 82 : 126)
        createPokemonIcon("fish_#{i}", specie, sp_x, sp_y)
      end
    end

    # 3. Bloque Principal (Suelo / Cueva / Surf)
    area_w = has_fish ? (divider_x - 16) : (box_w - 24)
    land_count = @land_species ? @land_species.length : 0

    if land_count == 0 && (!has_fish || @fish_species.length == 0)
      bmp.font.size = 16
      pbDrawTextPositions(bmp, [
        [_INTL("No se registran encuentros salvajes en esta zona."), box_w / 2, 85, 2, Color.new(150, 160, 175), ink]
      ])
    elsif land_count > 0
      # Cuadrícula de 2 filas: 2, 3 o 4 columnas
      cols = if land_count <= 4
               [land_count, 2].max
             elsif land_count <= 6
               3
             else
               4
             end

      col_w = area_w / cols
      @land_species.each_with_index do |specie, i|
        next if i >= 8
        c = i % cols
        r = i / cols # 0 o 1
        slot_cx = 14 + c * col_w + (col_w / 2)
        slot_cy = (r == 0) ? 62 : 118
        createPokemonIcon("land_#{i}", specie, box_x + slot_cx, box_y + slot_cy)
      end
    end

    # Transición suave de apertura
    pbFadeInAndShow(@sprites)

    # 4. Bucle de espera (se cierra con C, B, Espacio o Intro como un diálogo)
    loop do
      Graphics.update
      Input.update
      pbUpdateSpriteHash(@sprites)

      if Input.trigger?(Input::C) || Input.trigger?(Input::B)
        pbPlayDecisionSE
        break
      end
    end

    dispose
  end

  def createPokemonIcon(key, specie, x, y)
    spec_id = (specie.is_a?(Numeric) ? specie : getID(PBSpecies, specie)) rescue 0
    return if !spec_id || spec_id <= 0

    sprite = nil
    begin
      sprite = PokemonSpeciesIconSprite.new(spec_id, @viewport)
    rescue
      sprite = (PokemonSpeciesIconSprite.new(0, @viewport) rescue nil)
    end
    return if !sprite

    sprite.ox = 32
    sprite.oy = 32
    sprite.x = x
    sprite.y = y
    sprite.z = @viewport.z + 2
    sprite.zoom_x = 0.85
    sprite.zoom_y = 0.85

    # Verificación Pokédex:
    # No visto -> Silueta completamente negra
    # Visto / Capturado -> Icono a todo color original
    seen = $Trainer ? ($Trainer.hasSeen?(spec_id) || $Trainer.hasOwned?(spec_id)) : false
    if seen
      sprite.tone = Tone.new(0, 0, 0, 0)
    else
      sprite.tone = Tone.new(-255, -255, -255, 0)
    end

    @sprites[key] = sprite
  end

  def dispose
    pbFadeOutAndHide(@sprites)
    pbDisposeSpriteHash(@sprites)
    @viewport.dispose
  end
end

#===============================================================================
# Helper global de extracción de datos de encuentros
#===============================================================================
def pbGetRouteEncountersData(map_id)
  encdata = (load_data("Data/encounters.dat") rescue nil)
  return [[], []] if !encdata || !encdata[map_id] || !encdata[map_id][1]

  tables = encdata[map_id][1]
  land = []
  fish = []
  seen_land = {}
  seen_fish = {}

  tables.each_with_index do |table, t_idx|
    next if !table || !table.is_a?(Array)
    is_fishing = (t_idx == 4 || t_idx == 5 || t_idx == 6) # OldRod, GoodRod, SuperRod

    table.each do |slot|
      next if !slot || !slot[0]
      sp = slot[0]
      if is_fishing
        if !seen_fish[sp]
          seen_fish[sp] = true
          fish.push(sp)
        end
      else
        if !seen_land[sp]
          seen_land[sp] = true
          land.push(sp)
        end
      end
    end
  end

  return [land[0...8], fish[0...2]]
end

#===============================================================================
# Llamada polimórfica para eventos de carteles de ruta:
#   pbRouteSign
#   pbRouteSign("Ruta 1")
#   pbRouteSign(4)
#   pbRouteSign(4, "Costa Sepiola")
#   pbRouteSign(nil, "Ruta de Test", [PBSpecies::PIDGEY, ...], [PBSpecies::MAGIKARP])
#===============================================================================
def pbRouteSign(param1=nil, param2=nil, custom_land=nil, custom_fish=nil)
  map_id = nil
  title = nil

  if param1.is_a?(Numeric)
    map_id = param1
    title  = param2 if param2.is_a?(String)
  elsif param1.is_a?(String)
    title  = param1
    map_id = param2 if param2.is_a?(Numeric)
  elsif param2.is_a?(String)
    title  = param2
    map_id = param1 if param1.is_a?(Numeric)
  end

  REM_RouteSign_Scene.new(map_id, title, custom_land, custom_fish).pbStart
end
