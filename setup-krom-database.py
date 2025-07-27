#!/usr/bin/env python3
"""
Setup SQLite database for KROM calls storage and analysis
"""

import sqlite3
import os
from datetime import datetime

def create_database():
    """Create SQLite database with KROM calls schema"""
    db_path = 'krom_calls.db'
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)
    
    # Create new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create main calls table
    cursor.execute('''
        CREATE TABLE krom_calls (
            id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            name TEXT,
            contract TEXT,
            network TEXT,
            market_cap REAL,
            buy_price REAL,
            top_price REAL,
            current_price REAL,
            roi REAL,
            profit_percent REAL,
            status TEXT,
            call_timestamp TEXT,
            message TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create groups table
    cursor.execute('''
        CREATE TABLE groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            win_rate_30d REAL,
            profit_30d REAL,
            total_calls INTEGER,
            call_frequency REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create call_groups junction table
    cursor.execute('''
        CREATE TABLE call_groups (
            call_id TEXT,
            group_id INTEGER,
            PRIMARY KEY (call_id, group_id),
            FOREIGN KEY (call_id) REFERENCES krom_calls(id),
            FOREIGN KEY (group_id) REFERENCES groups(id)
        )
    ''')
    
    # Create analysis results table
    cursor.execute('''
        CREATE TABLE call_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT,
            analysis_type TEXT,
            result TEXT,
            score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (call_id) REFERENCES krom_calls(id)
        )
    ''')
    
    # Create indices for better query performance
    cursor.execute('CREATE INDEX idx_calls_timestamp ON krom_calls(call_timestamp)')
    cursor.execute('CREATE INDEX idx_calls_ticker ON krom_calls(ticker)')
    cursor.execute('CREATE INDEX idx_calls_roi ON krom_calls(roi)')
    cursor.execute('CREATE INDEX idx_calls_status ON krom_calls(status)')
    cursor.execute('CREATE INDEX idx_groups_name ON groups(name)')
    cursor.execute('CREATE INDEX idx_analysis_call ON call_analysis(call_id)')
    
    # Create triggers to update updated_at timestamps
    cursor.execute('''
        CREATE TRIGGER update_calls_timestamp 
        AFTER UPDATE ON krom_calls
        BEGIN
            UPDATE krom_calls SET updated_at = CURRENT_TIMESTAMP 
            WHERE id = NEW.id;
        END
    ''')
    
    cursor.execute('''
        CREATE TRIGGER update_groups_timestamp 
        AFTER UPDATE ON groups
        BEGIN
            UPDATE groups SET updated_at = CURRENT_TIMESTAMP 
            WHERE id = NEW.id;
        END
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"Database created successfully: {db_path}")
    print("\nTables created:")
    print("- krom_calls: Main calls data")
    print("- groups: Caller groups information")
    print("- call_groups: Links calls to groups")
    print("- call_analysis: Stores analysis results")

if __name__ == "__main__":
    create_database()