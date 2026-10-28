#!/usr/bin/env python3
"""Otak (LLM) AI Studio Lokal: satu fungsi tanya() untuk terjemah.py dan konten/naskah.py.
Pilihan disimpan di studio/otak.txt (atur lewat pilih_otak.sh), bisa ditimpa env OTAK=...:
  gemma    = Gemma 3 12B lokal (gratis, offline, ±15 dtk muat model)
  claude   = Claude Sonnet lewat Claude Code (`claude -p`, tanpa tool; memakai kuota langganan Claude)
  opus     = Claude Opus lewat Claude Code (paling pintar, kuota langganan lebih cepat habis)
  opencode = DeepSeek V4.1 Flash GRATIS dari OpenCode Zen (`opencode run`, ada batas pemakaian harian)
  genspark = DeepSeek V4.1 Flash lewat proxy Genspark yang dipakai OpenCode (key dari ~/.config/opencode/opencode.json)
  deepseek = DeepSeek V4.1 Flash lewat API DeepSeek langsung (key dari ~/.config/deepseek/api_key)
Otak online yang gagal (kredit habis, offline) otomatis diganti Gemma agar proses tidak berhenti.
Uji: otak.py tes [nama]"""
import json, os, shutil, subprocess, sys, tempfile, threading, time, urllib.request

STUDIO = os.path.dirname(os.path.abspath(__file__))
GEMMA = os.path.join(os.path.dirname(STUDIO), "models", "gemma-3-12b-it-4bit")
OPENCODE = shutil.which("opencode") or os.path.expanduser("~/.local/bin/opencode")
OPENCODE_MODEL = "opencode/deepseek-v4.1-flash-free"
CLAUDE = shutil.which("claude") or os.path.expanduser("~/.local/bin/claude")
PILIHAN = {
    "gemma": "Gemma 3 12B (lokal, gratis)",
    "claude": "Claude Sonnet via Claude Code",
    "opus": "Claude Opus via Claude Code",
    "opencode": "DeepSeek V4.1 Flash gratis dari OpenCode",
    "genspark": "DeepSeek V4.1 Flash via OpenCode/Genspark (kredit Genspark)",
    "deepseek": "DeepSeek V4.1 Flash via API DeepSeek (saldo DeepSeek)",
}


def dipilih():
    nama = os.environ.get("OTAK", "").strip()
    if not nama:
        try:
            nama = open(os.path.join(STUDIO, "otak.txt")).read().strip()
        except OSError:
            nama = "gemma"
    return nama if nama in PILIHAN else "gemma"


def log(pesan):
    print(pesan, file=sys.stderr, flush=True)


def _endpoint(nama):
    """(url chat/completions, key, model) untuk otak online."""
    if nama == "genspark":
        p = json.load(open(os.path.expanduser("~/.config/opencode/opencode.json")))["provider"]["genspark-llm-proxy"]["options"]
        return p["baseURL"].rstrip("/") + "/chat/completions", p["apiKey"], "deep-seek-v4.1-flash"
    key = open(os.path.expanduser("~/.config/deepseek/api_key")).read().strip()
    return "https://api.deepseek.com/chat/completions", key, "deepseek-flash"


