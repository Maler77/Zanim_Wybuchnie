"""Składa sprite sheet gracza (assets/player_sheet.png) z pojedynczych klatek 32x32 z katalogu assets/.

Uruchom z głównego katalogu repozytorium:   python tools/make_player_sheet.py
(wymaga biblioteki Pillow:  pip install pillow)

Jak to działa
  * Klatki narysowane ręcznie (pliki z assets/) trafiają do arkusza bez zmian.
  * Brakujące klatki (bieg, skok, spadanie, dash) skrypt składa z narysowanych: przestawia nogi i szalik,
    wycina nieruchome ręce i rysuje obie w ruchu (bliższa na ciele, dalsza pod nim), pochyla postać (dash), dodaje smugi. Używa tylko pikseli z Twoich klatek, więc styl jest ten sam.
  * Gdy narysujesz własną klatkę, wpisz ją w FRAMES niżej (zamiast generowanej) i uruchom skrypt jeszcze raz.

Układ arkusza (jeden WIERSZ = jedna animacja, klatki od lewej do prawej), zgodny z SPRITE_SHEETS.player
w src/js/animations.js. Na końcu skrypt wypisuje gotowy fragment do wklejenia w animations.js.
"""

import math
import sys
from pathlib import Path

from PIL import Image

ASSETS = Path(__file__).resolve().parent.parent / "assets"
OUT = ASSETS / "player_sheet.png"
SIZE = 32  # klatka ma SIZE x SIZE pikseli, postać patrzy w prawo, stopy na dolnej krawędzi

# --- Nazwy plików z narysowanymi klatkami (zmień tu, gdy je przemianujesz albo dorysujesz nowe) ---
IDLE_A = "Multimedia (1).png"            # stoi (oddech, 1. klatka)
IDLE_B = "Multimedia (2).png"            # stoi (oddech, 2. klatka)
STRIDE_A = "Multimedia.png"              # krok: prawa noga z przodu
STRIDE_B = "ludzik chód.png"             # krok (kolejne dwie kopie chód2 / chód3 są identyczne)
ROPE = ["lina1.png", "lina2.png", "lina 3.png"]   # huśta się na linie (ręka w górze)
WALL = ["spadanie ze sciany.png", "spadanie ze sciany2.png"]  # zsuwa się po ścianie
HURT = "obrazenia.png"
DEATH = ["smierc.png", "smierc 2.png"]

# Podział klatki na części: ciało (głowa, tułów, ręce) i nogi (4 dolne wiersze).
LEGS_TOP = 28
SPLIT_X = 18          # nogi: lewa < SPLIT_X <= prawa
MIRROR_AXIS = 37      # lustro nóg wokół osi bioder: x -> MIRROR_AXIS - x


def load(name):
    image = Image.open(ASSETS / name).convert("RGBA")
    if image.size != (SIZE, SIZE):
        sys.exit(f"{name}: klatka ma {image.size[0]}x{image.size[1]} px, a ma mieć {SIZE}x{SIZE}")
    return image


def blank():
    return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))


