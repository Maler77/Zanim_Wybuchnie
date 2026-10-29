import { createViewport } from "./viewport.js";
import { sound } from "./audio.js";
import { createInput } from "./input.js";
import { createGame, formatTime } from "./game.js";
import { drawWireFunnel } from "./wirefunnel.js";
import { createMenu } from "./menu.js";
import { applyDomTextures } from "./textures.js";
import { LEVELS } from "./levels.js";
import { createQuestionQueue, loadQuestions, QUESTION_CATEGORIES } from "./questions.js";
import { createEditor } from "./editor.js";
import { loadJsonLevels, mergeJsonLevels, normalizeLevel, PANEL_QUESTION_CATEGORY } from "./levelstore.js";
import { loadStory, storyChapter } from "./story.js";
import { createStoryPlayer } from "./storyplayer.js";
import { isCompleted, isUnlocked, markCompleted, resetProgress } from "./progress.js";

// Fabuła po ukończeniu poziomów (tytuł, czat grupowy, policja, zakończenie; treść w src/data/story.json).
// Ustaw false, żeby wyłączyć ją w całości (np. na czas testowania poziomów).
const STORY_ENABLED = true;
const story = await loadStory();

// Poziomy z plików JSON (wszystkie *.json z src/data/levels/) dochodzą po poziomach z levels.js;
// poziom JSON o tej samej nazwie co poziom z kodu zastępuje go.
mergeJsonLevels(LEVELS, await loadJsonLevels());
const baseLevelCount = LEVELS.length; // poziom testowany z edytora dostaje miejsce za nimi

let questionQueues;
let questionsByCategory;
try {
    questionsByCategory = await loadQuestions();
    questionQueues = Object.fromEntries(QUESTION_CATEGORIES.map((category) => [
        category,
        createQuestionQueue(questionsByCategory[category]),
    ]));
    for (const level of LEVELS) {
        if (!QUESTION_CATEGORIES.includes(level.questionCategory)) {
            throw new Error(`Level "${level.name}" has an invalid questionCategory. Use easy, medium, or hard.`);
        }
    }
} catch (error) {
    console.error("Question setup failed:", error);
    throw error;
}

const canvas = document.querySelector(".game__viewport");

if (!(canvas instanceof HTMLCanvasElement)) {
    throw new Error("Game viewport canvas is missing from index.html");
}

const viewport = createViewport(canvas);
const input = createInput();
const game = createGame(LEVELS[0]);
const soundToggles = [...document.querySelectorAll(".sound-toggle")];

function updateSoundToggle() {
    for (const button of soundToggles) {
        button.textContent = sound.enabled ? "Dźwięk: włączony" : "Dźwięk: wyłączony";
        button.setAttribute("aria-pressed", String(sound.enabled));
    }
}

updateSoundToggle();
for (const button of soundToggles) {
    button.addEventListener("click", () => {
        sound.setEnabled(!sound.enabled);
        updateSoundToggle();
        if (sound.enabled) sound.play("toggle");
    });
}

document.addEventListener("click", (event) => {
    if (event.target.closest("button:not(.sound-toggle):not([data-action='answer'])")) sound.play("click");
});

// ---------- Lista poziomów w menu głównym ----------
// Karty tworzą się z tablicy LEVELS (levels.js), więc nowy poziom pojawia się w menu sam.

const levelList = document.querySelector("#level-list");

// "1 bomba", "2 bomby", "5 bomb"
function bombCountLabel(count) {
    const lastTwo = count % 100;
    const last = count % 10;
    if (count === 1) return "1 bomba";
    if (last >= 2 && last <= 4 && !(lastTwo >= 12 && lastTwo <= 14)) return `${count} bomby`;
    return `${count} bomb`;
}

// Karty poziomów (do odświeżania blokad i przycisków fabuły): { card, replay, level, index }.
const levelCards = [];

