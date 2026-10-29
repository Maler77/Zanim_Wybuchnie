"""Rysuje grafiki poziomu 3 (miasto w nocy): tło z księżycem, chodnik, budynki (w tym trzy miejsca firmy Trelvos), rekwizyty.

Uruchom z głównego katalogu repozytorium:   python "tools/make level 3 art.py"
(wymaga bibliotek Pillow i numpy:  pip install pillow numpy)

Powstają pliki w assets/ (nazwy zaczynają się od "l3_", żeby nie mieszały się z resztą):
  l3_city.png            panorama miasta 1280 x 480 w nocy (zapętla się poziomo bez szwu), tło z paralaksą
  l3_pavement.png        kafelek mokrego chodnika 32 x 40 (podłoże)
  l3_trelvos_hotel.png   hotel Trelvos (256 x 160, tło przy bombie 1)      l3_trelvos_tower.png  wieża Trelvos (224 x 192, dach z bombą 2)
  l3_trelvos_sign.png    neon na dachu (128 x 48)                           l3_club.png           klub (192 x 208, dach z bombą 3)
  l3_flat.png            kamienica (224 x 192), l3_office.png biurowiec (192 x 192), l3_gate.png budynek z bramą (224 x 288),
  l3_depot.png           zajezdnia przy wyjściu (224 x 128)
  l3_fire_escape.png     schody przeciwpożarowe (56 x 208; podesty na y = 64, 112, 160)
  l3_mast.png            maszt radiowy z czerwonym światłem (64 x 378; punkt zaczepienia haka w (32, 32))
  l3_lamp.png            zapalona latarnia 100 x 300 (słup i oprawa z "lampa włączona.png", ale stożek światła jest rastrowany,
                         więc nie zasłania tła; słup ma środek w x = 44)
  rekwizyty: l3_crate, l3_dumpster, l3_taxi, l3_van, l3_container, l3_bench, l3_hydrant, l3_tree, l3_phone

Styl jak poziomy 1 i 2: czarny kontur 1 px na rekwizytach, trzy tony cieniowania, ostre piksele. Światło księżyca pada z góry
(chłodny, jasnoniebieski rant dachów), okna są ciemne albo świecą ciepłym żółtym, neony Trelvos mają ten sam bursztyn co w poziomie 2.
Kolory są w słownikach na górze, kształty w funkcjach draw_*.
"""

import importlib.util
import random
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"

# Canvas, kolory i czcionkę bierzemy z narzędzia poziomu 2 (które bierze je z poziomu 1), żeby wszystkie poziomy rysowały tak samo.
_spec = importlib.util.spec_from_file_location("level2_art", HERE / "make level 2 art.py")
_l2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_l2)
Canvas, hexc, INK, METAL, WOOD, GREEN = _l2.Canvas, _l2.hexc, _l2.INK, _l2.METAL, _l2.WOOD, _l2.GREEN
TRELVOS, TRELVOS_DARK, LIT = _l2.TRELVOS, _l2.TRELVOS_DARK, _l2.LIT
FONT, draw_text, text_width, trelvos_sign = _l2.FONT, _l2.draw_text, _l2.text_width, _l2.trelvos_sign

# Dodatkowe litery do napisów (HOTEL, KLUB, TAXI).
FONT.update({
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "X": ["#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"],
})

# Fasady w nocy: jasny (rant w świetle księżyca), bazowy, ciemny (cień / lewy brzeg)
NBRICK = (hexc("#6e5070"), hexc("#523a5c"), hexc("#382642"))
NCONC = (hexc("#5a6684"), hexc("#414c68"), hexc("#2c354e"))
NSAND = (hexc("#8a7684"), hexc("#665668"), hexc("#463a4c"))
NSLATE = (hexc("#566a96"), hexc("#3a4a72"), hexc("#26324f"))
NSTEEL = (hexc("#5a7690"), hexc("#415a74"), hexc("#2c4058"))
NCLUB = (hexc("#5a3f7c"), hexc("#3a2856"), hexc("#241638"))
MOON = hexc("#bcd2ff")           # światło księżyca na krawędziach dachów
MOON_DARK = hexc("#6c88cc")
GLASS = (hexc("#34447a"), hexc("#1f2a50"), hexc("#121a36"))      # ciemna szyba: góra, środek, dół
TV = (hexc("#a8f4ff"), hexc("#44bcdc"), hexc("#1e7898"))         # okno z telewizorem
PINK = (hexc("#ffb0e4"), hexc("#f0509c"), hexc("#962060"))       # neon różowy
CYAN = (hexc("#c4faff"), hexc("#3cd0ec"), hexc("#16809c"))       # neon turkusowy
LEAF = (hexc("#4a7a8a"), hexc("#2e5266"), hexc("#1c3446"))       # liście w świetle księżyca
BEACON = hexc("#ff3a3a")

BG_W, BG_H = 1280, 480


# ---------------------------------------------------------------------------
#  TŁO I CHODNIK
# ---------------------------------------------------------------------------

def rect_wrap(a, x, y, w, h, col):
    """Prostokąt w tablicy tła z zawinięciem poziomym (dzięki temu panorama nie ma szwu)."""
    for xx in range(x, x + w):
        px = xx % BG_W
        y0, y1 = max(0, y), min(BG_H, y + h)
        if y1 > y0:
            a[y0:y1, px] = col


def put_wrap(a, x, y, col):
    if 0 <= y < BG_H:
        a[y, x % BG_W] = col


