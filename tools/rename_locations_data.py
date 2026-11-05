#!/usr/bin/env python3
"""Renombra ubicaciones dentro de los .rxdata/.dat (Marshal de Ruby) sin reserializar:
recorre el formato Marshal y solo reescribe el contenido (y la longitud) de los strings
afectados; el resto de bytes y los indices de enlaces quedan identicos.
Uso (desde la raiz): python3 tools/rename_locations_data.py [--dry]
"""
import glob, os, sys

SUBS = [  # (viejo, nuevo) aplicado al contenido de cualquier string
    (b"Pueblo Cianita", b"Pueblo Albor"), (b"Pueblo Topacio", b"Pueblo Heliar"),
    (b"Granja Ambarina", b"Granja Apato"), (b"Bosque Turmalino", b"Bosque Dioptasa"),
    (b"PuebloIolar", b"PuebloAlbor"), (b"PUEBLO_IOLAR", b"PUEBLO_ALBOR"),
]
EXACT = {b"Topacio": b"Heliar"}  # autotile "Topacio.png"

class P:
    def __init__(s, b): s.b, s.i, s.out, s.n = b, 0, bytearray(), 0
    def byte(s): c = s.b[s.i]; s.i += 1; return c
    def long(s):
        c = s.byte(); c = c - 256 if c > 127 else c
        if c == 0: return 0
        if 4 < c < 128: return c - 5
        if -129 < c < -4: return c + 5
        n = abs(c); v = int.from_bytes(s.b[s.i:s.i + n], 'little'); s.i += n
        return v - (1 << (8 * n)) if c < 0 else v
    def wlong(s, v):
        o = s.out
        if v == 0: o.append(0)
        elif 0 < v < 123: o.append(v + 5)
        elif -124 < v < 0: o.append((v - 5) & 255)
        else:
            n = 1
            while True:
                if -(1 << (8 * n - 1)) <= v < (1 << (8 * n - 1)) or (v >= 0 and v < (1 << (8 * n))): break
                n += 1
            # formato Ruby: cuenta de bytes con signo
            if v > 0: o.append(n); o += v.to_bytes(n, 'little')
            else: o.append((-n) & 255); o += (v & ((1 << (8 * n)) - 1)).to_bytes(n, 'little')
    def raw_long(s):  # copia tal cual
        st = s.i; v = s.long(); s.out += s.b[st:s.i]; return v
    def sym(s):
        t = s.byte(); s.out.append(t)
        if t == 0x3a: n = s.raw_long(); s.out += s.b[s.i:s.i + n]; s.i += n
        elif t == 0x3b: s.raw_long()
        else: raise ValueError('simbolo esperado en %d' % s.i)
    def val(s):
        t = s.byte(); c = chr(t)
        if c in '0TF': s.out.append(t)
        elif c == 'i': s.out.append(t); s.raw_long()
        elif c == '"':
            n = s.long(); d = s.b[s.i:s.i + n]; s.i += n
            nd = EXACT.get(d, d)
            for a, b in SUBS: nd = nd.replace(a, b)
            if nd != d: s.n += 1
            s.out.append(t); s.wlong(len(nd)); s.out += nd
        elif c in ':;':
            s.i -= 1; s.sym()
        elif c == '@': s.out.append(t); s.raw_long()
        elif c == 'I':
            s.out.append(t); s.val(); n = s.raw_long()
            for _ in range(n): s.sym(); s.val()
        elif c == '[':
            s.out.append(t); n = s.raw_long()
            for _ in range(n): s.val()
        elif c in '{}':
            s.out.append(t); n = s.raw_long()
            for _ in range(2 * n): s.val()
            if c == '}': s.val()
        elif c in 'oS':
            s.out.append(t); s.sym(); n = s.raw_long()
            for _ in range(n): s.sym(); s.val()
        elif c == 'u':
            s.out.append(t); s.sym(); n = s.raw_long(); s.out += s.b[s.i:s.i + n]; s.i += n
        elif c in 'UC': s.out.append(t); s.sym(); s.val()
        elif c == 'e': s.out.append(t); s.sym(); s.val()
        elif c in 'cmf': s.out.append(t); n = s.raw_long(); s.out += s.b[s.i:s.i + n]; s.i += n
        elif c == 'l':
            s.out.append(t); s.out.append(s.byte()); n = s.raw_long(); s.out += s.b[s.i:s.i + 2 * n]; s.i += 2 * n
        elif c == '/': s.out.append(t); n = s.raw_long(); s.out += s.b[s.i:s.i + n]; s.i += n; s.out.append(s.byte())
        else: raise ValueError('tipo %r en %d' % (c, s.i - 1))

def rewrite(data):
    assert data[:2] == b'\x04\x08'
    p = P(data); p.i = 2; p.out += data[:2]; p.val()
    assert p.i == len(data), 'sobran bytes'
    return bytes(p.out), p.n

if __name__ == '__main__':
    dry = '--dry' in sys.argv
    for f in sorted(glob.glob('Data/Map*.rxdata') + ['Data/MapInfos.rxdata', 'Data/Tilesets.rxdata', 'Data/System.rxdata',
                    'Data/CommonEvents.rxdata', 'Data/messages.dat']):
        d = open(f, 'rb').read(); out, n = rewrite(d)
        if n:
            print('%-28s %d strings' % (f, n))
            if not dry: open(f, 'wb').write(out)
