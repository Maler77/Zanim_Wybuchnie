// ============================================================================
//  POZIOMY W PLIKACH JSON
//  Poza poziomami zapisanymi w kodzie (levels.js) gra wczytuje poziomy z plików JSON w katalogu
//  src/data/levels/. Wystarczy wrzucić tam plik *.json (np. pobrany z edytora: menu główne ->
//  "Edytor poziomów" -> "Pobierz JSON") i odświeżyć stronę: poziom sam pojawi się w menu.
//
//  JAK GRA ZNAJDUJE PLIKI
//    1. Przeglądarka nie umie wylistować katalogu, ale lokalny serwer (python -m http.server) wystawia
//       jego listing jako stronę HTML, więc gra czyta z niej nazwy plików *.json. Dzięki temu nie trzeba
//       nic dopisywać.
//    2. Hosting bez listingu katalogu (np. GitHub Pages) takiej strony nie ma. Wtedy gra korzysta z
//       src/data/levels/index.json, czyli listy plików:   { "levels": ["poziom-1.json", "inny.json"] }
//       Wygenerujesz ją jednym poleceniem:  python src/data/levels/level-index-generator.py
//       (index.json jest też zawsze brany pod uwagę lokalnie: pliki z niego idą w menu pierwsze,
//       w podanej kolejności, a pozostałe po nich, sortowane po nazwie pliku).
//
//  KOLEJNOŚĆ I DUPLIKATY
//    Poziomy z levels.js są pierwsze. Poziom JSON o TEJ SAMEJ NAZWIE (pole "name") co poziom z kodu
//    zastępuje go w tym samym miejscu menu, więc po przeniesieniu poziomu z kodu do JSON nie ma
//    duplikatu. Pozostałe poziomy JSON dochodzą na końcu. Uszkodzony plik jest pomijany z ostrzeżeniem
//    w konsoli przeglądarki (F12), reszta poziomów działa dalej.
//
//  FORMAT PLIKU (wszystkie współrzędne w pikselach gry, 1 tile = 32 px, patrz levels.js):
//    name, subtitle, questionCategory ("easy" | "medium" | "hard"), background (lista tekstur tła),
//    timeLimit (s), width, height, hp (opcjonalnie), spawn { x, y }   (x = środek, y = pod stopami)
//    mode       "bombs" (domyślnie: rozbrój wszystkie bomby i dojdź do drzwi na prawym końcu),
//               "panel" (skradanka: jedna "bomba" to panel, wygrywasz po jego rozbrojeniu; zauważenie przez
//               strażnika włącza alarm i spadają spadochroniarze; pytania zawsze trudne = "hard") albo
//               "boss" (duża mapa, goni cię boss Kamil, który musi cię dotknąć; bomby to panele, wygrywasz po rozbrojeniu
//               wszystkich, zwykle 3; poziom musi mieć przeciwnika typu "boss")
//    paratroopers  tylko w trybie "panel": ilu przeciwników spada po alarmie (domyślnie 14)
//    platforms  [{ x, y, w, h, texture, textureMode?, solid?, oneWay?, grappleable? }]
//    bombs      [{ x, y }]                                              (x = środek, y = podłoże)
//    enemies    [{ type: "weak" | "strong" | "boss", x, y, direction?, speed?, area?: { x1, y1, x2, y2 } }]
//               boss (stara nazwa "kamikaze" nadal działa): wait? (s bezczynności na starcie), respawns? [{ x, y, stage?, side? }] (gdzie wraca,
//               gdy utknie; stage = przy ilu rozbrojonych panelach punkt jest używany; side "left" | "right" =
//               punkt musi leżeć po lewej / prawej od gracza, czyli za jego plecami), respawnDistance? (min. odległość
//               punktu od gracza w px, domyślnie 600; jeśli żaden punkt nie jest dość daleko, boss czeka)
//    exit       opcjonalnie { x, y }: drzwi wyjścia (tryb "bombs"; w trybie "panel" tylko gdy pole jest ustawione: po panelu trzeba do nich dojść); x = środek drzwi, y = powierzchnia pod nimi.
//               Domyślnie drzwi stoją na ulicy przy prawej krawędzi poziomu.
//    fallLimit  opcjonalnie: wysokość y, poniżej której spadnięcie zabiera 1 HP i cofa do checkpointu (poziomy na dachach,
//               gdzie zamiast kolców na dole jest przepaść; ustaw ją trochę poniżej najniższej platformy)
//    spikes     [{ x, y, w, h }]                                        (prostokąt, patrz spike())
//    jumpPads   [{ x, y, w, h, power? }]                                (prostokąt, patrz jumpPad())
//    checkpoints [{ x, y }]   dodatkowe punkty odrodzenia (x = środek, y = podłoże). Włączają się, gdy gracz stanie
//               na ziemi przy x (na wysokości y); liczą się tylko te dalej w prawo niż obecny checkpoint
//               (start albo ostatnia rozbrojona bomba). Po wejściu na checkpoint pojawia się krótki komunikat.
//    hints      [{ x, w, y?, h?, text, when? }]   podpowiedzi (samouczek): gdy środek gracza jest w pasie
//               x..x+w (opcjonalnie też w y..y+h), u góry ekranu pojawia się text. when: "armed" (tylko dopóki
//               są nierozbrojone bomby) albo "defused" (dopiero po rozbrojeniu wszystkich). W tekście [A] to
//               klawisz (rysowany jak przycisk), "\n" to nowy wiersz.
//               Drugi rodzaj: { on: "defuse" | "allDefused", text, duration? }  komunikat na `duration` sekund
//               (domyślnie 7) po rozbrojeniu bomby / po rozbrojeniu ostatniej bomby.
//    Elementy dekoracyjne (budynki, rekwizyty, lampy) to zwykłe platformy z "solid": false i teksturą z pliku
//    (kolejność na liście = kolejność rysowania: tło najpierw). Kolizję daje osobna, niewidoczna platforma
//    z "color": "transparent". Punkt zaczepienia haka to mała platforma "grappleable": true (patrz make_level1.py).
//  texture to nazwa z textures.js ("platform", "ground", "wall") albo ścieżka do obrazka z folderu
//  assets, np. "assets/budynek.png"; textureMode ("stretch" | "tile" | "cover") mówi, jak go rysować.
// ============================================================================

