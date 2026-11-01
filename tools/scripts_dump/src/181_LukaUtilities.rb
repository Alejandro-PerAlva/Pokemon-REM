#===============================================================================
#  Scripting Utilities
#    by Luka S.J.
# ----------------
#  Various utilities used within my plugins. Neat and nifty ways to speed
#  the coding process of certain scripts.
#===============================================================================
#-------------------------------------------------------------------------------
#  Mathematical functions
#-------------------------------------------------------------------------------
# generates a uniform polygon based on the number of points, radius (for x and y),
# angle and coordinates of its origin
def getPolygonPoints(n,rx=50,ry=50,a=0,tx=Graphics.width/2,ty=Graphics.height/2)
  points = []
  ang = 360/n
  n.times do
    b = a*(Math::PI/180)
    r = rx*Math.cos(b).abs + ry*Math.sin(b).abs
    x = tx + r*Math.cos(b)
    y = ty - r*Math.sin(b)
    points.push([x,y])
    a += ang
  end
  return points
end

def randCircleCord(r,x=nil)
  x = rand(r*2) if x.nil?
  y1 = -Math.sqrt(r**2 - (x - r)**2)
  y2 =  Math.sqrt(r**2 - (x - r)**2)
  return x, (rand(2)==0 ? y1.to_i : y2.to_i) + r
end
#-------------------------------------------------------------------------------
#  Reads files of certain format from a directory
#-------------------------------------------------------------------------------
def readDirectoryFiles(directory,formats)
  files=[]
  Dir.chdir(directory){
    for i in 0...formats.length
      Dir.glob(formats[i]){|f| files.push(f) }
    end
  }
  return files
end
#-------------------------------------------------------------------------------
#  Extensions for String objects
#-------------------------------------------------------------------------------
class ::String
  def starts_with?(str)
    proc = (self[0...str.length] == str) if self.length >= str.length
    return proc ? proc : false
  end
  
  def ends_with?(str)
    e = self.length - 1
    proc = (self[(e-str.length)...e] == str) if self.length >= str.length
    return proc ? proc : false
  end
  
  def first?
    proc = self.scan(/./)
    return proc[0]
  end
  
  def last?
    proc = self.scan(/./)
    return proc[proc.length-1]
  end
  
  def bytesize
    return self.size
  end
  
  def capitalize
    proc = self.scan(/./)
    proc[0] = proc[0].upcase
    string = ""
    for letter in proc
      string+=letter
    end
    return string
  end
  
  def capitalize!
    self.replace(self.capitalize)
  end
  
  def blank?
    blank = true
    s = self.scan(/./)
    for l in s
      blank = false if l != ""
    end
    return blank
  end
  
  def cut(bitmap,width)
    string = self
    width -= bitmap.text_size("...").width
    string_width = 0
    text = []
    for char in string.scan(/./)
      wdh = bitmap.text_size(char).width
      next if (wdh+string_width) > width
      string_width += wdh
      text.push(char)
    end
    text.push("...") if text.length < string.length
    new_string = ""
    for char in text
      new_string += char
    end
    return new_string
  end
end
#-------------------------------------------------------------------------------
#  Extensions for Array objects
#-------------------------------------------------------------------------------
class ::Array
  def swap(val1,val2)
    index1 = self.index(val1)
    index2 = self.index(val2)
    self[index1] = val2
    self[index2] = val1
  end
  
  def swap_at(index1,index2)
    val1 = self[index1].clone
    val2 = self[index2].clone
    self[index1] = val2
    self[index2] = val1
  end
  
  def first?
    return self[0]
  end
  
  def last?
    return self[self.length-1]
  end
  
  def rand
  return self[rand(self.length)]
  end
end
#------------------------------------------------------------------------------
#  Additional functionality for the Viewport class
#------------------------------------------------------------------------------
class Viewport
  def getAllSprites
    hash = {}
    i = 0
    ObjectSpace.each_object(Sprite){|o|
      begin
        hash["sprite#{i}"] = o if o.viewport && !o.viewport.nil? && o.viewport == self
        rescue RGSSError
      end
    }
    return hash
  end
