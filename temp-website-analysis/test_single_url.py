#!/usr/bin/env python3
"""Test parsing a single URL"""

from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer
import sys

url = sys.argv[1] if len(sys.argv) > 1 else "https://ninjatraders.io/"

print(f"Testing URL: {url}")
analyzer = ComprehensiveWebsiteAnalyzer('test.db')

print("Starting parse...")
parsed = analyzer.parse_website_with_playwright(url)

if parsed and parsed.get('content'):
    print(f"✓ Parsed successfully: {len(parsed.get('content', ''))} characters")
else:
    print(f"✗ Failed to parse")