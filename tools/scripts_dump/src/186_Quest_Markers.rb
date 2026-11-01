#========================================================
#         Drago2308's Quest Marker Script
#                 7-7-2014
#               Version 1.2 updated 12-7-2014
#========================================================
#     Version History:
#     v1.0 Initial Release
#     v1.1 Fixed a few major bugs, and enhanced flicker effect
#     v1.1.2 Adding some code to try and dispose of sprites correctly
#     v1.2 Fixed huge bugs present in the earlier releases, disposing is
#     much more thurogh all thanks to black mage. also cleaned up the script
#     a bit. Also less lag when more sprites are present on the screen again
#     thanks to black mage for implementing that dispose correctly.
#----------------------------------------------------------
#     Compatibility:
#     No problems when running alongside all the scripts
#     present in my current game 30+
#----------------------------------------------------------
#     Instructions:
#    
#     Whenever you want to create a quest marker on an event
#     you must make the first line of the event a comment with
#     it saying "quest_marker" << this is the key word to call the script.
#    
#     The comments have a syntax as follows.
#     quest_marker filename
#     opacity
#     bouncing
#     flashing
#
#---------------------------------------------------------
#     Parameters:
#    
#     filename : Is the picture to be shown (usually red,blue,green,yellow) Default blue
#     opacity  : Sprites Opacity 255-0 255 = fully opaque 0 = transparent
#     bouncing : Type true if you want the quest marker to bounce
#     flashing : Type true if you want the quest marker to flash
#
#---------------------------------------------------------
#     Example:
#     A working example would look like the following
#    
#     quest_marker blue
#     255
#     true
#     false
#
#     This will result in a blue marker, fully opaque and bouncing
#---------------------------------------------------------
#   Tips:
#   You can use multiple event pages to update the markers
#   properties in real time, so you can turn on and off bounce
#   or change the color from blue to yellow for in progress quests
#   and yellow to green for finished quests.
#---------------------------------------------------------
#   Known Issues:
#   None, Find any tell me ok?
#---------------------------------------------------------
#     Notes:
#     Have any questions or suggestions feel free to contact me
#     drago2308@hotmail.com
#     http://www.gdunlimited.net/  search for drago2308
#---------------------------------------------------------
#   Special Thanks:
#   Just would give a huge thanks to black mages contribution to this
#   script as it certainly helped fix the huge bugs that this script
#   used to have. So thank you.
#---------------------------------------------------------
#OMG 68 lines of comments lol
 
 
#=========================================================
# **Sprite_Quest_Marker
#---------------------------------------------------------
#   Displays the marker
#=========================================================
 
