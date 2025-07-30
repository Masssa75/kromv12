import os
from supabase import create_client, Client
from dotenv import load_dotenv
import time

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("=== FIXING MISSING ROI FOR ALL TOKENS ===")
print("This will calculate and update ROI for tokens with both prices but no ROI\n")

# First, get count of tokens to fix
count_query = supabase.table("crypto_calls").select("count", count="exact").not_.is_("price_at_call", "null").not_.is_("current_price", "null").is_("roi_percent", "null")
count_result = count_query.execute()
total_to_fix = count_result.count

print(f"Total tokens to fix: {total_to_fix:,}\n")

print("Starting ROI calculation...")

# Process in batches
batch_size = 100
offset = 0
total_updated = 0
errors = 0

while offset < total_to_fix:
    # Get batch of tokens
    batch = supabase.table("crypto_calls").select("krom_id, ticker, price_at_call, current_price").not_.is_("price_at_call", "null").not_.is_("current_price", "null").is_("roi_percent", "null").limit(batch_size).offset(offset).execute()
    
    if not batch.data:
        break
    
    # Update each token
    for token in batch.data:
        try:
            # Calculate ROI
            roi = ((token['current_price'] - token['price_at_call']) / token['price_at_call']) * 100
            
            # Update database
            update_result = supabase.table("crypto_calls").update({
                "roi_percent": roi
            }).eq("krom_id", token['krom_id']).execute()
            
            total_updated += 1
            
        except Exception as e:
            print(f"Error updating {token['ticker']}: {e}")
            errors += 1
    
    # Progress update
    progress = min(offset + batch_size, total_to_fix)
    print(f"Progress: {progress:,}/{total_to_fix:,} ({progress/total_to_fix*100:.1f}%) - Updated: {total_updated:,}, Errors: {errors}")
    
    offset += batch_size
    time.sleep(0.1)  # Small delay to avoid overwhelming the database

print(f"\n=== COMPLETE ===")
print(f"Total updated: {total_updated:,}")
print(f"Total errors: {errors}")
print(f"Success rate: {total_updated/(total_updated+errors)*100:.1f}%")

# Verify the fix
print("\n=== VERIFICATION ===")
roi_count = supabase.table("crypto_calls").select("count", count="exact").not_.is_("roi_percent", "null").execute()
print(f"Total tokens with ROI now: {roi_count.count:,}")
