import os
import sys
sys.path.append('/Users/marcschwyn/Desktop/projects/KROMV12')
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv('/Users/marcschwyn/Desktop/projects/KROMV12/.env')

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

supabase = create_client(supabase_url, supabase_key)

# Get one row to see columns
result = supabase.table('crypto_calls').select('*').limit(1).execute()

if result.data:
    print("Available columns:")
    for key in result.data[0].keys():
        print(f"  - {key}")
else:
    print("No data found")
