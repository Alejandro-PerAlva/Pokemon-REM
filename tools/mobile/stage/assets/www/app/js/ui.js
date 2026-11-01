/* ==========================================================================
 * Pokémon REM Master Codex — ui.js
 * Componentes compartidos (enlaces, badges, iconos, sprites, tablas, toasts…)
 * y el «shell» (barra superior, subnavegación, tema, salud del PBS).
 *
 * Contrato público (SPEC §5):
 *   REM.ui.link(kind, id, label?) -> <a>
 *       kind ∈ pokemon|move|ability|item|tm|location|character|chapter|step|shop|mission
 *       label puede ser texto, Node, o un objeto {label, icon:true, size, cls}
 *   REM.ui.typeBadge(sym)   REM.ui.categoryBadge('Physical|Special|Status')
 *   REM.ui.pokeIcon(dex,{size})  REM.ui.pokeSprite(dex,{back,shiny,size}) -> <canvas>
 *   REM.ui.itemIcon(sym|item,{size})  REM.ui.diffBadges(entity)  REM.ui.statBars(pokemon)
 *   REM.ui.table(columns, rows, opts)  REM.ui.toast(msg, kind)  REM.ui.empty(msg)
 *   REM.ui.pager({total,page,pageSize,onPage})  (o posicional: total,page,pageSize,fn)
 * Más: ui.card, ui.section, ui.badge, ui.chip, ui.pageHeader, ui.tabs, ui.select,
 *   ui.input, ui.check, ui.kv, ui.copyButton, ui.stat, ui.methodBadge, ui.rarityBadge,
 *   ui.spinner, ui.settle() (espera sprites pendientes).
 * Seguridad: todo texto del PBS entra por nodos de texto (REM.h), jamás innerHTML.
 * ========================================================================== */
