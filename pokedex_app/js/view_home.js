/* ==========================================================================
 * Vista Inicio  (#/)
 * ========================================================================== */
(function (global) {
  'use strict';
  var REM = global.REM, h = REM.h, ui = REM.ui;

  function counts(m) {
    var c = m.meta.counts || {};
    function n(k, arr) { return c[k] != null && c[k] !== 0 ? c[k] : (arr ? arr.length : 0); }
    return {
      pokemon: n('pokemon', m.pokemon), moves: n('moves', m.moves), abilities: n('abilities', m.abilities), items: n('items', m.items),
      tms: n('tms', m.tms), locations: n('locations', m.locations), wildSlots: c.wildSlots || 0, fishSlots: c.fishSlots || 0,
      steps: n('steps', m.progression), chapters: n('chapters', m.story), characters: n('characters', m.characters),
      shops: n('shops', m.shops), missions: n('missions', m.missions)
    };
  }

  /* Calcula «Qué cambia en REM» desde el campo diff de cada entidad. */
  function changes(m) {
    var r = { retyped: 0, stats: 0, abilities: 0, evolutions: 0, learnset: 0, any: 0, movesChanged: 0, abilitiesReworked: 0, itemsNew: 0, itemsMod: 0, bstUp: 0, bstDown: 0 };
    m.pokemon.forEach(function (p) {
      var d = p.diff; if (!d || !d.changed) return;
      r.any++;
      if (d.types) r.retyped++;
      var st = d.stats;
      if (st && Object.keys(st).some(function (k) { return st[k] !== 0 && st[k] != null; })) { r.stats++; if (st.bst > 0) r.bstUp++; else if (st.bst < 0) r.bstDown++; }
      if (d.abilities && ((d.abilities.added || []).length)) r.abilities++;
      if (d.evolutions === true || (Array.isArray(d.evolutions) && d.evolutions.length)) r.evolutions++;
      if ((d.movesAdded || []).length || (d.movesRemoved || []).length) r.learnset++;
    });
    m.moves.forEach(function (x) { if (x.diff && x.diff.changed) r.movesChanged++; });
    m.abilities.forEach(function (a) { if (a.status === 'Reworked' || a.status === 'Buffed' || (a.changed && a.status == null)) r.abilitiesReworked++; });
    m.items.forEach(function (i) { if (i.isNew) r.itemsNew++; else if (i.diff && i.diff.changed) r.itemsMod++; });
    return r;
  }
  REM.homeChanges = changes;

  var SECTIONS = [
    { icon: '📖', title: 'Pokédex Maestra', href: '#/pokedex', text: 'Los 721 Pokémon con estadísticas, evoluciones, ubicaciones, learnsets y MT; con el cambio frente al juego original.' },
    { icon: '⚔️', title: 'Movimientos y Habilidades', href: '#/moves', text: 'Cada movimiento y habilidad con su valor antiguo y nuevo, quién lo aprende y quién lo porta.' },
    { icon: '🎒', title: 'Objetos, MT y Tiendas', href: '#/items', text: '414 objetos, las 100 MT, las tiendas por medallas y las misiones de Pía.' },
    { icon: '🗺️', title: 'Mapa y Atlas', href: '#/map', text: 'El mapa de Oniria, las 64 ubicaciones, sus encuentros salvajes y los objetos de cada lugar.' },
    { icon: '📈', title: 'Progresión', href: '#/progression', text: 'Los 68 pasos del juego con topes de nivel, jefes y MT recomendadas (sin spoilers).' },
    { icon: '📜', title: 'Personajes y Crónicas', href: '#/characters', text: 'Fichas de personajes y los 68 capítulos de la historia.' },
    { icon: '⚠️', title: 'Avisos de Sintaxis PBS', href: '#/warnings', text: 'Errores y avisos detectados al leer los archivos del PBS, con sugerencias.' }
  ];

  function healthCard(m) {
    var hh = m.meta.health || {}, st = hh.errors ? 'error' : hh.warnings ? 'warn' : 'ok';
    var label = { ok: 'En orden', warn: 'Con avisos', error: 'Con errores' }[st];
    var files = (m.files || []);
    var okFiles = files.filter(function (f) { return f.exists !== false; }).length;
    return h('section.card.home-health.home-health--' + st, { 'aria-label': 'Salud del PBS' },
      h('div.home-health__head', h('i.health__dot', { 'aria-hidden': 'true' }), h('h2', 'Salud del PBS'), h('span.chip.chip--' + (st === 'ok' ? 'ok' : st === 'warn' ? 'warn' : 'err'), label)),
      ui.kv([
        ['Errores', String(hh.errors || 0)], ['Avisos', String(hh.warnings || 0)],
        ['Archivos', files.length ? okFiles + ' de ' + files.length + ' presentes' : null],
        ['Fuente', m.meta.source === 'bundle' ? 'Bundle de respaldo (sin PBS en vivo)' : 'PBS en vivo'],
        ['Última lectura', REM.state.lastLoad ? new Date(REM.state.lastLoad).toLocaleString('es-ES') : null],
        ['Modelo generado', m.meta.generatedAt ? new Date(m.meta.generatedAt).toLocaleString('es-ES') : null]
      ]),
      h('div.row', { style: { marginTop: '12px' } }, h('a.btn.btn--sm', { href: '#/warnings' }, st === 'ok' ? 'Ver panel de avisos' : 'Ver avisos de sintaxis')));
  }

  function changeTile(label, n, href, sub) {
    return ui.stat(label, REM.num(n), { href: href, sub: sub });
  }

  function featuredRow(title, sub, list, extraFn) {
    var g = h('div.home-feat');
    list.forEach(function (p) {
      g.appendChild(h('a.home-feat__item', { href: REM.router.href('pokemon', p.dex), title: p.name },
        ui.pokeIcon(p.dex, { size: 56 }),
        h('span.home-feat__name', p.name),
        extraFn ? extraFn(p) : null));
    });
    return ui.section(title, sub, g);
  }

  REM.router.register('', {
    aliases: ['home', 'inicio'],
    title: 'Inicio',
    render: function (el) {
      var m = REM.state.model, c = counts(m), ch = changes(m);
      var widget = REM.search.widget({ inline: true, placeholder: 'Busca un Pokémon, movimiento, habilidad, objeto, lugar, personaje…' });
      el.appendChild(h('section.hero',
        h('div.hero__text',
          h('span.hero__eyebrow', 'Región Oniria · fan-game Essentials v16'),
          h('h1', 'Pokémon REM ', h('span.hero__accent', 'Master Codex')),
          h('p.hero__lead', 'La enciclopedia viva del juego: lee tu PBS en directo, compara cada cambio con el original y enlaza todo con todo.')),
        h('div.hero__search', widget,
          h('p.hero__hint', 'Pulsa ', h('kbd', 'Ctrl'), '+', h('kbd', 'K'), ' en cualquier pantalla para buscar. Atajos: ', h('kbd', 'g'), ' ', h('kbd', 'p'), ' Pokédex · ', h('kbd', 'g'), ' ', h('kbd', 'i'), ' Objetos.'))));

      /* contadores en vivo */
      var tiles = [
        ['Pokémon', c.pokemon, '#/pokedex'], ['Movimientos', c.moves, '#/moves'], ['Habilidades', c.abilities, '#/abilities'],
        ['Objetos', c.items, '#/items'], ['MT', c.tms, '#/tms'], ['Ubicaciones', c.locations, '#/atlas'],
        ['Encuentros salvajes', c.wildSlots, '#/atlas', c.fishSlots ? '+ ' + c.fishSlots + ' de pesca' : null],
        ['Pasos de progresión', c.steps, '#/progression'], ['Capítulos', c.chapters, '#/story'],
        ['Personajes', c.characters, '#/characters'], ['Tiendas', c.shops, '#/shops'], ['Misiones de Pía', c.missions, '#/missions']
      ];
      var grid = h('div.home-counters');
      tiles.forEach(function (t) { grid.appendChild(ui.stat(t[0], REM.num(t[1]), { href: t[2], sub: t[3] })); });
      el.appendChild(ui.section('El Codex en cifras', null, grid));

      /* salud + qué cambia */
      var changeGrid = h('div.home-changes',
        changeTile('Pokémon retipados', ch.retyped, '#/pokedex?change=Retipado'),
        changeTile('Con stats distintos', ch.stats, '#/pokedex?change=Stats', '↑ ' + ch.bstUp + ' · ↓ ' + ch.bstDown + ' BST'),
        changeTile('Con habilidades nuevas', ch.abilities, '#/pokedex?change=Habilidades'),
        changeTile('Evoluciones nuevas', ch.evolutions, '#/pokedex?change=' + encodeURIComponent('Evolución')),
        changeTile('Learnsets cambiados', ch.learnset, '#/pokedex?change=Learnset'),
        changeTile('Movimientos cambiados', ch.movesChanged, '#/moves?changed=1'),
        changeTile('Habilidades reelaboradas', ch.abilitiesReworked, '#/abilities?changed=1'),
        changeTile('Objetos nuevos', ch.itemsNew, '#/items?isnew=1', ch.itemsMod ? '+ ' + ch.itemsMod + ' modificados' : null));
      el.appendChild(h('div.home-split',
        h('div', ui.section('Qué cambia en REM', ch.any ? REM.num(ch.any) + ' de ' + REM.num(c.pokemon) + ' Pokémon tienen algún cambio frente al original.' : 'Sin comparación disponible con el juego original.', changeGrid)),
        h('div', ui.section('Estado de los datos', null, healthCard(m)))));

      /* accesos rápidos */
      var cards = h('div.home-sections');
      SECTIONS.forEach(function (s) {
        cards.appendChild(h('a.home-sec', { href: s.href }, h('span.home-sec__icon', { 'aria-hidden': 'true' }, s.icon),
          h('span.home-sec__body', h('b', s.title), h('span', s.text))));
      });
      el.appendChild(ui.section('Secciones', null, cards));

      /* destacados */
      var withBst = m.pokemon.filter(function (p) { return p.diff && p.diff.stats && p.diff.stats.bst; });
      var top = withBst.slice().sort(function (a, b) { return Math.abs(b.diff.stats.bst) - Math.abs(a.diff.stats.bst) || a.dex - b.dex; }).slice(0, 8);
      if (top.length) el.appendChild(featuredRow('Mayores cambios de estadísticas', 'Los Pokémon cuyo total de base más ha cambiado.', top, function (p) { return ui.deltaEl(p.diff.stats.bst); }));
      var retyped = m.pokemon.filter(function (p) { return p.diff && p.diff.types; }).slice(0, 8);
      if (retyped.length) el.appendChild(featuredRow('Recién retipados', 'Ahora tienen otro tipo; pasa el cursor para ver el cambio.', retyped, function (p) { return ui.typeBadges(p.types, { small: true }); }));
      var rnd = m.pokemon.length ? m.pokemon[Math.floor(Math.random() * m.pokemon.length)] : null;
      if (rnd) el.appendChild(h('div.row', { style: { marginTop: '24px' } },
        h('button.btn', { type: 'button', onclick: function () { var p = m.pokemon[Math.floor(Math.random() * m.pokemon.length)]; REM.router.go(REM.router.href('pokemon', p.dex)); } }, '🎲 Pokémon al azar'),
        h('span.muted.small', 'o abre uno de los iniciales: '), ui.link('pokemon', 1), ui.link('pokemon', 4), ui.link('pokemon', 7)));
    }
  });

  REM.selftest.add('home', ['#/']);
})(window);
