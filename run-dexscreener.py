#!/usr/bin/env python3
import subprocess
import sys

try:
    # Try to run the dexscreener-explore.py script
    result = subprocess.run([sys.executable, 'dexscreener-explore.py'], 
                          capture_output=True, 
                          text=True,
                          cwd='/Users/marcschwyn/Desktop/projects/KROMV12')
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr)
        
except Exception as e:
    print(f"Error running script: {e}")