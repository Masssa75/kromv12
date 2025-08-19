#!/usr/bin/env python3
"""
Compare Kimi K2 performance with other models
"""
import sqlite3
import json
from datetime import datetime

def compare_models():
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    # Get latest analyses from today
    sites = [
        ('https://tharwa.finance/', 'TRWA'),
        ('https://graphai.tech/', 'GAI'),
        ('https://buildon.online/', 'B'),
        ('https://blockstreet.xyz/', 'BLOCK')
    ]
    
    # We'll track results by looking at today's analyses
    print("\n" + "="*70)
    print("KIMI K2 vs OTHER MODELS COMPARISON")
    print("="*70)
    
    # Since we don't have model_name column, we'll compare based on timing
    # Latest entries are from Kimi K2, earlier ones from other models
    
    for site_url, site_name in sites:
        print(f"\n📍 {site_name} ({site_url})")
        print("-"*60)
        
        # Get all recent analyses for this site
        cursor.execute("""
            SELECT score, team_members_found, substr(reasoning, 1, 150), analyzed_at
            FROM website_analysis
            WHERE url = ?
            ORDER BY analyzed_at DESC
            LIMIT 10
        """, (site_url,))
        
        results = cursor.fetchall()
        
        if results:
            # Latest is Kimi K2
            kimi_score, kimi_team, kimi_reason, kimi_time = results[0]
            
            # Earlier ones are from other models
            other_scores = []
            other_teams = []
            
            for score, team, reason, time in results[1:]:
                # Skip if it's from same batch (within 1 minute)
                time_diff = (datetime.fromisoformat(kimi_time) - datetime.fromisoformat(time)).total_seconds()
                if time_diff > 60:  # More than 1 minute apart
                    other_scores.append(score)
                    other_teams.append(team)
            
            # Calculate averages
            avg_other_score = sum(other_scores) / len(other_scores) if other_scores else 0
            avg_other_team = sum(other_teams) / len(other_teams) if other_teams else 0
            
            print(f"🤖 Kimi K2 Results:")
            print(f"   Score: {kimi_score}/10")
            print(f"   Team Members: {kimi_team}")
            print(f"   Reasoning: {kimi_reason}...")
            
            if other_scores:
                print(f"\n📊 Other Models Average (from {len(other_scores)} analyses):")
                print(f"   Score: {avg_other_score:.1f}/10")
                print(f"   Team Members: {avg_other_team:.1f}")
                print(f"   Score Difference: {kimi_score - avg_other_score:+.1f}")
                print(f"   Team Count Difference: {kimi_team - avg_other_team:+.1f}")
    
    # Summary statistics
    print("\n" + "="*70)
    print("SUMMARY ANALYSIS")
    print("="*70)
    
    # Get aggregate statistics
    cursor.execute("""
        SELECT 
            AVG(score) as avg_score,
            AVG(team_members_found) as avg_team,
            COUNT(*) as total_analyses
        FROM website_analysis
        WHERE analyzed_at > datetime('now', '-1 day')
    """)
    
    overall = cursor.fetchone()
    if overall:
        avg_score, avg_team, total = overall
        print(f"📈 Overall Statistics (last 24 hours):")
        print(f"   Total Analyses: {total}")
        print(f"   Average Score: {avg_score:.1f}/10")
        print(f"   Average Team Members Found: {avg_team:.1f}")
    
    # Check for specific patterns
    print("\n🔍 Key Observations:")
    
    # Check Kimi K2's team detection accuracy
    cursor.execute("""
        SELECT url, team_members_found
        FROM website_analysis
        WHERE analyzed_at > datetime('now', '-1 hour')
        ORDER BY analyzed_at DESC
    """)
    
    recent = cursor.fetchall()
    if recent:
        print(f"\n   Kimi K2 Team Detection (latest run):")
        for url, team_count in recent[:4]:
            site = next((s[1] for s in sites if s[0] == url), url[:20])
            actual = {"TRWA": 5, "GAI": 4, "B": 0, "BLOCK": 0}
            expected = actual.get(site, "?")
            status = "✅" if team_count == expected else "❌"
            print(f"     {site}: Found {team_count} (Expected: {expected}) {status}")
    
    conn.close()

if __name__ == "__main__":
    compare_models()