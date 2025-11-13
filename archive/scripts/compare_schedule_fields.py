#!/usr/bin/env python3
"""Compare schedule fields between template, route, and database"""

print("="*70)
print("SCHEDULE FIELDS COMPARISON")
print("="*70)

# Template form fields
template_fields = {
    'title': '✅ Required text input',
    'description': '✅ Textarea',
    'scheduledStartTime': '✅ Required datetime-local',
    'tokenFile': '✅ Required select',
    'privacyStatus': '❌ Select (unlisted/private/public) - NOT SAVED',
    'useExistingStream': '❌ Checkbox - NOT SAVED',
    'streamNameExisting': '✅ Select (conditional)',
    'autoStart': '❌ Checkbox - NOT SAVED',
    'autoStop': '❌ Checkbox - NOT SAVED',
    'madeForKids': '❌ Checkbox - NOT SAVED',
    'thumbnailFile': '✅ Select (optional)',
    'repeat_daily': '❌ NOT IN FORM but saved to database!',
}

print("\n📝 TEMPLATE FORM FIELDS:")
print("-" * 70)
for field, status in template_fields.items():
    print(f"  {field:25} {status}")

# Route saves these to database
route_saves = {
    'title': '✅ Saved',
    'description': '✅ Saved',
    'scheduled_start_time': '✅ Saved (from scheduledStartTime)',
    'video_file': '✅ Saved (from videoFile)',
    'thumbnail': '✅ Saved (from thumbnailFile)',
    'stream_name': '✅ Saved (from streamNameExisting)',
    'stream_id': '✅ Saved (from streamIdExisting)',
    'token_file': '✅ Saved (from tokenFile)',
    'repeat_daily': '✅ Saved (but NO input in form!)',
    'success': '✅ Saved (default 0)',
}

print("\n💾 ROUTE SAVES TO DATABASE:")
print("-" * 70)
for field, status in route_saves.items():
    print(f"  {field:25} {status}")

# Database schema
db_schema = {
    'id': 'INTEGER PRIMARY KEY',
    'user_id': 'INTEGER NOT NULL',
    'title': 'TEXT NOT NULL',
    'description': 'TEXT',
    'scheduled_start_time': 'TIMESTAMP NOT NULL',
    'video_file': 'TEXT NOT NULL',
    'thumbnail': 'TEXT',
    'stream_name': 'TEXT',
    'stream_id': 'TEXT',
    'token_file': 'TEXT',
    'repeat_daily': 'INTEGER DEFAULT 0',
    'success': 'INTEGER DEFAULT 0',
    'broadcast_link': 'TEXT',
}

print("\n🗄️  DATABASE SCHEMA:")
print("-" * 70)
for field, type_info in db_schema.items():
    print(f"  {field:25} {type_info}")

print("\n")
print("="*70)
print("ISSUES IDENTIFIED:")
print("="*70)

issues = [
    "❌ 1. privacyStatus - Form has it, but NOT saved to database",
    "❌ 2. useExistingStream - Form has checkbox, but NOT saved",
    "❌ 3. autoStart - Form has checkbox, but NOT saved",
    "❌ 4. autoStop - Form has checkbox, but NOT saved",
    "❌ 5. madeForKids - Form has checkbox, but NOT saved",
    "❌ 6. repeat_daily - Saved to database, but NO input in form!",
    "❌ 7. videoFile - Form doesn't have this field (needed?)",
]

for issue in issues:
    print(f"  {issue}")

print("\n")
print("="*70)
print("RECOMMENDATIONS:")
print("="*70)

recommendations = [
    "1. Add 'repeat_daily' checkbox to the form",
    "2. Add columns to database for: privacyStatus, autoStart, autoStop, madeForKids",
    "3. Update add_schedule route to save all form fields",
    "4. Consider if 'useExistingStream' needs to be saved (probably not)",
    "5. Clarify if 'videoFile' is needed or can be removed",
]

for rec in recommendations:
    print(f"  {rec}")

print("\n")
