#===============================================================================
#  The Trade Expert
#    by Luka S.J.
# 
#  Provides an emulated experience of Wonder Trade, but uses the base stat total
#  of a Pokemon species to determine which Pokemon you'll obtain from the trade.
#  Includes dialogues to make the event more interesting when trading your Pokemon.
#  To use, simply call it in an event via the script command:
#      tradeExpert(margin)
#  where margin is a percentage value (from 0.0 to 1.0) that determines the
#  increase in upper and lower base stat total values for the traded Pokemon.
#  By default, it is set to 0.1; meaning that the Pokemon you recieve will be
#  in the base stat total range of within 90% - 110% of the base stat total of
#  the Pokemon you're giving up for trade. The 'margin' parameter can be
#  omitted.
#  Look at the 'def tradePokemon' if you want to customize the Pokemon you're
#  getting from the trade even further.
#
#  Enjoy the script, and make sure to give credit!
#===============================================================================                             
# set up plugin metadata
=begin
if defined?(PluginManager)
  PluginManager.register({
    :name => "Trade Expert",
    :version => "1.1",
    :link => "https://luka-sj.com/res/trdex",
    :dependencies => [
      ["Luka's Scripting Utilities", "3.0"]
    ],
    :credits => ["Luka S.J."]
  })
else
  raise "This script is only compatible with Essentials v18.x!"
