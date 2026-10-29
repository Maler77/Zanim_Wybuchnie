# Projekt konkursowy — gra przeglądarkowa

Minimalny szkielet gry działającej w nowoczesnej przeglądarce. Projekt używa zwykłego HTML, CSS i JavaScript, bez frameworka i bez zależności do instalowania.

## Uruchomienie

Uruchom lokalny serwer HTTP w katalogu projektu (wymagany dla modułów JavaScript):

```bash
python -m http.server 8000
```

Następnie otwórz <http://localhost:8000>. Wymagany jest Python 3. Polecenie uruchamia serwer tylko na czas pracy; zatrzymasz go przez `Ctrl+C`.

## Struktura

```text
index.html       Strona i punkt wejścia aplikacji
src/
  css/style.css  Wygląd strony i obszaru gry
  js/main.js     Punkt wejścia logiki gry
  js/game.js     Fizyka, rozgrywka i renderowanie obiektów
  js/levels.js   Definicje poziomów, bomb i przeciwników
  js/enemies.js  Typy przeciwników i reguły kajdankowania
  js/animations.js  Sprite sheety i animacje (opis arkuszy + mechanizm)
  js/viewport.js Renderowanie i skalowanie obszaru gry
  js/audio.js   Syntezowane efekty dźwiękowe i ustawienie głośności
assets/          Grafiki (tekstury, sprite sheety)
tools/           Skrypty pomocnicze w Pythonie (generowanie i składanie sprite sheetów)
```

## Dźwięk

Gra tworzy krótkie efekty retro i sześć zapętlonych motywów muzycznych przez Web Audio, bez dodatkowych plików. Każdy poziom ma własny motyw; zmienia się on po rozpoczęciu poziomu i zatrzymuje podczas pauzy oraz na ekranach menu i zakończenia. Efekty reagują na menu, skok, dash, hak, kajdankowanie, obrażenia, bombę, alarm oraz wygraną i przegraną. Przycisk „Dźwięk” w lewym górnym rogu włącza lub wycisza muzykę i efekty; ustawienie jest zapamiętywane w przeglądarce. Przeglądarka odblokowuje odtwarzanie po pierwszym kliknięciu lub naciśnięciu klawisza.

Menu główne jest pierwszym ekranem po otwarciu strony. Przycisk „Rozpocznij grę” uruchamia rozgrywkę i prosi przeglądarkę o tryb fullscreen. Menu pauzy pozostaje na pełnym ekranie podczas gry, gdy przeglądarka obsługuje blokadę klawisza Esc; przy braku tej obsługi Escape może wyjść z trybu przeglądarki, a gra pokaże menu pauzy w układzie wypełniającym stronę. Przycisk „Menu główne” kończy fullscreen. Obszar gry ma rozdzielczość 640 × 360 px (20 × 11,25 tila po 32 px, patrz `src/js/config.js`) i tymczasowe tło. Obraz jest skalowany do okna całkowitą skalą, żeby piksele były zawsze równe; przy proporcjach innych niż 16:9 renderer dodaje pasy. Jednostką w kodzie jest piksel gry (1/32 tila).

## Przeciwnicy

Poziom 1 zawiera patrolującego przeciwnika słabego (E z bliska lub dash) i patrolującego silnego (E od tyłu, zgodnie z kierunkiem, w którym patrzy). Kontakt z aktywnym przeciwnikiem odrzuca gracza; silny przeciwnik odrzuca mocniej. Krótki cooldown zapobiega ciągłym uderzeniom. Nowych przeciwników dodawaj do `enemies` w definicji poziomu. Typy i dozwolone metody kajdankowania są zdefiniowane w `src/js/enemies.js`; aby dodać metodę, dopisz jej nazwę do `cuffMethods` i wywołaj `game.cuffEnemy(enemy, "nazwaMetody")` z odpowiedniej akcji gry. Aktywni przeciwnicy skaczą wyłącznie po zablokowaniu przez solidną przeszkodę, którą mogą przeskoczyć; nie skaczą do gracza na wyższym piętrze ani przez przerwy.

