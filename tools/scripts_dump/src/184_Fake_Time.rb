#===============================================================================
# * Unreal time system - by FL (Credits will be apreciated)
#===============================================================================
#
# This script is for Pokémon Essentials. It makes the time in game have its
# own clock that only pass when you are in game instead of using real time
# (like Harvest Moon and Zelda: Ocarina of Time).
#
#===============================================================================
#
# To this script works, put it above main. If you wish to some parts still use
# real time like the Trainer Card start time and Pokémon Trainer Memo, 
# just change 'pbGetTimeNow' to 'Time.now' in their scripts (in this example, 
# PokemonMap and PokeBattle_Pokemon scripts sections).
#
# This script use the Ruby Time class that can only hold years around 
# 1970-2038 range. If you wish to have other years values, sum/subtract when
# displaying the year. Examples: 
# If you wants year 1000, start in 1970 and, when displaying year name use 
# 'pbGetTimeNow.year-970'. 
# If you wants year 5000, start in 1970 and, when displaying year name use 
# 'pbGetTimeNow.year+3030'.
# 
# Some time methods:
# 'pbGetTimeNow.year', 'pbGetTimeNow.mon' (the numbers from 1-12), 
# 'pbGetTimeNow.day','pbGetTimeNow.hour', 'pbGetTimeNow.min', 
# 'pbGetTimeNow.sec', 'pbGetAbbrevMonthName(pbGetTimeNow.mon)',
# 'pbGetTimeNow.strftime("%A")' (displays weekday name),
# 'pbGetTimeNow.strftime("%I:%M %p")' (displays Hours:Minutes pm/am)
# 
#===============================================================================

# Set false to disable this system (returns Time.now)
$ntnEnabled=true
#NTN_ENABLED=true 

# Make this true to time only pass at field (Scene_Map) 
# A note to scripters: To make time pass on other scenes, put line
# '$PokemonGlobal.addNewFrameCount' near to line 'Graphics.update'
NTN_TIMESTOPS=true 

# Make this true to time pass in battle, during turns and command selection.
# This won't affect the Pokémon and Bag submenus.
# Only works if NTN_TIMESTOPS=true.
NTN_BATTLEPASS=false

# Make this true to time pass when the Dialog box or the main menu are open.
# This won't affect the submenus like Pokémon and Bag.
# Only works if NTN_TIMESTOPS=true.
NTN_TALKPASS=false

# Time proportion here. 
# So if it is 100, one second in real time will be 100 seconds in game.
# If it is 60, one second in real time will be one minute in game.
NTS_TIMEPROPORTION=60

# Choose switch number that when true the time won't pass (or -1 to cancel). 
# Only works if NTN_TIMESTOPS=true.
NTN_SWITCHSTOPS=84

# Choose variable(s) number(s) that can hold time passage (or -1 to cancel).
# The time in this variable isn't affected by NTS_TIMEPROPORTION.
# Example: When the player sleeps you wish to the time in game advance
# 8 hours, so put in NTN_EXTRASECONDS a game variable number and sum 
# 28800 (60*60*8) in this variable every time that the players sleeps.
# 1 hora = 3600
# 1 cuarto de hora = 900
# 1 minuto = 60
NTN_EXTRASECONDS=46#-1
NTN_EXTRADAYS=75#-1

# Initial values
#NTN_INITIALYEAR=2000 # Can ONLY holds around range 1970-2038
#NTN_INITIALMONTH=1
#NTN_INITIALDAY=1
#NTN_INITIALHOUR=12
#NTN_INITIALMINUTE=0

NTN_INITIALYEAR=pbGetTimeNow.year # Can ONLY holds around range 1970-2038
NTN_INITIALMONTH=pbGetTimeNow.mon
NTN_INITIALDAY=pbGetTimeNow.day
NTN_INITIALHOUR=12#pbGetTimeNow.hour
NTN_INITIALMINUTE=30#pbGetTimeNow.min

