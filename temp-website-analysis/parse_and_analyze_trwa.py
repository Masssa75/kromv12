#!/usr/bin/env python3
"""
Parse TRWA website content and analyze with multiple AI models
"""
import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

def fetch_website_content(url):
    """Fetch and parse website content"""
    print(f"\n📥 Fetching content from {url}...")
    
    try:
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract key information
        website_data = {
            'url': url,
            'title': soup.title.string if soup.title else 'No title',
            'meta_description': '',
            'headings': [],
            'main_content': '',
            'links': [],
            'images': [],
            'team_section': '',
            'roadmap': '',
            'tokenomics': '',
            'features': []
        }
        
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
        
        # Get main content (paragraphs)
        paragraphs = []
        for p in soup.find_all('p')[:20]:  # First 20 paragraphs
            text = p.get_text(strip=True)
            if len(text) > 50:  # Only meaningful paragraphs
                paragraphs.append(text)
        website_data['main_content'] = '\n'.join(paragraphs[:10])  # First 10 meaningful paragraphs
        
        # Look for team section
        team_keywords = ['team', 'about us', 'who we are', 'founders', 'leadership']
        for keyword in team_keywords:
            team_section = soup.find(['section', 'div'], string=lambda t: t and keyword.lower() in t.lower())
            if team_section:
                parent = team_section.find_parent(['section', 'div'])
                if parent:
                    website_data['team_section'] = parent.get_text(strip=True)[:500]
                    break
        
        # Look for roadmap
        roadmap_section = soup.find(['section', 'div'], string=lambda t: t and 'roadmap' in t.lower())
        if roadmap_section:
            parent = roadmap_section.find_parent(['section', 'div'])
            if parent:
                website_data['roadmap'] = parent.get_text(strip=True)[:500]
        
        # Look for tokenomics
        token_section = soup.find(['section', 'div'], string=lambda t: t and 'tokenomics' in t.lower())
        if token_section:
            parent = token_section.find_parent(['section', 'div'])
            if parent:
                website_data['tokenomics'] = parent.get_text(strip=True)[:500]
        
        # Get important links
        for link in soup.find_all('a', href=True)[:30]:
            text = link.get_text(strip=True)
            href = link['href']
            if text and any(keyword in text.lower() for keyword in ['whitepaper', 'docs', 'github', 'audit', 'twitter', 'telegram']):
                website_data['links'].append(f"{text}: {urljoin(url, href)}")
        
        # Count images
        website_data['images'] = len(soup.find_all('img'))
        
        print("✅ Content extracted successfully")
        return website_data
        
    except Exception as e:
        print(f"❌ Error fetching website: {e}")
        return None

def create_analysis_prompt(website_data):
    """Create a comprehensive prompt with the parsed website data"""
    
    prompt = f"""Analyze this crypto project website based on the extracted content below.

Website: {website_data['url']}
Title: {website_data['title']}
Meta Description: {website_data['meta_description']}

HEADINGS FOUND:
{chr(10).join(website_data['headings'][:15])}

MAIN CONTENT:
{website_data['main_content'][:1500]}

TEAM SECTION:
{website_data['team_section'] if website_data['team_section'] else 'No team section found'}

ROADMAP:
{website_data['roadmap'] if website_data['roadmap'] else 'No roadmap found'}

TOKENOMICS:
{website_data['tokenomics'] if website_data['tokenomics'] else 'No tokenomics found'}

IMPORTANT LINKS:
{chr(10).join(website_data['links'][:10]) if website_data['links'] else 'No important links found'}

IMAGE COUNT: {website_data['images']} images on the page

Based on this content, score the website's legitimacy from 1-10:

SCORING CRITERIA:
8-10: ALPHA - Enterprise-grade with verifiable backing
6-7: SOLID - Professional project with clear vision
4-5: BASIC - Minimal but functional
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
                # Clean up response
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
    print("TRWA Website Analysis - Parse & Analyze Approach")
    print("="*80)
    
    # TRWA website
    url = "https://tharwa.finance/"
    
    # Step 1: Parse website content
    website_data = fetch_website_content(url)
    
    if not website_data:
        print("Failed to fetch website content")
        return
    
    # Display what we extracted
    print("\n📊 Extracted Content Summary:")
    print(f"  - Title: {website_data['title']}")
    print(f"  - Headings found: {len(website_data['headings'])}")
    print(f"  - Main content length: {len(website_data['main_content'])} chars")
    print(f"  - Team section: {'Yes' if website_data['team_section'] else 'No'}")
    print(f"  - Roadmap: {'Yes' if website_data['roadmap'] else 'No'}")
    print(f"  - Tokenomics: {'Yes' if website_data['tokenomics'] else 'No'}")
    print(f"  - Important links: {len(website_data['links'])}")
    print(f"  - Images: {website_data['images']}")
    
    # Step 2: Analyze with multiple models
    models_to_test = [
        # Models that performed well before
        ("google/gemini-2.0-flash-exp:free", "Gemini 2.0 Flash"),
        ("moonshotai/kimi-k2", "Kimi K2"),
        
        # Top tier models without browsing
        ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet"),
        ("openai/gpt-4o", "GPT-4o"),
        
        # Chinese models
        ("deepseek/deepseek-chat", "DeepSeek Chat"),
        ("qwen/qwen-2.5-72b-instruct", "Qwen 2.5 72B"),
        
        # Open source
        ("meta-llama/llama-3.3-70b-instruct", "Llama 3.3 70B"),
    ]
    
    print("\n" + "="*80)
    print("Analyzing with Multiple AI Models")
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
    print("COMPARISON OF RESULTS")
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
    
    # Save results
    output = {
        'website': url,
        'extracted_data': website_data,
        'analyses': results,
        'timestamp': datetime.now().isoformat()
    }
    
    with open('trwa_parsed_analysis.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n📁 Results saved to trwa_parsed_analysis.json")

if __name__ == "__main__":
    main()