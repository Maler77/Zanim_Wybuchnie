import { TILE, getScale, snap } from "./config.js";

// ============================================================================
//  TEKSTURY
//  Tu wybierasz grafiki z folderu assets/ dla wszystkich obiektów w grze
//  oraz dla elementów interfejsu (menu, okno z pytaniem, ekrany wygranej i przegranej).
//
//  PIXEL ART: 1 piksel obrazka = 1 piksel gry (1/32 tila). Obrazki rysuj w skali 1:1,
//  gra sama skaluje je do okna (patrz config.js i viewport.js). Wygładzanie jest wyłączone.
//
//  JAK UŻYĆ TEKSTURY DLA ISTNIEJĄCEGO OBIEKTU
//    Wpisz ścieżkę do pliku w polu `src` (np. src: "assets/bomb.png").
//    Bez ścieżki (src: null) obiekt jest rysowany zwykłym kolorem lub kształtem.
//
//  ROZMIAR OBRAZKA Z TEKSTURY (trim: true)
//    Obrazek jest najpierw przycinany z przezroczystych brzegów (pusty margines znika),
//    a rozmiar obiektu w grze to rozmiar przyciętego obrazka. Np. gracz 32x48 px z pustymi
//    bokami przycięty do 24x48 ma w grze 24x48 px (0,75 x 1,5 tila).
//    Bez tekstury obiekt ma rozmiar zastępczy (patrz game.js).
//    HITBOX jest osobno (patrz PLAYER_HITBOX i BOMB_HITBOX w game.js): domyślnie ręczny,
//    a po wpisaniu "auto" równy rozmiarowi przyciętego obrazka.
//
//  JAK DODAĆ TEKSTURĘ NOWEMU OBIEKTOWI W ŚWIECIE GRY (np. monecie)
//    1) Dodaj wpis poniżej:      coin: { src: "assets/coin.png", trim: true },
//    2) W obiekcie wpisz nazwę:  { x: 500, y: 300, w: 32, h: 32, texture: "coin", color: "gold" }
//       (rozmiar obrazka pobierzesz przez getTextureSize("coin"))
//    3) W funkcji draw() wywołaj: drawBox(ctx, coin);
//
//  JAK DODAĆ TEKSTURĘ ELEMENTOWI HTML
//    1) Dodaj wpis poniżej (np. pausePanel: { src: "assets/pause.png", mode: "cover" })
//    2) W index.html dopisz elementowi atrybut:  data-texture="pausePanel"
//    Tło zastępcze (gdy brak pliku) jest zdefiniowane w CSS.
//
//  OPCJE WPISU
//    src       ścieżka względem index.html albo null (brak tekstury)
//    trim      true = przytnij przezroczyste brzegi i weź rozmiar obiektu z obrazka
//              (tylko dla tekstur obiektów rysowanych w trybie "stretch")
//    smooth    true = wygładzanie przy skalowaniu (domyślnie wyłączone: ostre piksele)
//    mode      "stretch" (domyślnie) = rysuj w rozmiarze obiektu
//              "cover"               = wypełnij cały obiekt bez zniekształceń (nadmiar ucinany)
//              "tile"                = powtarzaj kafelek (platformy, podłoga, ściany)
//    tileWidth, tileHeight  rozmiar kafelka w trybie "tile" (domyślnie rozmiar pliku)
//    parallax  tylko dla tła gry: 0 = nieruchome, 1 = przesuwa się razem z kamerą (poziomo).
//              Tło wyższe niż ekran (np. 480 px przy ekranie 360 px) dodatkowo przesuwa się w pionie:
//              na samym dole poziomu widać dolną krawędź obrazka, na górze górną (drawBackground).
// ============================================================================

