"""Construcción de las entidades «oficiales» (tipos, habilidades, movimientos, objetos, Pokémon, MT) a partir
de los registros crudos de ``pbs.py``, resolviendo símbolos con corrección difusa y avisos."""
import re

from . import pbs
from .fuzzy import Lookup, Resolver, norm
from .pbs import EVOPARAM_BY_NAME, POCKET_NAMES, STAT_ORDER

DEFAULT_TYPES = [("NORMAL", "Normal"), ("FIGHTING", "Lucha"), ("FLYING", "Volador"), ("POISON", "Veneno"), ("GROUND", "Tierra"),
                 ("ROCK", "Roca"), ("BUG", "Bicho"), ("GHOST", "Fantasma"), ("STEEL", "Acero"), ("QMARKS", "???"),
                 ("FIRE", "Fuego"), ("WATER", "Agua"), ("GRASS", "Planta"), ("ELECTRIC", "Eléctrico"), ("PSYCHIC", "Psíquico"),
                 ("ICE", "Hielo"), ("DRAGON", "Dragón"), ("DARK", "Siniestro"), ("FAIRY", "Hada")]

_TM_RE = re.compile(r"^TM(\d{1,3})$", re.I)


class Core:
    """Resultado de construir las entidades oficiales."""

    def __init__(self):
        self.types = []
        self.abilities = []
        self.moves = []
        self.items = []
        self.pokemon = []
        self.tm_sections = []       # [{"move": sym, "dex": [..], "line": n}]
        self.berries = []
        self.official_enc = []
        self.Lt = Lookup("tipo", "tipo")
        self.La = Lookup("habilidad", "habilidad", fem=True)
        self.Lm = Lookup("movimiento", "movimiento")
        self.Li = Lookup("objeto", "objeto")
        self.Ls = Lookup("especie", "especie", fem=True)
        self.by_dex = {}
        self.sym_dex = {}
        self.move_by_sym = {}
        self.item_by_sym = {}
        self.ability_by_sym = {}
        self.type_by_sym = {}


def _dedupe(records, key, file, iss, what):
    """Elimina duplicados por clave (gana el último, como en el compilador) avisando."""
    seen = {}
    out = []
    for r in records:
        k = r[key]
        if k in seen:
            iss.add(file, r["line"], "error", "DUPLICATE_KEY",
                    "%s «%s» duplicad%s (primera definición en la línea %d); se usa la última" % (what.capitalize(), k, "a" if what.endswith("a") else "o", seen[k]["line"]))
            out[out.index(seen[k])] = r
            seen[k] = r
            continue
        seen[k] = r
        out.append(r)
    return out


def _assign_ids(records, file, iss):
    used = {r["id"] for r in records if r.get("id") is not None}
    nxt = (max(used) if used else 0) + 1
    for r in records:
        if r.get("id") is None:
            r["id"] = nxt
            nxt += 1


# ------------------------------------------------------------------------------------------------ tipos
def build_types(raw, iss, res, core):
    types = []
    if not raw:
        types = [{"sym": s, "name": n, "index": i, "weaknesses": [], "resistances": [], "immunities": [], "pseudo": s == "QMARKS", "special": False}
                 for i, (s, n) in enumerate(DEFAULT_TYPES)]
        for t in types:
            core.Lt.add(t["sym"], t["name"])
        core.types = types
        core.type_by_sym = {t["sym"]: t for t in types}
        return
    raw = _dedupe(raw, "sym", "types.txt", iss, "tipo")
    for r in raw:
        core.Lt.add(r["sym"], r["name"])
    for r in raw:
        try:
            rel = {}
            for key in ("weak", "resist", "immune"):
                lst = []
                for ln, tok in r[key]:
                    t = res.ref(core.Lt, tok, "types.txt", ln, "UNKNOWN_TYPE", context="el tipo %s" % r["sym"])
                    if t and t not in lst:
                        lst.append(t)
                rel[key] = lst
            types.append({"sym": r["sym"], "name": r["name"], "index": r["id"], "weaknesses": rel["weak"], "resistances": rel["resist"],
                          "immunities": rel["immune"], "pseudo": r["pseudo"], "special": r["special"]})
        except Exception:
            iss.add("types.txt", r.get("line", 0), "error", "BAD_LINE", "No se pudo construir el tipo %s" % r.get("sym"))
    types.sort(key=lambda t: t["index"])
    core.types = types
    core.type_by_sym = {t["sym"]: t for t in types}


