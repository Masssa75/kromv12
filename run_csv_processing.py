#!/usr/bin/env python3
import subprocess
import sys
import os

# Change to the correct directory
os.chdir('/Users/marcschwyn/Desktop/projects/KROMV12')

# Run the CSV processing script
try:
    # Execute the script directly
    exec(open('create_tweets_only_csv.py').read())
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)