function buildLevelList() {
    LEVELS.forEach((level, index) => {
        // Kontener: karta poziomu + mały przycisk "fabuła" w rogu (przycisk nie może być wewnątrz przycisku).
        const wrap = document.createElement("div");
        wrap.className = "level-card-wrap";

        const card = document.createElement("button");
        card.type = "button";
        card.className = "menu__button level-card";
        card.dataset.action = "play";
        card.dataset.level = String(index);

        // Miniatura: tekstura z textures.js (data-texture) albo gradient zastępczy.
        const thumb = document.createElement("span");
        thumb.className = "level-card__thumb";
        if (level.thumbnail) thumb.dataset.texture = level.thumbnail;
        const hue = 200 + index * 55;
        thumb.style.setProperty(
            "--fallback",
            `linear-gradient(135deg, hsl(${hue} 45% 32%), hsl(${hue + 40} 40% 14%))`,
        );

        const name = document.createElement("span");
        name.className = "level-card__name";
        name.textContent = level.name;

        const subtitle = document.createElement("span");
        subtitle.className = "level-card__subtitle";
        subtitle.textContent = level.subtitle ?? "";

        const info = document.createElement("span");
        info.className = "level-card__info";
        info.textContent = level.mode === "panel"
            ? `Panel · skradanka · ${formatTime(level.timeLimit)}`
            : level.mode === "boss"
                ? `BOSS · ${level.bombs.length} ${level.bombs.length === 1 ? "panel" : "panele"} · ${formatTime(level.timeLimit)}`
                : `${bombCountLabel(level.bombs.length)} · ${formatTime(level.timeLimit)}`;

        const status = document.createElement("span");
        status.className = "level-card__status";

        card.append(thumb, name, subtitle, info, status);

        const replay = document.createElement("button");
        replay.type = "button";
        replay.className = "level-card__replay";
        replay.dataset.action = "replay-story";
        replay.dataset.level = String(index);
        replay.textContent = "💬 Fabuła";
        replay.title = "Odtwórz fabułę tego poziomu";
        replay.hidden = true;

        wrap.append(card, replay);
        levelList.append(wrap);
        levelCards.push({ card, replay, status, level, index });
    });
}

// Ustawia blokady i przyciski fabuły według postępu gracza. W trybie debug wszystko jest odblokowane.
// Wołane przy każdym wejściu do menu oraz przy przełączeniu debugu.
function refreshLevelList() {
    for (const { card, replay, status, level, index } of levelCards) {
        const unlocked = debug || isUnlocked(LEVELS, index);
        const done = isCompleted(level.name);
        card.disabled = !unlocked;
        card.classList.toggle("is-locked", !unlocked);
        card.classList.toggle("is-complete", done);
        status.textContent = !unlocked ? "🔒 Ukończ poprzedni poziom" : done ? "✓ Ukończony" : "";
        replay.hidden = !(STORY_ENABLED && (done || debug) && storyChapter(story, index));
    }
    document.querySelector("#debug-hint").hidden = !debug;
    document.querySelector('[data-action="reset-progress"]').hidden = !LEVELS.every((level) => isCompleted(level.name));
}

buildLevelList();

// Tekstury elementów HTML (tło menu, miniatury poziomów, okno z pytaniem, ekrany końcowe).
applyDomTextures();

// Elementy okna z pytaniem oraz ekranów końcowych.
const bombTitle = document.querySelector("#bomb-title");
const bombTimer = document.querySelector("#bomb-timer");
const bombPenalty = document.querySelector("#bomb-penalty");
const bombOptions = [...document.querySelectorAll(".bomb-panel__option")];
const bombPanelEl = document.querySelector("#bomb-panel");
const bombBoard = document.querySelector(".bomb-board");
const bombMerge = document.querySelector("#bomb-merge");
const bombRows = bombOptions.map((button) => button.closest(".bomb-board__row")); // wiersz = kabel + odpowiedź
const loseReason = document.querySelector("#lose-reason");
const winSummary = document.querySelector("#win-summary");
const winTime = document.querySelector("#win-time");
const winNext = document.querySelector("#win-next");
const LETTERS = ["A", "B", "C"];

