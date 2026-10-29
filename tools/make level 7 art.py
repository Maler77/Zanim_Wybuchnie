"""Rysuje grafiki poziomu 7 (bossfight we wnętrzu siedziby Trelvosu): tło, ściany pomieszczeń, rekwizyty.

Uruchom z głównego katalogu repozytorium:   python "tools/make level 7 art.py"
(wymaga bibliotek Pillow i numpy:  pip install pillow numpy)

Rozmiary pomieszczeń i rekwizytów bierze z "tools/make level 7.py", więc po zmianie układu uruchom oba skrypty.

Powstają pliki w assets/ (nazwy zaczynają się od "l7_"):
  l7_interior.png                     tło 1280 x 720: betonowa ściana wnętrza z filarami, belkami i lampami (zapętla się poziomo)
  l7_wall_dock/store/canteen/server/corridor/shaft.png   ściany pomieszczeń (tło za graczem): dok serwisowy z bramami
                                      rozładunkowymi, magazyn z regałami i suwnicą, stołówka z szatnią personelu,
                                      serwerownia, korytarz techniczny, szyb
  l7_ceiling.png, l7_floor.png, l7_concrete.png, l7_shaft.png      kafelki: sufit z rurami, posadzka, beton, ciemny rów
  l7_pallet.png, l7_crate.png, l7_cart.png, l7_table.png, l7_counter.png, l7_ups.png, l7_cooler.png    osłony i przeszkody
  l7_catwalk.png, l7_rail.png, l7_post.png, l7_grate.png, l7_hoist.png    galerie, kratki, wózek suwnicy z hakiem
  l7_bulkhead.png, l7_pit_barrier.png, l7_duct_shaft.png, l7_tunnel.png   grodzia, barierki, kanał wentylacyjny

Styl jak reszta gry: trzy tony cieniowania, czarny kontur rekwizytów, przygaszone ściany i jaśniejsze obiekty, na
które da się wejść. Ciepłe światło lamp (żółć jak okna w tle poprzednich poziomów) i pomarańcz Trelvosu.
"""

import importlib.util
import random
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"

spec = importlib.util.spec_from_file_location("level7_layout", HERE / "make level 7.py")
layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(layout)


def hexc(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


INK = hexc("#0a0d14")
WALL = (hexc("#56677f"), hexc("#41506a"), hexc("#2f3b52"))            # ściana: chłodny granat-szary
WALL_DIM = (hexc("#3c4a60"), hexc("#2d3a4f"), hexc("#202a3b"))        # ściana w cieniu (tło tła)
TILE = (hexc("#a8c2c4"), hexc("#7fa0a6"), hexc("#587a84"))            # kafelki stołówki
CONCRETE = (hexc("#8d96a4"), hexc("#6b7585"), hexc("#4c5565"))
STEEL = (hexc("#c2cad6"), hexc("#8792a4"), hexc("#566174"))
DARK_STEEL = (hexc("#6c7688"), hexc("#454e60"), hexc("#2c3342"))
YELLOW = (hexc("#ffe066"), hexc("#f2b72a"), hexc("#a86f12"))
ORANGE = (hexc("#ffb060"), hexc("#ee7a2a"), hexc("#9a3e14"))
WOOD = (hexc("#d6a468"), hexc("#a8763e"), hexc("#74492a"))
CARDBOARD = (hexc("#d9b27a"), hexc("#b08650"), hexc("#7c5a34"))
BLUE_BOX = (hexc("#6aa8e8"), hexc("#3f78b8"), hexc("#264e82"))
RED_BOX = (hexc("#e87070"), hexc("#b84444"), hexc("#7a2a30"))
GREEN_BOX = (hexc("#6ac88a"), hexc("#3f9660"), hexc("#256240"))
LAMP = (hexc("#fff6c0"), hexc("#ffd878"), hexc("#e0a448"))
LED_G, LED_A, LED_C, LED_R = hexc("#78ff9c"), hexc("#ffc050"), hexc("#68e0ff"), hexc("#ff6a5a")
BLACK_RACK = (hexc("#3a4054"), hexc("#262a3a"), hexc("#171a26"))
CREAM = (hexc("#f0e6c8"), hexc("#cdbf98"), hexc("#9a8c68"))
TEAL = (hexc("#58b8b0"), hexc("#388a88"), hexc("#225a62"))


class Canvas:
    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), dtype=np.uint8)
        if fill is not None:
            self.rect(0, 0, w, h, fill)

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = (*c[:3], c[3] if len(c) > 3 else 255)

    def rect(self, x, y, w, h, c):
        x0, y0, x1, y1 = max(0, x), max(0, y), min(self.w, x + w), min(self.h, y + h)
        if x1 > x0 and y1 > y0:
            self.a[y0:y1, x0:x1] = (*c[:3], c[3] if len(c) > 3 else 255)

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def frame(self, x, y, w, h, c):
        self.hline(x, y, w, c)
        self.hline(x, y + h - 1, w, c)
        self.vline(x, y, h, c)
        self.vline(x + w - 1, y, h, c)

    def shaded(self, x, y, w, h, tones, ink=False):
        """Prostokąt w trzech tonach: jasna góra i prawa krawędź... jasna góra i lewa, ciemny dół i prawa (światło z lewej góry)."""
        light, base, dark = tones
        self.rect(x, y, w, h, base)
        self.hline(x, y, w, light)
        self.vline(x, y, h, light)
        self.hline(x, y + h - 1, w, dark)
        self.vline(x + w - 1, y, h, dark)
        if ink:
            self.frame(x - 1, y - 1, w + 2, h + 2, INK)

    def line(self, x0, y0, x1, y1, c, thick=1):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.rect(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), thick, thick, c)

    def disc(self, cx, cy, r, c):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + r // 2:
                    self.px(x, y, c)

    def blend(self, x, y, c, alpha):
        if 0 <= x < self.w and 0 <= y < self.h:
            old = self.a[y, x]
            if old[3] == 0:
                self.a[y, x] = (*c[:3], int(255 * alpha))
            else:
                self.a[y, x, :3] = (old[:3] * (1 - alpha) + np.array(c[:3]) * alpha).astype(np.uint8)

    def glow(self, cx, cy, rx, ry, c, strength=0.35, steps=4):
        """Miękka poświata lampy: kilka koncentrycznych eliptycznych warstw (pikselowo, bez gładkiego gradientu)."""
        for i in range(steps):
            k = (steps - i) / steps
            ax, ay = int(rx * k), int(ry * k)
            a = strength / steps
            for y in range(cy - ay, cy + ay + 1):
                for x in range(cx - ax, cx + ax + 1):
                    if ax and ay and ((x - cx) / ax) ** 2 + ((y - cy) / ay) ** 2 <= 1:
                        self.blend(x, y, c, a)

    def cone(self, x, y, top_w, bottom_w, h, c, strength=0.18):
        """Stożek światła z lampy: trapez rozszerzający się w dół."""
        for row in range(h):
            half = (top_w + (bottom_w - top_w) * row / max(1, h - 1)) / 2
            a = strength * (1 - row / h * 0.8)
            for xx in range(int(x - half), int(x + half) + 1):
                self.blend(xx, y + row, c, a)

    def outline_alpha(self, c=INK):
        alpha = self.a[:, :, 3] > 0
        grown = np.zeros_like(alpha)
        grown[1:, :] |= alpha[:-1, :]
        grown[:-1, :] |= alpha[1:, :]
        grown[:, 1:] |= alpha[:, :-1]
        grown[:, :-1] |= alpha[:, 1:]
        self.a[grown & ~alpha] = (*c[:3], 255)

    def save(self, name):
        Image.fromarray(self.a, "RGBA").save(ASSETS / name)
        print(f"{name}: {self.w}x{self.h}")


