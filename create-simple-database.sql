-- Simple KROM database with single calls table
-- Stores exactly what comes from the KROM API

CREATE TABLE IF NOT EXISTS calls (
    -- Primary key (using KROM's _id)
    id TEXT PRIMARY KEY,
    
    -- Token data
    pair_address TEXT,
    pair_timestamp INTEGER,
    network TEXT,
    contract_address TEXT,
    symbol TEXT,
    image_url TEXT,
    
    -- Trade data
    buy_price REAL,
    buy_timestamp INTEGER,
    top_price REAL,
    top_timestamp INTEGER,
    roi REAL,
    trade_error BOOLEAN,
    
    -- Call metadata
    hidden BOOLEAN,
    group_id TEXT,
    group_name TEXT,  -- Direct group name, no separate table needed!
    message_id INTEGER,
    text TEXT,
    timestamp INTEGER,
    
    -- Raw JSON storage for full data
    raw_data TEXT,
    
    -- Our tracking fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for common queries
    CHECK (json_valid(raw_data))
);

-- Create indexes for performance
CREATE INDEX idx_calls_timestamp ON calls(timestamp DESC);
CREATE INDEX idx_calls_group_name ON calls(group_name);
CREATE INDEX idx_calls_network ON calls(network);
CREATE INDEX idx_calls_roi ON calls(roi DESC);
CREATE INDEX idx_calls_symbol ON calls(symbol);
CREATE INDEX idx_calls_buy_timestamp ON calls(buy_timestamp DESC);