// Zła odpowiedź przy bombie zabiera tyle sekund z timera poziomu (a nie kończy gry). Zła odpowiedź
// zostaje wyłączona, więc pytanie można dokończyć, ale każde pudło kosztuje. Gdy czas spadnie do zera,
// poziom kończy się jak zwykle ("Czas minął").
const WRONG_ANSWER_PENALTY = 20;
const wrongAnswers = new Map(); // klucz bomby -> zbiór indeksów odpowiedzi, które już były złe

// Wybrana odpowiedź przecina swój kabel (klasa is-cut na wierszu, animacja w style.css). Po dobrej odpowiedzi okno
// zostaje jeszcze chwilę, żeby było widać przecięcie, i dopiero wtedy się zamyka (gra w tym czasie toczy się dalej).
const CUT_CLOSE_DELAY_MS = 1000;
let closeAfterCutTimer = null;

// ---------- Stan gry ----------
// "menu"    - menu główne, widoczne po otwarciu strony
// "playing" - gra
// "paused"  - pauza
// "bomb"    - okno z pytaniem przy bombie (czas leci dalej)
// "lost"    - ekran przegranej
// "won"     - ekran wygranej
// "story"   - ekran fabuły (prolog, przerywnik między poziomami, epilog)

let state = "menu";
let debug = false;      // tryb debug włączany klawiszem "/"
let activeBomb = null;  // bomba, której pytanie jest teraz otwarte
let activeQuestion = null;
const assignedQuestions = new Map();
let currentLevel = 0;   // indeks aktualnego poziomu w LEVELS
let ignoreEscapeUntil = 0;
let pausedFromState = "playing";

// Który ekran menu (data-screen w index.html) odpowiada któremu stanowi.
const SCREEN_FOR_STATE = {
    menu: "main",
    paused: "pause",
    bomb: "bomb",
    lost: "lose",
    won: "win",
    story: "story",
};

const menu = createMenu({
    play: (data) => playFromMenu(Number(data.level)),    // karta poziomu w menu głównym
    retry: () => startGame(currentLevel),                // "Spróbuj ponownie" po przegranej
    next: nextLevel,                                     // "Następny poziom" po wygranej (i fabule)
    restart: () => startGame(currentLevel),              // "Zacznij od początku" w menu pauzy
    "replay-story": (data) => replayStory(Number(data.level)), // "Fabuła" w rogu karty ukończonego poziomu
    "reset-progress": resetProgressFromMenu,             // "Resetuj postęp" w menu głównym
    resume: resumeGame,
    quit: quitToMenu,
    answer: (data) => answerBomb(Number(data.index)),
    continue: continueGame,                              // "Graj" w menu głównym
});

function setState(next) {
    state = next;
    document.body.dataset.state = next; // używa tego CSS (np. do panelu sterowania w rogu)

    if (next === "playing" || next === "bomb") sound.playLevelMusic(currentLevel);
    else sound.stopMusic();

    // Rozszerzamy viewport tylko podczas rozgrywki i ekranów w jej trakcie.
    const gameIsActive = ["playing", "paused", "bomb", "lost", "won", "story"].includes(next);
    document.body.classList.toggle("game-active", gameIsActive);
    // Kursor jest ukryty tylko, gdy naprawdę grasz.
    document.body.classList.toggle("cursor-hidden", next === "playing");

    if (next === "playing") menu.hide();
    else {
        if (next === "menu") refreshLevelList(); // blokady i przyciski fabuły według aktualnego postępu
        menu.show(SCREEN_FOR_STATE[next]);
        if (next === "story") storyPlayer.focus(); // fokus na ekranie fabuły, żeby Spacja nie klikała przycisku "Pomiń"
    }
}

// ---------- Edytor poziomów (editor.js) ----------
// Z edytora można przetestować poziom: gra uruchamia go jako ostatni na liście LEVELS, a przyciski
// "Menu główne" / "Powrót do menu" wracają wtedy do edytora zamiast do menu.
let testingFromEditor = false;

