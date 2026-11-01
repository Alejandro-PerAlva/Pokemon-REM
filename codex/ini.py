"""Lectura tolerante de archivos de texto PBS y del dialecto INI de los ``rem_*.txt`` (SPEC §2).

Más tolerante que ``tools/codex/remini_ref.py``: BOM o no, UTF-16, CRLF/LF/CR/mezcla, líneas basura,
claves repetidas (acumulan), espacios y mayúsculas indiferentes, cabeceras ``[ CLAVE ]`` con basura detrás.
Nada de lo que contenga un archivo puede lanzar una excepción desde este módulo.
"""
import difflib
import os
import re

from .fuzzy import norm

_EOL = re.compile(r"\r\n|\n|\r")


class TextFile:
    """Archivo ya leído y decodificado (cacheable por mtime+tamaño)."""

    __slots__ = ("name", "path", "exists", "size", "mtime", "mtime_ns", "text", "lines", "bom", "eol",
                 "enc_issues", "empty", "stale", "n_lines", "ok")

    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.exists = False
        self.size = 0
        self.mtime = 0.0
        self.mtime_ns = 0
        self.text = ""
        self.lines = []
        self.bom = False
        self.eol = None
        self.enc_issues = []     # (línea, severidad, código, mensaje, sugerencia)
        self.empty = True
        self.stale = False       # se reutiliza una lectura anterior porque el archivo desapareció
        self.n_lines = 0
        self.ok = False


def read_textfile(name, path):
    """Lee y decodifica ``path``. Jamás lanza: los fallos quedan reflejados en el objeto."""
    tf = TextFile(name, path)
    try:
        st = os.stat(path)
    except OSError:
        return tf
    tf.exists = True
    tf.size = st.st_size
    tf.mtime = st.st_mtime
    tf.mtime_ns = st.st_mtime_ns
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError as e:
        tf.enc_issues.append((0, "error", "ENCODING", "No se puede leer el archivo: %s" % e.__class__.__name__, None))
        return tf
    try:
        _decode(tf, raw)
    except Exception as e:  # pragma: no cover
        tf.enc_issues.append((0, "error", "ENCODING", "Error inesperado al decodificar: %s" % e.__class__.__name__, None))
        tf.text = raw.decode("utf-8", errors="replace")
    _split(tf)
    tf.empty = not tf.text.strip()
    tf.ok = not tf.empty
    return tf


def _decode(tf, raw):
    if raw.startswith(b"\xef\xbb\xbf"):
        tf.bom = True
        raw = raw[3:]
    elif raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        tf.enc_issues.append((1, "error", "ENCODING",
                              "El archivo está en UTF-16; Essentials necesita UTF-8 con BOM", "Guárdalo como UTF-8 con BOM"))
        tf.text = raw.decode("utf-16", errors="replace")
        return
    try:
        tf.text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        txt = raw.decode("utf-8", errors="replace")
        n = txt.count("�")
        line = raw[:e.start].count(b"\n") + 1
        tf.enc_issues.append((line, "error", "ENCODING",
                              "Codificación rota: %d carácter(es) no válidos en UTF-8 (se sustituyen por «�»)" % n,
                              "Guarda el archivo como UTF-8 con BOM"))
        tf.text = txt
        return
    if not tf.bom and any(ord(c) > 127 for c in tf.text[:200000]):
        tf.enc_issues.append((1, "info", "ENCODING",
                              "El archivo no tiene BOM UTF-8 (Essentials puede mostrar mal las tildes)", "Guárdalo como UTF-8 con BOM"))
    if "�" in tf.text:
        ln = tf.text[:tf.text.index("�")].count("\n") + 1
        tf.enc_issues.append((ln, "warn", "ENCODING", "El texto contiene el carácter de sustitución «�» (codificación dañada)", None))


def _split(tf):
    text = tf.text
    if "﻿" in text:
        text = text.replace("﻿", "")
        tf.text = text
    n_crlf = text.count("\r\n")
    n_lf = text.count("\n") - n_crlf
    n_cr = text.count("\r") - n_crlf
    if n_crlf and not n_lf and not n_cr:
        tf.eol = "crlf"
    elif n_lf and not n_crlf and not n_cr:
        tf.eol = "lf"
    elif n_cr and not n_crlf and not n_lf:
        tf.eol = "cr"
    elif n_crlf or n_lf or n_cr:
        tf.eol = "mixed"
    if tf.eol == "lf":
        tf.enc_issues.append((0, "info", "ENCODING", "Finales de línea LF (el estándar del proyecto es CRLF)", None))
    elif tf.eol == "cr":
        tf.enc_issues.append((0, "warn", "ENCODING", "Finales de línea CR antiguos (Mac clásico): conviene CRLF", None))
    elif tf.eol == "mixed":
        tf.enc_issues.append((0, "info", "ENCODING", "Finales de línea mezclados (CRLF/LF/CR)", None))
    lines = _EOL.split(text)
    if lines and lines[-1] == "":
        lines.pop()
    tf.lines = lines
    tf.n_lines = len(lines)