import { VIEW_HEIGHT } from "./config.js";
import { platform } from "./levels.js";
import { TEXTURES, textureKey } from "./textures.js";
import { ENEMY_TYPES, normalizeEnemyType } from "./enemies.js";

const MANIFEST_URL = new URL("../data/levels/index.json", import.meta.url);
const LEVELS_DIR = new URL("../data/levels/", import.meta.url);
const DRAFTS_KEY = "masywny.editor.drafts";
const AUTOSAVE_KEY = "masywny.editor.autosave";

export const QUESTION_CATEGORIES = ["easy", "medium", "hard"];
export const LEVEL_MODES = ["bombs", "panel", "boss"];
export const PANEL_QUESTION_CATEGORY = "hard"; // poziomy z panelem zawsze losują pytania trudne

const isNumber = (value) => typeof value === "number" && Number.isFinite(value);

// Pusty poziom dla edytora: podłoga i miejsce startu.
export function newLevel() {
    return {
        name: "Nowy poziom",
        subtitle: "",
        questionCategory: "easy",
        background: ["background"],
        timeLimit: 60,
        width: 1280,
        height: VIEW_HEIGHT,
        spawn: { x: 64, y: 320 },
        platforms: [{ x: 0, y: 320, w: 1280, h: 40, texture: "ground" }],
        bombs: [],
        enemies: [],
        spikes: [],
        jumpPads: [],
    };
}

