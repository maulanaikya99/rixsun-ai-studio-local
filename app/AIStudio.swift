// RIXSUN AI STUDIO LOCAL - jendela utama (SwiftUI). Menjalankan studio.sh di Terminal agar proses terlihat.
// Build: bash build.sh  (menghasilkan /Applications/RIXSUN AI STUDIO LOCAL.app)
import SwiftUI
import AppKit
import CoreImage
import UniformTypeIdentifiers

// Lokasi folder AI: ditulis installer (setup.sh) ke root.txt; di Mac pembuat bawaannya SSD "ikya MSI".
let KONFIG = NSHomeDirectory() + "/Library/Application Support/RIXSUN AI Studio/root.txt"
let BAWAAN = "/Volumes/ikya MSI/AI"
let SETUP_SH = (Bundle.main.resourcePath ?? "") + "/payload/setup.sh"
let REPO = "https://github.com/maulanaikya99/rixsun-ai-studio-local"
let DONASI_URL = "https://raw.githubusercontent.com/maulanaikya99/rixsun-ai-studio-local/main/donasi.json"
let VERSI = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "?"

func lokasiAI() -> String {
    let t = (try? String(contentsOfFile: KONFIG, encoding: .utf8))?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
    return t.isEmpty ? BAWAAN : t
}
var AI = lokasiAI()
var STUDIO: String { AI + "/studio" }
var STUDIO_SH: String { STUDIO + "/studio.sh" }
var PY: String { AI + "/ltx-2-mlx/.venv/bin/python" }
var HASIL: String { (AI as NSString).deletingLastPathComponent + "/file AI studio" }

// MARK: - bahasa

/// "id" atau "en"; tersimpan di UserDefaults, bawaan mengikuti bahasa sistem.
var BAHASA: String = {
    if let b = UserDefaults.standard.string(forKey: "bahasa") { return b }
    return (Locale.preferredLanguages.first ?? "en").hasPrefix("id") ? "id" : "en"
}()
func T(_ id: String, _ en: String) -> String { BAHASA == "en" ? en : id }

// MARK: - data

enum Alat: String, CaseIterable, Identifiable {
    case konten, gambar, video, perbesar, otak, pengaturan, dukung
    var id: String { rawValue }
    var judul: String {
        switch self {
        case .konten: return T("Konten TikTok Otomatis", "Automatic TikTok Content")
        case .gambar: return T("Buat Gambar", "Create Image")
        case .video: return T("Gambar → Video", "Image → Video")
        case .perbesar: return T("Perbesar Gambar", "Upscale Image")
        case .otak: return T("Otak AI", "AI Brain")
        case .pengaturan: return T("Pengaturan", "Settings")
        case .dukung: return T("Dukung Developer", "Support the Dev")
        }
    }
    var sub: String {
        switch self {
        case .konten: return T("Topik → video TikTok siap upload", "Topic → ready-to-post TikTok video")
        case .gambar: return T("Teks → gambar dengan FLUX", "Text → image with FLUX")
        case .video: return T("Gerakkan gambar dengan LTX", "Animate an image with LTX")
        case .perbesar: return T("2× lebih tajam (Real-ESRGAN)", "2× sharper (Real-ESRGAN)")
        case .otak: return T("Pilih LLM penulis naskah & prompt", "Choose the LLM that writes scripts & prompts")
        case .pengaturan: return T("Bahasa, lokasi, pembaruan", "Language, location, updates")
        case .dukung: return T("Bantu RIXSUN AI Studio terus berkembang", "Help RIXSUN AI Studio keep growing")
        }
    }
    var ikon: String {
        switch self {
        case .konten: return "play.rectangle.on.rectangle.fill"
        case .gambar: return "paintpalette.fill"
        case .video: return "film.stack.fill"
        case .perbesar: return "plus.magnifyingglass"
        case .otak: return "brain.head.profile.fill"
        case .pengaturan: return "gearshape.fill"
        case .dukung: return "heart.fill"
        }
    }
    var warna: [Color] {
        switch self {
        case .konten: return [Color(red: 1, green: 0.27, blue: 0.45), Color(red: 1, green: 0.55, blue: 0.25)]
        case .gambar: return [Color(red: 0.62, green: 0.35, blue: 1), Color(red: 0.95, green: 0.4, blue: 0.85)]
        case .video: return [Color(red: 0.2, green: 0.55, blue: 1), Color(red: 0.3, green: 0.85, blue: 1)]
        case .perbesar: return [Color(red: 0.15, green: 0.75, blue: 0.55), Color(red: 0.55, green: 0.95, blue: 0.45)]
        case .otak: return [Color(red: 1, green: 0.7, blue: 0.2), Color(red: 1, green: 0.45, blue: 0.3)]
        case .pengaturan: return [Color(red: 0.45, green: 0.5, blue: 0.62), Color(red: 0.62, green: 0.68, blue: 0.8)]
        case .dukung: return [Color(red: 1, green: 0.3, blue: 0.45), Color(red: 1, green: 0.6, blue: 0.7)]
        }
    }
}

struct OtakInfo: Identifiable {
    let id: String, nama: String, ikon: String, warna: Color
    var sub: String {
        switch id {
        case "gemma": return T("Lokal di Mac · gratis · offline", "Local on your Mac · free · offline")
        case "claude": return T("Lewat Claude Code · cepat & teliti · kuota langganan Claude", "Via Claude Code · fast & careful · uses your Claude plan")
        case "opus": return T("Lewat Claude Code · paling pintar · kuota lebih cepat habis", "Via Claude Code · smartest · uses your plan faster")
        case "opencode": return T("Gratis dari OpenCode · ada batas harian", "Free from OpenCode · daily limit")
        case "genspark": return T("Perlu kredit Genspark berbayar", "Needs paid Genspark credits")
        default: return T("Perlu saldo akun DeepSeek", "Needs DeepSeek account balance")
        }
    }
}

let DAFTAR_OTAK = [
    OtakInfo(id: "gemma", nama: "Gemma 3 12B", ikon: "cpu.fill", warna: .green),
    OtakInfo(id: "claude", nama: "Claude Sonnet", ikon: "staroflife.fill", warna: Color(red: 0.85, green: 0.47, blue: 0.34)),
    OtakInfo(id: "opus", nama: "Claude Opus", ikon: "crown.fill", warna: Color(red: 0.95, green: 0.75, blue: 0.35)),
    OtakInfo(id: "opencode", nama: "DeepSeek V4.1 Flash", ikon: "sparkles", warna: .cyan),
    OtakInfo(id: "genspark", nama: "DeepSeek via Genspark", ikon: "globe.asia.australia.fill", warna: .purple),
    OtakInfo(id: "deepseek", nama: "DeepSeek API", ikon: "key.fill", warna: .mint),
]

/// Daftar donasi: donasi.json di repo GitHub (bisa diubah tanpa rilis ulang), salinan bawaan di dalam app.
struct Dompet: Codable, Hashable { var nama: String; var jaringan: String; var alamat: String }
struct Donasi: Codable { var saweria: String = ""; var crypto: [Dompet] = [] }

enum Uji: Equatable { case belum, jalan, ok(String), gagal(String) }

func q(_ s: String) -> String { "'" + s.replacingOccurrences(of: "'", with: "'\\''") + "'" }

