"""
Contoh cara menambah custom metadata templates
"""

# Buka file: /home/ale/proyek/jadwalstream/modules/utils/random_metadata.py
# Cari bagian 'music' dan tambahkan template baru

'music': {
    'titles': [
        # Template existing...
        'Relaxing Music for Focus and Study',
        'Calm Background Music for Work',
        # TAMBAHKAN BARU:
        'Chillout Music for Evening Relaxation',
        'Ambient Sounds for Deep Sleep',
        'Custom Relaxing Piano Mix',
        # ...tambah sesuka Anda
    ],
    'descriptions': [
        # Template existing...
        'Enjoy this calming music perfect for studying...',
        # TAMBAHKAN BARU:
        'Perfect chillout music for evening relaxation and unwinding after a long day.',
        'Deep sleep ambient sounds designed to help you fall asleep naturally.',
        'Custom piano collection for ultimate relaxation and stress relief.',
        # ...tambah sesuka Anda
    ],
    'tags': [
        # Template existing...
        'relaxing music, background music, study music...',
        # TAMBAHKAN BARU:
        'chillout music, evening relaxation, sleep sounds, ambient piano, custom music, deep sleep, stress relief music, unwind, calming piano, sleep aid'
    ]
},

# Contoh kategori baru:
'cooking': {
    'titles': [
        'Easy Home Cooking Recipes',
        'Quick and Delicious Meal Ideas',
        'Homemade Food Tutorial',
        'Cooking Tips and Tricks',
        'Simple Recipes for Beginners'
    ],
    'descriptions': [
        'Learn to cook delicious homemade meals with these easy and quick recipes perfect for beginners.',
        'Discover simple cooking techniques and delicious meal ideas that anyone can make at home.',
        'Step-by-step cooking tutorial with tips and tricks for creating amazing homemade food.'
    ],
    'tags': [
        'cooking, recipes, homemade food, cooking tutorial, meal ideas, easy cooking, home cooking, cooking tips, simple recipes, beginner cooking'
    ]
}
