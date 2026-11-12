#===============================================================================
# INCUBADORA PORTÁTIL NOIR (Egg Hatcher)
# Dispositivo de cápsula única integrado en el menú de Pokémon (tecla D).
# Los huevos solo se transportan aquí: no ocupan ranuras de equipo ni de cajas.
# Al completarse los pasos, se abre manualmente desde esta interfaz con [C].
#===============================================================================

class PokemonGlobalMetadata
  attr_accessor :incubator_egg

  def egg
    return @incubator_egg
  end

  def egg=(val)
    @incubator_egg = val
  end

  # Compatibilidad con cualquier llamada anterior
  def eggs
    return [@incubator_egg]
  end

  def eggs=(val)
    @incubator_egg = val.is_a?(Array) ? val.compact.first : val
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
# Control de Recepción de Huevos (pbGenerateEgg y Guardería)
#===============================================================================
def pbGenerateEgg(pokemon, text = "")
  # 1. Comprobar si el jugador dispone de la Incubadora
  if !$PokemonBag || !$PokemonBag.pbHasItem?(:INCUBADORA)
    Kernel.pbMessage(_INTL("No dispones de una Incubadora para transportar este Huevo."))
    return false
  end

  # 2. Comprobar si la Incubadora ya está ocupada
  if $PokemonGlobal && $PokemonGlobal.egg != nil
    Kernel.pbMessage(_INTL("Tu Incubadora ya contiene un Huevo en gestación."))
    return false
  end

  # 3. Preguntar confirmación al jugador
  if !Kernel.pbConfirmMessage(_INTL("¿Quieres añadir el Huevo a tu Incubadora?"))
    Kernel.pbMessage(_INTL("Decidiste no recibir el Huevo."))
    return false
  end

  # 4. Crear el Pokémon huevo
  if pokemon.is_a?(String) || pokemon.is_a?(Symbol)
    pokemon = getID(PBSpecies, pokemon)
  end
  if pokemon.is_a?(Integer)
    pokemon = PokeBattle_Pokemon.new(pokemon, EGGINITIALLEVEL, $Trainer)
  end

  dexdata = pbOpenDexData
  pbDexDataOffset(dexdata, pokemon.species, 21)
  eggsteps = dexdata.fgetw
  dexdata.close

  pokemon.name = _INTL("Huevo")
  pokemon.eggsteps = eggsteps
  pokemon.obtainText = text
  pokemon.calcStats

  $PokemonGlobal.egg = pokemon
  pbPlayDecisionSE
  Kernel.pbMessage(_INTL("¡El Huevo fue colocado en la Incubadora!"))
  return true
end

# Hook para la entrega de huevos de la Guardería
if defined?(pbDayCareGenerateEgg)
  alias rem_orig_pbDayCareGenerateEgg pbDayCareGenerateEgg
  def pbDayCareGenerateEgg
    if !$PokemonBag || !$PokemonBag.pbHasItem?(:INCUBADORA)
      Kernel.pbMessage(_INTL("No dispones de una Incubadora para transportar el Huevo."))
      return false
    end
    if $PokemonGlobal && $PokemonGlobal.egg != nil
      Kernel.pbMessage(_INTL("Tu Incubadora ya contiene un Huevo en gestación."))
      return false
    end
    if !Kernel.pbConfirmMessage(_INTL("¿Quieres añadir el Huevo a tu Incubadora?"))
      Kernel.pbMessage(_INTL("Decidiste no recibir el Huevo."))
      return false
    end

    party_len = $Trainer.party.length
    rem_orig_pbDayCareGenerateEgg
    if $Trainer.party.length > party_len
      egg = $Trainer.party.pop
      $PokemonGlobal.egg = egg
      pbPlayDecisionSE
      Kernel.pbMessage(_INTL("¡El Huevo de la Guardería fue colocado en la Incubadora!"))
      return true
    end
    return true
  end
end

#===============================================================================
# Acumulación de pasos en Overworld (Events.onStepTaken)
#===============================================================================
Events.onStepTaken += proc { |sender, e|
  next if !$Trainer || !$PokemonGlobal || !$PokemonGlobal.egg

  egg = $PokemonGlobal.egg
  if egg.eggsteps && egg.eggsteps > 0
    egg.eggsteps -= 1
    has_flame_body = false
    for pkmn in $Trainer.pokemonParty
      if isConst?(pkmn.ability, PBAbilities, :FLAMEBODY) ||
         isConst?(pkmn.ability, PBAbilities, :MAGMAARMOR)
        has_flame_body = true
        break
      end
    end
    egg.eggsteps -= 1 if has_flame_body && egg.eggsteps > 0
    egg.eggsteps = 0 if egg.eggsteps < 0
  end
  # Al llegar a 0 no se abre automáticamente: el jugador entra y lo abre con [C].
}

