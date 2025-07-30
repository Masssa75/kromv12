#!/usr/bin/env python3
"""
Continuous ATH validation - performs spot checks on processed tokens
"""
import requests
import time
import random
from datetime import datetime
import sys
sys.path.append('.')
from test_3tier_ath import find_ath_3tier

# Configuration
MANAGEMENT_TOKEN = "sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7"
PROJECT_REF = "eucfoommxxvqmmwdbkdv"
CHECK_INTERVAL = 30  # Check every 30 seconds
SAMPLE_SIZE = 5  # Check 5 random tokens each time

def run_query(query):
    """Execute query via Supabase Management API"""
    response = requests.post(
        f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
        headers={"Authorization": f"Bearer {MANAGEMENT_TOKEN}", "Content-Type": "application/json"},
        json={"query": query}
    )
    return response.json()

def validate_token(token):
    """Validate a single token's ATH calculation"""
    try:
        # Get call timestamp
        call_timestamp = None
        if token['buy_timestamp']:
            call_timestamp = int(datetime.fromisoformat(token['buy_timestamp'].replace('Z', '+00:00')).timestamp())
        elif token['raw_data'] and 'timestamp' in token['raw_data']:
            call_timestamp = token['raw_data']['timestamp']
        
        if not call_timestamp:
            return None
        
        # Run manual verification
        result = find_ath_3tier(
            network=token['network'],
            pool_address=token['pool_address'],
            call_timestamp=call_timestamp,
            ticker=token['ticker'],
            group=token['raw_data'].get('group', 'Unknown') if token['raw_data'] else 'Unknown',
            price_at_call=float(token['price_at_call'])
        )
        
        if not result:
            return {
                'status': 'NO_DATA',
                'ticker': token['ticker'],
                'network': token['network']
            }
        
        # Compare results
        db_ath = float(token['ath_price'])
        db_roi = float(token['ath_roi_percent'])
        
        # The test script returns ATH data directly with these fields:
        # ath_high, ath_close, high_roi, close_roi
        # Our edge function uses max(open, close) which is ath_close
        manual_ath = result.get('ath_close', 0)
        manual_roi = result.get('close_roi', 0)
        
        # Calculate differences
        price_diff_pct = abs(db_ath - manual_ath) / manual_ath * 100 if manual_ath > 0 else 0
        roi_diff = abs(db_roi - manual_roi)
        
        return {
            'status': 'PASS' if price_diff_pct < 1 and roi_diff < 1 else 'FAIL',
            'ticker': token['ticker'],
            'network': token['network'],
            'db_ath': db_ath,
            'manual_ath': manual_ath,
            'db_roi': db_roi,
            'manual_roi': manual_roi,
            'price_diff_pct': price_diff_pct,
            'roi_diff': roi_diff
        }
        
    except Exception as e:
        return {
            'status': 'ERROR',
            'ticker': token['ticker'],
            'network': token['network'],
            'error': str(e)
        }

print("🔍 Starting continuous ATH validation")
print(f"Checking {SAMPLE_SIZE} random tokens every {CHECK_INTERVAL} seconds\n")

total_checked = 0
total_passed = 0
total_failed = 0
total_errors = 0

while True:
    # Get random sample of recently processed tokens
    query = """
    SELECT id, ticker, network, pool_address, buy_timestamp, price_at_call, 
           ath_price, ath_roi_percent, raw_data
    FROM crypto_calls
    WHERE ath_price IS NOT NULL
    ORDER BY RANDOM()
    LIMIT {}
    """.format(SAMPLE_SIZE)
    
    tokens = run_query(query)
    
    if not tokens:
        print("No tokens to validate yet...")
        time.sleep(CHECK_INTERVAL)
        continue
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Validating {len(tokens)} tokens...")
    print("-" * 80)
    
    batch_results = []
    
    for token in tokens:
        print(f"Checking {token['ticker']} on {token['network']}...", end=' ')
        result = validate_token(token)
        batch_results.append(result)
        
        if result['status'] == 'PASS':
            print("✅ PASS")
            total_passed += 1
        elif result['status'] == 'FAIL':
            print(f"❌ FAIL (Price diff: {result['price_diff_pct']:.2f}%, ROI diff: {result['roi_diff']:.2f})")
            total_failed += 1
        elif result['status'] == 'NO_DATA':
            print("⚠️  NO DATA")
        else:
            print(f"❗ ERROR: {result.get('error', 'Unknown')}")
            total_errors += 1
        
        total_checked += 1
    
    # Show any failures in detail
    failures = [r for r in batch_results if r['status'] == 'FAIL']
    if failures:
        print("\n⚠️  FAILURES DETECTED:")
        for fail in failures:
            print(f"\n  {fail['ticker']} ({fail['network']}):")
            print(f"    DB ATH: ${fail['db_ath']:.8f} | Manual: ${fail['manual_ath']:.8f}")
            print(f"    DB ROI: {fail['db_roi']:.1f}% | Manual: {fail['manual_roi']:.1f}%")
            print(f"    Differences: Price {fail['price_diff_pct']:.2f}%, ROI {fail['roi_diff']:.2f}")
    
    # Summary
    print(f"\n📊 Validation Summary:")
    print(f"   Total checked: {total_checked}")
    print(f"   Passed: {total_passed} ({total_passed/total_checked*100:.1f}%)")
    print(f"   Failed: {total_failed} ({total_failed/total_checked*100:.1f}%)")
    print(f"   Errors: {total_errors}")
    
    # Get current processing status
    count_result = run_query("SELECT COUNT(*) FROM crypto_calls WHERE ath_price IS NOT NULL")
    total_with_ath = count_result[0]['count']
    print(f"\n📈 Processing Progress: {total_with_ath} tokens have ATH data")
    
    # Wait before next check
    time.sleep(CHECK_INTERVAL)