#!/usr/bin/env python3
"""Check stream mappings in database"""
import sys
sys.path.insert(0, '/root/baru/jadwalstream')

from database import get_stream_mappings, get_database_stats

# Check database stats
print("=== Database Stats ===")
stats = get_database_stats()
for table, count in stats.items():
    if table != 'db_size_mb':
        print(f"{table}: {count}")
print(f"\nDatabase size: {stats.get('db_size_mb', 0)} MB")

# Check stream mappings for each user
print("\n=== Stream Mappings ===")
from database import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT user_id FROM stream_mappings')
    users = [row['user_id'] for row in cursor.fetchall()]
    
    if not users:
        print("No stream mappings found in database")
    else:
        for user_id in users:
            print(f"\nUser ID: {user_id}")
            mappings = get_stream_mappings(user_id)
            for token_file, streams in mappings.items():
                print(f"  Token: {token_file}")
                for stream_id, meta in streams.items():
                    stream_name = meta.get('stream_name', 'Unknown')
                    stream_key = meta.get('stream_key', 'N/A')
                    print(f"    - {stream_name} (ID: {stream_id})")
                    print(f"      Key: {stream_key[:20]}..." if len(stream_key) > 20 else f"      Key: {stream_key}")

print("\n=== Done ===")
