"""Caché del modelo: reconstrucción automática al cambiar cualquier PBS/*.txt, bundle de respaldo, JSON/gzip precomputados."""
import gzip
import json
import os
import sys
import threading
import time
import traceback

from . import ROOT, SCHEMA, __version__
from .model import ModelBuilder, now_iso

EMPTY_COUNTS = {"pokemon": 0, "moves": 0, "abilities": 0, "items": 0, "tms": 0, "locations": 0, "wildSlots": 0, "fishSlots": 0,
                "characters": 0, "chapters": 0, "steps": 0, "shops": 0, "missions": 0, "types": 0, "berries": 0}


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False, default=str).encode("utf-8")


def emergency_model(version, reason, pbs_dir):
    """Modelo mínimo válido (todas las claves obligatorias, listas vacías) cuando no hay nada mejor."""
    w = {"file": "PBS", "line": 0, "severity": "error", "code": "FILE_MISSING", "message": reason, "suggestion": None, "text": ""}
    return {"meta": {"source": "live", "generatedAt": now_iso(), "version": version,
                     "health": {"status": "error", "errors": 1, "warnings": 0, "infos": 0}, "counts": dict(EMPTY_COUNTS),
                     "schema": SCHEMA, "codexVersion": __version__, "pbsDir": pbs_dir, "baselineSource": None},
            "types": [], "chart": {}, "pokemon": [], "moves": [], "abilities": [], "items": [], "tms": [], "locations": [], "shops": [],
            "missions": [], "progression": [], "characters": [], "story": [], "prelude": None, "ledger": [],
            "assets": {"icons": [], "battlers": [], "battlersBack": [], "battlersShiny": [], "battlersShinyBack": [], "itemIcons": [], "sprites": {}, "missing": []},
            "berryPlants": [], "warnings": [w], "files": []}


class Entry:
    __slots__ = ("model", "body", "gz", "version", "warnings_body", "health_body", "build_ms", "built_at", "errors", "warns", "source", "_gzlock")

    def __init__(self, model, version, build_ms):
        self.model = model
        self.version = version
        self.build_ms = build_ms
        self.built_at = time.time()
        self.body = dumps(model)
        self.gz = None
        self._gzlock = threading.Lock()
        meta = model.get("meta", {})
        h = meta.get("health", {})
        self.errors = h.get("errors", 0)
        self.warns = h.get("warnings", 0)
        self.source = meta.get("source", "live")
        self.warnings_body = dumps(model.get("warnings", []))
        self.health_body = dumps({"status": h.get("status", "error"), "errors": self.errors, "warnings": self.warns, "infos": h.get("infos", 0),
                                  "files": model.get("files", []), "counts": meta.get("counts", {}), "source": self.source,
                                  "version": version, "generatedAt": meta.get("generatedAt"), "buildMs": build_ms})

    def gzip_body(self):
        if self.gz is None:
            with self._gzlock:
                if self.gz is None:
                    self.gz = gzip.compress(self.body, compresslevel=5, mtime=0)
        return self.gz


