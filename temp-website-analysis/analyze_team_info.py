#!/usr/bin/env python3
"""
Analyze team information from TRWA website using Playwright parser with focused prompts
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
                '[id*="team"]',
                '[class*="founder"]',
                '[class*="leadership"]',
                '[class*="advisor"]',
                '[class*="member"]'
            ]
            
            for selector in team_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    for elem in elements[:5]:  # Get more content for team analysis
                        text = elem.text_content()
                        if text and len(text) > 20:
                            team_texts.append(text)
                except:
                    pass
            
            if team_texts:
                website_data['team_section'] = '\n'.join(team_texts[:1000])  # More team content
            
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
            website_data['main_content'] = all_text[:5000] if all_text else ''  # More content
            
            # Look for social links (including LinkedIn for team members)
            social_keywords = ['twitter', 'telegram', 'discord', 'github', 'medium', 'linkedin', 'reddit', 'youtube']
            for link in soup.find_all('a', href=True):
                href = link['href'].lower()
                for keyword in social_keywords:
                    if keyword in href:
                        link_text = link.get_text(strip=True)
                        website_data['social_links'].append(f"{keyword.capitalize()}: {link['href']} (Text: {link_text})")
                        break
            
            # Remove duplicates from social links
            website_data['social_links'] = list(set(website_data['social_links']))
            
            # Count images
            website_data['images'] = len(soup.find_all('img'))
            
            # Get important links
            for link in soup.find_all('a', href=True)[:50]:
                text = link.get_text(strip=True)
                href = link['href']
                if text and any(keyword in text.lower() for keyword in ['whitepaper', 'docs', 'audit', 'contract', 'team', 'about']):
                    website_data['links'].append(f"{text}: {href}")
            
            print(f"✅ Successfully extracted content with JavaScript rendering")
            print(f"  - Total content length: {len(all_text)} characters")
            print(f"  - Headings found: {len(website_data['headings'])}")
            print(f"  - Social links: {len(website_data['social_links'])}")
            print(f"  - Team section: {'Yes' if website_data['team_section'] else 'No'}")
            
            return website_data
            
    except Exception as e:
        print(f"❌ Error with Playwright: {e}")
        return None

def create_team_focused_prompt(website_data):
    """Create a prompt specifically focused on team analysis"""
    
    prompt = f"""You are analyzing a crypto project website to identify TEAM INFORMATION. 
Focus specifically on finding and evaluating team members, their credentials, and legitimacy.

Website: {website_data['url']}
Title: {website_data['title']}

MAIN CONTENT (from fully rendered page with JavaScript):
{website_data['main_content'][:3000]}

TEAM SECTION CONTENT:
{website_data['team_section'] if website_data['team_section'] else 'No dedicated team section found'}

ALL HEADINGS ON THE PAGE:
{chr(10).join(website_data['headings'][:30])}

SOCIAL LINKS FOUND:
{chr(10).join(website_data['social_links']) if website_data['social_links'] else 'No social links found'}

IMPORTANT LINKS:
{chr(10).join(website_data['links'][:20]) if website_data['links'] else 'No important links found'}

Based on the content above, provide a DETAILED analysis of the TEAM information:

1. LIST EVERY TEAM MEMBER YOU CAN IDENTIFY:
   - What are their EXACT names? (First and Last names if available)
   - What are their roles/titles?
   - Any previous experience mentioned?
   - LinkedIn profiles or other professional links?

2. TEAM TRANSPARENCY ASSESSMENT:
   - Are team members using real names or pseudonyms?
   - Are there profile photos? Do they look real or stock?
   - Is there verifiable information (LinkedIn, previous companies)?
   - Any red flags (anonymous team, vague descriptions)?

3. LEGITIMACY SCORE (1-10):
   - 8-10: Full team with real names, LinkedIn profiles, verifiable backgrounds
   - 5-7: Some team info but limited verification possible
   - 3-4: Minimal team info, mostly anonymous or vague
   - 1-2: No team info or obviously fake/suspicious

Provide your analysis as JSON:
{{
  "team_members": [
    {{
      "name": "exact name as shown",
      "role": "their title/position",
      "experience": "any background mentioned",
      "linkedin": "LinkedIn URL if found",
      "other_links": ["any other professional links"]
    }}
  ],
  "team_transparency_score": (1-10),
  "real_names_found": true/false,
  "linkedin_profiles_found": (number),
  "profile_photos": "description of photos if any",
  "verification_possible": true/false,
  "red_flags": ["list any concerns"],
  "positive_indicators": ["list good signs"],
  "overall_assessment": "2-3 sentences about team legitimacy"
}}

