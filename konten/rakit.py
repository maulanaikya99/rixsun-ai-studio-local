#!/usr/bin/env python3
"""Tahap 5 - rakit otomatis (ffmpeg + Pillow): klip LTX (atau gambar + zoom pelan bila klip tak ada),
label adegan, judul, subtitle 2-3 kata sinkron Whisper, musik prosedural ditekan saat narasi, -14 LUFS.
Usage: rakit.py <folder proyek>   -> <folder>/<judul>.mp4 (1080x1920, 30 fps)"""
import json, os, re, subprocess, sys, time
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lafal import lafal

W, H, FPS = 1080, 1920, 30
LEAD, TAIL = 0.4, 1.4            # jeda sebelum narasi pertama / setelah narasi terakhir (detik)
FONT = "/System/Library/Fonts/Avenir Next.ttc"
HEAVY, BOLD = 8, 0
KUNING = (255, 214, 64, 255)
# nama bagian naskah yang kadang ditulis Gemma sebagai label: bukan untuk penonton, tidak ditampilkan
LABEL_INTERNAL = {"hook", "intro", "pembuka", "pembukaan", "penutup", "pertanyaan", "kesimpulan", "cta",
                  "outro", "call to action", "closing", "opening", "question", "conclusion", "ajakan"}
K = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

P = sys.argv[1]
NASKAH = json.load(open(f"{P}/naskah.json"))
ADG = json.load(open(f"{P}/suara/adegan.json"))
KATA = json.load(open(f"{P}/suara/kata.json"))
TMP = f"{P}/_rakit"; os.makedirs(TMP, exist_ok=True)


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ffmpeg gagal:\n{' '.join(cmd)}\n{r.stderr[-1500:]}")
    return r


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))


def jadwal():
    """Waktu tampil tiap adegan di video final: adegan i mulai saat narasinya mulai, berakhir saat narasi berikutnya mulai."""
    out = []
    for i, a in enumerate(ADG):
        t0 = 0.0 if i == 0 else a["mulai"] + LEAD
        t1 = ADG[i + 1]["mulai"] + LEAD if i + 1 < len(ADG) else a["selesai"] + LEAD + TAIL
        out.append((round(t0 * FPS) / FPS, round(t1 * FPS) / FPS))
    return out