class Store:
    def __init__(self, pbs_dir, root=ROOT, bundle_path=None, log=None):
        self.pbs_dir = os.path.abspath(pbs_dir)
        self.root = root
        self.bundle_path = bundle_path or os.path.join(root, "codex_bundle", "model.json")
        self.builder = ModelBuilder(self.pbs_dir, root)
        self._entry = None
        self._sig = None
        self._lock = threading.RLock()
        self._bundle = None            # (mtime, size, modelo)
        self._bundle_entry = None
        self.log = log or (lambda msg: print("[codex] " + msg, file=sys.stderr, flush=True))
        self.builds = 0

    # ----------------------------------------------------------------------- versión barata
    def version_info(self):
        try:
            version, mtimes = self.builder.signature()
        except Exception:
            version, mtimes = (self._entry.version if self._entry else "0"), {}
        return {"version": version, "mtimes": mtimes, "serverTime": time.time(),
                "built": self._entry.version if self._entry else None}

    # ------------------------------------------------------------------------ bundle
    def load_bundle(self):
        p = self.bundle_path
        try:
            st = os.stat(p)
        except OSError:
            return None
        key = (st.st_mtime_ns, st.st_size)
        if self._bundle and self._bundle[0] == key:
            return self._bundle[1]
        try:
            with open(p, "rb") as f:
                m = json.loads(f.read().decode("utf-8"))
            if isinstance(m, dict) and m.get("pokemon"):
                self._bundle = (key, m)
                return m
        except Exception as e:
            self.log("No se pudo leer el bundle (%s)" % e.__class__.__name__)
        return None

    def bundle_entry(self):
        b = self.load_bundle()
        if b is None:
            return None
        if self._bundle_entry is not None and self._bundle_entry[0] is b:
            return self._bundle_entry[1]
        m = json.loads(json.dumps(b))
        m.setdefault("meta", {})["source"] = "bundle"
        e = Entry(m, m["meta"].get("version", "bundle"), 0)
        self._bundle_entry = (b, e)
        return e

    # ------------------------------------------------------------------- construcción
    def _settle(self, version):
        """Si algún archivo se modificó hace un instante, espera un poco por si se está escribiendo."""
        try:
            v, mtimes = self.builder.signature()
            newest = max(mtimes.values()) if mtimes else 0
            if time.time() - newest < 0.25:
                time.sleep(0.3)
                return self.builder.signature()[0]
            return v
        except Exception:
            return version

    def _build(self, version, force=False):
        t0 = time.time()
        model = None
        try:
            if force:
                self.builder.store.invalidate()
            model = self.builder.build()
            model["meta"]["version"] = version
        except Exception as e:
            self.log("Fallo catastrófico al construir el modelo: %s" % "".join(traceback.format_exception_only(type(e), e)).strip())
            traceback.print_exc(file=sys.stderr)
            model = None
        if model is None or not model.get("pokemon"):
            reason = "No se pudo construir el modelo desde PBS/ (%s)" % ("error interno" if model is None else "pokemon.txt no contiene ninguna especie")
            be = self.bundle_entry()
            if be is not None:
                m = json.loads(json.dumps(be.model))
                warn = {"file": "PBS", "line": 0, "severity": "error", "code": "FILE_MISSING",
                        "message": reason + ": se sirve la copia de seguridad codex_bundle/model.json", "suggestion": "Revisa la carpeta PBS/", "text": ""}
                live_w = (model or {}).get("warnings", [])
                m["warnings"] = [warn] + live_w + m.get("warnings", [])
                m["files"] = (model or {}).get("files", m.get("files", []))
                m["meta"]["source"] = "bundle"
                m["meta"]["version"] = version
                h = m["meta"].setdefault("health", {})
                h["status"] = "error"
                h["errors"] = h.get("errors", 0) + 1 + (model or {}).get("meta", {}).get("health", {}).get("errors", 0)
                model = m
                self.log(reason + ": se sirve el bundle")
            elif model is None:
                model = emergency_model(version, reason + " y no hay bundle de respaldo", self.pbs_dir)
        entry = Entry(model, version, int((time.time() - t0) * 1000))
        self.builds += 1
        h = model.get("meta", {}).get("health", {})
        self.log("modelo %s construido en %.2f s: %d Pokémon, %d errores, %d avisos (origen: %s)" % (
            version, time.time() - t0, len(model.get("pokemon", [])), h.get("errors", 0), h.get("warnings", 0), model.get("meta", {}).get("source")))
        return entry

    def get(self):
        """Modelo vigente; reconstruye si cambió algún archivo."""
        try:
            version, _ = self.builder.signature()
        except Exception:
            version = self._sig
        e = self._entry
        if e is not None and version == self._sig:
            return e
        with self._lock:
            try:
                version, _ = self.builder.signature()
            except Exception:
                version = self._sig or "0"
            if self._entry is not None and version == self._sig:
                return self._entry
            if self._entry is not None:
                version = self._settle(version)
            self._entry = self._build(version)
            self._sig = version
            return self._entry

    def reload(self):
        with self._lock:
            try:
                version, _ = self.builder.signature()
            except Exception:
                version = self._sig or "0"
            self._entry = self._build(version, force=True)
            self._sig = version
            return self._entry
