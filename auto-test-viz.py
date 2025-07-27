#!/usr/bin/env python3
"""
Automatically test visualization functionality
Runs continuously and shows results
"""

import requests
import json
import time
import threading
import queue

class VizTester:
    def __init__(self):
        self.test_count = 0
        self.last_result = None
        self.result_queue = queue.Queue()
        
    def test_visualization(self):
        """Test if visualization is working"""
        url = "http://localhost:5001/api/chat"
        test_message = "Create a simple bar chart showing the top 10 groups by average ROI"
        
        payload = {
            "message": test_message,
            "session_id": f"auto_test_{self.test_count}"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            data = response.json()
            
            result = {
                'success': response.status_code == 200,
                'tools_used': data.get('tools_used', []),
                'has_visualization': 'visualization' in data,
                'response_length': len(data.get('response', '')),
                'error': None
            }
            
            if result['has_visualization']:
                viz = data['visualization']
                result['viz_type'] = viz.get('type')
                result['viz_title'] = viz.get('title')
                if 'data' in viz and isinstance(viz['data'], dict):
                    result['viz_data_keys'] = list(viz['data'].keys())
            
            # Check if JSON block is in response
            if '```json' in data.get('response', ''):
                result['has_json_block'] = True
            else:
                result['has_json_block'] = False
                
            return result
            
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Server not running'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def run_test_loop(self):
        """Run tests continuously"""
        while True:
            self.test_count += 1
            result = self.test_visualization()
            result['test_num'] = self.test_count
            result['timestamp'] = time.strftime('%H:%M:%S')
            self.result_queue.put(result)
            time.sleep(10)  # Test every 10 seconds
    
    def display_results(self):
        """Display results in a nice format"""
        print("\n" + "="*60)
        print("VISUALIZATION AUTO-TESTER")
        print("="*60)
        print("Testing every 10 seconds...")
        print("Waiting for first test...\n")
        
        working_count = 0
        
        while True:
            try:
                result = self.result_queue.get(timeout=1)
                
                # Clear previous output (simple version)
                print(f"\n[Test #{result['test_num']} at {result['timestamp']}]")
                
                if result.get('error'):
                    print(f"❌ ERROR: {result['error']}")
                else:
                    print(f"✅ Server responding: YES")
                    print(f"📋 Tools used: {result['tools_used']}")
                    print(f"📝 Has JSON block: {'YES' if result.get('has_json_block') else 'NO'}")
                    
                    if result['has_visualization']:
                        working_count += 1
                        print(f"🎉 VISUALIZATION WORKING! (Count: {working_count})")
                        print(f"   Type: {result.get('viz_type')}")
                        print(f"   Title: {result.get('viz_title')}")
                        print(f"   Data keys: {result.get('viz_data_keys')}")
                    else:
                        print(f"❌ No visualization data")
                        if result['tools_used']:
                            print(f"   But tools were used: {result['tools_used']}")
                
                print("-" * 60)
                
            except queue.Empty:
                continue

def main():
    tester = VizTester()
    
    # Start test loop in background thread
    test_thread = threading.Thread(target=tester.run_test_loop, daemon=True)
    test_thread.start()
    
    # Display results in main thread
    try:
        tester.display_results()
    except KeyboardInterrupt:
        print("\n\nStopping auto-tester...")

if __name__ == "__main__":
    main()