## Animacje i sprite sheety

### Jak to działa

Sprite sheet to jeden plik PNG, w którym leżą obok siebie wszystkie klatki animacji. Gra wycina z niego odpowiednią klatkę i zmienia ją kilka razy na sekundę. Arkusze opisujesz w `SPRITE_SHEETS` na górze `src/js/animations.js` (plik, rozmiar klatki, animacje), a to, **kiedy** gra która animacja, wybiera funkcja `pickPlayerAnimation()` w `src/js/game.js` na podstawie stanu gracza.

Przykładowy arkusz gracza to `assets/player_sheet.png` (placeholder wygenerowany skryptem `tools/make_player_sheet.py`). Możesz go podmienić na własny plik o tym samym układzie i nic w kodzie nie trzeba zmieniać.

### Zasady rysowania arkusza

| Zasada | Dlaczego |
| --- | --- |
| **Wszystkie klatki mają ten sam rozmiar** (u nas 32 × 48 px) | Gra dzieli plik siatką `frameWidth × frameHeight`. Inny rozmiar klatek = poucinane i przesunięte obrazki. |
| **Jeden wiersz = jedna animacja**, klatki od lewej do prawej | Tak gra znajduje klatki: wiersz `row`, kolumny od `column` (domyślnie 0) przez `frames` klatek. |
| **Szerokość pliku = liczba kolumn × szerokość klatki** (u nas 6 × 32 = 192), wysokość = liczba wierszy × wysokość klatki (8 × 48 = 384) | Brak odstępów, ramek i marginesów między klatkami. Nieużywane pola zostają puste (przezroczyste). |
| **Stopy na samym dole klatki, postać na środku poziomo** w każdej klatce | Klatka stoi dolnym środkiem na dolnym środku hitboxa. Jeśli stopy w jednej klatce są wyżej, postać „podskakuje” albo wchodzi w podłogę. |
| **Postać patrzy w prawo** | Przy chodzeniu w lewo gra odbija klatkę lustrzanie. |
| **Przezroczyste tło** (PNG z kanałem alfa) | Gra nie zamalowuje tła. |
| **Ostre piksele: bez antyaliasingu, bez półprzezroczystych krawędzi, bez wygładzania przy skalowaniu** | Gra jest pixel-art. 1 piksel obrazka = 1 piksel gry, skaluje ją sama (całkowitą skalą). Nie powiększaj ani nie obracaj klatek w programie graficznym. |
| **Nie przycinaj klatek** (żadnego „trim”) | `trim` z `textures.js` nie dotyczy arkuszy: przycięte klatki miałyby różne rozmiary i by się rozjechały. |

### Rozmiar klatki a hitbox

Rozmiar postaci w grze to rozmiar klatki (32 × 48 px = 1 × 1,5 tila). **Hitbox jest osobno** i dalej ustawiasz go ręcznie (`PLAYER_HITBOX` w `game.js`, obecnie 24 × 44 px) albo wpisujesz `"auto"` (wtedy hitbox = cała klatka). Hitbox stoi tym samym dolnym środkiem co klatka, więc narysuj postać tak, żeby jej tułów mieścił się mniej więcej w hitboxie (u nas ok. 16 px szerokości i 44 px wysokości w klatce 32 × 48), a zapas po bokach zostaw na wyciągnięte ręce, linie prędkości dasha itp.

Jak wybrać rozmiar klatki: weź największą pozę (np. wyskok z rękami w górę, dash z liniami prędkości), dodaj kilka pikseli zapasu i **zostaw ten rozmiar dla wszystkich animacji**. Zmiana rozmiaru klatki w środku projektu oznacza przerysowanie całego arkusza.

### Animacje gracza w przykładowym arkuszu

