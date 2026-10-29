// Retro sound effects and level music are synthesized with Web Audio; no audio assets are needed.
const STORAGE_KEY = "projekt-konkursowy-sound-enabled";

function readEnabled() {
    try {
        return window.localStorage.getItem(STORAGE_KEY) !== "false";
    } catch {
        return true;
    }
}

const effects = {
    click: [{ frequency: 520, endFrequency: 660, duration: 0.045, wave: "square", volume: 0.16 }],
    toggle: [
        { frequency: 520, endFrequency: 740, duration: 0.09, wave: "triangle", volume: 0.2 },
        { frequency: 740, endFrequency: 920, duration: 0.1, delay: 0.07, wave: "triangle", volume: 0.16 },
    ],
    jump: [{ frequency: 250, endFrequency: 470, duration: 0.14, wave: "triangle", volume: 0.25 }],
    jumpPad: [
        { frequency: 190, endFrequency: 620, duration: 0.2, wave: "sine", volume: 0.24 },
        { frequency: 420, endFrequency: 780, duration: 0.16, delay: 0.035, wave: "triangle", volume: 0.15 },
    ],
    dash: [{ frequency: 210, endFrequency: 90, duration: 0.16, wave: "sawtooth", volume: 0.2 }],
    grapple: [
        { frequency: 420, endFrequency: 700, duration: 0.12, wave: "triangle", volume: 0.2 },
        { frequency: 700, endFrequency: 560, duration: 0.1, delay: 0.08, wave: "sine", volume: 0.15 },
    ],
    release: [{ frequency: 600, endFrequency: 280, duration: 0.12, wave: "triangle", volume: 0.16 }],
    cuff: [
        { frequency: 920, endFrequency: 540, duration: 0.11, wave: "square", volume: 0.14 },
        { frequency: 1380, endFrequency: 820, duration: 0.08, delay: 0.025, wave: "sine", volume: 0.13 },
    ],
    damage: [
        { frequency: 190, endFrequency: 72, duration: 0.22, wave: "sawtooth", volume: 0.24 },
        { frequency: 130, endFrequency: 82, duration: 0.18, delay: 0.03, wave: "square", volume: 0.11 },
    ],
    smoke: [
        { frequency: 360, endFrequency: 170, duration: 0.19, wave: "triangle", volume: 0.17 },
        { frequency: 120, endFrequency: 75, duration: 0.22, delay: 0.03, wave: "sine", volume: 0.14 },
    ],
    bombOpen: [{ frequency: 520, endFrequency: 390, duration: 0.16, wave: "sine", volume: 0.18 }],
    defuse: [
        { frequency: 520, duration: 0.11, wave: "triangle", volume: 0.18 },
        { frequency: 660, duration: 0.12, delay: 0.09, wave: "triangle", volume: 0.2 },
        { frequency: 880, duration: 0.2, delay: 0.18, wave: "triangle", volume: 0.2 },
    ],
    wrong: [
        { frequency: 210, endFrequency: 150, duration: 0.18, wave: "square", volume: 0.18 },
        { frequency: 155, endFrequency: 110, duration: 0.2, delay: 0.08, wave: "square", volume: 0.15 },
    ],
    alarm: [
        { frequency: 620, endFrequency: 880, duration: 0.14, wave: "square", volume: 0.15 },
        { frequency: 880, endFrequency: 620, duration: 0.14, delay: 0.15, wave: "square", volume: 0.15 },
    ],
    win: [
        { frequency: 523, duration: 0.14, wave: "triangle", volume: 0.18 },
        { frequency: 659, duration: 0.14, delay: 0.11, wave: "triangle", volume: 0.18 },
        { frequency: 784, duration: 0.14, delay: 0.22, wave: "triangle", volume: 0.2 },
        { frequency: 1047, duration: 0.28, delay: 0.33, wave: "triangle", volume: 0.2 },
    ],
    lose: [
        { frequency: 440, endFrequency: 370, duration: 0.16, wave: "triangle", volume: 0.18 },
        { frequency: 370, endFrequency: 294, duration: 0.18, delay: 0.14, wave: "triangle", volume: 0.18 },
        { frequency: 294, endFrequency: 196, duration: 0.32, delay: 0.3, wave: "triangle", volume: 0.2 },
    ],
};

