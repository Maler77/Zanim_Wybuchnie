import { SCALE } from "./config.js";

// ============================================================================
//  PRZECIWNICY
//  Typy przeciwników, ich pole widzenia, zasady kajdankowania oraz zachowanie (patrol, pościg).
//  Wymiary i prędkości są zapisane dla tila 16 px i mnożone przez SCALE (patrz config.js).
//
//  ZACHOWANIE
//    patrol   chodzi lewo-prawo po całej platformie, na której stoi (nie schodzi z jej krawędzi)
//    pościg   gdy gracz wejdzie w pole widzenia (zielony/żółty stożek), biegnie za nim trochę szybciej
//             (chaseMultiplier). W pościgu MOŻE zejść z platformy, ale tylko tak, żeby nie wyjść
//             poza swój prostokąt `area` i wylądować na jakiejś platformie wewnątrz niego.
//    zagubienie  gdy straci gracza z oczu, biegnie jeszcze do miejsca, w którym go widział,
//             czeka SEARCH_TIME sekund, odwraca się i wraca do patrolu
//    dotknięcie od tyłu  nad głową pojawia się "!", po ALERT_TURN_DELAY sekundach przeciwnik się
//             odwraca i czeka SEARCH_TIME na gracza (zobaczy go = pościg, nie = odwraca się i patroluje)
//    skok     aktywni przeciwnicy skaczą tylko po zablokowaniu przez solidną przeszkodę, którą mogą
//             przeskoczyć; nie skaczą do gracza na wyższym piętrze ani przez przerwy w podłodze
//    atak     tylko od przodu (patrz resolveEnemyAttack w game.js); każdy atak zabiera `damage` HP
//    grawitacja  działa na przeciwników tak samo jak na gracza
//
//  JAK USTAWIĆ POLE WIDZENIA (vision) w ENEMY_TYPES poniżej (albo dla jednego przeciwnika w levels.js:
//  enemy("weak", x, y, { vision: { length: 120 * SCALE } }))
//    angle    kąt całego stożka w stopniach (np. 50 = 25° w górę i 25° w dół od kierunku patrzenia)
//    length   długość (promień) stożka w px
//    offsetX  przesunięcie początku stożka do przodu od środka przeciwnika (px; po obróceniu się
//             przeciwnika stożek obraca się razem z nim)
//    offsetY  przesunięcie początku stożka w dół od górnej krawędzi przeciwnika (px; "wysokość oczu")
//    alpha    przezroczystość rysowanego stożka, 0 = niewidoczny, 1 = pełny kolor
//    track    true = podczas pościgu stożek obraca się i celuje w gracza (także w górę i w dół, i za
//             plecy), więc pościg kończy się dopiero, gdy gracz jest poza długością stożka albo za ścianą.
//             false = stożek zawsze patrzy poziomo przed siebie (gracz może uciec kątem, np. skokiem).
//  Ściany zasłaniają widok: stożek jest przycinany przez solidne platformy.
//
//  SPADOCHRONIARZE I ŁOWCY (tryb poziomu "panel", patrz game.js)
//    Po alarmie na mapę spadają przeciwnicy na spadochronach (state "falling"): opadają ze stałą
//    prędkością PARATROOPER_FALL_SPEED, nie rażą, nie da się ich zakuć i nic nie widzą, dopóki nie wylądują.
//    Po wylądowaniu stają się zwykłymi aktywnymi przeciwnikami i od razu gonią gracza.
//    hunter: true  "łowca" zawsze wie, gdzie jest gracz (nie potrzebuje pola widzenia), dopóki nie wejdzie
//                  w chmurę dymu (oślepiony traci gracza z oczu jak każdy inny przeciwnik).
//
//  BOSS: KAMIL (boss, tryb poziomu "boss", patrz game.js)
//    Typ "boss" to łowca (hunter): zawsze wie, gdzie jest gracz, biegnie za nim nieco wolniej, niż biega
//    gracz, i nie da się go zakuć. NIE wybucha: żeby złapać gracza, musi go dotknąć (hitboxy muszą się
//    zetknąć, patrz updateBosses() w game.js), a złapany gracz przegrywa. Biega, skacze do ok. 3 tile tylko
//    po zablokowaniu przez przeszkodę, wall-jumpuje przy ścianie w szybie z dwóch ścian i schodzi z krawędzi.
//    Nie skacze do gracza na wyższym piętrze ani przez przerwy. Nie ma haka ani dasha, a ciasne przejścia (niższe niż
//    jego wysokość) są dla niego zamknięte.
//    Dym (klawisz F) go spowalnia (SMOKE_SLOW_FACTOR), ale nie zatrzymuje. Gdy utknie (prawie się nie
//    rusza przez BOSS_STUCK_TIME s), game.js przenosi go w jedno z miejsc `respawns`.
//    Opcje: wait (sekundy bezczynności na starcie), respawns [{ x, y, stage? }] (miejsca pojawiania się;
//    stage = przy ilu rozbrojonych panelach dany punkt jest używany, brak = zawsze).
//    Stara nazwa typu "kamikaze" nadal działa w plikach poziomów (jest aliasem "boss", patrz ENEMY_TYPE_ALIASES).
//
//  OBSZAR RUCHU (area) przy tworzeniu przeciwnika w levels.js:
//    enemy("weak", x, y, { area: { x1, y1, x2, y2 } })   dwa przeciwległe rogi prostokąta (w px poziomu)
//  Domyślnie obszarem jest platforma, na której przeciwnik stoi, więc nigdy z niej nie schodzi.
//  Żeby mógł zejść w pościgu, rozszerz prostokąt w dół (y2 = wysokość podłogi, na którą ma zejść).
//  Skacze wyłącznie po zablokowaniu przez osiągalną, solidną przeszkodę; nie wchodzi na wyższe platformy samym skokiem.
// ============================================================================

// Czasy zachowania (sekundy).
export const ALERT_TURN_DELAY = 0.5;  // po dotknięciu od tyłu: tyle czeka, zanim się odwróci
export const SEARCH_TIME = 2;         // tyle czeka na gracza, zanim się odwróci i wróci do patrolu
export const EXCLAIM_TIME = 1;        // jak długo widać "!" nad głową
export const PARATROOPER_FALL_SPEED = 36 * SCALE; // opadanie na spadochronie (px/s)

