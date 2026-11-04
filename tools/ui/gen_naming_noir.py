# naming2bg.png (entrada de nombre por teclado) en Oniria Noir. Original en tools/ui/orig/naming/
from PIL import Image, ImageDraw
S=4; W,H=512,384
im=Image.new('RGBA',(W*S,H*S),(14,16,21,255)); d=ImageDraw.Draw(im)
GRID=(19,22,29,255); SIL=(214,219,228,255); PAN=(20,22,29,255); WELL=(15,17,23,255); WB=(38,43,56,255)
for x in range(0,W,16): d.rectangle([x*S,0,x*S+S-1,H*S],fill=GRID)
for y in range(0,H,16): d.rectangle([0,y*S,W*S,y*S+S-1],fill=GRID)
def card(x0,y0,x1,y1,fill=PAN,border=SIL,bw=1,cut=2):
    X0,Y0,X1,Y1=x0*S,y0*S,x1*S,y1*S; c=cut*S; b=bw*S
    for (a,bb,f) in ((0,c,border),(b,max(c-b,0),fill)):
        pts=[(X0+a+bb,Y0+a),(X1-a-bb,Y0+a),(X1-a,Y0+a+bb),(X1-a,Y1-a-bb),(X1-a-bb,Y1-a),(X0+a+bb,Y1-a),(X0+a,Y1-a-bb),(X0+a,Y0+a+bb)]
        d.polygon(pts,fill=f)
card(14,4,498,94)                 # cabecera: sujeto + texto
card(22,10,128,88,fill=WELL,border=WB)   # hueco del sujeto (icono / personaje)
card(14,290,498,380)              # ayuda
im=im.resize((W,H),Image.LANCZOS).convert('RGB'); im.save('Graphics/Pictures/naming2bg.png')
