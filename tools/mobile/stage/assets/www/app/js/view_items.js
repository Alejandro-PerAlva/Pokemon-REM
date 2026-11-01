/* ==========================================================================
 * Vistas Objetos, MT y Tiendas
 *   #/items  #/item/<SYM>  #/tms  #/tm/<n>  #/shops[/<KEY>]  #/missions[/<n>]
 * ========================================================================== */
(function (global) {
  'use strict';
  var REM = global.REM, h = REM.h, ui = REM.ui;

  var ITEM_FIELD_ES = { name: 'Nombre', pocket: 'Bolsillo', price: 'Precio', description: 'Descripción', fieldUse: 'Uso fuera de combate', battleUse: 'Uso en combate', special: 'Código especial', move: 'Movimiento', plural: 'Plural' };

  function itemCell(it, size) {
    return h('span.cellitem', ui.itemIcon(it, { size: size || 32 }), ui.link('item', it.sym));
  }
  function effPrice(it, override) { return override != null && override !== '' ? Number(override) : it.price; }

  function legend() {
    var box = h('div.legend', h('b', 'Leyenda de métodos: '));
    Object.keys(ui.METHODS).forEach(function (k) {
      box.appendChild(h('span.legend__item', ui.methodBadge(k), h('span', ui.METHODS[k][0])));
    });
    return box;
  }
  function whereTable(list, o) {
    o = o || {};
    var rows = (list || []).slice();
    if (!rows.length) return ui.empty('Sin ubicaciones registradas: no aparece en el mapa.');
    var cols = [
      { key: 'loc', label: 'Ubicación', sort: function (w) { return (REM.idx.locByKey[w.loc] || {}).name || w.loc; }, render: function (w) { return REM.idx.locByKey[w.loc] ? ui.link('location', w.loc) : String(w.loc || '—'); } },
      { key: 'zone', label: 'Zona', render: function (w) { return w.zone || null; } }
    ];
    if (o.withItem) cols.unshift({ key: 'item', label: 'Objeto', sort: function (w) { return w.item; }, render: function (w) { return REM.idx.itemBySym[w.item] ? itemCell(REM.idx.itemBySym[w.item], 24) : w.item; } });
    cols.push({ key: 'qty', label: 'Cant.', align: 'right', render: function (w) { return String(w.qty == null ? 1 : w.qty); } });
    cols.push({ key: 'method', label: 'Método', render: function (w) { return ui.methodBadge(w.method); } });
    cols.push({ key: 'note', label: 'Nota', sort: false, className: 'td-wide', render: function (w) { return w.note ? h('span.small', w.note) : null; } });
    return h('div', ui.table(cols, rows, { filter: false, dense: true, pageSize: 60, countLabel: ['ubicación', 'ubicaciones'] }), legend());
  }

  /* ======================= OBJETOS ======================= */
  var IF = null;
  function renderItems(el, query) {
    var m = REM.state.model;
    var presets = query && (query.pocket != null || query.isnew != null || query.mod != null);
    if (!IF || presets) IF = { pocket: (query && query.pocket) || '', isnew: !!(query && query.isnew), mod: !!(query && query.mod) };
    var pockets = {}; m.items.forEach(function (i) { if (i.pocket != null) pockets[i.pocket] = i.pocketName || ('Bolsillo ' + i.pocket); });
    var nNew = m.items.filter(function (i) { return i.isNew; }).length;
    el.appendChild(ui.pageHeader({ title: 'Objetos', sub: REM.num(m.items.length) + ' objetos' + (nNew ? ' · ' + nNew + ' nuevos en REM' : '') + '. Cada ficha indica dónde conseguirlo y qué tiendas o misiones lo ofrecen.' }));
    var cols = [
      { key: 'name', label: 'Objeto', render: function (i) { return itemCell(i); } },
      { key: 'pocket', label: 'Bolsillo', sort: function (i) { return i.pocket; }, render: function (i) { return i.pocketName || null; } },
      { key: 'price', label: 'Precio', align: 'right', render: function (i) { return i.price ? ui.money(i.price) : h('span.muted', 'No se vende'); } },
      { key: 'description', label: 'Descripción', sort: false, className: 'td-wide', render: function (i) { return h('span.small.clamp2', i.description || ''); } },
      { key: 'where', label: 'Dónde', align: 'right', sort: function (i) { return (i.where || []).length; }, render: function (i) { var n = (i.where || []).length; return n ? h('span', { title: n + ' ubicaciones' }, String(n)) : null; } },
      { key: 'chg', label: 'Cambios', sort: function (i) { return i.isNew ? 2 : (i.diff && i.diff.changed ? 1 : 0); }, defaultDir: 'desc', render: function (i) { return ui.diffBadges(i); } }
    ];
    var tbl;
    function rows() {
      return m.items.filter(function (i) {
        if (IF.pocket && String(i.pocket) !== String(IF.pocket)) return false;
        if (IF.isnew && !i.isNew) return false;
        if (IF.mod && !(i.diff && i.diff.changed)) return false;
        return true;
      });
    }
    function upd() { tbl.setRows(rows()); }
    var pocketOpts = [['', 'Todos']].concat(Object.keys(pockets).sort(function (a, b) { return a - b; }).map(function (k) { return [k, pockets[k]]; }));
    var toolbar = [
      ui.select('Bolsillo', pocketOpts, IF.pocket, function (v) { IF.pocket = v; upd(); }),
      ui.check('Solo nuevos', IF.isnew, function (v) { IF.isnew = v; upd(); }),
      ui.check('Solo modificados', IF.mod, function (v) { IF.mod = v; upd(); })
    ];
    tbl = ui.table(cols, rows(), { placeholder: 'Filtrar objetos…', toolbar: toolbar, pageSize: 100, sort: 'name', countLabel: ['objeto', 'objetos'], filterText: function (i) { return i.name + ' ' + i.sym + ' ' + (i.plural || '') + ' ' + (i.pocketName || '') + ' ' + (i.description || ''); } });
    el.appendChild(tbl);
  }

  function renderItem(el, parts) {
    var it = REM.ent('item', parts[0]);
    if (!it) { el.appendChild(REM.router.notFound({ hash: '#/item/' + (parts[0] || '') })); return; }
    var b = it.baseline, d = it.diff || {};
    el.appendChild(ui.pageHeader({
      crumbs: [{ label: 'Objetos', href: '#/items' }, { label: it.name }],
      lead: ui.itemIcon(it, { size: 64 }), title: it.name,
      meta: [it.pocketName ? ui.chip(it.pocketName) : null, ui.chip(it.price ? ui.money(it.price) : 'No se vende'), ui.diffBadges(it), h('code', it.sym), it.tm ? ui.link('tm', it.tm, 'Ver MT' + REM.pad2(it.tm)) : null]
    }));
    var info = ui.card('Descripción', h('p.lead', it.description || 'Sin descripción.'),
      ui.kv([['Plural', it.plural && it.plural !== it.name ? it.plural : null], ['Movimiento', it.move ? ui.link('move', it.move) : null], ['Ficha de MT', it.tm ? ui.link('tm', it.tm, 'MT' + REM.pad2(it.tm)) : null]]));
    if (d.fields && d.fields.indexOf('description') >= 0 && b && b.description) info.appendChild(h('div.beforeafter', h('div', h('span.ba__tag', 'Antes'), h('p', b.description)), h('div', h('span.ba__tag.ba__tag--new', 'Ahora'), h('p', it.description))));
    var side = ui.card('Cambios frente al original');
    if (it.isNew) side.appendChild(h('p', ui.badge('Nuevo', 'new'), ' Este objeto no existe en el juego original.'));
    else if (b && d.fields && d.fields.length) {
      var t = h('table.tbl.tbl--dense.diff-table', h('thead', h('tr', h('th', 'Campo'), h('th', 'Antes'), h('th', ''), h('th', 'Ahora'))),
        h('tbody', d.fields.filter(function (f) { return f !== 'description'; }).map(function (f) {
          var fmt = function (v) { return f === 'price' ? ui.money(v) : (v == null || v === '' ? '—' : String(v)); };
          return h('tr', h('td', ITEM_FIELD_ES[f] || f), h('td', fmt(b[f])), h('td', h('span.arrow', { 'aria-hidden': 'true' }, '→')), h('td', fmt(it[f])));
        })));
      side.appendChild(h('div.tblx', h('div.tblx__scroll', t)));
    } else side.appendChild(h('p.muted', b ? 'Sin cambios frente al juego original.' : 'Sin datos del juego original para comparar.'));
    el.appendChild(h('div.grid.grid--2', info, side));

    el.appendChild(ui.section('Dónde conseguirlo', (it.where || []).length ? REM.num(it.where.length) + ' ubicaciones' : null, whereTable(it.where)));

    var shops = (it.shops || []).filter(function (s) { return REM.idx.shopByKey[s.shop]; });
    var missions = (it.missions || []).filter(function (n) { return REM.idx.missionByN[n]; });
    if (shops.length || missions.length) {
      var kids = [];
      if (shops.length) {
        kids.push(h('h3.subhead', 'Tiendas que lo venden'));
        kids.push(ui.table([
          { key: 'shop', label: 'Tienda', sort: function (s) { return REM.idx.shopByKey[s.shop].name; }, render: function (s) { return ui.link('shop', s.shop); } },
          { key: 'medals', label: 'Medallas', align: 'right', sort: function (s) { return REM.idx.shopByKey[s.shop].medals; }, render: function (s) { var md = REM.idx.shopByKey[s.shop].medals; return md == null ? null : String(md); } },
          { key: 'price', label: 'Precio', align: 'right', sort: function (s) { return effPrice(it, s.price); }, render: function (s) { return ui.money(effPrice(it, s.price)); } }
        ], shops, { filter: false, dense: true, pageSize: 30, countLabel: ['tienda', 'tiendas'] }));
      }
      if (missions.length) {
        kids.push(h('h3.subhead', 'Misiones que lo dan'));
        var ml = h('ul.chiplist'); missions.forEach(function (n) { ml.appendChild(h('li', ui.link('mission', n))); }); kids.push(ml);
      }
      el.appendChild(ui.section('Tiendas y misiones', null, kids));
    }
  }

  /* ======================= MT ======================= */
  var TF = null;
  function tmWhere(t) {
    var w = (t.where || [])[0], loc = w && REM.idx.locByKey[w.loc];
    return loc ? loc.name + ((t.where.length > 1) ? ' +' + (t.where.length - 1) : '') : 'Sin ubicación';
  }
  function renderTMs(el, query) {
    var m = REM.state.model;
    if (!TF || (query && (query.type != null))) TF = { q: '', type: (query && query.type) || '', sort: 'number' };
    el.appendChild(ui.pageHeader({ title: 'Máquinas Técnicas', sub: REM.num(m.tms.length) + ' MT. Cada una enseña un movimiento; haz clic para ver quién la aprende y dónde se consigue.' }));
    var host = h('div.tmgrid.tmgrid--big');
    var count = h('span.muted.small', { 'aria-live': 'polite' });
    function list() {
      var q = REM.norm(TF.q);
      var out = m.tms.filter(function (t) {
        var mv = REM.idx.moveBySym[t.move];
        if (TF.type && !(mv && mv.type === TF.type)) return false;
        if (q) {
          var blob = REM.norm('MT' + REM.pad2(t.number) + ' ' + (mv ? mv.name : t.move) + ' ' + t.move);
          if (blob.indexOf(q) < 0) return false;
        }
        return true;
      });
      var k = TF.sort;
      out.sort(function (a, b) {
        var ma = REM.idx.moveBySym[a.move], mb = REM.idx.moveBySym[b.move];
        if (k === 'name') return REM.collate(ma ? ma.name : a.move, mb ? mb.name : b.move);
        if (k === 'price') return (b.price || 0) - (a.price || 0) || a.number - b.number;
        if (k === 'learners') return (b.learners || []).length - (a.learners || []).length || a.number - b.number;
        if (k === 'power') return ((mb && mb.power) || 0) - ((ma && ma.power) || 0) || a.number - b.number;
        return a.number - b.number;
      });
      return out;
    }
    function draw() {
      var l = list(); REM.clear(host);
      count.textContent = l.length + ' de ' + m.tms.length + ' MT';
      if (!l.length) { host.appendChild(ui.empty('Ninguna MT coincide')); return; }
      var f = document.createDocumentFragment();
      l.forEach(function (t) {
        var mv = REM.idx.moveBySym[t.move];
        f.appendChild(h('a.tmtile.tmtile--big.t-' + (mv ? mv.type : 'NORMAL'), { href: REM.router.href('tm', t.number), 'data-kind': 'tm', 'data-id': String(t.number) },
          h('span.tmtile__n', 'MT' + REM.pad2(t.number)),
          h('span.tmtile__move', mv ? mv.name : t.move),
          h('span.tmtile__meta', mv ? [ui.typeBadge(mv.type, { small: true }), ' ', mv.power ? mv.power + ' pot.' : 'Estado'] : null),
          h('span.tmtile__stats', h('span', ui.money(t.price)), h('span', REM.num((t.learners || []).length) + ' aprendices')),
          h('span.tmtile__where', tmWhere(t))));
      });
      host.appendChild(f);
    }
    var typeOpts = [['', 'Todos los tipos']].concat(m.types.filter(function (t) { return t.sym !== 'QMARKS'; }).map(function (t) { return [t.sym, t.name]; }));
    el.appendChild(h('div.card.toolbar-card',
      ui.input('Buscar MT', TF.q, function (v) { TF.q = v; draw(); }, { placeholder: 'Nº o movimiento…' }),
      ui.select('Tipo', typeOpts, TF.type, function (v) { TF.type = v; draw(); }),
      ui.select('Ordenar por', [['number', 'Número de MT'], ['name', 'Nombre del movimiento'], ['power', 'Potencia'], ['price', 'Precio'], ['learners', 'Nº de aprendices']], TF.sort, function (v) { TF.sort = v; draw(); }),
      count));
    el.appendChild(host);
    draw();
  }

  function renderTM(el, parts) {
    var t = REM.ent('tm', parts[0]);
    if (!t) { el.appendChild(REM.router.notFound({ hash: '#/tm/' + (parts[0] || '') })); return; }
    var mv = REM.idx.moveBySym[t.move], prev = REM.idx.tmByNum[t.number - 1], next = REM.idx.tmByNum[t.number + 1];
    el.appendChild(ui.pageHeader({
      crumbs: [{ label: 'Máquinas Técnicas', href: '#/tms' }, { label: 'MT' + REM.pad2(t.number) }],
      lead: mv ? ui.typeBadge(mv.type) : null, title: 'MT' + REM.pad2(t.number) + ' · ' + (mv ? mv.name : t.move),
      meta: [mv ? ui.categoryBadge(mv.category) : null, ui.chip(ui.money(t.price)), mv ? ui.diffBadges(mv) : null],
      actions: [prev ? ui.link('tm', prev.number, '← MT' + REM.pad2(prev.number)) : null, next ? ui.link('tm', next.number, 'MT' + REM.pad2(next.number) + ' →') : null]
    }));
    if (mv) {
      el.appendChild(ui.card('Movimiento: ' + mv.name, h('p.lead', mv.description || ''),
        h('div.statgrid', ui.stat('Potencia', mv.power || '—'), ui.stat('Precisión', mv.accuracy ? mv.accuracy + '%' : 'Siempre'), ui.stat('PP', mv.pp), ui.stat('Prioridad', (mv.priority > 0 ? '+' : '') + (mv.priority || 0))),
        h('p', ui.link('move', mv.sym, 'Ver ficha completa del movimiento →'))));
    }
    el.appendChild(ui.section('Dónde se encuentra', null, whereTable(t.where)));
    var missions = (t.missions || []).filter(function (n) { return REM.idx.missionByN[n]; });
    var it = REM.idx.itemBySym[t.sym];
    var shops = it ? (it.shops || []).filter(function (s) { return REM.idx.shopByKey[s.shop]; }) : [];
    if (missions.length || shops.length) {
      var ul = h('ul.chiplist');
      missions.forEach(function (n) { ul.appendChild(h('li', ui.link('mission', n))); });
      shops.forEach(function (s) { ul.appendChild(h('li', ui.link('shop', s.shop), h('span.muted', ' · ' + ui.money(effPrice(it, s.price))))); });
      el.appendChild(ui.section('Misiones y tiendas', null, ul));
    }
    var rows = (t.learners || []).filter(function (d) { return REM.idx.pokemonByDex[d]; }).map(function (d) { return { dex: d, p: REM.idx.pokemonByDex[d] }; });
    el.appendChild(ui.section('Pokémon que la aprenden', rows.length ? REM.num(rows.length) + ' Pokémon' : null, rows.length ? ui.table([
      { key: 'name', label: 'Pokémon', sort: function (r) { return r.p.name; }, render: function (r) { return h('span.cellpoke', ui.pokeIcon(r.dex, { size: 36 }), ui.link('pokemon', r.dex)); } },
      { key: 'dex', label: 'Nº', align: 'right', sort: function (r) { return r.dex; }, render: function (r) { return '#' + REM.pad3(r.dex); } },
      { key: 'types', label: 'Tipos', sort: false, render: function (r) { return ui.typeBadges(r.p.types, { small: true }); } }
    ], rows, { dense: true, pageSize: 60, placeholder: 'Filtrar Pokémon…', countLabel: ['Pokémon', 'Pokémon'], filterText: function (r) { return r.p.name + ' ' + r.dex; } }) : ui.empty('Ningún Pokémon la aprende')));
  }

  /* ======================= TIENDAS ======================= */
  var SH = { mode: 'acum', medals: 0 };
  function shopTable(shop, mode) {
    var newSet = new Set((shop.items || []).map(function (x) { return x.item; }));
    var list = mode === 'acum' && (shop.stock || []).length ? shop.stock : (shop.items || []);
    var rows = list.map(function (x) { return { sym: x.item, it: REM.idx.itemBySym[x.item], price: x.price, isNewHere: newSet.has(x.item) }; });
    var cols = [
      { key: 'name', label: 'Objeto', sort: function (r) { return r.it ? r.it.name : r.sym; }, render: function (r) { return r.it ? itemCell(r.it) : r.sym; } },
      { key: 'pocket', label: 'Bolsillo', sort: function (r) { return r.it && r.it.pocket; }, render: function (r) { return r.it ? r.it.pocketName : null; } },
      { key: 'price', label: 'Precio', align: 'right', defaultDir: 'desc', sort: function (r) { return r.it ? effPrice(r.it, r.price) : r.price; }, render: function (r) {
        var base = r.it ? r.it.price : null, p = r.it ? effPrice(r.it, r.price) : r.price;
        return h('span', ui.money(p), r.price != null && base && Number(r.price) !== Number(base) ? h('span.muted.small', ' (base ' + ui.money(base) + ')') : null);
      } },
      { key: 'desc', label: 'Descripción', sort: false, className: 'td-wide', render: function (r) { return r.it ? h('span.small.clamp2', r.it.description || '') : null; } }
    ];
    if (mode === 'acum' && shop.medals) cols.push({ key: 'new', label: '', sort: function (r) { return r.isNewHere ? 1 : 0; }, defaultDir: 'desc', render: function (r) { return r.isNewHere ? ui.badge('Novedad', 'new') : null; } });
    return ui.table(cols, rows, { dense: true, pageSize: 80, placeholder: 'Filtrar objetos de la tienda…', sort: 'price', dir: 'asc', countLabel: ['objeto', 'objetos'], filterText: function (r) { return (r.it ? r.it.name : r.sym) + ' ' + r.sym; } });
  }
  function renderShops(el, parts) {
    var m = REM.state.model;
    var marts = m.shops.filter(function (s) { return s.medals != null; }).sort(function (a, b) { return a.medals - b.medals; });
    var specials = m.shops.filter(function (s) { return s.medals == null; });
    var want = parts && parts[0] ? REM.idx.shopByKey[parts[0]] : null;
    if (want && want.medals != null) SH.medals = want.medals;
    el.appendChild(ui.pageHeader({ title: 'Tiendas', sub: 'Los Poké Marts ampliaron su stock con cada medalla, y ' + specials.length + ' tiendas especiales venden objetos únicos. Los precios entre paréntesis indican el precio base cuando la tienda lo cambia.' }));
    if (!m.shops.length) { el.appendChild(ui.empty('No hay tiendas en el modelo')); return; }

    if (marts.length) {
      var host = h('div.shop-host'), info = h('p.muted.small');
      var tabItems = marts.map(function (s) { return { id: String(s.medals), label: s.medals + (s.medals === 1 ? ' medalla' : ' medallas') }; });
      var modeTabs = ui.tabs([{ id: 'acum', label: 'Stock acumulado' }, { id: 'new', label: 'Solo novedades' }], SH.mode, function (id) { SH.mode = id; draw(); });
      var tabs = ui.tabs(tabItems, String(SH.medals), function (id) { SH.medals = Number(id); draw(); });
      function draw() {
        var shop = marts.filter(function (s) { return s.medals === SH.medals; })[0] || marts[0];
        REM.clear(host);
        var nNew = (shop.items || []).length, nAll = (shop.stock || []).length;
        info.textContent = shop.name + ' · ' + (SH.mode === 'acum' ? REM.num(nAll || nNew) + ' objetos en total, ' + REM.num(nNew) + ' son novedad de este nivel.' : REM.num(nNew) + ' objetos nuevos respecto al nivel anterior.');
        host.appendChild(shopTable(shop, SH.mode));
      }
      el.appendChild(h('section.card', h('header.card__head', h('h2.card__title', 'Poké Marts por medallas'), modeTabs), h('div.row', { style: { marginBottom: '10px' } }, tabs), info, host));
      draw();
    }

    if (specials.length) {
      var wrap = h('div.shopcards');
      specials.forEach(function (s) {
        var rows = (s.items || []).map(function (x) { return { sym: x.item, it: REM.idx.itemBySym[x.item], price: x.price }; });
        var c = h('article.card.shopcard', { id: 'shop-' + s.key },
          h('header.card__head', h('h3', s.name || s.key), s.location ? ui.link('location', s.location) : null),
          s.requirement ? h('p.small', h('b', 'Requisito: '), s.requirement) : null,
          s.description ? h('p.small.muted', s.description) : null,
          rows.length ? ui.table([
            { key: 'name', label: 'Objeto', sort: function (r) { return r.it ? r.it.name : r.sym; }, render: function (r) { return r.it ? itemCell(r.it, 28) : r.sym; } },
            { key: 'price', label: 'Precio', align: 'right', sort: function (r) { return r.it ? effPrice(r.it, r.price) : r.price; }, render: function (r) { return ui.money(r.it ? effPrice(r.it, r.price) : r.price); } }
          ], rows, { filter: false, dense: true, pageSize: 40, countLabel: ['objeto', 'objetos'] }) : ui.empty('Sin objetos'));
        wrap.appendChild(c);
      });
      el.appendChild(ui.section('Tiendas especiales', null, wrap));
      if (want && want.medals == null) setTimeout(function () { var t = document.getElementById('shop-' + want.key); if (t) { t.scrollIntoView({ block: 'center' }); t.classList.add('is-flash'); } }, 50);
    }
  }

  /* ======================= MISIONES ======================= */
  function renderMissions(el, parts) {
    var m = REM.state.model, sel = parts && parts[0] ? Number(parts[0]) : null;
    el.appendChild(ui.pageHeader({ title: 'Misiones', sub: '' + REM.num(m.missions.length) + ' misiones.' }));
    if (!m.missions.length) { el.appendChild(ui.empty('No hay misiones en el modelo')); return; }
    var cols = [
      { key: 'n', label: 'Nº', align: 'right', render: function (x) { return h('b', String(x.n)); } },
      { key: 'title', label: 'Misión', render: function (x) { return x.title ? h('b', x.title) : '—'; } },
      { key: 'species', label: 'Especies a capturar', align: 'right', defaultDir: 'desc', render: function (x) { return REM.num(x.species); } },
      { key: 'item', label: 'Recompensa', sort: function (x) { var i = REM.idx.itemBySym[x.item]; return i ? i.name : x.item; }, render: function (x) {
        var it = REM.idx.itemBySym[x.item], tm = REM.idx.tmBySym[x.item];
        return h('span.cellitem', it ? ui.itemIcon(it, { size: 28 }) : null, it ? (tm ? ui.link('tm', tm.number, [it.name, ' ', h('span.muted', '(MT' + REM.pad2(tm.number) + ')')]) : ui.link('item', x.item)) : String(x.item || '—'), x.qty > 1 ? h('span.muted', ' ×' + x.qty) : null);
      } },
      { key: 'note', label: 'Nota', sort: false, className: 'td-wide', render: function (x) { return x.note ? h('span.small', x.note) : null; } }
    ];
    el.appendChild(ui.table(cols, m.missions, { dense: true, pageSize: 40, placeholder: 'Filtrar misiones…', sort: 'n', countLabel: ['misión', 'misiones'], rowClass: function (x) { return x.n === sel ? 'is-flash' : ''; },
      filterText: function (x) { return x.title + ' ' + x.note + ' ' + x.item + ' ' + x.n; } }));
  }

  /* ---------- registro ---------- */
  REM.router.register('items', { title: 'Objetos', render: function (el, p, q) { renderItems(el, q); } });
  REM.router.register('item', { title: function (p) { var x = REM.ent('item', p[0]); return x ? x.name : 'Objeto'; }, render: function (el, p) { if (!p.length) { REM.router.go('#/items', { replace: true }); return; } renderItem(el, p); } });
  REM.router.register('tms', { title: 'Máquinas Técnicas', render: function (el, p, q) { renderTMs(el, q); } });
  REM.router.register('tm', { title: function (p) { var t = REM.ent('tm', p[0]); return t ? 'MT' + REM.pad2(t.number) : 'MT'; }, render: function (el, p) { if (!p.length) { REM.router.go('#/tms', { replace: true }); return; } renderTM(el, p); } });
  REM.router.register('shops', { title: 'Tiendas', render: function (el, p) { renderShops(el, p); } });
  REM.router.register('missions', { title: 'Misiones', render: function (el, p) { renderMissions(el, p); } });

  REM.selftest.add('items', function () {
    var m = REM.state.model, out = ['#/items', '#/items?isnew=1', '#/items?mod=1'], seen = {};
    function add(i) { if (i && !seen[i.sym]) { seen[i.sym] = 1; out.push('#/item/' + encodeURIComponent(i.sym)); } }
    m.items.filter(function (i) { return i.id >= 674 && i.id <= 717; }).forEach(function (i, k) { if (k % 3 === 0) add(i); });
    m.items.filter(function (i) { return i.isNew; }).slice(0, 6).forEach(add);
    m.items.filter(function (i) { return i.diff && i.diff.changed; }).slice(0, 6).forEach(add);
    m.items.forEach(function (i, k) { if (k % 22 === 0) add(i); });
    return out;
  });
  REM.selftest.add('tms', function () {
    var m = REM.state.model, out = ['#/tms'];
    m.tms.forEach(function (t, k) { if (k % 7 === 0 || t.number === 100) out.push('#/tm/' + t.number); });
    return out;
  });
  REM.selftest.add('shops', function () {
    var m = REM.state.model, out = ['#/shops'];
    m.shops.forEach(function (s, k) { if (k % 3 === 1) out.push('#/shops/' + encodeURIComponent(s.key)); });
    return out;
  });
  REM.selftest.add('missions', function () { return ['#/missions', '#/missions/1']; });
})(window);
