"""Generuje poziom 1 (samouczek) do src/data/levels/poziom-1.json.

Uruchom z głównego katalogu repozytorium:   python tools/make_level1.py
Grafiki do niego robi tools/make_level1_art.py (pliki assets/l1_*.png). Poziom można potem otwierać i poprawiać
w edytorze albo zmieniać liczby tutaj i generować od nowa.

PLAN POZIOMU (współrzędne w px gry, y w dół; ulica = y 440, poziom ma 3900 x 480 px)
  0-520     chodzenie i skok: skrzynia i kontener do przeskoczenia
  520-860   bomba (proste pytanie); po jej rozbrojeniu czas staje, więc reszta bez pośpiechu
  860-1240  skocznia wyrzuca na dach sklepu (ulicę zamyka budynek)
  1240-1540 hak: dziura między dachami, na dole kolce, w środku lampa (punkt zaczepienia)
  1740-1930 dash: za duży odstęp na zwykły skok, na dole kolce
  2130-2850 wall jumpy: brama w budynku prowadzi do szybu między dwoma budynkami; wchodzisz na dach, schodzisz po schodach
  2850-3300 mały przeciwnik (zakuwany E)
  3300-3900 duży przeciwnik (E tylko od tyłu), auto do przeskoczenia, na końcu drzwi wyjścia

Elementy dekoracyjne to platformy z "solid": false i teksturą; kolizję daje osobna, niewidoczna platforma
(color "transparent"). Zaczep haka to mała niewidoczna platforma "grappleable": true w miejscu żarówki lampy.
"""

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "src" / "data" / "levels" / "poziom-1.json"

W, H = 3900, 480
G = H - 40            # powierzchnia ulicy (y)
LAMP = "assets/lampa wyłączona.png"   # rysunek lampy 100 x 300: słup ma środek w x = 44, żarówka w (62, 30)
LAMP_POLE_X, LAMP_BULB = 44, (62, 30)

platforms = []
hints = []
checkpoints = []


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
    """Pełny budynek od dachu (top) do ulicy: jedna bryła z teksturą."""
    return solid(x, top, w, G - top, texture)


def lamp(pole_x, hook):
    """Lampa uliczna ze słupem w pole_x, stojąca na ulicy. hook=True: żarówka jest punktem zaczepienia haka."""
    left = pole_x - LAMP_POLE_X
    decor(left, G - 300, 100, 300, LAMP)
    if hook:
        bx, by = left + LAMP_BULB[0], G - 300 + LAMP_BULB[1]
        solid(bx - 12, by - 12, 24, 24, solid=False, grappleable=True)
        return bx, by


# ---------------- ulica i budynki ----------------
solid(0, G, W, 40, "assets/l1_sidewalk.png", "tile")

# Strefa 1: skok. Skrzynia (32 px) i kontener (40 px) do przeskoczenia.
solid(300, G - 32, 32, 32, "assets/l1_crate.png")
solid(392, G - 40, 64, 40, "assets/l1_dumpster.png")

# Strefa 3: sklep zamyka ulicę, na jego dach wyrzuca skocznia.
SHOP_X, ROOF = 1040, G - 128
building(SHOP_X, ROOF, 200, "assets/l1_shop.png")

# Strefa 4: dziura 300 px między dachami; w środku lampa (hak), na dole kolce.
BLOCK_X = 1540
building(BLOCK_X, ROOF, 200, "assets/l1_block.png")
hook_pole = 1367
bulb = lamp(hook_pole, True)

# Strefa 5: dash, odstęp 190 px.
OFFICE_X = 1930
building(OFFICE_X, ROOF, 200, "assets/l1_office.png")

# Strefa 6: brama (budynek L) i wysoki budynek R tworzą szyb o szerokości 96 px.
ARCH_X, ARCH_TOP = 2330, G - 264
decor(ARCH_X, ARCH_TOP, 220, 264, "assets/l1_arch.png")
solid(ARCH_X, ARCH_TOP, 220, 264 - 64)                  # bryła nad przejściem (pod nią 64 px wolnego)
TOWER_X, TOWER_TOP = ARCH_X + 220 + 96, G - 208
building(TOWER_X, TOWER_TOP, 200, "assets/l1_tower.png")
# Schody przeciwpożarowe na prawej ścianie wieży: podesty co 64 px, można z nich zeskakiwać w dół.
FE_X, FE_Y = TOWER_X + 200, TOWER_TOP + 24
decor(FE_X, FE_Y, 56, 200, "assets/l1_fire_escape.png")
for rel in (40, 104, 168):
    solid(FE_X, FE_Y + rel, 56, 6, oneWay=True)

