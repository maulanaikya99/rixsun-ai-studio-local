# RIXSUN AI Studio Local untuk Windows

Berkas DMG hanya berjalan di Mac Apple silicon. Untuk Windows, pasang edisi terpisah dari ZIP repositori.

## Pemasangan

1. Unduh ZIP repositori dari GitHub, lalu ekstrak seluruh folder.
2. Buka folder `windows` dan klik dua kali `install.cmd`.
3. Pilih salah satu profil perangkat. Pemasang menyiapkan Python, FFmpeg, Ollama, PyTorch, dan model teks lokal, lalu membuat pintasan di Desktop.
4. Jalankan aplikasi dari pintasan tersebut. Pembuatan gambar pertama akan mengunduh model dari Hugging Face.

Pemasang memakai WinGet dan memasang aplikasi untuk akun Windows yang sedang digunakan. Koneksi internet diperlukan saat pemasangan dan ketika model gambar pertama kali diunduh.

## Profil perangkat

1. **Standar: GPU NVIDIA RTX dengan VRAM 12 GB atau lebih.** Profil ini direkomendasikan. Gemma 3 12B menulis naskah, sedangkan Stable Diffusion XL membuat gambar adegan dengan detail lebih baik. RAM 32 GB disarankan.
2. **Ringan: GPU NVIDIA dengan VRAM di bawah 12 GB, grafis terintegrasi, atau CPU.** Gemma 3 4B dan SDXL Turbo memakai pengaturan yang lebih ringan. Gambar lebih lambat dan kurang detail, terutama pada CPU. RAM 16 GB merupakan batas minimum praktis.

Kedua profil membuat video dari gambar dengan gerak kamera, narasi, takarir, dan musik. Edisi Windows ini belum membuat klip video AI LTX. Untuk itu, pasang [LTX Desktop](https://github.com/Lightricks/LTX-Desktop/releases/latest) secara terpisah. Pembuatan LTX lokal memerlukan GPU NVIDIA dengan VRAM minimal 24 GB dan RAM 32 GB.

## Fitur

- Membuat video TikTok otomatis: naskah, narasi, gambar adegan, takarir, musik, dan MP4.
- Membuat satu gambar dari deskripsi.
- Memakai suara Windows untuk narasi. Untuk suara kustom, pasang [VoiceStudio](https://github.com/debpalash/VoiceStudio/blob/main/docs/install/windows.md), buat profil suara, lalu masukkan ID profil di tab **Pengaturan**. `omnivoice` adalah nama model, bukan ID profil. Jika belum membuat profil, pilih **Suara Windows lokal**.
- Menyimpan hasil di `Videos\RIXSUN AI Studio`. Jika topik yang sama dijalankan kembali, aplikasi memakai berkas naskah, suara, dan gambar yang sudah ada.

## Persyaratan

- Windows 10 atau 11, 64-bit.
- RAM 16 GB untuk profil Ringan; RAM 32 GB disarankan untuk profil Standar dan LTX.
- GPU NVIDIA RTX disarankan. Pembuatan gambar dengan CPU dapat berlangsung lama.
- Ruang kosong minimal 25 GB untuk aplikasi, paket Python, dan model gambar. Sediakan lebih dari 100 GB jika memasang model video LTX secara terpisah.
- Model diunduh saat pertama kali digunakan. Periksa lisensi model sebelum memakainya untuk keperluan komersial.

## Jika pemasangan bermasalah

- Jika perintah tidak ditemukan setelah pemasangan, tutup PowerShell. Jalankan kembali `windows\install.cmd` dari folder hasil ekstraksi.
- Jika Ollama tidak merespons, buka Ollama dari menu Start.
- Jika model gambar gagal dimuat, perbarui pengandar NVIDIA dan jalankan kembali `windows\install.cmd`.
- Jika suara Bahasa Indonesia belum tersedia, pasang suara tersebut melalui pengaturan Bahasa Windows.
