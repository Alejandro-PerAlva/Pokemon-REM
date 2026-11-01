"""Capa «mundo» del modelo: lectura de los ``rem_*.txt`` (SPEC §2) y resolución de referencias cruzadas.

Todas las funciones son tolerantes: una sección, línea o clave defectuosa solo produce un ``Warning``.
"""
import json
import os
import re

from .fuzzy import Lookup, Resolver, norm, parse_int
from .ini import parse_ini, parse_range, split_csv_max, split_list

F_LOC = "rem_locations.txt"
F_ENC = "rem_encounters.txt"
F_ITEMS = "rem_location_items.txt"
F_SHOPS = "rem_shops.txt"
F_PROG = "rem_progression.txt"
F_CHARS = "rem_characters.txt"
F_STORY = "rem_story.txt"
F_BASE = "rem_vanilla_baseline.txt"
F_LOG = "rem_changelog.txt"
REM_FILES = [F_LOC, F_ENC, F_ITEMS, F_SHOPS, F_PROG, F_CHARS, F_STORY, F_BASE, F_LOG]

CATEGORY_ES = {"CIUDAD": "Ciudad", "PUEBLO": "Pueblo", "ESPECIAL": "Lugar especial", "RUTA_NORMAL": "Ruta normal",
               "RUTA_ESPECIAL": "Ruta especial", "RUTA_MONTANA": "Ruta de montaña", "RUTA_MARINA": "Ruta marina",
               "RUTA_NEVADA": "Ruta nevada"}
OBTAIN_METHODS = ["WILD", "FISHING", "STARTER", "FOSSIL", "EVENT", "LEGENDARY", "EVOLUTION_LEVEL", "EVOLUTION_ITEM",
                  "EVOLUTION_STONE", "THIRD_STAGE"]
RARITIES = ["COMMON", "UNCOMMON", "RARE"]
ITEM_METHODS = set("BHCNEJPS")
RARITY_LK = Lookup("rareza", "rareza", fem=True)
for _r, _al in (("COMMON", ("Común", "Comun")), ("UNCOMMON", ("Incomún", "Infrecuente", "Poco común")), ("RARE", ("Raro", "Rara"))):
    RARITY_LK.add(_r, *_al)
YES = {"yes", "y", "true", "1", "si", "sí", "s", "sip", "verdadero"}


def load_location_keys(root):
    for p in (os.path.join(root, "tools", "codex", "location_keys.json"), os.path.join(os.path.dirname(os.path.abspath(__file__)), "location_keys.json")):
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, list) and d:
                return d
        except Exception:
            continue
    return []


def camel(k):
    parts = [p for p in re.split(r"[_\s\-]+", k.strip()) if p]
    if not parts:
        return k
    if len(parts) == 1:
        w = parts[0]
        return w[0].lower() + w[1:]
    return parts[0].lower() + "".join(p[:1].upper() + p[1:].lower() for p in parts[1:])


def _ks(*names):
    return {norm(n) for n in names}


_RX_SLOT = [re.compile(r"^slot\d+$")]
_RX_ITEM = [re.compile(r"^item\d+$")]
LOC_KNOWN = (_ks("Name", "DraftNames", "Category", "Act", "ProgressionOrder", "MapNodeNumber", "RouteLabel", "MapCoords", "MapPath",
                 "ConnN", "ConnS", "ConnE", "ConnO", "ConnW", "LevelRangeDay", "LevelRangeNight", "Etymology", "Situation",
                 "Description", "EventsSummary", "CharactersPresent", "BossInfo", "MapID", "MapIDStatus", "Zones"), [])
ENC_KNOWN = (_ks("Type", "ZoneName", "SlotCount", "FishCommon", "FishRare"), _RX_SLOT)
ITEMS_KNOWN = (_ks("Name", "Note", "Comment"), _RX_ITEM)
SHOP_KNOWN = (_ks("Name", "Medals", "Cumulative", "Location", "Locations", "Description", "Requirement", "UniqueItems", "ItemNote"), _RX_ITEM)
MISSION_KNOWN = (set(), [re.compile(r"^mission\d+$"), re.compile(r"^missioninfo\d+$")])
PROG_KNOWN = (_ks("StepNumber", "Act", "LocationKey", "StepName", "ObjectiveSummary", "LevelCapDay", "LevelCapNight", "BossOrGymTitle",
                  "BossType", "BossLevelCap", "RecommendedTMsAvailable", "RecommendedTMsCumulative", "KeyItemsUnlocked",
                  "FieldAbilitiesUnlocked", "MedalsAfterStep", "WildLevelsDay", "WildLevelsNight", "KeyEvents", "Chapters"), [])
STORY_KNOWN = (_ks("Title", "Act", "LocationKey", "CharactersInScene", "NarrativeText", "Summary", "MedalsEarned", "FragmentsInPlay",
                   "WildLevels", "Milestones", "WhyItMatters", "ActTitle", "ActIntro", "AltLocations", "Chapters"), [])
LEDGER_KNOWN = (_ks("Result", "Title", "Intro"), [re.compile(r"^fragment\d+$"), re.compile(r"^orb\d+$")])
CL_KNOWN = {"POKEMON": (_ks("Role", "Note"), []), "ABILITY": (_ks("Status", "Note"), []), "MOVE": (_ks("Note"), []), "ITEM": (_ks("Note"), []),
            "PRUNED_ITEMS": (set(), _RX_ITEM)}
BL_KNOWN = {"POKEMON": (_ks("Name", "InternalName", "Types", "BaseStats", "Abilities", "HiddenAbility", "Evolutions", "Moves", "EggMoves",
                             "WildItemCommon", "WildItemUncommon", "WildItemRare"), []),
            "MOVE": (_ks("ID", "Name", "Type", "Category", "Power", "Accuracy", "PP", "Priority", "FunctionCode", "AddlEffect", "Target", "Flags", "Description", "ExtraFields"), []),
            "ITEM": (_ks("ID", "Name", "Plural", "Pocket", "Price", "Description", "FieldUse", "BattleUse", "Special", "Move"), []),
            "ABILITY": (_ks("ID", "Name", "Description"), [])}

INT_EXTRAS = {"mapid", "medalsafterstep", "medalsearned", "recommendedtmscumulative"}
LIST_EXTRAS = {"fieldabilitiesunlocked", "altlocations", "chapters", "locations", "uniqueitems", "fragmentsinplay"}


def extra_fields(sec, consumed, existing, iss, file, coerce=True):
    """Claves no consumidas de una sección -> {camelCase: valor} (lista si se repite o si es de tipo lista; int si procede)."""
    out = {}
    done = set()
    for it in sec.items:
        k = it.key
        if k in consumed or k in done:
            continue
        done.add(k)
        vals = [x.value for x in sec.all_items(k)]
        ck = camel(it.raw_key)
        if ck in existing:
            ck = "x" + ck[:1].upper() + ck[1:]
        if coerce and k in INT_EXTRAS and len(vals) == 1:
            v = vals[0].strip()
            out[ck] = parse_int(iss, file, it.line, "%s de [%s]" % (it.raw_key, sec.key), v, default=None) if v else None
        elif coerce and k in LIST_EXTRAS:
            out[ck] = [x for v in vals for x in split_list(v)]
        elif len(vals) == 1:
            out[ck] = vals[0]
        else:
            out[ck] = vals
    return out


