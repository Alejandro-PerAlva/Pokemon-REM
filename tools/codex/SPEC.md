# Pokémon REM — Fase 1/2: contrato único (formatos `rem_*`, modelo JSON y módulos del Codex)

Este documento es la **única fuente de verdad** compartida por todos los agentes. No renombres campos ni
claves: si falta algo, **añade** (campos extra permitidos), nunca cambies lo escrito aquí.
Idioma de la interfaz y de todos los textos de usuario: **español**. Claves/identificadores: ASCII (inglés/símbolos PBS).

## 0. Reglas globales

* Raíz del proyecto: `/Users/a.perezalvarez/Documents/notion/Pokemon-REM` (en adelante `ROOT`).
* **NO tocar** `ROOT/Data/` (ni `*.rxdata` ni `*.dat`), ni `ROOT/PBS_backup_original/` (copia intacta; solo lectura).
* Los archivos oficiales de `PBS/` y los `PBS/rem_*.txt` se escriben **UTF-8 con BOM (EF BB BF) y finales de línea CRLF**.
  Úsalo siempre vía `open(path,'w',encoding='utf-8-sig',newline='')` y `'\r\n'.join(lines)+'\r\n'`.
* Fuentes de diseño (solo lectura): `docs/rebalance/*` (Vol. 1–10 + `proposed_*.txt`). Vol. 11 queda fuera de esta fase.
* Plantel: solo #001–#721. Nombres definitivos: Pueblo Iolita, Pueblo Heliodoro, Granja Apatita, Bosque Dioptasa.
* Equipos de entrenadores/ases/Dominantes son **marcadores**: conserva literalmente `[PENDIENTE DE ASIGNACIÓN]`, `[EN REVISIÓN*]`,
  `[Especie Pendiente]*`, «Dominante N (tipo)». No inventes especies de jefes.
* Los generadores que escribas deben ser **reproducibles** y vivir en `tools/rebalance/phase1/` (Python 3 stdlib; `PIL`/`fitz` solo si ya están instalados).
* Scratchpad con datos intermedios útiles (solo lectura):
  `/private/tmp/claude-502/-Users-a-perezalvarez-Documents-notion/285284a2-47ac-4049-b444-bc02040390e5/scratchpad/`
  (`v10/vol9_by_loc.json`, `v10/final_assign.json`, `v10/notes_final.json`, `v10/facts_all.json`, `build/graph.json`, `vol2.txt` = texto del PDF Vol. 2).

## 1. Claves canónicas de ubicación (64)

`tools/codex/location_keys.json` (lista ordenada: 8 ciudades, 8 pueblos, 16 lugares especiales, 32 rutas) contiene
`{key, name, category}`. **Esa lista fija los 64 `LOC_KEY`** usados en todos los `rem_*.txt`
(p. ej. `PUEBLO_IOLITA`, `RUTA_01`, `GRANJA_APATITA`, `GRUTA_PIRITA`). Para zonas dobles (Lago Amatista, Ciénaga Limonita, Ladera Pórfido)
las tablas de encuentros usan `LOC_KEY:ZONA` (`LAGO_AMATISTA:A`, `LAGO_AMATISTA:B`); el resto usa `LOC_KEY` a secas.
Sub-lugares fuera de las 64 (Geoda Hundida, Umbral de la Liga…) no tienen clave propia: viven dentro de su ubicación madre.
Categorías (`Category`): `Ciudad`, `Pueblo`, `Lugar especial`, `Ruta normal`, `Ruta especial`, `Ruta de montaña`, `Ruta marina`, `Ruta nevada`.
Actos: `I`..`V` (acto de primera visita).

## 2. Formato INI de los `PBS/rem_*.txt`

```
# comentario (línea completa)            ; también se aceptan líneas en blanco
[SECTION_KEY]
Key = Value                              ; claves insensibles a mayúsculas; espacios alrededor del = opcionales
Slot1 = COMMON,20,PIDGEY,3,5,4,7,Texto con, comas libres   ; ver cada archivo
```

