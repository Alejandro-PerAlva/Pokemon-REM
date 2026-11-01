class PokeBattle_Trainer
  attr_accessor(:ultimoobjeto)

  def ultimoobjeto
    @ultimoobjeto = [] if !@ultimoobjeto
    return @ultimoobjeto
  end
  
end
             
     def usarobjeto          
      if $Trainer.ultimoobjeto
    
    objeto=$Trainer.ultimoobjeto
              
      if objeto>0
        usetype=$ItemData[objeto][ITEMBATTLEUSE]
        if usetype==1 || usetype==3
          pbUseItemOnPokemon(objeto,@choices[i.index][2],i,@scene)
        elsif usetype==2 || usetype==4
          if !ItemHandlers.hasUseInBattle(objeto)
            pbUseItemOnBattler(objeto,@choices[i.index][2],i,@scene)
          end          
        end
      end
        
  else
   Kernel.pbMessage("Todavía no has usado ningún objeto.")
  end
           
           
end
         