# encoding: UTF-8
# Eventos de PUEBLO ALBOR (mapas 2 Pueblo Albor, 3 Casa Player, 4 Laboratorio, 5 Casas, 14 Pozo).
# Uso (desde la raíz del proyecto):  ruby tools/events/albor_events.rb [--dry]
# Solo AÑADE/REEMPLAZA eventos con prefijo «ALBOR_» (idempotente). Conserva ID y POSICIÓN de los ya colocados (y sus copias).
#
# BANDAS DE ACTIVACIÓN («baldosas»): eventos sin gráfico y de «contacto con el jugador» (trigger 1): se activan al PISARLOS,
# sin hablar. Se nombran «ALBOR_Banda ...». Se colocan en el punto clave y, si la zona es ancha, se copian (cada copia
# conserva el mismo nombre, y el generador las respeta). Cada banda tiene 3 páginas: antes (vacía o aviso), la escena y después (vacía).
#
# Estados de la historia local V121 (H_PUEBLO_ALBOR):
#   0 inicio · 1 desayuno hecho (banda de la cocina) · 2 despedida y Deportivas recibidas (puedes salir de casa)
#   3 Lucián te ha recibido en la verja · 4 escena del laboratorio vista (puedes elegir inicial)
#   5 inicial elegido (Pía da el Mapa y el Caramelo; Lucián y Guiomar esperan en el patio) · 6 duelo tutorial hecho
#   7 Pokévial recibido de Amparo en la plaza (puedes partir por la Ruta 1).
# Misión local V201 (M_PUEBLO_ALBOR): 0 sin empezar · 1 aceptada · 3 Pokémon rescatado (entregar) · 99 completada.
# La misión solo se ofrece con el inicial ya elegido (V121 >= 5).
require File.join(File.dirname(File.expand_path(__FILE__)), 'rem_event_lib.rb')
DRY = ARGV.include?('--dry')
include REMEv
V_STORY = 121; V_QUEST = 201; SW_VIAL = 696; SW_MAP = 694; SW_CANDY = 697; SW_PIA = 400

def pg(*a); REMEv.page(*a); end
def loc(l, text); l.comment("[UBICACIÓN] " + text); end
def mov(l, text); l.comment("[MOVIMIENTO] " + text); end
def sv(n); "pbSetStoryVar(:PUEBLO_ALBOR,#{n}) if pbStoryVar(:PUEBLO_ALBOR)<#{n}"; end
# Para código Ruby embebido en los scripts de los eventos (texto → línea Kernel.pbMessage).
def rbq(t); t.gsub('\\', '\\\\\\\\').gsub('"', '\\"'); end
def rb_n(t); "$game_message.background=2\nKernel.pbMessage(_INTL(\"#{rbq(t)}\"))\n$game_message.background=0"; end
def rb_s(name, t); "Kernel.pbMessage(_INTL(\"<b>#{name}:</b> #{rbq(t)}\"))"; end
# Página vacía «antes / después» para una banda o NPC que aparece según el estado.
def blank(cond = {}); pg(cond: cond); end

# =========================================================================== ESCENAS REUTILIZABLES
def scene_desayuno(l)
  l.speak("Amparo", "Hoy es el día. No te he llamado para que te quedes mirando el techo.")
  l.narrate("Desayunas con prisa. Ella te ajusta el cuello de la chaqueta, te coloca un mechón rebelde y te mira un segundo de más.")
  l.speak("Amparo", "Anda, ve. Y antes de salir, pasa por la puerta: tengo algo para ti.")
  l.script(sv(1))
end

def scene_despedida(l)
  mov(l, "Amparo corre hasta la puerta y se pone frente al jugador; el jugador se gira hacia ella.")
  l.speak("Amparo", "¡Espera! Aún no te vas sin esto.")
  l.narrate("Amparo te tiende un paquete envuelto en papel de estraza: unas deportivas nuevas, con los cordones ya anudados.")
  l.script("$PokemonGlobal.runningShoes=true")
  l.say("\\se[ItemGet]¡Has recibido las Deportivas! Mantén pulsado el botón A para correr.")
  l.speak("Amparo", "Para que no llegues tarde ni a tu propio viaje.")
  l.speak("Amparo", "Vuelve cuando quieras. La casa no se mueve.")
  l.narrate("Tu padre, apoyado en el marco del salón, te guiña un ojo.")
  l.gender(lambda { |b| b.speak("Padre", "Si te cansas, vuelve a casa, campeón. Aquí siempre os dejaremos como nuevos, a ti y a los tuyos.") },
           lambda { |b| b.speak("Padre", "Si te cansas, vuelve a casa, campeona. Aquí siempre os dejaremos como nuevos, a ti y a los tuyos.") })
  l.script(sv(2))
end

def scene_llegada_plaza(l)
  l.narrate("Pueblo Albor es un lugar pequeño, de tejas azuladas y un olmo viejo en la plaza. Todo el mundo se conoce.")
  l.narrate("Cada mañana la misma gallina cruza la misma calle. Al fondo, sobre una loma, la casa-laboratorio del Profesor despide humo por la chimenea.")
end

def scene_lucian_verja(l)
  l.narrate("En la verja te espera Lucián, tu vecino de toda la vida. Lleva el chaleco abrochado hasta arriba, las gafas torcidas de tanto empujárselas y una libreta bajo el brazo.")
  l.speak("Lucián", "Llegas ocho minutos tarde. Probablemente no es grave. Aunque... con un setenta por ciento de confianza, Guiomar ya está dentro.")
  l.narrate("Lucián se ajusta las gafas y abre la libreta.")
  l.speak("Lucián", "Hoy empiezo el registro de especies. Completar la Pokédex es solo cuestión de método. Vamos, que el Profesor nos espera.")
  mov(l, "Lucián sube la loma hasta la puerta del laboratorio y entra (al cambiar V121 a 3 su sprite desaparece del patio).")
  l.script(sv(3))
end

