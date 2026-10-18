#!/usr/bin/env python3
"""Synthesize a royalty-free 128 BPM bed for the fast Reel: tense tick + filtered kick in the 'queue' part,
a riser, then a full upbeat drop when the day comes back. usage: music.py OUT.wav [duration]"""
import sys, numpy as np, wave
SR = 48000
out = sys.argv[1]; DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 12.0
BPM = 128; B = 60 / BPM
N = int(SR * DUR); mix = np.zeros((N, 2))
rng = np.random.default_rng(7)
DROP = 2.8  # seconds: the cut to the beach

def add(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR); j = min(N, i + len(sig))
    if i >= N: return
    s = sig[: j - i] * gain
    mix[i:j, 0] += s * (1 - max(0, pan)); mix[i:j, 1] += s * (1 + min(0, pan))

def env(n, a=0.002, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)

def kick():
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.12) * 1.0

def hp_noise(n, k=0.97):
    x = rng.standard_normal(n); y = np.zeros(n); prev = 0
    for i in range(1, n):
        y[i] = k * (y[i - 1] + x[i] - x[i - 1])
    return y

HAT = hp_noise(int(0.05 * SR)) * env(int(0.05 * SR), 0.0005, 0.012)
def clap():
    n = int(0.25 * SR); x = hp_noise(n, 0.9)
    e = sum(np.roll(env(n, 0.0005, 0.01), int(k * 0.011 * SR)) for k in range(3)) + env(n, 0.001, 0.06)
    return x * e * 0.5
CLAP = clap(); KICK = kick()

def pluck(freq, length=0.22):
    n = int(length * SR); t = np.arange(n) / SR
    saw = 2 * ((t * freq) % 1) - 1
    sq = np.sign(np.sin(2 * np.pi * freq * 2 * t)) * 0.3
    # simple one-pole lowpass with closing cutoff
    y = np.zeros(n); a = np.exp(-2 * np.pi * (300 + 2500 * np.exp(-t * 18)) / SR); x = saw + sq
    for i in range(1, n):
        y[i] = (1 - a[i]) * x[i] + a[i] * y[i - 1]
    return y * env(n, 0.002, 0.12)

def tick():
    n = int(0.03 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * 2400 * t) * env(n, 0.0005, 0.006)

# --- part 1: the queue (0 .. DROP): ticking clock + muffled kick
t = 0.0
while t < DROP:
    add(tick(), t, 0.25, 0.3); t += B / 2
t = 0.0
while t < DROP - 0.01:
    k = KICK.copy();  # muffle: crude lowpass by averaging
    k = np.convolve(k, np.ones(24) / 24, "same")
    add(k, t, 0.55); t += B
# riser into the drop
n = int(1.0 * SR); tt = np.arange(n) / SR
riser = hp_noise(n, 0.8) * (tt / tt[-1]) ** 2 * 0.25
add(riser, DROP - 1.0, 1.0)
# impact on the drop
add(KICK, DROP, 1.2); add(hp_noise(int(0.6 * SR), 0.6) * env(int(0.6 * SR), 0.001, 0.15) * 0.4, DROP, 1.0)

# --- part 2: the day back (DROP .. end): four-on-the-floor, claps, hats, bass plucks
roots = [261.63, 196.00, 220.00, 174.61]  # C G Am F (bass an octave down below)
beat = 0
t = DROP
while t < DUR - 0.05:
    add(KICK, t, 1.0)
    if beat % 2 == 1: add(CLAP, t, 0.9)
    add(HAT, t + B / 2, 0.35, -0.3)
    add(HAT, t + B / 4, 0.12, 0.3); add(HAT, t + 3 * B / 4, 0.12, 0.3)
    r = roots[(beat // 4) % 4]
    add(pluck(r / 2), t + B / 2, 0.45)
    if beat % 2 == 0: add(pluck(r, 0.15), t + 3 * B / 4, 0.18, 0.4)
    beat += 1; t += B

# fade the tail, gentle sidechain-ish pump on non-kick content is skipped for simplicity
fade = int(0.6 * SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
mix /= np.max(np.abs(mix)) + 1e-9; mix *= 0.85
pcm = (mix * 32767).astype(np.int16)
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print(out)
