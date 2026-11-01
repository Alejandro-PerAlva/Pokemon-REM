#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pbs_check.py - validador INDEPENDIENTE (solo stdlib) de los archivos oficiales de PBS/ (Pokemon Essentials v16, REM).

Replica las reglas del compilador (178_Compiler.rb: pbCompileAbilities / Moves / Items / BerryPlants / PokemonData /
Machines / Trainers / TrainerLists / Encounters / ShadowMoves) y comprueba ademas:

  * codificacion: UTF-8 estricto, BOM (EF BB BF) y CRLF puro con CRLF final (SPEC 0);
  * sintaxis y numero de campos de cada archivo; IDs/simbolos unicos; rangos de bytes/words del compilador;
  * integridad referencial: tipos, movimientos, habilidades, objetos, especies (Evolutions, Moves, EggMoves, WildItem*,
    Incense, tm.txt, trainers, btpokemon/copas, berryplants, shadowmoves, encounters);
  * que no queden referencias a objetos PODADOS (los de PBS_backup_original/items.txt que no estan en
    docs/rebalance/proposed_items.txt): escaneo por tokens de TODOS los archivos de texto;
  * coherencia de diseno (avisos): MT n <-> n-esimo bloque de tm.txt, plantel #001-#721, habilidad oculta fusionada,
    EggMoves fusionados, objetos Tier 1/2 llevados por Pokemon salvajes (Vol. 9 Sec. 6.4.1).

Uso:
    python3 tools/rebalance/phase1/pbs_check.py [--pbs DIR] [--legacy] [--json] [--json-out FILE] [--max N] [--quiet]
Codigo de salida: 0 sin errores, 1 con errores (los avisos no cuentan).

API:
    from pbs_check import check
    res = check("/ruta/PBS")            # {'errors': [...], 'warnings': [...], 'stats': {...}}
    --legacy / check(dir, legacy=True): trata el directorio como un PBS vanilla (p. ej. PBS_backup_original/): los
    objetos podados SON validos alli (no se buscan), y BOM/CRLF/diseno pasan a avisos.
Cada incidencia es un dict {file, line, code, message}.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DEFAULT_PBS = ROOT / "PBS"
DEFAULT_BACKUP = ROOT / "PBS_backup_original"
DEFAULT_DOCS = ROOT / "docs" / "rebalance"

ROSTER_MAX = 721
MAXLEVEL = 100          # 000_Settings.rb MAXIMUMLEVEL

# Archivos que escribe inject_core.py: BOM+CRLF obligatorios (error). Resto de oficiales: aviso.
CORE_FILES = ["abilities.txt", "moves.txt", "items.txt", "pokemon.txt", "tm.txt", "berryplants.txt",
              "btpokemon.txt", "fancycuppm.txt", "fancycupsinglepm.txt", "littlecuppm.txt", "pikacuppm.txt", "pokecuppm.txt"]
PM_FILES = ["btpokemon.txt", "fancycuppm.txt", "fancycupsinglepm.txt", "littlecuppm.txt", "pikacuppm.txt", "pokecuppm.txt"]
SKIP_FILES = {"~$okemon.txt"}       # archivo basura de Office: ni se lee ni se valida
# Documentos que describen el estado VANILLA/historial de cambios: mencionan objetos podados a proposito.
PRUNED_SCAN_EXEMPT = {"rem_vanilla_baseline.txt", "rem_changelog.txt"}

# ---- constantes de Essentials v16 (RGSS extraido) -------------------------------------------------------------------
EVONAMES = ["Unknown", "Happiness", "HappinessDay", "HappinessNight", "Level", "Trade", "TradeItem", "Item",
            "AttackGreater", "AtkDefEqual", "DefenseGreater", "Silcoon", "Cascoon", "Ninjask", "Shedinja", "Beauty",
            "ItemMale", "ItemFemale", "DayHoldItem", "NightHoldItem", "HasMove", "HasInParty", "LevelMale", "LevelFemale",
            "Location", "TradeSpecies", "LevelDay", "LevelNight", "LevelDarkInParty", "LevelRain", "HappinessMoveType",
            "LevelForm0", "LevelForm1", "LevelForm2", "ItemForm0", "ItemForm1", "ItemForm2", "HappinessForm0",
            "HappinessForm1", "HappinessForm2", "LevelDayForm0", "LevelDayForm1", "LevelDayForm2", "LevelNightForm0",
            "LevelNightForm1", "LevelNightForm2", "HoldItemForm0", "HoldItemForm1", "HoldItemForm2", "LevelDayTime",
            "Crits", "HasMoveForm0", "HasMoveForm1", "HasMoveForm2"]
# 0 sin parametro, 1 entero positivo, 2 objeto, 3 movimiento, 4 especie, 5 tipo
EVOPARAM = [0, 0, 0, 0, 1, 0, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 4, 1, 1, 1, 4, 1, 1, 1, 1, 5, 1, 1, 1, 2, 2, 2,
            0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 1, 0, 3, 3, 3]
GENDER_RATES = {"AlwaysMale", "FemaleOneEighth", "Female25Percent", "Female50Percent", "Female75Percent",
                "FemaleSevenEighths", "AlwaysFemale", "Genderless"}
GROWTH_RATES = {"Medium", "MediumFast", "Erratic", "Fluctuating", "Parabolic", "MediumSlow", "Fast", "Slow"}
COLORS = {"Red", "Blue", "Yellow", "Green", "Black", "Brown", "Purple", "Gray", "White", "Pink"}
HABITATS = {"", "Grassland", "Forest", "WatersEdge", "Sea", "Cave", "Mountain", "RoughTerrain", "Urban", "Rare"}
EGG_GROUPS = {"Monster", "Water1", "Bug", "Flying", "Field", "Fairy", "Grass", "Humanlike", "Water3", "Mineral",
              "Amorphous", "Water2", "Ditto", "Dragon", "Undiscovered"}
NATURES = {"HARDY", "LONELY", "BRAVE", "ADAMANT", "NAUGHTY", "BOLD", "DOCILE", "RELAXED", "IMPISH", "LAX", "TIMID",
           "HASTY", "SERIOUS", "JOLLY", "NAIVE", "MODEST", "MILD", "QUIET", "BASHFUL", "RASH", "CALM", "GENTLE",
           "SASSY", "CAREFUL", "QUIRKY"}
EV_TOKENS = {"HP", "ATK", "DEF", "SPD", "SA", "SD"}
MOVE_CATEGORIES = {"Physical", "Special", "Status"}
POCKETS = range(1, 9)
ENCOUNTER_TYPES = OrderedDict([
    ("Land", 12), ("Cave", 12), ("Water", 5), ("RockSmash", 5), ("OldRod", 2), ("GoodRod", 3), ("SuperRod", 5),
    ("HeadbuttLow", 8), ("HeadbuttHigh", 8), ("LandMorning", 12), ("LandDay", 12), ("LandNight", 12), ("BugContest", 12)])
SYMBOL_RE = re.compile(r"^(?![0-9])\w+$")


# ======================================================================================================================
# utilidades
# ======================================================================================================================
def prepline(line: str) -> str:
    """prepline de Essentials: quita comentarios `#...` (en cualquier punto de la linea) y espacios finales."""
    line = re.sub(r"\s*#.*$", "", line)
    return re.sub(r"\s+$", "", line)


def csv_fields(line: str):
    """Troceado CSV con la semantica de csvfield! (comillas, escape con barra invertida). Lanza ValueError si es invalido."""
    out = []
    s = line
    while True:
        s = s.lstrip()
        if s.startswith('"'):
            i, buf, esc = 1, [], False
            closed = False
            while i < len(s):
                ch = s[i]
                i += 1
                if ch == '"' and not esc:
                    closed = True
                    break
                if ch == "\\" and not esc:
                    esc = True
                else:
                    buf.append(ch)
                    esc = False
            if not closed:
                raise ValueError("comilla sin cerrar")
            out.append("".join(buf))
            s = s[i:].lstrip()
            if s.startswith(","):
                s = s[1:]
                continue
            if s == "":
                break
            raise ValueError("campo entrecomillado invalido (texto tras la comilla de cierre)")
        j = s.find(",")
        fld = s.rstrip() if j < 0 else s[:j].rstrip()
        if '"' in fld:
            raise ValueError(f"comilla dentro de un campo sin entrecomillar: {fld[:40]!r}")
        out.append(fld)
        if j < 0:
            break
        s = s[j + 1:]
    return out


