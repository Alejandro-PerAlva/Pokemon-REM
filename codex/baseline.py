"""Valores «vanilla» (baseline) para comparar con el PBS vivo y cálculo de los ``diff`` en vivo.

Fuente preferente: ``PBS/rem_vanilla_baseline.txt``. Si no existe o está vacío, se usa como alternativa el PBS
original (``PBS_backup_original/``) construido con el mismo código que el modelo vivo.
"""
import re

from .fuzzy import parse_int
from .ini import parse_ini, split_list
from .pbs import STAT_ORDER

BADGE_ORDER = ["Retipado", "Stats", "Habilidades", "Evolución", "Learnset"]
MOVE_FIELDS = ["name", "type", "category", "power", "accuracy", "pp", "priority", "fcode", "effectChance", "target", "flags", "description"]
ITEM_FIELDS = ["name", "pocket", "price", "description", "fieldUse", "battleUse", "special", "move"]


class Baseline:
    def __init__(self, source=None):
        self.source = source
        self.pokemon = {}      # dex -> dict
        self.moves = {}        # sym -> dict
        self.abilities = {}    # sym -> {"name","description"}
        self.items = {}        # sym -> dict
        self.tm = {}           # move sym -> [species syms]
        self.tm_counts = {}    # move sym -> nº de especies que aprendían la MT original
        self.has_items = False
        self.has_moves = False
        self.has_abilities = False

    def __bool__(self):
        return bool(self.pokemon or self.moves or self.abilities or self.items)


def from_core(core, source):
    """Baseline a partir de un ``Core`` construido sobre un PBS (p. ej. el original)."""
    b = Baseline(source)
    for p in core.pokemon:
        b.pokemon[p["dex"]] = {
            "name": p["name"], "sym": p["sym"], "types": list(p["types"]), "stats": dict(p["stats"]),
            "abilities": list(p["abilities"]), "hidden": list(p["hiddenAbilities"]),
            "evos": [(e["sym"], e["method"], e["param"]) for e in p["evolutions"]],
            "moves": [(m["lv"], m["move"]) for m in p["learnset"]], "eggMoves": list(p["eggMoves"]),
            "wild": dict(p.get("wildItems") or {})}
    for m in core.moves:
        b.moves[m["sym"]] = {k: m.get(k) for k in MOVE_FIELDS}
    for a in core.abilities:
        b.abilities[a["sym"]] = {"name": a["name"], "description": a["description"]}
    for i in core.items:
        b.items[i["sym"]] = {k: i.get(k) for k in ITEM_FIELDS}
    syms = {p["dex"]: p["sym"] for p in core.pokemon}
    for s in core.tm_sections:
        b.tm[s["move"]] = [syms[d] for d in s["dex"] if d in syms]
        b.tm_counts[s["move"]] = len(s["dex"])
    b.has_items, b.has_moves, b.has_abilities = bool(b.items), bool(b.moves), bool(b.abilities)
    return b


# ------------------------------------------------------------------------------- rem_vanilla_baseline.txt
def _nums(iss, f, line, label, text, n=None):
    vals = []
    for i, t in enumerate((text or "").split(",")):
        t = t.strip()
        vals.append(parse_int(iss, f, line, "%s (posición %d)" % (label, i + 1), t, default=0) if t else 0)
    if n:
        vals = (vals + [0] * n)[:n]
    return vals


