#!/usr/bin/env python3
"""
Fix group storage by adding group_name column and populating it.
This eliminates the need for the separate groups table and group_id references.
"""

import sqlite3
import json
from datetime import datetime

def main():
    print("Group Storage Fix Script")
    print("=" * 60)
    
    # Connect to database
    conn = sqlite3.connect('krom_calls.db')
    cursor = conn.cursor()
    
    # 1. Add group_name column if it doesn't exist
    print("\n1. Adding group_name column to crypto_calls table...")
    try:
        cursor.execute("ALTER TABLE krom_calls ADD COLUMN group_name TEXT")
        print("   ✓ Added group_name column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("   - group_name column already exists")
        else:
            raise
    
    # 2. Count how many records need updating
    cursor.execute("SELECT COUNT(*) FROM krom_calls WHERE group_name IS NULL")
    needs_update = cursor.fetchone()[0]
    print(f"\n2. Found {needs_update:,} records that need group_name populated")
    
    if needs_update > 0:
        # 3. Populate group_name from raw_data JSON
        print("\n3. Populating group_name from raw_data...")
        
        cursor.execute("""
            SELECT id, raw_data 
            FROM krom_calls 
            WHERE raw_data IS NOT NULL AND group_name IS NULL
            LIMIT 10000
        """)
        
        batch = []
        updated = 0
        errors = 0
        
        for row in cursor.fetchall():
            call_id, raw_data = row
            try:
                data = json.loads(raw_data)
                group_name = data.get('groupName', '')
                if group_name:
                    batch.append((group_name, call_id))
                    if len(batch) >= 1000:
                        cursor.executemany(
                            "UPDATE krom_calls SET group_name = ? WHERE id = ?",
                            batch
                        )
                        updated += len(batch)
                        batch = []
                        print(f"   Updated {updated:,} records...")
            except json.JSONDecodeError:
                errors += 1
        
        # Process remaining batch
        if batch:
            cursor.executemany(
                "UPDATE krom_calls SET group_name = ? WHERE id = ?",
                batch
            )
            updated += len(batch)
        
        conn.commit()
        print(f"   ✓ Successfully updated {updated:,} records")
        if errors > 0:
            print(f"   - {errors} records had JSON decode errors")
    
    # 4. For records without raw_data, try to get group_name from groups table
    cursor.execute("""
        SELECT COUNT(*) 
        FROM krom_calls c
        WHERE c.group_name IS NULL AND c.group_id IS NOT NULL
    """)
    needs_join_update = cursor.fetchone()[0]
    
    if needs_join_update > 0:
        print(f"\n4. Found {needs_join_update:,} records that need group_name from groups table...")
        cursor.execute("""
            UPDATE krom_calls
            SET group_name = (
                SELECT g.name 
                FROM groups g 
                WHERE g.group_id = krom_calls.group_id
            )
            WHERE group_name IS NULL AND group_id IS NOT NULL
        """)
        conn.commit()
        print(f"   ✓ Updated from groups table")
    
    # 5. Create index on group_name for performance
    print("\n5. Creating index on group_name...")
    try:
        cursor.execute("CREATE INDEX idx_calls_group_name ON krom_calls(group_name)")
        print("   ✓ Created index")
    except sqlite3.OperationalError as e:
        if "already exists" in str(e):
            print("   - Index already exists")
        else:
            raise
    
    # 6. Show statistics
    print("\n6. Final Statistics:")
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(group_name) as has_group_name,
            COUNT(DISTINCT group_name) as unique_groups
        FROM krom_calls
    """)
    stats = cursor.fetchone()
    print(f"   Total calls: {stats[0]:,}")
    print(f"   Calls with group_name: {stats[1]:,}")
    print(f"   Unique groups: {stats[2]:,}")
    
    # Show sample of groups
    print("\n   Sample groups:")
    cursor.execute("""
        SELECT group_name, COUNT(*) as count
        FROM krom_calls
        WHERE group_name IS NOT NULL
        GROUP BY group_name
        ORDER BY count DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"   - {row[0]}: {row[1]:,} calls")
    
    # 7. Create trigger to auto-populate group_name from raw_data
    print("\n7. Creating trigger to auto-populate group_name...")
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS populate_group_name
        AFTER INSERT ON krom_calls
        FOR EACH ROW
        WHEN NEW.raw_data IS NOT NULL AND NEW.group_name IS NULL
        BEGIN
            UPDATE krom_calls
            SET group_name = json_extract(NEW.raw_data, '$.groupName')
            WHERE id = NEW.id;
        END;
    """)
    print("   ✓ Created trigger")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Group storage fix complete!")
    print("\nNext steps:")
    print("1. Update download scripts to store group_name directly")
    print("2. Update dashboard to use group_name instead of group_id joins")
    print("3. Consider removing the groups table and group_id column later")

if __name__ == "__main__":
    main()