const editor = createEditor({
    canvas,
    container: canvas.closest(".game") ?? document.body,
    builtinLevels: LEVELS.slice(),
    onTest: startEditorTest,
    onExit: closeEditor,
});

function openEditor() {
    setState("editor");
    editor.open();
}

function closeEditor() {
    editor.close();
    setState("menu");
}

function setQuitLabels() {
    for (const button of document.querySelectorAll('[data-action="quit"]')) {
        button.dataset.label ??= button.textContent;
        button.textContent = testingFromEditor ? "Wróć do edytora" : button.dataset.label;
    }
}

function startEditorTest(rawLevel) {
    let level;
    try {
        level = normalizeLevel(rawLevel);
    } catch (error) {
        window.alert(`Poziom ma błąd: ${error.message}`);
        return;
    }
    LEVELS.length = baseLevelCount;
    LEVELS.push(level);
    testingFromEditor = true;
    setQuitLabels();
    editor.close();
    startGame(baseLevelCount);
}

function endEditorTest() {
    testingFromEditor = false;
    LEVELS.length = baseLevelCount;
    setQuitLabels();
    setState("editor");
    editor.resume();
}

// ---------- Fabuła ----------
// Po ukończeniu poziomu N (od 0) pokazuje się rozdział story.chapters[N] (czat grupowy itd., patrz story.js).
// Przed rozdziałem 0 pojawia się jeszcze tytuł. Zakończenie ostatniego rozdziału kończy się przyciskiem "Menu główne".
const storyPlayer = createStoryPlayer(document.querySelector("#story-root"), story);

// Odtwarza rozdział po poziomie `levelIndex` (albo od razu wywołuje `then`, gdy poziom nie ma fabuły).
function playChapter(levelIndex, then, { replay = false } = {}) {
    const chapter = STORY_ENABLED && !testingFromEditor ? storyChapter(story, levelIndex) : null;
    if (!chapter) {
        then();
        return;
    }
    setState("story");
    storyPlayer.play(chapter, {
        showTitle: story.showTitle && levelIndex === 0, // tytuł z story.json tylko, gdy "showTitle": true
        nextLabel: replay ? "Zamknij" : "Dalej",
        onDone: then,
    });
}

// Przycisk "Fabuła" na karcie ukończonego poziomu: odtwarza rozdział i wraca do menu.
function replayStory(levelIndex) {
    playChapter(levelIndex, () => { setState("menu"); menu.show("levels"); }, { replay: true });
}

// "Graj" w menu głównym: pierwszy odblokowany, nieukończony poziom (gdy wszystkie ukończone, pierwszy).
function continueGame() {
    const next = LEVELS.findIndex((level, index) => isUnlocked(LEVELS, index) && !isCompleted(level.name));
    startGame(next === -1 ? 0 : next);
}

// Karta poziomu w menu głównym (zablokowanego poziomu nie da się uruchomić, poza trybem debug).
function playFromMenu(levelIndex) {
    if (!debug && !isUnlocked(LEVELS, levelIndex)) return;
    startGame(levelIndex);
}

// "Resetuj postęp" w menu głównym: znów odblokowany tylko pierwszy poziom.
function resetProgressFromMenu() {
    if (!LEVELS.every((level) => isCompleted(level.name))) return;
    if (!window.confirm("Zresetować postęp? Poziomy zostaną znów zablokowane.")) return;
    resetProgress();
    refreshLevelList();
}

// Czy po wygranej jest rozdział fabuły do pokazania.
function hasStoryAfterLevel() {
    return STORY_ENABLED && !testingFromEditor && Boolean(storyChapter(story, currentLevel));
}

// "Następny poziom" na ekranie wygranej (rozdział fabuły był już pokazany zaraz po wygranej).
function nextLevel() {
    if (currentLevel + 1 < LEVELS.length) startGame(currentLevel + 1);
}

