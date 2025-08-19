#!/usr/bin/env python3
"""
Enhanced analysis that extracts specific details before AI analysis
This gives AI more context to find exceptional signals
"""

import sqlite3
import json
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

OPEN_ROUTER_API_KEY = "OPENROUTER_API_KEY_REMOVED"

def extract_key_details(url):
    """Extract LinkedIn profiles, team info, and notable mentions"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(3000)
            
            # Get all page content
            html = page.content()
            text = page.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script, style');
                    scripts.forEach(el => el.remove());
                    return document.body ? document.body.innerText : '';
                }
            """)
            
            # Extract LinkedIn profiles with context
            linkedin_profiles = []
            links = page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href*="linkedin.com"]'));
                    return links.map(link => {
                        // Get surrounding text for context
                        let parent = link.parentElement;
                        let context = '';
                        if (parent) {
                            // Look for parent divs that might contain team info
                            for (let i = 0; i < 3 && parent; i++) {
                                context = parent.innerText || '';
                                if (context.length > 20) break;
                                parent = parent.parentElement;
                            }
                        }
                        return {
                            url: link.href,
                            text: link.innerText,
                            context: context.substring(0, 200)
                        };
                    });
                }
            """)
            
            # Look for GitHub links
            github_links = page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href*="github.com"]'));
                    return links.map(l => l.href);
                }
            """)
            
            # Look for notable company mentions
            notable_companies = []
            notable_patterns = [
                r'(?:ex-|from |formerly |previously |veteran|alumni)[\s-]*(Google|Apple|Microsoft|Amazon|Facebook|Meta|Tesla|SpaceX|IBM|Oracle|Adobe|Netflix|Uber|Coinbase|Binance|OpenAI|DeepMind)',
                r'(?:backed by|funded by|investors include|investment from|partner[s]? with)[\s:]*(a16z|Andreessen Horowitz|Sequoia|YC|Y Combinator|Coinbase Ventures|Binance Labs|Pantera|Paradigm|Google Ventures|Microsoft)',
                r'(?:audited by|audit[s]? by|security by)[\s:]*(CertiK|OpenZeppelin|Trail of Bits|Quantstamp|ConsenSys|PeckShield|SlowMist)',
            ]
            
            for pattern in notable_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                notable_companies.extend(matches)
            
            # Look for team section
            team_sections = page.evaluate("""
                () => {
                    const sections = Array.from(document.querySelectorAll('*'));
                    return sections.filter(el => {
                        const text = el.innerText || '';
                        return text.match(/our team|team members|founders|leadership|about us/i);
                    }).slice(0, 3).map(el => el.innerText.substring(0, 500));
                }
            """)
            
            browser.close()
            
            return {
                'success': True,
                'text': text[:10000],
                'linkedin_profiles': links[:10],
                'github_links': github_links[:5],
                'notable_companies': list(set(notable_companies))[:10],
                'team_sections': team_sections[:3]
            }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def analyze_with_enhanced_prompt(url, ticker, details):
    """Analyze with detailed context and freedom to identify exceptional signals"""
    import requests
    
    # Build context-rich prompt
    prompt = f"""Analyze this crypto project website for investment potential.

URL: {url}
Ticker: {ticker}

KEY DETAILS EXTRACTED:

LINKEDIN PROFILES FOUND ({len(details.get('linkedin_profiles', []))}):"""
    
    for profile in details.get('linkedin_profiles', [])[:5]:
        prompt += f"\n- {profile['url']}"
        if profile.get('context'):
            prompt += f"\n  Context: {profile['context'][:100]}"
    
    prompt += f"""

GITHUB REPOSITORIES: {', '.join(details.get('github_links', [])) or 'None found'}

NOTABLE MENTIONS DETECTED: {', '.join(details.get('notable_companies', [])) or 'None found'}

TEAM SECTION CONTENT:
{details.get('team_sections', ['No team section found'])[0][:500] if details.get('team_sections') else 'No team section found'}

WEBSITE CONTENT EXCERPT:
{details.get('text', '')[:3000]}

================================================================================

STAGE 1 ASSESSMENT - Score each category 1-3:

1. Technical Infrastructure (GitHub, code quality, tech stack)
2. Business & Utility (use case, market fit, tokenomics, partnerships)
3. Documentation (whitepaper, docs, roadmap)
4. Community & Social (Twitter, Discord, Telegram, engagement)
5. Security & Trust (audits, KYC, liquidity locks)
6. Team Transparency (real names, experience, track record)
7. Website Presentation (design, UX, professionalism)

IMPORTANT: Look for SPECIFIC exceptional signals:
- Names and backgrounds of team members (e.g., "John Doe, ex-Google AI researcher")
- Specific company partnerships or backers (e.g., "Backed by a16z")
- Notable achievements or credentials
- Specific security firms or audit reports
- Any exceptional claims or features

BE SPECIFIC in your exceptional_signals and missing_elements lists!

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
    "exceptional_signals": ["BE SPECIFIC: mention actual names, companies, achievements"],
    "missing_elements": ["List specific missing items"],
    "quick_assessment": "One paragraph with specific details",
    "reasoning": "Explain scoring with specific examples"
}}
"""
    
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
                "temperature": 0.3
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        return None
    except Exception as e:
        print(f"Analysis error: {e}")
        return None

def main():
    """Re-analyze tokens with enhanced detail extraction"""
    
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
    print("🔬 ENHANCED ANALYSIS WITH DETAIL EXTRACTION")
    print("="*80)
    
    for ticker, url in tokens:
        print(f"\n📊 {ticker}: {url}")
        print("-"*60)
        
        # Extract details first
        print("  🔍 Extracting key details...")
        details = extract_key_details(url)
        
        if not details['success']:
            print(f"  ❌ Extraction failed: {details.get('error')}")
            continue
        
        print(f"  ✓ Found {len(details['linkedin_profiles'])} LinkedIn profiles")
        print(f"  ✓ Found {len(details['github_links'])} GitHub links")
        if details['notable_companies']:
            print(f"  ✓ Notable mentions: {', '.join(details['notable_companies'][:3])}")
        
        # Analyze with enhanced prompt
        print("  🤖 Analyzing with enhanced context...")
        result = analyze_with_enhanced_prompt(url, ticker, details)
        
        if result:
            print(f"  ✓ Score: {result.get('total_score')}/21")
            
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
            
            # Show specific signals
            signals = result.get('exceptional_signals', [])
            if signals:
                print(f"  🌟 Exceptional signals:")
                for s in signals[:3]:
                    print(f"     • {s}")
        else:
            print("  ❌ Analysis failed")
        
        time.sleep(3)
    
    conn.close()
    print("\n✅ Enhanced analysis complete! Check http://localhost:5006")

if __name__ == "__main__":
    main()