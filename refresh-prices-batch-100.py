import os
from supabase import create_client
from dotenv import load_dotenv
import requests
import time
from datetime import datetime, timedelta

load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=== BATCH PRICE REFRESH (100 tokens) ===")
print("Processing 100 oldest tokens first...\n")

# Get 100 oldest tokens
tokens = supabase.table('crypto_calls').select(
    'krom_id, ticker, contract_address, network, price_at_call'
).not_.is_('current_price', 'null').not_.is_('contract_address', 'null').order('price_updated_at', desc=False).limit(100).execute()

print(f"Processing {len(tokens.data)} tokens in batches of 30...\n")

updated = 0
failed = 0

# Process in batches of 30
for i in range(0, len(tokens.data), 30):
    batch = tokens.data[i:i+30]
    print(f"\nBatch {i//30 + 1}: Processing {len(batch)} tokens...")
    
    # Prepare addresses
    addresses = ','.join([t['contract_address'] for t in batch])
    
    try:
        # Call DexScreener
        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{addresses}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Process results
            found_prices = {}
            if data.get('pairs'):
                for pair in data['pairs']:
                    contract = pair['baseToken']['address'].lower()
                    if contract not in found_prices:
                        found_prices[contract] = float(pair['priceUsd'])
            
            # Update each token
            for token in batch:
                contract_lower = token['contract_address'].lower()
                
                if contract_lower in found_prices:
                    new_price = found_prices[contract_lower]
                    
                    # Calculate ROI
                    update_data = {
                        'current_price': new_price,
                        'price_updated_at': datetime.utcnow().isoformat()
                    }
                    
                    if token['price_at_call'] and token['price_at_call'] > 0:
                        roi = ((new_price - token['price_at_call']) / token['price_at_call']) * 100
                        update_data['roi_percent'] = roi
                        roi_str = f" (ROI: {roi:.1f}%)"
                    else:
                        roi_str = ""
                    
                    # Update
                    result = supabase.table('crypto_calls').update(update_data).eq('krom_id', token['krom_id']).execute()
                    
                    if result.data:
                        updated += 1
                        print(f"  ✅ {token['ticker']}: ${new_price:.10f}{roi_str}")
                else:
                    failed += 1
                    print(f"  ❌ {token['ticker']}: Not found on DexScreener")
        else:
            print(f"  ❌ API error: {response.status_code}")
            failed += len(batch)
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        failed += len(batch)
    
    time.sleep(0.5)  # Small delay between batches

print(f"\n\n=== SUMMARY ===")
print(f"Updated: {updated} tokens")
print(f"Failed: {failed} tokens") 
print(f"Success rate: {updated/(updated+failed)*100:.1f}%" if updated + failed > 0 else "N/A")

# Show next steps
remaining = supabase.table('crypto_calls').select('id', count='exact').not_.is_('current_price', 'null').not_.is_('contract_address', 'null').lt('price_updated_at', datetime.utcnow() - timedelta(hours=2)).execute()
print(f"\nRemaining tokens to update: {remaining.count}")