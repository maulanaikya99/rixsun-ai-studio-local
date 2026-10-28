#!/bin/bash
# Pilih otak (LLM) AI Studio Lokal untuk terjemah prompt & naskah konten. Pilihan disimpan di studio/otak.txt.
#   pilih_otak.sh            menu interaktif
#   pilih_otak.sh <nama>     langsung pilih (gemma | claude | opus | opencode | genspark | deepseek)
STUDIO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYO="$(dirname "$STUDIO")/ltx-2-mlx/.venv/bin/python"
NAMA=(gemma claude opus opencode genspark deepseek)
KET=("Gemma 3 12B - lokal, gratis, offline"
     "Claude Sonnet - lewat Claude Code (kuota langganan Claude)"
     "Claude Opus - lewat Claude Code (paling pintar, kuota lebih cepat habis)"
     "DeepSeek V4.1 Flash GRATIS - dari OpenCode (ada batas pemakaian harian)"
     "DeepSeek V4.1 Flash - lewat proxy Genspark (perlu kredit Genspark berbayar)"
     "DeepSeek V4.1 Flash - lewat API DeepSeek langsung (perlu saldo DeepSeek)")
SEKARANG=$("$PYO" -I "$STUDIO/otak.py" 2>/dev/null)

pilih="$1"
if [ -z "$pilih" ]; then
    printf '\e]0;Pilih Otak AI\a'; clear
    echo "=================================================================="
    echo "  PILIH OTAK AI STUDIO LOKAL   (sekarang: $SEKARANG)"
    echo "  Dipakai untuk: terjemah deskripsi -> prompt, dan naskah Konten Otomatis"
    echo "=================================================================="
    for i in 0 1 2 3 4 5; do
        tanda="  "; [ "${NAMA[$i]}" = "$SEKARANG" ] && tanda="->"
        echo " $tanda $((i + 1)). ${KET[$i]}"
    done
    echo; read -r -p "  Nomor (Enter = batal): " n
    [ -z "$n" ] && exit 0
    pilih="${NAMA[$((n - 1))]}"
    [ -n "$pilih" ] && [ "$n" -ge 1 ] 2>/dev/null || { echo "  nomor tidak dikenal"; exit 1; }
fi
case "$pilih" in gemma|claude|opus|opencode|genspark|deepseek) ;; *) echo "  otak tidak dikenal: $pilih"; exit 1;; esac

if [ "$pilih" != gemma ]; then
    echo; echo "  Menguji koneksi $pilih ..."
    hasil=$("$PYO" -I "$STUDIO/otak.py" tes "$pilih"); ok=$?
    echo "  $hasil"
    if [ $ok -ne 0 ]; then
        echo; echo "  Tetap dipilih: bila gagal saat dipakai, AI Studio otomatis beralih ke Gemma lokal."
    fi
fi
echo "$pilih" > "$STUDIO/otak.txt"
echo; echo "  Otak sekarang: $pilih"
