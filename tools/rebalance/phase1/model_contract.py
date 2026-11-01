#!/usr/bin/env python3
"""Validador del contrato del modelo JSON del Codex (tools/codex/SPEC.md §4.1).

    from model_contract import validate_model
    problems = validate_model(model)          # lista de str; vacía = el modelo cumple el contrato

CLI:
    python3 model_contract.py http://127.0.0.1:8765/api/model      # o un archivo .json
    python3 model_contract.py modelo.json --final                  # además exige los recuentos del juego final

Comprueba tipos, claves obligatorias, unicidad, referencias cruzadas resueltas (especies, movimientos, objetos,
habilidades, ubicaciones, tiendas, misiones, personajes, capítulos, pasos, MT) y que ``meta.counts`` coincide
con las listas. Solo biblioteca estándar. No lanza excepciones por datos malformados: los reporta.
"""
import datetime
import json
import os
import re
import sys

ROSTER_MAX = 721
SEVERITIES = {"error", "warn", "info"}
CATEGORIES = {"Physical", "Special", "Status"}
KINDS_WILD = {"Land", "Cave", "Surf", "Fish"}
KINDS_ENC = {"Land", "Cave", "Surf"}
RARITIES = {"COMMON", "UNCOMMON", "RARE"}
OBTAIN = {"WILD", "FISHING", "STARTER", "FOSSIL", "EVENT", "LEGENDARY", "EVOLUTION_LEVEL", "EVOLUTION_ITEM", "EVOLUTION_STONE", "THIRD_STAGE"}
BADGES = {"Retipado", "Stats", "Habilidades", "Evolución", "Learnset"}
STATUSES = {"Reworked", "Buffed", "Kept", "Untouched"}
ACTS = {"I", "II", "III", "IV", "V"}
COUNT_KEYS = ["pokemon", "moves", "abilities", "items", "tms", "locations", "wildSlots", "fishSlots", "characters", "chapters", "steps", "shops", "missions"]
TOP_LIST_KEYS = ["types", "pokemon", "moves", "abilities", "items", "tms", "locations", "shops", "missions", "progression", "characters",
                 "story", "ledger", "warnings", "files"]
FINAL_EXPECT = {"pokemon": 721, "items": 414, "tms": 100, "locations": 64, "wildSlots": 408, "fishSlots": 32, "chapters": 68, "steps": 68, "missions": 29}


class _P:
    """Acumula problemas agrupados por tipo (para no inundar la salida)."""

    def __init__(self):
        self.d = {}
        self.order = []

    def add(self, kind, msg):
        if kind not in self.d:
            self.d[kind] = [0, []]
            self.order.append(kind)
        e = self.d[kind]
        e[0] += 1
        if len(e[1]) < 3:
            e[1].append(msg)

    def out(self):
        res = []
        for k in self.order:
            n, msgs = self.d[k]
            for m in msgs:
                res.append(m)
            if n > len(msgs):
                res.append("   … y %d problema(s) más del tipo «%s»" % (n - len(msgs), k))
        return res


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_str(v):
    return isinstance(v, str)


def _range_ok(v):
    return v is None or (isinstance(v, list) and len(v) == 2 and all(_is_int(x) for x in v) and v[0] <= v[1])


def _canonical_keys():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", "..", ".."))
    for p in (os.path.join(root, "tools", "codex", "location_keys.json"), os.path.join(root, "codex", "location_keys.json")):
        try:
            with open(p, encoding="utf-8") as f:
                return {c["key"] for c in json.load(f)}
        except Exception:
            continue
    return None


def validate_model(model, final=False):
    """Devuelve la lista de problemas (str). ``final=True`` exige además los recuentos del juego terminado."""
    P = _P()
    try:
        _validate(model, P, final)
    except Exception as e:  # el validador no debe fallar nunca
        P.add("interno", "ERROR INTERNO DEL VALIDADOR: %s: %s" % (e.__class__.__name__, e))
    return P.out()


def _need(P, obj, path, keys, kind="faltan claves"):
    ok = True
    if not isinstance(obj, dict):
        P.add("tipo:" + path, "%s: se esperaba un objeto (dict) y es %s" % (path, type(obj).__name__))
        return False
    for k in keys:
        if k not in obj:
            P.add("falta:%s.%s" % (re.sub(r"\[\d+\]", "[]", path), k), "%s: falta la clave obligatoria «%s»" % (path, k))
            ok = False
    return ok


def _t(P, cond, path, field, msg):
    if not cond:
        P.add("campo:%s.%s" % (re.sub(r"\[\d+\]", "[]", path), field), "%s.%s: %s" % (path, field, msg))
    return cond


