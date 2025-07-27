#!/bin/bash

echo "Checking KAVR in Supabase database..."

curl -X GET "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls?ticker=eq.KAVR&select=krom_id,ticker,raw_data,fdv_at_call,current_fdv&limit=1" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Rika2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4" | jq '.[] | {
    krom_id,
    ticker,
    contract: .raw_data.token.ca,
    token_name: .raw_data.token.name,
    token_symbol: .raw_data.token.symbol,
    fdv_at_call,
    current_fdv
  }'