def pbGetTimeNow
  return Time.now if !$ntnEnabled#NTN_ENABLED
  
  if(NTN_TIMESTOPS)
    # Sum the extra values to newFrameCount
    if(NTN_EXTRASECONDS>0)
      $PokemonGlobal.newFrameCount+=(
        pbGet(NTN_EXTRASECONDS)*40)/NTS_TIMEPROPORTION
      $game_variables[NTN_EXTRASECONDS]=0
    end  
    if(NTN_EXTRADAYS>0)
      $PokemonGlobal.newFrameCount+=((60*60*24)*
        pbGet(NTN_EXTRADAYS)*40)/NTS_TIMEPROPORTION
      $game_variables[NTN_EXTRADAYS]=0
    end
  elsif(NTN_EXTRASECONDS>0 && NTN_EXTRADAYS>0)
    # Checks to regulate the max/min values at NTN_EXTRASECONDS
    while (pbGet(NTN_EXTRASECONDS)>=(60*60*24))
      $game_variables[NTN_EXTRASECONDS]-=(60*60*24)
      $game_variables[NTN_EXTRADAYS]+=1
    end
    while (pbGet(NTN_EXTRASECONDS)<=-(60*60*24))
      $game_variables[NTN_EXTRASECONDS]+=(60*60*24)
      $game_variables[NTN_EXTRADAYS]-=1
    end  
  end  
  start_time=Time.utc(NTN_INITIALYEAR,NTN_INITIALMONTH,NTN_INITIALDAY,
    NTN_INITIALHOUR,NTN_INITIALMINUTE)
  time_played=(NTN_TIMESTOPS && $PokemonGlobal) ? 
    $PokemonGlobal.newFrameCount : Graphics.frame_count
  time_played=(time_played*NTS_TIMEPROPORTION)/40
  time_jumped=0
  time_jumped+=pbGet(NTN_EXTRASECONDS) if NTN_EXTRASECONDS>-1 
  time_jumped+=pbGet(NTN_EXTRADAYS)*(60*60*24) if NTN_EXTRADAYS>-1 
  time_ret = nil
  # To prevent crashes due to year limit, every time that you reach in year 
  # 2036 the system will subtract 6 years (to works with leap year) from
  # your date and sum in $PokemonGlobal.extraYears. You can sum your actual
  # year with this extraYears when displaying years.
  loop do
    extraYears=($PokemonGlobal) ? $PokemonGlobal.extraYears : 0
    time_fix=extraYears*60*60*24*(365*6+1)/6
    time_ret=start_time+(time_played+time_jumped-time_fix)
    break if time_ret.year<2036
    $PokemonGlobal.extraYears+=6
  end
  return time_ret
end

if $ntnEnabled#NTN_ENABLED
  class PokemonGlobalMetadata
    attr_accessor :newFrameCount
    attr_accessor :extraYears 
    
    def addNewFrameCount
      self.newFrameCount+=1 if !(
        NTN_SWITCHSTOPS>0 && $game_switches[NTN_SWITCHSTOPS])
    end
    
    def newFrameCount
      @newFrameCount=0 if !@newFrameCount
      return @newFrameCount
    end
    
    def extraYears
      @extraYears=0 if !@extraYears
      return @extraYears
    end
  end  

  if NTN_TIMESTOPS  
    class Scene_Map
      alias :updateold :update
    
      def update
        $PokemonGlobal.addNewFrameCount
        updateold
      end
    
      if NTN_TALKPASS  
        alias :miniupdateold :miniupdate
        
        def miniupdate
          $PokemonGlobal.addNewFrameCount 
          miniupdateold
        end
      end
    end  
  
    if NTN_BATTLEPASS
      class PokeBattle_Scene
        alias :pbGraphicsUpdateold :pbGraphicsUpdate
        
        def pbGraphicsUpdate
          $PokemonGlobal.addNewFrameCount 
          pbGraphicsUpdateold
        end
      end
    end
  end
end
#Method to skip to a certain hour 
#Copied from a post FL made, so no credits to me
#I just did this in a blank section above main
def skipToHour(hour) 
# Hour is the desired hour in a range of 0 and 23, so 6 its 6 a.m and 18 6 p.m
 if(NTN_EXTRASECONDS>0) 
 min = 0
 sec = 0
 timeNow = pbGetTimeNow
 secInDay = 60*60*24
 secNow = pbGetTimeNow.hour*60*60+pbGetTimeNow.min*60+pbGetTimeNow.sec
 secWished = hour*60*60+min*60+sec
 secondsAdded = secWished-secNow
 secondsAdded +=secInDay if secondsAdded<0
 $game_variables[NTN_EXTRASECONDS]+=secondsAdded
 $game_map.need_refresh = true
 end
end

def timeInText
 Kernel.pbMessage(_INTL("Son las {2}. ¡A aprovechar el día!",
 pbGetTimeNow.strftime("%A"),pbGetTimeNow.strftime("%I:%M %p")))
end

#===============================================================================
# Month Reset
# Allows you to reset the current month to a different one.
# Requires FL's Unreal Time System script, found here:
#===============================================================================
# http://www.pokecommunity.com/showthread.php?p=7283916#7283916
#===============================================================================
# Use pbTimeCheck in an event to check the current date and time.
# Use pbResetDay in an event to change the day to the first of the month.
# Use pbSetMonth in an event to select a new month to set the time to.

# Use so you may check the current date and time.
# Useful way to check if the time has been properly set.
def pbTimeCheck
  curmon=pbGetAbbrevMonthName(pbGetTimeNow.mon)
  curday=pbGetTimeNow.day
  curyear=pbGetTimeNow.year
  curhour=pbGetTimeNow.hour
  curmin=pbGetTimeNow.min
  Kernel.pbMessage(_INTL("{1} {2}\nHora: {4}:{5}",#(_INTL("Date: {1} {2}, {3}\nTime: {4}:{5}",
  curmon,curday,curyear,curhour,curmin))
end

# Used to reset the current day to the first of the month.
# Months may be off by a few days otherwise.
def pbResetDay
  curDay = pbGetTimeNow.day
  timeDifference = (1-curDay)
  setToFirst = timeDifference
  $game_variables[NTN_EXTRADAYS]+=setToFirst
  Kernel.pbMessage(_INTL("The current day has been reset to the first of the month."))
