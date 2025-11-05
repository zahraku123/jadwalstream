# License Management System with Google Apps Script

## Overview
Sistem lisensi JadwalStream menggunakan Google Apps Script sebagai backend API dan Google Sheets sebagai database. Sistem ini memungkinkan:
- Admin generate license key tanpa perlu tahu HWID user
- User activate license dengan auto-bind ke hardware mereka
- Validasi online dan offline (cached)
- License revocation dan reset HWID
- Tracking penggunaan license

## Arsitektur

```
┌─────────────┐         ┌──────────────────┐         ┌──────────────┐
│ JadwalStream│ ──────> │ Google Apps      │ ──────> │ Google       │
│ Python App  │ <────── │ Script (API)     │ <────── │ Sheets (DB)  │
└─────────────┘         └──────────────────┘         └──────────────┘
    (Client)                 (Backend)                  (Storage)
```

**Flow:**
1. Admin generate license di Google Sheets
2. User input license key di web app
3. Python app call Apps Script API
4. Apps Script bind HWID ke license di Sheets
5. Response di-cache locally untuk offline mode

---

## Step 1: Setup Google Sheets

### 1.1 Create New Spreadsheet

1. Buka https://sheets.google.com
2. Klik **Blank** untuk spreadsheet baru
3. Rename menjadi: **JadwalStream_Licenses**

### 1.2 Initialize Sheet Structure

**Option A: Automatic (Recommended)**

1. Di Google Sheets, klik **Extensions > Apps Script**
2. Paste code dari `/root/jadwalstream/apps_script/Code.gs`
3. Klik **Save** (Ctrl+S)
4. Refresh halaman Google Sheets
5. Akan muncul menu baru: **License Manager**
6. Klik **License Manager > Initialize Sheet**
7. Sheet akan otomatis dibuat dengan headers

**Option B: Manual**

Buat sheet dengan nama `Licenses` dan kolom berikut:

| A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|
| License Key | Email | HWID | Status | Created Date | Activated Date | Expiry Date | Duration (Days) | Last Check | Notes |

**Keterangan Kolom:**
- **License Key**: Kode lisensi unik (e.g., ABCDE-12345-FGHIJ-67890)
- **Email**: Email user (opsional)
- **HWID**: Hardware ID (auto-filled saat aktivasi)
- **Status**: `pending`, `active`, `expired`, `revoked`
- **Created Date**: Tanggal generate license
- **Activated Date**: Tanggal user activate
- **Expiry Date**: Tanggal kadaluarsa
- **Duration (Days)**: Durasi license (default: 365)
- **Last Check**: Timestamp terakhir validasi
- **Notes**: Catatan admin

---

## Step 2: Deploy Apps Script

### 2.1 Open Apps Script Editor

1. Di Google Sheets yang sudah dibuat
2. Klik **Extensions > Apps Script**
3. Browser akan membuka Apps Script editor

### 2.2 Copy Script Code

1. Hapus semua kode default di `Code.gs`
2. Copy seluruh kode dari file `/root/jadwalstream/apps_script/Code.gs`
3. Paste ke Apps Script editor
4. **PENTING:** Edit line API_KEY:
   ```javascript
   const API_KEY = 'YOUR_SECRET_API_KEY_HERE'; // Change this!
   ```
   Ganti dengan API key yang kuat, contoh:
   ```javascript
   const API_KEY = 'JadwalStream2024SecureKey!@#$';
   ```
   **Simpan API key ini, akan dipakai di config!**

5. Klik **Save** (icon disket atau Ctrl+S)
6. Rename project (klik "Untitled project"): **JadwalStream License API**

### 2.3 Deploy as Web App

1. Klik **Deploy > New deployment**
2. Klik **Select type** → Pilih **Web app**
3. Isi form deployment:
   - **Description**: `JadwalStream License API v1`
   - **Execute as**: `Me (your_email@gmail.com)`
   - **Who has access**: `Anyone` 
     > **Penting:** Pilih "Anyone" agar app Python bisa akses API
4. Klik **Deploy**
5. Dialog permission akan muncul:
   - Klik **Authorize access**
   - Pilih akun Google Anda
   - Klik **Advanced** (jika muncul warning)
   - Klik **Go to JadwalStream License API (unsafe)**
   - Klik **Allow**
6. Copy **Web app URL** yang muncul:
   ```
   https://script.google.com/macros/s/AKfycbx.../exec
   ```
   **Simpan URL ini!**

### 2.4 Test Deployment

Test via browser atau curl:

```bash
curl "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec"
```

**Expected response:**
```json
{
  "status": "JadwalStream License System",
  "version": "1.0",
  "message": "Use POST requests to interact with the API"
}
```

---

## Step 3: Configure Python App

### 3.1 Create License Config

