import csv
import os

# Define input and output file paths with absolute paths
base_dir = '/Users/marcschwyn/Desktop/projects/KROMV12'
input_file = os.path.join(base_dir, 'kromv12_tweets_export_20250714_211235.csv')
output_file = os.path.join(base_dir, 'kromv12_tweets_only.csv')

print(f"Starting to process {input_file}...")

# Open input and output files
with open(input_file, 'r', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        
        # Read and write header
        header = next(reader)
        print(f"Original header: {header}")
        
        # Keep only first 5 columns
        new_header = header[:5]
        print(f"New header: {new_header}")
        writer.writerow(new_header)
        
        # Process all rows
        row_count = 0
        for row in reader:
            # Write only the first 5 columns
            writer.writerow(row[:5])
            row_count += 1
            
            # Print progress every 1000 rows
            if row_count % 1000 == 0:
                print(f"Processed {row_count} rows...")

print(f"\nCompleted! Processed {row_count} total rows.")
print(f"Output file: {output_file}")
print("The file contains only these columns: krom_id, ticker, buy_date, tweet_number, tweet_text")