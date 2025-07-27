#!/usr/bin/env python3
"""
Clean up database to have only one 'calls' table with all data.
Creates a backup first for safety.
"""

import sqlite3
import os
import shutil
from datetime import datetime

def main():
    print("Database Cleanup Script")
    print("=" * 60)
    
    db_path = "krom_calls.db"
    
    # 1. Create backup
    print("\n1. Creating backup...")
    backup_name = f"krom_calls.db.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_name)
    print(f"   ✓ Backup created: {backup_name}")
    
    # 2. Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 3. Get current stats before cleanup
    print("\n2. Current database state:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        print(f"   - {table[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM krom_calls")
    call_count = cursor.fetchone()[0]
    print(f"\n   Total calls in krom_calls: {call_count:,}")
    
    # 4. Drop unnecessary tables and views
    print("\n3. Dropping unnecessary tables...")
    tables_to_drop = ['call_analysis', 'call_groups', 'groups', 'sqlite_sequence', 'calls_with_groups']
    
    for table in tables_to_drop:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"   ✓ Dropped table: {table}")
        except:
            # Might be a view
            try:
                cursor.execute(f"DROP VIEW IF EXISTS {table}")
                print(f"   ✓ Dropped view: {table}")
            except Exception as e:
                print(f"   - Could not drop {table}: {e}")
    
    # 5. Drop all triggers on krom_calls
    print("\n4. Dropping triggers...")
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='trigger' AND tbl_name='krom_calls'
    """)
    triggers = cursor.fetchall()
    for trigger in triggers:
        cursor.execute(f"DROP TRIGGER IF EXISTS {trigger[0]}")
        print(f"   ✓ Dropped trigger: {trigger[0]}")
    
    # 6. Rename krom_calls to calls
    print("\n5. Renaming krom_calls to calls...")
    cursor.execute("ALTER TABLE krom_calls RENAME TO calls")
    print("   ✓ Renamed table to 'calls'")
    
    # 7. Drop and recreate indexes with new table name
    print("\n6. Recreating indexes...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='calls'")
    indexes = cursor.fetchall()
    
    # Drop old indexes
    for index in indexes:
        if not index[0].startswith('sqlite_'):  # Skip SQLite internal indexes
            cursor.execute(f"DROP INDEX IF EXISTS {index[0]}")
    
    # Create new indexes
    cursor.execute("CREATE INDEX idx_calls_timestamp ON calls(call_timestamp)")
    cursor.execute("CREATE INDEX idx_calls_ticker ON calls(ticker)")
    cursor.execute("CREATE INDEX idx_calls_roi ON calls(roi)")
    cursor.execute("CREATE INDEX idx_calls_status ON calls(status)")
    cursor.execute("CREATE INDEX idx_calls_group_name ON calls(group_name)")
    print("   ✓ Created indexes")
    
    # 8. Commit changes
    conn.commit()
    
    # 9. Vacuum to clean up space
    print("\n7. Optimizing database...")
    cursor.execute("VACUUM")
    print("   ✓ Database optimized")
    
    # 10. Show final state
    print("\n8. Final database state:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        print(f"   - {table[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM calls")
    final_count = cursor.fetchone()[0]
    print(f"\n   Total calls in 'calls' table: {final_count:,}")
    
    # Show columns
    print("\n   Columns in 'calls' table:")
    cursor.execute("PRAGMA table_info(calls)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Database cleanup complete!")
    print(f"\nBackup saved as: {backup_name}")
    print("\nNext steps:")
    print("1. Update all scripts to use 'calls' table instead of 'krom_calls'")
    print("2. If you want to clear all data and re-download:")
    print("   python3 clear-and-redownload.py")

if __name__ == "__main__":
    main()