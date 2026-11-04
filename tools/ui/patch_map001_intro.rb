# Uso: ruby tools/ui/patch_map001_intro.rb [--check]   (desde la raíz). Reescribe los eventos de Data/Map001.rxdata:
#   Intro (id 1)         -> autorrun; si !$DEBUG: pbRemStoryIntro
#   Inicio rápido (id 2) -> autorrun; si  $DEBUG: pbRemDebugIntro
# Guarda Data/Map001.rxdata.bak_pre_intro una vez. Strings en binario (sin ivar de codificación; RGSS1).
module RPG
  class Map; end; class Event; class Page; class Condition; end; class Graphic; end; end; end
  class EventCommand; end; class MoveRoute; end; class MoveCommand; end; class AudioFile; end
end
class Table; def self._load(s); o=new; o.instance_variable_set(:@raw,s); o; end; def _dump(l=-1); @raw; end; end
class Color; def self._load(s); o=new; o.instance_variable_set(:@raw,s); o; end; def _dump(l=-1); @raw; end; end
class Tone;  def self._load(s); o=new; o.instance_variable_set(:@raw,s); o; end; def _dump(l=-1); @raw; end; end
f='Data/Map001.rxdata'; bak=f+'.bak_pre_intro'
File.binwrite(bak,File.binread(f)) if !File.exist?(bak)
raw=File.binread(bak)
m=Marshal.load(raw)
if ARGV.include?('--check'); puts(Marshal.dump(m)==raw ? 'round-trip IDÉNTICO' : 'round-trip DIFIERE'); exit; end
def cmd(code,indent,*params)
  c=RPG::EventCommand.allocate
  c.instance_variable_set(:@code,code); c.instance_variable_set(:@indent,indent)
  c.instance_variable_set(:@parameters,params.map{|p| p.is_a?(String) ? p.dup.force_encoding('BINARY') : p})
  c
end
def build(branch_expr,script,comment)
  l=[]
  comment.each_with_index{|t,i| l<<cmd(i==0 ? 108 : 408,0,t)}
  l<<cmd(123,0,"A",0)                         # self-switch A: el autorrun no se repite
  l<<cmd(111,0,12,branch_expr)                 # Si <script>
  l<<cmd(355,1,script)
  l<<cmd(0,1)
  l<<cmd(411,0)                                # Si no
  l<<cmd(0,1)
  l<<cmd(412,0)                                # Fin
  l<<cmd(355,0,"pbToneChangeAll(Tone.new(0,0,0,0),20)")
  l<<cmd(0,0)
  l
end
ev=m.instance_variable_get(:@events)
{1=>['!$DEBUG','pbRemStoryIntro',["Intro de historia (partida normal): carta, selector de entrenador, nombre y traslado a Casa Player.","Solo se ejecuta fuera del modo debug. Código: REM_Intro en Scripts (REM_UI)."]],
 2=>['$DEBUG','pbRemDebugIntro',["Intro de debug (Inicio rápido): equipo aleatorio, mochila completa, sistemas desbloqueados y menú de destino.","Solo se ejecuta en modo debug. Destinos editables: REM_DEBUG_DESTINATIONS en REM_UI."]]}.each{|id,(expr,scr,com)|
  e=ev[id]; pg=e.instance_variable_get(:@pages)[0]
  pg.instance_variable_set(:@trigger,3)       # autorrun
  pg.instance_variable_set(:@list,build(expr,scr,com))
}
File.binwrite(f,Marshal.dump(m))
puts "Map001 OK"
