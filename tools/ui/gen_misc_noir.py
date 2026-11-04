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

# --- almacén de objetos del PC (pcItembg) y fondo del Triple Triad ---
S=4; W,H=512,384
def base():
    im=Image.new('RGBA',(W*S,H*S),OBS); d=ImageDraw.Draw(im)
    for x in range(0,W,16): d.rectangle([x*S,0,x*S+S-1,H*S],fill=GRID)
    for y in range(0,H,16): d.rectangle([0,y*S,W*S,y*S+S-1],fill=GRID)
    return im,d
def card(d,x0,y0,x1,y1,fill=PAN,border=SIL,bw=1,cut=2):
    X0,Y0,X1,Y1=x0*S,y0*S,x1*S,y1*S; c=cut*S; b=bw*S
    for (a,bb,f) in ((0,c,border),(b,max(c-b,0),fill)):
        pts=[(X0+a+bb,Y0+a),(X1-a-bb,Y0+a),(X1-a,Y0+a+bb),(X1-a,Y1-a-bb),(X1-a-bb,Y1-a),(X0+a+bb,Y1-a),(X0+a,Y1-a-bb),(X0+a,Y0+a+bb)]
        d.polygon(pts,fill=f)
WELL=(15,17,23,255); WB=(38,43,56,255)
im,d=base()
card(d,94,10,436,274)             # lista
card(d,6,10,90,84)                # título del bolsillo
card(d,0,282,512,384,cut=0); d.rectangle([0,282*S,W*S,282*S+S-1],fill=SIL)
card(d,42,326,102,382,fill=WELL,border=WB)   # hueco del icono
im.resize((W,H),Image.LANCZOS).convert('RGB').save('Graphics/Pictures/pcItembg.PNG')
# triadbg: ver recolor por umbral en el historial (tablero 3x3 conservado del original)
