#!/usr/bin/env python3
"""make.fun entry: sum up 21 November 2026 world news in one image.

Python 3.13, standard library only, no network, fully deterministic.
Renders a newspaper front page (1024x1024) using a hand-built 5x7
bitmap font and writes entry.png to the output directory:
MAKEFUN_OUTPUT_DIR if set, else /output if usable, else ./out.
Two runs always produce byte-identical output.
"""

import math
import os
import struct
import zlib

PAGE_W = 1024
PAGE_H = 1024

PAPER = (252, 252, 250)
INK = (16, 22, 44)
RED = (198, 32, 44)
GREY = (96, 104, 128)

# ---------------------------------------------------------------------------
# 5x7 bitmap font (uppercase, digits, basic punctuation).
# ---------------------------------------------------------------------------

GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#.##", "#..##"),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
}

# ---------------------------------------------------------------------------
# Drawing primitives on a row-based RGB canvas.
# ---------------------------------------------------------------------------


def new_page():
    row = bytearray(bytes(PAPER) * PAGE_W)
    return [bytearray(row) for _ in range(PAGE_H)]


def rect(page, x0, y0, x1, y1, color):
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(PAGE_W, x1)
    y1 = min(PAGE_H, y1)
    if x1 <= x0 or y1 <= y0:
        return
    seg = bytes(color) * (x1 - x0)
    for yy in range(y0, y1):
        page[yy][x0 * 3 : x1 * 3] = seg


def dot(page, cx, cy, size, color):
    half = size // 2
    rect(page, cx - half, cy - half, cx - half + size, cy - half + size, color)


def line(page, x0, y0, x1, y1, size, color):
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
    for i in range(steps + 1):
        dot(
            page,
            int(round(x0 + (x1 - x0) * i / steps)),
            int(round(y0 + (y1 - y0) * i / steps)),
            size,
            color,
        )


def poly(page, pts, size, color):
    for a, b in zip(pts, pts[1:]):
        line(page, a[0], a[1], b[0], b[1], size, color)


def ring(page, cx, cy, r, size, color, squash=1.0):
    for deg in range(0, 360, 2):
        rad = math.radians(deg)
        dot(
            page,
            int(round(cx + r * squash * math.cos(rad))),
            int(round(cy + r * math.sin(rad))),
            size,
            color,
        )