// Boss (Kamil): stałe ruchu.
const SMOKE_SLOW_FACTOR = 0.4;          // mnożnik prędkości bossa w dymie i tuż po nim
const SMOKE_SLOW_TIME = 2;              // jak długo po wyjściu z chmury nadal jest spowolniony (s)
const BOSS_WALL_JUMP_SPEED = 235 * SCALE;  // odbicie od ściany w górę (px/s)
const BOSS_WALL_KICK_SPEED = 120 * SCALE;  // odbicie od ściany w bok (px/s)
const BOSS_KICK_TIME = 0.3;         // tyle czasu leci w bok po odbiciu (s)
const BOSS_WALL_COOLDOWN = 1.0;     // odbicie od ściany z tej samej strony dopiero po tylu s (jak u gracza)
const BOSS_WALL_REACH = 30 * SCALE; // ściana bliżej niż tyle px zachęca do wspinania się
const BOSS_AIR_SPEED = 135 * SCALE; // pozioma prędkość bossa w powietrzu (px/s)
const BOSS_STUCK_TIME = 4.5;        // daj mu czas na próbę wspinania się po przeszkodzie
const BOSS_STUCK_DISTANCE = 20 * SCALE; // za utknięcie uznaj dopiero niemal całkowity brak postępu
const BOSS_LOST_HEIGHT = 125 * SCALE;   // różnica wysokości, od której boss uważa, że jest na innym piętrze niż gracz
const BOSS_LOST_TIME = 10;              // daj mu więcej czasu na dotarcie na piętro gracza ...
const BOSS_LOST_PROGRESS = 30 * SCALE;  // ... i wymagaj mniejszego postępu, by uznać, że się zgubił

// Stare nazwy typów, które nadal działają w plikach poziomów (po wczytaniu zamieniane na nową).
export const ENEMY_TYPE_ALIASES = Object.freeze({ kamikaze: "boss" });
export const normalizeEnemyType = (type) => ENEMY_TYPE_ALIASES[type] ?? type;

// Definicje typów. Add new enemy behavior by registering another type here and listing the
// methods that are allowed to cuff it.
export const ENEMY_TYPES = Object.freeze({
    weak: Object.freeze({
        label: "Słaby przeciwnik",
        width: 12 * SCALE,
        height: 20 * SCALE,
        speed: 24 * SCALE,          // prędkość patrolu (px/s)
        chaseMultiplier: 1.4,       // w pościgu: speed * chaseMultiplier
        jumpSpeed: 190 * SCALE,     // skok tylko po zablokowaniu przez przeszkodę, wysokość ok. 60 px
        cuffMethods: Object.freeze(["interact"]),
        cuffFromBackMethods: Object.freeze([]),
        armored: false,
        colors: Object.freeze({ body: "#c9823d", head: "#edb55f", visor: "#f2ead1", belt: "#5b382d", vision: "#ffe58a" }),
        vision: Object.freeze({ angle: 70, length: 100 * SCALE, offsetX: 3 * SCALE, offsetY: 5 * SCALE, alpha: 0.2, track: true }),
        attack: Object.freeze({ damage: 1 }),
    }),
    boss: Object.freeze({
        label: "Boss (Kamil)",
        width: 14 * SCALE,
        height: 24 * SCALE,
        speed: 56 * SCALE,          // patrol (nieużywany: łowca od razu goni)
        chaseMultiplier: 1.65,      // pościg: ok. 92 * SCALE px/s, gracz biega 96 * SCALE
        jumpSpeed: 235 * SCALE,     // skok tylko przez przeszkodę (ok. 92 px wysokości)
        hunter: true,
        cuffMethods: Object.freeze([]),
        cuffFromBackMethods: Object.freeze([]),
        armored: true,
        colors: Object.freeze({ body: "#8c2f2f", head: "#d9a066", visor: "#f2ead1", belt: "#2b2b30", vision: "#ff9a9a" }),
        vision: Object.freeze({ angle: 70, length: 100 * SCALE, offsetX: 3 * SCALE, offsetY: 5 * SCALE, alpha: 0, track: true }),
        attack: Object.freeze({ damage: 1 }),
    }),
    strong: Object.freeze({
        label: "Silny przeciwnik",
        width: 18 * SCALE,
        height: 26 * SCALE,
        speed: 18 * SCALE,
        chaseMultiplier: 1.4,
        jumpSpeed: 190 * SCALE,     // skok tylko po zablokowaniu przez przeszkodę, wysokość ok. 60 px
        cuffMethods: Object.freeze(["interact"]),
        cuffFromBackMethods: Object.freeze(["interact"]),
        armored: true,
        colors: Object.freeze({ body: "#713e59", head: "#c65366", visor: "#f2d9ab", belt: "#343343", vision: "#ffb3c1" }),
        vision: Object.freeze({ angle: 80, length: 120 * SCALE, offsetX: 4 * SCALE, offsetY: 6 * SCALE, alpha: 0.2, track: false }),
        attack: Object.freeze({ damage: 1 }),
    }),
});