def scene_laboratorio(l)
  l.narrate("Cuando cruzas la puerta del laboratorio, Guiomar da botes en medio de la sala, con la coleta rojiza desordenada, las vendas de las manos y una tirita nueva en cada rodilla.")
  l.speak("Guiomar", "¡Por fin! ¡Creía que os habíais echado atrás!")
  l.narrate("Ha venido corriendo desde Pueblo Heliar. Pía, la ayudante del Profesor, intenta que baje la voz. No lo consigue.")
  l.speak("Pía", "Guiomar, por favor... el Profesor está a punto de bajar.")
  mov(l, "Ambrosio baja las escaleras (eventos AS del laboratorio) con lentitud hasta el centro de la sala.")
  l.narrate("Entonces aparece él. Ambrosio Valdemar baja las escaleras con la lentitud de quien nunca ha tenido prisa. Debajo de la bata impoluta lleva un traje oscuro de cuello alto, de otro siglo.")
  l.narrate("En la mano izquierda sostiene un reloj de bolsillo de oro cuya esfera atraviesa una fina grieta. Lo consulta, lo guarda, y sonríe.")
  l.speak("Ambrosio", "Mis queridos. Qué día tan hermoso para empezar.")
  l.narrate("Les habla del vínculo entre las personas y las criaturas que las acompañan. Lo hace con ternura, con las manos entrelazadas a la espalda, y de pronto se detiene, como si hubiera encontrado una palabra dentro de otra.")
  l.speak("Ambrosio", "Últimamente he estado estudiando ciertos... desequilibrios en los sueños. Pero no es día para eso.")
  l.speak("Ambrosio", "Los vínculos, queridos míos, despiertan todo lo que duerme. Recordadlo.")
  l.narrate("Cada uno dice por qué viaja.")
  l.speak("Lucián", "Voy a completar la Pokédex. Es solo cuestión de método.")
  l.speak("Guiomar", "¡Voy a ganar los ocho gimnasios y a ser la mejor! ¡Los ocho gimnasios y ser la mejor! ¡LA MEJOR!")
  l.narrate("Tú no dices nada: sonríes, y los dos te miran como si hubieras dicho lo más sensato.")
  l.speak("Ambrosio", "Sobre las mesas os esperan dieciocho compañeros. Elegid con el corazón. Tú primero.")
  l.speak("Pía", "Cuando hayas elegido, pasa por mi mostrador: tengo algo para ti.")
  l.script(sv(4))
end

# Pía entrega el Mapa y el Caramelo Infinito (idempotente por interruptor).
def pia_regalos(l)
  l.if_(:sw, SW_MAP, false) { |c|
    c.speak("Pía", "Cuando salgas de aquí vas a necesitar esto: el Mapa de Oniria. Lo he dibujado yo misma, así que no te fíes de las escalas.")
    c.script("Kernel.pbReceiveItem(:TOWNMAP)")
    c.sw(SW_MAP)
  }
  l.if_(:sw, SW_CANDY, false) { |c|
    c.speak("Pía", "Y esto es para ti: un Caramelo Infinito. Sube un nivel cada vez que lo uses, sin límite de usos, hasta el tope de nivel.")
    c.script("Kernel.pbReceiveItem(:INFINITECANDY)")
    c.sw(SW_CANDY)
  }
  l.script("$game_switches[400]=true\n$game_map.need_refresh=true")
end

# Combate tutorial con Lucián (Nv 5) y despedida de los tres.
def scene_duelo(l, remind = true)
  l.ifelse(:sw, SW_CANDY, true) {
    [lambda { |b|
      b.speak("Lucián", "Había una probabilidad bastante alta de que salieras ahora. Quiero comprobar cuánto hemos mejorado desde que recibimos a nuestros compañeros. ¿Un combate amistoso?")
      b.ifelse(:script, "Kernel.pbConfirmMessage(_INTL(\"¿Aceptas el combate amistoso con Lucián?\"))") {
        [lambda { |c|
          c.script([
            "idx=pbPiaIndex(pbPiaFirst)", "g=idx/3", "t=idx%3", "lt=[1,2,0][t]", "pid=g*3+lt",
            "nm=PBSpecies.getName(getConst(PBSpecies,REM_PIA_STARTERS[pid][0]))",
            rb_n("Lucián se ajusta las gafas, elige con cuidado el Pokémon con ventaja de tipo y te explica con voz firme por qué va a ganar."),
            "Kernel.pbMessage(_INTL(\"<b>Lucián:</b> Mi compañero es {1}. Según mis cálculos, la ventaja de tipo es evidente.\",nm))",
            "tr=(pbLoadTrainer(:RIVAL_M,\"Lucián\",pid) rescue nil)",
            "if tr",
            "  pbTrainerBattle(:RIVAL_M,\"Lucián\",_I(\"<b>Lucián:</b> Vaya... mi estimación era incorrecta. Lo anoto.\"),false,pid,true)",
            "else",
            "  Kernel.pbMessage(_INTL(\"(Aviso de desarrollo: falta el entrenador RIVAL_M «Lucián» con ID de equipo {1} en trainers.txt.)\",pid)) if $DEBUG",
            "end"
          ].join("\n"))
          c.narrate("Lucián pierde el primer turno y lo anota.")
          c.speak("Lucián", "Es un buen dato. Lo registro.")
          c.speak("Guiomar", "¡Pues yo me voy ya! ¡Nos vemos en el gimnasio! ¡El que llegue segundo invita!")
          mov(c, "Guiomar sale corriendo del patio hacia la Ruta 1 (al cambiar V121 a 6 su sprite desaparece).")
          c.narrate("Lucián recoge su libreta.")
          c.speak("Lucián", "Probablemente nos alcanzará en el primer cruce.")
          mov(c, "Lucián se despide y echa a andar tras Guiomar hacia el sur (al cambiar V121 a 6 su sprite desaparece).")
          c.script("pbSetStoryVar(:PUEBLO_ALBOR,6)\npbAdvanceMilestone(1)")
          c.narrate("Mientras recoges tus cosas, oyes que alguien te llama desde la plaza.")
        }, lambda { |c| c.speak("Lucián", "Tómate tu tiempo. Lo he anotado como «pendiente».") }]
      }
    }, (remind ? lambda { |b|
      b.speak("Lucián", "Pía quería darte algo antes de que salgas. Pasa por su mostrador y luego hablamos.")
    } : nil)]
  }
