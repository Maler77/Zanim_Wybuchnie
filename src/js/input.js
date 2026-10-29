// Obsługa klawiatury. Pamięta, które klawisze są wciśnięte
// oraz które zostały wciśnięte dokładnie w tej klatce (skok, dash, debug, pauza, interakcja).

const LEFT = ["ArrowLeft", "KeyA"];
const RIGHT = ["ArrowRight", "KeyD"];
const JUMP = ["Space", "ArrowUp", "KeyW"];
const GRAPPLE_RELEASE = ["Space"];
const GRAPPLE_SHORTEN = ["ArrowUp", "KeyW"];
const GRAPPLE_EXTEND = ["ArrowDown", "KeyS"];
const DROP = ["ArrowDown", "KeyS"];
const DASH = ["ShiftLeft", "ShiftRight"];
const DEBUG = ["Slash"];
const PAUSE = ["Escape"];
const INTERACT = ["KeyE"];
const GRAPPLE = ["KeyQ"];
const SMOKE = ["KeyF"];
// Odpowiedzi w oknie bomby: litery A, B, C (albo cyfry 1, 2, 3).
const ANSWERS = [["KeyA", "Digit1"], ["KeyB", "Digit2"], ["KeyC", "Digit3"]];

// Klawisze, którym blokujemy domyślne działanie (strzałki i spacja przewijają stronę,
// a "/" w Firefoksie otwiera szybkie wyszukiwanie).
const GAME_KEYS = new Set([...LEFT, ...RIGHT, ...JUMP, ...DEBUG, ...GRAPPLE, ...GRAPPLE_EXTEND]);

// Zwraca kod klawisza. Znak "/" traktujemy zawsze jako "Slash", także na układach,
// gdzie jest pod Shift+7 (np. niemiecki).
function codeOf(event) {
    return event.key === "/" ? "Slash" : event.code;
}

export function createInput() {
    const down = new Set();    // klawisze trzymane teraz
    const pressed = new Set(); // klawisze wciśnięte w tej klatce

    const onKeyDown = (event) => {
        const code = codeOf(event);
        // Na przycisku menu zostawiamy domyślne działanie (Spacja i Enter mają go "klikać").
        // W polach tekstowych i listach (edytor) klawisze działają normalnie, np. można wpisać "a" albo spację.
        const onButton = event.target instanceof HTMLButtonElement
            || event.target instanceof HTMLInputElement
            || event.target instanceof HTMLSelectElement
            || event.target instanceof HTMLTextAreaElement;
        if (GAME_KEYS.has(code) && !onButton) event.preventDefault();
        // Przytrzymany klawisz wysyła powtórzenia; liczymy tylko pierwsze wciśnięcie.
        if (!event.repeat) pressed.add(code);
        down.add(code);
    };
    const onKeyUp = (event) => down.delete(codeOf(event));
    // Gdy okno traci fokus, puszczamy wszystkie klawisze (inaczej postać "ucieka").
    const onBlur = () => down.clear();

    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);
    window.addEventListener("blur", onBlur);

    const any = (codes, set) => codes.some((code) => set.has(code));

    return {
        // Kierunek poziomy: -1 (lewo), 0 albo 1 (prawo).
        moveX: () => Number(any(RIGHT, down)) - Number(any(LEFT, down)),
        // Czy klawisz skoku jest trzymany (do regulacji wysokości skoku).
        jumpHeld: () => any(JUMP, down),
        // Czy klawisz skoku został dopiero co wciśnięty (jeden skok na naciśnięcie).
        jumpPressed: () => any(JUMP, pressed),
        dropPressed: () => any(DROP, pressed),
        grappleReleasePressed: () => any(GRAPPLE_RELEASE, pressed),
        grappleLengthChange: () => Number(any(GRAPPLE_EXTEND, down)) - Number(any(GRAPPLE_SHORTEN, down)),
        // Czy Shift został dopiero co wciśnięty (dash).
        dashPressed: () => any(DASH, pressed),
        // Czy "/" został dopiero co wciśnięty (przełączenie trybu debug).
        debugPressed: () => any(DEBUG, pressed),
        // Czy Esc został dopiero co wciśnięty (pauza / wznowienie / powrót).
        escapePressed: () => any(PAUSE, pressed),
        // Czy E został dopiero co wciśnięty (interakcja z bombą).
        interactPressed: () => any(INTERACT, pressed),
        grapplePressed: () => any(GRAPPLE, pressed),
        // Czy F został dopiero co wciśnięty (bomba dymna).
        smokePressed: () => any(SMOKE, pressed),
        // Indeks odpowiedzi (0 = A, 1 = B, 2 = C) wciśniętej w tej klatce albo -1.
        answerPressed: () => ANSWERS.findIndex((codes) => any(codes, pressed)),
        // Wołane raz na koniec każdej klatki z main.js.
        endFrame: () => pressed.clear(),
        destroy() {
            window.removeEventListener("keydown", onKeyDown);
            window.removeEventListener("keyup", onKeyUp);
            window.removeEventListener("blur", onBlur);
        },
    };
}
