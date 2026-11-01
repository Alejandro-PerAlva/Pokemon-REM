/* ==========================================================================
 * Vistas Movimientos y Habilidades
 *   #/moves  #/move/<SYM>  #/abilities  #/ability/<SYM>
 * ========================================================================== */
(function (global) {
  'use strict';
  var REM = global.REM, h = REM.h, ui = REM.ui;

  var FIELD_ES = { name: 'Nombre', type: 'Tipo', category: 'Categoría', power: 'Potencia', accuracy: 'Precisión', pp: 'PP', priority: 'Prioridad',
    fcode: 'Código de efecto', effectChance: 'Prob. de efecto', target: 'Objetivo', flags: 'Indicadores', description: 'Descripción' };
  var TARGET_ES = { '00': 'Un objetivo', '01': 'Sin objetivo concreto', '02': 'Oponente aleatorio', '04': 'Todos los oponentes', '08': 'Todos los demás', '10': 'El usuario',
    '20': 'Lado del usuario', '40': 'Lado rival', '80': 'Ambos lados', '100': 'Un aliado', '200': 'Usuario o aliado', '400': 'Oponente cercano' };

  function fmtField(f, v) {
    if (v == null || v === '') return h('span.muted', '—');
    if (f === 'type') return ui.typeBadge(v, { small: true });
    if (f === 'category') return ui.categoryBadge(v);
    if (f === 'accuracy') return v === 0 ? h('span.muted', 'Siempre acierta') : v + '%';
    if (f === 'effectChance') return v ? v + '%' : '—';
    if (f === 'target') return (TARGET_ES[v] || 'Código ' + v);
    if (f === 'power') return v === 0 ? h('span.muted', '—') : String(v);
    return String(v);
  }
  function diffRows(mv) {
    var fields = (mv.diff && mv.diff.fields) || [], b = mv.baseline || {}, rows = [];
    fields.forEach(function (f) {
      if (f === 'description') return;
      rows.push([FIELD_ES[f] || f, fmtField(f, b[f]), h('span.arrow', { 'aria-hidden': 'true' }, '→'), fmtField(f, mv[f])]);
    });
    return rows;
  }

  /* ---------------- lista de movimientos ---------------- */
  var MF = null;
  function renderMoves(el, query) {
    var m = REM.state.model;
    var presets = query && (query.type != null || query.cat != null || query.changed != null || query.tm != null);
    if (!MF || presets) MF = { type: (query && query.type) || '', cat: (query && query.cat) || '', changed: !!(query && query.changed), tm: !!(query && query.tm) };
    el.appendChild(ui.pageHeader({ title: 'Movimientos', sub: REM.num(m.moves.length) + ' movimientos con su valor actual y el cambio frente al juego original. Haz clic en una cabecera para ordenar.' }));
    var cols = [
      { key: 'name', label: 'Movimiento', render: function (x) { return ui.link('move', x.sym); } },
      { key: 'type', label: 'Tipo', sort: function (x) { return x.type; }, render: function (x) { return ui.typeBadge(x.type, { small: true }); } },
      { key: 'category', label: 'Cat.', render: function (x) { return ui.categoryBadge(x.category); } },
      { key: 'power', label: 'Pot.', align: 'right', defaultDir: 'desc', render: function (x) { return x.power ? String(x.power) : '—'; } },
      { key: 'accuracy', label: 'Prec.', align: 'right', defaultDir: 'desc', render: function (x) { return x.accuracy ? x.accuracy + '%' : '—'; } },
      { key: 'pp', label: 'PP', align: 'right', render: function (x) { return String(x.pp); } },
      { key: 'priority', label: 'Prio.', align: 'right', render: function (x) { return x.priority ? (x.priority > 0 ? '+' : '') + x.priority : '0'; } },
      { key: 'tm', label: 'MT', sort: function (x) { return x.tm; }, render: function (x) { return x.tm != null ? ui.link('tm', x.tm, 'MT' + REM.pad2(x.tm)) : null; } },
      { key: 'learners', label: 'Aprendices', align: 'right', defaultDir: 'desc', sort: function (x) { return countLearners(x); }, render: function (x) { return REM.num(countLearners(x)); } },
      { key: 'chg', label: 'Cambios', sort: function (x) { return x.diff && x.diff.changed ? 1 : 0; }, defaultDir: 'desc', render: function (x) { return ui.diffBadges(x); } }
    ];
    var tbl;
    function rows() {
      return m.moves.filter(function (x) {
        if (MF.type && x.type !== MF.type) return false;
        if (MF.cat && x.category !== MF.cat) return false;
        if (MF.changed && !(x.diff && x.diff.changed)) return false;
        if (MF.tm && x.tm == null) return false;
        return true;
      });
    }
    function upd() { tbl.setRows(rows()); }
    var toolbar = [
      ui.select('Tipo', [['', 'Todos']].concat(m.types.filter(function (t) { return t.sym !== 'QMARKS'; }).map(function (t) { return [t.sym, t.name]; })), MF.type, function (v) { MF.type = v; upd(); }),
      ui.select('Categoría', [['', 'Todas'], ['Physical', 'Físico'], ['Special', 'Especial'], ['Status', 'Estado']], MF.cat, function (v) { MF.cat = v; upd(); }),
      ui.check('Cambiados en REM', MF.changed, function (v) { MF.changed = v; upd(); }),
      ui.check('Con MT', MF.tm, function (v) { MF.tm = v; upd(); })
    ];
    tbl = ui.table(cols, rows(), { placeholder: 'Filtrar movimientos…', toolbar: toolbar, pageSize: 120, sort: 'name', countLabel: ['movimiento', 'movimientos'], filterText: function (x) { return x.name + ' ' + x.sym + ' ' + ui.typeName(x.type) + ' ' + (x.description || ''); } });
    el.appendChild(tbl);
  }
  function countLearners(x) {
    var s = new Set(); (x.learnedBy || []).forEach(function (e) { s.add(e.dex); }); (x.tmLearners || []).forEach(function (d) { s.add(d); }); return s.size;
  }

  /* ---------------- ficha de movimiento ---------------- */
  function renderMove(el, parts) {
    var mv = REM.ent('move', parts[0]);
    if (!mv) { el.appendChild(REM.router.notFound({ hash: '#/move/' + (parts[0] || '') })); return; }
    var b = mv.baseline, d = mv.diff || {};
    el.appendChild(ui.pageHeader({
      crumbs: [{ label: 'Movimientos', href: '#/moves' }, { label: mv.name }],
      title: mv.name, lead: ui.typeBadge(mv.type),
      meta: [ui.categoryBadge(mv.category), ui.diffBadges(mv), mv.tm != null ? ui.link('tm', mv.tm, 'MT' + REM.pad2(mv.tm)) : null]
    }));
    var desc = ui.card('Descripción', h('p.lead', mv.description || 'Sin descripción.'));
    if (d.fields && d.fields.indexOf('description') >= 0 && b && b.description) {
      desc.appendChild(h('div.beforeafter', h('div', h('span.ba__tag', 'Antes'), h('p', b.description)), h('div', h('span.ba__tag.ba__tag--new', 'Ahora'), h('p', mv.description))));
    }
    var stats = h('div.statgrid',
      ui.stat('Potencia', mv.power ? mv.power : '—'), ui.stat('Precisión', mv.accuracy ? mv.accuracy + '%' : 'Siempre'),
      ui.stat('PP', mv.pp), ui.stat('Prioridad', (mv.priority > 0 ? '+' : '') + (mv.priority || 0)),
      ui.stat('Prob. de efecto', mv.effectChance ? mv.effectChance + '%' : '—'), ui.stat('Objetivo', TARGET_ES[mv.target] || ('Código ' + mv.target)));
    el.appendChild(h('div.grid.grid--2', desc, ui.card('Datos', stats, ui.kv([['Código de efecto', mv.fcode ? h('code', mv.fcode) : null], ['Indicadores', mv.flags ? h('code', mv.flags) : null], ['Símbolo PBS', h('code', mv.sym)]]))));

    var rows = diffRows(mv);
    if (rows.length) {
      var t = h('table.tbl.tbl--dense.diff-table', h('thead', h('tr', h('th', 'Campo'), h('th', 'Antes'), h('th', ''), h('th', 'Ahora'))),
        h('tbody', rows.map(function (r) { return h('tr', r.map(function (c) { return h('td', c); })); })));
      el.appendChild(ui.section('Cambios frente al juego original', 'Valores del PBS original comparados con los actuales.', h('div.tblx', h('div.tblx__scroll', t))));
    } else if (!b) {
      el.appendChild(h('p.muted.small', 'Sin datos del juego original para comparar este movimiento.'));
    }

    /* aprendices */
    var lv = (mv.learnedBy || []).filter(function (e) { return REM.idx.pokemonByDex[e.dex]; }).map(function (e) { return { dex: e.dex, lv: e.lv, p: REM.idx.pokemonByDex[e.dex] }; });
    var pcols = function (withLv) {
      var c = [
        { key: 'name', label: 'Pokémon', sort: function (r) { return r.p.name; }, render: function (r) { return h('span.cellpoke', ui.pokeIcon(r.dex, { size: 36 }), ui.link('pokemon', r.dex)); } },
        { key: 'dex', label: 'Nº', align: 'right', sort: function (r) { return r.dex; }, render: function (r) { return '#' + REM.pad3(r.dex); } },
        { key: 'types', label: 'Tipos', sort: false, render: function (r) { return ui.typeBadges(r.p.types, { small: true }); } }
      ];
      if (withLv) c.splice(2, 0, { key: 'lv', label: 'Nivel', align: 'right', render: function (r) { return h('b', String(r.lv)); } });
      return c;
    };
    el.appendChild(ui.section('Lo aprenden por nivel', lv.length ? REM.num(lv.length) + ' Pokémon' : null,
      lv.length ? ui.table(pcols(true), lv, { dense: true, pageSize: 50, sort: 'lv', placeholder: 'Filtrar Pokémon…', countLabel: ['Pokémon', 'Pokémon'], filterText: function (r) { return r.p.name + ' ' + r.dex; } }) : ui.empty('Ningún Pokémon lo aprende por nivel')));
    var tmRows = (mv.tmLearners || []).filter(function (dx) { return REM.idx.pokemonByDex[dx]; }).map(function (dx) { return { dex: dx, p: REM.idx.pokemonByDex[dx] }; });
    if (mv.tm != null || tmRows.length) {
      el.appendChild(ui.section('Lo aprenden por MT', mv.tm != null ? h('span', 'MT' + REM.pad2(mv.tm) + ' · ', ui.link('tm', mv.tm, 'ver ficha de la MT')) : 'Este movimiento no está en ninguna MT',
        tmRows.length ? ui.table(pcols(false), tmRows, { dense: true, pageSize: 50, placeholder: 'Filtrar Pokémon…', countLabel: ['Pokémon', 'Pokémon'], filterText: function (r) { return r.p.name + ' ' + r.dex; } }) : ui.empty('Ningún Pokémon la aprende')));
    }
  }

  /* ---------------- habilidades ---------------- */
  var AF = null;
  function renderAbilities(el, query) {
    var m = REM.state.model;
    var presets = query && (query.status != null || query.changed != null);
    if (!AF || presets) AF = { status: (query && query.status) || '', changed: !!(query && query.changed) };
    var rework = m.abilities.filter(function (a) { return a.status === 'Reworked'; }).length;
    el.appendChild(ui.pageHeader({ title: 'Habilidades', sub: REM.num(m.abilities.length) + ' habilidades' + (rework ? ' · ' + rework + ' reelaboradas en REM' : '') + '. Compara la descripción original con la nueva y ve qué Pokémon la portan.' }));
    var cols = [
      { key: 'name', label: 'Habilidad', render: function (a) { return ui.link('ability', a.sym); } },
      { key: 'status', label: 'Estado', sort: function (a) { return ({ Reworked: 0, Buffed: 1, Kept: 2, Untouched: 3 })[a.status] != null ? ({ Reworked: 0, Buffed: 1, Kept: 2, Untouched: 3 })[a.status] : 4; }, render: function (a) { var st = ui.ABIL_STATUS[a.status]; return st ? ui.badge(st[0], st[1]) : (a.changed ? ui.badge('Modificada', 'mod') : null); } },
      { key: 'description', label: 'Descripción', sort: false, className: 'td-wide', render: function (a) { return h('span', a.description || ''); } },
      { key: 'holders', label: 'Portadores', align: 'right', defaultDir: 'desc', sort: function (a) { return (a.holders || []).length; }, render: function (a) { return REM.num((a.holders || []).length); } }
    ];
    var tbl;
    function rows() {
      return m.abilities.filter(function (a) {
        if (AF.status && a.status !== AF.status) return false;
        if (AF.changed && !(a.changed || a.status === 'Reworked' || a.status === 'Buffed')) return false;
        return true;
      });
    }
    function upd() { tbl.setRows(rows()); }
    var toolbar = [
      ui.select('Estado', [['', 'Todos'], ['Reworked', 'Reelaboradas'], ['Buffed', 'Mejoradas'], ['Kept', 'Mantenidas'], ['Untouched', 'Sin cambios']], AF.status, function (v) { AF.status = v; upd(); }),
      ui.check('Cambiadas en REM', AF.changed, function (v) { AF.changed = v; upd(); })
    ];
    tbl = ui.table(cols, rows(), { placeholder: 'Filtrar habilidades…', toolbar: toolbar, pageSize: 120, sort: 'name', countLabel: ['habilidad', 'habilidades'], filterText: function (a) { return a.name + ' ' + a.sym + ' ' + (a.description || ''); } });
    el.appendChild(tbl);
  }

  function renderAbility(el, parts) {
    var a = REM.ent('ability', parts[0]);
    if (!a) { el.appendChild(REM.router.notFound({ hash: '#/ability/' + (parts[0] || '') })); return; }
    var st = ui.ABIL_STATUS[a.status];
    el.appendChild(ui.pageHeader({
      crumbs: [{ label: 'Habilidades', href: '#/abilities' }, { label: a.name }],
      title: a.name, meta: [st ? ui.badge(st[0], st[1]) : null, a.changed ? ui.badge('Cambiada en REM', 'mod') : null, h('code', a.sym)]
    }));
    var cur = ui.card('Descripción actual', h('p.lead', a.description || 'Sin descripción.'));
    var old = a.baseline && a.baseline.description;
    if (old && old !== a.description) cur.appendChild(h('div.beforeafter', h('div', h('span.ba__tag', 'Antes'), h('p', old)), h('div', h('span.ba__tag.ba__tag--new', 'Ahora'), h('p', a.description || '—'))));
    else if (old) cur.appendChild(h('p.small.muted', 'La descripción no cambia respecto al juego original.'));
    var right = ui.card('Nota de diseño', a.note ? h('p', a.note) : ui.empty('Sin nota de diseño registrada'));
    if (st) right.appendChild(h('p.small.muted', 'Estado: ', h('b', st[0]), { Reworked: ' — su efecto se ha rediseñado.', Buffed: ' — se ha mejorado respecto al original.', Kept: ' — se mantiene tal cual.', Untouched: ' — no se ha tocado.' }[a.status] || ''));
    el.appendChild(h('div.grid.grid--2', cur, right));
    var hol = (a.holders || []).filter(function (dx) { return REM.idx.pokemonByDex[dx]; }).map(function (dx) { return { dex: dx, p: REM.idx.pokemonByDex[dx] }; });
    var cols = [
      { key: 'name', label: 'Pokémon', sort: function (r) { return r.p.name; }, render: function (r) { return h('span.cellpoke', ui.pokeIcon(r.dex, { size: 36 }), ui.link('pokemon', r.dex)); } },
      { key: 'dex', label: 'Nº', align: 'right', sort: function (r) { return r.dex; }, render: function (r) { return '#' + REM.pad3(r.dex); } },
      { key: 'types', label: 'Tipos', sort: false, render: function (r) { return ui.typeBadges(r.p.types, { small: true }); } },
      { key: 'bst', label: 'BST', align: 'right', defaultDir: 'desc', sort: function (r) { return r.p.stats && r.p.stats.bst; }, render: function (r) { return r.p.stats ? String(r.p.stats.bst) : '—'; } },
      { key: 'new', label: 'En REM', sort: false, render: function (r) { var ad = r.p.diff && r.p.diff.abilities; return ad && (ad.added || []).indexOf(a.sym) >= 0 ? ui.badge('La gana en REM', 'new') : null; } }
    ];
    el.appendChild(ui.section('Pokémon con esta habilidad', hol.length ? REM.num(hol.length) + ' Pokémon' : null,
      hol.length ? ui.table(cols, hol, { dense: true, pageSize: 60, placeholder: 'Filtrar Pokémon…', countLabel: ['Pokémon', 'Pokémon'], filterText: function (r) { return r.p.name + ' ' + r.dex; } }) : ui.empty('Ningún Pokémon la porta')));
  }

  /* ---------------- registro ---------------- */
  REM.router.register('moves', { title: 'Movimientos', render: function (el, p, q) { renderMoves(el, q); } });
  REM.router.register('move', { title: function (p) { var x = REM.ent('move', p[0]); return x ? x.name : 'Movimiento'; }, render: function (el, p) { if (!p.length) { REM.router.go('#/moves', { replace: true }); return; } renderMove(el, p); } });
  REM.router.register('abilities', { title: 'Habilidades', render: function (el, p, q) { renderAbilities(el, q); } });
  REM.router.register('ability', { title: function (p) { var x = REM.ent('ability', p[0]); return x ? x.name : 'Habilidad'; }, render: function (el, p) { if (!p.length) { REM.router.go('#/abilities', { replace: true }); return; } renderAbility(el, p); } });

  function pick(list, step, extra) {
    var out = [], seen = {};
    function add(x) { if (x && !seen[x.sym]) { seen[x.sym] = 1; out.push(x); } }
    list.forEach(function (x, i) { if (i % step === 0) add(x); });
    (extra || []).forEach(add);
    return out;
  }
  REM.selftest.add('moves', function () {
    var m = REM.state.model;
    var ch = m.moves.filter(function (x) { return x.diff && x.diff.changed; }).slice(0, 8);
    var tm = m.moves.filter(function (x) { return x.tm != null; }).slice(0, 4);
    return ['#/moves', '#/moves?changed=1'].concat(pick(m.moves, 40, ch.concat(tm)).map(function (x) { return '#/move/' + encodeURIComponent(x.sym); }));
  });
  REM.selftest.add('abilities', function () {
    var m = REM.state.model;
    var rw = m.abilities.filter(function (a) { return a.status === 'Reworked'; }).slice(0, 8);
    return ['#/abilities', '#/abilities?changed=1'].concat(pick(m.abilities, 14, rw).map(function (x) { return '#/ability/' + encodeURIComponent(x.sym); }));
  });
})(window);