// Level coordinates use the same anchor as the player and bombs: x is the center,
// y is the floor under the enemy's feet.
// Opcje: id, direction (1 / -1), speed, chaseSpeed, area { x1, y1, x2, y2 }, vision { angle, length, offsetX, offsetY, alpha, track },
// hunter (zawsze zna położenie gracza), paratrooper (przeciwnik z alarmu), state ("falling" = opada na spadochronie).
export function createEnemy(data, index = 0) {
    const type = normalizeEnemyType(data.type);
    const definition = ENEMY_TYPES[type];
    if (!definition) throw new Error(`Unknown enemy type: ${data.type}`);

    const speed = data.speed ?? definition.speed;
    const enemy = {
        id: data.id ?? `enemy-${index + 1}`,
        type,
        x: data.x - definition.width / 2,
        y: data.y - definition.height,
        w: definition.width,
        h: definition.height,
        state: data.state ?? "active",
        cuffedBy: null,
        rescueTarget: null,
        rescueProgress: 0,
        hunter: Boolean(data.hunter) || definition.hunter === true,
        paratrooper: Boolean(data.paratrooper),
        waitHome: data.wait ?? 0,    // sekundy bezczynności na starcie poziomu
        wait: data.wait ?? 0,        // ile jeszcze stoi bezczynnie
        respawns: data.respawns ?? null, // boss: miejsca pojawiania się po utknięciu [{ x, y, stage? }]
        respawnDistance: data.respawnDistance ?? null, // boss: min. odległość punktu od gracza (px), null = domyślna
        caught: false,               // boss: złapał gracza (animacja "grab")
        fuse: null,                  // (nieużywane: zostawione dla zgodności ze starymi zapisami)
        respawnIn: 0,                // boss: ile jeszcze do pojawienia się po utknięciu (state "gone")
        slowTime: 0,                 // boss: ile jeszcze jest spowolniony przez dym
        kickTime: 0,                 // boss: ile jeszcze leci w bok po odbiciu od ściany
        kickDir: 0,
        lastKickSide: 0,             // boss: strona ostatniego odbicia od ściany (-1 / 1)
        sinceKick: 99,               // boss: czas od ostatniego odbicia od ściany
        stuckClock: 0,               // boss: wykrywanie utknięcia
        lostClock: 0,                // boss: jak długo jest na innym piętrze niż gracz
        lostGap: 0,
        lostDistance: 0,
        stuckX: 0,
        stuckY: 0,
        stuck: false,                // boss: utknął (zeruje to game.js po przeniesieniu)
        jumpCooldown: 0,
        obstacleJumping: false,
        fallTime: 0,                 // jak długo opada na spadochronie (do kołysania spadochronu)
        direction: data.direction ?? 1,
        speed,
        chaseSpeed: data.chaseSpeed ?? speed * definition.chaseMultiplier,
        vision: { ...definition.vision, ...(data.vision ?? {}) },
        areaData: data.area ?? null, // podany ręcznie prostokąt; null = platforma, na której stoi
        area: null,                  // ustawiany przez initEnemyArea()
        vy: 0,
        onGround: false,
        blocked: false,
        hitWall: false,
        blockingObstacle: null,
        blockingDirection: 0,
        support: null,               // platforma, na której przeciwnik stoi
        exclaim: 0,                  // ile jeszcze widać "!"
        aim: null,                   // kierunek stożka w radianach podczas pościgu (vision.track), poza nim null
        blind: false,                // true, gdy stoi w chmurze dymu (nic nie widzi); ustawia updateEnemy()
        ai: { mode: "patrol", timer: 0, lastSeenX: null, sees: false },
    };
    enemy.homeX = enemy.x;
    enemy.homeY = enemy.y;
    enemy.homeDirection = enemy.direction;
    enemy.facing = enemy.direction;
    return enemy;
}

// Ustawia prostokąt ruchu: podany w levels.js albo (domyślnie) cała platforma pod stopami.
export function initEnemyArea(enemy, platforms) {
    if (enemy.areaData) {
        const { x1, y1, x2, y2 } = enemy.areaData;
        enemy.area = { x1: Math.min(x1, x2), y1: Math.min(y1, y2), x2: Math.max(x1, x2), y2: Math.max(y1, y2) };
        enemy.patrolArea = { ...enemy.area };
        return;
    }
    const feet = enemy.homeY + enemy.h;
    const cx = enemy.homeX + enemy.w / 2;
    const floor = platforms.find((p) => p.solid !== false
        && Math.abs(p.y - feet) <= 1 && cx >= p.x && cx <= p.x + p.w);
    if (floor) {
        enemy.area = { x1: floor.x, y1: feet - 200 * SCALE, x2: floor.x + floor.w, y2: floor.y };
    } else {
        // Brak platformy pod stopami: wąski pas wokół miejsca startu.
        enemy.area = { x1: cx - 24 * SCALE, y1: feet - 200 * SCALE, x2: cx + 24 * SCALE, y2: feet };
    }
    enemy.patrolArea = { ...enemy.area };
}

export function canCuff(enemy, method, context = {}) {
    const definition = ENEMY_TYPES[enemy.type];
    if (enemy.state !== "active" || !definition?.cuffMethods.includes(method)) return false;
    if (definition.cuffFromBackMethods?.includes(method) && context.fromBehind !== true) return false;
    return true;
}

export function cuffEnemy(enemy, method, context = {}) {
    if (!canCuff(enemy, method, context)) return false;
    enemy.state = "cuffed";
    enemy.cuffedBy = method;
    enemy.exclaim = 0;
    enemy.rescueTarget = null;
    enemy.rescueProgress = 0;
    return true;
}

export function uncuffEnemy(enemy) {
    if (enemy.state !== "cuffed") return false;
    enemy.state = "active";
    enemy.cuffedBy = null;
    enemy.rescueTarget = null;
    enemy.rescueProgress = 0;
    enemy.wait = 0;
    enemy.ai = { mode: "patrol", timer: 0, lastSeenX: null, sees: false };
    enemy.exclaim = 0;
    enemy.aim = null;
    return true;
}

export function resetEnemy(enemy) {
    enemy.x = enemy.homeX;
    enemy.y = enemy.homeY;
    enemy.vy = 0;
    enemy.onGround = false;
    enemy.blocked = false;
    enemy.hitWall = false;
    enemy.blockingObstacle = null;
    enemy.blockingDirection = 0;
    enemy.support = null;
    enemy.state = "active";
    enemy.cuffedBy = null;
    enemy.rescueTarget = null;
    enemy.rescueProgress = 0;
    enemy.wait = enemy.waitHome;
    enemy.fuse = null;
    enemy.caught = false;
    enemy.respawnIn = 0;
    enemy.jumpCooldown = 0;
    enemy.obstacleJumping = false;
    enemy.slowTime = 0;
    enemy.kickTime = 0;
    enemy.lastKickSide = 0;
    enemy.sinceKick = 99;
    enemy.stuckClock = 0;
    enemy.lostClock = 0;
    enemy.lostGap = 0;
    enemy.lostDistance = 0;
    enemy.stuck = false;
    enemy.direction = enemy.homeDirection;
    enemy.facing = enemy.homeDirection;
    enemy.exclaim = 0;
    enemy.aim = null;
    enemy.blind = false;
    enemy.ai = { mode: "patrol", timer: 0, lastSeenX: null, sees: false };
}

