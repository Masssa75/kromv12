-- Website analysis columns for crypto_calls table
ALTER TABLE crypto_calls 
ADD COLUMN IF NOT EXISTS website_analyzed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS website_score INTEGER CHECK (website_score >= 0 AND website_score <= 21),
ADD COLUMN IF NOT EXISTS website_tier TEXT CHECK (website_tier IN ('HIGH', 'MEDIUM', 'LOW')),
ADD COLUMN IF NOT EXISTS website_parsed_content JSONB, -- Full parsed website data
ADD COLUMN IF NOT EXISTS website_category_scores JSONB, -- 7 category scores
ADD COLUMN IF NOT EXISTS website_stage2_qualified BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS website_auto_qualifiers JSONB, -- Array of exceptional signals
ADD COLUMN IF NOT EXISTS website_analysis_reasoning TEXT,
ADD COLUMN IF NOT EXISTS website_analyzed_at TIMESTAMPTZ;

-- Create index for quick filtering
CREATE INDEX IF NOT EXISTS idx_crypto_calls_website_score ON crypto_calls(website_score);
CREATE INDEX IF NOT EXISTS idx_crypto_calls_website_analyzed ON crypto_calls(website_analyzed);
CREATE INDEX IF NOT EXISTS idx_crypto_calls_website_tier ON crypto_calls(website_tier);
