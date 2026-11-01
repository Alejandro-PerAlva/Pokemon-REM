"""Parsers de los archivos oficiales de ``PBS/`` (formatos de Essentials v16, ver ``178_Compiler.rb``).

Cada ``parse_*`` recibe un ``TextFile`` y un ``Issues`` y devuelve registros crudos con números de línea.
Validan la SINTAXIS (campos, números, comillas, secciones); la resolución de símbolos entre archivos
(tipos, movimientos, objetos…) se hace después en ``model.py``. Ninguna función lanza excepciones.
"""
import re

from .fuzzy import Lookup, norm, parse_int, fix_number
from .ini import csv_fields, parse_ini, split_list

# --------------------------------------------------------------------------------------- constantes PBS
STAT_ORDER = ["hp", "atk", "def", "spe", "spa", "spd"]            # orden de BaseStats / EffortPoints en PBS
EVONAMES = ["Unknown", "Happiness", "HappinessDay", "HappinessNight", "Level", "Trade", "TradeItem", "Item",
            "AttackGreater", "AtkDefEqual", "DefenseGreater", "Silcoon", "Cascoon", "Ninjask", "Shedinja", "Beauty",
            "ItemMale", "ItemFemale", "DayHoldItem", "NightHoldItem", "HasMove", "HasInParty", "LevelMale",
            "LevelFemale", "Location", "TradeSpecies", "LevelDay", "LevelNight", "LevelDarkInParty", "LevelRain",
            "HappinessMoveType", "LevelForm0", "LevelForm1", "LevelForm2", "ItemForm0", "ItemForm1", "ItemForm2",
            "HappinessForm0", "HappinessForm1", "HappinessForm2", "LevelDayForm0", "LevelDayForm1", "LevelDayForm2",
            "LevelNightForm0", "LevelNightForm1", "LevelNightForm2", "HoldItemForm0", "HoldItemForm1", "HoldItemForm2",
            "LevelDayTime", "Crits", "HasMoveForm0", "HasMoveForm1", "HasMoveForm2"]
# 0 = sin parámetro, 1 = entero, 2 = objeto, 3 = movimiento, 4 = especie, 5 = tipo
EVOPARAM = [0, 0, 0, 0, 1, 0, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 4, 1, 1, 1, 4, 1, 1, 1, 1, 5,
            1, 1, 1, 2, 2, 2, 0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 1, 0, 3, 3, 3]
EVOPARAM_BY_NAME = {EVONAMES[i]: EVOPARAM[i] for i in range(len(EVONAMES))}
EVO_LOOKUP = Lookup("método de evolución", "método de evolución")
for _n in EVONAMES[1:]:
    EVO_LOOKUP.add(_n)

POCKET_NAMES = ["", "Objetos", "Medicinas", "Poké Balls", "MT / MO", "Bayas", "Cartas", "Objetos de combate", "Objetos clave"]
CATEGORIES = ("Physical", "Special", "Status")
CATEGORY_LOOKUP = Lookup("categoría", "categoría", fem=True)
for _c, _alias in (("Physical", "Físico"), ("Special", "Especial"), ("Status", "Estado")):
    CATEGORY_LOOKUP.add(_c, _alias)

HABITATS = ["", "Grassland", "Forest", "WatersEdge", "Sea", "Cave", "Mountain", "RoughTerrain", "Urban", "Rare"]
GENDER_RATES = ["AlwaysMale", "FemaleOneEighth", "Female25Percent", "Female50Percent", "Female75Percent",
                "FemaleSevenEighths", "AlwaysFemale", "Genderless"]
