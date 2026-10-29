"""Generuje poziom 7 (bossfight z Kamilem we wnętrzu siedziby Trelvosu) do src/data/levels/poziom-7.json.

Uruchom z głównego katalogu repozytorium:   python "tools/make level 7.py"
Grafiki do niego robi "tools/make level 7 art.py" (pliki assets/l7_*.png); ten skrypt jest też źródłem rozmiarów
pomieszczeń i rekwizytów (stałe na górze), więc zmieniając je uruchom oba skrypty.

PLAN POZIOMU (współrzędne w px gry, y w dół; poziom ma 7300 x 1400 px, sufit na y = 700)
Tryb "boss": od początku goni cię Kamil (zawsze wie, gdzie jesteś). Dotknięcie = przegrana. Trzeba rozbroić 3 panele
serwisowe (pytania "hard"). Każdy panel stoi w miejscu, do którego Kamil NIE WEJDZIE (nie ma haka, dasha ani skoczni,
nie skoczy wyżej niż ok. 90 px i nie zmieści się w niskim przejściu), a cała trasa główna jest dla niego przejezdna
(przepaście do 112 px, stopnie do 64 px, szyb z dwiema ścianami, na którym wspina się wall-jumpem jak gracz).
Po rozbrojeniu panelu Kamil gubi trop i wraca z odległego punktu `respawns` (silnik, game.js: defuse()).

  0-1190      DOK SERWISOWY (podłoga y = 1200): skrzynie i wózek do przeskoczenia, przepaść z kolcami
  1250-3000   MAGAZYN: skocznia -> GALERIA (panel 1 po przeskoczeniu 260 px haka na belkę suwnicy)
  3120-4040   STOŁÓWKA I SZATNIE PERSONELU: stoły i lada, potem niskie przejście pod grodzią
  4040-4216   SZYB: dwie ściany co 96 px, wspinaczka wall-jumpem o 300 px w górę do korytarza technicznego
  4216-5700   KORYTARZ TECHNICZNY (y = 900): rów kablowy z kolcami, kratka wentylacyjna -> KANAŁ (46 px wysokości,
              panel 2), wyjście skocznią przez drugą kratkę
  5700-7300   SERWEROWNIA (y = 1100): przepaść z kolcami, skocznia -> POMOST 150 px nad podłogą, dash 190 px, panel 3

Elementy dekoracyjne to platformy z "solid": false i teksturą (kolejność na liście = kolejność rysowania).
Kolizję daje osobna, niewidoczna platforma (color "transparent"). Kratki w korytarzu to platformy "oneWay": stoisz na
nich, a klawisz S pozwala przepaść w dół (Kamil nie umie [S], więc nie wpada do kanału).
"""

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "src" / "data" / "levels" / "poziom-7.json"

# Przesunięcia kolejnych części (w px): wstawki wydłużające trasę. Układ "wzorcowy" (bez wstawek) miał 7300 px.
D1 = 452                 # dłuższy dok (przed magazynem)
D2 = D1 + 900            # dłuższy magazyn (za galerią)
D3 = D2 + 560            # dłuższa stołówka (przed szybem)
D4 = D3 + 640            # dłuższy korytarz (za kanałem)
D5 = D4 + 400            # dłuższa serwerownia (przed przepaścią i pomostem)

W, H = 7300 + D5, 1400
CEIL_TOP, CEIL = 560, 700            # pas sufitu: y 560-700 (nad nim nic nie ma)
F1, F4, F5 = 1200, 900, 1100         # podłogi: dok-magazyn-stołówka, korytarz, serwerownia