export const TEXTURES = {
    // Gracz. Obrazek powinien patrzeć w PRAWO, bo przy chodzeniu w lewo jest odbijany.
    player: { src: "assets/player1.png", trim: true },

    // Platformy, podłoga i ściany: powtarzany kafelek o rozmiarze tila (TILE z config.js).
    platform: { src: null, mode: "tile", tileWidth: TILE, tileHeight: TILE }, // np. "assets/platform.png"
    ground: { src: null, mode: "tile", tileWidth: TILE, tileHeight: TILE },   // np. "assets/ground.png"
    wall: { src: null, mode: "tile", tileWidth: TILE, tileHeight: TILE },     // ściany szybu (poziom 4)

    // Tło poziomu: rysowane w skali 1:1 (narysuj je na rozmiar ekranu gry, 640x360), powtarzane w poziomie.
    background: { src: null, parallax: 0.3 },  // poziom 1, np. "assets/background.png"
    background2: { src: null, parallax: 0.3 },  // poziom 2
    background3: { src: null, parallax: 0.3 },  // poziom 3
    background4: { src: null, parallax: 0.3 },  // poziom 4 (tło przesuwa się tylko poziomo)
    // Miasto o zachodzie (poziom 1). Obrazek 1280 x 480 jest większy niż ekran (640 x 360): przewija się poziomo
    // (parallax) i pionowo (gdy poziom jest wyższy niż ekran, tło przesuwa się o nadmiar swojej wysokości).
    cityDusk: { src: "assets/l1_city.png", parallax: 0.3 },
    // Miasto w dzień (poziom 2, tools/make level 2 art.py): panorama 1280 x 480, przewija się jak cityDusk.
    cityDay: { src: "assets/l2_city.png", parallax: 0.3 },
    // Miasto w nocy (poziom 3): panorama 1280 x 480 z księżycem, przewija się jak cityDay.
    cityNight: { src: "assets/l3_city.png", parallax: 0.3 },
    // Zachód nad dachami (poziom 4): Zachod.png rozszerzone do 1280 x 540 (tools/make level 4 art.py).
    skylineDusk: { src: "assets/l4_skyline.png", parallax: 0.25 },
    // Noc nad miastem (poziom 5): 1280 x 480, zapętla się poziomo (tools/make level 5 art.py).
    nightCity: { src: "assets/l5_night.png", parallax: 0.25 },
    // Wnętrze siedziby Trelvosu (poziom 7): 1280 x 720, zapętla się poziomo (tools/make level 7 art.py).
    interior: { src: "assets/l7_interior.png", parallax: 0.2 },

    // Kolce: kafelek 1 x 1/4 tila (32 x 8 px), powtarzany na całej szerokości kolców (tools/make_level1_art.py).
    spike: { src: "assets/spike.png", mode: "tile", tileWidth: TILE, tileHeight: TILE / 4 },

    // Życie gracza w interfejsie: pełne i puste serce (rysowane w HUD, np. 10 x 10 px).
    heart: { src: null },       // np. "assets/heart.png"
    heartEmpty: { src: null },  // np. "assets/heart_empty.png"

    // Wykrzyknik nad przeciwnikiem, który zauważył gracza (rysowany w 6 x 14 px; bez pliku: czerwony wykrzyknik).
    exclamation: { src: null },  // np. "assets/exclamation.png"

    // Hak na końcu liny (24 x 16 px; game.js obraca go w stronę punktu zaczepienia).
    grappleHook: { src: "assets/hook.png" },

    // Skocznia (jump pad): kafelek 1 x 1/4 tila (32 x 8 px), powtarzany na całej szerokości.
    jumpPad: { src: "assets/jump_pad.png", mode: "tile", tileWidth: TILE, tileHeight: TILE / 4 },

    // Drzwi wyjścia (tryb "bombs", rysowane na prawym końcu poziomu, 56 x 96 px): zamknięte i otwarte (wszystkie bomby rozbrojone).
    exitDoor: { src: "assets/l1_exit_door.png" },
    exitDoorOpen: { src: "assets/l1_exit_door_open.png" },

    // Bomba dymna: pocisk (rysowany w 8 x 8 px) i jedna "kłębka" chmury (chmura to kilka takich
    // kłębków na sobie, kółko bez pliku). Obrazek kłębka narysuj półprzezroczysty, np. 32 x 32 px.
    smokeBomb: { src: null },   // np. "assets/smoke_bomb.png"
    smokeCloud: { src: null },  // np. "assets/smoke_puff.png"

    // Bomby w świecie gry. bombDefused to bomba po rozbrojeniu.
    // Dynamit z zegarem (tools/make_bomb_art.py). Cyfry odliczania rysuje na wyświetlaczu game.js (BOMB_CLOCK).
    bomb: { src: "assets/bomb.png", trim: true },
    bombDefused: { src: "assets/bomb_defused.png", trim: true },
    // Panel rozbrajania (poziomy z mode: "panel"): jedna "bomba" narysowana jako panel. panelDefused po rozbrojeniu.
    // Terminal z ekranem (tools/make_bomb_art.py). Diodę alarmu dorysowuje game.js (PANEL_OVERLAY).
    panel: { src: "assets/panel.png", trim: true },
    panelDefused: { src: "assets/panel_defused.png", trim: true },

    // Elementy interfejsu (HTML):
    menuBackground: { src: "assets/menu_background.png", mode: "cover" }, // ekran tytułowy 640 x 360 (tools/make_menu_art.py)
    // Okno z pytaniem: tło za planszą z bombą (sama bomba z kablami to assets/bomb_ui_*.png w style.css).
    bombPanel: { src: null },                     // np. "assets/bomb_panel.png"
    // Miniatury poziomów w menu głównym (ilustracje 160 x 90 z tools/make level thumbnails.py, nie zrzuty ekranu).
    level1Thumbnail: { src: "assets/thumb_level1.png", mode: "cover" },
    level2Thumbnail: { src: "assets/thumb_level2.png", mode: "cover" },
    level3Thumbnail: { src: "assets/thumb_level3.png", mode: "cover" },
    level4Thumbnail: { src: "assets/thumb_level4.png", mode: "cover" },
    level5Thumbnail: { src: "assets/thumb_level5.png", mode: "cover" },
    level6Thumbnail: { src: "assets/thumb_level6.png", mode: "cover" },
    winBackground: { src: null, mode: "cover" },  // ekran wygranej
    loseBackground: { src: null, mode: "cover" }, // ekran przegranej
};

