#===============================================================================
# INCUBADORA PORTÁTIL NOIR (Egg Hatcher)
# Permite transportar e incubar hasta 6 huevos sin ocupar espacio en el equipo.
# Acumula pasos al caminar, con bonificación de Cuerpo Llama y Escudo Magma.
#===============================================================================

class PokemonGlobalMetadata
  def eggs
    @eggs ||= [nil, nil, nil, nil, nil, nil]
    return @eggs
  end

  def eggs=(val)
    @eggs = val
  end
end

# Acceso desde la mochila usando el Objeto Clave :INCUBADORA
ItemHandlers::UseFromBag.add(:INCUBADORA, proc { |item|
  pbFadeOutIn(99999) {
    scene = REM_EggHatcher_Scene.new
    scene.pbStart
  }
  next 1
})

# Acceso directo por llamada de script
def pbOpenEggHatcher
  pbFadeOutIn(99999) {
    scene = REM_EggHatcher_Scene.new
    scene.pbStart
  }
end

def openHatcher
  pbOpenEggHatcher
end

#===============================================================================
# Sprite animado y cápsula individual de huevo
#===============================================================================
class REM_EggSlotSprite < SpriteWrapper
  attr_reader :index
  attr_accessor :selected

  def initialize(viewport, index, x, y)
    super(viewport)
    @index = index
    @x_pos = x
    @y_pos = y
    @selected = false
    @sprites = {}
    @current_frameskip = nil

    # Bitmap de la cápsula (ancho 76, alto 118)
    self.bitmap = Bitmap.new(76, 118)
    self.x = @x_pos
    self.y = @y_pos
    self.z = viewport.z + 1

    refresh(nil)
  end

  def dispose
    pbDisposeSpriteHash(@sprites)
    super
  end

  def update
    super
    pbUpdateSpriteHash(@sprites)
  end

  def refresh(pokemon)
    @pokemon = pokemon
    bmp = self.bitmap
    bmp.clear

    silver = defined?(REM_UI::SILVER) ? REM_UI::SILVER : Color.new(214, 219, 228)
    ink    = defined?(REM_UI::INK) ? REM_UI::INK : Color.new(13, 14, 18)

    # 1. Fondo de la cápsula Noir
    bg_color = @selected ? Color.new(28, 34, 48, 240) : Color.new(20, 24, 34, 235)
    bmp.fill_rect(2, 2, 72, 114, bg_color)

    # 2. Marco exterior
    if @selected
      # Borde cian iluminado al estar seleccionado
      border_col = Color.new(110, 195, 255)
      glow_col   = Color.new(60, 140, 210, 150)
      bmp.fill_rect(2, 0, 72, 1, border_col)
      bmp.fill_rect(2, 117, 72, 1, border_col)
      bmp.fill_rect(0, 2, 1, 114, border_col)
      bmp.fill_rect(75, 2, 1, 114, border_col)
      bmp.fill_rect(2, 1, 72, 1, glow_col)
      bmp.fill_rect(2, 116, 72, 1, glow_col)
      bmp.fill_rect(1, 2, 1, 114, glow_col)
      bmp.fill_rect(74, 2, 1, 114, glow_col)
    else
      # Borde plateado Noir discreto
      dark = Color.new(40, 45, 60)
      bmp.fill_rect(2, 0, 72, 1, silver)
      bmp.fill_rect(2, 117, 72, 1, silver)
      bmp.fill_rect(0, 2, 1, 114, silver)
      bmp.fill_rect(75, 2, 1, 114, silver)
      bmp.fill_rect(2, 1, 72, 1, dark)
      bmp.fill_rect(2, 116, 72, 1, dark)
      bmp.fill_rect(1, 2, 1, 114, dark)
      bmp.fill_rect(74, 2, 1, 114, dark)
    end

    # 3. Número de ranura en la esquina superior
    pbSetNarrowFont(bmp)
    bmp.font.size = 13
    num_col = @selected ? Color.new(180, 225, 255) : silver
    pbDrawTextPositions(bmp, [["0#{@index + 1}", 10, 4, 0, num_col, ink]])

    # 4. Contenido de la cápsula
    if @pokemon
      # Huevo presente: sprite animado
      steps = @pokemon.eggsteps || 0
      frameskip = 20
      frameskip = 15 if steps < 10200
      frameskip = 10 if steps < 2550
      frameskip = 5  if steps < 1275

      if @sprites["egg"] && !@sprites["egg"].disposed? && @current_frameskip != frameskip
        @sprites["egg"].dispose
        @sprites.delete("egg")
      end

      if !@sprites["egg"] || @sprites["egg"].disposed?
        @sprites["egg"] = AnimatedSprite.create("Graphics/Icons/iconEgg", 2, frameskip, self.viewport)
        @sprites["egg"].x = self.x + 6
        @sprites["egg"].y = self.y + 16
        @sprites["egg"].z = self.z + 1
        @current_frameskip = frameskip
      end
      @sprites["egg"].play

      # Barra de progreso mini (ancho 56, alto 5)
      max_steps = 10200.0
      pct = [[1.0 - (steps / max_steps), 0.0].max, 1.0].min
      bar_w = (56 * pct).round
      bmp.fill_rect(10, 84, 56, 5, Color.new(30, 35, 45))
      if bar_w > 0
        fill_col = pct >= 0.8 ? Color.new(110, 235, 140) : Color.new(110, 195, 255)
        bmp.fill_rect(10, 84, bar_w, 5, fill_col)
      end
      bmp.fill_rect(10, 84, 56, 1, Color.new(60, 70, 90))

      # Pasos restantes en número
      bmp.font.size = 14
      step_col = @selected ? Color.new(255, 255, 255) : Color.new(210, 220, 235)
      pbDrawTextPositions(bmp, [["#{steps}p", 38, 93, 2, step_col, ink]])
    else
      # Cápsula vacía
      if @sprites["egg"] && !@sprites["egg"].disposed?
        @sprites["egg"].dispose
        @sprites.delete("egg")
      end
      @current_frameskip = nil

      # Icono vacío / silueta tenue
      bmp.fill_rect(24, 38, 28, 36, Color.new(30, 36, 48, 120))
      bmp.fill_rect(26, 36, 24, 40, Color.new(30, 36, 48, 120))
      
      bmp.font.size = 14
      pbDrawTextPositions(bmp, [[_INTL("VACÍO"), 38, 88, 2, Color.new(100, 110, 125), ink]])
    end
  end