# ------------------------------------------------------------------------------------------ habilidades
def build_abilities(raw, iss, res, core):
    raw = _dedupe(raw, "sym", "abilities.txt", iss, "habilidad")
    _assign_ids(raw, "abilities.txt", iss)
    out = []
    for r in raw:
        out.append({"id": r["id"], "sym": r["sym"], "name": r["name"], "description": r["desc"], "line": r["line"]})
        core.La.add(r["sym"], r["name"])
    out.sort(key=lambda a: a["id"])
    core.abilities = out
    core.ability_by_sym = {a["sym"]: a for a in out}


# ------------------------------------------------------------------------------------------ movimientos
def build_moves(raw, iss, res, core, baseline=None):
    raw = _dedupe(raw, "sym", "moves.txt", iss, "movimiento")
    _assign_ids(raw, "moves.txt", iss)
    out = []
    for r in raw:
        core.Lm.add(r["sym"], r["name"])
    for r in raw:
        try:
            bl = (baseline or {}).get(r["sym"])
            t = res.ref(core.Lt, r["type"], "moves.txt", r["line"], "UNKNOWN_TYPE", context="el movimiento %s" % r["sym"]) if r["type"] else None
            if not t:
                if not r["type"]:
                    iss.add("moves.txt", r["line"], "error", "MISSING_FIELD", "El movimiento %s no tiene tipo" % r["sym"])
                t = (bl or {}).get("type") or "NORMAL"
                iss.add("moves.txt", r["line"], "warn", "UNKNOWN_TYPE", "Se usa %s provisionalmente como tipo de %s" % (t, r["sym"]), suggestion=t, applied=True)
            cat = pbs.CATEGORY_LOOKUP.lookup(r["category"])[0] if r["category"] else None
            if not cat:
                if r["category"]:
                    sug = pbs.CATEGORY_LOOKUP.suggest(r["category"])
                    cat = sug.sym if sug else None
                    iss.add("moves.txt", r["line"], "error", "UNKNOWN_CATEGORY",
                            "Categoría desconocida «%s» en %s%s" % (r["category"], r["sym"], ("; se usa «%s»" % cat) if cat else ""),
                            suggestion=sug.sym if sug else "Physical, Special o Status", applied=bool(cat))
                else:
                    iss.add("moves.txt", r["line"], "error", "MISSING_FIELD", "Falta la categoría del movimiento %s" % r["sym"])
                if not cat:
                    cat = (bl or {}).get("category") or ("Status" if not r["power"] else "Physical")
            out.append({"id": r["id"], "sym": r["sym"], "name": r["name"], "type": t, "category": cat, "power": r["power"],
                        "accuracy": r["accuracy"], "pp": r["pp"], "priority": r["priority"], "fcode": r["fcode"],
                        "effectChance": r["effectChance"], "target": r["target"], "flags": r["flags"],
                        "description": r["desc"], "tm": None, "learnedBy": [], "tmLearners": [], "eggBy": [],
                        "baseline": None, "diff": {"changed": False, "fields": []}, "line": r["line"]})
        except Exception:
            iss.add("moves.txt", r.get("line", 0), "error", "BAD_LINE", "No se pudo construir el movimiento %s" % r.get("sym"))
    out.sort(key=lambda m: m["id"])
    core.moves = out
    core.move_by_sym = {m["sym"]: m for m in out}


