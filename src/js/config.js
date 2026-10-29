// Podstawowe ustawienia pikseli gry. Jednostką w całym kodzie jest PIKSEL GRY (1/TILE tila):
// pozycje, rozmiary, prędkości (px/s) i przyspieszenia (px/s²). Czas jest w sekundach.

export const TILE = 32;         // rozmiar tila w pikselach
export const VIEW_WIDTH = 640;  // szerokość ekranu gry w pikselach (20 tili)
export const VIEW_HEIGHT = 360; // wysokość ekranu gry w pikselach (11,25 tila)

// Współczynnik skali względem pierwotnego projektu, w którym tile miał 16 px. Fizyka, rozmiary
// obiektów, przeciwnicy, kamera i czcionki HUD są zapisane jako wartości dla tila 16 px
// i mnożone przez SCALE, więc zmiana TILE (np. z 16 na 32) nie rozjeżdża rozgrywki.
// Uwaga: współrzędne w levels.js są w pikselach i trzeba je przeskalować ręcznie.
export const SCALE = TILE / 16;

// true  = skala zawsze całkowita (1x, 2x, 3x...): każdy piksel gry to idealny kwadrat, a nadmiar
//         okna wypełniają czarne pasy. Najostrzejszy obraz.
// false = obraz wypełnia okno maksymalnie (skala ułamkowa), kosztem nierównych pikseli.
export const PIXEL_PERFECT = true;

// true  = pozycje gracza i kamery NIE są zaokrąglane do całych pikseli gry, więc ruch jest
//         płynny (także poniżej 1 piksela gry). Obraz jest tylko wyrównywany do pikseli EKRANU
//         (1/skala piksela gry, np. co 1/4 piksela gry przy skali 4x), dzięki czemu piksele
//         pozostają ostre, nie rozmywają się i nie migają.
// false = zupełnie surowe pozycje (płynnie, ale krawędzie pikseli mogą migotać).
export const SNAP_TO_SCREEN_PIXELS = true;

// Aktualna skala rysowania (pikseli ekranu na piksel gry) odczytana z kontekstu canvasa.
export function getScale(ctx) {
    const t = ctx.getTransform ? ctx.getTransform() : null;
    return t && t.a ? Math.abs(t.a) : 1;
}

// Wyrównuje wartość (w pikselach gry) do pikseli ekranu przy danej skali.
export function snap(value, scale) {
    return SNAP_TO_SCREEN_PIXELS ? Math.round(value * scale) / scale : value;
}