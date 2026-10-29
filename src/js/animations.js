// ============================================================================
//  ANIMACJE (SPRITE SHEETY)
//  Sprite sheet to jeden obrazek z wieloma klatkami animacji ułożonymi w siatce.
//  Tu opisujesz każdy arkusz (plik, rozmiar klatki, nazwy animacji), a poniżej jest mechanizm,
//  którego zwykle nie musisz zmieniać. Pełna instrukcja tworzenia arkuszy: README.md,
//  sekcja "Animacje i sprite sheety".
//
//  UKŁAD ARKUSZA (siatka klatek o jednakowym rozmiarze frameWidth x frameHeight):
//    - jeden WIERSZ = jedna animacja, klatki idą od lewej do prawej,
//    - wszystkie klatki mają ten sam rozmiar, a postać stoi w nich w tym samym miejscu:
//      STOPY na dolnej krawędzi klatki, postać na środku poziomo,
//    - postać patrzy w PRAWO (przy chodzeniu w lewo gra odbija klatkę),
//    - tło przezroczyste, bez wygładzania (ostre piksele), 1 piksel obrazka = 1 piksel gry.
//
//  ROZMIAR W GRZE
//    Rozmiar postaci w grze to rozmiar KLATKI (frameWidth x frameHeight). Klatka stoi dolnym
//    środkiem na dolnym środku hitboxa (tak samo jak zwykła tekstura), więc hitbox jest dalej
//    ustawiany osobno (PLAYER_HITBOX w game.js). Przycinanie (trim) nie dotyczy arkuszy,
//    bo każda klatka musi zostać w swoim miejscu, inaczej postać "skakałaby" w animacji.
//
//  OPCJE ANIMACJI
//    row      numer wiersza w arkuszu (liczony od 0, od góry)
//    frames   ile klatek ma animacja (liczone od kolumny `column`)
//    fps      ile klatek na sekundę (domyślnie 8)
//    loop     true = powtarzaj w kółko (domyślnie), false = zatrzymaj się na ostatniej klatce
//    column   od której kolumny zaczyna się animacja (domyślnie 0, od lewej)
// ============================================================================

export const SPRITE_SHEETS = {
    // Gracz. Arkusz składa skrypt z klatek 32 x 32 z assets/: python tools/make_player_sheet.py
    // (narysowane klatki trafiają do arkusza bez zmian, brakujące bieg, skok, spadanie i dash skrypt składa z nich).
    player: {
        src: "assets/player_sheet.png",
        frameWidth: 32,
        frameHeight: 32,
        animations: {
            idle:       { row: 0, frames: 2, fps: 3 },                 // stoi
            run:        { row: 1, frames: 4, fps: 10 },                // biegnie
            jump:       { row: 2, frames: 2, fps: 8, loop: false },    // wznosi się
            fall:       { row: 3, frames: 2, fps: 8 },                 // opada
            dash:       { row: 4, frames: 2, fps: 12 },                // dash
            wallslide:  { row: 5, frames: 2, fps: 6 },                 // zsuwa się po ścianie
            swing:      { row: 6, frames: 4, fps: 6 },                 // huśta się na haku (tam i z powrotem)
            hurt:       { row: 7, frames: 1, fps: 10, loop: false },   // oberwał
            death:      { row: 8, frames: 2, fps: 4, loop: false },    // śmierć (na razie nieużywana przez grę)
        },
    },

    // Przeciwnicy. Nazwa arkusza = nazwa typu z ENEMY_TYPES (enemies.js), więc gra sama dobiera arkusz do przeciwnika.
    // Arkusze rysuje: python tools/make_enemy_sheets.py. Klatka stoi dolnym środkiem na dolnym środku hitboxa.
    weak: {
        src: "assets/enemy_weak_sheet.png",
        frameWidth: 32,
        frameHeight: 40,
        animations: {
            idle:   { row: 0, frames: 2, fps: 3 },                  // stoi (np. czeka po zgubieniu gracza)
            walk:   { row: 1, frames: 4, fps: 6 },                  // patrol
            run:    { row: 2, frames: 4, fps: 10 },                 // pościg
            alert:  { row: 3, frames: 2, fps: 6 },                  // zaskoczony dotknięciem od tyłu
            cuffed: { row: 4, frames: 1, fps: 1, loop: false },     // zakuty
        },
    },
    strong: {
        src: "assets/enemy_strong_sheet.png",
        frameWidth: 44,
        frameHeight: 52,
        animations: {
            idle:   { row: 0, frames: 2, fps: 2 },
            walk:   { row: 1, frames: 4, fps: 5 },
            run:    { row: 2, frames: 4, fps: 8 },
            alert:  { row: 3, frames: 2, fps: 6 },
            cuffed: { row: 4, frames: 1, fps: 1, loop: false },
        },
    },
    boss: {
        src: "assets/enemy_boss_sheet.png",       // Kamil (boss poziomu "boss"): łapie gracza dotykiem
        frameWidth: 40,
        frameHeight: 48,
        animations: {
            idle: { row: 0, frames: 2, fps: 3 },                  // stoi (jeszcze "śpi" albo chwilę po pojawieniu się)
            run:  { row: 1, frames: 4, fps: 10 },                 // goni gracza z wyciągniętymi rękami
            jump: { row: 2, frames: 2, fps: 8, loop: false },     // skacze przez przeszkodę
            fall: { row: 3, frames: 2, fps: 8 },                  // opada
            grab: { row: 4, frames: 2, fps: 8 },                  // złapał gracza
        },
    },
};

