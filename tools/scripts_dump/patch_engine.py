# Parchea el fuente descomprimido de Scripts.rxdata (rebalanceo REM). Idempotencia: se ejecuta sobre un dump limpio.
import glob,re
D='/Users/a.perezalvarez/Documents/notion/Pokemon-REM/tools/scripts_dump/src/'
S={};CRLF={}
def F(n): return glob.glob(D+n+'_*.rb')[0]
def load(n):
    if n not in S:
        b=open(F(n),'rb').read().decode('utf-8'); CRLF[n]='\r\n' in b
        S[n]=b.replace('\r\n','\n')
    return S[n]
def rep(n,old,new,count=1):
    t=load(n); c=t.count(old); assert c==count,(n,c,old[:80]); S[n]=t.replace(old,new)
def rx(n,pat,new,count=1):
    t=load(n); r,c=re.subn(pat,new,t,flags=re.S); assert c==count,(n,c,pat[:80]); S[n]=r
# ======================= 080 Battler =======================
rep('080',"      speedmult=speedmult*2 if self.hasWorkingAbility(:SLUSHRUSH)\n    end\n",
 "      speedmult=speedmult*2 if self.hasWorkingAbility(:SLUSHRUSH)\n    end\n"
 "    speedmult=(speedmult*1.25).round if self.hasWorkingAbility(:RUNAWAY) && self.hp<=(self.totalhp/2).floor   # Fuga\n"
 "    speedmult=(speedmult*1.1).round if self.hasWorkingAbility(:LIGHTMETAL)   # Metal Liviano\n")
rep('080','provocó granizo!','provocó una nevada!'); rep('080','provocó granizo")','provocó nevada")')
rep('080',"if canflinch && @battle.pbRandom(10)==0","if canflinch && @battle.pbRandom(100)<(user.hasWorkingAbility(:STENCH) ? 15 : 10)")
rep('080',"if self.hasWorkingAbility(:ANTICIPATION) && @battle.pbOwnedByPlayer?(@index) && onactive","if self.hasWorkingAbility(:ANTICIPATION) && onactive")
rep('080',"      @battle.pbDisplay(_INTL(\"¡Anticipación de {1} le hizo estremecerse!\",pbThis)) if found\n",
 "      if found\n        @battle.pbDisplay(_INTL(\"¡Anticipación de {1} le hizo estremecerse!\",pbThis))\n"
 "        pbIncreaseStatWithCause(PBStats::SPEED,1,self,PBAbilities.getName(self.ability))\n      end\n")
rep('080',"if self.hasWorkingAbility(:FOREWARN) && @battle.pbOwnedByPlayer?(@index) && onactive","if false && self.hasWorkingAbility(:FOREWARN) && onactive   # reemplazado en REM_Rebalance")
rep('080',"if !pbIsOpposing?(i) && @battle.battlers[i]!=self && !@battle.battlers[i].isFainted?\n          @battle.battlers[i].stages[PBStats::ATTACK]",
 "if pbIsOpposing?(i) && !@battle.battlers[i].isFainted?\n          @battle.battlers[i].stages[PBStats::ATTACK]")
rep('080',"if self.hasWorkingAbility(:PASTELVEIL) && @battle.doublebattle && !pbPartner.isFainted? && onactive","if false && self.hasWorkingAbility(:PASTELVEIL) && @battle.doublebattle && !pbPartner.isFainted? && onactive")
rep('080',"!(user.hasWorkingAbility(:STALWART)||user.hasWorkingAbility(:PROPELLERTAIL))","!user.hasWorkingAbility(:STALWART)",3)
rep('080',"        if target.hasWorkingAbility(:STAMINA)\n",
 "        if target.hasWorkingAbility(:PASTELVEIL) && move.pbIsSpecial?(movetype)\n"
 "          target.pbIncreaseStatWithCause(PBStats::SPDEF,1,target,PBAbilities.getName(target.ability))\n        end\n"
 "        if target.hasWorkingAbility(:STAMINA)\n")
