#!/bin/bash

# Script to process backlog of token discoveries with websites
# Processes in batches with the token-discovery-analyzer function

source .env

echo "🚀 Starting backlog processing for token discovery websites..."
echo "=================================================="

# Function to call the analyzer
call_analyzer() {
    local iteration=$1
    echo -n "[$iteration] Calling analyzer... "
    
    response=$(curl -s -X POST "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/token-discovery-analyzer" \
        -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
        -H "Content-Type: application/json" \
        -d '{}' \
        --max-time 120)
    
    if [ $? -eq 0 ]; then
        # Parse the response
        analyzed=$(echo "$response" | jq -r '.analyzed // 0')
        promoted=$(echo "$response" | jq -r '.promoted // 0')
        errors=$(echo "$response" | jq -r '.errors // 0')
        
        echo "✅ Analyzed: $analyzed, Promoted: $promoted, Errors: $errors"
        
        # Return number analyzed (for checking if we should continue)
        echo "$analyzed"
    else
        echo "❌ Failed or timed out"
        echo "0"
    fi
}

# Check initial count
echo "Checking initial backlog..."
initial_count=$(curl -s -X POST "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query" \
    -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "SELECT COUNT(*) as need_analysis FROM token_discovery WHERE website_url IS NOT NULL AND website_analyzed_at IS NULL;"
    }' | jq -r '.[0].need_analysis')

echo "📊 Initial backlog: $initial_count tokens need analysis"
echo ""

# Process in batches
iteration=1
total_analyzed=0
total_promoted=0
consecutive_zeros=0

while true; do
    result=$(call_analyzer $iteration)
    
    # Extract just the number from the last line
    analyzed_count=$(echo "$result" | tail -n 1)
    
    if [ "$analyzed_count" = "0" ]; then
        consecutive_zeros=$((consecutive_zeros + 1))
        if [ $consecutive_zeros -ge 3 ]; then
            echo ""
            echo "⚠️  No tokens analyzed in 3 consecutive attempts. Stopping."
            break
        fi
    else
        consecutive_zeros=0
        total_analyzed=$((total_analyzed + analyzed_count))
    fi
    
    # Check remaining
    remaining=$(curl -s -X POST "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query" \
        -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "query": "SELECT COUNT(*) as need_analysis FROM token_discovery WHERE website_url IS NOT NULL AND website_analyzed_at IS NULL;"
        }' | jq -r '.[0].need_analysis')
    
    echo "   Remaining: $remaining tokens"
    
    if [ "$remaining" = "0" ]; then
        echo ""
        echo "✅ All tokens processed!"
        break
    fi
    
    # Increment iteration
    iteration=$((iteration + 1))
    
    # Add a small delay to avoid overwhelming the system
    sleep 2
    
    # Safety limit
    if [ $iteration -gt 200 ]; then
        echo ""
        echo "⚠️  Reached maximum iterations (200). Stopping."
        break
    fi
done

echo ""
echo "=================================================="
echo "📊 Final Statistics:"
echo "=================================================="

# Get final statistics
stats=$(curl -s -X POST "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query" \
    -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "SELECT COUNT(*) as total_analyzed, COUNT(CASE WHEN website_stage1_score >= 8 THEN 1 END) as qualifying, AVG(website_stage1_score) as avg_score FROM token_discovery WHERE website_analyzed_at IS NOT NULL;"
    }' | jq -r '.[0]')

total_analyzed=$(echo "$stats" | jq -r '.total_analyzed')
qualifying=$(echo "$stats" | jq -r '.qualifying')
avg_score=$(echo "$stats" | jq -r '.avg_score')

echo "Total tokens analyzed: $total_analyzed"
echo "Qualifying tokens (score >= 8): $qualifying"
echo "Average score: $(printf "%.1f" $avg_score)/21"

# Check promoted tokens
promoted_count=$(curl -s "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls?select=ticker&source=eq.new%20pools" \
    -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
    -H "Range: 0-9" | jq '. | length')

echo "Total promoted to crypto_calls: $promoted_count"
echo ""
echo "✨ Backlog processing complete!"