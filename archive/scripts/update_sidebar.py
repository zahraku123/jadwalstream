#!/usr/bin/env python3
"""
Update Sidebar - Add User Limits Menu
"""

def update_base_html():
    """Update base.html sidebar"""
    
    with open('templates/base.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Update admin check to use is_admin from database
    old_check = "{% if current_user.is_authenticated and (current_user.role|lower == 'admin') %}"
    new_check = "{% if current_user.is_authenticated and current_user.username == 'admin' %}"
    
    if old_check in content:
        content = content.replace(old_check, new_check)
        print("✅ Updated admin check")
    
    # 2. Add User Limits menu after Manajemen User
    menu_insert = '''                            <a href="{{ url_for('admin_users') }}" class="group flex items-center px-3 py-2.5 text-sm font-medium rounded-lg text-slate-300 hover:text-white hover:bg-slate-700/50 transition-all duration-200">
                                <i class="fas fa-users-cog mr-3 text-accent-green group-hover:text-green-400"></i>
                                Manajemen User
                            </a>'''
    
    new_menu = '''                            <a href="{{ url_for('admin_users') }}" class="group flex items-center px-3 py-2.5 text-sm font-medium rounded-lg text-slate-300 hover:text-white hover:bg-slate-700/50 transition-all duration-200">
                                <i class="fas fa-users-cog mr-3 text-accent-green group-hover:text-green-400"></i>
                                Manajemen User
                            </a>
                            
                            <a href="{{ url_for('admin_user_limits') }}" class="group flex items-center px-3 py-2.5 text-sm font-medium rounded-lg text-slate-300 hover:text-white hover:bg-slate-700/50 transition-all duration-200">
                                <i class="fas fa-sliders-h mr-3 text-purple-400 group-hover:text-purple-300"></i>
                                User Limits
                            </a>'''
    
    if menu_insert in content and "admin_user_limits" not in content:
        content = content.replace(menu_insert, new_menu)
        print("✅ Added User Limits menu")
    elif "admin_user_limits" in content:
        print("⚠️  User Limits menu already exists")
    else:
        print("⚠️  Could not find menu insertion point")
    
    # Write back
    with open('templates/base.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def main():
    print("=" * 60)
    print("  Updating Sidebar - Add User Limits")
    print("=" * 60)
    
    update_base_html()
    
    print("\n" + "=" * 60)
    print("  ✅ Sidebar Updated!")
    print("=" * 60)
    print("\n📝 Changes:")
    print("   ✅ Updated admin check")
    print("   ✅ Added User Limits menu item")
    print("\n🔄 Restart app to see changes")

if __name__ == '__main__':
    main()