rx('080',r"    if self\.status==PBStatuses::FROZEN\n      if thismove\.canThawUser\?.*?return false\n      end\n    end\n(?=    if !turneffects\[PBEffects::SkipAccuracyCheck\]\n      if @effects\[PBEffects::Confusion\]>0)",
 "    if self.status==PBStatuses::FROZEN && thismove.canThawUser?   # Heladura: ya no paraliza el turno\n"
 "      self.pbCureStatus(false)\n      @battle.pbDisplay(_INTL(\"¡{1} derritió el hielo!\",pbThis))\n      pbCheckForm\n    end\n")
rep('080',"    when PBStatuses::FROZEN\n      if self.hasWorkingAbility(:MAGMAARMOR)","    when PBStatuses::FROZEN\n      if self.hasWorkingAbility(:MAGMAARMOR) || self.hasWorkingAbility(:VITALSPIRIT)")
# ======================= 081 BattlerEffects =======================
rep('081',"if hasWorkingAbility(:MAGMAARMOR) ||\n         (hasWorkingAbility(:FLOWERVEIL) && pbHasType?(:GRASS)) ||\n         (hasWorkingAbility(:LEAFGUARD) && (@battle.pbWeather==PBWeather::SUNNYDAY ||\n                                            @battle.pbWeather==PBWeather::HARSHSUN) && !hasWorkingItem(:UTILITYUMBRELLA))\n        @battle.pbDisplay(_INTL(\"¡{2} de {1} evita quedarse congelado",
 "if hasWorkingAbility(:MAGMAARMOR) || hasWorkingAbility(:VITALSPIRIT) ||\n         (hasWorkingAbility(:FLOWERVEIL) && pbHasType?(:GRASS)) ||\n         (hasWorkingAbility(:LEAFGUARD) && (@battle.pbWeather==PBWeather::SUNNYDAY ||\n                                            @battle.pbWeather==PBWeather::HARSHSUN) && !hasWorkingItem(:UTILITYUMBRELLA))\n        @battle.pbDisplay(_INTL(\"¡{2} de {1} evita quedarse congelado")
rep('081',"def pbFreeze(msg=nil)","def pbFreeze(msg=nil,attacker=nil)")
rep('081','    PBDebug.log("[Cambio de estado] #{pbThis} se ha congelado")\n',
 '    PBDebug.log("[Cambio de estado] #{pbThis} se ha congelado")\n'
 "    if attacker && self.index!=attacker.index && self.hasWorkingAbility(:SYNCHRONIZE)   # Sincronía (Heladura)\n"
 "      if attacker.pbCanFreezeSynchronize?(self)\n"
 "        PBDebug.log(\"[Habilidad disparada] Sincronía de #{self.pbThis}\")\n"
 "        attacker.pbFreeze(_INTL(\"¡{2} de {1} ha congelado a {3}!\",self.pbThis,PBAbilities.getName(self.ability),attacker.pbThis(true)))\n      end\n    end\n")
