"""Rysuje miniatury poziomów do menu głównego (to ilustracje, a nie zrzuty ekranu z gry).

Uruchom z głównego katalogu repozytorium:   python "tools/make level thumbnails.py"
(wymaga bibliotek Pillow i numpy:  pip install pillow numpy)

Powstają pliki assets/thumb_level1.png ... thumb_level7.png (160 x 90, proporcje 16:9 jak miniatura na karcie w menu).
Każda miniatura to osobna scena-plakat: jedno hasło wizualne poziomu, mocny kontrast, w stylu gry (trzy tony,
ciemny kontur, pomarańcz Trelvosu, żółte światło okien). Postacie i bomby są wzięte z gotowych grafik w assets/
(player_sheet, enemy_*_sheet, bomb, panel), więc zmiana ich wyglądu przenosi się na miniatury po ponownym uruchomieniu.

  1  Samouczek            zachód słońca nad miastem, gracz i bomba na dachu
  2  Trelvos w biały dzień  wieżowiec Trelvosu w słońcu, trzy bomby na ulicy
  3  Trelvos nocą         księżyc, reflektory, bomby żarzące się na dachach
  4  Dachy Trelvosu       skok z liną i hakiem między wieżowcami
  5  Nocna zmiana         strażnik z latarką, gracz za skrzynią, terminal panelu
  6  (brak - poziom 6 nie istnieje w repozytorium)
  7  Kamil                bossfight: Kamil w czerwonej bluzie w serwerowni z trzema panelami

Nazwy tekstur (textures.js): level1Thumbnail ... level7Thumbnail. Pole poziomu: "thumbnail": "level5Thumbnail".
"""