// Wczytaj wybrany poziom od początku (pełny reset: gracz, bomby, timer).
function startGame(levelIndex = currentLevel) {
    if (!LEVELS[levelIndex]) return;
    currentLevel = levelIndex;
    game.loadLevel(LEVELS[levelIndex]);
    // A fresh attempt starts a fresh question cycle, including after the player loses all HP.
    questionQueues = Object.fromEntries(QUESTION_CATEGORIES.map((category) => [
        category,
        createQuestionQueue(questionsByCategory[category]),
    ]));
    assignedQuestions.clear();
    activeBomb = null;
    activeQuestion = null;
    wrongAnswers.clear();
    pausedFromState = "playing";
    setState("playing");
    if (!testingFromEditor) enterFullscreen();
}

// Fullscreen is requested from the user's Play click. Keyboard Lock lets Escape
// open the pause menu without leaving fullscreen where the browser supports it.
function enterFullscreen() {
    const root = document.documentElement;
    const request = root.requestFullscreen ?? root.webkitRequestFullscreen;
    if (isFullscreen() || typeof request !== "function") return;

    try {
        Promise.resolve(request.call(root, { keyboardLock: "browser" })).catch(() => {
            // Keep the game playable in browsers without keyboard-lock support.
            if (!isFullscreen()) {
                Promise.resolve(request.call(root)).catch(() => {});
            }
        });
    } catch {
        try {
            Promise.resolve(request.call(root)).catch(() => {});
        } catch {
            // CSS still expands the game to the page viewport if fullscreen is denied.
        }
    }
}

function exitFullscreen() {
    const exit = document.exitFullscreen ?? document.webkitExitFullscreen;
    if (!isFullscreen() || typeof exit !== "function") return;
    try {
        Promise.resolve(exit.call(document)).catch(() => {});
    } catch {
        // The main menu remains available in the normal page layout.
    }
}

function isFullscreen() {
    return Boolean(document.fullscreenElement ?? document.webkitFullscreenElement);
}

function pauseGame() {
    if (state === "playing" || state === "bomb") {
        pausedFromState = state;
        setState("paused");
    }
}

function resumeGame() {
    if (state === "paused") {
        setState(pausedFromState);
        if (!testingFromEditor) enterFullscreen();
    }
}

// "Menu główne" z pauzy i z ekranów wygranej/przegranej.
function quitToMenu() {
    game.reset();
    activeBomb = null;
    activeQuestion = null;
    if (testingFromEditor) {
        endEditorTest();
        return;
    }
    exitFullscreen();
    setState("menu");
}

// Request the browser to keep Escape inside the game while fullscreen is active.
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && isFullscreen() && ["playing", "paused", "bomb", "story", "won", "lost"].includes(state)) {
        event.preventDefault();
    }
}, true);

function onFullscreenChange() {
    // If the browser exits fullscreen (for example with Escape where keyboard
    // locking is unavailable), preserve the page-filling pause screen.
    if (!isFullscreen() && (state === "playing" || state === "bomb")) {
        ignoreEscapeUntil = performance.now() + 300;
        pauseGame();
    }
}
document.addEventListener("fullscreenchange", onFullscreenChange);
document.addEventListener("webkitfullscreenchange", onFullscreenChange);

// ---------- Bomby, wygrana i przegrana ----------

// Kategoria pytań poziomu: poziomy z panelem (mode "panel") zawsze losują trudne.
function questionCategoryFor(level) {
    return level.mode === "panel" ? PANEL_QUESTION_CATEGORY : level.questionCategory; // boss: kategoria z pliku poziomu
}

