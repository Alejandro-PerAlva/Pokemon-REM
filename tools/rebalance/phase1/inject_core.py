#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_core.py - Pokemon REM, fase 1: inyeccion de los Volumenes 1-5 y 9 en los archivos OFICIALES de PBS/.

Agente `pbs-core`. Contrato: tools/codex/SPEC.md (secciones 0, 3 y 6).

* LEE SIEMPRE de  ROOT/PBS_backup_original/  (copia intacta del PBS vanilla) y de  ROOT/docs/rebalance/
  (proposed_*.txt, 9_Items_and_Economy_Master_Guide.md).
* ESCRIBE SOLO en  ROOT/PBS/  (o en --out DIR) estos 15 archivos, en UTF-8 con BOM y CRLF:
      abilities.txt  moves.txt  items.txt  pokemon.txt  tm.txt  berryplants.txt
      btpokemon.txt  fancycuppm.txt  fancycupsinglepm.txt  littlecuppm.txt  pikacuppm.txt  pokecuppm.txt
  (los seis ultimos solo reciben la sustitucion de objetos podados).
* Es idempotente: el resultado depende solo de las entradas, nunca del contenido previo de PBS/.
* NO toca Data/, PBS_backup_original/, PBS/rem_*.txt, PBS/encounters.txt ni PBS/~$okemon.txt.

Uso:
    python3 tools/rebalance/phase1/inject_core.py [--out DIR] [--dry-run] [--report FILE.json] [--no-verify] [--no-check]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]            # tools/rebalance/phase1 -> ROOT
SRC = ROOT / "PBS_backup_original"
DST = ROOT / "PBS"
DOCS = ROOT / "docs" / "rebalance"

PROPOSED = {
    "items": DOCS / "proposed_items.txt",
    "moves": DOCS / "proposed_moves.txt",
    "pokemon": DOCS / "proposed_pokemon.txt",
    "learnsets": DOCS / "proposed_learnsets.txt",
    "tm": DOCS / "proposed_tm.txt",
    "vol9": DOCS / "9_Items_and_Economy_Master_Guide.md",
}

ROSTER_MAX = 721          # solo #001-#721 forman el plantel (SPEC / memoria "Roster boundary")

# Archivos que escribe este generador.
OFFICIAL_WRITTEN = [
    "abilities.txt", "moves.txt", "items.txt", "pokemon.txt", "tm.txt", "berryplants.txt",
    "btpokemon.txt", "fancycuppm.txt", "fancycupsinglepm.txt", "littlecuppm.txt", "pikacuppm.txt", "pokecuppm.txt",
]
TEAM_FILES = ["btpokemon.txt", "fancycuppm.txt", "fancycupsinglepm.txt", "littlecuppm.txt", "pikacuppm.txt", "pokecuppm.txt"]

# ----------------------------------------------------------------------------------------------------------------------
# Entrada / salida
# ----------------------------------------------------------------------------------------------------------------------


def read_lines(path: Path) -> list[str]:
    """Lee un archivo de texto (UTF-8 estricto, con o sin BOM; CRLF/LF) y devuelve sus lineas sin fin de linea."""
    raw = Path(path).read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    text = raw.decode("utf-8")
    if "\ufffd" in text or "\ufeff" in text:
        raise ValueError(f"{path}: caracter de sustitucion/BOM interno")
    lines = re.split(r"\r\n|\n|\r", text)
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def data_lines(path: Path) -> list[str]:
    """Lineas de datos: sin lineas en blanco ni comentarios (#)."""
    return [l for l in read_lines(path) if l.strip() and not l.startswith("#")]


def write_lines(path: Path, lines: list[str], dry: bool = False) -> int:
    for l in lines:
        if "\r" in l or "\n" in l:
            raise ValueError(f"{path.name}: salto de linea embebido en {l[:60]!r}")
        if "\ufeff" in l or "\ufffd" in l:
            raise ValueError(f"{path.name}: BOM/U+FFFD en {l[:60]!r}")
    payload = "\r\n".join(lines) + "\r\n"
    if not dry:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            f.write(payload)
    return len(payload.encode("utf-8")) + 3


def md5_file(path: Path) -> str:
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def verify_backup() -> list[str]:
    """Comprueba que PBS_backup_original/ sigue intacto segun MANIFEST.md5."""
    bad = []
    manifest = SRC / "MANIFEST.md5"
    for ln in manifest.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([0-9a-f]{32})\s+\*?(.+)$", ln.strip())
        if not m:
            continue
        name = m.group(2)
        if name.startswith("./"):
            name = name[2:]
        p = SRC / name
        if not p.exists() or md5_file(p) != m.group(1):
            bad.append(name)
    return bad


