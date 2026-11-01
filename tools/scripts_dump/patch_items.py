exec(open('/Users/a.perezalvarez/Documents/notion/Pokemon-REM/tools/scripts_dump/patch_engine.py').read().split('# ======================= 080 Battler')[0])
# Capa Furtiva (Covert Cloak): ignora efectos secundarios del atacante
rep('080',"(user.hasMoldBreaker || !target.hasWorkingAbility(:SHIELDDUST) ||\n         thismove.doesBypassIgnorableAbilities?)\n        addleffect=thismove.addlEffect",
 "(user.hasMoldBreaker || !target.hasWorkingAbility(:SHIELDDUST) ||\n         thismove.doesBypassIgnorableAbilities?) && !target.hasWorkingItem(:COVERTCLOAK)\n        addleffect=thismove.addlEffect")
rep('080',"if user.hasMoldBreaker || !target.hasWorkingAbility(:SHIELDDUST) ||\n          thismove.doesBypassIgnorableAbilities?\n          canflinch=false",
 "if (user.hasMoldBreaker || !target.hasWorkingAbility(:SHIELDDUST) ||\n          thismove.doesBypassIgnorableAbilities?) && !target.hasWorkingItem(:COVERTCLOAK)\n          canflinch=false")
# Corona Jaqueca (Psyduck): x1,5 a Velocidad
rep('080',"    if self.hasWorkingItem(:CHOICESCARF)\n      speedmult=(speedmult*1.5).round\n    end\n",
 "    if self.hasWorkingItem(:CHOICESCARF)\n      speedmult=(speedmult*1.5).round\n    end\n    if self.hasWorkingItem(:PSYCROWN) && isConst?(self.species,PBSpecies,:PSYDUCK)\n      speedmult=(speedmult*1.5).round\n    end\n")
# Amuleto Puro
rep('081',"  def pbReduceStatWithCause(stat,increment,attacker,cause,showanim=true,showmessage=true,moldbreaker=false,ignoreContrary=false,ignoremirror=false)\n",
 "  def pbReduceStatWithCause(stat,increment,attacker,cause,showanim=true,showmessage=true,moldbreaker=false,ignoreContrary=false,ignoremirror=false)\n"
 "    if hasWorkingItem(:CLEARAMULET) && attacker && attacker.index!=self.index   # Amuleto Puro\n"
 "      @battle.pbDisplay(_INTL(\"¡{2} de {1} evita que le bajen las características!\",pbThis,PBItems.getName(self.item))) if showmessage\n      return false\n    end\n")
# Pluma Hada, Guante de Boxeo, Corona Jaqueca
rep('082',"    if attacker.hasWorkingItem(:ROCKINCENSE) && isConst?(type,PBTypes,:ROCK)\n",
 "    if attacker.hasWorkingItem(:FAIRYFEATHER) && isConst?(type,PBTypes,:FAIRY)\n      damagemult=(damagemult*1.25).round\n    end\n"
 "    if attacker.hasWorkingItem(:PUNCHINGGLOVE) && isPunchingMove?\n      damagemult=(damagemult*1.1).round\n    end\n"
 "    if attacker.hasWorkingItem(:ROCKINCENSE) && isConst?(type,PBTypes,:ROCK)\n")
rep('082',"    if attacker.hasWorkingAbility(:GUTS) &&\n       attacker.status!=0 && pbIsPhysical?(type)\n      atkmult=(atkmult*1.5).round\n    end\n",
 "    if attacker.hasWorkingAbility(:GUTS) &&\n       attacker.status!=0 && pbIsPhysical?(type)\n      atkmult=(atkmult*1.5).round\n    end\n"
 "    if attacker.hasWorkingItem(:PSYCROWN) && isConst?(attacker.species,PBSpecies,:PSYDUCK)\n      atkmult=(atkmult*1.5).round\n    end\n")
rep('082',"    if opponent.hasWorkingItem(:ASSAULTVEST) && pbIsSpecial?(type)\n      defmult=(defmult*1.5).round\n    end\n",
 "    if opponent.hasWorkingItem(:ASSAULTVEST) && pbIsSpecial?(type)\n      defmult=(defmult*1.5).round\n    end\n"
 "    if opponent.hasWorkingItem(:PSYCROWN) && isConst?(opponent.species,PBSpecies,:PSYDUCK)\n      defmult=(defmult*1.5).round\n    end\n")
# Dado Trucado
rep('083',"    ret=5 if attacker.hasWorkingAbility(:SKILLLINK)\n    return ret\n","    ret=5 if attacker.hasWorkingAbility(:SKILLLINK)\n    ret=4+@battle.pbRandom(2) if attacker.hasWorkingItem(:LOADEDDICE) && ret<4   # Dado Trucado: 4-5 golpes\n    return ret\n")
# Corona Jaqueca: no evoluciona
rep('126',"  return -1 if isConst?(pokemon.item,PBItems,:EVERSTONE) &&","  return -1 if isConst?(pokemon.item,PBItems,:PSYCROWN) && isConst?(pokemon.species,PBSpecies,:PSYDUCK)\n  return -1 if isConst?(pokemon.item,PBItems,:EVERSTONE) &&")
# anotación APTO/NO APTO para los nuevos objetos evolutivos
rep('115',":SUNSTONE,:DUSKSTONE,:DAWNSTONE,:SHINYSTONE,:ICESTONE]",":SUNSTONE,:DUSKSTONE,:DAWNSTONE,:SHINYSTONE,:ICESTONE,:RAZORFANG,:RAZORCLAW,:OVALSTONE]")
for n,t in S.items():
    if CRLF[n]: t=t.replace('\n','\r\n')
    open(F(n),'wb').write(t.encode('utf-8'))
print('OK items',sorted(S))
