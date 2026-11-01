"""Recolector de avisos (Warning del SPEC §4) con deduplicado, límites y contadores por archivo."""
from collections import Counter, defaultdict

SEVERITIES = ("error", "warn", "info")


class Issues:
    """Acumula avisos. Nunca lanza excepciones."""

    def __init__(self, max_total=6000, max_per_file=1500, silent=False):
        self.items = []
        self._seen = set()
        self.counts = defaultdict(Counter)     # archivo -> Counter(severidad)
        self.lines = {}                        # archivo -> lista de líneas (para el campo ``text``)
        self.max_total = max_total
        self.max_per_file = max_per_file
        self._stored_per_file = Counter()
        self._truncated = set()
        self.silent = silent

    def register_lines(self, file, lines):
        self.lines[file] = lines

    def add(self, file, line, severity, code, message, suggestion=None, text=None, applied=None, **extra):
        if self.silent:
            return
        try:
            if severity not in SEVERITIES:
                severity = "warn"
            line = int(line) if line else 0
            if text is None and line and file in self.lines:
                ls = self.lines[file]
                if 0 < line <= len(ls):
                    text = ls[line - 1]
            text = (text or "").strip()
            if len(text) > 260:
                text = text[:257] + "..."
            key = (file, line, code, message)
            if key in self._seen:
                return
            self._seen.add(key)
            self.counts[file][severity] += 1
            if len(self.items) >= self.max_total or self._stored_per_file[file] >= self.max_per_file:
                if file not in self._truncated:
                    self._truncated.add(file)
                    self.items.append({"file": file, "line": 0, "severity": "info", "code": "TOO_MANY",
                                       "message": "Demasiados avisos en este archivo: se omiten los siguientes (los contadores siguen siendo exactos)",
                                       "suggestion": None, "text": ""})
                return
            self._stored_per_file[file] += 1
            w = {"file": file, "line": line, "severity": severity, "code": code, "message": message,
                 "suggestion": suggestion, "text": text}
            if applied is not None:
                w["applied"] = bool(applied)
            if extra:
                w.update(extra)
            self.items.append(w)
        except Exception:  # pragma: no cover - el recolector jamás debe fallar
            pass

    # atajos
    def error(self, file, line, code, message, **kw):
        self.add(file, line, "error", code, message, **kw)

    def warn(self, file, line, code, message, **kw):
        self.add(file, line, "warn", code, message, **kw)

    def info(self, file, line, code, message, **kw):
        self.add(file, line, "info", code, message, **kw)

    def total(self, severity):
        return sum(c[severity] for c in self.counts.values())

    def file_counts(self, file):
        c = self.counts.get(file, Counter())
        return c["error"], c["warn"], c["info"]

    def sorted_items(self):
        order = {"error": 0, "warn": 1, "info": 2}
        return sorted(self.items, key=lambda w: (order.get(w["severity"], 3), w["file"], w["line"], w["code"]))
