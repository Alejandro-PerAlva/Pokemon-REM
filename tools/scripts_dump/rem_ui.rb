#===============================================================================
# REM_UI — interfaz: Diario de misiones (menú de pausa) y reloj día/noche.
# Se carga tras REM_Mechanics. Llamada desde evento: pbRemQuestLog
#===============================================================================
module REM_UI
  def self.timeInfo
    t=pbGetTimeNow
    phase=PBDayNight.isNight? ? _INTL("Noche") : _INTL("Día")
    lock=($PokemonGlobal && $PokemonGlobal.remTimeFrozen) ? _INTL(" (reloj fijo)") : ""
    return _INTL("{1} {2}:{3}{4}",phase,t.hour,sprintf("%02d",t.min),lock)
  end

  def self.piaLabel(i)
    sym=REM_PIA_STARTERS[i][0]
    name=PBSpecies.getName(getConst(PBSpecies,sym))
    pr=pbPiaProg(sym); g=pbPiaGoals(sym)
    done=(0...4).select{|k| pr[k]>=g[k]}.length
    case pbPiaState(sym)
    when :first   then return _INTL("✔ {1} (tu inicial)",name)
    when :claimed then return _INTL("✔ {1} (reclamado)",name)
    when :ready   then return _INTL("★ {1} (¡listo!)",name)
    when :active  then return _INTL("► {1} {2}/4 (activo)",name,done)
    end
    return _INTL("   {1} {2}/4",name,done)
  end

  def self.piaDetail(sym)
    q=REM_Quests.build(pbPiaIndex(sym))
    return q[:objectives].map{|o| sprintf("%s: %d/%d",o[:text],o[:cur],o[:goal])}.join("\n")
  end
end

def pbPiaQuestPanel
  pbPiaFirst
  last=0
  loop do
    names=[]
    for i in 0...REM_PIA_STARTERS.length; names.push(REM_UI.piaLabel(i)); end
    names.push(_INTL("Cerrar  ({1})",REM_UI.timeInfo))
    cmd=Kernel.pbShowCommands(nil,names,-1,last)
    last=cmd
    return if cmd<0 || cmd>=REM_PIA_STARTERS.length
    sym=REM_PIA_STARTERS[cmd][0]
    st=pbPiaState(sym)
    opts=[_INTL("Ver misiones")]
    opts.push(_INTL("Activar / Seleccionar")) if st==:idle
    opts.push(_INTL("Dejar de rastrear")) if st==:active
    opts.push(_INTL("Reclamar inicial")) if st==:ready
    opts.push(_INTL("Volver"))
    c=Kernel.pbShowCommands(nil,opts,-1)
    next if c<0
    case opts[c]
    when _INTL("Ver misiones")       then Kernel.pbMessage(REM_UI.piaDetail(sym))
    when _INTL("Activar / Seleccionar") then pbPiaSelect(sym)
    when _INTL("Dejar de rastrear")  then pbPiaSelect(nil)
    when _INTL("Reclamar inicial")   then pbClaimPiaStarter(sym)
    end
  end
end
def pbRemQuestLog; pbPiaQuestPanel; end

#===============================================================================
# POKÉDEX: ficha de datos (tecla C en la entrada) — stats base, tipos, habilidades,
# evolución exacta y zonas de captura (Data/encounters.dat, compilado de encounters.txt)
#===============================================================================
module REM_UI
  STATNAMES=["PS","Ataque","Defensa","Velocidad","At. Esp.","Def. Esp."]
  STATCOLORS=[Color.new(248,88,88),Color.new(248,168,64),Color.new(248,224,80),
              Color.new(248,136,200),Color.new(120,200,248),Color.new(120,224,120)]

  def self.evoMethod(e)
    t=e[0]; l=e[1]
    name=PBSpecies.getName(e[2])
    item=(l.is_a?(Integer) && l>0 && l<=PBItems.maxValue) ? PBItems.getName(l) : "?"
    how=case t
      when PBEvolution::Happiness,PBEvolution::HappinessDay,PBEvolution::HappinessNight then _INTL("con alta felicidad")
      when PBEvolution::Level,PBEvolution::LevelMale,PBEvolution::LevelFemale,PBEvolution::LevelDay,
           PBEvolution::LevelNight,PBEvolution::LevelRain,PBEvolution::LevelDarkInParty then _INTL("a nivel {1}",l)
      when PBEvolution::Trade then _INTL("por intercambio")
      when PBEvolution::TradeItem then _INTL("intercambio con {1}",item)
      when PBEvolution::Item,PBEvolution::ItemMale,PBEvolution::ItemFemale then _INTL("con {1}",item)
      when PBEvolution::DayHoldItem,PBEvolution::NightHoldItem then _INTL("subiendo nivel con {1}",item)
      else _INTL("(condición especial)")
    end
    return _INTL("{1}: {2}",name,how)
  end

  def self.zones(species)
    names=[]
    data=load_data("Data/encounters.dat") rescue {}
    for map in data.keys.sort
      if pbFindEncounter(data[map][1],species)
        n=pbGetMapNameFromId(map)
        names.push(n) if !names.include?(n)
      end
    end
    return names
  end

  def self.draw(species)
    pk=PokeBattle_Pokemon.new(species,5)
    bmp=Bitmap.new(Graphics.width,Graphics.height)
    bmp.fill_rect(0,0,Graphics.width,Graphics.height,Color.new(24,28,44))
    bmp.fill_rect(4,4,Graphics.width-8,Graphics.height-8,Color.new(40,48,72))
    pbSetSystemFont(bmp)
    base=Color.new(248,248,248); shadow=Color.new(64,64,80)
    tp=[[_INTL("#{sprintf('%03d',species)}  {1}",PBSpecies.getName(species)),16,10,0,base,shadow]]
    types=[pk.type1,pk.type2].uniq.map{|t| PBTypes.getName(t)}
    tp.push([_INTL("Tipo: {1}",types.join(" / ")),16,40,0,base,shadow])
    st=pk.baseStats; bst=st.inject(0){|a,b| a+b}
    for i in 0...6
      y=76+i*22
      tp.push([STATNAMES[i],16,y,0,base,shadow])
      tp.push([st[i].to_s,150,y,1,base,shadow])
      bmp.fill_rect(160,y+6,[st[i]*150/200,150].min,8,STATCOLORS[i])
    end
    tp.push([_INTL("Total: {1}",bst),16,208,0,Color.new(248,224,80),shadow])
    ab=pk.getAbilityList
    normal=ab.select{|a| a[1]<2}.map{|a| PBAbilities.getName(a[0])}.uniq
    hidden=ab.select{|a| a[1]>=2}.map{|a| PBAbilities.getName(a[0])}.uniq
    tp.push([_INTL("Habilidades: {1}",normal.join(", ")),16,236,0,base,shadow])
    tp.push([_INTL("Oculta: {1}",hidden.length>0 ? hidden.join(", ") : "—"),16,262,0,base,shadow])
    evos=pbGetEvolvedFormData(species).select{|e| e[2]<=PBSpecies.maxValue}
    prev=pbGetPreviousForm(species)
    evotxt=evos.map{|e| evoMethod(e)}
    evotxt=[prev!=species ? _INTL("Evoluciona de {1}",PBSpecies.getName(prev)) : _INTL("No evoluciona")] if evotxt.length==0
    tp.push([_INTL("Evolución: {1}",evotxt.join("; ")),16,288,0,base,shadow])
    z=zones(species)
    zt=z.length==0 ? _INTL("sin zona salvaje") : (z[0,4].join(", ")+(z.length>4 ? _INTL(" y {1} más",z.length-4) : ""))
    tp.push([_INTL("Zonas: {1}",zt),16,314,0,base,shadow])
    tp.push([_INTL("B: volver"),16,352,0,Color.new(200,200,216),shadow])
    pbDrawTextPositions(bmp,tp)
    return bmp
  end
end

def pbRemDexData(species)
  vp=Viewport.new(0,0,Graphics.width,Graphics.height); vp.z=99999
  sp=Sprite.new(vp); sp.bitmap=REM_UI.draw(species)
  loop do
    Graphics.update; Input.update
    break if Input.trigger?(Input::B) || Input.trigger?(Input::C)
  end
  sp.bitmap.dispose; sp.dispose; vp.dispose
end

#===============================================================================
# COMBATE "Oniria Noir": franja lateral de tipo en las cajas de datos, paleta de texto
# clara sobre obsidiana y tarjeta compacta de info del movimiento (tecla D / Z).
# Los PNG (Graphics/Pictures/battle*.png) los genera tools/ui/gen_oniria_noir.py; la ranura de
# 5 px de las cajas (filas STRIPE_Y0..STRIPE_Y1, pegada al borde oblicuo) se rellena aquí.
#===============================================================================
module PokeBattle_SceneConstants
  [[:BOXTEXTBASECOLOR,Color.new(255,255,255)],[:BOXTEXTSHADOWCOLOR,Color.new(13,14,18)],
   [:MESSAGEBASECOLOR,Color.new(240,243,248)],[:MESSAGESHADOWCOLOR,Color.new(13,14,18)],
   [:MENUBASECOLOR,Color.new(240,243,248)],[:MENUSHADOWCOLOR,Color.new(13,14,18)],
   [:PPTEXTBASECOLOR,Color.new(240,243,248)],[:PPTEXTSHADOWCOLOR,Color.new(13,14,18)]].each{|n,c|
    remove_const(n) if const_defined?(n)
    const_set(n,c)
  }
end

module PokeBattle_SceneConstants
  remove_const(:EXPGAUGESIZE) if const_defined?(:EXPGAUGESIZE)
  EXPGAUGESIZE=204   # la barra de EXP llega hasta el borde derecho visible de la pantalla
end

module REM_UI
  STRIPE_W=5; STRIPE_Y0=9; STRIPE_Y1=47
  TYPE_RGB=[[168,167,122],[194,46,40],[169,143,243],[163,62,161],[226,191,101],[182,161,54],
            [166,185,26],[115,87,151],[183,183,206],[104,160,144],[238,129,48],[99,144,240],
            [122,199,76],[247,208,44],[249,85,135],[150,217,214],[111,53,252],[112,87,70],[214,133,173]]
  INK=Color.new(13,14,18)
  SILVER=Color.new(214,219,228)

  def self.typeColor(t)
    c=TYPE_RGB[t] || TYPE_RGB[0]
    return Color.new(c[0],c[1],c[2])
  end

  # Borde oblicuo de cada fila (x del primer píxel opaco desde el lado del borde), calculado una vez por caja.
  def self.edges(src,foe)
    e=[]
    for y in 0...src.height
      if foe
        x=src.width-1
        x-=1 while x>=0 && src.get_pixel(x,y).alpha==0
      else
        x=0
        x+=1 while x<src.width && src.get_pixel(x,y).alpha==0
      end
      e.push(x)
    end
    return e
  end

  def self.drawTypeStripe(bmp,edges,foe,types)
    types=types.select{|t| t && t>=0}.uniq
    return if types.length==0
    mid=(STRIPE_Y0+STRIPE_Y1)/2
    for y in STRIPE_Y0..STRIPE_Y1
      x=foe ? edges[y]-STRIPE_W : edges[y]+1
      if types.length==1
        c=typeColor(types[0])
      elsif y<mid
        c=typeColor(types[0])
      elsif y==mid
        c=INK
      else
        c=typeColor(types[1])
      end
      bmp.fill_rect(x,y,STRIPE_W,1,c)
      if c!=INK
        hx=foe ? x+STRIPE_W-1 : x
        bmp.fill_rect(hx,y,1,1,Color.new((c.red+255)/2,(c.green+255)/2,(c.blue+255)/2))
      end
    end
  end

  # Ajusta el texto a un ancho dado (palabras) usando la fuente actual del bitmap.
  def self.wrap(bmp,text,width)
    lines=[]
    text.to_s.split("\n").each{|para|
      cur=""
      para.split(" ").each{|w|
        t=(cur=="") ? w : cur+" "+w
        if cur!="" && bmp.text_size(t).width>width
          lines.push(cur); cur=w
        else
          cur=t
        end
      }
      lines.push(cur) if cur!=""
    }
    return lines
  end
end

class PokemonDataBox
  # Reemplaza refresh: caja fina estilo Gen 5, tipografía única (fuente pequeña), franja lateral de tipo.
  def refresh
    self.bitmap.clear
    return if !@battler.pokemon
    self.bitmap.blt(0,0,@databox.bitmap,Rect.new(0,0,@databox.width,@databox.height))
    foe=((@battler.index&1)==1)
    base=PokeBattle_SceneConstants::BOXTEXTBASECOLOR
    shadow=PokeBattle_SceneConstants::BOXTEXTSHADOWCOLOR
    bx=@spritebaseX
    pbSetNarrowFont(self.bitmap)
    name=@battler.name
    self.bitmap.font.size=27
    self.bitmap.font.size-=1 while self.bitmap.font.size>19 && self.bitmap.text_size(name).width>108
    namesize=self.bitmap.font.size
    namew=self.bitmap.text_size(name).width
    textpos=[[name,bx+10,8,false,base,shadow]]
    case @battler.displayGender
    when 0 then textpos.push([_INTL("♂"),bx+14+namew,8,false,Color.new(110,170,255),shadow])
    when 1 then textpos.push([_INTL("♀"),bx+14+namew,8,false,Color.new(255,120,160),shadow])
    end
    pbDrawTextPositions(self.bitmap,textpos)
    pbSetNarrowFont(self.bitmap)
    self.bitmap.font.size=namesize   # nivel con el mismo tamaño y línea base que el nombre
    pbDrawTextPositions(self.bitmap,[[_INTL("Nv{1}",@battler.level),bx+196,8,true,base,shadow]])
    if @showhp
      pbSetNarrowFont(self.bitmap)
      self.bitmap.font.size=24
      pbDrawTextPositions(self.bitmap,[[_ISPRINTF("{1: 2d}/{2: 2d}",self.hp,@battler.totalhp),bx+196,49,true,base,shadow]])
    end
    imagepos=[]
    if @battler.isShiny?
      imagepos.push(["Graphics/Pictures/shiny.png",bx+(foe ? 200 : -6),(foe ? 22 : 36),0,0,-1,-1])
    end
    if @battler.isMega?
      imagepos.push(["Graphics/Pictures/battleMegaEvoBox.png",bx+8,30,0,0,-1,-1])
    elsif @battler.isPrimal?
      if isConst?(@battler.pokemon.species,PBSpecies,:KYOGRE)
        imagepos.push(["Graphics/Pictures/battlePrimalKyogreBox.png",bx+140,4,0,0,-1,-1])
      elsif isConst?(@battler.pokemon.species,PBSpecies,:GROUDON)
        imagepos.push(["Graphics/Pictures/battlePrimalGroudonBox.png",bx+140,4,0,0,-1,-1])
      end
    end
    if @battler.owned && foe
      imagepos.push(["Graphics/Pictures/battleBoxOwned.png",bx+10,35,0,0,-1,-1])
    end
    pbDrawImagePositions(self.bitmap,imagepos)
    if @battler.status>0
      self.bitmap.blt(bx+24,30,@statuses.bitmap,Rect.new(0,(@battler.status-1)*16,44,16))
    end
    hpGaugeSize=PokeBattle_SceneConstants::HPGAUGESIZE
    hpgauge=@battler.totalhp==0 ? 0 : (self.hp*hpGaugeSize/@battler.totalhp)
    hpgauge=2 if hpgauge==0 && self.hp>0
    hpzone=0
    hpzone=1 if self.hp<=(@battler.totalhp/2).floor
    hpzone=2 if self.hp<=(@battler.totalhp/4).floor
    hpcolors=[PokeBattle_SceneConstants::HPCOLORGREENDARK,PokeBattle_SceneConstants::HPCOLORGREEN,
       PokeBattle_SceneConstants::HPCOLORYELLOWDARK,PokeBattle_SceneConstants::HPCOLORYELLOW,
       PokeBattle_SceneConstants::HPCOLORREDDARK,PokeBattle_SceneConstants::HPCOLORRED]
    hpGaugeX=PokeBattle_SceneConstants::HPGAUGE_X
    hpGaugeY=PokeBattle_SceneConstants::HPGAUGE_Y
    if @animatingHP && self.hp>0
      self.bitmap.fill_rect(bx+hpGaugeX,hpGaugeY,@starthp*hpGaugeSize/@battler.totalhp,6,Color.new(60,60,70))
    end
    self.bitmap.fill_rect(bx+hpGaugeX,hpGaugeY,hpgauge,2,hpcolors[hpzone*2])
    self.bitmap.fill_rect(bx+hpGaugeX,hpGaugeY+2,hpgauge,4,hpcolors[hpzone*2+1])
    if @showexp
      expGaugeX=PokeBattle_SceneConstants::EXPGAUGE_X
      expGaugeY=74   # barra exterior acoplada bajo la caja (pista dibujada en el PNG)
      self.bitmap.fill_rect(bx+expGaugeX,expGaugeY,self.exp,2,PokeBattle_SceneConstants::EXPCOLORSHADOW)
      self.bitmap.fill_rect(bx+expGaugeX,expGaugeY+2,self.exp,2,PokeBattle_SceneConstants::EXPCOLORBASE)
    end
    @remEdges=REM_UI.edges(@databox.bitmap,foe) if !@remEdges
    REM_UI.drawTypeStripe(self.bitmap,@remEdges,foe,[@battler.type1,@battler.type2])
  end
end

# Botones de comando: texto dibujado con la misma fuente estrecha que los ataques (Luchar, Mochila...).
class CommandMenuButtons
  REM_LABELS=["Luchar","Pokémon","Mochila","Huir","Llamar","Ball","Roca","Cebo","Ball"]
  def refresh(index,mode=0)
    self.bitmap.clear
    @mode=mode
    cmdarray=[0,2,1,3]
    case @mode
    when 1 then cmdarray=[0,2,1,4]
    when 2 then cmdarray=[5,7,6,3]
    when 3 then cmdarray=[0,8,1,3]
    end
    pbSetNarrowFont(self.bitmap)
    textpos=[]
    [false,true].each{|sel|
      for i in 0...4
        next if (i==index)!=sel
        x=((i%2)==0) ? 0 : 130
        y=((i/2)==0) ? 4 : 50
        self.bitmap.blt(x,y,@buttonbitmap.bitmap,Rect.new(sel ? 130 : 0,cmdarray[i]*46,130,46))
        textpos.push([_INTL(REM_LABELS[cmdarray[i]]),x+65,y+10,2,
           PokeBattle_SceneConstants::MENUBASECOLOR,PokeBattle_SceneConstants::MENUSHADOWCOLOR])
      end
    }
    pbDrawTextPositions(self.bitmap,textpos)
  end
