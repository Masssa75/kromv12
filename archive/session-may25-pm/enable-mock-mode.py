#!/usr/bin/env python3
"""
Enable mock AI mode for testing when API limits are reached
"""

print("""
🤖 MOCK AI MODE SETUP
====================

Since you've hit API limits, here's how to use mock mode:

1. First, start the mock AI server:
   python3 mock-ai-server.py

2. Then modify your browser to use mock mode:
   - Open browser console (F12)
   - Run this JavaScript:
   
   localStorage.setItem('useMockAI', 'true');
   location.reload();

3. The chat will now use pre-programmed responses that still create real visualizations!

Available commands in mock mode:
- "Show ROI analysis" 
- "Display group performance"
- "Show time trends"
- "Calculate win rates"
- "Create scatter plot"

To disable mock mode later:
- Run in browser console: localStorage.removeItem('useMockAI'); location.reload();
""")