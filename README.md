# RIXSUN AI Studio Local

Studio konten AI yang berjalan **100% di Mac** (Apple Silicon): buat gambar, gerakkan gambar jadi video, perbesar gambar, dan buat **video TikTok otomatis** dari sebuah topik, lengkap dengan naskah, narator, gambar, video, musik, dan subtitle.

![RIXSUN AI Studio Local](app/Latar.jpg)

## Unduh

**[⬇️ RIXSUN-AI-Studio-Local.dmg](https://github.com/maulanaikya99/rixsun-ai-studio-local/releases/latest)** (±3 MB). Model AI diunduh saat pertama kali dibuka.

### Syarat
- Mac chip Apple (M1/M2/M3/M4). Mac Intel tidak didukung.
- RAM 16 GB atau lebih.
- Ruang kosong ±20 GB (Dasar) sampai ±52 GB (Lengkap). SSD eksternal disarankan.
- Internet untuk pemasangan pertama.

### Pasang
1. Buka DMG, seret **RIXSUN AI STUDIO LOCAL** ke **Applications**.
2. Pertama kali dibuka: **klik kanan → Open → Open**. Aplikasi ini tidak ditandatangani Apple. Bila tetap diblokir: System Settings → Privacy & Security → **Open Anyway**.
3. Di layar **Persiapan**, pilih lokasi dan paket, lalu klik **Pasang**. Terminal terbuka dan mengunduh semuanya otomatis (1–3 jam). Bila terputus, klik Pasang lagi; unduhan dilanjutkan.
4. Paket Konten: VoiceStudio terbuka. Selesaikan wizard-nya, lalu tekan Enter di Terminal.
5. Selesai: klik **Periksa Lagi**.

## Fitur

| Menu | Mesin |
|---|---|
| Konten TikTok Otomatis | Naskah (otak AI) → narator OmniVoice → Whisper → FLUX → LTX-2.3 → rakit MP4 1080×1920 |
| Buat Gambar | FLUX.1 schnell (MLX, 4-bit) |
| Gambar → Video | LTX-2.3 (MLX, 4-bit) |
| Perbesar Gambar | Real-ESRGAN x2 |

### Otak AI (penulis naskah & prompt)

| Otak | Keterangan |
|---|---|
| Gemma 3 12B | Lokal, gratis, offline (bawaan) |
| Claude Sonnet / Opus | Perlu [Claude Code](https://claude.com/claude-code) terpasang & login |
| DeepSeek V4.1 Flash | Gratis lewat [OpenCode](https://opencode.ai) (ada batas harian) |
| DeepSeek via Genspark / API | Perlu kredit berbayar |

Bila otak online gagal (kuota habis, tanpa internet), studio otomatis kembali ke Gemma lokal.

## Lisensi model

Model diunduh langsung dari sumber resminya dan tunduk pada lisensinya masing-masing:
FLUX.1 schnell (Apache-2.0), Gemma 3 (Gemma Terms of Use), LTX-2.3 (LTX-2 Community License),
Whisper (MIT), Real-ESRGAN (BSD-3), [VoiceStudio](https://github.com/debpalash/VoiceStudio) (AGPL-3.0),
OmniVoice (**CC-BY-NC, non-komersial**). Periksa lisensi sebelum memakai hasilnya untuk keperluan komersial.

## Struktur

```
studio.sh          pengendali (gambar | video | perbesar | konten | otak)
otak.py            pemilih LLM (gemma, claude, opus, opencode, genspark, deepseek)
terjemah.py        deskripsi Indonesia -> prompt Inggris
perbesar.py        Real-ESRGAN x2
konten/            pipeline konten otomatis (naskah, suara, gambar, video, rakit)
app/AIStudio.swift aplikasi SwiftUI
app/build.sh       bangun aplikasi; `build.sh dmg` membuat installer
app/pasang/        setup.sh (pemasang Mac baru) + mflux-req.txt
```
