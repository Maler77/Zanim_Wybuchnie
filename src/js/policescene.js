// ============================================================================
//  SCENA Z POLICJĄ
//  Pikselowa ilustracja rysowana na canvasie. Kamil używa klatki z tego samego
//  sprite sheeta co boss w ostatnim poziomie; pozostałe elementy zachowują
//  jego ostrą, ograniczoną paletę i nocny nastrój.
// ============================================================================

export const SCENE_WIDTH = 320;
export const SCENE_HEIGHT = 180;

const rect = (ctx, x, y, w, h, color) => {
    ctx.fillStyle = color;
    ctx.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
};

function disc(ctx, cx, cy, radius, color) {
    ctx.fillStyle = color;
    for (let dy = -radius; dy <= radius; dy++) {
        const half = Math.round(Math.sqrt(radius * radius - dy * dy));
        ctx.fillRect(Math.round(cx) - half, Math.round(cy) + dy, half * 2 + 1, 1);
    }
}

const GLYPHS = {
    P: ["110", "101", "110", "100", "100"],
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
                for (let rx = 0; rx < 3; rx++) {
                    if (row[rx] === "1") ctx.fillRect(cx + rx, y + ry, 1, 1);
                }
            });
        }
        cx += 4;
    }
}

const STARS = [
    [12, 21], [36, 43], [65, 17], [96, 32], [126, 15], [157, 46], [184, 23],
    [216, 39], [246, 18], [278, 44], [304, 16], [48, 69], [113, 61], [194, 70], [267, 66],
];

const FAR_BUILDINGS = [
    [-8, 38, 50], [20, 31, 39], [272, 34, 55], [295, 43, 74],
];

function drawSky(ctx, t) {
    const sky = ["#080e1b", "#0a1223", "#0d172a", "#111d32", "#15233a", "#192941"];
    sky.forEach((color, i) => rect(ctx, 0, i * 22, SCENE_WIDTH, 22, color));

    // Księżyc i drobne gwiazdy na chłodnym, nocnym niebie.
    disc(ctx, 270, 31, 8, "#aab9d0");
    disc(ctx, 273, 28, 8, "#111d32");
    STARS.forEach(([x, y], i) => {
        if ((Math.floor(t * 1.7) + i) % 5 !== 0) rect(ctx, x, y, 1, 1, i % 3 === 0 ? "#dce8f4" : "#8495b1");
    });

    FAR_BUILDINGS.forEach(([x, w, h], bi) => {
        const top = 130 - h;
        rect(ctx, x, top, w, h, "#10182a");
        rect(ctx, x + 2, top + 3, w - 4, 2, "#1a2942");
        for (let wy = top + 8; wy < 124; wy += 11) {
            for (let wx = x + 5; wx < x + w - 4; wx += 8) {
                const lit = (bi * 5 + Math.floor(wx / 8) + Math.floor(wy / 11) * 3) % 6 === 0;
                rect(ctx, wx, wy, 3, 4, lit ? "#b9a875" : "#26324a");
            }
        }
    });
}

