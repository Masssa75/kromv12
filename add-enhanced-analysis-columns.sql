-- Add enhanced analysis columns to crypto_calls table

-- Call analysis enhancements
ALTER TABLE crypto_calls 
ADD COLUMN IF NOT EXISTS analysis_score INTEGER CHECK (analysis_score >= 1 AND analysis_score <= 10),
ADD COLUMN IF NOT EXISTS analysis_model TEXT,
ADD COLUMN IF NOT EXISTS analysis_legitimacy_factor TEXT,
ADD COLUMN IF NOT EXISTS analysis_reanalyzed_at TIMESTAMPTZ;

-- X/Twitter analysis enhancements  
ALTER TABLE crypto_calls
ADD COLUMN IF NOT EXISTS x_analysis_score INTEGER CHECK (x_analysis_score >= 1 AND x_analysis_score <= 10),
ADD COLUMN IF NOT EXISTS x_analysis_model TEXT,
ADD COLUMN IF NOT EXISTS x_best_tweet TEXT,
ADD COLUMN IF NOT EXISTS x_legitimacy_factor TEXT,
ADD COLUMN IF NOT EXISTS x_reanalyzed_at TIMESTAMPTZ;

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_analysis_score ON crypto_calls(analysis_score);
CREATE INDEX IF NOT EXISTS idx_x_analysis_score ON crypto_calls(x_analysis_score);
CREATE INDEX IF NOT EXISTS idx_analysis_reanalyzed ON crypto_calls(analysis_reanalyzed_at);
CREATE INDEX IF NOT EXISTS idx_x_reanalyzed ON crypto_calls(x_reanalyzed_at);

-- Comments for documentation
COMMENT ON COLUMN crypto_calls.analysis_score IS '1-10 rating: 1-3 shitcoin, 4-7 some legitimacy, 8-10 major backing';
COMMENT ON COLUMN crypto_calls.analysis_model IS 'AI model used: claude-3-haiku, gpt-4, gemini-pro, etc';
COMMENT ON COLUMN crypto_calls.analysis_legitimacy_factor IS 'Short 1-6 word summary of legitimacy factor';
COMMENT ON COLUMN crypto_calls.x_analysis_score IS '1-10 rating based on Twitter/X research';
COMMENT ON COLUMN crypto_calls.x_best_tweet IS 'Most legitimate/informative tweet from the batch';
COMMENT ON COLUMN crypto_calls.x_legitimacy_factor IS 'Short summary of X legitimacy signals';