def csv_split(line: str) -> list[str]:
    """Troceado de una linea CSV con la misma semantica que csvfield! de Essentials (comillas con \\ como escape)."""
    fields: list[str] = []
    s = line
    while True:
        s = s.lstrip()
        if s.startswith('"'):
            i = 1
            buf = []
            esc = False
            while i < len(s):
                ch = s[i]
                i += 1
                if ch == '"' and not esc:
                    break
                if ch == "\\" and not esc:
                    esc = True
                else:
                    buf.append(ch)
                    esc = False
            fields.append("".join(buf))
            s = s[i:].lstrip()
            if s.startswith(","):
                s = s[1:]
                continue
            if s == "":
                break
            raise ValueError(f"campo entrecomillado invalido: {line[:80]!r}")
        j = s.find(",")
        if j < 0:
            fields.append(s.rstrip())
            break
        fields.append(s[:j].rstrip())
        s = s[j + 1:]
    return fields


# ----------------------------------------------------------------------------------------------------------------------
# 1. abilities.txt  <-  Vol. 2 (PDF; texto extraido en el scratchpad) -- descripciones en espanol
# ----------------------------------------------------------------------------------------------------------------------
# Solo cambian las DESCRIPCIONES. IDs, simbolos y nombres espanoles quedan intactos ("zero name changes").
# (ID segun la tabla de la Seccion 2 del Vol. 2, texto nuevo en una frase al estilo PBS.)
ABILITY_REWORKS: "OrderedDict[str, tuple[int, str]]" = OrderedDict([
    ("ILLUMINATE", (35, "Al entrar en combate reduce la Precisión de los rivales, y además aumenta la probabilidad de encontrar Pokémon salvajes.")),
    ("FOREWARN", (108, "Al entrar en combate amilana al rival de tal manera que su Ataque Especial disminuye.")),
    ("PUREPOWER", (74, "Duplica la potencia de los ataques especiales.")),
    ("PROPELLERTAIL", (257, "Aumenta la potencia de los movimientos que no son de contacto.")),
    ("SHELLARMOR", (75, "La robusta coraza que lo protege reduce el daño recibido por ataques físicos.")),
    ("VITALSPIRIT", (72, "Su determinación le impide quedarse dormido o sufrir congelación.")),
    ("SANDVEIL", (8, "Aumenta la Defensa durante las tormentas de arena.")),
    ("SNOWCLOAK", (81, "Aumenta la Defensa Especial cuando nieva.")),
    ("FLAREBOOST", (138, "Aumenta la potencia de los ataques especiales cuando el Pokémon sufre quemaduras o congelación.")),
    ("SYNCHRONIZE", (28, "Contagia el envenenamiento, las quemaduras, la parálisis o la congelación al Pokémon que le cause ese estado.")),
    ("PLUS", (57, "Potencia el Ataque Especial, sobre todo si un Pokémon aliado tiene la habilidad Más o Menos.")),
    ("MINUS", (58, "Potencia el Ataque Especial si un Pokémon aliado tiene la habilidad Más o Menos; si está solo, aumenta su Defensa Especial.")),
    ("STENCH", (1, "Debido al mal olor que emana, al atacar al rival tiene más probabilidades de hacerlo retroceder.")),
    ("RUNAWAY", (50, "Aumenta la Velocidad cuando le quedan la mitad de los PS o menos y permite escapar de todos los Pokémon salvajes.")),
    ("DAMP", (6, "Aumenta la humedad del entorno, evita que se puedan utilizar movimientos explosivos y reduce el daño de los movimientos de tipo Fuego.")),
    ("HONEYGATHER", (118, "Al entrar en combate reduce la Velocidad de los rivales, y es posible que el Pokémon encuentre Miel una vez concluido el combate.")),
    ("BALLFETCH", (236, "Al entrar en combate aumenta su Velocidad si algún miembro del equipo está debilitado y, si no lleva equipado ningún objeto, recupera la Poké Ball del primer intento de captura fallido.")),
    ("FRIENDGUARD", (132, "Reduce el daño que sufren los aliados y, en menor medida, el que sufre el propio Pokémon en combates individuales.")),
    ("LIGHTMETAL", (135, "Reduce a la mitad el peso del Pokémon y aumenta ligeramente su Velocidad.")),
    ("HEAVYMETAL", (134, "Duplica el peso del Pokémon y aumenta ligeramente su Defensa.")),
    ("HEALER", (131, "Recupera PS al final de cada turno si sufre un problema de estado y a veces cura los de un aliado.")),
    ("KLUTZ", (103, "El Pokémon no puede usar objetos equipados, pero sus ataques son más potentes.")),
    ("PASTELVEIL", (238, "Aumenta la Defensa Especial al recibir un ataque especial.")),
    ("ANTICIPATION", (107, "Prevé los movimientos peligrosos del rival y, si los detecta al entrar en combate, aumenta su Velocidad.")),
    ("CURIOUSMEDICINE", (265, "Al entrar en combate, rezuma una sustancia medicinal por la caracola que revierte los cambios en las características de los rivales.")),
])
# ICESCALES (249, "Buffed"): el Vol. 2 solo cambia el motor (Def. Esp. x1.5); el texto PBS ya describe el efecto final
# («reducen a la mitad el daño que le infligen los ataques especiales»). Se conserva tal cual y se documenta.
ABILITY_TEXT_ALREADY_CORRECT = {"ICESCALES": 249}

