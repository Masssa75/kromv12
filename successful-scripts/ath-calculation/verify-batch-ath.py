#!/usr/bin/env python3
"""
Verify the ATH calculations from our last batch of 50 tokens
"""
import sys
sys.path.append('.')
from verify_ath_manual import manual_ath_calculation
import json

# Tokens to verify from our last batch (sampling key ones with different ROI ranges)
tokens_to_verify = [
    {
        'ticker': 'ORB',
        'network': 'solana',
        'group': 'Unknown',
        'pool_address': '3mEqd9QcmpMFiJP8F7TTaJhtgaTMyvKBf5LG6d5gUQu4',
        'price_at_call': 0.00003308079088,
        'call_timestamp': 1747663200,  # Approximate
        'expected_ath': 0.00476515915246846,
        'expected_roi': 14318.33609930758
    },
    {
        'ticker': 'NOVAQ',
        'network': 'solana',
        'group': 'Unknown',
        'pool_address': '5XdW9yqvzmRiH2hckRyLgMHbF59jGywANy5xMUp8Muzw',
        'price_at_call': 0.00046429875776,
        'call_timestamp': 1747665000,  # Approximate
        'expected_ath': 0.00467184040061369,
        'expected_roi': 905.5172759480939
    },
    {
        'ticker': 'CMD',
        'network': 'solana',
        'group': 'Unknown',
        'pool_address': '3HHB3xUQGH5bfXJgWH9vLa6ywfHVYGGCwsDxqrUykx86',
        'price_at_call': 0.00484173968327,
        'call_timestamp': 1747658000,  # Approximate
        'expected_ath': 0.015497491201666077,
        'expected_roi': 220.07400155734143
    },
    {
        'ticker': 'MARV',
        'network': 'solana',
        'group': 'Unknown',
        'pool_address': '2WTvEEb5L32L64xH8uiSMprtRGJC6bpLvBxBmknLZJHJ',
        'price_at_call': 0.00003230058328,
        'call_timestamp': 1747652000,  # Approximate
        'expected_ath': 0.00007959453829149434,
        'expected_roi': 146.49521776217262
    },
    {
        'ticker': 'BONKGIRL',
        'network': 'solana',
        'group': 'Unknown',
        'pool_address': '8x8UyKb29qp3VGqxyJUrxAbyXPQ9W9ASsHvXzizLLe7a',
        'price_at_call': 7.78617103206e-7,
        'call_timestamp': 1747682000,  # Approximate
        'expected_ath': 7.010811113298091e-7,
        'expected_roi': 0  # Never exceeded entry
    }
]

print("🔍 VERIFYING ATH CALCULATIONS FROM BATCH")
print("=" * 80)

for i, token in enumerate(tokens_to_verify, 1):
    print(f"\n📊 Token {i}/{len(tokens_to_verify)}: {token['ticker']}")
    print(f"Expected ATH: ${token['expected_ath']:.12f}")
    print(f"Expected ROI: {token['expected_roi']:.2f}%")
    
    # Run manual calculation
    result = manual_ath_calculation(token)
    
    if result:
        # Compare with expected values
        print(f"\n✅ COMPARISON:")
        
        # Get the final ATH price (using max of open/close from our logic)
        manual_ath = result['ath_price']
        manual_roi = result['ath_roi_percent']
        
        # Calculate differences
        price_diff = abs(manual_ath - token['expected_ath']) / token['expected_ath'] * 100
        roi_diff = abs(manual_roi - token['expected_roi'])
        
        print(f"Price Match: {'✅' if price_diff < 1 else '⚠️'} ({price_diff:.2f}% difference)")
        print(f"ROI Match: {'✅' if roi_diff < 1 else '⚠️'} ({roi_diff:.2f}% point difference)")
        
        if price_diff > 1 or roi_diff > 1:
            print(f"⚠️ MISMATCH DETECTED!")
            print(f"Manual ATH: ${manual_ath:.12f}")
            print(f"Manual ROI: {manual_roi:.2f}%")
    else:
        print("❌ Failed to calculate ATH manually")
    
    print("-" * 80)

print("\n✅ VERIFICATION COMPLETE")