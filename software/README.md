# S-01 emulator

Software for the S-01 offline survival reference device, running on a laptop.
The screen, controls and answer pipeline behave as they will on the device;
only the hardware drivers differ (see `s01/hw/device.py`).

## Setup

1. Python 3.10 or newer with Tk. The python.org installer includes Tk.
   With Homebrew: `brew install python python-tk`
2. `pip install -r requirements.txt`
3. Optional, for AI answers: install Ollama (ollama.com), then
   `ollama pull gemma3:1b`
   Without it, the device runs in library-only mode and quotes passages directly.

## Run

    python run_emulator.py              # the device window
    python run_emulator.py --no-model   # library-only mode
    python run_emulator.py --rebuild    # after editing library files
    python ask.py "how do I treat stream water"   # quick test, no window

## Controls

| Device      | Keyboard            |
|-------------|---------------------|
| PTT         | Space (type your question; voice comes later) |
| 4-way pad   | Arrow keys          |
| OK          | Enter               |
| BACK        | Backspace or Esc    |
| HOME        | H                   |
| Knob        | Mouse wheel, or [ and ] |

On-screen buttons under the display do the same.

## How answers work

1. **Safety routing first** (`s01/safety.py`). Emergencies open a pre-written
   card with no AI involved. Questions about eating wild plants or mushrooms get
   a fixed refusal plus related library passages. Dose questions only get quotes.
2. **Library search** (`s01/library.py`): SQLite full-text search over the
   markdown files, filtered to the core library plus the selected region.
3. **Answer**: the local model answers only from the retrieved passages and must
   cite them. If it cites nothing or invents a citation, the device quotes the
   library instead. If nothing relevant is found, it says so.

## Adding content

- Library docs: markdown in `library/core/` or `library/regional/<region>/`,
  with frontmatter (title, source, date, vetted, region) and `##` sections.
- Emergency cards: `cards/*.md`. Numbered lines are steps; `- ` lines are "do not".
- Then run with `--rebuild`.

All included content is paraphrased SAMPLE material marked `vetted: false`.
Replace it with sourced, expert-reviewed text before anyone relies on it.

## Next steps

- Embedding search alongside keyword search (the synonym list is a stopgap)
- Voice: whisper.cpp or Moonshine for speech-to-text, Piper for speech output
- Port to a Raspberry Pi 5 with the Waveshare 6" e-paper panel and GPIO buttons
- Build the real core library and the first regional pack
