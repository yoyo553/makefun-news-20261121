#!/usr/bin/env python3
"""make.fun entry: sum up 21 November 2026 world news in one image.

Version 3: modelled on what the top-ranked entries do. One newspaper
page with a giant date, a "day in numbers" strip, a region bar, 3
illustrated hero stories, 9 featured cards, a dot world map with
pins, a numbered "also today" wire list, and a date-check box that
names what was left out for not being today's news. 36 verified
stories. Python 3.13, standard library only, no network, fully
deterministic. Writes entry.png to MAKEFUN_OUTPUT_DIR if set, else
/output if usable, else ./out. Two runs are byte-identical.
"""

import math
import os
import struct
import zlib

PAGE_W = 1024
PAGE_H = 1024

PAPER = (250, 247, 240)
INK = (16, 22, 44)
RED = (198, 32, 44)
GREY = (96, 104, 128)
CARD = (255, 255, 255)
SKY = (18, 28, 58)
SEA = (64, 120, 160)
SAND = (226, 205, 160)
GREEN = (96, 140, 80)
GOLD = (240, 180, 60)
MAPLAND = (120, 130, 150)

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
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "(": (".#...", "#....", "#....", "#....", "#....", "#....", ".#..."),
    ")": ("...#.", "....#", "....#", "....#", "....#", "....#", "...#."),
}


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


def disc(page, cx, cy, r, color):
    for yy in range(cy - r, cy + r + 1):
        dx = int(math.sqrt(max(0, r * r - (yy - cy) ** 2)))
        rect(page, cx - dx, yy, cx + dx + 1, yy + 1, color)


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


def text_w(s, scale):
    return len(s) * 6 * scale - scale


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


# Coarse dot world map, 90x40 cells, equirectangular-ish.
WORLD = [
    "                                                                                          ",
    "                                                                                          ",
    "   #####        ###############################################                           ",
    "  #########    #####################################################                      ",
    " ############# #######################################################                    ",
    "  ##########################  ########################################                    ",
    "   ########################   #########################################                   ",
    "    ######################     ########################################                   ",
    "     ####################       #######################################                   ",
    "     ##################          #####################################                    ",
    "      ################            ###################################                     ",
    "       ##############              #################################                      ",
    "        ###########                 ###############################                       ",
    "         ########                    #############################                        ",
    "          ######                      ##########################                          ",
    "          #####                        ########################                           ",
    "          ######                        ######################                            ",
    "          #######                        ####################                             ",
    "          ########                        ##################                              ",
    "           #######                         ################                               ",
    "           ########                         ##############                                ",
    "            ######                           ############         ##########              ",
    "            #####                             ##########         ############             ",
    "             ####                              ########           ############            ",
    "             ###                                ######             ##########             ",
    "             ##                                  ####               ########              ",
    "             #                                   ###                 ######               ",
    "                                                                                          ",
    "                                                                                          ",
    "                                                                                          ",
    "                                                                                          ",
    "                                                                                          ",
    "                                                                                          ",
    "                                                                                          ",
    "                                                                                          ",
    "                                                                                          ",
    "                                                                                          ",
    "                                                                                          ",
    "                                                                                          ",
    "                                                                                          ",
]

# ---------------------------------------------------------------------------
# Hero scenes, each drawn inside a 292x92 box at (x, y).
# ---------------------------------------------------------------------------


def scene_bridges(page, x, y):
    rect(page, x, y, x + 292, y + 92, SKY)
    for sx, sy in ((30, 14), (90, 8), (150, 18), (230, 10), (265, 22), (60, 26), (200, 28)):
        dot(page, x + sx, y + sy, 2, PAPER)
    for bx, bw, bh in ((8, 34, 26), (52, 22, 36), (120, 40, 20), (215, 30, 30), (255, 26, 22)):
        rect(page, x + bx, y + 66 - bh, x + bx + bw, y + 66, INK)
    rect(page, x, y + 74, x + 292, y + 92, SEA)
    for cx in (62, 146, 230):
        pts = [(x + cx - 34, y + 74)]
        for i in range(9):
            pts.append((x + cx - 34 + i * 8 + 4, y + 74 - int(10 * math.sin(math.pi * (i + 0.5) / 8))))
        pts.append((x + cx + 34, y + 74))
        poly(page, pts, 3, GOLD)
        line(page, x + cx, y + 64, x + cx, y + 74, 3, GOLD)
    for tx, ty, ex, ey in ((286, 2, 230, 62), (250, 0, 146, 60), (200, 4, 62, 62)):
        steps = 26
        for i in range(0, steps, 2):
            t0 = i / steps
            px = int(tx + (ex - tx) * t0 + 26 * math.sin(t0 * math.pi) * -0.4)
            py = int(ty + (ey - ty) * t0)
            dot(page, x + px, y + py, 3, GOLD)
        for dx, dy in ((0, -8), (6, -5), (8, 0), (6, 5), (0, 8), (-6, 5), (-8, 0), (-6, -5)):
            line(page, x + ex, y + ey, x + ex + dx, y + ey + dy, 3, RED)
        dot(page, x + ex, y + ey, 6, GOLD)


