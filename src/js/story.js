// ============================================================================
//  FABUŁA: WCZYTYWANIE I SPRAWDZANIE src/data/story.json
//  Plik story.json edytujesz zwykłym edytorem tekstu. Odtwarzanie (czat, tytuł, scena z policją,
//  zakończenie) jest w storyplayer.js. Całość opisana jest też w README.md, sekcja "Fabuła".
//
//  STRUKTURA story.json
//    title          ekran tytułowy (opcjonalnie): { "text": "Tytuł", "subtitle": "podpis", "fade": 2.2, "hold": 2.4 }
//                   fade = czas pojawiania się i znikania (s), hold = jak długo tytuł stoi (s)
//    showTitle      true = tytuł pokazuje się raz, na początku fabuły po 1. poziomie; false (domyślnie) = nigdzie
//                   się nie pokazuje (wpis "title" może zostać w pliku na później)
//    topicIntro     { "fade": 1.6, "hold": 1.2 } jak długo temat rozdziału pojawia się (fade) i stoi samotnie (hold),
//                   zanim pojawi się okno grupy (s)
//    me             imię osoby, z której telefonu patrzymy (jej wiadomości są po prawej stronie)
//    defaultDelay   domyślna przerwa przed wiadomością (s), gdy wiadomość nie ma własnego "delay"
//    group          { "name": "...", "status": "6 uczestników" } nagłówek czatu (domyślny dla wszystkich rozdziałów)
//    people         kolory autorów: { "Kamil": "#79d7c4", ... } (autor bez koloru dostaje kolor automatyczny)
//    chapters       lista rozdziałów; chapters[0] pokazuje się po ukończeniu 1. poziomu, chapters[1] po 2. itd.
//                   (kolejność poziomów w menu głównym). Poziom bez rozdziału po prostu idzie dalej bez fabuły.
//
//  ROZDZIAŁ
//    topic          temat rozdziału (np. "zwykła grupa"): duży napis nad oknem grupy, który pojawia się jako pierwszy
//    group, status  (opcjonalnie) nazwa grupy i podpis tylko dla tego rozdziału
//    messages       lista wiadomości (patrz niżej)
//    auto           (opcjonalnie) liczba sekund; po ostatniej wiadomości gra sama przechodzi dalej
//                   po tylu sekundach. Bez tego pola pojawia się przycisk "Dalej".
//    then           (opcjonalnie) sceny po czacie, po kolei:
//                   { "scene": "police", "duration": 8, "caption": "podpis pod obrazem", "image": "assets/story/policja.png" }
//                   ("image" jest opcjonalne: bez niego gra rysuje własną scenę z radiowozem, patrz policescene.js)
//                   { "scene": "end", "title": "Koniec", "text": "morał", "button": "Menu główne" }
//
//  WIADOMOŚĆ
//    author   kto pisze; "system" (albo brak) = szary wiersz na środku (np. "Ola opuściła grupę")
//    text     treść
//    delay    przerwa w sekundach PRZED tą wiadomością (od poprzedniej). Ostatni ułamek tej przerwy
//             widać "X pisze..."; brak = defaultDelay
//    typing   (opcjonalnie) ile sekund trwa "pisze..." (domyślnie zależy od długości tekstu, ale nie więcej niż delay)
//    time     (opcjonalnie) godzina pod wiadomością, np. "21:40"
//    banner   (opcjonalnie, tylko system) true = wielki napis na całym czacie (np. "Grupa usunięta"):
//             czat ciemnieje i nie da się już pisać
//
//  Kliknięcie lub Spacja przyspiesza (pokazuje następną wiadomość od razu), Esc / "Pomiń" przeskakuje dalej.
//  Brak pliku story.json = gra bez fabuły. Całą fabułę wyłączysz stałą STORY_ENABLED na górze main.js.
// ============================================================================

const STORY_URL = new URL("../data/story.json", import.meta.url);

const DEFAULT_DELAY = 1.7;
const PALETTE = ["#79d7c4", "#ffb86b", "#8ab4ff", "#c7a2ff", "#ff9ec4", "#ffe08a", "#9be37a", "#ff8f70"];

const isText = (value) => typeof value === "string";

// Liczba z pliku albo wartość domyślna; poza zakresem min..max przycinamy.
function num(value, fallback, min, max) {
    if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
    return Math.min(max, Math.max(min, value));
}

// Stały kolor autora (ta sama osoba zawsze ma ten sam kolor, nawet bez wpisu w "people").
function autoColor(name) {
    let hash = 0;
    for (const char of name) hash = (hash * 31 + char.codePointAt(0)) >>> 0;
    return PALETTE[hash % PALETTE.length];
}

