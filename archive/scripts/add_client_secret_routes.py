#!/usr/bin/env python3
"""
Add Client Secret Routes to app.py
"""

def add_routes():
    """Add client secret routes to app.py"""
    
    routes_code = '''
# ===== CLIENT SECRET MANAGEMENT (PER-USER) =====

@app.route('/settings/youtube-api')
@login_required
def client_secret_settings():
    """YouTube API settings page"""
    from client_secret_manager import get_client_secret_info, list_user_tokens
    
    user_id = int(current_user.id)
    client_info = get_client_secret_info(user_id)
    tokens = list_user_tokens(user_id)
    
    return render_template('client_secret_settings.html', 
                         client_info=client_info,
                         tokens=tokens)

@app.route('/settings/youtube-api/upload', methods=['POST'])
@login_required
def upload_client_secret():
    """Upload client_secret.json for current user"""
    from client_secret_manager import set_user_client_secret
    
    if 'client_secret' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('client_secret_settings'))
    
    file = request.files['client_secret']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('client_secret_settings'))
    
    if not file.filename.endswith('.json'):
        flash('File must be a JSON file', 'error')
        return redirect(url_for('client_secret_settings'))
    
    user_id = int(current_user.id)
    success, message, filepath = set_user_client_secret(user_id, file.read(), file.filename)
    
    flash(message, 'success' if success else 'error')
    return redirect(url_for('client_secret_settings'))

@app.route('/settings/youtube-api/delete', methods=['POST'])
@login_required
def delete_client_secret():
    """Delete client_secret for current user"""
    from client_secret_manager import delete_user_client_secret
    
    user_id = int(current_user.id)
    success, message = delete_user_client_secret(user_id)
    
    return jsonify({'success': success, 'message': message})

'''
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if routes already exist
    if '@app.route(\'/settings/youtube-api\')' in content:
        print("⚠️  Client secret routes already exist")
        return False
    
    # Add before "if __name__ == '__main__':"
    marker = "if __name__ == '__main__':"
    
    if marker in content:
        content = content.replace(marker, routes_code + "\n" + marker)
        
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Added client secret routes")
        return True
    else:
        print("❌ Could not find insertion point")
        return False

def main():
    print("=" * 60)
    print("  Adding Client Secret Routes")
    print("=" * 60)
    
    success = add_routes()
    
    if success:
        print("\n" + "=" * 60)
        print("  ✅ Routes Added!")
        print("=" * 60)
        print("\n📝 New routes:")
        print("   /settings/youtube-api - Settings page")
        print("   /settings/youtube-api/upload - Upload endpoint")
        print("   /settings/youtube-api/delete - Delete endpoint")
        print("\n🔄 Restart app to use new routes")
    
    return success

if __name__ == '__main__':
    import sys
    sys.exit(0 if main() else 1)
