// ============================================================================
//  POSTĘP GRACZA: które poziomy zostały ukończone (zapis w localStorage przeglądarki).
//  Poziomy rozpoznajemy po NAZWIE (pole name), więc zmiana kolejności poziomów nie psuje zapisu.
//  Odblokowanie: poziom jest dostępny, gdy jest pierwszy albo poprzedni na liście został ukończony
//  (w trybie debug, klawisz "/", main.js odblokowuje wszystkie). Gdy localStorage jest zablokowany
//  (np. tryb prywatny), postęp trwa tylko do zamknięcia karty.
// ============================================================================

const KEY = "masywny-projekt.progress.v1";

let completed = readSaved();

function readSaved() {
    try {
        const parsed = JSON.parse(localStorage.getItem(KEY) ?? "[]");
        return new Set(Array.isArray(parsed) ? parsed.filter((name) => typeof name === "string") : []);
    } catch {
        return new Set();
    }
}

function save() {
    try {
        localStorage.setItem(KEY, JSON.stringify([...completed]));
    } catch {
        // zablokowany localStorage: postęp zostaje tylko w pamięci
    }
}

export function isCompleted(levelName) {
    return completed.has(levelName);
}

export function markCompleted(levelName) {
    if (completed.has(levelName)) return;
    completed.add(levelName);
    save();
}

export function resetProgress() {
    completed = new Set();
    save();
}

// Czy poziom o numerze `index` na liście `levels` jest odblokowany.
export function isUnlocked(levels, index) {
    return index === 0 || isCompleted(levels[index - 1]?.name);
}
