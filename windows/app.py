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
from PIL import Image, ImageOps, ImageTk

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
        for label, icon in (("Gambar → video", "▣"), ("Perbesar gambar", "⌕")):
            tk.Button(
                sidebar, text=f"{icon}   {label}  ·  belum tersedia", anchor="w", padx=12, pady=11,
                relief="flat", borderwidth=0, font=("Segoe UI", 9), background="#0b0d16",
                foreground="#666b7a", disabledforeground="#666b7a", state="disabled",
            ).pack(fill="x", pady=2)
        support = tk.Button(
            sidebar, text="♥   Dukung developer", anchor="w", padx=12, pady=10,
            relief="flat", borderwidth=0, cursor="hand2", font=("Segoe UI", 9, "bold"),
            background="#4a1d39", foreground="#ffffff", activebackground="#6b2a4d",
            activeforeground="#ffffff", command=lambda: webbrowser.open("https://saweria.co/Rixsun"),
        )
        sidebar_bottom = ttk.Frame(sidebar, style="Sidebar.TFrame")
        ttk.Label(sidebar_bottom, text="OTAK AI", style="SidebarMuted.TLabel", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        brain_name = "Gemma 3 12B" if self.profile.get() == "standard" else "Gemma 3 4B"
        self.brain_label = ttk.Label(sidebar_bottom, text=brain_name, style="Sidebar.TLabel", font=("Segoe UI", 10, "bold"))
        self.brain_label.pack(anchor="w", pady=(2, 2))
        gpu_text = f"GPU NVIDIA · VRAM {vram} GB" if vram else "GPU NVIDIA tidak terdeteksi"
        ttk.Label(sidebar_bottom, text=gpu_text, style="SidebarMuted.TLabel", wraplength=190).pack(anchor="w", pady=(3, 0))
        if 0 < vram < 12:
            ttk.Label(sidebar_bottom, text="Profil Ringan disarankan", style="SidebarMuted.TLabel", wraplength=190).pack(anchor="w", pady=(5, 0))
        side_actions = ttk.Frame(sidebar, style="Sidebar.TFrame")
        side_actions.pack(side="bottom", fill="x", pady=(10, 8))
        tk.Button(side_actions, text="▰  Folder hasil", anchor="w", padx=5, pady=7, relief="flat", borderwidth=0,
                  background="#0b0d16", foreground="#c0c2ce", activebackground="#252033",
                  command=self._open_output).pack(side="left", fill="x", expand=True)
        tk.Button(side_actions, text="⚙", width=3, pady=6, relief="flat", borderwidth=0,
                  background="#252033", foreground="#ffffff", activebackground="#39364d",
                  command=lambda: self._show_page("settings")).pack(side="right")
        sidebar_bottom.pack(side="bottom", fill="x")
        support.pack(side="bottom", fill="x", pady=(0, 12))

        main = ttk.Frame(shell, style="Root.TFrame", padding=(28, 24, 28, 18))
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)
        self.page_title = tk.StringVar()
        self.page_subtitle = tk.StringVar()
        header = ttk.Frame(main, style="Root.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        self.page_icon = tk.Label(header, text="▶", width=2, height=1, font=("Segoe UI Symbol", 20, "bold"),
                                  background="#f05b78", foreground="#ffffff", padx=8, pady=6)
        self.page_icon.pack(side="left", padx=(0, 14))
        title_box = ttk.Frame(header, style="Root.TFrame")
        title_box.pack(side="left", fill="x", expand=True)
        ttk.Label(title_box, textvariable=self.page_title, style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(title_box, textvariable=self.page_subtitle, style="PageSub.TLabel").pack(anchor="w", pady=(2, 0))
        self.page_container = ttk.Frame(main, style="Root.TFrame")
        self.page_container.grid(row=1, column=0, sticky="nsew", pady=(18, 12))
        self.page_container.columnconfigure(0, weight=1)
        self.page_container.rowconfigure(0, weight=1)
        self.content_wrap = ttk.Frame(self.page_container, style="Root.TFrame")
        self.content_wrap.columnconfigure(0, weight=1)
        self.content_wrap.rowconfigure(0, weight=1)
        self.content_tab = tk.Canvas(self.content_wrap, highlightthickness=0, bd=0, bg="#170e2a")
        self.content_tab.grid(row=0, column=0, sticky="nsew")
        self.content_scrollbar = ttk.Scrollbar(self.content_wrap, orient="vertical", command=self.content_tab.yview)
        self.content_scrollbar.grid(row=0, column=1, sticky="ns")
        self.content_tab.configure(yscrollcommand=self.content_scrollbar.set)
        self.image_tab = ttk.Frame(self.page_container, style="Root.TFrame")
        self.settings_wrap = ttk.Frame(self.page_container, style="Root.TFrame")
        self.settings_wrap.columnconfigure(0, weight=1)
        self.settings_wrap.rowconfigure(0, weight=1)
        self.settings_canvas = tk.Canvas(self.settings_wrap, highlightthickness=0, bd=0, bg="#10121d")
        self.settings_canvas.grid(row=0, column=0, sticky="nsew")
        self.settings_scrollbar = ttk.Scrollbar(self.settings_wrap, orient="vertical", command=self.settings_canvas.yview)
        self.settings_scrollbar.grid(row=0, column=1, sticky="ns")
        self.settings_canvas.configure(yscrollcommand=self.settings_scrollbar.set)
        self.settings_tab = ttk.Frame(self.settings_canvas, style="Root.TFrame")
        self.settings_window = self.settings_canvas.create_window((0, 0), window=self.settings_tab, anchor="nw")
        self.settings_tab.bind("<Configure>", lambda _event: self.settings_canvas.configure(scrollregion=self.settings_canvas.bbox("all")))
        self.settings_canvas.bind("<Configure>", lambda event: self.settings_canvas.itemconfigure(self.settings_window, width=event.width))
        self.page_frames = {"content": self.content_wrap, "image": self.image_tab, "settings": self.settings_wrap}
        self._build_content()
        self._build_image()
        self._build_settings()
        for page in self.page_frames.values():
            page.grid(row=0, column=0, sticky="nsew")
        self.content_tab.bind("<MouseWheel>", self._scroll_content)
        self.topic_box.bind("<MouseWheel>", self._scroll_content)
        self.settings_canvas.bind("<MouseWheel>", self._scroll_settings)
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
        self.page_icon.configure(text={"content": "▶", "image": "▧", "settings": "⚙"}[page],
                                 background={"content": "#f05b78", "image": "#aa62eb", "settings": "#397de8"}[page])
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
        self.content_bg = None
        try:
            self.content_bg = Image.open(Path(__file__).with_name("Latar.jpg")).convert("RGB")
        except OSError:
            pass
        self.topic_box = tk.Text(frame, height=3, wrap="word", font=("Segoe UI", 11),
                                 background="#181225", foreground="#ffffff", insertbackground="#ffffff",
                                 relief="flat", borderwidth=0, padx=12, pady=10)
        self.topic_box.bind("<KeyRelease>", self._topic_changed)
        self.topic_placeholder = None
        self.content_button = tk.Button(
            frame, text="▶  Buat konten", command=self._start_content, cursor="hand2",
            relief="flat", borderwidth=0, padx=22, pady=10, font=("Segoe UI", 10, "bold"),
            background="#e34d79", foreground="#ffffff", activebackground="#f56a91", activeforeground="#ffffff",
        )
        self.content_tab.bind("<Configure>", self._draw_content)
        self._draw_content()

    def _topic_changed(self, _event=None):
        self.topic.set(self.topic_box.get("1.0", "end-1c").strip())
        if self.topic_placeholder is not None:
            self.content_tab.itemconfigure(self.topic_placeholder, state="hidden" if self.topic.get() else "normal")

    def _scroll_content(self, event):
        self.content_tab.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _scroll_settings(self, event):
        self.settings_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _round_card(self, canvas, x1, y1, x2, y2, fill="#251633", outline="#ffffff"):
        radius = 16
        points = [x1 + radius, y1, x2 - radius, y1, x2, y1 + radius, x2, y2 - radius,
                  x2 - radius, y2, x1 + radius, y2, x1, y2 - radius, x1, y1 + radius]
        return canvas.create_polygon(points, smooth=True, splinesteps=12, fill=fill, outline=outline, width=1)

    def _draw_content(self, _event=None):
        canvas = self.content_tab
        width, height = max(700, canvas.winfo_width()), max(560, canvas.winfo_height())
        canvas.delete("all")
        if self.content_bg is not None:
            image = ImageOps.fit(self.content_bg, (width, height), method=Image.Resampling.LANCZOS)
            shade = Image.new("RGB", image.size, (12, 7, 27))
            image = Image.blend(image, shade, 0.42)
            self.content_photo = ImageTk.PhotoImage(image)
            canvas.create_image(0, 0, image=self.content_photo, anchor="nw")
        else:
            canvas.configure(background="#170e2a")

        margin = 12
        card_width = width - margin * 2
        x1, x2 = margin, width - margin
        y = 8
        self._round_card(canvas, x1, y, x2, y + 116, fill="#241631", outline="#5b466b")
        canvas.create_text(x1 + 18, y + 19, text="TOPIK", anchor="w", fill="#b8aac9", font=("Segoe UI", 9, "bold"))
        self.topic_box_window = canvas.create_window(x1 + 18, y + 42, anchor="nw", width=card_width - 36, height=60, window=self.topic_box)
        self.topic_placeholder = canvas.create_text(x1 + 32, y + 58, text="Contoh: sejarah HP, asal-usul kopi, kenapa langit biru",
                                                    anchor="nw", fill="#80758e", font=("Segoe UI", 10), state="hidden" if self.topic.get() else "normal")
        y += 128

        self._round_card(canvas, x1, y, x2, y + 122, fill="#241631", outline="#5b466b")
        canvas.create_text(x1 + 18, y + 18, text="MODE VISUAL", anchor="w", fill="#b8aac9", font=("Segoe UI", 9, "bold"))
        gap = 12
        option_w = (card_width - 36 - gap) / 2
        left_x1, left_x2 = x1 + 18, x1 + 18 + option_w
        right_x1, right_x2 = left_x2 + gap, x2 - 18
        self._round_card(canvas, left_x1, y + 38, left_x2, y + 108, fill="#291b35", outline="#51425e")
        canvas.create_text(left_x1 + 14, y + 54, text="✦  Video AI", anchor="w", fill="#a795b2", font=("Segoe UI", 10, "bold"))
        canvas.create_text(left_x1 + 14, y + 82, text="LTX belum tersedia di edisi Windows", anchor="w", fill="#93879d", font=("Segoe UI", 8))
        self._round_card(canvas, right_x1, y + 38, right_x2, y + 108, fill="#4d2145", outline="#ff3c78")
        canvas.create_text(right_x1 + 14, y + 54, text="◌  Cepat", anchor="w", fill="#ffffff", font=("Segoe UI", 10, "bold"))
        canvas.create_text(right_x1 + 14, y + 82, text="Gambar + zoom pelan · durasi bergantung GPU", anchor="w", fill="#d7c4d9", font=("Segoe UI", 8))
        y += 134

        self._round_card(canvas, x1, y, x2, y + 116, fill="#241631", outline="#5b466b")
        canvas.create_text(x1 + 18, y + 18, text="ALUR KERJA", anchor="w", fill="#b8aac9", font=("Segoe UI", 9, "bold"))
        steps = [
            ("≡", "Naskah", "Gemma 3 12B" if self.profile.get() == "standard" else "Gemma 3 4B"),
            ("♫", "Suara", "VoiceStudio" if self.tts_backend.get() == "voicestudio" else "Windows lokal"),
            ("▧", "Gambar", "SDXL" if self.profile.get() == "standard" else "SDXL Turbo"),
            ("▣", "Video", "Gerak kamera"),
            ("▰", "Rakit", "MP4"),
        ]
        inner_width = card_width - 42
        col_width = inner_width / len(steps)
        for index, (icon, label, detail) in enumerate(steps):
            center_x = x1 + 21 + col_width * (index + 0.5)
            canvas.create_text(center_x, y + 46, text=icon, fill="#f4ebfb", font=("Segoe UI Symbol", 17, "bold"))
            canvas.create_text(center_x, y + 72, text=label, fill="#ffffff", font=("Segoe UI", 9, "bold"))
            canvas.create_text(center_x, y + 91, text=detail, fill="#b8aac9", font=("Segoe UI", 8))
            if index < len(steps) - 1:
                canvas.create_text(x1 + 21 + col_width * (index + 1), y + 72, text="›", fill="#80758e", font=("Segoe UI", 13))
        y += 128

        self._round_card(canvas, x1, y, x2, y + 48, fill="#321b3b", outline="#61476a")
        canvas.create_text(x1 + 18, y + 24, text="ⓘ  Narasi dan takarir dibuat dalam bahasa Indonesia. Video memakai gerak kamera pada gambar.",
                           anchor="w", fill="#d4c7dc", font=("Segoe UI", 8))
        y += 60
        canvas.create_text(x1 + 4, y + 21, text="Durasi tergantung perangkat dan jumlah adegan", anchor="w", fill="#b8aac9", font=("Segoe UI", 8))
        canvas.create_window(x2 - 4, y + 21, anchor="e", window=self.content_button)
        canvas.configure(scrollregion=(0, 0, width, y + 48))

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
        frame.columnconfigure(0, weight=1)

        profile_card = self._card(frame, "Pilih profil berdasarkan GPU")
        ttk.Radiobutton(
            profile_card, text="1. Standar: GPU NVIDIA RTX dengan VRAM 12 GB atau lebih",
            variable=self.profile, value="standard", command=self._profile_changed,
        ).pack(anchor="w", pady=(2, 0))
        ttk.Label(
            profile_card, text="Gemma 3 12B dan SDXL. RAM 32 GB disarankan.",
            style="CardBody.TLabel", wraplength=800,
        ).pack(anchor="w", padx=(24, 0), pady=(2, 5))
        ttk.Radiobutton(
            profile_card, text="2. Ringan: GPU dengan VRAM di bawah 12 GB, grafis terintegrasi, atau CPU",
            variable=self.profile, value="lite", command=self._profile_changed,
        ).pack(anchor="w", pady=(5, 0))
        ttk.Label(
            profile_card, text="Gemma 3 4B dan SDXL Turbo. RAM 16 GB disarankan; pembuatan gambar lebih lambat pada CPU.",
            style="CardBody.TLabel", wraplength=800,
        ).pack(anchor="w", padx=(24, 0), pady=(2, 5))
        gpu_text = f"GPU NVIDIA terdeteksi: VRAM {self.vram} GB" if self.vram else "GPU NVIDIA tidak terdeteksi. Profil Ringan disarankan."
        ttk.Label(profile_card, text=gpu_text, style="CardBody.TLabel").pack(anchor="w", pady=(5, 0))

        output_card = self._card(frame, "Folder hasil")
        output_row = ttk.Frame(output_card, style="Card.TFrame")
        output_row.pack(fill="x")
        ttk.Entry(output_row, textvariable=self.output_root).pack(side="left", fill="x", expand=True)
        ttk.Button(output_row, text="Pilih…", command=self._choose_output).pack(side="left", padx=(8, 0))

        voice_card = self._card(frame, "Narator")
        ttk.Radiobutton(
            voice_card, text="Suara Windows lokal (langsung digunakan, tanpa ID profil)",
            variable=self.tts_backend, value="sapi", command=self._voice_backend_changed,
        ).pack(anchor="w")
        ttk.Radiobutton(
            voice_card, text="VoiceStudio lokal (memerlukan ID profil VoiceStudio)",
            variable=self.tts_backend, value="voicestudio", command=self._voice_backend_changed,
        ).pack(anchor="w")
        ttk.Label(
            voice_card, text="OmniVoice adalah nama model, bukan ID profil. ID profil dibuat di aplikasi VoiceStudio.",
            style="CardBody.TLabel", wraplength=800,
        ).pack(anchor="w", pady=(2, 8))
        self.voice_entries = []
        self.voice_entries.append(self._setting_row(voice_card, "Alamat API", self.tts_base_url))
        self.voice_entries.append(self._setting_row(voice_card, "Model suara", self.tts_model))
        self.voice_entries.append(self._setting_row(voice_card, "ID profil VoiceStudio", self.voice_profile))
        self._update_voice_controls()
        ttk.Button(
            voice_card, text="Panduan VoiceStudio untuk Windows",
            command=lambda: webbrowser.open("https://github.com/debpalash/VoiceStudio/blob/main/docs/install/windows.md"),
        ).pack(anchor="w", pady=(8, 0))
        ttk.Button(frame, text="Simpan pengaturan", style="Primary.TButton", command=self._save).pack(anchor="w", pady=(2, 0))

    @staticmethod
    def _setting_row(parent, label, variable):
        row = ttk.Frame(parent, style="Card.TFrame")
        row.pack(fill="x", pady=4)
        ttk.Label(row, text=label, style="CardBody.TLabel", width=22).pack(side="left")
        entry = ttk.Entry(row, textvariable=variable)
        entry.pack(side="left", fill="x", expand=True)
        return entry

    def _update_voice_controls(self):
        enabled = self.tts_backend.get() == "voicestudio"
        for entry in self.voice_entries:
            entry.configure(state="normal" if enabled else "disabled")

    def _voice_backend_changed(self):
        self._update_voice_controls()
        self._save()
        if self.tts_backend.get() == "sapi":
            self._append("Narator memakai suara Windows lokal. ID profil tidak diperlukan.")
        elif self.voice_profile.get().strip().casefold() in ("", "omnivoice"):
            self._append("Isi ID profil VoiceStudio sebelum memilih narator ini. OmniVoice adalah nama model, bukan ID profil.")
        self._draw_content()

    def _profile_changed(self):
        self.config_data["profile"] = self.profile.get()
        self._save()
        self.brain_label.configure(text="Gemma 3 12B" if self.profile.get() == "standard" else "Gemma 3 4B")
        self._draw_content()
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
