"""Generuje src/data/levels/index.json z listą wszystkich plików poziomów (*.json).

Skrypt może leżeć w dowolnym miejscu projektu (np. w tools/ albo w samym src/data/levels/) -
sam znajdzie katalog src/data/levels.

Na lokalnym serwerze (python -m http.server) gra znajduje poziomy sama, ale hosting bez listingu
katalogu (np. GitHub Pages) potrzebuje tej listy. Uruchom po dodaniu lub usunięciu poziomu:

    python src/data/levels/level-index-generator.py

Kolejność w menu = kolejność w pliku (domyślnie: sortowanie po nazwie z liczbami po kolei,
więc poziom-2.json jest przed poziom-10.json). Jeśli index.json już istnieje, jego dotychczasowa
kolejność zostaje zachowana, a nowe pliki dochodzą na końcu.
"""
import json
import re
from pathlib import Path



def find_levels_dir():
    """Szuka src/data/levels: w katalogu skryptu i w katalogach nad nim."""
    here = Path(__file__).resolve().parent
    for folder in [here, *here.parents]:
        if folder.parts[-3:] == ("src", "data", "levels"):
            return folder
        candidate = folder / "src" / "data" / "levels"
        if candidate.is_dir():
            return candidate
    raise SystemExit("Nie znaleziono katalogu src/data/levels. Połóż skrypt gdzieś wewnątrz projektu.")


LEVELS_DIR = find_levels_dir()
INDEX = LEVELS_DIR / "index.json"


def natural_key(name):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", name)]


def main():
    files = sorted((p.name for p in LEVELS_DIR.glob("*.json") if p.name != "index.json"), key=natural_key)

    order = []
    if INDEX.exists():
        try:
            order = [n for n in json.loads(INDEX.read_text(encoding="utf-8")).get("levels", []) if n in files]
        except (json.JSONDecodeError, AttributeError):
            print("Uwaga: index.json był uszkodzony, tworzę go od nowa.")
    order += [n for n in files if n not in order]

    INDEX.write_text(json.dumps({"levels": order}, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Zapisano {INDEX} ({len(order)} poziomów):")
    for name in order:
        print("  -", name)


if __name__ == "__main__":
    main()