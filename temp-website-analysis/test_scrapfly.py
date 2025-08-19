#!/usr/bin/env python3
import requests
import json
import time

def test_scrapfly(url):
    """Test ScrapFly API with a crypto website"""
    api_key = "scp-live-2beb370f43d24c00b37aeba6514659d5"
    
    api_url = "https://api.scrapfly.io/scrape"
    
    params = {
        "key": api_key,
        "url": url,
        "render_js": "true",
        "wait_for_selector": "body",
        "timeout": 30000,
        "retry": "false",
        "country": "us",
        "format": "json"
    }
    
    print(f"Testing ScrapFly with: {url}")
    start_time = time.time()
    
    try:
        response = requests.get(api_url, params=params, timeout=35)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("result", {}).get("content", "")
            print(f"✅ Success in {elapsed:.1f}s")
            print(f"Content length: {len(content)} chars")
            print(f"First 500 chars: {content[:500]}")
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Timeout after {time.time() - start_time:.1f}s")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Test with a few problematic sites from your list
    test_urls = [
        "https://www.crocodilecoin.xyz",  # Recent discovery
        "https://cabal.cx",  # Another recent one
        "https://pump.fun/coin/8bfgR8CCyFVfRMNsLzPM9GKQRMrsUCfvRSj8BSuspump"  # Pump.fun page
    ]
    
    for url in test_urls:
        print("\n" + "="*60)
        test_scrapfly(url)
        time.sleep(2)  # Be nice to the API