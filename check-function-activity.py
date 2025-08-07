#!/usr/bin/env python3
import os
from datetime import datetime, timedelta, timezone
from supabase import create_client
from dotenv import load_dotenv
from dateutil import parser

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Check ultra-tracker updates (last 15 minutes)
fifteen_min_ago = (datetime.utcnow() - timedelta(minutes=15)).isoformat()
result = supabase.table('crypto_calls').select('id, ticker, ath_last_checked, current_price, ath_price, ath_roi_percent, price_updated_at').gte('ath_last_checked', fifteen_min_ago).order('ath_last_checked', desc=True).execute()

print('=== Ultra-Tracker Updates (Last 15 minutes) ===')
print(f'Total tokens updated: {len(result.data)}')

if result.data:
    # Show sample of recent updates
    print('\nMost recent 10 updates:')
    for token in result.data[:10]:
        check_time = token.get('ath_last_checked', 'N/A')
        if check_time != 'N/A':
            # Parse and format the time
            dt = parser.parse(check_time)
            if not dt.tzinfo:
                dt = dt.replace(tzinfo=timezone.utc)
            mins_ago = (datetime.now(timezone.utc) - dt).total_seconds() / 60
            print(f'  - {token["ticker"]}: {mins_ago:.1f} minutes ago')
            if token.get('ath_price'):
                print(f'    ATH: ${token["ath_price"]:.8f}, ROI: {token.get("ath_roi_percent", 0):.1f}%')

# Check price updates to see ultra-tracker activity
price_result = supabase.table('crypto_calls').select('id, ticker, price_updated_at').gte('price_updated_at', fifteen_min_ago).execute()
print(f'\nTotal price updates in last 15 min: {len(price_result.data)}')

# Check ATH verifier updates (last 10 minutes) - look for ATH timestamp changes
print('\n=== ATH Verifier Activity (Last 10 minutes) ===')
ten_min_ago = (datetime.utcnow() - timedelta(minutes=10)).isoformat()

# The verifier updates ath_last_checked when it verifies ATH
verifier_result = supabase.table('crypto_calls').select('id, ticker, ath_last_checked, ath_price, ath_roi_percent, ath_timestamp').gte('ath_last_checked', ten_min_ago).order('ath_last_checked', desc=True).limit(250).execute()

# Filter to see which ones might be from verifier (it processes 25 tokens/min)
verifier_tokens = []
ultra_tokens = []
for token in verifier_result.data:
    check_time = token.get('ath_last_checked', '')
    if check_time:
        dt = parser.parse(check_time)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        mins_ago = (datetime.now(timezone.utc) - dt).total_seconds() / 60
        if mins_ago <= 10:
            # Try to distinguish between ultra-tracker and verifier
            # Verifier processes 25/min, ultra processes ~3200/min
            # If many tokens have the exact same timestamp, likely ultra-tracker
            verifier_tokens.append((token, mins_ago))

# Group by timestamp to identify patterns
from collections import defaultdict
timestamp_groups = defaultdict(list)
for token, mins_ago in verifier_tokens:
    timestamp = token.get('ath_last_checked', '')
    timestamp_groups[timestamp].append(token['ticker'])

# If we see groups of 30+ with same timestamp, those are ultra-tracker
# If we see smaller groups or individual timestamps, those are verifier
verifier_count = 0
for timestamp, tickers in timestamp_groups.items():
    if len(tickers) < 30:  # Likely verifier (processes 25/min individually)
        verifier_count += len(tickers)

print(f'Estimated verifier checks in last 10 min: ~{verifier_count} tokens')
print(f'Total ATH checks in last 10 min: {len(verifier_tokens)} tokens')

# Show some examples
if verifier_tokens:
    print('\nSample of recent ATH checks:')
    for token, mins_ago in verifier_tokens[:5]:
        print(f'  - {token["ticker"]}: {mins_ago:.1f} minutes ago')
        if token.get('ath_timestamp'):
            ath_dt = parser.parse(token['ath_timestamp'])
            print(f'    ATH: ${token.get("ath_price", 0):.8f} on {ath_dt.strftime("%Y-%m-%d")}, ROI: {token.get("ath_roi_percent", 0):.1f}%')

# Check for discrepancy notifications (would be in logs, but we can check for recent ATH changes)
print('\n=== Checking for potential discrepancies ===')
# Look for tokens where ATH was updated recently
five_min_ago = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
recent_ath_updates = supabase.table('crypto_calls').select('ticker, ath_price, ath_roi_percent, ath_timestamp').gte('ath_timestamp', five_min_ago).execute()

if recent_ath_updates.data:
    print(f'Found {len(recent_ath_updates.data)} tokens with new ATH timestamps in last 5 minutes:')
    for token in recent_ath_updates.data[:5]:
        print(f'  - {token["ticker"]}: ATH ${token["ath_price"]:.8f}, ROI {token["ath_roi_percent"]:.1f}%')
else:
    print('No ATH timestamp updates in last 5 minutes (no new ATHs found)')

# Check logs for verifier function
print('\n=== Checking Edge Function Logs ===')
print('To see if ATH verifier found discrepancies, run:')
print('npx supabase functions logs crypto-ath-verifier --project-ref eucfoommxxvqmmwdbkdv')