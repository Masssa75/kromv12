#!/bin/bash

echo "Checking KAVR timestamps in database..."

# Check all timestamp fields for KAVR
curl -X POST "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query" \
  -H "Authorization: Bearer sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT krom_id, ticker, buy_timestamp, created_at, raw_data->>'\''timestamp'\'' as raw_timestamp, (raw_data->'\''token'\''->>'\''pairTimestamp'\'')::bigint as pair_timestamp FROM crypto_calls WHERE ticker = '\''KAVR'\'' LIMIT 1;"
  }' | jq '. | {
    krom_id: .[0].krom_id,
    ticker: .[0].ticker,
    buy_timestamp: .[0].buy_timestamp,
    created_at: .[0].created_at,
    raw_timestamp: .[0].raw_timestamp,
    pair_timestamp: .[0].pair_timestamp,
    buy_date: (.[0].buy_timestamp | if . then strptime("%Y-%m-%dT%H:%M:%S") | strftime("%Y-%m-%d %H:%M:%S UTC") else null end),
    created_date: (.[0].created_at | if . then strptime("%Y-%m-%dT%H:%M:%S") | strftime("%Y-%m-%d %H:%M:%S UTC") else null end),
    raw_date: (.[0].raw_timestamp | if . then tonumber | strftime("%Y-%m-%d %H:%M:%S UTC") else null end),
    pair_date: (.[0].pair_timestamp | if . then strftime("%Y-%m-%d %H:%M:%S UTC") else null end)
  }'