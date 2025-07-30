import os
from supabase import create_client
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=== CREATING DATABASE BACKUP ===")
print("Backing up price-related columns before bulk refresh...\n")

# Get all tokens with prices
result = supabase.table('crypto_calls').select(
    'krom_id, ticker, contract_address, network, price_at_call, current_price, roi_percent, price_updated_at'
).not_.is_('current_price', 'null').execute()

print(f"Found {len(result.data)} tokens with prices to backup")

# Create backup with timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = f'/Users/marcschwyn/Desktop/projects/KROMV12/database-backups/price_backup_{timestamp}.json'

# Save to JSON file
backup_data = {
    'backup_timestamp': datetime.now().isoformat(),
    'total_records': len(result.data),
    'description': 'Backup before bulk price refresh with GeckoTerminal pool selection fix',
    'data': result.data
}

with open(backup_file, 'w') as f:
    json.dump(backup_data, f, indent=2)

print(f"\n✅ Backup created: {backup_file}")
print(f"   Total records: {len(result.data)}")
print(f"   File size: {os.path.getsize(backup_file) / 1024 / 1024:.1f} MB")

# Show sample of what was backed up
print("\nSample of backed up data:")
for token in result.data[:5]:
    print(f"  {token['ticker']}: ${token['current_price']} (ROI: {token['roi_percent']:.1f}%)" if token['roi_percent'] else f"  {token['ticker']}: ${token['current_price']}")