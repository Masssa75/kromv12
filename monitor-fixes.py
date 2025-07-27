#!/usr/bin/env python3
"""
Monitor Claude's fixes to the code
Shows what files are being changed and test results
"""

import time
import os
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import requests

class FixMonitor(FileSystemEventHandler):
    def __init__(self):
        self.changes = []
        self.last_test_result = None
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Only track Python files
        if event.src_path.endswith('.py'):
            # Ignore monitoring scripts
            if any(x in event.src_path for x in ['monitor-', 'auto-', 'test-']):
                return
                
            timestamp = datetime.now().strftime('%H:%M:%S')
            filename = os.path.basename(event.src_path)
            self.changes.append(f"{timestamp} - Modified: {filename}")
            
            # Keep only last 10 changes
            if len(self.changes) > 10:
                self.changes.pop(0)
    
    def test_viz(self):
        """Quick test of visualization"""
        try:
            url = "http://localhost:5001/api/chat"
            response = requests.post(url, json={
                "message": "Create a simple bar chart showing the top 10 groups by average ROI",
                "session_id": "monitor_test"
            }, timeout=10)
            
            data = response.json()
            return {
                'working': 'visualization' in data,
                'tools_used': len(data.get('tools_used', [])) > 0,
                'has_json': '```json' in data.get('response', '')
            }
        except:
            return {'working': False, 'tools_used': False, 'has_json': False}
    
    def display_status(self):
        """Display current status"""
        while True:
            # Clear screen (simple version)
            print("\n" * 2)
            print("="*70)
            print("CLAUDE'S FIX MONITOR - VISUALIZATION STATUS")
            print("="*70)
            
            # Test current state
            test = self.test_viz()
            
            # Show test results
            print("\n📊 VISUALIZATION TEST:")
            if test['working']:
                print("✅ WORKING! Visualization data is being returned!")
            else:
                print("❌ Not working yet")
                print(f"   - JSON blocks found: {'✅' if test['has_json'] else '❌'}")
                print(f"   - Tools executed: {'✅' if test['tools_used'] else '❌'}")
            
            # Show recent changes
            print("\n📝 RECENT CODE CHANGES:")
            if self.changes:
                for change in self.changes[-5:]:  # Show last 5
                    print(f"   {change}")
            else:
                print("   No changes yet...")
            
            print("\n" + "-"*70)
            print("Monitoring... (Updates every 5 seconds)")
            
            time.sleep(5)

def main():
    print("Starting Fix Monitor...")
    print("This will show you what Claude is changing and whether it's working")
    
    monitor = FixMonitor()
    
    # Set up file watcher
    observer = Observer()
    observer.schedule(monitor, path='.', recursive=False)
    observer.start()
    
    try:
        monitor.display_status()
    except KeyboardInterrupt:
        print("\n\nStopping monitor...")
        observer.stop()
    
    observer.join()

if __name__ == "__main__":
    main()