// Otwiera okno z pytaniem dla bomby (E przy bombie).
function openBomb(bomb) {
    if (!bomb || bomb.defused) return;
    sound.play("bombOpen");
    const bombKey = `${currentLevel}:${bomb.id}`;
    let question = assignedQuestions.get(bombKey);
    if (!question) {
        question = shuffleAnswers(questionQueues[questionCategoryFor(LEVELS[currentLevel])].next());
        assignedQuestions.set(bombKey, question);
    }
    activeBomb = bomb;
    activeQuestion = question;
    bombTitle.textContent = question.question;
    const wrong = wrongAnswers.get(bombKey) ?? new Set();
    bombBoard.classList.remove("is-locked");
    bombOptions.forEach((button, index) => {
        button.hidden = false;
        button.disabled = wrong.has(index); // wcześniej wybrana zła odpowiedź zostaje wyłączona
        button.textContent = `${LETTERS[index]}. ${question.answers[index]}`;
        // Kabel wcześniej wybranej (złej) odpowiedzi jest już przecięty; bez ponownej animacji.
        bombRows[index].classList.remove("is-correct");
        bombRows[index].classList.toggle("is-cut", wrong.has(index));
        bombRows[index].classList.toggle("is-old", wrong.has(index));
    });
    bombPenalty.hidden = wrong.size === 0;
    if (wrong.size > 0) bombPenalty.textContent = `Zła odpowiedź! −${WRONG_ANSWER_PENALTY} s (razy ${wrong.size})`;
    // Przy panelu (poziomy "panel" i "boss") okno ma inny wygląd: panel sterujący i nadajnik zamiast płytki i dynamitu.
    bombPanelEl.dataset.kind = LEVELS[currentLevel].mode === "panel" || LEVELS[currentLevel].mode === "boss" ? "panel" : "bomb";
    setState("bomb");
    redrawBombWires();
}

// Shuffle each bomb's answer choices once, while keeping its correct answer attached.
function shuffleAnswers(question) {
    const answers = question.answers.map((text, index) => ({ text, correct: index === question.correctAnswer }));
    for (let index = answers.length - 1; index > 0; index--) {
        const swapIndex = Math.floor(Math.random() * (index + 1));
        [answers[index], answers[swapIndex]] = [answers[swapIndex], answers[index]];
    }
    return {
        ...question,
        answers: answers.map((answer) => answer.text),
        correctAnswer: answers.findIndex((answer) => answer.correct),
    };
}

// "Pusty" input: gra dostaje go zamiast klawiszy, gdy otwarty jest panel rozbrajania (postać stoi, reszta świata żyje).
const idleInput = new Proxy({}, {
    get: (_, name) => (name === "moveX" || name === "grappleLengthChange" ? () => 0 : name === "answerPressed" ? () => -1 : () => false),
});

// Zła odpowiedź = kara czasowa; po rozbrojeniu wszystkich bomb trzeba jeszcze dotrzeć do wyjścia po prawej.
function answerBomb(index) {
    if (state !== "bomb" || !activeBomb || !activeQuestion || !Number.isInteger(index) || index < 0 || index > 2) return;
    if (closeAfterCutTimer !== null) return; // poprawna odpowiedź już przecięła kabel, okno zaraz się zamknie
    const bombKey = `${currentLevel}:${activeBomb.id}`;
    if (wrongAnswers.get(bombKey)?.has(index)) return; // ta odpowiedź już była zła

    if (index === activeQuestion.correctAnswer) {
        // Bomba jest rozbrojona od razu, a okno zamyka się po chwili (żeby było widać przecięty kabel).
        game.defuse(activeBomb);
        cutWire(index, true);
        bombBoard.classList.add("is-locked");
        bombOptions.forEach((button) => { button.disabled = true; });
        closeAfterCutTimer = setTimeout(() => {
            closeAfterCutTimer = null;
            if (state !== "bomb") return;
            activeBomb = null;
            activeQuestion = null;
            setState("playing");
        }, CUT_CLOSE_DELAY_MS);
    } else {
        sound.play("wrong");
        const wrong = wrongAnswers.get(bombKey) ?? new Set();
        wrong.add(index);
        wrongAnswers.set(bombKey, wrong);
        game.addTimePenalty(WRONG_ANSWER_PENALTY);

        bombOptions[index].disabled = true;
        cutWire(index, false);
        bombPenalty.hidden = false;
        bombPenalty.textContent = `Zła odpowiedź! −${WRONG_ANSWER_PENALTY} s (razy ${wrong.size})`;
        // Fokus przechodzi na pierwszą dostępną odpowiedź (wyłączony przycisk go traci).
        bombOptions.find((button) => !button.disabled)?.focus({ preventScroll: true });
    }
}

