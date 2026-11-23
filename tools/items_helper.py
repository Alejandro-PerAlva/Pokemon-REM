import struct
import zlib
import rubymarshal.reader as r
import rubymarshal.writer as w

def encode_int(val):
    out = bytearray()
    while True:
        if val < 0x80:
            out.append(val)
            break
        out.append(0x80 | (val & 0x7F))
        val >>= 7
    return bytes(out)

def encode_string(s):
    s_bytes = s.encode('utf-8')
    return encode_int(len(s_bytes)) + s_bytes

def encode_record(fields):
    out = bytearray()
    for field in fields:
        if field is None:
            out.append(ord('0'))
        elif field is True:
            out.append(ord('T'))
        elif field is False:
            out.append(ord('F'))
        elif isinstance(field, str):
            out.append(ord('"'))
            out.extend(encode_string(field))
        elif isinstance(field, int):
            out.append(ord('i'))
            out.extend(encode_int(field))
    return bytes(out)

def decode_int(f):
    bits = 0
    ret = 0
    while True:
        b = f.read(1)[0]
        ret |= (b & 0x7F) << bits
        bits += 7
        if not (b & 0x80):
            break
    return ret

def decode_string(f):
    length = decode_int(f)
    return f.read(length).decode('utf-8', errors='ignore')

def decode_record(f, offset, length):
    f.seek(offset)
    end = offset + length
    fields = []
    while f.tell() < end:
        dt = f.read(1)
        if dt == b'0': fields.append(None)
        elif dt == b'T': fields.append(True)
        elif dt == b'F': fields.append(False)
        elif dt == b'"': fields.append(decode_string(f))
        elif dt == b'i': fields.append(decode_int(f))
    return fields

def add_reloj_item():
    # 1. Update PBS/items.txt
    with open('PBS/items.txt', 'r', encoding='utf-8') as f:
        content = f.read().lstrip('\ufeff')
    
    if '720,RELOJ' not in content:
        line_to_add = '720,RELOJ,Reloj Digital,Relojes Digitales,8,0,"Reloj digital de pulsera con formato 24 horas. Permite consultar la hora del mundo en cualquier momento desde el menú de pausa y saber si es de día o de noche en interiores y cuevas.",2,0,6,\r\n'
        if not content.endswith('\n'):
            content += '\r\n'
        content += line_to_add
        with open('PBS/items.txt', 'wb') as f:
            f.write(b'\xef\xbb\xbf')
            f.write(content.encode('utf-8'))
        print("Añadido 720,RELOJ a PBS/items.txt")
    else:
        print("720,RELOJ ya existe en PBS/items.txt")

    # 2. Update Data/items.dat
    with open('Data/items.dat', 'rb') as f:
        first_dw = struct.unpack('<I', f.read(4))[0]
        numrec = first_dw >> 3
        f.seek(0)
        offsets = []
        for i in range(numrec):
            off, size = struct.unpack('<II', f.read(8))
            offsets.append((off, size))
        records = [decode_record(f, off, size) for off, size in offsets]

    # Check if 720 already present
    has_720 = any(len(r) > 0 and r[0] == 720 for r in records)
    if not has_720:
        # fields: [id, name, pocket, price, desc, use, battleuse, type, machine]
        reloj_rec = [
            720,
            "Reloj Digital",
            8,
            0,
            "Reloj digital de pulsera con formato 24 horas. Permite consultar la hora del mundo en cualquier momento desde el menú de pausa y saber si es de día o de noche en interiores y cuevas.",
            2,
            0,
            6,
            0
        ]
        records.append(reloj_rec)
        
        # Write back Data/items.dat
        encoded_recs = [encode_record(r) for r in records]
        totalsize = len(records) * 8
        header = bytearray()
        for enc in encoded_recs:
            header.extend(struct.pack('<II', totalsize, len(enc)))
            totalsize += len(enc)
        
        with open('Data/items.dat', 'wb') as f:
            f.write(header)
            for enc in encoded_recs:
                f.write(enc)
        print(f"Data/items.dat actualizado con éxito. Total registros: {len(records)}")
    else:
        print("Data/items.dat ya contiene el registro 720.")

    # 3. Update Data/Constants.rxdata for PBItems
    with open('Data/Constants.rxdata', 'rb') as f:
        consts = r.loads(f.read())
    
    for item in consts:
        if len(item) >= 3 and item[1] == b'PBItems':
            code = zlib.decompress(item[2]).decode('utf-8', errors='ignore')
            if 'RELOJ=720' not in code:
                # Insert RELOJ=720 before def PBItems.getName
                target = 'def PBItems.getName'
                if target in code:
                    code = code.replace(target, 'RELOJ=720\r\n' + target)
                else:
                    code = code.replace('end\r\nend', 'RELOJ=720\r\nend\r\nend')
                code = code.replace('return 719', 'return 720')
                code = code.replace(f'return {numrec}', f'return {len(records)}')
                item[2] = zlib.compress(code.encode('utf-8'))
                print("Actualizado PBItems::RELOJ = 720 en Data/Constants.rxdata")
    
    with open('Data/Constants.rxdata', 'wb') as f:
        f.write(w.writes(consts))
    print("Guardado Data/Constants.rxdata")

if __name__ == '__main__':
    add_reloj_item()
