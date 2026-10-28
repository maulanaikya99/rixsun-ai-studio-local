#!/usr/bin/env python3
"""Tahap 4 - LTX-2.3 (lokal) menggerakkan tiap gambar adegan dengan prompt gerak dari Gemma.
Bisa dilanjutkan: klip yang sudah OK di klip/status.json dilewati.
Usage: video.py <folder proyek> [nomor adegan...]   -> klip/sNN.mp4 (576x1024, 24 fps)"""
import json, os, subprocess, sys, time
from PIL import Image

AI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # folder AI (portabel)
CLI = f"{AI}/ltx-2-mlx/.venv/bin/ltx-2-mlx"
P = sys.argv[1]
OUT = os.path.join(P, "klip")
STATUS = os.path.join(OUT, "status.json")
NASKAH = json.load(open(os.path.join(P, "naskah.json")))
ADEGAN = json.load(open(os.path.join(P, "suara", "adegan.json")))


def frames_untuk(i):
    """Panjang klip mengikuti lama narasi adegan (klip boleh diperlambat sampai ±1,6x saat dirakit)."""
    a = ADEGAN[i - 1]
    akhir = ADEGAN[i]["mulai"] if i < len(ADEGAN) else a["selesai"] + 1.2
    need = (akhir - a["mulai"]) * 24 / 1.6
    for f in (73, 97, 121, 145):
        if f >= need:
            return f
    return 145


def input_916(i):
    src, dst = os.path.join(P, "adegan", f"s{i:02d}.png"), os.path.join(OUT, f"s{i:02d}_input.png")
    im = Image.open(src).convert("RGB")
    w, h = im.size
    cw = min(w, round(h * 9 / 16))
    im.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h)).save(dst)
    return dst


def main():
    os.makedirs(OUT, exist_ok=True)
    status = json.load(open(STATUS)) if os.path.exists(STATUS) else {}
    env = {**os.environ, "HF_HOME": f"{AI}/hf-cache", "HF_HUB_OFFLINE": "1"}
    pilih = [int(x) for x in sys.argv[2:]] or list(range(1, len(NASKAH["adegan"]) + 1))
    t_all = time.time()
    for n, i in enumerate(pilih, 1):
        key, out = f"s{i:02d}", os.path.join(OUT, f"s{i:02d}.mp4")
        if status.get(key, {}).get("ok") and os.path.exists(out):
            print(f"[{n}/{len(pilih)}] {key}: sudah ada, dilewati", flush=True); continue
        a, f = NASKAH["adegan"][i - 1], frames_untuk(i)
        pr = f"{NASKAH['gaya'].rstrip('.')}. {a['gerak']}"
        print(f"\n{'=' * 66}\n[{n}/{len(pilih)}] adegan {i} - {a['label']}  ({f} frame = {f / 24:.1f} dtk)\n"
              f"GERAK: {pr}\n{'=' * 66}", flush=True)
        t = time.time()
        cmd = [CLI, "generate", "--distilled", "--no-audio", "--low-ram",
               "--model", f"{AI}/models/ltx-2.3-mlx-q4", "--gemma", f"{AI}/models/gemma-3-12b-it-4bit",
               "--image", input_916(i), "-H", "1024", "-W", "576", "-f", str(f), "--frame-rate", "24",
               "--seed", "42", "--prompt", pr, "-o", out]
        rc = subprocess.call(cmd, cwd=f"{AI}/ltx-2-mlx", env=env)
        ok = rc == 0 and os.path.exists(out)
        status[key] = {"ok": ok, "rc": rc, "detik": round(time.time() - t), "frames": f}
        json.dump(status, open(STATUS, "w"), indent=1)
        done = sum(1 for v in status.values() if v.get("ok"))
        sisa = (len(pilih) - n) * (time.time() - t) / 60
        print(f"\n>>> adegan {i}: {'OK' if ok else 'GAGAL (kode %d)' % rc} dalam {(time.time() - t) / 60:.1f} mnt | "
              f"selesai {done}/{len(pilih)} | berjalan {(time.time() - t_all) / 60:.0f} mnt | sisa ±{sisa:.0f} mnt", flush=True)
        if ok:
            subprocess.run(["open", out])
    print(f"\nVIDEO AI SELESAI: {sum(1 for v in status.values() if v.get('ok'))}/{len(pilih)} klip "
          f"dalam {(time.time() - t_all) / 60:.0f} mnt", flush=True)


if __name__ == "__main__":
    main()
