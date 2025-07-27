#!/usr/bin/env python3
"""
Clear all data from calls table and prepare for fresh download.
Keeps the table structure intact.
"""

import sqlite3
import os

def main():
    print("Clear and Re-download Script")
    print("=" * 60)
    
    db_path = "krom_calls.db"
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Show current status
    cursor.execute("SELECT COUNT(*) FROM calls")
    current_count = cursor.fetchone()[0]
    print(f"\nCurrent data: {current_count:,} calls")
    
    # 2. Confirm deletion
    response = input("\n⚠️  This will DELETE ALL DATA. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # 3. Delete all data
    print("\nDeleting all data...")
    cursor.execute("DELETE FROM calls")
    conn.commit()
    print("✓ All data deleted")
    
    # 4. Reset autoincrement if needed
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='calls'")
    conn.commit()
    
    # 5. Vacuum to reclaim space
    print("Optimizing database...")
    cursor.execute("VACUUM")
    print("✓ Database optimized")
    
    # 6. Verify empty
    cursor.execute("SELECT COUNT(*) FROM calls")
    final_count = cursor.fetchone()[0]
    print(f"\nFinal count: {final_count} calls")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Database cleared and ready for fresh download!")
    print("\nTo download all data, run:")
    print("   python3 download-all-calls-clean.py")

if __name__ == "__main__":
    main()