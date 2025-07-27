#!/usr/bin/env python3
"""
Auto-restart server when files change
This allows Claude to make fixes and see them applied automatically
"""

import subprocess
import time
import os
import sys
import signal
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ServerManager:
    def __init__(self):
        self.process = None
        self.start_server()
    
    def start_server(self):
        """Start the server process"""
        if self.process:
            self.stop_server()
        
        print(f"\n{'='*60}")
        print(f"Starting server at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # Start server in subprocess
        self.process = subprocess.Popen(
            [sys.executable, 'all-in-one-server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Give it time to start
        time.sleep(3)
        print("✅ Server started with PID:", self.process.pid)
    
    def stop_server(self):
        """Stop the server process"""
        if self.process:
            print("\n🛑 Stopping server...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            time.sleep(1)
    
    def restart_server(self):
        """Restart the server"""
        print("\n🔄 Restarting server due to file change...")
        self.stop_server()
        self.start_server()

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, server_manager):
        self.server_manager = server_manager
        self.last_restart = 0
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Only watch Python files
        if event.src_path.endswith('.py'):
            # Ignore this script and test scripts
            if 'auto-' in event.src_path or 'test-' in event.src_path or 'monitor-' in event.src_path:
                return
            
            # Debounce - don't restart more than once per 2 seconds
            current_time = time.time()
            if current_time - self.last_restart > 2:
                print(f"\n📝 Detected change in: {os.path.basename(event.src_path)}")
                self.server_manager.restart_server()
                self.last_restart = current_time

def main():
    print("🚀 Auto-restart server starting...")
    print("👀 Watching for changes to Python files")
    print("🛑 Press Ctrl+C to stop\n")
    
    # Check if watchdog is installed
    try:
        import watchdog
    except ImportError:
        print("❌ Error: watchdog not installed")
        print("Install it with: pip3 install watchdog")
        sys.exit(1)
    
    # Create server manager
    server_manager = ServerManager()
    
    # Set up file watcher
    event_handler = FileChangeHandler(server_manager)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()
    
    try:
        # Keep running and show server output
        while True:
            if server_manager.process:
                line = server_manager.process.stdout.readline()
                if line:
                    print(line.rstrip())
            else:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        observer.stop()
        server_manager.stop_server()
    
    observer.join()
    print("✅ Auto-restart server stopped")

if __name__ == "__main__":
    main()