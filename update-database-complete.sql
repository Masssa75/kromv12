-- Complete database schema update for KROM calls
-- This adds ALL missing fields from the KROM API response
-- Run this to upgrade existing krom_calls.db database

-- First, add the most important column: raw_data to store complete JSON
-- SQLite doesn't have native JSONB type, so we use TEXT and can use JSON functions
ALTER TABLE krom_calls ADD COLUMN raw_data TEXT;

-- Add missing token fields
ALTER TABLE krom_calls ADD COLUMN pair_address TEXT;
ALTER TABLE krom_calls ADD COLUMN pair_timestamp INTEGER;
ALTER TABLE krom_calls ADD COLUMN contract_address TEXT;  -- 'ca' field from API
ALTER TABLE krom_calls ADD COLUMN token_symbol TEXT;      -- 'symbol' field from API

-- Add missing trade fields
ALTER TABLE krom_calls ADD COLUMN buy_timestamp INTEGER;
ALTER TABLE krom_calls ADD COLUMN top_timestamp INTEGER;
ALTER TABLE krom_calls ADD COLUMN trade_error BOOLEAN DEFAULT FALSE;

-- Add missing call metadata
ALTER TABLE krom_calls ADD COLUMN hidden BOOLEAN DEFAULT FALSE;
ALTER TABLE krom_calls ADD COLUMN group_id TEXT;
ALTER TABLE krom_calls ADD COLUMN message_id INTEGER;
ALTER TABLE krom_calls ADD COLUMN timestamp INTEGER;  -- Original message timestamp
ALTER TABLE krom_calls ADD COLUMN text TEXT;         -- Full message text

-- Update groups table with missing stats fields
ALTER TABLE groups ADD COLUMN early_top_50 INTEGER;
ALTER TABLE groups ADD COLUMN lot_30 INTEGER;
ALTER TABLE groups ADD COLUMN ins_30 INTEGER;
ALTER TABLE groups ADD COLUMN group_id TEXT;

-- Create indexes for new fields for better performance
CREATE INDEX IF NOT EXISTS idx_calls_group_id ON krom_calls(group_id);
CREATE INDEX IF NOT EXISTS idx_calls_hidden ON krom_calls(hidden);
CREATE INDEX IF NOT EXISTS idx_calls_timestamp ON krom_calls(timestamp);
CREATE INDEX IF NOT EXISTS idx_calls_buy_timestamp ON krom_calls(buy_timestamp);
CREATE INDEX IF NOT EXISTS idx_calls_pair_address ON krom_calls(pair_address);
CREATE INDEX IF NOT EXISTS idx_calls_contract_address ON krom_calls(contract_address);
CREATE INDEX IF NOT EXISTS idx_groups_group_id ON groups(group_id);

-- Create a view to easily query calls with their group info
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
LEFT JOIN groups g ON c.group_id = g.group_id;

-- Add a trigger to parse and update fields from raw_data when inserted/updated
-- This ensures data consistency between raw_data and individual columns
CREATE TRIGGER IF NOT EXISTS parse_raw_data_insert
AFTER INSERT ON krom_calls
WHEN NEW.raw_data IS NOT NULL
BEGIN
    UPDATE krom_calls 
    SET 
        -- Token fields
        pair_address = json_extract(NEW.raw_data, '$.token.pa'),
        pair_timestamp = json_extract(NEW.raw_data, '$.token.pairTimestamp'),
        contract_address = json_extract(NEW.raw_data, '$.token.ca'),
        token_symbol = json_extract(NEW.raw_data, '$.token.symbol'),
        network = json_extract(NEW.raw_data, '$.token.network'),
        image_url = json_extract(NEW.raw_data, '$.token.imageUrl'),
        
        -- Trade fields
        buy_price = json_extract(NEW.raw_data, '$.trade.buyPrice'),
        buy_timestamp = json_extract(NEW.raw_data, '$.trade.buyTimestamp'),
        top_price = json_extract(NEW.raw_data, '$.trade.topPrice'),
        top_timestamp = json_extract(NEW.raw_data, '$.trade.topTimestamp'),
        roi = json_extract(NEW.raw_data, '$.trade.roi'),
        trade_error = json_extract(NEW.raw_data, '$.trade.error'),
        
        -- Call metadata
        hidden = json_extract(NEW.raw_data, '$.hidden'),
        group_id = json_extract(NEW.raw_data, '$.groupId'),
        message_id = json_extract(NEW.raw_data, '$.messageId'),
        text = json_extract(NEW.raw_data, '$.text'),
        timestamp = json_extract(NEW.raw_data, '$.timestamp'),
        ticker = UPPER(json_extract(NEW.raw_data, '$.token.symbol'))
    WHERE id = NEW.id;
END;

-- Similar trigger for updates
CREATE TRIGGER IF NOT EXISTS parse_raw_data_update
AFTER UPDATE OF raw_data ON krom_calls
WHEN NEW.raw_data IS NOT NULL
BEGIN
    UPDATE krom_calls 
    SET 
        -- Token fields
        pair_address = json_extract(NEW.raw_data, '$.token.pa'),
        pair_timestamp = json_extract(NEW.raw_data, '$.token.pairTimestamp'),
        contract_address = json_extract(NEW.raw_data, '$.token.ca'),
        token_symbol = json_extract(NEW.raw_data, '$.token.symbol'),
        network = json_extract(NEW.raw_data, '$.token.network'),
        image_url = json_extract(NEW.raw_data, '$.token.imageUrl'),
        
        -- Trade fields
        buy_price = json_extract(NEW.raw_data, '$.trade.buyPrice'),
        buy_timestamp = json_extract(NEW.raw_data, '$.trade.buyTimestamp'),
        top_price = json_extract(NEW.raw_data, '$.trade.topPrice'),
        top_timestamp = json_extract(NEW.raw_data, '$.trade.topTimestamp'),
        roi = json_extract(NEW.raw_data, '$.trade.roi'),
        trade_error = json_extract(NEW.raw_data, '$.trade.error'),
        
        -- Call metadata
        hidden = json_extract(NEW.raw_data, '$.hidden'),
        group_id = json_extract(NEW.raw_data, '$.groupId'),
        message_id = json_extract(NEW.raw_data, '$.messageId'),
        text = json_extract(NEW.raw_data, '$.text'),
        timestamp = json_extract(NEW.raw_data, '$.timestamp'),
        ticker = UPPER(json_extract(NEW.raw_data, '$.token.symbol'))
    WHERE id = NEW.id;
END;

-- Add a convenience function to get JSON data from raw_data column
-- Usage: SELECT json_extract(raw_data, '$.token.symbol') FROM krom_calls;

-- Summary of changes:
-- 1. Added raw_data column to store complete JSON response
-- 2. Added all missing fields from API response
-- 3. Created indexes for performance
-- 4. Added triggers to auto-populate fields from raw_data
-- 5. Created a view for easier querying with group data