#!/usr/bin/env python3
from verify_ath_manual import manual_ath_calculation

# TCM data from database
tcm_token = {
    'ticker': 'TCM',
    'network': 'solana',
    'group': 'Unknown',
    'pool_address': 'FPDxQgk3vDJnQM1HH2D5SuLsmCDNTBRgSU5PZA5EkZDr',
    'call_timestamp': 1747555860,  # 2025-05-18 15:11:00 UTC
    'price_at_call': 0.0000951165
}

print("Testing TCM manually...")
result = manual_ath_calculation(tcm_token)
print(f"\nEdge Function had: ATH ${0.0001138782972558933:.12f} @ 2025-05-18 22:12 UTC (ROI: 19.73%)")