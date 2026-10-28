#!/usr/bin/env python3
"""Musik latar prosedural (numpy, tanpa sampel/lisensi): pad hangat + arpeggio petik + ketukan lembut.
Usage: musik.py <out.wav> <durasi detik> [seed]"""
import sys, wave
import numpy as np

SR = 48000
BPM = 92
# progresi I - vi - IV - V (C - Am - F - G), tiap akor 2 birama
AKOR = [[48, 52, 55, 60], [45, 48, 52, 57], [41, 45, 48, 53], [43, 47, 50, 55]]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env(n, a, r):
    e = np.ones(n)
    a, r = min(a, n // 2), min(r, n // 2)
    e[:a] = np.linspace(0, 1, a)
    e[n - r:] = np.linspace(1, 0, r)
    return e


def pad(m, n, rng):
    t = np.arange(n) / SR
    s = np.zeros(n)
    for det in (-0.12, 0.0, 0.12):                       # tiga osilator sedikit detune = hangat
        f = hz(m) * 2 ** (det / 12)
        s += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) + 0.25 * np.sin(4 * np.pi * f * t)
    return s * env(n, int(0.6 * SR), int(0.8 * SR)) / 3


def pluck(m, n):
    t = np.arange(n) / SR
    f = hz(m)
    s = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(4 * np.pi * f * t) + 0.15 * np.sin(6 * np.pi * f * t))
    return s * np.exp(-t * 5.5) * env(n, 60, 2000)


def kick(n):
    t = np.arange(n) / SR
    f = 110 * np.exp(-t * 18) + 45
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def hat(n, rng):
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    x = np.diff(np.concatenate([[0], x]))                # buang frekuensi rendah
    return x * np.exp(-t * 60)


def buat(dur, seed=7):
    rng = np.random.default_rng(seed)
    N = int((dur + 2) * SR)
    L, R = np.zeros(N), np.zeros(N)
    beat = 60 / BPM
    bar = 4 * beat
    nbar = int(np.ceil((dur + 2) / bar))
    for b in range(nbar):
        a0 = int(b * bar * SR)
        akor = AKOR[(b // 2) % len(AKOR)]
        if b % 2 == 0:                                   # pad 2 birama
            n = min(int(2 * bar * SR), N - a0)
            for k, m in enumerate(akor):
                s = pad(m, n, rng) * 0.10
                L[a0:a0 + n] += s * (0.6 + 0.1 * k); R[a0:a0 + n] += s * (0.9 - 0.1 * k)
        pola = [0, 2, 1, 3, 2, 1, 3, 2]                  # arpeggio 1/8
        for j in range(8):
            i0 = a0 + int(j * beat / 2 * SR)
            if i0 >= N or b == 0:
                continue
            n = min(int(1.2 * SR), N - i0)
            s = pluck(akor[pola[j]] + 12, n) * (0.07 if j % 2 == 0 else 0.05)
            pan = 0.35 + 0.3 * (j % 3) / 2
            L[i0:i0 + n] += s * (1 - pan); R[i0:i0 + n] += s * pan
        if b >= 2:                                       # ritme masuk setelah intro
            for j in range(4):
                i0 = a0 + int(j * beat * SR)
                if j in (0, 2):
                    n = min(int(0.4 * SR), N - i0)
                    k = kick(n) * 0.22
                    L[i0:i0 + n] += k; R[i0:i0 + n] += k
                i1 = a0 + int((j + 0.5) * beat * SR)
                n = min(int(0.08 * SR), N - i1)
                if n > 0:
                    h = hat(n, rng) * 0.03
                    L[i1:i1 + n] += h * 0.7; R[i1:i1 + n] += h
    st = np.stack([L, R], 1)[: int(dur * SR)]
    fi, fo = int(1.0 * SR), int(2.5 * SR)
    st[:fi] *= np.linspace(0, 1, fi)[:, None]
    st[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return st / (np.abs(st).max() + 1e-9) * 0.7


if __name__ == "__main__":
    out, dur = sys.argv[1], float(sys.argv[2])
    st = buat(dur, int(sys.argv[3]) if len(sys.argv) > 3 else 7)
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype("<i2").tobytes())
    print(f"musik {dur:.1f} dtk -> {out}")
