#!/usr/bin/env python3
"""Test the exact flow of download_krom_calls"""

import os
import sys
import sqlite3
import requests
from dotenv import load_dotenv

load_dotenv()

# Test what happens in download_krom_calls
def test_download_flow():
    # Simulate get_krom_calls return value
    mock_krom_result = {
        "success": True,
        "data": {
            "calls": [
                {
                    "id": "test123",
                    "ticker": "BTC",
                    "name": "Bitcoin", 
                    "contract": "0x123",
                    "network": "ethereum",
                    "market_cap": 1000000,
                    "buy_price": 50000,
                    "top_price": 60000,
                    "current_price": 55000,
                    "roi": 1.1,
                    "profit_percent": 10.0,
                    "status": "profit",
                    "call_timestamp": "2024-01-01T00:00:00Z",
                    "group": {
                        "name": "Test Group",
                        "win_rate_30d": 80,
                        "profit_30d": 100,
                        "total_calls": 50,
                        "call_frequency": 5
                    },
                    "message": "Test message",
                    "image_url": "http://example.com/image.png"
                }
            ],
            "summary": {
                "total": 1,
                "profitable": 1,
                "win_rate": 100.0,
                "average_roi": 1.1
            }
        }
    }
    
    # Extract calls the same way download_krom_calls does
    data = mock_krom_result.get("data", {})
    print(f"data type: {type(data)}")
    print(f"data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
    
    calls_data = data.get("calls", []) if isinstance(data, dict) else data
    print(f"calls_data type: {type(calls_data)}")
    print(f"calls_data length: {len(calls_data)}")
    
    if calls_data:
        first_call = calls_data[0]
        print(f"First call type: {type(first_call)}")
        print(f"First call id: {first_call.get('id')}")
        print("This should work fine!")

print("Testing download flow...")
test_download_flow()