# ---------------------------------------------------------------------------------------------- objetos
def build_items(raw, iss, res, core):
    raw = _dedupe(raw, "sym", "items.txt", iss, "objeto")
    _assign_ids(raw, "items.txt", iss)
    out = []
    for r in raw:
        core.Li.add(r["sym"], r["name"], r["plural"])
    for r in raw:
        try:
            mv = None
            if r["move"]:
                mv = res.ref(core.Lm, r["move"], "items.txt", r["line"], "UNKNOWN_MOVE", context="el objeto %s" % r["sym"])
            pk = r["pocket"] if isinstance(r["pocket"], int) else 1
            m = _TM_RE.match(r["sym"])
            tmn = int(m.group(1)) if m and r["move"] else None
            if tmn is not None and not mv:
                iss.add("items.txt", r["line"], "error", "MISSING_FIELD", "La MT %s no tiene un movimiento válido" % r["sym"])
            out.append({"id": r["id"], "sym": r["sym"], "name": r["name"], "plural": r["plural"] or r["name"], "pocket": pk,
                        "pocketName": POCKET_NAMES[pk] if 0 < pk < len(POCKET_NAMES) else "Bolsillo %s" % pk,
                        "price": r["price"], "description": r["desc"], "fieldUse": r["fieldUse"], "battleUse": r["battleUse"],
                        "special": r["special"], "move": mv, "tm": tmn if mv else None, "icon": None, "isNew": False,
                        "where": [], "shops": [], "missions": [], "heldBy": [], "berry": None,
                        "baseline": None, "diff": {"changed": False, "fields": []}, "line": r["line"]})
        except Exception:
            iss.add("items.txt", r.get("line", 0), "error", "BAD_LINE", "No se pudo construir el objeto %s" % r.get("sym"))
    out.sort(key=lambda i: i["id"])
    core.items = out
    core.item_by_sym = {i["sym"]: i for i in out}


# --------------------------------------------------------------------------------------------- Pokémon
def stats_dict(vals):
    d = {}
    for i, k in enumerate(STAT_ORDER):
        d[k] = vals[i] if i < len(vals) and vals[i] is not None else 0
    d["bst"] = sum(d[k] for k in STAT_ORDER)
    return {"hp": d["hp"], "atk": d["atk"], "def": d["def"], "spa": d["spa"], "spd": d["spd"], "spe": d["spe"], "bst": d["bst"]}


def evo_text(method, param, nm):
    """Texto en español del método de evolución. ``nm`` resuelve nombres: item(sym), move(sym), species(sym), type(sym)."""
    p = (param or "").strip()
    base = re.sub(r"Form\d$", "", method)
    form = re.search(r"Form(\d)$", method)
    suffix = " (forma %s)" % form.group(1) if form else ""
    lv = ("Nivel %s" % p) if p else "Nivel"
    T = {
        "Level": lv, "LevelDay": lv + " (de día)", "LevelNight": lv + " (de noche)", "LevelDayTime": lv + " (de día)",
        "LevelMale": lv + " (macho)", "LevelFemale": lv + " (hembra)", "LevelRain": lv + " (bajo la lluvia)",
        "LevelDarkInParty": lv + " (con un Pokémon Siniestro en el equipo)",
        "Happiness": "Amistad", "HappinessDay": "Amistad (de día)", "HappinessNight": "Amistad (de noche)",
        "Trade": "Intercambio",
        "TradeItem": "Intercambio con %s" % nm.item(p), "Item": nm.item(p), "ItemMale": "%s (macho)" % nm.item(p),
        "ItemFemale": "%s (hembra)" % nm.item(p),
        "DayHoldItem": "Con %s equipado (de día)" % nm.item(p), "NightHoldItem": "Con %s equipado (de noche)" % nm.item(p),
        "HoldItem": "Con %s equipado" % nm.item(p),
        "HasMove": "Conociendo %s" % nm.move(p), "HasInParty": "Con %s en el equipo" % nm.species(p),
        "TradeSpecies": "Intercambio por %s" % nm.species(p),
        "Beauty": "Belleza %s" % p if p else "Belleza",
        "AttackGreater": lv + " (Ataque > Defensa)", "DefenseGreater": lv + " (Defensa > Ataque)", "AtkDefEqual": lv + " (Ataque = Defensa)",
        "Silcoon": lv + " (aleatorio, rama Silcoon)", "Cascoon": lv + " (aleatorio, rama Cascoon)",
        "Ninjask": lv, "Shedinja": lv + " (con hueco libre y una Poké Ball)",
        "Location": "En %s" % (p or "un lugar concreto"),
        "HappinessMoveType": "Amistad con un movimiento de tipo %s" % nm.type(p),
        "Crits": "Con %s golpes críticos en un combate" % p if p else "Con golpes críticos en un combate",
    }
    t = T.get(base) or T.get(method)
    if t is None:
        t = (method + (" " + p if p else "")).strip()
    return t + suffix


