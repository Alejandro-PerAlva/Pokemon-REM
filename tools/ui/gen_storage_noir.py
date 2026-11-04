# PC (almacenamiento) en Oniria Noir: mapeo de luminancia (oscuro->plata, claro->obsidiana).
# Originales en tools/ui/orig/storage/. Banner de cada caja: arte atenuado; rejilla: pozo recesado.
from PIL import Image
import colorsys, sys
SIL=(214,219,228); PAN=(20,22,29); WELL=(15,17,23); GRIDC=(38,43,56)
def lerp(a,b,t): return tuple(int(a[i]+(b[i]-a[i])*t+.5) for i in range(3))
def inv(px):
    r,g,b,a=px
    L=(0.299*r+0.587*g+0.114*b)/255
    t=min(max((L-0.18)/(0.88-0.18),0),1)
    return lerp(SIL,PAN,t)+(a,)
def invimg(im):
    im=im.convert('RGBA'); o=im.copy(); px=im.load(); op=o.load()
    for y in range(im.height):
        for x in range(im.width):
            op[x,y]=inv(px[x,y]) if px[x,y][3] else px[x,y]
    return o
def boxtheme(im):
    im=im.convert('RGBA'); o=im.copy(); px=im.load(); op=o.load()
    W,H=im.size
    for y in range(H):
        for x in range(W):
            p=px[x,y]
            if p[3]==0: continue
            arrow=(x<42 or x>=W-42) and y<46
            if y<48:
                if arrow: op[x,y]=inv(p)
                else:   # arte del banner atenuado
                    L=(0.299*p[0]+0.587*p[1]+0.114*p[2])/255
                    if L<0.25: op[x,y]=SIL+(255,)       # contorno
                    else: op[x,y]=lerp((10,12,16),(60,68,84),L)+(255,)
            else:
                L=(0.299*p[0]+0.587*p[1]+0.114*p[2])/255
                if L<0.30: op[x,y]=SIL+(255,)          # marco
                else:
                    # rejilla: variación leve sobre el pozo
                    v=int((L-0.45)*40)
                    op[x,y]=(max(WELL[0]+v//2,10),max(WELL[1]+v//2,12),max(WELL[2]+v//2,16),255)
    return o
src='tools/ui/orig/storage/'
invimg(Image.open(src+'boxsides.png')).save('Graphics/Pictures/boxsides.png')
invimg(Image.open(src+'boxpartytab.png')).save('Graphics/Pictures/boxpartytab.png')
for i in range(24):
    boxtheme(Image.open(src+'box%d.png'%i)).save('Graphics/Pictures/box%d.png'%i)
