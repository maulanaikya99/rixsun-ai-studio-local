// RIXSUN AI STUDIO LOCAL - jendela utama (SwiftUI). Menjalankan studio.sh di Terminal agar proses terlihat.
// Build: bash build.sh  (menghasilkan /Applications/RIXSUN AI STUDIO LOCAL.app)
import SwiftUI
import AppKit
import UniformTypeIdentifiers

// Lokasi folder AI: ditulis installer (setup.sh) ke root.txt; di Mac pembuat bawaannya SSD "ikya MSI".
let KONFIG = NSHomeDirectory() + "/Library/Application Support/RIXSUN AI Studio/root.txt"
let BAWAAN = "/Volumes/ikya MSI/AI"
let SETUP_SH = (Bundle.main.resourcePath ?? "") + "/payload/setup.sh"

func lokasiAI() -> String {
    let t = (try? String(contentsOfFile: KONFIG, encoding: .utf8))?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
    return t.isEmpty ? BAWAAN : t
}
var AI = lokasiAI()
var STUDIO: String { AI + "/studio" }
var STUDIO_SH: String { STUDIO + "/studio.sh" }
var PY: String { AI + "/ltx-2-mlx/.venv/bin/python" }
var HASIL: String { (AI as NSString).deletingLastPathComponent + "/file AI studio" }

// MARK: - data

enum Alat: String, CaseIterable, Identifiable {
    case konten, gambar, video, perbesar, otak
    var id: String { rawValue }
    var judul: String {
        switch self {
        case .konten: return "Konten TikTok Otomatis"
        case .gambar: return "Buat Gambar"
        case .video: return "Gambar → Video"
        case .perbesar: return "Perbesar Gambar"
        case .otak: return "Otak AI"
        }
    }
    var sub: String {
        switch self {
        case .konten: return "Topik → video TikTok siap upload"
        case .gambar: return "Teks → gambar dengan FLUX"
        case .video: return "Gerakkan gambar dengan LTX"
        case .perbesar: return "2× lebih tajam (Real-ESRGAN)"
        case .otak: return "Pilih LLM penulis naskah & prompt"
        }
    }
    var ikon: String {
        switch self {
        case .konten: return "play.rectangle.on.rectangle.fill"
        case .gambar: return "paintpalette.fill"
        case .video: return "film.stack.fill"
        case .perbesar: return "plus.magnifyingglass"
        case .otak: return "brain.head.profile.fill"
        }
    }
    var warna: [Color] {
        switch self {
        case .konten: return [Color(red: 1, green: 0.27, blue: 0.45), Color(red: 1, green: 0.55, blue: 0.25)]
        case .gambar: return [Color(red: 0.62, green: 0.35, blue: 1), Color(red: 0.95, green: 0.4, blue: 0.85)]
        case .video: return [Color(red: 0.2, green: 0.55, blue: 1), Color(red: 0.3, green: 0.85, blue: 1)]
        case .perbesar: return [Color(red: 0.15, green: 0.75, blue: 0.55), Color(red: 0.55, green: 0.95, blue: 0.45)]
        case .otak: return [Color(red: 1, green: 0.7, blue: 0.2), Color(red: 1, green: 0.45, blue: 0.3)]
        }
    }
}

struct OtakInfo: Identifiable {
    let id: String, nama: String, sub: String, ikon: String, warna: Color
}

let DAFTAR_OTAK = [
    OtakInfo(id: "gemma", nama: "Gemma 3 12B", sub: "Lokal di Mac · gratis · offline", ikon: "cpu.fill", warna: .green),
    OtakInfo(id: "claude", nama: "Claude Sonnet", sub: "Lewat Claude Code · cepat & teliti · kuota langganan Claude", ikon: "staroflife.fill", warna: Color(red: 0.85, green: 0.47, blue: 0.34)),
    OtakInfo(id: "opus", nama: "Claude Opus", sub: "Lewat Claude Code · paling pintar · kuota lebih cepat habis", ikon: "crown.fill", warna: Color(red: 0.95, green: 0.75, blue: 0.35)),
    OtakInfo(id: "opencode", nama: "DeepSeek V4.1 Flash", sub: "Gratis dari OpenCode · ada batas harian", ikon: "sparkles", warna: .cyan),
    OtakInfo(id: "genspark", nama: "DeepSeek via Genspark", sub: "Perlu kredit Genspark berbayar", ikon: "globe.asia.australia.fill", warna: .purple),
    OtakInfo(id: "deepseek", nama: "DeepSeek API", sub: "Perlu saldo akun DeepSeek", ikon: "key.fill", warna: .mint),
]