final class Studio: ObservableObject {
    @Published var alat: Alat = .konten
    @Published var bahasa: String = BAHASA {
        didSet { BAHASA = bahasa; UserDefaults.standard.set(bahasa, forKey: "bahasa") }
    }
    @Published var otak: String = "gemma"
    @Published var uji: [String: Uji] = [:]
    @Published var ssd = false
    @Published var pesan: String? = nil
    // isian formulir (disimpan di sini, bukan @State: macro SwiftUI tidak tersedia tanpa Xcode)
    @Published var topik = ""
    @Published var cepat = false
    @Published var gTeks = ""
    @Published var arah = "tegak"
    @Published var jumlah = 2
    @Published var vGambar: URL? = nil
    @Published var vTeks = ""
    @Published var detik = 4
    @Published var files: [URL] = []
    // persiapan (Mac baru / pindah lokasi)
    @Published var pernahPasang = false
    @Published var pasangUlang = false
    @Published var lokasiPasang = NSHomeDirectory() + "/RIXSUN AI Studio"
    @Published var pVideo = true
    @Published var pKonten = true
    // dukung & pembaruan
    @Published var donasi = Donasi()
    @Published var qrTerbuka: Set<String> = []
    @Published var cekVersi: String? = nil
    @Published var versiBaru: String? = nil

    init() {
        segarkan()
        if let u = Bundle.main.url(forResource: "donasi", withExtension: "json"), let d = try? Data(contentsOf: u),
           let v = try? JSONDecoder().decode(Donasi.self, from: d) { donasi = v }
        muatDonasi()
    }

    func segarkan() {
        AI = lokasiAI()
        ssd = FileManager.default.fileExists(atPath: STUDIO_SH)
        pernahPasang = FileManager.default.fileExists(atPath: KONFIG) || AI == BAWAAN && FileManager.default.fileExists(atPath: "/Volumes/ikya MSI")
        let t = (try? String(contentsOfFile: STUDIO + "/otak.txt", encoding: .utf8))?
            .trimmingCharacters(in: .whitespacesAndNewlines) ?? "gemma"
        otak = DAFTAR_OTAK.contains { $0.id == t } ? t : "gemma"
    }

    var otakAktif: OtakInfo { DAFTAR_OTAK.first { $0.id == otak } ?? DAFTAR_OTAK[0] }

    func pilihOtak(_ id: String) {
        try? (id + "\n").write(toFile: STUDIO + "/otak.txt", atomically: true, encoding: .utf8)
        otak = id
        if id != "gemma", uji[id] == nil || uji[id] == .belum { tes(id) }
    }

    func tes(_ id: String) {
        if id == "gemma" { uji[id] = .ok(T("Siap dipakai, berjalan di Mac ini", "Ready, runs on this Mac")); return }
        uji[id] = .jalan
        DispatchQueue.global().async {
            let p = Process()
            p.executableURL = URL(fileURLWithPath: PY)
            p.arguments = ["-I", STUDIO + "/otak.py", "tes", id]
            let pipe = Pipe(); p.standardOutput = pipe; p.standardError = pipe
            var hasil = Uji.gagal(T("Tidak bisa menjalankan tes", "Could not run the test"))
            if (try? p.run()) != nil {
                let data = pipe.fileHandleForReading.readDataToEndOfFile()
                p.waitUntilExit()
                let s = String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
                let baris = s.components(separatedBy: "\n").last ?? s
                if p.terminationStatus == 0 { hasil = .ok(baris) }
                else if baris.contains("Free usage limit") { hasil = .gagal(T("Kuota gratis hari ini habis, sementara memakai Gemma", "Today's free quota is used up, using Gemma for now")) }
                else if baris.contains("session limit") || baris.contains("usage limit") { hasil = .gagal(T("Batas sesi Claude tercapai, coba lagi setelah reset", "Claude session limit reached, try again after reset")) }
                else if baris.contains("Free-plan") { hasil = .gagal(T("Paket gratis Genspark ditolak, perlu kredit berbayar", "Genspark free plan refused, paid credits needed")) }
                else if baris.contains("Insufficient") || baris.contains("402") { hasil = .gagal(T("Saldo DeepSeek kosong", "DeepSeek balance is empty")) }
                else if baris.contains("No such file") || baris.contains("not found") { hasil = .gagal(T("Belum terpasang di Mac ini", "Not installed on this Mac")) }
                else { hasil = .gagal(baris.replacingOccurrences(of: "GAGAL: ", with: "")) }
            }
            DispatchQueue.main.async { self.uji[id] = hasil }
        }
    }

    func jalankan(_ args: [String]) { terminal([STUDIO_SH] + args) }

    func pasang() {
        var paket = ["dasar"]
        if pVideo || pKonten { paket.append("video") }
        if pKonten { paket.append("konten") }
        terminal([SETUP_SH, lokasiPasang] + paket, pesan: T("Pemasangan berjalan di Terminal. Setelah selesai, klik Periksa Lagi",
                                                           "Installing in Terminal. When it finishes, click Check Again"))
    }

    /// Jalankan skrip bash di Terminal (lewat file .command sementara, tanpa izin Apple Events).
    func terminal(_ argv: [String], pesan: String? = nil) {
        let cmd = "#!/bin/bash\nrm -f \"$0\"\nbash " + argv.map(q).joined(separator: " ") + "\n"
        let url = URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent("AI Studio \(Int(Date().timeIntervalSince1970)).command")
        do {
            try cmd.write(to: url, atomically: true, encoding: .utf8)
            try FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: url.path)
            NSWorkspace.shared.open(url)
            tampil(pesan ?? T("Dimulai di Terminal, prosesnya bisa dipantau di sana", "Started in Terminal, you can follow the progress there"))
        } catch { tampil(T("Gagal memulai: ", "Could not start: ") + error.localizedDescription) }
    }

    func tampil(_ s: String) {
        withAnimation(.spring) { pesan = s }
        DispatchQueue.main.asyncAfter(deadline: .now() + 4) { withAnimation { if self.pesan == s { self.pesan = nil } } }
    }

    func salin(_ teks: String, _ pesan: String) {
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(teks, forType: .string)
        tampil(pesan)
    }

    func muatDonasi() {
        guard let u = URL(string: DONASI_URL) else { return }
        URLSession.shared.dataTask(with: URLRequest(url: u, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 10)) { d, _, _ in
            guard let d, let v = try? JSONDecoder().decode(Donasi.self, from: d) else { return }
            DispatchQueue.main.async { self.donasi = v }
        }.resume()
    }

    func cekPembaruan() {
        cekVersi = T("Memeriksa…", "Checking…"); versiBaru = nil
        guard let u = URL(string: "https://api.github.com/repos/maulanaikya99/rixsun-ai-studio-local/releases/latest") else { return }
        URLSession.shared.dataTask(with: u) { d, _, _ in
            let tag = (d.flatMap { try? JSONSerialization.jsonObject(with: $0) as? [String: Any] })?["tag_name"] as? String
            DispatchQueue.main.async {
                guard let tag else { self.cekVersi = T("Gagal memeriksa (tanpa internet?)", "Could not check (no internet?)"); return }
                let baru = tag.hasPrefix("v") ? String(tag.dropFirst()) : tag
                if baru.compare(VERSI, options: .numeric) == .orderedDescending {
                    self.versiBaru = baru
                    self.cekVersi = T("Versi baru \(baru) tersedia", "New version \(baru) available")
                } else { self.cekVersi = T("Sudah versi terbaru", "You're up to date") }
            }
        }.resume()
    }
}

