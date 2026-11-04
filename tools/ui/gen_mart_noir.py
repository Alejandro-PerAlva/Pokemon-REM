# Genera martScreen.png (tienda) en estilo Oniria Noir. Original en tools/ui/orig/mart/
from PIL import Image, ImageDraw
S=4
W,H=512,384
im=Image.new('RGBA',(W*S,H*S),(14,16,21,255))
d=ImageDraw.Draw(im)
GRID=(19,22,29,255); SIL=(214,219,228,255); PAN=(20,22,29,255); WELL=(15,17,23,255); WB=(38,43,56,255)
for x in range(0,W,16): d.rectangle([x*S,0,x*S+S-1,H*S],fill=GRID)
for y in range(0,H,16): d.rectangle([0,y*S,W*S,y*S+S-1],fill=GRID)
def card(x0,y0,x1,y1,fill=PAN,border=SIL,bw=1,cut=2):
    X0,Y0,X1,Y1=x0*S,y0*S,x1*S,y1*S; c=cut*S
    pts=[(X0+c,Y0),(X1-c,Y0),(X1,Y0+c),(X1,Y1-c),(X1-c,Y1),(X0+c,Y1),(X0,Y1-c),(X0,Y0+c)]
    d.polygon(pts,fill=border)
    b=bw*S; c2=max(c-b,0)
    pts=[(X0+b+c2,Y0+b),(X1-b-c2,Y0+b),(X1-b,Y0+b+c2),(X1-b,Y1-b-c2),(X1-b-c2,Y1-b),(X0+b+c2,Y1-b),(X0+b,Y1-b-c2),(X0+b,Y0+b+c2)]
    d.polygon(pts,fill=fill)
card(190,2,510,278)            # lista de artículos
card(2,2,186,98)               # dinero
card(0,284,512,384,cut=0)      # barra inferior de descripción
d.rectangle([0,284*S,W*S,284*S+S-1],fill=SIL)
card(6,302,70,366,fill=WELL,border=WB,cut=2)   # hueco del icono
im=im.resize((W,H),Image.LANCZOS).convert('RGB')
im.save('Graphics/Pictures/martScreen.png')