# ------------------------------------------------------------------------------------------------
class Item:
    __slots__ = ("line", "key", "raw_key", "value")

    def __init__(self, line, key, raw_key, value):
        self.line, self.key, self.raw_key, self.value = line, key, raw_key, value


class Section:
    __slots__ = ("key", "ukey", "line", "items", "_idx", "raw_header")

    def __init__(self, key, line, raw_header=""):
        self.key = key               # tal cual (sin espacios exteriores)
        self.ukey = key.upper()
        self.line = line
        self.items = []
        self._idx = None
        self.raw_header = raw_header

    def _index(self):
        if self._idx is None:
            d = {}
            for it in self.items:
                d.setdefault(it.key, []).append(it)
            self._idx = d
        return self._idx

    def all_items(self, key):
        return self._index().get(norm(key), [])

    def all(self, key):
        """Todos los valores de la clave, en orden."""
        return [it.value for it in self.all_items(key)]

    def first(self, key, default=""):
        its = self.all_items(key)
        return its[0].value if its else default

    def last(self, key, default=""):
        its = self.all_items(key)
        return its[-1].value if its else default

    def has(self, key):
        return norm(key) in self._index()

    def line_of(self, key, default=None):
        its = self.all_items(key)
        return its[0].line if its else (default or self.line)

    def keys(self):
        return list(self._index().keys())


_SECTION = re.compile(r"^\[\s*([^\]]*?)\s*\]\s*(.*)$")
_PARTIAL_SECTION = re.compile(r"^\[\s*([A-Za-z0-9_:\-\. ]+?)\s*$")
_KEYVAL = re.compile(r"^\s*([^=]*?)\s*=\s?(.*?)\s*$")


def check_keys(sections, known_fn, iss, file, skip=None):
    """Comprueba las claves de cada sección. ``known_fn(sec)`` -> (conjunto de claves normalizadas, [regex]) o None.

    * Clave casi igual a una conocida (typo): se corrige y se avisa (warn, sugerencia aplicada).
    * Clave desconocida: se CONSERVA (el modelo la expone como campo extra) y se avisa una sola vez por clave (info).
    """
    unknown = {}
    for sec in sections:
        if skip is not None and skip(sec):
            continue
        try:
            kn = known_fn(sec)
        except Exception:
            kn = None
        if kn is None:
            continue
        ks, rx = kn
        for it in sec.items:
            if it.key in ks or any(r.match(it.key) for r in rx):
                continue
            cand = difflib.get_close_matches(it.key, sorted(ks), n=1, cutoff=0.82) if len(it.key) >= 4 else []
            if cand:
                iss.add(file, it.line, "warn", "UNKNOWN_KEY", "Clave «%s» no reconocida en [%s]; se interpreta como «%s»" % (it.raw_key, sec.key, cand[0]),
                        suggestion=cand[0], applied=True)
                it.key = cand[0]
                sec._idx = None
                continue
            u = unknown.setdefault(it.key, [it.line, it.raw_key, sec.key, 0])
            u[3] += 1
    for k, (line, raw_key, secname, n) in unknown.items():
        iss.add(file, line, "info", "UNKNOWN_KEY",
                "Clave «%s» no está en el contrato (%d aparici%s, p. ej. en [%s]); se conserva como campo extra" % (raw_key, n, "ón" if n == 1 else "ones", secname))


