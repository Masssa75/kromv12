import subprocess
import sys

# Run the dexscreener-signals.py script
result = subprocess.run([sys.executable, 'dexscreener-signals.py'], 
                       capture_output=True, 
                       text=True,
                       cwd='/Users/marcschwyn/Desktop/projects/KROMV12')

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)