// Przeciwnik traci gracza z oczu i wraca do patrolu (np. gdy gracz wraca do checkpointu).
export function calmEnemy(enemy) {
    if (enemy.state !== "active") return;
    enemy.ai = { mode: "patrol", timer: 0, lastSeenX: null, sees: false };
    enemy.direction = enemy.facing;
    enemy.exclaim = 0;
    enemy.aim = null;
}

// ---------------------------------------------------------------------------
// Geometria: pole widzenia
// ---------------------------------------------------------------------------

const blocksSight = (p) => p.solid !== false && !p.oneWay;

// Odległość (w jednostkach długości promienia) od (ox, oy) w kierunku (dx, dy) (wektor jednostkowy)
// do pierwszej solidnej platformy, ale nie więcej niż maxLength.
function rayDistance(platforms, ox, oy, dx, dy, maxLength) {
    let best = maxLength;
    for (const p of platforms) {
        if (!blocksSight(p)) continue;
        let tMin = 0;
        let tMax = best;
        let hit = true;
        for (const [origin, delta, min, max] of [[ox, dx, p.x, p.x + p.w], [oy, dy, p.y, p.y + p.h]]) {
            if (Math.abs(delta) < 1e-9) {
                if (origin < min || origin > max) { hit = false; break; }
                continue;
            }
            let near = (min - origin) / delta;
            let far = (max - origin) / delta;
            if (near > far) [near, far] = [far, near];
            tMin = Math.max(tMin, near);
            tMax = Math.min(tMax, far);
            if (tMin > tMax) { hit = false; break; }
        }
        if (hit && tMin < best) best = tMin;
    }
    return best;
}

// Początek stożka (oczy): przesunięty do przodu od środka i w dół od góry przeciwnika.
export function visionOrigin(enemy) {
    return {
        x: enemy.x + enemy.w / 2 + enemy.facing * enemy.vision.offsetX,
        y: enemy.y + enemy.vision.offsetY,
    };
}

// Kierunek środka stożka (radiany): do przodu poziomo albo, w pościgu przeciwnika ze śledzeniem, na gracza.
function visionBase(enemy) {
    return enemy.aim ?? (enemy.facing > 0 ? 0 : Math.PI);
}

// Czy przeciwnik widzi prostokąt `target` (hitbox gracza): któryś z 3 punktów (głowa, środek, nogi)
// musi być w stożku (kąt i długość) i nie może być zasłonięty przez ścianę.
export function canEnemySee(enemy, target, platforms) {
    if (enemy.state !== "active" || enemy.blind) return false; // oślepiony dymem nic nie widzi
    const { angle, length } = enemy.vision;
    const origin = visionOrigin(enemy);
    const half = (angle / 2) * Math.PI / 180;
    const base = visionBase(enemy);
    const cx = target.x + target.w / 2;
    for (const fraction of [0.2, 0.5, 0.8]) {
        const dx = cx - origin.x;
        const dy = target.y + target.h * fraction - origin.y;
        const distance = Math.hypot(dx, dy);
        if (distance > length) continue;
        if (distance > 0.001) {
            const cosine = (dx * Math.cos(base) + dy * Math.sin(base)) / distance;
            if (Math.acos(Math.max(-1, Math.min(1, cosine))) > half) continue;
            if (rayDistance(platforms, origin.x, origin.y, dx / distance, dy / distance, distance) < distance - 0.5) continue;
        }
        return true;
    }
    return false;
}

// Czy przeciwnik jest w chmurze dymu: jakakolwiek część jego ciała leży w promieniu chmury.
// Dym przenika przez ściany (chmura "przykleja się" do ściany, w którą trafił pocisk, więc wróg
// stojący tuż za nią też jest objęty). smokes = [{ x, y, r }].
export function isBlinded(enemy, smokes) {
    if (enemy.state !== "active") return false;
    return isInsideSmoke(enemy, smokes);
}

// Any entity whose hitbox intersects smoke is concealed by it.
export function isInsideSmoke(entity, smokes) {
    return smokes.some((smoke) => {
        const nearestX = Math.max(entity.x, Math.min(smoke.x, entity.x + entity.w));
        const nearestY = Math.max(entity.y, Math.min(smoke.y, entity.y + entity.h));
        return Math.hypot(nearestX - smoke.x, nearestY - smoke.y) <= smoke.r;
    });
}

// Wielokąt stożka widzenia przycięty przez ściany (do rysowania): lista punktów { x, y }.
export function visionPolygon(enemy, platforms, steps = 24) {
    const { angle, length } = enemy.vision;
    const origin = visionOrigin(enemy);
    const half = (angle / 2) * Math.PI / 180;
    const base = visionBase(enemy);
    const points = [{ x: origin.x, y: origin.y }];
    for (let i = 0; i <= steps; i++) {
        const a = base - half + (2 * half * i) / steps;
        const dx = Math.cos(a);
        const dy = Math.sin(a);
        const d = rayDistance(platforms, origin.x, origin.y, dx, dy, length);
        points.push({ x: origin.x + dx * d, y: origin.y + dy * d });
    }
    return points;
}

// ---------------------------------------------------------------------------
// Aktualizacja: decyzje (AI) i fizyka
// ---------------------------------------------------------------------------

const overlaps = (a, b) => a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;

// Najwyższa powierzchnia pod stopami na pozycji x (środek), nie wyżej niż `feet` (z tolerancją 1 px)
// i nie niżej niż feet + maxDrop. Zwraca platformę albo null.
function floorUnder(platforms, x, feet, maxDrop) {
    let best = null;
    for (const p of platforms) {
        if (p.solid === false) continue;
        if (x < p.x || x > p.x + p.w) continue;
        if (p.y < feet - 1 || p.y > feet + maxDrop) continue;
        if (!best || p.y < best.y) best = p;
    }
    return best;
}

