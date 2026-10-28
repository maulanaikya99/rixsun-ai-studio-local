#!/usr/bin/env python3
"""Tahap 3 - FLUX.1 schnell (lokal) menggambar tiap adegan dari prompt Gemma.
Usage: gambar.py <folder proyek> [nomor adegan...]   -> adegan/sNN.png (768x1360), tiap gambar dibuka di layar."""
import json, os, subprocess, sys, time

AI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # folder AI (portabel)
MODEL = f"{AI}/models/flux-1-schnell-mflux-q4"
W, H, STEPS = 768, 1360, 4
P = sys.argv[1]
OUT = os.path.join(P, "adegan")
NASKAH = json.load(open(os.path.join(P, "naskah.json")))


def prompt(a):
    return f"{NASKAH['gaya'].rstrip('.')}. {a['gambar'].rstrip('.')}. Vertical composition. No text, no letters, no logo, no watermark; any screen shows only simple icons or abstract shapes."


def main():
    os.makedirs(OUT, exist_ok=True)
    pilih = [int(x) for x in sys.argv[2:]] or list(range(1, len(NASKAH["adegan"]) + 1))
    todo = [i for i in pilih if not os.path.exists(f"{OUT}/s{i:02d}.png")]
    if not todo:
        print("semua gambar sudah ada", flush=True); return
    from mflux.models.flux.variants.txt2img.flux import Flux1
    from mflux.models.common.config.model_config import ModelConfig
    t = time.time()
    flux = Flux1(model_path=MODEL, model_config=ModelConfig.schnell())
    print(f"FLUX dimuat dalam {time.time() - t:.0f} dtk", flush=True)
    for i in todo:
        a = NASKAH["adegan"][i - 1]
        out = f"{OUT}/s{i:02d}.png"
        print(f"\n[{i}/{len(NASKAH['adegan'])}] {a['label']}\n  prompt: {prompt(a)}", flush=True)
        t = time.time()
        img = flux.generate_image(seed=1000 + i, prompt=prompt(a), num_inference_steps=STEPS, height=H, width=W)
        img.save(path=out, overwrite=True)
        print(f"  selesai {time.time() - t:.0f} dtk -> {os.path.basename(out)}", flush=True)
        subprocess.run(["open", out])


if __name__ == "__main__":
    main()
