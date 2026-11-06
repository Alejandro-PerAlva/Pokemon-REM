# encoding: UTF-8
# Eventos de PUEBLO ALBOR (mapas 2 Pueblo Albor, 3 Casa Player, 4 Laboratorio, 5 Casas).
# Uso (desde la raíz del proyecto):  ruby tools/events/albor_events.rb [--dry]
# Solo AÑADE eventos con prefijo «ALBOR_» (idempotente: los reemplaza); no toca los eventos existentes ni los scripts.
# Estados de la historia local V121 (H_PUEBLO_ALBOR):
#   0 inicio · 1 Pokévial recibido (sales de casa) · 2 Lucián te ha recibido en la verja · 3 escena del laboratorio vista
#   (puedes elegir inicial) · 4 inicial elegido (Pía da objetos; Lucián y Guiomar te esperan en el patio) · 5 duelo hecho (puedes partir).
# Misión local V201 (M_PUEBLO_ALBOR): 0 sin empezar · 1 aceptada · 3 Pokémon rescatado (entregar) · 99 completada.
require File.join(File.dirname(File.expand_path(__FILE__)), 'rem_event_lib.rb')
DRY = ARGV.include?('--dry')
include REMEv
V_STORY = 121; V_QUEST = 201; SW_VIAL = 696; SW_MAP = 694; SW_CANDY = 697; SW_PIA = 400

def n(l, text); l.say(text); end
def pg(*a); REMEv.page(*a); end
def loc(l, text); l.comment("[UBICACIÓN] " + text); end
def mov(l, text); l.comment("[MOVIMIENTO] " + text); end

# --------------------------------------------------------------------------- MAPA 3: CASA PLAYER
casa = []

# Despertar (Autorun, una sola vez)
l = L.new
loc(l, "Cualquier casilla de la habitación del jugador: es Autorun y corre solo al llegar (inicio de partida).")
l.script("pbAdvanceMilestone(1)")
l.say("Te despierta el olor a pan. La luz entra sesgada por la ventana de tu cuarto y dibuja en el suelo un rectángulo amarillo.")
l.say("Abajo se oye el tintineo de las tazas: tu madre, Amparo, ya ha puesto la mesa.")
l.say("Hoy es el día.")
mov(l, "Opcional: el jugador baja de la cama / camina hasta la puerta de la habitación.")
l.self_sw('A')
casa << ["ALBOR_Despertar", [pg(trig: 3, list: l), pg(cond: { :self => 'A' })]]

# Amparo (3 páginas: base, 3 medallas, 6 medallas)
def amparo_base(l)
  l.ifelse(:sw, SW_VIAL, true) {
    [lambda { |b|
      b.say("Amparo: ¿Todo bien, cariño? La casa no se mueve, ya lo sabes.")
      b.if_(:var, 105, :lt, 6) { |c|
        c.say("Amparo: Acuérdate: cuando hayas ganado tres medallas, pásate a verme; y otra vez con seis. Ya veré qué puedo hacer por el Pokévial.")
      }
    }, lambda { |b|
      b.say("Amparo: Hoy es el día. No te he llamado para que te quedes mirando el techo.")
      b.say("Desayunas con prisa. Ella te ajusta el cuello de la chaqueta, te coloca un mechón rebelde y te mira un segundo de más.")
      b.say("Amparo: Anda, ve. Y antes de salir, pasa por la puerta: tengo algo para ti.")
    }]
  }
end
def amparo_mejora(l, n)
  frase = (n == 2) ? "Tres medallas ya... Dame ese Pokévial, anda." : "Seis medallas. Se me hace raro verte tan mayor. Trae, trae ese Pokévial."
  sig = (n == 2) ? "Amparo: Vuelve a verme cuando lleves seis medallas." : "Amparo: Ya no puedo darle más de sí. Lo demás es cosa tuya."
  l.ifelse(:script, "pbRemVialMax<#{n} && $PokemonBag.pbQuantity(getConst(PBItems,:POKEVIAL))>0") {
    [lambda { |b|
      b.say("Amparo: #{frase}")
      b.say("Amparo hace algo con el frasco —un ajuste, un lazo, una palabra que no llega a decir— y te lo devuelve más pesado.")
      b.script("pbRemVialSetMin(#{n})\npbRemVialRefill\npbRemEnsureVialVars")
      b.say("\\se[ItemGet]¡El Pokévial ahora tiene #{n} cargas!")
      b.say(sig)
    }, lambda { |b| amparo_base(b) }]
  }