// Czyści poziom do postaci zapisywanej w pliku (bez pól tymczasowych i wartości domyślnych).
export function serializeLevel(level) {
    const out = {
        name: level.name,
        subtitle: level.subtitle ?? "",
        questionCategory: level.questionCategory,
        background: [...(level.background ?? ["background"])],
        timeLimit: level.timeLimit,
        width: level.width,
        height: level.height ?? VIEW_HEIGHT,
    };
    if (isNumber(level.hp)) out.hp = level.hp;
    if (isNumber(level.fallLimit)) out.fallLimit = level.fallLimit;
    if (level.exit && isNumber(level.exit.x) && isNumber(level.exit.y)) out.exit = { x: level.exit.x, y: level.exit.y };
    if (level.thumbnail) out.thumbnail = level.thumbnail;
    if (level.mode === "panel") {
        out.mode = "panel";
        out.questionCategory = PANEL_QUESTION_CATEGORY;
        if (isNumber(level.paratroopers)) out.paratroopers = level.paratroopers;
    } else if (level.mode === "boss") {
        out.mode = "boss";
    }
    out.spawn = { x: level.spawn.x, y: level.spawn.y };

    out.platforms = (level.platforms ?? []).map((p) => {
        const item = { x: p.x, y: p.y, w: p.w, h: p.h, texture: p.textureSource ?? p.texture ?? "platform" };
        if (p.textureMode && p.textureMode !== "stretch") item.textureMode = p.textureMode;
        if (p.color && p.color !== "#24343d") item.color = p.color;
        if (p.solid === false) item.solid = false;
        if (p.oneWay) item.oneWay = true;
        if (p.grappleable) item.grappleable = true;
        return item;
    });
    out.bombs = (level.bombs ?? []).map((b) => ({ x: b.x, y: b.y }));
    out.enemies = (level.enemies ?? []).map((e) => {
        const item = { type: e.type, x: e.x, y: e.y };
        if (e.id) item.id = e.id;
        if (e.direction === -1) item.direction = -1;
        if (isNumber(e.speed)) item.speed = e.speed;
        if (isNumber(e.chaseSpeed)) item.chaseSpeed = e.chaseSpeed;
        if (e.area) item.area = { x1: e.area.x1, y1: e.area.y1, x2: e.area.x2, y2: e.area.y2 };
        if (e.vision) item.vision = { ...e.vision };
        if (isNumber(e.wait) && e.wait > 0) item.wait = e.wait;
        if (Array.isArray(e.respawns) && e.respawns.length > 0) {
            item.respawns = e.respawns.map((r) => {
                const point = { x: r.x, y: r.y };
                if (isNumber(r.stage)) point.stage = r.stage;
                if (r.side === "left" || r.side === "right") point.side = r.side;
                return point;
            });
        }
        if (isNumber(e.respawnDistance)) item.respawnDistance = e.respawnDistance;
        return item;
    });
    if (Array.isArray(level.checkpoints) && level.checkpoints.length > 0) {
        out.checkpoints = level.checkpoints.map((c) => ({ x: c.x, y: c.y }));
    }
    if (Array.isArray(level.hints) && level.hints.length > 0) out.hints = level.hints.map((h) => ({ ...h }));
    out.spikes = (level.spikes ?? []).map((s) => ({ x: s.x, y: s.y, w: s.w, h: s.h }));
    out.jumpPads = (level.jumpPads ?? []).map((j) => {
        const item = { x: j.x, y: j.y, w: j.w, h: j.h };
        if (isNumber(j.power) && j.power !== 1) item.power = j.power;
        return item;
    });
    return out;
}

