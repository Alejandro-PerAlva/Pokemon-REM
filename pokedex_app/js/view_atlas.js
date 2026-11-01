/* ==========================================================================
   Pokémon REM Master Codex — Atlas de ubicaciones
   Rutas: #/atlas (rejilla/lista con filtros) y #/location/<KEY> (ficha completa)
   Propiedad: codex-front-world. Solo usa la API pública de SPEC §5.
   ========================================================================== */
(function () {
  'use strict';
  var REM = window.REM;
  if (!REM || !REM.router) return;
  var h = REM.h;
  var esc = REM.esc;
  var MAP_URL = '/map/Mapa_Final__Esqueleto.png';
  var MAP_W = 480, MAP_H = 320;

  /* ---------------------------------------------------------------- utilidades */
  function model() { return (REM.state && REM.state.model) || null; }
  function arr(x) { return Array.isArray(x) ? x : []; }
  function str(x) { return x == null ? '' : String(x); }
  function on(el, ev, fn) { el.addEventListener(ev, fn); return el; }
  function idx(name) { return (REM.idx && REM.idx[name]) || {}; }
  function fmtRange(r) {
    if (!r || !r.length) return '—';
    return REM.fmtRange ? REM.fmtRange(r) : (r[0] === r[1] ? String(r[0]) : r[0] + '–' + r[1]);
  }
  function ui(name) { return REM.ui && REM.ui[name]; }
  function emptyMsg(msg) {
    return ui('empty') ? REM.ui.empty(msg || 'Sin datos') : h('p', { class: 'w-empty' }, msg || 'Sin datos');
  }
  function noModel(el) {
    el.textContent = '';
    el.appendChild(h('div', { class: 'w-view' }, emptyMsg('Sin datos: el modelo todavía no está cargado.')));
  }

  /* Texto enriquecido seguro: SIEMPRE escapa con REM.esc y después añade solo <strong>/<em>/<mark>. */
  function rich(s) {
    s = str(s);
    var keep = [];
    s = s.replace(/\[[^\]\n]*(?:PENDIENTE|Pendiente|REVISI[ÓO]N|Revisi[óo]n)[^\]\n]*\]\*?/g, function (m) {
      keep.push(m);
      return '\u0001' + (keep.length - 1) + '\u0002';
    });
    s = esc(s);
    s = s.replace(/\*\*([^*\n]+?)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/(^|[^*\w])\*([^*\s][^*\n]*?)\*(?![*\w])/g, '$1<em>$2</em>');
    s = s.replace(/\u0001(\d+)\u0002/g, function (_, i) {
      return '<mark class="w-pending">' + esc(keep[+i]) + '</mark>';
    });
    return s;
  }
  function richEl(tag, cls, text) {
    var e = h(tag, { class: cls || null });
    e.innerHTML = rich(text);
    return e;
  }

  function stripAcc(s) { return str(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); }

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

  function locByKey(k) { return idx('locByKey')[k] || null; }
  function locName(k) { var l = locByKey(k); return l ? l.name : str(k); }
  function sortedLocs() {
    var M = model();
    return arr(M && M.locations).slice().sort(function (a, b) {
      var oa = a.order == null ? 999 : a.order, ob = b.order == null ? 999 : b.order;
      if (oa !== ob) return oa - ob;
      return str(a.name).localeCompare(str(b.name), 'es');
    });
  }
  function link(kind, id, label) {
    if (id != null && id !== '' && REM.ent(kind, id)) return REM.ui.link(kind, id, label);
    return h('span', { class: 'w-plain' }, label != null ? label : str(id));
  }
  function locRef(k, label) {
    var l = locByKey(k);
    if (!l) return h('span', { class: 'w-plain' }, label || str(k));
    return REM.ui.link('location', k, label || l.name);
  }

  function badge(text, cls, title) {
    return h('span', { class: 'badge w-badge ' + (cls || ''), title: title || null }, text);
  }
  function actBadge(a) {
    if (!a) return null;
    return badge('Acto ' + a, 'w-act-' + actNum(a));
  }
  function catBadge(c) { return badge(normCat(c), 'w-cat w-cat-' + catKind(c)); }
  function labelBadge(l) {
    if (l.node != null && l.node !== '') return badge('Nodo n.º ' + l.node, 'w-node');
    if (l.routeLabel) return badge('Ruta ' + l.routeLabel, 'w-node');
    return null;
  }
  function guard(label, fn, fallback) {
    try { return fn(); } catch (e) {
      if (REM.fail) REM.fail('atlas · ' + label, e);
      return fallback === undefined ? h('p', { class: 'w-empty' }, 'No se pudo mostrar esta sección.') : fallback;
    }
  }
  function section(title, body, id, cls) {
    return h('section', { class: 'card w-sec ' + (cls || ''), id: id || null, 'aria-label': title },
      h('h2', { class: 'w-sec-title' }, title), body);
  }

  /* ---------------------------------------------------------------- Pokémon / objetos */
  function monRef(dex, sym) {
    var p = null;
    if (dex != null && idx('pokemonByDex')[dex]) p = idx('pokemonByDex')[dex];
    if (!p && sym && idx('pokemonBySym')[sym]) p = idx('pokemonBySym')[sym];
    if (!p) return h('span', { class: 'w-mon' }, str(sym || (dex != null ? '#' + dex : '—')));
    return h('span', { class: 'w-mon' }, REM.ui.pokeIcon(p.dex, { size: 32 }), REM.ui.link('pokemon', p.dex, p.name));
  }
  var RARITY = { COMMON: 'Común', UNCOMMON: 'Poco común', RARE: 'Raro' };
  function rarityBadge(r) {
    var k = str(r).toUpperCase();
    return h('span', { class: 'rbadge r-' + (k.toLowerCase() || 'none') }, RARITY[k] || str(r) || '—');
  }
  var KIND = { Land: 'Tierra', Cave: 'Cueva', Surf: 'Surf', Fish: 'Pesca' };
  var METHODS = {
    B: 'Poké Ball visible', H: 'Objeto oculto', C: 'Cofre', N: 'Regalo de PNJ',
    E: 'Evento / misión', J: 'Botín de jefe o líder', P: 'Misión de Pía', S: 'Tienda (stock único)'
  };
  function pctBar(pct, max) {
    var w = Math.max(0, Math.min(100, Number(pct) || 0));
    var sc = max ? Math.min(100, (w / max) * 100) : w;
    var bar = h('span', { class: 'w-bar', role: 'img', 'aria-label': (REM.pct ? REM.pct(w) : w + ' %') },
      h('span', { class: 'w-bar-fill' }));
    bar.firstChild.style.width = sc + '%';
    return h('span', { class: 'w-pct' }, bar, h('b', null, (REM.pct ? REM.pct(w) : w + ' %')));
  }
  function uiTable(columns, rows, cls) {
    return REM.ui.table(columns, rows, { filter: false, dense: true, cls: cls || null, pageSize: 200 });
  }
  function encounterBlock(enc, loc) {
    var slots = arr(enc.slots);
    var title = KIND[enc.kind] || str(enc.kind) || 'Encuentros';
    var zone = enc.zoneName || (enc.zone ? 'Zona ' + enc.zone : '');
    var maxPct = 0;
    slots.forEach(function (s) { if ((s.pct || 0) > maxPct) maxPct = s.pct; });
    var cols = [
      { key: 'slot', label: '#', className: 'w-col-n', sort: function (r) { return r.slot; }, render: function (r, i) { return String(r.slot != null ? r.slot : i + 1); } },
      { key: 'rarity', label: 'Rareza', sort: function (r) { return ['COMMON', 'UNCOMMON', 'RARE'].indexOf(str(r.rarity).toUpperCase()); }, render: function (r) { return rarityBadge(r.rarity); } },
      { key: 'pct', label: '%', className: 'w-col-pct', defaultDir: 'desc', sort: function (r) { return r.pct; }, render: function (r) { return pctBar(r.pct, maxPct); } },
      { key: 'mon', label: 'Pokémon', sort: function (r) { var p = idx('pokemonByDex')[r.dex]; return p ? p.name : str(r.sym); }, render: function (r) { return monRef(r.dex, r.sym); } },
      { key: 'day', label: 'Nv. día', align: 'right', sort: function (r) { return r.day && r.day[0]; }, render: function (r) { return fmtRange(r.day); } },
      { key: 'night', label: 'Nv. noche', align: 'right', sort: function (r) { return r.night && r.night[0]; }, render: function (r) { return fmtRange(r.night); } },
      { key: 'note', label: 'Nota táctica', className: 'w-note', sort: false, render: function (r) { return r.note ? str(r.note) : '—'; } }
    ];
    return h('div', { class: 'w-enc' },
      h('h3', { class: 'w-enc-title' },
        h('span', { class: 'w-kind w-kind-' + str(enc.kind).toLowerCase() }, title),
        zone ? h('span', { class: 'w-zone' }, zone) : null,
        h('span', { class: 'w-muted' }, ' · ' + slots.length + ' casillas')),
      slots.length ? uiTable(cols, slots, 'w-table-enc') : emptyMsg('Sin datos'));
  }

  function fishingBlock(f) {
    var rows = [];
    [['common', 'Común'], ['rare', 'Rara']].forEach(function (p) {
      var s = f && f[p[0]];
      if (s) rows.push({ kind: p[0], label: p[1], s: s });
    });
    if (!rows.length) return null;
    var cols = [
      { key: 'kind', label: 'Tipo', sort: false, render: function (r) { return h('span', { class: 'rbadge r-' + (r.kind === 'common' ? 'common' : 'rare') }, r.label); } },
      { key: 'pct', label: '%', className: 'w-col-pct', sort: false, render: function (r) { return pctBar(r.s.pct); } },
      { key: 'mon', label: 'Pokémon', sort: false, render: function (r) { return monRef(r.s.dex, r.s.sym); } },
      { key: 'day', label: 'Nv. día', align: 'right', sort: false, render: function (r) { return fmtRange(r.s.day); } },
      { key: 'night', label: 'Nv. noche', align: 'right', sort: false, render: function (r) { return fmtRange(r.s.night); } },
      { key: 'note', label: 'Nota táctica', className: 'w-note', sort: false, render: function (r) { return r.s.note ? str(r.s.note) : '—'; } }
    ];
    return h('div', { class: 'w-enc' },
      h('h3', { class: 'w-enc-title' }, h('span', { class: 'w-kind w-kind-fish' }, 'Pesca'),
        h('span', { class: 'w-muted' }, ' · Común 70 % / Rara 30 %')),
      uiTable(cols, rows, 'w-table-fish'));
  }

  function itemRef(sym) {
    var m = /^TM0*(\d+)$/i.exec(str(sym));
    if (m) {
      var n = parseInt(m[1], 10);
      var tm = idx('tmByNum')[n];
      if (tm) {
        var mv = idx('moveBySym')[tm.move];
        var lab = 'MT' + (n < 10 ? '0' + n : n) + (mv ? ' · ' + mv.name : '');
        return h('span', { class: 'w-item' }, h('span', { class: 'w-item-tm', 'aria-hidden': 'true' }, 'MT'), REM.ui.link('tm', n, lab));
      }
    }
    var it = idx('itemBySym')[sym];
    if (it) return h('span', { class: 'w-item' }, ui('itemIcon') ? REM.ui.itemIcon(it, { size: 28 }) : null, REM.ui.link('item', sym, it.name));
    return h('span', { class: 'w-item w-plain' }, str(sym));
  }

  function itemsBlock(items) {
    items = arr(items);
    if (!items.length) return emptyMsg('Esta ubicación no tiene objetos ni MT registrados.');
    var cols = [
      { key: 'item', label: 'Objeto', sort: function (r) { return r.item; }, render: function (r) { return itemRef(r.item); } },
      { key: 'qty', label: 'Cant.', align: 'right', sort: function (r) { return r.qty; }, render: function (r) { return '×' + (r.qty == null ? 1 : r.qty); } },
      { key: 'method', label: 'Método', align: 'center', sort: function (r) { return r.method; },
        render: function (r) { var m = str(r.method).toUpperCase(); return h('span', { class: 'mbadge m-' + m, title: m + ' · ' + (METHODS[m] || 'Método desconocido') }, m || '?'); } },
      { key: 'zone', label: 'Zona', sort: function (r) { return r.zone; }, render: function (r) { return str(r.zone) || '—'; } },
      { key: 'note', label: 'Nota', className: 'w-note', sort: false, render: function (r) { return str(r.note) || '—'; } }
    ];
    var legend = h('details', { class: 'w-legend' }, h('summary', null, 'Leyenda de métodos (B · H · C · N · E · J · P · S)'),
      h('ul', { class: 'w-legend-list' }, Object.keys(METHODS).map(function (k) {
        return h('li', null, h('span', { class: 'mbadge m-' + k }, k), ' ' + METHODS[k]);
      })));
    return h('div', null, uiTable(cols, items, 'w-table-items'), legend);
  }

  /* ---------------------------------------------------------------- personajes presentes */
  function plainName(n) { return stripAcc(n).replace(/\(.*?\)/g, '').replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim(); }
  function charsBlock(loc) {
    var names = arr(loc.characters), keys = arr(loc.charKeys).slice();
    var chars = arr(model() && model().characters);
    var used = {};
    var out = [];
    names.forEach(function (n) {
      var pn = plainName(n), hit = null;
      if (pn) {
        for (var i = 0; i < chars.length && !hit; i++) {
          var cn = plainName(chars[i].name);
          if (!cn) continue;
          if ((pn === cn || pn.indexOf(cn) >= 0 || cn.indexOf(pn) >= 0) && keys.indexOf(chars[i].key) >= 0) hit = chars[i];
        }
        if (!hit) {
          for (var j = 0; j < chars.length && !hit; j++) {
            var c2 = plainName(chars[j].name);
            if (c2 && pn === c2) hit = chars[j];
          }
        }
      }
      if (hit && idx('charByKey')[hit.key]) {
        used[hit.key] = true;
        out.push(h('li', null, REM.ui.link('character', hit.key, str(n))));
      } else {
        out.push(h('li', null, h('span', { class: 'w-plain' }, str(n))));
      }
    });
    keys.forEach(function (k) {
      if (used[k] || !idx('charByKey')[k]) return;
      used[k] = true;
      out.push(h('li', null, REM.ui.link('character', k, idx('charByKey')[k].name)));
    });
    if (!out.length) return emptyMsg('Sin personajes registrados.');
    return h('ul', { class: 'w-chips' }, out);
  }

  /* ---------------------------------------------------------------- boss con marcadores */
  function bossBlock(text) {
    var t = str(text).trim();
    if (!t || t === '—') return emptyMsg('Sin jefe ni evento de combate.');
    return richEl('p', 'w-boss', t);
  }

  /* ---------------------------------------------------------------- brújula navegable */
  var DIRS = [
    { k: 'N', name: 'Norte' }, { k: 'E', name: 'Este' }, { k: 'S', name: 'Sur' }, { k: 'O', name: 'Oeste' }
  ];
  function compass(loc) {
    var conn = loc.conn || {};
    var cells = {};
    DIRS.forEach(function (d) {
      var c = conn[d.k] || {};
      var keys = arr(c.keys), text = str(c.text).trim();
      var body = [];
      keys.forEach(function (k) {
        var a = locByKey(k) ? REM.ui.link('location', k, locName(k)) : h('span', { class: 'w-plain' }, str(k));
        body.push(h('div', { class: 'w-dir-item' }, a));
      });
      var tail = text.split('→').pop().trim();
      if (keys.length) {
        if (/^(cruce|nexo)/i.test(tail)) body.push(h('small', { class: 'w-dir-via' }, '↳ ' + tail));
      } else if (text) {
        body.push(h('span', { class: 'w-dir-cross', 'aria-disabled': 'true', title: text }, tail || text));
      }
      if (!body.length) body.push(h('span', { class: 'w-dir-none', 'aria-disabled': 'true' }, 'Sin salida'));
      cells[d.k] = h('div', { class: 'w-dir w-dir-' + d.k, role: 'group', 'aria-label': 'Hacia el ' + d.name },
        h('span', { class: 'w-dir-head' }, h('b', { 'aria-hidden': 'true' }, d.k), h('span', { class: 'w-dir-name' }, d.name)),
        body);
    });
    var kind = catKind(loc.category);
    return h('div', { class: 'w-compass', role: 'navigation', 'aria-label': 'Brújula: ubicaciones vecinas' },
      cells.N, cells.O,
      h('div', { class: 'w-compass-center w-center-' + kind + ' w-act-bg-' + actNum(loc.act), 'aria-hidden': 'true', title: str(loc.name) },
        h('span', null, loc.node != null && loc.node !== '' ? String(loc.node) : str(loc.routeLabel) || '·')),
      cells.E, cells.S);
  }

  /* ---------------------------------------------------------------- minimapa */
  function parsePath(p) {
    var pts = [];
    if (!p) return pts;
    if (typeof p === 'string') {
      p.split(';').forEach(function (s) {
        var m = s.split(',');
        if (m.length >= 2 && isFinite(+m[0]) && isFinite(+m[1])) pts.push([+m[0], +m[1]]);
      });
      return pts;
    }
    if (Array.isArray(p)) {
      p.forEach(function (q) {
        if (Array.isArray(q) && q.length >= 2) pts.push([+q[0], +q[1]]);
        else if (q && typeof q === 'object' && 'x' in q) pts.push([+q.x, +q.y]);
      });
    }
    return pts;
  }
  function svgEl(tag, attrs) {
    var e = document.createElementNS('http://www.w3.org/2000/svg', tag);
    if (attrs) Object.keys(attrs).forEach(function (k) { if (attrs[k] != null) e.setAttribute(k, attrs[k]); });
    return e;
  }
  function mapHref(key) { return '#/map' + (key ? '?loc=' + encodeURIComponent(key) : ''); }
  function minimap(loc) {
    var c = loc.coords;
    var wrap = h('div', { class: 'w-minimap' });
    if (!c || c.length < 2) {
      wrap.appendChild(emptyMsg('Esta ubicación no tiene coordenadas en el mapa.'));
      return wrap;
    }
    var VW = 192, VH = 128;
    var x0 = Math.max(0, Math.min(MAP_W - VW, c[0] - VW / 2));
    var y0 = Math.max(0, Math.min(MAP_H - VH, c[1] - VH / 2));
    var frame = h('div', { class: 'w-minimap-frame' });
    var img = h('img', { class: 'w-minimap-img', src: MAP_URL, alt: 'Mapa de Oniria centrado en ' + str(loc.name), draggable: 'false' });
    img.style.width = (MAP_W / VW * 100) + '%';
    img.style.left = (-x0 / VW * 100) + '%';
    img.style.top = (-y0 / VH * 100) + '%';
    frame.appendChild(img);
    var svg = svgEl('svg', { viewBox: x0 + ' ' + y0 + ' ' + VW + ' ' + VH, class: 'w-minimap-svg', 'aria-hidden': 'true', focusable: 'false' });
    var pts = parsePath(loc.path);
    if (pts.length > 1) {
      var d = '';
      for (var i = 0; i < pts.length; i++) {
        var q = pts[i], pv = pts[i - 1];
        var jump = pv && pv[0] !== q[0] && pv[1] !== q[1];
        d += (i === 0 || jump ? 'M' : 'L') + q[0] + ' ' + q[1];
      }
      svg.appendChild(svgEl('path', { d: d, class: 'w-mm-path-out', fill: 'none' }));
      svg.appendChild(svgEl('path', { d: d, class: 'w-mm-path w-act-stroke-' + actNum(loc.act), fill: 'none' }));
    }
    var kind = catKind(loc.category);
    var g = svgEl('g', { transform: 'translate(' + c[0] + ' ' + c[1] + ')', class: 'w-mm-pin w-act-fill-' + actNum(loc.act) });
    g.appendChild(svgEl('circle', { r: 11, class: 'w-mm-halo' }));
    if (kind === 'place') g.appendChild(svgEl('rect', { x: -5, y: -5, width: 10, height: 10, transform: 'rotate(45)', class: 'w-mm-shape' }));
    else g.appendChild(svgEl('circle', { r: kind === 'city' ? 7 : kind === 'town' ? 5.5 : 4.5, class: 'w-mm-shape' }));
    svg.appendChild(g);
    frame.appendChild(svg);
    wrap.appendChild(frame);
    wrap.appendChild(h('a', { class: 'btn btn--sm', href: mapHref(loc.key) }, '🗺️ Ver en el mapa interactivo'));
    return wrap;
  }

  /* ---------------------------------------------------------------- estado de filtros del atlas */
  var F = { q: '', cat: '', acts: {}, lvMin: '', lvMax: '', fish: false, shop: false, sort: 'order', view: 'grid' };
  var UI_KEY = 'rem-atlas-view';
  try { var sv = localStorage.getItem(UI_KEY); if (sv === 'grid' || sv === 'list') F.view = sv; } catch (e) { /* sin almacenamiento */ }

  function lvBounds(l) {
    var lo = null, hi = null;
    [l.levelDay, l.levelNight].forEach(function (r) {
      if (!r || r.length < 2) return;
      if (lo == null || r[0] < lo) lo = r[0];
      if (hi == null || r[1] > hi) hi = r[1];
    });
    return lo == null ? null : [lo, hi];
  }
  function uniqueSpecies(l) {
    var s = {};
    arr(l.encounters).forEach(function (e) { arr(e.slots).forEach(function (x) { s[x.dex != null ? x.dex : x.sym] = 1; }); });
    if (l.fishing) ['common', 'rare'].forEach(function (k) { if (l.fishing[k]) s[l.fishing[k].dex != null ? l.fishing[k].dex : l.fishing[k].sym] = 1; });
    return Object.keys(s).length;
  }
  function matches(l) {
    if (F.cat && normCat(l.category) !== F.cat) return false;
    var anyAct = ACTS.some(function (a) { return F.acts[a]; });
    if (anyAct && !F.acts[str(l.act).toUpperCase()]) return false;
    if (F.fish && !l.fishing) return false;
    if (F.shop && !arr(l.shops).length) return false;
    var mn = F.lvMin === '' ? null : Number(F.lvMin), mx = F.lvMax === '' ? null : Number(F.lvMax);
    if (mn != null || mx != null) {
      var b = lvBounds(l);
      if (!b) return false;
      if (mn != null && b[1] < mn) return false;
      if (mx != null && b[0] > mx) return false;
    }
    if (F.q) {
      var hay = stripAcc([l.name, arr(l.draftNames).join(' '), l.key, l.situation, l.boss, arr(l.characters).join(' ')].join(' '));
      var terms = stripAcc(F.q).split(/\s+/).filter(Boolean);
      for (var i = 0; i < terms.length; i++) if (hay.indexOf(terms[i]) < 0) return false;
    }
    return true;
  }
  function sortRows(rows) {
    var s = F.sort;
    rows = rows.slice();
    if (s === 'name') rows.sort(function (a, b) { return str(a.name).localeCompare(str(b.name), 'es'); });
    else if (s === 'cat') rows.sort(function (a, b) {
      return (CAT_ORDER.indexOf(normCat(a.category)) - CAT_ORDER.indexOf(normCat(b.category))) || ((a.order || 0) - (b.order || 0));
    });
    else if (s === 'level') rows.sort(function (a, b) {
      var x = lvBounds(a), y = lvBounds(b);
      return (x ? x[0] : 999) - (y ? y[0] : 999) || ((a.order || 0) - (b.order || 0));
    });
    return rows;
  }

  function locCard(l, list) {
    var lv = lvBounds(l);
    var meta = [];
    meta.push(h('span', { title: 'Nivel salvaje día / noche' }, '☀ ' + fmtRange(l.levelDay) + ' · ☾ ' + fmtRange(l.levelNight)));
    var chips = [];
    var sp = uniqueSpecies(l);
    if (sp) chips.push(h('span', { class: 'w-mini', title: 'Especies distintas en encuentros y pesca' }, '🌿 ' + sp));
    if (l.fishing) chips.push(h('span', { class: 'w-mini', title: 'Tiene pesca' }, '🎣'));
    if (arr(l.shops).length) chips.push(h('span', { class: 'w-mini', title: 'Tiene tienda' }, '🛒'));
    if (arr(l.items).length) chips.push(h('span', { class: 'w-mini', title: 'Objetos y MT' }, '🎒 ' + arr(l.items).length));
    if (l.boss && str(l.boss).trim() && str(l.boss).trim() !== '—') chips.push(h('span', { class: 'w-mini', title: 'Jefe o evento de combate' }, '⚔'));
    var card = h('article', { class: 'card w-card w-loc-card w-act-edge-' + actNum(l.act) + (list ? ' w-loc-row' : '') },
      h('div', { class: 'w-loc-card-head' },
        h('span', { class: 'w-order', title: 'Orden de progresión' }, l.order != null ? String(l.order) : '·'),
        h('h3', { class: 'w-loc-card-title' }, REM.ui.link('location', l.key, l.name))),
      h('div', { class: 'w-badges' }, catBadge(l.category), actBadge(l.act), labelBadge(l)),
      lv ? h('div', { class: 'w-loc-lv' }, meta) : h('div', { class: 'w-loc-lv w-muted' }, 'Sin salvajes'),
      chips.length ? h('div', { class: 'w-loc-chips' }, chips) : null);
    return card;
  }

  /* ---------------------------------------------------------------- vista #/atlas */
  function renderAtlas(el) {
    var M = model();
    el.textContent = '';
    if (!M || !arr(M.locations).length) return noModel(el);
    var root = h('div', { class: 'w-view w-atlas' });
    root.appendChild(REM.ui.pageHeader({
      crumbs: [{ label: 'Inicio', href: '#/' }, { label: 'Atlas' }],
      title: 'Atlas de Oniria',
      sub: M.locations.length + ' ubicaciones: ciudades, pueblos, lugares especiales y rutas, ordenadas por progresión de la historia. Pulsa una para ver su ficha completa.',
      actions: [h('a', { class: 'btn', href: mapHref() }, '🗺️ Mapa interactivo'), h('a', { class: 'btn', href: '#/progression' }, '🧭 Progresión')]
    }));

    var results = h('div', { class: 'w-results', 'aria-live': 'polite' });
    var count = h('p', { class: 'w-count' });

    function paint() {
      var rows = sortRows(arr(M.locations).filter(matches));
      if (F.sort === 'order' && F.q === '' && !rows.length) rows = [];
      results.textContent = '';
      count.textContent = rows.length + ' de ' + M.locations.length + ' ubicaciones';
      if (!rows.length) { results.appendChild(emptyMsg('Ninguna ubicación coincide con los filtros.')); return; }
      var wrap = h('div', { class: 'w-grid' + (F.view === 'list' ? ' w-grid-list' : '') });
      rows.forEach(function (l) { wrap.appendChild(locCard(l, F.view === 'list')); });
      results.appendChild(wrap);
    }

    /* controles */
    var q = h('input', { type: 'search', class: 'input w-input', placeholder: 'Buscar nombre, jefe, personaje…', 'aria-label': 'Buscar ubicación', value: F.q });
    on(q, 'input', function () { F.q = q.value; paint(); });
    var cat = h('select', { class: 'input w-input', 'aria-label': 'Filtrar por categoría' },
      h('option', { value: '' }, 'Todas las categorías'),
      CAT_ORDER.map(function (c) { return h('option', { value: c }, c); }));
    cat.value = F.cat;
    on(cat, 'change', function () { F.cat = cat.value; paint(); });
    var sort = h('select', { class: 'input w-input', 'aria-label': 'Ordenar por' },
      h('option', { value: 'order' }, 'Orden de progresión'),
      h('option', { value: 'name' }, 'Nombre'),
      h('option', { value: 'cat' }, 'Categoría'),
      h('option', { value: 'level' }, 'Nivel salvaje'));
    sort.value = F.sort;
    on(sort, 'change', function () { F.sort = sort.value; paint(); });
    var lvMin = h('input', { type: 'number', class: 'input w-input w-input-num', min: '1', max: '100', placeholder: 'mín', 'aria-label': 'Nivel mínimo', value: F.lvMin });
    var lvMax = h('input', { type: 'number', class: 'input w-input w-input-num', min: '1', max: '100', placeholder: 'máx', 'aria-label': 'Nivel máximo', value: F.lvMax });
    on(lvMin, 'input', function () { F.lvMin = lvMin.value; paint(); });
    on(lvMax, 'input', function () { F.lvMax = lvMax.value; paint(); });

    var actBox = h('div', { class: 'w-chipset', role: 'group', 'aria-label': 'Filtrar por acto' });
    ACTS.forEach(function (a) {
      var b = h('button', { type: 'button', class: 'w-chip w-act-' + actNum(a), 'aria-pressed': F.acts[a] ? 'true' : 'false' }, 'Acto ' + a);
      on(b, 'click', function () {
        F.acts[a] = !F.acts[a];
        b.setAttribute('aria-pressed', F.acts[a] ? 'true' : 'false');
        paint();
      });
      actBox.appendChild(b);
    });
    function toggle(label, key) {
      var cb = h('input', { type: 'checkbox' });
      cb.checked = !!F[key];
      on(cb, 'change', function () { F[key] = cb.checked; paint(); });
      return h('label', { class: 'w-check' }, cb, h('span', null, label));
    }
    var viewBtns = h('div', { class: 'w-seg', role: 'group', 'aria-label': 'Tipo de vista' });
    ['grid', 'list'].forEach(function (v) {
      var b = h('button', { type: 'button', class: 'w-seg-btn', 'aria-pressed': F.view === v ? 'true' : 'false' }, v === 'grid' ? '▦ Rejilla' : '☰ Lista');
      on(b, 'click', function () {
        F.view = v;
        try { localStorage.setItem(UI_KEY, v); } catch (e) { /* sin almacenamiento */ }
        Array.prototype.forEach.call(viewBtns.children, function (x, i) { x.setAttribute('aria-pressed', (i === 0) === (v === 'grid') ? 'true' : 'false'); });
        paint();
      });
      viewBtns.appendChild(b);
    });
    var clear = h('button', { type: 'button', class: 'btn btn--sm' }, 'Limpiar filtros');
    on(clear, 'click', function () {
      F.q = ''; F.cat = ''; F.acts = {}; F.lvMin = ''; F.lvMax = ''; F.fish = false; F.shop = false; F.sort = 'order';
      renderAtlas(el);
    });

    root.appendChild(h('form', { class: 'w-filters w-card', role: 'search', 'aria-label': 'Filtros del atlas', onsubmit: function (e) { e.preventDefault(); } },
      h('div', { class: 'w-filter-row' }, h('label', { class: 'w-field w-field-grow' }, h('span', null, 'Texto'), q),
        h('label', { class: 'w-field' }, h('span', null, 'Categoría'), cat),
        h('label', { class: 'w-field' }, h('span', null, 'Orden'), sort)),
      h('div', { class: 'w-filter-row' },
        h('div', { class: 'w-field' }, h('span', null, 'Acto'), actBox),
        h('div', { class: 'w-field' }, h('span', null, 'Rango de niveles salvajes'), h('div', { class: 'w-inline' }, lvMin, h('span', null, '–'), lvMax)),
        h('div', { class: 'w-field w-checks' }, toggle('🎣 Tiene pesca', 'fish'), toggle('🛒 Tiene tienda', 'shop'))),
      h('div', { class: 'w-filter-row w-filter-foot' }, count, h('div', { class: 'w-inline' }, viewBtns, clear))));
    root.appendChild(results);
    el.appendChild(root);
    paint();
  }

  /* ---------------------------------------------------------------- vista #/location/<KEY> */
  function renderLocation(el, key) {
    var M = model();
    el.textContent = '';
    if (!M) return noModel(el);
    var loc = locByKey(key);
    if (!loc) {
      el.appendChild(h('div', { class: 'w-view' },
        h('p', null, h('a', { href: '#/atlas' }, '← Atlas')),
        emptyMsg('Sin datos: no existe la ubicación «' + str(key) + '».')));
      return;
    }
    var sorted = sortedLocs();
    var pos = -1;
    sorted.forEach(function (l, i) { if (l.key === loc.key) pos = i; });
    var prev = pos > 0 ? sorted[pos - 1] : null, next = pos >= 0 && pos < sorted.length - 1 ? sorted[pos + 1] : null;

    var root = h('article', { class: 'w-view w-loc w-act-edge-' + actNum(loc.act) });
    var drafts = arr(loc.draftNames).filter(Boolean);
    var stepsEl = arr(loc.steps).length ? h('span', { class: 'w-steps' }, h('b', null, 'Pasos de la progresión: '),
      arr(loc.steps).map(function (n, i) {
        return h('span', null, i ? ', ' : null, link('step', n, 'Paso ' + n));
      })) : null;
    root.appendChild(REM.ui.pageHeader({
      crumbs: [{ label: 'Atlas', href: '#/atlas' }, { label: normCat(loc.category) }, { label: str(loc.name) }],
      title: str(loc.name),
      sub: drafts.length ? 'Nombres en borrador: ' + drafts.join(' · ') : null,
      meta: [catBadge(loc.category), actBadge(loc.act), labelBadge(loc), loc.order != null ? badge('Progresión n.º ' + loc.order, 'w-order-b') : null, stepsEl],
      actions: [h('a', { class: 'btn', href: mapHref(loc.key) }, '🗺️ Ver en el mapa')]
    }));
    root.appendChild(h('div', { class: 'w-pager' },
      prev ? h('span', { class: 'w-pager-item' }, '← ', REM.ui.link('location', prev.key, prev.name)) : h('span', null),
      next ? h('span', { class: 'w-pager-item' }, REM.ui.link('location', next.key, next.name), ' →') : h('span', null)));

    /* columna lateral */
    var aside = h('aside', { class: 'w-loc-aside', 'aria-label': 'Resumen de la ubicación' },
      h('div', { class: 'card w-card' }, h('h2', { class: 'w-card-title' }, 'Mapa'), guard('minimapa', function () { return minimap(loc); })),
      h('div', { class: 'card w-card' }, h('h2', { class: 'w-card-title' }, 'Brújula'), guard('brújula', function () { return compass(loc); })),
      h('div', { class: 'card w-card' }, h('h2', { class: 'w-card-title' }, 'Niveles salvajes'),
        h('dl', { class: 'w-kv' },
          h('dt', null, '☀ Día'), h('dd', null, fmtRange(loc.levelDay)),
          h('dt', null, '☾ Noche'), h('dd', null, fmtRange(loc.levelNight)))));

    /* columna principal: cada bloque está protegido para que un dato raro no tumbe la ficha */
    var main = h('div', { class: 'w-loc-main' });
    function add(title, build, id, spoiler) {
      var body = guard(title, build);
      if (!body) return;
      var sec = section(title, body, id);
      if (spoiler) sec.firstChild.appendChild(h('span', { class: 'w-spoil-tag', title: 'Este bloque cuenta eventos de la trama' }, '⚠ spoilers'));
      main.appendChild(sec);
    }
    if (loc.situation) add('Situación en el mapa', function () { return richEl('p', 'w-prose', loc.situation); });
    if (loc.etymology) add('Etimología', function () { return richEl('p', 'w-prose', loc.etymology); });
    if (loc.description) add('Descripción ambiental', function () { return richEl('p', 'w-prose', loc.description); });
    add('Eventos principales', function () {
      var ev = arr(loc.events).filter(Boolean);
      return ev.length ? h('ul', { class: 'w-list' }, ev.map(function (e) { return richEl('li', null, e); })) : emptyMsg('Sin eventos registrados.');
    }, null, true);
    add('Jefe y combates clave', function () { return bossBlock(loc.boss); }, null, true);
    add('Personajes presentes', function () { return charsBlock(loc); });
    add('Pokémon salvajes y pesca', function () {
      var encs = arr(loc.encounters).filter(function (e) { return arr(e.slots).length; });
      var fish = loc.fishing && (loc.fishing.common || loc.fishing.rare) ? fishingBlock(loc.fishing) : null;
      var encBody = h('div', { class: 'w-encs' });
      encs.forEach(function (e) { encBody.appendChild(encounterBlock(e, loc)); });
      if (fish) encBody.appendChild(fish);
      if (!encs.length && !fish) encBody.appendChild(emptyMsg('Sin encuentros salvajes ni pesca en esta ubicación.'));
      return encBody;
    }, 'w-encounters');
    add('Objetos y MT de la ubicación', function () { return itemsBlock(loc.items); }, 'w-items');
    add('Tiendas', function () {
      var shops = arr(loc.shops), kind = catKind(loc.category);
      if (!shops.length && kind !== 'city' && kind !== 'town') return emptyMsg('Sin tiendas en esta ubicación.');
      var body = h('div', null);
      if (kind === 'city' || kind === 'town') {
        body.appendChild(h('p', { class: 'w-prose' }, 'Esta localidad dispone de Poké Mart estándar (mostrador acumulativo según las medallas). ',
          h('a', { href: '#/shops' }, 'Ver todas las tiendas')));
      }
      if (shops.length) {
        body.appendChild(h('ul', { class: 'w-chips' }, shops.map(function (sk) {
          var sh = idx('shopByKey')[sk];
          return h('li', null, link('shop', sk, sh ? sh.name : str(sk)));
        })));
      }
      return body;
    });
    add('Capítulos de las Crónicas ambientados aquí', function () {
      var chs = arr(loc.chapters);
      return chs.length ? h('ul', { class: 'w-chips' }, chs.map(function (c) {
        var ch = idx('chapterByKey')[c];
        return h('li', null, link('chapter', c, ch ? ch.title : str(c)));
      })) : emptyMsg('Ningún capítulo transcurre en esta ubicación.');
    }, null, true);

    root.appendChild(h('div', { class: 'w-loc-layout' }, main, aside));
    el.appendChild(root);
  }

  /* ---------------------------------------------------------------- registro */
  REM.router.register('atlas', { title: 'Atlas de Oniria', render: function (el) { renderAtlas(el); } });
  REM.router.register('location', {
    title: function (parts) { var l = locByKey(parts && parts[0]); return l ? l.name : 'Ubicación'; },
    render: function (el, parts) { renderLocation(el, (parts && parts[0]) || ''); }
  });

  if (REM.selftest && REM.selftest.add) {
    REM.selftest.add('atlas', function () {
      var M = model();
      var out = ['#/atlas'];
      arr(M && M.locations).forEach(function (l) { out.push('#/location/' + l.key); });
      return out;
    });
  }
})();