class Quest_Marker < Sprite
  #-------------------------------------------------------
  #   * Constants
  #-------------------------------------------------------
  #Defuault Sprite
  DEFAULT = 'blue'
  #Sprites Width
  MARKER_X = 30
  #Sprites Height
  MARKER_Y = 30
  #If you want to change the defualt height of the marker you can do so here. (Defualt = 44)
  HEIGHT = 22
  #Desplazamiento extra de X
  EXTRA_X = 17
  #How many frames to wait before updating - Lower the more lag, higher makes updating slow
  FRAME_SKIP = 2
  #How many seconds for the sprite to update on screen (Default = 1) Used for bounce animation
  UPDATE = 1
  #Speed of which the flash effect flashes - The higher the faster the flash (Default = 4)
  FLASHSP = 4
 
 
  #------------------------------------------------------
  #   * Public instance variables
  #------------------------------------------------------
  attr_accessor :event
  attr_accessor :sprite
 
  #------------------------------------------------------
  #   * Initialize
  #------------------------------------------------------
  def initialize(event, opacity, bounce, flash, filename)
    super()
    #Sprite variable
    @sprite = Sprite.new
    #How far forward the sprite is
    @sprite.z = 1
    #Sprites Opacity
    @sprite.opacity = opacity
    #Set Sprite to be visible
    @sprite.visible = true
    #Set sprites X co-ordinate (gets events location)
    @sprite.x = (event.real_x - MARKER_Y - MARKER_X - $game_map.display_x) / 4 + EXTRA_X
    #Set sprites Y co-ordinate (gets events location)
    @sprite.y = (event.real_y - MARKER_Y - MARKER_X - $game_map.display_y) / 4 - HEIGHT
    #Cache sprite (filename)
    bmp = filename == nil ? RPG::Cache.picture(DEFAULT) : RPG::Cache.picture(filename)
    #create the bitmap area
    @sprite.bitmap = Bitmap.new(MARKER_X, MARKER_Y)
    #Create bitmap rectangle
    @sprite.bitmap.stretch_blt(Rect.new(0, 0, MARKER_X, MARKER_Y), bmp, bmp.rect)
    #Create Global variables from local ones
    @visible = visible
    @filename = filename
    @event = event
    @count = 0
    @bounce = bounce
    @flash = flash
    @bouncecount = 0
    @bouncetoggle = false
    @dispcount = 0
    @flashcount = 0
    @flashtoggle = true
  end
 
  #-------------------------------------------------------------
  #   * Update Frame
  #-------------------------------------------------------------
  def update
    # add one to count every time this loops
    @count += 1
    #update bounce effect
    if @bounce    
      #check to see if bounce count = +-12px and turn toggle on or off
      if @bouncecount == 2
        @bouncetoogle = 0
        @bouncetoggle = false
      end    
      if @bouncecount == -2
        @bouncecount = 0
        @bouncetoggle = true
      end    
      #count up and down depending on toggle state
      if @bouncetoggle
        @bouncecount -= 1
      else
        @bouncecount += 1
      end
      #update sprites position with new co-ord (with @bouncecount for bounce effect)
      @sprite.x = (@event.real_x - (MARKER_X + MARKER_Y).to_f * self.zoom_x - $game_map.display_x) / 4 + EXTRA_X
      @sprite.y = (@event.real_y - (MARKER_X + MARKER_Y).to_f * self.zoom_y - $game_map.display_y) / 4 - (HEIGHT + @bouncecount.to_f / 4)          
      #For compatibility with bounce effect
      if @flash
        #count for flash count
        @flashcount += 1
        #at half the amount of UPDATE in seconds sprite will become invisible
        if @flashcount == (UPDATE * 40) / FLASHSP
          if @flashtoggle == true
            #Make sprite invisible
            @sprite.visible = false
            #toggle
            @flashtoggle = false
          else
            #Make sprite visible
            @sprite.visible = true
            #toggle
            @flashtoggle = true
          end
        #reset flash count
        @flashcount = 0
        end      
      end
      #------------------------------------------------------------
      #   * Default Update when no effects are active
      #------------------------------------------------------------
    else
      #if flash is activated
      if @flash
        #count for flash count
        @flashcount += 1
        #update sprites position on map
        @sprite.x = (@event.real_x - (MARKER_X + MARKER_Y).to_f * self.zoom_x - $game_map.display_x) / 4 + EXTRA_X
        @sprite.y = (@event.real_y - (MARKER_X + MARKER_Y).to_f * self.zoom_y - $game_map.display_y) / 4 - HEIGHT
        #Flash for flash speed
        if @flashcount == (UPDATE * 40) / FLASHSP
          if @flashtoggle == true
            #Make sprite invisible
            @sprite.visible = false
            #
            @flashtoggle = false
          else
            @sprite.visible = true
            @flashtoggle = true
          end      
        #reset flash count
        @flashcount = 0
        end      
      end                
      #------------------------------------------------------------
      #   * Default Update when no effects are active
      #------------------------------------------------------------
      #check to see if count = frame skip (Defualt = 2) and updates the markers posision on the screen
      if self.sprite != nil
      if @count == FRAME_SKIP
        @sprite.x = (@event.real_x - (MARKER_X + MARKER_Y).to_f * self.zoom_x - $game_map.display_x) / 4 + EXTRA_X
        @sprite.y = (@event.real_y - (MARKER_X + MARKER_Y).to_f * self.zoom_y - $game_map.display_y) / 4 - HEIGHT
        #reset count to 0
        @count = 0
      end      
      end
    end
    #add one to dispose count every loop
    @dispcount += 1  
    #check to see if dispose count is equal to 1 second and dispose of the sprite if neccicary
    if @dispcount == (UPDATE * 40)
      @dispcount = 0
      self.sprite.bitmap.dispose
    end
  end