class _Names:
    def __init__(self, core):
        self.core = core

    def item(self, s):
        it = self.core.item_by_sym.get(s)
        return it["name"] if it else (s or "un objeto")

    def move(self, s):
        m = self.core.move_by_sym.get(s)
        return m["name"] if m else (s or "un movimiento")

    def species(self, s):
        d = self.core.sym_dex.get(s)
        p = self.core.by_dex.get(d) if d else None
        return p["name"] if p else (s or "una especie")

    def type(self, s):
        t = self.core.type_by_sym.get(s)
        return t["name"] if t else (s or "un tipo")


def build_species_lookup(raw, iss, core):
    """Registra especies (símbolo y nombre) antes de resolver evoluciones."""
    seen = {}
    for r in raw:
        if r.get("outside"):
            core.Ls.ignore_add(r["sym"], r["name"])
            continue
        if r["sym"] in seen:
            iss.add("pokemon.txt", r["line"], "error", "DUPLICATE_KEY",
                    "InternalName «%s» repetido (también en la línea %d); la primera especie conserva el símbolo" % (r["sym"], seen[r["sym"]]))
            continue
        seen[r["sym"]] = r["line"]
        core.Ls.add(r["sym"], r["name"])
        core.sym_dex[r["sym"]] = r["dex"]