enum Uji: Equatable { case belum, jalan, ok(String), gagal(String) }

func q(_ s: String) -> String { "'" + s.replacingOccurrences(of: "'", with: "'\\''") + "'" }

final class Studio: ObservableObject {
    @Published var alat: Alat = .konten
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
    // persiapan (Mac baru)
    @Published var pernahPasang = false
    @Published var pasangUlang = false
    @Published var lokasiPasang = NSHomeDirectory() + "/RIXSUN AI Studio"
    @Published var pVideo = true
    @Published var pKonten = true

    init() { segarkan() }

    func segarkan() {
        AI = lokasiAI()
        ssd = FileManager.default.fileExists(atPath: STUDIO_SH)
        pernahPasang = FileManager.default.fileExists(atPath: KONFIG) || AI == BAWAAN && FileManager.default.fileExists(atPath: "/Volumes/ikya MSI")
        if ssd { pasangUlang = false }
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
        if id == "gemma" { uji[id] = .ok("Siap dipakai, berjalan di Mac ini"); return }
        uji[id] = .jalan
        DispatchQueue.global().async {
            let p = Process()
            p.executableURL = URL(fileURLWithPath: PY)
            p.arguments = ["-I", STUDIO + "/otak.py", "tes", id]
            let pipe = Pipe(); p.standardOutput = pipe; p.standardError = pipe
            var hasil = Uji.gagal("Tidak bisa menjalankan tes")
            if (try? p.run()) != nil {
                let data = pipe.fileHandleForReading.readDataToEndOfFile()
                p.waitUntilExit()
                let s = String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
                let baris = s.components(separatedBy: "\n").last ?? s
                if p.terminationStatus == 0 { hasil = .ok(baris) }
                else if baris.contains("Free usage limit") { hasil = .gagal("Kuota gratis hari ini habis, sementara memakai Gemma") }
                else if baris.contains("session limit") || baris.contains("usage limit") { hasil = .gagal("Batas sesi Claude tercapai, coba lagi setelah reset") }
                else if baris.contains("Free-plan") { hasil = .gagal("Paket gratis Genspark ditolak, perlu kredit berbayar") }
                else if baris.contains("Insufficient") || baris.contains("402") { hasil = .gagal("Saldo DeepSeek kosong") }
                else { hasil = .gagal(baris.replacingOccurrences(of: "GAGAL: ", with: "")) }
            }
            DispatchQueue.main.async { self.uji[id] = hasil }
        }
    }

    /// Jalankan studio.sh di Terminal (lewat file .command sementara, tanpa izin Apple Events).
    func jalankan(_ args: [String]) { terminal([STUDIO_SH] + args) }

    func pasang() {
        var paket = ["dasar"]
        if pVideo || pKonten { paket.append("video") }
        if pKonten { paket.append("konten") }
        terminal([SETUP_SH, lokasiPasang] + paket, pesan: "Pemasangan berjalan di Terminal. Setelah selesai, klik Periksa Lagi")
    }

