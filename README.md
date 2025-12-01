# 🎬 JadwalStream - YouTube Automation Tool

Platform automation untuk mengelola livestream dan upload video YouTube dengan mudah. Dilengkapi fitur scheduling, bulk upload, video looping, dan notifikasi Telegram.

## ✨ Fitur Utama

### 🎥 Live Streaming
- 📺 **Multi-Platform RTMP Streaming** - YouTube, Facebook, Instagram, Twitch, TikTok
- ⏰ **Auto Schedule** - Jadwal otomatis dengan timezone support
- 🔴 **Live Now** - Start streaming langsung tanpa schedule
- 📊 **Real-time Monitor** - Pantau status stream secara real-time
- ⏱️ **Auto Stop Timer** - Otomatis stop stream sesuai durasi

### 📤 Bulk Upload System
- 🤖 **AI Metadata Generator** - Generate title, description, tags dengan Gemini AI
- 🎬 **Bulk Scheduling** - Upload banyak video sekaligus dengan schedule
- 🔄 **Video Looping** - Loop video pendek menjadi video panjang
- 📋 **Upload Queue** - Antrian upload dengan progress tracking
- ⚡ **Auto Upload** - Upload otomatis sesuai jadwal

### 🛠️ Management Tools
- 👥 **Multi-User System** - Isolasi data per user
- 🔑 **Multi YouTube Account** - Support unlimited akun YouTube
- 🎨 **Video & Thumbnail Manager** - Kelola video dan thumbnail
- 📱 **Telegram Notifications** - Notifikasi dengan bahasa gaul Indonesia
- 🌙 **Dark Theme UI** - Interface modern dan responsive

## 📋 Requirements

- **Python 3.10+** ✅
- **FFmpeg** ✅ 
- **Google OAuth credentials** ✅
- **PM2** (opsional, recommended)

## 🚀 Quick Start

### 1️⃣ Clone & Install (Otomatis)

```bash
git clone https://github.com/zahraku123/jadwalstream.git
cd jadwalstream
chmod +x install.sh
./install.sh
```

**Installer akan:**
- ✅ Install semua dependencies
- ✅ Setup database SQLite
- ✅ Buat folder yang diperlukan
- ✅ Jalankan aplikasi dengan PM2

### 2️⃣ Setup Google OAuth

1. Buka [Google Cloud Console](https://console.cloud.google.com)
2. Buat project baru
3. Enable **YouTube Data API v3**
4. Buat **OAuth 2.0 Client ID** (Web Application)
5. Download credentials → Simpan sebagai `client_secret.json`

### 3️⃣ Akses Aplikasi

```
http://localhost:5000
```

**Login Default:**
- Username: `admin`
- Password: `admin123`

---

## 🔧 Instalasi Manual (Alternatif)

```bash
# Clone
git clone https://github.com/zahraku123/jadwalstream.git
cd jadwalstream

# Install dependencies
pip install -r requirements.txt

# Setup database
python3 -c "from modules.database import init_database; init_database()"

# Jalankan
python3 app.py
```

Akses: `http://localhost:5000`

## 📱 Fitur Detail

### 🎥 Live Streaming
- Streaming ke multi-platform (YouTube, FB, IG, Twitch, TikTok)
- Schedule otomatis dengan repeat daily
- Live now tanpa schedule
- Auto-stop timer
- Monitor real-time

### 📤 Bulk Upload
- AI metadata generator (Gemini)
- Video looping (pendek → panjang)
- Upload queue management
- Auto-upload scheduler
- Progress tracking

### 🛠️ Manajemen
- Multi-user dengan isolasi data
- Multi YouTube account
- Video & thumbnail gallery
- Telegram notifications
- Dark theme UI

## 🔧 PM2 Commands

```bash
# Start
pm2 start app.py --name jadwalstream --interpreter python3

# Status
pm2 list

# Logs
pm2 logs jadwalstream

# Restart
pm2 restart jadwalstream

# Stop
pm2 stop jadwalstream

# Auto-start on boot
pm2 startup
pm2 save
```

## 📚 Dokumentasi

- **Multi-User System**: Isolasi data per user
- **Token Management**: `tokens/user_{id}/` per user
- **Database**: SQLite di `jadwalstream.db`
- **Telegram**: Setup di Settings → Telegram

## 🔄 Database Migration (Update dari Versi Lama)

Jika Anda mengalami error seperti `no such column: synced_at` atau `no such column: title`, jalankan migrasi database:

```bash
# Cara 1: Jalankan script migrasi
python3 run_migration.py

# Cara 2: Restart aplikasi (migrasi otomatis)
pm2 restart jadwalstream

# Cara 3: Manual via Python
python3 -c "from modules.database.database import migrate_database; migrate_database()"
```

**Migrasi akan otomatis:**
- ✅ Menambahkan kolom `synced_at` ke tabel `playlist_cache`
- ✅ Mengubah nama kolom `playlist_title` → `title`
- ✅ Menambahkan semua kolom yang hilang
- ✅ Tidak menghapus data yang sudah ada

## 🐛 Troubleshooting

```bash
# Cek versi
python3 --version  # Min 3.10
ffmpeg -version

# Lihat log
pm2 logs jadwalstream

# Restart
pm2 restart jadwalstream

# Database error? Jalankan migrasi
python3 run_migration.py
```

## 📞 Support

Issues: [GitHub Issues](https://github.com/zahraku123/jadwalstream/issues)

---

**Made with ❤️ for YouTube Creators** 🎬

