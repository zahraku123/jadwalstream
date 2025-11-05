# Backup to Google Drive Setup Guide

## Overview
Sistem backup otomatis untuk JadwalStream yang menyimpan backup ke Google Drive.

## File yang Dibuat
1. **auth_gdrive.py** - Script untuk autentikasi Google Drive
2. **upload_to_gdrive.py** - Script untuk upload backup ke Google Drive
3. **backup_and_upload.sh** - Script bash untuk backup dan upload otomatis
4. **/root/backupjadwalstream/** - Folder penyimpanan backup lokal

## Setup Langkah demi Langkah

### 1. Autentikasi Google Drive (HANYA SEKALI)

```bash
cd /root/jadwalstream
python3 auth_gdrive.py
```

**Proses:**
- Script akan menampilkan URL untuk autentikasi
- Buka URL tersebut di browser
- Login dengan akun Google yang sama dengan app ini
- Klik "Allow" untuk memberikan akses ke Google Drive
- Copy authorization code yang muncul
- Paste code tersebut di terminal
- File `gdrive_token.json` akan dibuat

**Catatan:** Autentikasi ini hanya perlu dilakukan sekali. Token akan disimpan dan digunakan untuk upload berikutnya.

### 2. Jalankan Backup & Upload

**Cara 1: Menggunakan script bash (RECOMMENDED)**
```bash
/root/jadwalstream/backup_and_upload.sh
```

**Cara 2: Manual step by step**
```bash
# Buat backup
cd /root
tar --exclude='jadwalstream/node_modules' \
    --exclude='jadwalstream/__pycache__' \
    --exclude='jadwalstream/.git' \
    -czf /root/backupjadwalstream/jadwalstream_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    jadwalstream

# Upload ke Google Drive
cd /root/jadwalstream
python3 upload_to_gdrive.py
```

## Lokasi Backup di Google Drive

Backup akan disimpan di folder:
```
Google Drive > JadwalStream_Backups/
```

Setiap file backup akan memiliki nama format:
```
jadwalstream_backup_YYYYMMDD_HHMMSS.tar.gz
```

## Backup Otomatis dengan Cron

Untuk backup otomatis setiap hari jam 3 pagi:

```bash
# Edit crontab
crontab -e

# Tambahkan baris ini:
0 3 * * * /root/jadwalstream/backup_and_upload.sh >> /var/log/jadwalstream_backup.log 2>&1
```

Untuk backup setiap 6 jam:
```bash
0 */6 * * * /root/jadwalstream/backup_and_upload.sh >> /var/log/jadwalstream_backup.log 2>&1
```

## Apa yang Di-backup?

**✓ TERMASUK:**
- Semua file Python (.py)
- File konfigurasi (.json, .json.example)
- Templates HTML
- Static files (CSS, JS)
- Excel files (.xlsx)
- Dokumentasi (.md)
- Tokens folder
- Thumbnails & videos database
- Requirements.txt

**✗ TIDAK TERMASUK:**
- node_modules/ (terlalu besar, bisa di-install ulang)
- __pycache__/ (file Python cache)
- .git/ (git repository)
- venv/ (virtual environment)
- ffmpeg_logs/ (file log yang besar)
- backup/ (folder backup lama)

## Restore dari Backup

1. Download file backup dari Google Drive
2. Extract:
```bash
cd /root
tar -xzf jadwalstream_backup_YYYYMMDD_HHMMSS.tar.gz
```

3. Install dependencies:
```bash
cd /root/jadwalstream
pip3 install -r requirements.txt
npm install
```

4. Restart aplikasi

## Troubleshooting

### Error: "Insufficient Permission"
- Token belum punya akses Google Drive
- Jalankan ulang `python3 auth_gdrive.py`

### Error: "client_secret.json not found"
- File client_secret.json hilang atau terhapus
- Download ulang dari Google Cloud Console

### Error: "Cannot start local server"
- Normal untuk VPS tanpa GUI
- Script akan otomatis beralih ke manual mode
- Ikuti instruksi untuk copy-paste authorization code

### Upload Gagal - Koneksi Timeout
- Ukuran backup terlalu besar
- Cek koneksi internet
- Coba upload lagi

### Token Expired
- Token Google Drive expired (jarang terjadi)
- Jalankan ulang `python3 auth_gdrive.py`
- Token akan di-refresh otomatis

## Keamanan

⚠️ **PENTING:**
- File `gdrive_token.json` berisi kredensial akses Google Drive
- Jangan share atau commit file ini ke git
- Backup file mungkin berisi data sensitif (tokens, client_secret)
- Pastikan akses Google Drive hanya untuk Anda

## Status Backup Saat Ini

Lokasi backup lokal:
```bash
ls -lh /root/backupjadwalstream/
```

Cek ukuran total backup:
```bash
du -sh /root/backupjadwalstream/
```

Hapus backup lokal lama (opsional):
```bash
# Hapus backup lebih dari 7 hari
find /root/backupjadwalstream/ -name "*.tar.gz" -mtime +7 -delete
```
