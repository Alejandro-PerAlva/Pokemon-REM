#!/usr/bin/env python3
"""Autopruebas del backend del Codex. Copia PBS a un directorio temporal (no modifica PBS/)."""
import gzip, json, os, shutil, sys, tempfile, threading, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
from codex.server import make_server
from codex.store import Store
from model_contract import validate_model

FAILS = []
def check(name, cond, extra=""):
    print(("OK   " if cond else "FALLO"), name, extra)
    if not cond: FAILS.append(name)

def start(pbs):
    st = Store(pbs, ROOT, log=lambda m: None)
    srv, port = make_server(st, "127.0.0.1", 18800)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d" % port

def get(url, raw=False, method="GET"):
    req = urllib.request.Request(url, method=method, headers={"Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            b = r.read()
            if r.headers.get("Content-Encoding") == "gzip": b = gzip.decompress(b)
            if not raw:
                try: b = json.loads(b)
                except Exception: pass
            return r.status, b, r.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers

def endpoints(base, label):
    t = time.time(); s, m, h = get(base + "/api/model"); dt = time.time() - t
    check(label + " /api/model 200 + X-REM-Version", s == 200 and h.get("X-REM-Version"), "%.2fs" % dt)
    pr = validate_model(m); check(label + " validate_model", not pr, "; ".join(pr[:3]))
    check(label + " 721 Pokémon", len(m["pokemon"]) == 721)
    for ep in ("/api/version", "/api/warnings", "/api/health"):
        s, _, h = get(base + ep); check(label + " " + ep, s == 200 and h.get("Cache-Control") == "no-store")
    s, j, _ = get(base + "/api/reload", method="POST"); check(label + " POST reload", s == 200 and j.get("ok"), str(j))
    for p, code in (("/gfx/Icons/icon001.png", 200), ("/gfx/../PBS/pokemon.txt", 404), ("/gfx/%2e%2e/%2e%2e/etc/passwd", 404),
                    ("/app/../run_pokedex.py", 404), ("/map/Mapa_Final__Esqueleto.png", 200), ("/api/nada", 404), ("/gfx/Battlers/optipng.exe", 404)):
        s, _, _ = get(base + p); check(label + " " + p, s == code, str(s))
    return m

def inject(tmp):
    def ed(name, fn, enc="utf-8-sig"):
        p = os.path.join(tmp, name); t = open(p, encoding=enc, newline="").read(); open(p, "w", encoding=enc, newline="").write(fn(t))
    inj = []
    ed("pokemon.txt", lambda t: t.replace("Type1=GRASS", "Type1=FUEGOO", 1)); inj.append(("pokemon.txt", "UNKNOWN_TYPE", "FUEGOO"))
    ed("pokemon.txt", lambda t: t.replace("BaseStats=48,49,49,45,65,65", "BaseStats=48,49,4o,45,65,65", 1)); inj.append(("pokemon.txt", "BAD_NUMBER", "4o"))
    ed("pokemon.txt", lambda t: t.replace("Abilities=OVERGROW,", "Abilities=OVERGROWW,", 1)); inj.append(("pokemon.txt", "UNKNOWN_ABILITY", "OVERGROWW"))
    ed("pokemon.txt", lambda t: t.replace("Name=Ivysaur", "Name Ivysaur", 1)); inj.append(("pokemon.txt", "BAD_LINE", "Name Ivysaur"))
    ed("moves.txt", lambda t: t.replace(",TACKLE,", ",PLACAJEE,", 1) if False else t.replace("1,MEGAHORN,", "1,MEGAHORN,", 1))
    ed("pokemon.txt", lambda t: t.replace(",TACKLE,", ",PLACAJEE,", 1)); inj.append(("pokemon.txt", "UNKNOWN_MOVE", "PLACAJEE"))
    ed("items.txt", lambda t: t.replace(",POTION,", ",POTION,", 1))
    ed("tm.txt", lambda t: t.replace("BULBASAUR", "BULBASAURR", 1)); inj.append(("tm.txt", "UNKNOWN_SPECIES", "BULBASAURR"))
    ed("moves.txt", lambda t: t.replace("\r\n", "\r\nxxxx basura sin comas\r\n", 1)); inj.append(("moves.txt", "MISSING_FIELD", "xxxx"))
    ed("rem_shops.txt", lambda t: t.replace("Item1 = POKEBALL", "Item1 = POKEBAL", 1)); inj.append(("rem_shops.txt", "UNKNOWN_ITEM", "POKEBAL"))
    ed("rem_locations.txt", lambda t: t.replace("[PUEBLO_IOLITA]", "[PUEBLO_IOLITTA]", 1)); inj.append(("rem_locations.txt", "UNKNOWN_LOCATION", "IOLITTA"))
    p = os.path.join(tmp, "rem_story.txt"); b = open(p, "rb").read(); open(p, "wb").write(b[3:]); inj.append(("rem_story.txt", "ENCODING", "BOM"))
    ed("abilities.txt", lambda t: t.replace("Hedor", "Hedor\udcff".encode("utf-8", "surrogateescape").decode("latin-1") if False else "Hedor"))
    os.remove(os.path.join(tmp, "berryplants.txt")); inj.append(("berryplants.txt", "FILE_MISSING", "borrado"))
    return inj

def main():
    srv, base = start(os.path.join(ROOT, "PBS"))
    endpoints(base, "PBS"); srv.shutdown()
    tmp = tempfile.mkdtemp(prefix="codex_test_")
    try:
        shutil.copytree(os.path.join(ROOT, "PBS"), os.path.join(tmp, "PBS"))
        pbs = os.path.join(tmp, "PBS"); srv, base = start(pbs)
        s, m0, _ = get(base + "/api/model"); v0 = get(base + "/api/version")[1]["version"]
        inj = inject(pbs); time.sleep(0.5)
        s, m, _ = get(base + "/api/model"); s2, w, _ = get(base + "/api/warnings")
        check("tolerancia: responde 200 con errores inyectados", s == 200 and s2 == 200)
        check("tolerancia: mantiene 721 Pokémon", len(m["pokemon"]) == 721)
        check("tolerancia: FUEGOO corregido a FIRE", m["pokemon"][0]["types"][0] == "FIRE" or "FIRE" in m["pokemon"][0]["types"])
        for f, code, frag in inj:
            ok = any(x["file"] == f and x["code"] == code and (frag in (x["text"] + x["message"]) or frag in ("BOM", "borrado")) and (x["line"] > 0 or code in ("FILE_MISSING", "ENCODING")) for x in w)
            check("aviso %s %s (%s)" % (f, code, frag), ok)
        ex = [x for x in w if x["code"] == "UNKNOWN_TYPE"]
        check("sugerencia FIRE", any(x["suggestion"] == "FIRE" for x in ex))
        check("sugerencia TACKLE", any(x["suggestion"] == "TACKLE" for x in w))
        check("versión cambia", get(base + "/api/version")[1]["version"] != v0)
        v1 = get(base + "/api/version")[1]["version"]
        p = os.path.join(pbs, "pokemon.txt"); t = open(p, encoding="utf-8-sig", newline="").read()
        open(p, "w", encoding="utf-8-sig", newline="").write(t.replace("Name=Bulbasaur", "Name=Bulbasaur", 1).replace("BaseStats=48,49,4o,45,65,65", "BaseStats=50,49,49,45,65,65", 1))
        time.sleep(0.5)
        s, m2, _ = get(base + "/api/model")
        check("recarga en vivo sin reiniciar", get(base + "/api/version")[1]["version"] != v1 and m2["pokemon"][0]["stats"]["hp"] == 50, str(m2["pokemon"][0]["stats"]["hp"]))
        check("diff en vivo refleja stat", m2["pokemon"][0]["diff"]["stats"]["hp"] == 50 - m2["pokemon"][0]["baseline"]["stats"]["hp"])
        os.remove(os.path.join(pbs, "moves.txt")); time.sleep(0.5)
        s, m3, _ = get(base + "/api/model"); check("archivo obligatorio borrado: modelo sigue", s == 200 and len(m3["moves"]) == 765)
        srv.shutdown()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\nRESULTADO:", "TODO OK" if not FAILS else "%d fallos: %s" % (len(FAILS), FAILS))
    return 1 if FAILS else 0

if __name__ == "__main__":
    sys.exit(main())
