"""
Random Metadata Generator for JadwalStream using Excel Files
Generate random video metadata (title, description, tags) from Excel templates
"""
import random
import json
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

# Default metadata templates (fallback when no Excel files available)
DEFAULT_METADATA_TEMPLATES = {
    'general': {
        'titles': [
            'Amazing Content You Need to See',
            'Incredible Experience - Must Watch',
            'Entertaining Content for Everyone',
            'Amazing Moments Compilation',
            'Pure Entertainment Value',
            'Must See Content - Pure Fun',
            'Incredible Entertainment',
            'Amazing Content That Will Amaze You',
            'Pure Entertainment - Don\'t Miss Out',
            'Amazing Compilation - Entertainment Gold',
            'Incredible Content for All Ages',
            'Must Watch Entertainment',
            'Pure Fun - Amazing Content',
            'Entertainment That Will Make You Smile',
            'Amazing Content - Pure Joy'
        ],
        'descriptions': [
            'Amazing content that will entertain and amaze you! Pure entertainment value with incredible moments.',
            'Incredible entertainment content designed to bring joy and amazement to viewers of all ages.',
            'Pure entertainment featuring amazing moments, incredible content, and guaranteed fun for everyone.',
            'Must see content with amazing moments and pure entertainment value that will keep you engaged.',
            'Incredible entertainment compilation featuring the most amazing content and entertaining moments.',
            'Pure entertainment gold with amazing content that will make you smile and keep you entertained.',
            'Amazing content featuring incredible entertainment, pure fun, and unforgettable moments.',
            'Must watch entertainment with amazing content that will blow your mind and bring joy.',
            'Pure entertainment featuring incredible content, amazing moments, and pure fun for all.',
            'Incredible entertainment with amazing content that will amaze, entertain, and delight viewers.',
            'Amazing content compilation with pure entertainment value and incredible moments.',
            'Must see entertainment featuring amazing content, pure fun, and incredible experiences.',
            'Pure entertainment featuring amazing content with incredible moments and pure joy.',
            'Amazing entertainment content that will make you laugh, smile, and have pure fun.',
            'Incredible content with amazing entertainment, pure fun, and unforgettable experiences.'
        ],
        'tags': [
            'amazing content, entertainment, fun, incredible, must see, pure entertainment, amazing moments, entertainment gold, pure fun, incredible content, entertainment value, amazing compilation, entertainment for all, must watch, pure joy'
        ]
    }
}

def get_available_metadata_files():
    """Get list of available metadata Excel files"""
    try:
        # Import from main app
        import sys
        import os
        
        # Add project root to path if not already there
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        project_root = os.path.dirname(current_dir)  # Go up one more level to get project root
        
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from app import get_available_metadata_files as app_get_files
        return app_get_files()
    except Exception as e:
        print(f"Error getting metadata files: {e}")
        return []

def get_metadata_from_excel_file(excel_filename):
    """Get metadata from specific Excel file"""
    try:
        import sys
        import os
        
        # Add project root to path if not already there
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        project_root = os.path.dirname(current_dir)  # Go up one more level to get project root
        
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from app import get_metadata_from_excel as app_get_metadata
        return app_get_metadata(excel_filename)
    except Exception as e:
        print(f"Error getting metadata from Excel: {e}")
        return []

def get_random_metadata(excel_filename=None, count=1):
    """Get random metadata from Excel file or templates"""
    try:
        # Try to get from Excel file first
        if excel_filename:
            metadata_list = get_metadata_from_excel_file(excel_filename)
            if metadata_list:
                if count <= len(metadata_list):
                    return random.sample(metadata_list, count)
                else:
                    return random.choices(metadata_list, k=count)
        
        # Fall back to default templates
        return generate_random_metadata('general', count)
    except Exception as e:
        print(f"Error generating random metadata: {e}")
        return generate_random_metadata('general', count)

def generate_random_metadata(category: str = 'general', count: int = 1) -> List[Dict]:
    """Generate random metadata for a given category (fallback method)"""
    import random
    
    # If category doesn't exist, use general templates
    if category not in DEFAULT_METADATA_TEMPLATES:
        category = 'general'
        
    templates = DEFAULT_METADATA_TEMPLATES[category]
    
    # Generate random combinations
    metadata_list = []
    titles = templates['titles']
    descriptions = templates['descriptions']
    tags = templates['tags']
    
    for i in range(count):
        # Get random title and description
        title = random.choice(titles)
        description = random.choice(descriptions)
        tag_list = tags[0].split(', ')  # Convert comma-separated string to list
        
        # Create unique variations by adding numbers or random words
        title_variations = [
            title,
            f"{title} - Part {i+1}",
            f"{title} (2024)",
            f"Amazing {title.lower()}",
            f"Best {title.lower()}",
            f"{title} - Extended Version"
        ]
        
        metadata_list.append({
            'title': random.choice(title_variations),
            'description': description,
            'tags': random.sample(tag_list, random.randint(3, 6))  # Random 3-6 tags
        })
    
    return metadata_list

