# Step-by-Step Backup ke Google Drive

## ✅ Status: Backup sudah siap!

Backup file sudah dibuat di `/root/backupjadwalstream/`:
- **File:** `jadwalstream_backup_20251105_012547.tar.gz`
- **Ukuran:** 154 MB

Tinggal upload ke Google Drive dengan langkah berikut.

---

## 🔐 LANGKAH 1: Generate URL Autentikasi

Jalankan di terminal:

```bash
cd /root/jadwalstream
python3 simple_auth_gdrive.py
```

**Output:**
```
STEP 1: Open this URL in your browser:
https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=...
```

**Copy URL yang muncul ☝️**

---

## 🌐 LANGKAH 2: Buka URL di Browser

1. **Paste URL** di browser (Chrome/Firefox/Safari)
2. **Login** dengan akun Google yang sama dengan YouTube API
3. **Klik "Allow"** untuk memberikan akses Google Drive
4. **Halaman akan redirect** ke URL seperti ini:
   ```
   http://localhost:8080/?code=4/0AdLIrYe_abc123xyz...
   ```
   ⚠️ **Halaman mungkin error "Cannot connect"** - TIDAK MASALAH!
   
5. **Copy SELURUH URL** dari address bar browser

---

## 🔑 LANGKAH 3: Complete Autentikasi

Paste URL yang sudah di-copy ke perintah ini:

```bash
cd /root/jadwalstream
python3 complete_auth_gdrive.py 'http://localhost:8080/?code=4/0AdLIrYe_PASTE_CODE_DISINI...'
```

⚠️ **PENTING:** 
- Gunakan tanda petik tunggal `'...'` 
- Copy SELURUH URL termasuk `http://localhost:8080/?code=`

**Output yang diharapkan:**
```
Authorization code extracted: 4/0AdLIr...
Exchanging authorization code for token...

======================================================================
✓ Authentication successful!
======================================================================
Token saved to: gdrive_token.json

You can now upload backups to Google Drive:
  python3 upload_to_gdrive.py
```

---

## 📤 LANGKAH 4: Upload Backup

Setelah autentikasi berhasil, upload backup:

```bash
cd /root/jadwalstream
python3 upload_to_gdrive.py
```

**Output:**
```
Backup file: /root/backupjadwalstream/jadwalstream_backup_20251105_012547.tar.gz
Size: 153.82 MB

Using token file: gdrive_token.json
Created new folder: JadwalStream_Backups
Uploading jadwalstream_backup_20251105_012547.tar.gz...
✓ Upload successful!
  File ID: 1abc123...
  Link: https://drive.google.com/file/d/...

✓ Backup uploaded to Google Drive successfully!
```

---

## 🚀 CARA CEPAT - Selanjutnya

Setelah autentikasi selesai (hanya sekali), untuk backup berikutnya cukup:

```bash
/root/jadwalstream/backup_and_upload.sh
```

Script ini otomatis:
1. Buat backup baru
2. Upload ke Google Drive
3. Tampilkan link

---

## ❓ Troubleshooting

### URL tidak bisa dibuka
- Pastikan copy URL lengkap
- Tidak ada spasi atau line break

### "Authorization code invalid"
- Code expired (berlaku 10 menit)
- Jalankan ulang dari LANGKAH 1

### "Error: No authorization code found in URL"
- Pastikan copy SELURUH URL dari browser
- URL harus mulai dengan `http://localhost:8080/?code=`

### Browser menampilkan error setelah klik Allow
- **NORMAL!** Browser tidak bisa connect ke localhost:8080
- Yang penting **copy URL dari address bar**
- URL tetap valid meski ada error

### Upload stuck/lambat
- Normal untuk file 154 MB
- Tunggu 2-5 menit tergantung internet

---

## 📋 Summary Commands

```bash
# STEP 1: Generate auth URL
python3 simple_auth_gdrive.py

# STEP 2: Open URL in browser, authorize, copy redirect URL

# STEP 3: Complete auth with copied URL
python3 complete_auth_gdrive.py 'PASTE_URL_HERE'

# STEP 4: Upload backup
python3 upload_to_gdrive.py

# Future backups (after auth done)
/root/jadwalstream/backup_and_upload.sh
```

---

## ✅ Verification

Cek di Google Drive:
1. Buka https://drive.google.com
2. Lihat folder **JadwalStream_Backups**
3. Download file untuk test restore