rep('081','@battle.pbDisplay(_INTL("¡{1} está congelado!",pbThis))','@battle.pbDisplay(_INTL("¡{1} sufre la heladura!",pbThis))')
rep('081',"(pbHasType?(:POISON) || pbHasType?(:STEEL) || hasWorkingAbility(:PASTELVEIL)) &&","(pbHasType?(:POISON) || pbHasType?(:STEEL)) &&")
rx('081',r"if pbPartner\.hasWorkingAbility\(:FLOWERVEIL\) && pbHasType\?\(:GRASS\) \|\|\n\s+pbPartner\.hasWorkingAbility\(:PASTELVEIL\)[ ]*\n","if pbPartner.hasWorkingAbility(:FLOWERVEIL) && pbHasType?(:GRASS)\n")
# ======================= 082 Move =======================
rx('082',r"      if opponent\.hasWorkingAbility\(:SANDVEIL\) &&\n         @battle\.pbWeather==PBWeather::SANDSTORM\n        evasion\*=1\.25\n      end\n      if opponent\.hasWorkingAbility\(:SNOWCLOAK\) &&\n         @battle\.pbWeather==PBWeather::HAIL\n        evasion\*=1\.25\n      end\n","")
rep('082',"if opponent.hasWorkingAbility(:BATTLEARMOR) ||\n         opponent.hasWorkingAbility(:SHELLARMOR)\n","if opponent.hasWorkingAbility(:BATTLEARMOR)\n")
rep('082',"attacker.status==PBStatuses::BURN && pbIsSpecial?(type)\n      damagemult=(damagemult*1.5).round\n    end\n",
 "(attacker.status==PBStatuses::BURN || attacker.status==PBStatuses::FROZEN) && pbIsSpecial?(type)\n      damagemult=(damagemult*1.5).round\n    end\n"
 "    if attacker.hasWorkingAbility(:KLUTZ)   # Zoquete\n      damagemult=(damagemult*1.2).round\n    end\n"
 "    if attacker.hasWorkingAbility(:PROPELLERTAIL) && !isContactMove?   # Hélice Cola\n      damagemult=(damagemult*1.2).round\n    end\n")
rep('082',"      partner=attacker.pbPartner\n      if partner.hasWorkingAbility(:PLUS) || partner.hasWorkingAbility(:MINUS)\n        atkmult=(atkmult*1.5).round\n      end\n",
 "      partner=attacker.pbPartner\n      if partner.hasWorkingAbility(:PLUS) || partner.hasWorkingAbility(:MINUS)\n        atkmult=(atkmult*1.5).round\n      elsif attacker.hasWorkingAbility(:PLUS)\n        atkmult=(atkmult*1.25).round\n      end\n")
rep('082',"    if (attacker.hasWorkingAbility(:PUREPOWER) ||\n       attacker.hasWorkingAbility(:HUGEPOWER)) && pbIsPhysical?(type)\n      atkmult=(atkmult*2.0).round\n    end\n",
 "    if attacker.hasWorkingAbility(:HUGEPOWER) && pbIsPhysical?(type)\n      atkmult=(atkmult*2.0).round\n    end\n"
 "    if attacker.hasWorkingAbility(:PUREPOWER) && pbIsSpecial?(type)   # Energía Pura: Atq. Esp. x2\n      atkmult=(atkmult*2.0).round\n    end\n")
rep('082',"      if opponent.hasWorkingAbility(:ICESCALES) && pbIsSpecial?(type)\n        defmult=(defmult*1.5).round\n      end\n    end\n",
 "      if opponent.hasWorkingAbility(:SANDVEIL) && @battle.pbWeather==PBWeather::SANDSTORM && pbIsPhysical?(type)\n        defmult=(defmult*1.25).round\n      end\n"
 "      if opponent.hasWorkingAbility(:SNOWCLOAK) && @battle.pbWeather==PBWeather::HAIL && pbIsSpecial?(type)\n        defmult=(defmult*1.2).round\n      end\n"
 "      if opponent.hasWorkingAbility(:MINUS) && pbIsSpecial?(type) &&\n         !opponent.pbPartner.hasWorkingAbility(:PLUS) && !opponent.pbPartner.hasWorkingAbility(:MINUS)\n        defmult=(defmult*1.2).round\n      end\n"
 "      if opponent.hasWorkingAbility(:HEAVYMETAL) && pbIsPhysical?(type)\n        defmult=(defmult*1.1).round\n      end\n    end\n"
 "    if @battle.pbWeather==PBWeather::HAIL && opponent.pbHasType?(:ICE) && pbIsPhysical?(type)   # Nieve: Def. x1,5 a tipo Hielo\n      defmult=(defmult*1.5).round\n    end\n")