def get_categories() -> List[str]:
    """Get all available categories"""
    # For now, return fixed categories
    return list(DEFAULT_METADATA_TEMPLATES.keys())

def get_metadata_count(excel_filename=None) -> int:
    """Get number of available templates for a file or category"""
    if excel_filename:
        metadata = get_metadata_from_excel_file(excel_filename)
        return len(metadata) if metadata else 0
    
    # For default category
    if 'general' in DEFAULT_METADATA_TEMPLATES:
        return len(DEFAULT_METADATA_TEMPLATES['general']['titles'])
    return 0

def get_random_thumbnail_by_tag(user_id: int, tag: str) -> Optional[Dict]:
    """Get random thumbnail by tag - wrapper for database function"""
    try:
        from modules.database.database import get_random_thumbnail_by_tag as db_get_random_thumbnail
        return db_get_random_thumbnail(user_id, tag)
    except Exception as e:
        print(f"Error getting random thumbnail: {e}")
        return None

def get_all_thumbnail_tags(user_id: int) -> List[str]:
    """Get all thumbnail tags - wrapper for database function"""
    try:
        from modules.database.database import get_all_thumbnail_tags as db_get_all_thumbnail_tags
        return db_get_all_thumbnail_tags(user_id)
    except Exception as e:
        print(f"Error getting thumbnail tags: {e}")
        return []

def save_metadata_cache(user_id: int, category: str, metadata_list: List[Dict]) -> bool:
    """Save generated metadata to cache"""
    try:
        from modules.database.database import save_random_metadata_cache
        
        titles = [m['title'] for m in metadata_list]
        descriptions = [m['description'] for m in metadata_list]
        tags_list = [m['tags'] for m in metadata_list]
        
        return save_random_metadata_cache(user_id, category, titles, descriptions, tags_list)
    except Exception as e:
        print(f"Error saving metadata cache: {e}")
        return False

def get_cached_metadata(user_id: int, category: str) -> Optional[Dict]:
    """Get cached metadata"""
    try:
        from modules.database.database import get_random_metadata_cache
        return get_random_metadata_cache(user_id, category)
    except Exception as e:
        print(f"Error getting cached metadata: {e}")
        return None

def select_random_metadata(user_id: int, excel_filename: str = None) -> Optional[Dict]:
    """Select one random metadata from Excel file or cache/generate fallback"""
    try:
        # Try to get from Excel file
        if excel_filename:
            metadata = get_random_metadata(excel_filename, 1)
            if metadata:
                return metadata[0]
        
        # Fall back to cached metadata
        cached = get_cached_metadata(user_id, 'general')
        if cached and cached['titles'] and cached['descriptions'] and cached['tags']:
            import random
            
            titles = cached['titles']
            descriptions = cached['descriptions'] 
            tags_list = cached['tags']
            
            # Select random combination
            title = random.choice(titles)
            description = random.choice(descriptions)
            tags = random.choice(tags_list)
            
            return {
                'title': title,
                'description': description, 
                'tags': tags
            }
        
        # Generate new metadata and cache it
        metadata_list = generate_random_metadata('general', 10)  # Generate 10 templates
        save_metadata_cache(user_id, 'general', metadata_list)
        
        if metadata_list:
            import random
            return random.choice(metadata_list)
        
        return None
    except Exception as e:
        print(f"Error selecting random metadata: {e}")
        return None

def get_playlist_options(user_id: int) -> List[Dict]:
    """Get playlist options for user"""
    try:
        from modules.database.database import get_all_playlist_cache
        return get_all_playlist_cache(user_id)
    except Exception as e:
        print(f"Error getting playlist options: {e}")
        return []

def select_random_thumbnail_for_schedule(user_id: int, category: str = 'general') -> Optional[str]:
    """Select random thumbnail suitable for the category"""
    import random
    
    # Get available thumbnail tags
    available_tags = get_all_thumbnail_tags(user_id)
    
    if not available_tags:
        return None
    
    # Map categories to preferred thumbnail tags
    category_to_tags = {
        'general': ['general', 'content', 'video'],
        'music': ['music', 'audio', 'sound', 'melody'],
        'gaming': ['game', 'gaming', 'esports', 'gameplay'],
        'tutorial': ['education', 'learning', 'tutorial', 'guide'],
        'lifestyle': ['lifestyle', 'daily', 'routine', 'life'],
        'entertainment': ['entertainment', 'fun', 'comedy', 'entertainment']
    }
    
    # Get preferred tags for category, or use all available tags
    preferred_tags = category_to_tags.get(category, available_tags)
    matching_tags = [tag for tag in preferred_tags if tag in available_tags]
    
    # If no matching tags, use random available tag
    selected_tag = random.choice(matching_tags if matching_tags else available_tags)
    
    # Get random thumbnail with selected tag
    thumbnail = get_random_thumbnail_by_tag(user_id, selected_tag)
    
    return thumbnail['id'] if thumbnail else None
