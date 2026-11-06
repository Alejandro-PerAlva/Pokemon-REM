#===============================================================================
# REM_Events — hitos, tope de nivel y variables de eventos. GENERADO por
# tools/rebalance/phase1/build_event_architecture.py; no editar a mano.
# IDs: Variables 50/101-119/121-184/201-240; Interruptores 501-820 (ver PBS/rem_variables_switches.txt).
#===============================================================================
REM_VAR_CAP=50
REM_VAR_ACTO=101
REM_VAR_CAPITULO=102
REM_VAR_TRAMO=103
REM_VAR_FRAGMENTOS=104
REM_VAR_MEDALLAS=105
REM_VAR_VIAL_MAX=106
REM_VAR_VIAL_ACTUAL=107
REM_VAR_CAP_NOCHE=111
REM_VAR_HITO_MAX=112
REM_VAR_DOMINANTES=113
REM_VAR_BASES=114
REM_VAR_SIDEQUESTS=115
REM_VAR_LEGENDARIOS=116
REM_VAR_RIVALES=117

# Hito = paso STEP_NN. Fila: [acto, capitulo, tope_dia, tope_noche, medallas, fragmentos, interruptor_jefe]. Hito 69 = Postgame.
REM_MILESTONES=[nil,
 [1,1,9,9,0,0,0],
 [1,2,9,9,0,0,0],
 [1,3,9,9,0,0,0],
 [1,4,13,13,0,0,501],
 [1,5,14,16,0,1,502],
 [1,6,16,19,0,1,503],
 [1,9,16,19,1,1,0],
 [1,8,19,22,1,1,0],
 [1,10,25,25,1,1,504],
 [1,11,25,28,1,1,0],
 [1,12,28,28,2,1,0],
 [1,13,28,33,2,1,0],
 [1,14,28,33,2,1,0],
 [1,15,28,36,2,1,0],
 [1,15,28,39,2,1,505],
 [2,16,31,40,2,1,506],
 [2,17,32,42,2,2,507],
 [2,18,35,43,2,2,508],
 [2,21,38,43,3,2,0],
 [2,20,38,43,3,2,0],
 [2,22,38,46,3,2,509],
 [2,23,41,49,3,2,0],
 [2,24,41,52,3,2,0],
 [2,25,42,52,4,2,0],
 [2,26,45,55,4,2,510],
 [2,27,46,58,4,3,511],
 [2,28,46,60,4,3,0],
 [2,29,49,61,4,3,512],
 [2,30,52,61,5,3,0],
 [3,31,52,63,5,3,0],
 [3,32,55,67,5,4,513],
 [3,33,55,68,5,4,0],
 [3,34,55,68,5,4,0],
 [3,35,55,69,5,4,0],
 [3,36,55,71,5,4,514],
 [3,37,55,71,5,4,0],
 [3,38,55,71,5,4,0],
 [3,39,55,72,5,4,0],
 [3,40,55,72,5,4,515],
 [3,41,55,72,5,4,0],
 [3,44,58,72,6,4,0],
 [3,43,58,74,6,4,0],
 [3,45,58,75,6,4,0],
 [3,46,60,78,6,5,516],
 [4,47,62,81,6,5,517],
 [4,48,64,81,6,5,518],
 [4,49,64,84,6,5,0],
 [4,50,66,84,7,5,0],
 [4,51,66,84,7,5,0],
 [4,52,66,86,7,5,0],
 [4,53,68,87,7,6,519],
 [4,54,69,91,7,6,520],
 [4,55,70,93,7,6,521],
 [4,56,70,93,7,6,0],
 [4,57,70,93,8,6,0],
 [5,58,75,93,8,6,530],
 [5,59,75,93,8,6,522],
 [5,60,75,98,8,6,0],
 [5,61,75,99,8,6,523],
 [5,62,75,99,8,6,0],
 [5,63,76,99,8,6,524],
 [5,64,76,100,8,6,0],
 [5,64,76,100,8,6,0],
 [5,64,76,100,8,6,0],
 [5,64,76,100,8,6,0],
 [5,65,77,100,8,6,525],
 [5,66,80,100,8,6,526],
 [5,68,80,100,8,6,0],
 [6,68,100,100,8,6,0]]
