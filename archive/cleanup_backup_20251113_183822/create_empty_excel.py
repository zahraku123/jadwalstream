#!/usr/bin/env python3
"""
Helper script to create empty Excel file with proper structure
Run this if live_stream_data.xlsx doesn't exist
"""
import pandas as pd

# Define columns
columns = [
    'title',
    'scheduledStartTime', 
    'videoFile',
    'thumbnail',
    'streamNameExisting',
    'streamIdExisting',
    'token_file',
    'repeat_daily'
]

# Create empty DataFrame
df = pd.DataFrame(columns=columns)

# Save to Excel
df.to_excel('live_stream_data.xlsx', index=False)

print("✅ Empty live_stream_data.xlsx created successfully!")
print("Columns:", ', '.join(columns))
