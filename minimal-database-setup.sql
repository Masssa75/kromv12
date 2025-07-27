-- Create minimal crypto_calls table
CREATE TABLE IF NOT EXISTS crypto_calls (
    krom_id TEXT PRIMARY KEY,  -- uses the _id from KROM API
    raw_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX idx_crypto_calls_created_at ON crypto_calls(created_at);