class MoveSelectionSprite < SpriteWrapper
  attr_reader :preselected
  attr_reader :index

  def initialize(viewport=nil,fifthmove=false)
    super(viewport)
    @movesel=AnimatedBitmap.new("Graphics/Pictures/summarymovesel")
    @frame=0
    @index=0
    @fifthmove=fifthmove
    @preselected=false
    @updating=false
    @spriteVisible=true
    refresh
  end

  def dispose
    @movesel.dispose
    super
  end

  def index=(value)
    @index=value
    refresh
  end

  def preselected=(value)
    @preselected=value
    refresh
  end

  def visible=(value)
    super
    @spriteVisible=value if !@updating
  end

  def refresh
    w=@movesel.width
    h=@movesel.height/2
    self.x=240
    self.y=92+(self.index*64)
    self.y-=76 if @fifthmove
    self.y+=20 if @fifthmove && self.index==4
    self.bitmap=@movesel.bitmap
    if self.preselected
      self.src_rect.set(0,h,w,h)
    else
      self.src_rect.set(0,0,w,h)
    end
  end

  def update
    @updating=true
    super
    @movesel.update
    @updating=false
    refresh
  end
end



class PokemonSummaryScene
  # REM_UI: valor de estadística o IV/EV según @remStatMode (0 actual, 1 IV/EV)
  def remStatText(pokemon,idx,val)
    return val if @remStatMode!=1
    return sprintf("IV %d / EV %d",pokemon.iv[idx],pokemon.ev[idx])
  end

  def pbPokerus(pkmn)
    return pkmn.pokerusStage
  end

  def pbUpdate
    pbUpdateSpriteHash(@sprites)
  end

  def pbStartScene(party,partyindex)
    @viewport=Viewport.new(0,0,Graphics.width,Graphics.height)
    @viewport.z=99999
    @party=party
    @partyindex=partyindex
    @pokemon=@party[@partyindex]
    @sprites={}
    @typebitmap=AnimatedBitmap.new(_INTL("Graphics/Pictures/types"))
    @sprites["background"]=IconSprite.new(0,0,@viewport)
    @sprites["overlay"]=BitmapSprite.new(Graphics.width,Graphics.height,@viewport)
    @sprites["pokemon"]=PokemonSprite.new(@viewport)
    @sprites["pokemon"].setPokemonBitmap(@pokemon)
    @sprites["pokemon"].mirror=false
    @sprites["pokemon"].color=Color.new(0,0,0,0)
    pbPositionPokemonSprite(@sprites["pokemon"],49,140)
    @sprites["pokeicon"]=PokemonBoxIcon.new(@pokemon,@viewport)
    @sprites["pokeicon"].x=14
    @sprites["pokeicon"].y=52
    @sprites["pokeicon"].mirror=false
    @sprites["pokeicon"].visible=false
    @sprites["movepresel"]=MoveSelectionSprite.new(@viewport)
    @sprites["movepresel"].visible=false
    @sprites["movepresel"].preselected=true
    @sprites["movesel"]=MoveSelectionSprite.new(@viewport)
    @sprites["movesel"].visible=false
    @page=0
    drawPageOne(@pokemon)
    pbFadeInAndShow(@sprites) { pbUpdate }
  end

  def pbStartForgetScene(party,partyindex,moveToLearn)
    @viewport=Viewport.new(0,0,Graphics.width,Graphics.height)
    @viewport.z=99999
    @party=party
    @partyindex=partyindex
    @pokemon=@party[@partyindex]
    @sprites={}
    @page=3
    @typebitmap=AnimatedBitmap.new(_INTL("Graphics/Pictures/types"))
    @sprites["background"]=IconSprite.new(0,0,@viewport)
    @sprites["overlay"]=BitmapSprite.new(Graphics.width,Graphics.height,@viewport)
    @sprites["pokeicon"]=PokemonBoxIcon.new(@pokemon,@viewport)
    @sprites["pokeicon"].x=14
    @sprites["pokeicon"].y=52
    @sprites["pokeicon"].mirror=false
    @sprites["movesel"]=MoveSelectionSprite.new(@viewport,moveToLearn>0)
    @sprites["movesel"].visible=false
    @sprites["movesel"].visible=true
    @sprites["movesel"].index=0
    drawSelectedMove(@pokemon,moveToLearn,@pokemon.moves[0].id)
    pbFadeInAndShow(@sprites)
  end

  def pbEndScene
    pbFadeOutAndHide(@sprites) { pbUpdate }
    pbDisposeSpriteHash(@sprites)
    @typebitmap.dispose
    @viewport.dispose
  end

  def drawMarkings(bitmap,x,y,width,height,markings)
    totaltext=""
    oldfontname=bitmap.font.name
    oldfontsize=bitmap.font.size
    oldfontcolor=bitmap.font.color
    bitmap.font.size=24
    bitmap.font.name="Arial"
    PokemonStorage::MARKINGCHARS.each{|item| totaltext+=item }
    totalsize=bitmap.text_size(totaltext)
    realX=x+(width/2)-(totalsize.width/2)
    realY=y+(height/2)-(totalsize.height/2)
    i=0
    PokemonStorage::MARKINGCHARS.each{|item|
       marked=(markings&(1<<i))!=0
       bitmap.font.color=(marked) ? Color.new(255,255,255) : Color.new(70,76,90)
       itemwidth=bitmap.text_size(item).width
       bitmap.draw_text(realX,realY,itemwidth+2,totalsize.height,item)
       realX+=itemwidth
       i+=1
    }
    bitmap.font.name=oldfontname
    bitmap.font.size=oldfontsize
    bitmap.font.color=oldfontcolor
  end

  def drawPageOneEgg(pokemon)
    overlay=@sprites["overlay"].bitmap
    overlay.clear
    @sprites["background"].setBitmap("Graphics/Pictures/summaryEgg")
    remDrawCard(pokemon,_INTL("NOTAS ENTRENADOR"),true)
    memo=""
    if pokemon.timeReceived
      month=pbGetAbbrevMonthName(pokemon.timeReceived.mon)
      date=pokemon.timeReceived.day
      year=pokemon.timeReceived.year
      memo+=_INTL("<c3=FFFFFF,0D0E12>{2} de {1} de {3}\n",month,date,year)
    end
    mapname=pbGetMapNameFromId(pokemon.obtainMap)
    if (pokemon.obtainText rescue false) && pokemon.obtainText!=""
      mapname=pokemon.obtainText
    end
    if mapname && mapname!=""
      memo+=_INTL("<c3=FFFFFF,0D0E12>Un extraño Huevo Pokémon hallado por la <c3=F5A524,0D0E12>{1}<c3=FFFFFF,0D0E12>.\n",mapname)
    end
    memo+="<c3=FFFFFF,0D0E12>\n"
    memo+=_INTL("<c3=FFFFFF,0D0E12>\"Estado del Huevo\"\n")
    eggstate=_INTL("Parece que a este Huevo le tomará mucho tiempo abrirse.")
    eggstate=_INTL("¿Qué saldrá? Aún le queda para abrirse.") if pokemon.eggsteps<10200
    eggstate=_INTL("A veces se mueve. Debería abrirse pronto.") if pokemon.eggsteps<2550
    eggstate=_INTL("Está haciendo ruidos. ¡Está a punto de abrirse!") if pokemon.eggsteps<1275
    memo+=sprintf("<c3=FFFFFF,0D0E12>%s\n",eggstate)
    pbSetNarrowFont(overlay)
    overlay.font.size=24
    REM_UI.fmtText(overlay,248,60,240,memo,28)
  end

  def drawPageTwo(pokemon)
    overlay=@sprites["overlay"].bitmap
    overlay.clear
    @sprites["background"].setBitmap("Graphics/Pictures/summary2")
    remDrawCard(pokemon,_INTL("NOTAS ENTRENADOR"))
    naturename=PBNatures.getName(pokemon.nature)
    memo=""
    shownature=(!(pokemon.isShadow? rescue false)) || pokemon.heartStage<=3
    if shownature
      memo+=_INTL("<c3=FFFFFF,0D0E12>Naturaleza <c3=F5A524,0D0E12>{1}<c3=FFFFFF,0D0E12>.\n",naturename)
    end
    if pokemon.timeReceived
      month=pbGetAbbrevMonthName(pokemon.timeReceived.mon)
      date=pokemon.timeReceived.day
      year=pokemon.timeReceived.year
      memo+=_INTL("<c3=FFFFFF,0D0E12>{2} de {1} de {3}\n",month,date,year)
    end
    mapname=pbGetMapNameFromId(pokemon.obtainMap)
    if (pokemon.obtainText rescue false) && pokemon.obtainText!=""
      mapname=pokemon.obtainText
    end
    if mapname && mapname!=""
      memo+=sprintf("<c3=F5A524,0D0E12>%s\n",mapname)
    else
      memo+=_INTL("<c3=F5A524,0D0E12>Faraway place\n")
    end
    if pokemon.obtainMode
      mettext=[_INTL("Encontrado con Nv. {1}.",pokemon.obtainLevel),
               _INTL("Huevo recibido."),
               _INTL("Intercambiado con Nv. {1}.",pokemon.obtainLevel),
               "",
               _INTL("Lo conocí en un encuentro fatídico en Nv. {1}.",pokemon.obtainLevel)
               ][pokemon.obtainMode]
      memo+=sprintf("<c3=FFFFFF,0D0E12>%s\n",mettext)
      if pokemon.obtainMode==1 # hatched
        if pokemon.timeEggHatched
          month=pbGetAbbrevMonthName(pokemon.timeEggHatched.mon)
          date=pokemon.timeEggHatched.day
          year=pokemon.timeEggHatched.year
          memo+=_INTL("<c3=FFFFFF,0D0E12>{2} de {1} de {3}\n",month,date,year)
        end
        mapname=pbGetMapNameFromId(pokemon.hatchedMap)
        if mapname && mapname!=""
          memo+=sprintf("<c3=F5A524,0D0E12>%s\n",mapname)
        else
          memo+=_INTL("<c3=F5A524,0D0E12>Faraway place\n")
        end
        memo+=_INTL("<c3=FFFFFF,0D0E12>Huevo eclosionado.\n")
      else
        memo+="<c3=FFFFFF,0D0E12>\n"
      end
    end
    if shownature
      bestiv=0
      tiebreaker=pokemon.personalID%6
      for i in 0...6
        if pokemon.iv[i]==pokemon.iv[bestiv]
          bestiv=i if i>=tiebreaker && bestiv<tiebreaker
        elsif pokemon.iv[i]>pokemon.iv[bestiv]
          bestiv=i
        end
      end
      characteristic=[_INTL("Le encanta comer."),       # Loves to eat
                      _INTL("A menudo se duerme."),     # Often dozes off
                      _INTL("Suele perder cosas."),     # Often scatters things
                      _INTL("A veces se enoja."),       # Scatters things often
                      _INTL("Le gusta relajarse."),     # Likes to relax
                      _INTL("Orgulloso de su fuerza."), # Proud of its power.
                      _INTL("Le gusta revolverse."),    # Likes to thrash about
                      _INTL("Un poco cabezota."),       # A little quick tempered
                      _INTL("Le gusta luchar."),        # Likes to fight
                      _INTL("Muy cabezota."),           # Quick tempered
                      _INTL("Cuerpo resistente."),      # Sturdy body
                      _INTL("Capaz de hacerlo solo."),  # Capable of taking hits
                      _INTL("Muy persistente."),        # Highly persistent
                      _INTL("Buen fajador."),           # Good endurance
                      _INTL("Muy perseverante."),       # Good perseverance
                      _INTL("Le gusta correr."),        # Likes to run
                      _INTL("Oído siempre alerta."),    # Alert to sounds
                      _INTL("Impetuoso y bobo."),       # Impetuous and silly
                      _INTL("Es un poco payaso."),      # Somewhat of a clown
                      _INTL("Huye rápido."),            # Quick to flee
                      _INTL("Muy curioso."),            # Highly curious
                      _INTL("Travieso."),               # Mischievous
                      _INTL("Muy astuto."),             # Thoroughly cunning
                      _INTL("A veces se distrae."),     # Often lost in thought
                      _INTL("Muy quisquilloso."),       # Very finicky
                      _INTL("Voluntarioso."),           # Strong willed
                      _INTL("Algo orgulloso."),         # Somewhat vain
                      _INTL("Muy insolente."),          # Strongly defiant
                      _INTL("Odia perder."),            # Hates to lose
                      _INTL("Tiene mal genio.")         # Somewhat stubborn
                      ][bestiv*5+pokemon.iv[bestiv]%5]
      memo+=sprintf("<c3=FFFFFF,0D0E12>%s\n",characteristic)
    end
    pbSetNarrowFont(overlay)
    overlay.font.size=24
    REM_UI.fmtText(overlay,248,60,240,memo,28)
  end

  def pbChooseMoveToForget(moveToLearn)
    selmove=0
    ret=0
    maxmove=(moveToLearn>0) ? 4 : 3
    loop do
      Graphics.update
      Input.update
      pbUpdate
      if Input.trigger?(Input::B)
        ret=4
        break
      end
      if Input.trigger?(Input::C)
        break
      end
      if Input.trigger?(Input::DOWN)
        selmove+=1
        if selmove<4 && selmove>=@pokemon.numMoves
          selmove=(moveToLearn>0) ? maxmove : 0
        end
        selmove=0 if selmove>maxmove
        @sprites["movesel"].index=selmove
        newmove=(selmove==4) ? moveToLearn : @pokemon.moves[selmove].id
        drawSelectedMove(@pokemon,moveToLearn,newmove)
        ret=selmove
      end
      if Input.trigger?(Input::UP)
        selmove-=1
        selmove=maxmove if selmove<0
        if selmove<4 && selmove>=@pokemon.numMoves
          selmove=@pokemon.numMoves-1
        end
        @sprites["movesel"].index=selmove
        newmove=(selmove==4) ? moveToLearn : @pokemon.moves[selmove].id
        drawSelectedMove(@pokemon,moveToLearn,newmove)
        ret=selmove
      end
    end
    return (ret==4) ? -1 : ret
  end

  def pbMoveSelection
    @sprites["movesel"].visible=true
    @sprites["movesel"].index=0
    selmove=0
    oldselmove=0
    switching=false
    drawSelectedMove(@pokemon,0,@pokemon.moves[selmove].id)
    loop do
      Graphics.update
      Input.update
      pbUpdate
      if @sprites["movepresel"].index==@sprites["movesel"].index
        @sprites["movepresel"].z=@sprites["movesel"].z+1
      else
        @sprites["movepresel"].z=@sprites["movesel"].z
      end
      if Input.trigger?(Input::B)
        break if !switching
        @sprites["movepresel"].visible=false
        switching=false
      end
      if Input.trigger?(Input::C)
        if selmove==4
          break if !switching
          @sprites["movepresel"].visible=false
          switching=false
        else
          if !(@pokemon.isShadow? rescue false)
            if !switching
              @sprites["movepresel"].index=selmove
              oldselmove=selmove
              @sprites["movepresel"].visible=true
              switching=true
            else
              tmpmove=@pokemon.moves[oldselmove]
              @pokemon.moves[oldselmove]=@pokemon.moves[selmove]
              @pokemon.moves[selmove]=tmpmove
              @sprites["movepresel"].visible=false
              switching=false
              drawSelectedMove(@pokemon,0,@pokemon.moves[selmove].id)
            end
          end
        end
      end
      if Input.trigger?(Input::DOWN)
        selmove+=1
        selmove=0 if selmove<4 && selmove>=@pokemon.numMoves
        selmove=0 if selmove>=4
        selmove=4 if selmove<0
        @sprites["movesel"].index=selmove
        newmove=@pokemon.moves[selmove].id
        pbPlayCursorSE()
        drawSelectedMove(@pokemon,0,newmove)
      end
      if Input.trigger?(Input::UP)
        selmove-=1
        if selmove<4 && selmove>=@pokemon.numMoves
          selmove=@pokemon.numMoves-1
        end
        selmove=0 if selmove>=4
        selmove=@pokemon.numMoves-1 if selmove<0
        @sprites["movesel"].index=selmove
        newmove=@pokemon.moves[selmove].id
        pbPlayCursorSE()
        drawSelectedMove(@pokemon,0,newmove)
      end
    end 
    @sprites["movesel"].visible=false
  end

  def pbGoToPrevious
    if @page!=0
      newindex=@partyindex
      while newindex>0
        newindex-=1
        if @party[newindex] && !@party[newindex].isEgg?
          @partyindex=newindex
          break
        end
      end
    else
      newindex=@partyindex
      while newindex>0
        newindex-=1
        if @party[newindex]
          @partyindex=newindex
          break
        end
      end
    end
  end

  def pbGoToNext
    if @page!=0
      newindex=@partyindex
      while newindex<@party.length-1
        newindex+=1
        if @party[newindex] && !@party[newindex].isEgg?
          @partyindex=newindex
          break
        end
      end
    else
      newindex=@partyindex
      while newindex<@party.length-1
        newindex+=1
        if @party[newindex]
          @partyindex=newindex
          break
        end
      end
    end
  end

  def pbScene
    pbPlayCry(@pokemon)
    loop do
      Graphics.update
      Input.update
      pbUpdate
      if Input.trigger?(Input::B)
        break
      end
      dorefresh=false
      if Input.trigger?(Input::C)
        if @page==0
          break
        elsif @page==2
          @remStatMode=(@remStatMode==1) ? 0 : 1
          dorefresh=true
        elsif @page==3
          pbMoveSelection
          dorefresh=true
          drawPageFour(@pokemon)
        end
      end
      if Input.trigger?(Input::A) && @page==2 && !@pokemon.isEgg?
        remAbilityModal(@pokemon)   # REM_UI: ficha flotante de habilidad
      end
      if Input.trigger?(Input::UP) && @partyindex>0
        oldindex=@partyindex
        pbGoToPrevious
        if @partyindex!=oldindex
          @pokemon=@party[@partyindex]
          @sprites["pokemon"].setPokemonBitmap(@pokemon)
          @sprites["pokemon"].color=Color.new(0,0,0,0)
          pbPositionPokemonSprite(@sprites["pokemon"],49,140)
          dorefresh=true
          pbPlayCry(@pokemon)
        end
      end
      if Input.trigger?(Input::DOWN) && @partyindex<@party.length-1
        oldindex=@partyindex
        pbGoToNext
        if @partyindex!=oldindex
          @pokemon=@party[@partyindex]
          @sprites["pokemon"].setPokemonBitmap(@pokemon)
          @sprites["pokemon"].color=Color.new(0,0,0,0)
          pbPositionPokemonSprite(@sprites["pokemon"],49,140)
          dorefresh=true
          pbPlayCry(@pokemon)
        end
      end
      if Input.trigger?(Input::LEFT) && !@pokemon.isEgg?
        oldpage=@page
        @page-=1
        @page=0 if @page<0
        @page=3 if @page>3
        dorefresh=true
        if @page!=oldpage # Move to next page
          pbPlayCursorSE()
          dorefresh=true
        end
      end
      if Input.trigger?(Input::RIGHT) && !@pokemon.isEgg?
        oldpage=@page
        @page+=1
        @page=0 if @page<0
        @page=3 if @page>3
        if @page!=oldpage # Move to next page
          pbPlayCursorSE()
          dorefresh=true
        end
      end
      if dorefresh
        case @page
        when 0
          drawPageOne(@pokemon)
        when 1
          drawPageTwo(@pokemon)
        when 2
          drawPageThree(@pokemon)
        when 3
          drawPageFour(@pokemon)
        end
      end
    end
    return @partyindex
  end