# Nieve (Gen 9) sustituye a Granizo: solo se retoca el texto que lo menciona.
ABILITY_SNOW_WORDING: "OrderedDict[str, tuple[int, str]]" = OrderedDict([
    ("ICEBODY", (115, "Recupera PS de forma gradual cuando nieva.")),
    ("SNOWWARNING", (117, "El Pokémon hace que nieve al entrar en combate.")),
    ("SLUSHRUSH", (196, "Aumenta su Velocidad si está nevando.")),
    # La Nieve no hace dano residual (Vol. 2 Seccion 1): Funda deja de tener un granizo del que protegerse.
    ("OVERCOAT", (142, "Protege al Pokémon de las tormentas de arena y de los movimientos con polvos.")),
    ("ICEFACE", (254, "Recibe el daño ocasionado por un ataque físico con el hielo de su cabeza en lugar de afectar al Pokémon, tras lo cual cambia su forma. El hielo de su cabeza se restaura cuando vuelva a nevar.")),
])


def build_abilities(report: dict) -> list[str]:
    out = []
    seen_changed = set()
    changes = []
    for ln in data_lines(SRC / "abilities.txt"):
        m = re.match(r'^(\d+),(\w+),([^,"]*),"(.*)"$', ln)
        if not m:
            raise ValueError(f"abilities.txt: linea no reconocida: {ln!r}")
        aid, sym, name, desc = int(m.group(1)), m.group(2), m.group(3), m.group(4)
        new = desc
        if sym in ABILITY_REWORKS:
            eid, text = ABILITY_REWORKS[sym]
            assert eid == aid, f"ID de {sym}: {aid} != {eid}"
            new = text
            seen_changed.add(sym)
            changes.append([aid, sym, desc, new])
        elif sym in ABILITY_SNOW_WORDING:
            eid, text = ABILITY_SNOW_WORDING[sym]
            assert eid == aid, f"ID de {sym}: {aid} != {eid}"
            assert re.search(r"(?i)granizo|graniza", desc), f"{sym}: el original no menciona granizo: {desc!r}"
            new = text
            seen_changed.add(sym)
            changes.append([aid, sym, desc, new])
        elif sym in ABILITY_TEXT_ALREADY_CORRECT:
            assert ABILITY_TEXT_ALREADY_CORRECT[sym] == aid
        assert "#" not in new and '"' not in new and "\\" not in new, f"{sym}: caracter reservado en la descripcion"
        out.append(f'{aid},{sym},{name},"{new}"')
    missing = (set(ABILITY_REWORKS) | set(ABILITY_SNOW_WORDING)) - seen_changed
    assert not missing, f"habilidades no encontradas: {missing}"
    left = [l for l in out if re.search(r"(?i)granizo|graniza", l)]
    assert not left, f"quedan menciones a granizo: {left}"
    report["abilities"] = {
        "total": len(out),
        "reworked_descriptions": len(ABILITY_REWORKS),
        "snow_wording": sorted(ABILITY_SNOW_WORDING),
        "unchanged_text_icescales": True,
        "descriptions_changed_total": len(seen_changed),
        "changes": changes,
    }
    return out


# ----------------------------------------------------------------------------------------------------------------------
# 2. moves.txt  <-  proposed_moves.txt
# ----------------------------------------------------------------------------------------------------------------------


def fix_malformed_move(line: str, fixes: list) -> str:
    """Defecto heredado del PBS vanilla (y copiado en proposed_moves.txt): la linea 720 BURNINGJEALOUSY lleva 15 campos
    (el nombre «Envidia Ardiente» repetido tras las banderas), con lo que Essentials leeria ese nombre como DESCRIPCION.
    La correccion es inequivoca: se elimina el campo repetido."""
    f = csv_split(line)
    if len(f) == 15 and f[13] == f[2]:
        stray = f",{f[12]},{f[13]},"
        assert line.count(stray) == 1
        fixes.append(f"{f[1]}: campo repetido «{f[13]}» (15 campos) eliminado")
        return line.replace(stray, f",{f[12]},")
    return line


def build_moves(report: dict) -> list[str]:
    fixes: list[str] = []
    old = [fix_malformed_move(l, []) for l in data_lines(SRC / "moves.txt")]
    new = [fix_malformed_move(l, fixes) for l in data_lines(PROPOSED["moves"])]
    assert len(old) == len(new) == 765, (len(old), len(new))
    changed = 0
    for a, b in zip(old, new):
        fa, fb = csv_split(a), csv_split(b)
        assert len(fb) == 14 == len(fa), f"campos != 14: {b[:60]!r}"
        assert fa[0] == fb[0] and fa[1] == fb[1], f"ID/simbolo cambian: {a[:40]!r} -> {b[:40]!r}"
        assert "#" not in b, f"'#' en moves.txt (prepline lo truncaria): {b[:60]!r}"
        if a != b:
            changed += 1
    report["moves"] = {"total": len(new), "changed_lines": changed, "malformed_lines_fixed": fixes}
    return new


# ----------------------------------------------------------------------------------------------------------------------
# 3. items.txt  <-  proposed_items.txt  (+ rareza por objeto del Vol. 9, Cap. 2)
# ----------------------------------------------------------------------------------------------------------------------