# ---------- rozmiary pomieszczeń i rekwizytów (używa ich też skrypt grafik) ----------
WALL_DOCK = dict(x=0, w=1190 + D1, y=CEIL, h=F1 - CEIL)
WALL_STORE = dict(x=1190 + D1, w=1870 + D2 - D1, y=CEIL, h=F1 - CEIL)
WALL_CANTEEN = dict(x=3060 + D2, w=980 + D3 - D2, y=CEIL, h=F1 - CEIL)
WALL_SHAFT = dict(x=4120 + D3, w=96, y=CEIL, h=F1 - CEIL)
WALL_CORRIDOR = dict(x=4216 + D3, w=1484 + D4 - D3, y=CEIL, h=F4 - CEIL)
WALL_SERVER = dict(x=5700 + D4, w=1600 + D5 - D4, y=CEIL, h=F5 - CEIL)
BULKHEAD = dict(x=4040 + D3, w=80, y=CEIL, h=1130 - CEIL)    # grodzia: pod nią (y 1130-1200) jest przejście 70 px

CRATE = dict(w=64, h=64)
PALLET = dict(w=32, h=32)
CART = dict(w=96, h=48)
TABLE = dict(w=96, h=40)
COUNTER = dict(w=192, h=64)
UPS = dict(w=64, h=64)
COOLER = dict(w=96, h=64)

# Galeria magazynu: lewa część (skocznia ją wynosi), przerwa 260 px (hak), prawa część z panelem 1
SPRING1 = dict(x=1868 + D1, w=64)                      # skocznia przy galerii (środek +32)
GL = dict(x=1934 + D1, w=216, y=1056)                  # galeria lewa (wylądowanie ze skoczni)
GR = dict(x=2410 + D1, w=390, y=1076)                  # galeria prawa (20 px niżej niż lewa)
ANCHOR = dict(x=2280 + D1, y=918)                      # punkt haka: wózek suwnicy (środek 24 x 24)
HOIST = dict(x=ANCHOR["x"] - 16, y=850, w=32, h=80)    # wózek z hakiem; pierścień haka dokładnie w ANCHOR

# Korytarz techniczny: kratki nad kanałem wentylacyjnym
PIT_SHAFT = dict(x=4560 + D3, w=112, floor=964)        # płytki rów kablowy z kolcami (64 px): Kamil z niego wyskoczy
HATCH1 = dict(x=4900 + D3, w=96)                       # kratka wejściowa (S = przepadnij w dół)
TUNNEL = dict(x=4996 + D3, w=304, ceil=994, floor=1040)  # kanał: wysokość 46 px, gracz (44 px) się mieści, Kamil (48 px) nie
HATCH2 = dict(x=5300 + D3, w=128)                      # kratka wyjściowa, pod nią skocznia
SLAB_TOP = F4

# Serwerownia
PIT_SERVER = dict(x=6280 + D5, w=112, floor=1300)
SPRING3 = dict(x=6548 + D5, w=64)                      # skocznia pod pomost
T1 = dict(x=6620 + D5, w=140, y=950)                   # pomost 1 (150 px nad podłogą)
T2 = dict(x=6950 + D5, w=200, y=950)                   # pomost 2: przerwa 190 px = dash

PANELS = [  # (x środka, y powierzchni)
    (2640 + D1, GR["y"]),
    (5150 + D3, TUNNEL["floor"]),
    (7060 + D5, T2["y"]),
]


