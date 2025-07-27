#!/usr/bin/env python3
"""Simple database explorer without dependencies"""

import sqlite3

# Connect to database
conn = sqlite3.connect('krom_calls.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== DATABASE OVERVIEW ===\n")

# Count calls
cursor.execute("SELECT COUNT(*) as count FROM krom_calls")
total_calls = cursor.fetchone()['count']
print(f"Total calls: {total_calls}")

# Win rate stats
cursor.execute("""
    SELECT 
        COUNT(CASE WHEN status = 'profit' THEN 1 END) as wins,
        COUNT(*) as total,
        ROUND(AVG(roi), 2) as avg_roi,
        ROUND(MAX(roi), 2) as max_roi,
        ROUND(MIN(roi), 2) as min_roi
    FROM krom_calls
""")
stats = cursor.fetchone()
print(f"Win rate: {stats['wins'] / stats['total'] * 100:.1f}%")
print(f"Average ROI: {stats['avg_roi']}x")
print(f"Max ROI: {stats['max_roi']}x")
print(f"Min ROI: {stats['min_roi']}x")

# Top performers
print("\n=== TOP 10 PERFORMERS ===")
print(f"{'Ticker':<10} {'Name':<30} {'ROI':<8} {'Profit %':<10} {'Date'}")
print("-" * 75)
cursor.execute("""
    SELECT ticker, name, roi, profit_percent, date(call_timestamp) as call_date
    FROM krom_calls
    ORDER BY roi DESC
    LIMIT 10
""")
for row in cursor.fetchall():
    name = row['name'][:30] if row['name'] else 'N/A'
    print(f"{row['ticker']:<10} {name:<30} {row['roi']:<8.2f} {row['profit_percent']:<10.1f} {row['call_date']}")

# Recent calls
print("\n=== MOST RECENT 5 CALLS ===")
print(f"{'Ticker':<10} {'ROI':<8} {'Status':<10} {'Date'}")
print("-" * 40)
cursor.execute("""
    SELECT ticker, roi, status, date(call_timestamp) as call_date
    FROM krom_calls
    ORDER BY call_timestamp DESC
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"{row['ticker']:<10} {row['roi']:<8.2f} {row['status']:<10} {row['call_date']}")

# Network distribution
print("\n=== CALLS BY NETWORK ===")
cursor.execute("""
    SELECT network, COUNT(*) as count
    FROM krom_calls
    GROUP BY network
    ORDER BY count DESC
""")
for row in cursor.fetchall():
    print(f"{row['network']}: {row['count']} calls")

conn.close()