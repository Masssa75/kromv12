import os
from supabase import create_client, Client
from dotenv import load_dotenv
import time
import requests
import json

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("=== FAST ROI FIX USING SQL UPDATE ===")
print("This will calculate ROI for all tokens with both prices in one SQL command\n")

# Use Supabase Management API for direct SQL execution
management_token = os.environ.get("SUPABASE_ACCESS_TOKEN")
project_id = "eucfoommxxvqmmwdbkdv"

if not management_token:
    print("Error: SUPABASE_ACCESS_TOKEN not found in .env")
    exit(1)

# SQL to update all ROI at once
sql_query = """
UPDATE crypto_calls
SET roi_percent = ((current_price - price_at_call) / price_at_call) * 100
WHERE price_at_call IS NOT NULL 
  AND current_price IS NOT NULL 
  AND roi_percent IS NULL
  AND price_at_call > 0;
"""

print("Executing SQL update...")

# Execute via Management API
response = requests.post(
    f"https://api.supabase.com/v1/projects/{project_id}/database/query",
    headers={
        "Authorization": f"Bearer {management_token}",
        "Content-Type": "application/json"
    },
    json={"query": sql_query}
)

if response.status_code in [200, 201]:
    print("SQL update completed successfully!")
    
    # Verify the results
    print("\n=== VERIFICATION ===")
    
    # Count tokens with ROI
    roi_count = supabase.table("crypto_calls").select("count", count="exact").not_.is_("roi_percent", "null").execute()
    print(f"Total tokens with ROI now: {roi_count.count:,}")
    
    # Count tokens still missing ROI
    missing_roi = supabase.table("crypto_calls").select("count", count="exact").not_.is_("price_at_call", "null").not_.is_("current_price", "null").is_("roi_percent", "null").execute()
    print(f"Tokens still missing ROI: {missing_roi.count:,}")
    
    # Get some examples of newly calculated ROI
    print("\n=== SAMPLE OF NEWLY CALCULATED ROI ===")
    samples = supabase.table("crypto_calls").select("ticker, price_at_call, current_price, roi_percent").not_.is_("roi_percent", "null").order("price_updated_at", desc=True).limit(10).execute()
    
    for token in samples.data:
        print(f"{token['ticker']}: {token['roi_percent']:.1f}% ROI (${token['price_at_call']} → ${token['current_price']})")
        
else:
    print(f"Error executing SQL: {response.status_code}")
    print(response.text)
