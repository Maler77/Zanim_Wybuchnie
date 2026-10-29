"""Rysuje grafiki bomby (dynamit z zegarem) i okna rozbrajania z trzema kablami.

Uruchom z głównego katalogu repozytorium:   python tools/make_bomb_art.py
(wymaga biblioteki Pillow:  pip install pillow)

Powstają pliki w assets/:
  bomb.png, bomb_defused.png        bomba w świecie gry: pęk dynamitu z płytką i wyświetlaczem zegara.
                                    Cyfry odliczania rysuje game.js na wyświetlaczu (współrzędne wypisuje skrypt).
  panel.png, panel_defused.png      panel na mapie (poziomy "panel" i "boss"): terminal z ekranem i klawiaturą.
  bomb_ui_*.png                     elementy okna rozbrajania (płytka, laska dynamitu, nadajnik, terminale, kable, iskra);
                                    okno składa się z nich w src/css/style.css, a kable przecina main.js.

Styl jak reszta gry: czarny kontur 1 px, trzy tony cieniowania, przygaszone kolory, jaskrawy akcent
(czerwień diody jak maska gracza, żółć jak oświetlone okna w tle).
Chcesz zmienić wygląd? Kolory są w słownikach na górze, kształty w funkcjach draw_*.
"""

import math
from pathlib import Path

from PIL import Image

ASSETS = Path(__file__).resolve().parent.parent / "assets"
OUTLINE = (0, 0, 0, 255)

# --- Kolory (R, G, B): jasny (od góry), bazowy, ciemny (od dołu) ---
DYN = ((228, 112, 90), (188, 70, 58), (128, 42, 46))          # laska dynamitu
DYN_CAP = ((242, 164, 132), (220, 120, 96), (166, 74, 64))    # papierowy denek laski
STRAP = ((86, 86, 98), (40, 40, 48), (20, 20, 26))            # czarna taśma
PCB = ((108, 200, 124), (58, 142, 86), (34, 94, 62))          # płytka drukowana
TRACE = (142, 224, 154)                                       # ścieżki na płytce
GOLD = ((255, 232, 140), (232, 188, 76), (160, 118, 40))      # mosiądz (śruby, terminale)
STEEL = ((206, 212, 222), (146, 152, 166), (92, 96, 112))     # stal (denko spłonki, śruby)
RED = ((255, 120, 104), (224, 62, 62), (150, 32, 42))
YELLOW = ((255, 240, 130), (242, 198, 62), (170, 130, 30))
BLUE = ((140, 198, 255), (74, 134, 232), (42, 84, 164))
BLACK_WIRE = ((100, 100, 112), (46, 46, 54), (24, 24, 30))
COPPER = ((255, 190, 120), (222, 140, 70), (150, 86, 44))
WIRES = {"red": RED, "yellow": YELLOW, "blue": BLUE}
PANEL = ((124, 148, 178), (78, 100, 130), (46, 60, 84))        # obudowa panelu (stal z niebieskim odcieniem)
PANEL_DARK = ((72, 88, 114), (40, 50, 70), (24, 30, 44))       # nadajnik
SCR_BLUE = (46, 112, 150)                                      # ekran panelu (jak w zastępczym rysunku z game.js)
SCR_BLUE_LIGHT = (66, 138, 178)
SCR_GREEN = (30, 150, 100)
SCR_GREEN_LIGHT = (60, 190, 134)
ICON = (206, 234, 248)
LED_ON = (255, 70, 60)
LED_OFF = (96, 30, 32)
LED_OK = (90, 235, 150)
SCREEN = (22, 12, 14)
SCREEN_EDGE = (58, 40, 44)
INK = (122, 40, 46)    # farba nadruku "TNT" na lasce