# ---------------------------------------------------------------------------
#  Pikselowa czcionka 5 x 7 (napisy na ścianach i tablicach)
# ---------------------------------------------------------------------------
_FONT = """
A .###./#...#/#...#/#####/#...#/#...#/#...#
B ####./#...#/#...#/####./#...#/#...#/####.
C .####/#..../#..../#..../#..../#..../.####
D ####./#...#/#...#/#...#/#...#/#...#/####.
E #####/#..../#..../####./#..../#..../#####
F #####/#..../#..../####./#..../#..../#....
G .####/#..../#..../#.###/#...#/#...#/.###.
H #...#/#...#/#...#/#####/#...#/#...#/#...#
I #####/..#../..#../..#../..#../..#../#####
J ..###/...#./...#./...#./...#./#..#./.##..
K #...#/#..#./#.#../##.../#.#../#..#./#...#
L #..../#..../#..../#..../#..../#..../#####
M #...#/##.##/#.#.#/#.#.#/#...#/#...#/#...#
N #...#/##..#/#.#.#/#.#.#/#..##/#...#/#...#
O .###./#...#/#...#/#...#/#...#/#...#/.###.
P ####./#...#/#...#/####./#..../#..../#....
Q .###./#...#/#...#/#...#/#.#.#/#..#./.##.#
R ####./#...#/#...#/####./#.#../#..#./#...#
S .####/#..../#..../.###./....#/....#/####.
T #####/..#../..#../..#../..#../..#../..#..
U #...#/#...#/#...#/#...#/#...#/#...#/.###.
V #...#/#...#/#...#/#...#/#...#/.#.#./..#..
W #...#/#...#/#...#/#.#.#/#.#.#/##.##/#...#
X #...#/#...#/.#.#./..#../.#.#./#...#/#...#
Y #...#/#...#/.#.#./..#../..#../..#../..#..
Z #####/....#/...#./..#../.#.../#..../#####
0 .###./#...#/#..##/#.#.#/##..#/#...#/.###.
1 ..#../.##../..#../..#../..#../..#../.###.
2 .###./#...#/....#/...#./..#../.#.../#####
3 ####./....#/....#/.###./....#/....#/####.
4 #...#/#...#/#...#/#####/....#/....#/....#
5 #####/#..../####./....#/....#/#...#/.###.
6 .###./#..../#..../####./#...#/#...#/.###.
7 #####/....#/...#./..#../.#.../.#.../.#...
8 .###./#...#/#...#/.###./#...#/#...#/.###.
9 .###./#...#/#...#/.####/....#/....#/.###.
- ...../...../...../#####/...../...../.....
. ...../...../...../...../...../.##../.##..
! ..#../..#../..#../..#../..#../...../..#..
> #..../.#.../..#../...#./..#../.#.../#....
: ...../.##../.##../...../.##../.##../.....
< ...#./..#../.#.../#..../.#.../..#../...#.
^ ..#../.###./#.#.#/..#../..#../..#../..#..
"""
GLYPHS = {}
for _line in _FONT.strip().splitlines():
    _ch, _rows = _line.split(" ", 1)
    GLYPHS[_ch] = _rows.split("/")
GLYPHS[" "] = ["....."] * 7


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(c, x, y, text, scale, color):
    for ch in text:
        for ry, row in enumerate(GLYPHS[ch]):
            for rx, v in enumerate(row):
                if v == "#":
                    c.rect(x + rx * scale, y + ry * scale, scale, scale, color)
        x += 6 * scale


def sign(c, x, y, text, scale=1, fg=YELLOW[0], bg=(hexc("#1a1f2c"),), pad=3, frame=STEEL[2]):
    """Tabliczka z napisem (ciemne tło, jasne litery, ramka)."""
    w, h = text_width(text, scale) + pad * 2, 7 * scale + pad * 2
    c.rect(x, y, w, h, bg[0])
    c.frame(x, y, w, h, frame)
    draw_text(c, x + pad, y + pad, text, scale, fg)
    return w, h


