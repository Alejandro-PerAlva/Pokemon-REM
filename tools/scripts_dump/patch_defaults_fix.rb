# Uso: ruby tools/scripts_dump/patch_defaults_fix.rb   (desde la raíz; DESPUÉS de patch_screensize_fix.rb)
# Valores por defecto de Opciones: velocidad de texto = Rápida (2), estilo de combate = Fijo (1), tamaño = x2.
# La migración v2 (guardados anteriores) también los aplica una sola vez.
require 'zlib'
EDITS = {
  'PScreen_Options' => ['src/143_PScreen_Options.rb',
    ["    @textspeed   = 1   # Text speed (0=slow, 1=normal, 2=fast)\n", "    @textspeed   = 2   # Velocidad de texto: 0=lenta, 1=normal, 2=rápida (por defecto)\n"],
    ["    @battlestyle = 0   # Battle style (0=switch, 1=set)\n", "    @battlestyle = 1   # Estilo de combate: 0=cambio, 1=fijo (por defecto)\n"]],
  'PSystem_System' => ['src/169_PSystem_System.rb',
    ["      $PokemonSystem.screenver=2\n",
     "      $PokemonSystem.textspeed=2     # Rápida\n      $PokemonSystem.battlestyle=1   # Fijo\n      $PokemonSystem.screenver=2\n"]],
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