GROWTH_RATES = ["Medium", "MediumFast", "Erratic", "Fluctuating", "Parabolic", "MediumSlow", "Fast", "Slow"]
ROSTER_MAX = 721      # el plantel de REM es solo #001-#721; el resto de secciones se ignora sin avisos
POKEMON_KEYS = {"name", "internalname", "type1", "type2", "basestats", "genderrate", "growthrate", "baseexp",
                "effortpoints", "rareness", "happiness", "abilities", "hiddenability", "moves", "eggmoves",
                "compatibility", "stepstohatch", "height", "weight", "color", "habitat", "regionalnumbers", "kind",
                "pokedex", "battlerplayery", "battlerenemyy", "battleraltitude", "evolutions", "formnames",
                "wilditemcommon", "wilditemuncommon", "wilditemrare", "incense", "compat", "wilditem"}


def _csv_line(file, n, raw, iss, min_fields, label):
    """Línea CSV -> campos; avisa de comillas mal cerradas. Devuelve None si la línea está vacía/comentada."""
    s = raw.strip()
    if not s or s[0] == "#":
        return None
    fields, ok = csv_fields(s)
    if not ok:
        iss.add(file, n, "warn", "BAD_LINE", "Comillas mal cerradas o texto tras el cierre de un campo entrecomillado", text=raw)
    return fields


# --------------------------------------------------------------------------------------------- types.txt
def parse_types(tf, iss):
    out = []
    if not tf.ok:
        return out
    secs = parse_ini(tf, iss, "types.txt")
    for s in secs:
        try:
            m = re.match(r"^\d+$", s.key)
            if not m:
                iss.add("types.txt", s.line, "error", "BAD_LINE", "Sección de tipo inválida [%s]: se esperaba un número" % s.key)
                continue
            tid = int(s.key)
            sym = s.first("InternalName").strip()
            name = s.first("Name").strip()
            if not sym:
                iss.add("types.txt", s.line, "error", "MISSING_FIELD", "Falta InternalName en el tipo [%d]" % tid,
                        text="[%d]" % tid)
                if not name:
                    continue
                sym = re.sub(r"[^A-Z0-9]", "", name.upper())
            if not name:
                iss.add("types.txt", s.line, "warn", "MISSING_FIELD", "Falta Name en el tipo %s" % sym)
                name = sym.capitalize()
            rec = {"id": tid, "line": s.line, "sym": sym, "name": name,
                   "weak": [(it.line, t.strip()) for it in s.all_items("Weaknesses") for t in it.value.split(",") if t.strip()],
                   "resist": [(it.line, t.strip()) for it in s.all_items("Resistances") for t in it.value.split(",") if t.strip()],
                   "immune": [(it.line, t.strip()) for it in s.all_items("Immunities") for t in it.value.split(",") if t.strip()],
                   "pseudo": s.first("IsPseudoType").lower() in ("true", "1", "yes", "si", "sí"),
                   "special": s.first("IsSpecialType").lower() in ("true", "1", "yes", "si", "sí")}
            out.append(rec)
        except Exception:
            iss.add("types.txt", getattr(s, "line", 0), "error", "BAD_LINE", "No se pudo interpretar esta sección de tipo")
    return out


# ----------------------------------------------------------------------------------------- abilities.txt
def parse_abilities(tf, iss):
    out = []
    f = "abilities.txt"
    for n, raw in enumerate(tf.lines, 1):
        try:
            fl = _csv_line(f, n, raw, iss, 4, "habilidad")
            if fl is None:
                continue
            if len(fl) < 3:
                iss.add(f, n, "error", "MISSING_FIELD", "Habilidad incompleta: se esperaban 4 campos (id,SÍMBOLO,Nombre,«Descripción»)", text=raw)
                if len(fl) < 2:
                    continue
            aid = parse_int(iss, f, n, "ID de habilidad", fl[0], default=None, text_line=raw)
            sym = fl[1].strip()
            if not sym:
                iss.add(f, n, "error", "MISSING_FIELD", "Habilidad sin símbolo", text=raw)
                continue
            name = fl[2].strip() if len(fl) > 2 else ""
            desc = ",".join(fl[3:]).strip() if len(fl) > 3 else ""
            if len(fl) <= 3:
                iss.add(f, n, "warn", "MISSING_FIELD", "Habilidad %s sin descripción" % sym, text=raw)
            out.append({"id": aid, "line": n, "sym": sym, "name": name or sym, "desc": desc})
        except Exception:
            iss.add(f, n, "error", "BAD_LINE", "Línea de habilidad ilegible", text=raw)
    return out