1. Copy example config:
   ```bash
   cd /root/jadwalstream
   cp license_config.json.example license_config.json
   ```

2. Edit `license_config.json`:
   ```bash
   nano license_config.json
   ```

3. Isi dengan URL dan API key:
   ```json
   {
     "apps_script_url": "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec",
     "admin_api_key": "JadwalStream2024SecureKey!@#$"
   }
   ```

4. **PENTING:** Jangan commit file ini ke git!
   ```bash
   echo "license_config.json" >> .gitignore
   ```

### 3.2 Test License Validator

```bash
cd /root/jadwalstream
python3 license_validator.py
```

**Expected output:**
```
=== License Validator Test ===

System Info:
  OS: Linux
  Hostname: your-server
  HWID: ABC123DEF456...

License Status: ✗ INVALID
Message: Tidak ada lisensi aktif untuk device ini.
```

---

## Step 4: Admin - Generate License

Ada 3 cara generate license:

### Method 1: Via Google Sheets Menu (Easiest)

1. Buka Google Sheets
2. Klik **License Manager > Generate License**
3. Input format: `email,days`
   - Contoh: `user@example.com,365`
   - Atau kosongkan email: `,365`
4. Klik **OK**
5. Dialog akan tampilkan license key:
   ```
   License Key: ABCDE-12345-FGHIJ-67890
   Email: user@example.com
   Duration: 365 days
   ```
6. Copy license key dan kirim ke user

### Method 2: Via Apps Script Editor

1. Buka **Extensions > Apps Script**
2. Di editor, klik fungsi `generateLicense`
3. Klik **Run**
4. Check sheet, license baru akan muncul

### Method 3: Via API (Advanced)

```bash
curl -X POST "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "generate",
    "api_key": "YOUR_SECRET_API_KEY",
    "email": "user@example.com",
    "duration_days": 365,
    "notes": "Generated via API"
  }'
```

**Response:**
```json
{
  "success": true,
  "license_key": "ABCDE-12345-FGHIJ-67890",
  "email": "user@example.com",
  "duration_days": 365,
  "message": "License generated successfully"
}
```

---

## Step 5: User - Activate License

### 5.1 Via Web Interface

1. User buka aplikasi JadwalStream
2. Login dengan credentials
3. Klik menu **License** di sidebar
4. Input license key yang diterima dari admin
5. Klik **Activate License**
6. HWID akan otomatis ter-bind
7. License langsung aktif!

### 5.2 Via Command Line (for testing)

```python
from license_validator import LicenseValidator

validator = LicenseValidator()
success, message = validator.activate_license('ABCDE-12345-FGHIJ-67890')

if success:
    print("✓", message)
else:
    print("✗", message)
```

---

## Admin Operations

### Revoke License

Jika perlu mencabut lisensi user:

**Via API:**
```bash
curl -X POST "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "revoke",
    "api_key": "YOUR_SECRET_API_KEY",
    "license_key": "ABCDE-12345-FGHIJ-67890"
  }'
```

**Via Google Sheets:**
1. Buka sheet
2. Cari license key yang ingin di-revoke
3. Ubah kolom **Status** dari `active` menjadi `revoked`
4. User akan langsung tidak bisa akses

### Reset HWID

Jika user ganti device dan perlu activate ulang:

**Via API:**
```bash
curl -X POST "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "reset_hwid",
    "api_key": "YOUR_SECRET_API_KEY",
    "license_key": "ABCDE-12345-FGHIJ-67890"
  }'
```

**Via Google Sheets:**
1. Buka sheet
2. Cari license key
3. Hapus value di kolom **HWID**
4. Ubah **Status** menjadi `pending`
5. User bisa activate ulang di device baru

### Extend License Duration

1. Buka Google Sheets
2. Cari license key
3. Edit kolom **Expiry Date** ke tanggal baru
4. User akan langsung mendapat update saat verify online

---

## API Endpoints Reference

Base URL: `https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec`

### 1. Generate License

**Request:**
```json
{
  "action": "generate",
  "api_key": "YOUR_SECRET_API_KEY",
  "email": "user@example.com",
  "duration_days": 365,
  "notes": "Optional notes"
}
```

**Response:**
```json
{
  "success": true,
  "license_key": "ABCDE-12345-FGHIJ-67890",
  "email": "user@example.com",
  "duration_days": 365,
  "message": "License generated successfully"
}
```

### 2. Activate License

**Request:**
```json
{
  "action": "activate",
  "license_key": "ABCDE-12345-FGHIJ-67890",
  "hwid": "ABC123DEF456..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "License activated successfully",
  "license_key": "ABCDE-12345-FGHIJ-67890",
  "hwid": "ABC123DEF456...",
  "status": "active",
  "activated_date": "2025-11-05 12:30:00",
  "expiry_date": "2026-11-05",
  "days_remaining": 365
}
```

### 3. Validate License

