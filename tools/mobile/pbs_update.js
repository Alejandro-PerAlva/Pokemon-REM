/* Actualizador ligero: parsea en JS los .txt oficiales de PBS/ y los aplica sobre el modelo base (bundle).
   Quita BOM, normaliza saltos de línea y NO muestra avisos de sintaxis. */
(function (global) {
  'use strict';
  function clean(t) { return String(t).replace(/^﻿/, '').replace(/\r\n?/g, '\n'); }
  function unq(s) { s = s.trim(); return (s.length > 1 && s[0] === '"' && s[s.length - 1] === '"') ? s.slice(1, -1).replace(/""/g, '"') : s; }
  function csv(line) {
    var out = [], cur = '', q = false;
    for (var i = 0; i < line.length; i++) {
      var c = line[i];
      if (c === '"') { q = !q; cur += c; } else if (c === ',' && !q) { out.push(cur); cur = ''; } else cur += c;
    }
    out.push(cur); return out.map(unq);
  }
  function csvLines(txt) { return clean(txt).split('\n').filter(function (l) { return l && l[0] !== '#' && /^\d/.test(l); }).map(csv); }
  function sections(txt) {
    var res = [], cur = null;
    clean(txt).split('\n').forEach(function (l) {
      if (!l || l[0] === '#') return;
      var m = l.match(/^\[(.+)\]\s*$/);
      if (m) { cur = { id: m[1], kv: {}, lines: [] }; res.push(cur); return; }
      if (!cur) return;
      var i = l.indexOf('=');
      if (i > 0) cur.kv[l.slice(0, i).trim()] = l.slice(i + 1).trim(); else cur.lines.push(l.trim());
    });
    return res;
  }
  var NUM = function (v, d) { var n = Number(v); return isFinite(n) ? n : d; };

  function evoText(method, param, items) {
    var nm = function (s) { var it = items[s]; return it ? it.name : s; };
    switch (method) {
      case 'Level': return 'Nivel ' + param;
      case 'LevelMale': return 'Nivel ' + param + ' (macho)';
      case 'LevelFemale': return 'Nivel ' + param + ' (hembra)';
      case 'AttackGreater': return 'Nivel ' + param + ' (Ataque > Defensa)';
      case 'DefenseGreater': return 'Nivel ' + param + ' (Defensa > Ataque)';
      case 'AtkDefEqual': return 'Nivel ' + param + ' (Ataque = Defensa)';
      case 'Silcoon': return 'Nivel ' + param + ' (aleatorio, rama Silcoon)';
      case 'Cascoon': return 'Nivel ' + param + ' (aleatorio, rama Cascoon)';
      case 'Item': return nm(param);
      case 'ItemMale': return nm(param) + ' (macho)';
      case 'ItemFemale': return nm(param) + ' (hembra)';
      case 'Happiness': return 'Felicidad';
      case 'HappinessDay': return 'Felicidad (de día)';
      case 'HappinessNight': return 'Felicidad (de noche)';
      case 'Trade': return 'Intercambio';
      case 'TradeItem': return 'Intercambio con ' + nm(param);
      case 'HasMove': return 'Conociendo ' + param;
      case 'HoldItem': return 'Con ' + nm(param) + ' equipado';
      case 'DayHoldItem': return 'Con ' + nm(param) + ' (de día)';
      case 'NightHoldItem': return 'Con ' + nm(param) + ' (de noche)';
      default: return method + (param ? ' ' + param : '');
    }
  }

  function apply(model, files) {
    var F = function (n) { return files[n] != null ? files[n] : null; };
    var bySym = function (arr) { var o = {}; arr.forEach(function (x) { o[x.sym] = x; }); return o; };
    var notes = [];

    if (F('moves.txt')) {
      var mv = bySym(model.moves), n = 0;
      csvLines(F('moves.txt')).forEach(function (c) {
        if (c.length < 13) return;
        var m = mv[c[1]]; if (!m) { m = { id: NUM(c[0]), sym: c[1], learnedBy: [], tmLearners: [], eggBy: [], tm: null, baseline: null, diff: null }; model.moves.push(m); mv[c[1]] = m; }
        m.id = NUM(c[0]); m.name = c[2]; m.fcode = c[3]; m.power = NUM(c[4], 0); m.type = c[5]; m.category = c[6];
        m.accuracy = NUM(c[7], 0); m.pp = NUM(c[8], 0); m.effectChance = NUM(c[9], 0); m.target = c[10]; m.priority = NUM(c[11], 0); m.flags = c[12]; m.description = c.slice(13).join(',');
        n++;
      }); notes.push(n + ' movimientos');
    }
    if (F('abilities.txt')) {
      var ab = bySym(model.abilities), n2 = 0;
      csvLines(F('abilities.txt')).forEach(function (c) {
        if (c.length < 4) return;
        var a = ab[c[1]]; if (!a) { a = { id: NUM(c[0]), sym: c[1], holders: [], baseline: null, status: null, note: null, notes: [], changed: false }; model.abilities.push(a); ab[c[1]] = a; }
        a.id = NUM(c[0]); a.name = c[2]; a.description = c.slice(3).join(',');
        if (a.baseline && a.baseline.description != null) a.changed = a.baseline.description !== a.description;
        n2++;
      }); notes.push(n2 + ' habilidades');
    }
    var itemBy = bySym(model.items);
    if (F('items.txt')) {
      var n3 = 0, pocketNames = {};
      model.items.forEach(function (i) { pocketNames[i.pocket] = i.pocketName; });
      csvLines(F('items.txt')).forEach(function (c) {
        if (c.length < 10) return;
        var it = itemBy[c[1]]; if (!it) { it = { sym: c[1], where: [], shops: [], heldBy: [], berry: null, baseline: null, diff: null, isNew: true, tm: null }; model.items.push(it); itemBy[c[1]] = it; }
        it.id = NUM(c[0]); it.name = c[2]; it.plural = c[3]; it.pocket = NUM(c[4]); it.pocketName = pocketNames[it.pocket] || it.pocketName || ''; it.price = NUM(c[5], 0);
        it.description = c[6]; it.fieldUse = NUM(c[7], 0); it.battleUse = NUM(c[8], 0); it.special = NUM(c[9], 0); it.move = c[10] || null;
        it.icon = 'Icons/item' + ('00' + it.id).slice(-3) + '.png'; n3++;
      }); notes.push(n3 + ' objetos');
    }
    var pk = {}, symDex = {};
    model.pokemon.forEach(function (p) { pk[p.dex] = p; symDex[p.sym] = p.dex; });
    if (F('pokemon.txt')) {
      var n4 = 0;
      sections(F('pokemon.txt')).forEach(function (s) {
        var dex = NUM(s.id, 0), p = pk[dex]; if (!p || dex > 721) return;
        var k = s.kv;
        if (k.Name) p.name = k.Name;
        if (k.InternalName) { p.sym = k.InternalName; symDex[p.sym] = dex; }
        p.types = [k.Type1].concat(k.Type2 && k.Type2 !== k.Type1 ? [k.Type2] : []).filter(Boolean);
        if (k.BaseStats) {
          var b = k.BaseStats.split(',').map(Number);
          p.stats = { hp: b[0], atk: b[1], def: b[2], spe: b[3], spa: b[4], spd: b[5], bst: b.reduce(function (x, y) { return x + y; }, 0) };
        }
        if (k.Abilities) p.abilities = k.Abilities.split(',').filter(Boolean);
        p.hiddenAbilities = k.HiddenAbility ? k.HiddenAbility.split(',').filter(Boolean) : [];
        if (k.Moves) { var a = k.Moves.split(','), ls = []; for (var i = 0; i + 1 < a.length; i += 2) ls.push({ lv: NUM(a[i], 1), move: a[i + 1] }); p.learnset = ls; }
        p.eggMoves = k.EggMoves ? k.EggMoves.split(',').filter(Boolean) : [];
        if (k.Height) p.height = NUM(k.Height, p.height);
        if (k.Weight) p.weight = NUM(k.Weight, p.weight);
        if (k.Kind) p.kind = k.Kind;
        if (k.Pokedex) p.pokedex = k.Pokedex;
        if (k.Rareness) p.catchRate = NUM(k.Rareness, p.catchRate);
        if (k.BaseEXP) p.baseExp = NUM(k.BaseEXP, p.baseExp);
        p._evo = k.Evolutions || ''; n4++;
      });
      model.pokemon.forEach(function (p) {
        if (p._evo === undefined) return;
        var ev = [], a = p._evo.split(',').filter(Boolean);
        for (var i = 0; i + 1 < a.length; i += 3) {
          var to = symDex[a[i]]; if (!to) continue;
          var item = /Item|Stone/.test(a[i + 1]) ? a[i + 2] : null;
          ev.push({ to: to, sym: a[i], method: a[i + 1], param: a[i + 2] || '', text: evoText(a[i + 1], a[i + 2] || '', itemBy), item: item });
        }
        p.evolutions = ev; delete p._evo;
      });
      model.pokemon.forEach(function (p) { p.evolvesFrom = null; });
      model.pokemon.forEach(function (p) { p.evolutions.forEach(function (e) { var t = pk[e.to]; if (t) t.evolvesFrom = { from: p.dex, method: e.method, param: e.param, text: e.text, item: e.item }; }); });
      notes.push(n4 + ' Pokémon');
    }
    var tmByMove = {}; model.tms.forEach(function (t) { tmByMove[t.move] = t; });
    if (F('tm.txt')) {
      model.tms.forEach(function (t) { t.learners = []; });
      sections(F('tm.txt')).forEach(function (s) {
        var t = tmByMove[s.id]; if (!t) return;
        var list = []; s.lines.join(',').split(',').forEach(function (x) { x = x.trim(); if (x && symDex[x]) list.push(symDex[x]); });
        t.learners = list.sort(function (a, b) { return a - b; });
      });
      model.pokemon.forEach(function (p) { p.tms = []; });
      model.tms.forEach(function (t) { t.learners.forEach(function (d) { if (pk[d]) pk[d].tms.push(t.number); }); });
      notes.push(model.tms.length + ' MT');
    }
    model.tms.forEach(function (t) { var it = itemBy[t.sym]; if (it) { t.price = it.price; } });
    var mvIdx = bySym(model.moves), abIdx = bySym(model.abilities);
    model.moves.forEach(function (m) { m.learnedBy = []; m.tmLearners = []; m.eggBy = []; });
    model.abilities.forEach(function (a) { a.holders = []; });
    model.pokemon.forEach(function (p) {
      p.learnset.forEach(function (l) { var m = mvIdx[l.move]; if (m) m.learnedBy.push({ dex: p.dex, lv: l.lv }); });
      p.eggMoves.forEach(function (e) { var m = mvIdx[e]; if (m) m.eggBy.push(p.dex); });
      p.abilities.concat(p.hiddenAbilities).forEach(function (s) { var a = abIdx[s]; if (a && a.holders.indexOf(p.dex) < 0) a.holders.push(p.dex); });
    });
    model.tms.forEach(function (t) { var m = mvIdx[t.move]; if (m) { m.tm = t.number; m.tmLearners = t.learners.slice(); } });
    model.meta = model.meta || {}; model.meta.updatedAt = new Date().toISOString(); model.meta.updatedFrom = 'github';
    return { model: model, notes: notes };
  }
  global.REM_PBS = { apply: apply, clean: clean, csv: csv, sections: sections };
})(typeof window !== 'undefined' ? window : globalThis);