end

class FightMenuButtons
  alias rem_orig_refresh refresh
  def refresh(index,moves,megaButton,ultraButton)
    rem_orig_refresh(index,moves,megaButton,ultraButton)
    return if !moves
    pbSetNarrowFont(self.bitmap)
    self.bitmap.font.size=22
    pbDrawTextPositions(self.bitmap,[[_INTL("Tecla D: info"),448,UPPERGAP+64,2,
       REM_UI::SILVER,REM_UI::INK]])
    pbSetNarrowFont(self.bitmap)
  end
end

class PokeBattle_Scene
  # Ficha de ataque: 3 celdas (icono de categoría, potencia, precisión) y descripción debajo.
  # Anclada abajo a la izquierda, justo sobre el panel de botones de ataque.
  def pbRemMoveInfo(move)
    vp=Viewport.new(0,0,Graphics.width,Graphics.height); vp.z=99999
    sp=BitmapSprite.new(240,152,vp)
    sp.x=8; sp.y=Graphics.height-96-152-4
    bmp=sp.bitmap
    card=AnimatedBitmap.new("Graphics/Pictures/battleMoveInfo")
    bmp.blt(0,0,card.bitmap,Rect.new(0,0,240,152))
    card.dispose
    cat=move.pbIsStatus? ? 2 : (move.pbIsPhysical?(move.type) ? 0 : 1)
    icons=AnimatedBitmap.new("Graphics/Pictures/category")
    bmp.blt(40-32,20,icons.bitmap,Rect.new(0,cat*28,64,28))
    icons.dispose
    pw=(!move.pbIsStatus? && move.basedamage>0) ? move.basedamage.to_s : "-"
    ac=move.accuracy>0 ? _INTL("{1}%",move.accuracy) : "-"
    base=Color.new(255,255,255); dim=REM_UI::SILVER; shadow=REM_UI::INK
    pbSetNarrowFont(bmp)
    bmp.font.size=15
    pbDrawTextPositions(bmp,[[_INTL("Categoría"),40,4,2,dim,shadow],[_INTL("Potencia"),120,4,2,dim,shadow],
       [_INTL("Precisión"),200,4,2,dim,shadow]])
    bmp.font.size=26
    pbDrawTextPositions(bmp,[[pw,120,19,2,base,shadow],[ac,200,19,2,base,shadow]])
    bmp.font.size=23
    lines=REM_UI.wrap(bmp,pbGetMessage(MessageTypes::MoveDescriptions,move.id),216)
    if lines.length>4
      lines=lines[0,4]
      lines[3]=lines[3]+"..."
    end
    textpos=[]
    for i in 0...lines.length
      textpos.push([lines[i],12,58+i*22,0,base,shadow])
    end
    pbDrawTextPositions(bmp,textpos)
    loop do
      Graphics.update; Input.update
      break if Input.trigger?(Input::Z) || Input.trigger?(Input::B) || Input.trigger?(Input::C)
    end
    sp.bitmap.dispose; sp.dispose; vp.dispose
  end
end

#===============================================================================
# CALIBRACIÓN DE SPRITES DE COMBATE: plataformas y fondos conservan sus coordenadas nativas; cada sprite se apoya por su arte real (se descuenta el margen transparente inferior
# que mide BitmapWrapperEX), de modo que nada queda hundido ni flotando.
#===============================================================================
class PokemonBattlerSprite
  # Filas vacías por encima del arte (en píxeles de pantalla), para no sacar por arriba a los rivales enormes.
  def remTopTrim
    return @remTopTrim if @remTopTrim
    t=0
    f=@_iconbitmap ? (@_iconbitmap.instance_variable_get(:@bitmapFile) rescue nil) : nil
    if f && !f.disposed?
      h=f.height
      for y in 0...h
        empty=true
        x=0
        while x<h
          if f.get_pixel(x,y).alpha>10
            empty=false; break
          end
          x+=2
        end
        break if !empty
        t+=1
      end
      t*=@_iconbitmap.scale
    end
    @remTopTrim=t
    return t
  end

  def remTrimY
    return 0 if !@_iconbitmap || !@_iconbitmap.respond_to?(:offset_y) || !@_iconbitmap.offset_y
    t=@_iconbitmap.offset_y
    h=self.bitmap ? self.bitmap.height : 0
    return [t,h*2/3].min
  end
end

alias rem_orig_adjustBattleSpriteY adjustBattleSpriteY
def adjustBattleSpriteY(sprite,species,index,metrics=nil)
  ret=rem_orig_adjustBattleSpriteY(sprite,species,index,metrics)
  ret+=sprite.remTrimY if sprite.respond_to?(:remTrimY)
  if (index==1 || index==3) && sprite.respond_to?(:remTopTrim) && sprite.bitmap
    base=(index==3) ? PokeBattle_SceneConstants::FOEBATTLERD2_Y : PokeBattle_SceneConstants::FOEBATTLER_Y
    top=base+ret+sprite.remTopTrim
    ret+=[4-top,24].min if top<4   # arte más alto que el hueco: se baja hasta 24 px, el resto queda recortado
  end
  ret-=3 if index==0 || index==2   # pies del jugador casi sobre el centro de la plataforma
  return ret
end

# Las métricas de PBS/metrics.dat (Y del jugador/rival) estaban calibradas para los sprites estándar y
# hundían a los sprites nuevos (p. ej. +48 px en Bulbasaur). Como ahora cada sprite se apoya por su
# arte real, solo se conserva la altitud de los rivales voladores (acotada).
def getBattleSpriteMetricOffset(species,index,metrics=nil)
  return 0 if index!=1 && index!=3
  metrics=load_data("Data/metrics.dat") if !metrics
  alt=(metrics[2][species] || 0)*2
  alt=32 if alt>32
  return -alt
end

# Tipografía única en combate: la fuente estrecha de los nombres de ataque, también en mensajes y menús.
class PokeBattle_Scene
  alias rem_orig_pbEndBattle pbEndBattle
  def pbEndBattle(result)
    rem_orig_pbEndBattle(result)
    $remBagBattle=false
    pbRemRefreshFollower if defined?(pbRemRefreshFollower)
  end
end

#===============================================================================
# PANTALLA DE EQUIPO "Oniria Noir": franja de tipo en cada panel, marco oscuro de mensajes y menú.
# Los PNG los genera tools/ui/gen_party_noir.py (ranura de la franja: x=245..249, filas 15..88).
#===============================================================================
module REM_UI
  PARTY_STRIPE_X=245; PARTY_STRIPE_Y0=15; PARTY_STRIPE_Y1=88

  def self.drawPartyStripe(bmp,types)
    types=types.select{|t| t && t>=0}.uniq
    return if types.length==0
    mid=(PARTY_STRIPE_Y0+PARTY_STRIPE_Y1)/2
    for y in PARTY_STRIPE_Y0..PARTY_STRIPE_Y1
      if types.length==1 || y<mid
        c=typeColor(types[0])
      elsif y==mid
        c=INK
      else
        c=typeColor(types[1])
      end
      bmp.fill_rect(PARTY_STRIPE_X,y,STRIPE_W,1,c)
      if c!=INK
        bmp.fill_rect(PARTY_STRIPE_X+STRIPE_W-1,y,1,1,Color.new((c.red+255)/2,(c.green+255)/2,(c.blue+255)/2))
      end
    end
  end

  # Barra de mensajes inferior compacta (partyMessage.png, 512x77); las ventanas quedan transparentes con texto claro.
  def self.partyMessageFrame(sprites,viewport,multi=false)
    # Normal: 64 px (y=320), 8 px de aire sobre y bajo el botón SALIR (y=328..376) y 8 px a su derecha.
    # Con CONFIRMAR (selección múltiple) hace falta la versión alta (y=305).
    h=multi ? 79 : 64
    bg=IconSprite.new(0,Graphics.height-h,viewport)
    bg.setBitmap(multi ? "Graphics/Pictures/partyMessageTall" : "Graphics/Pictures/partyMessage")
    bg.z=0   # creado antes que paneles y botón: queda por debajo de ambos
    sprites["msgbg"]=bg
    for k in ["messagebox","helpwindow"]
      sprites[k].opacity=0
      sprites[k].baseColor=Color.new(255,255,255)
      sprites[k].shadowColor=INK
    end
  end

  # Menú contextual (Cambiar, Datos, Objeto, Salir) con marco obsidiana y cursor claro.
  def self.partyCmdWindow(w)
    w.setSkin("Graphics/Windowskins/rem_noir_choice")
    w.instance_variable_set(:@selarrow,AnimatedBitmap.new("Graphics/Pictures/rem_selarrow"))
    w.baseColor=Color.new(255,255,255)
    w.shadowColor=INK
  end
end

#===============================================================================
# DATOS DEL POKÉMON "Oniria Noir": 4 páginas (sin cintas), tarjeta izquierda con franja de tipo,
# tabla de estadísticas con IV/EV, ficha flotante de habilidad y ataques con borde del tipo.
# Los fondos los genera tools/ui/gen_summary_noir.py (la geometría de abajo debe coincidir).
#===============================================================================
module REM_UI
  SUM_STRIPE_X=212; SUM_STRIPE_Y0=58; SUM_STRIPE_Y1=300
  SUM_ROW_Y0=72; SUM_ROW_P=40; SUM_ROW_H=34
  SUM_S3_HEAD=62; SUM_S3_Y0=92; SUM_S3_P=46; SUM_S3_H=40
  SUM_SLOT_Y0=69; SUM_SLOT_P=74; SUM_SLOT_H=64; SUM_LEARN_Y0=16; SUM_LEARN_P=70
  WHITE=Color.new(255,255,255)
  LABEL=Color.new(176,184,200)
  DIM=Color.new(110,118,136)
  UPC=Color.new(255,122,104)     # estadística que sube con la naturaleza
  DNC=Color.new(110,182,255)     # estadística que baja

  def self.vStripe(bmp,x,y0,y1,types)
    types=types.select{|t| t && t>=0}.uniq
    return if types.length==0
    mid=(y0+y1)/2
    for y in y0..y1
      if types.length==1 || y<mid
        c=typeColor(types[0])
      elsif y==mid
        c=INK
      else
        c=typeColor(types[1])
      end
      bmp.fill_rect(x,y,STRIPE_W,1,c)
      if c!=INK
        bmp.fill_rect(x+STRIPE_W-1,y,1,1,Color.new((c.red+255)/2,(c.green+255)/2,(c.blue+255)/2))
      end
    end
  end

  # Texto con formato (<c3=...>) y altura de línea propia.
  def self.fmtText(bmp,x,y,w,text,lineheight)
    text="<c2="+colorToRgb16(WHITE)+colorToRgb16(INK)+">"+text
    chars=getFormattedText(bmp,x,y,w,-1,text,lineheight)
    drawFormattedChars(bmp,chars)
  end

  # Fuente estrecha de tamaño `size`, reducida hasta que `text` quepa en `maxw`.
  def self.fit(bmp,text,maxw,size)
    pbSetNarrowFont(bmp)
    bmp.font.size=size
    bmp.font.size-=1 while bmp.font.size>15 && bmp.text_size(text).width>maxw
  end

  # Dibuja una lista [texto,x,y,alineación,color,tamaño,anchoMáx] con la fuente única.
  def self.texts(bmp,list)
    for t in list
      if t[0]==:c   # [:c,texto,x,cy,alineación,color,tamaño,anchoMáx]: centrado vertical en cy
        fit(bmp,t[1],t[7],t[6])
        pbDrawTextPositions(bmp,[[t[1],t[2],(t[3]-bmp.font.size*0.435).round,t[4],t[5],INK]])
        next
      end
      fit(bmp,t[0],t[6] || 400,t[5] || 24)
      pbDrawTextPositions(bmp,[[t[0],t[1],t[2],t[3] || 0,t[4] || WHITE,INK]])
    end
  end

  # Texto centrado en (cx,cy): horizontal por alineación y vertical por la altura de mayúscula de la fuente estrecha.
  def self.ctext(bmp,text,cx,cy,color,size,maxw)
    fit(bmp,text,maxw,size)
    y=(cy-bmp.font.size*0.435).round
    pbDrawTextPositions(bmp,[[text,cx,y,2,color,INK]])
  end

  def self.borderRect(bmp,x0,y0,x1,y1,c)   # rectángulo de 2 px con esquinas recortadas
    bmp.fill_rect(x0+4,y0,x1-x0-7,2,c); bmp.fill_rect(x0+4,y1-1,x1-x0-7,2,c)
    bmp.fill_rect(x0,y0+4,2,y1-y0-7,c); bmp.fill_rect(x1-1,y0+4,2,y1-y0-7,c)
  end

  def self.dim(c,k)
    return Color.new((c.red*k).to_i,(c.green*k).to_i,(c.blue*k).to_i)
  end
end