**Request:**
```json
{
  "action": "validate",
  "hwid": "ABC123DEF456..."
}
```

**Response (Valid):**
```json
{
  "success": true,
  "message": "License is valid",
  "license_key": "ABCDE-12345-FGHIJ-67890",
  "hwid": "ABC123DEF456...",
  "status": "active",
  "expiry_date": "2026-11-05",
  "days_remaining": 365
}
```

**Response (Invalid):**
```json
{
  "success": false,
  "message": "No active license found for this device"
}
```

### 4. Revoke License

**Request:**
```json
{
  "action": "revoke",
  "api_key": "YOUR_SECRET_API_KEY",
  "license_key": "ABCDE-12345-FGHIJ-67890"
}
```

### 5. Reset HWID

**Request:**
```json
{
  "action": "reset_hwid",
  "api_key": "YOUR_SECRET_API_KEY",
  "license_key": "ABCDE-12345-FGHIJ-67890"
}
```

---

## Troubleshooting

### Issue 1: "Apps Script URL not configured"

**Solusi:**
```bash
# Pastikan file config ada
cat /root/jadwalstream/license_config.json

# Jika belum ada, copy dari example
cp license_config.json.example license_config.json
nano license_config.json
```

### Issue 2: "Invalid API key"

**Solusi:**
- Pastikan API key di `license_config.json` sama dengan di Apps Script
- Check API key di Apps Script editor (line `const API_KEY`)

### Issue 3: "Request timeout"

**Solusi:**
- Check koneksi internet
- Verify Apps Script deployment masih active
- Test URL di browser

### Issue 4: "License not found"

**Solusi:**
- Check license key typo
- Verify license ada di Google Sheets
- Pastikan sheet name adalah "Licenses"

### Issue 5: Permission Denied

**Solusi:**
- Re-deploy Apps Script dengan access "Anyone"
- Clear authorization dan authorize ulang
- Check Apps Script execution logs

### Issue 6: Update Deployment

Jika edit code Apps Script:

1. Klik **Deploy > Manage deployments**
2. Klik **Edit** (icon pensil)
3. Ubah **Version** menjadi **New version**
4. Klik **Deploy**
5. URL tetap sama, tidak perlu update config

---

## Security Best Practices

1. **API Key:**
   - Gunakan API key yang kuat (min 20 karakter)
   - Jangan share atau commit ke git
   - Ganti periodic (setiap 6 bulan)

2. **Google Sheets:**
   - Jangan share spreadsheet publicly
   - Share hanya ke admin yang diperlukan
   - Enable 2FA untuk akun Google

3. **Apps Script:**
   - Deploy dengan access "Anyone" tapi protect dengan API key
   - Monitor execution logs untuk aktivitas mencurigakan
   - Set quota/limit jika perlu

4. **License Keys:**
   - Generate secara random
   - Track siapa dapat license apa
   - Document di kolom Notes

---

## Monitoring

### Check Apps Script Logs

1. Buka **Extensions > Apps Script**
2. Klik **Executions** (icon stopwatch)
3. Lihat history API calls dan errors

### Monitor License Usage

Di Google Sheets, lihat:
- Kolom **Last Check**: Kapan terakhir user verify
- Kolom **Status**: License masih aktif atau expired
- Filter expired licenses:
  - Klik kolom **Status**
  - Filter: `expired`

### Auto-alert (Optional)

Tambahkan script untuk email notification:

```javascript
function notifyExpiringSoon() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Licenses');
  const data = sheet.getDataRange().getValues();
  
  const now = new Date();
  const weekFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
  
  for (let i = 1; i < data.length; i++) {
    const expiryDate = new Date(data[i][6]); // Expiry Date column
    const email = data[i][1]; // Email column
    
    if (expiryDate < weekFromNow && expiryDate > now && email) {
      MailApp.sendEmail({
        to: email,
        subject: 'License Expiring Soon',
        body: `Your JadwalStream license will expire on ${expiryDate.toDateString()}`
      });
    }
  }
}
```

Set trigger: **Triggers > Add Trigger** → Daily

---

## Summary

✅ **Files Created:**
- `/root/jadwalstream/apps_script/Code.gs` - Apps Script backend
- `/root/jadwalstream/license_validator.py` - Updated validator
- `/root/jadwalstream/license_config.json.example` - Config template
- `/root/jadwalstream/templates/license.html` - UI template

✅ **Setup Steps:**
1. Create Google Sheets dengan struktur licenses
2. Deploy Apps Script sebagai Web App
3. Copy deployment URL
4. Configure `license_config.json`
5. Admin generate license via Sheets
6. User activate via web interface

✅ **Result:**
- Admin dapat generate license tanpa perlu tahu HWID user
- User input license key → auto-bind HWID
- Online + offline validation
- Full tracking di Google Sheets
