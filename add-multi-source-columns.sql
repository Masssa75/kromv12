-- Add columns to support multiple signal sources (DexScreener, etc.)
-- Run this against Supabase using the Management API

-- Source tracking
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'krom';
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS source_id TEXT;
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS source_data JSONB;

-- Normalized fields for cross-source compatibility
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS contract_address TEXT;
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS chain TEXT;

-- Create index for efficient source filtering
CREATE INDEX IF NOT EXISTS idx_crypto_calls_source ON crypto_calls(source);
CREATE INDEX IF NOT EXISTS idx_crypto_calls_contract ON crypto_calls(contract_address);
CREATE INDEX IF NOT EXISTS idx_crypto_calls_chain ON crypto_calls(chain);

-- Update existing KROM records to populate normalized fields
UPDATE crypto_calls 
SET 
  contract_address = COALESCE(
    raw_data->'token'->>'ca',
    raw_data->'token'->>'address'
  ),
  chain = CASE 
    WHEN raw_data->'token'->>'chain' = 'ETH' THEN 'ethereum'
    WHEN raw_data->'token'->>'chain' = 'SOL' THEN 'solana'
    WHEN raw_data->'token'->>'chain' = 'ARB' THEN 'arbitrum'
    WHEN raw_data->'token'->>'chain' = 'BASE' THEN 'base'
    ELSE LOWER(raw_data->'token'->>'chain')
  END
WHERE source = 'krom' AND contract_address IS NULL;