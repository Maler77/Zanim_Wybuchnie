// Zbieganie się kabli w oknie rozbrajania: trzy kable (czerwony, żółty, niebieski) wychodzą z odpowiedzi,
// zwężają się ukośnie do jednej linii, wchodzą w stalową obejmę i dalej biegnie jeden gruby przewód
// (do pęku dynamitu albo do nadajnika). Rysujemy to pikselami jak resztę grafik: płótno ma rozdzielczość
// obrazków (1 piksel płótna = 1 piksel obrazka), a CSS powiększa je całkowitą skalą --px.
//
// Dlaczego płótno, a nie obrazek: odległości między odpowiedziami zależą od tego, ile linii tekstu mają
// plakietki, więc kształt "lejka" trzeba narysować na bieżąco pod aktualne położenie kabli.

const WIRE = {
    red: { light: "#ff7868", base: "#e03e3e", dark: "#961e2a" },
    yellow: { light: "#fff082", base: "#f2c63e", dark: "#aa821e" },
    blue: { light: "#8cc6ff", base: "#4a86e8", dark: "#2a54a4" },
};
const TRUNK = { light: "#646470", base: "#2e2e36", dark: "#18181e" };
const STEEL = { light: "#ced4de", base: "#929aa6", dark: "#5c6070" };
const OUTLINE = "#000";

const BODY = 4;          // grubość kabla w pikselach (bez konturu), tak jak w kafelku bomb_ui_wire_*.png
const START_X = 1;       // gdzie kończy się prosty odcinek, a zaczyna ukośny
const SLOPE_DX = 16;     // ile pikseli w poziomie zajmuje zejście do środkowej linii
const CLAMP_W = 7;       // szerokość stalowej obejmy
const CLAMP_H = 12;
const TRUNK_BODY = 6;    // grubość wspólnego przewodu

// Zbiór pikseli pasa o grubości BODY idącego po łamanej. Wartość to najmniejszy numer wiersza "stempla"
// (0 = górna krawędź, dzięki temu wiemy, gdzie dać światło, a gdzie cień).
function band(points, body = BODY) {
    const cover = new Map();
    for (let i = 0; i + 1 < points.length; i++) {
        const [ax, ay] = points[i];
        const [bx, by] = points[i + 1];
        const steps = Math.max(Math.abs(bx - ax), Math.abs(by - ay), 1);
        for (let s = 0; s <= steps; s++) {
            const x = Math.round(ax + ((bx - ax) * s) / steps);
            const y = Math.round(ay + ((by - ay) * s) / steps);
            for (let row = 0; row < body; row++) {
                for (let col = 0; col < body; col++) {
                    const key = `${x + col},${y + row}`;
                    const known = cover.get(key);
                    if (known === undefined || row < known) cover.set(key, row);
                }
            }
        }
    }
    return cover;
}

function paint(ctx, cover, tones, body = BODY) {
    // kontur: każdy piksel obok pasa, który sam do pasa nie należy
    ctx.fillStyle = OUTLINE;
    for (const key of cover.keys()) {
        const [x, y] = key.split(",").map(Number);
        for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
            if (!cover.has(`${x + dx},${y + dy}`)) ctx.fillRect(x + dx, y + dy, 1, 1);
        }
    }
    for (const [key, row] of cover) {
        const [x, y] = key.split(",").map(Number);
        ctx.fillStyle = row === 0 ? tones.light : row >= body - 1 ? tones.dark : tones.base;
        ctx.fillRect(x, y, 1, 1);
    }
}

function paintClamp(ctx, x, y) {
    ctx.fillStyle = OUTLINE;
    ctx.fillRect(x - 1, y - 1, CLAMP_W + 2, CLAMP_H + 2);
    ctx.fillStyle = STEEL.base;
    ctx.fillRect(x, y, CLAMP_W, CLAMP_H);
    ctx.fillStyle = STEEL.light;
    ctx.fillRect(x, y, CLAMP_W, 1);
    ctx.fillRect(x + CLAMP_W - 2, y, 1, CLAMP_H);
    ctx.fillStyle = STEEL.dark;
    ctx.fillRect(x, y + CLAMP_H - 1, CLAMP_W, 1);
    ctx.fillRect(x, y, 1, CLAMP_H);
    ctx.fillStyle = STEEL.dark;           // rowki obejmy
    ctx.fillRect(x + 3, y + 1, 1, CLAMP_H - 2);
}

// canvas: płótno w komórce siatki; colors: nazwy kolorów kabli od góry do dołu; centers: środki kabli
// (w pikselach ekranu, od górnej krawędzi płótna); px: ile pikseli ekranu ma jeden piksel obrazka.
export function drawWireFunnel(canvas, colors, centers, px) {
    const rect = canvas.getBoundingClientRect();
    const w = Math.max(1, Math.round(rect.width / px));
    const h = Math.max(1, Math.round(rect.height / px));
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, w, h);
    if (!centers.length) return;

    // górny wiersz ciała kabla; kafelek ma kontur w wierszu 0, ciało w wierszach 1..4, więc środek leży między 2 a 3
    const tops = centers.map((c) => Math.round(c / px) - 2);
    const mid = tops[Math.floor(tops.length / 2)];
    const meetX = START_X + SLOPE_DX;

    // najpierw kable najdalej od środka, na wierzchu ten w środku
    const order = tops.map((_, i) => i).sort((a, b) => Math.abs(tops[b] - mid) - Math.abs(tops[a] - mid));
    for (const i of order) {
        const path = [[0, tops[i]], [START_X, tops[i]], [meetX, mid], [meetX + 2, mid]];
        paint(ctx, band(path), WIRE[colors[i]] ?? WIRE.red);
    }

    // obejma na zbiegu i wspólny przewód aż do prawej krawędzi
    const clampX = meetX + 1;
    const clampY = mid + Math.round(BODY / 2) - Math.round(CLAMP_H / 2);
    const trunkTop = mid + Math.round(BODY / 2) - Math.round(TRUNK_BODY / 2);
    paint(ctx, band([[clampX + CLAMP_W - 1, trunkTop], [w, trunkTop]], TRUNK_BODY), TRUNK, TRUNK_BODY);
    paintClamp(ctx, clampX, clampY);
}