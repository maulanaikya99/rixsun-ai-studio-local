"""RIXSUN AI Studio Local — Windows edition."""
import json
import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

APP_ROOT = Path(__file__).resolve().parent.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from windows.pipeline import detect_vram_gb, generate_single_image, run_pipeline

APPDATA = Path(os.environ.get("APPDATA", Path.home())) / "RIXSUN AI Studio"
CONFIG_PATH = APPDATA / "config.json"
DEFAULT_OUTPUT = Path.home() / "Videos" / "RIXSUN AI Studio"


def load_config():
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {"profile": "lite", "output_root": str(DEFAULT_OUTPUT), "tts_backend": "sapi"}


def save_config(config):
    APPDATA.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


class StudioApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RIXSUN AI Studio Local (Windows)")
        self.geometry("920x720")
        self.minsize(800, 620)
        self.config_data = load_config()
        vram = detect_vram_gb()
        if "profile" not in self.config_data or self.config_data["profile"] not in ("standard", "lite"):
            self.config_data["profile"] = "standard" if vram >= 12 else "lite"
        self.profile = tk.StringVar(value=self.config_data.get("profile", "lite"))
        self.topic = tk.StringVar()
        self.output_root = tk.StringVar(value=self.config_data.get("output_root", str(DEFAULT_OUTPUT)))
        self.tts_backend = tk.StringVar(value=self.config_data.get("tts_backend", "sapi"))
        self.voice_profile = tk.StringVar(value=self.config_data.get("voice_profile", ""))
        self.tts_model = tk.StringVar(value=self.config_data.get("tts_model", "omnivoice"))
        self.tts_base_url = tk.StringVar(value=self.config_data.get("tts_base_url", "http://127.0.0.1:3900"))
        self.image_prompt = tk.StringVar()
        self.image_path = tk.StringVar(value=str(Path(self.output_root.get()) / "gambar.png"))
        self.busy = False
        self._build(vram)

    def _build(self, vram):
        head = ttk.Frame(self, padding=(18, 14))
        head.pack(fill="x")
        ttk.Label(head, text="RIXSUN AI STUDIO LOCAL", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(head, text="Edisi Windows: AI lokal dengan Ollama dan PyTorch", foreground="#555").pack(anchor="w", pady=(3, 0))
        ttk.Label(head, text=f"GPU NVIDIA terdeteksi: VRAM {vram} GB" if vram else "GPU NVIDIA tidak terdeteksi. Pembuatan gambar akan lebih lambat.", foreground="#555").pack(anchor="w", pady=(5, 0))

        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        self.content_tab = ttk.Frame(tabs, padding=16)
        self.image_tab = ttk.Frame(tabs, padding=16)
        self.settings_tab = ttk.Frame(tabs, padding=16)
        tabs.add(self.content_tab, text="Konten otomatis")
        tabs.add(self.image_tab, text="Buat gambar")
        tabs.add(self.settings_tab, text="Pengaturan")
        self._build_content()
        self._build_image()
        self._build_settings()

        self.log = scrolledtext.ScrolledText(self, height=10, wrap="word", state="disabled", font=("Consolas", 9))
        self.log.pack(fill="both", expand=False, padx=16, pady=(0, 10))
        self.status = tk.StringVar(value="Siap")
        ttk.Label(self, textvariable=self.status, anchor="w", padding=(18, 4)).pack(fill="x")

    def _build_content(self):
        frame = self.content_tab
        ttk.Label(frame, text="Pilih profil berdasarkan GPU", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Radiobutton(frame, text="1. Standar: GPU NVIDIA RTX dengan VRAM 12 GB+ (direkomendasikan)", variable=self.profile,
                        value="standard", command=self._profile_changed).pack(anchor="w", pady=(8, 0))
        ttk.Label(frame, text="Gemma 3 12B menulis naskah, sedangkan SDXL membuat gambar beresolusi lebih tinggi. RAM 32 GB disarankan. Untuk video LTX lokal, siapkan GPU dengan VRAM minimal 24 GB dan RAM 32 GB.", wraplength=840, foreground="#555").pack(anchor="w", padx=(24, 0))
        ttk.Radiobutton(frame, text="2. Ringan: GPU NVIDIA dengan VRAM di bawah 12 GB, grafis terintegrasi, atau CPU", variable=self.profile,
                        value="lite", command=self._profile_changed).pack(anchor="w", pady=(12, 0))
        ttk.Label(frame, text="Gemma 3 4B dan SDXL Turbo memakai pengaturan yang lebih ringan. RAM 16 GB disarankan. Gambar lebih lambat dan kurang detail, terutama pada CPU. Video memakai gerak kamera.", wraplength=840, foreground="#555").pack(anchor="w", padx=(24, 0))
        ttk.Label(frame, text="Topik video", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(18, 4))
        ttk.Entry(frame, textvariable=self.topic).pack(fill="x")
        ttk.Label(frame, text="Folder hasil", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(12, 4))
        row = ttk.Frame(frame)
        row.pack(fill="x")
        ttk.Entry(row, textvariable=self.output_root).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Pilih…", command=self._choose_output).pack(side="left", padx=(8, 0))
        ttk.Label(frame, text="Narator", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(12, 4))
        row = ttk.Frame(frame)
        row.pack(fill="x")
        ttk.Radiobutton(row, text="Suara Windows lokal", variable=self.tts_backend, value="sapi").pack(side="left")
        ttk.Radiobutton(row, text="VoiceStudio", variable=self.tts_backend, value="voicestudio").pack(side="left", padx=(18, 0))
        ttk.Label(frame, text="Video memakai gambar dengan gerak kamera, musik, dan takarir. Untuk membuat klip LTX lokal, pasang LTX Desktop secara terpisah. Siapkan GPU NVIDIA dengan VRAM minimal 24 GB dan RAM 32 GB.", wraplength=840, foreground="#555").pack(anchor="w", pady=(10, 0))
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=(14, 0))
        self.content_button = ttk.Button(row, text="Buat video otomatis", command=self._start_content)
        self.content_button.pack(side="left")
        ttk.Button(row, text="Buka folder hasil", command=self._open_output).pack(side="left", padx=8)
        ttk.Button(row, text="Panduan LTX Desktop", command=lambda: webbrowser.open("https://github.com/Lightricks/LTX-Desktop/releases/latest")).pack(side="right")

    def _build_image(self):
        frame = self.image_tab
        ttk.Label(frame, text="Deskripsi gambar", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Entry(frame, textvariable=self.image_prompt).pack(fill="x", pady=(4, 12))
        ttk.Label(frame, text="Simpan sebagai", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=(4, 12))
        ttk.Entry(row, textvariable=self.image_path).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Pilih…", command=self._choose_image_path).pack(side="left", padx=(8, 0))
        ttk.Button(frame, text="Buat gambar", command=self._start_image).pack(anchor="w")
        ttk.Label(frame, text="Model gambar diunduh otomatis saat pertama kali dipakai. Pastikan koneksi internet aktif dan sediakan ruang disk yang cukup.", wraplength=840, foreground="#555").pack(anchor="w", pady=(10, 0))

    def _build_settings(self):
        frame = self.settings_tab
        ttk.Label(frame, text="VoiceStudio lokal", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Opsional. Isi alamat server dan ID profil suara yang sudah dibuat di VoiceStudio. Jika kosong, aplikasi memakai suara Windows.", wraplength=840, foreground="#555").pack(anchor="w", pady=(4, 10))
        self._setting_row(frame, "Alamat API", self.tts_base_url)
        self._setting_row(frame, "Model suara", self.tts_model)
        self._setting_row(frame, "ID profil suara", self.voice_profile)
        ttk.Button(frame, text="Panduan VoiceStudio Windows", command=lambda: webbrowser.open("https://github.com/debpalash/VoiceStudio/blob/main/docs/install/windows.md")).pack(anchor="w", pady=(10, 0))
        ttk.Button(frame, text="Simpan pengaturan", command=self._save).pack(anchor="w", pady=(16, 0))

    @staticmethod
    def _setting_row(parent, label, variable):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text=label, width=22).pack(side="left")
        ttk.Entry(row, textvariable=variable).pack(side="left", fill="x", expand=True)

    def _profile_changed(self):
        self.config_data["profile"] = self.profile.get()
        self._save()
        model = "gemma3:12b" if self.profile.get() == "standard" else "gemma3:4b"

        def ensure_model():
            executable = shutil.which("ollama")
            if not executable:
                self.after(0, self._append, "Ollama tidak ditemukan. Jalankan kembali install.cmd.")
                return
            listed = subprocess.run([executable, "list"], capture_output=True, text=True)
            if listed.returncode == 0 and model in listed.stdout:
                self.after(0, self._append, f"Model {model} sudah tersedia.")
                return
            self.after(0, self._append, f"Mengunduh model {model} untuk profil ini...")
            pulled = subprocess.run([executable, "pull", model], capture_output=True, text=True)
            if pulled.returncode == 0:
                self.after(0, self._append, f"Model {model} siap digunakan.")
            else:
                detail = (pulled.stderr or pulled.stdout).strip()[-400:]
                self.after(0, self._append, f"Gagal mengunduh {model}: {detail}")

        threading.Thread(target=ensure_model, daemon=True).start()

    def _save(self):
        self.config_data.update({
            "profile": self.profile.get(),
            "output_root": self.output_root.get().strip(),
            "tts_backend": self.tts_backend.get(),
            "voice_profile": self.voice_profile.get().strip(),
            "tts_model": self.tts_model.get().strip(),
            "tts_base_url": self.tts_base_url.get().strip(),
        })
        save_config(self.config_data)
        self.status.set("Pengaturan tersimpan")

    def _choose_output(self):
        path = filedialog.askdirectory(initialdir=self.output_root.get() or str(DEFAULT_OUTPUT))
        if path:
            self.output_root.set(path)
            self._save()

    def _choose_image_path(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")], initialfile="gambar.png")
        if path:
            self.image_path.set(path)

    def _open_output(self):
        path = Path(self.output_root.get()).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(path)

    def _append(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")
        self.status.set(text[:120])

    def _start_content(self):
        topic = self.topic.get().strip()
        if not topic:
            messagebox.showinfo("Topik belum diisi", "Isi topik video dulu.")
            return
        if self.busy:
            return
        if self.tts_backend.get() == "voicestudio" and not self.voice_profile.get().strip():
            messagebox.showinfo("VoiceStudio", "Isi Voice profile ID di tab Pengaturan, atau pilih Suara Windows lokal.")
            return
        self._save()
        self._start_worker("content", topic)

    def _start_image(self):
        prompt = self.image_prompt.get().strip()
        if not prompt:
            messagebox.showinfo("Deskripsi belum diisi", "Isi deskripsi gambar dulu.")
            return
        if self.busy:
            return
        self._save()
        self._start_worker("image", prompt)

    def _start_worker(self, kind, value):
        self.busy = True
        self.content_button.configure(state="disabled")
        self.status.set("Proses berjalan…")
        config = dict(self.config_data)
        output_root = self.output_root.get()
        image_path = self.image_path.get()
        profile = self.profile.get()

        def work():
            try:
                if kind == "content":
                    result = run_pipeline(value, output_root, config,
                                          callback=lambda message: self.after(0, self._append, message))
                else:
                    result = generate_single_image(value, image_path, profile,
                                                   callback=lambda message: self.after(0, self._append, message))
                self.after(0, self._append, f"Selesai: {result}")
            except Exception as exc:
                self.after(0, self._append, f"Gagal: {exc}")
                self.after(0, messagebox.showerror, "Proses gagal", str(exc))
            finally:
                self.after(0, self._finished)

        threading.Thread(target=work, daemon=True).start()

    def _finished(self):
        self.busy = False
        self.content_button.configure(state="normal")


def main():
    StudioApp().mainloop()


if __name__ == "__main__":
    main()