def build_pokemon(raw, iss, res, core, baseline=None):
    """``baseline``: dict dex -> {"types","stats"(dict)} usado solo como último recurso ante datos irrecuperables."""
    out = []
    raw = [r for r in raw if not r.get("outside")]
    nm = _Names(core)
    by_dex = {}
    # primera pasada: estructura mínima para poder nombrar especies en los textos de evolución
    for r in raw:
        by_dex[r["dex"]] = {"name": r["name"], "sym": r["sym"]}
    core.by_dex = by_dex
    for r in raw:
        try:
            f = "pokemon.txt"
            bl = (baseline or {}).get(r["dex"]) or {}
            # tipos
            types = []
            t1 = res.ref(core.Lt, r["type1"][1], f, r["type1"][0], "UNKNOWN_TYPE", context="%s" % r["sym"]) if r["type1"][1] else None
            t2 = res.ref(core.Lt, r["type2"][1], f, r["type2"][0], "UNKNOWN_TYPE", context="%s" % r["sym"]) if r["type2"][1] else None
            if not t1:
                alt = (bl.get("types") or [None])[0] or ("NORMAL" if core.Lt.syms else None)
                if r["type1"][1]:
                    iss.add(f, r["type1"][0], "warn", "UNKNOWN_TYPE", "Se usa %s provisionalmente como tipo principal de %s" % (alt, r["sym"]), suggestion=alt, applied=True)
                t1 = alt
            for t in (t1, t2):
                if t and t not in types:
                    types.append(t)
            # estadísticas
            sv = r["stats"]
            if sv is None:
                b = bl.get("stats")
                sv = [b[k] for k in STAT_ORDER] if b else [None] * 6
            else:
                sv = list(sv)
                for i in range(6):
                    if sv[i] is None:
                        b = bl.get("stats")
                        alt = b[STAT_ORDER[i]] if b else 0
                        iss.add(f, r["statsLine"], "error", "BAD_NUMBER",
                                "Valor %d de BaseStats de %s irrecuperable; se usa %s" % (i + 1, r["sym"], alt), suggestion=str(alt), applied=True)
                        sv[i] = alt
            stats = stats_dict(sv)
            # habilidades
            abil, hidden = [], []
            for ln, tok in r["abilities"]:
                a = res.ref(core.La, tok, f, ln, "UNKNOWN_ABILITY", context=r["sym"])
                if a and a not in abil:
                    abil.append(a)
            for ln, tok in r["hidden"]:
                a = res.ref(core.La, tok, f, ln, "UNKNOWN_ABILITY", context="%s (oculta)" % r["sym"])
                if a and a not in hidden and a not in abil:
                    hidden.append(a)
            # movimientos
            learn = []
            for ln, lv, tok in r["moves"]:
                m = res.ref(core.Lm, tok, f, ln, "UNKNOWN_MOVE", context="Moves de %s" % r["sym"])
                if m:
                    learn.append({"lv": lv, "move": m})
            learn.sort(key=lambda x: x["lv"])
            egg = []
            for ln, tok in r["eggMoves"]:
                m = res.ref(core.Lm, tok, f, ln, "UNKNOWN_MOVE", context="EggMoves de %s" % r["sym"])
                if m and m not in egg:
                    egg.append(m)
            # evoluciones
            evos = []
            for ln, child, method, param in r["evos"]:
                to_sym = res.ref(core.Ls, child, f, ln, "UNKNOWN_SPECIES", context="Evolutions de %s" % r["sym"])
                if not to_sym:
                    continue
                m_sym, how = pbs.EVO_LOOKUP.lookup(method)
                if m_sym is None:
                    sug = pbs.EVO_LOOKUP.suggest(method)
                    if sug is not None and sug.auto:
                        iss.add(f, ln, "error", "BAD_LINE", "Método de evolución desconocido «%s» en %s: se usa «%s»" % (method, r["sym"], sug.sym),
                                suggestion=sug.sym, applied=True)
                        m_sym = sug.sym
                    else:
                        iss.add(f, ln, "error", "BAD_LINE", "Método de evolución desconocido «%s» en %s%s" % (method, r["sym"], (". ¿Quisiste decir «%s»?" % sug.sym) if sug else ""),
                                suggestion=sug.sym if sug else None, applied=False)
                        m_sym = method or "Unknown"
                ptype = EVOPARAM_BY_NAME.get(m_sym, 0)
                p = param.strip()
                item = None
                if ptype == 2:
                    item = res.ref(core.Li, p, f, ln, "UNKNOWN_ITEM", context="evolución de %s" % r["sym"])
                    p = item or p
                elif ptype == 3:
                    mv = res.ref(core.Lm, p, f, ln, "UNKNOWN_MOVE", context="evolución de %s" % r["sym"])
                    p = mv or p
                elif ptype == 4:
                    sp = res.ref(core.Ls, p, f, ln, "UNKNOWN_SPECIES", context="evolución de %s" % r["sym"])
                    p = sp or p
                elif ptype == 5:
                    tp = res.ref(core.Lt, p, f, ln, "UNKNOWN_TYPE", context="evolución de %s" % r["sym"])
                    p = tp or p
                elif ptype == 1:
                    if p and not re.fullmatch(r"\d+", p):
                        from .fuzzy import parse_int
                        v = parse_int(iss, f, ln, "nivel de evolución de %s" % r["sym"], p, default=None)
                        p = str(v) if v is not None else p
                    elif not p:
                        iss.add(f, ln, "error", "MISSING_FIELD", "Falta el parámetro del método %s en la evolución de %s" % (m_sym, r["sym"]))
                to_dex = core.sym_dex.get(to_sym)
                evos.append({"to": to_dex, "sym": to_sym, "method": m_sym, "param": p, "text": evo_text(m_sym, p, nm), "item": item})
            wild = {}
            for key, (ln, tok) in r["wild"].items():
                if tok:
                    it = res.ref(core.Li, tok, f, ln, "UNKNOWN_ITEM", context="objeto salvaje de %s" % r["sym"])
                    wild[key] = it
                else:
                    wild[key] = None
            if hasattr(r.get("sec"), "has") and r["sec"].has("WildItem") and not any(wild.values()):
                pass
            ev = r["ev"]
            ev_d = None
            if ev:
                ev_d = {STAT_ORDER[i]: (ev[i] or 0) for i in range(min(6, len(ev)))}
            gr = r["growthRate"]
            out.append({
                "dex": r["dex"], "sym": r["sym"], "name": r["name"], "types": types, "stats": stats,
                "abilities": abil, "hiddenAbilities": hidden, "evolutions": evos, "evolvesFrom": None, "family": [r["dex"]],
                "learnset": learn, "eggMoves": egg, "tms": [], "kind": r["kind"] or None, "height": r["height"], "weight": r["weight"],
                "color": r["color"] or None, "habitat": r["habitat"] or None, "pokedex": r["pokedex"] or None, "role": None, "notes": [],
                "obtain": [], "wild": [], "baseline": None, "diff": None,
                "eggGroups": r["compat"], "catchRate": r["catchRate"], "baseHappiness": r["baseHappiness"], "baseExp": r["baseExp"],
                "evYield": ev_d, "genderRate": r["genderRate"] or None, "growthRate": gr or None, "stepsToHatch": r["stepsToHatch"],
                "wildItems": wild, "line": r["line"],
            })
        except Exception as e:
            iss.add("pokemon.txt", r.get("line", 0), "error", "BAD_LINE", "No se pudo construir la especie %s (%s); se conserva con datos mínimos" % (r.get("sym"), e.__class__.__name__))
            out.append({"dex": r["dex"], "sym": r["sym"], "name": r["name"], "types": ["NORMAL"], "stats": stats_dict([0] * 6),
                        "abilities": [], "hiddenAbilities": [], "evolutions": [], "evolvesFrom": None, "family": [r["dex"]],
                        "learnset": [], "eggMoves": [], "tms": [], "kind": None, "height": None, "weight": None, "color": None,
                        "habitat": None, "pokedex": None, "role": None, "notes": [], "obtain": [], "wild": [], "baseline": None,
                        "diff": None, "line": r["line"], "wildItems": {}})
    out.sort(key=lambda p: p["dex"])
    # una entrada por número (el último gana ya se resolvió en el parser)
    uniq = {}
    for p in out:
        uniq[p["dex"]] = p
    out = [uniq[k] for k in sorted(uniq)]
    core.pokemon = out
    core.by_dex = {p["dex"]: p for p in out}
    # relaciones evolutivas
    for p in out:
        for e in p["evolutions"]:
            child = core.by_dex.get(e["to"])
            if child is not None and child["evolvesFrom"] is None and e["to"] != p["dex"]:
                child["evolvesFrom"] = {"from": p["dex"], "method": e["method"], "param": e["param"], "text": e["text"], "item": e["item"]}
    for p in out:
        p["family"] = _family(p["dex"], core.by_dex)


