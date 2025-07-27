#!/bin/bash

echo "Testing crypto-price-fetcher batch edge function..."

# Test with a batch including KAVR
curl -X POST https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-fetcher \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Rika2R2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1NjI4ODEsImV4cCI6MjA2MzEzODg4MX0.eaWAToMH3go56vYwvYWpbkgibVTEiv72AtUrqiIChTs" \
  -d '{
    "tokens": [
      {
        "krom_id": "test-kavr",
        "contract_address": "0x5832f53d147b3d6cd4578b9cbd62425c7ea9d0bd",
        "buy_timestamp": "2025-07-01T00:00:00Z"
      }
    ]
  }' | jq '.'