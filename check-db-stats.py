#!/usr/bin/env python3
"""Quick database statistics checker"""

import sqlite3
from datetime import datetime

conn = sqlite3.connect('krom_calls.db')
cursor = conn.cursor()

# Get stats
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        MIN(call_timestamp) as oldest,
        MAX(call_timestamp) as newest,
        COUNT(DISTINCT ticker) as unique_tokens,
        COUNT(DISTINCT network) as networks
    FROM krom_calls
""")
stats = cursor.fetchone()

print("=" * 50)
print("KROM Database Statistics")
print("=" * 50)
print(f"Total calls: {stats[0]:,}")
print(f"Unique tokens: {stats[3]:,}")
print(f"Networks: {stats[4]}")

if stats[1] and stats[2]:
    try:
        oldest = datetime.fromisoformat(stats[1].replace('Z', '+00:00'))
        newest = datetime.fromisoformat(stats[2].replace('Z', '+00:00'))
        print(f"Date range: {oldest.strftime('%Y-%m-%d')} to {newest.strftime('%Y-%m-%d')}")
        print(f"Days covered: {(newest - oldest).days}")
    except:
        print(f"Date range: {stats[1]} to {stats[2]}")

# Network breakdown
print("\nCalls by network:")
cursor.execute("""
    SELECT network, COUNT(*) as count 
    FROM krom_calls 
    GROUP BY network 
    ORDER BY count DESC
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]:,}")

conn.close()