def parse_ini(tf, iss, file=None, known=None, known_re=None, single=None, allow_semicolon_comments=True, skip=None):
    """Divide ``tf`` en secciones.

    ``known``: conjunto de claves normalizadas válidas (``norm``) -> las demás generan aviso info UNKNOWN_KEY.
    ``known_re``: expresiones adicionales para claves con sufijo numérico (``slot\\d+``…).
    ``single``: claves que no deberían repetirse (aviso DUPLICATE_KEY; gana la última).
    Devuelve la lista de ``Section`` (en orden).
    """
    file = file or tf.name
    sections = []
    cur = None
    in_garbage = 0
    for n, raw in enumerate(tf.lines, 1):
        try:
            s = raw.strip()
            if not s:
                continue
            if s[0] == "#" or (allow_semicolon_comments and s[0] == ";"):
                continue
            if s[0] == "[":
                m = _SECTION.match(s)
                if m and m.group(1):
                    if m.group(2) and not m.group(2).lstrip().startswith(("#", ";")):
                        iss.add(file, n, "info", "BAD_LINE", "Texto sobrante tras la cabecera de sección; se ignora", text=raw)
                    cur = Section(m.group(1).strip(), n, s)
                    sections.append(cur)
                    continue
                m2 = _PARTIAL_SECTION.match(s)
                if m2:
                    iss.add(file, n, "warn", "BAD_LINE", "Cabecera de sección sin «]»: se interpreta como [%s]" % m2.group(1).strip(),
                            suggestion="[%s]" % m2.group(1).strip(), text=raw, applied=True)
                    cur = Section(m2.group(1).strip(), n, s)
                    sections.append(cur)
                    continue
                iss.add(file, n, "warn", "BAD_LINE", "Cabecera de sección ilegible; se ignora la línea", text=raw)
                continue
            if "=" not in s:
                iss.add(file, n, "warn", "BAD_LINE", "Línea sin «=» (se esperaba «Clave = Valor»); se ignora",
                        suggestion="Añade «Clave = Valor» o conviértela en comentario con #", text=raw)
                continue
            m = _KEYVAL.match(s)
            if not m:
                iss.add(file, n, "warn", "BAD_LINE", "Línea ilegible; se ignora", text=raw)
                continue
            rk, val = m.group(1), m.group(2)
            nk = norm(rk)
            if not nk:
                iss.add(file, n, "warn", "BAD_LINE", "Línea con clave vacía antes del «=»; se ignora", text=raw)
                continue
            if cur is None:
                iss.add(file, n, "warn", "BAD_LINE", "Clave fuera de cualquier sección [CLAVE]; se ignora", text=raw)
                continue
            cur.items.append(Item(n, nk, rk, val))
        except Exception:  # pragma: no cover
            iss.add(file, n, "warn", "BAD_LINE", "Línea ilegible; se ignora", text=raw)
    if callable(known):
        check_keys(sections, known, iss, file, skip)
    if single:
        for sec in sections:
            if skip is not None and skip(sec):
                continue
            for k in single:
                its = sec.all_items(k)
                if len(its) > 1:
                    iss.add(file, its[1].line, "warn", "DUPLICATE_KEY",
                            "Clave «%s» repetida en [%s] (primera en línea %d); se usa la última" % (its[0].raw_key, sec.key, its[0].line),
                            text=None)
    return sections


# --------------------------------------------------------------------------------- utilidades de valores
def split_list(s, sep=";"):
    """Lista simple separada por ``sep`` (vacíos fuera)."""
    if s is None:
        return []
    return [p.strip() for p in str(s).split(sep) if p.strip()]


def split_csv_max(s, n):
    """Divide por comas con maxsplit ``n`` (el último campo conserva sus comas). Rellena a n+1 campos."""
    parts = [p.strip() for p in str(s).split(",", n)]
    while len(parts) < n + 1:
        parts.append("")
    return parts


def csv_fields(line):
    """Campos CSV estilo Essentials (comillas con ``\\"`` y también ``""``). Devuelve (campos, ok)."""
    out = []
    i, n = 0, len(line)
    ok = True
    while True:
        while i < n and line[i] in " \t":
            i += 1
        if i < n and line[i] == '"':
            i += 1
            buf = []
            closed = False
            while i < n:
                c = line[i]
                if c == "\\" and i + 1 < n and line[i + 1] in '"\\':
                    buf.append(line[i + 1])
                    i += 2
                    continue
                if c == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        buf.append('"')
                        i += 2
                        continue
                    closed = True
                    i += 1
                    break
                buf.append(c)
                i += 1
            if not closed:
                ok = False
            out.append("".join(buf))
            while i < n and line[i] in " \t":
                i += 1
            if i < n and line[i] != ",":
                ok = False
                # basura tras la comilla de cierre: se añade al campo
                j = line.find(",", i)
                if j < 0:
                    out[-1] += line[i:]
                    i = n
                else:
                    out[-1] += line[i:j]
                    i = j
        else:
            j = line.find(",", i)
            if j < 0:
                out.append(line[i:].strip())
                i = n
            else:
                out.append(line[i:j].strip())
                i = j
        if i >= n:
            break
        i += 1   # salta la coma
        if i >= n:
            out.append("")
            break
    return out, ok


def parse_range(s):
    """'3-5' | '3–5' | '4' -> [a,b] o None."""
    t = (s or "").strip()
    if not t:
        return None
    m = re.match(r"^(\d+)\s*(?:[-–—]|a|\.\.)\s*(\d+)$", t)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return [min(a, b), max(a, b)]
    m = re.match(r"^(\d+)$", t)
    if m:
        v = int(m.group(1))
        return [v, v]
    return None