// MARK: - komponen

struct Kartu<Isi: View>: View {
    var judul: String? = nil
    @ViewBuilder var isi: Isi
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            if let judul { Text(judul.uppercased()).font(.system(size: 11, weight: .bold)).tracking(1.2).foregroundStyle(.white.opacity(0.5)) }
            isi
        }
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 18).fill(.ultraThinMaterial).overlay(RoundedRectangle(cornerRadius: 18).fill(.black.opacity(0.25))))
        .overlay(RoundedRectangle(cornerRadius: 18).strokeBorder(.white.opacity(0.08)))
    }
}

struct Ikon: View {
    let nama: String, warna: [Color]; var ukuran: CGFloat = 40
    var body: some View {
        RoundedRectangle(cornerRadius: ukuran * 0.3)
            .fill(LinearGradient(colors: warna, startPoint: .topLeading, endPoint: .bottomTrailing))
            .frame(width: ukuran, height: ukuran)
            .overlay(Image(systemName: nama).font(.system(size: ukuran * 0.45, weight: .semibold)).foregroundStyle(.white))
            .shadow(color: warna[0].opacity(0.45), radius: 8, y: 3)
    }
}

struct Pilihan: View {
    let judul: String, sub: String, ikon: String, aktif: Bool, warna: Color, aksi: () -> Void
    var body: some View {
        Button(action: aksi) {
            VStack(alignment: .leading, spacing: 6) {
                Image(systemName: ikon).font(.system(size: 18, weight: .semibold)).foregroundStyle(aktif ? warna : .white.opacity(0.6))
                Text(judul).font(.system(size: 13, weight: .semibold)).foregroundStyle(.white)
                Text(sub).font(.system(size: 11)).foregroundStyle(.white.opacity(0.55))
            }
            .padding(14).frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 14).fill(aktif ? warna.opacity(0.18) : .white.opacity(0.04)))
            .overlay(RoundedRectangle(cornerRadius: 14).strokeBorder(aktif ? warna : .white.opacity(0.08), lineWidth: aktif ? 2 : 1))
            .contentShape(Rectangle())
        }.buttonStyle(.plain)
    }
}

struct KotakTeks: View {
    @Binding var teks: String
    let contoh: String
    var body: some View {
        ZStack(alignment: .topLeading) {
            if teks.isEmpty {
                Text(contoh).foregroundStyle(.white.opacity(0.3)).padding(.horizontal, 14).padding(.vertical, 12)
            }
            TextEditor(text: $teks).scrollContentBackground(.hidden).padding(.horizontal, 9).padding(.vertical, 12)
        }
        .font(.system(size: 14)).foregroundStyle(.white)
        .frame(minHeight: 90, maxHeight: 120)
        .background(RoundedRectangle(cornerRadius: 12).fill(.black.opacity(0.25)))
        .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(.white.opacity(0.1)))
    }
}

struct TombolMulai: View {
    let label: String, info: String, warna: [Color], aktif: Bool, aksi: () -> Void
    var body: some View {
        HStack {
            Label(info, systemImage: "clock").font(.system(size: 12)).foregroundStyle(.white.opacity(0.55))
            Spacer()
            Button(action: aksi) {
                HStack(spacing: 8) { Image(systemName: "play.fill"); Text(label).fontWeight(.bold) }
                    .font(.system(size: 14)).foregroundStyle(.white)
                    .padding(.horizontal, 26).padding(.vertical, 12)
                    .background(Capsule().fill(LinearGradient(colors: warna, startPoint: .leading, endPoint: .trailing)))
                    .shadow(color: warna[0].opacity(aktif ? 0.5 : 0), radius: 10, y: 4)
                    .opacity(aktif ? 1 : 0.35)
            }.buttonStyle(.plain).disabled(!aktif).keyboardShortcut(.return, modifiers: .command)
        }
    }
}

/// Tombol berwarna kecil (aksi sekunder: buka link, salin, dll.)
struct TombolPil: View {
    let label: String, ikon: String, warna: [Color], aksi: () -> Void
    var body: some View {
        Button(action: aksi) {
            Label(label, systemImage: ikon).font(.system(size: 13, weight: .semibold)).foregroundStyle(.white)
                .padding(.horizontal, 16).padding(.vertical, 9)
                .background(Capsule().fill(LinearGradient(colors: warna, startPoint: .leading, endPoint: .trailing)))
                .contentShape(Capsule())
        }.buttonStyle(.plain)
    }
}

func pilihFile(banyak: Bool) -> [URL] {
    let p = NSOpenPanel()
    p.allowedContentTypes = [.image]; p.allowsMultipleSelection = banyak; p.canChooseDirectories = false
    p.directoryURL = URL(fileURLWithPath: HASIL)
    return p.runModal() == .OK ? p.urls : []
}

struct Thumb: View {
    let url: URL
    var body: some View {
        Group {
            if let img = NSImage(contentsOf: url) { Image(nsImage: img).resizable().scaledToFill() }
            else { Color.white.opacity(0.1) }
        }
        .frame(width: 84, height: 84).clipShape(RoundedRectangle(cornerRadius: 10))
        .overlay(RoundedRectangle(cornerRadius: 10).strokeBorder(.white.opacity(0.15)))
    }
}

func kodeQR(_ teks: String) -> NSImage? {
    guard let f = CIFilter(name: "CIQRCodeGenerator") else { return nil }
    f.setValue(Data(teks.utf8), forKey: "inputMessage")
    f.setValue("M", forKey: "inputCorrectionLevel")
    guard let ci = f.outputImage?.transformed(by: CGAffineTransform(scaleX: 8, y: 8)),
          let cg = CIContext().createCGImage(ci, from: ci.extent) else { return nil }
    return NSImage(cgImage: cg, size: NSSize(width: ci.extent.width, height: ci.extent.height))
}

// MARK: - halaman

