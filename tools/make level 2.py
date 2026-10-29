"""Generuje poziom 2 (miasto w dzień, rozbrajanie bomb przy budynkach Trelvos) do src/data/levels/poziom-2.json.

Uruchom z głównego katalogu repozytorium:   python "tools/make level 2.py"
Grafiki do niego robi "tools/make level 2 art.py" (pliki assets/l2_*.png).

PLAN POZIOMU (px gry, y w dół; ulica G = 448, poziom 4352 x 488 px; przejście ok. minuty razem z 3 pytaniami)
  0-560      chodzenie: donica i kiosk do przeskoczenia
  576-800    SKLEP TRELVOS (tło) + bomba 1 przy drzwiach
  832-1120   rusztowanie (pomosty jednokierunkowe) na dach kamienicy blokującej ulicę
  1120-1320  DASH: przerwa 200 px między dachami (kolce na dole)
  1320-1512  dach kawiarni, zejście na ulicę
  1640-1900  słaby przeciwnik (patrol), zakuwany [E] od tyłu albo omijany
  2112-2368  BANK TRELVOS (tło) + bomba 2 przy drzwiach
  2432-2944  WALL JUMP: brama w budynku i wieża Trelvos tworzą szyb 96 px; na dachu wieży neon i bomba 3
  2944-3248  HAK: żuraw w przerwie 304 px (hak w (3088, 134)), na dole kolce
  3248-3504  dach magazynu, zejście na ulicę
  3600-4352  kontener, furgonetka, silny przeciwnik, zajezdnia i drzwi wyjścia

Elementy dekoracyjne to platformy z "solid": false (kolejność = kolejność rysowania), kolizję dają osobne, niewidoczne
platformy ("transparent"). Wszystkie bomby stoją przy budynkach z napisem Trelvos.
"""

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "src" / "data" / "levels" / "poziom-2.json"

W, H = 4352, 488
G = H - 40            # powierzchnia ulicy (y = 448; drzwi wyjścia z game.js stoją 40 px nad dołem poziomu)
A = "assets/"

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


# ---------------- ulica ----------------
solid(0, G, W, 40, A + "l2_pavement.png", "tile")

# ---------------- strefa 1: ulica, sklep Trelvos, bomba 1 ----------------
decor(120, G - 32, 16, 32, A + "l2_hydrant.png")
decor(170, G - 32, 64, 32, A + "l2_bench.png")
decor(262, G - 128, 32, 128, A + "l2_lamp.png")
solid(330, G - 32, 64, 32, A + "l2_planter.png")                 # do przeskoczenia
solid(452, G - 56, 64, 56, A + "l2_kiosk.png")                   # do przeskoczenia
decor(536, G - 24, 40, 24, A + "l2_cones.png")
MARKET_X = 600
decor(MARKET_X, G - 128, 224, 128, A + "l2_trelvos_market.png")   # tło, nie blokuje ulicy
BOMB1_X = MARKET_X + 112                                          # przy drzwiach sklepu
decor(MARKET_X - 90, G - 128, 64, 128, A + "l2_tree.png")

# ---------------- strefa 2: kamienica z rusztowaniem, dash ----------------
FLAT_X, FLAT_TOP = 928, G - 160
building(FLAT_X, FLAT_TOP, 224, "l2_flat.png")
SC_X = FLAT_X - 64
decor(SC_X, G - 176, 64, 176, A + "l2_scaffold.png")
for rel in (32, 80, 128):                                          # pomosty: y = G-176+rel = 304, 352, 400
    solid(SC_X, G - 176 + rel, 64, 6, oneWay=True)

CAFE_X = FLAT_X + 224 + 200                                        # przerwa 200 px = tylko z dashem
CAFE_TOP = G - 128
building(CAFE_X, CAFE_TOP, 192, "l2_cafe.png")

# ---------------- strefa 3: ulica, przeciwnik, bank Trelvos, bomba 2 ----------------
decor(CAFE_X + 192 + 40, G - 96, 96, 96, A + "l2_busstop.png")
decor(1610, G - 40, 24, 40, A + "l2_mailbox.png")
decor(1960, G - 128, 32, 128, A + "l2_lamp.png")
BANK_X = 2112
decor(BANK_X, G - 160, 256, 160, A + "l2_trelvos_bank.png")
BOMB2_X = BANK_X + 128                                             # przy drzwiach banku
decor(BANK_X - 90, G - 128, 64, 128, A + "l2_tree.png")

