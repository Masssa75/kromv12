#!/usr/bin/env python3
"""
Parse TRWA website with Playwright (JavaScript rendering) and analyze with multiple AI models
"""
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests
import json
import time
from datetime import datetime

def fetch_website_with_playwright(url):
    """Fetch website content with full JavaScript rendering using Playwright"""
    
    print(f"\n🌐 Fetching {url} with Playwright (JavaScript enabled)...")
    
    website_data = {
        'url': url,
        'title': '',
        'meta_description': '',
        'headings': [],
        'main_content': '',
        'links': [],
        'images': 0,
        'team_section': '',
        'roadmap': '',
        'tokenomics': '',
        'features': [],
        'social_links': []
    }
    
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate to the page and wait for it to load
            print("  Loading page...")
            page.goto(url, wait_until='networkidle')
            
            # Wait a bit more for any lazy-loaded content
            page.wait_for_timeout(3000)
            
            # Get the fully rendered HTML
            html_content = page.content()
            
            # Also try to extract some data directly from the page
            print("  Extracting content...")
            
            # Get title
            website_data['title'] = page.title()
            
            # Try to find team section using Playwright selectors
            team_texts = []
            team_selectors = [
                'text=/team/i',
                'text=/about us/i',
                'text=/our team/i',
                '[class*="team"]',
                '[id*="team"]'
            ]
            
            for selector in team_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    for elem in elements[:3]:  # Limit to avoid too much
                        text = elem.text_content()
                        if text and len(text) > 20:
                            team_texts.append(text)
                except:
                    pass
            
            if team_texts:
                website_data['team_section'] = ' '.join(team_texts[:500])
            
            # Look for roadmap
            roadmap_texts = []
            roadmap_selectors = [
                'text=/roadmap/i',
                '[class*="roadmap"]',
                '[id*="roadmap"]'
            ]
            
            for selector in roadmap_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    for elem in elements[:3]:
                        text = elem.text_content()
                        if text and len(text) > 20:
                            roadmap_texts.append(text)
                except:
                    pass
            
            if roadmap_texts:
                website_data['roadmap'] = ' '.join(roadmap_texts[:500])
            
            # Look for tokenomics
            token_texts = []
            token_selectors = [
                'text=/tokenomics/i',
                'text=/token distribution/i',
                '[class*="token"]',
                '[class*="distribution"]'
            ]
            
            for selector in token_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    for elem in elements[:3]:
                        text = elem.text_content()
                        if text and len(text) > 20:
                            token_texts.append(text)
                except:
                    pass
            
            if token_texts:
                website_data['tokenomics'] = ' '.join(token_texts[:500])
            
            # Get all text content from the page
            all_text = page.evaluate("() => document.body.innerText")
            
            browser.close()
            
            # Now parse the fully rendered HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Get meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                website_data['meta_description'] = meta_desc.get('content', '')
            
            # Get all headings
            for i in range(1, 4):
                for heading in soup.find_all(f'h{i}'):
                    text = heading.get_text(strip=True)
                    if text:
                        website_data['headings'].append(f"H{i}: {text}")
            
            # Get main content from all text
            website_data['main_content'] = all_text[:3000] if all_text else ''
            
            # Look for social links
            social_keywords = ['twitter', 'telegram', 'discord', 'github', 'medium', 'linkedin', 'reddit', 'youtube']
            for link in soup.find_all('a', href=True):
                href = link['href'].lower()
                for keyword in social_keywords:
                    if keyword in href:
                        website_data['social_links'].append(f"{keyword.capitalize()}: {link['href']}")
                        break
            
            # Remove duplicates from social links
            website_data['social_links'] = list(set(website_data['social_links']))
            
            # Count images
            website_data['images'] = len(soup.find_all('img'))
            
            # Get important links
            for link in soup.find_all('a', href=True)[:50]:
                text = link.get_text(strip=True)
                href = link['href']
                if text and any(keyword in text.lower() for keyword in ['whitepaper', 'docs', 'audit', 'contract']):
                    website_data['links'].append(f"{text}: {href}")
            
            print(f"✅ Successfully extracted content with JavaScript rendering")
            print(f"  - Total content length: {len(all_text)} characters")
            print(f"  - Headings found: {len(website_data['headings'])}")
            print(f"  - Social links: {len(website_data['social_links'])}")
            print(f"  - Team section: {'Yes' if website_data['team_section'] else 'No'}")
            print(f"  - Roadmap: {'Yes' if website_data['roadmap'] else 'No'}")
            print(f"  - Tokenomics: {'Yes' if website_data['tokenomics'] else 'No'}")
            
            return website_data
            
    except Exception as e:
        print(f"❌ Error with Playwright: {e}")
        return None

