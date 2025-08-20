import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

# Get WEEJ details
response = supabase.table("crypto_calls") \
    .select("*") \
    .eq("ticker", "WEEJ") \
    .single() \
    .execute()

token = response.data
print("WEEJ Token Analysis:")
print("="*40)
print(f"Ticker: {token['ticker']}")
print(f"Analysis Score: {token.get('analysis_score', 'N/A')}")
print(f"Current Price: {token.get('current_price', 'N/A')}")
print(f"ROI: {token.get('roi_percent', 'N/A')}")
print(f"ATH ROI: {token.get('ath_roi_percent', 'N/A')}")
print(f"Liquidity: ${token.get('liquidity_usd', 0)}")
print(f"Market Cap: ${token.get('current_market_cap', 0)}")
print()

# Check if it would be excluded by the rug filter
ath_roi = token.get("ath_roi_percent")
roi = token.get("roi_percent")
liquidity = token.get("liquidity_usd") or 0
market_cap = token.get("current_market_cap") or 0

print("Rug Filter Analysis:")
print("-"*40)

# The filter logic from the API: excludes tokens that meet ALL these conditions
conditions = []
if ath_roi is None or ath_roi < 20:
    conditions.append(f"ATH ROI ({ath_roi}) < 20% or None ✓")
else:
    conditions.append(f"ATH ROI ({ath_roi}) >= 20% ✗")

if roi is None or roi < -75:
    conditions.append(f"ROI ({roi}) < -75% or None ✓")
else:
    conditions.append(f"ROI ({roi}) >= -75% ✗")

if liquidity < 50000 and market_cap < 50000:
    conditions.append(f"Liquidity (${liquidity}) AND Market Cap (${market_cap}) < $50K ✓")
else:
    conditions.append(f"Liquidity (${liquidity}) OR Market Cap (${market_cap}) >= $50K ✗")

for condition in conditions:
    print(f"  {condition}")

all_conditions_met = (
    (ath_roi is None or ath_roi < 20) and
    (roi is None or roi < -75) and
    (liquidity < 50000 and market_cap < 50000)
)

print()
if all_conditions_met:
    print("🚫 WEEJ IS EXCLUDED by the default 'Exclude Rugs' filter")
    print("   All 3 conditions are met - token appears to be a rug")
else:
    print("✅ WEEJ SHOULD BE VISIBLE (not excluded by rug filter)")
    print("   Not all conditions are met")

print()
print("Solution: To see WEEJ in the UI:")
print("  1. Uncheck 'Exclude Rugs' filter in the sidebar")  
print("  2. Or search for 'WEEJ' directly (which works)")
print("  3. Or wait for price/liquidity data to be populated")