# Usage: GAME_DIR=<repo> OUT_DIR=<dir> ruby tools/render_ascii.rb [map ids...]   (default: all maps in MapInfos)
# Writes <OUT_DIR>/asciiNNN.txt: passability/terrain ASCII + event markers, using each map's own tileset.
# Legend: # blocked  . walkable  + partly walkable  g grass(tag2/10)  ~ water  L ledge  w waterfall  s sand  r rock
#         W warp  N npc  T trainer  I item ball  S sign/other action event  E other event
load File.join(File.dirname(File.expand_path(__FILE__)), "mocks.rb")
OUT = ENV["OUT_DIR"] || "world_dump"; Dir.mkdir(OUT) unless Dir.exist?(OUT)
ts = Marshal.load(File.binread("Data/Tilesets.rxdata"))
mi = Marshal.load(File.binread("Data/MapInfos.rxdata"))
def pass(m, t, x, y, bit)
  d = iv(m, :data); pa = iv(t, :passages).data; pr = iv(t, :priorities).data
  [2, 1, 0].each { |z| id = d[x, y, z]; next if id == 0
    p = pa[id] || 0
    next if p & 0x10 != 0
    return false if p & bit != 0
    return false if p & 0x0f == 0x0f
    return true if (pr[id] || 0) == 0 }
  true
end
def tag(m, t, x, y)
  d = iv(m, :data); tg = iv(t, :terrain_tags).data
  [2, 1, 0].each { |z| id = d[x, y, z]; next if id == 0; v = tg[id] || 0; return v if v > 0 }
  0
end
def glyph_for(e)
  cmds = iv(iv(e, :pages)[0], :list).map { |c| [iv(c, :code), iv(c, :parameters)] }
  gfx = iv(iv(iv(e, :pages)[0], :graphic), :character_name).to_s
  nm = iv(e, :name).to_s
  return 'W' if cmds.any? { |c, p| c == 355 && p[0].to_s =~ /pbTransfer|Transfer/ } || cmds.any? { |c, _| c == 201 }
  return 'T' if nm =~ /^Trainer/
  return 'I' if nm == "Item" || gfx == "Object ball"
  return 'N' if gfx != ""
  return 'S' if cmds.any? { |c, _| c == 101 || c == 355 }
  'E'
end
ids = ARGV.empty? ? mi.keys.sort : ARGV.map(&:to_i)
ids.each { |id|
  m = Marshal.load(File.binread(format("Data/Map%03d.rxdata", id))); t = ts[iv(m, :tileset_id)]
  w, h = iv(m, :width), iv(m, :height)
  grid = Array.new(h) { Array.new(w, '.') }; tags = Hash.new(0)
  h.times { |y| w.times { |x|
    dirs = [0x01, 0x02, 0x04, 0x08].map { |b| pass(m, t, x, y, b) }
    tg = tag(m, t, x, y); tags[tg] += 1
    c = dirs.any? ? '.' : '#'
    c = '+' if dirs.any? && !dirs.all?
    c = 'g' if [2, 10].include?(tg) && dirs.any?
    c = '~' if [5, 6, 7].include?(tg)
    c = 'w' if tg == 8 || tg == 9
    c = 'L' if tg == 1
    c = 's' if tg == 3; c = 'r' if tg == 4
    grid[y][x] = c } }
  evs = iv(m, :events)
  evs.each { |_, e| x, y = iv(e, :x), iv(e, :y); grid[y][x] = glyph_for(e) if x < w && y < h }
  File.open("#{OUT}/ascii%03d.txt" % id, "w") { |f|
    f.puts "MAP #{id} #{iv(mi[id], :name)} #{w}x#{h} tileset #{iv(m, :tileset_id)} (#{iv(t, :name)})"
    f.puts "tags: " + tags.sort.map { |k, v| "#{k}=#{v}" }.join(" ")
    f.print "    "; w.times { |x| f.print(x % 10 == 0 ? (x / 10).to_s : ' ') }; f.puts
    h.times { |y| f.puts "%3d %s" % [y, grid[y].join] } }
}
puts "rendered #{ids.size} map(s) to #{OUT}"
