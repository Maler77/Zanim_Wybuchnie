"""Rysuje sprite sheety przeciwników: assets/enemy_weak_sheet.png i assets/enemy_strong_sheet.png.

Uruchom z głównego katalogu repozytorium:   python tools/make_enemy_sheets.py
(wymaga biblioteki Pillow:  pip install pillow)

Styl jest dopasowany do gracza i teł: ciemne sylwetki z czarnym, 1-pikselowym konturem, przygaszone
kolory, jaskrawy akcent (pomarańcz kamizelki, żółć jak oświetlone okna w tle, czerwień jak maska gracza)
i duże, "chibi" głowy. Postaci patrzą w PRAWO, stopy stoją na dolnej krawędzi klatki (tak jak u gracza).

Trzy typy (zgodnie z ENEMY_TYPES w src/js/enemies.js):
  weak    zradykalizowany członek grupy: kominiarka, oliwkowe ubranie polowe, brązowa kamizelka taktyczna,
          łom. Inspirowany agentem Ground Rebel z CS2 (własna, uproszczona postać). Klatka 32 x 40 px (hitbox 24 x 40)
  strong  ochroniarz w kamizelce i hełmie z wizjerem, z pałką, klatka 44 x 52 px (hitbox 36 x 52)

  boss    Kamil, boss poziomu: bordowa bluza z kapturem, chusta na twarzy, latarka czołowa, plakietka pracownika
          i zwój kabla przy pasie (bez żadnych bomb). Biegnie z wyciągniętymi rękami i łapie gracza dotykiem.
          Klatka 40 x 48 px (hitbox 28 x 48)

Animacje (jeden WIERSZ = jedna animacja, klatki od lewej): weak i strong: idle, walk (patrol), run (pościg), alert
(zaskoczony, gdy ktoś dotknie go od tyłu), cuffed (zakuty, siedzi ze zwieszoną głową). boss: idle, run, jump, fall,
grab (łapie gracza).
Na końcu skrypt wypisuje gotowy fragment do wklejenia w SPRITE_SHEETS (src/js/animations.js).

Chcesz zmienić wygląd? Kolory są w słownikach WEAK i STRONG, proporcje w funkcjach draw_weak / draw_strong.
"""

from pathlib import Path

import sys
from PIL import Image

ASSETS = Path(__file__).resolve().parent.parent / "assets"
OUTLINE = (0, 0, 0, 255)

# --- Kolory (R, G, B). Trzy tony na część: jasny (od góry i prawej), bazowy, ciemny (od dołu i lewej) ---
WEAK = {
    "jacket": ((126, 138, 90), (94, 106, 66), (62, 70, 46)),        # oliwkowa kurtka polowa
    "vest": ((140, 108, 74), (106, 78, 52), (70, 50, 36)),          # brązowa kamizelka taktyczna z kieszeniami
    "pants": ((92, 100, 66), (68, 76, 48), (46, 52, 34)),           # spodnie moro
    "camo": (52, 44, 32),                                           # ciemne plamy moro
    "mask": ((70, 72, 66), (44, 46, 42), (28, 30, 28)),             # kominiarka
    "cap": ((92, 102, 64), (66, 74, 46), (44, 50, 32)),             # czapka
    "glove": ((60, 60, 54), (36, 36, 32), (22, 22, 20)),
    "boot": ((62, 54, 46), (36, 32, 28), (22, 20, 18)),
    "belt": ((60, 54, 48), (34, 30, 28), (22, 20, 18)),
    "steel": ((170, 176, 184), (118, 124, 134), (78, 82, 92)),      # łom
    "skin": ((250, 222, 196), (238, 200, 170), (200, 160, 134)),
    "light": (255, 238, 160),    # żółć oświetlonych okien w tle
    "white": (245, 245, 235),
    "pupil": (10, 10, 14),
    "brow": (28, 22, 20),
}

STRONG = {
    "vest": ((128, 92, 110), (96, 64, 82), (62, 40, 54)),
    "under": ((78, 80, 92), (54, 56, 66), (36, 38, 46)),
    "helmet": ((98, 104, 124), (62, 66, 82), (38, 40, 52)),
    "skin": ((236, 196, 168), (214, 168, 140), (176, 132, 112)),
    "boot": ((46, 46, 56), (26, 26, 32), (16, 16, 20)),
    "belt": ((60, 58, 66), (36, 34, 42), (22, 20, 26)),
    "metal": ((196, 200, 210), (140, 146, 160), (92, 96, 110)),
    "glove": ((70, 70, 82), (44, 44, 54), (28, 28, 36)),
    "visor": (14, 14, 20),
    "glow": (255, 112, 84),      # czerwień jak maska gracza
    "glow_dark": (186, 56, 52),
    "white": (245, 245, 235),
    "baton": ((96, 98, 110), (52, 54, 64), (30, 30, 38)),
}


