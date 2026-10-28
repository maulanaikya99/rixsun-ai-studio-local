#!/usr/bin/env python3
"""Tahap 2 - narasi lokal: VoiceStudio OmniVoice (kloning narator wanita 66) -> Whisper memilih take -> narasi.wav.
Jalankan dengan python venv mflux (butuh torch + transformers untuk Whisper).
Usage: suara.py <folder proyek> [tts|pilih|rakit|kata|semua]
Hasil: suara/narasi.wav, suara/adegan.json (waktu tiap adegan), suara/kata.json (waktu tiap kata)"""
import glob, json, os, re, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lafal import lafal

API = "http://localhost:3900"
AI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # folder AI (portabel)
ROOT = os.path.dirname(AI)
APP = next((a for a in (os.environ.get("VOICESTUDIO_APP", ""), f"{ROOT}/application/VoiceStudio.app", "/Applications/VoiceStudio.app")
            if a and os.path.exists(a)), "/Applications/VoiceStudio.app")
WHISPER = f"{AI}/models/whisper-large-v3-turbo"
REF = os.environ.get("REF", f"{AI}/tts/ref/narator_wanita_66.wav")
REF_TEXT = open(REF[:-4] + ".txt").read().strip() if os.path.exists(REF[:-4] + ".txt") else ""
TAKES = int(os.environ.get("TAKES", "2"))
SPEED = float(os.environ.get("SPEED", "1.0"))
GAP = 0.45

P = sys.argv[1]
SUARA = os.path.join(P, "suara")
TK = os.path.join(SUARA, "takes")
NASKAH = json.load(open(os.path.join(P, "naskah.json")))
LINES = {f"s{i:02d}": (a["narasi"], lafal(a["narasi"])) for i, a in enumerate(NASKAH["adegan"], 1)}


def sh(*a, **k):
    return subprocess.run(list(a), capture_output=True, text=True, **k)


def dur(p):
    return float(sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p).stdout)


def studio_siap():
    r = sh("curl", "-s", "-m", "5", f"{API}/health").stdout
    return '"status":"starting"' not in r and r.strip().startswith("{")


def studio_nyala():
    if studio_siap():
        return
    print("Menyalakan VoiceStudio ...", flush=True)
    subprocess.run(["open", "-g", "-a", APP])
    for _ in range(120):
        if studio_siap():
            print("VoiceStudio siap", flush=True)
            return
        time.sleep(3)
    sys.exit("VoiceStudio tidak siap dalam 6 menit")


def studio_mati():
    """Tutup VoiceStudio agar RAM lega untuk FLUX/LTX."""
    subprocess.run(["osascript", "-e", 'tell application "VoiceStudio" to quit'], capture_output=True)
    for _ in range(20):
        if not sh("pgrep", "-f", "uvicorn main:app --app-dir backend --host 127.0.0.1 --port 3900").stdout.strip():
            break
        time.sleep(1)
    subprocess.run(["pkill", "-f", "uvicorn main:app --app-dir backend --host 127.0.0.1 --port 3900"], capture_output=True)
    print("VoiceStudio ditutup (RAM dibebaskan)", flush=True)


def tts():
    os.makedirs(TK, exist_ok=True)
    studio_nyala()
    for k, (cap, sp) in LINES.items():
        print(f"\n[{k}] {cap}\n      dibaca: {sp}", flush=True)
        for seed in range(1, TAKES + 1):
            out = f"{TK}/{k}_t{seed}.wav"
            if os.path.exists(out):
                continue
            for coba in range(3):
                t0 = time.time()
                r = sh("curl", "-s", "-m", "600", "-X", "POST", f"{API}/generate", "-F", f"text={sp}", "-F", "language=id",
                       "-F", "engine=omnivoice", "-F", f"ref_audio=@{REF}", "-F", f"ref_text={REF_TEXT}",
                       "-F", f"seed={seed * 101 + coba}", "-F", f"speed={SPEED}", "-o", out, "-w", "%{http_code}")
                if r.stdout.strip() == "200" and os.path.exists(out) and open(out, "rb").read(4) == b"RIFF":
                    print(f"      take {seed}: {dur(out):.1f} dtk audio ({time.time() - t0:.0f} dtk)", flush=True)
                    break
                if os.path.exists(out):
                    os.remove(out)
                print(f"      take {seed} gagal (HTTP {r.stdout.strip()}), ulang ...", flush=True)
                time.sleep(5)
    studio_mati()


def _norm(s):
    return re.sub(r"[^a-z0-9 ]+", " ", lafal(s).lower()).split()


def _wer(ref, hyp):
    r, h = _norm(ref), _norm(hyp)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1]))
    return d[len(h)] / max(1, len(r))


_asr = None


def asr():
    global _asr
    if _asr is None:
        import torch
        from transformers import pipeline
        _asr = pipeline("automatic-speech-recognition", model=WHISPER, dtype=torch.float16, device="mps")
    return _asr