// Jump only after a solid obstacle blocks the enemy, and only if the jump can clear it.
// A platform edge or patrol boundary does not set blockingObstacle, so it never causes a jump.
function canJumpOverObstacle(enemy, world, direction = enemy.blockingDirection) {
    const obstacle = enemy.blockingObstacle;
    const jumpSpeed = ENEMY_TYPES[enemy.type]?.jumpSpeed;
    if (!obstacle || !jumpSpeed || direction === 0 || direction !== enemy.blockingDirection) return false;

    const obstacleHeight = enemy.y + enemy.h - obstacle.y;
    const jumpHeight = (jumpSpeed * jumpSpeed) / (2 * world.gravity);
    return obstacleHeight > 0 && obstacleHeight <= jumpHeight + 2 * SCALE;
}

// Kierunek i prędkość, jakie przeciwnik chce mieć w tej klatce (nie rusza się sam: robi to physics()).
function think(enemy, world, dt) {
    const { platforms, player } = world;
    const ai = enemy.ai;
    const ex = enemy.x + enemy.w / 2;
    const px = player.x + player.w / 2;
    // Śledzenie: w pościgu stożek celuje w środek gracza, więc o utracie gracza decyduje tylko
    // odległość (długość stożka) i ściany, a nie kąt.
    if (enemy.vision.track && ai.mode === "chase") {
        const origin = visionOrigin(enemy);
        enemy.aim = Math.atan2(player.y + player.h / 2 - origin.y, px - origin.x);
    } else {
        enemy.aim = null;
    }
    // Łowca zna położenie gracza bez pola widzenia (chyba że jest oślepiony dymem).
    const sees = !world.playerHidden && ((enemy.hunter && !enemy.blind) || canEnemySee(enemy, player, platforms));
    ai.sees = sees;

    const startChase = () => {
        // "!" tylko przy pierwszym zauważeniu (z patrolu albo po odwróceniu się), a nie gdy gracz
        // na chwilę znika i pojawia się na granicy pola widzenia podczas pościgu.
        const firstSight = ai.mode === "patrol" || (ai.mode === "search" && ai.lastSeenX === null);
        if (firstSight) enemy.exclaim = EXCLAIM_TIME;
        ai.mode = "chase";
        ai.timer = SEARCH_TIME;
    };

    // Dotknięcie od tyłu (tylko w patrolu albo gdy stoi i czeka).
    const touchedFromBehind = !world.playerHidden && overlaps(enemy, player) && (px - ex) * enemy.facing < 0;
    if (touchedFromBehind && (ai.mode === "patrol" || (ai.mode === "search" && ai.lastSeenX === null))) {
        ai.mode = "alert";
        ai.timer = ALERT_TURN_DELAY;
        enemy.exclaim = EXCLAIM_TIME;
    }

    switch (ai.mode) {
        case "alert": {
            ai.timer -= dt;
            if (ai.timer <= 0) {
                enemy.facing = -enemy.facing;
                enemy.direction = enemy.facing;
                ai.mode = "search";
                ai.timer = SEARCH_TIME;
                ai.lastSeenX = null;
            }
            return { move: 0, speed: 0, allowDrop: false };
        }
        case "patrol": {
            if (sees) {
                startChase();
                ai.lastSeenX = px;
                break;
            }
            // Patrol po całej platformie pod stopami (w granicach prostokąta).
            const support = enemy.support;
            let lo = enemy.area.x1 + enemy.w / 2;
            let hi = enemy.area.x2 - enemy.w / 2;
            if (support) {
                lo = Math.max(lo, support.x + enemy.w / 2);
                hi = Math.min(hi, support.x + support.w - enemy.w / 2);
            }
            if (lo > hi) lo = hi = (lo + hi) / 2;
            if (!enemy.onGround) {
                return enemy.obstacleJumping
                    ? { move: enemy.direction, speed: enemy.speed, allowDrop: false, lo, hi }
                    : { move: 0, speed: 0, allowDrop: false };
            }
            if (ex <= lo + 0.01) enemy.direction = 1;
            else if (ex >= hi - 0.01) enemy.direction = -1;
            if (enemy.hitWall && !canJumpOverObstacle(enemy, world)) enemy.direction = -enemy.direction; // zawraca na przeszkodzie, której nie może przeskoczyć, albo na krawędzi
            enemy.facing = enemy.direction;
            return { move: enemy.direction, speed: enemy.speed, allowDrop: false, lo, hi };
        }
        case "search": {
            if (sees) {
                startChase();
                ai.lastSeenX = px;
                break;
            }
            ai.timer -= dt;
            if (ai.timer <= 0) {
                enemy.facing = -enemy.facing; // odwraca się i wraca do patrolu
                enemy.direction = enemy.facing;
                ai.mode = "patrol";
                ai.lastSeenX = null;
                return { move: 0, speed: 0, allowDrop: false };
            }
            if (ai.lastSeenX !== null && Math.abs(ai.lastSeenX - ex) > 2) {
                const move = Math.sign(ai.lastSeenX - ex);
                if (enemy.blocked && !canJumpOverObstacle(enemy, world, move)) {
                    return { move: 0, speed: 0, allowDrop: false };
                }
                enemy.facing = move;
                enemy.direction = move;
                return { move, speed: enemy.chaseSpeed, allowDrop: true };
            }
            return { move: 0, speed: 0, allowDrop: false };
        }
        case "return": {
            if (sees) {
                startChase();
                ai.lastSeenX = px;
                break;
            }
            const patrolArea = enemy.patrolArea ?? enemy.area;
            const lo = patrolArea.x1 + enemy.w / 2;
            const hi = patrolArea.x2 - enemy.w / 2;
            const insideArea = ex >= lo && ex <= hi
                && enemy.y >= patrolArea.y1 && enemy.y + enemy.h <= patrolArea.y2;
            if (insideArea) {
                ai.mode = "patrol";
                return { move: 0, speed: 0, allowDrop: false };
            }
            const homeCenterX = enemy.homeX + enemy.w / 2;
            const targetX = Math.max(lo, Math.min(hi, homeCenterX));
            const move = Math.abs(targetX - ex) > 2 ? Math.sign(targetX - ex) : 0;
            if (move !== 0) enemy.facing = enemy.direction = move;
            return { move, speed: enemy.speed, allowDrop: true };
        }
        default:
            break;
    }

    if (ai.mode === "chase") {
        if (sees) {
            ai.lastSeenX = px;
            ai.timer = SEARCH_TIME;
        } else {
            ai.mode = "search";
            ai.timer = SEARCH_TIME;
            enemy.aim = null;
        }
        const dx = (ai.lastSeenX ?? px) - ex;
        if (Math.abs(dx) <= 2) return { move: 0, speed: 0, allowDrop: false };
        const move = Math.sign(dx);
        enemy.facing = move;
        enemy.direction = move;
        return { move, speed: enemy.chaseSpeed, allowDrop: true };
    }
    return { move: 0, speed: 0, allowDrop: false };
}

