-- Add notification tracking to crypto_calls table
ALTER TABLE crypto_calls 
ADD COLUMN notified BOOLEAN DEFAULT false;

-- Create index for unnotified calls
CREATE INDEX idx_crypto_calls_notified ON crypto_calls(notified);

-- Update existing records to be unnotified
UPDATE crypto_calls 
SET notified = false 
WHERE notified IS NULL;