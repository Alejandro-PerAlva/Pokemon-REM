/* ==========================================================================
   Pokémon REM Master Codex — Biblia de personajes
   Rutas: #/characters (rejilla por categoría) y #/character/<KEY> (ficha completa)
   Propiedad: codex-front-world. Solo usa la API pública de SPEC §5.
   ========================================================================== */
(function () {
  'use strict';
  var REM = window.REM;
  if (!REM || !REM.router) return;
  var h = REM.h;
  var esc = REM.esc;

  /* ---------------------------------------------------------------- utilidades */
  function model() { return (REM.state && REM.state.model) || null; }
  function arr(x) { return Array.isArray(x) ? x : []; }
  function str(x) { return x == null ? '' : String(x); }
  function idx(n) { return (REM.idx && REM.idx[n]) || {}; }
  function stripAcc(s) { return str(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); }
  function emptyMsg(msg) {
    return REM.ui && REM.ui.empty ? REM.ui.empty(msg || 'Sin datos') : h('p', { class: 'w-empty' }, msg || 'Sin datos');
  }
  function guard(label, fn, fallback) {
    try { return fn(); } catch (e) {
      if (REM.fail) REM.fail('personajes · ' + label, e);
      return fallback === undefined ? h('p', { class: 'w-empty' }, 'No se pudo mostrar esta sección.') : fallback;
    }
  }
  function link(kind, id, label) {
    if (id != null && id !== '' && REM.ent(kind, id)) return REM.ui.link(kind, id, label);
    return h('span', { class: 'w-plain' }, label != null ? label : str(id));
  }
  function badge(text, cls, title) { return h('span', { class: 'badge w-badge ' + (cls || ''), title: title || null }, text); }
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
  /* texto largo: varios párrafos si hay saltos de línea */
  function paras(text) {
    var parts = str(text).split(/\n{1,}/).map(function (s) { return s.trim(); }).filter(Boolean);
    if (!parts.length) return null;
    return h('div', { class: 'w-prose' }, parts.map(function (p) { return richEl('p', null, p); }));
  }
  function asList(v) {
    if (v == null || v === '') return [];
    if (Array.isArray(v)) return v.map(str).filter(function (s) { return s.trim() !== ''; });
    return str(v).split(/\s*;\s*|\n+/).map(function (s) { return s.trim(); }).filter(Boolean);
  }
  function locName(k) { var l = idx('locByKey')[k]; return l ? l.name : str(k); }
  function plainName(n) { return stripAcc(n).replace(/\(.*?\)/g, '').replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim(); }

  var CAT_ORDER = ['Protagonista', 'Aliado', 'Rival', 'Líder de Gimnasio', 'Alto Mando', 'Campeón', 'Equipo Morfeo', 'Dominante', 'PNJ'];
  var CAT_ICON = { 'Protagonista': '⭐', 'Aliado': '🤝', 'Rival': '⚡', 'Líder de Gimnasio': '🏅', 'Alto Mando': '🏛', 'Campeón': '🏆', 'Equipo Morfeo': '🌑', 'Dominante': '👁', 'PNJ': '💬' };
  function catRank(c) { var i = CAT_ORDER.indexOf(c); return i < 0 ? 99 : i; }
  var LABELS = {
    role: 'Rol', category: 'Categoría', aliases: 'Alias', age: 'Edad', appearance: 'Apariencia', personality: 'Personalidad',
    backstory: 'Historia previa', motivation: 'Motivación', arc: 'Arco narrativo', firstLocation: 'Primera aparición',
    locations: 'Ubicaciones', typeSpecialty: 'Especialidad de tipo', team: 'Equipo', quotes: 'Citas'
  };
  var KNOWN = { key: 1, name: 1, role: 1, category: 1, aliases: 1, age: 1, appearance: 1, personality: 1, backstory: 1, motivation: 1, arc: 1,
    firstLocation: 1, locations: 1, typeSpecialty: 1, team: 1, quotes: 1 };
  var SPOILER_KEYS = { backstory: 1, motivation: 1, arc: 1 };
  function humanize(k) {
    if (LABELS[k]) return LABELS[k];
    var s = str(k).replace(/([a-z0-9])([A-Z])/g, '$1 $2').replace(/[_-]+/g, ' ').trim().toLowerCase();
    return s.charAt(0).toUpperCase() + s.slice(1);
  }
  function spoilerish(k) { return !!SPOILER_KEYS[k] || /secret|twist|spoil|reveal|fate|destino|final|muerte|traici/i.test(k); }

  /* tipo de especialidad -> insignias */
  function typeNodes(txt) {
    var out = [];
    var t = str(txt).trim();
    if (!t || t === '—') return out;
    var ts = arr(model() && model().types);
    function find(token) {
      var k = stripAcc(token).replace(/[^a-z0-9]/g, '');
      if (!k) return null;
      for (var i = 0; i < ts.length; i++) {
        if (stripAcc(ts[i].sym).replace(/[^a-z0-9]/g, '') === k || stripAcc(ts[i].name).replace(/[^a-z0-9]/g, '') === k) return ts[i];
      }
      return null;
    }
    var d = find(t);
    if (d) return [REM.ui.typeBadge(d.sym)];
    t.split(/\s*(?:[\/,;·+]|\by\b|\be\b|\(|\))\s*/i).forEach(function (tok) {
      var f = find(tok);
      if (f) out.push(REM.ui.typeBadge(f.sym));
    });
    if (!out.length) out.push(h('span', { class: 'w-plain' }, t));
    return out;
  }

  /* ---------------------------------------------------------------- cruce personaje <-> capítulos */
  var cache = { model: null, map: null };
  function chapterMap() {
    var M = model();
    if (cache.model === M && cache.map) return cache.map;
    var map = {}, chars = arr(M && M.characters);
    var chapters = arr(M && M.story).slice();
    if (M && M.prelude) chapters.unshift(M.prelude);
    var names = chars.map(function (c) { return { key: c.key, pn: plainName(c.name) }; });
    chapters.forEach(function (ch) {
      var seen = {};
      arr(ch.charKeys).forEach(function (k) { seen[k] = 1; });
      arr(ch.characters).forEach(function (nm) {
        var pn = plainName(nm);
        if (!pn) return;
        names.forEach(function (c) {
          if (c.pn && (c.pn === pn || pn.indexOf(c.pn) >= 0 || (pn.length > 3 && c.pn.indexOf(pn) >= 0))) seen[c.key] = 1;
        });
      });
      Object.keys(seen).forEach(function (k) { (map[k] = map[k] || []).push(ch); });
    });
    cache.model = M; cache.map = map;
    return map;
  }

  /* ---------------------------------------------------------------- estado de filtros */
  var F = { q: '', cats: {}, type: '' };

  function typeKeysOf(c) {
    var out = [];
    typeNodes(c.typeSpecialty).forEach(function () { /* solo para contar */ });
    var ts = arr(model() && model().types), t = stripAcc(c.typeSpecialty);
    ts.forEach(function (x) {
      if (t && (t.indexOf(stripAcc(x.name)) >= 0 || t.indexOf(stripAcc(x.sym)) >= 0)) out.push(x.sym);
    });
    return out;
  }

  function charCard(c) {
    var chs = (chapterMap()[c.key] || []).length;
    var tn = typeNodes(c.typeSpecialty);
    var al = asList(c.aliases);
    return h('article', { class: 'card w-card w-char-card w-cat-edge-' + catRank(c.category) },
      h('div', { class: 'w-char-head' },
        h('span', { class: 'w-char-ico', 'aria-hidden': 'true' }, CAT_ICON[c.category] || '👤'),
        h('div', null,
          h('h3', { class: 'w-char-name' }, REM.ui.link('character', c.key, str(c.name))),
          c.role ? h('p', { class: 'w-char-role' }, str(c.role)) : null)),
      h('div', { class: 'w-badges' }, c.category ? badge(str(c.category), 'w-cat') : null, tn.length ? h('span', { class: 'w-boss-types' }, tn) : null,
        c.age ? badge(str(c.age), 'w-node', 'Edad') : null),
      al.length ? h('p', { class: 'w-char-alias w-muted' }, 'También: ' + al.slice(0, 3).join(' · ')) : null,
      chs ? h('p', { class: 'w-mini-line' }, '📜 ' + chs + (chs === 1 ? ' capítulo' : ' capítulos')) : null);
  }

  function renderList(el) {
    var M = model();
    var chars = arr(M && M.characters);
    if (!M || !chars.length) {
      el.appendChild(h('div', { class: 'w-view' }, h('h1', null, 'Personajes'), emptyMsg('Sin datos: el modelo todavía no contiene personajes (rem_characters.txt).')));
      return;
    }
    var results = h('div', { class: 'w-results', 'aria-live': 'polite' });
    var count = h('p', { class: 'w-count' });
    function match(c) {
      var anyCat = CAT_ORDER.some(function (k) { return F.cats[k]; }) || Object.keys(F.cats).some(function (k) { return F.cats[k]; });
      if (anyCat && !F.cats[c.category]) return false;
      if (F.type && typeKeysOf(c).indexOf(F.type) < 0) return false;
      if (F.q) {
        var hay = stripAcc([c.name, c.role, c.category, asList(c.aliases).join(' '), c.typeSpecialty].join(' '));
        var terms = stripAcc(F.q).split(/\s+/).filter(Boolean);
        for (var i = 0; i < terms.length; i++) if (hay.indexOf(terms[i]) < 0) return false;
      }
      return true;
    }
    function paint() {
      results.textContent = '';
      var rows = chars.filter(match);
      count.textContent = rows.length + ' de ' + chars.length + ' personajes';
      if (!rows.length) { results.appendChild(emptyMsg('Ningún personaje coincide con los filtros.')); return; }
      var groups = {};
      rows.forEach(function (c) { (groups[c.category || 'Otros'] = groups[c.category || 'Otros'] || []).push(c); });
      Object.keys(groups).sort(function (a, b) { return catRank(a) - catRank(b) || a.localeCompare(b, 'es'); }).forEach(function (cat) {
        var grid = h('div', { class: 'w-grid w-grid-chars' });
        groups[cat].forEach(function (c) { guard('tarjeta ' + c.key, function () { grid.appendChild(charCard(c)); return null; }, null); });
        results.appendChild(h('section', { class: 'w-char-group', 'aria-label': cat },
          h('h2', { class: 'w-group-head' }, h('span', { 'aria-hidden': 'true' }, (CAT_ICON[cat] || '👤') + ' '), cat, h('span', { class: 'w-muted' }, ' · ' + groups[cat].length)),
          grid));
      });
    }
    var cats = {};
    chars.forEach(function (c) { cats[c.category || 'Otros'] = (cats[c.category || 'Otros'] || 0) + 1; });
    var catList = Object.keys(cats).sort(function (a, b) { return catRank(a) - catRank(b) || a.localeCompare(b, 'es'); });
    var chipBox = h('div', { class: 'w-chipset', role: 'group', 'aria-label': 'Filtrar por categoría' });
    catList.forEach(function (c) {
      var b = h('button', { type: 'button', class: 'w-chip', 'aria-pressed': F.cats[c] ? 'true' : 'false' }, (CAT_ICON[c] || '') + ' ' + c + ' (' + cats[c] + ')');
      b.addEventListener('click', function () { F.cats[c] = !F.cats[c]; b.setAttribute('aria-pressed', F.cats[c] ? 'true' : 'false'); paint(); });
      chipBox.appendChild(b);
    });
    var q = h('input', { type: 'search', class: 'input w-input', placeholder: 'Buscar por nombre, rol, alias…', 'aria-label': 'Buscar personaje', value: F.q, autocomplete: 'off' });
    q.addEventListener('input', function () { F.q = q.value; paint(); });
    var tSel = h('select', { class: 'input w-input', 'aria-label': 'Filtrar por especialidad de tipo' }, h('option', { value: '' }, 'Cualquier tipo'),
      arr(M.types).filter(function (t) { return chars.some(function (c) { return typeKeysOf(c).indexOf(t.sym) >= 0; }); })
        .map(function (t) { return h('option', { value: t.sym }, t.name); }));
    tSel.value = F.type;
    tSel.addEventListener('change', function () { F.type = tSel.value; paint(); });
    var clear = h('button', { type: 'button', class: 'btn btn--sm' }, 'Limpiar filtros');
    clear.addEventListener('click', function () { F.q = ''; F.cats = {}; F.type = ''; el.textContent = ''; renderList(el); });

    var header = REM.ui.pageHeader({
      crumbs: [{ label: 'Inicio', href: '#/' }, { label: 'Personajes' }],
      title: 'Biblia de personajes',
      sub: chars.length + ' personajes de Oniria: protagonistas, aliados, rivales, líderes, Alto Mando, Equipo Morfeo y Dominantes. Las fichas ocultan los datos de trama tras un aviso de spoilers.',
      actions: [h('a', { class: 'btn', href: '#/story' }, '📜 Crónicas de Oniria')]
    });
    el.appendChild(h('div', { class: 'w-view w-chars' }, header,
      h('div', { class: 'w-filters w-card', role: 'search' },
        h('div', { class: 'w-filter-row' },
          h('label', { class: 'w-field w-field-grow' }, h('span', null, 'Buscar'), q),
          h('label', { class: 'w-field' }, h('span', null, 'Especialidad'), tSel)),
        h('div', { class: 'w-filter-row' }, h('div', { class: 'w-field w-field-grow' }, h('span', null, 'Categoría'), chipBox)),
        h('div', { class: 'w-filter-row w-filter-foot' }, count, clear)),
      results));
    paint();
  }

  /* ---------------------------------------------------------------- ficha */
  function lines(v) {
    if (v == null || v === '') return [];
    if (Array.isArray(v)) return v.map(str).filter(function (x) { return x.trim() !== ''; });
    return str(v).split(/\n+/).map(function (x) { return x.trim(); }).filter(Boolean);
  }
  /* líneas «a | b | c | d» -> tabla (el último campo absorbe los sobrantes) */
  function pipeTable(v, heads, cellFn, cls) {
    var rows = lines(v);
    if (!rows.length) return null;
    var n = heads.length;
    var trs = rows.map(function (ln) {
      var f = ln.split(/\s\|\s|\s*\|\s*/);
      if (f.length > n) f = f.slice(0, n - 1).concat([f.slice(n - 1).join(' | ')]);
      while (f.length < n) f.push('');
      return h('tr', null, f.map(function (c, i) {
        var td = h('td', { 'data-label': heads[i] });
        var node = cellFn ? cellFn(i, c.trim()) : null;
        if (node) td.appendChild(node);
        else { td.innerHTML = rich(c.trim()); if (!c.trim()) td.textContent = '—'; }
        return td;
      }));
    });
    return h('div', { class: 'w-table-wrap' }, h('table', { class: 'tbl tbl--dense w-table ' + (cls || '') },
      h('thead', null, h('tr', null, heads.map(function (t) { return h('th', { scope: 'col' }, t); }))),
      h('tbody', null, trs)));
  }
  function plainBlock(v) {
    if (v == null || v === '') return null;
    if (Array.isArray(v)) {
      var l = lines(v);
      return l.length ? h('ul', { class: 'w-list' }, l.map(function (t) { return richEl('li', null, t); })) : null;
    }
    if (typeof v === 'object') return h('dl', { class: 'kv' }, Object.keys(v).map(function (k) { return [h('dt', null, humanize(k)), h('dd', null, str(v[k]))]; }));
    return paras(v);
  }
  function block(label, node, cls) {
    if (!node) return null;
    return h('section', { class: 'w-sec ' + (cls || ''), 'aria-label': label }, h('h3', { class: 'w-sec-sub' }, label), node);
  }
  function cardBlock(label, node, cls) {
    if (!node) return null;
    return h('section', { class: 'card w-sec ' + (cls || ''), 'aria-label': label }, h('h2', { class: 'w-sec-title' }, label), node);
  }
  var HANDLED = {
    key: 1, name: 1, nameNote: 1, title: 1, role: 1, category: 1, aliases: 1, aliasList: 1, age: 1, oneLiner: 1, appearance: 1, personality: 1,
    themePosition: 1, backstory: 1, motivation: 1, arc: 1, firstLocation: 1, locations: 1, typeSpecialty: 1, combatIdentity: 1, quotesAbout: 1,
    source: 1, quotes: 1, draftNames: 1, allegiance: 1, nameMeaning: 1, light: 1, shadow: 1, themeStance: 1, teamNote: 1, team: 1, teamList: 1,
    voiceStyle: 1, hiddenCluesIntro: 1, hiddenClues: 1, chronology: 1, appearances: 1, battles: 1, gymScenario: 1, gymNumber: 1, philosophy: 1,
    concept: 1, line: 1
  };
  Object.assign(LABELS, {
    nameNote: 'Nota del nombre', title: 'Epíteto', oneLiner: 'En una frase', themePosition: 'Posición temática', combatIdentity: 'Identidad de combate',
    quotesAbout: 'Lo que dicen de él o ella', source: 'Fuente', draftNames: 'Nombre en borrador', allegiance: 'Lealtad', nameMeaning: 'Significado del nombre',
    light: 'Luz', shadow: 'Sombra', themeStance: 'Postura temática', teamNote: 'Nota del equipo', voiceStyle: 'Voz y estilo', hiddenCluesIntro: 'Pistas ocultas (introducción)',
    hiddenClues: 'Pistas ocultas', chronology: 'Cronología', appearances: 'Apariciones', battles: 'Combates', gymScenario: 'Escenario del gimnasio',
    gymNumber: 'Gimnasio', philosophy: 'Filosofía', concept: 'Concepto', aliasList: 'Alias'
  });

  function renderChar(el, key) {
    var M = model();
    var c = idx('charByKey')[key];
    if (!M || !c) {
      el.appendChild(h('div', { class: 'w-view' }, h('p', null, h('a', { href: '#/characters' }, '← Personajes')), emptyMsg('Sin datos: no existe el personaje «' + str(key) + '».')));
      return;
    }
    var chars = arr(M.characters);
    var chapters = chapterMap()[c.key] || [];
    var tn = typeNodes(c.typeSpecialty);
    var counts = [];
    if (c.appearances) counts.push(badge('📜 ' + str(c.appearances) + ' apariciones', 'w-node', 'Apariciones en la historia'));
    if (c.battles) counts.push(badge('⚔ ' + str(c.battles) + ' combates', 'w-node', 'Combates'));
    var gym = c.gymNumber ? badge('Gimnasio ' + str(c.gymNumber), 'w-node') : null;
    var header = REM.ui.pageHeader({
      crumbs: [{ label: 'Personajes', href: '#/characters' }, { label: str(c.category || 'Personaje') }, { label: str(c.name) }],
      title: str(c.name),
      sub: [c.title ? h('em', null, str(c.title)) : null, c.title && c.role ? ' · ' : null, c.role ? str(c.role) : null],
      lead: h('span', { class: 'w-char-ico w-char-ico-lg', 'aria-hidden': 'true' }, CAT_ICON[c.category] || '👤'),
      meta: [c.category ? badge(str(c.category), 'w-cat') : null, tn.length ? h('span', { class: 'w-boss-types', title: 'Especialidad de tipo' }, tn) : null,
        c.age ? badge(str(c.age), 'w-node', 'Edad') : null, gym].concat(counts)
    });

    var main = h('div', { class: 'w-char-main' });
    function put(parent, node) { if (node) parent.appendChild(node); }
    if (c.oneLiner) put(main, h('blockquote', { class: 'w-oneliner' }, richEl('p', null, c.oneLiner)));

    /* perfil (sin spoilers) */
    var aliasL = arr(c.aliasList).length ? arr(c.aliasList) : asList(c.aliases);
    aliasL = aliasL.filter(function (a) { return plainName(a) !== plainName(c.name); });
    var profile = h('dl', { class: 'w-kv' });
    function kv(label, node) { if (!node) return; profile.appendChild(h('dt', null, label)); profile.appendChild(h('dd', null, node)); }
    kv('Alias', aliasL.length ? h('ul', { class: 'w-chips' }, aliasL.map(function (a) { return h('li', null, h('span', { class: 'w-plain' }, a)); })) : null);
    kv(LABELS.draftNames, c.draftNames ? str(c.draftNames) : null);
    kv(LABELS.nameMeaning, c.nameMeaning ? richEl('span', null, c.nameMeaning) : null);
    kv(LABELS.nameNote, c.nameNote ? richEl('span', null, c.nameNote) : null);
    kv(LABELS.gymScenario, c.gymScenario ? richEl('span', null, c.gymScenario) : null);
    kv(LABELS.voiceStyle, c.voiceStyle ? richEl('span', null, c.voiceStyle) : null);
    kv(LABELS.combatIdentity, c.combatIdentity ? richEl('span', null, c.combatIdentity) : null);
    if (profile.children.length) put(main, cardBlock('Perfil', profile));
    var look = [guard('apariencia', function () { return block(LABELS.appearance, plainBlock(c.appearance)); }, null),
      guard('personalidad', function () { return block(LABELS.personality, plainBlock(c.personality)); }, null)].filter(Boolean);
    if (look.length) { var cd = h('section', { class: 'card w-sec', 'aria-label': 'Apariencia y personalidad' }, h('h2', { class: 'w-sec-title' }, 'Apariencia y personalidad')); look.forEach(function (n) { cd.appendChild(n); }); main.appendChild(cd); }

    /* equipo: «Casilla | Especie | Nivel | Notas» (marcadores [PENDIENTE…] tal cual) */
    var teamNode = guard('equipo', function () {
      var t = pipeTable(c.team, ['Casilla', 'Especie', 'Nivel', 'Notas'], null, 'w-table-team');
      var tl = lines(c.teamList);
      if (!t && !tl.length) return null;
      return h('div', null, c.teamNote ? richEl('p', 'w-muted w-small', c.teamNote) : null, t,
        tl.length ? h('ul', { class: 'w-list w-team' }, tl.map(function (x) { return richEl('li', null, x); })) : null);
    }, null);
    put(main, cardBlock('Equipo', teamNode, 'w-team-sec'));

    /* citas */
    var qs = lines(c.quotes);
    if (qs.length) put(main, cardBlock('Citas', h('div', { class: 'w-quotes' }, qs.map(function (t) { return richEl('blockquote', 'w-quote', t); }))));

    /* otros campos desconocidos: visibles salvo que el nombre sugiera trama */
    var extras = Object.keys(c).filter(function (k) { return !HANDLED[k] && c[k] != null && c[k] !== '' && !(Array.isArray(c[k]) && !c[k].length); });
    var extraPlain = extras.filter(function (k) { return !spoilerish(k); }), extraSpoil = extras.filter(spoilerish);
    if (extraPlain.length) {
      var ex = h('dl', { class: 'w-kv' });
      extraPlain.forEach(function (k) { var n = guard('campo ' + k, function () { return plainBlock(c[k]); }, null); if (n) { ex.appendChild(h('dt', null, humanize(k))); ex.appendChild(h('dd', null, n)); } });
      put(main, cardBlock('Otros datos', ex));
    }

    /* spoilers de trama (plegado) */
    var sp = [];
    [['backstory', 'Historia previa'], ['motivation', 'Motivación'], ['arc', 'Arco narrativo'], ['themePosition', 'Posición temática'], ['themeStance', 'Postura temática'],
      ['light', 'Luz'], ['shadow', 'Sombra'], ['philosophy', 'Filosofía'], ['concept', 'Concepto'], ['allegiance', 'Lealtad'], ['hiddenCluesIntro', 'Pistas ocultas: introducción']].forEach(function (p) {
      var n = guard(p[0], function () { return plainBlock(c[p[0]]); }, null);
      if (n) sp.push(block(p[1], n, 'w-field-' + p[0]));
    });
    var clues = lines(c.hiddenClues);
    if (clues.length) sp.push(block(LABELS.hiddenClues, h('ol', { class: 'w-list w-clues' }, clues.map(function (t) { return richEl('li', null, t); }))));
    var qa = lines(c.quotesAbout);
    if (qa.length) sp.push(block(LABELS.quotesAbout, h('div', { class: 'w-quotes' }, qa.map(function (t) { return richEl('blockquote', 'w-quote', t); }))));
    var chron = guard('cronología', function () {
      return pipeTable(c.chronology, ['N.º', 'Escena', 'Ubicación', 'Qué ocurre', 'Papel', '¿Combate?'], function (i, v) {
        if (i === 2 && v && REM.ent('location', v)) return REM.ui.link('location', v, locName(v));
        return null;
      }, 'w-table-chron');
    }, null);
    if (chron) sp.push(block(LABELS.chronology, chron));
    extraSpoil.forEach(function (k) { var n = guard('campo ' + k, function () { return plainBlock(c[k]); }, null); if (n) sp.push(block(humanize(k), n)); });
    sp = sp.filter(Boolean);
    if (sp.length) {
      var det = h('details', { class: 'w-spoiler card' },
        h('summary', null, h('span', { class: 'w-spoiler-ico', 'aria-hidden': 'true' }, '⚠'), ' Contiene spoilers de la trama ',
          h('small', null, '(' + sp.map(function (n) { return n.getAttribute('aria-label'); }).join(', ') + ') — pulsa para mostrar')),
        h('div', { class: 'w-spoiler-body' }, sp));
      main.appendChild(det);
    }
    if (!main.children.length) main.appendChild(emptyMsg('Sin datos: esta ficha no contiene campos de texto.'));

    /* lateral: ubicaciones y capítulos */
    var locKeys = asList(c.locations);
    var first = str(c.firstLocation).trim();
    var locBody = h('div', null,
      first ? h('p', null, h('b', null, 'Primera aparición: '), link('location', first, locName(first))) : null,
      locKeys.length ? h('ul', { class: 'w-chips' }, locKeys.map(function (k) { return h('li', null, link('location', k, locName(k))); })) : (first ? null : emptyMsg('Sin ubicaciones registradas.')));
    var chBody;
    if (chapters.length) {
      chBody = h('details', { class: 'w-card-details' },
        h('summary', null, h('b', null, chapters.length + (chapters.length === 1 ? ' capítulo' : ' capítulos')), h('small', { class: 'w-muted' }, ' · los títulos pueden contener spoilers')),
        h('ul', { class: 'w-list w-chap-list' }, chapters.map(function (ch) {
          var n = /CHAPTER_0*(\d+)/.exec(str(ch.key));
          return h('li', null, link('chapter', ch.key, (n ? n[1] + '. ' : (ch.key === 'PRELUDE' ? 'Preludio · ' : '')) + str(ch.title)));
        })));
    } else chBody = emptyMsg('No aparece en ningún capítulo registrado.');
    var aside = h('aside', { class: 'w-char-aside', 'aria-label': 'Ubicaciones y capítulos' },
      h('div', { class: 'card w-card' }, h('h2', { class: 'w-card-title' }, 'Ubicaciones'), locBody),
      h('div', { class: 'card w-card' }, h('h2', { class: 'w-card-title' }, 'Capítulos en los que aparece'), chBody),
      c.source ? h('p', { class: 'w-muted w-small' }, 'Fuente: ' + str(c.source)) : null);

    /* anterior / siguiente dentro de su categoría */
    var same = chars.filter(function (x) { return x.category === c.category; });
    var i = same.indexOf(c);
    var prev = i > 0 ? same[i - 1] : null, next = i >= 0 && i < same.length - 1 ? same[i + 1] : null;
    var pager = h('div', { class: 'w-pager' },
      prev ? h('span', { class: 'w-pager-item' }, '← ', REM.ui.link('character', prev.key, str(prev.name))) : h('span', null),
      next ? h('span', { class: 'w-pager-item' }, REM.ui.link('character', next.key, str(next.name)), ' →') : h('span', null));

    el.appendChild(h('div', { class: 'w-view w-char w-cat-edge-' + catRank(c.category) }, header,
      h('div', { class: 'w-char-layout' }, main, aside), pager));
  }

  /* ---------------------------------------------------------------- registro */
  REM.router.register('characters', {
    title: 'Personajes',
    render: function (el, parts) {
      if (parts && parts[0]) return renderChar(el, parts[0]);
      return renderList(el);
    }
  });
  REM.router.register('character', {
    title: function (parts) { var c = idx('charByKey')[parts && parts[0]]; return c ? c.name : 'Personaje'; },
    render: function (el, parts) { return renderChar(el, (parts && parts[0]) || ''); }
  });

  if (REM.selftest && REM.selftest.add) {
    REM.selftest.add('characters', function () {
      var out = ['#/characters'];
      arr(model() && model().characters).forEach(function (c) { out.push('#/character/' + encodeURIComponent(c.key)); });
      return out;
    });
  }
})();
