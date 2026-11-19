from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBRARY_DIR = ROOT / "library"
CARDS_DIR = ROOT / "cards"
INDEX_PATH = ROOT / "data" / "library.sqlite"

# 6" HD e-paper panel, portrait (Waveshare 1448x1072)
SCREEN_W, SCREEN_H = 1072, 1448
EMULATOR_SCALE = 0.5          # shrink the window on a laptop screen
GRAY_LEVELS = 16              # typical e-ink grayscale depth

REGION = "norcal-coast"       # regional pack loaded alongside "core"
REGION_LABEL = "NorCal Coast"
LIBRARY_VERSION = "0.1"

OLLAMA_URL = "http://localhost:11434"
MODEL = "gemma3:1b"
MAX_PASSAGES = 4