import random
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
W, H = 320, 180          # rozmiar rysunku
OUT_W, OUT_H = 160, 90    # rozmiar pliku miniatury

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def hexc(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


INK = hexc("#0a0d14")
ORANGE = (hexc("#ffb060"), hexc("#ee7a2a"), hexc("#9a3e14"))
YELLOW = (hexc("#fff0a0"), hexc("#ffd23c"), hexc("#c48a1a"))
STEEL = (hexc("#c2cad6"), hexc("#8792a4"), hexc("#566174"))
WHITE = hexc("#f4f8ff")


# ---------------------------------------------------------------------------
#  Płótno
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self):
        self.a = np.zeros((H, W, 3), dtype=np.float32)

    # -- podstawy -----------------------------------------------------------
    def px(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            self.a[y, x] = c[:3]

    def rect(self, x, y, w, h, c):
        x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        if x1 > x0 and y1 > y0:
            self.a[y0:y1, x0:x1] = c[:3]

    def shaded(self, x, y, w, h, tones, ink=False):
        light, base, dark = tones
        self.rect(x, y, w, h, base)
        self.rect(x, y, w, 1, light)
        self.rect(x, y, 1, h, light)
        self.rect(x, y + h - 1, w, 1, dark)
        self.rect(x + w - 1, y, 1, h, dark)
        if ink:
            self.frame(x - 1, y - 1, w + 2, h + 2, INK)

    def frame(self, x, y, w, h, c):
        self.rect(x, y, w, 1, c)
        self.rect(x, y + h - 1, w, 1, c)
        self.rect(x, y, 1, h, c)
        self.rect(x + w - 1, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c, thick=1):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.rect(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), thick, thick, c)

    def disc(self, cx, cy, r, c):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + r // 2:
                    self.px(x, y, c)

    # -- światło i tło ------------------------------------------------------
    def sky(self, stops, y0=0, y1=H):
        """Pasmowy gradient z rastrem (dither) na przejściach: wygląda jak ręcznie malowany pixel art."""
        n = len(stops) - 1
        for y in range(max(0, y0), min(H, y1)):
            t = (y - y0) / max(1, (y1 - y0 - 1)) * n
            i = min(int(t), n - 1)
            frac = t - i
            xs = np.arange(W)
            take_next = BAYER[y % 4, xs % 4] < frac
            for ch in range(3):
                self.a[y, :, ch] = np.where(take_next, stops[i + 1][ch], stops[i][ch])

    def glow(self, cx, cy, rx, ry, c, strength=0.5, steps=5):
        """Poświata: warstwy eliptyczne z rastrem, od zewnątrz do środka coraz jaśniejsze."""
        ys, xs = np.mgrid[0:H, 0:W]
        d = np.sqrt(((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2)
        for i in range(steps):
            r = 1 - i / steps
            level = strength * (i + 1) / steps
            inside = d < r
            mask = inside & (BAYER[ys % 4, xs % 4] < level)
            self.a[mask] = self.a[mask] * (1 - 0.55) + np.array(c[:3]) * 0.55

    def tint(self, x, y, w, h, c, alpha):
        x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        if x1 > x0 and y1 > y0:
            region = self.a[y0:y1, x0:x1]
            self.a[y0:y1, x0:x1] = region * (1 - alpha) + np.array(c[:3]) * alpha

    def beam(self, x0, y0, x1a, x1b, y1, c, strength=0.35):
        """Stożek światła (reflektor, latarka): od punktu (x0, y0) do odcinka [x1a, x1b] na wysokości y1, z rastrem."""
        ys, xs = np.mgrid[0:H, 0:W]
        t = np.clip((ys - y0) / max(1, (y1 - y0)), 0, 1)
        left = x0 + (x1a - x0) * t
        right = x0 + (x1b - x0) * t
        inside = (ys >= y0) & (ys <= y1) & (xs >= left) & (xs <= right)
        centre = (left + right) / 2
        half = np.maximum((right - left) / 2, 1)
        k = 1 - np.abs(xs - centre) / half            # 1 w osi, 0 na brzegu
        level = strength * (0.35 + 0.65 * k) * (1 - 0.55 * t)
        mask = inside & (BAYER[ys % 4, xs % 4] < level)
        self.a[mask] = self.a[mask] * 0.45 + np.array(c[:3]) * 0.55

    def vignette(self, strength=0.6, depth=0.28):
        ys, xs = np.mgrid[0:H, 0:W]
        dx = np.minimum(xs, W - 1 - xs) / (W * depth)
        dy = np.minimum(ys, H - 1 - ys) / (H * depth * 1.4)
        edge = np.clip(np.minimum(dx, dy), 0, 1)
        level = (1 - edge) * strength
        mask = BAYER[ys % 4, xs % 4] < level
        self.a[mask] *= 0.55

    # -- sprite'y z assets --------------------------------------------------
    def sprite(self, arr, x, y, scale=1, flip=False, outline=True, tint=None):
        """Wkleja RGBA (numpy) z lewym górnym rogiem w (x, y), powiększone w całkowitą skalę, z czarnym konturem."""
        if flip:
            arr = arr[:, ::-1]
        if scale > 1:
            arr = np.repeat(np.repeat(arr, scale, axis=0), scale, axis=1)
        h, w = arr.shape[:2]
        alpha = arr[:, :, 3] > 0
        if outline:
            pad = max(1, scale // 2 + (scale > 1))
            grown = np.zeros((h + 2 * pad, w + 2 * pad), dtype=bool)
            for dy in range(-pad, pad + 1):
                for dx in range(-pad, pad + 1):
                    if dx * dx + dy * dy <= pad * pad + 1:
                        grown[pad + dy:pad + dy + h, pad + dx:pad + dx + w] |= alpha
            ring = grown.copy()
            ring[pad:pad + h, pad:pad + w] &= ~alpha
            for yy, xx in zip(*np.nonzero(ring)):
                self.px(x - pad + xx, y - pad + yy, INK)
        for yy, xx in zip(*np.nonzero(alpha)):
            colour = arr[yy, xx, :3]
            if tint is not None:
                colour = np.array(colour) * (1 - tint[1]) + np.array(tint[0]) * tint[1]
            self.px(x + xx, y + yy, colour)

    def text(self, x, y, text, scale, color):
        for ch in text:
            for ry, row in enumerate(GLYPHS.get(ch, GLYPHS[" "])):
                for rx, v in enumerate(row):
                    if v == "#":
                        self.rect(x + rx * scale, y + ry * scale, scale, scale, color)
            x += 6 * scale

    def save(self, name):
        """Rysunek powstaje w 320 x 180 (więcej detali), do pliku trafia 160 x 90: miniatura w menu ma ok. 120-150 px
        szerokości, więc przy skali ~1:1 wzór rastra nie robi mory (przy zmniejszaniu "najbliższym sąsiadem" robił)."""
        im = Image.fromarray(np.clip(self.a, 0, 255).astype(np.uint8), "RGB").resize((OUT_W, OUT_H), Image.BOX)
        im.save(ASSETS / name)
        print(f"{name}: {OUT_W}x{OUT_H}")


_FONT = """
T #####/..#../..#../..#../..#../..#../..#..
R ####./#...#/#...#/####./#.#../#..#./#...#
E #####/#..../#..../####./#..../#..../#####
L #..../#..../#..../#..../#..../#..../#####
V #...#/#...#/#...#/#...#/#...#/.#.#./..#..
O .###./#...#/#...#/#...#/#...#/#...#/.###.
S .####/#..../#..../.###./....#/....#/####.
H #...#/#...#/#...#/#####/#...#/#...#/#...#
K #...#/#..#./#.#../##.../#.#../#..#./#...#
U #...#/#...#/#...#/#...#/#...#/#...#/.###.
B ####./#...#/#...#/####./#...#/#...#/####.
"""
GLYPHS = {" ": ["....."] * 7}
for _line in _FONT.strip().splitlines():
    _ch, _rows = _line.split(" ", 1)
    GLYPHS[_ch] = _rows.split("/")


def load(name, box=None):
    im = Image.open(ASSETS / name).convert("RGBA")
    if box:
        im = im.crop(box)
    arr = np.array(im)
    ys, xs = np.nonzero(arr[:, :, 3] > 0)
    return arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def player(col=0, row=0):
    """Klatka z player_sheet.png (komórki 32 x 32): wiersz 0 stoi, 1 idzie, 4 dash, 5 podciąga się na linie."""
    return load("player_sheet.png", (col * 32, row * 32, col * 32 + 32, row * 32 + 32))


def guard(col=0, row=0):
    return load("enemy_weak_sheet.png", (col * 32, row * 40, col * 32 + 32, row * 40 + 40))


def kamil(col=0, row=0):
    return load("enemy_boss_sheet.png", (col * 40, row * 48, col * 40 + 40, row * 48 + 48))


def bomb_sprite():
    return load("bomb.png")


def panel_sprite(defused=False):
    return load("panel_defused.png" if defused else "panel.png")


# ---------------------------------------------------------------------------
#  Elementy miasta
# ---------------------------------------------------------------------------
def skyline(c, y_base, colors, seed, min_h, max_h, width_range=(14, 30), windows=None, gap=(0, 3), x0=-5):
    """Rząd budynków (sylwetki) stojących na linii y_base. windows = (kolor, szansa) rysuje zapalone okna."""
    rnd = random.Random(seed)
    x = x0
    boxes = []
    while x < W:
        w = rnd.randint(*width_range)
        h = rnd.randint(min_h, max_h)
        top = y_base - h
        c.rect(x, top, w, h, colors[1])
        c.rect(x, top, w, 1, colors[0])
        c.rect(x + w - 2, top, 2, h, colors[2])
        if rnd.random() < 0.3:
            c.rect(x + w // 2, top - rnd.randint(3, 8), 1, rnd.randint(3, 8), colors[2])   # antena
        if windows:
            for wy in range(top + 4, y_base - 3, 5):
                for wx in range(x + 3, x + w - 4, 4):
                    if rnd.random() < windows[1]:
                        c.rect(wx, wy, 2, 2, windows[0])
        boxes.append((x, top, w, h))
        x += w + rnd.randint(*gap)
    return boxes


def stars(c, seed, count, y_max, colors=(WHITE, hexc("#9fb4e8"))):
    rnd = random.Random(seed)
    for _ in range(count):
        c.px(rnd.randrange(W), rnd.randrange(y_max), rnd.choice(colors))


def moon(c, cx, cy, r, crescent=True):
    c.glow(cx, cy, r * 3.4, r * 3.4, hexc("#9db4ff"), 0.45, 6)
    c.disc(cx, cy, r, hexc("#fff4c8"))
    if crescent:
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + r // 2 and (x - (cx + r // 2)) ** 2 + (y - (cy - r // 4)) ** 2 <= (r * 0.92) ** 2:
                    c.px(x, y, hexc("#16224c"))
    # kratery
    for dx, dy, rr in [(-r // 3, r // 3, 2), (-r // 2, -r // 5, 1)]:
        pass


def cloud(c, x, y, w, tones):
    light, base, dark = tones
    h = max(6, w // 4)
    c.rect(x + 3, y + h - 3, w - 6, 3, base)
    for i, (dx, rr) in enumerate([(w * 0.28, h * 0.55), (w * 0.52, h * 0.78), (w * 0.74, h * 0.5)]):
        c.disc(int(x + dx), int(y + h - 3 - rr * 0.4), int(rr), base)
    c.rect(x + 3, y + h, w - 6, 2, dark)
    for dx in range(int(w * 0.3), int(w * 0.7), 1):
        c.px(x + dx, y + 2, light)


def bomb_with_glow(c, x, y, scale=1, glow_color=hexc("#ff5a3c"), glow_strength=0.5):
    arr = bomb_sprite()
    h, w = arr.shape[:2]
    c.glow(x + w * scale // 2, y + h * scale // 2, w * scale * 0.9, h * scale * 1.1, glow_color, glow_strength, 5)
    c.sprite(arr, x, y, scale)
    return w * scale, h * scale


def trelvos_sign(c, x, y, scale=1):
    width = len("TRELVOS") * 6 * scale - scale
    c.rect(x - 2 * scale, y - 2 * scale, width + 4 * scale, 7 * scale + 4 * scale, hexc("#1a1f2c"))
    c.frame(x - 2 * scale, y - 2 * scale, width + 4 * scale, 7 * scale + 4 * scale, ORANGE[2])
    c.text(x + scale, y + scale, "TRELVOS", scale, ORANGE[2])
    c.text(x, y, "TRELVOS", scale, ORANGE[0])
    return width


def tower(c, x, y_top, w, y_base, tones, win_on, win_off, seed, cols=None, rows_step=6, sign_scale=0, lit=0.7):
    """Wieżowiec z siatką okien (plakat: elewacja z przodu)."""
    rnd = random.Random(seed)
    c.shaded(x, y_top, w, y_base - y_top, tones, ink=True)
    cols = cols or max(2, (w - 6) // 7)
    cw = (w - 6) // cols
    for wy in range(y_top + 10 + sign_scale * 10, y_base - 8, rows_step + 2):
        for i in range(cols):
            wx = x + 4 + i * cw
            c.rect(wx, wy, cw - 2, rows_step - 1, win_on if rnd.random() < lit else win_off)


# ---------------------------------------------------------------------------
#  Miniatury
# ---------------------------------------------------------------------------
def thumb_1():
    """Samouczek: zachód słońca, gracz patrzy na bombę na dachu."""
    c = Canvas()
    stops = [hexc("#2a2152"), hexc("#5b2f77"), hexc("#a8456a"), hexc("#e8704e"), hexc("#ffa458"), hexc("#ffd478")]
    c.sky(stops, 0, 118)
    stars(c, 11, 30, 40)
    # słońce z poziomymi nacięciami (retro), schowane za miastem
    cx, cy, r = 92, 104, 36
    c.glow(cx, cy, 100, 64, hexc("#ffb060"), 0.5, 6)
    for y in range(cy - r, cy + r + 1):
        k = y - (cy - r)
        if k > 22 and (k % 6) >= 6 - min(3, (k - 20) // 6 + 1):
            continue
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                c.px(x, y, hexc("#ffe28a") if y < cy else hexc("#ffc060"))
    skyline(c, 124, (hexc("#a8548c"), hexc("#7a3a76"), hexc("#552a62")), 3, 12, 38, (16, 26), None)
    skyline(c, 130, (hexc("#5b3068"), hexc("#3f2352"), hexc("#2c1a40")), 5, 18, 54, (14, 28), (hexc("#ffd478"), 0.18), (0, 2))
    # dach
    c.rect(0, 140, W, 40, hexc("#241a3c"))
    c.rect(0, 140, W, 2, hexc("#4a3a68"))
    c.rect(0, 142, W, 1, hexc("#17102a"))
    for x in range(0, W, 16):
        c.rect(x, 146, 15, 1, hexc("#31254f"))
    for x in range(8, W, 32):
        c.rect(x, 154, 15, 1, hexc("#31254f"))
        c.rect(x + 16, 162, 15, 1, hexc("#31254f"))
    # gracz po lewej, bomba po prawej, żółte strzałki między nimi
    p = player(0, 0)
    c.glow(110, 112, 40, 40, hexc("#ffb060"), 0.35, 5)
    c.sprite(p, 92, 150 - p.shape[0] * 2, 2)
    b = bomb_sprite()
    bx, by = 196, 150 - b.shape[0] * 2
    c.rect(bx + 4, 148, b.shape[1] * 2 - 8, 5, hexc("#17102a"))
    bomb_with_glow(c, bx, by, 2, hexc("#ff6a3c"), 0.5)
    for i in range(3):
        x0 = 150 + i * 12
        for k in range(7):
            c.rect(x0 + (k if k < 4 else 6 - k), 108 + k, 3, 1, YELLOW[1] if i < 2 else YELLOW[0])
    c.vignette(0.45)
    c.save("thumb_level1.png")


def thumb_2():
    """Trelvos w biały dzień: wieżowiec firmy w słońcu i trzy bomby na ulicy."""
    c = Canvas()
    c.sky([hexc("#3f8ad8"), hexc("#68aef0"), hexc("#9ad0f8"), hexc("#cfeafc"), hexc("#f4f8e8")], 0, 138)
    c.glow(268, 30, 70, 50, hexc("#fff6c8"), 0.55, 6)
    c.disc(268, 30, 14, hexc("#fff6b0"))
    c.disc(268, 30, 11, hexc("#fffbe0"))
    cl = (hexc("#ffffff"), hexc("#f0f6ff"), hexc("#bcd0ea"))
    cloud(c, 26, 22, 56, cl)
    cloud(c, 118, 40, 40, cl)
    cloud(c, 196, 14, 46, cl)
    # tło: dalsze budynki
    far = (hexc("#a8c4e0"), hexc("#86a6cc"), hexc("#6a88b0"))
    skyline(c, 138, far, 21, 20, 70, (16, 28), (hexc("#dff0ff"), 0.45), (0, 2))
    # wieżowiec Trelvosu pośrodku
    tw = (hexc("#b8d4ea"), hexc("#7a9cc4"), hexc("#4e6c96"))
    tower(c, 126, 22, 68, 140, tw, hexc("#ffe888"), hexc("#3c5a86"), 9, cols=7, rows_step=6, sign_scale=1, lit=0.5)
    c.rect(124, 20, 72, 4, hexc("#d8e8f4"))
    c.rect(124, 24, 72, 1, hexc("#4e6c96"))
    trelvos_sign(c, 134, 28, 1)
    c.rect(158, 8, 3, 12, hexc("#4e6c96"))
    c.px(159, 7, hexc("#ff5a4a"))
    # boczne wieże (niższe)
    tower(c, 86, 70, 34, 140, (hexc("#d8c4a8"), hexc("#b49a7c"), hexc("#7e6850")), hexc("#fff0b0"), hexc("#5a4a3c"), 3, cols=4, lit=0.5)
    tower(c, 200, 62, 38, 140, (hexc("#e8c4b8"), hexc("#c08c7c"), hexc("#84564c")), hexc("#fff0b0"), hexc("#5a3c38"), 4, cols=4, lit=0.5)
    # ulica
    c.rect(0, 140, W, 40, hexc("#4a5568"))
    c.rect(0, 140, W, 6, hexc("#9aa6b4"))                         # chodnik
    c.rect(0, 146, W, 1, hexc("#2e3646"))
    for x in range(6, W, 40):
        c.rect(x, 164, 22, 3, hexc("#f0e6b0"))                    # pasy
    # trzy bomby na chodniku, każda w ciepłej poświacie
    for i, x in enumerate((52, 134, 216)):
        c.rect(x + 4, 150, 46, 4, hexc("#2e3646"))
        bomb_with_glow(c, x, 118 + 0, 1, hexc("#ff7a50"), 0.3) if False else None
        c.rect(x + 3, 132 + 18, 48, 3, hexc("#34405a"))
        bomb_with_glow(c, x, 116 + 18, 1, hexc("#ff6a3c"), 0.35)
    c.vignette(0.4)
    c.save("thumb_level2.png")


def thumb_3():
    """Trelvos nocą: księżyc, skrzyżowane reflektory, bomby żarzące się na dachach."""
    c = Canvas()
    c.sky([hexc("#070b20"), hexc("#0e1838"), hexc("#18285a"), hexc("#27407a"), hexc("#3d5c96")], 0, 130)
    stars(c, 5, 70, 80)
    moon(c, 252, 40, 18)
    skyline(c, 132, (hexc("#26386a"), hexc("#1b2a54"), hexc("#121c3c")), 2, 18, 62, (16, 28), (hexc("#ffe08a"), 0.22), (0, 2))
    # reflektory z dwóch dachów, skrzyżowane wiązki
    c.beam(70, 128, 150, 196, 0, hexc("#e8f4ff"), 0.55)
    c.beam(250, 128, 140, 190, 0, hexc("#e8f4ff"), 0.55)
    # bliższy rząd budynków i wieża Trelvosu z neonem
    boxes = skyline(c, 150, (hexc("#1b2a54"), hexc("#121b3a"), hexc("#0b1128")), 8, 24, 60, (22, 38), (hexc("#ffd060"), 0.3), (2, 6), -10)
    tw = (hexc("#2e3f78"), hexc("#1d2a58"), hexc("#111a3a"))
    tower(c, 40, 52, 56, 150, tw, hexc("#ffdf7a"), hexc("#16204a"), 14, cols=6, rows_step=6, sign_scale=1, lit=0.45)
    c.glow(68, 62, 52, 16, hexc("#ff8a3c"), 0.45, 5)
    trelvos_sign(c, 46, 56, 1)
    c.rect(66, 36, 2, 16, hexc("#121a3a"))
    c.px(66, 35, hexc("#ff4a4a"))
    # trzy bomby na dachach (każdy dach to osobny blok z oknami), z czerwoną poświatą
    roof = (hexc("#34477e"), hexc("#222f5e"), hexc("#141c3e"))
    for (x, ytop) in [(112, 116), (182, 108), (248, 120)]:
        c.shaded(x, ytop, 58, 150 - ytop, roof, ink=True)
        for wy in range(ytop + 8, 146, 8):
            for wx in range(x + 5, x + 52, 9):
                c.rect(wx, wy, 4, 4, hexc("#ffd060") if (wx * wy) % 7 < 2 else hexc("#18244c"))
        bomb_with_glow(c, x + 2, ytop - 34, 1, hexc("#ff3c3c"), 0.55)
    # ulica i dół
    c.rect(0, 150, W, 30, hexc("#0a1026"))
    c.rect(0, 150, W, 1, hexc("#26386a"))
    for x in range(10, W, 50):
        c.rect(x, 168, 24, 2, hexc("#3a4a78"))
    c.vignette(0.5)
    c.save("thumb_level3.png")


def thumb_4():
    """Dachy Trelvosu: skok z liną i hakiem między wieżowcami o zachodzie słońca."""
    c = Canvas()
    c.sky([hexc("#123a5c"), hexc("#2a6a86"), hexc("#d8886a"), hexc("#ffb464"), hexc("#ffe090")], 0, 150)
    c.glow(160, 140, 120, 70, hexc("#ffc070"), 0.5, 6)
    skyline(c, 150, (hexc("#9a5a72"), hexc("#6e3e5e"), hexc("#4a2848")), 4, 20, 60, (14, 26), None, (0, 2))
    skyline(c, 160, (hexc("#4a3458"), hexc("#34223e"), hexc("#241630")), 6, 14, 44, (14, 24), (hexc("#ffe08a"), 0.12), (0, 2))
    # lewy wieżowiec (odbicie z krawędzi) i prawy
    left = (hexc("#5d7490"), hexc("#3f536e"), hexc("#2b3a52"))
    right = (hexc("#6a7ca0"), hexc("#475a7a"), hexc("#303f5e"))
    c.shaded(-4, 92, 82, 100, left, ink=True)
    c.rect(-4, 88, 86, 5, hexc("#8ea4c0"))
    c.rect(-4, 93, 86, 1, hexc("#2b3a52"))
    for y in range(102, 176, 9):
        for x in range(6, 72, 11):
            c.rect(x, y, 6, 5, hexc("#ffd878") if (x + y) % 3 else hexc("#33425e"))
    c.shaded(244, 74, 90, 120, right, ink=True)
    c.rect(242, 70, 94, 5, hexc("#9eb2cc"))
    c.rect(242, 75, 94, 1, hexc("#303f5e"))
    for y in range(84, 176, 9):
        for x in range(252, 316, 11):
            c.rect(x, y, 6, 5, hexc("#ffd878") if (x * y) % 5 else hexc("#33425e"))
    # klimatyzator i antena na dachach
    c.shaded(50, 78, 22, 10, STEEL, ink=True)
    c.rect(54, 80, 14, 1, STEEL[2])
    c.rect(280, 52, 2, 22, hexc("#2b3a52"))
    c.px(280, 51, hexc("#ff4a4a"))
    c.shaded(252, 62, 20, 8, STEEL, ink=True)
    # lina z hakiem: łuk od prawego dachu do postaci
    p = player(0, 4)
    px, py = 142, 62
    # łuk liny
    pts = []
    for i in range(0, 41):
        t = i / 40
        x = 244 + (px + 14 - 244) * t
        y = 70 + (py + 8 - 70) * t + 14 * np.sin(t * np.pi)
        pts.append((round(x), round(y)))
    for (x, y) in pts:
        c.rect(x, y, 1, 1, hexc("#e8d8a8"))
        c.rect(x, y + 1, 1, 1, hexc("#7a6040"))
    hook = load("hook.png")
    c.sprite(hook, 236, 64, 1)
    # smugi ruchu za graczem (dash) i postać
    c.glow(px + 32, py + 32, 46, 40, hexc("#fff0c0"), 0.4, 5)
    c.sprite(p, px, py, 2)
    # ostrzegawcza pustka na dole i kreski wysokości
    c.rect(78, 170, 166, 10, hexc("#120c1e"))
    for x in range(80, 244, 12):
        c.rect(x, 172, 6, 1, hexc("#2a1c3c"))
    c.vignette(0.5)
    c.save("thumb_level4.png")


def thumb_5():
    """Nocna zmiana: strażnik świeci latarką w stronę terminalu, gracz skrada się za nim zza skrzyni."""
    c = Canvas()
    c.sky([hexc("#050a14"), hexc("#0a1424"), hexc("#10203a"), hexc("#18304c")], 0, 120)
    stars(c, 3, 40, 50)
    skyline(c, 118, (hexc("#1a2a48"), hexc("#111c34"), hexc("#0a1224")), 7, 20, 60, (16, 30), (hexc("#3a5a84"), 0.1), (0, 2))
    # siedziba w tle
    c.shaded(206, 30, 100, 96, (hexc("#2a3a5a"), hexc("#1c2a46"), hexc("#111a30")), ink=True)
    rnd = random.Random(9)
    for y in range(46, 118, 10):
        for x in range(212, 300, 10):
            c.rect(x, y, 6, 5, hexc("#ffd878") if rnd.random() < 0.25 else hexc("#14203a"))
    trelvos_sign(c, 228, 36, 1)
    # betonowy plac
    c.rect(0, 126, W, 54, hexc("#16203a"))
    c.rect(0, 126, W, 2, hexc("#30426a"))
    c.rect(0, 128, W, 1, hexc("#0a1224"))
    for x in range(0, W, 20):
        c.rect(x, 140, 19, 1, hexc("#1f2c4c"))
        c.rect(x + 10, 156, 19, 1, hexc("#1f2c4c"))
    floor_y = 164
    # terminal panelu (po prawej) z zieloną poświatą
    pan = panel_sprite()
    c.glow(280, 148, 44, 36, hexc("#68ff9c"), 0.45, 5)
    c.sprite(pan, 266, floor_y - pan.shape[0] * 1 - 2, 1)
    # strażnik odwrócony w prawo, latarka świeci na terminal
    g = guard()
    gx, gy = 168, floor_y - g.shape[0] * 2
    c.beam(gx + 62, gy + 40, 330, 330, floor_y - 50, hexc("#ffe8a0"), 0.0) if False else None
    c.beam(gx + 54, gy + 44, 246, 340, floor_y + 12, hexc("#ffe8a0"), 0.8)
    c.sprite(g, gx, gy, 2)
    c.glow(gx + 58, gy + 44, 16, 12, hexc("#ffe8a0"), 0.8, 5)
    c.rect(gx + 56, gy + 42, 4, 3, hexc("#fff8d0"))
    # gracz skrada się za strażnikiem, ukryty za skrzynią (poza wiązką), w chłodnej poświacie
    pp = player(2, 1)
    c.glow(78, floor_y - 40, 48, 44, hexc("#7aa0ff"), 0.35, 5)
    c.sprite(pp, 62, floor_y - pp.shape[0] * 2, 2)
    c.shaded(28, floor_y - 30, 56, 30, (hexc("#b48a5a"), hexc("#8a6440"), hexc("#5a3e26")), ink=True)
    c.rect(30, floor_y - 17, 52, 1, hexc("#5a3e26"))
    c.rect(55, floor_y - 29, 1, 28, hexc("#5a3e26"))
    c.vignette(0.55)
    c.save("thumb_level5.png")


def thumb_7():
    """Kamil: bossfight w serwerowni siedziby, trzy panele na ścianie, czerwony alarm."""
    c = Canvas()
    c.sky([hexc("#1a2234"), hexc("#222d44"), hexc("#2c3a56")], 0, 130)
    # ściana serwerowni: pionowe szafy z diodami
    rnd = random.Random(7)
    for x in range(0, W, 24):
        c.shaded(x, 20, 22, 112, (hexc("#4a5268"), hexc("#2e3446"), hexc("#171b28")), ink=True)
        for y in range(26, 126, 7):
            c.rect(x + 3, y, 16, 4, hexc("#12151f"))
            for k in range(3):
                col = rnd.choice([hexc("#78ff9c"), hexc("#ffc050"), hexc("#68e0ff"), hexc("#ff6a5a"), hexc("#12151f")])
                c.rect(x + 4 + k * 3, y + 1, 2, 2, col)
    # trzy panele ponad szafami: jarzą się na pomarańczowo
    pan = panel_sprite()
    for i, x in enumerate((92, 144, 196)):
        c.glow(x + 16, 38, 34, 28, hexc("#ffb060"), 0.5, 5)
        c.rect(x - 6, 12, 44, 52, hexc("#1a1f2c"))
        c.frame(x - 6, 12, 44, 52, hexc("#c48a1a"))
        c.sprite(pan, x, 18, 1)
        c.rect(x + 3, 62 - 6, 26, 2, hexc("#ffd23c") if i % 2 == 0 else hexc("#12151f"))
    # czerwony alarm: nakładka, lampy po bokach
    c.tint(0, 0, W, H, hexc("#c02830"), 0.22)
    for x in (10, 300):
        c.glow(x, 20, 40, 30, hexc("#ff4a4a"), 0.7, 6)
        c.rect(x - 4, 14, 9, 9, hexc("#ff6a5a"))
        c.frame(x - 5, 13, 11, 11, INK)
    # posadzka z żółto-czarnymi pasami
    c.rect(0, 132, W, 48, hexc("#2a3144"))
    c.rect(0, 132, W, 2, hexc("#58627a"))
    for x in range(-20, W + 20, 14):
        for k in range(8):
            c.rect(x + k, 164 + k // 2, 7, 1, hexc("#ffd23c")) if False else None
    for x in range(0, W, 16):
        c.rect(x, 168, 8, 6, hexc("#ffd23c"))
        c.rect(x + 8, 168, 8, 6, INK)
    c.rect(0, 167, W, 1, INK)
    c.rect(0, 174, W, 1, INK)
    # Kamil: duży, centralnie, czerwona poświata z tyłu
    k = kamil(1, 1)
    scale = 3
    kx = 160 - k.shape[1] * scale // 2 + 20
    ky = 168 - k.shape[0] * scale + 4
    c.glow(kx + k.shape[1] * scale // 2, ky + k.shape[0] * scale // 2, 70, 80, hexc("#ff4a4a"), 0.45, 6)
    c.rect(kx - 6, 164, k.shape[1] * scale + 12, 4, hexc("#12151f"))
    c.sprite(k, kx, ky, scale, flip=False)
    c.vignette(0.55)
    c.save("thumb_level7.png")


if __name__ == "__main__":
    thumb_1()
    thumb_2()
    thumb_3()
    thumb_4()
    thumb_5()
    thumb_7()
