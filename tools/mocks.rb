module RPG
  class Base; def method_missing(*a); nil; end; end
  class Map<Base;end; class MapInfo<Base;end; class Event<Base; class Page<Base; class Condition<Base;end; class Graphic<Base;end;end;end
  class EventCommand<Base;end; class MoveRoute<Base;end; class MoveCommand<Base;end; class AudioFile<Base;end
  class Tileset<Base;end; class CommonEvent<Base;end; class System<Base; class Words<Base;end; class TestBattler<Base;end;end
end
class Table
  attr_accessor :dim,:xs,:ys,:zs,:data
  def self._load(s)
    t=allocate; d,x,y,z,n=s.unpack("l5"); t.dim=d; t.xs=x; t.ys=y; t.zs=z
    t.data=s[20..-1].unpack("s*"); t; end
  def _dump(level=0); [@dim,@xs,@ys,@zs,@data.size].pack("l5")+@data.pack("s*"); end
  def self.build(xs,ys,zs,data=nil)
    t=allocate; t.dim=(zs>1 ? 3 : (ys>1 ? 2 : 1)); t.xs=xs; t.ys=ys; t.zs=zs; t.data=data||Array.new(xs*ys*zs,0); t; end
  def [](x,y=0,z=0); @data[x+y*@xs+z*@xs*@ys]; end
  def []=(x,y,z,v); @data[x+y*@xs+z*@xs*@ys]=v; end
end
class Color; def self._load(s) s.unpack("d4") end; end
class Tone; def self._load(s) s.unpack("d4") end; end
def iv(o,n); o.instance_variable_get("@#{n}"); end
Dir.chdir(ENV["GAME_DIR"] || ".")
