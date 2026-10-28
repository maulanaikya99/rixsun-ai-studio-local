#!/usr/bin/env python3
"""Ubah teks narasi (angka, mata uang, singkatan) jadi ejaan ucapan bahasa Indonesia untuk TTS.
Isi kalimat tidak diubah; hanya cara bacanya.  lafal("Dirilis 1983, harga $3,995")
-> "Dirilis seribu sembilan ratus delapan puluh tiga, harga tiga ribu sembilan ratus sembilan puluh lima dolar" """
import re

SATUAN = ["", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan", "sepuluh", "sebelas"]
HURUF = dict(a="a", b="be", c="ce", d="de", e="e", f="ef", g="ge", h="ha", i="i", j="je", k="ka", l="el", m="em", n="en",
             o="o", p="pe", q="ki", r="er", s="es", t="te", u="u", v="ve", w="we", x="eks", y="ye", z="zet")
SATUAN_UKUR = {"kg": "kilogram", "g": "gram", "km": "kilometer", "m": "meter", "cm": "sentimeter", "mm": "milimeter",
               "mAh": "mili ampere jam", "MB": "megabita", "GB": "gigabita", "TB": "terabita", "GHz": "gigahertz",
               "MHz": "megahertz", "MP": "megapiksel", "jt": "juta", "rb": "ribu"}
# singkatan yang dibaca sebagai kata, bukan dieja
KATA = {"NASA", "ASEAN", "UNESCO", "WHO", "OPEC", "NATO", "BUMN", "LAN", "RAM", "ROM", "LED", "LCD", "OLED", "SIM", "PIN"}


def terbilang(n):
    n = int(n)
    if n < 0:
        return "minus " + terbilang(-n)
    if n < 12:
        return SATUAN[n] if n else "nol"
    if n < 20:
        return SATUAN[n - 10] + " belas"
    if n < 100:
        return (SATUAN[n // 10] + " puluh " + (SATUAN[n % 10])).strip()
    if n < 200:
        return ("seratus " + (terbilang(n - 100) if n > 100 else "")).strip()
    if n < 1000:
        return (SATUAN[n // 100] + " ratus " + (terbilang(n % 100) if n % 100 else "")).strip()
    if n < 2000:
        return ("seribu " + (terbilang(n - 1000) if n > 1000 else "")).strip()
    for nilai, nama in ((10 ** 12, "triliun"), (10 ** 9, "miliar"), (10 ** 6, "juta"), (1000, "ribu")):
        if n >= nilai:
            return (terbilang(n // nilai) + f" {nama} " + (terbilang(n % nilai) if n % nilai else "")).strip()
    return str(n)


def _angka(s):
    """'3,995' / '3.995' (ribuan) / '1.1' / '1,5' (desimal) -> ucapan"""
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", s):
        return terbilang(re.sub(r"[.,]", "", s))
    m = re.fullmatch(r"(\d+)[.,](\d+)", s)
    if m:
        return terbilang(m.group(1)) + " koma " + " ".join(terbilang(c) for c in m.group(2))
    if s.isdigit():
        return terbilang(s)
    return " ".join(terbilang(p) for p in re.split(r"[.,]+", s) if p)      # bentuk aneh (mis. 1.2.3): baca per bagian


def _eja(tok):
    return " ".join(HURUF.get(c.lower(), c) for c in tok if c.isalnum())


def lafal(teks):
    t = teks.replace("–", "-").replace("—", ", ")
    t = re.sub(r"(?:US)?\$\s?(\d(?:[\d.,]*\d)?)\s*(juta|miliar|ribu)?", lambda m: _angka(m.group(1)) + (" " + m.group(2) if m.group(2) else "") + " dolar", t)
    t = re.sub(r"\bRp\.?\s?(\d(?:[\d.,]*\d)?)\s*(juta|miliar|triliun|ribu)?", lambda m: _angka(m.group(1)) + (" " + m.group(2) if m.group(2) else "") + " rupiah", t)
    t = re.sub(r"(\d(?:[\d.,]*\d)?)\s?%", lambda m: _angka(m.group(1)) + " persen", t)
    t = re.sub(r"(\d+)-an\b", lambda m: terbilang(m.group(1)) + "an", t)
    t = re.sub(r"(\d[\d.,]*\d|\d)\s?(" + "|".join(SATUAN_UKUR) + r")\b", lambda m: _angka(m.group(1)) + " " + SATUAN_UKUR[m.group(2)], t)
    t = re.sub(r"\b(\d+)([a-zA-Z]{1,2})\b", lambda m: terbilang(m.group(1)) + " " + _eja(m.group(2)), t)   # 8000x, 3G, 5G
    t = re.sub(r"\d[\d.,]*\d|\d", lambda m: _angka(m.group(0)), t)
    t = re.sub(r"\b[a-z]?[A-Z]{2,5}s?\b", lambda m: m.group(0) if m.group(0) in KATA else _eja(m.group(0)), t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


if __name__ == "__main__":
    import sys
    for s in sys.argv[1:] or ["Handphone pertama dibuat tahun 1973? Beratnya sekitar 1.1 kg dan hanya 30 menit!",
                               "Motorola DynaTAC 8000x dirilis 1983, harganya $3,995!", "Era 2000-an, kamera dan SMS. HP 5G, iOS."]:
        print(s, "\n ->", lafal(s))
