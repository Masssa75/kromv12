#!/usr/bin/env python3
"""
Check if TRWA website uses JavaScript and what we might be missing
"""
import requests
from bs4 import BeautifulSoup
import re

def analyze_website_technology(url):
    """Analyze what technologies a website uses"""
    
    print(f"Analyzing: {url}\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    # Fetch the page
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Response Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
    print(f"Content Length: {len(response.text)} characters\n")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Check for JavaScript
    print("🔍 JavaScript Analysis:")
    print("-" * 40)
    
    # Count script tags
    script_tags = soup.find_all('script')
    print(f"Script tags found: {len(script_tags)}")
    
    # Check for React/Vue/Angular
    react_indicators = ['react', 'React', '_react', 'jsx', 'ReactDOM']
    vue_indicators = ['vue', 'Vue', 'v-for', 'v-if', 'v-model']
    angular_indicators = ['angular', 'Angular', 'ng-app', 'ng-controller']
    next_indicators = ['_next', '__NEXT_DATA__', 'nextjs']
    
    content = response.text.lower()
    
    frameworks_detected = []
    if any(indicator.lower() in content for indicator in react_indicators):
        frameworks_detected.append("React")
    if any(indicator.lower() in content for indicator in vue_indicators):
        frameworks_detected.append("Vue")
    if any(indicator.lower() in content for indicator in angular_indicators):
        frameworks_detected.append("Angular")
    if any(indicator.lower() in content for indicator in next_indicators):
        frameworks_detected.append("Next.js")
    
    if frameworks_detected:
        print(f"Frameworks detected: {', '.join(frameworks_detected)}")
    else:
        print("No major JS frameworks detected")
    
    # Check for JS files
    js_files = []
    for script in script_tags:
        src = script.get('src', '')
        if src:
            js_files.append(src)
    
    if js_files:
        print(f"\nExternal JS files: {len(js_files)}")
        for js in js_files[:5]:  # First 5
            print(f"  - {js}")
    
    # Check for inline JavaScript
    inline_scripts = [s for s in script_tags if not s.get('src')]
    if inline_scripts:
        print(f"\nInline scripts: {len(inline_scripts)}")
        # Show a sample
        if inline_scripts:
            first_script = inline_scripts[0].string or inline_scripts[0].get_text()
            if first_script:
                preview = first_script[:200].replace('\n', ' ')
                print(f"  Sample: {preview}...")
    
    # Check for API calls or dynamic content indicators
    print("\n🌐 Dynamic Content Indicators:")
    print("-" * 40)
    
    api_patterns = [
        r'fetch\(',
        r'axios\.',
        r'XMLHttpRequest',
        r'\.ajax\(',
        r'api/',
        r'/api/',
        r'graphql'
    ]
    
    dynamic_found = []
    for pattern in api_patterns:
        if re.search(pattern, response.text, re.IGNORECASE):
            dynamic_found.append(pattern)
    
    if dynamic_found:
        print(f"API/AJAX patterns found: {', '.join(dynamic_found)}")
    else:
        print("No obvious API/AJAX patterns found")
    
    # Check meta tags for SPA indicators
    print("\n📱 Single Page App (SPA) Indicators:")
    print("-" * 40)
    
    # Check if main content is minimal (typical of SPAs)
    body = soup.find('body')
    if body:
        # Remove scripts and styles
        for script in body.find_all('script'):
            script.decompose()
        for style in body.find_all('style'):
            style.decompose()
        
        body_text = body.get_text(strip=True)
        if len(body_text) < 500:
            print(f"⚠️ Very little static content ({len(body_text)} chars) - likely SPA")
        else:
            print(f"Static content found: {len(body_text)} characters")
    
    # Look for root div (common in React apps)
    root_div = soup.find('div', id='root') or soup.find('div', id='app') or soup.find('div', id='__next')
    if root_div:
        print(f"✓ Found SPA root element: {root_div.get('id')}")
        # Check if it's empty (content loaded by JS)
        if not root_div.get_text(strip=True):
            print("  └─ Root element is empty - content loaded via JavaScript!")
    
    # Check noscript tag
    noscript = soup.find('noscript')
    if noscript:
        print(f"\n<noscript> tag found: {noscript.get_text(strip=True)[:100]}...")
    
    print("\n" + "="*50)
    print("CONCLUSION:")
    
    if len(script_tags) > 0 or frameworks_detected:
        print("✓ This website USES JavaScript")
        if frameworks_detected:
            print(f"  - Framework: {', '.join(frameworks_detected)}")
        if root_div and not root_div.get_text(strip=True):
            print("  - Type: Single Page Application (SPA)")
            print("  - ⚠️ Most content is loaded dynamically")
            print("  - 📝 Simple HTML parsing will miss most content!")
    else:
        print("✗ No significant JavaScript usage detected")

if __name__ == "__main__":
    analyze_website_technology("https://tharwa.finance/")