def parse_items(lines: list[str]) -> "OrderedDict[str, list[str]]":
    items: "OrderedDict[str, list[str]]" = OrderedDict()
    for ln in lines:
        f = csv_split(ln)
        assert len(f) == 11, f"items.txt: {len(f)} campos en {ln[:60]!r}"
        assert f[1] not in items, f"simbolo duplicado {f[1]}"
        items[f[1]] = f
    return items


def build_items(report: dict) -> tuple[list[str], "OrderedDict[str, list[str]]", "OrderedDict[str, list[str]]"]:
    new_lines = data_lines(PROPOSED["items"])
    new = parse_items(new_lines)
    old = OrderedDict()      # el original tiene una linea de 10 campos: se normaliza a 11
    for ln in data_lines(SRC / "items.txt"):
        f = csv_split(ln)
        assert len(f) in (10, 11)
        f += [""] * (11 - len(f))
        old[f[1]] = f
    ids = [int(f[0]) for f in new.values()]
    assert ids == sorted(set(ids)), "IDs no ascendentes/unicos"
    for sym, f in new.items():
        if sym in old:
            assert old[sym][0] == f[0], f"ID de {sym} cambia: {old[sym][0]} -> {f[0]}"
    # MT -> movimiento
    tms = {}
    for sym, f in new.items():
        m = re.fullmatch(r"TM(\d{2,3})", sym)
        if m:
            tms[int(m.group(1))] = f[10]
    assert sorted(tms) == list(range(1, 101)), "faltan MT"
    pruned = [s for s in old if s not in new]
    gaps = [i for i in range(1, max(ids) + 1) if i not in set(ids)]
    report["items"] = {
        "total": len(new), "max_id": max(ids), "new_ids": sorted(int(f[0]) for s, f in new.items() if s not in old),
        "pruned": len(pruned), "gaps_in_id_space": len(gaps), "tm_items": len(tms),
    }
    return new_lines, new, old


def parse_item_rarity(new_items: "OrderedDict[str, list[str]]") -> dict:
    """Rareza por simbolo, leida de las tablas del Cap. 2 del Vol. 9 (columnas ID | Nombre | Categoria | Rareza | ...)."""
    L = PROPOSED["vol9"].read_text(encoding="utf-8").split("\n")
    start = next(i for i, l in enumerate(L) if l.startswith("# Capítulo 2"))
    end = next(i for i, l in enumerate(L) if l.startswith("# Capítulo 3"))
    by_id = {}
    for l in L[start:end]:
        if not l.startswith("|"):
            continue
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(c) >= 7 and c[0].isdigit():
            by_id[int(c[0])] = (c[1], c[3])
    tier = {}
    for sym, f in new_items.items():
        iid = int(f[0])
        if 288 <= iid <= 387:
            tier[sym] = "Tier 1"          # las 100 MT son Tier 1 (Vol. 9 Sec. 6.1)
            continue
        assert iid in by_id, f"{sym} ({iid}) sin rareza en el Vol. 9"
        assert by_id[iid][0] == f[2], f"{sym}: nombre {f[2]!r} != Vol. 9 {by_id[iid][0]!r}"
        r = by_id[iid][1]
        tier[sym] = ("Tier 1" if r.startswith("Tier 1") else "Tier 2" if r.startswith("Tier 2") else
                     "Tier 3" if r.startswith("Tier 3") else "Legendario" if r.startswith("Legend") else "Clave")
    cnt = Counter(tier.values())
    assert cnt["Tier 3"] == 148 and cnt["Tier 2"] == 84 and cnt["Clave"] == 31 and cnt["Legendario"] == 29 and cnt["Tier 1"] == 122, cnt
    return tier


# ----------------------------------------------------------------------------------------------------------------------
# 4. pokemon.txt  <-  proposed_pokemon.txt + proposed_learnsets.txt (+ limpieza #722-#905)
# ----------------------------------------------------------------------------------------------------------------------
# Metodos de evolucion cuyo parametro es un objeto (PBEvolution::EVOPARAM == 2 en 126_Pokemon_Evolution.rb).
EVO_ITEM_METHODS = {
    "TradeItem", "Item", "ItemMale", "ItemFemale", "DayHoldItem", "NightHoldItem",
    "ItemForm0", "ItemForm1", "ItemForm2", "HoldItemForm0", "HoldItemForm1", "HoldItemForm2",
}
WILD_KEYS = ("WildItemCommon", "WildItemUncommon", "WildItemRare")


def parse_sections(lines: list[str], numeric: bool = True) -> "OrderedDict[int, list[list[str]]]":
    """Secciones [N] -> lista de [clave, valor]. Los comentarios (#) y lineas en blanco se descartan."""
    secs: "OrderedDict[int, list[list[str]]]" = OrderedDict()
    cur = None
    for ln in lines:
        m = re.match(r"^\[(\d+)\]$", ln)
        if m:
            cur = int(m.group(1))
            assert cur not in secs, f"seccion duplicada [{cur}]"
            secs[cur] = []
            continue
        if not ln.strip() or ln.startswith("#"):
            continue
        assert cur is not None, f"linea fuera de seccion: {ln[:60]!r}"
        m = re.match(r"^(\w+)=(.*)$", ln)
        assert m, f"linea no clave=valor: {ln[:60]!r}"
        secs[cur].append([m.group(1), m.group(2)])
    return secs


