#!/bin/bash

# Run the price refresh script in the background with logging
echo "Starting price refresh process..."
echo "Check price-refresh.log for progress"

# Run Python script in background, redirect output to log file
nohup python3 -W ignore refresh-all-remaining-prices.py > price-refresh.log 2>&1 &

# Get the process ID
PID=$!
echo "Process started with PID: $PID"
echo "To check progress: tail -f price-refresh.log"
echo "To stop: kill $PID"