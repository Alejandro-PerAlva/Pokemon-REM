FOLLOWER_SWITCH = 101
COMMON_EVENT_ID = 5
$follower_hidden_by_map_change = false

def pbSpawnFollower
  return if !$Trainer || $Trainer.party.length == 0
  
  has_follower = false
  if $PokemonGlobal.dependentEvents
    $PokemonGlobal.dependentEvents.each do |event|
      if event && event[8] == "Dependent"
        has_follower = true
        break
      end
    end
  end
  
  if !has_follower
    px = $game_player.x
    py = $game_player.y
    case $game_player.direction
    when 2
      py -= 1
    when 4
      px += 1
    when 6
      px -= 1
    when 8
      py += 1
    end
    
    new_id = ($game_map.events.keys.max || 0) + 1
    rpg_event = RPG::Event.new(px, py)
    rpg_event.id = new_id
    rpg_event.name = "Dependent"
    
    event = Game_Event.new($game_map.map_id, rpg_event, $game_map)
    $game_map.events[new_id] = event
    
    Kernel.pbAddDependency2(new_id, "Dependent", COMMON_EVENT_ID)
  end
  
  $game_switches[FOLLOWER_SWITCH] = true
  $PokemonTemp.dependentEvents.refresh_sprite if $PokemonTemp.dependentEvents
end

class DependentEvents
  attr_accessor :realEvents
  
  def refresh_sprite
    return if !$game_switches[FOLLOWER_SWITCH]
    pkmn = $Trainer.party[0]
    
    if !pkmn || pkmn.isEgg? || pkmn.hp <= 0
      remove_sprite
      return
    end
    
    events = $PokemonGlobal.dependentEvents
    for i in 0...events.length
      if events[i] && events[i][8] == "Dependent"
        filename = sprintf("%03d%s", pkmn.species, (pkmn.isShiny? ? "s" : ""))
        filename = sprintf("%03d", pkmn.species) if !pbResolveBitmap("Graphics/Characters/" + filename)
        
        events[i][6] = filename
        if @realEvents && @realEvents[i]
          @realEvents[i].character_name = filename
          @realEvents[i].transparent = false
          @realEvents[i].instance_variable_set(:@walk_anime, true)
          @realEvents[i].instance_variable_set(:@step_anime, true)
          @realEvents[i].move_speed = $game_player.move_speed
        end
      end
    end
  end
  
  def remove_sprite
    events = $PokemonGlobal.dependentEvents
    for i in 0...events.length
      if events[i] && events[i][8] == "Dependent"
        events[i][6] = ""
        if @realEvents && @realEvents[i]
          @realEvents[i].character_name = ""
          @realEvents[i].transparent = true
        end
      end
    end
  end

  def pbFollowEventAcrossMaps(leader,follower,instant=false,leaderIsTrueLeader=true)
    d=leader.direction
    areConnected=$MapFactory.areConnected?(leader.map.map_id,follower.map.map_id)
    
    facingDirection=[0,0,8,0,6,0,4,0,2][d]
    facings=[facingDirection]
    
    mapTile=nil
    if areConnected
      bestRelativePos=-1
      for i in 0...facings.length
        facing=facings[i]
        tile=$MapFactory.getFacingTile(facing,leader)
        passable = (tile != nil) 
        
        if passable
          relativePos=$MapFactory.getThisAndOtherPosRelativePos(follower,tile[0],tile[1],tile[2])
          distance=Math.sqrt(relativePos[0]*relativePos[0]+relativePos[1]*relativePos[1])
          if bestRelativePos==-1 || bestRelativePos>distance
            bestRelativePos=distance
            mapTile=tile
          end
        end
      end
    else
      mapTile=$MapFactory.getFacingTile(facings[0],leader)
    end
    
    if mapTile && follower.map.map_id==mapTile[0]
      newX=mapTile[1]
      newY=mapTile[2]
      follower.move_speed=leader.move_speed
      
      if instant
        follower.moveto(newX,newY)
      else
        follower.through = true 
        pbFancyMoveTo(follower,newX,newY)
        follower.through = false
      end
    else
      if !mapTile
        mapTile=[leader.map.map_id,leader.x,leader.y]
      end
      if follower.map.map_id==mapTile[0]
        follower.moveto(leader.x,leader.y)
      else
        events=$PokemonGlobal.dependentEvents
        eventIndex=pbEnsureEvent(follower,mapTile[0])
        if eventIndex>=0
          newFollower=@realEvents[eventIndex]
          newEventData=events[eventIndex]
          newFollower.moveto(mapTile[1],mapTile[2])
          newEventData[3]=mapTile[1]
          newEventData[4]=mapTile[2]
        end
      end
    end
  end
end

class DependentEventSprites
  def refresh
    for sprite in @sprites
      sprite.dispose
    end
    @sprites.clear
    $PokemonTemp.dependentEvents.eachEvent {|event,data|
       if data[0]==@map.map_id 
         @map.events[data[1]].erase if @map.events[data[1]]
       end
       if data[2]==@map.map_id 
         spr = Sprite_Character.new(@viewport,event)
         @sprites.push(spr)
       end
    }
  end
end

class Scene_Map
  alias minimal_follower_update update
  def update
    minimal_follower_update
    
    if $follower_hidden_by_map_change
      if $game_player.moving?
        $follower_hidden_by_map_change = false
        pbSpawnFollower
      end
    else
      if !$game_switches[FOLLOWER_SWITCH] && $Trainer && $Trainer.party.length > 0
        pbSpawnFollower
      end
      
      if $game_switches[FOLLOWER_SWITCH] && $PokemonTemp && $PokemonTemp.dependentEvents && $PokemonTemp.dependentEvents.realEvents
        follower = $PokemonTemp.dependentEvents.realEvents[0]
        if follower && follower.character_name != ""
          follower.instance_variable_set(:@step_anime, true)
          follower.instance_variable_set(:@walk_anime, true)
        end
      end
    end
  end
  
  alias follower_map_transfer transfer_player
  def transfer_player(cancelVehicles=true)
    follower_map_transfer(cancelVehicles)
    $follower_hidden_by_map_change = true
    if $PokemonTemp && $PokemonTemp.dependentEvents
      $PokemonTemp.dependentEvents.remove_sprite
    end
  end
end

class PokemonScreen
  alias follow_pbSwitch pbSwitch
  def pbSwitch(oldid,newid)
    follow_pbSwitch(oldid,newid)
    $PokemonTemp.dependentEvents.refresh_sprite if $PokemonTemp.dependentEvents
  end
end

class Game_Player < Game_Character
  alias follow_update update
  def update
    follow_update
    if $PokemonTemp && $PokemonTemp.dependentEvents && $PokemonTemp.dependentEvents.realEvents
      events = $PokemonGlobal.dependentEvents
      for i in 0...events.length
        if events[i] && events[i][8] == "Dependent"
          if $PokemonTemp.dependentEvents.realEvents[i]
            $PokemonTemp.dependentEvents.realEvents[i].move_speed = self.move_speed
          end
        end
      end
    end
  end
end

class Game_Event < Game_Character
  alias follower_z_tiebreaker screen_z unless method_defined?(:follower_z_tiebreaker)
  def screen_z(height_pos = 0)
    ret = follower_z_tiebreaker(height_pos)
    if self.name == "Dependent"
      if (self.real_x - $game_player.real_x).abs < 128 && (self.real_y - $game_player.real_y).abs < 128
        return $game_player.screen_z(height_pos) - 1
      end
      ret -= 1
    end
    return ret
  end
end