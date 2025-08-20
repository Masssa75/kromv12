#!/usr/bin/env python3
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("Cleaning up old gecko_trending tokens with NULL values...")

# Delete all gecko_trending tokens
result = supabase.table('crypto_calls').delete().eq('source', 'gecko_trending').execute()

print(f"Deleted {len(result.data)} gecko_trending tokens")

# Now let's run the gecko trending function to get fresh data
print("\nTokens cleaned up. Run the orchestrator to fetch fresh trending tokens with proper data.")