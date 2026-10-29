"""Rysuje grafiki poziomu 1 (miasto o zachodzie): tło, chodnik, budynki, rekwizyty, drzwi wyjścia, kolce i skocznię.

Uruchom z głównego katalogu repozytorium:   python tools/make_level1_art.py
(wymaga bibliotek Pillow i numpy:  pip install pillow numpy)

Powstają pliki w assets/ (nazwy zaczynają się od "l1_", żeby nie mieszały się z resztą):
  l1_city.png          panorama miasta 1280 x 480 (zapętla się poziomo bez szwu), tło z paralaksą w poziomie i w pionie.
                       Powstaje z assets/wschód.png: bierzemy samo miasto i niebo (chodnik wycinamy), dorabiamy niebo
                       nad miastem, drugą połowę (odbicie lustrzane bez słońca i z innymi oknami) i podstawę ulicy.
  l1_sidewalk.png      kafelek chodnika 40 x 40 (podłoże, tekstura "ground"); rysunek z chodnika z wschód.png.
  l1_shop.png, l1_block.png, l1_office.png, l1_arch.png, l1_tower.png, l1_garage.png
                       budynki (rozmiar pliku = rozmiar budynku w poziomie, 1 piksel obrazka = 1 piksel gry).
  l1_crate.png, l1_dumpster.png, l1_car.png, l1_fire_escape.png     rekwizyty
  l1_exit_door.png, l1_exit_door_open.png                            drzwi wyjścia (56 x 96)
  spike.png, jump_pad.png                                            kafelki 32 x 8: kolce i skocznia (dla wszystkich poziomów)

Styl jak reszta gry: czarny kontur 1 px na rekwizytach, trzy tony cieniowania, kolory z zachodu słońca
(pomarańcz tła, żółć oświetlonych okien jak w wschód.png i na lampie).
Chcesz zmienić wygląd? Kolory są w słownikach na górze, kształty w funkcjach draw_*.
"""

import random
from pathlib import Path

import numpy as np
from PIL import Image

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def hexc(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


INK = hexc("#140e18")
# Fasady: jasny (rant), bazowy, ciemny (cień / lewy brzeg)
BRICK = (hexc("#6a4358"), hexc("#503348"), hexc("#3a2438"))       # cegła w odcieniu śliwki
CONCRETE = (hexc("#5a6178"), hexc("#444a60"), hexc("#31364a"))    # beton w chłodnym granacie
SAND = (hexc("#8a6a5a"), hexc("#6c4f4a"), hexc("#4c3540"))         # tynk w kolorze piasku
STEELB = (hexc("#50667a"), hexc("#3b4d60"), hexc("#2a3848"))      # blacha (garaż)
RIM = hexc("#ff9a3d")          # światło zachodu na krawędziach dachów
RIM_DARK = hexc("#c4601a")
GLASS = (hexc("#3a3050"), hexc("#241a38"), hexc("#17102a"))        # zgaszona szyba
GLASS_SHINE = hexc("#5a4c78")
LIT = (hexc("#fff3a0"), hexc("#ffc20e"), hexc("#d98a06"))          # oświetlone okno
WOOD = (hexc("#d38c42"), hexc("#a8672a"), hexc("#74431c"))
METAL = (hexc("#8a8a96"), hexc("#5e5e6c"), hexc("#3a3a46"))
GREEN = (hexc("#5ca070"), hexc("#3c7a52"), hexc("#285238"))
TEAL = (hexc("#4ca8b4"), hexc("#2f7d8c"), hexc("#1f5262"))
AWN_A = hexc("#e0661c")
AWN_B = hexc("#f6e2b0")


class Canvas:
    """Płótno RGBA z prymitywami rysującymi pełne, ostre piksele."""

    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), dtype=np.uint8)
        if fill is not None:
            self.rect(0, 0, w, h, fill)

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = (*c[:3], c[3] if len(c) > 3 else 255)

    def get(self, x, y):
        return tuple(int(v) for v in self.a[y, x])

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 > x0 and y1 > y0:
            self.a[y0:y1, x0:x1] = (*c[:3], c[3] if len(c) > 3 else 255)

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def outline_box(self, x, y, w, h, c):
        self.hline(x, y, w, c)
        self.hline(x, y + h - 1, w, c)
        self.vline(x, y, h, c)
        self.vline(x + w - 1, y, h, c)

    def paste(self, other, x, y):
        img = Image.fromarray(self.a)
        img.alpha_composite(Image.fromarray(other.a), (x, y))
        self.a = np.array(img)

    def outline_alpha(self, c=INK):
        """Czarny kontur 1 px wokół wszystkich nieprzezroczystych pikseli (poza krawędziami obrazka)."""
        alpha = self.a[:, :, 3] > 0
        grown = np.zeros_like(alpha)
        grown[1:, :] |= alpha[:-1, :]
        grown[:-1, :] |= alpha[1:, :]
        grown[:, 1:] |= alpha[:, :-1]
        grown[:, :-1] |= alpha[:, 1:]
        edge = grown & ~alpha
        self.a[edge] = (*c[:3], 255)

    def save(self, name):
        Image.fromarray(self.a, "RGBA").save(ASSETS / name)
        print(f"{name}: {self.w}x{self.h}")


