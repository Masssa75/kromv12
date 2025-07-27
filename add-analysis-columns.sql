-- Add columns for Claude analysis results
ALTER TABLE crypto_calls
ADD COLUMN IF NOT EXISTS analysis_tier TEXT,
ADD COLUMN IF NOT EXISTS analysis_description TEXT,
ADD COLUMN IF NOT EXISTS analyzed_at TIMESTAMPTZ;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_crypto_calls_analysis_tier ON crypto_calls(analysis_tier);
CREATE INDEX IF NOT EXISTS idx_crypto_calls_analyzed_at ON crypto_calls(analyzed_at);