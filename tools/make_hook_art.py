"""Generuje pikselową grafikę haka (assets/hook.png, 24 x 16 px).

Hak jest skierowany w prawo: jego środkowy ząb wskazuje punkt zaczepienia, a ucho łączy się z liną.
Uruchom z katalogu projektu: python tools/make_hook_art.py (wymaga Pillow).
"""
from pathlib import Path

from PIL import Image, ImageDraw


ASSETS = Path(__file__).resolve().parent.parent / "assets"
WIDTH, HEIGHT = 24, 16


def color(value, alpha=255):
    value = value.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), alpha)


MID = color("#8b98ad")
LIGHT = color("#d6dfec")
DARK = color("#4a5568")
OUTLINE = color("#05060f")
RED = color("#d9482b")
ROPE = color("#c9a46a")


def build():
    image = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Ucho z kawałkiem liny oraz trzon haka.
    draw.ellipse((1, 5, 8, 12), fill=MID)
    draw.ellipse((3, 7, 6, 10), fill=(0, 0, 0, 0))
    draw.rectangle((8, 7, 14, 9), fill=MID)
    draw.rectangle((13, 5, 16, 11), fill=MID)

    # Środkowy ząb wskazuje kotwicę, boczne zęby zawijają się do tyłu.
    draw.line((16, 7, 23, 7), fill=MID)
    draw.line((16, 8, 23, 8), fill=MID)
    draw.line((15, 5, 17, 2, 20, 1, 22, 2, 22, 4), fill=MID, width=2)
    draw.line((15, 11, 17, 14, 20, 15, 22, 14, 22, 12), fill=MID, width=2)

    # Jasna górna krawędź i ciemny spód podkreślają metalowy kształt.
    pixels = image.load()
    shaded = image.copy()
    shaded_pixels = shaded.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if pixels[x, y][3] == 0:
                continue
            above = pixels[x, y - 1][3] if y > 0 else 0
            below = pixels[x, y + 1][3] if y < HEIGHT - 1 else 0
            if above == 0:
                shaded_pixels[x, y] = LIGHT
            elif below == 0:
                shaded_pixels[x, y] = DARK

    detail = ImageDraw.Draw(shaded)
    detail.rectangle((13, 5, 14, 11), fill=RED)
    detail.line((14, 5, 15, 5), fill=LIGHT)
    detail.point([(1, 8), (2, 8), (2, 9)], fill=ROPE)

    # Ciemny obrys jednopikselowy poprawia czytelność na jasnym tle.
    base = shaded.load()
    result = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    result_pixels = result.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if base[x, y][3]:
                result_pixels[x, y] = base[x, y]
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and base[nx, ny][3]:
                    result_pixels[x, y] = OUTLINE
                    break
    return result


if __name__ == "__main__":
    asset = build()
    asset.save(ASSETS / "hook.png")
    print("hook.png", asset.size)
