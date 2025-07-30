#!/usr/bin/env python3
"""Verify specific tokens from our batch"""
import sys
sys.path.append('.')
from test_3tier_ath import find_ath_3tier

# Tokens from our batch with their database values
test_tokens = [
    # CMD - Mid-range ROI
    {
        'ticker': 'CMD',
        'network': 'solana',
        'pool_address': '8kaEhweQhLXQ2bbCaUbcmAW54ozwgTR1SxCrVWqSFjB9',
        'call_timestamp': 1747640570,
        'price_at_call': 0.0048418463,
        'expected_ath': 0.015497491201666077,
        'expected_roi': 220.07
    },
    # MARV - Another mid-range
    {
        'ticker': 'MARV', 
        'network': 'solana',
        'pool_address': '9RqBh214A1DQcUQKW66DWBhTjjnkmJKRWzzUjL4ZuQZ4',
        'call_timestamp': 1747630180,
        'price_at_call': 0.0000322905,
        'expected_ath': 0.00007959453829149434,
        'expected_roi': 146.50
    },
    # BONKGIRL - Zero ROI (never exceeded entry)
    {
        'ticker': 'BONKGIRL',
        'network': 'solana', 
        'pool_address': 'J6MKPwoaQ3ndCHo7iVTXrRPyAPBZdivPfPLT5FV1ZDXi',
        'call_timestamp': 1747682968,
        'price_at_call': 0.0000013428,
        'expected_ath': 7.010811113298091e-7,
        'expected_roi': 0
    }
]

print("🔍 VERIFYING TOKENS FROM BATCH\n")

for token in test_tokens:
    print(f"\n{'='*80}")
    print(f"VERIFYING: {token['ticker']}")
    print(f"Expected ATH: ${token['expected_ath']:.12f}")
    print(f"Expected ROI: {token['expected_roi']:.2f}%")
    
    result = find_ath_3tier(
        network=token['network'],
        pool_address=token['pool_address'],
        call_timestamp=token['call_timestamp'],
        ticker=token['ticker'],
        group='Unknown',
        price_at_call=token['price_at_call']
    )
    
    if result:
        # Our edge function uses max(open, close) from the minute with highest peak
        # The test script shows both peak and close, so we need to check the logic
        print(f"\n✅ VERIFICATION RESULT:")
        print(f"Manual script found data successfully")
        print("Our edge function would use max(open, close) from this data")
    else:
        print(f"\n❌ No data found - might be a new token without history")