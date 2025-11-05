#!/bin/bash
# Backup and upload to Google Drive script

echo "=============================================="
echo "  JadwalStream Backup & Upload to GDrive"
echo "=============================================="
echo ""

# Check if gdrive_token.json exists
if [ ! -f "/root/jadwalstream/gdrive_token.json" ]; then
    echo "⚠️  Google Drive not authenticated yet"
    echo ""
    echo "Please run authentication first:"
    echo "  cd /root/jadwalstream"
    echo "  python3 auth_gdrive.py"
    echo ""
    exit 1
fi

# Create backup directory if not exists
mkdir -p /root/backupjadwalstream

# Create backup
echo "Creating backup..."
BACKUP_FILE="/root/backupjadwalstream/jadwalstream_backup_$(date +%Y%m%d_%H%M%S).tar.gz"

cd /root
tar --exclude='jadwalstream/node_modules' \
    --exclude='jadwalstream/__pycache__' \
    --exclude='jadwalstream/.git' \
    --exclude='jadwalstream/venv' \
    --exclude='jadwalstream/ffmpeg_logs' \
    --exclude='jadwalstream/backup' \
    -czf "$BACKUP_FILE" jadwalstream

if [ $? -eq 0 ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✓ Backup created: $BACKUP_FILE"
    echo "  Size: $SIZE"
    echo ""
else
    echo "✗ Failed to create backup"
    exit 1
fi

# Upload to Google Drive
echo "Uploading to Google Drive..."
cd /root/jadwalstream
python3 upload_to_gdrive.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=============================================="
    echo "  ✓ Backup completed successfully!"
    echo "=============================================="
else
    echo ""
    echo "=============================================="
    echo "  ✗ Upload failed"
    echo "=============================================="
    exit 1
fi
