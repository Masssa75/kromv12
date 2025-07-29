#!/usr/bin/env python3
import json
import urllib.request
import gzip
from datetime import datetime
import os

print("=== Creating Database Backup Before Column Removal ===")
print()

# Get service key
service_key = None
try:
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('SUPABASE_SERVICE_ROLE_KEY='):
                service_key = line.split('=', 1)[1].strip()
                break
except:
    print("❌ Could not read .env file")
    exit(1)

supabase_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls"

# Create timestamp for filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = "database-backups"
filename = f"{backup_dir}/crypto_calls_backup_{timestamp}.json"
compressed_filename = f"{filename}.gz"

print(f"Backup filename: {filename}")
print()

# Fetch all records
print("Fetching all records from crypto_calls table...")
all_records = []
offset = 0
batch_size = 1000

while True:
    query_url = f"{supabase_url}?select=*&order=created_at.asc&limit={batch_size}&offset={offset}"
    
    req = urllib.request.Request(query_url)
    req.add_header('apikey', service_key)
    req.add_header('Authorization', f'Bearer {service_key}')
    
    try:
        response = urllib.request.urlopen(req)
        records = json.loads(response.read().decode())
        
        if not records:
            break
            
        all_records.extend(records)
        print(f"  Fetched {len(all_records)} records...")
        offset += batch_size
        
    except Exception as e:
        print(f"Error fetching records: {e}")
        break

print(f"\nTotal records fetched: {len(all_records)}")

# Count records with historical_price_usd
hist_count = sum(1 for r in all_records if r.get('historical_price_usd') is not None)
price_count = sum(1 for r in all_records if r.get('price_at_call') is not None)

print(f"Records with historical_price_usd: {hist_count}")
print(f"Records with price_at_call: {price_count}")

# Save to JSON file
print(f"\nSaving to {filename}...")
with open(filename, 'w') as f:
    json.dump({
        'backup_timestamp': datetime.now().isoformat(),
        'total_records': len(all_records),
        'records_with_historical_price_usd': hist_count,
        'records_with_price_at_call': price_count,
        'purpose': 'Backup before removing historical_price_usd column',
        'data': all_records
    }, f, indent=2, default=str)

# Get file size
file_size = os.path.getsize(filename)
print(f"Backup file size: {file_size / 1024 / 1024:.1f} MB")

# Compress the file
print(f"\nCompressing to {compressed_filename}...")
with open(filename, 'rb') as f_in:
    with gzip.open(compressed_filename, 'wb') as f_out:
        f_out.writelines(f_in)

compressed_size = os.path.getsize(compressed_filename)
print(f"Compressed file size: {compressed_size / 1024 / 1024:.1f} MB")
print(f"Compression ratio: {(1 - compressed_size/file_size) * 100:.1f}%")

# Create summary file
summary_filename = f"{backup_dir}/backup_summary_{timestamp}.txt"
with open(summary_filename, 'w') as f:
    f.write(f"Database Backup Summary\n")
    f.write(f"======================\n\n")
    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
    f.write(f"Purpose: Backup before removing historical_price_usd column\n")
    f.write(f"Total records: {len(all_records)}\n")
    f.write(f"Records with historical_price_usd: {hist_count}\n")
    f.write(f"Records with price_at_call: {price_count}\n")
    f.write(f"Backup file: {filename} ({file_size / 1024 / 1024:.1f} MB)\n")
    f.write(f"Compressed file: {compressed_filename} ({compressed_size / 1024 / 1024:.1f} MB)\n")

print(f"\n✅ Backup completed successfully!")
print(f"Files created:")
print(f"  - {filename}")
print(f"  - {compressed_filename}")
print(f"  - {summary_filename}")