/* Pokémon REM Codex (móvil): arranque instantáneo desde el bundle/cache; descarga de GitHub SOLO al pulsar «Actualizar PBS». */
(function (global) {
  'use strict';
  var REM = global.REM, busy = false;
  function toast(m, k) { try { REM.ui.toast(m, k || 'info', 3500); } catch (e) { /* ok */ } }
  function text(url) { return fetch(url, { cache: 'no-store' }).then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.text(); }); }

  function refresh() {
    if (busy) return Promise.reject(new Error('Ya hay una actualización en curso'));
    busy = true;
    toast('Descargando PBS de GitHub…');
    return text('/pbs/_list').then(function (l) { return JSON.parse(l); }).then(function (list) {
      var files = {}, got = 0, i = 0;
      function next() {
        var chunk = list.slice(i, i + 6); i += 6;
        if (!chunk.length) return Promise.resolve();
        return Promise.all(chunk.map(function (n) {
          return text('/pbs/' + encodeURIComponent(n)).then(function (t) { files[n] = global.REM_PBS.clean(t); got++; }, function () { /* archivo no disponible */ });
        })).then(next);
      }
      return next().then(function () {
        if (!got) throw new Error('Sin conexión: no se pudo descargar el PBS');
        return text('/data/model.json');
      }).then(function (base) {
        var r = global.REM_PBS.apply(JSON.parse(base), files), m = r.model;
        m.warnings = []; m.files = []; m.meta.health = { status: 'ok', errors: 0, warnings: 0 };
        global.AndroidBridge.saveModel(JSON.stringify(m));
        try { localStorage.setItem('rem-updated', new Date().toISOString()); } catch (e) { /* ok */ }
        return REM.api.load({ preserve: true }).then(function () { toast('PBS actualizado (' + r.notes.join(', ') + ')', 'ok'); return m; });
      });
    }).then(function (m) { busy = false; return m; }, function (e) { busy = false; toast('No se pudo actualizar: ' + (e && e.message), 'error'); throw e; });
  }
  REM.api.reload = refresh;
  REM.api.poll = function () { };
  REM.mobile = { refresh: refresh };

  /* Barra de navegación inferior */
  var TABS = [['📖', 'Pokédex', '#/pokedex', ['pokedex', 'pokemon']], ['⚔️', 'Mov./Hab.', '#/moves', ['moves', 'move', 'abilities', 'ability']],
    ['🎒', 'Objetos/MT', '#/items', ['items', 'item', 'tms', 'tm', 'shops']], ['🧭', 'Rutas', '#/atlas', ['atlas', 'location']], ['🗺️', 'Mapa', '#/map', ['map']]];
  var bar = document.createElement('nav'); bar.className = 'bnav'; bar.setAttribute('aria-label', 'Secciones');
  TABS.forEach(function (t) {
    var a = document.createElement('a'); a.href = t[2]; a.innerHTML = '<span class="bnav__i">' + t[0] + '</span><span class="bnav__t">' + t[1] + '</span>'; a._m = t[3]; bar.appendChild(a);
  });
  document.body.appendChild(bar);
  function mark() {
    var seg = (location.hash || '#/').replace(/^#\//, '').split(/[/?]/)[0];
    [].forEach.call(bar.children, function (a) { a.classList.toggle('is-on', a._m.indexOf(seg) >= 0); });
  }
  global.addEventListener('hashchange', mark); mark();
  /* Botón de actualizar: texto claro */
  var t = setInterval(function () {
    var b = document.querySelector('.reload__text'); if (b) { b.textContent = 'Actualizar PBS'; clearInterval(t); }
  }, 300);
})(window);