class Otak:
    def __init__(self, nama=None):
        self.nama = nama or dipilih()
        self._gemma = None
        if self.nama == "gemma":
            self._muat_gemma()

    def _muat_gemma(self):
        from mlx_lm import load
        t = time.time()
        self._gemma = load(GEMMA)
        log(f"Gemma dimuat dalam {time.time() - t:.0f} dtk")

    def _opencode(self, isi, batas=600):
        """Satu pesan lewat `opencode run` di folder kosong, semua tool OpenCode ditolak (hanya menjawab teks).
        OpenCode diam-diam mengulang bila server menolak (mis. kuota gratis habis), jadi stderr log diawasi
        dan proses dihentikan pada error pertama."""
        env = dict(os.environ, OPENCODE_CONFIG_CONTENT=json.dumps({"permission": "deny", "small_model": OPENCODE_MODEL}))
        with tempfile.TemporaryDirectory(prefix="otak-") as d:
            p = subprocess.Popen([OPENCODE, "run", "--pure", "--print-logs", "--log-level", "WARN", "-m", OPENCODE_MODEL,
                                  "--format", "json", "--title", "AI Studio", isi],
                                 cwd=d, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            galat = []

            def awasi():
                for baris in p.stderr:
                    if "level=ERROR" in baris and "error.error=" in baris:
                        galat.append(baris.split("error.error=", 1)[1].strip().strip('"'))
                        p.kill()
                        return
            threading.Thread(target=awasi, daemon=True).start()
            timer = threading.Timer(batas, p.kill); timer.start()
            out = p.stdout.read(); p.wait(); timer.cancel()
        if galat:
            raise RuntimeError(galat[0][:200])
        teks = []
        for baris in out.splitlines():
            try:
                ev = json.loads(baris)
            except ValueError:
                continue
            part = ev.get("part") or {}
            if ev.get("type") == "text" and part.get("text"):
                teks.append(part["text"])
            elif ev.get("type") == "error":
                raise RuntimeError(json.dumps(ev.get("error"))[:200])
        teks = "".join(teks).strip()
        if not teks:
            raise RuntimeError(f"tidak ada jawaban (kode keluar {p.returncode}, batas {batas} dtk)")
        return teks

    def _claude(self, isi, model="sonnet", batas=600):
        """Satu pesan lewat Claude Code headless: tanpa tool, tanpa MCP/setelan, sesi tidak disimpan."""
        with tempfile.TemporaryDirectory(prefix="otak-") as d:
            p = subprocess.run([CLAUDE, "-p", "--model", model, "--tools", "", "--strict-mcp-config",
                                "--setting-sources", "", "--no-session-persistence", "--output-format", "json"],
                               input=isi, cwd=d, capture_output=True, text=True, timeout=batas)
        try:
            r = json.loads(p.stdout)
        except ValueError:
            raise RuntimeError((p.stdout or p.stderr).strip()[:200] or f"kode keluar {p.returncode}")
        teks = str(r.get("result") or "").strip()
        if r.get("is_error") or not teks:
            raise RuntimeError(teks[:200] or "jawaban kosong")
        return teks

    def _online(self, isi, max_tokens, temp):
        if self.nama in ("claude", "opus"):
            return self._claude(isi, "opus" if self.nama == "opus" else "sonnet")
        if self.nama == "opencode":
            return self._opencode(isi)
        url, key, model = _endpoint(self.nama)
        body = {"model": model, "messages": [{"role": "user", "content": isi}], "temperature": temp,
                # DeepSeek V4.1 berpikir dulu (reasoning ikut dihitung token), beri ruang lebih
                "max_tokens": max(max_tokens * 4, 8000)}
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
            "Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "AIStudioLokal/1.0"})
        r = json.load(urllib.request.urlopen(req, timeout=300))
        teks = (r["choices"][0]["message"].get("content") or "").strip()
        # proxy Genspark menolak kredit gratis dengan HTTP 200 + pesan di content, token 0
        if not teks or (r.get("usage") or {}).get("completion_tokens", 1) == 0:
            raise RuntimeError(teks[:160] or "jawaban kosong")
        return teks

    def tanya(self, isi, max_tokens=1000, temp=0.0):
        if self.nama != "gemma":
            try:
                return self._online(isi, max_tokens, temp)
            except Exception as e:                       # noqa: BLE001
                msg = e.read().decode(errors="replace")[:160] if hasattr(e, "read") else str(e)
                log(f"!! {PILIHAN[self.nama]} gagal: {msg}\n!! beralih ke Gemma lokal")
                self.nama = "gemma"
                self._muat_gemma()
        from mlx_lm import generate
        from mlx_lm.sample_utils import make_sampler
        model, tok = self._gemma
        prompt = tok.apply_chat_template([{"role": "user", "content": isi}], add_generation_prompt=True, tokenize=False)
        return generate(model, tok, prompt=prompt, max_tokens=max_tokens, verbose=False,
                        sampler=make_sampler(temp=temp, top_p=0.95))


def tes(nama):
    """Cek otak online tanpa jatuh ke Gemma. Keluar 0 bila berhasil."""
    t = time.time()
    try:
        o = Otak.__new__(Otak); o.nama, o._gemma = nama, None
        jawab = o._online("Jawab satu kata saja: ibu kota Indonesia?", 50, 0.0)
        print(f"OK ({time.time() - t:.1f} dtk): {jawab[:80]}")
        return 0
    except Exception as e:                               # noqa: BLE001
        msg = e.read().decode(errors="replace")[:200] if hasattr(e, "read") else str(e)
        print(f"GAGAL: {msg}")
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "tes":
        n = sys.argv[2] if len(sys.argv) > 2 else dipilih()
        sys.exit(0 if n == "gemma" else tes(n))
    print(dipilih())
