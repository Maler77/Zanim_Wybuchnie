"""Rysuje grafiki poziomu 2 (miasto w dzień): tło, chodnik, budynki (w tym trzy budynki firmy Trelvos), rekwizyty.

Uruchom z głównego katalogu repozytorium:   python "tools/make level 2 art.py"
(wymaga bibliotek Pillow i numpy:  pip install pillow numpy)

Powstają pliki w assets/ (nazwy zaczynają się od "l2_", żeby nie mieszały się z resztą):
  l2_city.png            panorama miasta 1280 x 480 w dzień (zapętla się poziomo bez szwu), tło z paralaksą
  l2_pavement.png        kafelek chodnika 32 x 40 (podłoże)
  l2_trelvos_market.png  sklep Trelvos (224 x 128, tło przy bombie 1)       l2_trelvos_bank.png  bank Trelvos (256 x 160, bomba 2)
  l2_trelvos_tower.png   wieża Trelvos (192 x 160, dach z bombą 3)           l2_trelvos_sign.png  neon na dachu wieży (128 x 48)
  l2_flat.png            kamienica (224 x 160), l2_cafe.png kawiarnia (192 x 128), l2_gate.png budynek z bramą (224 x 288),
  l2_warehouse.png       magazyn (256 x 160), l2_depot.png zajezdnia przy wyjściu (224 x 128)
  l2_scaffold.png        rusztowanie (64 x 176), l2_crane.png żuraw (176 x 368; hak na (28, 54))
  rekwizyty: l2_planter, l2_kiosk, l2_van, l2_container, l2_tree, l2_bench, l2_hydrant, l2_busstop, l2_lamp, l2_mailbox, l2_cones

Styl jak poziom 1: czarny kontur 1 px na rekwizytach, trzy tony cieniowania, ostre piksele; światło dnia pada z lewej góry
(jasny rant dachów), okna odbijają niebo. Kolory są w słownikach na górze, kształty w funkcjach draw_*.
"""

import importlib.util
import random
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"

# Canvas, hexc i INK bierzemy z narzędzia poziomu 1, żeby oba poziomy rysowały tak samo.
_spec = importlib.util.spec_from_file_location("level1_art", HERE / "make level 1 art.py")
_l1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_l1)
Canvas, hexc, INK, METAL, WOOD, GREEN = _l1.Canvas, _l1.hexc, _l1.INK, _l1.METAL, _l1.WOOD, _l1.GREEN

# Fasady: jasny (rant), bazowy, ciemny (cień / lewy brzeg)
BRICK = (hexc("#d88a62"), hexc("#b4694c"), hexc("#85473a"))
CREAM = (hexc("#f6ead0"), hexc("#dcc9a0"), hexc("#ac966f"))
STONE = (hexc("#d2d6de"), hexc("#a4abb9"), hexc("#737b8e"))
STEEL = (hexc("#9db4c4"), hexc("#6c859a"), hexc("#4a6074"))
SLATE = (hexc("#8895ad"), hexc("#5e6c88"), hexc("#414d66"))
TRELVOS = (hexc("#ffd23c"), hexc("#f0a81c"), hexc("#b8700e"))       # firmowy bursztyn Trelvos
TRELVOS_DARK = hexc("#1d2a44")                                       # granat tabliczki z napisem
SKY_GLASS = (hexc("#c4ecfa"), hexc("#74bde4"), hexc("#3f84b8"))
RIM = hexc("#ffffff")
RIM_DARK = hexc("#c9d2e0")
LIT = (hexc("#fff7b0"), hexc("#ffd84a"), hexc("#d9a010"))
AWN_A = hexc("#2f9a7a")
AWN_B = hexc("#f4f0e0")
LEAF = (hexc("#7cc65a"), hexc("#4a9c3e"), hexc("#2c6a2c"))

# Mała czcionka 5 x 7 do napisów (tylko potrzebne litery).
FONT = {
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    " ": ["...", "...", "...", "...", "...", "...", "..."],
}


def text_width(text, scale, gap=1):
    return sum((3 if ch == " " else 5) * scale + gap * scale for ch in text) - gap * scale


def draw_text(c, x, y, text, scale, col, shadow=None, gap=1):
    """Rysuje napis czcionką 5 x 7 w skali `scale`; opcjonalny cień o 1 piksel gry w prawo i w dół."""
    cx = x
    for ch in text:
        glyph = FONT[ch]
        for ry, row in enumerate(glyph):
            for rx, v in enumerate(row):
                if v != "#":
                    continue
                if shadow is not None:
                    c.rect(cx + rx * scale + 1, y + ry * scale + 1, scale, scale, shadow)
                c.rect(cx + rx * scale, y + ry * scale, scale, scale, col)
        cx += (3 if ch == " " else 5) * scale + gap * scale
    return cx


def trelvos_sign(c, x, y, w, h, scale):
    """Tabliczka z napisem TRELVOS: granatowa płyta, bursztynowy napis i jasna ramka."""
    c.rect(x - 1, y - 1, w + 2, h + 2, INK)
    c.rect(x, y, w, h, TRELVOS_DARK)
    c.outline_box(x + 1, y + 1, w - 2, h - 2, TRELVOS[1])
    tw = text_width("TRELVOS", scale)
    tx = x + (w - tw) // 2
    ty = y + (h - 7 * scale) // 2
    draw_text(c, tx, ty, "TRELVOS", scale, TRELVOS[0], shadow=TRELVOS[2])


# ---------------------------------------------------------------------------
#  TŁO I CHODNIK
# ---------------------------------------------------------------------------

