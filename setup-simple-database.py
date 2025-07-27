#!/usr/bin/env python3
"""
Setup simple KROM database with single calls table
"""

import sqlite3
import os

def create_database():
    """Create the simple database structure"""
    # Remove old database if exists
    if os.path.exists('krom_calls.db'):
        print("Removing old database...")
        os.remove('krom_calls.db')
    
    # Create new database
    print("Creating new database...")
    conn = sqlite3.connect('krom_calls.db')
    cursor = conn.cursor()
    
    # Read and execute SQL schema
    with open('create-simple-database.sql', 'r') as f:
        sql = f.read()
        cursor.executescript(sql)
    
    conn.commit()
    
    # Verify table was created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"\nTables created: {[t[0] for t in tables]}")
    
    # Show table structure
    cursor.execute("PRAGMA table_info(calls);")
    columns = cursor.fetchall()
    print("\nCalls table structure:")
    for col in columns:
        print(f"  {col[1]:20} {col[2]:10}")
    
    conn.close()
    print("\n✅ Database setup complete!")

if __name__ == "__main__":
    create_database()