class PokemonSummaryScene

  # Tarjeta izquierda común a todas las páginas: bola, nombre, género, nivel, estado, sprite, marcas, objeto y franja de tipo.
  def remDrawCard(pokemon,title,egg=false)
    overlay=@sprites["overlay"].bitmap
    overlay.clear
    imagepos=[]
    ballimage=sprintf("Graphics/Pictures/summaryball%02d",(@pokemon.ballused ? @pokemon.ballused : 0))
    imagepos.push([ballimage,16,56,0,0,-1,-1])
    if !egg
      if pbPokerus(pokemon)==1 || pokemon.hp==0 || @pokemon.status>0
        status=6 if pbPokerus(pokemon)==1
        status=@pokemon.status-1 if @pokemon.status>0
        status=5 if pokemon.hp==0
        imagepos.push(["Graphics/Pictures/statuses",112,92,0,16*status,44,16])
      end
      imagepos.push(["Graphics/Pictures/summaryPokerus",162,92,0,0,-1,-1]) if pbPokerus(pokemon)==2
      imagepos.push(["Graphics/Pictures/shiny",26,130,0,0,-1,-1]) if pokemon.isShiny?
    end
    pbDrawImagePositions(overlay,imagepos)
    REM_UI.texts(overlay,[[title,18,12,0,REM_UI::WHITE,28]])
    REM_UI.fit(overlay,pokemon.name,118,26)
    namew=overlay.text_size(pokemon.name).width
    pbDrawTextPositions(overlay,[[pokemon.name,54,57,0,REM_UI::WHITE,REM_UI::INK]])
    if !egg
      if pokemon.isMale?
        pbDrawTextPositions(overlay,[[_INTL("♂"),54+namew+6,57,0,Color.new(110,170,255),REM_UI::INK]])
      elsif pokemon.isFemale?
        pbDrawTextPositions(overlay,[[_INTL("♀"),54+namew+6,57,0,Color.new(255,120,160),REM_UI::INK]])
      end
      REM_UI.texts(overlay,[[_INTL("Nv{1}",pokemon.level),54,88,0,REM_UI::WHITE,24]])
    end
    REM_UI.texts(overlay,[[_INTL("Objeto"),24,309,0,REM_UI::LABEL,20]])
    if pokemon.hasItem?
      iconfile=pbItemIconFile(pokemon.item)
      icon=AnimatedBitmap.new(iconfile) rescue nil
      if icon
        overlay.stretch_blt(Rect.new(22,335,28,28),icon.bitmap,Rect.new(0,0,icon.width,icon.height))
        icon.dispose
      end
      REM_UI.texts(overlay,[[PBItems.getName(pokemon.item),56,338,0,REM_UI::WHITE,26,152]])
    else
      REM_UI.texts(overlay,[[_INTL("Ninguno"),24,338,0,REM_UI::DIM,26]])
    end
    REM_UI.vStripe(overlay,REM_UI::SUM_STRIPE_X,REM_UI::SUM_STRIPE_Y0,REM_UI::SUM_STRIPE_Y1,
       [pokemon.type1,pokemon.type2]) if !egg
    return overlay
  end

  def drawPageOne(pokemon)
    if pokemon.isEgg?
      drawPageOneEgg(pokemon)
      return
    end
    @sprites["background"].setBitmap("Graphics/Pictures/summary1")
    overlay=remDrawCard(pokemon,_INTL("DATOS"))
    growthrate=pokemon.growthrate
    startexp=PBExperience.pbGetStartExperience(pokemon.level,growthrate)
    endexp=PBExperience.pbGetStartExperience(pokemon.level+1,growthrate)
    shadowpk=(pokemon.isShadow? rescue false)
    labels=[_INTL("N° Dex"),_INTL("Especie"),_INTL("Tipo"),_INTL("EO"),
            shadowpk ? _INTL("Corazón") : _INTL("Experiencia"),
            shadowpk ? _INTL("Estado") : _INTL("Sig. nivel")]
    ry=lambda{|i| REM_UI::SUM_ROW_Y0+REM_UI::SUM_ROW_P*i+5}
    for i in 0...6
      REM_UI.texts(overlay,[[labels[i],248,ry.call(i),0,REM_UI::LABEL,22,92]])
    end
    cx=416
    numcol=pokemon.isShiny? ? Color.new(255,110,100) : REM_UI::WHITE
    ownercol=REM_UI::WHITE
    ownercol=Color.new(110,170,255) if pokemon.ot!="" && pokemon.otgender==0
    ownercol=Color.new(255,120,160) if pokemon.ot!="" && pokemon.otgender==1
    REM_UI.texts(overlay,[
       [sprintf("%03d",pokemon.species),cx,ry.call(0),2,numcol,24,140],
       [PBSpecies.getName(pokemon.species),cx,ry.call(1),2,REM_UI::WHITE,24,140],
       [(pokemon.ot=="") ? _INTL("PRESTADO") : pokemon.ot,cx,ry.call(3),2,ownercol,24,140]])
    ty=REM_UI::SUM_ROW_Y0+REM_UI::SUM_ROW_P*2+3
    if pokemon.type1==pokemon.type2
      overlay.blt(cx-32,ty,@typebitmap.bitmap,Rect.new(0,pokemon.type1*28,64,28))
    else
      overlay.blt(cx-68,ty,@typebitmap.bitmap,Rect.new(0,pokemon.type1*28,64,28))
      overlay.blt(cx+4,ty,@typebitmap.bitmap,Rect.new(0,pokemon.type2*28,64,28))
    end
    if shadowpk
      shadowfract=pokemon.heartgauge*1.0/PokeBattle_Pokemon::HEARTGAUGESIZE
      REM_UI.texts(overlay,[[sprintf("%d/5",5-pokemon.heartStage),cx,ry.call(4),2,REM_UI::WHITE,24,140]])
      pbDrawImagePositions(overlay,[["Graphics/Pictures/summaryShadowBar",246,REM_UI::SUM_ROW_Y0+REM_UI::SUM_ROW_P*4+REM_UI::SUM_ROW_H-6,0,0,(shadowfract*248).floor,-1]])
      heartmessage=[_INTL("¡La puerta de su corazón está abierta! ¡Hacer purificación definitiva!"),
                    _INTL("La puerta de su corazón está casi abierta del todo."),
                    _INTL("La puerta de su corazón está bastante abierta."),
                    _INTL("La puerta de su corazón está un poco abierta."),
                    _INTL("La puerta de su corazón está apenas abierta."),
                    _INTL("La puerta está fuertemente cerrada.")
                    ][pokemon.heartStage]
      REM_UI.texts(overlay,[[heartmessage,cx,ry.call(5),2,REM_UI::WHITE,22,140]])
    else
      REM_UI.texts(overlay,[[sprintf("%d",pokemon.exp),cx,ry.call(4),2,REM_UI::WHITE,24,140],
         [sprintf("%d",endexp-pokemon.exp),cx,ry.call(5),2,REM_UI::WHITE,24,140]])
      if pokemon.level<PBExperience::MAXLEVEL
        # barra de EXP fina en el borde inferior de la fila "Experiencia"
        by=REM_UI::SUM_ROW_Y0+REM_UI::SUM_ROW_P*4+REM_UI::SUM_ROW_H-5
        overlay.fill_rect(246,by,244,3,Color.new(30,34,44))
        w=(pokemon.exp-startexp)*244/(endexp-startexp)
        overlay.fill_rect(246,by,w,3,Color.new(72,144,248))
      end
    end
    REM_UI.ctext(overlay,_INTL("Tecla D: ver en Pokédex"),368,335,Color.new(214,219,228),22,226)
  end

  # Abre la ficha de la Pokédex de la especie y vuelve a Datos sin reiniciar la pantalla.
  def remOpenDex(species)
    pbPlayDecisionSE()
    pbFadeOutIn(99999){
       scene=PokemonPokedexScene.new
       screen=PokemonPokedex.new(scene)
       screen.pbDexEntry(species)
    }
  end

  def drawPageThree(pokemon)
    @sprites["background"].setBitmap("Graphics/Pictures/summary3")
    overlay=remDrawCard(pokemon,_INTL("CARACTERÍSTICAS"))
    statbase=[REM_UI::LABEL]*5
    if !(pokemon.isShadow? rescue false) || pokemon.heartStage<=3
      natup=(pokemon.nature/5).floor
      natdn=(pokemon.nature%5).floor
      if natup!=natdn
        statbase[natup]=REM_UI::UPC
        statbase[natdn]=REM_UI::DNC
      end
    end
    REM_UI.texts(overlay,[[_INTL("Estadística"),248,REM_UI::SUM_S3_HEAD,0,REM_UI::DIM,22]])
    for h in [[_INTL("Valor"),345],[_INTL("IV"),409],[_INTL("EV"),467]]
      REM_UI.texts(overlay,[[h[0],h[1],REM_UI::SUM_S3_HEAD,2,REM_UI::DIM,22]])
    end
    # [nombre, color, valor, índice IV/EV]
    rows=[[_INTL("PS"),REM_UI::LABEL,sprintf("%d/%d",pokemon.hp,pokemon.totalhp),0],
          [_INTL("Ataque"),statbase[0],sprintf("%d",pokemon.attack),1],
          [_INTL("Defensa"),statbase[1],sprintf("%d",pokemon.defense),2],
          [_INTL("At. Esp."),statbase[3],sprintf("%d",pokemon.spatk),4],
          [_INTL("Def. Esp."),statbase[4],sprintf("%d",pokemon.spdef),5],
          [_INTL("Velocidad"),statbase[2],sprintf("%d",pokemon.speed),3]]
    for i in 0...6
      cy=REM_UI::SUM_S3_Y0+REM_UI::SUM_S3_P*i+REM_UI::SUM_S3_H/2
      REM_UI.fit(overlay,rows[i][0],58,24)
      pbDrawTextPositions(overlay,[[rows[i][0],248,(cy-overlay.font.size*0.435).round,0,rows[i][1],REM_UI::INK]])
      REM_UI.ctext(overlay,rows[i][2],345,cy,REM_UI::WHITE,30,60)
      REM_UI.ctext(overlay,sprintf("%d",pokemon.iv[rows[i][3]]),409,cy,REM_UI::WHITE,30,48)
      REM_UI.ctext(overlay,sprintf("%d",pokemon.ev[rows[i][3]]),467,cy,REM_UI::WHITE,30,48)
    end
    if pokemon.hp>0 && pokemon.totalhp>0
      hpzone=0
      hpzone=1 if pokemon.hp<=(pokemon.totalhp/2).floor
      hpzone=2 if pokemon.hp<=(pokemon.totalhp/4).floor
      cols=[Color.new(24,192,32),Color.new(232,168,0),Color.new(248,72,56)]
      overlay.fill_rect(246,REM_UI::SUM_S3_Y0+REM_UI::SUM_S3_H-3,pokemon.hp*248/pokemon.totalhp,2,cols[hpzone])
    end
  end

  # Página 2: memo centrado en su caja y contenedor permanente de Habilidad (nombre + descripción completa).
  def remDrawNotes(overlay,pokemon,memo)
    pbSetNarrowFont(overlay)
    overlay.font.size=24
    plain=memo.gsub(/<[^>]*>/,"").sub(/\n+\z/,"")
    nlines=0
    plain.split("\n",-1).each{|para|
      l=REM_UI.wrap(overlay,para,240).length
      nlines+=(l<1 ? 1 : l)
    }
    h=nlines*28
    y=56+[(152-h)/2,0].max
    REM_UI.fmtText(overlay,248,y,240,memo.sub(/\n+\z/,""),28)
    return if pokemon.isEgg?
    REM_UI.texts(overlay,[[_INTL("Habilidad"),252,223,0,REM_UI::LABEL,24,84],
       [PBAbilities.getName(pokemon.ability),344,223,0,REM_UI::WHITE,24,146]])
    pbSetNarrowFont(overlay)
    overlay.font.size=24
    lines=REM_UI.wrap(overlay,pbGetMessage(MessageTypes::AbilityDescs,pokemon.ability),236)
    if lines.length>4
      lines=lines[0,4]
      lines[3]=lines[3]+"..."
    end
    list=[]
    for i in 0...lines.length
      list.push([lines[i],252,260+i*26,0,REM_UI::WHITE,24])
    end
    REM_UI.texts(overlay,list)
  end

  # Borde de color del tipo + contenido de un hueco de ataque (compartido por la página 4 y la vista de detalle).
  def remDrawMoveSlot(overlay,move,y0,textlist)
    REM_UI.borderRect(overlay,240,y0,495,y0+REM_UI::SUM_SLOT_H-1,move.id>0 ? REM_UI.dim(REM_UI.typeColor(move.type),0.85) : Color.new(46,52,68))
    cy=y0+REM_UI::SUM_SLOT_H/2
    if move.id>0
      textlist.push([:c,PBMoves.getName(move.id),258,cy,0,REM_UI::WHITE,30,190])
      if move.totalpp>0
        pcol=(move.pp==0) ? REM_UI::UPC : REM_UI::WHITE
        textlist.push([:c,sprintf("PP %d/%d",move.pp,move.totalpp),486,cy,1,pcol,26,74])
      end
    else
      textlist.push([:c,"-",258,cy,0,REM_UI::DIM,30,40])
    end
  end

  def drawPageFour(pokemon)
    @sprites["background"].setBitmap("Graphics/Pictures/summary4")
    @sprites["pokemon"].visible=true
    @sprites["pokeicon"].visible=false
    overlay=remDrawCard(pokemon,_INTL("MOVIMIENTOS"))
    textlist=[]
    for i in 0...4
      m=pokemon.moves[i]
      remDrawMoveSlot(overlay,m,REM_UI::SUM_SLOT_Y0+REM_UI::SUM_SLOT_P*i,textlist) if m
    end
    REM_UI.texts(overlay,textlist)
  end

  def drawSelectedMove(pokemon,moveToLearn,moveid)
    @sprites["pokemon"].visible=false if @sprites["pokemon"]
    @sprites["pokeicon"].setBitmap(pbPokemonIconFile(pokemon))
    @sprites["pokeicon"].src_rect=Rect.new(0,0,64,64)
    @sprites["pokeicon"].visible=true
    movedata=PBMoveData.new(moveid)
    basedamage=movedata.basedamage
    category=movedata.category
    accuracy=movedata.accuracy
    overlay=drawMoveSelection(pokemon,moveToLearn)
    pw=(category==2 || basedamage<=0) ? "-" : (basedamage==1 ? "???" : sprintf("%d",basedamage))
    ac=(accuracy==0) ? "-" : sprintf("%d%%",accuracy)
    # filas 114,144,174,204 (28 px): Tipo, Categoría, Potencia, Precisión
    overlay.blt(134,114,@typebitmap.bitmap,Rect.new(0,movedata.type*28,64,28))
    icons=AnimatedBitmap.new("Graphics/Pictures/category")
    overlay.blt(134,144,icons.bitmap,Rect.new(0,category*28,64,28))
    icons.dispose
    REM_UI.texts(overlay,[[:c,pw,166,188,2,REM_UI::WHITE,24,84],[:c,ac,166,218,2,REM_UI::WHITE,24,84]])
    pbSetNarrowFont(overlay); overlay.font.size=21
    lines=REM_UI.wrap(overlay,pbGetMessage(MessageTypes::MoveDescriptions,moveid),186)
    lines=lines[0,5]
    textpos=[]
    for i in 0...lines.length
      textpos.push([lines[i],24,252+i*23,0,REM_UI::WHITE,21])
    end
    REM_UI.texts(overlay,textpos)
  end

  def drawMoveSelection(pokemon,moveToLearn)
    overlay=@sprites["overlay"].bitmap
    overlay.clear
    @sprites["background"].setBitmap("Graphics/Pictures/summary4details")
    @sprites["background"].setBitmap("Graphics/Pictures/summary4learning") if moveToLearn!=0
    textlist=[[_INTL("MOVIMIENTOS"),18,12,0,REM_UI::WHITE,28],
              [:c,_INTL("Tipo"),24,128,0,REM_UI::LABEL,20,90],
              [:c,_INTL("Categoría"),24,158,0,REM_UI::LABEL,20,90],
              [:c,_INTL("Potencia"),24,188,0,REM_UI::LABEL,20,90],
              [:c,_INTL("Precisión"),24,218,0,REM_UI::LABEL,20,90]]
    if pokemon.type1==pokemon.type2
      overlay.blt(117,78,@typebitmap.bitmap,Rect.new(0,pokemon.type1*28,64,28))
    else
      overlay.blt(84,78,@typebitmap.bitmap,Rect.new(0,pokemon.type1*28,64,28))
      overlay.blt(150,78,@typebitmap.bitmap,Rect.new(0,pokemon.type2*28,64,28))
    end
    y0=(moveToLearn!=0) ? REM_UI::SUM_LEARN_Y0 : REM_UI::SUM_SLOT_Y0
    pitch=(moveToLearn!=0) ? REM_UI::SUM_LEARN_P : REM_UI::SUM_SLOT_P
    for i in 0...5
      moveobject=nil
      if i==4
        moveobject=PBMove.new(moveToLearn) if moveToLearn!=0
        y0+=8
      else
        moveobject=pokemon.moves[i]
      end
      remDrawMoveSlot(overlay,moveobject,y0,textlist) if moveobject
      y0+=pitch
    end
    REM_UI.texts(overlay,textlist)
    return overlay
  end
end

#===============================================================================
# POKÉDEX "Oniria Noir": lista con panel de presentación + ficha única con descripción,
# estadísticas base con barras y método de evolución. Sin pisadas, grito, medidas, zonas ni formas.
# Fondos: tools/ui/gen_pokedex_noir.py (pokedexbg / pokedexEntry).
#===============================================================================
module REM_UI
  STAT_ORDER=[[0,"PS"],[1,"Ataque"],[2,"Defensa"],[4,"At. Esp."],[5,"Def. Esp."],[3,"Velocidad"]]

  def self.statColor(v)
    return Color.new(226,70,70) if v<50
    return Color.new(245,165,36) if v<80
    return Color.new(40,200,130) if v<110
    return Color.new(60,200,235)
  end

  # Rectángulo de esquinas recortadas relleno (borde de grosor bw).
  def self.slotBox(bmp,x,y,w,h,fill,border,bw)
    bmp.fill_rect(x+2,y,w-4,h,border); bmp.fill_rect(x,y+2,w,h-4,border); bmp.fill_rect(x+1,y+1,w-2,h-2,border)
    x+=bw; y+=bw; w-=2*bw; h-=2*bw
    bmp.fill_rect(x+1,y,w-2,h,fill); bmp.fill_rect(x,y+1,w,h-2,fill)
  end

  def self.evoText(e)
    t=e[0]; l=e[1]
    name=PBSpecies.getName(e[2])
    item=(l.is_a?(Integer) && l>0 && l<=PBItems.maxValue) ? PBItems.getName(l) : "?"
    how=case t
      when PBEvolution::Happiness,PBEvolution::HappinessDay,PBEvolution::HappinessNight then _INTL("Felicidad")
      when PBEvolution::Level,PBEvolution::LevelMale,PBEvolution::LevelFemale,PBEvolution::LevelDay,
           PBEvolution::LevelNight,PBEvolution::LevelRain,PBEvolution::LevelDarkInParty then _INTL("Nv. {1}",l)
      when PBEvolution::Trade then _INTL("Intercambio")
      when PBEvolution::TradeItem then _INTL("Intercambio + {1}",item)
      when PBEvolution::Item,PBEvolution::ItemMale,PBEvolution::ItemFemale then item
      when PBEvolution::DayHoldItem,PBEvolution::NightHoldItem then _INTL("{1} (sube nivel)",item)
      else _INTL("Especial")
    end
    return _INTL("{1} > {2}",how,name)
  end
end

# Lectura directa de PBS/pokemon.txt: los datos compilados (Data/*.dat) solo se regeneran al arrancar en
# modo debug, así que la Pokédex lee el texto fuente (se recarga si cambia la fecha del archivo).
module REM_UI
  @@pbsCache=nil
  @@pbsTime=nil
  @@pbsPrev={}

  def self.pbsLoad
    t=(File.mtime("PBS/pokemon.txt") rescue nil)
    return @@pbsCache if @@pbsCache && t && @@pbsTime==t
    data={}
    cur=nil
    begin
      File.open("PBS/pokemon.txt","rb"){|f|
        f.each_line{|line|
          line=line.chomp
          line.force_encoding("UTF-8") if line.respond_to?(:force_encoding)
          line=line.sub("\xEF\xBB\xBF","")
          if line=~/\A\[(\d+)\]/
            cur=$1.to_i
            data[cur]={}
          elsif cur && line=~/\A(\w+)=(.*)\z/
            data[cur][$1]=$2
          end
        }
      }
    rescue
      return @@pbsCache
    end
    @@pbsCache=data
    @@pbsTime=t
    @@pbsPrev={}
    for sp in data.keys.sort
      for e in pbsEvosOf(data[sp])
        @@pbsPrev[e[2]]=sp if !@@pbsPrev[e[2]]
      end
    end
    return data
  end

  # [nombre del método, parámetro, especie destino] leídos de la línea Evolutions=
  def self.pbsEvosOf(entry)
    ret=[]
    return ret if !entry || !entry["Evolutions"]
    tokens=entry["Evolutions"].split(",")
    i=0
    while i+1<tokens.length
      target=getConst(PBSpecies,tokens[i].strip)
      ret.push([tokens[i+1].strip,tokens[i+2].to_s.strip,target]) if target && target>0 && target<=PBSpecies.maxValue
      i+=3
    end
    return ret
  end

  def self.pbsEntry(species)
    d=pbsLoad
    return d ? d[species] : nil
  end

  def self.pbsStats(species)
    e=pbsEntry(species)
    return nil if !e || !e["BaseStats"]
    a=e["BaseStats"].split(",").map{|x| x.to_i}
    return a.length==6 ? a : nil
  end

  def self.pbsTypes(species)
    e=pbsEntry(species)
    return nil if !e || !e["Type1"]
    t1=getConst(PBTypes,e["Type1"].strip)
    return nil if !t1
    t2=e["Type2"] ? getConst(PBTypes,e["Type2"].strip) : nil
    return [t1,t2 || t1]
  end

  def self.pbsDex(species)
    e=pbsEntry(species)
    return (e && e["Pokedex"] && e["Pokedex"]!="") ? e["Pokedex"] : nil
  end

  def self.pbsEvos(species)
    return pbsEvosOf(pbsEntry(species))
  end

  def self.pbsPrevOf(species)
    pbsLoad
    return @@pbsPrev[species] || species
  end

  # Texto "método > especie" a partir del nombre del método del PBS (sin tablas por especie).
  def self.pbsEvoText(name,param,target)
    tname=PBSpecies.getName(target)
    lvl=param.to_i
    itemid=getConst(PBItems,param)
    item=itemid ? PBItems.getName(itemid) : param
    moveid=getConst(PBMoves,param)
    move=moveid ? PBMoves.getName(moveid) : param
    how=case name
      when "Level" then _INTL("Nv. {1}",lvl)
      when "LevelMale" then _INTL("Nv. {1} ♂",lvl)
      when "LevelFemale" then _INTL("Nv. {1} ♀",lvl)
      when "LevelDay","LevelDayTime" then _INTL("Nv. {1} (día)",lvl)
      when "LevelNight" then _INTL("Nv. {1} (noche)",lvl)
      when "AttackGreater" then _INTL("Nv. {1} (Atq>Def)",lvl)
      when "DefenseGreater" then _INTL("Nv. {1} (Def>Atq)",lvl)
      when "AtkDefEqual" then _INTL("Nv. {1} (Atq=Def)",lvl)
      when "Silcoon","Cascoon" then _INTL("Nv. {1} (azar)",lvl)
      when "Happiness" then _INTL("Felicidad")
      when "HappinessDay" then _INTL("Felicidad (día)")
      when "HappinessNight" then _INTL("Felicidad (noche)")
      when "Trade" then _INTL("Intercambio")
      when "TradeItem" then _INTL("Intercambio + {1}",item)
      when "Item","ItemMale","ItemFemale" then item
      when "HasMove" then _INTL("Con {1}",move)
      else name=~/\ALevel/ ? _INTL("Nv. {1}",lvl) : _INTL("Especial")
    end
    return _INTL("{1} > {2}",how,tname)
  end
end

