#!/bin/bash

echo "=== STARTING PARALLEL PRICE REFRESH ==="
echo "This will run 5 workers in parallel to speed up the process"
echo ""

# Kill any existing price refresh processes
pkill -f "refresh.*price" 2>/dev/null

# Run the parallel refresh in background
nohup python3 -W ignore refresh-prices-parallel.py > parallel-refresh.log 2>&1 &
PID=$!

echo "Process started with PID: $PID"
echo ""
echo "Commands:"
echo "  Monitor progress: tail -f parallel-refresh.log"
echo "  Check status: python3 check-update-status.py"
echo "  Stop process: kill $PID"
echo ""
echo "With 5 parallel workers, this should complete in ~1-2 hours instead of 5-6 hours"