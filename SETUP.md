# Setup Guide - JadwalStream

## File Konfigurasi yang Diperlukan

Setelah clone repository, Anda perlu membuat beberapa file konfigurasi dari template yang tersedia:

### 1. Copy File Template

```bash
# Copy semua file example menjadi file aktif
cp users.json.example users.json
cp telegram_config.json.example telegram_config.json
cp live_streams.json.example live_streams.json
cp stream_mapping.json.example stream_mapping.json
cp schedule_config.json.example schedule_config.json
cp video_database.json.example video_database.json
cp thumbnail_database.json.example thumbnail_database.json
```

### 2. Google OAuth Credentials

**File: `client_secret.json`**

1. Buka [Google Cloud Console](https://console.cloud.google.com)
2. Buat project baru atau pilih project yang ada
3. Enable **YouTube Data API v3**
4. Buat OAuth 2.0 credentials:
   - Application type: **Desktop app**
   - Authorized redirect URIs: `http://localhost:5000/oauth2callback`
5. Download credentials dan simpan sebagai `client_secret.json`

Format file:
```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["http://localhost"]
  }
}
```

### 3. License System (Optional)

**File: `license_credentials.json`**

Jika menggunakan sistem lisensi berbasis Google Sheets:

1. Buat Service Account di Google Cloud Console
2. Download JSON credentials
3. Simpan sebagai `license_credentials.json`
4. Share Google Sheet dengan email service account

Format file:
```json
{
  "type": "service_account",
  "project_id": "your-project",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
}
```

### 4. Telegram Notifications (Optional)

**File: `telegram_config.json`**

Sudah ada template, edit sesuai kebutuhan:

1. Buat bot Telegram via [@BotFather](https://t.me/botfather)
2. Dapatkan bot token
3. Dapatkan chat_id (gunakan [@userinfobot](https://t.me/userinfobot))
4. Edit `telegram_config.json`:

```json
{
  "enabled": true,
  "bot_token": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
  "chat_id": "123456789",
  "notifications": {
    "stream_start": true,
    "stream_end": true,
    "stream_error": true,
    "schedule_create": true,
    "schedule_update": true,
    "schedule_delete": true
  }
}
```

### 5. Schedule Database (Excel)

**File: `live_stream_data.xlsx`**

File Excel untuk menyimpan jadwal streaming. Akan dibuat otomatis oleh installer atau aplikasi saat pertama kali diakses.

Manual creation:
```bash
python3 create_empty_excel.py
```

### 6. Default User Login

**File: `users.json`**

User default akan dibuat otomatis saat pertama kali menjalankan aplikasi:
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: `admin`

⚠️ **PENTING**: Ganti password default setelah login pertama!

## Quick Setup dengan Install Script

```bash
# Jalankan installer otomatis
./install.sh
```

Script akan:
- Check dependencies (Python, FFmpeg, Node.js, PM2)
- Install requirements
- Buat folder yang diperlukan
- Guide setup credentials
- Start aplikasi

## Manual Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Copy template files
cp users.json.example users.json
cp telegram_config.json.example telegram_config.json
# ... (copy semua .example files)

# 3. Setup credentials
# - Tambahkan client_secret.json
# - Edit telegram_config.json (optional)
# - Tambahkan license_credentials.json (optional)

# 4. Buat folder yang diperlukan
mkdir -p videos thumbnails tokens ffmpeg_logs

# 5. Jalankan aplikasi
python3 app.py

# Atau dengan PM2
pm2 start app.py --name jadwalstream --interpreter python3
```

## Verifikasi Setup

Cek apakah semua file sudah tersedia:

```bash
# File wajib ada
ls -la client_secret.json

# File database (akan dibuat otomatis jika belum ada)
ls -la users.json
ls -la live_streams.json
ls -la video_database.json
ls -la thumbnail_database.json
ls -la stream_mapping.json
ls -la schedule_config.json

# File optional
ls -la license_credentials.json
ls -la telegram_config.json
```

## Troubleshooting

### Error: client_secret.json not found
- Download OAuth credentials dari Google Cloud Console
- Pastikan file bernama `client_secret.json` (bukan `client_secret (1).json`)

### Error: ModuleNotFoundError
- Jalankan: `pip install -r requirements.txt`

### Error: FFmpeg not found
- Install FFmpeg: `sudo apt install ffmpeg` (Linux)
- Atau download dari https://ffmpeg.org/download.html

### Port 5000 sudah digunakan
- Edit `app.py` baris terakhir, ganti port:
  ```python
  app.run(host='0.0.0.0', port=5001, debug=True)
  ```

## Keamanan

⚠️ **JANGAN commit file berikut ke repository public:**
- `client_secret.json`
- `license_credentials.json`
- `users.json`
- `telegram_config.json`
- `*_database.json`
- `stream_mapping.json`
- `schedule_config.json`

File `.gitignore` sudah dikonfigurasi untuk mengabaikan file-file sensitif ini.
