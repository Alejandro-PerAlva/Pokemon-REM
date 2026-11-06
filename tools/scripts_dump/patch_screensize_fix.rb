# Uso: ruby tools/scripts_dump/patch_screensize_fix.rb   (desde la raíz; se ejecuta DESPUÉS de patch_screensize.rb)
# Corrección: al abrir Opciones podía salir marcado «Completa» aunque el tamaño por defecto es x2.
# La migración pasa a la versión 2 y fija x2 (índice 1) en todo guardado anterior; un valor fuera de 0-2 también vuelve a x2.
require 'zlib'
EDITS = {
  'PScreen_Options' => ['src/143_PScreen_Options.rb',
    ["    @screenver   = 1   # 1 = esquema de 3 tamaños (los guardados antiguos usaban 5)\n",
     "    @screenver   = 2   # 2 = esquema de 3 tamaños con x2 por defecto (versiones anteriores: 5 tamaños)\n"]],
  'PSystem_System' => ['src/169_PSystem_System.rb',
    ["    if $PokemonSystem.screenver!=1   # guardado antiguo: P,M,G,MG,Compl -> x1,x1,x2,x2,Completa\n" \
     "      $PokemonSystem.screensize=[0,0,1,1,2][$PokemonSystem.screensize.to_i] || 1\n" \
     "      $PokemonSystem.screenver=1\n    end\n",
     "    if $PokemonSystem.screenver!=2 || !($PokemonSystem.screensize.is_a?(Integer) && $PokemonSystem.screensize>=0 && $PokemonSystem.screensize<=2)\n" \
     "      $PokemonSystem.screensize=1   # x2 por defecto en todo guardado anterior al esquema de 3 tamaños\n" \
     "      $PokemonSystem.screenver=2\n    end\n"]],
}
def apply(text, pairs)
  t = text.dup
  pairs.each do |old, new|
    cand = [[old, new], [old.gsub("\n", "\r\n"), new.gsub("\n", "\r\n")]].find { |o, _| t.scan(o).length == 1 }
    raise "no encontrado exactamente 1 vez: #{old[0,70]}" if !cand
    t = t.sub(cand[0]) { cand[1] }
  end
  t
end
a = Marshal.load(File.binread('Data/Scripts.rxdata'))
EDITS.each do |name, (file, *pairs)|
  s = a.find { |x| x[1] == name } or raise "sección #{name}"
  s[2] = Zlib::Deflate.deflate(apply(Zlib::Inflate.inflate(s[2]).force_encoding('UTF-8'), pairs))
  path = "tools/scripts_dump/#{file}"
  File.binwrite(path, apply(File.binread(path).force_encoding('UTF-8'), pairs))
  puts "parcheado #{name}"
end
File.binwrite('Data/Scripts.rxdata', Marshal.dump(a))
puts 'OK'
