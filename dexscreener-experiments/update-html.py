#!/usr/bin/env python3
"""Quick script to update all API URLs in the HTML file to use proxy"""

import re

# Read the HTML file
with open('index.html', 'r') as f:
    content = f.read()

# Replace all DexScreener API calls
content = re.sub(
    r"fetch\('https://api\.dexscreener\.com/(.*?)'\)",
    r"fetch(`${PROXY_BASE}/api/dexscreener/\1`)",
    content
)

# Replace all GeckoTerminal API calls
content = re.sub(
    r"fetch\(`https://api\.geckoterminal\.com/api/v2/(.*?)`\)",
    r"fetch(`${PROXY_BASE}/api/geckoterminal/\1`)",
    content
)

# Add proxy result handling for remaining functions
# This is a more complex replacement to add the result.success check
def add_proxy_handling(content):
    # Pattern to find response handling
    pattern = r"const data = await response\.json\(\);\s*display"
    replacement = """const result = await response.json();
                
                if (result.success) {
                    display"""
    
    content = re.sub(pattern, replacement, content)
    
    # Update the display function calls
    content = content.replace("displayDexScreenerResults(data,", "displayDexScreenerResults(result.data,")
    content = content.replace("displayGeckoResults(data,", "displayGeckoResults(result.data,")
    
    return content

content = add_proxy_handling(content)

# Write back
with open('index.html', 'w') as f:
    f.write(content)

print("HTML file updated to use proxy server!")