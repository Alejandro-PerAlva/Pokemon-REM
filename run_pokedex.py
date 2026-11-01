#!/usr/bin/env python3
"""Compatibilidad: la antigua Pokédex ahora es el Pokémon REM Master Codex (ver start_codex.py).

    python3 run_pokedex.py [puerto] [--no-browser] [--pbs-dir CARPETA]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from start_codex import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