def sec_get(sec: list[list[str]], key: str):
    for k, v in sec:
        if k == key:
            return v
    return None


def sec_set(sec: list[list[str]], key: str, value: str, after: str | None = None) -> None:
    for kv in sec:
        if kv[0] == key:
            kv[1] = value
            return
    idx = len(sec)
    if after is not None:
        for i, (k, _) in enumerate(sec):
            if k == after:
                idx = i + 1
                break
    sec.insert(idx, [key, value])


def sec_del(sec: list[list[str]], key: str) -> bool:
    n = len(sec)
    sec[:] = [kv for kv in sec if kv[0] != key]
    return len(sec) != n


def evo_triplets(value: str) -> list[list[str]]:
    if value == "":
        return []
    f = value.split(",")
    assert len(f) % 3 == 0, f"Evolutions con {len(f)} campos: {value!r}"
    return [f[i:i + 3] for i in range(0, len(f), 3)]


def build_pokemon(items_new: "OrderedDict[str, list[str]]", tier: dict, report: dict) -> tuple[list[str], dict]:
    orig = parse_sections(read_lines(SRC / "pokemon.txt"))
    prop = parse_sections(read_lines(PROPOSED["pokemon"]))
    # learnsets: pueden ir en LF puro; los comentarios (# Nombre) se descartan
    learn = parse_sections(read_lines(PROPOSED["learnsets"]))
    assert list(orig) == list(range(1, 906)), "pokemon.txt original no es 1..905"
    assert list(prop) == list(range(1, ROSTER_MAX + 1)), "proposed_pokemon no es 1..721"
    assert list(learn) == list(range(1, ROSTER_MAX + 1)), "proposed_learnsets no es 1..721"

    abilities = {re.match(r"^\d+,(\w+),", l).group(1) for l in data_lines(SRC / "abilities.txt")}
    moves = {csv_split(l)[1] for l in data_lines(PROPOSED["moves"])}
    types = set(re.findall(r"^InternalName=(\w+)", "\n".join(read_lines(SRC / "types.txt")), re.M))
    species = {sec_get(s, "InternalName"): n for n, s in orig.items()}
    removed_items = []      # (seccion, clave, objeto, motivo)
    stats = Counter()
    pruned = {}             # simbolo -> motivo
    for sym in set(csv_split(l)[1] for l in data_lines(SRC / "items.txt")):
        if sym not in items_new:
            pruned[sym] = "podado"

    roster_changed = Counter()
    for n, sec in orig.items():
        if n <= ROSTER_MAX:
            p = {k: v for k, v in prop[n]}
            lv = {k: v for k, v in learn[n]}
            assert sec_get(sec, "InternalName") == p["InternalName"], f"[{n}] InternalName cambia"
            assert sec_get(sec, "Name") == p["Name"], f"[{n}] Name cambia ({sec_get(sec, 'Name')} -> {p['Name']})"
            before = [list(kv) for kv in sec]
            for key in ("Name", "InternalName", "Type1", "BaseStats", "Abilities"):
                sec_set(sec, key, p[key])
            if "Type2" in p:
                sec_set(sec, "Type2", p["Type2"], after="Type1")
            else:
                sec_del(sec, "Type2")
            for t in (p["Type1"], p.get("Type2")):
                assert t is None or t in types, f"[{n}] tipo desconocido {t}"
            ab = p["Abilities"].split(",")
            assert 1 <= len(ab) <= 2 and all(a in abilities for a in ab), f"[{n}] habilidades invalidas {ab}"
            assert len(p["BaseStats"].split(",")) == 6
            if sec_del(sec, "HiddenAbility"):
                stats["hidden_ability_removed"] += 1
            if sec_del(sec, "EggMoves"):
                stats["eggmoves_removed"] += 1
            mv = lv["Moves"].split(",")
            assert len(mv) % 2 == 0 and all(mv[i].isdigit() and mv[i + 1] in moves for i in range(0, len(mv), 2)), f"[{n}] Moves invalidos"
            sec_set(sec, "Moves", lv["Moves"])
            assert lv.get("EggMoves", "") == "", f"[{n}] EggMoves no vacio en learnsets"
            evo = p.get("Evolutions", "")
            for tr in evo_triplets(evo):
                assert tr[0] in species and species[tr[0]] <= ROSTER_MAX, f"[{n}] evolucion a especie fuera del plantel: {tr}"
                if tr[1] in EVO_ITEM_METHODS:
                    assert tr[2] in items_new, f"[{n}] evolucion con objeto inexistente: {tr}"
                    stats["evolutions_by_item"] += 1
            sec_set(sec, "Evolutions", evo)
            if sec != before:
                roster_changed["sections_changed"] += 1
        else:
            # Fuera del plantel (#722-#905): se conserva, pero se limpia para que el PBS siga compilando.
            evo = sec_get(sec, "Evolutions") or ""
            kept = []
            for tr in evo_triplets(evo):
                if tr[1] in EVO_ITEM_METHODS and tr[2] not in items_new:
                    removed_items.append((n, "Evolutions", f"{tr[0]},{tr[1]},{tr[2]}", "evolucion con objeto podado (se elimina la evolucion)"))
                    stats["evolutions_dropped_outside_roster"] += 1
                else:
                    kept.append(",".join(tr))
            if evo and len(kept) != len(evo_triplets(evo)):
                sec_set(sec, "Evolutions", ",".join(kept))
                roster_changed["outside_cleaned"] += 1
        # Objetos llevados por Pokemon salvajes (todas las secciones)
        for key in WILD_KEYS + ("Incense",):
            v = sec_get(sec, key)
            if v is None:
                continue
            if v == "":
                sec_del(sec, key)
                continue
            if v not in items_new:
                reason = "objeto podado (no existe en items.txt)"
            elif tier[v] in ("Tier 1", "Tier 2", "Legendario", "Clave"):
                reason = f"{tier[v]}: copia extra rompe la escasez (Vol. 9 Sec. 6.4.1)"
            else:
                continue
            removed_items.append((n, key, v, reason))
            sec_del(sec, key)
            stats["wild_item_pruned" if v not in items_new else "wild_item_tier12"] += 1
            if n > ROSTER_MAX:
                roster_changed["outside_cleaned_wild"] += 1
    # ---- sanity de referencias en el resultado
    for n, sec in orig.items():
        for k, v in sec:
            if k in WILD_KEYS or k == "Incense":
                assert v in items_new, f"[{n}] {k}={v} sigue sin existir"
            if k == "Evolutions":
                for tr in evo_triplets(v):
                    assert tr[0] in species, f"[{n}] evolucion a especie inexistente {tr}"
                    if tr[1] in EVO_ITEM_METHODS:
                        assert tr[2] in items_new, f"[{n}] evolucion con objeto inexistente {tr}"
            if k in ("Abilities", "HiddenAbility"):
                assert all(a in abilities for a in v.split(",") if a), f"[{n}] habilidad inexistente en {v}"
            if k in ("Moves",):
                mvl = v.split(",")
                assert all(mvl[i + 1] in moves for i in range(0, len(mvl), 2)), f"[{n}] movimiento inexistente"
            if k == "EggMoves":
                assert all(m in moves for m in v.split(",")), f"[{n}] movimiento huevo inexistente"
    # ---- serializar
    out: list[str] = []
    for n, sec in orig.items():
        out.append(f"[{n}]")
        out.extend(f"{k}={v}" for k, v in sec)
    report["pokemon"] = {
        "sections": len(orig), "roster_sections_rewritten": ROSTER_MAX,
        "roster_sections_with_changes": roster_changed["sections_changed"],
        "outside_roster_sections_touched": sorted({x[0] for x in removed_items if x[0] > ROSTER_MAX}),
        "outside_roster_evolution_sections_cleaned": roster_changed["outside_cleaned"],
        "hidden_ability_lines_removed": stats["hidden_ability_removed"],
        "eggmoves_lines_removed": stats["eggmoves_removed"],
        "evolutions_by_item_in_roster": stats["evolutions_by_item"],
        "wild_item_refs_removed_pruned": stats["wild_item_pruned"],
        "wild_item_refs_removed_tier12": stats["wild_item_tier12"],
        "evolutions_dropped_outside_roster": stats["evolutions_dropped_outside_roster"],
        "removed_items_detail": [list(x) for x in removed_items],
    }
    return out, species


