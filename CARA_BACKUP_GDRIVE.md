# Cara Backup ke Google Drive - LANGKAH MUDAH

## ✅ Status Saat Ini

✓ Backup file sudah dibuat di `/root/backupjadwalstream/`
- File: `jadwalstream_backup_20251105_012547.tar.gz`
- Ukuran: 153.82 MB

⏳ Tinggal upload ke Google Drive

## 🔐 LANGKAH 1: Autentikasi Google Drive (Sekali Saja)

### A. Buka Terminal dan Jalankan:
```bash
cd /root/jadwalstream
python3 auth_gdrive.py
```

### B. Akan Muncul URL Seperti Ini:
```
https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=...
```

### C. Buka URL di Browser:
1. **Copy URL lengkap** yang muncul di terminal
2. **Paste di browser** (Chrome/Firefox/Safari)
3. **Login** dengan akun Google yang sama dengan app JadwalStream ini
4. **Klik "Allow"** untuk memberikan akses Google Drive

### D. Copy Authorization Code:
Setelah klik Allow, browser akan menampilkan:
```
Authorization Code: 4/0AdLIrYe....... (kode panjang)
```
atau redirect ke halaman dengan URL seperti:
```
http://localhost:8080/?code=4/0AdLIrYe.......
```

**Copy kode yang ada setelah `code=`**

### E. Paste di Terminal:
```
Enter the authorization code: [PASTE KODE DI SINI]
```

Tekan Enter, dan akan muncul:
```
✓ Authentication successful!
  Token saved to: gdrive_token.json
```

✅ **SELESAI!** Autentikasi hanya perlu dilakukan sekali. Token akan tersimpan.

---

## 📤 LANGKAH 2: Upload Backup ke Google Drive

Setelah autentikasi berhasil, jalankan:

```bash
cd /root/jadwalstream
python3 upload_to_gdrive.py
```

**Output yang diharapkan:**
```
Backup file: /root/backupjadwalstream/jadwalstream_backup_20251105_012547.tar.gz
Size: 153.82 MB

Using token file: gdrive_token.json
Uploading jadwalstream_backup_20251105_012547.tar.gz...
✓ Upload successful!
  File ID: 1abc123...
  File Name: jadwalstream_backup_20251105_012547.tar.gz
  Link: https://drive.google.com/file/d/...

✓ Backup uploaded to Google Drive successfully!
```

---

## 🚀 CARA CEPAT: All-in-One Script

Setelah autentikasi selesai, gunakan script ini untuk backup + upload otomatis:

```bash
/root/jadwalstream/backup_and_upload.sh
```

Script ini akan:
1. ✓ Buat backup baru dengan timestamp
2. ✓ Upload otomatis ke Google Drive
3. ✓ Tampilkan status dan link file

---

## 📂 Lokasi Backup

**Lokal:**
```
/root/backupjadwalstream/jadwalstream_backup_YYYYMMDD_HHMMSS.tar.gz
```

**Google Drive:**
```
Google Drive > JadwalStream_Backups/ > jadwalstream_backup_YYYYMMDD_HHMMSS.tar.gz
```

---

## 🔄 Backup Otomatis (Opsional)

Untuk backup otomatis setiap hari jam 3 pagi:

```bash
crontab -e
```

Tambahkan:
```bash
0 3 * * * /root/jadwalstream/backup_and_upload.sh >> /var/log/backup.log 2>&1
```

---

## ❓ Troubleshooting

### Masalah: URL tidak bisa dibuka
- Copy URL secara manual ke browser
- Pastikan tidak ada spasi atau karakter tambahan

### Masalah: "Authorization code invalid"
- Kode expired (valid 10 menit)
- Jalankan ulang `python3 auth_gdrive.py`
- Copy kode dengan cepat

### Masalah: "Insufficient Permission"
- Token belum punya akses Drive
- Hapus `gdrive_token.json` dan jalankan ulang autentikasi
```bash
rm gdrive_token.json
python3 auth_gdrive.py
```

### Masalah: Upload lambat/stuck
- Normal untuk file besar (154 MB)
- Tunggu hingga selesai (bisa 2-5 menit tergantung internet)

---

## ✅ Verifikasi Backup di Google Drive

1. Buka https://drive.google.com
2. Cari folder **JadwalStream_Backups**
3. Lihat file backup dengan timestamp
4. Download untuk test restore

---

## 🎯 RINGKASAN PERINTAH

```bash
# Autentikasi (sekali saja)
cd /root/jadwalstream
python3 auth_gdrive.py

# Upload backup yang sudah ada
python3 upload_to_gdrive.py

# Buat backup baru + upload (all-in-one)
/root/jadwalstream/backup_and_upload.sh

# Lihat backup lokal
ls -lh /root/backupjadwalstream/
```
