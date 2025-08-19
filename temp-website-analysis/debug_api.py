#!/usr/bin/env python3
"""Debug the API response"""

import requests
import json

response = requests.get('http://localhost:5005/api/results')
data = response.json()

print(f"Status: {response.status_code}")
print(f"Count: {data.get('count', 0)}")
print(f"Results length: {len(data.get('results', []))}")

if data.get('results'):
    print("\nFirst 3 results:")
    for i, result in enumerate(data['results'][:3]):
        print(f"\nResult {i+1}:")
        print(f"  Ticker: {result.get('ticker')}")
        print(f"  URL: {result.get('url')}")
        print(f"  Total Score: {result.get('total_score')}")
        print(f"  Tier: {result.get('tier')}")
        print(f"  Category Scores: {result.get('category_scores')}")
        print(f"  Proceed: {result.get('proceed_to_stage_2')}")