IMPORTANT: If you cannot find ANY specific team member names, say so explicitly in the overall_assessment.
Return ONLY the JSON, no other text."""
    
    return prompt

def analyze_with_model(model_id, model_name, website_data):
    """Analyze parsed content with a specific model"""
    
    OPEN_ROUTER_API_KEY = "OPENROUTER_API_KEY_REMOVED"
    
    prompt = create_team_focused_prompt(website_data)
    
    print(f"\n🤖 Analyzing team info with {model_name}...")
    
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
                'max_tokens': 2000
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
                    print(f"  Team transparency score: {analysis.get('team_transparency_score')}/10")
                    print(f"  Team members found: {len(analysis.get('team_members', []))}")
                    if analysis.get('team_members'):
                        for member in analysis['team_members'][:3]:  # Show first 3
                            print(f"    - {member.get('name')} ({member.get('role')})")
                    return analysis
                else:
                    print(f"  ❌ Could not parse JSON response")
                    return None
            except json.JSONDecodeError as e:
                print(f"  ❌ JSON parse error: {e}")
                print(f"  Response: {content[:500]}")
                return None
        else:
            print(f"  ❌ API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def main():
    print("\n" + "="*80)
    print("TRWA Website TEAM ANALYSIS - What Do AI Models See?")
    print("="*80)
    
    # TRWA website
    url = "https://tharwa.finance/"
    
    # Step 1: Parse website with Playwright (JavaScript rendering)
    website_data = fetch_website_with_playwright(url)
    
    if not website_data:
        print("Failed to fetch website content")
        return
    
    # Step 2: Analyze team info with multiple models
    models_to_test = [
        # Top performers from before
        ("google/gemini-2.0-flash-exp:free", "Gemini 2.0 Flash"),
        ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet"),
        ("openai/gpt-4o", "GPT-4o"),
        
        # Additional strong models
        ("deepseek/deepseek-chat", "DeepSeek Chat"),
        ("qwen/qwen-2.5-72b-instruct", "Qwen 2.5 72B"),
        ("meta-llama/llama-3.3-70b-instruct", "Llama 3.3 70B"),
    ]
    
    print("\n" + "="*80)
    print("Analyzing TEAM INFORMATION with Multiple AI Models")
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
    
    # Compare what different models see
    print("\n" + "="*80)
    print("COMPARISON: What Team Information Do Different Models See?")
    print("="*80)
    
    print("\n📊 Team Transparency Scores:")
    print("-" * 40)
    for r in results:
        score = r['analysis'].get('team_transparency_score', 'N/A')
        members_count = len(r['analysis'].get('team_members', []))
        print(f"{r['model']:<25} Score: {score}/10, Members found: {members_count}")
    
    print("\n👥 Team Members Identified by Each Model:")
    print("-" * 40)
    for r in results:
        print(f"\n{r['model']}:")
        team_members = r['analysis'].get('team_members', [])
        if team_members:
            for member in team_members[:5]:  # Show up to 5 members
                name = member.get('name', 'Unknown')
                role = member.get('role', 'No role')
                linkedin = "Yes" if member.get('linkedin') else "No"
                print(f"  • {name} - {role} (LinkedIn: {linkedin})")
        else:
            print("  No specific team members identified")
    
    print("\n🔍 Overall Assessments:")
    print("-" * 40)
    for r in results:
        print(f"\n{r['model']}:")
        print(f"  {r['analysis'].get('overall_assessment', 'No assessment provided')}")
    
    print("\n⚠️ Red Flags Identified:")
    print("-" * 40)
    all_red_flags = set()
    for r in results:
        flags = r['analysis'].get('red_flags', [])
        for flag in flags:
            all_red_flags.add(flag)
    
    if all_red_flags:
        for flag in all_red_flags:
            print(f"  • {flag}")
    else:
        print("  No red flags identified")
    
    print("\n✅ Positive Indicators:")
    print("-" * 40)
    all_positive = set()
    for r in results:
        positives = r['analysis'].get('positive_indicators', [])
        for positive in positives:
            all_positive.add(positive)
    
    if all_positive:
        for positive in all_positive:
            print(f"  • {positive}")
    else:
        print("  No positive indicators identified")
    
    # Save results
    output = {
        'website': url,
        'extracted_data': {
            'url': website_data['url'],
            'title': website_data['title'],
            'team_section_found': bool(website_data['team_section']),
            'team_section_length': len(website_data['team_section']) if website_data['team_section'] else 0,
            'social_links_count': len(website_data['social_links']),
            'total_content_length': len(website_data['main_content'])
        },
        'team_analyses': results,
        'timestamp': datetime.now().isoformat(),
        'method': 'playwright_with_javascript_team_focus'
    }
    
    with open('trwa_team_analysis.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n📁 Results saved to trwa_team_analysis.json")
    print("\n" + "="*80)
    print("KEY QUESTION: Did any model find SPECIFIC team member NAMES?")
    print("="*80)
    
    # Check if any model found actual names
    any_names_found = False
    for r in results:
        team_members = r['analysis'].get('team_members', [])
        for member in team_members:
            name = member.get('name', '').strip()
            if name and name.lower() not in ['unknown', 'not specified', 'anonymous', '']:
                any_names_found = True
                print(f"✅ {r['model']} found: {name}")
    
    if not any_names_found:
        print("❌ No models found specific team member names")

if __name__ == "__main__":
    main()