#===============================================================================
# * Constants for animated Pokémon sprites
#===============================================================================
FRONTSPRITE_SCALE = 2
BACKSPRITE_SCALE = 3

#===============================================================================
#                   Animated Sprites for vanilla Essentials
#                                by Luka S.J.
#===============================================================================
class BitmapWrapperEX
  attr_reader :width, :height, :totalFrames, :animationFrames, :currentIndex
  attr_accessor :constrict, :scale, :frameSkip, :offset_y

  def initialize(file, scale = 2, skip = 1, unavez = false, speed = 1)
    @unavez = unavez
    raise "filename is nil" if file == nil
    raise ".gif files are not supported!" if File.extname(file) == ".gif"
    
    @@disableBitmapAnimation = false
  
    @scale = scale
    @constrict = nil
    @frame = 0
    @frames = 2
    @frameSkip = skip
    @direction = 1
    @animationFinish = false
    @totalFrames = 0
    @currentIndex = 0
    @changed_hue = false
    @speed = speed
    @bitmapFile = pbBitmap(file)
    
    if $MKXP && @bitmapFile.width > 14000
      if $PokemonSystem.sprtanime == 0
        @bitmap = Bitmap.new(14000, @bitmapFile.height)
      else
        @bitmap = Bitmap.new(3000, @bitmapFile.height)
      end
      @bitmap.blt(0, 0, @bitmapFile, @bitmapFile.rect)
    else
      @bitmap = Bitmap.new(@bitmapFile.width, @bitmapFile.height)
      @bitmap.blt(0, 0, @bitmapFile, @bitmapFile.rect)
    end
   
    #---------------------------------------------------------------------------
    # ESCÁNER DINÁMICO (Compatible con Ruby 1.8 de RPG Maker)
    # Detecta el espacio vacío real debajo de cada Pokémon de forma individual.
    #---------------------------------------------------------------------------
    frame_height = @bitmapFile.height
    bg_color = @bitmapFile.get_pixel(0, 0)
    pixels_to_trim = 0
    
    (frame_height - 1).downto(0) do |y|
      row_is_empty = true
      (0...frame_height).step(2) do |x| 
        pixel = @bitmapFile.get_pixel(x, y)
        if pixel.alpha > 10 && pixel != bg_color
          row_is_empty = false
          break
        end
      end
      if row_is_empty
        pixels_to_trim += 1
      else
        break
      end
    end
    
    # Guardamos la distancia exacta que este Pokémon en concreto debe flotar
    @offset_y = pixels_to_trim * @scale
    #---------------------------------------------------------------------------

    @width = @bitmapFile.height * @scale
    @height = @bitmap.height * @scale
    
    self.refresh
    @actualBitmap = Bitmap.new(@width, @height)
    self.toFrame(0)
  end

  def length; @totalFrames; end
  def disposed?; @actualBitmap.disposed?; end
  def dispose
    @bitmap.dispose
    @bitmapFile.dispose
    @actualBitmap.dispose
  end
  def copy; @actualBitmap.clone; end
  def bitmap; @actualBitmap; end
  def bitmap=(val); @actualBitmap = val; end
  def each; end
  def alterBitmap(index); return @strip[index]; end

  def prepareStrip
    @strip = []
    for i in 0...@totalFrames
      b = Bitmap.new(@width, @height)
      b.stretch_blt(
        Rect.new(0, 0, @width, @height),
        @bitmapFile,
        Rect.new((@width / @scale) * i, 0, @width / @scale, @height / @scale)
      )
      @strip.push(b)
    end
  end

  def compileStrip
    @bitmap.clear
    for i in 0...@strip.length
      @bitmap.stretch_blt(
        Rect.new((@width / @scale) * i, 0, @width / @scale, @height / @scale),
        @strip[i],
        Rect.new(0, 0, @width, @height)
      )
    end
  end

  def compileLoop(data)
    r = @bitmapFile.height; w = 0; x = 0
    @bitmap.clear
    for p in data
      w += p[:range].to_a.length * p[:repeat] * r
    end
    @bitmap = Bitmap.new(w, r)
    for m in 0...data.length
      range = data[m][:range].to_a
      repeat = data[m][:repeat]
      x += m > 0 ? (data[m - 1][:range].to_a.length * data[m - 1][:repeat] * r) : 0
      for i in 0...repeat
        for j in 0...range.length
          x0 = x + (i * range.length * r) + (j * r)
          @bitmap.blt(x0, 0, @bitmapFile, Rect.new(range[j] * r, 0, r, r))
        end
      end
    end
    self.refresh
  end

  def refresh
    @totalFrames = (@bitmap.width.to_f / @bitmapFile.height).ceil
    @animationFrames = @totalFrames * @frames
  end

  def reverse
    if @direction > 0
      @direction = -1
    elsif @direction < 0
      @direction = +1
    end
  end

  def setSpeed(value)
    @speed = value
  end

  def box
    x = (@constrict.nil? || @width <= @constrict) ? 0 : ((@width - @constrict) / 2.0).ceil
    y = (@constrict.nil? || @height <= @constrict) ? 0 : ((@height - @constrict) / 2.0).ceil
    w = (@constrict.nil? || @width <= @constrict) ? @width : @constrict
    h = (@constrict.nil? || @height <= @constrict) ? @height : @constrict
    return x, y, w, h
  end

  def toFrame(frame)
    if frame.is_a?(String)
      frame = (frame == "last") ? (@totalFrames - 1) : 0
    end
    frame = @totalFrames - 1 if frame >= @totalFrames
    frame = 0 if frame < 0
    @currentIndex = frame
    
    @actualBitmap.clear
    x, y, w, h = self.box
    @actualBitmap.stretch_blt(
      Rect.new(x, y, w, h),
      @bitmap,
      Rect.new(@currentIndex * (@width / @scale) + x / @scale, y / @scale, w / @scale, h / @scale)
    )
  end

  def hue_change(value)
    @bitmap.hue_change(value)
    @changed_hue = true
  end
  def changedHue?; return @changed_hue; end

  def finished?
    return (@currentIndex >= @totalFrames - 1)
  end

  def update
    return false if @@disableBitmapAnimation
    return false if @actualBitmap.disposed?
    return false if self.finished? && @unavez == true
    return false if @speed < 1
    case @speed
    when 2; @frames = 4
    when 3; @frames = 5
    else; @frames = 2
    end
    @frame += 1
    if @frame >= @frames * @frameSkip
      @currentIndex += @direction
      @currentIndex = 0 if @currentIndex >= @totalFrames
      @currentIndex = @totalFrames - 1 if @currentIndex < 0
      @frame = 0
    end
    
    @actualBitmap.clear
    x, y, w, h = self.box
    @actualBitmap.stretch_blt(
      Rect.new(x, y, w, h),
      @bitmap,
      Rect.new(@currentIndex * (@width / @scale) + x / @scale, y / @scale, w / @scale, h / @scale)
    )
  end

  def deanimate
    @frame = 0
    @currentIndex = 0
    self.toFrame(0)
  end
end

#===============================================================================
# Parche de Anclaje Dinámico (Garantiza adaptación por Pokémon)
#===============================================================================
class PokemonBattlerSprite < RPG::Sprite
  alias _luka_oy_set oy= unless method_defined?(:_luka_oy_set)
  
  def oy=(val)
    if self.bitmap.is_a?(BitmapWrapperEX) && self.bitmap.offset_y
      # Cada vez que el motor intenta reubicar o centrar al Pokémon,
      # lo interceptamos y le sumamos su offset exacto.
      # Bulbasaur será empujado hacia arriba; Abomasnow se quedará igual.
      _luka_oy_set(val + self.bitmap.offset_y)
    else
      _luka_oy_set(val)
    end
  end
end