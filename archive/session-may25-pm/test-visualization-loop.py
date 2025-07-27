#!/usr/bin/env python3
"""
Test visualization functionality in a loop
Run this while the server is running to debug visualization issues
"""

import requests
import json
import time
import sys

def test_visualization():
    """Test if visualization is working"""
    url = "http://localhost:5001/api/chat"
    
    # Test message that should create a visualization
    test_message = "Create a simple bar chart showing the top 10 groups by average ROI"
    
    payload = {
        "message": test_message,
        "session_id": "test_viz_debug"
    }
    
    print(f"\n{'='*60}")
    print(f"Testing at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Message: {test_message}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()
        
        print(f"\nResponse status: {response.status_code}")
        print(f"Tools used: {data.get('tools_used', [])}")
        
        # Check if visualization data exists
        if 'visualization' in data:
            print(f"✅ VISUALIZATION FOUND!")
            print(f"Type: {data['visualization'].get('type')}")
            print(f"Title: {data['visualization'].get('title')}")
            if 'data' in data['visualization']:
                viz_data = data['visualization']['data']
                if isinstance(viz_data, dict):
                    print(f"Data keys: {list(viz_data.keys())}")
                    if 'labels' in viz_data:
                        print(f"Number of labels: {len(viz_data['labels'])}")
                    if 'values' in viz_data:
                        print(f"Number of values: {len(viz_data['values'])}")
            return True
        else:
            print(f"❌ No visualization in response")
            print(f"Response keys: {list(data.keys())}")
            
            # Show part of the response for debugging
            if 'response' in data:
                resp_text = data['response']
                if '```json' in resp_text:
                    print(f"JSON block found in response")
                    # Extract and show the JSON
                    import re
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', resp_text, re.DOTALL)
                    if json_match:
                        try:
                            tool_call = json.loads(json_match.group(1))
                            print(f"Tool call found: {tool_call.get('tool', 'Unknown')}")
                        except:
                            print("Failed to parse JSON from response")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Server not running!")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("Starting visualization test loop...")
    print("Make sure the server is running on port 5001")
    print("Press Ctrl+C to stop")
    
    attempt = 0
    while True:
        attempt += 1
        print(f"\n\nAttempt #{attempt}")
        
        result = test_visualization()
        
        if result is None:
            print("\nWaiting for server to start...")
            time.sleep(5)
        elif result:
            print("\n🎉 SUCCESS! Visualization is working!")
            print("\nContinuing to monitor... Press Ctrl+C to stop")
        else:
            print("\n⚠️  Visualization not working yet")
        
        # Wait before next test
        time.sleep(10)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest loop stopped.")