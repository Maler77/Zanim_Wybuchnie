"""Generuje poziom 3 (miasto w nocy, rozbrajanie bomb przy miejscach Trelvos) do src/data/levels/poziom-3.json.

Uruchom z głównego katalogu repozytorium:   python "tools/make level 3.py"
Grafiki do niego robi "tools/make level 3 art.py" (pliki assets/l3_*.png); tło to tekstura "cityNight" z textures.js.

PLAN POZIOMU (px gry, y w dół; ulica G = 448, poziom 4800 x 488 px; przejście ok. 1,5-2 minut razem z 3 pytaniami)
  0-560      chodzenie: skrzynia i taksówka do przeskoczenia
  620-876    HOTEL TRELVOS (tło) + bomba 1 przy wejściu
  954-1234   schody przeciwpożarowe (podesty jednokierunkowe) na dach kamienicy blokującej ulicę
  1234-1426  DASH: przerwa 192 px między dachami (kolce na dole)
  1426-1618  dach biurowca
  1618-1922  HAK: maszt radiowy w przerwie 304 px (hak w (1770, 102)), na dole kolce
  1922-2146  dach WIEŻY TRELVOS: neon i bomba 2; stąd zeskok na ulicę
  2146-2760  ulica: słaby przeciwnik (patrol), zakuwany [E] od tyłu albo omijany
  2760-3080  WALL JUMP: brama w budynku i klub tworzą szyb 96 px; na dachu klubu neon i bomba 3
  3272-4800  kontener, furgonetka, silny przeciwnik, skrzynia, słaby przeciwnik, zajezdnia i drzwi wyjścia

Elementy dekoracyjne to platformy z "solid": false (kolejność = kolejność rysowania), kolizję dają osobne, niewidoczne
platformy ("transparent"). Zaczep haka to mała niewidoczna platforma "grappleable": true w miejscu czerwonego światła masztu.
Wszystkie bomby stoją przy miejscach z napisem Trelvos (hotel, wieża, klub z neonem na dachu).
"""

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "src" / "data" / "levels" / "poziom-3.json"

W, H = 4800, 488
G = H - 40            # powierzchnia ulicy (y = 448; drzwi wyjścia z game.js stoją 40 px nad dołem poziomu)
A = "assets/"
LAMP = "assets/l3_lamp.png"    # zapalona latarnia 100 x 300 (tools/make level 3 art.py): słup ma środek w x = 44
LAMP_POLE_X = 44

platforms, checkpoints = [], []


def solid(x, y, w, h, texture=None, mode=None, **extra):
    item = {"x": x, "y": y, "w": w, "h": h, "texture": texture or "platform"}
    if mode:
        item["textureMode"] = mode
    if texture is None:
        item["color"] = "transparent"
    item.update(extra)
    platforms.append(item)
    return item


def decor(x, y, w, h, texture):
    return solid(x, y, w, h, texture, solid=False)


def building(x, top, w, texture):
    """Pełny budynek od dachu (top) do ulicy: jedna solidna bryła z teksturą."""
    return solid(x, top, w, G - top, A + texture)


def lamp(pole_x):
    """Zapalona lampa uliczna ze słupem w pole_x (tylko ozdoba, rzuca stożek światła na chodnik)."""
    decor(pole_x - LAMP_POLE_X, G - 300, 100, 300, LAMP)


# ---------------- ulica ----------------
solid(0, G, W, 40, A + "l3_pavement.png", "tile")

# ---------------- strefa 1: ulica, skrzynia, taksówka ----------------
decor(60, G - 32, 16, 32, A + "l3_hydrant.png")
lamp(150)
decor(230, G - 64, 32, 64, A + "l3_phone.png")
solid(330, G - 32, 32, 32, A + "l3_crate.png")                      # do przeskoczenia
CAR_X = 430
decor(CAR_X, G - 40, 112, 40, A + "l3_taxi.png")
solid(CAR_X, G - 24, 112, 24)                                      # korpus taksówki
solid(CAR_X + 24, G - 38, 60, 14)                                  # kabina

# ---------------- strefa 2: hotel Trelvos, bomba 1 ----------------
decor(540, G - 128, 64, 128, A + "l3_tree.png")
HOTEL_X = 620
decor(HOTEL_X, G - 160, 256, 160, A + "l3_trelvos_hotel.png")        # tło, nie blokuje ulicy
BOMB1_X = HOTEL_X + 128                                            # przy wejściu do hotelu
lamp(896)

# ---------------- strefa 3: kamienica ze schodami przeciwpożarowymi ----------------
FLAT_X, FLAT_TOP = 1010, G - 192
building(FLAT_X, FLAT_TOP, 224, "l3_flat.png")
FE_X, FE_Y = FLAT_X - 56, G - 208
decor(FE_X, FE_Y, 56, 208, A + "l3_fire_escape.png")
for rel in (64, 112, 160):                                         # podesty: y = G-144, G-96, G-48 (co 48 px)
    solid(FE_X, FE_Y + rel, 56, 6, oneWay=True)

# ---------------- strefa 4: dash, biurowiec ----------------
OFFICE_X = FLAT_X + 224 + 192                                      # przerwa 192 px = tylko z dashem
OFFICE_TOP = G - 192
building(OFFICE_X, OFFICE_TOP, 192, "l3_office.png")