# ----------------------------------------------------------------------------------------------------------------------
# 5. tm.txt  <-  proposed_tm.txt  (+ comprobacion contra items.txt y pokemon.txt)
# ----------------------------------------------------------------------------------------------------------------------
TM_HEADER = [
    "#================================================================",
    "# PBS/tm.txt - Pokemon REM: 100 MT (MT01-MT100), una seccion [MOVIMIENTO] con la lista de especies compatibles (#001-#721)",
    "# Inyectado por tools/rebalance/phase1/inject_core.py desde docs/rebalance/proposed_tm.txt (diseno: 5_TM_Master_Guide).",
    "# La MT n usa el movimiento de la n-esima seccion: items.txt TM01..TM100 -> campo Move. Sin MO ni tutores de movimientos.",
    "#================================================================",
]


def build_tm(items_new: "OrderedDict[str, list[str]]", species: dict, report: dict) -> list[str]:
    raw = read_lines(PROPOSED["tm"])
    idx = next(i for i, l in enumerate(raw) if l.startswith("# Early game"))
    assert raw[idx - 1].startswith("#===="), "estructura inesperada de proposed_tm.txt"
    body = raw[idx - 1:]
    moves = {csv_split(l)[1] for l in data_lines(PROPOSED["moves"])}
    blocks = []
    cur = None
    for ln in body:
        if not ln.strip() or ln.startswith("#"):
            continue
        m = re.match(r"^\[(\w+)\]$", ln)
        if m:
            cur = [m.group(1), []]
            blocks.append(cur)
            continue
        assert cur is not None
        cur[1].extend(s for s in ln.split(",") if s)
    assert len(blocks) == 100, f"{len(blocks)} bloques en proposed_tm.txt"
    seen_moves = set()
    n_pairs = 0
    for i, (mv, sp) in enumerate(blocks, 1):
        assert mv in moves, f"TM{i:02d}: movimiento {mv} no existe en moves.txt"
        assert mv not in seen_moves, f"movimiento repetido {mv}"
        seen_moves.add(mv)
        tmsym = f"TM{i:02d}"
        assert tmsym in items_new and items_new[tmsym][10] == mv, f"{tmsym}: items.txt -> {items_new.get(tmsym, ['?'] * 11)[10]} != {mv}"
        assert len(sp) == len(set(sp)), f"TM{i:02d}: especies repetidas"
        for s in sp:
            assert s in species and species[s] <= ROSTER_MAX, f"TM{i:02d}: especie {s} fuera del plantel o inexistente"
        n_pairs += len(sp)
    report["tm"] = {"tms": len(blocks), "species_listed_pairs": n_pairs}
    return TM_HEADER + body


