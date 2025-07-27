#!/usr/bin/env python3
import subprocess
import sys

# Run the test script
result = subprocess.run([sys.executable, 'test-dexscreener-api.py'], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)