#===============================================================================
# Escena principal de la Incubadora Noir (Cápsula Única)
#===============================================================================
class REM_EggHatcher_Scene
  def initialize
    @viewport = Viewport.new(0, 0, Graphics.width, Graphics.height)
    @viewport.z = 99999
    @sprites = {}
    @current_frameskip = nil

    # 1. Fondo Noir completo
    @sprites["bg"] = Sprite.new(@viewport)
    @sprites["bg"].bitmap = Bitmap.new(Graphics.width, Graphics.height)
    drawNoirBackground(@sprites["bg"].bitmap)

    # 2. Cápsula de Incubación (Lado izquierdo)
    @sprites["chamber"] = BitmapSprite.new(176, 270, @viewport)
    @sprites["chamber"].x = 40
    @sprites["chamber"].y = 74
    @sprites["chamber"].z = @viewport.z + 1

    # 3. Panel de Diagnóstico Térmico (Lado derecho)
    @sprites["panel"] = BitmapSprite.new(244, 270, @viewport)
    @sprites["panel"].x = 232
    @sprites["panel"].y = 74
    @sprites["panel"].z = @viewport.z + 1

    refresh
  end

  def drawNoirBackground(bmp)
    bmp.fill_rect(0, 0, bmp.width, bmp.height, Color.new(14, 16, 22))

    # Trama sutil de fondo
    y = 0
    while y < bmp.height
      bmp.fill_rect(0, y, bmp.width, 1, Color.new(18, 22, 30))
      y += 4
    end

    silver = defined?(REM_UI::SILVER) ? REM_UI::SILVER : Color.new(214, 219, 228)

    # Marco superior de cabecera
    bmp.fill_rect(10, 10, bmp.width - 20, 52, Color.new(20, 24, 34, 240))
    bmp.fill_rect(10, 10, bmp.width - 20, 1, silver)
    bmp.fill_rect(10, 61, bmp.width - 20, 1, silver)
    bmp.fill_rect(10, 10, 1, 52, silver)
    bmp.fill_rect(bmp.width - 11, 10, 1, 52, silver)

    # Marco de la cápsula izquierda
    bmp.fill_rect(38, 72, 180, 274, Color.new(20, 24, 34, 240))
    bmp.fill_rect(38, 72, 180, 1, silver)
    bmp.fill_rect(38, 345, 180, 1, silver)
    bmp.fill_rect(38, 72, 1, 274, silver)
    bmp.fill_rect(217, 72, 1, 274, silver)

    # Marco del panel derecho
    bmp.fill_rect(230, 72, 248, 274, Color.new(20, 24, 34, 240))
    bmp.fill_rect(230, 72, 248, 1, silver)
    bmp.fill_rect(230, 345, 248, 1, silver)
    bmp.fill_rect(230, 72, 1, 274, silver)
    bmp.fill_rect(477, 72, 1, 274, silver)
  end

  def refresh
    egg = $PokemonGlobal ? $PokemonGlobal.egg : nil

    silver = defined?(REM_UI::SILVER) ? REM_UI::SILVER : Color.new(214, 219, 228)
    ink    = defined?(REM_UI::INK) ? REM_UI::INK : Color.new(13, 14, 18)

    # 1. Cabecera
    bg = @sprites["bg"].bitmap
    bg.fill_rect(12, 12, bg.width - 24, 48, Color.new(20, 24, 34, 240))
    pbSetNarrowFont(bg)
    bg.font.size = 24
    pbDrawTextPositions(bg, [
      [_INTL("INCUBADORA PORTÁTIL"), 24, 22, 0, Color.new(255, 255, 255), ink]
    ])
    bg.font.size = 17
    status_label = egg ? (egg.eggsteps == 0 ? _INTL("ESTADO: ¡LISTO PARA ABRIR!") : _INTL("ESTADO: EN GESTACIÓN")) : _INTL("ESTADO: CÁPSULA DISPONIBLE")
    status_color = egg ? (egg.eggsteps == 0 ? Color.new(110, 235, 140) : Color.new(110, 195, 255)) : silver
    pbDrawTextPositions(bg, [
      [status_label, bg.width - 32, 25, 1, status_color, ink]
    ])

    # 2. Dibujar Cámara de Incubación
    drawChamber(egg)

    # 3. Dibujar Panel de Diagnóstico
    drawInspectionPanel(egg)
  end

  def drawChamber(egg)
    bmp = @sprites["chamber"].bitmap
    bmp.clear

    silver = defined?(REM_UI::SILVER) ? REM_UI::SILVER : Color.new(214, 219, 228)
    ink    = defined?(REM_UI::INK) ? REM_UI::INK : Color.new(13, 14, 18)

    # Fondo interior de la cápsula
    bmp.fill_rect(2, 2, bmp.width - 4, bmp.height - 4, Color.new(16, 22, 32))

    # Trama vertical de contenedor
    x = 6
    while x < bmp.width - 6
      bmp.fill_rect(x, 4, 1, bmp.height - 8, Color.new(22, 30, 44))
      x += 8
    end

    # Pedestal inferior metálico
    bmp.fill_rect(16, 216, bmp.width - 32, 14, Color.new(35, 42, 58))
    bmp.fill_rect(16, 216, bmp.width - 32, 1, silver)
    bmp.fill_rect(24, 230, bmp.width - 48, 6, Color.new(24, 28, 40))

    if egg
      steps = egg.eggsteps || 0
      ready = (steps == 0)

      # Gráfico del huevo: usa el battler sprite real de eclosión (Graphics/Battlers/egg)
      # a tamaño amplio (zoom 0.85 -> 136x94 px) centrado sobre el pedestal
      if !@sprites["egg"] || @sprites["egg"].disposed?
        @sprites["egg"] = PokemonSprite.new(@viewport)
        @sprites["egg"].setSpeciesBitmap(egg.species, false, 0, false, false, false, true)
        @sprites["egg"].ox = 80
        @sprites["egg"].oy = 158
        @sprites["egg"].zoom_x = 0.85
        @sprites["egg"].zoom_y = 0.85
        @sprites["egg"].x = @sprites["chamber"].x + (bmp.width / 2)
        @sprites["egg"].y = @sprites["chamber"].y + 216
        @sprites["egg"].z = @sprites["chamber"].z + 2
      end

      # Etiqueta inferior de estado del huevo
      pbSetNarrowFont(bmp)
      if ready
        bmp.font.size = 17
        bmp.fill_rect(10, 236, bmp.width - 20, 26, Color.new(25, 55, 38, 220))
        bmp.fill_rect(10, 236, bmp.width - 20, 1, Color.new(110, 235, 140))
        bmp.fill_rect(10, 261, bmp.width - 20, 1, Color.new(110, 235, 140))
        pbDrawTextPositions(bmp, [
          [_INTL("¡LISTO PARA ABRIR!"), bmp.width / 2, 239, 2, Color.new(110, 235, 140), ink]
        ])
      else
        bmp.font.size = 17
        bmp.fill_rect(10, 236, bmp.width - 20, 26, Color.new(20, 26, 36, 220))
        pbDrawTextPositions(bmp, [
          [_INTL("{1} PASOS", steps), bmp.width / 2, 239, 2, Color.new(255, 255, 255), ink]
        ])
      end
    else
      if @sprites["egg"] && !@sprites["egg"].disposed?
        @sprites["egg"].dispose
        @sprites.delete("egg")
      end

      # Silueta vacía estilizada en el pedestal
      bmp.fill_rect((bmp.width - 64) / 2, 115, 64, 96, Color.new(24, 32, 46, 90))
      bmp.fill_rect((bmp.width - 64) / 2 + 6, 108, 52, 106, Color.new(24, 32, 46, 90))
      pbSetNarrowFont(bmp)
      bmp.font.size = 17
      bmp.fill_rect(10, 236, bmp.width - 20, 26, Color.new(20, 26, 36, 220))
      pbDrawTextPositions(bmp, [
        [_INTL("CÁPSULA VACÍA"), bmp.width / 2, 239, 2, Color.new(130, 140, 155), ink]
      ])
    end
  end

  def drawInspectionPanel(egg)
    bmp = @sprites["panel"].bitmap
    bmp.clear

    pbSetNarrowFont(bmp)
    silver = defined?(REM_UI::SILVER) ? REM_UI::SILVER : Color.new(214, 219, 228)
    white  = Color.new(255, 255, 255)
    ink    = defined?(REM_UI::INK) ? REM_UI::INK : Color.new(13, 14, 18)

    # 1. Encabezado del panel
    bmp.font.size = 20
    pbDrawTextPositions(bmp, [
      [_INTL("DIAGNÓSTICO TÉRMICO"), bmp.width / 2, 7, 2, Color.new(110, 195, 255), ink]
    ])
    bmp.fill_rect(12, 33, bmp.width - 24, 1, Color.new(50, 56, 72))

    if egg
      steps = egg.eggsteps || 0
      ready = (steps == 0)
      max_steps = 10200.0
      pct = ready ? 100 : [[(1.0 - (steps / max_steps)) * 100, 0.0].max, 99.0].min

      # 2. Estado de gestación con 2 líneas fijas delimitadas (sin posibilidad de desborde ni solape)
      line1, line2 = if ready
                       [_INTL("¡El cascarón está a punto de abrirse!"), _INTL("¡Listo para eclosionar!")]
                     elsif steps < 1275
                       [_INTL("¡Hace ruidos y crujidos!"), _INTL("Eclosionará muy pronto.")]
                     elsif steps < 2550
                       [_INTL("A veces se mueve con fuerza."), _INTL("Le queda poco tiempo.")]
                     elsif steps < 10200
                       [_INTL("¿Qué Pokémon saldrá de él?"), _INTL("Aún requiere incubación.")]
                     else
                       [_INTL("Un Huevo Pokémon misterioso."), _INTL("Le tomará tiempo abrirse.")]
                     end

      bmp.font.size = 15
      pbDrawTextPositions(bmp, [
        [line1, 12, 39, 0, silver, ink],
        [line2, 12, 59, 0, ready ? Color.new(110, 235, 140) : silver, ink]
      ])

      # 3. Separador intermedio
      bmp.fill_rect(12, 82, bmp.width - 24, 1, Color.new(50, 56, 72))

      # 4. Sección de progreso de gestación
      bmp.font.size = 15
      pbDrawTextPositions(bmp, [
        [_INTL("Progreso de gestación:"), 12, 88, 0, silver, ink]
      ])
      bmp.font.size = 17
      pbDrawTextPositions(bmp, [
        [_INTL("{1}%", pct.round), bmp.width - 12, 87, 1, Color.new(110, 195, 255), ink]
      ])

      # Barra de progreso sólida (ancho 220, alto 12, y=108..120)
      bar_w = 220
      bar_h = 12
      bar_y = 108
      bmp.fill_rect(12, bar_y, bar_w, bar_h, Color.new(14, 16, 22))
      fill_w = (bar_w * (pct / 100.0)).round
      if fill_w > 0
        fill_col = ready ? Color.new(110, 235, 140) : Color.new(110, 195, 255)
        bmp.fill_rect(12, bar_y, fill_w, bar_h, fill_col)
        bmp.fill_rect(12, bar_y, fill_w, 1, Color.new(220, 245, 255, 160))
      end
      bmp.fill_rect(12, bar_y, bar_w, 1, Color.new(70, 80, 100))
      bmp.fill_rect(12, bar_y + bar_h - 1, bar_w, 1, Color.new(70, 80, 100))
      bmp.fill_rect(12, bar_y, 1, bar_h, Color.new(70, 80, 100))
      bmp.fill_rect(12 + bar_w - 1, bar_y, 1, bar_h, Color.new(70, 80, 100))

      # 5. Pasos restantes
      bmp.font.size = 15
      pbDrawTextPositions(bmp, [
        [_INTL("Pasos restantes:"), 12, 128, 0, silver, ink]
      ])
      bmp.font.size = 18
      pbDrawTextPositions(bmp, [
        [_INTL("{1}", steps), bmp.width - 12, 126, 1, white, ink]
      ])

      # 6. Separador de origen
      bmp.fill_rect(12, 150, bmp.width - 24, 1, Color.new(50, 56, 72))

      # Origen del huevo
      obtain = (egg.obtainText rescue "") || ""
      if obtain == "" && egg.obtainMap && egg.obtainMap > 0
        mapname = (pbGetMapNameFromId(egg.obtainMap) rescue "") || ""
        obtain = _INTL("Hallado en: {1}", mapname) if mapname != ""
      end

      if obtain != ""
        bmp.font.size = 14
        drawTextEx(bmp, 12, 156, bmp.width - 24, 2, obtain, Color.new(180, 190, 205), ink)
      end

      # 7. Botón de apertura (sin '[C]', limpio y destacado)
      if ready
        btn_y = 212
        bmp.fill_rect(12, btn_y, bar_w, 44, Color.new(24, 58, 38, 245))
        glow = Color.new(110, 235, 140)
        bmp.fill_rect(12, btn_y, bar_w, 1, glow)
        bmp.fill_rect(12, btn_y + 43, bar_w, 1, glow)
        bmp.fill_rect(12, btn_y, 1, 44, glow)
        bmp.fill_rect(12 + bar_w - 1, btn_y, 1, 44, glow)
        bmp.font.size = 20
        pbDrawTextPositions(bmp, [
          [_INTL("Eclosionar Huevo"), 12 + bar_w / 2, btn_y + 11, 2, Color.new(255, 255, 255), ink]
        ])
      else
        bmp.font.size = 15
        pbDrawTextPositions(bmp, [
          [_INTL("Incubación en curso."), 12, 218, 0, Color.new(160, 170, 185), ink]
        ])
        bmp.font.size = 13
        pbDrawTextPositions(bmp, [
          [_INTL("El Huevo no puede salir hasta nacer."), 12, 238, 0, Color.new(120, 130, 145), ink]
        ])
      end
    else
      # Mensaje para cápsula vacía con tipografía clara
      bmp.font.size = 16
      desc = _INTL("Cápsula de incubación disponible.\n\nCuando recibas un Huevo de una persona o de la Guardería, se colocará automáticamente en este dispositivo para su transporte y gestación.")
      drawTextEx(bmp, 12, 60, bmp.width - 24, 6, desc, Color.new(180, 190, 205), ink)
    end
  end

  def dispose
    if @sprites["egg"] && !@sprites["egg"].disposed?
      @sprites["egg"].dispose
    end
    pbDisposeSpriteHash(@sprites)
    @viewport.dispose
  end

  def pbStart
    loop do
      Graphics.update
      Input.update

      # Animación de respiración / balanceo del huevo en su pedestal
      @egg_timer = (@egg_timer || 0) + 1
      if @sprites["egg"] && !@sprites["egg"].disposed?
        egg = $PokemonGlobal ? $PokemonGlobal.egg : nil
        ready = egg && (egg.eggsteps || 0) == 0
        if ready
          # Balanceo continuo y perceptible cuando está a punto de nacer
          @sprites["egg"].angle = Math.sin(@egg_timer * 0.25) * 4.0
        else
          # Suave ciclo periódico cada ~2.5 segundos
          cycle = @egg_timer % 140
          if cycle < 30
            @sprites["egg"].angle = Math.sin(cycle * (Math::PI / 15)) * 2.5
          else
            @sprites["egg"].angle = 0
          end
        end
        @sprites["egg"].update
      end

      # Salir con tecla B (X / Escape)
      if Input.trigger?(Input::B)
        pbPlayCancelSE
        break
      end

      # Opción Debug: con tecla Y (S en teclado) o F9 en debug fuerza eclosión inmediata
      if $DEBUG && Input.trigger?(Input::Y) && $PokemonGlobal && $PokemonGlobal.egg
        $PokemonGlobal.egg.eggsteps = 0
        pbPlayDecisionSE
        refresh
      end

      # Abrir / Eclosionar Huevo con tecla C (Intro / Z)
      if Input.trigger?(Input::C)
        egg = $PokemonGlobal ? $PokemonGlobal.egg : nil
        if egg && (egg.eggsteps || 0) == 0
          pbPlayDecisionSE
          # Liberar sprite temporal del huevo en la incubadora antes de la cinemática
          if @sprites["egg"] && !@sprites["egg"].disposed?
            @sprites["egg"].dispose
            @sprites.delete("egg")
          end
          # Eclosión con cinemática Noir nativa
          pbFadeOutIn(99999) {
            pbHatch(egg)
          }
          $PokemonGlobal.egg = nil
          # Añadir al equipo o almacenar en PC
          if $Trainer.party.length < 6
            $Trainer.party.push(egg)
          else
            pbStorePokemon(egg)
          end
          refresh
        end
      end
    end

    dispose
  end
end

# Función de compatibilidad anterior
def pbAddEggToIncubator(egg)
  return false if !egg || !$PokemonGlobal
  if $PokemonGlobal.egg == nil
    $PokemonGlobal.egg = egg
    return true
  end
  return false
end
