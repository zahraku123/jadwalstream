# Telegram Notification Troubleshooting

## Test Berhasil Tapi Notifikasi Tidak Terkirim Saat Schedule

### Kemungkinan Penyebab:

1. **Aplikasi tidak restart setelah update kode**
   - Solusi: Restart aplikasi Flask
   ```bash
   # Stop aplikasi
   Ctrl + C
   
   # Start lagi
   python app.py
   ```

2. **Exception ter-catch tapi tidak terlihat**
   - Check log aplikasi untuk error
   - Log akan menampilkan `[TELEGRAM]` prefix

3. **Schedule dibuat sebelum konfigurasi Telegram disimpan**
   - Pastikan Telegram settings sudah disave
   - Coba buat schedule baru setelah configure Telegram

### Cara Debug:

#### 1. Check Log Aplikasi
Saat membuat schedule, log harus menampilkan:
```
[TELEGRAM] Sending notification for: [judul schedule]
[TELEGRAM] Sending message to chat_id: [chat_id]
[TELEGRAM] Message sent successfully
[TELEGRAM] Notification sent successfully
```

Jika tidak muncul, berarti fungsi tidak dipanggil atau error terjadi sebelum sampai ke telegram_notifier.

#### 2. Test Manual
Jalankan test script:
```bash
python test_telegram.py
```

Jika test berhasil tapi schedule tidak mengirim notif, berarti:
- Ada error di integrasi
- Aplikasi belum restart
- Kode lama masih running

#### 3. Check telegram_config.json
```bash
cat telegram_config.json
```

Pastikan isinya:
```json
{
  "enabled": true,
  "bot_token": "YOUR_BOT_TOKEN",
  "chat_id": "YOUR_CHAT_ID"
}
```

#### 4. Restart Aplikasi
**PENTING:** Setelah update kode atau konfigurasi Telegram:
1. Stop Flask app (Ctrl+C)
2. Start lagi: `python app.py`

### Error Messages dan Solusinya:

#### "Notifications are disabled or not configured"
- Buka Telegram Settings di aplikasi
- Toggle ON "Enable Notifications"
- Save settings
- Restart aplikasi

#### "Failed to send message. Status: 400"
- Bot token salah
- Check token dari @BotFather
- Update di settings

#### "Failed to send message. Status: 403"
- Bot diblokir atau belum di-start
- Buka chat dengan bot
- Send `/start`
- Coba lagi

#### "Chat not found"
- Chat ID salah
- Check dari @userinfobot
- Update di settings

### Checklist Verifikasi:

- [ ] Bot sudah dibuat di @BotFather
- [ ] Bot token sudah di-copy
- [ ] Chat ID sudah didapat dari @userinfobot
- [ ] Sudah send `/start` ke bot
- [ ] Settings sudah disimpan di aplikasi
- [ ] Toggle "Enable Notifications" ON
- [ ] Test connection SUCCESS
- [ ] File `telegram_config.json` exists dan benar
- [ ] Aplikasi Flask sudah di-restart
- [ ] Log aplikasi menampilkan `[TELEGRAM]` messages

### Debug Mode:

Untuk melihat log detail, tambahkan di `app.py` atau `live.py`:
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Common Issues:

**Issue:** Test berhasil tapi schedule tidak mengirim notif

**Solusi:**
1. Check apakah kode sudah benar di-integrate
2. Restart aplikasi Flask
3. Check log untuk error messages
4. Pastikan `telegram_config.json` enabled = true

**Issue:** Notif terkirim tapi format rusak

**Solusi:**
- HTML tags tidak support: gunakan tag yang valid (b, i, a, code, pre)
- URL harus lengkap dengan http:// atau https://
- Check response dari Telegram API

**Issue:** Notif terkirim untuk manual schedule tapi tidak untuk auto-schedule

**Solusi:**
- Check `live.py` sudah import telegram_notifier
- Pastikan notifikasi dipanggil di bagian yang benar
- Auto-schedule mungkin running di process terpisah - restart aplikasi

### Quick Fix:

Jika semua sudah benar tapi tidak work:

1. **Stop semua Python process**
   ```bash
   # Windows
   taskkill /F /IM python.exe
   
   # Linux/Mac
   pkill python
   ```

2. **Delete cache**
   ```bash
   rm -rf __pycache__
   rm *.pyc
   ```

3. **Restart aplikasi**
   ```bash
   python app.py
   ```

4. **Test lagi**
   ```bash
   python test_telegram.py
   ```

### Need More Help?

Check these files for integration points:
- `app.py` line ~1771: notification di run_schedule_now
- `live.py` line ~239: notification di auto-scheduler  
- `telegram_notifier.py`: notification functions

Look for:
```python
telegram_notifier.notify_schedule_created(...)
```

Dan pastikan ada log:
```python
logging.info(f"[TELEGRAM] Sending notification...")
```
