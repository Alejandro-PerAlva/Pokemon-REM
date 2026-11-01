"""Búsqueda difusa de símbolos/nombres (tipos, movimientos, habilidades, objetos, especies, ubicaciones…).

* ``norm``: minúsculas, sin tildes ni signos (compara símbolos PBS y nombres en español por igual).
* ``Lookup``: índice de un dominio (símbolo -> nombres alternativos) con coincidencia exacta, por nombre
  y difusa (distancia de edición + difflib).
* ``Resolver``: aplica un ``Lookup`` a un valor concreto y emite el ``Warning`` correspondiente
  (código ``UNKNOWN_*``, mensaje en español, sugerencia «¿quisiste decir…?»).
"""
import difflib
import re
import unicodedata

_NON_ALNUM = re.compile(r"[^0-9a-z]+")


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm(s):
    """Forma canónica comparable: sin tildes, minúsculas, solo [a-z0-9]."""
    if s is None:
        return ""
    return _NON_ALNUM.sub("", strip_accents(str(s)).lower())


def edit_distance(a, b, limit=None):
    """Distancia de Damerau-Levenshtein (alineación óptima de cadenas). Devuelve limit+1 si la supera."""
    la, lb = len(a), len(b)
    if limit is not None and abs(la - lb) > limit:
        return limit + 1
    if la == 0:
        return lb
    if lb == 0:
        return la
    prev2 = None
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        ai = a[i - 1]
        best = cur[0]
        for j in range(1, lb + 1):
            cost = 0 if ai == b[j - 1] else 1
            v = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            if prev2 is not None and i > 1 and j > 1 and ai == b[j - 2] and a[i - 2] == b[j - 1]:
                v = min(v, prev2[j - 2] + 1)
            cur[j] = v
            if v < best:
                best = v
        if limit is not None and best > limit:
            return limit + 1
        prev2, prev = prev, cur
    return prev[lb]


class Suggestion:
    __slots__ = ("sym", "dist", "ratio", "auto")

    def __init__(self, sym, dist, ratio, auto):
        self.sym, self.dist, self.ratio, self.auto = sym, dist, ratio, auto


