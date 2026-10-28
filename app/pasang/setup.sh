#!/bin/bash
# RIXSUN AI STUDIO LOCAL installer for another Mac (Apple silicon). Run by the app (Setup screen) in Terminal.
#   setup.sh <install folder> <packages...>      packages: dasar (basic) video konten (content)
# Safe to re-run: finished parts are skipped, model downloads resume where they stopped.
ROOT="${1%/}"; shift; PAKET=" $* "
PAY="$(cd "$(dirname "$0")" && pwd)"           # isi aplikasi: studio/, tts/
AI="$ROOT/AI"
KONFIG="$HOME/Library/Application Support/RIXSUN AI Studio"
export UV_PYTHON_INSTALL_DIR="$AI/python" UV_CACHE_DIR="$AI/uv-cache" HF_HOME="$AI/hf-cache" HF_XET_HIGH_PERFORMANCE=1
FF="https://ffmpeg.martin-riedl.de/download/macos/arm64/1789931890_9.0.2"
VS_DMG="https://github.com/debpalash/VoiceStudio/releases/download/v0.5.6/VoiceStudio-Electron-0.5.6-mac-arm64.dmg"
LTX_SHA="9e4a1a54194460547a103334b5e06382724fbba6"

printf '\e]0;Install RIXSUN AI Studio\a'; clear
garis() { echo "=================================================================="; }
tahap() { echo; garis; echo "  $1"; garis; }
gagal() { echo; echo "!! FAILED: $1"; echo "   Check your internet connection, then click Install (Pasang) again in the app. It resumes where it stopped."; exit 1; }
ada() { [[ "$PAKET" == *" $1 "* ]]; }

garis
echo "  INSTALL RIXSUN AI STUDIO LOCAL"
echo "  Folder  : $ROOT"
echo "  Packages:$PAKET"
garis

# ---- cek Mac ----
[ "$(uname -m)" = arm64 ] || gagal "requires a Mac with Apple silicon (M1/M2/M3/M4). Intel Macs are not supported."
RAM=$(( $(sysctl -n hw.memsize) / 1073741824 ))
[ "$RAM" -lt 16 ] && echo "  WARNING: ${RAM} GB RAM. 16 GB or more is recommended (FLUX/LTX may be very slow)."
mkdir -p "$AI/models" "$AI/bin" "$ROOT/file AI studio" || gagal "cannot write to $ROOT"
BUTUH=20; ada video && BUTUH=$((BUTUH + 20)); ada konten && BUTUH=$((BUTUH + 12))
KOSONG=$(df -g "$ROOT" | awk 'NR==2{print $4}')
echo "  RAM ${RAM} GB, free space ${KOSONG} GB, estimated need ~${BUTUH} GB"
[ "$KOSONG" -lt "$BUTUH" ] && gagal "not enough disk space (need ~${BUTUH} GB, have ${KOSONG} GB)"

tahap "[1/6] Copy studio scripts"
rsync -a --exclude otak.txt "$PAY/studio/" "$AI/studio/" && rsync -a "$PAY/tts/" "$AI/tts/" || gagal "copy scripts"
[ -f "$AI/studio/otak.txt" ] || echo gemma > "$AI/studio/otak.txt"
chmod +x "$AI/studio/"*.sh "$AI/studio/konten/"*.sh
echo "  OK"

tahap "[2/6] uv & Python"
UV=$(command -v uv || echo "$HOME/.local/bin/uv")
if [ ! -x "$UV" ]; then
    curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh || gagal "install uv"
    UV="$HOME/.local/bin/uv"
fi
"$UV" --version

tahap "[3/6] Python environments (FLUX, Whisper, Real-ESRGAN, Gemma, LTX)"
if [ ! -x "$AI/mflux-venv/bin/mflux-generate" ]; then
    "$UV" venv --python 3.12.15 "$AI/mflux-venv" || gagal "venv mflux"
    # versi persis dari Mac pembuat yang sudah terbukti jalan (mflux 0.22, torch 2.14.1, transformers 5.19, ...)
    "$UV" pip install --python "$AI/mflux-venv/bin/python" -r "$PAY/mflux-req.txt" || gagal "paket mflux"
else echo "  mflux-venv already installed"; fi
if [ ! -x "$AI/ltx-2-mlx/.venv/bin/ltx-2-mlx" ]; then
    mkdir -p "$AI/ltx-2-mlx"
    curl -L --fail "https://codeload.github.com/dgrauet/ltx-2-mlx/tar.gz/$LTX_SHA" | tar xz --strip-components 1 -C "$AI/ltx-2-mlx" \
        || gagal "download ltx-2-mlx"
    (cd "$AI/ltx-2-mlx" && "$UV" sync --frozen --python 3.11) || gagal "ltx-2-mlx environment"
else echo "  ltx-2-mlx already installed"; fi

