#!/bin/bash

# Test the crypto-price-single edge function with a known token

echo "Testing crypto-price-single edge function..."

curl -X POST https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1NjI4ODEsImV4cCI6MjA2MzEzODg4MX0.eaWAToMH3go56vYwvYWpbkgibVTEiv72AtUrqiIChTs" \
  -d '{
    "contractAddress": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "callTimestamp": 1737000000
  }' | jq '.'

echo -e "\n\nThis should return different values for priceAtCall and currentPrice if working correctly."