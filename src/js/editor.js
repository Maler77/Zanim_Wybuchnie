// ============================================================================
//  EDYTOR POZIOMÓW
//  Otwierany z menu głównego. Edytuje poziom w formacie JSON (patrz levelstore.js), który gra
//  wczytuje z src/data/levels/. Cały interfejs (panel po lewej) tworzy ten plik, a mapę rysuje na
//  tym samym canvasie co gra.
//
//  STEROWANIE
//    kamera        najedź kursorem na krawędź ekranu (albo strzałki, gdy nic nie jest zaznaczone)
//    kółko myszy   przybliżenie / oddalenie
//    lewy przycisk używa wybranego narzędzia, prawy przycisk usuwa obiekt pod kursorem
//    Del           usuwa zaznaczony obiekt, strzałki przesuwają go o krok siatki
//    Ctrl+Z / Ctrl+Y   cofnij / ponów,   Ctrl+S   zapisz szkic,   T   testuj poziom,   Esc   narzędzie "Zaznacz"
//
//  Współrzędne to piksele gry (1 tile = 32 px). Siatka przyciągania (snap) jest wybierana w panelu.
// ============================================================================

import { TILE, VIEW_HEIGHT } from "./config.js";
import { TEXTURES, drawBox, drawTexture, getTextureSize, overrideTextureSource, textureKey } from "./textures.js";
import { ENEMY_TYPES, normalizeEnemyType } from "./enemies.js";
import {
    PANEL_QUESTION_CATEGORY, QUESTION_CATEGORIES, listDrafts, loadAutosave, loadDraft, newLevel, normalizeLevel,
    saveAutosave, saveDraft, serializeLevel,
} from "./levelstore.js";

const BOMB_SIZE = TILE;                    // bomba: 1 x 1 tile
const SPAWN_SIZE = { w: 28, h: 28 };       // hitbox gracza (PLAYER_HITBOX w game.js)
const SPIKE_HEIGHT = TILE / 4;
const SURFACE_REACH = 96;                  // jak daleko pod kursorem szukamy podłoża dla obiektów punktowych
const EDGE = 40;                           // strefa przy krawędzi ekranu, w której przesuwa się kamera (px ekranu)
const EDGE_SPEED = 600;                    // prędkość kamery przy krawędzi (px ekranu / s)
const VIEW_MARGIN = 96;                    // o ile kamera może wyjść poza poziom (px gry)
const SNAPS = [1, 2, 4, 8, 16, 32];
const HANDLE = 8;                          // rozmiar uchwytów zmiany rozmiaru (px ekranu)
const MIN_ZOOM = 1;
const MAX_ZOOM = 4;

const TOOLS = [
    { id: "select", group: "Edycja", label: "Zaznacz / przesuń", hint: "Klik zaznacza, przeciągnięcie przesuwa, uchwyty zmieniają rozmiar platform. Del usuwa." },
    { id: "erase", group: "Edycja", label: "Gumka", hint: "Klik usuwa obiekt pod kursorem (prawy przycisk myszy robi to zawsze)." },
    { id: "block", group: "Teren (przeciągnij)", label: "Blok / ściana", hint: "Przeciągnij prostokąt. Z wybranym assetem: klik wkleja obrazek (rozmiar oryginalny) albo przeciągasz obszar." },
    { id: "oneway", group: "Teren (przeciągnij)", label: "Platforma jednostronna", hint: "Przeciągnij prostokąt. Przez taką platformę można przejść od dołu." },
    { id: "spike", group: "Teren (przeciągnij)", label: "Kolce", hint: "Przeciągnij w poziomie: kolce o szerokości całych tili, stoją na podłożu pod kursorem." },
    { id: "spawn", group: "Obiekty (kliknij)", label: "Punkt startu", hint: "Klik ustawia miejsce startu gracza (jest tylko jedno)." },
    { id: "bomb", group: "Obiekty (kliknij)", label: "Bomba / panel", hint: "Klik stawia bombę na podłożu pod kursorem. W trybie „Panel” jest tylko jeden (nowy zastępuje stary)." },
    { id: "enemy-weak", group: "Obiekty (kliknij)", label: "Przeciwnik słaby", hint: "Klik stawia przeciwnika, potem przeciągnij prostokąt pola patrolu (Enter = domyślne pole)." },
    { id: "enemy-strong", group: "Obiekty (kliknij)", label: "Przeciwnik silny", hint: "Klik stawia przeciwnika, potem przeciągnij prostokąt pola patrolu (Enter = domyślne pole)." },
    { id: "enemy-boss", group: "Obiekty (kliknij)", label: "Boss (Kamil)", hint: "Klik stawia bossa (tryb „Boss”). Goni gracza po całej mapie i musi go dotknąć; miejsca pojawiania się po utknięciu wpiszesz w polu „Respawny”." },
    { id: "jumppad", group: "Obiekty (kliknij)", label: "Skocznia", hint: "Klik stawia skocznię (1 tile) na podłożu pod kursorem." },
    { id: "grapple", group: "Obiekty (kliknij)", label: "Punkt zaczepienia haka", hint: "Klik stawia punkt, na którym zaczepia się hak (nie jest solidny)." },
];

// Rodzaje obiektów (klucze w modelu poziomu). Kolejność = kolejność rysowania.
const KINDS = ["platforms", "spikes", "jumpPads", "bombs", "enemies"];

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const isPath = (texture) => !TEXTURES[texture];

function el(tag, props = {}, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(props)) {
        if (value === false || value === undefined || value === null) continue;
        if (key === "class") node.className = value;
        else if (key === "text") node.textContent = value;
        else if (key.startsWith("on")) node.addEventListener(key.slice(2).toLowerCase(), value);
        else node.setAttribute(key, value === true ? "" : value);
    }
    node.append(...children.flat().filter((child) => child !== null && child !== undefined && child !== false));
    return node;
}