function drawHeadquarters(ctx) {
    // Szeroka, segmentowana elewacja nawiązuje do ciemnych paneli i świateł z poziomu 6.
    rect(ctx, 38, 38, 244, 94, "#111a2c");
    rect(ctx, 38, 38, 244, 5, "#34445f");
    rect(ctx, 38, 43, 244, 2, "#7283a0");
    rect(ctx, 41, 48, 238, 78, "#172238");

    for (const x of [47, 82, 117, 203, 238, 273]) {
        rect(ctx, x, 49, 4, 77, "#273752");
        rect(ctx, x + 4, 50, 1, 76, "#0b1220");
    }
    for (const y of [72, 98, 124]) {
        rect(ctx, 42, y, 236, 2, "#0b1321");
        rect(ctx, 42, y + 2, 236, 1, "#293a55");
    }

    // Chłodne okna i światła nad wejściem.
    for (const [x, y, w] of [[57, 57, 17], [91, 57, 18], [214, 57, 17], [248, 57, 16], [57, 81, 17], [91, 81, 18], [214, 81, 17], [248, 81, 16]]) {
        rect(ctx, x, y, w, 12, "#243c59");
        rect(ctx, x + 2, y + 2, w - 4, 8, "#1c304a");
        rect(ctx, x + 3, y + 2, 1, 8, "#496583");
    }
    rect(ctx, 129, 57, 62, 3, "#536985");
    rect(ctx, 137, 63, 46, 3, "#263d5a");

    // Szklane drzwi wejściowe.
    rect(ctx, 130, 84, 60, 45, "#0b1422");
    rect(ctx, 133, 87, 54, 39, "#304b69");
    rect(ctx, 136, 90, 22, 32, "#1b304b");
    rect(ctx, 162, 90, 22, 32, "#1b304b");
    rect(ctx, 159, 88, 2, 38, "#647994");
    rect(ctx, 155, 105, 2, 3, "#aebbd0");
    rect(ctx, 166, 105, 2, 3, "#aebbd0");
    rect(ctx, 128, 126, 64, 3, "#8ba0b8");
    rect(ctx, 142, 78, 36, 3, "#6ea1bc");
    rect(ctx, 148, 75, 24, 2, "#83bfd0");

    // Światła przy wejściu.
    rect(ctx, 123, 88, 3, 22, "#253a55");
    rect(ctx, 194, 88, 3, 22, "#253a55");
    rect(ctx, 124, 91, 1, 5, "#f3c875");
    rect(ctx, 195, 91, 1, 5, "#f3c875");
}

function drawStreet(ctx) {
    rect(ctx, 0, 128, SCENE_WIDTH, 13, "#343e50");
    rect(ctx, 0, 128, SCENE_WIDTH, 2, "#78849a");
    rect(ctx, 0, 135, SCENE_WIDTH, 2, "#252f42");
    rect(ctx, 0, 141, SCENE_WIDTH, 39, "#111722");
    rect(ctx, 0, 142, SCENE_WIDTH, 1, "#303a4b");
    for (let x = 9; x < SCENE_WIDTH; x += 38) {
        rect(ctx, x, 169, 20, 2, "#596375");
        rect(ctx, x + 2, 172, 16, 1, "#293242");
    }
    // Krótki słupek uliczny przy wejściu.
    rect(ctx, 294, 73, 2, 61, "#29364c");
    rect(ctx, 289, 70, 12, 3, "#445674");
    rect(ctx, 291, 67, 8, 3, "#d2b878");
    rect(ctx, 292, 64, 6, 3, "#f0d391");
}

function drawBackground(ctx, t) {
    drawSky(ctx, t);
    drawHeadquarters(ctx);
    drawStreet(ctx);
}

function drawEmergencyGlow(ctx, t) {
    const redBright = Math.floor(t * 4) % 2 === 0;
    const lights = [
        { x: 86, color: "255,48,62", alpha: redBright ? 0.34 : 0.12 },
        { x: 101, color: "65,145,255", alpha: redBright ? 0.12 : 0.36 },
    ];

    for (const light of lights) {
        const glow = ctx.createRadialGradient(light.x, 106, 2, light.x, 106, 70);
        glow.addColorStop(0, `rgba(${light.color},${light.alpha})`);
        glow.addColorStop(1, `rgba(${light.color},0)`);
        ctx.fillStyle = glow;
        ctx.fillRect(light.x - 70, 36, 140, 110);
    }

    ctx.globalAlpha = redBright ? 0.16 : 0.08;
    rect(ctx, 63, 143, 39, 2, "#ff4051");
    ctx.globalAlpha = redBright ? 0.08 : 0.17;
    rect(ctx, 101, 143, 35, 2, "#4b9cff");
    ctx.globalAlpha = 1;
}