def build():
    platforms, checkpoints, spikes, pads = [], [], [], []
    obstacles, grounds = [], []        # (x0, x1, podłoga) rekwizyty i odcinki podłogi: do wyboru miejsc pojawiania się Kamila

    def solid(x, y, w, h, texture=None, mode=None, **extra):
        item = {"x": x, "y": y, "w": w, "h": h, "texture": texture or "platform"}
        if mode:
            item["textureMode"] = mode
        if texture is None:
            item["color"] = "transparent"
        item.update(extra)
        platforms.append(item)
        return item

    def decor(x, y, w, h, texture, mode=None):
        return solid(x, y, w, h, texture, mode, solid=False)

    def ground(x0, x1, top, bottom=H):
        """Podłoga z betonową masą pod spodem: niewidoczna kolizja + płyta posadzki i beton."""
        solid(x0, top, x1 - x0, bottom - top)
        grounds.append((x0, x1, top))
        decor(x0, top, x1 - x0, 32, "assets/l7_floor.png", "tile")
        if bottom - top > 32:
            decor(x0, top + 32, x1 - x0, bottom - top - 32, "assets/l7_concrete.png", "tile")

    def pit(x, w, top, floor):
        """Przepaść z kolcami na dnie (ciemny szyb w tle)."""
        decor(x, top, w, floor - top, "assets/l7_shaft.png", "tile")
        solid(x, floor, w, 8, "assets/l7_concrete.png", "tile")
        spikes.append({"x": x, "y": floor - 8, "w": w, "h": 8})

    def crate(x, floor):
        obstacles.append((x, x + CRATE["w"], floor))
        solid(x, floor - CRATE["h"], CRATE["w"], CRATE["h"], "assets/l7_crate.png")

    def pallet(x, floor):
        obstacles.append((x, x + PALLET["w"], floor))
        solid(x, floor - PALLET["h"], PALLET["w"], PALLET["h"], "assets/l7_pallet.png")

    def cart(x, floor):
        obstacles.append((x, x + CART["w"], floor))
        solid(x, floor - CART["h"], CART["w"], CART["h"], "assets/l7_cart.png")

    def table(x, floor):
        obstacles.append((x, x + TABLE["w"], floor))
        solid(x, floor - TABLE["h"], TABLE["w"], TABLE["h"], "assets/l7_table.png")

    def counter(x, floor):
        obstacles.append((x, x + COUNTER["w"], floor))
        solid(x, floor - COUNTER["h"], COUNTER["w"], COUNTER["h"], "assets/l7_counter.png")

    def barrier(pit_def, top):
        decor(pit_def["x"] - 8, top - 40, pit_def["w"] + 16, 40, "assets/l7_pit_barrier.png")

    # ---------- ściany pomieszczeń (tło) i sufit ----------
    for key, wall in (("dock", WALL_DOCK), ("store", WALL_STORE), ("canteen", WALL_CANTEEN),
                      ("server", WALL_SERVER), ("corridor", WALL_CORRIDOR), ("shaft", WALL_SHAFT)):
        decor(wall["x"], wall["y"], wall["w"], wall["h"], f"assets/l7_wall_{key}.png")
    solid(0, CEIL_TOP, W, CEIL - CEIL_TOP, "assets/l7_ceiling.png", "tile")

    # ---------- podłogi ----------
    pit1, pit2 = dict(x=1138 + D1, w=112), dict(x=3000 + D2, w=112)
    ground(0, pit1["x"], F1)                                      # dok
    ground(pit1["x"] + pit1["w"], pit2["x"], F1)                  # magazyn
    ground(pit2["x"] + pit2["w"], 4216 + D3, F1)                  # stołówka i dno szybu
    ground(4216 + D3, PIT_SHAFT["x"], F4)                         # korytarz
    ground(PIT_SHAFT["x"] + PIT_SHAFT["w"], HATCH1["x"], F4)
    ground(HATCH2["x"] + HATCH2["w"], 5700 + D4, F4)
    ground(5700 + D4, PIT_SERVER["x"], F5)                        # serwerownia
    ground(PIT_SERVER["x"] + PIT_SERVER["w"], W, F5)

    # ---------- przepaści z kolcami ----------
    pit(pit1["x"], pit1["w"], F1, 1392)
    pit(pit2["x"], pit2["w"], F1, 1392)
    pit(PIT_SHAFT["x"], PIT_SHAFT["w"], F4, PIT_SHAFT["floor"])
    pit(PIT_SERVER["x"], PIT_SERVER["w"], F5, PIT_SERVER["floor"])
    barrier(PIT_SHAFT, F4)

    # ---------- dok serwisowy (0 - 1590) ----------
    pallet(420, F1)
    crate(600, F1)
    cart(830, F1)
    pallet(1010, F1)
    crate(1180, F1)
    pallet(1260, F1)
    crate(1292, F1)

    # ---------- magazyn: przy galerii żadnych skrzyń (nic, po czym Kamil mógłby na nią wejść) ----------
    crate(1440 + D1, F1)
    pallet(1640 + D1, F1)
    # galeria: podpory i poręcze (dekoracje), płyty (solidne)
    for g in (GL, GR):
        for px in range(g["x"] + 12, g["x"] + g["w"] - 8, 130):
            decor(px, g["y"] + 14, 12, F1 - g["y"] - 14, "assets/l7_post.png", "tile")
        decor(g["x"], g["y"] - 30, g["w"], 30, "assets/l7_rail.png", "tile")
    solid(GL["x"], GL["y"], GL["w"], 14, "assets/l7_catwalk.png", "tile")
    solid(GR["x"], GR["y"], GR["w"], 14, "assets/l7_catwalk.png", "tile")
    # wózek suwnicy z hakiem (pierścień = punkt zaczepienia)
    decor(HOIST["x"], HOIST["y"], HOIST["w"], HOIST["h"], "assets/l7_hoist.png")
    platforms.append({"x": ANCHOR["x"] - 12, "y": ANCHOR["y"] - 12, "w": 24, "h": 24, "texture": "platform",
                      "color": "transparent", "solid": False, "grappleable": True})
    pads.append({"x": SPRING1["x"], "y": F1 - 8, "w": SPRING1["w"], "h": 8})
    # dalsza część magazynu (za galerią, min. 250 px od jej krawędzi)
    gr_end = GR["x"] + GR["w"]
    crate(gr_end + 300, F1)
    pallet(gr_end + 480, F1)
    crate(gr_end + 512, F1)
    cart(gr_end + 660, F1)
    crate(gr_end + 860, F1)

    # ---------- stołówka (za przepaścią) ----------
    o = pit2["x"] + pit2["w"]
    table(o + 170, F1)
    counter(o + 400, F1)
    table(o + 680, F1)
    cart(o + 860, F1)
    counter(o + 1040, F1)
    table(o + 1240, F1)
    # grodzia nad przejściem (kolizja: y 700-1130, wysokość przejścia 70 px)
    solid(BULKHEAD["x"], BULKHEAD["y"], BULKHEAD["w"], BULKHEAD["h"], "assets/l7_bulkhead.png")

    # ---------- korytarz techniczny ----------
    crate(4320 + D3, F4)
    pallet(4780 + D3, F4)
    # kanał wentylacyjny: dno 1040, strop (płyta) 900-994, otwory pod kratkami
    h1, t, h2 = HATCH1, TUNNEL, HATCH2
    solid(h1["x"], t["floor"], h2["x"] + h2["w"] - h1["x"], H - t["floor"])             # dno otworów i kanału
    solid(t["x"], SLAB_TOP, t["w"], t["ceil"] - SLAB_TOP)                                # strop kanału
    decor(h1["x"], SLAB_TOP, h2["x"] + h2["w"] - h1["x"], t["floor"] - SLAB_TOP, "assets/l7_duct_shaft.png", "tile")
    decor(t["x"], SLAB_TOP, t["w"], 32, "assets/l7_floor.png", "tile")
    decor(t["x"], SLAB_TOP + 32, t["w"], t["ceil"] - SLAB_TOP - 32, "assets/l7_concrete.png", "tile")
    decor(t["x"], t["ceil"], t["w"], t["floor"] - t["ceil"], "assets/l7_tunnel.png")
    decor(h1["x"], t["floor"], h2["x"] + h2["w"] - h1["x"], H - t["floor"], "assets/l7_concrete.png", "tile")
    solid(h1["x"], SLAB_TOP, h1["w"], 8, "assets/l7_grate.png", "tile", oneWay=True)
    solid(h2["x"], SLAB_TOP, h2["w"], 8, "assets/l7_grate.png", "tile", oneWay=True)
    pads.append({"x": h2["x"] + 32, "y": t["floor"] - 8, "w": 64, "h": 8})
    # dalsza część korytarza (za kanałem)
    c0 = h2["x"] + h2["w"]
    crate(c0 + 150, F4)
    pallet(c0 + 330, F4)
    crate(c0 + 362, F4)
    cart(c0 + 540, F4)
    crate(c0 + 730, F4)

    # ---------- serwerownia ----------
    s0 = 5700 + D4
    for dx, kind in ((160, UPS), (340, COOLER), (540, UPS), (700, COOLER)):
        obstacles.append((s0 + dx, s0 + dx + kind["w"], F5))
        solid(s0 + dx, F5 - kind["h"], kind["w"], kind["h"], "assets/l7_ups.png" if kind is UPS else "assets/l7_cooler.png")
    barrier(PIT_SERVER, F5)
    pads.append({"x": SPRING3["x"], "y": F5 - 8, "w": SPRING3["w"], "h": 8})
    for g in (T1, T2):
        for px in (g["x"] + 8, g["x"] + g["w"] - 20):
            decor(px, g["y"] + 14, 12, F5 - g["y"] - 14, "assets/l7_post.png", "tile")
        decor(g["x"], g["y"] - 30, g["w"], 30, "assets/l7_rail.png", "tile")
        solid(g["x"], g["y"], g["w"], 14, "assets/l7_catwalk.png", "tile")

    # ---------- panele ----------
    bombs = [{"x": x, "y": y} for x, y in PANELS]

    # ---------- Kamil ----------
    def spot(x, floor):
        """Najbliższe wolne miejsce na podłodze `floor` przy x: poza rekwizytami (z zapasem) i z podłogą pod całym ciałem."""
        def clear(cx):
            if not any(a + 40 <= cx - 14 and cx + 14 <= b - 40 for a, b, f in grounds if f == floor):
                return False
            return not any(a - 40 < cx + 14 and cx - 14 < b + 40 for a, b, f in obstacles if f == floor)
        for step in range(0, 600, 10):
            for cx in (x + step, x - step):
                if clear(cx):
                    return cx
        raise ValueError(f"brak miejsca przy x={x}")

    def spawn(x, y, stage):
        return {"x": spot(x, y), "y": y, "stage": stage, "side": "left"}

    respawns = [
        # przed pierwszym panelem
        spawn(150, F1, 0), spawn(800, F1, 0), spawn(1500, F1, 0), spawn(2000, F1, 0), spawn(3800, F1, 0),
        # po pierwszym panelu (gracz na galerii albo dalej)
        spawn(1500, F1, 1), spawn(2300, F1, 1), spawn(3900, F1, 1), spawn(4700, F1, 1), spawn(5300, F1, 1),
        spawn(5800, F1, 1), spawn(6200, F4, 1), spawn(6700, F4, 1),
        # po drugim panelu
        spawn(6200, F4, 2), spawn(7500, F4, 2), spawn(7960, F4, 2), spawn(8500, F5, 2), spawn(8800, F5, 2),
        spawn(9100, F5, 2),
    ]
    enemies = [{"type": "boss", "x": 60, "y": F1, "id": "kamil", "wait": 4, "respawnDistance": 560,
                "respawns": respawns}]

    checkpoints += [
        {"x": pit1["x"] + pit1["w"] + 30, "y": F1},
        {"x": pit2["x"] + pit2["w"] + 30, "y": F1},
        {"x": 4216 + D3 + 44, "y": F4},
        {"x": 5700 + D4 - 100, "y": F4},
        {"x": 5700 + D4 + 80, "y": F5},
    ]
    checkpoints.sort(key=lambda c: c["x"])

    level = {
        "name": "Poziom 7",
        "subtitle": "Kamil",
        "mode": "boss",
        "questionCategory": "hard",
        "background": ["interior"],
        "timeLimit": 420,
        "width": W,
        "height": H,
        "hp": 1,
        "spawn": {"x": 220, "y": F1},
        "platforms": platforms,
        "bombs": bombs,
        "enemies": enemies,
        "checkpoints": checkpoints,
        "spikes": spikes,
        "jumpPads": pads,
    }
    return level


if __name__ == "__main__":
    level = build()
    OUT.write_text(json.dumps(level, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{OUT.name}: {len(level['platforms'])} platform, {len(level['enemies'])} przeciwników, {level['width']} x {level['height']} px")