end

# Amparo alcanza al jugador en la plaza y le da el Pokévial (tras el inicial y tras el primer combate).
def scene_pokevial(l)
  mov(l, "Amparo llega corriendo desde la casa hasta quedar frente al jugador; el jugador se gira hacia ella.")
  l.narrate("Amparo llega corriendo desde casa, con el delantal aún puesto y un frasco en las manos.")
  l.speak("Amparo", "¡Espera! ¡No te vas sin esto!")
  l.ifelse(:script, "Kernel.pbReceiveItem(:POKEVIAL)") {
    [lambda { |b|
      b.script("pbRemEnsureVialVars")
      b.sw(SW_VIAL)
      b.script(sv(7))
      b.speak("Amparo", "Es un Pokévial. Tiene una carga y se rellena solo en cualquier lugar donde curen a tu equipo.")
      b.speak("Amparo", "Cuando hayas ganado tres medallas, pasa a verme; y otra vez con seis. Ya veré qué puedo hacer por él.")
      b.speak("Amparo", "Y ahora ve con cuidado. Tu padre lo ha dicho antes, pero te lo repito yo: aquí siempre os dejaremos como nuevos.")
      b.narrate("Sales a la loma. Hacia el noreste, una cueva cuya entrada está sellada con tablones; hacia el oeste, el mar, y una ruta que solo se atraviesa con barco. Hacia el sur, la Ruta 1.")
      b.narrate("Detrás de ti, Amparo agita la mano, y la mano del Profesor, desde la ventana del laboratorio, abre y cierra la tapa de su reloj.")
    }, lambda { |b|
      b.speak("Amparo", "Pero si llevas la mochila llena... Haz sitio y vuelvo a dártelo.")
    }]
  }
end

# =========================================================================== MAPA 3: CASA PLAYER
casa = []

# Despertar (Autorun, una sola vez)
l = L.new
loc(l, "Cualquier casilla de la habitación del jugador: es Autorun y corre solo al llegar (inicio de partida).")
l.script("pbAdvanceMilestone(1)")
l.narrate("Te despierta el olor a pan. La luz entra sesgada por la ventana de tu cuarto y dibuja en el suelo un rectángulo amarillo.")
l.narrate("Abajo se oye el tintineo de las tazas: tu madre, Amparo, ya ha puesto la mesa.")
mov(l, "Opcional: el jugador baja de la cama / camina hasta la puerta de la habitación.")
l.self_sw('A')
casa << ["ALBOR_Despertar", [pg(trig: 3, list: l), pg(cond: { :self => 'A' })]]

# BANDA: cocina (desayuno con Amparo)
l = L.new
loc(l, "BANDA (baldosa de activación). Entrada de la cocina / comedor, antes de llegar a la mesa; copiar si la entrada es ancha.")
scene_desayuno(l)
casa << ["ALBOR_Banda cocina (desayuno)", [pg(trig: 1, list: l, cond: {}), pg(cond: { :var => [V_STORY, 1] })]]

# BANDA: puerta de la casa (despedida y Deportivas)
l0 = L.new
loc(l0, "BANDA (baldosa de activación). Casilla justo ANTES de la puerta de salida (sobre el evento PC de salida de la casa); copiar si hay varias casillas de salida.")
l0.speak("Amparo", "¿Ya te vas sin desayunar? Ven un momento a la cocina, anda.")
l0.script("pbMoveRoute($game_player,[PBMoveRoute::Up],true)")
l1 = L.new
scene_despedida(l1)
casa << ["ALBOR_Banda puerta (despedida y Deportivas)", [pg(trig: 1, list: l0), pg(cond: { :var => [V_STORY, 1] }, trig: 1, list: l1), pg(cond: { :var => [V_STORY, 2] })]]

# Amparo (3 páginas: base, 3 medallas, 6 medallas)
def amparo_base(l)
  l.ifelse(:sw, SW_VIAL, true) {
    [lambda { |b|
      b.speak("Amparo", "¿Todo bien, cariño? La casa no se mueve, ya lo sabes.")
      b.if_(:var, 105, :lt, 6) { |c|
        c.speak("Amparo", "Acuérdate: cuando hayas ganado tres medallas, pásate a verme; y otra vez con seis. Ya veré qué puedo hacer por el Pokévial.")
      }
    }, lambda { |b|
      b.ifelse(:var, V_STORY, :lt, 2) {
        [lambda { |c| c.speak("Amparo", "Anda, ve a la puerta. Tengo algo para ti.") },
         lambda { |c| c.speak("Amparo", "El Profesor te espera, y Lucián habrá anotado ya los minutos que llegas tarde. Vete, vete. Volveré a verte por la plaza.") }]
      }
    }]
  }
