# RIXSUN AI Studio Local

An AI content studio that runs **100% on your Mac** (Apple Silicon): generate images, turn images into video, upscale images, and create **automatic TikTok videos** from a single topic, complete with script, narrator voice, images, video, music and subtitles.

![RIXSUN AI Studio Local](app/Latar.jpg)

## Download

**[⬇️ RIXSUN-AI-Studio-Local.dmg](https://github.com/maulanaikya99/rixsun-ai-studio-local/releases/latest/download/RIXSUN-AI-Studio-Local.dmg)** (~3 MB). The AI models are downloaded on first launch.

### Requirements
- Mac with Apple silicon (M1/M2/M3/M4). Intel Macs are not supported.
- 16 GB RAM or more.
- ~20 GB (Basic) to ~52 GB (Full) of free disk space. An external SSD is recommended.
- Internet connection for the first-time setup.

### Install
1. Open the DMG and drag **RIXSUN AI STUDIO LOCAL** into **Applications**.
2. First launch: **right-click → Open → Open**. The app is not signed by Apple. If macOS still blocks it, go to System Settings → Privacy & Security → **Open Anyway**.
3. On the **Persiapan** (Setup) screen, choose a location and the packages, then click **Pasang** (Install). A Terminal window opens and downloads everything automatically (1–3 hours). If the connection drops, click Install again; downloads resume where they stopped.
4. Content package only: VoiceStudio opens. Finish its setup wizard, then press Enter in the Terminal window.
5. Done: click **Periksa Lagi** (Check Again).

> The app interface is currently in Indonesian. Menu guide: *Konten TikTok Otomatis* = automatic TikTok content, *Buat Gambar* = create image, *Gambar → Video* = image to video, *Perbesar Gambar* = upscale image, *Otak AI* = AI brain (LLM).

## Features

| Menu | Engine |
|---|---|
| Automatic TikTok content | Script (AI brain) → OmniVoice narrator → Whisper → FLUX → LTX-2.3 → 1080×1920 MP4 |
| Create image | FLUX.1 schnell (MLX, 4-bit) |
| Image → video | LTX-2.3 (MLX, 4-bit) |
| Upscale image | Real-ESRGAN x2 |

### AI brain (writes scripts & prompts)

| Brain | Notes |
|---|---|
| Gemma 3 12B | Local, free, offline (default) |
| Claude Sonnet / Opus | Requires [Claude Code](https://claude.com/claude-code) installed and signed in |
| DeepSeek V4.1 Flash | Free through [OpenCode](https://opencode.ai) (daily limit) |
| DeepSeek via Genspark / API | Requires paid credits |

If an online brain fails (quota used up, no internet), the studio automatically falls back to local Gemma.

## Model licenses

Models are downloaded directly from their official sources and are subject to their own licenses:
FLUX.1 schnell (Apache-2.0), Gemma 3 (Gemma Terms of Use), LTX-2.3 (LTX-2 Community License),
Whisper (MIT), Real-ESRGAN (BSD-3), [VoiceStudio](https://github.com/debpalash/VoiceStudio) (AGPL-3.0),
OmniVoice (**CC-BY-NC, non-commercial**). Check each license before using the output commercially.

## Layout

```
studio.sh          controller (gambar | video | perbesar | konten | otak)
otak.py            LLM selector (gemma, claude, opus, opencode, genspark, deepseek)
terjemah.py        Indonesian description -> English prompt
perbesar.py        Real-ESRGAN x2
konten/            automatic content pipeline (script, voice, image, video, assembly)
app/AIStudio.swift SwiftUI app
app/build.sh       builds the app; `build.sh dmg` creates the installer
app/pasang/        setup.sh (new-Mac installer) + mflux-req.txt
```
