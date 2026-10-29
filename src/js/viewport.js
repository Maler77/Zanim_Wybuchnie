// Viewport odpowiada tylko za canvas: rozdzielczość, skalowanie i czyszczenie ekranu.
// Gra ma stałą, wirtualną rozdzielczość VIEW_WIDTH x VIEW_HEIGHT (patrz config.js) i jest
// skalowana do okna tak, żeby piksel gry zawsze był kwadratem o równym rozmiarze.
import { VIEW_WIDTH, VIEW_HEIGHT, PIXEL_PERFECT } from "./config.js";

export function createViewport(canvas) {
    const context = canvas.getContext("2d");
    if (!context) throw new Error("This browser does not support the 2D canvas API");

    let scale = 1; // ile pikseli ekranu przypada na jeden piksel gry

    // Dopasowuje wewnętrzną rozdzielczość canvasa do jego rozmiaru na ekranie (1:1 z pikselami
    // urządzenia, także na ekranach retina), dzięki czemu skalowanie pikseli gry jest dokładne.
    const resize = () => {
        const pixelRatio = window.devicePixelRatio || 1;
        canvas.width = Math.max(1, Math.round(canvas.clientWidth * pixelRatio));
        canvas.height = Math.max(1, Math.round(canvas.clientHeight * pixelRatio));
    };

    const observer = new ResizeObserver(resize);
    observer.observe(canvas);
    resize();

    // Wywołaj na początku każdej klatki. Zwraca kontekst, na którym rysujesz
    // we współrzędnych gry (0..VIEW_WIDTH x 0..VIEW_HEIGHT).
    function begin() {
        // Czyszczenie całego canvasa kolorem pasków (letterbox).
        context.setTransform(1, 0, 0, 1, 0, 0);
        context.fillStyle = "#0b1016";
        context.fillRect(0, 0, canvas.width, canvas.height);

        // Skala: największa, przy której cały ekran gry się mieści. W trybie pixel-perfect
        // zaokrąglona w dół do liczby całkowitej (okno mniejsze niż ekran gry skaluje ułamkowo).
        const fit = Math.min(canvas.width / VIEW_WIDTH, canvas.height / VIEW_HEIGHT);
        scale = PIXEL_PERFECT && fit >= 1 ? Math.floor(fit) : fit;

        const offsetX = Math.floor((canvas.width - VIEW_WIDTH * scale) / 2);
        const offsetY = Math.floor((canvas.height - VIEW_HEIGHT * scale) / 2);

        context.save();
        context.setTransform(scale, 0, 0, scale, offsetX, offsetY);
        context.imageSmoothingEnabled = false; // ostre piksele

        // Przycinamy rysowanie do obszaru ekranu gry.
        context.beginPath();
        context.rect(0, 0, VIEW_WIDTH, VIEW_HEIGHT);
        context.clip();

        return context;
    }

    // Wywołaj na końcu klatki.
    function end() {
        context.restore();
    }

    // Tryb "surowy" (edytor poziomów): cały canvas bez skali i pasów, współrzędne w pikselach ekranu.
    function beginRaw() {
        context.setTransform(1, 0, 0, 1, 0, 0);
        context.fillStyle = "#0b1016";
        context.fillRect(0, 0, canvas.width, canvas.height);
        context.save();
        context.imageSmoothingEnabled = false;
        return context;
    }

    return {
        width: VIEW_WIDTH,
        height: VIEW_HEIGHT,
        get scale() { return scale; },
        canvas,
        begin,
        end,
        beginRaw,
        endRaw: end,
        destroy() {
            observer.disconnect();
        },
    };
}