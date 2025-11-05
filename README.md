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

## 🚀 Quick Start (5 Minutes!)

### Auto Installation

```bash
# 1. Clone repository
git clone <your-repo-url>
cd jadwalstream

# 2. Run installer
chmod +x install.sh
./install.sh
```

The installer will:
- ✅ Check all dependencies
- ✅ Install Python packages
- ✅ Install FFmpeg & PM2 (if needed)
- ✅ Copy template files
- ✅ Guide you through setup
- ✅ Start the application

### Manual Installation

See **[SETUP.md](SETUP.md)** for detailed manual setup instructions.

## 📋 Prerequisites

- **Python 3.10+**
- **FFmpeg** (for streaming)
- **PM2** (optional, for process management)
- **Google OAuth credentials** - See [SETUP.md](SETUP.md)

## 🔧 Configuration Files

After cloning, you'll need to setup configuration files:

```bash
# Template files are provided, just copy them:
cp *.example <actual-filename>

# Or let install.sh do it automatically
./install.sh
```

**Required files:**
- `client_secret.json` - Google OAuth (download from Google Cloud Console)
- `users.json` - Auto-created from template
- `telegram_config.json` - Optional, for notifications
- `license_credentials.json` - Optional, for license system

See **[SETUP.md](SETUP.md)** for detailed configuration instructions.

## 🔐 Default Login

- **Username**: `admin`
- **Password**: `admin123`

⚠️ **Change password immediately after first login!**

## 📚 Documentation

- **[SETUP.md](SETUP.md)** - Detailed setup instructions
- **[SECURITY.md](SECURITY.md)** - Security best practices
- **[USER_GUIDE.md](USER_GUIDE.md)** - User manual
- **[FEATURES.md](FEATURES.md)** - Complete feature list
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[TELEGRAM_SETUP.md](TELEGRAM_SETUP.md)** - Telegram bot setup
- **[TELEGRAM_TROUBLESHOOTING.md](TELEGRAM_TROUBLESHOOTING.md)** - Telegram troubleshooting
- **[LICENSE_APPSCRIPT_SETUP.md](LICENSE_APPSCRIPT_SETUP.md)** - License system setup

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

