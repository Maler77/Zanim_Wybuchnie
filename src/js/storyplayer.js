// ============================================================================
//  ODTWARZACZ FABUŁY
//  Pokazuje jeden rozdział z story.json (opis formatu: story.js): opcjonalnie tytuł, potem czat grupowy
//  z wiadomościami wysyłanymi z przerwami, a po nim (jeśli rozdział ma "then") scenę z policją i ekran końcowy.
//  main.js tworzy odtwarzacz raz (createStoryPlayer) i woła play(). Wygląd: sekcja "Fabuła" w style.css.
//
//  Sterowanie: kliknięcie albo Spacja przyspiesza (następna wiadomość od razu), Esc albo "Pomiń" przeskakuje
//  dalej, a po ostatniej wiadomości trzeba kliknąć "Dalej" (chyba że rozdział ma pole "auto").
// ============================================================================

import { drawPoliceScene, SCENE_HEIGHT, SCENE_WIDTH } from "./policescene.js";

const READ_LOCK_MS = 700; // tyle po pokazaniu "Dalej" Spacja jeszcze nie przechodzi dalej (żeby nie przeskoczyć przez przypadek)

function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
}

export function createStoryPlayer(root, story) {
    root.replaceChildren();
    root.tabIndex = -1;

    // ---------- Warstwy (każda scena to osobna warstwa, przełączane płynnie) ----------
    const layers = {};
    function addLayer(name) {
        const layer = el("div", `story-layer story-layer--${name}`);
        layers[name] = layer;
        root.append(layer);
        return layer;
    }

    // Tytuł
    const titleLayer = addLayer("title");
    const titleBox = el("div", "story-title");
    const titleText = el("h1", "story-title__text");
    const titleSub = el("p", "story-title__sub");
    titleBox.append(titleText, titleSub);
    titleLayer.append(titleBox);

    // Czat
    const chatLayer = addLayer("chat");
    const topicHeading = el("h2", "story-topic");
    const chatSlot = el("div", "chat-slot");
    const nextButton = el("button", "menu__button menu__button--primary story-next", "Dalej");
    nextButton.type = "button";
    nextButton.hidden = true;
    chatLayer.append(topicHeading, chatSlot, nextButton);

    // Policja
    const policeLayer = addLayer("police");
    const policeCanvas = el("canvas", "story-police__canvas");
    policeCanvas.width = SCENE_WIDTH;
    policeCanvas.height = SCENE_HEIGHT;
    const policeImage = el("div", "story-police__image");
    const policeCaption = el("p", "story-police__caption");
    policeLayer.append(policeCanvas, policeImage, policeCaption);

    // Zakończenie: tytuł u góry, tekst na środku, przycisk na dole
    const endLayer = addLayer("end");
    const endTitle = el("h2", "story-end__title");
    const endText = el("p", "story-end__text");
    const endButton = el("button", "menu__button menu__button--primary story-end__button");
    endButton.type = "button";
    endLayer.append(endTitle, endText, endButton);

    const skipButton = el("button", "story-skip", "Pomiń ⏭");
    skipButton.type = "button";
    root.append(skipButton);

    function showLayer(name) {
        for (const [key, layer] of Object.entries(layers)) layer.classList.toggle("is-visible", key === name);
    }

    // ---------- Stan odtwarzania ----------
    let runId = 0;          // zwiększany przy każdym play()/stop(), żeby stare sekwencje same się przerwały
    let stage = "idle";     // idle | title | chat | reading | police | end
    let fast = false;       // true = czekanie trwa 0 s (po Esc / "Pomiń")
    let wakeup = null;      // przerywa bieżące czekanie
    let buttonResolve = null;
    let readingSince = 0;
    let policeFrame = 0;

    const setStage = (next) => {
        stage = next;
        root.dataset.stage = next;
    };

    function wait(seconds) {
        return new Promise((resolve) => {
            if (fast || seconds <= 0) {
                resolve();
                return;
            }
            const done = () => {
                clearTimeout(timer);
                if (wakeup === done) wakeup = null;
                resolve();
            };
            const timer = setTimeout(done, seconds * 1000);
            wakeup = done;
        });
    }

    function nudge() {
        wakeup?.();
    }

    function waitForButton() {
        return new Promise((resolve) => {
            buttonResolve = () => {
                buttonResolve = null;
                resolve();
            };
        });
    }

    // ---------- Tytuł ----------
    async function titleScene(run) {
        const title = story.title;
        setStage("title");
        fast = false;
        titleText.textContent = title.text;
        titleSub.textContent = title.subtitle;
        titleLayer.style.setProperty("--fade", `${title.fade}s`);
        titleBox.className = "story-title";
        showLayer("title");

        await wait(0.7);
        if (run !== runId) return;
        titleBox.classList.add("is-in");                 // pojawia się
        await wait(title.fade + title.hold);
        if (run !== runId) return;
        titleBox.classList.add("is-out");                // dramatycznie zanika (dłużej niż się pojawiał)
        await wait(title.fade * 1.6 + 0.3);
    }

    // ---------- Czat ----------
    function buildChat(chapter) {
        const chat = el("div", "chat");

        const header = el("div", "chat__header");
        const avatar = el("span", "chat__avatar chat__avatar--group", chapter.group.slice(0, 1).toUpperCase());
        const info = el("div", "chat__info");
        const name = el("span", "chat__name", chapter.group);
        const status = el("span", "chat__status", chapter.status);
        info.append(name, status);
        header.append(avatar, info);

        const list = el("div", "chat__list");
        const typing = el("div", "chat__typing");
        const typingName = el("span", "chat__typing-name");
        const dots = el("span", "chat__dots");
        dots.append(el("i"), el("i"), el("i"));
        typing.append(typingName, dots);

        const composer = el("div", "chat__composer");
        const input = el("span", "chat__input", "Napisz wiadomość…");
        composer.append(input, el("span", "chat__send", "➤"));

        const banner = el("div", "chat__banner");
        chat.append(header, list, typing, composer, banner);
        chatSlot.replaceChildren(chat);
        return { chat, list, typing, typingName, banner, status, input };
    }

    function appendMessage(ui, msg, lastAuthorRef) {
        if (msg.system) {
            ui.list.append(el("div", `chat-sys${fast ? " is-instant" : ""}`, msg.text));
            lastAuthorRef.name = null;
        } else {
            const me = msg.author === story.me;
            const follow = lastAuthorRef.name === msg.author;
            const row = el("div", `chat-msg${me ? " is-me" : ""}${follow ? " is-follow" : ""}${fast ? " is-instant" : ""}`);
            const color = story.colorOf(msg.author);
            if (!me) {
                const avatar = el("span", "chat__avatar", msg.author.slice(0, 1).toUpperCase());
                avatar.style.background = color;
                row.append(avatar);
            }
            const bubble = el("div", "chat-msg__bubble");
            if (!me && !follow) {
                const author = el("span", "chat-msg__author", msg.author);
                author.style.color = color;
                bubble.append(author);
            }
            bubble.append(el("span", "chat-msg__text", msg.text));
            if (msg.time) bubble.append(el("span", "chat-msg__time", msg.time));
            row.append(bubble);
            ui.list.append(row);
            lastAuthorRef.name = msg.author;
        }
        ui.list.scrollTo({ top: ui.list.scrollHeight, behavior: fast ? "auto" : "smooth" });
    }

    // Domyślny czas "pisze..." rośnie z długością tekstu, ale nie przekracza przerwy przed wiadomością.
    function typingTime(msg) {
        const base = msg.typing ?? Math.min(2.6, Math.max(0.8, 0.5 + msg.text.length * 0.028));
        return Math.min(msg.delay, base);
    }

    async function chatScene(run, chapter, options) {
        setStage("chat");
        fast = false;
        nextButton.hidden = true;
        const ui = buildChat(chapter);
        const lastAuthorRef = { name: null };

        // Najpierw pojawia się sam temat rozdziału (jak tytuł), dopiero potem okno grupy pod nim.
        chatSlot.classList.remove("is-in");
        topicHeading.className = "story-topic";
        topicHeading.textContent = chapter.topic;
        chatLayer.style.setProperty("--fade", `${story.topicIntro.fade}s`);
        showLayer("chat");
        await wait(0.8);
        if (run !== runId) return;
        if (chapter.topic) {
            topicHeading.classList.add("is-in");
            await wait(story.topicIntro.fade + story.topicIntro.hold);
            if (run !== runId) return;
        }
        chatSlot.classList.add("is-in");
        await wait(0.9);
        for (const msg of chapter.messages) {
            if (run !== runId) return;
            const typing = msg.system ? 0 : typingTime(msg);
            await wait(msg.delay - typing);
            if (run !== runId) return;
            if (typing > 0 && !fast) {
                ui.typingName.textContent = `${msg.author} pisze`;
                ui.typing.classList.add("is-on");
                await wait(typing);
                ui.typing.classList.remove("is-on");
                if (run !== runId) return;
            }
            if (msg.banner) {
                ui.banner.textContent = msg.text;
                ui.chat.classList.add("is-deleted");
                ui.status.textContent = msg.text;
                ui.input.textContent = "Nie można już pisać w tej grupie";
            } else {
                appendMessage(ui, msg, lastAuthorRef);
            }
        }

        if (chapter.auto !== null) {
            await wait(chapter.auto);
            return;
        }
        // Czekamy na "Dalej": przyciski bez przypadkowego przeskoczenia Spacją.
        setStage("reading");
        readingSince = performance.now();
        nextButton.textContent = options.nextLabel;
        nextButton.hidden = false;
        await waitForButton();
        nextButton.hidden = true;
    }

    // ---------- Policja ----------
    async function policeScene(run, scene) {
        setStage("police");
        fast = false;
        policeCaption.textContent = scene.caption;
        policeCaption.classList.remove("is-in");
        const hasImage = Boolean(scene.image);
        policeCanvas.hidden = hasImage;
        policeImage.hidden = !hasImage;
        if (hasImage) policeImage.style.backgroundImage = `url("${new URL(scene.image, document.baseURI).href}")`;
        showLayer("police");

        const startedAt = performance.now();
        const ctx = policeCanvas.getContext("2d");
        const loop = () => {
            if (!hasImage) drawPoliceScene(ctx, (performance.now() - startedAt) / 1000);
            policeFrame = requestAnimationFrame(loop);
        };
        policeFrame = requestAnimationFrame(loop);

        await wait(1.4);
        if (run === runId) policeCaption.classList.add("is-in");
        await wait(scene.duration - 1.4);
        cancelAnimationFrame(policeFrame);
    }

    // ---------- Zakończenie ----------
    async function endScene(run, scene) {
        setStage("end");
        fast = false;
        endTitle.textContent = scene.title;
        endText.textContent = scene.text;
        endButton.textContent = scene.button;
        showLayer("end");
        await waitForButton();
    }

    // ---------- Sterowanie ----------
    function proceed() {
        buttonResolve?.();
    }

    function skip() {
        if (stage === "idle" || stage === "end") return;
        if (stage === "reading") {
            proceed();
            return;
        }
        fast = true; // title, chat, police: wszystkie czekania natychmiast się kończą
        nudge();
    }

    nextButton.addEventListener("click", proceed);
    endButton.addEventListener("click", proceed);
    skipButton.addEventListener("click", skip);

    // Kliknięcie w pusty obszar i Spacja / Enter przyspieszają.
    root.addEventListener("click", (event) => {
        if (event.target instanceof Element && event.target.closest("button")) return;
        if (stage === "chat") nudge();
        else if (stage === "title" || stage === "police") skip();
    });

    document.addEventListener("keydown", (event) => {
        if (stage === "idle" || event.repeat) return;
        if (event.code !== "Space" && event.code !== "Enter") return;
        if (document.activeElement instanceof HTMLButtonElement) return; // przycisk obsłuży to sam
        event.preventDefault();
        if (stage === "chat") nudge();
        else if (stage === "title" || stage === "police") skip();
        else if (stage === "reading" && performance.now() - readingSince > READ_LOCK_MS) proceed();
    });

    // ---------- Publiczne API ----------
    // chapter: wpis z story.chapters. options: { showTitle, nextLabel, onDone }.
    async function play(chapter, options = {}) {
        const opts = { showTitle: false, nextLabel: "Dalej", onDone: null, ...options };
        const run = ++runId;
        try {
            if (opts.showTitle && story.title) await titleScene(run);
            if (run !== runId) return;
            if (chapter.messages.length > 0) await chatScene(run, chapter, opts);
            for (const scene of chapter.then) {
                if (run !== runId) return;
                if (scene.scene === "police") await policeScene(run, scene);
                else await endScene(run, scene);
            }
        } finally {
            cancelAnimationFrame(policeFrame);
        }
        if (run !== runId) return;
        stop();
        opts.onDone?.();
    }

    function stop() {
        runId++;
        setStage("idle");
        fast = false;
        cancelAnimationFrame(policeFrame);
        nextButton.hidden = true;
        showLayer(null);
        wakeup?.();
        buttonResolve = null;
    }

    function focus() {
        root.focus({ preventScroll: true });
    }

    setStage("idle");
    return { play, skip, stop, focus, get stage() { return stage; } };
}