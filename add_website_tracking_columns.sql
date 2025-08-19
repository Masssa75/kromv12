-- Add columns to track website checking history and patterns
-- Run this against Supabase to enable smart re-checking

-- Track how many times we've checked for a website
ALTER TABLE token_discovery 
ADD COLUMN IF NOT EXISTS website_check_count INTEGER DEFAULT 0;

-- Track when to check next (for efficient scheduling)
ALTER TABLE token_discovery 
ADD COLUMN IF NOT EXISTS next_check_at TIMESTAMPTZ;

-- Track when website was first discovered (to measure time from launch)
ALTER TABLE token_discovery 
ADD COLUMN IF NOT EXISTS website_found_at TIMESTAMPTZ;

-- Track the last check attempt (even if no website found)
ALTER TABLE token_discovery 
ADD COLUMN IF NOT EXISTS last_check_at TIMESTAMPTZ;

-- Add index for efficient querying of tokens that need checking
CREATE INDEX IF NOT EXISTS idx_token_discovery_next_check 
ON token_discovery(next_check_at) 
WHERE next_check_at IS NOT NULL;

-- Add index for tokens without websites that still need checking
CREATE INDEX IF NOT EXISTS idx_token_discovery_needs_website_check
ON token_discovery(website_url, next_check_at)
WHERE website_url IS NULL AND next_check_at IS NOT NULL;