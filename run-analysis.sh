#!/bin/bash

echo "Starting KROM Legitimacy Analysis"
echo "================================="
echo "This will analyze all 4,543 crypto calls for legitimacy indicators"
echo "Processing 25 calls per minute to respect API rate limits"
echo "Total estimated time: ~3 hours"
echo ""
echo "The script will:"
echo "1. Look for real companies, products, and utilities"
echo "2. Identify named teams, funding, and partnerships"
echo "3. Score each project 1-10 for legitimacy"
echo "4. Save progress continuously (can be resumed if interrupted)"
echo ""
echo "Results will be saved to: final_nlp_complete.json"
echo ""

# Run the analyzer
python3 final-nlp-analyzer.py

echo ""
echo "Analysis complete! Check final_nlp_complete.json for results."