// ---------------------------------------------------------------------------
// Poniżej jest mechanizm. Zwykle nie musisz tego zmieniać.
// ---------------------------------------------------------------------------

const entries = new Map();   // nazwa -> { def, image, failed, trim }
const warnedUnknown = new Set();
const textureColorCache = new Map();

// Podmiana źródła obrazka (np. plik wybrany w edytorze spoza folderu assets/): ścieżka -> adres tymczasowy.
const sourceOverrides = new Map();

function addEntry(name, def) {
    const entry = { def, image: null, failed: false, trim: undefined };
    if (def.src) {
        entry.image = new Image();
        entry.image.onerror = () => {
            entry.failed = true;
            console.warn(`Tekstura "${name}": nie udało się wczytać pliku ${def.src}`);
            // Elementy HTML wracają do tła zastępczego z CSS.
            if (typeof document !== "undefined") {
                for (const element of document.querySelectorAll(`[data-texture="${name}"]`)) {
                    element.style.removeProperty("--texture");
                }
            }
        };
        entry.image.src = sourceOverrides.get(def.src) ?? def.src;
    }
    entries.set(name, entry);
    return entry;
}

for (const [name, def] of Object.entries(TEXTURES)) addEntry(name, def);

// ---------------------------------------------------------------------------
// Tekstury z plików poziomów (JSON): platforma może mieć w polu `texture` ścieżkę do obrazka
// (np. "assets/budynek.png") zamiast nazwy z TEXTURES, a w `textureMode` sposób rysowania:
//   "stretch" (domyślnie) = obrazek w rozmiarze platformy, "tile" = powtarzany, "cover" = wypełnia.
// textureKey() zwraca nazwę, której używa drawTexture (dla zwykłych nazw: tę samą nazwę).
// ---------------------------------------------------------------------------
export function textureKey(texture, mode = "stretch") {
    if (!texture || TEXTURES[texture]) return texture;
    const drawMode = mode === "tile" || mode === "cover" ? mode : "stretch";
    const key = `${drawMode}:${texture}`;
    if (!entries.has(key)) addEntry(key, { src: texture, mode: drawMode });
    return key;
}

// Wymusza inne źródło dla ścieżki (np. adres blob: pliku wybranego w edytorze). Działa tylko dla
// tekstur tworzonych PO tym wywołaniu.
export function overrideTextureSource(path, url) {
    sourceOverrides.set(path, url);
}

const isReady = (entry) => Boolean(entry.image && entry.image.complete && entry.image.naturalWidth > 0);

function warnUnknown(name) {
    if (warnedUnknown.has(name)) return;
    warnedUnknown.add(name);
    console.warn(`Nieznana tekstura "${name}". Dodaj ją do TEXTURES w textures.js.`);
}

// Zwraca wpis gotowy do rysowania albo null (brak nazwy, brak pliku, jeszcze się ładuje).
function getReady(name) {
    if (!name) return null;
    const entry = entries.get(name);
    if (!entry) {
        warnUnknown(name);
        return null;
    }
    return isReady(entry) ? entry : null;
}

// Prostokąt obrazka bez przezroczystych brzegów (rozmiar w pikselach obrazka).
function computeTrim(image) {
    const w = image.naturalWidth;
    const h = image.naturalHeight;
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    ctx.drawImage(image, 0, 0);
    const { data } = ctx.getImageData(0, 0, w, h);

    let minX = w, minY = h, maxX = -1, maxY = -1;
    for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
            if (data[(y * w + x) * 4 + 3] === 0) continue; // w pełni przezroczysty piksel
            if (x < minX) minX = x;
            if (x > maxX) maxX = x;
            if (y < minY) minY = y;
            if (y > maxY) maxY = y;
        }
    }
    if (maxX < 0) return null; // cały obrazek przezroczysty: bez przycinania
    return { x: minX, y: minY, w: maxX - minX + 1, h: maxY - minY + 1 };
}

