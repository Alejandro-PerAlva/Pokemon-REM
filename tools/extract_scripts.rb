# usage: ruby extract_scripts.rb Data/Scripts.rxdata Scripts/
require 'zlib'
module RPG; class Script; end; end
src, out = ARGV
Dir.mkdir(out) unless Dir.exist?(out)
Marshal.load(File.binread(src)).each_with_index do |(id, name, code), i|
  File.write(format("%s/%03d_%s.rb", out, i, name.to_s.gsub(/[^\w\-]+/, '_')),
             Zlib::Inflate.inflate(code).force_encoding('UTF-8'))
end