def _validate(m, P, final):
    if not isinstance(m, dict):
        P.add("raiz", "El modelo no es un objeto JSON")
        return
    if not _need(P, m, "model", ["meta"] + TOP_LIST_KEYS + ["prelude", "assets"]):
        pass
    for k in TOP_LIST_KEYS:
        if k in m and not isinstance(m[k], list):
            P.add("lista:" + k, "model.%s debe ser una lista" % k)
    meta = m.get("meta", {})
    counts = {}
    if _need(P, meta, "meta", ["source", "generatedAt", "version", "health", "counts"]):
        _t(P, meta["source"] in ("live", "bundle"), "meta", "source", "debe ser 'live' o 'bundle' (es %r)" % (meta["source"],))
        try:
            datetime.datetime.fromisoformat(str(meta["generatedAt"]).replace("Z", "+00:00"))
        except Exception:
            P.add("fecha", "meta.generatedAt no es ISO-8601: %r" % (meta["generatedAt"],))
        _t(P, _is_str(meta["version"]) and meta["version"], "meta", "version", "debe ser un texto no vacío")
        h = meta["health"]
        if _need(P, h, "meta.health", ["status", "errors", "warnings"]):
            _t(P, h["status"] in ("ok", "warn", "error"), "meta.health", "status", "debe ser ok|warn|error")
            _t(P, _is_int(h["errors"]) and _is_int(h["warnings"]), "meta.health", "errors/warnings", "deben ser enteros")
        counts = meta["counts"]
        if _need(P, counts, "meta.counts", COUNT_KEYS):
            for k in COUNT_KEYS:
                _t(P, _is_int(counts[k]) and counts[k] >= 0, "meta.counts", k, "debe ser un entero >= 0 (es %r)" % (counts[k],))
    lists = {k: (m.get(k) if isinstance(m.get(k), list) else []) for k in TOP_LIST_KEYS}

    # ------------------------------------------------------------------ tipos
    types = {}
    for i, t in enumerate(lists["types"]):
        p = "types[%d]" % i
        if _need(P, t, p, ["sym", "name", "index"]):
            _t(P, _is_str(t["sym"]) and t["sym"], p, "sym", "texto no vacío")
            _t(P, _is_str(t["name"]) and t["name"], p, "name", "texto no vacío")
            _t(P, _is_int(t["index"]) and t["index"] >= 0, p, "index", "entero >= 0")
            if t["sym"] in types:
                P.add("dup:types", "types: símbolo repetido %s" % t["sym"])
            types[t["sym"]] = t
    if len({t.get("index") for t in lists["types"] if isinstance(t, dict)}) != len([t for t in lists["types"] if isinstance(t, dict)]):
        P.add("dup:types.index", "types: hay índices repetidos")

    # ----------------------------------------------------- conjuntos de claves
    def keyset(lst, key):
        return {e.get(key) for e in lst if isinstance(e, dict) and e.get(key) is not None}

    dexes = keyset(lists["pokemon"], "dex")
    move_syms = keyset(lists["moves"], "sym")
    abil_syms = keyset(lists["abilities"], "sym")
    item_syms = keyset(lists["items"], "sym")
    loc_keys = keyset(lists["locations"], "key")
    shop_keys = keyset(lists["shops"], "key")
    char_keys = keyset(lists["characters"], "key")
    story_keys = keyset(lists["story"], "key")
    step_nums = keyset(lists["progression"], "step")
    mission_ns = keyset(lists["missions"], "n")
    tm_nums = keyset(lists["tms"], "number")
    tm_syms = keyset(lists["tms"], "sym")
    pk_by_dex = {p["dex"]: p for p in lists["pokemon"] if isinstance(p, dict) and _is_int(p.get("dex"))}
    mv_by_sym = {x["sym"]: x for x in lists["moves"] if isinstance(x, dict) and _is_str(x.get("sym"))}
    it_by_sym = {x["sym"]: x for x in lists["items"] if isinstance(x, dict) and _is_str(x.get("sym"))}

    def ref(kind, value, valid, where, allow_none=False):
        if value is None and allow_none:
            return True
        if value not in valid:
            P.add("ref:%s" % kind, "%s: referencia %s inexistente %r" % (where, kind, value))
            return False
        return True

    def uniq(lst, key, kind):
        seen = set()
        for e in lst:
            if isinstance(e, dict) and key in e:
                if e[key] in seen:
                    P.add("dup:%s" % kind, "%s: %s repetido %r" % (kind, key, e[key]))
                seen.add(e[key])

    for lstname, key in (("pokemon", "dex"), ("moves", "sym"), ("moves", "id"), ("abilities", "sym"), ("abilities", "id"), ("items", "sym"),
                         ("items", "id"), ("locations", "key"), ("shops", "key"), ("characters", "key"), ("story", "key"),
                         ("progression", "step"), ("missions", "n"), ("tms", "number"), ("tms", "sym")):
        uniq(lists[lstname], key, "%s.%s" % (lstname, key))

    def evo_ok(e, p, owner):
        if not _need(P, e, p, ["to", "method", "param", "text", "item"]):
            return
        ref("especie", e["to"], dexes, p + ".to")
        _t(P, _is_str(e["method"]) and e["method"], p, "method", "texto no vacío")
        _t(P, _is_str(e["param"]), p, "param", "debe ser texto")
        _t(P, _is_str(e["text"]) and e["text"], p, "text", "texto no vacío")
        ref("objeto", e["item"], item_syms, p + ".item", allow_none=True)

    stat_keys = ["hp", "atk", "def", "spa", "spd", "spe", "bst"]

    def stats_ok(s, p):
        if _need(P, s, p, stat_keys):
            for k in stat_keys:
                _t(P, _is_int(s[k]), p, k, "entero (es %r)" % (s[k],))
            if all(_is_int(s[k]) for k in stat_keys):
                _t(P, s["bst"] == sum(s[k] for k in stat_keys if k != "bst"), p, "bst", "no coincide con la suma de las 6 estadísticas")

    # ---------------------------------------------------------------- Pokémon
    learn_total = 0
    for i, pk in enumerate(lists["pokemon"]):
        p = "pokemon[%d]" % i
        if not _need(P, pk, p, ["dex", "sym", "name", "types", "stats", "abilities", "evolutions", "evolvesFrom", "family", "learnset",
                                "tms", "kind", "height", "weight", "color", "habitat", "pokedex", "role", "obtain", "wild", "baseline", "diff"]):
            continue
        label = "pokemon #%s" % pk.get("dex")
        _t(P, _is_int(pk["dex"]) and 1 <= pk["dex"] <= ROSTER_MAX, p, "dex", "fuera del plantel #001-#721 (%r)" % (pk["dex"],))
        _t(P, _is_str(pk["sym"]) and pk["sym"], p, "sym", "texto no vacío")
        _t(P, _is_str(pk["name"]) and pk["name"], p, "name", "texto no vacío")
        tl = pk["types"]
        if _t(P, isinstance(tl, list) and 1 <= len(tl) <= 2, p, "types", "lista de 1 o 2 tipos"):
            for t in tl:
                ref("tipo", t, types, p + ".types")
        stats_ok(pk["stats"], p + ".stats")
        al = pk["abilities"]
        if _t(P, isinstance(al, list), p, "abilities", "debe ser lista"):
            _t(P, len(al) >= 1, p, "abilities", "sin habilidades (%s)" % label)
            for a in al:
                ref("habilidad", a, abil_syms, p + ".abilities")
        if isinstance(pk["evolutions"], list):
            for j, e in enumerate(pk["evolutions"]):
                evo_ok(e, "%s.evolutions[%d]" % (p, j), pk)
        else:
            P.add("tipo:evolutions", "%s.evolutions debe ser lista" % p)
        ef = pk["evolvesFrom"]
        if ef is not None:
            if _need(P, ef, p + ".evolvesFrom", ["from", "method", "param", "text", "item"]):
                if ref("especie", ef["from"], dexes, p + ".evolvesFrom.from"):
                    par = pk_by_dex.get(ef["from"])
                    if par and not any(isinstance(e, dict) and e.get("to") == pk["dex"] for e in par.get("evolutions", [])):
                        P.add("evolvesFrom", "%s: evolvesFrom=%s pero esa especie no evoluciona a #%s" % (p, ef["from"], pk["dex"]))
        fam = pk["family"]
        if _t(P, isinstance(fam, list) and fam, p, "family", "lista no vacía"):
            _t(P, pk["dex"] in fam, p, "family", "no contiene la propia especie")
            for d in fam:
                if ref("especie", d, dexes, p + ".family"):
                    other = pk_by_dex[d].get("family")
                    if other is not None and sorted(other) != sorted(fam):
                        P.add("family", "%s: la familia %s no coincide con la de #%s (%s)" % (p, fam, d, other))
        if isinstance(pk["learnset"], list):
            for j, l in enumerate(pk["learnset"]):
                q = "%s.learnset[%d]" % (p, j)
                if _need(P, l, q, ["lv", "move"]):
                    _t(P, _is_int(l["lv"]) and l["lv"] >= 0, q, "lv", "entero >= 0")
                    ref("movimiento", l["move"], move_syms, q + ".move")
                    learn_total += 1
        else:
            P.add("tipo:learnset", "%s.learnset debe ser lista" % p)
        if isinstance(pk["tms"], list):
            for n in pk["tms"]:
                ref("MT", n, tm_nums, p + ".tms")
        else:
            P.add("tipo:tms", "%s.tms debe ser lista" % p)
        for k in ("kind", "color", "habitat", "pokedex", "role"):
            _t(P, pk[k] is None or _is_str(pk[k]), p, k, "texto o null")
        for k in ("height", "weight"):
            _t(P, pk[k] is None or _is_num(pk[k]), p, k, "número o null")
        if isinstance(pk["obtain"], list):
            for j, o in enumerate(pk["obtain"]):
                q = "%s.obtain[%d]" % (p, j)
                if _need(P, o, q, ["method", "loc", "level", "detail"]):
                    _t(P, o["method"] in OBTAIN, q, "method", "método desconocido %r" % (o["method"],))
                    ref("ubicación", o["loc"], loc_keys, q + ".loc", allow_none=True)
                    _t(P, _is_str(o["level"]) and _is_str(o["detail"]), q, "level/detail", "deben ser texto")
        else:
            P.add("tipo:obtain", "%s.obtain debe ser lista" % p)
        if isinstance(pk["wild"], list):
            for j, w in enumerate(pk["wild"]):
                q = "%s.wild[%d]" % (p, j)
                if _need(P, w, q, ["loc", "zone", "kind", "rarity", "pct", "day", "night", "note"]):
                    ref("ubicación", w["loc"], loc_keys, q + ".loc")
                    _t(P, w["zone"] is None or _is_str(w["zone"]), q, "zone", "texto o null")
                    _t(P, w["kind"] in KINDS_WILD, q, "kind", "debe ser Land|Cave|Surf|Fish (es %r)" % (w["kind"],))
                    _t(P, w["rarity"] in RARITIES, q, "rarity", "debe ser COMMON|UNCOMMON|RARE (es %r)" % (w["rarity"],))
                    _t(P, _is_int(w["pct"]), q, "pct", "entero")
                    _t(P, _range_ok(w["day"]) and _range_ok(w["night"]), q, "day/night", "deben ser [min,max] o null")
        else:
            P.add("tipo:wild", "%s.wild debe ser lista" % p)
        bl = pk["baseline"]
        if bl is not None and _need(P, bl, p + ".baseline", ["types", "stats", "abilities", "hiddenAbility", "evolutions", "moves"]):
            stats_ok(bl["stats"], p + ".baseline.stats")
            _t(P, isinstance(bl["types"], list) and 1 <= len(bl["types"]) <= 2, p + ".baseline", "types", "lista de 1-2 tipos")
            _t(P, isinstance(bl["moves"], list), p + ".baseline", "moves", "lista")
        d = pk["diff"]
        if _need(P, d, p + ".diff", ["changed", "types", "stats", "abilities", "evolutions", "movesAdded", "movesRemoved", "badges"]):
            _t(P, isinstance(d["changed"], bool), p + ".diff", "changed", "booleano")
            if d["types"] is not None:
                _need(P, d["types"], p + ".diff.types", ["before", "after"])
            if _need(P, d["stats"], p + ".diff.stats", stat_keys):
                pass
            _need(P, d["abilities"], p + ".diff.abilities", ["added", "removed"])
            _t(P, isinstance(d["evolutions"], bool), p + ".diff", "evolutions", "booleano")
            _t(P, isinstance(d["badges"], list) and all(b in BADGES for b in d["badges"]), p + ".diff", "badges", "valores permitidos: %s" % sorted(BADGES))
            if isinstance(d["badges"], list):
                _t(P, d["changed"] == bool(d["badges"]) or d.get("new"), p + ".diff", "changed", "inconsistente con badges")

    # -------------------------------------------------------------- movimientos
    for i, mv in enumerate(lists["moves"]):
        p = "moves[%d]" % i
        if not _need(P, mv, p, ["id", "sym", "name", "type", "category", "power", "accuracy", "pp", "priority", "fcode", "effectChance",
                                "target", "flags", "description", "tm", "learnedBy", "tmLearners", "baseline", "diff"]):
            continue
        _t(P, _is_int(mv["id"]), p, "id", "entero")
        _t(P, _is_str(mv["sym"]) and mv["sym"] and _is_str(mv["name"]) and mv["name"], p, "sym/name", "texto no vacío")
        ref("tipo", mv["type"], types, p + ".type")
        _t(P, mv["category"] in CATEGORIES, p, "category", "debe ser Physical|Special|Status (es %r)" % (mv["category"],))
        for k in ("power", "accuracy", "pp", "priority", "effectChance"):
            _t(P, _is_int(mv[k]), p, k, "entero (es %r)" % (mv[k],))
        for k in ("fcode", "target", "flags", "description"):
            _t(P, _is_str(mv[k]), p, k, "texto")
        if mv["category"] == "Status" and _is_int(mv["power"]):
            _t(P, mv["power"] == 0, p, "power", "un movimiento de Estado debe tener potencia 0")
        if mv["tm"] is not None:
            ref("MT", mv["tm"], tm_nums, p + ".tm")
        if isinstance(mv["learnedBy"], list):
            for l in mv["learnedBy"]:
                if _need(P, l, p + ".learnedBy[]", ["dex", "lv"]):
                    if ref("especie", l["dex"], dexes, p + ".learnedBy.dex"):
                        pk = pk_by_dex[l["dex"]]
                        if not any(isinstance(x, dict) and x.get("move") == mv["sym"] and x.get("lv") == l["lv"] for x in pk.get("learnset", [])):
                            P.add("learnedBy", "%s: learnedBy #%s lv %s no figura en el learnset de la especie" % (p, l["dex"], l["lv"]))
        else:
            P.add("tipo:learnedBy", "%s.learnedBy debe ser lista" % p)
        if isinstance(mv["tmLearners"], list):
            for d in mv["tmLearners"]:
                if ref("especie", d, dexes, p + ".tmLearners") and mv["tm"] is not None:
                    if mv["tm"] not in pk_by_dex[d].get("tms", []):
                        P.add("tmLearners", "%s: tmLearners incluye #%s pero su lista tms no contiene la MT%s" % (p, d, mv["tm"]))
        else:
            P.add("tipo:tmLearners", "%s.tmLearners debe ser lista" % p)
        if mv["baseline"] is not None:
            _t(P, isinstance(mv["baseline"], dict), p, "baseline", "objeto o null")
        df = mv["diff"]
        if _need(P, df, p + ".diff", ["changed", "fields"]):
            _t(P, isinstance(df["changed"], bool) and isinstance(df["fields"], list), p + ".diff", "changed/fields", "bool y lista")
    exp_learn = sum(len(x.get("learnedBy", [])) for x in lists["moves"] if isinstance(x, dict) and isinstance(x.get("learnedBy"), list))
    if exp_learn != learn_total:
        P.add("learnedBy.total", "Σ moves[].learnedBy (%d) != Σ pokemon[].learnset (%d)" % (exp_learn, learn_total))

    # ------------------------------------------------------------- habilidades
    holders_exp = {}
    for pk in lists["pokemon"]:
        if isinstance(pk, dict):
            for a in pk.get("abilities", []) if isinstance(pk.get("abilities"), list) else []:
                holders_exp.setdefault(a, set()).add(pk.get("dex"))
    for i, a in enumerate(lists["abilities"]):
        p = "abilities[%d]" % i
        if not _need(P, a, p, ["id", "sym", "name", "description", "holders", "baseline", "status", "note", "changed"]):
            continue
        _t(P, _is_int(a["id"]), p, "id", "entero")
        _t(P, _is_str(a["sym"]) and a["sym"] and _is_str(a["name"]) and a["name"], p, "sym/name", "texto no vacío")
        _t(P, _is_str(a["description"]), p, "description", "texto")
        if _t(P, isinstance(a["holders"], list), p, "holders", "lista"):
            for d in a["holders"]:
                ref("especie", d, dexes, p + ".holders")
            hs = set(a["holders"])
            miss = holders_exp.get(a["sym"], set()) - hs
            if miss:
                P.add("holders", "%s: holders no incluye a %s que sí tienen la habilidad" % (p, sorted(miss)[:5]))
        if a["baseline"] is not None:
            if _need(P, a["baseline"], p + ".baseline", ["description"]):
                _t(P, _is_str(a["baseline"]["description"]), p + ".baseline", "description", "texto")
        _t(P, a["status"] is None or a["status"] in STATUSES, p, "status", "debe ser Reworked|Buffed|Kept|Untouched|null (es %r)" % (a["status"],))
        _t(P, a["note"] is None or _is_str(a["note"]), p, "note", "texto o null")
        _t(P, isinstance(a["changed"], bool), p, "changed", "booleano")

    # ----------------------------------------------------------------- objetos
    icon_files = set((m.get("assets") or {}).get("itemIcons", [])) if isinstance(m.get("assets"), dict) else set()
    for i, it in enumerate(lists["items"]):
        p = "items[%d]" % i
        if not _need(P, it, p, ["id", "sym", "name", "plural", "pocket", "pocketName", "price", "description", "fieldUse", "battleUse", "special",
                                "move", "tm", "icon", "isNew", "where", "shops", "missions", "baseline", "diff"]):
            continue
        _t(P, _is_int(it["id"]), p, "id", "entero")
        _t(P, _is_str(it["sym"]) and it["sym"] and _is_str(it["name"]) and it["name"] and _is_str(it["plural"]), p, "sym/name/plural", "texto")
        for k in ("pocket", "price", "fieldUse", "battleUse", "special"):
            _t(P, _is_int(it[k]), p, k, "entero (es %r)" % (it[k],))
        _t(P, _is_str(it["pocketName"]), p, "pocketName", "texto")
        _t(P, _is_str(it["description"]), p, "description", "texto")
        ref("movimiento", it["move"], move_syms, p + ".move", allow_none=True)
        if it["tm"] is not None:
            ref("MT", it["tm"], tm_nums, p + ".tm")
        if it["icon"] is not None:
            if _t(P, _is_str(it["icon"]) and re.fullmatch(r"Icons/item\d{3,4}\.png", it["icon"]), p, "icon", "formato Icons/itemNNN.png (es %r)" % (it["icon"],)):
                if icon_files and it["icon"].split("/")[-1] not in icon_files:
                    P.add("icon", "%s: el icono %s no figura en assets.itemIcons" % (p, it["icon"]))
        _t(P, isinstance(it["isNew"], bool), p, "isNew", "booleano")
        if isinstance(it["where"], list):
            for w in it["where"]:
                if _need(P, w, p + ".where[]", ["loc", "qty", "method", "zone", "note"]):
                    ref("ubicación", w["loc"], loc_keys, p + ".where.loc")
                    _t(P, _is_int(w["qty"]), p + ".where[]", "qty", "entero")
        else:
            P.add("tipo:where", "%s.where debe ser lista" % p)
        if isinstance(it["shops"], list):
            for s in it["shops"]:
                if _need(P, s, p + ".shops[]", ["shop", "price"]):
                    ref("tienda", s["shop"], shop_keys, p + ".shops.shop")
                    _t(P, _is_int(s["price"]), p + ".shops[]", "price", "entero")
        else:
            P.add("tipo:shops", "%s.shops debe ser lista" % p)
        if isinstance(it["missions"], list):
            for n in it["missions"]:
                ref("misión", n, mission_ns, p + ".missions")
        else:
            P.add("tipo:missions", "%s.missions debe ser lista" % p)
        df = it["diff"]
        if _need(P, df, p + ".diff", ["changed", "fields"]):
            _t(P, isinstance(df["changed"], bool) and isinstance(df["fields"], list), p + ".diff", "changed/fields", "bool y lista")
    # ---------------------------------------------------------------------- MT
    for i, t in enumerate(lists["tms"]):
        p = "tms[%d]" % i
        if not _need(P, t, p, ["number", "sym", "move", "name", "price", "learners", "where", "missions"]):
            continue
        _t(P, _is_int(t["number"]) and t["number"] >= 1, p, "number", "entero >= 1")
        ref("movimiento", t["move"], move_syms, p + ".move")
        it = it_by_sym.get(t["sym"])
        if it is None:
            P.add("tm.item", "%s: la MT %s no existe como objeto" % (p, t["sym"]))
        else:
            _t(P, it.get("tm") == t["number"] and it.get("move") == t["move"], p, "sym", "no coincide con el objeto %s (tm=%r, move=%r)" % (t["sym"], it.get("tm"), it.get("move")))
        mv = mv_by_sym.get(t["move"])
        if mv is not None:
            _t(P, mv.get("tm") == t["number"], p, "move", "moves[%s].tm vale %r y la MT es %s" % (t["move"], mv.get("tm"), t["number"]))
        _t(P, _is_int(t["price"]), p, "price", "entero")
        if isinstance(t["learners"], list):
            for d in t["learners"]:
                ref("especie", d, dexes, p + ".learners")
        else:
            P.add("tipo:learners", "%s.learners debe ser lista" % p)
        if isinstance(t["where"], list):
            for w in t["where"]:
                if _need(P, w, p + ".where[]", ["loc", "qty", "method", "zone", "note"]):
                    ref("ubicación", w["loc"], loc_keys, p + ".where.loc")
        for n in t["missions"] if isinstance(t["missions"], list) else []:
            ref("misión", n, mission_ns, p + ".missions")

    # ------------------------------------------------------------ ubicaciones
    canon = _canonical_keys()
    wild_land = fish = 0
    for i, L in enumerate(lists["locations"]):
        p = "locations[%d]" % i
        if not _need(P, L, p, ["key", "name", "draftNames", "category", "act", "order", "node", "routeLabel", "coords", "path", "conn", "levelDay",
                               "levelNight", "etymology", "situation", "description", "events", "characters", "charKeys", "boss", "encounters",
                               "fishing", "items", "shops", "steps", "chapters"]):
            continue
        if canon is not None:
            _t(P, L["key"] in canon, p, "key", "clave de ubicación no canónica %r" % (L["key"],))
        _t(P, _is_str(L["name"]) and L["name"] and _is_str(L["category"]), p, "name/category", "texto no vacío")
        _t(P, isinstance(L["draftNames"], list) and all(_is_str(x) for x in L["draftNames"]), p, "draftNames", "lista de texto")
        _t(P, L["act"] is None or L["act"] in ACTS, p, "act", "debe ser I..V o null (es %r)" % (L["act"],))
        _t(P, L["order"] is None or _is_int(L["order"]), p, "order", "entero o null")
        _t(P, L["node"] is None or _is_int(L["node"]), p, "node", "entero o null")
        _t(P, L["routeLabel"] is None or _is_str(L["routeLabel"]), p, "routeLabel", "texto o null")
        _t(P, L["coords"] is None or (isinstance(L["coords"], list) and len(L["coords"]) == 2 and all(_is_num(x) for x in L["coords"])), p, "coords", "[x,y] o null")
        _t(P, L["path"] is None or (isinstance(L["path"], list) and all(isinstance(q, list) and len(q) == 2 and all(_is_num(x) for x in q) for q in L["path"])),
           p, "path", "lista de [x,y] o null")
        if _need(P, L["conn"], p + ".conn", ["N", "S", "E", "O"]):
            for d in "NSEO":
                c = L["conn"][d]
                if _need(P, c, "%s.conn.%s" % (p, d), ["keys", "text"]):
                    if isinstance(c["keys"], list):
                        for k in c["keys"]:
                            ref("ubicación", k, loc_keys, "%s.conn.%s" % (p, d))
                    else:
                        P.add("tipo:conn.keys", "%s.conn.%s.keys debe ser lista" % (p, d))
                    _t(P, _is_str(c["text"]), "%s.conn.%s" % (p, d), "text", "texto")
        _t(P, _range_ok(L["levelDay"]) and _range_ok(L["levelNight"]), p, "levelDay/levelNight", "[min,max] o null")
        for k in ("etymology", "situation", "description", "boss"):
            _t(P, _is_str(L[k]), p, k, "texto")
        for k in ("events", "characters"):
            _t(P, isinstance(L[k], list) and all(_is_str(x) for x in L[k]), p, k, "lista de texto")
        if isinstance(L["charKeys"], list):
            for k in L["charKeys"]:
                ref("personaje", k, char_keys, p + ".charKeys")
        else:
            P.add("tipo:charKeys", "%s.charKeys debe ser lista" % p)
        if isinstance(L["encounters"], list):
            for j, e in enumerate(L["encounters"]):
                q = "%s.encounters[%d]" % (p, j)
                if _need(P, e, q, ["zone", "zoneName", "kind", "slotCount", "slots"]):
                    _t(P, e["kind"] in KINDS_ENC, q, "kind", "debe ser Land|Cave|Surf (es %r)" % (e["kind"],))
                    _t(P, e["zone"] is None or _is_str(e["zone"]), q, "zone", "texto o null")
                    _t(P, _is_int(e["slotCount"]), q, "slotCount", "entero")
                    if isinstance(e["slots"], list):
                        for sl in e["slots"]:
                            if _need(P, sl, q + ".slots[]", ["slot", "rarity", "pct", "dex", "sym", "day", "night", "note"]):
                                wild_land += 1
                                _t(P, sl["rarity"] in RARITIES, q + ".slots[]", "rarity", "debe ser COMMON|UNCOMMON|RARE")
                                _t(P, _is_int(sl["pct"]) and _is_int(sl["slot"]), q + ".slots[]", "pct/slot", "enteros")
                                ref("especie", sl["dex"], dexes, q + ".slots.dex")
                                _t(P, _range_ok(sl["day"]) and _range_ok(sl["night"]), q + ".slots[]", "day/night", "[min,max] o null")
                    else:
                        P.add("tipo:slots", "%s.slots debe ser lista" % q)
        else:
            P.add("tipo:encounters", "%s.encounters debe ser lista" % p)
        if L["fishing"] is not None:
            if _need(P, L["fishing"], p + ".fishing", ["common", "rare"]):
                for rk in ("common", "rare"):
                    fe = L["fishing"][rk]
                    if fe is not None:
                        if _need(P, fe, "%s.fishing.%s" % (p, rk), ["pct", "dex", "day", "night", "note"]):
                            fish += 1
                            ref("especie", fe["dex"], dexes, "%s.fishing.%s.dex" % (p, rk))
                            _t(P, _is_int(fe["pct"]), "%s.fishing.%s" % (p, rk), "pct", "entero")
        for fz in L.get("fishingZones", []) if isinstance(L.get("fishingZones"), list) else []:
            pass
        if isinstance(L["items"], list):
            for w in L["items"]:
                if _need(P, w, p + ".items[]", ["item", "qty", "method", "zone", "note", "loc"]):
                    ref("objeto", w["item"], item_syms, p + ".items.item")
                    _t(P, w["loc"] == L["key"], p + ".items[]", "loc", "debe coincidir con la ubicación")
        else:
            P.add("tipo:loc.items", "%s.items debe ser lista" % p)
        for k in L["shops"] if isinstance(L["shops"], list) else []:
            ref("tienda", k, shop_keys, p + ".shops")
        for k in L["steps"] if isinstance(L["steps"], list) else []:
            ref("paso", k, step_nums, p + ".steps")
        for k in L["chapters"] if isinstance(L["chapters"], list) else []:
            ref("capítulo", k, story_keys, p + ".chapters")
    # fishSlots: entradas de pesca; wildSlots: casillas de tierra/cueva/surf (408 + 32 = 440 especies salvajes)
    # ----------------------------------------------------------------- tiendas
    mart_items = {}
    for i, s in enumerate(lists["shops"]):
        p = "shops[%d]" % i
        if not _need(P, s, p, ["key", "name", "medals", "cumulative", "location", "description", "requirement", "items", "stock"]):
            continue
        _t(P, _is_str(s["key"]) and s["key"] and _is_str(s["name"]), p, "key/name", "texto")
        _t(P, s["medals"] is None or _is_int(s["medals"]), p, "medals", "entero o null")
        _t(P, isinstance(s["cumulative"], bool), p, "cumulative", "booleano")
        ref("ubicación", s["location"], loc_keys, p + ".location", allow_none=True)
        _t(P, _is_str(s["description"]) and _is_str(s["requirement"]), p, "description/requirement", "texto")
        for fld in ("items", "stock"):
            if isinstance(s[fld], list):
                for e in s[fld]:
                    if _need(P, e, "%s.%s[]" % (p, fld), ["item", "price"]):
                        ref("objeto", e["item"], item_syms, "%s.%s.item" % (p, fld))
                        _t(P, _is_int(e["price"]), "%s.%s[]" % (p, fld), "price", "entero")
            else:
                P.add("tipo:shop." + fld, "%s.%s debe ser lista" % (p, fld))
        mm = re.match(r"^MART_(\d+)_MEDALS$", str(s["key"]))
        if mm and isinstance(s["items"], list) and isinstance(s["stock"], list):
            mart_items[int(mm.group(1))] = ({e.get("item") for e in s["items"] if isinstance(e, dict)}, {e.get("item") for e in s["stock"] if isinstance(e, dict)}, s["cumulative"])
    acc = set()
    for n in sorted(mart_items):
        own, stock, cum = mart_items[n]
        acc |= own
        if cum:
            _t(P, stock == acc, "shops[MART_%d_MEDALS]" % n, "stock", "no es la unión acumulada de las marts 0..%d" % n)
    # --------------------------------------------------------------- misiones
    for i, mi in enumerate(lists["missions"]):
        p = "missions[%d]" % i
        if _need(P, mi, p, ["n", "species", "item", "qty", "title", "note"]):
            _t(P, _is_int(mi["n"]) and _is_int(mi["species"]) and _is_int(mi["qty"]), p, "n/species/qty", "enteros")
            ref("objeto", mi["item"], item_syms, p + ".item")
            _t(P, _is_str(mi["title"]) and _is_str(mi["note"]), p, "title/note", "texto")
    # ------------------------------------------------------------ progresión
    for i, st in enumerate(lists["progression"]):
        p = "progression[%d]" % i
        if _need(P, st, p, ["step", "act", "loc", "summary", "levelCapDay", "levelCapNight", "boss", "bossType", "bossLevel", "tms", "keyItems"]):
            _t(P, _is_int(st["step"]), p, "step", "entero")
            _t(P, st["act"] is None or st["act"] in ACTS, p, "act", "I..V o null")
            ref("ubicación", st["loc"], loc_keys, p + ".loc", allow_none=True)
            _t(P, _is_str(st["summary"]), p, "summary", "texto")
            for k in ("levelCapDay", "levelCapNight", "bossLevel"):
                _t(P, st[k] is None or _is_int(st[k]), p, k, "entero o null")
            _t(P, _is_str(st["boss"]) and _is_str(st["bossType"]), p, "boss/bossType", "texto")
            if isinstance(st["tms"], list):
                for t in st["tms"]:
                    ref("MT", t, tm_syms, p + ".tms")
            else:
                P.add("tipo:prog.tms", "%s.tms debe ser lista" % p)
            _t(P, isinstance(st["keyItems"], list) and all(_is_str(x) for x in st["keyItems"]), p, "keyItems", "lista de texto")
    # ------------------------------------------------------------ personajes
    for i, c in enumerate(lists["characters"]):
        p = "characters[%d]" % i
        if _need(P, c, p, ["key", "name", "role", "category", "locations"]):
            _t(P, _is_str(c["key"]) and c["key"].startswith("CHAR_"), p, "key", "debe empezar por CHAR_ (es %r)" % (c["key"],))
            _t(P, _is_str(c["name"]) and c["name"] and _is_str(c["role"]) and _is_str(c["category"]), p, "name/role/category", "texto")
            if isinstance(c["locations"], list):
                for k in c["locations"]:
                    ref("ubicación", k, loc_keys, p + ".locations")
            else:
                P.add("tipo:char.locations", "%s.locations debe ser lista" % p)

    # --------------------------------------------------------------- crónica
    def chapter_ok(ch, p, prelude=False):
        if _need(P, ch, p, ["key", "title", "act", "loc", "characters", "charKeys", "paragraphs", "summary"]):
            _t(P, _is_str(ch["key"]) and (ch["key"] == "PRELUDE" if prelude else re.fullmatch(r"CHAPTER_\d+", ch["key"] or "")), p, "key", "clave no válida (%r)" % (ch["key"],))
            _t(P, _is_str(ch["title"]), p, "title", "texto")
            _t(P, ch["act"] is None or ch["act"] in ACTS or (prelude and ch["act"] == ""), p, "act", "I..V o null")
            ref("ubicación", ch["loc"], loc_keys, p + ".loc", allow_none=True)
            _t(P, isinstance(ch["characters"], list) and all(_is_str(x) for x in ch["characters"]), p, "characters", "lista de texto")
            if isinstance(ch["charKeys"], list):
                for k in ch["charKeys"]:
                    ref("personaje", k, char_keys, p + ".charKeys")
            else:
                P.add("tipo:chapter.charKeys", "%s.charKeys debe ser lista" % p)
            _t(P, isinstance(ch["paragraphs"], list) and all(_is_str(x) for x in ch["paragraphs"]), p, "paragraphs", "lista de texto")
            _t(P, ch["summary"] is None or _is_str(ch["summary"]), p, "summary", "texto o null")

    for i, ch in enumerate(lists["story"]):
        chapter_ok(ch, "story[%d]" % i)
    if m.get("prelude") is not None:
        chapter_ok(m["prelude"], "prelude", True)
    for i, l in enumerate(lists["ledger"]):
        p = "ledger[%d]" % i
        if _need(P, l, p, ["n", "name", "dominant", "loc", "chapter", "note"]):
            _t(P, _is_int(l["n"]), p, "n", "entero")
            _t(P, _is_str(l["name"]) and _is_str(l["dominant"]) and _is_str(l["note"]), p, "name/dominant/note", "texto")
            ref("ubicación", l["loc"], loc_keys, p + ".loc", allow_none=True)
            ref("capítulo", l["chapter"], story_keys, p + ".chapter", allow_none=True)

    # ------------------------------------------------------------- activos
    a = m.get("assets")
    if _need(P, a, "assets", ["icons", "battlers", "battlersBack", "battlersShiny", "itemIcons", "missing"]):
        for k in ("icons", "battlers", "battlersBack", "battlersShiny"):
            _t(P, isinstance(a[k], list) and all(_is_int(x) for x in a[k]), "assets", k, "lista de enteros")
        _t(P, isinstance(a["itemIcons"], list) and all(_is_str(x) for x in a["itemIcons"]), "assets", "itemIcons", "lista de nombres de archivo")
        _t(P, isinstance(a["missing"], list), "assets", "missing", "lista")
    # ------------------------------------------------- avisos y archivos
    for i, w in enumerate(lists["warnings"]):
        p = "warnings[%d]" % i
        if _need(P, w, p, ["file", "line", "severity", "code", "message", "suggestion", "text"]):
            _t(P, _is_str(w["file"]) and _is_int(w["line"]) and _is_str(w["code"]) and _is_str(w["message"]), p, "file/line/code/message", "tipos inválidos")
            _t(P, w["severity"] in SEVERITIES, p, "severity", "debe ser error|warn|info")
            _t(P, w["suggestion"] is None or _is_str(w["suggestion"]), p, "suggestion", "texto o null")
            _t(P, _is_str(w["text"]), p, "text", "texto")
    for i, f in enumerate(lists["files"]):
        p = "files[%d]" % i
        if _need(P, f, p, ["name", "exists", "size", "mtime", "lines", "errors", "warnings"]):
            _t(P, _is_str(f["name"]) and isinstance(f["exists"], bool), p, "name/exists", "texto y booleano")
            _t(P, _is_int(f["size"]) and _is_int(f["lines"]) and _is_int(f["errors"]) and _is_int(f["warnings"]), p, "size/lines/errors/warnings", "enteros")
            _t(P, _is_num(f["mtime"]), p, "mtime", "número")

    # --------------------------------------------------------------- recuentos
    if counts and all(k in counts for k in COUNT_KEYS):
        actual = {"pokemon": len(lists["pokemon"]), "moves": len(lists["moves"]), "abilities": len(lists["abilities"]), "items": len(lists["items"]),
                  "tms": len(lists["tms"]), "locations": len(lists["locations"]), "characters": len(lists["characters"]),
                  "chapters": len(lists["story"]), "steps": len(lists["progression"]), "shops": len(lists["shops"]),
                  "missions": len(lists["missions"]), "fishSlots": fish, "wildSlots": wild_land}
        for k, v in actual.items():
            if counts.get(k) != v:
                P.add("counts:" + k, "meta.counts.%s=%r pero la lista tiene %d elemento(s)" % (k, counts.get(k), v))
        if final:
            for k, v in FINAL_EXPECT.items():
                if counts.get(k) != v:
                    P.add("final:" + k, "recuento final esperado %s=%d y es %r" % (k, v, counts.get(k)))
            if counts.get("characters", 0) < 25:
                P.add("final:characters", "se esperaban >= 25 personajes y hay %r" % counts.get("characters"))
            if m.get("prelude") is None:
                P.add("final:prelude", "falta el preludio (prelude)")
            if len(lists["ledger"]) != 6:
                P.add("final:ledger", "el libro de cuentas debe tener 6 fragmentos y tiene %d" % len(lists["ledger"]))


def _load(src):
    if src.startswith("http://") or src.startswith("https://"):
        import urllib.request
        req = urllib.request.Request(src, headers={"Accept-Encoding": "identity"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    with open(src, encoding="utf-8") as f:
        return json.load(f)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    final = "--final" in argv
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    model = _load(args[0])
    probs = validate_model(model, final=final)
    if probs:
        print("CONTRATO: %d línea(s) de problemas" % len(probs))
        for p in probs:
            print(" - " + p)
        return 1
    print("CONTRATO: el modelo cumple SPEC §4.1%s" % (" (y los recuentos finales)" if final else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
