import csv

# Process the CSV file directly
input_path = '/Users/marcschwyn/Desktop/projects/KROMV12/kromv12_tweets_export_20250714_211235.csv'
output_path = '/Users/marcschwyn/Desktop/projects/KROMV12/kromv12_tweets_only.csv'

with open(input_path, 'r', encoding='utf-8') as inf:
    with open(output_path, 'w', newline='', encoding='utf-8') as outf:
        reader = csv.reader(inf)
        writer = csv.writer(outf)
        
        # Header
        header = next(reader)
        writer.writerow(header[:5])
        
        # Data rows
        count = 0
        for row in reader:
            writer.writerow(row[:5])
            count += 1

print(f"Processed {count} rows")