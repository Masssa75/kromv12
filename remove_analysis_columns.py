#!/usr/bin/env python3
"""
Remove analysis columns from CSV file (edits in place)
"""

import csv
import os
import sys

def main():
    filename = 'kromv12_tweets_export_20250714_211235.csv'
    
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found in current directory")
        return 1
    
    # Read all data into memory
    print(f"Reading {filename}...")
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        
        # Keep only first 5 columns
        new_header = header[:5]
        
        # Read all rows, keeping only first 5 columns
        rows = []
        for row in reader:
            rows.append(row[:5])
    
    # Write back to the same file
    print(f"Writing back to {filename} with only tweet columns...")
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(new_header)
        writer.writerows(rows)
    
    print(f"✓ Successfully removed analysis columns from {filename}")
    print(f"✓ File now contains {len(rows)} rows with columns: {', '.join(new_header)}")
    print(f"✓ Removed columns: analysis_tier, analysis_summary, analyzed_date")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())