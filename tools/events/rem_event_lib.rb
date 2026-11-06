# encoding: UTF-8
# Librería para AÑADIR eventos a Data/MapNNN.rxdata sin tocar los existentes (RMXP / RGSS1, Ruby 1.8 en el juego).
# Uso: ver tools/events/albor_events.rb y docs/EVENTOS_UBICACIONES (PBS/rem_workflow_ubicaciones.txt, paso EVENTOS).
# Reglas: (1) solo se añaden/reemplazan eventos cuyo nombre empieza por el prefijo de la ubicación (p. ej. «ALBOR_»);
#         (2) copia de seguridad única Data/MapNNN.rxdata.bak_pre_<tag> antes de escribir; (3) strings en binario (sin ivar de
#         codificación); (4) NO se tocan scripts ni otros eventos; (5) los eventos nuevos se colocan desde la casilla (0,0) en
#         orden de lectura; el diseñador los mueve a su sitio (cada evento lleva un comentario [UBICACIÓN]).
module RPG
  class Map; end; class Event; class Page; class Condition; end; class Graphic; end; end; end
  class EventCommand; end; class MoveRoute; end; class MoveCommand; end; class AudioFile; end
end
class Table; def self._load(s); o=new; o.instance_variable_set(:@raw,s); o; end; def _dump(l=-1); @raw; end; end
class Color; def self._load(s); o=new; o.instance_variable_set(:@raw,s); o; end; def _dump(l=-1); @raw; end; end
class Tone;  def self._load(s); o=new; o.instance_variable_set(:@raw,s); o; end; def _dump(l=-1); @raw; end; end

