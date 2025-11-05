# JadwalStream — Multi-Platform Live Streaming Scheduler

Aplikasi web Flask untuk mengelola jadwal livestream YouTube dan streaming video lokal ke berbagai platform RTMP (YouTube, Facebook, Instagram, Twitch, TikTok).

## ✨ Features

- 📺 Multi-platform streaming (YouTube, Facebook, Instagram, Twitch, TikTok)
- ⏰ Automated scheduling with timezone support
- 👥 Multi-user system with role-based access control
- 🔐 License validation system
- 📱 Telegram notifications
- 🎬 Video & thumbnail management
- 📊 Real-time streaming status monitoring
- 🔑 Multiple YouTube account support

## 📋 Prerequisites

Sebelum instalasi, pastikan sistem Anda memiliki:

- **Python 3.10+** (Wajib)
- **FFmpeg** (Wajib untuk streaming)
- **Node.js & PM2** (Opsional, untuk manajemen proses)
- **Google OAuth credentials** (Wajib untuk YouTube API)

### Cek Versi yang Terinstall

```bash
python3 --version    # Harus 3.10 atau lebih tinggi
ffmpeg -version      # Harus terinstall
node --version       # Opsional
pm2 --version        # Opsional
```

## 🚀 Instalasi

### Metode 1: Instalasi Otomatis (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/zahraku123/jadwalstream.git
cd jadwalstream

# 2. Jalankan script installer
chmod +x install.sh
./install.sh
```

Script installer akan otomatis:
- ✅ Validasi Python 3.10+
- ✅ Install dependencies Python dari requirements.txt
- ✅ Install FFmpeg (jika belum ada)
- ✅ Install Node.js & PM2 (opsional)
- ✅ Copy semua file template (.example) ke file konfigurasi aktual
- ✅ Membuat direktori yang diperlukan (videos, thumbnails, tokens, ffmpeg_logs)
- ✅ Membuat file Excel jadwal kosong (live_stream_data.xlsx)
- ✅ Memandu setup awal
- ✅ Menjalankan aplikasi dengan PM2 (opsional)

### Metode 2: Instalasi Manual

```bash
# 1. Clone repository
git clone https://github.com/zahraku123/jadwalstream.git
cd jadwalstream

# 2. Install Python dependencies
python3 -m pip install -r requirements.txt

# Jika gagal karena PEP 668 (externally-managed-environment):
python3 -m pip install -r requirements.txt --break-system-packages

# Atau gunakan virtual environment (recommended):
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Install FFmpeg
# Ubuntu/Debian:
sudo apt update && sudo apt install ffmpeg

# macOS:
brew install ffmpeg

# 4. Install PM2 (opsional)
sudo npm install -g pm2

# 5. Copy file template
cp users.json.example users.json
cp license_config.json.example license_config.json
cp telegram_config.json.example telegram_config.json
cp stream_mapping.json.example stream_mapping.json
cp live_streams.json.example live_streams.json
cp video_database.json.example video_database.json
cp thumbnail_database.json.example thumbnail_database.json
cp schedule_config.json.example schedule_config.json
cp stream_timers.json.example stream_timers.json

# 6. Buat direktori yang diperlukan
mkdir -p videos thumbnails tokens ffmpeg_logs

# 7. Buat file Excel jadwal kosong
python3 create_empty_excel.py

# 8. Setup Google OAuth (Wajib!)
# Download client_secret.json dari Google Cloud Console
# Simpan di root direktori proyek
```

Untuk instruksi manual lengkap, lihat **[SETUP.md](SETUP.md)**

## 🔧 Konfigurasi

### File Template yang Tersedia

Repository menyediakan file template dengan ekstensi `.example`:

```bash
# Copy otomatis semua file template
for file in *.example; do cp "$file" "${file%.example}"; done

# Atau biarkan install.sh yang menangani
./install.sh
```

**File template yang tersedia:**
- `users.json.example` → `users.json`
- `license_config.json.example` → `license_config.json`
- `telegram_config.json.example` → `telegram_config.json`
- `stream_mapping.json.example` → `stream_mapping.json`
- `live_streams.json.example` → `live_streams.json`
- `video_database.json.example` → `video_database.json`
- `thumbnail_database.json.example` → `thumbnail_database.json`
- `schedule_config.json.example` → `schedule_config.json`
- `stream_timers.json.example` → `stream_timers.json`

### Google OAuth Setup (Wajib)

Download `client_secret.json` dari Google Cloud Console:

1. Buka https://console.cloud.google.com
2. Buat project baru atau gunakan yang sudah ada
3. Aktifkan **YouTube Data API v3**
4. Buat **OAuth 2.0 Client ID** (Application type: Web application)
5. Download credentials → Simpan sebagai `client_secret.json` di root project

Panduan lengkap: **[SETUP.md](SETUP.md)**

## 🔐 Default Login

- **Username**: `admin`
- **Password**: `admin123`

⚠️ **Change password immediately after first login!**

## 📖 Langkah-Langkah Setup

### 1. Clone Repository
```bash
git clone https://github.com/zahraku123/jadwalstream.git
cd jadwalstream
```

### 2. Jalankan Installer
```bash
chmod +x install.sh
./install.sh
```

### 3. Setup Google OAuth (Wajib)
- Buka [Google Cloud Console](https://console.cloud.google.com)
- Buat OAuth 2.0 Client ID
- Download sebagai `client_secret.json`
- Letakkan di root project

### 4. Login & Aktivasi Lisensi
- Buka browser: `http://localhost:5000`
- Login: **admin** / **admin123**
- Pergi ke menu **License**
- Hubungi penjual untuk mendapatkan license key
- Masukkan license key dan aktivasi