# ---------------------------------------------------------------------------
#  TŁO I CHODNIK (z wschód.png)
# ---------------------------------------------------------------------------

SKY_TOP_ROWS = 120      # ile pikseli nieba dorabiamy nad miastem (pionowa paralaksa)
CITY_ROWS = 305         # wiersze 0..304 w wschód.png to niebo i miasto; od 305 zaczyna się chodnik
BG_W, BG_H = 1280, 480


def load_source():
    return np.array(Image.open(ASSETS / "wschód.png").convert("RGB"))


def components(mask):
    """Spójne obszary maski (4-sąsiedztwo), bez scipy: lista list pikseli."""
    h, w = mask.shape
    seen = np.zeros_like(mask)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                stack = [(y, x)]
                seen[y, x] = True
                comp = []
                while stack:
                    cy, cx = stack.pop()
                    comp.append((cy, cx))
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
                out.append(comp)
    return out


def draw_city():
    src = load_source()
    rng = random.Random(7)
    city = src[:CITY_ROWS].copy()                      # miasto i niebo, bez chodnika

    # Druga połowa panoramy: lustrzane odbicie. Odbicie sklejone z oryginałem nie ma szwu (ani na środku, ani na zawinięciu).
    mirror = city[:, ::-1].copy()

    # Słońce zastępujemy niebem, żeby w panoramie nie było dwóch słońc. Słońce to jasnożółte piksele
    # (R >= 240, G >= 125, B >= 18, razem z jasnym obrysem) w prostokącie wokół niego; oświetlone okna mają B = 14, więc zostają.
    sun_box = (130, 215, 639 - 395, 639 - 290)        # wiersze od-do i kolumny od-do w odbiciu
    region = mirror[sun_box[0]:sun_box[1], sun_box[2]:sun_box[3]]
    r, g, b = region[:, :, 0], region[:, :, 1], region[:, :, 2]
    window = (r == 255) & (g == 194) & (b == 14)
    sun = ((r >= 238) & (g >= 122) & (b >= 18) & ~window) | ((r == 255) & (g >= 205) & (b < 18))
    region[sun] = (235, 108, 23)
    # Okruchy poświaty (jasne piksele nieba pod słońcem) zostają: wyglądają jak mgła nad miastem.

    # Część okien gasimy, żeby odbicie nie było kopią: oświetlone okna (żółte skupiska) wyłączamy losowo.
    lit = (mirror[:, :, 0] == 255) & (mirror[:, :, 1] == 194) & (mirror[:, :, 2] == 14)
    for comp in components(lit):
        if rng.random() < 0.3:
            ys = [p[0] for p in comp]
            xs = [p[1] for p in comp]
            body = mirror[min(ys) - 2, min(xs)] if min(ys) >= 2 else mirror[max(ys) + 2, min(xs)]
            for cy, cx in comp:
                mirror[cy, cx] = body

    panorama = np.concatenate([city, mirror], axis=1)          # 1280 x 305

    # Podstawa ulicy pod miastem: ciemny pas z oryginału ciągnie się dalej w dół.
    base_rows = BG_H - SKY_TOP_ROWS - CITY_ROWS                # 55
    base = np.zeros((base_rows, BG_W, 3), dtype=np.uint8)
    for i in range(base_rows):
        shade = hexc("#4d2303") if i < 20 else hexc("#3f1c03") if i < 40 else hexc("#321602")
        base[i, :] = shade
    # Delikatne pionowe fugi muru, co 40 px (jak szczeliny chodnika), żeby pas nie był pustym kolorem.
    for x in range(0, BG_W, 40):
        base[:, x] = (np.array(base[:, x]) * 0.88).astype(np.uint8)

    # Niebo nad miastem: ciągnie kolor górnego wiersza (f7842d) i pomału przechodzi w koral, z "rastrem" 2x2
    # między pasami, plus kilka smug chmur w kolorach ze zdjęcia.
    top = np.zeros((SKY_TOP_ROWS, BG_W, 3), dtype=np.uint8)
    bands = [hexc("#f7842d"), hexc("#f67a34"), hexc("#f3703c"), hexc("#ee6644"), hexc("#e85c4c")]
    for y in range(SKY_TOP_ROWS):
        t = (SKY_TOP_ROWS - 1 - y) / (SKY_TOP_ROWS - 1) * (len(bands) - 1)    # 0 przy mieście, wyżej więcej korala
        lo = int(t)
        frac = t - lo
        hi = min(len(bands) - 1, lo + 1)
        for x in range(BG_W):
            dither = ((x // 2 + y // 2) % 2) * 0.5 + 0.25                      # raster 2 x 2
            top[y, x] = bands[hi] if frac > dither else bands[lo]
    # Chmury: poziome smugi z pikselowych elips, jaśniejsze od nieba, z ciemniejszym spodem.
    cloud_light = hexc("#f99f45")
    cloud_pale = hexc("#fbb557")
    cloud_dark = hexc("#e0652f")
    for _ in range(9):
        cx = rng.randrange(0, BG_W)
        cy = rng.randrange(14, SKY_TOP_ROWS - 14)
        cw = rng.randrange(60, 150)
        ch = rng.randrange(3, 6)
        for dy in range(-ch, ch + 1):
            span = int(cw * (1 - (dy / (ch + 0.5)) ** 2) ** 0.5)
            for dx in range(-span, span + 1):
                x = (cx + dx) % BG_W
                y = cy + dy
                if 0 <= y < SKY_TOP_ROWS:
                    top[y, x] = cloud_dark if dy > ch - 2 else (cloud_pale if dy < -ch + 2 else cloud_light)

    full = np.concatenate([top, panorama, base], axis=0)
    assert full.shape == (BG_H, BG_W, 3), full.shape
    # Pas z oryginału tuż nad chodnikiem (rząd 304) łączy się z podstawą bez szwu (ten sam kolor 4d2303).
    img = Image.fromarray(full, "RGB")
    img.save(ASSETS / "l1_city.png")
    print(f"l1_city.png: {BG_W}x{BG_H}")


def draw_sidewalk():
    """Chodnik 40 x 40: płyty z cienkimi łukowatymi fugami i krawężnik, jak w wschód.png."""
    src = load_source()
    c = Canvas(40, 40)
    slab_a, slab_b = hexc("#ef6c00"), hexc("#ff6d00")
    joint = hexc("#bd520b")
    for y in range(29):
        c.hline(0, y, 40, slab_a if y < 18 else slab_b)
    c.hline(0, 0, 40, hexc("#ff8a1f"))          # jasny brzeg góry płyty
    # Fuga: kształt skopiowany z pierwszej fugi oryginału (wiersze 306..332 wzdłuż łuku).
    for y in range(306, 333):
        base = tuple(src[y, 0])
        xs = [x for x in range(26, 44) if tuple(src[y, x]) != base]
        for x in xs:
            c.px(x - 20, y - 305, joint)
    # Krawężnik: jaśniejsza krawędź, ciemniejszy dół.
    for y in range(29, 40):
        c.hline(0, y, 40, hexc("#bd520b"))
    c.hline(0, 29, 40, hexc("#e0762a"))
    c.hline(0, 30, 40, hexc("#a8460a"))
    for y in range(36, 40):
        c.hline(0, y, 40, hexc("#833907"))
    # Drobne ubytki w płytach (kilka ciemniejszych pikseli).
    rng = random.Random(3)
    for _ in range(7):
        c.px(rng.randrange(40), rng.randrange(3, 27), hexc("#d65f00"))
    c.save("l1_sidewalk.png")


# ---------------------------------------------------------------------------
#  BUDYNKI
# ---------------------------------------------------------------------------

def facade(w, h, pal, seed, cap=7, pattern="brick"):
    """Gładka ściana z fakturą i dachem z attyką. Okna i parter dorysowują osobne funkcje."""
    light, base, dark = pal
    rng = random.Random(seed)
    c = Canvas(w, h, base)
    # Faktura: cegła (poziome fugi + przesunięte przerwy) albo tynk (plamki).
    if pattern == "brick":
        for y in range(cap + 3, h, 4):
            c.hline(0, y, w, dark)
            off = 0 if (y // 4) % 2 == 0 else 5
            for x in range(off, w, 10):
                c.px(x, y + 1, dark)
                c.px(x, y + 2, dark)
        for _ in range(w * h // 90):
            x, y = rng.randrange(w), rng.randrange(cap + 2, h)
            c.px(x, y, light if rng.random() < 0.5 else dark)
    else:
        for _ in range(w * h // 35):
            x, y = rng.randrange(w), rng.randrange(cap + 2, h)
            c.px(x, y, light if rng.random() < 0.4 else dark)
    # Boki: lewy w cieniu, prawy w świetle zachodu.
    c.rect(0, cap, 3, h - cap, dark)
    c.rect(w - 3, cap, 3, h - cap, light)
    c.vline(w - 1, cap, h - cap, RIM_DARK)
    # Dach: gzyms i attyka. Górna krawędź to powierzchnia, po której chodzi gracz.
    c.rect(0, 0, w, cap, light)
    c.rect(0, cap - 2, w, 2, dark)
    c.hline(0, 0, w, RIM)
    c.hline(0, 1, w, RIM_DARK)
    for x in range(6, w - 6, 24):          # słupki attyki
        c.rect(x, 2, 3, cap - 4, base)
    return c


def window(c, x, y, ww, wh, lit, sill=True, curtain=None):
    c.rect(x - 1, y - 1, ww + 2, wh + 2, INK)
    if lit:
        c.rect(x, y, ww, wh, LIT[1])
        c.rect(x + 1, y + 1, ww - 2, wh // 2 - 1, LIT[0])
        c.rect(x, y + wh - 3, ww, 3, LIT[2])
    else:
        c.rect(x, y, ww, wh, GLASS[1])
        c.rect(x, y + wh - 3, ww, 3, GLASS[2])
        for i in range(min(ww, wh) // 3):               # odblask po przekątnej
            c.px(x + 2 + i * 2, y + 2 + i * 2, GLASS_SHINE)
    c.vline(x + ww // 2, y, wh, INK)                    # słupek okna
    c.hline(x, y + wh // 2 - 1, ww, INK)                # poprzeczka
    if sill:
        c.rect(x - 2, y + wh + 1, ww + 4, 2, hexc("#8a7a86"))
        c.hline(x - 2, y + wh + 3, ww + 4, INK)
    if curtain:
        c.rect(x + 1, y + 1, 3, wh // 2 - 1, curtain)


def window_grid(c, x0, y0, x1, y1, ww, wh, gap_x, gap_y, seed, lit_ratio=0.35, curtains=False):
    rng = random.Random(seed)
    cols = max(1, (x1 - x0 + gap_x) // (ww + gap_x))
    used = cols * ww + (cols - 1) * gap_x
    start = x0 + (x1 - x0 - used) // 2
    y = y0
    while y + wh + 4 <= y1:
        for i in range(cols):
            lit = rng.random() < lit_ratio
            curtain = hexc("#d46a8a") if curtains and rng.random() < 0.3 else None
            window(c, start + i * (ww + gap_x), y, ww, wh, lit, curtain=curtain)
        y += wh + gap_y


def awning(c, x, y, w, depth=7):
    """Markiza w pasy pomarańczowo-kremowe z falbanką."""
    for i in range(w):
        col = AWN_A if (i // 6) % 2 == 0 else AWN_B
        c.rect(x + i, y, 1, depth, col)
        c.px(x + i, y + depth, col if (i % 6) not in (0, 5) else INK)
    c.hline(x, y - 1, w, INK)
    c.hline(x, y, w, hexc("#ffb060"))
    c.rect(x, y + depth + 1, w, 2, hexc("#00000040"))


def shopfront(c, x, y, w, h, kind="glass"):
    c.rect(x - 1, y - 1, w + 2, h + 2, INK)
    if kind == "shutter":
        c.rect(x, y, w, h, METAL[1])
        for i in range(0, h, 3):
            c.hline(x, y + i, w, METAL[0])
            c.hline(x, y + i + 1, w, METAL[2])
    else:
        c.rect(x, y, w, h, hexc("#4a3a30"))
        c.rect(x + 2, y + 2, w - 4, h - 4, hexc("#ffb347"))          # światło wnętrza
        c.rect(x + 2, y + h // 2, w - 4, h // 2 - 2, hexc("#e08a2a"))
        for i in range(x + 6, x + w - 4, 14):                         # półki
            c.rect(i, y + 6, 8, h - 12, hexc("#8a5a2a"))
            c.rect(i + 1, y + 8, 6, 3, hexc("#e0663a"))
        for i in range(0, w - 4, 4):                                  # odblask szyby
            c.px(x + 4 + i, y + 3 + (i // 4) % 3, hexc("#fff0c0"))


def door(c, x, y, w=16, h=30, glow=False):
    c.rect(x - 1, y - 1, w + 2, h + 1, INK)
    c.rect(x, y, w, h, hexc("#2a2230"))
    c.rect(x + 2, y + 3, w - 4, 10, hexc("#ffc20e") if glow else hexc("#463a56"))
    c.px(x + w - 4, y + h // 2 + 3, hexc("#d9d0a0"))


def draw_shop():
    """Sklep: 200 x 128, dach płaski; na parterze markiza i wystawa (można go obejść tylko po dachu)."""
    w, h = 200, 128
    c = facade(w, h, SAND, 11, cap=8, pattern="stucco")
    window_grid(c, 8, 18, w - 8, 66, 14, 18, 14, 8, 21, lit_ratio=0.3, curtains=True)
    # Parter: wystawa, drzwi, markiza, szyld.
    c.rect(3, 70, w - 6, h - 70, SAND[1])
    c.rect(3, 70, w - 6, 3, SAND[2])
    shopfront(c, 12, 88, 90, 36)
    shopfront(c, 112, 88, 76, 36, "shutter")
    door(c, 106, 94, 0, 0)
    awning(c, 8, 77, 98, 8)
    c.rect(124, 76, 52, 9, INK)
    c.rect(125, 77, 50, 7, hexc("#d03a22"))
    for i in range(0, 46, 6):      # napis "SKLEP" jako kreseczki
        c.rect(128 + i, 79, 4, 3, hexc("#ffe7a8"))
    c.save("l1_shop.png")


def draw_block():
    """Kamienica z balkonami: 200 x 128, dach płaski."""
    w, h = 200, 128
    c = facade(w, h, BRICK, 31, cap=8)
    window_grid(c, 10, 18, w - 10, 100, 12, 16, 22, 12, 41, lit_ratio=0.4, curtains=True)
    # Balkony pod co drugim oknem: płyta + balustrada.
    for by in (36, 64, 92):
        for bx in range(18, w - 24, 36):
            c.rect(bx - 2, by, 28, 3, hexc("#8a7a86"))
            c.hline(bx - 2, by + 3, 28, INK)
            for i in range(0, 26, 4):
                c.vline(bx + i, by - 8, 8, hexc("#3a3a46"))
            c.hline(bx - 1, by - 9, 26, hexc("#6a6a78"))
    c.rect(3, 106, w - 6, h - 106, BRICK[2])
    for i in range(6, w - 20, 40):
        door(c, i, 108, 14, 20, glow=(i // 40) % 2 == 0)
    c.save("l1_block.png")


def draw_office():
    """Biurowiec: 200 x 128, dach płaski z szarego betonu, pasy okien."""
    w, h = 200, 128
    c = facade(w, h, CONCRETE, 51, cap=8, pattern="stucco")
    for y in (18, 46, 74):
        for x in range(8, w - 8, 24):
            window(c, x, y, 18, 16, ((x // 24 + y) % 3 == 0), sill=False)
    c.rect(3, 98, w - 6, h - 98, CONCRETE[2])
    shopfront(c, 10, 104, 60, 20)
    shopfront(c, 78, 104, 60, 20)
    door(c, 150, 100, 20, 26, glow=True)
    c.save("l1_office.png")


def draw_arch():
    """Budynek-bramy: 220 x 264. Dół to przejście (wysokie na 64 px) z kolumnami, nad nim 4 piętra.
    Prawa ściana tego budynku jest ścianą szybu do wall jumpów (od 64 px nad ziemią w górę)."""
    w, h = 220, 264
    open_h = 64
    c = facade(w, h, BRICK, 61, cap=8)
    window_grid(c, 10, 18, w - 10, h - open_h - 8, 12, 16, 18, 14, 71, lit_ratio=0.35, curtains=True)
    # Architraw nad przejściem i ciemne wnętrze z odległym światłem ulicy.
    top = h - open_h
    c.rect(0, top - 6, w, 6, BRICK[2])
    c.hline(0, top - 6, w, hexc("#8a7a86"))
    c.rect(0, top, w, open_h, hexc("#1c1424"))
    for x in range(0, w, 3):
        c.vline(x, top + 18 + (x % 5), open_h - 18 - (x % 5), hexc("#241a30"))
    c.rect(w // 2 - 20, top + 10, 40, open_h - 10, hexc("#6a3a1e"))        # światło na końcu przejścia
    c.rect(w // 2 - 12, top + 18, 24, open_h - 18, hexc("#f08a30"))
    for x in (4, 62, 124, 186):                                              # kolumny
        c.rect(x, top, 10, open_h, BRICK[1])
        c.rect(x, top, 3, open_h, BRICK[2])
        c.rect(x + 8, top, 2, open_h, BRICK[0])
        c.rect(x - 1, top, 12, 4, hexc("#8a7a86"))
    c.save("l1_arch.png")


def draw_tower():
    """Wysoki budynek po prawej stronie szybu: 200 x 208, od ziemi do dachu."""
    w, h = 200, 208
    c = facade(w, h, CONCRETE, 81, cap=8, pattern="stucco")
    for y in range(18, h - 40, 30):
        for x in range(12, w - 12, 26):
            window(c, x, y, 14, 18, ((x * 3 + y) // 13 % 4 == 0))
    # Instalacje na ścianie od strony szybu (rura i klimatyzator), żeby szyb nie był pustym pasem.
    c.rect(6, 20, 4, h - 60, METAL[2])
    c.rect(6, 20, 1, h - 60, METAL[0])
    for y in (60, 120, 160):
        c.rect(5, y, 6, 4, METAL[1])
    c.rect(3, h - 36, w - 6, 36, CONCRETE[2])
    door(c, 150, h - 30, 20, 30, glow=True)
    shopfront(c, 20, h - 30, 70, 24, "shutter")
    c.save("l1_tower.png")


def draw_garage():
    """Garaż / budynek przy wyjściu: 200 x 144."""
    w, h = 200, 144
    c = facade(w, h, STEELB, 91, cap=8, pattern="stucco")
    window_grid(c, 10, 18, w - 10, 60, 14, 16, 18, 8, 95, lit_ratio=0.3)
    c.rect(3, 70, w - 6, h - 70, STEELB[1])
    for x in (14, 70):                                      # rolety garażowe
        shopfront(c, x, 84, 44, 56, "shutter")
    c.rect(8, 62, 150, 14, INK)
    for i in range(0, 142, 14):                             # pasy ostrzegawcze nad bramami
        c.rect(10 + i, 64, 7, 10, hexc("#e0a020"))
    c.save("l1_garage.png")


# ---------------------------------------------------------------------------
#  REKWIZYTY
# ---------------------------------------------------------------------------

def draw_crate():
    c = Canvas(32, 32)
    light, base, dark = WOOD
    c.rect(0, 0, 32, 32, base)
    for y in range(0, 32, 8):                       # deski
        c.hline(1, y + 7, 30, dark)
        c.hline(1, y, 30, light)
    c.rect(1, 1, 30, 3, light)
    for i in range(4, 28):                          # przekątna usztywniająca
        c.px(i, i, dark)
        c.px(i, i + 1, dark)
        c.px(i + 1, i, light)
    c.rect(1, 1, 4, 30, dark)
    c.rect(27, 1, 4, 30, dark)
    c.rect(1, 1, 4, 3, light)
    c.rect(27, 1, 4, 3, light)
    for x, y in ((2, 2), (28, 2), (2, 28), (28, 28)):
        c.rect(x, y, 2, 2, METAL[0])
    c.outline_box(0, 0, 32, 32, INK)
    c.save("l1_crate.png")


def draw_dumpster():
    w, h = 64, 40
    c = Canvas(w, h)
    light, base, dark = GREEN
    c.rect(1, 8, w - 2, h - 12, base)               # korpus
    for x in range(5, w - 4, 8):                    # żebra
        c.vline(x, 12, h - 20, dark)
        c.vline(x + 1, 12, h - 20, light)
    c.rect(1, 8, w - 2, 3, light)
    c.rect(1, h - 8, w - 2, 4, dark)
    c.rect(0, 1, w, 8, dark)                        # pokrywa
    c.rect(0, 1, w, 3, base)
    c.rect(0, 1, w, 1, light)
    c.rect(w - 14, 3, 10, 4, METAL[0])              # uchwyt
    for x in (8, w - 14):                           # kółka
        c.rect(x, h - 5, 7, 5, METAL[2])
        c.rect(x + 2, h - 4, 3, 3, METAL[0])
    c.rect(18, 20, 22, 10, hexc("#2c5c3c"))         # naklejka
    c.rect(20, 22, 18, 2, hexc("#f0e0a0"))
    c.rect(20, 26, 12, 2, hexc("#f0e0a0"))
    c.outline_alpha()
    # kontur nie mieści się w obrazku z każdej strony, więc dorysowujemy go na brzegach
    c.hline(0, 0, w, INK)
    c.save("l1_dumpster.png")


def draw_car():
    """Zaparkowany samochód z boku: 112 x 40. Kolizje: korpus (do 24 px nad ziemią) i kabina (nad nim, 60 px szer.)."""
    w, h = 112, 40
    c = Canvas(w, h)
    light, base, dark = TEAL
    # Korpus.
    c.rect(2, 16, w - 4, 18, base)
    c.rect(2, 16, w - 4, 3, light)
    c.rect(2, 30, w - 4, 4, dark)
    c.rect(4, 12, 20, 6, base)      # maska
    c.rect(w - 22, 13, 18, 5, base)  # bagażnik
    # Kabina.
    for i in range(0, 14):
        c.rect(24 + i // 2, 2 + (13 - i), 62 - i, 1, base)       # skosy szyb
    c.rect(26, 2, 58, 14, base)
    c.rect(26, 2, 58, 2, light)
    # Szyby.
    for x0, x1 in ((30, 53), (57, 80)):
        c.rect(x0, 5, x1 - x0, 9, hexc("#241a38"))
        for i in range(0, x1 - x0 - 4, 4):
            c.px(x0 + 3 + i, 6 + (i // 4) % 4, GLASS_SHINE)
    c.vline(55, 5, 9, base)
    # Światła i zderzaki.
    c.rect(w - 6, 20, 4, 5, hexc("#ff4a3a"))
    c.rect(2, 20, 4, 5, hexc("#ffe08a"))
    c.rect(0, 28, w, 5, dark)
    c.rect(0, 28, w, 1, METAL[0])
    # Koła.
    for cx in (24, 88):
        c.rect(cx - 8, 25, 16, 15, INK)
        c.rect(cx - 6, 27, 12, 12, hexc("#22202a"))
        c.rect(cx - 3, 30, 6, 6, METAL[0])
        c.rect(cx - 1, 32, 2, 2, METAL[2])
    c.rect(14, 22, 20, 3, INK)       # nadkola
    c.rect(78, 22, 20, 3, INK)
    c.rect(48, 26, 12, 2, dark)      # klamka / linia drzwi
    c.vline(55, 16, 12, dark)
    c.outline_alpha()
    c.save("l1_car.png")


def draw_fire_escape():
    """Schody przeciwpożarowe przy ścianie: 56 x 200. Lewa krawędź przylega do budynku. Podesty to 3 platformy
    jednokierunkowe w poziomie (patrz make_level1.py), a ten rysunek je ozdabia."""
    w, h = 56, 200
    c = Canvas(w, h)
    rail, dark = METAL[1], METAL[2]
    landings = [(0, 40, 56), (0, 104, 56), (0, 168, 56)]    # y górnej krawędzi podestów
    for (x, y, lw) in landings:
        c.rect(x, y, lw, 4, METAL[0])
        c.rect(x, y + 4, lw, 2, dark)
        for i in range(0, lw, 4):                           # kratownica pod podestem
            c.px(x + i, y + 6, dark)
            c.px(x + i + 2, y + 7, dark)
        for i in range(0, lw, 6):                           # barierka
            c.vline(x + i + 1, y - 14, 14, rail)
        c.hline(x, y - 15, lw, METAL[0])
        c.hline(x, y - 8, lw, rail)
    # Zygzak schodów między podestami.
    for k in range(2):
        y0 = 40 + k * 64 + 4
        for i in range(60):
            sx = 8 + i * 40 // 60 if k % 2 == 0 else 48 - i * 40 // 60
            c.rect(sx, y0 + i, 4, 1, METAL[1])
        c.vline(8 if k % 2 == 0 else 48, y0, 60, dark)
    c.outline_alpha()
    c.save("l1_fire_escape.png")


def draw_exit_door(open_):
    w, h = 56, 96
    c = Canvas(w, h)
    c.rect(0, 0, w, h, INK)
    c.rect(2, 2, w - 4, h - 2, METAL[2])                    # ościeżnica
    c.rect(5, 18, w - 10, h - 18, hexc("#20202a"))          # wnęka
    if open_:
        c.rect(5, 18, w - 10, h - 18, hexc("#ffd070"))      # światło zza drzwi
        c.rect(9, 22, w - 18, h - 22, hexc("#fff0b0"))
        c.rect(5, 18, 10, h - 18, METAL[1])                 # skrzydło odchylone
        c.rect(5, 18, 3, h - 18, METAL[0])
    else:
        c.rect(7, 20, w - 14, h - 20, METAL[1])
        c.rect(7, 20, 4, h - 20, METAL[0])
        c.rect(w - 11, 20, 4, h - 20, METAL[2])
        c.rect(12, 28, w - 24, 22, hexc("#2a3a46"))        # szybka
        c.rect(14, 30, w - 28, 3, hexc("#5a7a8c"))
        c.rect(w - 18, 64, 5, 3, hexc("#d9c060"))          # klamka
    # Świetlna tabliczka nad drzwiami: zielona, gdy otwarte.
    c.rect(6, 4, w - 12, 11, INK)
    c.rect(7, 5, w - 14, 9, hexc("#3cd488") if open_ else hexc("#7a2a2a"))
    glyphs = {
        "E": ["###", "#..", "##.", "#..", "###"],
        "X": ["#.#", "#.#", ".#.", "#.#", "#.#"],
        "I": ["###", ".#.", ".#.", ".#.", "###"],
        "T": ["###", ".#.", ".#.", ".#.", ".#."],
    }
    col = hexc("#0c3a24") if open_ else hexc("#ffb0a0")
    gx = 11
    for ch in "EXIT":
        for ry, row in enumerate(glyphs[ch]):
            for rx, v in enumerate(row):
                if v == "#":
                    c.px(gx + rx, 6 + ry - 0, col)
        gx += 9
    c.save("l1_exit_door_open.png" if open_ else "l1_exit_door.png")


def draw_spike():
    """Kolce 32 x 8: cztery stalowe zęby na płytce."""
    c = Canvas(32, 8)
    for t in range(4):
        x0 = t * 8
        for row in range(7):
            half = (row + 1) * 4 // 7 + 0
            for x in range(x0 + 4 - half - 1, x0 + 4 + half + 1):
                if x0 <= x < x0 + 8:
                    col = METAL[0] if x < x0 + 4 else METAL[2]
                    c.px(x, row, col)
        c.px(x0 + 3, 0, hexc("#e4ecf2"))
        c.px(x0 + 4, 0, hexc("#c8d2dc"))
    c.rect(0, 7, 32, 1, hexc("#2a2a34"))
    c.save("spike.png")


def draw_jump_pad():
    """Skocznia 32 x 8: płytka ze sprężyną; kolor akcentu jak światło zachodu."""
    c = Canvas(32, 8)
    c.rect(0, 6, 32, 2, hexc("#2a2a34"))                    # podstawa
    for x in range(4, 30, 7):                              # sprężyny
        c.rect(x, 3, 3, 3, METAL[0])
        c.px(x + 1, 4, METAL[2])
    c.rect(0, 0, 32, 3, hexc("#ff8a1f"))                    # płyta
    c.hline(0, 0, 32, hexc("#ffd98a"))
    c.hline(0, 2, 32, hexc("#c4601a"))
    for x in range(2, 30, 8):                              # pasy
        c.rect(x, 1, 4, 1, hexc("#fff3a0"))
    c.save("jump_pad.png")


if __name__ == "__main__":
    draw_city()
    draw_sidewalk()
    draw_shop()
    draw_block()
    draw_office()
    draw_arch()
    draw_tower()
    draw_garage()
    draw_crate()
    draw_dumpster()
    draw_car()
    draw_fire_escape()
    draw_exit_door(False)
    draw_exit_door(True)
    draw_spike()
    draw_jump_pad()