rep('082',"    # Make sure damage is at least 1\n    damage=1 if damage<1\n",
 "    if attacker.status==PBStatuses::FROZEN && pbIsSpecial?(type) && !attacker.hasWorkingAbility(:FLAREBOOST)   # Heladura\n      damage=(damage*0.5).round\n    end\n"
 "    # Make sure damage is at least 1\n    damage=1 if damage<1\n")
rep('082',"      if opponent.pbPartner.hasWorkingAbility(:FRIENDGUARD)\n        finaldamagemult=(finaldamagemult*0.75).round\n      end\n",
 "      if opponent.pbPartner.hasWorkingAbility(:FRIENDGUARD)\n        finaldamagemult=(finaldamagemult*0.75).round\n      end\n"
 "      if opponent.hasWorkingAbility(:FRIENDGUARD) && !@battle.doublebattle\n        finaldamagemult=(finaldamagemult*0.9).round\n      end\n"
 "      if opponent.hasWorkingAbility(:DAMP) && isConst?(type,PBTypes,:FIRE)\n        finaldamagemult=(finaldamagemult*0.8).round\n      end\n"
 "      if opponent.hasWorkingAbility(:SHELLARMOR) && pbIsPhysical?(type)\n        finaldamagemult=(finaldamagemult*0.85).round\n      end\n"
 "      if opponent.hasWorkingAbility(:ICESCALES) && pbIsSpecial?(type)\n        finaldamagemult=(finaldamagemult*0.5).round\n      end\n")
# ======================= 083 MoveEffects =======================
t=load('083'); S['083']=re.sub(r"(\n\s+opponent\.pbFreeze)(?=\n)",r"\1(nil,attacker)",t)
rep('083','¡Ha empezado a granizar!','¡Ha empezado a nevar!')
rep('083','# Activa el clima Granizo.\n# Granizo / Hail','# Activa el clima Nieve (antes Granizo; sin daño residual).\n# Nieve / Hail')
# ======================= 084 Battle =======================
rep('084','Sigue granizando...','Sigue nevando...',2)
rep('084','Ha dejado de granizar.','Ha dejado de nevar.')
rep('084','El clima Granizo terminó','El clima Nieve terminó')
rep('084',"if !i.pbHasType?(:ICE) &&\n               !i.hasWorkingAbility(:ICEBODY) &&","if false &&   # Nieve: sin daño residual\n               !i.hasWorkingAbility(:ICEBODY) &&")
rep('084',"      # Healer\n      if i.hasWorkingAbility(:HEALER) && pbRandom(10)<3\n",
 "      # Healer (REM): 1/8 PS propios con estado mayor\n      if i.hasWorkingAbility(:HEALER) && i.status>0 && !i.isFainted? && i.effects[PBEffects::HealBlock]==0\n"
 "        hpgain=i.pbRecoverHP((i.totalhp/8).floor,true)\n"
 "        pbDisplay(_INTL(\"¡{2} de {1} restauró sus PS!\",i.pbThis,PBAbilities.getName(i.ability))) if hpgain>0\n      end\n"
 "      if i.hasWorkingAbility(:HEALER) && pbRandom(10)<3\n")
rep('084',"      # Pesadilla  /  Nightmare\n",
 "      # Heladura (REM): daño residual 1/16\n      if i.status==PBStatuses::FROZEN\n        if !i.hasWorkingAbility(:MAGICGUARD)\n          PBDebug.log(\"[Daño por estado] #{i.pbThis} recibió daño por la heladura\")\n          i.pbReduceHP((i.totalhp/16).floor)\n        end\n        i.pbContinueStatus\n      end\n"
 "      # Pesadilla  /  Nightmare\n")
# ======================= escritura =======================
for n,t in S.items():
    if CRLF[n]: t=t.replace('\n','\r\n')
    open(F(n),'wb').write(t.encode('utf-8'))
print('OK',sorted(S))
