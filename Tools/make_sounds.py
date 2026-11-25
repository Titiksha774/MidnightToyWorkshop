import os
import wave

import numpy as np

RATE = 44100
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Assets", "Audio")
rng = np.random.default_rng(3)


def t(seconds):
    return np.arange(int(seconds * RATE)) / RATE


def env(x, attack=0.002, decay=0.2):
    return np.minimum(1, x / attack) * np.exp(-x / decay)


def tone(freq, seconds, decay=0.3, partials=((1, 1.0),)):
    x = t(seconds)
    return sum(a * np.sin(2 * np.pi * freq * k * x) for k, a in partials) * env(x, decay=decay)


def noise(seconds):
    return rng.uniform(-1, 1, int(seconds * RATE))


def lowpass(sig, amount):
    amount = np.broadcast_to(amount, sig.shape)
    out = np.empty_like(sig)
    acc = 0.0
    for i, s in enumerate(sig):
        acc += amount[i] * (s - acc)
        out[i] = acc
    return out


def place(buf, sig, at):
    i = int(at * RATE)
    n = min(len(sig), len(buf) - i)
    buf[i:i + n] += sig[:n]


def save(name, sig, peak=0.9):
    sig = sig / (np.max(np.abs(sig)) + 1e-9) * peak
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes((sig * 32767).astype(np.int16).tobytes())


def midi(n):
    return 440 * 2 ** ((n - 69) / 12)


def snap():
    knock = lowpass(noise(0.06), 0.3) * env(t(0.06), decay=0.012)
    return knock + 0.6 * tone(820, 0.06, decay=0.02) + 0.3 * tone(1640, 0.06, decay=0.01)


def wind():
    buf = np.zeros(int(0.32 * RATE))
    for i in range(4):
        place(buf, noise(0.015) * env(t(0.015), 0.0005, 0.004) + 0.5 * tone(2400 + 200 * i, 0.015, decay=0.004), i * 0.07)
    return buf


def train_chug():
    buf = np.zeros(int(2.0 * RATE))
    for i in range(4):
        puff = lowpass(noise(0.35), 0.08) * env(t(0.35), 0.01, 0.09)
        place(buf, puff * (1.0 if i % 2 == 0 else 0.7), i * 0.5)
    return buf + 0.15 * lowpass(noise(2.0), 0.02)


def whistle():
    x = t(1.3)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 6 * x)
    shape = np.minimum(1, x / 0.08) * np.minimum(1, (1.3 - x) / 0.2)
    sig = sum(np.sin(2 * np.pi * f * vib * x) for f in (midi(79), midi(83), midi(86)))
    return (sig + 0.3 * lowpass(noise(1.3), 0.3)) * shape


def boing():
    x = t(0.9)
    freq = 140 + 260 * np.exp(-x * 5) * (1 + 0.35 * np.sin(2 * np.pi * 9 * x))
    phase = 2 * np.pi * np.cumsum(freq) / RATE
    return np.sin(phase) * env(x, 0.003, 0.35)


def squeak():
    buf = np.zeros(int(0.35 * RATE))
    for i, f in enumerate((3200, 4100, 3600)):
        x = t(0.07)
        sweep = f * (1 + 0.25 * x / 0.07)
        place(buf, np.sin(2 * np.pi * np.cumsum(sweep) / RATE) * np.sin(np.pi * x / 0.07), i * 0.1)
    return buf


def clink(f=1300):
    return tone(f, 0.12, decay=0.03, partials=((1, 1.0), (2.76, 0.6), (5.4, 0.3)))


def march_loop():
    buf = np.zeros(int(1.0 * RATE))
    place(buf, clink(1300), 0.0)
    place(buf, clink(1180) * 0.8, 0.5)
    return buf


def clatter():
    buf = np.zeros(int(0.7 * RATE))
    for i in range(7):
        place(buf, clink(rng.uniform(900, 1700)) * rng.uniform(0.4, 1.0), rng.uniform(0, 0.5))
    return buf


def cuckoo():
    buf = np.zeros(int(3.0 * RATE))
    for i in range(3):
        for note, at in ((midi(79), 0.0), (midi(76), 0.28)):
            place(buf, tone(note, 0.4, decay=0.15, partials=((1, 1.0), (2, 0.25), (3, 0.1))), i * 0.95 + at)
    return buf


