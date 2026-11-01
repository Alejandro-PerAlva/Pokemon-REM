"""Reference reader for the PBS/rem_*.txt INI dialect (see SPEC.md section 2).

parse(path) -> (sections, warnings)
  sections: list of dict(key=SECTION_KEY, line=int, items=[(lineno, lowercase_key, value)], get(k), all(k))
  warnings: list of (lineno, message)
Repeated keys accumulate (all(k) returns every value in order). Tolerant: never raises on content.
Used by the generators to self-validate; the server has its own, more tolerant, implementation.
"""
import re

class Section(dict):
    def get(self, k, default=''):
        k = k.lower()
        for _, kk, v in self['items']:
            if kk == k:
                return v
        return default
    def all(self, k):
        k = k.lower()
        return [v for _, kk, v in self['items'] if kk == k]

def parse(path):
    raw = open(path, 'rb').read()
    warns = []
    if not raw.startswith(b'\xef\xbb\xbf'):
        warns.append((0, 'sin BOM UTF-8'))
    if b'\n' in raw.replace(b'\r\n', b''):
        warns.append((0, 'finales de línea no CRLF'))
    text = raw.decode('utf-8-sig', errors='replace')
    sections, cur = [], None
    for n, line in enumerate(text.replace('\r\n', '\n').split('\n'), 1):
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        m = re.match(r'^\[([^\]]+)\]\s*$', s)
        if m:
            cur = Section(key=m.group(1).strip(), line=n, items=[])
            sections.append(cur)
            continue
        if '=' not in s:
            warns.append((n, 'línea sin «=»: ' + s[:60]))
            continue
        if cur is None:
            warns.append((n, 'clave fuera de sección: ' + s[:60]))
            continue
        k, v = s.split('=', 1)
        cur['items'].append((n, k.strip().lower(), v.strip()))
    return sections, warns
