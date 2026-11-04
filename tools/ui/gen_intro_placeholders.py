# Uso: python3 tools/ui/gen_intro_placeholders.py   (desde la raíz del proyecto)
# Genera los PNG placeholder "Oniria Noir" de la pantalla de título y la intro. Sobrescribe: sustituye después por arte final con el MISMO nombre y tamaño.
import math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OBS=(20,22,29); OBS2=(27,30,40); GRID=(34,38,50); SILVER=(214,219,228); DIM=(120,128,146); GOLD=(170,176,196)
FONT_B="/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf"
FONT_R="/System/Library/Fonts/Supplemental/Arial Narrow.ttf"
def F(sz,b=False): return ImageFont.truetype(FONT_B if b else FONT_R,sz)
def ctext(d,xy,t,f,fill,anchor="mm"): d.text(xy,t,font=f,fill=fill,anchor=anchor)

def grid_bg(w,h,seed=7):
    im=Image.new("RGBA",(w,h),OBS+(255,)); d=ImageDraw.Draw(im)
    for x in range(0,w,32): d.line([(x,0),(x,h)],fill=GRID,width=1)
    for y in range(0,h,32): d.line([(0,y),(w,y)],fill=GRID,width=1)
    rnd=random.Random(seed); pts=[]
    for _ in range(26): pts.append((rnd.randrange(16,w-16),rnd.randrange(16,h-16)))
    for i in range(len(pts)-1):          # constelaciones tenues
        if math.dist(pts[i],pts[i+1])<150: d.line([pts[i],pts[i+1]],fill=(48,54,72),width=1)
    for p in pts: d.ellipse([p[0]-2,p[1]-2,p[0]+2,p[1]+2],fill=(150,158,178))
    return im

def frame(im,m=6,col=SILVER):
    d=ImageDraw.Draw(im); w,h=im.size
    d.rectangle([m,m,w-1-m,h-1-m],outline=col,width=1); d.rectangle([m+3,m+3,w-4-m,h-4-m],outline=(60,66,84),width=1)

def tag(im,name):
    d=ImageDraw.Draw(im); w,h=im.size
    ctext(d,(w-10,h-12),f"PLACEHOLDER  {name}  {w}x{h}",F(13),DIM,"rm")

# 1) Título: fondo + logo
bg=grid_bg(512,384); frame(bg); tag(bg,"Titles/intro_bg.png"); bg.save("Graphics/Titles/intro_bg.png")

logo=Image.new("RGBA",(408,230),(0,0,0,0)); d=ImageDraw.Draw(logo)
glow=Image.new("RGBA",(408,230),(0,0,0,0)); gd=ImageDraw.Draw(glow)
ctext(gd,(204,92),"POKÉMON REM",F(64,True),(214,219,228,150)); glow=glow.filter(ImageFilter.GaussianBlur(7)); logo.alpha_composite(glow)
d=ImageDraw.Draw(logo)
ctext(d,(204,92),"POKÉMON REM",F(64,True),SILVER+(255,))
d.line([(54,134),(354,134)],fill=GOLD+(255,),width=1); d.ellipse([200,130,208,138],outline=GOLD+(255,),width=1)
ctext(d,(204,172),"O N I R I A",F(34),SILVER+(255,))
ctext(d,(204,214),"PLACEHOLDER  Titles/intro_logo.png  408x230",F(12),DIM+(255,))
logo.save("Graphics/Titles/intro_logo.png")

# 2) Mapa de Oniria
m=grid_bg(512,384,seed=21); d=ImageDraw.Draw(m)
land=[(70,120),(150,60),(260,48),(360,70),(440,130),(455,230),(400,310),(300,340),(190,325),(105,270),(60,190)]
d.polygon(land,fill=(31,36,50),outline=(110,118,140)); d.line(land+[land[0]],fill=(110,118,140),width=2)
for i,(x,y) in enumerate([(150,150),(250,110),(350,160),(300,240),(190,240),(390,250),(230,300)]):
    d.ellipse([x-5,y-5,x+5,y+5],outline=SILVER,width=1); d.ellipse([x-1,y-1,x+1,y+1],fill=SILVER)
ctext(d,(256,200),"ONIRIA",F(54,True),(214,219,228)); frame(m); tag(m,"Pictures/intro_map_oniria.png"); m.save("Graphics/Pictures/intro_map_oniria.png")

# 3) Carta / dossier (320x240, alfa alrededor)
l=Image.new("RGBA",(320,240),(0,0,0,0)); d=ImageDraw.Draw(l)
d.rounded_rectangle([10,18,310,228],radius=8,fill=(0,0,0,90))           # sombra
d.rounded_rectangle([6,10,306,218],radius=8,fill=(34,38,50,255),outline=SILVER+(255,),width=2)
d.line([(6,10),(156,128),(306,10)],fill=(84,92,114,255),width=2)       # solapa
d.line([(6,218),(120,112)],fill=(60,66,84,255),width=1); d.line([(306,218),(192,112)],fill=(60,66,84,255),width=1)
d.ellipse([132,102,180,150],fill=(150,36,52,255),outline=(220,150,160,255),width=2)   # sello
ctext(d,(156,126),"REM",F(18,True),(240,220,224,255))
ctext(d,(156,176),"LABORATORIO POKÉMON DE ONIRIA",F(15,True),SILVER+(255,))
ctext(d,(156,196),"DOSSIER DE ADMISIÓN  ·  PLACEHOLDER  320x240",F(12),DIM+(255,))
l.save("Graphics/Pictures/intro_letter.png")

# 4) Fondo de selección
s=grid_bg(512,384,seed=33); d=ImageDraw.Draw(s)
d.rectangle([0,0,512,30],fill=OBS2); d.line([(0,30),(512,30)],fill=(70,78,98),width=1)
d.rectangle([0,356,512,384],fill=OBS2); d.line([(0,356),(512,356)],fill=(70,78,98),width=1)
frame(s,m=3); tag(s,"Pictures/intro_select_bg.png"); s.save("Graphics/Pictures/intro_select_bg.png")

# 5) Entrenadores (placeholder = sprites introBoy/introGirl ampliados x1.5 -> 120x240)
for src,dst in (("introBoy","intro_trainer_m"),("introGirl","intro_trainer_f")):
    im=Image.open(f"Graphics/Pictures/{src}.png").convert("RGBA").resize((120,240),Image.NEAREST)
    im.save(f"Graphics/Pictures/{dst}.png")
print("OK")
