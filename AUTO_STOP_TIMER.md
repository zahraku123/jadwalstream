# Auto-Stop Timer Feature

## Overview
Fitur auto-stop timer memastikan bahwa live stream akan otomatis berhenti sesuai dengan durasi yang telah ditentukan, bahkan ketika stream dimulai secara manual di waktu yang berbeda dari jadwal aslinya.

## Fitur Utama

### 1. Update Waktu Start Otomatis
Ketika Anda klik **"Start Live Manual"**, sistem akan:
- Mengupdate `start_date` di jadwal menjadi waktu actual saat tombol diklik
- Menyimpan `actual_start_time` untuk tracking
- Menghitung waktu stop berdasarkan: `actual_start_time + duration`

**Contoh:**
- Jadwal tersimpan: 5 Nov 2025, 13:10
- Klik start manual: 4 Nov 2025, 16:22
- Sistem update start_date ke: 4 Nov 2025, 16:22
- Durasi: 240 menit
- Auto-stop dijadwalkan: 4 Nov 2025, 20:22

### 2. Timer Auto-Stop dengan Threading
- Menggunakan `threading.Timer` (background thread Python)
- Timer berjalan di dalam aplikasi Flask
- Otomatis menghentikan FFmpeg process sesuai durasi
- Timer disimpan di memory (`active_timers` dict) dan persistent storage (`stream_timers.json`)

### 3. Cancel Timer Otomatis
Ketika stream dihentikan manual sebelum waktunya:
- Fungsi `stop_ffmpeg_stream()` otomatis memanggil `cancel_stream_timer()`
- Timer yang aktif di-cancel untuk menghindari double-stop
- Entry timer dihapus dari `stream_timers.json`

### 4. Tracking Timer Persistent
File `stream_timers.json` menyimpan informasi:
```json
[
  {
    "stream_id": "115b89e9-6382-4eda-aa5e-6fd807bd3b9d",
    "stream_title": "Live Labubu1",
    "pid": 174225,
    "start_time": "2025-11-04T16:22:28+07:00",
    "stop_time": "2025-11-04T20:22:28+07:00",
    "duration_minutes": 240,
    "created_at": "2025-11-04T16:22:28+07:00"
  }
]
```

## API Endpoints

### GET /api/active-timers
Mendapatkan daftar timer yang sedang aktif dengan informasi:
- Stream ID dan Title
- PID FFmpeg
- Waktu start dan stop
- Sisa waktu (seconds dan formatted)

**Response Example:**
```json
[
  {
    "stream_id": "115b89e9-6382-4eda-aa5e-6fd807bd3b9d",
    "stream_title": "Live Labubu1",
    "pid": 174225,
    "start_time": "2025-11-04T16:22:28+07:00",
    "stop_time": "2025-11-04T20:22:28+07:00",
    "duration_minutes": 240,
    "time_remaining_seconds": 7200,
    "time_remaining_formatted": "120m 0s"
  }
]
```

## Flow Diagram

### Manual Start with Auto-Stop
```
User clicks "Start Live Manual"
    ↓
System updates start_date to current time
    ↓
FFmpeg process starts (PID saved)
    ↓
Calculate stop_time = start_time + duration
    ↓
Create threading.Timer(duration_seconds, auto_stop_callback)
    ↓
Save timer info to stream_timers.json
    ↓
Timer counts down...
    ↓
When time expires → auto_stop_callback()
    ↓
Stop FFmpeg process (terminate/kill)
    ↓
Update stream status to "completed"
    ↓
Remove timer from active_timers & stream_timers.json
```

### Manual Stop Before Timer Expires
```
User clicks "Stop Live"
    ↓
cancel_stream_timer(stream_id) called
    ↓
Timer.cancel() called (prevents auto-stop)
    ↓
Remove from active_timers dict
    ↓
Remove from stream_timers.json
    ↓
Stop FFmpeg process
    ↓
Update stream status
```

