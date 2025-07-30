#!/bin/bash
# Continuous parallel ATH processor

echo "🚀 Starting continuous parallel ATH processing"

while true; do
    # Check if there are tokens to process
    count=$(curl -s -X POST "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query" \
        -H "Authorization: Bearer sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7" \
        -H "Content-Type: application/json" \
        -d '{"query": "SELECT COUNT(*) FROM crypto_calls WHERE pool_address IS NOT NULL AND price_at_call IS NOT NULL AND ath_price IS NULL;"}' | jq -r '.[0].count')
    
    if [ "$count" -eq "0" ]; then
        echo "✅ All tokens processed!"
        break
    fi
    
    echo "📊 Tokens remaining: $count"
    
    # Run batch of 500
    python3 simple-parallel-ath.py 2>&1 | grep -v "NotOpenSSL" | grep -E "(Processing|✅|❌|Rate:)"
    
    # Show progress
    ath_count=$(curl -s -X POST "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query" \
        -H "Authorization: Bearer sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7" \
        -H "Content-Type: application/json" \
        -d '{"query": "SELECT COUNT(*) FROM crypto_calls WHERE ath_price IS NOT NULL;"}' | jq -r '.[0].count')
    
    echo "📈 Total with ATH: $ath_count"
    echo "---"
    
    # Small pause between batches
    sleep 2
done