// Each level gets its own short, looping chiptune theme. Notes are generated
// with Web Audio so the soundtrack does not need external audio files.
// Themes follow the loaded level order: tutorial, daytime, night, rooftops,
// night shift, then the boss level.
const musicThemes = [
    {
        bpm: 108, tonic: 50, scale: [0, 2, 3, 5, 7, 8, 10], chords: [0, 5, 6, 3], wave: "triangle",
        melody: [0, null, 2, null, 3, null, 2, null, 0, null, 2, 3, 5, null, 3, null, 0, null, 2, 3, 2, null, 0, null, 5, null, 3, null, 2, null, 0, null],
    },
    {
        bpm: 116, tonic: 55, scale: [0, 2, 4, 5, 7, 9, 11], chords: [0, 3, 4, 0], wave: "square",
        melody: [0, 2, null, 4, 5, null, 4, 2, 0, null, 2, 4, 2, null, 0, null, 4, null, 5, 7, 5, null, 4, null, 2, null, 4, 2, 0, null, 2, null],
    },
    {
        bpm: 102, tonic: 57, scale: [0, 2, 3, 5, 7, 8, 10], chords: [0, 5, 3, 6], wave: "triangle",
        melody: [0, null, 3, null, 5, 3, null, 2, 0, null, 2, null, 3, null, 5, null, 7, null, 5, 3, 2, null, 0, null, 3, null, 5, null, 3, 2, 0, null],
    },
    {
        bpm: 122, tonic: 52, scale: [0, 2, 3, 5, 7, 9, 10], chords: [0, 3, 5, 4], wave: "square",
        melody: [0, 2, 3, null, 5, null, 3, 2, 0, null, 2, 3, 5, 7, 5, null, 3, null, 5, 7, 5, null, 3, null, 2, null, 3, 5, 3, null, 2, null],
    },
    {
        bpm: 88, tonic: 54, scale: [0, 2, 3, 5, 7, 8, 10], chords: [0, 3, 6, 5], wave: "sine",
        melody: [0, null, null, 2, null, 3, null, null, 5, null, 3, null, 2, null, null, 0, 3, null, null, 5, null, 7, null, 5, 3, null, 2, null, 0, null, null, null],
    },
    {
        bpm: 132, tonic: 48, scale: [0, 2, 3, 5, 7, 8, 11], chords: [0, 6, 3, 5], wave: "sawtooth",
        melody: [0, 0, 3, null, 5, 3, 2, null, 0, null, 3, 5, 7, null, 5, 3, 8, null, 7, 5, 3, null, 2, 3, 5, null, 3, 2, 0, null, 2, null],
    },
];

let enabled = readEnabled();
let context = null;
let masterGain = null;
let musicSession = null;

function ensureContext() {
    if (context) return context;
    const AudioContextClass = window.AudioContext ?? window.webkitAudioContext;
    if (!AudioContextClass) return null;

    try {
        context = new AudioContextClass();
        masterGain = context.createGain();
        masterGain.gain.value = enabled ? 0.28 : 0;
        masterGain.connect(context.destination);
        return context;
    } catch {
        context = null;
        masterGain = null;
        return null;
    }
}

function unlock() {
    const audio = ensureContext();
    if (audio?.state === "suspended") audio.resume().catch(() => {});
}

function playTone(audio, note, startAt) {
    const oscillator = audio.createOscillator();
    const envelope = audio.createGain();
    const duration = note.duration;
    const start = startAt + (note.delay ?? 0);
    const end = start + duration;
    const attack = Math.min(0.008, duration / 3);

    oscillator.type = note.wave ?? "triangle";
    oscillator.frequency.setValueAtTime(note.frequency, start);
    if (note.endFrequency) oscillator.frequency.exponentialRampToValueAtTime(note.endFrequency, end);

    envelope.gain.setValueAtTime(0.0001, start);
    envelope.gain.exponentialRampToValueAtTime(note.volume ?? 0.18, start + attack);
    envelope.gain.exponentialRampToValueAtTime(0.0001, end);

    oscillator.connect(envelope);
    envelope.connect(masterGain);
    oscillator.start(start);
    oscillator.stop(end + 0.01);
}

function midiFrequency(note) {
    return 440 * 2 ** ((note - 69) / 12);
}

function scaleNote(theme, degree, octave = 0) {
    const scaleLength = theme.scale.length;
    return theme.tonic + theme.scale[degree % scaleLength] + Math.floor(degree / scaleLength) * 12 + octave;
}

