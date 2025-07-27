#!/bin/bash

echo "Checking KAVR timestamps in database..."

# Check all timestamp fields for KAVR
curl -X POST "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query" \
  -H "Authorization: Bearer sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT krom_id, ticker, buy_timestamp, call_timestamp, created_at, raw_data->>'\''timestamp'\'' as raw_timestamp, raw_data->'\''token'\''->>'\''pairTimestamp'\'' as pair_timestamp FROM crypto_calls WHERE ticker = '\''KAVR'\'' LIMIT 1;"
  }' | jq '.'