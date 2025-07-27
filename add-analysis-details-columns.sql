-- Add detailed analysis columns to crypto_calls table
-- These columns will store the full AI analysis details and batch information

-- Add columns for storing full analysis details
ALTER TABLE crypto_calls 
ADD COLUMN IF NOT EXISTS analysis_reasoning TEXT,
ADD COLUMN IF NOT EXISTS analysis_batch_id UUID,
ADD COLUMN IF NOT EXISTS analysis_batch_timestamp TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS analysis_prompt_used TEXT,
ADD COLUMN IF NOT EXISTS analysis_duration_ms INTEGER,
ADD COLUMN IF NOT EXISTS analysis_confidence DECIMAL(3,2) CHECK (analysis_confidence >= 0 AND analysis_confidence <= 1);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_analysis_batch_id ON crypto_calls(analysis_batch_id);
CREATE INDEX IF NOT EXISTS idx_analysis_batch_timestamp ON crypto_calls(analysis_batch_timestamp);

-- Add comments for documentation
COMMENT ON COLUMN crypto_calls.analysis_reasoning IS 'Full AI reasoning/explanation for the analysis score';
COMMENT ON COLUMN crypto_calls.analysis_batch_id IS 'UUID identifying which batch this call was analyzed in';
COMMENT ON COLUMN crypto_calls.analysis_batch_timestamp IS 'Timestamp when this batch of calls was analyzed';
COMMENT ON COLUMN crypto_calls.analysis_prompt_used IS 'Exact prompt sent to the AI model for analysis';
COMMENT ON COLUMN crypto_calls.analysis_duration_ms IS 'Time taken for AI analysis in milliseconds';
COMMENT ON COLUMN crypto_calls.analysis_confidence IS 'AI confidence level (0-1) if provided by the model';

-- Query to check if migration was successful
-- SELECT 
--     column_name, 
--     data_type, 
--     is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'crypto_calls' 
-- AND column_name LIKE 'analysis_%'
-- ORDER BY column_name;