    /// Jalankan skrip bash di Terminal (lewat file .command sementara, tanpa izin Apple Events).
    func terminal(_ argv: [String], pesan: String = "Dimulai di Terminal, prosesnya bisa dipantau di sana") {
        let cmd = "#!/bin/bash\nrm -f \"$0\"\nbash " + argv.map(q).joined(separator: " ") + "\n"
        let url = URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent("AI Studio \(Int(Date().timeIntervalSince1970)).command")
        do {
            try cmd.write(to: url, atomically: true, encoding: .utf8)
            try FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: url.path)
            NSWorkspace.shared.open(url)
            tampil(pesan)
        } catch { tampil("Gagal memulai: \(error.localizedDescription)") }
    }

    func tampil(_ s: String) {
        withAnimation(.spring) { pesan = s }
        DispatchQueue.main.asyncAfter(deadline: .now() + 4) { withAnimation { if self.pesan == s { self.pesan = nil } } }
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

// MARK: - halaman

struct HalKonten: View {
    @EnvironmentObject var s: Studio
    var body: some View {
        VStack(spacing: 16) {
            Kartu(judul: "Topik") {
                KotakTeks(teks: $s.topik, contoh: "Contoh: sejarah HP, asal-usul kopi, kenapa langit biru")
            }
            Kartu(judul: "Mode visual") {
                HStack(spacing: 12) {
                    Pilihan(judul: "Video AI", sub: "Gerak nyata tiap adegan · ±2 jam", ikon: "wand.and.stars", aktif: !s.cepat, warna: .pink) { s.cepat = false }
                    Pilihan(judul: "Cepat", sub: "Gambar + zoom pelan · ±30 menit", ikon: "hare.fill", aktif: s.cepat, warna: .orange) { s.cepat = true }
                }
            }
            Kartu(judul: "Alur kerja") {
                HStack(spacing: 0) {
                    langkah("text.quote", "Naskah", s.otakAktif.nama)
                    panah; langkah("waveform", "Suara", "OmniVoice")
                    panah; langkah("photo", "Gambar", "FLUX")
                    panah; langkah("film", "Video", s.cepat ? "zoom" : "LTX-2.3")
                    panah; langkah("square.stack.3d.up.fill", "Rakit", "MP4")
                }
            }
            TombolMulai(label: "Buat Konten", info: s.cepat ? "±30 menit" : "±2 jam · tutup browser agar lebih cepat",
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
            Kartu(judul: "Deskripsi (boleh bahasa Indonesia)") {
                KotakTeks(teks: $s.gTeks, contoh: "Contoh: kucing oranye pakai baju astronot duduk di bulan, gaya kartun 3D")
            }
            Kartu(judul: "Bentuk") {
                HStack(spacing: 12) {
                    Pilihan(judul: "Tegak 9:16", sub: "TikTok · Reels", ikon: "rectangle.portrait", aktif: s.arah == "tegak", warna: .purple) { s.arah = "tegak" }
                    Pilihan(judul: "Mendatar 16:9", sub: "YouTube", ikon: "rectangle", aktif: s.arah == "mendatar", warna: .purple) { s.arah = "mendatar" }
                    Pilihan(judul: "Kotak 1:1", sub: "Instagram", ikon: "square", aktif: s.arah == "kotak", warna: .purple) { s.arah = "kotak" }
                }
            }
            Kartu(judul: "Jumlah variasi") {
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
            TombolMulai(label: "Buat Gambar", info: "±\(s.jumlah * 5 / 2) menit (±2,5 mnt per gambar)", warna: Alat.gambar.warna,
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
            Kartu(judul: "Gambar") {
                if let g = s.vGambar {
                    HStack(spacing: 14) {
                        Thumb(url: g)
                        Text(g.lastPathComponent).font(.system(size: 13, weight: .medium)).foregroundStyle(.white).lineLimit(2)
                        Spacer()
                        Button("Ganti…") { if let f = pilihFile(banyak: false).first { s.vGambar = f } }
                    }
                } else {
                    Button { s.vGambar = pilihFile(banyak: false).first } label: {
                        VStack(spacing: 8) {
                            Image(systemName: "photo.badge.plus").font(.system(size: 28)).foregroundStyle(.white.opacity(0.6))
                            Text("Klik untuk memilih gambar").foregroundStyle(.white.opacity(0.7))
                        }
                        .frame(maxWidth: .infinity, minHeight: 110)
                        .background(RoundedRectangle(cornerRadius: 14).strokeBorder(style: StrokeStyle(lineWidth: 1.5, dash: [6])).foregroundStyle(.white.opacity(0.25)))
                        .contentShape(Rectangle())
                    }.buttonStyle(.plain)
                }
            }
            Kartu(judul: "Apa yang bergerak?") {
                KotakTeks(teks: $s.vTeks, contoh: "Contoh: kucingnya melambaikan tangan, bintang berkelip, kamera pelan mendekat")
            }
            Kartu(judul: "Durasi") {
                HStack(spacing: 12) {
                    ForEach([3, 4, 5], id: \.self) { d in
                        Pilihan(judul: "\(d) detik", sub: "±\(d * 2 + 2) menit", ikon: "timer", aktif: s.detik == d, warna: .cyan) { s.detik = d }
                    }
                }
            }
            TombolMulai(label: "Buat Video", info: "±\(s.detik * 2 + 2) menit", warna: Alat.video.warna,
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
            Kartu(judul: "Gambar (boleh lebih dari satu)") {
                if s.files.isEmpty {
                    Button { s.files = pilihFile(banyak: true) } label: {
                        VStack(spacing: 8) {
                            Image(systemName: "photo.on.rectangle.angled").font(.system(size: 30)).foregroundStyle(.white.opacity(0.6))
                            Text("Klik untuk memilih gambar").foregroundStyle(.white.opacity(0.7))
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
                        Text("\(s.files.count) gambar dipilih").font(.system(size: 12)).foregroundStyle(.white.opacity(0.6))
                        Spacer()
                        Button("Ganti…") { let f = pilihFile(banyak: true); if !f.isEmpty { s.files = f } }
                    }
                }
            }
            Kartu {
                Label("Hasil disimpan di sebelah file asli dengan akhiran _2x.png", systemImage: "info.circle")
                    .font(.system(size: 12)).foregroundStyle(.white.opacity(0.6))
            }
            TombolMulai(label: "Perbesar", info: "±7 detik per gambar", warna: Alat.perbesar.warna, aktif: !s.files.isEmpty) {
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
            Kartu(judul: "Selamat datang") {
                Text("Mac ini belum punya mesin AI Studio. Pilih lokasi dan paket, lalu klik Pasang. Semua diunduh otomatis dari sumber resminya (HuggingFace, GitHub) dan bisa dilanjutkan bila internet terputus.")
                    .font(.system(size: 13)).foregroundStyle(.white.opacity(0.75))
                HStack(spacing: 14) {
                    syarat("cpu", "Chip Apple", true)
                    syarat("memorychip", "RAM \(ram) GB", ram >= 16)
                    syarat("internal.drive", "Kosong \(kosong) GB", kosong >= butuh)
                }
            }
            Kartu(judul: "Lokasi pasang") {
                HStack(spacing: 12) {
                    Image(systemName: "folder.fill").font(.system(size: 22)).foregroundStyle(.orange)
                    Text(s.lokasiPasang).font(.system(size: 13, design: .monospaced)).foregroundStyle(.white).lineLimit(2)
                    Spacer()
                    Button("Pilih Folder…") {
                        let p = NSOpenPanel()
                        p.canChooseDirectories = true; p.canChooseFiles = false; p.canCreateDirectories = true
                        p.prompt = "Pilih"; p.message = "Pilih folder atau SSD eksternal untuk AI Studio"
                        if p.runModal() == .OK, let u = p.url { s.lokasiPasang = u.path }
                    }
                }
                Text("Tips: pilih SSD eksternal agar disk Mac tidak penuh.").font(.system(size: 11)).foregroundStyle(.white.opacity(0.5))
            }
            Kartu(judul: "Paket") {
                VStack(spacing: 10) {
                    paket("Dasar", "Buat Gambar, Perbesar, otak Gemma lokal · ±20 GB", "paintpalette.fill", true, wajib: true) {}
                    paket("Video", "Gambar → Video dengan LTX-2.3 · +20 GB", "film.stack.fill", s.pVideo || s.pKonten, wajib: s.pKonten) { if !s.pKonten { s.pVideo.toggle() } }
                    paket("Konten TikTok", "Narator VoiceStudio + Whisper · +12 GB (termasuk Video)", "play.rectangle.on.rectangle.fill", s.pKonten, wajib: false) {
                        s.pKonten.toggle(); if s.pKonten { s.pVideo = true }
                    }
                }
            }
            TombolMulai(label: "Pasang", info: "Unduhan ±\(butuh) GB · bisa 1-3 jam tergantung internet", warna: [.orange, .pink],
                        aktif: kosong >= butuh) { s.pasang() }
            HStack {
                Spacer()
                Button("Periksa Lagi") { s.segarkan() }
                if s.pernahPasang { Button("Batal") { s.pasangUlang = false } }
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
                if wajib { Text("wajib").font(.system(size: 10, weight: .semibold)).foregroundStyle(.orange.opacity(0.8)) }
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
                Label("Otak dipakai untuk menerjemahkan deskripsi jadi prompt dan menulis naskah Konten Otomatis. Bila otak online gagal (kuota habis, tanpa internet), AI Studio otomatis kembali ke Gemma lokal.",
                      systemImage: "info.circle").font(.system(size: 12)).foregroundStyle(.white.opacity(0.6))
            }
        }
    }

    @ViewBuilder func status(_ id: String) -> some View {
        HStack(spacing: 8) {
            switch s.uji[id] ?? .belum {
            case .belum: Text("Belum diuji").foregroundStyle(.white.opacity(0.4))
            case .jalan: ProgressView().controlSize(.small); Text("Menguji koneksi…").foregroundStyle(.white.opacity(0.6))
            case .ok(let m): Image(systemName: "checkmark.seal.fill").foregroundStyle(.green); Text(m).foregroundStyle(.green.opacity(0.9)).lineLimit(1)
            case .gagal(let m): Image(systemName: "exclamationmark.triangle.fill").foregroundStyle(.yellow); Text(m).foregroundStyle(.yellow.opacity(0.9)).lineLimit(2)
            }
            if s.uji[id] != .jalan {
                Button("Uji") { s.tes(id) }.controlSize(.small)
            }
        }.font(.system(size: 11)).padding(.top, 2)
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
    var body: some View {
        HStack(spacing: 0) {
            samping.frame(width: 280).background(Color.black.opacity(0.45).background(.ultraThinMaterial))
            Rectangle().fill(.white.opacity(0.07)).frame(width: 1)
            ZStack(alignment: .bottom) {
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        HStack(spacing: 14) {
                            Ikon(nama: s.ssd ? s.alat.ikon : "arrow.down.circle.fill", warna: s.ssd ? s.alat.warna : [.orange, .pink], ukuran: 52)
                            VStack(alignment: .leading, spacing: 3) {
                                Text(s.ssd ? s.alat.judul : "Persiapan").font(.system(size: 24, weight: .bold)).foregroundStyle(.white)
                                Text(s.ssd ? s.alat.sub : "Pasang mesin AI di Mac ini (sekali saja)").font(.system(size: 13)).foregroundStyle(.white.opacity(0.55))
                            }
                        }
                        if !s.ssd && s.pernahPasang && !s.pasangUlang {
                            Kartu {
                                Label("Folder AI Studio tidak ditemukan:\n\(AI)\nBila terpasang di SSD, colokkan dulu lalu klik Periksa Lagi.", systemImage: "externaldrive.badge.xmark")
                                    .foregroundStyle(.yellow)
                                HStack {
                                    Button("Periksa Lagi") { s.segarkan() }
                                    Button("Pasang di lokasi lain…") { s.pasangUlang = true }
                                }
                            }
                        } else if !s.ssd {
                            HalPersiapan()
                        } else {
                        Group {
                            switch s.alat {
                            case .konten: HalKonten()
                            case .gambar: HalGambar()
                            case .video: HalVideo()
                            case .perbesar: HalPerbesar()
                            case .otak: HalOtak()
                            }
                        }.id(s.alat)
                        }
                    }.padding(28)
                }
                if let p = s.pesan {
                    Label(p, systemImage: "terminal.fill").font(.system(size: 13, weight: .medium)).foregroundStyle(.white)
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
                Text("100% di Mac ini").font(.system(size: 10, weight: .semibold)).tracking(1.5).foregroundStyle(.white.opacity(0.45))
            }.padding(.top, 34).padding(.bottom, 18).padding(.horizontal, 8)

            ForEach([Alat.konten, .gambar, .video, .perbesar]) { a in menu(a) }
            Spacer()
            Text("OTAK AI").font(.system(size: 10, weight: .bold)).tracking(1.2).foregroundStyle(.white.opacity(0.4)).padding(.horizontal, 8)
            Button { s.alat = .otak } label: {
                HStack(spacing: 10) {
                    Ikon(nama: s.otakAktif.ikon, warna: [s.otakAktif.warna, s.otakAktif.warna.opacity(0.6)], ukuran: 32)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(s.otakAktif.nama).font(.system(size: 12, weight: .semibold)).foregroundStyle(.white).lineLimit(1)
                        Text("Klik untuk mengganti").font(.system(size: 10)).foregroundStyle(.white.opacity(0.5))
                    }
                    Spacer()
                    Image(systemName: "chevron.right").font(.system(size: 10, weight: .bold)).foregroundStyle(.white.opacity(0.4))
                }
                .padding(10)
                .background(RoundedRectangle(cornerRadius: 12).fill(s.alat == .otak ? s.otakAktif.warna.opacity(0.18) : .white.opacity(0.06)))
                .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(s.alat == .otak ? s.otakAktif.warna : .white.opacity(0.08)))
                .contentShape(Rectangle())
            }.buttonStyle(.plain)
            Button { NSWorkspace.shared.open(URL(fileURLWithPath: HASIL)) } label: {
                Label("Buka folder hasil", systemImage: "folder.fill").font(.system(size: 12)).foregroundStyle(.white.opacity(0.6))
                    .padding(.horizontal, 8).padding(.vertical, 8)
            }.buttonStyle(.plain).padding(.bottom, 14)
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
            Utama().environmentObject(studio)
        }
        .windowStyle(.hiddenTitleBar)
        .defaultSize(width: 980, height: 700)
    }
}
