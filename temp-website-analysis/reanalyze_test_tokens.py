#!/usr/bin/env python3
"""
Re-analyze the 4 test tokens with proper comprehensive analysis
"""

import os
import sys
import sqlite3
import time

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the comprehensive analyzer
from comprehensive_website_analyzer import analyze_website

def main():
    """Re-analyze the 4 test tokens"""
    
    # Connect to database
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    # Get the 4 test tokens
    test_tokens = [
        ('GAI', 'https://www.gaiai.co/'),
        ('MSIA', 'https://messiah.network'),
        ('STRAT', 'https://www.ethstrat.xyz/'),
        ('REX', 'https://www.etherex.finance/')
    ]
    
    print("="*80)
    print("RE-ANALYZING 4 TEST TOKENS WITH COMPREHENSIVE ANALYSIS")
    print("="*80)
    
    for i, (ticker, url) in enumerate(test_tokens, 1):
        print(f"\n[{i}/4] Analyzing {ticker}: {url}")
        print("-"*60)
        
        try:
            # Delete existing record to start fresh
            cursor.execute("DELETE FROM website_analysis WHERE ticker = ?", (ticker,))
            conn.commit()
            print(f"  ✓ Cleared old data for {ticker}")
            
            # Run comprehensive analysis
            result = analyze_website(url, ticker)
            
            if result:
                print(f"  ✓ Analysis complete for {ticker}")
                print(f"    Score: {result.get('total_score', 'N/A')}/21")
                print(f"    Tier: {result.get('tier', 'N/A')}")
                print(f"    Stage 2: {'Yes' if result.get('proceed_to_stage_2') else 'No'}")
                
                # Show signals
                signals = result.get('exceptional_signals', [])
                if signals:
                    print(f"    Positive signals: {len(signals)}")
                    for signal in signals[:2]:  # Show first 2
                        print(f"      • {signal}")
                
                missing = result.get('missing_elements', [])
                if missing:
                    print(f"    Missing elements: {len(missing)}")
                    for element in missing[:2]:  # Show first 2
                        print(f"      • {element}")
            else:
                print(f"  ⚠️ Analysis failed for {ticker}")
        
        except Exception as e:
            print(f"  ❌ Error analyzing {ticker}: {e}")
        
        # Small delay between analyses
        if i < 4:
            print(f"\n  Waiting 3 seconds before next analysis...")
            time.sleep(3)
    
    # Show final summary
    print("\n" + "="*80)
    print("SUMMARY OF RE-ANALYZED TOKENS")
    print("="*80)
    
    cursor.execute("""
        SELECT ticker, total_score, tier, proceed_to_stage_2,
               exceptional_signals, missing_elements
        FROM website_analysis
        WHERE ticker IN ('GAI', 'MSIA', 'STRAT', 'REX')
        ORDER BY total_score DESC
    """)
    
    for row in cursor.fetchall():
        ticker, score, tier, stage2, signals, missing = row
        signal_count = len(eval(signals)) if signals else 0
        missing_count = len(eval(missing)) if missing else 0
        
        print(f"\n{ticker}:")
        print(f"  Score: {score}/21 ({tier})")
        print(f"  Stage 2: {'✅ Yes' if stage2 else '❌ No'}")
        print(f"  Signals: {signal_count} positive, {missing_count} missing")
    
    conn.close()
    print("\n✅ Re-analysis complete! Check http://localhost:5006 to see updated results.")

if __name__ == "__main__":
    main()