struct HalKonten: View {
    @EnvironmentObject var s: Studio
    var body: some View {
        VStack(spacing: 16) {
            Kartu(judul: T("Topik", "Topic")) {
                KotakTeks(teks: $s.topik, contoh: T("Contoh: sejarah HP, asal-usul kopi, kenapa langit biru", "Example: history of phones, origin of coffee, why the sky is blue"))
            }
            Kartu(judul: T("Mode visual", "Visual mode")) {
                HStack(spacing: 12) {
                    Pilihan(judul: T("Video AI", "AI video"), sub: T("Gerak nyata tiap adegan · ±2 jam", "Real motion in every scene · ~2 hours"), ikon: "wand.and.stars", aktif: !s.cepat, warna: .pink) { s.cepat = false }
                    Pilihan(judul: T("Cepat", "Fast"), sub: T("Gambar + zoom pelan · ±30 menit", "Images + slow zoom · ~30 minutes"), ikon: "hare.fill", aktif: s.cepat, warna: .orange) { s.cepat = true }
                }
            }
            Kartu(judul: T("Alur kerja", "Workflow")) {
                HStack(spacing: 0) {
                    langkah("text.quote", T("Naskah", "Script"), s.otakAktif.nama)
                    panah; langkah("waveform", T("Suara", "Voice"), "OmniVoice")
                    panah; langkah("photo", T("Gambar", "Images"), "FLUX")
                    panah; langkah("film", "Video", s.cepat ? "zoom" : "LTX-2.3")
                    panah; langkah("square.stack.3d.up.fill", T("Rakit", "Assemble"), "MP4")
                }
            }
            if BAHASA == "en" {
                Kartu {
                    Label("Narration and subtitles are generated in Indonesian (for Indonesian TikTok audiences).", systemImage: "info.circle")
                        .font(.system(size: 12)).foregroundStyle(.white.opacity(0.6))
                }
            }
            TombolMulai(label: T("Buat Konten", "Create Content"), info: s.cepat ? T("±30 menit", "~30 minutes") : T("±2 jam · tutup browser agar lebih cepat", "~2 hours · close your browser for speed"),
                        warna: Alat.konten.warna, aktif: !s.topik.trimmingCharacters(in: .whitespaces).isEmpty) {
                s.jalankan(["konten", s.cepat ? "cepat" : "ai", s.topik.trimmingCharacters(in: .whitespacesAndNewlines)])
            }
        }
    }
    var panah: some View { Image(systemName: "chevron.right").font(.system(size: 10, weight: .bold)).foregroundStyle(.white.opacity(0.3)) }
    func langkah(_ i: String, _ a: String, _ b: String) -> some View {
        VStack(spacing: 5) {
            Image(systemName: i).font(.system(size: 16)).foregroundStyle(.white.opacity(0.85))
            Text(a).font(.system(size: 11, weight: .semibold)).foregroundStyle(.white)
            Text(b).font(.system(size: 10)).foregroundStyle(.white.opacity(0.5)).lineLimit(1)
        }.frame(maxWidth: .infinity)
    }
}

struct HalGambar: View {
    @EnvironmentObject var s: Studio
    var body: some View {
        VStack(spacing: 16) {
            Kartu(judul: T("Deskripsi (boleh bahasa Indonesia)", "Description (any language)")) {
                KotakTeks(teks: $s.gTeks, contoh: T("Contoh: kucing oranye pakai baju astronot duduk di bulan, gaya kartun 3D", "Example: an orange cat in a spacesuit sitting on the moon, 3D cartoon style"))
            }
            Kartu(judul: T("Bentuk", "Shape")) {
                HStack(spacing: 12) {
                    Pilihan(judul: T("Tegak 9:16", "Portrait 9:16"), sub: "TikTok · Reels", ikon: "rectangle.portrait", aktif: s.arah == "tegak", warna: .purple) { s.arah = "tegak" }
                    Pilihan(judul: T("Mendatar 16:9", "Landscape 16:9"), sub: "YouTube", ikon: "rectangle", aktif: s.arah == "mendatar", warna: .purple) { s.arah = "mendatar" }
                    Pilihan(judul: T("Kotak 1:1", "Square 1:1"), sub: "Instagram", ikon: "square", aktif: s.arah == "kotak", warna: .purple) { s.arah = "kotak" }
                }
            }
            Kartu(judul: T("Jumlah variasi", "Number of variations")) {
                HStack(spacing: 10) {
                    ForEach(1...4, id: \.self) { n in
                        Button { s.jumlah = n } label: {
                            Text("\(n)").font(.system(size: 16, weight: .bold)).foregroundStyle(.white)
                                .frame(width: 52, height: 40)
                                .background(RoundedRectangle(cornerRadius: 10).fill(s.jumlah == n ? Color.purple.opacity(0.45) : .white.opacity(0.05)))
                                .overlay(RoundedRectangle(cornerRadius: 10).strokeBorder(s.jumlah == n ? Color.purple : .white.opacity(0.1), lineWidth: s.jumlah == n ? 2 : 1))
                        }.buttonStyle(.plain)
                    }
                    Spacer()
                }
            }
            TombolMulai(label: T("Buat Gambar", "Create Image"), info: T("±\(s.jumlah * 5 / 2) menit (±2,5 mnt per gambar)", "~\(s.jumlah * 5 / 2) min (~2.5 min per image)"), warna: Alat.gambar.warna,
                        aktif: !s.gTeks.trimmingCharacters(in: .whitespaces).isEmpty) {
                s.jalankan(["gambar", s.arah, "\(s.jumlah)", s.gTeks.trimmingCharacters(in: .whitespacesAndNewlines)])
            }
        }
    }
}

struct HalVideo: View {
    @EnvironmentObject var s: Studio
    var body: some View {
        VStack(spacing: 16) {
            Kartu(judul: T("Gambar", "Image")) {
                if let g = s.vGambar {
                    HStack(spacing: 14) {
                        Thumb(url: g)
                        Text(g.lastPathComponent).font(.system(size: 13, weight: .medium)).foregroundStyle(.white).lineLimit(2)
                        Spacer()
                        Button(T("Ganti…", "Change…")) { if let f = pilihFile(banyak: false).first { s.vGambar = f } }
                    }
                } else {
                    Button { s.vGambar = pilihFile(banyak: false).first } label: {
                        VStack(spacing: 8) {
                            Image(systemName: "photo.badge.plus").font(.system(size: 28)).foregroundStyle(.white.opacity(0.6))
                            Text(T("Klik untuk memilih gambar", "Click to choose an image")).foregroundStyle(.white.opacity(0.7))
                        }
                        .frame(maxWidth: .infinity, minHeight: 110)
                        .background(RoundedRectangle(cornerRadius: 14).strokeBorder(style: StrokeStyle(lineWidth: 1.5, dash: [6])).foregroundStyle(.white.opacity(0.25)))
                        .contentShape(Rectangle())
                    }.buttonStyle(.plain)
                }
            }
            Kartu(judul: T("Apa yang bergerak?", "What moves?")) {
                KotakTeks(teks: $s.vTeks, contoh: T("Contoh: kucingnya melambaikan tangan, bintang berkelip, kamera pelan mendekat", "Example: the cat waves, stars twinkle, the camera slowly moves in"))
            }
            Kartu(judul: T("Durasi", "Duration")) {
                HStack(spacing: 12) {
                    ForEach([3, 4, 5], id: \.self) { d in
                        Pilihan(judul: T("\(d) detik", "\(d) seconds"), sub: T("±\(d * 2 + 2) menit", "~\(d * 2 + 2) minutes"), ikon: "timer", aktif: s.detik == d, warna: .cyan) { s.detik = d }
                    }
                }
            }
            TombolMulai(label: T("Buat Video", "Create Video"), info: T("±\(s.detik * 2 + 2) menit", "~\(s.detik * 2 + 2) minutes"), warna: Alat.video.warna,
                        aktif: s.vGambar != nil && !s.vTeks.trimmingCharacters(in: .whitespaces).isEmpty) {
                if let g = s.vGambar { s.jalankan(["video", g.path, "\(s.detik)", s.vTeks.trimmingCharacters(in: .whitespacesAndNewlines)]) }
            }
        }
    }
}