// Wynik przycinania liczymy raz na teksturę. Bez `trim: true` to cały obrazek.
function getTrim(entry) {
    if (entry.trim !== undefined) return entry.trim;

    let trim = { x: 0, y: 0, w: entry.image.naturalWidth, h: entry.image.naturalHeight };
    if (entry.def.trim) {
        try {
            trim = computeTrim(entry.image) ?? trim;
        } catch (error) {
            // Odczyt pikseli jest zablokowany np. przy otwarciu strony z file:// (użyj serwera).
            console.warn("Nie można przyciąć tekstury (odczyt pikseli zablokowany). Uruchom grę przez serwer HTTP.", error);
        }
    }
    entry.trim = trim;
    return trim;
}

// Rozmiar tekstury w pikselach gry (po przycięciu, jeśli trim: true) albo null,
// gdy tekstury nie ma / jeszcze się ładuje. Z tego game.js bierze rozmiar obiektów.
export function getTextureSize(name) {
    const entry = getReady(name);
    if (!entry) return null;
    const { w, h } = getTrim(entry);
    return { w, h };
}

// Reprezentatywny kolor górnej krawędzi tekstury platformy, używany m.in. przez pył przy skoku.
export function getTextureSurfaceColor(name, edge = "top") {
    if (!name) return null;
    const cacheKey = `${name}:${edge}`;
    if (textureColorCache.has(cacheKey)) return textureColorCache.get(cacheKey);
    const entry = getReady(name);
    if (!entry || typeof document === "undefined") return null;

    let color = null;
    try {
        const canvas = document.createElement("canvas");
        canvas.width = 8;
        canvas.height = 2;
        const { naturalWidth: width, naturalHeight: height } = entry.image;
        const sampleWidth = Math.max(1, Math.floor(width * 0.18));
        const sampleHeight = Math.max(1, Math.floor(height * 0.18));
        const source = edge === "left"
            ? [0, 0, sampleWidth, height]
            : edge === "right"
                ? [width - sampleWidth, 0, sampleWidth, height]
                : edge === "bottom"
                    ? [0, height - sampleHeight, width, sampleHeight]
                    : [0, 0, width, sampleHeight];
        const context = canvas.getContext("2d", { willReadFrequently: true });
        context.drawImage(entry.image, ...source, 0, 0, canvas.width, canvas.height);
        const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
        let red = 0;
        let green = 0;
        let blue = 0;
        let count = 0;
        for (let i = 0; i < pixels.length; i += 4) {
            if (pixels[i + 3] < 32) continue;
            red += pixels[i];
            green += pixels[i + 1];
            blue += pixels[i + 2];
            count++;
        }
        if (count) color = `rgb(${Math.round(red / count)} ${Math.round(green / count)} ${Math.round(blue / count)})`;
    } catch {
        // Zewnętrzne tekstury mogą blokować odczyt pikseli; wtedy gra używa koloru zastępczego platformy.
    }
    textureColorCache.set(cacheKey, color);
    return color;
}

// Rysuje teksturę w prostokącie (x, y, w, h), zawsze w pełnych pikselach gry.
// Zwraca true, jeśli coś narysowano. Gdy zwróci false (brak tekstury lub pliku),
// wywołujący rysuje kolor zastępczy.
export function drawTexture(ctx, name, x, y, w, h) {
    const entry = getReady(name);
    if (!entry) return false;

    const { image, def } = entry;
    x = Math.round(x);
    y = Math.round(y);
    w = Math.round(w);
    h = Math.round(h);

    ctx.save();
    ctx.imageSmoothingEnabled = Boolean(def.smooth);

    if (def.mode === "tile") {
        const tileW = def.tileWidth ?? image.naturalWidth;
        const tileH = def.tileHeight ?? image.naturalHeight;
        ctx.beginPath();
        ctx.rect(x, y, w, h);
        ctx.clip(); // kafelki wystające poza obiekt są ucinane
        for (let ty = y; ty < y + h; ty += tileH) {
            for (let tx = x; tx < x + w; tx += tileW) {
                ctx.drawImage(image, tx, ty, tileW, tileH);
            }
        }
    } else if (def.mode === "cover") {
        // Skalujemy tak, żeby wypełnić prostokąt, a nadmiar obrazka ucinamy z brzegów.
        const scale = Math.max(w / image.naturalWidth, h / image.naturalHeight);
        const sw = w / scale;
        const sh = h / scale;
        ctx.drawImage(image, (image.naturalWidth - sw) / 2, (image.naturalHeight - sh) / 2, sw, sh, x, y, w, h);
    } else {
        const t = getTrim(entry); // tylko widoczna część obrazka
        ctx.drawImage(image, t.x, t.y, t.w, t.h, x, y, w, h);
    }

    ctx.restore();
    return true;
}