def potong_awal(src):
    """OmniVoice often puts a short "i" (+ a quiet breath) before the sentence: a loud sound <=0.35 s, then >=0.15 s
    before the next LOUD sound (quiet breath runs in between are ignored; "iPhone"-like words have only ~0.13 s).
    If found, write a copy that starts just before the sentence to takes/bersih/ and return its path (None otherwise)."""
    import numpy as np
    sr = 24000
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                                     capture_output=True, check=True).stdout, np.float32)
    h = sr // 100
    db = np.array([20 * np.log10(np.sqrt(np.mean(x[i * h:(i + 1) * h] ** 2)) + 1e-9) for i in range(len(x) // h)])
    if not len(db):
        return None
    v = db > db.max() - 35
    runs, i = [], 0
    while i < len(v) and len(runs) < 8:
        if v[i]:
            j = i
            while j < len(v) and v[j:j + 4].any():          # gaps < 40 ms stay one sound
                j += 1
            runs.append((i, j, db[i:j].max())); i = j
        else:
            i += 1
    loud = [r for r in runs if r[2] >= db.max() - 20]       # breaths are much quieter than words
    if len(loud) < 2:
        return None
    a, nxt = loud[0], loud[1]
    if not (a[1] - a[0] <= 35 and a[0] <= 60 and nxt[0] - a[1] >= 15 and nxt[0] <= 150):
        return None
    os.makedirs(f"{TK}/bersih", exist_ok=True)
    dst = f"{TK}/bersih/{os.path.basename(src)}"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, nxt[0] - 3) / 100:.2f}", "-i", src, dst], check=True)
    return dst


def pilih():
    hasil = {}
    for k, (cap, sp) in LINES.items():
        skor = []
        for p in sorted(glob.glob(f"{TK}/{k}_t*.wav")):
            hyp = asr()(p, generate_kwargs={"language": "indonesian", "task": "transcribe"})["text"].strip()
            w = _wer(sp, hyp)
            q = potong_awal(p)
            if q:                                            # pakai versi terpotong hanya bila Whisper tak kehilangan kata
                hyp2 = asr()(q, generate_kwargs={"language": "indonesian", "task": "transcribe"})["text"].strip()
                w2 = _wer(sp, hyp2)
                print(f"{k} {os.path.basename(p):10s} bunyi awal dibuang: salah {w * 100:.0f}% -> {w2 * 100:.0f}%"
                      f"{'' if w2 <= w else ' (dibatalkan)'}", flush=True)
                if w2 <= w:
                    p, hyp, w = q, hyp2, w2
            d = dur(p)
            cps = len(sp) / d
            skor.append(dict(file=os.path.relpath(p, TK), wer=round(w, 3), dur=round(d, 2),
                             score=round(w + (0.1 if not 12 <= cps <= 20 else 0), 3), heard=hyp))
            print(f"{k} {os.path.basename(p):10s} salah {w * 100:4.0f}%  {d:4.1f} dtk | {hyp}", flush=True)
        skor.sort(key=lambda s: (s["score"], s["dur"]))
        hasil[k] = skor
        if skor:
            print(f"   -> dipakai {skor[0]['file']}", flush=True)
    json.dump(hasil, open(f"{SUARA}/pilihan.json", "w"), indent=1, ensure_ascii=False)


def _rapikan(src, dst):
    t = "silenceremove=start_periods=1:start_threshold=-50dB"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af",
                    f"highpass=f=60,{t},areverse,{t},areverse,adelay=60:all=1,apad=pad_dur=0.12",
                    "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", dst], check=True)
    return dur(dst)


def rakit():
    pick = json.load(open(f"{SUARA}/pilihan.json"))
    tmp = os.path.join(SUARA, "_tmp"); os.makedirs(tmp, exist_ok=True)
    adg, parts, t = [], [], 0.0
    for k, (cap, sp) in LINES.items():
        d = _rapikan(f"{TK}/{pick[k][0]['file']}", f"{tmp}/{k}.wav")
        adg.append(dict(key=k, mulai=round(t, 3), selesai=round(t + d, 3), teks=cap, ucapan=sp))
        parts.append(f"{tmp}/{k}.wav")
        t += d + GAP
    gap = f"{tmp}/gap.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", str(GAP),
                    "-c:a", "pcm_s16le", gap], check=True)
    with open(f"{tmp}/list.txt", "w") as fh:
        for j, p in enumerate(parts):
            fh.write(f"file '{p}'\n" + (f"file '{gap}'\n" if j < len(parts) - 1 else ""))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt",
                    "-af", "loudnorm=I=-18:TP=-1.5:LRA=7", "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le",
                    f"{SUARA}/narasi.wav"], check=True)
    json.dump(adg, open(f"{SUARA}/adegan.json", "w"), indent=1, ensure_ascii=False)
    print(f"narasi.wav {dur(f'{SUARA}/narasi.wav'):.1f} dtk, {len(adg)} adegan", flush=True)


def kata():
    adg = json.load(open(f"{SUARA}/adegan.json"))
    tmp = os.path.join(SUARA, "_tmp")
    out = {}
    for a in adg:
        cut = f"{tmp}/{a['key']}_16k.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a['mulai']:.3f}", "-to", f"{a['selesai']:.3f}",
                        "-i", f"{SUARA}/narasi.wav", "-ar", "16000", "-ac", "1", cut], check=True)
        r = asr()(cut, return_timestamps="word", generate_kwargs={"language": "indonesian", "task": "transcribe"})
        out[a["key"]] = [[c["text"].strip(), round(a["mulai"] + c["timestamp"][0], 3),
                          round(a["mulai"] + (c["timestamp"][1] or c["timestamp"][0]), 3)] for c in r["chunks"]]
    json.dump(out, open(f"{SUARA}/kata.json", "w"), indent=1, ensure_ascii=False)
    print(f"waktu kata: {sum(len(v) for v in out.values())} kata", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[2] if len(sys.argv) > 2 else "semua"
    t0 = time.time()
    if cmd in ("tts", "semua"):
        tts()
    if cmd in ("pilih", "semua"):
        pilih()
    if cmd in ("rakit", "semua"):
        rakit()
    if cmd in ("kata", "semua"):
        kata()
    print(f"suara selesai dalam {time.time() - t0:.0f} dtk", flush=True)
