#!/usr/bin/env python3
import csv
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Input and output file paths
input_file = os.path.join(current_dir, 'kromv12_tweets_export_20250714_211235.csv')
output_file = os.path.join(current_dir, 'kromv12_tweets_only.csv')

# Counter for rows processed
row_count = 0

# Read the CSV and write only the first 5 columns
with open(input_file, 'r', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        
        # Process header
        header = next(reader)
        # Keep only the first 5 columns: krom_id, ticker, buy_date, tweet_number, tweet_text
        new_header = header[:5]
        writer.writerow(new_header)
        print(f"Header: {new_header}")
        
        # Process all data rows
        for row in reader:
            # Keep only the first 5 columns
            new_row = row[:5]
            writer.writerow(new_row)
            row_count += 1

print(f"Successfully created {output_file}")
print(f"Processed {row_count} data rows (excluding header)")
print(f"Kept columns: krom_id, ticker, buy_date, tweet_number, tweet_text")