def text(page, x, y, s, scale, color, advance=None, bold=False):
    step = advance if advance is not None else 6 * scale
    offsets = (0, max(1, scale // 3)) if bold else (0,)
    for ch in s.upper():
        glyph = GLYPHS.get(ch, GLYPHS[" "])
        for ri, row in enumerate(glyph):
            for ci, cell in enumerate(row):
                if cell == "#":
                    for off in offsets:
                        rect(
                            page,
                            x + ci * scale + off,
                            y + ri * scale,
                            x + (ci + 1) * scale + off,
                            y + (ri + 1) * scale,
                            color,
                        )
        x += step
    return x


def text_mid(page, y, s, scale, color):
    w = len(s) * 6 * scale - scale
    text(page, (PAGE_W - w) // 2, y, s, scale, color)


def wrap(s, max_chars):
    out, cur = [], ""
    for word in s.split():
        trial = word if not cur else cur + " " + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


# ---------------------------------------------------------------------------
# Icons for the six stories, each inside an 88x88 box at (x, y).
# ---------------------------------------------------------------------------


def icon_globe(page, x, y):
    cx, cy = x + 44, y + 44
    ring(page, cx, cy, 36, 4, INK)
    ring(page, cx, cy, 36, 4, INK, squash=0.45)
    line(page, cx - 36, cy, cx + 36, cy, 3, INK)
    line(page, cx - 31, cy - 20, cx + 31, cy - 20, 3, GREY)
    line(page, cx - 31, cy + 20, cx + 31, cy + 20, 3, GREY)
    line(page, cx, cy, cx, cy - 22, 5, RED)
    line(page, cx, cy, cx + 14, cy + 8, 5, RED)


def icon_missile(page, x, y):
    line(page, x + 18, y + 70, x + 52, y + 36, 9, INK)
    line(page, x + 52, y + 36, x + 62, y + 26, 7, INK)
    line(page, x + 18, y + 70, x + 30, y + 70, 6, INK)
    line(page, x + 18, y + 70, x + 18, y + 58, 6, INK)
    for dx, dy in ((0, -12), (10, -10), (12, 0), (10, 10), (0, 12), (-10, 10), (-12, 0), (-10, -10)):
        line(page, x + 68, y + 20, x + 68 + dx, y + 20 + dy, 4, RED)
    dot(page, x + 68, y + 20, 7, RED)
    for i in range(4):
        dot(page, x + 12 + i * 9, y + 80 - i * 9, 3, GREY)


def icon_quake(page, x, y):
    peaks = [(x + 4, y + 52), (x + 24, y + 22), (x + 38, y + 40), (x + 54, y + 16), (x + 84, y + 52)]
    poly(page, peaks, 5, INK)
    line(page, x + 4, y + 52, x + 84, y + 52, 4, INK)
    zig = [(x + 6 + i * 8, y + 68 + (8 if i % 2 else -2)) for i in range(10)]
    poly(page, zig, 4, RED)


def icon_alert(page, x, y):
    tri = [(x + 44, y + 10), (x + 82, y + 76), (x + 6, y + 76), (x + 44, y + 10)]
    poly(page, tri, 6, RED)
    text(page, x + 37, y + 34, "!", 4, INK)


def icon_chartdown(page, x, y):
    line(page, x + 10, y + 8, x + 10, y + 78, 4, GREY)
    line(page, x + 10, y + 78, x + 84, y + 78, 4, GREY)
    pts = [(x + 16, y + 18), (x + 32, y + 30), (x + 48, y + 26), (x + 62, y + 48), (x + 80, y + 62)]
    poly(page, pts, 6, RED)
    line(page, x + 80, y + 62, x + 65, y + 60, 6, RED)
    line(page, x + 80, y + 62, x + 77, y + 47, 6, RED)


def icon_planet(page, x, y):
    ring(page, x + 34, y + 52, 26, 4, INK)
    ring(page, x + 26, y + 44, 6, 3, GREY)
    ring(page, x + 42, y + 60, 4, 3, GREY)
    ring(page, x + 34, y + 52, 40, 3, GREY)
    rect(page, x + 62, y + 10, x + 72, y + 20, INK)
    rect(page, x + 50, y + 12, x + 60, y + 18, RED)
    rect(page, x + 74, y + 12, x + 84, y + 18, RED)
    line(page, x + 67, y + 20, x + 58, y + 34, 3, INK)


ICON_DRAW = {
    "globe": icon_globe,
    "missile": icon_missile,
    "quake": icon_quake,
    "alert": icon_alert,
    "chartdown": icon_chartdown,
    "planet": icon_planet,
}

# ---------------------------------------------------------------------------
# The verified news of Saturday 21 November 2026.
# ---------------------------------------------------------------------------

DATE_LINE = "SATURDAY 21 NOVEMBER 2026"
SUBTITLE = "THE WORLD IN ONE PAGE"

STORIES = [
    {
        "place": "ANTALYA, TURKIYE",
        "place_advance": None,
        "headline": ["COP31 IN", "OVERTIME"],
        "body": "NEARLY 200 NATIONS DEADLOCKED AS THE DRAFT DEAL OMITS FOSSIL FUELS",
        "icon": "globe",
    },
    {
        "place": "RIYADH, SAUDI ARABIA",
        "place_advance": 22,
        "headline": ["3 MISSILES", "INTERCEPTED"],
        "body": "SAUDI-LED COALITION DOWNS 3 HOUTHI MISSILES AIMED AT RIYADH",
        "icon": "missile",
    },
    {
        "place": "JUNIN, PERU",
        "place_advance": None,
        "headline": ["M6.7", "EARTHQUAKE"],
        "body": "STRONG QUAKE SHAKES THE ANDES. NO CASUALTIES REPORTED",
        "icon": "quake",
    },
    {
        "place": "POLAND AND UKRAINE",
        "place_advance": None,
        "headline": ["MISSILES LAND", "IN POLAND"],
        "body": "400 DRONES, 110 MISSILES HIT UKRAINE. 2 MISSILES LAND IN POLAND",
        "icon": "alert",
    },
    {
        "place": "NEW YORK, USA",
        "place_advance": None,
        "headline": ["AI SELL-OFF", "DEEPENS"],
        "body": "US STOCKS FALL 3.7%. THE S&P 500 SLIPS INTO CORRECTION",
        "icon": "chartdown",
    },
    {
        "place": "MERCURY, SPACE",
        "place_advance": None,
        "headline": ["PROBE REACHES", "MERCURY"],
        "body": "BEPICOLOMBO ARRIVES AFTER 8 YEARS. ONLY THE 2ND MISSION TO ORBIT MERCURY",
        "icon": "planet",
    },
]


def draw_story(page, px, py, story):
    w, h = 480, 250
    rect(page, px, py, px + w, py + 3, INK)
    rect(page, px, py + h - 3, px + w, py + h, INK)
    rect(page, px, py, px + 3, py + h, INK)
    rect(page, px + w - 3, py, px + w, py + h, INK)
    text(page, px + 16, py + 12, story["place"], 4, RED, advance=story["place_advance"])
    hy = py + 48
    for ln in story["headline"]:
        text(page, px + 16, hy, ln, 5, INK)
        hy += 43
    rect(page, px + 16, py + 134, px + w - 16, py + 136, GREY)
    ICON_DRAW[story["icon"]](page, px + 16, py + 146)
    ly = py + 142
    for ln in wrap(story["body"], 19)[:4]:
        text(page, px + 124, ly, ln, 3, INK, bold=True)
        ly += 25


def render():
    page = new_page()
    rect(page, 0, 0, PAGE_W, 148, INK)
    text_mid(page, 53, DATE_LINE, 6, PAPER)
    rect(page, 0, 148, PAGE_W, 160, RED)
    text_mid(page, 172, SUBTITLE, 4, INK)
    rect(page, 24, 212, PAGE_W - 24, 214, INK)
    for i, story in enumerate(STORIES):
        draw_story(page, 24 if i % 2 == 0 else 520, 224 + (i // 2) * 260, story)
    return page


def to_png(page):
    raw = bytearray()
    for row in page:
        raw.append(0)
        raw += row

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", PAGE_W, PAGE_H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return bytes(png)


def main():
    data = to_png(render())
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        out_dir = "/output" if os.path.isdir("/output") and os.access("/output", os.W_OK) else "out"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(data)
    print(f"wrote {path} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