BOSS = {
    "jacket": ((160, 62, 60), (122, 40, 42), (80, 24, 30)),         # bordowa bluza z kapturem (jak strój w scenie z policją)
    "inner": ((72, 70, 78), (46, 44, 52), (30, 28, 36)),            # ciemna koszulka pod spodem
    "pants": ((74, 74, 84), (48, 48, 58), (30, 30, 38)),            # robocze spodnie technika
    "boot": ((60, 56, 56), (34, 30, 30), (20, 18, 18)),
    "glove": ((64, 62, 66), (36, 34, 38), (22, 20, 24)),
    "mask": ((150, 152, 156), (112, 114, 120), (76, 78, 86)),       # szara chusta / maska na twarz
    "skin": ((246, 214, 188), (230, 192, 164), (192, 150, 128)),
    "charge": ((196, 96, 70), (154, 62, 48), (104, 40, 34)),        # ładunki na kamizelce (czerwone laski)
    "strap": ((82, 74, 66), (56, 50, 46), (36, 32, 30)),
    "cable": ((236, 196, 84), (196, 150, 52), (140, 100, 36)),      # zwój żółtego kabla przy pasie (technik z Nordexu)
    "metal": ((196, 200, 210), (140, 146, 160), (92, 96, 110)),
    "led_on": (255, 70, 60),
    "led_off": (120, 34, 34),
    "lamp_dim": (176, 160, 100),
    "lamp": (255, 238, 160),     # latarka czołowa: ta sama żółć, co oświetlone okna w tle
    "white": (245, 245, 235),
    "pupil": (10, 10, 14),
    "tired": (176, 120, 124),
}


class Canvas:
    """Prosta płótno z pikselami RGBA. Wszystkie prymitywy rysują pełne, ostre piksele."""

    def __init__(self, width, height):
        self.w, self.h = width, height
        self.img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        self.px = self.img.load()

    def dot(self, x, y, color):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = (*color[:3], 255)

    def rect(self, x0, y0, x1, y1, color):
        """Wypełnia prostokąt od (x0, y0) do (x1, y1) włącznie."""
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.dot(x, y, color)

    def shaded(self, x0, y0, x1, y1, tones, round_corners=True):
        """Prostokąt z trzema tonami: jasna górna i prawa krawędź, ciemna lewa i dolna. Zaokrąglone rogi."""
        light, base, dark = tones
        self.rect(x0, y0, x1, y1, base)
        self.rect(x0, y0, x1, y0, light)
        self.rect(x1, y0, x1, y1, light)
        self.rect(x0, y1, x1, y1, dark)
        self.rect(x0, y0 + 1, x0, y1, dark)
        if round_corners:
            for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
                self.px[int(cx), int(cy)] = (0, 0, 0, 0)

    def ellipse(self, cx, cy, rx, ry, tones):
        """Elipsa z trzema tonami (światło z góry i z prawej)."""
        light, base, dark = tones
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                nx, ny = (x - cx) / (rx + 0.5), (y - cy) / (ry + 0.5)
                d = nx * nx + ny * ny
                if d <= 1:
                    tone = base
                    if d > 0.55 and (nx + 0 > 0.25 or ny < -0.45):
                        tone = light
                    elif d > 0.55 and (nx < -0.25 or ny > 0.45):
                        tone = dark
                    self.dot(x, y, tone)

    def limb(self, x0, y0, x1, y1, width, tones):
        """Gruba kreska (noga, ręka) od (x0, y0) do (x1, y1)."""
        light, base, dark = tones
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        half = width // 2
        for i in range(int(steps) + 1):
            t = i / steps
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            for k in range(width):
                tone = dark if k == 0 else light if k == width - 1 else base
                self.dot(x - half + k, y, tone)
                if abs(x1 - x0) > abs(y1 - y0):   # kreska bardziej pozioma: grubość w pionie
                    self.dot(x, y - half + k, tone)

    def shear(self, base_y, leaning):
        """Pochyla postać do przodu: im wyżej nad base_y, tym bardziej przesuwa wiersz w prawo."""
        out = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        src, dst = self.px, out.load()
        for y in range(self.h):
            shift = round(max(0, base_y - y) * leaning)
            for x in range(self.w):
                if src[x, y][3] and 0 <= x + shift < self.w:
                    dst[x + shift, y] = src[x, y]
        self.img, self.px = out, out.load()

    def outlined(self):
        """Dodaje czarny kontur (1 px, tylko na zewnątrz) i zwraca gotowy obraz."""
        out = self.img.copy()
        src, dst = self.px, out.load()
        for y in range(self.h):
            for x in range(self.w):
                if src[x, y][3]:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.w and 0 <= ny < self.h and src[nx, ny][3]:
                        dst[x, y] = OUTLINE
                        break
        return out