# ---------------- strefa 5: hak, wieża Trelvos, bomba 2 ----------------
GAP_L = OFFICE_X + 192
TOWER_X = GAP_L + 304
TOWER_TOP = G - 192
HOOK = (GAP_L + 152, TOWER_TOP - 154)                              # czerwone światło masztu, 154 px nad dachami (jak żuraw w poziomie 2)
MAST_X, MAST_Y = HOOK[0] - 32, HOOK[1] - 32
decor(MAST_X, MAST_Y, 64, G - MAST_Y, A + "l3_mast.png")
solid(HOOK[0] - 12, HOOK[1] - 12, 24, 24, solid=False, grappleable=True)
building(TOWER_X, TOWER_TOP, 224, "l3_trelvos_tower.png")
decor(TOWER_X + 16, TOWER_TOP - 48, 128, 48, A + "l3_trelvos_sign.png")      # neon na dachu
BOMB2_X = TOWER_X + 168                                            # na dachu, obok neonu

# ---------------- strefa 6: ulica, słaby przeciwnik, brama ----------------
STREET_X = TOWER_X + 224
lamp(STREET_X + 110)
decor(STREET_X + 190, G - 32, 64, 32, A + "l3_bench.png")
decor(STREET_X + 400, G - 128, 64, 128, A + "l3_tree.png")
solid(2650, G - 40, 64, 40, A + "l3_dumpster.png")                 # do przeskoczenia przed bramą

# ---------------- strefa 7: szyb (wall jump), klub, bomba 3 ----------------
GATE_X, GATE_H = 2760, 288
decor(GATE_X, G - GATE_H, 224, GATE_H, A + "l3_gate.png")
solid(GATE_X, G - GATE_H, 224, GATE_H - 64)                        # bryła nad przejściem (pod nią 64 px wolnego)
CLUB_X, CLUB_H = GATE_X + 224 + 96, 208                            # szyb szeroki na 96 px
CLUB_TOP = G - CLUB_H
building(CLUB_X, CLUB_TOP, 192, "l3_club.png")
decor(CLUB_X + 16, CLUB_TOP - 48, 128, 48, A + "l3_trelvos_sign.png")          # neon na dachu klubu
BOMB3_X = CLUB_X + 168

# ---------------- strefa 8: ulica do wyjścia ----------------
lamp(3340)
decor(3420, G - 64, 32, 64, A + "l3_phone.png")
solid(3520, G - 64, 96, 64, A + "l3_container.png")                # do wskoczenia
VAN_X = 3700
solid(VAN_X, G - 56, 128, 56, A + "l3_van.png")                    # do wskoczenia i przeskoczenia nad przeciwnikiem
decor(4090, G - 32, 16, 32, A + "l3_hydrant.png")
solid(4150, G - 32, 32, 32, A + "l3_crate.png")                    # do przeskoczenia
lamp(4230)
decor(W - 224, G - 128, 224, 128, A + "l3_depot.png")

# ---------------- zagrożenia ----------------
MAST_FOOT_L, MAST_FOOT_R = MAST_X + 10, MAST_X + 54                # fundament masztu (44 px) stoi w środku dziury
spikes = [
    {"x": FLAT_X + 224, "y": G - 8, "w": OFFICE_X - (FLAT_X + 224), "h": 8},        # dziura pod dashem
    {"x": GAP_L, "y": G - 8, "w": MAST_FOOT_L - GAP_L, "h": 8},                    # dziura pod hakiem (lewa część)
    {"x": MAST_FOOT_R, "y": G - 8, "w": TOWER_X - MAST_FOOT_R, "h": 8},            # prawa część
]

# ---------------- przeciwnicy i bomby ----------------
enemies = [
    {"type": "weak", "id": "weak-1", "x": 2480, "y": G, "direction": -1, "speed": 48,
     "area": {"x1": 2360, "y1": G - 140, "x2": 2600, "y2": G}},
    {"type": "strong", "id": "strong-1", "x": VAN_X + 260, "y": G, "direction": -1, "speed": 36,
     "area": {"x1": VAN_X + 160, "y1": G - 140, "x2": VAN_X + 320, "y2": G}},
    {"type": "weak", "id": "weak-2", "x": 4380, "y": G, "direction": -1, "speed": 52,
     "area": {"x1": 4260, "y1": G - 140, "x2": 4500, "y2": G}},
]
bombs = [
    {"x": BOMB1_X, "y": G},
    {"x": BOMB2_X, "y": TOWER_TOP},
    {"x": BOMB3_X, "y": CLUB_TOP},
]

# ---------------- checkpointy ----------------
checkpoints += [
    {"x": FLAT_X + 40, "y": FLAT_TOP},       # dach kamienicy, przed dashem
    {"x": OFFICE_X + 40, "y": OFFICE_TOP},   # dach biurowca, przed hakiem
    {"x": TOWER_X + 30, "y": TOWER_TOP},     # dach wieży po haku
    {"x": 2200, "y": G},                     # ulica po zeskoku z wieży
    {"x": 2700, "y": G},                     # przed bramą
    {"x": 3480, "y": G},                     # przed kontenerem, furgonetką i silnym przeciwnikiem
    {"x": 4100, "y": G},                     # przed drugim słabym przeciwnikiem
]

level = {
    "name": "Poziom 3",
    "subtitle": "Trelvos nocą",
    "questionCategory": "medium",
    "background": ["cityNight"],
    "timeLimit": 130,
    "width": W,
    "height": H,
    "hp": 4,
    "spawn": {"x": 64, "y": G},
    "platforms": platforms,
    "bombs": bombs,
    "enemies": enemies,
    "checkpoints": checkpoints,
    "spikes": spikes,
    "jumpPads": [],
}

if __name__ == "__main__":
    OUT.write_text(json.dumps(level, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{OUT.name}: {len(platforms)} platform, hak w {HOOK}, bomby {[b['x'] for b in bombs]}")
