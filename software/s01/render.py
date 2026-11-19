"""Draws every screen as a grayscale PIL image at the panel's native resolution.
The same images go to the emulator window or the real e-ink panel."""
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import config

W, H = config.SCREEN_W, config.SCREEN_H
M = 56                      # side margin
TOP = 96                    # below status bar
BOTTOM = H - 96             # above hint bar
VIEW_H = BOTTOM - TOP

FONT_CANDIDATES = {
    "serif": ["/System/Library/Fonts/Supplemental/Georgia.ttf", "/Library/Fonts/Georgia.ttf",
              "C:/Windows/Fonts/georgia.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"],
    "sans": ["/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf",
             "C:/Windows/Fonts/arial.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "bold": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
             "C:/Windows/Fonts/arialbd.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
}


@lru_cache(maxsize=None)
def font(kind, size):
    for p in FONT_CANDIDATES[kind]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size=size)


BODY = ("serif", 36)
SMALL = ("sans", 27)
LABEL = ("bold", 28)
HEAD = ("bold", 50)
ITEM = ("bold", 40)
STEP = ("serif", 40)


def wrap(text, f, width):
    lines = []
    for para in text.split("\n"):
        words, line = para.split(), ""
        for w in words:
            trial = f"{line} {w}".strip()
            if f.getlength(trial) <= width:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = w
        lines.append(line)
    return lines


class Page:
    """A tall, scrollable column of text blocks."""

    def __init__(self):
        self.lines = []      # (y, text, font, x, inverted_block_id)
        self.boxes = {}      # block_id -> (y0, y1) for inverted blocks
        self.y = 0

    def add(self, text, style=BODY, indent=0, gap=22, invert=None):
        f = font(*style)
        lh = int(style[1] * 1.35)
        y0 = self.y
        for ln in wrap(text, f, W - 2 * M - indent - (24 if invert is not None else 0)):
            self.lines.append((self.y, ln, f, M + indent + (12 if invert is not None else 0), invert))
            self.y += lh
        if invert is not None:
            self.boxes[invert] = (y0 - 8, self.y + 4)
        self.y += gap

    def rule(self, gap=24):
        self.lines.append((self.y, None, None, 0, None))
        self.y += gap

    @property
    def max_scroll(self):
        return max(0, self.y - VIEW_H + 40)

    def draw(self, img, scroll, selected=None):
        d = ImageDraw.Draw(img)
        if selected in self.boxes:
            y0, y1 = self.boxes[selected]
            if y1 > scroll and y0 < scroll + VIEW_H:
                d.rectangle([M - 8, TOP + y0 - scroll, W - M + 8, TOP + y1 - scroll], fill=0)
        for y, text, f, x, blk in self.lines:
            sy = TOP + y - scroll
            if sy < TOP - 10 or sy > BOTTOM - 20:
                continue
            if text is None:
                d.line([M, sy + 6, W - M, sy + 6], fill=0, width=3)
            else:
                d.text((x, sy), text, font=f, fill=255 if (blk is not None and blk == selected) else 0)
        if self.max_scroll > 0:          # scroll position indicator
            track = VIEW_H - 20
            thumb = max(60, int(track * VIEW_H / (self.y + 40)))
            pos = int((track - thumb) * scroll / self.max_scroll)
            d.rectangle([W - 22, TOP + 10 + pos, W - 12, TOP + 10 + pos + thumb], fill=0)


def canvas(title, hints, status):
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 72], fill=0)
    d.text((M, 20), "S-01", font=font(*LABEL), fill=255)
    d.text((M + 110, 22), title.upper(), font=font(*SMALL), fill=255)
    right = f"OFFLINE  ·  {status}"
    f = font(*SMALL)
    d.text((W - M - f.getlength(right), 22), right, font=f, fill=255)
    d.line([0, BOTTOM + 20, W, BOTTOM + 20], fill=0, width=3)
    x = M
    for key, label in hints:
        k = font(*LABEL)
        kw = k.getlength(key) + 20
        d.rectangle([x, BOTTOM + 40, x + kw, BOTTOM + 80], outline=0, width=3)
        d.text((x + 10, BOTTOM + 44), key, font=k, fill=0)
        d.text((x + kw + 10, BOTTOM + 45), label, font=f, fill=0)
        x += kw + f.getlength(label) + 44
    return img


def menu(img, items, sel, subtitle=None):
    d = ImageDraw.Draw(img)
    y = TOP + 24
    if subtitle:
        d.text((M, y), subtitle, font=font(*SMALL), fill=0)
        y += 60
    row = 104
    first = max(0, min(sel - 5, len(items) - int((BOTTOM - y) / row)))
    for i, (label, sub) in enumerate(items[first:], first):
        if y + row > BOTTOM:
            break
        on = i == sel
        if on:
            d.rectangle([M - 12, y - 6, W - M + 12, y + row - 14], fill=0)
        d.text((M + 8, y + 4), label, font=font(*ITEM), fill=255 if on else 0)
        if sub:
            d.text((M + 8, y + 54), sub, font=font(*SMALL), fill=200 if on else 70)
        y += row
    return img


def quantize(img):
    """Mimic e-ink's limited grayscale."""
    step = 256 // config.GRAY_LEVELS
    return img.point(lambda v: min(255, (v // step) * step + (step - 1 if v > 250 else 0)))