end
class Sprite
  attr_reader :storedBitmap
  attr_accessor :speed
  attr_accessor :toggle
  attr_accessor :end_x
  attr_accessor :end_y
  attr_accessor :param
  attr_accessor :ex
  attr_accessor :ey
  
  def drawRect(width,height,color)
    self.bitmap = Bitmap.new(width,height)
    self.bitmap.fill_rect(0,0,width,height,color)
  end
  
  def center(snap=false)
    self.ox = self.src_rect.width/2
    self.oy = self.src_rect.height/2
    if snap && self.viewport
      self.x = self.viewport.rect.width/2
      self.y = self.viewport.rect.height/2
    end
  end
  
  def snapScreen
    bmp = Graphics.snap_to_bitmap
    width = self.viewport ? viewport.rect.width : Graphics.width
    height = self.viewport ? viewport.rect.height : Graphics.height
    x = self.viewport ? viewport.rect.x : 0
    y = self.viewport ? viewport.rect.y : 0
    self.bitmap = Bitmap.new(width,height)
    self.bitmap.blt(0,0,bmp,Rect.new(x,y,width,height))    
  end
  
  def skew(angle=90)
    return false if !self.bitmap
    angle=angle*(Math::PI/180)
    bitmap=self.bitmap
    rect=Rect.new(0,0,bitmap.width,bitmap.height)
    width=rect.width+((rect.height-1)/Math.tan(angle))
    self.bitmap=Bitmap.new(width,rect.height)
    for i in 0...rect.height
      y=rect.height-i
      x=i/Math.tan(angle)
      self.bitmap.blt(x+rect.x,y+rect.y,bitmap,Rect.new(0,y,rect.width,1))
    end
  end

  def blur_sprite(blur_val=2,opacity=35)
    bitmap = self.bitmap
    self.bitmap = Bitmap.new(bitmap.width,bitmap.height)
    self.bitmap.blt(0,0,bitmap,Rect.new(0,0,bitmap.width,bitmap.height))
    x=0
    y=0
    for i in 1...(8 * blur_val)
      dir = i % 8
      x += (1 + (i / 8))*([0,6,7].include?(dir) ? -1 : 1)*([1,5].include?(dir) ? 0 : 1)
      y += (1 + (i / 8))*([1,4,5,6].include?(dir) ? -1 : 1)*([3,7].include?(dir) ? 0 : 1)
      self.bitmap.blt(x-blur_val,y+(blur_val*2),bitmap,Rect.new(0,0,bitmap.width,bitmap.height),opacity)
    end
  end
  
  def getAvgColor(freq=2)
    return Color.new(0,0,0,0) if !self.bitmap
    bmp = self.bitmap
    width = self.bitmap.width/freq
    height = self.bitmap.height/freq
    red = 0
    green = 0
    blue = 0
    n = width*height
    for x in 0...width
      for y in 0...height
        color = bmp.get_pixel(x*freq,y*freq)
        if color.alpha > 0
          red += color.red
          green += color.green
          blue += color.blue
        end
      end
    end
    avg = Color.new(red/n,green/n,blue/n)
    return avg
  end
  
  def create_outline(color,thickness=2,hard=false)
    return false if !self.bitmap
    bmp = self.bitmap.clone
    self.bitmap = Bitmap.new(bmp.width,bmp.height)
    for x in 0...bmp.width-thickness
      for y in 0...bmp.height
        pixel = bmp.get_pixel(x,y)
        if pixel.alpha > 0
          for i in 1..thickness
            c1 = bmp.get_pixel(x,y-i)
            c2 = bmp.get_pixel(x,y+i)
            c3 = bmp.get_pixel(x-i,y)
            c4 = bmp.get_pixel(x+i,y)
            self.bitmap.set_pixel(x,y-i,color) if c1.alpha <= 0
            self.bitmap.set_pixel(x,y+i,color) if c2.alpha <= 0
            self.bitmap.set_pixel(x-i,y,color) if c3.alpha <= 0
            self.bitmap.set_pixel(x+i,y,color) if c4.alpha <= 0
          end
        end
      end
    end
    self.bitmap.blt(0,0,bmp,Rect.new(0,0,bmp.width,bmp.height))
  end
  
  def colorize(color)
    return false if !self.bitmap
    bmp = self.bitmap.clone
    self.bitmap = Bitmap.new(bmp.width,bmp.height)
    for x in 0...bmp.width
      for y in 0...bmp.height
        pixel = bmp.get_pixel(x,y)
        self.bitmap.set_pixel(x,y,color) if pixel.alpha > 0
      end
    end
  end
  
  def glow(color,opacity=35,keep=true)
    return false if !self.bitmap
    temp_bmp = self.bitmap.clone
    self.colorize(color)
    self.blur_sprite(3,opacity)
    src = self.bitmap.clone
    self.bitmap.clear
    self.bitmap.stretch_blt(Rect.new(-0.005*src.width,-0.015*src.height,src.width*1.01,1.02*src.height),src,Rect.new(0,0,src.width,src.height))
    self.bitmap.blt(0,0,temp_bmp,Rect.new(0,0,temp_bmp.width,temp_bmp.height)) if keep
  end
  
  def fuzz(color,opacity=35)
    return false if !self.bitmap
    self.colorize(color)
    self.blur_sprite(3,opacity)
    src = self.bitmap.clone
    self.bitmap.clear
    self.bitmap.stretch_blt(Rect.new(-0.005*src.width,-0.015*src.height,src.width*1.01,1.02*src.height),src,Rect.new(0,0,src.width,src.height))
  end
  
  def memorize_bitmap(bitmap = nil)
    @storedBitmap = bitmap if !bitmap.nil?
    @storedBitmap = self.bitmap.clone if bitmap.nil?
  end
  def restore_bitmap
    self.bitmap = @storedBitmap.clone
  end
  
  def toneAll(val)
    self.tone.red += val
    self.tone.green += val
    self.tone.blue += val
  end
  
  def onlineBitmap(url)
    pbDownloadToFile(url,"_temp.png")
    return if !FileTest.exist?("_temp.png")
    self.bitmap = pbBitmap("_temp")
    File.delete("_temp.png")
  end
  # quick parameter setting
  def setParams(*args)
    val = 0
    for param in args
      if param.is_a?(String)
        self.bitmap = BitmapCache.load_bitmap(param)
      elsif param.is_a?(Numeric)
        case val
        when 0
          self.x = param
        when 1
          self.y = param
        when 2
          self.z = param
        end
        val += 1
      elsif param.is_a?(Rect)
        self.src_rect = param
      elsif param.is_a?(Viewport)
        self.viewport = param
      elsif param.is_a?(Bitmap)
        self.bitmap = param
      end
    end
  end
  
  # Credit to Primal Sílex </jk>
  def mask(mask = nil,xpush = 0,ypush = 0) # Draw sprite on a sprite/bitmap
    return false if !self.bitmap
    bitmap = self.bitmap.clone
    if mask.is_a?(Bitmap)
      mbmp = mask
    elsif mask.is_a?(Sprite)
      mbmp = mask.bitmap
    elsif mask.is_a?(String)
      mbmp = BitmapCache.load_bitmap(mask)
    else
      return false
    end
    self.bitmap = Bitmap.new(mbmp.width, mbmp.height)
    mask = mbmp.clone
    ox = (bitmap.width - mbmp.width) / 2
    oy = (bitmap.height - mbmp.height) / 2
    width = mbmp.width + ox
    height = mbmp.height + oy
    for y in oy...height
      for x in ox...width
        pixel = mask.get_pixel(x - ox, y - oy)
        color = bitmap.get_pixel(x - xpush, y - ypush)
        alpha = pixel.alpha
        alpha = color.alpha if color.alpha < pixel.alpha
        self.bitmap.set_pixel(x - ox, y - oy, Color.new(color.red, color.green,
            color.blue, alpha))
      end
    end
    return self.bitmap
  end