end
l0 = L.new; loc(l0, "Cocina / comedor de la casa, junto a la mesa."); amparo_base(l0)
l1 = L.new; amparo_mejora(l1, 2)
l2 = L.new; amparo_mejora(l2, 3)
casa << ["ALBOR_Amparo", [pg(gfx: 'npc001', list: l0), pg(cond: { :var => [105, 3] }, gfx: 'npc001', list: l1),
                           pg(cond: { :var => [105, 6] }, gfx: 'npc001', list: l2)]]

# Padre: punto de curación del pueblo
l = L.new
loc(l, "Salón de la casa (sitio fijo del Padre: es el punto de curación de Pueblo Albor).")
l.ifelse(:var, V_STORY, :lt, 1) {
  [lambda { |b| b.say("Padre: Ve a despedirte de tu madre. Yo ya me he despedido de ti, que me conozco y me pongo blando.") },
   lambda { |b|
     b.say("Padre: ¿Ya te vas, campeón? Déjame echarle un vistazo a tu equipo.")
     b.ifelse(:script, "$Trainer.party.length>0 && Kernel.pbConfirmMessage(_INTL(\"¿Quieres que tu padre cure a tu equipo?\"))") {
       [lambda { |c|
         c.say("Tu padre se arremanga y atiende a tus compañeros con manos tranquilas.")
         c.script("pbHealAll\nKernel.pbSetPokemonCenter")
         c.say("Padre: Listo. Como nuevos. Si te cansas, vuelve a casa: aquí siempre os dejaremos como nuevos, a ti y a los tuyos.")
       }, lambda { |c| c.say("Padre: Cuando quieras. Esta casa siempre tiene la luz encendida.") }]
     }
   }]
}
casa << ["ALBOR_Padre (curación)", [pg(gfx: 'npc002', list: l)]]

# Despedida en la puerta: entrega del Pokévial (1 carga)
l = L.new
loc(l, "Casilla justo ANTES de la puerta de salida (la que está sobre el evento PC de salida de la casa). Es de contacto con el jugador.")
mov(l, "Amparo corre hasta la puerta y se pone frente al jugador; el jugador se gira hacia ella.")
l.say("Amparo: ¡Espera! No te vas sin esto.")
l.ifelse(:script, "Kernel.pbReceiveItem(:POKEVIAL)") {
  [lambda { |b|
    b.script("pbRemEnsureVialVars")
    b.sw(SW_VIAL)
    b.script("pbSetStoryVar(:PUEBLO_ALBOR,1) if pbStoryVar(:PUEBLO_ALBOR)<1")
    b.say("Amparo: Es un Pokévial. Tiene una carga y se rellena solo en cualquier lugar donde curen a tu equipo.")
    b.say("Amparo: Cuando hayas ganado tres medallas, pasa a verme; y otra vez con seis. Ya veré qué puedo hacer por él.")
    b.say("Amparo: Vuelve cuando quieras. La casa no se mueve.")
    b.say("Tu padre, apoyado en el marco del salón, te guiña un ojo.")
    b.say("Padre: Si te cansas, vuelve a casa. Aquí siempre os dejaremos como nuevos, a ti y a los tuyos.")
  }, lambda { |b|
    b.say("Amparo: Pero si llevas la mochila llena... Haz sitio y vuelve a por él.")
    b.script("pbMoveRoute($game_player,[PBMoveRoute::Up],true)")
  }]
}
casa << ["ALBOR_Despedida (Pokévial)", [pg(trig: 1, list: l), pg(cond: { :sw => SW_VIAL })]]

# --------------------------------------------------------------------------- MAPA 2: PUEBLO ALBOR
pueblo = []

# Lucián en la verja
l = L.new
loc(l, "Junto a la verja del laboratorio (a los pies de la loma).")
l.say("Lucián: Llegas ocho minutos tarde. Probablemente no es grave. Aunque... con un setenta por ciento de confianza, Guiomar ya está dentro.")
l.say("Lucián se ajusta las gafas torcidas y abre la libreta que lleva bajo el brazo.")
l.say("Lucián: Hoy empiezo el registro de especies. Completar la Pokédex es solo cuestión de método. Vamos, que el Profesor nos espera.")
mov(l, "Lucián sube la loma hasta la puerta del laboratorio y entra (al cambiar V121 a 2 su sprite desaparece del patio).")
l.script("pbSetStoryVar(:PUEBLO_ALBOR,2)")
pueblo << ["ALBOR_Lucián (verja)", [pg, pg(cond: { :var => [V_STORY, 1] }, gfx: 'trchar002', list: l), pg(cond: { :var => [V_STORY, 2] })]]

