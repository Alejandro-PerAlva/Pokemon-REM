#!/bin/bash
# Doble clic en macOS: arranca el Pokémon REM Master Codex y abre el navegador.
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
  python3 start_codex.py "$@"
else
  echo "No se encontró python3. Instálalo desde https://www.python.org/downloads/"
  read -r -p "Pulsa Intro para cerrar..." _
  exit 1
fi
status=$?
if [ $status -ne 0 ]; then
  echo
  read -r -p "El Codex terminó con errores (código $status). Pulsa Intro para cerrar..." _
fi
