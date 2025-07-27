#!/bin/bash
cd /Users/marcschwyn/Desktop/projects/KROMV12
python3 << 'EOF'
import csv

input_file = 'kromv12_tweets_export_20250714_211235.csv'
output_file = 'kromv12_tweets_only.csv'

with open(input_file, 'r', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        
        header = next(reader)
        new_header = header[:5]
        writer.writerow(new_header)
        
        row_count = 0
        for row in reader:
            new_row = row[:5]
            writer.writerow(new_row)
            row_count += 1

print(f'Successfully created {output_file} with {row_count} rows')
EOF