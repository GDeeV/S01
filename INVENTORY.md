# S-01 inventory

Every component in this repository as of the `baseline-2026-11` tag (November 2026).
"Started" is when the work was first created. This repository was first committed
in November 2026, rebuilt from that earlier work.

## Software (`software/`), started late September 2026

| Component | Description |
|-----------|-------------|
| `s01/config.py` | Settings: screen resolution, region, library paths, local model name |
| `s01/library.py` | Parses markdown library docs, builds a SQLite FTS5 index, searches it with synonym expansion |
| `s01/safety.py` | Routes emergencies to protocol cards, refuses edibility questions, limits dose questions to quotes |
| `s01/llm.py` | Client for a local model served by Ollama |
| `s01/answer.py` | Answer engine: retrieval, cited model answers, citation checks, library-only fallback |
| `s01/render.py` | Draws device screens at 6" e-ink resolution with Pillow |
| `s01/app.py` | Device interface: menus, answers, sources, emergency cards, library browser, About |
| `s01/hw/emulator.py` | Tk desktop window that emulates the device's screen and controls |
| `s01/hw/device.py` | Sketch of Raspberry Pi drivers (GPIO buttons, rotary knob, e-paper); untested |
| `run_emulator.py` | Launches the emulator |
| `ask.py` | Command-line test that asks one question without the window |
| `library/core/` | Sample core docs: water treatment, hypothermia |
| `library/regional/norcal-coast/` | Sample regional docs: poison oak, death cap, rattlesnakes |
| `cards/` | Sample emergency cards: severe bleeding, snakebite, hypothermia, anaphylaxis, mushroom ingestion |
| `README.md`, `requirements.txt` | Setup, controls and dependencies |

## Hardware design (`hardware/enclosure/`), started late September 2026

| Component | Description |
|-----------|-------------|
| `s01_enclosure.py` | Parametric build123d model: faceted split housing, cutouts, screw bosses, placeholder internals |
| `check.py` | Checks that internal parts don't collide with the housing |
| `render.py` | Renders front, rear and internal preview views |
| `s01_preview.png` | Preview render generated from the model |
| `README.md` | How to run and modify the model |

## Not in this repository

- AI-generated concept renders of the device (made late September 2026)
- Language model weights (downloaded separately under their own licenses)
