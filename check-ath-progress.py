import os
from supabase import create_client
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("=== ATH Processing Status ===\n")

# Check tokens with ATH data
ath_result = supabase.table('crypto_calls').select('id').not_('ath_price', 'is', None).execute()
ath_count = len(ath_result.data)
print(f"Tokens with ATH data: {ath_count}")

# Check tokens processed in last 2 hours
two_hours_ago = (datetime.utcnow() - timedelta(hours=2)).isoformat()
recent_result = supabase.table('crypto_calls').select('id, ticker, ath_roi_percent, ath_last_checked').gte('ath_last_checked', two_hours_ago).order('ath_last_checked', desc=True).limit(100).execute()

print(f"\nTokens processed in last 2 hours: {len(recent_result.data)}")
if recent_result.data:
    print("\nRecent ATH updates (showing first 5):")
    for token in recent_result.data[:5]:
        print(f"  - {token['ticker']}: ROI {token.get('ath_roi_percent', 0):.1f}%, checked {token['ath_last_checked']}")

# Check for potential notifications (ATH ROI > 10%)
notif_result = supabase.table('crypto_calls').select('ticker, ath_roi_percent, ath_last_checked').gte('ath_last_checked', two_hours_ago).gt('ath_roi_percent', 10).order('ath_roi_percent', desc=True).execute()

print(f"\nTokens with ATH > 10% in last 2 hours: {len(notif_result.data)}")
if notif_result.data:
    print("\nShould have triggered notifications:")
    for token in notif_result.data:
        print(f"  - {token['ticker']}: ROI {token['ath_roi_percent']:.1f}%, checked {token['ath_last_checked']}")

# Check most recent ATH check time
latest_result = supabase.table('crypto_calls').select('ath_last_checked').not_('ath_last_checked', 'is', None).order('ath_last_checked', desc=True).limit(1).execute()
if latest_result.data:
    print(f"\nMost recent ATH check: {latest_result.data[0]['ath_last_checked']}")
    # Check if it's stale
    last_check = datetime.fromisoformat(latest_result.data[0]['ath_last_checked'].replace('Z', '+00:00'))
    minutes_ago = (datetime.utcnow().replace(tzinfo=last_check.tzinfo) - last_check).total_seconds() / 60
    print(f"  (That was {minutes_ago:.1f} minutes ago)")
    
    if minutes_ago > 10:
        print("  ⚠️  WARNING: ATH processing appears to be stopped\!")

# Check for NEW ATHs that would trigger notifications
print("\n=== Checking for NEW ATH notifications ===")
# Look for tokens where current ATH is different from what it was 2 hours ago
# This would indicate a NEW all-time high was reached
new_ath_query = """
    SELECT ticker, ath_roi_percent, ath_last_checked 
    FROM crypto_calls 
    WHERE ath_last_checked >= '{}' 
    AND ath_roi_percent > 10
    ORDER BY ath_last_checked DESC
""".format(two_hours_ago)

# For now, let's check the pattern more carefully
print("\nChecking processing pattern over last hour...")
one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
pattern_result = supabase.table('crypto_calls').select('ath_last_checked').gte('ath_last_checked', one_hour_ago).not_('ath_last_checked', 'is', None).order('ath_last_checked', desc=True).execute()

if pattern_result.data:
    print(f"Tokens processed in last hour: {len(pattern_result.data)}")
    timestamps = [datetime.fromisoformat(d['ath_last_checked'].replace('Z', '+00:00')) for d in pattern_result.data]
    
    if len(timestamps) > 1:
        time_diffs = []
        for i in range(1, len(timestamps)):
            diff = (timestamps[i-1] - timestamps[i]).total_seconds()
            if diff > 0:  # Only positive diffs
                time_diffs.append(diff)
        
        if time_diffs:
            avg_diff = sum(time_diffs) / len(time_diffs)
            print(f"  Average time between updates: {avg_diff:.1f} seconds")
            print(f"  Processing rate: ~{3600/avg_diff:.1f} tokens/hour")
