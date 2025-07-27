#!/usr/bin/env python3

import sqlite3
from datetime import datetime, timedelta
import json

# Connect to database
db_path = '/Users/marcschwyn/Desktop/projects/KROMV12/krom_calls.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check overall X analysis status
print("=== X ANALYSIS STATUS CHECK ===\n")

# 1. Check how many calls have X analysis
cursor.execute("""
    SELECT 
        COUNT(*) as total_calls,
        COUNT(x_analyzed_at) as x_analyzed,
        COUNT(CASE WHEN x_analyzed_at IS NULL THEN 1 END) as not_x_analyzed,
        COUNT(CASE WHEN x_analysis_tier = 'ALPHA' THEN 1 END) as alpha_calls,
        COUNT(CASE WHEN x_analysis_tier = 'SOLID' THEN 1 END) as solid_calls,
        COUNT(CASE WHEN x_analysis_tier = 'BASIC' THEN 1 END) as basic_calls,
        COUNT(CASE WHEN x_analysis_tier = 'TRASH' THEN 1 END) as trash_calls
    FROM calls
""")
stats = cursor.fetchone()
print(f"Total calls: {stats['total_calls']:,}")
print(f"X analyzed: {stats['x_analyzed']:,}")
print(f"Not X analyzed: {stats['not_x_analyzed']:,}")
print(f"\nX Analysis Tiers:")
print(f"  ALPHA: {stats['alpha_calls']}")
print(f"  SOLID: {stats['solid_calls']}")
print(f"  BASIC: {stats['basic_calls']}")
print(f"  TRASH: {stats['trash_calls']}")

# 2. Check recent X analysis activity
print("\n=== RECENT X ANALYSIS ACTIVITY ===")
cursor.execute("""
    SELECT 
        ticker,
        buy_timestamp,
        x_analyzed_at,
        x_analysis_tier,
        substr(x_analysis_summary, 1, 100) as summary_preview
    FROM calls
    WHERE x_analyzed_at IS NOT NULL
    ORDER BY x_analyzed_at DESC
    LIMIT 10
""")
recent = cursor.fetchall()

if recent:
    print(f"\nLast 10 X analyses:")
    for row in recent:
        x_time = datetime.fromisoformat(row['x_analyzed_at'].replace('Z', '+00:00'))
        print(f"\n{row['ticker']} - {x_time.strftime('%Y-%m-%d %H:%M:%S')} - {row['x_analysis_tier']}")
        if row['summary_preview']:
            print(f"  Summary: {row['summary_preview']}...")
else:
    print("\nNo X analyses found!")

# 3. Check if X analysis stopped recently
print("\n=== X ANALYSIS TIMELINE ===")
cursor.execute("""
    SELECT 
        DATE(x_analyzed_at) as analysis_date,
        COUNT(*) as count
    FROM calls
    WHERE x_analyzed_at IS NOT NULL
    GROUP BY DATE(x_analyzed_at)
    ORDER BY analysis_date DESC
    LIMIT 7
""")
timeline = cursor.fetchall()

if timeline:
    print("\nX analyses per day (last 7 days):")
    for row in timeline:
        print(f"  {row['analysis_date']}: {row['count']} analyses")
else:
    print("\nNo X analysis timeline data found!")

# 4. Check calls that should have X analysis but don't
print("\n=== CALLS MISSING X ANALYSIS ===")
cursor.execute("""
    SELECT 
        ticker,
        buy_timestamp,
        analyzed_at,
        notified,
        json_extract(raw_data, '$.token.ca') as contract_address
    FROM calls
    WHERE x_analyzed_at IS NULL
    AND analyzed_at IS NOT NULL
    AND json_extract(raw_data, '$.token.ca') IS NOT NULL
    ORDER BY buy_timestamp DESC
    LIMIT 10
""")
missing = cursor.fetchall()

print(f"\nCalls with Claude analysis but no X analysis (showing last 10):")
for row in missing:
    buy_time = datetime.fromtimestamp(row['buy_timestamp'] / 1000)
    print(f"  {row['ticker']} - {buy_time.strftime('%Y-%m-%d %H:%M')} - CA: {row['contract_address'][:20]}...")

# 5. Check most recent call timestamps
print("\n=== MOST RECENT CALLS ===")
cursor.execute("""
    SELECT 
        ticker,
        buy_timestamp,
        analyzed_at,
        x_analyzed_at,
        notified
    FROM calls
    ORDER BY buy_timestamp DESC
    LIMIT 5
""")
most_recent = cursor.fetchall()

for row in most_recent:
    buy_time = datetime.fromtimestamp(row['buy_timestamp'] / 1000)
    print(f"\n{row['ticker']} - {buy_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Claude analyzed: {'Yes' if row['analyzed_at'] else 'No'}")
    print(f"  X analyzed: {'Yes' if row['x_analyzed_at'] else 'No'}")
    print(f"  Notified: {'Yes' if row['notified'] else 'No'}")

conn.close()