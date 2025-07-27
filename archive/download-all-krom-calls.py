#!/usr/bin/env python3
"""
Download ALL KROM calls from the API and store in SQLite database
Handles pagination and large datasets efficiently
"""

import os
import sqlite3
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
KROM_API_TOKEN = os.getenv("KROM_API_TOKEN")
BATCH_SIZE = 100  # API limit per request
COMMIT_INTERVAL = 500  # Commit to DB every N calls
DB_PATH = "krom_calls.db"

def get_krom_calls_batch(before_id=None):
    """Fetch a batch of KROM calls from the API"""
    if not KROM_API_TOKEN:
        raise ValueError("KROM_API_TOKEN not found in environment")
    
    url = f"https://krom.one/api/v1/calls?limit={BATCH_SIZE}"
    if before_id:
        # Try different pagination parameters
        url += f"&before={before_id}"  # This might be the correct parameter
    
    headers = {'Authorization': f'Bearer {KROM_API_TOKEN}'}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Request error: {e}")
        return None

def process_and_store_calls(calls, conn, cursor):
    """Process and store calls in the database"""
    inserted = 0
    updated = 0
    
    for call in calls:
        try:
            # Extract data
            token = call.get("token", {})
            trade = call.get("trade", {})
            group = call.get("group", {})
            
            # Calculate values
            buy_price = trade.get("buyPrice", 0)
            top_price = trade.get("topPrice", 0)
            roi = trade.get("roi", 0)
            profit_pct = (roi - 1) * 100 if roi > 0 else 0
            
            # Check if exists
            cursor.execute("SELECT id FROM krom_calls WHERE id = ?", (call.get("id"),))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing
                cursor.execute('''
                    UPDATE krom_calls SET 
                        current_price = ?, roi = ?, profit_percent = ?, 
                        status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    trade.get("currentPrice", 0),
                    roi,
                    profit_pct,
                    "profit" if roi > 1 else "loss" if roi < 1 else "breakeven",
                    call.get("id")
                ))
                updated += 1
            else:
                # Insert new
                cursor.execute('''
                    INSERT INTO krom_calls (
                        id, ticker, name, contract, network, market_cap,
                        buy_price, top_price, current_price, roi, profit_percent,
                        status, call_timestamp, message, image_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    call.get("id"),
                    token.get("symbol", "Unknown"),
                    token.get("name", ""),
                    token.get("ca", ""),
                    token.get("network", ""),
                    token.get("marketCap", 0),
                    buy_price,
                    top_price,
                    trade.get("currentPrice", 0),
                    roi,
                    profit_pct,
                    "profit" if roi > 1 else "loss" if roi < 1 else "breakeven",
                    trade.get("buyTimestamp"),
                    call.get("text", ""),
                    token.get("imageUrl", "")
                ))
                inserted += 1
                
                # Handle group data
                group_data = call.get("group", {})
                group_name = call.get("groupName", "Unknown")
                
                if group_name and group_name != "Unknown":
                    # Insert or update group
                    cursor.execute('''
                        INSERT OR REPLACE INTO groups (
                            name, win_rate_30d, profit_30d, total_calls, call_frequency
                        ) VALUES (?, ?, ?, ?, ?)
                    ''', (
                        group_name,
                        group.get("stats", {}).get("winRate30", 0),
                        group.get("stats", {}).get("profit30", 0),
                        group.get("stats", {}).get("totalCalls", 0),
                        group.get("stats", {}).get("callFrequency", 0)
                    ))
                    
                    # Link call to group
                    cursor.execute("SELECT id FROM groups WHERE name = ?", (group_name,))
                    group_result = cursor.fetchone()
                    if group_result:
                        group_id = group_result[0]
                        cursor.execute('''
                            INSERT OR IGNORE INTO call_groups (call_id, group_id) 
                            VALUES (?, ?)
                        ''', (call.get("id"), group_id))
                        
        except Exception as e:
            print(f"Error processing call {call.get('id')}: {e}")
            continue
    
    return inserted, updated

def main():
    """Main download function"""
    print("=" * 60)
    print("KROM Calls Bulk Downloader")
    print("=" * 60)
    
    # Check database
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        print("Please run setup-krom-database.py first")
        return
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get current count
    cursor.execute("SELECT COUNT(*) FROM krom_calls")
    initial_count = cursor.fetchone()[0]
    print(f"Current database has {initial_count:,} calls")
    
    # Initialize counters
    total_processed = 0
    total_inserted = 0
    total_updated = 0
    before_timestamp = None
    oldest_timestamp = None
    batch_count = 0
    
    print("\nStarting download... (Press Ctrl+C to stop)")
    print("-" * 60)
    
    try:
        while True:
            batch_count += 1
            
            # Fetch batch
            print(f"\nBatch {batch_count}: Fetching {BATCH_SIZE} calls", end="")
            if before_timestamp:
                print(f" (before {datetime.fromtimestamp(before_timestamp).strftime('%Y-%m-%d %H:%M')})", end="")
            print("...")
            
            calls = get_krom_calls_batch(before_timestamp)
            
            if not calls:
                print("No data received. Stopping.")
                break
            
            if len(calls) == 0:
                print("No more calls to fetch. Download complete!")
                break
            
            # Process calls
            inserted, updated = process_and_store_calls(calls, conn, cursor)
            total_processed += len(calls)
            total_inserted += inserted
            total_updated += updated
            
            # Get oldest timestamp from this batch
            timestamps = []
            for call in calls:
                trade = call.get("trade", {})
                ts = trade.get("buyTimestamp")
                if ts:
                    timestamps.append(ts)
            
            if timestamps:
                oldest_timestamp = min(timestamps)
                before_timestamp = oldest_timestamp
            else:
                print("Warning: No timestamps found in batch")
                break
            
            # Print progress
            print(f"  Processed: {len(calls)} calls")
            print(f"  New: {inserted}, Updated: {updated}")
            print(f"  Total so far: {total_processed:,} processed, {total_inserted:,} new")
            
            # Commit periodically
            if total_processed % COMMIT_INTERVAL == 0:
                conn.commit()
                print("  ✓ Committed to database")
            
            # Rate limiting (be nice to the API)
            time.sleep(0.5)
            
            # Check if we got less than requested (means we're at the end)
            if len(calls) < BATCH_SIZE:
                print("\nReached end of available calls")
                break
                
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
    finally:
        # Final commit
        conn.commit()
        
        # Get final count
        cursor.execute("SELECT COUNT(*) FROM krom_calls")
        final_count = cursor.fetchone()[0]
        
        # Close database
        conn.close()
        
        # Print summary
        print("\n" + "=" * 60)
        print("DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"Total calls processed: {total_processed:,}")
        print(f"New calls inserted: {total_inserted:,}")
        print(f"Existing calls updated: {total_updated:,}")
        print(f"Database now contains: {final_count:,} calls")
        print(f"Net increase: {final_count - initial_count:,} calls")
        
        if oldest_timestamp:
            print(f"\nOldest call date reached: {datetime.fromtimestamp(oldest_timestamp).strftime('%Y-%m-%d %H:%M')}")
        
        print("\nDone!")

if __name__ == "__main__":
    main()