def parse_baseline_file(tf, iss):
    f = "rem_vanilla_baseline.txt"
    b = Baseline("rem_vanilla_baseline.txt")
    from .world import BL_KNOWN

    def known(sec):
        return BL_KNOWN.get(sec.ukey.split("_", 1)[0]) if re.match(r"^(POKEMON|MOVE|ITEM|ABILITY)_", sec.ukey) else None

    secs = parse_ini(tf, iss, f, known=known)
    for s in secs:
        try:
            k = s.ukey
            m = re.match(r"^POKEMON_(\d+)$", k)
            if m:
                dex = int(m.group(1))
                st = _nums(iss, f, s.line_of("BaseStats"), "BaseStats de %s" % k, s.first("BaseStats"), 6)
                evos = []
                toks = [t.strip() for t in s.first("Evolutions").split(",")]
                if s.first("Evolutions"):
                    for i in range(0, len(toks) - 2, 3):
                        evos.append((toks[i], toks[i + 1], toks[i + 2]))
                mv = []
                mt = [t.strip() for t in s.first("Moves").split(",")] if s.first("Moves") else []
                for i in range(0, len(mt) - 1, 2):
                    lv = parse_int(iss, f, s.line_of("Moves"), "nivel en Moves de %s" % k, mt[i], default=None)
                    if lv is not None:
                        mv.append((lv, mt[i + 1]))
                stats = {STAT_ORDER[i]: st[i] for i in range(6)}
                stats["bst"] = sum(st)
                stats = {"hp": stats["hp"], "atk": stats["atk"], "def": stats["def"], "spa": stats["spa"], "spd": stats["spd"],
                         "spe": stats["spe"], "bst": stats["bst"]}
                b.pokemon[dex] = {
                    "name": s.first("Name") or None, "sym": s.first("InternalName") or None,
                    "types": list(dict.fromkeys(t.strip() for t in s.first("Types").split(",") if t.strip())),
                    "stats": stats,
                    "abilities": [t.strip() for t in s.first("Abilities").split(",") if t.strip()],
                    "hidden": [t.strip() for t in s.first("HiddenAbility").split(",") if t.strip()],
                    "evos": evos, "moves": mv,
                    "eggMoves": [t.strip() for t in s.first("EggMoves").split(",") if t.strip()],
                    "wild": {"common": s.first("WildItemCommon") or None, "uncommon": s.first("WildItemUncommon") or None,
                             "rare": s.first("WildItemRare") or None}}
                continue
            m = re.match(r"^MOVE_(.+)$", k)
            if m:
                sym = m.group(1)
                d = {"id": parse_int(iss, f, s.line_of("ID"), "ID de %s" % k, s.first("ID"), default=None), "name": s.first("Name") or sym,
                     "type": s.first("Type").upper() or None, "category": s.first("Category") or None,
                     "power": parse_int(iss, f, s.line_of("Power"), "Power de %s" % k, s.first("Power"), default=0),
                     "accuracy": parse_int(iss, f, s.line_of("Accuracy"), "Accuracy de %s" % k, s.first("Accuracy"), default=0),
                     "pp": parse_int(iss, f, s.line_of("PP"), "PP de %s" % k, s.first("PP"), default=0),
                     "priority": parse_int(iss, f, s.line_of("Priority"), "Priority de %s" % k, s.first("Priority"), default=0, allow_negative=True),
                     "fcode": (s.first("FunctionCode") or "").upper() or None,
                     "effectChance": parse_int(iss, f, s.line_of("AddlEffect"), "AddlEffect de %s" % k, s.first("AddlEffect"), default=0),
                     "target": s.first("Target") or None, "flags": s.first("Flags"), "description": s.first("Description")}
                b.moves[sym] = d
                continue
            m = re.match(r"^ABILITY_(.+)$", k)
            if m:
                b.abilities[m.group(1)] = {"id": parse_int(iss, f, s.line_of("ID"), "ID de %s" % k, s.first("ID"), default=None),
                                           "name": s.first("Name") or m.group(1), "description": s.first("Description")}
                continue
            m = re.match(r"^ITEM_(.+)$", k)
            if m:
                sym = m.group(1)
                ln = s.line
                b.items[sym] = {"id": parse_int(iss, f, ln, "ID de %s" % k, s.first("ID"), default=None), "plural": s.first("Plural") or None,
                                "name": s.first("Name") or sym,
                                "pocket": parse_int(iss, f, ln, "Pocket de %s" % k, s.first("Pocket"), default=None),
                                "price": parse_int(iss, f, ln, "Price de %s" % k, s.first("Price"), default=None),
                                "description": s.first("Description"),
                                "fieldUse": parse_int(iss, f, ln, "FieldUse de %s" % k, s.first("FieldUse"), default=None),
                                "battleUse": parse_int(iss, f, ln, "BattleUse de %s" % k, s.first("BattleUse"), default=None),
                                "special": parse_int(iss, f, ln, "Special de %s" % k, s.first("Special"), default=None),
                                "move": s.first("Move") or None}
                continue
            if k == "TM_VANILLA_COUNTS":
                for it in s.items:
                    n = parse_int(iss, f, it.line, "recuento de %s" % it.raw_key, it.value, default=None)
                    if n is not None:
                        b.tm_counts[it.raw_key.strip().upper()] = n
                continue
            if k == "TM_VANILLA":
                for it in s.items:
                    b.tm[it.raw_key.strip().upper()] = [x.strip() for x in it.value.split(",") if x.strip()]
                continue
            iss.add(f, s.line, "info", "UNKNOWN_KEY", "Sección de baseline desconocida [%s]; se ignora" % s.key)
        except Exception:
            iss.add(f, getattr(s, "line", 0), "warn", "BAD_LINE", "No se pudo interpretar la sección de baseline [%s]" % getattr(s, "key", "?"))
    b.has_items, b.has_moves, b.has_abilities = bool(b.items), bool(b.moves), bool(b.abilities)
    return b


