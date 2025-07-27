#!/bin/bash

echo "Checking timestamps for recent tokens with identical prices..."

# Get 5 recent tokens and their timestamps
curl -X POST "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query" \
  -H "Authorization: Bearer sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT ticker, buy_timestamp, created_at, raw_data->>'\''timestamp'\'' as raw_timestamp, price_at_call, current_price FROM crypto_calls WHERE price_at_call IS NOT NULL AND current_price IS NOT NULL ORDER BY created_at DESC LIMIT 5;"
  }' | jq -r '.[] | "\(.ticker): Call=\(.raw_timestamp | tonumber | strftime("%Y-%m-%d %H:%M")) | Created=\(.created_at[0:16]) | Entry=\(.price_at_call) | Now=\(.current_price)"'