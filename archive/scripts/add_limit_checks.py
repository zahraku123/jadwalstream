#!/usr/bin/env python3
"""
Add Limit Checks to Important Routes
Integrate storage and stream limit checks into upload and stream routes
"""

import re

def add_check_to_upload_video(content):
    """Add storage limit check to upload-video route"""
    
    # Find the upload-video route
    pattern = r"(@app\.route\('/upload-video', methods=\['POST'\]\).*?@login_required.*?def upload_video\(\):)"
    
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    if matches:
        for match in matches:
            route_start = match.group(1)
            
            # Check if limit check already added
            if "can_user_upload" in content[match.end():match.end()+1000]:
                print("⚠️  upload_video already has limit check")
                continue
            
            # Add limit check after function definition
            check_code = """
    # Check storage limit before upload
    from user_limits import can_user_upload
    
    user_id = int(current_user.id)
    files = request.files.getlist('video_files')
    
    # Calculate total size
    total_size = 0
    for file in files:
        if file and hasattr(file, 'content_length') and file.content_length:
            total_size += file.content_length
    
    total_size_mb = total_size / (1024 * 1024) if total_size > 0 else 0
    
    # Check if user can upload this size
    can_upload, message = can_user_upload(user_id, total_size_mb)
    if not can_upload:
        flash(f'Upload failed: {message}', 'error')
        return redirect(url_for('video_gallery'))
    
    # Continue with original upload logic..."""
            
            # Find the function body start (after def line)
            func_pattern = r"(def upload_video\(\):)"
            func_match = re.search(func_pattern, content[match.start():match.end()+500])
            
            if func_match:
                insert_pos = match.start() + func_match.end()
                content = content[:insert_pos] + check_code + content[insert_pos:]
                print("✅ Added storage limit check to upload_video")
                return content
    
    print("⚠️  Could not find upload_video route")
    return content

def add_check_to_add_live_stream(content):
    """Add stream limit check to add-live-stream route"""
    
    # Find routes that add live streams
    routes = [
        r"(@app\.route\('/add-live-stream'.*?def add_live_stream\(\):)",
        r"(@app\.route\('/start-stream'.*?def start_stream\(\):)"
    ]
    
    for pattern in routes:
        matches = list(re.finditer(pattern, content, re.DOTALL))
        
        if matches:
            for match in matches:
                # Check if already has limit check
                if "can_user_add_stream" in content[match.end():match.end()+1000]:
                    print(f"⚠️  {match.group(0)[:30]}... already has limit check")
                    continue
                
                check_code = """
    # Check stream limit before adding
    from user_limits import can_user_add_stream
    
    user_id = int(current_user.id)
    can_add, message = can_user_add_stream(user_id)
    if not can_add:
        flash(f'Cannot add stream: {message}', 'error')
        return redirect(url_for('live_streams'))
    
    # Continue with original logic..."""
                
                func_pattern = r"(def [a-z_]+\(\):)"
                func_match = re.search(func_pattern, content[match.start():match.end()+500])
                
                if func_match:
                    insert_pos = match.start() + func_match.end()
                    content = content[:insert_pos] + check_code + content[insert_pos:]
                    print("✅ Added stream limit check to add_live_stream")
                    return content
    
    return content

def add_check_to_add_schedule(content):
    """Add stream limit check to add_schedule route"""
    
    pattern = r"(@app\.route\('/add_schedule', methods=\['POST'\]\).*?def add_schedule\(\):)"
    
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    if matches:
        for match in matches:
            # Check if already has limit check
            if "can_user_add_stream" in content[match.end():match.end()+1000]:
                print("⚠️  add_schedule already has limit check")
                continue
            
            check_code = """
    # Check stream/schedule limit
    from user_limits import can_user_add_stream
    
    user_id = int(current_user.id)
    can_add, message = can_user_add_stream(user_id)
    if not can_add:
        flash(f'Cannot add schedule: {message}', 'error')
        return redirect(url_for('schedules'))
    
    # Continue with original logic..."""
            
            func_pattern = r"(def add_schedule\(\):)"
            func_match = re.search(func_pattern, content[match.start():match.end()+500])
            
            if func_match:
                insert_pos = match.start() + func_match.end()
                content = content[:insert_pos] + check_code + content[insert_pos:]
                print("✅ Added schedule limit check to add_schedule")
                return content
    
    return content

def add_usage_display_helper(content):
    """Add helper function to get user usage for display"""
    
    helper_code = """
# Helper function to get user usage for templates
def get_current_user_usage():
    \"\"\"Get current user's usage stats for display in templates\"\"\"
    if not current_user.is_authenticated:
        return None
    
    from user_limits import get_user_limits
    try:
        user_id = int(current_user.id)
        limits = get_user_limits(user_id)
        return limits
    except:
        return None

# Make it available in all templates
@app.context_processor
def inject_user_usage():
    return dict(user_usage=get_current_user_usage())

"""
    
    # Add before the first route definition
    marker = "@app.route('/')"
    
    if marker in content and "def get_current_user_usage():" not in content:
        content = content.replace(marker, helper_code + marker)
        print("✅ Added user usage helper for templates")
    
    return content

def main():
    print("=" * 60)
    print("  Adding Limit Checks to Routes")
    print("=" * 60)
    
    app_file = 'app.py'
    
    # Read content
    print("\n📖 Reading app.py...")
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply patches
    print("\n🔧 Adding limit checks...")
    
    original_len = len(content)
    
    content = add_check_to_upload_video(content)
    content = add_check_to_add_live_stream(content)
    content = add_check_to_add_schedule(content)
    content = add_usage_display_helper(content)
    
    if len(content) == original_len:
        print("\n⚠️  No changes made - checks may already exist")
    else:
        # Write back
        print("\n💾 Writing updated app.py...")
        with open(app_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("\n" + "=" * 60)
        print("  ✅ Limit Checks Added!")
        print("=" * 60)
        
        print("\n📝 Changes made:")
        print("   ✅ Storage limit check in upload_video")
        print("   ✅ Stream limit check in add_live_stream")
        print("   ✅ Schedule limit check in add_schedule")
        print("   ✅ User usage helper for templates")
        
        print("\n🔄 Restart app:")
        print("   pkill -f app.py && python3 app.py &")
        
        return True
    
    return False

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