# Los sprites de especie del Pokédex usaban AnimatedBitmap (muestra la tira de animación entera);
# ahora usan el mismo BitmapWrapperEX animado que el combate.
class PokemonSprite
  def setSpeciesBitmap(species,female=false,form=0,shiny=false,shadow=false,back=false,egg=false)
    @_iconbitmap.dispose if @_iconbitmap
    @_iconbitmap=nil
    if egg
      @_iconbitmap=pbLoadSpeciesBitmap(species,female,form,shiny,shadow,back,egg)
    else
      file=pbCheckPokemonBitmapFiles([species,back,female,shiny,form,shadow])
      @_iconbitmap=BitmapWrapperEX.new(file,(back ? BACKSPRITE_SCALE : FRONTSPRITE_SCALE)) if file
    end
    self.bitmap=@_iconbitmap ? @_iconbitmap.bitmap : nil
  end
end

class Window_Pokedex
  def initialize(x,y,width,height)
    @ballOwned=AnimatedBitmap.new("Graphics/Pictures/battleBoxOwned")
    @commands=[]
    super(x,y,width,height)
    self.windowskin=nil
    self.rowHeight=38
    refresh
  end

  def dispose
    @ballOwned.dispose
    super
  end

  def drawCursor(index,rect)
    return rect
  end

  def drawItem(index,count,rect)
    return if index >= self.top_row + self.page_item_max
    sel=(self.index==index)
    species=@commands[index][0]
    number=@commands[index][4]
    number-=1 if @commands[index][5]
    x=rect.x; y=rect.y+2; w=rect.width; h=self.rowHeight-4
    REM_UI.slotBox(self.contents,x,y,w,h,
       sel ? Color.new(34,40,54) : Color.new(24,27,36),
       sel ? Color.new(226,244,255) : Color.new(38,43,56),sel ? 2 : 1)
    pbSetNarrowFont(self.contents)
    self.contents.font.size=24
    seen=$Trainer.seen[species]
    pbDrawShadowText(self.contents,x+10,y,48,h,sprintf("%03d",number),
       seen ? REM_UI::LABEL : REM_UI::DIM,REM_UI::INK)
    if seen
      op=$Trainer.owned[species] ? 255 : 80
      self.contents.blt(x+62,y+10,@ballOwned.bitmap,Rect.new(0,0,14,14),op)
      REM_UI.fit(self.contents,@commands[index][1],158,26)
      pbDrawShadowText(self.contents,x+84,y,160,h,@commands[index][1],REM_UI::WHITE,REM_UI::INK)
    else
      pbDrawShadowText(self.contents,x+84,y,160,h,"-----",REM_UI::DIM,REM_UI::INK)
    end
  end
end

module REM_UI
  DEX_MAX=721   # la Pokédex nacional termina en Volcanion (generación 6)
end

class PokemonPokedexScene
  alias rem_orig_pbGetDexList pbGetDexList
  def pbGetDexList()
    return rem_orig_pbGetDexList().select{|e| e[0]<=REM_UI::DEX_MAX}
  end

  # Especies de la Pokédex activa limitadas a #721 (nacional o regional).
  def remDexSpecies
    region=pbGetPokedexRegion()
    list=[]
    if region>=0
      reg=pbAllRegionalSpecies(region)
      for i in 1...reg.length
        list.push(reg[i]) if reg[i] && reg[i]>0 && reg[i]<=REM_UI::DEX_MAX
      end
    end
    list=(1..REM_UI::DEX_MAX).to_a if list.length==0
    return list
  end

  # Centra un sprite animado en (cx,cy) y lo reduce si su fotograma no cabe en maxw x maxh.
  def remFitSprite(sprite,cx,cy,maxw,maxh)
    sprite.zoom_x=1.0; sprite.zoom_y=1.0
    return if !sprite.bitmap || sprite.bitmap.disposed?
    w=sprite.bitmap.width; h=sprite.bitmap.height
    z=[1.0,maxw*1.0/w,maxh*1.0/h].min
    sprite.zoom_x=z; sprite.zoom_y=z
    sprite.x=(cx-(w*z)/2).round
    sprite.y=(cy-(h*z)/2).round
  end

  def pbStartScene
    @dummypokemon=PokeBattle_Pokemon.new(1,1)
    @sprites={}
    @viewport=Viewport.new(0,0,Graphics.width,Graphics.height)
    @viewport.z=99999
    addBackgroundPlane(@sprites,"background",_INTL("pokedexbg"),@viewport)
    @sprites["pokedex"]=Window_Pokedex.new(224,5,288,374)
    @sprites["pokedex"].viewport=@viewport
    @sprites["dexentry"]=IconSprite.new(0,0,@viewport)
    @sprites["dexentry"].setBitmap(_INTL("Graphics/Pictures/pokedexEntry"))
    @sprites["dexentry"].visible=false
    @sprites["remlist"]=BitmapSprite.new(Graphics.width,Graphics.height,@viewport)
    @sprites["overlay"]=BitmapSprite.new(Graphics.width,Graphics.height,@viewport)
    @sprites["overlay"].visible=false
    @sprites["searchtitle"]=Window_AdvancedTextPokemon.newWithSize("",2,-18,Graphics.width,64,@viewport)
    @sprites["searchtitle"].windowskin=nil
    @sprites["searchtitle"].baseColor=Color.new(248,248,248)
    @sprites["searchtitle"].shadowColor=Color.new(0,0,0)
    @sprites["searchtitle"].text=_ISPRINTF("<ac>Modo de Búsqueda</ac>")
    @sprites["searchtitle"].visible=false
    @sprites["searchlist"]=Window_ComplexCommandPokemon.newEmpty(-6,32,284,352,@viewport)
    @sprites["searchlist"].baseColor=Color.new(248,248,248)
    @sprites["searchlist"].shadowColor=Color.new(0,0,0)
    @sprites["searchlist"].visible=false
    @sprites["auxlist"]=Window_CommandPokemonWhiteArrow.newEmpty(256,32,284,224,@viewport)
    @sprites["auxlist"].baseColor=Color.new(248,248,248)
    @sprites["auxlist"].shadowColor=Color.new(0,0,0)
    @sprites["auxlist"].visible=false
    @sprites["messagebox"]=Window_UnformattedTextPokemon.newWithSize("",254,256,264,128,@viewport)
    @sprites["messagebox"].baseColor=Color.new(248,248,248)
    @sprites["messagebox"].shadowColor=Color.new(0,0,0)
    @sprites["messagebox"].visible=false
    @sprites["messagebox"].letterbyletter=false
    # Ventanas de texto del diseño antiguo: se conservan ocultas porque pbRefreshDexList les asigna texto.
    for k in ["dexname","species","seen","owned"]
      @sprites[k]=Window_AdvancedTextPokemon.newWithSize("",0,0,64,64,@viewport)
      @sprites[k].windowskin=nil
      @sprites[k].visible=false
    end
    addBackgroundPlane(@sprites,"searchbg",_INTL("pokedexSearchbg"),@viewport)
    @sprites["searchbg"].visible=false
    @sprites["slider"]=IconSprite.new(Graphics.width-44,62,@viewport)
    @sprites["slider"].setBitmap(sprintf("Graphics/Pictures/pokedexSlider"))
    @sprites["slider"].visible=false
    @sprites["icon"]=PokemonSprite.new(@viewport)
    @sprites["entryicon"]=PokemonSprite.new(@viewport)
    @sprites["remlist"].z=1
    @sprites["overlay"].z=1
    @sprites["icon"].z=2
    @sprites["entryicon"].z=2
    @searchResults=false
    pbRefreshDexList($PokemonGlobal.pokedexIndex[pbGetSavePositionIndex])
    pbDeactivateWindows(@sprites)
    pbFadeInAndShow(@sprites)
  end

  # Sprite animado centrado en el pozo + panel de presentación (nombre, tipos y contadores).
  def setIconBitmap(species)
    gender=($Trainer.formlastseen[species][0] rescue 0)
    form=($Trainer.formlastseen[species][1] rescue 0)
    @sprites["icon"].setSpeciesBitmap(species,(gender==1),form)
    remFitSprite(@sprites["icon"],115,128,184,212)
    remDrawShowcase(species,gender,form)
  end

  def remDrawShowcase(species,gender,form)
    bmp=@sprites["remlist"].bitmap
    bmp.clear
    if species>0
      @dummypokemon.species=species
      @dummypokemon.setGender(gender)
      @dummypokemon.forceForm(form)
      REM_UI.texts(bmp,[[PBSpecies.getName(species),115,246,2,REM_UI::WHITE,30,190]])
      typebmp=AnimatedBitmap.new(_INTL("Graphics/Pictures/types"))
      pt=REM_UI.pbsTypes(species) || [@dummypokemon.type1,@dummypokemon.type2]
      t1=pt[0]; t2=pt[1]
      if t1==t2
        bmp.blt(115-32,282,typebmp.bitmap,Rect.new(0,t1*28,64,28))
      else
        bmp.blt(115-68,282,typebmp.bitmap,Rect.new(0,t1*28,64,28))
        bmp.blt(115+4,282,typebmp.bitmap,Rect.new(0,t2*28,64,28))
      end
      typebmp.dispose
    else
      REM_UI.texts(bmp,[["-----",115,246,2,REM_UI::DIM,30,190]])
    end
    if @searchResults
      pool=@dexlist.map{|i| i[0]}
    else
      pool=remDexSpecies
    end
    seenno=0; ownedno=0
    for sp in pool
      seenno+=1 if $Trainer.seen[sp]
      ownedno+=1 if $Trainer.owned[sp]
    end
    total=pool.length
    REM_UI.texts(bmp,[[_INTL("Vistos"),67,323,2,REM_UI::LABEL,18,90],[sprintf("%d/%d",seenno,total),67,340,2,REM_UI::WHITE,26,90],
       [_INTL("Capturados"),163,323,2,REM_UI::LABEL,18,90],[sprintf("%d/%d",ownedno,total),163,340,2,REM_UI::WHITE,26,90]])
  end

  # Ficha única: identidad y descripción a la izquierda; estadísticas base y evolución a la derecha.
  def pbChangeToDexEntry(species)
    @sprites["entryicon"].visible=true
    @sprites["dexentry"].visible=true
    @sprites["overlay"].visible=true
    overlay=@sprites["overlay"].bitmap
    overlay.clear
    indexNumber=pbGetRegionalNumber(pbGetPokedexRegion(),species)
    indexNumber=species if indexNumber==0
    indexNumber-=1 if DEXINDEXOFFSETS.include?(pbGetPokedexRegion)
    gender=($Trainer.formlastseen[species][0] rescue 0)
    form=($Trainer.formlastseen[species][1] rescue 0)
    @dummypokemon.species=species
    @dummypokemon.setGender(gender)
    @dummypokemon.forceForm(form)
    owned=$Trainer.owned[species]
    REM_UI.texts(overlay,[[sprintf("N° %03d",indexNumber),20,17,0,REM_UI::LABEL,24,70],
       [PBSpecies.getName(species),212,13,1,REM_UI::WHITE,28,124]])
    typebmp=AnimatedBitmap.new(_INTL("Graphics/Pictures/types"))
    pt=REM_UI.pbsTypes(species) || [@dummypokemon.type1,@dummypokemon.type2]
    t1=pt[0]; t2=pt[1]
    if t1==t2
      overlay.blt(115-32,66,typebmp.bitmap,Rect.new(0,t1*28,64,28))
    else
      overlay.blt(115-68,66,typebmp.bitmap,Rect.new(0,t1*28,64,28))
      overlay.blt(115+4,66,typebmp.bitmap,Rect.new(0,t2*28,64,28))
    end
    typebmp.dispose
    # estadísticas base
    base=REM_UI.pbsStats(species) || @dummypokemon.baseStats
    bst=0
    for v in base; bst+=v; end
    REM_UI.texts(overlay,[[_INTL("Estadísticas Base"),244,10,0,REM_UI::LABEL,22,150],
       [_INTL("Total {1}",bst),492,10,1,REM_UI::WHITE,22,100]])
    for i in 0...6
      idx=REM_UI::STAT_ORDER[i][0]
      v=base[idx]
      y=40+30*i
      REM_UI.texts(overlay,[[:c,_INTL(REM_UI::STAT_ORDER[i][1]),244,y+14,0,REM_UI::LABEL,22,84],
         [:c,sprintf("%d",v),330,y+14,1,REM_UI::WHITE,26,38]])
      w=[v,200].min*150/200
      w=1 if w<1
      overlay.fill_rect(340,y+10,w,8,REM_UI.statColor(v))
    end
    # evolución (datos de evolutions.dat, compilado desde el PBS) en una caja compacta de 2 líneas
    evos=REM_UI.pbsEntry(species) ? REM_UI.pbsEvos(species) : pbGetEvolvedFormData(species).select{|e| e[2]<=PBSpecies.maxValue}
    prev=REM_UI.pbsEntry(species) ? REM_UI.pbsPrevOf(species) : pbGetPreviousForm(species)
    branchlines=[]
    branchlines.push([_INTL("Evoluciona de {1}",PBSpecies.getName(prev)),REM_UI::DIM]) if prev!=species
    for e in evos
      branchlines.push([(e.length==3 && e[0].is_a?(String)) ? REM_UI.pbsEvoText(e[0],e[1],e[2]) : REM_UI.evoText(e),REM_UI::WHITE])
    end
    @remBranches=branchlines
    @remMulti=(evos.length>1)
    lines=[]
    if @remMulti
      lines.push([_INTL("Tecla S: ver ramificaciones"),Color.new(214,219,228)])   # el origen va en el árbol
    else
      lines=branchlines
      if evos.length==0
        lines.push([prev!=species ? _INTL("Fase final") : _INTL("No evoluciona"),REM_UI::WHITE])
      end
      lines=lines[0,2]
    end
    for i in 0...lines.length
      cy=(lines.length==1) ? 346 : 331+i*30
      REM_UI.texts(overlay,[[:c,lines[i][0],115,cy,2,lines[i][1],24,200]])
    end
    # descripción (PBS) en el cuadro inferior derecho
    pbSetNarrowFont(overlay)
    overlay.font.size=23
    text=owned ? (REM_UI.pbsDex(species) || @dummypokemon.dexEntry) : _INTL("Aún no has capturado a este Pokémon, así que su descripción sigue sin registrarse.")
    dlines=REM_UI.wrap(overlay,text,244)
    if dlines.length>5
      dlines=dlines[0,5]
      dlines[4]=dlines[4]+"..."
    end
    dy=232+(144-dlines.length*23)/2
    list=[]
    for i in 0...dlines.length
      list.push([dlines[i],246,dy+i*23,0,owned ? REM_UI::WHITE : REM_UI::DIM,23])
    end
    REM_UI.texts(overlay,list)
    if @remBranch && @remMulti
      @sprites["entryicon"].visible=false
      n=@remBranches.length
      pitch=[30,(186/n).floor].min
      size=(pitch>=26) ? 24 : ((pitch>=22) ? 21 : 18)
      cy0=206-(n-1)*pitch/2.0
      for i in 0...n
        REM_UI.texts(overlay,[[:c,@remBranches[i][0],115,(cy0+i*pitch).round,2,@remBranches[i][1],size,196]])
      end
    else
      @remBranch=false
      @sprites["entryicon"].visible=true
      @sprites["entryicon"].setSpeciesBitmap(species,(gender==1),form)
      remFitSprite(@sprites["entryicon"],115,206,198,196)
    end
    pbPlayCry(@dummypokemon) if !@remSkipCry
  end

  # Alterna entre el sprite y el árbol de ramificaciones evolutivas (tecla S).
  def remToggleBranches(species)
    return if !@remMulti
    @remBranch=!@remBranch
    @remSkipCry=true
    pbChangeToDexEntry(species)
    @remSkipCry=false
  end

  def pbStartDexEntryScene(species)     # al capturar una especie nueva
    @dummypokemon=PokeBattle_Pokemon.new(species,1)
    @sprites={}
    @viewport=Viewport.new(0,0,Graphics.width,Graphics.height)
    @viewport.z=99999
    @sprites["dexentry"]=IconSprite.new(0,0,@viewport)
    @sprites["dexentry"].setBitmap(_INTL("Graphics/Pictures/pokedexentry"))
    @sprites["dexentry"].visible=false
    @sprites["overlay"]=BitmapSprite.new(Graphics.width,Graphics.height,@viewport)
    @sprites["overlay"].visible=false
    @sprites["entryicon"]=PokemonSprite.new(@viewport)
    @sprites["overlay"].z=1
    @sprites["entryicon"].z=2
    pbChangeToDexEntry(species)
    pbFadeInAndShow(@sprites)
  end

  def pbMiddleDexEntryScene             # al capturar una especie nueva
    @remBranch=false
    pbActivateWindow(@sprites,nil){
       loop do
         Graphics.update
         Input.update
         pbUpdate
         if Input.trigger?(Input::Y)
           remToggleBranches(@dummypokemon.species)
         elsif Input.trigger?(Input::B) || Input.trigger?(Input::C)
           if @remBranch
             remToggleBranches(@dummypokemon.species)
           else
             break
           end
         end
       end
    }
  end

  def pbDexEntry(index)
    @remBranch=false
    oldsprites=pbFadeOutAndHide(@sprites)
    pbChangeToDexEntry(@dexlist[index][0])
    pbFadeInAndShow(@sprites)
    curindex=index
    pbActivateWindow(@sprites,nil){
       loop do
         Graphics.update
         Input.update
         pbUpdate
         if Input.trigger?(Input::B)
           if @remBranch
             remToggleBranches(@dexlist[curindex][0])
           else
             pbPlayCancelSE()
             pbFadeOutAndHide(@sprites)
             @sprites["entryicon"].clearBitmap
             break
           end
         elsif Input.trigger?(Input::Y)
           remToggleBranches(@dexlist[curindex][0])
         elsif Input.trigger?(Input::UP)
           nextindex=-1
           i=curindex-1; loop do break unless i>=0
             if $Trainer.seen[@dexlist[i][0]]
               nextindex=i
               break
             end
             i-=1
           end
           if nextindex>=0
             curindex=nextindex
             @remBranch=false
             pbPlayCursorSE()
             pbChangeToDexEntry(@dexlist[curindex][0])
           end
         elsif Input.trigger?(Input::DOWN)
           nextindex=-1
           for i in curindex+1...@dexlist.length
             if $Trainer.seen[@dexlist[i][0]]
               nextindex=i
               break
             end
           end
           if nextindex>=0
             curindex=nextindex
             @remBranch=false
             pbPlayCursorSE()
             pbChangeToDexEntry(@dexlist[curindex][0])
           end
         elsif Input.trigger?(Input::A)
           pbPlayCry(@dexlist[curindex][0])
         end
       end
    }
    $PokemonGlobal.pokedexIndex[pbGetSavePositionIndex]=curindex if !@searchResults
    @sprites["pokedex"].index=curindex
    @sprites["pokedex"].refresh
    iconspecies=@sprites["pokedex"].species
    iconspecies=0 if !$Trainer.seen[iconspecies]
    setIconBitmap(iconspecies)
    pbFadeInAndShow(@sprites,oldsprites)
  end