* Una clave **repetida acumula** valores en orden (así se escriben los párrafos: `NarrativeText = ...` varias veces).
* Listas sencillas: separador `;`. Listas con campos fijos: coma con **maxsplit** (el último campo es texto libre y puede llevar comas).
* Rangos de nivel: `a-b` (o un solo número). Vacío = sin dato. Los valores NO se entrecomillan.
* Comentarios al final de línea NO existen (un `#` dentro de un valor es parte del valor); solo líneas que empiezan por `#`.
* El parser debe ser tolerante: líneas sin `=` fuera de sección → aviso, no excepción; clave desconocida → ignorar con aviso `info`.
* Cabecera de cada archivo: 3–6 líneas `#` explicando el formato (en español).

### 2.1 `rem_locations.txt` — `[LOC_KEY]` ×64
```
Name = Pueblo Iolita
DraftNames = Pueblo Cianita
Category = Pueblo
Act = I
ProgressionOrder = 1            # primer paso (1-68) de rem_progression en que se pisa
MapNodeNumber = 1               # 1-32 para nodos; vacío en rutas
RouteLabel =                    # R1..R24 / E1..E8 en rutas; vacío en nodos
MapCoords = 136,232             # px sobre Mapa_Final__Esqueleto.png (480x320); nodos: centro; rutas: punto medio del trazado
MapPath =                       # solo rutas: x,y;x,y;x,y...  (polilínea sobre el mismo mapa)
ConnN = RUTA_01,RUTA_20 | Cruce de las Rutas 20 y 21   # claves LOC_KEY (0..n) | texto libre; igual ConnS, ConnE, ConnO (Oeste)
LevelRangeDay = 3-5             # vacío en ciudades/pueblos sin salvajes
LevelRangeNight = 4-7
Etymology = ...
Situation = ...                 # «Situación en el mapa»
Description = ...               # «Descripción ambiental» (un párrafo)
EventsSummary = evento 1; evento 2; ...     # lista `;`
CharactersPresent = Ambrosio (Profesor); Pía (ayudante); ...
BossInfo = Entrega inicial del Pokémon (Nv 5)   # conserva [Especie Pendiente]* donde aparezca
```
Las conexiones ya corregidas del mapa (Apéndice C del Vol. 6) mandan. Una conexión que termina en un cruce (no es ubicación) deja `keys` vacío y el texto «Cruce…».

### 2.2 `rem_encounters.txt` — `[LOC_KEY]` o `[LOC_KEY:ZONA]` (las 48 tablas = 408 casillas tierra/cueva/surf + 32 de pesca)
```
Type = Land            # Land | Cave | Surf   (una sección sin casillas de tierra/agua omite SlotN)
ZoneName =             # solo en secciones con zona
SlotCount = 6
Slot1 = COMMON,20,PIDGEY,3,5,4,7,Nota táctica (texto libre, puede llevar comas)
        #   RARITY(COMMON|UNCOMMON|RARE), PCT, SPECIES_SYMBOL, MinDay, MaxDay, MinNight, MaxNight, TacticalNote
Slot2 = ...
FishCommon = 70,MAGIKARP,10,12,15,18,Nota        # PCT,SPECIES,MinDay,MaxDay,MinNight,MaxNight,Nota
FishRare = 30,GOLDEEN,10,12,15,18,Nota
```
`PCT` son los porcentajes **exactos del Vol. 10** (6 casillas 20/15/10; 4 → 35/20/10; 8 → 16/10/6; 10 → 12/10/5; 16 → 7/6/4; pesca 70/30).
Además la sección especial **`[SPECIAL_OBTAINABILITY]`** con las **721** especies:
```
001 = STARTER,PUEBLO_IOLITA,5,Elección de inicial en el laboratorio
        #  DEX3 = METHOD,LOC_KEY,LEVEL,Detail   (METHOD ∈ WILD, FISHING, STARTER, FOSSIL, EVENT, LEGENDARY, EVOLUTION_LEVEL, EVOLUTION_ITEM, EVOLUTION_STONE, THIRD_STAGE)
```
(`LOC_KEY` vacío en evoluciones; el detalle explica «Evoluciona de X nivel N / con Piedra…»). Cada especie tiene exactamente una línea.