def _family(dex, by_dex):
    root, seen = dex, set()
    while True:
        p = by_dex.get(root)
        if p is None or p["evolvesFrom"] is None or root in seen:
            break
        seen.add(root)
        root = p["evolvesFrom"]["from"]
    order, queue, vis = [], [(root, 0)], set()
    depth = {}
    while queue:
        d, lv = queue.pop(0)
        if d in vis or d not in by_dex:
            continue
        vis.add(d)
        depth[d] = lv
        order.append(d)
        for e in by_dex[d]["evolutions"]:
            if e["to"] and e["to"] not in vis:
                queue.append((e["to"], lv + 1))
    order.sort(key=lambda x: (depth.get(x, 9), x))
    return order or [dex]


# -------------------------------------------------------------------------------------------------- MT
def build_tm(raw, iss, res, core):
    sections = {}
    for r in raw:
        mv = res.ref(core.Lm, r["move"], "tm.txt", r["line"], "UNKNOWN_MOVE", context="sección de tm.txt")
        if not mv:
            continue
        dexes = []
        for ln, tok in r["species"]:
            sp = res.ref(core.Ls, tok, "tm.txt", ln, "UNKNOWN_SPECIES", context="[%s]" % mv)
            if sp:
                d = core.sym_dex.get(sp)
                if d and d not in dexes:
                    dexes.append(d)
        if mv in sections:
            iss.add("tm.txt", r["line"], "error", "DUPLICATE_KEY", "Sección [%s] duplicada (primera en la línea %d): se fusionan las especies" % (mv, sections[mv]["line"]))
            for d in dexes:
                if d not in sections[mv]["dex"]:
                    sections[mv]["dex"].append(d)
        else:
            sections[mv] = {"move": mv, "line": r["line"], "dex": dexes}
    for s in sections.values():
        s["dex"].sort()
    core.tm_sections = list(sections.values())