# ----------------------------------------------------------------------------------------------------------------------
# 6. berryplants.txt
# ----------------------------------------------------------------------------------------------------------------------


def build_berryplants(items_new: dict, report: dict) -> list[str]:
    out, dropped = [], []
    for ln in data_lines(SRC / "berryplants.txt"):
        m = re.match(r"^(\w+)=(\d+(?:,\d+){3})$", ln)
        assert m, f"berryplants: {ln!r}"
        (out if m.group(1) in items_new else dropped).append(ln)
    report["berryplants"] = {"kept": len(out), "dropped": len(dropped), "dropped_names": [d.split("=")[0] for d in dropped],
                             "berries_in_items_without_plant_entry": sorted(
                                 s for s in items_new if s.endswith("BERRY") and s not in {l.split("=")[0] for l in out})}
    return out


# ----------------------------------------------------------------------------------------------------------------------
# 7. Limpieza transversal: btpokemon.txt y copas (*cuppm.txt)
# ----------------------------------------------------------------------------------------------------------------------
# Tabla EXPLICITA y DETERMINISTA de sustituciones: objeto podado -> objeto superviviente (items.txt nuevo) de rol parecido.
#   * FOCUSBAND (Cinta Focus, 10 % de aguantar con 1 PS)  -> FOCUSSASH (Banda Focus: aguantar un golpe letal; mismo rol de supervivencia).
#   * LAXINCENSE (Incienso Suave: -precision del rival)   -> BRIGHTPOWDER (Polvo Brillo: mismo efecto de evasion).
#   * SEAINCENSE (Incienso Marino: potencia Agua)         -> MYSTICWATER (Agua Mistica: mismo efecto).
#   * CLEANSETAG / EXPSHARE / SOOTHEBELL (sin efecto en combate al llevarlos) -> EVERSTONE (Piedra Eterna: tampoco altera el combate).
#   * 20 bayas podadas (14 sin efecto de combate + 6 de reduccion de EV; Vol. 9 Sec. 1.2, sin efecto al llevarlas)
#       -> ORANBERRY (la baya de menor efecto que sobrevive: 10 PS; no altera el equilibrio de los equipos).
PRUNED_BERRIES = [
    "RAZZBERRY", "BLUKBERRY", "NANABBERRY", "WEPEARBERRY", "PINAPBERRY",
    "POMEGBERRY", "KELPSYBERRY", "QUALOTBERRY", "HONDEWBERRY", "GREPABERRY", "TAMATOBERRY",
    "CORNNBERRY", "MAGOSTBERRY", "RABUTABERRY", "NOMELBERRY", "SPELONBERRY", "PAMTREBERRY",
    "WATMELBERRY", "DURINBERRY", "BELUEBERRY",
]
ITEM_SUBSTITUTIONS: "OrderedDict[str, str]" = OrderedDict(
    [("FOCUSBAND", "FOCUSSASH"), ("LAXINCENSE", "BRIGHTPOWDER"), ("SEAINCENSE", "MYSTICWATER"),
     ("CLEANSETAG", "EVERSTONE"), ("EXPSHARE", "EVERSTONE"), ("SOOTHEBELL", "EVERSTONE")]
    + [(b, "ORANBERRY") for b in PRUNED_BERRIES]
)


# Erratas del PBS vanilla en los equipos (referencias a simbolos que NO existen; Essentials las ignora en silencio:
# la especie desconocida cae a #001 Bulbasaur y el movimiento desconocido se descarta). La correccion es inequivoca.
TEAM_SYMBOL_FIXES = {
    "species": {"MR_MIME": "MRMIME"},
    "move": {"SMELLINGSALT": "SMELLINGSALTS"},
}


