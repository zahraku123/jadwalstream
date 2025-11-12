#!/bin/bash

echo "Testing upload endpoint..."
echo ""

# Create a small test video (1 second black video)
echo "Creating test video..."
ffmpeg -f lavfi -i color=black:s=320x240:d=1 -f lavfi -i anullsrc -c:v libx264 -t 1 -pix_fmt yuv420p /tmp/test_upload.mp4 -y >/dev/null 2>&1

if [ ! -f /tmp/test_upload.mp4 ]; then
    echo "Failed to create test video"
    exit 1
fi

echo "Test video created: /tmp/test_upload.mp4"
echo ""

# Test upload (without auth, will fail but we can see response format)
echo "Testing upload response format..."
curl -X POST http://localhost:5001/upload-video \
  -F "video_files=@/tmp/test_upload.mp4" \
  -H "Accept: application/json" \
  2>/dev/null | head -20

echo ""
echo "Done!"

# Cleanup
rm -f /tmp/test_upload.mp4