// ---------------------------------------------------------------------------
// Poniżej jest mechanizm. Zwykle nie musisz tego zmieniać.
// ---------------------------------------------------------------------------

const sheets = new Map(); // nazwa -> { def, image, failed, checked }
const warned = new Set();

function warnOnce(key, message) {
    if (warned.has(key)) return;
    warned.add(key);
    console.warn(message);
}

for (const [name, def] of Object.entries(SPRITE_SHEETS)) {
    const entry = { def, image: null, failed: false, checked: false };
    if (def.src && typeof Image !== "undefined") {
        entry.image = new Image();
        entry.image.onerror = () => {
            entry.failed = true;
            console.warn(`Sprite sheet "${name}": nie udało się wczytać pliku ${def.src}`);
        };
        entry.image.src = def.src;
    }
    sheets.set(name, entry);
}

const isReady = (entry) => Boolean(entry.image && entry.image.complete && entry.image.naturalWidth > 0);

// Sprawdza (raz, po wczytaniu), czy rozmiar pliku zgadza się z opisem, i ostrzega w konsoli.
function validate(name, entry) {
    if (entry.checked) return;
    entry.checked = true;
    const { def, image } = entry;
    const w = image.naturalWidth;
    const h = image.naturalHeight;
    const columns = Math.floor(w / def.frameWidth);
    const rows = Math.floor(h / def.frameHeight);

    if (w % def.frameWidth !== 0 || h % def.frameHeight !== 0) {
        warnOnce(`${name}:size`, `Sprite sheet "${name}": plik ma ${w}x${h} px, a klatka ${def.frameWidth}x${def.frameHeight} px, więc rozmiar pliku nie dzieli się równo na klatki.`);
    }
    for (const [animName, anim] of Object.entries(def.animations)) {
        const first = anim.column ?? 0;
        if (anim.row >= rows) {
            warnOnce(`${name}:${animName}:row`, `Sprite sheet "${name}", animacja "${animName}": wiersz ${anim.row} nie istnieje (plik ma ${rows} wierszy).`);
        } else if (first + anim.frames > columns) {
            warnOnce(`${name}:${animName}:cols`, `Sprite sheet "${name}", animacja "${animName}": potrzebuje ${first + anim.frames} kolumn, a plik ma ich ${columns}.`);
        }
    }
}

