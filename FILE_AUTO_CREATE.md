# File Auto-Creation Behavior

Dokumentasi tentang file mana yang dibuat otomatis dan mana yang harus di-setup manual.

## ✅ File yang OTOMATIS DIBUAT oleh Aplikasi

### 1. Database JSON Files

| File | Kapan Dibuat | Trigger |
|------|--------------|---------|
| `users.json` | Saat aplikasi pertama kali run | `initialize_default_user()` |
| `live_streams.json` | Saat user akses halaman Live Streams | `get_live_streams()` |
| `video_database.json` | Saat user upload video pertama | `save_video_database()` |
| `thumbnail_database.json` | Saat user upload thumbnail pertama | `save_thumbnail_database()` |
| `stream_mapping.json` | Saat user create stream key pertama | Save mapping function |
| `schedule_config.json` | Saat user konfigurasi schedule times | `save_schedule_times()` |
| `scheduler_status.json` | Saat scheduler berjalan | `save_scheduler_status()` |
| `license_cache.json` | Saat license validation | License validator |

### 2. Excel Database

| File | Kapan Dibuat | Trigger |
|------|--------------|---------|
| `live_stream_data.xlsx` | Saat user buka halaman Schedules | Route `/schedules` |
|  | Atau via installer | `install.sh` → `create_empty_excel.py` |

**Struktur columns:**
- `title` - Judul stream
- `scheduledStartTime` - Waktu mulai (datetime)
- `videoFile` - Path video file
- `thumbnail` - Path thumbnail
- `streamNameExisting` - Nama stream
- `streamIdExisting` - Stream ID
- `token_file` - Token file yang digunakan
- `repeat_daily` - Boolean repeat harian

### 3. Folders

Dibuat otomatis saat aplikasi start (baris 131-134 di `app.py`):
```python
os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)
os.makedirs(TOKENS_FOLDER, exist_ok=True)
```

- `videos/` - Storage video files
- `thumbnails/` - Storage thumbnail images
- `tokens/` - Storage OAuth tokens
- `ffmpeg_logs/` - FFmpeg log files

## ⚠️ File yang HARUS SETUP MANUAL

### 1. Google OAuth Credentials

**File: `client_secret.json`**

❌ TIDAK dibuat otomatis - harus download dari Google Cloud Console

**Cara obtain:**
1. Go to https://console.cloud.google.com
2. Create/select project
3. Enable YouTube Data API v3
4. Create OAuth 2.0 credentials (Desktop app)
5. Download JSON file
6. Rename/save as `client_secret.json`

**Tanpa file ini:**
- ❌ Tidak bisa create YouTube stream keys
- ❌ Tidak bisa authorize YouTube accounts
- ❌ Fitur YouTube scheduling tidak berfungsi

### 2. License System Credentials (Optional)

**File: `license_credentials.json`**

❌ TIDAK dibuat otomatis - optional untuk license system

**Cara obtain:**
1. Google Cloud Console
2. Create Service Account
3. Download JSON credentials
4. Save as `license_credentials.json`
5. Share Google Sheet dengan service account email

**Tanpa file ini:**
- ✅ Aplikasi tetap jalan normal
- ❌ License validation tidak berfungsi
- ℹ️ Bisa disable check di `app.py` (remove `@app.before_request`)

## 📋 Summary Checklist untuk New Installation

### Automatic (No Action Needed)
- ✅ Folders (videos, thumbnails, tokens, ffmpeg_logs)
- ✅ Database JSON files (dibuat saat pertama digunakan)
- ✅ Excel schedule database (dibuat saat buka /schedules)
- ✅ Default admin user (username: admin, password: admin123)

### Manual Setup Required
- ⚠️ `client_secret.json` - **WAJIB** untuk YouTube features
- ⚠️ `telegram_config.json` - Optional, untuk notifications
- ⚠️ `license_credentials.json` - Optional, untuk license system

### Template Files (Auto-copied by installer)
- ✅ `*.example` files → actual files (via `install.sh`)

## 🔍 Troubleshooting

### Error: "client_secret.json not found"
**Solution:** Download dari Google Cloud Console (lihat SETUP.md)

### Error: "No such file: live_stream_data.xlsx"
**Solution (Auto-fix):** 
- Buka halaman `/schedules` - akan auto-create
- Atau run: `python3 create_empty_excel.py`

### Error: "License check failed"
**Solution:**
- Setup `license_credentials.json` (lihat SETUP.md)
- Atau disable license check di `app.py`:
  ```python
  # Comment out atau hapus:
  # @app.before_request
  # def check_valid_license():
  #     ...
  ```

### Empty users.json or default user not created
**Solution:**
```bash
# Delete users.json dan restart aplikasi
rm users.json
python3 app.py
# Default user akan dibuat otomatis
```

## 🎯 Best Practice untuk Production

1. **Setup semua credentials sebelum deploy**
   - `client_secret.json`
   - `license_credentials.json` (if using)
   - `telegram_config.json` (if using)

2. **Backup database files regularly**
   ```bash
   # Backup script example
   tar -czf backup_$(date +%Y%m%d).tar.gz \
     users.json \
     live_streams.json \
     video_database.json \
     thumbnail_database.json \
     stream_mapping.json \
     schedule_config.json \
     live_stream_data.xlsx
   ```

3. **Monitor auto-created files**
   - Check `ffmpeg_logs/` untuk streaming errors
   - Monitor `license_cache.json` untuk license issues

4. **Use environment variables untuk sensitive data**
   - Consider using `.env` file untuk production
   - Store credentials path di environment variables
