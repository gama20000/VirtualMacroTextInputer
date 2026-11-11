"""Ponto de entrada para o PyInstaller (evita imports relativos em __main__)."""
import sys

from macropad.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