| Wiersz | Nazwa | Klatek | fps | Kiedy gra |
| --- | --- | --- | --- | --- |
| 0 | `idle` | 4 | 4 | stoi na ziemi |
| 1 | `run` | 6 | 12 | biegnie po ziemi (także na haku, gdy stoi na ziemi) |
| 2 | `jump` | 2 | 8 (bez pętli) | w powietrzu, leci w górę |
| 3 | `fall` | 2 | 8 | w powietrzu, spada |
| 4 | `dash` | 2 | 12 | podczas dasha |
| 5 | `wallslide` | 2 | 6 | zsuwa się po ścianie (ściana jest po PRAWEJ stronie klatki, gra odbija ją, gdy ściana jest po lewej) |
| 6 | `swing` | 2 | 6 | huśta się na haku w powietrzu |
| 7 | `hurt` | 2 | 10 (bez pętli) | chwilę po utracie życia (0,3 s); po nietykalności postać jeszcze miga |

Kolejność sprawdzania w `pickPlayerAnimation()`: hurt, dash, swing, ściana, skok/spadanie, bieg, idle. Cienie po dashu rysują klatki z chwili ich powstania.

### Jak zrobić arkusz krok po kroku

1. **Ustal rozmiar klatki** (np. 32 × 48) i listę animacji z liczbą klatek (tabela wyżej).
2. **Narysuj klatki** w programie do pixel-artu, np. Aseprite (płatny, najwygodniejszy), LibreSprite (darmowy, podobny), Piskel (darmowy, w przeglądarce) lub Pixelorama (darmowy). Ustaw płótno na rozmiar JEDNEJ klatki i rysuj kolejne klatki na osi czasu. Stopy rysuj zawsze na ostatnim rzędzie pikseli, środek postaci na środku płótna. Włącz siatkę i podgląd animacji, żeby widzieć, czy postać nie „pływa”.
3. **Złóż arkusz** jedną z dwóch metod:
   - **Aseprite / LibreSprite:** `File > Export Sprite Sheet`, `Layout: Sheet Type = By Rows`, `Constraints = Fixed # of Columns` (liczba kolumn = klatki najdłuższej animacji, np. 6), `Borders`: wszystkie odstępy i „Trim” wyłączone (padding 0, bez Trim Sprite / Trim Cells, bez Merge Duplicates). Ten tryb wstawia klatki po kolei, więc wiersz zaczyna się dopiero po zapełnieniu poprzedniego. Jeśli animacje mają różną liczbę klatek, wygodniej użyć metody niżej.
   - **Skryptem w Pythonie** (działa z każdym programem, który umie wyeksportować klatki jako osobne PNG, a Aseprite robi to przez `File > Export` z opcją „Save as separate files”): ułóż klatki w katalogach `0_idle/0.png 1.png ...`, `1_run/...` i uruchom
     ```bash
     python tools/pack_sheet.py assets/player_frames assets/player_sheet.png
     ```
     Skrypt złoży arkusz (wiersz = animacja), sprawdzi, czy wszystkie klatki mają ten sam rozmiar, i wypisze gotowy wpis do `SPRITE_SHEETS`. Wymaga Pillow (`pip install pillow`).
4. **Zapisz jako PNG** w `assets/` (np. `assets/player_sheet.png`). Plik musi mieć kanał alfa i nie może być wygładzany ani przeskalowany.
5. **Opisz arkusz w `src/js/animations.js`:** `src`, `frameWidth`, `frameHeight` i animacje (`row`, `frames`, `fps`, opcjonalnie `loop: false` i `column`). Dla animacji, której klatki nie zaczynają się w pierwszej kolumnie, wpisz `column`.
6. **Sprawdź w grze:** uruchom serwer (`python -m http.server 8000`), włącz debug klawiszem `/`. Linia „animacja” pokazuje aktualną animację i klatkę (np. `run [3/6]`), a ramka hitboxa pokazuje, jak postać stoi względem hitboxa. Błędy opisu (zły rozmiar pliku, nieistniejący wiersz, za mało kolumn) gra wypisuje w konsoli przeglądarki (F12).

### Dodawanie nowej animacji gracza

1. Dorysuj nowy wiersz w arkuszu (np. `crouch` jako wiersz 8; plik robi się o jedną klatkę wyższy).
2. Dopisz go w `SPRITE_SHEETS.player.animations`:
   ```js
   crouch: { row: 8, frames: 2, fps: 6 },
   ```
