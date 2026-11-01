"""Servidor HTTP local (solo biblioteca estándar) del Pokémon REM Master Codex. Contrato: tools/codex/SPEC.md §4."""
import json
import mimetypes
import os
import sys
import threading
import time
import traceback
from email.utils import formatdate
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

from . import ROOT, __version__
from .store import Store, dumps

APP_DIR = os.path.join(ROOT, "pokedex_app")
GFX_DIR = os.path.join(ROOT, "Graphics")
MAP_DIRS = [os.path.join(ROOT, "docs", "Mapa"), os.path.join(ROOT, "docs", "rebalance", "assets")]
DEV_INDEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dev_index.html")

MIME = {".html": "text/html; charset=utf-8", ".htm": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
        ".mjs": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8",
        ".map": "application/json; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp", ".ico": "image/x-icon",
        ".woff": "font/woff", ".woff2": "font/woff2", ".ttf": "font/ttf", ".otf": "font/otf", ".txt": "text/plain; charset=utf-8",
        ".md": "text/plain; charset=utf-8", ".webmanifest": "application/manifest+json"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".ico"}


def mime_of(path):
    ext = os.path.splitext(path)[1].lower()
    return MIME.get(ext) or mimetypes.guess_type(path)[0] or "application/octet-stream"


def safe_path(base, rel, allowed_ext=None):
    """Ruta absoluta dentro de ``base`` o None (protege contra path traversal, NUL, símbolos que escapan, etc.)."""
    try:
        if rel is None or "\x00" in rel or "\\" in rel:
            return None
        parts = [p for p in rel.split("/") if p not in ("", ".")]
        if any(p == ".." or p.startswith("..") and set(p) == {"."} for p in parts):
            return None
        if any(p.startswith("~$") for p in parts):
            return None
        base_real = os.path.realpath(base)
        target = os.path.realpath(os.path.join(base_real, *parts)) if parts else base_real
        if os.path.commonpath([base_real, target]) != base_real:
            return None
        if allowed_ext is not None and os.path.splitext(target)[1].lower() not in allowed_ext:
            return None
        return target
    except (ValueError, OSError):
        return None


class CodexServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 64

    def __init__(self, addr, handler, store):
        super().__init__(addr, handler)
        self.store = store

    def handle_error(self, request, client_address):  # silencia desconexiones del navegador
        exc = sys.exc_info()[1]
        if isinstance(exc, (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, TimeoutError)):
            return
        sys.stderr.write("[codex] error de conexión: %s\n" % (exc.__class__.__name__,))


