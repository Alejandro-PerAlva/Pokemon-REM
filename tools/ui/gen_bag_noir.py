#!/usr/bin/env python3
"""Fondo "Oniria Noir" de la Mochila (bagNoir.png). Uso: python3 tools/ui/gen_bag_noir.py
La geometría debe coincidir con rem_ui.rb (REM_UI::BAG_*). Los bagbg1..8 originales quedan sin usar."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import gen_summary_noir as S
G = S.G

def main():
    im = S.base_bg()
    S.card(im, (8, 48, 222, 226))
    S.card(im, (8, 234, 222, 376))
    S.card(im, (232, 48, 504, 376), S.PANEL)
    S.box(im, (20, 58, 210, 152), S.WELL, S.DIV, 6)       # pedestal del icono
    S.box(im, (20, 188, 210, 218), S.WELL, S.DIV, 5)      # datos de MT / cantidad
    G.save(im, "bagNoir")

if __name__ == "__main__":
    main()
