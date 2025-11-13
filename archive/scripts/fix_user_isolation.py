#!/usr/bin/env python3
"""
Quick fix for user isolation in app.py
Replace JSON functions with SQLite wrappers
"""

import re

def fix_app_py():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix get_live_streams
    content = re.sub(
        r'def get_live_streams\(\):\s+if not os\.path\.exists\(LIVE_STREAMS_FILE\):.*?return \[\]',
        '''def get_live_streams():
    """Get live streams for current user from SQLite"""
    try:
        return get_live_streams_data()
    except Exception as e:
        print(f"Error getting live streams: {e}")
        return []''',
        content,
        flags=re.DOTALL
    )
    
    # Fix get_video_database
    content = re.sub(
        r'def get_video_database\(\):\s+if not os\.path\.exists\(VIDEO_DB_FILE\):.*?return \[\]',
        '''def get_video_database():
    """Get videos for current user from SQLite"""
    try:
        return get_video_database_sqlite()
    except Exception as e:
        print(f"Error getting videos: {e}")
        return []''',
        content,
        flags=re.DOTALL
    )
    
    # Fix get_thumbnail_database
    content = re.sub(
        r'def get_thumbnail_database\(\):\s+if not os\.path\.exists\(THUMBNAIL_DB_FILE\):.*?except:',
        '''def get_thumbnail_database():
    """Get thumbnails for current user from SQLite"""
    try:
        return get_thumbnail_database_sqlite()
    except Exception as e:
        print(f"Error getting thumbnails: {e}")
        return []
    except:''',
        content,
        flags=re.DOTALL
    )
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ User isolation fixed!")
    print("🔄 Restart app: pkill -f app.py && python3 app.py")

if __name__ == '__main__':
    fix_app_py()
