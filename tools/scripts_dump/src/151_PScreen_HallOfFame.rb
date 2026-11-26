#===============================================================================
# BW Hall of Fame (KleinStudio / FL / Adaptado a Pokémon REM Oniria Noir)
# Secuencia cinemática estilo Gen 5 (Blanco y Negro) con estética Noir:
# 1. El Pokémon entra de espaldas caminando hacia las profundidades del Hall.
# 2. Gira y entra de frente en escala heroica 2.0x centrado con estandarte de tipo.
# 3. Grito de combate, temblor y datos de nivel/nombre centrados en barras.
# 4. Salida del Pokémon y entrada del siguiente miembro.
# 5. Descenso final del Entrenador con cuadro de honor simétrico y sello giratorio.
#===============================================================================

class HallOfFameScene
  SINGLEROW       = false
  ANIMATION       = true
  ENTRYWAITTIME   = 40    # Frames de exhibición de frente en el centro (~1 segundo)
  HALLLIMIT       = 50
  ENTRYMUSIC      = "HallofFame"
  ALLOWEGGS       = false
  FINALFADESPEED  = 16

  BASECOLOR   = Color.new(214, 219, 228)  # Plata Noir
  SHADOWCOLOR = Color.new(35, 40, 52)     # Sombra obsidiana

  def pbUpdate
    pbUpdateSpriteHash(@sprites)
    if @sprites["ball"]
      @sprites["ball"].angle -= 1
      @sprites["ball"].angle %= 360
    end
  end

  def pbSetupHallFont(bitmap, size = 24)
    pbSetNarrowFont(bitmap)
    bitmap.font.size = size
  end

  def pbGetHallTypeGraphic(type_id)
    typename = PBTypes.getName(type_id) rescue "Normal"
    name_map = {
      "Lucha" => "Luch",
      "Normal" => "NORMAL"
    }
    target = name_map[typename] || typename
    if pbResolveBitmap("Graphics/Pictures/HallOfFame/" + target)
      return target
    elsif pbResolveBitmap("Graphics/Pictures/HallOfFame/" + typename)
      return typename
    else
      return "NORMAL"
    end
  end

  def slowFadeOut(sprites, exponent)
    extraWaitExponent = exponent - 9
    exponent = 8 if 8 < exponent
    max = 2**exponent
    speed = (2**8) / max
    for j in 0..max
      pbWait(2**extraWaitExponent) if extraWaitExponent > -1
      pbSetSpritesToColor(sprites, Color.new(0, 0, 0, j * speed))
      block_given? ? yield : pbUpdateSpriteHash(sprites)
    end
  end

  def restartSpritePosition(sprites, spritename)
    sprites[spritename].dispose if sprites.include?(spritename) && sprites[spritename]
    sprites[spritename] = nil
  end

  # Inicialización de la escena cinemática
  def pbStartScene
    @sprites = {}
    @viewport = Viewport.new(0, 0, Graphics.width, Graphics.height)
    @viewport.z = 99999

    @sprites["bg"] = Sprite.new(@viewport)
    @sprites["bg"].bitmap = RPG::Cache.picture("HallOfFame/BG")
    @sprites["bg"].tone = Tone.new(-25, -25, -25)

    @sprites["typeback"] = Sprite.new(@viewport)
    @sprites["typeback"].bitmap = RPG::Cache.picture("HallOfFame/NORMAL")
    @sprites["typeback"].tone = Tone.new(-60, -60, -60, 10)
    @sprites["typeback"].opacity = 0
    @sprites["typeback"].z = 3

    @sprites["typebg"] = Sprite.new(@viewport)
    @sprites["typebg"].bitmap = RPG::Cache.picture("HallOfFame/NORMAL")
    @sprites["typebg"].opacity = 0
    @sprites["typebg"].z = 4

    # Barra superior (y=40, alto=47)
    @sprites["barup"] = Sprite.new(@viewport)
    @sprites["barup"].bitmap = RPG::Cache.picture("HallOfFame/hallbars")
    @sprites["barup"].y = 40
    @sprites["barup"].x = -352
    @sprites["barup"].src_rect.set(0, 0, 352, 47)
    @sprites["barup"].z = 8

    # Barra inferior (y=330, alto=47)
    @sprites["bardown"] = Sprite.new(@viewport)
    @sprites["bardown"].bitmap = RPG::Cache.picture("HallOfFame/hallbars")
    @sprites["bardown"].y = 330
    @sprites["bardown"].x = Graphics.width
    @sprites["bardown"].src_rect.set(0, 48, 352, 47)
    @sprites["bardown"].z = 8

    @sprites["barupov"] = BitmapSprite.new(352, 47, @viewport)
    @sprites["barupov"].y = 40
    @sprites["barupov"].x = -352
    @sprites["barupov"].z = 9
    pbSetupHallFont(@sprites["barupov"].bitmap, 24)

    @sprites["bardownov"] = BitmapSprite.new(352, 47, @viewport)
    @sprites["bardownov"].y = 330
    @sprites["bardownov"].x = Graphics.width
    @sprites["bardownov"].z = 9
    pbSetupHallFont(@sprites["bardownov"].bitmap, 24)

    @sprites["overlay"] = BitmapSprite.new(Graphics.width, Graphics.height, @viewport)
    @sprites["overlay"].z = 10
    pbSetupHallFont(@sprites["overlay"].bitmap, 24)

    @alreadyFadedInEnd = false
    @useMusic = false
    @showWin = false
    @isEnd = 0
    @battlerIndex = 0
    @hallEntry = []
    @faseinfo = []
    @playcry = []
    @holdtimer = []
  end

  def pbStartSceneEntry
    pbStartScene
    @useMusic = (ENTRYMUSIC && ENTRYMUSIC != "")
    pbBGMPlay(ENTRYMUSIC) if @useMusic
    saveHallEntry
    createBattlers
    pbFadeInAndShow(@sprites) { pbUpdate }
  end

  def saveHallEntry
    for i in 0...$Trainer.party.length
      @hallEntry.push($Trainer.party[i].clone) if (!$Trainer.party[i].isEgg? || ALLOWEGGS)
    end
    $PokemonGlobal.hallOfFame.push(@hallEntry)
    $PokemonGlobal.hallOfFameLastNumber += 1
    $PokemonGlobal.hallOfFame.delete_at(0) if HALLLIMIT > -1 && $PokemonGlobal.hallOfFame.size > HALLLIMIT
  end

  def createBattlers(hide = true)
    for i in 0...6
      restartSpritePosition(@sprites, "pokemon#{i}")
      next if i >= @hallEntry.size
      pok = @hallEntry[i]
      @sprites["pokemon#{i}"] = PokemonSprite.new(@viewport)
      # Comienza de espaldas (Back Sprite) ligeramente compacto (0.9x) alejándose hacia el Salón
      @sprites["pokemon#{i}"].setPokemonBitmap(pok, true)
      @sprites["pokemon#{i}"].zoom_x = 0.9
      @sprites["pokemon#{i}"].zoom_y = 0.9
      bw = @sprites["pokemon#{i}"].bitmap ? @sprites["pokemon#{i}"].bitmap.width : 96
      bh = @sprites["pokemon#{i}"].bitmap ? @sprites["pokemon#{i}"].bitmap.height : 96
      @sprites["pokemon#{i}"].ox = bw / 2
      @sprites["pokemon#{i}"].oy = bh / 2
      # Comienza a la derecha de la pantalla para cruzar de espaldas
      @sprites["pokemon#{i}"].x = Graphics.width + 120
      @sprites["pokemon#{i}"].y = 208
      @sprites["pokemon#{i}"].z = 7
      @faseinfo[i] = 0
      @holdtimer[i] = 0
      @playcry[i] = false
    end
  end

  def pbUpdateAnimation
    if @battlerIndex < @hallEntry.size && !@showWin
      if !@showinfo || !@showinfo[@battlerIndex]
        movePokemonPresentation(@battlerIndex)
      else
        @battlerIndex += 1
        if @battlerIndex < @hallEntry.size
          @sprites["overlay"].bitmap.clear
        else
          # Todos los Pokémon presentados: entrada del Entrenador
          createTrainerBattler
        end
      end
    elsif @showWin
      writeTrainerData
      if @isEnd == 1
        fadeSpeed = ((Math.log(2**12) - Math.log(FINALFADESPEED)) / Math.log(2)).floor
        pbBGMFade((2**fadeSpeed).to_f / 20) if @useMusic
        slowFadeOut(@sprites, fadeSpeed) { pbUpdate }
        @alreadyFadedInEnd = true
        @battlerIndex += 1
        @isEnd = 2
      end
    elsif @battlerIndex >= @hallEntry.size && !@showWin
      moveTrainerPresentation
    end
  end

  # Animación cinemática completa de cada Pokémon (de espaldas y luego de frente centrado)
  def movePokemonPresentation(i)
    spr = @sprites["pokemon#{i}"]
    return if !spr
    @showinfo ||= []
    pok = @hallEntry[i]

    # Fase 0: Entrada de espaldas caminando hacia el Salón (derecha hacia izquierda)
    if @faseinfo[i] == 0
      spr.x -= 20
      bob = ((spr.x.abs / 16) % 2 == 0) ? 2 : 0
      spr.y = 208 - bob
      if spr.x < -140
        @faseinfo[i] = 1
      end
    end

    # Fase 1: Giro al frente a escala media ideal (1.4x), centrado y preparación de barras y tipo
    if @faseinfo[i] == 1
      spr.setPokemonBitmap(pok, false) # Front sprite
      bw = spr.bitmap ? spr.bitmap.width : 96
      bh = spr.bitmap ? spr.bitmap.height : 96
      
      # Punto medio armónico: 1.4x (con tope de 185px para especies gigantes)
      scale = 1.4
      if bh * scale > 185
        scale = 185.0 / bh
      end
      spr.zoom_x = scale
      spr.zoom_y = scale

      spr.ox = bw / 2
      spr.oy = bh / 2
      spr.x = -140
      spr.y = 208

      typename = pbGetHallTypeGraphic(pok.type1)
      @sprites["typebg"].bitmap = RPG::Cache.picture("HallOfFame/" + typename)
      @sprites["typeback"].bitmap = RPG::Cache.picture("HallOfFame/" + typename)
      @sprites["typebg"].opacity = 0
      @sprites["typeback"].opacity = 0

      overlayup = @sprites["barupov"].bitmap
      overlayup.clear
      pbSetupHallFont(overlayup, 24)
      pbDrawTextPositions(overlayup, [[_INTL("¡El Hall de la Fama!"), 16, 11, 0, BASECOLOR, SHADOWCOLOR]])

      overlaydown = @sprites["bardownov"].bitmap
      overlaydown.clear
      pbSetupHallFont(overlaydown, 24)
      pbDrawTextPositions(overlaydown, [
        [pok.name, 24, 11, 0, BASECOLOR, SHADOWCOLOR],
        [_INTL("Nv. {1}", pok.level), 250, 11, 0, BASECOLOR, SHADOWCOLOR]
      ])

      @bgshake = 0
      @faseinfo[i] = 2
    end

    # Fase 2: Entrada al centro de frente, barras, destello elemental y grito
    if @faseinfo[i] == 2
      # Desplazamiento de barras hacia el centro
      @sprites["barup"].x += 35 if @sprites["barup"].x < 0
      @sprites["barup"].x = 0 if @sprites["barup"].x > 0
      @sprites["barupov"].x = @sprites["barup"].x

      @sprites["bardown"].x -= 35 if @sprites["bardown"].x > Graphics.width - 352
      @sprites["bardown"].x = Graphics.width - 352 if @sprites["bardown"].x < Graphics.width - 352
      @sprites["bardownov"].x = @sprites["bardown"].x

      # Opacidad del fondo de tipo
      @sprites["typebg"].opacity += 20 if @sprites["typebg"].opacity < 225
      @sprites["typeback"].opacity = @sprites["typebg"].opacity

      # Desplazamiento del Pokémon de frente hacia el centro geométrico (256)
      target_center = Graphics.width / 2
      if spr.x < target_center
        spr.x += 24
        spr.x = target_center if spr.x > target_center
      else
        # Ya está centrado: grito, temblor y pausa de exhibición
        if !@playcry[i]
          pbPlayCry(pok)
          @playcry[i] = true
        end

        case @bgshake
        when 0..1; @sprites["typebg"].x = 4
        when 2..3; @sprites["typebg"].x = -4
        when 4..5; @sprites["typebg"].x = 2
        when 6..7; @sprites["typebg"].x = -2
        else;      @sprites["typebg"].x = 0
        end
        @bgshake += 1 if @bgshake < 8

        @sprites["typeback"].opacity -= 3 if @sprites["typeback"].opacity > 0

        @holdtimer[i] += 1
        if @holdtimer[i] >= ENTRYWAITTIME
          @faseinfo[i] = 3
        end
      end
    end

    # Fase 3: Salida del Pokémon hacia la izquierda y retirada de barras
    if @faseinfo[i] == 3
      @sprites["barup"].x -= 35 if @sprites["barup"].x > -352
      @sprites["barup"].x = -352 if @sprites["barup"].x < -352
      @sprites["barupov"].x = @sprites["barup"].x

      @sprites["bardown"].x += 35 if @sprites["bardown"].x < Graphics.width
      @sprites["bardown"].x = Graphics.width if @sprites["bardown"].x > Graphics.width
      @sprites["bardownov"].x = @sprites["bardown"].x

      spr.x -= 28
      @sprites["typebg"].opacity -= 25 if @sprites["typebg"].opacity > 0

      if spr.x < -180 && @sprites["barup"].x <= -352 && @sprites["bardown"].x >= Graphics.width
        @sprites["typebg"].opacity = 0
        @sprites["typeback"].opacity = 0
        @showinfo[i] = true
      end
    end
  end

  # Creación del cuadro final con el Entrenador y su equipo simétrico
  def createTrainerBattler
    # Sello de Pokéball giratorio en marca de agua sutil
    @sprites["ball"] = Sprite.new(@viewport)
    @sprites["ball"].bitmap = RPG::Cache.picture("HallOfFame/hallball")
    @sprites["ball"].x = Graphics.width / 2
    @sprites["ball"].y = 190
    @sprites["ball"].ox = @sprites["ball"].bitmap.width / 2
    @sprites["ball"].oy = @sprites["ball"].bitmap.height / 2
    @sprites["ball"].blend_type = 1
    @sprites["ball"].opacity = 35
    @sprites["ball"].z = 2

    # Marco completo de Campeón (halltrainerbars.png)
    @sprites["halltrainer"] = Sprite.new(@viewport)
    @sprites["halltrainer"].bitmap = RPG::Cache.picture("HallOfFame/halltrainerbars")
    @sprites["halltrainer"].y = 0
    @sprites["halltrainer"].opacity = 0
    @sprites["halltrainer"].z = 8

    # Distribución simétrica del equipo alrededor del entrenador
    num_pokes = @hallEntry.size
    left_count = (num_pokes + 1) / 2
    right_count = num_pokes - left_count

    left_xs = (left_count == 1) ? [115] : (left_count == 2) ? [80, 155] : [55, 115, 175]
    right_xs = (right_count == 1) ? [397] : (right_count == 2) ? [357, 432] : [337, 397, 457]
    all_xs = left_xs + right_xs

    for i in 0...num_pokes
      pok = @hallEntry[i]
      @sprites["pokemon#{i}"] = PokemonSprite.new(@viewport)
      @sprites["pokemon#{i}"].setPokemonBitmap(pok, false)
      @sprites["pokemon#{i}"].zoom_x = 1.0
      @sprites["pokemon#{i}"].zoom_y = 1.0
      bw = @sprites["pokemon#{i}"].bitmap ? @sprites["pokemon#{i}"].bitmap.width : 96
      bh = @sprites["pokemon#{i}"].bitmap ? @sprites["pokemon#{i}"].bitmap.height : 96
      @sprites["pokemon#{i}"].ox = bw / 2
      @sprites["pokemon#{i}"].oy = bh
      @sprites["pokemon#{i}"].x = all_xs[i]
      # Base horizontal alineada en y=275
      @sprites["pokemon#{i}"].y = 275
      @sprites["pokemon#{i}"].z = 6
    end

    # Entrenador descendiendo desde arriba al centro
    @sprites["trainer"] = IconSprite.new(@viewport)
    @sprites["trainer"].setBitmap(pbTrainerSpriteFile($Trainer.trainertype))
    @sprites["trainer"].ox = @sprites["trainer"].bitmap.width / 2
    @sprites["trainer"].oy = @sprites["trainer"].bitmap.height / 2
    @sprites["trainer"].x = Graphics.width / 2
    @sprites["trainer"].y = -@sprites["trainer"].bitmap.height
    @sprites["trainer"].z = 9

    @sprites["overlay"].bitmap.clear
    @sprites["overlay"].opacity = 0

    overlay = @sprites["overlay"].bitmap
    pbSetupHallFont(overlay, 24)
    pubid = sprintf("%05d", $Trainer.publicID($Trainer.id))
    totalsec = Graphics.frame_count / Graphics.frame_rate
    hour = totalsec / 60 / 60
    min = (totalsec / 60) % 60

    texts = [
      [_INTL("¡Felicidades, {1}!", $Trainer.name), Graphics.width / 2, 37, 2, BASECOLOR, SHADOWCOLOR],
      [_INTL("CAMPEÓN DE LA LIGA"), 24, 325, 0, BASECOLOR, SHADOWCOLOR],
      [_INTL("ID: {1}", pubid), Graphics.width / 2, 325, 2, BASECOLOR, SHADOWCOLOR],
      [_ISPRINTF("Tiempo: {1:02d}:{2:02d}", hour, min), Graphics.width - 24, 325, 1, BASECOLOR, SHADOWCOLOR]
    ]
    pbDrawTextPositions(overlay, texts)
  end

  def moveTrainerPresentation
    tr = @sprites["trainer"]
    return if !tr
    target_y = 185
    if tr.y < target_y
      tr.y += 12
      tr.y = target_y if tr.y > target_y
    else
      if @sprites["halltrainer"].opacity < 255
        @sprites["halltrainer"].opacity += 20
        @sprites["overlay"].opacity = @sprites["halltrainer"].opacity
      else
        @showWin = true
      end
    end
  end

  def writeTrainerData
    if Input.trigger?(Input::C) || Input.trigger?(Input::B)
      @isEnd = 1
    end
  end

  def pbEndScene
    $game_map.autoplay if @useMusic
    Kernel.pbDisposeMessageWindow(@sprites["msgwindow"]) if @sprites.include?("msgwindow")
    pbFadeOutAndHide(@sprites) { pbUpdate } if !@alreadyFadedInEnd
    pbDisposeSpriteHash(@sprites)
    @viewport.dispose
  end

  def pbAnimationLoop
    loop do
      Graphics.update
      Input.update
      pbUpdate
      pbUpdateAnimation
      break if @battlerIndex == @hallEntry.size + 2
    end
  end

  # ===========================================================================
  # Visor del Hall de la Fama en el PC
  # ===========================================================================
  def pbStartScenePC
    @sprites = {}
    @viewport = Viewport.new(0, 0, Graphics.width, Graphics.height)
    @viewport.z = 99999

    @sprites["bg"] = Sprite.new(@viewport)
    @sprites["bg"].bitmap = RPG::Cache.picture("HallOfFame/famerecordbg")

    @sprites["overlay"] = BitmapSprite.new(Graphics.width, Graphics.height, @viewport)
    @sprites["overlay"].z = 10
    pbSetupHallFont(@sprites["overlay"].bitmap, 24)

    @hallIndex = $PokemonGlobal.hallOfFame.size - 1
    @hallEntry = $PokemonGlobal.hallOfFame[-1] || []
    createBattlersPC
    writePCData
    pbFadeInAndShow(@sprites) { pbUpdate }
  end

  def createBattlersPC
    for i in 0...6
      restartSpritePosition(@sprites, "pokemon#{i}")
      next if i >= @hallEntry.size
      pok = @hallEntry[i]
      @sprites["pokemon#{i}"] = PokemonSprite.new(@viewport)
      @sprites["pokemon#{i}"].setPokemonBitmap(pok, false)
      @sprites["pokemon#{i}"].x = 40 + (i % 3) * 150
      @sprites["pokemon#{i}"].y = 80 + (i / 3) * 130
      @sprites["pokemon#{i}"].y += adjustBattleSpriteY(@sprites["pokemon#{i}"], pok.species, 3)
    end
  end

  def writePCData
    overlay = @sprites["overlay"].bitmap
    overlay.clear
    title = [
      [_INTL("HALL DE LA FAMA — REGISTRO No. {1}", @hallIndex + 1), Graphics.width / 2, 16, 2, BASECOLOR, SHADOWCOLOR],
      [_INTL("Registro {1} de {2}  |  [←/→] Cambiar  [B] Salir", @hallIndex + 1, $PokemonGlobal.hallOfFame.size), Graphics.width / 2, Graphics.height - 32, 2, BASECOLOR, SHADOWCOLOR]
    ]
    pbDrawTextPositions(overlay, title)
  end

  def pbPCSelection
    loop do
      Graphics.update
      Input.update
      pbUpdate
      if Input.trigger?(Input::LEFT) && $PokemonGlobal.hallOfFame.size > 1
        pbSEPlay("menu")
        @hallIndex -= 1
        @hallIndex = $PokemonGlobal.hallOfFame.size - 1 if @hallIndex < 0
        @hallEntry = $PokemonGlobal.hallOfFame[@hallIndex]
        writePCData
        createBattlersPC
      elsif Input.trigger?(Input::RIGHT) && $PokemonGlobal.hallOfFame.size > 1
        pbSEPlay("menu")
        @hallIndex += 1
        @hallIndex = 0 if @hallIndex >= $PokemonGlobal.hallOfFame.size
        @hallEntry = $PokemonGlobal.hallOfFame[@hallIndex]
        writePCData
        createBattlersPC
      elsif Input.trigger?(Input::B)
        pbSEPlay("menu")
        break
      end
    end
  end
