#!/usr/bin/env python3
"""
Test what ROI values are being shown for gecko_trending tokens
and simulate how they display in the UI.
"""

import os
from supabase import create_client
from dotenv import load_dotenv
import math

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, service_key)

def format_roi(roi):
    """Simulate the JavaScript formatROI function"""
    if roi is None:
        return '-'
    prefix = '+' if roi >= 0 else ''
    # JavaScript Math.round() behavior
    rounded = round(roi)
    return f"{prefix}{rounded}%"

try:
    # Get gecko_trending tokens
    response = supabase.table("crypto_calls").select(
        "ticker, roi_percent, price_at_call, current_price"
    ).eq("source", "gecko_trending").execute()
    
    if response.data:
        print("GeckoTerminal Tokens ROI Display Test:\n")
        print(f"{'Ticker':<8} {'ROI Value':<20} {'UI Display':<12} {'Status'}")
        print("-" * 60)
        
        for token in response.data:
            roi = token['roi_percent'] if token['roi_percent'] is not None else None
            ui_display = format_roi(roi)
            
            # Determine status
            if roi is None:
                status = "❌ NULL (shows dash)"
            elif abs(roi) < 0.5:
                status = "⚠️ Rounds to 0%"
            else:
                status = "✅ Shows percentage"
            
            roi_str = f"{roi:.6f}%" if roi is not None else "NULL"
            print(f"{token['ticker']:<8} {roi_str:<20} {ui_display:<12} {status}")
        
        print("\n📊 Summary:")
        print("- Values < 0.5% round to 0% in UI")
        print("- NULL values show as '-' (dash)")
        print("- Most gecko_trending tokens show '+0%' instead of actual ROI")
        
except Exception as e:
    print(f"❌ Error: {e}")