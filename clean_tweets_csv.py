#!/usr/bin/env python3
"""
Script to extract only the first 5 columns from the KROM tweets export CSV file.
Columns to keep: krom_id, ticker, buy_date, tweet_number, tweet_text
"""

import csv
import os
import sys

def process_csv():
    # Set up file paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, 'kromv12_tweets_export_20250714_211235.csv')
    output_file = os.path.join(script_dir, 'kromv12_tweets_only.csv')
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        return False
    
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print("Starting CSV processing...")
    
    try:
        # Open input and output files
        with open(input_file, 'r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            
            with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
                writer = csv.writer(outfile)
                
                # Read and write header
                header = next(reader)
                print(f"\nOriginal columns ({len(header)}): {header}")
                
                # Keep only first 5 columns
                new_header = header[:5]
                print(f"Keeping columns: {new_header}")
                writer.writerow(new_header)
                
                # Process all rows
                row_count = 0
                for row in reader:
                    # Write only the first 5 columns
                    writer.writerow(row[:5])
                    row_count += 1
                    
                    # Print progress every 5000 rows
                    if row_count % 5000 == 0:
                        print(f"  Processed {row_count:,} rows...")
        
        print(f"\n✓ Successfully processed {row_count:,} rows")
        print(f"✓ Output file created: {output_file}")
        
        # Verify output file
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✓ Output file size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            
            # Read first few lines to verify
            print("\nFirst 3 rows of output file:")
            with open(output_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if i < 3:
                        print(f"  Row {i}: {row}")
                    else:
                        break
        
        return True
        
    except Exception as e:
        print(f"\nError during processing: {e}")
        return False

if __name__ == "__main__":
    success = process_csv()
    sys.exit(0 if success else 1)