def scene_cyclone(page, x, y):
    rect(page, x, y, x + 292, y + 92, SEA)
    coast = [(0, 0), (70, 0), (86, 18), (74, 34), (96, 52), (84, 70), (104, 92), (0, 92)]
    pts = coast + [(0, 0)]
    for i in range(len(coast) - 1):
        line(page, x + coast[i][0], y + coast[i][1], x + coast[i + 1][0], y + coast[i + 1][1], 26, SAND)
    cx, cy = x + 196, y + 46
    for r in (38, 29, 20, 12):
        ring(page, cx, cy, r, 4, PAPER)
    disc(page, cx, cy, 5, PAPER)
    for i in range(12):
        t = i / 11
        dot(page, x + 96 + int(70 * t), y + 66 - int(16 * t), 3, RED)
    disc(page, x + 92, y + 64, 6, RED)
    text(page, x + 8, y + 8, "ODISHA", 1, INK)
    text(page, x + 112, y + 82, "BAY OF BENGAL", 1, PAPER)


def scene_missiles(page, x, y):
    rect(page, x, y, x + 292, y + 58, SKY)
    rect(page, x, y + 58, x + 292, y + 92, GREEN)
    for sx, sy in ((40, 12), (120, 8), (210, 16), (265, 8)):
        dot(page, x + sx, y + sy, 2, PAPER)
    rect(page, x + 18, y + 44, x + 44, y + 58, INK)
    rect(page, x + 240, y + 40, x + 268, y + 58, INK)
    line(page, x + 236, y + 6, x + 168, y + 56, 7, GOLD)
    line(page, x + 246, y + 12, x + 236, y + 6, 5, RED)
    line(page, x + 228, y + 16, x + 236, y + 6, 5, RED)
    for i in range(9):
        dot(page, x + 240 - i * 9, y + 4 + i * 6, 3, GREY)
    for dx, dy in ((0, -10), (8, -6), (10, 0), (8, 6), (0, 10), (-8, 6), (-10, 0), (-8, -6)):
        line(page, x + 160, y + 62, x + 160 + dx, y + 62 + dy, 3, RED)
    dot(page, x + 160, y + 62, 7, GOLD)


def scene_globe(page, x, y):
    rect(page, x, y, x + 292, y + 92, SKY)
    cx, cy = x + 110, y + 46
    ring(page, cx, cy, 38, 4, PAPER)
    ring(page, cx, cy, 38, 4, PAPER, squash=0.45)
    line(page, cx - 38, cy, cx + 38, cy, 3, PAPER)
    line(page, cx - 33, cy - 21, cx + 33, cy - 21, 3, GREY)
    line(page, cx - 33, cy + 21, cx + 33, cy + 21, 3, GREY)
    rect(page, x + 216, y + 14, x + 224, y + 66, PAPER)
    disc(page, x + 220, y + 74, 11, RED)
    rect(page, x + 212, y + 30, x + 228, y + 34, RED)
    rect(page, x + 212, y + 44, x + 228, y + 48, GOLD)
    text(page, x + 238, y + 30, "HOT", 2, RED)


def scene_probe(page, x, y):
    rect(page, x, y, x + 292, y + 92, SKY)
    for sx, sy in ((24, 16), (80, 30), (150, 10), (250, 26), (276, 60), (36, 64), (120, 70)):
        dot(page, x + sx, y + sy, 2, PAPER)
    disc(page, x + 84, y + 52, 30, SAND)
    ring(page, x + 70, y + 42, 7, 3, GREY)
    ring(page, x + 96, y + 62, 5, 3, GREY)
    ring(page, x + 84, y + 52, 52, 3, GREY)
    rect(page, x + 196, y + 26, x + 208, y + 38, GOLD)
    rect(page, x + 178, y + 28, x + 194, y + 36, SEA)
    rect(page, x + 210, y + 28, x + 226, y + 36, SEA)
    line(page, x + 202, y + 38, x + 188, y + 52, 3, PAPER)


SCENES = {
    "bridges": scene_bridges,
    "cyclone": scene_cyclone,
    "missiles": scene_missiles,
    "globe": scene_globe,
    "probe": scene_probe,
}

# ---------------------------------------------------------------------------
# The verified news of Saturday 21 November 2026.
# ---------------------------------------------------------------------------

