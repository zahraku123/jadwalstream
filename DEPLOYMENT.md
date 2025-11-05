# Deployment Guide

## Tailwind CSS untuk Production di VPS

### ⚠️ PENTING: Build CSS Sebelum Upload ke VPS

File `static/css/output.css` **HARUS** sudah di-build di local sebelum di-upload ke VPS.

## Langkah Deployment

### 1. Build CSS di Local (Windows)

Sebelum upload ke VPS, jalankan:

```bash
# Build production CSS (minified)
.\tailwindcss.exe -i .\static\css\input.css -o .\static\css\output.css --minify

# ATAU menggunakan npm
npm run build:css
```

### 2. Commit dan Push

```bash
git add static/css/output.css
git commit -m "Build production CSS"
git push
```

### 3. Upload ke VPS

**Opsi A: Via Git**
```bash
cd /path/to/jadwalstream
git pull origin main
```

**Opsi B: Via SCP/FTP**
Upload file-file berikut:
- `static/css/output.css` ✅ (WAJIB)
- `templates/base.html` ✅ (sudah diupdate untuk gunakan local CSS)
- Semua file Python dan template lainnya

**Opsi C: Upload Semua File (kecuali yang di .gitignore)**

### 4. Restart Aplikasi di VPS

```bash
# Jika menggunakan systemd
sudo systemctl restart jadwalstream

# Jika menggunakan supervisor
sudo supervisorctl restart jadwalstream

# Jika manual
pkill -f "python.*app.py"
python3 app.py
```

### 5. Clear Browser Cache

Di browser, tekan:
- **Windows/Linux**: `Ctrl + Shift + R` atau `Ctrl + F5`
- **Mac**: `Cmd + Shift + R`

## File Yang Perlu Ada di VPS

### ✅ WAJIB Ada:
- `static/css/output.css` - Production CSS (hasil build)
- `templates/base.html` - Sudah reference local CSS
- `templates/` - Semua file template
- `static/css/dark-theme.css` - Custom dark theme
- `static/css/cyber-additions.css` - Custom cyber styles

### ❌ TIDAK Perlu Ada di VPS:
- `tailwindcss.exe` - Binary Windows, tidak jalan di Linux
- `static/css/input.css` - Source file, tidak dipakai di production
- `tailwind.config.js` - Config file, tidak dipakai di production
- `node_modules/` - Dependencies npm, tidak dipakai di production
- `package.json` - Hanya untuk development
- `package-lock.json` - Hanya untuk development

## Update CSS di Masa Depan

Jika Anda menambah/mengubah styling:

1. **Edit di local**: 
   - Ubah file `static/css/input.css`
   - Atau ubah Tailwind classes di template

2. **Rebuild CSS**:
   ```bash
   npm run build:css
   ```

3. **Upload output.css baru ke VPS**:
   ```bash
   git add static/css/output.css
   git commit -m "Update CSS styles"
   git push
   # Di VPS: git pull
   ```

4. **Restart aplikasi & clear cache**

## Troubleshooting di VPS

### CSS tidak muncul / tampilan rusak:

1. **Cek file output.css ada dan tidak kosong**:
   ```bash
   ls -lh static/css/output.css
   # Ukuran seharusnya ~48-50KB
   ```

2. **Cek permissions**:
   ```bash
   chmod 644 static/css/output.css
   ```

3. **Cek Flask static route**:
   ```bash
   curl http://localhost:5000/static/css/output.css
   # Seharusnya return CSS content
   ```

4. **Clear browser cache** dengan hard refresh

### CSS masih pakai CDN:

Cek `templates/base.html`, pastikan ada:
```html
<!-- BENAR ✅ -->
<link href="{{ url_for('static', filename='css/output.css') }}" rel="stylesheet">

<!-- SALAH ❌ -->
<script src="https://cdn.tailwindcss.com"></script>
```

## Alternative: Build di VPS (Tidak Recommended)

Jika Anda benar-benar ingin build di VPS:

```bash
# Install Node.js di VPS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Tailwind
npm install

# Build CSS
npm run build:css
```

**Tapi ini TIDAK RECOMMENDED karena:**
- Menambah dependencies di server production
- Memakan waktu dan resources
- Lebih baik build di local dan upload hasilnya

## Kesimpulan

**✅ CARA TERBAIK:**
1. Build `output.css` di local Windows
2. Commit file `output.css` ke git
3. Pull/upload ke VPS
4. Restart aplikasi

File CSS sudah production-ready dan tidak perlu Node.js/npm di VPS!
