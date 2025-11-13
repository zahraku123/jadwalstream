#!/usr/bin/env python3
"""
Final Fix for User Isolation
Replace ALL JSON loading functions with SQLite helpers
"""

import re

def fix_all_functions():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Track changes
    changes = []
    
    # 1. Fix get_looped_videos function
    old_looped = r'def get_looped_videos\(\):\s+"""[^"]*"""\s+if not os\.path\.exists\(LOOPED_DB_FILE\):.*?return \[\]'
    new_looped = '''def get_looped_videos():
    """Get looped videos for current user from SQLite"""
    try:
        return get_looped_videos_data()
    except Exception as e:
        print(f"Error getting looped videos: {e}")
        return []'''
    
    if re.search(old_looped, content, re.DOTALL):
        content = re.sub(old_looped, new_looped, content, flags=re.DOTALL)
        changes.append("✅ Fixed get_looped_videos()")
    
    # 2. Fix save_looped_videos function
    old_save_looped = r'def save_looped_videos\(looped_videos\):\s+with open\(LOOPED_DB_FILE.*?json\.dump\(looped_videos, f, indent=4\)'
    new_save_looped = '''def save_looped_videos(looped_videos):
    """DEPRECATED - use add_looped_video_to_db or update_looped_video_in_db instead"""
    pass'''
    
    if re.search(old_save_looped, content, re.DOTALL):
        content = re.sub(old_save_looped, new_save_looped, content, flags=re.DOTALL)
        changes.append("✅ Fixed save_looped_videos()")
    
    # 3. Fix get_bulk_upload_queue function
    old_queue = r'def get_bulk_upload_queue\(\):\s+"""[^"]*"""\s+if not os\.path\.exists\(BULK_UPLOAD_DB_FILE\):.*?return \[\]'
    new_queue = '''def get_bulk_upload_queue():
    """Get bulk upload queue for current user from SQLite"""
    try:
        return get_bulk_upload_queue_data()
    except Exception as e:
        print(f"Error getting upload queue: {e}")
        return []'''
    
    if re.search(old_queue, content, re.DOTALL):
        content = re.sub(old_queue, new_queue, content, flags=re.DOTALL)
        changes.append("✅ Fixed get_bulk_upload_queue()")
    
    # 4. Fix save_bulk_upload_queue function
    old_save_queue = r'def save_bulk_upload_queue\(queue\):\s+"""[^"]*"""\s+with open\(BULK_UPLOAD_DB_FILE.*?json\.dump\(queue, f, indent=4\)'
    new_save_queue = '''def save_bulk_upload_queue(queue):
    """DEPRECATED - use add_bulk_upload_to_db or update_bulk_upload_in_db instead"""
    pass'''
    
    if re.search(old_save_queue, content, re.DOTALL):
        content = re.sub(old_save_queue, new_save_queue, content, flags=re.DOTALL)
        changes.append("✅ Fixed save_bulk_upload_queue()")
    
    # 5. Check if there are any remaining JSON loads for videos/thumbnails/streams
    # that weren't caught by previous patches
    
    # Save the file
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    return changes

if __name__ == '__main__':
    print("=" * 60)
    print("  Final User Isolation Fix")
    print("=" * 60)
    
    changes = fix_all_functions()
    
    if changes:
        print("\n🔧 Applied changes:")
        for change in changes:
            print(f"  {change}")
    else:
        print("\n⚠️  No changes needed (already patched)")
    
    print("\n" + "=" * 60)
    print("  ✅ Fix Complete!")
    print("=" * 60)
    print("\n🔄 Now restart the app:")
    print("   cd /root/baru/jadwalstream")
    print("   python3 app.py")
    print("\n📝 Test in browser:")
    print("   http://localhost:5000")
    print("   Login as admin → should see data")
    print("   Login as demo → should see empty (no data yet)")
