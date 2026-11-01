"""Orquestación: lee los archivos PBS (con caché por mtime+tamaño), construye el modelo del contrato
(SPEC §4.1) con todas las referencias cruzadas resueltas, los diffs en vivo y la salud del PBS."""
import copy
import datetime
import hashlib
import os
import re
import time
import traceback

from . import ROOT, SCHEMA, __version__, assets as assets_mod, baseline as bl_mod, core as core_mod, pbs, world as world_mod
from .fuzzy import Resolver, norm
from .ini import TextFile, read_textfile
from .issues import Issues

REQUIRED = ["pokemon.txt", "moves.txt", "abilities.txt", "items.txt", "types.txt", "tm.txt"]
OPTIONAL = ["berryplants.txt", "encounters.txt", "townmap.txt"]
BATTLE_FILES = ["btpokemon.txt", "fancycuppm.txt", "fancycupsinglepm.txt", "littlecuppm.txt", "pikacuppm.txt", "pokecuppm.txt"]
REM_FILES = world_mod.REM_FILES
KNOWN_FILES = REQUIRED + OPTIONAL + BATTLE_FILES + REM_FILES
CORE_BASELINE_FILES = ["types.txt", "abilities.txt", "moves.txt", "items.txt", "pokemon.txt", "tm.txt", "berryplants.txt"]


def now_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _is_pbs_txt(name):
    return name.lower().endswith(".txt") and not name.startswith("~$") and not name.startswith(".")


def list_txt(pbs_dir):
    """{nombre: (mtime_ns, size)} de los .txt de la carpeta (barato)."""
    out = {}
    try:
        with os.scandir(pbs_dir) as it:
            for e in it:
                try:
                    if e.is_file() and _is_pbs_txt(e.name):
                        st = e.stat()
                        out[e.name] = (st.st_mtime_ns, st.st_size)
                except OSError:
                    continue
    except OSError:
        pass
    return out


class FileStore:
    """Lee archivos con caché por (mtime, tamaño) y conserva la última lectura válida si el archivo desaparece."""

    def __init__(self, directory):
        self.dir = directory
        self.cache = {}
        self.sig = {}

    def invalidate(self):
        self.cache.clear()
        self.sig.clear()

    def read(self, name):
        path = os.path.join(self.dir, name)
        try:
            st = os.stat(path)
        except OSError:
            st = None
        cached = self.cache.get(name)
        if st is None:
            if cached is not None and cached.ok:
                c = copy.copy(cached)
                c.stale = True
                c.exists = False
                return c
            return TextFile(name, path)
        key = (st.st_mtime_ns, st.st_size)
        if cached is not None and self.sig.get(name) == key and not cached.stale:
            return cached
        tf = read_textfile(name, path)
        if tf.ok:
            self.cache[name] = tf
            self.sig[name] = key
            return tf
        if cached is not None and cached.ok:
            c = copy.copy(cached)
            c.stale = True
            c.exists = tf.exists
            c.size, c.mtime = tf.size, tf.mtime
            return c
        return tf