struct HalPerbesar: View {
    @EnvironmentObject var s: Studio
    var body: some View {
        VStack(spacing: 16) {
            Kartu(judul: T("Gambar (boleh lebih dari satu)", "Images (one or more)")) {
                if s.files.isEmpty {
                    Button { s.files = pilihFile(banyak: true) } label: {
                        VStack(spacing: 8) {
                            Image(systemName: "photo.on.rectangle.angled").font(.system(size: 30)).foregroundStyle(.white.opacity(0.6))
                            Text(T("Klik untuk memilih gambar", "Click to choose images")).foregroundStyle(.white.opacity(0.7))
                        }
                        .frame(maxWidth: .infinity, minHeight: 130)
                        .background(RoundedRectangle(cornerRadius: 14).strokeBorder(style: StrokeStyle(lineWidth: 1.5, dash: [6])).foregroundStyle(.white.opacity(0.25)))
                        .contentShape(Rectangle())
                    }.buttonStyle(.plain)
                } else {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 10) { ForEach(s.files, id: \.self) { Thumb(url: $0) } }
                    }
                    HStack {
                        Text(T("\(s.files.count) gambar dipilih", "\(s.files.count) image(s) selected")).font(.system(size: 12)).foregroundStyle(.white.opacity(0.6))
                        Spacer()
                        Button(T("Ganti…", "Change…")) { let f = pilihFile(banyak: true); if !f.isEmpty { s.files = f } }
                    }
                }
            }
            Kartu {
                Label(T("Hasil disimpan di sebelah file asli dengan akhiran _2x.png", "Results are saved next to the original with the suffix _2x.png"), systemImage: "info.circle")
                    .font(.system(size: 12)).foregroundStyle(.white.opacity(0.6))
            }
            TombolMulai(label: T("Perbesar", "Upscale"), info: T("±7 detik per gambar", "~7 seconds per image"), warna: Alat.perbesar.warna, aktif: !s.files.isEmpty) {
                s.jalankan(["perbesar"] + s.files.map(\.path))
            }
        }
    }
}

struct HalPersiapan: View {
    @EnvironmentObject var s: Studio
    var ram: Int { Int(ProcessInfo.processInfo.physicalMemory / 1_073_741_824) }
    var butuh: Int { 20 + (s.pVideo || s.pKonten ? 20 : 0) + (s.pKonten ? 12 : 0) }
    var kosong: Int {
        var u = URL(fileURLWithPath: s.lokasiPasang)
        while !FileManager.default.fileExists(atPath: u.path) && u.path != "/" { u.deleteLastPathComponent() }
        let v = try? u.resourceValues(forKeys: [.volumeAvailableCapacityForImportantUsageKey])
        return Int((v?.volumeAvailableCapacityForImportantUsage ?? 0) / 1_000_000_000)
    }
    var body: some View {
        VStack(spacing: 16) {
            Kartu(judul: T("Selamat datang", "Welcome")) {
                Text(T("Mac ini belum punya mesin AI Studio. Pilih lokasi dan paket, lalu klik Pasang. Semua diunduh otomatis dari sumber resminya (HuggingFace, GitHub) dan bisa dilanjutkan bila internet terputus.",
                       "This Mac doesn't have the AI Studio engines yet. Choose a location and packages, then click Install. Everything is downloaded automatically from the official sources (HuggingFace, GitHub) and resumes if the connection drops."))
                    .font(.system(size: 13)).foregroundStyle(.white.opacity(0.75))
                HStack(spacing: 14) {
                    syarat("cpu", T("Chip Apple", "Apple silicon"), true)
                    syarat("memorychip", "RAM \(ram) GB", ram >= 16)
                    syarat("internal.drive", T("Kosong \(kosong) GB", "\(kosong) GB free"), kosong >= butuh)
                }
            }
            Kartu(judul: T("Lokasi pasang", "Install location")) {
                HStack(spacing: 12) {
                    Image(systemName: "folder.fill").font(.system(size: 22)).foregroundStyle(.orange)
                    Text(s.lokasiPasang).font(.system(size: 13, design: .monospaced)).foregroundStyle(.white).lineLimit(2)
                    Spacer()
                    Button(T("Pilih Folder…", "Choose Folder…")) {
                        let p = NSOpenPanel()
                        p.canChooseDirectories = true; p.canChooseFiles = false; p.canCreateDirectories = true
                        p.prompt = T("Pilih", "Choose"); p.message = T("Pilih folder atau SSD eksternal untuk AI Studio", "Choose a folder or external SSD for AI Studio")
                        if p.runModal() == .OK, let u = p.url { s.lokasiPasang = u.path }
                    }
                }
                Text(T("Tips: pilih SSD eksternal agar disk Mac tidak penuh.", "Tip: choose an external SSD so your Mac's disk doesn't fill up."))
                    .font(.system(size: 11)).foregroundStyle(.white.opacity(0.5))
            }
            Kartu(judul: T("Paket", "Packages")) {
                VStack(spacing: 10) {
                    paket(T("Dasar", "Basic"), T("Buat Gambar, Perbesar, otak Gemma lokal · ±20 GB", "Create Image, Upscale, local Gemma brain · ~20 GB"), "paintpalette.fill", true, wajib: true) {}
                    paket("Video", T("Gambar → Video dengan LTX-2.3 · +20 GB", "Image → Video with LTX-2.3 · +20 GB"), "film.stack.fill", s.pVideo || s.pKonten, wajib: s.pKonten) { if !s.pKonten { s.pVideo.toggle() } }
                    paket(T("Konten TikTok", "TikTok Content"), T("Narator VoiceStudio + Whisper · +12 GB (termasuk Video)", "VoiceStudio narrator + Whisper · +12 GB (includes Video)"), "play.rectangle.on.rectangle.fill", s.pKonten, wajib: false) {
                        s.pKonten.toggle(); if s.pKonten { s.pVideo = true }
                    }
                }
            }
            TombolMulai(label: T("Pasang", "Install"), info: T("Unduhan ±\(butuh) GB · bisa 1-3 jam tergantung internet", "~\(butuh) GB download · 1–3 hours depending on your internet"), warna: [.orange, .pink],
                        aktif: kosong >= butuh) { s.pasang() }
            HStack {
                Spacer()
                Button(T("Periksa Lagi", "Check Again")) { s.segarkan(); if s.ssd { s.pasangUlang = false } }
                if s.pernahPasang { Button(T("Batal", "Cancel")) { s.pasangUlang = false } }
            }
        }
    }
    func syarat(_ i: String, _ t: String, _ ok: Bool) -> some View {
        Label(t, systemImage: ok ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
            .font(.system(size: 12, weight: .medium)).foregroundStyle(ok ? .green : .yellow)
    }
    func paket(_ j: String, _ d: String, _ i: String, _ aktif: Bool, wajib: Bool, aksi: @escaping () -> Void) -> some View {
        Button(action: aksi) {
            HStack(spacing: 12) {
                Image(systemName: i).font(.system(size: 18)).foregroundStyle(aktif ? .orange : .white.opacity(0.4)).frame(width: 28)
                VStack(alignment: .leading, spacing: 2) {
                    Text(j).font(.system(size: 13, weight: .semibold)).foregroundStyle(.white)
                    Text(d).font(.system(size: 11)).foregroundStyle(.white.opacity(0.55))
                }
                Spacer()
                if wajib { Text(T("wajib", "required")).font(.system(size: 10, weight: .semibold)).foregroundStyle(.orange.opacity(0.8)) }
                Image(systemName: aktif ? (wajib ? "lock.square.fill" : "checkmark.square.fill") : "square").font(.system(size: 20))
                    .foregroundStyle(aktif ? .orange : .white.opacity(0.3))
            }
            .padding(12)
            .background(RoundedRectangle(cornerRadius: 12).fill(aktif ? Color.orange.opacity(0.12) : .white.opacity(0.04)))
            .contentShape(Rectangle())
        }.buttonStyle(.plain)
    }
}

struct HalOtak: View {
    @EnvironmentObject var s: Studio
    var body: some View {
        VStack(spacing: 12) {
            ForEach(DAFTAR_OTAK) { o in
                let aktif = s.otak == o.id
                Button { s.pilihOtak(o.id) } label: {
                    HStack(spacing: 14) {
                        Ikon(nama: o.ikon, warna: [o.warna, o.warna.opacity(0.6)], ukuran: 42)
                        VStack(alignment: .leading, spacing: 4) {
                            HStack(spacing: 8) {
                                Text(o.nama).font(.system(size: 15, weight: .semibold)).foregroundStyle(.white)
                                Text(o.id).font(.system(size: 10, design: .monospaced)).foregroundStyle(.white.opacity(0.4))
                            }
                            Text(o.sub).font(.system(size: 12)).foregroundStyle(.white.opacity(0.55))
                            status(o.id)
                        }
                        Spacer()
                        Image(systemName: aktif ? "checkmark.circle.fill" : "circle")
                            .font(.system(size: 22)).foregroundStyle(aktif ? o.warna : .white.opacity(0.25))
                    }
                    .padding(16)
                    .background(RoundedRectangle(cornerRadius: 16).fill(aktif ? o.warna.opacity(0.14) : .white.opacity(0.05)))
                    .overlay(RoundedRectangle(cornerRadius: 16).strokeBorder(aktif ? o.warna : .white.opacity(0.08), lineWidth: aktif ? 2 : 1))
                    .contentShape(Rectangle())
                }.buttonStyle(.plain)
            }
            Kartu {
                Label(T("Otak dipakai untuk menerjemahkan deskripsi jadi prompt dan menulis naskah Konten Otomatis. Bila otak online gagal (kuota habis, tanpa internet), AI Studio otomatis kembali ke Gemma lokal.",
                        "The brain turns your descriptions into prompts and writes the automatic content scripts. If an online brain fails (quota used up, no internet), AI Studio falls back to local Gemma."),
                      systemImage: "info.circle").font(.system(size: 12)).foregroundStyle(.white.opacity(0.6))
            }
        }
    }

