#!/usr/bin/env python3
"""Monitor the NLP analysis progress"""

import json
import time
import os
from datetime import datetime

print("Monitoring NLP Analysis Progress...")
print("=" * 60)

while True:
    try:
        # Check if progress file exists
        if os.path.exists('nlp_analysis_progress.json'):
            with open('nlp_analysis_progress.json', 'r') as f:
                progress = json.load(f)
            
            processed = progress.get('total_processed', 0)
            found = len(progress.get('results', []))
            last_update = progress.get('last_update', 'Unknown')
            
            # Calculate high scores
            results = progress.get('results', [])
            high_scores = len([r for r in results if r['score'] >= 7])
            very_high = len([r for r in results if r['score'] >= 8])
            
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] Processed: {processed}/4543 ({processed/4543*100:.1f}%) | Found: {found} legitimate | High (7+): {high_scores} | Very High (8+): {very_high}", end='', flush=True)
            
            # Show recent high scores
            if results:
                recent_high = [r for r in results if r['score'] >= 8][-3:]
                if recent_high:
                    print(f"\n\nRecent high scores:")
                    for r in recent_high:
                        print(f"  • {r['ticker']} ({r['score']}) - {r.get('why', 'No reason')[:50]}")
                    print("\n", end='')
        else:
            print("\rWaiting for analysis to start...", end='', flush=True)
    
    except Exception as e:
        print(f"\rError reading progress: {e}", end='', flush=True)
    
    time.sleep(5)  # Check every 5 seconds