class Lookup:
    """Índice de un dominio de símbolos. ``add(sym, *aliases)`` registra el símbolo y sus nombres."""

    MAX_FUZZY = 400     # consultas difusas distintas por construcción del modelo (límite de coste)

    def __init__(self, kind, label_es, fem=False):
        self.kind = kind
        self.label = label_es
        self.fem = fem
        self.syms = {}      # símbolo exacto -> símbolo
        self.upper = {}     # símbolo en mayúsculas -> símbolo
        self.nsym = {}      # norm(símbolo) -> símbolo
        self.nname = {}     # norm(nombre) -> símbolo
        self._cand = {}     # cadena normalizada -> símbolo (para difuso)
        self._cache = {}
        self._fuzzy_calls = 0
        self.ignore = set()     # cadenas normalizadas que existen pero quedan FUERA del modelo (se omiten sin avisar)

    def ignore_add(self, *names):
        for n in names:
            nn = norm(n)
            if nn:
                self.ignore.add(nn)

    def is_ignored(self, text):
        return bool(self.ignore) and norm(text) in self.ignore and self.lookup(text)[0] is None

    def __contains__(self, sym):
        return sym in self.syms

    def __len__(self):
        return len(self.syms)

    def add(self, sym, *aliases):
        if not sym:
            return
        self.syms.setdefault(sym, sym)
        self.upper.setdefault(sym.upper(), sym)
        n = norm(sym)
        if n:
            self.nsym.setdefault(n, sym)
            self._cand.setdefault(n, sym)
        for a in aliases:
            na = norm(a)
            if na:
                self.nname.setdefault(na, sym)
                self._cand.setdefault(na, sym)
        self._cache.clear()

    def lookup(self, text):
        """-> (símbolo, cómo) con cómo en {'exact','case','name'} o (None, None)."""
        t = (text or "").strip()
        if not t:
            return None, None
        if t in self.syms:
            return t, "exact"
        u = t.upper()
        if u in self.upper:
            return self.upper[u], "case"
        n = norm(t)
        if n in self.nsym:
            return self.nsym[n], "case"
        if n in self.nname:
            return self.nname[n], "name"
        return None, None

    def suggest(self, text):
        """Mejor candidato difuso o None. ``auto`` indica que es suficientemente seguro para aplicarlo."""
        n = norm(text)
        if not n or len(n) < 2:
            return None
        if n in self._cache:
            return self._cache[n]
        if self._fuzzy_calls >= self.MAX_FUZZY:
            return None
        self._fuzzy_calls += 1
        res = self._suggest(n)
        self._cache[n] = res
        return res

    def _suggest(self, n):
        keys = list(self._cand.keys())
        close = difflib.get_close_matches(n, keys, n=6, cutoff=0.5)
        scored = []
        seen = set()
        for c in close:
            sym = self._cand[c]
            lim = max(2, len(n) // 2)
            d = edit_distance(n, c, lim)
            r = difflib.SequenceMatcher(None, n, c).ratio()
            scored.append((d, -r, sym))
        # candidatos con prefijo/sufijo común (p. ej. nombre truncado)
        if len(n) >= 4:
            for c, sym in self._cand.items():
                if len(c) >= 4 and (c.startswith(n) or n.startswith(c)) and abs(len(c) - len(n)) <= 3:
                    d = edit_distance(n, c, 4)
                    scored.append((d, -difflib.SequenceMatcher(None, n, c).ratio(), sym))
        if not scored:
            return None
        scored.sort()
        best = scored[0]
        d, nr, sym = best
        # el más cercano de OTRO símbolo
        other = None
        for s in scored[1:]:
            if s[2] != sym:
                other = s
                break
        L = len(n)
        allowed = 1 if L <= 7 else (2 if L <= 14 else 3)
        auto = d <= allowed and (-nr) >= 0.8
        if auto and other is not None and other[0] <= d:
            auto = False        # ambiguo
        if d > max(2, L // 2) and -nr < 0.6:
            return None
        return Suggestion(sym, d, -nr, auto)


class Resolver:
    """Resuelve valores contra ``Lookup`` registrando avisos. ``issues`` es un ``Issues``."""

    def __init__(self, issues):
        self.issues = issues

    def ref(self, lk, raw, file, line, code, text=None, severity="error", quiet_case=True, apply=True, context=None):
        """Devuelve el símbolo canónico (posiblemente corregido) o None si es irrecuperable."""
        t = (raw or "").strip()
        if not t:
            return None
        try:
            if lk.ignore and lk.is_ignored(t):
                return None
            sym, how = lk.lookup(t)
            if sym is not None:
                if how == "name" and t != sym:
                    self.issues.add(file, line, "warn", code,
                                    "%s «%s» escrito como nombre; el compilador de Essentials espera el símbolo %s. Se usa %s"
                                    % (lk.label.capitalize(), t, sym, sym),
                                    suggestion=sym, text=text, applied=True)
                return sym
            sug = lk.suggest(t)
            ctx = (" en " + context) if context else ""
            if sug is not None and sug.auto and apply:
                self.issues.add(file, line, severity, code,
                                "%s desconocid%s «%s»%s: se usa «%s»" % (lk.label.capitalize(), "a" if lk.fem else "o", t, ctx, sug.sym),
                                suggestion=sug.sym, text=text, applied=True)
                return sug.sym
            if sug is not None:
                self.issues.add(file, line, severity, code,
                                "%s desconocid%s «%s»%s: se omite. ¿Quisiste decir «%s»?" % (lk.label.capitalize(), "a" if lk.fem else "o", t, ctx, sug.sym),
                                suggestion=sug.sym, text=text, applied=False)
                return None
            self.issues.add(file, line, severity, code,
                            "%s desconocid%s «%s»%s: se omite" % (lk.label.capitalize(), "a" if lk.fem else "o", t, ctx),
                            suggestion=None, text=text, applied=False)
        except Exception:
            pass
        return None

    def silent(self, lk, raw):
        """Resolución sin avisos (exacta, por nombre o difusa automática). -> símbolo | None"""
        t = (raw or "").strip()
        if not t:
            return None
        sym, how = lk.lookup(t)
        if sym is not None:
            return sym
        if lk.ignore and lk.is_ignored(t):
            return None
        sug = lk.suggest(t)
        if sug is not None and sug.auto:
            return sug.sym
        return None


# ---------------------------------------------------------------- números tolerantes
_LOOKALIKE = {"o": "0", "O": "0", "l": "1", "I": "1", "i": "1", "|": "1", "S": "5", "s": "5", "B": "8", "Z": "2", "z": "2"}


def fix_number(text, allow_negative=False, allow_float=False):
    """Intenta reparar un número mal escrito ('4o' -> 40). Devuelve (valor|None, texto_sugerido|None)."""
    t = (text or "").strip().replace(" ", "")
    if not t:
        return None, None
    pat = r"-?\d+(\.\d+)?" if allow_float else r"-?\d+"
    if re.fullmatch(pat, t):
        v = float(t) if allow_float else int(t)
        if not allow_negative and v < 0:
            return None, None
        return v, t
    t2 = t.replace(",", ".") if allow_float else t
    if allow_float and re.fullmatch(pat, t2):
        return float(t2), t2
    t3 = "".join(_LOOKALIKE.get(c, c) for c in t)
    if re.fullmatch(pat, t3):
        v = float(t3) if allow_float else int(t3)
        if allow_negative or v >= 0:
            return v, t3
    m = re.match(r"-?\d+(\.\d+)?" if allow_float else r"-?\d+", t)
    if m:
        s = m.group(0)
        v = float(s) if allow_float else int(s)
        if allow_negative or v >= 0:
            return v, s
    t4 = t.rstrip("%")
    if t4 != t and re.fullmatch(pat, t4):
        v = float(t4) if allow_float else int(t4)
        return v, t4
    return None, None


def parse_int(res_issues, file, line, field, text, default=None, minimum=None, maximum=None, allow_negative=False, text_line=None):
    """Convierte a entero con aviso BAD_NUMBER si no es válido. Devuelve el entero (posiblemente reparado) o ``default``."""
    t = (text or "").strip()
    if t == "":
        return default
    try:
        if re.fullmatch(r"-?\d+", t):
            v = int(t)
            if (not allow_negative and v < 0) or (minimum is not None and v < minimum) or (maximum is not None and v > maximum):
                res_issues.add(file, line, "warn", "BAD_NUMBER",
                               "Valor fuera de rango en %s: «%s»" % (field, t), suggestion=None, text=text_line)
            return v
        v, s = fix_number(t, allow_negative=allow_negative)
        if v is not None:
            res_issues.add(file, line, "error", "BAD_NUMBER",
                           "Número mal formado en %s: «%s»; se interpreta como %s" % (field, t, s),
                           suggestion=s, text=text_line, applied=True)
            return v
        res_issues.add(file, line, "error", "BAD_NUMBER",
                       "Número mal formado en %s: «%s»%s" % (field, t, "; se usa %s" % default if default is not None else "; se ignora"),
                       suggestion=None, text=text_line, applied=default is not None)
    except Exception:
        pass
    return default
