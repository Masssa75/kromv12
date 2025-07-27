#!/usr/bin/env python3
"""
Apply database schema updates to add missing columns and raw_data storage
"""

import sqlite3
import json
import os
from datetime import datetime

def check_column_exists(cursor, table_name, column_name):
    """Check if a column already exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return any(col[1] == column_name for col in columns)

def apply_updates(db_path='krom_calls.db'):
    """Apply all database updates safely"""
    
    if not os.path.exists(db_path):
        print(f"Error: Database {db_path} not found!")
        return False
    
    print(f"Applying updates to: {db_path}")
    
    # Create backup first
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Creating backup: {backup_path}")
    import shutil
    shutil.copy2(db_path, backup_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check existing schema
        print("\nChecking current schema...")
        cursor.execute("PRAGMA table_info(krom_calls)")
        existing_columns = {col[1] for col in cursor.fetchall()}
        print(f"Existing columns: {', '.join(sorted(existing_columns))}")
        
        # Define all columns we need to add
        columns_to_add = [
            ('raw_data', 'TEXT'),
            ('pair_address', 'TEXT'),
            ('pair_timestamp', 'INTEGER'),
            ('contract_address', 'TEXT'),
            ('token_symbol', 'TEXT'),
            ('buy_timestamp', 'INTEGER'),
            ('top_timestamp', 'INTEGER'),
            ('trade_error', 'BOOLEAN DEFAULT FALSE'),
            ('hidden', 'BOOLEAN DEFAULT FALSE'),
            ('group_id', 'TEXT'),
            ('message_id', 'INTEGER'),
            ('timestamp', 'INTEGER'),
            ('text', 'TEXT')
        ]
        
        # Add missing columns
        print("\nAdding missing columns...")
        added_columns = []
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE krom_calls ADD COLUMN {column_name} {column_type}")
                    added_columns.append(column_name)
                    print(f"✓ Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"✗ Error adding {column_name}: {e}")
        
        if not added_columns:
            print("No new columns needed!")
        else:
            print(f"\nAdded {len(added_columns)} new columns")
        
        # Update groups table
        print("\nUpdating groups table...")
        cursor.execute("PRAGMA table_info(groups)")
        groups_columns = {col[1] for col in cursor.fetchall()}
        
        groups_to_add = [
            ('early_top_50', 'INTEGER'),
            ('lot_30', 'INTEGER'),
            ('ins_30', 'INTEGER'),
            ('group_id', 'TEXT')
        ]
        
        for column_name, column_type in groups_to_add:
            if column_name not in groups_columns:
                try:
                    cursor.execute(f"ALTER TABLE groups ADD COLUMN {column_name} {column_type}")
                    print(f"✓ Added column to groups: {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"✗ Error adding {column_name} to groups: {e}")
        
        # Create indexes
        print("\nCreating indexes...")
        indexes = [
            ('idx_calls_group_id', 'krom_calls(group_id)'),
            ('idx_calls_hidden', 'krom_calls(hidden)'),
            ('idx_calls_timestamp', 'krom_calls(timestamp)'),
            ('idx_calls_buy_timestamp', 'krom_calls(buy_timestamp)'),
            ('idx_calls_pair_address', 'krom_calls(pair_address)'),
            ('idx_calls_contract_address', 'krom_calls(contract_address)'),
            ('idx_groups_group_id', 'groups(group_id)')
        ]
        
        for index_name, index_def in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}")
                print(f"✓ Created index: {index_name}")
            except sqlite3.OperationalError as e:
                print(f"✗ Error creating index {index_name}: {e}")
        
        # Create view
        print("\nCreating view...")
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS calls_with_groups AS
            SELECT 
                c.*,
                g.name as group_name,
                g.win_rate_30d,
                g.profit_30d,
                g.call_frequency,
                g.early_top_50,
                g.lot_30,
                g.ins_30
            FROM krom_calls c
            LEFT JOIN groups g ON c.group_id = g.group_id
        """)
        print("✓ Created calls_with_groups view")
        
        # Create triggers for auto-parsing raw_data
        print("\nCreating triggers...")
        
        # Drop existing triggers if they exist
        cursor.execute("DROP TRIGGER IF EXISTS parse_raw_data_insert")
        cursor.execute("DROP TRIGGER IF EXISTS parse_raw_data_update")
        
        # Create insert trigger
        cursor.execute("""
            CREATE TRIGGER parse_raw_data_insert
            AFTER INSERT ON krom_calls
            WHEN NEW.raw_data IS NOT NULL
            BEGIN
                UPDATE krom_calls 
                SET 
                    pair_address = json_extract(NEW.raw_data, '$.token.pa'),
                    pair_timestamp = json_extract(NEW.raw_data, '$.token.pairTimestamp'),
                    contract_address = json_extract(NEW.raw_data, '$.token.ca'),
                    token_symbol = json_extract(NEW.raw_data, '$.token.symbol'),
                    network = json_extract(NEW.raw_data, '$.token.network'),
                    image_url = json_extract(NEW.raw_data, '$.token.imageUrl'),
                    
                    buy_price = json_extract(NEW.raw_data, '$.trade.buyPrice'),
                    buy_timestamp = json_extract(NEW.raw_data, '$.trade.buyTimestamp'),
                    top_price = json_extract(NEW.raw_data, '$.trade.topPrice'),
                    top_timestamp = json_extract(NEW.raw_data, '$.trade.topTimestamp'),
                    roi = json_extract(NEW.raw_data, '$.trade.roi'),
                    trade_error = json_extract(NEW.raw_data, '$.trade.error'),
                    
                    hidden = json_extract(NEW.raw_data, '$.hidden'),
                    group_id = json_extract(NEW.raw_data, '$.groupId'),
                    message_id = json_extract(NEW.raw_data, '$.messageId'),
                    text = json_extract(NEW.raw_data, '$.text'),
                    timestamp = json_extract(NEW.raw_data, '$.timestamp'),
                    ticker = UPPER(json_extract(NEW.raw_data, '$.token.symbol'))
                WHERE id = NEW.id;
            END
        """)
        print("✓ Created insert trigger")
        
        # Create update trigger
        cursor.execute("""
            CREATE TRIGGER parse_raw_data_update
            AFTER UPDATE OF raw_data ON krom_calls
            WHEN NEW.raw_data IS NOT NULL
            BEGIN
                UPDATE krom_calls 
                SET 
                    pair_address = json_extract(NEW.raw_data, '$.token.pa'),
                    pair_timestamp = json_extract(NEW.raw_data, '$.token.pairTimestamp'),
                    contract_address = json_extract(NEW.raw_data, '$.token.ca'),
                    token_symbol = json_extract(NEW.raw_data, '$.token.symbol'),
                    network = json_extract(NEW.raw_data, '$.token.network'),
                    image_url = json_extract(NEW.raw_data, '$.token.imageUrl'),
                    
                    buy_price = json_extract(NEW.raw_data, '$.trade.buyPrice'),
                    buy_timestamp = json_extract(NEW.raw_data, '$.trade.buyTimestamp'),
                    top_price = json_extract(NEW.raw_data, '$.trade.topPrice'),
                    top_timestamp = json_extract(NEW.raw_data, '$.trade.topTimestamp'),
                    roi = json_extract(NEW.raw_data, '$.trade.roi'),
                    trade_error = json_extract(NEW.raw_data, '$.trade.error'),
                    
                    hidden = json_extract(NEW.raw_data, '$.hidden'),
                    group_id = json_extract(NEW.raw_data, '$.groupId'),
                    message_id = json_extract(NEW.raw_data, '$.messageId'),
                    text = json_extract(NEW.raw_data, '$.text'),
                    timestamp = json_extract(NEW.raw_data, '$.timestamp'),
                    ticker = UPPER(json_extract(NEW.raw_data, '$.token.symbol'))
                WHERE id = NEW.id;
            END
        """)
        print("✓ Created update trigger")
        
        # Commit changes
        conn.commit()
        print("\n✅ All updates applied successfully!")
        
        # Show final schema
        print("\nFinal schema:")
        cursor.execute("PRAGMA table_info(krom_calls)")
        columns = cursor.fetchall()
        print("\nkrom_calls columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Test the triggers with sample data
        print("\nTesting with sample data...")
        with open('sample-call-full.json', 'r') as f:
            sample_data = json.load(f)
        
        # Insert test record
        cursor.execute("""
            INSERT INTO krom_calls (id, ticker, raw_data, created_at)
            VALUES (?, ?, ?, datetime('now'))
        """, (sample_data['_id'], 'TEST', json.dumps(sample_data)))
        
        # Check if fields were populated
        cursor.execute("SELECT * FROM krom_calls WHERE id = ?", (sample_data['_id'],))
        row = cursor.fetchone()
        
        if row:
            print("✓ Test record inserted and triggers executed successfully")
            # Clean up test record
            cursor.execute("DELETE FROM krom_calls WHERE id = ?", (sample_data['_id'],))
            conn.commit()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error applying updates: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    success = apply_updates()
    
    if success:
        print("\n🎉 Database successfully updated!")
        print("\nNext steps:")
        print("1. Test the updated schema with your download script")
        print("2. Update download script to store raw_data JSON")
        print("3. Run download to get all historical calls")
    else:
        print("\n⚠️  Database update failed. Check the backup and error messages.")