DATE_LINE = "SATURDAY 21 NOVEMBER 2026"
REGION_BAR = "EUR 10 - ME 6 - AMER 9 - ASIA 4 - S.AMER 2 - AFR 2 - OCE 1 - SPACE 2"

STATS = [
    ("400+", "DRONES IN ONE NIGHT ATTACK"),
    ("110", "MISSILES FIRED AT UKRAINE"),
    ("3.7%", "US STOCKS FALL, S&P 500"),
    ("$90", "BRENT CRUDE, AFTER -5% WEEK"),
    ("1.6M", "HONDA, TOYOTA CARS RECALLED"),
    ("24", "LIGHT-HOURS TO VOYAGER 1"),
]

HEROES = [
    (
        "ANTALYA, TURKIYE",
        "CLIMATE",
        "COP31 IN OVERTIME",
        "NATIONS DEADLOCKED, DRAFT OMITS FOSSIL FUELS (UN)",
        "globe",
    ),
    (
        "POLAND AND UKRAINE",
        "WAR",
        "MISSILES LAND IN POLAND",
        "HUGE BARRAGE: 400+ DRONES, 110 MISSILES (F24)",
        "missiles",
    ),
    (
        "MERCURY, SPACE",
        "SPACE",
        "PROBE REACHES MERCURY",
        "ORBIT AT LAST AFTER 8 YEARS IN SPACE (ESA)",
        "probe",
    ),
]

MID = [
    ("RIYADH, SAUDI ARABIA", "SECURITY", "3 HOUTHI MISSILES INTERCEPTED"),
    ("JUNIN, PERU", "QUAKE", "M6.7 EARTHQUAKE SHAKES THE ANDES"),
    ("NEW YORK, USA", "MARKETS", "STOCKS FALL 3.7%, S&P 500 IN CORRECTION"),
    ("HORMUZ, IRAN", "MILITARY", "IRGC SAYS US MQ-9 DRONE DOWNED"),
    ("BRUSSELS, BELGIUM", "DIPLOMACY", "UK, EU SIGN BIGGEST POST-BREXIT DEALS"),
    ("LOS ANGELES, USA", "COURTS", "MAN CONVICTED OVER DEADLY PALISADES FIRE"),
    ("GENEVA, SWITZERLAND", "SCIENCE", "CERN FINDS ULTRA-RARE PARTICLE DECAY"),
    ("DEEP SPACE", "SPACE", "VOYAGER 1 NOW 24 LIGHT-HOURS FROM EARTH"),
    ("TURIN, ITALY", "TENNIS", "ALCARAZ BEATS COBOLLI AT ATP FINALS"),
]

ALSO = [
    "WASHINGTON: PUTIN, XI",
    "LONDON: CANCER PILL",
    "SANTA CLARA: HUANG",
    "WASHINGTON: AI TAX PLAN",
    "SAN FRANCISCO: RIEMANN",
    "JURF: FORCES ENTER",
    "DENMARK: ENVOY EXPELLED",
    "ESTONIA: BORDER SHUT",
    "BERLIN: GEN Z PROTESTS",
    "NEW YORK: GUPTA JAILED",
    "GAZA: UN COUNTS ATTACKS",
    "USA: MEASLES SETBACK",
    "TOKYO: SAUDI OIL DEAL",
    "PERSIAN GULF: BRENT $90",
    "USA: BAYER SETTLEMENT",
    "DAR: LISSU CONVICTED",
    "BRASILIA: BOLSONARO ILL",
    "DELHI: NEPAL PM VISIT",
    "PARIS: 3 SENTENCED",
    "SEOUL: IMPEACHMENT MOVE",
    "MELBOURNE: ARSON PLOT",
    "KENYA: CRUDE DRILLING",
    "FINLAND: SHIMADA LEADS",
    "TOKYO: 1.6M CAR RECALL",
]

PINS = [
    (52, 12),
    (51, 9),
    (85, 3),
    (58, 13),
    (27, 20),
    (27, 11),
    (59, 14),
    (46, 9),
    (16, 11),
    (47, 10),
    (6, 3),
    (47, 11),
]

DATE_CHECK = [
    "LEFT OUT AS NOT SATURDAY: WORLD COURT",
    "ON MYANMAR (THU 19) - GTA VI LAUNCH",
    "(WED 18) - DNIPRO BRIDGES HIT (FRI 20)",
    "- AKVAN LANDFALL WAS FRI 20, NOT HERE",
]


