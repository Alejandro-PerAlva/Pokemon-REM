/* ==========================================================================
 * Pokémon REM Master Codex — core.js
 * Núcleo: espacio de nombres REM, estado, eventos, API, router por hash,
 * constructor DOM (REM.h), formateadores e índices.  JS clásico, sin
 * dependencias, funciona offline.
 *
 * CONTRATO (SPEC §5) — no cambiar firmas:
 *   REM.state = {model, version, route, ...}
 *   REM.api.load() / reload() / poll()          (devuelven Promise / void)
 *   REM.on(ev, fn) / REM.emit(ev, data)         eventos: 'model','route','warnings'
 *   REM.router.register(prefix, {title, render(el, parts, query), exists?})
 *       - prefix = primer segmento del hash ('pokemon','moves','' = inicio…)
 *       - parts  = segmentos DESPUÉS del prefijo, ya decodificados
 *                  (#/pokemon/25 -> ['25'];  #/location/RUTA_01 -> ['RUTA_01']).
 *                  parts.all = todos los segmentos; parts.prefix = prefijo.
 *       - query  = objeto plano con ?a=1&b=2
 *       - render puede devolver una Promise y/o una función de limpieza.
 *       - title  = string o función (parts, query) -> string.
 *       - exists = (opcional) función (parts, query) -> bool para REM.router.exists.
 *   REM.router.go('#/pokemon/1')   REM.router.href(kind, id) -> '#/…'
 *   REM.router.exists(hash) -> true solo si la entidad existe en el modelo
 *   REM.h(tag, attrs, ...children)  (admite 'div.clase#id')   REM.esc(str)
 *   REM.fmtRange([a,b])  REM.pct(n)  REM.num(n)
 *   REM.idx = {pokemonByDex, pokemonBySym, moveBySym, abilityBySym, itemBySym,
 *              tmByNum, locByKey, charByKey, chapterByKey, shopByKey, typeBySym,
 *              stepByNum, missionByN, ...}
 *   REM.selftest.add(sección, ['#/…'] | () => ['#/…'])
 * Extras útiles: REM.norm, REM.ent(kind,id), REM.label(kind,id), REM.util.*,
 *   REM.fail(ctx, err) (único camino para errores reales de consola).
 * ========================================================================== */
