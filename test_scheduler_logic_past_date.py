#!/usr/bin/env python3
"""Test scheduler logic with past scheduled date"""
import sys
sys.path.insert(0, '/root/baru/jadwalstream')

from datetime import datetime, timedelta
import pytz

TIMEZONE = 'Asia/Jakarta'

print("=== Testing Auto Upload Scheduler Logic with Past Date ===\n")

# Current time
now = datetime.now(pytz.timezone(TIMEZONE))
print(f"Current time (Jakarta): {now.strftime('%Y-%m-%d %H:%M:%S')}")

# Scheduled time in the past
scheduled_time_str = '2025-11-13 07:05:00'
scheduled_time = datetime.strptime(scheduled_time_str, '%Y-%m-%d %H:%M:%S')
scheduled_time = pytz.timezone(TIMEZONE).localize(scheduled_time)

print(f"Scheduled publish time: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}")

# Upload offset (2 hours before publish)
upload_offset = timedelta(hours=2)
upload_time = scheduled_time - upload_offset

print(f"Upload time: {upload_time.strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Check condition
print("=== Scheduler Logic Check ===")
print(f"Condition: now >= upload_time")
print(f"           {now.strftime('%H:%M:%S')} >= {upload_time.strftime('%H:%M:%S')}")

if now >= upload_time:
    print("✅ RESULT: WILL UPLOAD")
    print("   Scheduler akan upload video ini pada check berikutnya!")
    
    # Time difference
    time_diff = now - upload_time
    hours_passed = time_diff.total_seconds() / 3600
    print(f"   Upload time sudah lewat {hours_passed:.2f} jam yang lalu")
else:
    print("❌ RESULT: WILL NOT UPLOAD YET")
    time_until = upload_time - now
    hours_until = time_until.total_seconds() / 3600
    print(f"   Akan upload dalam {hours_until:.2f} jam")

print()
print("=== YouTube API Handling ===")

# Convert to UTC for YouTube API
utc_tz = pytz.UTC
scheduled_time_utc = scheduled_time.astimezone(utc_tz)
now_utc = datetime.now(utc_tz)

print(f"Scheduled time (UTC): {scheduled_time_utc.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Current time (UTC):   {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")

# YouTube requires publishAt to be at least 1 hour in future
min_publish_time = now_utc + timedelta(hours=1)

print(f"\nYouTube minimum time: {min_publish_time.strftime('%Y-%m-%d %H:%M:%S')} (now + 1 hour)")

if scheduled_time_utc <= min_publish_time:
    print("⚠️  ADJUSTMENT NEEDED!")
    print("   Scheduled time di masa lalu atau terlalu dekat")
    
    # Auto-adjust (current logic in code)
    adjusted_time = now_utc + timedelta(hours=2)
    print(f"   Will be adjusted to: {adjusted_time.strftime('%Y-%m-%d %H:%M:%S')} (now + 2 hours)")
    print(f"   Jakarta time: {adjusted_time.astimezone(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d %H:%M:%S')}")
else:
    print("✅ Scheduled time valid for YouTube API")

print()
print("=== Summary ===")
print("1. ✅ Auto Upload Scheduler AKAN JALAN")
print("2. ⚠️  Video akan diupload pada check berikutnya (max 30 menit)")
print("3. ⚠️  Scheduled publish time akan AUTO-ADJUST ke 2 jam dari sekarang")
print("4. 💡 Video akan di-upload dengan status 'private' dan scheduled publish")

print("\n=== Done ===")
