#!/usr/bin/env python3
"""
Edit CSV file in place to remove analysis columns
"""

import csv
import os
import shutil

# File to edit
filename = 'kromv12_tweets_export_20250714_211235.csv'
temp_filename = filename + '.tmp'

# Read and write with only the first 5 columns
with open(filename, 'r', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    
    with open(temp_filename, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        
        # Process header
        header = next(reader)
        new_header = header[:5]  # Keep only first 5 columns
        writer.writerow(new_header)
        
        # Process data rows
        for row in reader:
            new_row = row[:5]  # Keep only first 5 columns
            writer.writerow(new_row)

# Replace original file with edited version
shutil.move(temp_filename, filename)
print(f"Successfully edited {filename} - removed analysis columns")
print("The file now contains only: krom_id, ticker, buy_date, tweet_number, tweet_text")