// Ruch poziomy (ściany, krawędzie, prostokąt ruchu) i pionowy (grawitacja, lądowanie).
function physics(enemy, command, world, dt) {
    const { platforms, gravity, maxFall } = world;
    const { area } = enemy;
    enemy.blocked = false;  // coś zatrzymało ruch (ściana, krawędź albo granica prostokąta)
    enemy.hitWall = false;  // tylko ściana albo krawędź (granicę prostokąta w patrolu obsługuje zawracanie)
    enemy.blockingObstacle = null;
    enemy.blockingDirection = 0;

    if (command.move !== 0) {
        const step = command.move * command.speed * dt;
        let x = enemy.x + step;
        const clamped = Math.max(area.x1, Math.min(area.x2 - enemy.w, x));
        if (clamped !== x) enemy.blocked = true;
        x = clamped;
        if (command.lo !== undefined) { // patrol: zostaje w granicach platformy
            x = Math.max(command.lo - enemy.w / 2, Math.min(command.hi - enemy.w / 2, x));
        }

        // Ściana na drodze.
        const probe = { x, y: enemy.y, w: enemy.w, h: enemy.h };
        for (const p of platforms) {
            if (p.solid === false || p.oneWay || !overlaps(probe, p)) continue;
            x = command.move > 0 ? p.x - enemy.w : p.x + p.w;
            probe.x = x;
            enemy.blocked = true;
            enemy.hitWall = true;
            enemy.blockingObstacle = p;
            enemy.blockingDirection = command.move;
        }

        // Krawędź: na ziemi idzie dalej tylko tam, gdzie pod stopami jest podłoga
        // (w pościgu może być niżej, byle w prostokącie ruchu).
        if (enemy.onGround) {
            const feet = enemy.y + enemy.h;
            const maxDrop = command.allowDrop ? Math.max(0, area.y2 - feet) : 0;
            if (!floorUnder(platforms, x + enemy.w / 2, feet, maxDrop)) {
                x = enemy.x;
                enemy.blocked = true;
                enemy.hitWall = true;
            }
        }
        enemy.x = x;
    }

    // Pion: grawitacja i lądowanie.
    const previousBottom = enemy.y + enemy.h;
    enemy.vy = Math.min(enemy.vy + gravity * dt, maxFall);
    enemy.y += enemy.vy * dt;
    enemy.onGround = false;
    enemy.support = null;
    for (const p of platforms) {
        if (p.solid === false || !overlaps(enemy, p)) continue;
        if (p.oneWay) {
            if (enemy.vy <= 0 || previousBottom > p.y + 1) continue;
            enemy.y = p.y - enemy.h;
            enemy.vy = 0;
            enemy.onGround = true;
            enemy.support = p;
            continue;
        }
        if (enemy.vy > 0) {
            enemy.y = p.y - enemy.h;
            enemy.onGround = true;
            enemy.support = p;
        } else if (enemy.vy < 0) {
            enemy.y = p.y + p.h;
        }
        enemy.vy = 0;
    }
    // Dolna granica prostokąta ruchu jest "podłogą": przeciwnik nigdy nie wypada poza obszar.
    if (enemy.y + enemy.h > area.y2) {
        enemy.y = area.y2 - enemy.h;
        enemy.vy = 0;
        enemy.onGround = true;
    }
    if (enemy.onGround) enemy.obstacleJumping = false;
}

// Spadochroniarz wylądował: staje się aktywnym przeciwnikiem i biegnie w stronę gracza.
function landParatrooper(enemy, world) {
    const px = world.player.x + world.player.w / 2;
    enemy.state = "active";
    enemy.facing = px >= enemy.x + enemy.w / 2 ? 1 : -1;
    enemy.direction = enemy.facing;
    enemy.ai = { mode: "chase", timer: SEARCH_TIME, lastSeenX: px, sees: false };
    enemy.exclaim = 0;
}

// Ściana przy ciele bossa po stronie dir (-1 lewo, 1 prawo): platforma sięgająca przy nim na co najmniej
// 18 * SCALE px (cienka półka nie jest ścianą, tak samo jak u gracza). reach = jak daleko szukamy.
function bossWall(enemy, platforms, dir, reach = 1) {
    const probe = { x: dir < 0 ? enemy.x - reach : enemy.x + enemy.w, y: enemy.y, w: reach, h: enemy.h };
    for (const p of platforms) {
        if (p.solid === false || p.oneWay || !overlaps(probe, p)) continue;
        const top = Math.max(probe.y, p.y);
        const bottom = Math.min(probe.y + probe.h, p.y + p.h);
        if (bottom - top >= 18 * SCALE) return true;
    }
    return false;
}

