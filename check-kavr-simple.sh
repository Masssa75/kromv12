#!/bin/bash

echo "Checking KAVR timestamps..."

curl -X POST "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query" \
  -H "Authorization: Bearer sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT buy_timestamp, created_at, raw_data->>'\''timestamp'\'' as raw_timestamp FROM crypto_calls WHERE ticker = '\''KAVR'\'' LIMIT 1;"
  }' | jq -r '.[0] | "Buy Timestamp: \(.buy_timestamp)\nCreated At: \(.created_at)\nRaw Timestamp: \(.raw_timestamp)"'

echo -e "\n\nConverting timestamps:"
echo "Raw timestamp (Unix): 1753401759"
echo "Raw timestamp (Date): $(date -r 1753401759)"
echo -e "\nTesting Edge Function with this timestamp:"

# Test the Edge Function with the actual call timestamp
curl -s -X POST https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1NjI4ODEsImV4cCI6MjA2MzEzODg4MX0.eaWAToMH3go56vYwvYWpbkgibVTEiv72AtUrqiIChTs" \
  -d '{
    "contractAddress": "0x867585e3DD8fC996Ab220ea9009C091fd948595f",
    "callTimestamp": 1753401759
  }' | jq '{
    priceAtCall: .priceAtCall,
    currentPrice: .currentPrice,
    roi: .roi,
    callDate: .callDate,
    duration: .duration
  }'