# --------------------------------------------------------------------------------------------- diffs
def _evo_sig(evs):
    return sorted((str(s or ""), str(m or ""), str(p or "")) for s, m, p in evs)


def pokemon_baseline_view(bp, evo_text_fn, sym_dex):
    """Convierte un baseline crudo en el objeto ``baseline`` del contrato."""
    evos = []
    for child, method, param in bp["evos"]:
        evos.append({"to": sym_dex.get(child), "sym": child, "method": method, "param": param,
                     "text": evo_text_fn(method, param), "item": None})
    return {"name": bp.get("name"), "types": list(bp["types"]), "stats": dict(bp["stats"]), "abilities": list(bp["abilities"]),
            "hiddenAbility": (bp["hidden"][0] if bp["hidden"] else None), "hiddenAbilities": list(bp["hidden"]),
            "evolutions": evos, "moves": [{"lv": lv, "move": mv} for lv, mv in bp["moves"]], "eggMoves": list(bp["eggMoves"]),
            "wildItems": dict(bp.get("wild") or {})}


def diff_pokemon(p, bp):
    """``p``: especie del modelo vivo. ``bp``: baseline crudo (o None). Devuelve el objeto ``diff``."""
    zero = {k: 0 for k in ("hp", "atk", "def", "spa", "spd", "spe", "bst")}
    if bp is None:
        return {"changed": False, "types": None, "stats": zero, "abilities": {"added": [], "removed": []}, "evolutions": False,
                "movesAdded": [], "movesRemoved": [], "badges": [], "hasBaseline": False}
    badges = []
    types = None
    if sorted(p["types"]) != sorted(bp["types"]):
        types = {"before": list(bp["types"]), "after": list(p["types"])}
        badges.append("Retipado")
    sd = {k: (p["stats"].get(k, 0) - bp["stats"].get(k, 0)) for k in zero}
    if any(sd[k] for k in ("hp", "atk", "def", "spa", "spd", "spe")):
        badges.append("Stats")
    live_ab = list(p["abilities"]) + [a for a in p["hiddenAbilities"] if a not in p["abilities"]]
    base_ab = list(bp["abilities"]) + [a for a in bp["hidden"] if a not in bp["abilities"]]
    added = [a for a in live_ab if a not in base_ab]
    removed = [a for a in base_ab if a not in live_ab]
    if added or removed:
        badges.append("Habilidades")
    evo_changed = _evo_sig((e["sym"], e["method"], e["param"]) for e in p["evolutions"]) != _evo_sig(bp["evos"])
    if evo_changed:
        badges.append("Evolución")
    live_moves = [(m["lv"], m["move"]) for m in p["learnset"]]
    live_set = {m for _, m in live_moves}
    base_set = {m for _, m in bp["moves"]}
    moves_added = sorted(live_set - base_set)
    moves_removed = sorted(base_set - live_set)
    ls_changed = sorted(live_moves) != sorted(bp["moves"])
    if ls_changed:
        badges.append("Learnset")
    badges = [b for b in BADGE_ORDER if b in badges]
    return {"changed": bool(badges), "types": types, "stats": sd, "abilities": {"added": added, "removed": removed},
            "evolutions": evo_changed, "movesAdded": moves_added, "movesRemoved": moves_removed, "badges": badges,
            "learnsetChanged": ls_changed, "eggMovesChanged": sorted(p["eggMoves"]) != sorted(bp["eggMoves"]), "hasBaseline": True}


def diff_fields(live, base, fields):
    out = []
    for f in fields:
        a, b = live.get(f), base.get(f)
        if f in ("pocket", "price", "fieldUse", "battleUse", "special", "power", "accuracy", "pp", "priority", "effectChance"):
            a = a if a is not None else 0
            b = b if b is not None else 0
        else:
            a = a if a not in (None, "") else ""
            b = b if b not in (None, "") else ""
        if a != b:
            out.append(f)
    return out
