// ============================================================================
//  SCENA Z POLICJĄ (pixel art rysowany kodem, bez plików graficznych)
//  Noc, radiowóz z migającymi światłami, dwóch policjantów i zatrzymany w kajdankach.
//  drawPoliceScene(ctx, t) rysuje jedną klatkę na płótnie SCENE_WIDTH x SCENE_HEIGHT; t to czas w sekundach.
//  Chcesz własną grafikę? Podaj ją w story.json w scenie "police" jako "image" (patrz storyplayer.js)
//  albo zmień kolory i położenia w tym pliku.
// ============================================================================

export const SCENE_WIDTH = 320;
export const SCENE_HEIGHT = 180;

const rect = (ctx, x, y, w, h, color) => {
    ctx.fillStyle = color;
    ctx.fillRect(Math.round(x), Math.round(y), w, h);
};

// Koło z pikseli (pełne), bo arc() rozmywa krawędzie.
function disc(ctx, cx, cy, radius, color) {
    ctx.fillStyle = color;
    for (let dy = -radius; dy <= radius; dy++) {
        const half = Math.round(Math.sqrt(radius * radius - dy * dy));
        ctx.fillRect(cx - half, cy + dy, half * 2, 1);
    }
}

// Maleńka czcionka 3x5 do napisu na radiowozie.
const GLYPHS = {
    P: ["111", "101", "111", "100", "100"],
    O: ["111", "101", "101", "101", "111"],
    L: ["100", "100", "100", "100", "111"],
    I: ["111", "010", "010", "010", "111"],
    C: ["111", "100", "100", "100", "111"],
    J: ["001", "001", "001", "101", "111"],
    A: ["010", "101", "111", "101", "101"],
};

function tinyText(ctx, text, x, y, color) {
    ctx.fillStyle = color;
    let cx = x;
    for (const letter of text) {
        const glyph = GLYPHS[letter];
        if (glyph) {
            glyph.forEach((row, ry) => {
                for (let rx = 0; rx < 3; rx++) if (row[rx] === "1") ctx.fillRect(cx + rx, y + ry, 1, 1);
            });
        }
        cx += 4;
    }
}

const STARS = [[18, 10], [52, 26], [96, 8], [140, 34], [188, 14], [236, 6], [282, 28], [34, 54], [172, 56], [266, 50], [300, 12], [120, 60]];

// Sylwetki budynków w tle: [x, szerokość, wysokość].
const BUILDINGS = [[0, 46, 70], [46, 34, 52], [80, 52, 84], [132, 40, 60], [172, 56, 76], [228, 38, 56], [266, 54, 88]];

function drawBackground(ctx, t) {
    ["#070a14", "#0a1020", "#0e1730", "#131f3d", "#1a2a4d", "#223560"].forEach((color, i) => rect(ctx, 0, i * 22, SCENE_WIDTH, 22, color));

    STARS.forEach(([x, y], i) => {
        if ((Math.floor(t * 1.5) + i) % 4 !== 0) rect(ctx, x, y, 1, 1, "#cdd8f0");
    });

    BUILDINGS.forEach(([x, w, h], bi) => {
        const top = 132 - h;
        rect(ctx, x, top, w, h, "#0b101c");
        for (let wy = top + 6; wy < 124; wy += 10) {
            for (let wx = x + 5; wx < x + w - 5; wx += 9) {
                const lit = (bi * 7 + Math.floor(wx / 9) * 3 + Math.floor(wy / 10) * 5) % 4 === 0;
                rect(ctx, wx, wy, 4, 5, lit ? "#e8c96a" : "#121a2b");
            }
        }
    });

    rect(ctx, 0, 128, SCENE_WIDTH, 12, "#3a404d");   // chodnik
    rect(ctx, 0, 128, SCENE_WIDTH, 2, "#555c6b");
    rect(ctx, 0, 140, SCENE_WIDTH, 40, "#1b2029");   // jezdnia
    for (let x = 6; x < SCENE_WIDTH; x += 34) rect(ctx, x, 170, 18, 2, "#4b5260");
}

function drawCar(ctx, t) {
    const x = 30;
    rect(ctx, x + 6, 146, 124, 6, "#12151c");                 // cień pod autem
    rect(ctx, x, 124, 136, 22, "#e9edf3");                    // dolna część karoserii
    rect(ctx, x + 28, 106, 74, 18, "#e9edf3");                // kabina
    rect(ctx, x + 33, 110, 29, 13, "#18263f");                // szyba tył
    rect(ctx, x + 66, 110, 31, 13, "#18263f");                // szyba przód
    rect(ctx, x + 62, 110, 4, 13, "#e9edf3");                 // słupek
    rect(ctx, x, 132, 136, 5, "#2159a8");                     // niebieski pas
    tinyText(ctx, "POLICJA", x + 54, 126, "#2159a8");
    rect(ctx, x, 127, 3, 4, "#ff3b3b");                       // tylne światło
    rect(ctx, x + 133, 127, 3, 5, "#ffe9a8");                 // przednie światło
    rect(ctx, x + 126, 138, 10, 3, "#aab2c0");                // zderzak

    // Koła
    for (const wx of [x + 26, x + 110]) {
        disc(ctx, wx, 146, 9, "#0b0c10");
        disc(ctx, wx, 146, 4, "#7b8393");
    }

    // Belka świetlna: lewa i prawa połowa świecą na przemian czerwono i niebiesko.
    const phase = Math.floor(t * 4) % 2 === 0;
    rect(ctx, x + 56, 100, 28, 6, "#20242d");
    rect(ctx, x + 57, 101, 13, 4, phase ? "#ff2d3a" : "#5a1017");
    rect(ctx, x + 70, 101, 13, 4, phase ? "#0e2552" : "#4aa3ff");
}

