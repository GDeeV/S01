"""Run the S-01 on a laptop.  python run_emulator.py [--no-model] [--model NAME] [--rebuild]"""
import argparse

from s01 import config
from s01.answer import Engine
from s01.app import App
from s01.library import build_index

p = argparse.ArgumentParser()
p.add_argument("--no-model", action="store_true", help="library-only mode, no language model")
p.add_argument("--model", default=config.MODEL, help="Ollama model name")
p.add_argument("--rebuild", action="store_true", help="re-index the library")
args = p.parse_args()

if args.rebuild or not config.INDEX_PATH.exists():
    print(f"Indexed {build_index()} library sections.")

engine = Engine(use_model=not args.no_model, model=args.model)
if not args.no_model and not engine.model:
    print(f"Model '{args.model}' not found in Ollama. Running in library-only mode.\n"
          f"To enable it:  ollama pull {args.model}")
print(f"Mode: {engine.mode}")

from s01.hw.emulator import Emulator   # imported late so --help works without Tk
Emulator(App(engine), engine).run()
