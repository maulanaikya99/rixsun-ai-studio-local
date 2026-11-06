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
        self.geometry("1120x780")
        self.minsize(980, 680)
        self.config_data = load_config()
        vram = detect_vram_gb()
        self.profile_adjusted = False
        profile = self.config_data.get("profile")
        if profile not in ("standard", "lite"):
            profile = "standard" if vram >= 12 else "lite"
        if vram < 12 and profile == "standard":
            profile = "lite"
            self.profile_adjusted = True
        self.config_data["profile"] = profile
        self.vram = vram
        self.profile = tk.StringVar(value=profile)
        self.topic = tk.StringVar()
        self.output_root = tk.StringVar(value=self.config_data.get("output_root", str(DEFAULT_OUTPUT)))
        self.voice_profile = tk.StringVar(value=self.config_data.get("voice_profile", ""))
        backend = self.config_data.get("tts_backend", "sapi")
        self.voice_backend_adjusted = backend == "voicestudio" and self.voice_profile.get().strip().casefold() in ("", "omnivoice")
        if self.voice_backend_adjusted:
            backend = "sapi"
        self.tts_backend = tk.StringVar(value=backend)
        self.tts_model = tk.StringVar(value=self.config_data.get("tts_model", "omnivoice"))
        self.tts_base_url = tk.StringVar(value=self.config_data.get("tts_base_url", "http://127.0.0.1:3900"))
        self.image_prompt = tk.StringVar()
        self.image_path = tk.StringVar(value=str(Path(self.output_root.get()) / "gambar.png"))
        self.busy = False
        self._build(vram)
        if self.profile_adjusted:
            note = f"GPU NVIDIA memiliki VRAM {vram} GB." if vram else "GPU NVIDIA tidak terdeteksi."
            self._append(f"{note} Profil Ringan dipilih agar sesuai dengan perangkat.")
            self.after(250, self._profile_changed)
        if self.voice_backend_adjusted:
            self.config_data["tts_backend"] = "sapi"
            self._save()
            self._append("VoiceStudio belum memiliki ID profil. Suara Windows lokal dipilih supaya Anda bisa langsung mulai.")

    def _build(self, vram):
        self.configure(background="#10121d")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Root.TFrame", background="#10121d")
        style.configure("Sidebar.TFrame", background="#0b0d16")
        style.configure("Card.TFrame", background="#1b1e2b")
        style.configure("TLabel", background="#10121d", foreground="#f2f3f8", font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background="#10121d", foreground="#a6a9b8", font=("Segoe UI", 9))
        style.configure("Sidebar.TLabel", background="#0b0d16", foreground="#f2f3f8")
        style.configure("SidebarMuted.TLabel", background="#0b0d16", foreground="#888c9d", font=("Segoe UI", 9))
        style.configure("PageTitle.TLabel", background="#10121d", foreground="#ffffff", font=("Segoe UI", 22, "bold"))
        style.configure("PageSub.TLabel", background="#10121d", foreground="#a6a9b8", font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background="#1b1e2b", foreground="#ffffff", font=("Segoe UI", 12, "bold"))
        style.configure("CardBody.TLabel", background="#1b1e2b", foreground="#b8bbca", font=("Segoe UI", 9))
        style.configure("TEntry", fieldbackground="#11141f", foreground="#ffffff", padding=8, borderwidth=1)
        style.configure("TButton", background="#292d3d", foreground="#ffffff", padding=(12, 8), borderwidth=0, font=("Segoe UI", 9, "bold"))
        style.map("TButton", background=[("active", "#393e52"), ("pressed", "#4d3151")], foreground=[("disabled", "#777b89")])
        style.configure("Primary.TButton", background="#c74283", foreground="#ffffff", padding=(18, 10), borderwidth=0, font=("Segoe UI", 10, "bold"))
        style.map("Primary.TButton", background=[("active", "#dc5798"), ("pressed", "#aa3470")])
        style.configure("TRadiobutton", background="#1b1e2b", foreground="#f2f3f8", padding=5, font=("Segoe UI", 9))
        style.map("TRadiobutton", background=[("active", "#1b1e2b")], foreground=[("disabled", "#777b89")])

        shell = ttk.Frame(self, style="Root.TFrame")
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(0, weight=1)
        sidebar = ttk.Frame(shell, style="Sidebar.TFrame", padding=(18, 26))
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.configure(width=235)
        sidebar.grid_propagate(False)
        ttk.Label(sidebar, text="RIXSUN", style="Sidebar.TLabel", font=("Segoe UI Black", 23)).pack(anchor="w")
        ttk.Label(sidebar, text="AI STUDIO LOCAL", style="Sidebar.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 2))
        ttk.Label(sidebar, text="EDISI WINDOWS", style="SidebarMuted.TLabel").pack(anchor="w", pady=(0, 28))
        ttk.Label(sidebar, text="MENU", style="SidebarMuted.TLabel", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 8))
        self.nav_buttons = {}
        for key, label, icon in (("content", "Konten TikTok", "▶"), ("image", "Buat gambar", "▧"), ("settings", "Pengaturan", "⚙")):
            button = tk.Button(
                sidebar, text=f"{icon}   {label}", anchor="w", padx=12, pady=12,
                relief="flat", borderwidth=0, cursor="hand2", font=("Segoe UI", 10, "bold"),
                background="#0b0d16", foreground="#e8e9f0", activebackground="#252033",
                activeforeground="#ffffff", command=lambda page=key: self._show_page(page),
            )
            button.pack(fill="x", pady=3)
            self.nav_buttons[key] = button
        sidebar_bottom = ttk.Frame(sidebar, style="Sidebar.TFrame")
        sidebar_bottom.pack(side="bottom", fill="x")
        ttk.Label(sidebar_bottom, text="AI lokal", style="Sidebar.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        gpu_text = f"GPU NVIDIA · VRAM {vram} GB" if vram else "GPU NVIDIA tidak terdeteksi"
        ttk.Label(sidebar_bottom, text=gpu_text, style="SidebarMuted.TLabel", wraplength=190).pack(anchor="w", pady=(3, 0))
        if 0 < vram < 12:
            ttk.Label(sidebar_bottom, text="Profil Ringan disarankan", style="SidebarMuted.TLabel", wraplength=190).pack(anchor="w", pady=(5, 0))

        main = ttk.Frame(shell, style="Root.TFrame", padding=(28, 24, 28, 18))
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)
        self.page_title = tk.StringVar()
        self.page_subtitle = tk.StringVar()
        ttk.Label(main, textvariable=self.page_title, style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(main, textvariable=self.page_subtitle, style="PageSub.TLabel").grid(row=0, column=0, sticky="w", pady=(38, 0))
        self.page_container = ttk.Frame(main, style="Root.TFrame")
        self.page_container.grid(row=1, column=0, sticky="nsew", pady=(18, 12))
        self.page_container.columnconfigure(0, weight=1)
        self.page_container.rowconfigure(0, weight=1)
        self.content_tab = ttk.Frame(self.page_container, style="Root.TFrame")
        self.image_tab = ttk.Frame(self.page_container, style="Root.TFrame")
        self.settings_tab = ttk.Frame(self.page_container, style="Root.TFrame")
        self.page_frames = {"content": self.content_tab, "image": self.image_tab, "settings": self.settings_tab}
        self._build_content()
        self._build_image()
        self._build_settings()
        for page in self.page_frames.values():
            page.grid(row=0, column=0, sticky="nsew")
        self._show_page("content")

        self.log = scrolledtext.ScrolledText(main, height=7, wrap="word", state="disabled", font=("Consolas", 9),
                                             background="#0b0d16", foreground="#d9dbe5", insertbackground="#ffffff",
                                             selectbackground="#4d3151", relief="flat", borderwidth=0, padx=10, pady=8)
        self.log.grid(row=2, column=0, sticky="ew")
        self.status = tk.StringVar(value="Siap")
        ttk.Label(main, textvariable=self.status, style="Muted.TLabel", anchor="w").grid(row=3, column=0, sticky="ew", pady=(7, 0))

    def _show_page(self, page):
        titles = {
            "content": ("Konten TikTok otomatis", "Buat naskah, narasi, gambar, dan video dari satu topik."),
            "image": ("Buat gambar", "Tulis deskripsi, lalu buat gambar dengan model lokal."),
            "settings": ("Pengaturan", "Atur suara dan folder hasil aplikasi."),
        }
        self.page_title.set(titles[page][0])
        self.page_subtitle.set(titles[page][1])
        self.page_frames[page].tkraise()
        for key, button in self.nav_buttons.items():
            button.configure(background="#252033" if key == page else "#0b0d16",
                             foreground="#ffffff" if key == page else "#b6b8c5")

    @staticmethod
    def _card(parent, title):
        card = ttk.Frame(parent, style="Card.TFrame", padding=16)
        card.pack(fill="x", pady=(0, 12))
        ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w", pady=(0, 10))
        return card

    def _build_content(self):
        frame = self.content_tab
        profile_card = self._card(frame, "Profil perangkat")
        ttk.Radiobutton(profile_card, text="1. Standar: GPU NVIDIA RTX dengan VRAM 12 GB+ (direkomendasikan)", variable=self.profile,
                        value="standard", command=self._profile_changed).pack(anchor="w", pady=(4, 0))
        ttk.Label(profile_card, text="Gemma 3 12B menulis naskah dan SDXL membuat gambar beresolusi lebih tinggi. RAM 32 GB disarankan.", style="CardBody.TLabel", wraplength=800).pack(anchor="w", padx=(24, 0), pady=(2, 5))
        ttk.Radiobutton(profile_card, text="2. Ringan: GPU NVIDIA dengan VRAM di bawah 12 GB, grafis terintegrasi, atau CPU", variable=self.profile,
                        value="lite", command=self._profile_changed).pack(anchor="w", pady=(6, 0))
        ttk.Label(profile_card, text="Gemma 3 4B dan SDXL Turbo memakai pengaturan ringan. RAM 16 GB disarankan. Gambar lebih lambat pada CPU.", style="CardBody.TLabel", wraplength=800).pack(anchor="w", padx=(24, 0), pady=(2, 0))

        topic_card = self._card(frame, "Topik video")
        ttk.Entry(topic_card, textvariable=self.topic).pack(fill="x")

        output_card = self._card(frame, "Folder hasil dan narator")
        row = ttk.Frame(output_card, style="Card.TFrame")
        row.pack(fill="x")
        ttk.Entry(row, textvariable=self.output_root).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Pilih…", command=self._choose_output).pack(side="left", padx=(8, 0))
        ttk.Label(output_card, text="Narator", style="CardBody.TLabel").pack(anchor="w", pady=(12, 4))
        row = ttk.Frame(output_card, style="Card.TFrame")
        row.pack(fill="x")
        ttk.Radiobutton(row, text="Suara Windows lokal", variable=self.tts_backend, value="sapi").pack(side="left")
        ttk.Radiobutton(row, text="VoiceStudio (opsional)", variable=self.tts_backend, value="voicestudio").pack(side="left", padx=(18, 0))
        ttk.Label(output_card, text="VoiceStudio memerlukan ID profil suara di Pengaturan. OmniVoice adalah nama model, bukan ID profil. Suara Windows lokal dapat langsung dipakai.", style="CardBody.TLabel", wraplength=800).pack(anchor="w", pady=(4, 0))

        row = ttk.Frame(frame, style="Root.TFrame")
        row.pack(fill="x", pady=(4, 0))
        self.content_button = ttk.Button(row, text="▶  Buat video otomatis", style="Primary.TButton", command=self._start_content)
        self.content_button.pack(side="left")
        ttk.Button(row, text="Buka folder hasil", command=self._open_output).pack(side="left", padx=8)
        ttk.Button(row, text="Panduan LTX Desktop", command=lambda: webbrowser.open("https://github.com/Lightricks/LTX-Desktop/releases/latest")).pack(side="right")

    def _build_image(self):
        frame = self.image_tab
        card = self._card(frame, "Deskripsi gambar")
        ttk.Entry(card, textvariable=self.image_prompt).pack(fill="x", pady=(0, 12))
        ttk.Label(card, text="Simpan sebagai", style="CardBody.TLabel").pack(anchor="w", pady=(0, 4))
        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill="x")
        ttk.Entry(row, textvariable=self.image_path).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Pilih…", command=self._choose_image_path).pack(side="left", padx=(8, 0))
        ttk.Label(card, text="Model gambar diunduh saat pertama kali digunakan. Sediakan ruang disk yang cukup.", style="CardBody.TLabel", wraplength=800).pack(anchor="w", pady=(10, 0))
        ttk.Button(frame, text="▶  Buat gambar", style="Primary.TButton", command=self._start_image).pack(anchor="w", pady=(2, 0))

    def _build_settings(self):
        frame = self.settings_tab
        card = self._card(frame, "VoiceStudio lokal (opsional)")
        ttk.Label(card, text="Gunakan jika VoiceStudio sudah terpasang dan berjalan. Jika tidak, pilih Suara Windows lokal di halaman Konten TikTok.", style="CardBody.TLabel", wraplength=800).pack(anchor="w", pady=(0, 10))
        self._setting_row(card, "Alamat API", self.tts_base_url)
        self._setting_row(card, "Model suara", self.tts_model)
        self._setting_row(card, "ID profil VoiceStudio", self.voice_profile)
        ttk.Label(card, text="OmniVoice adalah nama mesin suara. Kolom ID profil berisi ID profil yang Anda buat di VoiceStudio.", style="CardBody.TLabel", wraplength=800).pack(anchor="w", pady=(6, 0))
        ttk.Button(frame, text="Panduan VoiceStudio Windows", command=lambda: webbrowser.open("https://github.com/debpalash/VoiceStudio/blob/main/docs/install/windows.md")).pack(anchor="w", pady=(2, 8))
        ttk.Button(frame, text="Simpan pengaturan", style="Primary.TButton", command=self._save).pack(anchor="w")

    @staticmethod
    def _setting_row(parent, label, variable):
        row = ttk.Frame(parent, style="Card.TFrame")
        row.pack(fill="x", pady=4)
        ttk.Label(row, text=label, style="CardBody.TLabel", width=22).pack(side="left")
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
        if self.tts_backend.get() == "voicestudio" and self.voice_profile.get().strip().casefold() in ("", "omnivoice"):
            self.tts_backend.set("sapi")
            self._append("ID profil VoiceStudio belum diisi. Video ini memakai suara Windows lokal. Untuk VoiceStudio, isi ID profil di Pengaturan.")
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
