#!/usr/bin/env python3
"""
Comprehensive Analysis: All Pages vs Database
Checks which fields are in forms but not saved to database
"""
import sqlite3
import re

DB_FILE = 'jadwalstream.db'

def get_table_columns(table_name):
    """Get all columns for a table"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()
    return columns

def analyze_template(template_file):
    """Extract form fields from template"""
    try:
        with open(f'templates/{template_file}', 'r') as f:
            content = f.read()
        
        # Find input fields
        inputs = re.findall(r'name=["\']([^"\']+)["\']', content)
        return list(set(inputs))  # Remove duplicates
    except:
        return []

print("="*80)
print("COMPREHENSIVE PAGE ANALYSIS")
print("="*80)

# Define pages to check
pages = {
    'live_streams.html': {
        'table': 'live_streams',
        'description': 'Live Stream Management'
    },
    'videos.html': {
        'table': 'videos',
        'description': 'Video Gallery'
    },
    'thumbnails.html': {
        'table': 'thumbnails',
        'description': 'Thumbnail Gallery'
    },
    'video_looping.html': {
        'table': 'looped_videos',
        'description': 'Bulk Loop Videos'
    },
    'bulk_upload_queue.html': {
        'table': 'bulk_upload_queue',
        'description': 'Upload Queue'
    },
    'bulk_scheduling.html': {
        'table': 'bulk_upload_queue',  # Uses same table
        'description': 'AI Bulk Schedule'
    }
}

all_issues = []

for template, info in pages.items():
    print(f"\n{'='*80}")
    print(f"📄 {info['description']}")
    print(f"   Template: {template}")
    print(f"   Table: {info['table']}")
    print("="*80)
    
    # Get template fields
    form_fields = analyze_template(template)
    
    # Get database columns
    try:
        db_columns = get_table_columns(info['table'])
    except:
        print(f"   ⚠️  Table '{info['table']}' not found in database")
        continue
    
    print(f"\n📝 Form Fields ({len(form_fields)}):")
    for field in sorted(form_fields)[:15]:  # Show first 15
        print(f"   - {field}")
    if len(form_fields) > 15:
        print(f"   ... and {len(form_fields) - 15} more")
    
    print(f"\n💾 Database Columns ({len(db_columns)}):")
    for col in db_columns:
        print(f"   - {col}")
    
    # Find mismatches
    print(f"\n🔍 Analysis:")
    
    # Convert field names (camelCase to snake_case for comparison)
    def to_snake(name):
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    
    form_snake = {to_snake(f): f for f in form_fields}
    
    missing_in_db = []
    for field in form_fields:
        snake = to_snake(field)
        # Check if field or its snake_case version exists in DB
        if field not in db_columns and snake not in db_columns:
            # Skip common non-data fields
            if field not in ['csrf_token', 'submit', 'action']:
                missing_in_db.append(field)
    
    if missing_in_db:
        print(f"   ❌ Fields in form but NOT in database ({len(missing_in_db)}):")
        for field in missing_in_db:
            print(f"      - {field}")
            all_issues.append({
                'page': info['description'],
                'table': info['table'],
                'field': field
            })
    else:
        print(f"   ✅ All form fields have corresponding database columns")

print("\n")
print("="*80)
print("SUMMARY")
print("="*80)

if all_issues:
    print(f"\n⚠️  Found {len(all_issues)} potential issues:")
    
    # Group by table
    by_table = {}
    for issue in all_issues:
        table = issue['table']
        if table not in by_table:
            by_table[table] = []
        by_table[table].append(issue)
    
    for table, issues in by_table.items():
        print(f"\n📊 Table: {table}")
        for issue in issues:
            print(f"   ❌ {issue['page']}: {issue['field']}")
else:
    print("\n✅ No issues found! All forms match database structure.")

print("\n" + "="*80)
