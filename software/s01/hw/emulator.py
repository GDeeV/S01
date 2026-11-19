"""Laptop emulator: shows the screen in a window, maps keys and on-screen
buttons to the device's controls, and imitates e-ink refresh behavior."""
import queue
import threading
import tkinter as tk
from tkinter import simpledialog

from PIL import Image, ImageOps, ImageTk

from .. import config

KEYMAP = {
    "Up": "up", "Down": "down", "Left": "left", "Right": "right",
    "Return": "ok", "BackSpace": "back", "Escape": "back",
    "h": "home", "bracketright": "knob+", "bracketleft": "knob-",
}


class Emulator:
    def __init__(self, app, engine):
        self.app, self.engine = app, engine
        self.results = queue.Queue()
        self.root = tk.Tk()
        self.root.title("S-01 emulator")
        self.root.configure(bg="#8a7d5c")
        w = int(config.SCREEN_W * config.EMULATOR_SCALE)
        h = int(config.SCREEN_H * config.EMULATOR_SCALE)
        self.size = (w, h)
        self.screen = tk.Label(self.root, bd=0, bg="#8a7d5c")
        self.screen.pack(padx=24, pady=(24, 10))
        self._controls()
        for key, ev in KEYMAP.items():
            self.root.bind(f"<{key}>" if len(key) > 1 else key, lambda e, ev=ev: self.event(ev))
        self.root.bind("<space>", lambda e: self.ptt())
        self.root.bind("<MouseWheel>", lambda e: self.event("knob+" if e.delta < 0 else "knob-"))
        self.root.bind("<Button-4>", lambda e: self.event("knob-"))   # Linux wheel
        self.root.bind("<Button-5>", lambda e: self.event("knob+"))
        self.show("full")
        self.root.after(100, self._poll)

    def _controls(self):
        bar = tk.Frame(self.root, bg="#8a7d5c")
        bar.pack(pady=(0, 20))
        b = dict(width=6, font=("Helvetica", 12, "bold"))
        tk.Button(bar, text="PTT", command=self.ptt, **b).grid(row=0, column=0, rowspan=3, padx=8)
        tk.Button(bar, text="BACK", command=lambda: self.event("back"), **b).grid(row=1, column=1)
        tk.Button(bar, text="▲", command=lambda: self.event("up"), **b).grid(row=0, column=3)
        tk.Button(bar, text="◀", command=lambda: self.event("left"), **b).grid(row=1, column=2)
        tk.Button(bar, text="OK", command=lambda: self.event("ok"), fg="#d9531e", **b).grid(row=1, column=3)
        tk.Button(bar, text="▶", command=lambda: self.event("right"), **b).grid(row=1, column=4)
        tk.Button(bar, text="▼", command=lambda: self.event("down"), **b).grid(row=2, column=3)
        tk.Button(bar, text="HOME", command=lambda: self.event("home"), **b).grid(row=1, column=5)
        tk.Button(bar, text="KNOB −", command=lambda: self.event("knob-"), **b).grid(row=0, column=6, padx=8)
        tk.Button(bar, text="KNOB +", command=lambda: self.event("knob+"), **b).grid(row=2, column=6, padx=8)

    # display --------------------------------------------------------------
    def _paint(self, img):
        self._tk = ImageTk.PhotoImage(img.resize(self.size, Image.LANCZOS))
        self.screen.configure(image=self._tk)

    def show(self, refresh):
        img = self.app.render()
        if refresh == "full":
            # e-ink full refresh: flash inverted, then black, then the new page
            self._paint(ImageOps.invert(img))
            self.root.after(120, lambda: self._paint(Image.new("L", img.size, 0)))
            self.root.after(240, lambda: self._paint(img))
        else:
            self.root.after(60, lambda: self._paint(img))   # partial refresh lag

    # input ----------------------------------------------------------------
    def event(self, ev):
        hint = self.app.handle(ev)
        if hint == "ask":
            self.ptt()
        elif hint:
            self.show(hint)

    def ptt(self):
        q = simpledialog.askstring("Push-to-talk (emulated)",
                                   "Voice input isn't wired up yet.\nType what you would say:",
                                   parent=self.root)
        if not q or not q.strip():
            return
        self.app.begin_query(q.strip())
        self.show("full")
        threading.Thread(target=lambda: self.results.put(self.engine.ask(q.strip())),
                         daemon=True).start()

    def _poll(self):
        try:
            ans = self.results.get_nowait()
            self.app.finish_query(ans)
            self.show("full")
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def run(self):
        self.root.mainloop()
