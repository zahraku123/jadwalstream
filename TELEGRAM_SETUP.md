# Telegram Notification Setup Guide

## Overview

Aplikasi ini mendukung notifikasi Telegram untuk berbagai event scheduling:
- ✅ Schedule berhasil dibuat
- 🚀 Stream mulai live
- 🛑 Stream selesai
- ❌ Error saat membuat schedule

## Setup Steps

### 1. Buat Telegram Bot

1. Buka Telegram dan cari **@BotFather**
2. Send `/newbot` untuk membuat bot baru
3. Ikuti instruksi:
   - Beri nama bot (contoh: "My Stream Scheduler Bot")
   - Beri username bot (harus diakhiri dengan "bot", contoh: "mystreamscheduler_bot")
4. **Simpan Bot Token** yang diberikan (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Dapatkan Chat ID

**Untuk Personal Chat:**
1. Cari **@userinfobot** di Telegram
2. Send `/start`
3. Bot akan memberikan **Chat ID** Anda (angka positif, contoh: `123456789`)

**Untuk Group Chat:**
1. Tambahkan bot Anda ke group
2. Send pesan apa saja di group
3. Buka URL ini di browser (ganti `YOUR_BOT_TOKEN` dengan token bot Anda):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
4. Cari `"chat":{"id":` dalam response
5. **Chat ID group** biasanya angka negatif (contoh: `-1001234567890`)

### 3. Start Conversation dengan Bot

Penting! Sebelum bot bisa mengirim pesan:
1. Cari bot Anda di Telegram (gunakan username yang Anda buat)
2. Send `/start` ke bot
3. Bot sekarang bisa mengirim pesan ke Anda

### 4. Configure di Aplikasi

1. Login sebagai **Admin**
2. Buka menu **Telegram Notifications** di sidebar
3. Isi form:
   - **Enable Notifications**: Toggle ON
   - **Bot Token**: Paste token dari BotFather
   - **Chat ID**: Paste chat ID Anda atau group
4. Click **Save Settings**
5. Click **Test Connection** untuk verifikasi

## Notification Types

### 1. Schedule Created ✅
Dikirim saat jadwal berhasil dibuat di YouTube Studio:
```
🎬 Schedule Created Successfully!

📺 Title: My Stream Title
🕐 Scheduled Time: 2024-01-15T20:00:00Z
🔗 Link: [Open in YouTube Studio]

✅ Your stream is ready to go live!
```

### 2. Stream Starting 🚀
Dikirim saat stream mulai live:
```
🚀 Stream Starting Now!

📺 Title: My Stream Title
🕐 Time: 2024-01-15T20:00:00Z
🔗 Link: [Open Stream]

🎥 Your livestream is going live!
```

### 3. Stream Ended 🛑
Dikirim saat stream selesai:
```
🛑 Stream Ended

📺 Title: My Stream Title
⏱ Duration: 2h 30m

✅ Stream completed successfully!
```

### 4. Error Notification ❌
Dikirim saat ada error:
```
❌ Schedule Creation Failed

📺 Title: My Stream Title
⚠️ Error: [error message]

Please check the application logs for details.
```

## Troubleshooting

### Bot tidak mengirim pesan

1. **Check Bot Token**
   - Pastikan token benar dan tidak ada spasi
   - Token format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

2. **Check Chat ID**
   - Personal chat: angka positif (contoh: `123456789`)
   - Group chat: angka negatif (contoh: `-1001234567890`)
   - Pastikan tidak ada spasi

3. **Bot belum di-start**
   - Buka chat dengan bot
   - Send `/start`
   - Tunggu response dari bot

4. **Group Chat Issues**
   - Pastikan bot sudah ditambahkan ke group
   - Bot harus punya permission untuk send messages
   - Untuk group private, bot perlu diinvite

### Test Connection Failed

**"Bot authentication failed"**
- Token salah atau expired
- Buat bot baru atau cek token dari @BotFather

**"Failed to send test message. Check chat_id."**
- Chat ID salah
- Anda belum start conversation dengan bot
- Untuk group: pastikan bot sudah ditambahkan

**"Connection timeout"**
- Check internet connection
- Firewall mungkin memblokir Telegram API
- Coba lagi beberapa saat

## Security Notes

⚠️ **PENTING:**
- **Jangan share Bot Token** dengan orang lain
- Bot token = full control atas bot Anda
- File `telegram_config.json` sudah di-gitignore
- Backup token di tempat aman

## Features

- ✅ HTML formatting support untuk pesan yang lebih menarik
- ✅ Clickable links ke YouTube Studio
- ✅ Emoji untuk visual yang lebih baik
- ✅ Auto-retry dengan error handling
- ✅ Connection test di UI
- ✅ Admin-only access

## API Reference

Module `telegram_notifier.py` menyediakan fungsi:

```python
# Send schedule created notification
notify_schedule_created(title, scheduled_time, broadcast_link)

# Send stream starting notification
notify_stream_starting(title, scheduled_time, broadcast_link)

# Send stream ended notification
notify_stream_ended(title, duration=None)

# Send error notification
notify_schedule_error(title, error_message)

# Test bot connection
test_connection()  # Returns (success, message)
```

## FAQ

**Q: Bisakah saya menggunakan group chat?**
A: Ya, dapatkan group chat ID dan pastikan bot sudah ditambahkan ke group.

**Q: Bisakah multiple users menerima notifikasi?**
A: Ya, gunakan group chat dan invite semua users ke group.

**Q: Apakah notifikasi bekerja untuk auto-schedule?**
A: Ya, notifikasi dikirim baik untuk manual maupun auto-schedule.

**Q: Bisakah saya disable notifikasi sementara?**
A: Ya, toggle OFF "Enable Notifications" di halaman settings.

**Q: Apakah ada limit pesan?**
A: Telegram bot limit: 30 pesan per detik. Aplikasi ini jauh di bawah limit tersebut.

## Support

Jika mengalami masalah:
1. Test connection di halaman settings
2. Check application logs untuk error details
3. Verify bot token dan chat ID
4. Pastikan bot sudah di-start