def build_team_file(name: str, items_new: dict, report: dict, species: dict, moves: set) -> list[str]:
    out = []
    subs = Counter()
    fixes = Counter()
    for ln in data_lines(SRC / name):
        p = ln.split(";")
        assert len(p) == 5, f"{name}: {len(p)} campos en {ln[:60]!r}"
        if p[0] in TEAM_SYMBOL_FIXES["species"]:
            fixes[f"especie {p[0]}->{TEAM_SYMBOL_FIXES['species'][p[0]]}"] += 1
            p[0] = TEAM_SYMBOL_FIXES["species"][p[0]]
        mv = p[4].split(",")
        for i, m in enumerate(mv):
            if m in TEAM_SYMBOL_FIXES["move"]:
                fixes[f"movimiento {m}->{TEAM_SYMBOL_FIXES['move'][m]}"] += 1
                mv[i] = TEAM_SYMBOL_FIXES["move"][m]
        p[4] = ",".join(mv)
        it = p[1]
        if it != "" and it not in items_new:
            assert it in ITEM_SUBSTITUTIONS, f"{name}: objeto podado sin sustitucion: {it}"
            subs[(it, ITEM_SUBSTITUTIONS[it])] += 1
            p[1] = ITEM_SUBSTITUTIONS[it]
        assert p[0] in species, f"{name}: especie inexistente {p[0]}"
        assert all(m == "" or m in moves for m in mv), f"{name}: movimiento inexistente en {ln[:60]!r}"
        out.append(";".join(p))
    for (a, b) in subs:
        assert b in items_new
    report.setdefault("team_files", {})[name] = {
        "lines": len(out), "substitutions": sum(subs.values()),
        "by_item": {f"{a}->{b}": c for (a, b), c in sorted(subs.items())},
        "symbol_fixes": dict(fixes),
    }
    return out


# ----------------------------------------------------------------------------------------------------------------------
# Orquestacion
# ----------------------------------------------------------------------------------------------------------------------


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=DST, help="directorio de salida (por defecto ROOT/PBS)")
    ap.add_argument("--dry-run", action="store_true", help="calcula y valida, pero no escribe")
    ap.add_argument("--report", type=Path, help="escribe un JSON con el resumen")
    ap.add_argument("--no-verify", action="store_true", help="no comprobar MANIFEST.md5 de PBS_backup_original")
    ap.add_argument("--no-check", action="store_true", help="no ejecutar pbs_check.py al final")
    args = ap.parse_args(argv)

    if not args.no_verify:
        bad = verify_backup()
        if bad:
            print("ERROR: PBS_backup_original/ ha cambiado respecto a MANIFEST.md5:", ", ".join(bad), file=sys.stderr)
            return 2

    report: dict = {}
    abilities = build_abilities(report)
    moves = build_moves(report)
    items_lines, items_new, items_old = build_items(report)
    tier = parse_item_rarity(items_new)
    pokemon, species = build_pokemon(items_new, tier, report)
    tm = build_tm(items_new, species, report)
    berry = build_berryplants(items_new, report)
    moves_set = {csv_split(l)[1] for l in moves}
    teams = {n: build_team_file(n, items_new, report, species, moves_set) for n in TEAM_FILES}

    # simbolos de habilidad usados por los 721 existen (build_pokemon ya lo asegura); comprobar numero de habilidades
    report["abilities"]["ids_contiguous_1_to_n"] = [int(l.split(",")[0]) for l in abilities] == list(range(1, len(abilities) + 1))

    outputs = OrderedDict([
        ("abilities.txt", abilities), ("moves.txt", moves), ("items.txt", items_lines),
        ("pokemon.txt", pokemon), ("tm.txt", tm), ("berryplants.txt", berry),
    ])
    outputs.update(teams)
    sizes = {}
    for fname, lines in outputs.items():
        sizes[fname] = write_lines(args.out / fname, lines, dry=args.dry_run)
    report["files_written"] = sizes
    report["output_dir"] = str(args.out)
    report["dry_run"] = args.dry_run

    print(("DRY-RUN " if args.dry_run else "") + f"inject_core: {len(outputs)} archivos -> {args.out}")
    for fname, sz in sizes.items():
        print(f"  {fname:22s} {sz:9d} bytes  ({len(outputs[fname])} lineas)")
    def brief(d):
        return {k: (v if not isinstance(v, (list, dict)) or len(str(v)) < 80 else f"<{len(v)}>") for k, v in d.items()}
    for key in ("abilities", "moves", "items", "pokemon", "tm", "berryplants"):
        print(f"{key}:", json.dumps(brief(report[key]), ensure_ascii=False))
    for fname, d in report["team_files"].items():
        print(f"{fname}: {d['lines']} equipos, {d['substitutions']} sustituciones de objeto, correcciones de simbolo: {d['symbol_fixes'] or '-'}")

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    rc = 0
    if not args.no_check and not args.dry_run:
        spec = importlib.util.spec_from_file_location("pbs_check", HERE / "pbs_check.py")
        if spec and (HERE / "pbs_check.py").exists():
            mod = importlib.util.module_from_spec(spec)
            sys.modules["pbs_check"] = mod
            spec.loader.exec_module(mod)
            res = mod.check(str(args.out))
            print(f"pbs_check: {len(res['errors'])} errores, {len(res['warnings'])} avisos")
            for e in res["errors"][:30]:
                print("  ERROR", mod.format_issue(e))
            rc = 1 if res["errors"] else 0
    return rc


if __name__ == "__main__":
    sys.exit(main())
