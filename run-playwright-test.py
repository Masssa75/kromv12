#!/usr/bin/env python3
import subprocess
import sys
import os

# Change to project directory
os.chdir('/Users/marcschwyn/Desktop/projects/KROMV12')

# Run the playwright test
result = subprocess.run([sys.executable, 'playwright-test-dexscreener.py'], 
                       capture_output=True, 
                       text=True)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")