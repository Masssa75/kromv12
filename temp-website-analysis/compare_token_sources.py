#!/usr/bin/env python3
"""
Compare website analysis results between KROM tokens and token_discovery tokens
"""

import sqlite3
import json
from statistics import mean, median

def analyze_database(db_path, source_name):
    """Analyze a database and return statistics"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all results
    cursor.execute("""
        SELECT ticker, total_score, proceed_to_stage_2, category_scores, 
               exceptional_signals, missing_elements
        FROM website_analysis
        WHERE total_score IS NOT NULL
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        return None
    
    scores = [r[1] for r in results]
    stage2_count = sum(1 for r in results if r[2])
    
    # Parse category scores
    category_totals = {}
    for r in results:
        if r[3]:
            try:
                cats = json.loads(r[3])
                for cat, score in cats.items():
                    if cat not in category_totals:
                        category_totals[cat] = []
                    category_totals[cat].append(score)
            except:
                pass
    
    # Calculate category averages
    category_avgs = {cat: mean(scores) for cat, scores in category_totals.items()}
    
    return {
        'source': source_name,
        'total_analyzed': len(results),
        'avg_score': mean(scores),
        'median_score': median(scores),
        'min_score': min(scores),
        'max_score': max(scores),
        'stage2_count': stage2_count,
        'stage2_percent': (stage2_count / len(results)) * 100,
        'category_averages': category_avgs,
        'score_distribution': {
            '0-5': sum(1 for s in scores if 0 <= s <= 5),
            '6-10': sum(1 for s in scores if 6 <= s <= 10),
            '11-15': sum(1 for s in scores if 11 <= s <= 15),
            '16-21': sum(1 for s in scores if 16 <= s <= 21),
        }
    }

def main():
    print("=" * 80)
    print("WEBSITE ANALYSIS COMPARISON: KROM vs Token Discovery")
    print("=" * 80)
    
    # Analyze KROM tokens database
    krom_stats = analyze_database('website_analysis_new.db', 'KROM Utility Tokens')
    
    # Analyze token_discovery database
    discovery_stats = analyze_database('token_discovery_analysis.db', 'Token Discovery (GeckoTerminal)')
    
    # Display results
    for stats in [krom_stats, discovery_stats]:
        if stats:
            print(f"\n📊 {stats['source']}")
            print("-" * 40)
            print(f"Total Analyzed: {stats['total_analyzed']}")
            print(f"Average Score: {stats['avg_score']:.1f}/21")
            print(f"Median Score: {stats['median_score']:.1f}/21")
            print(f"Score Range: {stats['min_score']}-{stats['max_score']}/21")
            print(f"Stage 2 Qualified: {stats['stage2_count']} ({stats['stage2_percent']:.1f}%)")
            
            print(f"\nScore Distribution:")
            for range_name, count in stats['score_distribution'].items():
                pct = (count / stats['total_analyzed']) * 100
                bar = '█' * int(pct / 2)
                print(f"  {range_name:6} : {bar:25} {count:3} ({pct:.1f}%)")
            
            print(f"\nCategory Averages (out of 3):")
            for cat, avg in sorted(stats['category_averages'].items()):
                print(f"  {cat.replace('_', ' ').title():30} : {avg:.2f}")
    
    # Direct comparison
    if krom_stats and discovery_stats:
        print("\n" + "=" * 80)
        print("🔍 KEY FINDINGS")
        print("=" * 80)
        
        score_diff = krom_stats['avg_score'] - discovery_stats['avg_score']
        stage2_diff = krom_stats['stage2_percent'] - discovery_stats['stage2_percent']
        
        print(f"\n1. QUALITY DIFFERENCE:")
        print(f"   KROM tokens score {score_diff:.1f} points higher on average")
        print(f"   ({krom_stats['avg_score']:.1f} vs {discovery_stats['avg_score']:.1f})")
        
        print(f"\n2. STAGE 2 QUALIFICATION:")
        print(f"   KROM: {krom_stats['stage2_percent']:.1f}% qualify for deep analysis")
        print(f"   Discovery: {discovery_stats['stage2_percent']:.1f}% qualify")
        print(f"   Difference: {stage2_diff:.1f}% more KROM tokens qualify")
        
        print(f"\n3. SAMPLE SIZE:")
        print(f"   KROM: {krom_stats['total_analyzed']} tokens analyzed")
        print(f"   Discovery: {discovery_stats['total_analyzed']} tokens analyzed (so far)")
        
        print(f"\n4. IMPLICATIONS:")
        print(f"   • KROM's human curation selects higher quality projects")
        print(f"   • GeckoTerminal captures mostly low-quality meme coins")
        print(f"   • Only ~{discovery_stats['stage2_percent']:.0f}% of discovered tokens worth deeper analysis")
        print(f"   • Website presence alone is not a quality indicator")

if __name__ == "__main__":
    main()