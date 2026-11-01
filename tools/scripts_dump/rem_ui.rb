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
# COMBATE: iconos de tipo en las cajas de datos + info completa del movimiento
#===============================================================================
class PokemonDataBox
  alias rem_orig_refresh refresh
  def refresh
    rem_orig_refresh
    return if !@battler || !@battler.pokemon
    @@remTypeBmp=AnimatedBitmap.new(_INTL("Graphics/Pictures/types")) if !defined?(@@remTypeBmp)
    types=[@battler.type1,@battler.type2].uniq
    x=@spritebaseX+102
    for t in types
      next if !t || t<0
      self.bitmap.stretch_blt(Rect.new(x,24,30,13),@@remTypeBmp.bitmap,Rect.new(0,t*28,64,28))
      x+=33
    end
  end
end

class PokeBattle_Scene
  def pbRemMoveInfo(move)
    vp=Viewport.new(0,0,Graphics.width,Graphics.height); vp.z=99999
    sp=BitmapSprite.new(Graphics.width-32,230,vp)
    sp.x=16; sp.y=Graphics.height-96-46-230+40
    bmp=sp.bitmap
    bmp.fill_rect(0,0,sp.bitmap.width,230,Color.new(16,20,36))
    bmp.fill_rect(3,3,sp.bitmap.width-6,224,Color.new(44,52,84))
    pbSetSystemFont(bmp)
    cat=move.pbIsStatus? ? _INTL("Estado") : (move.pbIsPhysical?(move.type) ? _INTL("Físico") : _INTL("Especial"))
    pw=move.basedamage>0 ? move.basedamage.to_s : "—"
    ac=move.accuracy>0 ? move.accuracy.to_s : "—"
    base=Color.new(248,248,248); shadow=Color.new(64,64,80)
    pbDrawTextPositions(bmp,[
      [move.name,14,8,0,base,shadow],
      [_INTL("Categoría: {1}",cat),14,40,0,base,shadow],
      [_INTL("Potencia: {1}",pw),14,66,0,base,shadow],
      [_INTL("Precisión: {1}",ac),200,66,0,base,shadow],
      [_INTL("PP: {1}/{2}",move.pp,move.totalpp),360,66,0,base,shadow],
      [_INTL("D / B: cerrar"),sp.bitmap.width-12,8,1,Color.new(200,200,216),shadow]])
    bmp.blt(sp.bitmap.width-90,36,AnimatedBitmap.new(_INTL("Graphics/Pictures/types")).bitmap,Rect.new(0,move.type*28,64,28))
    drawTextEx(bmp,14,100,sp.bitmap.width-28,5,pbGetMessage(MessageTypes::MoveDescriptions,move.id),base,shadow)
    loop do
      Graphics.update; Input.update
      break if Input.trigger?(Input::Z) || Input.trigger?(Input::B) || Input.trigger?(Input::C)
    end
    sp.dispose; vp.dispose
  end
end