# Guiomar en el patio
l = L.new
loc(l, "Patio delante del laboratorio, junto a Lucián (aparece cuando eliges inicial).")
l.say("Guiomar: ¡Vamos, vamos! ¡Que el combate empiece ya, que yo estoy lista para marcharme!")
l.say("Guiomar: ¡Los ocho gimnasios y la mejor de todo Oniria! ¡Y lo digo tres veces si hace falta!")
pueblo << ["ALBOR_Guiomar (patio)", [pg, pg(cond: { :var => [V_STORY, 4] }, gfx: 'trchar003', list: l), pg(cond: { :var => [V_STORY, 5] })]]

# Lucián en el patio: combate tutorial (Nv 5)
l = L.new
loc(l, "Patio delante del laboratorio (frente al jugador al salir).")
l.ifelse(:sw, SW_CANDY, true) {
  [lambda { |b|
    b.say("Lucián: Había una probabilidad bastante alta de que salieras ahora. Quiero comprobar cuánto hemos mejorado desde que recibimos a nuestros compañeros. ¿Un combate amistoso?")
    b.ifelse(:script, "Kernel.pbConfirmMessage(_INTL(\"¿Aceptas el combate amistoso con Lucián?\"))") {
      [lambda { |c|
        c.script(<<'RB')
idx=pbPiaIndex(pbPiaFirst)
g=idx/3
t=idx%3
lt=[1,2,0][t]
pid=g*3+lt
nm=PBSpecies.getName(getConst(PBSpecies,REM_PIA_STARTERS[pid][0]))
Kernel.pbMessage(_INTL("Lucián se ajusta las gafas, elige con cuidado el Pokémon con ventaja de tipo y te explica con voz firme por qué va a ganar."))
Kernel.pbMessage(_INTL("Lucián: Mi compañero es {1}. Según mis cálculos, la ventaja de tipo es evidente.",nm))
tr=(pbLoadTrainer(:RIVAL_M,"Lucián",pid) rescue nil)
if tr
  pbTrainerBattle(:RIVAL_M,"Lucián",_I("Lucián: Vaya... mi estimación era incorrecta. Lo anoto."),false,pid,true)
else
  Kernel.pbMessage(_INTL("(Aviso de desarrollo: falta el entrenador RIVAL_M «Lucián» con ID de equipo {1} en trainers.txt; ver proposed_trainers_albor.txt.)",pid)) if $DEBUG
end
RB
        c.say("Lucián pierde el primer turno y lo anota.")
        c.say("Lucián: Es un buen dato. Lo registro.")
        c.say("Guiomar: ¡Pues yo me voy ya! ¡Nos vemos en el gimnasio! ¡El que llegue segundo invita!")
        mov(c, "Guiomar sale corriendo del patio hacia la Ruta 1 (al cambiar V121 a 5 su sprite desaparece).")
        c.say("Lucián recoge su libreta.")
        c.say("Lucián: Probablemente nos alcanzará en el primer cruce.")
        c.say("Sales a la loma. Hacia el noreste, una cueva cuya entrada está sellada con tablones; hacia el oeste, el mar, y una ruta que solo se atraviesa con barco. Hacia el sur, la Ruta 1.")
        c.say("Detrás de ti, Amparo agita la mano desde la puerta, y la mano del Profesor, desde la ventana del laboratorio, abre y cierra la tapa de su reloj.")
        c.script("pbSetStoryVar(:PUEBLO_ALBOR,5)\npbAdvanceMilestone(1)")
        mov(c, "Lucián se despide y echa a andar tras Guiomar hacia el sur (al cambiar V121 a 5 su sprite desaparece).")
      }, lambda { |c| c.say("Lucián: Tómate tu tiempo. Lo he anotado como «pendiente».") }]
    }
  }, lambda { |b|
    b.say("Lucián: Pía quería darte algo antes de que salgas. Pasa por su mostrador y luego hablamos.")
  }]
}
pueblo << ["ALBOR_Lucián (patio, combate tutorial)", [pg, pg(cond: { :var => [V_STORY, 4] }, gfx: 'trchar002', list: l), pg(cond: { :var => [V_STORY, 5] })]]

