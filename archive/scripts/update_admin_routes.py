#!/usr/bin/env python3
"""
Update Admin Routes to Support Integrated Users + Limits Page
"""

import re

def update_admin_users_route():
    """Update admin_users route to include limits data"""
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the admin_users route
    pattern = r"(@app\.route\('/admin/users'\).*?def admin_users\(\):.*?return render_template\('admin_users_cyber\.html', users=users\))"
    
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    if matches:
        for match in matches:
            old_route = match.group(1)
            
            # Create new route with limits data
            new_route = old_route.replace(
                "return render_template('admin_users_cyber.html', users=users)",
                """# Get user limits data
    from user_limits import get_all_users_with_limits
    user_limits = get_all_users_with_limits()
    
    return render_template('admin_users_with_limits.html', users=users, user_limits=user_limits)"""
            )
            
            content = content.replace(old_route, new_route)
            print("✅ Updated admin_users route")
            break
    else:
        print("⚠️  Could not find admin_users route")
    
    # Also update admin_users route to handle create with limits
    create_pattern = r"(if action == 'create':.*?success, message = create_user\(username, password, role\))"
    
    create_matches = list(re.finditer(create_pattern, content, re.DOTALL))
    
    if create_matches:
        for match in create_matches:
            old_create = match.group(1)
            
            new_create = old_create.replace(
                "success, message = create_user(username, password, role)",
                """# Get limits from form
                max_streams = int(request.form.get('max_streams', 3))
                max_storage_mb = int(request.form.get('max_storage_mb', 2000))
                
                success, message = create_user(username, password, 'user')
                
                # Set limits after user creation
                if success:
                    from database import get_user_by_username
                    from user_limits import update_user_limits
                    user_data = get_user_by_username(username)
                    if user_data:
                        update_user_limits(user_data['id'], max_streams, max_storage_mb)
                        message += f" (Limits: {max_streams} streams, {max_storage_mb}MB)"
                
                # Original success/message handling"""
            )
            
            content = content.replace(old_create, new_create)
            print("✅ Updated create user to include limits")
            break
    
    # Write back
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def main():
    print("=" * 60)
    print("  Updating Admin Routes")
    print("=" * 60)
    
    update_admin_users_route()
    
    print("\n" + "=" * 60)
    print("  ✅ Routes Updated!")
    print("=" * 60)
    print("\n📝 Changes:")
    print("   ✅ admin_users now includes limits data")
    print("   ✅ create_user now sets limits")
    print("   ✅ Template changed to admin_users_with_limits.html")
    
    print("\n🔄 Restart app to see changes")

if __name__ == '__main__':
    main()
