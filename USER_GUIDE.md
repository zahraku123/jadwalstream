# JadwalStream - Panduan Pengguna

## 🎯 Quick Start Guide

### 1. Login
1. Buka aplikasi di browser
2. Login dengan username & password
3. Default admin: `admin` / `admin123`

### 2. Setup YouTube Token (Wajib untuk YouTube Scheduling)
1. Buka menu **Token Channel**
2. Click **Create New Token**
3. Masukkan nama token (misal: `channel1.json`)
4. Follow OAuth flow di browser
5. Token tersimpan otomatis

### 3. Buat Schedule YouTube
1. Buka menu **Schedules**
2. Click **Add New Schedule**
3. Isi form:
   - Title & Description
   - Scheduled Start Time
   - Pilih Token
   - Privacy Status
   - Settings (Auto Start/Stop, Kids, Repeat Daily)
   - Thumbnail (opsional)
4. Submit
5. Check Telegram untuk notifikasi!

---

## 📚 Panduan Lengkap Per Fitur

### A. YouTube Schedule Management

#### Membuat Schedule Baru
**Path:** Schedules > Add New Schedule

**Steps:**
1. **Basic Info:**
   - Title: Judul stream
   - Description: Deskripsi stream
   - Scheduled Time: Kapan stream mulai

2. **Account:**
   - Token File: Pilih akun YouTube yang akan digunakan
   - Privacy Status: Public/Unlisted/Private

3. **Stream Settings:**
   - Use Existing Stream: Check jika mau pakai stream yang sudah ada
   - Stream Selection: Pilih stream dari dropdown

4. **Automation:**
   - ✅ Auto Start: Stream mulai otomatis
   - ✅ Auto Stop: Stream stop otomatis
   - ✅ Made for Kids: Untuk konten anak
   - ✅ Repeat Daily: Jadwal ulang setiap hari +1 hari

5. **Thumbnail:**
   - Pilih thumbnail dari gallery (opsional)
   - Preview langsung muncul

6. **Submit**
   - Schedule tersimpan
   - Notifikasi Telegram terkirim (jika enabled)

#### Edit Schedule
- Click tombol **Edit** (icon pensil) di card schedule
- Update informasi
- Save Changes

#### Run Schedule NOW
- Click **Jadwal Sekarang** untuk execute immediately
- Schedule langsung dijalankan tanpa tunggu waktu

#### Delete Schedule
- Click tombol **Delete** (icon trash)
- Confirm deletion

---

### B. Live Streaming (RTMP)

#### Membuat Live Stream Schedule
**Path:** Live Streaming > Add New Schedule

**Steps:**
1. **Select Video:**
   - Pilih video dari library
   - Preview thumbnail

2. **Platform:**
   - YouTube / Facebook / Twitch / Instagram / TikTok / Custom
   - Server URL & Stream Key

3. **Schedule:**
   - Start Date & Time
   - Duration (opsional)

4. **Thumbnail:**
   - Upload atau pilih dari gallery

5. **Submit**

#### Upload Video
1. Click **Upload Local** atau **Upload Drive**
2. Pilih file video
3. Wait upload complete
4. Video masuk library

#### Start Stream NOW
- Click **Start Now** untuk mulai streaming immediately
- FFmpeg process akan jalan
- Monitor di dashboard

#### Cancel Stream
- Click **Cancel** untuk stop running stream
- Process terminated gracefully

---

### C. Media Management

#### Upload Video
**Path:** Video Gallery > Upload Local

1. Click **Upload Local**
2. Pilih video file
3. Fill title & description
4. Upload
5. Video ready untuk digunakan

#### Import dari Google Drive
**Path:** Video Gallery > Upload Drive

1. Click **Upload Drive**
2. Paste Google Drive file ID
3. Fill title & description
4. Import
5. Video downloaded & ready

#### Upload Thumbnail
**Path:** Thumbnail Gallery > Upload Thumbnail

1. Click **Upload Thumbnail**
2. Pilih image file (PNG/JPG)
3. Fill title & description
4. Upload
5. Thumbnail ready untuk schedules

#### Delete Media
- Click **Delete** button
- Confirm deletion
- File removed dari storage

---

### D. Token Management

#### Create YouTube Token
**Path:** Token Channel > Create New Token

1. Click **Create New Token**
2. Enter token name (misal: `mychannel.json`)
3. Browser terbuka untuk OAuth
4. Login ke Google account
5. Allow permissions
6. Paste authorization code
7. Token created & saved

#### Delete Token
- Click **Delete** next to token
- Confirm deletion
- Token removed (schedules using this token affected)

---

### E. Stream Keys Management

#### Fetch Stream Keys
**Path:** Stream Keys > Fetch for [Token]

1. Pilih token
2. Click **Fetch Stream Keys**
3. Stream keys downloaded dari YouTube
4. Auto-mapped ke stream IDs

#### View Mappings
- See all stream mappings per token
- Stream ID → Stream Name
- Creation info

#### Export Mappings
- Click **Export** untuk download mapping file
- Backup purposes

---

### F. Dashboard & Monitoring

#### System Stats
**Path:** Dashboard (Homepage)

**Real-time Metrics:**
- CPU Usage %
- Memory Usage %
- Disk Usage %
- System Info

**Refresh:**
- Auto-refresh every 5 seconds
- Manual refresh available

#### Schedule Stats
- Total Schedules
- Completed count
- Pending count
- Success rate

#### Activity Log
- Recent actions
- User activity
- Timestamps

---

### G. Telegram Notifications

#### Setup Telegram Bot
**Path:** Settings > Telegram Notifications (Admin only)

**Steps:**

