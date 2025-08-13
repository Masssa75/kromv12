-- Add website and social link columns to crypto_calls table
-- These will store the URLs fetched from DexScreener for efficient UI access

ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS website_url TEXT;
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS twitter_url TEXT;
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS telegram_url TEXT;
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS discord_url TEXT;
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS socials_fetched_at TIMESTAMPTZ;

-- Add website analysis columns for Kimi K2 analysis results
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS website_score INTEGER CHECK (website_score >= 1 AND website_score <= 10);
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS website_tier TEXT CHECK (website_tier IN ('ALPHA', 'SOLID', 'BASIC', 'TRASH'));
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS website_analysis JSONB;
ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS website_analyzed_at TIMESTAMPTZ;

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_website_url ON crypto_calls(website_url) WHERE website_url IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_socials_fetched ON crypto_calls(socials_fetched_at);
CREATE INDEX IF NOT EXISTS idx_website_analyzed ON crypto_calls(website_analyzed_at);