class Handler(BaseHTTPRequestHandler):
    server_version = "REMCodex/" + __version__
    protocol_version = "HTTP/1.1"
    timeout = 60

    # ------------------------------------------------------------------ utilidades
    def log_message(self, fmt, *args):
        pass

    def log_error(self, fmt, *args):
        pass

    @property
    def store(self):
        return self.server.store

    def _send(self, code, body=b"", ctype="application/octet-stream", headers=None, head_only=False):
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if not head_only and body:
                self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            self.close_connection = True

    def _json(self, obj, code=200, headers=None, head_only=False):
        h = {"Cache-Control": "no-store"}
        h.update(headers or {})
        self._send(code, obj if isinstance(obj, (bytes, bytearray)) else dumps(obj), "application/json; charset=utf-8", h, head_only)

    def _error(self, code, message, head_only=False):
        phrase = HTTPStatus(code).phrase if code in [s.value for s in HTTPStatus] else "Error"
        self._json({"error": message, "status": code, "reason": phrase}, code, head_only=head_only)

    def _file(self, path, head_only=False, cache="no-cache"):
        try:
            st = os.stat(path)
            if not os.path.isfile(path):
                return self._error(404, "No encontrado", head_only)
            etag = '"%x-%x"' % (st.st_mtime_ns, st.st_size)
            if self.headers.get("If-None-Match") == etag:
                return self._send(304, b"", mime_of(path), {"ETag": etag, "Cache-Control": cache}, True)
            with open(path, "rb") as f:
                data = f.read()
        except OSError:
            return self._error(404, "No encontrado", head_only)
        self._send(200, data, mime_of(path), {"ETag": etag, "Cache-Control": cache, "Last-Modified": formatdate(st.st_mtime, usegmt=True)}, head_only)

    # --------------------------------------------------------------------- métodos
    def do_HEAD(self):
        self._dispatch("HEAD")

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_PUT(self):
        self._error(405, "Método no permitido")

    do_DELETE = do_PATCH = do_PUT

    def do_OPTIONS(self):
        self._send(204, b"", "text/plain", {"Allow": "GET, HEAD, POST, OPTIONS", "Cache-Control": "no-store"})

    def _dispatch(self, method):
        head = method == "HEAD"
        try:
            # consume el cuerpo de las peticiones POST para no desincronizar la conexión
            if method == "POST":
                try:
                    n = int(self.headers.get("Content-Length") or 0)
                    if 0 < n <= 1 << 20:
                        self.rfile.read(n)
                except Exception:
                    pass
            parts = urlsplit(self.path)
            path = unquote(parts.path)
            if "\x00" in path:
                return self._error(400, "Ruta inválida", head)
            if path.startswith("/api/"):
                return self._api(method, path, head)
            if method == "POST":
                return self._error(405, "Método no permitido", head)
            if path in ("/", "/index.html"):
                return self._index(head)
            if path.startswith("/app/"):
                return self._static(APP_DIR, path[5:], head)
            if path.startswith("/gfx/"):
                return self._static(GFX_DIR, path[5:], head, IMAGE_EXT, cache="public, max-age=60")
            if path.startswith("/map/"):
                rel = path[5:]
                for d in MAP_DIRS:
                    p = safe_path(d, rel, IMAGE_EXT)
                    if p and os.path.isfile(p):
                        return self._file(p, head, cache="public, max-age=60")
                return self._error(404, "No encontrado", head)
            if path == "/favicon.ico":
                p = safe_path(APP_DIR, "favicon.ico")
                if p and os.path.isfile(p):
                    return self._file(p, head)
                return self._send(204, b"", "image/x-icon", {"Cache-Control": "no-store"}, head)
            # alternativa: estáticos de la app en la raíz (index.html con rutas relativas)
            if os.path.isdir(APP_DIR):
                p = safe_path(APP_DIR, path.lstrip("/"))
                if p and os.path.isfile(p):
                    return self._file(p, head)
            return self._error(404, "No encontrado", head)
        except Exception as e:
            sys.stderr.write("[codex] error atendiendo %s %s: %s\n" % (method, self.path, e.__class__.__name__))
            traceback.print_exc(file=sys.stderr)
            try:
                self._error(500, "Error interno del servidor", head)
            except Exception:
                self.close_connection = True

    def _index(self, head):
        p = os.path.join(APP_DIR, "index.html")
        if os.path.isfile(p):
            return self._file(p, head)
        if os.path.isfile(DEV_INDEX):
            return self._file(DEV_INDEX, head)
        body = ("<!doctype html><meta charset=utf-8><title>Pokémon REM Codex</title><h1>Pokémon REM Codex</h1>"
                "<p>La interfaz (pokedex_app/index.html) aún no existe. API disponible en <a href=/api/health>/api/health</a>.</p>").encode("utf-8")
        self._send(200, body, "text/html; charset=utf-8", {"Cache-Control": "no-store"}, head)

    def _static(self, base, rel, head, allowed_ext=None, cache="no-cache"):
        p = safe_path(base, rel, allowed_ext)
        if p is None or not os.path.isfile(p):
            return self._error(404, "No encontrado", head)
        self._file(p, head, cache)

    # ------------------------------------------------------------------------ API
    def _api(self, method, path, head):
        store = self.store
        route = path.rstrip("/")
        if route == "/api/reload":
            if method != "POST":
                return self._json({"error": "Usa POST para recargar", "status": 405}, 405, {"Allow": "POST"}, head)
            e = store.reload()
            return self._json({"ok": True, "version": e.version, "errors": e.errors, "warnings": e.warns, "source": e.source, "buildMs": e.build_ms}, head_only=head)
        if method == "POST":
            return self._error(405, "Método no permitido", head)
        if route == "/api/version":
            return self._json(store.version_info(), head_only=head)
        if route == "/api/model":
            e = store.get()
            return self._model(e, head)
        if route == "/api/warnings":
            e = store.get()
            return self._json(e.warnings_body, headers={"X-REM-Version": e.version}, head_only=head)
        if route == "/api/health":
            e = store.get()
            return self._json(e.health_body, headers={"X-REM-Version": e.version}, head_only=head)
        if route == "/api/bundle":
            be = store.bundle_entry()
            if be is None:
                return self._error(404, "No hay copia de seguridad (ejecuta: python3 start_codex.py --build-bundle)", head)
            return self._model(be, head)
        return self._error(404, "Ruta de API desconocida", head)

    def _model(self, e, head):
        accept = (self.headers.get("Accept-Encoding", "") or "").lower()
        headers = {"X-REM-Version": e.version, "Cache-Control": "no-store", "Vary": "Accept-Encoding"}
        if "gzip" in accept:
            headers["Content-Encoding"] = "gzip"
            return self._send(200, e.gzip_body(), "application/json; charset=utf-8", headers, head)
        self._send(200, e.body, "application/json; charset=utf-8", headers, head)


def make_server(store, host="127.0.0.1", port=8765, max_tries=60):
    """Crea el servidor; si el puerto está ocupado prueba el siguiente. -> (servidor, puerto)"""
    last = None
    for p in range(port, port + max_tries):
        try:
            return CodexServer((host, p), Handler, store), p
        except OSError as e:
            last = e
            continue
    raise OSError("No hay ningún puerto libre entre %d y %d: %s" % (port, port + max_tries - 1, last))