(function (global) {
  'use strict';
  var REM = global.REM;
  var h = REM.h, pad3 = REM.pad3;
  var ui = REM.ui = REM.ui || {};

  var GFX = '/gfx/';
  ui.GFX = GFX;
  function eager() { return !!(REM.state && REM.state.selftest); }
  function cls() { return Array.prototype.filter.call(arguments, Boolean).join(' '); }
  function safeClass(s) { return String(s == null ? '' : s).replace(/[^A-Za-z0-9_-]/g, ''); }
  function hasAsset(set, n) {
    var s = REM.idx && REM.idx.assets && REM.idx.assets[set];
    return !s || s.has(Number(n));      // sin inventario de assets => se asume que existe
  }

  /* ------------------------------------------------------------------ *
   * Imágenes rotas: registro + sustituto limpio
   * ------------------------------------------------------------------ */
  ui._imgError = function (ev) {
    var img = ev.target;
    try {
      REM.diag.brokenImages.push({ src: img.getAttribute('src') || '', route: REM.state.route ? REM.state.route.hash : '' });
      var ph = h('span.img-missing', { title: 'Imagen no disponible', 'aria-hidden': 'true' }, '?');
      if (img.parentNode) { img.parentNode.classList.add('is-broken'); img.parentNode.replaceChild(ph, img); }
    } catch (e) { /* ok */ }
  };

  /* ------------------------------------------------------------------ *
   * Tipos y categorías
   * ------------------------------------------------------------------ */
  var CAT_ES = { Physical: 'Físico', Special: 'Especial', Status: 'Estado' };
  var CAT_IDX = { Physical: 0, Special: 1, Status: 2 };
  var CAT_TIP = { Physical: 'Daña según Ataque y Defensa', Special: 'Daña según Atq. Esp. y Def. Esp.', Status: 'No inflige daño directo' };
  ui.CAT_ES = CAT_ES;
  ui.sheet = { types: { ok: false, rowH: 28 }, cat: { ok: false, rowH: 28 } };

  function probeSheet(url, key, nRows) {
    var im = new Image();
    im.onload = function () {
      var hh = im.naturalHeight, w = im.naturalWidth, rows = nRows;
      var rowH = (hh % 28 === 0 && w === 64) ? 28 : (rows ? hh / rows : 28);
      ui.sheet[key] = { ok: im.naturalWidth > 0, rowH: rowH, w: w, h: hh };
      document.documentElement.style.setProperty('--' + key + '-sheet-h', hh + 'px');
      if (key === 'types') document.documentElement.dataset.typeSheet = '1';
    };
    im.onerror = function () { ui.sheet[key].ok = false; document.body && document.body.classList.remove('ts-sprite'); };
    im.src = url;
  }

  ui.typeName = function (sym) {
    var t = REM.idx && REM.idx.typeBySym && REM.idx.typeBySym[sym];
    if (t) return t.name;
    if (!sym) return '?';
    var s = String(sym).toLowerCase(); return s.charAt(0).toUpperCase() + s.slice(1);
  };
  ui.typeBadge = function (sym, o) {
    o = o || {};
    var t = REM.idx && REM.idx.typeBySym && REM.idx.typeBySym[sym];
    var name = ui.typeName(sym);
    var idx = t && t.index != null ? t.index : -1;
    var sp = h('i.tsp', { 'aria-hidden': 'true', style: { '--ty': (idx >= 0 ? -idx * ui.sheet.types.rowH : 0) + 'px' } });
    return h('span.tbadge.t-' + safeClass(sym) + (o.small ? '.tbadge--sm' : ''), { title: name }, sp, h('span.tn', name));
  };
  ui.typeBadges = function (types, o) {
    var w = h('span.tbadges');
    (types || []).forEach(function (t) { if (t) w.appendChild(ui.typeBadge(t, o)); });
    return w;
  };
  ui.categoryBadge = function (cat) {
    var c = CAT_ES[cat] ? cat : 'Status';
    return h('span.cbadge.c-' + c, { title: CAT_TIP[c] },
      h('i.csp', { 'aria-hidden': 'true', style: { '--cy': (-CAT_IDX[c] * ui.sheet.cat.rowH) + 'px' } }), h('span.cn', CAT_ES[c]));
  };

  /* ------------------------------------------------------------------ *
   * Enlaces entre entidades
   * ------------------------------------------------------------------ */
  var KIND_ICON = { pokemon: '', move: '', ability: '', item: '', tm: '', location: '', character: '', chapter: '', step: '', shop: '', mission: '' };
  ui.link = function (kind, id, label) {
    var opts = {};
    if (label && typeof label === 'object' && !label.nodeType && !Array.isArray(label)) { opts = label; label = opts.label; }
    var ent = REM.ent(kind, id);
    var text = label != null ? label : REM.label(kind, id);
    var kids = [];
    if (opts.icon && kind === 'pokemon' && ent) kids.push(ui.pokeIcon(ent.dex, { size: opts.size || 32 }));
    if (opts.icon && kind === 'item' && ent) kids.push(ui.itemIcon(ent, { size: opts.size || 24 }));
    kids.push(text);
    if (!ent && REM.state.model && KIND_ICON[kind] !== undefined) {
      // La entidad no existe en el modelo: no fabricamos un enlace roto.
      try { REM.diag.deadRefs.push({ kind: kind, id: String(id), route: REM.state.route ? REM.state.route.hash : '' }); } catch (e) { /* ok */ }
      return h('span.elink.elink--missing', { title: 'No existe en el modelo: ' + id }, kids);
    }
    return h('a.elink.k-' + kind + (opts.cls ? '.' + opts.cls : ''), {
      href: REM.router.href(kind, id), 'data-kind': kind, 'data-id': id == null ? '' : String(id)
    }, kids);
  };

  /* ------------------------------------------------------------------ *
   * Iconos de Pokémon (recorte del primer cuadro) y de objetos
   * ------------------------------------------------------------------ */
  ui.pokeIcon = function (dex, o) {
    o = o || {};
    var size = o.size || 48, p = REM.ent('pokemon', dex), n = p ? p.dex : Number(dex);
    var wrap = h('span.picon', { style: { width: size + 'px', height: size + 'px' }, 'aria-hidden': 'true' });
    if (o.title !== false && p) wrap.title = p.name;
    if (!n || !hasAsset('icons', n)) { wrap.classList.add('picon--none'); wrap.appendChild(h('span.img-missing', '?')); return wrap; }
    var img = h('img', {
      src: GFX + 'Icons/icon' + pad3(n) + '.png', alt: '', draggable: 'false',
      loading: (o.eager || eager()) ? 'eager' : 'lazy', decoding: 'async',
      style: { width: (size * 2) + 'px', height: size + 'px' }
    });
    img.addEventListener('error', ui._imgError);
    wrap.appendChild(img);
    return wrap;
  };

  ui.itemIcon = function (sym, o) {
    o = o || {};
    var size = o.size || 32;
    var it = (sym && typeof sym === 'object') ? sym : REM.ent('item', sym);
    var wrap = h('span.iticon', { style: { width: size + 'px', height: size + 'px' }, 'aria-hidden': 'true' });
    var file = it && it.icon ? String(it.icon) : null;
    var base = file ? file.split('/').pop() : null;
    var itemSet = REM.idx && REM.idx.assets && REM.idx.assets.itemIcons;
    if (!file || (itemSet && base && !itemSet.has(base))) {
      wrap.classList.add('iticon--none');
      wrap.title = it ? it.name + ' (sin icono en el juego)' : '';
      wrap.appendChild(h('span.iticon__glyph', '◆'));
      return wrap;
    }
    var img = h('img', { src: GFX + file.replace(/^\/+/, ''), alt: '', draggable: 'false', loading: (o.eager || eager()) ? 'eager' : 'lazy', decoding: 'async', width: size, height: size });
    img.addEventListener('error', ui._imgError);
    wrap.appendChild(img);
    return wrap;
  };

  /* ------------------------------------------------------------------ *
   * Sprites de combate (primer fotograma de tiras horizontales) en <canvas>
   * ------------------------------------------------------------------ */
  var imgCache = Object.create(null), frameCache = Object.create(null);
  ui._pending = new Set();

  function loadImg(url) {
    if (imgCache[url]) return imgCache[url];
    return (imgCache[url] = new Promise(function (res, rej) {
      var im = new Image();
      im.onload = function () { im.naturalWidth > 0 ? res(im) : rej(new Error('Imagen vacía ' + url)); };
      im.onerror = function () { rej(new Error('No se pudo cargar ' + url)); };
      im.src = url;
    }));
  }
  /* Recorta el primer fotograma (cuadrado: lado = alto) al rectángulo no transparente. */
  function frameOf(url) {
    if (frameCache[url]) return frameCache[url];
    return (frameCache[url] = loadImg(url).then(function (im) {
      var fh = im.naturalHeight, fw = Math.min(fh, im.naturalWidth);
      var c = document.createElement('canvas'); c.width = fw; c.height = fh;
      var ctx = c.getContext('2d'); ctx.drawImage(im, 0, 0, fw, fh, 0, 0, fw, fh);
      var x0 = 0, y0 = 0, x1 = fw, y1 = fh;
      try {
        var d = ctx.getImageData(0, 0, fw, fh).data, minX = fw, minY = fh, maxX = -1, maxY = -1;
        for (var y = 0; y < fh; y++) for (var x = 0; x < fw; x++) {
          if (d[(y * fw + x) * 4 + 3] > 10) { if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y; }
        }
        if (maxX >= 0) { x0 = minX; y0 = minY; x1 = maxX + 1; y1 = maxY + 1; }
      } catch (e) { /* lienzo contaminado: se usa el fotograma completo */ }
      var out = document.createElement('canvas'); out.width = x1 - x0; out.height = y1 - y0;
      out.getContext('2d').drawImage(c, x0, y0, x1 - x0, y1 - y0, 0, 0, x1 - x0, y1 - y0);
      return out;
    }));
  }

  function spriteUrl(n, o) {
    var suf = (o.shiny ? 's' : '') + (o.back ? 'b' : '');
    var set = o.shiny ? (o.back ? 'shinyBack' : 'shiny') : (o.back ? 'back' : 'battlers');
    var cand = [];
    if (hasAssetSprite(set, n, suf)) cand.push(GFX + 'Battlers/' + pad3(n) + suf + '.png');
    if (suf && hasAsset('battlers', n)) cand.push(GFX + 'Battlers/' + pad3(n) + '.png');
    cand.push(GFX + 'Battlers/000.png');
    return cand;
  }
  function hasAssetSprite(set, n, suf) {
    var s = REM.idx && REM.idx.assets && REM.idx.assets[set];
    if (set === 'shinyBack' && !s) return !(REM.idx.assets.shiny) ? true : false;
    return !s || s.has(Number(n));
  }

  function drawFrame(cv, frame, size) {
    var dpr = Math.min(2, global.devicePixelRatio || 1);
    var W = Math.round(size * dpr);
    cv.width = W; cv.height = W;
    var ctx = cv.getContext('2d');
    ctx.clearRect(0, 0, W, W);
    var fit = Math.min(W / frame.width, W / frame.height);
    var s = fit >= 2 ? Math.floor(fit) : fit;
    ctx.imageSmoothingEnabled = fit < 2;
    ctx.imageSmoothingQuality = 'high';
    var dw = Math.round(frame.width * s), dh = Math.round(frame.height * s);
    ctx.drawImage(frame, 0, 0, frame.width, frame.height, Math.round((W - dw) / 2), W - dh - Math.round((W - Math.min(dh, W)) / 6), dw, dh);
  }
  function drawMarker(cv, size) {
    var dpr = Math.min(2, global.devicePixelRatio || 1), W = Math.round(size * dpr);
    cv.width = W; cv.height = W;
    var ctx = cv.getContext('2d');
    ctx.fillStyle = 'rgba(127,127,127,.35)'; ctx.font = 'bold ' + Math.round(W * 0.4) + 'px system-ui,sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('?', W / 2, W / 2);
  }

  ui.pokeSprite = function (dex, o) {
    o = o || {};
    var p = REM.ent('pokemon', dex), n = p ? p.dex : Number(dex), size = o.size || 160;
    var cv = h('canvas.psprite', { width: size, height: size, role: 'img', 'aria-label': p ? ('Sprite de ' + p.name + (o.shiny ? ' variocolor' : '') + (o.back ? ' (espalda)' : '')) : 'Sprite', style: { width: size + 'px', height: size + 'px' } });
    var urls = n ? spriteUrl(n, o) : [GFX + 'Battlers/000.png'];
    var tryAt = function (i) {
      return frameOf(urls[i]).catch(function (err) {
        if (i + 1 < urls.length) return tryAt(i + 1);
        throw err;
      });
    };
    var ready = tryAt(0).then(function (frame) {
      drawFrame(cv, frame, size); cv.dataset.ready = '1'; return true;
    }, function (err) {
      drawMarker(cv, size); cv.dataset.ready = '0';
      REM.diag.brokenImages.push({ src: urls[0], kind: 'canvas', route: REM.state.route ? REM.state.route.hash : '' });
      return false;
    });
    cv.ready = ready; ui._pending.add(ready);
    ready.then(function () { ui._pending.delete(ready); });
    return cv;
  };
  ui.settle = function () {
    return Promise.all(Array.from(ui._pending));
  };

  /* ------------------------------------------------------------------ *
   * Badges de cambios REM y barras de estadísticas
   * ------------------------------------------------------------------ */
  ui.badge = function (text, kind, title) {
    return h('span.badge' + (kind ? '.badge--' + safeClass(kind) : ''), { title: title || null }, text);
  };
  ui.chip = function (text, o) {
    o = o || {};
    return h('span.chip' + (o.kind ? '.chip--' + safeClass(o.kind) : ''), { title: o.title || null }, text);
  };
  var DIFF_KIND = { 'Retipado': 'type', 'Stats': 'stats', 'Habilidades': 'ability', 'Evolución': 'evo', 'Learnset': 'moves' };
  var ABIL_STATUS = { Reworked: ['Reelaborada', 'rework'], Buffed: ['Mejorada', 'buff'], Kept: ['Mantenida', 'kept'], Untouched: ['Sin cambios', 'none'] };
  ui.ABIL_STATUS = ABIL_STATUS;
  ui.diffBadges = function (e) {
    var w = h('span.badges');
    if (!e) return w;
    var d = e.diff;
    if (e.dex != null) {                         // Pokémon
      var bs = (d && d.badges) || [];
      bs.forEach(function (b) { w.appendChild(ui.badge(b, DIFF_KIND[b] || 'mod', badgeTitle(b, e))); });
      if (d && d.changed && !bs.length) w.appendChild(ui.badge('Modificado', 'mod'));
    } else if (e.holders !== undefined || (e.status !== undefined && e.description !== undefined && e.power === undefined)) {      // Habilidad
      var st = ABIL_STATUS[e.status];
      if (st && e.status !== 'Untouched') w.appendChild(ui.badge(st[0], st[1]));
      else if (e.changed) w.appendChild(ui.badge('Modificada', 'mod'));
    } else if (e.power !== undefined || e.category !== undefined) {                                                          // Movimiento
      if (d && d.changed) w.appendChild(ui.badge('Cambiado', 'mod', d.fields && d.fields.length ? 'Campos: ' + d.fields.join(', ') : null));
    } else {                                                                                                                  // Objeto / otro
      if (e.isNew) w.appendChild(ui.badge('Nuevo', 'new'));
      else if (d && d.changed) w.appendChild(ui.badge('Modificado', 'mod', d.fields && d.fields.length ? 'Campos: ' + d.fields.join(', ') : null));
    }
    return w;
  };
  function badgeTitle(b, p) {
    var d = p.diff || {};
    if (b === 'Retipado' && d.types) return 'Antes: ' + (d.types.before || []).map(ui.typeName).join(' / ');
    if (b === 'Stats' && d.stats) return 'Δ BST ' + (d.stats.bst > 0 ? '+' : '') + d.stats.bst;
    if (b === 'Habilidades' && d.abilities) return 'Añade: ' + ((d.abilities.added || []).map(abName).join(', ') || '—');
    if (b === 'Learnset') return '+' + ((d.movesAdded || []).length) + ' / −' + ((d.movesRemoved || []).length) + ' movimientos';
    return null;
  }
  function abName(sym) { var a = REM.idx.abilityBySym[sym]; return a ? a.name : sym; }

  var STAT_ROWS = [['hp', 'PS'], ['atk', 'Ataque'], ['def', 'Defensa'], ['spa', 'At. Esp.'], ['spd', 'Def. Esp.'], ['spe', 'Velocidad']];
  ui.STAT_ROWS = STAT_ROWS;
  ui.statTier = function (v) { return v <= 40 ? 1 : v <= 60 ? 2 : v <= 80 ? 3 : v <= 100 ? 4 : v <= 130 ? 5 : 6; };
  ui.deltaEl = function (dlt, o) {
    o = o || {};
    if (dlt == null || isNaN(dlt)) return h('span.delta.delta--none', '');
    if (dlt === 0) return h('span.delta.delta--zero', { title: 'Igual que en el juego original' }, o.zero === false ? '' : '=');
    return h('span.delta' + (dlt > 0 ? '.delta--up' : '.delta--down'), { title: 'Frente al juego original (vanilla)' }, (dlt > 0 ? '+' : '−') + Math.abs(dlt));
  };
  ui.statBars = function (p) {
    var wrap = h('div.statbars', { role: 'table', 'aria-label': 'Estadísticas base' });
    if (!p || !p.stats) return wrap.appendChild(ui.empty('Sin datos')) && wrap;
    var base = p.baseline && p.baseline.stats, dd = p.diff && p.diff.stats;
    function delta(k) {
      if (dd && dd[k] != null) return dd[k];
      if (base && base[k] != null) return p.stats[k] - base[k];
      return null;
    }
    STAT_ROWS.forEach(function (r) {
      var k = r[0], v = p.stats[k], dl = delta(k);
      wrap.appendChild(h('div.statrow', { role: 'row' },
        h('span.statrow__label', { role: 'cell' }, r[1]),
        h('span.statrow__val', { role: 'cell' }, String(v)),
        h('span.statrow__bar', { role: 'cell', 'aria-hidden': 'true' },
          h('i.s' + ui.statTier(v), { style: { width: Math.min(100, v / 180 * 100) + '%' } })),
        h('span.statrow__delta', { role: 'cell' }, ui.deltaEl(dl))));
    });
    var bst = p.stats.bst != null ? p.stats.bst : REM.util.sum(STAT_ROWS.map(function (r) { return p.stats[r[0]]; }));
    var bd = delta('bst');
    wrap.appendChild(h('div.statrow.statrow--total', { role: 'row' },
      h('span.statrow__label', { role: 'cell' }, 'Total (BST)'),
      h('span.statrow__val', { role: 'cell' }, String(bst)),
      h('span.statrow__bar', { role: 'cell', 'aria-hidden': 'true' }, h('i.s' + (bst < 300 ? 1 : bst < 400 ? 2 : bst < 480 ? 3 : bst < 540 ? 4 : bst < 600 ? 5 : 6), { style: { width: Math.min(100, bst / 780 * 100) + '%' } })),
      h('span.statrow__delta', { role: 'cell' }, ui.deltaEl(bd))));
    return wrap;
  };

  /* ------------------------------------------------------------------ *
   * Bloques de maquetación
   * ------------------------------------------------------------------ */
  ui.empty = function (msg, o) {
    o = o || {};
    return h('div.empty', { role: 'note' }, h('span.empty__icon', { 'aria-hidden': 'true' }, o.icon || '∅'), h('span', msg == null ? 'Sin datos' : msg));
  };
  ui.spinner = function (msg) { return h('div.boot', { role: 'status' }, msg || 'Cargando…'); };
  ui.card = function (title, body) {
    var kids = Array.prototype.slice.call(arguments, 2);
    var head = title ? h('header.card__head', typeof title === 'object' && title.nodeType ? title : h('h2.card__title', title)) : null;
    return h('section.card', head, body, kids);
  };
  ui.section = function (title, subtitle) {
    var kids = Array.prototype.slice.call(arguments, 2);
    return h('section.sec', h('div.sec__head', h('h2', title), subtitle ? h('p.muted', subtitle) : null), kids);
  };
  ui.pageHeader = function (o) {
    o = o || {};
    var crumbs = o.crumbs && o.crumbs.length ? h('nav.crumbs', { 'aria-label': 'Migas de pan' }, o.crumbs.map(function (c, i) {
      return [i ? h('span.crumbs__sep', { 'aria-hidden': 'true' }, '›') : null, c.href ? h('a', { href: c.href }, c.label) : h('span', c.label)];
    })) : null;
    return h('header.pagehead', crumbs,
      (o.title || o.sub || o.lead || o.actions) ? h('div.pagehead__row',
        o.lead ? h('div.pagehead__lead', o.lead) : null,
        (o.title || o.sub || o.meta) ? h('div.pagehead__text', o.title ? h('h1', o.title) : null, o.sub ? h('p.pagehead__sub', o.sub) : null, o.meta ? h('div.pagehead__meta', o.meta) : null) : null,
        o.actions ? h('div.pagehead__actions', o.actions) : null) : null);
  };
  ui.stat = function (label, value, o) {
    o = o || {};
    var inner = [h('span.stat__value', value == null ? '—' : String(value)), h('span.stat__label', label), o.sub ? h('span.stat__sub', o.sub) : null];
    return o.href ? h('a.stat', { href: o.href, title: o.title || null }, inner) : h('div.stat', { title: o.title || null }, inner);
  };
  ui.kv = function (rows) {
    var dl = h('dl.kv');
    (rows || []).forEach(function (r) {
      if (!r || r[1] == null || r[1] === '' || (Array.isArray(r[1]) && !r[1].length)) return;
      dl.appendChild(h('dt', r[0])); dl.appendChild(h('dd', r[1]));
    });
    return dl;
  };
  ui.copyButton = function (text, label) {
    var b = h('button.btn.btn--sm', { type: 'button', title: 'Copiar al portapapeles', 'aria-label': 'Copiar «' + text + '»' }, label || 'Copiar');
    b.addEventListener('click', function () {
      REM.util.copy(text).then(function (ok) {
        ui.toast(ok ? 'Copiado: ' + text : 'No se pudo copiar', ok ? 'ok' : 'warn');
        var old = b.textContent; b.textContent = ok ? '¡Copiado!' : 'Error'; setTimeout(function () { b.textContent = old; }, 1400);
      });
    });
    return b;
  };
  ui.tabs = function (items, active, onSelect) {
    var nav = h('div.tabs', { role: 'tablist' });
    items.forEach(function (it) {
      var b = h('button.tab' + (it.id === active ? '.is-active' : ''), { type: 'button', role: 'tab', 'aria-selected': it.id === active ? 'true' : 'false' }, it.label);
      b.addEventListener('click', function () {
        Array.prototype.forEach.call(nav.children, function (x) { x.classList.remove('is-active'); x.setAttribute('aria-selected', 'false'); });
        b.classList.add('is-active'); b.setAttribute('aria-selected', 'true');
        if (onSelect) onSelect(it.id, it);
      });
      nav.appendChild(b);
    });
    return nav;
  };
  ui.select = function (label, options, value, onChange, o) {
    o = o || {};
    var sel = h('select.input', { 'aria-label': label });
    options.forEach(function (op) {
      var v = Array.isArray(op) ? op[0] : op, t = Array.isArray(op) ? op[1] : op;
      var oe = h('option', { value: String(v) }, t); if (String(v) === String(value)) oe.selected = true; sel.appendChild(oe);
    });
    sel.addEventListener('change', function () { onChange && onChange(sel.value, sel); });
    return h('label.field' + (o.cls ? '.' + o.cls : ''), h('span.field__label', label), sel);
  };
  ui.input = function (label, value, onInput, o) {
    o = o || {};
    var inp = h('input.input', { type: o.type || 'search', value: value || '', placeholder: o.placeholder || '', 'aria-label': label, autocomplete: 'off', spellcheck: 'false' });
    if (o.min != null) inp.min = o.min; if (o.max != null) inp.max = o.max; if (o.step != null) inp.step = o.step;
    var fire = o.debounce === 0 ? function () { onInput && onInput(inp.value, inp); } : REM.util.debounce(function () { onInput && onInput(inp.value, inp); }, o.debounce == null ? 140 : o.debounce);
    inp.addEventListener('input', fire);
    return o.bare ? inp : h('label.field' + (o.cls ? '.' + o.cls : ''), h('span.field__label', label), inp);
  };
  ui.check = function (label, checked, onChange, o) {
    var c = h('input', { type: 'checkbox' }); c.checked = !!checked;
    c.addEventListener('change', function () { onChange && onChange(c.checked, c); });
    return h('label.check' + (o && o.cls ? '.' + o.cls : ''), c, h('span', label));
  };

  var METHODS = {
    B: ['Poké Ball visible', 'Objeto visible sobre el mapa, dentro de una Poké Ball'],
    H: ['Objeto oculto', 'Escondido: se descubre inspeccionando el lugar o con el Buscaobjetos'],
    C: ['Cofre', 'Cofre o bulto que se abre con interacción'],
    N: ['Regalo de PNJ', 'Lo entrega un personaje no jugable'],
    E: ['Evento o misión', 'Recompensa de un evento de historia o una misión'],
    J: ['Botín de jefe o líder', 'Recompensa por vencer a un jefe, líder o combate importante'],
    P: ['Entrega especial', 'Entrega especial'],
    S: ['Tienda de stock único', 'Se compra en una tienda con existencias limitadas']
  };
  ui.METHODS = METHODS;
  ui.money = function (n) { return n == null ? '—' : '₽' + REM.num(n, 0); };
  ui.methodBadge = function (m) {
    var d = METHODS[m];
    return h('span.mbadge.m-' + safeClass(m), { title: d ? d[0] + ': ' + d[1] : String(m) }, String(m || '?'));
  };
  var RARITY = { COMMON: ['Común', 'common'], UNCOMMON: ['Poco común', 'uncommon'], RARE: ['Rara', 'rare'] };
  ui.rarityLabel = function (r) { return (RARITY[r] || [String(r || '—')])[0]; };
  ui.rarityBadge = function (r) {
    var d = RARITY[r] || [String(r || '—'), 'none'];
    return h('span.rbadge.r-' + d[1], d[0]);
  };

  /* ------------------------------------------------------------------ *
   * Toasts
   * ------------------------------------------------------------------ */
  ui.toast = function (msg, kind, ms) {
    var root = document.getElementById('toasts'); if (!root) return null;
    var t = h('div.toast.toast--' + safeClass(kind || 'info'), { role: 'status' },
      h('span.toast__icon', { 'aria-hidden': 'true' }, kind === 'ok' ? '✓' : kind === 'warn' ? '!' : kind === 'error' ? '✕' : 'i'), h('span', String(msg)));
    root.appendChild(t);
    while (root.children.length > 4) root.removeChild(root.firstChild);
    requestAnimationFrame(function () { t.classList.add('is-in'); });
    setTimeout(function () {
      t.classList.remove('is-in');
      setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, 300);
    }, ms || 4200);
    return t;
  };

  /* ------------------------------------------------------------------ *
   * Paginador
   * ------------------------------------------------------------------ */
  ui.pager = function (a, b, c, d) {
    var o = (a && typeof a === 'object') ? a : { total: a, page: b, pageSize: c, onPage: d };
    var total = o.total || 0, size = o.pageSize || 50, pages = Math.max(1, Math.ceil(total / size)), page = REM.util.clamp(o.page || 1, 1, pages);
    var nav = h('nav.pager', { 'aria-label': 'Paginación' });
    function go(p) { if (p >= 1 && p <= pages && p !== page && o.onPage) o.onPage(p); }
    function btn(label, p, dis, aria, active) {
      var bt = h('button.btn.btn--sm' + (active ? '.is-active' : ''), { type: 'button', disabled: dis, 'aria-label': aria || null, 'aria-current': active ? 'page' : null }, label);
      bt.addEventListener('click', function () { go(p); }); return bt;
    }
    nav.appendChild(btn('‹', page - 1, page <= 1, 'Página anterior'));
    var shown = {}; [1, 2, page - 1, page, page + 1, pages - 1, pages].forEach(function (p) { if (p >= 1 && p <= pages) shown[p] = 1; });
    var last = 0;
    Object.keys(shown).map(Number).sort(function (x, y) { return x - y; }).forEach(function (p) {
      if (p - last > 1) nav.appendChild(h('span.pager__gap', '…'));
      nav.appendChild(btn(String(p), p, false, 'Página ' + p, p === page)); last = p;
    });
    nav.appendChild(btn('›', page + 1, page >= pages, 'Página siguiente'));
    nav.appendChild(h('span.pager__info', REM.num(total) + ' elementos'));
    return nav;
  };

  /* ------------------------------------------------------------------ *
   * Tabla ordenable / filtrable con render incremental
   *   columns: [{key,label,render(row,i)->Node|string, sort:(row)->v | false,
   *              text:(row)->string, align:'right'|'center', className, width, title, defaultDir}]
   *   opts: {filter:true|false, placeholder, filterText(row), pageSize, sort:'key', dir:'asc'|'desc',
   *          rowClass(row), onRow(tr,row), empty, caption, toolbar:[Node], countLabel:[sing,plur],
   *          sticky:true, dense:true, id}
   * Devuelve un <div> con .setRows(rows) .refresh() .setFilter(str) .getRows() .count()
   * ------------------------------------------------------------------ */
  ui.table = function (columns, rows, opts) {
    opts = opts || {};
    var pageSize = opts.pageSize || 100, shown = 0;
    var tcache = new WeakMap();
    var state = { rows: rows || [], sortKey: opts.sort || null, dir: opts.dir || 'asc', q: '', view: [], texts: null };
    var cnt = opts.countLabel || ['fila', 'filas'];
    var wrap = h('div.tblx');
    var info = h('span.tblx__count', { 'aria-live': 'polite' });
    var filterInput = null;
    var tb = h('div.tblx__bar');
    if (opts.filter !== false) {
      filterInput = h('input.input.tblx__filter', { type: 'search', placeholder: opts.placeholder || 'Filtrar…', 'aria-label': opts.placeholder || 'Filtrar tabla', autocomplete: 'off', spellcheck: 'false' });
      filterInput.addEventListener('input', REM.util.debounce(function () { state.q = REM.norm(filterInput.value); apply(); }, 120));
      tb.appendChild(filterInput);
    }
    (opts.toolbar || []).forEach(function (n) { tb.appendChild(n); });
    tb.appendChild(info);
    if (tb.children.length > 1 || filterInput) wrap.appendChild(tb);

    var thead = h('thead'), tbody = h('tbody'), table = h('table.tbl' + (opts.dense ? '.tbl--dense' : '') + (opts.cls ? '.' + opts.cls : ''));
    if (opts.caption) table.appendChild(h('caption.sr-only', opts.caption));
    var trh = h('tr');
    columns.forEach(function (col) {
      var sortable = col.sort !== false && col.label != null && col.noSort !== true;
      var th = h('th', { scope: 'col', 'class': cls(col.className, col.align ? 'ta-' + col.align : '', sortable ? 'is-sortable' : ''), style: col.width ? { width: col.width } : null, title: col.title || null });
      if (sortable) {
        var bt = h('button.th-btn', { type: 'button' }, col.label, h('span.th-ind', { 'aria-hidden': 'true' }));
        bt.addEventListener('click', function () {
          if (state.sortKey === col.key) state.dir = state.dir === 'asc' ? 'desc' : 'asc';
          else { state.sortKey = col.key; state.dir = col.defaultDir || 'asc'; }
          apply();
        });
        th.appendChild(bt);
      } else th.appendChild(document.createTextNode(col.label || ''));
      col._th = th; trh.appendChild(th);
    });
    thead.appendChild(trh); table.appendChild(thead); table.appendChild(tbody);
    var scroller = h('div.tblx__scroll', table);
    var more = h('div.tblx__more');
    var sentinel = h('div.tblx__sentinel', { 'aria-hidden': 'true' });
    var empty = h('div.tblx__empty');
    wrap.appendChild(scroller); wrap.appendChild(empty); wrap.appendChild(sentinel); wrap.appendChild(more);

    function cellText(col, row) {
      if (col.text) return col.text(row);
      var v = col.key != null ? row[col.key] : null;
      return (typeof v === 'string' || typeof v === 'number') ? String(v) : '';
    }
    function rowText(row) {
      if (opts.filterText) return REM.norm(opts.filterText(row));
      var parts = []; columns.forEach(function (c) { parts.push(cellText(c, row)); });
      return REM.norm(parts.join(' '));
    }
    function sortVal(col, row) {
      if (typeof col.sort === 'function') return col.sort(row);
      return col.key != null ? row[col.key] : null;
    }
    function apply() {
      var list = state.rows;
      if (state.q) {
        var q = state.q, toks = q.split(' ').filter(Boolean);
        list = list.filter(function (r) {
          var t = tcache.get(r);
          if (t == null) { t = rowText(r); if (r && typeof r === 'object') tcache.set(r, t); }
          return toks.every(function (k) { return t.indexOf(k) >= 0; });
        });
      }
      var sc = columns.filter(function (c) { return c.key === state.sortKey; })[0];
      if (sc) {
        var sgn = state.dir === 'asc' ? 1 : -1;
        list = list.map(function (r, i) { return { r: r, v: sortVal(sc, r), i: i }; }).sort(function (a, b) {
          var av = a.v, bv = b.v, an = av == null || av === '', bn = bv == null || bv === '';
          if (an || bn) return an && bn ? a.i - b.i : an ? 1 : -1;
          var c = (typeof av === 'number' && typeof bv === 'number') ? av - bv : REM.collate(av, bv);
          return c ? c * sgn : a.i - b.i;
        }).map(function (x) { return x.r; });
      }
      columns.forEach(function (c) {
        if (!c._th) return;
        var on = c.key === state.sortKey;
        c._th.setAttribute('aria-sort', on ? (state.dir === 'asc' ? 'ascending' : 'descending') : 'none');
        c._th.classList.toggle('is-sorted', on);
        var ind = c._th.querySelector('.th-ind'); if (ind) ind.textContent = on ? (state.dir === 'asc' ? '▲' : '▼') : '';
      });
      state.view = list; shown = 0; REM.clear(tbody);
      var total = state.rows.length, n = list.length;
      info.textContent = (n === total ? REM.num(n) : REM.num(n) + ' de ' + REM.num(total)) + ' ' + (n === 1 ? cnt[0] : cnt[1]);
      REM.clear(empty);
      if (!n) empty.appendChild(ui.empty(state.q || (opts.hasFilters) ? 'Ningún resultado con estos filtros' : (opts.empty || 'Sin datos')));
      table.style.display = n ? '' : 'none';
      appendMore();
    }
    function appendMore() {
      var list = state.view, end = Math.min(list.length, shown + pageSize), f = document.createDocumentFragment();
      for (var i = shown; i < end; i++) f.appendChild(buildRow(list[i], i));
      tbody.appendChild(f); shown = end;
      REM.clear(more);
      if (shown < list.length) {
        var left = list.length - shown;
        var bt = h('button.btn', { type: 'button' }, 'Mostrar más (' + REM.num(left) + ' restantes)');
        bt.addEventListener('click', appendMore); more.appendChild(bt);
        observe();
      }
    }
    var io = null;
    function observe() {
      if (!('IntersectionObserver' in global) || eager()) return;
      if (!io) io = new IntersectionObserver(function (es) {
        if (es.some(function (e) { return e.isIntersecting; }) && shown < state.view.length) appendMore();
      }, { rootMargin: '600px 0px' });
      io.disconnect(); io.observe(sentinel);
    }
    function buildRow(row, i) {
      var tr = h('tr', { 'class': opts.rowClass ? opts.rowClass(row) : null });
      columns.forEach(function (col) {
        var td = h('td', { 'class': cls(col.className, col.align ? 'ta-' + col.align : '') });
        var v;
        try { v = col.render ? col.render(row, i) : (col.key != null ? row[col.key] : ''); } catch (e) { REM.fail('celda «' + col.key + '»', e); v = '—'; }
        if (v == null || v === '') td.appendChild(h('span.muted', '—')); else td.appendChild(v && v.nodeType ? v : document.createTextNode(String(v)));
        if (col.label) td.setAttribute('data-label', col.label);
        tr.appendChild(td);
      });
      if (opts.onRow) opts.onRow(tr, row);
      return tr;
    }
    wrap.setRows = function (r) { state.rows = r || []; apply(); };
    wrap.refresh = apply;
    wrap.setFilter = function (q) { state.q = REM.norm(q); if (filterInput) filterInput.value = q || ''; apply(); };
    wrap.getRows = function () { return state.view.slice(); };
    wrap.count = function () { return state.view.length; };
    wrap.sortBy = function (key, dir) { state.sortKey = key; state.dir = dir || 'asc'; apply(); };
    apply();
    return wrap;
  };

  /* ------------------------------------------------------------------ *
   * Shell: barra superior, subnavegación, tema, salud, pie
   * ------------------------------------------------------------------ */
  REM.nav = [
    { id: 'home', label: 'Inicio', icon: '🏠', href: '#/', match: [''] },
    { id: 'pokedex', label: 'Pokédex Maestra', icon: '📖', href: '#/pokedex', match: ['pokedex', 'pokemon'] },
    { id: 'moves', label: 'Movimientos y Habilidades', icon: '⚔️', href: '#/moves', match: ['moves', 'move', 'abilities', 'ability'],
      sub: [{ label: 'Movimientos', href: '#/moves', match: ['moves', 'move'] }, { label: 'Habilidades', href: '#/abilities', match: ['abilities', 'ability'] }] },
    { id: 'items', label: 'Objetos, MT y Tiendas', icon: '🎒', href: '#/items', match: ['items', 'item', 'tms', 'tm', 'shops'],
      sub: [{ label: 'Objetos', href: '#/items', match: ['items', 'item'] }, { label: 'MT', href: '#/tms', match: ['tms', 'tm'] },
        { label: 'Tiendas', href: '#/shops', match: ['shops'] }] },
    { id: 'world', label: 'Mapa y Atlas', icon: '🗺️', href: '#/map', match: ['map', 'atlas', 'location'],
      sub: [{ label: 'Mapa', href: '#/map', match: ['map'] }, { label: 'Atlas', href: '#/atlas', match: ['atlas', 'location'] }] },
  ];

  var shell = REM.shell = {};
  var els = {};
  var THEMES = [['auto', '🖥️', 'Tema: automático'], ['light', '☀️', 'Tema: claro'], ['dark', '🌙', 'Tema: oscuro']];

  function currentTheme() {
    var t = REM.util.store.get('rem-theme', 'auto'); return (t === 'light' || t === 'dark') ? t : 'auto';
  }
  function applyTheme(t) {
    var root = document.documentElement;
    if (t === 'light' || t === 'dark') root.setAttribute('data-theme', t); else root.removeAttribute('data-theme');
    REM.util.store.set('rem-theme', t);
    var d = THEMES.filter(function (x) { return x[0] === t; })[0] || THEMES[0];
    if (els.theme) { els.theme.textContent = d[1]; els.theme.title = d[2] + ' (clic para cambiar)'; els.theme.setAttribute('aria-label', d[2] + ', clic para cambiar'); }
  }
  shell.cycleTheme = function () {
    var cur = currentTheme(), i = THEMES.findIndex(function (x) { return x[0] === cur; });
    applyTheme(THEMES[(i + 1) % THEMES.length][0]);
  };

  function pokeballSvg() {
    return h('svg', { viewBox: '0 0 32 32', width: 26, height: 26, 'aria-hidden': 'true', focusable: 'false' },
      h('circle', { cx: 16, cy: 16, r: 14, fill: '#e5484d', stroke: 'currentColor', 'stroke-width': 2 }),
      h('path', { d: 'M2 16h28a14 14 0 0 1-28 0z', fill: '#f4f6fb', stroke: 'currentColor', 'stroke-width': 2 }),
      h('circle', { cx: 16, cy: 16, r: 5, fill: '#f4f6fb', stroke: 'currentColor', 'stroke-width': 2 }));
  }

  shell.init = function () {
    var top = document.getElementById('topbar'); if (!top) return;
    els.top = top; els.sub = document.getElementById('subnav'); els.foot = document.getElementById('footer');
    document.body.classList.toggle('ts-sprite', REM.util.store.get('rem-types', 'pill') === 'sprite');
    probeSheet(GFX + 'Pictures/types.png', 'types', null);
    probeSheet(GFX + 'Pictures/category.png', 'cat', 3);

    els.links = h('ul.nav__list');
    REM.nav.forEach(function (s) {
      var a = h('a.nav__link', { href: s.href, 'data-nav': s.id }, h('span.nav__icon', { 'aria-hidden': 'true' }, s.icon), h('span.nav__text', s.label));
      s.el = a; els.links.appendChild(h('li', a));
    });
    els.search = h('button.btn.searchbtn', { type: 'button', 'aria-label': 'Buscar en todo el Codex (Ctrl+K)', title: 'Buscar (Ctrl+K)' },
      h('span', { 'aria-hidden': 'true' }, '🔍'), h('span.searchbtn__text', 'Buscar…'), h('kbd', 'Ctrl K'));
    els.search.addEventListener('click', function () { REM.search.open(); });
    els.health = h('a.health.health--ok', { href: '#/warnings', title: 'Estado del PBS' }, h('i.health__dot', { 'aria-hidden': 'true' }), h('span.health__text', 'PBS'));
    els.warn = h('a.btn.warnbadge', { href: '#/warnings', title: 'Abrir el panel de avisos de sintaxis del PBS' }, '⚠️ Avisos de Sintaxis PBS (0)');
    els.reload = h('button.btn.btn--primary', { type: 'button', title: 'Releer los archivos PBS y reconstruir el modelo' }, '🔄 ', h('span.reload__text', 'Recargar PBS en Vivo'));
    els.reload.addEventListener('click', function () {
      if (els.reload.disabled) return;
      els.reload.disabled = true; els.reload.classList.add('is-busy');
      ui.toast('Recargando el PBS…', 'info', 1800);
      REM.api.reload().then(function (m) {
        var hh = m.meta.health || {};
        ui.toast('PBS recargado: ' + (hh.errors || 0) + ' errores, ' + (hh.warnings || 0) + ' avisos', hh.errors ? 'warn' : 'ok');
      }, function (e) { ui.toast('No se pudo recargar: ' + (e && e.message || e), 'error', 6000); })
        .then(function () { els.reload.disabled = false; els.reload.classList.remove('is-busy'); });
    });
    els.theme = h('button.btn.btn--icon', { type: 'button' }, '🖥️');
    els.theme.addEventListener('click', shell.cycleTheme);
    els.types = h('button.btn.btn--icon', { type: 'button', title: 'Alternar estilo de las etiquetas de tipo (moderno / sprites del juego)', 'aria-label': 'Alternar estilo de etiquetas de tipo' }, '🏷️');
    els.types.addEventListener('click', function () {
      var on = !document.body.classList.contains('ts-sprite');
      if (on && !ui.sheet.types.ok) { ui.toast('No se encontró types.png: se mantiene el estilo moderno', 'warn'); return; }
      document.body.classList.toggle('ts-sprite', on); REM.util.store.set('rem-types', on ? 'sprite' : 'pill');
    });

    REM.clear(top).appendChild(h('div.topbar__inner',
      h('a.brand', { href: '#/', 'aria-label': 'Pokémon REM Master Codex, ir al inicio' }, h('span.brand__logo', pokeballSvg()),
        h('span.brand__text', h('b', 'Pokémon REM'), h('small', 'Master Codex'))),
      h('nav.nav', { 'aria-label': 'Secciones principales' }, els.links),
      h('div.topbar__tools', els.search, els.health, els.warn, els.reload, els.types, els.theme)));
    applyTheme(currentTheme());
    renderFooter();
    shell.measure();
    if ('ResizeObserver' in global) {
      var ro = new ResizeObserver(function () { shell.measure(); });
      ro.observe(top); if (els.sub) ro.observe(els.sub);
    }
    global.addEventListener('resize', REM.util.debounce(function () { shell.measure(); }, 100));
    REM.on('model', function () { shell.updateHealth(); renderFooter(); });
    REM.on('route', shell.updateRoute);
    REM.on('poll', function () { renderFooter(); });
  };

  /* Mide la barra superior y la subnavegación para fijar cabeceras de tabla pegajosas. */
  shell.measure = function () {
    var root = document.documentElement.style;
    if (els.top) root.setProperty('--topbar-h', Math.round(els.top.getBoundingClientRect().height) + 'px');
    root.setProperty('--subnav-h', (els.sub && !els.sub.hidden) ? Math.round(els.sub.getBoundingClientRect().height) + 'px' : '0px');
  };

  shell.updateHealth = function () {
    var m = REM.state.model; if (!m || !els.health) return;
    var hh = m.meta.health || {}, n = (hh.errors || 0) + (hh.warnings || 0);
    var st = hh.errors ? 'error' : (hh.warnings ? 'warn' : (hh.status === 'error' ? 'error' : hh.status === 'warn' ? 'warn' : 'ok'));
    els.health.className = 'health health--' + st;
    els.health.querySelector('.health__text').textContent = st === 'ok' ? 'PBS en orden' : st === 'warn' ? 'PBS con avisos' : 'PBS con errores';
    els.health.title = (hh.errors || 0) + ' errores, ' + (hh.warnings || 0) + ' avisos' + (m.meta.source === 'bundle' ? ' · datos del bundle de respaldo' : '');
    els.warn.textContent = '⚠️ Avisos de Sintaxis PBS (' + n + ')';
    els.warn.className = 'btn warnbadge' + (hh.errors ? ' warnbadge--error' : n ? ' warnbadge--warn' : '');
  };

  function renderFooter() {
    if (!els.foot) return;
    var m = REM.state.model, c = m && m.meta.counts || {};
    var when = REM.state.lastLoad ? new Date(REM.state.lastLoad).toLocaleTimeString('es-ES') : '—';
    REM.clear(els.foot).appendChild(h('div.footer__inner',
      h('span', 'Pokémon REM Master Codex'),
      m ? h('span.muted', 'Fuente: ' + (m.meta.source === 'bundle' ? 'bundle de respaldo' : 'PBS en vivo') + ' · última lectura ' + when + (REM.state.online ? '' : ' · servidor sin respuesta')) : null,
      h('span.muted', 'Atajos: Ctrl+K buscar · g p Pokédex · g m Movimientos · g i Objetos'),
      m ? h('span.muted', REM.num(c.pokemon || 0) + ' Pokémon · ' + REM.num(c.moves || 0) + ' movimientos') : null));
  }

  shell.updateRoute = function (r) {
    if (!r) return;
    var prefix = r.prefix, active = null;
    REM.nav.forEach(function (s) {
      var on = s.match.indexOf(prefix) >= 0 && !(prefix === '' && s.id !== 'home');
      if (on) active = s;
      if (s.el) { s.el.classList.toggle('is-active', on); if (on) s.el.setAttribute('aria-current', 'page'); else s.el.removeAttribute('aria-current'); }
    });
    var sub = els.sub; if (!sub) return;
    REM.clear(sub);
    if (active && active.sub) {
      sub.hidden = false;
      var ul = h('ul.subnav__list');
      active.sub.forEach(function (x) {
        var on = x.match.indexOf(prefix) >= 0;
        ul.appendChild(h('li', h('a.subnav__link' + (on ? '.is-active' : ''), { href: x.href, 'aria-current': on ? 'page' : null }, x.label)));
      });
      sub.appendChild(h('div.subnav__inner', h('span.subnav__title', active.label), ul));
    } else sub.hidden = true;
    shell.measure();
  };

  /* Atajos "g + letra" (estilo GitHub) y cierre de overlays */
  var gPending = false, gTimer = null;
  document.addEventListener('keydown', function (ev) {
    var t = ev.target, tag = t && t.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || (t && t.isContentEditable)) return;
    if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
    if (gPending) {
      gPending = false; clearTimeout(gTimer);
      var map = { p: '#/pokedex', m: '#/moves', a: '#/abilities', i: '#/items', t: '#/tms', s: '#/shops', h: '#/', w: '#/warnings', l: '#/atlas' };
      if (map[ev.key]) { ev.preventDefault(); REM.router.go(map[ev.key]); }
      return;
    }
    if (ev.key === 'g') { gPending = true; clearTimeout(gTimer); gTimer = setTimeout(function () { gPending = false; }, 1200); }
    else if (ev.key === '/') { ev.preventDefault(); REM.search.open(); }
  });
})(window);
