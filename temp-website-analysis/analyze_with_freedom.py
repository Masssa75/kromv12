#!/usr/bin/env python3
"""
Give AI complete freedom to identify exceptional signals
Don't constrain it to specific patterns
"""

import sqlite3
import json
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

OPEN_ROUTER_API_KEY = "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"

def parse_website_fully(url):
    """Get comprehensive website content"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(3000)
            
            # Get everything we can
            title = page.title()
            
            # Full text content
            text = page.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script, style');
                    scripts.forEach(el => el.remove());
                    return document.body ? document.body.innerText : '';
                }
            """)
            
            # All links with context
            all_links = page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href]'));
                    return links.map(link => {
                        let parent = link.parentElement;
                        let context = '';
                        for (let i = 0; i < 3 && parent; i++) {
                            context = parent.innerText || '';
                            if (context.length > 20) break;
                            parent = parent.parentElement;
                        }
                        return {
                            text: link.innerText.trim(),
                            href: link.href,
                            context: context.substring(0, 200)
                        };
                    }).filter(l => l.text);
                }
            """)
            
            # Get meta descriptions and keywords
            meta_info = page.evaluate("""
                () => {
                    const metas = Array.from(document.querySelectorAll('meta'));
                    return metas.map(m => ({
                        name: m.getAttribute('name') || m.getAttribute('property'),
                        content: m.getAttribute('content')
                    })).filter(m => m.content);
                }
            """)
            
            # Get all headings for structure
            headings = page.evaluate("""
                () => {
                    const headings = Array.from(document.querySelectorAll('h1, h2, h3'));
                    return headings.map(h => ({
                        level: h.tagName,
                        text: h.innerText.trim()
                    })).filter(h => h.text);
                }
            """)
            
            browser.close()
            
            return {
                'success': True,
                'title': title,
                'text': text,
                'links': all_links,
                'meta': meta_info,
                'headings': headings
            }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def analyze_with_complete_freedom(url, ticker, content):
    """Let AI freely identify what makes this project exceptional"""
    import requests
    
    prompt = f"""You are analyzing a crypto project website to identify investment potential.

URL: {url}
Ticker: {ticker}

WEBSITE CONTENT:
{content['text'][:8000]}

KEY SECTIONS FOUND:
{json.dumps([h['text'] for h in content.get('headings', [])[:20]], indent=2)}

IMPORTANT LINKS ON THE SITE:
{json.dumps([{'text': l['text'], 'url': l['href']} for l in content.get('links', [])[:30]], indent=2)}

================================================================================

YOUR TASK: Identify what makes this project exceptional (or not).

Look for ANY exceptional signals, not just team or partnerships. Examples:
- Revolutionary technology or approach
- Unique market positioning or first-mover advantage
- Exceptional traction, adoption, or growth metrics
- Novel solutions to real problems
- Strong community engagement or grassroots movement
- Innovative tokenomics or economic model
- Strategic advantages (geographical, regulatory, timing)
- Academic or research breakthroughs
- Open source contributions or developer adoption
- Real-world integrations or enterprise adoption
- Unique competitive advantages
- Exceptional user experience or design
- Verifiable achievements or milestones
- Strong technical architecture
- Security innovations
- Anything else that stands out as exceptional

Also identify what's critically missing or concerning.

SCORING FRAMEWORK (1-3 scale, 7 categories):

1. Technical Infrastructure - code, architecture, innovation
2. Business & Utility - use case, market fit, competitive advantage  
3. Documentation - clarity, depth, transparency
4. Community & Social - engagement, growth, sentiment
5. Security & Trust - audits, safety measures, track record
6. Team Transparency - experience, credibility, openness
7. Website Presentation - professionalism, UX, information quality

Give 3s generously when you find something truly exceptional in a category.
Give 1s when something critical is missing or concerning.

BE VERY SPECIFIC about what you find. Don't say "strong team" - say WHO and WHY.
Don't say "good technology" - say WHAT makes it good.

