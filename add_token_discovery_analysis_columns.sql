-- Add website analysis columns to token_discovery table
ALTER TABLE token_discovery 
ADD COLUMN IF NOT EXISTS website_analyzed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS website_stage1_score INTEGER CHECK (website_stage1_score >= 0 AND website_stage1_score <= 21),
ADD COLUMN IF NOT EXISTS website_stage1_tier TEXT CHECK (website_stage1_tier IN ('TRASH', 'BASIC', 'SOLID', 'ALPHA', 'ERROR')),
ADD COLUMN IF NOT EXISTS website_stage1_analysis JSONB;

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_token_discovery_website_analyzed ON token_discovery(website_analyzed_at);
CREATE INDEX IF NOT EXISTS idx_token_discovery_website_score ON token_discovery(website_stage1_score);
CREATE INDEX IF NOT EXISTS idx_token_discovery_website_tier ON token_discovery(website_stage1_tier);

-- Index for finding tokens with websites that need analysis
CREATE INDEX IF NOT EXISTS idx_token_discovery_needs_analysis 
ON token_discovery(website_url, website_analyzed_at) 
WHERE website_url IS NOT NULL AND website_analyzed_at IS NULL;

-- Index for finding high-scoring tokens
CREATE INDEX IF NOT EXISTS idx_token_discovery_high_score 
ON token_discovery(website_stage1_score) 
WHERE website_stage1_score >= 4;