def fire():
    seconds = 4.0
    base = lowpass(noise(seconds), 0.015) * 0.6
    for _ in range(70):
        pop = noise(0.01) * env(t(0.01), 0.0003, 0.002) * rng.uniform(0.2, 1.0)
        place(base, pop, rng.uniform(0, seconds - 0.02))
    fade = int(0.05 * RATE)
    base[:fade] *= np.linspace(0, 1, fade)
    base[-fade:] *= np.linspace(1, 0, fade)
    return base


def bump():
    thud = tone(85, 0.25, decay=0.07, partials=((1, 1.0), (2.1, 0.3)))
    return thud + 0.5 * lowpass(noise(0.25), 0.05) * env(t(0.25), 0.001, 0.04)


def click():
    return tone(1800, 0.04, decay=0.008) + 0.3 * noise(0.04) * env(t(0.04), 0.0005, 0.003)


def whoosh():
    x = t(0.4)
    return lowpass(noise(0.4), 0.05 + 0.25 * x / 0.4) * np.sin(np.pi * x / 0.4)


def babble():
    buf = np.zeros(int(1.6 * RATE))
    at = 0.0
    while at < 1.4:
        length = rng.uniform(0.07, 0.14)
        x = t(length)
        f = rng.uniform(170, 260)
        voice = sum(a * np.sin(2 * np.pi * f * k * x) for k, a in ((1, 1.0), (2, 0.5), (3, 0.35), (4, 0.15)))
        place(buf, voice * np.sin(np.pi * x / length) ** 2, at)
        at += length + rng.uniform(0.02, 0.06)
    return buf


def sparkle():
    buf = np.zeros(int(1.4 * RATE))
    for i, n in enumerate((84, 88, 91, 96, 100)):
        place(buf, tone(midi(n), 0.9, decay=0.35, partials=((1, 1.0), (2.01, 0.3))), i * 0.07)
    return buf


def music_box_tune():
    melody = [(72, 1), (72, 1), (79, 1), (79, 1), (81, 1), (81, 1), (79, 2),
              (77, 1), (77, 1), (76, 1), (76, 1), (74, 1), (74, 1), (72, 2),
              (79, 1), (79, 1), (77, 1), (77, 1), (76, 1), (76, 1), (74, 2),
              (79, 1), (79, 1), (77, 1), (77, 1), (76, 1), (76, 1), (74, 2),
              (72, 1), (72, 1), (79, 1), (79, 1), (81, 1), (81, 1), (79, 2),
              (77, 1), (77, 1), (76, 1), (76, 1), (74, 1), (74, 1), (72, 2), (0, 2)]
    beat = 0.42
    buf = np.zeros(int(sum(b for _, b in melody) * beat * RATE))
    at = 0.0
    for n, beats in melody:
        if n:
            pluck = tone(midi(n), 2.0, decay=0.3, partials=((1, 1.0), (2, 0.3)))
            i = int(at * RATE)
            idx = (np.arange(len(pluck)) + i) % len(buf)
            np.add.at(buf, idx, pluck)
        at += beats * beat
    return buf


def background_music():
    chords = [(60, 64, 67), (57, 60, 64), (53, 57, 60), (55, 59, 62)] * 2
    beat = 0.5
    buf = np.zeros(int(len(chords) * 4 * beat * RATE))
    for c, chord in enumerate(chords):
        start = c * 4 * beat
        for k, n in enumerate((chord[0], chord[1], chord[2], chord[1])):
            place(buf, 0.5 * tone(midi(n + 12), 1.6, decay=0.6, partials=((1, 1.0), (3, 0.08))), start + k * beat)
        place(buf, 0.35 * tone(midi(chord[0] - 12), 2.2, decay=1.2), start)
    tail = int(1.0 * RATE)
    buf[:tail] += buf[-tail:] * np.linspace(1, 0, tail)
    return buf


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, make in (("Snap", snap), ("Wind", wind), ("TrainChug", train_chug), ("Whistle", whistle),
                       ("Boing", boing), ("Squeak", squeak), ("MarchLoop", march_loop), ("Clatter", clatter),
                       ("Cuckoo", cuckoo), ("Fire", fire), ("Click", click), ("Bump", bump), ("Whoosh", whoosh),
                       ("Babble", babble), ("Sparkle", sparkle), ("MusicBoxTune", music_box_tune),
                       ("Music", background_music)):
        save(name, make())
    print("sounds written to", OUT)


if __name__ == "__main__":
    main()