// Zamienia poziom z JSON na obiekt dla gry (tak jak poziomy z levels.js). Rzuca błąd z opisem
// problemu, gdy plik jest uszkodzony.
export function normalizeLevel(raw) {
    if (!raw || typeof raw !== "object") throw new Error("poziom nie jest obiektem");
    const need = (condition, message) => { if (!condition) throw new Error(message); };

    need(typeof raw.name === "string" && raw.name.trim() !== "", "brak pola name");
    need(QUESTION_CATEGORIES.includes(raw.questionCategory ?? "easy"), "questionCategory musi być easy, medium albo hard");
    const mode = raw.mode ?? "bombs";
    need(LEVEL_MODES.includes(mode), 'mode musi być "bombs", "panel" albo "boss"');
    need(raw.paratroopers === undefined || (Number.isInteger(raw.paratroopers) && raw.paratroopers >= 1 && raw.paratroopers <= 60),
        "paratroopers musi być liczbą całkowitą od 1 do 60");
    need(isNumber(raw.timeLimit ?? 60) && (raw.timeLimit ?? 60) > 0, "timeLimit musi być liczbą większą od 0");
    need(isNumber(raw.width) && raw.width > 0, "width musi być liczbą większą od 0");
    need(isNumber(raw.spawn?.x) && isNumber(raw.spawn?.y), "spawn musi mieć x i y");
    need(raw.fallLimit === undefined || isNumber(raw.fallLimit), "fallLimit musi być liczbą");
    need(raw.exit === undefined || (isNumber(raw.exit?.x) && isNumber(raw.exit?.y)), "exit musi mieć x i y");

    const list = (key) => {
        const value = raw[key] ?? [];
        need(Array.isArray(value), `${key} musi być listą`);
        return value;
    };
    const rect = (item, where) => need(
        [item.x, item.y, item.w, item.h].every(isNumber) && item.w > 0 && item.h > 0,
        `${where}: x, y, w, h muszą być liczbami (w i h > 0)`,
    );

    const platforms = list("platforms").map((p, i) => {
        rect(p, `platforms[${i}]`);
        const item = platform(p.x, p.y, p.w, p.h, textureKey(p.texture ?? "platform", p.textureMode), {
            color: p.color,
            solid: p.solid,
            oneWay: p.oneWay,
            grappleable: p.grappleable,
        });
        // Obrazek z pliku: pamiętamy oryginalną ścieżkę (item.texture to wewnętrzny klucz), żeby edytor
        // mógł poziom z powrotem zapisać do JSON.
        if (p.texture && !TEXTURES[p.texture]) {
            item.textureSource = p.texture;
            item.textureMode = p.textureMode ?? "stretch";
        }
        return item;
    });
    const spikes = list("spikes").map((s, i) => {
        rect(s, `spikes[${i}]`);
        return { x: s.x, y: s.y, w: s.w, h: s.h };
    });
    const jumpPads = list("jumpPads").map((j, i) => {
        rect(j, `jumpPads[${i}]`);
        return { x: j.x, y: j.y, w: j.w, h: j.h, power: j.power ?? 1 };
    });
    const bombs = list("bombs").map((b, i) => {
        need(isNumber(b.x) && isNumber(b.y), `bombs[${i}]: x i y muszą być liczbami`);
        return { ...b };
    });
    const enemies = list("enemies").map((e, i) => {
        need(Object.hasOwn(ENEMY_TYPES, normalizeEnemyType(e.type)), `enemies[${i}]: type musi być jednym z: ${Object.keys(ENEMY_TYPES).join(", ")}`);
        need(isNumber(e.x) && isNumber(e.y), `enemies[${i}]: x i y muszą być liczbami`);
        need(e.wait === undefined || (isNumber(e.wait) && e.wait >= 0), `enemies[${i}]: wait musi być liczbą >= 0`);
        need(e.respawns === undefined || (Array.isArray(e.respawns) && e.respawns.every((r) => isNumber(r?.x) && isNumber(r?.y))),
            `enemies[${i}]: respawns musi być listą punktów { x, y, stage?, side? }`);
        need(e.respawnDistance === undefined || (isNumber(e.respawnDistance) && e.respawnDistance >= 0), `enemies[${i}]: respawnDistance musi być liczbą >= 0`);
        return { ...e, type: normalizeEnemyType(e.type) }; // stara nazwa "kamikaze" to teraz "boss"
    });

    const checkpoints = list("checkpoints").map((c, i) => {
        need(isNumber(c?.x) && isNumber(c?.y), `checkpoints[${i}]: x i y muszą być liczbami`);
        return { x: c.x, y: c.y };
    });
    const hints = list("hints").map((h, i) => {
        need(typeof h?.text === "string" && h.text !== "", `hints[${i}]: brak pola text`);
        if (h.on !== undefined) {
            need(h.on === "defuse" || h.on === "allDefused", `hints[${i}]: on musi być "defuse" albo "allDefused"`);
        } else {
            need(isNumber(h.x) && isNumber(h.w) && h.w > 0, `hints[${i}]: x i w (> 0) muszą być liczbami`);
            need(h.y === undefined || isNumber(h.y), `hints[${i}]: y musi być liczbą`);
            need(h.h === undefined || isNumber(h.h), `hints[${i}]: h musi być liczbą`);
            need(h.when === undefined || h.when === "armed" || h.when === "defused", `hints[${i}]: when musi być "armed" albo "defused"`);
        }
        return { ...h };
    });

    // Panel to dokładnie jedna "bomba" i zawsze trudne pytania.
    if (mode === "panel") need(bombs.length === 1, `poziom z panelem musi mieć dokładnie 1 bombę (panel), a ma ${bombs.length}`);
    if (mode === "boss") {
        need(bombs.length >= 1, "poziom bossa musi mieć co najmniej 1 panel (bombę), zwykle 3");
        need(enemies.some((e) => e.type === "boss"), 'poziom bossa musi mieć przeciwnika typu "boss"');
    }

    const level = {
        ...raw,
        name: raw.name,
        subtitle: raw.subtitle ?? "",
        mode,
        questionCategory: mode === "panel" ? PANEL_QUESTION_CATEGORY : (raw.questionCategory ?? "easy"),
        background: raw.background ?? ["background"],
        timeLimit: raw.timeLimit ?? 60,
        width: raw.width,
        height: raw.height ?? VIEW_HEIGHT,
        spawn: { x: raw.spawn.x, y: raw.spawn.y },
        platforms,
        bombs,
        enemies,
        spikes,
        jumpPads,
        checkpoints,
        hints,
    };
    if (!isNumber(level.hp)) delete level.hp;
    if (mode !== "panel") delete level.paratroopers;
    return level;
}

