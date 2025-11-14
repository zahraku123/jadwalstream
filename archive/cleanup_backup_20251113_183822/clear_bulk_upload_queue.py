#!/usr/bin/env python3
"""Clear all bulk upload queue items"""
import sys
sys.path.insert(0, '/root/baru/jadwalstream')

from database import get_db_connection, get_bulk_upload_queue

def clear_queue(user_id=None):
    """Clear bulk upload queue for a specific user or all users"""
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if user_id:
            # Get queue items for specific user
            cursor.execute('SELECT id, title FROM bulk_upload_queue WHERE user_id = ?', (user_id,))
            items = cursor.fetchall()
            
            if not items:
                print(f"No queue items found for user_id={user_id}")
                return 0
            
            print(f"Found {len(items)} queue items for user_id={user_id}:")
            for item in items:
                print(f"  - {item['title']}")
            
            # Delete all items for this user
            cursor.execute('DELETE FROM bulk_upload_queue WHERE user_id = ?', (user_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            
            print(f"\n✓ Deleted {deleted_count} queue items for user_id={user_id}")
            return deleted_count
        else:
            # Get all queue items
            cursor.execute('SELECT user_id, COUNT(*) as count FROM bulk_upload_queue GROUP BY user_id')
            users = cursor.fetchall()
            
            if not users:
                print("No queue items found")
                return 0
            
            print("Queue items by user:")
            for user in users:
                print(f"  User ID {user['user_id']}: {user['count']} items")
            
            # Delete all items
            cursor.execute('DELETE FROM bulk_upload_queue')
            deleted_count = cursor.rowcount
            conn.commit()
            
            print(f"\n✓ Deleted {deleted_count} total queue items")
            return deleted_count

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Clear bulk upload queue')
    parser.add_argument('--user-id', type=int, help='User ID to clear queue for (default: all users)')
    parser.add_argument('--all', action='store_true', help='Clear all users queue')
    
    args = parser.parse_args()
    
    print("=== Clear Bulk Upload Queue ===\n")
    
    if args.all:
        confirm = input("Are you sure you want to delete ALL queue items for ALL users? (yes/no): ")
        if confirm.lower() == 'yes':
            clear_queue()
        else:
            print("Cancelled")
    elif args.user_id:
        confirm = input(f"Are you sure you want to delete all queue items for user_id={args.user_id}? (yes/no): ")
        if confirm.lower() == 'yes':
            clear_queue(args.user_id)
        else:
            print("Cancelled")
    else:
        # Default: clear for user_id=1 (admin)
        print("No user specified, clearing queue for user_id=1 (admin)")
        confirm = input("Continue? (yes/no): ")
        if confirm.lower() == 'yes':
            clear_queue(user_id=1)
        else:
            print("Cancelled")
    
    print("\n=== Done ===")