// Rysuje zbieganie się kabli za odpowiedziami (po każdej zmianie układu okna: otwarcie, zmiana rozmiaru okna).
const WIRE_COLORS = ["red", "yellow", "blue"];
function redrawBombWires() {
    const px = parseFloat(getComputedStyle(bombPanelEl).getPropertyValue("--px")) || 2;
    const top = bombMerge.getBoundingClientRect().top;
    const centers = bombRows.map((row) => {
        const rect = row.querySelector(".bomb-board__wire--right").getBoundingClientRect();
        return rect.top + rect.height / 2 - top;
    });
    drawWireFunnel(bombMerge, WIRE_COLORS, centers, px);
}
window.addEventListener("resize", () => {
    if (state === "bomb") redrawBombWires();
});

// Przecina kabel odpowiedzi o danym indeksie (correct = poprawna odpowiedź: plakietka robi się zielona).
function cutWire(index, correct) {
    const row = bombRows[index];
    row.classList.remove("is-old");
    row.classList.add("is-cut");
    row.classList.toggle("is-correct", correct);
}

function cancelCloseAfterCut() {
    clearTimeout(closeAfterCutTimer);
    closeAfterCutTimer = null;
}

// Zamyka okno z pytaniem bez odpowiadania (Esc albo Q). Pytanie dla tej bomby zostaje to samo przy ponownym otwarciu.
function closeBomb() {
    if (state !== "bomb") return;
    cancelCloseAfterCut();
    activeBomb = null;
    activeQuestion = null;
    setState("playing");
}

function loseGame(reason) {
    sound.play("lose");
    cancelCloseAfterCut();
    activeBomb = null;
    activeQuestion = null;
    loseReason.textContent = reason;
    setState("lost");
}

function winGame() {
    sound.play("win");
    const hasNext = currentLevel + 1 < LEVELS.length;
    const name = LEVELS[currentLevel].name;
    if (!testingFromEditor) markCompleted(name); // odblokowuje następny poziom w menu
    const panel = LEVELS[currentLevel].mode !== "bombs" && LEVELS[currentLevel].mode !== undefined;
    winSummary.textContent = hasNext
        ? `${name} ukończony! ${panel ? (LEVELS[currentLevel].mode === "boss" ? "Wszystkie panele rozbrojone." : "Panel rozbrojony.") : "Wszystkie bomby rozbrojone."}`
        : `${name} ukończony! To był ostatni poziom, gratulacje!`;
    winTime.textContent = `Pozostały czas: ${formatTime(game.timeLeft)}`;
    winNext.hidden = !hasNext;
    // Fabuła pokazuje się od razu po wygranej, a dopiero po niej ekran z przyciskami (następny poziom, menu).
    // Po ostatnim poziomie zakończenie fabuły kończy się przyciskiem "Menu główne", więc ekranu wygranej już nie ma.
    const hasStory = hasStoryAfterLevel();
    playChapter(currentLevel, () => (hasNext || !hasStory ? setState("won") : quitToMenu()));
}

// Gra sama się zatrzymuje, gdy przełączysz kartę lub okno.
document.addEventListener("visibilitychange", () => {
    if (document.hidden) pauseGame();
});
window.addEventListener("blur", pauseGame);

setState("menu");

// ---------- Pętla gry ----------

let lastTime = performance.now();
let fps = 60; // wygładzona wartość, tylko do wyświetlania w trybie debug
let shownBombTime = ""; // żeby nie dotykać DOM, gdy tekst się nie zmienił