# =====================================================================================================
#  SŁABY: zradykalizowany członek grupy (bojownik w kominiarce i oliwkowym ubraniu polowym, z łomem).
#  Inspiracja: agent Ground Rebel z CS2 (oliwka, brąz i czerń, kominiarka, kamizelka taktyczna z kieszeniami).
#  To własna, uproszczona postać w stylu gry, a nie kopia modelu z CS2.
#  Klatka 32 x 40, stopy na wierszu 38 (wiersz 39 to kontur), środek ciała x = 14.
# =====================================================================================================
W_W, W_H = 32, 40


def dim(tones, k=0.8):
    return tuple(tuple(int(v * k) for v in t) for t in tones)


def crowbar(c, ex, ey):
    """Łom trzymany w dłoni (ex, ey): trzonek do przodu i zagięty hak na końcu."""
    c.shaded(ex + 1, ey, ex + 6, ey + 1, WEAK["steel"], round_corners=False)
    c.rect(ex + 6, ey + 2, ex + 7, ey + 4, WEAK["steel"][1])           # zagięcie
    c.dot(ex + 6, ey + 4, WEAK["steel"][2])


def draw_weak(pose):
    """Rysuje jedną klatkę bojownika. pose: bob (opuszczenie ciała), legs [(przesunięcie stopy, uniesienie)] x2
    (tylna i przednia noga), back, front (koniec ręki względem barku), lean (pochylenie), eye (wielkość oka)."""
    c = Canvas(W_W, W_H)
    p = {"bob": 0, "legs": [(0, 0), (0, 0)], "back": (-1, 7), "front": (5, 6), "lean": 0.0,
         "head_dx": 0, "head_dy": 0, "eye": 1, **pose}
    cx, b = 14, p["bob"]
    hip = 27 + b

    # nogi: spodnie moro i ciężkie buty (najpierw tylna, ciemniejsza)
    for i, (foot, lift) in enumerate(p["legs"]):
        hx = cx - 3 + i * 4
        ax, ay = hx + foot, 35 - lift
        c.limb(hx, hip, ax, ay, 4, WEAK["pants"] if i else dim(WEAK["pants"]))
        c.dot(hx + foot // 2, (hip + ay) // 2, WEAK["camo"])             # plamy moro
        c.dot(hx + foot // 2 + 1, (hip + ay) // 2 + 2, WEAK["camo"])
        c.shaded(ax - 2, ay, ax + 4, min(38, ay + 3), WEAK["boot"], round_corners=False)
        c.dot(ax + 4, ay + 3 if ay + 3 <= 38 else 38, WEAK["boot"][0])

    # tylna ręka (w cieniu): rękaw kurtki i rękawiczka
    bx, by = cx - 5, 21 + b
    c.limb(bx, by, bx + p["back"][0], by + p["back"][1], 3, dim(WEAK["jacket"]))
    c.shaded(bx + p["back"][0] - 1, by + p["back"][1], bx + p["back"][0] + 1, by + p["back"][1] + 2, WEAK["glove"])

    # tułów: kurtka, na niej kamizelka taktyczna z kieszeniami na magazynki, pas
    c.shaded(cx - 6, 19 + b, cx + 6, 28 + b, WEAK["jacket"])
    c.shaded(cx - 5, 20 + b, cx + 5, 27 + b, WEAK["vest"], round_corners=False)
    for px in (cx - 4, cx - 1, cx + 2):                                 # trzy kieszenie na piersi
        c.shaded(px, 22 + b, px + 2, 25 + b, dim(WEAK["vest"], 0.72), round_corners=False)
        c.rect(px, 22 + b, px + 2, 22 + b, WEAK["vest"][0])
    c.rect(cx - 6, 27 + b, cx + 6, 28 + b, WEAK["belt"][1])
    c.rect(cx + 1, 27 + b, cx + 2, 28 + b, WEAK["steel"][1])            # klamra
    c.rect(cx - 5, 19 + b, cx - 4, 20 + b, WEAK["jacket"][0])           # kołnierz kurtki
    c.rect(cx + 4, 19 + b, cx + 5, 20 + b, WEAK["jacket"][0])

    # głowa: kominiarka (twarz zakryta, widać tylko oczy), na niej czapka
    hx, hy = cx + 1 + p["head_dx"], 12 + b + p["head_dy"]
    c.ellipse(hx, hy, 7.5, 7, WEAK["mask"])
    c.rect(hx - 6, hy + 1, hx - 5, hy + 3, WEAK["mask"][2])             # fałda kominiarki
    eye = p["eye"]
    c.rect(hx + 2, hy - 2, hx + 7, hy + eye + 1, WEAK["skin"][2])       # pasek odsłoniętej skóry wokół oczu
    c.rect(hx + 3, hy - 1, hx + 5, hy + eye, WEAK["white"])             # oko
    c.rect(hx + 4, hy, hx + 5, hy + eye, WEAK["pupil"])
    c.rect(hx + 2, hy - 2, hx + 6, hy - 2, WEAK["brow"])                # zmarszczone brwi: groźny wzrok
    c.dot(hx + 2, hy - 1, WEAK["brow"])
    c.rect(hx + 1, hy + 4, hx + 6, hy + 5, WEAK["mask"][2])             # dół kominiarki (usta zasłonięte)
    c.ellipse(hx - 1, hy - 5, 8, 4, WEAK["cap"])                        # czapka
    c.rect(hx - 8, hy - 4, hx + 7, hy - 3, WEAK["cap"][1])
    c.shaded(hx + 3, hy - 4, hx + 9, hy - 3, WEAK["cap"], round_corners=False)   # daszek
    c.rect(hx - 3, hy - 8, hx - 1, hy - 7, WEAK["cap"][0])

    # przednia ręka: rękaw, rękawiczka i łom
    fx, fy = cx + 4, 21 + b
    ex, ey = fx + p["front"][0], fy + p["front"][1]
    c.limb(fx, fy, ex, ey, 3, WEAK["jacket"])
    c.shaded(ex - 1, ey, ex + 2, ey + 2, WEAK["glove"])
    crowbar(c, ex, ey)

    if p["lean"]:
        c.shear(34, p["lean"])
    return c.outlined()


def weak_cuffed():
    """Zakuty: siedzi na ziemi ze zwieszoną głową, ręce z tyłu w kajdankach, łom leży obok."""
    c = Canvas(W_W, W_H)
    cx = 13
    c.limb(cx - 6, 35, cx + 6, 35, 4, WEAK["pants"])                     # nogi wyciągnięte do przodu
    c.dot(cx - 1, 34, WEAK["camo"])
    c.dot(cx + 2, 36, WEAK["camo"])
    c.shaded(cx + 6, 33, cx + 11, 37, WEAK["boot"], round_corners=False)
    c.shaded(cx - 7, 24, cx + 5, 36, WEAK["jacket"])                     # tułów pochylony
    c.shaded(cx - 6, 25, cx + 4, 33, WEAK["vest"], round_corners=False)
    for px in (cx - 5, cx - 2, cx + 1):
        c.shaded(px, 27, px + 2, 29, dim(WEAK["vest"], 0.72), round_corners=False)
    c.rect(cx - 7, 33, cx + 5, 34, WEAK["belt"][1])
    c.rect(cx - 9, 28, cx - 7, 34, WEAK["jacket"][2])                    # ręce za plecami
    c.rect(cx - 10, 31, cx - 8, 32, (200, 204, 212))                     # kajdanki
    c.rect(cx - 10, 33, cx - 8, 33, WEAK["steel"][2])
    c.ellipse(cx + 3, 18, 7.5, 6.5, WEAK["mask"])                        # głowa opuszczona
    c.rect(cx + 4, 17, cx + 8, 18, WEAK["skin"][2])                      # pasek skóry wokół oczu
    c.rect(cx + 5, 17, cx + 7, 17, WEAK["pupil"])                        # zamknięte oko
    c.ellipse(cx + 1, 13, 8, 4.5, WEAK["cap"])                           # czapka zsunięta na oczy
    c.shaded(cx + 5, 15, cx + 13, 16, WEAK["cap"], round_corners=False)
    c.shaded(cx + 8, 35, cx + 15, 36, WEAK["steel"], round_corners=False)   # łom upuszczony na ziemię
    return c.outlined()


# =====================================================================================================
#  SILNY: ochroniarz. Klatka 44 x 52, stopy na wierszu 50 (wiersz 51 to kontur), środek ciała x = 18.
# =====================================================================================================
S_W, S_H = 44, 52


def draw_strong(pose):
    """Rysuje jedną klatkę ochroniarza (parametry jak w draw_weak, ręka z pałką zamiast latarki)."""
    c = Canvas(S_W, S_H)
    p = {"bob": 0, "legs": [(0, 0), (0, 0)], "back": (-1, 10), "front": (4, 8), "lean": 0.0,
         "head_dx": 0, "head_dy": 0, "baton": "down", **pose}
    cx, b = 18, p["bob"]
    hip = 38 + b

    for i, (foot, lift) in enumerate(p["legs"]):
        hx = cx - 4 + i * 7
        ax, ay = hx + foot, 46 - lift
        tones = STRONG["under"] if i else tuple(tuple(int(v * 0.8) for v in t) for t in STRONG["under"])
        c.limb(hx, hip, ax, ay, 6, tones)
        c.shaded(ax - 3, ay, ax + 5, min(50, ay + 4), STRONG["boot"], round_corners=False)
        c.rect(ax + 5, min(50, ay + 3), ax + 6, min(50, ay + 4), STRONG["boot"][0])

    # tylna ręka
    bx, by = cx - 10, 27 + b
    back_tones = tuple(tuple(int(v * 0.8) for v in t) for t in STRONG["under"])
    c.limb(bx, by, bx + p["back"][0], by + p["back"][1], 5, back_tones)
    c.shaded(bx + p["back"][0] - 2, by + p["back"][1], bx + p["back"][0] + 2, by + p["back"][1] + 4, STRONG["glove"])

    # tułów: koszulka + kamizelka kuloodporna
    c.shaded(cx - 10, 26 + b, cx + 10, 39 + b, STRONG["under"])
    c.shaded(cx - 9, 27 + b, cx + 9, 36 + b, STRONG["vest"])
    c.rect(cx - 1, 27 + b, cx + 1, 36 + b, STRONG["vest"][2])            # zapięcie kamizelki
    c.rect(cx + 3, 30 + b, cx + 7, 31 + b, STRONG["glow"])               # czerwony pasek (akcent)
    c.rect(cx + 3, 32 + b, cx + 7, 32 + b, STRONG["glow_dark"])
    c.rect(cx - 7, 30 + b, cx - 4, 34 + b, STRONG["vest"][2])            # kieszeń na magazynki
    c.rect(cx - 10, 37 + b, cx + 10, 39 + b, STRONG["belt"][1])          # pas
    c.rect(cx + 2, 37 + b, cx + 4, 39 + b, STRONG["metal"][0])

    # głowa w hełmie z wizjerem
    hx, hy = cx + 2 + p["head_dx"], 15 + b + p["head_dy"]
    c.rect(hx - 5, hy + 5, hx + 5, hy + 9, STRONG["under"][1])           # szyja / kołnierz
    c.ellipse(hx, hy, 9.5, 8.5, STRONG["helmet"])
    c.rect(hx - 9, hy + 2, hx - 7, hy + 7, STRONG["helmet"][2])          # tył hełmu
    c.rect(hx + 1, hy - 1, hx + 9, hy + 4, STRONG["visor"])              # wizjer
    c.rect(hx + 4, hy + 1, hx + 8, hy + 2, STRONG["glow"])              # świecące oko
    c.rect(hx + 4, hy + 2, hx + 8, hy + 2, STRONG["glow_dark"])
    c.rect(hx + 2, hy + 5, hx + 8, hy + 7, STRONG["skin"][1])            # podbródek
    c.rect(hx + 2, hy + 7, hx + 8, hy + 7, STRONG["skin"][2])
    c.rect(hx - 2, hy - 7, hx + 2, hy - 7, STRONG["helmet"][0])          # błysk na hełmie

    # naramienniki
    c.shaded(cx - 13, 25 + b, cx - 7, 31 + b, STRONG["vest"])
    c.shaded(cx + 6, 25 + b, cx + 13, 32 + b, STRONG["vest"])
    c.rect(cx + 8, 27 + b, cx + 11, 27 + b, STRONG["glow"])

    # przednia ręka z pałką
    fx, fy = cx + 11, 28 + b
    ex, ey = fx + p["front"][0], fy + p["front"][1]
    c.limb(fx, fy, ex, ey, 5, STRONG["under"])
    c.shaded(ex - 2, ey, ex + 2, ey + 4, STRONG["glove"])
    if p["baton"] == "down":
        c.shaded(ex + 2, ey - 2, ex + 4, ey + 11, STRONG["baton"], round_corners=False)
    else:   # uniesiona do ataku
        c.shaded(ex - 1, ey - 12, ex + 1, ey + 1, STRONG["baton"], round_corners=False)

    if p["lean"]:
        c.shear(46, p["lean"])
    return c.outlined()


def strong_cuffed():
    c = Canvas(S_W, S_H)
    cx = 17
    c.limb(cx - 8, 46, cx + 8, 46, 6, STRONG["under"])
    c.shaded(cx + 8, 43, cx + 15, 49, STRONG["boot"], round_corners=False)
    c.shaded(cx - 10, 30, cx + 7, 47, STRONG["under"])
    c.shaded(cx - 9, 31, cx + 6, 42, STRONG["vest"])
    c.rect(cx - 10, 43, cx + 7, 45, STRONG["belt"][1])
    c.rect(cx - 13, 36, cx - 10, 44, STRONG["under"][2])                 # ręce za plecami
    c.rect(cx - 14, 40, cx - 11, 41, STRONG["metal"][0])                 # kajdanki
    c.rect(cx - 14, 42, cx - 11, 42, STRONG["metal"][2])
    c.ellipse(cx + 5, 24, 9.5, 8, STRONG["helmet"])                      # hełm zwieszony
    c.rect(cx + 6, 25, cx + 14, 28, STRONG["visor"])
    c.rect(cx + 8, 26, cx + 12, 26, STRONG["glow_dark"])                 # przygaszone oko
    c.rect(cx + 6, 29, cx + 12, 30, STRONG["skin"][1])
    c.shaded(cx - 14, 31, cx - 8, 36, STRONG["vest"])
    return c.outlined()


# =====================================================================================================
#  ANIMACJE
# =====================================================================================================
def weak_animations():
    idle = [draw_weak({"bob": 0, "front": (4, 7)}), draw_weak({"bob": 1, "front": (4, 8), "legs": [(0, 0), (0, 0)]})]
    walk_legs = [((-3, 0), (3, 0)), ((-1, 0), (1, 1)), ((3, 0), (-3, 0)), ((1, 1), (-1, 0))]
    walk = [draw_weak({"bob": 1 if i % 2 == 0 else 0, "legs": list(legs), "back": (-1 + (i < 2) * 2 - 1, 8),
                       "front": (4, 7)}) for i, legs in enumerate(walk_legs)]
    run_legs = [((-5, 1), (5, 0)), ((0, 3), (1, 2)), ((5, 0), (-5, 1)), ((1, 2), (0, 3))]
    run = [draw_weak({"bob": 1 if i % 2 == 0 else 0, "legs": list(legs), "lean": 0.07,
                      "back": (-5 if i < 2 else 3, 5), "front": (5 if i < 2 else -3, 4)}) for i, legs in enumerate(run_legs)]
    alert = [draw_weak({"bob": 0, "front": (3, -3), "back": (-2, 7), "legs": [(-1, 0), (2, 0)], "eye": 2, "head_dx": -1}),
             draw_weak({"bob": 0, "front": (3, -4), "back": (-2, 7), "legs": [(-1, 0), (2, 0)], "eye": 2, "head_dx": -1,
                        "head_dy": -1})]
    return [("idle", idle, 3, True), ("walk", walk, 6, True), ("run", run, 10, True),
            ("alert", alert, 6, True), ("cuffed", [weak_cuffed()], 1, False)]


def strong_animations():
    idle = [draw_strong({"bob": 0}), draw_strong({"bob": 1, "front": (4, 9)})]
    walk_legs = [((-3, 0), (3, 0)), ((-1, 0), (1, 1)), ((3, 0), (-3, 0)), ((1, 1), (-1, 0))]
    walk = [draw_strong({"bob": 1 if i % 2 == 0 else 0, "legs": list(legs), "front": (4, 8)}) for i, legs in enumerate(walk_legs)]
    run_legs = [((-6, 1), (6, 0)), ((0, 3), (1, 2)), ((6, 0), (-6, 1)), ((1, 2), (0, 3))]
    run = [draw_strong({"bob": 1 if i % 2 == 0 else 0, "legs": list(legs), "lean": 0.07, "baton": "up",
                        "front": (7, 2), "back": (-6 if i < 2 else 3, 8)}) for i, legs in enumerate(run_legs)]
    alert = [draw_strong({"baton": "up", "front": (6, 0), "legs": [(-1, 0), (3, 0)], "head_dx": -1}),
             draw_strong({"baton": "up", "front": (6, -1), "legs": [(-1, 0), (3, 0)], "head_dx": -1, "head_dy": -1})]
    return [("idle", idle, 2, True), ("walk", walk, 5, True), ("run", run, 8, True),
            ("alert", alert, 6, True), ("cuffed", [strong_cuffed()], 1, False)]


# =====================================================================================================
#  BOSS: Kamil. Były technik z Nordexu, który został "ostatnim zabezpieczeniem": bordowa bluza z kapturem, chusta
#  na twarzy, latarka czołowa, plakietka pracownika i zwój kabla przy pasie (bez żadnych ładunków).
#  Nie wybucha: biegnie z wyciągniętymi rękami i łapie gracza dotykiem. Klatka 40 x 48 (hitbox 28 x 48),
#  stopy na wierszu 46 (wiersz 47 to kontur), środek ciała x = 18 (po prawej zostaje miejsce na wyciągnięte ręce).
# =====================================================================================================
B_W, B_H = 40, 48


def draw_boss(pose):
    """Rysuje jedną klatkę bossa. pose: bob, legs [(przesunięcie stopy, uniesienie)] x2 (tylna, przednia),
    back, front (koniec ręki względem barku), lean (pochylenie), led (dioda świeci), eye, head_dx / head_dy."""
    c = Canvas(B_W, B_H)
    p = {"bob": 0, "legs": [(0, 0), (0, 0)], "back": (2, 10), "front": (3, 11), "lean": 0.0, "led": True,
         "eye": 1, "head_dx": 0, "head_dy": 0, **pose}
    cx, b = 18, p["bob"]
    hip = 36 + b

    # nogi: spodnie robocze, ciężkie buty (najpierw tylna, ciemniejsza)
    for i, (foot, lift) in enumerate(p["legs"]):
        hx = cx - 3 + i * 6
        ax, ay = hx + foot, 42 - lift
        c.limb(hx, hip, ax, ay, 5, BOSS["pants"] if i else dim(BOSS["pants"]))
        c.shaded(ax - 3, ay, ax + 4, min(46, ay + 4), BOSS["boot"], round_corners=False)
        c.rect(ax + 4, min(46, ay + 3), ax + 5, min(46, ay + 4), BOSS["boot"][0])

    # tylna ręka (w cieniu): rękaw i dłoń z palcami
    bx, by = cx + 1, 26 + b
    ex, ey = bx + p["back"][0], by + p["back"][1]
    c.limb(bx, by, ex, ey, 4, dim(BOSS["jacket"]))
    c.shaded(ex - 1, ey, ex + 3, ey + 3, BOSS["glove"])

    # tułów: bluza z kapturem (kieszeń kangurka, sznurki, plakietka pracownika), pas z kablem. Bez żadnych ładunków.
    c.shaded(cx - 8, 23 + b, cx + 8, 37 + b, BOSS["jacket"])
    c.shaded(cx - 5, 31 + b, cx + 6, 35 + b, (BOSS["jacket"][1], BOSS["jacket"][1], BOSS["jacket"][2]), round_corners=False)  # kieszeń kangurka
    c.rect(cx - 5, 31 + b, cx + 6, 31 + b, BOSS["jacket"][2])                                # szew kieszeni
    c.rect(cx - 5, 31 + b, cx - 5, 35 + b, BOSS["jacket"][2])
    c.rect(cx + 6, 31 + b, cx + 6, 35 + b, BOSS["jacket"][2])
    c.rect(cx + 1, 24 + b, cx + 1, 29 + b, BOSS["white"])                                    # sznurki kaptura
    c.rect(cx + 4, 24 + b, cx + 4, 28 + b, BOSS["white"])
    c.dot(cx + 1, 30 + b, BOSS["mask"][1])
    c.dot(cx + 4, 29 + b, BOSS["mask"][1])
    c.shaded(cx - 7, 26 + b, cx - 3, 29 + b, (BOSS["white"], (214, 214, 204), (150, 150, 146)), round_corners=False)             # plakietka pracownika na smyczy
    c.rect(cx - 6, 27 + b, cx - 4, 27 + b, BOSS["inner"][1])
    c.rect(cx - 6, 28 + b, cx - 5, 28 + b, BOSS["inner"][2])
    c.shaded(cx - 8, 35 + b, cx + 8, 37 + b, BOSS["inner"], round_corners=False)            # pas
    c.shaded(cx - 7, 34 + b, cx - 3, 38 + b, BOSS["cable"], round_corners=False)            # zwój żółtego kabla (technik)
    c.rect(cx - 6, 35 + b, cx - 4, 35 + b, BOSS["cable"][2])
    c.rect(cx + 2, 35 + b, cx + 4, 37 + b, BOSS["metal"][1])                                 # klamra

    # głowa: kaptur, chusta na dole twarzy, zmęczone oczy, latarka czołowa
    hx, hy = cx + 1 + p["head_dx"], 13 + b + p["head_dy"]
    c.ellipse(hx - 1, hy, 9.5, 9, BOSS["jacket"])                                            # kaptur
    c.rect(hx - 10, hy + 2, hx - 7, hy + 8, BOSS["jacket"][2])                               # tył kaptura
    c.rect(hx + 2, hy - 3, hx + 9, hy + 4, BOSS["skin"][1])                                  # odsłonięta twarz
    c.rect(hx + 2, hy - 3, hx + 9, hy - 3, BOSS["skin"][2])                                  # cień pod kapturem
    eye = p["eye"]
    c.rect(hx + 4, hy - 1, hx + 8, hy + eye, BOSS["white"])                                  # oko
    c.rect(hx + 6, hy, hx + 8, hy + eye, BOSS["pupil"])
    c.rect(hx + 4, hy - 2, hx + 8, hy - 2, BOSS["pupil"])                                    # ciężka brew
    c.rect(hx + 4, hy + eye + 1, hx + 8, hy + eye + 1, BOSS["tired"])                       # cień pod okiem
    c.shaded(hx + 1, hy + 4, hx + 9, hy + 9, BOSS["mask"], round_corners=False)             # chusta na twarzy
    c.rect(hx + 3, hy + 6, hx + 7, hy + 6, BOSS["mask"][2])
    c.shaded(hx + 5, hy - 7, hx + 8, hy - 5, BOSS["metal"], round_corners=False)            # latarka czołowa
    c.rect(hx + 8, hy - 6, hx + 9, hy - 5, BOSS["lamp"] if p["led"] else BOSS["lamp_dim"])
    if p["led"]:
        c.dot(hx + 10, hy - 6, (255, 250, 210))

    # przednia ręka wyciągnięta po gracza: rękaw i rękawica z palcami
    fx, fy = cx + 6, 25 + b
    ex, ey = fx + p["front"][0], fy + p["front"][1]
    c.limb(fx, fy, ex, ey, 4, BOSS["jacket"])
    c.shaded(ex - 1, ey - 1, ex + 3, ey + 3, BOSS["glove"])
    for dy in (-1, 1, 3):                                                                    # palce
        c.rect(ex + 3, ey + dy, ex + 4, ey + dy, BOSS["glove"][1])

    if p["lean"]:
        c.shear(44, p["lean"])
    return c.outlined()


def boss_animations():
    idle = [draw_boss({"bob": 0, "front": (1, 11), "back": (0, 11), "led": True}),
            draw_boss({"bob": 1, "front": (1, 12), "back": (0, 12), "led": False})]
    run_legs = [((-6, 1), (6, 0)), ((0, 3), (1, 2)), ((6, 0), (-6, 1)), ((1, 2), (0, 3))]
    run = [draw_boss({"bob": 1 if i % 2 == 0 else 0, "legs": list(legs), "lean": 0.08, "led": i % 2 == 0,
                      "front": (8, 2 if i < 2 else 0), "back": (10, 5 if i < 2 else 7), "head_dx": 1}) for i, legs in enumerate(run_legs)]
    jump = [draw_boss({"legs": [(-2, -1), (3, 3)], "front": (8, -3), "back": (9, -1), "lean": 0.06, "led": True}),
            draw_boss({"legs": [(-3, 1), (4, 5)], "front": (9, -5), "back": (10, -3), "lean": 0.06, "led": False})]
    fall = [draw_boss({"legs": [(-4, 0), (4, 0)], "front": (8, -1), "back": (8, -4), "led": True}),
            draw_boss({"legs": [(-5, 0), (5, 1)], "front": (9, 1), "back": (9, -2), "led": False})]
    grab = [draw_boss({"legs": [(-3, 0), (4, 0)], "front": (11, 0), "back": (12, 4), "lean": 0.10, "led": True, "head_dx": 1, "eye": 2}),
            draw_boss({"legs": [(-3, 0), (4, 0)], "front": (12, 1), "back": (13, 5), "lean": 0.12, "led": False, "head_dx": 2, "eye": 2})]
    return [("idle", idle, 3, True), ("run", run, 10, True), ("jump", jump, 8, False),
            ("fall", fall, 8, True), ("grab", grab, 8, True)]


def write_sheet(name, frame_w, frame_h, animations):
    columns = max(len(frames) for _, frames, _, _ in animations)
    sheet = Image.new("RGBA", (columns * frame_w, len(animations) * frame_h), (0, 0, 0, 0))
    for row, (_, frames, _, _) in enumerate(animations):
        for col, frame in enumerate(frames):
            sheet.paste(frame, (col * frame_w, row * frame_h))
    path = ASSETS / f"{name}.png"
    sheet.save(path)
    print(f"zapisano {path.relative_to(ASSETS.parent)} ({sheet.width}x{sheet.height} px)")
    print(f"    {name.replace('_sheet', '').replace('enemy_', '')}: {{")
    print(f'        src: "assets/{name}.png",\n        frameWidth: {frame_w},\n        frameHeight: {frame_h},\n        animations: {{')
    for row, (anim, frames, fps, loop) in enumerate(animations):
        extra = "" if loop else ", loop: false"
        print(f"            {anim + ':':8} {{ row: {row}, frames: {len(frames)}, fps: {fps}{extra} }},")
    print("        },\n    },\n")
    return sheet


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None          # np.: python "Make enemy sheets.py" boss
    if only in (None, "weak"):
        write_sheet("enemy_weak_sheet", W_W, W_H, weak_animations())
    if only in (None, "strong"):
        write_sheet("enemy_strong_sheet", S_W, S_H, strong_animations())
    if only in (None, "boss"):
        write_sheet("enemy_boss_sheet", B_W, B_H, boss_animations())


if __name__ == "__main__":
    main()