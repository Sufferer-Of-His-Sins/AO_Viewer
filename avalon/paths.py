import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
MAPS_DIR = BASE_DIR / "maps"
LOCALES_DIR = BASE_DIR / "locales"
ASSETS_DIR = BASE_DIR / "assets"