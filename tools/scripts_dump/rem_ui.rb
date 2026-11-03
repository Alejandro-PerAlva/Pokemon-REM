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
    pr=pbPiaProg(sym); g=pbPiaGoals(sym)
    t=REM_PIA_TYPENAMES[REM_PIA_STARTERS[pbPiaIndex(sym)][1]]
    lines=[]
    for k in 0...4
      lines.push(sprintf("%s: %d/%d",sprintf(REM_PIA_KINDS[k],t),pr[k],g[k]))
    end
    return lines.join("\n")
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

module REM_UI
  STRIPE_W=5; STRIPE_Y0=2; STRIPE_Y1=52
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
  alias rem_orig_refresh refresh
  def refresh
    rem_orig_refresh
    return if !@battler || !@battler.pokemon
    foe=((@battler.index&1)==1)
    @remEdges=REM_UI.edges(@databox.bitmap,foe) if !@remEdges
    REM_UI.drawTypeStripe(self.bitmap,@remEdges,foe,[@battler.type1,@battler.type2])
  end
end

class FightMenuButtons
  alias rem_orig_refresh refresh
  def refresh(index,moves,megaButton,ultraButton)
    rem_orig_refresh(index,moves,megaButton,ultraButton)
    return if !moves
    pbSetSmallFont(self.bitmap)
    self.bitmap.font.size=18
    pbDrawTextPositions(self.bitmap,[[_INTL("Tecla D / Z: info"),448,UPPERGAP+72,2,
       REM_UI::SILVER,REM_UI::INK]])
    pbSetNarrowFont(self.bitmap)
  end
end

class PokeBattle_Scene
  def pbRemMoveInfo(move)
    vp=Viewport.new(0,0,Graphics.width,Graphics.height); vp.z=99999
    sp=BitmapSprite.new(320,140,vp)
    sp.x=40; sp.y=0   # arriba, desplazada a la izquierda para no tapar al rival
    bmp=sp.bitmap
    card=AnimatedBitmap.new("Graphics/Pictures/battleMoveInfo")
    bmp.blt(0,0,card.bitmap,Rect.new(0,0,320,140))
    card.dispose
    types=AnimatedBitmap.new(_INTL("Graphics/Pictures/types"))
    bmp.stretch_blt(Rect.new(250,5,58,24),types.bitmap,Rect.new(0,move.type*28,64,28))
    types.dispose
    pbSetSmallFont(bmp)
    cat=move.pbIsStatus? ? _INTL("Estado") : (move.pbIsPhysical?(move.type) ? _INTL("Físico") : _INTL("Especial"))
    pw=move.basedamage>0 ? move.basedamage.to_s : "—"
    ac=move.accuracy>0 ? move.accuracy.to_s : "—"
    base=Color.new(255,255,255); dim=REM_UI::SILVER; shadow=REM_UI::INK
    pbDrawTextPositions(bmp,[
      [move.name,12,3,0,base,shadow],
      [_INTL("{1}  Pot {2}  Prec {3}  PP {4}/{5}",cat,pw,ac,move.pp,move.totalpp),12,38,0,dim,shadow]])
    lines=REM_UI.wrap(bmp,pbGetMessage(MessageTypes::MoveDescriptions,move.id),296)
    lines=lines[0,3]
    textpos=[]
    for i in 0...lines.length
      textpos.push([lines[i],12,64+i*22,0,base,shadow])
    end
    pbDrawTextPositions(bmp,textpos)
    loop do
      Graphics.update; Input.update
      break if Input.trigger?(Input::Z) || Input.trigger?(Input::B) || Input.trigger?(Input::C)
    end
    sp.bitmap.dispose; sp.dispose; vp.dispose
  end
end