REM_STORY_VAR={:PUEBLO_ALBOR=>121,:RUTA_01=>122,:PUEBLO_HELIODORO=>123,:GRANJA_APATITA=>124,:BOSQUE_DIOPTASA=>125,:RUTA_02=>126,:CIUDAD_CALCEDONIA=>127,:RUTA_03=>128,:RUTA_04=>129,:PLAYA_SEPIOLITA=>130,:CIUDAD_CALAITA=>131,:RUTA_05=>132,:PUEBLO_PEDERNAL=>133,:LAGO_AMATISTA=>134,:RUTA_06=>135,:CENTRAL_FULGURITA=>136,:RUTA_07=>137,:CIUDAD_MAGNETITA=>138,:ISLA_OPALINA=>139,:ESTEPA_LATERITA=>140,:DESIERTO_HALITA=>141,:RUTA_08=>142,:CIUDAD_NEFRITA=>143,:SENDA_SERPENTINA=>144,:RUINAS_ATACAMITA=>145,:RUTA_09=>146,:PUENTE_DOLOMITA=>147,:CIUDAD_AZABACHE=>148,:RUTA_10=>149,:CASCADAS_TRAVERTINAS=>150,:ACANTILADOS_RODONITA=>151,:PUEBLO_CASITERITA=>152,:RUTA_11=>153,:RUTA_12=>154,:PUEBLO_NACAR=>155,:RUTA_13=>156,:ISLA_OBSIDIANA=>157,:RUTA_14=>158,:RESERVA_PERIDOTO=>159,:CIUDAD_VENTURINA=>160,:RUTA_15=>161,:RUTA_16=>162,:VILLA_ADULARIA=>163,:CIENAGA_LIMONITA=>164,:PUEBLO_ESTEATITA=>165,:RUTA_17=>166,:CIUDAD_ALABASTRO=>167,:RUTA_19=>168,:RUTA_18=>169,:TEMPLO_MOLDAVITA=>170,:LADERA_PORFIDO=>171,:RUTA_20=>172,:RUTA_21=>173,:CIUDAD_REJALGAR=>174,:RUTA_22=>175,:MONTE_AZOGUE=>176,:RUTA_23=>177,:RUTA_24=>178,:GRUTA_HIALINA=>179,:GRUTA_AZURITA=>180,:GRUTA_LABRADORITA=>181,:GRUTA_PIRITA=>182,:CALZADA_CORINDON=>183,:MESETA_CELESTITA=>184}
REM_QUEST_VAR={:PUEBLO_ALBOR=>201,:PUEBLO_HELIODORO=>202,:GRANJA_APATITA=>203,:BOSQUE_DIOPTASA=>204,:CIUDAD_CALCEDONIA=>205,:PLAYA_SEPIOLITA=>206,:CIUDAD_CALAITA=>207,:PUEBLO_PEDERNAL=>208,:LAGO_AMATISTA=>209,:CENTRAL_FULGURITA=>210,:CIUDAD_MAGNETITA=>211,:ISLA_OPALINA=>212,:ESTEPA_LATERITA=>213,:DESIERTO_HALITA=>214,:CIUDAD_NEFRITA=>215,:SENDA_SERPENTINA=>216,:RUINAS_ATACAMITA=>217,:PUENTE_DOLOMITA=>218,:CIUDAD_AZABACHE=>219,:CASCADAS_TRAVERTINAS=>220,:ACANTILADOS_RODONITA=>221,:PUEBLO_CASITERITA=>222,:PUEBLO_NACAR=>223,:ISLA_OBSIDIANA=>224,:RESERVA_PERIDOTO=>225,:CIUDAD_VENTURINA=>226,:VILLA_ADULARIA=>227,:CIENAGA_LIMONITA=>228,:PUEBLO_ESTEATITA=>229,:CIUDAD_ALABASTRO=>230,:TEMPLO_MOLDAVITA=>231,:LADERA_PORFIDO=>232,:CIUDAD_REJALGAR=>233,:MONTE_AZOGUE=>234,:GRUTA_HIALINA=>235,:GRUTA_AZURITA=>236,:GRUTA_LABRADORITA=>237,:GRUTA_PIRITA=>238,:CALZADA_CORINDON=>239,:MESETA_CELESTITA=>240}
REM_QUEST_VIAL={:PUEBLO_ALBOR=>2,:LADERA_PORFIDO=>3}
REM_LEGEND_SWITCH={144=>761,145=>762,146=>763,150=>764,151=>765,243=>766,244=>767,245=>768,249=>769,250=>770,251=>771,377=>772,378=>773,379=>774,380=>775,381=>776,382=>777,383=>778,384=>779,385=>780,386=>781,480=>782,481=>783,482=>784,483=>785,484=>786,485=>787,486=>788,487=>789,488=>790,489=>791,490=>792,491=>793,492=>794,493=>795,494=>796,638=>797,639=>798,640=>799,641=>800,642=>801,643=>802,644=>803,645=>804,646=>805,647=>806,648=>807,649=>808,716=>809,717=>810,718=>811,719=>812,720=>813,721=>814}
REM_DOMINANT_STEPS=[5,17,26,31,44,51]
REM_BASE_STEPS=[15,45,52]
REM_RIVAL_STEPS=[4,6,16,18,25,28,39,53,66]

