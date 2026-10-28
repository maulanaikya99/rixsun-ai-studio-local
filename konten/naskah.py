#!/usr/bin/env python3
"""Tahap 1 - otak pilihan (Gemma 3 12B lokal / DeepSeek V4.1 Flash, lihat ../otak.py) menulis naskah video TikTok.
Anti-ngawur: (1) RISET - Gemma membuat kata kunci, skrip mengambil ringkasan artikel Wikipedia (id + en) sebagai
referensi; (2) NASKAH - Gemma menulis hanya dengan fakta spesifik dari referensi; (3) CEK FAKTA - Gemma memeriksa
tiap narasi terhadap referensi dan menulis ulang klaim yang tidak didukung jadi kalimat umum.
Usage: naskah.py <folder proyek> <topik...>   -> <folder>/naskah.json (+ referensi.txt, cek_fakta.json)"""
import json, os, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from otak import Otak, PILIHAN

N = int(os.environ.get("ADEGAN", "8"))
REF_MAX = 6000                     # huruf referensi yang diberikan ke Gemma (konteks & RAM tetap kecil)

KUNCI = """Give Wikipedia search queries for researching this video topic: "{topik}".
Reply with JSON only: {{"id": ["2-3 short Indonesian queries"], "en": ["2-3 short English queries"]}}"""

ATURAN = f"""You are the scriptwriter of a popular Indonesian educational TikTok channel.
Write the script for a vertical video of about 55 seconds on this topic: "{{topik}}".

REFERENCE (from Wikipedia):
{{ref}}

Rules:
- Exactly {N} scenes, in chronological or logical order.
- Scene 1 is a strong hook (surprising fact or question). The last scene closes with a short question or line for the audience.
- "narasi": Bahasa Indonesia, conversational, 1-2 sentences, 12-20 words, factually accurate. Write years and numbers with digits.
- Never invent facts. Any specific name (case, malware, product, company, person), statistic, number or year MUST appear
  in the REFERENCE above. If the reference does not cover something, explain the point in general terms instead.
- "label": short on-screen keyword the viewer reads (a year or topic word), max 3 words. Never a script-section name
  such as Hook, Intro, Pembuka, Penutup, Pertanyaan, Kesimpulan, CTA or Outro.
- "gambar": an English prompt for an image generator, 30-60 words: one clear subject, setting, lighting, camera angle.
  No text, no letters, no logos, no brand names. Screens, signs and documents show only simple icons or abstract
  glowing shapes, never words or messages. At most one person per image. If a person appears in several scenes,
  describe them identically every time (age, ethnicity, hair, clothing).
- "gerak": an English prompt for an image-to-video model, 15-35 words, describing ONLY what moves
  (subject action, hands, light, particles, background) and the camera movement. Present tense.
- "gaya": one English sentence describing the visual style shared by ALL images.
- "judul": a catchy Indonesian title, max 4 words, matching the topic exactly.

Reply with JSON only, no explanation:
{{{{"judul": "...", "gaya": "...", "adegan": [{{{{"label": "...", "narasi": "...", "gambar": "...", "gerak": "..."}}}}]}}}}"""

CEK = """You are a strict fact-checker for an Indonesian educational video.

REFERENCE (from Wikipedia):
{ref}

NARRATION (one line per scene):
{baris}

For every scene, check each specific claim (names of cases/malware/products/companies/people, statistics, numbers,
years, "first/biggest" claims). A claim is supported only if the REFERENCE states it, or it is common general knowledge
(e.g. "antivirus helps protect phones"). For each scene that has an unsupported claim, rewrite the narration in
Bahasa Indonesia so it keeps the same idea in general terms, 12-20 words, conversational, without the unsupported detail.
Reply with JSON only: {{"perbaikan": [{{"adegan": <scene number>, "klaim": "...", "narasi": "<rewritten narration>"}}]}}
Use an empty list if everything is supported."""


def json_dari(teks):
    m = re.search(r"\{.*\}", teks, re.S)
    if not m:
        raise ValueError("tidak ada JSON")
    return json.loads(m.group(0))


def tanya(model, tok, isi, max_tokens, temp=0.0):
    return model.tanya(isi, max_tokens, temp)        # model = Otak, tok tidak dipakai (tanda tangan lama dipertahankan)


def wiki(lang, query, n=2):
    """[(judul, ringkasan)] artikel teratas Wikipedia untuk query (kosong bila offline)."""
    api = f"https://{lang}.wikipedia.org/w/api.php"
    try:
        q = urllib.parse.urlencode(dict(action="query", list="search", srsearch=query, srlimit=n, format="json"))
        req = urllib.request.Request(f"{api}?{q}", headers={"User-Agent": "AIStudioLokal/1.0"})
        hits = json.load(urllib.request.urlopen(req, timeout=15))["query"]["search"]
        out = []
        for h in hits:
            q = urllib.parse.urlencode(dict(action="query", prop="extracts", explaintext=1, exintro=0, exchars=1800,
                                            titles=h["title"], format="json", redirects=1))
            req = urllib.request.Request(f"{api}?{q}", headers={"User-Agent": "AIStudioLokal/1.0"})
            pages = json.load(urllib.request.urlopen(req, timeout=15))["query"]["pages"]
            for pg in pages.values():
                if pg.get("extract"):
                    out.append((f"{lang}: {pg['title']}", pg["extract"].strip()))
        return out
    except Exception as e:                               # noqa: BLE001
        print(f"  wikipedia {lang} '{query}' gagal: {e}", flush=True)
        return []


