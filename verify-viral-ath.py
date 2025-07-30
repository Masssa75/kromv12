#!/usr/bin/env python3
"""
Verify VIRAL token ATH calculation
"""
import sys
sys.path.append('.')
from verify_ath_manual import manual_ath_calculation

# VIRAL token data from our processed batch
viral_token = {
    'ticker': 'VIRAL',
    'network': 'solana',
    'group': 'Crypto.com',
    'pool_address': '4wpVnSwRJzUDXgQaUM3xZfnJSdYfQiiQXgPTiPb7kLm5',
    'call_timestamp': 1747600000,  # Approximate based on ATH timestamp
    'price_at_call': 0.0024224336
}

result = manual_ath_calculation(viral_token)
print("\n🔍 COMPARISON WITH OUR EDGE FUNCTION:")
print(f"Our ATH: $0.0034596304")
print(f"Our ROI: 42.82%")