(function (global) {
  'use strict';

  var REM = global.REM = global.REM || {};
  REM.VERSION = '1.0.0';

  /* ------------------------------------------------------------------ *
   * Diagnóstico: errores reales (los recoge el arnés #/selftest)
   * ------------------------------------------------------------------ */
  REM.diag = { errors: [], brokenImages: [], deadRefs: [], consoleErrors: [] };
  /* En modo autoprueba se parchea console.error desde el primer instante. */
  if (/^#\/selftest/.test(global.location ? global.location.hash : '') && global.console && console.error) {
    var origConsoleError = console.error;
    console.error = function () {
      try { REM.diag.consoleErrors.push(Array.prototype.map.call(arguments, function (a) { return (a && a.message) ? a.message : String(a); }).join(' ').slice(0, 300)); } catch (e) { /* ok */ }
      return origConsoleError.apply(console, arguments);
    };
  }
  REM.fail = function (ctx, err) {
    try {
      REM.diag.errors.push({
        ctx: String(ctx),
        message: (err && err.message) ? String(err.message) : String(err),
        stack: err && err.stack ? String(err.stack).split('\n').slice(0, 4).join(' | ') : ''
      });
      if (REM.diag.errors.length > 200) REM.diag.errors.shift();
      if (global.console && console.error) console.error('[REM] ' + ctx, err);
    } catch (e) { /* nunca romper por registrar */ }
  };

  /* ------------------------------------------------------------------ *
   * Estado y eventos
   * ------------------------------------------------------------------ */
  REM.state = {
    model: null, version: null, route: null,
    loading: false, error: null, lastLoad: null, lastPoll: null, online: true,
    selftest: /^#\/selftest/.test(global.location ? global.location.hash : '')
  };

  var handlers = Object.create(null);
  REM.on = function (ev, fn) {
    (handlers[ev] = handlers[ev] || []).push(fn);
    return function () { REM.off(ev, fn); };
  };
  REM.off = function (ev, fn) {
    var l = handlers[ev]; if (!l) return;
    var i = l.indexOf(fn); if (i >= 0) l.splice(i, 1);
  };
  REM.emit = function (ev, data) {
    (handlers[ev] || []).slice().forEach(function (fn) {
      try { fn(data); } catch (e) { REM.fail('manejador de «' + ev + '»', e); }
    });
  };

  /* ------------------------------------------------------------------ *
   * Utilidades puras
   * ------------------------------------------------------------------ */
  var HTML_ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  REM.esc = function (s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return HTML_ESC[c]; });
  };

  /* Normaliza para búsqueda: minúsculas, sin tildes, sin signos raros. */
  REM.norm = function (s) {
    if (s == null) return '';
    s = String(s).toLowerCase();
    try { s = s.normalize('NFD').replace(/[̀-ͯ]/g, ''); } catch (e) { /* ok */ }
    return s.replace(/[’'`´]/g, '').replace(/\s+/g, ' ').trim();
  };

  function groupInt(str) {
    return str.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  }
  REM.num = function (n, dec) {
    if (n == null || n === '' || (typeof n === 'number' && !isFinite(n))) return '—';
    var v = Number(n);
    if (isNaN(v)) return String(n);
    var d = dec == null ? 2 : dec;
    var neg = v < 0; v = Math.abs(v);
    var s = v.toFixed(d);
    if (s.indexOf('.') >= 0) s = s.replace(/0+$/, '').replace(/\.$/, '');
    var p = s.split('.');
    var out = groupInt(p[0]) + (p[1] ? ',' + p[1] : '');
    return (neg ? '−' : '') + out;
  };
  REM.pct = function (n) {
    if (n == null || n === '' || isNaN(Number(n))) return '—';
    return REM.num(n, 1) + '%';
  };
  REM.fmtRange = function (r) {
    if (r == null || r === '') return '—';
    if (typeof r === 'number') return String(r);
    if (typeof r === 'string') {
      var m = /^\s*(\d+)\s*[-–—]\s*(\d+)\s*$/.exec(r);
      if (!m) return r.trim() || '—';
      r = [Number(m[1]), Number(m[2])];
    }
    if (!Array.isArray(r) || !r.length) return '—';
    var a = r[0], b = r.length > 1 ? r[1] : r[0];
    if (a == null && b == null) return '—';
    if (a == null) return String(b);
    if (b == null || a === b) return String(a);
    return a + '–' + b;
  };
  REM.pad3 = function (n) { n = String(n); while (n.length < 3) n = '0' + n; return n; };
  REM.pad2 = function (n) { n = String(n); return n.length < 2 ? '0' + n : n; };

  var collator;
  try { collator = new Intl.Collator('es', { sensitivity: 'base', numeric: true }); } catch (e) { collator = null; }
  REM.collate = function (a, b) {
    a = a == null ? '' : String(a); b = b == null ? '' : String(b);
    return collator ? collator.compare(a, b) : (a < b ? -1 : a > b ? 1 : 0);
  };

  REM.util = {
    debounce: function (fn, ms) {
      var t; return function () {
        var ctx = this, args = arguments; clearTimeout(t);
        t = setTimeout(function () { fn.apply(ctx, args); }, ms == null ? 160 : ms);
      };
    },
    uniq: function (a) { return Array.from(new Set(a)); },
    sum: function (a) { return a.reduce(function (x, y) { return x + (Number(y) || 0); }, 0); },
    groupBy: function (a, keyFn) {
      var o = {}; (a || []).forEach(function (x) { var k = keyFn(x); (o[k] = o[k] || []).push(x); }); return o;
    },
    clamp: function (v, lo, hi) { return Math.min(hi, Math.max(lo, v)); },
    copy: function (text) {
      text = String(text == null ? '' : text);
      function fallback() {
        try {
          var ta = document.createElement('textarea'); ta.value = text; ta.setAttribute('readonly', '');
          ta.style.cssText = 'position:fixed;opacity:0;left:-9999px'; document.body.appendChild(ta);
          ta.select(); var ok = document.execCommand('copy'); document.body.removeChild(ta); return ok;
        } catch (e) { return false; }
      }
      try {
        if (navigator.clipboard && navigator.clipboard.writeText && global.isSecureContext !== false) {
          return navigator.clipboard.writeText(text).then(function () { return true; }, function () { return fallback(); });
        }
      } catch (e) { /* cae al fallback */ }
      return Promise.resolve(fallback());
    },
    store: {
      get: function (k, d) { try { var v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } },
      set: function (k, v) { try { localStorage.setItem(k, v); return true; } catch (e) { return false; } },
      del: function (k) { try { localStorage.removeItem(k); } catch (e) { /* ok */ } }
    },
    /* BST, etc. */
    slug: function (s) { return REM.norm(s).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''); }
  };

  /* ------------------------------------------------------------------ *
   * REM.h — constructor DOM seguro (nunca interpreta HTML)
   * ------------------------------------------------------------------ */
  var SVG_NS = 'http://www.w3.org/2000/svg';
  var SVG_TAGS = { svg: 1, g: 1, path: 1, circle: 1, ellipse: 1, rect: 1, line: 1, polyline: 1, polygon: 1,
    text: 1, tspan: 1, defs: 1, marker: 1, use: 1, image: 1, title: 0, linearGradient: 1, stop: 1, clipPath: 1, pattern: 1, filter: 1, mask: 1 };
  var BOOL_PROPS = { checked: 1, selected: 1, disabled: 1, readOnly: 1, multiple: 1, required: 1, autofocus: 1, open: 1, hidden: 1 };
  var TAG_RE = /^([A-Za-z][A-Za-z0-9]*)?((?:[.#][\w-]+)*)$/;

  function appendChild(el, c) {
    if (c == null || c === false || c === true) return;
    if (Array.isArray(c)) { for (var i = 0; i < c.length; i++) appendChild(el, c[i]); return; }
    if (c.nodeType) { el.appendChild(c); return; }
    el.appendChild(document.createTextNode(String(c)));
  }
  REM.h = function (tag, attrs) {
    var children = Array.prototype.slice.call(arguments, 2);
    if (attrs != null && (typeof attrs !== 'object' || attrs.nodeType || Array.isArray(attrs))) {
      children.unshift(attrs); attrs = null;
    }
    var m = TAG_RE.exec(String(tag || 'div'));
    var name = (m && m[1]) || 'div', extra = (m && m[2]) || '';
    var isSvg = SVG_TAGS[name] === 1;
    var el = isSvg ? document.createElementNS(SVG_NS, name) : document.createElement(name);
    if (extra) {
      var classes = [];
      extra.replace(/([.#])([\w-]+)/g, function (_, k, v) { if (k === '#') el.id = v; else classes.push(v); return ''; });
      if (classes.length) el.setAttribute('class', classes.join(' '));
    }
    if (attrs) {
      for (var k in attrs) {
        if (!Object.prototype.hasOwnProperty.call(attrs, k)) continue;
        var v = attrs[k];
        if (v == null || v === false) continue;
        if (k === 'class' || k === 'className') {
          var cv = Array.isArray(v) ? v.filter(Boolean).join(' ') : String(v);
          if (extra && el.getAttribute('class')) cv = el.getAttribute('class') + ' ' + cv;
          el.setAttribute('class', cv);
        } else if (k === 'style') {
          if (typeof v === 'string') el.style.cssText += v;
          else Object.keys(v).forEach(function (sk) {
            if (sk.indexOf('--') === 0) el.style.setProperty(sk, v[sk]); else el.style[sk] = v[sk];
          });
        } else if (k === 'dataset') {
          Object.keys(v).forEach(function (dk) { if (v[dk] != null) el.dataset[dk] = v[dk]; });
        } else if (k === 'html' || k === 'innerHTML') {
          /* deliberadamente ignorado: los textos del PBS jamás se inyectan como HTML */
        } else if (k.length > 2 && k.charAt(0) === 'o' && k.charAt(1) === 'n' && typeof v === 'function') {
          el.addEventListener(k.slice(2).toLowerCase(), v);
        } else if (k === 'ref' && typeof v === 'function') {
          v(el);
        } else if (!isSvg && BOOL_PROPS[k]) {
          el[k] = !!v; if (v) el.setAttribute(k.toLowerCase(), '');
        } else if (!isSvg && k === 'value') {
          el.value = v; el.setAttribute('value', v);
        } else if (v === true) {
          el.setAttribute(k, '');
        } else {
          el.setAttribute(k, String(v));
        }
      }
    }
    for (var i = 0; i < children.length; i++) appendChild(el, children[i]);
    return el;
  };
  REM.frag = function () {
    var f = document.createDocumentFragment();
    for (var i = 0; i < arguments.length; i++) appendChild(f, arguments[i]);
    return f;
  };
  REM.clear = function (el) { while (el && el.firstChild) el.removeChild(el.firstChild); return el; };
  var h = REM.h;

  /* ------------------------------------------------------------------ *
   * Índices (se reconstruyen en cada carga del modelo)
   * ------------------------------------------------------------------ */
  REM.idx = {};

  function buildIdx(m) {
    var ix = REM.idx;
    Object.keys(ix).forEach(function (k) { delete ix[k]; });
    ix.pokemonByDex = {}; ix.pokemonBySym = {}; ix.pokemonByName = {};
    ix.moveBySym = {}; ix.moveById = {}; ix.abilityBySym = {}; ix.itemBySym = {}; ix.itemById = {};
    ix.tmByNum = {}; ix.tmBySym = {}; ix.locByKey = {}; ix.charByKey = {}; ix.chapterByKey = {};
    ix.shopByKey = {}; ix.typeBySym = {}; ix.stepByNum = {}; ix.missionByN = {};
    ix.assets = { icons: null, battlers: null, back: null, shiny: null, shinyBack: null, itemIcons: null };
    (m.types || []).forEach(function (t) { ix.typeBySym[t.sym] = t; });
    (m.pokemon || []).forEach(function (p) {
      ix.pokemonByDex[p.dex] = p; ix.pokemonBySym[p.sym] = p; ix.pokemonByName[REM.norm(p.name)] = p;
    });
    (m.moves || []).forEach(function (x) { ix.moveBySym[x.sym] = x; if (x.id != null) ix.moveById[x.id] = x; });
    (m.abilities || []).forEach(function (x) { ix.abilityBySym[x.sym] = x; });
    (m.items || []).forEach(function (x) { ix.itemBySym[x.sym] = x; if (x.id != null) ix.itemById[x.id] = x; });
    (m.tms || []).forEach(function (x) { ix.tmByNum[x.number] = x; if (x.sym) ix.tmBySym[x.sym] = x; });
    (m.locations || []).forEach(function (x) { ix.locByKey[x.key] = x; });
    (m.characters || []).forEach(function (x) { ix.charByKey[x.key] = x; });
    (m.story || []).forEach(function (x) { ix.chapterByKey[x.key] = x; });
    if (m.prelude && m.prelude.key) ix.chapterByKey[m.prelude.key] = m.prelude;
    else if (m.prelude) ix.chapterByKey.PRELUDE = m.prelude;
    (m.shops || []).forEach(function (x) { ix.shopByKey[x.key] = x; });
    (m.progression || []).forEach(function (x) { ix.stepByNum[x.step] = x; });
    (m.missions || []).forEach(function (x) { ix.missionByN[x.n] = x; });
    var a = m.assets || {};
    function toSet(l) { return Array.isArray(l) ? new Set(l) : null; }
    ix.assets.icons = toSet(a.icons); ix.assets.battlers = toSet(a.battlers);
    ix.assets.back = toSet(a.battlersBack); ix.assets.shiny = toSet(a.battlersShiny);
    ix.assets.shinyBack = toSet(a.battlersShinyBack);
    ix.assets.itemIcons = toSet(a.itemIcons);
  }

  /* Devuelve la entidad del modelo por tipo e id (o undefined). */
  REM.ent = function (kind, id) {
    var ix = REM.idx; if (!ix || !ix.pokemonByDex || id == null) return undefined;
    switch (kind) {
      case 'pokemon':
        if (typeof id === 'object') return id;
        return ix.pokemonByDex[Number(id)] || ix.pokemonBySym[String(id).toUpperCase()];
      case 'move': return ix.moveBySym[id] || ix.moveBySym[String(id).toUpperCase()];
      case 'ability': return ix.abilityBySym[id] || ix.abilityBySym[String(id).toUpperCase()];
      case 'item': return ix.itemBySym[id] || ix.itemBySym[String(id).toUpperCase()];
      case 'tm':
        var s = String(id), n = /^\s*(?:TM|MT)?\s*0*(\d+)\s*$/i.exec(s);
        return n ? ix.tmByNum[Number(n[1])] : undefined;
      case 'location': return ix.locByKey[id];
      case 'character': return ix.charByKey[id];
      case 'chapter': return ix.chapterByKey[id];
      case 'step': return ix.stepByNum[Number(id)];
      case 'shop': return ix.shopByKey[id];
      case 'mission': return ix.missionByN[Number(id)];
      case 'type': return ix.typeBySym[id];
    }
    return undefined;
  };

  function pad2(n) { n = String(n); return n.length < 2 ? '0' + n : n; }
  /* Etiqueta legible por defecto de una entidad. */
  REM.label = function (kind, id) {
    var e = REM.ent(kind, id);
    if (!e) return id == null ? '—' : String(id);
    switch (kind) {
      case 'pokemon': case 'move': case 'ability': case 'location': case 'character': return e.name || String(id);
      case 'item': return e.name || String(id);
      case 'tm': return e.name || ('MT' + pad2(e.number));
      case 'chapter': return e.title || String(id);
      case 'step': return 'Paso ' + e.step;
      case 'shop': return e.name || String(id);
      case 'mission': return 'Misión ' + e.n + (e.title ? ': ' + e.title : '');
      case 'type': return e.name || String(id);
    }
    return String(id);
  };

  /* ------------------------------------------------------------------ *
   * API: carga del modelo, recarga en vivo, sondeo de versión
   * ------------------------------------------------------------------ */
  function fetchJson(url, opts) {
    opts = opts || {}; opts.cache = 'no-store';
    return fetch(url, opts).then(function (r) {
      if (!r.ok) throw new Error(url + ' → HTTP ' + r.status);
      var ver = r.headers.get('X-REM-Version');
      return r.json().then(function (data) { return { data: data, version: ver }; });
    });
  }

  var knownPollVersion = null, pollTimer = null, loadPromise = null;

  function setModel(model, headerVersion) {
    var m = model || {};
    m.meta = m.meta || {};
    m.meta.counts = m.meta.counts || {};
    m.meta.health = m.meta.health || { status: 'ok', errors: 0, warnings: 0 };
    m.warnings = m.warnings || []; m.files = m.files || [];
    ['pokemon', 'moves', 'abilities', 'items', 'tms', 'locations', 'shops', 'missions', 'progression', 'characters', 'story', 'types', 'ledger']
      .forEach(function (k) { if (!Array.isArray(m[k])) m[k] = []; });
    REM.state.model = m;
    REM.state.version = headerVersion || m.meta.version || null;
    REM.state.lastLoad = Date.now();
    REM.state.error = null;
    buildIdx(m);
  }

  var api = REM.api = {
    /* Carga (o recarga) el modelo. opts.preserve = conserva ruta y scroll. */
    load: function (opts) {
      opts = opts || {};
      if (loadPromise) return loadPromise;
      var S = REM.state, firstTime = !S.model, scrollY = global.scrollY || 0;
      S.loading = true;
      loadPromise = fetchJson('/api/model').catch(function (e1) {
        return fetchJson('/api/bundle').then(function (r) { r.fallback = true; return r; }, function (e2) {
          var err = new Error('No se pudo cargar el modelo (' + e1.message + '; ' + e2.message + ')');
          err.cause = e2; throw err;
        });
      }).then(function (res) {
        setModel(res.data, res.version);
        if (res.fallback) res.data.meta.source = res.data.meta.source || 'bundle';
        S.loading = false; loadPromise = null;
        REM.emit('model', S.model);
        REM.emit('warnings', { warnings: S.model.warnings, health: S.model.meta.health, files: S.model.files });
        if (!firstTime || opts.render !== false) {
          return REM.router.render({ preserveScroll: !!opts.preserve || !firstTime }).then(function () {
            if (opts.preserve) global.scrollTo(0, scrollY);
            return S.model;
          });
        }
        return S.model;
      }, function (err) {
        S.loading = false; loadPromise = null; S.error = err;
        REM.emit('error', err);
        if (!S.model) REM.router.showLoadError(err);
        throw err;
      });
      return loadPromise;
    },
    /* POST /api/reload y recarga del modelo. */
    reload: function () {
      var S = REM.state;
      return fetch('/api/reload', { method: 'POST', cache: 'no-store' })
        .then(function (r) { return r.ok ? r.json().catch(function () { return {}; }) : {}; }, function () { return {}; })
        .then(function (info) {
          if (info && info.version) knownPollVersion = info.version;
          return api.load({ preserve: true });
        }).then(function (m) { return m; }, function (e) { throw e; });
    },
    /* Sondea /api/version cada 3 s; si cambia, avisa y recarga. */
    poll: function (ms) {
      if (pollTimer || REM.state.selftest) return;
      function tick() {
        if (document.hidden || REM.state.loading) return;
        fetch('/api/version', { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (v) {
          if (!v) return;
          REM.state.online = true; REM.state.lastPoll = Date.now();
          if (knownPollVersion == null) { knownPollVersion = v.version; return; }
          if (v.version !== knownPollVersion) {
            knownPollVersion = v.version;
            if (REM.ui && REM.ui.toast) REM.ui.toast('PBS modificado: recargando…', 'info');
            api.load({ preserve: true }).then(function () {
              var hh = REM.state.model.meta.health || {};
              if (REM.ui && REM.ui.toast) REM.ui.toast('Modelo actualizado (' + (hh.errors || 0) + ' errores, ' + (hh.warnings || 0) + ' avisos)', hh.errors ? 'warn' : 'ok');
            }, function () { /* ya mostrado en load */ });
          }
          REM.emit('poll', v);
        }).catch(function () {
          if (REM.state.online) { REM.state.online = false; REM.emit('poll', null); }
        });
      }
      pollTimer = setInterval(tick, ms || 3000);
    },
    stopPoll: function () { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } }
  };

  /* ------------------------------------------------------------------ *
   * Router por hash
   * ------------------------------------------------------------------ */
  var routes = Object.create(null);
  var renderToken = 0, cleanupFn = null;

  function safeDecode(s) { try { return decodeURIComponent(s); } catch (e) { return s; } }

  function parse(hash) {
    hash = String(hash == null ? (global.location.hash || '#/') : hash);
    var raw = hash.replace(/^#/, '');
    var q = '', qi = raw.indexOf('?');
    if (qi >= 0) { q = raw.slice(qi + 1); raw = raw.slice(0, qi); }
    var segs = raw.split('/').filter(function (x) { return x !== ''; }).map(safeDecode);
    var query = {};
    q.split('&').forEach(function (kv) {
      if (!kv) return; var i = kv.indexOf('=');
      var k = safeDecode((i < 0 ? kv : kv.slice(0, i)).replace(/\+/g, ' '));
      query[k] = i < 0 ? '' : safeDecode(kv.slice(i + 1).replace(/\+/g, ' '));
    });
    var prefix = segs.length ? segs[0] : '';
    var parts = segs.slice(1); parts.all = segs; parts.prefix = prefix;
    return { hash: '#/' + segs.map(encodeURIComponent).join('/') + (q ? '?' + q : ''), prefix: prefix, parts: parts, query: query };
  }

  function container() { return document.getElementById('view'); }

  var EXISTS = {
    pokemon: function (p) { return !!REM.ent('pokemon', p[0]); },
    move: function (p) { return !!REM.ent('move', p[0]); },
    ability: function (p) { return !!REM.ent('ability', p[0]); },
    item: function (p) { return !!REM.ent('item', p[0]); },
    tm: function (p) { return !!REM.ent('tm', p[0]); },
    location: function (p) { return !!REM.ent('location', p[0]); },
    character: function (p) { return !!REM.ent('character', p[0]); },
    story: function (p) { return !p.length || !!REM.ent('chapter', p[0]); },
    progression: function (p) { return !p.length || !!REM.ent('step', p[0]); },
    shops: function (p) { return !p.length || !!REM.ent('shop', p[0]); },
    missions: function (p) { return !p.length || !!REM.ent('mission', p[0]); },
    characters: function (p) { return !p.length || !!REM.ent('character', p[0]); },
    items: function (p) { return !p.length; },
    moves: function (p) { return !p.length; },
    abilities: function (p) { return !p.length; }
  };

  var router = REM.router = {
    register: function (prefix, def) {
      def = def || {};
      routes[prefix] = def;
      (def.aliases || []).forEach(function (a) { routes[a] = def; });
      return def;
    },
    routes: routes,
    parse: parse,
    container: container,
    href: function (kind, id) {
      var e, enc = encodeURIComponent;
      switch (kind) {
        case 'pokemon': e = REM.ent('pokemon', id); return '#/pokemon/' + (e ? e.dex : enc(id));
        case 'move': return '#/move/' + enc(id);
        case 'ability': return '#/ability/' + enc(id);
        case 'item': return '#/item/' + enc(id);
        case 'tm': e = REM.ent('tm', id); return '#/tm/' + (e ? e.number : enc(String(id).replace(/^(TM|MT)/i, '').replace(/^0+(?=\d)/, '')));
        case 'location': return '#/location/' + enc(id);
        case 'character': return '#/character/' + enc(id);
        case 'chapter': return '#/story/' + enc(id);
        case 'step': return '#/progression/' + enc(id);
        case 'shop': return '#/shops/' + enc(id);
        case 'mission': return '#/missions/' + enc(id);
        case 'home': return '#/';
        default: return '#/' + kind + (id != null && id !== '' ? '/' + enc(id) : '');
      }
    },
    go: function (hash, opts) {
      hash = String(hash || '#/');
      if (hash.charAt(0) !== '#') hash = '#' + hash;
      if (opts && opts.replace) { try { history.replaceState(null, '', hash); } catch (e) { global.location.hash = hash; } router.render(); return; }
      if (global.location.hash === hash) router.render({ preserveScroll: true }); else global.location.hash = hash;
    },
    /* ¿existe esta ruta con una entidad real del modelo? */
    exists: function (hash) {
      var r = parse(hash), def = routes[r.prefix];
      if (!def) return false;
      try {
        if (typeof def.exists === 'function') return !!def.exists(r.parts, r.query);
        if (EXISTS[r.prefix]) return !!EXISTS[r.prefix](r.parts, r.query);
        return true;
      } catch (e) { return false; }
    },
    /* Renderiza la ruta actual (o la indicada) en el contenedor. Devuelve Promise<{ok,…}>. */
    render: function (opts) {
      opts = opts || {};
      var r = parse(opts.hash != null ? opts.hash : global.location.hash);
      var def = routes[r.prefix];
      var my = ++renderToken, el = container();
      if (!el) return Promise.resolve({ ok: false });
      if (cleanupFn) { try { cleanupFn(); } catch (e) { /* ok */ } cleanupFn = null; }
      r.def = def || null;
      REM.state.route = r;
      var res = { ok: true, hash: r.hash };
      var finish = function () { REM.emit('route', r); return res; };
      el.className = 'view view-' + (r.prefix || 'home');
      if (!def) {
        REM.clear(el).appendChild(notFoundEl(r)); setTitle('Página no encontrada');
        res.ok = false; res.notFound = true; return Promise.resolve(finish());
      }
      if (!REM.state.model && !def.noModel) {
        if (!REM.state.error) REM.clear(el).appendChild(h('div.boot', { role: 'status' }, 'Cargando datos del Codex…'));
        res.ok = false; res.pending = true; return Promise.resolve(res);
      }
      var title = def.title;
      try { if (typeof title === 'function') title = title(r.parts, r.query); } catch (e) { title = ''; }
      setTitle(title || '');
      if (!opts.preserveScroll) { try { global.scrollTo(0, 0); } catch (e) { /* ok */ } }
      REM.clear(el);
      var ret;
      try {
        ret = def.render(el, r.parts, r.query);
      } catch (e) {
        res = renderFail(el, r, e);
        return Promise.resolve(finish());
      }
      return Promise.resolve(ret).then(function (cleanup) {
        if (my !== renderToken) { if (typeof cleanup === 'function') try { cleanup(); } catch (e) { /* ok */ } return res; }
        if (typeof cleanup === 'function') cleanupFn = cleanup;
        return finish();
      }, function (e) {
        if (my !== renderToken) return res;
        res = renderFail(el, r, e);
        return finish();
      });
    },
    /* Renderiza una ruta sin tocar location.hash (arnés de autoprueba). */
    visit: function (hash, opts) {
      opts = opts || {}; opts.hash = hash; opts.preserveScroll = true;
      return router.render(opts);
    },
    showLoadError: function (err) {
      var el = container(); if (!el) return;
      el.className = 'view view-error';
      REM.clear(el).appendChild(h('section.load-error', { role: 'alert' },
        h('div.load-error__icon', { 'aria-hidden': 'true' }, '🔌'),
        h('h1', 'No se pudieron cargar los datos'),
        h('p', 'El Codex necesita el servidor local para leer el PBS. Comprueba que ',
          h('code', 'python3 start_codex.py'), ' sigue en marcha y vuelve a intentarlo.'),
        h('p.muted.small', String(err && err.message || err)),
        h('div.load-error__actions',
          h('button.btn.btn--primary', { type: 'button', onclick: function () {
            el.firstChild && el.firstChild.classList.add('is-busy');
            REM.api.load().catch(function () { /* el error se vuelve a mostrar */ });
          } }, 'Reintentar'))));
    }
  };

  function setTitle(t) {
    document.title = (t ? t + ' · ' : '') + 'Pokémon REM Master Codex';
  }
  router.setTitle = setTitle;

  function renderFail(el, r, e) {
    REM.fail('vista «' + r.hash + '»', e);
    REM.clear(el).appendChild(h('section.view-error-card', { role: 'alert' },
      h('h1', 'No se pudo mostrar esta vista'),
      h('p', 'Ha ocurrido un error al construir la página. El resto del Codex sigue funcionando.'),
      h('details', h('summary', 'Detalle técnico'), h('pre', String(e && (e.stack || e.message) || e))),
      h('p', h('a.btn', { href: '#/' }, 'Volver al inicio'))));
    return { ok: false, hash: r.hash, error: e };
  }

  function notFoundEl(r) {
    return h('section.view-error-card',
      h('h1', 'Página no encontrada'),
      h('p', 'No existe la ruta ', h('code', r.hash), '.'),
      h('p', h('a.btn.btn--primary', { href: '#/' }, 'Ir al inicio'), ' ', h('a.btn', { href: '#/pokedex' }, 'Pokédex Maestra')));
  }
  router.notFound = notFoundEl;

  /* ------------------------------------------------------------------ *
   * Registro de rutas de autoprueba (la consume js/selftest.js)
   * ------------------------------------------------------------------ */
  REM.selftest = {
    sections: [],
    add: function (section, hashesOrFn) {
      this.sections.push({ section: String(section), src: hashesOrFn });
    },
    /* Resuelve todo a [{section, hash}] (tras cargar el modelo). */
    resolve: function () {
      var out = [];
      this.sections.forEach(function (s) {
        var list;
        try { list = typeof s.src === 'function' ? s.src() : s.src; } catch (e) { REM.fail('selftest.add(' + s.section + ')', e); list = []; }
        (list || []).forEach(function (hs) { if (hs) out.push({ section: s.section, hash: hs }); });
      });
      return out;
    }
  };

  /* Marcador: view_*.js registran sus rutas con REM.router.register; la ruta
     inicial se resuelve al arrancar (DOMContentLoaded). */

  /* Búsqueda: search.js sustituye estos stubs. */
  REM.search = REM.search || {
    query: function () { return []; },
    open: function () { /* search.js lo implementa */ }
  };

  /* ------------------------------------------------------------------ *
   * Arranque
   * ------------------------------------------------------------------ */
  var booted = false;
  REM.boot = function () {
    if (booted) return; booted = true;
    try { if (REM.shell && REM.shell.init) REM.shell.init(); } catch (e) { REM.fail('shell', e); }
    global.addEventListener('hashchange', function () { router.render(); });
    var el = container();
    if (el && !(location.hash)) { try { history.replaceState(null, '', '#/'); } catch (e) { /* ok */ } }
    api.load({ render: true }).then(function () {
      if (!REM.state.selftest) api.poll();
    }, function () { /* la pantalla de error ya está visible; reintento manual */ });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', REM.boot);
  else setTimeout(REM.boot, 0);

  /* Errores globales no capturados: se registran para el arnés. */
  global.addEventListener('error', function (ev) {
    try {
      REM.diag.errors.push({ ctx: 'window.onerror', message: String(ev.message || (ev.error && ev.error.message) || 'error'),
        stack: (ev.filename || '') + ':' + (ev.lineno || '') });
    } catch (e) { /* ok */ }
  });
  global.addEventListener('unhandledrejection', function (ev) {
    try {
      var r = ev.reason;
      REM.diag.errors.push({ ctx: 'unhandledrejection', message: String(r && r.message || r), stack: r && r.stack ? String(r.stack).split('\n').slice(0, 3).join(' | ') : '' });
    } catch (e) { /* ok */ }
  });
})(window);