# Avanza al hito m (1..69): fija tope de nivel, acto, capítulo, medallas, fragmentos y marca los jefes de los hitos anteriores.
# Nunca retrocede: si m es menor que el hito máximo ya alcanzado, no hace nada.
def pbAdvanceMilestone(m)
  m=m.to_i
  m=1 if m<1
  m=REM_MILESTONES.length-1 if m>REM_MILESTONES.length-1
  return false if m<$game_variables[REM_VAR_HITO_MAX]
  if m>1
    for i in 1...m
      b=REM_MILESTONES[i][6]
      $game_switches[b]=true if b>0
    end
    $game_variables[REM_VAR_DOMINANTES]=REM_DOMINANT_STEPS.select{|s| s<m}.length
    $game_variables[REM_VAR_BASES]=REM_BASE_STEPS.select{|s| s<m}.length
    $game_variables[REM_VAR_RIVALES]=REM_RIVAL_STEPS.select{|s| s<m}.length
  end
  e=REM_MILESTONES[m]
  $game_variables[REM_VAR_CAP]=e[2]
  $game_variables[REM_VAR_CAP_NOCHE]=e[3]
  $game_variables[REM_VAR_ACTO]=e[0]
  $game_variables[REM_VAR_CAPITULO]=e[1]
  $game_variables[REM_VAR_TRAMO]=m
  $game_variables[REM_VAR_MEDALLAS]=e[4]
  $game_variables[REM_VAR_FRAGMENTOS]=e[5]
  $game_variables[REM_VAR_HITO_MAX]=m
  pbRemEnsureVialVars
  $game_map.need_refresh=true if $game_map
  return true
end

# Tope de nivel vigente según la hora del juego (noche usa la variable 111).
def pbRemCurrentLevelCap
  night=(PBDayNight.isNight? rescue false)
  v=$game_variables[night ? REM_VAR_CAP_NOCHE : REM_VAR_CAP]
  return v>0 ? v : $game_variables[REM_VAR_CAP]
end

# Sincroniza las variables de Pokévial (106/107) con el estado real del objeto.
def pbRemEnsureVialVars
  $game_variables[REM_VAR_VIAL_MAX]=pbRemVialMax
  $game_variables[REM_VAR_VIAL_ACTUAL]=pbRemVialCharges
end
# Sube el máximo del Pokévial a n cargas como mínimo (idempotente con las misiones n.º 6 y 17 de Pía).
def pbRemVialSetMin(n)
  return if !$PokemonGlobal
  n=[[n,1].max,3].min
  return if pbRemVialMax>=n
  $PokemonGlobal.remVialMax=n
  $PokemonGlobal.remVialCharges=n
  pbRemEnsureVialVars
end

# Historia local (variables H_*, 121-184). loc = símbolo LOC_KEY, p. ej. :PUEBLO_ALBOR.
def pbStoryVar(loc)
  id=REM_STORY_VAR[loc]
  return id ? $game_variables[id] : 0
end
def pbSetStoryVar(loc,n)
  id=REM_STORY_VAR[loc]
  return if !id
  $game_variables[id]=n
  $game_map.need_refresh=true if $game_map
end

# Sidequests locales (variables M_*, 201-240): 0 no iniciada, 1 paso 1, 2 paso 2, 3 lista para entregar, 99 completada.
def pbQuestState(loc)
  id=REM_QUEST_VAR[loc]
  return id ? $game_variables[id] : 0
end
def pbSetQuestState(loc,n)
  id=REM_QUEST_VAR[loc]
  return false if !id
  old=$game_variables[id]
  return false if old==99
  $game_variables[id]=n
  if n==99
    $game_variables[REM_VAR_SIDEQUESTS]+=1
    pbRemVialSetMin(REM_QUEST_VIAL[loc]) if REM_QUEST_VIAL[loc]
  end
  $game_map.need_refresh=true if $game_map
  return true
end

# Legendarios (interruptores 761-814): marca la especie dex como obtenida una sola vez.
def pbMarkLegendary(dex)
  id=REM_LEGEND_SWITCH[dex]
  return false if !id || $game_switches[id]
  $game_switches[id]=true
  $game_variables[REM_VAR_LEGENDARIOS]+=1
  return true
end
