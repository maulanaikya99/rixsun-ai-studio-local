"""Windows content pipeline: Ollama script -> SDXL image -> local narration -> MP4."""
import json
import os
import re
import runpy
import shutil
import subprocess
import sys
import time
import types
import urllib.error
import urllib.request
from pathlib import Path

from windows.brain import Otak, PILIHAN


def resource_path(relative):
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return root / relative


CONTENT_DIR = resource_path("konten")


def _emit(message, callback=None):
    if callback:
        callback(message)
    else:
        print(message, flush=True)


def detect_vram_gb():
    exe = shutil.which("nvidia-smi")
    if not exe:
        return 0
    try:
        result = subprocess.run(
            [exe, "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            check=True, capture_output=True, text=True, errors="replace", timeout=10,
        )
        values = [int(line.strip()) for line in result.stdout.splitlines() if line.strip().isdigit()]
        return max(values, default=0) // 1024
    except (OSError, subprocess.SubprocessError, ValueError):
        return 0


def _run_naskah(project, topic, profile, brain_model, callback):
    script = CONTENT_DIR / "naskah.py"
    if not script.exists():
        raise FileNotFoundError(f"Skrip naskah tidak ditemukan: {script}")
    fake = types.ModuleType("otak")
    fake.Otak = Otak
    fake.PILIHAN = PILIHAN
    previous = sys.modules.get("otak")
    sys.modules["otak"] = fake
    old_argv = sys.argv[:]
    old_profile = os.environ.get("RIXSUN_PROFILE")
    old_brain_model = os.environ.get("RIXSUN_OLLAMA_MODEL")
    os.environ["RIXSUN_PROFILE"] = profile
    os.environ["RIXSUN_OLLAMA_MODEL"] = brain_model
    if str(CONTENT_DIR) not in sys.path:
        sys.path.insert(0, str(CONTENT_DIR))
    sys.argv = [str(script), str(project), topic]
    try:
        _emit("[1/4] Menulis naskah dan riset...", callback)
        runpy.run_path(str(script), run_name="__main__")
    finally:
        Otak().unload()
        sys.argv = old_argv
        if previous is None:
            sys.modules.pop("otak", None)
        else:
            sys.modules["otak"] = previous
        if old_profile is None:
            os.environ.pop("RIXSUN_PROFILE", None)
        else:
            os.environ["RIXSUN_PROFILE"] = old_profile
        if old_brain_model is None:
            os.environ.pop("RIXSUN_OLLAMA_MODEL", None)
        else:
            os.environ["RIXSUN_OLLAMA_MODEL"] = old_brain_model


def _seconds(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True, errors="replace",
    )
    return float(result.stdout.strip())


def _voice_studio(text, destination, settings):
    base = str(settings.get("tts_base_url", "http://127.0.0.1:3900")).rstrip("/")
    model = str(settings.get("tts_model", "omnivoice")).strip() or "omnivoice"
    voice = str(settings.get("voice_profile", "")).strip()
    if not voice:
        raise ValueError("Isi VoiceStudio profile ID di aplikasi, atau pilih Windows SAPI sebagai narator.")
    body = json.dumps({
        "model": model,
        "voice": voice,
        "input": text,
        "response_format": "wav",
    }).encode("utf-8")
    request = urllib.request.Request(
        f"{base}/v1/audio/speech", data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            destination.write_bytes(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        raise RuntimeError(f"VoiceStudio gagal membuat suara: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("VoiceStudio tidak ditemukan di localhost:3900. Jalankan aplikasinya dulu.") from exc


def _windows_sapi(text, destination, settings):
    try:
        import pyttsx3
    except ImportError as exc:
        raise RuntimeError("Windows SAPI belum siap. Jalankan kembali install.cmd.") from exc
    engine = pyttsx3.init()
    engine.setProperty("rate", int(settings.get("sapi_rate", 165)))
    voice_id = str(settings.get("sapi_voice_id", "")).strip()
    if voice_id:
        engine.setProperty("voice", voice_id)
    engine.save_to_file(text, str(destination))
    engine.runAndWait()
    engine.stop()
    if not destination.exists() or destination.stat().st_size < 1000:
        raise RuntimeError("Windows tidak menghasilkan audio. Pasang voice Bahasa Indonesia di Pengaturan Windows.")


def _make_audio(project, settings, callback):
    script = CONTENT_DIR / "naskah.json"
    data = json.loads((project / "naskah.json").read_text(encoding="utf-8"))
    scenes = data.get("adegan", [])
    if not scenes:
        raise ValueError("Naskah tidak berisi adegan.")
    out = project / "suara"
    takes = out / "takes"
    takes.mkdir(parents=True, exist_ok=True)
    backend = settings.get("tts_backend", "sapi")
    clips, durations = [], []
    for index, scene in enumerate(scenes, 1):
        text = str(scene.get("narasi", "")).strip()
        if not text:
            raise ValueError(f"Adegan {index} tidak memiliki narasi.")
        path = takes / f"s{index:02d}.wav"
        if not path.exists():
            _emit(f"[2/4] Narasi adegan {index}/{len(scenes)}...", callback)
            if backend == "voicestudio":
                _voice_studio(text, path, settings)
            else:
                _windows_sapi(text, path, settings)
        clips.append(path)
        durations.append(_seconds(path))

    silence = takes / "jeda.wav"
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono",
        "-t", "0.45", "-c:a", "pcm_s16le", str(silence),
    ], check=True, capture_output=True)
    parts = []
    for index, clip in enumerate(clips):
        parts.append(clip)
        if index < len(clips) - 1:
            parts.append(silence)
    command = ["ffmpeg", "-v", "error", "-y"]
    for part in parts:
        command.extend(["-i", str(part)])
    labels = "".join(f"[{i}:a]" for i in range(len(parts)))
    graph = f"{labels}concat=n={len(parts)}:v=0:a=1[out]"
    narration = out / "narasi.wav"
    command.extend(["-filter_complex", graph, "-map", "[out]", "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(narration)])
    subprocess.run(command, check=True, capture_output=True)

    adg, kata, t = [], {}, 0.0
    gap = 0.45
    for index, (scene, duration) in enumerate(zip(scenes, durations), 1):
        key = f"s{index:02d}"
        start, end = t, t + duration
        narration_text = str(scene.get("narasi", "")).strip()
        adg.append({"key": key, "mulai": round(start, 3), "selesai": round(end, 3),
                    "teks": narration_text, "ucapan": narration_text})
        words = narration_text.split()
        n = max(1, len(words))
        kata[key] = [[word, round(start + duration * i / n, 3), round(start + duration * (i + 1) / n, 3)]
                     for i, word in enumerate(words)]
        t = end + (gap if index < len(clips) else 0)
    (out / "adegan.json").write_text(json.dumps(adg, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "kata.json").write_text(json.dumps(kata, ensure_ascii=False, indent=2), encoding="utf-8")


def _image_pipeline(profile):
    import torch
    from diffusers import DiffusionPipeline

    is_cuda = torch.cuda.is_available()
    dtype = torch.float16 if is_cuda else torch.float32
    model_id = "stabilityai/stable-diffusion-xl-base-1.0" if profile == "standard" else "stabilityai/sdxl-turbo"
    options = {"torch_dtype": dtype, "use_safetensors": True}
    if is_cuda:
        options["variant"] = "fp16"
    pipeline = DiffusionPipeline.from_pretrained(model_id, **options)
    if is_cuda:
        pipeline.enable_model_cpu_offload()
    else:
        pipeline.to("cpu")
    pipeline.enable_attention_slicing()
    return pipeline, model_id


def _prompt(scene):
    style = "Flat 2D vector motion graphic, clean simple geometric forms, bold readable shapes, deep blue and teal with warm yellow accents, no photorealism, no 3D."
    return f"{style} {scene.get('gambar', '')}. Vertical 9:16 composition. No text, letters, logos, or watermark."


def _generate_images(project, profile, callback):
    data = json.loads((project / "naskah.json").read_text(encoding="utf-8"))
    output = project / "adegan"
    output.mkdir(exist_ok=True)
    todo = [(index, scene) for index, scene in enumerate(data["adegan"], 1)
            if not (output / f"s{index:02d}.png").exists()]
    if not todo:
        _emit("Semua gambar adegan sudah ada, dilewati.", callback)
        return
    _emit("[3/4] Memuat model gambar lokal; unduhan pertama bisa besar...", callback)
    pipe, model_id = _image_pipeline(profile)
    _emit(f"Model gambar: {model_id}", callback)
    for index, scene in todo:
        _emit(f"Membuat gambar {index}/{len(data['adegan'])}: {scene.get('label', '')}", callback)
        steps, guidance = (24, 5.0) if profile == "standard" else (4, 0.0)
        width, height = (768, 1344) if profile == "standard" else (512, 768)
        result = pipe(prompt=_prompt(scene), width=width, height=height,
                      num_inference_steps=steps, guidance_scale=guidance)
        result.images[0].save(output / f"s{index:02d}.png")
        del result
        if hasattr(pipe, "_execution_device"):
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass
    del pipe


def generate_single_image(prompt, destination, profile="lite", callback=None):
    pipe, model_id = _image_pipeline(profile)
    _emit(f"Model gambar: {model_id}", callback)
    steps, guidance = (24, 5.0) if profile == "standard" else (4, 0.0)
    width, height = (768, 1344) if profile == "standard" else (512, 768)
    result = pipe(prompt=prompt, width=width, height=height,
                  num_inference_steps=steps, guidance_scale=guidance)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    result.images[0].save(destination)
    del result, pipe
    return destination


def _run_assembly(project, callback):
    script = CONTENT_DIR / "rakit.py"
    if str(CONTENT_DIR) not in sys.path:
        sys.path.insert(0, str(CONTENT_DIR))
    old_argv = sys.argv[:]
    old_font = os.environ.get("RIXSUN_FONT_PATH")
    os.environ["RIXSUN_FONT_PATH"] = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "arialbd.ttf")
    sys.argv = [str(script), str(project)]
    try:
        _emit("[4/4] Merakit MP4 vertikal dengan subtitle, narasi, dan musik...", callback)
        runpy.run_path(str(script), run_name="__main__")
    except SystemExit as exc:
        if exc.code not in (None, 0):
            raise RuntimeError(str(exc.code)) from exc
    finally:
        sys.argv = old_argv
        if old_font is None:
            os.environ.pop("RIXSUN_FONT_PATH", None)
        else:
            os.environ["RIXSUN_FONT_PATH"] = old_font


def run_pipeline(topic, output_root, settings=None, callback=None):
    settings = settings or {}
    profile = settings.get("profile", "lite")
    brain_model = settings.get("brain_model", "gemma3:12b" if profile == "standard" else "gemma3:4b")
    safe = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', " ", topic).strip()[:60] or "Konten"
    project = Path(output_root).expanduser() / safe
    project.mkdir(parents=True, exist_ok=True)
    log_path = project / "proses.log"

    def logged(message):
        with log_path.open("a", encoding="utf-8") as log:
            log.write(message + "\n")
        _emit(message, callback)

    logged(f"Konten otomatis: {topic}")
    logged(f"Profil gambar: {profile}; model teks: {brain_model}; folder: {project}")
    if not (project / "naskah.json").exists():
        _run_naskah(project, topic, profile, brain_model, logged)
    else:
        logged("Naskah sudah ada, dipakai kembali.")
    if not (project / "suara" / "narasi.wav").exists():
        _make_audio(project, settings, logged)
    else:
        logged("Narasi sudah ada, dipakai kembali.")
    _generate_images(project, profile, logged)
    _run_assembly(project, logged)
    results = sorted(project.glob("*.mp4"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not results:
        raise RuntimeError("Proses selesai tetapi MP4 tidak ditemukan.")
    logged(f"SELESAI: {results[0]}")
    return results[0]