def create_analysis_prompt(website_data):
    """Create a comprehensive prompt with the parsed website data"""
    
    prompt = f"""Analyze this crypto project website based on the FULLY RENDERED content below (JavaScript was executed).

Website: {website_data['url']}
Title: {website_data['title']}
Meta Description: {website_data['meta_description']}

HEADINGS FOUND ({len(website_data['headings'])} total):
{chr(10).join(website_data['headings'][:20])}

MAIN CONTENT (from rendered page):
{website_data['main_content'][:2000]}

TEAM SECTION:
{website_data['team_section'] if website_data['team_section'] else 'No team section found'}

ROADMAP:
{website_data['roadmap'] if website_data['roadmap'] else 'No roadmap found'}

TOKENOMICS:
{website_data['tokenomics'] if website_data['tokenomics'] else 'No tokenomics found'}

SOCIAL LINKS FOUND ({len(website_data['social_links'])} total):
{chr(10).join(website_data['social_links']) if website_data['social_links'] else 'No social links found'}

IMPORTANT LINKS:
{chr(10).join(website_data['links'][:10]) if website_data['links'] else 'No important links found'}

IMAGE COUNT: {website_data['images']} images on the page

Based on this FULLY RENDERED content (JavaScript was executed), score the website's legitimacy from 1-10:

SCORING CRITERIA:
8-10: ALPHA - Enterprise-grade with verifiable backing, real team, audits
6-7: SOLID - Professional project with clear vision and some transparency
4-5: BASIC - Minimal but functional, limited information
1-3: TRASH - Red flags, vague promises, no substance

Provide your analysis as JSON:
{{
  "score": (1-10),
  "tier": "(ALPHA/SOLID/BASIC/TRASH)",
  "legitimacy_indicators": ["list positive findings"],
  "red_flags": ["list concerning elements"],
  "technical_depth": "assessment of documentation quality",
  "team_transparency": "assessment of team information",
  "reasoning": "2-3 sentences explaining the score"
}}

Return ONLY the JSON, no other text."""
    
    return prompt

def analyze_with_model(model_id, model_name, website_data):
    """Analyze parsed content with a specific model"""
    
    OPEN_ROUTER_API_KEY = "OPENROUTER_API_KEY_REMOVED"
    
    prompt = create_analysis_prompt(website_data)
    
    print(f"\n🤖 Analyzing with {model_name}...")
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {OPEN_ROUTER_API_KEY}',
            },
            json={
                'model': model_id,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.1,
                'max_tokens': 1000
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Parse JSON from response
            try:
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group(0))
                    print(f"  Score: {analysis.get('score')}/10 - {analysis.get('tier')}")
                    return analysis
                else:
                    print(f"  ❌ Could not parse JSON response")
                    return None
            except json.JSONDecodeError as e:
                print(f"  ❌ JSON parse error: {e}")
                return None
        else:
            print(f"  ❌ API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def main():
    print("\n" + "="*80)
    print("TRWA Website Analysis - Playwright (JavaScript Rendering) Approach")
    print("="*80)
    
    # TRWA website
    url = "https://tharwa.finance/"
    
    # Step 1: Parse website with Playwright (JavaScript rendering)
    website_data = fetch_website_with_playwright(url)
    
    if not website_data:
        print("Failed to fetch website content")
        return
    
    # Step 2: Analyze with multiple models
    models_to_test = [
        # Models that performed well before
        ("google/gemini-2.0-flash-exp:free", "Gemini 2.0 Flash"),
        ("moonshotai/kimi-k2", "Kimi K2"),
        
        # Top tier models
        ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet"),
        ("openai/gpt-4o", "GPT-4o"),
        
        # Chinese models
        ("deepseek/deepseek-chat", "DeepSeek Chat"),
        ("qwen/qwen-2.5-72b-instruct", "Qwen 2.5 72B"),
        
        # Open source
        ("meta-llama/llama-3.3-70b-instruct", "Llama 3.3 70B"),
    ]
    
    print("\n" + "="*80)
    print("Analyzing with Multiple AI Models (Using Fully Rendered Content)")
    print("="*80)
    
    results = []
    
    for model_id, model_name in models_to_test:
        analysis = analyze_with_model(model_id, model_name, website_data)
        
        if analysis:
            results.append({
                'model': model_name,
                'model_id': model_id,
                'analysis': analysis
            })
        
        time.sleep(2)  # Rate limiting
    
    # Compare results
    print("\n" + "="*80)
    print("COMPARISON OF RESULTS (With JavaScript Content)")
    print("="*80)
    
    print("\n📊 Score Comparison:")
    print("-" * 40)
    for r in results:
        score = r['analysis'].get('score', 'N/A')
        tier = r['analysis'].get('tier', 'N/A')
        print(f"{r['model']:<25} {score}/10 ({tier})")
    
    print("\n💭 Reasoning Comparison:")
    print("-" * 40)
    for r in results:
        print(f"\n{r['model']}:")
        print(f"  {r['analysis'].get('reasoning', 'No reasoning provided')}")
    
    # Compare with previous BeautifulSoup results
    print("\n" + "="*80)
    print("BEFORE vs AFTER JavaScript Rendering")
    print("="*80)
    print("\nPrevious scores (BeautifulSoup - no JS):")
    print("  Gemini 2.0: 4/10")
    print("  Kimi K2: 4/10")
    print("  Claude 3.5: 6/10")
    print("  GPT-4o: 5/10")
    print("\nNew scores (Playwright - with JS):")
    for r in results[:4]:
        print(f"  {r['model']}: {r['analysis'].get('score', 'N/A')}/10")
    
    # Save results
    output = {
        'website': url,
        'extracted_data': website_data,
        'analyses': results,
        'timestamp': datetime.now().isoformat(),
        'method': 'playwright_with_javascript'
    }
    
    with open('trwa_playwright_analysis.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n📁 Results saved to trwa_playwright_analysis.json")

if __name__ == "__main__":
    main()