end
 
class Spriteset_Map
 
  #---------------------------------------------------------------------------
  # * Constants
  #---------------------------------------------------------------------------
    #Time to update sprite image (seconds)
    UPDATE = 1
  #----------------------------------------------------------------------------
  # * Method Aliases
  #----------------------------------------------------------------------------
  unless self.method_defined?(:new_quest_marker_init)
    alias :new_quest_marker_init :initialize
  end
  unless self.method_defined?(:new_quest_marker_updt)
    alias :new_quest_marker_updt :update
  end
  unless self.method_defined?(:new_quest_marker_disp)
    alias :new_quest_marker_disp :dispose
  end
 
 
  #----------------------------------------------------------------------------
  # * Object Initialization
  #----------------------------------------------------------------------------
  def initialize(map=nil)
    #initialize global variables
    @quest_marker = []
    @count = 0
    @countnew = 0
    #call render_marker method
    render_quest_marker    
    new_quest_marker_init(map)
  end
  #----------------------------------------------------------------------------
  # * Update Frame
  #----------------------------------------------------------------------------
  def update
    # Run calling of each screen
    if Input.trigger?(Input::B)
      # If event is running, or menu is not forbidden
      unless $game_system.map_interpreter.running? or
             $game_system.menu_disabled or
             $game_temp.message_window_showing
             # Set menu calling flag or beep flag
             black_dispose
             @count = (UPDATE * 40) - 5
      end
    end
    unless $game_player.moving?
      if $game_temp.menu_calling
        black_dispose
        @count = (UPDATE * 40) - 5
      end
    end
    # update the quest marker if sprite actualy exitst
    @quest_marker.each {|quest| if quest.sprite != nil
                        quest.update
                        end}
    #add 1 to count per update cycle
    @count += 1
    #check to see if count = update (in seconds)
    if @count == UPDATE * 40
      #call render_quest_marker method
      render_quest_marker
      #reset count
      @count = 0
    end
    new_quest_marker_updt
  end
  #----------------------------------------------------------------------------
  # * Dispose Object
  #----------------------------------------------------------------------------
  def dispose
    #Call Blacks dispose method
    black_dispose
    #Call a clear
    @quest_marker.clear
    new_quest_marker_disp
    #Call a dispose
    @quest_marker.each {|quest| quest.dispose}
    #if quest sprite exists update it
    @quest_marker.each {|quest| if quest.sprite != nil
                          quest.update
                        end}
    #destroy connections
    @quest_marker = nil
  end      
  #----------------------------------------------------------------------------
  # * Render Marker
  #----------------------------------------------------------------------------
  def render_quest_marker
    #get map events
    $game_map.events.values.each {|event|
      next if event.list == nil
      if event.list[0].code == 108 && event.list[0].parameters[0].split[0] == 'quest_marker'
        # Get file name
        filename = event.list[0].parameters[0].split[1]
        parms = []
        #loop for 4 comment lines
        (1..4).each {|i|
          if event.list[i].code == 108
            parms << event.list[i].parameters
          end
        }
        4.times {|i| parms[i] = [0] if parms[i] == [nil] }        
        #get opacity
        opa = parms[0][0].to_i        
        # Get Bounce
        bou = (parms[1] == ['true'])
        # Get Flash
        fla = (parms[2] == ['true'])        
        #Call quest_marker      
        @quest_marker << Quest_Marker.new(event, opa, bou, fla,
        "Quest Markers/"+filename)
       end
    }
  end
 
  #--------------------------------------------------------------------
  #   * Dispose Quest Marker (Thanks to Black Mage)
  #--------------------------------------------------------------------
  def black_dispose
    #basicly, if quest.sprite exitst DESTROY ITS SOUL!
      @quest_marker.each {|quest| if quest.sprite != nil
                          quest.sprite.visible = false
                          quest.sprite.bitmap.dispose
                          quest.sprite.dispose
                          quest.sprite = nil
                          quest.dispose
                          end}
  end
end