3. W `pickPlayerAnimation()` w `game.js` dopisz warunek, kiedy ma grać, np. `if (player.crouching) return "crouch";`. Jeśli nazwy animacji nie ma w arkuszu, gra pokaże `idle` (a gdy go nie ma, pierwszą z listy).

### Animacje innych obiektów (np. przeciwnika)

Arkusz opisujesz tak samo w `SPRITE_SHEETS` (np. `enemyWeak: {...}`), a obiektowi dajesz własnego animatora:

```js
import { createAnimator } from "./animations.js";

const animator = createAnimator("enemyWeak");

// co klatkę:
animator.play(enemy.state === "chase" ? "run" : "walk"); // zmiana nazwy zaczyna animację od początku
animator.update(dt);

// przy rysowaniu (x, y, w, h to prostokąt, w którym ma stanąć klatka):
if (!animator.draw(ctx, x, y, w, h)) {
    // brak arkusza: rysuj zwykłą teksturę albo kolorowy prostokąt
}
```

Dla obiektu z hitboxem rozmiar obrazka możesz pobrać przez `getSheetFrameSize("enemyWeak")`. Gracz używa dokładnie tego mechanizmu (patrz `syncSize()` i `drawPlayer()` w `game.js`).

### Co robi gra, gdy arkusza brakuje

Gdy plik z arkuszem się nie wczyta, gra pisze ostrzeżenie w konsoli i rysuje statyczną teksturę `player` z `textures.js` (z przycięciem), a gdy i jej nie ma, kolorowy prostokąt. Dzięki temu gra działa, zanim powstanie jakakolwiek grafika.

### Typowe problemy

| Objaw | Przyczyna |
| --- | --- |
| Postać „podskakuje” albo drży między klatkami | Stopy lub środek postaci w różnych klatkach są w innych miejscach. Wyrównaj do dolnej krawędzi i środka klatki. |
| Postać jest rozciągnięta, ucięta albo widać kawałek sąsiedniej klatki | `frameWidth` / `frameHeight` w `animations.js` nie zgadzają się z rzeczywistym rozmiarem klatki w pliku (albo w pliku są odstępy lub marginesy). |
| Obraz jest rozmyty | Plik został przeskalowany albo wygładzony przy eksporcie. Eksportuj w skali 100% bez wygładzania. |
| Postać stoi lub chodzi odwrócona | Klatki są narysowane w lewo. Rysuj zawsze w prawo. |
| Animacja nie gra albo gra zła klatka | Zły `row` lub `frames`, albo warunek w `pickPlayerAnimation()`. Sprawdź linię „animacja” w debugu i konsolę. |
| Animacja się nie zmienia po podmianie pliku | Przeglądarka trzyma starą wersję w pamięci podręcznej. Odśwież z `Ctrl+F5`. |

## Zła odpowiedź, bomba dymna i skocznie

**Zła odpowiedź przy bombie** nie kończy już gry: zabiera 20 sekund z timera (`WRONG_ANSWER_PENALTY` na górze `src/js/main.js`), wybrana odpowiedź zostaje wyłączona, a pytanie zostaje otwarte. Każde kolejne pudło kosztuje kolejne 20 s. Gdy czas spadnie do zera, poziom kończy się jak zwykle ("Czas minął"). Kara jest też widoczna w HUD pod timerem.

**Bomba dymna (klawisz `F`).** Leci w linii prostej do najbliższego aktywnego przeciwnika w zasięgu haka (`SMOKE_RANGE` = `GRAPPLE_RANGE`). Po trafieniu w przeciwnika, w ścianę albo po przelocie całego zasięgu tworzy chmurę o promieniu 80 px, która trwa 6 s (rośnie na początku i kurczy się w ostatniej sekundzie). Przeciwnik, którego ciała dotyka chmura, jest oślepiony: nie ma stożka widzenia, nie zauważa gracza, a jeśli ścigał, przechodzi w tryb szukania i po 2 s wraca do patrolu. Nad oślepionym widać "?". Dym przenika przez ściany. Brak celu w zasięgu: rzut nie wychodzi i nie startuje cooldown (3 s, `SMOKE_COOLDOWN`). Wszystkie wartości (`SMOKE_*`) są na górze `src/js/game.js`. Wygląd: tekstury `smokeBomb` (pocisk) i `smokeCloud` (jeden kłębek chmury) w `textures.js`; bez plików rysowane są prosty kwadrat i kółka. Debug (`/`) pokazuje promienie chmur, linię do celu i liczbę oślepionych.