// Jedna klatka bossa: bieg, skok tylko przez przeszkodę oraz wall-jump przy kontakcie ze ścianą.
function updateBoss(enemy, world, dt) {
    const def = ENEMY_TYPES.boss;
    const { platforms, player } = world;
    const ex = enemy.x + enemy.w / 2;
    const ey = enemy.y + enemy.h / 2;
    const px = player.x + player.w / 2;
    const py = player.y + player.h / 2;
    const dx = px - ex;
    const feet = enemy.y + enemy.h;

    enemy.ai = { mode: "chase", timer: SEARCH_TIME, lastSeenX: px, sees: true };
    enemy.slowTime = enemy.blind ? SMOKE_SLOW_TIME : Math.max(0, enemy.slowTime - dt);
    const slow = enemy.slowTime > 0 ? SMOKE_SLOW_FACTOR : 1;
    const runSpeed = enemy.chaseSpeed * slow;
    enemy.sinceKick += dt;
    enemy.kickTime = Math.max(0, enemy.kickTime - dt);
    const canKick = (side) => side !== enemy.lastKickSide || enemy.sinceKick >= BOSS_WALL_COOLDOWN;

    // Wykrywanie utknięcia: prawie bez ruchu przez BOSS_STUCK_TIME s.
    if (enemy.stuckClock === 0) { enemy.stuckX = ex; enemy.stuckY = ey; }
    enemy.stuckClock += dt;
    if (enemy.stuckClock >= BOSS_STUCK_TIME) {
        if (Math.hypot(ex - enemy.stuckX, ey - enemy.stuckY) < BOSS_STUCK_DISTANCE) enemy.stuck = true;
        enemy.stuckClock = 0;
    }

    // Zgubiony trop: długo na innym piętrze niż gracz. Postęp liczy się także w poziomie,
    // żeby Kamil nie był przenoszony, gdy biegnie do przejścia albo wspina się po ścianie.
    const heightGap = Math.abs(py - ey);
    const playerDistance = Math.hypot(dx, py - ey);
    if (heightGap <= BOSS_LOST_HEIGHT) {
        enemy.lostClock = 0;
    } else {
        if (enemy.lostClock === 0) {
            enemy.lostGap = heightGap;
            enemy.lostDistance = playerDistance;
        }
        enemy.lostClock += dt;
        if (enemy.lostClock >= BOSS_LOST_TIME) {
            const heightProgress = heightGap <= enemy.lostGap - BOSS_LOST_PROGRESS;
            const distanceProgress = playerDistance <= enemy.lostDistance - BOSS_LOST_PROGRESS;
            if (!heightProgress && !distanceProgress) enemy.stuck = true;
            enemy.lostClock = 0;
        }
    }

    const wantDir = Math.abs(dx) > 4 ? Math.sign(dx) : 0;
    const needUp = player.y + player.h < feet - 6 * SCALE; // stopy gracza wyżej niż stopy bossa: trzeba się wspiąć
    let command = { move: wantDir, speed: runSpeed, allowDrop: true };

    if (enemy.onGround) {
        // Przerwa w podłodze ani sama pozycja gracza nie wywołują skoku.
        if (enemy.jumpCooldown <= 0 && canJumpOverObstacle(enemy, world, wantDir)) {
            enemy.vy = -def.jumpSpeed;
            enemy.onGround = false;
            enemy.jumpCooldown = 0.6;
            enemy.obstacleJumping = true;
        } else if (enemy.jumpCooldown <= 0 && enemy.hitWall && enemy.blockingObstacle
            && wantDir === enemy.blockingDirection && canKick(enemy.blockingDirection)
            && bossWall(enemy, platforms, enemy.blockingDirection, 2)) {
            // Jeśli przeszkoda jest za wysoka na zwykły skok, odbij się od niej nawet wtedy,
            // gdy gracz jest na tym samym piętrze. Po wyjściu nad przeszkodę wróć do pościgu.
            enemy.vy = -BOSS_WALL_JUMP_SPEED;
            enemy.onGround = false;
            enemy.obstacleJumping = true;
            enemy.kickDir = -enemy.blockingDirection;
            enemy.kickTime = BOSS_KICK_TIME;
            enemy.lastKickSide = enemy.blockingDirection;
            enemy.sinceKick = 0;
        }
    }

    if (!enemy.onGround) command.speed = Math.max(command.speed, BOSS_AIR_SPEED * slow); // w powietrzu sunie szybciej
    if (!enemy.onGround) {
        // W powietrzu wspina się, gdy gracz jest wyżej albo gdy właśnie próbuje obejść wysoką ścianę.
        const shouldClimb = needUp || enemy.obstacleJumping;
        const sides = [-1, 1];
        const touching = sides.find((side) => bossWall(enemy, platforms, side, 2));
        if (enemy.kickTime > 0) {
            command = { move: enemy.kickDir, speed: BOSS_WALL_KICK_SPEED * slow, allowDrop: true };
        } else if (shouldClimb && touching !== undefined && canKick(touching) && enemy.vy > -120 * SCALE) {
            enemy.vy = -BOSS_WALL_JUMP_SPEED;
            enemy.kickDir = -touching;
            enemy.kickTime = BOSS_KICK_TIME;
            enemy.lastKickSide = touching;
            enemy.sinceKick = 0;
            command = { move: enemy.kickDir, speed: BOSS_WALL_KICK_SPEED * slow, allowDrop: true };
        } else if (shouldClimb) {
            // Szuka ściany do odbicia: najpierw tej bliżej gracza, potem drugiej (jeśli wolno się od niej odbić).
            const order = wantDir >= 0 ? [1, -1] : [-1, 1];
            const side = order.find((s) => canKick(s) && bossWall(enemy, platforms, s, BOSS_WALL_REACH));
            if (side !== undefined) command = { move: side, speed: runSpeed, allowDrop: true };
        }
    }

    enemy.facing = command.move !== 0 ? command.move : enemy.facing;
    enemy.direction = enemy.facing;
    physics(enemy, command, world, dt);
}

