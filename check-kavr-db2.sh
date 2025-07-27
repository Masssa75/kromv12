#!/bin/bash

echo "Checking KAVR in database using SQL query..."

# Use the Supabase Management API to run SQL
curl -X POST "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query" \
  -H "Authorization: Bearer sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT krom_id, ticker, raw_data, fdv_at_call, current_fdv, price_at_call, current_price FROM crypto_calls WHERE ticker = '\''KAVR'\'' LIMIT 1;"
  }' | jq '.'