# ---------------- strefa 4: szyb (wall jump), wieża Trelvos, bomba 3 ----------------
GATE_X, GATE_H = 2448, 288
decor(GATE_X, G - GATE_H, 224, GATE_H, A + "l2_gate.png")
solid(GATE_X, G - GATE_H, 224, GATE_H - 64)                        # bryła nad przejściem (pod nią 64 px wolnego)
TOWER_X, TOWER_H = GATE_X + 224 + 96, 160                          # szyb szeroki na 96 px
TOWER_TOP = G - TOWER_H
building(TOWER_X, TOWER_TOP, 192, "l2_trelvos_tower.png")
decor(TOWER_X + 16, TOWER_TOP - 48, 128, 48, A + "l2_trelvos_sign.png")   # neon na dachu
BOMB3_X = TOWER_X + 168                                            # na dachu, obok neonu

# ---------------- strefa 5: żuraw (hak), magazyn ----------------
GAP_L = TOWER_X + 192
WARE_X = GAP_L + 304
CRANE_X = GAP_L + 116                                              # lewy brzeg obrazka; hak w (+28, +54 od góry obrazka)
CRANE_Y = G - 368
decor(CRANE_X, CRANE_Y, 176, 368, A + "l2_crane.png")
HOOK = (CRANE_X + 28, CRANE_Y + 54)
solid(HOOK[0] - 12, HOOK[1] - 12, 24, 24, solid=False, grappleable=True)
building(WARE_X, G - 160, 256, "l2_warehouse.png")

# ---------------- strefa 6: ulica do wyjścia ----------------
decor(WARE_X + 256 + 40, G - 32, 64, 32, A + "l2_bench.png")
solid(3640, G - 64, 96, 64, A + "l2_container.png")                 # do wskoczenia
VAN_X = 3800
solid(VAN_X, G - 56, 128, 56, A + "l2_van.png")                    # do wskoczenia i przeskoczenia nad przeciwnikiem
decor(W - 224, G - 128, 224, 128, A + "l2_depot.png")
decor(4130, G - 128, 32, 128, A + "l2_lamp.png")

# ---------------- zagrożenia ----------------
spikes = [
    {"x": FLAT_X + 224, "y": G - 8, "w": CAFE_X - (FLAT_X + 224), "h": 8},          # dziura pod dashem
    {"x": GAP_L, "y": G - 8, "w": CRANE_X + 84 - GAP_L, "h": 8},                    # dziura pod hakiem (lewa część)
    {"x": CRANE_X + 148, "y": G - 8, "w": WARE_X - (CRANE_X + 148), "h": 8},        # prawa część (fundament żurawia w środku)
]

# ---------------- przeciwnicy i bomby ----------------
enemies = [
    {"type": "weak", "id": "weak-1", "x": 1780, "y": G, "direction": -1, "speed": 48,
     "area": {"x1": 1660, "y1": G - 140, "x2": 1900, "y2": G}},
    {"type": "strong", "id": "strong-1", "x": 4060, "y": G, "direction": -1, "speed": 36,
     "area": {"x1": 3960, "y1": G - 140, "x2": 4120, "y2": G}},
]
bombs = [
    {"x": BOMB1_X, "y": G},
    {"x": BOMB2_X, "y": G},
    {"x": BOMB3_X, "y": TOWER_TOP},
]

# ---------------- checkpointy ----------------
checkpoints += [
    {"x": FLAT_X + 40, "y": FLAT_TOP},   # dach kamienicy, przed dashem
    {"x": CAFE_X + 40, "y": CAFE_TOP},   # dach kawiarni
    {"x": 1590, "y": G},                 # ulica przed słabym przeciwnikiem
    {"x": 2410, "y": G},                 # przed bramą
    {"x": WARE_X + 40, "y": G - 160},    # dach magazynu
    {"x": 3580, "y": G},                 # przed kontenerem i furgonetką
]

level = {
    "name": "Poziom 2",
    "subtitle": "Trelvos w biały dzień",
    "questionCategory": "medium",
    "background": ["cityDay"],
    "timeLimit": 110,
    "width": W,
    "height": H,
    "hp": 5,
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
