#!/usr/bin/env python3
"""Synthesize the Reel's sound-effects layer, locked to the reel.html timeline (128 BPM grid).
Royalty-free: every sound is generated here. usage: sfx.py OUT.wav [duration]

Sound map (the brand's sonic kit):
  slam    - punchy thud + air for every word that slams in
  zip     - fast whoosh when the queue of cars zips in
  honk    - two short car horns while the queue is stuck (pain only)
  whoosh  - on every cut, under the white flash
  wash    - soft sea/air swell when the day comes back
  swish   - rising swish while the checkmark draws
  ding    - the Avar "passed" chime (two notes up) when the check lands and when the logo pops
  pop     - bubbly pop for the CTA pill and small UI elements
"""
import sys, wave
import numpy as np

SR = 48000
OUT = sys.argv[1]; DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 12.0
B = 60 / 128
S = [0, 4 * B, 6 * B, 14 * B, 18 * B]      # shot starts, same as reel.html
N = int(SR * DUR); mix = np.zeros((N, 2))
rng = np.random.default_rng(11)

def t_(sec): return np.arange(int(sec * SR)) / SR
def env(n, a=0.002, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
def lp(x, cut):
    a = np.exp(-2 * np.pi * cut / SR); y = np.zeros_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc; y[i] = acc
    return y
def hp(x, cut): return x - lp(x, cut)
def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N: return
    j = min(N, i + len(sig)); s = sig[: j - i] * gain
    mix[i:j, 0] += s * (1 - max(0, pan)); mix[i:j, 1] += s * (1 + min(0, pan))

def slam():
    t = t_(0.30); f = 50 + 140 * np.exp(-t * 35)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.001, 0.09)
    air = hp(rng.standard_normal(len(t)), 2500) * env(len(t), 0.001, 0.03) * 0.35
    return body + air

def whoosh(length=0.35, up=True):
    t = t_(length); n = len(t)
    noise = rng.standard_normal(n)
    shape = np.sin(np.pi * t / length) ** 2
    # sweep a band by blending low/high-passed noise over time
    lo, hi = lp(noise, 900), hp(noise, 3000)
    k = t / length if up else 1 - t / length
    return (lo * (1 - k) + hi * k) * shape * 0.6

def zip_(length=0.45):
    t = t_(length)
    f = 300 + 2200 * (t / length) ** 1.5
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.12
    return (whoosh(length) + tone) * np.sin(np.pi * t / length)

def honk(length=0.16):
    t = t_(length)
    sq = np.sign(np.sin(2 * np.pi * 415 * t)) + np.sign(np.sin(2 * np.pi * 523 * t))
    return lp(sq * 0.25, 2200) * np.minimum(1, t / 0.005) * np.minimum(1, (length - t) / 0.02)

def wash(length=2.0):
    t = t_(length); n = len(t)
    x = lp(rng.standard_normal(n), 1200) * (np.sin(np.pi * t / length) ** 2)
    return x * (0.6 + 0.4 * np.sin(2 * np.pi * 0.9 * t)) * 0.5

def swish(length=0.45):
    t = t_(length)
    return hp(rng.standard_normal(len(t)), 1500) * (t / length) ** 2 * 0.35

def bell(freq, length=0.9, gain=1.0):
    t = t_(length)
    partials = [(1, 1.0, 0.5), (2.0, 0.35, 0.25), (3.01, 0.18, 0.15), (4.2, 0.08, 0.08)]
    x = sum(a * np.sin(2 * np.pi * freq * m * t) * np.exp(-t / d) for m, a, d in partials)
    return x * np.minimum(1, t / 0.002) * gain

def ding():  # the Avar "passed" chime: E6 then B6, bright and quick
    out = np.zeros(int(1.1 * SR))
    a = bell(1318.5, 0.9); b = bell(1975.5, 1.0, 0.9)
    out[: len(a)] += a; o = int(0.09 * SR); out[o: o + len(b)] += b[: len(out) - o]
    return out * 0.45

def pop():
    t = t_(0.09); f = 900 * np.exp(-t * 30) + 300
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.0008, 0.03) * 0.6

# --- shot 1: the queue (pain)
add(slam(), 0.02, 0.9); add(slam(), B, 0.9)
add(zip_(0.5), 0.12, 0.9, -0.4)
add(honk(), 0.95, 0.45, 0.3); add(honk(0.22), 1.20, 0.5, -0.2)
add(pop(), 0.70, 0.5)                     # clock pops in
# --- cut to "ואתם?"
add(whoosh(0.3), S[1] - 0.22, 0.9); add(slam(), S[1] + 0.02, 1.0)
# --- the day back
add(whoosh(0.35), S[2] - 0.25, 0.8); add(slam(), S[2] + 0.02, 1.1)
add(wash(2.4), S[2] + 0.1, 0.55)
add(whoosh(0.25, up=False), S[2] + 5 * B - 0.05, 0.6)
add(slam(), S[2] + 5 * B + 0.04, 0.8); add(slam(), S[2] + 6 * B, 0.8)
# --- verdict
add(whoosh(0.3), S[3] - 0.22, 0.9); add(slam(), S[3] + 0.02, 1.0); add(slam(), S[3] + B, 1.0)
add(swish(B), S[3] + 2 * B, 0.9); add(ding(), S[3] + 3 * B - 0.02, 1.0)
# --- end card
add(whoosh(0.3), S[4] - 0.22, 0.8)
add(ding(), S[4] + 0.04, 0.8)              # logo pops with the brand chime
add(pop(), S[4] + B, 0.6); add(pop(), S[4] + 2 * B, 0.9); add(pop(), S[4] + 3 * B, 0.5)

mix /= np.max(np.abs(mix)) + 1e-9; mix *= 0.9
with wave.open(OUT, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print(OUT)
