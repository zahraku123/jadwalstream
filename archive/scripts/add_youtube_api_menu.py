#!/usr/bin/env python3
"""
Add YouTube API Settings Menu to Sidebar
"""

def update_sidebar():
    """Add YouTube API menu to base.html"""
    
    with open('templates/base.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find Settings section in sidebar
    # Add after Token Channel menu
    menu_marker = '''<a href="{{ url_for('tokens') }}" class="group flex items-center px-3 py-2.5 text-sm font-medium rounded-lg text-slate-300 hover:text-white hover:bg-slate-700/50 transition-all duration-200">
                                <i class="fas fa-key mr-3 text-accent-yellow group-hover:text-yellow-400"></i>
                                Token Channel
                            </a>'''
    
    new_menu = '''<a href="{{ url_for('tokens') }}" class="group flex items-center px-3 py-2.5 text-sm font-medium rounded-lg text-slate-300 hover:text-white hover:bg-slate-700/50 transition-all duration-200">
                                <i class="fas fa-key mr-3 text-accent-yellow group-hover:text-yellow-400"></i>
                                Token Channel
                            </a>
                            
                            <a href="{{ url_for('client_secret_settings') }}" class="group flex items-center px-3 py-2.5 text-sm font-medium rounded-lg text-slate-300 hover:text-white hover:bg-slate-700/50 transition-all duration-200">
                                <i class="fab fa-youtube mr-3 text-red-400 group-hover:text-red-300"></i>
                                YouTube API
                            </a>'''
    
    if menu_marker in content and "client_secret_settings" not in content:
        content = content.replace(menu_marker, new_menu)
        
        with open('templates/base.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Added YouTube API menu to sidebar")
        return True
    elif "client_secret_settings" in content:
        print("⚠️  YouTube API menu already exists")
        return True
    else:
        print("❌ Could not find menu insertion point")
        return False

def main():
    print("=" * 60)
    print("  Adding YouTube API Menu")
    print("=" * 60)
    
    success = update_sidebar()
    
    if success:
        print("\n✅ Sidebar updated!")
        print("\n📝 New menu item:")
        print("   YouTube API (Settings → YouTube API)")
        print("   Icon: YouTube logo (red)")
        print("\n🔄 Restart app to see changes")
    
    return success

if __name__ == '__main__':
    import sys
    sys.exit(0 if main() else 1)