end
def amparo_mejora(l, n)
  frase = (n == 2) ? "Tres medallas ya... Dame ese Pokévial, anda." : "Seis medallas. Se me hace raro verte tan mayor. Trae, trae ese Pokévial."
  sig = (n == 2) ? "Vuelve a verme cuando lleves seis medallas." : "Ya no puedo darle más de sí. Lo demás es cosa tuya."
  l.ifelse(:script, "pbRemVialMax<#{n} && $PokemonBag.pbQuantity(getConst(PBItems,:POKEVIAL))>0") {
    [lambda { |b|
      b.speak("Amparo", frase)
      b.narrate("Amparo hace algo con el frasco —un ajuste, un lazo, una palabra que no llega a decir— y te lo devuelve más pesado.")
      b.script("pbRemVialSetMin(#{n})\npbRemVialRefill\npbRemEnsureVialVars")
      b.say("\\se[ItemGet]¡El Pokévial ahora tiene #{n} cargas!")
      b.speak("Amparo", sig)
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
l.ifelse(:var, V_STORY, :lt, 2) {
  [lambda { |b| b.speak("Padre", "Ve a hablar con tu madre. Yo ya me despediré de ti en la puerta, que me conozco y me pongo blando.") },
   lambda { |b|
     b.gender(lambda { |c| c.speak("Padre", "¿Ya te vas, campeón? Déjame echarle un vistazo a tu equipo.") },
              lambda { |c| c.speak("Padre", "¿Ya te vas, campeona? Déjame echarle un vistazo a tu equipo.") })
     b.ifelse(:script, "$Trainer.party.length>0 && Kernel.pbConfirmMessage(_INTL(\"¿Quieres que tu padre cure a tu equipo?\"))") {
       [lambda { |c|
         c.narrate("Tu padre se arremanga y atiende a tus compañeros con manos tranquilas.")
         c.script("pbHealAll\nKernel.pbSetPokemonCenter")
         c.speak("Padre", "Listo. Como nuevos. Si te cansas, vuelve a casa: aquí siempre os dejaremos como nuevos, a ti y a los tuyos.")
       }, lambda { |c| c.speak("Padre", "Cuando quieras. Esta casa siempre tiene la luz encendida.") }]
     }
   }]
}
casa << ["ALBOR_Padre (curación)", [pg(gfx: 'npc002', list: l)]]

# =========================================================================== MAPA 2: PUEBLO ALBOR
pueblo = []

# BANDA: salida de la casa (descripción del pueblo, una vez)
l = L.new
loc(l, "BANDA (baldosa de activación). Plaza, justo delante de la puerta de la casa del jugador (primer paso al salir).")
scene_llegada_plaza(l); l.self_sw('A')
pueblo << ["ALBOR_Banda salida de casa (descripción)", [blank, pg(cond: { :var => [V_STORY, 2] }, trig: 1, list: l), pg(cond: { :self => 'A' })]]

# BANDA + sprite: Lucián en la verja
l = L.new
loc(l, "BANDA (baldosa de activación). Camino que sube al laboratorio, justo antes de la verja (cruzar la zona activa a Lucián).")
scene_lucian_verja(l)
pueblo << ["ALBOR_Banda Lucián (verja)", [blank, pg(cond: { :var => [V_STORY, 2] }, trig: 1, list: l), pg(cond: { :var => [V_STORY, 3] })]]
l = L.new
loc(l, "Junto a la verja del laboratorio (a los pies de la loma). Si el jugador le habla antes de pisar la banda, hace la misma escena.")
scene_lucian_verja(l)
pueblo << ["ALBOR_Lucián (verja)", [blank, pg(cond: { :var => [V_STORY, 2] }, gfx: 'trchar002', list: l), pg(cond: { :var => [V_STORY, 3] })]]

# Guiomar en el patio
l = L.new
loc(l, "Patio delante del laboratorio, junto a Lucián (aparece cuando eliges inicial).")
l.speak("Guiomar", "¡Vamos, vamos! ¡Que el combate empiece ya, que yo estoy lista para marcharme!")
l.speak("Guiomar", "¡Los ocho gimnasios y la mejor de todo Oniria! ¡Y lo digo tres veces si hace falta!")
pueblo << ["ALBOR_Guiomar (patio)", [blank, pg(cond: { :var => [V_STORY, 5] }, gfx: 'trchar003', list: l), pg(cond: { :var => [V_STORY, 6] })]]

# BANDA + sprite: Lucián en el patio (combate tutorial, Nv 5)
l = L.new
loc(l, "BANDA (baldosa de activación). Salida del laboratorio hacia el patio: cruzarla activa el combate amistoso (solo si Pía ya te ha dado el Mapa y el Caramelo).")
scene_duelo(l, false)
pueblo << ["ALBOR_Banda combate (patio)", [blank, pg(cond: { :var => [V_STORY, 5] }, trig: 1, list: l), pg(cond: { :var => [V_STORY, 6] })]]
l = L.new
loc(l, "Patio delante del laboratorio (frente al jugador al salir). Si se le habla, hace la misma escena del combate.")
scene_duelo(l)
pueblo << ["ALBOR_Lucián (patio, combate tutorial)", [blank, pg(cond: { :var => [V_STORY, 5] }, gfx: 'trchar002', list: l), pg(cond: { :var => [V_STORY, 6] })]]

# BANDA + sprite: Amparo en la plaza (Pokévial, tras el combate)
l = L.new
loc(l, "BANDA (baldosa de activación). Camino de la loma a la plaza, tras el patio: cruzarla activa la llegada de Amparo con el Pokévial.")
scene_pokevial(l)
pueblo << ["ALBOR_Banda Amparo (Pokévial)", [blank, pg(cond: { :var => [V_STORY, 6] }, trig: 1, list: l), pg(cond: { :var => [V_STORY, 7] })]]
l = L.new
loc(l, "Plaza, junto al olmo (Amparo espera al jugador tras el combate). Si se le habla, entrega el Pokévial igual que la banda.")
scene_pokevial(l)
pueblo << ["ALBOR_Amparo (plaza)", [blank, pg(cond: { :var => [V_STORY, 6] }, gfx: 'npc001', list: l), pg(cond: { :var => [V_STORY, 7] })]]

# Bloqueos de salida por la Ruta 1 (x4)
4.times do |i|
  l = L.new
  loc(l, "BANDA (baldosa de activación). Fila justo ENCIMA de las salidas a Ruta 1 (la fila anterior a los eventos R1 de la fila inferior del mapa), una copia por cada columna de salida (4).") if i == 0
  l.if_(:var, V_STORY, :lt, 7) { |b|
    b.ifelse(:var, V_STORY, :lt, 3) {
      [lambda { |c| c.narrate("Todavía no es momento de irse: Lucián te espera junto a la verja del laboratorio.") },
       lambda { |c|
         c.ifelse(:var, V_STORY, :lt, 5) {
           [lambda { |d| d.narrate("Todavía no tienes compañero: el Profesor te espera en el laboratorio.") },
            lambda { |d|
              d.ifelse(:var, V_STORY, :lt, 6) {
                [lambda { |e| e.narrate("Lucián te espera en el patio del laboratorio. Y Pía tiene algo para ti.") },
                 lambda { |e| e.narrate("Alguien te llama desde la plaza. Mejor esperar a que llegue.") }]
              }
            }]
         }
       }]
    }
    b.script("pbMoveRoute($game_player,[PBMoveRoute::Up],true)")
  }
  pueblo << ["ALBOR_Bloqueo salida Ruta 1 (#{i + 1}/4)", [pg(trig: 1, list: l)]]
end

# Cueva sellada (Ruta 20)
l = L.new
loc(l, "Entrada de la cueva del noreste (Ruta 20), sobre los tablones.")
l.narrate("Una entrada de cueva sellada con tablones clavados a conciencia. Por las rendijas sopla un aire frío y antiguo.")
l.narrate("Parece que, por ahora, no hay forma de abrirla.")
pueblo << ["ALBOR_Cueva sellada (Ruta 20)", [pg(list: l)]]

# Carteles
l = L.new; loc(l, "Plaza, a la entrada del pueblo desde la Ruta 1 (se puede copiar en varias casillas).")
l.narrate("PUEBLO ALBOR — Casas bajas, un olmo viejo y la luz más temprana de Oniria.")
pueblo << ["ALBOR_Cartel del pueblo", [pg(list: l)]]
l = L.new; loc(l, "Verja / puerta del laboratorio (loma).")
l.narrate("LABORATORIO POKÉMON DE ONIRIA — Prof. Ambrosio Valdemar. Llame antes de entrar. (Pía dice que no hace falta.)")
pueblo << ["ALBOR_Cartel del laboratorio", [pg(list: l)]]

# --- Misión local: «El Pokémon del pozo» ---
# Anciano (Don Anselmo, nombre provisional). Solo ofrece la misión con el inicial ya elegido; al aceptar se aparta una baldosa a la derecha.
l0 = L.new
loc(l0, "Junto al pozo del pueblo, DELANTE de la entrada (tapándola). Antes de tener inicial solo conversa.")
l0.speak("Anciano", "Ay, qué mañana... Hoy los chicos del Profesor se ponen en marcha, ¿verdad? Cuando tengas a tu compañero, ven a verme, hijo.")
l = L.new
loc(l, "Junto al pozo del pueblo, DELANTE de la entrada (tapándola). Al aceptar la misión se aparta UNA baldosa a la derecha y deja libre el pozo.")
l.ifelse(:var, V_QUEST, :eq, 0) {
  [lambda { |b|
    b.speak("Anciano", "Ay, hijo... mi Wooper se cayó al pozo esta mañana, mientras bebía. Con estas rodillas no puedo bajar a buscarlo.")
    b.ifelse(:script, "Kernel.pbConfirmMessage(_INTL(\"¿Ayudas al anciano a rescatar a su Pokémon?\"))") {
      [lambda { |c|
        c.script("pbSetQuestState(:PUEBLO_ALBOR,1)")
        c.speak("Anciano", "¡Gracias, gracias! Pero ten cuidado: lleva rato llorando ahí abajo y estará aterrado. No te lo tomes a mal si te ataca.")
        mov(c, "El anciano se aparta una baldosa a la derecha (lo hace el script de la línea siguiente) y deja libre la entrada del pozo.")
        c.script("pbMoveRoute(get_character(0),[PBMoveRoute::Right],true)")
        c.speak("Anciano", "El pozo está ahí mismo. Tráemelo de vuelta, por favor.")
      }, lambda { |c| c.speak("Anciano", "Lo entiendo, hijo. Seguiré esperando por aquí.") }]
    }
  }, lambda { |b|
    b.ifelse(:var, V_QUEST, :eq, 1) {
      [lambda { |c| c.speak("Anciano", "Se oye ahí abajo, ¿verdad? Pobrecito. Baja con cuidado, y no tengas prisa por tranquilizarlo.") },
       lambda { |c|
         c.ifelse(:var, V_QUEST, :eq, 3) {
           [lambda { |d|
             d.narrate("Sacas del pozo al Wooper, aún tembloroso, y se lo pones en los brazos al anciano.")
             d.speak("Anciano", "¡Mi Wooper! ¡Mi pequeño! Ya está, ya pasó...")
             d.speak("Anciano", "No sé cómo agradecértelo. Toma, esto es lo único que tengo a mano.")
             d.ifelse(:script, "Kernel.pbReceiveItem(:PARLYZHEAL)") {
               [lambda { |e|
                 e.script("pbSetQuestState(:PUEBLO_ALBOR,99)")
                 e.speak("Anciano", "Cuídate mucho ahí fuera. Y vuelve a saludarnos cuando quieras.")
               }, lambda { |e| e.speak("Anciano", "Ay, tu mochila está llena. Haz sitio y vuelve, que no se me olvida.") }]
             }
           }, lambda { |d|
             d.speak("Anciano", "Mi Wooper vuelve a jugar con el agua del abrevadero. Ha sido gracias a ti.")
           }]
         }
       }]
    }
  }]
}
pueblo << ["ALBOR_Anciano (misión del pozo)", [pg(gfx: 'npc004', list: l0), pg(cond: { :var => [V_STORY, 5] }, gfx: 'npc004', list: l)]]

# Wooper del pozo (mapa 14 «Pozo», hijo de Pueblo Albor). La entrada ya existe (evento E de Albor en el pozo); aquí vive el combate.
pozo = []
l = L.new
loc(l, "Orilla del fondo del pozo (mapa 14), cerca del agua.")
l.narrate("Del agua oscura llegan quejidos y chapoteos. Entre la penumbra brillan unos ojos aterrados.")
l.ifelse(:script, "$Trainer.ablePokemonCount>0") {
  [lambda { |c|
    c.narrate("¡El Pokémon del anciano, asustado, se abalanza sobre ti!")
    mov(c, "Opcional: el Wooper salta desde el agua hacia el jugador antes del combate.")
    c.script([
      "pbWildBattle(:WOOPER,5,1,false,false)", "d=$game_variables[1]", "if d==4",
      "  for i in (0...$Trainer.party.length).to_a.reverse", "    pk=$Trainer.party[i]",
      "    if pk && pk.species==PBSpecies::WOOPER && pk.level==5", "      $Trainer.party.delete_at(i)", "      break",
      "    end", "  end",
      rb_n("El Pokémon del anciano no es para ti: lo sueltas con cuidado."), "  d=1", "end", "if d==1",
      rb_n("El Wooper, agotado, se deja coger en brazos. Poco a poco deja de temblar."),
      rb_n("Ahora sube por la soga y llévaselo a su dueño."), "  pbSetQuestState(:PUEBLO_ALBOR,3)", "elsif d!=2",
      rb_n("El Wooper se hunde en el agua oscura. Tendrás que bajar otra vez."), "end"
    ].join("\n"))
  }, lambda { |c| c.narrate("No puedes acercarte a un Pokémon asustado sin un compañero en condiciones. Sube y vuelve cuando tu equipo esté sano.") }]
}
pozo << ["ALBOR_Wooper del pozo (misión)", [pg, pg(cond: { :var => [V_QUEST, 1] }, gfx: '194', list: l), pg(cond: { :var => [V_QUEST, 3] })]]

# --- Ambientación del pueblo (NPC genéricos npcNNN; el diseñador los sustituye por arte final) ---
l = L.new; loc(l, "Cerca del olmo de la plaza (NPC de ambientación).")
l.ifelse(:var, V_STORY, :lt, 7) {
  [lambda { |b| b.speak("Aldeano", "Tocar la flauta antes del desayuno da buena suerte. Lo dice mi abuela, y mi abuela casi nunca falla.") },
   lambda { |b| b.speak("Aldeano", "Si vuelves por aquí, te tocaré algo más animado. Esta melodía es solo de las mañanas tranquilas.") }]
}
pueblo << ["ALBOR_Aldeano flautista", [pg(gfx: 'npc003', list: l)]]

l = L.new; loc(l, "Plaza, cerca del olmo (NPC de ambientación: un crío del pueblo).")
l.ifelse(:var, V_STORY, :lt, 7) {
  [lambda { |b| b.speak("Niño", "¡Hoy se marchan los chicos del Profesor! Yo, cuando sea mayor, voy a ganar los ocho gimnasios. Bueno, siete. El octavo da miedo.") },
   lambda { |b| b.speak("Niño", "¿Ya te vas? Guárdame un sitio en la Liga. Y no le cuentes a nadie lo de los siete gimnasios.") }]
}
pueblo << ["ALBOR_Niño del olmo", [pg(gfx: 'npc008', list: l)]]

l = L.new; loc(l, "Junto a los tendederos de una casa (NPC de ambientación).")
l.speak("Granjera", "Con este sol la ropa se seca en un suspiro. Si vas hacia la Ruta 1, cuidado con los Pokémon salvajes: muerden cuando se asustan.")
pueblo << ["ALBOR_Granjera de los tendederos", [pg(gfx: 'npc009', list: l)]]

l = L.new; loc(l, "Orilla oeste del pueblo, mirando al mar (NPC de ambientación).")
l.speak("Pescador", "Ese mar no se cruza sin barco. Llevo años mirando el horizonte; algún día llegará quien lo cruce.")
l.speak("Pescador", "Por ahora me conformo con lo que pique cerca de la orilla. Que no es mucho, pero es honrado.")
pueblo << ["ALBOR_Pescador de la orilla", [pg(gfx: 'npc010', list: l)]]

l = L.new; loc(l, "Una de las calles del pueblo (Pokémon de ambientación: la gallina que cruza cada mañana). Sprite del propio Pokémon.")
l.script("pbPlayCry(getConst(PBSpecies,:FARFETCHD)) rescue nil")
l.narrate("Un Farfetch'd cruza la calle como cada mañana, muy seguro de sí mismo, con su puerro bien alto. Ni te mira.")
pueblo << ["ALBOR_Gallina (Farfetch'd)", [pg(gfx: '083', list: l)]]

# --- Objetos de Albor (consumibles de suministro, 1-2 por pueblo; autointerruptor por evento) ---
l = L.new; loc(l, "Detrás de la casa del jugador, junto a la tapia (Poké Ball visible). Poción: suministro de ruta.")
l.if_(:script, "Kernel.pbReceiveItem(:POTION)") { |b| b.self_sw('A') }
pueblo << ["ALBOR_Objeto Poción (tapia)", [pg(gfx: 'rem_itemball', list: l), pg(cond: { :self => 'A' })]]
l = L.new; loc(l, "Al pie del olmo de la plaza (objeto oculto: sin gráfico). Baya Aranja: suministro de ruta.")
l.if_(:script, "Kernel.pbReceiveItem(:ORANBERRY)") { |b| b.self_sw('A') }
pueblo << ["ALBOR_Objeto oculto Baya Aranja (olmo)", [pg(list: l), pg(cond: { :self => 'A' })]]

# =========================================================================== MAPA 4: LABORATORIO
lab = []

# BANDA: entrada del laboratorio (escena de llegada con Ambrosio, Pía y Guiomar)
l = L.new
loc(l, "BANDA (baldosa de activación). Zona de entrada del laboratorio, nada más cruzar la puerta (copiar si la entrada es ancha). Colocar a Pía, Guiomar y Lucián en sus eventos de sitio; Ambrosio baja por las escaleras.")
scene_laboratorio(l)
lab << ["ALBOR_Escena del laboratorio", [blank, pg(cond: { :var => [V_STORY, 3] }, trig: 1, list: l), pg(cond: { :var => [V_STORY, 4] })]]

# Lucián y Guiomar dentro del laboratorio (visibles en V121 3..4)
[['Lucián', 'trchar002', "Tengo anotados dieciséis datos útiles sobre los iniciales. Elige tú primero, que luego yo elijo con ventaja."],
 ['Guiomar', 'trchar003', "¡Elige ya, elige ya! ¡Yo no me puedo estar quieta!"]].each do |nom, gfx, txt|
  l = L.new; loc(l, "Sala principal del laboratorio, cerca de las mesas de los iniciales."); l.speak(nom, txt)
  lab << ["ALBOR_#{nom} (laboratorio)", [blank, pg(cond: { :var => [V_STORY, 3] }, gfx: gfx, list: l), pg(cond: { :var => [V_STORY, 5] })]]
end

# Ambrosio (Profesor)
l = L.new
loc(l, "Sala principal del laboratorio (cerca de las escaleras o del centro de la sala).")
l.ifelse(:var, V_STORY, :lt, 5) {
  [lambda { |b| b.speak("Ambrosio", "Cuando quieras. Los compañeros no tienen prisa... aunque yo, a veces, sí.") },
   lambda { |b|
     b.ifelse(:var, V_STORY, :lt, 7) {
       [lambda { |c| c.speak("Ambrosio", "Pasad por el patio, queridos. Lucián tiene ganas de probar sus apuntes.") },
        lambda { |c|
          c.narrate("Ambrosio consulta su reloj de bolsillo, lo guarda y sonríe.")
          c.speak("Ambrosio", "Los vínculos despiertan todo lo que duerme. Recuérdalo, y viajad juntos.")
        }]
     }
   }]
}
lab << ["ALBOR_Ambrosio (Profesor)", [pg(gfx: 'trchar004', list: l)]]

# BANDA: salida del laboratorio (Ambrosio se despide tras elegir inicial; una sola vez)
l = L.new
loc(l, "BANDA (baldosa de activación). Zona interior de la puerta de salida del laboratorio (cruzarla tras elegir inicial).")
l.narrate("Ambrosio consulta su reloj de bolsillo, lo guarda y sonríe.")
l.speak("Ambrosio", "Pasa por el patio, que Lucián tiene ganas de probar sus apuntes. Y viaja con ellos, ¿de acuerdo? Con los dos.")
l.self_sw('A')
lab << ["ALBOR_Banda salida del laboratorio (Ambrosio)", [blank, pg(cond: { :var => [V_STORY, 5] }, trig: 1, list: l), pg(cond: { :self => 'A' })]]

# BANDA: mostrador de Pía (entrega del Mapa y el Caramelo, una sola vez)
l = L.new
loc(l, "BANDA (baldosa de activación). Casilla delante del mostrador de Pía (la que se pisa al acercarse a ella tras elegir inicial).")
pia_regalos(l); l.self_sw('A')
lab << ["ALBOR_Banda Pía (bienvenida)", [blank, pg(cond: { :var => [V_STORY, 5] }, trig: 1, list: l), pg(cond: { :self => 'A' })]]

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
l.ifelse(:var, V_STORY, :lt, 5) {
  [lambda { |b|
    b.speak("Pía", "¡Bienvenido al laboratorio! En cuanto elijas a tu compañero, pasa por mi mostrador, que tengo cosas para ti.")
  }, lambda { |b|
    pia_regalos(b)
    b.script(<<RB)
hs_hitos=[#{hitos.join(",\n")}]
loop do
  c=Kernel.pbMessage(_INTL("<b>Pía:</b> ¿Qué necesitas?"),[_INTL("Misiones de Pía"),_INTL("Entregas de captura"),_INTL("Reclamar un inicial"),_INTL("Nada, gracias")],4)
  if c==0
    pbPiaQuestPanel
  elsif c==1
    owned=$Trainer.pokedexOwned
    d=(pbRemPia[:hito]||={})
    ready=hs_hitos.select{|h| !d[h[0]] && owned>=h[1] && $game_variables[101]>=h[4]}
    if ready.length==0
      Kernel.pbMessage(_INTL("<b>Pía:</b> Llevas {1} especies capturadas. Todavía no tienes ninguna entrega pendiente; sigue anotando en el cuaderno.",owned))
    else
      names=ready.map{|h| h[5]}
      names.push(_INTL("Cancelar"))
      k=Kernel.pbShowCommands(nil,names,-1)
      if k>=0 && k<ready.length
        h=ready[k]
        Kernel.pbMessage(_INTL("<b>Pía:</b> ¡Misión «{1}» cumplida! Toma tu recompensa.",h[5]))
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

# Los 18 iniciales (Gen 1-6): sprite del propio Pokémon, visibles con V121 = 4 y retirados en V121 >= 5
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
  l.script([
    "sp=PBSpecies.getName(getConst(PBSpecies,:#{sym}))", "pbPlayCry(getConst(PBSpecies,:#{sym})) rescue nil",
    "Kernel.pbMessage(_INTL(\"{1}, de tipo #{tipo}: #{frase[tipo]}.\",sp))",
    "if Kernel.pbConfirmMessage(_INTL(\"¿Quieres elegir a {1} como tu compañero?\",sp))",
    "  if pbAddPokemon(:#{sym},5)", "    pbPiaMarkFirst(:#{sym})", "    $game_switches[400]=true", "    pbRemRefreshFollower",
    rb_n("El tuyo te mira desde la palma abierta, pequeño, de nivel 5, con una curiosidad idéntica a la tuya."),
    rb_n("Ambrosio inclina la cabeza."),
    "    t=#{idx % 3}", "    g=#{idx / 3}", "    lt=[1,2,0][t]", "    gt=3-t-lt",
    "    nl=PBSpecies.getName(getConst(PBSpecies,REM_PIA_STARTERS[g*3+lt][0]))",
    "    ng=PBSpecies.getName(getConst(PBSpecies,REM_PIA_STARTERS[g*3+gt][0]))",
    "    Kernel.pbMessage(_INTL(\"<b>Lucián:</b> Yo me quedo con {1}. La ventaja de tipo es del noventa y cinco por ciento, aproximadamente.\",nl))",
    "    Kernel.pbMessage(_INTL(\"<b>Guiomar:</b> ¡Pues yo con {1}! ¡Es clavado a mí!\",ng))",
    rb_s("Ambrosio", "Viajad juntos. Los tres. Prometédmelo."),
    rb_s("Lucián", "Prometido. Con un noventa por ciento de seguridad."),
    rb_s("Guiomar", "¡Prometido! ¡Y el que llegue segundo al gimnasio invita!"),
    rb_n("Tú asientes. No hace falta decir nada más."),
    "    pbSetStoryVar(:PUEBLO_ALBOR,5)", "    pbAdvanceMilestone(1)", "  end", "end"
  ].join("\n"))
  lab << ["ALBOR_Inicial #{idx + 1} #{sym}", [blank, pg(cond: { :var => [V_STORY, 4] }, gfx: spr, list: l), pg(cond: { :var => [V_STORY, 5] })]]
end

# =========================================================================== MAPA 5: CASAS (2 interiores)
casas = []
# --- Casa 1 (mitad superior del mapa 5)
l = L.new
loc(l, "Casa 1 (mitad superior del mapa 5): salón, junto a la mesa.")
l.ifelse(:var, V_STORY, :lt, 6) {
  [lambda { |b| b.speak("Madre de Lucián", "Lucián salió volando con su libreta. Dijo que había un setenta por ciento de probabilidades de llegar tarde. Llegó tarde.") },
   lambda { |b| b.speak("Madre de Lucián", "Mi Lucián ya es todo un investigador. Cuídamelo por ahí, que es capaz de olvidarse de comer por anotar un dato.") }]
}
casas << ["ALBOR_Madre de Lucián", [pg(gfx: 'npc006', list: l)]]
l = L.new; loc(l, "Casa 1 (mitad superior): junto a la butaca del salón.")
l.speak("Abuelo", "Mi nieto lo apunta todo. De pequeño apuntó cuántas veces estornudaba el gato. Veintitrés. Y el gato, ofendido.")
casas << ["ALBOR_Abuelo de Lucián", [pg(gfx: 'npc011', list: l)]]
l = L.new; loc(l, "Casa 1 (mitad superior): junto a la mesa pequeña o la estantería.")
l.speak("Niña", "Lucián dice que la probabilidad de que me deje su libreta es del cero por ciento. Yo digo que es del cien. Se equivoca mucho.")
casas << ["ALBOR_Hermana de Lucián", [pg(gfx: 'npc012', list: l)]]
l = L.new; loc(l, "Casa 1 (mitad superior): junto a la estufa o la alfombra (Pokémon de ambientación). Sprite del propio Pokémon.")
l.script("pbPlayCry(getConst(PBSpecies,:SKITTY)) rescue nil")
l.narrate("Un Skitty duerme hecho un ovillo junto a la estufa. Al acercarte mueve una oreja, sin abrir los ojos.")
casas << ["ALBOR_Skitty dormido", [pg(gfx: '300', list: l)]]
# --- Casa 2 (mitad inferior del mapa 5)
l = L.new
loc(l, "Casa 2 (mitad inferior del mapa 5): cocina, junto a la ventana.")
l.ifelse(:var, V_QUEST, :eq, 0) {
  [lambda { |b|
    b.gender(lambda { |c| c.speak("Doña Remedios", "Ay, jovencito, el pobre Don Anselmo pasa las mañanas junto al pozo, con su Wooper. Siempre se les ve juntos.") },
             lambda { |c| c.speak("Doña Remedios", "Ay, jovencita, el pobre Don Anselmo pasa las mañanas junto al pozo, con su Wooper. Siempre se les ve juntos.") })
  },
   lambda { |b|
     b.ifelse(:var, V_QUEST, :eq, 99) {
       [lambda { |c| c.speak("Doña Remedios", "Me han dicho que rescataste al Wooper del pozo. En este pueblo todo se sabe, y casi siempre antes de que ocurra.") },
        lambda { |c| c.speak("Doña Remedios", "¿Has bajado ya al pozo? Con ese Wooper asustado, ve con cuidado, que muerde.") }]
     }
   }]
}
casas << ["ALBOR_Doña Remedios", [pg(gfx: 'npc007', list: l)]]
l = L.new; loc(l, "Casa 2 (mitad inferior): junto al horno o la encimera.")
l.speak("Panadero", "Aquí se hornea desde antes del alba. Por eso Albor huele a pan. Tu madre es mi mejor cliente: se lleva dos hogazas y dice que es para el vecindario.")
casas << ["ALBOR_Panadero Gaspar", [pg(gfx: 'npc013', list: l)]]
l = L.new; loc(l, "Casa 2 (mitad inferior): junto a una estantería con cestas.")
l.speak("Joven", "Colecciono bayas. Aún no tengo ninguna rara, pero dicen que cerca del olmo de la plaza algo se esconde entre las raíces.")
casas << ["ALBOR_Joven coleccionista de bayas", [pg(gfx: 'npc014', list: l)]]
l = L.new; loc(l, "Casa 2 (mitad inferior): junto a la ventana que da al laboratorio.")
l.speak("Vecina", "Desde esta ventana veo el laboratorio. La luz del Profesor está encendida toda la noche. Dicen que ese hombre no duerme.")
casas << ["ALBOR_Vecina de la ventana", [pg(gfx: 'npc016', list: l)]]

# Eventos renombrados que heredan la posición ya colocada por el diseñador.
RENAMES = { 'ALBOR_Despedida (Pokévial)' => 'ALBOR_Banda puerta (despedida y Deportivas)' }

# =========================================================================== APLICAR
{ 2 => pueblo, 3 => casa, 4 => lab, 5 => casas, 14 => pozo }.each do |mid, defs|
  placed = REMEv.apply(mid, 'ALBOR_', 'albor_events_v2', defs, DRY, RENAMES)
  puts "Map#{'%03d' % mid}: #{placed.length} eventos #{DRY ? '(dry)' : 'escritos'}"
  placed.each { |id, nm, x, y| puts format('   ev%-3d (%2d,%2d) %s', id, x, y, nm) }
end
