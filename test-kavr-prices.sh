#!/bin/bash

echo "Testing KAVR token price at different timestamps..."

# KAVR contract address (assuming Ethereum)
CONTRACT="0x5832f53d147b3d6cd4578b9cbd62425c7ea9d0bd"

# Test 1 day ago
TIMESTAMP_1D=$(date -v-1d +%s)
echo -e "\n1 day ago ($(date -v-1d)):"
curl -s -X POST https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1NjI4ODEsImV4cCI6MjA2MzEzODg4MX0.eaWAToMH3go56vYwvYWpbkgibVTEiv72AtUrqiIChTs" \
  -d "{\"contractAddress\": \"$CONTRACT\", \"callTimestamp\": $TIMESTAMP_1D}" | jq '.'

# Test 7 days ago
TIMESTAMP_7D=$(date -v-7d +%s)
echo -e "\n7 days ago ($(date -v-7d)):"
curl -s -X POST https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1NjI4ODEsImV4cCI6MjA2MzEzODg4MX0.eaWAToMH3go56vYwvYWpbkgibVTEiv72AtUrqiIChTs" \
  -d "{\"contractAddress\": \"$CONTRACT\", \"callTimestamp\": $TIMESTAMP_7D}" | jq '.'

# Test 30 days ago
TIMESTAMP_30D=$(date -v-30d +%s)
echo -e "\n30 days ago ($(date -v-30d)):"
curl -s -X POST https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1NjI4ODEsImV4cCI6MjA2MzEzODg4MX0.eaWAToMH3go56vYwvYWpbkgibVTEiv72AtUrqiIChTs" \
  -d "{\"contractAddress\": \"$CONTRACT\", \"callTimestamp\": $TIMESTAMP_30D}" | jq '.'

echo -e "\n=== Testing with Solana address format ==="
# Also test as Solana in case KAVR is on Solana
SOLANA_CONTRACT="5832f53d147b3d6cd4578b9cbd62425c7ea9d0bd"
echo -e "\nTesting as Solana token:"
curl -s -X POST https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Rika2R2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1NjI4ODEsImV4cCI6MjA2MzEzODg4MX0.eaWAToMH3go56vYwvYWpbkgibVTEiv72AtUrqiIChTs" \
  -d "{\"contractAddress\": \"$SOLANA_CONTRACT\", \"callTimestamp\": $TIMESTAMP_7D}" | jq '.'