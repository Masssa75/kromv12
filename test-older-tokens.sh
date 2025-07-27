#!/bin/bash

echo "Testing older tokens to verify price differences..."

# Get tokens from a few days ago
curl -X POST "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query" \
  -H "Authorization: Bearer sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT ticker, raw_data->>'\''timestamp'\'' as raw_timestamp, price_at_call, current_price, roi_percent FROM crypto_calls WHERE price_at_call IS NOT NULL AND raw_data->>'\''timestamp'\'' IS NOT NULL AND (raw_data->>'\''timestamp'\'')::bigint < 1753300000 ORDER BY (raw_data->>'\''timestamp'\'')::bigint DESC LIMIT 10;"
  }' | jq -r '.[] | "\(.ticker): \((.raw_timestamp | tonumber) | strftime("%m/%d %H:%M")) | Entry=\(.price_at_call) | Now=\(.current_price) | ROI=\(.roi_percent // "N/A")%"'