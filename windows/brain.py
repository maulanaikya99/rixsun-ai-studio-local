"""Windows adapter for the local Ollama API used by konten/naskah.py."""
import json
import os
import urllib.error
import urllib.request

PILIHAN = {
    "gemma": "Gemma 3 12B via Ollama",
    "qwen": "Gemma 3 4B via Ollama (lite profile)",
}


class Otak:
    def __init__(self, nama=None, tugas="naskah"):
        profile = os.environ.get("RIXSUN_PROFILE", "lite")
        default = "gemma" if profile == "standard" else "qwen"
        self.nama = nama or os.environ.get("RIXSUN_BRAIN", default)
        self.model = os.environ.get("RIXSUN_OLLAMA_MODEL", "gemma3:12b" if self.nama == "gemma" else "gemma3:4b")
        self.base_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")

    def tanya(self, isi, max_tokens=1000, temp=0.0):
        body = {
            "model": self.model,
            "prompt": isi,
            "stream": False,
            "format": "json",
            "options": {"temperature": temp, "num_predict": max_tokens},
        }
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=600) as response:
                result = json.load(response)
        except urllib.error.URLError as exc:
            raise RuntimeError("Ollama tidak merespons. Jalankan Ollama atau ulangi pemasangan.") from exc
        text = str(result.get("response", "")).strip()
        if not text:
            raise RuntimeError("Ollama mengembalikan jawaban kosong.")
        return text

    def unload(self):
        """Release Ollama's RAM/VRAM before loading the image model."""
        body = {"model": self.model, "prompt": "", "keep_alive": 0, "stream": False}
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60):
                pass
        except urllib.error.URLError:
            # Ollama may already have unloaded the model or shut down.
            pass
