import json
import urllib.request
import os
from datetime import datetime
import gzip

# Load environment variables
env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env_vars[k] = v.strip()

SUPABASE_URL = env_vars['SUPABASE_URL']
SUPABASE_SERVICE_ROLE_KEY = env_vars['SUPABASE_SERVICE_ROLE_KEY']

def fetch_all_calls(limit=1000, offset=0):
    """Fetch all crypto_calls data from Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += f"?select=*"
    url += f"&order=created_at.desc"
    url += f"&limit={limit}&offset={offset}"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching calls: {e}")
        return []

def create_backup():
    """Create a complete backup of the crypto_calls table"""
    print("=== Creating Database Backup ===")
    print(f"Started at: {datetime.now()}\n")
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = "database-backups"
    
    # Create directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"Created directory: {backup_dir}")
    
    backup_filename = f"{backup_dir}/crypto_calls_backup_{timestamp}.json"
    backup_gz_filename = f"{backup_filename}.gz"
    
    # Fetch all data
    all_calls = []
    offset = 0
    batch_size = 1000
    
    print("Fetching data from Supabase...")
    while True:
        batch = fetch_all_calls(limit=batch_size, offset=offset)
        if not batch:
            break
        
        all_calls.extend(batch)
        print(f"  Fetched {len(all_calls)} calls so far...")
        
        if len(batch) < batch_size:
            break
        
        offset += batch_size
    
    print(f"\nTotal calls fetched: {len(all_calls)}")
    
    # Create backup metadata
    backup_data = {
        "metadata": {
            "backup_timestamp": timestamp,
            "backup_date": datetime.now().isoformat(),
            "total_records": len(all_calls),
            "backup_reason": "Before clearing all price data for fresh repopulation",
            "table": "crypto_calls",
            "fields_with_price_data": [
                "price_at_call",
                "current_price",
                "ath_price",
                "ath_timestamp",
                "roi_percent",
                "ath_roi_percent",
                "market_cap_at_call",
                "current_market_cap",
                "ath_market_cap",
                "fdv_at_call",
                "current_fdv",
                "ath_fdv",
                "price_fetched_at",
                "price_network",
                "token_supply"
            ]
        },
        "data": all_calls
    }
    
    # Count how many records have price data
    with_price_data = 0
    for call in all_calls:
        if (call.get('price_at_call') is not None or 
            call.get('current_price') is not None or 
            call.get('ath_price') is not None):
            with_price_data += 1
    
    backup_data["metadata"]["records_with_price_data"] = with_price_data
    
    # Save uncompressed JSON
    print(f"\nSaving backup to: {backup_filename}")
    with open(backup_filename, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    # Also save compressed version
    print(f"Creating compressed backup: {backup_gz_filename}")
    with gzip.open(backup_gz_filename, 'wt', encoding='utf-8') as f:
        json.dump(backup_data, f)
    
    # Get file sizes
    json_size = os.path.getsize(backup_filename) / (1024 * 1024)  # MB
    gz_size = os.path.getsize(backup_gz_filename) / (1024 * 1024)  # MB
    
    print(f"\n=== Backup Complete ===")
    print(f"Total records backed up: {len(all_calls)}")
    print(f"Records with price data: {with_price_data}")
    print(f"Backup file: {backup_filename} ({json_size:.2f} MB)")
    print(f"Compressed: {backup_gz_filename} ({gz_size:.2f} MB)")
    print(f"Compression ratio: {(1 - gz_size/json_size)*100:.1f}% reduction")
    
    # Show a sample of what we're backing up
    if all_calls:
        sample = all_calls[0]
        if sample.get('price_at_call') or sample.get('current_price'):
            print(f"\nSample record with price data ({sample.get('ticker', 'Unknown')}):")
            print(f"  price_at_call: {sample.get('price_at_call')}")
            print(f"  current_price: {sample.get('current_price')}")
            print(f"  ath_price: {sample.get('ath_price')}")
            print(f"  roi_percent: {sample.get('roi_percent')}")
    
    return backup_filename, len(all_calls), with_price_data

if __name__ == "__main__":
    backup_file, total_records, price_records = create_backup()
    
    print(f"\n✅ Backup completed successfully!")
    print(f"\nNext steps:")
    print(f"1. Verify the backup file: {backup_file}")
    print(f"2. Run the price data clearing script")
    print(f"3. Implement new price fetching method")