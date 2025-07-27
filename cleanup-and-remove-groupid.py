#!/usr/bin/env python3
"""
Remove group_id column from calls table if it exists.
SQLite doesn't support DROP COLUMN, so we need to recreate the table.
"""

import sqlite3
import os
from datetime import datetime

def main():
    print("Remove group_id Column Script")
    print("=" * 60)
    
    db_path = "krom_calls.db"
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if group_id column exists
    cursor.execute("PRAGMA table_info(calls)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    if 'group_id' not in column_names:
        print("✓ group_id column doesn't exist. Database is clean!")
        return
    
    print("Found group_id column. Removing it...")
    
    # Get list of all columns EXCEPT group_id
    columns_to_keep = [col[1] for col in columns if col[1] != 'group_id']
    columns_str = ', '.join(columns_to_keep)
    
    print(f"\nColumns to keep: {len(columns_to_keep)}")
    print("Creating new table without group_id...")
    
    # Start transaction
    cursor.execute("BEGIN TRANSACTION")
    
    try:
        # Create new table without group_id
        cursor.execute(f"""
            CREATE TABLE calls_new AS 
            SELECT {columns_str}
            FROM calls
        """)
        
        # Drop old table
        cursor.execute("DROP TABLE calls")
        
        # Rename new table
        cursor.execute("ALTER TABLE calls_new RENAME TO calls")
        
        # Recreate indexes
        print("Recreating indexes...")
        cursor.execute("CREATE INDEX idx_calls_timestamp ON calls(call_timestamp)")
        cursor.execute("CREATE INDEX idx_calls_ticker ON calls(ticker)")
        cursor.execute("CREATE INDEX idx_calls_roi ON calls(roi)")
        cursor.execute("CREATE INDEX idx_calls_status ON calls(status)")
        cursor.execute("CREATE INDEX idx_calls_group_name ON calls(group_name)")
        
        # Commit transaction
        cursor.execute("COMMIT")
        print("✓ Successfully removed group_id column")
        
        # Vacuum to optimize
        print("Optimizing database...")
        cursor.execute("VACUUM")
        
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"Error: {e}")
        raise
    
    # Verify
    cursor.execute("PRAGMA table_info(calls)")
    final_columns = [col[1] for col in cursor.fetchall()]
    
    print("\nFinal columns:")
    for col in final_columns:
        print(f"  - {col}")
    
    if 'group_id' in final_columns:
        print("\n⚠️  ERROR: group_id still exists!")
    else:
        print("\n✅ group_id successfully removed!")
    
    conn.close()

if __name__ == "__main__":
    main()