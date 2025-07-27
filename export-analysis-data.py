#!/usr/bin/env python3
"""Export Supabase analysis data for local analysis"""

import os
import json
import csv
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(url, key)

print("Exporting analysis data from KROMV12...")
print("=" * 60)

# Get all analyzed calls
try:
    # Fetch all calls with analysis
    result = supabase.table('crypto_calls') \
        .select('*') \
        .not_.is_('analysis_tier', 'null') \
        .order('created_at', desc=True) \
        .execute()
    
    print(f"Found {len(result.data)} analyzed calls")
    
    # Save as JSON for detailed analysis
    with open('kromv12_analysis_export.json', 'w') as f:
        json.dump(result.data, f, indent=2)
    print("✓ Saved to kromv12_analysis_export.json")
    
    # Save as CSV for easy viewing
    if result.data:
        with open('kromv12_analysis_export.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=result.data[0].keys())
            writer.writeheader()
            writer.writerows(result.data)
        print("✓ Saved to kromv12_analysis_export.csv")
    
    # Create summary statistics
    stats = {
        'total_analyzed': len(result.data),
        'claude_tiers': {},
        'x_tiers': {},
        'both_alpha': 0,
        'premium_worthy': 0
    }
    
    for call in result.data:
        # Claude tiers
        claude_tier = call.get('analysis_tier', 'UNKNOWN')
        stats['claude_tiers'][claude_tier] = stats['claude_tiers'].get(claude_tier, 0) + 1
        
        # X tiers
        x_tier = call.get('x_analysis_tier', 'UNKNOWN')
        stats['x_tiers'][x_tier] = stats['x_tiers'].get(x_tier, 0) + 1
        
        # Both ALPHA
        if claude_tier == 'ALPHA' and x_tier == 'ALPHA':
            stats['both_alpha'] += 1
        
        # Premium worthy (SOLID or ALPHA in either)
        if claude_tier in ['ALPHA', 'SOLID'] or x_tier in ['ALPHA', 'SOLID']:
            stats['premium_worthy'] += 1
    
    # Save statistics
    with open('kromv12_analysis_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    print("\nAnalysis Summary:")
    print(f"  Total analyzed: {stats['total_analyzed']}")
    print(f"  Premium worthy (SOLID/ALPHA): {stats['premium_worthy']} ({stats['premium_worthy']/stats['total_analyzed']*100:.1f}%)")
    print(f"  Both ALPHA: {stats['both_alpha']}")
    
    print("\nFiles created:")
    print("  - kromv12_analysis_export.json (full data)")
    print("  - kromv12_analysis_export.csv (spreadsheet format)")
    print("  - kromv12_analysis_stats.json (summary statistics)")
    
except Exception as e:
    print(f"Error: {e}")