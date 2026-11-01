/* ==========================================================================
 * Pokémon REM Master Codex — search.js
 * Buscador global difuso (paleta Ctrl+K y buscador grande de Inicio).
 *   REM.search.query(text, {limit, kinds}) -> [{kind,id,label,sub,score}]
 *   REM.search.open()  /  REM.search.close()
 *   REM.search.widget({inline:true, placeholder, onPick}) -> Node (buscador incrustable)
 * ========================================================================== */
(function (global) {
  'use strict';
  var REM = global.REM, h = REM.h;
  var S = REM.search = REM.search || {};

  var KIND_ES = { pokemon: 'Pokémon', move: 'Movimiento', ability: 'Habilidad', item: 'Objeto', tm: 'MT',
    location: 'Ubicación', character: 'Personaje', chapter: 'Capítulo', step: 'Paso', shop: 'Tienda' };
  var KIND_ICON = { pokemon: '🐾', move: '⚔️', ability: '✨', item: '🎒', tm: '💿', location: '📍', character: '👤', chapter: '📜', step: '📈', shop: '🏪' };
  var KIND_BONUS = { pokemon: 6, move: 5, ability: 5, item: 4, tm: 4, location: 5, character: 3, chapter: 2, step: 1, shop: 1 };
  S.KIND_ES = KIND_ES;

  var entries = [], built = null;

  function add(kind, id, label, sub, keys, extra) {
    var nk = [];
    keys.forEach(function (k) { if (k != null && k !== '') { var n = REM.norm(k); if (n) nk.push(n); } });
    entries.push({ kind: kind, id: id, label: String(label == null ? id : label), sub: sub || '', keys: nk, extra: extra || null });
  }

  /* (Re)construye el índice a partir del modelo. */
  function build() {
    var m = REM.state.model, ix = REM.idx;
    if (!m || built === m) return;
    entries = []; built = m;
    var tName = function (s) { return REM.ui && REM.ui.typeName ? REM.ui.typeName(s) : s; };
    (m.pokemon || []).forEach(function (p) {
      var t = (p.types || []).map(tName);
      add('pokemon', p.dex, p.name, '#' + REM.pad3(p.dex) + ' · ' + t.join(' / '), [p.name, p.sym, REM.pad3(p.dex), String(p.dex), '#' + p.dex], { dex: p.dex });
    });
    (m.moves || []).forEach(function (x) {
      add('move', x.sym, x.name, tName(x.type) + ' · ' + ((REM.ui && REM.ui.CAT_ES[x.category]) || x.category || '') + (x.power ? ' · pot. ' + x.power : ''), [x.name, x.sym.replace(/_/g, ' ')]);
    });
    (m.abilities || []).forEach(function (x) { add('ability', x.sym, x.name, 'Habilidad' + (x.status ? '' : ''), [x.name, x.sym.replace(/_/g, ' ')]); });
    var tmSyms = {};
    (m.tms || []).forEach(function (t) {
      var mv = ix.moveBySym[t.move];
      tmSyms[t.sym] = 1;
      var mn = REM.pad2 ? REM.pad2(t.number) : (t.number < 10 ? '0' + t.number : String(t.number));
      add('tm', t.number, 'MT' + mn + ' · ' + (mv ? mv.name : t.move), mv ? (tName(mv.type) + ' · ' + t.learners.length + ' aprendices') : '', ['MT' + mn, 'MT' + t.number, 'TM' + mn, mv && mv.name, t.move]);
    });
    (m.items || []).forEach(function (x) {
      if (tmSyms[x.sym] || /^TM\d+$/.test(x.sym)) return;
      add('item', x.sym, x.name, x.pocketName || '', [x.name, x.plural, x.sym.replace(/_/g, ' ')], { icon: x.icon });
    });
    (m.locations || []).forEach(function (x) {
      add('location', x.key, x.name, x.category || '', [x.name].concat(x.draftNames || []).concat([x.key.replace(/_/g, ' ')]));
    });
    (m.characters || []).forEach(function (x) {
      var al = x.aliases; if (typeof al === 'string') al = al.split(/[;,]/);
      add('character', x.key, x.name, x.role || x.category || '', [x.name].concat(al || []));
    });
    (m.story || []).forEach(function (x) {
      var n = String(x.key).replace(/^CHAPTER_0*/, '');
      add('chapter', x.key, x.title || x.key, 'Capítulo ' + n + (x.act ? ' · Acto ' + x.act : ''), [x.title, 'capitulo ' + n, 'cap ' + n, x.key.replace(/_/g, ' ')]);
    });
    (m.shops || []).forEach(function (x) { add('shop', x.key, x.name || x.key, 'Tienda', [x.name, x.key.replace(/_/g, ' ')]); });
  }

  /* Distancia de edición con tope (devuelve > max si se pasa). */
  function lev(a, b, max) {
    var la = a.length, lb = b.length;
    if (Math.abs(la - lb) > max) return max + 1;
    var prev = [], cur = [], i, j;
    for (j = 0; j <= lb; j++) prev[j] = j;
    for (i = 1; i <= la; i++) {
      cur[0] = i; var rowMin = i;
      for (j = 1; j <= lb; j++) {
        var c = a.charCodeAt(i - 1) === b.charCodeAt(j - 1) ? 0 : 1;
        cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + c);
        if (cur[j] < rowMin) rowMin = cur[j];
      }
      if (rowMin > max) return max + 1;
      var t = prev; prev = cur; cur = t;
    }
    return prev[lb];
  }

  function scoreKey(key, q, qTokens) {
    if (key === q) return 1000;
    if (key.indexOf(q) === 0) return 820 - Math.min(60, key.length - q.length);
    var wi = key.indexOf(' ' + q);
    if (wi >= 0) return 640 - Math.min(60, wi);
    var si = key.indexOf(q);
    if (si >= 0) return 440 - Math.min(80, si);
    if (qTokens.length > 1) {
      var all = qTokens.every(function (t) { return key.indexOf(t) >= 0; });
      if (all) return 380;
    }
    return 0;
  }
  function fuzzy(key, q) {
    if (q.length < 4) return 0;
    var max = q.length >= 8 ? 2 : 1, best = 99;
    var words = key.split(' ');
    for (var i = 0; i < words.length; i++) {
      var w = words[i]; if (!w) continue;
      var d = lev(w.length > q.length ? w.slice(0, q.length + max) : w, q, max);
      if (d < best) best = d;
    }
    if (best <= max) return 240 - best * 40;
    // subsecuencia (iniciales) para consultas cortas, p. ej. «chrz» -> charizard
    if (q.length >= 4 && key.length >= q.length) {
      var qi = 0; for (var k = 0; k < key.length && qi < q.length; k++) if (key.charAt(k) === q.charAt(qi)) qi++;
      if (qi === q.length && key.length < q.length * 2 + 3) return 120;
    }
    return 0;
  }

  S.query = function (text, o) {
    o = o || {};
    build();
    var q = REM.norm(text);
    if (!q) return [];
    var qTokens = q.split(' ').filter(Boolean), out = [], kinds = o.kinds ? new Set(o.kinds) : null;
    var numeric = /^#?\d{1,3}$/.test(q) ? Number(q.replace('#', '')) : null;
    for (var i = 0; i < entries.length; i++) {
      var e = entries[i];
      if (kinds && !kinds.has(e.kind)) continue;
      var best = 0;
      for (var k = 0; k < e.keys.length; k++) {
        var s = scoreKey(e.keys[k], q, qTokens);
        if (s > best) best = s;
      }
      if (!best) {
        for (var k2 = 0; k2 < e.keys.length && !best; k2++) best = fuzzy(e.keys[k2], q);
      }
      if (numeric != null && e.kind === 'pokemon' && e.extra && e.extra.dex === numeric) best = Math.max(best, 900);
      if (best) out.push({ kind: e.kind, id: e.id, label: e.label, sub: e.sub, score: best + (KIND_BONUS[e.kind] || 0), extra: e.extra });
    }
    out.sort(function (a, b) { return b.score - a.score || REM.collate(a.label, b.label); });
    return out.slice(0, o.limit || 40);
  };

  /* ---------------- UI ---------------- */
  var fold = function (s) {
    var o = ''; for (var i = 0; i < s.length; i++) { var c = s.charAt(i), n = c; try { n = c.normalize('NFD').charAt(0); } catch (e) { /* ok */ } o += n.toLowerCase(); }
    return o;
  };
  function highlight(label, q) {
    var nq = REM.norm(q); if (!nq) return label;
    var f = fold(label), i = f.indexOf(nq);
    if (i < 0 || f.length !== label.length) return label;
    return [label.slice(0, i), h('mark', label.slice(i, i + nq.length)), label.slice(i + nq.length)];
  }
  function leadFor(r) {
    var UI = REM.ui;
    try {
      if (r.kind === 'pokemon') return UI.pokeIcon(r.id, { size: 40, eager: true });
      if (r.kind === 'item') { var it = REM.ent('item', r.id); return UI.itemIcon(it, { size: 32 }); }
      if (r.kind === 'move') { var mv = REM.ent('move', r.id); if (mv) return UI.typeBadge(mv.type, { small: true }); }
    } catch (e) { /* ok */ }
    return h('span.pal__glyph', { 'aria-hidden': 'true' }, KIND_ICON[r.kind] || '•');
  }
  var RECENT_KEY = 'rem-recent-search';
  function getRecent() { try { return JSON.parse(REM.util.store.get(RECENT_KEY, '[]')) || []; } catch (e) { return []; } }
  function pushRecent(r) {
    var l = getRecent().filter(function (x) { return !(x.kind === r.kind && String(x.id) === String(r.id)); });
    l.unshift({ kind: r.kind, id: r.id, label: r.label, sub: r.sub }); REM.util.store.set(RECENT_KEY, JSON.stringify(l.slice(0, 6)));
  }

  var QUICK = [
    { kind: 'link', label: 'Pokédex Maestra', sub: 'Todos los Pokémon', href: '#/pokedex', icon: '📖' },
    { kind: 'link', label: 'Movimientos', sub: 'Tabla de movimientos', href: '#/moves', icon: '⚔️' },
    { kind: 'link', label: 'Habilidades', sub: 'Habilidades reelaboradas', href: '#/abilities', icon: '✨' },
    { kind: 'link', label: 'Objetos', sub: 'Mochila completa', href: '#/items', icon: '🎒' },
    { kind: 'link', label: 'Máquinas Técnicas', sub: 'MT01 – MT100', href: '#/tms', icon: '💿' },
    { kind: 'link', label: 'Tiendas', sub: 'Marts y tiendas especiales', href: '#/shops', icon: '🏪' },
    { kind: 'link', label: 'Mapa', sub: 'Mapa de Oniria', href: '#/map', icon: '🗺️' },
    { kind: 'link', label: 'Avisos de Sintaxis PBS', sub: 'Panel de errores del PBS', href: '#/warnings', icon: '⚠️' }
  ];

  /* Crea el widget: input + lista de resultados con teclado. */
  S.widget = function (o) {
    o = o || {};
    var uid = 'sw' + Math.random().toString(36).slice(2, 7);
    var input = h('input.input.sw__input', { type: 'search', placeholder: o.placeholder || 'Busca Pokémon, movimientos, habilidades, objetos, lugares…', autocomplete: 'off', spellcheck: 'false',
      role: 'combobox', 'aria-expanded': 'true', 'aria-controls': uid + '-list', 'aria-autocomplete': 'list', 'aria-label': 'Buscar en todo el Codex' });
    var list = h('ul.sw__list', { id: uid + '-list', role: 'listbox', 'aria-label': 'Resultados de búsqueda' });
    var status = h('div.sr-only', { role: 'status', 'aria-live': 'polite' });
    var root = h('div.sw' + (o.inline ? '.sw--inline' : '.sw--palette'), input, list, status);
    var items = [], active = -1;

    function setActive(i, scroll) {
      if (!items.length) { active = -1; input.removeAttribute('aria-activedescendant'); return; }
      active = (i + items.length) % items.length;
      items.forEach(function (it, k) { it.el.classList.toggle('is-active', k === active); it.el.setAttribute('aria-selected', k === active ? 'true' : 'false'); });
      input.setAttribute('aria-activedescendant', items[active].el.id);
      if (scroll !== false) items[active].el.scrollIntoView({ block: 'nearest' });
    }
    function pick(r) {
      if (!r) return;
      if (r.kind !== 'link') pushRecent(r);
      var href = r.kind === 'link' ? r.href : REM.router.href(r.kind, r.id);
      if (o.onPick) o.onPick(r, href);
      REM.router.go(href);
    }
    function row(r, i, q) {
      var li = h('li.sw__item', { id: uid + '-o' + i, role: 'option', 'aria-selected': 'false', 'data-kind': r.kind });
      li.appendChild(h('span.sw__lead', r.kind === 'link' ? h('span.pal__glyph', { 'aria-hidden': 'true' }, r.icon) : leadFor(r)));
      li.appendChild(h('span.sw__main', h('span.sw__label', q ? highlight(r.label, q) : r.label), r.sub ? h('span.sw__sub', r.sub) : null));
      li.appendChild(h('span.sw__kind.k-' + r.kind, r.kind === 'link' ? 'Ir a' : (KIND_ES[r.kind] || r.kind)));
      li.addEventListener('mousemove', function () { if (active !== i) setActive(i, false); });
      li.addEventListener('click', function () { pick(r); });
      return li;
    }
    function render() {
      var q = input.value, res;
      REM.clear(list); items = [];
      if (!REM.state.model) { list.appendChild(h('li.sw__empty', 'Cargando datos…')); return; }
      var heading = null;
      if (!REM.norm(q)) {
        var rec = getRecent();
        res = rec.concat(QUICK); heading = rec.length ? 'Recientes y accesos' : 'Accesos rápidos';
        if (heading) list.appendChild(h('li.sw__group', { role: 'presentation' }, heading));
      } else {
        res = S.query(q, { limit: o.limit || 30 });
        if (!res.length) { list.appendChild(h('li.sw__empty', 'Sin resultados para «' + q + '». Prueba con otra ortografía o parte del nombre.')); status.textContent = 'Sin resultados'; setActive(-1); return; }
      }
      var frag = document.createDocumentFragment();
      res.forEach(function (r, i) { var el = row(r, i, REM.norm(q) ? q : ''); items.push({ el: el, r: r }); frag.appendChild(el); });
      list.appendChild(frag);
      status.textContent = REM.norm(q) ? res.length + ' resultados' : '';
      setActive(0, false);
    }
    var rerender = REM.util.debounce(render, 70);
    input.addEventListener('input', rerender);
    input.addEventListener('keydown', function (ev) {
      if (ev.key === 'ArrowDown') { ev.preventDefault(); setActive(active + 1); }
      else if (ev.key === 'ArrowUp') { ev.preventDefault(); setActive(active - 1); }
      else if (ev.key === 'Enter') { ev.preventDefault(); if (items[active]) pick(items[active].r); }
      else if (ev.key === 'Home' && ev.ctrlKey) { setActive(0); }
    });
    if (o.inline) input.addEventListener('focus', render, { once: true });
    root.input = input; root.refresh = render; root.focus = function () { input.focus(); input.select(); };
    root.setValue = function (v) { input.value = v; render(); };
    setTimeout(render, 0);
    return root;
  };

  var overlay = null, lastFocus = null;
  S.isOpen = function () { return !!overlay; };
  S.open = function (initial) {
    if (overlay) { overlay.widget.focus(); return; }
    lastFocus = document.activeElement;
    var widget = S.widget({ placeholder: 'Buscar Pokémon, movimientos, habilidades, objetos, MT, lugares, personajes…' });
    var dialog = h('div.pal__dialog', { role: 'dialog', 'aria-modal': 'true', 'aria-label': 'Búsqueda global' },
      widget,
      h('div.pal__foot', h('span', h('kbd', '↑'), h('kbd', '↓'), ' navegar'), h('span', h('kbd', '⏎'), ' abrir'), h('span', h('kbd', 'Esc'), ' cerrar')));
    var back = h('div.pal', dialog);
    back.addEventListener('mousedown', function (ev) { if (ev.target === back) S.close(); });
    var root = document.getElementById('overlay-root') || document.body;
    root.appendChild(back);
    document.body.classList.add('no-scroll');
    overlay = { el: back, widget: widget };
    if (initial) widget.setValue(initial);
    requestAnimationFrame(function () { back.classList.add('is-in'); widget.focus(); });
    dialog.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape') { ev.preventDefault(); S.close(); }
      else if (ev.key === 'Tab') { ev.preventDefault(); widget.input.focus(); }
    });
  };
  S.close = function () {
    if (!overlay) return;
    var o = overlay; overlay = null;
    o.el.classList.remove('is-in');
    document.body.classList.remove('no-scroll');
    setTimeout(function () { if (o.el.parentNode) o.el.parentNode.removeChild(o.el); }, 120);
    try { if (lastFocus && lastFocus.focus) lastFocus.focus(); } catch (e) { /* ok */ }
  };
  REM.on('route', function () { S.close(); });
  REM.on('model', function () { built = null; });

  document.addEventListener('keydown', function (ev) {
    if ((ev.ctrlKey || ev.metaKey) && !ev.shiftKey && !ev.altKey && (ev.key === 'k' || ev.key === 'K')) {
      ev.preventDefault(); overlay ? S.close() : S.open();
    }
  });
})(window);