end

#===============================================================================
# Escena principal de la Incubadora Noir
#===============================================================================
class REM_EggHatcher_Scene
  def initialize
    $PokemonGlobal.eggs ||= [nil, nil, nil, nil, nil, nil]
    while $PokemonGlobal.eggs.length < 6
      $PokemonGlobal.eggs.push(nil)
    end

    @viewport = Viewport.new(0, 0, Graphics.width, Graphics.height)
    @viewport.z = 99999
    @sprites = {}
    @slots = []
    @index = 0

    # 1. Fondo Noir completo
    @sprites["bg"] = Sprite.new(@viewport)
    @sprites["bg"].bitmap = Bitmap.new(Graphics.width, Graphics.height)
    drawNoirBackground(@sprites["bg"].bitmap)

    # 2. Panel derecho de telemetría e inspección
    @sprites["panel"] = BitmapSprite.new(216, 250, @viewport)
    @sprites["panel"].x = 280
    @sprites["panel"].y = 74
    @sprites["panel"].z = @viewport.z + 1

    # 3. Crear las 6 ranuras de incubación (2 filas x 3 columnas)
    for i in 0...6
      row = i / 3
      col = i % 3
      x = 20 + col * 84
      y = 74 + row * 132
      slot = REM_EggSlotSprite.new(@viewport, i, x, y)
      @slots.push(slot)
    end

    # 4. Barra inferior de comandos / ayuda
    @sprites["bottom_bar"] = BitmapSprite.new(Graphics.width, 36, @viewport)
    @sprites["bottom_bar"].x = 0
    @sprites["bottom_bar"].y = Graphics.height - 36
    @sprites["bottom_bar"].z = @viewport.z + 2
    drawBottomBar

    refresh
  end

  def drawNoirBackground(bmp)
    bmp.fill_rect(0, 0, bmp.width, bmp.height, Color.new(14, 16, 22))

    # Trama sutil de fondo
    for y in (0...bmp.height).step(4)
      bmp.fill_rect(0, y, bmp.width, 1, Color.new(18, 22, 30))
    end

    silver = defined?(REM_UI::SILVER) ? REM_UI::SILVER : Color.new(214, 219, 228)

    # Marco superior de cabecera
    bmp.fill_rect(10, 10, bmp.width - 20, 52, Color.new(20, 24, 34, 240))
    bmp.fill_rect(10, 10, bmp.width - 20, 1, silver)
    bmp.fill_rect(10, 61, bmp.width - 20, 1, silver)
    bmp.fill_rect(10, 10, 1, 52, silver)
    bmp.fill_rect(bmp.width - 11, 10, 1, 52, silver)

    # Marco decorativo del panel derecho
    bmp.fill_rect(278, 72, 220, 254, Color.new(20, 24, 34, 240))
    bmp.fill_rect(278, 72, 220, 1, silver)
    bmp.fill_rect(278, 325, 220, 1, silver)
    bmp.fill_rect(278, 72, 1, 254, silver)
    bmp.fill_rect(497, 72, 1, 254, silver)
  end

  def drawBottomBar
    bmp = @sprites["bottom_bar"].bitmap
    bmp.clear
    bmp.fill_rect(0, 0, bmp.width, bmp.height, Color.new(12, 14, 18, 245))
    bmp.fill_rect(0, 0, bmp.width, 1, Color.new(45, 50, 65))
    pbSetNarrowFont(bmp)
    bmp.font.size = 16
    silver = defined?(REM_UI::SILVER) ? REM_UI::SILVER : Color.new(214, 219, 228)
    ink    = defined?(REM_UI::INK) ? REM_UI::INK : Color.new(13, 14, 18)
    help = _INTL("[C] Gestionar    [B] Salir    [Flechas] Seleccionar cápsula")
    pbDrawTextPositions(bmp, [[help, bmp.width / 2, 7, 2, silver, ink]])
  end

  def refresh
    eggs = $PokemonGlobal.eggs
    count = eggs.compact.length

    silver = defined?(REM_UI::SILVER) ? REM_UI::SILVER : Color.new(214, 219, 228)
    ink    = defined?(REM_UI::INK) ? REM_UI::INK : Color.new(13, 14, 18)

    # 1. Cabecera (Título y contador)
    bg = @sprites["bg"].bitmap
    bg.fill_rect(12, 12, bg.width - 24, 48, Color.new(20, 24, 34, 240))
    pbSetNarrowFont(bg)
    bg.font.size = 24
    pbDrawTextPositions(bg, [
      [_INTL("INCUBADORA PORTÁTIL"), 24, 22, 0, Color.new(255, 255, 255), ink]
    ])
    bg.font.size = 16
    pbDrawTextPositions(bg, [
      [_INTL("Huevos en gestación: {1} / 6", count), bg.width - 32, 26, 1, silver, ink]
    ])

    # 2. Actualizar las 6 ranuras
    for i in 0...6
      @slots[i].selected = (i == @index)
      @slots[i].refresh(eggs[i])
    end

    # 3. Actualizar panel derecho de telemetría
    drawInspectionPanel(eggs[@index])
  end

  def drawInspectionPanel(pokemon)
    bmp = @sprites["panel"].bitmap
    bmp.clear

    pbSetNarrowFont(bmp)
    silver = defined?(REM_UI::SILVER) ? REM_UI::SILVER : Color.new(214, 219, 228)
    white  = Color.new(255, 255, 255)
    ink    = defined?(REM_UI::INK) ? REM_UI::INK : Color.new(13, 14, 18)

    # Encabezado del panel
    bmp.font.size = 17
    pbDrawTextPositions(bmp, [
      [_INTL("DIAGNÓSTICO TÉRMICO"), bmp.width / 2, 8, 2, Color.new(110, 195, 255), ink]
    ])
    bmp.fill_rect(12, 34, bmp.width - 24, 1, Color.new(45, 50, 65))

    if pokemon
      steps = pokemon.eggsteps || 0
      max_steps = 10200.0
      pct = [[(1.0 - (steps / max_steps)) * 100, 0.0].max, 100.0].min

      # Estado de gestación
      state_text = if steps < 1275
                     _INTL("¡Está haciendo ruidos y crujidos! ¡A punto de eclosionar!")
                   elsif steps < 2550
                     _INTL("A veces se mueve con fuerza. Debería abrirse muy pronto.")
                   elsif steps < 10200
                     _INTL("¿Qué saldrá de él? Aún le queda recorrido para abrirse.")
                   else
                     _INTL("Parece que a este Huevo aún le tomará mucho tiempo abrirse.")
                   end

      bmp.font.size = 15
      drawTextEx(bmp, 12, 44, bmp.width - 24, 3, state_text, silver, ink)

      # Sección de progreso
      bmp.fill_rect(12, 116, bmp.width - 24, 1, Color.new(45, 50, 65))
      bmp.font.size = 14
      pbDrawTextPositions(bmp, [
        [_INTL("Progreso de incubación:"), 12, 124, 0, silver, ink],
        [_INTL("{1}%", pct.round), bmp.width - 12, 124, 1, Color.new(110, 195, 255), ink]
      ])

      # Barra de progreso grande (ancho 192, alto 10)
      bmp.fill_rect(12, 146, 192, 10, Color.new(14, 16, 22))
      fill_w = (192 * (pct / 100.0)).round
      if fill_w > 0
        fill_col = pct >= 80 ? Color.new(110, 235, 140) : Color.new(110, 195, 255)
        bmp.fill_rect(12, 146, fill_w, 10, fill_col)
      end
      bmp.fill_rect(12, 146, 192, 1, Color.new(60, 70, 90))

      # Pasos restantes
      pbDrawTextPositions(bmp, [
        [_INTL("Pasos restantes:"), 12, 164, 0, silver, ink],
        [_INTL("{1}", steps), bmp.width - 12, 164, 1, white, ink]
      ])

      # Origen del huevo
      obtain = (pokemon.obtainText rescue "") || ""
      if obtain == "" && pokemon.obtainMap && pokemon.obtainMap > 0
        mapname = (pbGetMapNameFromId(pokemon.obtainMap) rescue "") || ""
        obtain = _INTL("Hallado en: {1}", mapname) if mapname != ""
      end

      if obtain != ""
        bmp.fill_rect(12, 190, bmp.width - 24, 1, Color.new(45, 50, 65))
        bmp.font.size = 13
        drawTextEx(bmp, 12, 196, bmp.width - 24, 2, obtain, Color.new(160, 170, 185), ink)
      end
    else
      # Mensaje para ranura vacía
      bmp.font.size = 15
      desc = _INTL("Cápsula de incubación disponible.\n\nPulsa [C] para seleccionar un Huevo de tu equipo y empezar a incubarlo mientras caminas.")
      drawTextEx(bmp, 12, 54, bmp.width - 24, 5, desc, Color.new(160, 170, 185), ink)
    end
  end

  def dispose
    for slot in @slots
      slot.dispose
    end
    pbDisposeSpriteHash(@sprites)
    @viewport.dispose
  end

  def pbStart
    loop do
      Graphics.update
      Input.update
      for slot in @slots
        slot.update
      end

      # Salir con tecla B (X/Escape)
      if Input.trigger?(Input::B)
        pbPlayCancelSE
        break
      end

      # Navegación izquierda / derecha
      if Input.trigger?(Input::RIGHT) && (@index % 3) < 2
        @index += 1
        pbPlayCursorSE
        refresh
      elsif Input.trigger?(Input::LEFT) && (@index % 3) > 0
        @index -= 1
        pbPlayCursorSE
        refresh
      # Navegación arriba / abajo
      elsif Input.trigger?(Input::DOWN) && @index < 3
        @index += 3
        pbPlayCursorSE
        refresh
      elsif Input.trigger?(Input::UP) && @index >= 3
        @index -= 3
        pbPlayCursorSE
        refresh
      end

      # Acción con tecla C (Intro / Z)
      if Input.trigger?(Input::C)
        handleSlotAction
      end
    end

    dispose
  end

  def handleSlotAction
    eggs = $PokemonGlobal.eggs
    target_egg = eggs[@index]

    if target_egg.nil?
      # Ranura vacía: introducir un huevo desde el equipo
      has_party_egg = $Trainer.party.any? { |pkmn| pkmn && pkmn.egg? }
      if !has_party_egg
        Kernel.pbMessage(_INTL("No tienes ningún Huevo en tu equipo Pokémon."))
        return
      end

      if Kernel.pbConfirmMessage(_INTL("¿Quieres introducir un Huevo en esta cápsula?"))
        chosen = -1
        pbFadeOutIn(99999) {
          scene = PokemonScreen_Scene.new
          screen = PokemonScreen.new(scene, $Trainer.party)
          chosen = screen.pbChooseAblePokemon(proc { |poke| poke && poke.egg? }, false)
        }

        if chosen >= 0
          chosen_pkmn = $Trainer.party[chosen]
          if !chosen_pkmn.egg?
            Kernel.pbMessage(_INTL("El Pokémon seleccionado no es un Huevo."))
          else
            eggs[@index] = chosen_pkmn
            $Trainer.party.delete_at(chosen)
            pbPlayDecisionSE
            Kernel.pbMessage(_INTL("¡El Huevo fue transferido a la incubadora!"))
            refresh
          end
        end
      end
    else
      # Ranura ocupada: gestionar el huevo
      commands = [_INTL("Retirar al equipo")]
      commands.push(_INTL("Fijar pasos a 1 (Debug)")) if $DEBUG
      commands.push(_INTL("Eliminar Huevo (Debug)")) if $DEBUG
      commands.push(_INTL("Cancelar"))

      cmd = Kernel.pbShowCommands(nil, commands, -1, 0)
      if cmd == 0
        # Retirar al equipo
        if $Trainer.party.length >= 6
          Kernel.pbMessage(_INTL("Tu equipo Pokémon ya está lleno (6 Pokémon)."))
        else
          $Trainer.party.push(target_egg)
          eggs[@index] = nil
          pbPlayDecisionSE
          Kernel.pbMessage(_INTL("El Huevo ha sido devuelto a tu equipo."))
          refresh
        end
      elsif $DEBUG && cmd == 1
        # Debug: fijar pasos a 1
        target_egg.eggsteps = 1
        pbPlayDecisionSE
        Kernel.pbMessage(_INTL("Pasos del Huevo fijados a 1."))
        refresh
      elsif $DEBUG && cmd == 2
        # Debug: eliminar huevo
        if Kernel.pbConfirmMessage(_INTL("¿Seguro que deseas eliminar este Huevo?"))
          eggs[@index] = nil
          pbPlayDecisionSE
          refresh
        end
      end
    end
  end