def build_berries(raw, iss, res, core):
    out = []
    seen = set()
    for r in raw:
        it = res.ref(core.Li, r["item"], "berryplants.txt", r["line"], "UNKNOWN_ITEM", context="berryplants.txt")
        if not it:
            continue
        if it in seen:
            iss.add("berryplants.txt", r["line"], "error", "DUPLICATE_KEY", "Planta de baya %s repetida" % it)
            continue
        seen.add(it)
        v = r["values"]
        out.append({"item": it, "hoursPerStage": v[0], "dryingPerHour": v[1], "minYield": v[2], "maxYield": v[3]})
    core.berries = out


def build_core(files, iss, baseline=None):
    """``files``: dict nombre -> TextFile. ``baseline``: {"pokemon": {dex:{types,stats}}, "moves": {sym:{type,category}}}."""
    core = Core()
    res = Resolver(iss)

    def stage(name, fn, *a):
        try:
            fn(*a)
        except Exception as e:  # pragma: no cover
            iss.add(name, 0, "error", "INTERNAL", "Error interno procesando %s (%s: %s); se continúa con lo disponible" % (name, e.__class__.__name__, e))

    def get(name):
        return files.get(name)

    tf = get("types.txt")
    raw_types = pbs.parse_types(tf, iss) if tf and tf.ok else []
    stage("types.txt", build_types, raw_types, iss, res, core)
    tf = get("abilities.txt")
    raw_ab = pbs.parse_abilities(tf, iss) if tf and tf.ok else []
    stage("abilities.txt", build_abilities, raw_ab, iss, res, core)
    tf = get("moves.txt")
    raw_mv = pbs.parse_moves(tf, iss) if tf and tf.ok else []
    stage("moves.txt", build_moves, raw_mv, iss, res, core, (baseline or {}).get("moves"))
    tf = get("items.txt")
    raw_it = pbs.parse_items(tf, iss) if tf and tf.ok else []
    stage("items.txt", build_items, raw_it, iss, res, core)
    tf = get("pokemon.txt")
    raw_pk = pbs.parse_pokemon(tf, iss) if tf and tf.ok else []
    stage("pokemon.txt", build_species_lookup, raw_pk, iss, core)
    stage("pokemon.txt", build_pokemon, raw_pk, iss, res, core, (baseline or {}).get("pokemon"))
    tf = get("tm.txt")
    raw_tm = pbs.parse_tm(tf, iss) if tf and tf.ok else []
    stage("tm.txt", build_tm, raw_tm, iss, res, core)
    tf = get("berryplants.txt")
    raw_b = pbs.parse_berryplants(tf, iss) if tf and tf.ok else []
    stage("berryplants.txt", build_berries, raw_b, iss, res, core)
    return core