def to_int(s: str):
    return int(s) if re.fullmatch(r"-?\d+", s or "") else None


def format_issue(i: dict) -> str:
    loc = i["file"] + (f":{i['line']}" if i.get("line") else "")
    return f"{loc} [{i['code']}] {i['message']}"


# ======================================================================================================================
class Checker:
    def __init__(self, pbs_dir, legacy=False, backup_dir=None, docs_dir=None):
        self.dir = Path(pbs_dir)
        self.legacy = legacy
        self.backup = Path(backup_dir) if backup_dir else DEFAULT_BACKUP
        self.docs = Path(docs_dir) if docs_dir else DEFAULT_DOCS
        self.errors: list[dict] = []
        self.warnings: list[dict] = []
        self.stats: dict = {}
        self.cache: dict[str, list[tuple[int, str]]] = {}
        self.types: set[str] = set()
        self.abilities: dict[str, int] = {}
        self.moves: dict[str, int] = {}
        self.items: dict[str, int] = {}
        self.item_rows: dict[str, list[str]] = {}
        self.species: dict[str, int] = {}          # InternalName exacto -> numero
        self.species_by_num: dict[int, str] = {}
        self.trainer_types: set[str] = set()
        self.pruned: set[str] = set()
        self.rarity: dict[str, str] = {}
        self.pm_line_counts: dict[str, int] = {}

    # ---- registro de incidencias -----------------------------------------------------------------------------------
    def err(self, file, line, code, msg):
        self.errors.append({"file": file, "line": line, "code": code, "message": msg})

    def warn(self, file, line, code, msg):
        self.warnings.append({"file": file, "line": line, "code": code, "message": msg})

    def design(self, file, line, code, msg):
        """Incoherencia de diseno: aviso (no rompe el compilador)."""
        if not self.legacy:
            self.warn(file, line, code, msg)

    # ---- lectura --------------------------------------------------------------------------------------------------
    def path(self, name):
        return self.dir / name

    def exists(self, name):
        return self.path(name).is_file()

    def read(self, name):
        """Lista de (n.o de linea, texto) sin BOM ni fin de linea; vacia si falta o es ilegible."""
        if name in self.cache:
            return self.cache[name]
        p = self.path(name)
        out: list[tuple[int, str]] = []
        if p.is_file():
            raw = p.read_bytes()
            if raw.startswith(b"\xef\xbb\xbf"):
                raw = raw[3:]
            text = raw.decode("utf-8", errors="replace")
            lines = re.split(r"\r\n|\n|\r", text)
            if lines and lines[-1] == "":
                lines.pop()
            out = list(enumerate(lines, 1))
        self.cache[name] = out
        return out

    def check_encoding(self, name, strict):
        p = self.path(name)
        raw = p.read_bytes()
        emit = self.err if (strict and not self.legacy) else self.warn
        if len(raw) == 0:
            return
        if not raw.startswith(b"\xef\xbb\xbf"):
            emit(name, 1, "ENC_NO_BOM", "falta el BOM UTF-8 (EF BB BF)")
        body = raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw
        if b"\xef\xbb\xbf" in body:
            emit(name, None, "ENC_BOM_INTERNAL", "BOM embebido en el interior del archivo")
        try:
            txt = body.decode("utf-8")
        except UnicodeDecodeError as e:
            self.err(name, None, "ENCODING", f"UTF-8 invalido: {e}")
            return
        if "�" in txt:
            line = txt[:txt.index("�")].count("\n") + 1
            self.err(name, line, "ENC_REPLACEMENT_CHAR", "contiene U+FFFD (texto corrupto)")
        crlf = body.count(b"\r\n")
        lone_lf = body.count(b"\n") - crlf
        lone_cr = body.count(b"\r") - crlf
        if lone_lf:
            m = re.search(rb"(?<!\r)\n", body)
            first = body[:m.start()].count(b"\n") + 1
            emit(name, first, "ENC_LF", f"{lone_lf} saltos de linea LF sin CR (se exige CRLF)")
        if lone_cr:
            emit(name, None, "ENC_CR", f"{lone_cr} CR sueltos")
        if body and not body.endswith(b"\r\n"):
            emit(name, None, "ENC_NO_FINAL_CRLF", "el archivo no termina en CRLF")

    # ---- carga de definiciones -------------------------------------------------------------------------------------
    def load_types(self):
        for n, l in self.read("types.txt"):
            m = re.match(r"^\s*InternalName\s*=\s*(\w+)", l)
            if m:
                self.types.add(m.group(1))

    def load_trainer_types(self):
        for n, l in self.read("trainertypes.txt"):
            l = prepline(l)
            if not l or l.startswith("#"):
                continue
            try:
                f = csv_fields(l)
            except ValueError:
                continue
            if len(f) >= 2:
                self.trainer_types.add(f[1])

    def load_pruned(self):
        """Objetos podados = items de PBS_backup_original no presentes en proposed_items.txt."""
        if self.legacy:
            return
        bi, pi = self.backup / "items.txt", self.docs / "proposed_items.txt"
        if not bi.is_file() or not pi.is_file():
            self.warn("items.txt", None, "PRUNED_SET_UNAVAILABLE",
                      "no se pudo calcular el conjunto de objetos podados (falta PBS_backup_original/items.txt o proposed_items.txt)")
            return

        def syms(p):
            s = set()
            raw = p.read_bytes().decode("utf-8-sig")
            for l in re.split(r"\r?\n", raw):
                if l.strip() and not l.startswith("#"):
                    try:
                        s.add(csv_fields(l)[1])
                    except (ValueError, IndexError):
                        pass
            return s
        self.pruned = syms(bi) - syms(pi)
        self.stats["pruned_items_reference_set"] = len(self.pruned)
        self.stats["proposed_items_reference_set"] = len(syms(pi))

    def load_rarity(self):
        """Rareza por objeto (Vol. 9 Cap. 2) para el aviso de objetos Tier 1/2 en WildItem*."""
        md = self.docs / "9_Items_and_Economy_Master_Guide.md"
        if self.legacy or not md.is_file():
            return
        L = md.read_text(encoding="utf-8").split("\n")
        try:
            a = next(i for i, l in enumerate(L) if l.startswith("# Capítulo 2"))
            b = next(i for i, l in enumerate(L) if l.startswith("# Capítulo 3"))
        except StopIteration:
            return
        by_id = {}
        for l in L[a:b]:
            if l.startswith("|"):
                c = [x.strip() for x in l.strip().strip("|").split("|")]
                if len(c) >= 7 and c[0].isdigit():
                    by_id[int(c[0])] = c[3]
        for sym, iid in self.items.items():
            if 288 <= iid <= 387:
                self.rarity[sym] = "Tier 1"
            elif iid in by_id:
                r = by_id[iid]
                self.rarity[sym] = ("Tier 1" if r.startswith("Tier 1") else "Tier 2" if r.startswith("Tier 2")
                                    else "Tier 3" if r.startswith("Tier 3") else "Otro")

    # ---- referencias -----------------------------------------------------------------------------------------------
    def ref_item(self, name, line, sym, ctx):
        if sym in self.items:
            return True
        if sym in self.pruned:
            self.err(name, line, "PRUNED_ITEM_REF", f"{ctx}: referencia al objeto podado {sym}")
        else:
            self.err(name, line, "UNKNOWN_ITEM", f"{ctx}: objeto inexistente {sym!r}")
        return False

    def ref_move(self, name, line, sym, ctx):
        if sym in self.moves:
            return True
        self.err(name, line, "UNKNOWN_MOVE", f"{ctx}: movimiento inexistente {sym!r}")
        return False

    def ref_ability(self, name, line, sym, ctx):
        if sym in self.abilities:
            return True
        self.err(name, line, "UNKNOWN_ABILITY", f"{ctx}: habilidad inexistente {sym!r}")
        return False

    def ref_type(self, name, line, sym, ctx):
        if sym in self.types:
            return True
        self.err(name, line, "UNKNOWN_TYPE", f"{ctx}: tipo inexistente {sym!r}")
        return False

    def ref_species(self, name, line, sym, ctx, exact=True):
        """exact=True: const_defined? exacto (Evolutions/btpokemon). exact=False: parseSpecies (upcase + NIDORAN)."""
        s = sym
        if not exact:
            s = sym.strip().upper()
            if s == "NIDORANMA":
                s = "NIDORANmA"
            if s == "NIDORANFE":
                s = "NIDORANfE"
        if s in self.species:
            return True
        self.err(name, line, "UNKNOWN_SPECIES", f"{ctx}: especie inexistente {sym!r}")
        return False

    # ==================================================================================================================
    # archivos
    # ==================================================================================================================
    def check_abilities(self):
        name = "abilities.txt"
        if not self.exists(name):
            self.err(name, None, "FILE_MISSING", "falta abilities.txt")
            return
        ids = {}
        for n, raw in self.read(name):
            line = prepline(raw)
            if not line or line.startswith("#"):
                continue
            if "#" in raw:
                self.err(name, n, "HASH_IN_LINE", "'#' en una linea de datos (prepline truncaria la descripcion)")
            try:
                f = csv_fields(line)
            except ValueError as e:
                self.err(name, n, "BAD_LINE", f"CSV invalido: {e}")
                continue
            if len(f) != 4:
                self.err(name, n, "BAD_FIELD_COUNT", f"{len(f)} campos (se esperan 4: ID,SIMBOLO,Nombre,\"Descripcion\")")
                continue
            iid = to_int(f[0])
            if iid is None or iid <= 0:
                self.err(name, n, "BAD_NUMBER", f"ID invalido {f[0]!r}")
                continue
            if not SYMBOL_RE.match(f[1]):
                self.err(name, n, "BAD_NAME", f"simbolo invalido {f[1]!r}")
            if f[1] in self.abilities:
                self.err(name, n, "DUPLICATE_SYMBOL", f"simbolo duplicado {f[1]}")
            if iid in ids:
                self.err(name, n, "DUPLICATE_ID", f"ID {iid} duplicado ({ids[iid]} y {f[1]})")
            ids[iid] = f[1]
            if not f[2]:
                self.err(name, n, "MISSING_FIELD", "nombre vacio")
            if not f[3]:
                self.warn(name, n, "EMPTY_DESCRIPTION", f"descripcion vacia en {f[1]}")
            self.abilities[f[1]] = iid
        self.stats["abilities"] = len(ids)
        self.stats["abilities_max_id"] = max(ids) if ids else 0
        if ids and sorted(ids) != list(range(1, len(ids) + 1)):
            self.warn(name, None, "NON_CONTIGUOUS_IDS", "los IDs de habilidades no son 1..N consecutivos")
        if not self.legacy:
            for n, raw in self.read(name):
                if re.search(r"(?i)granizo|graniza", raw):
                    self.warn(name, n, "DESIGN_HAIL_WORDING", "la descripcion aun habla de granizo (Vol. 2: la Nieve sustituye al Granizo)")

    def check_moves(self):
        name = "moves.txt"
        if not self.exists(name):
            self.err(name, None, "FILE_MISSING", "falta moves.txt")
            return
        ids = {}
        n_status0 = 0
        for n, raw in self.read(name):
            line = prepline(raw)
            if not line or line.startswith("#"):
                continue
            if "#" in raw:
                self.err(name, n, "HASH_IN_LINE", "'#' en una linea de datos (prepline truncaria la descripcion)")
            try:
                f = csv_fields(line)
            except ValueError as e:
                self.err(name, n, "BAD_LINE", f"CSV invalido: {e}")
                continue
            if len(f) != 14:
                self.err(name, n, "BAD_FIELD_COUNT", f"{len(f)} campos (se esperan 14); el compilador leeria mal la descripcion")
                if len(f) < 14:
                    continue
            iid = to_int(f[0])
            if iid is None or iid <= 0:
                self.err(name, n, "BAD_NUMBER", f"ID invalido {f[0]!r}")
                continue
            if not SYMBOL_RE.match(f[1]):
                self.err(name, n, "BAD_NAME", f"simbolo invalido {f[1]!r}")
            if f[1] in self.moves:
                self.err(name, n, "DUPLICATE_SYMBOL", f"simbolo duplicado {f[1]}")
            if iid in ids:
                self.err(name, n, "DUPLICATE_ID", f"ID {iid} duplicado")
            ids[iid] = f[1]
            self.moves[f[1]] = iid
            if not f[2]:
                self.err(name, n, "MISSING_FIELD", f"{f[1]}: nombre vacio")
            if not re.fullmatch(r"[A-Fa-f0-9]+", f[3]) or int(f[3], 16) > 0xFFFF:
                self.err(name, n, "BAD_FUNCTION_CODE", f"{f[1]}: codigo de funcion invalido {f[3]!r}")
            for idx, label, lo, hi in ((4, "danio base", 0, 255), (7, "precision", 0, 255), (8, "PP", 0, 255), (9, "prob. efecto", 0, 255)):
                v = to_int(f[idx])
                if v is None or not (lo <= v <= hi) or not f[idx].isdigit():
                    self.err(name, n, "BAD_NUMBER", f"{f[1]}: {label} invalido {f[idx]!r} (0-255)")
            if not re.fullmatch(r"[A-Fa-f0-9]+", f[10]) or int(f[10], 16) > 0xFFFF:
                self.err(name, n, "BAD_TARGET", f"{f[1]}: objetivo invalido {f[10]!r}")
            pr = to_int(f[11])
            if pr is None or not (-128 <= pr <= 127):
                self.err(name, n, "BAD_NUMBER", f"{f[1]}: prioridad invalida {f[11]!r}")
            if f[5] not in self.types:
                self.err(name, n, "UNKNOWN_TYPE", f"{f[1]}: tipo inexistente {f[5]!r}")
            if f[6] not in MOVE_CATEGORIES:
                self.err(name, n, "BAD_CATEGORY", f"{f[1]}: categoria invalida {f[6]!r}")
            elif f[4].isdigit():
                p = int(f[4])
                if f[6] == "Status" and p != 0:
                    self.err(name, n, "STATUS_WITH_POWER", f"{f[1]}: movimiento de Estado con danio base {p} (el compilador falla)")
                if f[6] != "Status" and p == 0:
                    self.warn(name, n, "DAMAGING_WITHOUT_POWER", f"{f[1]}: Fisico/Especial con danio base 0 (el compilador lo convierte en Estado)")
                if f[6] == "Status":
                    n_status0 += 1
            if re.search(r"[^a-p]", f[12]):
                self.warn(name, n, "BAD_FLAGS", f"{f[1]}: banderas fuera de a-p: {f[12]!r}")
            if not f[13]:
                self.warn(name, n, "EMPTY_DESCRIPTION", f"{f[1]}: descripcion vacia")
        self.stats["moves"] = len(ids)
        self.stats["moves_max_id"] = max(ids) if ids else 0

    def check_items(self):
        name = "items.txt"
        if not self.exists(name):
            self.err(name, None, "FILE_MISSING", "falta items.txt")
            return
        ids = {}
        rows = []
        for n, raw in self.read(name):
            if not raw.strip() or raw.startswith("#"):
                continue
            try:
                f = csv_fields(raw)
            except ValueError as e:
                self.err(name, n, "BAD_LINE", f"CSV invalido: {e}")
                continue
            if len(f) not in (10, 11):
                self.err(name, n, "BAD_FIELD_COUNT", f"{len(f)} campos (se esperan 11: ID,SIMBOLO,Nombre,Plural,Bolsillo,Precio,\"Desc\",UsoCampo,UsoCombate,Especial[,Movimiento])")
                continue
            if len(f) == 10:
                self.warn(name, n, "SHORT_LINE", f"{f[1]}: 10 campos (falta la coma del campo Move; valido pero irregular)")
                f = f + [""]
            iid = to_int(f[0])
            if iid is None or iid <= 0:
                self.err(name, n, "BAD_NUMBER", f"ID invalido {f[0]!r}")
                continue
            if not SYMBOL_RE.match(f[1]):
                self.err(name, n, "BAD_NAME", f"simbolo invalido {f[1]!r}")
            if f[1] in self.items:
                self.err(name, n, "DUPLICATE_SYMBOL", f"simbolo duplicado {f[1]}")
            if iid in ids:
                self.err(name, n, "DUPLICATE_ID", f"ID {iid} duplicado ({ids[iid]} y {f[1]})")
            ids[iid] = f[1]
            self.items[f[1]] = iid
            self.item_rows[f[1]] = f
            if not f[2] or not f[3]:
                self.err(name, n, "MISSING_FIELD", f"{f[1]}: nombre o plural vacio")
            for idx, label in ((4, "bolsillo"), (5, "precio"), (7, "uso en campo"), (8, "uso en combate")):
                if not f[idx].isdigit():
                    self.err(name, n, "BAD_NUMBER", f"{f[1]}: {label} invalido {f[idx]!r}")
            if f[4].isdigit() and int(f[4]) not in POCKETS:
                self.err(name, n, "BAD_POCKET", f"{f[1]}: bolsillo {f[4]} fuera de 1-8")
            if f[9] != "" and not f[9].isdigit():
                self.err(name, n, "BAD_NUMBER", f"{f[1]}: campo Especial invalido {f[9]!r}")
            if not f[6]:
                self.warn(name, n, "EMPTY_DESCRIPTION", f"{f[1]}: descripcion vacia")
            rows.append((n, f))
        # Move (despues de conocer moves.txt)
        self._item_rows_for_moves = rows
        self.stats["items"] = len(ids)
        self.stats["items_max_id"] = max(ids) if ids else 0
        self.stats["items_id_gaps"] = (max(ids) - len(ids)) if ids else 0
        # el campo ITEMUSE 3/4 = MT/MO
        self.stats["items_tm"] = sum(1 for s in self.items if re.fullmatch(r"TM\d{2,3}", s))

    def check_items_moves(self):
        name = "items.txt"
        for n, f in getattr(self, "_item_rows_for_moves", []):
            mv = f[10]
            if mv != "":
                self.ref_move(name, n, mv.strip().upper(), f"{f[1]} (campo Move)")
            if f[7] in ("3", "4") and mv == "":
                self.err(name, n, "TM_WITHOUT_MOVE", f"{f[1]}: MT/MO (uso en campo {f[7]}) sin movimiento")
        if not self.legacy and self.pruned:
            extra = [s for s in self.items if s in self.pruned]
            for s in extra:
                self.err(name, None, "PRUNED_ITEM_DEFINED", f"el objeto podado {s} sigue definido en items.txt")
        # comparacion con el diseno
        pi = self.docs / "proposed_items.txt"
        if not self.legacy and pi.is_file():
            ps = set()
            for l in re.split(r"\r?\n", pi.read_bytes().decode("utf-8-sig")):
                if l.strip() and not l.startswith("#"):
                    try:
                        ps.add(csv_fields(l)[1])
                    except (ValueError, IndexError):
                        pass
            if ps != set(self.items):
                a, b = sorted(set(self.items) - ps), sorted(ps - set(self.items))
                self.design(name, None, "DESIGN_ITEMS_DIFFER",
                            f"items.txt difiere de proposed_items.txt: sobran {a[:6]}{'...' if len(a) > 6 else ''}, faltan {b[:6]}{'...' if len(b) > 6 else ''}")

    def check_berryplants(self):
        name = "berryplants.txt"
        if not self.exists(name):
            self.warn(name, None, "FILE_MISSING", "falta berryplants.txt (opcional)")
            return
        seen = set()
        count = 0
        for n, raw in self.read(name):
            if not raw.strip() or raw.startswith("#"):
                continue
            m = re.match(r"^([^=]+)=(.*)$", raw)
            if not m:
                self.warn(name, n, "IGNORED_LINE", "linea sin 'CLAVE=valores' (el compilador la ignora)")
                continue
            key = m.group(1).strip().upper()
            vals = [v.strip() for v in m.group(2).split(",")]
            if len(vals) != 4 or not all(v.isdigit() for v in vals):
                self.err(name, n, "BAD_FIELD_COUNT", f"{key}: se esperan 4 enteros (horas/etapa, secado/hora, cosecha min, max), hay {vals}")
            elif int(vals[2]) > int(vals[3]):
                self.warn(name, n, "BAD_RANGE", f"{key}: cosecha minima {vals[2]} > maxima {vals[3]}")
            self.ref_item(name, n, key, "baya")
            if key in seen:
                self.warn(name, n, "DUPLICATE_KEY", f"{key} repetida (gana la ultima)")
            seen.add(key)
            count += 1
        self.stats["berryplants"] = count

    # ---- pokemon.txt -----------------------------------------------------------------------------------------------
    REQUIRED = ["Name", "Kind", "InternalName", "Pokedex", "Moves", "Color", "Type1", "BaseStats", "Rareness",
                "GenderRate", "Happiness", "GrowthRate", "StepsToHatch", "EffortPoints", "Compatibility", "Height",
                "Weight", "BaseEXP"]

    def parse_pokemon(self):
        """Lee las secciones numericas de pokemon.txt como pbEachFileSection. Devuelve {num: (linea, {clave: (linea, valor)})}."""
        name = "pokemon.txt"
        secs: "OrderedDict[int, tuple[int, dict]]" = OrderedDict()
        cur = None
        cur_name = None
        for n, raw in self.read(name):
            if not raw.strip() or raw.startswith("#"):
                continue
            m = re.match(r"^\s*\[\s*(.*?)\s*\]\s*$", raw)
            if m:
                cur_name = m.group(1)
                if re.fullmatch(r"\d+", cur_name):
                    num = int(cur_name)
                    if num in secs:
                        self.err(name, n, "DUPLICATE_SECTION", f"seccion [{num}] duplicada")
                    cur = {}
                    secs[num] = (n, cur)
                else:
                    cur = None
                    self.warn(name, n, "IGNORED_SECTION", f"seccion no numerica [{cur_name}] (el compilador la ignora)")
                continue
            if cur_name is None:
                self.err(name, n, "BAD_LINE", "linea antes de la primera seccion")
                continue
            m = re.match(r"^\s*(\w+)\s*=\s*(.*)$", raw)
            if not m:
                self.err(name, n, "BAD_LINE", f"se esperaba CLAVE=VALOR: {raw[:60]!r}")
                continue
            if cur is None:
                continue
            key, val = m.group(1), re.sub(r"\s+$", "", m.group(2))
            if key in cur:
                self.warn(name, n, "DUPLICATE_KEY", f"[{list(secs)[-1]}] clave {key} repetida (gana la ultima)")
            cur[key] = (n, val)
        return secs

    def check_pokemon(self):
        name = "pokemon.txt"
        if not self.exists(name):
            self.err(name, None, "FILE_MISSING", "falta pokemon.txt")
            return
        secs = self.parse_pokemon()
        self.pokemon_secs = secs
        # primera pasada: simbolos de especie
        for num, (ln, d) in secs.items():
            if "InternalName" in d and d["InternalName"][1]:
                s = d["InternalName"][1]
                if not re.fullmatch(r"(?![0-9])\w*", s):
                    self.err(name, d["InternalName"][0], "BAD_NAME", f"[{num}] InternalName invalido {s!r}")
                if s in self.species:
                    self.err(name, d["InternalName"][0], "DUPLICATE_SYMBOL", f"[{num}] InternalName {s} repetido (ya en [{self.species[s]}])")
                self.species[s] = num
                self.species_by_num[num] = s
        nums = list(secs)
        if nums != list(range(1, len(nums) + 1)):
            self.warn(name, None, "NON_CONTIGUOUS_IDS", "las secciones de pokemon.txt no son 1..N consecutivas y ordenadas")
        stats = Counter()
        for num, (ln, d) in secs.items():
            roster = num <= ROSTER_MAX
            if num == 0:
                self.err(name, ln, "BAD_ID", "una especie no puede numerarse como 0")

            def val(k):
                return d[k][1] if k in d else None

            def lno(k):
                return d[k][0] if k in d else ln
            for k in self.REQUIRED:
                if k == "Type1":
                    continue
                if k not in d or d[k][1] == "":
                    self.err(name, ln, "MISSING_FIELD", f"[{num}] falta el valor obligatorio {k}")
            if "Type1" not in d or d["Type1"][1] == "":
                self.err(name, ln, "MISSING_FIELD", f"[{num}] sin Type1")
            else:
                self.ref_type(name, lno("Type1"), val("Type1"), f"[{num}] Type1")
            if val("Type2"):
                self.ref_type(name, lno("Type2"), val("Type2"), f"[{num}] Type2")
            for k in ("Name", "Kind"):
                if val(k) is not None and len(val(k)) > 20:
                    self.err(name, lno(k), "TOO_LONG", f"[{num}] {k} tiene {len(val(k))} caracteres (max 20)")
            # numericos
            bs = (val("BaseStats") or "").split(",")
            if val("BaseStats") is not None:
                if len(bs) != 6 or not all(x.strip().isdigit() and int(x) <= 255 for x in bs):
                    self.err(name, lno("BaseStats"), "BAD_BASESTATS", f"[{num}] BaseStats debe ser 6 enteros 0-255: {val('BaseStats')!r}")
            ep = (val("EffortPoints") or "").split(",")
            if val("EffortPoints") is not None and (len(ep) != 6 or not all(x.strip().isdigit() and int(x) <= 255 for x in ep)):
                self.err(name, lno("EffortPoints"), "BAD_NUMBER", f"[{num}] EffortPoints debe ser 6 enteros 0-255")
            for k, hi in (("Rareness", 255), ("Happiness", 255), ("StepsToHatch", 65535), ("BaseEXP", 65535)):
                if val(k) is not None and not (val(k).isdigit() and int(val(k)) <= hi):
                    self.err(name, lno(k), "BAD_NUMBER", f"[{num}] {k} invalido {val(k)!r} (0-{hi})")
            for k in ("Height", "Weight"):
                if val(k):
                    try:
                        fv = float(val(k))
                        if round(fv * 10) <= 0 or round(fv * 10) > 65535:
                            raise ValueError
                    except ValueError:
                        self.err(name, lno(k), "BAD_NUMBER", f"[{num}] {k} invalido {val(k)!r}")
            if val("GenderRate") and val("GenderRate") not in GENDER_RATES:
                self.err(name, lno("GenderRate"), "BAD_ENUM", f"[{num}] GenderRate {val('GenderRate')!r}")
            if val("GrowthRate") and val("GrowthRate") not in GROWTH_RATES:
                self.err(name, lno("GrowthRate"), "BAD_ENUM", f"[{num}] GrowthRate {val('GrowthRate')!r}")
            if val("Color") and val("Color") not in COLORS:
                self.err(name, lno("Color"), "BAD_ENUM", f"[{num}] Color {val('Color')!r}")
            if val("Habitat") is not None and val("Habitat") not in HABITATS:
                self.err(name, lno("Habitat"), "BAD_ENUM", f"[{num}] Habitat {val('Habitat')!r}")
            if val("Compatibility"):
                eg = val("Compatibility").split(",")
                if not (1 <= len(eg) <= 2) or any(x.strip() not in EGG_GROUPS for x in eg):
                    self.err(name, lno("Compatibility"), "BAD_ENUM", f"[{num}] Compatibility {val('Compatibility')!r}")
            for k in ("BattlerPlayerY", "BattlerEnemyY", "BattlerAltitude"):
                if val(k) is not None and to_int(val(k)) is None:
                    self.err(name, lno(k), "BAD_NUMBER", f"[{num}] {k} invalido {val(k)!r}")
            if val("RegionalNumbers"):
                if not all(x.strip().isdigit() for x in val("RegionalNumbers").split(",")):
                    self.err(name, lno("RegionalNumbers"), "BAD_NUMBER", f"[{num}] RegionalNumbers invalido")
            # habilidades
            if val("Abilities"):
                ab = [x.strip() for x in val("Abilities").split(",")]
                if len(ab) > 2:
                    self.err(name, lno("Abilities"), "TOO_MANY_ABILITIES", f"[{num}] Abilities con {len(ab)} simbolos (solo se leen 2)")
                for a in ab:
                    if a:
                        self.ref_ability(name, lno("Abilities"), a, f"[{num}] Abilities")
                if roster and not self.legacy and not (1 <= len([a for a in ab if a]) <= 2):
                    self.err(name, lno("Abilities"), "ABILITY_COUNT", f"[{num}] Abilities debe llevar 1 o 2 habilidades")
                stats["abilities_1"] += len([a for a in ab if a]) == 1
                stats["abilities_2"] += len([a for a in ab if a]) == 2
            elif roster:
                self.err(name, ln, "MISSING_FIELD", f"[{num}] sin Abilities")
            if val("HiddenAbility"):
                ha = [x.strip() for x in val("HiddenAbility").split(",")]
                if len(ha) > 4:
                    self.err(name, lno("HiddenAbility"), "TOO_MANY_ABILITIES", f"[{num}] HiddenAbility con {len(ha)} simbolos (solo 4)")
                for a in ha:
                    if a:
                        self.ref_ability(name, lno("HiddenAbility"), a, f"[{num}] HiddenAbility")
                if roster:
                    self.design(name, lno("HiddenAbility"), "DESIGN_HIDDEN_ABILITY", f"[{num}] HiddenAbility residual en el plantel (Vol. 2: fusionada en Abilities)")
            # movimientos
            mv = val("Moves")
            if mv:
                f = [x.strip() for x in mv.split(",")]
                if len(f) % 2:
                    self.err(name, lno("Moves"), "BAD_MOVES", f"[{num}] Moves con numero impar de campos")
                for i in range(0, len(f) - 1, 2):
                    if not f[i].isdigit():
                        self.err(name, lno("Moves"), "BAD_MOVES", f"[{num}] nivel invalido {f[i]!r}")
                    elif int(f[i]) > MAXLEVEL:
                        self.warn(name, lno("Moves"), "BAD_MOVES", f"[{num}] nivel {f[i]} > {MAXLEVEL}")
                    self.ref_move(name, lno("Moves"), f[i + 1], f"[{num}] Moves")
                stats["level_moves"] += len(f) // 2
            if val("EggMoves"):
                for m_ in val("EggMoves").split(","):
                    self.ref_move(name, lno("EggMoves"), m_.strip(), f"[{num}] EggMoves")
                if roster:
                    self.design(name, lno("EggMoves"), "DESIGN_EGGMOVES", f"[{num}] EggMoves residual en el plantel (Vol. 4: fusionados en Moves)")
            # objetos salvajes
            for k in ("WildItemCommon", "WildItemUncommon", "WildItemRare", "Incense"):
                if val(k):
                    ok = self.ref_item(name, lno(k), val(k), f"[{num}] {k}")
                    if ok and self.rarity.get(val(k)) in ("Tier 1", "Tier 2", "Otro"):
                        self.design(name, lno(k), "DESIGN_WILD_TIER", f"[{num}] {k}={val(k)}: objeto {self.rarity[val(k)]} llevado por un Pokemon salvaje (Vol. 9 Sec. 6.4.1)")
            # evoluciones (segunda pasada de simbolos de especie ya hecha)
            ev = val("Evolutions")
            if ev:
                f = [x.strip() for x in ev.split(",")]
                if len(f) % 3 == 2:
                    f.append("")
                if len(f) % 3:
                    self.err(name, lno("Evolutions"), "BAD_EVOLUTION", f"[{num}] Evolutions con {len(f)} campos (se esperan multiplos de 3)")
                for i in range(0, len(f) - 2, 3):
                    sp, meth, par = f[i], f[i + 1], f[i + 2]
                    if sp not in self.species:
                        self.err(name, lno("Evolutions"), "UNKNOWN_SPECIES", f"[{num}] Evolutions: especie inexistente {sp!r}")
                    elif roster and self.species[sp] > ROSTER_MAX:
                        self.warn(name, lno("Evolutions"), "ROSTER_BOUNDARY", f"[{num}] evoluciona a {sp} (#{self.species[sp]}), fuera del plantel #001-#721")
                    if meth not in EVONAMES:
                        self.err(name, lno("Evolutions"), "BAD_EVOLUTION", f"[{num}] metodo de evolucion desconocido {meth!r}")
                        continue
                    pt = EVOPARAM[EVONAMES.index(meth)]
                    if pt == 1 and not par.isdigit():
                        self.err(name, lno("Evolutions"), "BAD_EVOLUTION", f"[{num}] {meth} requiere un entero positivo, hay {par!r}")
                    elif pt == 2:
                        self.ref_item(name, lno("Evolutions"), par, f"[{num}] Evolutions {meth}")
                        stats["evolutions_by_item"] += 1
                    elif pt == 3:
                        self.ref_move(name, lno("Evolutions"), par, f"[{num}] Evolutions {meth}")
                    elif pt == 4 and par not in self.species:
                        self.err(name, lno("Evolutions"), "UNKNOWN_SPECIES", f"[{num}] Evolutions {meth}: especie inexistente {par!r}")
                    elif pt == 5:
                        self.ref_type(name, lno("Evolutions"), par, f"[{num}] Evolutions {meth}")
                stats["evolution_entries"] += len(f) // 3
        self.stats["species"] = len(secs)
        self.stats["species_roster_1_721"] = sum(1 for n in secs if n <= ROSTER_MAX)
        self.stats["species_outside_roster"] = sum(1 for n in secs if n > ROSTER_MAX)
        self.stats["species_with_1_ability"] = stats["abilities_1"]
        self.stats["species_with_2_abilities"] = stats["abilities_2"]
        self.stats["level_up_move_entries"] = stats["level_moves"]
        self.stats["evolution_entries"] = stats["evolution_entries"]
        self.stats["evolutions_by_item"] = stats["evolutions_by_item"]

    # ---- tm.txt ---------------------------------------------------------------------------------------------------
    def check_tm(self):
        name = "tm.txt"
        if not self.exists(name):
            self.err(name, None, "FILE_MISSING", "falta tm.txt")
            return
        blocks = []        # (linea, movimiento, [especies])
        cur = None
        for n, raw in self.read(name):
            if raw.startswith("#") or not raw.strip():
                continue
            m = re.match(r"^\s*\[\s*(.*)\s*\]\s*$", raw)
            if m:
                mv = m.group(1).strip().upper()
                if mv not in self.moves:
                    self.err(name, n, "UNKNOWN_MOVE", f"seccion de MT con movimiento inexistente {m.group(1)!r}")
                cur = [n, mv, []]
                blocks.append(cur)
                continue
            if cur is None:
                self.err(name, n, "BAD_LINE", "especies antes de la primera seccion [MOVIMIENTO]")
                continue
            for s in re.sub(r"\s+$", "", raw).split(","):
                if s == "" or s.strip() == "":
                    continue
                self.ref_species(name, n, s, f"[{cur[1]}]", exact=False)
                cur[2].append(s.strip().upper() if s.strip().upper() not in ("NIDORANMA", "NIDORANFE") else {"NIDORANMA": "NIDORANmA", "NIDORANFE": "NIDORANfE"}[s.strip().upper()])
        seen = Counter(b[1] for b in blocks)
        for mv, c in seen.items():
            if c > 1:
                line = next(b[0] for b in blocks if b[1] == mv)
                self.warn(name, line, "DUPLICATE_SECTION", f"movimiento {mv} con {c} secciones (la ultima sustituye a las anteriores)")
        for ln, mv, sp in blocks:
            if len(sp) != len(set(sp)):
                self.warn(name, ln, "DUPLICATE_SPECIES", f"[{mv}] especies repetidas")
            if not self.legacy:
                out = [s for s in sp if self.species.get(s, 0) > ROSTER_MAX]
                if out:
                    self.warn(name, ln, "ROSTER_BOUNDARY", f"[{mv}] incluye especies fuera del plantel: {out[:5]}")
        self.stats["tm_sections"] = len(blocks)
        self.stats["tm_species_pairs"] = sum(len(b[2]) for b in blocks)
        # MT <-> bloque n-esimo
        tm_items = sorted((int(re.fullmatch(r"TM(\d+)", s).group(1)), s) for s in self.items if re.fullmatch(r"TM\d{2,3}", s))
        section_moves = {b[1] for b in blocks}
        emit = self.warn if self.legacy else self.err
        for num, sym in tm_items:
            mv = self.item_rows[sym][10].upper()
            if mv and mv not in section_moves:
                emit(name, None, "TM_WITHOUT_SECTION", f"{sym} usa {mv}, que no tiene seccion [{mv}] en tm.txt")
            if not self.legacy and num <= len(blocks) and blocks[num - 1][1] != mv:
                self.err(name, blocks[num - 1][0], "TM_ORDER_MISMATCH", f"el bloque n.o {num} es [{blocks[num - 1][1]}] pero {sym} apunta a {mv}")
        if not self.legacy:
            if len(tm_items) != len(blocks):
                self.design(name, None, "DESIGN_TM_COUNT", f"{len(tm_items)} objetos TMxx pero {len(blocks)} bloques en tm.txt")
            # Vol. 5: todo Pokemon que aprende el movimiento por nivel es compatible con su MT
            learners = defaultdict(set)
            for num, (pl, d) in getattr(self, "pokemon_secs", {}).items():
                if "Moves" in d:
                    f = [x.strip() for x in d["Moves"][1].split(",")]
                    for i in range(1, len(f), 2):
                        learners[f[i]].add(num)
            reach = []
            for ln, mv, sp in blocks:
                nums = {self.species[s] for s in sp if s in self.species}
                reach.append(len(nums))
                miss = sorted(n for n in learners.get(mv, ()) if n <= ROSTER_MAX and n not in nums)
                if miss:
                    self.design(name, ln, "DESIGN_TM_LEARNER_MISSING",
                                f"[{mv}] {len(miss)} especies lo aprenden por nivel pero no estan en su MT: {[self.species_by_num[n] for n in miss[:5]]}")
            if reach:
                self.stats["tm_min_reach"] = min(reach)
        self.stats["tm_items_checked"] = len(tm_items)

    # ---- trainers / trainertypes / cups ---------------------------------------------------------------------------
    def check_trainertypes(self):
        name = "trainertypes.txt"
        if not self.exists(name):
            return
        ids = {}
        for n, raw in self.read(name):
            line = prepline(raw)
            if not line or line.startswith("#"):
                continue
            try:
                f = csv_fields(line)
            except ValueError as e:
                self.err(name, n, "BAD_LINE", f"CSV invalido: {e}")
                continue
            if len(f) < 3 or not f[0].isdigit() or not SYMBOL_RE.match(f[1]):
                self.err(name, n, "BAD_LINE", f"se esperaba ID,SIMBOLO,Nombre,...: {line[:60]!r}")
                continue
            if int(f[0]) in ids:
                self.err(name, n, "DUPLICATE_ID", f"tipo de entrenador {f[1]} y {ids[int(f[0])]} comparten ID {f[0]}")
            ids[int(f[0])] = f[1]
        self.stats["trainer_types"] = len(ids)

    def check_trainers(self):
        name = "trainers.txt"
        if not self.exists(name):
            return
        lines = [(n, prepline(raw)) for n, raw in self.read(name)]
        lines = [(n, l) for n, l in lines if l != "" and not l.startswith("#")]
        i = 0
        count = 0
        while i < len(lines):
            n, l = lines[i]
            tname = l.strip()
            if tname not in self.trainer_types:
                self.err(name, n, "UNKNOWN_TRAINER_TYPE", f"tipo de entrenador inexistente {tname!r}")
            if i + 2 >= len(lines):
                self.err(name, n, "BAD_LINE", "bloque de entrenador incompleto")
                break
            hdr = re.split(r"\s*,\s*", lines[i + 1][1])
            if len(hdr) > 1 and hdr[1] and not hdr[1].isdigit():
                self.err(name, lines[i + 1][0], "BAD_NUMBER", "ID de batalla no numerico")
            items = re.split(r"\s*,\s*", lines[i + 2][1])
            if not items[0].strip().isdigit():
                self.err(name, lines[i + 2][0], "BAD_NUMBER", "cantidad de Pokemon no numerica")
                break
            npk = int(items[0])
            for it in items[1:]:
                if it:
                    self.ref_item(name, lines[i + 2][0], it, f"{tname}/{hdr[0]} objetos del entrenador")
            for j in range(npk):
                if i + 3 + j >= len(lines):
                    self.err(name, n, "BAD_LINE", "faltan lineas de Pokemon")
                    break
                pn, pl = lines[i + 3 + j]
                f = re.split(r"\s*,\s*", pl)
                self.ref_species(name, pn, f[0], f"{tname}/{hdr[0]}", exact=False)
                lvl = to_int(f[1]) if len(f) > 1 else None
                if lvl is None or not (1 <= lvl <= MAXLEVEL):
                    self.err(name, pn, "BAD_NUMBER", f"nivel invalido {f[1] if len(f) > 1 else ''!r}")
                if len(f) > 2 and f[2]:
                    self.ref_item(name, pn, f[2], f"{tname}/{hdr[0]} objeto llevado")
                for k in range(3, 7):
                    if len(f) > k and f[k]:
                        self.ref_move(name, pn, f[k].upper(), f"{tname}/{hdr[0]} movimiento")
                if len(f) > 11 and f[11] and f[11].upper() not in NATURES:
                    self.err(name, pn, "BAD_ENUM", f"naturaleza invalida {f[11]!r}")
            i += 3 + npk
            count += 1
        self.stats["trainers"] = count

    def check_pm_file(self, name):
        if not self.exists(name):
            self.warn(name, None, "FILE_MISSING", f"falta {name}")
            return
        count = 0
        for n, raw in self.read(name):
            if not raw.strip() or raw.startswith("#"):
                continue
            p = raw.strip().split(";")
            if len(p) != 5:
                self.err(name, n, "BAD_FIELD_COUNT", f"{len(p)} campos (se esperan 5: ESPECIE;OBJETO;NATURALEZA;EVS;MOVIMIENTOS)")
                continue
            count += 1
            self.ref_species(name, n, p[0], "ESPECIE", exact=True)
            if p[1] != "":
                self.ref_item(name, n, p[1], "OBJETO llevado")
            if p[2] not in NATURES:
                self.err(name, n, "BAD_ENUM", f"naturaleza invalida {p[2]!r}")
            for e in [x for x in re.split(r"\s*,\s*", p[3]) if x]:
                if e.upper() not in EV_TOKENS:
                    self.err(name, n, "BAD_ENUM", f"EV desconocido {e!r}")
            mv = re.split(r"\s*,\s*", p[4])
            real = [m for m in mv if m]
            if not real:
                self.err(name, n, "MISSING_FIELD", "sin movimientos")
            if len(mv) > 4:
                self.warn(name, n, "BAD_FIELD_COUNT", f"{len(mv)} movimientos (solo se leen 4)")
            for m in real:
                self.ref_move(name, n, m, "movimiento")
        self.pm_line_counts[name] = count
        self.stats[name.replace(".txt", "") + "_lines"] = count

    def check_trainer_lists(self):
        name = "trainerlists.txt"
        if not self.exists(name):
            return
        cur = None
        pairs = []
        for n, raw in self.read(name):
            if not raw.strip() or raw.startswith("#"):
                continue
            m = re.match(r"^\s*\[\s*(.*?)\s*\]\s*$", raw)
            if m:
                cur = {"name": m.group(1), "line": n}
                pairs.append(cur)
                continue
            m = re.match(r"^\s*(\w+)\s*=\s*(.*)$", raw)
            if not m or cur is None:
                self.err(name, n, "BAD_LINE", "se esperaba CLAVE=VALOR dentro de una seccion")
                continue
            cur[m.group(1)] = m.group(2).strip()
        for p in pairs:
            if p["name"] not in ("DefaultTrainerList", "TrainerList"):
                continue
            for k in ("Trainers", "Pokemon"):
                if not p.get(k):
                    self.err(name, p["line"], "MISSING_FIELD", f"[{p['name']}] sin {k}")
                elif not self.exists(p[k]):
                    self.err(name, p["line"], "FILE_MISSING", f"[{p['name']}] {k}={p[k]} no existe en {self.dir.name}/")
            if p.get("Trainers") and p.get("Pokemon") and self.exists(p["Trainers"]):
                self.check_bt_trainers(p["Trainers"], p.get("Pokemon"))
        self.stats["trainer_lists"] = len(pairs)

    def check_bt_trainers(self, name, pmname):
        cur = None
        count = 0
        maxno = self.pm_line_counts.get(pmname)
        for n, raw in self.read(name):
            if not raw.strip() or raw.startswith("#"):
                continue
            m = re.match(r"^\s*\[\s*(.*?)\s*\]\s*$", raw)
            if m:
                cur = m.group(1)
                count += 1
                continue
            m = re.match(r"^\s*(\w+)\s*=\s*(.*)$", raw)
            if not m:
                self.err(name, n, "BAD_LINE", f"se esperaba CLAVE=VALOR: {raw[:50]!r}")
                continue
            key, v = m.group(1), m.group(2).strip()
            if key == "Type" and v not in self.trainer_types:
                self.err(name, n, "UNKNOWN_TRAINER_TYPE", f"[{cur}] Type inexistente {v!r}")
            if key == "PokemonNos":
                nums = [x.strip() for x in v.split(",") if x.strip()]
                if not all(x.isdigit() for x in nums):
                    self.err(name, n, "BAD_NUMBER", f"[{cur}] PokemonNos no numerico")
                elif maxno is not None and nums and max(int(x) for x in nums) >= maxno:
                    self.warn(name, n, "OUT_OF_RANGE", f"[{cur}] PokemonNos hasta {max(int(x) for x in nums)} pero {pmname} tiene {maxno} equipos")
        self.stats[name.replace(".txt", "") + "_trainers"] = count

    def check_shadowmoves(self):
        name = "shadowmoves.txt"
        if not self.exists(name):
            return
        for n, raw in self.read(name):
            if not raw.strip() or raw.startswith("#"):
                continue
            m = re.match(r"^([^=]+)=(.*)$", raw)
            if not m:
                continue
            self.ref_species(name, n, m.group(1), "especie Oscura", exact=False)
            for mv in m.group(2).split(",")[:4]:
                # pbCompileShadowMoves hace `parseMove(...) rescue nil`: un movimiento inexistente se descarta en silencio
                if mv.strip() and mv.strip().upper() not in self.moves:
                    self.warn(name, n, "UNKNOWN_MOVE_IGNORED", f"movimiento Oscuro inexistente {mv.strip()!r} (el compilador lo descarta en silencio)")

    def check_encounters(self):
        name = "encounters.txt"
        if not self.exists(name):
            return
        lines = [(n, prepline(raw)) for n, raw in self.read(name)]
        lines = [(n, l) for n, l in lines if l != ""]
        i = 0
        maps = 0
        needdensity = False
        while i < len(lines):
            n, l = lines[i]
            if re.fullmatch(r"\d+", l):
                maps += 1
                needdensity = True
                i += 1
                continue
            if l in ENCOUNTER_TYPES:
                needdensity = False
                k = ENCOUNTER_TYPES[l]
                j = i + 1
                got = 0
                while j < len(lines) and got < k:
                    pn, pl = lines[j]
                    f = re.split(r"\s*,\s*", pl)
                    if len(f) < 2:
                        self.err(name, pn, "BAD_LINE", f"se esperaba 'ESPECIE,min[,max]' ({got}/{k} entradas de {l})")
                        break
                    self.ref_species(name, pn, f[0], f"encuentro {l}", exact=False)
                    lo = to_int(f[1])
                    hi = to_int(f[2]) if len(f) > 2 else lo
                    if lo is None or hi is None or not (1 <= lo <= MAXLEVEL) or not (1 <= hi <= MAXLEVEL):
                        self.err(name, pn, "BAD_NUMBER", f"nivel invalido en {pl!r}")
                    elif lo > hi:
                        self.err(name, pn, "BAD_NUMBER", f"nivel minimo > maximo en {pl!r}")
                    j += 1
                    got += 1
                if got < k and j >= len(lines):
                    self.err(name, n, "BAD_LINE", f"fin de archivo inesperado en {l}: {got}/{k} entradas")
                i = j
            elif needdensity:
                needdensity = False
                if len(l.split(",")) < 3:
                    self.err(name, n, "BAD_LINE", f"densidades invalidas {l!r}")
                i += 1
            else:
                self.err(name, n, "BAD_LINE", f"tipo de encuentro indefinido {l!r}")
                i += 1
        self.stats["encounter_maps"] = maps

    # ---- archivos rem_* (opcionales; solo referencias a objetos) -------------------------------------------------
    def check_rem_items(self):
        for fname, pat in (("rem_location_items.txt", r"^\s*Item\d+\s*=\s*([A-Za-z0-9_]+)"),
                           ("rem_shops.txt", r"^\s*(?:Item\d+\s*=\s*([A-Za-z0-9_]+)|Mission\d+\s*=\s*[^,]*,\s*([A-Za-z0-9_]+))")):
            if not self.exists(fname):
                continue
            n_ref = 0
            for n, raw in self.read(fname):
                m = re.match(pat, raw)
                if not m:
                    continue
                sym = next((g for g in m.groups() if g), None)
                if sym:
                    n_ref += 1
                    if sym not in self.items:
                        self.warn(fname, n, "PRUNED_ITEM_REF" if sym in self.pruned else "UNKNOWN_ITEM", f"objeto {sym!r} no existe en items.txt")
            self.stats[fname.replace(".txt", "") + "_item_refs"] = n_ref

    # ---- escaneo por tokens ----------------------------------------------------------------------------------------
    def scan_pruned_tokens(self):
        """Busca cualquier simbolo de objeto podado en TODOS los .txt del directorio (salvo items.txt)."""
        if self.legacy or not self.pruned:
            return
        tok = re.compile(r"(?<![A-Za-z0-9_])[A-Z][A-Z0-9_]+(?![A-Za-z0-9_])")
        reported = {(e["file"], e["line"], e["message"].split()[-1]) for e in self.errors if e["code"] == "PRUNED_ITEM_REF"}
        hits = Counter()
        for p in sorted(self.dir.glob("*.txt")):
            if p.name in SKIP_FILES or p.name == "items.txt" or p.name in PRUNED_SCAN_EXEMPT:
                continue
            for n, raw in self.read(p.name):
                if raw.startswith("#"):
                    continue
                for m in tok.finditer(raw):
                    t = m.group(0)
                    if t in self.pruned:
                        hits[p.name] += 1
                        if (p.name, n, t) not in reported:
                            self.err(p.name, n, "PRUNED_ITEM_REF", f"referencia al objeto podado {t}")
                            reported.add((p.name, n, t))
        self.stats["pruned_item_token_hits"] = dict(hits)

    # ---- orquestacion ----------------------------------------------------------------------------------------------
    def run(self):
        d = self.dir
        if not d.is_dir():
            self.err(str(d), None, "DIR_MISSING", "el directorio PBS no existe")
            return
        self.stats["legacy_mode"] = self.legacy
        self.stats["pbs_dir"] = str(d)
        self.load_types()
        self.load_trainer_types()
        self.load_pruned()
        # codificacion
        for p in sorted(d.glob("*.txt")):
            if p.name in SKIP_FILES:
                continue
            strict = p.name in CORE_FILES or p.name.startswith("rem_")
            try:
                self.check_encoding(p.name, strict)
            except OSError as e:
                self.err(p.name, None, "ENCODING", f"no se pudo leer: {e}")
        # definiciones en orden de dependencias del compilador
        self.check_abilities()
        self.check_moves()
        self.check_items()
        self.check_items_moves()
        self.load_rarity()
        self.check_berryplants()
        self.check_pokemon()
        self.check_tm()
        self.check_trainertypes()
        self.check_trainers()
        for f in PM_FILES:
            self.check_pm_file(f)
        self.check_trainer_lists()
        self.check_shadowmoves()
        self.check_encounters()
        self.check_rem_items()
        self.scan_pruned_tokens()
        self.stats["errors"] = len(self.errors)
        self.stats["warnings"] = len(self.warnings)