module REMEv
  def self.bin(s); s.is_a?(String) ? s.dup.force_encoding('BINARY') : s; end
  def self.cmd(code, indent, *params)
    c = RPG::EventCommand.allocate
    c.instance_variable_set(:@code, code); c.instance_variable_set(:@indent, indent)
    c.instance_variable_set(:@parameters, params.map { |p| bin(p) })
    c
  end

  # Constructor de listas de comandos con control de sangría.
  class L
    attr_reader :cmds
    def initialize; @cmds = []; @ind = 0; end
    def add(code, *p); @cmds << REMEv.cmd(code, @ind, *p); self; end
    def comment(text)
      text.to_s.split("\n").each_with_index { |t, i| add(i == 0 ? 108 : 408, t) }; self
    end
    # Script multilínea (355 + 655...). Cada línea es un parámetro.
    def script(code)
      lines = code.to_s.split("\n"); lines = [''] if lines.empty?
      lines.each_with_index { |t, i| add(i == 0 ? 355 : 655, t) }; self
    end
    def esc(t); t.to_s.gsub('\\', '\\\\\\\\').gsub('"', '\\"'); end
    # Mensaje (texto con \PN, \c[1]... escrito con UNA barra; se escapa aquí).
    def say(text); script(%{Kernel.pbMessage(_INTL("#{esc(text)}"))}); end
    def sw(id, on = true); add(121, id, id, on ? 0 : 1); end
    def var(id, val); add(122, id, id, 0, 0, val); end
    def self_sw(ch = 'A', on = true); add(123, ch, on ? 0 : 1); end
    def wait(n); add(106, n); end
    def erase; add(214); end
    # Condicionales. kind: :script (expr), :sw (id, on), :var (id, op, val), :self (ch)
    # if sin else: l.if_(:sw, 696, false) { |b| ... }
    def if_(kind, *a, &blk); ifelse(kind, *a) { [blk, nil] }; end
    # if/else: l.ifelse(:var, 121, :lt, 5) { [lambda { |b| ... }, lambda { |b| ... }] }
    def ifelse(kind, *a, &blk)
      thenb, elseb = blk.call
      params = case kind
               when :script then [12, a[0]]
               when :sw     then [0, a[0], (a[1] == false ? 1 : 0)]
               when :var    then [1, a[0], 0, a[2], { :eq => 0, :ge => 1, :le => 2, :gt => 3, :lt => 4, :ne => 5 }[a[1]]]
               when :self   then [2, a[0], 0]
               end
      add(111, *params); @ind += 1
      thenb.call(self); add(0); @ind -= 1
      add(411); @ind += 1
      elseb.call(self) if elseb; add(0); @ind -= 1
      add(412); self
    end
    def finish; add(0); @cmds; end
  end

  # Condición de página: :sw=>id, :sw2=>id, :var=>[id,min], :self=>'A'
  def self.condition(h)
    c = RPG::Event::Page::Condition.allocate
    iv = lambda { |k, v| c.instance_variable_set("@#{k}", v) }
    iv.call(:switch1_valid, !!h[:sw]);   iv.call(:switch1_id, h[:sw] || 1)
    iv.call(:switch2_valid, !!h[:sw2]);  iv.call(:switch2_id, h[:sw2] || 1)
    iv.call(:variable_valid, !!h[:var]); iv.call(:variable_id, h[:var] ? h[:var][0] : 1)
    iv.call(:variable_value, h[:var] ? h[:var][1] : 0)
    iv.call(:self_switch_valid, !!h[:self]); iv.call(:self_switch_ch, h[:self] || 'A')
    c
  end

  def self.graphic(name, dir = 2)
    g = RPG::Event::Page::Graphic.allocate
    { :tile_id => 0, :character_name => bin(name.to_s), :character_hue => 0, :direction => dir,
      :pattern => 0, :opacity => 255, :blend_type => 0 }.each { |k, v| g.instance_variable_set("@#{k}", v) }
    g
  end

  def self.move_route
    m = RPG::MoveRoute.allocate
    m.instance_variable_set(:@repeat, true); m.instance_variable_set(:@skippable, false)
    mc = RPG::MoveCommand.allocate; mc.instance_variable_set(:@code, 0); mc.instance_variable_set(:@parameters, [])
    m.instance_variable_set(:@list, [mc]); m
  end

  # trig: 0 acción, 1 contacto con el jugador, 2 contacto con evento, 3 autoejecución, 4 proceso paralelo
  def self.page(cond: {}, gfx: nil, dir: 2, trig: 0, list: nil, fixdir: false, through: false)
    pg = RPG::Event::Page.allocate
    { :condition => condition(cond), :graphic => graphic(gfx || '', dir), :move_type => 0, :move_speed => 3,
      :move_frequency => 3, :move_route => move_route, :walk_anime => true, :step_anime => false,
      :direction_fix => fixdir, :through => through, :always_on_top => false, :trigger => trig,
      :list => (list ? list.finish : [cmd(0, 0)]) }.each { |k, v| pg.instance_variable_set("@#{k}", v) }
    pg
  end

  def self.event(id, name, x, y, pages)
    e = RPG::Event.allocate
    { :id => id, :name => bin(name), :x => x, :y => y, :pages => pages }.each { |k, v| e.instance_variable_set("@#{k}", v) }
    e
  end

  # Aplica una definición {mapa => [ [nombre, [páginas]] ...]} a Data/MapNNN.rxdata.
  # Reemplaza los eventos cuyo nombre empiece por prefix; los demás no se tocan.
  def self.apply(map_id, prefix, tag, defs, dry = false)
    f = format('Data/Map%03d.rxdata', map_id); bak = f + '.bak_pre_' + tag
    File.binwrite(bak, File.binread(f)) if !File.exist?(bak) && !dry
    m = Marshal.load(File.binread(f))
    ev = m.instance_variable_get(:@events)
    ev.delete_if { |_, e| e.instance_variable_get(:@name).to_s.start_with?(prefix) }
    w = m.instance_variable_get(:@width); h = m.instance_variable_get(:@height)
    taken = {}; ev.each { |_, e| taken[[e.instance_variable_get(:@x), e.instance_variable_get(:@y)]] = true }
    nid = (ev.keys.max || 0) + 1; slot = 0; placed = []
    defs.each do |name, pages|
      slot += 1 while taken[[slot % w, slot / w]]
      x, y = slot % w, slot / w; raise "mapa #{map_id} sin hueco" if y >= h
      taken[[x, y]] = true; slot += 1
      ev[nid] = event(nid, name, x, y, pages); placed << [nid, name, x, y]; nid += 1
    end
    File.binwrite(f, Marshal.dump(m)) if !dry
    placed
  end
end
