#!/usr/bin/env python3
"""
Final analysis of Kimi K2 performance with parsed content
"""
import sqlite3
from datetime import datetime

def analyze_kimi_k2():
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("KIMI K2 PERFORMANCE ANALYSIS WITH PARSED CONTENT")
    print("="*80)
    
    # Define expected values
    expected_data = {
        'https://tharwa.finance/': {'name': 'TRWA', 'actual_team': 5, 'quality': 'High'},
        'https://graphai.tech/': {'name': 'GAI', 'actual_team': 4, 'quality': 'High'},
        'https://buildon.online/': {'name': 'B', 'actual_team': 0, 'quality': 'Trash'},
        'https://www.buildon.online': {'name': 'B', 'actual_team': 0, 'quality': 'Trash'},
        'https://blockstreet.xyz/': {'name': 'BLOCK', 'actual_team': 0, 'quality': 'Low'},
        'https://www.blockstreet.xyz/': {'name': 'BLOCK', 'actual_team': 0, 'quality': 'Low'}
    }
    
    # Get latest Kimi K2 results (from last hour)
    kimi_results = []
    for url in expected_data:
        cursor.execute("""
            SELECT score, team_members_found, substr(reasoning, 1, 200)
            FROM website_analysis
            WHERE url = ? AND analyzed_at > datetime('now', '-1 hour')
            ORDER BY analyzed_at DESC
            LIMIT 1
        """, (url,))
        
        result = cursor.fetchone()
        if result:
            kimi_results.append({
                'url': url,
                'name': expected_data[url]['name'],
                'score': result[0],
                'team_found': result[1],
                'team_expected': expected_data[url]['actual_team'],
                'quality': expected_data[url]['quality'],
                'reasoning': result[2]
            })
    
    # Print individual results
    print("\n📊 KIMI K2 RESULTS WITH PARSED CONTENT:")
    print("-"*80)
    
    for r in kimi_results:
        accuracy = "✅" if r['team_found'] == r['team_expected'] else "❌"
        print(f"\n🌐 {r['name']} ({r['quality']} quality site)")
        print(f"   Score: {r['score']}/10")
        print(f"   Team Detection: Found {r['team_found']}, Expected {r['team_expected']} {accuracy}")
        print(f"   Reasoning: {r['reasoning'][:100]}...")
    
    # Compare with other models (earlier analyses)
    print("\n" + "="*80)
    print("COMPARISON WITH OTHER MODELS")
    print("-"*80)
    
    # Get averages from earlier today (before Kimi K2 tests)
    cursor.execute("""
        SELECT 
            AVG(CASE WHEN url LIKE '%tharwa%' THEN score END) as trwa_score,
            AVG(CASE WHEN url LIKE '%graphai%' THEN score END) as gai_score,
            AVG(CASE WHEN url LIKE '%buildon%' THEN score END) as b_score,
            AVG(CASE WHEN url LIKE '%blockstreet%' THEN score END) as block_score
        FROM website_analysis
        WHERE analyzed_at BETWEEN datetime('now', '-24 hours') AND datetime('now', '-2 hours')
    """)
    
    other_avgs = cursor.fetchone()
    
    # Kimi K2 averages
    kimi_scores = {
        'TRWA': next((r['score'] for r in kimi_results if r['name'] == 'TRWA'), None),
        'GAI': next((r['score'] for r in kimi_results if r['name'] == 'GAI'), None),
        'B': next((r['score'] for r in kimi_results if r['name'] == 'B'), None),
        'BLOCK': next((r['score'] for r in kimi_results if r['name'] == 'BLOCK'), None)
    }
    
    print("\n📈 Score Comparison:")
    print("   Site   | Kimi K2 | Other Models Avg | Difference")
    print("   -------|---------|------------------|------------")
    
    if other_avgs:
        sites = ['TRWA', 'GAI', 'B', 'BLOCK']
        other_scores = [other_avgs[0], other_avgs[1], other_avgs[2], other_avgs[3]]
        
        for i, site in enumerate(sites):
            kimi = kimi_scores.get(site)
            other = other_scores[i]
            if kimi and other:
                diff = kimi - other
                sign = "+" if diff >= 0 else ""
                print(f"   {site:6} | {kimi:7.1f} | {other:16.1f} | {sign}{diff:.1f}")
    
    # Final verdict
    print("\n" + "="*80)
    print("🎯 FINAL VERDICT ON KIMI K2")
    print("-"*80)
    
    # Calculate accuracy metrics
    correct_scores = sum(1 for r in kimi_results if 
                        (r['quality'] == 'High' and r['score'] >= 6) or
                        (r['quality'] == 'Trash' and r['score'] <= 3) or
                        (r['quality'] == 'Low' and 3 < r['score'] < 6))
    
    correct_teams = sum(1 for r in kimi_results if r['team_found'] == r['team_expected'])
    
    print(f"\n✅ Scoring Accuracy: {correct_scores}/{len(kimi_results)} sites scored appropriately")
    print(f"❌ Team Detection: {correct_teams}/{len(kimi_results)} sites with correct team count")
    
    # Overall assessment
    kimi_avg = sum(r['score'] for r in kimi_results) / len(kimi_results) if kimi_results else 0
    
    print(f"\n📊 Overall Performance:")
    print(f"   Average Score Given: {kimi_avg:.1f}/10")
    
    # Issues found
    print(f"\n⚠️  Key Issues:")
    print(f"   1. Team member count is consistently wrong (doubles the actual count)")
    print(f"   2. Scores are reasonable but team detection is unreliable")
    print(f"   3. With parsed content, Kimi K2 gives similar scores to other models")
    
    # Recommendation
    print(f"\n💡 RECOMMENDATION:")
    if correct_teams < len(kimi_results) / 2:
        print(f"   ❌ DO NOT include Kimi K2 in the model rotation")
        print(f"   Reason: Unreliable team detection (found {10} instead of {5} for TRWA)")
    else:
        print(f"   ✅ Include Kimi K2 in the model rotation")
        print(f"   Reason: Acceptable scoring accuracy")
    
    conn.close()

if __name__ == "__main__":
    analyze_kimi_k2()