1. **Create Bot:**
   - Open Telegram
   - Search `@BotFather`
   - Send `/newbot`
   - Follow instructions
   - Copy Bot Token

2. **Get Chat ID:**
   - Search `@userinfobot`
   - Send `/start`
   - Copy your Chat ID

3. **Start Bot:**
   - Search your bot
   - Send `/start` to activate

4. **Configure in App:**
   - Open Telegram Settings
   - Toggle ON "Enable Notifications"
   - Paste Bot Token
   - Paste Chat ID
   - Click **Save Settings**
   - Click **Test Connection**

5. **Verify:**
   - Should receive test message
   - Ready to receive notifications!

#### Notification Events
**You'll receive notifications for:**
- ✅ Schedule created successfully
- 🚀 Stream starting
- 🛑 Stream ended
- ❌ Errors

---

### H. User Management (Admin Only)

#### View Users
**Path:** Admin > Users

- See all registered users
- Username, role, created date

#### Create User
1. Click **Add New User**
2. Fill username & password
3. Select role (Admin/User/Demo)
4. Submit

#### Change User Role
- Select new role dari dropdown
- Click **Change Role**
- Role updated

#### Delete User
- Click **Delete** button
- Confirm deletion
- User removed

#### Change Password
1. Click **Change Password**
2. Enter new password
3. Confirm
4. Password updated

---

### I. License Management

#### Activate License
**Path:** License

1. Enter license key
2. Click **Activate**
3. Validation from Google Sheets
4. License activated if valid

#### Check License Info
- HWID displayed
- License status
- Expiry date
- System information

---

## 🎓 Tips & Best Practices

### For YouTube Scheduling

1. **Use Descriptive Titles**
   - Clear, searchable titles
   - Include keywords

2. **Set Correct Time**
   - Check timezone
   - Add buffer time (5-10 minutes early)

3. **Use Repeat Daily**
   - For regular broadcasts
   - Auto +1 day after completion

4. **Test with Unlisted First**
   - Test schedules as unlisted
   - Change to public when confident

5. **Use Thumbnails**
   - Professional thumbnails = more views
   - Upload to gallery for reuse

### For RTMP Streaming

1. **Test Stream Keys**
   - Verify RTMP URL & key
   - Test dengan stream pendek dulu

2. **Check Video Format**
   - MP4 recommended
   - H.264 codec untuk compatibility

3. **Monitor Resources**
   - Check CPU/Memory usage
   - Multiple streams = high resource usage

4. **Use Quality Videos**
   - Higher quality = better stream
   - 1080p atau 720p optimal

### For Multi-Account Management

1. **Organize Tokens**
   - Clear naming: `channel1.json`, `gaming.json`
   - One token per YouTube account

2. **Map Streams Properly**
   - Fetch keys regularly
   - Keep mappings updated

3. **Schedule Distribution**
   - Distribute schedules across accounts
   - Avoid spam detection

### For Telegram Notifications

1. **Use Group Chat**
   - Create Telegram group
   - Add bot to group
   - All team members get notifs

2. **Test Regularly**
   - Test connection di settings page
   - Verify notifs received

3. **Keep Bot Active**
   - Don't block bot
   - Don't delete chat

### Security Best Practices

1. **Change Default Password**
   - Change admin password immediately
   - Use strong passwords

2. **Use Demo Role**
   - For read-only access
   - Show without risk

3. **Backup Regularly**
   - Backup tokens folder
   - Backup databases
   - Backup videos/thumbnails

4. **Don't Share Tokens**
   - Token = full account access
   - Keep credentials secure

---

## 🆘 Troubleshooting

### Schedule Tidak Terkirim ke YouTube

**Check:**
1. Token masih valid?
2. Scheduled time sudah lewat?
3. Internet connection OK?
4. Check logs untuk error

**Solution:**
- Re-authorize token
- Use "Run Schedule NOW"
- Check YouTube quota

### Stream Tidak Jalan

**Check:**
1. FFmpeg installed?
2. Video file exists?
3. RTMP URL & key correct?
4. Internet bandwidth sufficient?

**Solution:**
- Test RTMP credentials
- Use smaller video untuk test
- Check process logs

### Telegram Notif Tidak Masuk

**Check:**
1. Bot token correct?
2. Chat ID correct?
3. Already /start bot?
4. Notifications enabled?

**Solution:**
- Run `python test_telegram.py`
- Re-configure settings
- Restart aplikasi

### Login Tidak Bisa

**Check:**
1. Username/password benar?
2. User exists?
3. Not locked out?

**Solution:**
- Check users.json
- Reset password via admin
- Re-create user

---

## 📱 Mobile Usage

### Optimized for Mobile
- ✅ All pages responsive
- ✅ Touch-friendly buttons
- ✅ Mobile navigation
- ✅ Optimized forms

### Tips for Mobile
1. Use portrait mode untuk forms
2. Landscape untuk galleries
3. Swipe untuk navigation
4. Pinch zoom untuk images

---

## 🔧 Advanced Features

### Custom FFmpeg Arguments
- Edit live stream
- Add custom FFmpeg flags
- For advanced users

### Stream Mapping Export
- Backup your mappings
- Import to other instances
- Version control

### API Endpoints
- `/api/system-stats` - System metrics
- `/api/dashboard-stats` - Dashboard data
- Use untuk custom integrations

---

## 📞 Support

### Resources
- `README.md` - Installation guide
- `FEATURES.md` - Complete feature list
- `TELEGRAM_SETUP.md` - Telegram guide
- `DEPLOYMENT.md` - VPS deployment

### Logs
- Check console output
- Python traceback untuk errors
- FFmpeg logs untuk streams

---

**Happy Streaming! 🎬**
