#!/bin/bash
# Run DexScreener price fetcher in a loop

echo "🚀 Starting DexScreener batch price fetching..."
echo "Press Ctrl+C to stop"

count=0
max_runs=100  # Process 100 tokens

while [ $count -lt $max_runs ]; do
    echo ""
    echo "=== Run $((count + 1)) of $max_runs ==="
    python3 fetch-current-prices-dexscreener-simple.py
    
    # Check if script found a token to process
    if [ $? -ne 0 ]; then
        echo "No more tokens to process or error occurred"
        break
    fi
    
    count=$((count + 1))
    
    # Small delay between requests
    sleep 1
done

echo ""
echo "✅ Batch processing complete! Processed $count tokens"