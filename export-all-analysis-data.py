#!/usr/bin/env python3
"""Export ALL Supabase analysis data using pagination"""

import os
import json
import csv
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(url, key)

print("Exporting ALL analysis data from KROMV12...")
print("=" * 60)

# Fetch all calls with analysis using pagination
all_data = []
page_size = 1000
offset = 0

try:
    while True:
        print(f"Fetching rows {offset} to {offset + page_size}...")
        
        result = supabase.table('crypto_calls') \
            .select('*') \
            .not_.is_('analysis_tier', 'null') \
            .order('created_at', desc=True) \
            .range(offset, offset + page_size - 1) \
            .execute()
        
        if not result.data:
            break
            
        all_data.extend(result.data)
        print(f"  Got {len(result.data)} rows (total so far: {len(all_data)})")
        
        if len(result.data) < page_size:
            break
            
        offset += page_size
    
    print(f"\nTotal analyzed calls fetched: {len(all_data)}")
    
    # Save as JSON
    with open('kromv12_ALL_analysis_export.json', 'w') as f:
        json.dump(all_data, f, indent=2)
    print("✓ Saved to kromv12_ALL_analysis_export.json")
    
    # Save as CSV
    if all_data:
        with open('kromv12_ALL_analysis_export.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_data[0].keys())
            writer.writeheader()
            writer.writerows(all_data)
        print("✓ Saved to kromv12_ALL_analysis_export.csv")
    
    # Create comprehensive statistics
    stats = {
        'total_analyzed': len(all_data),
        'claude_tiers': {},
        'x_tiers': {},
        'both_alpha': [],
        'both_solid': [],
        'premium_worthy': 0,
        'disagreements': {
            'claude_better': 0,  # Claude rated higher than X
            'x_better': 0,       # X rated higher than Claude
            'examples': []
        }
    }
    
    tier_rank = {'ALPHA': 4, 'SOLID': 3, 'BASIC': 2, 'TRASH': 1}
    
    for call in all_data:
        # Claude tiers
        claude_tier = call.get('analysis_tier', 'UNKNOWN')
        stats['claude_tiers'][claude_tier] = stats['claude_tiers'].get(claude_tier, 0) + 1
        
        # X tiers
        x_tier = call.get('x_analysis_tier', 'UNKNOWN')
        stats['x_tiers'][x_tier] = stats['x_tiers'].get(x_tier, 0) + 1
        
        # Both ALPHA
        if claude_tier == 'ALPHA' and x_tier == 'ALPHA':
            stats['both_alpha'].append({
                'ticker': call.get('ticker'),
                'created_at': call.get('created_at')
            })
        
        # Both SOLID
        if claude_tier == 'SOLID' and x_tier == 'SOLID':
            stats['both_solid'].append({
                'ticker': call.get('ticker'),
                'created_at': call.get('created_at')
            })
        
        # Premium worthy
        if claude_tier in ['ALPHA', 'SOLID'] or x_tier in ['ALPHA', 'SOLID']:
            stats['premium_worthy'] += 1
        
        # Disagreements
        if claude_tier in tier_rank and x_tier in tier_rank:
            if tier_rank[claude_tier] > tier_rank[x_tier]:
                stats['disagreements']['claude_better'] += 1
                if len(stats['disagreements']['examples']) < 10:
                    stats['disagreements']['examples'].append({
                        'ticker': call.get('ticker'),
                        'claude': claude_tier,
                        'x': x_tier,
                        'message': call.get('raw_data', {}).get('text', '')[:100] if isinstance(call.get('raw_data'), dict) else ''
                    })
            elif tier_rank[x_tier] > tier_rank[claude_tier]:
                stats['disagreements']['x_better'] += 1
    
    # Save statistics
    with open('kromv12_ALL_analysis_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    print("\nAnalysis Summary:")
    print(f"  Total analyzed: {stats['total_analyzed']}")
    print(f"  Premium worthy (SOLID/ALPHA): {stats['premium_worthy']} ({stats['premium_worthy']/stats['total_analyzed']*100:.1f}%)")
    print(f"  Both ALPHA: {len(stats['both_alpha'])}")
    print(f"  Both SOLID: {len(stats['both_solid'])}")
    print(f"\nDisagreements:")
    print(f"  Claude rated higher: {stats['disagreements']['claude_better']}")
    print(f"  X rated higher: {stats['disagreements']['x_better']}")
    
except Exception as e:
    print(f"Error: {e}")