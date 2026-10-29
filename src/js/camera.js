import { SCALE, getScale, snap } from "./config.js";

// Kamera: przesuwa "okno" (ekran gry) po większym poziomie i płynnie goni gracza.

export function createCamera({
    viewWidth,
    viewHeight,
    levelWidth,
    levelHeight,
    smoothing = 6,   // poziomo: im większa wartość, tym szybciej kamera dogania gracza
    smoothingY = 8,  // pionowo (trochę szybciej, żeby nie zgubić gracza przy szybkim spadaniu)
    deadZoneY = 30 * SCALE,  // pionowo (w px gry): o ile gracz może odejść od środka ekranu, zanim kamera ruszy
}) {
    // Poziomo kamera zawsze dąży do gracza. Pionowo ma "strefę martwą": drobne skoki
    // (np. po płaskim terenie) nie bujają obrazem, a kamera przesuwa się dopiero, gdy gracz
    // wejdzie wyraźnie wyżej lub niżej. W niskich poziomach (wysokość = ekran) nie rusza się wcale.

    // Kamera nie wychodzi poza krawędzie poziomu.
    const clampX = (value) => Math.max(0, Math.min(levelWidth - viewWidth, value));
    const clampY = (value) => Math.max(0, Math.min(levelHeight - viewHeight, value));

    // Pozycja lewego górnego rogu kamery, przy której cel byłby na środku ekranu.
    const targetX = (target) => clampX(target.x + target.w / 2 - viewWidth / 2);
    const targetY = (target) => clampY(target.y + target.h / 2 - viewHeight / 2);

    const camera = {
        x: 0,
        y: 0,

        // Zmienia rozmiar poziomu (przy przejściu na inny poziom).
        setLevelSize(width, height) {
            levelWidth = width;
            levelHeight = height;
        },

        // Natychmiast ustawia kamerę na celu (na start gry i po respawnie).
        snapTo(target) {
            camera.x = targetX(target);
            camera.y = targetY(target);
        },

        // Co klatkę przybliża kamerę do celu. dt = czas klatki w sekundach.
        follow(target, dt) {
            // Wygładzanie niezależne od liczby klatek na sekundę:
            // przy 60 i 144 FPS kamera zachowuje się tak samo.
            camera.x += (targetX(target) - camera.x) * (1 - Math.exp(-smoothing * dt));

            // Pion: gdzie kamera musiałaby być, żeby gracz był na brzegu strefy martwej.
            const offset = target.y + target.h / 2 - (camera.y + viewHeight / 2);
            let wantedY = camera.y;
            if (offset > deadZoneY) wantedY = camera.y + (offset - deadZoneY);
            else if (offset < -deadZoneY) wantedY = camera.y + (offset + deadZoneY);
            camera.y += (clampY(wantedY) - camera.y) * (1 - Math.exp(-smoothingY * dt));
        },

        // Przesuwa układ współrzędnych rysowania: wszystko narysowane po tym
        // wywołaniu trafia w odpowiednie miejsce względem kamery.
        apply(ctx) {
            // Kamera porusza się płynnie (nie jest zaokrąglana do pikseli gry). Wyrównujemy ją tylko
            // do pikseli ekranu, żeby obraz był ostry (patrz SNAP_TO_SCREEN_PIXELS w config.js).
            const scale = getScale(ctx);
            ctx.translate(-snap(camera.x, scale), -snap(camera.y, scale));
        },
    };

    return camera;
}