end
#------------------------------------------------------------------------------
#  Additional functionality for the Bitmap class
#------------------------------------------------------------------------------
class Bitmap
  attr_accessor :storedPath
  
  def drawCircle(color=Color.new(255,255,255),r=(self.width/2),tx=(self.width/2),ty=(self.height/2),hollow=false)
    # basic circle formula
    # (x - tx)**2 + (y - ty)**2 = r**2
    for x in 0...self.width
      f = (r**2 - (x - tx)**2)
      next if f < 0
      y1 = -Math.sqrt(f).to_i + ty
      y2 =  Math.sqrt(f).to_i + ty
      if hollow
        self.set_pixel(x,y1,color)
        self.set_pixel(x,y2,color)
      else
        for y in y1..y2
          self.set_pixel(x,y,color)
        end
      end
    end
  end
  
  def setFont(size,bold=false)
    self.font.name = "Arial"
    self.font.size = size
    self.font.bold = bold
  end
  
  # Credit to Primal Sílex </jk>
  def mask(mask = nil,xpush = 0,ypush = 0) # Draw sprite on a sprite/bitmap
    bitmap = self.clone
    if mask.is_a?(Bitmap)
      mbmp = mask
    elsif mask.is_a?(Sprite)
      mbmp = mask.bitmap
    elsif mask.is_a?(String)
      mbmp = BitmapCache.load_bitmap(mask)
    else
      return false
    end
    cbmp = Bitmap.new(mbmp.width, mbmp.height)
    mask = mbmp.clone
    ox = (bitmap.width - mbmp.width) / 2
    oy = (bitmap.height - mbmp.height) / 2
    width = mbmp.width + ox
    height = mbmp.height + oy
    for y in oy...height
      for x in ox...width
        pixel = mask.get_pixel(x - ox, y - oy)
        color = bitmap.get_pixel(x - xpush, y - ypush)
        alpha = pixel.alpha
        alpha = color.alpha if color.alpha < pixel.alpha
        cbmp.set_pixel(x - ox, y - oy, Color.new(color.red, color.green,
            color.blue, alpha))
      end
    end
    return cbmp.clone
  end
