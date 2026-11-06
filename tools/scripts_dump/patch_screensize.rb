# Uso: ruby tools/scripts_dump/patch_screensize.rb   (desde la raíz del proyecto)
# Opción «Tamaño de pantalla»: de 5 valores (P, M, G, MG, Compl) a 3: x1 (=M), x2 (=MG, por defecto) y Completa.
# Índices nuevos: 0=x1 (1.0), 1=x2 (2.0), 2=Completa. Parchea Data/Scripts.rxdata (secciones compiladas) y los volcados src/ + rem_ui.rb.
# Los guardados antiguos (índices 0-4) se migran una sola vez con PokemonSystem#screenver.
require 'zlib'
EDITS = {
  'Sprite_Resizer' => [['src/028_Sprite_Resizer.rb',
    ["  factor=[0.5,1.0,1.5,2.0,-1][factor] if !norecalc\n",
     "  factor=([1.0,2.0,-1][factor.to_i] || 2.0) if !norecalc   # 0=x1, 1=x2, 2=Completa\n"]]],
  'PScreen_Options' => [['src/143_PScreen_Options.rb',
    ["  attr_accessor :screensize\n", "  attr_accessor :screensize\n  attr_accessor :screenver\n"],
    ["    @screensize  = (DEFAULTSCREENZOOM.floor).to_i   # 0=half size, 1=full size, 2=double size\n",
     "    @screensize  = 1   # Tamaño de pantalla: 0=x1, 1=x2 (por defecto), 2=Completa\n    @screenver   = 1   # 1 = esquema de 3 tamaños (los guardados antiguos usaban 5)\n"],
    ['EnumOption.new(_INTL("Tamaño de ventana"),[_INTL("P"),_INTL("M"),_INTL("G"),_INTL("MG"),_INTL("Compl")],',
     'EnumOption.new(_INTL("Tamaño de ventana"),[_INTL("x1"),_INTL("x2"),_INTL("Completa")],']]],
  'PSystem_System' => [['src/169_PSystem_System.rb',
    ["    pbSetResizeFactor($PokemonSystem.screensize)\n",
     "    if $PokemonSystem.screenver!=1   # guardado antiguo: P,M,G,MG,Compl -> x1,x1,x2,x2,Completa\n" \
     "      $PokemonSystem.screensize=[0,0,1,1,2][$PokemonSystem.screensize.to_i] || 1\n" \
     "      $PokemonSystem.screenver=1\n    end\n" \
     "    pbSetResizeFactor($PokemonSystem.screensize)\n"],
    ["    pbSetResizeFactor(1.0)\n", "    pbSetResizeFactor(1.0,true)\n"]]],
  'Fancy Badges' => [['src/189_Fancy_Badges.rb',
    ['fp["eff"].visible = $PokemonSystem.screensize < 2', 'fp["eff"].visible = $PokemonSystem.screensize < 1']]],
  'REM_UI' => [['rem_ui.rb',
    ['EnumOption.new(_INTL("Tamaño de pantalla"),[_INTL("P"),_INTL("M"),_INTL("G"),_INTL("MG"),_INTL("Compl")],',
     'EnumOption.new(_INTL("Tamaño de pantalla"),[_INTL("x1"),_INTL("x2"),_INTL("Completa")],'],
    ['_INTL("Tamaño de la ventana del juego.")', '_INTL("Tamaño de la ventana: x1, x2 (por defecto) o pantalla completa.")']]],
}
def apply(text, pairs)
  t = text.dup
  pairs.each do |old, new|
    # Respeta los finales de línea del original (los volcados mezclan LF y CRLF).
    cand = [[old, new], [old.gsub("\n", "\r\n"), new.gsub("\n", "\r\n")]].find { |o, _| t.scan(o).length == 1 }
    raise "no encontrado exactamente 1 vez: #{old[0,70]}" if !cand
    t = t.sub(cand[0]) { cand[1] }
  end
  t
end
a = Marshal.load(File.binread('Data/Scripts.rxdata'))
EDITS.each do |name, groups|
  file, *pairs = groups[0]
  s = a.find { |x| x[1] == name } or raise "sección #{name}"
  src = Zlib::Inflate.inflate(s[2]).force_encoding('UTF-8')
  new = apply(src, pairs)
  s[2] = Zlib::Deflate.deflate(new)
  path = "tools/scripts_dump/#{file}"
  File.binwrite(path, apply(File.binread(path).force_encoding('UTF-8'), pairs))
  puts "parcheado #{name} (#{pairs.length} cambios)"
end
File.binwrite('Data/Scripts.rxdata', Marshal.dump(a))
puts 'OK'