## Files Modified
- `app.py`: 
  - Added `STREAM_TIMERS_FILE` constant
  - Added `active_timers` dict
  - Added functions: `get_stream_timers()`, `save_stream_timers()`, `cancel_stream_timer()`
  - Modified `start_ffmpeg_stream()`: Update start_date, create persistent timer
  - Modified `stop_ffmpeg_stream()`: Cancel timer before stopping
  - Added API endpoint: `/api/active-timers`

## Files Created
- `stream_timers.json`: Persistent storage for active timers
- `stream_timers.json.example`: Example/template file
- `AUTO_STOP_TIMER.md`: This documentation

## Testing
1. **Start stream manual dengan durasi**:
   ```
   - Set durasi: 240 menit
   - Klik "Start Live Manual"
   - Check log: Harus ada "[AUTO-STOP] ✓ Scheduled..."
   - Check stream_timers.json: Harus ada entry baru
   ```

2. **Verify timer berjalan**:
   ```
   - Call API: GET /api/active-timers
   - Harus mengembalikan timer dengan time_remaining
   ```

3. **Stop manual sebelum timer**:
   ```
   - Klik "Stop Live"
   - Check log: Harus ada "[TIMER] Cancelled timer..."
   - Check stream_timers.json: Entry harus terhapus
   ```

4. **Wait for auto-stop**:
   ```
   - Biarkan timer sampai habis
   - Stream harus otomatis stop
   - Check log: "[AUTO-STOP] Timer triggered!"
   - Stream status updated to "completed"
   ```

## Important Notes
- Timer menggunakan background thread, akan hilang jika app.py restart
- Untuk production, pertimbangkan menggunakan `at` command atau cron untuk persistence yang lebih kuat
- `stream_timers.json` hanya untuk tracking/monitoring, tidak mempengaruhi timer yang sudah berjalan
- Timer accuracy tergantung Python threading (biasanya akurat dalam 1-2 detik)

## Troubleshooting

### Timer tidak jalan
- Check log saat start stream: Harus ada pesan "[AUTO-STOP] ✓ Scheduled..."
- Pastikan durasi tidak kosong atau 0
- Check `stream_timers.json` apakah entry dibuat

### Stream tidak stop otomatis
- Check apakah app.py masih running
- Check log FFmpeg: `/root/jadwalstream/ffmpeg_logs/<stream_id>.log`
- Verify PID masih sama dengan yang di timer

### Stream manual stop tidak mematikan FFmpeg (FIXED)
**Masalah:** Ketika klik stop manual di web, FFmpeg masih berjalan karena:
- App.py direstart setelah stream dimulai
- Dictionary `live_processes` kosong setelah restart
- Fungsi `stop_ffmpeg_stream()` tidak menemukan PID

**Solusi yang diimplementasikan:**
- Tambahkan fallback mechanism: Jika PID tidak ada di `live_processes`, ambil dari `live_streams.json`
- Gunakan `psutil` untuk verify dan kill process berdasarkan PID
- Verify bahwa PID adalah FFmpeg process sebelum kill

**Kode fix:**
```python
# Try to get PID from live_processes or from live_streams.json
if stream_id in live_processes:
    pid_to_kill = live_processes[stream_id].pid
else:
    # Fallback: Get PID from live_streams.json
    for stream in streams:
        if stream['id'] == stream_id and stream.get('process_pid'):
            pid_to_kill = stream['process_pid']
            break

# Kill process using psutil
if psutil.pid_exists(pid_to_kill):
    proc = psutil.Process(pid_to_kill)
    if 'ffmpeg' in proc.name().lower():
        proc.terminate()
        proc.wait(timeout=5)
```

### Double instance app.py
- Stop semua instance lama sebelum start yang baru
- `pkill -f "python.*app.py"`
- Lalu start ulang: `python3 app.py --no-debug`

### Manual kill FFmpeg jika masih stuck
Jika ada FFmpeg yang masih berjalan setelah stop manual:
```bash
# Cek FFmpeg yang berjalan
ps aux | grep ffmpeg | grep -v grep

# Kill berdasarkan PID
kill -9 <PID>
```
