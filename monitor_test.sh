#!/bin/bash

echo "=================================="
echo "MONITORING TEST A & B"
echo "=================================="
echo ""
echo "Current Time: $(TZ='Asia/Jakarta' date '+%Y-%m-%d %H:%M:%S')"
echo ""

echo "--- Auto Scheduler Status ---"
cat auto_upload_config.json 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "Config not found"
echo ""

echo "--- Upload Queue Status ---"
queue_count=$(cat bulk_upload_queue.json 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data))" 2>/dev/null || echo "0")
echo "Total items in queue: $queue_count"

if [ "$queue_count" -gt 0 ]; then
    echo ""
    echo "Queue items:"
    cat bulk_upload_queue.json 2>/dev/null | python3 -m json.tool 2>/dev/null | grep -E "title|status|scheduled_publish_time" | head -20
fi

echo ""
echo "--- Recent Logs (last 20 lines) ---"
pm2 logs baru --lines 20 --nostream 2>&1 | grep -E "AUTO-UPLOAD|Uploading|YouTube|error" | tail -20

echo ""
echo "=================================="
echo "To monitor in real-time:"
echo "  pm2 logs baru --lines 100 | grep -i upload"
echo "=================================="
