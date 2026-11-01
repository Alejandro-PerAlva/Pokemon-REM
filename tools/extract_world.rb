# Usage: GAME_DIR=/path/to/Pokemon-REM OUT_DIR=/path/out ruby tools/extract_world.rb   (read-only on the project)
# Dumps tilesets, system (switch/var names), every MapNNN (tiles+events+commands) and CommonEvents to text.
module RPG
  class Base; def method_missing(*a); nil; end; end
  class Map<Base;end; class MapInfo<Base;end; class Event<Base; class Page<Base; class Condition<Base;end; class Graphic<Base;end;end;end
  class EventCommand<Base;end; class MoveRoute<Base;end; class MoveCommand<Base;end; class AudioFile<Base;end
  class Tileset<Base;end; class CommonEvent<Base;end; class System<Base; class Words<Base;end; class TestBattler<Base;end;end
end
class Table
  attr_reader :xs,:ys,:zs,:data
  def self._load(s)
    t=allocate; d,x,y,z,n=s.unpack("l5"); t.instance_variable_set(:@xs,x); t.instance_variable_set(:@ys,y); t.instance_variable_set(:@zs,z)
    t.instance_variable_set(:@data, s[20..-1].unpack("s*")); t; end
  def [](x,y=0,z=0); @data[x+y*@xs+z*@xs*@ys]; end
end
class Color; def self._load(s) s.unpack("d4") end; end
class Tone; def self._load(s) s.unpack("d4") end; end
def iv(o,n); o.instance_variable_get("@#{n}"); end
Dir.chdir(ENV["GAME_DIR"] || ".")
out=ENV["OUT_DIR"] || "world_dump"; Dir.mkdir(out) unless Dir.exist?(out)
ts=Marshal.load(File.binread("Data/Tilesets.rxdata"))
File.open("#{out}/tilesets.txt","w"){|f| ts.each_with_index{|t,i| next unless t
  f.puts "TS #{i} name=#{iv(t,:name)} gfx=#{iv(t,:tileset_name)} autotiles=#{iv(t,:autotile_names).inspect} fog=#{iv(t,:fog_name)} panorama=#{iv(t,:panorama_name)}"
  f.puts " passages n=#{iv(t,:passages).data.size} terrain n=#{iv(t,:terrain_tags).data.size}" }}
sysd=Marshal.load(File.binread("Data/System.rxdata"))
File.open("#{out}/system.txt","w"){|f|
 f.puts "start map=#{iv(sysd,:start_map_id)} x=#{iv(sysd,:start_x)} y=#{iv(sysd,:start_y)}"
 f.puts "switches=#{iv(sysd,:switches).each_with_index.map{|s,i| "#{i}:#{s}"}.join(' | ')}"
 f.puts "variables=#{iv(sysd,:variables).each_with_index.map{|s,i| "#{i}:#{s}"}.join(' | ')}"
 f.puts "title_bgm=#{iv(iv(sysd,:title_bgm),:name)} battle_bgm=#{iv(iv(sysd,:battle_bgm),:name)}"}
def cmd(c); "#{'  '*iv(c,:indent)}#{iv(c,:code)} #{iv(c,:parameters).inspect}"; end
def dump_list(f,list); (list||[]).each{|c| f.puts "      "+cmd(c)}; end
mi=Marshal.load(File.binread("Data/MapInfos.rxdata"))
mi.keys.sort.each{|id|
 m=Marshal.load(File.binread(format("Data/Map%03d.rxdata",id)))
 File.open(format("#{out}/map%03d.txt",id),"w"){|f|
  w,h=iv(m,:width),iv(m,:height)
  f.puts "MAP #{id} #{iv(mi[id],:name)} size=#{w}x#{h} tileset=#{iv(m,:tileset_id)} bgm=#{iv(iv(m,:bgm),:name)} bgs=#{iv(iv(m,:bgs),:name)} autoBGM=#{iv(m,:autoplay_bgm)} parent=#{iv(mi[id],:parent_id)}"
  d=iv(m,:data)
  f.puts "TILES"
  3.times{|z| f.puts "LAYER #{z}"; h.times{|y| f.puts (0...w).map{|x| d[x,y,z].to_s.rjust(4)}.join(" ")}}
  iv(m,:events).keys.sort.each{|eid| e=iv(m,:events)[eid]
   f.puts "EVENT #{eid} '#{iv(e,:name)}' (#{iv(e,:x)},#{iv(e,:y)})"
   iv(e,:pages).each_with_index{|p,pi| c=iv(p,:condition); g=iv(p,:graphic)
    f.puts "  PAGE #{pi} trig=#{iv(p,:trigger)} cond[sw1=#{iv(c,:switch1_valid)&&iv(c,:switch1_id)} sw2=#{iv(c,:switch2_valid)&&iv(c,:switch2_id)} var=#{iv(c,:variable_valid)&&"#{iv(c,:variable_id)}>=#{iv(c,:variable_value)}"} self=#{iv(c,:self_switch_valid)&&iv(c,:self_switch_ch)}] gfx=#{iv(g,:character_name)} dir=#{iv(g,:direction)} movetype=#{iv(p,:move_type)} thru=#{iv(p,:through)}"
    dump_list(f,iv(p,:list)) } }}
}
cev=Marshal.load(File.binread("Data/CommonEvents.rxdata"))
File.open("#{out}/common.txt","w"){|f| cev.each{|c| next unless c
 f.puts "CE #{iv(c,:id)} '#{iv(c,:name)}' trigger=#{iv(c,:trigger)} switch=#{iv(c,:switch_id)}"; dump_list(f,iv(c,:list))}}
puts "ok"