### 5. Mulai Streaming!
- Tambahkan akun YouTube via menu **Settings**
- Buat jadwal atau mulai live streaming
- Monitor stream secara real-time

## 🌐 Access

Open browser: `http://localhost:5000`

For VPS/remote access: `http://your-server-ip:5000`

## 📦 Instalasi FFmpeg

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
1. Download dari https://ffmpeg.org/download.html
2. Extract dan tambahkan ke PATH

**macOS:**
```bash
brew install ffmpeg
```

## 🔧 Manajemen Aplikasi dengan PM2

### Perintah PM2 Dasar
```bash
# Start aplikasi
pm2 start app.py --name jadwalstream --interpreter python

# Stop aplikasi
pm2 stop jadwalstream

# Restart aplikasi
pm2 restart jadwalstream

# Lihat status semua aplikasi
pm2 list

# Lihat log real-time
pm2 logs jadwalstream

# Lihat log dengan filter
pm2 logs jadwalstream --lines 100

# Hapus aplikasi dari PM2
pm2 delete jadwalstream

# Monitor resource usage
pm2 monit
```

### Setup Auto-Start saat Boot
```bash
# Simpan konfigurasi PM2 saat ini
pm2 save

# Setup startup script
pm2 startup
# Jalankan perintah yang ditampilkan oleh PM2

# Untuk menghapus auto-start
pm2 unstartup
```

### Deployment Production
```bash
# Pindahkan aplikasi ke direktori deployment
sudo mkdir -p /opt/jadwalstream
sudo cp -r . /opt/jadwalstream/
cd /opt/jadwalstream

# Install dependencies
pip install -r requirements.txt

# Jalankan dengan PM2
pm2 start app.py --name jadwalstream --interpreter python
pm2 save
pm2 startup
```

### Keuntungan PM2
- **Tidak mengganggu stream_loop**: PM2 mengelola proses secara independen
- **Auto-restart**: Otomatis restart jika aplikasi crash
- **Monitoring**: Built-in monitoring dan log management
- **Zero-downtime reload**: Reload aplikasi tanpa downtime
- **Cluster mode**: Bisa menjalankan multiple instances (jika diperlukan)

## 🔑 YouTube Multi-Account Support

Aplikasi ini mendukung multiple akun YouTube dengan token terpisah. Token disimpan di folder `tokens/`.

### Menambah Token YouTube Baru:
1. Login ke aplikasi sebagai admin
2. Buka menu **"Settings"** → **"YouTube Accounts"**
3. Klik **"Add New Account"**
4. Ikuti proses OAuth authorization
5. Token akan tersimpan otomatis di `tokens/channel_name.json`

### Menggunakan Token untuk Schedule:
- Setiap livestream dapat menggunakan token berbeda
- Pilih token saat membuat/edit jadwal livestream
- Mendukung unlimited YouTube accounts

## 📁 Struktur File Penting

```
jadwalstream/
├── app.py                      # Aplikasi Flask utama
├── live.py                     # Logika penjadwalan YouTube
├── kunci.py                    # Helper untuk YouTube API
├── user_auth.py                # Sistem autentikasi user
├── license_validator.py        # Validasi lisensi
├── hwid.py                     # Hardware ID generator
├── telegram_notifier.py        # Notifikasi Telegram
├── requirements.txt            # Dependencies Python
├── client_secret.json          # Kredensial Google OAuth
├── live_stream_data.xlsx       # Data jadwal livestream
├── users.json                  # Database users
├── license_config.json         # Konfigurasi lisensi
├── telegram_config.json        # Konfigurasi Telegram
├── stream_mapping.json         # Mapping stream keys
├── live_streams.json           # Status stream aktif
├── templates/                  # Template HTML
├── static/                     # CSS, JS, assets
├── videos/                     # Folder video lokal
├── thumbnails/                 # Folder thumbnail
├── tokens/                     # Folder token YouTube
└── ffmpeg_logs/                # Log FFmpeg
```

## 🔧 Troubleshooting

### Error Umum:
- **ModuleNotFoundError**: Install dependencies dengan `pip install -r requirements.txt`
- **FFmpeg not found**: Install FFmpeg dan pastikan ada di PATH
- **Token gagal**: Periksa `client_secret.json` dan akses YouTube Data API v3
- **PM2 tidak start**: Cek dengan `pm2 logs jadwalstream` untuk error details

### Cek Status:
```bash
# Cek FFmpeg
ffmpeg -version

# Cek status PM2
pm2 status jadwalstream

# Lihat log error
pm2 logs jadwalstream --err --lines 50
```