### 2.3 `rem_location_items.txt` — `[LOC_KEY]` ×64
```
Item1 = POTION,1,B,Cuadrante O,En el huerto trasero. Nota completa del Vol. 9
        #  ITEM_ID,Qty,Method,Zone,Note   Method ∈ B,H,C,N,E,J,P,S (leyenda del Vol. 9); ITEM_ID = símbolo PBS de proposed_items.txt (TM01..TM100 para las MT)
```
Una línea por cada una de las 775 filas del Vol. 9 (las MT con `TMxx`). `Qty` entero (1 por defecto).

### 2.4 `rem_shops.txt`
```
[MART_0_MEDALS]   ...  [MART_8_MEDALS]          # tienda estándar acumulativa
Name = Poké Mart (0 medallas)
Medals = 0
Cumulative = yes                                # la sección lista solo los objetos NUEVOS a este nivel; la app acumula
Item1 = POKEBALL,200                            # ITEM_ID,PrecioOverride (vacío = precio del objeto)
[SHOP_<SLUG>]                                   # 8 tiendas especiales del Vol. 9 §3.3
Name = ...      Location = LOC_KEY      Description = ...      Requirement = ...
Item1 = ITEM_ID,Price
[PIA_MISSIONS]                                  # 29 misiones
Mission1 = 5,TM01,1,Primeras anotaciones,Pía revisa el cuaderno...    # CAPTURED_SPECIES,ITEM_ID,Qty,Title,Note
```

### 2.5 `rem_progression.txt` — `[STEP_01]`..`[STEP_68]` (sin spoilers)
`StepNumber`, `Act`, `LocationKey`, `ObjectiveSummary` (una frase **sin spoilers**), `LevelCapDay`, `LevelCapNight` (enteros),
`BossOrGymTitle`, `BossType`, `BossLevelCap`, `RecommendedTMsAvailable` (lista `;` de `TMxx`), `KeyItemsUnlocked` (lista `;` de ITEM_ID o texto).
Una sección por fila de la tabla 1.4 del Vol. 6 (68 filas). Topes de nivel: usa el Vol. 6/9 (tope por paso).

### 2.6 `rem_characters.txt` — `[CHAR_<SLUG>]` (≥ 25; todos los del Vol. 7)
`Name`, `Role`, `Category` (Protagonista, Aliado, Rival, Líder de Gimnasio, Alto Mando, Campeón, Equipo Morfeo, Dominante, PNJ),
`Aliases`, `Age`, `Appearance`, `Personality`, `Backstory`, `Motivation`, `Arc`, `FirstLocation` (LOC_KEY), `Locations` (lista `;` de LOC_KEY),
`TypeSpecialty`, `Team` (conserva marcadores `[PENDIENTE DE ASIGNACIÓN]`), `Quotes` (repetible). Añade las claves que existan en el Vol. 7.

### 2.7 `rem_story.txt`
`[PRELUDE]`, `[CHAPTER_01]`..`[CHAPTER_68]`, `[FRAGMENT_LEDGER]` (libro de cuentas de los 6 fragmentos). Claves: `Title`, `Act`, `LocationKey`,
`CharactersInScene` (lista `;` de nombres tal como aparecen), `NarrativeText` (**repetida: un párrafo por línea**, texto íntegro del Vol. 8), `Summary` (opcional).
Para `[FRAGMENT_LEDGER]`: `Fragment1`..`Fragment6` = `Nombre,Dominante,Ubicación(LOC_KEY),Capítulo(CHAPTER_NN),Nota`.