# --------------------------------------------------------------------------------------------- moves.txt
def parse_moves(tf, iss):
    out = []
    f = "moves.txt"
    for n, raw in enumerate(tf.lines, 1):
        try:
            fl = _csv_line(f, n, raw, iss, 14, "movimiento")
            if fl is None:
                continue
            if len(fl) < 14:
                iss.add(f, n, "error" if len(fl) < 9 else "warn", "MISSING_FIELD",
                        "Movimiento incompleto: %d campos de 14 (id,SÍMBOLO,Nombre,código,daño,tipo,categoría,precisión,PP,prob.,objetivo,prioridad,banderas,«descripción»)" % len(fl),
                        text=raw)
                if len(fl) < 3:
                    continue
            while len(fl) < 14:
                fl.append("")
            if len(fl) > 14:
                iss.add(f, n, "info", "BAD_LINE", "El movimiento %s tiene %d campos (se leen 14; los sobrantes se ignoran, como hace el compilador)" % (fl[1].strip(), len(fl)), text=raw)
                fl = fl[:14]
            mid = parse_int(iss, f, n, "ID de movimiento", fl[0], default=None, text_line=raw)
            sym = fl[1].strip()
            if not sym:
                iss.add(f, n, "error", "MISSING_FIELD", "Movimiento sin símbolo", text=raw)
                continue
            fcode = fl[3].strip()
            if fcode and not re.fullmatch(r"[0-9A-Fa-f]{1,4}", fcode):
                iss.add(f, n, "error", "BAD_NUMBER", "Código de función no válido «%s» (se espera un número hexadecimal de hasta 4 dígitos)" % fcode, text=raw)
            rec = {"id": mid, "line": n, "sym": sym, "name": fl[2].strip() or sym, "fcode": fcode.upper() or "000",
                   "power": parse_int(iss, f, n, "Daño base de %s" % sym, fl[4], default=0, text_line=raw),
                   "type": fl[5].strip(), "category": fl[6].strip(),
                   "accuracy": parse_int(iss, f, n, "Precisión de %s" % sym, fl[7], default=0, text_line=raw),
                   "pp": parse_int(iss, f, n, "PP de %s" % sym, fl[8], default=0, text_line=raw),
                   "effectChance": parse_int(iss, f, n, "Probabilidad de efecto de %s" % sym, fl[9], default=0, text_line=raw),
                   "target": fl[10].strip() or "00",
                   "priority": parse_int(iss, f, n, "Prioridad de %s" % sym, fl[11], default=0, allow_negative=True, text_line=raw),
                   "flags": fl[12].strip(), "desc": fl[13].strip()}
            if rec["flags"] and not re.fullmatch(r"[a-zA-Z]*", rec["flags"]):
                iss.add(f, n, "warn", "BAD_LINE", "Banderas de movimiento no válidas «%s» (solo letras a-p)" % rec["flags"], text=raw)
            out.append(rec)
        except Exception:
            iss.add(f, n, "error", "BAD_LINE", "Línea de movimiento ilegible", text=raw)
    return out


