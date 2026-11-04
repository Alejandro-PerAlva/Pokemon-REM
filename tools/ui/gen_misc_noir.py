# Fondos de Salón de la Fama e intercambio en Oniria Noir (originales en tools/ui/orig/misc/)
from PIL import Image, ImageDraw
OBS=(14,16,21,255); GRID=(19,22,29,255); PAN=(20,22,29,255); SIL=(214,219,228,255)
# hallfamebg: mosaico 8x24
t=Image.new('RGBA',(8,24),OBS)
for y in range(0,24,8):
    for x in range(8): t.putpixel((x,y),GRID)
for y in range(24): t.putpixel((0,y),GRID)
t.save('Graphics/Pictures/hallfamebg.png')
# tradebg: mosaico 16x320
t=Image.new('RGBA',(16,320),OBS)
for y in range(0,320,16):
    for x in range(16): t.putpixel((x,y),GRID)
for y in range(320): t.putpixel((0,y),GRID)
t.save('Graphics/Pictures/tradebg.png')
# barras superior (0-31) e inferior (288-383), centro transparente
b=Image.new('RGBA',(512,384),(0,0,0,0)); d=ImageDraw.Draw(b)
d.rectangle([0,0,511,31],fill=PAN); d.rectangle([0,31,511,31],fill=SIL)
d.rectangle([0,288,511,383],fill=PAN); d.rectangle([0,288,511,288],fill=SIL)
b.save('Graphics/Pictures/hallfamebars.png')