**Skocznia (jump pad).** Wejście na nią wyrzuca gracza w górę na ok. 5,3 tila (`JUMP_PAD_SPEED` w `game.js`). Dodajesz ją w poziomie w liście `jumpPads`, np. `jumpPad(464, 320)` (x = lewa krawędź, y = powierzchnia pod nią, opcjonalnie `count` i `{ power: 1.2 }` zmieniające siłę). Nie działa, gdy gracz wisi na linie. Tekstura `jumpPad` (kafelek 32 × 8 px) w `textures.js`. W poziomie 1 jest przykładowa skocznia na podłodze przy pierwszej wieży.

## Platform types

Level platforms are created with `platform(x, y, w, h, options)`. Platforms default to the existing fully solid behavior. Examples:

```js
platform(100, 240, 96, 12, { oneWay: true });
platform(300, 160, 24, 24, { solid: false, grappleable: true });
platform(400, 200, 96, 16, { grappleable: true });
```

`oneWay` lets the player pass from below and the sides, then catches them while descending onto the top. Intentional drop-through is not implemented. `grappleable` is independent of collision, so a target can be non-solid. A future hook can query `game.getGrappleTargets()`; each result has `x`, `y`, `w`, `h`, and its capability flags.

## Grappling hook

Press Q while facing a grappleable point within `160 * SCALE` game pixels (320 px with the current tile size) to attach. Solid platforms block the hook path. The rope swings with gravity and preserves momentum; left and right add swing force. While attached, W/Up shortens the rope and S/Down lengthens it. Space releases the rope and keeps swing momentum. Press Q again to switch to another reachable target immediately, or release if there is no other target. A full release starts the 0.5-second regrapple cooldown. The last detached anchor stays unavailable for 0.5 seconds. Grapple targets are level platforms marked with `grappleable: true` and can be listed with `game.getGrappleTargets()`.

## Editing bomb questions

All question content is in `src/data/questions.json`, grouped under `categories.easy`, `categories.medium`, and `categories.hard`. Edit this file with a text editor; questions and answers do not need to be changed in JavaScript. Each JSON level chooses a category through `questionCategory` (Level 1 uses easy, Levels 2-4 use medium, and Levels 5-7 use hard).

Add each question object to the array for its category. Give it a unique, non-empty `id` across the whole file, write its `question`, provide exactly three non-empty strings in `answers`, and set `correctAnswer` to the correct answer's zero-based position: `0` for the first answer, `1` for the second, or `2` for the third. When adding another object, put a comma after the previous object, but not after the final object in that category. Keep the file valid JSON and each category non-empty.

The game validates the file at startup and reports a clear error in the browser console if it cannot be loaded or any question is malformed. Run the local HTTP server described above so the browser can fetch the JSON file.
## Typy poziomów

Typ poziomu ustawia pole `mode` (w pliku JSON albo w edytorze, pole „Tryb”). Poziomy bez tego pola działają jak dotąd.

