#!/usr/bin/env python3
"""Compila e inserta todas las secciones personalizadas REM en Data/Scripts.rxdata usando rubymarshal.
Mantiene el orden correcto justo antes de la sección 'Main'.
"""
import os, zlib
import rubymarshal.reader as r
import rubymarshal.writer as w
import rubymarshal.classes as rc

rx_path = os.path.join("Data", "Scripts.rxdata")
if not os.path.exists(rx_path):
    raise FileNotFoundError(f"No se encontró {rx_path}")

data = open(rx_path, "rb").read()
scripts = r.loads(data)

rem_names = [
    "REM_Rebalance",
    "REM_Mechanics",
    "REM_Events",
    "REM_UI",
    "REM_Shadows",
    "REM_Stairs",
    "REM_Incubator",
]

# Filtrar secciones REM preexistentes para evitar duplicados
filtered = []
for s in scripts:
    s_name = s[1].text if hasattr(s[1], "text") else (s[1].decode("utf-8", errors="ignore") if isinstance(s[1], bytes) else str(s[1]))
    if s_name not in rem_names:
        filtered.append(s)

# Localizar la sección Main
main_idx = None
max_id = 0
for idx, s in enumerate(filtered):
    if s[0] > max_id:
        max_id = s[0]
    s_name = s[1].text if hasattr(s[1], "text") else (s[1].decode("utf-8", errors="ignore") if isinstance(s[1], bytes) else str(s[1]))
    if s_name == "Main":
        main_idx = idx

if main_idx is None:
    main_idx = len(filtered) - 2

for k, name in enumerate(rem_names):
    fname = os.path.join("tools", "scripts_dump", f"{name.lower()}.rb")
    with open(fname, "rb") as f:
        code_bytes = f.read()
    compressed = zlib.compress(code_bytes)
    sec = [max_id + 1 + k, rc.RubyString(name), compressed]
    filtered.insert(main_idx + k, sec)
    print(f"Insertada sección {name} en el índice {main_idx + k}")

out = w.writes(filtered)
with open(rx_path, "wb") as f:
    f.write(out)

print(f"Data/Scripts.rxdata compilado con éxito. Total de secciones: {len(filtered)}")