end



class PokemonSummary
  def initialize(scene)
    @scene=scene
  end

  def pbStartScreen(party,partyindex)
    @scene.pbStartScene(party,partyindex)
    ret=@scene.pbScene
    @scene.pbEndScene
    return ret
  end

  def pbStartForgetScreen(party,partyindex,moveToLearn)
    ret=-1
    @scene.pbStartForgetScene(party,partyindex,moveToLearn)
    loop do
      ret=@scene.pbChooseMoveToForget(moveToLearn)
      if ret>=0 && moveToLearn!=0 && pbIsHiddenMove?(party[partyindex].moves[ret].id) && !$DEBUG
        Kernel.pbMessage(_INTL("Los movimientos de MO no se pueden olvidar así.")){ @scene.pbUpdate }
      else
        break
      end
    end
    @scene.pbEndScene
    return ret
  end

  def pbStartChooseMoveScreen(party,partyindex,message)
    ret=-1
    @scene.pbStartForgetScene(party,partyindex,0)
    Kernel.pbMessage(message){ @scene.pbUpdate }
    loop do
      ret=@scene.pbChooseMoveToForget(0)
      if ret<0
        Kernel.pbMessage(_INTL("¡Debes elegir un movimiento!")){ @scene.pbUpdate }
      else
        break
      end
    end
    @scene.pbEndScene
    return ret
  end
end