function syncEnemyArea(enemy, world) {
    const patrolArea = enemy.patrolArea ?? enemy.area;
    if (!patrolArea) return;
    const pursuitModes = ["chase", "search", "rescue", "return"];
    if (enemy.state === "active" && !pursuitModes.includes(enemy.ai.mode)) {
        const centerX = enemy.x + enemy.w / 2;
        const insideArea = centerX >= patrolArea.x1 + enemy.w / 2
            && centerX <= patrolArea.x2 - enemy.w / 2
            && enemy.y >= patrolArea.y1 && enemy.y + enemy.h <= patrolArea.y2;
        if (!insideArea) enemy.ai.mode = "return";
    }
    enemy.area = pursuitModes.includes(enemy.ai.mode) && world.bounds
        ? { ...world.bounds }
        : { ...patrolArea };
}

// Jedna klatka przeciwnika. world = { platforms, player, gravity, maxFall, smokes }.
export function updateEnemy(enemy, world, dt) {
    if (!enemy.area) initEnemyArea(enemy, world.platforms);
    syncEnemyArea(enemy, world);

    if (enemy.state === "falling") {
        // Opada ze stałą prędkością (bez grawitacji), aż stanie na platformie albo na dole poziomu.
        enemy.fallTime += dt;
        enemy.blind = false;
        enemy.vy = PARATROOPER_FALL_SPEED;
        physics(enemy, { move: 0, speed: 0, allowDrop: false },
            { ...world, gravity: 0, maxFall: PARATROOPER_FALL_SPEED }, dt);
        if (enemy.onGround) landParatrooper(enemy, world);
        return;
    }

    if (enemy.state === "gone") return; // boss, który utknął: czeka na pojawienie się w innym miejscu (game.js)

    enemy.blind = world.smokes ? isBlinded(enemy, world.smokes) : false;
    enemy.exclaim = Math.max(0, enemy.exclaim - dt);
    enemy.jumpCooldown = Math.max(0, enemy.jumpCooldown - dt);

    // Enemies that spot a cuffed ally leave their current behavior to free him.
    if (enemy.state === "active") {
        const playerHasPriority = !world.playerHidden
            && ((enemy.hunter && !enemy.blind) || canEnemySee(enemy, world.player, world.platforms));
        const pursuingPlayer = playerHasPriority || ["chase", "search", "alert"].includes(enemy.ai.mode);
        if (pursuingPlayer) {
            enemy.rescueTarget = null;
            enemy.rescueProgress = 0;
            if (enemy.ai.mode === "rescue") {
                enemy.ai = { mode: "patrol", timer: 0, lastSeenX: null, sees: false };
            }
        } else {
            const visibleCuffed = !enemy.blind && (world.cuffedEnemies ?? [])
                .find((target) => target !== enemy && target.state === "cuffed"
                    && canEnemySee(enemy, target, world.platforms));
            if (visibleCuffed && visibleCuffed !== enemy.rescueTarget) {
                enemy.rescueTarget = visibleCuffed;
                enemy.rescueProgress = 0;
            }
        }

        const target = enemy.rescueTarget;
        if (target?.state === "cuffed") {
            const dx = target.x + target.w / 2 - (enemy.x + enemy.w / 2);
            const dy = target.y + target.h / 2 - (enemy.y + enemy.h / 2);
            if (Math.hypot(dx, dy) <= 20 * SCALE) {
                enemy.ai.mode = "rescue";
                enemy.ai.sees = false;
                enemy.rescueProgress += dt;
                if (enemy.rescueProgress >= 1) {
                    uncuffEnemy(target);
                    enemy.rescueTarget = null;
                    enemy.rescueProgress = 0;
                    enemy.ai = { mode: "patrol", timer: 0, lastSeenX: null, sees: false };
                }
                syncEnemyArea(enemy, world);
                physics(enemy, { move: 0, speed: 0, allowDrop: false }, world, dt);
                return;
            } else {
                enemy.rescueProgress = 0;
                const move = Math.sign(dx);
                enemy.ai.mode = "rescue";
                enemy.ai.sees = false;
                if (move !== 0) {
                    enemy.facing = move;
                    enemy.direction = move;
                }
                const jumpSpeed = ENEMY_TYPES[enemy.type].jumpSpeed;
                if (jumpSpeed && enemy.onGround && enemy.jumpCooldown <= 0
                    && canJumpOverObstacle(enemy, world, move)) {
                    enemy.vy = -jumpSpeed;
                    enemy.onGround = false;
                    enemy.jumpCooldown = 0.6;
                    enemy.obstacleJumping = true;
                }
                syncEnemyArea(enemy, world);
                physics(enemy, { move, speed: enemy.chaseSpeed, allowDrop: true }, world, dt);
                return;
            }
        } else {
            enemy.rescueTarget = null;
            enemy.rescueProgress = 0;
            if (enemy.ai.mode === "rescue") {
                enemy.ai = { mode: "patrol", timer: 0, lastSeenX: null, sees: false };
                syncEnemyArea(enemy, world);
            }
        }
    }

    let waiting = false;
    if (enemy.wait > 0) { // bezczynność na starcie (np. boss "budzi się" po kilku sekundach)
        enemy.wait = Math.max(0, enemy.wait - dt);
        waiting = true;
    }
    if (enemy.type === "boss" && enemy.state === "active" && !waiting) {
        if (world.playerHidden) {
            physics(enemy, { move: 0, speed: 0, allowDrop: false }, world, dt);
        } else {
            updateBoss(enemy, world, dt);
        }
        return;
    }
    const command = enemy.state === "active" && !waiting
        ? think(enemy, world, dt)
        : { move: 0, speed: 0, allowDrop: false }; // zakuty albo czekający: tylko grawitacja
    syncEnemyArea(enemy, world);

    // Patrol, pościg i powrót skaczą tylko wtedy, gdy fizyka zgłosiła osiągalną przeszkodę przed nimi.
    const jumpSpeed = ENEMY_TYPES[enemy.type].jumpSpeed;
    if (jumpSpeed && enemy.state === "active" && !waiting && enemy.onGround && enemy.jumpCooldown <= 0
        && command.move !== 0 && canJumpOverObstacle(enemy, world, command.move)) {
        enemy.vy = -jumpSpeed;
        enemy.onGround = false;
        enemy.jumpCooldown = 0.6;
        enemy.obstacleJumping = true;
    }
    physics(enemy, command, world, dt);
}