# Strefa 8: auto (korpus i kabina to osobne bryły), garaż przy wyjściu jako tło.
CAR_X = 3380
decor(CAR_X, G - 40, 112, 40, "assets/l1_car.png")
solid(CAR_X, G - 24, 112, 24)
solid(CAR_X + 24, G - 38, 60, 14)
decor(W - 200, G - 144, 200, 144, "assets/l1_garage.png")

# ---------------- zagrożenia ----------------
spikes = [
    {"x": SHOP_X + 200, "y": G - 8, "w": BLOCK_X - (SHOP_X + 200), "h": 8},      # dziura pod hakiem
    {"x": BLOCK_X + 200, "y": G - 8, "w": OFFICE_X - (BLOCK_X + 200), "h": 8},   # dziura pod dashem
]
jump_pads = [{"x": 968, "y": G - 8, "w": 32, "h": 8, "power": 1}]

# ---------------- przeciwnicy i bomba ----------------
enemies = [
    {"type": "weak", "id": "weak-1", "x": 3160, "y": G, "direction": -1, "speed": 48,
     "area": {"x1": 3040, "y1": 300, "x2": 3300, "y2": G}},
    {"type": "strong", "id": "strong-1", "x": 3620, "y": G, "direction": -1, "speed": 36,
     "area": {"x1": 3540, "y1": 300, "x2": 3700, "y2": G}},
]
bombs = [{"x": 640, "y": G}]

# ---------------- checkpointy ----------------
checkpoints += [
    {"x": 1100, "y": ROOF},        # dach sklepu, przed hakiem
    {"x": 1600, "y": ROOF},        # dach kamienicy, przed dashem
    {"x": 2250, "y": G},           # ulica przed bramą
    {"x": 2720, "y": TOWER_TOP},   # dach wieży po wspinaczce
    {"x": 2960, "y": G},           # przed małym przeciwnikiem
    {"x": 3320, "y": G},           # przed dużym przeciwnikiem
]

# ---------------- podpowiedzi ----------------
hints += [
    {"x": 0, "w": 270, "text": "Rozbrój bombę i dojdź do wyjścia po prawej\n[A] [D] lub [←] [→] – chodzenie"},
    {"x": 270, "w": 290, "text": "[Spacja] (albo [W], [↑]) – skok\nPrzeskocz skrzynię i kontener"},
    {"x": 560, "w": 300, "when": "armed",
     "text": "Podejdź do bomby i naciśnij [E]\nZła odpowiedź kosztuje 20 s"},
    {"on": "allDefused", "duration": 8,
     "text": "Bomba rozbrojona – czas stanął!\nMożesz iść dalej bez pośpiechu"},
    {"x": 860, "w": 170, "text": "Skocznia wyrzuca wysoko\nWejdź na nią i wyląduj na dachu"},
    {"x": 1150, "w": 100, "text": "Kolce! Skocz i w locie naciśnij [Q] – hak\nHuśtaj się [A] [D], puść [Spacja] nad dachem"},
    {"x": 1540, "w": 96, "text": "Dash jest pod [Shift]\nPrzyda się na następnej przerwie"},
    {"x": 1640, "w": 100, "text": "Za daleko na zwykły skok\nSkocz i w locie naciśnij [Shift] – dash"},
    {"x": 2250, "w": 300, "text": "Szyb między budynkami: wskocz do niego\n[Spacja] przy ścianie w powietrzu – wall jump"},
    {"x": ARCH_X + 220, "w": 96, "y": 150,
     "text": "Odbijaj się naprzemiennie od lewej i prawej ściany\nOd tej samej ściany odbijesz się dopiero po chwili"},
    {"x": 2960, "w": 200, "text": "Przeciwnik atakuje tylko od przodu\nPodejdź i naciśnij [E], żeby go zakuć"},
    {"x": 3300, "w": 240,
     "text": "Duży przeciwnik: [E] działa tylko od tyłu\nWskocz na auto i przeskocz nad nim; [F] – dym"},
    {"x": 3700, "w": 200, "when": "armed", "text": "Wyjście jest zamknięte\nWróć i rozbrój bombę"},
    {"x": 3700, "w": 200, "when": "defused", "text": "Wyjście otwarte – wejdź do drzwi!"},
]

level = {
    "name": "Poziom 1",
    "subtitle": "Samouczek",
    "questionCategory": "easy",
    "background": ["cityDusk"],
    "timeLimit": 120,
    "width": W,
    "height": H,
    "hp": 5,
    "spawn": {"x": 64, "y": G},
    "platforms": platforms,
    "bombs": bombs,
    "enemies": enemies,
    "checkpoints": checkpoints,
    "hints": hints,
    "spikes": spikes,
    "jumpPads": jump_pads,
}

if __name__ == "__main__":
    OUT.write_text(json.dumps(level, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{OUT.name}: {len(platforms)} platform, żarówka lampy w {bulb}")
