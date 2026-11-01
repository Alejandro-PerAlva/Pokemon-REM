/* ==========================================================================
 * Arnés de autoprueba  (#/selftest)
 * Recorre todas las rutas registradas con REM.selftest.add(...), las renderiza
 * en el contenedor real y recoge excepciones, console.error, imágenes rotas,
 * enlaces rotos y la prueba de búsqueda. Resultado: <pre id="selftest-result">.
 * Lo usa el verificador con Chrome headless (--dump-dom).
 * ========================================================================== */
(function (global) {
  'use strict';
  var REM = global.REM, h = REM.h;
  var MAX_ROUTES = 700, CAP = 300;
  var run = null;        // {started, done, result, progress}

  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function cap(list, o) { if (list.length < CAP) list.push(o); }

  function waitImages(root) {
    var imgs = Array.prototype.slice.call(root.querySelectorAll('img'));
    var ps = imgs.filter(function (im) { return !im.complete; }).map(function (im) {
      im.loading = 'eager';
      return new Promise(function (res) { im.addEventListener('load', res, { once: true }); im.addEventListener('error', res, { once: true }); });
    });
    ps.push(REM.ui.settle());
    return Promise.race([Promise.all(ps), sleep(3000)]);
  }

  function progressBox() {
    var box = document.getElementById('selftest-progress');
    if (!box) { box = h('div#selftest-progress.selftest-progress', { role: 'status' }, 'Autoprueba…'); document.body.appendChild(box); }
    return box;
  }

  function searchTest(errors) {
    var checks = [['pika', 'pokemon'], ['hedor', 'ability'], ['poción', 'item'], ['iolita', 'location']], ok = true, detail = [];
    checks.forEach(function (c) {
      var r;
      try { r = REM.search.query(c[0]); } catch (e) { r = []; cap(errors, { route: 'search:' + c[0], message: String(e && e.message || e) }); }
      var hit = r.some(function (x) { return x.kind === c[1]; });
      detail.push({ q: c[0], kind: c[1], ok: hit, n: r.length, first: r[0] ? r[0].label : null });
      if (!hit) ok = false;
    });
    /* paleta Ctrl+K: se abre con una consulta, debe pintar resultados y cerrarse */
    try {
      REM.search.open('pika');
      return new Promise(function (resolve) {
        setTimeout(function () {
          var n = document.querySelectorAll('.pal .sw__item').length;
          detail.push({ q: 'paleta', ok: n > 0, n: n });
          if (!n) ok = false;
          REM.search.close();
          setTimeout(function () { resolve({ ok: ok, detail: detail }); }, 200);
        }, 300);
      });
    } catch (e) {
      cap(errors, { route: 'search:paleta', message: String(e && e.message || e) });
      return Promise.resolve({ ok: false, detail: detail });
    }
  }

  async function execute() {
    var t0 = Date.now(), container = REM.router.container();
    var all = REM.selftest.resolve();
    var skipped = 0;
    if (all.length > MAX_ROUTES) { var step = Math.ceil(all.length / MAX_ROUTES); skipped = all.length - Math.ceil(all.length / step); all = all.filter(function (x, i) { return i % step === 0; }); }
    var errors = [], brokenImages = [], brokenLinks = [], visited = {}, seenLinks = {}, nRoutes = 0;
    var box = progressBox();
    var diag = REM.diag, e0 = diag.errors.length, c0 = diag.consoleErrors.length, i0 = diag.brokenImages.length, d0 = diag.deadRefs.length;
    var linkCache = {};
    for (var i = 0; i < all.length; i++) {
      var it = all[i];
      box.textContent = 'Autoprueba ' + (i + 1) + '/' + all.length + ' · ' + it.hash;
      var res;
      try {
        res = await REM.router.visit(it.hash);
      } catch (e) { res = { ok: false, error: e }; }
      nRoutes++; visited[it.section] = (visited[it.section] || 0) + 1;
      if (!res || !res.ok) {
        cap(errors, { route: it.hash, section: it.section, message: res && res.error ? String(res.error && res.error.message || res.error) : (res && res.notFound ? 'Ruta no registrada' : 'La vista no se pudo renderizar') });
      }
      if (!container.firstChild || !container.textContent.trim()) cap(errors, { route: it.hash, section: it.section, message: 'Vista vacía' });
      await waitImages(container);
      /* imágenes rotas en el DOM */
      Array.prototype.forEach.call(container.querySelectorAll('img'), function (im) {
        if (im.complete && im.naturalWidth === 0) cap(brokenImages, { route: it.hash, src: im.getAttribute('src') });
      });
      /* enlaces internos */
      Array.prototype.forEach.call(container.querySelectorAll('a[href^="#/"]'), function (a) {
        var hr = a.getAttribute('href');
        if (!(hr in linkCache)) { try { linkCache[hr] = REM.router.exists(hr); } catch (e) { linkCache[hr] = false; } }
        if (!linkCache[hr]) { var key = hr + '|' + it.hash; if (!seenLinks[key]) { seenLinks[key] = 1; cap(brokenLinks, { route: it.hash, href: hr }); } }
      });
      await sleep(0);
    }
    /* navegación superior y subnavegación también deben resolver */
    Array.prototype.forEach.call(document.querySelectorAll('#topbar a[href^="#/"], #subnav a[href^="#/"]'), function (a) {
      var hr = a.getAttribute('href'); if (!REM.router.exists(hr)) cap(brokenLinks, { route: '(barra de navegación)', href: hr });
    });
    (REM.nav || []).forEach(function (s) { (s.sub || []).concat([s]).forEach(function (x) { if (!REM.router.exists(x.href)) cap(brokenLinks, { route: '(navegación)', href: x.href }); }); });

    var st = await searchTest(errors);
    /* errores acumulados por el núcleo durante la ejecución */
    diag.errors.slice(e0).forEach(function (e) { cap(errors, { route: e.ctx, message: e.message }); });
    diag.brokenImages.slice(i0).forEach(function (b) { cap(brokenImages, { route: b.route, src: b.src, kind: b.kind || 'img' }); });
    var consoleErrors = diag.consoleErrors.slice(c0).slice(0, CAP);
    var sections = Object.keys(visited);
    var result = {
      routes: nRoutes, sections: sections, errors: errors, consoleErrors: consoleErrors, brokenImages: brokenImages, brokenLinks: brokenLinks,
      searchOk: st.ok, elapsedMs: Date.now() - t0,
      searchDetail: st.detail, deadRefs: diag.deadRefs.slice(d0, d0 + 60), skipped: skipped,
      perSection: visited, registered: REM.selftest.sections.map(function (s) { return s.section; })
    };
    return result;
  }

  function renderSummary(el) {
    var r = run.result;
    if (!run.done) {
      el.appendChild(h('section.card', h('h1', 'Autoprueba en curso…'), h('p.muted', 'Se recorren todas las rutas registradas. No cierres esta pestaña.')));
      return;
    }
    var bad = r.errors.length + r.consoleErrors.length + r.brokenImages.length + r.brokenLinks.length + (r.searchOk ? 0 : 1);
    el.appendChild(h('section.card', h('h1', bad ? 'Autoprueba: hay problemas' : 'Autoprueba superada'),
      h('p', h('b', String(r.routes)), ' rutas en ', h('b', String(r.sections.length)), ' secciones · ', Math.round(r.elapsedMs / 100) / 10 + ' s'),
      REM.ui.kv([['Excepciones', String(r.errors.length)], ['console.error', String(r.consoleErrors.length)], ['Imágenes rotas', String(r.brokenImages.length)],
        ['Enlaces rotos', String(r.brokenLinks.length)], ['Búsqueda', r.searchOk ? 'correcta' : 'FALLA'], ['Referencias muertas (informativo)', String(r.deadRefs.length)]])));
    el.appendChild(h('pre#selftest-result', JSON.stringify(r)));
  }

  REM.router.register('selftest', {
    title: 'Autoprueba',
    render: function (el) {
      if (!run) {
        run = { started: true, done: false, result: null };
        setTimeout(function () {
          execute().then(function (r) { run.result = r; run.done = true; var b = document.getElementById('selftest-progress'); if (b) b.remove(); return REM.router.visit('#/selftest'); },
            function (e) {
              run.done = true; run.result = { routes: 0, sections: [], errors: [{ route: 'selftest', message: String(e && e.message || e) }], consoleErrors: [], brokenImages: [], brokenLinks: [], searchOk: false, elapsedMs: 0 };
              var b = document.getElementById('selftest-progress'); if (b) b.remove();
              return REM.router.visit('#/selftest');
            });
        }, 30);
      }
      renderSummary(el);
    }
  });
})(window);
