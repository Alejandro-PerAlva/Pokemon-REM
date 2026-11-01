"""Pokémon REM Master Codex: backend local (Python 3, solo biblioteca estándar).

Lee en vivo los archivos PBS (oficiales de Essentials v16 y los ``rem_*.txt``), construye el modelo
JSON del contrato (tools/codex/SPEC.md §4) y lo sirve por HTTP en 127.0.0.1:8765.
"""
import os

__version__ = "1.0.0"
SCHEMA = 1

#: Raíz del proyecto (carpeta que contiene ``codex/``, ``PBS/``, ``Graphics/``…).
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