# ---------------------------------------------------------------------------
#  Wspólne elementy
# ---------------------------------------------------------------------------
def hazard_stripe(c, x, y, w, h, a=YELLOW[1], b=INK, step=6):
    """Pasy ostrzegawcze żółto-czarne (ukośne)."""
    for yy in range(h):
        for xx in range(w):
            c.px(x + xx, y + yy, a if ((xx + yy) // (step // 2)) % 2 == 0 else b)


def ceiling_lamp(c, x, y, w=34, glow=True, cone_h=0):
    """Lampa sufitowa (świetlówka w obudowie) z poświatą i opcjonalnym stożkiem światła w dół."""
    c.shaded(x, y, w, 5, DARK_STEEL, ink=True)
    c.rect(x + 2, y + 5, w - 4, 3, LAMP[1])
    c.rect(x + 3, y + 5, w - 6, 1, LAMP[0])
    if glow:
        c.glow(x + w // 2, y + 12, w, 16, LAMP[1], 0.28, 3)
    if cone_h:
        c.cone(x + w // 2, y + 8, w - 6, w + 70, cone_h, LAMP[1], 0.12)


def pipe_h(c, x, y, w, thick=6, tones=STEEL, bands=True):
    """Rura pozioma z obejmami."""
    c.rect(x, y, w, thick, tones[1])
    c.hline(x, y, w, tones[0])
    c.hline(x, y + thick - 1, w, tones[2])
    if bands:
        for bx in range(x + 14, x + w - 6, 56):
            c.rect(bx, y - 1, 4, thick + 2, DARK_STEEL[1])
            c.hline(bx, y - 1, 4, DARK_STEEL[0])


def pipe_v(c, x, y, h, thick=6, tones=STEEL):
    c.rect(x, y, thick, h, tones[1])
    c.vline(x, y, h, tones[0])
    c.vline(x + thick - 1, y, h, tones[2])
    for by in range(y + 20, y + h - 6, 64):
        c.rect(x - 1, by, thick + 2, 4, DARK_STEEL[1])
        c.hline(x - 1, by, thick + 2, DARK_STEEL[0])


def logo(c, x, y, scale=1, fg=ORANGE[0], shadow=ORANGE[2]):
    draw_text(c, x + scale, y + scale, "TRELVOS", scale, shadow)
    draw_text(c, x, y, "TRELVOS", scale, fg)
    return text_width("TRELVOS", scale)


def cardboard_box(c, x, y, w, h, tones=CARDBOARD, label=True):
    c.shaded(x, y, w, h, tones, ink=True)
    c.rect(x + w // 2 - 1, y, 2, h, tones[2])                    # taśma
    if label and w >= 14 and h >= 10:
        c.rect(x + 2, y + h - 6, 5, 3, CREAM[0])


def plastic_crate(c, x, y, w, h, tones=BLUE_BOX):
    c.shaded(x, y, w, h, tones, ink=True)
    for gy in range(y + 3, y + h - 2, 4):
        c.hline(x + 2, gy, w - 4, tones[2])


# ---------------------------------------------------------------------------
#  KAFELKI
# ---------------------------------------------------------------------------
def make_tiles():
    # posadzka: płyta betonowa z żółtą linią przy krawędzi (kafelek 32 x 32; widać tylko górny wiersz płyty)
    c = Canvas(32, 32, CONCRETE[1])
    rng = random.Random(3)
    c.rect(0, 0, 32, 3, CONCRETE[0])
    c.hline(0, 3, 32, CONCRETE[2])
    c.rect(0, 4, 32, 2, STEEL[2])
    c.rect(0, 6, 32, 26, CONCRETE[1])
    for _ in range(60):
        c.px(rng.randrange(32), rng.randrange(7, 32), CONCRETE[2] if rng.random() < 0.5 else CONCRETE[0])
    c.vline(0, 6, 26, CONCRETE[2])
    c.vline(31, 6, 26, CONCRETE[2])
    c.hline(0, 31, 32, CONCRETE[2])
    c.save("l7_floor.png")

    # beton pod posadzką: bloki 64 x 64 ze szwami
    c = Canvas(64, 64, CONCRETE[2])
    c.rect(0, 0, 64, 64, hexc("#3e4757"))
    rng = random.Random(4)
    for _ in range(220):
        c.px(rng.randrange(64), rng.randrange(64), hexc("#4a5465") if rng.random() < 0.6 else hexc("#343c4b"))
    c.hline(0, 0, 64, hexc("#566074"))
    c.hline(0, 32, 64, hexc("#2c3340"))
    c.vline(0, 0, 32, hexc("#2c3340"))
    c.vline(32, 32, 32, hexc("#2c3340"))
    c.hline(0, 33, 64, hexc("#566074"))
    c.save("l7_concrete.png")

    # sufit: pas 64 x 140: ciemna płyta, rury, korytarz kablowy, lampy
    c = Canvas(64, 140, hexc("#1c2230"))
    c.rect(0, 0, 64, 90, hexc("#171c28"))
    c.hline(0, 89, 64, hexc("#3a4458"))
    c.rect(0, 90, 64, 10, hexc("#2a3242"))
    c.hline(0, 90, 64, hexc("#4a566c"))
    c.hline(0, 99, 64, hexc("#10141e"))
    for x in range(0, 64, 16):                                   # żebra stropu
        c.vline(x, 0, 90, hexc("#222a3a"))
    # rura wzdłuż sufitu i kabel
    c.rect(0, 104, 64, 8, DARK_STEEL[1])
    c.hline(0, 104, 64, DARK_STEEL[0])
    c.hline(0, 111, 64, DARK_STEEL[2])
    c.rect(30, 103, 4, 10, DARK_STEEL[2])
    c.rect(0, 116, 64, 3, hexc("#3a2a1a"))                       # korytarz kablowy
    c.hline(0, 116, 64, hexc("#5a4630"))
    for x in range(2, 64, 8):
        c.px(x, 117, hexc("#8a6a3a"))
    c.rect(0, 126, 64, 14, hexc("#10141e"))                      # dolna krawędź (cień)
    c.hline(0, 125, 64, hexc("#4a566c"))
    c.save("l7_ceiling.png")

    # ciemny rów / szyb (kafelek 32 x 32): czarny beton z kablami
    c = Canvas(32, 32, hexc("#0e121b"))
    for x in (4, 14, 25):
        c.vline(x, 0, 32, hexc("#1a2132"))
    rng = random.Random(5)
    for _ in range(40):
        c.px(rng.randrange(32), rng.randrange(32), hexc("#161c2a"))
    c.vline(9, 0, 32, hexc("#3a2a1a"))
    c.vline(20, 0, 32, hexc("#2a3a3e"))
    c.hline(0, 16, 32, hexc("#141a28"))
    c.save("l7_shaft.png")

    # kratka: kafelek 32 x 8 (stalowa kratka, widać wnętrze)
    c = Canvas(32, 8)
    c.rect(0, 0, 32, 2, STEEL[0])
    c.rect(0, 2, 32, 1, STEEL[2])
    for x in range(0, 32, 4):
        c.rect(x, 3, 2, 5, STEEL[1])
        c.px(x, 3, STEEL[0])
        c.rect(x + 2, 3, 2, 5, (0, 0, 0, 0))
    c.rect(0, 6, 32, 2, DARK_STEEL[1])
    c.outline_alpha()
    c.save("l7_grate.png")

    # kratownica pod grate (duct shaft): kafelek 32 x 32 ciemne ściany otworu z drabinką
    c = Canvas(32, 32, hexc("#161c2a"))
    c.vline(0, 0, 32, hexc("#2a3348"))
    c.vline(31, 0, 32, hexc("#0c1018"))
    for y in range(4, 32, 8):
        c.rect(10, y, 12, 2, DARK_STEEL[1])
        c.hline(10, y, 12, DARK_STEEL[0])
    c.vline(10, 0, 32, DARK_STEEL[2])
    c.vline(21, 0, 32, DARK_STEEL[2])
    c.save("l7_duct_shaft.png")

    # pomost kratowy (kafelek 32 x 14, widać krawędź płyty i spód)
    c = Canvas(32, 14, STEEL[1])
    c.rect(0, 0, 32, 3, STEEL[0])
    c.hline(0, 3, 32, STEEL[2])
    for x in range(0, 32, 8):
        c.rect(x, 4, 4, 4, DARK_STEEL[1])
        c.px(x, 4, DARK_STEEL[0])
    c.rect(0, 8, 32, 4, DARK_STEEL[1])
    c.hline(0, 8, 32, DARK_STEEL[0])
    c.hline(0, 11, 32, DARK_STEEL[2])
    c.rect(0, 12, 32, 2, hexc("#10141e"))
    c.rect(0, 12, 32, 1, YELLOW[1])
    c.save("l7_catwalk.png")

    # poręcz (kafelek 32 x 30): barierka z żółtym prętem
    c = Canvas(32, 30)
    c.rect(0, 0, 32, 3, YELLOW[1])
    c.hline(0, 0, 32, YELLOW[0])
    c.hline(0, 2, 32, YELLOW[2])
    c.rect(0, 13, 32, 2, YELLOW[1])
    c.hline(0, 14, 32, YELLOW[2])
    c.rect(0, 26, 32, 4, DARK_STEEL[1])
    c.rect(14, 3, 4, 27, STEEL[1])
    c.vline(14, 3, 27, STEEL[0])
    c.vline(17, 3, 27, STEEL[2])
    c.outline_alpha()
    c.save("l7_rail.png")

    # słupek podpory (kafelek 12 x 16): stalowy dwuteownik z kreskami
    c = Canvas(12, 16, STEEL[1])
    c.rect(0, 0, 12, 16, DARK_STEEL[1])
    c.rect(3, 0, 6, 16, STEEL[1])
    c.vline(3, 0, 16, STEEL[0])
    c.vline(8, 0, 16, STEEL[2])
    c.vline(0, 0, 16, INK)
    c.vline(11, 0, 16, INK)
    c.hline(1, 7, 10, DARK_STEEL[2])
    c.save("l7_post.png")

    # barierka przy rowie (128 x 40): żółto-czarne poprzeczki na słupkach
    c = Canvas(128, 40)
    for px in (4, 62, 120):
        c.rect(px, 8, 4, 32, STEEL[1])
        c.vline(px, 8, 32, STEEL[0])
    hazard_stripe(c, 0, 10, 128, 6)
    hazard_stripe(c, 0, 24, 128, 6)
    c.hline(0, 9, 128, INK)
    c.hline(0, 16, 128, INK)
    c.hline(0, 23, 128, INK)
    c.hline(0, 30, 128, INK)
    c.outline_alpha()
    c.save("l7_pit_barrier.png")


# ---------------------------------------------------------------------------
#  REKWIZYTY (osłony i przeszkody)
# ---------------------------------------------------------------------------
def make_props():
    L = layout
    # paleta ze skrzynką (32 x 32)
    c = Canvas(32, 32)
    c.shaded(0, 24, 32, 8, WOOD, ink=False)                       # drewniana paleta
    for x in (2, 14, 26):
        c.rect(x, 26, 5, 6, WOOD[2])
    c.rect(0, 28, 32, 1, INK)
    cardboard_box(c, 3, 3, 26, 21)
    c.rect(6, 6, 6, 4, CREAM[0])
    c.outline_alpha()
    c.save("l7_pallet.png")

    # skrzynia (64 x 64): drewniana, z żółtym oznaczeniem i naklejką "TRELVOS"
    c = Canvas(64, 64)
    c.shaded(0, 0, 64, 64, WOOD, ink=False)
    for y in (0, 21, 42):
        c.rect(1, y + 1, 62, 3, WOOD[0])
        c.hline(1, y + 4, 62, WOOD[2])
    for x in (0, 28, 60):
        c.rect(x, 0, 4, 64, WOOD[1])
        c.vline(x, 0, 64, WOOD[0])
        c.vline(x + 3, 0, 64, WOOD[2])
    c.line(4, 4, 59, 59, WOOD[2])
    c.line(59, 4, 4, 59, WOOD[2])
    c.rect(14, 22, 36, 20, CREAM[1])
    c.frame(14, 22, 36, 20, INK)
    logo(c, 17, 28, 1, ORANGE[2], CREAM[2])
    hazard_stripe(c, 4, 58, 56, 4)
    for x, y in ((3, 3), (60, 3), (3, 60), (60, 60)):
        c.px(x, y, STEEL[0])
    c.outline_alpha()
    c.save("l7_crate.png")

    # wózek paletowy z paczkami (96 x 48)
    c = Canvas(96, 48)
    c.shaded(8, 30, 80, 6, STEEL, ink=False)                      # platforma wózka
    c.shaded(2, 4, 6, 32, DARK_STEEL)                             # pałąk
    c.rect(2, 2, 14, 4, DARK_STEEL[1])
    for wx in (14, 74):
        c.disc(wx, 41, 5, DARK_STEEL[2])
        c.disc(wx, 41, 3, STEEL[1])
    plastic_crate(c, 14, 14, 30, 16, BLUE_BOX)
    plastic_crate(c, 48, 18, 28, 12, GREEN_BOX)
    cardboard_box(c, 18, 4, 22, 10)
    cardboard_box(c, 52, 8, 18, 10)
    c.rect(8, 36, 80, 3, DARK_STEEL[2])
    c.outline_alpha()
    c.save("l7_cart.png")

    # stół stołówkowy (96 x 40): blat z kafelków, nogi, krzesła po bokach
    c = Canvas(96, 40)
    for cx in (4, 78):                                            # krzesła
        c.shaded(cx, 12, 14, 4, DARK_STEEL)
        c.rect(cx + (0 if cx < 40 else 12), 2, 2, 12, DARK_STEEL[1])
        c.rect(cx + 1, 16, 2, 22, DARK_STEEL[2])
        c.rect(cx + 11, 16, 2, 22, DARK_STEEL[2])
    c.shaded(10, 8, 76, 5, CREAM, ink=False)                      # blat
    c.hline(10, 8, 76, TEAL[0])
    c.rect(14, 13, 4, 25, DARK_STEEL[1])
    c.rect(78, 13, 4, 25, DARK_STEEL[1])
    c.rect(14, 36, 68, 2, DARK_STEEL[2])
    c.rect(24, 3, 8, 5, RED_BOX[1])                               # taca i kubek
    c.hline(24, 3, 8, RED_BOX[0])
    c.rect(52, 2, 5, 6, CREAM[0])
    c.rect(53, 3, 3, 1, TEAL[1])
    c.outline_alpha()
    c.save("l7_table.png")

    # lada wydawcza (192 x 64): stal nierdzewna, szyba osłonowa, tace, podgrzewacze
    c = Canvas(192, 64)
    c.shaded(0, 20, 192, 44, STEEL, ink=False)
    for x in range(4, 188, 48):
        c.shaded(x, 26, 40, 30, DARK_STEEL)
        c.rect(x + 4, 30, 32, 22, hexc("#1a2030"))
        c.rect(x + 14, 44, 12, 4, ORANGE[1])
        c.hline(x + 4, 30, 32, hexc("#2c3548"))
    c.rect(0, 60, 192, 4, DARK_STEEL[2])
    c.shaded(0, 12, 192, 8, TEAL, ink=False)                      # blat
    for x in range(10, 180, 36):                                  # tace z jedzeniem
        c.rect(x, 7, 22, 5, STEEL[0])
        c.rect(x + 2, 4, 18, 3, (ORANGE, YELLOW, GREEN_BOX)[(x // 36) % 3][1])
    c.rect(0, 0, 192, 3, hexc("#cfe8ea"))                         # szyba (jasna listwa)
    for x in (0, 94, 188):
        c.rect(x, 0, 4, 12, STEEL[1])
    c.hline(0, 3, 192, hexc("#8ab0b4"))
    c.outline_alpha()
    c.save("l7_counter.png")

    # zasilacz awaryjny UPS (64 x 64): szafa z wyświetlaczem i diodami
    c = Canvas(64, 64)
    c.shaded(0, 0, 64, 64, BLACK_RACK, ink=False)
    c.rect(4, 4, 56, 12, hexc("#0f131d"))
    c.rect(8, 7, 20, 6, hexc("#0a3a2a"))
    draw_text(c, 9, 8, "UPS", 1, LED_G)
    for i in range(6):
        c.rect(34 + i * 4, 8, 2, 4, (LED_G, LED_G, LED_G, LED_A, LED_C, LED_G)[i])
    for y in range(20, 56, 6):
        c.rect(6, y, 52, 4, hexc("#1a1f2e"))
        c.hline(6, y, 52, hexc("#323a50"))
        for x in range(8, 54, 4):
            c.px(x, y + 2, hexc("#0c0f18"))
    c.rect(4, 58, 56, 4, DARK_STEEL[2])
    hazard_stripe(c, 4, 56, 56, 2)
    c.outline_alpha()
    c.save("l7_ups.png")

    # agregat chłodzący (96 x 64): kratki wentylatorów, rury, żółta tabliczka
    c = Canvas(96, 64)
    c.shaded(0, 0, 96, 64, STEEL, ink=False)
    for fx in (6, 54):
        c.rect(fx, 8, 36, 36, hexc("#1a2030"))
        c.disc(fx + 18, 26, 15, hexc("#0e121b"))
        for ang in range(0, 360, 45):
            import math
            c.line(fx + 18, 26, fx + 18 + int(14 * math.cos(math.radians(ang))), 26 + int(14 * math.sin(math.radians(ang))), DARK_STEEL[1])
        c.disc(fx + 18, 26, 3, STEEL[0])
        c.frame(fx, 8, 36, 36, DARK_STEEL[2])
    c.rect(4, 48, 88, 10, DARK_STEEL[1])
    c.hline(4, 48, 88, DARK_STEEL[0])
    draw_text(c, 8, 50, "COOL", 1, CREAM[0])
    c.rect(66, 50, 22, 6, YELLOW[1])
    c.rect(68, 52, 18, 2, INK)
    c.rect(2, 60, 92, 4, DARK_STEEL[2])
    c.outline_alpha()
    c.save("l7_cooler.png")

    # wózek suwnicy z hakiem (32 x 80): pierścień haka w wierszu 68 (środek x 16) = punkt zaczepienia
    anchor_row = layout.ANCHOR["y"] - layout.HOIST["y"]
    c = Canvas(32, 80)
    c.shaded(4, 0, 24, 12, DARK_STEEL, ink=True)                  # wózek na belce
    c.rect(7, 12, 4, 4, STEEL[1])
    c.rect(21, 12, 4, 4, STEEL[1])
    c.rect(15, 12, 2, anchor_row - 22, STEEL[2])                  # łańcuch
    for y in range(14, anchor_row - 10, 4):
        c.rect(14, y, 4, 2, STEEL[0])
    c.shaded(10, anchor_row - 10, 12, 8, YELLOW, ink=True)        # blok haka
    c.disc(16, anchor_row + 3, 4, STEEL[0])                       # pierścień
    c.disc(16, anchor_row + 3, 2, hexc("#0a0d14"))
    c.px(16, anchor_row, YELLOW[0])
    c.save("l7_hoist.png")

    # grodzia (80 x 430): stalowa przegroda od sufitu do wysokości 1130, z pasami ostrzegawczymi na dole
    h = layout.BULKHEAD["h"]
    c = Canvas(80, h, DARK_STEEL[1])
    c.vline(0, 0, h, INK)
    c.vline(79, 0, h, INK)
    c.vline(1, 0, h, DARK_STEEL[0])
    c.vline(78, 0, h, DARK_STEEL[2])
    rng = random.Random(8)
    for y in range(0, h, 64):
        c.hline(2, y, 76, DARK_STEEL[2])
        c.hline(2, y + 1, 76, DARK_STEEL[0])
        for x in (6, 72):
            c.disc(x, y + 8, 1, STEEL[0])
    for _ in range(80):
        c.px(rng.randrange(3, 77), rng.randrange(h), DARK_STEEL[0] if rng.random() < 0.5 else DARK_STEEL[2])
    hazard_stripe(c, 2, h - 26, 76, 12)
    c.rect(2, h - 14, 76, 14, hexc("#10141e"))
    c.hline(2, h - 14, 76, STEEL[2])
    draw_text(c, 12, 18, "B-4", 2, YELLOW[1])
    c.rect(8, 44, 64, 4, hexc("#10141e"))
    c.save("l7_bulkhead.png")

    # kanał wentylacyjny (304 x 46): ciemne wnętrze z żebrami, wentylator na końcu, tabliczka "NIE WCHODZIC"
    t = layout.TUNNEL
    c = Canvas(t["w"], t["floor"] - t["ceil"], hexc("#10151f"))
    for x in range(0, t["w"], 32):
        c.rect(x, 0, 3, c.h, hexc("#1c2434"))
        c.vline(x, 0, c.h, hexc("#2c3850"))
    c.rect(0, 0, c.w, 3, hexc("#2a3446"))
    c.rect(0, c.h - 4, c.w, 4, hexc("#2a3446"))
    c.hline(0, c.h - 4, c.w, hexc("#4a566e"))
    for x in range(10, t["w"] - 10, 6):                           # kratka podłogowa
        c.px(x, c.h - 2, hexc("#3a465e"))
    c.rect(24, 10, 60, 24, hexc("#0a0d14"))                       # tabliczka (z dala od panelu)
    c.frame(24, 10, 60, 24, ORANGE[1])
    draw_text(c, 27, 14, "PANEL", 1, ORANGE[0])
    draw_text(c, 27, 24, "SERWIS", 1, ORANGE[0])
    c.save("l7_tunnel.png")


# ---------------------------------------------------------------------------
#  ŚCIANY POMIESZCZEŃ (tło za graczem) i TŁO
# ---------------------------------------------------------------------------
def darken(c, x, y, w, h, factor):
    """Przyciemnia prostokąt (mnoży kolory przez factor < 1): rekwizyty w tle są ciemniejsze od tego, po czym się chodzi."""
    x0, y0, x1, y1 = max(0, x), max(0, y), min(c.w, x + w), min(c.h, y + h)
    if x1 > x0 and y1 > y0:
        c.a[y0:y1, x0:x1, :3] = (c.a[y0:y1, x0:x1, :3] * factor).astype(np.uint8)


def vignette_top(c, depth=70, strength=0.55):
    """Cień pod sufitem: góra ściany ciemniejsza (pikselowo, kilka pasów)."""
    for i in range(depth // 6):
        f = 1 - strength * (1 - i / (depth / 6))
        darken(c, 0, i * 6, c.w, 6, f)


def base_wall(c, panel_w=128, tones=WALL, seed=1, base_dark=0.8):
    """Ściana z płyt: pionowe szwy co panel_w px, nity, delikatne plamy."""
    rng = random.Random(seed)
    c.rect(0, 0, c.w, c.h, tones[1])
    for x in range(0, c.w, panel_w):
        c.vline(x, 0, c.h, tones[2])
        c.vline(x + 1, 0, c.h, tones[0])
        for y in range(10, c.h, 70):
            c.px(x + 4, y, tones[2])
            c.px(x + panel_w - 5, y, tones[2])
    for _ in range(c.w * c.h // 90):
        c.px(rng.randrange(c.w), rng.randrange(c.h), tones[0] if rng.random() < 0.45 else tones[2])
    darken(c, 0, 0, c.w, c.h, base_dark)


def wainscot(c, height=56, y_floor=None):
    """Cokół ściany: ciemny beton z żółtą linią."""
    y_floor = c.h if y_floor is None else y_floor
    c.rect(0, y_floor - height, c.w, height, hexc("#2b3342"))
    c.hline(0, y_floor - height, c.w, hexc("#4a566c"))
    c.rect(0, y_floor - height + 1, c.w, 2, hexc("#202735"))
    c.rect(0, y_floor - 14, c.w, 3, YELLOW[2])
    for x in range(0, c.w, 96):
        c.vline(x, y_floor - height + 3, height - 3, hexc("#202735"))


def lamps_row(c, y, spacing, offset=60, cone=0, w=34):
    for x in range(offset, c.w - 40, spacing):
        ceiling_lamp(c, x, y, w, True, cone)


def roller_shutter(c, x, y, w, h, label, open_px=0, seed=0):
    """Brama rozładunkowa: rama w pasy, lamele, opcjonalnie podniesiona (widać noc za nią)."""
    c.rect(x - 5, y - 5, w + 10, h + 5, hexc("#10141e"))
    hazard_stripe(c, x - 5, y - 5, w + 10, 4)
    hazard_stripe(c, x - 5, y - 5, 4, h + 5)
    hazard_stripe(c, x + w + 1, y - 5, 4, h + 5)
    c.rect(x, y, w, h, hexc("#0c1426"))                          # otwór (noc na zewnątrz)
    rng = random.Random(seed)
    for _ in range(14):
        c.px(x + rng.randrange(w), y + rng.randrange(max(1, h // 2)), hexc("#8fb0ff") if rng.random() < 0.5 else hexc("#3a4a86"))
    c.rect(x, y + h - 16, w, 16, hexc("#1c2646"))
    for i in range(0, w, 14):                                    # światełka miasta daleko
        c.px(x + 4 + i, y + h - 22 - (i * 7) % 5, hexc("#ffd36a"))
    slats_h = h - open_px
    for yy in range(0, slats_h, 5):                             # lamele opuszczonej części (od góry)
        c.rect(x, y + yy, w, 4, STEEL[1] if (yy // 5) % 2 == 0 else STEEL[2])
        c.hline(x, y + yy, w, STEEL[0])
    c.rect(x, y + slats_h, w, 3, DARK_STEEL[2])                  # dolna listwa
    c.rect(x + w // 2 - 6, y + slats_h - 6, 12, 5, YELLOW[1])    # uchwyt
    c.frame(x - 1, y - 1, w + 2, h + 1, INK)
    sign(c, x + w // 2 - text_width(label, 2) // 2 - 3, y - 26, label, 2, YELLOW[0])


def extinguisher(c, x, y):
    c.rect(x - 1, y - 1, 16, 26, INK)
    c.rect(x, y, 14, 24, RED_BOX[1])
    c.hline(x, y, 14, RED_BOX[0])
    c.rect(x + 3, y + 4, 8, 10, hexc("#f0f0e0"))
    c.rect(x + 6, y + 5, 2, 8, RED_BOX[1])
    c.rect(x + 4, y + 8, 6, 2, RED_BOX[1])
    c.rect(x + 3, y + 16, 8, 6, DARK_STEEL[1])


def electrical_cabinet(c, x, y, w=30, h=46):
    c.shaded(x, y, w, h, DARK_STEEL, ink=True)
    c.rect(x + 3, y + 3, w - 6, 10, hexc("#0f131d"))
    c.px(x + 5, y + 6, LED_G)
    c.px(x + 8, y + 6, LED_A)
    c.px(x + 11, y + 6, LED_R)
    # piktogram: błyskawica
    c.line(x + w // 2 + 2, y + 18, x + w // 2 - 2, y + 28, YELLOW[0])
    c.line(x + w // 2 - 2, y + 28, x + w // 2 + 3, y + 28, YELLOW[0])
    c.line(x + w // 2 + 3, y + 28, x + w // 2 - 1, y + 38, YELLOW[0])
    c.rect(x + w - 6, y + h // 2, 2, 8, STEEL[0])


def service_door(c, x, y, label):
    c.rect(x - 2, y - 2, 48, 88, INK)
    c.shaded(x, y, 44, 84, DARK_STEEL)
    c.rect(x + 4, y + 4, 36, 42, DARK_STEEL[2])
    c.frame(x + 4, y + 4, 36, 42, DARK_STEEL[0])
    c.rect(x + 8, y + 52, 28, 22, DARK_STEEL[1])
    hazard_stripe(c, x + 2, y + 76, 40, 6)
    c.rect(x + 36, y + 40, 3, 8, STEEL[0])                       # klamka
    c.rect(x + 30, y + 22, 8, 12, hexc("#10141e"))               # czytnik kart
    c.px(x + 34, y + 25, LED_R)
    sign(c, x + 22 - text_width(label, 1) // 2 - 2, y - 14, label, 1, YELLOW[0], pad=2)


def vent_grille(c, x, y, w=44, h=22):
    c.rect(x - 1, y - 1, w + 2, h + 2, INK)
    c.rect(x, y, w, h, DARK_STEEL[2])
    for yy in range(y + 2, y + h - 1, 3):
        c.rect(x + 2, yy, w - 4, 2, hexc("#10141e"))
        c.hline(x + 2, yy + 2, w - 4, DARK_STEEL[0])
    c.frame(x, y, w, h, DARK_STEEL[1])


def fire_exit_sign(c, x, y, arrow=">"):
    c.rect(x, y, 44, 14, hexc("#0e3a24"))
    c.frame(x, y, 44, 14, hexc("#1c7a48"))
    draw_text(c, x + 4, y + 4, "WYJSCIE" if False else "EXIT", 1, hexc("#d8ffe0"))
    draw_text(c, x + 30, y + 4, arrow, 1, hexc("#d8ffe0"))


def make_wall_dock():
    d = layout.WALL_DOCK
    c = Canvas(d["w"], d["h"])
    base_wall(c, 128, seed=11)
    vignette_top(c)
    # rury i belka przy suficie
    pipe_h(c, 0, 26, c.w, 7, DARK_STEEL)
    pipe_h(c, 0, 38, c.w, 5, STEEL)
    lamps_row(c, 4, 250, 90, cone=120)
    wainscot(c, 56)
    # bramy rozładunkowe
    roller_shutter(c, 150, 190, 200, 240, "DOK 1", open_px=120, seed=1)
    roller_shutter(c, 640, 190, 200, 240, "DOK 2", open_px=0, seed=2)
    roller_shutter(c, 1130, 190, 200, 240, "DOK 3", open_px=40, seed=3)
    # napis i logo
    c.rect(430, 60, 160, 40, hexc("#10141e"))
    c.frame(430, 60, 160, 40, ORANGE[2])
    logo(c, 440, 66, 3)
    draw_text(c, 458, 90, "LOGISTYKA", 1, CREAM[1])
    # drobiazgi: gaśnice, szafki elektryczne, tablica z regulaminem, strzałki
    extinguisher(c, 40, 410)
    extinguisher(c, 560, 410)
    extinguisher(c, 1010, 410)
    electrical_cabinet(c, 388, 380)
    electrical_cabinet(c, 880, 380)
    electrical_cabinet(c, 1400, 380)
    sign(c, 1450, 190, "TYLKO PERSONEL", 1, ORANGE[0])
    c.rect(1450, 206, 100, 44, CREAM[1])
    c.frame(1450, 206, 100, 44, INK)
    for i in range(4):
        c.rect(1456, 212 + i * 9, 88 - i * 6, 3, hexc("#5a5040"))
    fire_exit_sign(c, 1560, 120)
    # pasy hazard przy bramach (na ścianie nad cokołem)
    for x in (150, 640, 1130):
        hazard_stripe(c, x - 5, c.h - 70, 210, 8)
    c.save("l7_wall_dock.png")


def shelf_unit(c, x, floor_y, w, h, seed, dim=0.62):
    """Regał magazynowy: słupki, półki, kartony i skrzynki (w tle, przyciemniony)."""
    rng = random.Random(seed)
    top = floor_y - h
    for px in (x, x + w - 5):
        c.shaded(px, top, 5, h, (ORANGE[0], ORANGE[1], ORANGE[2]))
    shelves = 5
    for i in range(shelves):
        sy = top + 8 + i * ((h - 18) // shelves)
        c.shaded(x, sy + (h - 18) // shelves - 6, w, 5, DARK_STEEL)
        cx = x + 8
        while cx < x + w - 14:
            bw = rng.choice((14, 18, 22, 26))
            bh = rng.choice((14, 18, 22)) if i < shelves - 1 else rng.choice((12, 16))
            bh = min(bh, (h - 18) // shelves - 10)
            if cx + bw > x + w - 8:
                break
            by = sy + (h - 18) // shelves - 6 - bh
            kind = rng.random()
            if kind < 0.55:
                cardboard_box(c, cx, by, bw, bh)
            elif kind < 0.8:
                plastic_crate(c, cx, by, bw, bh, rng.choice((BLUE_BOX, GREEN_BOX, RED_BOX)))
            cx += bw + rng.choice((2, 4, 6))
    darken(c, x - 1, top - 1, w + 2, h + 2, dim)


def i_beam(c, x, y, w, thick=16):
    """Belka dwuteowa (tor suwnicy): półki i środnik, z nitami."""
    c.rect(x, y, w, 4, STEEL[1])
    c.hline(x, y, w, STEEL[0])
    c.rect(x, y + thick - 4, w, 4, STEEL[1])
    c.hline(x, y + thick - 1, w, STEEL[2])
    c.rect(x, y + 4, w, thick - 8, DARK_STEEL[1])
    for xx in range(x + 8, x + w - 4, 24):
        c.px(xx, y + 7, STEEL[0])
    c.frame(x - 1, y - 1, w + 2, thick + 2, INK)


def make_wall_store():
    d = layout.WALL_STORE
    c = Canvas(d["w"], d["h"])
    base_wall(c, 160, seed=21)
    vignette_top(c)
    pipe_h(c, 0, 24, c.w, 6, DARK_STEEL)
    lamps_row(c, 4, 280, 100, cone=190, w=40)
    wainscot(c, 44)
    # regały wzdłuż ściany (pomijamy pas przy suwnicy, żeby belka i hak były czytelne)
    seed = 100
    x = 20
    while x < c.w - 140:
        w = 132
        h = 300 if (x // 150) % 3 else 340
        shelf_unit(c, x, c.h - 12, w, h, seed)
        seed += 1
        x += w + 16
    # tablice stref nad regałami
    for i, name in enumerate(("A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3", "D1", "D2", "D3", "E1", "E2", "E3", "F1", "F2", "F3")):
        px = 40 + i * 148
        if px < c.w - 100:
            sign(c, px + 40, 62, "ZONA " + name[0] + name[1], 1, YELLOW[0], pad=2)
    # tor suwnicy (belka) przez środek hali + wózki
    beam_x0 = layout.GL["x"] - 120 - d["x"]
    beam_x1 = layout.GR["x"] + layout.GR["w"] + 60 - d["x"]
    by = 840 - d["y"]
    i_beam(c, beam_x0, by, beam_x1 - beam_x0)
    for ex in (beam_x0 - 10, beam_x1 - 4):                       # ograniczniki na końcach toru
        c.rect(ex, by - 4, 14, 24, ORANGE[1])
        c.frame(ex, by - 4, 14, 24, INK)
        hazard_stripe(c, ex + 2, by + 2, 10, 8)
    for sx in range(beam_x0 + 120, beam_x1 - 80, 260):           # wsporniki toru
        c.rect(sx, by + 16, 6, 36, DARK_STEEL[1])
        c.rect(sx - 8, by + 14, 22, 4, DARK_STEEL[0])
    # wózek zapasowy zaparkowany przy lewym końcu
    c.shaded(beam_x0 + 40, by - 6, 26, 8, DARK_STEEL, ink=True)
    # duży napis i logo
    c.rect(22, 90, 220, 52, hexc("#10141e"))
    c.frame(22, 90, 220, 52, ORANGE[2])
    draw_text(c, 34, 98, "MAGAZYN", 3, YELLOW[0])
    logo(c, 150, 124, 1)
    # oznaczenie skoczni (tablica z napisem i strzałką w górę) przy podstawie galerii
    spx = layout.SPRING1["x"] - d["x"]
    sign(c, spx - 24, c.h - 150, "SKOCZNIA", 1, ORANGE[0])
    draw_text(c, spx + 18, c.h - 130, "^", 2, YELLOW[0])
    # strzałka-wskazówka do galerii serwisowej
    sign(c, layout.GR["x"] - d["x"] + 120, c.h - 330, "GALERIA SERWISOWA", 1, CREAM[0])
    # gaśnice, szafki
    for ex in (360, 1500, 2300):
        extinguisher(c, ex, c.h - 70)
    for ex in (700, 2000, 2500):
        electrical_cabinet(c, ex, c.h - 76)
    c.save("l7_wall_store.png")


def make_wall_canteen():
    d = layout.WALL_CANTEEN
    c = Canvas(d["w"], d["h"])
    base_wall(c, 128, seed=31, base_dark=0.85)
    # dolna część: kafelki (łazienkowo-kuchenne), od 230 px wzwyż malowana ściana
    tile_top = c.h - 240
    for yy in range(tile_top, c.h, 16):
        for xx in range(0, c.w, 16):
            c.rect(xx, yy, 15, 15, TILE[1])
            c.hline(xx, yy, 15, TILE[0])
            c.vline(xx, yy, 15, TILE[0])
            c.hline(xx, yy + 14, 15, TILE[2])
    darken(c, 0, tile_top, c.w, 240, 0.62)
    c.rect(0, tile_top - 6, c.w, 6, ORANGE[1])                   # pas w kolorze Trelvosu
    c.hline(0, tile_top - 6, c.w, ORANGE[0])
    c.hline(0, tile_top - 1, c.w, ORANGE[2])
    vignette_top(c)
    pipe_h(c, 0, 22, c.w, 6, DARK_STEEL)
    lamps_row(c, 4, 230, 80, cone=170, w=38)
    wainscot(c, 20)
    # napis, menu, zegar
    c.rect(40, 56, 190, 40, hexc("#10141e"))
    c.frame(40, 56, 190, 40, ORANGE[2])
    draw_text(c, 52, 66, "STOLOWKA", 3, YELLOW[0])
    # tablica menu (zielona tablica kredowa)
    mx, my = 300, 120
    c.rect(mx - 2, my - 2, 160, 108, INK)
    c.rect(mx, my, 156, 104, hexc("#1c3a30"))
    c.frame(mx, my, 156, 104, WOOD[1])
    draw_text(c, mx + 50, my + 6, "MENU", 2, CREAM[0])
    for i, (a, b) in enumerate((("ZUPA", "6"), ("OBIAD", "14"), ("KAWA", "4"), ("DESER", "5"))):
        draw_text(c, mx + 10, my + 30 + i * 17, a, 1, CREAM[1])
        draw_text(c, mx + 120, my + 30 + i * 17, b, 1, YELLOW[0])
        for dx in range(50, 112, 4):
            c.px(mx + dx, my + 34 + i * 17, hexc("#3a6a58"))
    # okno wydawcze do kuchni (za ladą) z roletą
    kx, ky = 560, 190
    c.rect(kx - 3, ky - 3, 270, 126, INK)
    c.rect(kx, ky, 264, 120, hexc("#1a1208"))
    c.rect(kx + 6, ky + 6, 252, 108, hexc("#3a2a14"))
    c.glow(kx + 132, ky + 40, 120, 50, LAMP[1], 0.3, 3)
    for i in range(7):                                           # garnki i półka w kuchni
        c.shaded(kx + 14 + i * 34, ky + 70, 24, 18, STEEL)
    c.rect(kx + 6, ky + 90, 252, 5, DARK_STEEL[1])
    for yy in range(0, 34, 5):                                   # roleta podniesiona do połowy
        c.rect(kx, ky + yy, 264, 4, STEEL[1] if (yy // 5) % 2 == 0 else STEEL[2])
    c.frame(kx, ky, 264, 120, STEEL[2])
    # szatnia: rząd szafek
    sx0 = 1010
    c.rect(sx0 - 6, c.h - 232, 500, 214, hexc("#10141e"))
    for i in range(14):
        lx = sx0 + i * 34
        tones = (BLUE_BOX, DARK_STEEL, BLUE_BOX, TEAL)[i % 4]
        c.shaded(lx, c.h - 224, 32, 196, tones, ink=True)
        for vy in range(c.h - 214, c.h - 180, 4):
            c.hline(lx + 6, vy, 20, tones[2])
        c.rect(lx + 22, c.h - 138, 4, 10, STEEL[0])
        c.rect(lx + 4, c.h - 150, 12, 7, hexc("#10141e"))
        draw_text(c, lx + 5, c.h - 149, str(i + 1), 1, ORANGE[0])
    sign(c, sx0 + 170, c.h - 262, "SZATNIA", 2, CREAM[0])
    # automaty z napojami i przekąskami (świecące)
    for vx in (760, 850):
        c.shaded(vx, c.h - 150, 76, 122, (hexc("#d84a4a"), hexc("#a82e36"), hexc("#701c26")), ink=True)
        c.rect(vx + 6, c.h - 142, 48, 80, hexc("#14243a"))
        c.glow(vx + 30, c.h - 102, 40, 50, hexc("#8fd0ff"), 0.35, 3)
        for r in range(4):
            for q in range(3):
                col = (YELLOW[1], BLUE_BOX[1], GREEN_BOX[1], ORANGE[1])[(r + q) % 4]
                c.rect(vx + 9 + q * 15, c.h - 136 + r * 18, 11, 12, col)
        c.rect(vx + 58, c.h - 140, 12, 30, hexc("#0a0d14"))
        c.rect(vx + 10, c.h - 54, 40, 14, hexc("#0a0d14"))
        c.px(vx + 62, c.h - 120, LED_G)
    # zegar ścienny
    zx, zy = 700, 80
    c.disc(zx, zy, 15, INK)
    c.disc(zx, zy, 13, CREAM[0])
    c.line(zx, zy, zx + 6, zy - 7, INK)
    c.line(zx, zy, zx - 8, zy + 3, INK)
    c.px(zx, zy, RED_BOX[1])
    # znak wyjścia i gaśnica
    fire_exit_sign(c, c.w - 70, 100, "<")
    extinguisher(c, c.w - 60, c.h - 80)
    extinguisher(c, 700, c.h - 80)
    c.save("l7_wall_canteen.png")


def make_wall_shaft():
    d = layout.WALL_SHAFT
    c = Canvas(d["w"], d["h"], hexc("#161c28"))
    rng = random.Random(41)
    for _ in range(d["w"] * d["h"] // 40):
        c.px(rng.randrange(d["w"]), rng.randrange(d["h"]), hexc("#1e2636") if rng.random() < 0.6 else hexc("#10141e"))
    pipe_v(c, 10, 0, d["h"], 8, DARK_STEEL)
    pipe_v(c, d["w"] - 18, 0, d["h"], 6, DARK_STEEL)
    # strzałki w górę: wskazówka dla wspinaczki po ścianach
    for y in range(40, d["h"] - 50, 78):
        draw_text(c, d["w"] // 2 - 7, y, "^", 3, YELLOW[2])
    sign(c, 18, d["h"] - 40, "P-1", 1, YELLOW[0], pad=2)
    sign(c, 18, 200 - 40 + 10, "P0", 1, YELLOW[0], pad=2)         # poziom korytarza (y = 900)
    hazard_stripe(c, 0, d["h"] - 12, d["w"], 8)
    c.save("l7_wall_shaft.png")


def make_wall_corridor():
    d = layout.WALL_CORRIDOR
    c = Canvas(d["w"], d["h"])
    base_wall(c, 96, seed=51, base_dark=0.78)
    # korytarz kablowy pod sufitem
    c.rect(0, 0, c.w, 26, hexc("#141926"))
    c.hline(0, 26, c.w, hexc("#4a566c"))
    for y, col in ((6, ORANGE[1]), (11, hexc("#3a8ad8")), (16, hexc("#58c878")), (21, hexc("#8a8a96"))):
        c.rect(0, y, c.w, 2, col)
        c.hline(0, y, c.w, tuple(min(255, v + 40) for v in col))
    for x in range(30, c.w, 120):
        c.rect(x, 0, 4, 26, DARK_STEEL[1])
    lamps_row(c, 28, 240, 120, cone=140, w=30)
    wainscot(c, 40)
    # drzwi techniczne, szafki, kratki wentylacyjne
    door_x = [260, 620, 1230, 1690]
    for i, dx in enumerate(door_x):
        service_door(c, dx, c.h - 84 - 2, ("TECH 1", "TECH 2", "ZASILANIE", "TECH 3")[i])
    for vx in (140, 480, 900, 1460, 1900):
        vent_grille(c, vx, 62)
    for ex in (420, 1060, 1580):
        electrical_cabinet(c, ex, c.h - 48)
    extinguisher(c, 1930, c.h - 52)
    # opisy przy kanale wentylacyjnym
    h1 = layout.HATCH1["x"] - d["x"]
    sign(c, h1 - 36, 66, "KANAL WENT.", 1, ORANGE[0])
    for ax in range(h1 - 40, h1 + 120, 14):                       # strzałki w dół nad kratką
        pass
    h2 = layout.HATCH2["x"] - d["x"]
    sign(c, h2 - 10, 66, "WYJSCIE KANALU", 1, ORANGE[0])
    # rów kablowy
    ps = layout.PIT_SHAFT["x"] - d["x"]
    sign(c, ps - 30, 66, "KOLCE W ROWIE", 1, YELLOW[0])
    # logo i drogowskaz do serwerowni na końcu
    logo(c, 40, 100, 2)
    sign(c, c.w - 150, 66, "SERWEROWNIA", 1, CREAM[0])
    draw_text(c, c.w - 40, 66, ">", 1, YELLOW[0])
    c.save("l7_wall_corridor.png")


def server_rack(c, x, floor_y, w, h, seed):
    rng = random.Random(seed)
    top = floor_y - h
    c.shaded(x, top, w, h, BLACK_RACK, ink=True)
    for yy in range(top + 6, floor_y - 6, 6):
        c.rect(x + 3, yy, w - 6, 4, hexc("#12151f"))
        c.hline(x + 3, yy, w - 6, hexc("#2c3246"))
        for lx in range(x + 5, x + w - 6, 4):
            r = rng.random()
            if r < 0.30:
                c.rect(lx, yy + 1, 2, 2, LED_G)
            elif r < 0.42:
                c.rect(lx, yy + 1, 2, 2, LED_A)
            elif r < 0.50:
                c.rect(lx, yy + 1, 2, 2, LED_C)
            elif r < 0.53:
                c.rect(lx, yy + 1, 2, 2, LED_R)
    darken(c, x - 1, top - 1, w + 2, h + 2, 0.95)


def make_wall_server():
    d = layout.WALL_SERVER
    c = Canvas(d["w"], d["h"], hexc("#10141e"))
    rng = random.Random(61)
    for _ in range(c.w * c.h // 60):
        c.px(rng.randrange(c.w), rng.randrange(c.h), hexc("#161c2a") if rng.random() < 0.6 else hexc("#0c1018"))
    vignette_top(c, 60, 0.4)
    # sufitowe tace kablowe z pomarańczowymi i niebieskimi kablami
    c.rect(0, 14, c.w, 16, hexc("#1c2230"))
    c.hline(0, 14, c.w, hexc("#4a566c"))
    for y, col in ((17, ORANGE[1]), (21, hexc("#3a8ad8")), (25, hexc("#58c878"))):
        c.rect(0, y, c.w, 2, col)
    for x in range(40, c.w, 140):
        c.rect(x, 14, 4, 16, DARK_STEEL[1])
    lamps_row(c, 32, 300, 160, cone=100, w=40)
    # rzędy szaf serwerowych (dwa rzędy: bliższy jaśniejszy, dalszy ciemniejszy)
    seed = 200
    for x in range(10, c.w - 10, 50):
        server_rack(c, x, c.h - 6, 44, 150, seed)
        seed += 1
    for x in range(34, c.w - 30, 50):
        if (x // 50) % 7 != 3:
            darken(c, x, c.h - 190, 0, 0, 1)
    # zimny korytarz: niebieska poświata przy podłodze
    c.glow(c.w // 2, c.h - 20, c.w // 2, 50, hexc("#3a6ad8"), 0.18, 4)
    # nad szafami: napisy
    c.rect(60, 78, 240, 52, hexc("#0a0d14"))
    c.frame(60, 78, 240, 52, ORANGE[2])
    draw_text(c, 72, 86, "SERWEROWNIA", 3, ORANGE[0])
    draw_text(c, 74, 112, "TRELVOS DATA CENTER", 1, CREAM[1])
    # tablica ostrzegawcza
    sign(c, c.w - 430, 90, "UWAGA: PANEL 3 NA POMOSCIE", 1, YELLOW[0])
    # rury chłodzące pionowe
    for px in range(480, c.w, 400):
        pipe_v(c, px, 32, c.h - 190, 6, STEEL)
    # pasy hazard przy podłodze
    c.save("l7_wall_server.png")


def make_interior_bg():
    """Tło 1280 x 720 (zapętla się poziomo): betonowa hala z filarami co 320 px, belkami i pasami świetlówek."""
    w, h = 1280, 720
    c = Canvas(w, h)
    rng = random.Random(71)
    top, bottom = np.array(hexc("#0e131d")), np.array(hexc("#26324a"))
    for y in range(h):
        t = y / (h - 1)
        col = top + (bottom - top) * t
        for x in range(w):
            d = ((x // 2 + y // 2) % 2) * 0.03
            c.a[y, x] = (*(col * (1 + d)).astype(np.uint8), 255)
    # szary beton: delikatne plamy
    for _ in range(w * h // 40):
        x, y = rng.randrange(w), rng.randrange(h)
        c.blend(x, y, hexc("#3a465e") if rng.random() < 0.5 else hexc("#0a0e16"), 0.35)
    # poziome belki konstrukcji
    for by in (80, 300, 520):
        c.rect(0, by, w, 14, hexc("#1a2132"))
        c.hline(0, by, w, hexc("#38445c"))
        c.hline(0, by + 13, w, hexc("#0a0e16"))
    # filary co 320 px
    for x in range(0, w, 320):
        c.rect(x + 20, 0, 56, h, hexc("#1c2436"))
        c.vline(x + 20, 0, h, hexc("#3a465e"))
        c.vline(x + 75, 0, h, hexc("#0a0e16"))
        c.rect(x + 14, 0, 68, 8, hexc("#2a3448"))
        for y in range(40, h, 90):
            c.rect(x + 20, y, 56, 3, hexc("#10151f"))
    # pasy świetlówek i ich poświata
    for lx in range(100, w, 320):
        for ly in (60, 280, 500):
            c.rect(lx + 60, ly, 90, 4, hexc("#d8e8ff"))
            c.glow(lx + 105, ly + 8, 90, 24, hexc("#9ac0ff"), 0.2, 3)
    # okna serwisowe z przyciemnionym światłem
    for wx in range(210, w, 320):
        for wy in (140, 360):
            c.rect(wx, wy, 60, 40, hexc("#0a0e16"))
            c.rect(wx + 2, wy + 2, 56, 36, hexc("#16223a"))
            c.rect(wx + 2, wy + 24, 56, 14, hexc("#1c2c4c"))
            c.frame(wx, wy, 60, 40, hexc("#38445c"))
    c.save("l7_interior.png")


if __name__ == "__main__":
    make_tiles()
    make_props()
    make_interior_bg()
    make_wall_dock()
    make_wall_store()
    make_wall_canteen()
    make_wall_shaft()
    make_wall_corridor()
    make_wall_server()