// Światło z belki: kolorowa poświata na otoczeniu, przełączana razem z lampami.
function drawGlow(ctx, t) {
    const phase = Math.floor(t * 4) % 2 === 0;
    const color = phase ? "255,45,58" : "74,163,255";
    const cx = phase ? 94 : 106;
    const glow = ctx.createRadialGradient(cx, 103, 2, cx, 103, 130);
    glow.addColorStop(0, `rgba(${color},0.45)`);
    glow.addColorStop(1, `rgba(${color},0)`);
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, SCENE_WIDTH, SCENE_HEIGHT);
}

// Postać z perspektywy z boku. x = środek, gy = linia stóp.
function person(ctx, x, gy, o) {
    const { torso, pants, skin, hat, facing = 1, head = 0, badge = false } = o;
    rect(ctx, x - 4, gy - 12, 3, 12, pants);
    rect(ctx, x + 1, gy - 12, 3, 12, pants);
    rect(ctx, x - 5, gy - 2, 4, 2, "#0b0d12");
    rect(ctx, x + 1, gy - 2, 4, 2, "#0b0d12");
    rect(ctx, x - 5, gy - 25 + head, 10, 13 - head, torso);
    rect(ctx, x - 5, gy - 14, 10, 2, "#0d0f14");
    if (badge) rect(ctx, x + (facing > 0 ? 1 : -3), gy - 22, 2, 2, "#ffd24a");
    rect(ctx, x - 7, gy - 24 + head, 2, 10 - head, torso);
    rect(ctx, x + 5, gy - 24 + head, 2, 10 - head, torso);
    // głowa (u zatrzymanego opuszczona)
    rect(ctx, x - 4, gy - 34 + head, 8, 9, skin);
    rect(ctx, x + (facing > 0 ? 1 : -2), gy - 30 + head, 1, 1, "#1a1a1a");
    if (hat) {
        rect(ctx, x - 5, gy - 38, 10, 5, hat);
        rect(ctx, x + (facing > 0 ? 0 : -6), gy - 34, 6, 1, hat);
        rect(ctx, x - 1, gy - 37, 2, 2, "#ffd24a");
    } else {
        rect(ctx, x - 4, gy - 35 + head, 8, 3, "#33231c");
    }
}

function drawFigures(ctx, t) {
    const gy = 160;
    const police = { torso: "#27467f", pants: "#161e30", skin: "#d9a77e", hat: "#14213d", badge: true };

    // Policjant z lewej: trzyma zatrzymanego za ramię.
    person(ctx, 194, gy, { ...police, facing: 1 });
    rect(ctx, 199, gy - 24, 11, 3, "#27467f");
    rect(ctx, 209, gy - 24, 2, 3, "#d9a77e");

    // Zatrzymany (Kamil): strój bossa bez ładunków, głowa opuszczona, ręce w kajdankach z tyłu.
    person(ctx, 218, gy, { torso: "#8c2f2f", pants: "#2b2b30", skin: "#d9a066", hat: null, facing: 1, head: 2 });
    rect(ctx, 215, gy - 16, 4, 2, "#c9ced6");
    rect(ctx, 213, gy - 15, 2, 1, "#c9ced6");

    // Policjant z prawej: mówi do krótkofalówki.
    person(ctx, 242, gy, { ...police, facing: -1 });
    rect(ctx, 235, gy - 29, 2, 7, "#27467f");
    rect(ctx, 234, gy - 33, 4, 6, "#101216");
    if (Math.floor(t * 2) % 2 === 0) rect(ctx, 235, gy - 33, 1, 1, "#ff5757");

    // Cienie pod postaciami
    ctx.globalAlpha = 0.35;
    for (const x of [194, 218, 242]) rect(ctx, x - 8, gy, 16, 2, "#000");
    ctx.globalAlpha = 1;
}

export function drawPoliceScene(ctx, t) {
    ctx.imageSmoothingEnabled = false;
    drawBackground(ctx, t);
    drawCar(ctx, t);
    drawFigures(ctx, t);
    drawGlow(ctx, t);
    // pasy "kinowe" u góry i u dołu
    rect(ctx, 0, 0, SCENE_WIDTH, 12, "#000");
    rect(ctx, 0, SCENE_HEIGHT - 12, SCENE_WIDTH, 12, "#000");
}