#===============================================================================
# Ultimate Title Screen Resource - VERSIÓN ESTABLE (GENÉRICA)
#===============================================================================
SCREENSTYLE = 0          # 0: Personalizado
GEN_CUSTOM_BGM = "Titulo" # Tu música en Audio/BGM/

RESTART_TITLE = true
PLAY_ON_DEBUG = true     # Permite ver la pantalla desde el editor
PLAY_INTRO_SCENE = false
EXPAND_STYLE = true      # Activa animaciones de fondo y logo

#===============================================================================
# MOTOR DEL SISTEMA
#===============================================================================
class Scene_Intro
  alias main_old main
  def main
    $DEBUG = $memDebug
    Graphics.transition(0)
    
    # Se eliminó por completo la lógica de especies y gritos para evitar errores
    @cry = nil 
    
    $Trainer = PokeBattle_Trainer.new("",0)
    @skip = false

    case SCREENSTYLE
    when 0; @screen = GenCustomStyle.new
    else; @screen = EssentialsTitleScreen.new
    end

    @screen.intro
    self.update
    Graphics.freeze
  end
  
  def update
    ret = 0
    loop do
      @screen.update
      Graphics.update
      Input.update
      # Salir/Borrar partida (Abajo + B + CTRL)
      if Input.press?(Input::DOWN) && Input.press?(Input::B) && Input.press?(Input::CTRL)
        ret = 1; break
      end
      # Entrar al juego (Botón C o Click Izquierdo)
      if Input.trigger?(Input::C) || (defined?($mouse) && $mouse.leftClick?)
        ret = 2; break
      end
    end
    case ret
    when 1; closeTitleDelete
    when 2; closeTitle 
    end
  end
  
  def closeTitle
    # Sonido estándar de confirmación (SE)
    pbSEPlay("realidea", 100, 100) 
    
    pbBGMStop(1.0)
    disposeTitle
    
    # Inicia el proceso de carga que lleva a tu evento de Debug
    sscene = PokemonLoadScene.new
    sscreen = PokemonLoad.new(sscene)
    sscreen.pbStartLoadScreen
  end
  
  def closeTitleDelete
    pbBGMStop(1.0)
    disposeTitle
    sscene = PokemonLoadScene.new
    sscreen = PokemonLoad.new(sscene)
    sscreen.pbStartDeleteScreen
  end

  def disposeTitle; @screen.dispose; end

  def wait(frames, advance=true)
    return false if @skip
    frames.times do
      Graphics.update
      Input.update
      @skip = true if Input.trigger?(Input::C)
    end
    return true
  end
end

#===============================================================================
# ESTILO CUSTOM
#===============================================================================
class GenCustomStyle
  def initialize
    bgm = GEN_CUSTOM_BGM
    @skip = false
    @disposed = false
    @particles = 12
    @opacity = 15
    @logoY = 0
    
    pbBGMPlay(bgm)
    
    @viewport = Viewport.new(0,0,Graphics.width,Graphics.height)
    @viewport.z = 99999
    @sprites = {}
    
    # Oniria Noir: fondo, logo y barra "PULSA START" (arte final: Graphics/Titles/intro_bg.png e intro_logo.png)
    @sprites["background"] = Sprite.new(@viewport)
    @sprites["background"].bitmap = pbBitmap("Graphics/Titles/intro_bg")

    @sprites["logo"] = Sprite.new(@viewport)
    @sprites["logo"].bitmap = pbBitmap("Graphics/Titles/intro_logo")
    @sprites["logo"].z = 100
    @sprites["logo"].ox = @sprites["logo"].bitmap.width/2
    @sprites["logo"].oy = @sprites["logo"].bitmap.height/2
    @sprites["logo"].x = @viewport.rect.width/2
    @sprites["logo"].y = @viewport.rect.height/2

    bw = Graphics.width; bh = 34
    bar = Bitmap.new(bw,bh)
    bar.fill_rect(0,0,bw,bh,Color.new(14,16,22,200))
    bar.fill_rect(0,0,bw,1,Color.new(214,219,228,150))
    bar.fill_rect(0,bh-1,bw,1,Color.new(214,219,228,150))
    pbSetSystemFont(bar)
    bar.font.size = 26
    pbDrawShadowText(bar,0,1,bw,bh,_INTL("PULSA ENTER PARA CONTINUAR"),Color.new(214,219,228),Color.new(20,22,29),1)
    @sprites["start"] = Sprite.new(@viewport)
    @sprites["start"].bitmap = bar
    @sprites["start"].z = 110
    @sprites["start"].x = 0
    @sprites["start"].y = @viewport.rect.height - 60
    @sprites["start"].opacity = 0
    
    for i in 0...@particles
      @sprites["p#{i}"] = AnimatedSpriteParticle.new(@viewport, rand(20))
      @sprites["p#{i}"].refresh
    end
  end
  
  def intro
    @viewport.color = Color.new(0,0,0,255)
    20.times do
      @viewport.color.alpha -= 13
      Graphics.update
    end
  end
  
  def update
    @sprites["start"].opacity += @opacity
    @opacity = -10 if @sprites["start"].opacity >= 255
    @opacity = 10 if @sprites["start"].opacity <= 0
    
    for i in 0...@particles
      @sprites["p#{i}"].update if @sprites["p#{i}"]
    end
    
    @logoY = Math.sin(Graphics.frame_count/25.0)*6
    @sprites["logo"].y = (@viewport.rect.height/2) + @logoY
  end
  
  def dispose
    pbFadeOutAndHide(@sprites)
    pbDisposeSpriteHash(@sprites)
    @viewport.dispose
    @disposed = true
  end

  def disposed?; return @disposed; end
end

class AnimatedSpriteParticle < Sprite
  def initialize(viewport, delay=0)
    super(viewport)
    @delay = delay
    @frame = 0
    self.refresh
    self.visible = false
  end
  
  def update
    @frame += 1
    return if @frame < @delay
    self.visible = true
    self.x += @vx
    self.y += @vy
    self.opacity -= 3
    self.refresh if self.opacity <= 0
  end
  
  def refresh
    self.opacity = 255
    self.x = rand(Graphics.width)
    self.y = rand(Graphics.height)
    @vx = (rand(10)-5)/4.0
    @vy = (rand(10)-5)/4.0
    begin
      self.bitmap = pbBitmap("Graphics/Titles/gen_6_particle")
    rescue
      self.bitmap = Bitmap.new(2,2)
      self.bitmap.fill_rect(0,0,2,2,Color.new(255,255,255))
    end
  end
end