- **`"bombs"` (domyślny): bomby + drzwi.** Rozbrój wszystkie bomby (każda to pytanie z kategorii `questionCategory`), potem dojdź do drzwi „EXIT” na prawym końcu poziomu. Po rozbrojeniu ostatniej bomby timer się zatrzymuje.
- **`"panel"`: skradanka z jednym panelem.** Poziom ma dokładnie jedną „bombę” i jest ona panelem rozbrajania. Trzeba do niego podejść niezauważonym; wygrywasz od razu po poprawnej odpowiedzi (bez drzwi). Pytania są **zawsze trudne** (`hard`), niezależnie od `questionCategory`. Gdy którykolwiek przeciwnik zauważy gracza (przejdzie w pościg), włącza się **alarm**: na całej szerokości mapy zaczyna opadać na spadochronach kilkunastu przeciwników (pole `paratroopers`, domyślnie 14, co czwarty jest silny). Opadają ok. 3-6 s, nie rażą i nie widać ich pól widzenia, dopóki nie wylądują. Po wylądowaniu są „łowcami”: gonią gracza bez pola widzenia (oślepia ich tylko dym, klawisz F). Po utracie HP alarm trwa dalej, a restart poziomu go wyłącza.
- **`"boss"`: ucieczka przed kamikaze.** Duża mapa, po której goni gracza kamikaze z przyczepionymi bombami (przeciwnik typu `"kamikaze"`, minimum jeden na poziomie; na starcie stoi po lewej od gracza i rusza po `wait` sekundach). „Bomby” poziomu są panelami rozbrajania (zwykle 3); wygrywasz po poprawnych odpowiedziach na pytania ze wszystkich paneli, bez drzwi. Poziom zwykle ma `hp: 1`. **Gdy gracz zbliży się do kamikaze na ok. 80 px, ten wybucha od razu i oznacza to przegraną.** Kamikaze biega niewiele wolniej od gracza, skacze (do ok. 90 px wysokości) tylko po zablokowaniu przez osiągalną przeszkodę, odbija się od ścian (wall-jump w szybach z dwóch ścian, po jednej ścianie się nie wspina) i schodzi z krawędzi. Nie skacze przez luki ani do gracza na wyższym piętrze. Nie ma haka, dasha ani nie zmieści się w przejściach niższych niż jego wysokość (48 px; gracz ma 44 px), więc panele chroń przerwami tylko do pokonania hakiem albo ciasnym tunelem. Dym (F) trafiony w kamikaze spowalnia go do 40% (w chmurze i 2 s po niej), ale go nie zatrzymuje. Gdy kamikaze utknie (prawie się nie rusza przez 3 s) albo długo błąka się na innym piętrze niż gracz, znika i po chwili pojawia się w jednym z punktów `respawns` (tylko takim, który jest co najmniej `respawnDistance` px od gracza, domyślnie 600, a gdy żaden nie jest dość daleko, czeka). Punkty respawnu mogą mieć `stage` (ile paneli ma być rozbrojonych) i `side` (`"left"`/`"right"`: punkt musi leżeć po lewej/prawej od gracza, czyli za jego plecami). Przykład: `src/data/levels/poziom 7 boss.json` (6100 x 1500: dash, wall-jump, hak, tunel i trzy panele; wygenerowany skryptem, ale to zwykły JSON do edycji). W edytorze: Tryb „Boss (kamikaze)”, narzędzie „Kamikaze (boss)”, a pola „Start po (s)”, „Respawny” (`x,y[,panele[,L|P]]; ...`) i „Min. odległość respawnu” są we właściwościach zaznaczonego kamikaze.

Wskazówki do projektowania poziomu z panelem: pole widzenia przeciwnika sięga tylko do przodu i jest zasłaniane przez solidne platformy, więc od tyłu można podejść i zakuć go (E, silnego tylko od tyłu), a platforma pod graczem całkowicie chroni go przed strażnikami pod nią. Przykłady w `src/data/levels/poziom-5-panel.json` (górna ścieżka nad strażnikami) i `poziom-6-panel.json` (trzy piętra połączone skoczniami).

W edytorze po wybraniu trybu „Panel” zostaje jedna bomba (nowa zastępuje starą), pole „Pytania” znika (zawsze trudne), a pojawia się „Spadochroniarze”.

## Fabuła i postęp

