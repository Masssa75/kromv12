#!/usr/bin/env python3
try:
    import playwright
    print("✅ Playwright is installed")
    print(f"Version: {playwright.__version__}")
except ImportError:
    print("❌ Playwright is NOT installed")
    print("To install: pip3 install playwright")
    print("Then: playwright install chromium")