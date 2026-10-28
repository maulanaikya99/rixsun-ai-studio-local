#!/bin/bash
# KONTEN OTOMATIS - topik -> video TikTok 1080x1920, 100% AI lokal di Mac ini.
#   konten.sh <ai|cepat> <topik...>
#   ai    = tiap adegan digerakkan LTX-2.3 (±12 mnt/adegan)
#   cepat = gambar FLUX + gerak kamera pelan (tanpa LTX)
# Naskah: otak pilihan (../otak.py, default Gemma 3 12B; OTAK=opencode konten.sh ... untuk sekali jalan) | Suara: OmniVoice (narator wanita 66) + Whisper | Gambar: FLUX.1 schnell | Video: LTX-2.3
# Bisa dilanjutkan: jalankan ulang dengan topik yang sama, tahap yang sudah selesai dilewati.
AI="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"   # folder AI = induk folder studio (portabel)
ROOT="$(dirname "$AI")"
export PATH="$AI/bin:$PATH:/opt/homebrew/bin"            # ffmpeg dari installer RIXSUN (AI/bin) atau Homebrew
K="$AI/studio/konten"
GEMMA_PY="$AI/ltx-2-mlx/.venv/bin/python"
PY="$AI/mflux-venv/bin/python"
MODE="$1"; shift; TOPIK="$*"
NAMA=$(echo "$TOPIK" | sed 's/[\/:*?"<>|]/ /g' | tr -s ' ' | cut -c1-40 | sed 's/ *$//')
P="${PROYEK:-$ROOT/file AI studio/konten/$NAMA}"
mkdir -p "$P"; cd "$P" || exit 1
LOG="$P/proses.log"
VS_DATA=$(sed -n "s/^OMNIVOICE_DATA_DIR=//p" ~/.config/omnivoice/env 2>/dev/null | tr -d "'\"")
VS_OUT="${VS_DATA:-$ROOT/AppData/VoiceStudio/OmniVoice}/outputs"   # VoiceStudio menyimpan salinan tiap take di sini
[ -e "$P/.mulai" ] || touch "$P/.mulai"
printf '\e]0;Konten Otomatis\a'; clear
garis() { echo "=================================================================="; }
tahap() { echo; garis; echo "  $1"; garis; }
gagal() { echo; echo "!! BERHENTI: $1"; echo "   Jalankan lagi dengan topik yang sama untuk melanjutkan."; exit 1; }

{
garis
echo "  KONTEN OTOMATIS (AI lokal)   mode: $MODE"
echo "  Topik : $TOPIK"
echo "  Folder: $P"
echo "  Mulai : $(date '+%d %b %Y %H:%M')"
garis
echo "  Tips: tutup browser & aplikasi berat (RAM 16 GB) selama proses."

tahap "[1/5] NASKAH - otak '$("$GEMMA_PY" -I "$AI/studio/otak.py")' menulis naskah, prompt gambar & gerak"
if [ -f naskah.json ]; then echo "  sudah ada, dilewati"; else
    caffeinate -i "$GEMMA_PY" -I "$K/naskah.py" "$P" "$TOPIK" 2>&1 | grep --line-buffered -v -i -E "warn|deprecat"
    [ -f naskah.json ] || gagal "naskah tidak terbentuk"
fi

tahap "[2/5] SUARA - OmniVoice membaca naskah, Whisper memilih take terbaik"
if [ -f suara/kata.json ]; then echo "  sudah ada, dilewati"; else
    caffeinate -i "$PY" -I "$K/suara.py" "$P" semua 2>&1 | grep --line-buffered -v -i -E "warn|deprecat|generation_config|Loading weights|attention_mask|forced_decoder"
    [ -f suara/kata.json ] || gagal "suara belum lengkap"
    open suara/narasi.wav
fi

tahap "[3/5] GAMBAR - FLUX menggambar tiap adegan (±2,5 mnt/gambar)"
caffeinate -i "$PY" -I "$K/gambar.py" "$P" 2>&1 | grep --line-buffered -v -i -E "warn|deprecat|it/s\]|s/it\]"

if [ "$MODE" = "ai" ]; then
    tahap "[4/5] VIDEO AI - LTX-2.3 menggerakkan tiap gambar (±12 mnt/adegan)"
    caffeinate -i "$PY" -I "$K/video.py" "$P" 2>&1 | grep --line-buffered -v -i -E "warn|deprecat"
else
    tahap "[4/5] VIDEO AI dilewati (mode cepat: gerak kamera pelan)"
fi

tahap "[5/5] RAKIT - musik, subtitle, judul, ekspor MP4"
caffeinate -i "$PY" -I "$K/rakit.py" "$P" 2>&1 | grep --line-buffered -v -i -E "warn|deprecat"
F=$(ls -t "$P"/*.mp4 2>/dev/null | head -1)
[ -n "$F" ] || gagal "rakit gagal"
# Hanya video siap upload yang disimpan: MP4 dipindah ke folder konten, folder proses (gambar, klip, suara,
# naskah, log) dihapus agar SSD tidak penuh. SIMPAN_PROSES=1 konten.sh ... untuk menyimpannya (mis. mau revisi).
if [ "${SIMPAN_PROSES:-0}" != 1 ] && [ -n "$NAMA" ] && [ "$(dirname "$P")" = "$ROOT/file AI studio/konten" ]; then
    TUJUAN="$(dirname "$P")/$(basename "$F")"
    n=2; while [ -e "$TUJUAN" ]; do TUJUAN="$(dirname "$P")/$(basename "$F" .mp4) ($n).mp4"; n=$((n + 1)); done
    [ -d "$VS_OUT" ] && find "$VS_OUT" -type f -newer "$P/.mulai" -delete
    mv "$F" "$TUJUAN" && F="$TUJUAN" && rm -rf "$P" && echo "  File proses dihapus, hanya video yang disimpan."
fi
garis
echo "  SELESAI dalam $(( SECONDS / 3600 )) jam $(( SECONDS % 3600 / 60 )) mnt"
echo "  Video: $F"
garis
open "$F"
} 2>&1 | tee -a "$LOG"
