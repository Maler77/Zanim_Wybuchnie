// Menu w HTML: pokazuje i ukrywa ekrany (.menu[data-screen]) oraz obsługuje przyciski.
// Przyciski z data-action="controls" i "back" obsługuje samo, resztę przekazuje do main.js.

export function createMenu(actions) {
    const screens = new Map(
        [...document.querySelectorAll(".menu[data-screen]")].map((element) => [element.dataset.screen, element]),
    );

    let current = null;   // nazwa widocznego ekranu albo null, gdy menu jest ukryte
    let origin = "main";  // dokąd wraca "Wróć" z ekranu sterowania

    function show(name) {
        // Zapamiętujemy, skąd otwarto sterowanie (z menu głównego czy z pauzy).
        if ((name === "controls" || name === "levels") && current && current !== "controls" && current !== "levels") origin = current;

        for (const [key, element] of screens) element.hidden = key !== name;
        current = name;
        document.body.dataset.menuScreen = name; // CSS (np. ukrycie rogu ze sterowaniem na ekranie tytułowym)
        if (name === "controls") document.body.dataset.menuOrigin = origin;
        else delete document.body.dataset.menuOrigin;

        // Fokus na pierwszym przycisku, żeby Enter działał od razu.
        visibleButtons(name)[0]?.focus({ preventScroll: true });
    }

    // Przyciski ekranu, które są teraz widoczne (część może mieć atrybut hidden).
    function visibleButtons(name) {
        return [...(screens.get(name)?.querySelectorAll("button") ?? [])].filter((button) => !button.hidden && !button.disabled);
    }

    function hide() {
        for (const element of screens.values()) element.hidden = true;
        current = null;
        delete document.body.dataset.menuScreen;
        delete document.body.dataset.menuOrigin;
    }

    function back() {
        show(origin);
    }

    // Kliknięcia w przyciski.
    document.addEventListener("click", (event) => {
        const target = event.target instanceof Element ? event.target : null;
        const button = target?.closest("button[data-action]");
        if (!button) return;

        const action = button.dataset.action;
        if (action === "controls" || action === "levels") show(action);
        else if (action === "back") back();
        else actions[action]?.(button.dataset);
    });

    // Strzałki góra/dół (oraz W/S) przesuwają zaznaczenie między przyciskami.
    document.addEventListener("keydown", (event) => {
        if (!current) return;

        const step = ["ArrowDown", "KeyS"].includes(event.code) ? 1
            : ["ArrowUp", "KeyW"].includes(event.code) ? -1
            : 0;
        if (step === 0) return;
        event.preventDefault();

        const buttons = visibleButtons(current);
        if (buttons.length === 0) return;
        const index = buttons.indexOf(document.activeElement);
        const next = index === -1
            ? (step > 0 ? 0 : buttons.length - 1)
            : (index + step + buttons.length) % buttons.length;
        buttons[next].focus();
    });

    return {
        show,
        hide,
        back,
        get current() { return current; },
    };
}