export function createEditor({ canvas, container, builtinLevels = [], onTest, onExit }) {
    // ------------------------------------------------------------------ stan
    let active = false;
    let model = newLevel();
    let sel = null;              // { kind, index } albo { kind: "spawn" }
    let tool = "select";
    let snapSize = 8;
    let magnet = true;           // przyciąganie obiektów punktowych do podłoża
    let showGrid = true;
    let zoom = 2;
    const cam = { x: 0, y: 0 };  // lewy górny róg widoku w pikselach gry
    const mouse = { x: 0, y: 0, wx: 0, wy: 0, inside: false };
    let drag = null;
    let areaFor = null;          // indeks przeciwnika, któremu zaznaczamy pole patrolu
    let dirty = false;
    let flash = { text: "", time: 0 };

    const asset = { path: "", mode: "original", solid: true, img: null, w: 0, h: 0, status: "" };
    const toolOpts = { texture: "platform", power: 1 };

    let history = [];
    let hIndex = -1;
    let autosaveTimer = null;

    // ------------------------------------------------------------------ historia
    function resetHistory() {
        history = [JSON.stringify(model)];
        hIndex = 0;
    }

    function commit() {
        const text = JSON.stringify(model);
        if (text === history[hIndex]) return;
        history = history.slice(0, hIndex + 1);
        history.push(text);
        if (history.length > 100) history.shift();
        hIndex = history.length - 1;
        dirty = true;
        clearTimeout(autosaveTimer);
        autosaveTimer = setTimeout(() => saveAutosave(model), 400);
    }

    function restore(index) {
        hIndex = index;
        model = JSON.parse(history[hIndex]);
        sel = null;
        areaFor = null;
        dirty = true;
        refreshAll();
    }

    const undo = () => { if (hIndex > 0) restore(hIndex - 1); };
    const redo = () => { if (hIndex < history.length - 1) restore(hIndex + 1); };

    // ------------------------------------------------------------------ geometria
    const snapTo = (value) => Math.round(value / snapSize) * snapSize;

    function panelWidth() {
        return panel.offsetWidth;
    }

    function toWorld(cssX, cssY) {
        return { x: (cssX - panelWidth()) / zoom + cam.x, y: cssY / zoom + cam.y };
    }

    // Podłoże pod punktem (x, y): górna krawędź najwyższej platformy pod kursorem w zasięgu SURFACE_REACH.
    function surfaceY(x, y) {
        if (!magnet) return null;
        let best = null;
        for (const p of model.platforms) {
            if (p.solid === false) continue;
            if (x < p.x || x > p.x + p.w) continue;
            if (p.y < y - 12 || p.y - y > SURFACE_REACH) continue;
            if (best === null || p.y < best) best = p.y;
        }
        return best;
    }

    // Pozycja obiektu punktowego: x = środek (przyciągnięty do siatki), y = podłoże.
    function pointPos(x, y) {
        const px = snapTo(x);
        return { x: px, y: surfaceY(px, y) ?? snapTo(y) };
    }

    function enemySize(type) {
        const def = ENEMY_TYPES[normalizeEnemyType(type)];
        return { w: def.width, h: def.height };
    }

    // Prostokąt obiektu (do rysowania i klikania).
    function rectOf(kind, item) {
        if (kind === "bombs") return { x: item.x - BOMB_SIZE / 2, y: item.y - BOMB_SIZE, w: BOMB_SIZE, h: BOMB_SIZE };
        if (kind === "enemies") {
            const { w, h } = enemySize(item.type);
            return { x: item.x - w / 2, y: item.y - h, w, h };
        }
        if (kind === "spawn") return { x: item.x - SPAWN_SIZE.w / 2, y: item.y - SPAWN_SIZE.h, w: SPAWN_SIZE.w, h: SPAWN_SIZE.h };
        return { x: item.x, y: item.y, w: item.w, h: item.h };
    }

    const inRect = (r, p, pad = 0) => p.x >= r.x - pad && p.x <= r.x + r.w + pad && p.y >= r.y - pad && p.y <= r.y + r.h + pad;

    // Obiekt pod punktem: od góry (ostatnio narysowany) do dołu. Zwraca { kind, index } albo null.
    function hitTest(p) {
        const pad = 2 / zoom;
        if (inRect(rectOf("spawn", model.spawn), p, pad)) return { kind: "spawn" };
        for (const kind of [...KINDS].reverse()) {
            const list = model[kind];
            for (let i = list.length - 1; i >= 0; i--) {
                if (inRect(rectOf(kind, list[i]), p, kind === "platforms" ? 0 : pad)) return { kind, index: i };
            }
        }
        return null;
    }

    const getObj = (s) => (!s ? null : s.kind === "spawn" ? model.spawn : model[s.kind][s.index] ?? null);

    function handles(r) {
        const mx = r.x + r.w / 2;
        const my = r.y + r.h / 2;
        return {
            nw: [r.x, r.y], n: [mx, r.y], ne: [r.x + r.w, r.y],
            e: [r.x + r.w, my], se: [r.x + r.w, r.y + r.h], s: [mx, r.y + r.h],
            sw: [r.x, r.y + r.h], w: [r.x, my],
        };
    }

    function handleAt(r, p) {
        const reach = HANDLE / zoom;
        for (const [id, [hx, hy]] of Object.entries(handles(r))) {
            if (Math.abs(p.x - hx) <= reach && Math.abs(p.y - hy) <= reach) return id;
        }
        return null;
    }

    // ------------------------------------------------------------------ operacje na modelu
    function nextEnemyId(type) {
        let n = model.enemies.filter((e) => e.type === type).length + 1;
        while (model.enemies.some((e) => e.id === `${type}-${n}`)) n++;
        return `${type}-${n}`;
    }

    function select(next) {
        sel = next;
        buildProps();
    }

    function addTo(kind, item) {
        model[kind].push(item);
        select({ kind, index: model[kind].length - 1 });
        commit();
    }

    function removeSelection(target = sel) {
        if (!target || target.kind === "spawn") return;
        model[target.kind].splice(target.index, 1);
        if (areaFor !== null) areaFor = null;
        select(null);
        commit();
    }

    function eraseAt(p) {
        const hit = hitTest(p);
        if (hit) removeSelection(hit);
    }

    function platformTemplate(rect) {
        const item = { x: rect.x, y: rect.y, w: rect.w, h: rect.h, texture: toolOpts.texture };
        if (tool === "oneway") {
            item.texture = "platform";
            item.oneWay = true;
        }
        if (tool === "block" && asset.path) {
            item.texture = asset.path;
            item.textureMode = asset.mode === "original" ? "stretch" : asset.mode;
            if (!asset.solid) item.solid = false;
        }
        return item;
    }

    function placePoint(p) {
        if (tool === "spawn") {
            const pos = pointPos(p.x, p.y);
            model.spawn = { x: pos.x, y: pos.y };
            select({ kind: "spawn" });
            commit();
        } else if (tool === "bomb") {
            const pos = pointPos(p.x, p.y);
            if (model.mode === "panel") model.bombs = []; // panel jest tylko jeden
            addTo("bombs", { x: pos.x, y: pos.y });
        } else if (tool === "enemy-boss") {
            const pos = pointPos(p.x, p.y);
            addTo("enemies", { type: "boss", x: pos.x, y: pos.y, id: nextEnemyId("boss"), wait: 5 });
        } else if (tool === "enemy-weak" || tool === "enemy-strong") {
            const type = tool === "enemy-weak" ? "weak" : "strong";
            const pos = pointPos(p.x, p.y);
            addTo("enemies", { type, x: pos.x, y: pos.y, id: nextEnemyId(type) });
            areaFor = model.enemies.length - 1; // następne przeciągnięcie ustawia pole patrolu
        } else if (tool === "jumppad") {
            const pos = pointPos(p.x, p.y);
            addTo("jumpPads", { x: pos.x - TILE / 2, y: pos.y - SPIKE_HEIGHT, w: TILE, h: SPIKE_HEIGHT, power: toolOpts.power });
        } else if (tool === "grapple") {
            const cx = snapTo(p.x);
            const cy = snapTo(p.y);
            addTo("platforms", { x: cx - 12, y: cy - 12, w: 24, h: 24, texture: "platform", solid: false, grappleable: true, color: "#d1a94f" });
        }
    }

    // Wklejenie assetu w oryginalnym rozmiarze: obrazek stoi dolnym środkiem na podłożu pod kursorem.
    function stampAsset(p) {
        if (!asset.w || !asset.h) { say("Asset jeszcze się nie wczytał albo nie ma pliku."); return; }
        const pos = pointPos(p.x, p.y);
        addTo("platforms", platformTemplate({ x: Math.round(pos.x - asset.w / 2), y: pos.y - asset.h, w: asset.w, h: asset.h }));
    }

    // ------------------------------------------------------------------ wskaźnik myszy
    function updateMouse(event) {
        const rect = canvas.getBoundingClientRect();
        mouse.x = event.clientX - rect.left;
        mouse.y = event.clientY - rect.top;
        const w = toWorld(mouse.x, mouse.y);
        mouse.wx = w.x;
        mouse.wy = w.y;
    }

    function normalizeRect(x0, y0, x1, y1) {
        return { x: Math.min(x0, x1), y: Math.min(y0, y1), w: Math.abs(x1 - x0), h: Math.abs(y1 - y0) };
    }

    function onPointerDown(event) {
        if (!active) return;
        document.activeElement?.blur?.();
        updateMouse(event);
        const p = { x: mouse.wx, y: mouse.wy };

        if (event.button === 2) { eraseAt(p); return; }
        if (event.button !== 0) return;
        canvas.setPointerCapture(event.pointerId);

        if (areaFor !== null) {
            drag = { type: "area", x0: snapTo(p.x), y0: snapTo(p.y), x1: snapTo(p.x), y1: snapTo(p.y) };
            return;
        }

        if (tool === "select") {
            if (sel && sel.kind === "platforms") {
                const handle = handleAt(rectOf("platforms", getObj(sel)), p);
                if (handle) {
                    drag = { type: "resize", handle, orig: { ...getObj(sel) } };
                    return;
                }
            }
            const hit = hitTest(p);
            select(hit);
            if (hit) drag = { type: "move", start: p, orig: { ...getObj(hit) }, kind: hit.kind, moved: false };
        } else if (tool === "erase") {
            eraseAt(p);
        } else if (tool === "block" && asset.path && asset.mode === "original") {
            stampAsset(p);
        } else if (tool === "block" || tool === "oneway") {
            drag = { type: "create", x0: snapTo(p.x), y0: snapTo(p.y), x1: snapTo(p.x), y1: snapTo(p.y), sx: mouse.x, sy: mouse.y };
        } else if (tool === "spike") {
            const pos = pointPos(p.x, p.y);
            drag = { type: "spike", x0: snapTo(p.x), y: pos.y, x1: snapTo(p.x) };
        } else {
            placePoint(p);
        }
    }

    function onPointerMove(event) {
        if (!active) return;
        updateMouse(event);
        mouse.inside = true;
        if (!drag) return;
        const p = { x: mouse.wx, y: mouse.wy };

        if (drag.type === "create" || drag.type === "area") {
            drag.x1 = snapTo(p.x);
            drag.y1 = snapTo(p.y);
        } else if (drag.type === "spike") {
            drag.x1 = snapTo(p.x);
        } else if (drag.type === "move") {
            const dx = p.x - drag.start.x;
            const dy = p.y - drag.start.y;
            const target = getObj(sel);
            if (!target) return;
            if (Math.abs(dx) + Math.abs(dy) > 2 / zoom) drag.moved = true;
            if (!drag.moved) return;
            if (drag.kind === "spawn" || drag.kind === "bombs" || drag.kind === "enemies") {
                const pos = pointPos(drag.orig.x + dx, drag.orig.y + dy);
                target.x = pos.x;
                target.y = pos.y;
            } else {
                target.x = snapTo(drag.orig.x + dx);
                target.y = snapTo(drag.orig.y + dy);
            }
            syncProps();
        } else if (drag.type === "resize") {
            const target = getObj(sel);
            if (!target) return;
            const o = drag.orig;
            let left = o.x, top = o.y, right = o.x + o.w, bottom = o.y + o.h;
            const gx = snapTo(p.x);
            const gy = snapTo(p.y);
            if (drag.handle.includes("w")) left = Math.min(gx, right - snapSize);
            if (drag.handle.includes("e")) right = Math.max(gx, left + snapSize);
            if (drag.handle.includes("n")) top = Math.min(gy, bottom - snapSize);
            if (drag.handle.includes("s")) bottom = Math.max(gy, top + snapSize);
            Object.assign(target, { x: left, y: top, w: right - left, h: bottom - top });
            syncProps();
        }
    }

    function onPointerUp(event) {
        if (!active || !drag) return;
        const finished = drag;
        drag = null;
        try { canvas.releasePointerCapture(event.pointerId); } catch { /* nie był przechwycony */ }

        if (finished.type === "create") {
            let r = normalizeRect(finished.x0, finished.y0, finished.x1, finished.y1);
            const clicked = Math.hypot(mouse.x - finished.sx, mouse.y - finished.sy) < 4;
            if (clicked || r.w === 0 || r.h === 0) {
                r = tool === "oneway"
                    ? { x: finished.x0, y: finished.y0, w: 2 * TILE, h: 12 }
                    : { x: finished.x0, y: finished.y0, w: TILE, h: TILE };
            }
            addTo("platforms", platformTemplate(r));
        } else if (finished.type === "spike") {
            const dx = finished.x1 - finished.x0;
            const count = Math.max(1, Math.round(Math.abs(dx) / TILE));
            const x = dx < 0 ? finished.x0 - count * TILE : finished.x0;
            addTo("spikes", { x, y: finished.y - SPIKE_HEIGHT, w: count * TILE, h: SPIKE_HEIGHT });
        } else if (finished.type === "area") {
            const r = normalizeRect(finished.x0, finished.y0, finished.x1, finished.y1);
            const enemy = model.enemies[areaFor];
            if (enemy && r.w >= enemySize(enemy.type).w && r.h > 0) {
                enemy.area = { x1: r.x, y1: r.y, x2: r.x + r.w, y2: r.y + r.h };
                areaFor = null;
                buildProps();
                commit();
            } else {
                say("Pole patrolu jest za małe. Przeciągnij większy prostokąt albo naciśnij Enter (domyślne pole).");
            }
        } else if (finished.type === "move" || finished.type === "resize") {
            if (finished.type === "resize" || finished.moved) commit();
        }
    }

    function onWheel(event) {
        if (!active) return;
        event.preventDefault();
        updateMouse(event);
        const before = { x: mouse.wx, y: mouse.wy };
        setZoom(zoom + (event.deltaY < 0 ? 1 : -1));
        // Punkt pod kursorem zostaje w tym samym miejscu ekranu.
        cam.x = before.x - (mouse.x - panelWidth()) / zoom;
        cam.y = before.y - mouse.y / zoom;
        clampCamera();
    }

    function setZoom(value) {
        zoom = clamp(value, MIN_ZOOM, MAX_ZOOM);
        if (zoomLabel) zoomLabel.textContent = `${zoom}x`;
    }

    function clampCamera() {
        const viewW = (canvas.clientWidth - panelWidth()) / zoom;
        const viewH = canvas.clientHeight / zoom;
        const maxX = Math.max(-VIEW_MARGIN, model.width - viewW + VIEW_MARGIN);
        const maxY = Math.max(-VIEW_MARGIN, model.height - viewH + VIEW_MARGIN);
        cam.x = clamp(cam.x, -VIEW_MARGIN, maxX);
        cam.y = clamp(cam.y, -VIEW_MARGIN, maxY);
    }

    function fitView() {
        zoom = clamp(Math.floor(canvas.clientHeight / Math.max(model.height, VIEW_HEIGHT)), MIN_ZOOM, 3);
        if (zoomLabel) zoomLabel.textContent = `${zoom}x`;
        const viewH = canvas.clientHeight / zoom;
        cam.x = -24;
        cam.y = model.height - viewH + 24;
        clampCamera();
    }

    // ------------------------------------------------------------------ klawiatura
    function onKeyDown(event) {
        if (!active) return;
        const tag = event.target?.tagName;
        const typing = tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA";
        const ctrl = event.ctrlKey || event.metaKey;

        if (ctrl && event.code === "KeyZ") { event.preventDefault(); if (!typing) (event.shiftKey ? redo : undo)(); return; }
        if (ctrl && event.code === "KeyY") { event.preventDefault(); if (!typing) redo(); return; }
        if (ctrl && event.code === "KeyS") { event.preventDefault(); saveDraftNow(); return; }
        if (typing) {
            if (event.code === "Escape" || event.code === "Enter") event.target.blur?.();
            return;
        }

        if (event.code === "Escape") {
            if (areaFor !== null) { areaFor = null; say("Pole patrolu pominięte (domyślnie cała platforma)."); }
            else { setTool("select"); select(null); }
        } else if (event.code === "Enter" && areaFor !== null) {
            areaFor = null;
            say("Pole patrolu pominięte (domyślnie cała platforma).");
        } else if (event.code === "Delete" || event.code === "Backspace") {
            removeSelection();
        } else if (event.code === "KeyT") {
            testLevel();
        } else if (event.code.startsWith("Arrow")) {
            event.preventDefault();
            const dx = (event.code === "ArrowRight") - (event.code === "ArrowLeft");
            const dy = (event.code === "ArrowDown") - (event.code === "ArrowUp");
            const target = getObj(sel);
            if (target) {
                target.x += dx * snapSize;
                target.y += dy * snapSize;
                syncProps();
                commit();
            } else {
                cam.x += dx * 64 / zoom;
                cam.y += dy * 64 / zoom;
                clampCamera();
            }
        }
    }

    // ------------------------------------------------------------------ panel (DOM)
    const root = el("div", { class: "editor", hidden: true });
    const panel = el("aside", { class: "editor__panel", "aria-label": "Edytor poziomów" });
    const statusEl = el("div", { class: "editor__status" });
    root.append(panel, statusEl);
    container.append(root);

    let zoomLabel = null;
    let levelBox = null;
    let toolBox = null;
    let optionsBox = null;
    let propsBox = null;
    const toolButtons = new Map();

    function say(text) {
        flash = { text, time: 4 };
    }

    function afterEdit() {
        commit();
    }

    function numberField(label, read, write, { min, step, allowEmpty = false, placeholder } = {}) {
        const input = el("input", { type: "number", step: step ?? 1, placeholder });
        if (min !== undefined) input.min = min;
        const sync = () => {
            const value = read();
            input.value = value === undefined || value === null ? "" : String(value);
        };
        sync();
        input.addEventListener("change", () => {
            if (input.value === "") {
                if (allowEmpty) { write(null); afterEdit(); } else sync();
                return;
            }
            const n = Number(input.value);
            if (!Number.isFinite(n) || (min !== undefined && n < min)) { sync(); return; }
            write(n);
            afterEdit();
            sync();
        });
        const field = el("label", { class: "editor__field" }, el("span", { text: label }), input);
        field.sync = sync;
        return field;
    }

    function textField(label, read, write, { list, placeholder } = {}) {
        const input = el("input", { type: "text", list, placeholder });
        input.value = read() ?? "";
        input.addEventListener("change", () => { write(input.value); afterEdit(); });
        return el("label", { class: "editor__field editor__field--wide" }, el("span", { text: label }), input);
    }

    function selectField(label, options, read, write) {
        const select = el("select", {}, options.map(([value, text]) => el("option", { value, text })));
        select.value = String(read());
        select.addEventListener("change", () => { write(select.value); afterEdit(); });
        return el("label", { class: "editor__field" }, el("span", { text: label }), select);
    }

    function checkField(label, read, write) {
        const input = el("input", { type: "checkbox" });
        input.checked = Boolean(read());
        input.addEventListener("change", () => { write(input.checked); afterEdit(); });
        return el("label", { class: "editor__check" }, input, el("span", { text: label }));
    }

    function button(text, onClick, extra = {}) {
        return el("button", { type: "button", class: `editor__button ${extra.class ?? ""}`.trim(), title: extra.title, onClick }, text);
    }

    // ----- sekcja "Poziom" -----
    function buildLevelBox() {
        levelBox.replaceChildren();
        const backgrounds = Object.keys(TEXTURES).filter((name) => name.startsWith("background"));
        const loadSelect = el("select", { class: "editor__select" },
            el("option", { value: "", text: "Wczytaj poziom…" }),
            el("optgroup", { label: "Wbudowane (kopia do edycji)" },
                builtinLevels.map((level, i) => el("option", { value: `b:${i}`, text: level.name }))),
            el("optgroup", { label: "Szkice z tej przeglądarki" },
                listDrafts().map((name) => el("option", { value: `d:${name}`, text: name }))),
            el("option", { value: "file", text: "Z pliku JSON…" }),
        );
        const fileInput = el("input", { type: "file", accept: ".json,application/json", hidden: true });
        fileInput.addEventListener("change", async () => {
            const file = fileInput.files[0];
            fileInput.value = "";
            if (!file) return;
            try {
                const raw = JSON.parse(await file.text());
                normalizeLevel(raw); // sprawdza poprawność
                loadModel(serializeLevel(raw), `Wczytano ${file.name}`);
            } catch (error) {
                say(`Nie można wczytać pliku: ${error.message}`);
            }
        });
        loadSelect.addEventListener("change", () => {
            const value = loadSelect.value;
            loadSelect.value = "";
            if (!value) return;
            if (dirty && !window.confirm("Masz niezapisane zmiany. Wczytać inny poziom?")) return;
            if (value === "file") fileInput.click();
            else if (value.startsWith("b:")) {
                const copy = serializeLevel(builtinLevels[Number(value.slice(2))]);
                copy.name = `${copy.name} (kopia)`;
                loadModel(copy, "Wczytano kopię poziomu wbudowanego");
            } else {
                const draft = loadDraft(value.slice(2));
                if (draft) loadModel(draft, `Wczytano szkic ${value.slice(2)}`);
            }
        });

        levelBox.append(
            el("div", { class: "editor__row" },
                loadSelect, fileInput),
            textField("Nazwa", () => model.name, (v) => { model.name = v.trim() || "Bez nazwy"; }),
            textField("Podtytuł", () => model.subtitle, (v) => { model.subtitle = v; }),
            selectField("Tryb", [["bombs", "Bomby + drzwi"], ["panel", "Panel (skradanka)"], ["boss", "Boss (Kamil)"]], () => model.mode ?? "bombs", (v) => {
                if (v === "boss") {
                    model.mode = "boss";
                    delete model.paratroopers;
                    say("Tryb Boss: postaw bossa (narzędzie „Boss (Kamil)”) i zwykle 3 panele (narzędzie „Bomba / panel”).");
                } else if (v === "panel") {
                    model.mode = "panel";
                    model.questionCategory = PANEL_QUESTION_CATEGORY;
                    if (model.bombs.length > 1) {
                        model.bombs = model.bombs.slice(0, 1);
                        say("Tryb Panel: zostawiono tylko pierwszą bombę (jako panel).");
                    }
                } else {
                    delete model.mode;
                    delete model.paratroopers;
                }
                sel = null;
                buildLevelBox();
                refreshAll();
            }),
            model.mode === "boss"
                ? el("p", { class: "editor__hint", text: "Boss: goni cię Kamil (musi cię dotknąć), a wygrywasz po rozbrojeniu wszystkich paneli (bomb). Bez drzwi." })
                : document.createComment("brak"),
            model.mode === "panel"
                ? el("p", { class: "editor__hint", text: "Panel: pytania zawsze trudne; zauważenie przez przeciwnika = alarm i spadochroniarze. Bez drzwi, wygrywasz po rozbrojeniu panelu." })
                : selectField("Pytania", QUESTION_CATEGORIES.map((c) => [c, c]), () => model.questionCategory, (v) => { model.questionCategory = v; }),
            model.mode === "panel"
                ? numberField("Spadochroniarze", () => model.paratroopers ?? 14, (v) => { model.paratroopers = Math.max(1, Math.min(60, Math.round(v))); }, { min: 1 })
                : document.createComment("brak"), // levelBox.append() nie pomija null, więc pusty węzeł
            selectField("Tło", backgrounds.map((b) => [b, b]), () => model.background?.[0] ?? "background", (v) => { model.background = [v]; }),
            el("div", { class: "editor__grid" },
                numberField("Czas (s)", () => model.timeLimit, (v) => { model.timeLimit = v; }, { min: 1 }),
                numberField("Życie", () => model.hp, (v) => { if (v === null) delete model.hp; else model.hp = v; }, { min: 1, allowEmpty: true, placeholder: "3" }),
                numberField("Szerokość", () => model.width, (v) => { model.width = v; }, { min: TILE, step: TILE }),
                numberField("Wysokość", () => model.height, (v) => { model.height = v; }, { min: TILE, step: TILE }),
            ),
            el("div", { class: "editor__row" },
                button("Zapisz szkic", saveDraftNow, { title: "Ctrl+S. Szkic zostaje w tej przeglądarce" }),
                button("Pobierz JSON", downloadJson, { title: "Plik wrzuć do src/data/levels/, a poziom sam pojawi się w menu" }),
            ),
        );
    }

    // ----- sekcja "Narzędzia" -----
    function buildToolBox() {
        toolBox.replaceChildren();
        let group = null;
        for (const t of TOOLS) {
            if (t.group !== group) {
                group = t.group;
                toolBox.append(el("h5", { class: "editor__group", text: group }));
            }
            const btn = button(t.label, () => setTool(t.id), { class: "editor__tool", title: t.hint });
            toolButtons.set(t.id, btn);
            toolBox.append(btn);
        }
        highlightTool();
    }

    function highlightTool() {
        for (const [id, btn] of toolButtons) btn.classList.toggle("is-active", id === tool);
    }

    function setTool(id) {
        tool = id;
        areaFor = null;
        highlightTool();
        buildOptions();
    }

    // ----- sekcja "Opcje narzędzia" (tekstura, asset, siła skoczni) -----
    function setAsset(path, blobUrl = null) {
        asset.path = path.trim();
        asset.w = 0;
        asset.h = 0;
        asset.img = null;
        asset.status = "";
        if (!asset.path) { buildOptions(); return; }

        const finish = (img) => {
            asset.img = img;
            asset.w = img.naturalWidth;
            asset.h = img.naturalHeight;
            buildOptions();
        };
        const img = new Image();
        img.onload = () => {
            asset.status = `${img.naturalWidth} × ${img.naturalHeight} px`;
            finish(img);
        };
        img.onerror = () => {
            if (!blobUrl) {
                asset.status = `Nie znaleziono pliku ${asset.path}. Wrzuć go do folderu assets/.`;
                buildOptions();
                return;
            }
            // Plik wybrany spoza assets/: edytor pokazuje go z pamięci, ale gra znajdzie go dopiero po skopiowaniu.
            overrideTextureSource(asset.path, blobUrl);
            const local = new Image();
            local.onload = () => {
                asset.status = `${local.naturalWidth} × ${local.naturalHeight} px. UWAGA: pliku nie ma w assets/, skopiuj go tam, inaczej gra go nie wczyta.`;
                finish(local);
            };
            local.src = blobUrl;
        };
        img.src = asset.path;
    }

    function buildOptions() {
        optionsBox.replaceChildren();
        const t = TOOLS.find((item) => item.id === tool);
        optionsBox.append(el("p", { class: "editor__hint", text: t?.hint ?? "" }));

        if (tool === "block") {
            optionsBox.append(
                selectField("Tekstura", [["platform", "platform"], ["ground", "ground"], ["wall", "wall"]],
                    () => toolOpts.texture, (v) => { toolOpts.texture = v; }),
            );

            const fileInput = el("input", { type: "file", accept: "image/*", hidden: true });
            fileInput.addEventListener("change", () => {
                const file = fileInput.files[0];
                fileInput.value = "";
                if (file) setAsset(`assets/${file.name}`, URL.createObjectURL(file));
            });
            const modeSelect = selectField("Rysowanie", [
                ["original", "rozmiar obrazka (klik)"],
                ["stretch", "rozciągnij do obszaru"],
                ["tile", "kafelkuj w obszarze"],
            ], () => asset.mode, (v) => { asset.mode = v; buildOptions(); });

            optionsBox.append(
                el("h5", { class: "editor__group", text: "Asset (obrazek jako ściana)" }),
                el("div", { class: "editor__row" },
                    button("Wybierz plik…", () => fileInput.click(), { title: "Wybierz obrazek z folderu assets/ projektu" }),
                    button("Bez assetu", () => setAsset(""), { title: "Wróć do zwykłych tekstur" }),
                    fileInput),
                textField("Ścieżka", () => asset.path, (v) => setAsset(v), { placeholder: "assets/budynek.png" }),
                modeSelect,
                checkField("Solidny (kolizja)", () => asset.solid, (v) => { asset.solid = v; }),
            );
            if (asset.path) {
                optionsBox.append(el("p", { class: "editor__hint", text: asset.status || "Wczytywanie…" }));
                if (asset.img) optionsBox.append(el("img", { class: "editor__preview", src: asset.img.src, alt: "Podgląd assetu" }));
            }
        } else if (tool === "jumppad") {
            optionsBox.append(numberField("Siła (1 = domyślna)", () => toolOpts.power, (v) => { toolOpts.power = v; }, { min: 0.1, step: 0.1 }));
        }
    }

    // ----- sekcja "Zaznaczony obiekt" -----
    const KIND_NAMES = {
        platforms: "Platforma / ściana", spikes: "Kolce", jumpPads: "Skocznia",
        bombs: "Bomba", enemies: "Przeciwnik", spawn: "Punkt startu",
    };

    let propFields = [];

    function syncProps() {
        for (const field of propFields) field.sync?.();
    }

    function buildProps() {
        propsBox.replaceChildren();
        propFields = [];
        const obj = getObj(sel);
        if (!obj) {
            propsBox.append(el("p", { class: "editor__hint", text: "Nic nie zaznaczono." }));
            return;
        }
        const add = (node) => { propFields.push(node); propsBox.append(node); return node; };
        const num = (label, key, opts) => add(numberField(label, () => obj[key], (v) => { obj[key] = v; }, opts));

        propsBox.append(el("h5", { class: "editor__group", text: KIND_NAMES[sel.kind] }));
        const xy = el("div", { class: "editor__grid" });
        propsBox.append(xy);
        const addXY = (node) => { propFields.push(node); xy.append(node); };

        addXY(numberField("x", () => obj.x, (v) => { obj.x = v; }));
        addXY(numberField("y", () => obj.y, (v) => { obj.y = v; }));

        if (sel.kind === "platforms") {
            addXY(numberField("w", () => obj.w, (v) => { obj.w = v; }, { min: 1 }));
            addXY(numberField("h", () => obj.h, (v) => { obj.h = v; }, { min: 1 }));
            add(textField("Tekstura", () => obj.texture, (v) => {
                obj.texture = v.trim() || "platform";
                buildProps();
            }, { list: "editor-textures", placeholder: "nazwa albo assets/plik.png" }));
            if (isPath(obj.texture)) {
                add(selectField("Rysowanie", [["stretch", "rozciągnij"], ["tile", "kafelkuj"], ["cover", "wypełnij"]],
                    () => obj.textureMode ?? "stretch", (v) => { obj.textureMode = v; }));
            }
            add(checkField("Solidna", () => obj.solid !== false, (v) => { if (v) delete obj.solid; else obj.solid = false; }));
            add(checkField("Jednostronna", () => obj.oneWay, (v) => { if (v) obj.oneWay = true; else delete obj.oneWay; }));
            add(checkField("Punkt zaczepienia haka", () => obj.grappleable, (v) => { if (v) obj.grappleable = true; else delete obj.grappleable; }));
        } else if (sel.kind === "spikes") {
            addXY(numberField("w", () => obj.w, (v) => { obj.w = Math.max(TILE, Math.round(v / TILE) * TILE); }, { min: TILE, step: TILE }));
        } else if (sel.kind === "jumpPads") {
            num("Siła", "power", { min: 0.1, step: 0.1 });
        } else if (sel.kind === "enemies") {
            add(selectField("Typ", Object.entries(ENEMY_TYPES).map(([id, def]) => [id, def.label]), () => obj.type, (v) => { obj.type = v; if (v === "boss") delete obj.area; buildProps(); }));
            add(selectField("Kierunek", [["1", "w prawo"], ["-1", "w lewo"]], () => String(obj.direction ?? 1), (v) => {
                if (v === "-1") obj.direction = -1; else delete obj.direction;
            }));
            add(numberField("Prędkość", () => obj.speed, (v) => { if (v === null) delete obj.speed; else obj.speed = v; }, { min: 1, allowEmpty: true, placeholder: `${ENEMY_TYPES[obj.type].speed}` }));

            if (obj.type === "boss") {
                add(numberField("Start po (s)", () => obj.wait ?? 0, (v) => { if (v > 0) obj.wait = v; else delete obj.wait; }, { min: 0, step: 0.5 }));
                add(textField("Respawny", () => (obj.respawns ?? []).map((r) => [r.x, r.y, r.stage ?? (r.side ? "-" : null), r.side ? r.side[0].toUpperCase() : null]
                    .filter((part) => part !== null).join(",")).join("; "), (v) => {
                    const points = [];
                    for (const part of v.split(";")) {
                        const [x, y, stage, side] = part.split(",").map((token) => token.trim());
                        if (![x, y].every((n) => n !== undefined && n !== "" && Number.isFinite(Number(n)))) continue;
                        const point = { x: Number(x), y: Number(y) };
                        if (stage !== undefined && stage !== "-" && Number.isFinite(Number(stage))) point.stage = Number(stage);
                        if (side && /^l/i.test(side)) point.side = "left";
                        if (side && /^[pr]/i.test(side)) point.side = "right";
                        points.push(point);
                    }
                    if (points.length > 0) obj.respawns = points; else delete obj.respawns;
                }, { placeholder: "x,y[,panele[,L|P]]; ... (L/P = punkt po lewej/prawej od gracza)" }));
                add(numberField("Min. odległość respawnu", () => obj.respawnDistance, (v) => { if (v === null) delete obj.respawnDistance; else obj.respawnDistance = v; }, { min: 0, allowEmpty: true, placeholder: "600" }));
                propsBox.append(el("p", { class: "editor__hint", text: "Boss goni gracza po całej mapie, więc nie ma pola patrolu. Gdy utknie (np. przed ciasnym przejściem), wraca na jeden z punktów „Respawny” (trzeci numer = ile paneli ma być już rozbrojonych)." }));
            } else {
                propsBox.append(el("h5", { class: "editor__group", text: "Pole patrolu" }));
                if (obj.area) {
                    const grid = el("div", { class: "editor__grid" });
                    propsBox.append(grid);
                    for (const [label, key] of [["x1", "x1"], ["y1", "y1"], ["x2", "x2"], ["y2", "y2"]]) {
                        const field = numberField(label, () => obj.area?.[key], (v) => { obj.area[key] = v; });
                        propFields.push(field);
                        grid.append(field);
                    }
                } else {
                    propsBox.append(el("p", { class: "editor__hint", text: "Domyślnie: cała platforma, na której stoi." }));
                }
                propsBox.append(el("div", { class: "editor__row" },
                    button(obj.area ? "Zaznacz od nowa" : "Zaznacz pole patrolu", () => { areaFor = sel.index; say("Przeciągnij prostokąt pola patrolu (Enter = pomiń)."); }),
                    obj.area ? button("Domyślne", () => { delete obj.area; buildProps(); commit(); }) : null,
                ));
            }
        }

        if (sel.kind !== "spawn") {
            propsBox.append(el("div", { class: "editor__row" }, button("Usuń (Del)", () => removeSelection(), { class: "editor__button--danger" })));
        }
    }

    // ----- góra panelu i szkielet -----
    function buildPanel() {
        levelBox = el("div", { class: "editor__section" });
        toolBox = el("div", { class: "editor__section editor__tools" });
        optionsBox = el("div", { class: "editor__section" });
        propsBox = el("div", { class: "editor__section" });

        const snapSelect = el("select", { class: "editor__select", title: "Siatka przyciągania w pikselach" },
            SNAPS.map((value) => el("option", { value, text: `${value} px` })));
        snapSelect.value = String(snapSize);
        snapSelect.addEventListener("change", () => { snapSize = Number(snapSelect.value); });

        zoomLabel = el("span", { class: "editor__zoom", text: `${zoom}x` });

        panel.append(
            el("div", { class: "editor__head" },
                el("h3", { class: "editor__title", text: "Edytor poziomów" }),
                el("div", { class: "editor__row" },
                    button("Testuj (T)", testLevel, { class: "editor__button--primary" }),
                    button("Menu", exitEditor),
                ),
            ),
            el("details", { open: true },
                el("summary", { text: "Poziom" }), levelBox),
            el("h4", { class: "editor__heading", text: "Narzędzia" }),
            toolBox,
            el("div", { class: "editor__row editor__view" },
                el("label", { class: "editor__inline" }, el("span", { text: "Siatka" }), snapSelect),
                el("span", { class: "editor__inline" },
                    button("−", () => setZoom(zoom - 1), { title: "Oddal" }), zoomLabel, button("+", () => setZoom(zoom + 1), { title: "Przybliż" })),
            ),
            el("div", { class: "editor__row" },
                checkField("Przyciągaj do podłoża", () => magnet, (v) => { magnet = v; }),
                checkField("Siatka tili", () => showGrid, (v) => { showGrid = v; }),
            ),
            el("div", { class: "editor__row" }, button("Cofnij", undo), button("Ponów", redo)),
            el("h4", { class: "editor__heading", text: "Opcje narzędzia" }),
            optionsBox,
            el("h4", { class: "editor__heading", text: "Zaznaczony obiekt" }),
            propsBox,
            el("datalist", { id: "editor-textures" }, ["platform", "ground", "wall"].map((name) => el("option", { value: name }))),
        );
        // Pola checkField zmieniające tylko ustawienia widoku nie powinny dodawać wpisów do historii.
        buildLevelBox();
        buildToolBox();
        buildOptions();
        buildProps();
    }

    function syncLevelFields() {
        buildLevelBox();
    }

    function refreshAll() {
        syncLevelFields();
        buildProps();
        buildOptions();
        clampCamera();
    }

    // ------------------------------------------------------------------ pliki i test
    function slug(name) {
        return name.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ł/g, "l")
            .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "poziom";
    }

    function downloadJson() {
        const text = JSON.stringify(serializeLevel(model), null, 2);
        const url = URL.createObjectURL(new Blob([text], { type: "application/json" }));
        const link = el("a", { href: url, download: `${slug(model.name)}.json` });
        document.body.append(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        dirty = false;
        say(`Pobrano ${slug(model.name)}.json. Wrzuć go do src/data/levels/ i odśwież stronę, a poziom pojawi się w menu.`);
    }

    function saveDraftNow() {
        if (saveDraft(model)) {
            saveAutosave(model);
            dirty = false;
            say(`Zapisano szkic "${model.name}" w tej przeglądarce.`);
            buildLevelBox();
        } else {
            say("Nie udało się zapisać szkicu (localStorage jest zablokowany).");
        }
    }

    function loadModel(data, message) {
        model = JSON.parse(JSON.stringify(serializeLevel(data)));
        sel = null;
        areaFor = null;
        dirty = false;
        resetHistory();
        refreshAll();
        fitView();
        if (message) say(message);
    }

    function testLevel() {
        if (model.bombs.length === 0) say(model.mode === "bombs" || !model.mode ? "Uwaga: poziom nie ma bomb, więc nie da się go wygrać." : "Uwaga: poziom nie ma panelu, więc nie da się go wygrać.");
        saveAutosave(model);
        onTest?.(serializeLevel(model));
    }

    function exitEditor() {
        saveAutosave(model);
        onExit?.();
    }

    // ------------------------------------------------------------------ rysowanie
    function drawSpikes(ctx, spike) {
        if (drawTexture(ctx, "spike", spike.x, spike.y, spike.w, spike.h)) return;
        ctx.fillStyle = "#aab4bd";
        for (let tx = 0; tx + SPIKE_HEIGHT <= spike.w; tx += SPIKE_HEIGHT) {
            ctx.beginPath();
            ctx.moveTo(spike.x + tx, spike.y + spike.h);
            ctx.lineTo(spike.x + tx + SPIKE_HEIGHT / 2, spike.y);
            ctx.lineTo(spike.x + tx + SPIKE_HEIGHT, spike.y + spike.h);
            ctx.closePath();
            ctx.fill();
        }
    }

    function drawJumpPad(ctx, pad) {
        if (drawTexture(ctx, "jumpPad", pad.x, pad.y, pad.w, pad.h)) return;
        ctx.fillStyle = "#3a2f1c";
        ctx.fillRect(pad.x, pad.y + pad.h - 2, pad.w, 2);
        ctx.fillStyle = "#e0a030";
        ctx.fillRect(pad.x, pad.y, pad.w, 3);
        ctx.fillStyle = "#c8c2b6";
        for (let tx = 4; tx + 2 <= pad.w - 2; tx += 6) ctx.fillRect(pad.x + tx, pad.y + 3, 2, pad.h - 5);
    }

    function drawBomb(ctx, x, y, alpha = 1) {
        ctx.save();
        ctx.globalAlpha = alpha;
        if (model.mode === "panel" || model.mode === "boss") {
            // W trybach "panel" i "boss" bomby są panelami rozbrajania.
            const size = getTextureSize("panel") ?? { w: BOMB_SIZE, h: BOMB_SIZE };   // tekstura w naturalnym rozmiarze, stoi na podłożu
            if (!drawTexture(ctx, "panel", x - size.w / 2, y - size.h, size.w, size.h)) {
                ctx.fillStyle = "#1d2a33";
                ctx.fillRect(x - BOMB_SIZE / 2, y - BOMB_SIZE, BOMB_SIZE, BOMB_SIZE);
                ctx.fillStyle = "#2f6f8f";
                ctx.fillRect(x - BOMB_SIZE / 2 + 3, y - BOMB_SIZE + 3, BOMB_SIZE - 6, BOMB_SIZE * 0.4);
                ctx.fillStyle = "#43586a";
                for (let i = 0; i < 3; i++) ctx.fillRect(x - BOMB_SIZE / 2 + 3 + i * 8, y - BOMB_SIZE * 0.4, 6, 4);
            }
        } else if (!drawTexture(ctx, "bomb", x - (getTextureSize("bomb")?.w ?? BOMB_SIZE) / 2, y - (getTextureSize("bomb")?.h ?? BOMB_SIZE),
            getTextureSize("bomb")?.w ?? BOMB_SIZE, getTextureSize("bomb")?.h ?? BOMB_SIZE)) {   // tekstura w naturalnym rozmiarze, stoi na podłożu
            ctx.fillStyle = "#1b1f24";
            ctx.beginPath();
            ctx.arc(x, y - BOMB_SIZE / 2 - 2, BOMB_SIZE / 2 - 3, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = "#e0a030";
            ctx.fillRect(x - 1, y - BOMB_SIZE + 1, 3, 5);
        }
        ctx.restore();
    }

    function drawEnemyBody(ctx, type, x, y, direction = 1, alpha = 1) {
        const def = ENEMY_TYPES[normalizeEnemyType(type)];
        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.fillStyle = def.colors.body;
        ctx.fillRect(x - def.width / 2, y - def.height, def.width, def.height);
        ctx.fillStyle = def.colors.head;
        ctx.fillRect(x - def.width / 2, y - def.height, def.width, def.height * 0.3);
        ctx.fillStyle = def.colors.visor;
        const visorW = def.width * 0.35;
        ctx.fillRect(direction > 0 ? x + def.width / 2 - visorW : x - def.width / 2, y - def.height + def.height * 0.1, visorW, 3);
        ctx.restore();
    }

    function drawSpawn(ctx, x, y, alpha = 1) {
        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.fillStyle = "rgba(121, 215, 196, 0.35)";
        ctx.fillRect(x - SPAWN_SIZE.w / 2, y - SPAWN_SIZE.h, SPAWN_SIZE.w, SPAWN_SIZE.h);
        ctx.strokeStyle = "#79d7c4";
        ctx.lineWidth = 1 / zoom;
        ctx.strokeRect(x - SPAWN_SIZE.w / 2, y - SPAWN_SIZE.h, SPAWN_SIZE.w, SPAWN_SIZE.h);
        ctx.fillStyle = "#79d7c4";
        ctx.font = `700 ${11 / zoom}px system-ui, sans-serif`;
        ctx.textAlign = "center";
        ctx.fillText("START", x, y - SPAWN_SIZE.h - 3 / zoom);
        ctx.restore();
    }

    function strokeRectOutline(ctx, r, color, width = 1.5, dash = null) {
        ctx.save();
        ctx.strokeStyle = color;
        ctx.lineWidth = width / zoom;
        if (dash) ctx.setLineDash(dash.map((d) => d / zoom));
        ctx.strokeRect(r.x, r.y, r.w, r.h);
        ctx.restore();
    }

    function label(ctx, text, x, y, color = "#fff") {
        ctx.save();
        ctx.font = `${11 / zoom}px ui-monospace, Menlo, Consolas, monospace`;
        ctx.textAlign = "left";
        ctx.textBaseline = "bottom";
        ctx.fillStyle = "rgba(10, 15, 22, 0.8)";
        const width = ctx.measureText(text).width;
        ctx.fillRect(x, y - 13 / zoom, width + 6 / zoom, 14 / zoom);
        ctx.fillStyle = color;
        ctx.fillText(text, x + 3 / zoom, y);
        ctx.restore();
    }

    function drawGhost(ctx) {
        if (!mouse.inside || drag || areaFor !== null) return;
        const p = { x: mouse.wx, y: mouse.wy };
        if (tool === "block" && asset.path && asset.mode === "original" && asset.img) {
            const pos = pointPos(p.x, p.y);
            ctx.save();
            ctx.globalAlpha = 0.6;
            ctx.drawImage(asset.img, Math.round(pos.x - asset.w / 2), pos.y - asset.h, asset.w, asset.h);
            ctx.restore();
        } else if (tool === "block" || tool === "oneway" || tool === "select" || tool === "erase") {
            const x = snapTo(p.x), y = snapTo(p.y);
            ctx.fillStyle = "rgba(255,255,255,0.5)";
            ctx.fillRect(x - 2 / zoom, y - 2 / zoom, 4 / zoom, 4 / zoom);
        } else if (tool === "spawn") {
            const pos = pointPos(p.x, p.y);
            drawSpawn(ctx, pos.x, pos.y, 0.6);
        } else if (tool === "bomb") {
            const pos = pointPos(p.x, p.y);
            drawBomb(ctx, pos.x, pos.y, 0.6);
        } else if (tool === "enemy-weak" || tool === "enemy-strong" || tool === "enemy-boss") {
            const pos = pointPos(p.x, p.y);
            drawEnemyBody(ctx, tool === "enemy-weak" ? "weak" : tool === "enemy-strong" ? "strong" : "boss", pos.x, pos.y, 1, 0.6);
        } else if (tool === "jumppad") {
            const pos = pointPos(p.x, p.y);
            ctx.save();
            ctx.globalAlpha = 0.6;
            drawJumpPad(ctx, { x: pos.x - TILE / 2, y: pos.y - SPIKE_HEIGHT, w: TILE, h: SPIKE_HEIGHT });
            ctx.restore();
        } else if (tool === "grapple") {
            ctx.fillStyle = "rgba(209, 169, 79, 0.6)";
            ctx.fillRect(snapTo(p.x) - 12, snapTo(p.y) - 12, 24, 24);
        } else if (tool === "spike") {
            const pos = pointPos(p.x, p.y);
            ctx.save();
            ctx.globalAlpha = 0.6;
            drawSpikes(ctx, { x: snapTo(p.x), y: pos.y - SPIKE_HEIGHT, w: TILE, h: SPIKE_HEIGHT });
            ctx.restore();
        }
    }

    function draw(ctx) {
        if (!active) return;
        const dpr = window.devicePixelRatio || 1;
        const width = canvas.width;
        const height = canvas.height;
        ctx.fillStyle = "#0e151d";
        ctx.fillRect(0, 0, width, height);

        const panelPx = Math.round(panelWidth() * dpr);
        const z = zoom * dpr;
        ctx.save();
        ctx.beginPath();
        ctx.rect(panelPx, 0, width - panelPx, height);
        ctx.clip();
        ctx.translate(Math.round(panelPx - cam.x * z), Math.round(-cam.y * z));
        ctx.scale(z, z);
        ctx.imageSmoothingEnabled = false;

        // Obszar poziomu i siatka tili.
        ctx.fillStyle = "#17212c";
        ctx.fillRect(0, 0, model.width, model.height);
        if (showGrid) {
            ctx.fillStyle = "rgba(255, 255, 255, 0.07)";
            const line = 1 / zoom;
            for (let x = 0; x <= model.width; x += TILE) ctx.fillRect(x, 0, line, model.height);
            for (let y = 0; y <= model.height; y += TILE) ctx.fillRect(0, y, model.width, line);
        }

        // Obiekty.
        for (const p of model.platforms) {
            ctx.save();
            if (p.solid === false) ctx.globalAlpha = 0.7;
            drawBox(ctx, { x: p.x, y: p.y, w: p.w, h: p.h, texture: textureKey(p.texture, p.textureMode), color: p.color ?? "#24343d" });
            ctx.restore();
            if (p.oneWay) {
                ctx.fillStyle = "#5c8790";
                ctx.fillRect(p.x, p.y, p.w, Math.min(3, p.h));
            }
            if (p.grappleable) strokeRectOutline(ctx, { x: p.x, y: p.y, w: p.w, h: p.h }, "#f2d37b", 1.5);
            else if (p.solid === false) strokeRectOutline(ctx, { x: p.x, y: p.y, w: p.w, h: p.h }, "rgba(255,255,255,0.35)", 1, [3, 3]);
        }
        for (const s of model.spikes) drawSpikes(ctx, s);
        for (const j of model.jumpPads) drawJumpPad(ctx, j);
        for (const b of model.bombs) drawBomb(ctx, b.x, b.y);
        model.enemies.forEach((e, i) => {
            if (e.area) {
                const a = { x: e.area.x1, y: e.area.y1, w: e.area.x2 - e.area.x1, h: e.area.y2 - e.area.y1 };
                const selected = sel?.kind === "enemies" && sel.index === i;
                ctx.fillStyle = selected ? "rgba(90, 200, 255, 0.12)" : "rgba(90, 200, 255, 0.05)";
                ctx.fillRect(a.x, a.y, a.w, a.h);
                strokeRectOutline(ctx, a, selected ? "rgba(90, 200, 255, 0.95)" : "rgba(90, 200, 255, 0.4)", 1, [4, 3]);
            }
            drawEnemyBody(ctx, e.type, e.x, e.y, e.direction ?? 1);
        });
        drawSpawn(ctx, model.spawn.x, model.spawn.y);

        // Granice poziomu.
        strokeRectOutline(ctx, { x: 0, y: 0, w: model.width, h: model.height }, "rgba(255, 0, 255, 0.6)", 1);

        // Zaznaczenie i uchwyty.
        const selected = getObj(sel);
        if (selected) {
            const r = rectOf(sel.kind, selected);
            strokeRectOutline(ctx, r, "#ffffff", 2);
            if (sel.kind === "platforms") {
                ctx.fillStyle = "#ffffff";
                const size = HANDLE / zoom;
                for (const [hx, hy] of Object.values(handles(r))) ctx.fillRect(hx - size / 2, hy - size / 2, size, size);
            }
        }

        // Przeciągany prostokąt.
        if (drag && (drag.type === "create" || drag.type === "area")) {
            const r = normalizeRect(drag.x0, drag.y0, drag.x1, drag.y1);
            const isArea = drag.type === "area";
            ctx.fillStyle = isArea ? "rgba(90, 200, 255, 0.2)" : "rgba(255, 255, 255, 0.18)";
            ctx.fillRect(r.x, r.y, r.w, r.h);
            strokeRectOutline(ctx, r, isArea ? "#5ac8ff" : "#ffffff", 1.5, [4, 3]);
            label(ctx, `${r.w} × ${r.h}`, r.x, r.y - 2 / zoom);
        } else if (drag && drag.type === "spike") {
            const count = Math.max(1, Math.round(Math.abs(drag.x1 - drag.x0) / TILE));
            const x = drag.x1 < drag.x0 ? drag.x0 - count * TILE : drag.x0;
            ctx.save();
            ctx.globalAlpha = 0.7;
            drawSpikes(ctx, { x, y: drag.y - SPIKE_HEIGHT, w: count * TILE, h: SPIKE_HEIGHT });
            ctx.restore();
            label(ctx, `${count} × kolce`, x, drag.y - SPIKE_HEIGHT - 2 / zoom);
        }

        drawGhost(ctx);
        ctx.restore();
    }

    // ------------------------------------------------------------------ pętla
    function update(dt) {
        if (!active) return;
        flash.time = Math.max(0, flash.time - dt);

        // Kamera przesuwa się, gdy kursor jest blisko krawędzi obszaru mapy (poza panelem).
        if (mouse.inside) {
            const left = panelWidth();
            const right = canvas.clientWidth;
            const step = EDGE_SPEED * dt / zoom;
            if (mouse.x >= left && mouse.x < left + EDGE) cam.x -= step;
            if (mouse.x > right - EDGE) cam.x += step;
            if (mouse.y < EDGE) cam.y -= step;
            if (mouse.y > canvas.clientHeight - EDGE) cam.y += step;
            clampCamera();
            const w = toWorld(mouse.x, mouse.y);
            mouse.wx = w.x;
            mouse.wy = w.y;
            // Podczas przeciągania kamera i rysowany obiekt idą razem.
            if (drag && (drag.type === "create" || drag.type === "area")) { drag.x1 = snapTo(mouse.wx); drag.y1 = snapTo(mouse.wy); }
            if (drag && drag.type === "spike") drag.x1 = snapTo(mouse.wx);
        }

        const hint = areaFor !== null
            ? "POLE PATROLU: przeciągnij prostokąt, po którym ma chodzić przeciwnik (Enter = pomiń, domyślnie cała platforma)"
            : (TOOLS.find((t) => t.id === tool)?.hint ?? "");
        const where = mouse.inside ? `x ${Math.round(mouse.wx)}  y ${Math.round(mouse.wy)}   ` : "";
        statusEl.textContent = flash.time > 0 ? flash.text : `${where}${hint}`;
        statusEl.classList.toggle("is-flash", flash.time > 0);
        statusEl.classList.toggle("is-area", areaFor !== null && flash.time <= 0);
    }

    // ------------------------------------------------------------------ podłączenie
    canvas.addEventListener("pointerdown", onPointerDown);
    canvas.addEventListener("pointermove", onPointerMove);
    canvas.addEventListener("pointerup", onPointerUp);
    canvas.addEventListener("pointercancel", onPointerUp);
    canvas.addEventListener("pointerleave", () => { mouse.inside = false; });
    canvas.addEventListener("pointerenter", (event) => { updateMouse(event); mouse.inside = true; });
    canvas.addEventListener("wheel", onWheel, { passive: false });
    canvas.addEventListener("contextmenu", (event) => { if (active) event.preventDefault(); });
    window.addEventListener("keydown", onKeyDown);

    buildPanel();

    return {
        // Otwiera edytor. Bez argumentu wraca do ostatniej edycji albo ładuje kopię istniejącego poziomu.
        open(level = null) {
            active = true;
            root.hidden = false;
            canvas.style.cursor = "crosshair";
            mouse.inside = false; // kamera przy krawędzi zaczyna działać po pierwszym ruchu myszy nad mapą
            loadModel(level ?? loadAutosave() ?? (builtinLevels[0] ? serializeLevel(builtinLevels[0]) : model));
            fitView();
        },
        // Wraca do edytora po teście (bez zmiany modelu).
        resume() {
            active = true;
            root.hidden = false;
            canvas.style.cursor = "crosshair";
            clampCamera();
        },
        close() {
            active = false;
            root.hidden = true;
            canvas.style.cursor = "";
            drag = null;
        },
        get active() { return active; },
        get model() { return model; },
        // Widok (tylko do odczytu; używają go testy): kamera, przybliżenie, szerokość panelu.
        get view() { return { camX: cam.x, camY: cam.y, zoom, panelWidth: panelWidth(), tool, areaFor, snapSize }; },
        update,
        draw,
    };
}