BG_W, BG_H = 1280, 480


def rect_wrap(a, x, y, w, h, col):
    """Prostokąt w tablicy tła z zawinięciem poziomym (dzięki temu panorama nie ma szwu)."""
    for xx in range(x, x + w):
        px = xx % BG_W
        y0, y1 = max(0, y), min(BG_H, y + h)
        if y1 > y0:
            a[y0:y1, px] = col


def draw_city():
    rng = random.Random(21)
    a = np.zeros((BG_H, BG_W, 3), dtype=np.uint8)

    # Niebo: pasy błękitu z rastrem 2 x 2 na styku (jak w Dzien.png), jaśniejsze przy horyzoncie.
    bands = [hexc("#2f86dc"), hexc("#3b94e4"), hexc("#4ea5ea"), hexc("#66b6f0"), hexc("#84caf4"), hexc("#a6dcf8"), hexc("#c4ecfb")]
    horizon = 340
    for y in range(horizon):
        t = y / (horizon - 1) * (len(bands) - 1)
        lo = int(t)
        hi = min(len(bands) - 1, lo + 1)
        frac = t - lo
        for x in range(BG_W):
            dither = ((x // 2 + y // 2) % 2) * 0.5 + 0.25
            a[y, x] = bands[hi] if frac > dither else bands[lo]
    a[horizon:] = bands[-1]

    # Słońce: żółta tarcza z jaśniejszym środkiem i obwódką z rastra.
    sx, sy, sr = 330, 150, 46
    for y in range(sy - sr - 6, sy + sr + 7):
        for x in range(sx - sr - 6, sx + sr + 7):
            d = ((x - sx) ** 2 + (y - sy) ** 2) ** 0.5
            if d <= sr - 14:
                a[y, x] = hexc("#fff59a")
            elif d <= sr - 5:
                a[y, x] = hexc("#fff04a") if (x + y) % 6 else hexc("#fff59a")
            elif d <= sr:
                a[y, x] = hexc("#ffe21a")
            elif d <= sr + 5 and (x // 2 + y // 2) % 2 == 0:
                a[y, x] = hexc("#fff08a")

    # Chmury: białe z błękitnym spodem i jasną górą, kilka kępek z pikselowych elips.
    white, pale, shade = hexc("#ffffff"), hexc("#eaf5ff"), hexc("#a9cdee")
    for _ in range(11):
        cx = rng.randrange(0, BG_W)
        cy = rng.randrange(30, 250)
        for _ in range(rng.randrange(3, 6)):
            bw = rng.randrange(26, 60)
            bh = rng.randrange(9, 17)
            ox = cx + rng.randrange(-50, 50)
            oy = cy + rng.randrange(-8, 8)
            for dy in range(-bh, bh + 1):
                span = int(bw * (1 - (dy / (bh + 0.5)) ** 2) ** 0.5)
                for dx in range(-span, span + 1):
                    yy = oy + dy
                    if not (0 <= yy < horizon):
                        continue
                    col = shade if dy > bh - 4 else (white if dy < -bh // 3 else pale)
                    a[yy, (ox + dx) % BG_W] = col

    # Trzy warstwy panoramy miasta: coraz bliżej, coraz ciemniej (jak szare bryły z Dzien.png).
    layers = [
        dict(base=hexc("#9fb6d2"), edge=hexc("#b4c8e0"), win=hexc("#b8cce4"), top=250, low=190, step=(40, 80)),
        dict(base=hexc("#7388a8"), edge=hexc("#8aa0c0"), win=hexc("#8ea3c2"), top=290, low=235, step=(46, 90)),
        dict(base=hexc("#4f6280"), edge=hexc("#647a9a"), win=hexc("#6a809f"), top=330, low=275, step=(50, 100)),
    ]
    ground_line = BG_H - 70
    for li, L in enumerate(layers):
        x = rng.randrange(0, 30)
        while x < BG_W + 40:
            bw = rng.randrange(*L["step"])
            top = rng.randrange(L["low"], L["top"] + 1)
            if (x // 7) % 5 == 0:
                top -= rng.randrange(20, 45)             # od czasu do czasu wyższy budynek
            rect_wrap(a, x, top, bw, ground_line - top, L["base"])
            rect_wrap(a, x, top, bw, 2, L["edge"])        # rant dachu w świetle
            rect_wrap(a, x, top, 2, ground_line - top, L["edge"])
            # Okna: siatka ciemniejszych kwadratów, w bliższej warstwie część świeci.
            for wy in range(top + 8, ground_line - 8, 10):
                for wx in range(x + 6, x + bw - 6, 9):
                    lit = li == 2 and rng.random() < 0.16
                    col = hexc("#ffe680") if lit else L["win"]
                    rect_wrap(a, wx, wy, 4, 5, col)
            # Dodatki na dachu: antena, nadbudówka, zbiornik.
            kind = rng.random()
            if kind < 0.3:
                rect_wrap(a, x + bw // 2, top - 14, 2, 14, L["edge"])
            elif kind < 0.55 and bw > 36:
                rect_wrap(a, x + 6, top - 8, bw // 3, 8, L["base"])
                rect_wrap(a, x + 6, top - 8, bw // 3, 2, L["edge"])
            x += bw - rng.randrange(0, 6)

    # Podstawa ulicy pod miastem: mur z jasnym gzymsem, a pod nim żywopłot (widać tylko wąski pas nad chodnikiem).
    for y in range(ground_line, BG_H):
        i = y - ground_line
        col = hexc("#6f7f98") if i < 3 else hexc("#56667f") if i < 28 else hexc("#43526a")
        a[y, :] = col
    a[ground_line, :] = hexc("#b8c6da")
    for x in range(0, BG_W, 32):                        # fugi muru
        a[ground_line + 3:BG_H, x] = (a[ground_line + 3:BG_H, x] * 0.86).astype(np.uint8)

    Image.fromarray(a, "RGB").save(ASSETS / "l2_city.png")
    print(f"l2_city.png: {BG_W}x{BG_H}")


def draw_pavement():
    """Chodnik 32 x 40: jasne płyty z fugami i krawężnik (jak w l1_sidewalk, ale w dzień i szary)."""
    c = Canvas(32, 40)
    slab_a, slab_b = hexc("#c9ced8"), hexc("#bfc5d1")
    joint = hexc("#98a0b2")
    for y in range(26):
        c.hline(0, y, 32, slab_a if y < 14 else slab_b)
    c.hline(0, 0, 32, hexc("#f0f3f8"))
    c.hline(0, 1, 32, hexc("#dde2ea"))
    c.vline(31, 2, 24, joint)                        # fuga między płytami (kafelek 32 px)
    c.vline(15, 14, 12, joint)
    c.hline(0, 13, 32, joint)
    rng = random.Random(5)
    for _ in range(8):
        c.px(rng.randrange(32), rng.randrange(3, 25), hexc("#b0b7c6"))
    c.hline(0, 26, 32, hexc("#e8ecf2"))             # krawężnik
    for y in range(27, 33):
        c.hline(0, y, 32, hexc("#a2aabb"))
    c.hline(0, 27, 32, hexc("#d0d6e2"))
    for y in range(33, 40):
        c.hline(0, y, 32, hexc("#767f94"))
    c.save("l2_pavement.png")


# ---------------------------------------------------------------------------
#  BUDYNKI
# ---------------------------------------------------------------------------

def facade(w, h, pal, seed, cap=8, pattern="brick"):
    light, base, dark = pal
    rng = random.Random(seed)
    c = Canvas(w, h, base)
    if pattern == "brick":
        for y in range(cap + 3, h, 4):
            c.hline(0, y, w, dark)
            off = 0 if (y // 4) % 2 == 0 else 5
            for x in range(off, w, 10):
                c.px(x, y + 1, dark)
                c.px(x, y + 2, dark)
        for _ in range(w * h // 90):
            c.px(rng.randrange(w), rng.randrange(cap + 2, h), light if rng.random() < 0.5 else dark)
    else:
        for _ in range(w * h // 38):
            c.px(rng.randrange(w), rng.randrange(cap + 2, h), light if rng.random() < 0.4 else dark)
    c.rect(0, cap, 3, h - cap, dark)                 # lewy bok w cieniu
    c.rect(w - 3, cap, 3, h - cap, light)            # prawy w świetle
    c.rect(0, 0, w, cap, light)                      # dach i attyka (po niej chodzi gracz)
    c.rect(0, cap - 2, w, 2, dark)
    c.hline(0, 0, w, RIM)
    c.hline(0, 1, w, RIM_DARK)
    for x in range(6, w - 6, 24):
        c.rect(x, 2, 3, cap - 4, base)
    return c


def window(c, x, y, ww, wh, kind="glass", sill=True, curtain=None):
    """Okno w dzień: szyba odbija niebo (jasny pas na górze i ukośny odblask); kind: glass | lit | open."""
    c.rect(x - 1, y - 1, ww + 2, wh + 2, INK)
    if kind == "lit":
        c.rect(x, y, ww, wh, LIT[1])
        c.rect(x + 1, y + 1, ww - 2, wh // 2 - 1, LIT[0])
        c.rect(x, y + wh - 3, ww, 3, LIT[2])
    else:
        c.rect(x, y, ww, wh, SKY_GLASS[1])
        c.rect(x, y, ww, wh // 3, SKY_GLASS[0])
        c.rect(x, y + wh - 3, ww, 3, SKY_GLASS[2])
        for i in range(min(ww, wh) // 3):
            c.px(x + 2 + i * 2, y + 2 + i * 2, RIM)
    if kind == "open":
        c.rect(x + ww // 2, y, ww // 2, wh, hexc("#2a3a5a"))   # uchylone skrzydło
    c.vline(x + ww // 2, y, wh, INK)
    c.hline(x, y + wh // 2 - 1, ww, INK)
    if sill:
        c.rect(x - 2, y + wh + 1, ww + 4, 2, hexc("#e4e8ee"))
        c.hline(x - 2, y + wh + 3, ww + 4, INK)
    if curtain:
        c.rect(x + 1, y + 1, 3, wh // 2 - 1, curtain)


def window_grid(c, x0, y0, x1, y1, ww, wh, gap_x, gap_y, seed, lit_ratio=0.15, curtains=False, open_ratio=0.1):
    rng = random.Random(seed)
    cols = max(1, (x1 - x0 + gap_x) // (ww + gap_x))
    used = cols * ww + (cols - 1) * gap_x
    start = x0 + (x1 - x0 - used) // 2
    y = y0
    while y + wh + 4 <= y1:
        for i in range(cols):
            r = rng.random()
            kind = "lit" if r < lit_ratio else "open" if r < lit_ratio + open_ratio else "glass"
            curtain = hexc("#e87aa0") if curtains and rng.random() < 0.3 else None
            window(c, start + i * (ww + gap_x), y, ww, wh, kind, curtain=curtain)
        y += wh + gap_y


def awning(c, x, y, w, depth=7, a=AWN_A, b=AWN_B):
    for i in range(w):
        col = a if (i // 6) % 2 == 0 else b
        c.rect(x + i, y, 1, depth, col)
        c.px(x + i, y + depth, col if (i % 6) not in (0, 5) else INK)
    c.hline(x, y - 1, w, INK)
    c.hline(x, y, w, hexc("#ffffff"))
    c.rect(x, y + depth + 1, w, 2, hexc("#00000040"))


def shopfront(c, x, y, w, h, kind="glass"):
    c.rect(x - 1, y - 1, w + 2, h + 2, INK)
    if kind == "shutter":
        c.rect(x, y, w, h, METAL[1])
        for i in range(0, h, 3):
            c.hline(x, y + i, w, METAL[0])
            c.hline(x, y + i + 1, w, METAL[2])
    else:
        c.rect(x, y, w, h, hexc("#3a4a64"))
        c.rect(x + 2, y + 2, w - 4, h - 4, hexc("#9ad4ee"))          # szyba z odbiciem nieba
        c.rect(x + 2, y + h // 2, w - 4, h // 2 - 2, hexc("#5aa0c8"))
        for i in range(0, w - 4, 4):
            c.px(x + 4 + i, y + 3 + (i // 4) % 3, RIM)


def door(c, x, y, w=16, h=30, glow=False):
    c.rect(x - 1, y - 1, w + 2, h + 1, INK)
    c.rect(x, y, w, h, hexc("#2a3450"))
    c.rect(x + 2, y + 3, w - 4, min(10, h - 6), hexc("#ffd84a") if glow else hexc("#6a86b0"))
    c.px(x + w - 4, y + h // 2 + 3, hexc("#f0e8b0"))


def draw_trelvos_market():
    """Sklep Trelvos 224 x 128: wielki szyld TRELVOS nad markizą, szerokie drzwi pośrodku (tu stoi bomba 1)."""
    w, h = 224, 128
    c = facade(w, h, CREAM, 111, cap=8, pattern="stucco")
    # Piętro: rząd okien nad szyldem.
    for x in range(14, w - 14, 34):
        window(c, x, 14, 18, 16, "lit" if x in (48, 150) else "glass", curtain=None)
    # Pas z szyldem.
    c.rect(3, 40, w - 6, 3, CREAM[2])
    trelvos_sign(c, 40, 46, 144, 24, 3)
    # Parter: dwie wystawy i drzwi środkiem, markiza w pasy.
    c.rect(3, 74, w - 6, h - 74, CREAM[1])
    shopfront(c, 10, 90, 78, 34)
    shopfront(c, 136, 90, 78, 34)
    door(c, 98, 88, 28, 40, glow=True)
    awning(c, 6, 78, 212, 8)
    for x in range(14, 80, 14):                     # towary na wystawie
        c.rect(x, 108, 8, 10, hexc("#e8663a"))
        c.rect(x + 1, 109, 6, 3, hexc("#ffd070"))
    for x in range(144, 206, 14):
        c.rect(x, 108, 8, 10, hexc("#5aa84a"))
        c.rect(x + 1, 109, 6, 3, hexc("#c8f0a0"))
    c.save("l2_trelvos_market.png")


def draw_trelvos_bank():
    """Bank Trelvos 256 x 160: kolumny, schody przed wejściem, szyld na fasadzie (bomba 2 stoi przy drzwiach)."""
    w, h = 256, 160
    c = facade(w, h, STONE, 121, cap=10, pattern="stucco")
    # Fronton z napisem.
    c.rect(24, 12, w - 48, 26, STONE[2])
    c.rect(24, 12, w - 48, 3, STONE[0])
    trelvos_sign(c, 52, 16, 152, 20, 3)
    # Okna na piętrze w arkadach.
    for x in range(20, w - 30, 40):
        window(c, x, 50, 22, 28, "glass")
        c.hline(x - 2, 46, 26, STONE[2])
    # Kolumny parteru.
    top = 88
    c.rect(3, top, w - 6, h - top, STONE[1])
    for x in range(12, w - 18, 56):
        c.rect(x, top, 12, h - top, STONE[0])
        c.rect(x, top, 3, h - top, STONE[2])
        c.rect(x + 10, top, 2, h - top, STONE[2])
        c.rect(x - 2, top, 16, 4, STONE[2])
        c.rect(x - 2, h - 8, 16, 8, STONE[2])
    # Wejście: szklane drzwi środkiem, nad nimi markiza i zegar.
    door(c, 112, 100, 32, 60, glow=False)
    c.rect(113, 102, 14, 56, hexc("#9ad4ee"))
    c.rect(129, 102, 14, 56, hexc("#7cbce0"))
    c.vline(128, 102, 56, INK)
    c.rect(108, 92, 40, 6, TRELVOS[1])
    c.hline(108, 92, 40, TRELVOS[0])
    c.hline(108, 97, 40, INK)
    c.rect(122, 80, 12, 10, INK)                    # zegar nad wejściem
    c.rect(123, 81, 10, 8, hexc("#fff7e0"))
    c.vline(128, 82, 4, INK)
    c.hline(128, 85, 3, INK)
    # Boczne okna bankowe z kratami.
    for x in (22, 188):
        c.rect(x - 1, 108, 46, 36, INK)
        c.rect(x, 109, 44, 34, hexc("#7cbce0"))
        for i in range(0, 44, 8):
            c.vline(x + i, 109, 34, INK)
    c.rect(0, h - 6, w, 6, STONE[2])                # cokół
    c.save("l2_trelvos_bank.png")


def draw_trelvos_tower():
    """Wieża Trelvos 192 x 160: szklana fasada z szyldem; prawa część to dach, na którym stoi neon (l2_trelvos_sign)."""
    w, h = 192, 160
    c = facade(w, h, SLATE, 131, cap=8, pattern="stucco")
    for y in range(16, 100, 24):                      # szklane pasy
        for x in range(10, w - 10, 22):
            window(c, x, y, 16, 16, "glass" if (x + y) % 3 else "lit", sill=False)
    trelvos_sign(c, 28, 110, 136, 22, 3)
    c.rect(3, 138, w - 6, h - 138, SLATE[2])
    shopfront(c, 10, 142, 50, 14)
    door(c, 80, 138, 32, 22, glow=True)
    shopfront(c, 132, 142, 50, 14)
    # Instalacje przy lewej ścianie (od strony szybu): rura i klimatyzatory.
    c.rect(6, 14, 4, h - 20, METAL[2])
    c.rect(6, 14, 1, h - 20, METAL[0])
    for y in (40, 84, 120):
        c.rect(5, y, 6, 4, METAL[1])
    c.save("l2_trelvos_tower.png")


def draw_trelvos_sign():
    """Neon na dachu wieży 128 x 48: słupki i tablica z napisem TRELVOS."""
    w, h = 128, 48
    c = Canvas(w, h)
    for x in (14, w - 18):
        c.rect(x, 28, 4, 20, METAL[2])
        c.rect(x, 28, 1, 20, METAL[0])
    trelvos_sign(c, 4, 4, 120, 26, 3)
    c.hline(4, 4, 120, TRELVOS[0])
    c.outline_alpha()
    c.save("l2_trelvos_sign.png")


def draw_flat():
    """Kamienica 224 x 160 z balkonami, cegła w ciepłym odcieniu."""
    w, h = 224, 160
    c = facade(w, h, BRICK, 141)
    window_grid(c, 12, 16, w - 12, 112, 14, 18, 24, 12, 151, lit_ratio=0.1, curtains=True)
    for by in (44, 74):
        for bx in range(16, w - 28, 38):
            c.rect(bx - 2, by + 22, 32, 3, hexc("#e4e8ee"))
            c.hline(bx - 2, by + 25, 32, INK)
            for i in range(0, 30, 4):
                c.vline(bx + i, by + 12, 10, hexc("#33405c"))
            c.hline(bx - 1, by + 11, 30, hexc("#6a7a98"))
    c.rect(3, 128, w - 6, h - 128, BRICK[2])
    for i in range(14, w - 30, 46):
        door(c, i, 130, 16, 30, glow=(i // 46) % 2 == 0)
    c.save("l2_flat.png")


def draw_cafe():
    """Kawiarnia 192 x 128: markiza, okno z kawą, tablica z menu."""
    w, h = 192, 128
    c = facade(w, h, CREAM, 161, cap=8, pattern="stucco")
    window_grid(c, 10, 16, w - 10, 62, 16, 16, 18, 8, 171, lit_ratio=0.15, curtains=True)
    c.rect(3, 68, w - 6, h - 68, CREAM[1])
    shopfront(c, 12, 88, 90, 36)
    door(c, 112, 86, 26, 42, glow=True)
    awning(c, 6, 76, 140, 8, a=hexc("#d8503a"), b=AWN_B)
    c.rect(150, 84, 34, 40, INK)                    # tablica z menu
    c.rect(151, 85, 32, 38, hexc("#2c4a3c"))
    for y in range(90, 118, 6):
        c.hline(155, y, 22, hexc("#f4f0e0"))
    for x in range(20, 94, 18):                     # stoliki i filiżanki widoczne przez szybę
        c.rect(x, 108, 12, 3, hexc("#8a5a2a"))
        c.rect(x + 4, 102, 4, 6, hexc("#fff7e0"))
    c.save("l2_cafe.png")


def draw_gate():
    """Budynek z bramą 224 x 288: dół to przejście (wysokie na 64 px), nad nim kilka pięter. Prawa ściana szybu."""
    w, h = 224, 288
    open_h = 64
    c = facade(w, h, BRICK, 181)
    window_grid(c, 12, 16, w - 12, h - open_h - 10, 14, 18, 22, 14, 191, lit_ratio=0.12, curtains=True)
    top = h - open_h
    c.rect(0, top - 6, w, 6, BRICK[2])
    c.hline(0, top - 6, w, hexc("#e4e8ee"))
    c.rect(0, top, w, open_h, hexc("#27304a"))
    for x in range(0, w, 3):
        c.vline(x, top + 16 + (x % 5), open_h - 16 - (x % 5), hexc("#323c5a"))
    c.rect(w // 2 - 22, top + 12, 44, open_h - 12, hexc("#7a9ac0"))      # dzień po drugiej stronie przejścia
    c.rect(w // 2 - 14, top + 20, 28, open_h - 20, hexc("#d6efff"))
    for x in (4, 62, 124, 186):
        c.rect(x, top, 10, open_h, BRICK[1])
        c.rect(x, top, 3, open_h, BRICK[2])
        c.rect(x + 8, top, 2, open_h, BRICK[0])
        c.rect(x - 1, top, 12, 4, hexc("#e4e8ee"))
    c.save("l2_gate.png")


def draw_warehouse():
    """Magazyn 256 x 160: blacha falista, bramy rolowane, pasy ostrzegawcze."""
    w, h = 256, 160
    c = facade(w, h, STEEL, 201, cap=8, pattern="stucco")
    for x in range(6, w - 4, 6):                    # blacha falista
        c.vline(x, 10, h - 10, STEEL[0])
        c.vline(x + 1, 10, h - 10, STEEL[2])
    window_grid(c, 14, 20, w - 14, 56, 20, 12, 22, 8, 211, lit_ratio=0.0, open_ratio=0.0)
    c.rect(3, 80, w - 6, h - 80, STEEL[1])
    for x in (14, 98, 182):
        shopfront(c, x, 94, 60, 62, "shutter")
        c.rect(x - 1, 84, 62, 6, INK)
        for i in range(0, 60, 12):                  # pasy ostrzegawcze nad bramą
            c.rect(x + i, 85, 6, 4, hexc("#f0c020"))
    c.save("l2_warehouse.png")


def draw_depot():
    """Zajezdnia przy wyjściu 224 x 128: duża brama garażowa, zielony pas, tło dla drzwi wyjścia."""
    w, h = 224, 128
    c = facade(w, h, STONE, 221, cap=8, pattern="stucco")
    window_grid(c, 12, 16, w - 12, 50, 16, 14, 20, 8, 231, lit_ratio=0.2)
    c.rect(3, 62, w - 6, h - 62, STONE[1])
    c.rect(8, 54, 130, 10, AWN_A)
    c.hline(8, 54, 130, hexc("#6ad4aa"))
    shopfront(c, 12, 74, 112, 50, "shutter")
    c.rect(11, 66, 114, 6, INK)
    for i in range(0, 112, 14):
        c.rect(12 + i, 67, 7, 4, hexc("#f0c020"))
    c.save("l2_depot.png")


# ---------------------------------------------------------------------------
#  REKWIZYTY
# ---------------------------------------------------------------------------

def draw_scaffold():
    """Rusztowanie przy ścianie 64 x 176: słupki, trzy pomosty (y = 128, 80, 32 od góry) i poprzeczki. Pomosty to platformy
    jednokierunkowe w poziomie (make level 2.py)."""
    w, h = 64, 176
    c = Canvas(w, h)
    pole, deck, dark = METAL[1], WOOD, METAL[2]
    for x in (4, 56):
        c.rect(x, 0, 4, h, pole)
        c.rect(x, 0, 1, h, METAL[0])
    for y in (32, 80, 128):
        for x in range(0, w, 8):
            c.rect(x, y, 8, 4, deck[0] if (x // 8) % 2 == 0 else deck[1])
            c.vline(x, y, 4, deck[2])
        c.hline(0, y + 4, w, deck[2])
        c.hline(4, y - 16, 56, pole)
        c.hline(4, y - 8, 56, pole)
    for y0 in (36, 84):                               # przekątne usztywnienia
        for i in range(44):
            c.px(8 + i, y0 + i, dark)
    c.rect(2, h - 6, 60, 6, METAL[2])                 # stopy
    c.outline_alpha()
    c.save("l2_scaffold.png")


def draw_crane():
    """Żuraw 176 x 368: maszt kratownicowy, wysięgnik z przeciwwagą i hak na linie. Hak (punkt zaczepienia) jest w (28, 54)."""
    w, h = 176, 368
    c = Canvas(w, h)
    yellow, ydark = TRELVOS[1], TRELVOS[2]
    mx = 100                                           # maszt: x 100..132
    c.rect(mx, 28, 32, h - 28, yellow)
    c.rect(mx, 28, 4, h - 28, TRELVOS[0])
    c.rect(mx + 28, 28, 4, h - 28, ydark)
    for y in range(36, h - 24, 16):                    # kratownica
        for i in range(16):
            c.px(mx + 4 + i * 24 // 16, y + i, ydark)
            c.px(mx + 28 - i * 24 // 16, y + 16 + i - 16 + 0, ydark) if False else None
        c.hline(mx, y, 32, ydark)
    c.rect(mx - 8, h - 24, 48, 24, METAL[1])            # fundament
    c.rect(mx - 8, h - 24, 48, 3, METAL[0])
    # Wysięgnik: poziomy dźwigar od x=16 do 172, kabina i przeciwwaga.
    c.rect(16, 8, 156, 12, yellow)
    c.rect(16, 8, 156, 3, TRELVOS[0])
    c.rect(16, 17, 156, 3, ydark)
    for x in range(16, 120, 12):
        for i in range(12):
            c.px(x + i, 11 + i * 6 // 12, ydark)
    c.rect(mx + 6, 0, 20, 12, yellow)                   # wieżyczka
    c.rect(mx + 10, 2, 12, 6, hexc("#9ad4ee"))
    c.rect(148, 20, 24, 20, METAL[2])                   # przeciwwaga
    c.rect(148, 20, 24, 3, METAL[0])
    c.vline(mx + 16, 0, 2, METAL[2])
    # Lina i hak.
    c.vline(28, 20, 28, INK)
    c.vline(29, 20, 28, METAL[1])
    c.rect(22, 48, 14, 10, METAL[1])
    c.outline_box(22, 48, 14, 10, INK)
    c.rect(26, 52, 6, 4, INK)
    c.rect(27, 53, 4, 2, hexc("#00000000"))
    c.outline_alpha()
    c.save("l2_crane.png")


def draw_planter():
    """Donica z krzewem 64 x 32 (przeszkoda do przeskoczenia)."""
    w, h = 64, 32
    c = Canvas(w, h)
    c.rect(2, 14, w - 4, 18, STONE[1])
    c.rect(2, 14, w - 4, 3, STONE[0])
    c.rect(2, 28, w - 4, 4, STONE[2])
    for x in range(8, w - 6, 12):
        c.vline(x, 18, 10, STONE[2])
    for i in range(0, w - 8, 6):                     # krzew
        r = 6 + (i * 7) % 5
        c.rect(4 + i, 14 - r, 10, r, LEAF[1])
        c.rect(4 + i, 14 - r, 10, 3, LEAF[0])
        c.rect(4 + i + 6, 14 - r + 3, 4, r - 3, LEAF[2])
    c.outline_alpha()
    c.hline(0, 0, w, INK) if False else None
    c.save("l2_planter.png")


def draw_kiosk():
    """Kiosk z gazetami 64 x 56: zielone ściany, okienko, daszek."""
    w, h = 64, 56
    c = Canvas(w, h)
    light, base, dark = GREEN
    c.rect(2, 10, w - 4, h - 10, base)
    c.rect(2, 10, 4, h - 10, dark)
    c.rect(w - 6, 10, 4, h - 10, light)
    c.rect(0, 2, w, 10, hexc("#d8503a"))              # daszek
    c.rect(0, 2, w, 3, hexc("#ff8a6a"))
    for x in range(0, w, 8):
        c.rect(x, 9, 4, 4, AWN_B)
    c.rect(10, 20, 44, 20, INK)                       # okienko
    c.rect(11, 21, 42, 18, hexc("#9ad4ee"))
    for x in range(14, 50, 9):                        # gazety
        c.rect(x, 28, 7, 10, hexc("#f4f0e0"))
        c.rect(x + 1, 30, 5, 2, hexc("#d8503a"))
    c.rect(8, 40, 48, 4, METAL[0])                    # lada
    c.rect(6, h - 6, w - 12, 6, dark)
    c.outline_alpha()
    c.save("l2_kiosk.png")


def draw_van():
    """Furgonetka dostawcza 128 x 56 (cała bryła jest solidna): korpus, kabina, koła, logo."""
    w, h = 128, 56
    c = Canvas(w, h)
    body, bl, bd = hexc("#e8eef6"), hexc("#ffffff"), hexc("#a8b4c8")
    c.rect(2, 4, 88, 40, body)                        # skrzynia
    c.rect(2, 4, 88, 3, bl)
    c.rect(2, 38, 88, 6, bd)
    c.rect(90, 14, 34, 30, body)                      # kabina
    c.rect(90, 14, 34, 3, bl)
    for i in range(10):                               # skos szyby
        c.rect(104 + i, 16 + i, 18 - i, 1, hexc("#7cbce0"))
    c.rect(94, 18, 12, 12, hexc("#7cbce0"))
    c.rect(94, 18, 12, 3, hexc("#c4ecfa"))
    c.vline(89, 6, 38, bd)
    c.rect(8, 14, 74, 16, TRELVOS[1])                 # pas z logo Trelvos
    c.rect(8, 14, 74, 2, TRELVOS[0])
    draw_text(c, 12, 18, "TRELVOS", 1, TRELVOS_DARK)
    c.rect(122, 34, 4, 5, hexc("#ff4a3a"))
    c.rect(0, 40, w, 6, bd)
    for cx in (24, 104):
        c.rect(cx - 10, 36, 20, 20, INK)
        c.rect(cx - 7, 39, 14, 15, hexc("#2a2a34"))
        c.rect(cx - 3, 43, 6, 6, METAL[0])
        c.rect(cx - 1, 45, 2, 2, METAL[2])
    c.outline_alpha()
    c.save("l2_van.png")


def draw_container():
    """Kontener 96 x 64 (solidny): blacha falista, drzwi z zasuwami."""
    w, h = 96, 64
    c = Canvas(w, h)
    col = hexc("#3f8fbf"), hexc("#2c6f9c"), hexc("#1e4c70")
    c.rect(0, 0, w, h, col[1])
    for x in range(3, w - 3, 4):
        c.vline(x, 5, h - 8, col[0])
        c.vline(x + 1, 5, h - 8, col[2])
    c.rect(0, 0, w, 5, col[0])
    c.rect(0, h - 4, w, 4, col[2])
    c.rect(w - 14, 5, 10, h - 8, col[2])              # drzwi
    for x in (w - 12, w - 8):
        c.vline(x, 8, h - 14, METAL[0])
    c.rect(8, 22, 30, 12, hexc("#f4f0e0"))             # napis
    draw_text(c, 11, 25, "TRELVOS", 1, TRELVOS_DARK) if False else c.rect(11, 25, 24, 2, hexc("#c04030"))
    c.rect(11, 29, 16, 2, hexc("#c04030"))
    c.outline_box(0, 0, w, h, INK)
    c.save("l2_container.png")


def draw_tree():
    """Drzewo uliczne 64 x 128: pień i korona (dekoracja)."""
    w, h = 64, 128
    c = Canvas(w, h)
    c.rect(28, 56, 8, 72, WOOD[2])
    c.rect(28, 56, 3, 72, WOOD[1])
    c.rect(24, 120, 16, 8, STONE[2])
    for (cx, cy, r) in ((32, 30, 24), (16, 42, 14), (48, 42, 14), (32, 54, 14)):
        for y in range(cy - r, cy + r + 1):
            span = int((r * r - (y - cy) ** 2) ** 0.5)
            for x in range(cx - span, cx + span + 1):
                shade = LEAF[0] if (x - cx) + (y - cy) < -r // 2 else LEAF[2] if (x - cx) + (y - cy) > r // 2 else LEAF[1]
                c.px(x, y, shade)
    c.outline_alpha()
    c.save("l2_tree.png")


def draw_bench():
    """Ławka 64 x 32 (dekoracja)."""
    w, h = 64, 32
    c = Canvas(w, h)
    for y in (6, 11, 16):
        c.rect(4, y, 56, 4, WOOD[1])
        c.rect(4, y, 56, 1, WOOD[0])
    c.rect(4, 22, 56, 4, WOOD[1])
    c.rect(4, 22, 56, 1, WOOD[0])
    for x in (8, 52):
        c.rect(x, 4, 4, 28, METAL[2])
        c.rect(x, 26, 4, 6, METAL[1])
    c.outline_alpha()
    c.save("l2_bench.png")


def draw_hydrant():
    """Hydrant 16 x 32 (dekoracja)."""
    w, h = 16, 32
    c = Canvas(w, h)
    red, rl, rd = hexc("#d8402a"), hexc("#ff7a5a"), hexc("#8a2418")
    c.rect(4, 6, 8, 24, red)
    c.rect(4, 6, 2, 24, rl)
    c.rect(10, 6, 2, 24, rd)
    c.rect(2, 2, 12, 6, red)
    c.rect(2, 2, 12, 2, rl)
    c.rect(6, 0, 4, 3, METAL[1])
    c.rect(0, 14, 16, 5, red)
    c.rect(0, 14, 16, 1, rl)
    c.rect(2, 28, 12, 4, rd)
    c.outline_alpha()
    c.save("l2_hydrant.png")


def draw_busstop():
    """Przystanek 96 x 96 (dekoracja): szklana wiata, słupek, ławka."""
    w, h = 96, 96
    c = Canvas(w, h)
    c.rect(6, 10, 84, 6, hexc("#2c6f9c"))             # dach wiaty
    c.rect(6, 10, 84, 2, hexc("#7cbce0"))
    for x in (8, 86):
        c.rect(x, 16, 3, 80, METAL[2])
    c.rect(12, 18, 72, 58, hexc("#9ad4ee80"))        # szyba
    for i in range(0, 60, 6):
        c.px(18 + i, 22 + i // 2, RIM)
    c.rect(20, 66, 56, 4, WOOD[1])                    # ławka
    c.rect(20, 66, 56, 1, WOOD[0])
    c.rect(24, 70, 3, 10, METAL[2])
    c.rect(69, 70, 3, 10, METAL[2])
    c.rect(32, 28, 32, 22, INK)                        # rozkład jazdy
    c.rect(33, 29, 30, 20, hexc("#f4f0e0"))
    for y in range(32, 46, 4):
        c.hline(36, y, 24, hexc("#33405c"))
    c.rect(2, 4, 20, 8, INK)                           # tabliczka "BUS"
    c.rect(3, 5, 18, 6, hexc("#2c6f9c"))
    draw_text(c, 5, 6, "BUS", 1, RIM) if False else None
    c.outline_alpha()
    c.save("l2_busstop.png")


def draw_lamp():
    """Latarnia uliczna 32 x 128 (dekoracja): słup z wysięgnikiem i zgaszoną lampą."""
    w, h = 32, 128
    c = Canvas(w, h)
    c.rect(14, 8, 4, 120, METAL[1])
    c.rect(14, 8, 1, 120, METAL[0])
    c.rect(10, 120, 12, 8, METAL[2])
    c.rect(14, 4, 14, 3, METAL[1])
    c.rect(24, 4, 8, 6, METAL[2])
    c.rect(25, 9, 6, 2, hexc("#e8eef6"))
    c.outline_alpha()
    c.save("l2_lamp.png")


def draw_mailbox():
    """Skrzynka pocztowa 24 x 40 (dekoracja)."""
    w, h = 24, 40
    c = Canvas(w, h)
    c.rect(10, 22, 4, 18, METAL[2])
    c.rect(2, 2, 20, 22, hexc("#3a62c8"))
    c.rect(2, 2, 20, 4, hexc("#7a9af0"))
    c.rect(2, 18, 20, 6, hexc("#26408a"))
    c.rect(6, 10, 12, 2, INK)
    c.rect(6, 14, 8, 2, hexc("#f4f0e0"))
    c.outline_alpha()
    c.save("l2_mailbox.png")


def draw_cones():
    """Dwa pachołki 40 x 24 (dekoracja)."""
    w, h = 40, 24
    c = Canvas(w, h)
    for x0 in (2, 22):
        c.rect(x0, 20, 16, 4, METAL[2])
        for row in range(18):
            half = 2 + row * 6 // 18
            c.rect(x0 + 8 - half, 2 + row, half * 2, 1, hexc("#ff8a1f"))
        c.rect(x0 + 4, 10, 8, 3, hexc("#f4f0e0"))
        c.rect(x0 + 3, 16, 10, 3, hexc("#f4f0e0"))
    c.outline_alpha()
    c.save("l2_cones.png")


if __name__ == "__main__":
    draw_city()
    draw_pavement()
    draw_trelvos_market()
    draw_trelvos_bank()
    draw_trelvos_tower()
    draw_trelvos_sign()
    draw_flat()
    draw_cafe()
    draw_gate()
    draw_warehouse()
    draw_depot()
    draw_scaffold()
    draw_crane()
    draw_planter()
    draw_kiosk()
    draw_van()
    draw_container()
    draw_tree()
    draw_bench()
    draw_hydrant()
    draw_busstop()
    draw_lamp()
    draw_mailbox()
    draw_cones()
