import os
from supabase import create_client
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=== CREATING COMPLETE DATABASE BACKUP ===")
print("Backing up ALL price-related data...\n")

# Get total count first
count_result = supabase.table('crypto_calls').select('id', count='exact').not_.is_('current_price', 'null').execute()
total_count = count_result.count
print(f"Total records to backup: {total_count}")

# Fetch all records in batches
all_data = []
batch_size = 1000
offset = 0

while offset < total_count:
    print(f"Fetching batch: {offset}-{offset+batch_size}...")
    batch = supabase.table('crypto_calls').select(
        'krom_id, ticker, contract_address, network, price_at_call, current_price, roi_percent, price_updated_at'
    ).not_.is_('current_price', 'null').range(offset, offset + batch_size - 1).execute()
    
    all_data.extend(batch.data)
    offset += batch_size

print(f"\nFetched {len(all_data)} total records")

# Create backup with timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = f'/Users/marcschwyn/Desktop/projects/KROMV12/database-backups/complete_price_backup_{timestamp}.json'

# Save to JSON file
backup_data = {
    'backup_timestamp': datetime.now().isoformat(),
    'total_records': len(all_data),
    'description': 'Complete backup before bulk price refresh with GeckoTerminal pool selection fix',
    'data': all_data
}

with open(backup_file, 'w') as f:
    json.dump(backup_data, f, indent=2)

print(f"\n✅ Complete backup created: {backup_file}")
print(f"   Total records: {len(all_data)}")
print(f"   File size: {os.path.getsize(backup_file) / 1024 / 1024:.1f} MB")

# Show statistics
roi_values = [t['roi_percent'] for t in all_data if t['roi_percent'] is not None]
print(f"\nBackup statistics:")
print(f"   Records with ROI: {len(roi_values)}")
print(f"   ROI > 1000%: {len([r for r in roi_values if r > 1000])}")
print(f"   ROI < -90%: {len([r for r in roi_values if r < -90])}")