function getReady(name) {
    if (!name) return null;
    const entry = sheets.get(name);
    if (!entry) {
        warnOnce(`unknown:${name}`, `Nieznany sprite sheet "${name}". Dodaj go do SPRITE_SHEETS w animations.js.`);
        return null;
    }
    if (!isReady(entry)) return null;
    validate(name, entry);
    return entry;
}

// Czy arkusz o tej nazwie jest opisany w SPRITE_SHEETS (nie sprawdza, czy plik już się wczytał).
export function hasSpriteSheet(name) {
    return sheets.has(name);
}

// Rozmiar jednej klatki w pikselach gry albo null, gdy arkusza nie ma / jeszcze się ładuje.
export function getSheetFrameSize(name) {
    const entry = getReady(name);
    if (!entry) return null;
    return { w: entry.def.frameWidth, h: entry.def.frameHeight };
}

// Podsumowanie wczytywania arkuszy (do trybu debug).
export function getSheetReport() {
    const report = { ok: 0, loading: 0, error: 0 };
    for (const entry of sheets.values()) {
        if (entry.failed) report.error++;
        else if (isReady(entry)) report.ok++;
        else report.loading++;
    }
    return report;
}

// Animacja o danej nazwie albo zastępcza ("idle", a jak jej nie ma: pierwsza z listy).
function findAnimation(def, animName) {
    return def.animations[animName] ?? def.animations.idle ?? Object.values(def.animations)[0] ?? null;
}

// Numer klatki (od 0) dla animacji po `time` sekundach od jej początku.
function frameAt(anim, time) {
    const step = Math.floor(time * (anim.fps ?? 8));
    if (anim.loop === false) return Math.min(step, anim.frames - 1);
    return step % anim.frames;
}

// Animator obiektu: pamięta, jaka animacja gra i od ilu sekund. Użycie:
//   const animator = createAnimator("player");
//   animator.play("run");           // co klatkę (zmiana nazwy zaczyna animację od początku)
//   animator.update(dt);            // co klatkę
//   animator.draw(ctx, x, y, w, h); // rysuje bieżącą klatkę; false = brak arkusza (rysuj zastępczo)
export function createAnimator(sheetName) {
    let current = null; // nazwa animacji
    let time = 0;       // sekundy od początku animacji

    function pose() {
        const entry = sheets.get(sheetName);
        const anim = entry && current ? findAnimation(entry.def, current) : null;
        return { anim: current, frame: anim ? frameAt(anim, time) : 0 };
    }

    // Rysuje klatkę `frame` animacji `animName` w prostokącie (x, y, w, h), w pełnych pikselach.
    function drawFrame(ctx, animName, frame, x, y, w, h) {
        const entry = getReady(sheetName);
        if (!entry) return false;

        const { def, image } = entry;
        const anim = findAnimation(def, animName);
        if (!anim) return false;

        const column = (anim.column ?? 0) + Math.max(0, Math.min(frame, anim.frames - 1));
        ctx.save();
        ctx.imageSmoothingEnabled = false;
        ctx.drawImage(
            image,
            column * def.frameWidth, anim.row * def.frameHeight, def.frameWidth, def.frameHeight,
            Math.round(x), Math.round(y), Math.round(w), Math.round(h),
        );
        ctx.restore();
        return true;
    }

    return {
        get name() { return current; },
        get time() { return time; },
        get frame() { return pose().frame; },
        get frames() {
            const entry = sheets.get(sheetName);
            const anim = entry && current ? findAnimation(entry.def, current) : null;
            return anim ? anim.frames : 0;
        },
        pose,
        play(animName, restart = false) {
            if (animName !== current || restart) {
                current = animName;
                time = 0;
            }
        },
        update(dt) { time += dt; },
        draw(ctx, x, y, w, h) { return drawFrame(ctx, current, pose().frame, x, y, w, h); },
        drawFrame,
    };
}
