#!/usr/bin/env python3
"""Lanzador del Pokémon REM Master Codex (aplicación local, solo biblioteca estándar de Python 3).

Uso:
    python3 start_codex.py                      # arranca en http://127.0.0.1:8765 y abre el navegador
    python3 start_codex.py --port 9000          # otro puerto (si está ocupado se prueba el siguiente)
    python3 start_codex.py --no-browser         # sin abrir el navegador
    python3 start_codex.py --pbs-dir PBS_backup_original   # leer otra carpeta PBS (o variable REM_PBS_DIR)
    python3 start_codex.py --build-bundle       # genera codex_bundle/model.json (copia de seguridad) y sale
    python3 start_codex.py --check              # construye el modelo, lo valida contra el contrato y sale
"""
import argparse
import os
import sys
import threading
import time
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DEFAULT_PORT = 8765


def _msg(text):
    print(text, flush=True)


def resolve_pbs_dir(arg):
    d = arg or os.environ.get("REM_PBS_DIR") or os.path.join(ROOT, "PBS")
    if not os.path.isabs(d):
        cand = os.path.join(os.getcwd(), d)
        d = cand if os.path.isdir(cand) else os.path.join(ROOT, d)
    return os.path.abspath(d)


def load_contract():
    """Importa tools/rebalance/phase1/model_contract.py si existe."""
    p = os.path.join(ROOT, "tools", "rebalance", "phase1")
    if os.path.isfile(os.path.join(p, "model_contract.py")):
        sys.path.insert(0, p)
        try:
            import model_contract  # type: ignore
            return model_contract
        except Exception:
            return None
        finally:
            try:
                sys.path.remove(p)
            except ValueError:
                pass
    return None


def build_bundle(pbs_dir, out=None):
    from codex.model import ModelBuilder
    from codex.store import dumps
    t0 = time.time()
    model = ModelBuilder(pbs_dir).build()
    version = model["meta"].get("version")
    model["meta"]["source"] = "bundle"
    model["meta"]["builtFrom"] = pbs_dir
    out = out or os.path.join(ROOT, "codex_bundle", "model.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out + ".tmp"
    with open(tmp, "wb") as f:
        f.write(dumps(model))
    os.replace(tmp, out)
    h = model["meta"]["health"]
    _msg("Bundle escrito en %s (%.1f MB, %.2f s): %d Pokémon, %d movimientos, %d objetos; salud: %s (%d errores, %d avisos)" % (
        out, os.path.getsize(out) / 1e6, time.time() - t0, len(model["pokemon"]), len(model["moves"]), len(model["items"]),
        h["status"], h["errors"], h["warnings"]))
    return model


def check(pbs_dir):
    from codex.model import ModelBuilder
    t0 = time.time()
    model = ModelBuilder(pbs_dir).build()
    dt = time.time() - t0
    h = model["meta"]["health"]
    _msg("PBS: %s" % pbs_dir)
    _msg("Modelo construido en %.2f s. Salud: %s (%d errores, %d avisos, %d notas)" % (dt, h["status"], h["errors"], h["warnings"], h.get("infos", 0)))
    _msg("Recuentos: " + ", ".join("%s=%s" % kv for kv in model["meta"]["counts"].items()))
    for f in model["files"]:
        if f["errors"] or f["warnings"] or (f["required"] and not f["exists"]):
            _msg("  %-26s %s errores, %s avisos%s" % (f["name"], f["errors"], f["warnings"], "" if f["exists"] else "  (ausente)"))
    for w in model["warnings"][:15]:
        _msg("  [%s] %s:%s %s %s" % (w["severity"], w["file"], w["line"], w["code"], w["message"]))
    mc = load_contract()
    if mc is None:
        _msg("(tools/rebalance/phase1/model_contract.py no encontrado: no se valida el contrato)")
        return 0
    problems = mc.validate_model(model)
    if problems:
        _msg("CONTRATO: %d problemas" % len(problems))
        for p in problems[:40]:
            _msg("  - " + p)
        return 1
    _msg("CONTRATO: el modelo cumple SPEC §4.1")
    return 0


def serve(pbs_dir, host, port, open_browser):
    from codex.server import make_server
    from codex.store import Store
    store = Store(pbs_dir, ROOT)
    t0 = time.time()
    entry = store.get()
    h = entry.model.get("meta", {}).get("health", {})
    _msg("Pokémon REM Master Codex")
    _msg("  PBS leído de: %s" % pbs_dir)
    _msg("  Modelo listo en %.2f s: %d Pokémon, %d movimientos, %d habilidades, %d objetos; salud del PBS: %s (%s errores, %s avisos)" % (
        time.time() - t0, len(entry.model.get("pokemon", [])), len(entry.model.get("moves", [])), len(entry.model.get("abilities", [])),
        len(entry.model.get("items", [])), h.get("status"), h.get("errors"), h.get("warnings")))
    if entry.source == "bundle":
        _msg("  AVISO: no se pudo leer PBS/; se sirve la copia de seguridad codex_bundle/model.json")
    srv, p = make_server(store, host, port)
    if p != port:
        _msg("  El puerto %d está ocupado; se usa el %d." % (port, p))
    url = "http://%s:%d/" % (host, p)
    _msg("  Abre %s  (Ctrl+C para salir)" % url)
    if not os.path.isfile(os.path.join(ROOT, "pokedex_app", "index.html")):
        _msg("  Nota: pokedex_app/index.html todavía no existe; se muestra la página de desarrollo codex/dev_index.html")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever(poll_interval=0.3)
    except KeyboardInterrupt:
        _msg("\nCodex detenido.")
    finally:
        srv.server_close()
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0].isdigit():                    # compatibilidad con «run_pokedex.py 8000»
        argv = ["--port", argv[0]] + argv[1:]
    ap = argparse.ArgumentParser(description="Pokémon REM Master Codex: servidor local de consulta del PBS en vivo.")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT, help="puerto (por defecto %d; si está ocupado se prueba el siguiente)" % DEFAULT_PORT)
    ap.add_argument("--host", default="127.0.0.1", help="dirección de escucha (por defecto 127.0.0.1)")
    ap.add_argument("--no-browser", action="store_true", help="no abrir el navegador")
    ap.add_argument("--pbs-dir", default=None, help="carpeta PBS a leer (por defecto PBS/ o la variable REM_PBS_DIR)")
    ap.add_argument("--build-bundle", action="store_true", help="genera codex_bundle/model.json a partir del PBS y sale")
    ap.add_argument("--check", action="store_true", help="construye y valida el modelo contra el contrato y sale")
    args = ap.parse_args(argv)
    if sys.version_info < (3, 8):
        _msg("Se necesita Python 3.8 o superior.")
        return 2
    pbs_dir = resolve_pbs_dir(args.pbs_dir)
    if args.build_bundle:
        build_bundle(pbs_dir)
        return 0
    if args.check:
        return check(pbs_dir)
    return serve(pbs_dir, args.host, args.port, not args.no_browser)


if __name__ == "__main__":
    sys.exit(main())