    @ViewBuilder func status(_ id: String) -> some View {
        HStack(spacing: 8) {
            switch s.uji[id] ?? .belum {
            case .belum: Text(T("Belum diuji", "Not tested")).foregroundStyle(.white.opacity(0.4))
            case .jalan: ProgressView().controlSize(.small); Text(T("Menguji koneksi…", "Testing connection…")).foregroundStyle(.white.opacity(0.6))
            case .ok(let m): Image(systemName: "checkmark.seal.fill").foregroundStyle(.green); Text(m).foregroundStyle(.green.opacity(0.9)).lineLimit(1)
            case .gagal(let m): Image(systemName: "exclamationmark.triangle.fill").foregroundStyle(.yellow); Text(m).foregroundStyle(.yellow.opacity(0.9)).lineLimit(2)
            }
            if s.uji[id] != .jalan {
                Button(T("Uji", "Test")) { s.tes(id) }.controlSize(.small)
            }
        }.font(.system(size: 11)).padding(.top, 2)
    }
}

struct HalPengaturan: View {
    @EnvironmentObject var s: Studio
    var body: some View {
        VStack(spacing: 16) {
            Kartu(judul: T("Bahasa", "Language")) {
                HStack(spacing: 12) {
                    Pilihan(judul: "Bahasa Indonesia", sub: "Indonesian", ikon: "character.bubble.fill", aktif: s.bahasa == "id", warna: .red) { s.bahasa = "id" }
                    Pilihan(judul: "English", sub: "Bahasa Inggris", ikon: "textformat", aktif: s.bahasa == "en", warna: .blue) { s.bahasa = "en" }
                }
            }
            Kartu(judul: T("Lokasi mesin AI", "AI engine location")) {
                baris("cpu", AI)
                HStack {
                    Button(T("Buka di Finder", "Show in Finder")) { NSWorkspace.shared.open(URL(fileURLWithPath: AI)) }
                    Button(T("Pasang ulang / pindah lokasi…", "Reinstall / move…")) { s.pasangUlang = true }
                }
            }
            Kartu(judul: T("Folder hasil", "Output folder")) {
                baris("folder.fill", HASIL)
                Button(T("Buka di Finder", "Show in Finder")) { NSWorkspace.shared.open(URL(fileURLWithPath: HASIL)) }
            }
            Kartu(judul: T("Tentang", "About")) {
                HStack(spacing: 12) {
                    Text("RIXSUN AI Studio Local").font(.system(size: 14, weight: .bold)).foregroundStyle(.white)
                    Text("v\(VERSI)").font(.system(size: 12, design: .monospaced)).foregroundStyle(.white.opacity(0.5))
                    Spacer()
                }
                HStack(spacing: 10) {
                    Button(T("Cek pembaruan", "Check for updates")) { s.cekPembaruan() }
                    if let v = s.cekVersi {
                        Text(v).font(.system(size: 12)).foregroundStyle(s.versiBaru != nil ? .green : .white.opacity(0.6))
                    }
                    if s.versiBaru != nil {
                        Button(T("Unduh", "Download")) { NSWorkspace.shared.open(URL(string: REPO + "/releases/latest")!) }
                    }
                    Spacer()
                    Button("GitHub") { NSWorkspace.shared.open(URL(string: REPO)!) }
                }
            }
        }
    }
    func baris(_ i: String, _ t: String) -> some View {
        HStack(spacing: 10) {
            Image(systemName: i).foregroundStyle(.orange)
            Text(t).font(.system(size: 12, design: .monospaced)).foregroundStyle(.white).lineLimit(2).textSelection(.enabled)
        }
    }
}

struct HalDukung: View {
    @EnvironmentObject var s: Studio
    var body: some View {
        VStack(spacing: 16) {
            Kartu {
                HStack(alignment: .top, spacing: 14) {
                    Text("☕️").font(.system(size: 34))
                    Text(T("RIXSUN AI Studio Local gratis dan semua AI-nya berjalan di Mac Anda sendiri. Kalau aplikasi ini membantu, dukungan Anda membantu developer menambah fitur baru dan merawatnya. Terima kasih! 🙏",
                           "RIXSUN AI Studio Local is free and all of its AI runs on your own Mac. If it helps you, your support lets the developer keep adding features and maintaining it. Thank you! 🙏"))
                        .font(.system(size: 13)).foregroundStyle(.white.opacity(0.8))
                }
            }
            Kartu(judul: "Saweria") {
                Text(T("QRIS, GoPay, OVO, DANA, ShopeePay, transfer bank", "QRIS, GoPay, OVO, DANA, ShopeePay, bank transfer (Indonesia)"))
                    .font(.system(size: 12)).foregroundStyle(.white.opacity(0.6))
                if let u = URL(string: s.donasi.saweria), !s.donasi.saweria.isEmpty {
                    TombolPil(label: T("Donasi lewat Saweria", "Donate via Saweria"), ikon: "heart.fill", warna: [Color(red: 0.95, green: 0.6, blue: 0.1), Color(red: 1, green: 0.4, blue: 0.3)]) {
                        NSWorkspace.shared.open(u)
                    }
                } else { segera }
            }
            Kartu(judul: T("Crypto", "Crypto")) {
                if s.donasi.crypto.isEmpty { segera }
                ForEach(s.donasi.crypto, id: \.self) { w in dompet(w) }
                if !s.donasi.crypto.isEmpty {
                    Label(T("Kirim hanya lewat jaringan yang tertulis. Salah jaringan = dana hilang.", "Only send on the network shown. Wrong network = lost funds."), systemImage: "exclamationmark.triangle.fill")
                        .font(.system(size: 11)).foregroundStyle(.yellow.opacity(0.85))
                }
            }
            Kartu(judul: T("Cara lain mendukung", "Other ways to help")) {
                HStack(spacing: 10) {
                    TombolPil(label: T("Beri ⭐ di GitHub", "Star on GitHub"), ikon: "star.fill", warna: [Color(red: 0.3, green: 0.3, blue: 0.4), Color(red: 0.45, green: 0.45, blue: 0.6)]) {
                        NSWorkspace.shared.open(URL(string: REPO)!)
                    }
                    TombolPil(label: T("Salin link untuk dibagikan", "Copy link to share"), ikon: "square.and.arrow.up", warna: [Color(red: 0.2, green: 0.5, blue: 0.9), Color(red: 0.3, green: 0.75, blue: 1)]) {
                        s.salin(REPO, T("Link disalin", "Link copied"))
                    }
                    Spacer()
                }
            }
        }
    }
    var segera: some View {
        Label(T("Segera hadir", "Coming soon"), systemImage: "clock").font(.system(size: 12)).foregroundStyle(.white.opacity(0.45))
    }
    func dompet(_ w: Dompet) -> some View {
        let buka = s.qrTerbuka.contains(w.alamat)
        return VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Text(w.nama).font(.system(size: 13, weight: .semibold)).foregroundStyle(.white)
                Text(w.jaringan).font(.system(size: 10, weight: .bold)).foregroundStyle(.black)
                    .padding(.horizontal, 7).padding(.vertical, 2).background(Capsule().fill(.yellow.opacity(0.85)))
                Spacer()
                Button(T("Salin", "Copy")) { s.salin(w.alamat, T("Alamat \(w.nama) disalin", "\(w.nama) address copied")) }
                Button(buka ? T("Tutup QR", "Hide QR") : "QR") {
                    if buka { s.qrTerbuka.remove(w.alamat) } else { s.qrTerbuka.insert(w.alamat) }
                }
            }
            Text(w.alamat).font(.system(size: 11.5, design: .monospaced)).foregroundStyle(.white.opacity(0.8)).textSelection(.enabled).lineLimit(2)
            if buka, let img = kodeQR(w.alamat) {
                Image(nsImage: img).interpolation(.none).resizable().frame(width: 150, height: 150)
                    .padding(8).background(RoundedRectangle(cornerRadius: 10).fill(.white))
            }
        }
        .padding(12)
        .background(RoundedRectangle(cornerRadius: 12).fill(.white.opacity(0.05)))
    }
}