end

class HallOfFameScreen
  def initialize(scene)
    @scene = scene
  end

  def pbStartScreenEntry
    @scene.pbStartSceneEntry
    @scene.pbAnimationLoop
    @scene.pbEndScene
  end

  def pbStartScreenPC
    @scene.pbStartScenePC
    @scene.pbPCSelection
    @scene.pbEndScene
  end
end

class HallOfFamePC
  def shouldShow?
    return $PokemonGlobal.hallOfFameLastNumber > 0
  end

  def name
    return _INTL("Hall de la Fama")
  end

  def access
    Kernel.pbMessage(_INTL("\\se[accesspc]Acceso al Hall de la Fama concedido."))
    pbHallOfFamePC
  end
end

PokemonPCList.registerPC(HallOfFamePC.new)

class PokemonGlobalMetadata
  attr_accessor :hallOfFame
  attr_accessor :hallOfFameLastNumber

  def hallOfFame
    @hallOfFame = [] if !@hallOfFame
    return @hallOfFame
  end

  def hallOfFameLastNumber
    @hallOfFameLastNumber = 0 if !@hallOfFameLastNumber
    return @hallOfFameLastNumber
  end
end

def pbHallOfFameEntry
  scene = HallOfFameScene.new
  screen = HallOfFameScreen.new(scene)
  screen.pbStartScreenEntry
end

def pbHallOfFamePC
  scene = HallOfFameScene.new
  screen = HallOfFameScreen.new(scene)
  screen.pbStartScreenPC
end
