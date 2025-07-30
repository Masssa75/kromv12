#!/bin/bash
# Run the fixed ATH processor continuously

echo "🚀 Starting FIXED parallel ATH processing for entire database"
echo "This will process all 5,553 tokens with the corrected algorithm"
echo ""

START_TIME=$(date +%s)

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
    python3 fixed-parallel-ath.py 2>&1 | grep -v "NotOpenSSL" | grep -E "(Processing|✅|❌|Rate:)"
    
    # Show progress
    ath_count=$(curl -s -X POST "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query" \
        -H "Authorization: Bearer sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7" \
        -H "Content-Type: application/json" \
        -d '{"query": "SELECT COUNT(*) FROM crypto_calls WHERE ath_price IS NOT NULL;"}' | jq -r '.[0].count')
    
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    ELAPSED_MIN=$((ELAPSED / 60))
    
    echo "📈 Total with ATH: $ath_count/5553 ($(( ath_count * 100 / 5553 ))%)"
    echo "⏱️  Elapsed time: $ELAPSED_MIN minutes"
    echo "---"
    
    # Small pause between batches
    sleep 2
done

END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))
TOTAL_MIN=$((TOTAL_TIME / 60))

echo ""
echo "🎉 COMPLETE!"
echo "Total processing time: $TOTAL_MIN minutes"
echo "Average rate: $(( 5553 / TOTAL_MIN )) tokens/minute"