end

# Allows you to choose the desired month to switch to. The day is reset to
# the first day of the newly selected month.
# Use the "Reset" option at the bottom of the list to revert the month and
# day to its natural time.
def pbSetMonth
  curMonth = pbGetTimeNow.mon*30
  curDay = pbGetTimeNow.day
  timeNow = curMonth+curDay
  command=0
  loop do
    command=Kernel.pbShowCommands(nil,[
    _INTL("Enero"),
    _INTL("Febrero"),
    _INTL("Marzo"),
    _INTL("Abril"),
    _INTL("Mayo"),
    _INTL("Junio"),
    _INTL("Julio"),
    _INTL("Augosto"),
    _INTL("Septiembre"),
    _INTL("Octubre"),
    _INTL("Noviembre"),
    _INTL("Diciembre"),
    _INTL("Reset"),
    _INTL("Cancel")
    ],-1)
    case command
    ### Cancel ###
    when -1, 13
      Kernel.pbMessage(_INTL("The current date was not changed."))
      break
    ### Jan ###
    when 0
      month = 1
      timeWished = month*30
      timeDifference = timeWished-timeNow
      monthSet = timeDifference
      $game_variables[NTN_EXTRADAYS]+=monthSet
      Kernel.pbMessage(_INTL("The month has been set to January."))
      pbResetDay
      break
    ### Feb ###
    when 1
      month = 2
      timeWished = month*31
      timeDifference = timeWished-timeNow
      monthSet = timeDifference
      $game_variables[NTN_EXTRADAYS]+=monthSet
      Kernel.pbMessage(_INTL("The month has been set to February."))
      pbResetDay
      break
    ### Mar ###
    when 2
      month = 3
      timeWished = month*31
      timeDifference = timeWished-timeNow
      monthSet = timeDifference
      $game_variables[NTN_EXTRADAYS]+=monthSet
      Kernel.pbMessage(_INTL("The month has been set to March."))
      pbResetDay
      break
    ### Apr ###
    when 3
      month = 4
      timeWished = month*31
      timeDifference = timeWished-timeNow
      monthSet = timeDifference
      $game_variables[NTN_EXTRADAYS]+=monthSet
      Kernel.pbMessage(_INTL("The month has been set to April."))
      pbResetDay
      break
    ### May ###
    when 4
      month = 5
      timeWished = month*31
      timeDifference = timeWished-timeNow
      monthSet = timeDifference
      $game_variables[NTN_EXTRADAYS]+=monthSet
      Kernel.pbMessage(_INTL("The month has been set to May."))
      pbResetDay
      break
    ### Jun ###
    when 5
      month = 6
      timeWished = month*31
      timeDifference = timeWished-timeNow
      monthSet = timeDifference
      $game_variables[NTN_EXTRADAYS]+=monthSet
      Kernel.pbMessage(_INTL("The month has been set to June."))
      pbResetDay
      break
    ### Jul ###
    when 6
      month = 7
      timeWished = month*31
      timeDifference = timeWished-timeNow
      monthSet = timeDifference
      $game_variables[NTN_EXTRADAYS]+=monthSet
      Kernel.pbMessage(_INTL("The month has been set to July."))
      pbResetDay
      break
    ### Aug ###
    when 7
      month = 8
      timeWished = month*31
      timeDifference = timeWished-timeNow
      monthSet = timeDifference
      $game_variables[NTN_EXTRADAYS]+=monthSet
      Kernel.pbMessage(_INTL("The month has been set to August."))
      pbResetDay
      break
    ### Sep ###
    when 8
      month = 9
      timeWished = month*31
      timeDifference = timeWished-timeNow
      monthSet = timeDifference
      $game_variables[NTN_EXTRADAYS]+=monthSet
      Kernel.pbMessage(_INTL("The month has been set to September."))
      pbResetDay
      break
    ### Oct ###
    when 9
      month = 10
      timeWished = month*31
      timeDifference = timeWished-timeNow
      monthSet = timeDifference
      $game_variables[NTN_EXTRADAYS]+=monthSet
      Kernel.pbMessage(_INTL("The month has been set to October."))
      pbResetDay
      break
    ### Nov ###
    when 10
      month = 11
      timeWished = month*31
      timeDifference = timeWished-timeNow
      monthSet = timeDifference
      $game_variables[NTN_EXTRADAYS]+=monthSet
      Kernel.pbMessage(_INTL("The month has been set to November."))
      pbResetDay
      break
    ### Dec ###
    when 11
      month = 12
      timeWished = month*31
      timeDifference = timeWished-timeNow
      monthSet = timeDifference
      $game_variables[NTN_EXTRADAYS]+=monthSet
      Kernel.pbMessage(_INTL("The month has been set to December."))
      pbResetDay
      break
    ### Reset ###
    when 12
      $game_variables[NTN_EXTRADAYS] = 0
      $PokemonGlobal.newFrameCount=0
      Kernel.pbMessage(_INTL("The time has been reset to the current date."))
      break
    end
  end
end