def riset(model, tok, topik, out_dir):
    try:
        k = json_dari(tanya(model, tok, KUNCI.format(topik=topik), 200))
    except Exception:                                    # noqa: BLE001
        k = {"id": [topik], "en": []}
    artikel, sudah = [], set()
    for lang in ("id", "en"):
        for q in (k.get(lang) or [])[:3]:
            for judul, isi in wiki(lang, q):
                if judul not in sudah:
                    sudah.add(judul); artikel.append((judul, isi))
    teks = "\n\n".join(f"[{j}]\n{isi}" for j, isi in artikel)[:REF_MAX]
    open(os.path.join(out_dir, "referensi.txt"), "w").write(teks or "(tidak ada referensi)")
    print(f"Riset: {len(artikel)} artikel Wikipedia ({', '.join(j for j, _ in artikel[:6])})", flush=True)
    return teks or "(no reference available - use only general, widely known facts; no specific names or numbers)"


def periksa(teks):
    d = json_dari(teks)
    adg = d.get("adegan") or []
    if len(adg) != N:
        raise ValueError(f"jumlah adegan {len(adg)}, harus {N}")
    for i, a in enumerate(adg, 1):
        for k in ("label", "narasi", "gambar", "gerak"):
            if not str(a.get(k, "")).strip():
                raise ValueError(f"adegan {i} tanpa '{k}'")
    for k in ("judul", "gaya"):
        if not str(d.get(k, "")).strip():
            raise ValueError(f"tanpa '{k}'")
    return d


def cek_fakta(model, tok, d, ref, out_dir):
    baris = "\n".join(f"{i}. {a['narasi']}" for i, a in enumerate(d["adegan"], 1))
    try:
        hasil = json_dari(tanya(model, tok, CEK.format(ref=ref, baris=baris), 1500)).get("perbaikan") or []
    except Exception as e:                               # noqa: BLE001
        print(f"  cek fakta gagal dibaca ({e}), naskah dipakai apa adanya", flush=True)
        return
    json.dump(hasil, open(os.path.join(out_dir, "cek_fakta.json"), "w"), indent=1, ensure_ascii=False)
    for p in hasil:
        i, baru = int(p.get("adegan", 0)), str(p.get("narasi", "")).strip()
        if 1 <= i <= N and 8 <= len(baru.split()) <= 26:
            print(f"  CEK FAKTA adegan {i}: '{p.get('klaim', '')}' tidak ada di referensi\n"
                  f"     lama: {d['adegan'][i - 1]['narasi']}\n     baru: {baru}", flush=True)
            d["adegan"][i - 1]["narasi"] = baru
    if not hasil:
        print("  CEK FAKTA: semua klaim didukung referensi", flush=True)


def main():
    out_dir, topik = sys.argv[1], " ".join(sys.argv[2:]).strip()
    model, tok = Otak(), None
    print(f"Otak: {PILIHAN[model.nama]}", flush=True)
    ref = riset(model, tok, topik, out_dir)
    for coba in range(1, 5):
        t = time.time()
        raw = tanya(model, tok, ATURAN.format(topik=topik, ref=ref), 2500, temp=0.0 if coba == 1 else 0.7)
        open(os.path.join(out_dir, f"naskah_mentah_{coba}.txt"), "w").write(raw)
        try:
            d = periksa(raw)
        except Exception as e:                       # noqa: BLE001
            print(f"  percobaan {coba}: JSON belum valid ({e}), {model.nama} menulis ulang ...", flush=True)
            continue
        print(f"Naskah selesai dalam {time.time() - t:.0f} dtk (percobaan {coba}), cek fakta ...", flush=True)
        cek_fakta(model, tok, d, ref, out_dir)
        d["topik"] = topik
        json.dump(d, open(os.path.join(out_dir, "naskah.json"), "w"), indent=1, ensure_ascii=False)
        print(f"\n  JUDUL : {d['judul']}\n  GAYA  : {d['gaya']}\n", flush=True)
        for i, a in enumerate(d["adegan"], 1):
            print(f"  [{i}] {a['label']}\n      {a['narasi']}\n      gambar: {a['gambar']}\n      gerak : {a['gerak']}\n", flush=True)
        return
    sys.exit(f"{model.nama} gagal menghasilkan naskah yang valid setelah 4 percobaan")


if __name__ == "__main__":
    main()