end
#-------------------------------------------------------------------------------
#  Class used for generating scrolling backgrounds (move animations)
#-------------------------------------------------------------------------------
class ScrollingSprite < Sprite
  attr_accessor :speed
  attr_accessor :direction
  attr_accessor :vertical
  
  def setBitmap(val,vertical=false,pulse=false)
    @vertical = vertical
    @pulse = pulse
    @direction = 1 if @direction.nil?
    @gopac = 1
    @speed = 32 if @speed.nil?
    val = pbBitmap(val) if val.is_a?(String)
    if @vertical
      bmp = Bitmap.new(val.width,val.height*2)
      for i in 0...2
        bmp.blt(0,val.height*i,val,Rect.new(0,0,val.width,val.height))
      end
      self.bitmap = bmp.clone
      y = @direction > 0 ? 0 : val.height
      self.src_rect.set(0,y,val.width,val.height)
    else
      bmp = Bitmap.new(val.width*2,val.height)
      for i in 0...2
        bmp.blt(val.width*i,0,val,Rect.new(0,0,val.width,val.height))
      end
      self.bitmap = bmp.clone
      x = @direction > 0 ? 0 : val.width
      self.src_rect.set(x,0,val.width,val.height)
    end
  end
  
  def update
    if @vertical
      self.src_rect.y += @speed*@direction
      self.src_rect.y = 0 if @direction > 0 && self.src_rect.y >= self.src_rect.height
      self.src_rect.y = self.src_rect.height if @direction < 0 && self.src_rect.y <= 0
    else
      self.src_rect.x += @speed*@direction
      self.src_rect.x = 0 if @direction > 0 && self.src_rect.x >= self.src_rect.width
      self.src_rect.x = self.src_rect.width if @direction < 0 && self.src_rect.x <= 0
    end
    if @pulse
      self.opacity -= @gopac*@speed
      @gopac *= -1 if self.opacity == 255 || self.opacity == 0
    end
  end
    
end
#-------------------------------------------------------------------------------
#  Class used for generating sprites with a trail
#-------------------------------------------------------------------------------
class TrailingSprite
  attr_accessor :x
  attr_accessor :y
  attr_accessor :z
  attr_accessor :color
  attr_accessor :keyFrame
  attr_accessor :zoom_x
  attr_accessor :zoom_y
  attr_accessor :opacity
  
  def initialize(viewport,bmp)
    @viewport = viewport
    @bmp = bmp
    @sprites = {}
    @x = 0
    @y = 0
    @z = 0
    @i = 0
    @frame = 128
    @keyFrame = 0
    @color = Color.new(0,0,0,0)
    @zoom_x = 1
    @zoom_y = 1
    @opacity = 255
  end
  
  def update
    @frame += 1
    if @frame > @keyFrame
      @sprites["#{@i}"] = Sprite.new(@viewport)
      @sprites["#{@i}"].bitmap = @bmp
      @sprites["#{@i}"].center
      @sprites["#{@i}"].x = x
      @sprites["#{@i}"].y = y
      @sprites["#{@i}"].z = z
      @sprites["#{@i}"].zoom_x = @zoom_x
      @sprites["#{@i}"].zoom_y = @zoom_y
      @sprites["#{@i}"].opacity = @opacity
      @i += 1
      @frame = 0
    end
    for key in @sprites.keys
      if @sprites[key].opacity > @keyFrame
        @sprites[key].opacity -= 24
        @sprites[key].zoom_x -= 0.035
        @sprites[key].zoom_y -= 0.035
        @sprites[key].color = @color
      end
    end
  end
  
  def visible=(val)
    for key in @sprites.keys
      @sprites[key].visible = val
    end
  end
  
  def dispose
    for key in @sprites.keys
      @sprites[key].dispose
    end
    @sprites.clear
  end
  
  def disposed?
    @sprites.keys.length < 1
  end