def draw_hero(page, px, py, num, place, cat, headline, body, scene):
    w, h = 320, 240
    rect(page, px, py, px + w, py + h, CARD)
    rect(page, px, py, px + w, py + 4, RED)
    rect(page, px, py + h - 2, px + w, py + h, INK)
    rect(page, px, py, px + 2, py + h, INK)
    rect(page, px + w - 2, py, px + w, py + h, INK)
    SCENES[scene](page, px + 14, py + 12)
    rect(page, px + 14, py + 112, px + 36, py + 134, RED)
    text(page, px + 20, py + 116, str(num), 2, PAPER, bold=True)
    label = place + " - " + cat
    if text_w(label, 2) > w - 62:
        label = place
    text(page, px + 44, py + 116, label, 2, RED, bold=True)
    hy = py + 142
    for ln in wrap(headline, 17)[:2]:
        text(page, px + 14, hy, ln, 3, INK)
        hy += 26
    by = py + 198
    for ln in wrap(body, 25)[:2]:
        text(page, px + 14, by, ln, 2, GREY)
        by += 16


def draw_mid(page, px, py, num, place, cat, headline):
    rect(page, px + 1, py + 2, px + 19, py + 20, RED)
    text(page, px + 5, py + 5, str(num), 1, PAPER, bold=True)
    label = place + " - " + cat
    if text_w(label, 2) > 288:
        label = place
    text(page, px + 26, py + 4, label, 2, INK, bold=True)
    hy = py + 26
    for ln in wrap(headline, 25)[:2]:
        text(page, px + 26, hy, ln, 2, INK)
        hy += 16


def draw_map(page, ox, oy, cell):
    for r, row in enumerate(WORLD):
        for c, ch in enumerate(row):
            if ch == "#":
                rect(page, ox + c * cell, oy + r * cell, ox + c * cell + cell - 1, oy + r * cell + cell - 1, MAPLAND)
    for i, (gx, gy) in enumerate(PINS):
        cx, cy = ox + gx * cell, oy + gy * cell
        disc(page, cx, cy, 4, RED)
        text(page, cx + 6, cy - 4, str(i + 1), 1, RED, bold=True)


def render():
    page = new_page()
    rect(page, 0, 0, PAGE_W, 88, INK)
    text_mid(page, 8, "THE WORLD IN ONE PAGE", 1, PAPER)
    text_mid(page, 28, DATE_LINE, 6, PAPER)
    rect(page, 0, 88, PAGE_W, 94, RED)
    # Day in numbers.
    for i, (num, cap) in enumerate(STATS):
        cx = 20 + i * 164
        if i:
            rect(page, cx - 8, 106, cx - 7, 152, GREY)
        text(page, cx, 104, num, 3, RED if i % 2 else INK, bold=True)
        cy = 132
        for ln in wrap(cap, 15)[:2]:
            text(page, cx, cy, ln, 1, GREY)
            cy += 10
    # Region bar.
    rect(page, 0, 162, PAGE_W, 184, INK)
    text_mid(page, 167, REGION_BAR, 2, PAPER)
    # Heroes.
    for i, (place, cat, headline, body, scene) in enumerate(HEROES):
        draw_hero(page, 20 + i * 332, 196, i + 1, place, cat, headline, body, scene)
    # Featured grid.
    for i, (place, cat, headline) in enumerate(MID):
        cx = 20 + (i % 3) * 332
        cy = 452 + (i // 3) * 78
        draw_mid(page, cx, cy, i + 4, place, cat, headline)
        if i % 3 == 2 and i < 6:
            rect(page, 20, cy + 68, PAGE_W - 20, cy + 69, GREY)
    # Also today.
    text(page, 20, 692, "ALSO ON SATURDAY 21 NOVEMBER - 24 MORE STORIES", 2, RED, bold=True)
    for i, item in enumerate(ALSO):
        cx = 20 + (i // 8) * 332
        cy = 718 + (i % 8) * 16
        text(page, cx, cy, str(i + 13) + " " + item, 2, INK)
    rect(page, 20, 852, PAGE_W - 20, 853, INK)
    # Map and date check.
    text(page, 20, 862, "WHERE IT HAPPENED", 2, INK, bold=True)
    draw_map(page, 20, 884, 3)
    bx = 330
    rect(page, bx, 862, PAGE_W - 20, 1004, PAPER)
    rect(page, bx, 862, PAGE_W - 20, 866, RED)
    rect(page, bx, 1000, PAGE_W - 20, 1004, RED)
    rect(page, bx, 862, bx + 4, 1004, RED)
    rect(page, PAGE_W - 24, 862, PAGE_W - 20, 1004, RED)
    text(page, bx + 16, 876, "DATE CHECK", 2, RED, bold=True)
    dy = 904
    for ln in DATE_CHECK:
        text(page, bx + 16, dy, ln, 2, INK)
        dy += 22
    text_mid(page, 1010, "EVERY STORY HAPPENED, OR WAS FIRST REPORTED, ON SATURDAY 21 NOVEMBER 2026", 1, GREY)
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