class World:
    """Datos de los rem_* ya interpretados (listas listas para el modelo)."""

    def __init__(self):
        self.locations = []
        self.shops = []
        self.missions = []
        self.progression = []
        self.characters = []
        self.story = []
        self.prelude = None
        self.ledger = []
        self.ledger_meta = {}
        self.pruned_items = []
        self.pruned_notes = {}
        self.changelog = {"pokemon": {}, "abilities": {}, "moves": {}, "items": {}}
        self.meta_log = {}
        self.obtain = {}                # dex -> [obtain entries]
        self.wild_slots = 0
        self.fish_slots = 0
        self.has = {}                   # nombre de archivo -> bool (con contenido)


class Builder:
    def __init__(self, files, iss, core, root, baseline=None):
        self.baseline = baseline
        self.files = files
        self.iss = iss
        self.core = core
        self.res = Resolver(iss)
        self.w = World()
        self.canon = load_location_keys(root)
        self.Ll = Lookup("ubicación", "ubicación", fem=True)
        self.canon_by_key = {}
        for i, c in enumerate(self.canon):
            self.canon_by_key[c["key"]] = dict(c, idx=i)
            nm = c.get("name", "")
            self.Ll.add(c["key"], nm, re.sub(r"\s*\(.*?\)\s*", "", nm), c["key"].replace("_", " "))
        self.char_index = {}          # norm(nombre|alias) -> key
        self.char_tokens = []         # (key, set(tokens))
        self.item_shops = {}
        self.warned_zone = set()
        self.w.locations = [self.default_location(c) for c in self.canon]
        self.loc_by_key = {L["key"]: L for L in self.w.locations}

    @staticmethod
    def default_location(c):
        key = c["key"]
        return {"key": key, "name": c.get("name", key), "draftNames": [], "category": CATEGORY_ES.get(c.get("category", ""), str(c.get("category", "")).capitalize()),
                "act": None, "order": None, "node": None, "routeLabel": None, "coords": None, "path": None,
                "conn": {d: {"keys": [], "text": ""} for d in "NSEO"}, "levelDay": None, "levelNight": None, "etymology": "",
                "situation": "", "description": "", "events": [], "characters": [], "charKeys": [], "boss": "",
                "encounters": [], "fishing": None, "fishingZones": [], "items": [], "shops": [], "marts": [], "steps": [], "chapters": [],
                "hasData": False}

    # ------------------------------------------------------------------ utilidades
    def tf(self, name):
        t = self.files.get(name)
        return t if (t is not None and t.ok) else None

    def sections(self, name, **kw):
        t = self.tf(name)
        self.w.has[name] = bool(t)
        if not t:
            return []
        try:
            return parse_ini(t, self.iss, name, **kw)
        except Exception as e:  # pragma: no cover
            self.iss.add(name, 0, "error", "INTERNAL", "Error interno leyendo %s (%s)" % (name, e.__class__.__name__))
            return []

    def loc(self, raw, file, line, text=None, allow_zone=True):
        """-> (LOC_KEY | None, zona | None)."""
        raw = (raw or "").strip()
        if not raw:
            return None, None
        base, _, zone = raw.partition(":")
        key = self.res.ref(self.Ll, base, file, line, "UNKNOWN_LOCATION", text=text)
        z = zone.strip().upper() or None
        return key, z

    def item(self, raw, file, line, text=None, context=None):
        return self.res.ref(self.core.Li, raw, file, line, "UNKNOWN_ITEM", text=text, context=context)

    def species(self, raw, file, line, text=None, context=None):
        return self.res.ref(self.core.Ls, raw, file, line, "UNKNOWN_SPECIES", text=text, context=context)

    def int_(self, file, line, label, text, default=None, **kw):
        return parse_int(self.iss, file, line, label, text, default=default, **kw)

    def run(self):
        for fn in (self.do_characters, self.do_locations, self.do_progression, self.do_story, self.do_encounters,
                   self.do_location_items, self.do_shops, self.do_changelog):
            try:
                fn()
            except Exception as e:  # pragma: no cover
                self.iss.add(fn.__name__, 0, "error", "INTERNAL", "Error interno en %s (%s: %s); se continúa" % (fn.__name__, e.__class__.__name__, e))
        try:
            self.link()
        except Exception as e:  # pragma: no cover
            self.iss.add("modelo", 0, "error", "INTERNAL", "Error enlazando referencias cruzadas (%s: %s)" % (e.__class__.__name__, e))
        return self.w

    # ---------------------------------------------------------------- personajes
    def do_characters(self):
        f = F_CHARS
        secs = self.sections(f)
        seen = {}
        out = []
        for s in secs:
            try:
                key = s.key.strip()
                ukey = key.upper()
                if not ukey.startswith("CHAR_"):
                    if ukey.startswith("CHAR"):
                        nk = "CHAR_" + re.sub(r"^CHAR[_\s\-]*", "", ukey)
                        self.iss.add(f, s.line, "warn", "BAD_LINE", "Clave de personaje «%s» no empieza por CHAR_; se usa «%s»" % (key, nk), suggestion=nk, applied=True)
                        ukey = nk
                    else:
                        self.iss.add(f, s.line, "warn", "BAD_LINE", "Sección «%s» sin el prefijo CHAR_; se usa «CHAR_%s»" % (key, ukey), suggestion="CHAR_" + ukey, applied=True)
                        ukey = "CHAR_" + ukey
                ch = {"key": ukey}
                multi = {}
                for it in s.items:
                    multi.setdefault(camel(it.raw_key), []).append(it.value)
                for ck, vals in multi.items():
                    if ck in ("quotes", "quote"):
                        ch["quotes"] = [v for v in vals if v]
                    elif len(vals) == 1:
                        ch[ck] = vals[0]
                    else:
                        ch[ck] = vals
                ch.setdefault("name", ukey[5:].replace("_", " ").title())
                if not ch.get("name"):
                    self.iss.add(f, s.line, "warn", "MISSING_FIELD", "El personaje %s no tiene Name" % ukey)
                    ch["name"] = ukey[5:].replace("_", " ").title()
                ch.setdefault("role", "")
                ch.setdefault("category", "")
                ch.setdefault("quotes", [])
                if "locations" not in ch:
                    ch["locations"] = []
                locs_raw = ch.get("locations")
                if isinstance(locs_raw, list):
                    locs_raw = ";".join(locs_raw)
                locs = []
                ln = s.line_of("Locations")
                for tok in split_list(locs_raw or ""):
                    k, _z = self.loc(tok, f, ln)
                    if k and k not in locs:
                        locs.append(k)
                ch["locations"] = locs
                if ch.get("firstLocation"):
                    fl = ch["firstLocation"] if isinstance(ch["firstLocation"], str) else ch["firstLocation"][0]
                    k, _z = self.loc(fl, f, s.line_of("FirstLocation"))
                    ch["firstLocation"] = k
                team = ch.get("team")
                if team is not None:
                    ch["teamList"] = [t.strip() for t in ([team] if isinstance(team, str) else team) if t and t.strip()]
                if ch.get("aliases") is not None:
                    a = ch["aliases"] if isinstance(ch["aliases"], str) else ";".join(ch["aliases"])
                    ch["aliasList"] = [x.strip() for x in (a.split(";") if ";" in a else a.split(",")) if x.strip()]
                chron = ch.get("chronology")
                if chron:
                    cl = []
                    cln = s.line_of("Chronology")
                    for row in ([chron] if isinstance(chron, str) else chron):
                        p6 = [x.strip() for x in row.split("|", 5)]
                        while len(p6) < 6:
                            p6.append("")
                        ck = None
                        if p6[2]:
                            ck, _z = self.loc(p6[2], f, cln)
                        cl.append({"n": p6[0], "place": p6[1], "loc": ck, "event": p6[3], "role": p6[4], "combat": p6[5]})
                    ch["chronologyList"] = cl
                ch["line"] = s.line
                if ukey in seen:
                    self.iss.add(f, s.line, "warn", "DUPLICATE_KEY", "Personaje %s duplicado (primera definición en la línea %d); se usa el último" % (ukey, seen[ukey]))
                    out = [c for c in out if c["key"] != ukey]
                seen[ukey] = s.line
                out.append(ch)
            except Exception:
                self.iss.add(f, getattr(s, "line", 0), "warn", "BAD_LINE", "No se pudo interpretar el personaje [%s]" % getattr(s, "key", "?"))
        self.w.characters = out
        for c in out:
            names = [c.get("name", "")]
            names += c.get("aliasList", [])
            for n in names:
                for variant in (re.sub(r"\(.*?\)", "", n), n):
                    nn = norm(variant)
                    if nn:
                        self.char_index.setdefault(nn, c["key"])
            toks = set(t for t in re.split(r"\W+", re.sub(r"\(.*?\)", "", norm_spaces(c.get("name", "")).lower())) if len(t) > 2)
            self.char_tokens.append((c["key"], toks))

    def chars_from_names(self, names):
        keys = []
        for n in names:
            k = self.char_key(n)
            if k and k not in keys:
                keys.append(k)
        return keys

    def char_key(self, name):
        if not name:
            return None
        stripped = re.sub(r"\(.*?\)", "", name).strip()
        for cand in (stripped, name):
            k = self.char_index.get(norm(cand))
            if k:
                return k
        toks = set(t for t in re.split(r"\W+", stripped.lower()) if len(t) > 2)
        if toks:
            hits = [k for k, ct in self.char_tokens if toks <= ct and ct]
            if len(hits) == 1:
                return hits[0]
        return None

    # ---------------------------------------------------------------- ubicaciones
    def do_locations(self):
        f = F_LOC
        secs = self.sections(f, known=lambda sec: LOC_KNOWN, single=["Name", "Category", "Act", "ProgressionOrder", "MapCoords", "MapPath"])
        by_key = {}
        for s in secs:
            try:
                key = self.res.ref(self.Ll, s.key, f, s.line, "UNKNOWN_LOCATION", text=s.raw_header)
                if not key:
                    continue
                if key in by_key:
                    self.iss.add(f, s.line, "warn", "DUPLICATE_KEY", "Ubicación %s duplicada (primera en la línea %d); se usa la última" % (key, by_key[key][0]))
                by_key[key] = (s.line, s)
            except Exception:
                self.iss.add(f, getattr(s, "line", 0), "warn", "BAD_LINE", "No se pudo interpretar la ubicación [%s]" % getattr(s, "key", "?"))
        if self.tf(f) and len(by_key) < len(self.canon):
            missing = [c["key"] for c in self.canon if c["key"] not in by_key]
            if missing:
                self.iss.add(f, 0, "warn", "MISSING_FIELD", "Faltan %d ubicaciones en %s: %s%s" % (len(missing), f, ", ".join(missing[:6]), "…" if len(missing) > 6 else ""))
        locs = []
        for c in self.canon:
            key = c["key"]
            ln, s = by_key.get(key, (0, None))
            L = self.loc_by_key[key]
            L["hasData"] = s is not None
            if s is not None:
                try:
                    g = s.last
                    L["name"] = g("Name").strip() or L["name"]
                    L["draftNames"] = split_list(";".join(s.all("DraftNames")))
                    cat_raw = g("Category").strip()
                    if cat_raw:
                        L["category"] = cat_raw
                    act = g("Act").strip().upper()
                    L["act"] = act or None
                    if act and act not in ("I", "II", "III", "IV", "V"):
                        self.iss.add(f, s.line_of("Act"), "warn", "BAD_LINE", "Acto desconocido «%s» en %s (se esperan I a V)" % (act, key))
                    po = g("ProgressionOrder").strip()
                    L["order"] = self.int_(f, s.line_of("ProgressionOrder"), "ProgressionOrder de %s" % key, po) if po else None
                    nn = g("MapNodeNumber").strip()
                    L["node"] = self.int_(f, s.line_of("MapNodeNumber"), "MapNodeNumber de %s" % key, nn) if nn else None
                    L["routeLabel"] = g("RouteLabel").strip() or None
                    L["coords"] = self.pair(g("MapCoords"), f, s.line_of("MapCoords"), key)
                    L["path"] = self.path(g("MapPath"), f, s.line_of("MapPath"), key)
                    for d, kk in (("N", "ConnN"), ("S", "ConnS"), ("E", "ConnE"), ("O", "ConnO")):
                        raw = ";".join(s.all(kk)) if s.has(kk) else (";".join(s.all("ConnW")) if d == "O" and s.has("ConnW") else "")
                        L["conn"][d] = self.conn(raw, f, s.line_of(kk), key)
                    L["levelDay"] = self.lr(g("LevelRangeDay"), f, s.line_of("LevelRangeDay"), key)
                    L["levelNight"] = self.lr(g("LevelRangeNight"), f, s.line_of("LevelRangeNight"), key)
                    L["etymology"] = " ".join(s.all("Etymology")).strip()
                    L["situation"] = " ".join(s.all("Situation")).strip()
                    L["description"] = "\n\n".join(s.all("Description")) if len(s.all("Description")) > 1 else g("Description").strip()
                    L["events"] = split_list(";".join(s.all("EventsSummary")))
                    L["characters"] = split_list(";".join(s.all("CharactersPresent")))
                    L["boss"] = " ".join(s.all("BossInfo")).strip()
                    L.update(extra_fields(s, LOC_KNOWN[0], L, self.iss, f))
                    L["mapId"] = self.int_(f, s.line_of("MapID"), "MapID de %s" % key, g("MapID")) if g("MapID").strip() else None
                    L["mapIdStatus"] = g("MapIDStatus").strip() or None
                    zl = []
                    for chunk in re.split(r";\s*(?=[A-Za-z0-9]{1,3}\s*:)", g("Zones").strip()):
                        mz = re.match(r"^([A-Za-z0-9]+)\s*:\s*(.*)$", chunk)
                        if mz:
                            zl.append({"zone": mz.group(1).upper(), "text": mz.group(2).strip()})
                    L["zoneList"] = zl
                except Exception:
                    self.iss.add(f, s.line, "warn", "BAD_LINE", "No se pudo interpretar por completo la ubicación %s" % key)
            locs.append(L)
        self.w.locations = locs

    def pair(self, text, f, line, key):
        t = (text or "").strip()
        if not t:
            return None
        nums = re.findall(r"-?\d+(?:\.\d+)?", t)
        if len(nums) < 2:
            self.iss.add(f, line, "error", "BAD_NUMBER", "Coordenadas inválidas en %s: «%s» (se espera x,y)" % (key, t))
            return None
        a, b = float(nums[0]), float(nums[1])
        return [int(a) if a == int(a) else a, int(b) if b == int(b) else b]

    def path(self, text, f, line, key):
        t = (text or "").strip()
        if not t:
            return None
        pts = []
        for chunk in re.split(r"\s*[;|]\s*", t):
            nums = re.findall(r"-?\d+(?:\.\d+)?", chunk)
            if len(nums) >= 2:
                a, b = float(nums[0]), float(nums[1])
                pts.append([int(a) if a == int(a) else a, int(b) if b == int(b) else b])
            elif chunk.strip():
                self.iss.add(f, line, "warn", "BAD_NUMBER", "Punto de MapPath ilegible en %s: «%s»" % (key, chunk.strip()))
        return pts or None

    def lr(self, text, f, line, key):
        t = (text or "").strip()
        if not t:
            return None
        r = parse_range(t)
        if r is None:
            v = self.int_(f, line, "rango de niveles de %s" % key, t.split("-")[0] if "-" in t else t)
            if v is None:
                return None
            self.iss.add(f, line, "warn", "BAD_NUMBER", "Rango de niveles mal formado en %s: «%s»" % (key, t))
            return [v, v]
        return r

    def conn(self, raw, f, line, key):
        raw = (raw or "").strip()
        keys, text = [], ""
        if not raw:
            return {"keys": keys, "text": text}
        if "|" in raw:
            left, text = raw.split("|", 1)
            text = text.strip()
        else:
            left = raw
        toks = [t.strip() for t in re.split(r"[,;]", left) if t.strip()]
        if "|" not in raw and toks and not all(self.Ll.lookup(t)[0] for t in toks):
            # sin barra: si no son claves, es texto libre (p. ej. «Cruce de las Rutas 20 y 21»)
            if not any(self.Ll.lookup(t)[0] for t in toks):
                return {"keys": [], "text": raw}
        for t in toks:
            k = self.res.ref(self.Ll, t, f, line, "UNKNOWN_LOCATION", context="conexión de %s" % key)
            if k and k not in keys:
                keys.append(k)
        return {"keys": keys, "text": text}

    # ----------------------------------------------------------------- progresión
    def do_progression(self):
        f = F_PROG
        secs = self.sections(f, known=lambda sec: PROG_KNOWN)
        out = {}
        for s in secs:
            try:
                m = re.match(r"^STEP[_\s\-]*(\d+)$", s.ukey)
                if not m:
                    self.iss.add(f, s.line, "warn", "BAD_LINE", "Sección [%s] ignorada: se esperaba STEP_NN" % s.key, text=s.raw_header)
                    continue
                n = int(m.group(1))
                sn = s.last("StepNumber").strip()
                if sn:
                    v = self.int_(f, s.line_of("StepNumber"), "StepNumber de %s" % s.key, sn)
                    if v is not None and v != n:
                        self.iss.add(f, s.line_of("StepNumber"), "warn", "BAD_NUMBER", "StepNumber=%d no coincide con la sección %s" % (v, s.key))
                        n = v
                loc, _z = self.loc(s.last("LocationKey"), f, s.line_of("LocationKey"))
                if not s.last("LocationKey").strip():
                    self.iss.add(f, s.line, "warn", "MISSING_FIELD", "Falta LocationKey en %s" % s.key)
                tms = []
                for tok in split_list(";".join(s.all("RecommendedTMsAvailable"))):
                    it = self.item(tok, f, s.line_of("RecommendedTMsAvailable"), context="paso %d" % n)
                    if it and it not in tms:
                        tms.append(it)
                keyitems = split_list(";".join(s.all("KeyItemsUnlocked")))
                d = {"step": n, "act": s.last("Act").strip().upper() or None, "loc": loc,
                     "summary": " ".join(s.all("ObjectiveSummary")).strip(),
                     "levelCapDay": self.int_(f, s.line_of("LevelCapDay"), "LevelCapDay de %s" % s.key, s.last("LevelCapDay")),
                     "levelCapNight": self.int_(f, s.line_of("LevelCapNight"), "LevelCapNight de %s" % s.key, s.last("LevelCapNight")),
                     "boss": s.last("BossOrGymTitle").strip(), "bossType": s.last("BossType").strip(),
                     "bossLevel": self.int_(f, s.line_of("BossLevelCap"), "BossLevelCap de %s" % s.key, s.last("BossLevelCap")),
                     "tms": tms, "keyItems": keyitems, "line": s.line}
                d.update(extra_fields(s, PROG_KNOWN[0] - _ks("StepName", "KeyEvents", "FieldAbilitiesUnlocked", "RecommendedTMsCumulative", "MedalsAfterStep",
                                                              "WildLevelsDay", "WildLevelsNight", "Chapters"), d, self.iss, f))
                d["chapters"] = [self.chap_key(c) for c in d.get("chapters", []) if c]
                if n in out:
                    self.iss.add(f, s.line, "warn", "DUPLICATE_KEY", "Paso %d duplicado; se usa el último" % n)
                out[n] = d
            except Exception:
                self.iss.add(f, getattr(s, "line", 0), "warn", "BAD_LINE", "No se pudo interpretar el paso [%s]" % getattr(s, "key", "?"))
        self.w.progression = [out[k] for k in sorted(out)]

    # ------------------------------------------------------------------- crónica
    def chap_key(self, c):
        m = re.match(r"^CHAPTER[_\s\-]*(\d+)$", (c or "").strip().upper())
        return "CHAPTER_%02d" % int(m.group(1)) if m else (c or "").strip()

    def do_story(self):
        f = F_STORY
        secs = self.sections(f, known=lambda sec: LEDGER_KNOWN if sec.ukey == "FRAGMENT_LEDGER" else STORY_KNOWN)
        chapters = {}
        for s in secs:
            try:
                u = s.ukey
                if u == "FRAGMENT_LEDGER":
                    self.ledger(s)
                    continue
                if u == "PRELUDE":
                    self.w.prelude = self.chapter(s, "PRELUDE")
                    continue
                m = re.match(r"^CHAPTER[_\s\-]*(\d+)$", u)
                if not m:
                    self.iss.add(f, s.line, "info", "UNKNOWN_KEY", "Sección [%s] desconocida en rem_story.txt; se ignora" % s.key, text=s.raw_header)
                    continue
                key = "CHAPTER_%02d" % int(m.group(1))
                if key in chapters:
                    self.iss.add(f, s.line, "warn", "DUPLICATE_KEY", "Capítulo %s duplicado (primero en la línea %d); se usa el último" % (key, chapters[key]["line"]))
                chapters[key] = self.chapter(s, key)
            except Exception:
                self.iss.add(f, getattr(s, "line", 0), "warn", "BAD_LINE", "No se pudo interpretar la sección [%s]" % getattr(s, "key", "?"))
        self.w.story = [chapters[k] for k in sorted(chapters)]

    def chapter(self, s, key):
        f = F_STORY
        names = split_list(";".join(s.all("CharactersInScene")))
        loc, _z = self.loc(s.last("LocationKey"), f, s.line_of("LocationKey")) if s.last("LocationKey").strip() else (None, None)
        paragraphs = [p for p in s.all("NarrativeText") if p.strip()]
        if not paragraphs and key != "PRELUDE":
            self.iss.add(f, s.line, "warn", "MISSING_FIELD", "El capítulo %s no tiene NarrativeText" % key)
        d = {"key": key, "title": s.last("Title").strip(), "act": s.last("Act").strip().upper() or None, "loc": loc,
             "characters": names, "charKeys": self.chars_from_names(names), "paragraphs": paragraphs,
             "summary": (" ".join(s.all("Summary")).strip() or None), "line": s.line}
        d.update(extra_fields(s, _ks("Title", "Act", "LocationKey", "CharactersInScene", "NarrativeText", "Summary"), d, self.iss, f))
        if "altLocations" in d:
            alts = []
            for tok in d["altLocations"]:
                k, _z = self.loc(tok, f, s.line_of("AltLocations"))
                if k and k not in alts:
                    alts.append(k)
            d["altLocations"] = alts
        if "chapters" in d:
            d["chapters"] = [self.chap_key(c) for c in d["chapters"] if c]
        for lk in ("milestones",):
            if lk in d and not isinstance(d[lk], list):
                d[lk] = [d[lk]] if d[lk] else []
        return d

    def ledger(self, s):
        f = F_STORY
        out = []
        orbs = {}
        for it in s.items:
            mo = re.match(r"^orb(\d+)$", it.key)
            if mo:
                orbs[int(mo.group(1))] = it.value.strip()
        self.w.ledger_meta = {"result": s.last("Result").strip() or None, "title": s.last("Title").strip() or None, "intro": s.last("Intro").strip() or None}
        for it in s.items:
            m = re.match(r"^fragment(\d+)$", it.key)
            if not m:
                continue
            parts = split_csv_max(it.value, 4)
            loc, _z = self.loc(parts[2], f, it.line) if parts[2] else (None, None)
            chap = parts[3].strip().upper()
            mm = re.match(r"^CHAPTER[_\s\-]*(\d+)$", chap)
            if mm:
                chap = "CHAPTER_%02d" % int(mm.group(1))
            elif chap:
                self.iss.add(f, it.line, "warn", "BAD_LINE", "Capítulo «%s» ilegible en el libro de cuentas (se espera CHAPTER_NN)" % parts[3])
            out.append({"n": int(m.group(1)), "name": parts[0], "dominant": parts[1], "loc": loc, "chapter": chap or None, "note": parts[4],
                        "orb": orbs.get(int(m.group(1)))})
        out.sort(key=lambda x: x["n"])
        self.w.ledger = out

    # ----------------------------------------------------------------- encuentros
    def do_encounters(self):
        f = F_ENC
        secs = self.sections(f)
        by_loc = self.loc_by_key
        pokes = self.core.by_dex
        special = None
        slots_total = fish_total = 0
        wild_by_dex = {}
        for s in secs:
            try:
                if s.ukey.replace(" ", "_") in ("SPECIAL_OBTAINABILITY", "SPECIALOBTAINABILITY"):
                    special = s
                    continue
                key, zone = self.loc(s.key, f, s.line, text=s.raw_header)
                if not key:
                    continue
                L = by_loc.get(key)
                kind = s.last("Type").strip()
                if kind:
                    kk = norm(kind)
                    kind = {"land": "Land", "cave": "Cave", "surf": "Surf", "water": "Surf"}.get(kk)
                    if not kind:
                        kind = "Land"
                        self.iss.add(f, s.line_of("Type"), "warn", "BAD_LINE", "Tipo de encuentro desconocido «%s» en [%s] (Land, Cave o Surf); se usa Land" % (s.last("Type").strip(), s.key))
                else:
                    kind = "Land"
                zone_name = s.last("ZoneName").strip() or None
                slots = []
                slot_items = [it for it in s.items if re.match(r"^slot\d+$", it.key)]
                declared = None
                if s.last("SlotCount").strip():
                    declared = self.int_(f, s.line_of("SlotCount"), "SlotCount de [%s]" % s.key, s.last("SlotCount"))
                seen_slots = {}
                for it in slot_items:
                    n = int(it.key[4:])
                    if n in seen_slots:
                        self.iss.add(f, it.line, "warn", "DUPLICATE_KEY", "Casilla %s repetida en [%s] (primera en la línea %d)" % (it.raw_key, s.key, seen_slots[n]))
                    seen_slots[n] = it.line
                    sl = self.slot(it, n, s.key)
                    if sl:
                        slots.append(sl)
                slots.sort(key=lambda x: x["slot"])
                if declared is not None and declared != len(slots) and (slot_items or declared):
                    self.iss.add(f, s.line_of("SlotCount"), "warn", "MISSING_FIELD",
                                 "[%s] declara SlotCount=%d pero define %d casillas válidas" % (s.key, declared, len(slots)))
                if slots and L is not None:
                    L["encounters"].append({"zone": zone, "zoneName": zone_name, "kind": kind, "slotCount": declared if declared else len(slots), "slots": slots})
                    slots_total += len(slots)
                    for sl in slots:
                        wild_by_dex.setdefault(sl["dex"], []).append(
                            {"loc": key, "zone": zone, "zoneName": zone_name, "kind": kind, "rarity": sl["rarity"], "pct": sl["pct"],
                             "day": sl["day"], "night": sl["night"], "note": sl["note"], "slot": sl["slot"]})
                fish = {}
                for fk, rar, sn in (("FishCommon", "COMMON", "P1"), ("FishRare", "RARE", "P2")):
                    its = s.all_items(fk)
                    if not its:
                        continue
                    if len(its) > 1:
                        self.iss.add(f, its[1].line, "warn", "DUPLICATE_KEY", "%s repetido en [%s]; se usa el último" % (fk, s.key))
                    fe = self.fish(its[-1], s.key, rar)
                    if fe:
                        fish["common" if rar == "COMMON" else "rare"] = fe
                        fish_total += 1
                        wild_by_dex.setdefault(fe["dex"], []).append(
                            {"loc": key, "zone": zone, "zoneName": zone_name, "kind": "Fish", "rarity": rar, "pct": fe["pct"],
                             "day": fe["day"], "night": fe["night"], "note": fe["note"], "slot": sn})
                if fish and L is not None:
                    L["fishingZones"].append({"zone": zone, "zoneName": zone_name, "common": fish.get("common"), "rare": fish.get("rare")})
                    if L["fishing"] is None:
                        L["fishing"] = {"common": fish.get("common"), "rare": fish.get("rare")}
                if not slots and not fish and not s.has("Type") and not slot_items:
                    self.iss.add(f, s.line, "warn", "MISSING_FIELD", "La sección [%s] no define casillas ni pesca" % s.key)
            except Exception:
                self.iss.add(f, getattr(s, "line", 0), "warn", "BAD_LINE", "No se pudo interpretar la sección [%s]" % getattr(s, "key", "?"))
        for dex, lst in wild_by_dex.items():
            p = pokes.get(dex)
            if p is not None:
                p["wild"].extend(lst)
        self.w.wild_slots = slots_total + fish_total
        self.w.fish_slots = fish_total
        if special is not None:
            try:
                self.obtainability(special)
            except Exception:
                self.iss.add(f, special.line, "warn", "BAD_LINE", "No se pudo interpretar [SPECIAL_OBTAINABILITY]")

    def rng2(self, a, b, f, line, label):
        lo = self.int_(f, line, label + " (mín.)", a) if a.strip() else None
        hi = self.int_(f, line, label + " (máx.)", b) if b.strip() else None
        if lo is None and hi is None:
            return None
        if lo is None:
            lo = hi
        if hi is None:
            hi = lo
        if lo > hi:
            self.iss.add(f, line, "warn", "BAD_NUMBER", "%s: el nivel mínimo (%d) es mayor que el máximo (%d)" % (label, lo, hi))
            lo, hi = hi, lo
        return [lo, hi]

    def slot(self, it, n, secname):
        f = F_ENC
        p = split_csv_max(it.value, 7)
        if not it.value.strip():
            self.iss.add(f, it.line, "warn", "MISSING_FIELD", "Casilla %s vacía en [%s]" % (it.raw_key, secname), text=None)
            return None
        rar_raw = p[0].strip()
        rar = self.res.ref(RARITY_LK, rar_raw, f, it.line, "BAD_LINE", context="casilla %s de [%s]" % (it.raw_key, secname)) if rar_raw else None
        if not rar:
            rar = "COMMON"
            if not rar_raw:
                self.iss.add(f, it.line, "warn", "MISSING_FIELD", "Casilla %s sin rareza; se usa COMMON" % it.raw_key)
        pct_raw = p[1].strip().rstrip("%")
        pct = self.int_(f, it.line, "porcentaje de %s en [%s]" % (it.raw_key, secname), pct_raw, default=0)
        sp = self.species(p[2], f, it.line, context="casilla %s de [%s]" % (it.raw_key, secname)) if p[2].strip() else None
        if not p[2].strip():
            self.iss.add(f, it.line, "error", "MISSING_FIELD", "Casilla %s sin especie en [%s]; se omite" % (it.raw_key, secname))
        if not sp:
            return None
        dex = self.core.sym_dex.get(sp)
        day = self.rng2(p[3], p[4], f, it.line, "niveles de día de %s" % it.raw_key)
        night = self.rng2(p[5], p[6], f, it.line, "niveles de noche de %s" % it.raw_key)
        return {"slot": n, "rarity": rar, "pct": pct, "dex": dex, "sym": sp, "day": day, "night": night, "note": p[7].strip()}

    def fish(self, it, secname, rar):
        f = F_ENC
        p = split_csv_max(it.value, 6)
        pct = self.int_(f, it.line, "porcentaje de %s en [%s]" % (it.raw_key, secname), p[0].strip().rstrip("%"), default=0)
        sp = self.species(p[1], f, it.line, context="%s de [%s]" % (it.raw_key, secname)) if p[1].strip() else None
        if not p[1].strip():
            self.iss.add(f, it.line, "error", "MISSING_FIELD", "%s sin especie en [%s]; se omite" % (it.raw_key, secname))
        if not sp:
            return None
        return {"pct": pct, "dex": self.core.sym_dex.get(sp), "sym": sp, "day": self.rng2(p[2], p[3], f, it.line, "niveles de día de pesca"),
                "night": self.rng2(p[4], p[5], f, it.line, "niveles de noche de pesca"), "note": p[6].strip()}

    def obtainability(self, s):
        f = F_ENC
        ml = Lookup("método de obtención", "método de obtención")
        for m in OBTAIN_METHODS:
            ml.add(m, m.replace("_", " "))
        pokes = self.core.by_dex
        seen = set()
        for it in s.items:
            try:
                kraw = it.raw_key.strip()
                dex = None
                if re.fullmatch(r"\d+", kraw):
                    dex = int(kraw)
                    if dex not in pokes:
                        self.iss.add(f, it.line, "error", "UNKNOWN_SPECIES", "Número de Pokédex %d desconocido en [SPECIAL_OBTAINABILITY]; se omite" % dex)
                        continue
                else:
                    sp = self.species(kraw, f, it.line, context="[SPECIAL_OBTAINABILITY]")
                    dex = self.core.sym_dex.get(sp) if sp else None
                    if dex is None:
                        continue
                p = split_csv_max(it.value, 3)
                method = self.res.ref(ml, p[0], f, it.line, "BAD_LINE", context="obtención de #%03d" % dex) if p[0].strip() else None
                if not method:
                    if not p[0].strip():
                        self.iss.add(f, it.line, "error", "MISSING_FIELD", "Falta el método de obtención de #%03d" % dex)
                    continue
                loc = None
                if p[1].strip():
                    loc, _z = self.loc(p[1], f, it.line)
                level = p[2].strip()
                if level and not re.fullmatch(r"\d+(\s*[-–]\s*\d+)?", level):
                    self.iss.add(f, it.line, "warn", "BAD_NUMBER", "Nivel de obtención ilegible en #%03d: «%s»" % (dex, level))
                level = re.sub(r"\s*[-–]\s*", "-", level)
                self.w.obtain.setdefault(dex, []).append({"method": method, "loc": loc, "level": level, "detail": p[3].strip()})
                if dex in seen:
                    self.iss.add(f, it.line, "warn", "DUPLICATE_KEY", "La especie #%03d tiene más de una línea en [SPECIAL_OBTAINABILITY]" % dex)
                seen.add(dex)
            except Exception:
                self.iss.add(f, it.line, "warn", "BAD_LINE", "Línea de obtenibilidad ilegible", text=None)
        if self.core.pokemon:
            missing = [p["dex"] for p in self.core.pokemon if p["dex"] <= 721 and p["dex"] not in seen]
            if missing:
                self.iss.add(f, s.line, "warn", "MISSING_FIELD", "%d especies sin línea en [SPECIAL_OBTAINABILITY] (p. ej. #%s)" %
                             (len(missing), ", #".join("%03d" % d for d in missing[:5])))
        for dex, lst in self.w.obtain.items():
            p = pokes.get(dex)
            if p is not None:
                p["obtain"] = lst

    # ------------------------------------------------------ objetos por ubicación
    def do_location_items(self):
        f = F_ITEMS
        secs = self.sections(f)
        seen = {}
        for s in secs:
            try:
                key, _z = self.loc(s.key, f, s.line, text=s.raw_header)
                if not key:
                    continue
                if key in seen:
                    self.iss.add(f, s.line, "warn", "DUPLICATE_KEY", "Ubicación %s duplicada (primera en la línea %d); se fusionan las filas" % (key, seen[key]))
                seen[key] = s.line
                L = self.loc_by_key.get(key)
                for it in s.items:
                    if not re.match(r"^item\d+$", it.key):
                        if it.key not in ("name", "note", "comment"):
                            self.iss.add(f, it.line, "info", "UNKNOWN_KEY", "Clave «%s» desconocida en [%s]; se ignora" % (it.raw_key, s.key))
                        continue
                    p = split_csv_max(it.value, 4)
                    if not p[0].strip():
                        self.iss.add(f, it.line, "error", "MISSING_FIELD", "%s sin ITEM_ID en [%s]; se omite" % (it.raw_key, s.key))
                        continue
                    sym = self.item(p[0], f, it.line, context="[%s]" % s.key)
                    if not sym:
                        continue
                    qty = self.int_(f, it.line, "cantidad de %s en [%s]" % (it.raw_key, s.key), p[1], default=1, minimum=1) if p[1].strip() else 1
                    method = p[2].strip().upper()
                    if method and method not in ITEM_METHODS:
                        self.iss.add(f, it.line, "warn", "BAD_LINE", "Método de obtención de objeto «%s» desconocido (se esperan B,H,C,N,E,J,P,S)" % p[2].strip())
                    entry = {"loc": key, "qty": qty, "method": method, "zone": p[3].strip(), "note": p[4].strip()}
                    ci = self.core.item_by_sym.get(sym)
                    if ci is not None:
                        ci["where"].append(entry)
                    if L is not None:
                        L["items"].append(dict(entry, item=sym))
            except Exception:
                self.iss.add(f, getattr(s, "line", 0), "warn", "BAD_LINE", "No se pudo interpretar la sección [%s]" % getattr(s, "key", "?"))

    # --------------------------------------------------------------------- tiendas
    def do_shops(self):
        f = F_SHOPS
        secs = self.sections(f, known=lambda sec: MISSION_KNOWN if sec.ukey == "PIA_MISSIONS" else SHOP_KNOWN)
        shops, missions = [], []
        mission_info = {}
        for s in secs:
            try:
                u = s.ukey
                if u == "PIA_MISSIONS":
                    for it in s.items:
                        mi = re.match(r"^missioninfo(\d+)$", it.key)
                        if mi:
                            pi = split_csv_max(it.value, 3)
                            iloc = None
                            if pi[2].strip():
                                iloc, _z = self.loc(pi[2], f, it.line)
                            mission_info[int(mi.group(1))] = {"act": pi[0].strip().upper() or None, "kind": pi[1].strip() or None,
                                                              "loc": iloc, "requirement": pi[3].strip()}
                            continue
                        m = re.match(r"^mission(\d+)$", it.key)
                        if not m:
                            continue
                        p = split_csv_max(it.value, 4)
                        sym = self.item(p[1], f, it.line, context="misión %s" % m.group(1)) if p[1].strip() else None
                        if not p[1].strip():
                            self.iss.add(f, it.line, "error", "MISSING_FIELD", "%s sin ITEM_ID; se omite" % it.raw_key)
                            continue
                        if not sym:
                            continue
                        missions.append({"n": int(m.group(1)),
                                         "species": self.int_(f, it.line, "especies capturadas de %s" % it.raw_key, p[0], default=0),
                                         "item": sym, "qty": self.int_(f, it.line, "cantidad de %s" % it.raw_key, p[2], default=1) if p[2].strip() else 1,
                                         "title": p[3].strip(), "note": p[4].strip()})
                    continue
                shop = {"key": s.key.strip().upper().replace(" ", "_"), "name": s.last("Name").strip(), "medals": None,
                        "cumulative": s.last("Cumulative").strip().lower() in YES, "location": None,
                        "description": " ".join(s.all("Description")).strip(), "requirement": " ".join(s.all("Requirement")).strip(),
                        "items": [], "stock": [], "line": s.line}
                mm = re.match(r"^MART_(\d+)_MEDALS$", shop["key"])
                if mm:
                    shop["medals"] = int(mm.group(1))
                    if not s.has("Cumulative"):
                        shop["cumulative"] = True
                if s.last("Medals").strip():
                    v = self.int_(f, s.line_of("Medals"), "Medals de [%s]" % s.key, s.last("Medals"))
                    if v is not None:
                        shop["medals"] = v
                if not shop["name"]:
                    shop["name"] = ("Poké Mart (%s medallas)" % shop["medals"]) if shop["medals"] is not None else s.key
                    self.iss.add(f, s.line, "warn", "MISSING_FIELD", "Falta Name en [%s]" % s.key)
                if s.last("Location").strip():
                    shop["location"], _z = self.loc(s.last("Location"), f, s.line_of("Location"))
                shop["locations"] = []
                for tok in split_list(";".join(s.all("Locations"))):
                    k, _z = self.loc(tok, f, s.line_of("Locations"))
                    if k and k not in shop["locations"]:
                        shop["locations"].append(k)
                if shop["location"] and shop["location"] not in shop["locations"] and not mm:
                    shop["locations"].append(shop["location"])
                shop["uniqueItems"] = []
                for tok in split_list(";".join(s.all("UniqueItems"))):
                    u = self.item(tok, f, s.line_of("UniqueItems"), context="UniqueItems de [%s]" % s.key)
                    if u and u not in shop["uniqueItems"]:
                        shop["uniqueItems"].append(u)
                notes = {}
                for it in s.all_items("ItemNote"):
                    pn = split_csv_max(it.value, 1)
                    nsym = self.item(pn[0], f, it.line, context="ItemNote de [%s]" % s.key) if pn[0].strip() else None
                    if nsym:
                        notes[nsym] = pn[1].strip()
                shop["itemNotes"] = notes
                shop.update(extra_fields(s, SHOP_KNOWN[0], shop, self.iss, f))
                seen_items = set()
                for it in s.items:
                    if not re.match(r"^item\d+$", it.key):
                        continue
                    p = split_csv_max(it.value, 1)
                    if not p[0].strip():
                        self.iss.add(f, it.line, "error", "MISSING_FIELD", "%s sin ITEM_ID en [%s]; se omite" % (it.raw_key, s.key))
                        continue
                    sym = self.item(p[0], f, it.line, context="[%s]" % s.key)
                    if not sym:
                        continue
                    ov = self.int_(f, it.line, "precio de %s en [%s]" % (it.raw_key, s.key), p[1], default=None, minimum=0) if p[1].strip() else None
                    ci = self.core.item_by_sym.get(sym)
                    price = ov if ov is not None else (ci["price"] if ci else 0)
                    if sym in seen_items:
                        self.iss.add(f, it.line, "warn", "DUPLICATE_KEY", "%s aparece más de una vez en [%s]" % (sym, s.key))
                        continue
                    seen_items.add(sym)
                    shop["items"].append({"item": sym, "price": price, "override": ov is not None, "note": notes.get(sym), "unique": sym in shop["uniqueItems"]})
                shops.append(shop)
            except Exception:
                self.iss.add(f, getattr(s, "line", 0), "warn", "BAD_LINE", "No se pudo interpretar la sección [%s]" % getattr(s, "key", "?"))
        # stock acumulado de las marts
        marts = sorted([s for s in shops if s["medals"] is not None and re.match(r"^MART_\d+_MEDALS$", s["key"])], key=lambda x: x["medals"])
        for sh in shops:
            if sh in marts and sh["cumulative"]:
                acc = {}
                for m in marts:
                    if m["medals"] > sh["medals"]:
                        break
                    for e in m["items"]:
                        acc[e["item"]] = {"item": e["item"], "price": e["price"], "override": e["override"], "note": e.get("note"), "unique": e.get("unique", False)}
                sh["stock"] = list(acc.values())
            else:
                sh["stock"] = [dict(e) for e in sh["items"]]
        shops.sort(key=lambda x: (0 if x["medals"] is not None and x["key"].startswith("MART_") else 1, x["medals"] if x["medals"] is not None else 99, x["key"]))
        missions.sort(key=lambda x: x["n"])
        for mi in missions:
            inf = mission_info.get(mi["n"])
            if inf:
                mi.update(inf)
        self.w.shops = shops
        self.w.missions = missions

    # ------------------------------------------------------------------ changelog
    def do_changelog(self):
        f = F_LOG

        def known(sec):
            u = sec.ukey
            if u == "META":
                return None
            if u == "PRUNED_ITEMS":
                return CL_KNOWN["PRUNED_ITEMS"]
            return CL_KNOWN.get(u.split("_", 1)[0])

        secs = self.sections(f, known=known)
        pruned = {}
        for s in secs:
            if s.ukey == "PRUNED_ITEMS":
                for it in s.items:
                    if re.match(r"^item\d+$", it.key):
                        pp = split_csv_max(it.value, 1)
                        if pp[0].strip():
                            pruned[pp[0].strip().upper()] = pp[1].strip()
        bl = self.baseline
        for s in secs:
            try:
                u = s.ukey
                if u == "PRUNED_ITEMS":
                    for it in s.items:
                        if not re.match(r"^item\d+$", it.key):
                            continue
                        pp = split_csv_max(it.value, 1)
                        if pp[0].strip():
                            self.w.pruned_items.append({"sym": pp[0].strip(), "name": pp[1].strip()})
                    continue
                if u == "META":
                    for it in s.items:
                        self.w.meta_log[it.raw_key] = it.value
                    continue
                m = re.match(r"^POKEMON_(\d+)$", u)
                if m:
                    dex = int(m.group(1))
                    if dex not in self.core.by_dex:
                        self.iss.add(f, s.line, "warn", "UNKNOWN_SPECIES", "Especie #%d desconocida en el changelog; se omite" % dex)
                        continue
                    self.w.changelog["pokemon"][dex] = {"role": s.last("Role").strip() or None, "notes": [v for v in s.all("Note") if v.strip()]}
                    continue
                m = re.match(r"^(ABILITY|MOVE|ITEM)_(.+)$", u)
                if m:
                    kind, sym = m.group(1), m.group(2)
                    lk = {"ABILITY": self.core.La, "MOVE": self.core.Lm, "ITEM": self.core.Li}[kind]
                    if lk.lookup(sym)[0] is None:
                        # entidad ya inexistente (objeto podado, etc.): la nota se guarda aparte, sin aviso
                        in_base = bl is not None and sym in {"ABILITY": bl.abilities, "MOVE": bl.moves, "ITEM": bl.items}[kind]
                        if sym.upper() in pruned or in_base:
                            if kind == "ITEM":
                                self.w.pruned_notes[sym.upper()] = [v for v in s.all("Note") if v.strip()]
                            else:
                                self.iss.add(f, s.line, "info", "UNKNOWN_" + kind, "%s «%s» ya no existe en el PBS actual; la nota se conserva solo en el changelog" % (kind.capitalize(), sym), text=s.raw_header)
                            continue
                    code = {"ABILITY": "UNKNOWN_ABILITY", "MOVE": "UNKNOWN_MOVE", "ITEM": "UNKNOWN_ITEM"}[kind]
                    rs = self.res.ref(lk, sym, f, s.line, code, text=s.raw_header, severity="warn")
                    if not rs:
                        continue
                    status = s.last("Status").strip()
                    if status:
                        sl = Lookup("estado", "estado")
                        for st in ("Reworked", "Buffed", "Kept", "Untouched"):
                            sl.add(st)
                        status = self.res.ref(sl, status, f, s.line_of("Status"), "BAD_LINE", context="[%s]" % s.key) or None
                    self.w.changelog[{"ABILITY": "abilities", "MOVE": "moves", "ITEM": "items"}[kind]][rs] = {
                        "status": status, "notes": [v for v in s.all("Note") if v.strip()]}
                    continue
                self.iss.add(f, s.line, "info", "UNKNOWN_KEY", "Sección [%s] desconocida en el changelog; se ignora" % s.key, text=s.raw_header)
            except Exception:
                self.iss.add(f, getattr(s, "line", 0), "warn", "BAD_LINE", "No se pudo interpretar la sección [%s]" % getattr(s, "key", "?"))

    # ----------------------------------------------------------------- enlaces
    def link(self):
        w = self.w
        for pi in w.pruned_items:
            pi["notes"] = w.pruned_notes.get(pi["sym"].upper(), [])
            pi["inLive"] = pi["sym"] in self.core.item_by_sym
        # misiones -> objetos
        for m in w.missions:
            ci = self.core.item_by_sym.get(m["item"])
            if ci is not None and m["n"] not in ci["missions"]:
                ci["missions"].append(m["n"])
        # tiendas -> objetos
        for sh in w.shops:
            for e in sh["items"]:
                ci = self.core.item_by_sym.get(e["item"])
                if ci is not None:
                    ci["shops"].append({"shop": sh["key"], "price": e["price"], "cumulative": bool(sh["cumulative"]), "medals": sh["medals"]})
            if sh["location"]:
                L = self.loc_by_key.get(sh["location"])
                if L is not None and sh["key"] not in L["shops"]:
                    L["shops"].append(sh["key"])
            if re.match(r"^MART_\d+_MEDALS$", sh["key"]):
                for lk in sh.get("locations", []):
                    L = self.loc_by_key.get(lk)
                    if L is not None:
                        L.setdefault("marts", [])
                        if sh["key"] not in L["marts"]:
                            L["marts"].append(sh["key"])
        # progresión / crónica -> ubicaciones
        for st in w.progression:
            L = self.loc_by_key.get(st["loc"]) if st["loc"] else None
            if L is not None and st["step"] not in L["steps"]:
                L["steps"].append(st["step"])
        for ch in w.story:
            L = self.loc_by_key.get(ch["loc"]) if ch["loc"] else None
            if L is not None and ch["key"] not in L["chapters"]:
                L["chapters"].append(ch["key"])
        # personajes -> ubicaciones
        char_by_key = {c["key"]: c for c in w.characters}
        for L in w.locations:
            keys = self.chars_from_names(L["characters"])
            for c in w.characters:
                if (L["key"] in c.get("locations", []) or c.get("firstLocation") == L["key"]) and c["key"] not in keys:
                    keys.append(c["key"])
            L["charKeys"] = keys
        # orden de progresión (si faltan datos, se deduce del primer paso)
        first_step = {}
        for st in w.progression:
            if st["loc"] and st["loc"] not in first_step:
                first_step[st["loc"]] = st["step"]
        for L in w.locations:
            if L["order"] is None and L["key"] in first_step:
                L["order"] = first_step[L["key"]]
            if L["act"] is None:
                for st in w.progression:
                    if st["loc"] == L["key"] and st["act"]:
                        L["act"] = st["act"]
                        break
        w.locations.sort(key=lambda x: (x["order"] if x["order"] is not None else 9999, self.canon_by_key.get(x["key"], {}).get("idx", 999)))


def norm_spaces(s):
    return re.sub(r"\s+", " ", s or "").strip()