function cleanMessage(raw, where, defaultDelay) {
    if (!raw || typeof raw !== "object" || !isText(raw.text)) {
        console.warn(`story.json: ${where} pominięta (wiadomość musi mieć pole "text" z tekstem)`);
        return null;
    }
    const author = isText(raw.author) && raw.author.trim() ? raw.author.trim() : "system";
    const system = author.toLowerCase() === "system";
    return {
        author,
        system,
        text: raw.text,
        delay: num(raw.delay, defaultDelay, 0, 60),
        typing: raw.typing === undefined ? null : num(raw.typing, null, 0, 30),
        time: isText(raw.time) ? raw.time : "",
        banner: system && raw.banner === true,
    };
}

function cleanScene(raw, where) {
    if (!raw || typeof raw !== "object") return null;
    if (raw.scene === "police") {
        return {
            scene: "police",
            duration: num(raw.duration, 8, 1, 120),
            caption: isText(raw.caption) ? raw.caption : "",
            image: isText(raw.image) && raw.image ? raw.image : null,
        };
    }
    if (raw.scene === "end") {
        return {
            scene: "end",
            title: isText(raw.title) ? raw.title : "Koniec",
            text: isText(raw.text) ? raw.text : "",
            button: isText(raw.button) && raw.button ? raw.button : "Menu główne",
        };
    }
    console.warn(`story.json: ${where} pominięta (scene musi być "police" albo "end")`);
    return null;
}

function cleanChapter(raw, index, defaults) {
    const where = `chapters[${index}]`;
    if (!raw || typeof raw !== "object") {
        console.warn(`story.json: ${where} pominięty (rozdział musi być obiektem)`);
        return null;
    }
    const messages = (Array.isArray(raw.messages) ? raw.messages : [])
        .map((message, i) => cleanMessage(message, `${where}.messages[${i}]`, defaults.delay))
        .filter(Boolean);
    const then = (Array.isArray(raw.then) ? raw.then : [])
        .map((scene, i) => cleanScene(scene, `${where}.then[${i}]`))
        .filter(Boolean);
    return {
        topic: isText(raw.topic) ? raw.topic : "",
        group: isText(raw.group) && raw.group ? raw.group : defaults.group.name,
        status: isText(raw.status) ? raw.status : defaults.group.status,
        messages,
        auto: typeof raw.auto === "number" && Number.isFinite(raw.auto) ? Math.max(0, raw.auto) : null,
        then,
    };
}

// Zamienia surowy JSON na obiekt, z którego korzysta gra (z domyślnymi wartościami i bez błędnych wpisów).
export function normalizeStory(raw) {
    const defaults = {
        delay: num(raw.defaultDelay, DEFAULT_DELAY, 0, 60),
        group: {
            name: isText(raw.group?.name) ? raw.group.name : "Grupa",
            status: isText(raw.group?.status) ? raw.group.status : "",
        },
    };
    const people = raw.people && typeof raw.people === "object" ? raw.people : {};
    const title = raw.title && typeof raw.title === "object" && isText(raw.title.text) && raw.title.text
        ? {
            text: raw.title.text,
            subtitle: isText(raw.title.subtitle) ? raw.title.subtitle : "",
            fade: num(raw.title.fade, 2.2, 0.2, 10),
            hold: num(raw.title.hold, 2.4, 0, 30),
        }
        : null;
    const chapters = (Array.isArray(raw.chapters) ? raw.chapters : [])
        .map((chapter, i) => cleanChapter(chapter, i, defaults));
    return {
        loaded: true,
        title,
        showTitle: raw.showTitle === true && title !== null,
        topicIntro: {
            fade: num(raw.topicIntro?.fade, 1.6, 0.2, 10),
            hold: num(raw.topicIntro?.hold, 1.2, 0, 30),
        },
        me: isText(raw.me) ? raw.me : "",
        people,
        chapters, // wpis null = ten poziom nie ma fabuły
        colorOf: (name) => (isText(people[name]) ? people[name] : autoColor(name)),
    };
}

// Rozdział fabuły po ukończeniu poziomu o numerze `index` (od 0) albo null, gdy go nie ma.
export function storyChapter(story, index) {
    if (!story.loaded) return null;
    const chapter = story.chapters[index];
    if (!chapter || (chapter.messages.length === 0 && chapter.then.length === 0)) return null;
    return chapter;
}

// Wczytuje fabułę. Zawsze zwraca obiekt z polem loaded (false, gdy nie ma pliku albo jest błędny).
export async function loadStory() {
    const empty = { loaded: false, title: null, showTitle: false, topicIntro: { fade: 1.6, hold: 1.2 }, me: "", people: {}, chapters: [], colorOf: autoColor };
    try {
        const response = await fetch(STORY_URL, { cache: "no-cache" });
        if (!response.ok) return empty;
        return normalizeStory(await response.json());
    } catch (error) {
        console.warn(`Nie można wczytać fabuły (src/data/story.json): ${error.message}`);
        return empty;
    }
}