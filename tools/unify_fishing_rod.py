#!/usr/bin/env python3
"""Unifica las tres cañas de pescar (OLDROD, GOODROD, SUPERROD) en una única Caña de Pescar (504, OLDROD)."""
import csv
import io
import os
import re
import shutil
import struct
import sys
import zlib
import rubymarshal.reader as r
import rubymarshal.writer as w

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from items_helper import encode_record, decode_record


ROD_NAME = "Caña de Pescar"
ROD_PLURAL = "Cañas de Pescar"
ROD_DESC = "Caña de pescar resistente para atrapar Pokémon salvajes en cualquier cuerpo de agua."
COINCASE_DESC = "Caja pequeña para guardar fichas."


def write_bom_crlf(path, lines):
    text = "\r\n".join(lines).rstrip("\r\n") + "\r\n"
    with open(path, "wb") as f:
        f.write(b"\xef\xbb\xbf")
        f.write(text.encode("utf-8"))


def read_lines_normalized(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read().replace("\r\n", "\n").replace("\r", "\n").rstrip("\n").split("\n")


def update_pbs_items():
    lines = read_lines_normalized("PBS/items.txt")
    new_lines = []
    for ln in lines:
        if ln.startswith("504,OLDROD,"):
            new_lines.append(f'504,OLDROD,{ROD_NAME},{ROD_PLURAL},8,0,"{ROD_DESC}",2,0,6,')
        elif ln.startswith("505,GOODROD,") or ln.startswith("506,SUPERROD,"):
            continue
        elif ln.startswith("512,COINCASE,"):
            new_lines.append(f'512,COINCASE,Monedero,Monederos,8,0,"{COINCASE_DESC}",2,0,6,')
        else:
            new_lines.append(ln)
    write_bom_crlf("PBS/items.txt", new_lines)
    print(f"PBS/items.txt actualizado ({len(new_lines)} entradas, UTF-8 BOM + CRLF).")
    return new_lines


def parse_pbs_items_map(lines):
    parsed = {}
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        row = next(csv.reader(io.StringIO(s)))
        iid = int(row[0])
        parsed[iid] = {
            "id": iid,
            "sym": row[1],
            "name": row[2],
            "plural": row[3],
            "pocket": int(row[4]),
            "price": int(row[5]),
            "desc": row[6],
            "use": int(row[7]),
            "battleuse": int(row[8]),
            "type": int(row[9]),
        }
    return parsed


def update_rem_pbs_files():
    # 1. rem_overworlds.txt
    ow = read_lines_normalized("PBS/rem_overworlds.txt")
    ow = [ln.replace("Entrega la Caña Vieja y enseña a pescar", "Entrega la Caña de Pescar y enseña a pescar") for ln in ow]
    write_bom_crlf("PBS/rem_overworlds.txt", ow)

    # 2. rem_progression.txt
    pr = read_lines_normalized("PBS/rem_progression.txt")
    new_pr = []
    cur_step = None
    for ln in pr:
        m = re.match(r"^\[(STEP_\d+)\]$", ln.strip())
        if m:
            cur_step = m.group(1)
        if cur_step == "STEP_35" and ln.startswith("KeyItemsUnlocked ="):
            ln = "KeyItemsUnlocked = "
        elif cur_step == "STEP_35" and ln.startswith("FieldAbilitiesUnlocked ="):
            ln = "FieldAbilitiesUnlocked = "
        elif cur_step == "STEP_36" and ln.startswith("FieldAbilitiesUnlocked ="):
            ln = "FieldAbilitiesUnlocked = Pesca (Caña de Pescar)"
        elif cur_step == "STEP_61" and ln.startswith("KeyItemsUnlocked ="):
            ln = "KeyItemsUnlocked = "
        new_pr.append(ln)
    write_bom_crlf("PBS/rem_progression.txt", new_pr)

    # 3. rem_location_items.txt
    li = read_lines_normalized("PBS/rem_location_items.txt")
    new_li = []
    cur_sec = None
    nacar_items = []
    ruta12_items = []

    def flush_nacar():
        nonlocal new_li, nacar_items
        # Replace comment count "# Pueblo Nacara - 12 filas" -> "11 filas"
        for idx in range(len(new_li) - 1, -1, -1):
            if new_li[idx].startswith("# Pueblo Nacara"):
                new_li[idx] = f"# Pueblo Nacara - {len(nacar_items)} filas"
                break
        for i, body in enumerate(nacar_items, 1):
            new_li.append(f"Item{i} = {body}")
        nacar_items = []

    def flush_ruta12():
        nonlocal new_li, ruta12_items
        for idx in range(len(new_li) - 1, -1, -1):
            if new_li[idx].startswith("# Ruta 12"):
                new_li[idx] = f"# Ruta 12 - {len(ruta12_items)} filas"
                break
        for i, body in enumerate(ruta12_items, 1):
            new_li.append(f"Item{i} = {body}")
        ruta12_items = []

    for ln in li:
        msec = re.match(r"^\[([A-Z0-9_]+)\]$", ln.strip())
        if msec:
            if cur_sec == "PUEBLO_NACAR":
                flush_nacar()
            elif cur_sec == "RUTA_12":
                flush_ruta12()
            cur_sec = msec.group(1)
            new_li.append(ln)
            continue

        if cur_sec == "PUEBLO_NACAR":
            mitem = re.match(r"^Item\d+\s*=\s*(.+)$", ln)
            if mitem:
                body = mitem.group(1)
                if body.startswith("SUPERROD,"):
                    continue
                if body.startswith("OLDROD,"):
                    body = "OLDROD,1,N,Casa de Telmo · mesa de pesca,Caña de Pescar de Telmo (Acto III)."
                nacar_items.append(body)
                continue
            elif ln.strip() == "":
                flush_nacar()
        elif cur_sec == "RUTA_12":
            mitem = re.match(r"^Item\d+\s*=\s*(.+)$", ln)
            if mitem:
                body = mitem.group(1)
                if body.startswith("GOODROD,"):
                    continue
                ruta12_items.append(body)
                continue
            elif ln.strip() == "":
                flush_ruta12()

        new_li.append(ln)

    if cur_sec == "PUEBLO_NACAR":
        flush_nacar()
    elif cur_sec == "RUTA_12":
        flush_ruta12()
    write_bom_crlf("PBS/rem_location_items.txt", new_li)

    # 4. rem_variables_switches.txt
    vs = read_lines_normalized("PBS/rem_variables_switches.txt")
    new_vs = []
    for ln in vs:
        if ln.startswith("708 ="):
            ln = "708 = Regalo_Unico_PuebloNacara_OLDROD | Telmo entrega la Caña de Pescar única"
        elif ln.startswith("715 ="):
            ln = "715 = Reserva_SinUso_Ruta12 | Antiguo slot de Caña Buena (caña unificada en 504 OLDROD)"
        new_vs.append(ln)
    write_bom_crlf("PBS/rem_variables_switches.txt", new_vs)

    # 5. rem_changelog.txt
    cl = read_lines_normalized("PBS/rem_changelog.txt")
    new_cl = []
    i = 0
    while i < len(cl):
        ln = cl[i]
        if ln.strip() == "[ITEM_OLDROD]" and i + 1 < len(cl) and cl[i + 1].startswith("Note ="):
            new_cl.append(ln)
            new_cl.append("Note = Unificada en REM como la única Caña de Pescar (504 OLDROD, nombre en juego: «Caña de Pescar»). Conserva las tablas 70/30 exactas y pica con tasa alta.")
            i += 2
            continue
        elif ln.strip() in ("[ITEM_GOODROD]", "[ITEM_SUPERROD]") and i + 1 < len(cl) and cl[i + 1].startswith("Note ="):
            new_cl.append(ln)
            new_cl.append("Note = Eliminada en REM al unificar las tres cañas en una única Caña de Pescar (504 OLDROD).")
            i += 2
            continue
        new_cl.append(ln)
        i += 1
    write_bom_crlf("PBS/rem_changelog.txt", new_cl)
    print("Archivos PBS/rem_*.txt actualizados.")


def update_binary_data(items_map):
    # 1. Data/items.dat
    with open("Data/items.dat", "rb") as f:
        raw_bytes = f.read()
        first_dw = struct.unpack("<I", raw_bytes[:4])[0]
        numrec = first_dw >> 3
        offsets = [struct.unpack("<II", raw_bytes[i * 8:(i + 1) * 8]) for i in range(numrec)]
        records = [decode_record(io.BytesIO(raw_bytes), off, size) for off, size in offsets]

    # Verify untouched records encode identically byte-for-byte
    for idx, (rec, (off, size)) in enumerate(zip(records, offsets)):
        if rec and rec[0] not in (504, 505, 506, 512, 720):
            assert encode_record(rec) == raw_bytes[off:off + size], f"Mismatch in roundtrip for record {rec[0]}"

    new_records = []
    for rec in records:
        if not rec:
            continue
        iid = rec[0]
        if iid in (505, 506):
            continue
        if iid == 504:
            rec = [504, ROD_NAME, ROD_PLURAL, 8, 0, ROD_DESC, 2, 0, 6, 0]
        elif iid == 512:
            rec = [512, "Monedero", "Monederos", 8, 0, COINCASE_DESC, 2, 0, 6, 0]
        new_records.append(rec)

    encoded_recs = [encode_record(rec) for rec in new_records]
    totalsize = len(new_records) * 8
    header = bytearray()
    for enc in encoded_recs:
        header.extend(struct.pack("<II", totalsize, len(enc)))
        totalsize += len(enc)

    with open("Data/items.dat", "wb") as f:
        f.write(header)
        for enc in encoded_recs:
            f.write(enc)
    print(f"Data/items.dat recompilado ({len(new_records)} registros).")

    # 2. Data/Constants.rxdata (PBItems)
    with open("Data/Constants.rxdata", "rb") as f:
        consts = r.loads(f.read())

    max_id = max(items_map.keys())
    const_lines = ["class PBItems"]
    for iid in sorted(items_map.keys()):
        const_lines.append(f"{items_map[iid]['sym']}={iid}")
    const_lines.append("")
    const_lines.append("def PBItems.getName(id)")
    const_lines.append("return pbGetMessage(MessageTypes::Items,id)")
    const_lines.append("end")
    const_lines.append("")
    const_lines.append("def PBItems.getNamePlural(id)")
    const_lines.append("return pbGetMessage(MessageTypes::ItemPlurals,id)")
    const_lines.append("end")
    const_lines.append("")
    const_lines.append("def PBItems.getCount")
    const_lines.append(f"return {len(items_map)}")
    const_lines.append("end")
    const_lines.append("")
    const_lines.append("def PBItems.maxValue")
    const_lines.append(f"return {max_id}")
    const_lines.append("end")
    const_lines.append("end")
    new_code = "\r\n".join(const_lines) + "\r\n"

    updated_const = False
    for sec in consts:
        if len(sec) >= 3 and sec[1] == b"PBItems":
            sec[2] = zlib.compress(new_code.encode("utf-8"))
            updated_const = True
            break
    assert updated_const, "No se encontró PBItems en Data/Constants.rxdata"

    with open("Data/Constants.rxdata", "wb") as f:
        f.write(w.writes(consts))
    print(f"Data/Constants.rxdata actualizado (count={len(items_map)}, maxValue={max_id}).")

    # 3. Data/messages.dat (sections 7=Items, 8=ItemPlurals, 9=ItemDescriptions)
    with open("Data/messages.dat", "rb") as f:
        msgs = r.loads(f.read())

    for sec_idx, key in ((7, "name"), (8, "plural"), (9, "desc")):
        sec = msgs[sec_idx]
        while len(sec) <= max_id:
            sec.append(b"")
        for iid in range(len(sec)):
            if iid in items_map:
                sec[iid] = items_map[iid][key].encode("utf-8")
            elif iid in (505, 506):
                sec[iid] = b""

    with open("Data/messages.dat", "wb") as f:
        f.write(w.writes(msgs))
    print("Data/messages.dat actualizado (Items, ItemPlurals, ItemDescriptions).")


def update_icon():
    # Usar el icono moderno de caña con carrete (item506) para la única Caña de Pescar (504)
    src = "Graphics/Icons/item506.png"
    dst = "Graphics/Icons/item504.png"
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"Icono {dst} actualizado desde {src}.")


def main():
    lines = update_pbs_items()
    items_map = parse_pbs_items_map(lines)
    update_rem_pbs_files()
    update_binary_data(items_map)
    update_icon()


if __name__ == "__main__":
    main()
