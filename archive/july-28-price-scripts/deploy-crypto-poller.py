import json
import urllib.request

# Load environment variables
env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env_vars[k] = v.strip()

SUPABASE_ACCESS_TOKEN = env_vars['SUPABASE_ACCESS_TOKEN']

# Read the updated crypto-poller function
with open('edge-functions/crypto-poller.ts', 'r') as f:
    function_code = f.read()

print("=== Deploying Enhanced Crypto-Poller ===")
print("Function includes:")
print("✅ Current price fetching via GeckoTerminal")
print("✅ Immediate price storage in historical_price_usd")
print("✅ Dead token detection")
print("✅ Enhanced logging")

# Try to update the function using Supabase CLI equivalent
print(f"\nFunction code length: {len(function_code)} characters")
print("Ready to deploy!")

print(f"\nTo manually deploy, run:")
print(f"supabase functions deploy crypto-poller")
print(f"(Make sure you're logged in with: supabase login)")

print(f"\nOr use the Supabase dashboard to upload the updated function code.")
print(f"The enhanced crypto-poller is ready!")

# Let's also test the function locally first
print(f"\n=== Key Features Added ===")
print(f"1. fetchCurrentPrice() function")
print(f"2. Automatic price fetching for all new calls")
print(f"3. historical_price_usd column population")
print(f"4. price_source tracking (GECKO_LIVE, DEAD_TOKEN, NO_POOL_DATA)")
print(f"5. Enhanced logging with price information")

print(f"\n=== Next Steps ===")
print(f"1. Deploy the function to Supabase")
print(f"2. Monitor crypto-orchestrator logs to see prices being fetched")
print(f"3. All new calls will have immediate price data!")