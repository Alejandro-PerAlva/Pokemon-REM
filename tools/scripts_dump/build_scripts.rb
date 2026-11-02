# Uso: ruby tools/scripts_dump/build_scripts.rb   (desde la raíz del proyecto)
# Reconstruye Data/Scripts.rxdata desde el backup original + secciones parcheadas en src/ + REM_Rebalance.
require 'zlib'
bak=Dir['tools/scripts_dump/Scripts.rxdata.bak_*'].sort.first
# Sin backup original (está en .gitignore): se parte de Data/Scripts.rxdata y se quitan las secciones REM_* para reinsertarlas.
a=Marshal.load(File.binread(bak || 'Data/Scripts.rxdata'))
a.reject!{|s| %w(REM_Rebalance REM_Mechanics REM_Events REM_UI).include?(s[1])} if !bak
a.each_with_index do |s,i|
  f=Dir["tools/scripts_dump/src/#{'%03d'%i}_*.rb"].first
  next if !f
  src=File.binread(f)
  orig=Zlib::Inflate.inflate(s[2])
  next if src==orig
  s[2]=Zlib::Deflate.deflate(src)
  puts "patched #{i} #{s[1]}"
end
main=a.index{|s| s[1]=='Main'}
new_id=a.map{|s| s[0]}.max+1
%w(REM_Rebalance REM_Mechanics REM_Events REM_UI).each_with_index do |n,k|
  a.insert(main+k,[new_id+k,n,Zlib::Deflate.deflate(File.binread("tools/scripts_dump/#{n.downcase}.rb"))])
end
File.binwrite('Data/Scripts.rxdata',Marshal.dump(a))
puts "OK #{a.size} secciones"
