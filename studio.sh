#!/bin/bash
# Pengendali "AI Lokal" (dipanggil dari aplikasi di Desktop, tampil di Terminal).
#   studio.sh gambar  <tegak|mendatar|kotak> <jumlah> <deskripsi...>
#   studio.sh video   <file gambar> <detik 3|4|5> <deskripsi gerakan...>
#   studio.sh perbesar <file...>
#   studio.sh konten  <ai|cepat> <topik...>   (konten TikTok otomatis, lihat konten/konten.sh)
#   studio.sh otak    [gemma|claude|opencode|genspark|deepseek]   (pilih LLM untuk terjemah & naskah, lihat otak.py)
AI="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # folder AI = induk folder studio (portabel)
ROOT="$(dirname "$AI")"
export PATH="$AI/bin:$PATH:/opt/homebrew/bin"            # ffmpeg dari installer RIXSUN (AI/bin) atau Homebrew
STUDIO="$AI/studio"
HASIL="$ROOT/file AI studio"
LTXPY="$AI/ltx-2-mlx/.venv/bin/python"
mkdir -p "$HASIL"
WAKTU=$(date +%Y%m%d_%H%M%S)
cd "$HASIL" || exit 1
printf '\e]0;AI Lokal\a'; clear

garis() { echo "=================================================================="; }
terjemah() {   # $1 = gambar|video, $2 = teks  -> prompt bahasa Inggris
    echo "[1] Otak '$("$LTXPY" -I "$STUDIO/otak.py")' menerjemahkan & menyempurnakan deskripsi ..." >&2
    "$LTXPY" -I "$STUDIO/terjemah.py" "$1" "$2" 2> >(grep --line-buffered '^!!' >&2)
}
selesai() {
    garis; echo "  SELESAI dalam $(( SECONDS / 60 )) mnt $(( SECONDS % 60 )) dtk"
    echo "  Hasil tersimpan di: SSD ikya MSI / file AI studio"; garis
    echo; echo "Jendela ini boleh ditutup."
}

MODE="$1"; shift
case "$MODE" in
gambar)
    ARAH="$1"; JUMLAH="$2"; shift 2; TEKS="$*"
    case "$ARAH" in mendatar) W=1360; H=768;; kotak) W=1024; H=1024;; *) W=768; H=1360;; esac
    garis; echo "  BUAT GAMBAR (FLUX.1 schnell)  $JUMLAH gambar, ${W}x${H}"; echo "  Deskripsi: $TEKS"; garis
    PROMPT=$(terjemah gambar "$TEKS")
    [ -z "$PROMPT" ] && PROMPT="$TEKS"
    echo "    Prompt: $PROMPT"; echo
    echo "[2] FLUX menggambar ($JUMLAH x ±2,5 mnt) ..."
    for i in $(seq 1 "$JUMLAH"); do
        SEED=$RANDOM
        OUT="gambar_${WAKTU}_$i.png"
        echo "    gambar $i/$JUMLAH (seed $SEED)"
        caffeinate -i "$AI/mflux-venv/bin/mflux-generate" --model "$AI/models/flux-1-schnell-mflux-q4" --base-model schnell \
            --steps 4 --width $W --height $H --seed $SEED --prompt "$PROMPT" --output "$OUT" 2>&1 | grep -vE "^\s*$" | tail -n 3
        [ -f "$OUT" ] && open "$OUT" || echo "    !! gambar $i gagal"
    done
    echo "$TEKS | $PROMPT" > "gambar_${WAKTU}_prompt.txt"
    selesai ;;
video)
    GAMBAR="$1"; DETIK="$2"; shift 2; TEKS="$*"
    case "$DETIK" in 3) F=73;; 5) F=121;; *) F=97;; esac
    LEBAR=$(sips -g pixelWidth "$GAMBAR" | awk '/pixelWidth/{print $2}')
    TINGGI=$(sips -g pixelHeight "$GAMBAR" | awk '/pixelHeight/{print $2}')
    if   [ "$TINGGI" -gt $(( LEBAR * 6 / 5 )) ]; then W=576; H=1024
    elif [ "$LEBAR" -gt $(( TINGGI * 6 / 5 )) ]; then W=1024; H=576
    else W=768; H=768; fi
    garis; echo "  GAMBAR -> VIDEO (LTX-2.3)  ${DETIK} dtk, ${W}x${H}"; echo "  Gambar: $(basename "$GAMBAR")"
    echo "  Gerakan: $TEKS"; garis
    echo "  Perkiraan: ±$(( DETIK * 2 + 2 )) menit. Tutup browser/aplikasi berat agar lebih cepat."; echo
    PROMPT=$(terjemah video "$TEKS")
    [ -z "$PROMPT" ] && PROMPT="$TEKS"
    echo "    Prompt: $PROMPT"; echo
    echo "[2] LTX membuat video (tahap 1 gerakan, tahap 2 menajamkan, lalu decode) ..."
    OUT="$HASIL/video_${WAKTU}.mp4"
    cd "$AI/ltx-2-mlx" && caffeinate -i .venv/bin/ltx-2-mlx generate --distilled --no-audio --low-ram \
        --model "$AI/models/ltx-2.3-mlx-q4" --gemma "$AI/models/gemma-3-12b-it-4bit" \
        --image "$GAMBAR" -H $H -W $W -f $F --frame-rate 24 --seed $RANDOM --prompt "$PROMPT" -o "$OUT"
    [ -f "$OUT" ] && { echo "$TEKS | $PROMPT" > "${OUT%.mp4}_prompt.txt"; open "$OUT"; } || echo "!! video gagal dibuat"
    selesai ;;
konten)
    # Konten TikTok otomatis: berjalan di latar (nohup) agar tidak mati bila jendela ditutup; jendela ini menampilkan lognya.
    MODE_K="$1"; shift; TOPIK="$*"
    NAMA=$(echo "$TOPIK" | sed 's/[\/:*?"<>|]/ /g' | tr -s ' ' | cut -c1-40 | sed 's/ *$//')
    P="$HASIL/konten/$NAMA"; mkdir -p "$P"; touch "$P/proses.log"
    printf '\e]0;Konten Otomatis - %s\a' "$NAMA"
    PROYEK="$P" nohup bash "$STUDIO/konten/konten.sh" "$MODE_K" "$TOPIK" >/dev/null 2>&1 &
    PID=$!
    tail -n 0 -f "$P/proses.log" & TPID=$!
    wait $PID; sleep 2; kill $TPID 2>/dev/null
    echo; echo "Jendela ini boleh ditutup. Video siap upload ada di: file AI studio / konten" ;;
otak)
    bash "$STUDIO/pilih_otak.sh" "$@" ;;
perbesar)
    garis; echo "  PERBESAR GAMBAR 2x (Real-ESRGAN)  $# file"; garis
    echo "  Hasil disimpan di sebelah file asli dengan akhiran _2x.png"; echo
    "$AI/mflux-venv/bin/python" -I "$STUDIO/perbesar.py" "$@"
    selesai ;;
*)
    echo "mode tidak dikenal: $MODE" ;;
esac
