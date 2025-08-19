#!/usr/bin/env python3
"""Monitor analysis progress"""

import sqlite3
import time
from datetime import datetime

def check_progress():
    conn = sqlite3.connect('token_discovery_analysis.db')
    cursor = conn.cursor()
    
    # Get statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            AVG(total_score) as avg_score,
            MIN(total_score) as min_score,
            MAX(total_score) as max_score,
            SUM(CASE WHEN proceed_to_stage_2 = 1 THEN 1 ELSE 0 END) as stage2_count,
            MAX(analyzed_at) as last_analyzed
        FROM website_analysis
    """)
    stats = cursor.fetchone()
    
    # Get score distribution
    cursor.execute("""
        SELECT 
            CASE 
                WHEN total_score <= 5 THEN '0-5'
                WHEN total_score <= 10 THEN '6-10'
                WHEN total_score <= 15 THEN '11-15'
                ELSE '16-21'
            END as range,
            COUNT(*) as count
        FROM website_analysis
        GROUP BY range
        ORDER BY range
    """)
    distribution = cursor.fetchall()
    
    # Get recent analyses
    cursor.execute("""
        SELECT ticker, total_score, proceed_to_stage_2, analyzed_at
        FROM website_analysis
        ORDER BY analyzed_at DESC
        LIMIT 5
    """)
    recent = cursor.fetchall()
    
    conn.close()
    
    # Display results
    print("\n" + "=" * 60)
    print(f"TOKEN DISCOVERY ANALYSIS PROGRESS - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    print(f"\nTotal Analyzed: {stats[0]} / 157 tokens ({stats[0]/157*100:.1f}%)")
    print(f"Average Score: {stats[1]:.1f}/21")
    print(f"Score Range: {stats[2]}-{stats[3]}/21")
    print(f"Stage 2 Qualified: {stats[4]} ({stats[4]/stats[0]*100:.1f}%)")
    
    print(f"\nScore Distribution:")
    for range_name, count in distribution:
        pct = count / stats[0] * 100
        bar = '█' * int(pct / 2)
        print(f"  {range_name:6} : {bar:25} {count:3} ({pct:.1f}%)")
    
    print(f"\nLast 5 Analyzed:")
    for ticker, score, stage2, analyzed_at in recent:
        stage2_str = "✓" if stage2 else "✗"
        print(f"  {ticker:10} - Score: {score:2}/21 - Stage 2: {stage2_str} - {analyzed_at[11:19]}")
    
    # Estimate remaining time
    if stats[0] > 10:  # Need some data to estimate
        # Parse last analyzed time
        last_time = datetime.fromisoformat(stats[5])
        time_per_token = (datetime.now() - last_time).total_seconds() / 1  # Rough estimate
        remaining = 157 - stats[0]
        eta_seconds = remaining * 15  # Assume 15 seconds per token
        eta_minutes = eta_seconds / 60
        print(f"\nEstimated time remaining: {eta_minutes:.1f} minutes")

if __name__ == "__main__":
    while True:
        check_progress()
        time.sleep(30)  # Check every 30 seconds