function drawCar(ctx, t) {
    const x = 14;
    const phase = Math.floor(t * 4) % 2 === 0;

    // Cień i koła.
    rect(ctx, x + 5, 150, 151, 5, "#090d14");
    for (const wx of [x + 36, x + 121]) {
        disc(ctx, wx, 146, 9, "#080b11");
        disc(ctx, wx, 146, 5, "#586477");
        disc(ctx, wx, 146, 2, "#a7b2c2");
    }

    // Dolna część nadwozia i maska.
    rect(ctx, x + 5, 123, 138, 22, "#d8e0eb");
    rect(ctx, x, 127, 9, 11, "#e5eaf0");
    rect(ctx, x + 7, 119, 31, 8, "#e2e8f0");
    rect(ctx, x + 105, 116, 37, 11, "#e5eaf0");
    rect(ctx, x + 138, 121, 10, 14, "#dce4ee");
    rect(ctx, x + 8, 120, 2, 4, "#f6f7f8");
    rect(ctx, x + 144, 127, 4, 4, "#fff0ad");

    // Kabina z grubymi, ostrymi słupkami.
    rect(ctx, x + 31, 103, 79, 22, "#e4eaf1");
    rect(ctx, x + 37, 106, 28, 16, "#213550");
    rect(ctx, x + 70, 106, 33, 16, "#29415f");
    rect(ctx, x + 65, 104, 5, 20, "#c6d0dd");
    rect(ctx, x + 38, 107, 24, 2, "#6e89a9");
    rect(ctx, x + 72, 107, 27, 2, "#7791ad");
    rect(ctx, x + 31, 117, 78, 2, "#f4f5f5");

    // Niebieski pas, drzwi, klamki i oznaczenie.
    rect(ctx, x + 1, 130, 143, 6, "#275aa0");
    rect(ctx, x + 67, 124, 1, 20, "#8896a9");
    rect(ctx, x + 44, 127, 4, 1, "#526176");
    rect(ctx, x + 76, 127, 4, 1, "#526176");
    tinyText(ctx, "POLICJA", x + 51, 131, "#f1f4f8");
    rect(ctx, x + 16, 131, 7, 4, "#d9bf74");
    rect(ctx, x + 18, 130, 3, 1, "#fff0bd");

    // Tylne i przednie światła, zderzak oraz belka.
    rect(ctx, x, 125, 3, 5, "#f04450");
    rect(ctx, x + 145, 125, 3, 6, "#fff0ad");
    rect(ctx, x + 140, 138, 10, 3, "#9aa6b7");
    rect(ctx, x + 55, 99, 34, 5, "#202a3b");
    rect(ctx, x + 57, 100, 14, 4, phase ? "#ff384a" : "#641d2b");
    rect(ctx, x + 72, 100, 15, 4, phase ? "#1b3d71" : "#62a4ff");
}

function drawOfficer(ctx, cx, gy, { facing = 1, reachesForKamil = false, radio = false, t = 0 } = {}) {
    const uniform = "#243a5b";
    const uniformLight = "#3f5d83";
    const pants = "#18253a";
    const skin = "#c89170";

    // Nogi i buty.
    rect(ctx, cx - 7, gy - 17, 6, 15, pants);
    rect(ctx, cx + 1, gy - 17, 6, 15, pants);
    rect(ctx, cx - 9, gy - 3, 8, 3, "#090d14");
    rect(ctx, cx + 1, gy - 3, 8, 3, "#090d14");
    rect(ctx, cx - 7, gy - 16, 5, 2, "#354760");
    rect(ctx, cx + 1, gy - 16, 5, 2, "#354760");

    // Kurtka i kamizelka.
    rect(ctx, cx - 9, gy - 35, 18, 20, uniform);
    rect(ctx, cx - 7, gy - 32, 14, 13, uniformLight);
    rect(ctx, cx - 6, gy - 29, 12, 2, "#283d5c");
    rect(ctx, cx - 5, gy - 24, 10, 1, "#263a56");
    rect(ctx, cx - 8, gy - 17, 16, 3, "#101a2a");
    rect(ctx, cx + (facing > 0 ? 2 : -4), gy - 30, 3, 4, "#e7c76b");
    rect(ctx, cx + (facing > 0 ? 3 : -3), gy - 29, 1, 2, "#fff0bb");

    // Ramiona i dłonie.
    rect(ctx, cx - 12, gy - 33, 4, 15, uniform);
    rect(ctx, cx + 8, gy - 33, 4, 15, uniform);
    rect(ctx, cx - 12, gy - 21, 4, 3, skin);
    rect(ctx, cx + 8, gy - 21, 4, 3, skin);

    if (reachesForKamil) {
        rect(ctx, cx + 8, gy - 34, 13, 4, uniform);
        rect(ctx, cx + 18, gy - 34, 5, 4, skin);
        rect(ctx, cx + 10, gy - 35, 9, 1, uniformLight);
    }

    // Głowa i czapka.
    rect(ctx, cx - 5, gy - 45, 10, 9, skin);
    rect(ctx, cx - 3, gy - 40, 2, 1, "#302522");
    rect(ctx, cx - 7, gy - 48, 14, 4, "#172844");
    rect(ctx, cx - 6, gy - 50, 12, 3, "#243a5b");
    rect(ctx, cx - 2, gy - 48, 4, 2, "#e7c76b");
    rect(ctx, facing > 0 ? cx + 4 : cx - 8, gy - 45, 4, 1, "#31496b");

    if (radio) {
        rect(ctx, cx - 10, gy - 39, 4, 7, "#101722");
        rect(ctx, cx - 9, gy - 41, 2, 3, "#3b4b62");
        if (Math.floor(t * 2.2) % 2 === 0) rect(ctx, cx - 9, gy - 38, 1, 1, "#f15b61");
    }
}