# --------------------------------------------------------------------------------------------- items.txt
def parse_items(tf, iss):
    out = []
    f = "items.txt"
    for n, raw in enumerate(tf.lines, 1):
        try:
            fl = _csv_line(f, n, raw, iss, 10, "objeto")
            if fl is None:
                continue
            if len(fl) < 10:
                iss.add(f, n, "error" if len(fl) < 6 else "warn", "MISSING_FIELD",
                        "Objeto incompleto: %d campos de 10-11 (id,SÍMBOLO,Nombre,Plural,bolsillo,precio,«descripción»,uso,combate,especial[,movimiento])" % len(fl),
                        text=raw)
                if len(fl) < 3:
                    continue
            while len(fl) < 11:
                fl.append("")
            if len(fl) > 11:
                fl = fl[:11]
            iid = parse_int(iss, f, n, "ID de objeto", fl[0], default=None, text_line=raw)
            sym = fl[1].strip()
            if not sym:
                iss.add(f, n, "error", "MISSING_FIELD", "Objeto sin símbolo", text=raw)
                continue
            out.append({"id": iid, "line": n, "sym": sym, "name": fl[2].strip() or sym, "plural": fl[3].strip(),
                        "pocket": parse_int(iss, f, n, "Bolsillo de %s" % sym, fl[4], default=1, text_line=raw),
                        "price": parse_int(iss, f, n, "Precio de %s" % sym, fl[5], default=0, text_line=raw),
                        "desc": fl[6].strip(),
                        "fieldUse": parse_int(iss, f, n, "Uso fuera de combate de %s" % sym, fl[7], default=0, text_line=raw),
                        "battleUse": parse_int(iss, f, n, "Uso en combate de %s" % sym, fl[8], default=0, text_line=raw),
                        "special": parse_int(iss, f, n, "Tipo especial de %s" % sym, fl[9], default=0, text_line=raw),
                        "move": fl[10].strip()})
        except Exception:
            iss.add(f, n, "error", "BAD_LINE", "Línea de objeto ilegible", text=raw)
    return out


# ------------------------------------------------------------------------------------------------ tm.txt
def parse_tm(tf, iss):
    """[MOVIMIENTO] + líneas de especies separadas por comas. -> [{move, line, species:[(line,raw)]}]"""
    out = []
    f = "tm.txt"
    cur = None
    for n, raw in enumerate(tf.lines, 1):
        try:
            s = raw.strip()
            if not s or s[0] == "#":
                continue
            m = re.match(r"^\[\s*([^\]]*?)\s*\]\s*(.*)$", s)
            if m:
                cur = {"move": m.group(1).strip(), "line": n, "species": []}
                if not cur["move"]:
                    iss.add(f, n, "error", "BAD_LINE", "Sección de MT sin nombre de movimiento", text=raw)
                    cur = None
                    continue
                out.append(cur)
                continue
            if s.startswith("["):
                iss.add(f, n, "error", "BAD_LINE", "Cabecera de MT sin «]»", text=raw)
                continue
            if cur is None:
                iss.add(f, n, "error", "BAD_LINE", "Especies antes de la primera sección [MOVIMIENTO]: se ignoran", text=raw)
                continue
            for tok in s.split(","):
                tok = tok.strip()
                if tok:
                    cur["species"].append((n, tok))
        except Exception:
            iss.add(f, n, "error", "BAD_LINE", "Línea de tm.txt ilegible", text=raw)
    return out


# ----------------------------------------------------------------------------------------- berryplants.txt
def parse_berryplants(tf, iss):
    out = []
    f = "berryplants.txt"
    for n, raw in enumerate(tf.lines, 1):
        try:
            s = raw.strip()
            if not s or s[0] == "#":
                continue
            if "=" not in s:
                iss.add(f, n, "warn", "BAD_LINE", "Línea sin «=» (se esperaba BAYA=horas,secado,mín,máx)", text=raw)
                continue
            k, v = s.split("=", 1)
            vals = []
            toks = [t.strip() for t in v.split(",")]
            for i, t in enumerate(toks):
                vals.append(parse_int(iss, f, n, "valor %d de la planta %s" % (i + 1, k.strip()), t, default=0, text_line=raw))
            if len(vals) < 4:
                iss.add(f, n, "warn", "MISSING_FIELD", "Planta de baya incompleta: %d valores de 4" % len(vals), text=raw)
                vals += [0] * (4 - len(vals))
            out.append({"line": n, "item": k.strip(), "values": vals})
        except Exception:
            iss.add(f, n, "warn", "BAD_LINE", "Línea de berryplants.txt ilegible", text=raw)
    return out


