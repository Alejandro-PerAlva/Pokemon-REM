#===============================================================================
# BW Hall of Fame (KleinStudio / FL / Adaptado a Pokémon REM Oniria Noir)
# Secuencia cinemática estilo Gen 5 (Blanco y Negro) con estética Noir,
# presentación dinámica de cada Pokémon por tipos, animaciones fluidas
# y tarjeta conmemorativa del Campeón.
#===============================================================================

class HallOfFameScene
  SINGLEROW       = false
  ANIMATION       = true
  ANIMATIONSPEED  = 32
  ENTRYWAITTIME   = 28
  HALLLIMIT       = 50
  ENTRYMUSIC      = "HallofFame"
  ALLOWEGGS       = false
  REMOVEBARS      = true
  FINALFADESPEED  = 16
  OPACITY         = 64

  BASECOLOR   = Color.new(214, 219, 228)  # Plata Noir
  SHADOWCOLOR = Color.new(35, 40, 52)     # Sombra obsidiana

  def pbUpdate
    pbUpdateSpriteHash(@sprites)
    if @sprites["ball"]
      @sprites["ball"].angle -= 1
      @sprites["ball"].angle %= 360
    end
  end

  def pbGetHallTypeGraphic(type_id)
    typename = PBTypes.getName(type_id) rescue "Normal"
    name_map = {
      "Lucha" => "Luch",
      "Normal" => "NORMAL",
      "Hada" => "Psíquico"
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

  def setPokemonSpritesOpacity(index, opacity = 255)
    for n in 0...@hallEntry.size
      @sprites["pokemon#{n}"].opacity = (n == index) ? 255 : opacity if @sprites["pokemon#{n}"]
    end
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

    @sprites["typebg"] = Sprite.new(@viewport)
    @sprites["typebg"].bitmap = RPG::Cache.picture("HallOfFame/NORMAL")
    @sprites["typebg"].opacity = 0

    @sprites["barup"] = Sprite.new(@viewport)
    @sprites["barup"].bitmap = RPG::Cache.picture("HallOfFame/hallbars")
    @sprites["barup"].y = 424 - Graphics.height
    @sprites["barup"].x = -352
    @sprites["barup"].src_rect.set(0, 0, 352, 47)

    @sprites["bardown"] = Sprite.new(@viewport)
    @sprites["bardown"].bitmap = RPG::Cache.picture("HallOfFame/hallbars")
    @sprites["bardown"].y = 714 - Graphics.height
    @sprites["bardown"].x = Graphics.width
    @sprites["bardown"].src_rect.set(0, 48, 352, 47)
    @sprites["bardown"].z = 999999

    @sprites["barupov"] = BitmapSprite.new(352, 47, @viewport)
    @sprites["barupov"].y = 424 - Graphics.height
    @sprites["barupov"].x = -352
    pbSetNarrowFont(@sprites["barupov"].bitmap)

    @sprites["bardownov"] = BitmapSprite.new(352, 47, @viewport)
    @sprites["bardownov"].y = 714 - Graphics.height
    @sprites["bardownov"].x = Graphics.width
    @sprites["bardownov"].z = 999999
    pbSetNarrowFont(@sprites["bardownov"].bitmap)

    @sprites["overlay"] = BitmapSprite.new(Graphics.width, Graphics.height, @viewport)
    @sprites["overlay"].z = 10
    pbSetNarrowFont(@sprites["overlay"].bitmap)

    @alreadyFadedInEnd = false
    @useMusic = false
    @showWin = false
    @isEnd = 0
    @battlerIndex = 0
    @hallEntry = []
    @oldPoke = -1
  end

  def pbStartSceneEntry
    pbStartScene
    @useMusic = (ENTRYMUSIC && ENTRYMUSIC != "")
    pbBGMPlay(ENTRYMUSIC) if @useMusic
    saveHallEntry
    @xmovement = []
    @ymovement = []
    @showinfo = []
    @faseinfo = []
    @playcry = []
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
      @sprites["pokemon#{i}"].setPokemonBitmap(pok, true)
      @sprites["pokemon#{i}"].y += adjustBattleSpriteY(@sprites["pokemon#{i}"], pok.species, 3)
      @faseinfo[i] = 0
      pbPositionPokemonSprite(@sprites["pokemon#{i}"], Graphics.width + 200, 660 - Graphics.height - 80)
      @sprites["pokemon#{i}"].z = 7 - i if SINGLEROW
    end
  end

  def pbUpdateAnimation
    if @battlerIndex <= @hallEntry.size && !@showWin
      if !@showinfo[@battlerIndex]
        spriteIndex = (@battlerIndex < @hallEntry.size) ? @battlerIndex : -1
        moveSprite(spriteIndex)
      else
        @battlerIndex += 1
        if @battlerIndex <= @hallEntry.size
          pbWait(ENTRYWAITTIME)
          if @battlerIndex < @hallEntry.size
            @sprites["overlay"].bitmap.clear
          else
            createTrainerBattler
          end
        end
      end
    end
    if @showWin
      writeTrainerData
      if @isEnd == 1
        fadeSpeed = ((Math.log(2**12) - Math.log(FINALFADESPEED)) / Math.log(2)).floor
        pbBGMFade((2**fadeSpeed).to_f / 20) if @useMusic
        slowFadeOut(@sprites, fadeSpeed) { pbUpdate }
        @alreadyFadedInEnd = true
        @battlerIndex += 1
        @isEnd = 2
      end
    end
  end

  def moveSprite(i)
    spritename = (i > -1) ? "pokemon#{i}" : "trainer"
    return if !@sprites[spritename]
    width = (@sprites[spritename].bitmap.width * 2) - 60

    if i > -1
      # Fase 0: Entrada rápida desde la derecha hacia la izquierda
      if @faseinfo[i] == 0
        @sprites[spritename].x -= 24
        @sprites[spritename].x = -width if @sprites[spritename].x < -width
        @faseinfo[i] = 1 if @sprites[spritename].x == -width
      end

      # Fase 1: Carga de cartel de tipo y datos del Pokémon
      if @faseinfo[i] == 1
        pok = @hallEntry[i]
        @sprites[spritename].y = 250
        @sprites[spritename].y += adjustBattleSpriteY(@sprites[spritename], @hallEntry[i].species, 3)
        @opacityx = 0
        @bgshake = 0
        @sprites["typebg"].x = 0
        @sprites["typeback"].x = 0
        @sprites[spritename].setPokemonBitmap(pok, false)

        typename = pbGetHallTypeGraphic(pok.type1)
        @sprites["typebg"].bitmap = RPG::Cache.picture("HallOfFame/" + typename)
        @sprites["typeback"].bitmap = RPG::Cache.picture("HallOfFame/" + typename)
        @sprites["typebg"].opacity += 25 if @sprites["typebg"].opacity != 225
        @sprites["typeback"].opacity = @sprites["typebg"].opacity

        # Textos en barras superior e inferior
        overlaydown = @sprites["bardownov"].bitmap
        overlaydown.clear
        texts = [
          [@hallEntry[i].name, 34, 12, 0, BASECOLOR, SHADOWCOLOR],
          [_INTL("Nv. {1}", @hallEntry[i].level), 240, 12, 0, BASECOLOR, SHADOWCOLOR]
        ]
        overlayup = @sprites["barupov"].bitmap
        overlayup.clear
        pbDrawTextPositions(overlaydown, texts)
        pbDrawTextPositions(overlayup, [[_INTL("¡El Hall de la Fama!"), 16, 12, 0, BASECOLOR, SHADOWCOLOR]])

        @faseinfo[i] = 2 if @sprites["typebg"].opacity >= 225
      end

      # Fase 2: Entrada de barras y Pokémon al centro con grito
      if @faseinfo[i] == 2
        @opacityx += 1
        @opacityx = 0 if @opacityx == 4
        @sprites["barup"].x += 60 if @sprites["barup"].x != 0
        @sprites["barup"].x = 0 if @sprites["barup"].x > 0
        @sprites["barupov"].x = @sprites["barup"].x
        @sprites["bardown"].x -= 60 if @sprites["bardown"].x != Graphics.width - 352
        @sprites["bardown"].x = Graphics.width - 352 if @sprites["bardown"].x < Graphics.width - 352
        @sprites["bardownov"].x = @sprites["bardown"].x

        @sprites[spritename].x += 24 if @sprites[spritename].x < 100
        @sprites[spritename].x = 100 if @sprites[spritename].x > 100

        if @sprites[spritename].x > 0
          if !@playcry[i]
            pbPlayCry(@hallEntry[i])
            @playcry[i] = true
          end
          # Temblor cinemático de fondo de tipo
          case @bgshake
          when 0
            @sprites["typebg"].x += 1 if @sprites["typebg"].x != 5
            @bgshake += 1 if @sprites["typebg"].x == 5
          when 1
            @sprites["typebg"].x -= 1 if @sprites["typebg"].x != 0
            @bgshake += 1 if @sprites["typebg"].x == 0
          when 2
            @sprites["typebg"].x += 1 if @sprites["typebg"].x != 3
            @bgshake += 1 if @sprites["typebg"].x == 3
          when 3
            @sprites["typebg"].x -= 1 if @sprites["typebg"].x != 0
            @bgshake += 1 if @sprites["typebg"].x == 0
          when 4
            @sprites["typebg"].x += 1 if @sprites["typebg"].x != 1
            @bgshake += 1 if @sprites["typebg"].x == 1
          when 5
            @sprites["typebg"].x -= 1 if @sprites["typebg"].x != 0
            @bgshake += 1 if @sprites["typebg"].x == 0
          end

          @sprites["typeback"].opacity -= 3.5
          @sprites["typeback"].x -= 3 if @opacityx == 3

          if @sprites["typeback"].opacity <= 0
            @sprites["typebg"].opacity -= 25
          end
        end
        @faseinfo[i] = 3 if @sprites["typebg"].opacity <= 0
      end

      # Fase 3: Retirada de barras y salida del Pokémon
      if @faseinfo[i] == 3
        @sprites["barup"].x -= 60 if @sprites["barup"].x != -352
        @sprites["barup"].x = -352 if @sprites["barup"].x < -352
        @sprites["barupov"].x = @sprites["barup"].x
        @sprites["bardown"].x += 60 if @sprites["bardown"].x != Graphics.width
        @sprites["bardown"].x = Graphics.width if @sprites["bardown"].x > Graphics.width
        @sprites["bardownov"].x = @sprites["bardown"].x

        @sprites[spritename].x -= 24
        @sprites[spritename].x = -width if @sprites[spritename].x < -width
        if @sprites[spritename].x == -width && @sprites["barup"].x == -352 && @sprites["bardown"].x == Graphics.width
          @showinfo[i] = true
        end
      end
    else
      # Entrada cinemática del Entrenador desde arriba
      @sprites[spritename].y += 14
      target_y = 190
      @sprites[spritename].y = target_y if @sprites[spritename].y > target_y
      if @sprites[spritename].y == target_y
        @sprites["halltrainer"].opacity += 25.5
        @sprites["overlay"].opacity = @sprites["halltrainer"].opacity
      end

      if @sprites["halltrainer"].opacity >= 255
        @showWin = true
        @showinfo[i] = true
      end
    end
  end

  def createTrainerBattler
    @sprites["ball"] = Sprite.new(@viewport)
    @sprites["ball"].bitmap = RPG::Cache.picture("HallOfFame/hallball")
    @sprites["ball"].x = Graphics.width / 2
    @sprites["ball"].y = 76
    @sprites["ball"].ox = @sprites["ball"].bitmap.width / 2
    @sprites["ball"].oy = @sprites["ball"].bitmap.height / 2
    @sprites["ball"].blend_type = 1
    @sprites["ball"].opacity = 140

    @sprites["halltrainer"] = Sprite.new(@viewport)
    @sprites["halltrainer"].bitmap = RPG::Cache.picture("HallOfFame/halltrainerbars")
    @sprites["halltrainer"].y = 0
    @sprites["halltrainer"].opacity = 0

    pokex = 20
    for i in 0...6
      next if i >= @hallEntry.size
      pok = @hallEntry[i]
      @sprites["pokemon#{i}"] = PokemonSprite.new(@viewport)
      @sprites["pokemon#{i}"].setPokemonBitmap(pok, false)
      @sprites["pokemon#{i}"].x = pokex
      @sprites["pokemon#{i}"].y = 230
      @sprites["pokemon#{i}"].y += adjustBattleSpriteY(@sprites["pokemon#{i}"], pok.species, 3)
      pokex += 65
      pokex += 80 if i == 2 # Hueco central para el entrenador
    end

    @sprites["trainer"] = IconSprite.new(@viewport)
    @sprites["trainer"].setBitmap(pbTrainerSpriteFile($Trainer.trainertype))
    @sprites["trainer"].x = Graphics.width / 2
    @sprites["trainer"].y = -@sprites["trainer"].bitmap.height
    @sprites["trainer"].z = 9
    @sprites["trainer"].ox = @sprites["trainer"].bitmap.width / 2
    @sprites["trainer"].oy = @sprites["trainer"].bitmap.height / 2

    @sprites["overlay"].bitmap.clear
    @sprites["overlay"].opacity = 0

    overlay = @sprites["overlay"].bitmap
    overlay.clear
    pubid = sprintf("%05d", $Trainer.publicID($Trainer.id))
    totalsec = Graphics.frame_count / Graphics.frame_rate
    hour = totalsec / 60 / 60
    min = (totalsec / 60) % 60

    texts = [
      [_INTL("¡Felicidades, {1}!", $Trainer.name), Graphics.width / 2, 28, 2, BASECOLOR, SHADOWCOLOR],
      [_INTL("CAMPEÓN DE LA LIGA"), 24, Graphics.height - 40, 0, BASECOLOR, SHADOWCOLOR],
      [_INTL("ID: {1}", pubid), Graphics.width / 2, Graphics.height - 40, 2, BASECOLOR, SHADOWCOLOR],
      [_ISPRINTF("Tiempo: {1:02d}:{2:02d}", hour, min), Graphics.width - 24, Graphics.height - 40, 1, BASECOLOR, SHADOWCOLOR]
    ]
    pbDrawTextPositions(overlay, texts)
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
    pbSetNarrowFont(@sprites["overlay"].bitmap)

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
