class Scene_DebugIntro
  def initialize
    if !$pkmn_animations
      $pkmn_animations = load_data("Data/PkmnAnimations.rxdata")
    end
  end
  
  def main
    Graphics.transition(0)
    sscene=PokemonLoadScene.new
    sscreen=PokemonLoad.new(sscene)
    sscreen.pbStartLoadScreen
    Graphics.freeze
  end
end



def pbCallTitle #:nodoc:
  # Siempre pasa por la pantalla de título (Scene_Intro, ver Title_Screen):
  # Arranque -> Título -> Pulsar C/Start -> Continuar / Nueva partida (PokemonLoad).
  # (Antes, con $DEBUG, se usaba Scene_DebugIntro y se saltaba el título.)
  return Scene_Intro.new(['intro1'], 'splash')
end

def mainFunction #:nodoc:
  if $DEBUG
    pbCriticalCode { mainFunctionDebug }
  else
    mainFunctionDebug
  end
  return 1
end

def mainFunctionDebug #:nodoc:
  begin
    getCurrentProcess=Win32API.new("kernel32.dll","GetCurrentProcess","","l")
    setPriorityClass=Win32API.new("kernel32.dll","SetPriorityClass",%w(l i),"")
    setPriorityClass.call(getCurrentProcess.call(),32768) # "Above normal" priority class
    $data_animations    = pbLoadRxData("Data/Animations")
    $data_tilesets      = pbLoadRxData("Data/Tilesets")
    $data_common_events = pbLoadRxData("Data/CommonEvents")
    $data_system        = pbLoadRxData("Data/System")
    $game_system        = Game_System.new
    setScreenBorderName("border") # Estable el archivo de imágen para los bordes
    Graphics.update
    Graphics.freeze
    $scene = pbCallTitle
    while $scene != nil
      $scene.main
    end
    Graphics.transition(20)
  rescue Hangup
    pbEmergencySave
    raise
  end
end

loop do
  retval=mainFunction
  if retval==0 # falla
    loop do
      Graphics.update
    end
  elsif retval==1 # termina exitosamente
    break
  end
end