#===============================================================================
# MÓDULO DE MODO TURBO (Activado con la tecla CONTROL)
#===============================================================================
module Graphics
  # Variable para saber si el turbo está activado
  @turbo_toggle = false

  class << self
    alias turbo_update update
    def update
      # Detectamos si se PULSA la tecla (Input.trigger)
      # Esto solo ocurre una vez por pulsación, aunque dejes el dedo puesto
      if Input.trigger?(Input::CTRL)
        @turbo_toggle = !@turbo_toggle # Cambia de verdadero a falso y viceversa
      end

      # Aplicamos la velocidad según el estado del interruptor
      if @turbo_toggle
        Graphics.frame_rate = 100 # Velocidad Turbo
      else
        Graphics.frame_rate = 40  # Velocidad Normal
      end

      turbo_update
    end
  end
end