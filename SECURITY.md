# Security & Privacy

## File yang TIDAK boleh di-commit ke Git

File-file berikut berisi data sensitif dan sudah dilindungi oleh `.gitignore`:

### Credentials & API Keys
- `client_secret.json` - Google OAuth credentials
- `license_credentials.json` - Google Sheets service account
- `tokens/*.json` - User OAuth tokens

### User Data
- `users.json` - Username, hashed passwords, roles

### Configuration
- `telegram_config.json` - Bot token & chat ID

### Database Files
- `live_streams.json` - Stream keys & RTMP URLs (SENSITIF!)
- `video_database.json` - Video metadata
- `thumbnail_database.json` - Thumbnail metadata
- `stream_mapping.json` - Stream mappings
- `schedule_config.json` - Scheduling data
- `scheduler_status.json` - Scheduler state
- `license_cache.json` - License cache

### Folders
- `videos/` - Video files
- `thumbnails/` - Thumbnail images
- `tokens/` - OAuth token files
- `ffmpeg_logs/` - Log files
- `backup/` - Backup files
- `__pycache__/` - Python cache

## Template Files (Safe to commit)

File template berikut **AMAN** untuk di-commit:
- `*.example` - Template configuration files
- Tidak berisi data sensitif
- User akan copy dan edit sesuai kebutuhan

## Verifikasi Sebelum Push

Sebelum push ke GitHub, selalu jalankan:

```bash
# Check file yang akan di-commit
git status

# Pastikan tidak ada file sensitif
git diff --cached

# Cari credential yang mungkin tercampur
grep -r "client_secret" .
grep -r "bot_token" .
grep -r "password" .
```

## Jika Accidental Commit

Jika tidak sengaja commit file sensitif:

```bash
# Remove dari git history (HATI-HATI!)
git rm --cached file_sensitif.json
git commit -m "Remove sensitive file"

# Untuk remove dari semua history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch file_sensitif.json" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (jika sudah push ke remote)
git push origin --force --all
```

⚠️ **Lebih baik**: Rotate/regenerate credentials yang ter-expose!

## Best Practices

1. ✅ **Selalu check** `.gitignore` sebelum commit
2. ✅ **Gunakan template** files untuk dokumentasi
3. ✅ **Review diff** sebelum push
4. ✅ **Rotate credentials** jika ter-expose
5. ✅ **Gunakan environment variables** untuk production
6. ❌ **Jangan** commit file `.env`
7. ❌ **Jangan** hardcode credentials di code
8. ❌ **Jangan** commit database files

## Environment Variables (Alternative)

Untuk production, consider menggunakan environment variables:

```bash
# .env file (add to .gitignore!)
GOOGLE_CLIENT_SECRET=/path/to/client_secret.json
TELEGRAM_BOT_TOKEN=your_bot_token
LICENSE_CREDENTIALS=/path/to/license_credentials.json
SECRET_KEY=your-secret-key-here
```

Lalu load di `app.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key')
```

## Reporting Security Issues

Jika menemukan vulnerability, jangan buat public issue. Contact maintainer secara private.