# Bloqueos de salida por la Ruta 1 (x4)
4.times do |i|
  l = L.new
  loc(l, "Fila justo ENCIMA de las salidas a Ruta 1 (la fila anterior a los eventos R1 de la fila inferior del mapa), una copia por cada columna de salida (4).") if i == 0
  l.if_(:var, V_STORY, :lt, 5) { |b|
    b.ifelse(:var, V_STORY, :lt, 1) { [lambda { |c| c.say("Tu madre quería decirte algo antes de que te vayas.") }, lambda { |c|
      c.ifelse(:var, V_STORY, :lt, 4) { [lambda { |d| d.say("Todavía no tienes compañero: el Profesor te espera en el laboratorio.") },
        lambda { |d| d.say("Lucián te espera en el patio del laboratorio. Y Pía tiene algo para ti.") }] }
    }] }
    b.script("pbMoveRoute($game_player,[PBMoveRoute::Up],true)")
  }
  pueblo << ["ALBOR_Bloqueo salida Ruta 1 (#{i + 1}/4)", [pg(trig: 1, list: l)]]
end

# Cueva sellada (Ruta 20) y mar (Ruta 13)
l = L.new
loc(l, "Entrada de la cueva del noreste (Ruta 20), sobre los tablones.")
l.say("Una entrada de cueva sellada con tablones clavados a conciencia. Por las rendijas sopla un aire frío y antiguo.")
l.say("Parece que, por ahora, no hay forma de abrirla.")
pueblo << ["ALBOR_Cueva sellada (Ruta 20)", [pg(list: l)]]
l = L.new
loc(l, "Orilla oeste del pueblo (hacia la Ruta 13), como cartel en el embarcadero.")
l.say("Hacia el oeste, el mar. Una ruta marítima que solo se atraviesa en barco.")
l.say("Por ahora no hay ninguna embarcación disponible.")
pueblo << ["ALBOR_Mar oeste (Ruta 13)", [pg(list: l)]]

# Carteles
l = L.new; loc(l, "Plaza, a la entrada del pueblo desde la Ruta 1.")
l.say("PUEBLO ALBOR — Casas bajas, un olmo viejo y la luz más temprana de Oniria.")
pueblo << ["ALBOR_Cartel del pueblo", [pg(list: l)]]
l = L.new; loc(l, "Verja / puerta del laboratorio (loma).")
l.say("LABORATORIO POKÉMON DE ONIRIA — Prof. Ambrosio Valdemar. Llame antes de entrar. (Pía dice que no hace falta.)")
pueblo << ["ALBOR_Cartel del laboratorio", [pg(list: l)]]

# Flautista de ambientación
l = L.new; loc(l, "Cerca del olmo de la plaza (NPC de ambientación).")
l.ifelse(:var, V_STORY, :lt, 5) {
  [lambda { |b| b.say("Aldeano: Tocar la flauta antes del desayuno da buena suerte. Lo dice mi abuela, y mi abuela casi nunca falla.") },
   lambda { |b| b.say("Aldeano: Si vuelves por aquí, te tocaré algo más animado. Esta melodía es solo de las mañanas tranquilas.") }]
}
pueblo << ["ALBOR_Aldeano flautista", [pg(gfx: 'npc003', list: l)]]

# --- Misión local: «El Pokémon del pozo» ---
# Anciano (Don Anselmo, nombre provisional)
l = L.new
loc(l, "Junto al pozo del pueblo (el anciano que ha perdido a su Pokémon).")
l.ifelse(:var, V_QUEST, :eq, 0) {
  [lambda { |b|
    b.say("Anciano: Ay, hijo... mi Wooper se cayó al pozo esta mañana, mientras bebía. Con estas rodillas no puedo bajar a buscarlo.")
    b.ifelse(:script, "Kernel.pbConfirmMessage(_INTL(\"¿Ayudas al anciano a rescatar a su Pokémon?\"))") {
      [lambda { |c|
        c.script("pbSetQuestState(:PUEBLO_ALBOR,1)")
        c.say("Anciano: ¡Gracias, gracias! Pero ten cuidado: lleva rato llorando ahí abajo y estará aterrado. No te lo tomes a mal si te ataca.")
        c.say("Anciano: El pozo está ahí mismo. Tráemelo de vuelta, por favor.")
      }, lambda { |c| c.say("Anciano: Lo entiendo, hijo. Seguiré esperando por aquí.") }]
    }
  }, lambda { |b|
    b.ifelse(:var, V_QUEST, :eq, 1) {
      [lambda { |c| c.say("Anciano: Se oye ahí abajo, ¿verdad? Pobrecito. Baja con cuidado, y no tengas prisa por tranquilizarlo.") },
       lambda { |c|
         c.ifelse(:var, V_QUEST, :eq, 3) {
           [lambda { |d|
             d.say("Sacas del pozo al Wooper, aún tembloroso, y se lo pones en los brazos al anciano.")
             d.say("Anciano: ¡Mi Wooper! ¡Mi pequeño! Ya está, ya pasó...")
             d.say("Anciano: No sé cómo agradecértelo. Toma, esto es lo único que tengo a mano.")
             d.ifelse(:script, "Kernel.pbReceiveItem(:PARLYZHEAL)") {
               [lambda { |e|
                 e.script("pbSetQuestState(:PUEBLO_ALBOR,99)")
                 e.say("Anciano: Cuídate mucho ahí fuera. Y vuelve a saludarnos cuando quieras.")
               }, lambda { |e| e.say("Anciano: Ay, tu mochila está llena. Haz sitio y vuelve, que no se me olvida.") }]
             }
           }, lambda { |d|
             d.say("Anciano: Mi Wooper vuelve a jugar con el agua del abrevadero. Ha sido gracias a ti.")
           }]
         }
       }]
    }
  }]
}
pueblo << ["ALBOR_Anciano (misión del pozo)", [pg(gfx: 'npc004', list: l)]]