def check(pbs_dir=None, legacy: bool = False, backup_dir=None, docs_dir=None) -> dict:
    """Valida un directorio PBS. Devuelve {'errors': [...], 'warnings': [...], 'stats': {...}} (incidencias = dicts)."""
    c = Checker(pbs_dir or DEFAULT_PBS, legacy=legacy, backup_dir=backup_dir, docs_dir=docs_dir)
    c.run()
    return {"errors": c.errors, "warnings": c.warnings, "stats": c.stats}


# ======================================================================================================================
def render(res: dict, max_per_code: int = 12) -> str:
    out = []
    st = res["stats"]
    out.append(f"== pbs_check: {st.get('pbs_dir')} {'(modo legacy)' if st.get('legacy_mode') else ''}")
    keys = [k for k in st if k not in ("pbs_dir", "legacy_mode", "errors", "warnings")]
    for k in keys:
        out.append(f"   {k}: {st[k]}")
    for label, items in (("ERRORES", res["errors"]), ("AVISOS", res["warnings"])):
        out.append(f"-- {label}: {len(items)}")
        by = defaultdict(list)
        for it in items:
            by[(it["file"], it["code"])].append(it)
        for (f, code), lst in sorted(by.items()):
            out.append(f"   {f} [{code}] x{len(lst)}")
            for it in lst[:max_per_code]:
                out.append(f"      {('L' + str(it['line'])) if it.get('line') else '-'}: {it['message']}")
            if len(lst) > max_per_code:
                out.append(f"      ... y {len(lst) - max_per_code} mas")
    out.append("RESULTADO: " + ("OK (0 errores)" if not res["errors"] else f"FALLO ({len(res['errors'])} errores)"))
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Validador independiente de los archivos oficiales de PBS/")
    ap.add_argument("--pbs", default=str(DEFAULT_PBS), help="directorio PBS a validar (por defecto ROOT/PBS)")
    ap.add_argument("--legacy", action="store_true", help="PBS vanilla (p. ej. PBS_backup_original): objetos podados validos, BOM/CRLF/diseno como avisos")
    ap.add_argument("--backup", default=None, help="PBS_backup_original (para calcular los objetos podados)")
    ap.add_argument("--docs", default=None, help="docs/rebalance (proposed_items.txt y Vol. 9)")
    ap.add_argument("--json", action="store_true", help="imprime el resultado en JSON (en lugar del informe legible)")
    ap.add_argument("--json-out", default=None, help="ademas escribe el JSON en este archivo")
    ap.add_argument("--max", type=int, default=12, help="maximo de lineas por tipo de incidencia en el informe legible")
    ap.add_argument("--quiet", action="store_true", help="solo resumen final")
    args = ap.parse_args(argv)
    res = check(args.pbs, legacy=args.legacy, backup_dir=args.backup, docs_dir=args.docs)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    elif args.quiet:
        print(f"pbs_check {args.pbs}: {len(res['errors'])} errores, {len(res['warnings'])} avisos")
    else:
        print(render(res, args.max))
    return 1 if res["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
