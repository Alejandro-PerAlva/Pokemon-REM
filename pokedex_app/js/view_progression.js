/* ==========================================================================
   Pokémon REM Master Codex — Guía de Progresión y Level Caps
   Rutas: #/progression (línea de tiempo de 68 pasos + gráfico de topes) y #/progression/<n>
   Propiedad: codex-front-world. Solo usa la API pública de SPEC §5.
   Los resúmenes son SIN spoilers (campo `summary`).
   ========================================================================== */
(function () {
  'use strict';
  var REM = window.REM;
  if (!REM || !REM.router) return;
  var h = REM.h;
  var NS = 'http://www.w3.org/2000/svg';

  /* ---------------------------------------------------------------- utilidades */
  function model() { return (REM.state && REM.state.model) || null; }
  function arr(x) { return Array.isArray(x) ? x : []; }
  function str(x) { return x == null ? '' : String(x); }
  function idx(n) { return (REM.idx && REM.idx[n]) || {}; }
  function stripAcc(s) { return str(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); }
  function store(k, d) { return REM.util && REM.util.store ? REM.util.store.get(k, d) : d; }
  function storeSet(k, v) { if (REM.util && REM.util.store) REM.util.store.set(k, v); }
  function emptyMsg(msg) {
    return REM.ui && REM.ui.empty ? REM.ui.empty(msg || 'Sin datos') : h('p', { class: 'w-empty' }, msg || 'Sin datos');
  }
  function guard(label, fn, fallback) {
    try { return fn(); } catch (e) {
      if (REM.fail) REM.fail('progresión · ' + label, e);
      return fallback === undefined ? h('p', { class: 'w-empty' }, 'No se pudo mostrar esta sección.') : fallback;
    }
  }
  /* enlace solo si la entidad existe en el modelo; si no, texto plano */
  function link(kind, id, label) {
    if (id != null && id !== '' && REM.ent(kind, id)) return REM.ui.link(kind, id, label);
    return h('span', { class: 'w-plain' }, label != null ? label : str(id));
  }
  function pad2(n) { n = String(n); return n.length < 2 ? '0' + n : n; }
  function svg(tag, attrs) {
    var e = document.createElementNS(NS, tag);
    if (attrs) Object.keys(attrs).forEach(function (k) { if (attrs[k] != null) e.setAttribute(k, attrs[k]); });
    for (var i = 2; i < arguments.length; i++) {
      var c = arguments[i];
      if (c == null) continue;
      e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    }
    return e;
  }
  var ACTS = ['I', 'II', 'III', 'IV', 'V'];
  function actNum(a) { var i = ACTS.indexOf(str(a).toUpperCase()); return i < 0 ? 0 : i + 1; }
  function steps() {
    var M = model();
    return arr(M && M.progression).slice().sort(function (a, b) { return a.step - b.step; });
  }
  function locName(k) { var l = idx('locByKey')[k]; return l ? l.name : str(k); }
  function badge(text, cls, title) { return h('span', { class: 'badge w-badge ' + (cls || ''), title: title || null }, text); }

  /* tipo del jefe: acepta símbolo (FIRE), nombre en español (Fuego) o varios («Siniestro/Volador») */
  function typeNodes(txt) {
    var out = [];
    var t = str(txt).trim();
    if (!t) return out;
    var ts = arr(model() && model().types);
    function find(token) {
      var k = stripAcc(token).replace(/[^a-z0-9]/g, '');
      if (!k) return null;
      for (var i = 0; i < ts.length; i++) {
        if (stripAcc(ts[i].sym).replace(/[^a-z0-9]/g, '') === k || stripAcc(ts[i].name).replace(/[^a-z0-9]/g, '') === k) return ts[i];
      }
      return null;
    }
    var direct = find(t);
    if (direct) return [REM.ui.typeBadge(direct.sym)];
    t.split(/\s*(?:[\/,;·+]|\by\b|\be\b)\s*/i).forEach(function (tok) {
      var f = find(tok);
      if (f) out.push(REM.ui.typeBadge(f.sym));
      else if (tok.trim()) out.push(h('span', { class: 'w-plain' }, tok.trim()));
    });
    return out;
  }
  function bossKind(st) {
    var b = stripAcc(st.boss);
    if (!b) return '';
    if (/gimnasio|medalla/.test(b)) return 'gym';
    if (/alto mando|campe|liga/.test(b)) return 'elite';
    return 'boss';
  }
  var KIND_LABEL = { gym: 'Gimnasio', elite: 'Liga', boss: 'Jefe' };

  /* ---------------------------------------------------------------- «mi paso actual» */
  var MINE_KEY = 'rem-prog-mine';
  function getMine() {
    var v = parseInt(store(MINE_KEY, ''), 10);
    return isFinite(v) && v >= 1 && v <= 999 ? v : null;
  }
  function setMine(n) {
    if (n == null) { if (REM.util && REM.util.store) REM.util.store.del(MINE_KEY); }
    else storeSet(MINE_KEY, String(n));
  }
  var PLAYER_KEY = 'rem-prog-player';
  var SPOIL_KEY = 'rem-prog-spoil';
  function spoilOn() { return store(SPOIL_KEY, '0') === '1'; }

  /* campos opcionales del paso (el backend puede exponerlos con distinto nombre camelCase) */
  function ext(st, re) {
    var ks = Object.keys(st || {});
    for (var i = 0; i < ks.length; i++) if (re.test(ks[i]) && st[ks[i]] != null && st[ks[i]] !== '') return st[ks[i]];
    return null;
  }
  function asList(v) {
    if (v == null || v === '') return [];
    if (Array.isArray(v)) return v.map(str).filter(Boolean);
    return str(v).split(/\s*;\s*/).map(function (x) { return x.trim(); }).filter(Boolean);
  }
  function stepChapters(st) {
    var own = asList(ext(st, /^chapters$/i));
    if (own.length) return own;
    var loc = idx('locByKey')[st.loc];
    return loc ? arr(loc.chapters) : [];
  }

  /* ---------------------------------------------------------------- referencias */
  function tmRef(sym) {
    var e = REM.ent('tm', sym);
    if (!e) return h('span', { class: 'w-plain' }, str(sym));
    var mv = idx('moveBySym')[e.move];
    var n = e.number;
    return REM.ui.link('tm', e.number, 'MT' + pad2(n) + (mv ? ' ' + mv.name : ''));
  }
  function itemRefAny(v) {
    var e = REM.ent('item', v) || (/^(TM|MT)\d+$/i.test(str(v)) ? null : null);
    if (e) return h('span', { class: 'w-item' }, REM.ui.itemIcon ? REM.ui.itemIcon(e, { size: 24 }) : null, REM.ui.link('item', e.sym, e.name));
    if (/^(TM|MT)\s*\d+$/i.test(str(v)) && REM.ent('tm', v)) return tmRef(v);
    return h('span', { class: 'w-plain' }, str(v));
  }
  /* Todo lo que revela trama del paso (jefe/gimnasio, eventos clave, capítulos) va tras un aviso plegable. */
  function bossDetails(st, open) {
    var keyEv = ext(st, /^keyevents?$/i);
    var chapters = stepChapters(st);
    if (!st.boss && !keyEv && !chapters.length) return null;
    var inner = h('div', { class: 'w-spoiler-body' },
      st.boss ? bossBlock(st) : null,
      keyEv ? h('p', { class: 'w-keyev' }, h('b', null, 'Eventos clave: '), str(keyEv)) : null,
      chapters.length ? h('p', { class: 'w-extra' }, h('b', null, 'Capítulos: '), chapters.map(function (c, i) {
        var ch = REM.ent('chapter', c);
        var n = /CHAPTER_0*(\d+)/.exec(str(c));
        return h('span', null, i ? ', ' : null, link('chapter', c, (n ? n[1] + '. ' : '') + (ch ? str(ch.title) : str(c))));
      })) : null);
    var d = h('details', { class: 'w-spoiler' },
      h('summary', null, h('span', { class: 'w-spoiler-ico', 'aria-hidden': 'true' }, '⚠'), ' Combate clave y eventos ', h('small', null, '— contiene spoilers, pulsa para mostrar')),
      inner);
    if (open) d.open = true;
    return d;
  }
  function bossBlock(st, compact) {
    if (!st.boss) return null;
    var k = bossKind(st);
    var types = typeNodes(st.bossType);
    return h('div', { class: 'w-boss-line w-boss-' + k },
      h('span', { class: 'w-boss-kind', title: KIND_LABEL[k] || '' }, k === 'gym' ? '🏅' : k === 'elite' ? '🏆' : '⚔'),
      h('b', { class: 'w-boss-title' }, str(st.boss)),
      types.length ? h('span', { class: 'w-boss-types' }, types) : null,
      st.bossLevel != null && st.bossLevel !== '' ? h('span', { class: 'w-boss-lv', title: 'Nivel del As (Pokémon más fuerte)' }, 'As Nv ' + st.bossLevel) : null);
  }

  /* ---------------------------------------------------------------- gráfico SVG de topes de nivel */
  function buildChart(list, opts) {
    opts = opts || {};
    var W = 960, H = opts.compact ? 230 : 340;
    var m = { l: 42, r: 16, t: 28, b: 32 };
    var iw = W - m.l - m.r, ih = H - m.t - m.b;
    var n = list.length;
    if (!n) return emptyMsg('Sin datos de progresión.');
    var maxLv = 0;
    list.forEach(function (s) { [s.levelCapDay, s.levelCapNight, s.bossLevel].forEach(function (v) { if (isFinite(v) && v > maxLv) maxLv = +v; }); });
    var yMax = Math.max(20, Math.ceil(maxLv / 10) * 10);
    var first = list[0].step, last = list[n - 1].step, span = Math.max(1, last - first);
    function X(s) { return m.l + (s - first) / span * iw; }
    function Y(v) { return m.t + ih - (v / yMax) * ih; }
    var root = svg('svg', {
      class: 'w-chart', viewBox: '0 0 ' + W + ' ' + H, role: 'img', preserveAspectRatio: 'xMidYMid meet',
      'aria-label': 'Gráfico de topes de nivel por paso: línea de día y línea de noche, con marcadores de gimnasios y jefes'
    });
    root.appendChild(svg('title', null, 'Topes de nivel por paso de la progresión'));
    /* bandas por acto */
    var bands = {};
    list.forEach(function (s) {
      var a = str(s.act).toUpperCase();
      if (!bands[a]) bands[a] = { a: a, from: s.step, to: s.step };
      bands[a].to = s.step;
    });
    Object.keys(bands).forEach(function (a) {
      var b = bands[a], x0 = X(b.from - 0.5), x1 = X(b.to + 0.5);
      x0 = Math.max(m.l, x0); x1 = Math.min(m.l + iw, x1);
      root.appendChild(svg('rect', { class: 'w-ch-band w-act-bg-' + actNum(a), x: x0, y: m.t, width: Math.max(0, x1 - x0), height: ih }));
      root.appendChild(svg('text', { class: 'w-ch-act', x: (x0 + x1) / 2, y: m.t - 10, 'text-anchor': 'middle' }, 'Acto ' + a));
    });
    /* rejilla y eje Y */
    for (var v = 0; v <= yMax; v += 10) {
      root.appendChild(svg('line', { class: 'w-ch-grid', x1: m.l, x2: m.l + iw, y1: Y(v), y2: Y(v) }));
      root.appendChild(svg('text', { class: 'w-ch-tick', x: m.l - 6, y: Y(v) + 3.5, 'text-anchor': 'end' }, String(v)));
    }
    /* eje X */
    list.forEach(function (s) {
      if (s.step === first || s.step === last || s.step % 5 === 0) {
        root.appendChild(svg('text', { class: 'w-ch-tick', x: X(s.step), y: H - m.b + 16, 'text-anchor': 'middle' }, String(s.step)));
        root.appendChild(svg('line', { class: 'w-ch-tickline', x1: X(s.step), x2: X(s.step), y1: m.t + ih, y2: m.t + ih + 4 }));
      }
    });
    root.appendChild(svg('text', { class: 'w-ch-axis', x: m.l + iw / 2, y: H - 4, 'text-anchor': 'middle' }, 'Paso de la progresión'));
    root.appendChild(svg('text', { class: 'w-ch-axis', x: 12, y: m.t + ih / 2, 'text-anchor': 'middle', transform: 'rotate(-90 12 ' + (m.t + ih / 2) + ')' }, 'Nivel'));
    /* líneas día / noche (escalonadas: el tope vale hasta el siguiente cambio) */
    function stepped(key) {
      var d = '', prev = null;
      list.forEach(function (s) {
        var v = isFinite(s[key]) ? +s[key] : null;
        if (v == null) return;
        if (prev == null) d += 'M' + X(s.step) + ' ' + Y(v);
        else d += 'L' + X(s.step) + ' ' + Y(prev) + 'L' + X(s.step) + ' ' + Y(v);
        prev = v;
      });
      return d;
    }
    var dN = stepped('levelCapNight'), dD = stepped('levelCapDay');
    if (dN) root.appendChild(svg('path', { class: 'w-ch-line w-ch-night', d: dN, fill: 'none' }));
    if (dD) root.appendChild(svg('path', { class: 'w-ch-line w-ch-day', d: dD, fill: 'none' }));
    /* «mi paso» y paso actual */
    var mine = opts.mine;
    if (mine != null && mine >= first && mine <= last) {
      root.appendChild(svg('line', { class: 'w-ch-mine', x1: X(mine), x2: X(mine), y1: m.t, y2: m.t + ih }));
      root.appendChild(svg('text', { class: 'w-ch-minelbl', x: X(mine), y: m.t + 12, 'text-anchor': mine > last * 0.85 ? 'end' : 'start', dx: mine > last * 0.85 ? -4 : 4 }, 'Estás aquí · paso ' + mine));
    }
    if (opts.current != null) {
      root.appendChild(svg('line', { class: 'w-ch-cur', x1: X(opts.current), x2: X(opts.current), y1: m.t, y2: m.t + ih }));
    }
    /* marcadores de jefes: solo con «mostrar spoilers» */
    list.forEach(function (s) {
      if (!opts.showBoss) return;
      var k = bossKind(s);
      if (!k) return;
      var lv = isFinite(s.bossLevel) && s.bossLevel !== null && s.bossLevel !== '' ? +s.bossLevel : (isFinite(s.levelCapDay) ? +s.levelCapDay : null);
      if (lv == null) return;
      var cx = X(s.step), cy = Y(lv);
      var a = svg('a', { href: REM.router.href('step', s.step), class: 'w-ch-mark w-ch-' + k, 'aria-label': 'Paso ' + s.step + ': ' + str(s.boss) + (s.bossLevel ? ', As nivel ' + s.bossLevel : '') });
      a.appendChild(svg('title', null, 'Paso ' + s.step + ' · ' + str(s.boss) + (s.bossLevel ? ' (As Nv ' + s.bossLevel + ')' : '')));
      a.appendChild(svg('line', { class: 'w-ch-stem', x1: cx, x2: cx, y1: cy, y2: m.t + ih }));
      if (k === 'gym') a.appendChild(svg('circle', { class: 'w-ch-shape', cx: cx, cy: cy, r: 5.5 }));
      else if (k === 'elite') a.appendChild(svg('path', { class: 'w-ch-shape', d: 'M' + cx + ' ' + (cy - 7) + 'L' + (cx + 2.2) + ' ' + (cy - 2.2) + 'L' + (cx + 7) + ' ' + (cy - 2) + 'L' + (cx + 3.2) + ' ' + (cy + 1.6) + 'L' + (cx + 4.4) + ' ' + (cy + 6.6) + 'L' + cx + ' ' + (cy + 3.8) + 'L' + (cx - 4.4) + ' ' + (cy + 6.6) + 'L' + (cx - 3.2) + ' ' + (cy + 1.6) + 'L' + (cx - 7) + ' ' + (cy - 2) + 'L' + (cx - 2.2) + ' ' + (cy - 2.2) + 'Z' }));
      else a.appendChild(svg('path', { class: 'w-ch-shape', d: 'M' + cx + ' ' + (cy - 6) + 'L' + (cx + 5.5) + ' ' + (cy + 4.5) + 'L' + (cx - 5.5) + ' ' + (cy + 4.5) + 'Z' }));
      root.appendChild(a);
    });
    var legend = h('ul', { class: 'w-ch-legend', 'aria-label': 'Leyenda del gráfico' },
      h('li', null, h('span', { class: 'w-sw w-sw-day' }), ' Tope de día'),
      h('li', null, h('span', { class: 'w-sw w-sw-night' }), ' Tope de noche'),
      opts.showBoss ? h('li', null, h('span', { class: 'w-lg-shape w-lg-gym' }), ' Gimnasio (Nv del As)') : null,
      opts.showBoss ? h('li', null, h('span', { class: 'w-lg-shape w-lg-boss' }), ' Jefe / Dominante') : null,
      opts.showBoss ? h('li', null, h('span', { class: 'w-lg-shape w-lg-elite' }), ' Liga y Campeón') : null,
      !opts.showBoss ? h('li', { class: 'w-muted' }, 'Los marcadores de jefes y gimnasios están ocultos (spoilers).') : null);
    return h('figure', { class: 'w-chart-fig' }, h('div', { class: 'w-chart-scroll' }, root), legend);
  }

  /* ---------------------------------------------------------------- fila de la línea de tiempo */
  function stepRow(st, ctx) {
    var mine = ctx.mine, player = ctx.player;
    var future = player && mine != null && st.step > mine;
    var current = player && mine != null && st.step === mine;
    var cls = 'w-step w-act-edge-' + actNum(st.act) + (future ? ' is-future' : '') + (current ? ' is-mine' : '');
    var tms = arr(st.tms), keys = arr(st.keyItems);
    var mineBtn = h('button', { type: 'button', class: 'btn btn--sm w-mine-btn', 'aria-pressed': current ? 'true' : 'false', title: 'Marcar este paso como el actual de mi partida' },
      current ? '📍 Estás aquí' : '📍 Marcar paso');
    mineBtn.addEventListener('click', function () { ctx.setMine(current ? null : st.step); });
    return h('li', { class: cls, id: 'paso-' + st.step },
      h('a', { class: 'w-step-num', href: REM.router.href('step', st.step), 'aria-label': 'Abrir el paso ' + st.step }, String(st.step)),
      h('div', { class: 'w-step-body' },
        h('div', { class: 'w-step-top' },
          h('b', { class: 'w-step-loc' }, link('location', st.loc, locName(st.loc))),
          h('span', { class: 'w-caps', title: 'Topes de nivel (día / noche)' },
            h('span', { class: 'w-cap w-cap-day' }, '☀ ' + (st.levelCapDay != null ? st.levelCapDay : '—')),
            h('span', { class: 'w-cap w-cap-night' }, '☾ ' + (st.levelCapNight != null ? st.levelCapNight : '—'))),
          mineBtn),
        st.summary ? h('p', { class: 'w-step-sum' }, str(st.summary)) : null,
        bossDetails(st, ctx.spoil),
        (tms.length || keys.length || ext(st, /medals/i) != null) ? h('div', { class: 'w-step-extra' },
          ext(st, /medals/i) != null ? h('span', { class: 'w-extra' }, h('b', null, 'Medallas: '), str(ext(st, /medals/i))) : null,
          tms.length ? h('span', { class: 'w-extra' }, h('b', null, 'MT: '), tms.map(function (t, i) { return h('span', null, i ? ', ' : null, tmRef(t)); })) : null,
          keys.length ? h('span', { class: 'w-extra' }, h('b', null, 'Objetos clave: '), keys.map(function (k, i) { return h('span', null, i ? ', ' : null, itemRefAny(k)); })) : null) : null));
  }

  /* ---------------------------------------------------------------- vista #/progression */
  var FILTER = { acts: {}, bosses: false };
  function renderList(el) {
    var M = model();
    var list = steps();
    if (!M || !list.length) {
      el.appendChild(h('div', { class: 'w-view' }, h('h1', null, 'Guía de Progresión'), emptyMsg('Sin datos: el modelo no contiene pasos de progresión.')));
      return;
    }
    var player = store(PLAYER_KEY, '') === '1';
    var spoil = spoilOn();
    var mine = getMine();
    if (mine != null && mine > list.length) mine = null;

    var results = h('div', { class: 'w-timeline' });
    var chartBox = h('div', { class: 'card w-card w-chart-card' });
    var count = h('p', { class: 'w-count', 'aria-live': 'polite' });
    var mineInfo = h('p', { class: 'w-mine-info' });

    var sel = null;
    function setMine(n) {
      mine = n;
      if (n == null) { if (REM.util && REM.util.store) REM.util.store.del(MINE_KEY); } else storeSet(MINE_KEY, String(n));
      paintAll();
    }

    function visible(st) {
      var anyAct = ACTS.some(function (a) { return FILTER.acts[a]; });
      if (anyAct && !FILTER.acts[str(st.act).toUpperCase()]) return false;
      if (FILTER.bosses && !bossKind(st)) return false;
      return true;
    }
    function paintChart() {
      chartBox.textContent = '';
      chartBox.appendChild(h('h2', { class: 'w-card-title' }, 'Topes de nivel por paso'));
      chartBox.appendChild(h('p', { class: 'w-muted w-small' }, 'La línea de día y la de noche muestran el nivel máximo recomendado en cada paso; los marcadores indican el nivel del As de cada gimnasio o jefe.'));
      chartBox.appendChild(guard('gráfico', function () { return buildChart(list, { mine: player ? mine : null, showBoss: spoil }); }));
    }
    function paintTimeline() {
      results.textContent = '';
      var shown = 0;
      ACTS.forEach(function (a) {
        var rows = list.filter(function (s) { return str(s.act).toUpperCase() === a && visible(s); });
        if (!rows.length) return;
        shown += rows.length;
        var all = list.filter(function (s) { return str(s.act).toUpperCase() === a; });
        var ol = h('ol', { class: 'w-steps-list' });
        rows.forEach(function (s) {
          guard('paso ' + s.step, function () {
            ol.appendChild(stepRow(s, { mine: mine, player: player, setMine: setMine, spoil: spoil }));
            return null;
          }, null);
        });
        results.appendChild(h('section', { class: 'w-act-sec', 'aria-label': 'Acto ' + a },
          h('h2', { class: 'w-act-head w-act-edge-' + actNum(a) },
            h('span', { class: 'badge w-badge w-act-' + actNum(a) }, 'Acto ' + a),
            h('span', { class: 'w-muted' }, ' pasos ' + all[0].step + '–' + all[all.length - 1].step)),
          ol));
      });
      if (!shown) results.appendChild(emptyMsg('Ningún paso coincide con los filtros.'));
      count.textContent = shown + ' de ' + list.length + ' pasos';
    }
    function paintMineInfo() {
      mineInfo.textContent = '';
      if (!player) return;
      if (mine == null) { mineInfo.appendChild(document.createTextNode('Pulsa «Marcar paso» en cualquier paso para indicar dónde vas; lo posterior se atenuará.')); return; }
      var st = idx('stepByNum')[mine];
      mineInfo.appendChild(h('b', null, '📍 Mi paso actual: ' + mine));
      if (st) mineInfo.appendChild(document.createTextNode(' · ' + locName(st.loc) + ' · tope ☀ ' + st.levelCapDay + ' / ☾ ' + st.levelCapNight + ' · '));
      var go = h('a', { href: '#paso-' + mine, class: 'w-link-btn' }, 'ir al paso');
      go.addEventListener('click', function (ev) { ev.preventDefault(); var t = document.getElementById('paso-' + mine); if (t) t.scrollIntoView({ block: 'center', behavior: 'smooth' }); });
      mineInfo.appendChild(go);
      mineInfo.appendChild(document.createTextNode(' · '));
      var clr = h('button', { type: 'button', class: 'w-link-btn' }, 'olvidar');
      clr.addEventListener('click', function () { setMine(null); });
      mineInfo.appendChild(clr);
    }
    function paintAll() {
      paintChart(); paintTimeline(); paintMineInfo();
      results.classList.toggle('is-player', player && mine != null);
      if (sel) sel.value = mine != null ? String(mine) : '';
    }

    /* controles */
    var actBox = h('div', { class: 'w-chipset', role: 'group', 'aria-label': 'Filtrar por acto' });
    ACTS.forEach(function (a) {
      var b = h('button', { type: 'button', class: 'w-chip w-act-' + actNum(a), 'aria-pressed': FILTER.acts[a] ? 'true' : 'false' }, 'Acto ' + a);
      b.addEventListener('click', function () { FILTER.acts[a] = !FILTER.acts[a]; b.setAttribute('aria-pressed', FILTER.acts[a] ? 'true' : 'false'); paintTimeline(); });
      actBox.appendChild(b);
    });
    var cbBoss = h('input', { type: 'checkbox' }); cbBoss.checked = FILTER.bosses;
    cbBoss.addEventListener('change', function () { FILTER.bosses = cbBoss.checked; paintTimeline(); });
    var cbSpoil = h('input', { type: 'checkbox' }); cbSpoil.checked = spoil;
    cbSpoil.addEventListener('change', function () { spoil = cbSpoil.checked; storeSet(SPOIL_KEY, spoil ? '1' : '0'); paintAll(); });
    var cbPlayer = h('input', { type: 'checkbox' }); cbPlayer.checked = player;
    cbPlayer.addEventListener('change', function () { player = cbPlayer.checked; storeSet(PLAYER_KEY, player ? '1' : '0'); paintAll(); });
    sel = h('select', { class: 'input w-input', 'aria-label': 'Mi paso actual' },
      h('option', { value: '' }, '— elegir —'),
      list.map(function (s) { return h('option', { value: String(s.step) }, 'Paso ' + s.step + ' · ' + locName(s.loc)); }));
    sel.addEventListener('change', function () { setMine(sel.value ? parseInt(sel.value, 10) : null); });

    var header = REM.ui.pageHeader({
      crumbs: [{ label: 'Inicio', href: '#/' }, { label: 'Progresión' }],
      title: 'Guía de Progresión y Level Caps',
      sub: list.length + ' pasos agrupados en cinco actos, con el tope de nivel recomendado de día y de noche, los jefes de cada tramo, las MT disponibles y los objetos clave. Los resúmenes no contienen spoilers.',
      actions: [h('a', { class: 'btn', href: '#/map' }, '🗺️ Mapa'), h('a', { class: 'btn', href: '#/story' }, '📜 Crónicas')]
    });
    var controls = h('div', { class: 'w-filters w-card' },
      h('div', { class: 'w-filter-row' },
        h('div', { class: 'w-field' }, h('span', null, 'Acto'), actBox),
        h('div', { class: 'w-field w-checks' }, h('span', null, 'Mostrar'),
          h('label', { class: 'w-check' }, cbBoss, h('span', null, 'Solo pasos con jefe o gimnasio')),
          h('label', { class: 'w-check' }, cbSpoil, h('span', null, '⚠ Mostrar jefes y gimnasios (spoilers)'))),
        h('div', { class: 'w-field w-checks' }, h('span', null, 'Modo jugador'),
          h('label', { class: 'w-check' }, cbPlayer, h('span', null, 'Atenuar lo posterior a mi paso')),
          h('label', { class: 'w-field-inline' }, h('span', null, 'Mi paso: '), sel))),
      h('div', { class: 'w-filter-row w-filter-foot' }, count, mineInfo));
    el.appendChild(h('div', { class: 'w-view w-prog' }, header, chartBox, controls, results));
    paintAll();
  }

  /* ---------------------------------------------------------------- vista #/progression/<n> */
  function renderStep(el, n) {
    var list = steps();
    var st = idx('stepByNum')[n];
    if (!st) {
      el.appendChild(h('div', { class: 'w-view' }, h('p', null, h('a', { href: '#/progression' }, '← Guía de progresión')), emptyMsg('Sin datos: no existe el paso ' + n + '.')));
      return;
    }
    var i = list.indexOf(st);
    var prev = i > 0 ? list[i - 1] : null, next = i >= 0 && i < list.length - 1 ? list[i + 1] : null;
    var mine = getMine();
    var loc = idx('locByKey')[st.loc];
    var mineBtn = h('button', { type: 'button', class: 'btn', 'aria-pressed': mine === st.step ? 'true' : 'false' }, mine === st.step ? '📍 Este es mi paso actual' : '📍 Marcar como mi paso actual');
    mineBtn.addEventListener('click', function () {
      var now = getMine() === st.step;
      if (now) { if (REM.util && REM.util.store) REM.util.store.del(MINE_KEY); } else storeSet(MINE_KEY, String(st.step));
      var isMine = !now;
      mineBtn.textContent = isMine ? '📍 Este es mi paso actual' : '📍 Marcar como mi paso actual';
      mineBtn.setAttribute('aria-pressed', isMine ? 'true' : 'false');
    });
    function nav(s, dir) {
      if (!s) return h('span', null);
      return h('a', { class: 'btn w-nav-' + dir, href: REM.router.href('step', s.step) },
        dir === 'prev' ? '← Paso ' + s.step + ' · ' + locName(s.loc) : 'Paso ' + s.step + ' · ' + locName(s.loc) + ' →');
    }
    var header = REM.ui.pageHeader({
      crumbs: [{ label: 'Progresión', href: '#/progression' }, { label: 'Acto ' + str(st.act) }, { label: 'Paso ' + st.step }],
      title: 'Paso ' + st.step + ' de ' + list.length + ' · ' + locName(st.loc),
      sub: st.summary ? str(st.summary) : null,
      meta: [badge('Acto ' + str(st.act), 'w-act-' + actNum(st.act)), loc ? badge(str(loc.category), 'w-cat') : null],
      actions: [mineBtn]
    });
    var facts = h('div', { class: 'card w-card' },
      h('h2', { class: 'w-card-title' }, 'Topes de nivel'),
      h('div', { class: 'w-caps-big' },
        h('div', { class: 'w-capbox w-cap-day' }, h('span', { class: 'w-cap-ico' }, '☀'), h('b', null, st.levelCapDay != null ? String(st.levelCapDay) : '—'), h('small', null, 'Tope de día')),
        h('div', { class: 'w-capbox w-cap-night' }, h('span', { class: 'w-cap-ico' }, '☾'), h('b', null, st.levelCapNight != null ? String(st.levelCapNight) : '—'), h('small', null, 'Tope de noche'))),
      h('p', { class: 'w-muted w-small' }, 'Nivel máximo recomendado de tu equipo en este paso; no te pases mucho para conservar el reto.'));
    var bossD = guard('jefe', function () { return bossDetails(st, spoilOn()); }, null);
    var boss = h('div', { class: 'card w-card' }, h('h2', { class: 'w-card-title' }, 'Jefe, gimnasio y eventos clave'),
      bossD || emptyMsg('Sin combate de jefe en este paso.'));
    var medals = ext(st, /medals/i), cumul = ext(st, /cumulative/i), fieldAb = asList(ext(st, /fieldabil/i));
    var progress = (medals != null || cumul != null || fieldAb.length) ? h('div', { class: 'card w-card' }, h('h2', { class: 'w-card-title' }, 'Estado de la partida tras este paso'),
      h('dl', { class: 'w-kv' },
        medals != null ? h('dt', null, 'Medallas') : null, medals != null ? h('dd', null, str(medals)) : null,
        cumul != null ? h('dt', null, 'MT acumuladas') : null, cumul != null ? h('dd', null, str(cumul)) : null,
        fieldAb.length ? h('dt', null, 'Habilidades de campo') : null, fieldAb.length ? h('dd', null, fieldAb.join(' · ')) : null)) : null;
    var tms = arr(st.tms), keys = arr(st.keyItems);
    var rewards = h('div', { class: 'card w-card' }, h('h2', { class: 'w-card-title' }, 'MT recomendadas y objetos clave'),
      h('h3', { class: 'w-side-sub' }, 'MT disponibles'),
      tms.length ? h('ul', { class: 'w-chips' }, tms.map(function (t) { return h('li', null, tmRef(t)); })) : h('p', { class: 'w-muted' }, 'Ninguna MT nueva en este paso.'),
      h('h3', { class: 'w-side-sub' }, 'Objetos clave desbloqueados'),
      keys.length ? h('ul', { class: 'w-chips' }, keys.map(function (k) { return h('li', null, itemRefAny(k)); })) : h('p', { class: 'w-muted' }, 'Ninguno.'));
    var where = h('div', { class: 'card w-card' }, h('h2', { class: 'w-card-title' }, 'Dónde'),
      h('p', null, h('b', null, 'Ubicación: '), link('location', st.loc, locName(st.loc))),
      loc ? h('dl', { class: 'w-kv' },
        h('dt', null, 'Categoría'), h('dd', null, str(loc.category)),
        h('dt', null, '☀ Salvajes día'), h('dd', null, REM.fmtRange(loc.levelDay)),
        h('dt', null, '☾ Salvajes noche'), h('dd', null, REM.fmtRange(loc.levelNight))) : null,
      h('p', { class: 'w-links' },
        h('a', { class: 'btn btn--sm', href: '#/map?loc=' + encodeURIComponent(str(st.loc)) + '&step=' + st.step }, '🗺️ Ver en el mapa'),
        ' ', loc ? REM.ui.link('location', st.loc, 'Ficha en el Atlas') : null));
    /* contexto: pasos vecinos */
    var ctxList = list.slice(Math.max(0, i - 3), Math.min(list.length, i + 4));
    var context = h('div', { class: 'card w-card' }, h('h2', { class: 'w-card-title' }, 'Contexto'),
      h('ol', { class: 'w-ctx' }, ctxList.map(function (s) {
        return h('li', { class: s.step === st.step ? 'is-cur' : null },
          h('a', { href: REM.router.href('step', s.step) }, h('b', null, String(s.step)), ' · ', locName(s.loc),
            h('small', { class: 'w-muted' }, ' ☀' + s.levelCapDay + ' ☾' + s.levelCapNight + '')));
      })));
    var chart = h('div', { class: 'card w-card w-chart-card' }, h('h2', { class: 'w-card-title' }, 'Este paso en el gráfico de topes'),
      guard('gráfico', function () { return buildChart(list, { current: st.step, compact: true, mine: mine, showBoss: spoilOn() }); }));
    el.appendChild(h('div', { class: 'w-view w-prog w-prog-step' }, header,
      h('div', { class: 'w-pager w-pager-top' }, nav(prev, 'prev'), nav(next, 'next')),
      h('div', { class: 'w-two' }, h('div', { class: 'w-col' }, facts, boss, rewards, progress), h('div', { class: 'w-col' }, where, context)),
      chart,
      h('div', { class: 'w-pager' }, nav(prev, 'prev'), nav(next, 'next'))));
  }

  /* ---------------------------------------------------------------- registro */
  REM.router.register('progression', {
    title: function (parts) { return parts && parts[0] ? 'Paso ' + parts[0] + ' · Progresión' : 'Guía de Progresión y Level Caps'; },
    render: function (el, parts) {
      var p = parts && parts[0];
      if (p == null || p === '') return renderList(el);
      return renderStep(el, parseInt(p, 10));
    }
  });

  if (REM.selftest && REM.selftest.add) {
    REM.selftest.add('progression', function () {
      var out = ['#/progression'];
      steps().forEach(function (s) { out.push('#/progression/' + s.step); });
      return out;
    });
  }
})();