end

#===============================================================================
# MOCHILA "Oniria Noir" (mundo y combate comparten PokemonBag_Scene): título del bolsillo, mochila con
# indicador de 8 puntos, lista de huecos de una línea y pie de ancho completo con icono + descripción.
# Fondo y mochilas recoloreadas: tools/ui/gen_bag_noir.py.
#===============================================================================
module REM_UI
  BAG_FOOT=80
  BAG_HIDDEN=[6,7]   # Cartas y Combate: eliminados (sus objetos pasan a Objetos)

  # Bolsillos navegables: en combate solo Medicinas, Poké Balls y Bayas.
  def self.bagPockets
    return [2,3,5] if $remBagBattle   # lo activa PokeBattle_Scene#pbItemMenu
    ret=[]
    for i in 1..PokemonBag.numPockets
      ret.push(i) if !BAG_HIDDEN.include?(i)
    end
    return ret
  end

  def self.bagStep(cur,dir)
    list=bagPockets
    i=list.index(cur) || 0
    return list[(i+dir)%list.length]
  end
  BAG_SHADOW=Color.new(40,44,55)

  # Ventana auxiliar (cantidad, Sí/No, menú de acciones) con el marco obsidiana de las demás pantallas.
  def self.noirWindow(w)
    w.setSkin("Graphics/Windowskins/rem_noir_choice") if w.respond_to?(:setSkin)
    if w.instance_variable_get(:@selarrow)
      w.instance_variable_set(:@selarrow,AnimatedBitmap.new("Graphics/Pictures/rem_selarrow"))
    end
    w.baseColor=WHITE
    w.shadowColor=INK
  end

  # Triángulo relleno de 6x11 apuntando a la izquierda (dir=-1) o a la derecha (dir=1).
  def self.arrow(bmp,x,cy,dir,c)
    for dy in -5..5
      w=6-dy.abs
      bmp.fill_rect(dir<0 ? x+(6-w) : x,cy+dy,w,1,c)
    end
  end
end

class PokemonBag_Scene
  remove_const(:ITEMSVISIBLE) if const_defined?(:ITEMSVISIBLE)
  ITEMSVISIBLE=7

  def pbStartScene(bag)
    $remBagFooter=true
    @viewport=Viewport.new(0,0,Graphics.width,Graphics.height)
    @viewport.z=99999
    @bag=bag
    @sprites={}
    @remOldPocket=@bag.lastpocket
    if !REM_UI.bagPockets.include?(@bag.lastpocket)
      @bag.lastpocket=REM_UI.bagPockets[0]
    end
    lastpocket=@bag.lastpocket
    lastitem=@bag.getChoice(lastpocket)
    @sprites["background"]=IconSprite.new(0,0,@viewport)
    @sprites["background"].setBitmap("Graphics/Pictures/bagNoir")
    @sprites["bag"]=IconSprite.new(39,78,@viewport)
    @sprites["remhead"]=BitmapSprite.new(Graphics.width,Graphics.height,@viewport)
    @sprites["remprev"]=BitmapSprite.new(Graphics.width,Graphics.height,@viewport)
    @sprites["icon"]=ItemIconSprite.new(44,336,-1,@viewport)   # icono nativo (1x) en su pedestal
    @sprites["icon"].z=2
    @sprites["itemwindow"]=Window_PokemonBag.new(@bag,lastpocket,198,-1,314,32+ITEMSVISIBLE*38)
    @sprites["itemwindow"].viewport=@viewport
    @sprites["itemwindow"].rowHeight=38
    @sprites["itemwindow"].pocket=lastpocket
    @sprites["itemwindow"].index=lastitem
    @sprites["itemwindow"].refresh
    @sprites["helpwindow"]=Window_UnformattedTextPokemon.new("")
    @sprites["helpwindow"].visible=false
    @sprites["helpwindow"].viewport=@viewport
    REM_UI.noirWindow(@sprites["helpwindow"])
    @sprites["msgwindow"]=Window_AdvancedTextPokemon.new("")
    @sprites["msgwindow"].visible=false
    @sprites["msgwindow"].viewport=@viewport
    REM_UI.noirWindow(@sprites["msgwindow"])
    pbBottomLeftLines(@sprites["helpwindow"],1)
    pbDeactivateWindows(@sprites)
    pbRefresh
    pbFadeInAndShow(@sprites)
  end

  alias rem_bag_pbEndScene pbEndScene
  def pbEndScene
    rem_bag_pbEndScene
    $remBagFooter=false
  end

  def pbRefresh
    remDrawHeader
    remRefreshItem
    @sprites["itemwindow"].refresh
  end

  # Título del bolsillo, mochila del bolsillo activo e indicador de 8 puntos con flechas.
  def remDrawHeader
    bmp=@sprites["remhead"].bitmap
    bmp.clear
    pocket=@bag.lastpocket
    REM_UI.texts(bmp,[[:c,PokemonBag.pocketNames()[pocket],103,28,2,REM_UI::WHITE,28,176]])
    f=sprintf("Graphics/Pictures/bag#{pocket}f")
    if $Trainer.isFemale? && pbResolveBitmap(f)
      @sprites["bag"].setBitmap(f)
    else
      @sprites["bag"].setBitmap(sprintf("Graphics/Pictures/bag#{pocket}"))
    end
    list=REM_UI.bagPockets
    n=list.length
    x0=103-(n*24-8)/2          # iconos de 16 px separados 8 px y centrados bajo la mochila
    icons=AnimatedBitmap.new("Graphics/Pictures/bagPockets")
    for k in 0...n
      ix=x0+k*24
      on=(list[k]==pocket)
      bmp.blt(ix,250,icons.bitmap,Rect.new((list[k]-1)*16,on ? 16 : 0,16,16))
      bmp.fill_rect(ix+1,270,14,2,REM_UI::SILVER) if on
    end
    icons.dispose
    REM_UI.arrow(bmp,14,258,-1,REM_UI::LABEL)
    REM_UI.arrow(bmp,180,258,1,REM_UI::LABEL)
  end

  # Pie: icono del objeto + descripción completa (y datos del movimiento en el bolsillo de MT/MO).
  def remRefreshItem
    itemwindow=@sprites["itemwindow"]
    item=itemwindow.item
    @sprites["icon"].item=item
    bmp=@sprites["remprev"].bitmap
    bmp.clear
    if item==0
      desc=_INTL("Guarda la mochila y vuelve al juego.")
    else
      desc=pbGetMessage(MessageTypes::ItemDescriptions,item)
    end
    tm=(item!=0 && pbIsMachine?(item))
    if tm
      move=$ItemData[item][ITEMMACHINE]
      md=PBMoveData.new(move)
      types=AnimatedBitmap.new(_INTL("Graphics/Pictures/types"))
      bmp.stretch_blt(Rect.new(84,303,56,24),types.bitmap,Rect.new(0,md.type*28,64,28))
      types.dispose
      icons=AnimatedBitmap.new("Graphics/Pictures/category")
      bmp.stretch_blt(Rect.new(144,303,56,24),icons.bitmap,Rect.new(0,md.category*28,64,28))
      icons.dispose
      pw=(md.category==2 || md.basedamage<=0) ? "-" : (md.basedamage==1 ? "???" : sprintf("%d",md.basedamage))
      ac=(md.accuracy==0) ? "-" : sprintf("%d%%",md.accuracy)
      REM_UI.texts(bmp,[[:c,_INTL("Potencia {1}",pw),212,315,0,REM_UI::WHITE,22,130],
                        [:c,_INTL("Precisión {1}",ac),356,315,0,REM_UI::WHITE,22,130]])
    end
    pbSetNarrowFont(bmp)
    size=tm ? 20 : 22
    bmp.font.size=size
    maxlines=tm ? 2 : 3
    lines=REM_UI.wrap(bmp,desc,404)
    if lines.length>maxlines
      lines=lines[0,maxlines]
      lines[maxlines-1]=lines[maxlines-1]+"..."
    end
    pitch=tm ? 21 : 24
    cy0=tm ? 349-(lines.length-1)*pitch/2.0 : 336-(lines.length-1)*pitch/2.0
    list=[]
    for i in 0...lines.length
      list.push([:c,lines[i],84,(cy0+i*pitch).round,0,REM_UI::WHITE,size,404])
    end
    REM_UI.texts(bmp,list)
  end
end

class Window_PokemonBag
  def drawCursor(index,rect)
    return rect
  end

  def drawItem(index,count,rect)
    pocket=@bag.pockets[self.pocket]
    x=rect.x; y=rect.y+2; w=rect.width; h=@row_height-4
    sel=(self.index==index)
    sorting=(index==@sortIndex)
    border=sorting ? Color.new(245,165,36) : (sel ? Color.new(214,219,228) : Color.new(38,43,56))
    REM_UI.slotBox(self.contents,x,y,w,h,sel ? Color.new(30,34,45) : Color.new(24,27,36),border,(sel || sorting) ? 2 : 1)
    close=(index==pocket.length)
    item=close ? 0 : pocket[index][0]
    bmp=(pbBitmap(pbItemIconFile(item)) rescue nil)
    self.contents.stretch_blt(Rect.new(x+10,y+5,24,24),bmp,Rect.new(0,0,48,48)) if bmp
    pbSetNarrowFont(self.contents)
    self.contents.font.size=24
    if close
      pbDrawShadowText(self.contents,x+44,y,w-54,h,_INTL("Cerrar la mochila"),REM_UI::WHITE,REM_UI::BAG_SHADOW)
      return
    end
    important=pbIsImportantItem?(item)
    qty=important ? "" : _ISPRINTF("x{1: 2d}",pocket[index][1])
    qw=qty=="" ? 0 : self.contents.text_size(qty).width
    reg=(@bag.registeredItem==item) ? 50 : 0
    maxw=w-44-14-qw-(qw>0 ? 8 : 0)-reg
    name=@adapter.getDisplayName(item)
    REM_UI.fit(self.contents,name,maxw,24)
    pbDrawShadowText(self.contents,x+44,y,maxw,h,name,REM_UI::WHITE,REM_UI::BAG_SHADOW)
    if qty!=""
      pbSetNarrowFont(self.contents)
      self.contents.font.size=24
      pbDrawShadowText(self.contents,x,y,w-14,h,qty,REM_UI::WHITE,REM_UI::BAG_SHADOW,1)
    end
    if reg>0
      pbDrawImagePositions(self.contents,[["Graphics/Pictures/bagReg",x+w-14-qw-(qw>0 ? 8 : 0)-46,y+5,0,0,-1,-1]])
    end
  end
end

# Cartas (6) y Combate (7) ya no existen: sus objetos se guardan en Objetos (1), también los de partidas ya guardadas.
alias rem_orig_pbGetPocket pbGetPocket
def pbGetPocket(item)
  p=rem_orig_pbGetPocket(item)
  return 1 if REM_UI::BAG_HIDDEN.include?(p)
  return p
end

class PokemonBag
  alias rem_orig_pockets pockets
  def pockets
    ps=rem_orig_pockets
    for k in REM_UI::BAG_HIDDEN
      next if !ps[k] || ps[k].length==0
      for entry in ps[k]
        next if !entry
        found=nil
        for e in ps[1]
          found=e if e && e[0]==entry[0]
        end
        if found
          found[1]=[found[1]+entry[1],BAGMAXPERSLOT].min
        else
          ps[1].push(entry)
        end
      end
      ps[k].clear
    end
    return ps
  end
end

#===============================================================================
# FICHA DE ENTRENADOR, OPCIONES, CARGA Y MARCO GLOBAL "Oniria Noir"
# Fondos y marcos: tools/ui/gen_menus_noir.py
#===============================================================================
# --- Marco de diálogo, menús y fuente bloqueados (ya no son opciones del jugador) ---
module MessageConfig
  remove_const(:TextSkinName) if const_defined?(:TextSkinName)
  TextSkinName="rem_noir_speech"
  remove_const(:ChoiceSkinName) if const_defined?(:ChoiceSkinName)
  ChoiceSkinName="rem_noir_choice"
  remove_const(:FontName) if const_defined?(:FontName)
  FontName="Power Green Narrow"
  @@systemFrame=nil
  @@defaultTextSkin=nil
  @@systemFont=nil

  def self.pbSetSystemFrame(value)
    @@systemFrame=pbResolveBitmap("Graphics/Windowskins/rem_noir_choice") || ""
  end

  def self.pbSetSpeechFrame(value)
    @@defaultTextSkin=pbResolveBitmap("Graphics/Windowskins/rem_noir_speech") || ""
  end

  def self.pbSetSystemFontName(value)
    @@systemFont=MessageConfig.pbTryFonts(FontName,"Arial Narrow","Arial")
  end
end

class PokemonSystem
  def frame; return 0; end
  def textskin; return 0; end
  def font; return 0; end
  def border; return 0; end
  def runstyle; return 0; end
  alias rem_orig_initialize initialize
  def initialize
    rem_orig_initialize
    @textspeed=2     # Rápida
    @battlescene=0   # Animación de combate: Sí
    @battlestyle=1   # Fijo
    @bgmvolume=100
    @sevolume=100
  end
end

#-------------------------------------------------------------------------------
# OPCIONES: 6 ajustes en una sola pantalla, sin desplazamiento
#-------------------------------------------------------------------------------
class Window_PokemonOption
  def initialize(options,x,y,width,height)
    @options=options
    @optvalues=[]
    @mustUpdateOptions=false
    for i in 0...@options.length
      @optvalues[i]=0
    end
    super(x,y,width,height)
    self.windowskin=nil
    self.rowHeight=34
  end

  def drawCursor(index,rect)
    return rect
  end

  def drawItem(index,count,rect)
    x=rect.x; y=rect.y+2; w=rect.width; h=@row_height-6
    sel=(self.index==index)
    REM_UI.slotBox(self.contents,x,y,w,h,sel ? Color.new(30,34,45) : Color.new(24,27,36),
       sel ? Color.new(214,219,228) : Color.new(38,43,56),sel ? 2 : 1)
    cy=y+h/2
    pbSetNarrowFont(self.contents)
    if index==@options.length
      REM_UI.ctext(self.contents,_INTL("Salir"),x+w/2,cy,REM_UI::WHITE,26,200)
      return
    end
    REM_UI.texts(self.contents,[[:c,@options[index].name,x+12,cy,0,REM_UI::WHITE,24,170]])
    opt=@options[index]
    vx=x+196; vw=w-196-12
    if opt.is_a?(EnumOption)
      vals=opt.values
      n=vals.length
      pw=(vw-(n-1)*6)/n
      for k in 0...n
        on=(k==self[index])
        px=vx+k*(pw+6)
        REM_UI.slotBox(self.contents,px,y+3,pw,h-6,on ? Color.new(48,56,78) : Color.new(20,22,29),
           on ? Color.new(214,219,228) : Color.new(52,58,76),1)
        REM_UI.ctext(self.contents,vals[k],px+pw/2,cy,on ? REM_UI::WHITE : REM_UI::DIM,22,pw-6)
      end
    elsif opt.is_a?(SliderOption)
      val=opt.optstart+self[index]
      tw=vw-52
      self.contents.fill_rect(vx,cy-2,tw,4,Color.new(46,52,68))
      fill=tw*val/opt.optend
      self.contents.fill_rect(vx,cy-2,fill,4,Color.new(214,219,228))
      self.contents.fill_rect(vx+[fill-3,0].max,cy-8,6,16,REM_UI::WHITE)
      REM_UI.ctext(self.contents,sprintf("%d",val),vx+vw-20,cy,REM_UI::WHITE,24,44)
    else
      REM_UI.ctext(self.contents,sprintf("%d",opt.optstart+self[index]),vx+vw/2,cy,REM_UI::WHITE,24,vw)
    end
  end
end