class Canvas:
    """Płótno z pikselami RGBA. Wszystkie prymitywy rysują pełne, ostre piksele."""

    def __init__(self, width, height):
        self.w, self.h = width, height
        self.img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        self.px = self.img.load()

    def dot(self, x, y, color):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = (*color[:3], 255)

    def clear(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = (0, 0, 0, 0)

    def rect(self, x0, y0, x1, y1, color):
        """Wypełnia prostokąt od (x0, y0) do (x1, y1) włącznie."""
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.dot(x, y, color)

    def shaded(self, x0, y0, x1, y1, tones, round_corners=True):
        """Prostokąt z trzema tonami: jasna górna i prawa krawędź, ciemna lewa i dolna."""
        light, base, dark = tones
        self.rect(x0, y0, x1, y1, base)
        self.rect(x0, y0, x1, y0, light)
        self.rect(x1, y0, x1, y1, light)
        self.rect(x0, y1, x1, y1, dark)
        self.rect(x0, y0 + 1, x0, y1, dark)
        if round_corners:
            for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
                self.clear(int(cx), int(cy))

    def line(self, x0, y0, x1, y1, color):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(int(steps) + 1):
            t = i / steps
            self.dot(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, color)

    def disc(self, cx, cy, r, tones):
        """Koło z trzema tonami (światło z góry i z prawej)."""
        light, base, dark = tones
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                nx, ny = (x - cx) / (r + 0.5), (y - cy) / (r + 0.5)
                d = nx * nx + ny * ny
                if d <= 1:
                    tone = base
                    if d > 0.4 and (nx > 0.3 or ny < -0.5):
                        tone = light
                    elif d > 0.4 and (nx < -0.3 or ny > 0.5):
                        tone = dark
                    self.dot(x, y, tone)

    def glyphs(self, x, y, text, color):
        """Napis czcionką 3 x 5 px."""
        for ch in text:
            for gy, row in enumerate(FONT[ch]):
                for gx, bit in enumerate(row):
                    if bit == "#":
                        self.dot(x + gx, y + gy, color)
            x += len(FONT[ch][0]) + 1

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


FONT = {
    "T": ("###", ".#.", ".#.", ".#.", ".#."),
    "N": ("#..#", "##.#", "#.##", "#..#", "#..#"),
    "-": ("...", "...", "###", "...", "..."),
    "X": ("#.#", "#.#", ".#.", "#.#", "#.#"),
}


def crop(img):
    """Przycina obraz do widocznych pikseli i zwraca (obraz, (x, y) lewego górnego rogu w starym obrazie)."""
    box = img.getbbox()
    return img.crop(box), (box[0], box[1])


def save(img, name):
    path = ASSETS / name
    img.save(path)
    print(f"zapisano {path.relative_to(ASSETS.parent)} ({img.width}x{img.height} px)")


# =====================================================================================================
#  BOMBA W ŚWIECIE: poziomy pęk dynamitu (3 laski), dwie czarne taśmy, płytka z zegarem, pętle kabli.
#  game.js rysuje na wyświetlaczu cyfry odliczania (DISPLAY niżej).
# =====================================================================================================
BW, BH = 54, 34
STICK_Y = (8, 15, 22)       # górny wiersz każdej laski (każda ma 7 px wysokości)
STICK_X0, STICK_X1 = 2, 51
STRAP_X = ((8, 11), (43, 46))
PCB_BOX = (15, 10, 39, 28)  # x0, y0, x1, y1 płytki
DISPLAY = (17, 14, 37, 22)  # ramka wyświetlacza (x0, y0, x1, y1); cyfry w środku, cyfry 3 x 5 px
# Układ cyfr MM:SS na wyświetlaczu: przesunięcia (px) od lewej krawędzi wnętrza ramki (4 cyfry i dwukropek).
DIGIT_OFFSETS = (1, 5, 11, 15)
COLON_OFFSET = 9


def draw_stick(c, y):
    """Pozioma laska dynamitu (7 px wysokości): jasny grzbiet, ciemny spód i jasne papierowe denko z prawej."""
    light, base, dark = DYN
    c.rect(STICK_X0, y, STICK_X1, y + 6, base)
    c.rect(STICK_X0, y, STICK_X1, y, light)
    c.rect(STICK_X0, y + 1, STICK_X1, y + 1, light)
    c.rect(STICK_X0, y + 5, STICK_X1, y + 5, dark)
    c.rect(STICK_X0, y + 6, STICK_X1, y + 6, dark)
    for dx in (STICK_X0, STICK_X1):          # zaokrąglone końce
        c.clear(dx, y)
        c.clear(dx, y + 6)
    cl, cb, cd = DYN_CAP                      # denko: dwa jasne piksele i ciemna linia przed nim
    c.rect(STICK_X1 - 2, y, STICK_X1, y + 6, cb)
    c.rect(STICK_X1 - 2, y, STICK_X1, y + 1, cl)
    c.rect(STICK_X1 - 2, y + 5, STICK_X1, y + 6, cd)
    c.clear(STICK_X1, y)
    c.clear(STICK_X1, y + 6)
    c.rect(STICK_X1 - 3, y + 1, STICK_X1 - 3, y + 5, dark)
    for dx in (13, 22, 29, 36):               # kilka ciemniejszych kropek: papier
        c.dot(dx + (y % 3), y + 3, dark)


def draw_strap(c, x0, x1):
    light, base, dark = STRAP
    c.rect(x0, STICK_Y[0] - 1, x1, STICK_Y[2] + 7, base)
    c.rect(x0, STICK_Y[0] - 1, x0, STICK_Y[2] + 7, light)
    c.rect(x1, STICK_Y[0] - 1, x1, STICK_Y[2] + 7, dark)


def draw_pcb(c, defused):
    x0, y0, x1, y1 = PCB_BOX
    c.shaded(x0, y0, x1, y1, PCB)
    # ścieżki i luty
    for tx in (x0 + 3, x0 + 8, x1 - 5):
        c.dot(tx, y0 + 1, TRACE)
    c.line(x0 + 2, y1 - 2, x0 + 7, y1 - 2, TRACE)
    c.line(x1 - 9, y1 - 2, x1 - 6, y1 - 2, TRACE)
    for sx, sy in ((x0 + 1, y0 + 1), (x1 - 1, y0 + 1), (x0 + 1, y1 - 1), (x1 - 1, y1 - 1)):
        c.dot(sx, sy, STEEL[0])
    # wyświetlacz
    dx0, dy0, dx1, dy1 = DISPLAY
    c.rect(dx0, dy0, dx1, dy1, SCREEN_EDGE)
    c.rect(dx0 + 1, dy0 + 1, dx1 - 1, dy1 - 1, SCREEN)
    if defused:                               # po rozbrojeniu zielone kreski zamiast cyfr
        for off in DIGIT_OFFSETS:
            c.glyphs(dx0 + 1 + off, dy0 + 2, "-", LED_OK)
        c.dot(dx0 + 1 + COLON_OFFSET, dy0 + 3, LED_OK)
        c.dot(dx0 + 1 + COLON_OFFSET, dy0 + 5, LED_OK)
    # układ scalony, kondensator, cewka
    c.rect(x0 + 3, y1 - 4, x0 + 6, y1 - 3, (24, 24, 30))
    c.dot(x0 + 3, y1 - 4, STEEL[1])
    c.disc(x1 - 4, y1 - 3, 2, COPPER)
    c.dot(x1 - 4, y1 - 3, (60, 30, 20))
    c.rect(x0 + 9, y1 - 3, x0 + 11, y1 - 3, BLUE[1])
    # dioda statusu (miga w grze nie, jest stała)
    c.dot(x1 - 1, y0 + 4, LED_OK if defused else LED_ON)
    # brzęczyk: czarny krążek wystający nad płytką z lewej
    c.disc(x0 + 3, y0 - 1, 3, ((70, 70, 80), (30, 30, 36), (14, 14, 18)))
    c.dot(x0 + 3, y0 - 1, STEEL[2])


def draw_world_wires(c, defused):
    """Trzy kable (czerwony, żółty, niebieski) wychodzą z płytki, robią pętle nad pękiem i wbijają się w górną laskę.
    Po rozbrojeniu każdy jest przecięty: końcówki wiszą osobno."""
    plan = (
        ("red", 24, 4, 14),
        ("yellow", 28, 2, 9),
        ("blue", 32, 0, 4),
    )
    for name, sx, top, ex_ in plan:
        color = WIRES[name]
        pts = [(sx, PCB_BOX[1]), (sx, top + 1), (sx - 1, top), (ex_ + 1, top), (ex_, top + 1), (ex_, STICK_Y[0])]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            c.line(ax, ay, bx, by, color[1])
        # jasny grzbiet na poziomych odcinkach
        for x in range(ex_ + 2, sx - 1):
            c.dot(x, top, color[0])
        if defused:                            # przecięcie: dziura w poziomym odcinku i miedziane końcówki
            gap = (ex_ + sx) // 2
            for x in range(gap - 1, gap + 2):
                c.clear(x, top)
            c.dot(gap - 2, top, COPPER[1])
            c.dot(gap + 2, top, COPPER[1])
            c.dot(gap - 2, top + 1, color[2])
            c.dot(gap + 2, top + 1, color[2])


def draw_world_extras(c):
    """Czarny kabel w pętli po prawej stronie i żółto-czarna para na dole (jak na zdjęciu referencyjnym)."""
    bl = BLACK_WIRE
    x = PCB_BOX[2]
    for pts in (
        [(x, 18), (x + 2, 18), (x + 3, 17), (x + 3, 13), (x + 4, 12), (STICK_X1 + 1, 12)],
        [(x, 21), (x + 2, 21), (x + 3, 22), (x + 3, 28), (x + 4, 29), (STICK_X1 + 1, 29)],
    ):
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            c.line(ax, ay, bx, by, bl[1])
    # żółto-czarna para zwisająca pod pękiem
    for dx, color in ((0, YELLOW[1]), (2, bl[1])):
        c.line(20 + dx, PCB_BOX[3] + 1, 20 + dx, BH - 3, color)
    c.dot(20, BH - 2, COPPER[1])
    c.dot(22, BH - 2, COPPER[1])


def draw_world_bomb(defused):
    c = Canvas(BW, BH)
    for y in STICK_Y:
        draw_stick(c, y)
    for x0, x1 in STRAP_X:
        draw_strap(c, x0, x1)
    draw_world_wires(c, defused)
    draw_world_extras(c)
    draw_pcb(c, defused)
    return c.outlined()


def make_world_bomb():
    live = draw_world_bomb(False)
    done = draw_world_bomb(True)
    # oba obrazki muszą mieć identyczny rozmiar i przesunięcie, więc przycinamy oba tym samym prostokątem
    box = tuple(
        f(a, b) for f, a, b in zip((min, min, max, max), live.getbbox(), done.getbbox())
    )
    live, done = live.crop(box), done.crop(box)
    save(live, "bomb.png")
    save(done, "bomb_defused.png")
    dx0, dy0, dx1, dy1 = DISPLAY
    ox, oy = box[0], box[1]
    display = (dx0 + 1 - ox, dy0 + 1 - oy, dx1 - dx0 - 1, dy1 - dy0 - 1)
    print(f"    wyświetlacz w bomb.png: x={display[0]} y={display[1]} w={display[2]} h={display[3]}; "
          f"cyfry 3x5 px na przesunięciach {DIGIT_OFFSETS}, dwukropek {COLON_OFFSET}, pion +1 (patrz BOMB_DISPLAY w game.js)")
    return live, done, display


# =====================================================================================================
#  OKNO ROZBRAJANIA: bomba z bliska. Po lewej płytka z zegarem, po prawej trzy laski dynamitu, między nimi
#  trzy kable (czerwony, żółty, niebieski), a każdy kabel przechodzi przez jedną odpowiedź.
#  Elementy są małe i skalowane w CSS (zmienna --px, 1 piksel obrazka = --px pikseli ekranu).
#  Obrazki z "9-slice" (pcb, stick, display) CSS rozciąga ramką border-image: rogi i krawędzie zostają ostre.
# =====================================================================================================
def make_pcb_frame():
    """Rama płytki 12 x 12 (krawędź 4 px): kontur, jasna górna i lewa krawędź, ciemny spód, ciemniejszy rant."""
    light, base, dark = PCB
    c = Canvas(12, 12)
    c.rect(0, 0, 11, 11, OUTLINE[:3])
    c.rect(1, 1, 10, 10, base)
    c.rect(1, 1, 10, 1, light)
    c.rect(1, 1, 1, 10, light)
    c.rect(1, 10, 10, 10, dark)
    c.rect(10, 1, 10, 10, dark)
    c.rect(2, 2, 9, 9, base)
    for dx, dy in ((0, 0), (11, 0), (0, 11), (11, 11)):
        c.clear(dx, dy)
    # wnętrze 4..7 jest jednolite, żeby rozciąganie niczego nie psuło
    c.rect(3, 3, 8, 8, base)
    save(c.img, "bomb_ui_pcb.png")


def make_traces():
    """Kafelek 16 x 16 ze ścieżkami i lutami; CSS kładzie go półprzezroczyście na płytce."""
    c = Canvas(16, 16)
    t = TRACE
    c.line(0, 3, 7, 3, t)
    c.line(7, 3, 10, 6, t)
    c.line(10, 6, 15, 6, t)
    c.line(0, 11, 4, 11, t)
    c.line(4, 11, 7, 14, t)
    c.line(7, 14, 15, 14, t)
    c.line(11, 6, 11, 0, t)
    c.disc(7, 3, 1, (t, t, t))
    c.disc(4, 11, 1, (t, t, t))
    c.dot(11, 0, t)
    save(c.img, "bomb_ui_traces.png")


def make_stick_frame():
    """Laska dynamitu 12 x 12 (krawędź 4 px): jasny grzbiet, ciemny spód, zaokrąglone końce, jasne denko z prawej."""
    light, base, dark = DYN
    cl, cb, cd = DYN_CAP
    c = Canvas(12, 12)
    c.rect(1, 0, 10, 11, OUTLINE[:3])
    c.rect(0, 1, 11, 10, OUTLINE[:3])
    c.rect(1, 1, 10, 10, base)
    c.rect(1, 1, 10, 3, light)       # grzbiet: trzy jasne wiersze, potem bazowy
    c.rect(1, 3, 10, 3, base)
    c.rect(1, 2, 10, 2, light)
    c.rect(1, 9, 10, 10, dark)
    c.rect(1, 8, 10, 8, dark)
    c.rect(1, 4, 10, 7, base)
    c.rect(1, 1, 2, 10, base)
    c.rect(1, 1, 1, 10, dark)
    c.rect(1, 1, 1, 3, base)
    c.rect(8, 1, 10, 10, cb)         # denko po prawej
    c.rect(8, 1, 10, 3, cl)
    c.rect(8, 8, 10, 10, cd)
    c.rect(8, 1, 8, 10, dark)
    for dx, dy in ((1, 1), (10, 1), (1, 10), (10, 10)):
        c.dot(dx, dy, OUTLINE[:3])
    save(c.img, "bomb_ui_stick.png")


def make_strap():
    c = Canvas(6, 8)
    light, base, dark = STRAP
    c.rect(0, 0, 5, 7, base)
    c.rect(0, 0, 0, 7, OUTLINE[:3])
    c.rect(5, 0, 5, 7, OUTLINE[:3])
    c.rect(1, 0, 1, 7, light)
    c.rect(4, 0, 4, 7, dark)
    save(c.img, "bomb_ui_strap.png")


def make_tnt():
    """Papierowa etykieta z napisem TNT, naklejona na laskę."""
    c = Canvas(19, 9)
    c.rect(0, 0, 18, 8, (238, 214, 160))
    c.rect(0, 0, 18, 0, (252, 236, 190))
    c.rect(0, 8, 18, 8, (190, 160, 110))
    c.glyphs(3, 2, "TNT", INK)
    for dx, dy in ((0, 0), (18, 0), (0, 8), (18, 8)):
        c.clear(dx, dy)
    save(c.outlined(), "bomb_ui_tnt.png")


def make_cap():
    """Spłonka (stalowy walec) wbita w lewy koniec laski. Kabel wchodzi w jej lewe denko."""
    c = Canvas(12, 10)
    c.shaded(0, 0, 11, 9, STEEL)
    c.rect(2, 1, 2, 8, STEEL[2])      # rowek
    c.rect(8, 1, 8, 8, STEEL[2])
    c.rect(1, 3, 1, 6, (30, 30, 36))  # otwór na kabel
    c.clear(0, 0)
    c.clear(0, 9)
    save(c.outlined(), "bomb_ui_cap.png")


def make_terminals():
    """Terminal na płytce (stalowy blok ze śrubą) z kolorową osłonką kabla, skierowany w prawo. 22 x 10 px."""
    for name, tones in WIRES.items():
        c = Canvas(22, 10)
        c.shaded(0, 0, 9, 9, STEEL)
        c.disc(4, 4, 3, GOLD)
        c.line(2, 5, 6, 3, (110, 80, 30))   # rowek śruby
        l, b, d = tones
        c.rect(9, 2, 21, 7, b)
        c.rect(9, 2, 21, 2, l)
        c.rect(9, 3, 21, 3, b)
        c.rect(9, 6, 21, 7, d)
        c.rect(9, 4, 21, 5, b)
        save(c.outlined(), f"bomb_ui_terminal_{name}.png")


def make_wires():
    """Kafelek kabla (8 x 6, powtarzany w poziomie): kontur, jasny skręt, cień. I końcówka po przecięciu."""
    for name, (l, b, d) in WIRES.items():
        c = Canvas(8, 6)
        c.rect(0, 0, 7, 5, b)
        c.rect(0, 0, 7, 0, OUTLINE[:3])
        c.rect(0, 5, 7, 5, OUTLINE[:3])
        c.rect(0, 1, 4, 1, l)
        c.rect(4, 4, 7, 4, d)
        c.rect(0, 4, 3, 4, b)
        c.rect(5, 2, 7, 2, b)
        c.rect(0, 3, 3, 3, b)
        c.rect(4, 3, 7, 3, d)
        save(c.img, f"bomb_ui_wire_{name}.png")

        # Przecięty kabel (koniec zwrócony w PRAWO): osłonka z postrzępionym brzegiem i rozchylone miedziane druciki.
        e = Canvas(14, 10)
        e.rect(0, 0, 6, 5, b)
        e.rect(0, 0, 6, 0, OUTLINE[:3])
        e.rect(0, 5, 6, 5, OUTLINE[:3])
        e.rect(0, 1, 4, 1, l)
        e.rect(0, 4, 5, 4, d)
        e.dot(7, 1, b)
        e.dot(7, 3, b)
        e.dot(7, 4, d)
        e.dot(6, 2, OUTLINE[:3])
        for pts in (((7, 2), (10, 1), (12, 1)), ((7, 3), (10, 3), (13, 4)), ((7, 4), (9, 6), (11, 8))):
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                e.line(ax, ay, bx, by, COPPER[1])
            e.dot(*pts[-1], COPPER[0])
        save(e.outlined(), f"bomb_ui_cut_{name}.png")


def make_spark():
    """Iskra przy przecięciu: pasek z trzema klatkami po 15 x 15 px (CSS przełącza je skokowo)."""
    c = Canvas(45, 15)
    white, yellow, orange = (255, 255, 235), (255, 232, 110), (255, 150, 60)

    def star(cx, rays, long_, short):
        c.dot(cx, 7, white)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for i in range(1, long_ + 1):
                c.dot(cx + dx * i, 7 + dy * i, yellow if i <= short else orange)
        if rays:
            for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                for i in range(1, rays + 1):
                    c.dot(cx + dx * i, 7 + dy * i, yellow if i == 1 else orange)

    star(7, 0, 3, 2)           # klatka 1: mały błysk
    star(22, 3, 6, 3)          # klatka 2: pełna gwiazda
    for dx, dy in ((-5, -4), (5, -3), (-4, 5), (6, 4), (0, -6), (1, 6)):   # klatka 3: rozlatujące się iskry
        c.dot(37 + dx, 7 + dy, orange)
    c.dot(37, 7, yellow)
    save(c.img, "bomb_ui_spark.png")


def make_display():
    """Ramka wyświetlacza zegara 12 x 12 (krawędź 4 px): stalowy rant i ciemny ekran, na którym CSS pisze czas."""
    c = Canvas(12, 12)
    c.rect(0, 0, 11, 11, OUTLINE[:3])
    c.rect(1, 1, 10, 10, STEEL[1])
    c.rect(1, 1, 10, 1, STEEL[0])
    c.rect(1, 1, 1, 10, STEEL[0])
    c.rect(1, 10, 10, 10, STEEL[2])
    c.rect(10, 1, 10, 10, STEEL[2])
    c.rect(2, 2, 9, 9, SCREEN_EDGE)
    c.rect(3, 3, 8, 8, SCREEN)
    for dx, dy in ((0, 0), (11, 0), (0, 11), (11, 11)):
        c.clear(dx, dy)
    save(c.img, "bomb_ui_display.png")


def make_parts():
    """Małe ozdoby płytki: układ scalony, brzęczyk i cewka."""
    c = Canvas(14, 8)
    c.rect(1, 1, 12, 6, (34, 34, 42))
    c.rect(1, 1, 12, 1, (62, 62, 74))
    for x in range(2, 13, 3):
        c.dot(x, 0, STEEL[1])
        c.dot(x, 7, STEEL[1])
    c.dot(2, 2, STEEL[1])
    c.rect(5, 3, 9, 4, (62, 62, 74))
    save(c.outlined(), "bomb_ui_chip.png")

    c = Canvas(14, 14)
    c.disc(6.5, 6.5, 6, ((78, 78, 90), (32, 32, 38), (14, 14, 18)))
    c.disc(6.5, 6.5, 2, STEEL)
    c.dot(6, 6, (10, 10, 14))
    c.dot(7, 6, (10, 10, 14))
    c.dot(3, 3, STEEL[1])
    save(c.outlined(), "bomb_ui_buzzer.png")

    c = Canvas(14, 14)
    c.disc(6.5, 6.5, 6, COPPER)
    c.disc(6.5, 6.5, 2, ((40, 24, 18), (28, 16, 12), (18, 10, 8)))
    for x, y in ((2, 4), (4, 2), (9, 2), (11, 4), (2, 9), (4, 11), (9, 11), (11, 9)):
        c.dot(x, y, COPPER[2])
    save(c.outlined(), "bomb_ui_coil.png")


# =====================================================================================================
#  PANEL NA MAPIE (poziomy "panel" i "boss"): wolnostojący terminal z ekranem, klawiaturą i anteną.
#  Ekran jest niebieski z kłódką, po rozbrojeniu zielony z haczykiem. Dioda alarmu to jedyny element,
#  który rysuje gra (PANEL_LED w game.js): w alarmie miga na czerwono.
# =====================================================================================================
PW, PH = 32, 40
PANEL_LED_BOX = (24, 22)    # lewy górny róg diody 3 x 3 px


def draw_world_panel(defused):
    c = Canvas(PW, PH)
    # podstawa i trzon
    c.shaded(6, 36, 25, 39, PANEL, round_corners=False)
    c.rect(12, 30, 19, 35, PANEL[2])
    c.rect(13, 30, 14, 35, PANEL[1])
    # antena
    c.rect(26, 1, 26, 5, STEEL[1])
    c.dot(26, 0, LED_OK if defused else LED_ON)
    c.dot(25, 1, STEEL[0])
    # korpus
    c.shaded(1, 5, 30, 30, PANEL)
    c.rect(2, 6, 29, 6, PANEL[0])
    # ekran
    edge = (20, 26, 38)
    c.rect(4, 8, 27, 19, edge)
    main, light = (SCR_GREEN, SCR_GREEN_LIGHT) if defused else (SCR_BLUE, SCR_BLUE_LIGHT)
    c.rect(5, 9, 26, 18, main)
    for y in range(10, 18, 2):
        c.rect(5, y, 26, y, light)
    if defused:      # haczyk
        for (x, y) in ((12, 14), (13, 15), (14, 16), (15, 15), (16, 14), (17, 13), (18, 12), (19, 11)):
            c.dot(x, y, ICON)
            c.dot(x, y + 1, ICON)
    else:            # kłódka: kabłąk i korpus
        for (x, y) in ((14, 11), (15, 10), (16, 10), (17, 11)):
            c.dot(x, y, ICON)
        c.rect(14, 11, 14, 12, ICON)
        c.rect(17, 11, 17, 12, ICON)
        c.rect(12, 13, 19, 17, ICON)
        c.rect(15, 14, 16, 16, main)
    # klawiatura 3 x 2
    for row in range(2):
        for col in range(3):
            x0, y0 = 5 + col * 6, 22 + row * 4
            c.rect(x0, y0, x0 + 4, y0 + 2, PANEL_DARK[1])
            c.rect(x0, y0, x0 + 4, y0, STEEL[1])
    # dioda alarmu (gra rysuje ją na wierzchu, gdy panel jest aktywny)
    lx, ly = PANEL_LED_BOX
    c.rect(lx, ly, lx + 2, ly + 2, (24, 20, 26))
    c.dot(lx + 1, ly + 1, LED_OK if defused else LED_OFF)
    # szczeliny wentylacyjne
    for x in (24, 26, 28):
        c.rect(x, 26, x, 28, PANEL[2])
    return c.outlined()


def make_world_panel():
    live, done = draw_world_panel(False), draw_world_panel(True)
    box = tuple(f(a, b) for f, a, b in zip((min, min, max, max), live.getbbox(), done.getbbox()))
    live, done = live.crop(box), done.crop(box)
    save(live, "panel.png")
    save(done, "panel_defused.png")
    lx, ly = PANEL_LED_BOX
    print(f"    obrazek panelu {live.width}x{live.height} px; dioda 3x3 px w x={lx - box[0]} y={ly - box[1]} (PANEL_LED w game.js)")


# =====================================================================================================
#  OKNO ROZBRAJANIA PANELU: zamiast płytki z bombą po lewej jest panel sterujący (klawiatura, diody, głośnik),
#  a po prawej zamiast dynamitu nadajnik z anteną, do którego zbiegają się kable.
# =====================================================================================================
def make_panel_frame():
    light, base, dark = PANEL
    c = Canvas(12, 12)
    c.rect(0, 0, 11, 11, OUTLINE[:3])
    c.rect(1, 1, 10, 10, base)
    c.rect(1, 1, 10, 1, light)
    c.rect(1, 1, 1, 10, light)
    c.rect(1, 10, 10, 10, dark)
    c.rect(10, 1, 10, 10, dark)
    c.rect(3, 3, 8, 8, base)
    for dx, dy in ((0, 0), (11, 0), (0, 11), (11, 11)):
        c.clear(dx, dy)
    save(c.img, "bomb_ui_panel_frame.png")


def make_panel_parts():
    # klawiatura 3 x 3
    c = Canvas(17, 13)
    for row in range(3):
        for col in range(3):
            x0, y0 = col * 6, row * 4
            c.rect(x0, y0, x0 + 4, y0 + 2, PANEL_DARK[1])
            c.rect(x0, y0, x0 + 4, y0, STEEL[0])
            c.rect(x0, y0 + 2, x0 + 4, y0 + 2, PANEL_DARK[2])
    save(c.outlined(), "bomb_ui_keypad.png")
    # trzy diody: czerwona, bursztynowa, zielona
    c = Canvas(14, 4)
    for i, col in enumerate(((255, 80, 70), (255, 190, 70), LED_OK)):
        c.rect(i * 5, 0, i * 5 + 3, 3, (24, 20, 26))
        c.rect(i * 5 + 1, 1, i * 5 + 2, 2, col)
    save(c.outlined(), "bomb_ui_leds.png")
    # głośnik: kratka
    c = Canvas(14, 10)
    c.rect(0, 0, 13, 9, PANEL_DARK[1])
    c.rect(0, 0, 13, 0, PANEL_DARK[0])
    for y in range(2, 9, 2):
        c.rect(2, y, 11, y, (14, 18, 26))
    for dx, dy in ((0, 0), (13, 0), (0, 9), (13, 9)):
        c.clear(dx, dy)
    save(c.outlined(), "bomb_ui_grille.png")


def make_transmitter():
    """Nadajnik radiowy 40 x 46: kabel wchodzi w złotą wtyczkę po lewej, na górze antena z falami."""
    c = Canvas(40, 46)
    light, base, dark = PANEL_DARK
    # korpus
    c.shaded(9, 16, 39, 44, PANEL_DARK)
    c.rect(10, 17, 38, 17, PANEL[1])
    # wtyczka (tu kończy się przewód): stalowa obejma i złoty trzpień
    c.shaded(2, 25, 9, 35, STEEL, round_corners=False)
    c.rect(0, 28, 3, 32, GOLD[1])
    c.rect(0, 28, 3, 28, GOLD[0])
    c.rect(0, 32, 3, 32, GOLD[2])
    # ekran odbioru z paskami sygnału
    c.rect(13, 21, 35, 30, (14, 20, 30))
    c.rect(14, 22, 34, 29, (22, 34, 50))
    for i, h in enumerate((2, 3, 4, 5, 6)):
        x = 17 + i * 4
        c.rect(x, 29 - h, x + 2, 28, LED_OK if i < 4 else (255, 190, 70))
    # napis TX i diody
    c.glyphs(15, 34, "T", STEEL[0])
    c.glyphs(19, 34, "X", STEEL[0])
    c.rect(28, 34, 29, 35, (255, 80, 70))
    c.rect(32, 34, 33, 35, LED_OK)
    for x in (14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34):
        c.rect(x, 40, x, 42, (14, 18, 26))
    # antena: maszt z kulką i dwa łuki fal po prawej
    c.rect(29, 6, 30, 15, STEEL[1])
    c.rect(29, 6, 29, 15, STEEL[0])
    c.disc(29.5, 4.5, 2, STEEL)
    c.dot(29, 4, (255, 255, 235))
    for r, color in ((5, (255, 236, 130)), (8, (255, 210, 90))):
        for ang in range(-55, 56, 11):
            c.dot(29.5 + r * math.cos(math.radians(ang)), 4.5 - r * math.sin(math.radians(ang)), color)
    save(c.outlined(), "bomb_ui_transmitter.png")


def main():
    ASSETS.mkdir(exist_ok=True)
    make_world_bomb()
    make_pcb_frame()
    make_traces()
    make_stick_frame()
    make_strap()
    make_tnt()
    make_cap()
    make_terminals()
    make_wires()
    make_spark()
    make_display()
    make_parts()
    make_world_panel()
    make_panel_frame()
    make_panel_parts()
    make_transmitter()


if __name__ == "__main__":
    main()