const KAMIL_SHEET = typeof Image === "undefined" ? null : new Image();
if (KAMIL_SHEET) KAMIL_SHEET.src = new URL("../../assets/enemy_boss_sheet.png", import.meta.url).href;

function drawKamilFallback(ctx, x, gy) {
    // Awaryjna wersja w tych samych bordowych i piaskowych barwach co boss.
    rect(ctx, x + 7, gy - 44, 25, 43, "#762c31");
    rect(ctx, x + 11, gy - 47, 18, 16, "#a85f48");
    rect(ctx, x + 11, gy - 47, 18, 4, "#59242b");
    rect(ctx, x + 26, gy - 39, 4, 2, "#f0dbb0");
    rect(ctx, x + 10, gy - 20, 18, 4, "#292a32");
    rect(ctx, x + 11, gy - 16, 7, 13, "#292a32");
    rect(ctx, x + 22, gy - 16, 7, 13, "#292a32");
    rect(ctx, x + 9, gy - 3, 10, 3, "#10131a");
    rect(ctx, x + 22, gy - 3, 10, 3, "#10131a");
}

function drawKamil(ctx, t, cx, gy) {
    const x = Math.round(cx - 20);
    const frame = Math.floor(t * 3) % 2;

    if (KAMIL_SHEET?.complete && KAMIL_SHEET.naturalWidth >= 80 && KAMIL_SHEET.naturalHeight >= 48) {
        // Odbicie w lewo, w stronę policjanta. Klatka 40x48 jest taka sama jak w poziomie 6.
        ctx.save();
        ctx.translate(x + 40, 0);
        ctx.scale(-1, 1);
        ctx.drawImage(KAMIL_SHEET, frame * 40, 0, 40, 48, 0, gy - 48, 40, 48);
        ctx.restore();
    } else {
        drawKamilFallback(ctx, x, gy);
    }

    // Mały błysk kajdanek przy dłoniach za plecami.
    rect(ctx, x + 29, gy - 17, 5, 2, "#c4cedb");
    rect(ctx, x + 33, gy - 16, 2, 1, "#e3e8ee");
}

export function drawPoliceScene(ctx, t) {
    ctx.imageSmoothingEnabled = false;
    drawBackground(ctx, t);
    drawEmergencyGlow(ctx, t);
    drawCar(ctx, t);

    const ground = 160;
    drawOfficer(ctx, 197, ground, { facing: 1, reachesForKamil: true, t });
    drawKamil(ctx, t, 231, ground);
    drawOfficer(ctx, 267, ground, { facing: -1, radio: true, t });

    // Miękkie cienie pod butami, pozostające w pikselowej palecie sceny.
    ctx.globalAlpha = 0.45;
    for (const x of [197, 231, 267]) rect(ctx, x - 10, ground, 20, 2, "#05080e");
    ctx.globalAlpha = 1;

    // Pasy kinowe utrzymują kadr zgodny z dotychczasową sceną fabularną.
    rect(ctx, 0, 0, SCENE_WIDTH, 12, "#05070c");
    rect(ctx, 0, SCENE_HEIGHT - 12, SCENE_WIDTH, 12, "#05070c");
}