# Wooper del pozo (mapa 14 «Pozo», hijo de Pueblo Albor). La entrada ya existe (evento E de Albor en el pozo); aquí vive el combate.
pozo = []
l = L.new
loc(l, "Orilla del fondo del pozo (mapa 14), cerca del agua.")
l.say("Del agua oscura llegan quejidos y chapoteos. Entre la penumbra brillan unos ojos aterrados.")
l.ifelse(:script, "$Trainer.ablePokemonCount>0") {
  [lambda { |c|
    c.say("¡El Pokémon del anciano, asustado, se abalanza sobre ti!")
    mov(c, "Opcional: el Wooper salta desde el agua hacia el jugador antes del combate.")
    c.script(<<'RB')
pbWildBattle(:WOOPER,5,1,false,false)
d=$game_variables[1]
if d==4
  for i in (0...$Trainer.party.length).to_a.reverse
    pk=$Trainer.party[i]
    if pk && pk.species==PBSpecies::WOOPER && pk.level==5
      $Trainer.party.delete_at(i)
      break
    end
  end
  Kernel.pbMessage(_INTL("El Pokémon del anciano no es para ti: lo sueltas con cuidado."))
  d=1
end
if d==1
  Kernel.pbMessage(_INTL("El Wooper, agotado, se deja coger en brazos. Poco a poco deja de temblar."))
  Kernel.pbMessage(_INTL("Ahora sube por la soga y llévaselo a su dueño."))
  pbSetQuestState(:PUEBLO_ALBOR,3)
elsif d!=2
  Kernel.pbMessage(_INTL("El Wooper se hunde en el agua oscura. Tendrás que bajar otra vez."))
end
RB
  }, lambda { |c| c.say("No puedes acercarte a un Pokémon asustado sin un compañero en condiciones. Sube y vuelve cuando tu equipo esté sano.") }]
}
pozo << ["ALBOR_Wooper del pozo (misión)", [pg, pg(cond: { :var => [V_QUEST, 1] }, gfx: '194', list: l), pg(cond: { :var => [V_QUEST, 3] })]]

# --------------------------------------------------------------------------- MAPA 4: LABORATORIO
lab = []