Return JSON:
{{
    "category_scores": {{
        "technical_infrastructure": 1-3,
        "business_utility": 1-3,
        "documentation_quality": 1-3,
        "community_social": 1-3,
        "security_trust": 1-3,
        "team_transparency": 1-3,
        "website_presentation": 1-3
    }},
    "total_score": sum,
    "tier": "HIGH/MEDIUM/LOW",
    "proceed_to_stage_2": true if >= 10,
    "exceptional_signals": [
        "BE EXTREMELY SPECIFIC - mention exact features, metrics, people, technologies, achievements"
    ],
    "missing_elements": [
        "BE SPECIFIC about what's missing"
    ],
    "quick_assessment": "One paragraph with specific details about what makes this project stand out (or not)",
    "reasoning": "Explain your scoring with specific examples"
}}"""
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPEN_ROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "moonshotai/kimi-k2",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4  # Slightly higher for more creative identification
            },
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        else:
            print(f"API error: {response.status_code}")
        return None
    except Exception as e:
        print(f"Analysis error: {e}")
        return None

def main():
    """Analyze with complete freedom to identify exceptional qualities"""
    
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    # Get test tokens
    cursor.execute("""
        SELECT ticker, url 
        FROM website_analysis 
        WHERE ticker IN ('GAI', 'MSIA', 'STRAT', 'REX')
        ORDER BY ticker
    """)
    
    tokens = cursor.fetchall()
    
    print("="*80)
    print("🚀 UNCONSTRAINED ANALYSIS - FINDING UNIQUE EXCEPTIONAL SIGNALS")
    print("="*80)
    
    for ticker, url in tokens:
        print(f"\n📊 {ticker}: {url}")
        print("-"*60)
        
        # Parse website
        print("  📖 Parsing website comprehensively...")
        content = parse_website_fully(url)
        
        if not content['success']:
            print(f"  ❌ Parse failed: {content.get('error')}")
            continue
        
        print(f"  ✓ Captured {len(content['text'])} chars of content")
        print(f"  ✓ Found {len(content['headings'])} sections")
        print(f"  ✓ Found {len(content['links'])} links")
        
        # Analyze with freedom
        print("  🤖 Analyzing with complete freedom to identify exceptional qualities...")
        result = analyze_with_complete_freedom(url, ticker, content)
        
        if result:
            print(f"  ✓ Score: {result.get('total_score')}/21 ({result.get('tier')})")
            
            # Update database
            cursor.execute("""
                UPDATE website_analysis 
                SET 
                    total_score = ?,
                    tier = ?,
                    proceed_to_stage_2 = ?,
                    category_scores = ?,
                    exceptional_signals = ?,
                    missing_elements = ?,
                    quick_assessment = ?,
                    reasoning = ?,
                    analyzed_at = ?
                WHERE ticker = ?
            """, (
                result.get('total_score'),
                result.get('tier'),
                result.get('proceed_to_stage_2', False),
                json.dumps(result.get('category_scores', {})),
                json.dumps(result.get('exceptional_signals', [])),
                json.dumps(result.get('missing_elements', [])),
                result.get('quick_assessment'),
                result.get('reasoning'),
                datetime.now().isoformat(),
                ticker
            ))
            conn.commit()
            
            # Show specific signals found
            signals = result.get('exceptional_signals', [])
            if signals:
                print(f"\n  🌟 Exceptional signals discovered:")
                for s in signals:
                    print(f"     • {s[:100]}...")
            
            missing = result.get('missing_elements', [])
            if missing:
                print(f"\n  ⚠️ Critical missing elements:")
                for m in missing[:3]:
                    print(f"     • {m[:100]}...")
            
            print(f"\n  📝 Assessment: {result.get('quick_assessment', '')[:200]}...")
        else:
            print("  ❌ Analysis failed")
        
        print()
        time.sleep(3)
    
    conn.close()
    print("="*80)
    print("✅ Analysis complete! Check http://localhost:5006 for detailed results")

if __name__ == "__main__":
    main()