def segmen(i, t0, t1):
    """Video satu adegan, tepat (t1-t0) detik, 1080x1920."""
    key, d = f"s{i:02d}", t1 - t0
    out = f"{TMP}/seg_{key}.mp4"
    klip = f"{P}/klip/{key}.mp4"
    ok = os.path.exists(klip) and json.load(open(f"{P}/klip/status.json")).get(key, {}).get("ok") if os.path.exists(f"{P}/klip/status.json") else False
    enc = ["-r", str(FPS), "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p", "-an", out]
    if ok:
        cd = dur(klip) - 0.15                                  # ujung klip LTX kadang rusak: buang 0,15 dtk
        k = min(max(d / cd, 1.0), 2.0)
        vf = f"trim=end={cd:.3f},setpts=(PTS-STARTPTS)*{k:.4f},"
        vf += ("minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1," if k > 1.03 else "fps=30,")
        vf += "tpad=stop_mode=clone:stop_duration=3,scale=1080:1920:flags=lanczos,unsharp=5:5:0.7"
        sh(["ffmpeg", "-v", "error", "-y", "-i", klip, "-vf", vf, "-t", f"{d:.3f}"] + enc)
        return "AI", k
    img = Image.open(f"{P}/adegan/{key}.png").convert("RGB")
    w, h = img.size
    cw = min(w, round(h * 9 / 16))
    src = f"{TMP}/kb_{key}.png"
    img.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h)).resize((2160, 3840), Image.LANCZOS).save(src)
    n = int(round(d * FPS))
    z = "1.0+0.10*on/{n}" if i % 2 else "1.10-0.10*on/{n}"            # selang-seling maju / mundur
    vf = (f"zoompan=z='{z.format(n=n)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1080x1920:fps={FPS}")
    sh(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", src, "-vf", vf, "-frames:v", str(n)] + enc)
    return "zoom", 1.0


def pecah(teks):
    """Subtitle 2-3 kata; patah di tanda baca."""
    kata, out, cur = teks.split(), [], []
    for j, w in enumerate(kata):
        cur.append(w)
        nxt = kata[j + 1] if j + 1 < len(kata) else ""
        satuan = re.search(r"\d$", w) and 0 < len(nxt) <= 3            # "1.1 kg", "30 %" jangan dipisah
        if re.search(r"[.,!?;:]$", w) or ((len(cur) >= 3 or len(" ".join(cur)) > 16) and not satuan):
            out.append(cur); cur = []
    if cur:
        if len(cur) == 1 and out and len(out[-1]) < 3:
            out[-1] += cur
        else:
            out.append(cur)
    return [" ".join(c) for c in out]


def subtitle():
    """[(t0, t1, teks)] sinkron dengan waktu kata Whisper (dipetakan proporsional ke jumlah kata ucapan)."""
    hasil = []
    for a in ADG:
        chunks = pecah(a["teks"])
        n_ucap = [max(1, len(lafal(c).split())) for c in chunks]
        S = sum(n_ucap)
        wk = KATA.get(a["key"], [])
        pos, waktu = 0, []
        for n in n_ucap:
            if wk:
                q = min(len(wk) - 1, int(round(pos * len(wk) / S)))
                waktu.append(wk[q][1])
            else:
                waktu.append(a["mulai"] + (a["selesai"] - a["mulai"]) * pos / S)
            pos += n
        for j, c in enumerate(chunks):
            t0 = waktu[j] + LEAD
            t1 = (waktu[j + 1] + LEAD) if j + 1 < len(chunks) else a["selesai"] + LEAD + 0.25
            hasil.append((t0, t1, c))
    return hasil


_font = {}


def font(sz, idx=HEAVY):
    if (sz, idx) not in _font:
        _font[(sz, idx)] = ImageFont.truetype(FONT, sz, index=idx)
    return _font[(sz, idx)]


def gradien():
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = g.load()
    for y in range(0, 560):
        a = int(150 * (1 - y / 560) ** 1.6)
        for x in range(W):
            px[x, y] = (0, 0, 0, a)
    for y in range(1080, H):
        a = int(120 * ((y - 1080) / (H - 1080)) ** 1.4)
        for x in range(W):
            px[x, y] = (0, 0, 0, a)
    return g


def teks_tengah(dr, y, s, sz, fill, stroke=8, maxw=980, idx=HEAVY):
    while sz > 40 and dr.textlength(s, font=font(sz, idx)) > maxw:
        sz -= 4
    f = font(sz, idx)
    x = (W - dr.textlength(s, font=f)) / 2
    dr.text((x, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0, 255), anchor="la")
    return sz


def kartu(label, judul, cap, base):
    im = base.copy()
    dr = ImageDraw.Draw(im)
    if label:
        sz = 50
        f = font(sz, HEAVY)
        tw = dr.textlength(label.upper(), font=f)
        x0, y0 = (W - tw) / 2 - 34, 250
        dr.rounded_rectangle((x0, y0, x0 + tw + 68, y0 + 86), radius=43, fill=(255, 214, 64, 235))
        dr.text((W / 2, y0 + 43), label.upper(), font=f, fill=(20, 20, 20, 255), anchor="mm")
    if judul:
        teks_tengah(dr, 380, judul.upper(), 104, (255, 255, 255, 255), stroke=10)
    if cap:
        words = cap.upper().split()
        sz = 84
        while sz > 48 and dr.textlength(" ".join(words), font=font(sz)) > 960:
            sz -= 4
        f = font(sz)
        total = dr.textlength(" ".join(words), font=f)
        x, y = (W - total) / 2, 1250
        for w in words:
            col = KUNING if re.search(r"\d", w) else (255, 255, 255, 255)
            dr.text((x, y), w, font=f, fill=col, stroke_width=9, stroke_fill=(0, 0, 0, 255))
            x += dr.textlength(w + " ", font=f)
    return im


def overlay(jd, subs, total):
    base = gradien()
    judul_sampai = min(3.0, jd[0][1])
    titik = sorted({0.0, total, judul_sampai} | {t for a, b in jd for t in (a, b)} | {t for a, b, _ in subs for t in (a, b)})
    titik = [t for t in titik if 0 <= t <= total]
    cache, lines = {}, ["ffconcat version 1.0"]
    for t0, t1 in zip(titik, titik[1:]):
        if t1 - t0 < 1e-3:
            continue
        m = (t0 + t1) / 2
        lab = next((NASKAH["adegan"][i]["label"] for i, (a, b) in enumerate(jd) if a <= m < b), "")
        if lab.strip().casefold() in LABEL_INTERNAL:
            lab = ""
        cap = next((c for a, b, c in subs if a <= m < b), "")
        jud = NASKAH["judul"] if m < judul_sampai else ""
        key = (lab, jud, cap)
        if key not in cache:
            fn = f"{TMP}/ov_{len(cache):03d}.png"
            kartu(lab, jud, cap, base).save(fn)
            cache[key] = fn
        lines += [f"file '{cache[key]}'", f"duration {t1 - t0:.4f}"]
    lines.append(f"file '{cache[key]}'")
    open(f"{TMP}/overlay.txt", "w").write("\n".join(lines) + "\n")
    return len(cache)


def audio(total):
    musik = f"{TMP}/musik.wav"
    subprocess.run([PY, "-I", f"{K}/musik.py", musik, f"{total:.2f}"], check=True)
    mix = f"{TMP}/mix.wav"
    fc = (f"[0:a]adelay={int(LEAD * 1000)}:all=1,aformat=channel_layouts=stereo,apad=whole_dur={total:.3f},asplit=2[v][sc];"
          f"[1:a]volume=0.30[m];[m][sc]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=450:makeup=1[md];"
          f"[v][md]amix=inputs=2:normalize=0:duration=first[out]")
    sh(["ffmpeg", "-v", "error", "-y", "-i", f"{P}/suara/narasi.wav", "-i", musik, "-filter_complex", fc,
        "-map", "[out]", "-t", f"{total:.3f}", "-ar", "48000", mix])
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", mix, "-af", "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    final = f"{TMP}/audio.wav"
    sh(["ffmpeg", "-v", "error", "-y", "-i", mix, "-af",
        f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
        f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true", "-ar", "48000", final])
    return final


def main():
    t_all = time.time()
    jd = jadwal()
    total = jd[-1][1]
    print(f"Durasi video {total:.1f} dtk, {len(jd)} adegan", flush=True)
    jenis = []
    for i, (t0, t1) in enumerate(jd, 1):
        t = time.time()
        j, k = segmen(i, t0, t1)
        jenis.append(j)
        print(f"  adegan {i}: {t1 - t0:4.1f} dtk  {'video AI' if j == 'AI' else 'gambar+zoom'}"
              f"{'  (diperlambat %.2fx)' % k if k > 1.03 else ''}  [{time.time() - t:.0f} dtk]", flush=True)
    open(f"{TMP}/segmen.txt", "w").write("".join(f"file '{TMP}/seg_s{i:02d}.mp4'\n" for i in range(1, len(jd) + 1)))
    sh(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{TMP}/segmen.txt", "-c", "copy", f"{TMP}/visual.mp4"])
    subs = subtitle()
    n = overlay(jd, subs, total)
    print(f"  subtitle {len(subs)} potong, {n} kartu teks", flush=True)
    aud = audio(total)
    print("  musik + narasi dicampur, -14 LUFS", flush=True)
    nama = re.sub(r'[\\/:*?"<>|!]', "", NASKAH["judul"]).strip() or "Konten"
    out = f"{P}/{nama}.mp4"
    sh(["ffmpeg", "-v", "error", "-y", "-i", f"{TMP}/visual.mp4", "-f", "concat", "-safe", "0", "-i", f"{TMP}/overlay.txt",
        "-i", aud, "-filter_complex", "[1:v]fps=30,format=rgba[ov];[0:v][ov]overlay=0:0:shortest=0:eof_action=repeat,format=yuv420p[v]",
        "-map", "[v]", "-map", "2:a", "-t", f"{total:.3f}", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    print(f"\nVIDEO JADI: {out}\n  {dur(out):.1f} dtk | video AI {jenis.count('AI')}/{len(jenis)} adegan | "
          f"rakit {time.time() - t_all:.0f} dtk", flush=True)


if __name__ == "__main__":
    main()
