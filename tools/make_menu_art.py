"""Generuje grafiki menu głównego (assets/menu_*.png).

Uruchomienie z katalogu projektu:   python tools/make_menu_art.py
Wymaga Pillow i numpy. Wynik jest deterministyczny (ten sam plik za każdym razem).

Powstają:
  menu_background.png  640 x 360  tło ekranu tytułowego (nocne miasto, dach, księżyc)
  menu_logo.png        logo "ZANIM WYBUCHNIE" z bombą (pozycję iskry wypisuje skrypt)
  menu_spark.png       iskra przy lontie, 3 klatki po 11 x 11 (animacja w CSS)
  menu_btn*.png        przyciski 16 x 16 (9-slice: border-image w CSS, 6 px)
  menu_panel.png       ramka paneli 24 x 24 (9-slice, 8 px)
  menu_arrow.png       strzałka przy zaznaczonym przycisku
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

PLAYER_X = 134   # lewa krawędź klatki gracza w tle (CSS ustawia animowany sprite w tym samym miejscu)

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def hexc(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


# ----------------------------------------------------------------------------
#  TŁO 640 x 360
# ----------------------------------------------------------------------------
def make_background():
    night = Image.open(ASSETS / "l5_night.png").convert("RGBA")
    # Wycinek 640 x 360 z panoramy poziomu 5: wieżowiec z oświetlonym szczytem ląduje po prawej.
    x0, y0 = 396, 120
    img = night.crop((x0, y0, x0 + 640, y0 + 360)).convert("RGBA")
    px = img.load()
    d = ImageDraw.Draw(img)

    # --- księżyc z poświatą (dither Bayera, jak w pozostałych tłach)
    mx, my, mr = 112, 78, 21
    arr = np.array(img).astype(float)
    yy, xx = np.mgrid[0:360, 0:640]
    dist = np.hypot(xx - mx, yy - my)
    halo = np.clip(1 - (dist - mr) / 34.0, 0, 1) ** 1.6
    mask = (halo > BAYER[yy % 4, xx % 4]) & (dist > mr)
    arr[mask] = arr[mask] * 0.45 + np.array([150, 160, 215, 255]) * 0.55
    img = Image.fromarray(arr.astype(np.uint8), "RGBA")
    sky = img.copy()                                                          # niebo z poświatą, bez tarczy
    d = ImageDraw.Draw(img)
    d.ellipse((mx - mr, my - mr, mx + mr, my + mr), fill=hexc("#f4efc2"))
    d.ellipse((mx - mr + 4, my - mr + 3, mx + mr, my + mr), fill=hexc("#fbf8dc"))
    for cx, cy, r in [(-8, -6, 4), (7, 5, 5), (-4, 10, 3), (9, -9, 2)]:      # kratery
        d.ellipse((mx + cx - r, my + cy - r, mx + cx + r, my + cy + r), fill=hexc("#d9d19a"))
    # sierp: część tarczy zasłania cień, więc wklejamy tam z powrotem niebo
    shade = Image.new("L", img.size, 0)
    ImageDraw.Draw(shade).ellipse((mx - mr - 9, my - mr - 4, mx + mr - 9, my + mr - 4), fill=255)
    img.paste(sky, (0, 0), shade)
    d = ImageDraw.Draw(img)

    # --- dach na pierwszym planie (lewa strona), tam stoi gracz
    roof_top = 292
    roof_w = 300
    wall = hexc("#0a1024")
    brick = hexc("#0e1630")
    edge_hi = hexc("#3a4c80")
    edge_mid = hexc("#26335a")
    d.rectangle((0, roof_top, roof_w, 360), fill=wall)
    for y in range(roof_top + 10, 360, 8):                                  # cegły
        off = 0 if ((y - roof_top) // 8) % 2 == 0 else 8
        d.line((0, y, roof_w, y), fill=brick)
        for x in range(off, roof_w, 16):
            d.line((x, y, x, y + 7), fill=brick)
    d.rectangle((0, roof_top, roof_w, roof_top + 1), fill=edge_hi)          # krawędź dachu
    d.rectangle((0, roof_top + 2, roof_w, roof_top + 5), fill=edge_mid)
    d.rectangle((0, roof_top + 6, roof_w, roof_top + 7), fill=hexc("#101a38"))
    d.rectangle((roof_w - 1, roof_top, roof_w, 360), fill=hexc("#16213f"))       # krawędź boczna dachu

    # zbiornik na wodę, antena i klimatyzator na dachu (sylwetki)
    tank = hexc("#080d1e")
    tank_hi = hexc("#1b2748")
    d.rectangle((22, roof_top - 34, 62, roof_top - 8), fill=tank)           # korpus
    d.rectangle((22, roof_top - 34, 24, roof_top - 8), fill=tank_hi)
    d.polygon([(20, roof_top - 34), (42, roof_top - 46), (64, roof_top - 34)], fill=tank)
    d.line((26, roof_top - 8, 26, roof_top - 1), fill=tank)                 # nogi
    d.line((58, roof_top - 8, 58, roof_top - 1), fill=tank)
    for yb in (roof_top - 28, roof_top - 18):                                # obręcze
        d.line((22, yb, 62, yb), fill=hexc("#0f1731"))
    d.rectangle((226, roof_top - 18, 262, roof_top - 1), fill=tank)         # klimatyzator
    d.rectangle((226, roof_top - 18, 262, roof_top - 17), fill=tank_hi)
    for x in range(230, 260, 5):
        d.line((x, roof_top - 14, x, roof_top - 5), fill=hexc("#0f1731"))
    d.line((196, roof_top - 1, 196, roof_top - 64), fill=tank)              # antena
    d.line((186, roof_top - 52, 206, roof_top - 52), fill=tank)
    d.line((189, roof_top - 42, 203, roof_top - 42), fill=tank)
    d.rectangle((195, roof_top - 66, 197, roof_top - 64), fill=hexc("#ff4a3a"))   # czerwona lampka

    # --- gracz: klatka 0 wiersza idle z player_sheet (32 x 48), stopy na krawędzi dachu
    sheet = Image.open(ASSETS / "player_sheet.png").convert("RGBA")
    frame = sheet.crop((0, 0, 32, 32))
    foot = frame.getbbox()[3]                                                  # ostatni wiersz z pikselami
    img.alpha_composite(frame, (PLAYER_X, roof_top - foot + 2))
    print("gracz w menu: left", PLAYER_X, "top", roof_top - foot + 2)

    # --- winieta (ciemniejsze rogi), żeby logo i przyciski się wyróżniały
    arr = np.array(img).astype(float)
    yy, xx = np.mgrid[0:360, 0:640]
    v = np.hypot((xx - 320) / 330.0, (yy - 170) / 230.0)
    dark = np.clip((v - 0.72) / 0.6, 0, 1)
    dm = dark > BAYER[yy % 4, xx % 4] * 0.9
    arr[dm, :3] *= 0.55
    # delikatne rozjaśnienie nieba przy horyzoncie (ciepła łuna miasta)
    out = Image.fromarray(arr.astype(np.uint8), "RGBA")
    out.save(ASSETS / "menu_background.png")
    print("menu_background.png", out.size)


# ----------------------------------------------------------------------------
#  LOGO "ZANIM WYBUCHNIE"
# ----------------------------------------------------------------------------
GLYPHS = {
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "N": ["10001", "11001", "11001", "10101", "10011", "10011", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
}


def word_mask(word, scale):
    cols = len(word) * 6 - 1
    m = np.zeros((7 * scale, cols * scale), bool)
    for i, ch in enumerate(word):
        for r, row in enumerate(GLYPHS[ch]):
            for c, v in enumerate(row):
                if v == "1":
                    m[r * scale:(r + 1) * scale, (i * 6 + c) * scale:(i * 6 + c + 1) * scale] = True
    return m


def shift(m, dx, dy):
    out = np.zeros_like(m)
    h, w = m.shape
    ys, ye = max(dy, 0), min(h + dy, h)
    xs, xe = max(dx, 0), min(w + dx, w)
    out[ys:ye, xs:xe] = m[ys - dy:ye - dy, xs - dx:xe - dx]
    return out


def dilate(m, r):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= shift(m, dx, dy)
    return out


GRADIENT = [hexc("#fff3b0"), hexc("#ffd24a"), hexc("#ff9a2e"), hexc("#ee5a24"), hexc("#c9361c")]


def paint_word(canvas, word, scale, ox, oy):
    """Rysuje słowo na canvas (numpy RGBA): wytłoczenie, obrys, ściana z gradientem i fazą."""
    mask = word_mask(word, scale)
    h, w = mask.shape
    depth = max(3, scale // 2)
    full = np.zeros((h + 2 * 3 + depth, w + 2 * 3 + depth), bool)
    base = np.zeros_like(full)
    base[3:3 + h, 3:3 + w] = mask
    ext = np.zeros_like(full)
    for k in range(1, depth + 1):
        ext |= shift(base, k, k)
    outline = dilate(base | ext, 2)
    layer = np.zeros(full.shape + (4,), np.uint8)
    layer[outline] = hexc("#05060f")
    layer[ext] = hexc("#5b1a12")
    layer[shift(ext, 0, 0) & ~shift(base, 1, 1) & ext & ~base] = hexc("#5b1a12")
    # ciemniejszy dolny fragment wytłoczenia
    low = ext & ~shift(ext, 0, -scale // 2)
    layer[low & ~base] = hexc("#33100c")
    # ściana liter z gradientem w pasach
    ys = np.nonzero(base.any(axis=1))[0]
    y0, y1 = ys.min(), ys.max()
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, (y1 - y0))
        band = min(len(GRADIENT) - 1, int(t * len(GRADIENT)))
        row = base[y]
        layer[y][row] = GRADIENT[band]
    # faza: jasna krawędź od góry i z lewej, ciemna od dołu i z prawej
    top = base & ~shift(base, 0, 1)
    left = base & ~shift(base, 1, 0)
    bottom = base & ~shift(base, 0, -1)
    right = base & ~shift(base, -1, 0)
    t = max(1, scale // 3)
    for k in range(t):
        layer[shift(top, 0, k) & base] = hexc("#fffbe0")
        layer[shift(left, k, 0) & base & ~shift(top, 0, k)] = hexc("#fff0a0")
        layer[shift(bottom, 0, -k) & base] = hexc("#a82a16")
        layer[shift(right, -k, 0) & base & ~shift(bottom, 0, -k)] = hexc("#c9361c")
    # wklej na canvas
    H, W = layer.shape[:2]
    reg = canvas[oy:oy + H, ox:ox + W]
    m = layer[..., 3] > 0
    reg[m] = layer[m]
    return W, H


def draw_bomb(canvas, cx, cy, r):
    """Pixel-artowa bomba: czarny korpus, błysk, kołnierz i lont. Zwraca punkt końca lontu."""
    img = Image.fromarray(canvas)
    d = ImageDraw.Draw(img)
    d.ellipse((cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2), fill=hexc("#05060f"))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=hexc("#1c2033"))
    d.ellipse((cx - r + 2, cy - r + 2, cx + r - 3, cy + r - 3), fill=hexc("#2b3150"))
    d.ellipse((cx - r + 4, cy - r + 4, cx + r - 8, cy + r - 8), fill=hexc("#4a5380"))      # błysk
    d.ellipse((cx - r + 5, cy - r + 5, cx - r + 9, cy - r + 9), fill=hexc("#aab6e8"))
    # czerwony pas ostrzegawczy na dole korpusu
    d.arc((cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1), 30, 150, fill=hexc("#c9361c"), width=3)
    # kołnierz i lont
    d.rectangle((cx - 5, cy - r - 6, cx + 4, cy - r + 1), fill=hexc("#05060f"))
    d.rectangle((cx - 4, cy - r - 5, cx + 3, cy - r), fill=hexc("#6b7388"))
    d.rectangle((cx - 4, cy - r - 5, cx + 3, cy - r - 4), fill=hexc("#aab3c8"))
    pts = [(cx, cy - r - 6), (cx + 1, cy - r - 10), (cx + 5, cy - r - 13), (cx + 10, cy - r - 12), (cx + 13, cy - r - 16)]
    d.line(pts, fill=hexc("#05060f"), width=4)
    d.line(pts, fill=hexc("#c9a46a"), width=2)
    canvas[:] = np.array(img)
    return pts[-1]


def make_logo():
    W, H = 400, 132
    canvas = np.zeros((H, W, 4), np.uint8)
    # górny wiersz: ZANIM + bomba, wyśrodkowany nad drugim
    zw, _ = word_mask("ZANIM", 5).shape[::-1]
    bomb_r = 15
    group = zw + 8 + 2 * bomb_r + 16
    gx = (W - group) // 2
    paint_word(canvas, "ZANIM", 5, gx, 18)
    bx, by = gx + zw + 8 + bomb_r + 6, 18 + 22
    tip = draw_bomb(canvas, bx, by, bomb_r)
    paint_word(canvas, "WYBUCHNIE", 7, (W - (9 * 6 - 1) * 7) // 2 - 3, 74)
    Image.fromarray(canvas).save(ASSETS / "menu_logo.png")
    print("menu_logo.png", (W, H), "iskra (koniec lontu):", tip)
    return tip


# ----------------------------------------------------------------------------
#  ISKRA 3 x (11 x 11)
# ----------------------------------------------------------------------------
def make_spark():
    sheet = Image.new("RGBA", (33, 11), (0, 0, 0, 0))
    frames = [
        ["00000100000", "00100100100", "00010101000", "00001110000", "11111111111", "00001110000", "00010101000", "00100100100", "00000100000"],
        ["00000000000", "00010001000", "00001010000", "00000100000", "00111111100", "00000100000", "00001010000", "00010001000", "00000000000"],
        ["00001000000", "00000100010", "10000100100", "01001110000", "00111111100", "00001110010", "00100100001", "00010100000", "00000100000"],
    ]
    cols = [hexc("#fff8c8"), hexc("#ffc83a"), hexc("#fff0a0")]
    for i, rows in enumerate(frames):
        for y, row in enumerate(rows):
            for x, v in enumerate(row):
                if v == "1":
                    sheet.putpixel((i * 11 + x, y + 1), cols[i])
        sheet.putpixel((i * 11 + 5, 5), hexc("#ffffff"))
    sheet.save(ASSETS / "menu_spark.png")


# ----------------------------------------------------------------------------
#  PRZYCISKI (16 x 16, 9-slice 6 px), RAMKA PANELU (24 x 24, 9-slice 8 px), STRZAŁKA
# ----------------------------------------------------------------------------
def carve(img, size, k):
    """Ścina rogi o k pikseli (pixel-artowe zaokrąglenie)."""
    for i in range(k):
        for j in range(k - i):
            for (x, y) in [(i, j), (size - 1 - i, j), (i, size - 1 - j), (size - 1 - i, size - 1 - j)]:
                img.putpixel((x, y), (0, 0, 0, 0))


def make_button(name, outline, edge, fill_top, fill, fill_bot, shine):
    n = 16
    img = Image.new("RGBA", (n, n), hexc(outline))
    d = ImageDraw.Draw(img)
    d.rectangle((1, 1, n - 2, n - 2), fill=hexc(edge))
    d.rectangle((2, 2, n - 3, n - 3), fill=hexc(fill))
    d.rectangle((2, 2, n - 3, 4), fill=hexc(fill_top))
    d.rectangle((2, n - 5, n - 3, n - 3), fill=hexc(fill_bot))
    d.line((3, 2, n - 4, 2), fill=hexc(shine))
    carve(img, n, 2)
    # wewnętrzny narożnik krawędzi (żeby obrys był ciągły po ścięciu)
    for (x, y) in [(1, 1), (n - 2, 1), (1, n - 2), (n - 2, n - 2)]:
        img.putpixel((x, y), hexc(outline))
    img.save(ASSETS / f"{name}.png")


def make_panel():
    n = 24
    img = Image.new("RGBA", (n, n), hexc("#05060f"))
    d = ImageDraw.Draw(img)
    d.rectangle((1, 1, n - 2, n - 2), fill=hexc("#3a4e63"))
    d.rectangle((2, 2, n - 3, n - 3), fill=hexc("#1c2838"))
    d.rectangle((3, 3, n - 4, n - 4), fill=hexc("#2a3b52"))
    d.rectangle((4, 4, n - 5, n - 5), fill=(11, 16, 32, 232))
    d.line((2, 2, n - 3, 2), fill=hexc("#5f7896"))
    carve(img, n, 3)
    for (x, y) in [(2, 2), (n - 3, 2), (2, n - 3), (n - 3, n - 3)]:
        img.putpixel((x, y), hexc("#05060f"))
    img.save(ASSETS / "menu_panel.png")


def make_arrow():
    rows = ["1100000", "1111000", "1122110", "1222211", "1222221", "1222211", "1122110", "1111000", "1100000"]
    img = Image.new("RGBA", (7, 9), (0, 0, 0, 0))
    for y, r in enumerate(rows):
        for x, v in enumerate(r):
            if v == "1":
                img.putpixel((x, y), hexc("#05060f"))
            elif v == "2":
                img.putpixel((x, y), hexc("#ffd24a") if x < 4 else hexc("#ff9a2e"))
    img.save(ASSETS / "menu_arrow.png")


def make_ui():
    # normalny: granat ze stalową krawędzią
    make_button("menu_btn", "#05060f", "#3a4e63", "#1d2b44", "#16213a", "#0f1729", "#4d6482")
    # zaznaczony: pomarańczowa krawędź i jaśniejsze wnętrze
    make_button("menu_btn_hover", "#05060f", "#ff9a2e", "#2c3a5e", "#222e50", "#18213c", "#ffd27a")
    # główny (Graj): czerwono-pomarańczowy jak bomba
    make_button("menu_btn_primary", "#05060f", "#ffb347", "#f0702b", "#d9482b", "#a8301c", "#ffe08a")
    make_button("menu_btn_primary_hover", "#05060f", "#fff3b0", "#ff9a3d", "#f06a2c", "#c9431f", "#ffffff")
    # nieaktywny
    make_button("menu_btn_disabled", "#05060f", "#252f3c", "#171d28", "#131822", "#0e121a", "#252f3c")
    make_panel()
    make_arrow()
    make_spark()


if __name__ == "__main__":
    make_background()
    make_logo()
    make_ui()