# Escena de entrada (Autorun, una vez)
l = L.new
loc(l, "Cualquier casilla del laboratorio (Autorun). Colocar Pía, Guiomar y Lucián en sus eventos de sitio; Ambrosio baja por las escaleras.")
l.script("pbSetStoryVar(:PUEBLO_ALBOR,2) if pbStoryVar(:PUEBLO_ALBOR)<2")
l.say("Cuando cruzas la puerta del laboratorio, Guiomar da botes en medio de la sala, con la coleta rojiza desordenada, las vendas de las manos y una tirita nueva en cada rodilla. Ha venido corriendo desde Pueblo Heliar.")
l.say("Guiomar: ¡Por fin! ¡Creía que os habíais echado atrás!")
l.say("Pía, la ayudante del Profesor, intenta que baje la voz. No lo consigue.")
l.say("Pía: Guiomar, por favor... el Profesor está a punto de bajar.")
mov(l, "Ambrosio baja las escaleras (AS del laboratorio) con lentitud hasta el centro de la sala.")
l.say("Entonces aparece él. Ambrosio Valdemar baja las escaleras con la lentitud de quien nunca ha tenido prisa. Debajo de la bata impoluta lleva un traje oscuro de cuello alto, de otro siglo.")
l.say("En la mano izquierda sostiene un reloj de bolsillo de oro cuya esfera atraviesa una fina grieta. Lo consulta, lo guarda, y sonríe.")
l.say("Ambrosio: Mis queridos. Qué día tan hermoso para empezar.")
l.say("Les habla del vínculo entre las personas y las criaturas que las acompañan. Lo hace con ternura, con las manos entrelazadas a la espalda, y de pronto se detiene, como si hubiera encontrado una palabra dentro de otra.")
l.say("Ambrosio: Últimamente he estado estudiando ciertos... desequilibrios en los sueños. Pero no es día para eso. Los vínculos, queridos míos, despiertan todo lo que duerme. Recordadlo.")
l.say("Cada uno dice por qué viaja.")
l.say("Lucián: Voy a completar la Pokédex. Es solo cuestión de método.")
l.say("Guiomar: ¡Voy a ganar los ocho gimnasios y a ser la mejor! ¡Los ocho gimnasios y ser la mejor! ¡LA MEJOR!")
l.say("Tú no dices nada: sonríes, y los dos te miran como si hubieras dicho lo más sensato.")
l.say("Ambrosio: Sobre las mesas os esperan dieciocho compañeros. Elegid con el corazón. Tú primero.")
l.say("Pía: Cuando hayas elegido, pasa por mi mostrador: tengo algo para ti.")
l.script("pbSetStoryVar(:PUEBLO_ALBOR,3)")
l.self_sw('A')
lab << ["ALBOR_Escena del laboratorio", [pg(cond: { :var => [V_STORY, 1] }, trig: 3, list: l), pg(cond: { :self => 'A' })]]

# Lucián y Guiomar dentro del laboratorio (visibles en V121 2..3)
[['Lucián', 'trchar002', "Lucián: Tengo anotados dieciséis datos útiles sobre los iniciales. Elige tú primero, que luego yo elijo con ventaja."],
 ['Guiomar', 'trchar003', "Guiomar: ¡Elige ya, elige ya! ¡Yo no me puedo estar quieta!"]].each do |nom, gfx, txt|
  l = L.new; loc(l, "Sala principal del laboratorio, cerca de las mesas de los iniciales."); l.say(txt)
  lab << ["ALBOR_#{nom} (laboratorio)", [pg, pg(cond: { :var => [V_STORY, 2] }, gfx: gfx, list: l), pg(cond: { :var => [V_STORY, 4] })]]
end

# Ambrosio (Profesor)
l = L.new
loc(l, "Sala principal del laboratorio (cerca de las escaleras o del centro de la sala).")
l.ifelse(:var, V_STORY, :lt, 4) {
  [lambda { |b| b.say("Ambrosio: Cuando quieras. Los compañeros no tienen prisa... aunque yo, a veces, sí.") },
   lambda { |b|
     b.ifelse(:var, V_STORY, :lt, 5) {
       [lambda { |c| c.say("Ambrosio: Pasad por el patio, queridos. Lucián tiene ganas de probar sus apuntes.") },
        lambda { |c|
          c.say("Ambrosio consulta su reloj de bolsillo, lo guarda y sonríe.")
          c.say("Ambrosio: Los vínculos despiertan todo lo que duerme. Recuérdalo, y viajad juntos.")
        }]
     }
   }]
}
lab << ["ALBOR_Ambrosio (Profesor)", [pg(gfx: 'trchar004', list: l)]]

# Pía: mostrador (objetos de bienvenida, panel de misiones, reclamar inicial, hitos de captura)
hitos = []
shops = File.read('PBS/rem_shops.txt', :encoding => 'UTF-8').gsub("\r\n", "\n")
info = {}
shops.scan(/^MissionInfo(\d+) = (\w+),(\w+),(\w+),(.*)$/) { |nn, act, tipo, lk, req| info[nn.to_i] = [act, tipo] }
shops.scan(/^Mission(\d+) = (\d+),(\w+),(\d+),([^,]*),/) do |nn, cap, item, qty, titulo|
  i = info[nn.to_i]; next if !i || i[1] != 'HITO' || cap.to_i == 0
  act = { 'I' => 1, 'II' => 2, 'III' => 3, 'IV' => 4, 'V' => 5 }[i[0]] || 1
  hitos << "[#{nn},#{cap},:#{item},#{qty},#{act},\"#{titulo.gsub('"', '')}\"]"