end
=end
#===============================================================================                             
#  Trade Expert (settings)
#===============================================================================                           
# A list of Pokemon you cannot obtain from the Trade Expert
TRADING_BLACKLIST = [
  :MEWTWO,
  :MEW,
  :ARTICUNO,
  :MOLTRES,
  :ZAPDOS,
  :ENTEI,
  :RAIKOU,
  :SUICUNE,
  :HOOH,
  :LUGIA,
  :REGICE,
  :REGISTEEL,
  :REGIROCK,
  :LATIAS,
  :LATIOS,
  :ROTOM,
  :KYOGRE,
  :GROUDON,
  :RAYQUAZA,
  :UXIE,
  :MESPRIT,
  :AZELF,
  :DARKRAI,
  :CRESSELIA,
  :HEATRAN,
  :PALKIA,
  :DIALGA,
  :GIRATINA,
  :REGIGIGAS,
  :MANAPHY,
  :PHIONE,
  :SHAYMIN,
  :VICTINI,
  :COBALION,
  :TERRAKION,
  :VIRIZION,
  :RESHIRAM,
  :ZEKROM,
  :KYUREM,
  :LANDORUS,
  :TORNADUS,
  :THUNDURUS,
  :MELOETTA,
  :XERNEAS,
  :YVELTAL,
  :ZYGARDE,
  :MAGEARNA,
  :TAPUBULU,
  :TAPULELE,
  :VOLCANION,
  :MARSHADOW,
  :TAPUFINI,
  :TAPUKOKO,
  :TYPENULL,
  :DIANCIE,
  :ZERAORA,
  :SILVALLY,
  :HOOPA,
  :CELESTEELA,
  :PHEROMOSA,
  :LUNALA,
  :SOLGALEO,
  :NIHILEGO,
  :COSMOG,
  :COSMOEM,
  :NECROZMA,
  :GUZZLORD,
  :BUZZWOLE,
  :XURKITREE,
  :GUZZLORD,
  :POIPOLE,
  :NAGANADEL,
  :CELEBI,
  :JIRACHI,
  :DEOXYS,
  :ARCEUS,
  :GENESECT,
  :AMAROWAK,
  :AEXEGGUTOR,
  :AMUK,
  :AGRIMER,
  :AGOLEM,
  :AGRAVELER,
  :AGEODUDE,
  :ADIGLETT,
  :ADUGTRIO,
  :APERSIAN,
  :AMEOWTH,
  :ANINETALES,
  :AVULPIX,
  :ASANDSLASH,
  :ASANDSHREW,
  :ARAICHU,
  :ARATICATE,
  :ARATTATA,
  :FAEMIE,
  :FAEMIE1,
  :FAEMIE2,
  :FAEMIE3,
  :CASTFORM,
  :MEGUMIN,
  :TARTAGLIA,
  :FAEMIEBICHITO
]
# A list of Pokemon you cannot give to the Trade Expert
GIVING_BLACKLIST = [
  :ARCEUS
]
# hash containing the spoken text
# add multiple entries as array to speak in sequence, or assign single message
# to each defined key
TRADE_EXPERT_TEXT = {
  # text when starting the event
  "intro" => [
    "¡Hola! Me gusta intercambiar Pokémon de todo tipo.",
    "Puedo ofrecer Pokémon de valor similar a los que tengas."
  ],
  # confirmation message from the expert
  "asktrade" => "¿Hay alguno que quieras cambiar? Igual tengo algo que te interese.",
  # rejection message if no mon for trade
  "invalid" => "No parece que tengas ningún Pokémon para mí.",
  # rejection if no offer found
  "notrade" => "¡Ese {1} es un Pokémon demasiado especial! No tengo nada de igual valor.",
  # thinking intermission
  "thinking" => "Mmm...\nMmm...",
  # trade options
  "trade0" => "Ese {1} es muy debilucho.",
  "trade1" => "Ese {1} no parece muy especial.",
  "trade2" => "Ese {1} no está muy mal.",
  "trade3" => "Ese {1} parece bastante interesante.",
  "trade4" => "¡Ese {1} sí que es un buen Pokémon!",
  "trade5" => "¡Ese {1}...! ¡Pero qué guapada de Pokémon!",
  # trade proposal
  "propose" => "¿Intercambiarías mi {1} por tu {2}?",
  # trade acceptance (player action)
  "accepttrade" => "Ha sido un placer hacer tratos contigo.",
  # trade rejection (player action)
  "rejecttrade" => [
    "Pensaba que era un intercambio justo. Qué sad.",
  ],
  # trade cancelled (player action)
  "canceltrade" => "Bueno... Avísame si cambias de opinión."
}
#===============================================================================        
# Main class for handling the Trade Expert
#-------------------------------------------------------------------------------
class TradeExpert
  #-----------------------------------------------------------------------------
  # starts up the Trade Expert
  #-----------------------------------------------------------------------------
  def initialize(margin = 0.1)
    # flavour text displaying a little intro for the Trade Expert
    if $game_switches[287]==true
        Kernel.pbMessage(_INTL("Igual podemos hacer otro trato algún día."))
        return false
    end
    self.displayMsg("intro")
    # confirmation for the trade
    if self.confirmMsg("asktrade")
      giveID = self.givePokemon
      return self.displayMsg("invalid") if giveID.nil?
      give = $Trainer.party[giveID]
      giveBST = calcBST(give)
      # protects trading from abuse
      if !$cachedTrade["#{giveBST}"].nil?
        recv = $cachedTrade["#{giveBST}"]
      else
        recv = self.fetchEqualSpecies(give,margin)
        # cancels the trade if the Trade Expert cannot offer you anything in return
        if recv.length < 1
          self.displayMsg("notrade", PBSpecies.getName(give.species))
          return false
        end
        recv = recv[rand(recv.length - 1)]
      end
      self.displayMsg("thinking")
      bst = calcBST(PokeBattle_Pokemon.new(recv,5))
      # flavour text displayed when evaluating the offered Pokemon species
      if bst <= 200
        self.displayMsg("trade0", PBSpecies.getName(give.species))
      elsif bst <= 300
        self.displayMsg("trade1", PBSpecies.getName(give.species))
      elsif bst <= 400
        self.displayMsg("trade2", PBSpecies.getName(give.species))
      elsif bst <= 500
        self.displayMsg("trade3", PBSpecies.getName(give.species))
      elsif bst <= 600
        self.displayMsg("trade4", PBSpecies.getName(give.species))
      else
        self.displayMsg("trade5", PBSpecies.getName(give.species))
      end
      # protects trading from abuse
      $cachedTrade["#{giveBST}"] = recv
      # final confirmation for the trade
      if self.confirmMsg("propose", PBSpecies.getName(recv), PBSpecies.getName(give.species))
        $cachedTrade.delete("#{giveBST}")
        self.tradePoke(giveID,recv)
        self.displayMsg("accepttrade")
        $game_switches[287]=true
        self.saveCache
        return true
      else
        self.displayMsg("rejecttrade")
        $game_switches[287]=true
        self.saveCache
        return false
      end
    else
      # the trade was cancelled at the start
      return self.displayMsg("canceltrade")
    end
  end
  #-----------------------------------------------------------------------------
  # method used to get a list of Pokemon you cannot get in a trade
  #-----------------------------------------------------------------------------
  def getBlacklist
    list = []
    for poke in TRADING_BLACKLIST
      if poke.is_a?(Numeric)
        list.push(poke)
      elsif poke.is_a?(Symbol)
        list.push(getConst(PBSpecies,poke))
      end
    end
    return list
  end
  #-----------------------------------------------------------------------------
  # method used to get a list of Pokemon you cannot give in a trade
  #-----------------------------------------------------------------------------
  def sendBlacklist
    list = []
    for poke in GIVING_BLACKLIST
      if poke.is_a?(Numeric)
        list.push(poke)
      elsif poke.is_a?(Symbol)
        list.push(getConst(PBSpecies,poke))
      end
    end
    return list
  end
  #-----------------------------------------------------------------------------
  # method used to calculate the base stat total of a Pokemon
  #-----------------------------------------------------------------------------
  def calcBST(poke)
    stats = poke.baseStats
    bst = 0
    for stat in stats
      bst += stat
    end
    return bst
  end
  #-----------------------------------------------------------------------------
  # method used to return a list of Pokemon that would be of similar value to your Pokemon
  #-----------------------------------------------------------------------------
  def fetchEqualSpecies(poke, margin = 0.1)
    bst = self.calcBST(poke)
    upper = bst*(1 + margin)
    lower = bst*(1 - margin)
    potential = []
    for i in 1..PBSpecies.maxValue
      spec = PokeBattle_Pokemon.new(i, 5)
      stats = self.calcBST(spec)
      potential.push(i) if stats >= lower && stats <= upper && !getBlacklist.include?(i) && i != poke.species
    end
    return potential
  end
  #-----------------------------------------------------------------------------
  # brings up the UI to select a Pokemon to give to the Trade Expert
  #-----------------------------------------------------------------------------
  def givePokemon
    # decides the parameters that determine Pokemon trade elegibility
    ableProc = proc{|poke| !poke.egg? && !poke.isShadow? && !sendBlacklist.include?(poke.species)}
    chosen = 0
    pbFadeOutIn(99999){
    scene = PokemonScreen_Scene.new
    screen = PokemonScreen.new(scene,$Trainer.party)
    if ableProc
      chosen = screen.pbChooseAblePokemon(ableProc,false)      
    else
      screen.pbStartScene(_INTL("Escoge un Pokémon."),false)
      chosen = screen.pbChoosePokemon
      screen.pbEndScene
    end
    }
    return (chosen >= 0 ? chosen : nil)
  end
  #-----------------------------------------------------------------------------
  # brings up the trading UI (you can further customize the traded Pokemon here)
  #-----------------------------------------------------------------------------
  def tradePoke(give, recv)
    myPokemon = $Trainer.party[give]
    # name of the Trade Expert is decided here
    opponent = PokeBattle_Trainer.new("Intercambista", 0)
    opponent.setForeignID($Trainer)
    # custom trainer ID of the Trade Expert
    opponent.id = 1204
    # generates the Pokemon
    yourPokemon = PokeBattle_Pokemon.new(recv, myPokemon.level, opponent)
    # sets the Pokemon's mode to be traded
    yourPokemon.obtainMode = 2
    # handles moves
    yourPokemon.resetMoves
    yourPokemon.pbRecordFirstMoves
    # registers Pokemon in the Pokedex
    $Trainer.seen[yourPokemon.species] = true
    $Trainer.owned[yourPokemon.species] = true
    pbSeenForm(yourPokemon)
    # starts trading sequence
    pbFadeOutInWithMusic(99999){
      evo = PokemonTradeScene.new
      evo.pbStartScreen(myPokemon,yourPokemon,$Trainer.name,opponent.name)
      evo.pbTrade
      evo.pbEndScreen
    }
    # sets traded Pokemon
    $Trainer.party[give] = yourPokemon
  end
  #-----------------------------------------------------------------------------
  # saves cached trades
  #-----------------------------------------------------------------------------
  def saveCache
    File.open(RTP.getSaveFileName("trexpert"),"wb"){|f|
       Marshal.dump($cachedTrade,f)
    }
  end
  #-----------------------------------------------------------------------------
  # display message
  #-----------------------------------------------------------------------------
  def displayMsg(msg, *args)
    msg = TRADE_EXPERT_TEXT[msg]
    msg = [msg] if !msg.is_a?(Array)
    for m in msg
      Kernel.pbMessage(_INTL(m, *args)) if m.is_a?(String)
    end
  end
  def confirmMsg(msg, *args)
    msg = TRADE_EXPERT_TEXT[msg]
    msg = [msg] if !msg.is_a?(Array)
    if msg.length > 1
      for m in msg[0...-1]
        Kernel.pbMessage(_INTL(m, *args)) if m.is_a?(String)
      end
    end
    return Kernel.pbConfirmMessage(_INTL(msg[-1], *args))
  end
  #-----------------------------------------------------------------------------
end
#-------------------------------------------------------------------------------
# Method used to call the Trade Expert in event
#-------------------------------------------------------------------------------
def tradeExpert(margin = 0.1)
  return TradeExpert.new(margin)
end
#-------------------------------------------------------------------------------
# Used so that the Player can't infinitely reject and get whatever new Pokemon
# before completing an old trade first
#-------------------------------------------------------------------------------
if safeExists?(RTP.getSaveFileName("trexpert"))
  File.open(RTP.getSaveFileName("trexpert")){|f|
    $cachedTrade = Marshal.load(f)
  }
else
  $cachedTrade = {}
end