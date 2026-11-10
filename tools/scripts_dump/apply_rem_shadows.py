#!/usr/bin/env python3
"""Inserta la seccion REM_Shadows en Data/Scripts.rxdata usando rubymarshal.
Crea un backup automatico Data/Scripts.rxdata.bak_pre_shadows.
"""
import os, zlib, shutil
import rubymarshal.reader as r
import rubymarshal.writer as w
import rubymarshal.classes as rc

rx_path = os.path.join("Data", "Scripts.rxdata")
bak_path = rx_path + ".bak_pre_shadows"

if not os.path.exists(bak_path):
    shutil.copy2(rx_path, bak_path)
    print("Backup creado:", bak_path)

code_path = os.path.join("tools", "scripts_dump", "rem_shadows.rb")
with open(code_path, "rb") as f:
    code_bytes = f.read()

compressed_code = zlib.compress(code_bytes)

data = open(rx_path, "rb").read()
scripts = r.loads(data)

# Buscar el indice de Main
scripts = [s for s in scripts if str(s[1]) != "REM_Shadows" and getattr(s[1], 'text', None) != "REM_Shadows"]

main_idx = None
max_id = 0
for idx, s in enumerate(scripts):
    if s[0] > max_id:
        max_id = s[0]
    s_name = s[1].decode('utf-8', errors='ignore') if isinstance(s[1], bytes) else str(s[1])
    if s_name == "Main":
        main_idx = idx

if main_idx is None:
    main_idx = len(scripts) - 2

new_sec = [max_id + 1, rc.RubyString("REM_Shadows"), compressed_code]
scripts.insert(main_idx, new_sec)
print(f"Seccion REM_Shadows insertada en el indice {main_idx} (antes de Main). Total secciones: {len(scripts)}")

out = w.writes(scripts)
with open(rx_path, "wb") as f:
    f.write(out)

print("Data/Scripts.rxdata guardado correctamente con REM_Shadows.")
