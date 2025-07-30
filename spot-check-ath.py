#!/usr/bin/env python3
"""Quick spot check of ATH calculations"""
import requests
import random
from test_3tier_ath import find_ath_3tier
from datetime import datetime

# Get a random sample
response = requests.post(
    'https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query',
    headers={'Authorization': 'Bearer sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7', 'Content-Type': 'application/json'},
    json={'query': 'SELECT * FROM crypto_calls WHERE ath_price IS NOT NULL ORDER BY RANDOM() LIMIT 5'}
)
tokens = response.json()

print('🔍 SPOT CHECK VALIDATION')
print('=' * 80)

passed = 0
failed = 0

for token in tokens:
    print(f"\nChecking {token['ticker']} on {token['network']}:")
    
    try:
        # Get timestamp
        call_timestamp = None
        if token['buy_timestamp']:
            call_timestamp = int(datetime.fromisoformat(token['buy_timestamp'].replace('Z', '+00:00')).timestamp())
        elif token['raw_data'] and 'timestamp' in token['raw_data']:
            call_timestamp = token['raw_data']['timestamp']
        
        if not call_timestamp:
            print('  ⚠️  No timestamp available')
            continue
        
        # Run manual verification
        result = find_ath_3tier(
            network=token['network'],
            pool_address=token['pool_address'],
            call_timestamp=call_timestamp,
            ticker=token['ticker'],
            group=token['raw_data'].get('group', 'Unknown') if token['raw_data'] else 'Unknown',
            price_at_call=float(token['price_at_call'])
        )
        
        if result:
            db_ath = float(token['ath_price'])
            db_roi = float(token['ath_roi_percent'])
            manual_ath = result.get('ath_close', 0)
            manual_roi = result.get('close_roi', 0)
            
            price_diff_pct = abs(db_ath - manual_ath) / manual_ath * 100 if manual_ath > 0 else 0
            roi_diff = abs(db_roi - manual_roi)
            
            print(f'  DB ATH: ${db_ath:.8f} | Manual: ${manual_ath:.8f}')
            print(f'  DB ROI: {db_roi:.1f}% | Manual: {manual_roi:.1f}%')
            print(f'  Differences: Price {price_diff_pct:.2f}%, ROI {roi_diff:.2f}')
            
            if price_diff_pct < 1 and roi_diff < 1:
                print('  Status: ✅ PASS')
                passed += 1
            else:
                print('  Status: ❌ FAIL')
                failed += 1
        else:
            print('  ❌ No manual data available')
            
    except Exception as e:
        print(f'  ❗ Error: {e}')

print(f'\n📊 Summary: {passed} passed, {failed} failed')