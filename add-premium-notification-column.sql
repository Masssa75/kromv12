-- Add premium notification tracking column
ALTER TABLE crypto_calls 
ADD COLUMN notified_premium BOOLEAN DEFAULT FALSE;

-- Create index for performance on premium notification queries
CREATE INDEX idx_crypto_calls_notified_premium ON crypto_calls(notified_premium) WHERE notified_premium = FALSE;