tahap "[4/6] ffmpeg"
if command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null; then echo "  already installed: $(command -v ffmpeg)"
else
    for f in ffmpeg ffprobe; do
        [ -x "$AI/bin/$f" ] && continue
        curl -L --fail -o "$AI/bin/$f.zip" "$FF/$f.zip" || gagal "download $f"
        want=$(curl -sL "$FF/$f.zip.sha256" | awk '{print $1}')
        [ "$(shasum -a 256 "$AI/bin/$f.zip" | awk '{print $1}')" = "$want" ] || gagal "checksum mismatch for $f"
        unzip -o -q "$AI/bin/$f.zip" -d "$AI/bin" && rm "$AI/bin/$f.zip" && chmod +x "$AI/bin/$f"
    done
    "$AI/bin/ffmpeg" -version | head -1
fi

tahap "[5/6] AI models (from HuggingFace; this can take a while and resumes if interrupted)"
HF="$AI/mflux-venv/bin/hf"
unduh() { echo; echo "  -> $1"; "$HF" download "$@" || gagal "download model $1"; }
unduh mflux-community/flux-1-schnell-mflux-q4 --local-dir "$AI/models/flux-1-schnell-mflux-q4"
unduh mlx-community/gemma-3-12b-it-4bit --local-dir "$AI/models/gemma-3-12b-it-4bit"
if [ ! -s "$AI/models/realesrgan/RealESRGAN_x2plus.pth" ]; then
    mkdir -p "$AI/models/realesrgan"
    curl -L --fail -o "$AI/models/realesrgan/RealESRGAN_x2plus.pth" \
        https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth || gagal "download Real-ESRGAN"
fi
if ada video || ada konten; then
    unduh dgrauet/ltx-2.3-mlx-q4 --local-dir "$AI/models/ltx-2.3-mlx-q4" \
        --include "config.json" "embedded_config.json" "quantize_config.json" "split_model.json" "LICENSE" "README.md" \
                  "transformer-distilled-1.1.safetensors" "connector.safetensors" "vae_encoder.safetensors" \
                  "vae_decoder.safetensors" "spatial_upscaler_x2_v1_1.safetensors" "spatial_upscaler_x2_v1_1_config.json"
fi
ada konten && unduh openai/whisper-large-v3-turbo --local-dir "$AI/models/whisper-large-v3-turbo" \
    --include "*.json" "*.txt" "model.safetensors"

tahap "[6/6] Narrator voice (VoiceStudio + OmniVoice)"
if ada konten; then
    VS=""; for a in "$ROOT/application/VoiceStudio.app" /Applications/VoiceStudio.app; do [ -d "$a" ] && VS="$a"; done
    if [ -z "$VS" ]; then
        VS="$ROOT/application/VoiceStudio.app"; mkdir -p "$ROOT/application"
        curl -L --fail -o "$ROOT/application/VoiceStudio.dmg" "$VS_DMG" || gagal "download VoiceStudio"
        M=$(hdiutil attach -nobrowse -readonly "$ROOT/application/VoiceStudio.dmg" | awk -F'\t' '/\/Volumes\//{print $NF; exit}')
        ditto "$M/VoiceStudio.app" "$VS" && hdiutil detach -quiet "$M" && rm "$ROOT/application/VoiceStudio.dmg" || gagal "install VoiceStudio"
    fi
    if [ ! -f "$HOME/.config/omnivoice/env" ]; then
        mkdir -p "$HOME/.config/omnivoice" "$ROOT/AppData/VoiceStudio/OmniVoice"
        printf "OMNIVOICE_DATA_DIR='%s'\nOMNIVOICE_CACHE_DIR='%s'\n" "$ROOT/AppData/VoiceStudio/OmniVoice" "$AI/hf-cache/hub" > "$HOME/.config/omnivoice/env"
        chmod 600 "$HOME/.config/omnivoice/env"
    fi
    if curl -s -m 5 http://localhost:3900/health | grep -q '"status"'; then echo "  VoiceStudio is already running"
    else
        open -a "$VS"
        echo; echo "  VoiceStudio is open. Finish its first-run wizard (installs its runtime, ~4 GB),"
        echo "  then come back to this window and press Enter."; read -r
    fi
    for _ in $(seq 60); do curl -s -m 5 http://localhost:3900/health | grep -q '"status"' && break; sleep 5; done
    curl -s -m 30 -X POST http://localhost:3900/models/install -H "Content-Type: application/json" \
        -d '{"repo_id":"k2-fsa/OmniVoice"}' >/dev/null \
        && echo "  VoiceStudio is installing the OmniVoice model (~3.3 GB). Watch the progress in the VoiceStudio app." \
        || echo "  !! Install the OmniVoice model manually in VoiceStudio: Models -> OmniVoice -> Install"
else echo "  skipped (Content package not selected)"; fi

mkdir -p "$KONFIG" && echo "$AI" > "$KONFIG/root.txt"
echo; garis
echo "  DONE. Go back to RIXSUN AI Studio Local and click Periksa Lagi (Check Again). All menus are ready."
command -v claude >/dev/null || echo "  Optional: the Claude/Opus brain needs Claude Code (https://claude.com/claude-code), then sign in."
command -v opencode >/dev/null || echo "  Optional: the free DeepSeek brain needs OpenCode: curl -fsSL https://opencode.ai/install | bash"
garis
