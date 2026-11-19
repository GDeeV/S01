"""Real-hardware drivers (Raspberry Pi). Sketch only, untested.

The App class doesn't change on the device: swap the emulator for these.
  - Display: Waveshare 6" HD e-paper uses an IT8951 driver board; its Python
    driver accepts a PIL image. Use full refresh for page changes and the fast
    partial mode for scrolling and menu moves.
  - Controls: gpiozero Buttons and a RotaryEncoder, mapped to the same events.
"""

PINS = {"up": 5, "down": 6, "left": 13, "right": 19, "ok": 26,
        "back": 16, "home": 20, "ptt": 21, "knob_a": 17, "knob_b": 27}


def run_device(app, engine, display):
    from gpiozero import Button, RotaryEncoder
    from signal import pause

    def fire(ev):
        hint = app.handle(ev)
        if hint:
            display.show(app.render(), full=(hint == "full"))

    buttons = {ev: Button(pin, bounce_time=0.05) for ev, pin in PINS.items() if not ev.startswith("knob")}
    for ev, b in buttons.items():
        if ev != "ptt":
            b.when_pressed = lambda ev=ev: fire(ev)
    knob = RotaryEncoder(PINS["knob_a"], PINS["knob_b"])
    knob.when_rotated_clockwise = lambda: fire("knob+")
    knob.when_rotated_counter_clockwise = lambda: fire("knob-")
    # TODO: PTT -> record audio while held -> speech-to-text -> app.begin_query()
    display.show(app.render(), full=True)
    pause()