def draw_city():
    rng = random.Random(33)
    a = np.zeros((BG_H, BG_W, 3), dtype=np.uint8)

    # Niebo: pasy granatu z rastrem 2 x 2 na styku (jak w l2_city), jaśniejsze i fioletowo-niebieskie przy horyzoncie.
    bands = [hexc(c) for c in ("#050918", "#091030", "#0e1a42", "#142654", "#1c3266", "#274278", "#36568c")]
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

    # Gwiazdy: pojedyncze piksele (mniej przy horyzoncie) i kilka większych krzyżyków.
    star_cols = [hexc("#ffffff"), hexc("#dfe8ff"), hexc("#fff2b8"), hexc("#a8c0ff")]
    for _ in range(260):
        x, y = rng.randrange(BG_W), rng.randrange(0, 280)
        if y > 190 and rng.random() < 0.6:
            continue
        put_wrap(a, x, y, rng.choice(star_cols))
    for _ in range(16):
        x, y = rng.randrange(BG_W), rng.randrange(8, 200)
        put_wrap(a, x, y, hexc("#ffffff"))
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            put_wrap(a, x + dx, y + dy, hexc("#8fa8e8"))

    # Księżyc: jasna tarcza z kraterami, obwódka z rastra i poświata z rastra.
    mx, my, mr = 330, 130, 38
    for y in range(my - mr - 22, my + mr + 23):
        for x in range(mx - mr - 22, mx + mr + 23):
            d = ((x - mx) ** 2 + (y - my) ** 2) ** 0.5
            if d <= mr:
                shade = (x - mx) * 0.6 + (y - my) * 0.8     # prawy dół w cieniu
                col = hexc("#fffbd8") if shade < -mr * 0.35 else hexc("#f2edb8") if shade < mr * 0.35 else hexc("#d9d39c")
                put_wrap(a, x, y, col)
            elif d <= mr + 4 and (x // 2 + y // 2) % 2 == 0:
                put_wrap(a, x, y, hexc("#e8e6c0"))
            elif d <= mr + 10 and (x + y) % 4 == 0:
                put_wrap(a, x, y, hexc("#5a76b0"))
            elif d <= mr + 20 and (x // 2 + y) % 6 == 0:
                put_wrap(a, x, y, hexc("#3c5894"))
    for cx, cy, cr in ((mx - 12, my - 8, 8), (mx + 14, my + 12, 6), (mx - 4, my + 20, 5), (mx + 18, my - 14, 4)):
        for y in range(cy - cr, cy + cr + 1):
            for x in range(cx - cr, cx + cr + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= cr * cr:
                    put_wrap(a, x, y, hexc("#cfc88e"))

    # Chmury: ciemne smugi z jasnym grzbietem od księżyca.
    body, ridge = hexc("#16224c"), hexc("#3a5290")
    for _ in range(9):
        cx = rng.randrange(0, BG_W)
        cy = rng.randrange(40, 250)
        for k in range(rng.randrange(2, 4)):
            bw = rng.randrange(60, 170) - k * 22
            ox = cx + rng.randrange(-20, 20)
            oy = cy + k * 5
            rect_wrap(a, ox, oy, bw, 4, body)
            rect_wrap(a, ox + 3, oy, bw - 6, 1, ridge)

    # Trzy warstwy panoramy miasta: coraz bliżej, coraz ciemniej; w bliższych coraz więcej świecących okien.
    layers = [
        dict(base=hexc("#243468"), edge=hexc("#3a4e92"), win=hexc("#2e4078"), lit=(hexc("#8a8a5a"), hexc("#7a8ab0")), p=0.07, top=250, low=190, step=(40, 80)),
        dict(base=hexc("#182450"), edge=hexc("#2c4088"), win=hexc("#21306a"), lit=(hexc("#c8aa58"), hexc("#a0b0e0")), p=0.15, top=290, low=235, step=(46, 90)),
        dict(base=hexc("#0d1434"), edge=hexc("#1f3070"), win=hexc("#16204c"), lit=(hexc("#ffdc66"), hexc("#ffe99a")), p=0.30, top=330, low=275, step=(50, 100)),
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
            rect_wrap(a, x, top, bw, 2, L["edge"])        # rant dachu w świetle księżyca
            rect_wrap(a, x, top, 2, ground_line - top, L["edge"])
            # Okna: siatka ciemnych kwadratów, część świeci (ciepłe żółte, czasem chłodne z telewizora).
            for wy in range(top + 8, ground_line - 8, 10):
                for wx in range(x + 6, x + bw - 6, 9):
                    col = L["win"]
                    if rng.random() < L["p"]:
                        col = L["lit"][0] if rng.random() < 0.85 else L["lit"][1]
                    rect_wrap(a, wx, wy, 4, 5, col)
            # Dodatki na dachu: antena z czerwonym światłem, nadbudówka.
            kind = rng.random()
            if kind < 0.3:
                rect_wrap(a, x + bw // 2, top - 14, 2, 14, L["edge"])
                if li >= 1:
                    rect_wrap(a, x + bw // 2 - 1, top - 17, 4, 3, BEACON if li == 2 else hexc("#a02a3a"))
            elif kind < 0.55 and bw > 36:
                rect_wrap(a, x + 6, top - 8, bw // 3, 8, L["base"])
                rect_wrap(a, x + 6, top - 8, bw // 3, 2, L["edge"])
            x += bw - rng.randrange(0, 6)

    # Podstawa ulicy pod miastem: mur z gzymsem w świetle księżyca (widać tylko wąski pas nad chodnikiem).
    for y in range(ground_line, BG_H):
        i = y - ground_line
        col = hexc("#2c3556") if i < 3 else hexc("#222a46") if i < 28 else hexc("#1a2038")
        a[y, :] = col
    a[ground_line, :] = hexc("#5870b0")
    for x in range(0, BG_W, 32):                        # fugi muru
        a[ground_line + 3:BG_H, x] = (a[ground_line + 3:BG_H, x] * 0.8).astype(np.uint8)

    Image.fromarray(a, "RGB").save(ASSETS / "l3_city.png")
    print(f"l3_city.png: {BG_W}x{BG_H}")


def draw_pavement():
    """Chodnik 32 x 40: ciemne, mokre płyty z fugami i krawężnik; na płytach odbicia neonów (jak l2_pavement, ale w nocy)."""
    c = Canvas(32, 40)
    slab_a, slab_b = hexc("#4a5470"), hexc("#434c68")
    joint = hexc("#2c3450")
    for y in range(26):
        c.hline(0, y, 32, slab_a if y < 14 else slab_b)
    c.hline(0, 0, 32, hexc("#8aa0d8"))
    c.hline(0, 1, 32, hexc("#64789e"))
    c.vline(31, 2, 24, joint)
    c.vline(15, 14, 12, joint)
    c.hline(0, 13, 32, joint)
    rng = random.Random(7)
    for _ in range(7):
        c.px(rng.randrange(32), rng.randrange(3, 25), hexc("#5c6890"))
    for x, y, col in ((5, 6, hexc("#7a6ab0")), (6, 6, hexc("#7a6ab0")), (21, 19, hexc("#4a98b4")), (22, 19, hexc("#4a98b4")), (9, 20, hexc("#b09a58"))):
        c.px(x, y, col)                                  # odbicia neonów w kałużach
    c.hline(0, 26, 32, hexc("#6a7aa8"))                  # krawężnik
    for y in range(27, 33):
        c.hline(0, y, 32, hexc("#3a4466"))
    c.hline(0, 27, 32, hexc("#56668f"))
    for y in range(33, 40):
        c.hline(0, y, 32, hexc("#222a44"))
    c.save("l3_pavement.png")


# ---------------------------------------------------------------------------
#  ELEMENTY BUDYNKÓW
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
            c.px(rng.randrange(w), rng.randrange(cap + 2, h), light if rng.random() < 0.4 else dark)
    else:
        for _ in range(w * h // 38):
            c.px(rng.randrange(w), rng.randrange(cap + 2, h), light if rng.random() < 0.3 else dark)
    c.rect(0, cap, 3, h - cap, dark)                 # lewy bok w cieniu
    c.rect(w - 3, cap, 3, h - cap, light)            # prawy w świetle
    c.rect(0, 0, w, cap, light)                      # dach i attyka (po niej chodzi gracz)
    c.rect(0, cap - 2, w, 2, dark)
    c.hline(0, 0, w, MOON)
    c.hline(0, 1, w, MOON_DARK)
    for x in range(6, w - 6, 24):
        c.rect(x, 2, 3, cap - 4, base)
    return c


def window(c, x, y, ww, wh, kind="glass", sill=True, curtain=None):
    """Okno w nocy: kind = glass (ciemne) | lit (ciepłe światło) | tv (niebieskie światło telewizora) | open (uchylone)."""
    c.rect(x - 1, y - 1, ww + 2, wh + 2, INK)
    if kind == "lit":
        c.rect(x, y, ww, wh, LIT[1])
        c.rect(x + 1, y + 1, ww - 2, wh // 2 - 1, LIT[0])
        c.rect(x, y + wh - 3, ww, 3, LIT[2])
    elif kind == "tv":
        c.rect(x, y, ww, wh, TV[1])
        c.rect(x + 1, y + 1, ww - 2, wh // 2 - 1, TV[0])
        c.rect(x, y + wh - 3, ww, 3, TV[2])
    else:
        c.rect(x, y, ww, wh, GLASS[1])
        c.rect(x, y, ww, wh // 3, GLASS[0])
        c.rect(x, y + wh - 3, ww, 3, GLASS[2])
        for i in range(min(ww, wh) // 3):
            c.px(x + 2 + i * 2, y + 2 + i * 2, MOON_DARK)
    if kind == "open":
        c.rect(x + ww // 2, y, ww // 2, wh, hexc("#121a36"))
    c.vline(x + ww // 2, y, wh, INK)
    c.hline(x, y + wh // 2 - 1, ww, INK)
    if sill:
        c.rect(x - 2, y + wh + 1, ww + 4, 2, hexc("#7a8ab8"))
        c.hline(x - 2, y + wh + 3, ww + 4, INK)
    if curtain:
        c.rect(x + 1, y + 1, 3, wh // 2 - 1, curtain)


def window_grid(c, x0, y0, x1, y1, ww, wh, gap_x, gap_y, seed, lit_ratio=0.35, tv_ratio=0.06, curtains=False, open_ratio=0.05):
    rng = random.Random(seed)
    cols = max(1, (x1 - x0 + gap_x) // (ww + gap_x))
    used = cols * ww + (cols - 1) * gap_x
    start = x0 + (x1 - x0 - used) // 2
    y = y0
    while y + wh + 4 <= y1:
        for i in range(cols):
            r = rng.random()
            kind = "lit" if r < lit_ratio else "tv" if r < lit_ratio + tv_ratio else "open" if r < lit_ratio + tv_ratio + open_ratio else "glass"
            curtain = hexc("#e87aa0") if curtains and kind == "lit" and rng.random() < 0.4 else None
            window(c, start + i * (ww + gap_x), y, ww, wh, kind, curtain=curtain)
        y += wh + gap_y


def awning(c, x, y, w, depth=7, a=hexc("#a8382e"), b=hexc("#e8d8b0")):
    """Markiza w pasy; w nocy trochę przygaszona (czerwień i kremowy)."""
    for i in range(w):
        col = a if (i // 6) % 2 == 0 else b
        c.rect(x + i, y, 1, depth, col)
        c.px(x + i, y + depth, col if (i % 6) not in (0, 5) else INK)
    c.hline(x, y - 1, w, INK)
    c.hline(x, y, w, hexc("#c4d0f0"))
    c.rect(x, y + depth + 1, w, 2, hexc("#00000050"))


def shopfront(c, x, y, w, h, kind="lit"):
    """Witryna: lit = ciepłe światło sklepu i sylwetki towarów, dark = ciemna szyba, shutter = rolety."""
    c.rect(x - 1, y - 1, w + 2, h + 2, INK)
    if kind == "shutter":
        c.rect(x, y, w, h, METAL[2])
        for i in range(0, h, 3):
            c.hline(x, y + i, w, METAL[1])
            c.hline(x, y + i + 1, w, hexc("#262a38"))
    elif kind == "dark":
        c.rect(x, y, w, h, hexc("#1a2444"))
        c.rect(x + 2, y + 2, w - 4, h - 4, GLASS[1])
        c.rect(x + 2, y + 2, w - 4, (h - 4) // 3, GLASS[0])
        for i in range(0, w - 4, 4):
            c.px(x + 4 + i, y + 3 + (i // 4) % 3, MOON_DARK)
    else:
        c.rect(x, y, w, h, hexc("#3a2a1c"))
        c.rect(x + 2, y + 2, w - 4, h - 4, hexc("#ffc850"))
        c.rect(x + 2, y + 2, w - 4, (h - 4) // 2, hexc("#ffe08a"))
        c.rect(x + 2, y + h - 6, w - 4, 4, hexc("#c88a28"))
        for i in range(0, w - 8, 9):                      # półki z towarem (sylwetki)
            c.rect(x + 5 + i, y + h - 12, 5, 6, hexc("#7a4a22"))


def door(c, x, y, w=16, h=30, glow=True):
    c.rect(x - 1, y - 1, w + 2, h + 1, INK)
    c.rect(x, y, w, h, hexc("#1a2038"))
    c.rect(x + 2, y + 3, w - 4, min(10, h - 6), hexc("#ffd84a") if glow else hexc("#3a4e86"))
    c.px(x + w - 4, y + h // 2 + 3, hexc("#f0e8b0"))


def neon_text(c, x, y, text, scale, pal, plate=True):
    """Napis neonowy (jasny środek, ciemny cień) na ciemnej płytce z ramką w kolorze neonu."""
    tw = text_width(text, scale)
    if plate:
        c.rect(x - 4, y - 4, tw + 8, 7 * scale + 8, INK)
        c.rect(x - 3, y - 3, tw + 6, 7 * scale + 6, hexc("#141a34"))
        c.outline_box(x - 3, y - 3, tw + 6, 7 * scale + 6, pal[1])
    draw_text(c, x, y, text, scale, pal[0], shadow=pal[2])
    return tw


# ---------------------------------------------------------------------------
#  BUDYNKI
# ---------------------------------------------------------------------------

def draw_trelvos_hotel():
    """Hotel Trelvos 256 x 160: wielki neon TRELVOS, turkusowy HOTEL pod nim, oświetlone wejście pod markizą (bomba 1)."""
    w, h = 256, 160
    c = facade(w, h, NSAND, 311, cap=8, pattern="stucco")
    window_grid(c, 12, 14, w - 12, 44, 16, 14, 20, 6, 321, lit_ratio=0.45, curtains=True)
    trelvos_sign(c, 40, 40, 176, 28, 3)
    neon_text(c, 100, 76, "HOTEL", 2, CYAN)
    c.rect(3, 96, w - 6, h - 96, NSAND[1])
    shopfront(c, 10, 108, 80, 44, "lit")
    shopfront(c, 166, 108, 80, 44, "lit")
    door(c, 106, 104, 44, 56, glow=True)
    c.vline(128, 106, 54, INK)
    awning(c, 96, 96, 64, 7, a=hexc("#8a2a3e"), b=hexc("#e8c878"))
    for x in (4, 240):                                 # lampy przy wejściu
        c.rect(x, 90, 8, 4, METAL[1])
        c.rect(x + 1, 94, 6, 3, hexc("#fff3a0"))
    c.rect(98, 156, 60, 4, NSAND[2])
    c.save("l3_trelvos_hotel.png")


def draw_flat():
    """Kamienica 224 x 192 z balkonami i oknami w nocy (przy lewej ścianie stoją schody przeciwpożarowe)."""
    w, h = 224, 192
    c = facade(w, h, NBRICK, 331)
    window_grid(c, 12, 16, w - 12, 128, 14, 18, 24, 12, 341, lit_ratio=0.38, curtains=True)
    for by in (44, 82):
        for bx in range(16, w - 28, 38):
            c.rect(bx - 2, by + 22, 32, 3, hexc("#8a96bc"))
            c.hline(bx - 2, by + 25, 32, INK)
            for i in range(0, 30, 4):
                c.vline(bx + i, by + 12, 10, hexc("#1e2848"))
            c.hline(bx - 1, by + 11, 30, hexc("#4a5a88"))
    c.rect(3, 148, w - 6, h - 148, NBRICK[2])
    shopfront(c, 14, 156, 56, 30, "dark")
    door(c, 84, 152, 22, 40, glow=True)
    shopfront(c, 120, 156, 50, 30, "shutter")
    door(c, 184, 156, 16, 36, glow=False)
    c.save("l3_flat.png")


def draw_office():
    """Biurowiec 192 x 192: beton, pasy okien (część biur jeszcze świeci), rury i klimatyzatory przy ścianie."""
    w, h = 192, 192
    c = facade(w, h, NCONC, 351, cap=8, pattern="stucco")
    window_grid(c, 14, 16, w - 14, 146, 18, 12, 14, 8, 361, lit_ratio=0.3, tv_ratio=0.1, open_ratio=0.0)
    for y in (36, 76, 116):
        c.rect(5, y, 6, 5, METAL[1])
        c.rect(5, y, 6, 1, METAL[0])
    c.rect(w - 11, 14, 4, h - 40, METAL[2])
    c.rect(w - 11, 14, 1, h - 40, METAL[0])
    c.rect(3, 152, w - 6, h - 152, NCONC[2])
    shopfront(c, 10, 160, 60, 28, "dark")
    door(c, 84, 156, 28, 36, glow=True)
    shopfront(c, 124, 160, 60, 28, "shutter")
    c.save("l3_office.png")


def draw_trelvos_tower():
    """Wieża Trelvos 224 x 192: szklana fasada z neonem; dach jest płaski (stoi na nim bomba 2 i neon l3_trelvos_sign)."""
    w, h = 224, 192
    c = facade(w, h, NSLATE, 371, cap=8, pattern="stucco")
    for y in range(16, 112, 24):
        for x in range(10, w - 10, 22):
            window(c, x, y, 16, 16, "lit" if (x * 3 + y) % 5 < 2 else "glass", sill=False)
    trelvos_sign(c, 44, 128, 136, 22, 3)
    c.rect(3, 158, w - 6, h - 158, NSLATE[2])
    shopfront(c, 10, 164, 70, 24, "dark")
    door(c, 96, 160, 32, 32, glow=True)
    shopfront(c, 144, 164, 70, 24, "dark")
    c.rect(6, 14, 4, h - 20, METAL[2])
    c.rect(6, 14, 1, h - 20, METAL[0])
    for y in (40, 84, 120):
        c.rect(5, y, 6, 4, METAL[1])
    c.save("l3_trelvos_tower.png")


def draw_trelvos_sign():
    """Neon na dachu 128 x 48: słupki i tablica z napisem TRELVOS."""
    w, h = 128, 48
    c = Canvas(w, h)
    for x in (14, w - 18):
        c.rect(x, 28, 4, 20, METAL[2])
        c.rect(x, 28, 1, 20, METAL[0])
    trelvos_sign(c, 4, 4, 120, 26, 3)
    c.hline(4, 4, 120, TRELVOS[0])
    c.outline_alpha()
    c.save("l3_trelvos_sign.png")


def draw_gate():
    """Budynek z bramą 224 x 288: dół to przejście (wysokie na 64 px), nad nim kilka pięter. Lewa ściana szybu."""
    w, h = 224, 288
    open_h = 64
    c = facade(w, h, NBRICK, 381)
    window_grid(c, 12, 16, w - 12, h - open_h - 10, 14, 18, 22, 14, 391, lit_ratio=0.33, curtains=True)
    top = h - open_h
    c.rect(0, top - 6, w, 6, NBRICK[2])
    c.hline(0, top - 6, w, hexc("#8a96bc"))
    c.rect(0, top, w, open_h, hexc("#141a30"))
    for x in range(0, w, 3):
        c.vline(x, top + 16 + (x % 5), open_h - 16 - (x % 5), hexc("#1c2442"))
    c.rect(w // 2 - 22, top + 12, 44, open_h - 12, hexc("#2a3c6c"))        # księżycowa poświata po drugiej stronie przejścia
    c.rect(w // 2 - 14, top + 20, 28, open_h - 20, hexc("#6c88cc"))
    for x in (4, 62, 124, 186):
        c.rect(x, top, 10, open_h, NBRICK[1])
        c.rect(x, top, 3, open_h, NBRICK[2])
        c.rect(x + 8, top, 2, open_h, NBRICK[0])
        c.rect(x - 1, top, 12, 4, hexc("#8a96bc"))
    for x in (30, 150):                                # lampy w przejściu
        c.rect(x, top + 6, 6, 3, METAL[1])
        c.rect(x + 1, top + 9, 4, 3, hexc("#fff3a0"))
    c.save("l3_gate.png")


def draw_club():
    """Klub 192 x 208: ciemny fiolet, różowo-turkusowy neon KLUB, oświetlone wejście. Prawa ściana szybu; dach z bombą 3."""
    w, h = 192, 208
    c = facade(w, h, NCLUB, 401, cap=8, pattern="stucco")
    for y in range(16, 84, 22):                        # okna z kolorowymi światłami (imprezy na piętrach)
        for i, x in enumerate(range(16, w - 24, 34)):
            kind = ("lit", "glass", "tv", "glass")[(i + y // 22) % 4]
            window(c, x, y, 18, 14, kind, sill=False)
    neon_text(c, 56, 108, "KLUB", 4, PINK)
    c.hline(30, 100, w - 60, CYAN[1])
    c.hline(30, 148, w - 60, CYAN[1])
    c.rect(3, 160, w - 6, h - 160, NCLUB[2])
    door(c, 78, 164, 36, 44, glow=True)
    c.rect(70, 156, 52, 5, PINK[1])                    # daszek nad wejściem
    c.hline(70, 156, 52, PINK[0])
    c.rect(12, 176, 40, 28, INK)                       # głośniki
    c.rect(13, 177, 38, 26, hexc("#241a38"))
    for cx in (24, 40):
        c.rect(cx - 5, 182, 10, 10, hexc("#4a3a6a"))
        c.rect(cx - 2, 185, 4, 4, INK)
    for x in (w - 14, w - 10):                        # pionowe rurki neonowe przy prawym brzegu
        c.vline(x, 20, 130, CYAN[1])
    c.vline(w - 14, 20, 130, CYAN[0])
    c.save("l3_club.png")


def draw_depot():
    """Zajezdnia przy wyjściu 224 x 128: stalowa hala z rolowanymi bramami, lampami i neonem Trelvos (tło dla drzwi wyjścia)."""
    w, h = 224, 128
    c = facade(w, h, NSTEEL, 411, cap=8, pattern="stucco")
    window_grid(c, 12, 16, w - 12, 44, 16, 12, 20, 6, 421, lit_ratio=0.3)
    trelvos_sign(c, 56, 48, 112, 18, 2)
    c.rect(3, 72, w - 6, h - 72, NSTEEL[1])
    shopfront(c, 12, 80, 100, 44, "shutter")
    c.rect(11, 72, 102, 6, INK)
    for i in range(0, 100, 14):                        # pasy ostrzegawcze nad bramą
        c.rect(12 + i, 73, 7, 4, hexc("#f0c020"))
    for x in (124, 160):
        c.rect(x, 74, 8, 3, METAL[1])
        c.rect(x + 1, 77, 6, 3, hexc("#fff3a0"))
    c.save("l3_depot.png")


# ---------------------------------------------------------------------------
#  REKWIZYTY
# ---------------------------------------------------------------------------

def draw_fire_escape():
    """Schody przeciwpożarowe 56 x 208 przy lewej ścianie kamienicy: trzy podesty (y = 64, 112, 160 od góry) połączone schodami.
    Podesty to platformy jednokierunkowe w poziomie (make level 3.py); schody są tylko ozdobą."""
    w, h = 56, 208
    c = Canvas(w, h)
    deck, rail, dark = METAL[1], METAL[0], METAL[2]
    for y in (64, 112, 160):
        c.rect(0, y, w, 4, deck)
        c.hline(0, y, w, rail)
        for x in range(2, w, 6):                        # kratka podestu
            c.vline(x, y + 1, 3, dark)
        c.hline(0, y + 4, w, dark)
        c.hline(0, y - 16, w, rail)                     # poręcz
        for x in range(0, w, 12):
            c.vline(x, y - 16, 16, dark)
    for y in (64, 112):                                 # schody w dół (skos od podestu do podestu)
        for i in range(36):
            c.px(8 + i, y + 5 + i * 43 // 36, dark)
            c.px(8 + i, y + 6 + i * 43 // 36, deck)
    for i in range(0, 36, 4):                           # drabina z górnego podestu na dach
        c.hline(w - 20, 16 + i, 10, deck)
    c.vline(w - 20, 16, 48, rail)
    c.vline(w - 11, 16, 48, rail)
    c.rect(w - 4, 14, 4, h - 14, dark)                  # wspornik przy ścianie
    c.rect(w - 4, 14, 1, h - 14, METAL[0])
    c.outline_alpha()
    c.save("l3_fire_escape.png")


def draw_mast():
    """Maszt radiowy 64 x 378: kratownica zwężająca się ku górze, antena i czerwone światło ostrzegawcze (punkt zaczepienia haka
    w (32, 32)); stoi w dziurze między dachami, na dole kolce."""
    w, h = 64, 378
    c = Canvas(w, h)
    steel, light, dark = METAL[1], METAL[0], METAL[2]
    top_y = 44
    for y in range(top_y, h - 16):                      # dwie nogi rozchodzące się ku dołowi
        t = (y - top_y) / (h - 16 - top_y)
        half = int(4 + t * 18)
        for x in (32 - half, 32 + half):
            c.rect(x - 1, y, 3, 1, steel)
            c.px(x - 1, y, light)
            c.px(x + 1, y, dark)
        if (y - top_y) % 18 == 0:                       # poprzeczki i krzyżulce
            c.hline(32 - half, y, 2 * half + 1, dark)
        if (y - top_y) % 18 < 18 and half > 6:
            k = (y - top_y) % 36
            if k < 18:
                c.px(32 - half + (k * 2 * half // 18), y, dark)
            else:
                c.px(32 + half - ((k - 18) * 2 * half // 18), y, dark)
    c.rect(24, 36, 16, 8, steel)                        # platforma pod światłem
    c.rect(24, 36, 16, 2, light)
    c.rect(24, 42, 16, 2, dark)
    c.rect(28, 22, 8, 14, METAL[2])                     # oprawa lampy
    c.rect(28, 26, 8, 8, BEACON)                        # czerwone światło
    c.rect(29, 27, 3, 3, hexc("#ffb0a0"))
    c.vline(31, 0, 22, steel)                           # antena
    c.vline(32, 0, 22, light)
    c.px(31, 0, BEACON)
    c.px(32, 0, BEACON)
    c.rect(10, h - 16, 44, 16, hexc("#5a6684"))         # betonowy fundament
    c.rect(10, h - 16, 44, 3, hexc("#8aa0d8"))
    c.rect(10, h - 4, 44, 4, hexc("#2c3552"))
    c.outline_alpha()
    c.save("l3_mast.png")


def draw_crate():
    """Skrzynia 32 x 32 (przeszkoda do przeskoczenia)."""
    c = Canvas(32, 32)
    c.rect(0, 0, 32, 32, WOOD[1])
    c.outline_box(0, 0, 32, 32, WOOD[2])
    c.outline_box(3, 3, 26, 26, WOOD[2])
    for i in range(26):
        c.px(3 + i, 3 + i, WOOD[2])
    c.hline(0, 0, 32, hexc("#e8b878"))
    c.vline(0, 0, 32, WOOD[0])
    c.outline_alpha()
    c.save("l3_crate.png")


def draw_dumpster():
    """Kontener na śmieci 64 x 40 (solidny, do wskoczenia): zielona skrzynia z pokrywą."""
    w, h = 64, 40
    c = Canvas(w, h)
    light, base, dark = GREEN
    c.rect(2, 8, w - 4, h - 8, base)
    c.rect(2, 8, 4, h - 8, dark)
    c.rect(w - 6, 8, 4, h - 8, light)
    c.rect(0, 4, w, 6, dark)
    c.rect(0, 4, w, 2, light)
    for x in range(10, w - 8, 10):
        c.vline(x, 12, 22, dark)
    c.rect(4, h - 6, 8, 6, METAL[2])
    c.rect(w - 12, h - 6, 8, 6, METAL[2])
    c.outline_alpha()
    c.save("l3_dumpster.png")


def draw_taxi():
    """Taksówka 112 x 40 (patrzy w prawo): żółty korpus, kabina, świecący znak TAXI, światła."""
    w, h = 112, 40
    c = Canvas(w, h)
    y1, y2, y3 = hexc("#ffd84a"), hexc("#e8b420"), hexc("#a87a10")
    c.rect(2, 16, w - 4, 16, y2)                        # korpus
    c.rect(2, 16, w - 4, 3, y1)
    c.rect(2, 28, w - 4, 4, y3)
    c.rect(22, 4, 62, 14, y2)                           # kabina
    c.rect(22, 4, 62, 2, y1)
    for x0, x1 in ((26, 50), (54, 80)):                 # szyby
        c.rect(x0, 7, x1 - x0, 9, hexc("#1c2a52"))
        c.rect(x0, 7, x1 - x0, 3, hexc("#34447a"))
    c.vline(52, 6, 11, y3)
    c.rect(44, 0, 20, 5, INK)                           # znak TAXI na dachu
    c.rect(45, 1, 18, 3, hexc("#fff8c8"))
    draw_text(c, 46, 1, "T", 1, INK) if False else None
    for x in range(46, 62, 4):
        c.px(x, 2, INK)
    c.rect(w - 6, 20, 5, 4, hexc("#fff3a0"))            # przednie światło
    c.rect(1, 20, 4, 4, hexc("#ff3a3a"))                # tylne światło
    for i in range(0, w - 8, 12):                       # szachownica na drzwiach
        c.rect(8 + i, 24, 6, 3, INK if (i // 12) % 2 == 0 else hexc("#fff8c8"))
    for cx in (22, 90):
        c.rect(cx - 9, 24, 18, 16, INK)
        c.rect(cx - 6, 26, 12, 13, hexc("#22222c"))
        c.rect(cx - 2, 30, 4, 4, METAL[0])
    c.outline_alpha()
    c.save("l3_taxi.png")


def draw_van():
    """Furgonetka Trelvos 128 x 56 (cała bryła jest solidna), jak l2_van, ale nocna: ciemniejsza, ze świecącymi światłami."""
    w, h = 128, 56
    c = Canvas(w, h)
    body, bl, bd = hexc("#aab6d0"), hexc("#d8e2f8"), hexc("#6a7898")
    c.rect(2, 4, 88, 40, body)
    c.rect(2, 4, 88, 3, bl)
    c.rect(2, 38, 88, 6, bd)
    c.rect(90, 14, 34, 30, body)
    c.rect(90, 14, 34, 3, bl)
    for i in range(10):
        c.rect(104 + i, 16 + i, 18 - i, 1, hexc("#34447a"))
    c.rect(94, 18, 12, 12, hexc("#34447a"))
    c.rect(94, 18, 12, 3, hexc("#6c88cc"))
    c.vline(89, 6, 38, bd)
    c.rect(8, 14, 74, 16, TRELVOS[1])
    c.rect(8, 14, 74, 2, TRELVOS[0])
    draw_text(c, 12, 18, "TRELVOS", 1, TRELVOS_DARK)
    c.rect(122, 34, 4, 5, hexc("#fff3a0"))              # przednie światło
    c.rect(0, 20, 3, 5, hexc("#ff3a3a"))                # tylne światło
    c.rect(0, 40, w, 6, bd)
    for cx in (24, 104):
        c.rect(cx - 10, 36, 20, 20, INK)
        c.rect(cx - 7, 39, 14, 15, hexc("#22222c"))
        c.rect(cx - 3, 43, 6, 6, METAL[0])
        c.rect(cx - 1, 45, 2, 2, METAL[2])
    c.outline_alpha()
    c.save("l3_van.png")


def draw_container():
    """Kontener towarowy 96 x 64 (solidny): ciemna czerwień, blacha falista, drzwi z zasuwami."""
    w, h = 96, 64
    c = Canvas(w, h)
    col = hexc("#a4483c"), hexc("#7c3028"), hexc("#521c1a")
    c.rect(0, 0, w, h, col[1])
    for x in range(3, w - 3, 4):
        c.vline(x, 5, h - 8, col[0])
        c.vline(x + 1, 5, h - 8, col[2])
    c.rect(0, 0, w, 5, col[0])
    c.rect(0, h - 4, w, 4, col[2])
    c.rect(w - 14, 5, 10, h - 8, col[2])
    for x in (w - 12, w - 8):
        c.vline(x, 8, h - 14, METAL[0])
    c.rect(8, 22, 30, 12, hexc("#d8d0b8"))
    c.rect(11, 25, 24, 2, hexc("#1d2a44"))
    c.rect(11, 29, 16, 2, hexc("#1d2a44"))
    c.outline_box(0, 0, w, h, INK)
    c.save("l3_container.png")


def draw_bench():
    """Ławka 64 x 32 (dekoracja)."""
    w, h = 64, 32
    c = Canvas(w, h)
    for y in (6, 11, 16):
        c.rect(4, y, 56, 4, WOOD[2])
        c.rect(4, y, 56, 1, WOOD[1])
    c.rect(4, 22, 56, 4, WOOD[2])
    c.rect(4, 22, 56, 1, WOOD[1])
    for x in (8, 52):
        c.rect(x, 4, 4, 28, METAL[2])
        c.rect(x, 26, 4, 6, METAL[1])
    c.outline_alpha()
    c.save("l3_bench.png")


def draw_hydrant():
    """Hydrant 16 x 32 (dekoracja)."""
    w, h = 16, 32
    c = Canvas(w, h)
    red, rl, rd = hexc("#b8382a"), hexc("#f07058"), hexc("#701c14")
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
    c.save("l3_hydrant.png")


def draw_tree():
    """Drzewo uliczne 64 x 128 w świetle księżyca (dekoracja)."""
    w, h = 64, 128
    c = Canvas(w, h)
    c.rect(28, 56, 8, 72, WOOD[2])
    c.rect(28, 56, 3, 72, WOOD[1])
    c.rect(24, 120, 16, 8, hexc("#3a4466"))
    for (cx, cy, r) in ((32, 30, 24), (16, 42, 14), (48, 42, 14), (32, 54, 14)):
        for y in range(cy - r, cy + r + 1):
            span = int((r * r - (y - cy) ** 2) ** 0.5)
            for x in range(cx - span, cx + span + 1):
                shade = LEAF[0] if (x - cx) + (y - cy) < -r // 2 else LEAF[2] if (x - cx) + (y - cy) > r // 2 else LEAF[1]
                c.px(x, y, shade)
    c.outline_alpha()
    c.save("l3_tree.png")


def draw_lamp():
    """Zapalona latarnia 100 x 300: słup i oprawa jak w assets/lampa włączona.png, a pełny żółty stożek światła zamieniamy na
    raster (wzór Bayera: gęsty przy lampie, rzadszy przy chodniku), jak raster nieba w tle. Dzięki temu stożek nie zasłania
    budynków za lampą. Żarówka jest w (62, 30), słup ma środek w x = 44."""
    src = ASSETS / "lampa włączona.png"
    if not src.exists():                                  # archiwum zip bez UTF-8 psuje nazwy plików z polskimi literami
        found = [p for p in ASSETS.glob("lampa w*") if not p.name.startswith("lampa wy")]   # "lampa wy..." to lampa wyłączona
        if not found:
            raise SystemExit("Brak pliku assets/lampa włączona.png (potrzebny do narysowania l3_lamp.png)")
        src = found[0]
    a = np.array(Image.open(src).convert("RGBA"))
    cone = (a[:, :, 0] == 245) & (a[:, :, 1] == 238) & (a[:, :, 2] == 147) & (a[:, :, 3] == 255)
    bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
    h = a.shape[0]
    for y in range(h):
        density = 0.9 - 0.65 * max(0.0, (y - 30) / (h - 30))
        for x in range(a.shape[1]):
            if cone[y, x] and bayer[y % 4, x % 4] >= density:
                a[y, x] = (0, 0, 0, 0)
    Image.fromarray(a, "RGBA").save(ASSETS / "l3_lamp.png")
    print("l3_lamp.png: 100x300")


def draw_phone():
    """Budka telefoniczna 32 x 64 (dekoracja): turkusowe światło w środku."""
    w, h = 32, 64
    c = Canvas(w, h)
    c.rect(2, 2, w - 4, h - 2, hexc("#8a2a3e"))         # czerwona obudowa
    c.rect(2, 2, 3, h - 2, hexc("#d0506a"))
    c.rect(w - 5, 2, 3, h - 2, hexc("#521a28"))
    c.rect(6, 8, w - 12, 40, CYAN[1])                   # szyba świecąca od środka
    c.rect(6, 8, w - 12, 12, CYAN[0])
    c.rect(6, 44, w - 12, 4, CYAN[2])
    c.hline(6, 28, w - 12, INK)
    c.vline(w // 2, 8, 40, INK)
    c.rect(4, 2, w - 8, 4, hexc("#f4f0e0"))             # napis nad szybą
    c.rect(2, h - 6, w - 4, 6, hexc("#521a28"))
    c.outline_alpha()
    c.save("l3_phone.png")


if __name__ == "__main__":
    draw_city()
    draw_pavement()
    draw_trelvos_hotel()
    draw_flat()
    draw_office()
    draw_trelvos_tower()
    draw_trelvos_sign()
    draw_gate()
    draw_club()
    draw_depot()
    draw_fire_escape()
    draw_mast()
    draw_crate()
    draw_dumpster()
    draw_taxi()
    draw_van()
    draw_container()
    draw_bench()
    draw_hydrant()
    draw_tree()
    draw_phone()
    draw_lamp()