end
#-------------------------------------------------------------------------------
#  Class used to render the background for the special S&M trainer battle
#  animation
#-------------------------------------------------------------------------------
class RainbowSprite < Sprite
  attr_accessor :speed
  def setBitmap(val,speed = 1)
    @val = val
    @val = pbBitmap(val) if val.is_a?(String)
    @speed = speed
    self.bitmap = Bitmap.new(@val.width,@val.height)
    self.bitmap.blt(0,0,@val,Rect.new(0,0,@val.width,@val.height))
    @current_hue = 0
  end
  
  def update
    self.bitmap.clear
    self.bitmap.blt(0,0,@val,Rect.new(0,0,@val.width,@val.height))
    self.bitmap.hue_change(@current_hue)
    @current_hue += @speed
    @current_hue = 0 if @current_hue >= 360
  end
end
#-------------------------------------------------------------------------------
#  Common UI handlers
#-------------------------------------------------------------------------------
class CommonButton < Sprite
  attr_accessor :selected
  def setButton(size="M",var=1,text="")
    bmp = pbBitmap("Graphics/Pictures/Common/btn#{size}_#{var}")
    pbSetSmallFont(bmp)
    case size
    when "M"
      x, y, w, h = 46, 22, 92, 38
    when "N"
      x, y, w, h = 54, 16, 108, 30
    when "L"
      x, y, w, h = 61, 22, 122, 38
    end
    color = self.darkenColor(bmp.get_pixel(x, y))
    self.bitmap = Bitmap.new(bmp.width - 22, bmp.height)
    pbSetSmallFont(self.bitmap)
    self.bitmap.blt(0, 0, bmp, Rect.new(0, 0, bmp.width - 22, bmp.height))
    pbDrawOutlineText(self.bitmap,2,2,w,h,text,Color.new(255,255,255),color,1)
  end
    
  def darkenColor(color=nil,amt=0.6)
    return getDarkerColor(color,amt)
  end
end

def getDarkerColor(color=nil,amt=0.6)
  return nil if color.nil?
  red = color.red - color.red*amt
  green = color.green - color.green*amt
  blue = color.blue - color.blue*amt
  return Color.new(red,green,blue)
end
#-------------------------------------------------------------------------------
#  Misc scripting utilities
#-------------------------------------------------------------------------------
class Bitmap
  attr_accessor :storedPath
end

def pbBitmap(name)
  if !pbResolveBitmap(name).nil?
    bmp = BitmapCache.load_bitmap(name)
    bmp.storedPath = name
  else
    p "Image located at '#{name}' was not found!" if $DEBUG
    bmp = Bitmap.new(1,1)
  end
  return bmp
end
#-------------------------------------------------------------------------------
#  F12 Soft-resetting fix
#-------------------------------------------------------------------------------
if defined?(SOFTRESETFIX) && SOFTRESETFIX
unless $f12_fix.nil?
  game_name = "Game"
  if $DEBUG
    Thread.new{system(game_name+" debug")}
  else
    Thread.new{system(game_name)}
  end
  exit
end
$f12_fix = true
end
#-------------------------------------------------------------------------------
#  Other utilities
#-------------------------------------------------------------------------------
# Allows for skipping of the global wait function
alias pbWait_updater pbWait
def pbWait(*args)
  skip = $skipDatWait
  $skipDatWait = false
  return if skip
  return pbWait_updater(*args)
end
#===============================================================================
# Don't touch these
# Used to configure the system for potential DS styles (leftovers)
#-----------------------------------------------------
VIEWPORT_HEIGHT = DEFAULTSCREENHEIGHT
VIEWPORT_OFFSET = 0
# Other system config
#-----------------------------------------------------
INCLUDEGEN6 = respond_to?(:pbForceEvo) ? true : false
EFFECTMESSAGES = false if INCLUDEGEN6
$memDebug = $DEBUG
$DEBUG = false if defined?(PLAY_ON_DEBUG) && (PLAY_ON_DEBUG)
#-----------------------------------------------------
def isVersion17?; return defined?(ESSENTIALSVERSION); end
  
  
  
  
#-----------QUITAR BASES-----------  
      # Apply graphics
      USEBATTLEBASES = false
    enemybase=USEBATTLEBASES ? "Graphics/Battlebacks/enemybase": nil
    playerbase=USEBATTLEBASES ? "Graphics/Battlebacks/playerbase": nil