def pixels(image, box):
    """Lista (x, y, kolor) widocznych pikseli w prostokącie box = (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    px = image.load()
    return [(x, y, px[x, y]) for y in range(y0, y1) for x in range(x0, x1) if px[x, y][3] > 0]


def clear(image, box):
    x0, y0, x1, y1 = box
    px = image.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            px[x, y] = (0, 0, 0, 0)


def put(image, pts, dx=0, dy=0, mirror=False):
    """Wkleja piksele z listy pts z przesunięciem (dx, dy); mirror odbija je lustrzanie wokół osi bioder."""
    px = image.load()
    for x, y, color in pts:
        nx = (MIRROR_AXIS - x if mirror else x) + dx
        ny = y + dy
        if 0 <= nx < SIZE and 0 <= ny < SIZE:
            px[nx, ny] = color


def body_of(frame):
    return pixels(frame, (0, 0, SIZE, LEGS_TOP))


def legs_of(frame):
    left = pixels(frame, (0, LEGS_TOP, SPLIT_X, SIZE))
    right = pixels(frame, (SPLIT_X, LEGS_TOP, SIZE, SIZE))
    return left, right


def compose(body, left, right, body_dy=0, body_dx=0, left_d=(0, 0), right_d=(0, 0), mirror_legs=False):
    """Nowa klatka: nogi pod spodem, na nich ciało (może być przesunięte, np. opuszczone o 1 piksel przy kroku)."""
    image = blank()
    put(image, left, *left_d, mirror=mirror_legs)
    put(image, right, *right_d, mirror=mirror_legs)
    put(image, body, body_dx, body_dy)
    return image


# --- Ręce ---------------------------------------------------------------------------------------------
# Narysowane klatki mają obie ręce przyklejone do ciała (bliższa po prawej, dalsza po lewej, przy szaliku), więc
# w generowanych animacjach (bieg, skok, spadanie, dash) wycinamy je i rysujemy od nowa w ruchu, OBIE naraz.
# Kąty ręki liczymy od "w dół": 0 = wisi, 90 = do przodu, 180 = w górę, ujemne = do tyłu.
NEAR_SHOULDER = (20, 17)    # bliższa ręka (rysowana na wierzchu ciała)
FAR_SHOULDER = (17, 17)     # dalsza ręka (rysowana pod ciałem, wystaje tylko to, co nie jest zasłonięte)
NEAR_CLEAR = (21, 14, SIZE, 24)   # miejsce, gdzie narysowana klatka ma swoją bliższą rękę
FAR_CLEAR = (12, 16, 15, 25)      # ... i dalszą
ARM_NEAR = ((84, 82, 90), (50, 50, 56))     # (dłoń, rękaw) bliższej ręki
ARM_FAR = ((56, 54, 62), (32, 32, 37))      # dalsza jest ciemniejsza (w cieniu)
UPPER, FOREARM = 4.2, 4.2                    # długości ramienia i przedramienia w pikselach


def strip_arms(frame, near=True, far=True):
    """Kopia klatki bez rąk (tułów zostaje) z odnowionym czarnym konturem tam, gdzie była ręka."""
    out = frame.copy()
    if near:
        clear(out, NEAR_CLEAR)
    if far:
        clear(out, FAR_CLEAR)
    px = out.load()
    edge = []
    for y in range(SIZE):
        for x in range(SIZE):
            if px[x, y][3] or not any(
                0 <= x + dx < SIZE and 0 <= y + dy < SIZE and px[x + dx, y + dy][3]
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                continue
            # kontur tylko w miejscach po wyciętej ręce (nie dotykamy reszty klatki)
            inside = lambda box: box[0] - 1 <= x < box[2] + 1 and box[1] - 1 <= y < box[3] + 1
            if (near and inside(NEAR_CLEAR)) or (far and inside(FAR_CLEAR)):
                edge.append((x, y))
    for x, y in edge:
        px[x, y] = (0, 0, 0, 255)
    return out


def arm_layers(shoulder, upper, fore, colors):
    """Rysuje rękę (dwa odcinki, grubość 2 px) i jej kontur. Zwraca (ręka, kontur) jako osobne obrazy."""
    hand_color, sleeve = colors
    a1, a2 = math.radians(upper), math.radians(fore)
    sx, sy = shoulder
    ex, ey = sx + UPPER * math.sin(a1), sy + UPPER * math.cos(a1)
    hx, hy = ex + FOREARM * math.sin(a2), ey + FOREARM * math.cos(a2)
    arm = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = arm.load()

    def brush(x, y, color):
        for dx in (0, 1):
            for dy in (0, 1):
                nx, ny = int(round(x)) + dx - 1, int(round(y)) + dy - 1
                if 0 <= nx < SIZE and 0 <= ny < SIZE:
                    px[nx, ny] = (*color, 255)

    for (x0, y0), (x1, y1) in (((sx, sy), (ex, ey)), ((ex, ey), (hx, hy))):
        steps = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) * 2))
        for i in range(steps + 1):
            t = i / steps
            brush(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, sleeve)
    brush(hx, hy, hand_color)                        # dłoń

    outline = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    op = outline.load()
    for y in range(SIZE):
        for x in range(SIZE):
            if px[x, y][3]:
                continue
            if any(0 <= x + dx < SIZE and 0 <= y + dy < SIZE and px[x + dx, y + dy][3]
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                op[x, y] = (0, 0, 0, 255)
    return arm, outline


def with_arms(frame, near, far):
    """Dorysowuje obie ręce. near / far = (kąt ramienia, kąt przedramienia). Dalsza jest POD ciałem, bliższa NA nim."""
    back_arm, back_outline = arm_layers(FAR_SHOULDER, *far, ARM_FAR)
    behind = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    behind.alpha_composite(back_outline)
    behind.alpha_composite(back_arm)
    behind.alpha_composite(frame)
    front_arm, front_outline = arm_layers(NEAR_SHOULDER, *near, ARM_NEAR)
    behind.alpha_composite(front_outline)
    behind.alpha_composite(front_arm)
    return behind


# --- Brakujące animacje (składane z narysowanych klatek) ---

def make_run(idle, stride_a, stride_b):
    body = body_of(idle)
    idle_left, idle_right = legs_of(idle)
    a_left, a_right = legs_of(stride_a)
    b_left, b_right = legs_of(stride_b)
    frames = [
        compose(body_of(stride_a), a_left, a_right, body_dy=1),                                   # krok: prawa noga z przodu
        compose(body, idle_left, idle_right, right_d=(-1, -2)),                                   # przejście: prawa noga w górze
        compose(body_of(stride_b), b_left, b_right, body_dy=1, mirror_legs=True),                 # krok: lewa noga z przodu
        compose(body, idle_left, idle_right, left_d=(1, -2)),                                     # przejście: lewa noga w górze
    ]
    # Ręce biegną w przeciwfazie do nóg: bliższa ręka do tyłu, gdy bliższa noga jest z przodu, dalsza odwrotnie.
    # Przedramię jest zgięte do przodu (jak u biegacza). Para (ramię, przedramię) w stopniach.
    arms = [
        ((-60, 10), (55, 125)),
        ((-15, 60), (20, 95)),
        ((55, 125), (-60, 10)),
        ((20, 95), (-15, 60)),
    ]
    return [with_arms(strip_arms(frame), near, far) for frame, (near, far) in zip(frames, arms)]


SCARF = (0, 11, 10, 19)   # prostokąt z szalikiem (lewa strona klatki)


def with_scarf(frame, dx=0, dy=0):
    scarf = pixels(frame, SCARF)
    clear(frame, SCARF)
    put(frame, scarf, dx, dy)
    return frame


def make_jump(idle):
    body = body_of(idle)
    left, right = legs_of(idle)
    frames = []
    for near, far in (((92, 122), (45, 85)), ((105, 138), (60, 100))):       # obie ręce w górę, lekko do przodu
        frame = compose(body, left, right, left_d=(0, -2), right_d=(1, -3))      # nogi podkurczone
        frames.append(with_scarf(with_arms(strip_arms(frame), near, far), dy=2))  # szalik opada w dół
    return frames


def make_fall(idle):
    body = body_of(idle)
    left, right = legs_of(idle)
    frames = []
    for near, far, scarf_dy, spread in (((100, 140), (35, 75), -2, 1), ((115, 155), (50, 95), -3, 2)):
        frame = compose(body, left, right, left_d=(-spread, 0), right_d=(spread, 0))   # nogi rozrzucone
        frames.append(with_scarf(with_arms(strip_arms(frame), near, far), dy=scarf_dy))  # ręce machają, szalik leci w górę
    return frames


def shear(frame, leaning):
    """Pochyla ciało do przodu: górne wiersze przesuwa w prawo (w klatce jest miejsce, bo postać kończy się ok. x=27)."""
    out = blank()
    px_in, px_out = frame.load(), out.load()
    for y in range(SIZE):
        shift = round(max(0, LEGS_TOP - 1 - y) * leaning)
        for x in range(SIZE):
            if px_in[x, y][3] > 0 and 0 <= x + shift < SIZE:
                px_out[x + shift, y] = px_in[x, y]
    return out


def make_dash(idle):
    body = body_of(idle)
    left, right = legs_of(idle)
    frames = []
    for streak, leaning, near, far in ((5, 0.10, (-60, -40), (-45, -25)), (8, 0.12, (-70, -50), (-55, -35))):
        frame = compose(body, left, right, left_d=(-3, -1), right_d=(-4, -2))   # nogi ciągną się z tyłu
        frame = with_scarf(with_arms(strip_arms(frame), near, far), dx=-2, dy=-1)  # obie ręce wzdłuż pleców
        frame = shear(frame, leaning)
        px = frame.load()
        for y, length in ((14, streak), (20, streak - 2), (25, streak - 1)):   # smugi prędkości za plecami
            for x in range(0, length):
                if px[x, y][3] == 0:
                    px[x, y] = (205, 205, 215, 150 if x > 1 else 90)
        frames.append(frame)
    return frames


def main():
    idle_a, idle_b = load(IDLE_A), load(IDLE_B)
    stride_a, stride_b = load(STRIDE_A), load(STRIDE_B)
    rope = [load(name) for name in ROPE]
    wall = [load(name) for name in WALL]

    # (nazwa animacji, klatki, fps, loop). Kolejność = kolejność wierszy w arkuszu.
    animations = [
        ("idle",      [idle_a, idle_b],                          3,  True),
        ("run",       make_run(idle_a, stride_a, stride_b),      10, True),
        ("jump",      make_jump(idle_a),                   8,  False),
        ("fall",      make_fall(idle_a),             8,  True),
        ("dash",      make_dash(idle_a),                   12, True),
        ("wallslide", wall,                                      6,  True),
        ("swing",     [rope[0], rope[1], rope[2], rope[1]],      6,  True),   # tam i z powrotem
        ("hurt",      [load(HURT)],                              10, False),
        ("death",     [load(name) for name in DEATH],            4,  False),
    ]

    columns = max(len(frames) for _, frames, _, _ in animations)
    sheet = Image.new("RGBA", (columns * SIZE, len(animations) * SIZE), (0, 0, 0, 0))
    for row, (_, frames, _, _) in enumerate(animations):
        for column, frame in enumerate(frames):
            sheet.paste(frame, (column * SIZE, row * SIZE))
    sheet.save(OUT)
    print(f"zapisano {OUT.relative_to(ASSETS.parent)} ({sheet.width}x{sheet.height} px, {len(animations)} animacji)\n")

    print("Fragment do src/js/animations.js (SPRITE_SHEETS.player):")
    print(f"        frameWidth: {SIZE},\n        frameHeight: {SIZE},\n        animations: {{")
    for row, (name, frames, fps, loop) in enumerate(animations):
        extra = "" if loop else ", loop: false"
        print(f"            {name + ':':11} {{ row: {row}, frames: {len(frames)}, fps: {fps}{extra} }},")
    print("        },")


if __name__ == "__main__":
    main()