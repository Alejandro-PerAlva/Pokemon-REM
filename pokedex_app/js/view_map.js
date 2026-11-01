/* ==========================================================================
   Pokémon REM Master Codex — Mapa interactivo de Oniria
   Ruta: #/map  (admite #/map/<KEY> y #/map?loc=<KEY>&step=<n> para preseleccionar)
   Imagen base 480×320 + capa SVG en coordenadas del mapa: 32 nodos y 32 rutas.
   Propiedad: codex-front-world. Solo usa la API pública de SPEC §5.
   ========================================================================== */
(function () {
  'use strict';
  var REM = window.REM;
  if (!REM || !REM.router) return;
  var h = REM.h;
  var esc = REM.esc;
  var MAP_URL = '/map/Mapa_Final__Esqueleto.png';
  var MAP_W = 480, MAP_H = 320, MAX_Z = 8;

  /* ---------------------------------------------------------------- utilidades */
  function model() { return (REM.state && REM.state.model) || null; }
  function arr(x) { return Array.isArray(x) ? x : []; }
  function str(x) { return x == null ? '' : String(x); }
  function idx(n) { return (REM.idx && REM.idx[n]) || {}; }
  function clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); }
  function fmtRange(r) { return REM.fmtRange ? REM.fmtRange(r) : (r && r.length ? r.join('–') : '—'); }
  function stripAcc(s) { return str(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); }
  function store(k, d) { return REM.util && REM.util.store ? REM.util.store.get(k, d) : d; }
  function storeSet(k, v) { if (REM.util && REM.util.store) REM.util.store.set(k, v); }
  function emptyMsg(msg) {
    return REM.ui && REM.ui.empty ? REM.ui.empty(msg || 'Sin datos') : h('p', { class: 'w-empty' }, msg || 'Sin datos');
  }
  function guard(label, fn, fallback) {
    try { return fn(); } catch (e) {
      if (REM.fail) REM.fail('mapa · ' + label, e);
      return fallback === undefined ? h('p', { class: 'w-empty' }, 'No se pudo mostrar esta sección.') : fallback;
    }
  }
  function rich(s) {
    s = str(s);
    var keep = [];
    s = s.replace(/\[[^\]\n]*(?:PENDIENTE|Pendiente|REVISI[ÓO]N|Revisi[óo]n)[^\]\n]*\]\*?/g, function (m) {
      keep.push(m); return '\u0001' + (keep.length - 1) + '\u0002';
    });
    s = esc(s);
    s = s.replace(/\*\*([^*\n]+?)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/(^|[^*\w])\*([^*\s][^*\n]*?)\*(?![*\w])/g, '$1<em>$2</em>');
    s = s.replace(/\u0001(\d+)\u0002/g, function (_, i) { return '<mark class="w-pending">' + esc(keep[+i]) + '</mark>'; });
    return s;
  }
  function richEl(tag, cls, text) { var e = h(tag, { class: cls || null }); e.innerHTML = rich(text); return e; }

  var CAT_ORDER = ['Ciudad', 'Pueblo', 'Lugar especial', 'Ruta normal', 'Ruta especial', 'Ruta de montaña', 'Ruta marina', 'Ruta nevada'];
  function normCat(c) {
    var k = stripAcc(c).replace(/[_\s]+/g, ' ').trim();
    var map = {
      'ciudad': 'Ciudad', 'pueblo': 'Pueblo', 'especial': 'Lugar especial', 'lugar especial': 'Lugar especial',
      'ruta normal': 'Ruta normal', 'ruta especial': 'Ruta especial', 'ruta montana': 'Ruta de montaña',
      'ruta de montana': 'Ruta de montaña', 'ruta marina': 'Ruta marina', 'ruta nevada': 'Ruta nevada'
    };
    return map[k] || str(c);
  }
  function catKind(c) {
    var k = stripAcc(normCat(c));
    if (k.indexOf('ruta') === 0) return 'route';
    if (k === 'ciudad') return 'city';
    if (k === 'pueblo') return 'town';
    return 'place';
  }
  var ACTS = ['I', 'II', 'III', 'IV', 'V'];
  function actNum(a) { var i = ACTS.indexOf(str(a).toUpperCase()); return i < 0 ? 0 : i + 1; }
  function badge(text, cls) { return h('span', { class: 'badge w-badge ' + (cls || '') }, text); }
  function firstStep(l) {
    var s = arr(l.steps).filter(function (n) { return isFinite(n); });
    if (s.length) return Math.min.apply(null, s);
    return l.order != null ? Number(l.order) : 999;
  }
  function coordsOf(l) {
    var c = l && l.coords;
    if (!c || c.length < 2) return null;
    var x = Number(c[0]), y = Number(c[1]);
    return isFinite(x) && isFinite(y) ? [x, y] : null;
  }
  function parsePath(p) {
    var pts = [];
    if (!p) return pts;
    if (typeof p === 'string') {
      p.split(';').forEach(function (s) {
        var m = s.split(',');
        if (m.length >= 2 && isFinite(+m[0]) && isFinite(+m[1])) pts.push([+m[0], +m[1]]);
      });
    } else if (Array.isArray(p)) {
      p.forEach(function (q) {
        if (Array.isArray(q) && q.length >= 2) pts.push([+q[0], +q[1]]);
        else if (q && typeof q === 'object' && 'x' in q) pts.push([+q.x, +q.y]);
      });
    }
    return pts;
  }
  /* Polilínea; los saltos entre tramos no ortogonales (el mapa solo traza en horizontal/vertical) cortan el trazo. */
  function pathD(pts) {
    var d = '';
    for (var i = 0; i < pts.length; i++) {
      var q = pts[i], pv = pts[i - 1];
      var jump = pv && pv[0] !== q[0] && pv[1] !== q[1];
      d += (i === 0 || jump ? 'M' : 'L') + q[0] + ' ' + q[1];
    }
    return d;
  }
  function svgTitle(text) {
    var t = document.createElementNS('http://www.w3.org/2000/svg', 'title');
    t.textContent = text;
    return t;
  }

  /* ---------------------------------------------------------------- brújula del mapa */
  var DIRS = [{ k: 'N', name: 'Norte' }, { k: 'E', name: 'Este' }, { k: 'S', name: 'Sur' }, { k: 'O', name: 'Oeste' }];
  function compass(loc, pick) {
    var conn = loc.conn || {}, cells = {};
    DIRS.forEach(function (d) {
      var c = conn[d.k] || {}, keys = arr(c.keys), text = str(c.text).trim(), body = [];
      keys.forEach(function (k) {
        var t = idx('locByKey')[k];
        var b = h('button', { type: 'button', class: 'w-dir-btn', title: 'Ir a ' + (t ? t.name : k) }, t ? t.name : str(k));
        if (!t) b.disabled = true;
        b.addEventListener('click', function () { pick(k); });
        body.push(b);
      });
      var tail = text.split('→').pop().trim();
      if (keys.length) {
        if (/^(cruce|nexo)/i.test(tail)) body.push(h('small', { class: 'w-dir-via' }, '↳ ' + tail));
      } else if (text) {
        body.push(h('button', { type: 'button', class: 'w-dir-btn w-dir-cross', disabled: true, title: text }, tail || text));
      }
      if (!body.length) body.push(h('button', { type: 'button', class: 'w-dir-btn w-dir-none', disabled: true }, 'Sin salida'));
      cells[d.k] = h('div', { class: 'w-dir w-dir-' + d.k, role: 'group', 'aria-label': 'Hacia el ' + d.name },
        h('span', { class: 'w-dir-head' }, h('b', { 'aria-hidden': 'true' }, d.k), h('span', { class: 'w-dir-name' }, d.name)), body);
    });
    return h('div', { class: 'w-compass', role: 'group', 'aria-label': 'Brújula: ubicaciones vecinas' },
      cells.N, cells.O,
      h('div', { class: 'w-compass-center w-center-' + catKind(loc.category) + ' w-act-bg-' + actNum(loc.act), 'aria-hidden': 'true', title: str(loc.name) },
        h('span', null, loc.node != null && loc.node !== '' ? String(loc.node) : str(loc.routeLabel) || '·')),
      cells.E, cells.S);
  }

  /* ---------------------------------------------------------------- vista principal */
  function render(el, parts, query) {
    var M = model();
    var locs = arr(M && M.locations);
    if (!M || !locs.length) {
      el.appendChild(h('div', { class: 'w-view' }, h('h1', null, 'Mapa de Oniria'), emptyMsg('Sin datos: no hay ubicaciones en el modelo.')));
      return;
    }
    var progress = arr(M.progression).slice().sort(function (a, b) { return a.step - b.step; });
    var maxStep = progress.length ? progress[progress.length - 1].step : 68;

    /* ---- estado ---- */
    var S = {
      z: 1, tx: 0, ty: 0, sel: null, hover: null, step: null,
      layers: { nodes: true, routes: true, labels: true },
      acts: {}, cat: '', q: '', moved: false
    };
    var pins = {};      // key -> {loc, g, kind, first}
    var mapped = [], unmapped = [];
    var cleanups = [];

    /* ---- construcción de elementos fijos ---- */
    var viewport = h('div', {
      class: 'w-map-viewport', tabindex: '0', role: 'application',
      'aria-label': 'Mapa interactivo de Oniria. Con el mapa enfocado: flechas para desplazar, más y menos para acercar o alejar, cero para reiniciar. Tabulador recorre las ubicaciones.'
    });
    var world = h('div', { class: 'w-map-world' });
    var img = h('img', { class: 'w-map-img', src: MAP_URL, alt: 'Mapa de la región de Oniria (480 por 320 píxeles)', draggable: 'false' });
    var svg = h('svg', { class: 'w-map-svg', viewBox: '0 0 ' + MAP_W + ' ' + MAP_H, preserveAspectRatio: 'none', focusable: 'false' });
    var gRoutes = h('g', { class: 'w-g-routes' });
    var gNodes = h('g', { class: 'w-g-nodes' });
    svg.appendChild(gRoutes); svg.appendChild(gNodes);
    world.appendChild(img); world.appendChild(svg);
    viewport.appendChild(world);
    var tip = h('div', { class: 'w-tip', role: 'tooltip', hidden: true });
    var stage = h('div', { class: 'w-map-stage' }, viewport, tip);
    var side = h('aside', { class: 'w-map-side', 'aria-label': 'Ficha rápida de la ubicación' });
    var statusLine = h('p', { class: 'w-map-status', 'aria-live': 'polite' });

    /* ---- pines ---- */
    function pinShape(kind) {
      if (kind === 'city') return h('circle', { class: 'w-shape', r: 7 });
      if (kind === 'town') return h('circle', { class: 'w-shape', r: 5.4 });
      if (kind === 'place') return h('rect', { class: 'w-shape', x: -4.4, y: -4.4, width: 8.8, height: 8.8, rx: 0.8, transform: 'rotate(45)' });
      return h('rect', { class: 'w-shape', x: -7, y: -3.8, width: 14, height: 7.6, rx: 3 });
    }
    function tipText(l) {
      var kind = catKind(l.category);
      var tag = kind === 'route' ? (l.routeLabel ? 'Ruta ' + l.routeLabel : '') : (l.node != null ? 'Nodo ' + l.node : '');
      return str(l.name) + '. ' + normCat(l.category) + (l.act ? ', acto ' + l.act : '') + (tag ? ', ' + tag : '') + '.';
    }
    function buildPin(l) {
      var c = coordsOf(l), kind = catKind(l.category), an = actNum(l.act);
      var g = h('g', {
        class: 'w-pin w-pin-' + kind + ' w-act-fill-' + an, tabindex: '0', role: 'button',
        'aria-label': tipText(l), 'aria-pressed': 'false', 'data-key': l.key
      });
      var label = kind === 'route' ? str(l.routeLabel || '') : (l.node != null && l.node !== '' ? String(l.node) : '');
      var body = h('g', { class: 'w-pin-body' },
        h('circle', { class: 'w-halo', r: kind === 'route' ? 11 : 12 }),
        pinShape(kind),
        label ? h('text', { class: 'w-pin-num', 'text-anchor': 'middle', 'dominant-baseline': 'central', y: kind === 'route' ? 0.2 : 0.3 }, label) : null,
        kind === 'route' ? null : h('text', { class: 'w-lbl w-lbl-' + kind, 'text-anchor': 'middle', y: kind === 'city' ? 13 : 11 },
          str(l.name).replace(/\s*\(.*\)$/, '')));
      g.appendChild(body);
      g.setAttribute('transform', 'translate(' + c[0] + ' ' + c[1] + ')');
      var rec = { loc: l, g: g, body: body, kind: kind, first: firstStep(l), c: c };
      pins[l.key] = rec;
      wirePin(rec, g);
      if (kind === 'route') {
        var pts = parsePath(l.path);
        if (pts.length > 1) {
          var d = pathD(pts);
          var rg = h('g', { class: 'w-route w-act-stroke-' + an, 'data-key': l.key },
            h('path', { class: 'w-route-hit', d: d, fill: 'none' }),
            h('path', { class: 'w-route-out', d: d, fill: 'none' }),
            h('path', { class: 'w-route-line', d: d, fill: 'none' }));
          rec.path = rg;
          rg.addEventListener('mouseenter', function () { showTip(rec, rec.g); setHover(l.key); });
          rg.addEventListener('mouseleave', function () { hideTip(); setHover(null); });
          rg.addEventListener('click', function () { if (S.moved) return; select(l.key); });
          gRoutes.appendChild(rg);
        }
        rec.layer = 'routes';
        gRoutes.appendChild(g);
      } else {
        rec.layer = 'nodes';
        gNodes.appendChild(g);
      }
      return rec;
    }
    function wirePin(rec, g) {
      var l = rec.loc;
      g.addEventListener('mouseenter', function () { showTip(rec, g); setHover(l.key); });
      g.addEventListener('mouseleave', function () { hideTip(); setHover(null); });
      g.addEventListener('focus', function () { showTip(rec, g); setHover(l.key); });
      g.addEventListener('blur', function () { hideTip(); setHover(null); });
      g.addEventListener('click', function (ev) { if (S.moved) { S.moved = false; return; } ev.stopPropagation(); select(l.key); });
      g.addEventListener('keydown', function (ev) {
        if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); select(l.key, { center: true }); }
      });
    }
    locs.forEach(function (l) {
      if (!coordsOf(l)) { unmapped.push(l); return; }
      mapped.push(l);
    });
    /* rutas debajo, nodos encima: se construyen en orden estable */
    mapped.slice().sort(function (a, b) { return (a.order || 0) - (b.order || 0); }).forEach(function (l) {
      guard('pin ' + l.key, function () { buildPin(l); return null; }, null);
    });

    /* ---- tooltip ---- */
    function showTip(rec, targetEl) {
      var l = rec.loc;
      tip.textContent = '';
      var lv = [];
      if (l.levelDay || l.levelNight) lv.push('☀ ' + fmtRange(l.levelDay) + '  ☾ ' + fmtRange(l.levelNight));
      tip.appendChild(h('strong', null, str(l.name)));
      tip.appendChild(h('span', { class: 'w-tip-sub' }, normCat(l.category) + (l.act ? ' · Acto ' + l.act : '')));
      tip.appendChild(h('span', { class: 'w-tip-lv' }, lv.length ? 'Niveles ' + lv[0] : 'Sin salvajes'));
      tip.hidden = false;
      var sr = stage.getBoundingClientRect(), r = targetEl.getBoundingClientRect();
      var cx = r.left + r.width / 2 - sr.left, top = r.top - sr.top, bottom = r.bottom - sr.top;
      var w = tip.offsetWidth || 180, hgt = tip.offsetHeight || 60;
      var x = clamp(cx, w / 2 + 6, Math.max(w / 2 + 6, sr.width - w / 2 - 6));
      var below = top - hgt - 12 < 0;
      tip.style.left = x + 'px';
      tip.style.top = (below ? bottom + 10 : top - 10) + 'px';
      tip.classList.toggle('w-tip-below', below);
    }
    function hideTip() { tip.hidden = true; }
    function setHover(key) {
      if (S.hover && pins[S.hover]) { pins[S.hover].g.classList.remove('is-hover'); if (pins[S.hover].path) pins[S.hover].path.classList.remove('is-hover'); }
      S.hover = key;
      if (key && pins[key]) { pins[key].g.classList.add('is-hover'); if (pins[key].path) pins[key].path.classList.add('is-hover'); }
    }

    /* ---- zoom y arrastre ---- */
    function vsize() { return { w: viewport.clientWidth || 1, h: viewport.clientHeight || 1 }; }
    function applyView() {
      var s = vsize();
      S.z = clamp(S.z, 1, MAX_Z);
      S.tx = clamp(S.tx, s.w - s.w * S.z, 0);
      S.ty = clamp(S.ty, s.h - s.h * S.z, 0);
      world.style.transform = 'translate(' + S.tx.toFixed(2) + 'px,' + S.ty.toFixed(2) + 'px) scale(' + S.z.toFixed(3) + ')';
      var k = Math.pow(S.z, -0.72);
      svg.style.setProperty('--k', k.toFixed(3));
      svg.style.setProperty('--sw', (2.1 * Math.pow(S.z, -0.45)).toFixed(3));
      var kk = k.toFixed(3);
      Object.keys(pins).forEach(function (key) { pins[key].body.setAttribute('transform', 'scale(' + kk + ')'); });
      svg.classList.toggle('w-zoomed', S.z >= 2);
      svg.classList.toggle('w-zoomed-more', S.z >= 3.2);
      zoomOut.textContent = '×' + S.z.toFixed(1).replace('.', ',');
    }
    function zoomAt(px, py, f) {
      var nz = clamp(S.z * f, 1, MAX_Z), r = nz / S.z;
      S.tx = px - (px - S.tx) * r; S.ty = py - (py - S.ty) * r; S.z = nz;
      applyView();
    }
    function zoomCenter(f) { var s = vsize(); zoomAt(s.w / 2, s.h / 2, f); }
    function centerOn(c, z) {
      var s = vsize();
      if (z) S.z = clamp(z, 1, MAX_Z);
      S.tx = s.w / 2 - (c[0] / MAP_W) * s.w * S.z;
      S.ty = s.h / 2 - (c[1] / MAP_H) * s.h * S.z;
      applyView();
    }
    function resetView() { S.z = 1; S.tx = 0; S.ty = 0; applyView(); }

    var ptrs = {}, dragStart = null, pinch = null;
    function pdist() {
      var ks = Object.keys(ptrs); if (ks.length < 2) return 0;
      var a = ptrs[ks[0]], b = ptrs[ks[1]];
      return Math.hypot(a.x - b.x, a.y - b.y);
    }
    viewport.addEventListener('pointerdown', function (ev) {
      if (ev.pointerType === 'mouse' && ev.button !== 0) return;
      S.moved = false;
      ptrs[ev.pointerId] = { x: ev.clientX, y: ev.clientY };
      if (Object.keys(ptrs).length === 1) dragStart = { x: ev.clientX, y: ev.clientY, tx: S.tx, ty: S.ty };
      else if (Object.keys(ptrs).length === 2) { pinch = { d: pdist(), z: S.z }; dragStart = null; }
      window.addEventListener('pointermove', onMove);
      window.addEventListener('pointerup', onUp);
      window.addEventListener('pointercancel', onUp);
    });
    function onMove(ev) {
      if (!ptrs[ev.pointerId]) return;
      ptrs[ev.pointerId] = { x: ev.clientX, y: ev.clientY };
      var n = Object.keys(ptrs).length;
      if (n === 1 && dragStart) {
        var dx = ev.clientX - dragStart.x, dy = ev.clientY - dragStart.y;
        if (!S.moved && Math.hypot(dx, dy) > 4) { S.moved = true; viewport.classList.add('is-dragging'); hideTip(); }
        if (S.moved) { S.tx = dragStart.tx + dx; S.ty = dragStart.ty + dy; applyView(); }
      } else if (n === 2 && pinch && pinch.d > 0) {
        S.moved = true;
        var ks = Object.keys(ptrs), a = ptrs[ks[0]], b = ptrs[ks[1]], r = viewport.getBoundingClientRect();
        var nz = clamp(pinch.z * (pdist() / pinch.d), 1, MAX_Z);
        zoomAt((a.x + b.x) / 2 - r.left, (a.y + b.y) / 2 - r.top, nz / S.z);
      }
    }
    function onUp(ev) {
      delete ptrs[ev.pointerId];
      if (!Object.keys(ptrs).length) {
        window.removeEventListener('pointermove', onMove);
        window.removeEventListener('pointerup', onUp);
        window.removeEventListener('pointercancel', onUp);
        viewport.classList.remove('is-dragging');
        dragStart = null; pinch = null;
        setTimeout(function () { S.moved = false; }, 0);
      } else if (Object.keys(ptrs).length === 1) {
        var k = Object.keys(ptrs)[0];
        dragStart = { x: ptrs[k].x, y: ptrs[k].y, tx: S.tx, ty: S.ty }; pinch = null;
      }
    }
    cleanups.push(function () {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
      window.removeEventListener('pointercancel', onUp);
    });
    viewport.addEventListener('wheel', function (ev) {
      ev.preventDefault();
      var r = viewport.getBoundingClientRect();
      zoomAt(ev.clientX - r.left, ev.clientY - r.top, ev.deltaY < 0 ? 1.2 : 1 / 1.2);
    }, { passive: false });
    viewport.addEventListener('keydown', function (ev) {
      if (ev.target !== viewport) return;
      var step = 36, handled = true;
      switch (ev.key) {
        case '+': case '=': zoomCenter(1.4); break;
        case '-': case '_': zoomCenter(1 / 1.4); break;
        case '0': resetView(); break;
        case 'ArrowLeft': S.tx += step; applyView(); break;
        case 'ArrowRight': S.tx -= step; applyView(); break;
        case 'ArrowUp': S.ty += step; applyView(); break;
        case 'ArrowDown': S.ty -= step; applyView(); break;
        case 'Escape': if (S.sel) select(null); break;
        default: handled = false;
      }
      if (handled) ev.preventDefault();
    });
    viewport.addEventListener('dblclick', function (ev) {
      var r = viewport.getBoundingClientRect();
      zoomAt(ev.clientX - r.left, ev.clientY - r.top, 1.8);
    });
    if (window.ResizeObserver) {
      var ro = new ResizeObserver(function () { applyView(); });
      ro.observe(viewport);
      cleanups.push(function () { ro.disconnect(); });
    }

    /* ---- filtros ---- */
    function passes(rec) {
      var l = rec.loc;
      var anyAct = ACTS.some(function (a) { return S.acts[a]; });
      if (anyAct && !S.acts[str(l.act).toUpperCase()]) return false;
      if (S.cat) {
        if (S.cat === '__routes') { if (rec.kind !== 'route') return false; }
        else if (normCat(l.category) !== S.cat) return false;
      }
      return true;
    }
    function refresh() {
      var shown = 0;
      Object.keys(pins).forEach(function (key) {
        var rec = pins[key], vis = passes(rec);
        if (vis) shown++;
        var dim = S.step != null && rec.first > S.step;
        var cur = S.step != null && stepLoc(S.step) === key;
        [rec.g, rec.path].forEach(function (n) {
          if (!n) return;
          n.classList.toggle('is-filtered', !vis);
          n.classList.toggle('is-dim', !!dim);
        });
        rec.g.classList.toggle('is-cur', !!cur);
        if (rec.path) rec.path.classList.toggle('is-cur', !!cur);
        rec.g.setAttribute('tabindex', vis ? '0' : '-1');
        rec.g.setAttribute('aria-hidden', vis ? 'false' : 'true');
      });
      svg.classList.toggle('hide-nodes', !S.layers.nodes);
      svg.classList.toggle('hide-routes', !S.layers.routes);
      svg.classList.toggle('hide-labels', !S.layers.labels);
      statusLine.textContent = 'Mostrando ' + shown + ' de ' + mapped.length + ' ubicaciones en el mapa'
        + (S.step != null ? ' · Resaltado hasta el paso ' + S.step : '');
    }
    function stepLoc(n) { var st = idx('stepByNum')[n]; return st ? st.loc : null; }

    /* ---- selección y ficha lateral ---- */
    function select(key, opts) {
      opts = opts || {};
      if (S.sel && pins[S.sel]) {
        pins[S.sel].g.classList.remove('is-sel'); pins[S.sel].g.setAttribute('aria-pressed', 'false');
        if (pins[S.sel].path) pins[S.sel].path.classList.remove('is-sel');
      }
      S.sel = key && pins[key] ? key : null;
      if (S.sel) {
        var rec = pins[S.sel];
        rec.g.classList.add('is-sel'); rec.g.setAttribute('aria-pressed', 'true');
        if (rec.path) rec.path.classList.add('is-sel');
        if (opts.center) centerOn(rec.c, Math.max(S.z, 2.4));
        else ensureVisible(rec.c);
        try { history.replaceState(null, '', '#/map?loc=' + encodeURIComponent(S.sel) + (S.step != null ? '&step=' + S.step : '')); } catch (e) { /* ok */ }
      } else {
        try { history.replaceState(null, '', '#/map' + (S.step != null ? '?step=' + S.step : '')); } catch (e) { /* ok */ }
      }
      paintSide();
    }
    function ensureVisible(c) {
      var s = vsize();
      var sx = S.tx + (c[0] / MAP_W) * s.w * S.z, sy = S.ty + (c[1] / MAP_H) * s.h * S.z, m = 48;
      if (S.z > 1 && (sx < m || sx > s.w - m || sy < m || sy > s.h - m)) centerOn(c);
    }
    function paintSide() {
      side.textContent = '';
      side.appendChild(guard('ficha', function () { return sidePanel(); }));
      side.appendChild(guard('leyenda', function () { return legend(); }));
      if (unmapped.length) {
        side.appendChild(h('p', { class: 'w-unmapped' },
          'Aviso: ' + unmapped.length + (unmapped.length === 1 ? ' ubicación sin coordenadas no se pinta' : ' ubicaciones sin coordenadas no se pintan') + ': ',
          unmapped.map(function (l, i) { return h('span', null, i ? ', ' : null, REM.ui.link('location', l.key, l.name)); })));
      }
    }
    function sidePanel() {
      var rec = S.sel && pins[S.sel];
      if (!rec) {
        return h('div', { class: 'card w-card w-side-card' },
          h('h2', { class: 'w-card-title' }, 'Ficha rápida'),
          h('p', { class: 'w-prose' }, 'Pulsa un nodo o una ruta del mapa (o búscalo arriba) para ver su ficha rápida, moverte por la brújula y abrir su ficha completa en el Atlas.'),
          h('ul', { class: 'w-tips' },
            h('li', null, 'Rueda del ratón o botones ＋ ／ − para acercar; arrastra para desplazar.'),
            h('li', null, 'Con el mapa enfocado: flechas para desplazar, + y − para zoom, 0 para reiniciar.'),
            h('li', null, 'El deslizador «Paso de la progresión» ilumina los lugares ya visitados.')));
      }
      var l = rec.loc;
      var species = {};
      arr(l.encounters).forEach(function (e) { arr(e.slots).forEach(function (x) { species[x.dex != null ? x.dex : x.sym] = 1; }); });
      if (l.fishing) ['common', 'rare'].forEach(function (k) { if (l.fishing[k]) species[l.fishing[k].dex != null ? l.fishing[k].dex : l.fishing[k].sym] = 1; });
      var nSp = Object.keys(species).length;
      var openLink = REM.ui.link('location', l.key, 'Abrir en el Atlas');
      openLink.classList.add('btn', 'btn--primary');
      var card = h('div', { class: 'card w-card w-side-card w-act-edge-' + actNum(l.act) },
        h('h2', { class: 'w-side-name' }, str(l.name)),
        h('div', { class: 'w-badges' },
          badge(normCat(l.category), 'w-cat w-cat-' + rec.kind),
          l.act ? badge('Acto ' + l.act, 'w-act-' + actNum(l.act)) : null,
          l.node != null && l.node !== '' ? badge('Nodo n.º ' + l.node, 'w-node') : (l.routeLabel ? badge('Ruta ' + l.routeLabel, 'w-node') : null)),
        h('dl', { class: 'w-kv' },
          h('dt', null, '☀ Día'), h('dd', null, fmtRange(l.levelDay)),
          h('dt', null, '☾ Noche'), h('dd', null, fmtRange(l.levelNight)),
          nSp ? h('dt', null, 'Especies') : null, nSp ? h('dd', null, String(nSp)) : null,
          arr(l.items).length ? h('dt', null, 'Objetos y MT') : null, arr(l.items).length ? h('dd', null, String(arr(l.items).length)) : null,
          arr(l.shops).length ? h('dt', null, 'Tiendas') : null, arr(l.shops).length ? h('dd', null, String(arr(l.shops).length)) : null,
          arr(l.steps).length ? h('dt', null, 'Pasos') : null,
          arr(l.steps).length ? h('dd', null, arr(l.steps).slice(0, 6).map(function (n, i) { return h('span', null, i ? ', ' : null, REM.ui.link('step', n, String(n))); })) : null));
      if (l.situation) {
        var sit = str(l.situation).replace(/\s*\*?\(Nodo[^)]*\)\*?\s*$/, '');
        card.appendChild(richEl('p', 'w-prose w-clamp', sit));
      }
      card.appendChild(h('h3', { class: 'w-side-sub' }, 'Brújula'));
      card.appendChild(compass(l, function (k) { select(k, { center: true }); }));
      card.appendChild(h('div', { class: 'w-side-actions' }, openLink));
      return card;
    }
    function legend() {
      function sw(n) { return h('span', { class: 'w-sw w-act-bg-' + n }, ''); }
      function ico(kind) {
        var s = h('svg', { class: 'w-legend-ico', viewBox: '-9 -9 18 18', 'aria-hidden': 'true', focusable: 'false' },
          h('g', { class: 'w-pin w-pin-' + kind + ' w-act-fill-0' }, pinShape(kind)));
        return s;
      }
      return h('details', { class: 'card w-card w-legend-card', open: true },
        h('summary', null, 'Leyenda'),
        h('ul', { class: 'w-legend-list' },
          [1, 2, 3, 4, 5].map(function (n) { return h('li', null, sw(n), ' Acto ' + ACTS[n - 1] + ' (primera visita)'); }),
          h('li', null, ico('city'), ' Ciudad (círculo grande)'),
          h('li', null, ico('town'), ' Pueblo (círculo mediano)'),
          h('li', null, ico('place'), ' Lugar especial (rombo)'),
          h('li', null, ico('route'), ' Ruta: R1–R24 normales y de montaña/mar/nieve; E1–E8 rutas especiales')));
    }

    /* ---- barra de controles ---- */
    var qIn = h('input', { type: 'search', class: 'input w-input', placeholder: 'Buscar ubicación…', 'aria-label': 'Buscar ubicación en el mapa', autocomplete: 'off' });
    var resBox = h('ul', { class: 'w-suggest', role: 'listbox', hidden: true, 'aria-label': 'Resultados de búsqueda' });
    function runSearch() {
      var q = stripAcc(qIn.value).trim();
      resBox.textContent = '';
      if (!q) { resBox.hidden = true; return; }
      var found = mapped.filter(function (l) {
        return stripAcc(l.name + ' ' + arr(l.draftNames).join(' ') + ' ' + str(l.routeLabel)).indexOf(q) >= 0;
      }).slice(0, 8);
      if (!found.length) { resBox.appendChild(h('li', { class: 'w-suggest-none' }, 'Sin resultados')); resBox.hidden = false; return; }
      found.forEach(function (l) {
        var b = h('button', { type: 'button', role: 'option', class: 'w-suggest-item' }, str(l.name), h('small', null, ' ' + normCat(l.category)));
        b.addEventListener('click', function () { choose(l.key); });
        resBox.appendChild(h('li', null, b));
      });
      resBox.hidden = false;
      resBox._first = found[0].key;
    }
    function choose(key) {
      resBox.hidden = true; qIn.value = '';
      select(key, { center: true });
      viewport.focus({ preventScroll: true });
    }
    qIn.addEventListener('input', runSearch);
    qIn.addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter') { ev.preventDefault(); if (!resBox.hidden && resBox._first) choose(resBox._first); }
      else if (ev.key === 'Escape') { resBox.hidden = true; }
    });
    var onDocClick = function (ev) { if (!resBox.contains(ev.target) && ev.target !== qIn) resBox.hidden = true; };
    document.addEventListener('click', onDocClick);
    cleanups.push(function () { document.removeEventListener('click', onDocClick); });

    function layerCheck(label, key) {
      var cb = h('input', { type: 'checkbox' });
      cb.checked = S.layers[key];
      cb.addEventListener('change', function () { S.layers[key] = cb.checked; refresh(); });
      return h('label', { class: 'w-check' }, cb, h('span', null, label));
    }
    var actBox = h('div', { class: 'w-chipset', role: 'group', 'aria-label': 'Filtrar por acto' });
    ACTS.forEach(function (a) {
      var b = h('button', { type: 'button', class: 'w-chip w-act-' + actNum(a), 'aria-pressed': 'false' }, 'Acto ' + a);
      b.addEventListener('click', function () {
        S.acts[a] = !S.acts[a]; b.setAttribute('aria-pressed', S.acts[a] ? 'true' : 'false'); refresh();
      });
      actBox.appendChild(b);
    });
    var catSel = h('select', { class: 'input w-input', 'aria-label': 'Filtrar por categoría' },
      h('option', { value: '' }, 'Todas las categorías'),
      h('option', { value: '__routes' }, 'Todas las rutas'),
      CAT_ORDER.map(function (c) { return h('option', { value: c }, c); }));
    catSel.addEventListener('change', function () { S.cat = catSel.value; refresh(); });

    /* progresión */
    var stepOn = h('input', { type: 'checkbox', id: 'w-step-on' });
    var stepRange = h('input', { type: 'range', min: '1', max: String(maxStep), value: '1', 'aria-label': 'Paso de la progresión', disabled: true, class: 'w-range' });
    var stepOut = h('output', { class: 'w-step-out', for: 'w-step-on', 'aria-live': 'polite' }, 'Desactivado');
    function stepUpdate() {
      if (!stepOn.checked) { S.step = null; stepRange.disabled = true; stepOut.textContent = 'Desactivado'; refresh(); return; }
      stepRange.disabled = false;
      S.step = parseInt(stepRange.value, 10) || 1;
      var st = idx('stepByNum')[S.step];
      stepOut.textContent = '';
      stepOut.appendChild(h('b', null, 'Paso ' + S.step + '/' + maxStep));
      if (st) {
        stepOut.appendChild(document.createTextNode(' · ' + (idx('locByKey')[st.loc] ? idx('locByKey')[st.loc].name : str(st.loc)) + ' · Acto ' + str(st.act)));
        if (st.summary) stepOut.appendChild(h('span', { class: 'w-step-sum' }, str(st.summary)));
      }
      refresh();
      try { history.replaceState(null, '', '#/map?' + (S.sel ? 'loc=' + encodeURIComponent(S.sel) + '&' : '') + 'step=' + S.step); } catch (e) { /* ok */ }
    }
    stepOn.addEventListener('change', stepUpdate);
    stepRange.addEventListener('input', stepUpdate);

    var zoomOut = h('span', { class: 'w-zoom-out', 'aria-live': 'off' }, '×1,0');
    function zbtn(label, aria, fn) {
      var b = h('button', { type: 'button', class: 'w-zbtn', 'aria-label': aria, title: aria }, label);
      b.addEventListener('click', fn); return b;
    }
    var zoomBar = h('div', { class: 'w-zoombar', role: 'group', 'aria-label': 'Controles de zoom' },
      zbtn('＋', 'Acercar', function () { zoomCenter(1.5); }),
      zbtn('−', 'Alejar', function () { zoomCenter(1 / 1.5); }),
      zbtn('⌖', 'Centrar en la ubicación seleccionada', function () { if (S.sel) centerOn(pins[S.sel].c, Math.max(S.z, 2.4)); else resetView(); }),
      zbtn('⟲', 'Reiniciar vista', resetView), zoomOut);
    stage.appendChild(zoomBar);

    var toolbar = h('div', { class: 'w-map-toolbar w-card' },
      h('div', { class: 'w-filter-row' },
        h('div', { class: 'w-field w-field-grow w-search' }, h('span', null, 'Ubicación'), qIn, resBox),
        h('div', { class: 'w-field' }, h('span', null, 'Categoría'), catSel),
        h('div', { class: 'w-field w-checks' }, h('span', null, 'Capas'),
          h('div', { class: 'w-inline' }, layerCheck('Nodos', 'nodes'), layerCheck('Rutas', 'routes'), layerCheck('Etiquetas', 'labels')))),
      h('div', { class: 'w-filter-row' },
        h('div', { class: 'w-field' }, h('span', null, 'Acto'), actBox),
        h('div', { class: 'w-field w-field-grow w-prog' },
          h('label', { class: 'w-check', for: 'w-step-on' }, stepOn, h('span', null, 'Resaltar paso de la progresión')),
          stepRange, stepOut)));

    var root = h('div', { class: 'w-view w-mapview' },
      h('header', { class: 'w-head' },
        h('h1', null, 'Mapa de Oniria'),
        h('p', { class: 'w-lead' }, 'La región completa en un mapa de ' + mapped.length + ' ubicaciones: 32 nodos (ciudades, pueblos y lugares especiales) y 32 rutas. Pulsa un pin para su ficha rápida y sigue la brújula para moverte por vecinos.'),
        h('div', { class: 'w-head-actions' }, h('a', { class: 'btn', href: '#/atlas' }, '📖 Atlas de ubicaciones'),
          h('a', { class: 'btn', href: '#/progression' }, '🧭 Guía de progresión'))),
      toolbar,
      statusLine,
      h('div', { class: 'w-map-layout' }, h('div', { class: 'w-map-main' }, stage), side));
    el.appendChild(root);
    paintSide();
    applyView();
    refresh();

    /* ---- preselección por URL ---- */
    var q0 = query || {};
    var stepQ = parseInt(q0.step, 10);
    if (isFinite(stepQ) && stepQ >= 1 && stepQ <= maxStep) { stepOn.checked = true; stepRange.value = String(stepQ); stepUpdate(); }
    var want = q0.loc || (parts && parts[0]) || null;
    if (want && pins[want]) {
      /* el contenedor aún puede no tener tamaño en este instante: se centra al siguiente fotograma */
      requestAnimationFrame(function () { select(want, { center: true }); });
    }
    return function () { cleanups.forEach(function (f) { try { f(); } catch (e) { /* ok */ } }); };
  }

  REM.router.register('map', {
    title: 'Mapa interactivo',
    render: function (el, parts, query) { return render(el, parts, query); },
    exists: function (parts, query) {
      var k = (query && query.loc) || (parts && parts[0]);
      return !k || !!idx('locByKey')[k];
    }
  });

  if (REM.selftest && REM.selftest.add) {
    REM.selftest.add('map', function () {
      var out = ['#/map'];
      var locs = arr(model() && model().locations);
      if (locs[0]) out.push('#/map?loc=' + encodeURIComponent(locs[0].key));
      if (arr(model() && model().progression).length) out.push('#/map?step=12');
      return out;
    });
  }
})();