// MARK: - latar karya seni

let LUKISAN: NSImage? = Bundle.main.url(forResource: "Latar", withExtension: "jpg").flatMap { NSImage(contentsOf: $0) }

struct Latar: View {
    var body: some View {
        ZStack {
            LinearGradient(colors: [Color(red: 0.07, green: 0.06, blue: 0.14), Color(red: 0.1, green: 0.07, blue: 0.2), Color(red: 0.05, green: 0.08, blue: 0.16)],
                           startPoint: .topLeading, endPoint: .bottomTrailing)
            if let img = LUKISAN {
                GeometryReader { g in
                    Image(nsImage: img).resizable().scaledToFill().frame(width: g.size.width, height: g.size.height).clipped()
                }
            }
            TimelineView(.animation(minimumInterval: 1 / 20)) { tl in
                let t = tl.date.timeIntervalSinceReferenceDate
                Canvas { ctx, size in
                    // tiga cahaya lembut yang melayang pelan
                    let bola: [(Color, Double, Double, Double)] = [(.pink, 0.70, 0.25, 0.11), (.orange, 0.85, 0.80, 0.07), (.cyan, 0.45, 0.65, 0.09)]
                    for (i, b) in bola.enumerated() {
                        let x = size.width * (b.1 + 0.08 * sin(t * b.3 + Double(i)))
                        let y = size.height * (b.2 + 0.08 * cos(t * b.3 * 1.3 + Double(i)))
                        let r = min(size.width, size.height) * 0.38
                        ctx.fill(Path(ellipseIn: CGRect(x: x - r, y: y - r, width: r * 2, height: r * 2)),
                                 with: .radialGradient(Gradient(colors: [b.0.opacity(0.22), .clear]), center: CGPoint(x: x, y: y), startRadius: 0, endRadius: r))
                    }
                }
            }.blendMode(.screen)
            LinearGradient(colors: [.black.opacity(0.55), .black.opacity(0.25), .black.opacity(0.45)], startPoint: .leading, endPoint: .trailing)
        }
    }
}

// MARK: - jendela