// Rysuje obiekt-prostokąt { x, y, w, h, texture, color }: teksturą, a jeśli jej nie ma,
// kolorem (o ile obiekt ma `color`). Zwraca true tylko wtedy, gdy użyto tekstury.
export function drawBox(ctx, box) {
    if (drawTexture(ctx, box.texture, box.x, box.y, box.w, box.h)) return true;
    if (box.color) {
        ctx.fillStyle = box.color;
        ctx.fillRect(Math.round(box.x), Math.round(box.y), Math.round(box.w), Math.round(box.h));
    }
    return false;
}

// Rysuje warstwę tła na ekranie (nie w układzie poziomu) w skali 1:1, powtarzaną w poziomie.
// scrollX to pozycja kamery. Tło wyższe niż ekran przesuwa się też w pionie: scrollY to pozycja kamery
// w pionie, maxScrollY to największa możliwa (wysokość poziomu - wysokość ekranu). Na samym dole poziomu
// (scrollY = maxScrollY) widać dolną krawędź obrazka, na górze górną; w poziomie bez przewijania pionowego
// (maxScrollY = 0) zawsze dolną, żeby podstawa miasta leżała na podłodze.
export function drawBackground(ctx, name, scrollX, viewWidth, viewHeight, scrollY = 0, maxScrollY = 0) {
    const entry = getReady(name);
    if (!entry) return false;

    const { image, def } = entry;
    const width = Math.max(1, image.naturalWidth);
    // Przesunięcie jest płynne (nie zaokrąglane do pikseli gry), tylko wyrównane do pikseli ekranu.
    const offset = -snap((scrollX * (def.parallax ?? 0)) % width, getScale(ctx));
    const extra = Math.max(0, image.naturalHeight - viewHeight);
    const progress = maxScrollY > 0 ? Math.max(0, Math.min(1, scrollY / maxScrollY)) : 1;
    const top = -snap(extra * progress, getScale(ctx));

    ctx.save();
    ctx.imageSmoothingEnabled = Boolean(def.smooth);
    for (let x = offset; x < viewWidth; x += width) {
        ctx.drawImage(image, x, top);
    }
    ctx.restore();
    return true;
}

// Nakłada tekstury na elementy HTML z atrybutem data-texture="nazwa".
// Element dostaje zmienną CSS --texture; samo rysowanie robi CSS (patrz style.css).
export function applyDomTextures(root = document) {
    for (const element of root.querySelectorAll("[data-texture]")) {
        const name = element.dataset.texture;
        const entry = entries.get(name);
        if (!entry) {
            warnUnknown(name);
            continue;
        }
        const { def } = entry;
        if (!def.src || entry.failed) continue; // zostaje tło zastępcze z CSS

        let size = "100% 100%"; // "stretch"
        let repeat = "no-repeat";
        if (def.mode === "cover") {
            size = "cover";
        } else if (def.mode === "tile") {
            size = def.tileWidth && def.tileHeight ? `${def.tileWidth}px ${def.tileHeight}px` : "auto";
            repeat = "repeat";
        }

        // WAŻNE: adres musi być bezwzględny. Względna ścieżka ("assets/x.png") w zmiennej CSS
        // jest rozwiązywana względem arkusza stylów (src/css/), a nie strony, więc obrazek się
        // nie ładował (szukał src/css/assets/x.png).
        const url = new URL(def.src, document.baseURI).href;

        element.style.setProperty("--texture", `url("${url}")`);
        element.style.setProperty("--texture-size", size);
        element.style.setProperty("--texture-repeat", repeat);
        element.style.imageRendering = def.smooth ? "" : "pixelated";
    }
}

// Podsumowanie wczytywania tekstur (do trybu debug).
export function getTextureReport() {
    const report = { ok: 0, loading: 0, error: 0, none: 0 };
    for (const entry of entries.values()) {
        if (!entry.def.src) report.none++;
        else if (entry.failed) report.error++;
        else if (isReady(entry)) report.ok++;
        else report.loading++;
    }
    return report;
}
