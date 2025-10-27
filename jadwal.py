import schedule
import time
import subprocess
import logging
from datetime import datetime
import pytz
import os

# ================= CONFIG =================
YOUTUBE_SCRIPT = "live.py"  # skrip utama scheduler
# Jam eksekusi sesuai waktu Jakarta (3x sehari)
SCHEDULE_TIMES = ["00:23", "00:37", "00:39"]
TIMEZONE = "Asia/Jakarta"
# =========================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

jakarta_tz = pytz.timezone(TIMEZONE)

def run_scheduler():
    now_jakarta = datetime.now(jakarta_tz)
    logging.info(f"🔴 Running YouTube Scheduler bro... Waktu Jakarta: {now_jakarta.strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        subprocess.call(["python", YOUTUBE_SCRIPT])
        logging.info("✅ Scheduler selesai bro")
    except Exception as e:
        logging.error(f"Error menjalankan scheduler bro: {e}")

def schedule_jobs():
    for t in SCHEDULE_TIMES:
        schedule.every().day.at(t).do(run_scheduler)
        logging.info(f"⏰ Scheduler terpasang tiap hari jam {t} WIB")

def main():
    logging.info("✅ Auto-scheduler Jakarta aktif bro. Tunggu prosesnya...")
    schedule_jobs()
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()