end
raise 'sin misiones de hito' if hitos.length < 10
l = L.new
loc(l, "Mostrador de Pía, en la sala principal.")
l.ifelse(:var, V_STORY, :lt, 4) {
  [lambda { |b|
    b.say("Pía: ¡Bienvenido al laboratorio! En cuanto elijas a tu compañero, pasa por mi mostrador, que tengo cosas para ti.")
  }, lambda { |b|
    b.if_(:sw, SW_MAP, false) { |c|
      c.say("Pía: Cuando salgas de aquí vas a necesitar esto: el Mapa de Oniria. Lo he dibujado yo misma, así que no te fíes de las escalas.")
      c.script("Kernel.pbReceiveItem(:TOWNMAP)")
      c.sw(SW_MAP)
    }
    b.if_(:sw, SW_CANDY, false) { |c|
      c.say("Pía: Y esto es para ti: un Caramelo Infinito. Sube un nivel cada vez que lo uses, sin límite de usos, hasta el tope de nivel.")
      c.script("Kernel.pbReceiveItem(:INFINITECANDY)")
      c.sw(SW_CANDY)
    }
    b.script("$game_switches[400]=true\n$game_map.need_refresh=true")
    b.script(<<RB)
hs_hitos=[#{hitos.join(",\n")}]
loop do
  c=Kernel.pbMessage(_INTL("Pía: ¿Qué necesitas?"),[_INTL("Misiones de Pía"),_INTL("Entregas de captura"),_INTL("Reclamar un inicial"),_INTL("Nada, gracias")],4)
  if c==0
    pbPiaQuestPanel
  elsif c==1
    owned=$Trainer.pokedexOwned
    d=(pbRemPia[:hito]||={})
    ready=hs_hitos.select{|h| !d[h[0]] && owned>=h[1] && $game_variables[101]>=h[4]}
    if ready.length==0
      Kernel.pbMessage(_INTL("Pía: Llevas {1} especies capturadas. Todavía no tienes ninguna entrega pendiente; sigue anotando en el cuaderno.",owned))
    else
      names=ready.map{|h| h[5]}
      names.push(_INTL("Cancelar"))
      k=Kernel.pbShowCommands(nil,names,-1)
      if k>=0 && k<ready.length
        h=ready[k]
        Kernel.pbMessage(_INTL("Pía: ¡Misión «{1}» cumplida! Toma tu recompensa.",h[5]))
        d[h[0]]=true if Kernel.pbReceiveItem(h[2],h[3])
      end
    end
  elsif c==2
    pbClaimPiaStarter
  else
    break
  end
end
RB
  }]
}
lab << ["ALBOR_Pía (mostrador)", [pg(gfx: 'npc005', list: l)]]

# Los 18 iniciales (Gen 1-6): sprite del propio Pokémon, visibles con V121 = 3 y retirados en V121 >= 4
iniciales = [
  ['BULBASAUR', '001', 'Planta'], ['CHARMANDER', '004', 'Fuego'], ['SQUIRTLE', '007', 'Agua'],
  ['CHIKORITA', '152', 'Planta'], ['CYNDAQUIL', '155', 'Fuego'], ['TOTODILE', '158', 'Agua'],
  ['TREECKO', '252', 'Planta'], ['TORCHIC', '255', 'Fuego'], ['MUDKIP', '258', 'Agua'],
  ['TURTWIG', '387', 'Planta'], ['CHIMCHAR', '390', 'Fuego'], ['PIPLUP', '393', 'Agua'],
  ['SNIVY', '495', 'Planta'], ['TEPIG', '498', 'Fuego'], ['OSHAWOTT', '501', 'Agua'],
  ['CHESPIN', '650', 'Planta'], ['FENNEKIN', '653', 'Fuego'], ['FROAKIE', '656', 'Agua']
]
frase = { 'Planta' => 'un compañero tranquilo que busca el sol', 'Fuego' => 'una llama inquieta que no sabe estarse quieta',
          'Agua' => 'un compañero fresco, curioso y siempre en movimiento' }
iniciales.each_with_index do |(sym, spr, tipo), idx|
  l = L.new
  loc(l, "Mesas del laboratorio, junto a su pareja de región (3 por mesa: Planta, Fuego, Agua). Región #{idx / 3 + 1}.")
  l.script(<<RB)
sp=PBSpecies.getName(getConst(PBSpecies,:#{sym}))
pbPlayCry(getConst(PBSpecies,:#{sym})) rescue nil
Kernel.pbMessage(_INTL("{1}, de tipo #{tipo}: #{frase[tipo]}.",sp))
if Kernel.pbConfirmMessage(_INTL("¿Quieres elegir a {1} como tu compañero?",sp))
  if pbAddPokemon(:#{sym},5)
    pbPiaMarkFirst(:#{sym})
    $game_switches[400]=true
    pbRemRefreshFollower
    Kernel.pbMessage(_INTL("El tuyo te mira desde la palma abierta, pequeño, de nivel 5, con una curiosidad idéntica a la tuya."))
    Kernel.pbMessage(_INTL("Ambrosio inclina la cabeza."))
    t=#{idx % 3}
    g=#{idx / 3}
    lt=[1,2,0][t]
    gt=3-t-lt
    nl=PBSpecies.getName(getConst(PBSpecies,REM_PIA_STARTERS[g*3+lt][0]))
    ng=PBSpecies.getName(getConst(PBSpecies,REM_PIA_STARTERS[g*3+gt][0]))
    Kernel.pbMessage(_INTL("Lucián: Yo me quedo con {1}. La ventaja de tipo es del noventa y cinco por ciento, aproximadamente.",nl))
    Kernel.pbMessage(_INTL("Guiomar: ¡Pues yo con {1}! ¡Es clavado a mí!",ng))
    Kernel.pbMessage(_INTL("Ambrosio: Viajad juntos. Los tres. Prometédmelo."))
    Kernel.pbMessage(_INTL("Lucián: Prometido. Con un noventa por ciento de seguridad."))
    Kernel.pbMessage(_INTL("Guiomar: ¡Prometido! ¡Y el que llegue segundo al gimnasio invita!"))
    Kernel.pbMessage(_INTL("Tú asientes. No hace falta decir nada más."))
    pbSetStoryVar(:PUEBLO_ALBOR,4)
    pbAdvanceMilestone(1)
  end
end
RB
  lab << ["ALBOR_Inicial #{idx + 1} #{sym}", [pg, pg(cond: { :var => [V_STORY, 3] }, gfx: spr, list: l), pg(cond: { :var => [V_STORY, 4] })]]
end

# --------------------------------------------------------------------------- MAPA 5: CASAS (2 interiores)
casas = []
l = L.new
loc(l, "Casa 1 (mitad superior del mapa 5): salón, junto a la mesa.")
l.ifelse(:var, V_STORY, :lt, 5) {
  [lambda { |b| b.say("Madre de Lucián: Lucián salió volando con su libreta. Dijo que había un setenta por ciento de probabilidades de llegar tarde. Llegó tarde.") },
   lambda { |b| b.say("Madre de Lucián: Mi Lucián ya es todo un investigador. Cuídamelo por ahí, que es capaz de olvidarse de comer por anotar un dato.") }]
}
casas << ["ALBOR_Madre de Lucián", [pg(gfx: 'npc006', list: l)]]
l = L.new
loc(l, "Casa 2 (mitad inferior del mapa 5): cocina, junto a la ventana.")
l.ifelse(:var, V_QUEST, :eq, 0) {
  [lambda { |b| b.say("Doña Remedios: El pobre Don Anselmo pasa las mañanas junto al pozo, con su Wooper. Siempre se les ve juntos.") },
   lambda { |b|
     b.ifelse(:var, V_QUEST, :eq, 99) {
       [lambda { |c| c.say("Doña Remedios: Me han dicho que rescataste al Wooper del pozo. En este pueblo todo se sabe, y casi siempre antes de que ocurra.") },
        lambda { |c| c.say("Doña Remedios: ¿Has bajado ya al pozo? Con ese Wooper asustado, ve con cuidado, que muerde.") }]
     }
   }]
}
casas << ["ALBOR_Doña Remedios", [pg(gfx: 'npc007', list: l)]]

# --------------------------------------------------------------------------- APLICAR
{ 2 => pueblo, 3 => casa, 4 => lab, 5 => casas, 14 => pozo }.each do |mid, defs|
  placed = REMEv.apply(mid, 'ALBOR_', 'albor_events', defs, DRY)
  puts "Map#{'%03d' % mid}: #{placed.length} eventos #{DRY ? '(dry)' : 'escritos'}"
  placed.each { |id, nm, x, y| puts format('   ev%-3d (%2d,%2d) %s', id, x, y, nm) }
end
