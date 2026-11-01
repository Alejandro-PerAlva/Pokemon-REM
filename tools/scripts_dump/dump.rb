require 'zlib'
a=Marshal.load(File.binread('Data/Scripts.rxdata'))
a.each_with_index{|s,i| src=Zlib::Inflate.inflate(s[2]).force_encoding('UTF-8'); File.write("tools/scripts_dump/src/#{'%03d'%i}_#{s[1].gsub(/[^\w]/,'_')}.rb",src)}
puts a.size
