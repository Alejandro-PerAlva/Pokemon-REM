/* ==========================================================================
 * Vista Avisos de Sintaxis PBS  (#/warnings)
 * ========================================================================== */
(function (global) {
  'use strict';
  var REM = global.REM, h = REM.h, ui = REM.ui;

  var SEV = { error: ['Error', 'err', 0], warn: ['Aviso', 'warn', 1], info: ['Info', 'info', 2] };
  var CODE_ES = {
    UNKNOWN_TYPE: 'Tipo desconocido', UNKNOWN_MOVE: 'Movimiento desconocido', UNKNOWN_ABILITY: 'Habilidad desconocida', UNKNOWN_ITEM: 'Objeto desconocido',
    UNKNOWN_SPECIES: 'Especie desconocida', UNKNOWN_LOCATION: 'Ubicación desconocida', BAD_LINE: 'Línea mal formada', BAD_NUMBER: 'Número inválido',
    DUPLICATE_KEY: 'Clave duplicada', MISSING_FIELD: 'Campo ausente', ENCODING: 'Codificación', FILE_MISSING: 'Archivo ausente'
  };
  var WF = { sev: '', file: '' };

  function fmtSize(n) {
    if (n == null) return '—';
    if (n < 1024) return n + ' B'; if (n < 1048576) return REM.num(n / 1024, 1) + ' KB'; return REM.num(n / 1048576, 2) + ' MB';
  }
  function fmtTime(t) {
    if (!t) return '—';
    var d = new Date(Number(t) * (t < 1e11 ? 1000 : 1)); return isNaN(d) ? '—' : d.toLocaleString('es-ES');
  }

  function fileCard(f, onPick) {
    var bad = f.exists === false, st = bad ? 'err' : f.errors ? 'err' : f.warnings ? 'warn' : 'ok';
    var c = h('button.filecard.filecard--' + st, { type: 'button', title: 'Filtrar la tabla por ' + f.name, 'aria-label': 'Filtrar por ' + f.name },
      h('span.filecard__name', f.name),
      h('span.filecard__status', bad ? 'No existe' : f.errors ? f.errors + ' errores' : f.warnings ? f.warnings + ' avisos' : 'Sin incidencias'),
      h('span.filecard__meta', bad ? '' : fmtSize(f.size) + ' · ' + REM.num(f.lines || 0) + ' líneas'),
      h('span.filecard__meta', bad ? '' : fmtTime(f.mtime)),
      (f.errors || f.warnings) ? h('span.filecard__counts', f.errors ? h('b.err', f.errors + ' E') : null, f.warnings ? h('b.warn', f.warnings + ' A') : null) : null);
    c.addEventListener('click', function () { onPick(f.name); });
    return c;
  }

  function render(el) {
    var m = REM.state.model, warns = m.warnings || [], files = m.files || [];
    var hh = m.meta.health || {};
    var nE = hh.errors != null ? hh.errors : warns.filter(function (w) { return w.severity === 'error'; }).length;
    var nW = hh.warnings != null ? hh.warnings : warns.filter(function (w) { return w.severity === 'warn'; }).length;
    var st = nE ? 'error' : nW ? 'warn' : 'ok';

    el.appendChild(ui.pageHeader({ title: '⚠️ Panel de Avisos de Sintaxis PBS',
      sub: 'Los archivos del PBS se editan a mano. Aquí aparece cualquier línea que el lector no entienda, con sugerencias de corrección. Se actualiza solo al guardar un archivo.',
      actions: [h('button.btn.btn--primary', { type: 'button', onclick: function (ev) { var b = ev.currentTarget; b.disabled = true; REM.api.reload().then(function () { ui.toast('PBS recargado', 'ok'); }, function (e) { ui.toast('No se pudo recargar: ' + (e && e.message), 'error'); }).then(function () { b.disabled = false; }); } }, '🔄 Recargar PBS en Vivo')] }));

    /* resumen de salud */
    el.appendChild(h('section.card.warn-summary.warn-summary--' + st, { 'aria-label': 'Resumen de salud del PBS' },
      h('i.health__dot', { 'aria-hidden': 'true' }),
      h('div', h('h2', st === 'ok' ? 'Todo en orden' : st === 'warn' ? 'El PBS se lee con avisos' : 'El PBS tiene errores'),
        h('p.muted', st === 'ok' ? 'No se ha detectado ningún problema de sintaxis en ' + files.length + ' archivos.' : nE + ' errores y ' + nW + ' avisos en ' + files.filter(function (f) { return f.errors || f.warnings; }).length + ' archivos.')),
      h('div.warn-summary__nums', ui.stat('Errores', nE), ui.stat('Avisos', nW), ui.stat('Archivos', files.length || '—'))));

    if (m.meta.source === 'bundle') el.appendChild(h('p.callout.callout--warn', 'Estás viendo datos del bundle de respaldo: el servidor no ha podido leer el PBS en vivo.'));

    /* tarjetas por archivo */
    var tableHost = h('div');
    if (files.length) {
      var grid = h('div.filecards');
      files.slice().sort(function (a, b) { return ((b.errors || 0) * 1000 + (b.warnings || 0)) - ((a.errors || 0) * 1000 + (a.warnings || 0)) || REM.collate(a.name, b.name); })
        .forEach(function (f) { grid.appendChild(fileCard(f, function (name) { WF.file = WF.file === name ? '' : name; drawTable(); window.scrollTo({ top: tableHost.getBoundingClientRect().top + window.scrollY - 140, behavior: 'smooth' }); })); });
      el.appendChild(ui.section('Archivos leídos', REM.num(files.length) + ' archivos. Pulsa una tarjeta para filtrar la tabla.', grid));
    }

    /* tabla de avisos */
    el.appendChild(ui.section('Detalle de avisos', null, tableHost));
    function drawTable() {
      REM.clear(tableHost);
      if (!warns.length) {
        tableHost.appendChild(h('div.allok', h('span.allok__icon', { 'aria-hidden': 'true' }, '✅'), h('div', h('b', 'Todo en orden'), h('p.muted', 'El PBS no tiene avisos de sintaxis. Si editas un archivo, esta página se actualizará sola.'))));
        return;
      }
      var fileNames = Array.from(new Set(warns.map(function (w) { return w.file; }).concat(files.map(function (f) { return f.name; })))).sort();
      var cols = [
        { key: 'severity', label: 'Gravedad', sort: function (w) { return (SEV[w.severity] || [0, 0, 9])[2]; }, render: function (w) { var s = SEV[w.severity] || [w.severity, 'info']; return h('span.chip.chip--' + s[1], s[0]); } },
        { key: 'file', label: 'Archivo', render: function (w) { return h('code', w.file || '—'); } },
        { key: 'line', label: 'Línea', align: 'right', render: function (w) { return w.line != null ? String(w.line) : '—'; } },
        { key: 'code', label: 'Tipo', sort: function (w) { return w.code; }, render: function (w) { return h('span.small', { title: w.code }, CODE_ES[w.code] || w.code || '—'); } },
        { key: 'text', label: 'Texto original', sort: false, className: 'td-wide', render: function (w) { return w.text ? h('code.wtext', w.text) : null; } },
        { key: 'message', label: 'Mensaje', sort: false, className: 'td-wide', render: function (w) { return w.message || '—'; } },
        { key: 'suggestion', label: '¿Quisiste decir…?', sort: function (w) { return w.suggestion; }, render: function (w) { return w.suggestion ? h('span.suggest', h('b', w.suggestion), ui.copyButton(w.suggestion)) : null; } }
      ];
      var tbl;
      function rows() { return warns.filter(function (w) { return (!WF.sev || w.severity === WF.sev) && (!WF.file || w.file === WF.file); }); }
      function upd() { tbl.setRows(rows()); }
      tbl = ui.table(cols, rows(), {
        placeholder: 'Buscar en los avisos…', pageSize: 100, sort: 'severity', dense: true, countLabel: ['aviso', 'avisos'], hasFilters: true,
        filterText: function (w) { return [w.file, w.code, w.message, w.text, w.suggestion].join(' '); },
        toolbar: [
          ui.select('Gravedad', [['', 'Todas'], ['error', 'Errores'], ['warn', 'Avisos'], ['info', 'Información']], WF.sev, function (v) { WF.sev = v; upd(); }),
          ui.select('Archivo', [['', 'Todos']].concat(fileNames.map(function (n) { return [n, n]; })), WF.file, function (v) { WF.file = v; upd(); })
        ]
      });
      tableHost.appendChild(tbl);
    }
    drawTable();
  }

  REM.router.register('warnings', { title: 'Avisos de Sintaxis PBS', render: render });
  REM.selftest.add('warnings', ['#/warnings']);
})(window);
