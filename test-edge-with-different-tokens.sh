#!/bin/bash

echo "Testing crypto-price-single edge function with different tokens..."

# Test with a popular token that should have historical data
# Using timestamp from 30 days ago
TIMESTAMP=$(date -v-30d +%s)

echo -e "\n1. Testing with PEPE (Ethereum):"
curl -s -X POST https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1NjI4ODEsImV4cCI6MjA2MzEzODg4MX0.eaWAToMH3go56vYwvYWpbkgibVTEiv72AtUrqiIChTs" \
  -d "{
    \"contractAddress\": \"0x6982508145454ce325ddbe47a25d4ec3d2311933\",
    \"callTimestamp\": $TIMESTAMP
  }" | jq '.'

echo -e "\n2. Testing with BONK (Solana):"
curl -s -X POST https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1NjI4ODEsImV4cCI6MjA2MzEzODg4MX0.eaWAToMH3go56vYwvYWpbkgibVTEiv72AtUrqiIChTs" \
  -d "{
    \"contractAddress\": \"DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263\",
    \"callTimestamp\": $TIMESTAMP
  }" | jq '.'

echo -e "\n3. Testing with SHIB (Ethereum):"
curl -s -X POST https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1NjI4ODEsImV4cCI6MjA2MzEzODg4MX0.eaWAToMH3go56vYwvYWpbkgibVTEiv72AtUrqiIChTs" \
  -d "{
    \"contractAddress\": \"0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce\",
    \"callTimestamp\": $TIMESTAMP
  }" | jq '.'