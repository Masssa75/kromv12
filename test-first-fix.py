#!/usr/bin/env python3
"""Test the fix on FIRST token"""
import sys
sys.path.append('.')

# Import the fixed processor function
from fixed_parallel_ath import process_single_token

# FIRST token data
token_data = (
    "94ace5ec-696d-43de-b763-efca7d0f0f94",  # id
    "FIRST",  # ticker
    "solana",  # network
    "HWqsR2EZdnr6xptXNA43uK6UQ7FAApgpZUyWCo9w1tP1",  # pool
    None,  # buy_timestamp (null)
    "0.0000497015",  # price_at_call
    {"timestamp": 1753756555}  # raw_data with timestamp
)

print("Testing FIRST token with fixed ATH calculation...")
print("-" * 60)

# Process it
result = process_single_token(token_data)

if result == 1:
    print("\n✅ Successfully processed!")
else:
    print("\n❌ Processing failed!")