class PokemonOptionScene
  def pbStartScene(inloadscreen=false)
    @sprites={}
    @viewport=Viewport.new(0,0,Graphics.width,Graphics.height)
    @viewport.z=99999
    @sprites["bg"]=IconSprite.new(0,0,@viewport)
    @sprites["bg"].setBitmap("Graphics/Pictures/optionsNoir")
    @sprites["overlay"]=BitmapSprite.new(Graphics.width,Graphics.height,@viewport)
    @PokemonOptions=[
       EnumOption.new(_INTL("Velocidad de texto"),[_INTL("Lenta"),_INTL("Normal"),_INTL("Rápida")],
          proc { $PokemonSystem.textspeed },
          proc {|value|
             $PokemonSystem.textspeed=value
             MessageConfig.pbSetTextSpeed(pbSettingToTextSpeed(value))
          }
       ),
       EnumOption.new(_INTL("Animación de combate"),[_INTL("Sí"),_INTL("No")],
          proc { $PokemonSystem.battlescene },
          proc {|value| $PokemonSystem.battlescene=value }
       ),
       EnumOption.new(_INTL("Estilo de combate"),[_INTL("Cambio"),_INTL("Fijo")],
          proc { $PokemonSystem.battlestyle },
          proc {|value| $PokemonSystem.battlestyle=value }
       ),
       SliderOption.new(_INTL("Volumen BGM"),0,100,5,
          proc { $PokemonSystem.bgmvolume },
          proc {|value|
             if $PokemonSystem.bgmvolume!=value
               $PokemonSystem.bgmvolume=value
               if $game_system.playing_bgm != nil && !inloadscreen
                 $game_system.playing_bgm.volume=value
                 playingBGM=$game_system.getPlayingBGM
                 $game_system.bgm_pause
                 $game_system.bgm_resume(playingBGM)
               end
             end
          }
       ),
       SliderOption.new(_INTL("Volumen SE"),0,100,5,
          proc { $PokemonSystem.sevolume },
          proc {|value|
             if $PokemonSystem.sevolume!=value
               $PokemonSystem.sevolume=value
               if $game_system.playing_bgs != nil
                 $game_system.playing_bgs.volume=value
                 playingBGS=$game_system.getPlayingBGS
                 $game_system.bgs_pause
                 $game_system.bgs_resume(playingBGS)
               end
               pbPlayCursorSE()
             end
          }
       ),
       EnumOption.new(_INTL("Tamaño de pantalla"),[_INTL("P"),_INTL("M"),_INTL("G"),_INTL("MG"),_INTL("Compl")],
          proc { $PokemonSystem.screensize },
          proc {|value|
             oldvalue=$PokemonSystem.screensize
             $PokemonSystem.screensize=value
             if value!=oldvalue
               pbSetResizeFactor($PokemonSystem.screensize)
               ObjectSpace.each_object(TilemapLoader){|o| next if o.disposed?; o.updateClass }
             end
          }
       )
    ]
    @PokemonOptions=pbAddOnOptions(@PokemonOptions)
    @remDescs=[_INTL("Velocidad a la que aparecen los textos de los diálogos."),
               _INTL("Activa o desactiva las animaciones de los movimientos en combate."),
               _INTL("Fijo: no se ofrece cambiar de Pokémon al derrotar a un rival. Cambio: sí se ofrece."),
               _INTL("Volumen de la música de fondo."),
               _INTL("Volumen de los efectos de sonido."),
               _INTL("Tamaño de la ventana del juego."),
               _INTL("Guarda los ajustes y vuelve al menú.")]
    @sprites["option"]=Window_PokemonOption.new(@PokemonOptions,0,40,Graphics.width,
       32+(@PokemonOptions.length+1)*34)
    @sprites["option"].viewport=@viewport
    @sprites["option"].visible=true
    for i in 0...@PokemonOptions.length
      @sprites["option"][i]=(@PokemonOptions[i].get || 0)
    end
    REM_UI.texts(@sprites["overlay"].bitmap,[[_INTL("OPCIONES"),18,12,0,REM_UI::WHITE,28,300]])
    remDrawDesc
    pbDeactivateWindows(@sprites)
    pbFadeInAndShow(@sprites) { pbUpdate }
  end

  def remDrawDesc
    bmp=@sprites["overlay"].bitmap
    bmp.fill_rect(12,308,488,64,Color.new(0,0,0,0))
    idx=[@sprites["option"].index,@remDescs.length-1].min
    pbSetNarrowFont(bmp)
    bmp.font.size=22
    lines=REM_UI.wrap(bmp,@remDescs[idx],468)[0,2]
    for i in 0...lines.length
      REM_UI.texts(bmp,[[:c,lines[i],20,340+(i-(lines.length-1)/2.0)*26,0,REM_UI::WHITE,22,468]])
    end
  end

  def pbOptions
    pbActivateWindow(@sprites,"option"){
       olddesc=-1
       loop do
         Graphics.update
         Input.update
         pbUpdate
         if @sprites["option"].mustUpdateOptions
           for i in 0...@PokemonOptions.length
             @PokemonOptions[i].set(@sprites["option"][i])
           end
         end
         if @sprites["option"].index!=olddesc
           olddesc=@sprites["option"].index
           remDrawDesc
         end
         if Input.trigger?(Input::B)
           break
         end
         if Input.trigger?(Input::C) && @sprites["option"].index==@PokemonOptions.length
           break
         end
       end
    }
  end

  def pbEndScene
    pbFadeOutAndHide(@sprites) { pbUpdate }
    for i in 0...@PokemonOptions.length
      @PokemonOptions[i].set(@sprites["option"][i])
    end
    pbDisposeSpriteHash(@sprites)
    pbRefreshSceneMap
    @viewport.dispose
  end
end

#-------------------------------------------------------------------------------
# FICHA DE ENTRENADOR
#-------------------------------------------------------------------------------
class PokemonTrainerCardScene
  def pbStartScene
    @sprites={}
    @viewport=Viewport.new(0,0,Graphics.width,Graphics.height)
    @viewport.z=99999
    @sprites["card"]=IconSprite.new(0,0,@viewport)
    @sprites["card"].setBitmap("Graphics/Pictures/trainercard")
    @sprites["overlay"]=BitmapSprite.new(Graphics.width,Graphics.height,@viewport)
    @sprites["trainer"]=IconSprite.new(0,0,@viewport)
    @sprites["trainer"].setBitmap(pbPlayerSpriteFile($Trainer.trainertype))
    bw=@sprites["trainer"].bitmap.width; bh=@sprites["trainer"].bitmap.height
    z=[1.0,184.0/bw,180.0/bh].min
    @sprites["trainer"].zoom_x=z
    @sprites["trainer"].zoom_y=z
    @sprites["trainer"].x=(406-bw*z/2).round
    @sprites["trainer"].y=(153-bh*z/2).round
    @sprites["trainer"].z=2
    pbDrawTrainerCardFront
    if $PokemonGlobal.trainerRecording
      $PokemonGlobal.trainerRecording.play
    end
    pbFadeInAndShow(@sprites) { update }
  end

  def pbDrawTrainerCardFront
    overlay=@sprites["overlay"].bitmap
    overlay.clear
    totalsec=Graphics.frame_count/Graphics.frame_rate
    time=_ISPRINTF("{1:02d}:{2:02d}",totalsec/60/60,totalsec/60%60)
    $PokemonGlobal.startTime=pbGetTimeNow if !$PokemonGlobal.startTime
    starttime=_ISPRINTF("{2:d} {1:s} {3:d}",
       pbGetAbbrevMonthName($PokemonGlobal.startTime.mon),
       $PokemonGlobal.startTime.day,$PokemonGlobal.startTime.year)
    pubid=sprintf("%05d",$Trainer.publicID($Trainer.id))
    owned=0; seen=0
    for sp in 1..REM_UI::DEX_MAX
      owned+=1 if $Trainer.owned[sp]
      seen+=1 if $Trainer.seen[sp]
    end
    list=[[:c,_INTL("FICHA DE ENTRENADOR"),18,28,0,REM_UI::WHITE,28,330],
          [:c,_INTL("ID No. {1}",pubid),433,28,2,REM_UI::WHITE,22,120]]
    rows=[[_INTL("Nombre"),$Trainer.name],
          [_INTL("Dinero"),_INTL("${1}",$Trainer.money)],
          [_INTL("Pokédex"),_INTL("{1} capt. / {2} vistos",owned,seen)],
          [_INTL("Tiempo"),time],
          [_INTL("Inicio"),starttime]]
    for i in 0...5
      cy=56+38*i+17
      list.push([:c,rows[i][0],18,cy,0,REM_UI::LABEL,22,80])
      list.push([:c,rows[i][1],290,cy,1,REM_UI::WHITE,24,180])
    end
    list.push([:c,_INTL("MEDALLAS"),20,276,0,REM_UI::LABEL,22,200])
    REM_UI.texts(overlay,list)
    region=pbGetCurrentRegion(0)
    imagePositions=[]
    for i in 0...8
      if $Trainer.badges[i+region*8]
        imagePositions.push(["Graphics/Pictures/badges",20+60*i+10,298+10,i*32,region*32,32,32])
      end
    end
    pbDrawImagePositions(overlay,imagePositions)
  end
end

#-------------------------------------------------------------------------------
# CARGA / MENÚ PRINCIPAL: tarjetas de partida
#-------------------------------------------------------------------------------
class PokemonLoadPanel
  def refresh
    return if @refreshing
    return if disposed?
    @refreshing=true
    if !self.bitmap || self.bitmap.disposed?
      self.bitmap=BitmapWrapper.new(@bgbitmap.width,111*2)
    end
    if @refreshBitmap
      @refreshBitmap=false
      self.bitmap.clear if self.bitmap
      bmp=self.bitmap
      wh=REM_UI::WHITE; lb=REM_UI::LABEL
      if @isContinue
        bmp.blt(0,0,@bgbitmap.bitmap,Rect.new(0,(@selected ? 111*2 : 0),@bgbitmap.width,111*2))
        hour=@totalsec/60/60
        min=@totalsec/60%60
        mapname=pbGetMapNameFromId(@mapid)
        mapname.gsub!(/\\PN/,@trainer.name)
        owned=0
        for sp in 1..REM_UI::DEX_MAX
          owned+=1 if @trainer.owned[sp]
        end
        REM_UI.texts(bmp,[
           [:c,_INTL("Partida Guardada"),16,21,0,wh,26,200],
           [:c,mapname,392,21,1,Color.new(214,219,228),22,180],
           [:c,@trainer.name,62,178,2,wh,26,100],
           [:c,_INTL("Tiempo"),132,76,0,lb,20,52],
           [:c,sprintf("%02d:%02d",hour,min),244,76,1,wh,26,66],
           [:c,_INTL("Medallas"),132,130,0,lb,20,56],
           [:c,sprintf("%d/8",@trainer.numbadges),244,130,1,wh,26,52],
           [:c,_INTL("Dinero"),270,76,0,lb,20,46],
           [:c,_INTL("${1}",@trainer.money),388,76,1,wh,26,70],
           [:c,_INTL("Pokédex"),270,130,0,lb,20,52],
           [:c,sprintf("%d/%d",owned,REM_UI::DEX_MAX),388,130,1,wh,26,64]])
      else
        bmp.blt(0,0,@bgbitmap.bitmap,Rect.new(0,111*2*2+(@selected ? 23*2 : 0),@bgbitmap.width,23*2))
        REM_UI.texts(bmp,[[:c,@title,204,23,2,wh,28,360]])
      end
    end
    @refreshing=false
  end
end

#-------------------------------------------------------------------------------
# PANTALLA DE GUARDADO EN EL MUNDO: misma tarjeta obsidiana que la de carga, con el sprite del mapa
#-------------------------------------------------------------------------------
class PokemonSaveScene
  def pbStartScreen
    @viewport=Viewport.new(0,0,Graphics.width,Graphics.height)
    @viewport.z=99999
    @sprites={}
    totalsec=Graphics.frame_count/Graphics.frame_rate
    hour=totalsec/60/60
    min=totalsec/60%60
    owned=0
    if $Trainer.pokedex
      for sp in 1..REM_UI::DEX_MAX
        owned+=1 if $Trainer.owned[sp]
      end
    end
    @sprites["card"]=BitmapSprite.new(262,156,@viewport)
    @sprites["card"].x=6; @sprites["card"].y=6
    bmp=@sprites["card"].bitmap
    REM_UI.slotBox(bmp,0,0,262,156,Color.new(20,22,29),REM_UI::SILVER,1)
    REM_UI.slotBox(bmp,3,3,256,150,Color.new(20,22,29),Color.new(30,34,45),1)
    REM_UI.slotBox(bmp,6,6,250,28,Color.new(24,27,36),Color.new(24,27,36),1)
    REM_UI.slotBox(bmp,12,40,68,108,Color.new(15,17,23),Color.new(38,43,56),1)
    for i in 0...4
      REM_UI.slotBox(bmp,88,40+i*28,164,26,Color.new(27,31,42),Color.new(38,43,56),1)
    end
    wh=REM_UI::WHITE; lb=REM_UI::LABEL
    REM_UI.texts(bmp,[
       [:c,$game_map.name,131,20,2,Color.new(214,219,228),24,236],
       [:c,_INTL("Jugador"),96,53,0,lb,20,56],[:c,$Trainer.name,244,53,1,wh,24,90],
       [:c,_INTL("Tiempo"),96,81,0,lb,20,56],[:c,sprintf("%02d:%02d",hour,min),244,81,1,wh,24,90],
       [:c,_INTL("Medallas"),96,109,0,lb,20,60],[:c,sprintf("%d/8",$Trainer.numbadges),244,109,1,wh,24,80],
       [:c,_INTL("Pokédex"),96,137,0,lb,20,60],[:c,sprintf("%d/%d",owned,REM_UI::DEX_MAX),244,137,1,wh,24,80]])
    meta=pbGetMetadata(0,MetadataPlayerA+$Trainer.metaID)
    if meta
      filename=pbGetPlayerCharset(meta,1,$Trainer)
      @sprites["player"]=TrainerWalkingCharSprite.new(filename,@viewport)
      cw=@sprites["player"].bitmap.width
      ch=@sprites["player"].bitmap.height
      @sprites["player"].src_rect=Rect.new(0,0,cw/4,ch/4)
      @sprites["player"].x=6+46-cw/8
      @sprites["player"].y=6+94-ch/8
      @sprites["player"].z=2
    end
  end
end

# Todas las ventanas (diálogos, elecciones, menús, monedero...) usan los marcos obsidiana: cualquier setSkin
# se redirige, así ni \w[...] de un evento ni código antiguo pueden recuperar un marco por defecto.
class SpriteWindow_Base
  alias rem_orig_setSkin setSkin
  def setSkin(skin)
    name=skin.to_s
    if name=~/speech|sign|message|text/i
      skin="Graphics/Windowskins/rem_noir_speech"
    elsif name!="" && !(name=~/rem_noir/)
      skin="Graphics/Windowskins/rem_noir_choice"
    end
    rem_orig_setSkin(skin)
  end
end
MessageConfig.pbSetSystemFrame(nil)
MessageConfig.pbSetSpeechFrame(nil)

#===============================================================================
# FUENTES: se registran en privado desde Fonts/ (AddFontResourceEx con FR_PRIVATE) al cargar los scripts,
# así el motor las detecta sin instalarlas en Windows y no aparece el aviso de "fuentes que no existen".
#===============================================================================
module FontInstaller
  def self.registerPrivate
    begin
      api=Win32API.new('gdi32','AddFontResourceEx',['P','L','L'],'L')
      for f in Filenames
        path=pbResolveFont(f)
        full=File.expand_path(path)
        api.call(full,0x10,0) if File.exist?(full)
      end
    rescue
    end
  end

  def self.install
    # el registro privado de fuentes ya se hizo al cargar rem_ui.rb
  end
end
FontInstaller.registerPrivate
MessageConfig.pbSetSystemFontName(nil)

#===============================================================================
# MISIONES — encargos del Ayudante del Profesor (Pía): un expediente por inicial.
# REM_Quests es la capa de datos sobre el sistema ya existente (pbRemPia en
# $PokemonGlobal, se guarda con la partida). Estados: :locked :active :ready :completed
#===============================================================================
module REM_Quests
  REGIONS=["Kanto","Johto","Hoenn","Sinnoh","Teselia","Kalos"]

  def self.entries
    first=pbPiaFirst
    ret=[]
    for i in 0...REM_PIA_STARTERS.length
      sym=REM_PIA_STARTERS[i][0]
      next if sym==first          # tu inicial no tiene encargo
      ret.push(build(i))
    end
    return ret
  end

  def self.find(id)
    for q in entries
      return q if q[:id]==id
    end
    return nil
  end

  def self.symOf(id)
    for s in REM_PIA_STARTERS
      return s[0] if ("starter_"+s[0].to_s.downcase).to_sym==id
    end
    return nil
  end

  def self.names(list)
    return pbPiaSpeciesList(list).map{|x| PBSpecies.getName(x)}.join(" / ")
  end

  # Tipos del Pokémon mostrado, leídos de PBS/pokemon.txt (Type1/Type2 de esa especie)
  def self.finalTypes(sp)
    return REM_UI.pbsTypes(sp) || [PBTypes::NORMAL,PBTypes::NORMAL]
  end

  def self.build(i)
    sym=REM_PIA_STARTERS[i][0]
    sp=getConst(PBSpecies,sym)
    name=PBSpecies.getName(sp)
    t=REM_PIA_QUESTS[sym]
    pr=pbPiaProg(sym); g=pbPiaGoals(sym)
    tx=[_INTL("Derrotar {1} {2}",g[0],names(t[0])),
        _INTL("Evolucionar un {1}",names(t[1])),
        _INTL("Derrotar {1} Pokémon de tipo {2}",g[2],PBTypes.getName(getConst(PBTypes,t[2]))),
        _INTL("Capturar {1} Pokémon de tipo {2}",g[3],PBTypes.getName(getConst(PBTypes,t[3])))]
    objs=[]
    for k in 0...4
      objs.push({:text=>tx[k],:cur=>[pr[k],g[k]].min,:goal=>g[k]})
    end
    st=case pbPiaState(sym)
      when :claimed then :completed
      when :ready   then :ready
      when :active  then :active
      else :locked
    end
    return {:id=>("starter_"+sym.to_s.downcase).to_sym,:sym=>sym,:title=>_INTL("Investigación: {1}",name),
      :short=>name,:species=>sp,:state=>st,:objectives=>objs,
      :reward_text=>_INTL("{1} (Nv. 5)",name)}
  end

  def self.done(q)
    return q[:objectives].select{|o| o[:cur]>=o[:goal]}.length
  end
end

# Ayudas para eventos de mapa
def pbUnlockQuest(id)      # deja el encargo disponible (activa el menú de misiones)
  $game_switches[REM_PIA_QUESTS_SWITCH]=true
  $game_map.need_refresh=true if $game_map
  return true
end
def pbActivateQuest(id)    # lo pone en seguimiento
  sym=REM_Quests.symOf(id)
  return false if !sym
  pbUnlockQuest(id)
  return pbPiaSelect(sym)
end
def pbCompleteQuest(id)    # cumple todos los objetivos (queda listo para reclamar)
  sym=REM_Quests.symOf(id)
  return false if !sym
  g=pbPiaGoals(sym); pr=pbPiaProg(sym)
  for k in 0...4; pr[k]=g[k]; end
  d=pbRemPia
  d[:ready][sym]=true
  d[:active]=nil if d[:active]==sym
  return true
end
def pbSetQuestStage(id,stage) # stage = nº de objetivos cumplidos (0..4)
  sym=REM_Quests.symOf(id)
  return false if !sym
  g=pbPiaGoals(sym); pr=pbPiaProg(sym)
  for k in 0...4; pr[k]=(k<stage) ? g[k] : 0; end
  return pbCompleteQuest(id) if stage>=4
  return true
end