# --------------------------------------------------------------------------------------------- pokemon.txt
def _num_list(iss, f, line, label, text, count=None, text_line=None, allow_float=False):
    vals = []
    toks = [t.strip() for t in (text or "").split(",")]
    for i, t in enumerate(toks):
        if t == "":
            vals.append(None)
            continue
        v = parse_int(iss, f, line, "%s (posición %d)" % (label, i + 1), t, default=None, text_line=text_line)
        vals.append(v)
    return vals


def parse_pokemon(tf, iss):
    """Devuelve registros crudos por especie. ``stats`` puede contener ``None`` en posiciones irrecuperables."""
    f = "pokemon.txt"
    out = []
    if not tf.ok:
        return out
    def _out(sec):
        return sec.key.isdigit() and int(sec.key) > ROSTER_MAX

    secs = parse_ini(tf, iss, f, known=lambda sec: (POKEMON_KEYS, []), skip=_out, single=["Name", "InternalName", "Type1", "Type2", "BaseStats", "Abilities",
                                                              "HiddenAbility", "Moves", "Evolutions", "Kind", "Pokedex"])
    seen = {}
    for s in secs:
        try:
            if not re.fullmatch(r"\d+", s.key):
                iss.add(f, s.line, "error", "BAD_LINE", "Sección de Pokémon inválida [%s]: se esperaba el número de Pokédex" % s.key, text=s.raw_header)
                continue
            dex = int(s.key)
            if dex > ROSTER_MAX:
                out.append({"dex": dex, "line": s.line, "outside": True, "sym": s.last("InternalName").strip(), "name": s.last("Name").strip()})
                continue
            if dex == 0:
                iss.add(f, s.line, "error", "BAD_NUMBER", "Una especie no puede numerarse como 0", text=s.raw_header)
                continue
            if dex in seen:
                iss.add(f, s.line, "error", "DUPLICATE_KEY", "Sección [%d] duplicada (la anterior está en la línea %d); se usa la última" % (dex, seen[dex]), text=s.raw_header)
            seen[dex] = s.line
            g = lambda k: s.last(k).strip()
            gl = lambda k: s.line_of(k)
            rec = {"dex": dex, "line": s.line, "sec": s}
            rec["name"] = g("Name")
            rec["sym"] = g("InternalName")
            if not rec["sym"]:
                iss.add(f, s.line, "error", "MISSING_FIELD", "Falta InternalName en la especie [%d]" % dex, text=s.raw_header)
                rec["sym"] = re.sub(r"[^A-Z0-9]", "", (rec["name"] or ("SPECIES%d" % dex)).upper()) or ("SPECIES%d" % dex)
            if not rec["name"]:
                iss.add(f, s.line, "warn", "MISSING_FIELD", "Falta Name en la especie %s" % rec["sym"], text=s.raw_header)
                rec["name"] = rec["sym"].capitalize()
            rec["type1"] = (gl("Type1"), g("Type1"))
            rec["type2"] = (gl("Type2"), g("Type2"))
            if not rec["type1"][1]:
                iss.add(f, s.line, "error", "MISSING_FIELD", "Falta Type1 en %s [%d]" % (rec["sym"], dex), text=s.raw_header)
            bs = g("BaseStats")
            if not bs:
                iss.add(f, s.line, "error", "MISSING_FIELD", "Falta BaseStats en %s [%d]" % (rec["sym"], dex), text=s.raw_header)
                rec["stats"] = None
            else:
                vals = _num_list(iss, f, gl("BaseStats"), "BaseStats de %s" % rec["sym"], bs, text_line=None)
                if len(vals) != 6:
                    iss.add(f, gl("BaseStats"), "error", "MISSING_FIELD",
                            "BaseStats de %s tiene %d valores (se esperaban 6: PS,Ataque,Defensa,Velocidad,At.Esp.,Def.Esp.)" % (rec["sym"], len(vals)))
                    vals = (vals + [None] * 6)[:6]
                rec["stats"] = vals
            rec["statsLine"] = gl("BaseStats")
            ev = g("EffortPoints")
            rec["ev"] = _num_list(iss, f, gl("EffortPoints"), "EffortPoints de %s" % rec["sym"], ev) if ev else None
            rec["kind"] = g("Kind")
            rec["pokedex"] = s.last("Pokedex").strip()
            rec["color"] = g("Color")
            rec["habitat"] = g("Habitat")
            rec["genderRate"] = g("GenderRate")
            rec["growthRate"] = g("GrowthRate")
            for key, field, label in (("BaseEXP", "baseExp", "BaseEXP"), ("Rareness", "catchRate", "Rareness"),
                                      ("Happiness", "baseHappiness", "Happiness"), ("StepsToHatch", "stepsToHatch", "StepsToHatch")):
                t = g(key)
                rec[field] = parse_int(iss, f, gl(key), "%s de %s" % (label, rec["sym"]), t, default=None) if t else None
            for key, field in (("Height", "height"), ("Weight", "weight")):
                t = g(key)
                val = None
                if t:
                    try:
                        val = float(t.replace(",", "."))
                    except ValueError:
                        v, sg = fix_number(t, allow_float=True)
                        if v is not None:
                            iss.add(f, gl(key), "error", "BAD_NUMBER", "Número mal formado en %s de %s: «%s»; se interpreta como %s" % (key, rec["sym"], t, sg),
                                    suggestion=sg, applied=True)
                            val = float(v)
                        else:
                            iss.add(f, gl(key), "error", "BAD_NUMBER", "Número mal formado en %s de %s: «%s»; se ignora" % (key, rec["sym"], t))
                rec[field] = val
            rec["compat"] = [t.strip() for t in g("Compatibility").split(",") if t.strip()] or [t.strip() for t in g("Compat").split(",") if t.strip()]
            rec["regional"] = [t.strip() for t in g("RegionalNumbers").split(",") if t.strip()]
            rec["abilities"] = [(gl("Abilities"), t.strip()) for t in g("Abilities").split(",") if t.strip()]
            rec["hidden"] = [(gl("HiddenAbility"), t.strip()) for t in g("HiddenAbility").split(",") if t.strip()]
            mv = g("Moves")
            moves = []
            if mv:
                toks = [t.strip() for t in mv.split(",")]
                ln = gl("Moves")
                if len(toks) % 2:
                    iss.add(f, ln, "error", "BAD_LINE", "Moves de %s: número impar de campos (se esperan pares nivel,MOVIMIENTO); se ignora el último" % rec["sym"])
                for i in range(0, len(toks) - 1, 2):
                    lv = parse_int(iss, f, ln, "nivel del movimiento %s en %s" % (toks[i + 1], rec["sym"]), toks[i], default=None)
                    if lv is None:
                        continue
                    moves.append((ln, lv, toks[i + 1]))
            rec["moves"] = moves
            em = g("EggMoves")
            rec["eggMoves"] = [(gl("EggMoves"), t.strip()) for t in em.split(",") if t.strip()]
            ev_raw = g("Evolutions")
            evos = []
            if ev_raw:
                toks = [t.strip() for t in ev_raw.split(",")]
                ln = gl("Evolutions")
                if len(toks) % 3:
                    iss.add(f, ln, "error", "BAD_LINE", "Evolutions de %s: los campos no son múltiplos de 3 (HIJO,Método,Parámetro)" % rec["sym"])
                    toks += [""] * (3 - len(toks) % 3)
                for i in range(0, len(toks), 3):
                    if toks[i]:
                        evos.append((ln, toks[i], toks[i + 1], toks[i + 2]))
            rec["evos"] = evos
            rec["wild"] = {"common": (gl("WildItemCommon"), g("WildItemCommon")),
                           "uncommon": (gl("WildItemUncommon"), g("WildItemUncommon")),
                           "rare": (gl("WildItemRare"), g("WildItemRare")),
                           "incense": (gl("Incense"), g("Incense"))}
            out.append(rec)
        except Exception as e:
            iss.add(f, getattr(s, "line", 0), "error", "BAD_LINE", "No se pudo interpretar la sección [%s] (%s)" % (getattr(s, "key", "?"), e.__class__.__name__))
    return out