end

#===============================================================================
# Acumulación de pasos en Overworld (Events.onStepTaken)
#===============================================================================
Events.onStepTaken += proc { |sender, e|
  next if !$Trainer || !$PokemonGlobal || !$PokemonGlobal.eggs

  has_flame_body = false
  for pkmn in $Trainer.pokemonParty
    if isConst?(pkmn.ability, PBAbilities, :FLAMEBODY) ||
       isConst?(pkmn.ability, PBAbilities, :MAGMAARMOR)
      has_flame_body = true
      break
    end
  end

  for i in 0...$PokemonGlobal.eggs.length
    egg = $PokemonGlobal.eggs[i]
    next if egg.nil?

    if egg.eggsteps && egg.eggsteps > 0
      egg.eggsteps -= 1
      egg.eggsteps -= 1 if has_flame_body && egg.eggsteps > 0

      if egg.eggsteps <= 0
        egg.eggsteps = 0
        $PokemonGlobal.eggs[i] = nil
        pbHatch(egg)

        # Tras eclosionar, añadir al equipo o almacenar en PC
        if $Trainer.party.length < 6
          $Trainer.party.push(egg)
        else
          pbStorePokemon(egg)
        end
      end
    end
  end
}

#===============================================================================
# Función auxiliar para añadir huevos recibidos directamente a la incubadora
#===============================================================================
def pbAddEggToIncubator(egg)
  return false if !egg || !$PokemonGlobal
  $PokemonGlobal.eggs ||= [nil, nil, nil, nil, nil, nil]
  for i in 0...6
    if $PokemonGlobal.eggs[i].nil?
      $PokemonGlobal.eggs[i] = egg
      return true
    end
  end
  return false
end