const naturalCompare = (a, b) => a.localeCompare(b, "pl", { numeric: true, sensitivity: "base" });

// Nazwy plików *.json z listingu katalogu (strona HTML z linkami, którą daje m.in. python -m http.server).
// Gdy serwer listingu nie ma, zwraca pustą listę.
async function listDirectory() {
    try {
        const response = await fetch(LEVELS_DIR, { cache: "no-cache" });
        if (!response.ok) return [];
        if (!(response.headers.get("content-type") ?? "").includes("text/html")) return [];
        const html = await response.text();
        const names = [];
        for (const match of html.matchAll(/href\s*=\s*["']([^"'#?]+)["']/gi)) {
            let name;
            try { name = decodeURIComponent(match[1]); } catch { continue; }
            name = name.split("/").pop();
            if (name.toLowerCase().endsWith(".json") && name.toLowerCase() !== "index.json") names.push(name);
        }
        return names;
    } catch {
        return [];
    }
}

// Lista z index.json (opcjonalna). Brak pliku to nie błąd.
async function readManifest() {
    try {
        const response = await fetch(MANIFEST_URL, { cache: "no-cache" });
        if (!response.ok) return null;
        const list = (await response.json()).levels;
        if (!Array.isArray(list)) throw new Error('pole "levels" musi być listą nazw plików');
        return list.filter((name) => typeof name === "string" && name !== "index.json");
    } catch (error) {
        console.warn(`Nie można odczytać src/data/levels/index.json: ${error.message}`);
        return null;
    }
}

// Wczytuje wszystkie poziomy JSON z src/data/levels/ (patrz opis na górze pliku).
export async function loadJsonLevels() {
    const [manifest, listed] = await Promise.all([readManifest(), listDirectory()]);

    if (!manifest && listed.length === 0) {
        console.info("Brak poziomów JSON: serwer nie pokazuje listingu src/data/levels/ i nie ma index.json " +
            "(wygeneruj go: python src/data/levels/level-index-generator.py).");
        return [];
    }

    // Najpierw pliki z index.json (w jego kolejności), potem reszta z listingu po nazwie.
    const names = [...new Set(manifest ?? [])];
    const rest = listed.filter((name) => !names.includes(name)).sort(naturalCompare);
    names.push(...new Set(rest));

    const levels = [];
    for (const file of names) {
        try {
            const response = await fetch(new URL(encodeURIComponent(file), LEVELS_DIR), { cache: "no-cache" });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const level = normalizeLevel(await response.json());
            level.source = file;
            levels.push(level);
        } catch (error) {
            console.warn(`Poziom ${file} pominięty: ${error.message}`);
        }
    }
    return levels;
}

// Dokłada poziomy JSON do listy poziomów gry: poziom o tej samej nazwie co istniejący go zastępuje
// (w tym samym miejscu), pozostałe trafiają na koniec. Modyfikuje `target` (zwykle LEVELS).
export function mergeJsonLevels(target, jsonLevels) {
    for (const level of jsonLevels) {
        const index = target.findIndex((existing) => existing.name === level.name);
        if (index === -1) {
            target.push(level);
        } else {
            console.info(`Poziom "${level.name}" z ${level.source} zastępuje poziom o tej samej nazwie z levels.js.`);
            target[index] = level;
        }
    }
    return target;
}

// ---------- Szkice w przeglądarce (localStorage) ----------

function readJson(key, fallback) {
    try {
        const text = localStorage.getItem(key);
        return text ? JSON.parse(text) : fallback;
    } catch {
        return fallback;
    }
}

function writeJson(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch {
        return false; // zablokowany localStorage (np. tryb prywatny)
    }
}

export const listDrafts = () => Object.keys(readJson(DRAFTS_KEY, {}));
export const loadDraft = (name) => readJson(DRAFTS_KEY, {})[name] ?? null;

export function saveDraft(level) {
    const drafts = readJson(DRAFTS_KEY, {});
    drafts[level.name] = serializeLevel(level);
    return writeJson(DRAFTS_KEY, drafts);
}

export function deleteDraft(name) {
    const drafts = readJson(DRAFTS_KEY, {});
    delete drafts[name];
    return writeJson(DRAFTS_KEY, drafts);
}

// Automatyczny zapis ostatnio edytowanego poziomu (żeby odświeżenie strony niczego nie traciło).
export const saveAutosave = (level) => writeJson(AUTOSAVE_KEY, serializeLevel(level));
export const loadAutosave = () => readJson(AUTOSAVE_KEY, null);