# -------------------------------------------------------------------- encounters.txt / btpokemon / copas
_ENC_TYPES = {"land", "landmorning", "landday", "landnight", "bugcontest", "cave", "water", "rocksmash", "oldrod", "goodrod",
              "superrod", "headbuttlow", "headbutthigh", "pokeradar", "flytrap", "headbutt"}


def parse_official_encounters(tf, iss):
    """Valida el encounters.txt de Essentials (por mapa). Devuelve [{map, line, tables:{tipo:[(line,especie,min,max)]}}]."""
    f = "encounters.txt"
    maps = []
    if not tf.ok:
        return maps
    cur = None
    ctype = None
    for n, raw in enumerate(tf.lines, 1):
        try:
            s = raw.strip()
            if not s:
                continue
            if s[0] == "#":
                continue
            s = s.split("#", 1)[0].strip() if re.match(r"^\d+\s*#", s) else s
            if re.fullmatch(r"\d+", s):
                cur = {"map": int(s), "line": n, "tables": {}, "dens": None}
                maps.append(cur)
                ctype = None
                continue
            if cur is None:
                iss.add(f, n, "warn", "BAD_LINE", "Línea antes del primer ID de mapa; se ignora", text=raw)
                continue
            if norm(s) in _ENC_TYPES and "," not in s:
                ctype = norm(s)
                cur["tables"].setdefault(ctype, [])
                continue
            parts = [p.strip() for p in s.split(",")]
            if cur["dens"] is None and ctype is None and len(parts) >= 3 and all(re.fullmatch(r"\d+", p) for p in parts):
                cur["dens"] = [int(p) for p in parts]
                continue
            if ctype is None:
                iss.add(f, n, "warn", "BAD_LINE", "Tipo de encuentro desconocido «%s»" % s, text=raw)
                continue
            if len(parts) < 2:
                iss.add(f, n, "error", "BAD_LINE", "Se esperaba «ESPECIE,nivelMin[,nivelMax]»", text=raw)
                continue
            lo = parse_int(iss, f, n, "nivel mínimo", parts[1], default=None, text_line=raw)
            hi = parse_int(iss, f, n, "nivel máximo", parts[2], default=lo, text_line=raw) if len(parts) > 2 else lo
            cur["tables"][ctype].append((n, parts[0], lo, hi))
        except Exception:
            iss.add(f, n, "warn", "BAD_LINE", "Línea de encounters.txt ilegible", text=raw)
    return maps


def parse_battle_pokemon(tf, iss):
    """btpokemon.txt / *cuppm.txt: ESPECIE;OBJETO;NATURALEZA;EVS;MOV1,MOV2,MOV3,MOV4. -> [{line,species,item,moves}]"""
    out = []
    f = tf.name
    for n, raw in enumerate(tf.lines, 1):
        try:
            s = raw.strip()
            if not s or s[0] == "#":
                continue
            parts = [p.strip() for p in s.split(";")]
            if len(parts) < 5:
                iss.add(f, n, "warn", "MISSING_FIELD", "Pokémon de torneo incompleto: %d campos de 5 (ESPECIE;OBJETO;NATURALEZA;EVS;MOVIMIENTOS)" % len(parts), text=raw)
                if len(parts) < 2:
                    continue
            moves = [m.strip() for m in (parts[4] if len(parts) > 4 else "").split(",") if m.strip()]
            out.append({"line": n, "species": parts[0], "item": parts[1] if len(parts) > 1 else "", "moves": moves})
        except Exception:
            iss.add(f, n, "warn", "BAD_LINE", "Línea ilegible", text=raw)
    return out
