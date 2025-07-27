#!/usr/bin/env python3
"""Quick database explorer script"""

import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('krom_calls.db')

# Get overview
print("=== DATABASE OVERVIEW ===\n")

# Count calls
total_calls = pd.read_sql("SELECT COUNT(*) as count FROM krom_calls", conn).iloc[0]['count']
print(f"Total calls: {total_calls}")

# Win rate
stats = pd.read_sql("""
    SELECT 
        COUNT(CASE WHEN status = 'profit' THEN 1 END) as wins,
        COUNT(*) as total,
        ROUND(AVG(roi), 2) as avg_roi,
        ROUND(MAX(roi), 2) as max_roi
    FROM krom_calls
""", conn)
print(f"Win rate: {stats.iloc[0]['wins'] / stats.iloc[0]['total'] * 100:.1f}%")
print(f"Average ROI: {stats.iloc[0]['avg_roi']}x")
print(f"Max ROI: {stats.iloc[0]['max_roi']}x")

# Top performers
print("\n=== TOP 10 PERFORMERS ===")
top_calls = pd.read_sql("""
    SELECT ticker, name, roi, profit_percent, call_timestamp
    FROM krom_calls
    ORDER BY roi DESC
    LIMIT 10
""", conn)
print(top_calls.to_string(index=False))

# Groups performance
print("\n=== GROUP PERFORMANCE ===")
groups = pd.read_sql("""
    SELECT 
        g.name,
        COUNT(c.id) as calls,
        ROUND(AVG(c.roi), 2) as avg_roi,
        g.win_rate_30d
    FROM groups g
    JOIN call_groups cg ON g.id = cg.group_id
    JOIN krom_calls c ON cg.call_id = c.id
    GROUP BY g.name
    ORDER BY avg_roi DESC
    LIMIT 10
""", conn)
print(groups.to_string(index=False))

conn.close()