class PokemonQuests_Scene
  CYAN=Color.new(74,200,255)
  EMERALD=Color.new(56,216,120)
  GREY=Color.new(130,138,152)
  BG=Color.new(14,16,21)
  PANEL=Color.new(20,22,29)
  ROW=Color.new(24,27,36)
  ROWSEL=Color.new(30,34,45)
  WELL=Color.new(15,17,23)
  WELLB=Color.new(38,43,56)
  GRID=Color.new(19,22,29)
  ROWS=7
  ROWH=45

  def pbStartScene
    @viewport=Viewport.new(0,0,Graphics.width,Graphics.height)
    @viewport.z=99999
    @sprites={}
    @sprites["bg"]=BitmapSprite.new(Graphics.width,Graphics.height,@viewport)
    @sprites["overlay"]=BitmapSprite.new(Graphics.width,Graphics.height,@viewport)
    @sprites["species"]=PokemonSprite.new(@viewport)
    @sprites["species"].z=5
    @icons={}
    @index=0; @top=0; @shown=nil
    drawBackground
    reload
    refresh
    pbFadeInAndShow(@sprites) { pbUpdate }
    loop do
      Graphics.update
      Input.update
      pbUpdate
      if Input.trigger?(Input::B)
        pbPlayCancelSE()
        break
      elsif Input.trigger?(Input::UP)
        move(-1)
      elsif Input.trigger?(Input::DOWN)
        move(1)
      elsif Input.trigger?(Input::C)
        act
      end
    end
    pbFadeOutAndHide(@sprites) { pbUpdate }
    pbEndScene
  end

  def pbUpdate
    pbUpdateSpriteHash(@sprites)
  end

  def pbEndScene
    for i in @icons.values; i.dispose if i && !i.disposed?; end
    pbDisposeSpriteHash(@sprites)
    @viewport.dispose
  end

  def reload
    @list=REM_Quests.entries
    @index=[[@index,@list.length-1].min,0].max
  end

  def move(d)
    return if @list.length==0
    n=[[@index+d,0].max,@list.length-1].min
    return if n==@index
    pbPlayCursorSE()
    @index=n
    @top=@index if @index<@top
    @top=@index-ROWS+1 if @index>=@top+ROWS
    refresh
  end

  # C: reclama si está lista; pone / quita el seguimiento si no. Las completadas quedan bloqueadas.
  def act
    q=@list[@index]
    return if !q
    if q[:state]==:ready
      if pbClaimPiaStarter(q[:sym])
        reload; refresh
      end
    elsif q[:state]==:active
      pbPiaSelect(nil); reload; refresh
    elsif q[:state]==:locked
      pbPiaSelect(q[:sym]); reload; refresh
    else
      pbPlayBuzzerSE() if defined?(pbPlayBuzzerSE)
    end
  end

  # ---- dibujo ---------------------------------------------------------------
  def drawBackground
    bmp=@sprites["bg"].bitmap
    bmp.fill_rect(0,0,512,384,BG)
    x=0
    while x<512; bmp.fill_rect(x,0,1,384,GRID); x+=16; end
    y=0
    while y<384; bmp.fill_rect(0,y,512,1,GRID); y+=16; end
  end

  def box(bmp,x,y,w,h,fill,border)
    REM_UI.slotBox(bmp,x,y,w,h,fill,border,1)
  end

  def pill(bmp,x,y,w,h,text,color,filled,size=15)
    REM_UI.slotBox(bmp,x,y,w,h,filled ? REM_UI.dim(color,0.30) : WELL,color,1)
    REM_UI.texts(bmp,[[:c,text,x+w/2,y+h/2,2,color,size,w-6]])
  end

  def diamond(bmp,cx,cy,r,c)
    for dy in -r..r
      bmp.fill_rect(cx-(r-dy.abs),cy+dy,(r-dy.abs)*2+1,1,c)
    end
  end

  def check(bmp,cx,cy,c)   # visto de 9x7 px
    pts=[[-4,0],[-3,1],[-2,2],[-1,1],[0,0],[1,-1],[2,-2],[3,-3]]
    for p in pts
      bmp.fill_rect(cx+p[0],cy+p[1],2,2,c)
    end
  end

  def checkbox(bmp,x,cy,on)   # 16x16 centrada verticalmente en cy
    box(bmp,x,cy-8,16,16,WELL,on ? EMERALD : WELLB)
    check(bmp,x+8,cy,EMERALD) if on
  end

  def stateInfo(q)
    case q[:state]
    when :active    then return [_INTL("ACTIVA"),CYAN,false,_INTL("EN CURSO")]
    when :ready     then return [_INTL("LISTA"),EMERALD,true,_INTL("LISTA PARA RECLAMAR")]
    when :completed then return [_INTL("HECHA"),EMERALD,false,_INTL("COMPLETADA")]
    end
    return [_INTL("PENDIENTE"),GREY,false,_INTL("SIN INICIAR")]
  end

  # [x,y,ancho,alto] del área no transparente del fotograma (se calcula una vez por especie)
  def boundsFor(species,bitmap)
    @bounds={} if !@bounds
    return @bounds[species] if @bounds[species]
    w=bitmap.width; h=bitmap.height
    x0=w; y0=h; x1=-1; y1=-1
    for y in 0...h
      for x in 0...w
        if bitmap.get_pixel(x,y).alpha>16
          x0=x if x<x0; x1=x if x>x1
          y0=y if y<y0; y1=y if y>y1
        end
      end
    end
    @bounds[species]=(x1<0) ? [0,0,w,h] : [x0,y0,x1-x0+1,y1-y0+1]
    return @bounds[species]
  end

  def iconFor(q)
    return @icons[q[:species]] if @icons[q[:species]]
    file=pbCheckPokemonIconFiles([q[:species],false,false,0,false])
    @icons[q[:species]]=file ? AnimatedBitmap.new(file) : nil
    return @icons[q[:species]]
  end

  def refresh
    bmp=@sprites["overlay"].bitmap
    bmp.clear
    REM_UI.texts(bmp,[[:c,_INTL("MISIONES"),16,22,0,REM_UI::WHITE,30,160]])
    drawList(bmp)
    drawDossier(bmp)
  end

  def drawList(bmp)
    box(bmp,12,40,212,332,PANEL,REM_UI::SILVER)
    for r in 0...ROWS
      i=@top+r
      break if i>=@list.length
      q=@list[i]
      y=46+r*ROWH
      sel=(i==@index)
      box(bmp,18,y,192,ROWH-4,sel ? ROWSEL : ROW,sel ? REM_UI::SILVER : WELLB)
      ic=iconFor(q)
      bmp.stretch_blt(Rect.new(22,y+2,36,36),ic.bitmap,Rect.new(0,0,64,64)) if ic
      info=stateInfo(q)
      if q[:state]==:completed
        box(bmp,44,y+25,13,13,WELL,EMERALD); check(bmp,50,y+31,EMERALD)
      elsif q[:state]==:active || q[:state]==:ready
        box(bmp,44,y+25,13,13,WELL,info[1]); diamond(bmp,50,y+31,3,info[1])
      end
      REM_UI.texts(bmp,[[:c,q[:short],62,y+12,0,REM_UI::WHITE,18,82],
                        [:c,_INTL("{1}/4 objetivos",REM_Quests.done(q)),62,y+29,0,REM_UI::DIM,15,82]])
      pill(bmp,148,y+10,58,20,info[0],info[1],info[2])
    end
    if @list.length>ROWS   # barra de desplazamiento
      th=318; bh=[th*ROWS/@list.length,18].max
      by=44+((th-bh)*@top/(@list.length-ROWS))
      bmp.fill_rect(216,44,3,th,WELL)
      bmp.fill_rect(216,by,3,bh,REM_UI::SILVER)
    end
  end

  def drawDossier(bmp)
    q=@list[@index]
    sp=@sprites["species"]
    return if !q
    info=stateInfo(q)
    # --- tarjeta superior: sprite + identidad ---
    box(bmp,232,40,268,120,PANEL,REM_UI::SILVER)
    box(bmp,240,48,104,104,WELL,WELLB)
    bmp.fill_rect(241,100,102,1,GRID); bmp.fill_rect(292,49,1,102,GRID)
    if @shown!=q[:species]
      sp.setSpeciesBitmap(q[:species])
      @shown=q[:species]
    end
    sp.visible=true
    sp.zoom_x=1.0; sp.zoom_y=1.0
    if sp.bitmap && !sp.bitmap.disposed?
      bb=boundsFor(q[:species],sp.bitmap)     # caja del dibujo opaco: todos se ajustan al marco por igual
      z=[88.0/bb[2],88.0/bb[3]].min
      sp.zoom_x=z; sp.zoom_y=z
      sp.x=(292-(bb[0]+bb[2]/2.0)*z).round
      sp.y=(100-(bb[1]+bb[3]/2.0)*z).round
    end
    REM_UI.texts(bmp,[[:c,q[:title],352,56,0,REM_UI::WHITE,20,140]])
    # fila de tipos (de la especie mostrada, leídos de PBS/pokemon.txt)
    box(bmp,352,70,140,36,WELL,WELLB)
    types=REM_Quests.finalTypes(q[:species])
    tb=AnimatedBitmap.new(_INTL("Graphics/Pictures/types"))
    if types[0]==types[1]
      bmp.stretch_blt(Rect.new(422-26,76,52,23),tb.bitmap,Rect.new(0,types[0]*28,64,28))
    else
      bmp.stretch_blt(Rect.new(422-55,76,52,23),tb.bitmap,Rect.new(0,types[0]*28,64,28))
      bmp.stretch_blt(Rect.new(422+3,76,52,23),tb.bitmap,Rect.new(0,types[1]*28,64,28))
    end
    tb.dispose
    # estado
    pill(bmp,352,114,140,38,info[3],info[1],info[2],20)
    # --- objetivos ---
    box(bmp,232,164,268,208,PANEL,REM_UI::SILVER)
    d=REM_Quests.done(q)
    REM_UI.texts(bmp,[[:c,_INTL("OBJETIVOS"),242,180,0,REM_UI::WHITE,19,110]])
    bmp.fill_rect(366,176,100,8,WELL)
    bmp.fill_rect(367,177,98,6,GRID)
    bmp.fill_rect(367,177,(98*d/4).to_i,6,info[1])
    REM_UI.texts(bmp,[[:c,sprintf("%d/4",d),492,180,1,REM_UI::DIM,16,30]])
    for k in 0...4
      o=q[:objectives][k]
      y=192+k*36
      ok=o[:cur]>=o[:goal]
      box(bmp,240,y,252,32,ROW,ok ? REM_UI.dim(EMERALD,0.6) : WELLB)
      checkbox(bmp,248,y+16,ok)
      col=ok ? EMERALD : REM_UI::WHITE
      REM_UI.texts(bmp,[[:c,o[:text],272,y+16,0,col,19,174],
                        [:c,sprintf("%d/%d",o[:cur],o[:goal]),484,y+16,1,col,19,40]])
    end
    box(bmp,240,340,252,24,WELL,WELLB)
    REM_UI.texts(bmp,[[:c,_INTL("Recompensa: {1}",q[:reward_text]),366,352,2,REM_UI::SILVER,18,240]])
  end
end

#===============================================================================
# MENÚ DE PAUSA — columna flotante de tarjetas Oniria Noir (sin ventana contenedora)
#===============================================================================
module REM_UI
  # Iconos de 2x escala (rejilla de hasta 12x12). '#' = trazo.
  MENU_ICONS={
    :dex=>[".rrrrrrrrrr.","rrrrrrrrrrrr","rrbbbbbbbbrr","rrbbbbbbbbrr","rrbbbbbbbbrr","rrbbbbbbbbrr","rrrrrrrrrrrr","rryyrrrgrrrr","rryyrrrgrrrr","rrrrrrrrrrrr",".rrrrrrrrrr."],
    :ball=>["...RRRRRR...",".RRRRRRRRRR.","RRRRRRRRRRRR","RRRRRRRRRRRR","kkkkkwwkkkkk","kkkkwwwwkkkk","WWWWWwwWWWWW","WWWWWWWWWWWW",".WWWWWWWWWW.","...WWWWWW..."],
    :bag=>["....gggg....","...g....g...","..dddddddd..",".dddddddddd.",".oooooooooo.",".ooyyyyyyoo.",".ooyyyyyyoo.",".ooyyyyyyoo.",".oooooooooo.",".oooooooooo.",".dddddddddd."],
    :quest=>["...gggg...",".nnnnnnnn.",".nppppppn.",".npbbbbpn.",".nppppppn.",".npbbbbpn.",".nppppppn.",".npbbbypn.",".nppppppn.",".nnnnnnnn."],
    :card=>["cccccccccccc","cccccccccccc","cwwwccWWWWcc","cwwwcccccccc","cwwwccWWWWcc","cccccccccccc","ccWWWWWWWWcc","cccccccccccc"],
    :save=>["cccccccccccc","ccWWWWWWWWcc","ccWWWWWWyWcc","ccWWWWWWWWcc","cccccccccccc","cwwwwwwwwwwc","cwwwwwwwwwwc","cwwwwwwwwwwc","cwwwwwwwwwwc","cccccccccccc"],
    :gear=>["....WWWW....",".WW.WWWW.WW.",".WWWWWWWWWW.","..WWW..WWW..","WWWW....WWWW","WWWW....WWWW","..WWW..WWW..",".WWWWWWWWWW.",".WW.WWWW.WW.","....WWWW...."],
    :bug=>["..g......g..","...g....g...","....GGGG....","...GGGGGG...","ggg.GkkG.ggg","...GGGGGG...","ggg.GkkG.ggg","...GGGGGG...","....GGGG...."],
    :exit=>["WWWWWWWWWW","WnnnnnnnnW","WnnnnnnnnW","WnnnnnnnnW","WnnnnnyynW","WnnnnnnnnW","WnnnnnnnnW","WnnnnnnnnW","WWWWWWWWWW"],
    :phone=>["..cccccc..","..cbbbbc..","..cbbbbc..","..cbbbbc..","..cccccc..","..cyccyc..","..cccccc.."]
  }
  MENU_PAL={"r"=>[216,64,60],"R"=>[232,72,60],"b"=>[127,212,255],"y"=>[242,201,76],"g"=>[122,130,148],
    "k"=>[35,38,47],"w"=>[255,255,255],"W"=>[220,226,236],"o"=>[224,138,46],"d"=>[184,96,28],
    "p"=>[232,217,168],"c"=>[74,134,216],"G"=>[76,195,106],"n"=>[168,103,45]}

  def self.menuIconKey(label)
    case label
    when _INTL("Pokédex") then return :dex
    when _INTL("Pokémon") then return :ball
    when _INTL("Mochila") then return :bag
    when _INTL("Pokégear") then return :phone
    when _INTL("Misiones") then return :quest
    when _INTL("Guardar") then return :save
    when _INTL("Opciones") then return :gear
    when _INTL("Depurador") then return :bug
    when _INTL("Salir"),_INTL("Salir del Juego") then return :exit
    end
    return :card      # el nombre del jugador = ficha de entrenador
  end

  # k = brillo (1.0 seleccionada, <1 apagada)
  def self.drawMenuIcon(bmp,key,cx,cy,k)
    g=MENU_ICONS[key] || MENU_ICONS[:card]
    w=g[0].length*2; h=g.length*2
    ox=cx-w/2; oy=cy-h/2
    for r in 0...g.length
      for i in 0...g[r].length
        c=MENU_PAL[g[r][i,1]]
        next if !c
        bmp.fill_rect(ox+i*2,oy+r*2,2,2,Color.new((c[0]*k).to_i,(c[1]*k).to_i,(c[2]*k).to_i))
      end
    end
  end

  def self.vArrow(bmp,cx,cy,dir,c)   # triángulo de 11x6 arriba (dir=-1) o abajo (dir=1)
    for dx in -5..5
      h=6-dx.abs
      bmp.fill_rect(cx+dx,dir<0 ? cy+(6-h) : cy,1,h,c)
    end
  end
end

class PokemonMenu_Scene
  MENU_VISIBLE=6
  MENU_GAP=4
  MENU_H=40
  MENU_HSEL=50

  def pbStartScene
    @viewport=Viewport.new(0,0,Graphics.width,Graphics.height)
    @viewport.z=99999
    @sprites={}
    @sprites["cards"]=BitmapSprite.new(240,Graphics.height,@viewport)
    @sprites["cards"].x=Graphics.width-240
    @sprites["cards"].visible=false
    @sprites["vial"]=BitmapSprite.new(190,44,@viewport)
    @sprites["vial"].x=10
    @sprites["vial"].y=10
    @sprites["vial"].visible=false
    @sprites["infowindow"]=Window_UnformattedTextPokemon.newWithSize("",0,0,32,32,@viewport)
    @sprites["infowindow"].visible=false
    @sprites["helpwindow"]=Window_UnformattedTextPokemon.newWithSize("",0,0,32,32,@viewport)
    @sprites["helpwindow"].visible=false
    @infostate=false
    @helpstate=false
    @menuTop=0
    pbSEPlay("menu")
  end

  def pbHideMenu
    @sprites["vial"].visible=false
    @sprites["cards"].visible=false
    @sprites["infowindow"].visible=false
    @sprites["helpwindow"].visible=false
  end

  def pbShowMenu
    remDrawVial
    @sprites["cards"].visible=true
    @sprites["infowindow"].visible=@infostate
    @sprites["helpwindow"].visible=@helpstate
  end

  def remDrawCards(commands,index)
    bmp=@sprites["cards"].bitmap
    bmp.clear
    n=commands.length
    # fuente exacta de los mensajes (MessageConfig / pbSetSystemFont)
    pbSetSystemFont(bmp)
    mw=0
    for c in commands; mw=[mw,bmp.text_size(c).width].max; end
    uw=[[mw+56,110].max,214].min          # ancho de la tarjeta sin seleccionar: se ajusta a la etiqueta más larga
    sw=uw+14
    fs=bmp.font.size
    while fs>16 && mw>uw-56
      fs-=1; bmp.font.size=fs
      mw=0
      for c in commands; mw=[mw,bmp.text_size(c).width].max; end
    end
    vis=1
    vis+=1 while vis<n && (vis+1)*MENU_H+(MENU_HSEL-MENU_H)+vis*MENU_GAP<=Graphics.height-20
    @menuTop=[[@menuTop,index].min,index-vis+1].max
    @menuTop=0 if @menuTop<0
    @menuTop=n-vis if @menuTop>n-vis
    last=[@menuTop+vis,n].min
    right=@sprites["cards"].bitmap.width-12
    y=10
    top=y
    for i in @menuTop...last
      sel=(i==index)
      h=sel ? MENU_HSEL : MENU_H
      w=sel ? sw : uw
      x=right-w
      key=REM_UI.menuIconKey(commands[i])
      ix=right-uw+8          # eje común de iconos y texto para ambos estados
      if sel
        REM_UI.slotBox(bmp,x,y,w,h,Color.new(28,32,43),REM_UI::SILVER,2)
        bmp.fill_rect(x+3,y+3,w-6,1,Color.new(40,46,61)); bmp.fill_rect(x+3,y+h-4,w-6,1,Color.new(40,46,61))
        bmp.fill_rect(x+3,y+3,1,h-6,Color.new(40,46,61)); bmp.fill_rect(x+w-4,y+3,1,h-6,Color.new(40,46,61))
        REM_UI.slotBox(bmp,ix,y+(h-30)/2,30,30,Color.new(15,17,23),Color.new(46,52,66),1)
        REM_UI.drawMenuIcon(bmp,key,ix+15,y+h/2,1.0)
        base=REM_UI::WHITE; shadow=Color.new(40,44,55)
      else
        REM_UI.slotBox(bmp,x,y,w,h,Color.new(14,16,21,217),Color.new(46,52,66),1)
        REM_UI.slotBox(bmp,ix,y+(h-30)/2,30,30,Color.new(10,12,16,200),Color.new(30,34,44),1)
        REM_UI.drawMenuIcon(bmp,key,ix+15,y+h/2,0.72)
        base=Color.new(150,158,176); shadow=Color.new(30,33,42)
      end
      bmp.font.size=fs
      pbDrawShadowText(bmp,ix+40,y,w-(ix+40-x)-6,h,commands[i],base,shadow)
      y+=h+MENU_GAP
    end
    cx=right-uw/2
    REM_UI.vArrow(bmp,cx,top-8,-1,REM_UI::SILVER) if @menuTop>0
    REM_UI.vArrow(bmp,cx,y-MENU_GAP+3,1,REM_UI::SILVER) if last<n
  end

  # ---- Pokévial: cajita informativa (arriba a la izquierda) solo si lo tienes ----
  def remHasVial?
    return false if pbInSafari? || pbInBugContest?
    return false if !hasConst?(PBItems,:POKEVIAL)
    return $PokemonBag && $PokemonBag.pbQuantity(getConst(PBItems,:POKEVIAL))>0
  rescue
    return false
  end

  def remDrawVial
    spr=@sprites["vial"]
    if !remHasVial?
      spr.visible=false
      return
    end
    bmp=spr.bitmap
    bmp.clear
    cur=pbRemVialCharges; mx=pbRemVialMax
    empty=(cur<=0)
    white=empty ? Color.new(150,158,176) : REM_UI::WHITE
    pbSetSystemFont(bmp)
    bmp.font.size=20
    cw=bmp.text_size(sprintf("%d/%d",cur,mx)).width
    bmp.font.size=17
    hint=empty ? _INTL("Vacío") : _INTL("Z: usar")
    hw=bmp.text_size(hint).width
    w=46+[cw,hw].max+12
    REM_UI.slotBox(bmp,0,0,w,44,Color.new(20,22,29),REM_UI::SILVER,1)
    REM_UI.slotBox(bmp,6,6,32,32,Color.new(15,17,23),Color.new(38,43,56),1)
    file=pbItemIconFile(getConst(PBItems,:POKEVIAL))
    if file && pbResolveBitmap(file)
      ico=AnimatedBitmap.new(file)
      bmp.stretch_blt(Rect.new(8,8,28,28),ico.bitmap,Rect.new(0,0,ico.bitmap.width,ico.bitmap.height))
      ico.dispose
    end
    bmp.font.size=20
    pbDrawShadowText(bmp,46,2,cw+4,22,sprintf("%d/%d",cur,mx),empty ? white : Color.new(74,200,255),Color.new(40,44,55))
    bmp.font.size=17
    pbDrawShadowText(bmp,46,22,hw+4,18,hint,Color.new(122,130,148),Color.new(30,33,42))
    spr.visible=true
  end

  def remUseVial
    @sprites["vial"].visible=false
    ItemHandlers.triggerUseFromBag(getConst(PBItems,:POKEVIAL))
    remDrawVial
  end

  def pbShowCommands(commands)
    ret=-1
    n=commands.length
    index=[[$PokemonTemp.menuLastChoice,n-1].min,0].max
    @sprites["cards"].visible=true
    remDrawCards(commands,index)
    remDrawVial
    loop do
      Graphics.update
      Input.update
      pbUpdateSceneMap
      if Input.trigger?(Input::A) && remHasVial?
        remUseVial
      elsif Input.trigger?(Input::UP)
        index=(index+n-1)%n
        pbPlayCursorSE()
        remDrawCards(commands,index)
      elsif Input.trigger?(Input::DOWN)
        index=(index+1)%n
        pbPlayCursorSE()
        remDrawCards(commands,index)
      elsif Input.trigger?(Input::B)
        ret=-1
        break
      elsif Input.trigger?(Input::C)
        ret=index
        $PokemonTemp.menuLastChoice=ret
        break
      end
    end
    return ret
  end
