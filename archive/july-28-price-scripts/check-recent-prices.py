#\!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
}

# Get tokens updated in last hour
one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=ticker,current_price,price_updated_at,roi_percent&price_updated_at.gte.{one_hour_ago}&order=price_updated_at.desc&limit=20"

response = requests.get(query, headers=headers)

if response.status_code == 200:
    tokens = response.json()
    print(f"📊 Tokens with prices updated in last hour: {len(tokens)}")
    
    if tokens:
        print("\nRecent updates:")
        for token in tokens[:10]:
            ticker = token.get('ticker', 'UNKNOWN')
            price = token.get('current_price')
            updated = token.get('price_updated_at', '')
            roi = token.get('roi_percent')
            
            if price:
                roi_str = f" (ROI: {roi:+.1f}%)" if roi is not None else ""
                # Parse and format timestamp
                if updated:
                    dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M:%S')
                    print(f"  {ticker}: ${price:.8f}{roi_str} - Updated at {time_str}")
    else:
        print("No recent price updates found.")
else:
    print(f"Error: {response.status_code}")