### 2.8 `rem_vanilla_baseline.txt` y `rem_changelog.txt`
Baseline = valores **originales** (sacados de `PBS_backup_original/`) para TODAS las entidades que cambian (Pokémon #001–#721, todos los movimientos, habilidades y objetos):
```
[POKEMON_001]   Name, Types (A,B), BaseStats (HP,ATK,DEF,SPE,SPA,SPD), Abilities (a,b), HiddenAbility, Evolutions (CHILD,Method,Param,...), Moves (lv,MOVE,...), EggMoves, WildItemCommon, WildItemUncommon, WildItemRare
[MOVE_MEGAHORN] Name, Type, Category, Power, Accuracy, PP, Priority? (si existe), FunctionCode, AddlEffect, Target, Flags, Description
[ABILITY_STENCH] Name, Description
[ITEM_POTION]   ID, Name, Pocket, Price, Description, FieldUse, BattleUse, Special, Move
[TM_VANILLA]    una línea por TM original: HONECLAWS = ESPECIE,ESPECIE... (opcional; puede omitirse si pesa)
```
Changelog = notas de diseño legibles (no cifras: las cifras las calcula la app): `[POKEMON_001]` `Role = ...` (rol REM de `Pokemon_Changes_Master.md`), `Note` (repetible),
`[ABILITY_ILLUMINATE]` `Status = Reworked|Buffed|Kept|Untouched`, `Note = ...`; `[MOVE_X]`/`[ITEM_X]` `Note`. Más `[META]` con `Volumes = 1-10`, `Generated = <fecha>`.

## 3. Archivos oficiales de `PBS/` que se inyectan (propietario: agente `pbs-core`, salvo `encounters.txt` → `rem-world`)

`abilities.txt` (Vol. 2: nombres intactos, descripciones nuevas de las 26 habilidades reelaboradas + Nieve/Heladura), `moves.txt` (`proposed_moves.txt`),
`pokemon.txt` (`proposed_pokemon.txt` + `proposed_learnsets.txt`; EggMoves vacío; habilidad oculta fusionada en 1–2 ranuras; WildItem* limpios),
`tm.txt` (`proposed_tm.txt`), `items.txt` (`proposed_items.txt`), `berryplants.txt` (sin las 20 bayas podadas), `encounters.txt` (formato PBS Essentials v16),
más limpieza de referencias a objetos podados en `btpokemon.txt`, `fancycuppm.txt`, `fancycupsinglepm.txt`, `littlecuppm.txt`, `pikacuppm.txt`, `pokecuppm.txt` y cualquier otro archivo que las contenga.

## 4. Contrato del backend (`codex/`) → JSON que consume el frontend

Servidor stdlib (`http.server`, sin dependencias obligatorias), puerto por defecto **8765**, `127.0.0.1`.

| Ruta | Respuesta |
|---|---|
| `GET /` | `pokedex_app/index.html` |
| `GET /app/<ruta>` | estáticos de `pokedex_app/` (js, css, fuentes) |
| `GET /gfx/<ruta>` | archivos bajo `Graphics/` (ruta relativa, p. ej. `/gfx/Icons/icon001.png`); 404 si no existe |
| `GET /map/<archivo>` | imágenes de `docs/Mapa/` y `docs/rebalance/assets/` (`/map/Mapa_Final__Esqueleto.png`) |
| `GET /api/model` | modelo completo (abajo). Cabecera `X-REM-Version`. Se reconstruye si cambia cualquier mtime de `PBS/*.txt` |
| `GET /api/version` | `{"version":"<hash>","mtimes":{"pokemon.txt":1730...,...},"serverTime":...}` (barato; el front lo consulta cada 3 s para recarga en vivo) |
| `GET /api/warnings` | `[Warning]` (ver abajo) |
| `GET /api/health` | `{"status":"ok|warn|error","errors":n,"warnings":n,"files":[FileInfo],"counts":{...}}` |
| `POST /api/reload` | fuerza reconstrucción; devuelve `{"ok":true,"version":...,"errors":n,"warnings":n}` |
| `GET /api/bundle` | el mismo modelo, servido desde `codex_bundle/model.json` (copia de seguridad pre-generada con `python3 start_codex.py --build-bundle`) |

Si `PBS/` no se puede leer, el servidor sirve el bundle (`meta.source = "bundle"`). **Ninguna excepción** de un archivo puede tumbar el servidor ni vaciar el modelo:
cada archivo/sección se parsea dentro de `try/except` y genera `Warning`s.

`Warning` = `{"file":"pokemon.txt","line":123,"severity":"error|warn|info","code":"UNKNOWN_TYPE","message":"Tipo desconocido «FUEGOO»","suggestion":"FIRE","text":"Type1=FUEGOO"}`
(`suggestion` = «¿quisiste decir…?» por distancia de edición/difflib; `null` si no hay).
`FileInfo` = `{"name":"pokemon.txt","exists":true,"size":765652,"mtime":1730000000.0,"lines":25248,"errors":0,"warnings":0}`.
Códigos mínimos: `UNKNOWN_TYPE`, `UNKNOWN_MOVE`, `UNKNOWN_ABILITY`, `UNKNOWN_ITEM`, `UNKNOWN_SPECIES`, `UNKNOWN_LOCATION`, `BAD_LINE`, `BAD_NUMBER`, `DUPLICATE_KEY`, `MISSING_FIELD`, `ENCODING`, `FILE_MISSING`.

### 4.1 Modelo (`GET /api/model`) — campos **obligatorios** (se pueden añadir más)

```jsonc
{
 "meta": {"source":"live|bundle","generatedAt":"ISO-8601","version":"…","health":{"status":"ok|warn|error","errors":0,"warnings":0},
          "counts":{"pokemon":721,"moves":765,"abilities":267,"items":414,"tms":100,"locations":64,"wildSlots":440,"fishSlots":32,"characters":0,"chapters":68,"steps":68,"shops":9,"missions":29}},
 "types":[{"sym":"FIRE","name":"Fuego","index":10}],            // index = fila (0..) en Graphics/Pictures/types.png (64x672, alto 28/fila? el backend calcula h=alto/nº de tipos) y pokedexTypes.png
 "pokemon":[{
   "dex":1,"sym":"BULBASAUR","name":"Bulbasaur","types":["GRASS","POISON"],
   "stats":{"hp":45,"atk":49,"def":49,"spa":65,"spd":65,"spe":45,"bst":318},
   "abilities":["OVERGROW","CHLOROPHYLL"],
   "evolutions":[{"to":2,"method":"Level","param":"16","text":"Nivel 16","item":null}],
   "evolvesFrom":null | {"from":1,"method":"Level","param":"16","text":"Nivel 16","item":null},
   "family":[1,2,3],
   "learnset":[{"lv":1,"move":"TACKLE"}],
   "tms":[9,22],                                    // números MT que puede aprender
   "kind":"Semilla","height":0.7,"weight":6.9,"color":"Green","habitat":"Grassland","pokedex":"texto|null",
   "role":"texto de rol REM|null",                  // de rem_changelog (Role)
   "obtain":[{"method":"WILD","loc":"RUTA_01","level":"3-5","detail":"…"}],     // de [SPECIAL_OBTAINABILITY]
   "wild":[{"loc":"RUTA_01","zone":null,"kind":"Land|Cave|Surf|Fish","rarity":"COMMON","pct":20,"day":[3,5],"night":[4,7],"note":"…"}],
   "baseline":{"types":["GRASS","POISON"],"stats":{"hp":45,…,"bst":318},"abilities":["OVERGROW"],"hiddenAbility":"CHLOROPHYLL","evolutions":[…],"moves":[{"lv":1,"move":"TACKLE"}]}|null,
   "diff":{"changed":true,"types":null|{"before":[…],"after":[…]},"stats":{"hp":0,"atk":3,…,"bst":3},"abilities":{"added":[],"removed":[]},
           "evolutions":false,"movesAdded":["…"],"movesRemoved":["…"],"badges":["Retipado","Stats","Habilidades","Evolución","Learnset"]}
 }],
 "moves":[{"id":1,"sym":"MEGAHORN","name":"Megacuerno","type":"BUG","category":"Physical|Special|Status","power":120,"accuracy":85,"pp":10,
           "priority":0,"fcode":"000","effectChance":0,"target":"00","flags":"abefh","description":"…",
           "tm":5|null,"learnedBy":[{"dex":1,"lv":13}],"tmLearners":[1,2],"baseline":{…mismos campos…}|null,"diff":{"changed":true,"fields":["power","pp"]}}],
 "abilities":[{"id":1,"sym":"STENCH","name":"Hedor","description":"…","holders":[44,45],"baseline":{"description":"…"}|null,
               "status":"Reworked|Buffed|Kept|Untouched|null","note":"texto changelog|null","changed":true}],
 "items":[{"id":1,"sym":"REPEL","name":"Repelente","plural":"Repelentes","pocket":1,"pocketName":"Objetos","price":350,"description":"…",
           "fieldUse":2,"battleUse":0,"special":0,"move":null,"tm":null,"icon":"Icons/item001.png"|null,"isNew":false,
           "where":[{"loc":"RUTA_01","qty":1,"method":"B","zone":"…","note":"…"}],"shops":[{"shop":"MART_0_MEDALS","price":200}],"missions":[2],
           "baseline":{…}|null,"diff":{"changed":true,"fields":["price"]}}],
 "tms":[{"number":1,"sym":"TM01","move":"PROTECT","name":"MT01","price":3000,"learners":[1,2],"where":[…igual que items.where…],"missions":[1]}],
 "locations":[{"key":"PUEBLO_IOLITA","name":"…","draftNames":[],"category":"Pueblo","act":"I","order":1,"node":1,"routeLabel":null,"coords":[136,232],"path":null,
               "conn":{"N":{"keys":[],"text":""},"S":{…},"E":{…},"O":{…}},"levelDay":[3,5]|null,"levelNight":[4,7]|null,"etymology":"…","situation":"…","description":"…",
               "events":["…"],"characters":["Ambrosio (Profesor)"],"charKeys":["CHAR_AMBROSIO"],"boss":"…",
               "encounters":[{"zone":null,"zoneName":null,"kind":"Land","slotCount":6,"slots":[{"slot":1,"rarity":"COMMON","pct":20,"dex":16,"sym":"PIDGEY","day":[3,5],"night":[4,7],"note":"…"}]}],
               "fishing":{"common":{"pct":70,"dex":129,"day":[10,12],"night":[15,18],"note":"…"},"rare":{…}}|null,
               "items":[…igual que items.where pero con "item":"POTION"…],"shops":["SHOP_X"],"steps":[1],"chapters":["CHAPTER_01"]}],
 "shops":[{"key":"MART_0_MEDALS","name":"…","medals":0|null,"cumulative":true,"location":null|"LOC_KEY","description":"","requirement":"",
           "items":[{"item":"POKEBALL","price":200}],"stock":[…lista acumulada resuelta, solo marts…]}],
 "missions":[{"n":1,"species":5,"item":"TM01","qty":1,"title":"…","note":"…"}],
 "progression":[{"step":1,"act":"I","loc":"PUEBLO_IOLITA","summary":"…","levelCapDay":5,"levelCapNight":5,"boss":"…","bossType":"…","bossLevel":16,"tms":["TM01"],"keyItems":["…"]}],
 "characters":[{"key":"CHAR_AMBROSIO","name":"…","role":"…","category":"…", /* + todas las claves del INI en minúscula camelCase */ "locations":["PUEBLO_IOLITA"]}],
 "story":[{"key":"CHAPTER_01","title":"…","act":"I","loc":"PUEBLO_IOLITA","characters":["…"],"charKeys":["…"],"paragraphs":["…"],"summary":null}],
 "prelude":{…igual que story…}|null,"ledger":[{"n":1,"name":"…","dominant":"…","loc":"…","chapter":"CHAPTER_12","note":"…"}],
 "assets":{"icons":[1,2,…],"battlers":[1,2,…],"battlersBack":[…],"battlersShiny":[…],"itemIcons":["item001.png",…],"missing":[]}, // qué ficheros existen en Graphics/
 "warnings":[…Warning…],"files":[…FileInfo…]
}
```
Resolución cruzada obligatoria en el backend (el front no recalcula): `pokemon.wild/obtain`, `moves.learnedBy/tmLearners`, `abilities.holders`, `items.where/shops/missions`,
`locations.encounters/items/steps/chapters/charKeys`, `family`, `evolvesFrom`, `diff`. Nombres/símbolos desconocidos con typo → corrección difusa + `Warning` (`suggestion`).

## 5. Contrato del frontend (`pokedex_app/`)

Un único `index.html` + módulos `<script>` clásicos (sin bundler, sin CDN: **todo local y offline**). SPA con **ruteo por hash**:

`#/` Inicio · `#/pokedex` · `#/pokemon/<dex>` · `#/moves` · `#/move/<SYM>` · `#/abilities` · `#/ability/<SYM>` · `#/items` · `#/item/<SYM>` · `#/tms` · `#/tm/<n>` ·
`#/shops` · `#/missions` · `#/map` · `#/atlas` · `#/location/<KEY>` · `#/progression` · `#/progression/<step>` · `#/characters` · `#/character/<KEY>` · `#/story` · `#/story/<CHAPTER_KEY>` · `#/warnings`.

Navbar (7 secciones + extras): **Inicio · Pokédex Maestra · Movimientos y Habilidades · Objetos, MT y Tiendas · Mapa y Atlas · Progresión · Personajes y Crónicas**, buscador global (`Ctrl+K`),
botón «🔄 Recargar PBS en Vivo», «⚠️ Avisos de Sintaxis PBS (n)», indicador de salud del PBS, tema claro/oscuro.

Espacio de nombres global `REM` (lo define `js/core.js`; **no cambiar firmas**):
```
REM.state = {model, version, route}            REM.api.load() / reload() / poll()    REM.on(event, fn) / REM.emit(event, data)   // eventos: 'model','route','warnings'
REM.router.register(prefix, {title, render(el, parts, query)})   REM.router.go('#/pokemon/1')   REM.router.href(kind, id) -> '#/…'
REM.h(tag, attrs, ...children) -> HTMLElement      REM.esc(str)      REM.fmtRange([a,b]) -> "3–5" | "—"      REM.pct(n)      REM.num(n)
REM.idx = {pokemonByDex, pokemonBySym, moveBySym, abilityBySym, itemBySym, tmByNum, locByKey, charByKey, chapterByKey, shopByKey, typeBySym}   // construidos al cargar
REM.ui.link(kind, id, label?) -> <a>   // kind ∈ pokemon|move|ability|item|tm|location|character|chapter|step|shop
REM.ui.typeBadge(sym) -> <span>  REM.ui.categoryBadge('Physical|Special|Status')  REM.ui.pokeIcon(dex,{size}) -> <span> (primer cuadro de Icons/iconNNN.png, recorte CSS)
REM.ui.pokeSprite(dex,{back,shiny,size}) -> <canvas> (primer fotograma de Battlers/NNN.png)  REM.ui.itemIcon(sym)  REM.ui.diffBadges(entity)  REM.ui.statBars(pokemon)
REM.ui.table(columns, rows, opts) (ordenable, filtrable)   REM.ui.toast(msg, kind)   REM.ui.empty(msg)   REM.ui.pager(...)
REM.search.query(text) -> [{kind,id,label,sub}]    REM.search.open()
```
Cada vista vive en `js/view_<nombre>.js` y se registra con `REM.router.register(...)`. Todo enlace entre entidades usa `REM.ui.link`. Cada vista debe sobrevivir a datos ausentes
(`null`/listas vacías → mensaje «Sin datos»), nunca lanzar excepciones no capturadas y **no producir errores de consola**.
Estilos en `css/codex.css` con variables CSS y tema oscuro; responsive; accesible (foco visible, `aria-label`).

## 6. Propiedad de archivos (un solo escritor por archivo)

| Agente | Escribe |
|---|---|
| `pbs-core` | `PBS/{abilities,moves,pokemon,items,tm,berryplants}.txt`, limpieza de `btpokemon.txt` y `*cuppm.txt`, `tools/rebalance/phase1/inject_core.py`, `tools/rebalance/phase1/pbs_check.py` |
| `rem-world` | `PBS/rem_locations.txt`, `PBS/rem_encounters.txt`, `PBS/encounters.txt`, `tools/rebalance/phase1/build_world.py` |
| `rem-items` | `PBS/rem_location_items.txt`, `PBS/rem_shops.txt`, `tools/rebalance/phase1/build_items_shops.py` |
| `rem-narrative` | `PBS/rem_progression.txt`, `PBS/rem_characters.txt`, `PBS/rem_story.txt`, `tools/rebalance/phase1/build_narrative.py` |
| `rem-baseline` | `PBS/rem_vanilla_baseline.txt`, `PBS/rem_changelog.txt`, `tools/rebalance/phase1/build_baseline.py` |
| `codex-backend` | `codex/*.py`, `start_codex.py`, `start_codex.command`, `start_codex.bat`, `run_pokedex.py`, `codex_bundle/` |
| `codex-front-core` | `pokedex_app/index.html`, `pokedex_app/css/*`, `pokedex_app/js/{core,ui,search,view_home,view_pokedex,view_moves_abilities,view_items,view_warnings}.js` |
| `codex-front-world` | `pokedex_app/js/{view_map,view_atlas,view_progression,view_characters,view_story}.js`, `pokedex_app/css/world.css` |