Gra opowiada historię radykalizacji: po ukończeniu każdego poziomu pokazuje się jeden rozdział, czyli rozmowa w czacie grupowym (wiadomości pojawiają się z przerwami, jak na prawdziwym czacie, z „Ola pisze…”). Tematy po kolei: 1 „zwykła grupa”, 2 „my kontra oni”, 3 „izolacja”, 4 „eskalacja”, 5 „działanie” (plan ataku, który gracz udaremniał przez całą grę), 6 „konsekwencje”. Przed rozdziałem 1 pojawia się jeszcze ekran z tytułem gry, który dramatycznie zanika. Rozdział 6 pokazuje czat z napisem „Grupa usunięta”, potem scenę z policją i radiowozem (pixel art rysowany kodem w `src/js/policescene.js`), a na końcu ekran „Koniec” z morałem i przyciskiem „Menu główne”.

**Wszystko edytujesz w `src/data/story.json`** (zwykły edytor tekstu, pełny opis formatu jest w komentarzu na górze `src/js/story.js`). Najważniejsze pola:

- `title`: tytuł gry (`text`, `subtitle`, `fade` = czas pojawiania/znikania w sekundach, `hold` = jak długo stoi).
- `me`: imię osoby, z której telefonu patrzymy (jej wiadomości są po prawej, zielone). `people`: kolory autorów. `group`: domyślna nazwa i podpis grupy. `defaultDelay`: domyślna przerwa przed wiadomością.
- `chapters`: lista rozdziałów, `chapters[0]` po 1. poziomie, `chapters[1]` po 2. itd. (kolejność poziomów w menu). Rozdział ma `topic` (temat widoczny w nagłówku czatu), opcjonalnie `group` i `status` (nazwa grupy i podpis tylko w tym rozdziale), `messages`, opcjonalnie `auto` (liczba sekund, po których gra sama przechodzi dalej zamiast czekać na „Dalej”) i `then` (sceny po czacie).
- wiadomość w `messages`: `author` (`"system"` = szary wiersz na środku), `text`, **`delay` = przerwa w sekundach przed tą wiadomością**, opcjonalnie `typing` (jak długo widać „pisze…”), `time` (godzina pod wiadomością) i `banner: true` (wielki napis na czacie, np. „Grupa usunięta”).
- `then`: `{ "scene": "police", "duration": 8, "caption": "podpis" }` (opcjonalnie `"image": "assets/story/policja.png"` zamiast rysowanej sceny) oraz `{ "scene": "end", "title": "Koniec", "text": "morał", "button": "Menu główne" }`.

Poziom bez rozdziału (za mało wpisów w `chapters`) po prostu idzie dalej bez fabuły. Podczas odtwarzania kliknięcie albo Spacja pokazuje następną wiadomość od razu, a Esc / „Pomiń” przeskakuje dalej. Całą fabułę wyłączysz stałą `STORY_ENABLED` na górze `src/js/main.js`.

**Blokada poziomów.** W menu głównym kolejny poziom jest zablokowany, dopóki gracz nie ukończy poprzedniego (kolejność jak na liście w menu). Ukończone poziomy zapamiętuje przeglądarka (`localStorage`, `src/js/progress.js`, po nazwie poziomu), a „Resetuj postęp” pod listą poziomów zaczyna od nowa. **W trybie debug (klawisz `/`) wszystkie poziomy są odblokowane.** Na karcie ukończonego poziomu (w debugu na każdej) w rogu jest przycisk „💬 Fabuła”, który odtwarza jego rozdział, a potem wraca do menu.

Kolejność poziomów w menu: najpierw poziomy z `levels.js`, potem pliki JSON w kolejności z `index.json`; plik JSON o tej samej nazwie co poziom z kodu zastępuje go. Poziomy 2 i 3 z `levels.js` zostały usunięte, a poziomy są teraz w plikach JSON (1, 2, 3, 4, 5, 6 i 7 boss). Rozdziałów fabuły jest sześć, więc poziom 3 (`poziom-3.json`, miasto w nocy) nie ma własnego: jego miejsce w `story.json` zajmuje pusty rozdział `chapters[2]` (bez tematu i wiadomości, gra go pomija), dzięki czemu pozostałe rozdziały zostają przy swoich poziomach, a zakończenie po poziomie 7. Żeby dodać fabułę po poziomie 3, wpisz temat i wiadomości w tym pustym rozdziale.
