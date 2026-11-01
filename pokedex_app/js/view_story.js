/* ==========================================================================
   Pokémon REM Master Codex — Crónicas de Oniria (lector tipo novela)
   Rutas: #/story (índice por actos + libro de cuentas) y #/story/<CHAPTER_KEY> (PRELUDE, CHAPTER_01…68)
   Propiedad: codex-front-world. Solo usa la API pública de SPEC §5.
   El texto de cada párrafo se escapa SIEMPRE con REM.esc antes de añadir cursivas/negritas seguras.
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
  function store(k, d) { return REM.util && REM.util.store ? REM.util.store.get(k, d) : d; }
  function storeSet(k, v) { if (REM.util && REM.util.store) REM.util.store.set(k, v); }
  function emptyMsg(msg) {
    return REM.ui && REM.ui.empty ? REM.ui.empty(msg || 'Sin datos') : h('p', { class: 'w-empty' }, msg || 'Sin datos');
  }
  function guard(label, fn, fallback) {
    try { return fn(); } catch (e) {
      if (REM.fail) REM.fail('crónicas · ' + label, e);
      return fallback === undefined ? h('p', { class: 'w-empty' }, 'No se pudo mostrar esta sección.') : fallback;
    }
  }
  function link(kind, id, label) {
    if (id != null && id !== '' && REM.ent(kind, id)) return REM.ui.link(kind, id, label);
    return h('span', { class: 'w-plain' }, label != null ? label : str(id));
  }
  function badge(text, cls, title) { return h('span', { class: 'badge w-badge ' + (cls || ''), title: title || null }, text); }
  var ACTS = ['I', 'II', 'III', 'IV', 'V'];
  function actNum(a) { var i = ACTS.indexOf(str(a).toUpperCase()); return i < 0 ? 0 : i + 1; }
  function plainName(n) { return stripAcc(n).replace(/\(.*?\)/g, '').replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim(); }
  function locName(k) { var l = idx('locByKey')[k]; return l ? l.name : str(k); }
  function sess(k, d) { try { var v = sessionStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } }
  function sessSet(k, v) { try { sessionStorage.setItem(k, v); } catch (e) { /* sin almacenamiento */ } }

  /* Un párrafo: se escapa con REM.esc y solo después se permiten cursivas/negritas seguras. */
  function richHtml(s) {
    s = str(s);
    var keep = [];
    s = s.replace(/\[[^\]\n]*(?:PENDIENTE|Pendiente|REVISI[ÓO]N|Revisi[óo]n)[^\]\n]*\]\*?/g, function (m) {
      keep.push(m); return '\u0001' + (keep.length - 1) + '\u0002';
    });
    s = esc(s);
    s = s.replace(/\*\*([^*\n]+?)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/(^|[^*\w])\*([^*\s][^*\n]*?)\*(?![*\w])/g, '$1<em>$2</em>');
    s = s.replace(/(^|[^_\w])_([^_\s][^_\n]*?)_(?![_\w])/g, '$1<em>$2</em>');
    s = s.replace(/\u0001(\d+)\u0002/g, function (_, i) { return '<mark class="w-pending">' + esc(keep[+i]) + '</mark>'; });
    return s;
  }
  var SCENE_RE = /^\s*(?:\*\s*\*\s*\*|-{3,}|—{2,}|_{3,}|·\s*·\s*·|⁂|#{1,3}\s*)\s*$/;
  function paraNode(p) {
    p = str(p);
    if (SCENE_RE.test(p)) return h('hr', { class: 'w-scene', 'aria-hidden': 'true' });
    var head = /^(#{2,4})\s+(.+)$/.exec(p);
    if (head) { var hh = h('h3', { class: 'w-novel-h' }); hh.innerHTML = richHtml(head[2]); return hh; }
    var q = /^>\s?(.*)$/.exec(p);
    var node = h(q ? 'blockquote' : 'p', { class: q ? 'w-novel-quote' : null });
    node.innerHTML = richHtml(q ? q[1] : p);
    return node;
  }

  function chapterNum(ch) {
    var m = /CHAPTER_0*(\d+)/.exec(str(ch && ch.key));
    return m ? parseInt(m[1], 10) : null;
  }
  function allChapters() {
    var M = model();
    var list = arr(M && M.story).slice();
    if (M && M.prelude) { var pre = M.prelude; if (!pre.key) pre = Object.assign({ key: 'PRELUDE' }, pre); list.unshift(pre); }
    return list;
  }
  function chapterLabel(ch) {
    var n = chapterNum(ch);
    return (n != null ? 'Capítulo ' + n : 'Preludio') + (ch.title ? ' · ' + str(ch.title) : '');
  }
  function wordCount(ch) {
    var n = 0;
    arr(ch && ch.paragraphs).forEach(function (p) { n += str(p).split(/\s+/).filter(Boolean).length; });
    return n;
  }
  function minutes(ch) { return Math.max(1, Math.round(wordCount(ch) / 200)); }

  /* escena: personajes enlazados cuando existen en la biblia */
  function sceneChars(ch) {
    var chars = arr(model() && model().characters);
    var used = {}, out = [];
    arr(ch.characters).forEach(function (nm, i) {
      var pn = plainName(nm), hit = null;
      var byKey = arr(ch.charKeys)[i];
      if (byKey && idx('charByKey')[byKey] && arr(ch.charKeys).length === arr(ch.characters).length) hit = idx('charByKey')[byKey];
      if (!hit && pn) {
        for (var j = 0; j < chars.length && !hit; j++) {
          var cn = plainName(chars[j].name);
          if (cn && (cn === pn || pn.indexOf(cn) >= 0 || (pn.length > 3 && cn.indexOf(pn) >= 0))) hit = chars[j];
        }
      }
      if (hit) { used[hit.key] = 1; out.push(h('li', null, REM.ui.link('character', hit.key, str(nm)))); }
      else out.push(h('li', null, h('span', { class: 'w-plain' }, str(nm))));
    });
    arr(ch.charKeys).forEach(function (k) {
      if (used[k] || !idx('charByKey')[k]) return;
      used[k] = 1;
      out.push(h('li', null, REM.ui.link('character', k, idx('charByKey')[k].name)));
    });
    return out;
  }

  /* ---------------------------------------------------------------- «leído» (localStorage) */
  var LAST_KEY = 'rem-story-last', READ_KEY = 'rem-story-read', FS_KEY = 'rem-story-fs', TH_KEY = 'rem-story-theme', SPOILER_KEY = 'rem-story-spoiler-ok';
  function readSet() {
    try { var v = JSON.parse(store(READ_KEY, '[]')); return Array.isArray(v) ? v : []; } catch (e) { return []; }
  }
  function markRead(key) {
    var s = readSet();
    if (s.indexOf(key) < 0) { s.push(key); storeSet(READ_KEY, JSON.stringify(s)); }
  }

  /* ---------------------------------------------------------------- índice #/story */
  function renderIndex(el) {
    var M = model();
    var chapters = allChapters();
    if (!M || !chapters.length) {
      el.appendChild(h('div', { class: 'w-view' }, h('h1', null, 'Crónicas de Oniria'), emptyMsg('Sin datos: el modelo todavía no contiene capítulos (rem_story.txt).')));
      return;
    }
    var last = store(LAST_KEY, '');
    var lastCh = last && idx('chapterByKey')[last];
    var read = readSet();
    var actions = [h('a', { class: 'btn', href: '#/characters' }, '👥 Personajes')];
    var first = chapters[0];
    var cta = lastCh ? REM.ui.link('chapter', lastCh.key, '▶ Continuar: ' + chapterLabel(lastCh))
      : (first ? REM.ui.link('chapter', first.key, '▶ Empezar a leer') : null);
    if (cta) { cta.classList.add('btn', 'btn--primary'); actions.unshift(cta); }
    var header = REM.ui.pageHeader({
      crumbs: [{ label: 'Inicio', href: '#/' }, { label: 'Crónicas' }],
      title: 'Crónicas de Oniria',
      sub: 'La novela completa de la aventura: un Preludio, ' + arr(M.story).length + ' capítulos en cinco actos y el libro de cuentas de los seis fragmentos.',
      actions: actions
    });
    var warn = h('div', { class: 'w-callout w-callout-warn', role: 'note' },
      h('b', null, '⚠ Contiene spoilers. '), 'Las Crónicas cuentan la historia entera, incluidos los giros y el final. Si todavía no has jugado, usa la ',
      h('a', { href: '#/progression' }, 'Guía de Progresión'), ' (sin spoilers).');
    var sections = [];
    /* preludio */
    if (M.prelude) {
      var pre = chapters[0];
      sections.push(h('section', { class: 'w-act-sec', 'aria-label': 'Preludio' },
        h('h2', { class: 'w-act-head' }, h('span', { class: 'badge w-badge' }, 'Preludio')),
        h('ol', { class: 'w-chap-grid' }, chapterItem(pre, read, last))));
    }
    ACTS.forEach(function (a) {
      var rows = arr(M.story).filter(function (c) { return str(c.act).toUpperCase() === a; });
      if (!rows.length) return;
      var nums = rows.map(chapterNum).filter(function (n) { return n != null; });
      sections.push(h('section', { class: 'w-act-sec', 'aria-label': 'Acto ' + a },
        h('h2', { class: 'w-act-head w-act-edge-' + actNum(a) },
          h('span', { class: 'badge w-badge w-act-' + actNum(a) }, 'Acto ' + a),
          h('span', { class: 'w-muted' }, nums.length ? ' capítulos ' + Math.min.apply(null, nums) + '–' + Math.max.apply(null, nums) : '')),
        h('ol', { class: 'w-chap-grid' }, rows.map(function (c) { return guard('capítulo ' + c.key, function () { return chapterItem(c, read, last); }, null); }))));
    });
    /* libro de cuentas */
    var ledger = arr(M.ledger);
    sections.push(h('section', { class: 'w-act-sec w-ledger', id: 'libro-de-cuentas', 'aria-label': 'Libro de cuentas de los fragmentos' },
      h('h2', { class: 'w-act-head' }, h('span', { class: 'badge w-badge' }, 'Libro de cuentas'), h('span', { class: 'w-muted' }, ' los seis fragmentos y sus Dominantes')),
      ledger.length ? guard('libro de cuentas', function () { return ledgerTable(ledger); }) : emptyMsg('Sin datos: no hay fragmentos registrados.')));
    el.appendChild(h('div', { class: 'w-view w-story' }, header, warn, sections));
  }
  function chapterItem(c, read, last) {
    var n = chapterNum(c);
    var isRead = read.indexOf(c.key) >= 0, isLast = c.key === last;
    return h('li', { class: 'w-chap' + (isRead ? ' is-read' : '') + (isLast ? ' is-last' : '') },
      h('a', { class: 'w-chap-link', href: REM.router.href('chapter', c.key) },
        h('span', { class: 'w-chap-n' }, n != null ? String(n) : '✦'),
        h('span', { class: 'w-chap-t' },
          h('b', null, str(c.title) || str(c.key)),
          h('small', { class: 'w-muted' }, (c.loc ? locName(c.loc) + ' · ' : '') + '≈ ' + minutes(c) + ' min'),
          c.summary ? h('small', { class: 'w-chap-sum' }, str(c.summary)) : null),
        isRead ? h('span', { class: 'w-chap-flag', title: 'Leído' }, '✓') : (isLast ? h('span', { class: 'w-chap-flag', title: 'Último capítulo abierto' }, '▶') : null)));
  }
  function ledgerTable(ledger) {
    var rows = ledger.map(function (f) {
      return h('tr', null,
        h('td', { class: 'w-num', 'data-label': 'N.º' }, String(f.n != null ? f.n : '')),
        h('td', { 'data-label': 'Fragmento' }, h('b', null, str(f.name))),
        h('td', { 'data-label': 'Dominante' }, str(f.dominant) || '—'),
        h('td', { 'data-label': 'Ubicación' }, f.loc ? link('location', f.loc, locName(f.loc)) : '—'),
        h('td', { 'data-label': 'Capítulo' }, f.chapter ? link('chapter', f.chapter, idx('chapterByKey')[f.chapter] ? chapterLabel(idx('chapterByKey')[f.chapter]) : str(f.chapter)) : '—'),
        h('td', { class: 'w-note', 'data-label': 'Nota' }, str(f.note) || '—'));
    });
    return h('div', { class: 'w-table-wrap' }, h('table', { class: 'tbl w-table' },
      h('thead', null, h('tr', null, ['N.º', 'Fragmento', 'Dominante', 'Ubicación', 'Capítulo', 'Nota'].map(function (t) { return h('th', { scope: 'col' }, t); }))),
      h('tbody', null, rows)));
  }

  /* ---------------------------------------------------------------- lector #/story/<KEY> */
  var FS_STEPS = [15, 16.5, 18, 20, 22, 25];
  function renderChapter(el, key) {
    var M = model();
    var ch = idx('chapterByKey')[key];
    var all = allChapters();
    if (!M || !ch) {
      el.appendChild(h('div', { class: 'w-view' }, h('p', null, h('a', { href: '#/story' }, '← Crónicas')), emptyMsg('Sin datos: no existe el capítulo «' + str(key) + '».')));
      return;
    }
    var i = -1;
    all.forEach(function (c, j) { if (c.key === ch.key) i = j; });
    var prev = i > 0 ? all[i - 1] : null, next = i >= 0 && i < all.length - 1 ? all[i + 1] : null;
    var n = chapterNum(ch);
    storeSet(LAST_KEY, ch.key);

    var fsIdx = parseInt(store(FS_KEY, '2'), 10);
    if (!isFinite(fsIdx) || fsIdx < 0 || fsIdx >= FS_STEPS.length) fsIdx = 2;
    var theme = store(TH_KEY, 'auto');
    if (['auto', 'light', 'sepia', 'dark'].indexOf(theme) < 0) theme = 'auto';

    var reader = h('div', { class: 'w-reader', 'data-rtheme': theme });
    function applyFs() { reader.style.setProperty('--w-fs', FS_STEPS[fsIdx] + 'px'); }
    applyFs();

    /* barra de herramientas + progreso */
    var progress = h('div', { class: 'w-progress', role: 'progressbar', 'aria-label': 'Progreso de lectura', 'aria-valuemin': '0', 'aria-valuemax': '100', 'aria-valuenow': '0' },
      h('span', { class: 'w-progress-fill' }));
    var fsOut = h('span', { class: 'w-fs-out', 'aria-live': 'polite' }, '');
    function fsLabel() { fsOut.textContent = FS_STEPS[fsIdx] + ' px'; }
    fsLabel();
    function fsBtn(label, aria, d) {
      var b = h('button', { type: 'button', class: 'btn btn--sm', 'aria-label': aria, title: aria }, label);
      b.addEventListener('click', function () {
        fsIdx = Math.max(0, Math.min(FS_STEPS.length - 1, fsIdx + d));
        storeSet(FS_KEY, String(fsIdx)); applyFs(); fsLabel();
      });
      return b;
    }
    var themeSel = h('select', { class: 'input w-input', 'aria-label': 'Tema de lectura' },
      [['auto', 'Tema: como la app'], ['light', 'Claro'], ['sepia', 'Sepia'], ['dark', 'Oscuro']].map(function (o) { return h('option', { value: o[0] }, o[1]); }));
    themeSel.value = theme;
    themeSel.addEventListener('change', function () { theme = themeSel.value; storeSet(TH_KEY, theme); reader.setAttribute('data-rtheme', theme); });
    var tools = h('div', { class: 'w-reader-bar', role: 'toolbar', 'aria-label': 'Herramientas de lectura' },
      h('a', { class: 'btn btn--sm', href: '#/story' }, '☰ Índice'),
      prev ? h('a', { class: 'btn btn--sm', href: REM.router.href('chapter', prev.key), title: chapterLabel(prev) }, '← Anterior') : h('span', null),
      next ? h('a', { class: 'btn btn--sm', href: REM.router.href('chapter', next.key), title: chapterLabel(next) }, 'Siguiente →') : h('span', null),
      h('span', { class: 'w-fs-group', role: 'group', 'aria-label': 'Tamaño de letra' }, fsBtn('A−', 'Reducir el tamaño de letra', -1), fsOut, fsBtn('A+', 'Aumentar el tamaño de letra', 1)),
      themeSel, progress);

    /* aviso de spoilers (una vez por sesión) */
    var notice = null;
    if (sess(SPOILER_KEY, '') !== '1') {
      var ok = h('button', { type: 'button', class: 'btn btn--sm' }, 'Entendido');
      notice = h('div', { class: 'w-callout w-callout-warn', role: 'note' },
        h('span', null, h('b', null, '⚠ Aviso de spoilers: '), 'este capítulo cuenta la historia con todo detalle (y puede adelantar giros de la trama).'), ok);
      ok.addEventListener('click', function () { sessSet(SPOILER_KEY, '1'); if (notice.parentNode) notice.parentNode.removeChild(notice); });
    }

    /* cabecera */
    var locKey = ch.loc;
    var sceneList = sceneChars(ch);
    var head = h('header', { class: 'w-novel-head' },
      h('div', { class: 'w-badges' }, ch.act ? badge('Acto ' + str(ch.act), 'w-act-' + actNum(ch.act)) : null,
        h('span', { class: 'badge w-badge' }, n != null ? 'Capítulo ' + n + ' de ' + arr(M.story).length : 'Preludio'),
        h('span', { class: 'badge w-badge w-node', title: 'Tiempo de lectura estimado' }, '≈ ' + minutes(ch) + ' min')),
      h('h1', { class: 'w-novel-title' }, str(ch.title) || str(ch.key)),
      h('p', { class: 'w-novel-meta' },
        locKey ? [h('b', null, 'Lugar: '), link('location', locKey, locName(locKey))] : null),
      sceneList.length ? h('div', { class: 'w-scene-chars' }, h('b', null, 'Personajes en escena: '), h('ul', { class: 'w-chips' }, sceneList)) : null,
      ch.summary ? h('p', { class: 'w-novel-sum' }, str(ch.summary)) : null);

    /* texto */
    var body = h('article', { class: 'w-novel', 'aria-label': 'Texto del capítulo' });
    var paragraphs = arr(ch.paragraphs);
    if (!paragraphs.length) body.appendChild(emptyMsg('Sin datos: este capítulo no tiene texto.'));
    var frag = document.createDocumentFragment();
    paragraphs.forEach(function (p) { frag.appendChild(guard('párrafo', function () { return paraNode(p); }, null) || document.createComment('')); });
    body.appendChild(frag);

    function cardNav(c, dir) {
      if (!c) return h('span', null);
      return h('a', { class: 'w-novel-next w-nav-' + dir, href: REM.router.href('chapter', c.key) },
        h('small', null, dir === 'prev' ? '← Anterior' : 'Siguiente →'), h('b', null, chapterLabel(c)));
    }
    var footer = h('nav', { class: 'w-novel-pager', 'aria-label': 'Capítulos anterior y siguiente' }, cardNav(prev, 'prev'), cardNav(next, 'next'));

    reader.appendChild(tools);
    if (notice) reader.appendChild(notice);
    reader.appendChild(h('div', { class: 'w-novel-wrap' }, head, body, footer,
      h('p', { class: 'w-novel-end' }, h('a', { href: '#/story' }, '← Volver al índice de las Crónicas'))));
    el.appendChild(h('div', { class: 'w-view w-story-view' }, reader));

    /* progreso de lectura */
    var ticking = false, marked = false;
    var fill = progress.firstChild;
    function update() {
      ticking = false;
      var r = body.getBoundingClientRect();
      var vh = window.innerHeight || 800;
      var total = r.height - vh * 0.6;
      var done = total <= 0 ? 1 : Math.min(1, Math.max(0, (vh * 0.3 - r.top) / Math.max(1, total)));
      var pct = Math.round(done * 100);
      fill.style.width = pct + '%';
      progress.setAttribute('aria-valuenow', String(pct));
      if (!marked && pct >= 92) { marked = true; markRead(ch.key); }
    }
    function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(update); } }
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    requestAnimationFrame(update);
    return function () {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
    };
  }

  /* ---------------------------------------------------------------- registro */
  REM.router.register('story', {
    title: function (parts) {
      var ch = parts && parts[0] ? idx('chapterByKey')[parts[0]] : null;
      return ch ? chapterLabel(ch) : 'Crónicas de Oniria';
    },
    render: function (el, parts) {
      if (parts && parts[0]) return renderChapter(el, parts[0]);
      return renderIndex(el);
    }
  });

  if (REM.selftest && REM.selftest.add) {
    REM.selftest.add('story', function () {
      var out = ['#/story'];
      allChapters().forEach(function (c) { out.push('#/story/' + encodeURIComponent(c.key)); });
      return out;
    });
  }
})();
