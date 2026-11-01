/* ==========================================================================
 * Vistas Pokédex Maestra  (#/pokedex  y  #/pokemon/<dex>)
 * ========================================================================== */
(function (global) {
  'use strict';
  var REM = global.REM, h = REM.h, ui = REM.ui;

  var GENS = [[1, 151], [152, 251], [252, 386], [387, 493], [494, 649], [650, 721]];
  var GEN_NAME = ['Kanto', 'Johto', 'Hoenn', 'Sinnoh', 'Teselia', 'Kalos'];
  var METHOD_ES = {
    WILD: 'Salvaje', FISHING: 'Pesca', STARTER: 'Inicial', FOSSIL: 'Fósil', EVENT: 'Evento', LEGENDARY: 'Legendario',
    EVOLUTION_LEVEL: 'Evolución por nivel', EVOLUTION_ITEM: 'Evolución con objeto', EVOLUTION_STONE: 'Evolución con piedra', THIRD_STAGE: 'Tercera etapa evolutiva'
  };
  var KIND_ES = { Land: 'Hierba / tierra', Cave: 'Cueva', Surf: 'Surf (agua)', Fish: 'Pesca' };
  var COLOR_ES = { Red: 'Rojo', Blue: 'Azul', Yellow: 'Amarillo', Green: 'Verde', Black: 'Negro', Brown: 'Marrón', Purple: 'Morado', Gray: 'Gris', White: 'Blanco', Pink: 'Rosa' };
  var HABITAT_ES = { Cave: 'Cueva', Forest: 'Bosque', Grassland: 'Pradera', Mountain: 'Montaña', Rare: 'Raro', RoughTerrain: 'Terreno escarpado', Sea: 'Mar', Urban: 'Urbano', WatersEdge: 'Orilla del agua' };
  REM.METHOD_ES = METHOD_ES; REM.KIND_ES = KIND_ES;

  function uniq(a) { return Array.from(new Set(a)); }
  function genOf(dex) { for (var i = 0; i < GENS.length; i++) if (dex >= GENS[i][0] && dex <= GENS[i][1]) return i + 1; return 0; }
  function bstDelta(p) { return p.diff && p.diff.stats && p.diff.stats.bst != null ? p.diff.stats.bst : 0; }

  /* ---------- metadatos precomputados por Pokémon ---------- */
  var META = null, META_FOR = null;
  function meta() {
    var m = REM.state.model;
    if (META && META_FOR === m) return META;
    META_FOR = m; META = {};
    var tmMove = {}; m.tms.forEach(function (t) { tmMove[t.number] = t.move; });
    m.pokemon.forEach(function (p) {
      var moves = new Set(), methods = new Set(), locs = new Set();
      (p.learnset || []).forEach(function (e) { moves.add(e.move); });
      (p.tms || []).forEach(function (n) { if (tmMove[n]) moves.add(tmMove[n]); });
      (p.obtain || []).forEach(function (o) { if (o.method) methods.add(o.method); if (o.loc) locs.add(String(o.loc).split(':')[0]); });
      (p.wild || []).forEach(function (w) { methods.add(w.kind === 'Fish' ? 'FISHING' : 'WILD'); if (w.loc) locs.add(String(w.loc).split(':')[0]); });
      var tn = (p.types || []).map(ui.typeName);
      var an = (p.abilities || []).map(function (a) { var x = REM.idx.abilityBySym[a]; return x ? x.name : a; });
      META[p.dex] = {
        moves: moves, methods: methods, locs: locs, gen: genOf(p.dex),
        blob: REM.norm([p.name, p.sym, REM.pad3(p.dex), '#' + p.dex].concat(tn, an).join(' '))
      };
    });
    return META;
  }

  /* ---------- estado de filtros (persistente entre navegaciones) ---------- */
  function defaults() {
    return { q: '', gen: '', t1: '', t2: '', ability: '', move: '', mod: false, change: '', method: '', loc: '', bmin: '', bmax: '', sort: 'dex', dir: 'asc', view: REM.util.store.get('rem-dex-view', 'grid') };
  }
  var PF = null;

  var SORTS = [['dex', 'Nº de Pokédex'], ['name', 'Nombre'], ['bst', 'Total de base (BST)'], ['dbst', 'Δ BST frente al original'],
    ['hp', 'PS'], ['atk', 'Ataque'], ['def', 'Defensa'], ['spa', 'At. Esp.'], ['spd', 'Def. Esp.'], ['spe', 'Velocidad']];
  function sortVal(p, k) {
    switch (k) {
      case 'dex': return p.dex; case 'name': return p.name; case 'dbst': return bstDelta(p);
      default: return p.stats ? p.stats[k] : null;
    }
  }
  function matchSyms(list, text) {
    var q = REM.norm(text); if (!q) return null;
    var exact = list.filter(function (x) { return REM.norm(x.name) === q || x.sym.toLowerCase() === q.replace(/ /g, '_'); });
    if (exact.length) return new Set(exact.map(function (x) { return x.sym; }));
    return new Set(list.filter(function (x) { return REM.norm(x.name).indexOf(q) >= 0; }).map(function (x) { return x.sym; }));
  }
  function applyFilters() {
    var m = REM.state.model, M = meta(), toks = REM.norm(PF.q).split(' ').filter(Boolean);
    var gen = PF.gen ? GENS[Number(PF.gen) - 1] : null;
    var abil = matchSyms(m.abilities, PF.ability), mvs = matchSyms(m.moves, PF.move);
    var bmin = PF.bmin !== '' ? Number(PF.bmin) : null, bmax = PF.bmax !== '' ? Number(PF.bmax) : null;
    var out = m.pokemon.filter(function (p) {
      var x = M[p.dex];
      if (gen && (p.dex < gen[0] || p.dex > gen[1])) return false;
      if (PF.t1 && (p.types || []).indexOf(PF.t1) < 0) return false;
      if (PF.t2 && (p.types || []).indexOf(PF.t2) < 0) return false;
      if (abil && !(p.abilities || []).some(function (a) { return abil.has(a); })) return false;
      if (mvs) { var ok = false; mvs.forEach(function (s) { if (x.moves.has(s)) ok = true; }); if (!ok) return false; }
      if (PF.mod && !(p.diff && p.diff.changed)) return false;
      if (PF.change && !(p.diff && (p.diff.badges || []).indexOf(PF.change) >= 0)) return false;
      if (PF.method && !x.methods.has(PF.method)) return false;
      if (PF.loc && !x.locs.has(PF.loc)) return false;
      var bst = p.stats ? p.stats.bst : null;
      if (bmin != null && (bst == null || bst < bmin)) return false;
      if (bmax != null && (bst == null || bst > bmax)) return false;
      for (var i = 0; i < toks.length; i++) if (x.blob.indexOf(toks[i]) < 0) return false;
      return true;
    });
    var sgn = PF.dir === 'desc' ? -1 : 1, k = PF.sort;
    out.sort(function (a, b) {
      var av = sortVal(a, k), bv = sortVal(b, k);
      var c = (typeof av === 'number' && typeof bv === 'number') ? av - bv : REM.collate(av, bv);
      return (c * sgn) || (a.dex - b.dex);
    });
    return out;
  }
  function anyFilter() {
    return !!(PF.q || PF.gen || PF.t1 || PF.t2 || PF.ability || PF.move || PF.mod || PF.change || PF.method || PF.loc || PF.bmin !== '' || PF.bmax !== '');
  }

  /* ---------- tarjeta de la rejilla ---------- */
  function pcard(p) {
    var d = p.diff, dl = bstDelta(p);
    return h('a.pcard' + (d && d.changed ? '.is-mod' : ''), { href: REM.router.href('pokemon', p.dex), 'data-kind': 'pokemon', 'data-id': String(p.dex), 'aria-label': p.name + ', número ' + p.dex },
      h('span.pcard__top', h('span.pcard__dex', '#' + REM.pad3(p.dex)), dl ? ui.deltaEl(dl) : null),
      ui.pokeIcon(p.dex, { size: 64 }),
      h('span.pcard__name', p.name),
      ui.typeBadges(p.types, { small: true }),
      h('span.pcard__bst', 'BST ', h('b', String(p.stats ? p.stats.bst : '—'))),
      (d && d.badges && d.badges.length) ? h('span.pcard__badges', d.badges.map(function (b) { return ui.badge(b, { 'Retipado': 'type', 'Stats': 'stats', 'Habilidades': 'ability', 'Evolución': 'evo', 'Learnset': 'moves' }[b] || 'mod'); })) : null);
  }

  /* ---------- lista ---------- */
  function renderList(el, query) {
    var m = REM.state.model;
    var presets = ['q', 'gen', 'type', 't2', 'change', 'mod', 'method', 'loc', 'move', 'ability', 'bmin', 'bmax'];
    var hasPreset = presets.some(function (k) { return query && query[k] != null; });
    if (!PF || hasPreset) {
      PF = defaults();
      if (hasPreset) {
        if (query.q) PF.q = query.q; if (query.gen) PF.gen = query.gen; if (query.type) PF.t1 = query.type; if (query.t2) PF.t2 = query.t2;
        if (query.change) { PF.change = query.change; PF.mod = false; } if (query.mod) PF.mod = query.mod === '1' || query.mod === 'true';
        if (query.method) PF.method = query.method; if (query.loc) PF.loc = query.loc; if (query.move) PF.move = query.move; if (query.ability) PF.ability = query.ability;
        if (query.bmin) PF.bmin = query.bmin; if (query.bmax) PF.bmax = query.bmax;
      }
    }
    meta();
    el.appendChild(ui.pageHeader({ title: 'Pokédex Maestra', sub: 'Los ' + REM.num(m.pokemon.length) + ' Pokémon de Oniria con su estado frente al juego original. Filtra por cualquier combinación y abre una ficha para ver evoluciones, ubicaciones y learnset.' }));

    var results = h('div.dex-results');
    var countEl = h('div.dex-count', { 'aria-live': 'polite' });
    var gridHost = h('div.dex-host');
    var current = [], tbl = null, shown = 0, io = null;

    function typeOptions(first) { return [['', first]].concat((m.types || []).filter(function (t) { return t.sym !== 'QMARKS'; }).map(function (t) { return [t.sym, t.name]; })); }
    var locOptions = [['', 'Cualquier ubicación']].concat((m.locations || []).map(function (l) { return [l.key, l.name]; }));
    var methodOptions = [['', 'Cualquier método']].concat(Object.keys(METHOD_ES).map(function (k) { return [k, METHOD_ES[k]]; }));
    var changeOptions = [['', 'Cualquier cambio'], ['Retipado', 'Retipado'], ['Stats', 'Estadísticas'], ['Habilidades', 'Habilidades'], ['Evolución', 'Evolución'], ['Learnset', 'Learnset']];
    var genOptions = [['', 'Todas las generaciones']].concat(GENS.map(function (g, i) { return [String(i + 1), 'Gen ' + (i + 1) + ' · ' + GEN_NAME[i] + ' (' + g[0] + '–' + g[1] + ')']; }));

    function refresh() {
      current = applyFilters();
      countEl.textContent = '';
      countEl.appendChild(h('b', REM.num(current.length)));
      countEl.appendChild(document.createTextNode(' de ' + REM.num(m.pokemon.length) + ' Pokémon' + (anyFilter() ? ' con los filtros actuales' : '')));
      buildResults();
    }
    function buildResults() {
      if (io) { io.disconnect(); io = null; }
      REM.clear(gridHost); tbl = null; shown = 0;
      if (!current.length) { gridHost.appendChild(ui.empty('Ningún Pokémon coincide con estos filtros')); return; }
      if (PF.view === 'table') { gridHost.appendChild(buildTable()); return; }
      var grid = h('div.pgrid'), more = h('div.pgrid__more'), sentinel = h('div.tblx__sentinel', { 'aria-hidden': 'true' });
      gridHost.appendChild(grid); gridHost.appendChild(sentinel); gridHost.appendChild(more);
      var chunk = REM.state.selftest ? 800 : 72;
      function next() {
        var end = Math.min(current.length, shown + chunk), f = document.createDocumentFragment();
        for (var i = shown; i < end; i++) f.appendChild(pcard(current[i]));
        grid.appendChild(f); shown = end; REM.clear(more);
        if (shown < current.length) {
          more.appendChild(h('button.btn', { type: 'button', onclick: next }, 'Mostrar más (' + REM.num(current.length - shown) + ' restantes)'));
        }
      }
      next();
      if ('IntersectionObserver' in global && !REM.state.selftest) {
        io = new IntersectionObserver(function (es) { if (es.some(function (e) { return e.isIntersecting; }) && shown < current.length) next(); }, { rootMargin: '700px 0px' });
        io.observe(sentinel);
      }
    }
    function buildTable() {
      var cols = [
        { key: 'name', label: 'Pokémon', sort: function (p) { return p.name; }, render: function (p) { return h('span.cellpoke', ui.pokeIcon(p.dex, { size: 40 }), ui.link('pokemon', p.dex)); } },
        { key: 'dex', label: 'Nº', align: 'right', sort: function (p) { return p.dex; }, render: function (p) { return '#' + REM.pad3(p.dex); } },
        { key: 'types', label: 'Tipos', sort: function (p) { return (p.types || []).join(); }, render: function (p) { return ui.typeBadges(p.types, { small: true }); } },
        { key: 'abilities', label: 'Habilidades', sort: false, render: function (p) { var f = document.createDocumentFragment(); (p.abilities || []).forEach(function (a, i) { if (i) f.appendChild(document.createTextNode(' · ')); f.appendChild(ui.link('ability', a)); }); return f; } }
      ];
      ui.STAT_ROWS.forEach(function (r) { cols.push({ key: r[0], label: { hp: 'PS', atk: 'Atq', def: 'Def', spa: 'AEsp', spd: 'DEsp', spe: 'Vel' }[r[0]], title: r[1], align: 'right', defaultDir: 'desc', sort: function (p) { return p.stats && p.stats[r[0]]; }, render: function (p) { return p.stats ? h('span.sv.s' + ui.statTier(p.stats[r[0]]), String(p.stats[r[0]])) : '—'; } }); });
      cols.push({ key: 'bst', label: 'BST', align: 'right', defaultDir: 'desc', sort: function (p) { return p.stats && p.stats.bst; }, render: function (p) { return h('b', String(p.stats ? p.stats.bst : '—')); } });
      cols.push({ key: 'dbst', label: 'Δ BST', align: 'right', defaultDir: 'desc', sort: function (p) { return bstDelta(p); }, render: function (p) { var d = bstDelta(p); return d ? ui.deltaEl(d) : null; } });
      cols.push({ key: 'badges', label: 'Cambios REM', sort: false, render: function (p) { return ui.diffBadges(p); } });
      tbl = ui.table(cols, current, { filter: false, pageSize: REM.state.selftest ? 800 : 80, sort: PF.sort === 'name' ? 'name' : PF.sort, dir: PF.dir, dense: true, countLabel: ['Pokémon', 'Pokémon'], hasFilters: anyFilter(), cls: 'tbl--dex' });
      return tbl;
    }

    /* ---- controles ---- */
    function bind(key, v) { PF[key] = v; refresh(); }
    var abilityList = h('datalist', { id: 'dl-abilities' }, m.abilities.map(function (a) { return h('option', { value: a.name }); }));
    var moveList = h('datalist', { id: 'dl-moves' }, m.moves.map(function (a) { return h('option', { value: a.name }); }));
    var qInput = ui.input('Buscar por nombre, nº, tipo o habilidad', PF.q, function (v) { bind('q', v); }, { placeholder: 'p. ej. char, 025, fuego…', cls: 'f-q' });
    var abInput = ui.input('Habilidad', PF.ability, function (v) { bind('ability', v); }, { type: 'text', placeholder: 'Cualquier habilidad', cls: 'f-ab' }); abInput.querySelector('input').setAttribute('list', 'dl-abilities');
    var mvInput = ui.input('Movimiento que aprende', PF.move, function (v) { bind('move', v); }, { type: 'text', placeholder: 'Cualquier movimiento', cls: 'f-mv' }); mvInput.querySelector('input').setAttribute('list', 'dl-moves');
    var modCheck = ui.check('Solo modificados por REM', PF.mod, function (v) { bind('mod', v); });
    var dirBtn = h('button.btn.btn--icon', { type: 'button', title: 'Invertir orden', 'aria-label': 'Invertir orden' }, PF.dir === 'asc' ? '↑' : '↓');
    dirBtn.addEventListener('click', function () { PF.dir = PF.dir === 'asc' ? 'desc' : 'asc'; dirBtn.textContent = PF.dir === 'asc' ? '↑' : '↓'; refresh(); });
    var viewTabs = ui.tabs([{ id: 'grid', label: '▦ Rejilla' }, { id: 'table', label: '☰ Tabla' }], PF.view, function (id) { PF.view = id; REM.util.store.set('rem-dex-view', id); buildResults(); });
    var reset = h('button.btn', { type: 'button' }, 'Limpiar filtros');
    reset.addEventListener('click', function () { var v = PF.view; PF = defaults(); PF.view = v; REM.router.go('#/pokedex'); });
    var filters = h('details.filters.card', { open: true },
      h('summary', h('b', 'Filtros y orden'), h('span.muted.small', ' · pulsa para plegar')),
      h('div.filters__grid',
        qInput,
        ui.select('Generación', genOptions, PF.gen, function (v) { bind('gen', v); }),
        ui.select('Tipo', typeOptions('Cualquier tipo'), PF.t1, function (v) { bind('t1', v); }),
        ui.select('Y también tipo', typeOptions('Cualquier tipo'), PF.t2, function (v) { bind('t2', v); }),
        abInput, mvInput,
        ui.select('Cómo se obtiene', methodOptions, PF.method, function (v) { bind('method', v); }),
        ui.select('Dónde aparece', locOptions, PF.loc, function (v) { bind('loc', v); }),
        ui.select('Cambio REM', changeOptions, PF.change, function (v) { bind('change', v); }),
        ui.input('BST mínimo', PF.bmin, function (v) { bind('bmin', v); }, { type: 'number', min: 0, max: 800, step: 10, placeholder: '0' }),
        ui.input('BST máximo', PF.bmax, function (v) { bind('bmax', v); }, { type: 'number', min: 0, max: 800, step: 10, placeholder: '800' }),
        h('div.field', h('span.field__label', 'Solo cambios'), modCheck)),
      h('div.filters__row',
        ui.select('Ordenar por', SORTS, PF.sort, function (v) { PF.sort = v; refresh(); }, { cls: 'f-sort' }), dirBtn, viewTabs, reset, abilityList, moveList));
    el.appendChild(filters);
    el.appendChild(h('div.dex-bar', countEl));
    el.appendChild(gridHost);
    refresh();
  }

  /* ---------- ficha ---------- */
  function methodText(m) { return METHOD_ES[m] || m || '—'; }

  function evoLabel(e) {
    var parts = [];
    var text = e.text || [e.method, e.param].filter(Boolean).join(' ');
    parts.push(h('span', text || '—'));
    if (e.item && REM.ent('item', e.item)) { parts.push(' '); parts.push(ui.link('item', e.item)); }
    return parts;
  }
  function evoTree(p) {
    var ix = REM.idx;
    var fam = (p.family && p.family.length ? p.family : [p.dex]).map(function (d) { return ix.pokemonByDex[d]; }).filter(Boolean);
    if (!fam.some(function (x) { return x.dex === p.dex; })) fam.push(p);
    var famSet = new Set(fam.map(function (x) { return x.dex; })), seen = new Set();
    var roots = fam.filter(function (x) { return !x.evolvesFrom || !famSet.has(x.evolvesFrom.from); });
    if (!roots.length) roots = [fam[0]];
    function nodeCard(x) {
      return h('a.evo-card' + (x.dex === p.dex ? '.is-current' : ''), { href: REM.router.href('pokemon', x.dex), 'data-kind': 'pokemon', 'data-id': String(x.dex), 'aria-current': x.dex === p.dex ? 'true' : null },
        ui.pokeIcon(x.dex, { size: 64 }), h('span.evo-card__dex', '#' + REM.pad3(x.dex)), h('span.evo-card__name', x.name), ui.typeBadges(x.types, { small: true }));
    }
    function branch(x, edge) {
      seen.add(x.dex);
      var kids = (x.evolutions || []).filter(function (e) { return famSet.has(e.to) && !seen.has(e.to) && ix.pokemonByDex[e.to]; });
      var b = h('div.evo-branch');
      if (edge) b.appendChild(h('div.evo-edge', h('span.evo-edge__label', evoLabel(edge)), h('i.evo-edge__arrow', { 'aria-hidden': 'true' }, '→')));
      b.appendChild(nodeCard(x));
      if (kids.length) {
        var col = h('div.evo-children');
        kids.forEach(function (e) { col.appendChild(branch(ix.pokemonByDex[e.to], e)); });
        b.appendChild(col);
      }
      return b;
    }
    var tree = h('div.evo-tree');
    roots.forEach(function (r) { if (!seen.has(r.dex)) tree.appendChild(branch(r, null)); });
    return tree;
  }

  function obtainSection(p) {
    var ob = p.obtain || [], wi = p.wild || [];
    var card = ui.card('Dónde obtenerlo');
    if (!ob.length && !wi.length) { card.appendChild(ui.empty('Sin datos de obtención')); return card; }
    if (ob.length) {
      var list = h('ul.obtain');
      ob.forEach(function (o) {
        list.appendChild(h('li',
          h('span.chip.chip--info', methodText(o.method)),
          o.loc ? ui.link('location', String(o.loc).split(':')[0]) : null,
          o.level ? h('span.muted', 'Nv ' + REM.fmtRange(o.level)) : null,
          o.detail ? h('span.obtain__detail', o.detail) : null));
      });
      card.appendChild(list);
    }
    if (wi.length) {
      var cols = [
        { key: 'loc', label: 'Ubicación', sort: function (w) { return w.loc; }, render: function (w) { var k = String(w.loc).split(':')[0], z = w.zone || (String(w.loc).split(':')[1]); return h('span', ui.link('location', k), z ? h('span.muted', ' · zona ' + z) : null); } },
        { key: 'kind', label: 'Tipo', render: function (w) { return KIND_ES[w.kind] || w.kind; } },
        { key: 'rarity', label: 'Rareza', sort: function (w) { return { COMMON: 0, UNCOMMON: 1, RARE: 2 }[w.rarity]; }, render: function (w) { return ui.rarityBadge(w.rarity); } },
        { key: 'pct', label: '%', align: 'right', defaultDir: 'desc', render: function (w) { return REM.pct(w.pct); } },
        { key: 'day', label: 'Nv día', align: 'right', sort: function (w) { return w.day && w.day[0]; }, render: function (w) { return REM.fmtRange(w.day); } },
        { key: 'night', label: 'Nv noche', align: 'right', sort: function (w) { return w.night && w.night[0]; }, render: function (w) { return REM.fmtRange(w.night); } },
        { key: 'note', label: 'Nota táctica', sort: false, render: function (w) { return w.note ? h('span.small', w.note) : null; } }
      ];
      card.appendChild(h('h3.subhead', 'Encuentros salvajes'));
      card.appendChild(ui.table(cols, wi, { filter: false, dense: true, pageSize: 60, countLabel: ['encuentro', 'encuentros'] }));
    }
    return card;
  }

  function abilitiesCard(p) {
    var card = ui.card('Habilidades'), list = h('ul.abil');
    var ad = p.diff && p.diff.abilities || {}, added = new Set(ad.added || []), removed = new Set(ad.removed || []);
    (p.abilities || []).forEach(function (a) {
      var ab = REM.idx.abilityBySym[a];
      list.appendChild(h('li', h('div.abil__head', ui.link('ability', a), added.has(a) ? ui.badge('Nueva en REM', 'new') : null, ab && ab.status && ab.status !== 'Untouched' && ab.status !== 'Kept' ? ui.diffBadges(ab) : null),
        ab && ab.description ? h('p.abil__desc', ab.description) : null));
    });
    if (!(p.abilities || []).length) card.appendChild(ui.empty('Sin habilidades registradas'));
    card.appendChild(list);
    var b = p.baseline;
    if (b && (b.abilities || b.hiddenAbility) && (removed.size || added.size)) {
      var orig = (b.abilities || []).concat(b.hiddenAbility ? [b.hiddenAbility] : []);
      var row = h('p.small.muted', 'Original: ');
      uniq(orig).forEach(function (a, i) {
        if (i) row.appendChild(document.createTextNode(' · '));
        var nm = (REM.idx.abilityBySym[a] || {}).name || a;
        var oh = b.hiddenAbility === a && (b.abilities || []).indexOf(a) < 0;
        var node = removed.has(a) ? h('s', { title: 'Ya no la tiene' }, nm) : h('span', nm);
        row.appendChild(node); if (oh) row.appendChild(h('span.faint', ' (oculta)'));
      });
      card.appendChild(row);
    }
    return card;
  }

  function learnsetCard(p) {
    var card = ui.card('Movimientos por nivel');
    var ls = p.learnset || [], added = new Set((p.diff && p.diff.movesAdded) || []);
    if (!ls.length) { card.appendChild(ui.empty('Sin learnset registrado')); return card; }
    var rows = ls.map(function (e, i) { return { lv: e.lv, sym: e.move, mv: REM.idx.moveBySym[e.move], isNew: added.has(e.move), i: i }; });
    var cols = [
      { key: 'lv', label: 'Nv', align: 'right', sort: function (r) { return r.lv; }, render: function (r) { return h('b', String(r.lv)); } },
      { key: 'move', label: 'Movimiento', sort: function (r) { return r.mv ? r.mv.name : r.sym; }, render: function (r) { return h('span', ui.link('move', r.sym), r.isNew ? h('span.newtag', ui.badge('Nuevo en REM', 'new')) : null); } },
      { key: 'type', label: 'Tipo', sort: function (r) { return r.mv && r.mv.type; }, render: function (r) { return r.mv ? ui.typeBadge(r.mv.type, { small: true }) : null; } },
      { key: 'cat', label: 'Cat.', sort: function (r) { return r.mv && r.mv.category; }, render: function (r) { return r.mv ? ui.categoryBadge(r.mv.category) : null; } },
      { key: 'pow', label: 'Pot.', align: 'right', defaultDir: 'desc', sort: function (r) { return r.mv && r.mv.power; }, render: function (r) { return r.mv && r.mv.power ? String(r.mv.power) : '—'; } },
      { key: 'acc', label: 'Prec.', align: 'right', defaultDir: 'desc', sort: function (r) { return r.mv && r.mv.accuracy; }, render: function (r) { return r.mv && r.mv.accuracy ? r.mv.accuracy + '%' : '—'; } },
      { key: 'pp', label: 'PP', align: 'right', sort: function (r) { return r.mv && r.mv.pp; }, render: function (r) { return r.mv ? String(r.mv.pp) : '—'; } }
    ];
    card.appendChild(ui.table(cols, rows, { filter: false, dense: true, pageSize: 200, sort: 'lv', countLabel: ['movimiento', 'movimientos'] }));
    var rem = (p.diff && p.diff.movesRemoved) || [];
    if (rem.length) {
      var l = h('p.small.muted', 'Movimientos que ya no aprende frente al original: ');
      rem.forEach(function (s, i) { if (i) l.appendChild(document.createTextNode(', ')); l.appendChild(REM.idx.moveBySym[s] ? ui.link('move', s) : document.createTextNode(s)); });
      card.appendChild(l);
    }
    return card;
  }

  function tmCard(p) {
    var card = ui.card('MT compatibles (' + (p.tms || []).length + ')');
    var list = (p.tms || []).slice().sort(function (a, b) { return a - b; });
    if (!list.length) { card.appendChild(ui.empty('No aprende ninguna MT')); return card; }
    var grid = h('div.tmgrid');
    list.forEach(function (n) {
      var t = REM.idx.tmByNum[n]; if (!t) return;
      var mv = REM.idx.moveBySym[t.move], w = (t.where || [])[0], loc = w && REM.idx.locByKey[w.loc];
      grid.appendChild(h('a.tmtile.t-' + (mv ? mv.type : 'NORMAL'), { href: REM.router.href('tm', n), 'data-kind': 'tm', 'data-id': String(n) },
        h('span.tmtile__n', 'MT' + REM.pad2(n)), h('span.tmtile__move', mv ? mv.name : t.move),
        h('span.tmtile__where', loc ? loc.name + ((t.where.length > 1) ? ' +' + (t.where.length - 1) : '') : 'Sin ubicación')));
    });
    card.appendChild(grid);
    return card;
  }

  function renderDetail(el, parts) {
    var p = REM.ent('pokemon', parts[0]), m = REM.state.model;
    if (!p) { el.appendChild(REM.router.notFound({ hash: '#/pokemon/' + (parts[0] || '') })); return; }
    var prev = REM.idx.pokemonByDex[p.dex - 1], next = REM.idx.pokemonByDex[p.dex + 1];
    var d = p.diff || {};
    var hasKind = p.kind || p.height || p.weight || p.color || p.habitat;

    /* cabecera */
    var spriteHost = h('div.sprite-host');
    var variant = 'front';
    function drawSprite() {
      REM.clear(spriteHost).appendChild(ui.pokeSprite(p.dex, { size: 200, back: variant === 'back', shiny: variant === 'shiny' }));
    }
    drawSprite();
    var vtabs = ui.tabs([{ id: 'front', label: 'Frontal' }, { id: 'back', label: 'Espalda' }, { id: 'shiny', label: 'Variocolor' }], 'front', function (id) { variant = id; drawSprite(); });

    var typesRow = h('div.dex-types', ui.typeBadges(p.types));
    if (d.types && d.types.before) typesRow.appendChild(h('span.chip.chip--warn', { title: 'Tipos del juego original' }, 'Antes: ', ui.typeBadges(d.types.before, { small: true })));
    var hero = h('section.card.dex-hero',
      h('div.dex-hero__sprite', spriteHost, vtabs),
      h('div.dex-hero__info',
        h('div.dex-hero__no', '#' + REM.pad3(p.dex), p.kind ? h('span.muted', ' · Pokémon ' + p.kind) : null),
        h('h1', p.name),
        typesRow,
        h('div.dex-hero__badges', ui.diffBadges(p), d.changed ? null : h('span.chip', 'Sin cambios frente al original')),
        p.role ? h('blockquote.role', h('b', 'Rol en REM · '), p.role) : null,
        p.pokedex ? h('p.dex-text', p.pokedex) : null,
        hasKind ? ui.kv([['Categoría', p.kind || null], ['Altura', p.height != null ? REM.num(p.height) + ' m' : null], ['Peso', p.weight != null ? REM.num(p.weight) + ' kg' : null],
          ['Color', p.color ? (COLOR_ES[p.color] || p.color) : null], ['Hábitat', p.habitat ? (HABITAT_ES[p.habitat] || p.habitat) : null]]) : null));

    el.appendChild(ui.pageHeader({
      crumbs: [{ label: 'Pokédex Maestra', href: '#/pokedex' }, { label: '#' + REM.pad3(p.dex) + ' ' + p.name }],
      title: null,
      actions: [prev ? h('a.btn', { href: REM.router.href('pokemon', prev.dex), title: prev.name }, '← #' + REM.pad3(prev.dex) + ' ' + prev.name) : null,
        next ? h('a.btn', { href: REM.router.href('pokemon', next.dex), title: next.name }, '#' + REM.pad3(next.dex) + ' ' + next.name + ' →') : null]
    }));
    el.appendChild(hero);

    /* estadísticas + habilidades */
    var statsCard = ui.card('Estadísticas base', ui.statBars(p));
    if (p.baseline && p.baseline.stats) statsCard.appendChild(h('p.small.muted', { style: { marginTop: '10px' } }, 'Las diferencias (+/−) comparan con el juego original. Original: BST ' + p.baseline.stats.bst + '.'));
    else statsCard.appendChild(h('p.small.muted', { style: { marginTop: '10px' } }, 'Sin datos del juego original para comparar.'));
    el.appendChild(h('div.grid.grid--2.dex-pair', statsCard, abilitiesCard(p)));

    /* evoluciones */
    var evo = ui.card('Línea evolutiva');
    if ((p.family || []).length > 1 || (p.evolutions || []).length || p.evolvesFrom) evo.appendChild(evoTree(p));
    else evo.appendChild(h('p.muted', 'Este Pokémon no evoluciona ni procede de otro.'));
    if (d.evolutions && p.baseline && (p.baseline.evolutions || []).length) {
      var bl = h('p.small.muted', { style: { marginTop: '10px' } }, ui.badge('Evolución', 'evo'), ' Original: ');
      p.baseline.evolutions.forEach(function (e, i) {
        if (i) bl.appendChild(document.createTextNode(' · '));
        var to = REM.idx.pokemonByDex[e.to]; bl.appendChild(document.createTextNode((to ? to.name : (e.to || '?')) + ' (' + (e.text || [e.method, e.param].filter(Boolean).join(' ')) + ')'));
      });
      evo.appendChild(bl);
    }
    el.appendChild(evo);

    el.appendChild(obtainSection(p));
    el.appendChild(learnsetCard(p));
    el.appendChild(tmCard(p));
  }

  /* ---------- registro ---------- */
  REM.router.register('pokedex', { title: 'Pokédex Maestra', render: function (el, parts, query) { renderList(el, query); } });
  REM.router.register('pokemon', {
    title: function (parts) { var p = REM.ent('pokemon', parts[0]); return p ? '#' + REM.pad3(p.dex) + ' ' + p.name : 'Pokémon'; },
    render: function (el, parts) { if (!parts.length) { REM.router.go('#/pokedex', { replace: true }); return; } renderDetail(el, parts); }
  });

  REM.selftest.add('pokedex', function () {
    var m = REM.state.model, out = ['#/pokedex'], seen = {};
    function add(d) { if (REM.idx.pokemonByDex[d] && !seen[d]) { seen[d] = 1; out.push('#/pokemon/' + d); } }
    m.pokemon.forEach(function (p, i) { if (i % 5 === 0) add(p.dex); });
    [133, 1, 25, 151, 493, 494, 292, 132, 6, 150, 143, 479, 721, 649, 386, 491, 492, 235, 412, 413, 351, 414, 266, 268, 265, 267, 269, 201, 489, 490].forEach(add);
    out.push('#/pokedex?mod=1', '#/pokedex?change=Retipado');
    return out;
  });
})(window);
