#!/usr/bin/env python3
"""Create a backup of the Supabase database"""
import requests
import json
import gzip
from datetime import datetime
import os

# Configuration
MANAGEMENT_TOKEN = "sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7"
PROJECT_REF = "eucfoommxxvqmmwdbkdv"

def run_query(query):
    """Execute Supabase query"""
    try:
        response = requests.post(
            f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
            headers={"Authorization": f"Bearer {MANAGEMENT_TOKEN}", "Content-Type": "application/json"},
            json={"query": query},
            timeout=30
        )
        return response.json()
    except Exception as e:
        print(f"Query error: {e}")
        return []

# Create timestamp for backup
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = "database-backups"
os.makedirs(backup_dir, exist_ok=True)

print(f"Creating backup at {timestamp}...")

# Get total count
count_result = run_query("SELECT COUNT(*) as count FROM crypto_calls")
total_count = count_result[0]['count'] if count_result else 0
print(f"Total records to backup: {total_count}")

# Fetch all data in chunks
all_data = []
chunk_size = 1000
offset = 0

while offset < total_count:
    print(f"Fetching records {offset} to {offset + chunk_size}...")
    
    # Fetch chunk
    query = f"""
    SELECT * FROM crypto_calls 
    ORDER BY created_at ASC
    LIMIT {chunk_size} OFFSET {offset}
    """
    
    chunk_data = run_query(query)
    if chunk_data:
        all_data.extend(chunk_data)
    
    offset += chunk_size

print(f"Fetched {len(all_data)} records total")

# Save backup
backup_file = f"{backup_dir}/crypto_calls_backup_{timestamp}.json"
compressed_file = f"{backup_file}.gz"

# Write JSON
print(f"Writing backup to {backup_file}...")
with open(backup_file, 'w') as f:
    json.dump({
        'timestamp': timestamp,
        'total_records': len(all_data),
        'table': 'crypto_calls',
        'data': all_data
    }, f, indent=2, default=str)

# Compress
print(f"Compressing to {compressed_file}...")
with open(backup_file, 'rb') as f_in:
    with gzip.open(compressed_file, 'wb') as f_out:
        f_out.writelines(f_in)

# Remove uncompressed version to save space
os.remove(backup_file)

# Get file size
compressed_size = os.path.getsize(compressed_file) / (1024 * 1024)  # MB

# Create summary
summary = f"""Database Backup Summary
======================
Timestamp: {timestamp}
Total Records: {len(all_data)}
Compressed File: {compressed_file}
File Size: {compressed_size:.2f} MB

Recent Changes:
- Added security analysis columns
- Fetched security data for 50 tokens
- Implemented security display in UI
"""

summary_file = f"{backup_dir}/backup_summary_{timestamp}.txt"
with open(summary_file, 'w') as f:
    f.write(summary)

print(f"\n{summary}")
print(f"Backup completed successfully!")