end


#===============================================================================
# MOVIMIENTOS POR NIVEL desde PBS/pokemon.txt: Data/attacksRS.dat solo se recompila en modo debug y
# quedaba desfasado, así que los Pokémon aprendían los movimientos antiguos al subir de nivel.
#===============================================================================
module REM_UI
  @@pbsMoveCache={}
  # [[nivel, movimiento], ...] de la línea Moves= (nil si no hay entrada o falla)
  def self.pbsMoves(species)
    pbsLoad
    return @@pbsMoveCache[species] if @@pbsMoveCache.has_key?(species) && @@pbsMoveTime==@@pbsTime
    if @@pbsMoveTime!=@@pbsTime
      @@pbsMoveCache={}; @@pbsMoveTime=@@pbsTime
    end
    e=pbsEntry(species)
    ret=nil
    if e && e["Moves"]
      ret=[]
      t=e["Moves"].split(",")
      i=0
      while i+1<t.length
        mv=getConst(PBMoves,t[i+1].strip)
        ret.push([t[i].strip.to_i,mv]) if mv && mv>0
        i+=2
      end
      ret=nil if ret.length==0
    end
    @@pbsMoveCache[species]=ret
    return ret
  end
  @@pbsMoveTime=nil
end

class PokeBattle_Pokemon
  def __mf_getMoveList
    movelist=REM_UI.pbsMoves(@species) rescue nil
    return movelist.map{|m| [m[0],m[1]]} if movelist
    atkdata=pbRgssOpen("Data/attacksRS.dat","rb")
    offset=atkdata.getOffset(@species-1)
    length=atkdata.getLength(@species-1)>>1
    atkdata.pos=offset
    ret=[]
    for k in 0..length-1
      level=atkdata.fgetw
      move=atkdata.fgetw
      ret.push([level,move])
    end
    atkdata.close
    return ret
  end
end

#===============================================================================
# EVOLUCIÓN: la animación llamaba a sprite.pbHasType? sobre un SpriteMetafile (ese método es global
# y privado) y provocaba NoMethodError al evolucionar. Se reescribe con un destello plateado y fondo noir.
#===============================================================================
class REM_NoirPlane < Plane      # fondo obsidiana con rejilla tenue (mosaico de 16 px)
  def initialize(viewport=nil)
    super(viewport)
    bmp=Bitmap.new(16,16)
    bmp.fill_rect(0,0,16,16,Color.new(14,16,21))
    bmp.fill_rect(0,0,16,1,Color.new(19,22,29)); bmp.fill_rect(0,0,1,16,Color.new(19,22,29))
    self.bitmap=bmp
    self.z=0
  end
  def dispose
    self.bitmap.dispose if self.bitmap && !self.bitmap.disposed?
    super
  end
  def update; end
end

class PokemonEvolutionScene
  def pbGenerateMetafiles(s1x,s1y,s2x,s2y)
    sprite=SpriteMetafile.new
    sprite2=SpriteMetafile.new
    sprite.opacity=255
    sprite2.opacity=255
    sprite2.zoom=0.0
    sprite.ox=s1x
    sprite.oy=s1y
    sprite2.ox=s2x
    sprite2.oy=s2y
    alpha=0
    glow=Color.new(230,234,241,0)
    for j in 0...26
      glow.alpha=[alpha,255].min
      sprite.color=Color.new(glow.red,glow.green,glow.blue,glow.alpha)
      sprite2.color=Color.new(glow.red,glow.green,glow.blue,255)
      sprite.update
      sprite2.update
      alpha+=10
    end
    totaltempo=0
    currenttempo=25
    maxtempo=7*Graphics.frame_rate
    while totaltempo<maxtempo
      for j in 0...currenttempo
        sprite.zoom=[1.1*(currenttempo-j-1)/currenttempo,1.0].min
        sprite2.zoom=[1.1*(j+1)/currenttempo,1.0].min
        sprite.update
        sprite2.update
      end
      totaltempo+=currenttempo
      if totaltempo+currenttempo<maxtempo
        for j in 0...currenttempo
          sprite.zoom=[1.1*(j+1)/currenttempo,1.0].min
          sprite2.zoom=[1.1*(currenttempo-j-1)/currenttempo,1.0].min
          sprite.update
          sprite2.update
        end
      end
      totaltempo+=currenttempo
      currenttempo=[(currenttempo/1.5).floor,5].max
    end
    @metafile1=sprite
    @metafile2=sprite2
  end

  def pbStartScreen(pokemon,newspecies)
    @sprites={}
    @bgviewport=Viewport.new(0,0,Graphics.width,Graphics.height)
    @bgviewport.z=99999
    @viewport=Viewport.new(0,0,Graphics.width,Graphics.height)
    @viewport.z=99999
    @msgviewport=Viewport.new(0,0,Graphics.width,Graphics.height)
    @msgviewport.z=99999
    @pokemon=pokemon
    @newspecies=newspecies
    @sprites["background"]=REM_NoirPlane.new(@bgviewport)
    rsprite1=PokemonSprite.new(@viewport)
    rsprite2=PokemonSprite.new(@viewport)
    begin
      rsprite1.setPokemonBitmap(@pokemon,false)
    rescue
      rsprite1.bitmap=nil
    end
    begin     # un único fotograma (BitmapWrapperEX), no la tira entera de animación
      rsprite2.setSpeciesBitmap(@newspecies,@pokemon.isFemale?,(@pokemon.form rescue 0),
                                @pokemon.isShiny?,(@pokemon.isShadow? rescue false),false,@pokemon.isEgg?)
    rescue
      rsprite2.bitmap=nil
    end
    rsprite1.bitmap=Bitmap.new(2,2) if !rsprite1.bitmap || rsprite1.bitmap.disposed?
    rsprite2.bitmap=Bitmap.new(2,2) if !rsprite2.bitmap || rsprite2.bitmap.disposed?
    rsprite1.ox=rsprite1.bitmap.width/2
    rsprite1.oy=rsprite1.bitmap.height/2
    rsprite2.ox=rsprite2.bitmap.width/2
    rsprite2.oy=rsprite2.bitmap.height/2
    rsprite1.x=Graphics.width/2
    rsprite1.y=(Graphics.height-64)/2
    rsprite2.x=rsprite1.x
    rsprite2.y=rsprite1.y
    rsprite2.opacity=0
    @sprites["rsprite1"]=rsprite1
    @sprites["rsprite2"]=rsprite2
    pbGenerateMetafiles(rsprite1.ox,rsprite1.oy,rsprite2.ox,rsprite2.oy)
    @sprites["msgwindow"]=Kernel.pbCreateMessageWindow(@msgviewport)
    pbFadeInAndShow(@sprites) { pbUpdate }
  end
end

#===============================================================================
# RECORDADOR DE MOVIMIENTOS — lista de ranuras Oniria Noir + panel de detalle (diseño procedural)
#===============================================================================
module REM_UI
  NOIR_PANEL=Color.new(20,22,29)
  NOIR_ROW=Color.new(24,27,36)
  NOIR_SEL=Color.new(30,34,45)
  NOIR_WELL=Color.new(15,17,23)
  NOIR_WELLB=Color.new(38,43,56)
end

class MoveRelearnerScene
  def pbStartScene(pokemon,moves)
    @pokemon=pokemon
    @moves=moves
    moveCommands=[]
    moves.each{|i| moveCommands.push(PBMoves.getName(i)) }
    @viewport=Viewport.new(0,0,Graphics.width,Graphics.height)
    @viewport.z=99999
    @sprites={}
    @sprites["bg"]=REM_NoirPlane.new(@viewport)
    @sprites["overlay"]=BitmapSprite.new(Graphics.width,Graphics.height,@viewport)
    @sprites["pokeicon"]=PokemonIconSprite.new(@pokemon,@viewport)
    @sprites["pokeicon"].x=300
    @sprites["pokeicon"].y=4
    @sprites["pokeicon"].z=5
    @sprites["commands"]=Window_CommandPokemon.new(moveCommands,32)
    @sprites["commands"].x=Graphics.width
    @sprites["commands"].height=32*(VISIBLEMOVES+1)
    @sprites["msgwindow"]=Window_AdvancedTextPokemon.new("")
    @sprites["msgwindow"].visible=false
    @sprites["msgwindow"].viewport=@viewport
    @typebitmap=AnimatedBitmap.new(_INTL("Graphics/Pictures/types"))
    @catbitmap=AnimatedBitmap.new("Graphics/Pictures/category")
    pbDrawMoveList
    pbDeactivateWindows(@sprites)
    pbFadeInAndShow(@sprites) { pbUpdate }
  end

  def remBox(bmp,x,y,w,h,fill,border)
    REM_UI.slotBox(bmp,x,y,w,h,fill,border,1)
  end

  def pbDrawMoveList
    bmp=@sprites["overlay"].bitmap
    bmp.clear
    wh=REM_UI::WHITE; dm=REM_UI::DIM
    cmds=@sprites["commands"]
    # cabecera
    REM_UI.texts(bmp,[[:c,_INTL("¿Qué movimiento quieres que enseñe?"),16,24,0,wh,24,270]])
    t1=@pokemon.type1; t2=@pokemon.type2
    if t1==t2
      bmp.stretch_blt(Rect.new(440,12,52,23),@typebitmap.bitmap,Rect.new(0,t1*28,64,28))
    else
      bmp.stretch_blt(Rect.new(384,12,52,23),@typebitmap.bitmap,Rect.new(0,t1*28,64,28))
      bmp.stretch_blt(Rect.new(440,12,52,23),@typebitmap.bitmap,Rect.new(0,t2*28,64,28))
    end
    bmp.fill_rect(12,46,488,1,REM_UI::NOIR_WELLB)
    # lista
    remBox(bmp,12,54,244,318,REM_UI::NOIR_PANEL,REM_UI::SILVER)
    for i in 0...VISIBLEMOVES
      idx=cmds.top_item+i
      mv=@moves[idx]
      break if !mv
      y=62+i*76
      sel=(idx==cmds.index)
      remBox(bmp,20,y,228,70,sel ? REM_UI::NOIR_SEL : REM_UI::NOIR_ROW,sel ? REM_UI::SILVER : REM_UI::NOIR_WELLB)
      md=PBMoveData.new(mv)
      bmp.stretch_blt(Rect.new(28,y+8,56,24),@typebitmap.bitmap,Rect.new(0,md.type*28,64,28))
      REM_UI.texts(bmp,[[:c,PBMoves.getName(mv),94,y+20,0,wh,21,148]])
      bmp.stretch_blt(Rect.new(28,y+42,44,18),@catbitmap.bitmap,Rect.new(0,md.category*28,64,28))
      pw=md.basedamage<=1 ? (md.basedamage==1 ? "???" : "---") : sprintf("%d",md.basedamage)
      ac=md.accuracy==0 ? "---" : sprintf("%d",md.accuracy)
      REM_UI.texts(bmp,[[:c,_INTL("Pot. {1}",pw),82,y+51,0,sel ? W : dm,16,70],
                        [:c,_INTL("Prec. {1}",ac),150,y+51,0,sel ? W : dm,16,70],
                        [:c,_INTL("PP {1}",md.totalpp),240,y+20,1,sel ? W : dm,16,60]])
    end
    REM_UI.vArrow(bmp,134,48,-1,REM_UI::SILVER) if cmds.top_item>0
    REM_UI.vArrow(bmp,134,372,1,REM_UI::SILVER) if cmds.top_item+VISIBLEMOVES<@moves.length
    # panel de detalle
    cur=@moves[cmds.index]
    md=PBMoveData.new(cur)
    remBox(bmp,264,54,236,318,REM_UI::NOIR_PANEL,REM_UI::SILVER)
    REM_UI.texts(bmp,[[:c,PBMoves.getName(cur),276,76,0,wh,24,212]])
    bmp.stretch_blt(Rect.new(276,94,60,26),@typebitmap.bitmap,Rect.new(0,md.type*28,64,28))
    bmp.stretch_blt(Rect.new(344,94,60,26),@catbitmap.bitmap,Rect.new(0,md.category*28,64,28))
    stats=[[_INTL("POTENCIA"),md.basedamage<=1 ? (md.basedamage==1 ? "???" : "---") : sprintf("%d",md.basedamage)],
           [_INTL("PRECISIÓN"),md.accuracy==0 ? "---" : sprintf("%d",md.accuracy)],
           [_INTL("PP"),sprintf("%d",md.totalpp)]]
    for k in 0...3
      y=130+k*28
      remBox(bmp,276,y,212,24,REM_UI::NOIR_WELL,REM_UI::NOIR_WELLB)
      REM_UI.texts(bmp,[[:c,stats[k][0],284,y+12,0,dm,17,110],[:c,stats[k][1],480,y+12,1,wh,19,80]])
    end
    remBox(bmp,276,222,212,140,REM_UI::NOIR_WELL,REM_UI::NOIR_WELLB)
    desc=pbGetMessage(MessageTypes::MoveDescriptions,cur)
    REM_UI.fit(bmp,"x",999,18)
    lines=REM_UI.wrap(bmp,desc.to_s,196)
    for k in 0...[lines.length,6].min
      REM_UI.texts(bmp,[[:c,lines[k],284,236+k*20,0,wh,18,200]])
    end
  end

  def pbChooseMove
    oldcmd=-1
    pbActivateWindow(@sprites,"commands"){
       loop do
         oldcmd=@sprites["commands"].index
         Graphics.update
         Input.update
         pbUpdate
         pbDrawMoveList if @sprites["commands"].index!=oldcmd
         return 0 if Input.trigger?(Input::B)
         return @moves[@sprites["commands"].index] if Input.trigger?(Input::C)
       end
    }
  end

  def pbEndScene
    pbFadeOutAndHide(@sprites) { pbUpdate }
    pbDisposeSpriteHash(@sprites)
    @typebitmap.dispose
    @catbitmap.dispose
    @viewport.dispose
  end
end


# Centra un sprite por el rectángulo de su dibujo opaco (no por el fotograma) y lo reduce si excede maxw x maxh.
module REM_UI
  def self.spriteBounds(bitmap)
    w=bitmap.width; h=bitmap.height
    x0=w; y0=h; x1=-1; y1=-1
    for y in 0...h
      for x in 0...w
        if bitmap.get_pixel(x,y).alpha>16
          x0=x if x<x0; x1=x if x>x1
          y0=y if y<y0; y1=y if y>y1
        end
      end
    end
    return [0,0,w,h] if x1<0
    return [x0,y0,x1-x0+1,y1-y0+1]
  end

  def self.centerSprite(sprite,cx,cy,maxw,maxh)
    sprite.zoom_x=1.0; sprite.zoom_y=1.0
    return if !sprite.bitmap || sprite.bitmap.disposed?
    bb=spriteBounds(sprite.bitmap)
    z=[1.0,maxw*1.0/bb[2],maxh*1.0/bb[3]].min
    sprite.zoom_x=z; sprite.zoom_y=z
    sprite.x=(cx-(bb[0]+bb[2]/2.0)*z).round
    sprite.y=(cy-(bb[1]+bb[3]/2.0)*z).round
  end
end