function playMusicNote(session, note, startAt, duration, wave, volume) {
    const audio = session.audio;
    const oscillator = audio.createOscillator();
    const envelope = audio.createGain();
    const end = startAt + duration;

    oscillator.type = wave;
    oscillator.frequency.setValueAtTime(midiFrequency(note), startAt);
    envelope.gain.setValueAtTime(0.0001, startAt);
    envelope.gain.exponentialRampToValueAtTime(volume, startAt + Math.min(0.015, duration / 4));
    envelope.gain.exponentialRampToValueAtTime(0.0001, end);
    oscillator.connect(envelope);
    envelope.connect(session.output);
    oscillator.onended = () => {
        session.sources.delete(oscillator);
        if (session.stopping && session.sources.size === 0) session.output.disconnect();
    };
    session.sources.add(oscillator);
    oscillator.start(startAt);
    oscillator.stop(end + 0.02);
}

function scheduleMusicStep(session, step, startAt) {
    const { theme } = session;
    const slot = step % theme.melody.length;
    const stepDuration = 30 / theme.bpm;
    const chordDegree = theme.chords[Math.floor(slot / 8) % theme.chords.length];

    // A low pulse marks each beat, while the chord changes once per bar.
    if (slot % 2 === 0) {
        playMusicNote(session, scaleNote(theme, chordDegree, -12), startAt, stepDuration * 1.65, "triangle", 0.13);
    }
    if (slot % 8 === 0) {
        for (const interval of [0, 2, 4]) {
            playMusicNote(session, scaleNote(theme, chordDegree + interval, 12), startAt, stepDuration * 3.5, "sine", 0.024);
        }
    }

    const melodyDegree = theme.melody[slot];
    if (melodyDegree !== null && melodyDegree !== undefined) {
        playMusicNote(session, scaleNote(theme, melodyDegree, 12), startAt, stepDuration * 0.78, theme.wave, 0.12);
    }
}

function scheduleMusic(session) {
    if (musicSession !== session || session.audio.state === "closed") return;
    const horizon = session.audio.currentTime + 0.12;
    while (session.nextStepAt < horizon) {
        scheduleMusicStep(session, session.step, session.nextStepAt);
        session.step = (session.step + 1) % session.theme.melody.length;
        session.nextStepAt += 30 / session.theme.bpm;
    }
}

function stopMusic() {
    if (!musicSession) return;
    const session = musicSession;
    musicSession = null;
    window.clearInterval(session.timer);
    session.stopping = true;
    const now = session.audio.currentTime;
    session.output.gain.cancelScheduledValues(now);
    session.output.gain.setTargetAtTime(0.0001, now, 0.025);
    for (const source of session.sources) {
        try { source.stop(now + 0.12); } catch { /* It may have ended already. */ }
    }
    window.setTimeout(() => session.output.disconnect(), 220);
}

function playLevelMusic(levelIndex) {
    if (!Number.isInteger(levelIndex) || levelIndex < 0) return;
    const themeIndex = levelIndex % musicThemes.length;
    if (musicSession?.themeIndex === themeIndex) return;
    stopMusic();

    const audio = ensureContext();
    if (!audio || !masterGain) return;
    if (audio.state === "suspended") audio.resume().catch(() => {});

    const output = audio.createGain();
    output.gain.setValueAtTime(0.0001, audio.currentTime);
    output.gain.setTargetAtTime(0.75, audio.currentTime, 0.06);
    output.connect(masterGain);
    const session = {
        audio,
        output,
        theme: musicThemes[themeIndex],
        themeIndex,
        sources: new Set(),
        step: 0,
        nextStepAt: audio.currentTime + 0.04,
        stopping: false,
        timer: null,
    };
    musicSession = session;
    session.timer = window.setInterval(() => scheduleMusic(session), 25);
    scheduleMusic(session);
}

export const sound = {
    get enabled() {
        return enabled;
    },

    setEnabled(next) {
        enabled = Boolean(next);
        try {
            window.localStorage.setItem(STORAGE_KEY, String(enabled));
        } catch {
            // Sound still works for this session when browser storage is unavailable.
        }

        const audio = ensureContext();
        if (audio && masterGain) {
            masterGain.gain.setTargetAtTime(enabled ? 0.28 : 0, audio.currentTime, 0.015);
            if (enabled && audio.state === "suspended") audio.resume().catch(() => {});
        }
    },

    unlock,

    playLevelMusic,

    stopMusic,

    play(name) {
        if (!enabled) return;
        const notes = effects[name];
        const audio = ensureContext();
        if (!notes || !audio || !masterGain) return;
        if (audio.state === "suspended") audio.resume().catch(() => {});

        const startAt = audio.currentTime + 0.01;
        for (const note of notes) playTone(audio, note, startAt);
    },
};

// Browsers require a user gesture before audio can play. Keep the context ready
// on the first click or key press, without playing anything by itself.
window.addEventListener("pointerdown", unlock, { capture: true });
window.addEventListener("keydown", unlock, { capture: true });
