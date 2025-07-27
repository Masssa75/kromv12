-- Add columns for X (Twitter) analysis results
ALTER TABLE crypto_calls
ADD COLUMN IF NOT EXISTS x_analysis_tier TEXT,
ADD COLUMN IF NOT EXISTS x_analysis_summary TEXT,
ADD COLUMN IF NOT EXISTS x_raw_tweets JSONB,
ADD COLUMN IF NOT EXISTS x_analyzed_at TIMESTAMPTZ;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_crypto_calls_x_analysis_tier ON crypto_calls(x_analysis_tier);
CREATE INDEX IF NOT EXISTS idx_crypto_calls_x_analyzed_at ON crypto_calls(x_analyzed_at);