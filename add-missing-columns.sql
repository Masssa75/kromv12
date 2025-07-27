-- Add missing columns to capture ALL data from KROM API
-- Run this to upgrade existing database

-- Add missing token fields
ALTER TABLE krom_calls ADD COLUMN pair_address TEXT;
ALTER TABLE krom_calls ADD COLUMN pair_timestamp INTEGER;

-- Add missing trade fields  
ALTER TABLE krom_calls ADD COLUMN top_timestamp INTEGER;
ALTER TABLE krom_calls ADD COLUMN trade_error BOOLEAN DEFAULT FALSE;
ALTER TABLE krom_calls ADD COLUMN current_roi REAL;

-- Add missing call metadata
ALTER TABLE krom_calls ADD COLUMN hidden BOOLEAN DEFAULT FALSE;
ALTER TABLE krom_calls ADD COLUMN group_id TEXT;
ALTER TABLE krom_calls ADD COLUMN message_id INTEGER;
ALTER TABLE krom_calls ADD COLUMN timestamp INTEGER;  -- Original message timestamp
ALTER TABLE krom_calls ADD COLUMN raw_data TEXT;      -- Store complete JSON for future analysis

-- Add missing group stats (update groups table)
ALTER TABLE groups ADD COLUMN early_top_50 INTEGER;
ALTER TABLE groups ADD COLUMN lot_30 INTEGER;
ALTER TABLE groups ADD COLUMN ins_30 INTEGER;
ALTER TABLE groups ADD COLUMN group_id TEXT;

-- Create index for new fields
CREATE INDEX idx_calls_group_id ON krom_calls(group_id);
CREATE INDEX idx_calls_hidden ON krom_calls(hidden);
CREATE INDEX idx_calls_timestamp ON krom_calls(timestamp);
CREATE INDEX idx_groups_group_id ON groups(group_id);