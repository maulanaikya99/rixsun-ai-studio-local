$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

function Write-Heading($text) {
    Write-Host "`n==================================================================" -ForegroundColor DarkCyan
    Write-Host "  $text" -ForegroundColor Cyan
    Write-Host "==================================================================" -ForegroundColor DarkCyan
}

function Install-WingetPackage($id) {
    Write-Host "Memasang $id..." -ForegroundColor Cyan
    & winget install --id $id --exact --accept-package-agreements --accept-source-agreements --silent
    if ($LASTEXITCODE -ne 0) { throw "winget gagal memasang $id (kode $LASTEXITCODE). Pasang secara manual, lalu jalankan install.cmd lagi." }
}

Write-Heading 'RIXSUN AI STUDIO LOCAL: PEMASANGAN WINDOWS'
Write-Host 'Pilih profil perangkat:'
Write-Host '  1. Standar: GPU NVIDIA RTX dengan VRAM 12 GB+; RAM 32 GB disarankan. Gemma 3 12B + SDXL.'
Write-Host '     Untuk video LTX lokal, siapkan GPU dengan VRAM minimal 24 GB.'
Write-Host '  2. Ringan: GPU NVIDIA dengan VRAM di bawah 12 GB, grafis terintegrasi, atau CPU.'
Write-Host '     Gemma 3 4B + SDXL Turbo. RAM 16 GB disarankan; pembuatan gambar lebih lambat.'
Write-Host '     Video otomatis memakai gerak kamera.'
$choice = Read-Host 'Masukkan 1 atau 2'
if ($choice -notin @('1', '2')) { throw 'Pilih 1 atau 2.' }
$profile = if ($choice -eq '1') { 'standard' } else { 'lite' }
$model = if ($profile -eq 'standard') { 'gemma3:12b' } else { 'gemma3:4b' }

$sourceRoot = Split-Path -Parent $PSScriptRoot
$installRoot = Join-Path $env:LOCALAPPDATA 'RIXSUN AI Studio'
New-Item -ItemType Directory -Force -Path $installRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $installRoot 'windows'), (Join-Path $installRoot 'konten') | Out-Null
Copy-Item (Join-Path $PSScriptRoot '*') (Join-Path $installRoot 'windows') -Recurse -Force
Copy-Item (Join-Path $sourceRoot 'konten/*') (Join-Path $installRoot 'konten') -Recurse -Force

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw 'Windows Package Manager (winget) tidak ditemukan. Perbarui App Installer dari Microsoft Store, lalu jalankan install.cmd lagi.'
}

Write-Heading '[1/4] Python dan FFmpeg'
$python = (Get-Command py -ErrorAction SilentlyContinue).Source
$hasPython312 = $false
if ($python) {
    & $python -3.12 --version
    $hasPython312 = ($LASTEXITCODE -eq 0)
}
if (-not $hasPython312) {
    Install-WingetPackage 'Python.Python.3.12'
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
    $python = (Get-Command py -ErrorAction SilentlyContinue).Source
}
if (-not $python) { throw 'Peluncur Python tidak ditemukan setelah pemasangan.' }
& $python -3.12 --version
if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 diperlukan. Pasang Python 3.12, lalu jalankan install.cmd lagi.' }
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Install-WingetPackage 'Gyan.FFmpeg'
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
}
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue) -or -not (Get-Command ffprobe -ErrorAction SilentlyContinue)) {
    throw 'FFmpeg atau FFprobe tidak ditemukan di PATH. Buka ulang PowerShell, lalu jalankan install.cmd lagi.'
}

Write-Heading '[2/4] Model bahasa lokal Ollama'
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Install-WingetPackage 'Ollama.Ollama'
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
}
$ollama = (Get-Command ollama -ErrorAction SilentlyContinue).Source
if (-not $ollama) {
    $candidate = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
    if (Test-Path $candidate) { $ollama = $candidate }
}
if (-not $ollama) { throw 'Ollama tidak ditemukan setelah pemasangan. Buka sesi baru, lalu jalankan install.cmd lagi.' }
$ollamaApi = 'http://127.0.0.1:11434/api/tags'
try {
    Invoke-RestMethod -Uri $ollamaApi -TimeoutSec 3 | Out-Null
} catch {
    Write-Host 'Menjalankan layanan Ollama...'
    Start-Process -FilePath $ollama -ArgumentList 'serve' -WindowStyle Hidden
    $ollamaReady = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 2
        try {
            Invoke-RestMethod -Uri $ollamaApi -TimeoutSec 3 | Out-Null
            $ollamaReady = $true
            break
        } catch { }
    }
    if (-not $ollamaReady) { throw 'Layanan Ollama gagal dimulai. Buka Ollama dari menu Start, lalu jalankan install.cmd lagi.' }
}

Write-Heading '[3/4] Lingkungan Python dan mesin gambar'
$venv = Join-Path $installRoot '.venv'
$venvPython = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $venvPython)) {
    & $python -3.12 -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw 'Lingkungan Python gagal dibuat.' }
}
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip gagal diperbarui.' }
$nvidia = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nvidia) {
    & $venvPython -m pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128
} else {
    Write-Host 'GPU NVIDIA tidak ditemukan. PyTorch versi CPU akan dipasang; pembuatan gambar akan lambat.' -ForegroundColor Yellow
    & $venvPython -m pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cpu
}
if ($LASTEXITCODE -ne 0) { throw 'PyTorch gagal dipasang.' }
& $venvPython -m pip install -r (Join-Path $installRoot 'windows\requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Paket Python RIXSUN gagal dipasang.' }

Write-Heading '[4/4] Mengunduh model teks lokal'
& $ollama pull $model
if ($LASTEXITCODE -ne 0) { throw "Model $model gagal diunduh. Periksa koneksi internet, lalu jalankan install.cmd lagi." }

$appData = Join-Path $env:APPDATA 'RIXSUN AI Studio'
New-Item -ItemType Directory -Force -Path $appData, (Join-Path $env:USERPROFILE 'Videos\RIXSUN AI Studio') | Out-Null
$config = @{
    profile = $profile
    output_root = (Join-Path $env:USERPROFILE 'Videos\RIXSUN AI Studio')
    tts_backend = 'sapi'
    tts_model = 'omnivoice'
    tts_base_url = 'http://127.0.0.1:3900'
    voice_profile = ''
}
$config | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $appData 'config.json')

$shortcutPath = Join-Path ([Environment]::GetFolderPath('Desktop')) 'RIXSUN AI Studio Local.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $venvPython
$appScript = Join-Path $installRoot 'windows\app.py'
$shortcut.Arguments = '"' + $appScript + '"'
$shortcut.WorkingDirectory = $installRoot
$shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll, 25"
$shortcut.Save()

Write-Heading 'PEMASANGAN SELESAI'
Write-Host "Profil: $profile"
Write-Host "Aplikasi: $installRoot"
Write-Host 'Pembuatan gambar pertama akan mengunduh model SDXL. VoiceStudio bersifat opsional. Aplikasi memakai suara Windows secara bawaan.'
Write-Host 'Buka RIXSUN AI Studio Local melalui pintasan di Desktop.' -ForegroundColor Green
Start-Process -FilePath $venvPython -ArgumentList @('"' + $appScript + '"') -WorkingDirectory $installRoot