struct Utama: View {
    @EnvironmentObject var s: Studio
    /// halaman yang tidak butuh mesin AI terpasang
    var bebas: Bool { s.alat == .dukung || (s.alat == .pengaturan && !s.pasangUlang) }
    var persiapan: Bool { s.pasangUlang || (!s.ssd && !s.pernahPasang) }
    var body: some View {
        HStack(spacing: 0) {
            samping.frame(width: 280).background(Color.black.opacity(0.45).background(.ultraThinMaterial))
            Rectangle().fill(.white.opacity(0.07)).frame(width: 1)
            ZStack(alignment: .bottom) {
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        HStack(spacing: 14) {
                            let siap = bebas || (!persiapan && s.ssd)
                            Ikon(nama: siap ? s.alat.ikon : "arrow.down.circle.fill", warna: siap ? s.alat.warna : [.orange, .pink], ukuran: 52)
                            VStack(alignment: .leading, spacing: 3) {
                                Text(siap ? s.alat.judul : T("Persiapan", "Setup")).font(.system(size: 24, weight: .bold)).foregroundStyle(.white)
                                Text(siap ? s.alat.sub : T("Pasang mesin AI di Mac ini (sekali saja)", "Install the AI engines on this Mac (one time)"))
                                    .font(.system(size: 13)).foregroundStyle(.white.opacity(0.55))
                            }
                        }
                        if s.alat == .pengaturan && !s.pasangUlang {
                            HalPengaturan()
                        } else if s.alat == .dukung {
                            HalDukung()
                        } else if persiapan {
                            HalPersiapan()
                        } else if !s.ssd {
                            Kartu {
                                Label(T("Folder AI Studio tidak ditemukan:\n\(AI)\nBila terpasang di SSD, colokkan dulu lalu klik Periksa Lagi.",
                                        "AI Studio folder not found:\n\(AI)\nIf it's on an external SSD, plug it in and click Check Again."), systemImage: "externaldrive.badge.xmark")
                                    .foregroundStyle(.yellow)
                                HStack {
                                    Button(T("Periksa Lagi", "Check Again")) { s.segarkan() }
                                    Button(T("Pasang di lokasi lain…", "Install somewhere else…")) { s.pasangUlang = true }
                                }
                            }
                        } else {
                            Group {
                                switch s.alat {
                                case .konten: HalKonten()
                                case .gambar: HalGambar()
                                case .video: HalVideo()
                                case .perbesar: HalPerbesar()
                                default: HalOtak()
                                }
                            }.id(s.alat)
                        }
                    }.padding(28)
                }
                if let p = s.pesan {
                    Label(p, systemImage: "checkmark.circle.fill").font(.system(size: 13, weight: .medium)).foregroundStyle(.white)
                        .padding(.horizontal, 18).padding(.vertical, 10)
                        .background(Capsule().fill(.green.opacity(0.85))).padding(.bottom, 18)
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                }
            }
        }
        .background(Latar().ignoresSafeArea())
        .preferredColorScheme(.dark)
        .frame(minWidth: 900, minHeight: 640)
        .onReceive(NotificationCenter.default.publisher(for: NSApplication.didBecomeActiveNotification)) { _ in s.segarkan() }
    }

    var samping: some View {
        VStack(alignment: .leading, spacing: 6) {
            VStack(alignment: .leading, spacing: 2) {
                Text("RIXSUN").font(.system(size: 26, weight: .black)).tracking(2).foregroundStyle(
                    LinearGradient(colors: [.pink, .orange], startPoint: .leading, endPoint: .trailing))
                Text("AI STUDIO LOCAL").font(.system(size: 13, weight: .heavy)).tracking(1.5).foregroundStyle(.white.opacity(0.9))
                Text(T("100% di Mac ini", "100% on this Mac")).font(.system(size: 10, weight: .semibold)).tracking(1.5).foregroundStyle(.white.opacity(0.45))
            }.padding(.top, 34).padding(.bottom, 18).padding(.horizontal, 8)

            ForEach([Alat.konten, .gambar, .video, .perbesar]) { a in menu(a) }
            Spacer()
            Button { s.alat = .dukung } label: {
                HStack(spacing: 8) {
                    Image(systemName: "heart.fill").foregroundStyle(.pink)
                    Text(T("Dukung Developer", "Support the Dev")).font(.system(size: 12, weight: .semibold)).foregroundStyle(.white)
                    Spacer()
                }
                .padding(.horizontal, 12).padding(.vertical, 9)
                .background(RoundedRectangle(cornerRadius: 12).fill(LinearGradient(colors: [Color.pink.opacity(s.alat == .dukung ? 0.45 : 0.22), Color.orange.opacity(s.alat == .dukung ? 0.35 : 0.15)], startPoint: .leading, endPoint: .trailing)))
                .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(.pink.opacity(s.alat == .dukung ? 0.8 : 0.3)))
                .contentShape(Rectangle())
            }.buttonStyle(.plain).padding(.bottom, 8)
            Text(T("OTAK AI", "AI BRAIN")).font(.system(size: 10, weight: .bold)).tracking(1.2).foregroundStyle(.white.opacity(0.4)).padding(.horizontal, 8)
            Button { s.alat = .otak } label: {
                HStack(spacing: 10) {
                    Ikon(nama: s.otakAktif.ikon, warna: [s.otakAktif.warna, s.otakAktif.warna.opacity(0.6)], ukuran: 32)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(s.otakAktif.nama).font(.system(size: 12, weight: .semibold)).foregroundStyle(.white).lineLimit(1)
                        Text(T("Klik untuk mengganti", "Click to change")).font(.system(size: 10)).foregroundStyle(.white.opacity(0.5))
                    }
                    Spacer()
                    Image(systemName: "chevron.right").font(.system(size: 10, weight: .bold)).foregroundStyle(.white.opacity(0.4))
                }
                .padding(10)
                .background(RoundedRectangle(cornerRadius: 12).fill(s.alat == .otak ? s.otakAktif.warna.opacity(0.18) : .white.opacity(0.06)))
                .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(s.alat == .otak ? s.otakAktif.warna : .white.opacity(0.08)))
                .contentShape(Rectangle())
            }.buttonStyle(.plain)
            HStack {
                Button { NSWorkspace.shared.open(URL(fileURLWithPath: HASIL)) } label: {
                    Label(T("Folder hasil", "Output folder"), systemImage: "folder.fill").font(.system(size: 12)).foregroundStyle(.white.opacity(0.6))
                        .padding(.horizontal, 8).padding(.vertical, 8).contentShape(Rectangle())
                }.buttonStyle(.plain)
                Spacer()
                Button { s.alat = .pengaturan } label: {
                    Image(systemName: "gearshape.fill").font(.system(size: 15))
                        .foregroundStyle(s.alat == .pengaturan ? .white : .white.opacity(0.6))
                        .padding(8).background(Circle().fill(.white.opacity(s.alat == .pengaturan ? 0.18 : 0.06)))
                        .contentShape(Circle())
                }.buttonStyle(.plain).help(T("Pengaturan (⌘,)", "Settings (⌘,)"))
            }.padding(.bottom, 14)
        }.padding(.horizontal, 14)
    }

    func menu(_ a: Alat) -> some View {
        let aktif = s.alat == a
        return Button { withAnimation(.easeOut(duration: 0.15)) { s.alat = a } } label: {
            HStack(spacing: 12) {
                Ikon(nama: a.ikon, warna: a.warna, ukuran: 34)
                VStack(alignment: .leading, spacing: 2) {
                    Text(a.judul).font(.system(size: 13, weight: .semibold)).foregroundStyle(.white)
                    Text(a.sub).font(.system(size: 10.5)).foregroundStyle(.white.opacity(0.5)).lineLimit(1)
                }
                Spacer(minLength: 0)
            }
            .padding(9)
            .background(RoundedRectangle(cornerRadius: 12).fill(aktif ? .white.opacity(0.1) : .clear))
            .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(aktif ? .white.opacity(0.15) : .clear))
            .contentShape(Rectangle())
        }.buttonStyle(.plain)
    }
}

final class Delegasi: NSObject, NSApplicationDelegate {
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}

@main
struct AIStudioApp: App {
    @NSApplicationDelegateAdaptor(Delegasi.self) var delegasi
    @StateObject var studio = Studio()
    var body: some Scene {
        Window("RIXSUN AI Studio Local", id: "utama") {
            Utama().environmentObject(studio).id(studio.bahasa)   // ganti bahasa = gambar ulang semua teks
        }
        .windowStyle(.hiddenTitleBar)
        .defaultSize(width: 980, height: 700)
        .commands {
            CommandGroup(replacing: .appSettings) {
                Button(T("Pengaturan…", "Settings…")) { studio.alat = .pengaturan }.keyboardShortcut(",", modifiers: .command)
            }
        }
    }
}
