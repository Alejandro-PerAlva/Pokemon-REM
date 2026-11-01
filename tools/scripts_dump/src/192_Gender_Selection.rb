#===============================================================================
# * Gender Selection Script - Versión Limpia (Sin nombres ni variables fijas)
#===============================================================================
class PokemonGenderSelection
 
  def initialize
    @select=1; @close=0
    @viewport=Viewport.new(0,0,Graphics.width,Graphics.height)
    @viewport.z=99999
    @sprites={}
   
    # Carga de imágenes (Asegúrate de tenerlas en Graphics/Pictures/GenderSelection/)
    @sprites["1"]=IconSprite.new(0,0,@viewport)
    @sprites["1"].setBitmap("Graphics/Pictures/GenderSelection/default")
   
    @sprites["2"]=IconSprite.new(0,0,@viewport)
    @sprites["2"].setBitmap("Graphics/Pictures/GenderSelection/boy_1")
    @sprites["2"].visible=false
   
    @sprites["3"]=IconSprite.new(0,0,@viewport)
    @sprites["3"].setBitmap("Graphics/Pictures/GenderSelection/boy_2")
    @sprites["3"].visible=false
   
    @sprites["4"]=IconSprite.new(0,0,@viewport)
    @sprites["4"].setBitmap("Graphics/Pictures/GenderSelection/girl_1")
    @sprites["4"].visible=false
   
    @sprites["5"]=IconSprite.new(0,0,@viewport)
    @sprites["5"].setBitmap("Graphics/Pictures/GenderSelection/girl_2")
    @sprites["5"].visible=false
    
    pbWait(10)
    main_method
  end
 
  def input  
    if Input.trigger?(Input::RIGHT) && (@select==1 || @select==4)
      @select=2
    elsif Input.trigger?(Input::LEFT) && (@select==1 || @select==2)
      @select=4
    end
    
    if Input.trigger?(Input::C)
      @select+=1
      actualizar_visibilidad
      self.continue
    end
    
    if defined?($mouse) && $mouse.leftClick?
      if $mouse.over?(@sprites["2"]) || $mouse.over?(@sprites["4"])
        @select+=1
        actualizar_visibilidad
        self.continue
      end
    end
  end
 
  def actualizar_visibilidad
    for i in 1..5
      @sprites["#{i}"].visible = (@select==i)
    end
  end

  def main_method
    while @close!=1
      Graphics.update
      Input.update
      actualizar_visibilidad
      input
    end
  end
 
  def continue
    # SELECCIÓN CHICO
    if @select==3
      pbWait(20)
      if Kernel.pbConfirmMessage(_INTL("¿Elegir al chico?"))
        pbChangePlayer(0) # ID 0 suele ser el chico en Essentials
        finalizar_escena
      else
        @select=2
      end
    # SELECCIÓN CHICA
    elsif @select==5
      pbWait(20)
      if Kernel.pbConfirmMessage(_INTL("¿Elegir a la chica?"))
        pbChangePlayer(1) # ID 1 suele ser la chica en Essentials
        finalizar_escena
      else
        @select=4
      end
    end
  end

  def finalizar_escena
    @close=1
    20.times do
      @sprites["#{@select}"].opacity -= 13
      Graphics.update
      pbWait(1)
    end
    pbDisposeSpriteHash(@sprites)
    @viewport.dispose
  end
end