class ModelBuilder:
    def __init__(self, pbs_dir, root=ROOT, backup_dir=None):
        self.pbs_dir = os.path.abspath(pbs_dir)
        self.root = root
        self.store = FileStore(self.pbs_dir)
        self.backup_dir = backup_dir if backup_dir is not None else os.path.join(root, "PBS_backup_original")
        self.backup_store = FileStore(self.backup_dir)
        self._backup_cache = None      # (firma, Baseline)
        self.graphics_dir = os.path.join(root, "Graphics")
        self._assets_cache = None      # (firma, assets dict)

    # ------------------------------------------------------------------ firma barata
    def signature(self):
        """-> (version, mtimes{nombre: mtime}) sin leer contenido."""
        files = list_txt(self.pbs_dir)
        h = hashlib.sha1()
        for n in sorted(files):
            h.update(("%s|%d|%d\n" % (n, files[n][0], files[n][1])).encode("utf-8", "replace"))
        h.update(repr(assets_mod.dir_stamp(self.graphics_dir)).encode())
        bk = list_txt(self.backup_dir) if (files.get("rem_vanilla_baseline.txt") is None and os.path.realpath(self.backup_dir) != os.path.realpath(self.pbs_dir)) else {}
        for n in sorted(bk):
            h.update(("B%s|%d|%d\n" % (n, bk[n][0], bk[n][1])).encode("utf-8", "replace"))
        h.update(("v%s" % __version__).encode())
        return h.hexdigest()[:12], {n: files[n][0] / 1e9 for n in sorted(files)}

    # ----------------------------------------------------------------------- assets
    def get_assets(self, n_types):
        stamp = (assets_mod.dir_stamp(self.graphics_dir), n_types)
        if self._assets_cache and self._assets_cache[0] == stamp:
            return copy.deepcopy(self._assets_cache[1])
        a = assets_mod.scan_assets(self.graphics_dir, n_types)
        self._assets_cache = (stamp, a)
        return copy.deepcopy(a)

    # --------------------------------------------------------------------- baseline
    def make_baseline(self, files, iss):
        """Baseline preferente de rem_vanilla_baseline.txt; si no, del PBS original (si existe)."""
        tf = files.get("rem_vanilla_baseline.txt")
        if tf is not None and tf.ok:
            try:
                b = bl_mod.parse_baseline_file(tf, iss)
                if b:
                    return b
                iss.add("rem_vanilla_baseline.txt", 0, "warn", "MISSING_FIELD", "El baseline no contiene ninguna sección POKEMON_/MOVE_/ABILITY_/ITEM_ reconocible")
            except Exception as e:
                iss.add("rem_vanilla_baseline.txt", 0, "error", "INTERNAL", "Error interno leyendo el baseline (%s)" % e.__class__.__name__)
        if os.path.isdir(self.backup_dir) and os.path.realpath(self.backup_dir) != os.path.realpath(self.pbs_dir):
            try:
                bfiles = {n: self.backup_store.read(n) for n in CORE_BASELINE_FILES}
                sig = tuple(sorted((n, f.mtime_ns, f.size) for n, f in bfiles.items()))
                if self._backup_cache and self._backup_cache[0] == sig:
                    return self._backup_cache[1]
                if bfiles["pokemon.txt"].ok:
                    quiet = Issues(silent=True)
                    c = core_mod.build_core(bfiles, quiet)
                    b = bl_mod.from_core(c, "PBS_backup_original")
                    self._backup_cache = (sig, b)
                    iss.add("rem_vanilla_baseline.txt", 0, "info", "FILE_MISSING",
                            "No hay rem_vanilla_baseline.txt utilizable: los diffs se calculan contra PBS_backup_original/")
                    return b
            except Exception as e:
                iss.add("rem_vanilla_baseline.txt", 0, "warn", "INTERNAL", "No se pudo construir el baseline alternativo (%s)" % e.__class__.__name__)
        return bl_mod.Baseline(None)

    # ------------------------------------------------------------------ construcción
    def build(self):
        t0 = time.time()
        iss = Issues()
        files = {}
        names = list(KNOWN_FILES)
        disk = list_txt(self.pbs_dir)
        extras = sorted(n for n in disk if n not in names)
        for n in names + extras:
            tf = self.store.read(n)
            files[n] = tf
            if tf.exists or tf.ok:
                iss.register_lines(n, tf.lines)
        dir_ok = os.path.isdir(self.pbs_dir)
        if not dir_ok:
            iss.add("PBS", 0, "error", "FILE_MISSING", "No se puede leer la carpeta PBS (%s)" % self.pbs_dir)
        self.file_issues(files, iss)
        baseline = self.make_baseline(files, iss)
        bl_core = {"pokemon": {d: {"types": p["types"], "stats": p["stats"]} for d, p in baseline.pokemon.items()},
                   "moves": {s: {"type": m.get("type"), "category": m.get("category")} for s, m in baseline.moves.items()}}
        core = core_mod.build_core(files, iss, bl_core)
        w = world_mod.Builder(files, iss, core, self.root, baseline).run()
        for fn in (self.check_battle_files, self.check_engine_encounters):
            try:
                fn(files, iss, core)
            except Exception as e:  # pragma: no cover
                iss.add(fn.__name__, 0, "warn", "INTERNAL", "Error interno en %s (%s)" % (fn.__name__, e.__class__.__name__))
        model = self.assemble(files, iss, core, w, baseline, disk)
        model["meta"]["buildMs"] = int((time.time() - t0) * 1000)
        return model

    # -------------------------------------------------------------- avisos de archivo
    def file_issues(self, files, iss):
        for name in KNOWN_FILES:
            tf = files[name]
            required = name in REQUIRED
            rem = name in REM_FILES
            if tf.stale:
                iss.add(name, 0, "error", "FILE_MISSING",
                        "El archivo %s %s: se usa la última copia leída en memoria" % (name, "está vacío o ilegible" if tf.exists else "ha desaparecido"),
                        suggestion="Restaura o recrea PBS/%s" % name)
                continue
            if not tf.exists:
                sev = "error" if required else ("warn" if rem else "info")
                msg = ("Archivo obligatorio ausente: PBS/%s; el modelo continúa con lo disponible" % name) if required else \
                      ("Archivo ausente: PBS/%s (aún no generado); sus secciones del Codex quedan vacías" % name if rem else
                       "Archivo opcional ausente: PBS/%s" % name)
                iss.add(name, 0, sev, "FILE_MISSING", msg)
            elif tf.empty:
                sev = "error" if required else ("warn" if rem else "info")
                iss.add(name, 0, sev, "FILE_MISSING", "El archivo %s está vacío" % name)
            else:
                for ln, sev, code, msg, sug in tf.enc_issues:
                    iss.add(name, ln, sev, code, msg, suggestion=sug)
        for name, tf in files.items():
            if name not in KNOWN_FILES and tf.ok:
                for ln, sev, code, msg, sug in tf.enc_issues:
                    if sev in ("error", "warn"):
                        iss.add(name, ln, sev, code, msg, suggestion=sug)

    def check_battle_files(self, files, iss, core):
        res = Resolver(iss)
        for name in BATTLE_FILES:
            tf = files.get(name)
            if tf is None or not tf.ok:
                continue
            for r in pbs.parse_battle_pokemon(tf, iss):
                if r["species"]:
                    res.ref(core.Ls, r["species"], name, r["line"], "UNKNOWN_SPECIES")
                if r["item"]:
                    res.ref(core.Li, r["item"], name, r["line"], "UNKNOWN_ITEM")
                for m in r["moves"]:
                    res.ref(core.Lm, m, name, r["line"], "UNKNOWN_MOVE")

    def check_engine_encounters(self, files, iss, core):
        tf = files.get("encounters.txt")
        if tf is None or not tf.ok:
            return
        res = Resolver(iss)
        maps = pbs.parse_official_encounters(tf, iss)
        for m in maps:
            for ctype, rows in m["tables"].items():
                for ln, sp, lo, hi in rows:
                    res.ref(core.Ls, sp, "encounters.txt", ln, "UNKNOWN_SPECIES")
                    for v in (lo, hi):
                        if v is not None and not (1 <= v <= 100):
                            iss.add("encounters.txt", ln, "error", "BAD_NUMBER", "Nivel fuera de rango (1-100): %s" % v)
        self._engine_maps = len(maps)

    # ------------------------------------------------------------------- ensamblado
    def assemble(self, files, iss, core, w, baseline, disk):
        # ---- MT ------------------------------------------------------------------
        sections = {s["move"]: s for s in core.tm_sections}
        tms = []
        moves_by = core.move_by_sym
        pokes = core.by_dex
        tm_items = [i for i in core.items if i["tm"] is not None and i["move"]]
        tm_items.sort(key=lambda i: (i["tm"], i["id"]))
        used_sections = set()
        seen_num = {}
        for it in tm_items:
            n = it["tm"]
            if n in seen_num:
                iss.add("items.txt", it["line"], "error", "DUPLICATE_KEY", "MT %02d repetida (%s y %s)" % (n, seen_num[n], it["sym"]))
                continue
            seen_num[n] = it["sym"]
            sec = sections.get(it["move"])
            if sec is None:
                if files["tm.txt"].ok:
                    iss.add("tm.txt", 0, "warn", "MISSING_FIELD", "tm.txt no tiene sección [%s] para %s" % (it["move"], it["sym"]),
                            suggestion="Añade [%s] con su lista de especies" % it["move"])
                learners = []
            else:
                learners = list(sec["dex"])
                used_sections.add(it["move"])
            m = moves_by.get(it["move"])
            if m is not None and m["tm"] is None:
                m["tm"] = n
            tms.append({"number": n, "sym": it["sym"], "move": it["move"], "moveName": m["name"] if m else it["move"], "name": it["name"],
                        "price": it["price"], "learners": learners, "where": it["where"], "missions": it["missions"], "itemId": it["id"]})
        orphan = [s for s in sections if s not in used_sections]
        if orphan and files["tm.txt"].ok:
            iss.add("tm.txt", 0, "info", "UNKNOWN_MOVE",
                    "%d secciones de tm.txt no tienen una MT asociada en items.txt (p. ej. %s)" % (len(orphan), ", ".join(orphan[:4])))
        for s in core.tm_sections:
            m = moves_by.get(s["move"])
            if m is not None:
                m["tmLearners"] = list(s["dex"])
        tm_by_dex = {}
        for t in tms:
            for d in t["learners"]:
                tm_by_dex.setdefault(d, []).append(t["number"])
        for p in core.pokemon:
            p["tms"] = sorted(set(tm_by_dex.get(p["dex"], [])))
        # ---- cruces de movimientos y habilidades ----------------------------------
        holders = {}
        for p in core.pokemon:
            for mv in p["learnset"]:
                m = moves_by.get(mv["move"])
                if m is not None:
                    m["learnedBy"].append({"dex": p["dex"], "lv": mv["lv"]})
            for mv in p["eggMoves"]:
                m = moves_by.get(mv)
                if m is not None and p["dex"] not in m["eggBy"]:
                    m["eggBy"].append(p["dex"])
            for a in list(p["abilities"]) + list(p["hiddenAbilities"]):
                holders.setdefault(a, []).append(p["dex"])
            for rarity, it in (p.get("wildItems") or {}).items():
                ci = core.item_by_sym.get(it) if it else None
                if ci is not None:
                    ci["heldBy"].append({"dex": p["dex"], "rarity": rarity})
        for m in core.moves:
            m["learnedBy"].sort(key=lambda x: (x["dex"], x["lv"]))
        abilities = core.abilities
        for a in abilities:
            a["holders"] = sorted(set(holders.get(a["sym"], [])))
        # ---- bayas ------------------------------------------------------------------
        for b in core.berries:
            ci = core.item_by_sym.get(b["item"])
            if ci is not None:
                ci["berry"] = {k: v for k, v in b.items() if k != "item"}
        # ---- activos gráficos -------------------------------------------------------
        types = core.types
        assets = self.get_assets(len([t for t in types]))
        icon_set = set(assets["itemIcons"])
        for it in core.items:
            fn = "item%03d.png" % it["id"]
            it["icon"] = ("Icons/" + fn) if fn in icon_set else None
        icons, battlers = set(assets["icons"]), set(assets["battlers"])
        missing = []
        for p in core.pokemon:
            if p["dex"] not in icons:
                missing.append("icon:%d" % p["dex"])
            if p["dex"] not in battlers:
                missing.append("battler:%d" % p["dex"])
        for it in core.items:
            if it["icon"] is None:
                missing.append("itemIcon:%d:%s" % (it["id"], it["sym"]))
        assets["missing"] = missing
        for t in types:
            pass
        # ---- changelog -------------------------------------------------------------
        cl = w.changelog
        for p in core.pokemon:
            e = cl["pokemon"].get(p["dex"])
            if e:
                p["role"] = e["role"]
                p["notes"] = e["notes"]
        # ---- baseline y diffs -------------------------------------------------------
        self.apply_baseline(core, w, baseline, assets)
        self.check_vs_baseline(core, w, baseline, iss)
        for m in core.moves:
            m["tmVanillaCount"] = baseline.tm_counts.get(m["sym"])
        for t in tms:
            t["vanillaLearners"] = baseline.tm_counts.get(t["move"])
        for a in abilities:
            e = cl["abilities"].get(a["sym"])
            a["status"] = e["status"] if e else None
            a["note"] = " ".join(e["notes"]) if e and e["notes"] else None
            a["notes"] = e["notes"] if e else []
            if a.get("baseline") is not None:
                a["changed"] = a["baseline"]["description"] != a["description"] or a["status"] in ("Reworked", "Buffed")
            else:
                a["changed"] = a["status"] in ("Reworked", "Buffed")
        for m in core.moves:
            e = cl["moves"].get(m["sym"])
            m["note"] = " ".join(e["notes"]) if e and e["notes"] else None
        for it in core.items:
            e = cl["items"].get(it["sym"])
            it["note"] = " ".join(e["notes"]) if e and e["notes"] else None
        # ---- tipos: tabla de efectividad -------------------------------------------
        chart = {}
        for d in types:
            for a in d["weaknesses"]:
                chart.setdefault(a, {})[d["sym"]] = 2
            for a in d["resistances"]:
                chart.setdefault(a, {})[d["sym"]] = 0.5
            for a in d["immunities"]:
                chart.setdefault(a, {})[d["sym"]] = 0
        # ---- limpieza de campos internos ----------------------------------------------
        for coll in (core.pokemon, core.moves, core.items, abilities):
            for e in coll:
                e.pop("line", None)
        shops = w.shops
        for s in shops:
            s.pop("line", None)
        for d in (w.progression, w.story):
            for e in d:
                e.pop("line", None)
        if w.prelude:
            w.prelude.pop("line", None)
        for c in w.characters:
            c.pop("line", None)
        chapters = [c for c in w.story if c["key"].startswith("CHAPTER_")]
        counts = {"pokemon": len(core.pokemon), "moves": len(core.moves), "abilities": len(abilities), "items": len(core.items),
                  "tms": len(tms), "locations": len(w.locations), "wildSlots": w.wild_slots - w.fish_slots, "fishSlots": w.fish_slots,
                  "characters": len(w.characters), "chapters": len(chapters), "steps": len(w.progression), "shops": len(shops),
                  "missions": len(w.missions), "types": len(types), "berries": len(core.berries)}
        # ---- archivos y salud -------------------------------------------------------
        file_infos = self.file_infos(files, iss, disk)
        errors, warns, infos = iss.total("error"), iss.total("warn"), iss.total("info")
        status = "error" if errors else ("warn" if warns else "ok")
        warnings = iss.sorted_items()
        version, _ = self.signature()
        health = {"status": status, "errors": errors, "warnings": warns, "infos": infos}
        meta = {"source": "live", "generatedAt": now_iso(), "version": version, "health": health, "counts": counts,
                "schema": SCHEMA, "codexVersion": __version__, "pbsDir": self.pbs_dir,
                "baselineSource": baseline.source, "hasRem": {n: bool(files[n].ok) for n in REM_FILES},
                "engineMaps": getattr(self, "_engine_maps", 0)}
        model = {"meta": meta, "types": types, "chart": chart, "pokemon": core.pokemon, "moves": core.moves, "abilities": abilities,
                 "items": core.items, "tms": tms, "locations": w.locations, "shops": shops, "missions": w.missions,
                 "progression": w.progression, "characters": w.characters, "story": chapters, "prelude": w.prelude,
                 "ledger": w.ledger, "ledgerMeta": w.ledger_meta, "prunedItems": w.pruned_items, "changelogMeta": w.meta_log, "assets": assets, "berryPlants": core.berries, "warnings": warnings, "files": file_infos}
        return model

    def check_vs_baseline(self, core, w, baseline, iss):
        """Símbolos del baseline que ya no están en el PBS vivo y no constan como podados: probable renombrado por error."""
        pruned = {p["sym"].upper() for p in w.pruned_items}
        for kind, fname, base, live, lk in (("habilidad", "abilities.txt", baseline.abilities, core.ability_by_sym, core.La),
                                            ("movimiento", "moves.txt", baseline.moves, core.move_by_sym, core.Lm),
                                            ("objeto", "items.txt", baseline.items, core.item_by_sym, core.Li)):
            if not base or not live:
                continue
            gone = [x for x in base if x not in live and x.upper() not in pruned]
            extra = [x for x in live if x not in base]
            if not gone or len(gone) > 12:
                continue
            for sym in gone:
                cand = difflib_best(sym, extra)
                line = live[cand]["line"] if cand else 0
                iss.add(fname, line, "warn", "UNKNOWN_" + {"habilidad": "ABILITY", "movimiento": "MOVE", "objeto": "ITEM"}[kind],
                        "El %s vanilla «%s» ya no existe en %s%s" % (kind, sym, fname, (": ¿se renombró a «%s»?" % cand) if cand else ""),
                        suggestion=sym if cand else None, applied=False)

    def apply_baseline(self, core, w, baseline, assets):
        syms_dex = dict(core.sym_dex)
        names = core_mod._Names(core)

        class _N:
            def item(s_, x):
                b = baseline.items.get(x)
                return names.item(x) if x in core.item_by_sym else (b["name"] if b else (x or "un objeto"))

            def move(s_, x):
                b = baseline.moves.get(x)
                return names.move(x) if x in core.move_by_sym else (b["name"] if b else (x or "un movimiento"))

            species = staticmethod(names.species)
            type = staticmethod(names.type)

        nm = _N()
        # Pokémon
        have = bool(baseline.pokemon)
        for p in core.pokemon:
            bp = baseline.pokemon.get(p["dex"])
            if bp is not None:
                p["baseline"] = bl_mod.pokemon_baseline_view(bp, lambda mth, par: core_mod.evo_text(mth, par, nm), syms_dex)
                for e, ev in zip(p["baseline"]["evolutions"], bp["evos"]):
                    ptype = pbs.EVOPARAM_BY_NAME.get(e["method"], 0)
                    if ptype == 2:
                        e["item"] = e["param"]
                p["diff"] = bl_mod.diff_pokemon(p, bp)
            else:
                p["diff"] = bl_mod.diff_pokemon(p, None)
                if have:
                    p["diff"]["changed"] = True
                    p["diff"]["new"] = True
        # Movimientos
        for m in core.moves:
            b = baseline.moves.get(m["sym"])
            if b is not None:
                m["baseline"] = {k: b.get(k) for k in bl_mod.MOVE_FIELDS}
                fields = bl_mod.diff_fields(m, b, bl_mod.MOVE_FIELDS)
                m["diff"] = {"changed": bool(fields), "fields": fields}
            else:
                m["diff"] = {"changed": bool(baseline.has_moves), "fields": [], "new": bool(baseline.has_moves)}
        # Habilidades
        for a in core.abilities:
            b = baseline.abilities.get(a["sym"])
            a["baseline"] = {"description": b["description"], "name": b["name"]} if b is not None else None
        # Objetos
        for it in core.items:
            b = baseline.items.get(it["sym"])
            if b is not None:
                it["baseline"] = {k: b.get(k) for k in bl_mod.ITEM_FIELDS}
                fields = bl_mod.diff_fields(it, b, bl_mod.ITEM_FIELDS)
                it["diff"] = {"changed": bool(fields), "fields": fields}
                it["isNew"] = False
            else:
                is_new = bool(baseline.has_items) or it["id"] >= 674
                it["isNew"] = is_new
                it["diff"] = {"changed": is_new, "fields": [], "new": is_new}

    def file_infos(self, files, iss, disk):
        out = []
        order = KNOWN_FILES + sorted(n for n in files if n not in KNOWN_FILES)
        for name in order:
            tf = files.get(name)
            if tf is None:
                continue
            if name not in KNOWN_FILES and not tf.exists:
                continue
            e, w_, i_ = iss.file_counts(name)
            out.append({"name": name, "exists": bool(tf.exists), "size": tf.size, "mtime": tf.mtime, "lines": tf.n_lines,
                        "errors": e, "warnings": w_, "infos": i_, "stale": bool(tf.stale), "empty": bool(tf.empty and tf.exists),
                        "required": name in REQUIRED, "kind": "rem" if name in REM_FILES else ("oficial" if name in KNOWN_FILES else "otro")})
        return out


def difflib_best(sym, cands):
    import difflib
    r = difflib.get_close_matches(sym, cands, n=1, cutoff=0.75)
    return r[0] if r else None