function frame(now) {
    const rawDt = (now - lastTime) / 1000;
    lastTime = now;
    if (rawDt > 0) fps += (1 / rawDt - fps) * 0.1;

    // dt = czas od poprzedniej klatki w sekundach (z limitem, np. po powrocie z innej karty).
    const dt = Math.min(rawDt, 0.05);

    if (input.debugPressed()) {
        debug = !debug;
        if (state === "menu") refreshLevelList(); // debug odblokowuje wszystkie poziomy
    }

    // Esc: w grze pauza; w pauzie najpierw wyłącza pełny ekran (jeśli jest włączony), a kolejny Esc wznawia grę;
    // w fabule przeskakuje dalej. Panel rozbrajania zamyka się niżej (Esc albo Q), bo gra się wtedy nie zatrzymuje.
    if (input.escapePressed() && performance.now() >= ignoreEscapeUntil) {
        if (state === "playing") pauseGame();
        else if (state === "paused") {
            if (isFullscreen()) exitFullscreen();
            else resumeGame();
        } else if (state === "story") storyPlayer.skip();
    }

    if (state === "playing" || state === "bomb") {
        // Gra toczy się dalej także przy otwartym panelu rozbrajania (przeciwnicy się ruszają, czas leci),
        // ale postać stoi: wtedy dostaje "pusty" input zamiast klawiszy gracza.
        const panelOpen = state === "bomb";
        const hpBeforeUpdate = game.hp;
        const updateResult = game.update(dt, panelOpen ? idleInput : input);

        if (!panelOpen) {
            if (updateResult.dashed && updateResult.dashTarget) {
                game.cuffEnemy(updateResult.dashTarget, "dash", { fromBehind: updateResult.dashFromBehind });
            }

            if (input.interactPressed()) {
                const enemy = game.nearbyEnemy("interact");
                if (enemy && game.cuffEnemy(enemy, "interact")) {
                    // Cuffing takes this E press; bombs remain available on the next press.
                } else {
                    const bomb = game.nearbyBomb();
                    if (bomb) openBomb(bomb);
                }
            }
        }

        if (state === "playing" || state === "bomb") game.resolveEnemyAttack();

        // Taking damage interrupts a defuse attempt. Keep the assigned question so
        // the player can reopen it and continue after recovering from the hit.
        if (panelOpen && state === "bomb" && game.hp < hpBeforeUpdate) closeBomb();

        // Tryb "bombs": rozbrojone wszystkie bomby i dojście do drzwi. Tryb "panel": wystarczy rozbrojony panel (chyba że poziom ma pole exit).
        if (state === "playing" && game.allDefused() && (!game.exitRequired || game.atExit())) winGame();

        // Utrata ostatniego HP (kolce albo przeciwnik) kończy poziom. Wcześniejsze trafienia
        // tylko cofają gracza do checkpointu (patrz game.js).
        if ((state === "playing" || state === "bomb") && game.isDead()) {
            loseGame(game.deathReason === "caught" ? "Kamil cię dopadł!" : "Straciłeś całe życie!");
        }

        if (state === "bomb") {
            const answer = input.answerPressed(); // klawisze A, B, C
            if (answer !== -1) answerBomb(answer);
            else if (input.escapePressed() || input.grapplePressed()) closeBomb(); // Esc albo Q zamyka panel

            const text = formatTime(game.timeLeft);
            if (text !== shownBombTime) {
                shownBombTime = text;
                bombTimer.textContent = text;
            }
        }
    }

    // Koniec czasu = przegrana (także podczas pytania).
    if ((state === "playing" || state === "bomb") && !game.allDefused() && game.timeLeft <= 0) {
        loseGame(game.mode === "bombs" ? "Czas minął! Bomby wybuchły." : "Czas minął! Nie rozbrojono wszystkich paneli.");
    }

    input.endFrame();

    if (state === "editor") {
        // Edytor rysuje na całym canvasie (bez skali i pasów gry).
        editor.update(dt);
        editor.draw(viewport.beginRaw());
        viewport.endRaw();
    } else {
        const ctx = viewport.begin();
        game.draw(ctx, { debug, fps, hud: state === "playing" || state === "bomb" });
        viewport.end();
    }

    requestAnimationFrame(frame);
}

requestAnimationFrame(frame);
